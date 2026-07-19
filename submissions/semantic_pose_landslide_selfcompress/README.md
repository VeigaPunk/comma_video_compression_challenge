# Semantic Pose Landslide Self-Compressed

This is the clean submission stage for the self-compressed integer-HPAC
candidate. The canonical CPR1 `archive.zip` is `191,052` bytes with SHA-256:

```text
0491d5df84fc70b62b3f7ccf8894f5e1b81c616de46a052e4423fc1e18fdc7cd
```

[Download the canonical archive](https://github.com/fesalfayed/comma_video_compression_challenge/releases/download/semantic-pose-landslide-selfcompress-cpr1/archive.zip).
The complete approach and experiment history are covered in the
[technical write-up](https://fesalfayed.com/blog/semantic-pose-compression/).

Do not replace the published `archive.zip` with a rebuild unless the result is
byte-identical to the size and SHA-256 above. Any different archive is a new
and unverified candidate.

## Lossless Repack Result

CPR1 reduces the frozen `194,380`-byte archive by `3,328` bytes without
changing the decoded semantic renderer, pose basis, pose coefficients, HPAC
model, or semantic-token stream. The new exact compression rate is
`0.005088547388475883`.

Applying that rate to the displayed metrics from the frozen archive's two
completed official CUDA validations gives:

| Source validator | PoseNet | SegNet | CPR1 score from displayed metrics |
| --- | ---: | ---: | ---: |
| RTX 2000 Ada | 0.00001967 | 0.00028609 | approximately 0.169847662 |
| RTX A4500 (Ampere) | 0.00001981 | 0.00029607 | approximately 0.170895485 |

The conservative A4500 projection is about `0.007653215` below the
`0.178548700` landslide threshold. Because the official report rounds
distortions to eight decimal places, that projected score lies approximately in
`[0.170893209, 0.170897761]`. These are projections from already displayed
metrics, not a claim of hidden evaluator precision or a replacement for the
pending official T4 result.

## Exact Equivalence

`repack_carrier.py` accepts only the frozen source archive with SHA-256
`f4457de09a6e69c8cd29e886a84705462a8c77dc6978020b11dff52e661a1451`.
It decodes the legacy carrier, encodes CPR1, decodes CPR1 again, and requires
exact equality of every stored symbol before writing a deterministic ZIP.

The golden integration test then loads the old and new archives through the
submission decoder and requires `torch.equal` for every semantic state tensor,
the complete pose basis, and all `7,200` pose coefficients. The HPAC model and
token bitstream remain byte-identical. Fourteen codec, malformed-stream, and
frozen-golden test cases pass, including 200 deterministic randomized carrier
round trips. The locked decoded hashes are:

| Artifact | SHA-256 |
| --- | --- |
| Semantic state | `de0e5fc616b75eb0bdb55528aa61a7405eebbd3a81064f513adfbb69b33105ba` |
| Pose basis tensor | `7a6576e991a068e084ffc12f6377b9bfcc00fd2529eb8df27c424921f3c3933b` |
| Pose coefficient tensor | `dee2587ec99eea45e76ebd68eaaad3e3ae52d51e0a9b673103be8d4128e07ca8` |
| HPAC packed model | `b07fff73fac41c5fec2d8acbfd7c43c518852696f18d95cf7465fc6ed7510b58` |
| Semantic token stream | `948379872ff81a4e5d948ec301c143be00ebd0033544c8abdfb4af0f4c4a15eb` |

The CPR1 archive also completed a full CPU entropy replay: all `600` frames
decoded in `2,197.6` seconds, and the resulting `600 x 384 x 512` token tensor
matched SHA-256
`c5c7671d037b6912980c57929a5b6d789d250ee6a93e3b0a6018cf9f63e32ece`.

## Compression Reproduction

`compress.sh` and `repack_carrier.py` are the exact final lossless compression
stage used for CPR1. The script accepts the frozen `194,380`-byte predecessor
archive, or downloads it from the pinned release asset, and requires SHA-256
`f4457de09a6e69c8cd29e886a84705462a8c77dc6978020b11dff52e661a1451`.
It then encodes the canonical Huffman and Rice streams, verifies every decoded
symbol, writes a deterministic ZIP, and refuses success unless the result is
exactly `191,052` bytes with the published CPR1 SHA-256.

```bash
bash submissions/semantic_pose_landslide_selfcompress/compress.sh \
  --output /tmp/semantic-pose-cpr1/archive.zip \
  --report /tmp/semantic-pose-cpr1/repack.json
```

This is the exact frozen-source CPR1 compression/repacking stage, not the
multi-day model-fitting pipeline from the original video. The predecessor is a
compression-side provenance input. It is never loaded during inflation and
does not bypass the charged payload.

## Portability Evidence

The source archive's two validations used:

- challenge commit `d3f688f84f555c5aaebee7d2c4203efc8a9051e2`;
- freshly pulled official PoseNet, SegNet, video, and video-name LFS objects;
- `torch 2.9.0+cu128`, CUDA 12.8, `constriction 0.4.2`, and NumPy 2.3.4;
- the official command:

```bash
uv run --group cu128 bash evaluate.sh \
  --device cuda \
  --submission-dir ./submissions/semantic_pose_landslide_selfcompress
```

The independent A4500 run used driver `550.90.07`, decoded all 600
arithmetic-coded token frames, rendered all 1,200 camera frames, scored all 600
pairs, and exited zero in 3 minutes 42 seconds. Its inflated output was
`3,662,409,600` bytes with SHA-256:

```text
60ead43617ef8fcfa692074d9fc9021947dbd7e47e1ad7654b7239df493d9af2
```

The Ada output hash was
`8b5e62294db79ec3b7fb19d8805bf6af3184d37ddf15ae5ed2d1b9f0cbdc448b`.
The renderer uses GPU floating-point kernels, so raw output and metric
bit-identity are not claimed across GPU architectures. The entropy portability
gate is that the exact bitstream decodes all 600 frames and the complete
official evaluator succeeds.

As a stricter entropy-only check, the preserved source decoder recomputed every
quantized probability table on the A4500. Its full logit SHA-256 exactly matched
the encoder's recorded value:

```text
33fd711b305efb12ab9f7363c1404229996b79b8e27896f20ed910e98f105f75
```

The decoded raw semantic-token tensor has SHA-256
`c5c7671d037b6912980c57929a5b6d789d250ee6a93e3b0a6018cf9f63e32ece`.

This fixes the hardware-pinned arithmetic-decoder failure in the retired
floating-point SPLM archive. CPR1 changes only the lossless pose-carrier
representation. It does not replace the final GitHub `linux-nvidia-t4` run;
T4 CI remains the hardware-specific gate.

## Representation

The archive contains all charged model data and tokens:

- a `40,252`-byte quantized semantic renderer for the second frame of each pair;
- a `23,054`-byte CPR1 low-rank gray pose carrier for the first frame;
- a `20,179`-byte integer-lattice HPAC entropy model;
- a `116,980`-byte self-compressed semantic token stream.

Within the submission's fixed tensor schema, CPR1 is self-delimiting. It stores
the original 32-symbol pose basis with a canonical Huffman table and the
original 12 coefficient time series with exact per-dimension Rice parameters.
Its header, scales, and tables are all charged to the archive. The carrier
round-trips every original 5-bit basis symbol and 12-bit delta/zigzag
coefficient code exactly.

No external neural model or uncharged data artifact is loaded during inflation.

## Submission Files

- `archive.zip`: charged payload; contains one stored member named `p`.
- `compress.sh`: hash-locked entry point that reproduces the exact charged
  archive.
- `inflate.sh`: challenge entry point.
- `inflate.py`, `carrier_codec.py`: entropy decode, exact CPR1 decode, and
  semantic/pose rendering.
- `hpac_integer.py`, `hpac_integer_sparse.py`, `integer_model_io.py`: portable
  integer HPAC runtime.
- `repack_carrier.py`: deterministic frozen-source-to-CPR1 repacker.
- `test_carrier_codec.py`: positive, randomized, malformed-stream, and frozen
  golden tests.
- `verification.json`: machine-readable provenance and validation facts.
- `MANIFEST.sha256`: checksum lock for the PR-tracked submission files.

Full official reports, logs, source checkpoints, and the exact entropy hash
proof are retained outside the PR tree in the project preservation bundle at
`results/preserved/semantic_pose_landslide_selfcompress/`.

## Submission Checklist

- [x] Freeze the exact archive and decoder hashes.
- [x] Verify ZIP structure and payload lineage.
- [x] Prove decoded model/carrier equality against the validated source archive.
- [x] Preserve the source archive's complete Ada and Ampere validation evidence.
- [x] Confirm the submission name is absent from upstream commit `d3f688f`.
- [x] Upload this exact `archive.zip` to a stable public URL.
- [x] Include the deterministic compression stage and exact-output checks.
- [x] Open the PR with the runtime files under this exact directory name.
- [ ] Select `linux-nvidia-t4` and require official CI success before merging.

The upstream PR template says not to commit `archive.zip` or `report.txt`; use
the external archive URL and include the report contents in the PR body.
