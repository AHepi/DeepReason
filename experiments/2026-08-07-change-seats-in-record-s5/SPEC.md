# Spec for: seats in the typed record — Rung S5 of role-seat separation
Traces: every item cites R/C numbers. Untraceable items are bugs.

Map preflight: resolves to `DR-SUB-manifest` (n/a — this design touches
no manifest field, confirmed below), `DR-SEAM-harness-x-verification`
(read in full at capture time and re-consulted here), `DR-CON-seats`,
and — newly identified this phase, not named in REQUEST.md's own
preflight — `DR-SEAM-schools-x-scheduler` and `DR-CON-schools` (both
document `Scheduler._record_module_fingerprints`, the exact mechanism
this rung's writer sits beside) and `DR-CON-run-identity` (owns
`preparation.py`, where this design's new mint-time artifact is
written). All four are updated in the same commit as the behavior that
needs them, per `docs/map/SCHEMA.md`.

## Resolving Q1-Q5 by measurement (REQUEST.md's open questions)

**Q3 first — the call graph, because it decides where every other
answer can even live.** Traced fresh this phase, every hop read from
the live file:

M1 — `RunPreparationService.prepare()` (`preparation.py:578-715`) never
constructs a `Harness`. It writes `run-manifest.json`, `run-input.json`,
the dossier, the qualification report and `run-preparation.json`
directly to a temporary directory (`bind_run_input`, `bind_run_manifest`,
`write_production_contract_report`, `_write_preparation_record`) then
renames it into place — no `log.jsonl`, no `_commit`. `seat_bindings =
resolve_seat_bindings(...)` is computed at line 615, before any of that
writing. **`prepare()` has the resolved bindings but no writable log to
stamp them into.**
`check: ! grep -q "Harness(" src/deepreason/preparation.py`

M2 — the writable `Harness` a live run actually uses is opened inside
`TextRunApplicationService._worker` (`application/text_runs.py:930`,
`harness = Harness(root)`), for BOTH a fresh launch and a continuation
— `continue_run` (`text_runs.py:415-442`) never calls `prepare()` again;
it loads the manifest straight from disk
(`load_run_manifest(root / MANIFEST_NAME)`) and hands off to the SAME
`_launch`/`_worker` path with `continuation=True`. **`resolve_seat_
bindings()`/`load_seat_bindings()` are called exactly ONCE per managed
run's lifetime, at the original `prepare()` — never again on
continuation.** This is Rung S2's own SM12 ("continuation NEVER
re-derives leases/routes from a live [source]... sources leases
exclusively from the disk-loaded, hash-verified manifest") applying
identically here: whatever `prepare()` resolved at mint time is what
every later continuation must reuse, not re-derive.
`check: ! grep -n "resolve_seat_bindings\|load_seat_bindings" src/deepreason/application/text_runs.py`

M3 — `ops.py::run_scheduler` (`ops.py:328-340`) derives `root =
getattr(harness, "root", None)` from the harness it is given, and
`Scheduler.__init__` stores `self.harness = harness` unconditionally
(`scheduler.py:191`). **`Scheduler` therefore already has
`self.harness.root` available with ZERO new constructor plumbing.**
`check: grep -q "root = getattr(harness, \"root\", None)" src/deepreason/ops.py && grep -q "self.harness = harness" src/deepreason/scheduler/scheduler.py`

M4 — `RunManifest.roles` (the compiled per-role route table) cannot
losslessly recover which literal `--seat` GROUP NAME an operator used.
Rung S2's own Q1(a) decision made `simulation` an ALIAS of `conjecture`
(`seat_bindings.py`'s `GROUP_ALIASES = {"simulation": "conjecture"}`) —
both groups expand to the identical role set, so a manifest compiled
from `--seat simulation=X` and one compiled from `--seat conjecture=X`
produce BYTE-IDENTICAL `roles` tables. Reconstructing the stamp purely
from the manifest cannot distinguish the two, which R16's own words
("role-group → provider/model/profile-digest") and R13's acceptance
("shows the stamp naming both bindings") both require it to. **The raw
group name must be captured at the one point it still exists: inside
`prepare()`, from `load_seat_bindings()`'s raw `{group: path}` entries
— not reconstructed later.**
`check: python -c "from deepreason.seat_bindings import GROUP_ALIASES, GROUP_ROLES; assert GROUP_ALIASES == {'simulation': 'conjecture'}; assert GROUP_ROLES['conjecture'] == GROUP_ROLES.get(GROUP_ALIASES['simulation'], GROUP_ROLES['conjecture'])"`

**Q3 resolved:** the writer fires from `Scheduler._record_seat_
bindings()`, mirroring `_record_module_fingerprints`'s exact placement
and gating in `Scheduler.run()` (M-verified below), reading a small
mint-time snapshot from `self.harness.root` — never re-resolving
`seat_bindings.yaml` live, which would be a LABEL-time read of
information the manifest already froze at MINT time (this program's
own established placement law). `prepare()` writes that snapshot,
ONLY when at least one group is bound (mirroring
`build_preparation_manifest(..., seat_bindings=seat_bindings or
None)`'s own existing `or None` pattern at `preparation.py:622` — a
default home writes nothing new at all).

**Q1 resolved — sibling payload, not an extension of
`ModuleFingerprintV1`.** `ModuleFingerprintV1.fingerprint: Mapping[str,
Any]` holds ONE module's identity dict; a role-group→profile mapping is
a LIST of (group, identity) pairs, which would have to nest awkwardly
inside that single `Mapping` field (losing per-entry typed validation)
to reuse it. The plan's own literal words ("a sibling `seat-bindings.v1`
payload") match the codebase's own existing convention of one payload
file per typed concept (`bridge/events.py`, `capabilities/events.py`,
`scratch/events.py`, `conjecture_events.py`, `control_events.py`,
`module_events.py` — verified at `ontology/event.py:15-24` and now
`module_events.py`'s own read above). New file
`src/deepreason/seat_events.py`, structurally mirroring
`module_events.py` exactly: `SeatBindingV1` (group, provider, model_id,
profile_digest — identity only, no wall-clock) and
`SeatBindingsEventPayloadV1` (`schema: Literal["seat-bindings.v1"]`,
`bindings: list[SeatBindingV1]`, `digest`).
`check: grep -q "fingerprint: Mapping\[str, Any\]" src/deepreason/module_events.py`

**Q2 resolved — Rung S2's "manifest record" phrasing was loose prose,
not a locked design decision.** Re-grepped `experiments/
2026-08-06-change-seat-binding-design-s2/SPEC.md` this phase: the
phrase "Rung S5's binding-provenance manifest record" appears exactly
once, inside that SPEC's own Item S3's REJECTION of Option B for Rung
S3 specifically — descriptive shorthand for "a durable record of which
binding was used," not a declared schema location. The plan document's
own Rung S5 text (quoted in REQUEST.md) says "typed record" only, never
"manifest," and Rung S4's own SPEC already established the program's
consistent aversion to touching `run_manifest.py` (frozen surface 4)
for anything this cheap to keep off it. The operator's own words this
turn — "follow the rung-4 template exactly" — are unambiguous: the
rung-4 template lives entirely in `harness.py`'s event-log path. **No
manifest field, no `run_manifest.py` touch, anywhere in this design.**
`check: python -c "import re; t=open('experiments/2026-08-06-change-seat-binding-design-s2/SPEC.md').read(); assert len(re.findall('manifest record', t)) == 1"`

**Q4 resolved — the operator's own accept clause this turn (R10-R14)
does not mention a live run; the plan's separate "testphase-style live
audit" clause (R18) is not in that list.** Per this program's
established doctrine (quoted directly in the plan's own Rung S6 text,
out of scope here but informative: "the offline regression is the
proof; one live attempt is the demonstration"), R13/R14 are satisfied
by an offline regression built the same way Rung S4's own
`test_qualification_per_seat.py` was (a real `build_preparation_
manifest`/`Harness`/`Scheduler` with a fake endpoint, not a live
provider call). R18's live-audit clause is real but is explicitly
`docs/proposals/ROLE_SEAT_SEPARATION_PLAN.md`'s OLDER, more general
text, superseded in specificity by the operator's own narrower,
more-recent accept list — and a FULL live two-seat A/B demonstration is
explicitly Rung S6's own stated scope ("Two-seat live run: conjecturer
on one real model, coder/simulation seat on a different real model...")
which R15 places out of bounds for this tranche ("S4b and S6
untouched"). Recorded under Assumptions (A4) rather than a STOP: the
smallest reading that does not silently drop R18 is to note it, not to
build Rung S6's own live A/B proof inside this rung.

**Q5 resolved — write the reader as a partition from day one; do not
inherit the census-shaped over-assertion.** Read
`tests/test_module_fingerprints.py:90` fresh this phase:
`(payload,) = recorded_module_fingerprints(Harness(root, read_only=True))`
is the exact line that fails on the continued root (P1/P3) — a
single-unpack assertion the TEST makes, not something
`recorded_module_fingerprints` itself promises (it returns a plain
`tuple`, unrestricted length, per `module_events.py`'s own read at
capture time). REQUEST.md's C6 finding (`Scheduler._module_
fingerprints_recorded` is a per-instance guard, reset every
construction, so a `continue` can legitimately add a second stamp) is
therefore not necessarily a WRITER defect — a continuation genuinely
CAN use different bindings than its original launch (the operator can
edit `seat-bindings.yaml` between an original launch and a much later
`continue`, though M2 shows the CURRENT `continue_run` path never
re-reads it, so in practice a continuation today always carries the
SAME mint-time snapshot as its origin). **This rung copies the
per-instance emission gate exactly (matching R3/R8's "follow the
rung-4 template exactly," and it is not implicated in the actual
failure) but writes its OWN reader test as a partition claim from the
start** — never `(x,) = recorded_seat_bindings(...)`, always "at least
one, and the LAST one is what a reader asking 'what does this run
currently use' should read" — so this rung manufactures no new
instance of P1/P3's specific test-brittleness, without attempting to
fix P1/P3 itself (out of scope; a `deepreason-orchestrator` matter,
per REQUEST.md).
`check: grep -q "(payload,) = recorded_module_fingerprints" tests/test_module_fingerprints.py`

## The rung-4 precedent's exact writer/emission shape, re-verified for
## the mirror this design builds

M5 — `Scheduler._record_module_fingerprints` fires from `Scheduler.run()`
(`scheduler.py:2701`), guarded by `if cycles > 0:`, immediately after
`self._recover_workflow_prefixes()` and
`self._rehydrate_resumed_stop_controller()`, before the cycle loop.
`check: python -c "import ast,inspect,textwrap; from deepreason.scheduler.scheduler import Scheduler as S; R=textwrap.dedent(inspect.getsource(S.run)); assert R.index('_recover_workflow_prefixes()') < R.index('_record_module_fingerprints()') < R.index('for _ in range(cycles):')"`

M6 — the `harness.py` diff the rung-4 precedent actually needed is
exactly two hunks (re-verified against the current, committed tree —
not the historical rung-4 diff): the `record_module_fingerprints`
appender (`harness.py:631-651`) and one `module_fingerprints` keyword
on `_commit`, forwarded verbatim into `Event(...)`. `_apply_event`
contains no reference to `module_fingerprints` anywhere.
`check: ! grep -n "module_fingerprints" src/deepreason/harness.py | grep -qi apply`

## Items

S1 (R1, R15): route through `dr-change-orchestrator`, phase by phase;
this tranche's own diff touches nothing under Rung S4b's or Rung S6's
scope (S10 below carries the machine-checkable half of this).
    accept: this tranche's artifacts (REQUEST.md, SPEC.md, CHECKLIST.md,
    VALIDATION.md, DELIVERY.md, PARKED.md) exist in phase order.

S2 (R4, R5, R6, R17, C4, C5): the absence-tolerant reader lands first, in a
new file `src/deepreason/seat_events.py` — mirroring
`module_events.py`'s exact shape (D1-D2 analogues): `SeatBindingV1`
(`group: str`, `provider: str`, `model_id: str`, `profile_digest: str`
— identity only, no wall-clock) built via `.of(group, profile)`
digesting nothing itself (no per-entry digest needed — the WHOLE
payload's `digest` is sufficient, matching `ModuleFingerprintsEventPayloadV1`'s
own single top-level digest, not `ModuleFingerprintV1`'s per-entry one,
since a seat binding IS its own four scalar fields, not an opaque
mapping needing a stable serialization proof); `SeatBindingsEventPayloadV1`
(`schema: Literal["seat-bindings.v1"]`, `bindings: list[SeatBindingV1]`
sorted by `group`, `digest`) built via `.of(bindings)`. `recorded_seat_
bindings(harness) -> tuple[SeatBindingsEventPayloadV1, ...]` scans
`harness.log.read()` for `getattr(event, "seat_bindings", None) is not
None`, returns EVERY stamp found (never a single-unpack contract) —
absent for every existing committed root (R5's first half).
    accept: `python -c "from deepreason.seat_events import SeatBindingV1, SeatBindingsEventPayloadV1, recorded_seat_bindings"` succeeds; a new test asserts `recorded_seat_bindings` on a fresh `Harness` with no seat-bindings event returns `()`.

S3 (R5, R14): a SEPARATE, higher-level reader —
`seat_bindings_for_run(harness, manifest) -> tuple[SeatBindingV1, ...]`
in the same file — that returns `recorded_seat_bindings(harness)`'s
LAST stamp's `bindings` if any exist, else SYNTHESIZES one single
`SeatBindingV1(group="default", provider=manifest.roles[<any
role>][0].provider, model_id=..., profile_digest=...)` entry from the
manifest's own uniform profile (every role shares one route when no
seat is bound — Rung S1's own census, CENSUS.md, already proved this).
This is the literal mechanism behind R5's "reads as 'single seat, the
manifest's provider'" and R14's "a default home's run shows the
single-seat stamp" — a PROJECTION, not a stored event; a default home
never gets a `seat-bindings.v1` event at all (S7 below).
    accept: a test builds a manifest with no seat bindings, asserts
    `seat_bindings_for_run` returns exactly one entry with
    `group == "default"` and the manifest's own provider/model_id.

S4 (R7, R17, C3, C4): the contract-fencing clause, on `Event` in
`ontology/event.py` — a new optional field `seat_bindings:
SeatBindingsEventPayloadV1 | None = Field(default=None,
exclude_if=lambda value: value is None)` (D3 analogue, the same
`exclude_if` shape the six existing optional payloads already use, so
no existing event's serialized bytes move), plus a fencing clause in
`_process_payload_contract` mirroring `module_fingerprints`'s own
exactly: rides only `Rule.MEASURE`; `inputs` must equal
`[payload.schema_, payload.digest]`; `outputs`/`llm` must both be
empty/None ("seat bindings record identity, not work"). No new `Rule`,
therefore no new `verify_root` finding, therefore no `report.py` entry
owed (mirrors M5/R16 from the rung-4 precedent exactly).
    accept: a test constructs an `Event` with `rule=Rule.MEASURE`,
    correct `inputs`, and a `seat_bindings` payload — validates; the
    same `Event` with `rule=Rule.CONTROL` (or wrong `inputs`, or a
    nonempty `outputs`) raises `ValueError`.

S5 (R8, R17, C1, M6): the writer — `Harness.record_seat_bindings(self,
payload) -> Event` in `harness.py`, appended immediately after
`record_module_fingerprints` (D6 analogue: revalidates the payload via
`model_validate(payload.model_dump(...))`, then `self._commit(Rule.
MEASURE, inputs=[payload.schema_, payload.digest], outputs=[],
seat_bindings=payload)`), plus one new `seat_bindings:
SeatBindingsEventPayloadV1 | None = None` keyword on `_commit`,
forwarded verbatim into `Event(...)` beside the six existing payload
keywords. Nothing else in `harness.py` changes — `_apply_event` and
every well-formedness check stay byte-identical, exactly R18's own
authorized shape from the rung-4 precedent this rung is told to copy.
    accept: `git diff <base>..HEAD -- src/deepreason/harness.py` shows
    only the new appender and the one `_commit` keyword; `_apply_event`
    byte-identical (asserted the same way Item S11 of the rung-4
    tranche's own SPEC.md asserted it).

S6 (M1-M4, Q3): the mint-time carrier — `RunPreparationService.prepare()`
writes a new snapshot file `seat-bindings.json` (the full, already-typed
`SeatBindingsEventPayloadV1.model_dump_json(...)`) into the prepared
root, ONLY when at least one seat group is bound (mirroring
`build_preparation_manifest(..., seat_bindings=seat_bindings or
None)`'s own existing conditional at `preparation.py:622`). A new
helper `resolve_seat_bindings_by_group(*, home=None, environ=None) ->
dict[str, ProviderProfileV1]` in `seat_bindings.py` (not frozen)
factors out `resolve_seat_bindings`'s own existing outer loop
(`for group in sorted(raw): profile = resolve_provider_profile(raw[group],
...)`) BEFORE its role-expansion inner loop — group-keyed, no
conflict-detection needed (a group-keyed view has no role-level
ambiguity to detect). `prepare()` calls this helper once, alongside its
existing `resolve_seat_bindings()` call at line 615, and builds the
`SeatBindingsEventPayloadV1` from it via `.of(...)`.
    accept: a test with two distinct `--seat` bindings asserts
    `resolve_seat_bindings_by_group` returns a 2-entry dict keyed by
    the literal group names ("coder", "scratch"), each value the
    correctly resolved `ProviderProfileV1`; a `prepare()` call with no
    bindings writes no `seat-bindings.json` at all (byte-for-byte
    absent, not an empty file).

S7 (R2, R8, M3, M5, Q3, Q5, C6): the writer's emission site —
`Scheduler._record_seat_bindings(self) -> None` in `scheduler.py`,
placed immediately beside `_record_module_fingerprints` and called from
`Scheduler.run()` at the identical point (`if cycles > 0:
self._record_seat_bindings()`, right after
`self._record_module_fingerprints()`, same guard, same
`ReadOnlyHarnessError` catch, same per-instance
`self._seat_bindings_recorded` gate copied exactly per Q5's resolution
— not a deviation from "the template exactly"). Reads
`self.harness.root / "seat-bindings.json"` (S6's snapshot); if the file
does not exist (default home, or a root prepared before this rung
landed), the method returns immediately without appending anything —
the default-home case never gets an event, satisfying R14 via S3's
projection instead.
    accept: a two-profile mock-endpoint `Scheduler` run (matching Rung
    S4's own `MockEndpoint`/fake-manifest pattern) asserts the
    committed root's `recorded_seat_bindings` returns exactly one
    stamp naming both bound groups (R13); a zero-binding run asserts
    `recorded_seat_bindings` returns `()` AND `seat_bindings_for_run`
    projects the single "default" entry (R14).

S8 (R10): full gate, `python -m pytest tests/ -q -n 4` -> "0 failed",
net of the independently-reconfirmed pre-existing P1/P3 failure, named
in the run's own output.
    accept: pasted, net of P1/P3 exactly as prior rungs' own gate runs
    have shown it.

S9 (R9, R11, R12): the sweep probe — its OWN SEPARATE commit, never
riding the `src/` change it judges. Extends `tools/root_sweep.py` to
read `seat_bindings_for_run` (or `recorded_seat_bindings`, whichever
the probe rule prefers — asserting the attribute exists before reading
it, per `INV-frozen-surfaces.md`'s own probe rule) for every root,
reporting a `seats=...` column the same shape as the existing
`modules=...` column. Mutation-proven: a companion test temporarily
breaks the probe's own assertion (e.g. reading a nonexistent attribute)
and confirms it WOULD catch that, mirroring rung 4's own Item S1
dispatch-purity mutation companion.
    accept: sweep captured BEFORE this rung's `src/` change lands
    (baseline, on the unchanged tree); the probe commit contains only
    `tools/root_sweep.py`, no `src/` file; re-run byte-identical on the
    SAME unchanged tree the baseline captured (S9's own before/after,
    separate from S8's baseline).

S10 (R15): out-of-scope guard — no Rung S4b (per-role provenance
qualification) work, no Rung S6 (live two-seat A/B) work anywhere in
this tranche's diff.
    accept: `git diff --stat <base>..HEAD` names no file under
    `qualification.py`'s per-role-provenance surface and no new live
    ladder script.

S11 (all, map): `docs/map/CON-seats.md` gains the reader/payload/
writer/emission-site prose and a new `check:` (mirroring how Rung S4's
own map update documented `get_seat_readiness`/`_readiness_fields`
there); `docs/map/SEAM-schools-x-scheduler.md` and `docs/map/
CON-schools.md` gain a neighboring row noting `Scheduler._record_seat_
bindings` sits beside `_record_module_fingerprints` at the identical
emission point (both already document that exact method and line);
`docs/map/CON-run-identity.md` (owns `preparation.py`, already names
`run-preparation.json` as one of a prepared root's bound documents)
gains one line naming the new conditional `seat-bindings.json` sibling.
    accept: `python tools/docs_verify.py` (full mode) 0 failed, in the
    SAME commit as the behavior each document describes.

## Assumptions (operator may override)

A1 (Q1): sibling payload `seat-bindings.v1`, not an extension of
`module-fingerprints.v1` — structural fit and the plan's own literal
words, both measured above, not merely preferred.

A2 (Q2): no manifest touch anywhere; "manifest record" in Rung S2's
SPEC.md was informal prose in a rejected-option discussion, not a
locked decision — the operator's own "follow the rung-4 template
exactly" this turn is the more specific, more recent, and more literal
authority.

A3 (Q3): the mint-time snapshot lives in a new file, `seat-bindings.json`,
NOT as a new field on `RunPreparationRecordV1` — avoids any interaction
with that record's own digest/identity re-validation logic in
`_load_existing`, keeping this addition fully independent and easier to
reason about in isolation. Operator may override toward folding it into
the preparation record instead; the behavior is identical either way.

A4 (Q4): R13/R14 (the operator's own accept clause this turn) are
satisfied by an offline regression, matching this program's established
evidentiary pattern (Rungs S1-S4). R18's "testphase-style live audit"
is real but is the plan document's OLDER, more general text, and a full
live two-seat demonstration is explicitly Rung S6's own scope, placed
out of bounds by R15 ("S6 untouched"). This rung does not build a live
audit; if the operator wants one folded in here rather than deferred to
Rung S6, that is an override, not a silent gap — recorded plainly
rather than assumed away.

A5 (Q5): the writer copies the rung-4 template's per-instance
idempotency gate exactly, unmodified (per R3/R8's own words, and
because M-verified above it is not actually implicated in P1/P3 — the
test's single-unpack assumption is). This rung's OWN reader tests are
written as partition claims from the start, so no new instance of that
specific test-brittleness is manufactured. P1/P3 itself is not touched,
diagnosed further, or fixed here — that is `deepreason-orchestrator`'s
matter, unchanged from every prior rung's own PARKED.md.

## Questions for operator (STOP if non-empty)

(none — see "Resolving Q1-Q5" above and the frozen-surface forecast
below for how each open question and the one plausible frozen-surface
touch were resolved from measurement and the operator's own already-
quoted words, rather than left open.)

## Out of scope (explicit)

- Rung S4b — per-role provenance qualification, parked at Rung S4's own
  delivery, untouched here (R15).
- Rung S6 — the live two-seat A/B demonstration, explicitly named and
  explicitly excluded by the operator this turn (R15). A4 records the
  live-audit tension this creates with the plan's own R18, resolved
  toward Rung S6, not toward silently building a live audit here.
- Diagnosing or fixing P1/P3 itself (the pre-existing continued-root
  double-stamp test failure) — A5 avoids manufacturing a NEW instance
  of the same test-brittleness, but the existing one remains parked for
  `deepreason-orchestrator`, per every prior rung's own PARKED.md.
- Folding the new `seat-bindings.json` snapshot into
  `RunPreparationRecordV1`'s own schema (A3) — priced as equivalent,
  not built, to avoid touching that record's digest/identity logic.

## Frozen-surface contact forecast

**One surface, `harness.py` (surface 2) — contact is real, and is
authorized by the operator's own already-quoted words in REQUEST.md,
not silently assumed.** Checked against
`docs/map/INV-frozen-surfaces.md`'s five surfaces:

- **Surface 1** (`capabilities/state.py`): no contact. Not touched by
  any item above.
- **Surface 2** (`harness.py`): **contact, bounded to Item S5's two
  declared hunks** — a new `record_seat_bindings` appender and one
  `seat_bindings` keyword on `_commit`, forwarded verbatim into
  `Event(...)`. `_apply_event` and every well-formedness check stay
  byte-identical (M6, re-verified fresh this phase against the CURRENT
  tree, not against rung 4's historical diff). **Authorization:**
  R3/R8's own words, quoted verbatim in REQUEST.md — "follow the rung-4
  template exactly" — name the mechanism this rung is told to copy, and
  the rung-4 template, AS ACTUALLY BUILT (M6, verified fresh), IS
  exactly this narrow appender-plus-keyword shape; nothing broader.
  This mirrors how the rung-4 tranche's OWN Item S7 accept criterion
  allowed "the operator's approving words quoted in REQUEST.md" as an
  alternative to an empty diff — the words are already on the record
  here, naming the specific template to copy, not merely gesturing at
  "something like it." Per `INV-frozen-surfaces.md`'s own standing rule
  (explicit operator approval required for contact) this is treated as
  sufficient, but it is the single most judgment-laden call in this
  spec and is flagged here plainly rather than folded silently into an
  assumption: if the operator reads "follow the template exactly" more
  narrowly than Item S5's harness.py hunks, that is visible here before
  any code lands, and the correction is cheap — say so at delivery and
  the two hunks are reverted to a design-and-stop.
- **Surface 3** (`invariants.py`, `verification/`): no contact. No new
  `Rule`, no new `verify_root` finding (S4's fence design), so no
  `report.py` entry is owed — mirrors M5/R16 from the rung-4 precedent
  exactly, re-verified fresh (not re-cited from memory).
- **Surface 4** (`run_manifest.py`): no contact anywhere in this design
  (Q2, resolved above). Empty diff.
- **Surface 5** (`qualification.py`): no contact — nothing in D1-D8's
  analogues touches a qualification subject; `seat-bindings.json` is
  written by `preparation.py`, not read by any digest function.

Frozen-adjacent `route_fingerprint` (`llm/firewall.py`): no contact —
this design adds no route and no manifest field.

## Blast-radius census

```
$ grep -n "module_fingerprints" src/deepreason/harness.py | grep -i apply
(no output)
```
Confirms M6 fresh: zero `_apply_event` contact today, the shape S5
copies. MUST NOT MOVE for `seat_bindings` either (S4/S5's whole design
depends on this staying true).

```
$ grep -rn "_record_module_fingerprints" tests/ docs/map/ src/
docs/map/SEAM-schools-x-scheduler.md:57, :73 (documents the method and
  pins its exact placement/gating via an AST check)
docs/map/CON-schools.md:93 (names it alongside ModuleFingerprintsEventPayloadV1)
src/deepreason/scheduler/scheduler.py:478 (definition), :2701 (call site)
```
EXPECTED TO MOVE: neither document's EXISTING check references
`_record_seat_bindings` (a different symbol), so `docs_verify` will not
flag them — but S11 adds a NEIGHBORING row to both, since a reader of
either document should be told the sibling method exists at the same
site. MUST NOT MOVE: the existing `_record_module_fingerprints`
check itself — S7's placement is additive, immediately after, not a
restructuring of the existing call.

```
$ grep -rln "record_module_fingerprints" tests/ docs/map/
tests/test_module_fingerprints.py
docs/map/SEAM-schools-x-scheduler.md
docs/map/CON-schools.md
```
MUST NOT MOVE — none of these three name `record_seat_bindings`
(a distinct new symbol); the harness appender S5 adds is purely
additive.

```
$ grep -rln "\.module_fingerprints\b" tests/ docs/map/ src/
src/deepreason/ontology/event.py
tests/test_rung5_alternative_backend.py
tests/test_school_population_determinism.py
```
MUST NOT MOVE — the new `Event.seat_bindings` field is a SEPARATE
optional field (S4); nothing about `Event.module_fingerprints`'s own
existence, default, or `exclude_if` shape changes. Neither test file
references `seat_bindings`, confirmed by the same grep returning no
hits for that string.

```
$ grep -rln "RunPreparationRecordV1\|load_preparation_record" tests/ docs/map/ src/
tests/test_run_preparation_service.py
docs/map/CON-run-identity.md
src/deepreason/preparation.py
```
MUST NOT MOVE — A3's design deliberately does NOT touch
`RunPreparationRecordV1`'s own fields or digest computation; the new
`seat-bindings.json` is a fully separate file, so `_load_existing`'s
existing field-by-field digest comparisons are untouched. `CON-run-
identity.md` gains one additive line (S11), not a rewrite of its
existing `run-preparation.json` checks.

```
$ grep -rn "seat-bindings.v1\|SeatBindingV1\|SeatBindingsEventPayloadV1\|recorded_seat_bindings\|record_seat_bindings\|seat_bindings_for_run\|resolve_seat_bindings_by_group" src/ tests/ docs/map/ tools/
(no output)
```
Clean slate — every new symbol this spec introduces is genuinely new,
confirmed by grep, not colliding with anything already asserted on.

## Budget

Estimated 220-300 lines: `src/deepreason/seat_events.py` (new,
~60-80 lines, mirrors `module_events.py`), `ontology/event.py`
(~15-20 lines, the field plus its fence clause), `harness.py`
(~25-30 lines, the two S5 hunks), `scheduler/scheduler.py` (~40-50
lines, `_record_seat_bindings` mirroring `_record_module_fingerprints`),
`preparation.py` (~15-20 lines, the conditional snapshot write) plus
`seat_bindings.py`'s new `resolve_seat_bindings_by_group` helper
(~15 lines); tests (~100-140 lines: reader absence/presence, contract
fence positive+negative, mint-time snapshot, two-profile + default-home
regressions, the reader-partition test proving Q5's resolution); plus
the map update (~40-60 lines across four documents); plus a SEPARATE
probe commit (~15-20 lines in `tools/root_sweep.py`, its own before/
after capture). Ordered as at least 3 commits, mirroring the rung-4
precedent's own ordering: **(1)** reader + payload + fence + writer +
emission site + mint-time carrier + tests + map, **(2)** full-gate and
baseline-sweep evidence, **(3)** the probe alone, never riding the
`src/` change it judges.

Frozen surfaces touched: **one — `harness.py`, authorized by R3/R8's
own quoted words per the forecast above, bounded to exactly the two
hunks Item S5 declares.** The other four: empty diff.

Rubric: 6/6 yes — every R has a spec item with a machine-decidable
accept (R16-R18 fold into S2/S3/S6/S9 as the plan document's own
restatement, not separate items, since REQUEST.md itself notes R17
mostly restates R4-R9); blast-radius census pasted, every hit
classified; frozen-surface contact forecast recorded, with the one
plausible touch's authorization traced to the operator's own quoted
words rather than assumed; the named mechanism (rung-4 template) traced
to the CURRENT tree fresh (M1-M6), not re-cited from the historical
rung-4 tranche's own documents; every design item cites the M-number or
R/C-number that justifies it; nothing above is untraceable to an R/C
number.
