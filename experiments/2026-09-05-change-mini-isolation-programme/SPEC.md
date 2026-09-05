# Spec for: the mini isolation programme
Tranche: `experiments/2026-09-05-change-mini-isolation-programme/`
Phase: `dr-spec-change`. Shape: **DESIGN-AND-STOP** — the deliverable of
this window is this document plus CHECKLIST.md, and no production code.

Authority: REQUEST.md (R1-R12, R-again/R-stored/R-history, C1-C10).
Every item cites its R/C numbers. Untraceable items are bugs.
Measurements: FEASIBILITY.md and `proof/`. Nothing load-bearing below is
asserted where a command could have decided it.

---

## 0. The eight design questions, answered

Each answer is an item or a group of items below. This table is the index;
the items carry the acceptance checks.

| | question | answer | items |
|---|---|---|---|
| D1 | isolation | mini keeps its own root and its own record, takes the STANDARD frozen input, and a module fence test proves eleven named packages are never imported during a mini isolation run | S1 |
| D2 | relaxed forms | **Road M**, a mini-only form registry outside the V6 Literals — measured `CLEAR`; the stored default form is registered beside it, never replaced | S2 |
| D3 | cycles without commitments | a registered `MiniCommitmentPolicyV1`; switching either commitment channel off emits a typed WARNING into the record, never a refusal | S3 |
| D4 | the commitment artifact | a new artifact kind `mini.commitment-proposal.v1` whose ONLY requirement is that it names the conjecture it is about | S4 |
| D5 | who sees what | two layouts and one structural omission: the critic layout registers no commitment section at all | S5, S6 |
| D6 | one interface, three seats | all three seats resolve a `SeatShellV1` and render through one public `render_seat_brief`; `SeatShellV1.form_id` gains its first consumer; the controller hook is DECLARED with a no-op default and called by nothing | S5, S6, S7 |
| D7 | pluggable flow | a registered, versioned `MiniFlowV1` — stage order and the SET of artifact kinds are data; an architecture test goes red when the loop names a seat | S8, S9 |
| D8 | the measure | a pre-registered blind comparison against the same model's single call on the same standard input, length held constant, per-seat spend reported | S12 |

---

## Items

### S0 — the two prerequisites (F1, F2)

Without both, D5-D7 are a code edit rather than configuration, and C8's
enforcement clause ("a check that can fail when a customization point
requires a code edit to use") cannot be satisfied. Measured dead, both:
`proof/m3_seat_shell_reach.txt` line `ARM B layouts after: False`, and
`blast_mini_declared.json`'s own `disclosure_summary` — "1 declared
symbol(s) already have no live call path today: `load_operator_plugins`".

**S0a (R7, C8; F1)** — `src/deepreason/llm/seat_sections.py`,
`src/deepreason/shallow.py` | before: `load_operator_plugins` has no call
site under `src/`, so a file an operator places in
`<DEEPREASON_HOME>/seat_plugins/` is never read by a run | after: the
managed shallow path calls it once during setup, and BOTH of its notice
lists reach the run's record. Disclose, never die (C10): a plugin that
failed to load produces a typed notice, never a silently missing section.

    accept: python -c "
    import subprocess
    out = subprocess.run(['grep','-rn','load_operator_plugins','src/'],
                         capture_output=True, text=True).stdout
    assert len([l for l in out.splitlines() if l.strip()]) >= 2, out
    " ; python -m pytest tests/test_seat_section_home.py -q   -> 0 failed

**S0b (R7, R9, R10, C8; F2)** — `src/deepreason/llm/seat_sections.py` |
before: `register_seat_pack_layout` is reachable only from Python, so
`DR-REC-add-a-section-plugin` step 3 has no non-code road | after: a layout
declared in a `.layout.json` file under `<DEEPREASON_HOME>/seat_plugins/` is
registered by id, and a file that does not parse produces a typed refusal
(never a silent fallback).

    accept: python -m pytest tests/test_seat_section_home.py::test_a_file_declared_layout_is_registered tests/test_seat_section_home.py::test_an_unparseable_layout_file_is_refused_typed -q
      -> 2 passed

---

### S1 (R1, R11, R12) — isolation, and what "the larger harness" means

`src/deepreason/shallow.py`, `src/deepreason/cli/main.py`,
`mini/minireason/compat.py`.

**Before.** `deepreason reason --shallow "Q"` takes one bare question
string; `compat.mini_run_input()` binds a CONSTANT process root
(`minireason:process-root`) with "no frozen input criteria and an empty
evidence dossier" (`compat.py:80-90`).

**After.** `deepreason reason --shallow --run-input <root>` accepts the
STANDARD frozen input — the `RunInputManifestV2` that `deepreason input
freeze` already writes, problem plus criteria (R12). The bare-question form
keeps working unchanged. Mini binds the supplied run input instead of the
constant process root when one is given.

**"The larger harness", named by module.** A mini isolation run must not
import, at run time, any of:

    deepreason.scheduler          deepreason.qualification
    deepreason.capabilities       deepreason.amendment
    deepreason.bridge             deepreason.evaluation
    deepreason.adjudication       deepreason.application.text_runs
    deepreason.calculus           deepreason.workflow.transaction_service
    deepreason.schools

It MAY use, because they are the record itself rather than the harness
around it: `deepreason.harness`, `deepreason.ontology`,
`deepreason.log.event_log`, `deepreason.invariants` (read-only),
`deepreason.programs`, `deepreason.informal.skeleton`, `deepreason.llm.*`,
`deepreason.rules.guards`, `deepreason.rules.warrants`,
`deepreason.run_manifest` (mini binds its own minimal v6 manifest today and
keeps doing so).

The fence is a TEST, not a convention — that is C8's "enforced" clause.

**AMENDED 2026-09-05, before step 10 ran, on a measurement this item's own
wording could not survive.** The sentence above — "must not import, at run
time, any of" the eleven — is FALSE of four of them and cannot be made true
within this programme, because the modules S1 explicitly ALLOWS import them
themselves. Measured, in a fresh interpreter each arm
(`proof/fence_arms.txt`, `proof/fence_measure.py`):

    ARM A  importing ONLY the allowed record modules already pulls in:
             deepreason.adjudication          <- deepreason.harness imports
                                                 adjudication.edges
             deepreason.bridge                <- deepreason.ontology.event
                                                 imports bridge.events
             deepreason.capabilities          <- deepreason.ontology.event
                                                 imports capabilities.events
             deepreason.workflow.transaction_service
    ARM B  importing minireason.loop pulls in those four PLUS
             deepreason.application.text_runs
    ARM C  what MINI adds beyond ARM A:  ['deepreason.application.text_runs']

So "never imported" would be a fence nobody could pass without changing the
event ontology and the harness — two frozen surfaces, and both of them the
RECORD rather than the harness around it, which is exactly why S1 allowed
them in the first place. The eleven-module list is not wrong about what mini
must not USE; it is wrong about what "import" can prove.

**The fence, restated so it says something true and still bites.** Three
parts, each its own test:

1. **No direct dependency.** No module under `mini/minireason/` imports a
   fenced module directly (AST over mini's own sources, relative imports
   resolved). Measured today: ONE violation,
   `mini/minireason/compat.py:38`, `from deepreason.bridge.retry import
   WorkflowRetryPolicyV1`. Mini takes the manifest's own schema types from
   `deepreason.run_manifest`, which S1 allows, so its dependency is on the
   record's schema rather than on the subsystem that happens to define it.
2. **No closure growth.** Importing mini adds NO fenced package beyond the
   closure the allowed record modules already bring (ARM C is empty).
   Measured today: ONE violation, `deepreason.application.text_runs`,
   which arrives because `deepreason/application/__init__.py` eagerly
   re-exports the text-run service and mini imports
   `deepreason.application.conjecture` from that package. Fixed by making
   those three names lazy — the public surface is unchanged
   (`from deepreason.application import TextRunApplicationService` still
   works) and importing the boundary package no longer starts the run
   engine.
3. **Nothing new during the run.** A mini isolation run imports no fenced
   module that was not already loaded when it started. This is what catches
   a lazy `import deepreason.scheduler` inside a function, which parts 1
   and 2 would both miss.

What the fence therefore DOES prove: mini reaches for nothing in the larger
harness, and adds nothing to what the record modules already carry. What it
does NOT prove, stated so it is never over-read: that no code inside those
four packages is ever executed. Their event-payload types are constructed by
the record itself. Proving non-EXECUTION is a different instrument and is
not built here.

    accept: python -m pytest mini/tests/test_isolation_fence.py -q -> passed,
      and each of the three parts fails under a mutation proven in the same
      commit (proof/fence_mutation.txt)
    accept: python -m pytest tests/test_shallow_reason.py -q -> 0 failed
    accept: python proof/fence_measure.py -> ARM C empty

**Record.** Mini's record stays mini's own: typed, append-only, and
replayable by the code that wrote it (CLAUDE.md's within-version scope
boundary). Measured to survive this programme's other changes at S10.

---

### S2 (R2, R7, R-stored, C1, C9) — the mini form registry

`mini/minireason/forms.py` (new), `mini/minireason/compat.py`.

**Road chosen: M.** See §Options. `mini/minireason/forms.py` registers
`MiniFormV1(form_id, form_version, wire_model, canonical_model, compile)`
keyed by `form_id`. Selection: explicit argument → `DEEPREASON_MINI_FORM` →
the flow's declared default. **Never `Config`, never the manifest** — the
same rule `DR-INV-seat-section-plugins` states, for the same measured
reason: `run_manifest.py` dumps every `Config` field into
`engine_config_json` and `qualification.py` folds that into every
qualification subject digest.

Four forms ship:

| form_id | what it is |
|---|---|
| `mini.conjecturer.legacy-v0` | the STORED default: today's `ReferenceFreeConjecturerWireContract`, wrapped, unchanged, byte-for-byte (R-stored) |
| `mini.conjecturer.relaxed.v1` | `{candidates: [{content: str, typicality: float = 0.5}]}` — `min_length=1`, and **no `max_length` on any string field anywhere in the model** |
| `mini.critic.relaxed.v1` | `{objections: [{about: str, body: str}]}` — `about` names the conjecture; `body` is free prose, unbounded |
| `mini.commitment.relaxed.v1` | `{proposals: [{about: str, body: str}]}` — see S4 |

**"Not limit prose length at all" (R2) is three separate limits, and all
three go.** (a) No `max_length` on any field of any mini form. (b) No
required skeleton: the relaxed forms demand no `claim`/`mechanism`/
`forbidden` structure, so a candidate that is one paragraph of prose is a
well-formed candidate. (c) No truncation of what a seat is SHOWN: the mini
section plugins at S5 render every artifact in full, replacing
`loop.py:340-349`'s `[-k:]` window and `content[:300]` cut. (a) and (b) are
the FORM; (c) is R6, and R2 would be hollow without it — a form that accepts
unlimited prose feeding a brief that shows 300 characters of it is not an
unlimited channel.

    accept: python -c "
    from minireason.forms import resolve_mini_form, mini_form_ids
    import json
    assert 'mini.conjecturer.legacy-v0' in mini_form_ids()
    for fid in mini_form_ids():
        schema = json.dumps(resolve_mini_form(fid).wire_model.model_json_schema())
        assert 'maxLength' not in schema, (fid, 'a mini form bounds a string')
    "
    accept: python -m pytest mini/tests/test_mini_forms.py -q -> 0 failed
    accept: the stored form's rendered wire schema is byte-identical to
      today's — pinned by a golden committed in the same step (R-stored)

---

### S3 (R3, C10) — cycles with commitments disabled

`mini/minireason/checks.py`, `mini/minireason/loop.py`.

**Before.** `compile_checks` unconditionally prepends the mandatory
`skeleton-wf` commitment. Measured consequence for a relaxed form
(`proof/m2_free_prose_today.txt`): six candidates admitted, six refuted on
arrival, **zero survivors**, problem dry in three cycles. So R2 without R3
produces a run that cannot survive anything — they are one change.

**After.** A registered `MiniCommitmentPolicyV1` with two switches:

    mandatory_skeleton_wf: bool = True     # the well-formedness commitment
    model_authored_forbidden: bool = True  # the candidate's own forbidden[]

`compile_checks` consults the policy. The isolation flow (S8) declares both
`False`. Switching either off emits a typed WARNING record into the run —
never a refusal and never silence (C10, the operator's 2026-08-28 words:
"Gates are always optional: with warnings"). The warning text names what is
no longer being checked.

    accept: python -c "
    from minireason.checks import compile_checks
    from minireason.policy import MiniCommitmentPolicyV1
    off = MiniCommitmentPolicyV1(mandatory_skeleton_wf=False, model_authored_forbidden=False)
    assert compile_checks('free prose, no skeleton', policy=off) == []
    assert compile_checks('free prose, no skeleton') != []   # default unchanged
    "
    accept: a mini run under the isolation flow with a free-prose candidate
      records >=1 surviving conjecture AND a typed commitments-disabled
      warning -- pytest mini/tests/test_mini_commitment_policy.py -q

---

### S4 (R4, C9) — the commitment artifact

`mini/minireason/seats.py` (new), `mini/minireason/forms.py`.

A NEW artifact kind, `mini.commitment-proposal.v1`, produced by its own seat
(`mini.commitment`), which reads a conjecture and proposes commitments in
free prose.

**Its minimum, stated exactly as the window asked.** A commitment proposal
must name the conjecture it is about (`about: <artifact id present in this
run>`) **and nothing more is required**. The body is free prose with no
required fields, no schema beyond "non-empty string", and no length bound.
There is no penalty of any kind for its shape: it is not ranked, not
admitted differently, not immunised and not refuted on account of being
informal (C9, the formalism-optional law; `DR-CON-conjecture-kinds`' R-g
guardrail applied to a third artifact kind).

**What it does NOT do here.** A proposal is RECORDED, not registered as a
canonical `Commitment`. Turning a free-prose proposal into an evaluable
commitment that can refute is a separate road, and it is the subject of the
one question at §Questions.

    accept: python -c "
    from minireason.forms import resolve_mini_form
    m = resolve_mini_form('mini.commitment.relaxed.v1').wire_model
    m.model_validate({'proposals': [{'about': 'a1', 'body': 'x'}]})   # minimum
    import pydantic
    try: m.model_validate({'proposals': [{'body': 'x'}]}); raise SystemExit('about not required')
    except pydantic.ValidationError: pass
    "
    accept: python -m pytest mini/tests/test_mini_commitment_seat.py -q -> 0 failed
    accept: an architecture test proves no rank, admission, immunity or
      refutation path reads the string 'commitment-proposal' --
      pytest mini/tests/test_mini_shape_buys_nothing.py -q

---

### S5 (R5, R6) — the mini source, and who sees what

`mini/minireason/sources.py` (new), `src/deepreason/llm/seat_plugins.py`.

**The adapter.** Measured at `proof/m3_seat_shell_reach.txt`: the shipped
walk runs from a live mini session and renders `dr.problem` once its dict is
adapted (`RENDERED ... [('problem','rendered',30)]`), and fails on
`dr.neighbourhood` with `'dict' object has no attribute 'content_ref'`. So
one read-only projection from mini's `State` dict view to the ontology types
the plugins already expect is the whole gap. It writes nothing and changes
no digest — the `DR-INV-seat-section-sources` pattern applied to a second
engine.

**Three mini section plugins**, registered like any other:

| plugin | renders | declared by |
|---|---|---|
| `mini.everything-so-far` | EVERY artifact generated in this run so far, in full, untruncated (R6) | conjecturer and commitment layouts |
| `mini.target-conjecture` | the one conjecture under criticism, in full (R5) | critic layout |
| `mini.problem` | the standard input's problem and criteria (R12) | all three |

**The blinding is STRUCTURAL, not a filter.** The critic layout REGISTERS NO
commitment section at all — a present-but-empty slot is not the design.
That is the shape the record already requires of provenance blinding
(CLAUDE.md, the amended judge law, 2026-08-28: "renderers OMIT provenance
fields entirely (a present-but-blank slot draws more attention than a filled
one)"), applied to R5.

    accept: python -m pytest mini/tests/test_mini_exposure.py -q -> 0 failed
    accept: python -c "
    from minireason.flow import resolve_mini_flow
    from deepreason.llm.seat_sections import resolve_seat_pack_layout, resolve_seat_shell
    flow = resolve_mini_flow('mini.flow.isolation.v1')
    critic = resolve_seat_pack_layout('mini.critic', resolve_seat_shell('mini.critic').layout_id)
    ids = {e.plugin_id for e in critic.entries}
    assert not any('commitment' in i for i in ids), ids
    "
    accept: a rendered critic brief over a run containing commitment
      proposals contains NONE of their bodies -- a byte assertion, not a
      count (pytest mini/tests/test_mini_exposure.py::test_critic_brief_carries_no_proposal_bytes)

---

### S6 (R7, C7, C8) — one interface, three seats

`src/deepreason/llm/packs.py`, `src/deepreason/llm/seat_layouts.py`,
`mini/minireason/seats.py`.

**A public entry.** `_walk_seat_layout` is private; mini reaching into it
would be the bypass C8's architecture test is supposed to catch. Add
`render_seat_brief(seat_id, layout_id, request, receipts=None)` as the
declared public interface, with `_walk_seat_layout` as its body. No
behaviour change for the two existing seats.

**Three mini shells registered**, one per seat:

    seat.mini.conjecturer.v0  seat_id=mini.conjecturer  layout=seat-pack.mini.conjecturer.v0  form=mini.conjecturer.relaxed.v1
    seat.mini.critic.v0       seat_id=mini.critic       layout=seat-pack.mini.critic.v0       form=mini.critic.relaxed.v1
    seat.mini.commitment.v0   seat_id=mini.commitment   layout=seat-pack.mini.commitment.v0   form=mini.commitment.relaxed.v1

**`SeatShellV1.form_id` gains its first consumer.** Measured today: `grep
-rn "form_id" src/` returns three lines — the field and the two shipped
shells. Nothing reads it. Mini's dispatch resolves its form THROUGH the
shell, which is what makes all three seats one interface rather than three
similar code paths, and is the output half of C7 ("a seat kind is a
registered pairing of a brief layout and a form"). The full harness's two
shells are untouched: their `form_id` values stay exactly as registered and
no full-harness dispatch site starts reading them in this programme.

    accept: python -m pytest tests/test_conj_pack_legacy_golden.py tests/test_crit_pack_legacy_golden.py -q -> 0 failed (C4)
    accept: python -c "
    from minireason.seats import form_for_seat
    from deepreason.llm.seat_sections import resolve_seat_shell
    for seat in ('mini.conjecturer','mini.critic','mini.commitment'):
        assert form_for_seat(seat).form_id == resolve_seat_shell(seat).form_id
    "
    accept: python -m pytest mini/tests/test_mini_seat_shell.py -q -> 0 failed

---

### S7 (R7, R8, C2) — the controller hook: declared, never implemented

`mini/minireason/seats.py`.

R7 asks that what each seat is shown be "calibrated on the fly and
modifiable by the controller". R8 and C2 say do not change the controller
yet. So this item ships the INTERFACE and nothing behind it:

    class MiniCalibrationHookV1(Protocol):
        hook_id: str
        hook_version: str
        def calibrate(self, *, seat_id: str, cycle: int,
                      entries: tuple[SeatPackLayoutEntryV1, ...]
                      ) -> tuple[SeatPackLayoutEntryV1, ...] | None: ...

Registered like every other artifact here, versioned, selected by id. ONE
implementation ships: `mini.calibration.noop.v1`, which returns `None`. It
is the default and the only registered hook. The mini loop calls it between
cycles, so the seam exists and is exercised; what it does is nothing.

**The guard is a test, because a promise is not a mechanism.** An
architecture test asserts (a) the default resolves to the no-op, (b) nothing
under `src/` or `mini/minireason/` registers a second hook, and (c) the
no-op's return is `None` for every input.

    accept: python -m pytest mini/tests/test_mini_calibration_hook.py -q -> 0 failed
    accept: grep -rn "register_mini_calibration_hook" src/ mini/minireason/ | wc -l -> 2
      (the definition and the one no-op registration; a third line is a
       violation of R8 and the test says so by name)

---

### S8 (R9, R10, C1, C8) — the pluggable flow

`mini/minireason/flow.py` (new), `mini/minireason/loop.py`.

    MiniFlowV1(flow_id, flow_version,
               stages: tuple[MiniStageV1, ...],
               artifact_kinds: tuple[str, ...],
               commitment_policy: MiniCommitmentPolicyV1,
               calibration_hook_id: str = "mini.calibration.noop.v1")

    MiniStageV1(stage_id, seat_id, shell_id, produces_kind,
                reads_kinds: tuple[str, ...])

`loop.run` walks `flow.stages` in order. It names no seat, no artifact kind
and no stage. **Adding a new artifact kind and its seat is a registration:**
register a form, a layout, a shell, and a stage that names them — no source
edit (R10, C8).

Two flows ship, both switchable, neither permanent (C1):

| flow_id | stages | commitments |
|---|---|---|
| `mini.flow.legacy-v0` | conjecturer only | both ON — reproduces today's loop exactly |
| `mini.flow.isolation.v1` | conjecturer → critic → commitment | both OFF, with the typed warning |

Selection: argument → `DEEPREASON_MINI_FLOW` → `mini.flow.legacy-v0`. **The
default is today's behaviour**, so nothing changes for anyone who does not
select the new flow (C1, C4).

    accept: python -m pytest mini/tests/test_mini_flow.py -q -> 0 failed
    accept: python -c "
    import ast, pathlib
    src = pathlib.Path('mini/minireason/loop.py').read_text()
    for name in ('mini.conjecturer','mini.critic','mini.commitment',
                 'commitment-proposal','skeleton'):
        assert name not in src, name
    "
    accept: a flow registered ONLY in a test file (never in mini/minireason/)
      adds a fourth stage with a fourth artifact kind and runs end to end --
      pytest mini/tests/test_mini_flow.py::test_a_new_artifact_kind_is_a_registration -q

---

### S9 (C8) — the architecture tests that go red on a bypass

`mini/tests/test_mini_architecture.py`.

C8's "enforced" clause is a check that can FAIL. Five, each with a mutation
proof committed beside it (a mutation that makes it red, run and pasted):

1. the loop names no seat, kind or stage (S8's accept, as a test)
2. no evidence-side path reads a mini seat name or artifact kind (C7's scope
   boundary; the R-g guardrail)
3. a section added to a mini brief needs no source edit under
   `mini/minireason/`
4. a new artifact kind needs no source edit under `mini/minireason/`
5. only the no-op calibration hook is registered (R8)

    accept: python -m pytest mini/tests/test_mini_architecture.py -q -> 0 failed
    accept: each of the five has a `proof/mutation_<n>.txt` showing it RED on
      a deliberately broken tree

---

### S10 (C4, all) — regression, goldens, and the record

1. `python -m pytest tests/ -q -n 4` -> 0 failed (the documented gate).
2. `python -m pytest mini/tests/ -q` -> 0 failed. **This is not the same
   command**: `pyproject.toml:58` declares `testpaths = ["tests",
   "mini/tests"]`, but the documented gate passes `tests/` explicitly, which
   overrides it. Measured: `python -m pytest mini/tests --collect-only` ->
   **95 tests collected**; `python -m pytest tests/ --collect-only` -> 5 078.
   So mini's own 95 tests are outside the gate every tranche runs. Recorded
   as a finding in PARKED.md; run explicitly here regardless.
3. `python -m pytest tests/test_conj_pack_legacy_golden.py
   tests/test_crit_pack_legacy_golden.py -q` -> 0 failed. The full harness's
   two briefs stay byte-identical (C4).
4. `python tools/docs_verify.py` -> 0 failed, and `--audit` -> 0 findings.
5. `verify_root` over a mini isolation run -> 0 violations, and
   `replay(root).digest() == Session(root).state.digest()`.

    accept: every one of the five, pasted into CHECKLIST.md

---

### S11 (map, C8) — the map moves in the same commit

**S11a — `docs/map/SUB-minireason.md` (new).** Measured gap: no map document
names `mini/minireason/`. It owns the eleven modules, the reduced loop, the
form registry, the flow registry and the seat set, with `check:` lines that
re-derive rather than assert.

**S11b — the seam and the invariants.** `docs/map/SEAM-llm-x-minireason.md`
(new; mini consumes the seat-shell, the wire contracts and the route lease,
and that agreement is exactly what this programme changes), plus:
`INV-seat-section-plugins.md` gains the `form_id`-has-a-consumer row and the
`render_seat_brief` entry point; `REC-add-a-section-plugin.md`'s steps 2-4
become true once S0a/S0b land; `INDEX.md`'s seam matrix and coverage section
gain the new rows.

Both move in the SAME commit as the code they describe. `Verified-at:`
advances only where the checks were actually re-run.

    accept: python tools/docs_verify.py -> 0 failed
    accept: python tools/docs_verify.py --audit -> 0 findings
    accept: python tools/docs_verify.py --links -> every DR- reference resolves

---

### S12 (D8, C6) — the measure

`experiments/2026-09-05-change-mini-isolation-programme/PREREG_D8.md`.

C6 is the acceptance criterion for the whole programme: success is output
**materially better than what the same model produces WITHOUT the harness on
the same question**, never correctness and never "it reached a terminal".

**Design.** Two arms on the same standard input, same model, matched spend.
ARM 0: one call, no harness. ARM M: `mini.flow.isolation.v1`. Criteria
written and committed BEFORE any output is read. Judging blind, through the
committed panel. **Length held constant**, because the record measures the
panel scoring it: Spearman ρ = +0.797 between candidate characters and
judged total, R² = 0.589 (`experiments/2026-09-03-change-provenance-history-
channel/RESULTS_M1_QUALITY.md` §3.4) — a relaxed, unbounded form is exactly
the change most likely to buy length and be scored for it. Per-seat spend
reported: conjecturer, critic, commitment, separately.

**"Better" is Popperian progress** (C6): more error eliminated, survivors
harder to vary, bolder conjectures that survived criticism, deeper successor
problems. An unfinished run with better survivors beats a finished one whose
answer a single call would have matched.

**An inconclusive result is recorded as inconclusive.** No arm is re-run to
get a number, and the pre-registration is sealed before the first call.

    accept: PREREG_D8.md committed with its criteria BEFORE any arm runs;
      its sha recorded in RESULTS.md
    accept: RESULTS.md carries both arms' typed outputs, the blind judging
      output, the length distributions, and per-seat spend

---

## Assumptions (operator may override)

Each resolves an open question from REQUEST.md by derivation, per
`dr-ask-the-right-question` §4. Every one of these is dominant under the
operator's recorded values; each says so and why.

**A1 (Q1) — "commitments disabled" means BOTH commitment channels.**
Chosen because the measurement decides it: with only the model-authored
`forbidden[]` disabled, the mandatory `skeleton-wf` commitment still refutes
every free-prose candidate on arrival — six admitted, six refuted, zero
survivors (`proof/m2_free_prose_today.txt`). A reading of R3 that leaves R2
producing zero survivors is not a reading of R3. Both switches are
independent, so the operator can restore either.

**A2 (Q2) — "not limit prose length at all" means all three limits.** The
form's field bounds, the required skeleton, and the truncation of what a
seat is shown. Derived from R2's own word "at all" and from R6, which asks
for everything generated so far — a 300-character cut on what a conjecturer
sees would make R2 an unlimited channel feeding a limited one.

**A3 (Q3) — the three seats are conjecturer, critic, commitment.** R7 says
"all three seats" immediately after R4 introduces the commitment artifact
and R5 introduces critics. Mini has one seat today, so R7 is naming the set
R3-R5 just built.

**A4 (Q4) — "everything generated so far" means everything in the RUN.**
Not everything for the problem under work. R6's word is "everything", and
mini's isolation runs are single-problem by construction (the standard input
freezes one problem and its criteria). Where a future flow carries several
problems, the section's own parameter decides; it defaults to the whole run.

**A5 (Q5) — "standard" starting input is the frozen `RunInputManifestV2`.**
The same artifact `deepreason input freeze` writes and the full harness
takes: a problem plus its criteria. Derived from R12's word "standard" and
from R1/R11's "the same question file and criteria the full harness takes"
in the window's own D1. The bare-question form stays, so nothing regresses.

**A6 (Q6) — "the larger harness" is the eleven modules named in S1.** Built
by asking what a mini run must NOT activate to be a test of mini rather than
of the harness, and cross-checked against what `compat.py:94-103` already
declares absent. The fence is a test, so a wrong boundary is visible and
cheap to move — **and it moved.** AMENDED 2026-09-05: the eleven modules
stand as the list of what mini must not USE, but the fence measures three
things that can be true rather than one that cannot (S1, amended). Four of
the eleven are already loaded by modules S1 itself allows, because the event
ontology and the harness import their payload and edge types; measured in
`proof/fence_arms.txt`. The amendment costs nothing in scope: mini's two real
violations — one direct import, one package-`__init__` side effect — are both
inside T1 and both fixed there.

**A7 (Q7) — "on the fly" means at run configuration time, not mid-run.** A
flow is resolved once, before the first call, and is immutable thereafter —
the same discipline every other registry here follows, and the one that
keeps a run's record replayable. Mid-run mutation of the artifact-kind set
would make two replays of one log disagree, which is the epistemology
itself. The operator's phrase "if I can see it might help" describes when
THEY decide, not when the run does.

**A8 (C1) — "not permanent" is implemented as: default OFF, registered,
removable by configuration.** Both mini flows ship; the default is
`mini.flow.legacy-v0`, which is today's behaviour exactly. Nothing in the
full harness changes default behaviour, and the two existing seats' goldens
are pinned byte-identical (C4, S10.3).

**A9 (Q-A) — NOT an assumption: an operator ruling.** "Within mini,
criticism overturns nothing" is the operator's own answer of 2026-09-05,
ledgered in CLAUDE.md the same day and recorded in REQUEST.md as Amendment
1. It sits here only as a pointer, so a reader of the assumption list is not
left thinking the question is still open.

---

## Questions for operator (STOP if non-empty)

**NONE OPEN.** The one question this document asked (Q-A) was answered by
the operator on 2026-09-05, before any step ran. It is recorded below as
answered, not deleted, so the reasoning that produced it stays readable.

### Q-A — with commitments off, may a critic eliminate? — ANSWERED: E1 ONLY

**The operator's words, verbatim (2026-09-05):** "within mini, criticism
can't overturn anything. The point is content generation for now. Then
testing on the full harness."

**The ruling, as it binds this programme.** ROAD E1, and only E1. In the
mini flow a criticism is written to the record and shown to whichever seats
the layouts allow, and it CHANGES NO STATUS. No elimination road is built
for mini — not behind a switch, not off by default, not at all.

- **E2 is NOT built.** The recommendation this document previously made
  ("E2 built and switched OFF") is SUPERSEDED by the operator's answer. No
  per-run switch, no fail-warrant road from a free-prose objection, no
  ~40 lines in `mini/minireason/seats.py`.
- **E3 is NOT built here either.** The commitment artifact at S4 PROPOSES
  commitments and eliminates nothing; a proposal is RECORDED, never
  registered as a canonical `Commitment`. S4 already said this; the ruling
  makes it binding rather than provisional, and removes "the flow that
  follows" from this programme's scope.
- **What mini's content is worth is decided later**, by running it through
  the full harness, whose authority layer is unchanged by this programme.
  That is the operator's own "then testing on the full harness".

**Consequence for D8/S12.** The measure compares better-criticised
conjectures against a single call, not eliminated ones. That is the weaker
but honest first result E1's row priced, and the operator has chosen it
knowingly. S12 reports it as such; an inconclusive result stays recorded as
inconclusive (C6, CLAUDE.md Conventions).

**The roads as they were priced, kept for the record.**

| | what it does | cost | risk | disposition |
|---|---|---|---|---|
| **E1 — record only** | criticism is written to the record and shown to nobody it should not be; status never changes in the R3 flow | ~0 extra lines; it is the flow's default | D8 measures better-criticised conjectures, not eliminated ones | **CHOSEN by the operator, 2026-09-05** |
| **E2 — critic may eliminate, behind a per-run switch, default OFF** | a free-prose objection can mint a fail warrant | ~40 lines in `mini/minireason/seats.py` | prose changes status | **NOT BUILT** — "criticism can't overturn anything" |
| **E3 — elimination arrives with the commitment artifact** | the commitment seat's proposals become the warrant road | ~60 lines, one more registered stage | this is the R4 configuration, not the R3 one | **NOT BUILT HERE** — S4 proposes; it eliminates nothing |

---

## Out of scope (explicit)

- **Episodes** (R-again) — the window places them out; nothing here decides
  what an episode is. Not requested.
- **Changing the controller** (R8, C2) — the hook is declared with a no-op
  default and called by nothing. Not requested.
- **The history conjecture experiment** (R-history) — the operator's own
  "but before that" puts it after this programme. Not requested.
- **The four other seats' briefs** — parked as P5 of the pluggable-interface
  tranche. Not requested.
- **Adding any id to `ContractVersionPolicyV3`** — road C2, 3 surfaces, and
  unnecessary (§Options). Not requested.
- **Making the full harness use any of this.** Every default is unchanged.
  Not requested.
- **Any elimination road inside mini** (Q-A roads E2 and E3) — the operator
  ruled E1 only on 2026-09-05: "within mini, criticism can't overturn
  anything." Not requested, and now forbidden.

---

## Frozen-surface contact forecast

`tools/blast_radius.py --files mini/minireason/loop.py
mini/minireason/checks.py mini/minireason/compat.py
src/deepreason/llm/seat_sections.py src/deepreason/llm/seat_layouts.py
src/deepreason/llm/seat_plugins.py src/deepreason/shallow.py --symbols
compile_checks run_checks skeleton_wf_commitment load_operator_plugins
register_seat_pack_layout register_seat_shell resolve_seat_shell
run_shallow_question SeatShellV1 SeatPackLayoutV1`
(full output: `proof/blast_mini_declared.json`)

    "frozen_surface_verdict": "CLEAR"
    "frozen_surface_contacts": []
    "frozen_adjacent_contacts": []

**NO CONTACT. No grant is owed and no STOP is triggered here.**

Two things are disclosed anyway, because a forecast that hides its
near-misses is not a forecast.

**(1) The conservative run.** Declaring the EXISTING mini contract
`ReferenceFreeConjecturerWireContract` as a target — which this programme
does not do, because R-stored keeps it — produces one row
(`proof/blast_mini_conservative.json`):

    "frozen_surface_verdict": "CONTACT"
    [ { "surface": "replay-validation record formats (invariants.py)",
        "tier": "SYMBOL_INDIRECT",
        "target": "ReferenceFreeConjecturerWireContract",
        "detail": "'ReferenceFreeConjecturerWireContract' referenced in
                   src/deepreason/invariants.py (grep-based; not proof of
                   semantic contact)" } ]

Disposed by measurement, not assurance. The reference is
`invariants.py:1258-1265`, inside the `h.workflow_state.work_orders` branch.
Measured on a real mini root: `work_orders (legacy branch input): 0`,
`transaction_work: 0` — the branch is never entered, which is what
`invariants.py`'s own comment at 1199-1204 predicts. And a mini run
dispatching a contract id that has never existed verifies clean:
`proof/m1_new_contract_id.txt`, ARM2, `verify_root violations: 0`.

**(2) A gate false positive worth rowing.** An earlier run declaring the
bare symbol `run` returned CONTACT on all five surfaces plus the frozen-
adjacent one, because `run` is a substring of ordinary words in every one of
those files. Same shape as the `clamp` false alarm `DR-INV-frozen-surfaces`
already records. It is the gate working as documented — its detail strings
say "grep-based; not proof of semantic contact" — and the lesson is to
declare precise symbols, which the run above does.

---

## Blast-radius census

Every hit from `proof/blast_mini_declared.json`'s `consumers`, classified.
`qualification_digest: []` and `wheel_smoke_pins: []` — both empty, which is
itself the census for those two channels.

| target | consumers | classification |
|---|---|---|
| `src/deepreason/llm/seat_plugins.py` | `tests/test_render_layout_policy.py:120,190`, `tests/test_seat_section_architecture.py:74`, `tests/test_seat_section_citation.py:155` | **MUST NOT MOVE** — S5 ADDS three plugins; it changes none |
| `skeleton_wf_commitment` | 13 hits across `tests/test_candidate_compilation.py`, `test_guards.py`, `test_informal.py`, `test_security.py`, `test_trial_accounting.py` | **MUST NOT MOVE** — S3 makes the CALLER consult a policy; the commitment constructor itself is untouched |
| `load_operator_plugins` | 10 hits, all under `tests/test_seat_section_architecture.py` and `test_seat_section_home.py` | **EXPECTED TO MOVE** — S0a gives it its first `src/` call site; `test_seat_section_home.py` gains cases |
| `register_seat_pack_layout` | 18 hits, `tests/test_seat_pack_layout.py` | **EXPECTED TO MOVE** — S0b adds a file-declared road; existing registrations unchanged |
| `resolve_seat_shell` | 5 hits, `tests/test_seat_section_architecture.py:176`, `test_seat_shell_swap.py:32,56,57,107` | **MUST NOT MOVE** — S6 registers three more shells; resolution order is untouched |
| `run_shallow_question` | 7 hits, `tests/test_shallow_reason.py` | **EXPECTED TO MOVE** — S1 adds `--run-input`; the bare-question signature is preserved and its existing cases must still pass |
| `SeatShellV1` | `tests/test_seat_section_architecture.py:174,243,267` | **MUST NOT MOVE** — S6 adds a consumer for an existing field; the model is unchanged |
| `SeatPackLayoutV1` | 18 hits, `tests/test_seat_pack_layout.py` | **MUST NOT MOVE** — S0b adds a construction road; the model is unchanged |
| map: `llm/seat_sections.py` | `CON-packs-and-token-economy.md:41-43`, `INV-seat-section-plugins.md:4` | **EXPECTED TO MOVE** — S11b |
| map: `llm/seat_layouts.py` | `CON-packs-and-token-economy.md:44`, `INV-seat-section-plugins.md:4` | **EXPECTED TO MOVE** — S11b |
| map: `llm/seat_plugins.py` | `CON-packs-and-token-economy.md:45`, `INV-render-layout.md:193`, `INV-seat-section-plugins.md:4`, `SEAM-rules-x-scratch.md:68` | **EXPECTED TO MOVE** — S11b |
| map: `shallow.py` | `SUB-application.md:4` | **EXPECTED TO MOVE** — S1 changes the shallow entry, so that `Owns:` line's document is re-verified |
| map: `SeatShellV1` | `INV-seat-section-plugins.md:126`, `REC-add-a-section-plugin.md:56` | **EXPECTED TO MOVE** — S11b |
| map: `SeatPackLayoutV1` | `CON-packs-and-token-economy.md:43,69`, `INV-render-layout.md:59` | **EXPECTED TO MOVE** — S11b |

**Manual cross-check, required for every symbol the gate reports
`UNKNOWN`** (`compile_checks`, `run_checks`, `SeatShellV1`,
`SeatPackLayoutV1`) — `grep -rn "<symbol>" tests/ docs/map/ mini/tests/`:

    compile_checks    15 hits -> mini/tests/{test_checks,test_chaos,test_normative_kernel,test_gate}.py
    run_checks         8 hits -> mini/tests/{test_checks,test_chaos}.py
    SeatShellV1        5 hits -> tests/test_seat_section_architecture.py,
                                 docs/map/{REC-add-a-section-plugin,INV-seat-section-plugins}.md
    SeatPackLayoutV1  21 hits -> tests/{test_seat_section_citation,test_seat_section_template,
                                        test_seat_pack_layout,test_seat_section_architecture}.py,
                                 docs/map/{CON-packs-and-token-economy,INV-render-layout}.md

`compile_checks` and `run_checks` are **EXPECTED TO MOVE** (S3 adds the
policy parameter; their default behaviour is pinned unchanged by the same
tests).

**A census finding the gate structurally cannot report.** `tools/
blast_radius.py` greps `tests/` only, so it saw none of mini's own 95 tests.
Every `compile_checks`/`run_checks` consumer lives in `mini/tests/`. Rowed
in PARKED.md.

---

## Measurements (DESIGN-AND-STOP)

Every load-bearing claim above, with the command that decided it. Anything
not on this list is an assumption and sits in §Assumptions.

**M1 — a new mini contract id is replay-valid.** `python
experiments/.../proof/m_mini_form.py` (`proof/m1_new_contract_id.txt`):

    --- ARM1 shipped reference_free.v1     verify_root violations: 0
    --- ARM2 new id mini.conjecturer.relaxed.v1   verify_root violations: 0

Supports: D2's Road M; the frozen-surface forecast's disposal (1).

**M2 — a free-prose mini conjecture is refuted on arrival today.**
(`proof/m2_free_prose_today.txt`):

    run_checks verdict -> [{'commitment': 'skeleton-wf', 'verdict': 'fail',
                            'error': 'content does not parse as a skeleton'}]
    summary: {'cycles': 3, 'problems': {'pi-0': 0}, 'refuted': 6}
    survivors: []

Supports: A1; S3's claim that R2 and R3 are one change.

**M3 — the seat-shell walk runs from a live mini session.**
(`proof/m3_seat_shell_reach.txt`):

    ARM A shell resolves -> seat.mini.conjecturer.v0 | form_id: mini.conjecturer.relaxed.v1
      seat-pack.mini.a1.v0: RENDERED 2 section(s); [('problem','rendered',30)]
      seat-pack.mini.a2.v0: FAILED AttributeError: 'dict' object has no attribute 'content_ref'

Supports: S5's "one adapter, not a second renderer"; S6's public entry.

**M4 — both prerequisites are dead.** Same file:

    ARM B loader notices: ([], [])
    ARM B layouts after   : False

Plus `blast_mini_declared.json`'s own summary: "1 declared symbol(s) already
have no live call path today: `load_operator_plugins`". Supports: S0a, S0b.

**M5 — Road M is CLEAR; Road C2 costs three surfaces.**
`proof/blast_mini_declared.json` -> `"frozen_surface_verdict": "CLEAR"`;
`experiments/2026-09-03-change-conjecturer-pluggable-interface/
blast_road_c.json` -> three DIRECT/SYMBOL_INDIRECT surfaces. Supports: the
Options table's rejection of C2.

**M6 — `SeatShellV1.form_id` has no consumer.** `grep -rn "form_id" src/
--include=*.py` -> 3 lines: `seat_sections.py:711` (the field),
`seat_layouts.py:116` and `:124` (the two registrations). Supports: S6.

**M7 — mini's 95 tests are outside the documented gate.** `python -m pytest
mini/tests --collect-only` -> `95 tests collected`; `python -m pytest tests/
--collect-only` -> `5078 tests collected`; `pyproject.toml:58` declares
`testpaths = ["tests", "mini/tests"]`, which an explicit path argument
overrides. Supports: S10.2; PARKED.

**M8 — the judge panel scores length.** Spearman ρ = +0.797, Pearson r =
+0.691, R² = 0.589 between candidate characters and judged total
(`experiments/2026-09-03-change-provenance-history-channel/
RESULTS_M1_QUALITY.md` §3.4). Supports: S12's length control.

**M9 — mini's manifest names a contract its dispatch does not use.**
`compat.py:168` binds `ContractVersionPolicyV3()`, whose
`conjecturer_turn_contract` defaults to `conjecturer.turn.v6`
(`run_manifest.py:674`), while `compat.py:287-291` dispatches
`conjecturer.compact.reference_free.v1`. Supports: D2's claim that a mini
form registry sits outside the V6 Literals. Rowed in PARKED as a truthfulness
question about mini's manifest, not fixed here.

---

## Options

Every rejection cites a measurement.

### The D2 fork — how a relaxed mini form is registered

| | option | files | frozen contact | ~lines | verdict |
|---|---|---|---|---|---|
| **C2** | add the id to `ContractVersionPolicyV3.conjecturer_turn_contract` and teach `wire_contract_for` | `run_manifest.py`, `qualification.py`, `llm/wire.py`, `llm/contracts.py` | **3 of 5** (M5) | ~200 + a grant | **REJECTED** — cites M5, and the prior tranche's PARKED P1: the knob cannot be turned anyway, because any manifest whose `control_plane_policy` differs from the repository preset returns `QUALIFICATION_POLICY_PRESET_MISMATCH` on four committed manifests |
| **M** | a mini-only form registry, selected in `compat.initialize`, outside the V6 Literals | `mini/minireason/forms.py`, `compat.py` | **none** — `CLEAR` (M5) | ~120 | **CHOSEN** — cites M1 (a brand-new contract id verifies with zero violations) and M9 (mini's dispatch already sits outside those Literals) |
| **W** | widen `ReferenceFreeConjecturer` in place to drop its constraints | `llm/wire.py` | none by the gate, but | ~15 | **REJECTED** — it deletes the stored default rather than registering beside it, which R-stored forbids in the operator's own words, and it changes what `qualification.py`'s shallow-fitness battery sends (`qualification.py:63,504` pin that id) |

### The D5 fork — how critics are kept from the commitment proposals

| | option | ~lines | verdict |
|---|---|---|---|
| **filter** | render the section, then strip proposal bytes | ~25 | **REJECTED** — a present-but-blank slot draws more attention than a filled one; the record's own finding on provenance blinding (CLAUDE.md, amended judge law 2026-08-28) |
| **omit** | the critic layout registers no commitment section at all | ~0 beyond the layout | **CHOSEN** — structural, and it is the same shape the blinding finding already required |

### The prerequisite fork — F1/F2 here, or as their own tranche

| | option | cost | verdict |
|---|---|---|---|
| **inside** | S0a/S0b as the first two steps of this checklist | +115 lines to this programme; they land with the work that needs them | **CHOSEN** — cites M4: without them, S5-S8 are a code edit and C8's enforcement clause cannot be satisfied, so the programme cannot honestly claim configuration. Splitting them out means the middle tranches ship a claim their tests cannot make |
| **outside** | two small tranches first | two extra delivery cycles; this programme blocks on both | **REJECTED** — same evidence; nothing in F1/F2 is contested, so a separate approval round buys no information |

### The D8 fork — what ARM 0 is

| | option | verdict |
|---|---|---|
| **single call, matched spend** | **CHOSEN** — C6 names it exactly: "materially better than what the same model produces WITHOUT the harness on the same question ... at matched spend where spend matters" |
| **full-harness run** | **REJECTED** — that measures mini against the harness, which is a different question and the one the isolation requirement (R1) removes |

---

## Budget

Itemized, then summed by the arithmetic below rather than by hand
(`dr-spec-change` §7).

    S0a  45   S0b  70   S1   90   S2  120   S3   55
    S4   85   S5  130   S6  110   S7   35   S8  150
    S9   90   S10 120   S11a 80   S11b 60   S12  80

    $ python3 -c "print(sum([45,70,90,120,55,85,130,110,35,150,90,120,80,60,80]))"
    1320

**1 320 lines is far over the ~300-line single-tranche ceiling, so this is a
PROGRAMME of eight ordered sub-tranches, each with its own delivery**
(`dr-spec-change` §7). Each row's number is the sum of its items:

| | sub-tranche | items | ~lines |
|---|---|---|---|
| T0 | prerequisites (F1, F2) | S0a+S0b | 115 |
| T1 | isolation entry, standard input, the module fence, `SUB-minireason.md` | S1+S11a | 170 |

**T1's 170 is EXCEEDED, and re-baselined rather than absorbed (2026-09-05,
during step 11).** Measured against T0's delivery head `d319f2d6c`, S1's
production diff is **218 insertions**, and `SUB-minireason.md` has not been
written yet (S11a, ~80). Itemised, with what each line is for:

| file | insertions | why |
|---|---|---|
| `src/deepreason/shallow.py` | 117 | the frozen-input reader and its three typed refusals (~50), the `run_input` report that discloses criteria are bound but not compiled (~35), the two starting inputs and their conflict refusal (~25); ~10 lines are comments stating constraints |
| `src/deepreason/cli/main.py` | 40 | `--run-input`, `question` made optional, and the two refusals on the full path that keep "optional" from becoming a silent difference between the paths |
| `mini/minireason/compat.py` | 36 | `bind_mini_root`/`initialize` take a supplied run input; the reopening-mismatch refusal; the fenced `bridge.retry` import replaced |
| `mini/minireason/loop.py` | 8 | forwarding only |
| `src/deepreason/application/__init__.py` | 17 | **not foreseen by S1 at all** — the lazy text-run re-export, which is the S1 amendment's own consequence |

**Why the estimate was low, stated plainly.** S1 priced ONE thing — accept a
`--run-input` and bind it. Three obligations it did not price came with it,
and each is required by a standing law rather than by taste: a frozen input
that cannot be read must fail typed at the point of use, not silently
(all-configurations law); criteria that reach a root's identity without being
compiled into commitments must be DISCLOSED, or a reader who saw the count
would assume they were (disclose-never-die); and making `question` optional
must not leave the full path silently accepting a flag that does nothing.
Together those are ~110 of the 218.

**Nothing here is scope creep.** Every line traces to R1, R11, R12 or to the
amended fence, and the alternative — dropping the disclosure and the
refusals — would ship a smaller change that lies about itself.

**T1's budget is therefore restated as ~300** (218 measured + ~80 for
`SUB-minireason.md`), and the programme total moves from 1 320 to ~1 450. The
later sub-tranches' numbers are untouched; whether they hold is measured when
they run, not assumed here.
| T2 | the mini form registry and the commitment switch | S2+S3 | 175 |
| T3 | the mini source adapter and the three shells | S5+S6 | 240 |
| T4 | the commitment seat, the controller hook, the map | S4+S7+S11b | 180 |
| T5 | the pluggable flow and the architecture tests | S8+S9 | 240 |
| T6 | regression, goldens, the record | S10 | 120 |
| T7 | the measure | S12 | 80 |

    $ python3 -c "print(sum([115,170,175,240,180,240,120,80]))"
    1320

Commits: at minimum one `[COMMIT]` per sub-tranche boundary and one after
each item's tests land — see CHECKLIST.md.

**Frozen surfaces touched: none.** `"frozen_surface_verdict": "CLEAR"`,
measured (§Frozen-surface contact forecast).

---

Rubric: 6/6 yes
- every R has a spec item with a machine-decidable accept? yes — R1/R11→S1,
  R2→S2, R3→S3, R4→S4, R5→S5, R6→S5, R7→S2/S5/S6/S7, R8→S7, R9/R10→S8,
  R12→S1; R-stored→S2; R-again and R-history explicitly deferred with the
  window's own words.
- blast-radius census pasted and every hit classified? yes — 14 rows plus
  the manual cross-check for all four `UNKNOWN` symbols.
- frozen-surface contact forecast recorded? yes — `CLEAR`, with both
  near-misses disclosed and disposed by measurement.
- every mechanism the request names traced to code it actually reaches?
  yes — the seat-shell was traced by RUNNING it from a live mini session
  (M3), not by reading it; the `form_id` half was found to have no consumer
  (M6) and is specified as work rather than as reuse.
- DESIGN-AND-STOP only: every claim measured, every option priced? yes —
  M1-M9, four priced forks.
- nothing in the spec untraceable to an R/C number? yes — every item and
  every assumption carries its numbers.
