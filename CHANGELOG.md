# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial repository skeleton (Faz 0 — research & infrastructure setup).
- Apache 2.0 LICENSE.
- Project documentation: README, PRIVACY (KVKK), CONTRIBUTING, DERIVATION,
  BENCHMARKS, ARCHITECTURE, PERFORMANCE, EXTENSION, learning-log.
- `.github/workflows/ci.yml` — ruff + mypy + pytest gate.
- `pyproject.toml` — Python 3.11+, Apache 2.0, dev dependency pins.
- Directory layout for SDK, models, data, skills (×5), space, tests, notebooks.

### Roadmap
- Faz 0: research log (12 topics × 200+ words) → in progress
- Faz 1: dataset derivation from `umutertugrul/turkish-academic-theses-dataset`
- Faz 2-7: NER labeling → models → SDK → Space → Skills → Reasoner (optional)

[Unreleased]: https://github.com/hakansabunis/tr-academic-nlp/compare/HEAD
