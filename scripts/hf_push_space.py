"""Create + populate the HuggingFace Space (Gradio) for trakad demo.

Run: python scripts/hf_push_space.py
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
        print("ERROR: HF_TOKEN not set", file=sys.stderr)
        sys.exit(1)

    repo_id = "hakansabunis/trakad-academic-rag-demo"
    folder = ROOT / "space"
    if not folder.exists():
        print(f"ERROR: space/ folder not found: {folder}", file=sys.stderr)
        sys.exit(1)

    from huggingface_hub import HfApi, create_repo

    print(f"[hf] Space repo: {repo_id}")
    print(f"[hf] Folder: {folder}")

    print("[hf] Creating/ensuring space (gradio SDK)...")
    url = create_repo(
        repo_id,
        token=token,
        repo_type="space",
        space_sdk="gradio",
        exist_ok=True,
        private=False,
    )
    print(f"[hf] Space URL: {url}")

    api = HfApi(token=token)
    print("[hf] Uploading space/ contents...")
    api.upload_folder(
        folder_path=str(folder),
        repo_id=repo_id,
        repo_type="space",
        commit_message="Initial Gradio demo — Turkish academic semantic search over 48k theses",
    )
    print(f"[hf] DONE -> https://huggingface.co/spaces/{repo_id}")


if __name__ == "__main__":
    main()
