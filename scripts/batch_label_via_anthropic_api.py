"""Faz 2 batch labeling via the Anthropic Messages API directly.

Drop-in replacement for ``batch_label_via_claude_cli.py`` that bypasses
the Claude Code CLI subprocess (which gets billed against the user's
Pro/Max usage window) and instead hits the Anthropic Messages API
directly with an ``ANTHROPIC_API_KEY``. ~40× cheaper for this workload
(no CLI startup, no Pro/Max overage, just metered token billing).

Reads ``ANTHROPIC_API_KEY`` from the environment or the project ``.env``
file. Resume-safe: appends to the output JSONL and skips paragraph IDs
that already have a ``succeeded=true`` record.

Usage::

    python scripts/batch_label_via_anthropic_api.py \\
        --paragraphs data/corpora/smoke-2k/paragraphs-B.jsonl \\
        --output docs/labeler-eval/api-haiku-B.jsonl \\
        --batch-size 30
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.labeling.entity_types import ENTITY_TYPES  # noqa: E402
from data.labeling.llm_label import (  # noqa: E402
    DEFAULT_HAIKU_MODEL,
    HAIKU_INPUT_COST_PER_MTOK,
    HAIKU_OUTPUT_COST_PER_MTOK,
    LLMLabelerStats,
    _parse_spans,
)

# Reuse the batch prompt + parser from the CLI script — keeps both paths
# semantically identical so output formats are interchangeable.
from scripts.batch_label_via_claude_cli import (  # noqa: E402
    BATCH_SYSTEM_PROMPT,
    _format_batch_prompt,
    _parse_batch_response,
)


def _load_env(env_path: Path) -> None:
    """Tiny KEY=VALUE parser; doesn't depend on python-dotenv."""
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and value and key not in os.environ:
            os.environ[key] = value


def _read_paragraphs(path: Path) -> list[tuple[str, str]]:
    paragraphs: list[tuple[str, str]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            paragraphs.append((str(record["paragraph_id"]), record["text"]))
    return paragraphs


def _read_completed_ids(output_path: Path) -> set[str]:
    if not output_path.exists():
        return set()
    completed: set[str] = set()
    with output_path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("succeeded"):
                completed.add(str(record.get("paragraph_id", "")))
    return completed


def _extract_response_text(response: object) -> str:
    """Pull the first text block from an Anthropic Messages response."""
    for block in getattr(response, "content", []):
        text = getattr(block, "text", None)
        if isinstance(text, str):
            return text
    raise ValueError("No text block in response")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch NER labeling via Anthropic Messages API (direct, billable per-token)",
    )
    parser.add_argument("--paragraphs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default=DEFAULT_HAIKU_MODEL)
    parser.add_argument(
        "--batch-size",
        type=int,
        default=30,
        help="Paragraphs per API call (default: 30). Higher = fewer calls but a bad JSON response fails the whole batch.",
    )
    parser.add_argument(
        "--pause-seconds",
        type=float,
        default=0.5,
        help="Sleep between API calls (default: 0.5s) — prevents accidental bursts above the rate limit.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=4096,
        help="Max output tokens per call (default: 4096) — enough for ~30 paragraphs of compact spans JSON.",
    )
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    args = parser.parse_args()

    _load_env(args.env_file)
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "ERROR: ANTHROPIC_API_KEY not set. Add it to .env or export it before running.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        from anthropic import Anthropic
    except ImportError:
        print(
            "ERROR: `anthropic` package not installed. Run: pip install anthropic",
            file=sys.stderr,
        )
        sys.exit(1)

    client = Anthropic(api_key=api_key)

    paragraphs = _read_paragraphs(args.paragraphs)
    completed = _read_completed_ids(args.output)
    pending = [(pid, text) for pid, text in paragraphs if pid not in completed]
    print(
        f"[api] Total: {len(paragraphs)}, "
        f"already done: {len(completed)}, "
        f"pending: {len(pending)}",
    )
    print(f"[api] Model: {args.model}")
    print(f"[api] Batch size: {args.batch_size}")

    args.output.parent.mkdir(parents=True, exist_ok=True)

    stats = LLMLabelerStats()
    success_count = 0
    failure_count = 0
    total_batches = (len(pending) + args.batch_size - 1) // args.batch_size

    with args.output.open("a", encoding="utf-8") as out_handle:
        for batch_idx, batch_start in enumerate(
            range(0, len(pending), args.batch_size),
            start=1,
        ):
            batch = pending[batch_start : batch_start + args.batch_size]
            user_prompt = _format_batch_prompt(batch)
            try:
                start = time.monotonic()
                response = client.messages.create(
                    model=args.model,
                    max_tokens=args.max_tokens,
                    system=BATCH_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                elapsed = time.monotonic() - start

                text_response = _extract_response_text(response)
                usage = response.usage
                in_tok = int(getattr(usage, "input_tokens", 0))
                out_tok = int(getattr(usage, "output_tokens", 0))
                cost = (
                    in_tok / 1_000_000 * HAIKU_INPUT_COST_PER_MTOK
                    + out_tok / 1_000_000 * HAIKU_OUTPUT_COST_PER_MTOK
                )
                stats.record_call(in_tok, out_tok, cost, success=True)

                parsed_items = _parse_batch_response(text_response)
                by_id = {
                    str(item.get("paragraph_id", "")): item
                    for item in parsed_items
                    if isinstance(item, dict)
                }

                batch_success = 0
                batch_entities = 0
                for paragraph_id, text in batch:
                    item = by_id.get(paragraph_id)
                    if item is None:
                        failure_count += 1
                        out_handle.write(
                            json.dumps(
                                {
                                    "paragraph_id": paragraph_id,
                                    "text": text,
                                    "succeeded": False,
                                    "model": args.model,
                                    "elapsed_seconds": 0.0,
                                    "raw_response": "",
                                    "spans": [],
                                    "error": "paragraph_id missing in batch response",
                                },
                                ensure_ascii=False,
                            )
                            + "\n",
                        )
                        continue

                    item_json = json.dumps(item.get("spans", []), ensure_ascii=False)
                    spans = _parse_spans(item_json, ENTITY_TYPES)
                    out_handle.write(
                        json.dumps(
                            {
                                "paragraph_id": paragraph_id,
                                "text": text,
                                "succeeded": True,
                                "model": args.model,
                                "elapsed_seconds": round(elapsed / max(1, len(batch)), 2),
                                "raw_response": item_json,
                                "spans": [
                                    {
                                        "start": s.start,
                                        "end": s.end,
                                        "entity": s.entity,
                                        "text": s.text,
                                        "confidence": s.confidence,
                                    }
                                    for s in spans
                                ],
                                "error": None,
                            },
                            ensure_ascii=False,
                        )
                        + "\n",
                    )
                    success_count += 1
                    batch_success += 1
                    batch_entities += len(spans)

                out_handle.flush()
                print(
                    f"  [api] {batch_idx}/{total_batches} ({len(batch)}p) -> "
                    f"{batch_success} ok, {batch_entities} entities, "
                    f"{elapsed:.1f}s, ${cost:.4f} "
                    f"(running total: ${stats.cost_usd:.4f})"
                )
            except Exception as exc:  # noqa: BLE001
                stats.record_call(0, 0, 0.0, success=False)
                error_msg = f"{type(exc).__name__}: {exc}"
                for paragraph_id, text in batch:
                    failure_count += 1
                    out_handle.write(
                        json.dumps(
                            {
                                "paragraph_id": paragraph_id,
                                "text": text,
                                "succeeded": False,
                                "model": args.model,
                                "elapsed_seconds": 0.0,
                                "raw_response": "",
                                "spans": [],
                                "error": f"batch failure: {error_msg}",
                            },
                            ensure_ascii=False,
                        )
                        + "\n",
                    )
                out_handle.flush()
                print(f"  [api] {batch_idx}/{total_batches} FAIL — {error_msg[:200]}")
            if batch_idx < total_batches:
                time.sleep(args.pause_seconds)

    print()
    print(f"[api] Done. Success: {success_count}, Fail: {failure_count}")
    print(f"[api] Total cost: ${stats.cost_usd:.4f}")
    print(f"[api] Total tokens: {stats.input_tokens:,} in, {stats.output_tokens:,} out")


if __name__ == "__main__":
    main()
