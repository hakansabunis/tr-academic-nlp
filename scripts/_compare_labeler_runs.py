"""Render a side-by-side comparison from any number of labeler-eval JSON files.

Usage:
    python scripts/_compare_labeler_runs.py \
        docs/labeler-eval/labeler-eval-gemini.json \
        docs/labeler-eval/labeler-eval-claude-opus-chat.json
"""
from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _spans_summary(spans: list[dict]) -> str:
    if not spans:
        return "(none)"
    return "; ".join(
        f"{s['entity']}={s['text']!r}" for s in spans
    )


def main() -> None:
    paths = [Path(p) for p in sys.argv[1:]]
    if not paths:
        print("usage: _compare_labeler_runs.py file1.json file2.json [...]")
        sys.exit(1)

    runs = [(p, _load(p)) for p in paths]
    providers = [d["provider"] for _, d in runs]

    out_path = ROOT / "docs" / "labeler-eval" / "comparison.md"
    lines: list[str] = ["# Labeler Comparison", ""]
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    lines.append("")
    lines.append("Inputs:")
    for path, data in runs:
        stats = data["stats"]
        lines.append(
            f"- `{path.name}` — provider `{data['provider']}`, "
            f"{stats['successful_calls']}/{stats['calls']} ok, "
            f"${stats['cost_usd']:.4f} total"
        )
    lines.append("")

    # Headline stats table
    lines.append("## Headline stats")
    lines.append("")
    headers = ["provider", "ok/total", "entities found", "cost_usd"]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join(["---"] * len(headers)) + "|")
    for path, data in runs:
        stats = data["stats"]
        ent_total = sum(data.get("entity_counts", {}).values())
        lines.append(
            f"| {data['provider']} | "
            f"{stats['successful_calls']}/{stats['calls']} | "
            f"{ent_total} | "
            f"${stats['cost_usd']:.4f} |"
        )
    lines.append("")

    # Entity distribution side-by-side
    lines.append("## Entity counts (per provider)")
    lines.append("")
    all_entities = sorted({
        e
        for _, data in runs
        for e in data.get("entity_counts", {})
    })
    lines.append("| entity | " + " | ".join(providers) + " |")
    lines.append("|---|" + "|".join(["---"] * len(runs)) + "|")
    for entity in all_entities:
        row = [entity]
        for _, data in runs:
            row.append(str(data.get("entity_counts", {}).get(entity, 0)))
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")

    # Per-paragraph side by side
    lines.append("## Per-paragraph entities")
    lines.append("")
    paragraphs_by_id: dict[str, dict[str, dict]] = defaultdict(dict)
    paragraph_text: dict[str, str] = {}
    for _, data in runs:
        for row in data["paragraphs"]:
            paragraphs_by_id[row["paragraph_id"]][data["provider"]] = row
            paragraph_text[row["paragraph_id"]] = row["text"]

    for paragraph_id in sorted(paragraphs_by_id):
        lines.append(f"### {paragraph_id}")
        lines.append("")
        lines.append("> " + paragraph_text[paragraph_id])
        lines.append("")
        for provider in providers:
            row = paragraphs_by_id[paragraph_id].get(provider)
            if row is None:
                lines.append(f"**{provider}**: (no data)")
                lines.append("")
                continue
            if not row["succeeded"]:
                err = (row.get("error") or "")[:120]
                lines.append(f"**{provider}**: FAILED — {err}")
                lines.append("")
                continue
            lines.append(f"**{provider}** ({len(row['spans'])} entities):")
            if not row["spans"]:
                lines.append("- (no entities)")
            else:
                for span in row["spans"]:
                    lines.append(
                        f"- `{span['entity']}` \"{span['text']}\" "
                        f"({span['start']}-{span['end']})"
                    )
            lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
