<!-- DR-CON-conjecture-source -->
Verified-at: 7e1ab8a54
Verify: python tools/docs_verify.py
Owns: src/deepreason/rules/conj.py
Seams: DR-SEAM-rules-x-scratch
Seams-undocumented: conjecture-source x llm, conjecture-source x manifest, conjecture-source x scheduler

# Conjecture source — where a candidate artifact is proposed

## What it is

`rules/conj.py::conj` is the one entry point through which a new candidate
artifact enters the graph. It is gated on a registered problem, dispatches
by the manifest's `schema_version` (v4/v5/v6 turn contracts, plus the v6
atomic-candidate fallback), and is the ONLY module on the rules side that
both reads and writes the scratchpad (`DR-SEAM-rules-x-scratch`) — the
"socket" is this one function's contract with everything around it, not the
whole `rules/` package, which is `DR-SUB-rules`'s wider concern.

## The socket contract — what it promises, what it is handed, what it must never do

**Promises:** every admitted candidate passes the anti-relapse gate before
it can be registered; a blocked candidate registers no commitment and
emits no `Register` event.
`check: python -c "s=open('src/deepreason/rules/conj.py').read(); assert s.count('anti_relapse.check(')==1, s.count('anti_relapse.check('); assert s.count('register_batch(')==1, s.count('register_batch('); assert s.index('anti_relapse.check(') < s.index('register_batch('); assert 'if not admitted:' in s"`

The whole batch commits through exactly one `harness.register_batch` call
— candidates are never registered one at a time.
`check: test "$(grep -c 'register_batch(' src/deepreason/rules/conj.py)" -eq 1`

Every candidate's interface is compiled from the problem's own criteria,
never invented independently of them.
`check: grep -q "for commitment_id in problem.criteria" src/deepreason/rules/conj.py && grep -q "compile_interface_draft(" src/deepreason/rules/conj.py`

**What it is handed:** the registered `problem` (and its `criteria`); the
manifest's `run_manifest` object itself (injected, optional — legacy v4/v5
callers pass `None`), read for `schema_version` and
`control_plane_policy.conjecture_context`, never mutated; school
conditioning as a paired `(endpoint_lease, execution_school_id)` when
school-routed (`DR-CON-schools`); a bounded, single-use scratch advisory
context it may both read and, uniquely among rules-side callers, write back
into (`DR-SEAM-rules-x-scratch`).
`check: grep -q "if (endpoint_lease is None) != (execution_school_id is None):" src/deepreason/rules/conj.py`

**Must never do:** write the log, compute a label, or decide a `Status` —
that is the harness's and adjudication's job; `rules/` only constructs the
records that make the harness do so (the package-wide guarantee
`DR-SUB-rules` already checks, which binds `conj.py` as a member of
`rules/`).
`check: ! grep -rqE "deepreason\.(harness|adjudication)|from deepreason import [^#]*\b(harness|adjudication)\b" --include=*.py src/deepreason/rules/`

Let a candidate bypass the anti-relapse gate to reach `register_batch`
(see the ordering check above — there is no second path into `batch`).

Hand-build a demonstrative fail warrant. `conj` proposes; it never
constructs the `(attackable ν, DEMONSTRATIVE w:<κ>:<target>, critic)`
triple — that constructor is `rules/warrants.py::register_fail_warrant`
alone, and `conj.py` does not call it.
`check: ! grep -q "register_fail_warrant" src/deepreason/rules/conj.py`

## Where it lives

| Aspect | File | Symbol |
|---|---|---|
| The entry point | `rules/conj.py` | `conj` |
| Provenance-root key for anti-relapse scoping | `rules/conj.py` | `root_problem_family` (delegates to the scheduler) |
| The mandatory pre-commit gate it consults | `rules/guards/anti_relapse.py` | `check` |
| Interface compilation from criteria | `workloads/models.py` | `MandatoryInterface`, `compile_interface_draft` |
| Scratch read/write (the only rules-side module that touches both) | `scratch/conjecture.py` | `plan_conjecture_context`, `commit_conjecture_context` |
| School-routed execution pairing | `llm/firewall.py` | `EndpointLease`, resolved before `conj` is called |
| Turn contract dispatch by schema_version | `llm/wire.py` | `ConjecturerTurnWireContractV4`/`V6` |

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| The conjecture turn contract version or its dispatch | the `active_v4`/`active_v5`/`active_v6` branch in `conj`, against `llm/wire.py` contracts | `tests/test_v6_conjecture_component_atomicity.py` |
| What a candidate's interface is compiled from | `MandatoryInterface`/`compile_interface_draft` call sites in `conj.py`, `workloads/models.py` | `tests/test_relapse_domains.py` |
| Whether/how conjecture reads or writes the scratchpad | `DR-SEAM-rules-x-scratch` — this is a seam change, not an isolated one; follow `docs/map/REC-change-a-seam.md` | `tests/test_conjecture_scratch_context_v4.py`, `tests/test_v6_conjecture_scratch_consumption.py` |

## What the conjecturer is now shown about criticism

`conj` renders the problem's OPEN CRITICISMS into the pack's binding block,
beside `criteria` (`DR-CON-discharge-channel`). The socket reaches the channel
through one public interface and hands `llm/packs.py` a plain string, so the
pack layer never learns that criticism is what it is rendering, and the channel
never learns what a pack is. This is the whole of the channel's contact with
`rules/`: exactly one file imports it.
`check: python -m pytest tests/test_discharge_contract.py::test_no_consumer_reaches_past_the_interface -q`
`check: grep -q "from deepreason.discharge import" src/deepreason/rules/conj.py && grep -q "open_criticism_context=open_criticism_context" src/deepreason/rules/conj.py`

## Traps

See `DR-SUB-rules`'s Traps for the package-wide hazards that also bind this
socket (the two supremacy guards, a provider call reaching the log exactly
once, successor-description nesting) — not re-derived here to avoid a
second, driftable copy. Socket-specific:

- **A refusal raised from inside a nested draft item kills the whole
  turn.** Already fixed and pinned by `DR-SEAM-rules-x-scratch`'s Traps
  (`run-bc3e8797`); recorded here because it is precisely the shape of
  "must never do" this socket's promise about partial completion protects
  against — a scratch-side validator that raises instead of discarding
  turns an advisory component into a candidate-killer.
`check: python -m pytest tests/test_scratch_contracts.py::test_a_self_link_is_dropped_rather_than_killing_the_whole_turn -q`
