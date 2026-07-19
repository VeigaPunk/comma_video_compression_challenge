#!/usr/bin/env python3
"""Run the byte-exact official evaluator with separate precision/cardinality proof."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path


OFFICIAL_EVALUATOR_SHA256 = "7da71a84ce24286bc6b583470f9bbd25c998971da301320d0d4e9d6fd40baa4b"
PAIRS = 600
WIDTH = 1164
HEIGHT = 874


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def full_precision_source(official: str) -> str:
    """Change only the four report float formats; scoring statements stay identical."""
    anchors = (".8f", ".8f", ".8f", ".2f")
    if sum(official.count(anchor) for anchor in set(anchors)) != 4:
        raise ValueError("official evaluator format anchors changed")
    precise = official.replace(".8f", ".17g").replace(".2f", ".17g")
    restored = precise.replace(".17g", ".8f", 3).replace(".17g", ".2f", 1)
    if restored != official:
        raise AssertionError("precision transform changed evaluator semantics")
    return precise


def assert_exact_raw(raw: Path, *, pairs: int = PAIRS, width: int = WIDTH, height: int = HEIGHT) -> dict:
    expected_frames = pairs * 2
    expected_bytes = expected_frames * width * height * 3
    actual_bytes = raw.stat().st_size
    if actual_bytes != expected_bytes:
        raise ValueError(f"raw byte cardinality: expected {expected_bytes}, got {actual_bytes}")
    return {
        "bytes": actual_bytes,
        "frames": expected_frames,
        "pairs": pairs,
        "raw_shape": [expected_frames, height, width, 3],
        "sha256": sha256_file(raw),
    }


def count_video_frames(video: Path) -> int:
    import av

    with av.open(video) as container:
        return sum(1 for _ in container.decode(container.streams.video[0]))


def parse_report(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")

    def number(pattern: str) -> float:
        match = re.search(pattern, text)
        if match is None:
            raise ValueError(f"missing report field: {pattern}")
        return float(match.group(1).replace(",", ""))

    return {
        "samples": int(number(r"results over ([0-9,]+) samples")),
        "pose": number(r"Average PoseNet Distortion:\s*([0-9.eE+-]+)"),
        "seg": number(r"Average SegNet Distortion:\s*([0-9.eE+-]+)"),
        "archive_bytes": int(number(r"Submission file size:\s*([0-9,]+) bytes")),
        "uncompressed_bytes": int(number(r"Original uncompressed size:\s*([0-9,]+) bytes")),
        "rate": number(r"Compression Rate:\s*([0-9.eE+-]+)"),
        "final": number(r"Final score:.*=\s*([0-9.eE+-]+)"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submission-dir", type=Path, required=True)
    parser.add_argument("--uncompressed-dir", type=Path, default=Path("videos"))
    parser.add_argument("--video-names-file", type=Path, default=Path("public_test_video_names.txt"))
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--output", type=Path, default=Path(".evidence/m04_evaluator_proof.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    evaluator = root / "evaluate.py"
    evaluator_hash = sha256_file(evaluator)
    if evaluator_hash != OFFICIAL_EVALUATOR_SHA256:
        raise ValueError(f"evaluate.py is not official: {evaluator_hash}")

    names = [line.strip() for line in args.video_names_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(names) != 1:
        raise ValueError(f"expected one official video, got {len(names)}")
    name = Path(names[0])
    raw = args.submission_dir / "inflated" / name.with_suffix(".raw")
    raw_proof = assert_exact_raw(raw)
    gt_frames = count_video_frames(args.uncompressed_dir / name)
    if gt_frames != raw_proof["frames"]:
        raise ValueError(f"loader cardinality mismatch: GT {gt_frames}, inflated {raw_proof['frames']}")

    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="m04-precise-") as temporary:
        precise_evaluator = Path(temporary) / "evaluate_precise.py"
        precise_evaluator.write_text(full_precision_source(evaluator.read_text(encoding="utf-8")), encoding="utf-8")
        precise_report = Path(temporary) / "report.txt"
        command = [
            sys.executable, str(precise_evaluator), "--submission-dir", str(args.submission_dir),
            "--uncompressed-dir", str(args.uncompressed_dir), "--video-names-file", str(args.video_names_file),
            "--device", args.device, "--report", str(precise_report),
        ]
        env = {**os.environ, "PYTHONPATH": str(root) + os.pathsep + os.environ.get("PYTHONPATH", "")}
        process = subprocess.run(command, cwd=root, env=env, text=True, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, timeout=args.timeout_seconds, check=False)
        if process.returncode:
            raise RuntimeError(f"precision evaluation failed ({process.returncode})\n{process.stdout}")
        metrics = parse_report(precise_report)
    if metrics["samples"] != PAIRS:
        raise ValueError(f"official evaluator judged {metrics['samples']} samples, expected {PAIRS}")

    proof = {
        "schema": "m04-official-evaluator-proof-v1",
        "official_evaluator_sha256": evaluator_hash,
        "precision_transform": "four .12f report formats replaced by .17g; executable statements unchanged",
        "metrics": metrics,
        "cardinality": {"ground_truth_frames": gt_frames, "inflated": raw_proof},
        "runtime_seconds": time.monotonic() - started,
        "archive_sha256": sha256_file(args.submission_dir / "archive.zip"),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(proof, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
