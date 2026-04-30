"""Unit tests for the Faz 1 derivation pipeline filters.

Tests the pure functions that don't require the upstream dataset to be
available — they exercise the determinism and correctness guarantees that
``Requirement 2.9`` (deterministic re-derivation) relies on.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow importing data/derive/* without installing as a package
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from data.derive.load_umutertugrul import (  # noqa: E402
    PRESERVED_FIELDS,
    compute_quality_score,
    has_valid_abstract,
    normalize_record,
    normalize_text,
)


class TestNormalizeText:
    def test_preserves_turkish_characters(self) -> None:
        assert normalize_text("şçğıöü") == "şçğıöü"
        assert normalize_text("Çağdaş Türk Edebiyatı") == "Çağdaş Türk Edebiyatı"

    def test_handles_none(self) -> None:
        assert normalize_text(None) is None

    def test_handles_empty_string(self) -> None:
        assert normalize_text("") == ""

    def test_idempotent(self) -> None:
        # NFC applied twice produces same result — required for determinism
        sample = "Çağdaş Türk Edebiyatında Şiir"
        once = normalize_text(sample)
        twice = normalize_text(once)
        assert once == twice


class TestHasValidAbstract:
    def test_long_enough(self) -> None:
        rec = {"abstract_tr": " ".join(["kelime"] * 60)}
        assert has_valid_abstract(rec, min_words=50)

    def test_too_short(self) -> None:
        rec = {"abstract_tr": " ".join(["kelime"] * 10)}
        assert not has_valid_abstract(rec, min_words=50)

    def test_empty_string(self) -> None:
        assert not has_valid_abstract({"abstract_tr": ""})

    def test_none_value(self) -> None:
        assert not has_valid_abstract({"abstract_tr": None})

    def test_missing_key(self) -> None:
        assert not has_valid_abstract({})

    def test_non_string_value(self) -> None:
        assert not has_valid_abstract({"abstract_tr": 12345})

    def test_threshold_exact(self) -> None:
        rec = {"abstract_tr": " ".join(["k"] * 50)}
        assert has_valid_abstract(rec, min_words=50)
        assert not has_valid_abstract(rec, min_words=51)


class TestQualityScore:
    def test_range(self) -> None:
        rec = {"abstract_tr": " ".join(["w"] * 100)}
        score = compute_quality_score(rec)
        assert 0.0 <= score <= 1.0

    def test_rich_record_scores_higher(self) -> None:
        rich = {
            "abstract_tr": " ".join(["w"] * 300),
            "abstract_en": " ".join(["w"] * 300),
            "author": "Hakan Sabunis",
            "advisor": "Prof. X",
        }
        sparse = {"abstract_tr": " ".join(["w"] * 50)}
        assert compute_quality_score(rich) > compute_quality_score(sparse)

    def test_caps_at_one(self) -> None:
        rec = {
            "abstract_tr": " ".join(["w"] * 10_000),
            "abstract_en": " ".join(["w"] * 10_000),
            "author": "X",
            "advisor": "Y",
        }
        # Float arithmetic can land at 0.9999...; we want the cap to hold
        assert compute_quality_score(rec) == 1.0 or abs(compute_quality_score(rec) - 1.0) < 1e-9

    def test_empty_record(self) -> None:
        assert compute_quality_score({}) == 0.0


class TestNormalizeRecord:
    def test_preserves_only_known_fields(self) -> None:
        record = {
            "tez_no": 12345,
            "title_tr": "Başlık",
            "abstract_tr": "Abstract",
            "year": 2023,
            "irrelevant_extra": "should be dropped",
            "internal_meta": {"foo": "bar"},
        }
        out = normalize_record(record)
        assert out["tez_no"] == 12345
        assert "irrelevant_extra" not in out
        assert "internal_meta" not in out
        assert set(out.keys()) == set(PRESERVED_FIELDS)

    def test_missing_fields_become_none(self) -> None:
        out = normalize_record({"tez_no": 1})
        assert out["tez_no"] == 1
        assert out["title_tr"] is None
        assert out["abstract_tr"] is None

    def test_text_fields_normalized(self) -> None:
        # Use a string with combining diacritic vs precomposed; both NFC-normalize
        # to the same precomposed form.
        decomposed = "Çağdaş"  # Ç̧ağ̆daş̧ via combining marks
        composed = "Çağdaş"
        rec = {"title_tr": decomposed, "abstract_tr": composed, "tez_no": 1}
        out = normalize_record(rec)
        # Both inputs should normalize to NFC precomposed form
        assert normalize_text(decomposed) == out["title_tr"]
        assert out["abstract_tr"] == composed

    def test_non_string_text_field_passthrough(self) -> None:
        # Defensive: if upstream ever returns int in a text field, don't crash
        rec = {"tez_no": 1, "year": 2023, "pages": 150}
        out = normalize_record(rec)
        assert out["year"] == 2023
        assert out["pages"] == 150
