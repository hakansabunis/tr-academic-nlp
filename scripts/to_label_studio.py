"""Convert sampled paragraphs + LLM annotations into Label Studio import.

Label Studio's "JSON-MIN with predictions" format. The user opens
LS, imports this JSON, then edits the pre-fills.

Usage::

    python scripts/to_label_studio.py \\
        --paragraphs data/corpora/smoke-2k/paragraphs-300-gold.jsonl \\
        --labeled docs/labeler-eval/cli-haiku-2k.jsonl \\
        --output data/corpora/smoke-2k/paragraphs-300-ls-import.json
"""
from __future__ import annotations

import argparse
import json
import uuid
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
        help="Import paragraphs WITHOUT any LLM labels.",
    )
    args = parser.parse_args()

    label_index: dict[str, list[dict]] = {}
    with args.labeled.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get("succeeded"):
                label_index[str(record["paragraph_id"])] = record.get("spans", [])

    items: list[dict] = []
    with args.paragraphs.open(encoding="utf-8") as src:
        for line in src:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            text = record.get("text") or ""
            if not text:
                continue
            paragraph_id = str(record["paragraph_id"])

            results: list[dict] = []
            if not args.no_prelabels:
                for span in label_index.get(paragraph_id, []):
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
                    results.append(
                        {
                            "id": str(uuid.uuid4())[:8],
                            "from_name": "label",
                            "to_name": "text",
                            "type": "labels",
                            "value": {
                                "start": start,
                                "end": end,
                                "text": text[start:end],
                                "labels": [entity],
                            },
                        }
                    )

            item = {
                "data": {"text": text, "paragraph_id": paragraph_id},
            }
            if results:
                item["predictions"] = [{"result": results, "model_version": "haiku-pre"}]
            items.append(item)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as dst:
        json.dump(items, dst, ensure_ascii=False, indent=2)

    pre_count = sum(len(item.get("predictions", [{"result": []}])[0]["result"])
                    for item in items if item.get("predictions"))
    print(f"Wrote {len(items)} tasks -> {args.output}")
    print(f"Total pre-labels: {pre_count}")


if __name__ == "__main__":
    main()
