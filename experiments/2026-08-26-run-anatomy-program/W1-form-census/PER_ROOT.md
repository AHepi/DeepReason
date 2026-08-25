# Per-root form census

Machine-readable source: `CENSUS_PER_ROOT.json` and `census/<root>.json`.
Re-derive with `python3 census.py && python3 aggregate.py`.

`valid` counts attempts VALID ON ARRIVAL — the contract accepted the
response as written, with no repair. `2nd+` counts attempts at workflow
attempt index 1 or higher, i.e. calls the seat spent because an earlier
call on the same work was not accepted. `cycle join` is `exact` only
where the run recorded at least one completed cycle; where it is
`none`, per-cycle numbers for that root must not be quoted.

| root | run id | state / stop | attempts | valid | rate | 2nd+ | repair-scoped | trunc | cycle join |
|---|---|---|---|---|---|---|---|---|---|
| `experiments/2026-08-02-stress-triplet/home-orbit/runs/run-6472629dbc5d408a733d472040671752` | `4e9897f86aeeab8b` | completed / budget_exhausted | 45 | 28 | 0.6222 | 14 | 4 | 0 | exact |
| `experiments/2026-08-02-stress-triplet/home-triage/runs/run-0a3e93d6e8031e2e6d1d21dde2fa93cc` | `2e8904aa31694454` | completed / budget_exhausted | 42 | 38 | 0.9048 | 4 | 0 | 0 | exact |
| `experiments/2026-08-02-stress-triplet/home-workshop/runs/run-1a0d4168a446f052bc7ccc9aa20b9829` | `7098a900b2b194c9` | completed / budget_exhausted | 52 | 43 | 0.8269 | 8 | 1 | 0 | exact |
| `experiments/2026-08-04-change-rung5-dumb-alternative-backend/ab-home/runs/run-9a6be78e1e79184a0bd89923b957586c` | `64cc945753f3a9a9` | completed / budget_exhausted | 31 | 27 | 0.871 | 4 | 0 | 0 | exact |
| `experiments/2026-08-04-change-rung5-dumb-alternative-backend/rr-home/runs/run-9a6be78e1e79184a0bd89923b957586c` | `c87d5802b5f51583` | completed / budget_exhausted | 24 | 18 | 0.75 | 5 | 1 | 0 | exact |
| `experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-0becdcfe2987fea4b74bc1c7e58e41ea` | `a45501493e81871b` | completed / budget_exhausted | 59 | 49 | 0.8305 | 11 | 2 | 0 | exact |
| `experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-0cdd57d1d8edc5328803a7bb5070a1d1` | `c2dcb87e33616c32` | completed / budget_exhausted | 63 | 50 | 0.7937 | 15 | 1 | 0 | exact |
| `experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-167fe0eb4b373a0e27e87f0482ee5ce7` | `c336e3e2ad956c35` | completed / budget_exhausted | 55 | 48 | 0.8727 | 8 | 0 | 0 | exact |
| `experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-18ca3170f2ff30d99e8255b48f47ab70` | `6e193328f7c2d559` | completed / budget_exhausted | 48 | 45 | 0.9375 | 4 | 0 | 0 | exact |
| `experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-4056c2bce14e9eeabd35956c4fab1e4b` | `fad450c0c6530902` | completed / budget_exhausted | 58 | 48 | 0.8276 | 8 | 1 | 0 | exact |
| `experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-4c08a14af6e9db79ddd67c253bfc8913` | `43c51c7e28836214` | completed / budget_exhausted | 53 | 51 | 0.9623 | 2 | 2 | 0 | exact |
| `experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-8af8d02b35c6afad6c76604d39809008` | `eacd3b0030fd3125` | completed / budget_exhausted | 78 | 59 | 0.7564 | 19 | 3 | 0 | exact |
| `experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-e3f4f7007c50fe7e09b301d31851c3e7` | `d1f434411fa7aa76` | running / None | 56 | 48 | 0.8571 | 9 | 3 | 0 | exact |
| `experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-f7718a2254b048b88d50d56208ef0726` | `910c3a2285d5fd8c` | completed / budget_exhausted | 64 | 49 | 0.7656 | 12 | 3 | 0 | exact |
| `experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-fd071eaf7b1741b165a97a3529900a06` | `0d3f6545627c9462` | completed / budget_exhausted | 56 | 52 | 0.9286 | 6 | 1 | 0 | exact |
| `experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/failed-epoch1-run-8c77c6588485304d1f73416318c62949` | `a6c39cf0f55d2177` | failed / operational_failure | 41 | 35 | 0.8537 | 6 | 4 | 0 | exact |
| `experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/run-6995cd12124d2697030bb4b9e48f79bd` | `0c91885760965df2` | completed / budget_exhausted | 57 | 55 | 0.9649 | 1 | 0 | 0 | exact |
| `experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/run-79900e7847544b09bfb266518e2d8484` | `947d7fe89791bd61` | completed / budget_exhausted | 38 | 36 | 0.9474 | 2 | 0 | 0 | exact |
| `experiments/2026-08-12-live-grounded-extension-expansion/run` | `8e22d0431fd2b98d` | completed / budget_exhausted | 666 | 658 | 0.988 | 5 | 0 | 0 | exact |
| `experiments/2026-08-13-defect-controller-steering-inert/failed-epoch1-run-8e22d0431fd2b98d` | `8e22d0431fd2b98d` | failed / operational_failure | 4 | 0 | 0.0 | 2 | 0 | 0 | none |
| `experiments/2026-08-13-defect-controller-steering-inert/failed-epoch2-run-8e22d0431fd2b98d` | `8e22d0431fd2b98d` | failed / operational_failure | 7 | 3 | 0.4286 | 5 | 1 | 0 | none |
| `experiments/2026-08-13-defect-controller-steering-inert/failed-epoch3-run-8e22d0431fd2b98d` | `8e22d0431fd2b98d` | failed / operational_failure | 14 | 8 | 0.5714 | 10 | 0 | 0 | none |
| `experiments/2026-08-22-change-epoch3-second-lineage/failed-attempt2-run-bb0455384ea09b5b72664a4f6f3f0cb7a5ac227c00a93976e5c8c31873ca84f4` | `bb0455384ea09b5b` | failed / operational_failure | 56 | 47 | 0.8393 | 13 | 3 | 0 | none |
| `experiments/2026-08-22-change-epoch3-second-lineage/failed-attempt3-run-bb0455384ea09b5b72664a4f6f3f0cb7a5ac227c00a93976e5c8c31873ca84f4` | `bb0455384ea09b5b` | failed / operational_failure | 49 | 37 | 0.7551 | 15 | 7 | 0 | exact |
| `experiments/2026-08-22-change-epoch3-second-lineage/run` | `bb0455384ea09b5b` | completed / budget_exhausted | 140 | 123 | 0.8786 | 25 | 11 | 0 | exact |
| `experiments/2026-08-22-live-reach-rich-run/failed-epoch1-run-40e713b30a147dfc1a0f73feb91fa67a493454f6103a452888b8e08713368c4c` | `40e713b30a147dfc` | failed / operational_failure | 41 | 30 | 0.7317 | 13 | 4 | 0 | exact |
| `experiments/2026-08-22-live-reach-rich-run/run` | `40e713b30a147dfc` | failed / operational_failure | 47 | 37 | 0.7872 | 12 | 6 | 0 | exact |
| `experiments/2026-08-24-change-rung7-wounds-falls-succession/run` | `40e713b30a147dfc` | failed / operational_failure | 38 | 33 | 0.8684 | 8 | 3 | 0 | none |
| `experiments/2026-08-25-change-constructive-frontier/run` | `1950b3d0ee228113` | failed / operational_failure | 292 | 256 | 0.8767 | 28 | 5 | 0 | exact |
| `experiments/2026-08-25-change-constructive-frontier/void-inert-battery-run-6913328037a61ca6` | `6913328037a61ca6` | failed / operational_failure | 84 | 70 | 0.8333 | 17 | 3 | 0 | exact |
| `experiments/2026-08-25-poietics-program/run` | `1b31f0065687bd24` | completed / budget_exhausted | 163 | 146 | 0.8957 | 18 | 9 | 0 | exact |
| `experiments/live_engaged_2026-07-27/run-f4fa6663e5412d64df943a5a22342baf` | `a37208a539d9fcec` | completed / budget_exhausted | 29 | 24 | 0.8276 | 6 | 2 | 0 | exact |
| `experiments/live_research_2026-07-29/narrow/runs/run-7d8723fbe8626c71db880826c244d332` | `acfa496ccc1745c7` | completed / budget_exhausted | 57 | 47 | 0.8246 | 13 | 4 | 0 | exact |
| `experiments/live_research_2026-07-29/openchallenge/runs/completed-epoch2-run-9e9812feefa792179d490db7734825b5` | `47ca0551cf0fc365` | completed / budget_exhausted | 31 | 29 | 0.9355 | 8 | 2 | 0 | exact |
| `experiments/live_research_2026-07-29/openchallenge/runs/completed-epoch3-run-9e9812feefa792179d490db7734825b5` | `f36b122383ed8368` | completed / budget_exhausted | 20 | 16 | 0.8 | 8 | 3 | 0 | exact |
| `experiments/live_research_2026-07-29/openchallenge/runs/failed-epoch1-run-0d1f88e18779b7eb6d8c5d6af3473ba7` | `410bf6349ee41363` | failed / operational_failure | 18 | 12 | 0.6667 | 3 | 0 | 0 | none |
| `experiments/live_research_2026-07-29/openchallenge/runs/run-27b80f26bd398c718360e97e2a403593` | `91bb8195d1c16bea` | completed / budget_exhausted | 26 | 21 | 0.8077 | 2 | 1 | 0 | exact |
| `experiments/live_research_2026-07-29/openchallenge/runs/run-9e9812feefa792179d490db7734825b5` | `384d5671a3298023` | completed / budget_exhausted | 23 | 19 | 0.8261 | 8 | 2 | 0 | exact |
| `experiments/live_research_2026-07-29/referee/runs/run-d17935a4bf5ffa67c7f6e67b9a637a00` | `479dcc93b2de9582` | completed / budget_exhausted | 15 | 14 | 0.9333 | 1 | 0 | 0 | exact |
| `experiments/live_research_2026-07-29/referee/runs/run-e542c3c1fc266943e0260c5aa8d7c107` | `c02d82870dc6abe6` | failed / operational_failure | 18 | 14 | 0.7778 | 3 | 2 | 0 | exact |
| `experiments/live_research_2026-07-29/referee/runs/run-e6c07aec698426a9b21d01399ba6b5b0` | `d13c506c29b09405` | completed / budget_exhausted | 38 | 30 | 0.7895 | 16 | 5 | 0 | exact |
| `experiments/live_research_2026-07-29/selfstudy/runs/completed-epoch3-run-9175f0ecb055e57455af3c50df153c5a` | `887a2ccbd89efbb9` | completed / budget_exhausted | 42 | 33 | 0.7857 | 12 | 4 | 0 | exact |
| `experiments/live_research_2026-07-29/selfstudy/runs/failed-epoch1-run-9175f0ecb055e57455af3c50df153c5a` | `aa97a67dac8674f7` | failed / operational_failure | 40 | 34 | 0.85 | 9 | 3 | 0 | exact |
| `experiments/live_research_2026-07-29/selfstudy/runs/failed-epoch2-run-9175f0ecb055e57455af3c50df153c5a` | `c381d9e48accc09e` | failed / operational_failure | 27 | 23 | 0.8519 | 4 | 1 | 0 | exact |
| `experiments/live_research_2026-07-29/selfstudy/runs/failed-epoch4-run-9175f0ecb055e57455af3c50df153c5a` | `7575fa009beb04b7` | running / None | 7 | 6 | 0.8571 | 2 | 1 | 0 | exact |
| `experiments/live_research_2026-07-29/selfstudy/runs/run-9175f0ecb055e57455af3c50df153c5a` | `45c17980581a06b4` | completed / budget_exhausted | 35 | 29 | 0.8286 | 9 | 2 | 0 | exact |
| `experiments/live_research_2026-07-29/wide/runs/run-0c3ce902cc5bca75a709b04e2473d100` | `f69d6211ebd4f295` | running / None | 16 | 12 | 0.75 | 4 | 1 | 0 | exact |
| `experiments/live_research_2026-07-29/wide/runs/run-5a771259557378224bd68591483817be` | `5f25d072f10846a9` | completed / budget_exhausted | 17 | 12 | 0.7059 | 4 | 3 | 0 | exact |
| `experiments/live_tri_2026-07-27/run-15a53aca8a6fc66a39f382fc688c5346` | `728f11ff917fa36b` | completed / budget_exhausted | 49 | 35 | 0.7143 | 14 | 5 | 0 | exact |
| `experiments/live_tri_2026-07-27/run-6dab80d615a437a8b3fa489a279df847` | `594d29e006d57dab` | completed / budget_exhausted | 21 | 15 | 0.7143 | 6 | 3 | 0 | exact |
| `experiments/live_tri_2026-07-27/run-9ae94bb478990cbecca373fc3bcb1345` | `1e538d1b04537819` | completed / budget_exhausted | 21 | 18 | 0.8571 | 4 | 0 | 0 | exact |
| `experiments/live_tri_2026-07-27/run-ac1836b6237b6e9d80b3b0cb492b39f5` | `49e9c1354452aef6` | completed / budget_exhausted | 36 | 34 | 0.9444 | 3 | 2 | 0 | exact |
| `experiments/live_tri_2026-07-27/run-c5ab654afd1b4aa131aede83bdca0f03` | `17b98372bd1e2df3` | completed / budget_exhausted | 22 | 17 | 0.7727 | 6 | 3 | 0 | exact |
| `experiments/live_tri_2026-07-27/run-faa5feae126bc2558ea9c6d8d200a90c` | `5363cd2291f5be1f` | completed / budget_exhausted | 26 | 22 | 0.8462 | 2 | 1 | 0 | exact |
