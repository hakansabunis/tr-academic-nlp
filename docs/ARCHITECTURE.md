# Architecture

> **Status:** Middleware Pivot — System is transitioning from custom models to a secure API middleware.

## System overview

```
User interfaces:
  HF Space (Gradio)  |  Python SDK  |  Claude Skills
        ↓                  ↓                  ↓
        └──────────────────┼──────────────────┘
                           ↓
              AcademicPipeline (Middleware Core)
                           ↓
  ┌─────────────────────────────────────────────────────────┐
  │ 1. Local RAG (ChromaDB)                                 │
  │    - Retrieves context using trakad-embed-v1            │
  │                                                         │
  │ 2. Local Anonymizer                                     │
  │    - Uses trakad-ner-v1 to mask sensitive entities      │
  │    - Dr. Ahmet -> [KİŞİ_1]                              │
  │                                                         │
  │ 3. Academic Prompt Engine                               │
  │    - Injects domain-specific Turkish instructions       │
  │                                                         │
  │ 4. Frontier API Integration                             │
  │    - Sends masked data + prompt to Claude/GPT-4o        │
  │                                                         │
  │ 5. De-anonymizer                                        │
  │    - Restores [KİŞİ_1] -> Dr. Ahmet before output       │
  └─────────────────────────────────────────────────────────┘
```

## Design decisions

### Why pivot to a Middleware Architecture?

General-purpose LLMs (Claude 3.5, GPT-4o) are advancing too rapidly for small, specialized custom models (like a local 3B reasoner or an mT5 summarizer) to compete. However, these frontier models still face two major barriers in Turkish academia:
1. **KVKK / Privacy:** Academics cannot upload unpublished theses or sensitive datasets to third-party APIs.
2. **Domain Register:** Frontier models often hallucinate Turkish academic register and citation formats.

This architecture solves both: it leverages the immense intelligence of frontier models via API, but wraps them in a **local security and prompt-engineering shell**. 

### Why ChromaDB default?

- ChromaDB has native metadata filtering (year, field, etc.) and incremental add.
- It operates entirely locally, which is mandatory for the privacy guarantees of this toolkit.

### What happened to the AI Detector (`trakad-detector-v1`)?

The AI text detector has been deprecated from the core pipeline. Statistical AI detection is fundamentally flawed, especially for academic texts which inherently use formulaic, objective, "robotic" language. The false-positive rate on legitimate Turkish academic text is unacceptably high, creating severe ethical risks. The project now focuses entirely on the "Sword" (assistance) aspect securely.

### Why use `trakad-ner-v1` for Anonymization?

Instead of using NER merely for analysis, it is weaponized for defense. By locally detecting `PER` (Person), `ORG` (Organization), and `LOC` (Location) entities using a small local model (BERTurk fine-tune), we can strip personally identifiable information (PII) before it ever touches the network.

## Component-level docs

- `data/derive/` — Data preparation for local embedding.
- `models/embedder/` — Local embedding model (`trakad-embed-v1`).
- `models/ner/` — Local NER model (`trakad-ner-v1`) used for anonymization.
- `sdk/tr_academic_nlp/anonymizer.py` — The KVKK masking logic.
- `sdk/tr_academic_nlp/prompts/` — The academic prompt library.
- `sdk/tr_academic_nlp/pipeline.py` — The core `AcademicPipeline` orchestrator.

## Update policy

This file is updated whenever a major design decision is made or a component is added. Each design decision must include the rationale for the choice and the alternatives considered.
