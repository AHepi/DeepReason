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
