"""Tests for CoNLL-2003 BIO writer / parser (Faz 2, Requirement 4.2)."""
from __future__ import annotations

from data.labeling.conll_writer import (
    assign_bio_tags,
    parse_conll,
    to_conll,
    tokenize_with_offsets,
)
from data.labeling.regex_rules import Span


class TestTokenizer:
    def test_simple_split(self) -> None:
        tokens = tokenize_with_offsets("CNN modeli kullanıldı")
        assert [t[0] for t in tokens] == ["CNN", "modeli", "kullanıldı"]

    def test_offsets_align(self) -> None:
        text = "CNN modeli"
        tokens = tokenize_with_offsets(text)
        for token, start, end in tokens:
            assert text[start:end] == token

    def test_punctuation_split(self) -> None:
        tokens = tokenize_with_offsets("CNN, LSTM kullanıldı.")
        token_texts = [t[0] for t in tokens]
        assert "," in token_texts
        assert "." in token_texts


class TestAssignBioTags:
    def test_basic_tag_assignment(self) -> None:
        text = "CNN ve LSTM modelleri"
        tokens = tokenize_with_offsets(text)
        spans = [
            Span(0, 3, "METODOLOJI", 0.95, "CNN"),
            Span(7, 11, "METODOLOJI", 0.95, "LSTM"),
        ]
        tags = assign_bio_tags(tokens, spans)
        # Tokens: ["CNN", "ve", "LSTM", "modelleri"]
        assert tags == ["B-METODOLOJI", "O", "B-METODOLOJI", "O"]

    def test_multi_token_entity_gets_b_then_i(self) -> None:
        text = "Boğaziçi Üniversitesi açıkladı"
        tokens = tokenize_with_offsets(text)
        spans = [Span(0, 21, "KURUM", 0.85, "Boğaziçi Üniversitesi")]
        tags = assign_bio_tags(tokens, spans)
        # Tokens: ["Boğaziçi", "Üniversitesi", "açıkladı"]
        assert tags[0] == "B-KURUM"
        assert tags[1] == "I-KURUM"
        assert tags[2] == "O"

    def test_no_spans_all_o(self) -> None:
        tokens = tokenize_with_offsets("normal cümle")
        tags = assign_bio_tags(tokens, [])
        assert all(tag == "O" for tag in tags)


class TestRoundTrip:
    def test_to_conll_then_parse(self) -> None:
        sentences = [
            (
                "CNN modeli 2023 yılında",
                [
                    Span(0, 3, "METODOLOJI", 0.95, "CNN"),
                    Span(11, 15, "YIL", 0.99, "2023"),
                ],
            ),
            (
                "F1 skoru 0.85",
                [Span(0, 8, "METRİK", 0.95, "F1 skoru")],
            ),
        ]
        text = to_conll(sentences)
        parsed = parse_conll(text)
        assert len(parsed) == 2
        # First sentence: CNN B-METODOLOJI / modeli O / 2023 B-YIL / yılında O
        first = parsed[0]
        first_dict = dict(first)
        assert first_dict["CNN"] == "B-METODOLOJI"
        assert first_dict["2023"] == "B-YIL"

    def test_to_conll_separates_sentences_with_blank_line(self) -> None:
        sentences = [
            ("A", []),
            ("B", []),
        ]
        text = to_conll(sentences)
        # Each sentence emits "<token>\tO\n" then a blank line
        assert "\n\n" in text
        assert text.count("\n\n") >= 2

    def test_parse_conll_handles_trailing_blank(self) -> None:
        content = "kelime\tO\n\n"
        sentences = parse_conll(content)
        assert sentences == [[("kelime", "O")]]

    def test_parse_conll_rejects_malformed(self) -> None:
        import pytest

        with pytest.raises(ValueError):
            parse_conll("kelime\tO\textra\n")
