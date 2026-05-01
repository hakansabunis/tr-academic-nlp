"""End-to-end smoke test for the AcademicPipeline.

Usage::

    python scripts/test_pipeline.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sdk"))

from tr_academic_nlp.pipeline import AcademicPipeline


SAMPLES = [
    {
        "label": "Tez örneği — yazar/kurum/yıl/metodoloji yoğun",
        "text": (
            "Prof. Dr. Ayşe Yılmaz tarafından Hacettepe Üniversitesi'nde 2023 "
            "yılında yapılan çalışmada, derin öğrenme yöntemlerinden BERT "
            "modeli IMDB veri seti üzerinde değerlendirilmiş ve F1 skoru 0.89 "
            "olarak ölçülmüştür. Çalışma, Türk Bilişim Dergisi'nde yayımlanmıştır."
        ),
        "task": "summarize",
    },
    {
        "label": "Soru-cevap",
        "text": (
            "Bu makalede CNN ve LSTM modelleri Türkçe duygu analizi için "
            "karşılaştırılmıştır. ODTÜ Bilgisayar Mühendisliği Bölümü'nde "
            "Yrd. Doç. Dr. Mehmet Demir tarafından 2024 yılında yapılan "
            "deneyler, ROUGE-L değeri 0.42 ile sonuçlanmıştır."
        ),
        "task": "extract_methods",
    },
]


def main() -> None:
    print("=" * 70)
    print("AcademicPipeline End-to-End Smoke Test")
    print("=" * 70)

    print("\n[init] Pipeline başlatılıyor...")
    pipe = AcademicPipeline()
    print(f"[init] LLM: {pipe.llm_model}")
    print(f"[init] Ollama health: {'OK' if pipe._ollama_health() else 'YOK'}")

    for i, sample in enumerate(SAMPLES, start=1):
        print()
        print("=" * 70)
        print(f"Örnek {i}: {sample['label']}")
        print("=" * 70)
        print("\n--- ORİJİNAL ---")
        print(sample["text"])

        # Use audit method to expose the masked + unmasked stages
        try:
            final, audit = pipe.analyze_with_audit(sample["text"], task=sample["task"])
        except ValueError as exc:
            # Some tasks (qa) require extra args — fall back to default
            print(f"\n[skipped: {exc}]")
            continue

        print("\n--- MASKELENMİŞ (Ollama'ya giden) ---")
        print(audit["masked_text"])

        print("\n--- MAPPING (geri çözüm sözlüğü) ---")
        for tag, real in audit["mapping"].items():
            print(f"  {tag} -> {real!r}")

        print("\n--- LLM CEVABI (maskeli) ---")
        print(audit["llm_response_masked"])

        print("\n--- FİNAL (kullanıcıya verilen) ---")
        print(final)


if __name__ == "__main__":
    main()
