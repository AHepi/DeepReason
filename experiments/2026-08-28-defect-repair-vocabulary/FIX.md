# Fix: one repair-`mode` vocabulary, declared once in the producer and consumed by import at the authority boundary

Guarantee restored: a `mode` value the repair writer can put into a
`repair.semantic-task.v1` payload is, by construction rather than by
agreement, a value the recovery authority accepts.

## The design question the brief asked, answered

*Is the checker meant to admit only the modes that carry authorized pointers
(so `whole_object_syntax` children are the caller's mistake), or every mode the
producer can emit (so the set should BE the producer's Literal, imported)?*

**Every mode the producer can emit, imported.** Three pieces of evidence, none
of them a reading of intent:

1. The reader already has a whole-object branch and it is the one on the
   record. `nonconjecture_recovery.py:1029-1030` reads
   `if mode == "full": return tuple(pointers), raw_value` — return the raw
   response as the entire replacement candidate, apply no patch. That is
   exactly what `V6PatchRepairSession.candidate_from_raw` does for
   `whole_object_syntax` (`llm/repair.py:1620-1622`). The reader was written
   to handle this mode and named it something the writer never says. A reader
   with no business seeing whole-object repairs would not carry the branch.
2. The structural split is a WRITER GUARANTEE, not a coincidence, and it says
   the two modes are peers rather than legal/illegal. A patch turn takes its
   pointers from `RepairDiagnosticEnvelopeV2.authorized_pointers`, which is
   `Field(min_length=1)` (`llm/repair.py:283`) — a patch repair therefore
   ALWAYS carries at least one canonical pointer. A whole-object turn is
   constructed with no `authorized_pointers` at all
   (`llm/repair.py:1605-1614`), so it ALWAYS carries none. The census the
   audit built agrees on every row of every root
   (`probes/q5_repair_payloads.json`: 36 whole-object rows with `[]` and
   `repair_index: 1`; 20 patch rows with a non-empty canonical list).
3. Refusing them would strand paid work. A `whole_object_syntax` child is a
   durable repair work item with its own reservation, its own provider
   attempt and its own admitted terminal — epoch 5's own `run-result.json`
   records five of them `completed`. A recovery path that cannot terminalize
   them does not protect an invariant; it discards work the run already
   bought and then kills the run.

So the bug is the NAME, and `full` is a name for the whole-object case that
nothing has ever emitted. Per the brief's end state, `full` is GONE rather
than kept: nothing emits it, and a value sitting in an authority boundary that
no writer can produce is exactly the thing that let the two sets drift apart
unnoticed.

## Change sites (exhaustive)

  - `src/deepreason/llm/repair.py:1499-1510` — declare the vocabulary once,
    beside the dataclass that carries it: a `V6RepairMode` alias for the
    existing `Literal`, `V6_REPAIR_TASK_MODES` DERIVED from it by
    `get_args(...) - {"initial"}` (the initial call writes no repair payload),
    and `V6_WHOLE_OBJECT_REPAIR_MODES` for the modes whose response IS the
    whole replacement object. Derived, not restated: adding a mode to the
    Literal moves both sets. `V6RepairTurn.mode` is retyped to
    `V6RepairMode` — same values, one name.
  - `src/deepreason/llm/repair.py:1620, 1661` — the producer's own two
    copies of `{"initial", "whole_object_syntax"}` become
    `V6_WHOLE_OBJECT_REPAIR_MODES`. The same distinction the reader makes,
    so it is the same object.
  - `src/deepreason/workflow/nonconjecture_recovery.py:1002` —
    `_authority(mode in {"patch", "full"}, ...)` becomes
    `_authority(mode in V6_REPAIR_TASK_MODES, ...)`, importing the name from
    `deepreason.llm.repair` (the module already imports
    `RepairDiagnosticEnvelopeV2`, `apply_repair_patch` and
    `parse_one_json_value` from there, so this adds no new dependency edge —
    `workflow/` imports `llm/` at module scope, never the reverse; see
    `DR-SEAM-llm-x-workflow`).
  - `src/deepreason/workflow/nonconjecture_recovery.py:1029` — the whole-object
    branch's guard becomes `mode in V6_WHOLE_OBJECT_REPAIR_MODES`, so the
    branch is selected by what the mode MEANS rather than by a string spelt
    twice.
  - `src/deepreason/workflow/nonconjecture_recovery.py` (new, ~4 lines, beside
    the existing pointer-canonicality check) — one authority check that mode
    and pointer shape AGREE: a whole-object repair carries no pointers, a
    patch repair carries at least one. This is the writer guarantee of point 2
    above, asserted where it is relied on, so a future mode that is misnamed
    OR mis-branched fails loudly at the boundary instead of silently returning
    a raw value where a patch was owed. Verified against the record before
    being written: it holds on all 56 payloads in all three roots.

  - `scripts/cycle_soak.py` — the soak gap, narrowed to what is actually
    missing (see REPRO.md's finding: `--induce-repairs` already exists and
    already provokes one repair, so nothing is added that exists):
      - `install_repair_inducer(limit, *, kind)` gains an `unparseable` kind
        returning a non-JSON body. The current inducer returns
        `{"soak_induced_repair": <title>}` — well-formed JSON, so a baseline
        always parses and the session can only ever take the PATCH turn.
        Only an UNPARSEABLE response reaches `whole_object_syntax`, which is
        the mode that killed epoch 5.
      - `--induce-repair-kind {invalid,unparseable,alternate}`, default
        `invalid` so every existing invocation and its recorded output are
        unchanged; `alternate` drives both modes in one soak.
      - `_attempt_facts` additionally reports `repair_modes`, read from the
        `repair.semantic-task.v1` preparations rather than inferred, and the
        D1-seat-contract seam detail carries it. This is an honesty fix the
        measurement forced: D1 reported `covered` on `repairs: 1`, a count of
        provider attempts with `attempt_index > 0`, which is not the same
        thing as a repair payload having been written and read.

  - `docs/map/SEAM-llm-x-workflow.md` — a `Traps` entry for this defect (new
    failure mode; no existing trap in `SEAM-llm-x-workflow`,
    `SEAM-rules-x-workflow` or `SUB-workflow` names the mode vocabulary), with
    a `check:` that fails if either side stops sharing the type.
  - `docs/map/SEAM-rules-x-workflow.md` — the reader's side of the same trap,
    naming `atomic_recovery.py` as the call site the record and the repro both
    identify.

## Regression artifact

`tests/test_v6_repair_mode_vocabulary.py` (committed RED in the repro phase,
`3 failed, 1 passed`) must invert to `4 passed`:
  - `test_whole_object_syntax_repair_child_recovers_instead_of_killing_the_run`
    — the epoch-5 shape through the epoch-5 call site.
  - `test_patch_repair_child_still_recovers_through_its_own_branch` — must
    KEEP passing and must still show the patch APPLIED
    (`typicality == 0.5` where the baseline carried `2.0`). This is the
    condition that stops the fix degenerating into "return the raw value for
    every mode", which would make the first test pass for the wrong reason.
  - the two vocabulary tests — the reader consumes `V6_REPAIR_TASK_MODES` by
    import and `"full"` is gone.

NEW conditions this fix must be tested against, beyond the repro:
  - the new mode/pointer-agreement check REJECTS a whole-object payload
    carrying pointers and a patch payload carrying none (both directions,
    or the check is decorative);
  - `scripts/cycle_soak.py --case epoch3 --cycles 8 --induce-repairs 2
    --induce-repair-kind unparseable` records at least one
    `whole_object_syntax` repair payload — the soak reaching, offline, the
    exact mode that has only ever been reachable live.

## Existing tests at risk

From `grep -rn 'whole_object_syntax\|"full"\|V6RepairTurn' src/ tests/`:
  - `tests/test_v6_patch_repair_and_wire.py:249`
    (`assert syntax_retry.mode == "whole_object_syntax"`) — must keep passing;
    the Literal's VALUES do not change, only the name of the type.
  - `tests/test_v6_live_repair_transactions.py:349`
    (`assert work[1].preparation.task_payload_value["mode"] ==
    "whole_object_syntax"`) — must keep passing; it pins the writer, which is
    unchanged. It is also the pre-existing proof that the writer emits the
    value the reader rejected.
  - `tests/test_v6_nonconjecture_recovery.py:1295` — builds a
    `repair.semantic-task.v1` payload by hand; its mode and pointer shape must
    satisfy the new agreement check. If it carries `mode: "full"` it is a
    fixture that depended on a value nothing emits and is updated to the real
    vocabulary; if it carries `patch` with pointers it is untouched.
  - `tests/test_v6_engaged_repair_verification.py` — already extended in the
    repro phase by one parameter; its own assertions
    (`work[1]...["mode"] == "patch"`) are unchanged.
  - No test asserts `{"patch", "full"}` or the string `"full"` as a repair
    mode anywhere; `grep -rn 'repair mode' tests/` is empty.

## Explicitly not changed

`src/deepreason/invariants.py:775`
(`payload.get("mode") == "patch"` inside `_is_patch_repair_semantic_rejection`)
and every other positive single-mode filter. That line asks "is this ONE
particular mode?", which is a correct question that needs no vocabulary; it is
not a second copy of the set, and widening it would change which provider rows
`verify_root` treats as semantic rejections — a replay-validation record
format question on FROZEN SURFACE 3. Reading one member of a vocabulary is not
owning the vocabulary. Not touched, not imported into, not tested against.

Also not changed: the four other windows' cones (`llm/layout.py`,
`llm/packs.py`, `llm/roles.py`, `informal/trial.py`; `run_manifest.py`,
`preparation.py`; `premises.py`, `rules/crit.py`) — none is needed. `rules/`
is read only to name the call site; `rules/conj.py` is not modified.

## Frozen-surface check

None of the five frozen surfaces is in the cone. `capabilities/state.py`,
`harness.py`, `invariants.py`, `verification/`, `run_manifest.py`,
`qualification.py` and the frozen-adjacent `route_fingerprint` in
`llm/firewall.py` are all untouched. No record FORMAT changes: the payload's
written bytes are identical before and after — this fix moves only what a
READER accepts, which is the direction the fix rules require. Committed roots
containing `whole_object_syntax` payloads become MORE readable, never less.

## Estimated diff

~30 lines of production code across 2 files (`llm/repair.py` ~14,
`workflow/nonconjecture_recovery.py` ~12, both counting comments), plus ~45
lines in `scripts/cycle_soak.py` (an instrument, not the harness), ~150 lines
of tests, and 2 map entries. Production total well under the 150-line budget;
class is `defect` with no frozen surface, so this proceeds to
`dr-implement-fix` without an operator stop.

---

## Amendment 1 (during implementation) — one change site FIX.md missed

**Added change site: `scripts/wheel_operational_smoke.py`, the loopback
handler's response serialization (~6 lines).**

What forced it: the soak's stub server serializes whatever
`response_for_schema` returns with
`content = json.dumps(response, sort_keys=True, separators=(",", ":"))`
(`wheel_operational_smoke.py:1216`). So an "unparseable" induction that
returns a Python string arrives at the adapter as a QUOTED JSON string —
`"I cannot answer that as JSON. {{{"` — which is one complete JSON value.
`parse_one_json_value` accepts it (`llm/repair.py:446`,
`JSONDecoder().raw_decode`), `candidate_from_raw` sets `_pending_candidate`,
and `note_invalid` takes the `invalid_value_parseable = True` branch
(`llm/repair.py:1683-1696`) — a PATCH turn, which is the mode the soak could
already reach. There is no value `json.dumps` can emit that is not valid JSON,
so the induction cannot be made to work from `cycle_soak.py` alone.

The change: a `RawResponse(str)` marker in the smoke, and one branch in the
handler that serves a `RawResponse` verbatim instead of encoding it. Every
existing return value is untouched and still encoded, so no existing stage of
`wheel_operational_smoke.py` or `cycle_soak.py` changes behaviour. This
keeps the module's own rule — "the stub is REUSED, never re-minted; a second
stub would be a second thing to keep true" (`cycle_soak.py:35-38`) — which is
exactly the reason not to solve this by minting a second server in the soak.

Not a public-surface change (no console entry point, MCP tool, schema sha or
wheel-layout pin touched), but `scripts/wheel_smoke.py`,
`python -u scripts/wheel_operational_smoke.py` and
`tests/test_wheel_operational.py` — which loads this module by path — are all
run before the commit, since this is the file they exercise.

Revised estimated diff: production code unchanged at ~30 lines across the two
`src/` files; instruments now ~50 lines in `scripts/cycle_soak.py` plus ~6 in
`scripts/wheel_operational_smoke.py`.

## Amendment 2 (during implementation) — one planned test could not be written as planned, and was replaced

FIX.md's regression conditions asked that the new mode/pointer-agreement check
be shown to reject BOTH directions, "or the check is decorative". Writing it
revealed why that is not reachable through the ordinary path: a repair
payload is digest-bound to its preparation by
`_trigger(preparation, payload, "repair:")`, which recomputes
`"repair:" + sha256(canonical_json(payload))`
(`nonconjecture_recovery.py:162-164`). A payload with a substituted field
therefore fails the TRIGGER check before it ever reaches the mode or pointer
checks, and no writer can produce a disagreeing payload in the first place.

Resolved, not dropped: the two direction tests call `_repair_authority`
directly over a real recorded repair — real harness, real work item, real
preparation, real raw value — with `_trigger` stubbed for that one call and
the reason stated in the helper's docstring. That makes the agreement check
mutation-provable, and it was mutation-proved: replacing the condition with
`True` turns both tests red (one gets "repair envelope pointers differ"
instead, the other stops raising), and restoring it returns 7 passed. A third
test then pins the WRITER guarantee the check depends on, read from both
fixture roots rather than reasoned about.
