# Parked — Rung 2, step 2

## P1 — the premise channel is built but not yet WIRED

**What is built** (`src/deepreason/premises.py`, 17 tests): the attribution and
resolution shapes, the mention-law check, the derived orphan predicate with both
grades, the three resolutions with reversibility, the producer's decision rule,
and the operator's siren case passing end to end.

**What is not**: nothing calls the producer rule yet, so no run will produce an
attribution on its own. Three pieces remain, and they are the ones that touch
running code rather than the channel's own shape:

1. **S3 — the premise rent battery.** A demarcation criterion pinned onto premise
   artifacts requiring a SUBSTANTIVE commitment (reuse
   `measures/reach.py::_substantive`), so a premise that forbids nothing is
   refuted by program. This is what makes the siren case work on a LIVE run
   rather than in a test that refutes the premise by hand. It also needs the
   `crit` half of `active()`, today an unimported stub in
   `measures/demarcation.py` (drift row M-1).
2. **S6b — the wiring.** The critic pack gains the invitation; the scheduler
   consults `premise_work_invited` and deprioritises marked problems and skips
   retired ones. Attention only.
3. **The three detection signals** — problem thrash, attack-target entropy, the
   independence-resolution rate — declared through the Rung 1b-i contract for
   Rung 1b-ii's policy to consume (Amendment 3, R39).

**Why it stopped here.** The channel is a complete, tested, gate-green unit and
the wiring is a separable one. Splitting at this seam keeps a half-finished
scheduler change out of the record.

### Ready-to-send prompt

```
Rung 2 step 2 of the v2 calculus program: wire the premise channel. Route
through dr-change-orchestrator.

READ FIRST: experiments/2026-08-15-change-rung2-premise-channel/SPEC.md
(S3, S6b), docs/map/CON-problem-layer-lifecycle.md, and
src/deepreason/premises.py -- the channel is built and tested; this
tranche connects it.

SCOPE, three parts:
(1) the premise rent battery: a demarcation criterion on premise artifacts
    requiring a SUBSTANTIVE commitment (reuse measures/reach.py::_substantive
    -- structural checks must not satisfy it, per the self-immunisation trap
    in rules/warrants.py::formally_backed). Build the crit half of active();
    measures/demarcation.py is an unimported stub today.
(2) the wiring: critic pack invitation + scheduler consulting
    premise_work_invited, deprioritising marked problems and skipping
    retired ones. ATTENTION ONLY -- no label may move.
(3) declare the three detection signals through the Rung 1b-i contract:
    problem thrash, attack-target entropy, independence-resolution rate.

HARD CONSTRAINTS: no problem is minted from a conjecture's failure (H1 --
failure may redirect attention only); nothing ranks or admits a conjecture
differently for carrying or lacking an attribution; no new LLM role (it
would move every qualification subject digest).

TESTS: the producer fires in an offline run of the actual loop, not just in
a unit test of the rule; a live premise falls by demarcation with no hand
-written refutation; a marked problem is deprioritised and a retired one is
not selected. GATE: full gate 0 failed, docs_verify full, map moves in the
same commit.
```
