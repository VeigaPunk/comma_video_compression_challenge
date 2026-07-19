# M04 — Video Compression Round 4 Local Qualification
**Status:** COMPLETE | **Date:** 2026-07-19 | **Session:** 4

## Does
Records the final Round-4 synthesis: PR #130 is **LOCAL QUALIFIED**, M401–M406 are accepted, M407 is held, M408 is dropped, and no duplicate PR will be opened while official eligibility/authorship remains unresolved.

## Gate
```bash
python -m unittest -v tests.test_m02_verifier tests.test_m03_screen tests.test_m04_evaluator_proof && python scripts/m02_verify_reference_submission.py && python -c 'import json,pathlib; p=json.loads(pathlib.Path(".evidence/m04_pr130_exact.json").read_text()); assert p["metrics"] == {"archive_bytes":191052,"final":0.17076926565506415,"pose":1.94819294847548e-05,"rate":0.005088547388475883,"samples":600,"seg":0.0002959781268145889,"uncompressed_bytes":37545489}; assert p["runtime_seconds"] == 181.40392018099374; assert p["official_run"]["wall_seconds"] == 142.0979006879934; assert p["cardinality"] == {"ground_truth_frames":1200,"inflated":{"bytes":3662409600,"frames":1200,"pairs":600,"raw_shape":[1200,874,1164,3],"sha256":"bc3c6b6092ae26f76ef375ce9314d1270ad57380341608f6dc5b43467cf9c650"}}; assert p["archive_sha256"] == "0491d5df84fc70b62b3f7ccf8894f5e1b81c616de46a052e4423fc1e18fdc7cd"; assert p["source"] == {"ref":"refs/remotes/upstream/pr/130","sha":"4ea9513451a0bc375faa84c97b8820410fefe918","tracked_tree_matches":True}; print("m04 local qualification: pass")' && git diff --check
```
Expected: the seven named tests report `ok`, the suite reports `OK`, then exactly `manifest: .evidence/m02_reference_manifest.json` and `m04 local qualification: pass`, with exit code `0` and no `git diff --check` output.
Actual:
```text
test_blob_is_rejected (tests.test_m02_verifier.SourceObjectVerificationTest.test_blob_is_rejected) ... ok
test_nonexistent_full_sha_is_rejected (tests.test_m02_verifier.SourceObjectVerificationTest.test_nonexistent_full_sha_is_rejected) ... ok
test_pinned_commit_is_accepted (tests.test_m02_verifier.SourceObjectVerificationTest.test_pinned_commit_is_accepted) ... ok
test_exact_one_pair_formula (tests.test_m03_screen.ExactPredictionTest.test_exact_one_pair_formula) ... ok
test_exact_raw_cardinality (tests.test_m04_evaluator_proof.OfficialEvaluatorProofTest.test_exact_raw_cardinality) ... ok
test_official_evaluator_is_byte_exact (tests.test_m04_evaluator_proof.OfficialEvaluatorProofTest.test_official_evaluator_is_byte_exact) ... ok
test_precision_transform_only_changes_result_formats (tests.test_m04_evaluator_proof.OfficialEvaluatorProofTest.test_precision_transform_only_changes_result_formats) ... ok

----------------------------------------------------------------------
Ran 7 tests in 0.025s

OK
manifest: .evidence/m02_reference_manifest.json
m04 local qualification: pass
```

## Touches
- `docs/reports/video-compression-r4-2026-07-19.md` — final Round-4 axes, roster, exact local proof, evidence audit, verdicts, blockers, and PR decision.
- `.evidence/m01_progress_ledger.jsonl` — appended the atomic Round-4 final-synthesis event.

## Out-of-scope
- Official GitHub `linux-nvidia-t4` qualification remains pending; local RTX 5070 qualification does not replace that hardware-specific gate (`submissions/semantic_pose_landslide_selfcompress/verification.json:248-259`; `submissions/semantic_pose_landslide_selfcompress/README.md:130-133,173-186`).
- No duplicate upstream PR is opened: PR #130 is already open under Fesal Fayed's `fesalfayed/agent/semantic-pose-landslide-selfcompress`, while this mission has no evidence resolving eligibility or author authorization for a duplicate (GitHub PR query, direct quote: `"author" ... "login":"fesalfayed"`, `"state":"OPEN"`, `"statusCheckRollup":[]`; PR #130).
- Untracked `scripts/m04_round4_search.py` is deliberately left untracked and unstaged. It is stale and unneeded after PR #130 qualified, and its worsening path increments `full_count` without running a full qualification (`scripts/m04_round4_search.py:377-381`); no submission, evaluator, dependency lock, plan, or upstream ref is changed.

## Findings

### Axes and Round-4 roster

| Axis | Exact Round-4 observable | Direction / decision |
| --- | --- | --- |
| Final score | `0.17076926565506415` | lower; passes strict `<0.187` locally |
| PoseNet distortion | `1.94819294847548e-05` | lower |
| SegNet distortion | `0.0002959781268145889` | lower |
| Rate | `0.005088547388475883` = `191052 / 37545489` | lower |
| Runtime | official `142.0979006879934 s`; official-plus-diagnostic `181.40392018099374 s` | below `1800 s` local limit |
| Cardinality | `600` scored pairs; `1,200` ground-truth/inflated frames; `3,662,409,600` bytes; `[1200,874,1164,3]` | exact |
| Identity | source, archive, evaluator, shell evaluator, inflated output, and license SHA-256 | exact equality where declared |
| Portability | local `constriction 0.5.0` versus historical validations on `0.4.2` | disclose; do not generalize to T4 |
| Eligibility/authorship | existing author-owned PR; official T4 absent | hold merge claim; drop duplicate PR |

All metric, runtime, cardinality, source, and output values above are transcribed from the local proof (`.evidence/m04_pr130_exact.json:2-51`). The historical dependency value is recorded for both prior GPU validations (`submissions/semantic_pose_landslide_selfcompress/verification.json:185-235`); the local `0.5.0` value is the direct output of `.tools/uv/uv run --group cu130 python -c 'import importlib.metadata; print(importlib.metadata.version("constriction"))'`.

| Slot | Round role | Evidence target | Final verdict |
| --- | --- | --- | --- |
| Planner | preserve Pareto axes and distinguish local from official qualification | exact proof and T4 boundary (`.evidence/m04_pr130_exact.json:18-51`; `submissions/semantic_pose_landslide_selfcompress/verification.json:248-259`) | **accept** |
| M401 | bind the candidate to PR #130 source and tracked tree | source SHA `4ea9513451a0bc375faa84c97b8820410fefe918`, `tracked_tree_matches: true` (`.evidence/m04_pr130_exact.json:48-51`) | **accept** |
| M402 | prove official evaluator integrity | evaluator SHA `7da71a84ce24286bc6b583470f9bbd25c998971da301320d0d4e9d6fd40baa4b`; shell SHA `9612284ce6e9585aefcf636f3027808a56160ffd572edffdf4b8622a65fac917` (`.evidence/m04_pr130_exact.json:31-32`) | **accept** |
| M403 | retain exact full-precision metrics | exact pose, seg, rate, byte counts, samples, and final score (`.evidence/m04_pr130_exact.json:22-30`) | **accept** |
| M404 | retain runtime and cardinality | official and total wall times plus exact raw dimensions/hash (`.evidence/m04_pr130_exact.json:3-16,33-46`) | **accept** |
| M405 | bind the external artifact and lossless reproduction | archive `191,052` bytes / SHA `0491d5…c7cd`; deterministic repack requires that output (`submissions/semantic_pose_landslide_selfcompress/verification.json:4-19,130-144`) | **accept** |
| M406 | apply the strict local admission gate | exact final `0.17076926565506415 < 0.187` and total `181.40392018099374 < 1800` (`.evidence/m04_pr130_exact.json:18-30,46`) | **accept — LOCAL QUALIFIED** |
| M407 | claim official qualification/portability | T4 is `pending`; local dependency is `0.5.0`, historical evidence is `0.4.2` (`submissions/semantic_pose_landslide_selfcompress/verification.json:185-251`; local version command quoted above) | **hold** |
| M408 | open a duplicate PR | existing PR #130 is open and ownership/eligibility for duplication is unresolved (GitHub PR query quoted above; PR #130) | **drop** |

### Exact LOCAL QUALIFIED record

- **LOCAL QUALIFIED** means the untouched official `evaluate.sh` completed over `600` samples on the NVIDIA GeForce RTX 5070, and a separate display-format-only diagnostic exposed final `0.17076926565506415`, pose `1.94819294847548e-05`, seg `0.0002959781268145889`, rate `0.005088547388475883`, archive bytes `191052`, and uncompressed bytes `37545489` (`.evidence/m04_pr130_official.log:31-43,87-94`; `.evidence/m04_pr130_exact.json:22-45`).
- Runtime is official `142.0979006879934 s` and total official-plus-diagnostic `181.40392018099374 s`; exact cardinality is `600` pairs, `1,200` ground-truth frames, `1,200` inflated frames, `3,662,409,600` inflated bytes, shape `[1200,874,1164,3]` (`.evidence/m04_pr130_exact.json:3-16,33-46`).
- Exact hashes are source `4ea9513451a0bc375faa84c97b8820410fefe918`, archive `0491d5df84fc70b62b3f7ccf8894f5e1b81c616de46a052e4423fc1e18fdc7cd`, inflated output `bc3c6b6092ae26f76ef375ce9314d1270ad57380341608f6dc5b43467cf9c650`, evaluator `7da71a84ce24286bc6b583470f9bbd25c998971da301320d0d4e9d6fd40baa4b`, shell evaluator `9612284ce6e9585aefcf636f3027808a56160ffd572edffdf4b8622a65fac917`, and license `f6f2bcc9096b01dd1017365f74be2b31236bb34b04a4dc04a324679326ec976e` (`.evidence/m04_pr130_exact.json:2,15,31-32,48-51`; prior qualification record in this file's commit `7cb0719`).

### Evidence audit, blockers, and decision

- Supplied Round-4 audit is **7 with evidence / 1 without evidence / 1 dropped / 5 spoof-flagged**, with audit hash `1d1afc4167b6f24857c9edb5add49e509978b7d09c1fed5708438bc34e3144d9` (Round-4 mission directive, direct quote: “evidence audit 7/1/1/5”).
- Evidence-backed slots are M401–M407; M407 nevertheless remains held because the required official T4 result is the one missing item. M408 is dropped, not promoted (`submissions/semantic_pose_landslide_selfcompress/verification.json:248-259`; PR #130 query direct quote: `"statusCheckRollup":[]`).
- The five isolated spoof flags are: treating rounded official `0.17` as exact; treating the precision diagnostic as the untouched official executable; treating local RTX 5070 success as official T4 success; treating historical `constriction 0.4.2` as the local `0.5.0` runtime; and treating license/tree identity as eligibility or authorship authorization. None is used to cross the official gate or open another PR (`.evidence/m04_pr130_official.log:87-94`; `.evidence/m04_pr130_exact.json:31-51`; `submissions/semantic_pose_landslide_selfcompress/verification.json:185-251`; PR #130 query quoted above).
- Final verdicts are exactly **accept M401–M406; hold M407; drop M408**. The durable status is **LOCAL QUALIFIED**, not official-qualified, merge-ready, or author-eligible (`.evidence/m04_pr130_exact.json:18-30`; `submissions/semantic_pose_landslide_selfcompress/verification.json:248-259`).

## Links
- Plan: team `video-compression-0719`, Round 4 mission directive (no repository plan document supplied)
- Proof: `.evidence/m04_pr130_exact.json`
- Official log: `.evidence/m04_pr130_official.log`
- Durable ledger: `.evidence/m01_progress_ledger.jsonl`
- PR: https://github.com/commaai/comma_video_compression_challenge/pull/130
- Previous: `docs/reports/video-compression-r3-2026-07-19.md`
- Next: M05 — official T4/eligibility resolution only; no duplicate PR
