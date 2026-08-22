# Request: "reach epoch 3 — put a SECOND problem lineage in the root, then launch"
Captured: 2026-08-22 from the operator's single tranche brief (this session's
first and only operator message so far).

## Verbatim

> Evidence-minting tranche: reach epoch 3 — put a SECOND problem
> lineage in the root, then launch. Route through
> dr-change-orchestrator for the design amendment, then execute; the
> workflow's own stops apply.
>
> SETUP (fresh container): git fetch origin main && git checkout -B
> claude/reach-epoch3-second-lineage-d8wj4t origin/main;
> git merge-base --is-ancestor e1ea05e82 HEAD || re-fetch. pip install
> -e . --break-system-packages -q; pip install pytest pytest-xdist
> jsonschema --break-system-packages -q. deepreason embedder-warmup.
> Read CLAUDE.md in full; load dr-drive-harness,
> dr-explain-to-operator. THE OPERATOR SUPPLIES the OLLAMA_API_KEY env
> file at the launch step; all design work first, offline.
>
> CONTEXT (read IN FULL): experiments/2026-08-22-live-reach-rich-run/
> RESULTS.md + PARKED.md. Both operational killers are FIXED on main
> (P7: lossless patch spellings absorbed, E42; P9: max_tokens ceiling,
> E43) — epoch 3 cannot die the recorded ways. The remaining blocker
> is P4-reach: reach_sweep skips problems an artifact already
> addresses, and a single-seed run puts every accepted artifact on the
> seed's own problem — the seed is never FOREIGN to anything. The
> mission needs a second lineage whose artifacts can meet the seed's
> subject predicates.
>
> DESIGN, in preference order — establish which vehicle works, ledger
> the choice in SPEC.md:
> (1) AMENDMENT EPOCH on the existing terminal root (run id
>     40e713b3..., state=failed is a typed terminal): deepreason amend
>     to reshape the question / admit a second seed problem carrying
>     its OWN subject-substantive criteria (distinct predicates,
>     same domain family so cross-lineage survival is plausible), then
>     deepreason continue. This reuses the epistemic state, exercises
>     the amendment machinery live (L-2 parity), and puts both
>     lineages in one root — exactly what reach pairs need.
> (2) If amend cannot introduce a second lineage: a fresh run whose
>     question decomposes into two sibling problems with distinct
>     criteria, if the config surface can express it.
> (3) If NEITHER vehicle exists without code changes: STOP at SPEC
>     with the capability gap stated precisely and a parked prompt —
>     do not build harness features inside a live-run tranche.
> ALSO IN SCOPE (the ladder's own script): P8-reach — reach_run.sh
> records a path error from `deepreason results --root`; fix the
> ladder invocation per P8's parked note before launch.
>
> LAUNCH (dr-drive-harness): detached, snapshot loop armed, monitor on
> progress.jsonl + rc= lines. Budget: PREREG's bound stands; the
> P9 fix means max_tokens tuning is safe; the P7 fix means repair
> grants are spent only on real failures.
>
> JUDGE ON TYPED OUTCOMES ONLY: SUCCESS = typed terminal, verify_root
> clean, census (committed tooling) shows reach_set > 0. One repeat
> pre-authorized. Zero on both attempts: prediction UNSUPPORTED,
> both roots committed, STOP — the decision returns to the operator.
> Report any empty-battery or coverage==0.5 event under the P5
> rulings now on main (they are codified; the census vocabulary knows
> exit E0). Honest-ledger RESULTS.md segment either way.
>
> NO src/tests changes beyond none: git diff --stat proves the tree
> untouched outside experiments/. Commit and push every phase
> boundary (retry 2s/4s/8s/16s).

## Requirements

R1 (behavior): "reach epoch 3 — put a SECOND problem lineage in the root,
then launch."

R2 (process): "Route through dr-change-orchestrator for the design
amendment, then execute; the workflow's own stops apply."

R3 (process): SETUP as stated — "pip install -e . --break-system-packages
-q; pip install pytest pytest-xdist jsonschema --break-system-packages -q.
deepreason embedder-warmup. Read CLAUDE.md in full; load dr-drive-harness,
dr-explain-to-operator."

R4 (process): "THE OPERATOR SUPPLIES the OLLAMA_API_KEY env file at the
launch step; all design work first, offline."

R5 (process): "CONTEXT (read IN FULL): experiments/2026-08-22-live-reach-
rich-run/RESULTS.md + PARKED.md."

R6 (artifact): "DESIGN, in preference order — establish which vehicle
works, ledger the choice in SPEC.md".

R6a (behavior, preference 1): "AMENDMENT EPOCH on the existing terminal
root (run id 40e713b3..., state=failed is a typed terminal): deepreason
amend to reshape the question / admit a second seed problem carrying its
OWN subject-substantive criteria (distinct predicates, same domain family
so cross-lineage survival is plausible), then deepreason continue."

R6b (behavior, preference 2): "If amend cannot introduce a second lineage:
a fresh run whose question decomposes into two sibling problems with
distinct criteria, if the config surface can express it."

R6c (process, preference 3): "If NEITHER vehicle exists without code
changes: STOP at SPEC with the capability gap stated precisely and a
parked prompt — do not build harness features inside a live-run tranche."

R7 (behavior): "ALSO IN SCOPE (the ladder's own script): P8-reach —
reach_run.sh records a path error from `deepreason results --root`; fix
the ladder invocation per P8's parked note before launch."

R8 (process): "LAUNCH (dr-drive-harness): detached, snapshot loop armed,
monitor on progress.jsonl + rc= lines."

R9 (process): "Budget: PREREG's bound stands; the P9 fix means max_tokens
tuning is safe; the P7 fix means repair grants are spent only on real
failures."

R10 (process): "JUDGE ON TYPED OUTCOMES ONLY: SUCCESS = typed terminal,
verify_root clean, census (committed tooling) shows reach_set > 0."

R11 (process): "One repeat pre-authorized. Zero on both attempts:
prediction UNSUPPORTED, both roots committed, STOP — the decision returns
to the operator."

R12 (process): "Report any empty-battery or coverage==0.5 event under the
P5 rulings now on main (they are codified; the census vocabulary knows
exit E0)."

R13 (artifact): "Honest-ledger RESULTS.md segment either way."

R14 (process): "NO src/tests changes beyond none: git diff --stat proves
the tree untouched outside experiments/."

R15 (process): "Commit and push every phase boundary (retry
2s/4s/8s/16s)."

## Standing constraints

C1: "NO src/tests changes beyond none: git diff --stat proves the tree
untouched outside experiments/." — operator brief, LAUNCH/scope paragraph.
This is the tranche's hardest boundary and it interacts with R6c: any
vehicle needing a code change is a STOP, not an implementation.

C2: "do not build harness features inside a live-run tranche." — operator
brief, DESIGN option (3).

C3: "THE OPERATOR SUPPLIES the OLLAMA_API_KEY env file at the launch step;
all design work first, offline." — operator brief, SETUP.

C4: "the workflow's own stops apply." — operator brief, opening paragraph.
dr-change-orchestrator's stop conditions (a step failing twice the same
way; frozen-record semantics; budget exceeded; a requirement contradicting
the record) bind this tranche.

C5 (standing repo law, CLAUDE.md): the typed record is the only admissible
evidence; model prose is never evidence.

C6 (standing repo law, CLAUDE.md "Live runs"): never edit a committed run
root; retire by rename and COMMIT THE RENAME FIRST.

## Open questions (for dr-spec-change)

Q1: Can `deepreason amend` introduce a SECOND problem carrying its own
criteria, or does `amendment/apply.py` copy `criteria=parent_input.problem.
criteria` verbatim (P4-reach's claim) and seed exactly one problem? The
brief's preference order turns entirely on this and it is answerable
offline from the code plus a dry amend against a scratch copy of a root.

Q2: If amend seeds one problem only, can the workload/config surface
express a two-sibling-problem seeding without a code change? P4-reach
claims every route is closed (`deepreason run` refuses a non-`text`
workload profile; `input freeze` binds one run input; `merge` refuses
`Control` events). Whether that claim is still true on the current tree is
a re-derivation, not an assumption.

Q3: If a second lineage IS reachable, what second question / predicate set
makes cross-lineage reach plausible — "distinct predicates, same domain
family"? The seed's three predicates are the urban-heat-island set;
the sibling must be answerable by artifacts that could satisfy them.

Q4: Does the existing root `40e713b3…` (state=failed,
stop_reason=operational_failure) actually satisfy `deepreason amend`'s
terminal precondition? Epoch 2 of the reach-rich tranche is the candidate;
the brief asserts "state=failed is a typed terminal", and
`deepreason results` reports amend-readiness directly.

## Amendments
(append-only)

### Amendment 1 — 2026-08-22, the launch-boundary fork (QO1) answered

Asked at CHECKLIST.md step 15, after SPEC.md established that the vehicle
R6a names is refused three ways on the root R6a names (M3/M4/M5) and that
the property R1 wants is still deliverable on a new root (M7).

The question put to the operator, verbatim as asked:

> Epoch 3 is built and rehearsed offline. Which road do you want, and I
> need the OLLAMA_API_KEY env file at
> experiments/2026-08-22-change-epoch3-second-lineage/env before anything
> launches.
>
> - Two-phase ladder (recommended): Launch as built: phase 1 (12 cycles),
>   amend to add the second seed lineage, phase 2 (12 cycles). Delivers
>   what you asked for. Cost: one extra qualification battery (~14 min,
>   ~1160 calls) because enabling attached evidence moves the
>   qualification subject. Two independent routes to a reach carrier.
> - Phase 1 only, unchanged manifest: Relaunch the reach-rich design as-is
>   on a retired root: qualification is a cache hit (~1s), no second
>   lineage. The measured evidence says the reach carrier exists in a
>   single-seed run that survives past cycle 2, so this alone may produce
>   reach_set > 0 — but it does not deliver R1.
> - Fix the amend defect first: Stop here and route P1-epoch3
>   (question-only amendment cannot be continued) through the defect
>   workflow before minting anything.

The operator's answer, verbatim:

> "Two-phase ladder (recommended)"

R16 (behavior): the two-phase ladder as built is AUTHORISED to launch —
phase 1 (12 cycles / 200 000 tokens), the amendment adding the second seed
lineage, phase 2 (12 cycles / 200 000 tokens). This settles SPEC.md's QO1
and, with it, deviations D1 (the lineage lands in a new root
`bb0455384ea09b5b…`, not in `40e713b3…`) and D2 (the second lineage's
criteria are inherited, not distinct) — both were stated in the question's
own framing ("Delivers what you asked for", "adds the second seed
lineage") and in PREREG_EPOCH3.md §3, frozen before the question was put.

The re-qualification cost (~14 min, ~1160 calls) is accepted with the
answer, having been priced in the option text.

NOT settled by this answer, and still outstanding: the OLLAMA_API_KEY env
file. The same message asked for it and it has not appeared at
`experiments/2026-08-22-change-epoch3-second-lineage/env`. The ladder's own
first guard exits rc=1 without it (C3: "THE OPERATOR SUPPLIES the
OLLAMA_API_KEY env file at the launch step"), so CHECKLIST.md step 15
remains the tranche's blocker.
