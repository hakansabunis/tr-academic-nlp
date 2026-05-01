"""Repair offset errors in LLM-labeled JSONL by re-anchoring on text.

The LLM gives correct entity *text* but wildly wrong start/end offsets
(its character counter drifts inside batches and Turkish text). Since the
text strings are accurate, we ignore the LLM's offsets and use
``record_text.find(span_text)`` to recover the correct boundaries —
yielding clean span boundaries (no mid-word cuts).

Usage::

    python scripts/fix_offsets.py \\
        --input docs/labeler-eval/api-sonnet-100.jsonl \\
        --output docs/labeler-eval/api-sonnet-100-fixed.jsonl
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)

    stats: Counter[str] = Counter()
    total_spans = 0
    fixed_spans = 0
    dropped_no_match = 0
    duplicate_text_warnings = 0

    with args.input.open(encoding="utf-8") as src, args.output.open(
        "w", encoding="utf-8"
    ) as dst:
        for line in src:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            text = record.get("text", "")
            new_spans = []

            # Track positions already used so duplicate texts get distinct anchors
            used_positions: list[tuple[int, int]] = []

            for span in record.get("spans", []):
                total_spans += 1
                surface = span.get("text", "")
                entity = span.get("entity", "")
                if not surface or not entity or not text:
                    dropped_no_match += 1
                    continue

                # Find the first occurrence not already claimed by another span
                search_from = 0
                start = -1
                while True:
                    pos = text.find(surface, search_from)
                    if pos < 0:
                        break
                    end_pos = pos + len(surface)
                    overlaps = any(
                        not (end_pos <= s or pos >= e) for s, e in used_positions
                    )
                    if not overlaps:
                        start = pos
                        break
                    search_from = pos + 1

                if start < 0:
                    # Either not found at all OR all occurrences already claimed
                    if surface in text:
                        # Same surface form occurs multiple times and prior spans
                        # consumed all positions — accept the duplicate but flag.
                        start = text.find(surface)
                        duplicate_text_warnings += 1
                    else:
                        dropped_no_match += 1
                        continue

                end = start + len(surface)
                used_positions.append((start, end))
                new_spans.append(
                    {
                        "start": start,
                        "end": end,
                        "entity": entity,
                        "text": surface,
                        "confidence": span.get("confidence", 0.92),
                    }
                )
                fixed_spans += 1
                stats[entity] += 1

            # Sort by start position for deterministic output
            new_spans.sort(key=lambda s: (s["start"], s["end"]))
            record["spans"] = new_spans
            dst.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Total spans:    {total_spans}")
    print(f"Fixed spans:    {fixed_spans}")
    print(f"Dropped (no match in text): {dropped_no_match}")
    print(f"Duplicate-text warnings:    {duplicate_text_warnings}")
    print(f"By entity: {dict(stats.most_common())}")
    print(f"Wrote -> {args.output}")


if __name__ == "__main__":
    main()
