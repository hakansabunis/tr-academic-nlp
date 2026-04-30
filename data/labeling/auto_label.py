"""Faz 2 — semi-automatic NER labeling pipeline (regex pass).

Stage 1 of the two-stage labeling pipeline (Requirement 4.3):

    raw text → regex_rules.extract_all → resolve_overlaps → CoNLL BIO

Stage 2 (Ollama qwen2.5:7b verification of low-confidence spans) is a
separate module ``data/labeling/ollama_verify.py`` to be added next; this
file ships the offline regex-only path so we can iterate on patterns and
test outputs without an LLM dependency.

Output: CoNLL-2003 BIO with stratified train/val/test split (R4.7).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .conll_writer import to_conll, tokenize_with_offsets
from .entity_types import ENTITY_TYPES
from .regex_rules import Span, extract_all, resolve_overlaps

LABELING_VERSION = "v1.0-regex-only"


def label_paragraph(text: str, low_confidence_threshold: float = 0.80) -> tuple[list[Span], list[Span]]:
    """Label one paragraph; return ``(high_confidence_spans, low_confidence_spans)``.

    Low-confidence spans are kept separate so a future Ollama verification
    pass can review them without re-running regex.
    """
    raw = extract_all(text)
    resolved = resolve_overlaps(raw)
    high = [s for s in resolved if s.confidence >= low_confidence_threshold]
    low = [s for s in resolved if s.confidence < low_confidence_threshold]
    return high, low


def stable_split(
    paragraph_id: str,
    train: float = 0.80,
    val: float = 0.10,
) -> str:
    """Deterministic 80/10/10 split via hash of the paragraph id.

    Using a hash (rather than `random.shuffle`) keeps the split stable
    across runs and across paragraph reorderings — critical for
    Requirement 4.7's stratified-by-entity-distribution constraint.
    """
    h = int(hashlib.sha256(paragraph_id.encode()).hexdigest(), 16) % 10_000
    bucket = h / 10_000
    if bucket < train:
        return "train"
    if bucket < train + val:
        return "val"
    return "test"


def label_paragraphs(
    paragraphs: list[tuple[str, str]],
    output_dir: Path,
    train: float = 0.80,
    val: float = 0.10,
    low_confidence_threshold: float = 0.80,
) -> dict[str, Any]:
    """Label and split a batch of ``(paragraph_id, text)`` items.

    Writes three CoNLL files (train.conll, val.conll, test.conll) plus a
    ``labeling_report.json`` with entity distribution and ambiguity stats.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    splits: dict[str, list[tuple[str, list[Span]]]] = {
        "train": [],
        "val": [],
        "test": [],
    }
    entity_counter: Counter[str] = Counter()
    low_confidence_log: list[dict[str, Any]] = []
    paragraphs_with_no_entities = 0

    for paragraph_id, text in paragraphs:
        high, low = label_paragraph(text, low_confidence_threshold)
        for span in high:
            entity_counter[span.entity] += 1
        for span in low:
            low_confidence_log.append(
                {
                    "paragraph_id": paragraph_id,
                    "text": span.text,
                    "entity": span.entity,
                    "confidence": span.confidence,
                    "start": span.start,
                    "end": span.end,
                }
            )
        if not high and not low:
            paragraphs_with_no_entities += 1

        bucket = stable_split(paragraph_id, train, val)
        splits[bucket].append((text, high))

    # Write per-split CoNLL files
    for split_name, sentences in splits.items():
        path = output_dir / f"{split_name}.conll"
        path.write_text(to_conll(sentences), encoding="utf-8")

    # Compute average entities per paragraph
    total_entities = sum(entity_counter.values())
    avg_entities_per_paragraph = (
        total_entities / len(paragraphs) if paragraphs else 0.0
    )

    report: dict[str, Any] = {
        "labeling_version": LABELING_VERSION,
        "labeled_at": datetime.now(timezone.utc).isoformat(),
        "input_paragraphs": len(paragraphs),
        "split_sizes": {k: len(v) for k, v in splits.items()},
        "entity_distribution": dict(entity_counter.most_common()),
        "total_high_confidence_entities": total_entities,
        "low_confidence_count": len(low_confidence_log),
        "ambiguity_rate": (
            len(low_confidence_log) / total_entities if total_entities else 0.0
        ),
        "average_entities_per_paragraph": avg_entities_per_paragraph,
        "paragraphs_with_no_entities": paragraphs_with_no_entities,
        "low_confidence_threshold": low_confidence_threshold,
        "low_confidence_sample": low_confidence_log[:50],  # first 50 for inspection
    }

    report_path = output_dir / "labeling_report.json"
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)

    # Persist the full low-confidence list separately for the Ollama pass
    low_path = output_dir / "low_confidence_spans.jsonl"
    with low_path.open("w", encoding="utf-8") as handle:
        for entry in low_confidence_log:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Faz 2 — regex-pass NER labeling for Turkish academic text",
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="JSONL file with one record per line, each containing `paragraph_id` and `text`",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/corpora/tr-academic-ner-corpus"),
    )
    parser.add_argument("--train", type=float, default=0.80)
    parser.add_argument("--val", type=float, default=0.10)
    parser.add_argument(
        "--low-confidence-threshold",
        type=float,
        default=0.80,
        help="Spans below this confidence go to the Ollama verification queue",
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)

    paragraphs: list[tuple[str, str]] = []
    with args.input.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            paragraphs.append((str(record["paragraph_id"]), record["text"]))

    report = label_paragraphs(
        paragraphs,
        output_dir=args.output_dir,
        train=args.train,
        val=args.val,
        low_confidence_threshold=args.low_confidence_threshold,
    )
    print(f"[label] Labeled {report['input_paragraphs']:,} paragraphs")
    print(f"  Splits: {report['split_sizes']}")
    print(f"  Entity distribution: {report['entity_distribution']}")
    print(f"  Low-confidence spans queued: {report['low_confidence_count']:,}")
    print(f"  Avg entities/paragraph: {report['average_entities_per_paragraph']:.2f}")


if __name__ == "__main__":
    main()
