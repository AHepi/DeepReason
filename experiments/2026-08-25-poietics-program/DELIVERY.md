# DELIVERY — the Poietics program, P-R1

Branch: `claude/poietics-p-r1-explanation-8dy9b0`
Base: `origin/main` at `853bf705c`
Outcome: **P-R1 SUCCESS by PREREG.md §6.** All three registered milestones
hold; `verify_root` 0 violations; typed terminal.

## 1. Requirement by requirement, against the operator's verbatim words

| R | operator's words | status | evidence |
|---|---|---|---|
| R1 | "TARGET REPOSITORY: AHepi/DeepReason — verify before anything else" | **HONOURED** | verified before any other action; `git remote -v` → `AHepi/DeepReason` |
| R2 | "Route the setup through dr-change-orchestrator; judge the run on typed outcomes only" | **HONOURED** | REQUEST → SPEC → execute → RESULTS. Every verdict from `results.txt`, `verify_root.json`, `milestones.json`; no prose judged |
| R3 | the SETUP block | **DONE** | branch from `origin/main`; `853bf705c` confirmed ancestor; editable install; pytest/xdist/jsonschema; `embedder-warmup` → sentinel `d6e3599ce0377000` |
| R4 | "THE OPERATOR SUPPLIES … POIETICS_FULL_RECORD.zip now, and the OLLAMA_API_KEY env file at the launch step only" | **HONOURED, after one stop** | the zip did not arrive with the task; two other files did. Stopped and asked rather than substituting. Key requested only after the green soak (C6) |
| R5 | "record/ receives VERBATIM: README.md, report/00, 12, 14, 15, and data/ (all JSON)" | **DONE** | 12 files, each sha256-proved byte-identical to the zip; manifest in the tranche README |
| R6 | "The rest of the report/ and sources/ trees are NOT committed … note that in the tranche README with the zip's name" | **DONE** | README names `POIETICS_FULL_RECORD.zip` and lists what is deliberately absent |
| R7 | "Provenance header … the record's own §14 caution, quoted" | **DONE** | tranche README quotes both bundle cautions verbatim plus §14's own statement of the compression mechanism |
| R8 | "PROGRAM.md registering all three runs" | **DONE** | PROGRAM.md: P-R1, P-R2 with the five stated confounds as registered ammunition and explicit demarcation criteria, P-R3 under the Rung 7 protocol |
| R9 | "P-R2 and P-R3 are REGISTERED, not run here — one tranche, one run" | **HONOURED** | both carry STATUS: REGISTERED, NOT RUN, launch preconditions, and their own honest limits. Neither launched |
| R10 | "P-R1 DESIGN, frozen in PREREG before any API call" | **DONE** | PREREG.md committed at `ee604f914`; first provider call at 09:40 the following commit |
| R10a | QUESTION verbatim | **DONE** | `build_manifest_pr1.py::QUESTION`, em-dashes included; echoed in `results.txt` |
| R10b | "the six committed documents, bound as attached evidence … critics cite the bound dossier" | **DONE** | 12 files = 6 documents (D1), admitted at seed: 12 sources, 623 blocks, 0 refusals. **212 byte-checked citations into the dossier**, 2 critic-side |
| R10c | "solo, everything on … glm-5.2 profile" | **SUPERSEDED by R17** | operator replaced the solo posture mid-tranche; see R17 |
| R10d | "REGISTERED MILESTONES … Stochastic extras named as such" | **DONE** | PREREG §5: M1, M2, M3 (conditional), plus five stochastic extras explicitly barred from being success conditions |
| R11 | "the P-R1 config is a NEW case — extend scripts/cycle_soak.py's case table in the same commit, run it, paste exit 0. Then ask for the key" | **DONE** | case `pr1` added; `exit 0 (clean)` pasted; epoch3 regression `exit 0`; key requested only afterwards |
| R12 | "LAUNCH: detached, snapshot loop, monitor progress.jsonl + rc= lines" | **DONE** | `setsid nohup`, snapshot loop bound to the driver PID, monitor on phases/`rc=`/progress |
| R13 | "SUCCESS: typed terminal, verify_root clean, the registered milestones present — commit the root; RESULTS.md names what the run's accepted-and-surviving conjectures actually claim, with the honest residue" | **DONE** | all four conditions met; root committed; RESULTS.md names three claim groups and six residue items |
| R14 | "An operational death: park for the soak's ledger and STOP … One repeat pre-authorized" | **HONOURED** | attempt 1 refused at launch; parked as P1; **the one repeat was used** and succeeded. No third attempt |
| R15 | "NO src/tests changes beyond the soak case line (git diff --stat proves it)" | **HONOURED** | see §2 |
| R16 | "Commit and push every phase boundary (retry 2s/4s/8s/16s)" | **DONE** | every phase boundary committed and pushed; no retry needed, no push failed |
| R17 | "Deepseek V4 Pro 0813 for conjecturer, Kimi K3 for critic, Qwen 3.5 for judge one and GLM 5.2 for judge 3" | **DONE, with D2** | exact seat matrix compiled and qualified; ensemble built as TWO seats because two models were named |

## 2. R15 proof

    git diff --stat origin/main...HEAD -- src/ tests/
    (no output)

    git diff --stat origin/main...HEAD -- ':!experiments/2026-08-25-poietics-program'
     scripts/cycle_soak.py | 67 ++++++++++++++++++++++++++++++++++++++++++++++-----
     1 file changed, 61 insertions(+), 6 deletions(-)

Zero files under `src/` or `tests/`. The only change outside the tranche is
`scripts/cycle_soak.py`, which R11 authorises. It is more than one line, and
the excess is accounted for: `builder_dir` (the case table could not name a
builder outside the reach-rich directory), `delegates_to_builder` (the
default path compiles a single-model manifest with an empty dossier — the
wrong shape for P-R1, and an instrument that soaks the wrong shape reports
green), and an ensemble fix in `_loopback_config` (a role carrying a LIST of
routes was skipped by the endpoint redirect, so an offline soak of any
ensemble config would have pointed its judge seats at the live provider with
the operator's key). Both existing cases keep their exact behaviour;
`--case epoch3` re-verified `exit 0`.

## 3. Declared deviations

**D1 — twelve FILES, six DOCUMENTS.** R10b says "the six committed
documents". The committed set is `README.md`, four `report/` sections, and
`data/` as one seven-file bundle. All twelve bound as separate sources —
inside `maximum_sources=16`, and each file keeps its own citable identity.
Binding `data/` as one concatenated source would have exceeded
`maximum_excerpt_bytes_per_source` and destroyed per-file citability.

**D2 — the judge ensemble is two seats.** R17 named "judge one" and
"judge 3" and skipped judge 2. Two seats is the smallest reading that
compiles, and it satisfies the gate exactly:
`require_cross_family_judge_ensemble` demands ≥2 seats AND ≥2 families. The
operator was told before launch that silence meant two.

**D3 — seven unnamed roles stay on `glm-5.2`.** R17 named four seats;
`Config.roles` defaults to `{}`, so silence would have left the rest with
zero routes.

## 4. What went wrong, and what it cost

**Attempt 1 was refused at launch, after the qualification battery.**
`RUN_INPUT_MISMATCH` — `build_manifest_pr1.py` wrote `"sources": []` in
`problem.json`, inherited from two predecessor builders where it was correct
because their dossiers are empty. Cost: one battery. Retired as
`refused-attempt1-manifest-1b31f0065687bd24`, rename committed first, never
edited. Fixed, and the fix is mutation-proven: the guard passes the corrected
root, refuses the planted defect with a byte-identical error, and refuses a
reordering.

**The bench could not have caught it**, which is the finding that outlives
the tranche (PARKED P1): the soak drives `TextRunApplicationService`, and
the check lives in the CLI shell above it; every non-delegating case binds
an empty dossier, so the predicate is vacuous on the bench.

**A defect in my own scoring instrument, caught before the terminal.** The
census counted conjecture-side citations toward M2, which PREREG registered
as a CRITICISM milestone. On the final record that is decisive: 212 citations
into the dossier, only 2 critic-side. The loose version reports M2 MET on 212;
the registration says it is met on 2. **The instrument was tightened; the
registration was not loosened.** Recorded here because the opposite move —
widening a milestone to fit what the run produced — is the exact mechanism
the attached record diagnoses.

## 5. Parked, not fixed

Five findings, each with a ready-to-send prompt: **P1** the soak cannot see
a launch-time workload mismatch; **P2** `deepreason results` may not describe
a refused-at-launch root; **P3** `report/14` scores 0/3 on this tranche's
criteria (a note for P-R2's design); **P4** the results surface counts 24
import-role records among the 82 survivors, against CLAUDE.md's invariant;
**P5** the judge ensemble was qualified, paid for, and never entered the
trial path.

## 6. The two things not to over-read

The judge ensemble made **zero calls**. The 419 acceptances are legacy-path
acceptances, not adjudicated verdicts, and nothing in this run is evidence
about cross-family judging.

The largest group of surviving conjectures says the record **cannot** answer
the question. That position engages the confound the question handed it, and
this run cannot adjudicate it against the positive group — because
adjudication is precisely what did not run. P-R3 exists for that, and its
precondition is now satisfied.
