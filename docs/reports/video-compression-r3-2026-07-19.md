# M03 — Video Compression Round 3 Screen Proof
**Status:** COMPLETE | **Date:** 2026-07-19 | **Session:** 3

## Does
Records the Round-3 one-pair CPU screen proof, repaired runtime/source checks, rejected harmful mutant, scoped probe conclusions, and strict Round-4 `<0.187` funnel.

## Gate
```bash
python -m unittest -v tests.test_m02_verifier tests.test_m03_screen && python scripts/m02_verify_reference_submission.py && python -c 'import json, pathlib; r=json.loads(pathlib.Path(".evidence/m03_onepair_delta_screen.jsonl").read_text()); assert r["mode"] == "full_qualification"; assert r["output"]["samples"] == 600; assert r["render_matches_full_inflate"] == {"baseline": True, "mutant": True}; assert abs(r["prediction_error"]) < 1e-9; print("m03 screen proof: pass")' && git diff --check
```
Expected: four unit tests report `OK`, then `manifest: .evidence/m02_reference_manifest.json`, then `m03 screen proof: pass`, with exit code `0`.
Actual:
```text
test_blob_is_rejected (tests.test_m02_verifier.SourceObjectVerificationTest.test_blob_is_rejected) ... ok
test_nonexistent_full_sha_is_rejected (tests.test_m02_verifier.SourceObjectVerificationTest.test_nonexistent_full_sha_is_rejected) ... ok
test_pinned_commit_is_accepted (tests.test_m02_verifier.SourceObjectVerificationTest.test_pinned_commit_is_accepted) ... ok
test_exact_one_pair_formula (tests.test_m03_screen.ExactPredictionTest.test_exact_one_pair_formula) ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.011s

OK
manifest: .evidence/m02_reference_manifest.json
m03 screen proof: pass

exit code: 0
```

## Touches
- `docs/reports/video-compression-r3-2026-07-19.md` — durable Round-3 roster, audit, screen proof, verdicts, and next-round funnel.
- `.evidence/m01_progress_ledger.jsonl` — appended Round-3 screen-proof event.

## Out-of-scope
- No harmful mutant is promoted, and no archive, codec, evaluator, model, selector, dependency lock, plan document, upstream branch, or attribution statement is changed.
- The proof is scoped to pair `0`, latent dimension `0`, step `+1`, the pinned artifact/runtime, and the recorded host; it does not prove global latent, rate, selector, or cross-host behavior (`.evidence/m03_onepair_delta_screen.jsonl:1`; `.evidence/m02_reference_manifest.json:25-75`).

## Findings

### Round-3 roster and axes

| Slot | Round role | Evidence target | Provisional verdict |
| --- | --- | --- | --- |
| Planner | preserve the strict checkpoint and synthesize the Pareto frontier | Round-2 `<0.187` gate (`docs/reports/video-compression-r2-2026-07-19.md:96-103`) | **accept** |
| M301 | audit M02 source/runtime repair | commit `1a8c303`; repaired manifest (`.evidence/m02_reference_manifest.json:25-75`) | **accept, scoped** |
| M302 | prove one-pair prediction against a full CPU run | commit `52f8f46`; prediction and measurement (`.evidence/m03_onepair_delta_screen.jsonl:1`) | **accept** |
| M303 | audit runtime, cardinality, and artifact identities | full-qualification record (`.evidence/m03_onepair_delta_screen.jsonl:1`) | **accept** |
| M304 | decide the tested candidate | positive measured score delta (`.evidence/m03_onepair_delta_screen.jsonl:1`) | **reject and drop** |
| M305 | probe rate behavior | one equal-byte/equal-rate observation (`.evidence/m03_onepair_delta_screen.jsonl:1`) | **hold** — no general evidence |
| M306 | probe selector behavior | unchanged-selector latent path and pair/full equality (`scripts/m03_onepair_delta_screen.py:128-135,269-296`; `.evidence/m03_onepair_delta_screen.jsonl:1`) | **hold** — no selector-candidate evidence |

| Axis | Round-3 observable | Direction / decision |
| --- | --- | --- |
| Full-precision CPU score | baseline `0.187960070469`; mutant `0.18796257629` | lower; mutant is harmful |
| Prediction fidelity | predicted `0.1879625766500441`; error `3.600441056406112e-10` | minimize error |
| SegNet distortion | baseline `0.000532786071`; predicted `0.000532803025242407`; measured `0.000532803067` | lower |
| PoseNet distortion | baseline `2.9366705e-05`; predicted `2.9369484100517122e-05`; measured `2.9369468e-05` | lower |
| Rate | baseline/measured `0.004701789874`; exact predicted ratio `0.0047017898741444015` | lower; observed byte delta `0` |
| Runtime | one-pair `3.3108921379898675 s`; total qualification `289.4277758440003 s` | lower while preserving proof |
| Cardinality | `600` judged pairs, `1,200` frames per render, shape `[1200,874,1164,3]` | exact |
| Artifact identity | four archive/raw hashes plus two member hashes | exact SHA-256 equality/inequality as declared |

All numerical axis values in the table are transcribed from the sole full-qualification record (`.evidence/m03_onepair_delta_screen.jsonl:1`).

### M301 — M02 repair and provenance limit

- Repair commit `1a8c303befccfc808fbc4fcc275fe6408a8afa37` requires a full 40-hex source identifier, checks that it is a Git `commit`, pins six LFS object IDs, and records Python `3.11.15`, uv `0.11.29`, Git LFS `3.7.1`, and FFmpeg `n8.1.2` (`scripts/m02_verify_reference_submission.py:53-68,98-114,145-163`; `.evidence/m02_reference_manifest.json:25-75`).
- The repair closes the earlier abbreviated-object/type and runtime-identity gaps, but `git cat-file -t` still proves only that commit `5a6cdcbdbabcef8b7c5682c861e5689783d4587c` exists and has type `commit`; it does **not** establish a content derivation from that commit (`scripts/m02_verify_reference_submission.py:98-114`; `.evidence/m02_reference_manifest.json:72-75`). M301 is therefore accepted only as object/runtime/LFS binding, not end-to-end provenance.

### M302–M304 — numerical screen proof and harmful-candidate rejection

- The tested mutation is pair `0`, dimension `0`, code `147→148`, step `+1`; member SHA changes from `2687049683aae7848bc9d0a23feb8809efe7875d8cf0ba34e58f41ab538f7827` to `b665e1ddbbaebc65784cdd1be8debeef035f9a47ef3132b3660c3894460789d8` (`.evidence/m03_onepair_delta_screen.jsonl:1`).
- Pair-local measurements are baseline pose `2.4338538423762657e-05`, baseline seg `0.0005340576171875`, mutant pose `2.600599873403553e-05`, mutant seg `0.0005442301626317203`, pose delta `1.6674603102728724e-06`, and seg delta `1.0172545444220304e-05`; judging took `0.5669008169934386 s` inside a `3.3108921379898675 s` render-and-judge screen (`.evidence/m03_onepair_delta_screen.jsonl:1`).
- From the 600-sample baseline, the exact formula predicts pose `2.9369484100517122e-05`, seg `0.000532803025242407`, rate `0.0047017898741444015`, score `0.1879625766500441`, and delta `+2.5062701092259942e-06`; the full CPU run measures pose `2.9369468e-05`, seg `0.000532803067`, rate `0.004701789874`, score `0.18796257629`, and delta `+2.505820999976205e-06`, leaving prediction error `3.600441056406112e-10` (`.evidence/m03_onepair_delta_screen.jsonl:1`).
- Because both predicted and measured deltas are positive, the candidate harms the score axis while improving none of the recorded axes; M304 rejects and drops it under the Pareto filter (`.evidence/m03_onepair_delta_screen.jsonl:1`).

### Runtime, cardinality, and hash evidence

- Runtime seconds are baseline inflate `39.37681218801299`, mutant inflate `41.58414972000173`, baseline full CPU `97.74288165899634`, mutant full CPU `102.64426790000289`, one-pair screen `3.3108921379898675`, and total `289.4277758440003` (`.evidence/m03_onepair_delta_screen.jsonl:1`).
- Both full renders contain `1,200` frames and both evaluations contain `600` samples; the recorded raw shape is `[1200,874,1164,3]`, and pair-local baseline/mutant renders each match their respective full inflate exactly (`.evidence/m03_onepair_delta_screen.jsonl:1`).
- Baseline archive/raw SHA-256 are `6d11284b051540be190b2613e615edad4efec7fddbfc627000d0d5fd0bd3f859` / `00ef1cec006d637455f3490edcbe78f32ee8a8e2d2a949fe25364e18b1047d90`; mutant archive/raw SHA-256 are `27173f6707ee724b5fb2bd3eaa3ce129777a152ff8b0bac8febc934b4ce4baa9` / `d90d3178d44055a3ca8cdc2f336b9ea9268a186055456bc307d80ac420c23564` (`.evidence/m03_onepair_delta_screen.jsonl:1`).

### M305/M306 probe outcomes and scope

- **Rate probe:** baseline and mutant archives are each `176,531` bytes and report rate `0.004701789874`, so this mutation's exact byte delta is zero even though archive/member hashes differ (`.evidence/m03_onepair_delta_screen.jsonl:1`). One point cannot support “latent clicks are rate-neutral”; M305 remains held without general evidence.
- **Selector probe:** the mutation rebuild preserves the original selector bytes and coder IDs, then the pair-only render applies the normal compact selector; both baseline and mutant pair renders equal their full-inflate slices (`scripts/m03_onepair_delta_screen.py:128-135,269-296,398-409`; `.evidence/m03_onepair_delta_screen.jsonl:1`). This validates selector-path preservation for the tested latent mutation only; no alternate selector was generated or scored, so M306 remains held without selector-candidate evidence.

### Evidence audit and provisional verdicts

- Supplied Round-3 audit: **4 with evidence / 2 without evidence / 1 dropped / 4 spoof-flagged**; audit hash `3a0fe695032ca8f68c2e5a17657a0c71a3d30b4ec35fd338cb25f44562b8fc14` (Round-3 mission directive, direct quote: “evidence audit 4/2/1/4”).
- Evidence-backed: **M301 (scoped), M302, M303, M304**; without general/selector-candidate evidence: **M305, M306**; dropped: the M304 pair-0/dim-0/+1 mutant (`.evidence/m03_onepair_delta_screen.jsonl:1`).
- The four isolated spoof flags are: treating commit-object existence as derivation provenance; treating distinct-pair distortion additivity as literal final-score additivity despite PoseNet's square root; generalizing one zero-byte delta into universal rate neutrality; and claiming selector optimization from an unchanged-selector path probe (`scripts/m02_verify_reference_submission.py:98-114`; `docs/reports/video-compression-r2-2026-07-19.md:69-85`; `.evidence/m03_onepair_delta_screen.jsonl:1`; `scripts/m03_onepair_delta_screen.py:128-135`). None is used to promote a candidate.
- Round-3 implementation anchors are M02 repair commit `1a8c303` and M03 full proof commit `52f8f46` (`git log --oneline`; commits `1a8c303`, `52f8f46`).

### Round-4 strict `<0.187` funnel

1. Screen only representable candidates through the exact CPU pair path; preserve selector application and record pair/dimension/step, pair seg/pose deltas, render time, and member hash (`scripts/m03_onepair_delta_screen.py:269-329`; `.evidence/m03_onepair_delta_screen.jsonl:1`).
2. Reject every predicted `ΔS ≥ 0`; for survivors, re-encode with the real coder and publish exact archive bytes/rate and archive/member SHA-256 (`scripts/m03_onepair_delta_screen.py:332-350,373-387`).
3. Full-qualify survivors over exactly 600 CPU samples and 1,200 frames, requiring pair renders to equal full-inflate slices and predicted/measured values to agree within a declared numerical tolerance (`scripts/m03_onepair_delta_screen.py:389-441`).
4. Promote only a measured full-precision official CPU score **strictly `<0.187`**. Neither baseline `0.187960070469` nor harmful mutant `0.18796257629` enters Round 4 (`.evidence/m03_onepair_delta_screen.jsonl:1`).
5. Require deterministic artifact hashes, pinned runtime/LFS identities, content-derived provenance beyond object existence, and exact local/`VeigaPunk/mission/M01` SHA equality; rounded score text and `upstream` pushes remain inadmissible (`.evidence/m02_reference_manifest.json:25-75`; `scripts/m01_verify_remote_sha.py:38-50`).

## Links
- Plan: team `video-compression-0719`, Round 3 mission directive (no repository plan document supplied)
- Proof: `.evidence/m03_onepair_delta_screen.jsonl`
- Repair: commit `1a8c303befccfc808fbc4fcc275fe6408a8afa37`
- Full proof: commit `52f8f46a5870bee8f6d52b8744c07c58b41ede11`
- Durable ledger: `.evidence/m01_progress_ledger.jsonl`
- Previous: `docs/reports/video-compression-r2-2026-07-19.md`
- Next: M04 — admit only a fully qualified, independently evidenced score strictly `<0.187`
