# Contributing to tr-academic-nlp

Thanks for your interest. This document covers dev setup, testing, and PR
conventions.

## Dev setup

Requires Python 3.11+.

```bash
git clone https://github.com/hakansabunis/tr-academic-nlp.git
cd tr-academic-nlp
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Tests

```bash
# Full test suite
pytest

# Coverage (target: >=80%)
pytest --cov=sdk/tr_academic_nlp --cov-report=term-missing

# Property tests only (hypothesis fuzz)
pytest tests/property/

# Performance budgets only
pytest -m perf
```

## Lint & type check

```bash
ruff check .
ruff format .
mypy --strict sdk/
```

CI runs all three on every PR. Merge is blocked until they pass.

## Project structure

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full layout.

Key directories:
- `sdk/tr_academic_nlp/` — Python SDK (public API)
- `models/` — model training scripts (one folder per model)
- `data/derive/` — dataset derivation pipelines (umutertugrul → academic-ready)
- `skills/` — Claude Skills (5 sub-skills, each Apache 2.0)
- `tests/` — `unit/`, `integration/`, `property/`

## PR conventions

1. **Open an issue first** for non-trivial changes. Discuss the approach before coding.
2. **Conventional commits**: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.
3. **Test your changes**: new code requires unit tests; bug fixes require
   regression tests.
4. **Update CHANGELOG.md** under "Unreleased".
5. **One concern per PR**: don't bundle unrelated changes.

## Skills contributions

If contributing a new sub-skill or modifying existing skills:
- Follow the [Anthropic Pre-Flight Checklist](../turkce-akademi-YOL-HARITASI.md#118-anthropic-submission-pre-flight-checklist--v22)
  (12 items: Apache 2.0, frontmatter, ≥5 examples, ≥10 tests, EXTENSION.md,
  demo GIF, README pitch, honest limitations, Turkish error messages, English
  docs, performance bench, CI green).
- Each skill is standalone — no shared dependencies between skills.

## Reporting issues

- **Bug**: include reproduction steps, expected vs actual behavior, Python version.
- **Feature**: explain the use case and why existing components don't cover it.
- **Question**: please use GitHub Discussions instead of issues.

## Code of conduct

Be respectful. Disagree on technical merit, not personal grounds. The maintainer
reserves the right to close abusive issues/PRs.

## License

By contributing, you agree your contributions are licensed under Apache 2.0.
