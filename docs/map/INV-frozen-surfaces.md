<!-- DR-INV-frozen-surfaces -->
Verified-at: a40450f1c
Verify: python tools/docs_verify.py
Owns: src/deepreason/capabilities/state.py, src/deepreason/harness.py, src/deepreason/invariants.py, src/deepreason/run_manifest.py
Seams: 
Seams-undocumented: harness x verification, llm x manifest

# Frozen surfaces — what you may not change, and why

Read this BEFORE scoping any change. Some surfaces are not yours to change, and
discovering that after the code is written is the expensive order to discover it
in. Everything here is enforced by the gate, by an existing recorded root, or by
both — none of it is style.

## The governing principle

> The append-only record itself: fix READERS so old roots stay valid; a change
> that invalidates existing replay-valid roots is wrong by definition.

A committed run root is evidence. Evidence that changes meaning when the code
changes is not evidence. So the asymmetry is deliberate: readers may be fixed
freely, writers and formats may not.

**The operational consequence:** a change that alters what a FUTURE run may do
is ordinary work. A change that alters how a PAST run verifies is a defect,
whatever its motivation. Measure the difference rather than assuming it — the
42-root sweep below is the instrument.

## The five frozen surfaces

### 1. `capabilities/state.py` — digests and event application

Capability state digests are content addresses over proposal and work-order
maps. Changing what is digested, or the order of application, changes the digest
of every recorded capability transition.

`check: grep -q "def " src/deepreason/capabilities/state.py`

### 2. `harness.py` — event application and well-formedness

The append-only log's write path and the state materialization that replays it.
`verify_root` re-derives state from the log; if application order changes,
re-derivation of an old log produces a state its own record never held.

`check: grep -q "class Harness" src/deepreason/harness.py`

### 3. Replay-validation record formats — `invariants.py`, `verification/`

`verify_root` and the epistemic-check report. Their output shape is compared
across runs and across time; a format change silently reinterprets every stored
verdict.

`check: grep -q "def verify_root" src/deepreason/invariants.py`

**Granted contact, 2026-08-21 — the seat-instance anchor (Rung 1b-ii).** The
operator granted a READER fix inside this surface, on the record and against a
committed design, after the request and its reason were written into
`experiments/2026-08-21-change-rung1b-ii-signal-consumption/SPEC.md` first (their
own words: "Don't grant it verbally in chat"). What moved: `_configured_role_cap`
and the one `allowed_caps` lookup beside it now resolve a SEAT-keyed cap knob
(`cap:<role>#<seat>`) through `allocation.route_cap_for_knob`, so a per-seat
limit anchors to that seat's own route instead of missing the role lookup and
falling back to the unanchored `[500, 2500]` default. A reader fix is the
permitted kind here precisely because it changes no OUTPUT: the same
`verify_root` violation records, in the same shape, over the same logs — a
role-keyed knob resolves byte-identically, and only the seat-keyed form, which
no committed root uses, resolves differently. Proven, not asserted: a 107-root
sweep before and after diffs empty
(`.../proof/sweep_before.txt` vs `sweep_after.txt`), and the regression that
motivated it was run RED on the unfixed tree first (`.../proof/s12_red.txt`).

`check: grep -q "route_cap_for_knob" src/deepreason/invariants.py`
`check: grep -q "cap:{e.llm.role}#{attempt.seat}" src/deepreason/invariants.py`

**Granted contact, 2026-08-22 — the `standing-integrity` check (Rung 4).** The
operator FORECAST this contact in the tranche instruction itself, named its
exact content, and directed that the grant be requested in SPEC.md rather than
in chat: "surface 3 (verification) — FORECAST ADDITIVE CONTACT: a
standing-integrity check (mention law held; every consulted assertion addressed
to a promotion problem). Request the grant in SPEC.md BEFORE code, per the
discipline; the monitor reviews it there." The request was written into
`experiments/2026-08-22-change-rung4-frame-assertions/SPEC.md` S13 with
`tools/blast_radius.py`'s own `frozen_surface_contacts` list pasted verbatim,
before a line of the check existed, and the disposition with its three
checkable facts is ledgered at that tranche's REQUEST.md Amendment 2.

What moved: ONE additive `fail("standing-integrity", …)` clause at the end of
`verify_root`, plus the check's name in `_EPISTEMIC_CHECKS`. **Insertions only —
52 and 1, zero deletions** — so no existing finding's shape, name, order or
detail string changed. Additive is provable rather than asserted here: the check
recognises frame assertions by a body and a commitment that no root written
before 2026-08-22 contains, so every committed root yields nothing from it,
pinned by a probe against a committed root rather than a fixture.

One design point worth keeping, because the obvious implementation is wrong: the
check recognises assertions by the LOOSE reading (body plus commitment), not the
strict one the consult path uses. The strict recogniser additionally requires
the interface to match the controller's compiler — so an assertion violating the
mention law is not recognised by it at all, and a check built on it could only
ever report a clean bill. The first implementation here did exactly that and
reported nothing on a root purpose-built to violate the law.

`check: grep -q "standing-integrity" src/deepreason/invariants.py && grep -q "standing-integrity" src/deepreason/verification/report.py && grep -q "_declared_frame_assertions" src/deepreason/invariants.py && python -m pytest tests/test_calculus_standing.py::test_standing_integrity_fires_on_a_violated_mention_law tests/test_calculus_standing.py::test_standing_integrity_reports_nothing_on_a_root_that_predates_it -q`

**Granted contact, 2026-08-24 — the `cascade-integrity` check (Rung 7).** The
operator FORECAST this contact in the tranche instruction itself, named its
exact content, and directed that the grant be requested in SPEC.md rather than
in chat: "surface 3 — FORECAST ADDITIVE CONTACT (a cascade-integrity check in
verification); request the grant in SPEC.md BEFORE code, the monitor reviews it
there." The request was written into
`experiments/2026-08-24-change-rung7-wounds-falls-succession/SPEC.md` §1 with
`tools/blast_radius.py`'s own contact rows pasted and disposed one by one,
before a line of the check existed.

What moved: one additive `fail("cascade-integrity", …)` family at the END of
`verify_root`, three limbs, plus six in-function reader helpers and the check's
name in `_EPISTEMIC_CHECKS`. **Insertions only — 87 and 1, zero deletions** —
so no existing finding's shape, name, order or detail string changed. Additive
is provable rather than asserted: all three limbs recognise their inputs by
bodies, commitments and marks no root written before this layer can produce,
pinned by a probe against a committed root rather than a fixture.

One design point worth keeping, because the obvious implementation is worthless
rather than merely wrong. Limb 2 states Prop 9.7's totality — every problem a
fallen frame carried is marked — and the obvious way to check it is to ask the
marking function on both sides. That version agrees with itself on every
possible record and can never fire. The shipped limb RE-DERIVES the obligation
from the exits and σ and compares it against the marks, so a mutation to either
derivation breaks it. `docs_verify --audit` refuses map checks that cannot
fail; the same standard is owed to a `verify_root` finding, which has no
equivalent auditor of its own.

`check: grep -q "cascade-integrity" src/deepreason/invariants.py && grep -q "cascade-integrity" src/deepreason/verification/report.py && python -m pytest tests/test_cascade_integrity.py -q`
`check: python -c "
import inspect
from deepreason.invariants import verify_root
block = inspect.getsource(verify_root)
block = block[block.index('Cascade integrity'):]
assert '_framed_problem_ids(h, fallen.scope)' in block
assert block.count('_orphan_marks(h)') == 1
"`

**False alarm rowed, same date.** `tools/blast_radius.py` also reported
`manifest schemas and validators (run_manifest.py)` as `SYMBOL_INDIRECT` contact
for the symbol `clamp`. It is a substring false positive: every `clamp` in that
file is `clamp_reserved_attention_fractions` /
`_reserved_fractions_are_clamped`, imported from `deepreason.config` and
unrelated to `controller.clamp`. `run_manifest.py` was NOT touched by that
tranche. The gate states its own method in each detail string — "grep-based; not
proof of semantic contact" — so this is the gate working as documented, and the
disposal is by measurement rather than by assurance.

`check: ! grep -q "controller import clamp\|from deepreason.controller" src/deepreason/run_manifest.py`

**Granted contact, 2026-08-25 — the `workflow-call-pairing` raw-blob normalization.** The
operator forecast this contact in the tranche instruction and directed that the grant be
requested in FIX.md before implementation ("if the fix wants contact, request the grant in
FIX.md BEFORE implementing, with the reader-vs-writer asymmetry argued; the monitor reviews it
there"). It was, with `tools/blast_radius.py`'s own `CONTACT` verdict and both contact rows
pasted and disposed one by one, at
`experiments/2026-08-25-defect-workflow-call-pairing/FIX.md`.

What moved: ONE comparison inside `verify_root`'s pairing check — `attempt.raw_ref ==
call.raw_ref` became `attempt.raw_ref == (call.raw_ref or None)`, matching the writer
(`transaction_service.py`, `raw_ref=call.raw_ref or None`) and replay's copy of the same six
agreements (`replay.py`, `attempt.raw_ref != (call.raw_ref or None)`). No check name, no
`_EPISTEMIC_CHECKS` entry, no `report.py` channel, no record format.

**This grant is NOT insertions-only, and does not claim to be.** Unlike the 2026-08-21,
2026-08-22 and 2026-08-24 contacts (52+1, 87+1 and 11+0, zero deletions), this is a one-line
modification, so additivity carries none of the safety argument. Two other things carry it
instead, and both are measured. First, the predicate is ADD-ONLY in the sense this document's
`SUB-verification` sibling requires: every pair accepted before is accepted after, and exactly
one new pair — an absent attempt raw against an absent call raw — is admitted. Second, no
committed root contains an event the changed line can decide differently: across the 14
committed roots carrying `objects/workflow-provider-attempt-v1/`, 459 attempts in total, there
are zero with `outcome: "transport_failure"` and zero with `"raw_ref": null`. The census, not a
sweep, is the instrument — it says why no verdict COULD move rather than that none did.

`check: python -c "import inspect; from deepreason.invariants import _controller_v3_history as h; src=inspect.getsource(h); assert 'attempt.raw_ref == (call.raw_ref or None)' in src" && grep -q "raw_ref=call.raw_ref or None," src/deepreason/workflow/transaction_service.py && grep -q "attempt.raw_ref != (call.raw_ref or None)" src/deepreason/workflow/replay.py && python -m pytest tests/test_v6_transport_failure_pairing.py -q`
`check: test "$(find experiments runs -path '*workflow-provider-attempt-v1/*.json' -exec grep -l 'transport_failure' {} + 2>/dev/null | wc -l)" -eq 0`

**Granted contact, 2026-08-27 — the `split-legs` family (a leg is not a repair).**
The tranche instruction forecast this contact and directed that the grant be requested in
FIX.md before implementation ("this touches invariants.py/verification (surface 3) — request
the grant in FIX.md BEFORE implementing, with the writer/reader design stated; the monitor
reviews it there"). It was, with `tools/blast_radius.py`'s own `CONTACT` verdict and all
three contact rows plus the qualification-digest row pasted verbatim and disposed one by
one, at `experiments/2026-08-27-defect-split-leg-recording/FIX.md`, before a line of the
check existed.

What moved: ONE additive `split-legs` family at the END of `verify_root` — six limbs
(shape, token accounting, the `B_r + B_a` envelope, trace continuity, blob reachability,
request provenance). **Insertions only, zero deletions**, and no existing check's name,
shape, order or detail string changed. `verification/report.py` was NOT touched and no
`_EPISTEMIC_CHECKS` entry was added: `split-legs` falls through `_legacy_channel` to
`integrity`, which is where all four checks it relieves already sit, so the request
narrowed during implementation rather than widened.

Additive is provable here more strongly than in the 2026-08-22 and 2026-08-24 grants,
which recognised their inputs by bodies no older root contains. Every limb is guarded on
`attempt.split_legs`, **a field that did not exist before this commit**: `FrozenRecord`
sets only `frozen=True`, so pydantic's `extra="ignore"` applies, every attempt in every
committed root deserialises with `split_legs == ()`, and no limb can reach a `fail`.
Pinned by a probe against a real committed root rather than a fixture.

Why the reader had to change at all, since readers-may-be-fixed is this document's own
asymmetry: the WRITER was the defect. `llm/adapter.py` spliced the split protocol's
deliberation leg into `attempt_trace`, which `verify_root` reads as a repair ladder, so
every thinking-ON run was replay-invalid — 260 violations across four unrelated checks on a
run that CONVERGED, plus an `LLMAttempt.prompt_ref=None` operational failure. The writer is
fixed; this family is what makes the new record READ rather than merely accepted, so a leg
recorded wrongly still fails. `LLMAttempt.split_leg` and `split_max_tokens` were REMOVED,
which the 2026-08-14 law permits and which no committed root feels: 0 of 3 155 attempts
carry a non-empty `split_leg` (`docs/RUN_ANATOMY_SYNTHESIS_2026-08-26.md` §3.2), the
protocol having never run live before this tranche.

`harness.py` (surface 2) took ZERO contact, and that was measured rather than assumed:
both of its `attempt_trace` reads are attempt-level, and they now see strictly fewer and
more correct entries. The seam is written up at `DR-SEAM-llm-x-verification`, which did not
exist — and whose absence is why the defect shipped.

`check: grep -q "split-legs" src/deepreason/invariants.py && ! grep -q "split-legs" src/deepreason/verification/report.py && python -c "
from deepreason.verification.report import _legacy_channel
assert _legacy_channel('split-legs', 'x') == 'integrity'
from deepreason.ontology.event import LLMAttempt as A
assert not {'split_leg', 'split_max_tokens'} & set(A.model_fields)
" && python -m pytest tests/test_split_leg_recording.py -q`
`check: python -m pytest tests/test_split_leg_recording.py::test_an_attempt_from_a_committed_root_deserialises_with_no_legs -q`

**Granted contact, 2026-08-27 — the sandbox attribute boundary (the escape fix).**
The operator granted this contact IN CHAT, conditionally, after being shown the
verdict it unblocks: "can you fix please. Frozen surface changes are permitted
as long as you document what is affected." The condition is the grant, so the
disposition is written out in full at
`experiments/2026-08-27-change-execution-safety/FIX.md` — what moved, what did
not, and why no committed root can change verdict.

Why the contact was unavoidable. Every AST guard over model-authored Python in
this repository rejected attributes beginning with an underscore and nothing
else, and `gg.gi_frame.f_back.f_back.f_globals` contains no underscore. Two of
the five guards live inside this surface. The escape was demonstrated, not
inferred: a file written outside the ephemeral scratch directory, an arbitrary
shell command at harness privilege, and — on the code-testing channel, which is
ON by default — a TCP connection to the open internet, each while the recorded
verdict stayed `pass`
(`.../SAFETY.md` E1-E3, reproduced by `proof/containment_probe.py` whose pre-fix
output is committed at `proof/containment_probe_BEFORE.out`).

What moved, inside this surface, and only this. In `verification/contained.py`:
the frozen worker's `guard()` tests `forbidden_attribute(node.attr)` instead of
`node.attr.startswith("_")`, and the worker source became a template that
interpolates the ONE boundary definition from `deepreason.sandbox_guard` — the
worker runs in a scrubbed environment with no `PYTHONPATH` and cannot import
this repository, so it receives the rule as generated source rather than a
hand-copied twin. In `verification/simulation.py`: the same two conditions
inside `_guard`. Nothing else in either module.

**`CONTAINED_WORKER_SHA256` MOVES, and `BROKERED_WORKER_SHA256_V2` with it**
(`brokered.py` derives its worker from V1 and was not edited). That is this
surface's design working rather than a cost to route around — `contained.py`'s
own docstring says a changed worker is a changed runtime identity, "visible in
each immutable receipt". No test pins a literal digest; each asserts the digest
equals the hash of the source, which stays true.

**This grant is NOT insertions-only and does not claim to be** — like the
2026-08-25 contact, it modifies conditions rather than appending a check. What
carries it instead is a categorical argument rather than a census, and the
distinction matters: the changed code runs INSIDE a worker at EXECUTION time
and decides whether a future proposal's source is admitted. It is not a reader.
No record format, no digest algorithm, no manifest schema, no `_EPISTEMIC_CHECKS`
entry, no `verify_root` finding and no `report.py` channel changed. A committed
root's stored `SimulationVerificationResult` is bytes that no code path in this
change reads, writes or re-derives — so the governing principle at the top of
this document lands on the ordinary-work side: this alters what a FUTURE run
may do, not how a PAST run verifies.

The rejected set is CLOSED and the closure is re-derived rather than asserted:
the test walks the live `dir()` of every scope-bearing object type and pins the
residue to eight names, so a future CPython adding an introspection attribute
under a new prefix turns it RED. That is the property the old rule — a denylist
over an OPEN set — could never have.

`check: python -c "
from deepreason.verification import contained
from deepreason.sandbox_guard import WORKER_GUARD_SOURCE
import ast
assert 'forbidden_attribute(node.attr)' in contained.CONTAINED_WORKER_SOURCE_V1
assert '__DEEPREASON_SANDBOX_GUARD__' not in contained.CONTAINED_WORKER_SOURCE_V1
assert WORKER_GUARD_SOURCE.rstrip() in contained.CONTAINED_WORKER_SOURCE_V1
ast.parse(contained.CONTAINED_WORKER_SOURCE_V1)
import inspect
from deepreason.verification import simulation
assert 'forbidden_attribute(node.attr)' in inspect.getsource(simulation._guard)
"`
`check: python -m pytest tests/test_sandbox_guard.py -q`
`check: ! git diff --name-only origin/main...HEAD | grep -qE "capabilities/state\.py|/harness\.py|/invariants\.py|/run_manifest\.py|/qualification\.py|llm/firewall\.py"`

### 4. Manifest schemas AND their validators — `run_manifest.py`

Not only the Pydantic models: the validators too. Admitting a value a validator
previously rejected widens what counts as a valid manifest, and every
qualification subject digest derives from the manifest.

This is a live example rather than a hypothetical. `CriticismPolicyV1.authority`
is a closed two-value Literal, and the v4 validator additionally rejects any
criticism binding whose role is not `argumentative_critic`:

`check: grep -q 'V4_CRITICISM_ROLE_UNSUPPORTED' src/deepreason/run_manifest.py`
`check: grep -rq 'V4_CRITICISM_ROLE_UNSUPPORTED\|role == .judge' experiments/2026-08-01-change-prose-can-refute/SPEC.md`

The tranche in `experiments/2026-08-01-change-prose-can-refute/` wanted
school-bound JUDGE seats. The Pydantic model permits
`role="judge"`; the validator forbids it. The change was redesigned to avoid the
manifest entirely rather than widen the validator. **Reading the model and not
the validator is the specific mistake to avoid here.**

### Frozen-adjacent, found by falsification: `route_fingerprint`

The v6 behavioral gate compares stored route digests against
`route_fingerprint(route)` — recorded roots therefore depend on its exact
serialization, yet neither `llm/firewall.py` nor the function was filed here
until the map's falsification pass flagged it (see
`DR-SEAM-llm-x-manifest`). Treat its output format as frozen.

`check: grep -q "def route_fingerprint" src/deepreason/llm/firewall.py`

**Granted contact, 2026-08-23 — the split-budget knobs in the source-config
echo.** The two-call seat protocol tranche added two `Config` fields and the
full gate went red in 40 places: the qualification subject digest moved, and
with it 22 frozen manifest wire-byte goldens and the shipped-digest pin. The
grant was requested with `tools/blast_radius.py`'s own `DIRECT` contact verdict
pasted and the fix already measured, and the operator gave it in those terms
("Insertions only, 11 and 0 ... Its effect is to PRESERVE digests, not move
them").

What moved: two `data.pop("SPLIT_BUDGET_*", None)` lines in
`_versioned_source_config_data`, joining the eight knobs already there.
**Insertions only — 11 and 0** — and no schema, validator or Pydantic model was
touched. Additive is provable rather than asserted here: the qualification
subject digest over a committed fixture returns to
`b9038b84efdea313c3f3f2a8862d8acf180d3938ab3d1bf3588c3585dfe07386`, which is
byte-identical to the value the tranche base produces, so this contact makes
the surface MORE stable rather than less. Ledgered at
`experiments/2026-08-22-change-two-call-seat-protocol/REQUEST.md` Amendment 2.

`check: python -c "import json; from tests.test_reusable_qualification import _manifest, _profile; p = _profile(); m = _manifest(p); c = json.loads(m.engine_config_json); leaked = sorted(k for k in c if k.startswith('SPLIT_BUDGET_')); assert not leaked, leaked" && test "$(grep -c 'data.pop(\"SPLIT_BUDGET_' src/deepreason/run_manifest.py)" -eq 2`

**Granted contact, 2026-08-26 — the three F3 knobs (channels and the wander
cap).** The operator FORECAST this contact in the tranche instruction and named
its exact content: "the operator-seeded lineage gets a declared budget-share
FLOOR (**Config knob, versioned-source line for every schema version**)". The
request was written into
`experiments/2026-08-26-change-f3-channels-and-wander-cap/SPEC.md` with
`tools/blast_radius.py`'s own `frozen_surface_contacts` list pasted verbatim,
before a line of code existed — the same discipline as the 2026-08-21,
2026-08-22 and 2026-08-24 grants.

What moved: THREE `data.pop` lines in `_versioned_source_config_data` —
`SEED_PROBLEM_BUDGET_FLOOR`, `ATTENTION_ALLOCATION_POLICY` and
`CHANNELS_DISABLED` — joining the sixteen already there. **Insertions only, and
no schema, validator, Pydantic model, check name or record format was touched.**
Their effect is to PRESERVE digests: `source_config_hash` is byte-identical at
every schema version, and the two attention knobs never reach a manifest at all.

The engaged preset's qualification SUBJECT digest did move, from
`d47cb2bf2702…` to `f3bb65623852…` — but not because of these lines. It moved
because research now compiles ENABLED by default, which is the change the
operator asked for and whose price was measured before the code and reported
rather than avoided (that tranche's MEASUREMENTS.md). The two causes are kept
separable by a check rather than by a claim: the pin now asserts the digest AND
that none of the three knobs reaches `engine_config_json`.

`check: python -c "
import json
from deepreason.config import Config
from deepreason.run_manifest import source_config_hash
from tests.test_reusable_qualification import _manifest, _profile
c = json.loads(_manifest(_profile()).engine_config_json)
leaked = sorted(k for k in c if k in ('SEED_PROBLEM_BUDGET_FLOOR','ATTENTION_ALLOCATION_POLICY','CHANNELS_DISABLED'))
assert not leaked, leaked
h = [source_config_hash(Config(), schema_version=v) for v in (1,2,3,4,5,6)]
assert h[0]==h[1] and h[2]==h[3]==h[4]==h[5]
" && test "$(grep -c 'data.pop(\"SEED_PROBLEM_BUDGET_FLOOR\|data.pop(\"ATTENTION_ALLOCATION_POLICY\|data.pop(\"CHANNELS_DISABLED' src/deepreason/run_manifest.py)" -eq 3`

**A naming constraint this grant surfaced, worth keeping.** Every `Config` field
is echoed BY NAME inside this file's drop list, so a field name must satisfy
every invariant that greps this file. `DR-SEAM-manifest-x-schools` holds — with
a `check:` — that the words `stance`, `lineage`, `crossover` and `reseed` never
occur in `run_manifest.py`, which is what keeps the manifest unable to describe
what a SCHOOL is. The F3 knobs were first written `SEED_LINEAGE_BUDGET_FLOOR`
and `LINEAGE_ALLOCATION_POLICY`, in the operator's own vocabulary and about a
PROBLEM lineage rather than a school one, and they turned that check red. They
were renamed rather than the check carved up: a blunt tripwire is worth more
than a word, and `wander.py` keeps the vocabulary throughout.

`check: sh -c '! grep -qiE "\bstance\b|lineage|crossover|reseed" src/deepreason/run_manifest.py'`

**Rung 8 took the same grant, for ten knobs, and PROVED the preservation
directly.** `SCOPE_MAX_DEPTH`, `SCOPE_MAX_NODES`, `FRAME_SLICE_ATTACKERS`,
`FRAME_SLICE_DEPARTURES` and the six `CAPTURE14_*` values are `Config` fields
consulted at sites inside a run and never written to the manifest; each has an
unconditional `data.pop` line. The check is not "the test suite is green" but
the digest itself, compared at the tranche base and at HEAD **for every schema
version**:

```
schema  462d6091d                                                          HEAD
1       6c2d01f6b8cbe65e2a26bb57e864a80feec07b0896142fb2267bc83d2717dc81   identical
2       6c2d01f6b8cbe65e2a26bb57e864a80feec07b0896142fb2267bc83d2717dc81   identical
3-6     2624603035bc335e59da63f25426d3ae6619bf7f84d48657e8f25310de49edc5   identical
```

Ten knobs, zero digest motion. Their effect IS recorded, and more precisely
than a `Config` echo would record it: the two scope bounds travel inside each
reach certificate, and the eight capture values inside the diagnostics payload
and the `capture14-hysteresis.v1` policy artifact.

`check: test "$(grep -c 'data.pop("CAPTURE14_' src/deepreason/run_manifest.py)" -eq 6 && test "$(grep -c 'data.pop("SCOPE_MAX_\|data.pop("FRAME_SLICE_' src/deepreason/run_manifest.py)" -eq 4`
`check: python -c "from deepreason.config import Config; from deepreason.run_manifest import source_config_hash; h=[source_config_hash(Config(), schema_version=v) for v in (1,2,3,4,5,6)]; assert h[0]==h[1] and h[2]==h[3]==h[4]==h[5]" && python -m pytest tests/test_allocation_signal_consumption.py::test_the_shipped_qualification_subject_digest_does_not_move -q`

**Granted contact, 2026-08-28 — the uncarried-field disclosure (audit F-A / P10).**
The monitor FORECAST this contact in the tranche instruction and granted it
conditionally, to the discipline the four grants above record: name in FIX.md,
before implementation, exactly what moves, what cannot move, and why no
committed root changes verdict. Requested at
`experiments/2026-08-28-defect-manifest-config-disclosure/FIX.md`.

The defect it repairs: `_versioned_source_config_data` pops 25 `Config` fields
out of `engine_config_json`, and `config_from_run_manifest` is the ONLY source
of a run's `Config`, so each of them silently took its default for the whole
run and nothing anywhere said so. Twenty-two of the 25 are consumed at sites
INSIDE a run; the drop list's own justification ("it lives on Config only,
consulted at dispatch sites") is the one that fails, because on the single run
path `Config` IS the echo. Census over every committed `run-config.yaml` and
`run-manifest.json` on main:
`.../probe/census_dropped_fields.py`.

What moved: `compile_run_manifest` now emits one `ENGINE_CONFIG_FIELD_NOT_CARRIED`
compile notice per dropped field whose configured value differs from its
default, on the `CompileNoticeV1` channel the all-configurations tranche built
for exactly this. **Insertions only, and no `data.pop` line was added, removed
or made conditional** — the echo is READ, never edited, so `source_config_hash`
is byte-identical at every schema version. No Pydantic model, validator, schema
guard, serializer branch or record format was touched, so the mistake §4 names
("reading the model and not the validator") cannot arise: no validator is in
the diff.

Emission is COMPILE-TIME ONLY, and that is what keeps every committed root
fixed. A committed manifest is READ (`model_validate_json`), never recompiled;
no read path calls `compile_run_manifest`, so no notice attaches, no canonical
byte moves, and no stored verdict can change. The root sweep is retired as an
instrument (operator ruling 2026-08-22); this categorical argument is the proof,
and the census re-derives its premise on demand — 0 of 79 committed manifests
carry a notice or a dropped field.

The drop set is DERIVED from the drop list, not restated beside it, so a future
`data.pop` line joins the disclosure automatically instead of escaping it.

`check: python -c "
from deepreason.run_manifest import _unconditionally_dropped_config_fields as f
dropped = set(f())
assert {'JUDGE_SEATS_ENABLED','ADJUDICATION_STATUS_AUTHORITY_ENABLED','SCHOOL_SEATS_ENABLED','ENGAGED_CRITICISM_AUTHORITY','LEGACY_CRITICISM_ENABLED'} <= dropped, sorted(dropped)
assert 'scratchpad' not in dropped and 'bridge' not in dropped
" && python -m pytest tests/test_manifest_config_disclosure.py -q`

### 5. Anything altering qualification subject digests — `qualification.py`

The qualification cache keys on a subject digest built from the manifest, the
pair inventory and the provider profile. Change what enters that digest and
every cached "qualified" verdict refers to a subject that no longer exists.

`check: grep -q "def qualification_subject_payload" src/deepreason/qualification.py`

**Granted contact, 2026-08-28 — excluding one notice code from the subject
(audit F-A / P10).** The monitor GRANTED this contact on the record, on the
measurements rather than on the argument, after the request was written into
`experiments/2026-08-28-defect-manifest-config-disclosure/FIX.md` Amendment 1
BEFORE the code stood — the same discipline the four surface-4 grants above
record. The grant's own words: *"zero subject digests move, no cache
invalidates, no battery is owed, no schema/validator/model is touched, and the
rule generalises the committed exclusion guarantee rather than special-casing
it."*

**Why it was needed, which is the part worth remembering.** The uncarried-field
disclosure recorded under surface 4 above emits notices that NAME the dropped
`Config` field. The qualification subject is built from
`manifest.model_dump(...)`, which includes `compile_notices` — so a notice
about a subject-EXCLUDED field puts that field's name and value straight back
into the subject, defeating the exclusion by way of its own disclosure. Three
committed tests guarantee that exclusion and they are right to: these knobs
gate dispatch, not provider identity, so they must never cost a home a
~14-minute battery (Parts C/D/E, S2a/S2b/S2d, C9 —
`test_adjudication_status_authority_flag_excluded_from_subject_digest`,
`test_judge_seats_fields_excluded_from_subject_digest`,
`test_school_seats_enabled_field_excluded_from_subject_digest`). The
alternative was to INVERT all three, which is deleting a guarantee to get
green.

**The rule, stated once so a future notice code is measured against it:** a
disclosure that a subject-excluded `Config` field was not carried must not
itself enter the qualification subject, or the exclusion is defeated by its own
disclosure. It generalises the three tests rather than routing around them.

What moved: SEVEN lines in `qualification_subject_payload`, between the two
`behavior.pop(...)` lines already there, dropping notices whose code is
`ENGINE_CONFIG_FIELD_NOT_CARRIED`. **Insertions only — 7 and 0.** Every other
notice keeps its subject contribution unchanged; no schema, validator, Pydantic
model, check name or record format was touched.

**Preservation is measured per case, not argued**
(`experiments/2026-08-28-defect-manifest-config-disclosure/MEASUREMENTS.md`,
and `probe/digests_base.txt` vs `probe/digests_optionA.txt` vs
`probe/digests_optionB_narrow.txt`):

```
config                                       base          without the grant   WITH it
default                                      02ee7e098bb9  02ee7e098bb92390    identical
JUDGE_SEATS_ENABLED=True                     02ee7e098bb9  478c15619dd81fb4    identical
ADJUDICATION_STATUS_AUTHORITY_ENABLED=True   02ee7e098bb9  230c5dff627a7d37    identical
SCHOOL_SEATS_ENABLED=True                    02ee7e098bb9  170fec05dc38d47a    identical
P-T1's five switches                         02ee7e098bb9  f40357e9e31b8768    identical
a manifest already carrying an unrelated
  notice (SECOND_JUDGE_FAMILY_REQUIRED)      061efe5bdf7e  061efe5bdf7eb565    identical
```

Zero subject digests move, including for a manifest that already carried a
notice before this tranche existed — which is why the exclusion is scoped to
one notice CODE rather than to `compile_notices` wholesale. Dropping the whole
field would have moved that last row from `061efe5bdf7e…` to `ae14adca4722…`,
measured and rejected on exactly that ground.

`check: python -c "
from deepreason.qualification import qualification_subject_digest, qualification_subject_payload
from tests.test_reusable_qualification import _manifest, _profile
p = _profile()
base = qualification_subject_digest(_manifest(p), p)
assert base == '02ee7e098bb9239011708a4aa0bce4b7479619b3aff28eff46188125a869e713', base
loud = _manifest(p, config_updates={'JUDGE_SEATS_ENABLED': True, 'ADJUDICATION_STATUS_AUTHORITY_ENABLED': True, 'ENGAGED_CRITICISM_AUTHORITY': 'defended_trial', 'LEGACY_CRITICISM_ENABLED': False, 'SCHOOL_SEATS_ENABLED': True})
assert any(n.code == 'ENGINE_CONFIG_FIELD_NOT_CARRIED' for n in loud.compile_notices), loud.compile_notices
assert qualification_subject_digest(loud, p) == base
dumped = str(qualification_subject_payload(loud, p))
for field in ('JUDGE_SEATS_ENABLED', 'ADJUDICATION_STATUS_AUTHORITY_ENABLED', 'SCHOOL_SEATS_ENABLED'):
    assert field not in dumped, field
"`
`check: python -c "
from deepreason.qualification import qualification_subject_digest
from tests.test_reusable_qualification import _manifest, _profile
p = _profile()
noisy = _manifest(p, rubric_policy='require_cross_family', criticism_policy=None)
assert [n.code for n in noisy.compile_notices] == ['SECOND_JUDGE_FAMILY_REQUIRED']
assert qualification_subject_digest(noisy, p) == '061efe5bdf7eb5654c569dfab134efd47c88be0eb18134012242c295a653d754'
" && test "$(grep -c 'ENGINE_CONFIG_FIELD_NOT_CARRIED' src/deepreason/qualification.py)" -eq 1`
`check: python -m pytest tests/test_reusable_qualification.py::test_adjudication_status_authority_flag_excluded_from_subject_digest tests/test_reusable_qualification.py::test_judge_seats_fields_excluded_from_subject_digest tests/test_reusable_qualification.py::test_school_seats_enabled_field_excluded_from_subject_digest -q`

## Where authority is allowed to live instead

When a change needs a new per-run mode, put it on `Config` (`config.py`), never
on the manifest. This is the codebase's own precedent: `ARGUMENTATIVE_AUTHORITY`
is a `Config` field, while `require_distinct_families` is a manifest field
governing the proposing side only.

`check: grep -q "ARGUMENTATIVE_AUTHORITY" src/deepreason/config.py`
`check: ! grep -q "ARGUMENTATIVE_AUTHORITY" src/deepreason/run_manifest.py`

A `Config` value is invisible to replay, and a manifest field is permanent, so
`Config` is the right home for a new per-run mode. But the older form of this
sentence — "a `Config` value costs nothing to add" — is true only WITH ONE STEP
that sentence did not mention, and this is the correction: `Config` is
serialized into every manifest's `engine_config_json` and hashed into its
`source_config_hash`, both of which the qualification subject embeds. A new
field therefore moves every qualification subject digest and every frozen
manifest golden UNLESS it is dropped in
`run_manifest.py::_versioned_source_config_data`, which is what that function
exists for and what its eight prior entries did. Measured 2026-08-22 by the
two-call seat protocol tranche: without the drop, the subject digest over a
committed fixture moved from `b9038b84efdea313...` to `a5d81e5d34f51635...` and
the full gate went red in 40 places; with it, byte-identical and green. Add the
mode to `Config`, and add its key here in the same commit. See `docs/ERRATA.md`
E44.

`check: python -c "import json; from tests.test_reusable_qualification import _manifest, _profile; p = _profile(); m = _manifest(p); c = json.loads(m.engine_config_json); leaked = sorted(k for k in c if k.startswith('SPLIT_BUDGET_')); assert not leaked, leaked" && grep -q 'data.pop("SPLIT_BUDGET_SEAT_PROTOCOL", None)' src/deepreason/run_manifest.py`

**Rung 5's contact, recorded because a granted contact still gets written down.**
The v2 calculus program's promotion rung added two `Config` knobs — `K_FRAME`
(how many distinct problem lineages one subject's reach must span before a
promotion problem is spawned) and `PROMOTION_ENVIRONMENT_MAX` (how much of the
record one reach certificate may freeze) — and therefore two `data.pop` lines
here. The grant was given in advance and in the operator's own words, over
exactly this file and for exactly this reason: "new knobs on Config only, each
with its versioned-source line". The LADDER's own Rung 5 row pre-grants it
identically. What makes the contact SAFE is measured rather than argued: with
the pops, no key reaches `engine_config_json` and no qualification subject
digest moves.

`check: python -c "import json; from tests.test_reusable_qualification import _manifest, _profile; c = json.loads(_manifest(_profile()).engine_config_json); leaked = sorted(k for k in c if k in ('K_FRAME', 'PROMOTION_ENVIRONMENT_MAX')); assert not leaked, leaked; from deepreason.config import Config; assert Config().K_FRAME == 2 and Config().PROMOTION_ENVIRONMENT_MAX == 64" && grep -q 'data.pop("K_FRAME", None)' src/deepreason/run_manifest.py && grep -q 'data.pop("PROMOTION_ENVIRONMENT_MAX", None)' src/deepreason/run_manifest.py`

**Surface 5 stayed at ZERO across Rung 5, and it is checked rather than
asserted.** The whole promotion road — nomination, the six criteria, the
closure sweep — reaches no LLM seat, so the pair inventory is unchanged, no
subject digest moves, and no home owes a ~14-minute battery rerun. See
`DR-INV-axiom-basis`'s A4 preservation row for the import check that pins it.

`check: python -m pytest tests/test_promotion_solo.py::test_no_promotion_module_can_reach_a_seat -q`

**Granted contact, 2026-08-26 — `DISCHARGE_POLICY` and the discharge channel
(REBUILD F1).** The discharge-required criticism channel needs one per-run mode:
which policy preset governs how open criticisms render and how an undischarged
submission is handled. The operator forecast the contact when the tranche's
SPEC.md requested it — with `tools/blast_radius.py`'s own `"frozen_surface_
verdict": "CONTACT"` and both contact rows pasted and disposed one by one — and
granted it in those terms: "This is not an exception to the frozen surface — it
is the documented recipe (a Config field is not done WITHOUT that line; the
ENGAGED_CRITICISM_AUTHORITY trap is its ancestor)."

What moved: ONE `data.pop("DISCHARGE_POLICY", None)` line in
`_versioned_source_config_data`, joining the twelve unconditional pops already
there. **Insertions only — 9 and 0.** No schema, no validator, no Pydantic
model, no check name, no record format.

The pop is UNCONDITIONAL, and that is the grant's fourth rider rather than a
style choice: the `ENGAGED_CRITICISM_AUTHORITY` trap below is the recorded case
where scoping such a fix to `schema_version < 4` — reasoning "no pinned-hash
test exists above v3" — was itself refuted by two v5 goldens. The check above
compares the pop's line at its EXACT indent rather than asking whether the
source contains it, because the first version of that check did the latter and
a mutation proved it vacuous: an eight-space guard-scoped pop CONTAINS the
four-space string as a substring, so the check passed on the one arrangement it
existed to forbid, while v6's hash had already moved to `80425b81f1dd1ec6…`
(`experiments/2026-08-26-change-f1-discharge-criticism-channel/proof/
granted_contact_mutation.txt`, M-B). Preservation is
measured per version, not argued, and the instrument is committed:
`experiments/2026-08-26-change-f1-discharge-criticism-channel/digests.py`
prints the six `source_config_hash` values and the qualification subject digest,
and its before/after captures under that tranche's `proof/` diff EMPTY.

Surface 5 stayed at ZERO for the tranche's other half too, and that is measured
rather than assumed: the channel adds two optional wire fields to
`CompactConjectureCandidate` and `ReasoningCandidateProposal`, and the
qualification subject embeds `contract_id` STRINGS rather than any wire schema,
so the subject digest over a committed fixture is unchanged at
`b9038b84efdea313…`.

`check: python -c "
import inspect
from deepreason.run_manifest import _versioned_source_config_data as f
found = [ln for ln in inspect.getsource(f).splitlines() if ln.strip() == 'data.pop(\"DISCHARGE_POLICY\", None)']
assert found == ['    data.pop(\"DISCHARGE_POLICY\", None)'], found
"`
`check: python -c "
from deepreason.config import Config
from deepreason.run_manifest import source_config_hash
h = [source_config_hash(Config(), schema_version=v) for v in (1, 2, 3, 4, 5, 6)]
assert h[0] == h[1] == '6c2d01f6b8cbe65e2a26bb57e864a80feec07b0896142fb2267bc83d2717dc81', h
assert h[2] == h[3] == h[4] == h[5] == '2624603035bc335e59da63f25426d3ae6619bf7f84d48657e8f25310de49edc5', h
"`
`check: python -c "
import json
from tests.test_reusable_qualification import _manifest, _profile
from deepreason.qualification import qualification_subject_digest
p = _profile()
assert qualification_subject_digest(_manifest(p), p) == 'b9038b84efdea313c3f3f2a8862d8acf180d3938ab3d1bf3588c3585dfe07386'
leaked = sorted(k for k in json.loads(_manifest(p).engine_config_json) if k == 'DISCHARGE_POLICY')
assert not leaked, leaked
"`

## The instruments that prove you did not break anything

### The full gate

    python -m pytest tests/ -q -n 4

`0 failed` is the only acceptable result. Never weaken an assertion to get
green — that converts a caught defect into an uncaught one. A fixture that
depended on defective behaviour may be minimally updated ONLY when the change's
design document predicted the update in advance.

Use `python -m pytest`; bare `pytest` may resolve to a tool shim that cannot see
the editable install.

### The root sweep

Before and after any change to a reader, a guard, or an authority rule, sweep
every openable run root and diff. The instrument is committed, not per-session:

    python tools/root_sweep.py <output.txt>    # ~10 min over 42 roots

`check: python -c "import ast; ast.parse(open('tools/root_sweep.py').read())"`
`check: grep -q "verify_root_report" tools/root_sweep.py`

Fields compared:

    valid, epistemic_checks_passed, len(state.att), adjudication-blindness count,
    module_digests (ModuleFingerprintsEventPayloadV1.digest, content not just
    module_id), seat_digests (SeatBindingsEventPayloadV1.digest, content not
    just group name)

No root's `valid` and no root's `att` may change. The two sweeps should compare
byte-identical. The last two fields were added 2026-08-11 (docs/ERRATA.md E18):
the sweep previously reported only `modules=`/`seats=` identity keys
(module_id/group names), which would sweep two roots as identical even if
their fingerprinted content or bound profiles differed. Several committed
roots already carry both stamps (confirmed by the first full-tree run with
the new fields: `modules=default`/`round-robin`, `seats=coder`/`conjecture`,
each identity key mapping to exactly one digest across every root that uses
it) — the gap was live, not hypothetical, though no actual divergence was
found hiding behind it. The sweep's expected baseline is 11 ERROR lines, all
`UnsupportedRunManifestVersionError` — not a failure. Note the instrument
matters twice over: by DIRECT manifest load over every git-tracked root the
census is 28 v6 / 14 raising / 3 with no manifest (pinned by a check in
`DR-SEAM-harness-x-verification`; 25 v6 before the stress-triplet roots were
committed), while the sweep scans `experiments/` only — the three
no-manifest calibration roots live under `runs/` and never enter it — and
reads through `verify_root_report`, which surfaces three of the raisers
differently. Two true numbers, two instruments — cite the instrument with
the number.

`check: python -c "from deepreason.verification.report import verify_root_report"`

A worked example of both instruments, including the sweep script and its output
before and after a change that widened what prose may refute, is in
`experiments/2026-08-01-change-prose-can-refute/CHECKLIST.md` steps 1, 15 and 24.

### The diff budget gate (Rung G1)

Actual cumulative insertions against a ledgered ceiling, computed from the
real `git diff --numstat`, never a plan-time estimate — the gap Rung S5 fell
through twice (REQUEST.md Amendments 2 and 3): its SPEC's own headline
(220–300 lines) contradicted its own itemization (~325–435), and nothing
checked the ceiling against the ACTUAL diff until an executor noticed by
hand. `dr-execute-step` runs this gate at every `[COMMIT]` step; EXCEEDED is
a stop, decided by the calling skill, never by this tool's exit code.

    python tools/diff_budget.py <base> [--against REF] [--ceiling N] [--paths PATH ...]

`check: python -c "import ast; ast.parse(open('tools/diff_budget.py').read())"`
`check: grep -q "DIFF_BUDGET_RESULT_V1" tools/diff_budget.py`

### The blast-radius disclosure gate (Rung G6)

Given a proposed change's declared target files/symbols, computes frozen-
surface contacts (this document's own five surfaces plus the frozen-
adjacent list above), syntactic reachability (a hand-maintained entry-
point registry, BFS over an AST-based call graph, with an honest UNKNOWN
bucket for anything the walk cannot resolve — it proves a call path
exists, never that it is ever exercised at runtime), consumers (tests,
map documents, the qualification digest, the wheel-smoke pins), and a
plain-language disclosure summary — mechanically, so a grant request
never has to be hand-summarized from memory. The gap this closes: the
2026-08-09 incident below, where a tranche's own SPEC.md had already
found surface-3 contact in prose and the STOP that finding should have
forced did not happen before the commit landed — every fact this gate
reports was, in that incident and the six others cited in its own module
docstring, statically derivable from the tree at grant time.

    python tools/blast_radius.py --files PATH [PATH ...] [--symbols NAME [NAME ...]] [--against REF]

`check: python -c "import ast; ast.parse(open('tools/blast_radius.py').read())"`
`check: grep -q "BLAST_RADIUS_RESULT_V1" tools/blast_radius.py`

## Traps

- **Reading a model and not its validator.** Surface 4 above. Pydantic permits
  what the validator refuses; only the validator decides admissibility.
- **Assuming a guard is where you would have put it.** The prose-immunity guard
  sits in `informal/trial.py`, not in the criticism rule, because the criticism
  rule's own guard also governs whether a case is RECORDED. Widening the wrong
  one deletes scrutiny evidence for every target carrying a passing problem
  criterion — the criteria are instantiated into every candidate's interface.
- **A count call that is also a guarantee call.** `require_cross_family_judges`
  was used to obtain a seat COUNT, which meant a path could not ask how many
  seats it had without asserting a guarantee it did not use. `judge_seats()`
  now separates the two.
`check: grep -q "def judge_seats" src/deepreason/llm/adapter.py`
- **Renaming a typed reason string.** Decline reasons and Measure inputs are
  compared against recorded roots. `execution-backed` kept its spelling when its
  guard widened to `formally_backed`, because the string's meaning in old roots
  must not shift.
`check: grep -q '"execution-backed"' src/deepreason/informal/trial.py`
- **Adding a `Config` field is not automatically invisible to replay.**
  "A `Config` value costs nothing to add and is invisible to replay"
  (above) is true of the manifest's own schema, but `_versioned_source_
  config_data` in `run_manifest.py` is what actually keeps a NEW field out
  of `source_config_hash`/`engine_config_json`/the compiled manifest's
  `sha256` — and it must be told about each one, per schema version,
  explicitly. Adding `Config.ENGAGED_CRITICISM_AUTHORITY`
  (`experiments/2026-08-03-change-rung2-engaged-criticism-switch/`)
  broke `test_v1_v2_v3_canonical_shapes_and_hashes_remain_byte_identical`
  immediately, and a first fix scoped to `schema_version < 4` — reasoning
  "no pinned-hash test exists above v3" — was ITSELF refuted by the full
  gate: two more goldens at schema v5
  (`test_v5_canonical_bytes_match_incident_head_golden`,
  `test_incident_descriptors_and_generated_roots_are_frozen_and_deterministic`)
  failed too. "No test above v3" was a false inference from an incomplete
  grep, not a verified fact. Fixed by popping the new key
  UNCONDITIONALLY (every schema version), not by enumerating which
  versions happen to have a pinned test today. Operator-approved per
  that tranche's REQUEST.md Amendment 3 (the fix touches this file,
  surface 4). Rule for the future: a new top-level `Config` field is
  not done until `_versioned_source_config_data` has an explicit line
  for it, and "no test covers version N" must be proven by running the
  full gate, not by grepping test names.
`check: grep -q "ENGAGED_CRITICISM_AUTHORITY" src/deepreason/run_manifest.py`
- **A STOP already written in prose is not a STOP that was obeyed.**
  The CP1-M tranche's own SPEC.md correctly identified surface 3
  (`invariants.py`) as plausible contact and said so in writing — the
  finding was never the gap. The commit widening `invariants.py`
  landed anyway, with REQUEST.md's own Amendments section still reading
  "(none yet)" (`docs/ERRATA_EXECUTOR.md`, "2026-08-09 — the frozen-
  surface stop did not hold"). The work itself was correct (additive,
  reader-widening, zero committed-root verdicts moved) — X9's own rule
  applied a second time: correctness never substitutes for
  authorization. Fixed going forward by the blast-radius disclosure
  gate above: `dr-execute-step`'s own `[COMMIT]` checkpoint now diffs
  actual-touch against SPEC.md's own specced radius mechanically, so a
  prose finding three steps back cannot be silently outrun by memory.
`check: grep -q "frozen_surface_verdict" tools/blast_radius.py`
