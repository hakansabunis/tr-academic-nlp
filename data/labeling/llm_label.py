"""LLM-based academic NER labeling — provider-agnostic.

Stage 2 of the semi-automatic labeling pipeline (Requirement 4.3 revised v2.4):
an LLM produces full BIO annotations for each paragraph; the human reviewer
then accepts or edits each annotation (Requirement 4.4 revised v2.4 — full
human-in-the-loop review of every paragraph).

Two providers ship out of the box:

    * :class:`AnthropicLabeler` — Claude Haiku 3.5 (paid, ~$0.25/$1.25 per MTOK).
    * :class:`GeminiLabeler` — Gemini 2.5 Flash (free tier: 1500 req/day, paid
      tier ~$0.30/$2.50 per MTOK). Recommended default for this project.

Both implement :class:`BaseLabeler`. Adding a third provider (OpenAI,
OpenRouter, etc.) is a 30-line subclass.

Pattern reference: UniversalNER (Zhou et al., NeurIPS 2023).

Design notes:
    * SDKs are soft dependencies: each labeler accepts an injectable
      ``client`` so unit tests can pass a fake without installing real SDKs.
    * Cost tracking is per-call so a batch can be paused mid-run and resumed
      deterministically. :class:`LLMLabelerStats` accumulates totals.
    * Output spans match :class:`data.labeling.regex_rules.Span` so the
      regex pre-pass and the LLM pass merge into the same downstream
      CoNLL writer (:mod:`data.labeling.conll_writer`).
"""
from __future__ import annotations

import json
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from .entity_types import ENTITY_TYPES
from .regex_rules import Span

# ---------------------------------------------------------------------------
# Provider model identifiers + pricing (snapshot at v2.4)
# ---------------------------------------------------------------------------
DEFAULT_HAIKU_MODEL = "claude-haiku-4-5-20251001"
HAIKU_INPUT_COST_PER_MTOK = 0.25
HAIKU_OUTPUT_COST_PER_MTOK = 1.25

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_INPUT_COST_PER_MTOK = 0.30
GEMINI_OUTPUT_COST_PER_MTOK = 2.50

# ---------------------------------------------------------------------------
# Prompts (shared across providers — vendor-neutral plain text)
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Stats + result dataclasses
# ---------------------------------------------------------------------------
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
        cost_usd: float,
        success: bool,
    ) -> None:
        self.calls += 1
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.cost_usd += cost_usd
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
    provider: str = ""
    error: str | None = None
    retries: int = 0


# ---------------------------------------------------------------------------
# Provider abstraction
# ---------------------------------------------------------------------------
class BaseLabeler(ABC):
    """Provider-agnostic interface for an LLM-based labeler.

    Subclasses wrap a vendor SDK and implement :meth:`call_api` returning the
    raw text response plus token counts. The shared ``label_paragraph`` driver
    handles retries, parsing, span validation, and cost accounting.
    """

    #: short identifier used in result metadata + cost reports
    name: str = "abstract"

    @abstractmethod
    def call_api(self, system_prompt: str, user_prompt: str) -> tuple[str, int, int]:
        """Send a prompt to the underlying provider.

        Returns ``(text_response, input_tokens, output_tokens)``. Implementations
        SHOULD raise on transport errors so the retry loop in
        :func:`label_paragraph` can catch and back off.
        """

    @abstractmethod
    def cost_usd(self, input_tokens: int, output_tokens: int) -> float:
        """Convert a token count into a dollar cost for THIS provider."""


class AnthropicLabeler(BaseLabeler):
    """Claude Haiku 3.5 NER labeler.

    The injected ``client`` only needs to expose ``client.messages.create(...)``
    matching the Anthropic SDK shape. Mock clients in tests satisfy this with
    a few lines of dataclass code.
    """

    name = "anthropic-haiku"

    def __init__(
        self,
        client: Any,
        model: str = DEFAULT_HAIKU_MODEL,
        max_tokens: int = 1024,
    ) -> None:
        self.client = client
        self.model = model
        self.max_tokens = max_tokens

    def call_api(self, system_prompt: str, user_prompt: str) -> tuple[str, int, int]:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = ""
        for block in response.content:
            block_text = getattr(block, "text", None)
            if isinstance(block_text, str):
                text = block_text
                break
        if not text:
            raise ValueError("No text block in Anthropic response")
        usage = response.usage
        in_tok = int(getattr(usage, "input_tokens", 0))
        out_tok = int(getattr(usage, "output_tokens", 0))
        return text, in_tok, out_tok

    def cost_usd(self, input_tokens: int, output_tokens: int) -> float:
        return (
            input_tokens / 1_000_000 * HAIKU_INPUT_COST_PER_MTOK
            + output_tokens / 1_000_000 * HAIKU_OUTPUT_COST_PER_MTOK
        )


class GeminiLabeler(BaseLabeler):
    """Gemini 2.5 Flash NER labeler — recommended default (free tier available).

    The injected ``client`` only needs to expose
    ``client.models.generate_content(...)`` matching the google-genai SDK
    shape. Mock clients in tests satisfy this with a few lines.
    """

    name = "gemini-flash"

    def __init__(
        self,
        client: Any,
        model: str = DEFAULT_GEMINI_MODEL,
    ) -> None:
        self.client = client
        self.model = model

    def call_api(self, system_prompt: str, user_prompt: str) -> tuple[str, int, int]:
        # The google-genai SDK uses `types.GenerateContentConfig`; we import
        # lazily so unit tests with mock clients don't require the SDK.
        try:
            from google.genai import types as _types  # noqa: PLC0415

            config: Any = _types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.0,
            )
        except ImportError:
            # Mock/test path — pass a dict that the fake client can read
            config = {
                "system_instruction": system_prompt,
                "response_mime_type": "application/json",
                "temperature": 0.0,
            }

        response = self.client.models.generate_content(
            model=self.model,
            config=config,
            contents=user_prompt,
        )
        text = getattr(response, "text", None)
        if not isinstance(text, str) or not text:
            raise ValueError("No text in Gemini response")
        usage = getattr(response, "usage_metadata", None)
        in_tok = int(getattr(usage, "prompt_token_count", 0)) if usage else 0
        out_tok = int(getattr(usage, "candidates_token_count", 0)) if usage else 0
        return text, in_tok, out_tok

    def cost_usd(self, input_tokens: int, output_tokens: int) -> float:
        return (
            input_tokens / 1_000_000 * GEMINI_INPUT_COST_PER_MTOK
            + output_tokens / 1_000_000 * GEMINI_OUTPUT_COST_PER_MTOK
        )


# ---------------------------------------------------------------------------
# Span parser (shared)
# ---------------------------------------------------------------------------
def _parse_spans(raw: str, allowed_entities: tuple[str, ...]) -> list[Span]:
    """Convert the JSON-array response into validated ``Span`` objects.

    Raises ``ValueError`` for malformed JSON. Unknown entity types and invalid
    offsets are silently dropped (LLM hallucinations vs network errors get
    different treatments — the retry loop only retries on raised exceptions).
    """
    raw = raw.strip()
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
                confidence=0.92,
                text=text_value,
            )
        )
    return spans


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def label_paragraph(
    paragraph_id: str,
    text: str,
    labeler: BaseLabeler,
    *,
    max_retries: int = 3,
    backoff_seconds: float = 1.0,
    allowed_entities: tuple[str, ...] = ENTITY_TYPES,
) -> LLMLabelResult:
    """Label one paragraph using any :class:`BaseLabeler` implementation.

    Retries on transient errors (network, malformed JSON) up to
    ``max_retries`` times with exponential backoff.
    """
    user_prompt = USER_PROMPT_TEMPLATE.format(paragraph=text)
    last_error: str | None = None
    last_response_text = ""
    last_input_tokens = 0
    last_output_tokens = 0

    for attempt in range(max_retries + 1):
        try:
            text_response, in_tok, out_tok = labeler.call_api(SYSTEM_PROMPT, user_prompt)
            last_response_text = text_response
            last_input_tokens = in_tok
            last_output_tokens = out_tok
            spans = _parse_spans(text_response, allowed_entities)
            return LLMLabelResult(
                paragraph_id=paragraph_id,
                spans=spans,
                raw_response=text_response,
                input_tokens=in_tok,
                output_tokens=out_tok,
                cost_usd=labeler.cost_usd(in_tok, out_tok),
                succeeded=True,
                provider=labeler.name,
                retries=attempt,
            )
        except Exception as exc:  # noqa: BLE001 — caller wants every failure as data
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt == max_retries:
                break
            time.sleep(backoff_seconds * (2**attempt))

    return LLMLabelResult(
        paragraph_id=paragraph_id,
        spans=[],
        raw_response=last_response_text,
        input_tokens=last_input_tokens,
        output_tokens=last_output_tokens,
        cost_usd=labeler.cost_usd(last_input_tokens, last_output_tokens),
        succeeded=False,
        provider=labeler.name,
        error=last_error,
        retries=max_retries,
    )


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------
def get_anthropic_labeler() -> AnthropicLabeler:
    """Return a live :class:`AnthropicLabeler` configured from env vars."""
    try:
        from anthropic import Anthropic  # noqa: PLC0415
    except ImportError as exc:
        raise RuntimeError(
            "The `anthropic` package is required. Install with `pip install anthropic`."
        ) from exc
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY environment variable is not set. "
            "Get a key from https://console.anthropic.com/."
        )
    return AnthropicLabeler(client=Anthropic(api_key=api_key))


def get_gemini_labeler() -> GeminiLabeler:
    """Return a live :class:`GeminiLabeler` configured from env vars."""
    try:
        from google import genai  # noqa: PLC0415
    except ImportError as exc:
        raise RuntimeError(
            "The `google-genai` package is required. Install with `pip install google-genai`."
        ) from exc
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY environment variable is not set. "
            "Get a free key from https://aistudio.google.com/apikey."
        )
    return GeminiLabeler(client=genai.Client(api_key=api_key))


def get_default_labeler(provider: str | None = None) -> BaseLabeler:
    """Return the configured default labeler.

    Selection priority:
        1. ``provider`` argument if given ("gemini" or "anthropic").
        2. ``LABELER_PROVIDER`` environment variable.
        3. Fallback: Gemini (free tier available).
    """
    chosen = (provider or os.environ.get("LABELER_PROVIDER") or "gemini").lower()
    if chosen == "gemini":
        return get_gemini_labeler()
    if chosen == "anthropic":
        return get_anthropic_labeler()
    raise ValueError(
        f"Unknown LLM provider: {chosen!r}. Supported: 'gemini', 'anthropic'."
    )


__all__ = [
    "AnthropicLabeler",
    "BaseLabeler",
    "DEFAULT_GEMINI_MODEL",
    "DEFAULT_HAIKU_MODEL",
    "GEMINI_INPUT_COST_PER_MTOK",
    "GEMINI_OUTPUT_COST_PER_MTOK",
    "GeminiLabeler",
    "HAIKU_INPUT_COST_PER_MTOK",
    "HAIKU_OUTPUT_COST_PER_MTOK",
    "LLMLabelResult",
    "LLMLabelerStats",
    "SYSTEM_PROMPT",
    "USER_PROMPT_TEMPLATE",
    "get_anthropic_labeler",
    "get_default_labeler",
    "get_gemini_labeler",
    "label_paragraph",
]
