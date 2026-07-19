#!/usr/bin/env python3
"""Minimal durable ledger for M01 progress/experiments."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path


LEDGER_PATH = Path(".evidence/m01_progress_ledger.jsonl")


def run_git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def get_current_commit() -> str:
    return run_git("rev-parse", "HEAD")


def append_entry(event: str, status: str, notes: str) -> None:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mission": "M01",
        "event": event,
        "status": status,
        "branch": run_git("rev-parse", "--abbrev-ref", "HEAD"),
        "commit": get_current_commit(),
        "notes": notes,
    }
    with LEDGER_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"ledger: wrote {LEDGER_PATH}")


def tail_entries(limit: int) -> None:
    if not LEDGER_PATH.exists():
        print(f"ledger: no entries at {LEDGER_PATH}")
        return
    lines = LEDGER_PATH.read_text(encoding="utf-8").splitlines()
    for line in lines[-limit:]:
        print(line)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Track M01 progress in a durable local ledger.")
    sub = parser.add_subparsers(dest="command", required=True)

    add_cmd = sub.add_parser("add", help="Append a ledger entry")
    add_cmd.add_argument("--event", required=True, help="Short event label.")
    add_cmd.add_argument("--status", required=True, help="Status label.")
    add_cmd.add_argument("--notes", default="", help="Optional details.")

    tail_cmd = sub.add_parser("tail", help="Show most recent entries.")
    tail_cmd.add_argument("--n", type=int, default=10, help="Number of entries to show.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "add":
        append_entry(args.event, args.status, args.notes)
    elif args.command == "tail":
        tail_entries(args.n)


if __name__ == "__main__":
    main()
