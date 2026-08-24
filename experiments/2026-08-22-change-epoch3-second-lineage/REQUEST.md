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


### Amendment 2 — 2026-08-23, the budget fork answered after attempt 2

Asked after attempt 2 terminated typed at cycle 0 with `WorkBudgetDenied`,
and after RESULTS.md established the arithmetic: 165 466 logged tokens in
56 calls against a 200 000 phase-1 budget, with the 57th reservation
(~35 700) unable to fit the remaining 34 534.

The question put to the operator, verbatim as asked:

> Phase 1 needs more tokens than the frozen 200,000 split allows. One
> partial cycle cost 165k. How should epoch 3 proceed?
>
> - Single phase, full 400k, cycles=4 (recommended): Drop the second
>   lineage for now. Spend the whole frozen 400,000 bound on one phase with
>   a small cycle budget it can actually finish, so the run reaches
>   'budget_exhausted' via CYCLES — a resumable terminal. Tests the reach
>   hypothesis (measured: a surviving single-seed run does produce
>   foreign-problem carriers) and leaves a root that CAN be amended later.
> - Raise the bound to ~2M tokens, keep 12+12: Keep the two-phase design as
>   frozen but give it fuel matched to the measured burn rate. Delivers the
>   second lineage in one go. Costs roughly 5x the registered bound — your
>   call, since R9 froze it at 400,000.
> - Fix P5-epoch3 first, then relaunch: Route the budget/lifecycle finding
>   through the defect workflow: a token-exhausted run should probably stop
>   resumably instead of being denied. Delays evidence, but makes
>   token-budgeted runs amendable for every future tranche, not just this
>   one.

The operator's answer, verbatim:

> "Single phase, full 400k, cycles=4 (recommended)"

R17 (behavior): epoch 3 runs as a SINGLE phase — `--budget cycles=4
--token-budget 400000`. The registered bound of 400 000 is unchanged and is
no longer split. The second lineage is DEFERRED: the ladder does not amend
in this attempt, and R1 is therefore not delivered by it. R16's
authorization of the two-phase ladder is superseded for execution purposes
by this answer; the amendment vehicle itself is unchanged and still the one
SPEC.md M1/M7 established.

R17a (recorded honestly, not silently absorbed): the option text reasons
that four cycles will be reached and the run will stop `budget_exhausted`
via CYCLES, leaving an amendable root. This tranche's own measurement
predicts otherwise and says so before launching rather than after. Tokens
are charged on ACTUAL usage (165 466 across 56 calls, ~2 955 per call), so
400 000 buys roughly 2.2x the work attempt 2 managed — on the order of 124
calls — while cycle 0 alone consumed at least 56. Four cycles are therefore
unlikely to fit, and the token budget is likely to bind first, which under
P5-epoch3 means `operational_failure` rather than `budget_exhausted`.

That prediction does NOT put the tranche's success criterion at risk. PREREG
SUCCESS is a typed terminal, `verify_root` clean, and `reach_set > 0`; none
of the three requires resumability. Resumability matters only for the
deferred second lineage, which this answer defers anyway. The operator's
instruction is executed as given, with the expected terminal registered in
advance.


### Amendment 3 — 2026-08-24, attempt 4 authorised: depth over frugality

Asked after the soak gate came back clean on this checkout (exit 0, cycle 8
of 8 requested, `verify_root` 0 violations, D4-reservation-bound now PASS)
and before any provider call.

The authorising prompt, verbatim in the parts that bind execution:

> Evidence-minting tranche: reach attempt 4 — soak first, then launch. Both
> cycle-2 killers are fixed and the pre-launch instrument now exists; this
> prompt is the operator's authorization for a fourth attempt.
>
> STEP 2 — PREREG AMENDMENT, ledgered before launch: attempt 4 runs SINGLE
> PHASE, token budget 400000 (R17 unchanged), cycles raised 4 -> 8.
> Authority: SPEC.md M9 — the committed comparison root's carrier appears
> between cycle 2 and cycle 8; a 4-cycle run risks starving the hypothesis
> even while healthy. Operator approval is this prompt.

The operator then supplied the credential mid-session, with the message
(credential redacted; the key itself is never written to a tracked file):

> "here's the API key. unlimited tokens. <OLLAMA_API_KEY>"

That message arrived AFTER the 400 000 bound was written, and it bears on
it, so the fork was put rather than assumed. The question asked, verbatim:

> The soak gate passed clean (exit 0, cycle 8 of 8, replay check green, and
> the reservation-bound seam that killed attempt 3 is now green). Before I
> launch: your prompt froze the token budget at 400,000 with cycles raised
> 4 -> 8, but attempt 3's measured burn was ~55,000 tokens per completed
> cycle, so 400,000 buys roughly 6 cycles, not 8 — and because each call
> books its full completion cap up front, the run would die typed as an
> operational failure around cycle 6 rather than reaching the depth where
> the carrier is expected to appear. Your 'unlimited tokens' message
> arrived after that budget was written. Which budget should attempt 4
> carry?
>
> - Raise to 1,200,000 (Recommended): Enough headroom that the CYCLE budget
>   binds first, so 8 cycles actually complete and the run stops as
>   'budget_exhausted' — a clean, resumable terminal — instead of starving
>   mid-run. Costs more provider tokens; you said tokens are cheap and
>   unlimited. This is the only option that actually gives the registered
>   hypothesis 8 cycles to fire in.
> - Keep 400,000 as frozen: Honours the prompt's written bound exactly.
>   Expected outcome by the measured burn rate: the token budget binds
>   around cycle 6 and the run ends as an operational failure short of
>   cycle 8 — likely a fourth TRUNCATED-BEFORE-CARRIER, i.e. the hypothesis
>   untested again.
> - Raise to 800,000: Middle road: buys roughly 7 cycles by the measured
>   rate, so cycle 8 is still at risk if the burn rate rises in later cycles
>   (which n=1 cannot rule out). Cheaper than 1,200,000, but may repeat the
>   same starvation one cycle later.

The operator's answer, verbatim:

> "Raise to 1,200,000 (Recommended)"

**R18 (behavior).** Attempt 4 runs as a SINGLE phase, `--budget cycles=8
--token-budget 1200000`. The cycle budget is raised from 4 to 8 on the
authorising prompt's own authority (SPEC.md M9: the committed comparison
root's carrier appears between cycle 2 and cycle 8). The token bound is
raised from 400 000 to 1 200 000 on this answer. R17's single-phase shape
and its deferral of the second lineage (`SECOND_LINEAGE=0`) are UNCHANGED;
only the two budget numbers move.

**R18a (what the raise is for, stated so it cannot be re-read later as
generosity).** The registered bound existed to cap spend, not to define the
experiment. Raising it removes the token budget as the thing that ends the
run, so the CYCLE budget binds and the run reaches cycle 8 — the depth at
which SPEC.md M9 measured the carrier in a committed root. A run that dies
of fuel starvation at cycle 6 tests nothing the previous three attempts did
not already fail to test.

**R18b (the prediction registered for this attempt).** At the measured
~55 000 tokens per completed cycle (attempt 3: 109 975 tokens across 49
calls for 2 completed cycles), 8 cycles cost on the order of 440 000
tokens. Against 1 200 000 that is roughly 2.7x headroom, so the CYCLE
budget is expected to bind first and the terminal is expected to be
`completed` / `budget_exhausted` — resumable, therefore amendable later for
the deferred second lineage. If the burn rate rises steeply with depth (n=1
cannot exclude it), the token budget could still bind; that would be
`WorkBudgetDenied`, the shape attempt 2 already recorded, and NOT a fifth
distinct death.

**Scope unchanged.** No `src/` or `tests/` change is authorised by this
amendment, and none is made.
