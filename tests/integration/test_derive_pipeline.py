"""End-to-end integration test for the Faz 1 derivation pipeline.

Builds a tiny in-memory mock of the upstream dataset structure, runs the
full ``derive()`` pipeline, and verifies the output Parquet plus the
derivation_report.json. Doesn't touch the real upstream dataset (which is
gated and requires HuggingFace authentication).

This proves the pipeline works end-to-end independent of upstream auth.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from data.derive import load_umutertugrul as derive_mod  # noqa: E402


def _make_mock_records() -> list[dict[str, Any]]:
    """Return a fixture set covering every filter branch."""
    return [
        # Valid records (should be kept)
        {
            "tez_no": 1001,
            "pdf_url": "https://tez.yok.gov.tr/UlusalTezMerkezi/...?id=1001",
            "title_tr": "Derin Öğrenme ile Türkçe Akademik NLP",
            "title_en": "Deep Learning for Turkish Academic NLP",
            "author": "Hakan Sabunis",
            "advisor": "Prof. Dr. X",
            "location": "Istanbul Üniversitesi / Fen Bilimleri / Bilgisayar Müh.",
            "subject": "Bilgisayar Mühendisliği",
            "index": "derin öğrenme; doğal dil işleme",
            "status": "Onaylandı",
            "degree": "Yüksek Lisans",
            "language": "Türkçe",
            "year": 2024,
            "pages": 150,
            "abstract_tr": " ".join(["kelime"] * 100),
            "abstract_en": " ".join(["word"] * 100),
        },
        {
            "tez_no": 1002,
            "pdf_url": "https://tez.yok.gov.tr/...?id=1002",
            "title_tr": "Türkçe Soru Cevaplama",
            "title_en": None,
            "author": "Test Yazar",
            "advisor": "Prof. Y",
            "location": "ODTÜ / Mühendislik",
            "subject": "Bilgisayar Mühendisliği",
            "index": "soru-cevap",
            "status": "Onaylandı",
            "degree": "Doktora",
            "language": "Türkçe",
            "year": 2023,
            "pages": 200,
            "abstract_tr": " ".join(["kelime"] * 80),
            "abstract_en": None,
        },
        # Drop: empty abstract
        {
            "tez_no": 1003,
            "title_tr": "Bos Abstract",
            "abstract_tr": "",
            "year": 2022,
        },
        # Drop: short abstract
        {
            "tez_no": 1004,
            "title_tr": "Kisa Abstract",
            "abstract_tr": " ".join(["kelime"] * 10),
            "year": 2022,
        },
        # Drop: duplicate tez_no (same as 1001)
        {
            "tez_no": 1001,
            "title_tr": "Duplicate",
            "abstract_tr": " ".join(["kelime"] * 100),
            "year": 2025,
        },
        # Drop: None abstract
        {
            "tez_no": 1005,
            "title_tr": "None Abstract",
            "abstract_tr": None,
            "year": 2022,
        },
    ]


class _FakeDataset:
    """Mimics the iterable + .select() interface used by `derive()`."""

    def __init__(self, records: list[dict[str, Any]]) -> None:
        self._records = records

    def __iter__(self) -> Any:
        return iter(self._records)

    def __len__(self) -> int:
        return len(self._records)

    def select(self, indices: range) -> "_FakeDataset":
        return _FakeDataset([self._records[i] for i in indices])

    def take(self, n: int) -> "_FakeDataset":
        return _FakeDataset(self._records[:n])


def _fake_load_dataset(*_args: Any, **_kwargs: Any) -> _FakeDataset:
    return _FakeDataset(_make_mock_records())


def test_derive_end_to_end(tmp_path: Path) -> None:
    """Full pipeline: load → filter → write Parquet → write report."""
    output_dir = tmp_path / "tr-thesis-academic-ready"

    with patch("datasets.load_dataset", side_effect=_fake_load_dataset):
        stats = derive_mod.derive(
            upstream_id="mock/dataset",
            min_abstract_words=50,
            output_dir=output_dir,
            streaming=False,
            sample_n=None,
        )

    # 6 input records: 2 kept, 4 dropped
    assert stats["input_records"] == 6
    assert stats["output_records"] == 2
    assert stats["drops"]["empty_abstract"] >= 1
    assert stats["drops"]["short_abstract"] == 1
    assert stats["drops"]["duplicate_tez_no"] == 1

    # Output files exist
    parquet_path = output_dir / "data.parquet"
    report_path = output_dir / "derivation_report.json"
    assert parquet_path.exists()
    assert report_path.exists()

    # Report is valid JSON with required fields
    with report_path.open(encoding="utf-8") as handle:
        report = json.load(handle)
    assert report["upstream_id"] == "mock/dataset"
    assert report["upstream_license"] == "CC-BY-4.0"
    assert report["filter_version"] == "v1.0"
    assert report["downstream_id"] == "hakansabunis/tr-thesis-academic-ready"
    assert "derived_at" in report
    assert "abstract_word_percentiles" in report

    # Output Parquet has expected schema
    import pyarrow.parquet as pq  # noqa: PLC0415

    table = pq.read_table(parquet_path)
    assert table.num_rows == 2
    expected_fields = set(derive_mod.PRESERVED_FIELDS) | {
        "quality_score",
        "derived_at",
        "filter_version",
    }
    assert expected_fields.issubset(set(table.schema.names))


def test_derive_deterministic(tmp_path: Path) -> None:
    """Same upstream + same filter version → identical Parquet bytes (R2.9)."""
    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"

    with patch("datasets.load_dataset", side_effect=_fake_load_dataset):
        derive_mod.derive(output_dir=out1, sample_n=None, streaming=False)
        derive_mod.derive(output_dir=out2, sample_n=None, streaming=False)

    # Read both Parquet files; the row content (sorted by tez_no) must match
    import pyarrow.parquet as pq  # noqa: PLC0415

    t1 = pq.read_table(out1 / "data.parquet").sort_by("tez_no")
    t2 = pq.read_table(out2 / "data.parquet").sort_by("tez_no")
    assert t1.num_rows == t2.num_rows
    # Every column except `derived_at` (which is a timestamp at run time)
    # must be byte-identical
    for col in t1.schema.names:
        if col == "derived_at":
            continue
        assert t1.column(col).to_pylist() == t2.column(col).to_pylist(), (
            f"Determinism violation in column {col}"
        )


def test_derive_sample_n(tmp_path: Path) -> None:
    """sample_n correctly limits input records."""
    output_dir = tmp_path / "small"
    with patch("datasets.load_dataset", side_effect=_fake_load_dataset):
        stats = derive_mod.derive(output_dir=output_dir, sample_n=2, streaming=False)
    assert stats["input_records"] == 2


@pytest.mark.parametrize("min_words", [50, 100, 1000])
def test_derive_threshold_strictness(tmp_path: Path, min_words: int) -> None:
    """Higher word threshold → fewer kept records (monotonic)."""
    output_dir = tmp_path / f"thresh-{min_words}"
    with patch("datasets.load_dataset", side_effect=_fake_load_dataset):
        stats = derive_mod.derive(
            output_dir=output_dir,
            min_abstract_words=min_words,
            streaming=False,
        )
    if min_words == 50:
        assert stats["output_records"] == 2
    elif min_words == 100:
        # Exactly 100-word records are kept; 80-word one is dropped
        assert stats["output_records"] == 1
    else:  # 1000
        assert stats["output_records"] == 0
