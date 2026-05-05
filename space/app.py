"""trakad — Türkçe akademik hybrid (vector + BM25) search demo.

HuggingFace Space entry point. On boot:
  1. Load (or download) ChromaDB index over 48k Turkish theses
  2. Pull all docs/metadata once, build an in-memory BM25 index
  3. Serve a Gradio UI that fuses vector + lexical retrieval via RRF

Locally: `python space/app.py`.
"""
from __future__ import annotations

import os
import re
import time
import urllib.parse
from pathlib import Path

import chromadb
import gradio as gr
from chromadb.utils import embedding_functions
from rank_bm25 import BM25Okapi

INDEX_REPO = os.getenv("TRAKAD_INDEX_REPO", "hakansabunis/trakad-rag-index-mpnet")
EMBED_MODEL = os.getenv(
    "TRAKAD_EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
)
COLLECTION = "turkish_theses"
# YÖK Tez Merkezi has no public deep-link by tez_no (session-based access).
# Best UX: open a Google search prefilled with the title; YÖK page surfaces
# in the first results so the user can verify in one click.
YOK_HOME = "https://tez.yok.gov.tr/UlusalTezMerkezi/giris.jsp"
GOOGLE_SEARCH_TMPL = "https://www.google.com/search?q={q}"

# RRF parameters
RRF_K = 60
N_CANDIDATES_MULT = 4  # per branch, candidates = top_k * mult


def _resolve_db_path() -> str:
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent / "data" / "chroma_db",
        here / "chroma_db",
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


_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def _tokenize_tr(text: str) -> list[str]:
    """Naive Turkish tokenization: lowercase + word-boundary split.

    No stemming; relies on substring overlap from BM25's term matching. Good
    enough for first iteration over academic abstracts where terms repeat.
    """
    return _TOKEN_RE.findall((text or "").lower())


print("[trakad] booting...")
DB_PATH = _resolve_db_path()
client = chromadb.PersistentClient(path=DB_PATH)
embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
collection = client.get_or_create_collection(name=COLLECTION, embedding_function=embed_fn)
TOTAL = collection.count()
print(f"[trakad] collection ready: {TOTAL} items")

print("[trakad] pulling docs for BM25...")
t0 = time.time()
_dump = collection.get(include=["documents", "metadatas"])
ALL_IDS: list[str] = _dump["ids"]
ALL_DOCS: list[str] = _dump["documents"]
ALL_METAS: list[dict] = _dump["metadatas"]
ID_TO_IDX = {tid: i for i, tid in enumerate(ALL_IDS)}
print(f"[trakad] pulled {len(ALL_IDS)} docs in {time.time()-t0:.1f}s")

print("[trakad] building BM25 index...")
t0 = time.time()
_TOKENIZED = [_tokenize_tr(d) for d in ALL_DOCS]
BM25 = BM25Okapi(_TOKENIZED)
print(f"[trakad] BM25 ready in {time.time()-t0:.1f}s")


def _hybrid_search(query: str, top_k: int) -> list[dict]:
    """Vector + BM25 with Reciprocal Rank Fusion.

    Returns up to ``top_k`` items, each with id, doc, meta. Branches retrieve
    ``top_k * N_CANDIDATES_MULT`` candidates so RRF has overlap to fuse.
    """
    n = max(top_k * N_CANDIDATES_MULT, 20)

    # Vector branch
    vec_res = collection.query(query_texts=[query], n_results=n)
    vec_ids = vec_res["ids"][0]
    vec_rank = {tid: i + 1 for i, tid in enumerate(vec_ids)}

    # BM25 branch
    q_tokens = _tokenize_tr(query)
    bm25_scores = BM25.get_scores(q_tokens)
    top_idx = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:n]
    bm25_ids = [ALL_IDS[i] for i in top_idx]
    bm25_rank = {tid: i + 1 for i, tid in enumerate(bm25_ids)}

    # RRF: score = sum(1 / (k + rank)) across branches
    candidates = set(vec_ids) | set(bm25_ids)
    rrf = {}
    for tid in candidates:
        s = 0.0
        if tid in vec_rank:
            s += 1.0 / (RRF_K + vec_rank[tid])
        if tid in bm25_rank:
            s += 1.0 / (RRF_K + bm25_rank[tid])
        rrf[tid] = s

    sorted_ids = sorted(rrf.keys(), key=lambda t: rrf[t], reverse=True)[:top_k]

    out = []
    for tid in sorted_ids:
        idx = ID_TO_IDX[tid]
        out.append({
            "id": tid,
            "doc": ALL_DOCS[idx],
            "meta": ALL_METAS[idx],
            "rrf": rrf[tid],
            "in_vec": tid in vec_rank,
            "in_bm25": tid in bm25_rank,
        })
    return out


def _result_md(query: str, top_k: int) -> str:
    if not query.strip():
        return "_Sorgu girin._"
    results = _hybrid_search(query, top_k)
    if not results:
        return "_Sonuç yok._"

    lines = [f"### Top-{len(results)} eşleşme — sorgu: *{query}*", ""]
    for i, r in enumerate(results, start=1):
        m = r["meta"]
        title = m.get("title", "Başlıksız")
        author = m.get("author", "?")
        year = m.get("year", "?")
        subject = m.get("subject", "?")
        tez_no = r["id"]
        doc = r["doc"] or ""

        snippet = doc.strip().replace("\n", " ")
        if len(snippet) > 350:
            snippet = snippet[:347] + "..."

        # Google search by title — most reliable way to land on the YÖK page
        gquery = urllib.parse.quote_plus(f'"{title}" YÖK tez')
        google_link = GOOGLE_SEARCH_TMPL.format(q=gquery)

        lines.append(f"**[{i}] {title}**")
        lines.append(f"_{author} · {year} · {subject}_")
        lines.append("")
        lines.append(f"> {snippet}")
        lines.append("")
        lines.append(f"🔍 [Google'da ara]({google_link})  ·  [YÖK Tez Merkezi]({YOK_HOME})")
        lines.append("")
        lines.append("---")
    return "\n".join(lines)


with gr.Blocks(title="trakad — Türkçe Akademik Arama") as demo:
    gr.Markdown(
        f"""
# trakad — Türkçe Akademik Arama

{TOTAL:,} Türkçe tez özeti üzerinde anlam-tabanlı arama. "Yapay zeka"
yazınca "AI", "makine öğrenmesi" geçen tezler de yakalanır.

_Korpus: [umutertugrul/turkish-academic-theses-dataset](https://huggingface.co/datasets/umutertugrul/turkish-academic-theses-dataset) (CC-BY-4.0)_
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
            ["federe öğrenme sağlık verisi", 5],
        ],
        inputs=[q, k],
    )

    btn.click(_result_md, inputs=[q, k], outputs=out)
    q.submit(_result_md, inputs=[q, k], outputs=out)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
