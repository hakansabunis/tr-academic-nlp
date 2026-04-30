"""One-off helper: convert hand-written annotations from Claude Opus 4.7
(this chat session) into the same JSON shape the eval pipeline produces,
so it can be diffed against the Gemini run in the markdown summary.

Run once:
    python scripts/_emit_claude_chat_eval.py

This file is intentionally not part of the regular test/CI surface; it
documents the manual annotation pass for reproducibility.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


# Manual annotations produced by Claude Opus 4.7 in chat for the bundled
# 10 sample paragraphs. Format: paragraph_id -> list of (entity, text).
# Offsets are computed below by str.find() on the original paragraph.
ANNOTATIONS: dict[str, list[tuple[str, str]]] = {
    "sp-001": [
        ("YAZAR", "Yılmaz, A.M."),
        ("YIL", "2023"),
        ("KURUM", "Boğaziçi Üniversitesi"),
        ("METODOLOJI", "BERT"),
        ("DATASET", "IMDB"),
        ("METRİK", "F1 skoru"),
    ],
    "sp-002": [
        ("METODOLOJI", "CNN"),
        ("METODOLOJI", "LSTM"),
        ("KURUM", "ODTÜ Bilgisayar Mühendisliği"),
        ("YIL", "2024"),
        ("METRİK", "ROUGE-L"),
    ],
    "sp-003": [
        ("YAZAR", "Demir, K."),
        ("YAZAR", "Kaya, S."),
        ("YIL", "2022"),
        ("DERGİ", "Türk Bilişim Dergisi"),
        ("METODOLOJI", "Random Forest"),
        ("METODOLOJI", "XGBoost"),
        ("KURUM", "Hacettepe Üniversitesi Tıp Fakültesi"),
    ],
    "sp-004": [
        ("DATASET", "Twitter veri seti"),
        ("METODOLOJI", "Naive Bayes"),
        ("METRİK", "doğruluk"),
    ],
    "sp-005": [
        ("YAZAR", "Çetin, A."),
        ("YIL", "2021"),
        ("KURUM", "Yıldız Teknik Üniversitesi"),
        ("METODOLOJI", "Gradient Boosting"),
        ("DATASET", "WikiNeural"),
        ("METRİK", "Precision"),
    ],
    "sp-006": [
        ("METODOLOJI", "mT5"),
        ("KURUM", "Marmara Üniversitesi"),
        ("METRİK", "Spearman"),
    ],
    "sp-007": [
        ("YAZAR", "Karadeniz, M."),
        ("YIL", "2020"),
        ("METODOLOJI", "ResNet-50"),
        ("DATASET", "CIFAR-10"),
        ("METRİK", "mAP"),
        ("KURUM", "KTÜ Elektrik-Elektronik Mühendisliği"),
    ],
    "sp-008": [
        ("METODOLOJI", "Transformer"),
        ("DATASET", "Mukayese"),
        ("METRİK", "METEOR"),
        ("METRİK", "BLEU"),
    ],
    "sp-009": [
        ("YAZAR", "Akın, B."),
        ("YAZAR", "Yıldız, R."),
        ("YAZAR", "Şahin, T."),
        ("YIL", "2025"),
        ("DERGİ", "Anadolu Üniversitesi Eğitim Fakültesi Dergisi"),
        ("METODOLOJI", "k-NN"),
        ("DATASET", "PISA 2018"),
        ("METRİK", "MSE"),
    ],
    "sp-010": [
        ("METODOLOJI", "XLM-RoBERTa"),
        ("DATASET", "WikiANN-tr"),
        ("METRİK", "Cohen Kappa"),
        ("METODOLOJI", "BERTurk"),
    ],
}


def _load_paragraphs() -> dict[str, str]:
    paragraphs: dict[str, str] = {}
    path = ROOT / "scripts" / "sample_paragraphs.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            paragraphs[record["paragraph_id"]] = record["text"]
    return paragraphs


def _build_rows() -> tuple[list[dict], dict[str, int]]:
    paragraphs = _load_paragraphs()
    rows: list[dict] = []
    entity_counter: dict[str, int] = {}
    for paragraph_id, annotations in ANNOTATIONS.items():
        text = paragraphs[paragraph_id]
        spans_out: list[dict] = []
        for entity, surface in annotations:
            start = text.find(surface)
            if start < 0:
                raise ValueError(
                    f"Surface form not found in {paragraph_id}: {surface!r}"
                )
            spans_out.append(
                {
                    "start": start,
                    "end": start + len(surface),
                    "entity": entity,
                    "text": surface,
                    "confidence": 1.00,  # human-equivalent confidence
                }
            )
            entity_counter[entity] = entity_counter.get(entity, 0) + 1
        rows.append(
            {
                "paragraph_id": paragraph_id,
                "text": text,
                "succeeded": True,
                "error": None,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_usd": 0.0,
                "spans": spans_out,
            }
        )
    return rows, entity_counter


def main() -> None:
    rows, entity_counter = _build_rows()
    payload = {
        "provider": "claude-opus-4-7-chat",
        "paragraphs": rows,
        "stats": {
            "calls": len(rows),
            "successful_calls": len(rows),
            "failed_calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_usd": 0.0,
            "retries": 0,
            "invalid_json_count": 0,
            "paragraphs_with_zero_entities": 0,
            "note": (
                "Annotations produced by Claude Opus 4.7 in chat (Pro/Max "
                "subscription, no per-call API charge). For 30K-scale, use "
                "Claude Code CLI batch (`claude --print`) with the same "
                "prompt — see scripts/batch_label_via_claude_cli.py."
            ),
        },
        "entity_counts": dict(
            sorted(entity_counter.items(), key=lambda kv: -kv[1])
        ),
    }
    out_path = ROOT / "docs" / "labeler-eval" / "labeler-eval-claude-opus-chat.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
    print(f"Wrote {out_path}")
    print(f"Total entities: {sum(entity_counter.values())}")
    print(f"Per-entity counts: {payload['entity_counts']}")


if __name__ == "__main__":
    main()
