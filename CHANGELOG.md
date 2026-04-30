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
- **Faz 1 (in progress):**
  - `data/derive/load_umutertugrul.py` — derivation pipeline for
    `tr-thesis-academic-ready` (R2 revised v2.3 + R17). Deterministic NFC
    normalization, abstract length filter, duplicate `tez_no` filter,
    quality score, derivation report (JSON).
  - `tests/unit/test_derive_filters.py` — 18 unit tests covering the pure
    filter functions; runs without the upstream dataset.

### Roadmap
- Faz 1: smoke-run pipeline on a small sample, then full ~500K derivation.
- Faz 2-7: NER labeling → models → SDK → Space → Skills → Reasoner (optional).

[Unreleased]: https://github.com/hakansabunis/tr-academic-nlp/compare/HEAD
