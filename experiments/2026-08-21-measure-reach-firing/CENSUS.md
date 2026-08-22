# CENSUS — reach outcomes across every committed run root

Instruments (all READ-ONLY; nothing under `src/` or `tests/` was touched):

| script | what it produces | output |
|---|---|---|
| `census.py` | recorded + re-derived census, every pair attributed to one exit | `census.json` (cheap pass), `census-verdicts.json` (`--verdicts`) |
| `probe_criteria.py` | which criteria rejected, and their verdicts, on two named roots | `probe_criteria.json` |
| `probe_content.py` | control for the missing-blob trap: is artifact content resolvable | `probe_content.json` |
| `probe_novelty.py` | the novelty x pass cross-tabulation for both qualifying criteria | `probe_novelty.json` |
| `probe_immunity.py` | the prose-immunity consequence of the P1 finding | `probe_immunity.json` |
| `verify_sweep_equivalence.py` | the REAL `reach_sweep` run on copies of four roots | `verify_sweep_equivalence.json` |

Two independent passes, deliberately not sharing a reader:

- **RECORDED** parses `<root>/log.jsonl` as text — Measure events carrying
  `reach_set` / `addr+`, and Measure inputs beginning `reach-provisional`.
  This is the typed record and it is the authority for *did reach fire*.
- **RE-DERIVED** opens the root with `Harness(root, read_only=True)` and walks
  `measures/reach.py::reach_sweep`'s decision tree over the replayed FINAL
  state, attributing every (ACCEPTED + addressing artifact, foreign problem)
  pair to exactly one exit. It records nothing: `record_measure` is never
  called. This is the diagnosis for *and if not, why*.

Exits, in the order `reach_sweep` takes them:

| exit | `reach.py` guard | meaning |
|---|---|---|
| `A-skip/status` | `if status != Status.ACCEPTED` | artifact-level, not a pair |
| `A-skip/unaddr` | `or aid not in addressed` | artifact-level, not a pair |
| `E1 no-criteria` | `or not problem.criteria` | foreign problem has no criteria |
| `E2 non-qualifying` | `if not qualifying` | no criterion is substantive-and-evaluable |
| `E3 no-novel` | `or not (set(qualifying) - carried)` | every qualifying criterion is already in the artifact's own battery |
| `E4 criterion-fail` | `if not all(_verdict(...) == PASS)` | some qualifying criterion does not PASS |
| `E5 coverage/provisional` | `if len(qualifying)/len(problem.criteria) < coverage_min` | logs `reach-provisional`; grounds nothing |
| `HIT full` | the fall-through | full hit: reach count + `addr_add` |

The operator's brief named three rejection paths (non-qualifying, no novel
criterion, coverage). The code has **five** pair-level exits: `E1` and `E4`
are the two the module docstring does not enumerate, and `E4` turns out to
carry every rejection that is not `E1` or `E3`. Recorded here rather than
silently folded into the nearest of the three.

## Scope

107 roots carry a `log.jsonl` under `experiments/`. **96 open** under the
current reader and are in scope. **11 do not** — every one of them with the
same typed refusal (a machine-readable decline, not a crash),
`UnsupportedRunManifestVersionError: UNSUPPORTED_RUN_MANIFEST`. Under the
operator law of 2026-08-14 ("old runs do not need to be valid or returnable
... what's important is that new versions are optimised for new functions")
those are recorded as out of scope, not diagnosed.

## The headline numbers

| quantity | value |
|---|---|
| roots with a `log.jsonl` | 107 |
| roots openable by the current reader (in scope) | 96 |
| roots recording ANY reach event, in scope | **0** |
| roots recording ANY `reach-provisional` event, anywhere in the corpus | **0** |
| candidate (artifact, foreign problem) pairs re-derived, in scope | 1 178 430 |
| ... rejected at `E1 no-criteria` | 285 070 |
| ... rejected at `E2 non-qualifying` | **0** |
| ... rejected at `E3 no-novel` | 308 264 |
| ... rejected at `E4 criterion-fail` | **585 096** (100% of everything reaching the verdict gate) |
| ... rejected at `E5 coverage` (provisional) | 0 |
| ... full hits | **0** |
| every `E4` first non-pass verdict | `fail` — never `overrun`, never an evaluator error |

The three columns sum exactly: 285 070 + 308 264 + 585 096 = 1 178 430.

Reach DID fire twice in the project's history, and both roots are out of
scope: `gemma4_dna_unattended_2026-07-12` (4 `reach_set` events, 24 `addr+`
pairs) and `gemma4_dna_unattended_3_2026-07-12` (2 and 11). Both predate the
Bronze Age postmortem discipline (`_STRUCTURAL_PROGRAMS`, `coverage_min`).
The only reach this project has ever recorded came from a version that had
no reach discipline.

## Per-root table

| root | opens | recorded reach events | recorded provisional | pairs | E1 no-criteria | E2 non-qualifying | E3 no-novel | E4 criterion-fail | E5 coverage/provisional | HIT full |
|---|---|---|---|---|---|---|---|---|---|---|
| experiments/2026-08-02-stress-triplet/home-orbit/runs/run-6472629dbc5d408a733d472040671752 | yes | 0 | 0 | 1680 | 1300 | 0 | 0 | 380 | 0 | 0 |
| experiments/2026-08-02-stress-triplet/home-triage/runs/run-0a3e93d6e8031e2e6d1d21dde2fa93cc | yes | 0 | 0 | 10292 | 7502 | 0 | 704 | 2086 | 0 | 0 |
| experiments/2026-08-02-stress-triplet/home-workshop/runs/run-1a0d4168a446f052bc7ccc9aa20b9829 | yes | 0 | 0 | 5049 | 3621 | 0 | 621 | 807 | 0 | 0 |
| experiments/2026-08-04-change-rung5-dumb-alternative-backend/ab-home/runs/run-9a6be78e1e79184a0bd89923b957586c | yes | 0 | 0 | 4165 | 3150 | 0 | 168 | 847 | 0 | 0 |
| experiments/2026-08-04-change-rung5-dumb-alternative-backend/rr-home/runs/run-9a6be78e1e79184a0bd89923b957586c | yes | 0 | 0 | 1170 | 414 | 0 | 492 | 264 | 0 | 0 |
| experiments/2026-08-05-testphase-live-validation/home-testphase/runs/run-a518e33a75507207633f864ba6a864b1 | yes | 0 | 0 | 1610 | 1196 | 0 | 85 | 329 | 0 | 0 |
| experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-0becdcfe2987fea4b74bc1c7e58e41ea | yes | 0 | 0 | 10208 | 7424 | 0 | 470 | 2314 | 0 | 0 |
| experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-0cdd57d1d8edc5328803a7bb5070a1d1 | yes | 0 | 0 | 4982 | 3498 | 0 | 729 | 755 | 0 | 0 |
| experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-167fe0eb4b373a0e27e87f0482ee5ce7 | yes | 0 | 0 | 4656 | 3312 | 0 | 594 | 750 | 0 | 0 |
| experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-18ca3170f2ff30d99e8255b48f47ab70 | yes | 0 | 0 | 7257 | 5133 | 0 | 805 | 1319 | 0 | 0 |
| experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-4056c2bce14e9eeabd35956c4fab1e4b | yes | 0 | 0 | 7398 | 5130 | 0 | 492 | 1776 | 0 | 0 |
| experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-4c08a14af6e9db79ddd67c253bfc8913 | yes | 0 | 0 | 21052 | 7372 | 0 | 6265 | 7415 | 0 | 0 |
| experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-8af8d02b35c6afad6c76604d39809008 | yes | 0 | 0 | 11224 | 6405 | 0 | 1404 | 3415 | 0 | 0 |
| experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-e3f4f7007c50fe7e09b301d31851c3e7 | yes | 0 | 0 | 7656 | 5568 | 0 | 840 | 1248 | 0 | 0 |
| experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-f7718a2254b048b88d50d56208ef0726 | yes | 0 | 0 | 6216 | 4592 | 0 | 784 | 840 | 0 | 0 |
| experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-fd071eaf7b1741b165a97a3529900a06 | yes | 0 | 0 | 17608 | 11147 | 0 | 990 | 5471 | 0 | 0 |
| experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/failed-epoch1-run-8c77c6588485304d1f73416318c62949 | yes | 0 | 0 | 8352 | 5278 | 0 | 260 | 2814 | 0 | 0 |
| experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/run-6995cd12124d2697030bb4b9e48f79bd | yes | 0 | 0 | 17381 | 11648 | 0 | 1736 | 3997 | 0 | 0 |
| experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/run-79900e7847544b09bfb266518e2d8484 | yes | 0 | 0 | 4784 | 3536 | 0 | 644 | 604 | 0 | 0 |
| experiments/2026-08-09-change-fix-p-cepp-1-dual-mode-wiring/live_run_v7 | yes | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| experiments/2026-08-09-change-hard-question-set/pilot-tier-o/runs/run-6bca5a31141b3f0ea6140501146f5646 | yes | 0 | 0 | 31920 | 7360 | 0 | 11628 | 12932 | 0 | 0 |
| experiments/2026-08-09-change-hard-question-set/pilot-tier-v/runs/run-7906485ce1cfc314a653c185cbf61d75 | yes | 0 | 0 | 9576 | 4503 | 0 | 1496 | 3577 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry/home-cross/runs/run-0321107a895b02654cb44044aa2cf68d | yes | 0 | 0 | 2945 | 1984 | 0 | 0 | 961 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry/home-cross/runs/run-050dd9ed53fdd1a30a0cec59f50d5baa | yes | 0 | 0 | 24494 | 6734 | 0 | 8365 | 9395 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry/home-cross/runs/run-341a3a3e618715f7023e822cdff510f2 | yes | 0 | 0 | 15580 | 10564 | 0 | 650 | 4366 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry/home-cross/runs/run-4faa222fd2fb014e56c7005107f84ad3 | yes | 0 | 0 | 11100 | 7500 | 0 | 1269 | 2331 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry/home-cross/runs/run-6927465d9ac5bfae2aa06dbb983aebea | yes | 0 | 0 | 12558 | 8418 | 0 | 531 | 3609 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry/home-cross/runs/run-6ffa0a9e06186d5e5d2bb19ad68d25d2 | yes | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry/home-cross/runs/run-944946f53dee4b636672677a0a534469 | yes | 0 | 0 | 12648 | 7548 | 0 | 962 | 4138 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry/home-cross/runs/run-a200f0c471f1225d9379d502e249976e | yes | 0 | 0 | 3201 | 2112 | 0 | 0 | 1089 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry/home-cross/runs/run-a529cbb6b02be078a09592449fadc502 | yes | 0 | 0 | 13800 | 8280 | 0 | 1106 | 4414 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry/home-cross/runs/run-b74e71aa434dd8b09a6451d23fd83c7a | yes | 0 | 0 | 16725 | 11850 | 0 | 640 | 4235 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry/home-cross/runs/run-b7514714c3310b6f805f466ff39915be | yes | 0 | 0 | 2552 | 1711 | 0 | 0 | 841 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry/home-cross/runs/run-bf30545893db661ec4d3c8da3a3f7f65 | yes | 0 | 0 | 14350 | 9922 | 0 | 1484 | 2944 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry/home-cross/runs/run-c52837bd8f673cea80c20db89758ea80 | yes | 0 | 0 | 23987 | 8715 | 0 | 5856 | 9416 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry/home-cross/runs/run-c6f6a743c5f6f2b49db7acf5edb8fb43 | yes | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry/home-cross/runs/run-d04b1ded7e35b8a2d6dc0336554f0e33 | yes | 0 | 0 | 3264 | 2240 | 0 | 0 | 1024 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry/home-cross/runs/run-ec7f3cdd63e1c39951be34d17e482e9a | yes | 0 | 0 | 10730 | 7104 | 0 | 1248 | 2378 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry/home-self/runs/run-0321107a895b02654cb44044aa2cf68d | yes | 0 | 0 | 420 | 320 | 0 | 0 | 100 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry/home-self/runs/run-4faa222fd2fb014e56c7005107f84ad3 | yes | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry/home-self/runs/run-6927465d9ac5bfae2aa06dbb983aebea | yes | 0 | 0 | 13281 | 9462 | 0 | 594 | 3225 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry/home-self/runs/run-6ffa0a9e06186d5e5d2bb19ad68d25d2 | yes | 0 | 0 | 2940 | 2220 | 0 | 138 | 582 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry/home-self/runs/run-944946f53dee4b636672677a0a534469 | yes | 0 | 0 | 5330 | 3895 | 0 | 204 | 1231 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry/home-self/runs/run-a200f0c471f1225d9379d502e249976e | yes | 0 | 0 | 1088 | 799 | 0 | 0 | 289 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry/home-self/runs/run-b74e71aa434dd8b09a6451d23fd83c7a | yes | 0 | 0 | 8736 | 6656 | 0 | 468 | 1612 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry/home-self/runs/run-b7514714c3310b6f805f466ff39915be | yes | 0 | 0 | 1156 | 867 | 0 | 0 | 289 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry/home-self/runs/run-c52837bd8f673cea80c20db89758ea80 | yes | 0 | 0 | 6594 | 5082 | 0 | 210 | 1302 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry/home-self/runs/run-c6f6a743c5f6f2b49db7acf5edb8fb43 | yes | 0 | 0 | 2116 | 1587 | 0 | 0 | 529 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry/home-self/runs/run-d04b1ded7e35b8a2d6dc0336554f0e33 | yes | 0 | 0 | 1105 | 816 | 0 | 0 | 289 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry/home-self/runs/run-ec7f3cdd63e1c39951be34d17e482e9a | yes | 0 | 0 | 13780 | 8905 | 0 | 1184 | 3691 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-b-capability-stochasticity/home-b/runs/run-168a41157d05ca53431f268fba264b4c | yes | 0 | 0 | 22 | 11 | 0 | 0 | 11 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-b-capability-stochasticity/home-b/runs/run-649323b4f264ac6b69fb87736d40fb27 | yes | 0 | 0 | 12 | 6 | 0 | 0 | 6 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-b-capability-stochasticity/home-b/runs/run-7f93a0955557fa490e1b1ead01ed459e | yes | 0 | 0 | 26 | 13 | 0 | 0 | 13 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-b-capability-stochasticity/home-b/runs/run-89d6f536c4daeee986e44a68042afded | yes | 0 | 0 | 16 | 8 | 0 | 0 | 8 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-b-capability-stochasticity/home-b/runs/run-97623b8fecfdf79fdace40e46cb7ac0c | yes | 0 | 0 | 18 | 9 | 0 | 0 | 9 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-b-capability-stochasticity/home-b/runs/run-a277abb13327846e13fb3124c1804aa8 | yes | 0 | 0 | 32 | 16 | 0 | 0 | 16 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-b-capability-stochasticity/home-b/runs/run-b212590cf2957821796b560163e1941e | yes | 0 | 0 | 28 | 14 | 0 | 0 | 14 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-b-capability-stochasticity/home-b/runs/run-d63e92d295084b9d303eec6f76e1a34e | yes | 0 | 0 | 10 | 5 | 0 | 0 | 5 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-b-capability-stochasticity/home-b/runs/run-db8194b08518dd3afc2b78c533170ab3 | yes | 0 | 0 | 16 | 8 | 0 | 0 | 8 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-b-capability-stochasticity/home-b/runs/run-ecf3ce54012a3df4eef08d0cdb772f41 | yes | 0 | 0 | 34 | 17 | 0 | 0 | 17 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-c-completion-cap-curve/home-16384/runs/run-6ffa0a9e06186d5e5d2bb19ad68d25d2 | yes | 0 | 0 | 1224 | 900 | 0 | 0 | 324 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-c-completion-cap-curve/home-16384/runs/run-c6f6a743c5f6f2b49db7acf5edb8fb43 | yes | 0 | 0 | 2772 | 2100 | 0 | 92 | 580 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-c-completion-cap-curve/home-4096/runs/run-370ab72342ecd4a23ebaf983d0828598 | yes | 0 | 0 | 2254 | 1725 | 0 | 0 | 529 | 0 | 0 |
| experiments/2026-08-09-overnight-omnibus/block-c-completion-cap-curve/home-4096/runs/run-f5aee6107cb0de151e72bf282c86d166 | yes | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| experiments/2026-08-12-live-grounded-extension-expansion/run | yes | 0 | 0 | 708785 | 4497 | 0 | 250038 | 454250 | 0 | 0 |
| experiments/2026-08-13-defect-controller-steering-inert/failed-epoch1-run-8e22d0431fd2b98d | yes | 0 | 0 | 84 | 12 | 0 | 0 | 72 | 0 | 0 |
| experiments/2026-08-13-defect-controller-steering-inert/failed-epoch2-run-8e22d0431fd2b98d | yes | 0 | 0 | 84 | 12 | 0 | 0 | 72 | 0 | 0 |
| experiments/2026-08-13-defect-controller-steering-inert/failed-epoch3-run-8e22d0431fd2b98d | yes | 0 | 0 | 84 | 12 | 0 | 0 | 72 | 0 | 0 |
| experiments/bronze_flat_2026-07-13/deepseek-v4-pro | yes | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| experiments/bronze_flat_2026-07-13/kimi-k2_6 | yes | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| experiments/bronze_flat_2026-07-13/qwen3_5_397b | yes | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| experiments/live_coin_canonicity_2026-07-31/home/runs/run-c5f901f38208e862f4ce2fe60a26e551 | yes | 0 | 0 | 574 | 406 | 0 | 0 | 168 | 0 | 0 |
| experiments/live_compare_2026-07-28/deepseek/shallow-runs/shallow-dc6fe3f9c26cede686906a16 | yes | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| experiments/live_engaged_2026-07-27/run-f4fa6663e5412d64df943a5a22342baf | yes | 0 | 0 | 4935 | 3850 | 0 | 150 | 935 | 0 | 0 |
| experiments/live_research_2026-07-29/narrow/runs/run-7d8723fbe8626c71db880826c244d332 | yes | 0 | 0 | 6435 | 3465 | 0 | 780 | 2190 | 0 | 0 |
| experiments/live_research_2026-07-29/openchallenge/runs/completed-epoch2-run-9e9812feefa792179d490db7734825b5 | yes | 0 | 0 | 1536 | 1056 | 0 | 0 | 480 | 0 | 0 |
| experiments/live_research_2026-07-29/openchallenge/runs/completed-epoch3-run-9e9812feefa792179d490db7734825b5 | yes | 0 | 0 | 280 | 200 | 0 | 0 | 80 | 0 | 0 |
| experiments/live_research_2026-07-29/openchallenge/runs/failed-epoch1-run-0d1f88e18779b7eb6d8c5d6af3473ba7 | yes | 0 | 0 | 30 | 10 | 0 | 0 | 20 | 0 | 0 |
| experiments/live_research_2026-07-29/openchallenge/runs/run-27b80f26bd398c718360e97e2a403593 | yes | 0 | 0 | 1380 | 1040 | 0 | 0 | 340 | 0 | 0 |
| experiments/live_research_2026-07-29/openchallenge/runs/run-9e9812feefa792179d490db7734825b5 | yes | 0 | 0 | 290 | 210 | 0 | 0 | 80 | 0 | 0 |
| experiments/live_research_2026-07-29/referee/runs/run-d17935a4bf5ffa67c7f6e67b9a637a00 | yes | 0 | 0 | 2225 | 1675 | 0 | 0 | 550 | 0 | 0 |
| experiments/live_research_2026-07-29/referee/runs/run-e542c3c1fc266943e0260c5aa8d7c107 | yes | 0 | 0 | 440 | 330 | 0 | 0 | 110 | 0 | 0 |
| experiments/live_research_2026-07-29/referee/runs/run-e6c07aec698426a9b21d01399ba6b5b0 | yes | 0 | 0 | 672 | 512 | 0 | 54 | 106 | 0 | 0 |
| experiments/live_research_2026-07-29/selfstudy/runs/completed-epoch3-run-9175f0ecb055e57455af3c50df153c5a | yes | 0 | 0 | 406 | 116 | 0 | 192 | 98 | 0 | 0 |
| experiments/live_research_2026-07-29/selfstudy/runs/failed-epoch1-run-9175f0ecb055e57455af3c50df153c5a | yes | 0 | 0 | 1326 | 897 | 0 | 230 | 199 | 0 | 0 |
| experiments/live_research_2026-07-29/selfstudy/runs/failed-epoch2-run-9175f0ecb055e57455af3c50df153c5a | yes | 0 | 0 | 238 | 68 | 0 | 96 | 74 | 0 | 0 |
| experiments/live_research_2026-07-29/selfstudy/runs/failed-epoch4-run-9175f0ecb055e57455af3c50df153c5a | yes | 0 | 0 | 132 | 22 | 0 | 48 | 62 | 0 | 0 |
| experiments/live_research_2026-07-29/selfstudy/runs/run-9175f0ecb055e57455af3c50df153c5a | yes | 0 | 0 | 1166 | 792 | 0 | 0 | 374 | 0 | 0 |
| experiments/live_research_2026-07-29/wide/runs/run-0c3ce902cc5bca75a709b04e2473d100 | yes | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| experiments/live_research_2026-07-29/wide/runs/run-5a771259557378224bd68591483817be | yes | 0 | 0 | 330 | 230 | 0 | 0 | 100 | 0 | 0 |
| experiments/live_tri_2026-07-27/run-15a53aca8a6fc66a39f382fc688c5346 | yes | 0 | 0 | 5160 | 3800 | 0 | 198 | 1162 | 0 | 0 |
| experiments/live_tri_2026-07-27/run-6dab80d615a437a8b3fa489a279df847 | yes | 0 | 0 | 3120 | 2544 | 0 | 0 | 576 | 0 | 0 |
| experiments/live_tri_2026-07-27/run-9ae94bb478990cbecca373fc3bcb1345 | yes | 0 | 0 | 672 | 528 | 0 | 0 | 144 | 0 | 0 |
| experiments/live_tri_2026-07-27/run-ac1836b6237b6e9d80b3b0cb492b39f5 | yes | 0 | 0 | 9152 | 6760 | 0 | 270 | 2122 | 0 | 0 |
| experiments/live_tri_2026-07-27/run-c5ab654afd1b4aa131aede83bdca0f03 | yes | 0 | 0 | 1386 | 1062 | 0 | 0 | 324 | 0 | 0 |
| experiments/live_tri_2026-07-27/run-faa5feae126bc2558ea9c6d8d200a90c | yes | 0 | 0 | 2328 | 1752 | 0 | 0 | 576 | 0 | 0 |
| **TOTAL (96 openable roots)** | | **0** | **0** | **1178430** | **285070** | **0** | **308264** | **585096** | **0** | **0** |

## Out of scope (11 roots — the reader refuses them, by law, not by defect)

| root | reader error | recorded reach events | recorded addr pairs |
|---|---|---|---|
| experiments/bronze_feedback_v1_superseded_2026-07-14/observe_only | `UnsupportedRunManifestVersionError` | 0 | 0 |
| experiments/bronze_feedback_v1_superseded_2026-07-14/trial_required | `UnsupportedRunManifestVersionError` | 0 | 0 |
| experiments/bronze_pilot_2026-07-14 | `UnsupportedRunManifestVersionError` | 0 | 0 |
| experiments/bronze_repertoire_v2_2026-07-14/deepseek-v4-pro | `UnsupportedRunManifestVersionError` | 0 | 0 |
| experiments/bronze_repertoire_v2_2026-07-14/gpt-oss_120b | `UnsupportedRunManifestVersionError` | 0 | 0 |
| experiments/bronze_repertoire_v2_2026-07-14/kimi-k2_6 | `UnsupportedRunManifestVersionError` | 0 | 0 |
| experiments/bronze_repertoire_v2_2026-07-14/qwen3_5_397b | `UnsupportedRunManifestVersionError` | 0 | 0 |
| experiments/gemma4_dna_unattended_2026-07-12 | `UnsupportedRunManifestVersionError` | 4 | 24 |
| experiments/gemma4_dna_unattended_3_2026-07-12 | `UnsupportedRunManifestVersionError` | 2 | 11 |
| experiments/glm_judge_2026-07-14 | `UnsupportedRunManifestVersionError` | 0 | 0 |
| experiments/jolt_architecture_2026-07-16/run | `UnsupportedRunManifestVersionError` | 0 | 0 |

## The qualifying vocabulary — the whole corpus has two criteria

A criterion QUALIFIES (can carry reach) iff it is registered, evaluable, and
not a `program:` in `_STRUCTURAL_PROGRAMS`. Over the 96 in-scope roots there
are exactly **two distinct qualifying criteria**, and both are FORM gates:

| gate pairs | roots | criterion | eval |
|---|---|---|---|
| 584 303 | 86 | `relation-form@578e42df713e` | `predicate:'refuted if' in content.lower() and any(k in content.lower() for k in ('depends on', 'reduces to', 'shares mechanism', ...))` |
| 793 | 46 | `reasoning-envelope-wf` | `program:reasoning-envelope-wf` |

`relation_form_commitment()` (`unification/isolation.py:43`) calls itself, in
its own docstring, a "Form gate for RELATION candidates". Its expression is a
CONSTANT, so its content-addressed id is a **singleton**: every connection and
every integration problem, in every run, carries the same commitment id.
`reasoning-envelope-wf` is declared `class_="structural"` in
`programs.PROGRAMS` (see P1 below).

Nothing in the corpus's criterion vocabulary asks a question about a
problem's SUBJECT. Full census of criterion occurrences over all problems:

| occurrences | kind |
|---|---|
| 6 107 | substantive-predicate (all `relation-form`) |
| 2 284 | `structural:lineage_ref` |
| 2 284 | `unknown-program:hv_floor` (deliberately unregistered — `programs.py`) |
| 90 | `substantive-program:reasoning-envelope-wf` |
| 16 | `rubric` |
| 16 | `structural:skeleton_wf` |

Zero exec-oracle, property-oracle, dataset-oracle or subject-predicate
criteria appear on any problem in any in-scope root.

## Coverage is NOT the binding constraint

At the verdict gate, coverage (qualifying / total criteria) is bimodal:

| coverage | gate pairs | consequence |
|---|---|---|
| 0.33 | 97 184 | connection problems (`hv_floor` + `lineage_ref` + `relation-form`) — below `REACH_COVERAGE_MIN` 0.5, so capped at provisional even on a pass |
| 1.00 | 487 912 | integration and reasoning-envelope problems — coverage would allow a full hit |

**83% of gate pairs would clear the coverage threshold.** Lowering
`REACH_COVERAGE_MIN` would change nothing: `E5` rejected 0 pairs because no
pair ever reached it.

## Why every gate pair fails: novelty and survival are mutually exclusive here

`reach_sweep` demands, of the same criterion set, that at least one qualifying
criterion be NOVEL to the artifact's own battery AND that every qualifying
criterion PASS. The 2x2 over every candidate artifact in the corpus
(`probe_novelty.py`):

| criterion | carries=F passes=F | carries=F **passes=T** | carries=T passes=F | carries=T passes=T | not registered in root |
|---|---|---|---|---|---|
| `relation-form@578e42df713e` | 2 534 | **0** | 0 | 880 | 114 |
| `reasoning-envelope-wf` | 861 | **0** | 79 | 2 296 | 292 |

The only cell that can produce a reach hit — *does not carry it, yet passes
it* — is **empty for both criteria, across 96 roots**. Carrying
`relation-form` is, in this corpus, exactly equivalent to passing it: the
conjecturer is told by the connection/integration spawn prompt to "state what
it is REFUTED IF" and to name a relation kind, so precisely the artifacts
built against the gate satisfy it, and because the gate is a singleton it is
never novel to them.

## Control: the failures are content-level, not a missing-blob artifact

`SUB-evaluation.md` Traps: "A missing blob evaluates as the empty string, not
as an error ... a predicate over a sealed or absent artifact yields a
confident `fail`." If artifact bytes were unresolvable on replay, the 585 096
`fail` verdicts would be an artifact of the reader. They are not
(`probe_content.py`):

| quantity | value |
|---|---|
| candidate artifacts | 3 528 |
| with NON-EMPTY resolvable content | **3 528** (100%) |
| shortest resolvable content | 402 characters |
| containing `refuted if` | 880 |
| containing a relation keyword | 1 139 |
| that WOULD pass `relation-form` | 880 — and all 880 already carry it |

## Control: the real `reach_sweep` agrees with the re-derivation

The census re-implements the decision tree. `reach_sweep` itself writes when
it finds something, and a committed root must never be written to, so the
real function was run against COPIES of four roots in a scratch directory
(`verify_sweep_equivalence.py`):

| root | `reach_sweep` returned | log lines before → after |
|---|---|---|
| `2026-08-13-defect-controller-steering-inert/failed-epoch3-run-8e22d0431fd2b98d` | `[]` | 114 → 114 |
| `live_research_2026-07-29/selfstudy/runs/completed-epoch3-run-9175f0ecb055e57455af3c50df153c5a` | `[]` | 754 → 754 |
| `live_tri_2026-07-27/run-ac1836b6237b6e9d80b3b0cb492b39f5` | `[]` | 1202 → 1202 |
| `2026-08-12-live-grounded-extension-expansion/run` | `[]` | 12991 → 12991 |

Zero hits, zero appended events — so also zero provisional. The re-derivation
and the shipped function agree.

## The sweep is invoked; absence of events is not absence of calls

`reach_sweep` is called on every cycle of the main path
(`scheduler/scheduler.py:2274`) and again on the discrimination path
(`:2024`), both with `coverage_min=config.REACH_COVERAGE_MIN` (0.5,
`config.py:353`). It records nothing when nothing changes, so an empty log is
consistent with "called and found nothing" — which the re-derivation and the
copy-run above independently confirm is what happened.
