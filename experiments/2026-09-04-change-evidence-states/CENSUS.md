# Census — how much of the committed record ever survived anything

R13 of `REQUEST.md` says this number is the point, so it is committed as a
re-derivable table rather than quoted from a session:

    python experiments/2026-09-04-change-evidence-states/census.py

The script runs the SHIPPED reader (`deepreason.views.evidence_states`) over
every git-tracked run root, opened read-only. It is not a second implementation
of the reading; a second implementation would be a second answer to the same
question, and the record would then have two numbers and no way to choose.

## The headline

Across **77 committed run roots** holding **8 683** admitted artifacts:

| reading | artifacts | share |
|---|---|---|
| nothing has been brought against it yet (OPEN) | **7 713** | 88.8% |
| it came through an attack, or a trial that ruled (SUPPORTED) | **47** | 0.5% |
| it fell (REFUTED) | 844 | 9.7% |
| the evidence points both ways (CONTESTED) | 79 | 0.9% |

And on the FRONTIER — the set a reader of `deepreason results` actually looks
at, the published open edge of each inquiry — **941 artifacts**:

| reading | artifacts | share |
|---|---|---|
| OPEN | **939** | 99.8% |
| SUPPORTED | **1** | 0.1% |
| REFUTED | 0 | 0.0% |
| CONTESTED | 1 | 0.1% |

**Not one of the 77 roots carries a criticism-dispatch declaration**, because
every one of them predates it. So none of those 939 is OPEN because a pass ran
in full and found nothing: they are OPEN because the record cannot say whether
anything ever looked.

## What this does and does not mean

It does NOT mean the harness produced nothing. 844 artifacts were refuted —
error elimination happened, and it is visible. What it means is narrower and
sharper: **on the published frontier, the record cannot show that anything
survived criticism.** Under the old reading all 941 of those artifacts read as
`accepted` alike.

It also does not mean the 939 failed. OPEN is a statement about the RECORD, not
about the conjecture: nothing warranted has been brought against it, and no
trial ruled on it. Some of them may be excellent. The point is that the record
does not say so, and until this tranche it looked as though it did.

Two consequences for the progress law, which asks whether a run's output is
materially better than the same model without the harness:

1. A comparison against a no-harness baseline that counts "accepted artifacts"
   was comparing generated candidates, not survivors. `--survivors-only` on
   both instruments now restricts the comparison to the 47.
2. The declaration is what changes the denominator going forward. A run whose
   criticism passes declare themselves complete will report survivors that
   mean something; these 77 cannot, and no amount of re-reading them will
   change that.

## The full table

# Evidence-state census over 77 committed run roots

| root | open | supported | refuted | contested | frontier o/s/r/c |
|---|---|---|---|---|---|
| `experiments/2026-08-02-stress-triplet/home-orbit/runs/run-6472629dbc5d408a733d472040671752` | 39 | 0 | 0 | 0 | 8/0/0/0 |
| `experiments/2026-08-02-stress-triplet/home-triage/runs/run-0a3e93d6e8031e2e6d1d21dde2fa93cc` | 110 | 0 | 1 | 0 | 16/0/0/0 |
| `experiments/2026-08-02-stress-triplet/home-workshop/runs/run-1a0d4168a446f052bc7ccc9aa20b9829` | 100 | 0 | 0 | 0 | 23/0/0/0 |
| `experiments/2026-08-04-change-rung5-dumb-alternative-backend/ab-home/runs/run-9a6be78e1e79184a0bd89923b957586c` | 71 | 0 | 0 | 0 | 6/0/0/0 |
| `experiments/2026-08-04-change-rung5-dumb-alternative-backend/rr-home/runs/run-9a6be78e1e79184a0bd89923b957586c` | 38 | 0 | 0 | 0 | 12/0/0/0 |
| `experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-0becdcfe2987fea4b74bc1c7e58e41ea` | 99 | 0 | 1 | 0 | 10/0/0/0 |
| `experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-0cdd57d1d8edc5328803a7bb5070a1d1` | 95 | 0 | 2 | 0 | 27/0/0/0 |
| `experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-167fe0eb4b373a0e27e87f0482ee5ce7` | 83 | 0 | 2 | 0 | 22/0/0/0 |
| `experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-18ca3170f2ff30d99e8255b48f47ab70` | 91 | 0 | 0 | 0 | 23/0/0/0 |
| `experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-4056c2bce14e9eeabd35956c4fab1e4b` | 95 | 0 | 0 | 0 | 12/0/0/0 |
| `experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-4c08a14af6e9db79ddd67c253bfc8913` | 115 | 0 | 1 | 0 | 35/0/0/0 |
| `experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-8af8d02b35c6afad6c76604d39809008` | 100 | 0 | 0 | 0 | 18/0/0/0 |
| `experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-e3f4f7007c50fe7e09b301d31851c3e7` | 110 | 0 | 3 | 0 | 24/0/0/0 |
| `experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-f7718a2254b048b88d50d56208ef0726` | 93 | 0 | 1 | 0 | 28/0/0/0 |
| `experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-fd071eaf7b1741b165a97a3529900a06` | 93 | 0 | 1 | 0 | 11/0/0/0 |
| `experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/failed-epoch1-run-8c77c6588485304d1f73416318c62949` | 95 | 0 | 0 | 0 | 0/0/0/0 |
| `experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/run-6995cd12124d2697030bb4b9e48f79bd` | 177 | 0 | 0 | 0 | 28/0/0/0 |
| `experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/run-79900e7847544b09bfb266518e2d8484` | 102 | 0 | 0 | 0 | 28/0/0/0 |
| `experiments/2026-08-09-change-fix-p-cepp-1-dual-mode-wiring/live_run_v7` | 27 | 0 | 0 | 0 | 0/0/0/0 |
| `experiments/2026-08-12-live-grounded-extension-expansion/run` | 171 | 37 | 16 | 62 | 87/0/0/0 |
| `experiments/2026-08-13-defect-controller-steering-inert/failed-epoch1-run-8e22d0431fd2b98d` | 4 | 0 | 0 | 0 | 0/0/0/0 |
| `experiments/2026-08-13-defect-controller-steering-inert/failed-epoch2-run-8e22d0431fd2b98d` | 4 | 0 | 0 | 0 | 0/0/0/0 |
| `experiments/2026-08-13-defect-controller-steering-inert/failed-epoch3-run-8e22d0431fd2b98d` | 4 | 0 | 0 | 0 | 0/0/0/0 |
| `experiments/2026-08-22-change-epoch3-second-lineage/failed-attempt2-run-bb0455384ea09b5b72664a4f6f3f0cb7a5ac227c00a93976e5c8c31873ca84f4` | 56 | 0 | 3 | 0 | 0/0/0/0 |
| `experiments/2026-08-22-change-epoch3-second-lineage/failed-attempt3-run-bb0455384ea09b5b72664a4f6f3f0cb7a5ac227c00a93976e5c8c31873ca84f4` | 55 | 0 | 2 | 0 | 0/0/0/0 |
| `experiments/2026-08-22-change-epoch3-second-lineage/run` | 190 | 0 | 26 | 0 | 1/0/0/0 |
| `experiments/2026-08-22-live-reach-rich-run/failed-epoch1-run-40e713b30a147dfc1a0f73feb91fa67a493454f6103a452888b8e08713368c4c` | 46 | 0 | 4 | 0 | 0/0/0/0 |
| `experiments/2026-08-22-live-reach-rich-run/run` | 59 | 0 | 1 | 0 | 0/0/0/0 |
| `experiments/2026-08-24-change-rung7-wounds-falls-succession/run` | 58 | 0 | 8 | 0 | 0/0/0/0 |
| `experiments/2026-08-25-change-constructive-frontier/run` | 913 | 0 | 163 | 0 | 0/0/0/0 |
| `experiments/2026-08-25-change-constructive-frontier/void-inert-battery-run-6913328037a61ca6` | 1295 | 0 | 214 | 0 | 0/0/0/0 |
| `experiments/2026-08-25-poietics-program/run` | 399 | 0 | 104 | 0 | 40/0/0/0 |
| `experiments/2026-08-26-pc2-rematch/retired-transport-timeout180-run-42ad288038dd606c` | 4 | 0 | 0 | 0 | 0/0/0/0 |
| `experiments/2026-08-26-pc2-rematch/retired-truncation-cap32768-run-58fb0d20488be869` | 16 | 0 | 2 | 0 | 0/0/0/0 |
| `experiments/2026-08-26-pc2-rematch/run` | 847 | 0 | 220 | 0 | 0/0/0/0 |
| `experiments/2026-08-26-pc2-rematch/run_h3` | 4 | 0 | 0 | 0 | 0/0/0/0 |
| `experiments/2026-08-27-pc2b-symmetric-reasoning/run` | 25 | 0 | 4 | 0 | 0/0/0/0 |
| `experiments/2026-09-01-live-all-modules-p-a1/run` | 27 | 0 | 4 | 2 | 0/0/0/0 |
| `experiments/2026-09-02-live-p-a2-corrected/failed-epoch3-run-1b89ed64e050c354` | 11 | 2 | 3 | 4 | 0/0/0/0 |
| `experiments/2026-09-02-live-p-a2-corrected/run` | 63 | 8 | 12 | 11 | 27/1/0/1 |
| `experiments/2026-09-03-change-provenance-history-channel/runs/home-default/runs/failed-429-run-fe00609058e10605590206d51ab2b7a0` | 86 | 0 | 4 | 0 | 0/0/0/0 |
| `experiments/2026-09-03-change-provenance-history-channel/runs/home-default/runs/retired-1cycle-run-292f964edb58e58ef0e7d957f29bac55` | 40 | 0 | 0 | 0 | 18/0/0/0 |
| `experiments/2026-09-03-change-provenance-history-channel/runs/home-default/runs/run-fe00609058e10605590206d51ab2b7a0` | 146 | 0 | 6 | 0 | 65/0/0/0 |
| `experiments/2026-09-03-change-provenance-history-channel/runs/home-h1/runs/retired-noinject-run-fe00609058e10605590206d51ab2b7a0` | 13 | 0 | 0 | 0 | 0/0/0/0 |
| `experiments/2026-09-03-change-provenance-history-channel/runs/home-h1/runs/retired-probe-contaminated-run-fe00609058e10605590206d51ab2b7a0` | 4 | 0 | 0 | 0 | 0/0/0/0 |
| `experiments/2026-09-03-change-provenance-history-channel/runs/home-m1/runs/run-ad41064484366337ed61a9d5a58de58f` | 129 | 0 | 7 | 0 | 60/0/0/0 |
| `experiments/2026-09-03-change-provenance-history-channel/runs/home-m1/runs/run-f23da86ddfd5ab820957221cfebe4b2e` | 95 | 0 | 0 | 0 | 47/0/0/0 |
| `experiments/2026-09-03-change-provenance-history-channel/runs/home-m3/runs/run-5565bd1ef7011e3d25fef3197bdf1cdb` | 106 | 0 | 3 | 0 | 46/0/0/0 |
| `experiments/2026-09-03-change-provenance-history-channel/runs/home-m3/runs/run-7a8fc89b33f8e055a212fafa09acd83f` | 90 | 0 | 1 | 0 | 44/0/0/0 |
| `experiments/2026-09-04-fix-provider-reasoning-contract/relaunch-home/runs/run-ecd1a8d2461eff1eddd9756b51336ce5` | 41 | 0 | 0 | 0 | 0/0/0/0 |
| `experiments/bronze_flat_2026-07-13/deepseek-v4-pro` | 23 | 0 | 11 | 0 | 0/0/0/0 |
| `experiments/bronze_flat_2026-07-13/kimi-k2_6` | 11 | 0 | 4 | 0 | 0/0/0/0 |
| `experiments/bronze_flat_2026-07-13/qwen3_5_397b` | 17 | 0 | 8 | 0 | 0/0/0/0 |
| `experiments/live_compare_2026-07-28/deepseek/shallow-runs/shallow-dc6fe3f9c26cede686906a16` | 27 | 0 | 1 | 0 | 0/0/0/0 |
| `experiments/live_engaged_2026-07-27/run-f4fa6663e5412d64df943a5a22342baf` | 68 | 0 | 1 | 0 | 5/0/0/0 |
| `experiments/live_research_2026-07-29/narrow/runs/run-7d8723fbe8626c71db880826c244d332` | 64 | 0 | 0 | 0 | 12/0/0/0 |
| `experiments/live_research_2026-07-29/openchallenge/runs/completed-epoch2-run-9e9812feefa792179d490db7734825b5` | 36 | 0 | 0 | 0 | 1/0/0/0 |
| `experiments/live_research_2026-07-29/openchallenge/runs/completed-epoch3-run-9e9812feefa792179d490db7734825b5` | 16 | 0 | 0 | 0 | 5/0/0/0 |
| `experiments/live_research_2026-07-29/openchallenge/runs/failed-epoch1-run-0d1f88e18779b7eb6d8c5d6af3473ba7` | 16 | 0 | 0 | 0 | 0/0/0/0 |
| `experiments/live_research_2026-07-29/openchallenge/runs/run-27b80f26bd398c718360e97e2a403593` | 34 | 0 | 0 | 0 | 4/0/0/0 |
| `experiments/live_research_2026-07-29/openchallenge/runs/run-9e9812feefa792179d490db7734825b5` | 16 | 0 | 0 | 0 | 1/0/0/0 |
| `experiments/live_research_2026-07-29/referee/runs/run-d17935a4bf5ffa67c7f6e67b9a637a00` | 41 | 0 | 0 | 0 | 22/0/0/0 |
| `experiments/live_research_2026-07-29/referee/runs/run-e542c3c1fc266943e0260c5aa8d7c107` | 18 | 0 | 0 | 0 | 0/0/0/0 |
| `experiments/live_research_2026-07-29/referee/runs/run-e6c07aec698426a9b21d01399ba6b5b0` | 32 | 0 | 0 | 0 | 6/0/0/0 |
| `experiments/live_research_2026-07-29/selfstudy/runs/completed-epoch3-run-9175f0ecb055e57455af3c50df153c5a` | 64 | 0 | 0 | 0 | 48/0/0/0 |
| `experiments/live_research_2026-07-29/selfstudy/runs/failed-epoch1-run-9175f0ecb055e57455af3c50df153c5a` | 44 | 0 | 0 | 0 | 0/0/0/0 |
| `experiments/live_research_2026-07-29/selfstudy/runs/failed-epoch2-run-9175f0ecb055e57455af3c50df153c5a` | 38 | 0 | 0 | 0 | 0/0/0/0 |
| `experiments/live_research_2026-07-29/selfstudy/runs/failed-epoch4-run-9175f0ecb055e57455af3c50df153c5a` | 19 | 0 | 0 | 0 | 0/0/0/0 |
| `experiments/live_research_2026-07-29/selfstudy/runs/run-9175f0ecb055e57455af3c50df153c5a` | 28 | 0 | 0 | 0 | 2/0/0/0 |
| `experiments/live_research_2026-07-29/wide/runs/run-0c3ce902cc5bca75a709b04e2473d100` | 28 | 0 | 0 | 0 | 0/0/0/0 |
| `experiments/live_research_2026-07-29/wide/runs/run-5a771259557378224bd68591483817be` | 20 | 0 | 0 | 0 | 8/0/0/0 |
| `experiments/live_tri_2026-07-27/run-15a53aca8a6fc66a39f382fc688c5346` | 73 | 0 | 0 | 0 | 6/0/0/0 |
| `experiments/live_tri_2026-07-27/run-6dab80d615a437a8b3fa489a279df847` | 39 | 0 | 0 | 0 | 1/0/0/0 |
| `experiments/live_tri_2026-07-27/run-9ae94bb478990cbecca373fc3bcb1345` | 27 | 0 | 0 | 0 | 8/0/0/0 |
| `experiments/live_tri_2026-07-27/run-ac1836b6237b6e9d80b3b0cb492b39f5` | 96 | 0 | 0 | 0 | 6/0/0/0 |
| `experiments/live_tri_2026-07-27/run-c5ab654afd1b4aa131aede83bdca0f03` | 37 | 0 | 0 | 0 | 14/0/0/0 |
| `experiments/live_tri_2026-07-27/run-faa5feae126bc2558ea9c6d8d200a90c` | 47 | 0 | 0 | 0 | 24/0/0/0 |

## Totals

- admitted artifacts read: **8683**
  - open: **7713** (88.8%)
  - supported: **47** (0.5%)
  - refuted: **844** (9.7%)
  - contested: **79** (0.9%)
- frontier artifacts read: **941**
  - open: **939** (99.8%)
  - supported: **1** (0.1%)
  - refuted: **0** (0.0%)
  - contested: **1** (0.1%)
- roots carrying a criticism-dispatch declaration: **0** of 77

## Roots the replay reader could not rebuild

- `experiments/bronze_pilot_2026-07-14: UnsupportedRunManifestVersionError: UNSUPPORTED_RUN_MANIFEST_VERSION at /schema_version: RunManifest schema version 2 is unsupported; only schema version 6 is accepted`
- `experiments/gemma4_dna_unattended_2026-07-12: UnsupportedRunManifestVersionError: UNSUPPORTED_RUN_MANIFEST_VERSION at /schema_version: RunManifest schema version 1 is unsupported; only schema version 6 is accepted`
- `experiments/gemma4_dna_unattended_3_2026-07-12: UnsupportedRunManifestVersionError: UNSUPPORTED_RUN_MANIFEST_VERSION at /schema_version: RunManifest schema version 1 is unsupported; only schema version 6 is accepted`
- `experiments/glm_judge_2026-07-14: UnsupportedRunManifestVersionError: UNSUPPORTED_RUN_MANIFEST_VERSION at /schema_version: RunManifest schema version 2 is unsupported; only schema version 6 is accepted`
- `experiments/jolt_architecture_2026-07-16/run: UnsupportedRunManifestVersionError: UNSUPPORTED_RUN_MANIFEST_VERSION at /schema_version: RunManifest schema version 3 is unsupported; only schema version 6 is accepted`
- `runs/jolt_positive_headroom_v3_1/calibration/20260701: UnsupportedRunManifestVersionError: UNSUPPORTED_RUN_MANIFEST_VERSION at /schema_version: RunManifest schema version 2 is unsupported; only schema version 6 is accepted`
- `runs/jolt_positive_headroom_v3_1/calibration/20260702: UnsupportedRunManifestVersionError: UNSUPPORTED_RUN_MANIFEST_VERSION at /schema_version: RunManifest schema version 2 is unsupported; only schema version 6 is accepted`
- `runs/jolt_positive_headroom_v3_1/calibration/20260703: UnsupportedRunManifestVersionError: UNSUPPORTED_RUN_MANIFEST_VERSION at /schema_version: RunManifest schema version 2 is unsupported; only schema version 6 is accepted`
