# DIAGNOSIS — why the conjecturer seat exhausted its repair budget

Root under diagnosis:
`experiments/2026-08-22-live-reach-rich-run/failed-epoch1-run-40e713b30a147dfc1a0f73feb91fa67a493454f6103a452888b8e08713368c4c`

Re-derive everything below in one command:

    python experiments/2026-08-22-fix-repair-patch-transport/repair_turn_census.py \
      experiments/2026-08-22-live-reach-rich-run/failed-epoch1-run-40e713b3…

Output committed as `repair-turn-census.json`.

---

## Finding 0 — the commissioning premise is falsified by the record

**There were no off-target patches.** All 13 v6 repair turns dispatched in the
run were answered with a patch addressed inside that turn's own dispatched
`authorized_pointers`. `repair-turn-census.json` reports
`off_target_repairs: []` and `verdicts: {applied: 7, wire_rejected: 6}`.

### Why the parked census said otherwise

`experiments/2026-08-22-live-reach-rich-run/repair_census.py` reads the
authorized set from the provider attempt's own `diagnostic_ref`. For a repair
turn, `workflow/repair_transaction.py::_terminalize_invalid` writes that field
as `trace_ref or next_diagnostic_ref` — the diagnostic derived *after* the
response was applied. So the script compares attempt N's patch against attempt
N+1's authority. Any converging repair, which by definition moves the pointer
on, is scored off-target.

The dispatched authority is elsewhere and is frozen before issue: the work
preparation's `repair.semantic-task.v1` payload, carrying
`authorized_pointers`, `diagnostic_ref` and `baseline_sha256`. Joining
`provider_attempt.work_id -> preparation.id` reads it.

### The specific case named in PARKED P7-reach, checked byte by byte

`conjecturer.atomic-candidate.v1`, repair #4:

| | |
|---|---|
| preparation payload `authorized_pointers` | `["/candidate/checker_specs/0/terms"]` |
| dispatched envelope (`blobs/43/433c086d…`) diagnostic | `extra field at /candidate/checker_specs/0/terms` |
| recorded raw response (`blobs/9b/9b29d126…`) | `{"op":"remove","path":"/candidate/checker_specs/0/terms"}` |

The patch is **exactly on target**, and it was applied.

`blobs/11/11659d8c…` — the envelope PARKED P7 cites as the authority, with
`authorized_pointers ["/candidate/checker_specs/1/id"]` — is the diagnostic
derived from the document *after* that removal. Two independent confirmations:
its `baseline_sha256` differs from the dispatched payload's
(`1a478807191f3af7…`), and its `frozen_subtree_hashes` list no longer contains
`/candidate/checker_specs/0/terms`, the subtree the patch had just removed.

The sibling-index appearance is an artifact of that pairing, not seat behaviour.

---

## Finding 1 — the primary cause: lossless transport spellings are discarded,
## and each discard consumes a metered repair grant

Six of the 13 repair turns were lost at the wire boundary — `tolerant_patch_value`
followed by `RepairPatchV1.model_validate` — never reaching
`apply_repair_patch`. Every one of the six carried a legal operation and a
pointer inside its authorized set. They were discarded on *spelling*:

| contract | # | recorded response shape | why it was lost |
|---|---|---|---|
| `batch-critic.v2` | 1 | `{"patch": [ {op, path, value} ]}` | container key `patch` is not an unwrapped wrapper |
| `batch-critic.v2` | 2 | `{"patch": {op, path, value}}` | same |
| `batch-critic.v2` | 2 | `{"contract", "operations":[{operation, path, value}], "schema"}` | `contract` echo + container key `operations` |
| `conjecturer.atomic-candidate.v1` | 1 | `{"repair.patch.v1": {"baseline_sha256", "patches":[{op, path, old, new:null}]}}` | `old`/`new` in place of `value` |
| `conjecturer.atomic-candidate.v1` | 3 | `{"repair.patch.v1": {"pointer", "op":"remove"}}` | pointer field spelled `pointer`, not `path` |
| `conjecturer.turn.v6` | 4 | `{"repair.patch.v1": {"contract", "pointer", "operation":"replace", "value"}}` | `contract` echo + `pointer` spelling |

This is the same tolerance class `tolerant_patch_value` already exists to
absorb. Its docstring records two earlier members, both observed live and both
admitted: the `{"repair.patch.v1": …}` wrapper key, and the `operation` → `op`
rename ("the one-key rename is lossless when `op` is absent and the value is a
legal operation"). Five of the six above differ from those only in which
synonym or which container name the model reached for.

**The budget consequence.** In `V6PatchRepairSession.note_invalid` a patch-mode
rejection returns the already-bound envelope unchanged — the next grant re-asks
the identical question. That re-ask mechanism demonstrably works: after
`atomic-candidate` #1 and #3 were discarded, #2 and #4 re-asked the same
pointer and succeeded. But each discard costs one of the contract's finite
`maximum_schema_repairs`, and the grant meters provider calls
(`observed_provider_calls 5 / maximum 5` in the cause object). So a spelling
miss spends the budget reserved for answering the question.

### The fatal chain, in full

`conjecturer.turn.v6`, parent work `sha256:eba68d26…`, four diagnostics and four
grants — a perfectly convergent repair that ran out one rename short:

| grant | authorized set | response | outcome |
|---|---|---|---|
| #1 | 4 pointers | `replace /scratch_proposal/links/0/to_ref` = `"NEW_001"` | applied |
| #2 | 3 pointers | `replace /scratch_proposal/links/1/to_ref` = `"NEW_002"` | applied |
| #3 | 2 pointers | `replace /scratch_proposal/unresolved_questions/0/related_refs` = `["NEW_001"]` | applied |
| #4 | 1 pointer | `replace /scratch_proposal/unresolved_questions/1/related_refs` = `["NEW_002"]` | **discarded — `pointer` for `path`** |

Grant #4's edit is the structural twin of grant #3's, which had just been
accepted: the same operation, at the sibling slot, with the same value shape.
The dispatched envelope at #4 listed exactly one remaining diagnostic —
`unresolved questions may use only visible/local scratch refs` — and the
baseline shows `related_refs = ["SRC_005","SRC_008","NEW_002"]`, i.e. two
formal source aliases where only local scratch refs are admissible. Replacing
it with `["NEW_002"]` removes precisely the two illegal refs.

The seat had written a correct answer. The harness could not read the envelope
it was written in, and the grant that would have carried it was already spent.

`conjecturer.atomic-candidate.v1` is the same story with two discards (#1, #3)
rather than one: #4 finally applied, and the document that emerged had a
further diagnostic with no grant left to spend on it.

---

## Finding 2 — one of the six is a genuine, correct rejection

`atomic-candidate` #1 returned `{"op":"replace","path":…,"old":"uhi-energy-balance@v1","new":null}`.
`RepairPatchV1` requires `value` for a non-remove operation. Reading `new` as
`value` is an inference about intent, not a rename of a field the harness
supplied. This one must stay a typed rejection, and any fix that "recovers" it
has widened tolerance past losslessness.

That is the line the fix must hold: **absorb only what the harness itself can
prove costs no information.**

---

## The fork the record closes

The tranche instruction offered (a) a harness defect in the repair loop or its
prompt, and (b) seat behaviour to be defended against with
reject-without-consuming semantics, noting they might compose.

- **(b) is ruled out for its stated reason.** The seat does not mangle array
  indices; it patched the authorized pointer 13 times out of 13.
- **(a) is confirmed, but not at the site proposed.** The diagnostic envelope
  does not under-specify the target: it names the pointer explicitly, and
  `repair_patch_response_schema` narrows the provider's `path` field to an enum
  of exactly the authorized pointers. Nothing about the target was ambiguous.
  The defect is one layer down, in what the harness will accept as a spelling
  of the answer.
- **Reject-without-consuming is rejected as the remedy.** The grant meters
  provider calls, not parses; the provider call has already happened by the
  time the spelling is seen. Not consuming it would issue a sixth call against
  a five-call ceiling — the unmetered retry loop the instruction warns against.
  The right move is to remove the reason the grants were wasted, not to make
  waste free.

## Primary cause, stated once

`llm/repair.py::tolerant_patch_value` absorbs a strict subset of the lossless
transport spellings the provider actually emits for `repair.patch.v1`. Every
spelling it does not absorb becomes a discarded provider call that still
consumes one of the contract's finite `maximum_schema_repairs` grants, so a
convergent repair chain can exhaust its seat while holding a correct answer.

## Blast radius

`src/deepreason/llm/repair.py` (`tolerant_patch_value` and its two callers:
`V6PatchRepairSession.candidate_from_raw` and
`llm/wire.py::RepairPatchWireContract.validate_value`, which the code requires
to stay in exact agreement). No frozen surface. Nothing in `llm/firewall.py`,
`llm/adapter.py`, or allocation.
