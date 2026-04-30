"""LLM-based academic NER labeling via Claude Haiku 3.5.

Implements stage 2 of the semi-automatic labeling pipeline (Requirement 4.3
revised v2.4): Claude Haiku 3.5 produces full BIO annotations for paragraph
text; the human reviewer then accepts or edits each annotation (Requirement
4.4 revised v2.4 — "human-in-the-loop", ~100 hours total over 30K paragraphs).

Pattern reference: UniversalNER (Zhou et al., NeurIPS 2023). Cost target:
~$10-20 over the full corpus (~30K paragraphs × ~500 tokens I/O × Haiku
$0.25/$1.25 per million).

Design notes:
    * The Anthropic SDK is a soft dependency. ``label_paragraph`` accepts
      an optional ``client`` to allow offline mock testing without the real
      SDK installed (see ``tests/unit/test_llm_label.py``).
    * Cost tracking is per-call so the pipeline can be paused mid-batch and
      resumed deterministically; ``LLMLabelerStats`` accumulates totals.
    * Output spans match :class:`data.labeling.regex_rules.Span` so the
      regex pre-pass and the LLM pass merge into the same downstream
      writer (:mod:`data.labeling.conll_writer`).
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

from .entity_types import ENTITY_TYPES
from .regex_rules import Span

# Default model id — pinned per-version so research log records what was used.
# When a stronger Haiku ships, bump this and the cost table in learning-log.
DEFAULT_HAIKU_MODEL = "claude-haiku-4-5-20251001"

# Pricing snapshot at v2.4 — used for cost reporting only, not contractual.
HAIKU_INPUT_COST_PER_MTOK = 0.25
HAIKU_OUTPUT_COST_PER_MTOK = 1.25

# Prompt is intentionally short and structured: the lower the token count, the
# cheaper. We rely on Haiku producing valid JSON; failures are retried.
SYSTEM_PROMPT = """You are a precise academic NER annotator for Turkish academic text.

You output ONLY a JSON array. Each element is an object with these exact keys:
- "start": integer character offset of the entity start in the input text
- "end": integer character offset of the entity end (exclusive)
- "entity": one of "YAZAR", "KURUM", "DERGİ", "YIL", "METODOLOJI", "DATASET", "METRİK"
- "text": the exact substring of the input from start to end

Entity definitions:
- YAZAR: full name of a paper author (any format including "Soyad, Ad" or "A. Soyad")
- KURUM: university, institute, faculty, department, or research center
- DERGİ: journal or conference name
- YIL: 4-digit publication year between 1900 and 2030
- METODOLOJI: machine learning model, algorithm, or scientific method (e.g., CNN, BERT, k-means)
- DATASET: named dataset (e.g., MNIST, IMDB, YÖK Tez Merkezi corpus)
- METRİK: evaluation metric (e.g., F1, ROUGE-L, doğruluk, accuracy)

Output exactly one JSON array. No prose, no explanations, no markdown fences."""

USER_PROMPT_TEMPLATE = """Annotate the following Turkish academic paragraph:

```
{paragraph}
```

Return only the JSON array."""


class _AnthropicMessageLike(Protocol):
    """Subset of the Anthropic Messages response shape we depend on."""

    @property
    def content(self) -> list[Any]: ...

    @property
    def usage(self) -> Any: ...


class _AnthropicClientLike(Protocol):
    """Minimal shape of an Anthropic SDK client for dependency injection."""

    @property
    def messages(self) -> Any: ...


@dataclass
class LLMLabelerStats:
    """Running totals — accumulated across calls in a single batch run."""

    calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    retries: int = 0
    invalid_json_count: int = 0
    paragraphs_with_zero_entities: int = 0

    def record_call(
        self,
        input_tokens: int,
        output_tokens: int,
        success: bool,
    ) -> None:
        self.calls += 1
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.cost_usd += (
            input_tokens / 1_000_000 * HAIKU_INPUT_COST_PER_MTOK
            + output_tokens / 1_000_000 * HAIKU_OUTPUT_COST_PER_MTOK
        )
        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "calls": self.calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": round(self.cost_usd, 4),
            "retries": self.retries,
            "invalid_json_count": self.invalid_json_count,
            "paragraphs_with_zero_entities": self.paragraphs_with_zero_entities,
        }


@dataclass
class LLMLabelResult:
    """Output of one paragraph labeling call."""

    paragraph_id: str
    spans: list[Span]
    raw_response: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    succeeded: bool
    error: str | None = None
    retries: int = 0


def _extract_text(response: _AnthropicMessageLike) -> str:
    """Pull the first text block from an Anthropic Messages response."""
    for block in response.content:
        # The SDK exposes blocks with `.type == "text"` and `.text`; we duck-type
        # so the same code handles real and mock objects.
        text = getattr(block, "text", None)
        if isinstance(text, str):
            return text
    raise ValueError("No text block in response")


def _parse_spans(raw: str, allowed_entities: tuple[str, ...]) -> list[Span]:
    """Convert the JSON-array response into validated ``Span`` objects.

    Raises ``ValueError`` for malformed JSON or unknown entity types.
    """
    raw = raw.strip()
    # Tolerate occasional ```json fences from misbehaving outputs
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].lstrip()
    parsed = json.loads(raw)
    if not isinstance(parsed, list):
        raise ValueError("Expected a JSON array at the top level")

    spans: list[Span] = []
    allowed = set(allowed_entities)
    for item in parsed:
        if not isinstance(item, dict):
            continue
        entity = item.get("entity")
        if entity not in allowed:
            continue
        try:
            start = int(item["start"])
            end = int(item["end"])
        except (KeyError, TypeError, ValueError):
            continue
        if end <= start:
            continue
        text_value = item.get("text")
        if not isinstance(text_value, str):
            continue
        spans.append(
            Span(
                start=start,
                end=end,
                entity=entity,
                # LLM-derived spans share a single confidence baseline; the
                # human review pass replaces this with a reviewer trust score.
                confidence=0.92,
                text=text_value,
            )
        )
    return spans


def label_paragraph(
    paragraph_id: str,
    text: str,
    client: _AnthropicClientLike,
    *,
    model: str = DEFAULT_HAIKU_MODEL,
    max_tokens: int = 1024,
    max_retries: int = 3,
    backoff_seconds: float = 1.0,
    allowed_entities: tuple[str, ...] = ENTITY_TYPES,
) -> LLMLabelResult:
    """Label one paragraph using a Claude Haiku-style messages API.

    Retries on transient errors (network, malformed JSON) up to
    ``max_retries`` times with exponential backoff.
    """
    last_error: str | None = None
    retries_used = 0
    last_response_text = ""
    last_input_tokens = 0
    last_output_tokens = 0

    for attempt in range(max_retries + 1):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": USER_PROMPT_TEMPLATE.format(paragraph=text),
                    }
                ],
            )
            text_response = _extract_text(response)
            usage = response.usage
            in_tok = int(getattr(usage, "input_tokens", 0))
            out_tok = int(getattr(usage, "output_tokens", 0))
            last_response_text = text_response
            last_input_tokens = in_tok
            last_output_tokens = out_tok

            spans = _parse_spans(text_response, allowed_entities)
            cost = (
                in_tok / 1_000_000 * HAIKU_INPUT_COST_PER_MTOK
                + out_tok / 1_000_000 * HAIKU_OUTPUT_COST_PER_MTOK
            )
            return LLMLabelResult(
                paragraph_id=paragraph_id,
                spans=spans,
                raw_response=text_response,
                input_tokens=in_tok,
                output_tokens=out_tok,
                cost_usd=cost,
                succeeded=True,
                # `attempt` is the index of this successful try; if any
                # earlier try failed we want to report it so callers can
                # see retry pressure in the logs.
                retries=attempt,
            )
        except Exception as exc:  # noqa: BLE001 — caller wants every failure as data
            last_error = f"{type(exc).__name__}: {exc}"
            retries_used = attempt
            if attempt == max_retries:
                break
            time.sleep(backoff_seconds * (2**attempt))

    cost = (
        last_input_tokens / 1_000_000 * HAIKU_INPUT_COST_PER_MTOK
        + last_output_tokens / 1_000_000 * HAIKU_OUTPUT_COST_PER_MTOK
    )
    return LLMLabelResult(
        paragraph_id=paragraph_id,
        spans=[],
        raw_response=last_response_text,
        input_tokens=last_input_tokens,
        output_tokens=last_output_tokens,
        cost_usd=cost,
        succeeded=False,
        error=last_error,
        retries=retries_used,
    )


def get_default_client() -> Any:
    """Return a real Anthropic client; raises if SDK / API key missing.

    Callers should pass an explicit ``client`` to :func:`label_paragraph` in
    tests and pipelines to avoid network calls during unit tests.
    """
    try:
        from anthropic import Anthropic  # noqa: PLC0415
    except ImportError as exc:
        raise RuntimeError(
            "The `anthropic` package is required for live LLM labeling. "
            "Install with `pip install anthropic`."
        ) from exc

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY environment variable is not set. "
            "Get a key from https://console.anthropic.com/ and export it before running."
        )
    return Anthropic(api_key=api_key)


__all__ = [
    "DEFAULT_HAIKU_MODEL",
    "HAIKU_INPUT_COST_PER_MTOK",
    "HAIKU_OUTPUT_COST_PER_MTOK",
    "LLMLabelResult",
    "LLMLabelerStats",
    "SYSTEM_PROMPT",
    "USER_PROMPT_TEMPLATE",
    "get_default_client",
    "label_paragraph",
]
