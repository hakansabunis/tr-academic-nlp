"""Push the local ChromaDB vector index to HF Hub as a dataset.

The dataset is consumed by the Gradio Space (`space/app.py`) on cold start
via `huggingface_hub.snapshot_download`.

Run: python scripts/hf_push_index.py
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
        print("ERROR: HF_TOKEN not set in .env", file=sys.stderr)
        sys.exit(1)

    repo_id = "hakansabunis/trakad-rag-index-mpnet"
    folder = ROOT / "data" / "chroma_db"
    if not folder.exists():
        print(f"ERROR: ChromaDB folder not found: {folder}", file=sys.stderr)
        sys.exit(1)

    from huggingface_hub import HfApi, create_repo

    print(f"[hf] Repo: {repo_id}")
    print(f"[hf] Folder: {folder}")
    size_mb = sum(p.stat().st_size for p in folder.rglob("*") if p.is_file()) / (1024 * 1024)
    print(f"[hf] Total size: {size_mb:.0f} MB")

    print("[hf] Creating/ensuring dataset repo...")
    url = create_repo(
        repo_id,
        token=token,
        repo_type="dataset",
        exist_ok=True,
        private=False,
    )
    print(f"[hf] Repo URL: {url}")

    api = HfApi(token=token)
    print("[hf] Uploading folder (this may take several minutes)...")
    api.upload_folder(
        folder_path=str(folder),
        repo_id=repo_id,
        repo_type="dataset",
        commit_message="Initial release — mpnet 768-dim index over 48,376 Turkish theses",
    )
    print(f"[hf] DONE -> https://huggingface.co/datasets/{repo_id}")


if __name__ == "__main__":
    main()
