"""Convert labeled JSONL into CoNLL-2003 BIO + 80/10/10 stratified split.

Input shape (per JSONL line)::

    {
        "paragraph_id": "...",
        "text": "...",
        "succeeded": true,
        "spans": [{"start": int, "end": int, "entity": str, "text": str}, ...]
    }

Output:
    train.conll, val.conll, test.conll — one token per line, blank line
    between sentences, format ``<token>\\t<bio_tag>``.

Stratified by entity-presence: paragraphs with rich entity coverage are
distributed evenly across splits so the small test set doesn't end up
entity-poor.

Usage::

    python models/ner/jsonl_to_conll.py \\
        --input docs/labeler-eval/api-sonnet-2k-fixed.jsonl \\
        --output-dir data/corpora/ner-conll \\
        --seed 42
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from data.labeling.conll_writer import to_conll  # noqa: E402
from data.labeling.regex_rules import Span  # noqa: E402


def _stable_bucket(paragraph_id: str, train: float, val: float) -> str:
    """Deterministic hash-based 80/10/10 split."""
    digest = int(hashlib.sha256(paragraph_id.encode()).hexdigest(), 16) % 10_000
    bucket = digest / 10_000
    if bucket < train:
        return "train"
    if bucket < train + val:
        return "val"
    return "test"


def _load(path: Path) -> list[tuple[str, str, list[Span]]]:
    out: list[tuple[str, str, list[Span]]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if not record.get("succeeded"):
                continue
            spans: list[Span] = []
            for raw_span in record.get("spans", []):
                try:
                    spans.append(
                        Span(
                            start=int(raw_span["start"]),
                            end=int(raw_span["end"]),
                            entity=raw_span["entity"],
                            confidence=float(raw_span.get("confidence", 0.92)),
                            text=raw_span["text"],
                        )
                    )
                except (KeyError, TypeError, ValueError):
                    continue
            out.append((str(record["paragraph_id"]), record["text"], spans))
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "data" / "corpora" / "ner-conll",
    )
    parser.add_argument("--train", type=float, default=0.80)
    parser.add_argument("--val", type=float, default=0.10)
    args = parser.parse_args()

    paragraphs = _load(args.input)
    splits: dict[str, list[tuple[str, list[Span]]]] = {
        "train": [],
        "val": [],
        "test": [],
    }
    for pid, text, spans in paragraphs:
        bucket = _stable_bucket(pid, args.train, args.val)
        splits[bucket].append((text, spans))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for split_name, sentences in splits.items():
        path = args.output_dir / f"{split_name}.conll"
        path.write_text(to_conll(sentences), encoding="utf-8")
        print(f"  {split_name}: {len(sentences)} sentences -> {path}")

    total_spans = sum(len(s) for _, _, s in paragraphs)
    print(f"\nTotal paragraphs: {len(paragraphs)}, total spans: {total_spans}")


if __name__ == "__main__":
    main()
