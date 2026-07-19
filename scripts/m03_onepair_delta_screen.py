#!/usr/bin/env python3
"""Screen one latent mutation exactly, then optionally qualify all 600 samples."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submission-dir", default="submissions/rhnerv_latent_polish")
    parser.add_argument("--video-names-file", default="public_test_video_names.txt")
    parser.add_argument("--uncompressed-dir", default="videos")
    parser.add_argument("--pair", type=int, default=0)
    parser.add_argument("--dim", type=int, default=0)
    parser.add_argument("--step", type=int, default=1)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--qualify-full", action="store_true")
    parser.add_argument("--report", default=".evidence/m03_onepair_delta_screen.jsonl")
    return parser.parse_args()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_submission_modules(submission_dir: Path):
    resolved = str(submission_dir.resolve())
    if resolved not in sys.path:
        sys.path.insert(0, resolved)
    import codec
    import codec_ctx
    import inflate

    return codec, codec_ctx, inflate


def unpack_member(member: bytes) -> tuple[int, bytes, bytes, bytes, tuple[int, int, int]]:
    if len(member) < 7:
        raise ValueError("truncated container")
    version = member[0] >> 4
    decoder_len = int.from_bytes(member[1:4], "little")
    latent_len = int.from_bytes(member[4:7], "little")
    decoder_end = 7 + decoder_len
    latent_end = decoder_end + latent_len
    if latent_end > len(member):
        raise ValueError("invalid section lengths")
    coder_ids = (member[0] & 1, (member[0] >> 1) & 1, (member[0] >> 2) & 1)
    return (
        version,
        member[7:decoder_end],
        member[decoder_end:latent_end],
        member[latent_end:],
        coder_ids,
    )


def mutate_latent_raw(latent_raw: bytes, pair: int, dim: int, step: int, codec) -> tuple[bytes, int, int]:
    import numpy as np

    header_bytes = codec.LATENT_DIM * 4
    header = latent_raw[:header_bytes]
    stored = np.frombuffer(latent_raw[header_bytes:], dtype=np.uint8).copy()
    stored = stored.reshape(codec.LATENT_DIM, codec.N_PAIRS)
    ordered = stored.copy()
    ordered[:, 1:] = (
        np.cumsum(
            ((stored[:, 1:].astype(np.int16) - 128) & 255),
            axis=1,
            dtype=np.uint16,
        ).astype(np.uint8)
        + stored[:, :1]
    )
    codes = np.empty((codec.N_PAIRS, codec.LATENT_DIM), dtype=np.uint8)
    codes[:, codec.LATENT_DIM_ORDER] = ordered.T

    before = int(codes[pair, dim])
    after = before + step
    if not 0 <= after <= 255:
        raise ValueError(f"mutation leaves uint8 range: {before} + {step}")
    codes[pair, dim] = after

    ordered_mutant = codes[:, codec.LATENT_DIM_ORDER].T
    stored_mutant = np.empty_like(stored)
    stored_mutant[:, 0] = ordered_mutant[:, 0]
    stored_mutant[:, 1:] = (
        (ordered_mutant[:, 1:].astype(np.int16) - ordered_mutant[:, :-1].astype(np.int16) + 128)
        & 255
    ).astype(np.uint8)
    return header + stored_mutant.tobytes(), before, after


def build_mutant_member(submission_dir: Path, pair: int, dim: int, step: int) -> tuple[bytes, dict[str, Any]]:
    codec, codec_ctx, _ = load_submission_modules(submission_dir)
    if not 0 <= pair < codec.N_PAIRS:
        raise ValueError("pair out of range")
    if not 0 <= dim < codec.LATENT_DIM:
        raise ValueError("dimension out of range")
    if step == 0:
        raise ValueError("step must be nonzero")

    with zipfile.ZipFile(submission_dir / "archive.zip") as archive:
        if archive.namelist() != ["x"]:
            raise ValueError(f"unexpected archive members: {archive.namelist()}")
        baseline_member = archive.read("x")

    version, decoder, latent, selector, coder_ids = unpack_member(baseline_member)
    if version != 1 or coder_ids[1] != 1:
        raise ValueError(f"unsupported container version/coders: {version}/{coder_ids}")
    latent_raw = codec_ctx.decode_latent_section(latent)
    mutant_raw, before, after = mutate_latent_raw(latent_raw, pair, dim, step, codec)
    mutant_latent = codec_ctx.encode_latent_section(mutant_raw)
    mutant_member = codec_ctx.pack_container(decoder, mutant_latent, selector, coder_ids)
    return mutant_member, {
        "pair": pair,
        "dimension": dim,
        "step": step,
        "code_before": before,
        "code_after": after,
        "baseline_member_sha256": sha256_bytes(baseline_member),
        "mutant_member_sha256": sha256_bytes(mutant_member),
    }


def write_archive(member: bytes, destination: Path) -> None:
    info = zipfile.ZipInfo("x", date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_STORED
    info.external_attr = 0
    info.create_system = 0
    with zipfile.ZipFile(destination, "w") as archive:
        archive.writestr(info, member)


def run_checked(command: list[str], timeout: int, env: dict[str, str] | None = None) -> tuple[str, float]:
    started = time.monotonic()
    process = subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        env=env,
        check=False,
    )
    elapsed = time.monotonic() - started
    if process.returncode:
        raise RuntimeError(f"command failed ({process.returncode}): {' '.join(command)}\n{process.stdout}")
    return process.stdout, elapsed


def inflate(submission: Path, names_file: Path, timeout: int) -> tuple[Path, float]:
    archive_dir = submission / "packed"
    inflated = submission / "inflated"
    archive_dir.mkdir()
    inflated.mkdir()
    with zipfile.ZipFile(submission / "archive.zip") as archive:
        archive.extractall(archive_dir)
    env = {**os.environ, "PACT_PYTHON_BIN": sys.executable}
    _, elapsed = run_checked(
        ["bash", str(submission / "inflate.sh"), str(archive_dir), str(inflated), str(names_file)],
        timeout,
        env,
    )
    return inflated, elapsed


def parse_official_report(path: Path) -> dict[str, float | int]:
    text = path.read_text(encoding="utf-8")

    def number(pattern: str) -> float:
        match = re.search(pattern, text)
        if not match:
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


def official_cpu_eval(
    submission: Path, uncompressed: Path, names_file: Path, report: Path, timeout: int
) -> tuple[dict[str, float | int], float, str]:
    output, elapsed = run_checked(
        [
            sys.executable,
            "evaluate.py",
            "--submission-dir",
            str(submission),
            "--uncompressed-dir",
            str(uncompressed),
            "--video-names-file",
            str(names_file),
            "--device",
            "cpu",
            "--report",
            str(report),
        ],
        timeout,
    )
    return parse_official_report(report), elapsed, output


def load_ground_truth_pair(video: Path, pair: int):
    import av
    import torch
    from frame_utils import yuv420_to_rgb

    wanted = {2 * pair, 2 * pair + 1}
    frames = []
    with av.open(video) as container:
        for index, frame in enumerate(container.decode(container.streams.video[0])):
            if index in wanted:
                frames.append(yuv420_to_rgb(frame))
            if index >= 2 * pair + 1:
                break
    if len(frames) != 2:
        raise ValueError(f"could not decode pair {pair}")
    return torch.stack(frames).unsqueeze(0)


def load_raw_pair(raw: Path, pair: int):
    import numpy as np
    import torch
    from frame_utils import camera_size

    width, height = camera_size
    frame_bytes = width * height * 3
    frame_count = raw.stat().st_size // frame_bytes
    mapped = np.memmap(raw, dtype=np.uint8, mode="r", shape=(frame_count, height, width, 3))
    tensor = torch.from_numpy(mapped[2 * pair : 2 * pair + 2].copy()).unsqueeze(0)
    del mapped
    return tensor, frame_count


def render_member_pair(submission_dir: Path, member: bytes, pair: int):
    """Render only the selected pair through the submission's exact CPU path."""
    import torch
    import torch.nn.functional as functional

    _, _, inflate_module = load_submission_modules(submission_dir)
    decoder_state, latents, selector_codes, selector_specs = inflate_module.parse_member(member)
    decoder = inflate_module.HNeRVDecoder(
        latent_dim=inflate_module.LATENT_DIM,
        base_channels=inflate_module.BASE_CHANNELS,
        eval_size=inflate_module.EVAL_SIZE,
    ).to("cpu")
    decoder.load_state_dict(decoder_state)
    decoder.eval()
    batch_start = (pair // 16) * 16
    batch_end = min(batch_start + 16, inflate_module.N_PAIRS)
    batch_size = batch_end - batch_start
    with torch.inference_mode():
        decoded = decoder(latents[batch_start:batch_end])
        flat = decoded.reshape(batch_size * 2, 3, *inflate_module.EVAL_SIZE)
        up = functional.interpolate(
            flat,
            size=(inflate_module.CAMERA_H, inflate_module.CAMERA_W),
            mode="bicubic",
            align_corners=False,
        ).reshape(batch_size, 2, 3, inflate_module.CAMERA_H, inflate_module.CAMERA_W)
        up[:, 0, 0].sub_(1.0)
        up[:, 0, 2].sub_(1.0)
        up[:, 1, 1].sub_(1.0)
        rounded = up.reshape(
            batch_size * 2, 3, inflate_module.CAMERA_H, inflate_module.CAMERA_W
        ).clamp(0, 255).round()
        selected = inflate_module.apply_compact_selector_to_frames(
            rounded, selector_codes, selector_specs, pair_start=batch_start
        )
        pair_offset = (pair - batch_start) * 2
        return (
            selected[pair_offset : pair_offset + 2]
            .to(torch.uint8)
            .permute(0, 2, 3, 1)
            .unsqueeze(0)
        )


def score_pair(ground_truth, baseline, mutant) -> tuple[dict[str, Any], float]:
    import torch
    from modules import DistortionNet, posenet_sd_path, segnet_sd_path

    started = time.monotonic()
    model = DistortionNet().eval().to(device="cpu")
    model.load_state_dicts(posenet_sd_path, segnet_sd_path, torch.device("cpu"))
    with torch.inference_mode():
        baseline_pose, baseline_seg = model.compute_distortion(ground_truth, baseline)
        mutant_pose, mutant_seg = model.compute_distortion(ground_truth, mutant)
    elapsed = time.monotonic() - started
    result = {
        "input_shape": list(ground_truth.shape),
        "baseline_pose": float(baseline_pose.item()),
        "baseline_seg": float(baseline_seg.item()),
        "mutant_pose": float(mutant_pose.item()),
        "mutant_seg": float(mutant_seg.item()),
        "pose_delta": float(mutant_pose.item() - baseline_pose.item()),
        "seg_delta": float(mutant_seg.item() - baseline_seg.item()),
    }
    return result, elapsed


def exact_prediction(
    baseline: dict[str, float | int], pair: dict[str, Any], mutant_archive_bytes: int
) -> dict[str, float]:
    samples = int(baseline["samples"])
    predicted_pose = float(baseline["pose"]) + pair["pose_delta"] / samples
    predicted_seg = float(baseline["seg"]) + pair["seg_delta"] / samples
    predicted_rate = mutant_archive_bytes / int(baseline["uncompressed_bytes"])
    predicted_final = 100 * predicted_seg + math.sqrt(10 * predicted_pose) + 25 * predicted_rate
    baseline_final = (
        100 * float(baseline["seg"])
        + math.sqrt(10 * float(baseline["pose"]))
        + 25 * float(baseline["rate"])
    )
    return {
        "pose": predicted_pose,
        "seg": predicted_seg,
        "rate": predicted_rate,
        "final": predicted_final,
        "final_delta": predicted_final - baseline_final,
    }


def append_report(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(result, sort_keys=True) + "\n")


def main() -> int:
    args = parse_args()
    started = time.monotonic()
    root = Path.cwd().resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    source_submission = Path(args.submission_dir).resolve()
    names_file = Path(args.video_names_file).resolve()
    uncompressed = Path(args.uncompressed_dir).resolve()
    names = [line.strip() for line in names_file.read_text().splitlines() if line.strip()]
    if len(names) != 1:
        raise ValueError("this 600-pair codec proof requires exactly one official video")

    mutant_member, mutation = build_mutant_member(source_submission, args.pair, args.dim, args.step)
    with zipfile.ZipFile(source_submission / "archive.zip") as archive:
        baseline_member = archive.read("x")

    screen_started = time.monotonic()
    ground_truth_pair = load_ground_truth_pair(uncompressed / names[0], args.pair)
    baseline_pair = render_member_pair(source_submission, baseline_member, args.pair)
    mutant_pair = render_member_pair(source_submission, mutant_member, args.pair)
    pair_metrics, judge_seconds = score_pair(ground_truth_pair, baseline_pair, mutant_pair)
    screen_seconds = time.monotonic() - screen_started
    pair_metrics["render_and_judge_seconds"] = screen_seconds
    pair_metrics["judge_seconds"] = judge_seconds

    artifacts = root / ".artifacts"
    artifacts.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="m03-screen-", dir=artifacts) as temporary:
        workspace = Path(temporary)
        baseline_submission = workspace / "baseline"
        mutant_submission = workspace / "mutant"
        shutil.copytree(source_submission, baseline_submission, ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(source_submission, mutant_submission, ignore=shutil.ignore_patterns("__pycache__"))
        write_archive(mutant_member, mutant_submission / "archive.zip")
        baseline_metrics = parse_official_report(source_submission / "report_cpu.txt")
        if baseline_metrics["samples"] != 600:
            raise ValueError(f"baseline sample count is {baseline_metrics['samples']}, not 600")
        prediction = exact_prediction(
            baseline_metrics, pair_metrics, (mutant_submission / "archive.zip").stat().st_size
        )
        result = {
            "schema": "m03-onepair-screen-proof-v2",
            "mode": "full_qualification" if args.qualify_full else "screen_only",
            "mutation": mutation,
            "baseline": baseline_metrics,
            "predicted_mutant": prediction,
            "screen": pair_metrics,
            "hashes": {
                "baseline_archive_sha256": sha256_file(baseline_submission / "archive.zip"),
                "mutant_archive_sha256": sha256_file(mutant_submission / "archive.zip"),
            },
            "runtime_seconds": {
                "one_pair_screen": screen_seconds,
                "total": time.monotonic() - started,
            },
        }

        if args.qualify_full:
            import torch

            baseline_inflated, baseline_inflate_seconds = inflate(
                baseline_submission, names_file, args.timeout_seconds
            )
            mutant_inflated, mutant_inflate_seconds = inflate(
                mutant_submission, names_file, args.timeout_seconds
            )
            baseline_metrics, baseline_eval_seconds, _ = official_cpu_eval(
                baseline_submission,
                uncompressed,
                names_file,
                workspace / "baseline-report.txt",
                args.timeout_seconds,
            )
            mutant_metrics, mutant_eval_seconds, _ = official_cpu_eval(
                mutant_submission,
                uncompressed,
                names_file,
                workspace / "mutant-report.txt",
                args.timeout_seconds,
            )
            if baseline_metrics["samples"] != 600 or mutant_metrics["samples"] != 600:
                raise ValueError("full qualification did not score exactly 600 samples")

            baseline_raw = baseline_inflated / Path(names[0]).with_suffix(".raw")
            mutant_raw = mutant_inflated / Path(names[0]).with_suffix(".raw")
            baseline_raw_pair, baseline_frames = load_raw_pair(baseline_raw, args.pair)
            mutant_raw_pair, mutant_frames = load_raw_pair(mutant_raw, args.pair)
            render_matches_full = {
                "baseline": bool(torch.equal(baseline_pair, baseline_raw_pair)),
                "mutant": bool(torch.equal(mutant_pair, mutant_raw_pair)),
            }
            if not all(render_matches_full.values()):
                raise ValueError(f"one-pair render differs from full inflate: {render_matches_full}")

            prediction = exact_prediction(
                baseline_metrics, pair_metrics, (mutant_submission / "archive.zip").stat().st_size
            )
            result.update(
                {
                    "baseline": baseline_metrics,
                    "predicted_mutant": prediction,
                    "measured_mutant": mutant_metrics,
                    "measured_final_delta": float(mutant_metrics["final"])
                    - float(baseline_metrics["final"]),
                    "prediction_error": prediction["final"] - float(mutant_metrics["final"]),
                    "render_matches_full_inflate": render_matches_full,
                    "output": {
                        "baseline_frames": baseline_frames,
                        "mutant_frames": mutant_frames,
                        "samples": int(mutant_metrics["samples"]),
                        "raw_shape": [mutant_frames, 874, 1164, 3],
                    },
                }
            )
            result["hashes"].update(
                {
                    "baseline_raw_sha256": sha256_file(baseline_raw),
                    "mutant_raw_sha256": sha256_file(mutant_raw),
                }
            )
            result["runtime_seconds"].update(
                {
                    "baseline_inflate": baseline_inflate_seconds,
                    "mutant_inflate": mutant_inflate_seconds,
                    "baseline_full_cpu": baseline_eval_seconds,
                    "mutant_full_cpu": mutant_eval_seconds,
                    "total": time.monotonic() - started,
                }
            )

        append_report(Path(args.report), result)
        print(json.dumps(result, indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
