"""Smoke test — Faz 0 placeholder.

Confirms package imports and CI infrastructure works. Replaced with real
unit tests as components are implemented (Faz 3+).
"""

import tr_academic_nlp


def test_version_string() -> None:
    assert isinstance(tr_academic_nlp.__version__, str)
    assert tr_academic_nlp.__version__.count(".") == 2


def test_public_api_placeholder() -> None:
    # Faz 0: __all__ is empty until components are implemented.
    assert isinstance(tr_academic_nlp.__all__, list)
