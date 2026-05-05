"""trakad — Türkçe akademik hybrid (vector + BM25) search + RAG synthesis.

HuggingFace Space entry point. On boot:
  1. Load (or download) ChromaDB index over 48k Turkish theses
  2. Pull all docs/metadata once, build an in-memory BM25 index
  3. Serve a Gradio UI that fuses vector + lexical retrieval via RRF,
     optionally synthesizes a Turkish academic answer with citations
     (BYO Gemini API key — free tier).

Locally: `python space/app.py`.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
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
YOK_HOME = "https://tez.yok.gov.tr/UlusalTezMerkezi/giris.jsp"
GOOGLE_SEARCH_TMPL = "https://www.google.com/search?q={q}"

# RRF parameters
RRF_K = 60
N_CANDIDATES_MULT = 4

# Gemini config
GEMINI_MODEL = os.getenv("TRAKAD_GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_URL_TMPL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
)

SYNTH_SYSTEM = """Sen Türkçe akademik literatürde uzman bir araştırma asistanısın.
Görevin: aşağıda verilen TÜRKÇE TEZ KAYNAKLARINI kullanarak kullanıcının sorusuna
Türkçe akademik üslupta cevap vermek.

KURALLAR:
1. Sadece KAYNAKLAR bölümündeki bilgilere dayan. Kaynaklarda yer almayan bir
   bilgiyi UYDURMA. Bilinmeyen kısımları "incelenen kaynaklarda tespit edilemedi"
   diye belirt.
2. Her cümlenin sonuna [1], [2] biçiminde numaralı atıf koy. Tek cümle birden
   çok kaynaktan besleniyorsa [1, 3] gibi yaz.
3. Pasif çatı, üçüncü tekil şahıs, akademik terminoloji kullan
   ("şudur ki", "büyük oranda" gibi konuşma dilini kullanma).
4. En fazla 200 kelime, 2-3 paragraf. Liste değil paragraf.
5. Cevabı yalnızca düz metin olarak ver — başlık, bullet, kod bloğu KOYMA.
"""


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
    n = max(top_k * N_CANDIDATES_MULT, 20)

    vec_res = collection.query(query_texts=[query], n_results=n)
    vec_ids = vec_res["ids"][0]
    vec_rank = {tid: i + 1 for i, tid in enumerate(vec_ids)}

    q_tokens = _tokenize_tr(query)
    bm25_scores = BM25.get_scores(q_tokens)
    top_idx = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:n]
    bm25_ids = [ALL_IDS[i] for i in top_idx]
    bm25_rank = {tid: i + 1 for i, tid in enumerate(bm25_ids)}

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
        })
    return out


def _build_context(results: list[dict]) -> str:
    """Format retrieved theses as numbered context for the LLM."""
    lines = []
    for i, r in enumerate(results, start=1):
        m = r["meta"]
        title = m.get("title", "Başlıksız")
        author = m.get("author", "?")
        year = m.get("year", "?")
        doc = (r["doc"] or "").strip().replace("\n", " ")
        # Cap each context entry so the prompt stays small
        if len(doc) > 800:
            doc = doc[:797] + "..."
        lines.append(f"[{i}] {title} — {author} ({year})\n    Özet: {doc}")
    return "\n\n".join(lines)


def _gemini_generate(api_key: str, system: str, user: str, timeout: int = 60) -> str:
    """Single-shot Gemini call via REST. Returns generated text or raises."""
    url = GEMINI_URL_TMPL.format(model=GEMINI_MODEL, key=api_key)
    body = {
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "systemInstruction": {"parts": [{"text": system}]},
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 800,
        },
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        payload = json.loads(r.read().decode("utf-8"))
    candidates = payload.get("candidates") or []
    if not candidates:
        raise RuntimeError(f"Gemini boş yanıt döndü: {payload}")
    parts = candidates[0].get("content", {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts).strip()
    if not text:
        raise RuntimeError(f"Gemini boş metin döndü: {payload}")
    return text


def _synthesize(query: str, results: list[dict], api_key: str) -> str:
    """Run RAG synthesis. Returns markdown answer or error notice."""
    if not api_key.strip():
        return (
            "_Synthesis için Gemini API key gerekli. "
            "[Ücretsiz al](https://aistudio.google.com/apikey) ve sağdaki kutuya yapıştır._"
        )
    if not results:
        return "_Sentez için kaynak bulunamadı._"

    ctx = _build_context(results)
    user_prompt = f"KAYNAKLAR:\n{ctx}\n\nSORU: {query}\n\nCEVAP (Türkçe akademik üslup, atıflı):"

    try:
        answer = _gemini_generate(api_key.strip(), SYNTH_SYSTEM, user_prompt)
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")[:300]
        except Exception:
            pass
        return f"_Gemini API hatası (HTTP {e.code}): {body}_"
    except Exception as e:
        return f"_Hata: {type(e).__name__}: {e}_"

    return f"### Sentez\n\n{answer}"


def _do_search(query: str, top_k: int, synth_on: bool, api_key: str):
    """Combined handler: returns (synthesis_md, results_md)."""
    if not query.strip():
        return "", "_Sorgu girin._"

    results = _hybrid_search(query, top_k)
    if not results:
        return "", "_Sonuç yok._"

    # Results markdown
    rlines = [f"### Top-{len(results)} eşleşme — sorgu: *{query}*", ""]
    for i, r in enumerate(results, start=1):
        m = r["meta"]
        title = m.get("title", "Başlıksız")
        author = m.get("author", "?")
        year = m.get("year", "?")
        subject = m.get("subject", "?")
        doc = r["doc"] or ""

        snippet = doc.strip().replace("\n", " ")
        if len(snippet) > 350:
            snippet = snippet[:347] + "..."

        gquery = urllib.parse.quote_plus(f'"{title}" YÖK tez')
        google_link = GOOGLE_SEARCH_TMPL.format(q=gquery)

        rlines.append(f"**[{i}] {title}**")
        rlines.append(f"_{author} · {year} · {subject}_")
        rlines.append("")
        rlines.append(f"> {snippet}")
        rlines.append("")
        rlines.append(f"🔍 [Google'da ara]({google_link})  ·  [YÖK Tez Merkezi]({YOK_HOME})")
        rlines.append("")
        rlines.append("---")
    results_md = "\n".join(rlines)

    if synth_on:
        synth_md = _synthesize(query, results, api_key)
    else:
        synth_md = ""

    return synth_md, results_md


with gr.Blocks(title="trakad — Türkçe Akademik Arama") as demo:
    gr.Markdown(
        f"""
# trakad — Türkçe Akademik Arama

{TOTAL:,} Türkçe tez özeti üzerinde anlam-tabanlı arama. "Yapay zeka"
yazınca "AI", "makine öğrenmesi" geçen tezler de yakalanır. **Sentez
modu** açıldığında bulunan kaynaklardan Türkçe akademik üslupta atıflı
cevap üretir.

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

    with gr.Row():
        synth_toggle = gr.Checkbox(
            label="Sentez modu (atıflı Türkçe akademik cevap)",
            value=False,
        )
        api_key = gr.Textbox(
            label="Gemini API key",
            placeholder="Ücretsiz: https://aistudio.google.com/apikey",
            type="password",
            visible=False,
        )

    synth_toggle.change(
        lambda on: gr.update(visible=on),
        inputs=[synth_toggle],
        outputs=[api_key],
    )

    btn = gr.Button("Ara", variant="primary")
    synth_out = gr.Markdown()
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

    btn.click(_do_search, inputs=[q, k, synth_toggle, api_key], outputs=[synth_out, out])
    q.submit(_do_search, inputs=[q, k, synth_toggle, api_key], outputs=[synth_out, out])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
