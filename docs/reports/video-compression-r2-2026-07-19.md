# M02 — Video Compression Round 2 Reference Frontier
**Status:** COMPLETE | **Date:** 2026-07-19 | **Session:** 2

## Does
Records the Round-2 reference checkpoint, independently retained evidence, provisional M201–M205 frontier, and the strict next-round admission gates.

## Gate
```bash
python -m compileall -q scripts && python scripts/m02_verify_reference_submission.py && git diff --check
```
Expected: `manifest: .evidence/m02_reference_manifest.json` followed by exit code `0`.
Actual:
```text
manifest: .evidence/m02_reference_manifest.json

exit code: 0
```

## Touches
- `docs/reports/video-compression-r2-2026-07-19.md` — durable Round-2 checkpoint, claims, audit, and gates.
- `.evidence/m01_progress_ledger.jsonl` — appended Round-2 provisional-frontier event.

## Out-of-scope
- No candidate is promoted as the new reference until its full-precision CPU score is **strictly `<0.187`**; `0.187946` does not pass.
- No submission payload, evaluator, dependency, plan document, upstream branch, or attribution statement was changed.

## Findings

### Checkpoint and axes

The Round-2 checkpoint is **strictly `<0.187`**, not `≤0.187` and not a two-decimal display value. The retained reference computes to `0.18794542778901213`, while its report displays `0.19` (`.evidence/m02_reference_manifest.json:27-35`; `submissions/rhnerv_latent_polish/report_cpu.txt:11-17`). It remains a reference artifact, not a passing next-round candidate.

| Axis | Round-2 observable | Direction / gate |
| --- | --- | --- |
| Full-precision final score | `0.18794542778901213` | lower; admission requires **strictly `<0.187`** |
| SegNet distortion | `0.00053263` | lower |
| PoseNet distortion | `0.00002937` | lower |
| Compression rate | `0.00470179` (`176,531 / 37,545,489`) | lower |
| Artifact identity | archive `6d1128…f859`; member `268704…7827` | exact SHA equality |
| CPU reproducibility | CPU report plus deterministic rebuild | preserve / independently rerun |
| Attribution integrity | content-derived provenance, not object existence | prove |
| Evidence integrity | `5/0/0/2` | retain evidence; isolate flags |

The score axis uses the exact contest formula `S = 100·seg + sqrt(10·pose) + 25·rate` (`submissions/rhnerv_latent_polish/README.md:31-40`; `scripts/m02_verify_reference_submission.py:150-179`).

### Round-2 roster and xask targets

| Slot | Round role | xask target |
| --- | --- | --- |
| Planner | checkpoint, axes, and frontier synthesis | local planner baseline |
| M201 | source-attribution audit and mismatch triage | `codex` |
| M202 | archive/member identity audit | `codex` |
| M203 | full-precision metric reconstruction | `codex` |
| M204 | deterministic reconstruction and required-file audit | `codex` |
| M205 | pair-local scoring and next-gate derivation | `codex` |

Claims remain identified by M-number; model output is retained only when independently supported by repository evidence.

### M201–M205 claims and evidence

| ID | Claim | Evidence | Provisional verdict |
| --- | --- | --- | --- |
| M201 | Commit `5a6cdcbdbabcef8b7c5682c861e5689783d4587c` proves the reconstructed artifact's source attribution. | The verifier only runs `git rev-parse --verify` and accepts any locally present object prefix (`scripts/m02_verify_reference_submission.py:81-86`); the resulting `source_ref_match: true` therefore proves object existence, not artifact derivation (`.evidence/m02_reference_manifest.json:37-40`). | **hold** — source-ref false-positive; `spoof_flagged` |
| M202 | The retained archive and member identities are pinned. | Actual and expected archive SHA are `6d11284b051540be190b2613e615edad4efec7fddbfc627000d0d5fd0bd3f859`; member SHA is `2687049683aae7848bc9d0a23feb8809efe7875d8cf0ba34e58f41ab538f7827` (`.evidence/m02_reference_manifest.json:2-4,25`). | **accept** |
| M203 | The complete metric vector reconstructs the reference score at full precision. | Pose `2.937e-05`, seg `0.00053263`, and rate `0.00470179` produce `0.18794542778901213` (`.evidence/m02_reference_manifest.json:26-35`). | **accept** |
| M204 | The checked-in reference is reproducible and structurally complete. | All 18 required paths are true and manifest status is `pass` (`.evidence/m02_reference_manifest.json:5-24,40`); the encoder asserts member bytes, archive bytes, and both SHA-256 values (`submissions/rhnerv_latent_polish/compress.py:31-40,71-98`). | **accept** |
| M205 | Pair-local latent changes admit exact aggregate rescoring without a full conceptual redefinition of the metric. | There are 600 independent latent rows and one row renders one two-frame pair (`submissions/rhnerv_latent_polish/METHOD.md:24-42,83-94`); selection is exact-gated with real archive bytes (`submissions/rhnerv_latent_polish/METHOD.md:98-125`). | **accept** |

### Exact pair formula

For baseline pair means `seḡ`, `posē`, archive bytes `B`, raw bytes `U = 37,545,489`, and a change confined to pair `p` with per-pair distortion deltas `Δseg_p`, `Δpose_p` and exact re-encoded byte delta `ΔB`, the exact score delta is:

```text
ΔS_p = 100·(Δseg_p / 600)
       + sqrt(10·(posē + Δpose_p / 600)) - sqrt(10·posē)
       + 25·(ΔB / 37,545,489)
```

For a set of distinct pairs, replace each single-pair delta by the sum of those pair deltas inside the corresponding mean update, and use the set's exact re-encoded `ΔB`. Pair distortions are additive before aggregation; final-score deltas are not literally pairwise additive because PoseNet's mean is inside a square root. This resolves the over-broad “effects … add up exactly” wording (`submissions/rhnerv_latent_polish/METHOD.md:83-94`) while retaining the independently supported pair-local evaluation fact.

### Source-attribution mismatch resolution

- The Round-1 source-dependent audit is **invalid** because repository object presence cannot establish that the evidence was produced from that source (`scripts/m02_verify_reference_submission.py:81-86`). This source-ref result is the first `spoof_flagged` audit item.
- Independently rerun artifact, required-file, metric, and deterministic-build evidence is retained because those checks bind directly to checked-in bytes and values (`.evidence/m02_reference_manifest.json:2-35`; `submissions/rhnerv_latent_polish/compress.py:71-98`). The invalid source-dependent reuse is isolated rather than allowed to contaminate M202–M205.
- The second `spoof_flagged` audit item is the inherited claim that source-dependent Round-1 evidence remained valid after reconstruction; it is explicitly retired, not counted as missing or dropped. No unresolved source attribution is used to accept M202–M205.

### Evidence audit and provisional frontier

- Audit: **5 with evidence, 0 without, 0 dropped, 2 spoof_flagged**.
- `audit_hash`: `b9b4f805be4043fb30b9d557b4d0ac369596a1eea047c4aa4388800228d671fb`.
- Provisional accept: **M202, M203, M204, M205**.
- Hold: **M201**, pending content-derived source proof.
- M02 implementation commits: `8b280d3` (reference reconstruction and verifier) and `91378de` (pinned metric enforcement) (`git log --oneline`; commits `8b280d3`, `91378de`).
- Pre-report remote checkpoint: local `HEAD` and `VeigaPunk/mission/M01` both resolved to `91378de299a33976e449abafe479cb585d68fc24`; post-commit closeout must push only `HEAD:mission/M01` to `VeigaPunk` and verify exact SHA equality.

### Next-round gates

1. **Score:** official full-precision CPU evaluation computes `S < 0.187`; rounded report text is non-evidence.
2. **Pair accounting:** publish `seḡ`, `posē`, `B`, `U`, changed-pair deltas, exact re-encoded `ΔB`, and the exact aggregate formula above.
3. **Artifact identity:** deterministic rebuild reproduces the declared archive and member SHA-256 values byte-for-byte.
4. **Runtime structure:** required files exist, ZIP has exactly member `x`, raw output size is invariant, and decode remains CPU-valid.
5. **Source attribution:** compare content/tree provenance or a reproducible derivation chain; `git rev-parse` object existence is forbidden as source proof.
6. **Remote closeout:** push only `HEAD:mission/M01` to `VeigaPunk`; local and remote full SHAs must be identical. Never amend, force, set upstream, or push `upstream`.

## Links
- Plan: team `video-compression-0719`, Round 2 session prompt (no repository plan document supplied)
- Reference manifest: `.evidence/m02_reference_manifest.json`
- Durable ledger: `.evidence/m01_progress_ledger.jsonl`
- Round 1: `docs/reports/video-compression-r1-2026-07-19.md`
- Next: M03 — admit only a strictly `<0.187` independently evidenced candidate
