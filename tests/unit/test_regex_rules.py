"""Tests for the regex-based entity extractors (Faz 2, Requirement 4.3)."""
from __future__ import annotations

from data.labeling.regex_rules import (
    Span,
    extract_all,
    find_authors,
    find_datasets,
    find_institutions,
    find_methodologies,
    find_metrics,
    find_years,
    resolve_overlaps,
)


class TestYearExtractor:
    def test_finds_4_digit_year(self) -> None:
        spans = find_years("Bu çalışma 2023 yılında yayınlandı.")
        assert len(spans) == 1
        assert spans[0].text == "2023"
        assert spans[0].entity == "YIL"

    def test_finds_multiple_years(self) -> None:
        spans = find_years("1995 ile 2024 arasında ...")
        assert {s.text for s in spans} == {"1995", "2024"}

    def test_rejects_invalid_years(self) -> None:
        # 1899 = before academic publishing era; 2050 = future beyond plausible
        spans = find_years("1899 ve 2050 yılları arasında")
        assert spans == []

    def test_word_boundary(self) -> None:
        # 12023 should not match (no word boundary)
        spans = find_years("ID12023 numaralı kayıt")
        assert spans == []


class TestInstitutionExtractor:
    def test_basic_university(self) -> None:
        spans = find_institutions("Boğaziçi Üniversitesi'nde okumaktayım.")
        assert any("Boğaziçi" in s.text for s in spans)

    def test_institute_suffix(self) -> None:
        spans = find_institutions("Karadeniz Teknik Enstitüsü açıklama yaptı.")
        assert any(s.entity == "KURUM" for s in spans)

    def test_does_not_match_lowercase_noise(self) -> None:
        spans = find_institutions("normal kelimeler içeren cümle")
        assert spans == []


class TestMethodologyExtractor:
    def test_finds_known_methods(self) -> None:
        spans = find_methodologies("CNN ve LSTM modelleri kullanıldı.")
        terms = {s.text for s in spans}
        assert "CNN" in terms
        assert "LSTM" in terms

    def test_finds_turkish_phrase(self) -> None:
        spans = find_methodologies("Derin Öğrenme yöntemleri uygulandı.")
        assert any("Derin Öğrenme" in s.text for s in spans)

    def test_case_insensitive(self) -> None:
        spans = find_methodologies("bert tabanlı model")
        assert any(s.text.lower() == "bert" for s in spans)


class TestDatasetExtractor:
    def test_finds_named_dataset(self) -> None:
        spans = find_datasets("MNIST üzerinde test edildi.")
        assert any(s.text == "MNIST" for s in spans)

    def test_suffix_pattern_veri_seti(self) -> None:
        spans = find_datasets("Türkçe NLP veri seti hazırlandı.")
        # Suffix pattern catches "Türkçe NLP" as the dataset prefix
        assert any(s.entity == "DATASET" for s in spans)


class TestMetricExtractor:
    def test_finds_f1(self) -> None:
        spans = find_metrics("Modelin F1 skoru 0.85 oldu.")
        assert any("F1" in s.text or "F-skoru" in s.text for s in spans)

    def test_finds_rouge_l(self) -> None:
        spans = find_metrics("ROUGE-L değeri 0.42 hesaplandı.")
        assert any(s.text == "ROUGE-L" for s in spans)

    def test_finds_turkish_metric(self) -> None:
        spans = find_metrics("Doğruluk yüzde 92 olarak ölçüldü.")
        assert any(s.text == "Doğruluk" for s in spans)


class TestAuthorExtractor:
    def test_reversed_format(self) -> None:
        spans = find_authors("Yılmaz, A.M. tarafından önerilen yaklaşım")
        assert any("Yılmaz" in s.text for s in spans)

    def test_initial_lastname(self) -> None:
        spans = find_authors("H. Sabunis tarafından yapılan analizde")
        assert any("Sabunis" in s.text for s in spans)


class TestExtractAllAndResolveOverlaps:
    def test_extract_all_produces_sorted_spans(self) -> None:
        text = "2023 yılında CNN modeli MNIST veri seti üzerinde F1 skoru ile değerlendirildi."
        spans = extract_all(text)
        # Sorted by start position
        starts = [s.start for s in spans]
        assert starts == sorted(starts)

    def test_resolve_overlaps_keeps_higher_confidence(self) -> None:
        spans = [
            Span(0, 4, "DATASET", 0.7, "BERT"),
            Span(0, 4, "METODOLOJI", 0.95, "BERT"),
        ]
        kept = resolve_overlaps(spans)
        assert len(kept) == 1
        assert kept[0].entity == "METODOLOJI"

    def test_resolve_overlaps_keeps_disjoint(self) -> None:
        spans = [
            Span(0, 4, "YIL", 0.99, "2023"),
            Span(5, 8, "METRİK", 0.95, "F1"),
        ]
        kept = resolve_overlaps(spans)
        assert len(kept) == 2

    def test_full_paragraph_extraction(self) -> None:
        text = (
            "Yılmaz, A.M. (2023). Boğaziçi Üniversitesi'nde yapılan çalışmada "
            "BERT modeli IMDB veri seti üzerinde F1 skoru ile değerlendirildi."
        )
        spans = extract_all(text)
        entities = {s.entity for s in spans}
        # Expect at least these to be detected
        assert "YIL" in entities
        assert "KURUM" in entities
        assert "METODOLOJI" in entities
        assert "DATASET" in entities
        assert "METRİK" in entities
