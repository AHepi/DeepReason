# PARKED — found on the way, not fixed here

R6: "Every defect discovered on the way is PARKED with a ready-to-send
prompt, never fixed here." Each entry is one line of WHAT, then a prompt
the operator can paste whole.

---

## P1 — CRITICAL, LIVE TODAY: sandbox escape on the code-testing channel

**What.** Model-authored Python running on the code-testing channel — ON
by default, no switch anywhere — escapes `oracle.py`'s AST guard via a
running-generator frame walk, reaches the real `builtins`, and opens
outbound network connections and arbitrary files at harness privilege,
while the exec-oracle commitment still returns `pass`. Demonstrated:
`experiments/2026-08-27-change-execution-safety/proof/containment_probe.py`,
finding E3. This channel is used by the LIVE technique run on
`claude/spec-to-code-technique-k5209o`.

**Prompt:**

```
TARGET REPOSITORY: AHepi/DeepReason.

Route through deepreason-orchestrator (this is a defect, not a change).
One tranche, one goal: close the sandbox escape on the code-testing
channel. Do not switch any channel off — the standing operator ruling
keeps research, simulation and code-testing ON.

THE DEFECT, already reproduced — do not re-derive it:
experiments/2026-08-27-change-execution-safety/SAFETY.md finding E3, and
proof/containment_probe.py which reproduces it end to end and cleans up
after itself. Model-authored Python reaches the worker module's own
globals with:
    gg.gi_frame.f_back.f_back.f_globals
Every attribute in that chain is public, so neither oracle.py::_guard
(oracle.py:92-110) nor the contained worker's guard rejects it. From
those globals the real builtins, sys, json and random modules are plain
dict lookups. On this channel there is no network namespace at all, so
the escape reaches the open internet: the probe opened a TCP connection
to 1.1.1.1:80 from inside the sandbox while the commitment returned pass.

THE FIX, as specified rather than as invented:
1. Replace the underscore-attribute DENYLIST in oracle.py::_guard with an
   ALLOWLIST of permitted AST node kinds. A denylist over attribute names
   is the wrong shape for this job and G1 in SAFETY.md says why. At
   minimum the allowlist must exclude every route to a frame object:
   generator/coroutine/async-generator/traceback attributes (gi_*, cr_*,
   ag_*, tb_*) and every f_* attribute of a frame.
2. oracle_sandbox.py::_apply_worker_limits (oracle_sandbox.py:135-166)
   wraps every setrlimit in `except (...): pass` — it fails OPEN. Invert
   it to fail CLOSED, the way verification/contained.py:386-408 already
   does.
3. Deny network at the OS layer, not the language layer. The repo already
   has both mechanisms: the unshare probe at contained.py:450-483 and
   verification/_sandbox.py::seccomp_available, which oracle_sandbox.py
   never calls.

PROOF OBLIGATION: the regression test is proof/containment_probe.py's E3
case, committed as a test and shown RED on the unfixed tree first. Then
each of the three fixes above gets its own mutation proof. A test that
asserts a self-reported string ("network": False) does not count — G5 in
SAFETY.md is the record of why that shape let this through.

FROZEN SURFACES: oracle.py and oracle_sandbox.py are NOT frozen.
verification/_sandbox.py IS inside frozen surface 3 (verification/) — if
the fix wants to touch it, request the grant in FIX.md BEFORE
implementing, per the discipline; the monitor reviews it there.

GATE: pytest tests/ -q -n 4, 0 failed. python tools/docs_verify.py
(expect only the 3 known shallow-clone failures). The map moves in the
SAME commit: DR-INV-evidence-channels gains a Trap naming this defect,
and a check that would fail if the escape reopened.
```

---

## P2 — CRITICAL: the same escape on the contained simulation runner

**What.** `ContainedSimulationBackend`'s frozen worker `guard()`
(`contained.py:80-87`) has the identical hole, so `sandboxed_python_v1`
would escape to arbitrary local file access and process execution the
moment the runner is switched on. Network stays denied by the namespace.
This is the gate that stopped R4.

**Prompt:**

```
TARGET REPOSITORY: AHepi/DeepReason.

Route through deepreason-orchestrator. One tranche, one goal: make
verification/contained.py's containment true as stated, so the operator's
pre-authorized switch-on of model-authored code execution can proceed.

THE DEFECT, already assessed — read it, do not re-derive it:
experiments/2026-08-27-change-execution-safety/SAFETY.md, properties (d)
and (e), gaps G1-G3. proof/containment_probe.py reproduces both and
cleans up after itself. Three of five containment properties already
hold and are demonstrated — no network (the namespace survives even a
full language escape), bounded wall time, bounded memory. Do not rebuild
those; they are fine.

WHAT MUST CHANGE (G1 is the one that matters; G2/G3 are defence in depth):
G1. The worker's guard (contained.py:80-87) rejects leading-underscore
    ATTRIBUTES only. gi_frame, f_back and f_globals carry no underscore,
    so a running generator hands model code the worker module's own
    globals and the real builtins. Replace the denylist with an ALLOWLIST
    of permitted AST node kinds. The worker source is frozen by digest
    (CONTAINED_WORKER_SHA256, contained.py:333) — changing it is a new
    worker identity, visible in every receipt fingerprint, which is the
    design working, not a problem to route around.
G2. There is no mount namespace: the probe prefix is --net only
    (contained.py:463), so cwd=scratch is a starting directory, not a
    jail, while resource_limits() reports "filesystem": "ephemeral
    scratch workdir" as though it were one. Either add --mount with a
    real root, or stop reporting a confinement that does not exist.
G3. Nothing stops os.system/fork/exec once the language boundary falls.
    verification/_sandbox.py already provides a seccomp filter that
    contained.py never applies.

PROOF OBLIGATION: proof/containment_probe.py's E1 and E2 cases committed
as tests, shown RED on the unfixed tree first, then GREEN. Additionally a
differential for each property that could fail — SAFETY.md G5 records
that the existing suite pinned self-reported strings, which is how this
went unnoticed through a full committed containment proof.

FROZEN SURFACES: verification/ IS frozen surface 3. This fix touches it
by necessity. Request the grant in FIX.md BEFORE implementing, with the
reader/writer asymmetry argued and tools/blast_radius.py's own contact
rows pasted and disposed one by one — the discipline
docs/map/INV-frozen-surfaces.md records for the 2026-08-25 and 2026-08-27
grants. The monitor reviews it there, not in chat.

AFTER IT LANDS: the execution-safety tranche
(experiments/2026-08-27-change-execution-safety/) re-runs its R2
assessment. If all five properties then hold, its R4/R5 are
pre-authorized by the operator's own words — "If so switch both on" —
and become the next tranche.

GATE: pytest tests/ -q -n 4, 0 failed. docs_verify (3 known shallow-clone
failures only). Map moves in the same commit.
```

---

## P3 — HIGH: the "everything on" preset advertises a channel it cannot reach

**What.** `engaged_simulation_policy` binds
`python_toolchain_identity=PUBLIC_SIMULATION_TOOLCHAIN_ID`
(`v6_policy.py:292, 378-382`) while returning
`runner_profile="simulation.declarative.v1"`, so the compiled manifest
carries a Python toolchain the policy can never dispatch to and every
`sandboxed_python_v1` proposal dies at `runner_profile_mismatch`
(`capabilities/simulation.py:581-587`). Recorded live at commit
`74d9f71ca`. It is a silent dead channel where the all-configurations law
requires a typed disclosure.

**Prompt:**

```
TARGET REPOSITORY: AHepi/DeepReason.

Route through dr-change-orchestrator. One tranche, one goal: a
configuration whose runner profile cannot serve the toolchain it binds
must carry a TYPED DISCLOSURE, never a silent dead channel.

AUTHORITY: the all-configurations law (operator 2026-08-12, CLAUDE.md) as
applied to channels in docs/map/INV-evidence-channels.md — "a typo must
not stop a run, and must not pass silently either: silence is how an
operator believes a channel is off when it is on". And that document's
first Trap: "A default that is True over a road that is severed. The flag
is the cheap half."

THE FACTS, already established — cite, do not re-derive:
experiments/2026-08-27-change-execution-safety/SPEC.md finding F2, and
commit 74d9f71ca on claude/spec-to-code-technique-k5209o which recorded
it live (a validated sandboxed_python_v1 proposal DENIED with terminal
reason runner_profile_mismatch after four silent epochs).

WHAT TO BUILD: a CompileNoticeV1 on the model of channels.py's
CHANNEL_UNKNOWN, emitted when the compiled simulation policy's
runner_profile cannot dispatch to its own bound python_toolchain_identity.
Never a refusal — the configuration still COMPILES. The notice must reach
the same door every launch path enters
(preparation.build_preparation_manifest), per the operations-parity law.

DO NOT change any default in this tranche. Whether the contained runner
becomes the default is gated on P2 landing and is the operator's call
under their standing 2026-08-27 authorization.

FROZEN SURFACES: v6_policy.py and preparation.py are NOT frozen.
run_manifest.py IS (surface 4) — if the notice needs a manifest schema
change, STOP and ask before designing.

GATE: pytest tests/ -q -n 4, 0 failed. Map: DR-INV-evidence-channels
gains the disclosure to its "Where the toggle is read" table plus a check
that would fail if the notice stopped firing.
```

---

## P4 — MEDIUM: containment tests pin self-reported strings

**What.** `tests/test_contained_simulation_runner.py:134-149` asserts
`reported["network"] is False` and
`reported["filesystem"] == "ephemeral scratch workdir"` — values the
backend reports about itself. A backend whose containment silently
regressed would keep reporting them. This is how G1–G3 survived a
committed containment proof.

**Prompt:**

```
TARGET REPOSITORY: AHepi/DeepReason.

Route through dr-change-orchestrator. One tranche, one goal: every
containment property claimed by verification/contained.py and
oracle_sandbox.py is pinned by a DIFFERENTIAL that can fail, never by a
string the backend reports about itself.

AUTHORITY: docs/map/INV-evidence-channels.md's first Trap ("The flag is
the cheap half. Assert the values a dispatch or a controller would
actually CONSUME"), and the standard docs_verify --audit already applies
to map checks — a check that cannot fail is refused. A verify_root
finding is held to the same standard (INV-frozen-surfaces.md, the
2026-08-24 cascade-integrity grant). Containment tests are not.

MODEL TO FOLLOW: experiments/2026-08-27-change-execution-safety/proof/
network_namespace_differential.sh — it runs the real interpreter inside
and outside the backend's own probed prefix and shows the interface list
and the connect result differ. That is what a differential looks like.

SCOPE: tests/ only, plus whatever docs/map check makes the standard
enforceable. No src changes — if a differential goes RED, that is a
finding for a defect tranche, not something to fix here.

GATE: pytest tests/ -q -n 4, 0 failed.
```

---

## P5 — LOW: the `capabilities × channels` seam has no map document

**What.** `docs/map/INV-evidence-channels.md` lists
`Seams-undocumented: capabilities x channels, channels x manifest`. This
tranche's whole subject — a channel flag that is ON over a capability
road that is severed — lives exactly on the first of those. Recorded per
the map preflight rule that a missing id is a finding, not a blocker.

**Prompt:**

```
TARGET REPOSITORY: AHepi/DeepReason.

Route through dr-change-orchestrator. One tranche, one goal: write
docs/map/SEAM-capabilities-x-channels.md.

Read docs/map/SCHEMA.md first — it is the contract for writing a map
document, and the check rule (every load-bearing claim carries a `check:`
shell command at column 0 that exits 0) is not optional.

WHAT THE SEAM ACTUALLY IS, with the worked example already in hand:
a channel's enablement flag (channels.py) and a capability's dispatchable
road (capabilities/policy.py runner_profile, capabilities/simulation.py
admission) are two different facts, and the second can be severed while
the first says ON. experiments/2026-08-27-change-execution-safety/SPEC.md
findings F2 and F3 are the case study; commit 74d9f71ca is the live
record of it costing four epochs.

The document's Traps section owns that story, with its run id.

GATE: python tools/docs_verify.py, and --audit must not refuse any check
you write.
```

---

## P6 — LOW: the documented gate needs two dependencies the install does not declare

**What.** CLAUDE.md's gate command is `pytest tests/ -q -n 4`, and
`tests/test_schema_carries_every_prose_rule.py:170` imports `jsonschema`.
Neither `pytest-xdist` (which `-n 4` requires) nor `jsonschema` appears in
`pyproject.toml` — `dependencies` has three entries and
`optional-dependencies.dev` has `pytest` and `ruff` only. A fresh container
that runs the documented setup and then the documented gate gets one failure
that looks like a code defect and is not. This tranche hit it:
`1 failed, 4334 passed` on `ModuleNotFoundError: No module named 'jsonschema'`.

**Prompt:**

```
TARGET REPOSITORY: AHepi/DeepReason.

Route through deepreason-orchestrator. One tranche, one goal: the setup
CLAUDE.md documents must be sufficient for the gate CLAUDE.md documents.

THE DEFECT, already observed — cite, do not re-derive:
experiments/2026-08-27-change-execution-safety/DELIVERY.md, the "Full gate"
section. A fresh container that runs
    pip install -e . --break-system-packages
then
    pytest tests/ -q -n 4
fails on ModuleNotFoundError: No module named 'jsonschema'
(tests/test_schema_carries_every_prose_rule.py:170), and cannot use -n 4 at
all without pytest-xdist. Neither is declared: pyproject.toml dependencies
carries pydantic, pyyaml and fastembed; optional-dependencies.dev carries
pytest and ruff.

THE FIX: declare what the gate actually needs in
optional-dependencies.dev — at minimum jsonschema and pytest-xdist. Take
the census from the tests rather than from this prompt: grep the suite for
third-party imports and reconcile the whole set against pyproject.toml, so
this is fixed once rather than one module at a time.

WHILE YOU ARE THERE: CLAUDE.md's Build-and-test section says "expect ~3100
passed, 0 failed". The 2026-08-27 run collected 4334 passed, 15 skipped.
Update the baseline in the same commit and record the new number, so the
next session can tell a real regression from a stale expectation. Check
docs/AUDIT_BASELINES.md for the same number.

PROOF OBLIGATION: a clean-container reproduction — install from the
declared extras alone, run the gate, 0 failed. If the container cannot be
reset, a fresh virtualenv is the equivalent and must be shown.

GATE: pytest tests/ -q -n 4, 0 failed. python tools/docs_verify.py.
```

---

## P7 — HIGH: the 2026-08-25 frozen-surface grant's census is now false

**What.** `docs/map/INV-frozen-surfaces.md:181` asserts that no committed
root carries a `transport_failure` workflow-provider attempt. That census
is the safety argument for the 2026-08-25 granted contact with frozen
surface 3 — the `workflow-call-pairing` raw-blob normalization, whose
grant explicitly does NOT claim to be insertions-only and rests instead on
"no committed root contains an event the changed line can decide
differently". One now does:
`experiments/2026-08-26-pc2-rematch/retired-transport-timeout180-run-42ad288038dd606c/objects/workflow-provider-attempt-v1/f750d2979c3e248e549efb5754bfb11b947cba1cfa7fb2bb8c1d77babad3b570.json`,
committed 2026-08-26 by `50885d29f`. `docs_verify` has been red on it
since. Found incidentally by this tranche's phase-boundary gate; not
introduced by it.

**Prompt:**

```
TARGET REPOSITORY: AHepi/DeepReason.

Route through deepreason-orchestrator. One tranche, one goal: re-derive
the safety argument for the 2026-08-25 frozen-surface grant, whose census
a later commit falsified.

THE FACTS, already measured — cite, do not re-derive:
experiments/2026-08-27-change-execution-safety/DELIVERY.md, the
"docs_verify" section. docs/map/INV-frozen-surfaces.md:181 checks that
zero committed roots carry a transport_failure workflow-provider attempt.
Exactly one now does, in
experiments/2026-08-26-pc2-rematch/retired-transport-timeout180-run-42ad288038dd606c/,
committed 2026-08-26 by 50885d29f. The file is on origin/main.

WHY IT MATTERS. That census is not decoration. The 2026-08-25 grant
changed one comparison inside verify_root — attempt.raw_ref ==
call.raw_ref became attempt.raw_ref == (call.raw_ref or None) — and the
grant document states plainly that this "is NOT insertions-only, and does
not claim to be". Two measured facts carry it instead, and the census is
the second: no committed root holds an event the changed line could
decide differently. A root that does now exists.

WHAT TO ESTABLISH, in this order:
1. Read that attempt record. Does the changed predicate decide it
   differently — i.e. does it pair under the new reading and not the old,
   or vice versa? Answer from the record, not from the code.
2. If it does NOT: the check's THRESHOLD is what rotted, not the
   argument. Rewrite the check so it states the property that actually
   matters (no attempt whose pairing the predicate decides differently),
   and say in the grant document why the count moved without the
   guarantee moving.
3. If it DOES: the grant's second safety leg is gone and the first
   (add-only predicate) has to carry it alone, or the grant needs
   re-requesting. That is an operator decision — STOP and ask, with both
   readings priced.

FROZEN SURFACES: INV-frozen-surfaces.md is a map document about frozen
surfaces, not itself frozen — editing it is ordinary work. Do NOT touch
invariants.py in this tranche; the goal is the argument, not the code.

GATE: python tools/docs_verify.py — this check green, and the three known
shallow-clone CON-run-identity.md failures unchanged. --audit must not
refuse whatever check replaces it.
```
