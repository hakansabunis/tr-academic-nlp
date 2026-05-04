---
title: trakad — Türkçe Akademik Arama
emoji: 📚
colorFrom: indigo
colorTo: pink
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: apache-2.0
short_description: Türkçe akademik tezlerde semantic search (48k+ abstract)
---

# trakad — Türkçe Akademik Semantic Search

48,376 Türkçe tez özeti üzerinde **anlam-tabanlı** arama. Vektör tabanlı
retrieval; klasik keyword taramasının kaçırdığı eş anlamlı / yakın anlamlı
ifadeleri yakalar.

## Mimari

- **Embedding:** `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` (768-dim)
- **Index:** ChromaDB (HNSW)
- **Korpus:** [`umutertugrul/turkish-academic-theses-dataset`](https://huggingface.co/datasets/umutertugrul/turkish-academic-theses-dataset) (CC-BY-4.0)
- **Pre-built index:** `hakansabunis/trakad-rag-index-mpnet`

## Kaynak kod

GitHub: <https://github.com/hakansabunis/tr-academic-nlp>

İlgili araştırma & roadmap dokümanları repo'daki `turkce-akademi-YOL-HARITASI.md` içinde.
