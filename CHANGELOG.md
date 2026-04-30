# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Faz 0 complete:**
  - Initial repository skeleton — directory layout for SDK, models, data,
    skills (×5), space, tests, notebooks.
  - Apache 2.0 LICENSE.
  - Project documentation: README, PRIVACY (KVKK), CONTRIBUTING, DERIVATION,
    BENCHMARKS, ARCHITECTURE, PERFORMANCE, EXTENSION.
  - `docs/learning-log.md` — 12 topic research summaries (R1.3–R1.6).
  - `.github/workflows/ci.yml` — ruff + mypy + pytest gate.
  - `pyproject.toml` — Python 3.11+, Apache 2.0, dev dependency pins.
- **Faz 1 — Dataset derivation:**
  - `data/derive/load_umutertugrul.py` — derivation pipeline for
    `tr-thesis-academic-ready` (R2 revised v2.3 + R17). Deterministic NFC
    normalization, abstract length filter, duplicate `tez_no` filter,
    quality score, derivation report (JSON).
  - `tests/unit/test_derive_filters.py` (19 tests) +
    `tests/integration/test_derive_pipeline.py` (6 tests) — full pipeline
    validated end-to-end on a mock dataset (independent of upstream auth).
  - `tests/conftest.py` — sys.path setup for in-tree imports.
- **Faz 2 — NER labeling pipeline (regex pass):**
  - `data/labeling/entity_types.py` — canonical 7-entity schema + BIO tag
    table (R4.1).
  - `data/labeling/regex_rules.py` — 7 regex extractors (YIL, KURUM,
    METODOLOJI, DATASET, METRİK, YAZAR, DERGİ) with confidence scoring
    and overlap resolution.
  - `data/labeling/conll_writer.py` — tokenizer + BIO tag assignment +
    CoNLL-2003 round-trip (R4.2).
  - `data/labeling/auto_label.py` — full labeling pipeline with
    deterministic 80/10/10 split (hash-based, R4.7) and low-confidence
    span queue for the upcoming Ollama verification pass.
  - 47 new unit + integration tests for entity types, regex rules, CoNLL
    writer, and auto-label pipeline.

### Roadmap
- Faz 1 next: real upstream smoke run requires `huggingface-cli login` +
  accepting the dataset gating; full ~500K derivation thereafter.
- Faz 2 next: Ollama qwen2.5:7b verification pass for low-confidence spans
  (`data/labeling/ollama_verify.py`); inter-annotator κ measurement on
  500-sample validation set.
- Faz 3-7: NER training → embedder → summarizer → AI detector → SDK →
  Space → Skills → Reasoner (optional).

[Unreleased]: https://github.com/hakansabunis/tr-academic-nlp/compare/HEAD
