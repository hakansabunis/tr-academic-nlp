"""Convert ``Span`` annotations on raw text into CoNLL-2003 BIO format.

Format spec (Requirement 4.2):
    - One token per line: ``<token>\\t<bio_tag>``
    - Sentences separated by an empty line
    - BIO tags use the entity types from :mod:`entity_types`

This module is deliberately small and pure: tokenization is whitespace-based
plus light punctuation handling. Real BERTurk fine-tuning re-tokenizes with
the model's WordPiece tokenizer; we only need word-level alignment here.
"""
from __future__ import annotations

import re
from io import StringIO
from typing import Iterable

from .regex_rules import Span, resolve_overlaps

# Whitespace + punctuation tokenizer. Keeps offsets stable for span alignment.
_TOKEN_RE = re.compile(r"\S+|[\.\,\;\:\!\?\(\)\[\]]")


def tokenize_with_offsets(text: str) -> list[tuple[str, int, int]]:
    """Tokenize whitespace-separated, returning ``(token, start, end)``."""
    out: list[tuple[str, int, int]] = []
    for match in re.finditer(r"\S+", text):
        token = match.group()
        start = match.start()
        # Strip trailing punctuation as a separate token if present
        if token and token[-1] in ".,;:!?":
            if len(token) > 1:
                out.append((token[:-1], start, start + len(token) - 1))
                out.append((token[-1], start + len(token) - 1, start + len(token)))
            else:
                out.append((token, start, start + len(token)))
        else:
            out.append((token, start, start + len(token)))
    return out


def assign_bio_tags(
    tokens: list[tuple[str, int, int]],
    spans: list[Span],
) -> list[str]:
    """Assign one BIO tag per token from a list of (start, end, entity) spans.

    Tokens whose ``[start, end)`` overlap with a span at the **start** receive
    ``B-<entity>``; subsequent overlapping tokens receive ``I-<entity>``.
    Non-overlapping tokens receive ``O``.

    Overlapping spans are pre-resolved by :func:`resolve_overlaps` so each
    token maps to at most one entity.
    """
    spans = resolve_overlaps(spans)
    tags: list[str] = ["O"] * len(tokens)

    for span in spans:
        first_in_span = True
        for i, (_token, t_start, t_end) in enumerate(tokens):
            # Token overlaps span when intervals intersect
            if t_end <= span.start or t_start >= span.end:
                continue
            if tags[i] != "O":
                continue  # already taken by an earlier (higher-priority) span
            tags[i] = ("B-" if first_in_span else "I-") + span.entity
            first_in_span = False

    return tags


def to_conll(
    sentences: Iterable[tuple[str, list[Span]]],
) -> str:
    """Render an iterable of ``(text, spans)`` pairs as CoNLL-2003 BIO.

    Returns a single string with sentences separated by blank lines.
    """
    buffer = StringIO()
    for text, spans in sentences:
        tokens = tokenize_with_offsets(text)
        tags = assign_bio_tags(tokens, spans)
        for (token, _start, _end), tag in zip(tokens, tags, strict=True):
            buffer.write(f"{token}\t{tag}\n")
        buffer.write("\n")
    return buffer.getvalue()


def parse_conll(content: str) -> list[list[tuple[str, str]]]:
    """Inverse of :func:`to_conll` — parse CoNLL string into sentence list.

    Each sentence is a list of ``(token, tag)`` tuples. Useful for tests
    and for round-trip property verification.
    """
    sentences: list[list[tuple[str, str]]] = []
    current: list[tuple[str, str]] = []
    for line in content.split("\n"):
        line = line.rstrip()
        if not line:
            if current:
                sentences.append(current)
                current = []
            continue
        parts = line.split("\t")
        if len(parts) != 2:
            raise ValueError(f"Malformed CoNLL line: {line!r}")
        current.append((parts[0], parts[1]))
    if current:
        sentences.append(current)
    return sentences


__all__ = [
    "assign_bio_tags",
    "parse_conll",
    "to_conll",
    "tokenize_with_offsets",
]
