"""Merge multiple labeling-pass JSONL files into a single dedup'd output.

Each input file is the output of a labeling pipeline (CLI batch, API batch,
or single-paragraph recovery). For every ``paragraph_id`` across all
inputs, we keep:

    1. The most recent ``succeeded=true`` record, if any exists; OR
    2. The first ``succeeded=false`` record otherwise (so failures stay
       visible in the output).

This is needed because the labeling pipeline appends records as it runs;
a paragraph that failed in pass 1 and succeeded in pass 3 ends up with
both records on disk. The merge picks the success.

Usage::

    python scripts/merge_labeled.py docs/labeler-eval/cli-haiku-A.jsonl \\
        docs/labeler-eval/api-haiku-B.jsonl \\
        --output docs/labeler-eval/cli-haiku-2k.jsonl
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    merged: dict[str, dict] = {}
    line_count = 0
    per_input_lines: dict[str, int] = {}

    for path in args.inputs:
        per_input_lines[str(path)] = 0
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                line_count += 1
                per_input_lines[str(path)] += 1
                record = json.loads(line)
                paragraph_id = str(record.get("paragraph_id", ""))
                if not paragraph_id:
                    continue
                existing = merged.get(paragraph_id)
                # Prefer succeeded=true over false; among multiple successes
                # prefer the LAST one (latest pass).
                if existing is None:
                    merged[paragraph_id] = record
                elif record.get("succeeded") and not existing.get("succeeded"):
                    merged[paragraph_id] = record
                elif record.get("succeeded") and existing.get("succeeded"):
                    merged[paragraph_id] = record  # later pass wins

    # Stats
    ok = sum(1 for r in merged.values() if r.get("succeeded"))
    fail = sum(1 for r in merged.values() if not r.get("succeeded"))
    entity_counter: Counter[str] = Counter()
    total_entities = 0
    for r in merged.values():
        if r.get("succeeded"):
            for s in r.get("spans", []):
                entity_counter[s["entity"]] += 1
                total_entities += 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as out_handle:
        # Write in deterministic order — sort by paragraph_id
        for paragraph_id in sorted(merged):
            out_handle.write(json.dumps(merged[paragraph_id], ensure_ascii=False) + "\n")

    print(f"Inputs scanned: {line_count} total lines")
    for path, n in per_input_lines.items():
        print(f"  {path}: {n} lines")
    print(f"Merged: {len(merged)} unique paragraph_ids -> {args.output}")
    print(f"  Succeeded: {ok}")
    print(f"  Failed: {fail}")
    print(f"  Total entities: {total_entities}")
    print(f"  Entity distribution:")
    for entity, count in entity_counter.most_common():
        print(f"    {entity}: {count}")


if __name__ == "__main__":
    main()
