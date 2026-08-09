# Parked: findings from the two-tier hard question set tranche

Parked 2026-08-09 during the live-pilot phase (CHECKLIST.md steps
19/22). Neither item was fixed here — scope is locked to `src/`,
`tests/`, `tools/` byte-untouched (R18). Both are ready-to-send
prompts for a future `deepreason-orchestrator` runner.

## 1. Transient `foreign-criticism` verify_root violation, clears after one continue

**WHAT:** Both live pilots (Tier V and Tier O, independent runs,
independent questions) showed a `foreign-criticism` violation on
`verify_root`'s FIRST audit — taken right after the initial `reason`
call (10 cycles) — that was fully gone (`replay_valid: true`, 0
violations) by the SECOND audit, taken after one
`continue --budget cycles=2`. Same violation name, same clearing
behavior, reproduced twice on unrelated questions under the same
sole-model/no-seat-flags gemma4:31b configuration.

**Ready-to-send prompt:**

> Route through `deepreason-orchestrator` from `dr-set-goal`. Goal: determine
> whether the `foreign-criticism` verify_root violation observed on early
> audits of two sole-model (gemma4:31b, no `--seat` flags) live runs is a
> genuine timing/ordering artifact of early-stage runs — plausibly because a
> sole-model run has no natural cross-"school" diversity for the
> foreign-criticism-coverage check to draw on until enough cycles have
> accumulated — or a real defect in how
> `foreign-criticism-coverage.v1` (`src/deepreason/verification/report.py`,
> `src/deepreason/scheduler/scheduler.py` ~line 1277-1282) evaluates partial
> runs. Evidence: `experiments/2026-08-09-change-hard-question-set/
> tier-v-audit1.json` vs `tier-v-audit2.json`, and `tier-o-audit1.json` vs
> `tier-o-audit2.json` — same violation on audit1, clean by audit2 in both
> cases, committed run roots at
> `experiments/2026-08-09-change-hard-question-set/pilot-tier-v/runs/
> run-7906485ce1cfc314a653c185cbf61d75` and
> `experiments/2026-08-09-change-hard-question-set/pilot-tier-o/runs/
> run-6bca5a31141b3f0ea6140501146f5646`. End state: either a recorded,
> falsified explanation for why this is expected/benign under sole-model
> operation (and, if so, whether it deserves documentation in
> `docs/map/INV-frozen-surfaces.md` or a seam document so it stops looking
> like a fresh defect on the next sole-model run), or a diagnosed, reproduced
> defect with a proposed fix routed onward through `dr-diagnose` →
> `dr-propose-fix`.

## 2. Criticism that is judged correct does not flip the target's `accepted` status (open question, not an assumed bug)

**WHAT:** In the Tier O pilot's final record
(`experiments/2026-08-09-change-hard-question-set/pilot-tier-o/runs/
run-6bca5a31141b3f0ea6140501146f5646`), `deepreason findings --json`
reports `positions`: 141 accepted, 0 refuted, 0 suspended. Several
`role=conjecturer` artifacts whose `problems` field names the run's
own seed question directly assert the Collatz conjecture IS resolved
(e.g. `3a1b4be2ad92`: "The Collatz conjecture is settled in the
negative: it is fundamentally undecidable because the 3n+1 map can
simulate a Universal Turing Machine."). Separate `role=critic`
artifacts correctly identify several of these as factual errors
(e.g. `8c4b31f0f029`: "This is a factual error; the conjecture is
currently an open problem, and it has not been proven to be
undecidable."). Despite the critic being right, `positions.refuted`
stays empty — the overclaiming artifact's own status is never
flipped. A reader who inspects only `positions.accepted` (as this
tranche's own Tier O hygiene classification does, per PREREG.md) sees
the overclaim standing, indistinguishable from an uncontested claim.

This MAY be intended behavior — CLAUDE.md's own recorded law is "no
warrant, no edge, no REFUTED" (`CON-warrants-and-attacks.md`): informal
prose criticism without a formally wired attack/warrant is not
supposed to change a target's status. This finding does not assume
that law is being violated; it is an open question, not a claimed
defect.

**Ready-to-send prompt:**

> Route through `deepreason-orchestrator` from `dr-set-goal`. Open question,
> not a presumed defect: in
> `experiments/2026-08-09-change-hard-question-set/pilot-tier-o/runs/
> run-6bca5a31141b3f0ea6140501146f5646`, several `role=critic` artifacts
> correctly call out `role=conjecturer` artifacts (which directly target the
> run's own seed question) as factual errors, yet `positions.refuted` is
> empty and the overclaiming artifacts remain in `positions.accepted`
> unqualified. Determine from `CON-warrants-and-attacks.md` and the actual
> event log (`log.jsonl` in that run root) whether this is the intended
> behavior of "no warrant, no edge, no REFUTED" (i.e. these criticisms never
> got wired into a formal attack/warrant, so a status flip was never on the
> table) or a gap where a criticism that IS judged sound by the harness's own
> mechanisms should be — but currently is not — reflected in
> `positions.accepted`/`positions.refuted` for a reader who does not also
> inspect the full criticism graph. If intended: no fix, but consider
> whether `deepreason findings`/`positions.accepted` needs a documented
> caveat, since this tranche's own Tier O hygiene metric (PREREG.md) reads
> `positions.accepted` directly and would misclassify a genuinely
> criticism-defeated overclaim as a standing one. If a gap: diagnose and
> route onward through `dr-diagnose` → `dr-propose-fix`. Directly relevant
> to the operator's own stated motivation for this tranche ("criticism ...
> run under-exercised") — this is the first live evidence of what
> "exercised but not load-bearing" criticism looks like in the typed record.
