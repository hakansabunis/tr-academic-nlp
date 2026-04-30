"""Mock-based unit tests for the Claude Haiku NER labeling module.

These tests do NOT make real Anthropic API calls. They inject a fake client
that mimics the SDK's response shape (``response.content[0].text`` plus
``response.usage.input_tokens`` / ``output_tokens``). This proves the
parsing, retry, cost-tracking, and span-validation logic works regardless
of whether the `anthropic` package is installed.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import pytest

from data.labeling.llm_label import (
    HAIKU_INPUT_COST_PER_MTOK,
    HAIKU_OUTPUT_COST_PER_MTOK,
    LLMLabelerStats,
    label_paragraph,
)


# ---------------------------------------------------------------------------
# Fake Anthropic SDK shapes
# ---------------------------------------------------------------------------
@dataclass
class _FakeBlock:
    text: str
    type: str = "text"


@dataclass
class _FakeUsage:
    input_tokens: int
    output_tokens: int


@dataclass
class _FakeResponse:
    content: list[_FakeBlock]
    usage: _FakeUsage


class _ScriptedClient:
    """Sequentially returns pre-canned responses; raises if exhausted."""

    def __init__(self, responses: list[_FakeResponse | Exception]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    @property
    def messages(self) -> "_ScriptedClient":
        return self

    def create(self, **kwargs: Any) -> _FakeResponse:
        self.calls.append(kwargs)
        if not self._responses:
            raise RuntimeError("No more scripted responses")
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _success_response(spans: list[dict[str, Any]], in_tok: int = 200, out_tok: int = 50) -> _FakeResponse:
    return _FakeResponse(
        content=[_FakeBlock(text=json.dumps(spans, ensure_ascii=False))],
        usage=_FakeUsage(input_tokens=in_tok, output_tokens=out_tok),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestParseValidJson:
    def test_extracts_known_entities(self) -> None:
        client = _ScriptedClient(
            [
                _success_response(
                    [
                        {"start": 0, "end": 4, "entity": "YIL", "text": "2023"},
                        {"start": 13, "end": 16, "entity": "METODOLOJI", "text": "CNN"},
                    ]
                )
            ]
        )
        result = label_paragraph("p1", "2023 yılında CNN modeli", client=client)
        assert result.succeeded
        assert len(result.spans) == 2
        assert {s.entity for s in result.spans} == {"YIL", "METODOLOJI"}

    def test_strips_json_fences(self) -> None:
        # Some models occasionally wrap output in ```json fences
        fenced = (
            "```json\n"
            + json.dumps([{"start": 0, "end": 4, "entity": "YIL", "text": "2023"}])
            + "\n```"
        )
        response = _FakeResponse(
            content=[_FakeBlock(text=fenced)],
            usage=_FakeUsage(input_tokens=100, output_tokens=20),
        )
        client = _ScriptedClient([response])
        result = label_paragraph("p1", "2023", client=client)
        assert result.succeeded
        assert len(result.spans) == 1

    def test_drops_unknown_entity_types(self) -> None:
        # An LLM might hallucinate an entity type outside the schema; we drop those
        client = _ScriptedClient(
            [
                _success_response(
                    [
                        {"start": 0, "end": 4, "entity": "YIL", "text": "2023"},
                        {"start": 5, "end": 10, "entity": "FOOBAR", "text": "foooo"},
                    ]
                )
            ]
        )
        result = label_paragraph("p1", "2023 fooooo", client=client)
        assert len(result.spans) == 1
        assert result.spans[0].entity == "YIL"

    def test_drops_invalid_offsets(self) -> None:
        # end <= start, missing text, missing offsets — all dropped
        client = _ScriptedClient(
            [
                _success_response(
                    [
                        {"start": 5, "end": 5, "entity": "YIL", "text": ""},  # zero-width
                        {"start": 10, "end": 4, "entity": "YIL", "text": "x"},  # reversed
                        {"entity": "YIL", "text": "2023"},  # missing offsets
                        {"start": 0, "end": 4, "entity": "YIL", "text": "2023"},  # ok
                    ]
                )
            ]
        )
        result = label_paragraph("p1", "2023 başlık", client=client)
        assert len(result.spans) == 1


class TestRetryAndFailure:
    def test_retries_on_invalid_json(self) -> None:
        bad = _FakeResponse(
            content=[_FakeBlock(text="not valid json {")],
            usage=_FakeUsage(input_tokens=100, output_tokens=10),
        )
        good = _success_response(
            [{"start": 0, "end": 4, "entity": "YIL", "text": "2023"}]
        )
        client = _ScriptedClient([bad, good])
        result = label_paragraph(
            "p1", "2023", client=client, max_retries=2, backoff_seconds=0
        )
        assert result.succeeded
        assert result.retries == 1
        assert len(result.spans) == 1

    def test_gives_up_after_max_retries(self) -> None:
        bad = _FakeResponse(
            content=[_FakeBlock(text="still not json")],
            usage=_FakeUsage(input_tokens=100, output_tokens=10),
        )
        client = _ScriptedClient([bad, bad, bad])
        result = label_paragraph(
            "p1", "2023", client=client, max_retries=2, backoff_seconds=0
        )
        assert not result.succeeded
        assert result.error is not None
        assert result.spans == []

    def test_retries_on_exception(self) -> None:
        good = _success_response(
            [{"start": 0, "end": 4, "entity": "YIL", "text": "2023"}]
        )
        client = _ScriptedClient([RuntimeError("rate limited"), good])
        result = label_paragraph(
            "p1", "2023", client=client, max_retries=2, backoff_seconds=0
        )
        assert result.succeeded
        assert result.retries == 1


class TestCostTracking:
    def test_cost_calculation(self) -> None:
        # 1M input + 1M output should equal the published rate sum
        response = _FakeResponse(
            content=[_FakeBlock(text="[]")],
            usage=_FakeUsage(input_tokens=1_000_000, output_tokens=1_000_000),
        )
        client = _ScriptedClient([response])
        result = label_paragraph("p1", "x", client=client)
        expected = HAIKU_INPUT_COST_PER_MTOK + HAIKU_OUTPUT_COST_PER_MTOK
        assert abs(result.cost_usd - expected) < 1e-9

    def test_stats_accumulator(self) -> None:
        stats = LLMLabelerStats()
        stats.record_call(input_tokens=200, output_tokens=50, success=True)
        stats.record_call(input_tokens=300, output_tokens=80, success=False)
        assert stats.calls == 2
        assert stats.successful_calls == 1
        assert stats.failed_calls == 1
        assert stats.input_tokens == 500
        assert stats.output_tokens == 130
        # Cost in dollars; both calls combined
        expected_cost = (
            500 / 1_000_000 * HAIKU_INPUT_COST_PER_MTOK
            + 130 / 1_000_000 * HAIKU_OUTPUT_COST_PER_MTOK
        )
        assert abs(stats.cost_usd - expected_cost) < 1e-9

    def test_stats_to_dict_serializable(self) -> None:
        stats = LLMLabelerStats()
        stats.record_call(input_tokens=200, output_tokens=50, success=True)
        d = stats.to_dict()
        assert json.dumps(d)  # round-trips through JSON


class TestEdgeCases:
    def test_empty_response_returns_zero_spans(self) -> None:
        client = _ScriptedClient([_success_response([])])
        result = label_paragraph("p1", "no entities here", client=client)
        assert result.succeeded
        assert result.spans == []

    def test_non_array_top_level_fails(self) -> None:
        # LLM returned an object instead of array; should fail and retry
        bad = _FakeResponse(
            content=[_FakeBlock(text='{"not": "an array"}')],
            usage=_FakeUsage(input_tokens=100, output_tokens=10),
        )
        client = _ScriptedClient([bad])
        result = label_paragraph(
            "p1", "x", client=client, max_retries=0, backoff_seconds=0
        )
        assert not result.succeeded


def test_get_default_client_raises_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_default_client should error clearly if API key is missing."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from data.labeling.llm_label import get_default_client  # noqa: PLC0415

    # Either the SDK isn't installed (ImportError-wrapped RuntimeError) or
    # the key is missing (RuntimeError); both are acceptable failure modes
    # because both prevent live calls.
    with pytest.raises(RuntimeError):
        get_default_client()
