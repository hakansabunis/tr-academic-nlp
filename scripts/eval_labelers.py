"""Smoke + comparison tool for the LLM-as-labeler providers.

Runs each requested provider (Gemini and/or Anthropic) over a small set of
Turkish academic paragraphs and emits:

    1. ``docs/labeler-eval-<provider>.json`` — raw per-paragraph results,
       suitable for diffing across runs.
    2. ``docs/labeler-eval-summary.md`` — human-friendly side-by-side report
       with cost totals and entity counts per provider.

Usage::

    # Quick check on the bundled 10 sample paragraphs (no upstream download):
    python scripts/eval_labelers.py --provider gemini --paragraphs scripts/sample_paragraphs.jsonl

    # Full A/B comparison once both keys are in `.env`:
    python scripts/eval_labelers.py --provider both --paragraphs scripts/sample_paragraphs.jsonl

    # Larger run from your own JSONL (one record per line, must include
    # `paragraph_id` and `text` keys):
    python scripts/eval_labelers.py --provider gemini --paragraphs my_paragraphs.jsonl --output-dir docs/eval-2026-04-30

The script reads ``GEMINI_API_KEY`` and ``ANTHROPIC_API_KEY`` from the
environment. Use a ``.env`` file (loaded via ``python-dotenv`` if installed,
or set in your shell before running) — never paste the keys on the command
line.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.labeling.llm_label import (  # noqa: E402
    LLMLabelerStats,
    get_anthropic_labeler,
    get_default_labeler,
    get_gemini_labeler,
    label_paragraph,
)


def _load_env_file(env_path: Path) -> None:
    """Tiny KEY=VALUE parser so we don't depend on python-dotenv."""
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


def _load_paragraphs(path: Path) -> list[tuple[str, str]]:
    paragraphs: list[tuple[str, str]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            paragraphs.append((str(record["paragraph_id"]), record["text"]))
    return paragraphs


def _run_provider(
    provider: str,
    paragraphs: list[tuple[str, str]],
    output_dir: Path,
    pause_seconds: float,
) -> dict[str, Any]:
    """Label every paragraph with a single provider; return summary stats."""
    if provider == "gemini":
        labeler = get_gemini_labeler()
    elif provider == "anthropic":
        labeler = get_anthropic_labeler()
    else:
        labeler = get_default_labeler(provider)

    stats = LLMLabelerStats()
    rows: list[dict[str, Any]] = []
    entity_counter: Counter[str] = Counter()

    print(f"[{provider}] Labeling {len(paragraphs)} paragraphs ...")
    for idx, (paragraph_id, text) in enumerate(paragraphs, start=1):
        result = label_paragraph(paragraph_id, text, labeler=labeler)
        stats.record_call(
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            cost_usd=result.cost_usd,
            success=result.succeeded,
        )
        if not result.spans:
            stats.paragraphs_with_zero_entities += 1
        for span in result.spans:
            entity_counter[span.entity] += 1
        rows.append(
            {
                "paragraph_id": paragraph_id,
                "text": text,
                "succeeded": result.succeeded,
                "error": result.error,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "cost_usd": round(result.cost_usd, 6),
                "spans": [
                    {
                        "start": s.start,
                        "end": s.end,
                        "entity": s.entity,
                        "text": s.text,
                        "confidence": s.confidence,
                    }
                    for s in result.spans
                ],
            }
        )
        flag = "ok" if result.succeeded else "FAIL"
        print(
            f"  [{provider}] {idx}/{len(paragraphs)} {paragraph_id} {flag} "
            f"({len(result.spans)} entities, {result.input_tokens}+{result.output_tokens} tokens)"
        )
        if pause_seconds and idx < len(paragraphs):
            time.sleep(pause_seconds)

    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / f"labeler-eval-{provider}.json"
    with raw_path.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "provider": provider,
                "paragraphs": rows,
                "stats": stats.to_dict(),
                "entity_counts": dict(entity_counter.most_common()),
            },
            handle,
            indent=2,
            ensure_ascii=False,
        )
    print(f"[{provider}] Wrote raw results → {raw_path}")
    return {
        "provider": provider,
        "stats": stats.to_dict(),
        "entity_counts": dict(entity_counter.most_common()),
        "raw_path": str(raw_path),
        "rows": rows,
    }


def _write_markdown_summary(summaries: list[dict[str, Any]], output_dir: Path) -> Path:
    lines: list[str] = ["# Labeler Evaluation Summary", ""]
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    lines.append("")

    # Side-by-side stats table
    lines.append("## Per-provider stats")
    lines.append("")
    headers = [
        "provider",
        "calls",
        "succeeded",
        "failed",
        "input_tokens",
        "output_tokens",
        "cost_usd",
        "zero_entity_paragraphs",
    ]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join(["---"] * len(headers)) + "|")
    for s in summaries:
        stats = s["stats"]
        lines.append(
            "| "
            + " | ".join(
                [
                    s["provider"],
                    str(stats["calls"]),
                    str(stats["successful_calls"]),
                    str(stats["failed_calls"]),
                    str(stats["input_tokens"]),
                    str(stats["output_tokens"]),
                    f"{stats['cost_usd']:.4f}",
                    str(stats["paragraphs_with_zero_entities"]),
                ]
            )
            + " |"
        )
    lines.append("")

    # Entity distribution per provider
    lines.append("## Entity counts")
    lines.append("")
    all_entities = sorted({e for s in summaries for e in s["entity_counts"]})
    lines.append("| entity | " + " | ".join(s["provider"] for s in summaries) + " |")
    lines.append("|---|" + "|".join(["---"] * len(summaries)) + "|")
    for entity in all_entities:
        row = [entity]
        for s in summaries:
            row.append(str(s["entity_counts"].get(entity, 0)))
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")

    # Side-by-side paragraph comparison (only when 2+ providers ran)
    if len(summaries) >= 2:
        lines.append("## Per-paragraph comparison")
        lines.append("")
        for idx, row_a in enumerate(summaries[0]["rows"]):
            paragraph_id = row_a["paragraph_id"]
            lines.append(f"### {paragraph_id}")
            lines.append("")
            lines.append("> " + row_a["text"].replace("\n", " "))
            lines.append("")
            for s in summaries:
                row = next(
                    (r for r in s["rows"] if r["paragraph_id"] == paragraph_id),
                    None,
                )
                if row is None:
                    continue
                lines.append(f"**{s['provider']}** "
                             f"({row['input_tokens']}+{row['output_tokens']} tokens, "
                             f"${row['cost_usd']:.5f}):")
                if not row["spans"]:
                    lines.append("- (no entities)")
                else:
                    for span in row["spans"]:
                        lines.append(
                            f"- `{span['entity']}` \"{span['text']}\" "
                            f"({span['start']}-{span['end']})"
                        )
                lines.append("")

    summary_path = output_dir / "labeler-eval-summary.md"
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[summary] Wrote markdown report → {summary_path}")
    return summary_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare LLM labelers on Turkish academic paragraphs")
    parser.add_argument(
        "--provider",
        choices=["gemini", "anthropic", "both"],
        default="gemini",
    )
    parser.add_argument(
        "--paragraphs",
        type=Path,
        default=ROOT / "scripts" / "sample_paragraphs.jsonl",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "docs" / "labeler-eval",
    )
    parser.add_argument(
        "--pause-seconds",
        type=float,
        default=0.5,
        help="Sleep between calls (Gemini free tier rate-limit kindness)",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=ROOT / ".env",
        help="Path to .env file with GEMINI_API_KEY / ANTHROPIC_API_KEY",
    )
    args = parser.parse_args()

    _load_env_file(args.env_file)
    paragraphs = _load_paragraphs(args.paragraphs)

    providers = ["gemini", "anthropic"] if args.provider == "both" else [args.provider]
    summaries = [
        _run_provider(p, paragraphs, args.output_dir, args.pause_seconds)
        for p in providers
    ]
    _write_markdown_summary(summaries, args.output_dir)

    print("\n=== Final summary ===")
    for s in summaries:
        stats = s["stats"]
        print(
            f"  {s['provider']:<18} "
            f"{stats['successful_calls']}/{stats['calls']} ok, "
            f"${stats['cost_usd']:.4f} total, "
            f"entities={sum(s['entity_counts'].values())}"
        )


if __name__ == "__main__":
    main()
