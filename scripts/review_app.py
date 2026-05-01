"""Manual NER labeling review — Streamlit local app.

Reads the merged labeling output ``cli-haiku-2k.jsonl`` and lets the
human reviewer accept, flag, or reject the LLM-produced annotations
per paragraph. Decisions stream to ``review_decisions.jsonl`` and the
app picks up where you left off on relaunch (resume-safe).

Usage::

    pip install streamlit
    streamlit run scripts/review_app.py
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]

LABELED_PATH = ROOT / "docs" / "labeler-eval" / "api-sonnet-2k-fixed.jsonl"
DECISIONS_PATH = ROOT / "docs" / "labeler-eval" / "review_decisions.jsonl"

ENTITY_COLORS = {
    "YAZAR": "#FFE4B5",
    "KURUM": "#B3E5FC",
    "DERGİ": "#F8BBD0",
    "YIL": "#C5E1A5",
    "METODOLOJI": "#FFCCBC",
    "DATASET": "#D1C4E9",
    "METRİK": "#FFF59D",
}

VOTE_LABELS = {
    "ok": "✅ OK (etiketler doğru)",
    "edit": "✏️ Düzeltme gerek (kısmen doğru)",
    "bad": "❌ Hatalı (önemli problem)",
    "skip": "⏭️ Atla",
}


@st.cache_data
def load_paragraphs() -> list[dict]:
    """Load every successfully-labeled paragraph as a dict."""
    if not LABELED_PATH.exists():
        return []
    out: list[dict] = []
    with LABELED_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get("succeeded"):
                out.append(record)
    out.sort(key=lambda r: str(r.get("paragraph_id", "")))
    return out


def load_decisions() -> dict[str, dict]:
    decisions: dict[str, dict] = {}
    if DECISIONS_PATH.exists():
        with DECISIONS_PATH.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                decisions[str(record["paragraph_id"])] = record
    return decisions


def save_decision(paragraph_id: str, vote: str, note: str) -> None:
    DECISIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "paragraph_id": paragraph_id,
        "vote": vote,
        "note": note,
        "decided_at": datetime.now(timezone.utc).isoformat(),
    }
    with DECISIONS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def render_highlighted(text: str, spans: list[dict]) -> str:
    """Return HTML where every span is wrapped in a coloured highlight."""
    if not spans:
        return f"<div style='line-height:1.9; padding:8px;'>{_html_escape(text)}</div>"
    sorted_spans = sorted(spans, key=lambda s: (int(s["start"]), -int(s["end"])))
    pieces: list[str] = []
    cursor = 0
    for span in sorted_spans:
        start, end = int(span["start"]), int(span["end"])
        if start < cursor:
            continue
        pieces.append(_html_escape(text[cursor:start]))
        entity = span["entity"]
        colour = ENTITY_COLORS.get(entity, "#EEEEEE")
        pieces.append(
            f"<span style='background:{colour}; padding:1px 4px; border-radius:4px; "
            f"margin:0 1px;' title='{entity}'>"
            f"{_html_escape(text[start:end])}"
            f"<sub style='color:#666; font-size:0.7em; margin-left:2px;'>{entity}</sub>"
            f"</span>"
        )
        cursor = end
    pieces.append(_html_escape(text[cursor:]))
    return f"<div style='line-height:2.1; padding:8px;'>{''.join(pieces)}</div>"


def _html_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def main() -> None:
    st.set_page_config(
        page_title="tr-academic-nlp NER Review",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🇹🇷 tr-academic-nlp — NER Etiket İncelemesi")
    st.caption(
        "Her paragraf için Claude Haiku'nun ürettiği etiketleri kontrol et: "
        "✅ OK / ✏️ Düzeltme gerek / ❌ Hatalı / ⏭️ Atla"
    )

    paragraphs = load_paragraphs()
    if not paragraphs:
        st.error(
            f"`{LABELED_PATH.name}` bulunamadı veya boş. "
            "Önce labeling pipeline'ı çalıştırılmalı."
        )
        return

    decisions = load_decisions()
    total = len(paragraphs)
    done = len(decisions)

    if "idx" not in st.session_state:
        # Resume from first undecided paragraph
        st.session_state.idx = next(
            (
                i
                for i, record in enumerate(paragraphs)
                if str(record["paragraph_id"]) not in decisions
            ),
            0,
        )

    # ---------- Sidebar ----------
    with st.sidebar:
        st.header("İlerleme")
        if total > 0:
            st.progress(min(done / total, 1.0))
        st.write(f"**{done} / {total}** karar verildi")
        st.write(f"Kalan: {total - done}")

        votes = {"ok": 0, "edit": 0, "bad": 0, "skip": 0}
        for record in decisions.values():
            v = record.get("vote", "skip")
            votes[v] = votes.get(v, 0) + 1
        st.divider()
        st.subheader("Oy dağılımı")
        for key, label in VOTE_LABELS.items():
            st.write(f"{label}: **{votes.get(key, 0)}**")

        st.divider()
        st.subheader("Renk kodları")
        for entity, colour in ENTITY_COLORS.items():
            st.markdown(
                f"<span style='background:{colour}; padding:2px 6px; "
                f"border-radius:3px;'>{entity}</span>",
                unsafe_allow_html=True,
            )

        st.divider()
        st.subheader("Atla")
        if total > 0:
            jump_to = st.number_input(
                "Belirli paragraph indekse git",
                min_value=1,
                max_value=total,
                value=min(st.session_state.idx + 1, total),
                step=1,
            )
            if st.button("Git"):
                st.session_state.idx = int(jump_to) - 1
                st.rerun()

    # ---------- Main ----------
    idx = int(st.session_state.idx)

    if idx >= total:
        st.success(f"🎉 Tüm {total} paragraph incelendi!")
        st.balloons()
        return

    record = paragraphs[idx]
    pid = str(record["paragraph_id"])
    text = record["text"]
    spans = record.get("spans", [])
    existing = decisions.get(pid)

    st.markdown(f"### Paragraph {idx + 1} / {total}")
    st.caption(
        f"`{pid}` · {len(spans)} entity"
        + (f" · daha önce: **{existing['vote']}**" if existing else "")
    )

    # Plain text
    st.markdown("**Orijinal metin:**")
    st.markdown(
        f"<div style='background:#fafafa; padding:12px; border-radius:6px; "
        f"border-left:4px solid #2E86AB; line-height:1.8; white-space:pre-wrap;'>"
        f"{_html_escape(text)}</div>",
        unsafe_allow_html=True,
    )

    # Highlighted text
    st.markdown("**Etiketli metin:**")
    st.markdown(render_highlighted(text, spans), unsafe_allow_html=True)

    # Entity list
    if spans:
        with st.expander(f"Entity listesi ({len(spans)} adet)"):
            entity_groups: dict[str, list[str]] = {}
            for span in spans:
                entity_groups.setdefault(span["entity"], []).append(span["text"])
            for entity in sorted(entity_groups):
                terms = ", ".join(f'"{t}"' for t in entity_groups[entity])
                st.markdown(f"- **{entity}** ({len(entity_groups[entity])}): {terms}")

    st.write("")
    note = st.text_input(
        "Not (opsiyonel — örn. 'BERT kaçırılmış', 'Türkçe yanlış DATASET',  vs.)",
        key=f"note_{idx}",
    )

    st.markdown("##### Karar")
    bcols = st.columns(4)
    if bcols[0].button("✅ OK", use_container_width=True, type="primary"):
        save_decision(pid, "ok", note)
        st.session_state.idx += 1
        st.rerun()
    if bcols[1].button("✏️ Düzeltme gerek", use_container_width=True):
        save_decision(pid, "edit", note)
        st.session_state.idx += 1
        st.rerun()
    if bcols[2].button("❌ Hatalı", use_container_width=True):
        save_decision(pid, "bad", note)
        st.session_state.idx += 1
        st.rerun()
    if bcols[3].button("⏭️ Atla", use_container_width=True):
        save_decision(pid, "skip", note)
        st.session_state.idx += 1
        st.rerun()

    st.write("")
    nav = st.columns([1, 4, 1])
    if nav[0].button("← Önceki"):
        st.session_state.idx = max(0, st.session_state.idx - 1)
        st.rerun()
    if nav[2].button("Sonraki (oy vermeden) →"):
        st.session_state.idx += 1
        st.rerun()


if __name__ == "__main__":
    main()
