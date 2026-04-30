"""Batch NER labeling via the Claude Code CLI (``claude --print``).

Runs against a Pro/Max Claude subscription with no per-call API charge.
Each paragraph triggers one ``claude --print --model <m>`` subprocess
which counts as one message in your usage window. Plan accordingly:
Pro tier ~45 messages per 5h window, Max 5× ~225, Max 20× ~900.

Resume-safe: every successful paragraph is appended to a JSONL output
file immediately. Re-running the script with the same ``--output``
skips paragraphs already present.

Usage::

    # 1) Smoke test — 5 paragraphs with Sonnet (faster than Haiku via CLI)
    python scripts/batch_label_via_claude_cli.py \\
        --paragraphs scripts/sample_paragraphs_small.jsonl \\
        --output docs/labeler-eval/cli-sonnet-smoke.jsonl \\
        --model sonnet

    # 2) Larger batch — Haiku, slower stream into checkpoint file
    python scripts/batch_label_via_claude_cli.py \\
        --paragraphs scripts/sample_paragraphs.jsonl \\
        --output docs/labeler-eval/cli-haiku-10.jsonl \\
        --model haiku
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.labeling.llm_label import (  # noqa: E402
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
    _parse_spans,
)
from data.labeling.entity_types import ENTITY_TYPES  # noqa: E402

# Defaults — tune via CLI
DEFAULT_TIMEOUT_SECONDS = 180
DEFAULT_PAUSE_SECONDS = 2.0
DEFAULT_MODEL = "sonnet"
DEFAULT_BATCH_PAUSE_SECONDS = 30.0  # Longer pause between batches to avoid rate limits
MAX_BATCH_RETRIES = 3

# `claude` CLI accepts these as model aliases (verified docs as of 2026-04):
# 'haiku', 'sonnet', 'opus' — or full IDs like 'claude-haiku-4-5-20251001'.
SUPPORTED_MODELS = {"haiku", "sonnet", "opus"}


@lru_cache(maxsize=1)
def _resolve_claude_executable() -> str:
    """Return the absolute path of the `claude` CLI on this system.

    Windows installs `claude` as `claude.cmd` (or `.bat`); Python's
    ``subprocess`` doesn't auto-append PATHEXT extensions when given a bare
    name with ``shell=False``. We probe the common variants so the user
    doesn't need to know the install detail.
    """
    candidates = ["claude", "claude.cmd", "claude.bat", "claude.exe"]
    for name in candidates:
        found = shutil.which(name)
        if found:
            return found
    raise RuntimeError(
        "Claude Code CLI bulunamadı. Tried: "
        + ", ".join(candidates)
        + ". PATH'i kontrol edin (which claude / where claude)."
    )


def call_claude_cli(
    paragraph_text: str,
    model: str = DEFAULT_MODEL,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> tuple[str, float]:
    """Invoke ``claude --print --model <m>`` once and return (stdout, elapsed_s).

    The full prompt (system + user) is fed via stdin to avoid argv escaping
    issues with multi-line Turkish content.
    """
    full_prompt = (
        SYSTEM_PROMPT
        + "\n\n"
        + USER_PROMPT_TEMPLATE.format(paragraph=paragraph_text)
    )
    claude_exe = _resolve_claude_executable()
    start = time.monotonic()
    proc = subprocess.run(
        [claude_exe, "--print", "--model", model],
        input=full_prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout,
        check=False,
    )
    elapsed = time.monotonic() - start
    if proc.returncode != 0:
        stderr_tail = (proc.stderr or "").strip()[-500:]
        raise RuntimeError(
            f"claude CLI exited {proc.returncode}: {stderr_tail or '(no stderr)'}"
        )
    return proc.stdout.strip(), elapsed


# ---------------------------------------------------------------------------
# Batch mode — multiple paragraphs in a single subprocess call
# ---------------------------------------------------------------------------
BATCH_SYSTEM_PROMPT = """You are a precise academic NER annotator for Turkish academic text.

You will receive a numbered list of paragraphs. For EACH paragraph, output one
JSON object with these exact keys:
- "paragraph_id": the id given for that paragraph
- "spans": a JSON array of entity span objects, each with keys:
    "start" (int), "end" (int), "entity" (str), "text" (str)

Output a SINGLE JSON ARRAY containing one object per input paragraph, in the
same order. No prose, no markdown fences, just the JSON array.

Entity types (exactly these 7): YAZAR, KURUM, DERGİ, YIL, METODOLOJI, DATASET, METRİK
- YAZAR: paper author full name (any format including "Soyad, Ad" or "A. Soyad")
- KURUM: university, institute, faculty, department, research center
- DERGİ: journal or conference name
- YIL: 4-digit year (1900-2030)
- METODOLOJI: ML model, algorithm, scientific method (CNN, BERT, k-means, etc.)
- DATASET: named dataset (MNIST, IMDB, YÖK Tez Merkezi corpus, etc.)
- METRİK: evaluation metric (F1, ROUGE-L, doğruluk, accuracy, etc.)

start/end are character offsets within THAT paragraph's text. text must equal
text[start:end] exactly."""


def _format_batch_prompt(batch: list[tuple[str, str]]) -> str:
    """Render a list of (paragraph_id, text) into the batch user prompt."""
    parts = ["Annotate the following Turkish academic paragraphs:\n"]
    for paragraph_id, text in batch:
        parts.append(f"\n=== paragraph_id: {paragraph_id} ===\n{text}\n")
    parts.append(
        "\nReturn a JSON array of objects "
        "[{\"paragraph_id\": ..., \"spans\": [...]}, ...] "
        "in the same order."
    )
    return "".join(parts)


def _parse_batch_response(raw: str) -> list[dict]:
    """Parse Claude's batch JSON-array response into per-paragraph dicts."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].lstrip()
    parsed = json.loads(raw)
    if not isinstance(parsed, list):
        raise ValueError("Batch response is not a top-level JSON array")
    return parsed


def call_claude_cli_batch(
    batch: list[tuple[str, str]],
    model: str = DEFAULT_MODEL,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> tuple[str, float]:
    """Run ONE subprocess for an entire batch of paragraphs.

    Trades per-paragraph isolation for huge throughput: ~30s subprocess
    overhead is amortized across the whole batch instead of being paid per
    paragraph. A bad JSON response fails the whole batch — the script retries
    by falling back to single-paragraph calls for that batch.
    """
    full_prompt = BATCH_SYSTEM_PROMPT + "\n\n" + _format_batch_prompt(batch)
    claude_exe = _resolve_claude_executable()
    start = time.monotonic()
    proc = subprocess.run(
        [claude_exe, "--print", "--model", model],
        input=full_prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout,
        check=False,
    )
    elapsed = time.monotonic() - start
    if proc.returncode != 0:
        stderr_tail = (proc.stderr or "").strip()[-500:]
        raise RuntimeError(
            f"claude CLI exited {proc.returncode}: {stderr_tail or '(no stderr)'}"
        )
    return proc.stdout.strip(), elapsed


def _read_paragraphs(path: Path) -> list[tuple[str, str]]:
    paragraphs: list[tuple[str, str]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            paragraphs.append((str(record["paragraph_id"]), record["text"]))
    return paragraphs


def _read_completed_ids(output_path: Path) -> set[str]:
    """Read existing JSONL output and collect already-labeled paragraph IDs."""
    if not output_path.exists():
        return set()
    completed: set[str] = set()
    with output_path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("succeeded"):
                completed.add(str(record.get("paragraph_id", "")))
    return completed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch NER labeling via Claude Code CLI (Pro/Max — no API charge)",
    )
    parser.add_argument(
        "--paragraphs",
        type=Path,
        required=True,
        help="JSONL file with one record per line (`paragraph_id` + `text`)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="JSONL output path; resume-safe (appends, skips done IDs)",
    )
    parser.add_argument(
        "--model",
        choices=sorted(SUPPORTED_MODELS),
        default=DEFAULT_MODEL,
        help=f"Claude model alias (default: {DEFAULT_MODEL!r})",
    )
    parser.add_argument(
        "--pause-seconds",
        type=float,
        default=DEFAULT_PAUSE_SECONDS,
        help="Seconds to wait between calls (default: %(default)s)",
    )
    parser.add_argument(
        "--batch-pause-seconds",
        type=float,
        default=DEFAULT_BATCH_PAUSE_SECONDS,
        help="Seconds to wait between batch calls to avoid rate limits (default: %(default)s)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Per-call subprocess timeout (default: %(default)ss)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional: stop after this many newly-labeled paragraphs",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help=(
            "Send N paragraphs in ONE subprocess call (default 1). "
            "Higher = far fewer subprocess startups, but a malformed "
            "response from Claude fails the whole batch. Try 10-30 for "
            "real workloads."
        ),
    )
    parser.add_argument(
        "--timeout-per-batch",
        type=int,
        default=600,
        help="Subprocess timeout when --batch-size > 1 (default: 600s)",
    )
    args = parser.parse_args()

    paragraphs = _read_paragraphs(args.paragraphs)
    completed = _read_completed_ids(args.output)
    pending = [(pid, text) for pid, text in paragraphs if pid not in completed]
    print(
        f"[cli] Total: {len(paragraphs)}, "
        f"already done: {len(completed)}, "
        f"pending: {len(pending)}",
    )
    if args.limit is not None:
        pending = pending[: args.limit]
        print(f"[cli] Limiting to first {len(pending)} this run")

    args.output.parent.mkdir(parents=True, exist_ok=True)

    success_count = 0
    failure_count = 0
    elapsed_total = 0.0

    # ------------------------------------------------------------------
    # BATCH MODE — one subprocess call covers many paragraphs
    # ------------------------------------------------------------------
    if args.batch_size > 1:
        batch_size = args.batch_size
        batch_pause = getattr(args, "batch_pause_seconds", DEFAULT_BATCH_PAUSE_SECONDS)
        
        with args.output.open("a", encoding="utf-8") as handle:
            for batch_start in range(0, len(pending), batch_size):
                batch = pending[batch_start : batch_start + batch_size]
                batch_idx = batch_start // batch_size + 1
                total_batches = (len(pending) + batch_size - 1) // batch_size
                
                # Retry loop with exponential backoff
                batch_success = 0
                batch_entities = 0
                attempt = 0
                success = False
                
                while attempt < MAX_BATCH_RETRIES and not success:
                    attempt += 1
                    try:
                        if attempt > 1:
                            wait_time = batch_pause * (2 ** (attempt - 2))
                            print(f"  [cli-batch] {batch_idx}/{total_batches} retry {attempt}/{MAX_BATCH_RETRIES}, waiting {wait_time:.1f}s...")
                            time.sleep(wait_time)
                        
                        raw_response, elapsed = call_claude_cli_batch(
                            batch, model=args.model, timeout=args.timeout_per_batch,
                        )
                        elapsed_total += elapsed
                        parsed_items = _parse_batch_response(raw_response)
                        by_id = {
                            str(item.get("paragraph_id", "")): item
                            for item in parsed_items
                            if isinstance(item, dict)
                        }
                        
                        for paragraph_id, text in batch:
                            item = by_id.get(paragraph_id)
                            if item is None:
                                failure_count += 1
                                handle.write(
                                    json.dumps(
                                        {
                                            "paragraph_id": paragraph_id,
                                            "text": text,
                                            "succeeded": False,
                                            "model": args.model,
                                            "elapsed_seconds": 0.0,
                                            "raw_response": "",
                                            "spans": [],
                                            "error": "paragraph_id missing in batch response",
                                        },
                                        ensure_ascii=False,
                                    )
                                    + "\n",
                                )
                                continue
                            # Re-run the per-paragraph span schema validation
                            item_json = json.dumps(item.get("spans", []), ensure_ascii=False)
                            spans = _parse_spans(item_json, ENTITY_TYPES)
                            record = {
                                "paragraph_id": paragraph_id,
                                "text": text,
                                "succeeded": True,
                                "model": args.model,
                                "elapsed_seconds": round(elapsed / max(1, len(batch)), 2),
                                "raw_response": item_json,
                                "spans": [
                                    {
                                        "start": s.start,
                                        "end": s.end,
                                        "entity": s.entity,
                                        "text": s.text,
                                        "confidence": s.confidence,
                                    }
                                    for s in spans
                                ],
                                "error": None,
                            }
                            success_count += 1
                            batch_success += 1
                            batch_entities += len(spans)
                            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                        handle.flush()
                        
                        print(
                            f"  [cli-batch] {batch_idx}/{total_batches} "
                            f"({len(batch)} paragraphs) "
                            f"-> {batch_success} ok, {batch_entities} entities, "
                            f"{elapsed:.1f}s ({elapsed / max(1, len(batch)):.1f}s/paragraph)"
                        )
                        success = True
                        
                    except Exception as exc:  # noqa: BLE001
                        if attempt < MAX_BATCH_RETRIES:
                            print(f"  [cli-batch] {batch_idx}/{total_batches} attempt {attempt}/{MAX_BATCH_RETRIES} FAIL — {exc}")
                        else:
                            print(f"  [cli-batch] {batch_idx}/{total_batches} FAILED all {MAX_BATCH_RETRIES} attempts — {exc}")
                            # Write per-paragraph fail markers for resume safety
                            for paragraph_id, text in batch:
                                failure_count += 1
                                handle.write(
                                    json.dumps(
                                        {
                                            "paragraph_id": paragraph_id,
                                            "text": text,
                                            "succeeded": False,
                                            "model": args.model,
                                            "elapsed_seconds": 0.0,
                                            "raw_response": "",
                                            "spans": [],
                                            "error": f"batch failure after {MAX_BATCH_RETRIES} retries: {type(exc).__name__}: {exc}",
                                        },
                                        ensure_ascii=False,
                                    )
                                    + "\n",
                                )
                            handle.flush()
                
                if batch_idx < total_batches and success:
                    time.sleep(batch_pause)

        print()
        print(f"[cli-batch] Done. Success: {success_count}, Fail: {failure_count}")
        if success_count:
            avg = elapsed_total / max(1, success_count)
            print(f"[cli-batch] Average per-paragraph time: {avg:.1f}s")
        return

    # ------------------------------------------------------------------
    # SINGLE-PARAGRAPH MODE (default, one subprocess per paragraph)
    # ------------------------------------------------------------------
    with args.output.open("a", encoding="utf-8") as handle:
        for idx, (paragraph_id, text) in enumerate(pending, start=1):
            try:
                raw_response, elapsed = call_claude_cli(
                    text, model=args.model, timeout=args.timeout,
                )
                elapsed_total += elapsed
                spans = _parse_spans(raw_response, ENTITY_TYPES)
                record = {
                    "paragraph_id": paragraph_id,
                    "text": text,
                    "succeeded": True,
                    "model": args.model,
                    "elapsed_seconds": round(elapsed, 2),
                    "raw_response": raw_response,
                    "spans": [
                        {
                            "start": s.start,
                            "end": s.end,
                            "entity": s.entity,
                            "text": s.text,
                            "confidence": s.confidence,
                        }
                        for s in spans
                    ],
                    "error": None,
                }
                success_count += 1
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                handle.flush()
                print(
                    f"  [cli] {idx}/{len(pending)} {paragraph_id} ok "
                    f"({len(spans)} entities, {elapsed:.1f}s)"
                )
            except Exception as exc:  # noqa: BLE001 — log every failure
                failure_count += 1
                record = {
                    "paragraph_id": paragraph_id,
                    "text": text,
                    "succeeded": False,
                    "model": args.model,
                    "elapsed_seconds": 0.0,
                    "raw_response": "",
                    "spans": [],
                    "error": f"{type(exc).__name__}: {exc}",
                }
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                handle.flush()
                print(f"  [cli] {idx}/{len(pending)} {paragraph_id} FAIL — {exc}")
            if idx < len(pending):
                time.sleep(args.pause_seconds)

    print()
    print(f"[cli] Done. Success: {success_count}, Fail: {failure_count}")
    if success_count:
        avg = elapsed_total / success_count
        print(f"[cli] Average call time: {avg:.1f}s — extrapolated 1K paragraphs ≈ {avg * 1000 / 60:.0f} min")


if __name__ == "__main__":
    main()
