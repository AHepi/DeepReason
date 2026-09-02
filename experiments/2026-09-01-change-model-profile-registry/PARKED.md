# Parked — model-profile-registry tranche

Append-only. Each entry: one line of WHAT, then a ready-to-send prompt so the
follow-up costs the operator a paste, not an authoring session. Nothing here is
fixed by this tranche (`dr-change-orchestrator` scope contract, item 2).

Parked at capture (2026-09-01) on the executor window's own instruction
(REQUEST.md C5: "OUT OF SCOPE — parked, not fixed, each has its own tranche").

---

## P1 — F4: one seat's exhaustion kills the whole run, and the failed terminal is not continuable

WHAT: when a single seat exhausts its completion budget the run terminates, and
the terminal it lands in cannot be continued — so the epistemic state built by
every other seat is lost with it. Named as F4 by the P-A1 tranche; out of scope
here because this tranche changes what value a seat SENDS, not what happens when
one dies.

Bears on the 2026-08-29 operator law ("Exhaustion is a clean stop, every stop
secures continuation, and continuation is integrity-gated"), which this
behaviour appears to contradict — that law is the reason this is a defect and
not a design choice.

READY-TO-SEND PROMPT:

```
Route: deepreason-orchestrator (defect family). One goal, one tranche.

GOAL: a single seat exhausting its completion budget must not kill the run, and
whatever terminal the run does reach must be continuable.

The operator's law of 2026-08-29 (CLAUDE.md, verbatim): "clean stop. with an
assurance that continuing is possible. Too often an operational failure
overlooks securing enough checkpoints to allow relaunches or forgets to ensure
continuing is possible that trigger corrupted stops."

EVIDENCE (start at the record, per dr-diagnose — code reading comes second):
- experiments/2026-09-01-live-all-modules-p-a1/ — the P-A1 run, its
  run-status.json, progress.jsonl and MONITOR_REVIEW.md. Finding F4.
- The seat that died there died of the glm-5.3 reasoning-knob defect, which is
  fixed by experiments/2026-09-01-change-model-profile-registry/. Do NOT
  re-diagnose that cause; this tranche is about the CONSEQUENCE — that one
  seat's death is fatal and unrecoverable.

END STATE: DIAGNOSIS.md names one primary cause from the typed record; REPRO.md
demonstrates it offline; the fix makes the terminal continuable (or explains,
against the 2026-08-29 law, why the current terminal is already correct).
```

---

## P2 — F6: the ~300 s transport wall, and blind identical retries in `request_with_retries`

WHAT: at high reasoning effort a glm-5.3 request drops at roughly 300 seconds,
and `src/deepreason/llm/endpoints.py::request_with_retries` responds by
re-sending the identical request — which costs the same 300 seconds again and
fails the same way. Out of scope here: this tranche declares transport quirks in
a profile document, it does not change retry behaviour.

Note the interaction, which is the reason to do this one AFTER the registry
lands: once a profile can declare a transport note, a retry policy has somewhere
to read "this model drops at ~300 s at max effort" from, instead of guessing.

READY-TO-SEND PROMPT:

```
Route: deepreason-orchestrator (defect family). One goal, one tranche.

GOAL: a request that dies at the transport wall must not be retried identically
until the budget is gone.

EVIDENCE (record first):
- experiments/2026-09-01-live-all-modules-p-a1/MONITOR_REVIEW.md — the ~300 s
  drop at max reasoning effort, with seq numbers.
- src/deepreason/llm/endpoints.py::request_with_retries — the retry loop.
- experiments/2026-09-01-change-model-profile-registry/ — the model-profile
  registry, which by then can declare a transport note per model. Read its
  interface before designing: a retry policy that READS a declared transport
  fact is in the spirit of the 2026-08-26 modularity law; one that hard-codes
  300 is the exact thing that tranche retired.

END STATE: the typed record shows a transport-wall failure being handled
differently from an ordinary failure, proven by an offline regression test.
```

---

## P3 — `SPLIT_BUDGET_EXTRACTION_TOKENS` default of 512 is too small for the conjecturer schema

WHAT: the extraction leg's default completion budget is 512 tokens, and the
conjecturer's schema does not reliably fit in it. This is a config-default
question, not a defect in the registry: the window classifies it as "a
config-default question; note it in PARKED.md" (REQUEST.md C5).

Distinguish it carefully from the defect this tranche DOES fix. In P-A1 the 512
cut was the *visible* symptom, but the cause was the reasoning knob: the leg
spent its 512 tokens on thinking prose that should never have been emitted.
Raising 512 would have masked that. Whether 512 is *also* too small once the
thinking prose is gone is a separate, still-open question — and it is open,
not answered, because this tranche is forbidden from running a new live
reasoning run (C5).

READY-TO-SEND PROMPT:

```
Route: dr-change-orchestrator (change family) — this is a configuration
default, not a defect.

OPERATOR QUESTION TO ANSWER FIRST: should the extraction leg's default
completion budget stay at 512 tokens?

EVIDENCE:
- src/deepreason/llm/split.py — SPLIT_BUDGET_EXTRACTION_TOKENS and its use.
- experiments/2026-09-01-live-all-modules-p-a1/MONITOR_REVIEW.md — every
  glm-5.3 extraction blob cut at 512, WITH thinking prose occupying it.
- experiments/2026-09-01-change-model-profile-registry/ — after that tranche the
  thinking prose is gone, so the measurement must be re-taken; the pre-fix
  numbers do not answer this question.

END STATE: a measured answer (how many tokens the conjecturer schema actually
needs, with the reasoning knob correct), and either a changed default or a
recorded decision to keep 512, traceable to that measurement.
```

---

## P4 — the map's seam matrix has no row for `llm x qualification`

WHAT: `docs/map/INDEX.md`'s seam matrix carries no entry for this pair in any
form — not a document, not a "not yet written" dash. By that table's own stated
convention, absence means "no measured import traffic at all", which is a
different claim from "not interesting", and the window's M8 asks for a seam
entry for exactly this pair. Recorded at capture as a map gap
(`dr-drive-harness` §4 step 5: a missing id is a finding, not a blocker).

Whether closing it belongs to THIS tranche or a later one is decided in
`dr-spec-change`, once the reconnaissance says whether the registry actually
creates traffic between the two sides. Parked here so the finding is not lost
if the answer turns out to be "no traffic, no seam needed".

READY-TO-SEND PROMPT (only if dr-spec-change rules it out of this tranche):

```
Route: dr-change-orchestrator (change family). Map-only tranche.

GOAL: docs/map/INDEX.md's seam matrix states the truth about llm x
qualification — either a written SEAM document, or an explicit row recording a
measured zero, per that table's own convention that a dash and an absence mean
different things.

EVIDENCE: docs/map/INDEX.md seam matrix and its closing paragraphs (which
already record two cases — llm x verification and capabilities x channels —
where a low or zero count hid a load-bearing agreement); docs/map/SCHEMA.md for
the authoring contract.

END STATE: docs_verify.py green, INDEX.md routing correct, no code change.
```

---

## P5 — the SAME hard-coded `reasoning_effort: "none"`, in a file this tranche may not touch

WHAT: `src/deepreason/verification/llm_broker.py:225` builds a request body with
`"reasoning_effort": "none"` written directly into the payload dict. It does not
import `llm/providers.py` at all, so it is a SECOND, independent instance of the
exact defect this tranche was opened to fix — and the registry does not reach it.

Parked, not fixed, for one reason only: `verification/` is frozen surface 3
(`docs/map/INV-frozen-surfaces.md:47`, "Replay-validation record formats —
`invariants.py`, `verification/`"), and this tranche's authorization says
"qualification.py (surface 5), capabilities/state.py, harness.py, invariants.py,
verification/, and the frozen-adjacent route_fingerprint in llm/firewall.py: NOT
touched. Any contact is an immediate stop." So it was found, verified
first-hand, and left exactly as it is.

Found by an independent reconnaissance pass, not by the change itself — the
blast-radius gate could not see it either, because the file names neither
`REASONING_OFF` nor `providers`. It is a literal in a dict.

WHAT IT MEANS, honestly. This is the brokered verification path, not the
reasoning engine: `deepreason reason` does not route through it. So the three
runs that died are not attributable to this line. But it is the same mistake in
the same repo, it will behave the same way on glm-5.3 (contaminated content
rather than disabled thinking), and it is invisible to the registry that now
governs every other seat.

READY-TO-SEND PROMPT:

```
Route: dr-change-orchestrator (change family). One goal, one tranche.

GOAL: src/deepreason/verification/llm_broker.py stops hard-coding
"reasoning_effort": "none" into its request body, and reads the model's own
document like every other seat does.

FROZEN SURFACE — READ FIRST, THIS IS THE WHOLE DIFFICULTY. verification/ is
frozen surface 3 (docs/map/INV-frozen-surfaces.md:47). This tranche therefore
CANNOT begin with an edit. It begins with a priced stop:

1. Run tools/blast_radius.py --files src/deepreason/verification/llm_broker.py
   --symbols <the payload builder> and paste its frozen_surface_contacts list
   verbatim into SPEC.md.
2. Price what actually moves. The frozen claim about verification/ is about
   REPLAY-VALIDATION RECORD FORMATS. A request-body literal is arguably not a
   record format at all — but that argument is exactly what an operator grant
   is for, and it must be made in writing with a measurement, not asserted.
   The template is experiments/2026-09-01-defect-judge-canary-compile-gap/
   price_compile_gap.py and the granted-contact blocks at
   docs/map/INV-frozen-surfaces.md:546-669.
3. STOP and put the priced grant request to the operator. Do not edit first.

CONTEXT AND THE INTERFACE TO USE:
- experiments/2026-09-01-change-model-profile-registry/ — the registry, its
  declared interface (deepreason.model_profiles.resolve), and
  docs/map/CON-model-profiles.md. Reach it through the interface only; the
  architecture test in tests/test_model_profile_registry.py goes red otherwise.
- glm-5.3's own document, docs/model-profiles/glm-5.3/agent.md, records why
  "none" is the wrong value on that model: 0/8 clean content against 8/8 at
  "low".

END STATE: either the literal is gone and the broker reads the registry, with an
operator grant recorded in INV-frozen-surfaces.md the way the 2026-08-30 and
2026-09-01 grants are; or a written finding that the grant was refused and the
literal stays, with the reason. Not silence.
```

---

## P6 — the operational wheel smoke is red at `continuation_resume`, and nothing runs it

WHAT: `python -u scripts/wheel_operational_smoke.py` fails at
`"stage":"continuation_resume"` with `"failure_kind":"assertion_failed"` and a
payload whose every observation is `not_observed`/`null`. It fails IDENTICALLY
on the pre-tranche base `dd0916fb5`, so it is not this tranche's doing — and no
gate runs it, which is why it can sit red without anyone noticing.

Found because this tranche runs the smokes by checklist step rather than by
habit: `dr-drive-harness` §4 calls them "the third instrument, which NO gate
runs for you". Its sibling `scripts/wheel_smoke.py` passes.

Not fixed here: the failure is in the continuation lifecycle, which this
tranche does not touch, and diagnosing it is a defect tranche's work.

READY-TO-SEND PROMPT:

```
Route: deepreason-orchestrator (defect family). One goal, one tranche.

GOAL: `python -u scripts/wheel_operational_smoke.py` exits 0, or its failure is
diagnosed and recorded as a known limitation of this container with a check
that says so.

WHY IT MATTERS MORE THAN IT LOOKS: no gate runs this instrument
(dr-drive-harness section 4), so a red here is invisible until someone runs it
by hand. It pins the public operational surface over the INSTALLED wheel --
lifecycle, terminalization, continuation, MCP -- which the ordinary pytest gate
does not exercise at all.

EVIDENCE (record first, per dr-diagnose):
- The failure payload is `deepreason-wheel-operational-failure-v4`, printed as
  a single ::error line. `"stage":"continuation_resume"`,
  `"failure_kind":"assertion_failed"`, and every lifecycle observation
  `not_observed` -- so the assertion fired before anything was recorded. Start
  by finding WHICH assertion: scripts/wheel_operational_smoke.py around
  2119-2143 carries five candidates, all about `deepreason continue`.
- Reproduced on the pre-tranche base:
  experiments/2026-09-01-change-model-profile-registry/BASELINE.txt addendum 2.
- Bears on the operator's 2026-08-29 law ("every stop secures continuation"):
  if continuation really is broken over the installed wheel, that law is not
  being met on the shipped surface.

END STATE: either the smoke exits 0, or a recorded diagnosis naming the cause
with a committed regression test, plus a decision about whether a gate should
run this instrument at all.
```

---

## P7 — a document edited mid-run changes behaviour the run's own stamp denies

WHAT: `model_profiles.resolve` re-reads the documents directory on every split
plan, while `scheduler._record_module_fingerprints` stamps the registry ONCE at
run start. So editing an `agent.md` while a run is in flight changes what later
emission legs send, and the run's record still carries the digest of the
document that existed at cycle 0. The record would be describing a run that did
not happen.

Noticed while building this tranche, not requested by any requirement, and
deliberately not fixed: the fix is a caching or freezing decision with real
semantics to choose between, and choosing it inside a tranche that was not
asked to would be scope creep.

It is not a live problem today — nothing edits these files during a run, and a
human would have to do it deliberately — which is exactly why it should be
closed before someone does.

READY-TO-SEND PROMPT:

```
Route: dr-change-orchestrator (change family). One goal, one tranche.

GOAL: a run's model profiles are FIXED for the life of the run, and the digest
its record stamps is provably the one every seat actually used.

THE CHOICE TO MAKE, which is the whole tranche:
(a) Freeze at run start -- resolve every profile once, carry the frozen set,
    and let a mid-run edit take effect on the NEXT run. Matches how the split
    plan itself is frozen ("the division happens once, before the first leg is
    sent") and how the manifest freezes a configuration.
(b) Re-read every time and stamp every time, so the record carries every
    version that was in force. Honest but noisy, and it makes a run's
    behaviour depend on a file nobody versioned.
Recommendation is (a); the operator's 2026-08-28 law ("behaviour path should be
deterministic, yet also configurable") points the same way -- deterministic
GIVEN a configuration, configurable BETWEEN runs.

EVIDENCE: src/deepreason/model_profiles/registry.py (`_load` runs per call);
src/deepreason/scheduler/scheduler.py::_record_module_fingerprints (stamps
once); docs/map/CON-model-profiles.md for the interface the fix must not widen.

END STATE: a test that edits a document mid-run and proves the run's behaviour
did not change, plus the map document updated in the same commit.
```
