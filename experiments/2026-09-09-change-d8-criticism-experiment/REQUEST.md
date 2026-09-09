# Request: "do it" — does criticism, once connected and allowed to bite, make the harness's output materially better than the plain model?

Captured: 2026-09-09, executor window opening message (the monitor's brief),
carrying the operator's one-word authority for the experiment it proposes.

## Verbatim

### The operator's authority (2026-09-09)

> do it

Stated in answer to the monitor's proposal, which the executor window's brief
reproduces below. No other operator words were given for this tranche at
capture time.

### The monitor's brief, verbatim (the executor window's opening message)

> Setup FIRST: `git fetch origin main && git checkout -B claude/<your-branch-name> origin/main`. Confirm on this head that `pytest tests/test_organiser_seat.py -q` is green and that `docs/map/INV-frozen-surfaces.md` carries the 2026-09-09 verification grant (both landed by earlier windows; if either is missing, stop and say so). Preflight: `which deepreason || pip install -e . --break-system-packages -q`, plus `python -m pip install pytest pytest-xdist jsonschema --break-system-packages -q`, then `deepreason embedder-warmup`. THEN read CLAUDE.md from this checkout in full (every operator design law binds — the success law of 2026-09-03, the ungated-seats law, the judge law as amended; the MANDATORY block at the top binds you), read `.claude/skills/pinker-write-for-readers/SKILL.md` directly with the Read tool and follow it for every message, and read `.claude/skills/README.md` and `.claude/skills/dr-drive-harness/SKILL.md`.
>
> EXECUTOR WINDOW — EXPERIMENT: does criticism, once connected and allowed to bite, make the harness's output materially better than the plain model? Route through `dr-change-orchestrator` starting with `dr-capture-request`. The operator's words, the authority: "do it" (2026-09-09), answering the monitor's proposal below. Cite in REQUEST.md the audit that motivates it: `experiments/2026-09-08-audit-llm-capabilities/AUDIT_REPORT.md` §2.3a (0 of 196 model-written attacks ever shown to the next conjecturer in the two roots examined; every status change from mechanical verdicts), §3.5 (four losses to the plain model, all with criticism disconnected or observe-only), §5.1 gap 3 (the four-arm design), §5.2 (run-to-run variance comparable to every reported effect — ERRATA E78). Read those sections, `experiments/2026-08-26-run-anatomy-w2/` (the placebo-column method you must copy), `docs/map/CON-warrants-and-attacks.md`, `CON-evidence-states.md`, `CON-criticism-source.md`, and `src/deepreason/config.py` lines 505-548 (`ARGUMENTATIVE_AUTHORITY`: `observe_only` default, `trial_required`, `single_family_trial`; `ADJUDICATION_STATUS_AUTHORITY_ENABLED`).
>
> THE DESIGN (SPEC.md refines it; it does not shrink it). One question — the D8 question, frozen input `experiments/2026-09-05-change-mini-isolation-programme/runs/input-d8` — one model (the harness's current model, every seat), matched token budget per harness run (500 000, the figure the operator set), four arms:
>   ARM 0 — plain repeated sampling, no harness, spend matched to a harness run by number of calls (report the actual spend; unused allowance is reported, never padded).
>   ARM C — the harness as it ships: default conjecturer and critic shells, criticism rendered to the next candidate through the open-criticisms section (VERIFY on the record, per call, via the section-plan receipts that `dr.open-criticisms` rendered, as the monitor verified on the organiser run: 9 of 11), `ARGUMENTATIVE_AUTHORITY=observe_only`.
>   ARM V — identical to ARM C except the critic seat's output is VACUOUS: objections of matched length and count carrying no content about the target. Price two roads and pick one: (a) bind the critic role to a local deterministic endpoint (the soak's stub, `scripts/cycle_soak.py` "redirecting every role to the stub" shows how one role is redirected) that returns generic objections drawn from a fixed bank, length-matched to ARM C's; (b) a registered critic shell whose wording asks for generic, target-free objections. Prefer (a): a stub carries no information by construction; a model asked to be vacuous may not comply. Whichever road, prove offline on a stub root that ARM V's objections reach the next candidate exactly as ARM C's do (same section, same disposition) and that they name nothing specific about their targets.
>   ARM A — identical to ARM C with authority GRANTED: `ARGUMENTATIVE_AUTHORITY=single_family_trial` (the solo-model road the 2026-08-09 law requires to exist) and `ADJUDICATION_STATUS_AUTHORITY_ENABLED=true`, with the typed warning any switched gate emits captured on the record. If the ungated-seats law's switches do not reach a managed run (the 2026-08-28 audit's P10), STOP and say so before launch.
>   REPEATS: every harness arm runs TWICE (E78: the control alone ranged 4.71–6.70 of 15 across identical inputs), so eight harness runs plus ARM 0; a second run of the same question and config would be refused as RUN_ALREADY_STARTED — vary ONLY a declared nonce in the configuration or the home, disclose it, and confirm it moves nothing else (read `docs/map/CON-run-identity.md`). Batteries: one per home whose configuration moves the qualification subject digest; count them in the plan.
>
> MEASUREMENT, pre-registered and sealed by sha256 before any live call (PREREG.md; follow the organiser tranche's PREREG Amendments 7–9 and PREREG_D8 for form; P11 of the mini programme for the unit): the judged unit is each run's composed result (`experiments/2026-09-06-change-writers-room-organiser-testing/tools/compose_result.py`, copied); ARM 0's units are its essays. Judging by blind pairwise forced choice with position swap, three judges, the D8 criteria as the standard (`tools/judge_pairwise.py` from the organiser tranche, copied; CRITERIA byte-identical, checked by diff) — the length rule (1.5×) applied to the verdict AND the raw consistent-win share reported beside it, since a composed unit is expected to be several times an essay's length and the rule will likely NULL any win; register that in advance and ALSO register the secondary comparison the length rule cannot defeat: per-position units (each surviving position as a unit) against the bare essays' matched-length sections, if the composer can emit them deterministically — if it cannot, say so and do not build it here. The pairwise comparisons that answer the question: C vs 0, V vs 0, C vs V (criticism's content, the arm that makes this a measurement of criticism), A vs C (authority), A vs 0. Decision rule: consistent-win share ≥ 2/3 BETTER, ≤ 1/3 WORSE, between NULL; a failed arm INCONCLUSIVE, and with two runs per arm the verdict is reported per pair of runs, never pooled into a win. Copy W2's placebo discipline for the coupling measure: for every criticism, compute whether the candidate AFTER it changed and whether the candidate BEFORE it changed, and report only the difference; report, from the record, attack edges minted, warrants by road (demonstrative / argumentative), refutations, evidence states (open / supported / refuted / contested) per arm. Write the whole plan as a claims file for `tools/record_claims.py` (every prediction a claim; "not shown able to fail" standing required).
>
> RUN DISCIPLINE: `python -u scripts/cycle_soak.py --case <the launch shape>` green per configuration before launch; env file discipline (`git check-ignore`, `chmod 600`, never commit or echo; absent → stop); launch each arm detached with the snapshot loop; monitor `progress.jsonl` and `rc=`; typed outcomes only; one relaunch per arm for a transport death before cycle 1 completed; failure budget 8 live calls beyond the plan, S6-style ledger; every root committed whole. RESULTS.md as an honest ledger: what ran, the record-derived criticism table per arm (did criticism reach the next candidate, did it bite), the pairwise tables, verdicts in the rule's words, the claims file's output, spend per arm, and the residue (one question, one model, two runs per arm, same-model judges, the length ceiling).
>
> Scope, hard: `src/`, `mini/` byte-untouched; if any arm needs a code change to exist (a stub route binding that does not exist, a switch that does not reach the run), STOP at SPEC.md with the smallest priced change and the frozen-surface reading — do not build it here. Tests only for the tranche's own tools. No gate run unless a file under `tests/` changed. Park everything else. Deliver through `dr-validate-change` and `dr-deliver-change` with the R-by-R table. Commit and push at every phase boundary and every `rc=` line with retry (2s/4s/8s/16s).  Stop when delivered and pushed.

### The operator's second message in this window (2026-09-09, mid-turn)

> df5fdd8c16284bd5b6787ed623194a62.InAzwc_cCUuQOsOU82TFPuxd
>
> API key

Handled as a credential, not as a requirement: written to
`experiments/2026-09-09-change-d8-criticism-experiment/env` as
`OLLAMA_API_KEY=...`, `chmod 600`, confirmed gitignored by
`git check-ignore -v` (rule `.gitignore:50 experiments/**/env`), never
committed and never echoed. Recorded here as C7 below.

## Requirements

R1 (process): "Route through `dr-change-orchestrator` starting with `dr-capture-request`."
R2 (artifact): "Cite in REQUEST.md the audit that motivates it: `experiments/2026-09-08-audit-llm-capabilities/AUDIT_REPORT.md` §2.3a ... §3.5 ... §5.1 gap 3 ... §5.2 (run-to-run variance comparable to every reported effect — ERRATA E78)."
R3 (process): "Read those sections, `experiments/2026-08-26-run-anatomy-w2/` (the placebo-column method you must copy), `docs/map/CON-warrants-and-attacks.md`, `CON-evidence-states.md`, `CON-criticism-source.md`, and `src/deepreason/config.py` lines 505-548".
R4 (behavior): "One question — the D8 question, frozen input `experiments/2026-09-05-change-mini-isolation-programme/runs/input-d8` — one model (the harness's current model, every seat), matched token budget per harness run (500 000, the figure the operator set), four arms".
R5 (behavior): "ARM 0 — plain repeated sampling, no harness, spend matched to a harness run by number of calls (report the actual spend; unused allowance is reported, never padded)."
R6 (behavior): "ARM C — the harness as it ships: default conjecturer and critic shells, criticism rendered to the next candidate through the open-criticisms section (VERIFY on the record, per call, via the section-plan receipts that `dr.open-criticisms` rendered, as the monitor verified on the organiser run: 9 of 11), `ARGUMENTATIVE_AUTHORITY=observe_only`."
R7 (behavior): "ARM V — identical to ARM C except the critic seat's output is VACUOUS: objections of matched length and count carrying no content about the target."
R8 (process): "Price two roads and pick one: (a) bind the critic role to a local deterministic endpoint (the soak's stub ...) that returns generic objections drawn from a fixed bank, length-matched to ARM C's; (b) a registered critic shell whose wording asks for generic, target-free objections. Prefer (a): a stub carries no information by construction; a model asked to be vacuous may not comply."
R9 (behavior): "Whichever road, prove offline on a stub root that ARM V's objections reach the next candidate exactly as ARM C's do (same section, same disposition) and that they name nothing specific about their targets."
R10 (behavior): "ARM A — identical to ARM C with authority GRANTED: `ARGUMENTATIVE_AUTHORITY=single_family_trial` ... and `ADJUDICATION_STATUS_AUTHORITY_ENABLED=true`, with the typed warning any switched gate emits captured on the record."
R11 (process): "If the ungated-seats law's switches do not reach a managed run (the 2026-08-28 audit's P10), STOP and say so before launch."
R12 (behavior): "REPEATS: every harness arm runs TWICE ..., so eight harness runs plus ARM 0".
R13 (behavior): "a second run of the same question and config would be refused as RUN_ALREADY_STARTED — vary ONLY a declared nonce in the configuration or the home, disclose it, and confirm it moves nothing else (read `docs/map/CON-run-identity.md`)."
R14 (artifact): "Batteries: one per home whose configuration moves the qualification subject digest; count them in the plan."
R15 (artifact): "MEASUREMENT, pre-registered and sealed by sha256 before any live call (PREREG.md; follow the organiser tranche's PREREG Amendments 7–9 and PREREG_D8 for form; P11 of the mini programme for the unit)".
R16 (behavior): "the judged unit is each run's composed result (`experiments/2026-09-06-change-writers-room-organiser-testing/tools/compose_result.py`, copied); ARM 0's units are its essays."
R17 (behavior): "Judging by blind pairwise forced choice with position swap, three judges, the D8 criteria as the standard (`tools/judge_pairwise.py` from the organiser tranche, copied; CRITERIA byte-identical, checked by diff)".
R18 (behavior): "the length rule (1.5×) applied to the verdict AND the raw consistent-win share reported beside it ...; register that in advance".
R19 (behavior): "ALSO register the secondary comparison the length rule cannot defeat: per-position units (each surviving position as a unit) against the bare essays' matched-length sections, if the composer can emit them deterministically — if it cannot, say so and do not build it here."
R20 (behavior): "The pairwise comparisons that answer the question: C vs 0, V vs 0, C vs V (criticism's content, the arm that makes this a measurement of criticism), A vs C (authority), A vs 0."
R21 (behavior): "Decision rule: consistent-win share ≥ 2/3 BETTER, ≤ 1/3 WORSE, between NULL; a failed arm INCONCLUSIVE, and with two runs per arm the verdict is reported per pair of runs, never pooled into a win."
R22 (behavior): "Copy W2's placebo discipline for the coupling measure: for every criticism, compute whether the candidate AFTER it changed and whether the candidate BEFORE it changed, and report only the difference".
R23 (artifact): "report, from the record, attack edges minted, warrants by road (demonstrative / argumentative), refutations, evidence states (open / supported / refuted / contested) per arm."
R24 (artifact): "Write the whole plan as a claims file for `tools/record_claims.py` (every prediction a claim; 'not shown able to fail' standing required)."
R25 (process): "`python -u scripts/cycle_soak.py --case <the launch shape>` green per configuration before launch".
R26 (process): "env file discipline (`git check-ignore`, `chmod 600`, never commit or echo; absent → stop)".
R27 (process): "launch each arm detached with the snapshot loop; monitor `progress.jsonl` and `rc=`; typed outcomes only".
R28 (process): "one relaunch per arm for a transport death before cycle 1 completed; failure budget 8 live calls beyond the plan, S6-style ledger; every root committed whole."
R29 (artifact): "RESULTS.md as an honest ledger: what ran, the record-derived criticism table per arm (did criticism reach the next candidate, did it bite), the pairwise tables, verdicts in the rule's words, the claims file's output, spend per arm, and the residue (one question, one model, two runs per arm, same-model judges, the length ceiling)."
R30 (process): "Scope, hard: `src/`, `mini/` byte-untouched; if any arm needs a code change to exist (a stub route binding that does not exist, a switch that does not reach the run), STOP at SPEC.md with the smallest priced change and the frozen-surface reading — do not build it here."
R31 (process): "Tests only for the tranche's own tools. No gate run unless a file under `tests/` changed. Park everything else."
R32 (process): "Deliver through `dr-validate-change` and `dr-deliver-change` with the R-by-R table."
R33 (process): "Commit and push at every phase boundary and every `rc=` line with retry (2s/4s/8s/16s). Stop when delivered and pushed."

## Standing constraints

C1: "do it" — the operator, 2026-09-09. The whole authority for running this
    experiment; every design choice below traces to the monitor's brief, which
    that word approved.
C2: "SPEC.md refines it; it does not shrink it" — the brief, on THE DESIGN.
C3: "the figure the operator set" — 500 000 tokens per harness run, the
    matched budget (the brief attributes the number to the operator).
C4: "STOP and say so before launch" — the brief, on the P10 switch-reachability
    question (R11), and "STOP at SPEC.md with the smallest priced change and
    the frozen-surface reading" on any needed code change (R30). Both are hard
    stops in the orchestrator's sense: a committed document and an ended turn.
C5: CLAUDE.md's MANDATORY block, binding on this window: "Never verify a review
    without the operator's explicit permission." This tranche is not a review,
    so its own instruments run — but no review, audit, or verdict task inside
    it may run a verification instrument.
C6: CLAUDE.md's success law, 2026-09-03, verbatim: "a complete answer isn't the
    goal. Neither is correctness. The condition of success it something
    materially better than what's produced without it." This experiment IS a
    direct measurement of that law's criterion; ARM 0 is the baseline the law
    requires.
C7: The operator's API key, sent mid-window 2026-09-09, is a credential:
    written to the tranche's gitignored `env` at mode 600, never committed,
    never echoed. If it were absent, R26 says stop.
C8: CLAUDE.md Conventions, 2026-09-03: no terms of art in operator-facing
    prose; one closing analogy on the final message only.

## The motivating audit (R2), quoted from the record

`experiments/2026-09-08-audit-llm-capabilities/AUDIT_REPORT.md`:

- **§2.3a** — "**0 of 196 model-written attacks were ever exposed to a later
  conjecture dispatch.** Not a low rate — zero." And: "Every status any
  criticism moved was moved by the problem's own admission criteria. All 118
  attack edges in one root and all 345 in the other come from demonstrative
  warrants minted by mechanical commitment verdicts; **0 come from a
  model-written attack**". The section's own conclusion: "Every statement in
  this report about what criticism did or did not achieve should be read as a
  statement about criticism that could not have achieved anything."
  It also carries the placebo table this tranche must copy (R22): each rate
  computed once on the candidate AFTER the criticism and once on the candidate
  BEFORE it, "The difference is the only evidence", with three of four
  placebo-corrected effects zero or negative.
- **§3.5** — "in this record there is no measured case of the harness making
  the model's output better than the model alone, and four cases of it not
  doing so": construction (harness 0.0004075 vs plain 0.0135949), composition
  (mini D8: three plain calls 15/15 median, harness best candidate 10, mean
  5.62, at 7.6× the spend, verdict INDISTINGUISHABLE), the 2026-07
  rank-concentration experiment ("the criticism/adjudication apparatus showed
  NO measurable quality advantage over raw generation + self-selection on
  these informal problems — and lost outright on one"), and the P-C2b
  reasoning-on rematch (4% against the harness at a budget match of 1.0248).
  All four with criticism disconnected or observe-only.
- **§5.1 gap 3** — "**Whether criticism improves anything.** Worse than
  unmeasured. ... *Missing:* one question, matched budget, four arms — plain
  repeated sampling; generation with criticism actually rendered into the next
  dispatch; generation with an equal quantity of vacuous criticism; and the
  same with authority granted — judged blind with length held constant, with
  W2's before-and-after placebo column computed. The vacuous arm is what turns
  a pipeline comparison into a measurement of criticism; the rendering is what
  makes the comparison mean anything at all." This tranche is that gap.
- **§5.2** — "**Run-to-run variance is comparable to every effect the corpus
  reports.**" `docs/ERRATA.md` E78: across three paired runs with every input
  identical, the control arm alone ranged 314,220–541,666 tokens and 4.71–6.70
  judged of 15, "a run-to-run spread comparable to every between-arm difference
  the experiment has reported." This is why R12 requires two runs per arm and
  R21 forbids pooling.

## Map preflight — the ids this work resolves to

Read in the fixed order (`dr-drive-harness` §4): `INDEX.md`, then
`INV-frozen-surfaces.md`, then the seam before either side.

| id | why it is in scope |
|---|---|
| `DR-CON-criticism-source` | the socket ARM V replaces and ARM A grants authority to; `_resolve_authority`/`_TRIAL_MODES`, `_observe_case`'s `["scrutiny", target, critic]` Measure |
| `DR-CON-discharge-channel` | the mechanism that makes ARM C's criticism reach the next candidate at all — the `open-criticisms` pack section, ON by default since 2026-08-26 |
| `DR-CON-authority` | the two authority vocabularies; what `single_family_trial` means and who may move a Status |
| `DR-CON-warrants-and-attacks` | "no warrant, no edge, no REFUTED" — the chain R23 counts per arm |
| `DR-CON-evidence-states` | the four derived readings R23 reports (open / supported / refuted / contested) |
| `DR-CON-run-identity` | R13's nonce question: what moves a run id and what a leftover root refuses |
| `DR-CON-configuration-stages` | R11's question: where a switch is lost between the configuration file and the seat |
| `DR-CON-seats` | one model in every seat (R4); `select_lease`, one-profile-per-run |
| `DR-SEAM-adjudication-x-authority` | ARM A's seam: granting authority is a change of what may move a Status |
| `DR-INV-frozen-surfaces` | read BEFORE designing (R30's frozen-surface reading); qualification subject digests bear on R14 |
| `DR-SUB-rules`, `DR-SUB-adjudication`, `DR-SUB-manifest`, `DR-SUB-application` | the sides the above seams join; `start_manifest_run` is the one run path |

No map document is MODIFIED by this tranche: R30 holds `src/` and `mini/`
byte-untouched, so nothing the map describes changes. Map documents are read
here as authorities, and any `Verified-at:` stamp stays where it is.

## Open questions (for dr-spec-change)

Q1: Does the brief's ARM A switch pair actually reach a managed run on this
    head? R11 makes the answer a hard stop if it does not. The 2026-08-28 audit
    P10 says five switches were silently reverted by the manifest echo;
    `DR-CON-discharge-channel` records that ONE such field (`DISCHARGE_POLICY`)
    was given a carriage road on 2026-08-29 while the general defect stayed
    open. Which of the two switches R10 names travels, and by which road, is a
    record question to settle before launch.
Q2: Is ARM V's road (a) reachable without a code change? The brief prefers the
    stub-bound critic role, and R30 forbids building a route binding that does
    not exist. Whether `Config.roles` already admits a per-role endpoint that
    points at a local stub, and whether the soak's stub can serve the critic
    contract, decides between road (a), road (b), and a stop.
Q3: Can `compose_result.py` emit per-position units deterministically? R19
    conditions the secondary comparison on exactly this, and says to record the
    negative rather than build it.
Q4: What is the nonce road that varies a run id and nothing else (R13)? A
    declared configuration field, a distinct `DEEPREASON_HOME`, or a question
    suffix are three candidates with different costs — the question suffix
    changes the input, which R4 forbids.
Q5: How many qualification batteries does the plan cost (R14)? One per home
    whose configuration moves the subject digest, at ~14 minutes and ~1160
    calls each; the answer depends on whether the ARM V and ARM A switches sit
    inside the subject digest.
Q6: Is ARM 0's spend match "by number of calls" (the brief's words in R5)
    computable before the harness arms run, or does ARM 0 run last? The brief
    matches by call count, so the harness arms' call counts must exist first.

## Amendments

(append-only; later operator messages land here as R34... or
"R2a supersedes R2", each with its verbatim quote)

### Amendment 1 (2026-09-09) — the operator answers SPEC.md's two questions

Received after SPEC.md was committed and pushed (commit `7fd80663a`) and the
STOP was presented. Verbatim, both answers in one message:

> Q-OP1: Road A-cross. Keep every generating seat on the one model and give the
> JUDGE role a two-seat cross-family ensemble with
> ARGUMENTATIVE_AUTHORITY=trial_required, exactly as you priced it. Disclose the
> deviation from the one-model rule in PREREG and confine it to the seats that
> adjudicate, so the conjecturer and critic in ARM A stay byte-identical to ARM
> C. Zero lines under src/. Your PARKED P1 (the solo road the 2026-08-09 law
> requires does not reach a run) stays parked as its own defect window; do not
> build it here.
>
> Q-OP2: Split. Tranche 1: every instrument, the offline proofs, the soaks,
> PREREG.md sealed, no live call. Deliver and stop; the launches are tranche 2
> in this same window after the monitor has read tranche 1.

New requirements, numbered from R34:

R34 (behavior): "Road A-cross. Keep every generating seat on the one model and
    give the JUDGE role a two-seat cross-family ensemble with
    ARGUMENTATIVE_AUTHORITY=trial_required, exactly as you priced it."
    **SUPERSEDES R10's** `single_family_trial` and its
    `ADJUDICATION_STATUS_AUTHORITY_ENABLED` half is RETAINED (the master gate
    is still required for any trial mode to take effect —
    `rules/crit.py::_authority`). R10 is marked `superseded-by:R34` for the
    authority mode only; its "with the typed warning any switched gate emits
    captured on the record" clause stands unchanged.
R35 (artifact): "Disclose the deviation from the one-model rule in PREREG and
    confine it to the seats that adjudicate, so the conjecturer and critic in
    ARM A stay byte-identical to ARM C." Amends R4's "one model ... every
    seat": the generating seats stay one model; the judge seats do not, and
    the deviation is disclosed rather than hidden.
R36 (process): "Zero lines under src/." Restates and hardens R30 — no
    exception is granted by this amendment.
R37 (process): "Your PARKED P1 (the solo road the 2026-08-09 law requires does
    not reach a run) stays parked as its own defect window; do not build it
    here."
R38 (process): "Split. Tranche 1: every instrument, the offline proofs, the
    soaks, PREREG.md sealed, no live call."
R39 (process): "Deliver and stop". Tranche 1 ends at `dr-deliver-change` with
    the R-by-R table; R33's "Stop when delivered and pushed" applies to
    tranche 1's delivery.
R40 (process): "the launches are tranche 2 in this same window after the
    monitor has read tranche 1." Tranche 2 does not begin in this turn and does
    not begin unprompted.

Standing constraint added:

C9: "no live call" (R38) is an absolute bound on tranche 1. Every instrument
    is proven against the deterministic stub, a committed root, or a fixture —
    never against the provider. The credential stays in place for tranche 2
    and is not read by anything tranche 1 runs.


### Amendment 2 (2026-09-09) — the operator rules on the budget stop

Received after step 17 committed the EXCEEDED verdict (4 498 of 4 400) and the
stop was presented with three priced options. Verbatim, in full:

> Raise.

R41 (process): "Raise." The ceiling is corrected once more rather than the
    tranche being split again or its documents trimmed. SUPERSEDES the
    self-imposed rule this window wrote into SPEC.md Amendment 2 — "a third
    amendment to this number would be the S5 failure arriving one step later
    than usual". That sentence was this window's own caution, not an operator
    law, and the operator has overruled it with the overrun's two measured
    causes in front of them. It is recorded rather than deleted: the caution
    was right to fire, and the decision to override it is the operator's to
    take and is now on the record as theirs.
    R38's tranche-1 boundary is untouched — the raise buys lines, not live
    calls, and C9 (no live call in tranche 1) still binds.
