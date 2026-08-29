# PARKED — findings this tranche measured and did not touch

R3 is a MEASUREMENT phase. Nothing in `src/`, no committed check text and
no map document other than `SCHEMA.md` was edited. Each finding below is
one ready-to-send prompt: paste it whole into a fresh window.

Order them by weight: P1 first (a frozen-adjacent coupling the map
denies), then P2 (a frozen-surface pin that disagrees with itself), then
P3, P4, P5.

---

## P1 — `invariants.py` imports `llm/`, and the seam says it cannot

```
TARGET REPOSITORY: AHepi/DeepReason — verify before anything else.

SETUP: fresh container. git fetch origin main && git checkout -B <your
session-designated branch> origin/main. pip install -e .
--break-system-packages -q, and note the container's interpreter split:
`python` may resolve to /usr/local/bin/python while `pip` resolves to
/usr/bin/pip, so run `python -m pip install -e . pytest pytest-xdist
jsonschema --break-system-packages` or every `python -m pytest` map check
dies with "No module named pytest" and you will read 502 false failures.
Read CLAUDE.md IN FULL; load deepreason-orchestrator (DEFECT tranche),
dr-drive-harness, dr-explain-to-operator.

AUTHORITY: finding B1 of experiments/2026-08-29-fix-docs-verify-multiline-
checks/FINDINGS.md, produced by the first-ever execution of that check.

GOAL, one sentence: decide whether DR-SEAM-llm-x-verification's central
claim or the code is wrong, and make one of them true.

EVIDENCE, already gathered — do not re-derive:
- docs/map/SEAM-llm-x-verification.md states, verbatim: "Between them
  there is **no import in either direction** — `invariants.py` names
  nothing from `llm/`, and `llm/` names nothing from `invariants.py`."
- Its check at SEAM-llm-x-verification.md:19 fails:
  AssertionError: ('src/deepreason/invariants.py', 'deepreason.llm.firewall')
- src/deepreason/invariants.py:21 is a MODULE-LEVEL
  `from deepreason.llm.firewall import route_fingerprint`. Four further
  function-local deepreason.llm.* imports at lines 1214, 1215, 1260, 4101.
- That check had never run before 2026-08-29: it is a multi-line block,
  and the parser only read single-line ones.

WHY THIS ONE IS FIRST: `invariants.py` is FROZEN SURFACE 3 and
`route_fingerprint` is named in CLAUDE.md as the frozen-ADJACENT surface.
A coupling between them that the map denies is the exact shape of thing
the map exists to make impossible.

SCOPE: diagnose first from docs/map/INV-frozen-surfaces.md and the seam
document, not by editing. Two roads, and you must PRICE BOTH before
choosing: (i) the import is legitimate and the seam document's claim must
be narrowed to what is actually true, with a check that would fail if the
arrow widened again; (ii) the import is a real violation and belongs
behind the seam's record-only agreement. Road (ii) touches a frozen
surface — STOP and ask the operator before writing any code, per
INV-frozen-surfaces.md's grant procedure.

END STATE: the seam document and the tree agree, the check passes, and
whichever road you took is argued in the tranche's RESULTS.md.
```

---

## P2 — a frozen-surface digest pinned twice, two different values

```
TARGET REPOSITORY: AHepi/DeepReason — verify before anything else.

SETUP: as P1 above, including the interpreter note.

AUTHORITY: finding B2 of experiments/2026-08-29-fix-docs-verify-multiline-
checks/FINDINGS.md.

GOAL, one sentence: docs/map/INV-frozen-surfaces.md pins the qualification
subject digest at two places with two different values; make it pin the
true one, once.

EVIDENCE, already gathered — do not re-derive:
    qualification_subject_digest(_manifest(_profile()), _profile())
      actual     02ee7e098bb9239011708a4aa0bce4b7479619b3aff28eff46188125a869e713
      :533 pins  02ee7e098bb9239011708a4aa0bce4b7479619b3aff28eff46188125a869e713   PASSES
      :657 pins  b9038b84efdea313c3f3f2a8862d8acf180d3938ab3d1bf3588c3585dfe07386   FAILS
Both checks are multi-line and both were dark until 2026-08-29, so the two
pins have never once been able to contradict each other.

SCOPE: this is FROZEN SURFACE 5 ("anything altering qualification subject
digests"). You are NOT changing a digest — the value the tree produces is
the one :533 already asserts, so the surface has not moved. You are
correcting a stale ASSERTION in a map document. Establish that from the
git history of both pins BEFORE editing: find the commit that introduced
b9038b84 and what it was measuring. If the history shows the digest DID
move at some point and :533 was updated while :657 was not, say so — that
is a different and larger finding, and it goes to the operator before any
edit.

END STATE: one pin, with the value the tree produces, and a Traps entry in
INV-frozen-surfaces.md naming this tranche as how it was found.
```

---

## P3 — a malformed check that has been unable to do its job since it was written

```
TARGET REPOSITORY: AHepi/DeepReason — verify before anything else.

SETUP: as P1 above.

AUTHORITY: finding C1 of experiments/2026-08-29-fix-docs-verify-multiline-
checks/FINDINGS.md.

GOAL, one sentence: repair the malformed check at
docs/map/SEAM-llm-x-rules.md:54 so it runs, and re-derive the count it
pins.

EVIDENCE, already gathered — do not re-derive: line 54 is a single-line
check that lost its closing backtick, and the prose paragraph after it
lost its blank line, so the two merged into one line. The check ends at
`= "41"`; the text from `What does not cross is every transport
primitive` onward is prose belonging to the following paragraph (which
continues on lines 55-56). docs_verify now reports it as
`unparseable check` and fails the run; before 2026-08-29 it was silent.

THE POINT, so the repair is taken seriously: the document's own prose says
this check exists BECAUSE the number had already drifted once — "this
sentence read 'Thirty-nine' while the tree carried FORTY". The check
written to stop that drift has never been able to run. Re-derive the count
against today's tree; if it is not 41, that is a second finding and the
prose above it moves in the same commit.

SCOPE: docs/map/SEAM-llm-x-rules.md only. Restore the closing backtick,
restore the blank line, re-derive the count, re-run
`python tools/docs_verify.py --self-test` and the document's own checks.

END STATE: `python tools/docs_verify.py` reports no unparseable opener,
and the count in the check matches the tree.
```

---

## P4 — a check defeated by a comment

```
TARGET REPOSITORY: AHepi/DeepReason — verify before anything else.

SETUP: as P1 above.

AUTHORITY: finding B4 of experiments/2026-08-29-fix-docs-verify-multiline-
checks/FINDINGS.md.

GOAL, one sentence: make DR-INV-signal-contract's consumer-decoupling
check bind the CODE rather than the source text, so a comment explaining
the decoupling stops falsifying it.

EVIDENCE, already gathered — do not re-derive: the check at
INV-signal-contract.md:222 asserts `LINEAGE_POLICIES` does not appear in
`inspect.getsource(Scheduler)`. It appears exactly once, at
src/deepreason/scheduler/scheduler.py:1127, inside a COMMENT: "# The
policy is selected by id from `wander.LINEAGE_POLICIES`". `getsource`
returns comments, so the sentence documenting the decoupling trips the
check proving it. On this evidence the CLAIM still holds and the CHECK is
what is wrong.

SCOPE: docs/map/INV-signal-contract.md only, unless the AST rewrite shows
a real naming in code — then route it as a defect. Use the map's own
recorded technique (SCHEMA.md, "Check-writing rules learned by
falsification", class 3): resolve names through `ast`, not substring greps
over raw source. Mutation-prove the new check: it must go RED when a real
`LINEAGE_POLICIES` reference is planted in scheduler code, and stay GREEN
with the comment present.

NOTE: src/deepreason/scheduler/scheduler.py is an in-flight fix window's
cone. This failure is on main at ae490e26b and is NOT theirs; coordinate
before touching that file, and prefer changing only the check.
```

---

## P5 — a check that cannot reach its own claim

```
TARGET REPOSITORY: AHepi/DeepReason — verify before anything else.

SETUP: as P1 above.

AUTHORITY: finding B3 of experiments/2026-08-29-fix-docs-verify-multiline-
checks/FINDINGS.md.

GOAL, one sentence: make the check at docs/map/CON-discharge-channel.md:150
construct a manifest the current validator accepts, so the claim it
defends is actually tested.

EVIDENCE, already gathered — do not re-derive: the check dies before
either assertion with
  pydantic ValidationError: V6_SIMULATION_TOOLCHAIN_REQUIRED: policy must
  bind one frozen toolchain
raised at src/deepreason/run_manifest.py:3527-3538, which requires exactly
one manifest toolchain whose id equals
`capabilities.simulation.python_toolchain_identity`. Measured:
  engaged_inquiry_capability_policy(...).simulation.python_toolchain_identity
      = python@deepreason-public-contained.v1
  engaged_local_simulation_toolchain().id
      = python@deepreason-public-local.v1
The check binds the LOCAL toolchain against a policy naming the CONTAINED
one. Its claim — that the manifest echo drops DISCHARGE_POLICY and
config_from_run_manifest restores the default — is UNREACHED, not
disproven.

WHY IT MATTERS BEYOND THE CHECK: that claim is the evidence for the
document's own statement that this signal's FREE layer "is, today,
reachable only by editing code", which the modularity law (CLAUDE.md,
2026-08-26) forbids. If the claim turns out FALSE once the check can run,
the document's conclusion moves with it.

SCOPE: docs/map/CON-discharge-channel.md only. Bind the toolchain the
policy names, re-run, and record what the assertions then say — including
if they pass, which would be the more interesting outcome.
```
