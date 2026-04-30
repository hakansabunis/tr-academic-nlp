# Privacy & KVKK Compliance

## Summary

`tr-academic-nlp` is designed to be **KVKK-compliant when run in local mode**.
Inference can run entirely on your machine without sending user-provided text to
external services.

## What data the toolkit handles

| Data | Where it lives | Notes |
|---|---|---|
| Pre-built thesis abstracts (~500K) | HuggingFace Hub (`hakansabunis/tr-thesis-academic-ready`) | Derived from `umutertugrul/turkish-academic-theses-dataset` (CC-BY-4.0); only public abstracts + metadata, no full text |
| Pre-computed embeddings | HuggingFace Hub | Lossy, non-reversible |
| User input text (PDFs, queries) | **Local machine only** | Never persisted to disk unless `cache=True` is explicitly set |
| User-uploaded documents | **Local machine only** | Never transmitted off the user's machine |

## Web search mode

The SDK exposes a `web` parameter:

- `web=True` (**default**): RAG augments local results with Brave Search /
  SearXNG queries. The user's query string IS sent to the configured search
  provider. The SDK logs a warning on initialization.
- `web=False`: Fully local mode. No outbound network calls during inference.
  Use this for KVKK-sensitive deployments.

```python
from tr_academic_nlp import AcademicRAG

# KVKK-compliant local mode
rag = AcademicRAG(corpus="yok-tez", web=False)
```

## Cache behavior

- Model weights downloaded from HuggingFace Hub are cached in the standard
  `~/.cache/huggingface/` directory (or `HF_HOME` if set).
- Document embeddings are cached **only if the user opts in**:

```python
rag = AcademicRAG(documents=["paper.pdf"], cache=True)  # opt-in
```

By default, embeddings of user-supplied documents are computed in memory and
discarded after the session.

## Deleting cached data

```bash
# Remove all HuggingFace caches
rm -rf ~/.cache/huggingface/

# Remove user RAG caches (if cache=True was used)
rm -rf ~/.cache/tr_academic_nlp/
```

## Scraping policy

The toolkit does NOT include scrapers for YÖK Tez Merkezi or DergiPark in its
required scope. The thesis corpus is sourced from a publicly licensed
HuggingFace dataset (CC-BY-4.0). An optional DergiPark fetcher is available;
when used, it respects rate limits and collects only public metadata.

## KVKK compliance statement

When `web=False` is set and `cache=True` is NOT enabled, no user text data is
shared with third parties or persisted to disk by this toolkit. This makes the
toolkit suitable for institutional deployments under KVKK
(Kişisel Verilerin Korunması Kanunu) constraints, subject to the user's own
review of their environment.

This is a self-described compliance posture; a formal KVKK audit is outside
the scope of this open-source project.
