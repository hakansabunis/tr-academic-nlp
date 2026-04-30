"""Mock-based unit tests for the provider-agnostic LLM labeler.

These tests do NOT make real API calls. They inject fake clients that mimic
the SDK response shapes for both Anthropic (Messages API: ``content[0].text``
+ ``usage.input_tokens`` / ``output_tokens``) and Gemini (GenAI API:
``response.text`` + ``response.usage_metadata.prompt_token_count`` /
``candidates_token_count``).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import pytest

from data.labeling.llm_label import (
    GEMINI_INPUT_COST_PER_MTOK,
    GEMINI_OUTPUT_COST_PER_MTOK,
    HAIKU_INPUT_COST_PER_MTOK,
    HAIKU_OUTPUT_COST_PER_MTOK,
    AnthropicLabeler,
    GeminiLabeler,
    LLMLabelerStats,
    label_paragraph,
)


# ---------------------------------------------------------------------------
# Fake Anthropic SDK shape
# ---------------------------------------------------------------------------
@dataclass
class _FakeAnthropicBlock:
    text: str
    type: str = "text"


@dataclass
class _FakeAnthropicUsage:
    input_tokens: int
    output_tokens: int


@dataclass
class _FakeAnthropicResponse:
    content: list[_FakeAnthropicBlock]
    usage: _FakeAnthropicUsage


class _FakeAnthropicClient:
    def __init__(self, responses: list[_FakeAnthropicResponse | Exception]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    @property
    def messages(self) -> "_FakeAnthropicClient":
        return self

    def create(self, **kwargs: Any) -> _FakeAnthropicResponse:
        self.calls.append(kwargs)
        if not self._responses:
            raise RuntimeError("No more scripted Anthropic responses")
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _anthropic_response(spans: list[dict[str, Any]], in_tok: int = 200, out_tok: int = 50) -> _FakeAnthropicResponse:
    return _FakeAnthropicResponse(
        content=[_FakeAnthropicBlock(text=json.dumps(spans, ensure_ascii=False))],
        usage=_FakeAnthropicUsage(input_tokens=in_tok, output_tokens=out_tok),
    )


# ---------------------------------------------------------------------------
# Fake Gemini SDK shape
# ---------------------------------------------------------------------------
@dataclass
class _FakeGeminiUsage:
    prompt_token_count: int
    candidates_token_count: int
    total_token_count: int = 0


@dataclass
class _FakeGeminiResponse:
    text: str
    usage_metadata: _FakeGeminiUsage


class _FakeGeminiModels:
    def __init__(self, responses: list[_FakeGeminiResponse | Exception]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def generate_content(self, **kwargs: Any) -> _FakeGeminiResponse:
        self.calls.append(kwargs)
        if not self._responses:
            raise RuntimeError("No more scripted Gemini responses")
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


@dataclass
class _FakeGeminiClient:
    models: _FakeGeminiModels = field(default_factory=lambda: _FakeGeminiModels([]))

    @classmethod
    def with_responses(cls, responses: list[_FakeGeminiResponse | Exception]) -> "_FakeGeminiClient":
        return cls(models=_FakeGeminiModels(responses))


def _gemini_response(spans: list[dict[str, Any]], in_tok: int = 200, out_tok: int = 50) -> _FakeGeminiResponse:
    return _FakeGeminiResponse(
        text=json.dumps(spans, ensure_ascii=False),
        usage_metadata=_FakeGeminiUsage(
            prompt_token_count=in_tok,
            candidates_token_count=out_tok,
            total_token_count=in_tok + out_tok,
        ),
    )


# ---------------------------------------------------------------------------
# Tests for both labelers via the shared driver
# ---------------------------------------------------------------------------
@pytest.fixture(params=["anthropic", "gemini"])
def labeler(request: pytest.FixtureRequest) -> Any:
    """Yield a labeler with a single successful response — used for shared tests."""
    spans = [
        {"start": 0, "end": 4, "entity": "YIL", "text": "2023"},
        {"start": 13, "end": 16, "entity": "METODOLOJI", "text": "CNN"},
    ]
    if request.param == "anthropic":
        client = _FakeAnthropicClient([_anthropic_response(spans)])
        return AnthropicLabeler(client=client)
    client = _FakeGeminiClient.with_responses([_gemini_response(spans)])
    return GeminiLabeler(client=client)


class TestSharedDriver:
    def test_extracts_known_entities(self, labeler: Any) -> None:
        result = label_paragraph("p1", "2023 yılında CNN modeli", labeler=labeler)
        assert result.succeeded
        assert {s.entity for s in result.spans} == {"YIL", "METODOLOJI"}
        assert result.provider in {"anthropic-haiku", "gemini-flash"}


class TestAnthropicLabeler:
    def test_strips_json_fences(self) -> None:
        fenced = (
            "```json\n"
            + json.dumps([{"start": 0, "end": 4, "entity": "YIL", "text": "2023"}])
            + "\n```"
        )
        response = _FakeAnthropicResponse(
            content=[_FakeAnthropicBlock(text=fenced)],
            usage=_FakeAnthropicUsage(input_tokens=100, output_tokens=20),
        )
        labeler = AnthropicLabeler(client=_FakeAnthropicClient([response]))
        result = label_paragraph("p1", "2023", labeler=labeler)
        assert result.succeeded
        assert len(result.spans) == 1

    def test_drops_unknown_entity_types(self) -> None:
        spans = [
            {"start": 0, "end": 4, "entity": "YIL", "text": "2023"},
            {"start": 5, "end": 10, "entity": "FOOBAR", "text": "foooo"},
        ]
        labeler = AnthropicLabeler(
            client=_FakeAnthropicClient([_anthropic_response(spans)]),
        )
        result = label_paragraph("p1", "2023 fooooo", labeler=labeler)
        assert len(result.spans) == 1
        assert result.spans[0].entity == "YIL"

    def test_drops_invalid_offsets(self) -> None:
        spans = [
            {"start": 5, "end": 5, "entity": "YIL", "text": ""},  # zero-width
            {"start": 10, "end": 4, "entity": "YIL", "text": "x"},  # reversed
            {"entity": "YIL", "text": "2023"},  # missing offsets
            {"start": 0, "end": 4, "entity": "YIL", "text": "2023"},  # ok
        ]
        labeler = AnthropicLabeler(
            client=_FakeAnthropicClient([_anthropic_response(spans)]),
        )
        result = label_paragraph("p1", "2023 başlık", labeler=labeler)
        assert len(result.spans) == 1

    def test_cost_calculation(self) -> None:
        response = _FakeAnthropicResponse(
            content=[_FakeAnthropicBlock(text="[]")],
            usage=_FakeAnthropicUsage(input_tokens=1_000_000, output_tokens=1_000_000),
        )
        labeler = AnthropicLabeler(client=_FakeAnthropicClient([response]))
        result = label_paragraph("p1", "x", labeler=labeler)
        expected = HAIKU_INPUT_COST_PER_MTOK + HAIKU_OUTPUT_COST_PER_MTOK
        assert abs(result.cost_usd - expected) < 1e-9


class TestGeminiLabeler:
    def test_extracts_entities(self) -> None:
        spans = [
            {"start": 0, "end": 4, "entity": "YIL", "text": "2023"},
            {"start": 13, "end": 16, "entity": "METODOLOJI", "text": "CNN"},
        ]
        labeler = GeminiLabeler(
            client=_FakeGeminiClient.with_responses([_gemini_response(spans)]),
        )
        result = label_paragraph("p1", "2023 yılında CNN", labeler=labeler)
        assert result.succeeded
        assert len(result.spans) == 2
        assert result.provider == "gemini-flash"

    def test_cost_calculation(self) -> None:
        labeler = GeminiLabeler(
            client=_FakeGeminiClient.with_responses(
                [_gemini_response([], in_tok=1_000_000, out_tok=1_000_000)],
            ),
        )
        result = label_paragraph("p1", "x", labeler=labeler)
        expected = GEMINI_INPUT_COST_PER_MTOK + GEMINI_OUTPUT_COST_PER_MTOK
        assert abs(result.cost_usd - expected) < 1e-9

    def test_drops_unknown_entity_types(self) -> None:
        spans = [
            {"start": 0, "end": 4, "entity": "YIL", "text": "2023"},
            {"start": 5, "end": 10, "entity": "BOGUS", "text": "x"},
        ]
        labeler = GeminiLabeler(
            client=_FakeGeminiClient.with_responses([_gemini_response(spans)]),
        )
        result = label_paragraph("p1", "2023 bogus", labeler=labeler)
        assert len(result.spans) == 1


class TestRetryAndFailure:
    def test_retries_on_invalid_json_anthropic(self) -> None:
        bad = _FakeAnthropicResponse(
            content=[_FakeAnthropicBlock(text="not valid json {")],
            usage=_FakeAnthropicUsage(input_tokens=100, output_tokens=10),
        )
        good = _anthropic_response(
            [{"start": 0, "end": 4, "entity": "YIL", "text": "2023"}],
        )
        labeler = AnthropicLabeler(client=_FakeAnthropicClient([bad, good]))
        result = label_paragraph(
            "p1", "2023", labeler=labeler, max_retries=2, backoff_seconds=0,
        )
        assert result.succeeded
        assert result.retries == 1

    def test_retries_on_invalid_json_gemini(self) -> None:
        bad = _FakeGeminiResponse(
            text="not json",
            usage_metadata=_FakeGeminiUsage(prompt_token_count=100, candidates_token_count=10),
        )
        good = _gemini_response(
            [{"start": 0, "end": 4, "entity": "YIL", "text": "2023"}],
        )
        labeler = GeminiLabeler(
            client=_FakeGeminiClient.with_responses([bad, good]),
        )
        result = label_paragraph(
            "p1", "2023", labeler=labeler, max_retries=2, backoff_seconds=0,
        )
        assert result.succeeded
        assert result.retries == 1

    def test_gives_up_after_max_retries(self) -> None:
        bad = _FakeAnthropicResponse(
            content=[_FakeAnthropicBlock(text="still not json")],
            usage=_FakeAnthropicUsage(input_tokens=100, output_tokens=10),
        )
        labeler = AnthropicLabeler(client=_FakeAnthropicClient([bad, bad, bad]))
        result = label_paragraph(
            "p1", "2023", labeler=labeler, max_retries=2, backoff_seconds=0,
        )
        assert not result.succeeded
        assert result.error is not None
        assert result.retries == 2

    def test_retries_on_exception(self) -> None:
        good = _gemini_response(
            [{"start": 0, "end": 4, "entity": "YIL", "text": "2023"}],
        )
        labeler = GeminiLabeler(
            client=_FakeGeminiClient.with_responses([RuntimeError("rate limited"), good]),
        )
        result = label_paragraph(
            "p1", "2023", labeler=labeler, max_retries=2, backoff_seconds=0,
        )
        assert result.succeeded
        assert result.retries == 1


class TestStatsAccumulator:
    def test_record_call_tracks_totals(self) -> None:
        stats = LLMLabelerStats()
        stats.record_call(input_tokens=200, output_tokens=50, cost_usd=0.001, success=True)
        stats.record_call(input_tokens=300, output_tokens=80, cost_usd=0.002, success=False)
        assert stats.calls == 2
        assert stats.successful_calls == 1
        assert stats.failed_calls == 1
        assert stats.input_tokens == 500
        assert stats.output_tokens == 130
        assert abs(stats.cost_usd - 0.003) < 1e-9

    def test_to_dict_serializable(self) -> None:
        stats = LLMLabelerStats()
        stats.record_call(input_tokens=200, output_tokens=50, cost_usd=0.001, success=True)
        d = stats.to_dict()
        assert json.dumps(d)


class TestEdgeCases:
    def test_empty_response_returns_zero_spans_anthropic(self) -> None:
        labeler = AnthropicLabeler(
            client=_FakeAnthropicClient([_anthropic_response([])]),
        )
        result = label_paragraph("p1", "no entities here", labeler=labeler)
        assert result.succeeded
        assert result.spans == []

    def test_empty_response_returns_zero_spans_gemini(self) -> None:
        labeler = GeminiLabeler(
            client=_FakeGeminiClient.with_responses([_gemini_response([])]),
        )
        result = label_paragraph("p1", "no entities here", labeler=labeler)
        assert result.succeeded
        assert result.spans == []

    def test_non_array_top_level_fails(self) -> None:
        bad = _FakeAnthropicResponse(
            content=[_FakeAnthropicBlock(text='{"not": "an array"}')],
            usage=_FakeAnthropicUsage(input_tokens=100, output_tokens=10),
        )
        labeler = AnthropicLabeler(client=_FakeAnthropicClient([bad]))
        result = label_paragraph(
            "p1", "x", labeler=labeler, max_retries=0, backoff_seconds=0,
        )
        assert not result.succeeded


class TestFactories:
    def test_get_default_labeler_unknown_provider(self) -> None:
        from data.labeling.llm_label import get_default_labeler  # noqa: PLC0415

        with pytest.raises(ValueError, match="Unknown LLM provider"):
            get_default_labeler(provider="bogus-llm")

    def test_get_anthropic_raises_without_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        from data.labeling.llm_label import get_anthropic_labeler  # noqa: PLC0415

        with pytest.raises(RuntimeError):
            get_anthropic_labeler()

    def test_get_gemini_raises_without_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        from data.labeling.llm_label import get_gemini_labeler  # noqa: PLC0415

        with pytest.raises(RuntimeError):
            get_gemini_labeler()
