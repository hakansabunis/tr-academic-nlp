"""Push trakad-ner-v1 to HuggingFace Hub.

Reads HF_TOKEN from .env (write scope required). Skips intermediate epoch
checkpoints — only the final merged model + tokenizer + README go to Hub.

Usage::

    python scripts/hf_push_ner.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and value and not os.environ.get(key):
            os.environ[key] = value


def main() -> None:
    _load_env()
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("ERROR: HF_TOKEN not set in .env or environment", file=sys.stderr)
        sys.exit(1)

    repo_id = "hakansabunis/trakad-ner-v1"
    folder = ROOT / "models" / "ner" / "trakad-ner-v1"
    if not folder.exists():
        print(f"ERROR: Model folder not found: {folder}", file=sys.stderr)
        sys.exit(1)

    from huggingface_hub import HfApi, create_repo

    print(f"[hf] Repo: {repo_id}")
    print(f"[hf] Folder: {folder}")

    print("[hf] Creating/ensuring repo...")
    url = create_repo(
        repo_id,
        token=token,
        repo_type="model",
        exist_ok=True,
        private=False,
    )
    print(f"[hf] Repo URL: {url}")

    api = HfApi(token=token)
    print("[hf] Uploading folder (skipping checkpoint-*/ subdirs)...")
    api.upload_folder(
        folder_path=str(folder),
        repo_id=repo_id,
        repo_type="model",
        ignore_patterns=["checkpoint-*/**"],
        commit_message=(
            "Initial release — trakad-ner-v1 "
            "(BERTurk fine-tune, F1=0.375 epoch 3)"
        ),
    )
    print(f"[hf] DONE -> https://huggingface.co/{repo_id}")


if __name__ == "__main__":
    main()
