# M01 — Video Compression Round 1 Bootstrap Frontier
**Status:** COMPLETE | **Date:** 2026-07-19 | **Session:** 1

## Does
Records the first-round baseline, six anonymized evidence-bearing claims, provisional frontier, surveyed optimization routes, and durable M01/remote state for team `video-compression-0719`.

## Gate
```bash
python -m compileall -q scripts
python scripts/m01_progress_ledger.py tail -n 1
git diff --check
```
Expected:
```text
{"ts_utc": "2026-07-19T17:08:05Z", "mission": "M01", "event": "round1.frontier", "status": "provisional", "branch": "mission/M01", "commit": "ebd8f735484506c8321c4bff766348abcd103960", "notes": "Round 1: accept M001/M002/M003/M006; hold M004/M005 pending triage; evidence audit 6/0/0, 2 spoof-flagged; report docs/reports/video-compression-r1-2026-07-19.md"}

exit code: 0
```
Actual:
```text
{"ts_utc": "2026-07-19T17:08:05Z", "mission": "M01", "event": "round1.frontier", "status": "provisional", "branch": "mission/M01", "commit": "ebd8f735484506c8321c4bff766348abcd103960", "notes": "Round 1: accept M001/M002/M003/M006; hold M004/M005 pending triage; evidence audit 6/0/0, 2 spoof-flagged; report docs/reports/video-compression-r1-2026-07-19.md"}

exit code: 0
```

## Touches
- `docs/reports/video-compression-r1-2026-07-19.md` — durable Round-1 report and evidence audit.
- `.evidence/m01_progress_ledger.jsonl` — concise Round-1 status appended through `scripts/m01_progress_ledger.py add`.

## Out-of-scope
- M004 and M005 implementation or performance conclusions are deferred pending spoof triage.
- No codec candidate, evaluator, challenge asset, dependency lock, or upstream branch was changed.

## Findings

### Axes and observables

| Axis | Round-1 observable | Direction |
| --- | --- | --- |
| Final score | `4.44` over 600 samples | lower |
| SegNet distortion | `0.00947028` | lower |
| PoseNet distortion | `0.39854303` | lower |
| Compression rate | `0.05988320` (`2,248,344 / 37,545,489` bytes) | lower |
| Encode wall time | `1.387 s` | lower |
| Evaluation wall time | `102.506 s` on CPU | lower |
| Reproducibility | pinned input/model/script hashes, raw-size check, CPU check | preserve/pass |
| Evidence integrity | `6 with evidence, 0 without, 0 dropped, 2 spoof_flagged` | maximize evidence; triage flags |

The metric formula weights semantic distortion, temporal distortion, and rate as `100*segnet_dist + sqrt(10*posenet_dist) + 25*rate` (`README.md:18-25`). The measured baseline values and timings are transcribed from `.evidence/baseline-evaluate.log:60-68` and `.evidence/baseline-compress.log:1-5`.

### Roster and xask targets

| Slot | Round role | xask target |
| --- | --- | --- |
| Planner | baseline framing and frontier synthesis | local planner baseline |
| M001 | anonymous evidence claim | `codex` |
| M002 | anonymous evidence claim | `codex` |
| M003 | anonymous evidence claim | `codex` |
| M004 | anonymous evidence claim; spoof triage | `codex` |
| M005 | anonymous evidence claim; spoof triage | `codex` |
| M006 | anonymous evidence claim | `codex` |

Claims remain identified only by M-number; no author/model attribution is retained in this durable report.

### Planner baseline

- Starting source was `d3f688f84f555c5aaebee7d2c4203efc8a9051e2`, with Python `3.11.15`, uv `0.11.29`, Git LFS `3.7.1`, FFmpeg `n8.1.2`, and checksummed video/models/evaluator scripts (`.evidence/preflight.log:1-15`).
- The baseline encoded one video to HEVC, producing a `2,248,344`-byte archive in `1.387` wall seconds (`.evidence/baseline-compress.log:1-5`).
- CPU evaluation decoded 1,200 frames and scored 600 samples at `4.44` in `102.506` wall seconds (`.evidence/baseline-evaluate.log:1-3,60-68`).
- Verification confirmed tracked objects, HEVC geometry, the `3,662,409,600`-byte raw-frame invariant, and CPU execution (`.evidence/verification.log:4-31`).

### Anonymized claims and evidence

| ID | Claim | Evidence | Provisional verdict |
| --- | --- | --- | --- |
| M001 | The repository and challenge assets are sufficiently pinned to reproduce the bootstrap run. | SHA-256 values cover the source video, both metric models, lockfile, evaluator, and baseline scripts (`.evidence/preflight.log:7-15`). | **accept** |
| M002 | The local baseline establishes a complete score vector, not merely an aggregate score. | PoseNet `0.39854303`, SegNet `0.00947028`, rate `0.05988320`, and score `4.44` are emitted together (`.evidence/baseline-evaluate.log:60-67`). | **accept** |
| M003 | A runnable CPU environment exists despite the stale locked-resolution path. | `uv sync --locked` reports a lock update requirement, while frozen sync installs 36 packages including CPU Torch (`.evidence/uv-sync.log:6-9`; `.evidence/uv-sync-frozen.log:22-60`). | **accept** |
| M004 | Conventional codec/resolution/ROI tuning may advance the score frontier cheaply. | The repository points to a large FFmpeg grid search and the leaderboard contains codec, resize, ROI, and masking families (`README.md:1087-1095`; `README.md:781-959`). Evidence is survey-only, not a candidate run. | **hold** — `spoof_flagged`, triage required |
| M005 | Learned implicit-video or hybrid residual methods may dominate conventional tuning. | The leaderboard's leading entries are HNeRV/learned families with scores `0.187`–`0.206` (`README.md:151-344`). Evidence is third-party leaderboard evidence, not a locally reproduced artifact. | **hold** — `spoof_flagged`, triage required |
| M006 | M01 progress and remote identity can be recorded and machine-checked. | Commit `ebd8f735484506c8321c4bff766348abcd103960` introduced the JSONL ledger and SHA verifier; the Round-1 event records that commit (`.evidence/m01_progress_ledger.jsonl:3`; `scripts/m01_verify_remote_sha.py:38-50`). | **accept** |

### Contradictions and resolutions

- **Locked vs runnable environment:** `uv sync --locked` failed because `uv.lock` needs updating (`.evidence/uv-sync.log:6-9`), while `uv sync --frozen` installed the recorded environment (`.evidence/uv-sync-frozen.log:22-60`). Resolution: accept environment bootstrapping for Round 1, preserve the lock mismatch as a reproducibility caveat, and do not mutate the lockfile.
- **Documented vs observed baseline:** README documents score `4.39` and archive size `2,244,900` bytes (`README.md:95-101`), while this run observed `4.44` and `2,248,344` bytes (`.evidence/baseline-evaluate.log:60-67`). Resolution: use the locally measured vector as planner baseline and retain README values only as historical reference.
- **Promising routes vs reproduced evidence:** M004/M005 survey evidence suggests large gains but supplies no local candidate run. Resolution: preserve both claims, mark both `spoof_flagged`, and hold rather than drop them pending triage.
- **Initial remote check vs verified M01:** the ledger initially recorded remote verification as failed/pending at source `d3f688f...` (`.evidence/m01_progress_ledger.jsonl:2`); commit `ebd8f735484506c8321c4bff766348abcd103960` is now the M01 bootstrap commit and was observed at both local `HEAD` and `VeigaPunk/mission/M01` before this report commit. Resolution: supersede the pending state with explicit post-push SHA equality evidence for this atomic report commit.

### Evidence audit and provisional verdicts

- Audit: **6 with evidence, 0 without, 0 dropped, 2 spoof_flagged**.
- `audit_hash`: `39323a912e96d4c2eb400a380bb7101ea02e96f659b631efee56f8b18e4b7b00`.
- Accept: **M001, M002, M003, M006**.
- Hold pending triage: **M004, M005**.

### Optimization routes surveyed

1. Conventional HEVC/AV1 parameter, GOP, rate-control, film-grain, and resize sweeps (`README.md:781-1003,1087-1095`).
2. Semantic ROI, adaptive masks, range/tile coding, and task-metric-aware preprocessing (`README.md:421-539,781-959`).
3. Learned implicit video representations, especially HNeRV variants and latent/codebook compression (`README.md:151-344`).
4. Hybrid neural/residual/entropy and exact-context recoding routes represented by the leading leaderboard families (`README.md:151-224,301-419`).
5. Cheap frontier controls: retain the CPU baseline as a regression anchor and compare full score vectors, archive bytes, and wall time rather than score alone (`.evidence/baseline-evaluate.log:60-68`).

### M01 commit and remote verification

- Bootstrap commit: `ebd8f735484506c8321c4bff766348abcd103960` (`ebd8f735...`).
- Pre-report observation: local `HEAD` and `refs/heads/mission/M01` on remote `VeigaPunk` both resolved to `ebd8f735484506c8321c4bff766348abcd103960`.
- Required closeout: push only `HEAD:mission/M01` to `VeigaPunk`, then compare local and remote SHAs with `scripts/m01_verify_remote_sha.py`; the final evidence belongs in the task return.

## Links
- Plan: team `video-compression-0719`, Round 1 session prompt (no repository plan document supplied)
- Baseline evidence: `.evidence/preflight.log`, `.evidence/baseline-compress.log`, `.evidence/baseline-evaluate.log`, `.evidence/verification.log`
- Durable ledger: `.evidence/m01_progress_ledger.jsonl`
- Next: M02 — triage M004/M005 and run the first non-dominated candidate
