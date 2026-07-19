#!/usr/bin/env python3
"""Reversible one-pair delta screen helper for M03.

This script generates exact one-pair latent candidate payloads, runs official-style
CPU evaluation, and emits logged deltas for each candidate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run one-pair exact delta screen candidates.")
    p.add_argument(
        "--submission-dir",
        default="submissions/rhnerv_latent_polish",
        help="Submission directory containing baseline archive and inflate stack.",
    )
    p.add_argument(
        "--pair-start", type=int, default=0, help="First pair index to screen (inclusive)."
    )
    p.add_argument(
        "--pair-end", type=int, default=1, help="Exclusive pair index bound for screening."
    )
    p.add_argument(
        "--dims", type=str, default="0,1,2",
        help="Comma-separated latent dimensions to mutate (e.g., 0,1,2).",
    )
    p.add_argument(
        "--steps",
        type=str,
        default="-2,-1,1,2",
        help="Comma-separated code steps (signed ints), e.g. -1,1",
    )
    p.add_argument(
        "--video-names-file",
        default="public_test_video_names.txt",
        help="Video list file (official format).",
    )
    p.add_argument(
        "--uncompressed-dir",
        default="videos",
        help="Uncompressed video directory used by evaluate.py",
    )
    p.add_argument(
        "--timeout-seconds",
        type=int,
        default=1800,
        help="Per-candidate runtime budget in seconds.",
    )
    p.add_argument(
        "--report",
        default=".evidence/m03_onepair_delta_screen.jsonl",
        help="JSONL path for candidate logs. Exact score deltas are appended.",
    )
    p.add_argument(
        "--run-cpu-eval",
        action="store_true",
        help="Run full official-format CPU evaluation per candidate.",
    )
    p.add_argument(
        "--skip-baseline",
        action="store_true",
        help="Skip baseline score detection; candidate deltas logged as raw.",
    )
    return p.parse_args()


@dataclass
class Candidate:
    pair: int
    dim: int
    step: int


def ensure_runtime_env() -> None:
    if not shutil.which("python") and not shutil.which("python3"):
        raise RuntimeError("python interpreter missing")
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg missing")


def ensure_runtime_deps() -> None:
    from importlib.util import find_spec

    missing = []
    for name in ("numpy", "torch"):
        if find_spec(name) is None:
            missing.append(name)
    if missing:
        raise RuntimeError(f"missing python deps: {', '.join(missing)}")


def module_path(submission_dir: Path) -> Path:
    return submission_dir.resolve()


def parse_int_csv(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def load_submission_modules(submission_dir: Path):
    path = module_path(submission_dir)
    if not path.exists():
        raise FileNotFoundError(f"submission dir not found: {path}")
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
    import codec
    import codec_ctx

    return codec, codec_ctx


def parse_metric(path: Path, label: str) -> float:
    if not path.exists():
        raise FileNotFoundError(f"missing report: {path}")
    text = path.read_text(encoding="utf-8", errors="ignore")
    import re

    if label == "Final":
        m = re.search(r"Final score:.*?=\s*([0-9.]+)", text)
    else:
        m = re.search(rf"{re.escape(label)}:\\s*([0-9.]+)", text)
    if not m:
        raise ValueError(f"missing metric {label}")
    return float(m.group(1))


def archive_member_parts(member_bytes: bytes) -> tuple[int, bytes, bytes, bytes, int, int]:
    ld = int.from_bytes(member_bytes[1:4], "little")
    ll = int.from_bytes(member_bytes[4:7], "little")
    dec_sec = member_bytes[7 : 7 + ld]
    lat_sec = member_bytes[7 + ld : 7 + ld + ll]
    sel_sec = member_bytes[7 + ld + ll :]
    ids = (
        member_bytes[0] & 1,
        (member_bytes[0] >> 1) & 1,
        (member_bytes[0] >> 2) & 1,
    )
    version = member_bytes[0] >> 4
    return version, dec_sec, lat_sec, sel_sec, ids[1], ld + ll + len(sel_sec)


def mutate_latent_raw(latent_raw: bytes, pair: int, dim: int, step: int, *, codec) -> bytes:
    import numpy as np

    hdr16 = latent_raw[:codec.LATENT_HDR]
    stored = np.frombuffer(latent_raw[codec.LATENT_HDR :], dtype=np.uint8).copy()
    stored = stored.reshape(codec.LATENT_DIM, codec.N_PAIRS)

    diffs = ((stored[:, 1:].astype(np.int16) - 128) & 255)
    diffs = np.where(diffs >= 128, diffs - 256, diffs).astype(np.int16)
    ordered = np.empty_like(stored, dtype=np.int16)
    ordered[:, 0] = stored[:, 0]
    ordered[:, 1:] = (np.cumsum(diffs, axis=1) + ordered[:, 0:1]) % 256

    q = np.zeros((codec.N_PAIRS, codec.LATENT_DIM), dtype=np.int16)
    q[:, codec.LATENT_DIM_ORDER] = ordered.T
    v = int(q[pair, dim]) + step
    v = np.clip(v, 0, 255)
    q[pair, dim] = v

    ordered2 = q[:, codec.LATENT_DIM_ORDER].T.astype(np.int16)
    stored2 = np.empty_like(stored)
    stored2[:, 0] = ordered2[:, 0] & 255
    d = (ordered2[:, 1:] - ordered2[:, :-1]).astype(np.int16)
    stored2[:, 1:] = ((d + 128) & 255).astype(np.uint8)
    return hdr16 + stored2.tobytes()


def build_mutant_archive(submission_dir: Path, candidate: Candidate) -> bytes:
    codec, codec_ctx = load_submission_modules(submission_dir)
    archive_path = submission_dir / "archive.zip"
    with __import__("zipfile").ZipFile(archive_path, "r") as zf:
        members = zf.namelist()
        if members != ["x"]:
            raise RuntimeError(f"unexpected archive members: {members}")
        member = zf.read("x")

    version, dec_sec, lat_sec, sel_sec, latent_flag, _ = archive_member_parts(member)
    if version != 1:
        raise RuntimeError(f"unexpected container version: {version}")
    if latent_flag != 1:
        raise RuntimeError(f"latent coder is not ctx-coded: flag={latent_flag}")

    latent_raw = codec_ctx.decode_latent_section(lat_sec)
    mutated_raw = mutate_latent_raw(latent_raw, candidate.pair, candidate.dim, candidate.step, codec=codec)
    if mutated_raw == latent_raw:
        return member
    mutant_lat_sec = codec_ctx.encode_latent_section(mutated_raw)
    selector_sec = sel_sec
    mutant_member = codec_ctx.pack_container(dec_sec, mutant_lat_sec, selector_sec, (1, 1, 1))
    return mutant_member


def write_archive(member: bytes, dst: Path) -> None:
    info = __import__("zipfile").ZipInfo("x", date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = __import__("zipfile").ZIP_STORED
    info.external_attr = 0
    info.create_system = 0
    with __import__("zipfile").ZipFile(dst, "w") as z:
        z.writestr(info, member)


def run_cmd(cmd: list[str], *, timeout: int | None = None) -> tuple[int, str, str]:
    proc = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
        env={**__import__("os").environ},
    )
    return proc.returncode, proc.stdout, proc.stderr


def score_candidate(submission_dir: Path, tmp_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    if not args.run_cpu_eval:
        return {"status": "skipped", "score": None}

    archive_dir = tmp_root / "archive"
    inflated = tmp_root / "inflated"
    archive_dir.mkdir()
    inflated.mkdir()

    with __import__("zipfile").ZipFile(submission_dir / "archive.zip", "r") as z:
        z.extractall(archive_dir)

    cmd_inflate = [
        "bash",
        str(submission_dir / "inflate.sh"),
        str(archive_dir),
        str(inflated),
        str(args.video_names_file),
    ]
    rc, out, err = run_cmd(cmd_inflate, timeout=max(30, min(args.timeout_seconds, 1200)))
    if rc != 0:
        return {
            "status": "inflate_fail",
            "stdout": out,
            "stderr": err,
        }

    report = tmp_root / "report.txt"
    cmd_eval = [
        sys.executable,
        "evaluate.py",
        "--submission-dir",
        str(submission_dir),
        "--uncompressed-dir",
        str(args.uncompressed_dir),
        "--video-names-file",
        str(args.video_names_file),
        "--device",
        "cpu",
        "--report",
        str(report),
    ]
    rc, out2, err2 = run_cmd(cmd_eval, timeout=max(60, args.timeout_seconds - 60))
    if rc != 0:
        return {
            "status": "evaluate_fail",
            "stdout": out + "\n" + out2,
            "stderr": err + "\n" + err2,
        }

    final = parse_metric(report, "Final")
    pose = parse_metric(report, "Average PoseNet Distortion")
    seg = parse_metric(report, "Average SegNet Distortion")

    return {
        "status": "ok",
        "final": final,
        "pose": pose,
        "seg": seg,
        "stdout": out + "\n" + out2,
        "stderr": err + "\n" + err2,
    }


def baseline_score(submission_dir: Path) -> dict[str, float] | None:
    baseline_report = submission_dir / "report_cpu.txt"
    if not baseline_report.exists():
        return None
    return {
        "final": parse_metric(baseline_report, "Final"),
        "pose": parse_metric(baseline_report, "Average PoseNet Distortion"),
        "seg": parse_metric(baseline_report, "Average SegNet Distortion"),
        "rate": parse_metric(submission_dir / "report_cpu.txt", "Compression Rate"),
    }


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def emit_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    args = parse_args()
    ensure_runtime_env()
    ensure_runtime_deps()

    submission = Path(args.submission_dir).resolve()
    dims = parse_int_csv(args.dims)
    steps = parse_int_csv(args.steps)

    if not dims:
        raise ValueError("--dims empty")
    if not steps:
        raise ValueError("--steps empty")

    codec, _ = load_submission_modules(submission)
    if not (0 <= args.pair_start < codec.N_PAIRS):
        raise ValueError("pair-start out of range")
    if not (0 < args.pair_end <= codec.N_PAIRS):
        raise ValueError("pair-end out of range")

    baseline = baseline_score(submission) if not args.skip_baseline else None

    candidates = [
        Candidate(pair=p, dim=d, step=s)
        for p in range(args.pair_start, args.pair_end)
        for d in dims
        for s in steps
    ]

    out_path = Path(args.report)
    logged: list[dict[str, Any]] = []

    for cand in candidates:
        if not (0 <= cand.pair < codec.N_PAIRS):
            continue
        if not (0 <= cand.dim < codec.LATENT_DIM):
            continue

        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td)
            tmp_submission = tmp_root / "submission"
            shutil.copytree(submission, tmp_submission, dirs_exist_ok=False)
            mutant_member = build_mutant_archive(submission, cand)
            write_archive(mutant_member, tmp_submission / "archive.zip")

            eval_result = score_candidate(tmp_submission, tmp_root, args)
            log: dict[str, Any] = {
                "pair": cand.pair,
                "dim": cand.dim,
                "step": cand.step,
                "archive_sha": file_sha(tmp_submission / "archive.zip"),
            }
            log.update(eval_result)

            if baseline and "final" in eval_result:
                log["final_delta"] = eval_result["final"] - baseline["final"]
                log["pose_delta"] = eval_result["pose"] - baseline["pose"]
                log["seg_delta"] = eval_result["seg"] - baseline["seg"]
                log["baseline_final"] = baseline["final"]

            logged.append(log)

    emit_jsonl(out_path, logged)
    print(f"wrote {len(logged)} candidate rows to {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
