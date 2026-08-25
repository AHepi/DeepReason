# The RUN ANATOMY PROGRAM

Registered 2026-08-26. Three windows, ten dimensions, one shared root
inventory. Read-only throughout: this program MEASURES committed runs. It
fixes nothing, anywhere. Every defect it surfaces becomes a parked,
ready-to-send prompt for `deepreason-orchestrator` or
`dr-change-orchestrator`, and nothing else.

## The authority — the operator's words, verbatim

> I need a prompt that measurs what happened each run: Was scratch pad
> called, when and why, what were models filling in the forms with, what
> parts of evidence were used, what were criticisms attacking, what were
> judges doing, how were they filling out forms, were signals working,
> were commitments attacked correctly and how, everything.

Reproduced rather than paraphrased because it is the whole scope of the
program, and a scope whose authority is a paraphrase is a scope nobody can
audit later. The ten dimensions below are a decomposition of that sentence,
not an extension of it: nine are named in it directly, and D10 is the
"everything" clause given a bounded reading (where the tokens went), stated
as an interpretation so it can be overruled.

## The ten dimensions

| id | dimension | the operator's phrase it answers to |
|---|---|---|
| D1 | **Scratchpad invocation** — when a scratch turn was taken, on which problem, under which authority, and what the run did with the block afterwards | "Was scratch pad called, when and why" |
| D2 | **Form filling** — what the models wrote into every typed form: which contract, valid or not on arrival, which field failed and how, and what the content classes look like | "what were models filling in the forms with" |
| D3 | **Evidence use** — which admitted dossier blocks were cited, by whom, whether the byte-check passed, and which parts were never touched | "what parts of evidence were used" |
| D4 | **Criticism targets** — what each criticism was aimed at, on what ground, and whether it landed | "what were criticisms attacking" |
| D5 | **Judge activity** — when a judge seat was called, on what exchange, and what followed from its ruling | "what were judges doing" |
| D6 | **Judge form filling** — the judge's own two-field form: the verdict it chose and the decisive point it named | "how were they filling out forms" |
| D7 | **Signals** — whether the declared signals were produced, consumed and acted on, or whether allocation ran open-loop | "were signals working" |
| D8 | **Commitment attacks** — whether a commitment was attacked through a warrant that licenses the edge, and what the status change rested on | "were commitments attacked correctly and how" |
| D9 | **Capability channels** — typed simulation and research proposals: raised, admitted, worked, consumed, or never used | "everything" (the capability lifecycle is typed and unmeasured) |
| D10 | **Run economy** — where the tokens went, by seat, contract, cycle and phase | "everything", read as: what did the run spend itself on |

## The three rounds

- **Round 1 — CENSUS (this round).** Establish what is in the record, per
  attempt and per event, with instruments that re-derive their own numbers.
  No interpretation beyond naming causes the record itself names. Three
  windows run CONCURRENTLY.
- **Round 2 — CORRELATION.** Join the census dimensions to each other and
  to outcomes: does a seat that fabricates handles also lose repair grants;
  does scratchpad use precede better conjectures; does judge severity move
  with the model. Round 2 may not begin on a dimension whose Round 1 census
  is missing.
- **Round 3 — DISPOSITION.** Turn surviving findings into parked prompts,
  one per finding, each routed and priced. Round 3 authors no fixes either;
  it is where the program hands its results to the two fixing families.

## Concurrency contract between the windows

W1, W2 and W3 run at the same time on the same branch family. They
coordinate BY DIRECTORY, never by file:

| window | owns, and writes ONLY | dimensions |
|---|---|---|
| W1 | `W1-form-census/` **plus** the program-level files `PROGRAM.md`, `inventory.py`, `ROOT_INVENTORY.json` | D2 (and the D10 slice visible in provider attempts) |
| W2 | `W2-<its own slug>/` | assigned in its own prompt |
| W3 | `W3-<its own slug>/` | assigned in its own prompt |

W1 was given the program-registration duty for this round, which is why the
program-level files are W1's this window and no one else's. A later window
that needs to change `PROGRAM.md` appends a dated amendment section rather
than editing what is above it — the same never-rewrite rule REQUEST.md
applies to requirements.

`ROOT_INVENTORY.json` is the shared substrate. It is REGENERATED, never
hand-edited: `python3 inventory.py`.

## The root inventory

Every committed run root on `main` at `bdb516ae4`, after the prune. A root
is a directory carrying BOTH `run-status.json` and `log.jsonl`. **54 roots,
3 155 provider attempts.**

One tracked `run-status.json` is NOT a root and is excluded by name rather
than dropped silently:
`experiments/2026-08-21-fix-wheel-smoke-reason-stage/evidence/run-e9d4bb16-run-status.json`
is a bare status file committed as wheel-smoke evidence, with no log beside it.

"Dimensions measurable" is a statement about the RECORD, not an assignment
of work: it says which dimensions have any events to count in that root, so
a later window does not spend a session discovering that a root has no judge
in it. D2 and D10 are measurable everywhere because every root has provider
attempts.

Two roots are the program's priority, per the W1 prompt: the P-C1 ARM H root
(row 54) and the P-R1 root (row 52).

| # | root | run id | date | state / stop | cyc | seats × model(s) | opt-ins | attempts | dimensions measurable |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `experiments/live_engaged_2026-07-27/run-f4fa6663e5412d64df943a5a22342baf` | `a37208a539d9fcec` | 2026-07-27 | completed / budget_exhausted | 6 | 11 × mistral-large-3:675b | simulation | 29 | D1 D2 D3 D4/D8 D9 D10 |
| 2 | `experiments/live_tri_2026-07-27/run-9ae94bb478990cbecca373fc3bcb1345` | `1e538d1b04537819` | 2026-07-27 | completed / budget_exhausted | 6 | 11 × deepseek-v4-pro | simulation | 21 | D1 D2 D3 D4/D8 D9 D10 |
| 3 | `experiments/live_tri_2026-07-27/run-6dab80d615a437a8b3fa489a279df847` | `594d29e006d57dab` | 2026-07-27 | completed / budget_exhausted | 6 | 11 × glm-5.2 | simulation | 21 | D1 D2 D3 D4/D8 D9 D10 |
| 4 | `experiments/live_tri_2026-07-27/run-faa5feae126bc2558ea9c6d8d200a90c` | `5363cd2291f5be1f` | 2026-07-27 | completed / budget_exhausted | 6 | 11 × kimi-k2.6 | simulation | 26 | D1 D2 D3 D4/D8 D9 D10 |
| 5 | `experiments/live_tri_2026-07-27/run-15a53aca8a6fc66a39f382fc688c5346` | `728f11ff917fa36b` | 2026-07-27 | completed / budget_exhausted | 12 | 11 × glm-5.2 | simulation | 49 | D1 D2 D3 D4/D8 D9 D10 |
| 6 | `experiments/live_tri_2026-07-27/run-c5ab654afd1b4aa131aede83bdca0f03` | `17b98372bd1e2df3` | 2026-07-27 | completed / budget_exhausted | 12 | 11 × kimi-k2.6 | simulation | 22 | D1 D2 D3 D4/D8 D9 D10 |
| 7 | `experiments/live_tri_2026-07-27/run-ac1836b6237b6e9d80b3b0cb492b39f5` | `49e9c1354452aef6` | 2026-07-27 | completed / budget_exhausted | 12 | 11 × deepseek-v4-pro | simulation | 36 | D1 D2 D3 D4/D8 D9 D10 |
| 8 | `experiments/live_research_2026-07-29/wide/runs/run-0c3ce902cc5bca75a709b04e2473d100` | `f69d6211ebd4f295` | 2026-07-29 | running / None | 1 | 11 × glm-5.2 | research,simulation | 16 | D1 D2 D3 D4/D8 D9 D10 |
| 9 | `experiments/live_research_2026-07-29/narrow/runs/run-7d8723fbe8626c71db880826c244d332` | `acfa496ccc1745c7` | 2026-07-29 | completed / budget_exhausted | 18 | 11 × glm-5.2 | research,simulation | 57 | D1 D2 D3 D4/D8 D9 D10 |
| 10 | `experiments/live_research_2026-07-29/wide/runs/run-5a771259557378224bd68591483817be` | `5f25d072f10846a9` | 2026-07-29 | completed / budget_exhausted | 6 | 11 × glm-5.2 | research,simulation | 17 | D1 D2 D3 D4/D8 D9 D10 |
| 11 | `experiments/live_research_2026-07-29/referee/runs/run-e542c3c1fc266943e0260c5aa8d7c107` | `c02d82870dc6abe6` | 2026-07-29 | failed / operational_failure | 4 | 11 × glm-5.2 | config_referee,research,simulation | 18 | D1 D2 D3 D4/D8 D9 D10 |
| 12 | `experiments/live_research_2026-07-29/referee/runs/run-d17935a4bf5ffa67c7f6e67b9a637a00` | `479dcc93b2de9582` | 2026-07-29 | completed / budget_exhausted | 6 | 11 × glm-5.2 | config_referee,research,simulation | 15 | D1 D2 D3 D4/D8 D9 D10 |
| 13 | `experiments/live_research_2026-07-29/referee/runs/run-e6c07aec698426a9b21d01399ba6b5b0` | `d13c506c29b09405` | 2026-07-29 | completed / budget_exhausted | 6 | 11 × glm-5.2 | config_referee,research,simulation | 38 | D2 D3 D4/D8 D9 D10 |
| 14 | `experiments/live_research_2026-07-29/selfstudy/runs/failed-epoch1-run-9175f0ecb055e57455af3c50df153c5a` | `aa97a67dac8674f7` | 2026-07-29 | failed / operational_failure | 3 | 11 × glm-5.2 | config_referee,research,simulation | 40 | D1 D2 D3 D4/D8 D9 D10 |
| 15 | `experiments/live_research_2026-07-29/selfstudy/runs/failed-epoch2-run-9175f0ecb055e57455af3c50df153c5a` | `c381d9e48accc09e` | 2026-07-29 | failed / operational_failure | 2 | 11 × glm-5.2 | attached_evidence,config_referee,research,simulation | 27 | D2 D3 D4/D8 D9 D10 |
| 16 | `experiments/live_research_2026-07-29/selfstudy/runs/completed-epoch3-run-9175f0ecb055e57455af3c50df153c5a` | `887a2ccbd89efbb9` | 2026-07-29 | completed / budget_exhausted | 6 | 11 × glm-5.2 | attached_evidence,config_referee,research,simulation | 42 | D1 D2 D3 D4/D8 D9 D10 |
| 17 | `experiments/live_research_2026-07-29/selfstudy/runs/failed-epoch4-run-9175f0ecb055e57455af3c50df153c5a` | `7575fa009beb04b7` | 2026-07-30 | running / None | 1 | 11 × glm-5.2 | attached_evidence,config_referee,research,simulation | 7 | D1 D2 D3 D4/D8 D9 D10 |
| 18 | `experiments/live_research_2026-07-29/selfstudy/runs/run-9175f0ecb055e57455af3c50df153c5a` | `45c17980581a06b4` | 2026-07-30 | completed / budget_exhausted | 6 | 11 × glm-5.2 | attached_evidence,config_referee,research,simulation | 35 | D2 D3 D4/D8 D9 D10 |
| 19 | `experiments/live_research_2026-07-29/openchallenge/runs/failed-epoch1-run-0d1f88e18779b7eb6d8c5d6af3473ba7` | `410bf6349ee41363` | 2026-07-30 | failed / operational_failure | 0 | 11 × glm-5.2 | attached_evidence,config_referee,research,simulation | 18 | D2 D3 D4/D8 D9 D10 |
| 20 | `experiments/live_research_2026-07-29/openchallenge/runs/completed-epoch2-run-9e9812feefa792179d490db7734825b5` | `47ca0551cf0fc365` | 2026-07-30 | completed / budget_exhausted | 6 | 11 × glm-5.2 | attached_evidence,config_referee,research,simulation | 31 | D1 D2 D3 D4/D8 D9 D10 |
| 21 | `experiments/live_research_2026-07-29/openchallenge/runs/completed-epoch3-run-9e9812feefa792179d490db7734825b5` | `f36b122383ed8368` | 2026-07-30 | completed / budget_exhausted | 6 | 11 × glm-5.2 | attached_evidence,config_referee,research,simulation | 20 | D2 D3 D4/D8 D9 D10 |
| 22 | `experiments/live_research_2026-07-29/openchallenge/runs/run-9e9812feefa792179d490db7734825b5` | `384d5671a3298023` | 2026-07-30 | completed / budget_exhausted | 6 | 11 × glm-5.2 | attached_evidence,config_referee,research,simulation | 23 | D2 D3 D4/D8 D9 D10 |
| 23 | `experiments/live_research_2026-07-29/openchallenge/runs/run-27b80f26bd398c718360e97e2a403593` | `91bb8195d1c16bea` | 2026-07-30 | completed / budget_exhausted | 6 | 11 × glm-5.2 | attached_evidence,config_referee,research,simulation | 26 | D2 D3 D4/D8 D9 D10 |
| 24 | `experiments/2026-08-02-stress-triplet/home-orbit/runs/run-6472629dbc5d408a733d472040671752` | `4e9897f86aeeab8b` | 2026-08-02 | completed / budget_exhausted | 6 | 11 × glm-5.2 | attached_evidence,config_referee,simulation | 45 | D2 D3 D4/D8 D9 D10 |
| 25 | `experiments/2026-08-02-stress-triplet/home-triage/runs/run-0a3e93d6e8031e2e6d1d21dde2fa93cc` | `2e8904aa31694454` | 2026-08-02 | completed / budget_exhausted | 6 | 11 × glm-5.2 | attached_evidence,simulation | 42 | D1 D2 D3 D4/D8 D9 D10 |
| 26 | `experiments/2026-08-02-stress-triplet/home-workshop/runs/run-1a0d4168a446f052bc7ccc9aa20b9829` | `7098a900b2b194c9` | 2026-08-02 | completed / budget_exhausted | 6 | 11 × glm-5.2 | simulation | 52 | D1 D2 D3 D4/D8 D9 D10 |
| 27 | `experiments/2026-08-04-change-rung5-dumb-alternative-backend/ab-home/runs/run-9a6be78e1e79184a0bd89923b957586c` | `64cc945753f3a9a9` | 2026-08-04 | completed / budget_exhausted | 6 | 11 × glm-5.2 | simulation | 31 | D1 D2 D3 D4/D8 D9 D10 |
| 28 | `experiments/2026-08-04-change-rung5-dumb-alternative-backend/rr-home/runs/run-9a6be78e1e79184a0bd89923b957586c` | `c87d5802b5f51583` | 2026-08-04 | completed / budget_exhausted | 6 | 11 × glm-5.2 | simulation | 24 | D2 D3 D4/D8 D9 D10 |
| 29 | `experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/run-79900e7847544b09bfb266518e2d8484` | `947d7fe89791bd61` | 2026-08-08 | completed / budget_exhausted | 8 | 11 × gemma4:31b, glm-5.2 | simulation | 38 | D1 D2 D3 D4/D8 D9 D10 |
| 30 | `experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/failed-epoch1-run-8c77c6588485304d1f73416318c62949` | `a6c39cf0f55d2177` | 2026-08-08 | failed / operational_failure | 0 | 11 × gemma4:31b, glm-5.2 | simulation | 41 | D1 D2 D3 D4/D8 D9 D10 |
| 31 | `experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/run-6995cd12124d2697030bb4b9e48f79bd` | `0c91885760965df2` | 2026-08-08 | completed / budget_exhausted | 12 | 11 × gemma4:31b, glm-5.2 | simulation | 57 | D1 D2 D3 D4/D8 D9 D10 |
| 32 | `experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-e3f4f7007c50fe7e09b301d31851c3e7` | `d1f434411fa7aa76` | 2026-08-08 | running / None | 2 | 11 × gemma4:31b, glm-5.2 | simulation | 56 | D1 D2 D3 D4/D8 D9 D10 |
| 33 | `experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-fd071eaf7b1741b165a97a3529900a06` | `0d3f6545627c9462` | 2026-08-08 | completed / budget_exhausted | 10 | 11 × gemma4:31b, glm-5.2 | simulation | 56 | D1 D2 D3 D4/D8 D9 D10 |
| 34 | `experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-0cdd57d1d8edc5328803a7bb5070a1d1` | `c2dcb87e33616c32` | 2026-08-08 | completed / budget_exhausted | 12 | 11 × gemma4:31b, glm-5.2 | simulation | 63 | D1 D2 D3 D4/D8 D9 D10 |
| 35 | `experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-18ca3170f2ff30d99e8255b48f47ab70` | `6e193328f7c2d559` | 2026-08-09 | completed / budget_exhausted | 10 | 11 × gemma4:31b, glm-5.2 | simulation | 48 | D1 D2 D3 D4/D8 D9 D10 |
| 36 | `experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-167fe0eb4b373a0e27e87f0482ee5ce7` | `c336e3e2ad956c35` | 2026-08-09 | completed / budget_exhausted | 10 | 11 × gemma4:31b, glm-5.2 | simulation | 55 | D1 D2 D3 D4/D8 D9 D10 |
| 37 | `experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-0becdcfe2987fea4b74bc1c7e58e41ea` | `a45501493e81871b` | 2026-08-09 | completed / budget_exhausted | 12 | 11 × gemma4:31b, glm-5.2 | simulation | 59 | D1 D2 D3 D4/D8 D9 D10 |
| 38 | `experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-4056c2bce14e9eeabd35956c4fab1e4b` | `fad450c0c6530902` | 2026-08-09 | completed / budget_exhausted | 12 | 11 × gemma4:31b, glm-5.2 | simulation | 58 | D1 D2 D3 D4/D8 D9 D10 |
| 39 | `experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-8af8d02b35c6afad6c76604d39809008` | `eacd3b0030fd3125` | 2026-08-09 | completed / budget_exhausted | 12 | 11 × gemma4:31b, glm-5.2 | simulation | 78 | D1 D2 D3 D4/D8 D9 D10 |
| 40 | `experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-4c08a14af6e9db79ddd67c253bfc8913` | `43c51c7e28836214` | 2026-08-09 | completed / budget_exhausted | 12 | 11 × gemma4:31b, glm-5.2 | simulation | 53 | D1 D2 D3 D4/D8 D9 D10 |
| 41 | `experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-f7718a2254b048b88d50d56208ef0726` | `910c3a2285d5fd8c` | 2026-08-09 | completed / budget_exhausted | 12 | 11 × gemma4:31b, glm-5.2 | simulation | 64 | D1 D2 D3 D4/D8 D9 D10 |
| 42 | `experiments/2026-08-12-live-grounded-extension-expansion/run` | `8e22d0431fd2b98d` | 2026-08-13 | completed / budget_exhausted | 8 | 11 × deepseek-v4-flash:0731, glm-5.2, mistral-large-3:675b, qwen3.5:397b | attached_evidence,simulation | 666 | D1 D2 D3 D4/D8 D5/D6 D9 D10 |
| 43 | `experiments/2026-08-13-defect-controller-steering-inert/failed-epoch1-run-8e22d0431fd2b98d` | `8e22d0431fd2b98d` | 2026-08-13 | failed / operational_failure | 0 | 11 × deepseek-v4-flash:0731, glm-5.2, mistral-large-3:675b, qwen3.5:397b | attached_evidence,simulation | 4 | D2 D3 D9 D10 |
| 44 | `experiments/2026-08-13-defect-controller-steering-inert/failed-epoch2-run-8e22d0431fd2b98d` | `8e22d0431fd2b98d` | 2026-08-13 | failed / operational_failure | 0 | 11 × deepseek-v4-flash:0731, glm-5.2, mistral-large-3:675b, qwen3.5:397b | attached_evidence,simulation | 7 | D2 D3 D9 D10 |
| 45 | `experiments/2026-08-13-defect-controller-steering-inert/failed-epoch3-run-8e22d0431fd2b98d` | `8e22d0431fd2b98d` | 2026-08-13 | failed / operational_failure | 0 | 11 × deepseek-v4-flash:0731, glm-5.2, mistral-large-3:675b, qwen3.5:397b | attached_evidence,simulation | 14 | D2 D3 D9 D10 |
| 46 | `experiments/2026-08-22-live-reach-rich-run/failed-epoch1-run-40e713b30a147dfc1a0f73feb91fa67a493454f6103a452888b8e08713368c4c` | `40e713b30a147dfc` | 2026-08-22 | failed / operational_failure | 2 | 11 × glm-5.2 | — | 41 | D1 D2 D3 D4/D8 D10 |
| 47 | `experiments/2026-08-22-live-reach-rich-run/run` | `40e713b30a147dfc` | 2026-08-22 | failed / operational_failure | 2 | 11 × glm-5.2 | — | 47 | D1 D2 D3 D4/D8 D10 |
| 48 | `experiments/2026-08-22-change-epoch3-second-lineage/failed-attempt2-run-bb0455384ea09b5b72664a4f6f3f0cb7a5ac227c00a93976e5c8c31873ca84f4` | `bb0455384ea09b5b` | 2026-08-23 | failed / operational_failure | 0 | 11 × glm-5.2 | attached_evidence | 56 | D2 D3 D4/D8 D9 D10 |
| 49 | `experiments/2026-08-22-change-epoch3-second-lineage/failed-attempt3-run-bb0455384ea09b5b72664a4f6f3f0cb7a5ac227c00a93976e5c8c31873ca84f4` | `bb0455384ea09b5b` | 2026-08-23 | failed / operational_failure | 2 | 11 × glm-5.2 | attached_evidence | 49 | D1 D2 D3 D4/D8 D9 D10 |
| 50 | `experiments/2026-08-22-change-epoch3-second-lineage/run` | `bb0455384ea09b5b` | 2026-08-24 | completed / budget_exhausted | 8 | 11 × glm-5.2 | attached_evidence | 140 | D1 D2 D3 D4/D8 D9 D10 |
| 51 | `experiments/2026-08-24-change-rung7-wounds-falls-succession/run` | `40e713b30a147dfc` | 2026-08-25 | failed / operational_failure | 0 | 11 × glm-5.2 | — | 38 | D2 D3 D4/D8 D10 |
| 52 | `experiments/2026-08-25-poietics-program/run` | `1b31f0065687bd24` | 2026-08-25 | completed / budget_exhausted | 12 | 11 × deepseek-v4-pro:0813, glm-5.2, kimi-k3, qwen3.5:397b | attached_evidence,simulation | 163 | D1 D2 D3 D4/D8 D9 D10 |
| 53 | `experiments/2026-08-25-change-constructive-frontier/void-inert-battery-run-6913328037a61ca6` | `6913328037a61ca6` | 2026-08-25 | failed / operational_failure | 11 | 11 × glm-5.2 | simulation | 84 | D1 D2 D3 D9 D10 |
| 54 | `experiments/2026-08-25-change-constructive-frontier/run` | `1950b3d0ee228113` | 2026-08-25 | failed / operational_failure | 15 | 11 × glm-5.2 | simulation | 292 | D1 D2 D3 D4/D8 D9 D10 |

## What this program will not do

- It will not fix anything, in any window or round.
- It will not modify a committed run root. Roots are opened read-only; a
  writable open repairs, which is to say destroys, the evidence.
- It will not treat model prose as evidence. Every number traces to
  `log.jsonl`, `objects/`, `blobs/`, `progress.jsonl`, `run-status.json` or
  a committed scoring artifact.
- It will not report a number that its own committed instrument cannot
  re-derive from the committed roots.
