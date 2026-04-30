# Learning Log — Faz 0 Research Notes

> **Purpose:** Per Requirement 1 (Faz 0 — Research & Learning Infrastructure),
> every technical component must be researched before implementation begins.
> Each topic below requires a minimum 200-word summary covering:
> - **Selected approach** + rationale
> - **Rejected alternatives** + why
> - **Hardware budget** for RTX 3050 Laptop 4GB GPU (where applicable)
>
> Entries are recorded in chronological order. Add the date when you start a
> topic and the date when you finish.

---

## Topic 1 — Web scraping with rate limiting

**Status:** Likely deprioritized (Faz 1 v2.3 uses `umutertugrul/turkish-academic-theses-dataset` directly; scraping is now optional for DergiPark only).
**Started:**
**Completed:**

### Selected approach


### Rejected alternatives


### Hardware budget


---

## Topic 2 — BERTurk fine-tuning for token classification

**Used in:** Faz 3 (NER `trakad-ner-v1`), Faz 6.5 (AI detector `trakad-detector-v1`).
**Started:**
**Completed:**

### Selected approach


### Rejected alternatives


### Hardware budget


---

## Topic 3 — sentence-transformers contrastive training

**Used in:** Faz 5 (embedder `trakad-embed-v1`).
**Started:**
**Completed:**

### Selected approach


### Rejected alternatives


### Hardware budget


---

## Topic 4 — mT5 abstractive summarization fine-tuning

**Used in:** Faz 6 (summarizer `trakad-summarizer-v1`).
**Started:**
**Completed:**

### Selected approach


### Rejected alternatives


### Hardware budget


---

## Topic 5 — QLoRA / PEFT (BitsAndBytes 4-bit)

**Used in:** Faz 7 (reasoner `trakad-reasoner-3b`, optional final phase).
**Started:**
**Completed:**

### Selected approach


### Rejected alternatives


### Hardware budget


---

## Topic 6 — ChromaDB vs FAISS

**Used in:** Faz 8 (RAG in SDK).
**Started:**
**Completed:**

### Selected approach


### Rejected alternatives


### Hardware budget


---

## Topic 7 — Gradio Space (CPU-free tier limitations + quantized loading)

**Used in:** Faz 9.5 (HF Space).
**Started:**
**Completed:**

### Selected approach


### Rejected alternatives


### Hardware budget


---

## Topic 8 — Python packaging (pyproject.toml + PyPI publish)

**Used in:** Faz 8 (SDK release).
**Started:**
**Completed:**

### Selected approach


### Rejected alternatives


### Hardware budget


---

## Topic 9 — Anthropic Skills spec format

Subtopics:
- SKILL.md schema (YAML frontmatter: name, description with when-to-use + when-NOT-to-use)
- `anthropics/skills` repo audit — read existing Document skills (pdf, docx, pptx, xlsx) and identify common patterns
- agentskills.io standard spec

**Used in:** Faz 9.7 (Claude Skills package).
**Started:**
**Completed:**

### Selected approach


### Rejected alternatives


### Hardware budget


---

## Topic 10 — AI text detection

Subtopics:
- GPTZero / DetectGPT approaches
- Perplexity-based vs classifier-based methods
- Calibration (temperature scaling, isotonic regression)

**Used in:** Faz 6.5 (AI detector).
**Started:**
**Completed:**

### Selected approach


### Rejected alternatives


### Hardware budget


---

## Topic 11 — TR-MTEB paper reading + reproduction

Reference: Baysan & Güngör, Findings of EMNLP 2025.
- Read the paper end-to-end.
- Clone `selmanbaysan/mteb_tr` and run baseline against an off-the-shelf BERTurk model.
- Identify the academic-domain task subset (or note its absence and plan to contribute one).

**Used in:** Faz 5 (embedder evaluation).
**Started:**
**Completed:**

### Selected approach


### Rejected alternatives


### Hardware budget


---

## Topic 12 — umutertugrul dataset audit

- Load `umutertugrul/turkish-academic-theses-dataset` with `datasets` lib.
- Compute basic stats: discipline distribution, year range, abstract length distribution, empty/duplicate rate.
- Decide filter thresholds (target: ~500K usable abstracts after filtering).

**Used in:** Faz 1 (dataset derivation).
**Started:**
**Completed:**

### Selected approach


### Rejected alternatives


### Hardware budget


---

## Notes

- Each topic must be completed before starting any code in the corresponding phase.
- Rejected alternatives are as important as the selected approach — they show the reasoning trail.
- Hardware budgets matter most for Topics 2, 3, 4, 5 (fine-tuning) and Topic 7 (Space deployment).
- This log is permanent; when revising approaches later, add a new dated entry rather than overwriting.
