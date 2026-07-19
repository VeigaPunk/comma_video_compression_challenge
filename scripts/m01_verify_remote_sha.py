#!/usr/bin/env python3
"""Verify local branch SHA against a remote ref SHA."""

from __future__ import annotations

import argparse
import subprocess
import sys


def run_git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def get_local_sha(ref: str) -> str:
    return run_git("rev-parse", ref)


def get_remote_sha(remote: str, ref: str) -> str:
    result = run_git("ls-remote", remote, ref).splitlines()
    if not result:
        raise RuntimeError(f"remote ref not found: {remote} {ref}")
    return result[0].split()[0]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare local and remote SHAs for a given ref.")
    parser.add_argument("remote", help="remote name (e.g., VeigaPunk)")
    parser.add_argument("ref", help="branch or ref to compare (e.g., mission/M01)")
    parser.add_argument(
        "--expect-local",
        default="HEAD",
        help="local ref to compare against remote ref (default: HEAD)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    local_ref = args.expect_local
    local_sha = get_local_sha(local_ref)
    remote_sha = get_remote_sha(args.remote, args.ref)

    print(f"local({local_ref}): {local_sha}")
    print(f"remote({args.remote} {args.ref}): {remote_sha}")

    if local_sha != remote_sha:
        print("sha mismatch")
        return 1
    print("sha match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
