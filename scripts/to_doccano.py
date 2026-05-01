"""Convert merged labeled JSONL into Doccano import format.

Doccano sequence-labeling import shape (one record per line)::

    {"text": "...", "label": [[start, end, "ENTITY_TYPE"], ...]}

We pull paragraph text + best-available LLM annotations (from the merged
``cli-haiku-2k.jsonl``) and write the Doccano file. The user opens
Doccano, imports this JSONL, then edits the pre-fills — far faster than
labeling from scratch.

Turkish-character entity names (``DERGİ`` / ``METRİK``) are normalized
to ASCII (``DERGI`` / ``METRIK``) by default to avoid Doccano label
config quirks. Pass ``--keep-turkish`` to disable.

Usage::

    python scripts/to_doccano.py \\
        --paragraphs data/corpora/smoke-2k/paragraphs-300-gold.jsonl \\
        --labeled docs/labeler-eval/cli-haiku-2k.jsonl \\
        --output data/corpora/smoke-2k/paragraphs-300-doccano-import.jsonl
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ASCII_ENTITY_MAP = {
    "DERGİ": "DERGI",
    "METRİK": "METRIK",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paragraphs", type=Path, required=True)
    parser.add_argument("--labeled", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--keep-turkish",
        action="store_true",
        help="Keep DERGİ / METRİK with Turkish chars (default: ASCII-fold).",
    )
    parser.add_argument(
        "--no-prelabels",
        action="store_true",
        help="Import paragraphs WITHOUT any LLM labels — start from blank.",
    )
    args = parser.parse_args()

    # Load LLM labels keyed by paragraph_id
    label_index: dict[str, list[dict]] = {}
    with args.labeled.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get("succeeded"):
                label_index[str(record["paragraph_id"])] = record.get("spans", [])

    # Iterate sampled paragraphs and emit Doccano records
    written = 0
    skipped_no_text = 0
    label_counter: dict[str, int] = {}

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.paragraphs.open(encoding="utf-8") as src, args.output.open(
        "w", encoding="utf-8"
    ) as dst:
        for line in src:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            text = record.get("text") or ""
            if not text:
                skipped_no_text += 1
                continue
            paragraph_id = str(record["paragraph_id"])

            labels: list[list] = []
            if not args.no_prelabels:
                spans = label_index.get(paragraph_id, [])
                for span in spans:
                    try:
                        start = int(span["start"])
                        end = int(span["end"])
                    except (KeyError, TypeError, ValueError):
                        continue
                    if end <= start or end > len(text) or start < 0:
                        continue
                    entity = span.get("entity", "")
                    if not args.keep_turkish:
                        entity = ASCII_ENTITY_MAP.get(entity, entity)
                    if not entity:
                        continue
                    labels.append([start, end, entity])
                    label_counter[entity] = label_counter.get(entity, 0) + 1

            doccano_record = {
                "text": text,
                "label": labels,
                # Optional metadata so Doccano UI shows the original ID
                "meta": {"paragraph_id": paragraph_id},
            }
            dst.write(json.dumps(doccano_record, ensure_ascii=False) + "\n")
            written += 1

    print(f"Wrote {written:,} records -> {args.output}")
    if skipped_no_text:
        print(f"Skipped {skipped_no_text} records with empty text.")
    if label_counter:
        print(f"Pre-label counts: {label_counter}")
    else:
        print("No pre-labels written (either --no-prelabels or no matches).")


if __name__ == "__main__":
    main()
