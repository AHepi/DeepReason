# PARKED — Rung 7

Things noticed and NOT fixed here, each with a ready-to-send prompt so the
follow-up costs a paste rather than an authoring session. Nothing on this list
was in Rung 7's scope; a defect found mid-change is parked, never fixed.

## P1 — the epoch3 config dies `operational_failure` at cycle 2, live

**What.** Every live attempt in this tranche — three of them — ran the soak's
own epoch3 configuration and ended `state: failed`, `stop_reason:
operational_failure`, `typed_error: null`, after 2 completed cycles, with 69
accepted and 6 refuted artifacts on the record and **0 tokens** reported
against a 150 000 budget. The cycle soak drives the same shape to cycle 8
against the deterministic stub and passes, so this is a live-only death the
offline instrument does not reach. It did not block Rung 7's gate — the record
it produced was real and the fall staged on it cleanly — but a run that cannot
pass cycle 2 live is not a run anyone can use.

**Prompt:**

> Route through `deepreason-orchestrator`. GOAL: one bounded tranche —
> diagnose why the epoch3 live configuration
> (`experiments/2026-08-22-live-reach-rich-run/run-config.yaml` via that
> tranche's `build_manifest`) ends `operational_failure` at cycle 2 on
> glm-5.2, and fix the cause or record it as typed and expected.
> DIAGNOSIS COMES FROM THE RECORD FIRST, before any code reading: three live
> roots exist under
> `experiments/2026-08-24-change-rung7-wounds-falls-succession/run/`
> (`log.jsonl`, `progress.jsonl`, `run-status.json`, `FINDINGS.md`,
> `TOKEN_ACCOUNTING.json`). Two facts to explain together: the stop is
> `operational_failure` with `typed_error: null`, and `TOKEN_ACCOUNTING`
> reports 0 tokens spent against a 150 000 budget while 69 artifacts were
> accepted. `scripts/cycle_soak.py --case epoch3` drives the SAME shape to
> cycle 8 offline and exits 0, so start by asking what the stub supplies that
> the live provider does not. END STATE: DIAGNOSIS.md naming one primary
> cause with record pointers, a reproduction, and either a fix with its
> regression test or a typed disclosure that says this stop is expected.

## P2 — no live succession has ever happened

**What.** Every succession proof in Rung 7 is offline. No live run has produced
two rival frame assertions on one promotion problem, so the succession pack and
the trial record have never been exercised by a model, and the flip rate has no
measured value on this harness. The instrument reports one on every trial; what
it will say here is unknown. Q2's own number (16–39% top-1 reversal) is from six
open-weight judges on four datasets, not from this tree.

**Prompt:**

> Route through `dr-change-orchestrator`. GOAL: measure this harness's OWN
> succession flip rate, live. Rung 7 shipped the instrument
> (`calculus/succession.py`: `run_succession_trial`, the `succession-trial.v1`
> record, `succession.trial-flip-rate.v1`) and proved every road offline,
> including a constructed order-disagreement case. What is missing is a
> measured number. Stage a live run in which TWO rival frame assertions are
> addressed to one promotion problem so the ordinary discrimination spawn
> fires, let the succession trial run with a judge seat present, and report
> the recorded `flip_rate` across as many trials as the budget allows.
> P1 above may block this: the epoch3 config currently dies at cycle 2 live,
> so fix or characterise that first. JUDGE ON THE TRIAL RECORD ONLY — the
> `flip_rate`, `flips`, `evaluated`, `rubric_pairs_judged` and
> `rubric_pairs_available` fields — never on what the judge said. Compare the
> measured rate against Q2's 16–39% and record the comparison as evidence,
> not as confirmation.

## P3 — a separation lost after consultation is disclosed, never repaired

**What.** Adjudication components only ever grow, so a frame assertion that was
separated from its subject when it was consulted can be UNSEPARATED later. The
frame entry is then silent for it — correctly, since R64 says an unconsultable
assertion moves nothing — and `verify_root`'s `cascade-integrity` limb 3
reports it. Nothing decides what should happen next, and the case has never
been observed on a live root.

**Prompt:**

> Route through `dr-change-orchestrator`. GOAL: decide what a
> separation-lost-after-consultation should DO, beyond being disclosed.
> Rung 7 ships the disclosure only
> (`calculus/standing.py::unseparated_fallen_frames`,
> `invariants.py`'s third `cascade-integrity` limb,
> `tests/test_cascade_integrity.py::test_an_unseparated_fallen_frame_is_disclosed`).
> The open question is whether the problems such an assertion FRAMED while it
> was still separated should be marked when it falls. Arguments exist both
> ways and the tranche did not settle it: they were genuinely framed, and yet
> R64 says an unconsultable assertion moves nothing. START by measuring
> whether the case occurs at all — a census over committed roots for
> assertions in a marking exit grade that fail only the separation condition.
> If the census is empty, the honest outcome is to record that and defer.

## P4 — the SPEC size estimate and the diff-budget gate measure different things

**What.** `SPEC.md` §4 estimated 562 lines by counting the executable lines each
item needs; `tools/diff_budget.py` counts INSERTIONS, which includes every
docstring, comment and blank line. On `calculus/succession.py` the two differ by
90 per cent (241 executable, 458 added). That is the whole of Rung 7's overrun,
and Rung 6 overran for the same reason (759 against 560).

**Prompt:**

> Route through `dr-change-orchestrator`. GOAL: make a tranche's size estimate
> and its size GATE measure the same quantity. Two rungs have now overrun
> their ledgered ceiling for the identical reason — the estimate counts
> executable lines and `tools/diff_budget.py` counts insertions, and this
> repository's own comment convention makes the gap large. Either teach
> `dr-spec-change` to estimate ADDED LINES (and say so in the size table), or
> teach `tools/diff_budget.py` to report both numbers so a ceiling can be set
> against the one it is checking. Prefer the cheaper of the two. Ledger the
> decision in `docs/map/` wherever the ceiling discipline is described, and
> cite Rung 6's Amendment 1 and Rung 7's Amendment 1 as the two recorded
> occurrences.
