"""Canonical academic NER entity types for ``trakad-ner-v1``.

Defined in Requirement 4.1: exactly 7 entity types with stable identifiers.
Used by both the labeling pipeline (``data/labeling/``) and the model
training pipeline (``models/ner/``).

The BIO scheme adds ``B-`` and ``I-`` prefixes:
    O, B-YAZAR, I-YAZAR, B-KURUM, I-KURUM, ..., B-METRİK, I-METRİK
Total: 1 + 2*7 = 15 tags.
"""
from __future__ import annotations

from typing import Final

ENTITY_TYPES: Final[tuple[str, ...]] = (
    "YAZAR",  # author names
    "KURUM",  # institutions
    "DERGİ",  # journals / conferences
    "YIL",  # publication year
    "METODOLOJI",  # methodology / algorithm
    "DATASET",  # dataset names
    "METRİK",  # evaluation metrics
)


def bio_tags() -> list[str]:
    """Return the full BIO tag set (15 tags including ``O``)."""
    tags = ["O"]
    for entity in ENTITY_TYPES:
        tags.append(f"B-{entity}")
        tags.append(f"I-{entity}")
    return tags


def label2id() -> dict[str, int]:
    """Map BIO tag → integer id (stable ordering for HF Trainer)."""
    return {tag: i for i, tag in enumerate(bio_tags())}


def id2label() -> dict[int, str]:
    """Inverse of :func:`label2id`."""
    return {i: tag for tag, i in label2id().items()}
