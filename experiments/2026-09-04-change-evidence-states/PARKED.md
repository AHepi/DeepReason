# Parked — found during the evidence-states tranche, not fixed here

One tranche, one goal (CLAUDE.md). Each entry costs the operator a paste.

---

## P1 — the signal-registry gate cannot see a signal emitted through a constant

WHAT. `tests/test_signals.py::test_every_emitted_signal_is_registered` is the
gate that stops an undeclared measure tag reaching the record. Its AST scan
(`_emitted_signals`) only recognises a LITERAL head at a `record_measure`
call site: `record_measure(inputs=["some-tag", ...])`. A signal emitted through
a named constant — `record_measure(inputs=[SOME_SIGNAL, ...])`, which is the
shape every recent typed channel uses (`seat.retired.v1`, and this tranche's
`criticism.dispatch.v1`) — is invisible to it. The gate passes; the registry
silently omits the signal; `deepreason results`' signal counters and
`signals.describe` then report it as unregistered at read time.

Measured here: `criticism.dispatch.v1` was emitted from
`src/deepreason/runtime/criticism_dispatch.py` and `pytest tests/test_signals.py
-q` reported 9 passed with the signal undeclared. It was declared anyway (per
`docs/map/REC-add-signal.md`) and pinned by an assertion inside this tranche's
own test, so THIS signal is covered — but the hole is general and the next
channel will fall in it.

NOT FIXED HERE because widening a shared gate's scanner is a change to an
instrument every tranche depends on, and this tranche's goal is the evidence
reading.

### Ready-to-send prompt

```
EXECUTOR WINDOW — DEFECT: the signal-registry gate is blind to any signal
emitted through a named constant

Read CLAUDE.md IN FULL. Load deepreason-orchestrator, dr-drive-harness and
pinker-write-for-readers. Start at dr-set-goal. Base on main.
Tranche directory: experiments/<today>-defect-signal-scan-blindness/.
Offline; no key.

THE DEFECT, from the record: tests/test_signals.py::_emitted_signals AST-scans
src/deepreason for record_measure(inputs=[<literal>, ...]) and
record_llm_calls(..., <literal>) heads. A signal emitted through a MODULE-LEVEL
CONSTANT rather than a literal at the call site is invisible to it, so
test_every_emitted_signal_is_registered passes while the signal is undeclared.
Reproduced 2026-09-04: criticism.dispatch.v1, emitted from
src/deepreason/runtime/criticism_dispatch.py, left tests/test_signals.py at
9 passed with signals.is_known('criticism.dispatch.v1') == False.
Parked at experiments/2026-09-04-change-evidence-states/PARKED.md P1.

WHAT TO DO: resolve module-level string constants in the scan (they are all
simple `NAME = "literal"` assignments in the file being scanned, or imported
from one module), and census what the widened scan turns up — every currently
undeclared emitted signal is a finding, not a fixture to update. Declare each
per docs/map/REC-add-signal.md, or, where declaring one is wrong, say why in
writing. Then make test_emitted_inventory_is_nontrivial pin the constant-headed
case too, so the widening cannot silently rot back.

PROOF: the widened scan proven RED against a planted constant-headed
undeclared signal; the census pasted; full gate alone, 0 failed; docs_verify
FULL. Known-not-yours docs_verify rows: SEAM-llm-x-rules.md:54,
INV-frozen-surfaces.md:181 and :736, CON-run-identity.md:211/213/215/298.
```

---

## P2 — the foreign-criticism road files `cut:foreign` and measures nothing

WHAT. `Scheduler._foreign_arg_crit` enacts the manifest-owned criticism plan,
and this tranche declares `cut:foreign` at its entry — an honest refusal to
claim completeness, since that road counts coverage by foreign school identity
in `CoverageDebtV1` receipts, which is a different question from "was every
planned criticism call made". The consequence: on a run using manifest-bound
foreign criticism, NO artifact can ever be read as SUPPORTED on the strength of
an absence, however exhaustively its critics actually worked.

That is the conservative failure, and it is the right one to ship. It is still
a gap: the coverage debt receipts almost certainly carry enough to derive a
real completeness statement for that road.

NOT FIXED HERE because deriving it means reading the foreign-criticism coverage
model properly, which is `DR-SEAM-scheduler-x-workflow` work and its own scope.

### Ready-to-send prompt

```
EXECUTOR WINDOW — CHANGE TRANCHE: a real completeness declaration for the
foreign-criticism road

Read CLAUDE.md IN FULL. Load dr-change-orchestrator, dr-drive-harness,
dr-ask-the-right-question and pinker-write-for-readers. Start at
dr-capture-request with THIS prompt as authority. Base on main.
Tranche directory: experiments/<today>-change-foreign-criticism-completeness/.
Offline; no key.

CONTEXT: experiments/2026-09-04-change-evidence-states/ added a per-cycle
declaration, criticism.dispatch.v1, saying whether a criticism pass made every
call it planned. Only `complete` licenses a reader to treat the absence of a
warranted attack as a measurement rather than a gap. The manifest-owned
foreign-criticism road (Scheduler._foreign_arg_crit) files `cut:foreign` at
entry and therefore licenses nothing, so a run configured with foreign
criticism gets no SUPPORTED readings from absence at all. Parked as P2 of that
tranche.

WHAT TO BUILD: derive completeness for that road from what it already records —
CoverageDebtV1's completed_school_ids, outstanding_school_ids and
termination_reason, plus policy.minimum_foreign_school_coverage — and file
`complete` (naming the covered targets) exactly when the plan's coverage
requirement was met for them with no outstanding schools and no
budget_exhausted termination. Read DR-SEAM-scheduler-x-workflow BEFORE either
subsystem. Keep the closed outcome vocabulary in
src/deepreason/runtime/criticism_dispatch.py closed: if a fifth cut is needed,
add a member, never widen `complete` by silence.

PROOF: mutation-proven tests that a partially covered plan does NOT declare
complete and a fully covered one does; the evidence-states reader's own tests
extended to the foreign road; full gate alone, 0 failed; docs_verify FULL; map
moves in the same commit. Known-not-yours docs_verify rows:
SEAM-llm-x-rules.md:54, INV-frozen-surfaces.md:181 and :736,
CON-run-identity.md:211/213/215/298.
```
