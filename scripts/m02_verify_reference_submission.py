#!/usr/bin/env python3
"""Verification tooling for M02 PR #128 reconstructed reference submission."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
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


def verify_source_ref(expected: str) -> bool:
    try:
        got = subprocess.check_output(["git", "rev-parse", "--verify", expected], text=True).strip()
        return got.startswith(expected)
    except Exception:
        return False


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Verify PR #128 reference reconstruction.")
    p.add_argument("submission_dir", nargs="?", default=EXPECTED["submission_dir"])
    p.add_argument("--source", default=EXPECTED["source_ref"], help="Expected source commit")
    p.add_argument("--archive-sha", default=EXPECTED["archive_sha"], help="Expected archive SHA-256")
    p.add_argument("--member-sha", default=EXPECTED["member_sha"], help="Expected archive member SHA-256")
    p.add_argument("--output", default=".evidence/m02_reference_manifest.json", help="Manifest output")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.submission_dir)
    if not root.exists():
        print(f"missing submission_dir: {root}")
        return 1

    results = {
        "mission": "M02",
        "submission_dir": str(root),
        "source_ref": args.source,
        "source_ref_match": verify_source_ref(args.source),
        "expected_archive_sha": args.archive_sha,
        "expected_member_sha": args.member_sha,
        "files": {},
        "metrics": {},
        "status": "pass",
    }

    if not results["source_ref_match"]:
        results["status"] = "fail"
        print(f"source_ref_missing: {args.source}")

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
