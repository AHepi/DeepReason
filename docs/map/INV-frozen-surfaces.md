<!-- DR-INV-frozen-surfaces -->
Verified-at: e9fac8671
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

### 5. Anything altering qualification subject digests — `qualification.py`

The qualification cache keys on a subject digest built from the manifest, the
pair inventory and the provider profile. Change what enters that digest and
every cached "qualified" verdict refers to a subject that no longer exists.

`check: grep -q "def qualification_subject_payload" src/deepreason/qualification.py`

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
