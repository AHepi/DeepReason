<!-- DR-SEAM-harness-x-verification -->
Verified-at: 546544b5
Verify: python tools/docs_verify.py
Owns: src/deepreason/harness.py, src/deepreason/invariants.py, src/deepreason/log/event_log.py, src/deepreason/storage/blobs.py
Sides: DR-SUB-harness, DR-SUB-verification

# harness x verification

## The agreement

The harness promises that everything a run knows is reconstructible from
`log.jsonl` and the two content-addressed stores, and that the live session and
a later reopen reach that state through one function — `_apply_event` — so the
record is not a diary written alongside the state but the thing the state is
made of. Verification promises, in exchange, never to touch what it judges: it
opens the root read-only, repairs nothing, writes nothing, and converts every
kind of damage into a typed finding rather than into a fix. Neither side owns a
second implementation of the other's work. `verify_root` does not re-derive
epistemic state with independent code; it re-runs the harness twice, compares
the two materializations, and then checks that the graph the harness produced is
internally well-formed and that every durable projection beside the log agrees
with a fresh replay of the log. The verdict is a function of the root's bytes
and one integer (`meter_total`), which is why two verifications of one root at
two times are comparable at all. Both surfaces are frozen
(`DR-INV-frozen-surfaces`): the asymmetry that governs every change here is that
READERS may be fixed and FORMATS may not, because a committed root is evidence
and evidence whose meaning moves with the code is not evidence.

`verify_root` opens the root only read-only, and takes no configuration beyond
the meter total.
`check: python -c "import re,pathlib,inspect;from deepreason.invariants import verify_root;t=pathlib.Path('src/deepreason/invariants.py').read_text();c=re.findall(r'Harness\([^)]*\)',t);assert c and all('read_only=True' in x for x in c),c;assert list(inspect.signature(verify_root).parameters)==['root','meter_total']"`

The dependency arrow points one way only: the verifier imports the writer, and
importing the writer pulls in no verifier. The one place the arrow appears to
reverse — `Harness.__init__` calling `validate_terminal_commitment_storage`,
which lives in the module that later calls `verify_root` — is broken by
function-local imports on both hops.
`check: grep -q "^class Harness" src/deepreason/harness.py && grep -q "^def verify_root" src/deepreason/invariants.py && ! grep -qE "deepreason\.(invariants|verification)" src/deepreason/harness.py && python -c "import sys,deepreason.harness;assert not [m for m in ('deepreason.invariants','deepreason.verification.report') if m in sys.modules];import deepreason.invariants;assert 'deepreason.harness' in sys.modules"`

Every state family the harness rebuilds in `_reset` has its own determinism
finding name, and the correspondence is exact in both directions.
`check: python -c "import re,pathlib,inspect;from deepreason.harness import Harness;inv=pathlib.Path('src/deepreason/invariants.py').read_text();e=set(re.findall(r'fail\(.([a-z-]*replay).',inv));assert e=={'replay','scratch-replay','bridge-replay','workflow-replay','capability-replay'},e;s=set(re.findall(r'self\.(\w+_state) = ',inspect.getsource(Harness._reset)));assert s=={'scratch_state','bridge_state','workflow_state','capability_state'},s"`

The finding vocabulary is closed: of the 219 `fail(` sites in `invariants.py`,
exactly one passes a non-literal name, and that one forwards a name another
literal already minted. Only `detail` is free text.
`check: python -c "import re,pathlib;t=pathlib.Path('src/deepreason/invariants.py').read_text();c=[m for m in re.finditer(r'(?<!def )\bfail\(',t)];d=[m for m in c if not t[m.end():m.end()+40].lstrip().startswith(chr(34))];assert len(c)>150 and len(d)==1,(len(c),len(d))"`

`StateDiff` carries two different kinds of thing, and only one is replay input.
`hv_set`, `reach_set`, `addr+` and `carry+` are read back and applied;
`status_changed` is read back only by the incremental transition program;
`att+`, `dep+`, `A+` and `Π+` are written for the record and never read again,
because adjudication recomputes them.
`check: python -c "import re,pathlib;from deepreason.ontology.event import StateDiff;t=pathlib.Path('src/deepreason/harness.py').read_text();read=set(re.findall(r'event\.state_diff\.(\w+)',t));assert read=={'status_changed','hv_set','reach_set','addr_add','carry_add'},read;assert {'att_add','dep_add','a_add','pi_add'} <= set(StateDiff.model_fields)"`

## Where it is expressed

| Site | File | Symbol | What it enforces |
|---|---|---|---|
| One application path | `harness.py` | `_apply_event`, reached from `_commit` and from the `__init__` replay loop | live materialization and replay cannot diverge by construction |
| Adjudicate once | `harness.py` | `__init__`'s `_apply_event(event, adjudicate=False)` then `_adjudicate()` | the fixpoint is a pure function of the final graph; new state needing per-event recompute cannot ride on it |
| Rollback on failed append | `harness.py` | `_commit`'s `except` → `_reset()` → re-replay durable log | the in-memory view never outruns the log, which is what makes re-derivation admissible |
| Read-only opens | `invariants.py` | every `Harness(root, read_only=True)` in `verify_root`; `Harness.at` for the prefix probe | validation observes the evidence and never opens a writable view of it |
| Repair asymmetry | `log/event_log.py` | `EventLog.__init__`'s `if not read_only: self._repair_torn_tail()` | a torn final line is a repair on the writer's path and a finding on the verifier's |
| Holdout fence | `harness.py`, `storage/blobs.py` | `if self._read_only: self.blobs = FencedBlobStore(...)`, `historical_sealed_refs` | no read-only reader, verification included, sees holdout bytes no `Reveal` released |
| Replay determinism | `invariants.py` | two `Harness` opens → `replay`, `scratch-replay`, `bridge-replay`, `workflow-replay`, `capability-replay` | one log materializes to one state, five families deep |
| Incremental vs fresh | `invariants.py`, `harness.py` | `h.transitions() != Harness(root, read_only=True).transitions()` | the transition program is a function of the log, not of the instance; the only place a stored root gets per-event adjudication |
| Prefix openability | `invariants.py` | `Harness.at(root, seq)` at five quantile seqs | a truncated replay of a stored root still opens |
| Graph well-formedness | `invariants.py` | `warrant-validity`, `warrant-target`, `carry-carrier`, `carry-warrant`, `att-endpoints`, `dep-dag`, `addr`, `status-domain` | every reference the materialized state holds resolves inside that same state |
| Event stream shape | `log/event_log.py`, `invariants.py` | `validate_seq` → `EventSequenceError`; `seq-stream` | seqs consecutive from 0, enforced at the reader and re-asserted by the verifier |
| Sealed authority prefix | `harness.py` | `write_workflow_checkpoint`, `_verify_workflow_checkpoint` on every full open | a lost log tail is detected at open; verification inherits the raise |
| Terminal storage | `runtime/terminal_authority.py` | `validate_terminal_commitment_storage`, called from `Harness.__init__` | a latched commitment without its immutable stop object makes the root unopenable |
| Digests crossing out | `invariants.py` | `stats["workflow_process_digest"]`, `stats["capability_process_digest"]` from `h.workflow_state.digest` / `h.capability_state.digest` | the verdict carries the harness's own content addresses so a caller can bind them |
| The binding record | `runtime/terminal_authority.py` | `_fresh_replay_validation` — one read-only `Harness` plus one `verify_root` in a single `replay-validation.v1` payload | `REPLAY_VALIDATION.json` names both the re-derived digests and the verdict |
| Cycle break, both hops | `harness.py`, `runtime/terminal_authority.py` | function-local `from deepreason.runtime.terminal_authority import ...` and `from deepreason.invariants import verify_root` | importing the writer never imports the verifier |
| Legacy reader tolerance | `ontology/event.py`, `invariants.py` | `LLMCall.attempt_trace` default; the `elif manifest is not None:` gate; `_legacy_bridge_failure_call_seqs` | pre-manifest roots stay readable while manifest-bound roots must substantiate every call |

The binding record and the digests it quotes come from the harness's own replay
states, not from a recomputation.
`check: grep -q '"workflow_process_digest": h.workflow_state.digest' src/deepreason/invariants.py && grep -q '"capability_process_digest": h.capability_state.digest' src/deepreason/invariants.py && grep -q "replayed = Harness(root, read_only=True)" src/deepreason/runtime/terminal_authority.py && grep -q "replayed.workflow_state.digest" src/deepreason/runtime/terminal_authority.py && grep -q "not verification\[.violations.\]" src/deepreason/runtime/terminal_authority.py`

The transition cross-check and the sampled prefix probe are both present, and the
prefix sample is five quantiles rather than every seq.
`check: grep -q "h.transitions() != Harness(root, read_only=True).transitions()" src/deepreason/invariants.py && grep -q "seqs\[i \* (len(seqs) - 1) // 4\]" src/deepreason/invariants.py`

Reader tolerance is a defaulted field plus a gate, not a special case:
`attempt_trace` defaults empty so an old event still validates, and the demand
for a trace fires only when the root is manifest-bound.
`check: python -c "from deepreason.ontology.event import LLMCall;assert not LLMCall.model_fields['attempt_trace'].is_required()" && grep -q "manifest-bound LLM call has no attempt trace" src/deepreason/invariants.py && grep -q "def _legacy_bridge_failure_call_seqs" src/deepreason/invariants.py`

## What is deliberately absent

**The write path never consults the verifier.** No import, deferred or
otherwise, reaches `invariants` or `verification` from `harness.py`, and no
registration is refused because the resulting root would fail validation. This
is not an oversight to be closed by "validating before committing": if the
writer consulted the verifier, a verifier bug would suppress evidence instead of
reporting it, and the log would stop being the only admissible record of what a
run did. Validation is strictly post hoc, and it is allowed to say that a
committed root is broken. Checked above, in both directions — static text and
runtime `sys.modules`.

**Verification does not re-derive labels.** `invariants.py` contains no
`label0`, no `final_labels` and no adjudication call. It checks that the
dependence relation is acyclic and that every status is a member of the `Status`
enum — nothing about which label is *right*. The comment above `status-domain`
records why: `SUSPENDED` / `SUSPENDED_UNSUPPORTED` are legal spec §4
support-cascade labels first produced live on `runs/ab_needham`, and a verifier
that recomputed "expected" labels would have refused them. A clean `verify_root`
does not mean the labels are correct; it means nothing in the graph dangles.
`check: grep -q "final_labels(compute_label0(nodes, att), dep)" src/deepreason/harness.py && grep -q "def _adjudicate" src/deepreason/harness.py && grep -q "toposort(set(h.state.artifacts), build_dep(h.state.artifacts))" src/deepreason/invariants.py && grep -q "Any Status enum member is legal" src/deepreason/invariants.py && ! grep -qE "compute_label0|final_labels|label0|adjudicate\(" src/deepreason/invariants.py`

**Verification never repairs, and the writer always does.** The same torn final
line is truncated by a writable open and left byte-identical by `verify_root`
and by any read-only open. The gate is one `if not read_only:` in
`EventLog.__init__`. Making repair unconditional would make the verifier destroy
the damage it exists to report.
`check: python -W ignore -c "import tempfile,pathlib;from deepreason.harness import Harness;from deepreason.invariants import verify_root;d=pathlib.Path(tempfile.mkdtemp())/'run';h=Harness(d);h.record_measure(inputs=['x']);p=h.log.path;open(p,'a').write('torn');b=p.read_bytes();verify_root(d);Harness(d,read_only=True);assert p.read_bytes()==b,'read-only open rewrote the log';Harness(d);assert p.read_bytes()!=b,'writable open did not repair the torn tail'"`

**Verification cannot read a sealed holdout.** The fence is applied on ANY
read-only open, not only on a truncated `Harness.at` view, so `verify_root`'s
own harness sees `KeyError` for holdout bytes no `Reveal` event released. A
verifier that could read them could leak the answer into a finding's `detail`.
`check: python -c "import tempfile,pathlib;from deepreason.harness import Harness;from deepreason.storage.blobs import FencedBlobStore;d=pathlib.Path(tempfile.mkdtemp())/'run';Harness(d);assert isinstance(Harness(d,read_only=True).blobs,FencedBlobStore);assert not isinstance(Harness(d).blobs,FencedBlobStore)"`

**Nothing outside the root enters the verdict.** `invariants.py` imports no
`os`, no clock, no randomness and no uuid; its only non-root input is
`meter_total`, the caller's live meter, and the one finding that consumes it
(`accounting`) says so in its detail. There is no strictness flag, no
allow-list, and no way to skip a check — because a verdict that depends on
options is not comparable across roots or across time, which is the property
`REPLAY_VALIDATION.json` is stored to assert.
`check: python -c "import pathlib;t=pathlib.Path('src/deepreason/invariants.py').read_text();bad=[m for m in ('import os','os.environ','getenv','import random','datetime','time.time','uuid') if m in t];assert not bad,bad;assert 'def verify_root(' in t"`

**Not every prefix is verified.** `Harness.at` is probed at five quantile seqs,
not at every seq. Bounded on purpose — the cost is linear in events per probe —
so "verify_root passed" is not evidence that an arbitrary historical view opens.
If you need that, sweep it yourself; see the grep above for the sampling
expression.

**`verify_root` writes no file at all**, including `REPLAY_VALIDATION.json`.
That record is assembled by callers out of the return value; see
`DR-SUB-verification` for who writes it and what else it binds.

## How to change it

1. **Read `DR-INV-frozen-surfaces` first.** Both sides are frozen surfaces. The
   question is never "is this better" but "does any recorded root's `valid` or
   `att` move". The 42-root sweep documented there is the instrument; run it
   before and after and compare byte-identically.
2. **Reader before writer, always.** A new field on a durable record gets a
   default and a reader that decides what its ABSENCE means for a root written
   before the field existed. Only then may the writer emit it. `attempt_trace`
   is the worked example: defaulted so old events validate, demanded only when
   `manifest is not None`.
3. **A new typed event channel moves in one order**: `Rule` and the payload
   field in `ontology/event.py` → the `_apply_event` branch → a `_reset`
   attribute if it materializes state → the `record_*` seam → a determinism
   finding in `verify_root` → a channel entry in `report.py`. Stopping before
   the last step defaults the new finding to `integrity`, and `integrity` is
   what decides `valid` — so every recorded root that trips it flips. See
   `DR-SUB-verification`'s first trap.
4. **Anything added to `_reset` must be reconstructible from the log alone.**
   `_commit`'s failure path resets and re-replays; state that cannot be rebuilt
   that way survives a failed append in memory but not on disk, and the next
   `verify_root` reports it as a `replay` divergence rather than as the write
   bug it is.
5. **Never route the writer through the verifier** to "fail fast". See the
   absences above; this is a design decision, not an unimplemented feature.
6. **If a change makes an existing root unopenable, it is wrong by definition.**
   The symptom is not a helpful error: the root collapses to a single `open`
   finding with empty `stats`, which erases every other finding it would have
   produced.

What breaks first, in the order you will meet it:
`test_replay_reproduces_state_byte_for_byte` (the only test that compares replay
against the state a LIVE session actually held); then the persistence
invariants — read-only enforcement, torn-tail repair, failed-append rollback,
seq fencing; then `verify_root` over generated messy runs; then the root sweep,
which is the expensive one, because by then you need to know whether a committed
root moved.

`check: python -m pytest tests/test_replay.py tests/test_persistence_invariants.py -q`
`check: python -m pytest tests/test_chaos_invariants.py "tests/test_process_metadata.py::test_invariants_detect_manifest_hash_corruption" -q`

Also worth running when you touch the correlation passes rather than the replay
itself: `tests/test_v6_controller3_replay_verification.py`, which pins the
fail-closed behaviour of the pre-replay controller-v3 correlation.

## Traps

- **Opening a suspect root writable destroys the evidence.** `Harness(root)` is
  the default spelling and it truncates a torn final line in place. A diagnostic
  script that opens the root "just to look" before running `verify_root` has
  already changed the bytes the verifier was going to judge, and the resulting
  clean verdict is worthless. Always `read_only=True`; the check under
  *deliberately absent* demonstrates both halves of the asymmetry.
- **A harness-side raise at open erases every other finding.** A corrupt
  `workflow-checkpoint.json`, a failed `validate_terminal_commitment_storage`,
  and a mid-log seq gap all surface identically: one `open` finding, `"stats":
  {}`. `_controller_v3_history` runs BEFORE replay precisely so its typed
  findings survive that collapse — nothing else does. A caller that indexes into
  `stats` unconditionally crashes on exactly the roots most worth inspecting.
`check: python -c "import tempfile,pathlib,json;from deepreason.harness import Harness;from deepreason.invariants import verify_root;d=pathlib.Path(tempfile.mkdtemp())/'run';h=Harness(d);h.record_measure(inputs=['x']);g=verify_root(d);assert set(g)=={'violations','stats'} and g['stats']['events']==1,g;(d/'workflow-checkpoint.json').write_text(json.dumps({'schema':'workflow.checkpoint.v0'}));b=verify_root(d);assert b['stats']=={} and [v['check'] for v in b['violations']]==['open'],b" && grep -q "controller_v3_findings, controller_v3 = _controller_v3_history(Path(root))" src/deepreason/invariants.py`
- **Two replays of the same code are not a correctness check.** The `replay`
  finding compares two `Harness` opens of one log; both run the same
  `_apply_event`. It catches NONDETERMINISM — an iteration order that leaked
  into serialization, a set where a list was needed — and nothing else. The only
  evidence that replay reproduces what the live session held is
  `tests/test_replay.py`, which captures the live state before reopening and
  compares against it. Deleting that test removes the property; deleting the
  `replay` finding does not.
- **Tampering with a derived `state_diff` field proves nothing.** `att+`, `dep+`,
  `A+` and `Π+` are written for the record and never read back, so editing them
  in a stored log changes no reopened state; `carry+`, `addr+`, `hv_set` and
  `reach_set` ARE replay inputs and editing them does. A tamper-detection
  experiment that mutates only the first group will report, correctly and
  uselessly, that nothing happened. The read-back set is pinned by the check
  under *The agreement*.
- **Pre-v6 roots are expected to refuse.** 11 of the 42 recorded roots raise
  `UnsupportedRunManifestVersionError` on open. That is the sweep's baseline, not
  a regression to be fixed by widening the manifest loader —
  see `DR-INV-frozen-surfaces`, surface 4.
- **`seq-stream` is defence in depth, not the enforcement.** The reader raises
  `EventSequenceError` on any gap, so a gapped log never reaches the graph
  checks; it becomes an `open` finding instead. Reading the `seq-stream` name in
  a report and concluding the log was parsed successfully is backwards.
