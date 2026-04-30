"""Pytest configuration — add `sdk/` and project root to `sys.path`.

Allows tests to import the `tr_academic_nlp` package and `data.derive`
modules without requiring `pip install -e .` first. CI still runs an
editable install, but local devs can run `pytest` immediately after a
fresh clone.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SDK_PATH = ROOT / "sdk"

for path in (SDK_PATH, ROOT):
    str_path = str(path)
    if str_path not in sys.path:
        sys.path.insert(0, str_path)
