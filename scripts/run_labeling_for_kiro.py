#!/usr/bin/env python
"""Batch labeling coordinator for Kiro's terminal.

Usage:
    python scripts/run_labeling_for_kiro.py [batch_number]

Examples:
    # Process first 45 paragraphs
    python scripts/run_labeling_for_kiro.py 1

    # Process next 45 (after waiting 5 hours)
    python scripts/run_labeling_for_kiro.py 2

Each batch processes 45 paragraphs with 5-minute pauses between
subprocess calls. This keeps within Claude Pro tier limits (~45 msg/5h).
"""
import argparse
import sys
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Batch labeling coordinator for Kiro"
    )
    parser.add_argument(
        "batch_num",
        type=int,
        nargs="?",
        default=1,
        help="Batch number (1-22, process 45 paragraphs each)",
    )
    args = parser.parse_args()

    if args.batch_num < 1 or args.batch_num > 22:
        print(f"❌ Batch number must be 1-22, got {args.batch_num}")
        return 1

    limit = args.batch_num * 45
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent

    print()
    print("=" * 60)
    print(f"Batch Labeling for Kiro - Batch #{args.batch_num}")
    print("=" * 60)
    print()
    print("Settings:")
    print(f"  • Model: haiku (Kiro's Claude)")
    print(f"  • Batch size: 15 paragraphs/call")
    print(f"  • Pause: 300s (5min) between batches")
    print(f"  • Limit: {limit} paragraphs (batch #{args.batch_num})")
    print(f"  • Resume-safe: Yes ✓")
    print()

    cmd = [
        sys.executable,
        str(script_dir / "batch_label_via_claude_cli.py"),
        "--paragraphs",
        str(repo_root / "data/corpora/smoke-2k/paragraphs-B.jsonl"),
        "--output",
        str(repo_root / "docs/labeler-eval/cli-haiku-B.jsonl"),
        "--model",
        "haiku",
        "--batch-size",
        "15",
        "--batch-pause-seconds",
        "300",
        "--limit",
        str(limit),
    ]

    print(f"Running: {' '.join(cmd[2:])}")
    print()

    result = subprocess.run(cmd, cwd=repo_root)

    print()
    print("=" * 60)
    if result.returncode == 0:
        print(f"✓ SUCCESS! Batch #{args.batch_num} completed.")
        print()
        print("Next steps:")
        print(f"  1. Wait ~5 hours for rate limits to reset")
        print(f"  2. Run: python scripts/run_labeling_for_kiro.py {args.batch_num + 1}")
    else:
        print(f"✗ FAILED! Batch #{args.batch_num} failed (exit code {result.returncode})")
        print()
        print("Check the error messages above.")
    print("=" * 60)
    print()

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
