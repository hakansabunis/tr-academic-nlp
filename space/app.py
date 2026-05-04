"""trakad — Türkçe akademik semantic search demo.

HuggingFace Space entry point. Loads a pre-built ChromaDB index from a
companion HF dataset on first run, then serves a Gradio UI.

Locally: `python space/app.py` (will index from data/chroma_db if present,
otherwise will download from HF).
"""
from __future__ import annotations

import os
from pathlib import Path

import chromadb
import gradio as gr
from chromadb.utils import embedding_functions

INDEX_REPO = os.getenv("TRAKAD_INDEX_REPO", "hakansabunis/trakad-rag-index-mpnet")
EMBED_MODEL = os.getenv(
    "TRAKAD_EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
)
COLLECTION = "turkish_theses"
YOK_URL_TMPL = "https://tez.yok.gov.tr/UlusalTezMerkezi/tezSorguSonucYeni.jsp?id={tez_no}"


def _resolve_db_path() -> str:
    """Return a local ChromaDB path. Prefers repo-local dump, falls back to HF download."""
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent / "data" / "chroma_db",  # dev / monorepo
        here / "chroma_db",                  # bundled in space
    ]
    for c in candidates:
        if c.is_dir() and (c / "chroma.sqlite3").exists():
            print(f"[trakad] using local ChromaDB: {c}")
            return str(c)

    print(f"[trakad] downloading index from {INDEX_REPO} ...")
    from huggingface_hub import snapshot_download
    local_dir = snapshot_download(repo_id=INDEX_REPO, repo_type="dataset")
    print(f"[trakad] downloaded to: {local_dir}")
    return local_dir


print("[trakad] booting...")
DB_PATH = _resolve_db_path()
client = chromadb.PersistentClient(path=DB_PATH)
embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
collection = client.get_or_create_collection(name=COLLECTION, embedding_function=embed_fn)
TOTAL = collection.count()
print(f"[trakad] collection ready: {TOTAL} items")


def _result_md(query: str, top_k: int) -> str:
    if not query.strip():
        return "_Sorgu girin._"
    res = collection.query(query_texts=[query], n_results=top_k)
    ids = res["ids"][0]
    docs = res["documents"][0]
    metas = res["metadatas"][0]
    if not docs:
        return "_Sonuç yok._"

    lines = [f"### Top-{len(docs)} eşleşme — sorgu: *{query}*", ""]
    for i, (tez_no, doc, m) in enumerate(zip(ids, docs, metas), start=1):
        title = m.get("title", "Başlıksız")
        author = m.get("author", "?")
        year = m.get("year", "?")
        subject = m.get("subject", "?")
        snippet = (doc or "").strip().replace("\n", " ")
        if len(snippet) > 350:
            snippet = snippet[:347] + "..."

        link = YOK_URL_TMPL.format(tez_no=tez_no) if tez_no else ""
        link_md = f" · [YÖK]({link})" if link else ""

        lines.append(f"**[{i}] {title}**{link_md}")
        lines.append(f"_{author} · {year} · {subject}_")
        lines.append("")
        lines.append(f"> {snippet}")
        lines.append("")
        lines.append("---")
    return "\n".join(lines)


with gr.Blocks(title="trakad — Türkçe Akademik Arama") as demo:
    gr.Markdown(
        f"""
# trakad — Türkçe Akademik Semantic Search

48,376 Türkçe tez özeti üzerinde **anlam-tabanlı** arama. Klasik anahtar
kelime taramasının aksine, "yapay zeka" yazınca "AI", "makine öğrenmesi"
geçen tezler de yakalanır.

**Embedding:** `{EMBED_MODEL.split("/")[-1]}` ·
**Index:** ChromaDB · **Korpus:** {TOTAL:,} tez ·
**Kaynak:** umutertugrul/turkish-academic-theses-dataset (CC-BY-4.0)
"""
    )
    with gr.Row():
        with gr.Column(scale=4):
            q = gr.Textbox(
                label="Sorgu",
                placeholder="örn: derin öğrenme görüntü sınıflandırma",
                lines=2,
            )
        with gr.Column(scale=1):
            k = gr.Slider(1, 10, value=5, step=1, label="Top-K")
    btn = gr.Button("Ara", variant="primary")
    out = gr.Markdown()

    gr.Examples(
        examples=[
            ["derin öğrenme görüntü sınıflandırma", 5],
            ["yapay zeka tıbbi tanı", 5],
            ["doğal dil işleme türkçe", 5],
            ["evrişimsel sinir ağı kanser tespiti", 5],
            ["transformer mimarisi metin sınıflandırma", 5],
        ],
        inputs=[q, k],
    )

    btn.click(_result_md, inputs=[q, k], outputs=out)
    q.submit(_result_md, inputs=[q, k], outputs=out)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
