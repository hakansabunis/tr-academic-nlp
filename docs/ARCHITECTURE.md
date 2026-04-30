# Architecture

> **Status:** Skeleton — populated incrementally as components are built.
> See [`turkce-akademi-YOL-HARITASI.md`](../../tools/turkce-akademi-YOL-HARITASI.md) §6 for the high-level system diagram.

## System overview

(High-level diagram from yol-haritasi §6 will be embedded here as `architecture.svg` once Faz 0 design is finalized.)

```
User interfaces:
  HF Space (Gradio)  |  Python SDK  |  Claude Skills (×5)
        ↓                  ↓                  ↓
        └──────────────────┼──────────────────┘
                           ↓
        ┌──────────────────┴──────────────────┐
        ↓                                      ↓
  Core models (×6)                      Data layer
  - trakad-embed-v1                     - tr-thesis-academic-ready
  - trakad-ner-v1                       - tr-thesis-embeddings-v1
  - trakad-citation-v1                  - tr-academic-ner-corpus
  - trakad-summarizer-v1                - tr-citation-pairs-tr
  - trakad-detector-v1                  - tr-ai-vs-human-academic
  - trakad-reasoner-3b (opt.)           ChromaDB (default) | FAISS (opt)
                                        Web search (opt., default ON)
```

## Design decisions

### Why Apache 2.0 over MIT?

Anthropic's [`anthropics/skills`](https://github.com/anthropics/skills) repo
uses Apache 2.0 across most skills. Aligning license maximizes ecosystem
acceptance probability when submitting skills upstream. Both licenses are
similarly permissive.

### Why ChromaDB default, FAISS optional?

- ChromaDB has native metadata filtering (year, field, etc.) and incremental
  add (user-uploaded PDFs need this).
- FAISS is faster and more memory-efficient for static large indexes —
  exposed as opt-in (`backend="faiss"`) for advanced users.

### Why derive from upstream dataset instead of scraping?

`umutertugrul/turkish-academic-theses-dataset` already provides 650K abstracts
under CC-BY-4.0. Re-scraping would (a) take a week of unnecessary work,
(b) produce a smaller corpus, (c) be a wheel-reinvention anti-pattern.
v2.3 of the project plan drops the scraper requirement in favor of a
deterministic derivation pipeline. See [`DERIVATION.md`](../DERIVATION.md).

### Why TR-MTEB instead of a self-authored embedding benchmark?

TR-MTEB (Baysan & Güngör, Findings of EMNLP 2025) is the peer-reviewed
standard for Turkish embedding evaluation. Self-authored metrics are weaker
in defense; aligning to a published benchmark makes results comparable to
the broader Turkish NLP community. See [`BENCHMARKS.md`](../BENCHMARKS.md).

### Why no AI humanizer?

Building a "Turnitin bypass" tool would constitute an academic dishonesty
aid — incompatible with Anthropic's Usage Policy and unjustifiable in a
capstone defense. The toolkit instead ships an **AI detector** (the
defensive counterpart). See `turkce-akademi-YOL-HARITASI.md` Appendix B.

### Why split into 5 single-purpose Claude Skills instead of one mega-skill?

Anthropic Skills convention favors single-focus skills. Bundling reduces
discoverability and violates the "tek odak" principle in
[Requirement 13.2](../../tools/.kiro/specs/tr-academic-nlp/requirements.md).

## Component-level docs

(To be added as components are built.)

- `data/derive/` — Faz 1
- `models/ner/` — Faz 3
- `models/citation/` — Faz 4
- `models/embedder/` — Faz 5
- `models/summarizer/` — Faz 6
- `models/detector/` — Faz 6.5
- `models/reasoner/` — Faz 7 (optional)
- `sdk/tr_academic_nlp/` — Faz 8
- `space/app.py` — Faz 9.5
- `skills/*/` — Faz 9.7

## Update policy

This file is updated whenever a major design decision is made or a component
is added. Each design decision must include the rationale for the choice
and the alternatives considered (per Requirement 15.6).
