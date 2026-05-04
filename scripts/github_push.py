"""Create GitHub repo + add remote + push.

Reads GITHUB_TOKEN from .env (PAT with `repo` scope).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
REPO_NAME = "tr-academic-nlp"
REPO_OWNER = "hakansabunis"  # kullanıcının GitHub username'i


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


def _ensure_repo(token: str) -> str:
    """Create the repo if it doesn't exist; return its clone URL."""
    api_url = "https://api.github.com/user/repos"
    payload = {
        "name": REPO_NAME,
        "description": (
            "Türkçe Akademik NLP — Secure Academic Middleware "
            "(local KVKK shield + frontier/local LLM prompt engine)"
        ),
        "private": False,
        "has_issues": True,
        "has_projects": False,
        "has_wiki": False,
        "auto_init": False,
    }
    req = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "tr-academic-nlp-bootstrap",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            print(f"[gh] Repo created: {body['html_url']}")
            return body["clone_url"]
    except urllib.error.HTTPError as exc:
        if exc.code == 422:
            # Already exists — that's fine, just compute the URL
            print(f"[gh] Repo already exists, continuing.")
            return f"https://github.com/{REPO_OWNER}/{REPO_NAME}.git"
        body = exc.read().decode("utf-8", errors="replace")
        print(f"[gh] HTTP {exc.code}: {body[:300]}", file=sys.stderr)
        raise


def _git(args: list[str], *, env: dict[str, str] | None = None) -> str:
    """Run git in the repo and return stdout."""
    proc = subprocess.run(
        ["git", *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed: {proc.stderr.strip() or proc.stdout.strip()}"
        )
    return proc.stdout.strip()


def main() -> None:
    _load_env()
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN not set in .env", file=sys.stderr)
        sys.exit(1)

    # 1. Create repo (or no-op if exists)
    clone_url = _ensure_repo(token)

    # 2. Set or update origin remote — embed token in URL for one-shot push
    #    Format: https://<token>@github.com/owner/repo.git
    auth_url = clone_url.replace("https://", f"https://{token}@")

    existing_remote = ""
    try:
        existing_remote = _git(["remote", "get-url", "origin"])
    except RuntimeError:
        pass

    if existing_remote:
        print("[gh] Updating existing 'origin' remote URL")
        _git(["remote", "set-url", "origin", auth_url])
    else:
        print("[gh] Adding 'origin' remote")
        _git(["remote", "add", "origin", auth_url])

    # 3. Push main + tags
    print("[gh] Pushing main branch...")
    push_out = _git(["push", "-u", "origin", "main"])
    print(push_out)

    # 4. Sanitize remote URL — replace token with public URL so it doesn't
    #    sit on disk in plain text inside .git/config
    print("[gh] Sanitizing remote URL (removing embedded token)...")
    _git(["remote", "set-url", "origin", clone_url])

    print(f"\n[gh] DONE -> https://github.com/{REPO_OWNER}/{REPO_NAME}")


if __name__ == "__main__":
    main()
