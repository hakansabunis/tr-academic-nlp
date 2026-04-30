"""Integration-ish tests for the regex-pass labeling pipeline."""
from __future__ import annotations

import json
from pathlib import Path

from data.labeling.auto_label import (
    label_paragraph,
    label_paragraphs,
    stable_split,
)


class TestLabelParagraph:
    def test_returns_high_and_low(self) -> None:
        text = "2023 yılında CNN modeli BERT ile karşılaştırıldı."
        high, low = label_paragraph(text, low_confidence_threshold=0.80)
        # 2023 is YIL (0.99), CNN/BERT are METODOLOJI (0.95) → all high
        assert len(high) >= 3
        # No low-confidence spans expected for these well-known entities
        assert all(s.confidence >= 0.80 for s in high)

    def test_low_confidence_routed_separately(self) -> None:
        # Author-initial pattern returns 0.70 confidence; with threshold 0.80
        # it should go to the low queue.
        text = "H. Sabunis tarafından yapılan çalışma"
        high, low = label_paragraph(text, low_confidence_threshold=0.80)
        assert any(s.entity == "YAZAR" for s in low)

    def test_threshold_lowering(self) -> None:
        text = "H. Sabunis çalışmasında"
        high, low = label_paragraph(text, low_confidence_threshold=0.60)
        # All spans should now be high
        assert any(s.entity == "YAZAR" for s in high)


class TestStableSplit:
    def test_deterministic(self) -> None:
        assert stable_split("p123") == stable_split("p123")

    def test_distribution(self) -> None:
        # With 10K paragraph ids, we expect roughly 80/10/10 split
        counts = {"train": 0, "val": 0, "test": 0}
        for i in range(10_000):
            counts[stable_split(f"para-{i}")] += 1
        # Allow ±2% slack
        assert 7800 <= counts["train"] <= 8200
        assert 800 <= counts["val"] <= 1200
        assert 800 <= counts["test"] <= 1200


class TestLabelParagraphs:
    def test_full_pipeline(self, tmp_path: Path) -> None:
        paragraphs = [
            ("p1", "2023 yılında CNN modeli MNIST veri seti üzerinde test edildi."),
            ("p2", "Boğaziçi Üniversitesi'nde F1 skoru ile değerlendirme yapıldı."),
            ("p3", "Yılmaz, A.M. (2024) çalışmasında LSTM kullanıldı."),
            ("p4", "Önemli bir konu hakkında yazılmış cümle."),  # no entities
        ]
        report = label_paragraphs(paragraphs, output_dir=tmp_path)

        # All three split files must exist (even if empty)
        assert (tmp_path / "train.conll").exists()
        assert (tmp_path / "val.conll").exists()
        assert (tmp_path / "test.conll").exists()
        assert (tmp_path / "labeling_report.json").exists()
        assert (tmp_path / "low_confidence_spans.jsonl").exists()

        # Report sanity
        assert report["input_paragraphs"] == 4
        assert sum(report["split_sizes"].values()) == 4
        # At least YIL and METODOLOJI should appear
        assert "YIL" in report["entity_distribution"]

    def test_empty_input(self, tmp_path: Path) -> None:
        report = label_paragraphs([], output_dir=tmp_path)
        assert report["input_paragraphs"] == 0
        assert report["entity_distribution"] == {}

    def test_low_confidence_log_persisted(self, tmp_path: Path) -> None:
        paragraphs = [
            ("p1", "H. Sabunis tarafından öneri sunuldu."),
        ]
        label_paragraphs(paragraphs, output_dir=tmp_path)
        low_path = tmp_path / "low_confidence_spans.jsonl"
        lines = low_path.read_text(encoding="utf-8").strip().split("\n")
        # H. Sabunis is initial-format author with confidence 0.70 (low)
        assert any(json.loads(line)["entity"] == "YAZAR" for line in lines if line)
