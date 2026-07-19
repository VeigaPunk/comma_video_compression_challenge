# M04 PR #130 local qualification

## Result

PR #130 `semantic_pose_landslide_selfcompress` qualified locally on an NVIDIA
GeForce RTX 5070 with the official evaluator restored byte-for-byte.

- source: `4ea9513451a0bc375faa84c97b8820410fefe918`
- archive SHA-256: `0491d5df84fc70b62b3f7ccf8894f5e1b81c616de46a052e4423fc1e18fdc7cd`
- archive size: `191052` bytes
- exact samples: `600`
- exact score: `0.17076926565506415`
- official `evaluate.sh` wall time: `142.0979006879934` seconds
- total official-plus-diagnostic wall time: `181.40392018099374` seconds
- inflated shape: `[1200, 874, 1164, 3]`
- inflated SHA-256 on this GPU: `bc3c6b6092ae26f76ef375ce9314d1270ad57380341608f6dc5b43467cf9c650`

The tracked submission tree is byte-identical to the PR head. Its license is
the PR repository's MIT `LICENSE`, whose SHA-256 matches this repository's
root `LICENSE`: `f6f2bcc9096b01dd1017365f74be2b31236bb34b04a4dc04a324679326ec976e`.
The archive remains an external, hash-locked release asset as required by the
upstream submission policy.

## Reproduction

```bash
git fetch upstream pull/130/head:refs/remotes/upstream/pr/130
curl --fail --location \
  --output submissions/semantic_pose_landslide_selfcompress/archive.zip \
  https://github.com/fesalfayed/comma_video_compression_challenge/releases/download/semantic-pose-landslide-selfcompress-cpr1/archive.zip
.tools/uv/uv sync --frozen --group cu130
.tools/uv/uv run --group cu130 python scripts/m04_evaluate_proof.py \
  --run-official \
  --submission-dir submissions/semantic_pose_landslide_selfcompress \
  --device cuda \
  --timeout-seconds 1800 \
  --expected-output-sha256 bc3c6b6092ae26f76ef375ce9314d1270ad57380341608f6dc5b43467cf9c650 \
  --official-log .evidence/m04_pr130_official.log \
  --output .evidence/m04_pr130_exact.json
```

The official run uses untouched `evaluate.sh` and `evaluate.py`. The second
pass is an isolated diagnostic copy that changes only four display format
specifiers to expose the already-computed floating-point values. The proof
fails on source/archive/output hash drift, cardinality drift, score
`>= 0.187`, or total runtime `>= 1800` seconds.
