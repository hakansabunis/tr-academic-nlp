"""Tests for the canonical entity type schema (Requirement 4.1)."""
from __future__ import annotations

from data.labeling.entity_types import ENTITY_TYPES, bio_tags, id2label, label2id


def test_seven_entity_types() -> None:
    assert len(ENTITY_TYPES) == 7


def test_entity_types_are_unique() -> None:
    assert len(set(ENTITY_TYPES)) == len(ENTITY_TYPES)


def test_canonical_entity_names() -> None:
    assert set(ENTITY_TYPES) == {
        "YAZAR",
        "KURUM",
        "DERGİ",
        "YIL",
        "METODOLOJI",
        "DATASET",
        "METRİK",
    }


def test_bio_tags_count() -> None:
    # 1 (O) + 2 * 7 (B-/I- per entity) = 15
    assert len(bio_tags()) == 15


def test_bio_tags_start_with_o() -> None:
    assert bio_tags()[0] == "O"


def test_label2id_inverts_id2label() -> None:
    fwd = label2id()
    rev = id2label()
    for tag, idx in fwd.items():
        assert rev[idx] == tag


def test_label2id_stable_ordering() -> None:
    """Same call twice yields identical mapping (no randomness)."""
    assert label2id() == label2id()
