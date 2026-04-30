"""Faz 1 — derive ``tr-thesis-academic-ready`` from upstream.

Reads :data:`UPSTREAM_DATASET_ID` (umutertugrul/turkish-academic-theses-dataset,
CC-BY-4.0) and produces a quality-filtered, NFC-normalized Parquet dataset for
downstream NER labeling, embedding fine-tune, and RAG indexing.

Compliance:
    Requirement 2 (revised v2.3) — dataset derivation, deterministic, attribution.
    Requirement 17 — DERIVATION.md / BENCHMARKS.md attribution chain.

Usage::

    python data/derive/load_umutertugrul.py \\
        --output-dir data/corpora/tr-thesis-academic-ready \\
        --min-abstract-words 50

For a smoke run on a small sample::

    python data/derive/load_umutertugrul.py --sample-n 1000 --streaming
"""
from __future__ import annotations

import argparse
import json
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

UPSTREAM_DATASET_ID = "umutertugrul/turkish-academic-theses-dataset"
UPSTREAM_LICENSE = "CC-BY-4.0"
DOWNSTREAM_DATASET_ID = "hakansabunis/tr-thesis-academic-ready"
FILTER_VERSION = "v1.0"

# Fields preserved verbatim from upstream (Requirement 2.4)
PRESERVED_FIELDS: tuple[str, ...] = (
    "tez_no",
    "pdf_url",
    "title_tr",
    "title_en",
    "author",
    "advisor",
    "location",
    "subject",
    "index",
    "status",
    "degree",
    "language",
    "year",
    "pages",
    "abstract_tr",
    "abstract_en",
)

# Text fields that get Unicode NFC normalization
TEXT_FIELDS: tuple[str, ...] = (
    "title_tr",
    "title_en",
    "abstract_tr",
    "abstract_en",
    "author",
    "advisor",
    "location",
    "subject",
    "index",
)


def normalize_text(text: str | None) -> str | None:
    """Apply Unicode NFC normalization to a text field.

    NFC composes Turkish characters consistently (ç, ğ, ı, ö, ş, ü) regardless
    of upstream encoding. Idempotent: ``normalize_text(normalize_text(x)) ==
    normalize_text(x)``.
    """
    if text is None:
        return None
    return unicodedata.normalize("NFC", text)


def has_valid_abstract(record: dict[str, Any], min_words: int = 50) -> bool:
    """Return True if the Turkish abstract is present and long enough.

    Empty / None / non-string abstracts fail. Word count uses simple whitespace
    split — accurate enough for filtering purposes; precise tokenization
    happens later in the labeling and embedding pipelines.
    """
    abstract = record.get("abstract_tr")
    if not abstract or not isinstance(abstract, str):
        return False
    return len(abstract.split()) >= min_words


def compute_quality_score(record: dict[str, Any]) -> float:
    """Heuristic 0.0-1.0 quality score for downstream sorting / filtering.

    Components:
        * Abstract length (capped at 300 words) — primary signal, weight 0.7
        * Has English abstract — bilingual completeness, weight 0.1
        * Has author — metadata completeness, weight 0.1
        * Has advisor — metadata completeness, weight 0.1
    """
    abstract_tr = record.get("abstract_tr") or ""
    word_count = len(abstract_tr.split()) if isinstance(abstract_tr, str) else 0
    score = min(word_count / 300.0, 1.0) * 0.7

    if record.get("abstract_en"):
        score += 0.1
    if record.get("author"):
        score += 0.1
    if record.get("advisor"):
        score += 0.1

    return min(score, 1.0)


def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    """Project the upstream record onto preserved fields and apply NFC."""
    out: dict[str, Any] = {field: record.get(field) for field in PRESERVED_FIELDS}
    for field in TEXT_FIELDS:
        value = out.get(field)
        if isinstance(value, str):
            out[field] = normalize_text(value)
    return out


def derive(
    upstream_id: str = UPSTREAM_DATASET_ID,
    min_abstract_words: int = 50,
    output_dir: Path = Path("data/corpora/tr-thesis-academic-ready"),
    streaming: bool = False,
    sample_n: int | None = None,
) -> dict[str, Any]:
    """Run the full derivation pipeline. Returns a stats report dict.

    The pipeline is deterministic (Requirement 2.9): same upstream snapshot +
    same filter version produce identical output. We sort the output by
    ``tez_no`` before writing for stable Parquet hashes.
    """
    # Lazy import so unit tests of pure functions don't require the heavy
    # `datasets` dependency.
    from datasets import Dataset, load_dataset  # noqa: PLC0415

    print(f"[derive] Loading {upstream_id} (streaming={streaming}) ...")
    ds = load_dataset(upstream_id, split="train", streaming=streaming)
    if sample_n is not None:
        ds = ds.take(sample_n) if streaming else ds.select(range(min(sample_n, len(ds))))

    derived_at = datetime.now(timezone.utc).isoformat()
    stats: dict[str, Any] = {
        "upstream_id": upstream_id,
        "upstream_license": UPSTREAM_LICENSE,
        "downstream_id": DOWNSTREAM_DATASET_ID,
        "filter_version": FILTER_VERSION,
        "min_abstract_words": min_abstract_words,
        "derived_at": derived_at,
        "input_records": 0,
        "output_records": 0,
        "drops": Counter(),
        "year_distribution": Counter(),
        "subject_distribution": Counter(),
        "_abstract_words": [],  # list for percentile compute, dropped from final report
    }

    output_records: list[dict[str, Any]] = []
    seen_tez_no: set[Any] = set()

    for record in ds:
        stats["input_records"] += 1

        # Filter 1: duplicate tez_no
        tez_no = record.get("tez_no")
        if tez_no is not None and tez_no in seen_tez_no:
            stats["drops"]["duplicate_tez_no"] += 1
            continue
        if tez_no is not None:
            seen_tez_no.add(tez_no)

        # Filter 2: empty / short abstract
        if not has_valid_abstract(record, min_abstract_words):
            abstract = record.get("abstract_tr")
            stats["drops"]["empty_abstract" if not abstract else "short_abstract"] += 1
            continue

        # Normalize + augment
        normalized = normalize_record(record)
        normalized["quality_score"] = compute_quality_score(normalized)
        normalized["derived_at"] = derived_at
        normalized["filter_version"] = FILTER_VERSION

        output_records.append(normalized)
        stats["output_records"] += 1

        # Distribution tracking
        if normalized.get("year") is not None:
            stats["year_distribution"][normalized["year"]] += 1
        if normalized.get("subject"):
            stats["subject_distribution"][normalized["subject"]] += 1
        abstract_tr = normalized.get("abstract_tr") or ""
        stats["_abstract_words"].append(len(abstract_tr.split()))

    # Determinism: sort by tez_no before write
    output_records.sort(key=lambda r: (r.get("tez_no") or 0, r.get("title_tr") or ""))

    output_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = output_dir / "data.parquet"
    out_ds = Dataset.from_list(output_records)
    out_ds.to_parquet(parquet_path)
    print(f"[derive] Wrote {len(output_records):,} records → {parquet_path}")

    # Build final report (drop internal helper field)
    word_lengths = stats.pop("_abstract_words")
    if word_lengths:
        sorted_lengths = sorted(word_lengths)
        n = len(sorted_lengths)
        stats["abstract_word_percentiles"] = {
            "p25": sorted_lengths[n // 4],
            "p50": sorted_lengths[n // 2],
            "p75": sorted_lengths[(3 * n) // 4],
            "p99": sorted_lengths[min(n - 1, (99 * n) // 100)],
        }
    stats["drops"] = dict(stats["drops"])
    stats["year_distribution"] = dict(sorted(stats["year_distribution"].items()))
    stats["subject_distribution"] = dict(stats["subject_distribution"].most_common(20))

    report_path = output_dir / "derivation_report.json"
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(stats, handle, indent=2, ensure_ascii=False)
    print(f"[derive] Report → {report_path}")

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Derive tr-thesis-academic-ready from "
            "umutertugrul/turkish-academic-theses-dataset (CC-BY-4.0)"
        ),
    )
    parser.add_argument("--upstream", default=UPSTREAM_DATASET_ID)
    parser.add_argument("--min-abstract-words", type=int, default=50)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/corpora/tr-thesis-academic-ready"),
    )
    parser.add_argument(
        "--streaming",
        action="store_true",
        help="Use streaming load (lower RAM, recommended on first run)",
    )
    parser.add_argument(
        "--sample-n",
        type=int,
        default=None,
        help="Sample first N records (for smoke testing the pipeline)",
    )
    args = parser.parse_args()

    stats = derive(
        upstream_id=args.upstream,
        min_abstract_words=args.min_abstract_words,
        output_dir=args.output_dir,
        streaming=args.streaming,
        sample_n=args.sample_n,
    )
    print("\n[derive] Summary")
    print(f"  Input records:  {stats['input_records']:,}")
    print(f"  Output records: {stats['output_records']:,}")
    print(f"  Drop reasons:   {stats['drops']}")
    if "abstract_word_percentiles" in stats:
        print(f"  Abstract length percentiles: {stats['abstract_word_percentiles']}")


if __name__ == "__main__":
    main()
