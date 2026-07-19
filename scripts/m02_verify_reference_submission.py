#!/usr/bin/env python3
"""Verification tooling for M02 PR #128 reconstructed reference submission."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


EXPECTED = {
    "mission": "M02",
    "source_ref": "5a6cdcbdbabcef8b7c5682c861e5689783d4587c",
    "submission_dir": "submissions/rhnerv_latent_polish",
    "archive_sha": "6d11284b051540be190b2613e615edad4efec7fddbfc627000d0d5fd0bd3f859",
    "member_sha": "2687049683aae7848bc9d0a23feb8809efe7875d8cf0ba34e58f41ab538f7827",
    "expected_metrics": {
        "pose": 2.937e-05,
        "seg": 5.3263e-04,
        "rate": 4.70179e-03,
        "final": 0.187946,
    },
    "required_files": [
        "README.md",
        "LICENSE",
        "METHOD.md",
        "THIRD_PARTY_NOTICES.md",
        "archive.zip",
        "compress.py",
        "compress.sh",
        "inflate.py",
        "inflate.sh",
        "codec.py",
        "codec_ctx.py",
        "frame_selector.py",
        "model.py",
        "expected_output.sha256",
        "report_cpu.txt",
        "encoder/decoder_streams.bin",
        "encoder/selector_payload.bin",
        "encoder/polished_latent_raw.bin",
    ],
    "runtime": {
        "python": "3.11.15",
        "uv": "0.11.29",
        "git_lfs": "git-lfs/3.7.1",
        "ffmpeg": "n8.1.2",
    },
    "lfs_oids": {
        "models/posenet.safetensors": "0f3a0874c5c387f990d7b88bd1d7e1f6de35d98b45f2a289989db2c77b9b6576",
        "models/segnet.safetensors": "68956e328d4c5d875389a1a444870e6bac1c052c9986123827af95c07c6991b6",
        "submissions/rhnerv_latent_polish/encoder/decoder_streams.bin": "83598024bdb4d60463610db23934cdee60c3b6a81158a97e0dd55ea621833fcd",
        "submissions/rhnerv_latent_polish/encoder/polished_latent_raw.bin": "af58e8ace2815288570dd295bb4f7858fb2ac3aa47f81029b9c7b2673984bf22",
        "submissions/rhnerv_latent_polish/encoder/selector_payload.bin": "fc5c431b5d793c33e2f320076fe6f0dd76c2d91e3826ae4b05abfb4f86f453ca",
        "videos/0.mkv": "2611f5f3e186f3529777749f97bd4cce3a208d6b3559e137bd45d256980d2fa9",
    },
}


def parse_metric(path: Path, label: str) -> float | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="ignore")
    if label == "Final score":
        match = re.search(rf"{re.escape(label)}[^=]*=\s*([0-9.]+)", text)
    else:
        match = re.search(rf"{re.escape(label)}:\s*([0-9.]+)", text)
    return float(match.group(1)) if match else None


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def member_sha(archive: Path) -> str:
    with zipfile.ZipFile(archive) as zf:
        names = zf.namelist()
        if not names:
            raise RuntimeError("archive has no members")
        if "x" not in names:
            raise RuntimeError("expected single member 'x' not found")
        data = zf.read("x")
    return hashlib.sha256(data).hexdigest()


def run_cmd(*args: str) -> str:
    return subprocess.check_output(args, text=True, stderr=subprocess.PIPE).strip()


def verify_source_ref(expected: str) -> tuple[bool, str]:
    if re.fullmatch(r"[0-9a-fA-F]{40}", expected) is None:
        return False, "invalid_sha"
    try:
        kind = run_cmd("git", "cat-file", "-t", expected)
    except Exception:
        return False, ""
    if kind != "commit":
        return False, kind
    try:
        run_cmd("git", "cat-file", "-e", f"{expected}^{{commit}}")
        return True, kind
    except Exception:
        return False, kind


def verify_lfs_oids(expected: dict[str, str]) -> tuple[bool, dict[str, str]]:
    """Bind tracked LFS paths to their committed object identities."""
    try:
        output = run_cmd("git", "lfs", "ls-files", "--long")
    except Exception:
        return False, {}

    observed: dict[str, str] = {}
    for line in output.splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})\s+[-*]\s+(.+)", line)
        if match:
            observed[match.group(2)] = match.group(1)

    selected = {path: observed.get(path, "") for path in expected}
    return selected == expected, selected


def verify_runtime(expected: dict[str, str]) -> tuple[bool, dict[str, str | None]]:
    observed: dict[str, str | None] = {}

    def pick(cmd: list[str], pattern: str) -> str | None:
        try:
            text = run_cmd(*cmd)
            m = re.search(pattern, text)
            return m.group(1) if m else None
        except Exception:
            return None

    observed["python"] = re.match(r"([0-9]+\.[0-9]+\.[0-9]+)", sys.version).group(1)
    observed["uv"] = pick(["uv", "--version"], r"uv\s+([0-9]+\.[0-9]+\.[0-9]+)")
    observed["git_lfs"] = pick(
        ["git", "lfs", "version"], r"(git-lfs/[0-9]+\.[0-9]+\.[0-9]+)"
    )
    observed["ffmpeg"] = pick(["ffmpeg", "-version"], r"ffmpeg version\s+([a-zA-Z0-9._-]+)")

    ok = True
    for key, expected_value in expected.items():
        got = observed.get(key)
        if got != expected_value:
            ok = False
            print(f"runtime_mismatch {key} expected={expected_value} actual={got}")

    if not shutil.which("git"):
        print("runtime_mismatch git command missing")
        ok = False

    return ok, observed


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Verify PR #128 reference reconstruction.")
    p.add_argument("submission_dir", nargs="?", default=EXPECTED["submission_dir"])
    p.add_argument("--source", default=EXPECTED["source_ref"], help="Expected source commit")
    p.add_argument("--archive-sha", default=EXPECTED["archive_sha"], help="Expected archive SHA-256")
    p.add_argument("--member-sha", default=EXPECTED["member_sha"], help="Expected archive member SHA-256")
    p.add_argument("--output", default=".evidence/m02_reference_manifest.json", help="Manifest output")
    p.add_argument(
        "--require-runtime",
        action="store_true",
        help="Require runtime identity checks against pinned versions.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.submission_dir)
    if not root.exists():
        print(f"missing submission_dir: {root}")
        return 1

    source_ok, source_type = verify_source_ref(args.source)
    lfs_ok, lfs_observed = verify_lfs_oids(EXPECTED["lfs_oids"])

    results = {
        "mission": "M02",
        "submission_dir": str(root),
        "source_ref": args.source,
        "source_ref_type": source_type,
        "source_ref_match": source_ok,
        "source_verification": "full_sha_git_cat_file_commit_type",
        "expected_archive_sha": args.archive_sha,
        "expected_member_sha": args.member_sha,
        "files": {},
        "metrics": {},
        "runtime": {
            "pinned": EXPECTED["runtime"],
            "observed": {},
            "match": True,
        },
        "lfs": {
            "pinned": EXPECTED["lfs_oids"],
            "observed": lfs_observed,
            "match": lfs_ok,
        },
        "status": "pass",
    }

    if not source_ok:
        results["status"] = "fail"
        print(f"source_ref_invalid: {args.source} type={source_type}")

    if not lfs_ok:
        results["status"] = "fail"
        print("lfs_oid_mismatch")

    missing = []
    for rel in EXPECTED["required_files"]:
        exists = (root / rel).exists()
        results["files"][rel] = bool(exists)
        if not exists:
            missing.append(rel)

    if missing:
        results["status"] = "fail"
        print("missing_required_files", ",".join(missing))

    archive = root / "archive.zip"
    if archive.exists():
        try:
            results["archive_sha"] = sha256(archive)
            results["member_sha"] = member_sha(archive)
            if results["archive_sha"] != args.archive_sha:
                results["status"] = "fail"
                print(f"archive_sha_mismatch expected={args.archive_sha} actual={results['archive_sha']}")
            if results["member_sha"] != args.member_sha:
                results["status"] = "fail"
                print(f"member_sha_mismatch expected={args.member_sha} actual={results['member_sha']}")
        except Exception as exc:
            results["status"] = "fail"
            print(f"archive_invalid: {exc}")
    else:
        results["status"] = "fail"

    if args.require_runtime:
        runtime_ok, runtime_observed = verify_runtime(EXPECTED["runtime"])
        results["runtime"]["observed"] = runtime_observed
        results["runtime"]["match"] = runtime_ok
        if not runtime_ok:
            results["status"] = "fail"

    report_cpu = root / "report_cpu.txt"
    pose = parse_metric(report_cpu, "Average PoseNet Distortion")
    seg = parse_metric(report_cpu, "Average SegNet Distortion")
    rate = parse_metric(report_cpu, "Compression Rate")
    calculated_final = (
        100 * seg + math.sqrt(10 * pose) + 25 * rate
        if pose is not None and seg is not None and rate is not None
        else None
    )
    results["metrics"] = {
        "pose": pose,
        "seg": seg,
        "rate": rate,
        "reported_final_rounded": parse_metric(report_cpu, "Final score"),
        "calculated_final": calculated_final,
        "pose_expected": EXPECTED["expected_metrics"]["pose"],
        "seg_expected": EXPECTED["expected_metrics"]["seg"],
        "rate_expected": EXPECTED["expected_metrics"]["rate"],
        "final_expected": EXPECTED["expected_metrics"]["final"],
    }
    metric_tolerances = {"pose": 1e-12, "seg": 1e-12, "rate": 1e-12}
    for name, tolerance in metric_tolerances.items():
        actual = results["metrics"][name]
        expected = EXPECTED["expected_metrics"][name]
        if actual is None or not math.isclose(actual, expected, rel_tol=0, abs_tol=tolerance):
            results["status"] = "fail"
            print(f"metric_mismatch {name} expected={expected} actual={actual}")
    if calculated_final is None or not math.isclose(
        calculated_final, EXPECTED["expected_metrics"]["final"], rel_tol=0, abs_tol=1e-6
    ):
        results["status"] = "fail"
        print(
            "metric_mismatch final "
            f"expected={EXPECTED['expected_metrics']['final']} actual={calculated_final}"
        )

    manifest = Path(args.output)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"manifest: {manifest}")

    return 0 if results["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
