"""Convert a derived ``tr-thesis-academic-ready`` Parquet file into the
``paragraph_id``/``text`` JSONL shape that the labeling pipeline expects.

Usage::

    python scripts/parquet_to_jsonl.py \\
        data/corpora/tr-thesis-academic-ready/data.parquet \\
        data/corpora/tr-thesis-academic-ready/paragraphs.jsonl
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pyarrow.parquet as pq


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("parquet_path", type=Path)
    parser.add_argument("jsonl_path", type=Path)
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional: write only the first N records (for smoke runs)",
    )
    args = parser.parse_args()

    table = pq.read_table(args.parquet_path)
    columns = table.column_names
    if "tez_no" not in columns or "abstract_tr" not in columns:
        raise SystemExit(
            "Expected 'tez_no' and 'abstract_tr' columns; "
            f"got {columns}",
        )

    args.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with args.jsonl_path.open("w", encoding="utf-8") as handle:
        for batch in table.to_batches():
            tez_nos = batch.column("tez_no").to_pylist()
            abstracts = batch.column("abstract_tr").to_pylist()
            for tez_no, abstract in zip(tez_nos, abstracts, strict=True):
                if not abstract:
                    continue
                record = {
                    "paragraph_id": f"tez-{tez_no}",
                    "text": abstract,
                }
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                written += 1
                if args.limit and written >= args.limit:
                    break
            if args.limit and written >= args.limit:
                break

    print(f"Wrote {written:,} records -> {args.jsonl_path}")


if __name__ == "__main__":
    main()
