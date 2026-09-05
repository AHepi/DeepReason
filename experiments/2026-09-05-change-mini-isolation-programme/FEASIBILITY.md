# Feasibility — what mini has, what the seat-shell gives, what D2 costs
Tranche: `experiments/2026-09-05-change-mini-isolation-programme/`
Phase: written between `dr-capture-request` and `dr-spec-change`, because
SPEC.md's roads have to be priced against measurements rather than against
a reading of the code. Every load-bearing claim below ends in a pasted
command output under `proof/`.

Authority: REQUEST.md. Map ids: recorded in REQUEST.md's map preflight.

---

## 1. What mini is today

MiniReason is `mini/minireason/` (11 modules, 2 213 lines of engine plus
tests and scripts), reached publicly through `deepreason reason --shallow`
(`src/deepreason/shallow.py`). It is not a fork: registration, object
identity, attack construction, adjudication, replay and the append-only log
all execute in the parent `Harness`. Mini owns the outer loop only —
`propose → gate → check → log → rotate` (`mini/minireason/loop.py::run`).

| fact | where | consequence for this programme |
|---|---|---|
| **ONE seat.** `EndpointLease(role="conjecturer", seat=0)` is the only lease mini mints. | `mini/minireason/compat.py:276-281` | R7's "all three seats" means building two seats mini does not have |
| **The brief is a hard-coded f-string.** `_prompt(description, stance_directive, neighbourhood, vs_k)` builds the whole conjecturer brief inline. | `mini/minireason/loop.py:351-370` | mini reaches NONE of the seat-shell machinery today |
| **Criticism is mechanical, not a seat.** `checks.run_checks` executes the candidate's own `forbidden` cases; failures become fail-warrants. There is no critic call. | `mini/minireason/checks.py:83`, `loop.py:706-711` | R3's "conjecture/criticism cycles" needs a criticism SEAT built |
| **The form is strict by construction.** The brief demands a JSON skeleton `{claim, mechanism, scope, forbidden[], prose_notes}`, and `skeleton_wf` fails any content that does not parse or that forbids nothing. | `loop.py:355-364`; `src/deepreason/informal/skeleton.py:106-121` | R2/R4's "does not force a strict format" lands here |
| **What a seat SEES is truncated twice.** `_neighbourhood` takes the last `k` survivors (`k=8`) and cuts each to `content[:300]`. | `loop.py:340-349` | R6's "everything generated so far" contradicts both cuts |
| **Mini's wire contract is its own.** `conjecturer.compact.reference_free.v1`, chosen directly in `initialize`, NOT through `wire_contract_for`. | `compat.py:287-291`; `src/deepreason/llm/wire.py:1393-1407` | this is why D2 has a road that is not C2 — see §4 |
| **Mini binds a CONSTANT process root, not a real question.** `minireason:process-root`, "no frozen input criteria and no evidence". Problems arrive per `run()` call as bare `(id, description)` pairs. | `compat.py:80-90` | R12's "standard starting input" lands here |
| **Mini already omits the transactional V6 authorities.** `production_qualification_policy`, `terminal_commitment_policy` and four others are absent by design. | `compat.py:94-103` | R1/R11's isolation is already three-quarters true |
| **Mini's `State` is a DICTIONARY view, not ontology objects.** | `mini/minireason/log.py:114`; measured, `proof/m3_seat_shell_reach.txt` | the one real adapter this programme must build — §3 |

**The map gap.** No `docs/map/` document names `mini/minireason/`. This
programme's entire subject is unmapped, which is why REQUEST.md records
creating `SUB-minireason.md` as work rather than as an errand.

---

## 2. What the seat-shell gives

The 2026-09-03/09-04 tranches shipped exactly the machinery R7 asks for,
for the full harness's two seats (`docs/map/INV-seat-section-plugins.md`):

| piece | what it is | file |
|---|---|---|
| `SeatSectionPluginV1` | one protocol, every section, every seat: `render(request, params) -> SectionRenderV1 \| None` | `llm/seat_sections.py:164` |
| `SectionRequestV1` | everything a plugin may read (`problem`, `state`, `commitments`, `blobs`, `layout`, `supplied`), frozen, and nothing it may write | `llm/seat_sections.py:61` |
| `SeatPackLayoutV1` | one seat's brief as an ordered list of `(plugin_id, priority, droppable, compressible, min_tokens, params)` | `llm/seat_sections.py:352` |
| `SeatShellV1` | the pairing: `seat_id + layout_id + form_id + role_prompt_template_id` | `llm/seat_sections.py:704` |
| `_walk_seat_layout` | THE ONE legal way a brief section is constructed | `llm/packs.py:422` |
| the seeded plugins | 20 conjecturer + 10 critic + an episode slot | `llm/seat_plugins.py` |
| the two shipped shells | `seat.conjecturer.legacy-v0`, `seat.critic.legacy-v0` | `llm/seat_layouts.py:110-126` |

**Three facts that decide how much of D6/D7 is new work.**

**(a) The walk runs from a live mini session, with no scheduler, no V6
transaction and no manifest policy.** Measured, not assumed
(`proof/m3_seat_shell_reach.txt`):

    ARM A shell resolves -> seat.mini.conjecturer.v0 | form_id: mini.conjecturer.relaxed.v1
      seat-pack.mini.a1.v0: RENDERED 2 section(s); [('problem', 'rendered', 30)]
      seat-pack.mini.a2.v0: FAILED AttributeError: 'dict' object has no attribute 'content_ref'

So a mini seat registers a layout and a shell, resolves them, and renders a
brief through the shipped walk. What fails is the second line: the
record-backed plugins read ontology objects, and mini's `State` hands back
dicts. **The gap between mini and the seat-shell is one adapter, not a
second renderer.**

**(b) `SeatShellV1.form_id` has no consumer.** `grep -rn "form_id" src/`
returns three lines: the field's declaration and the two shipped shells.
Nothing reads it. The shell pairs a layout with a form DECLARATIVELY, and
only the layout half is wired — the form is still chosen at each dispatch
site. So R7's "same pluggable interface" for the OUTPUT half is not
something to reuse; it is something to finish, and mini is the cheapest
place to finish it because mini has one dispatch site.

**(c) Neither prerequisite works today.** Both are already parked as F1 and
F2 of `experiments/2026-09-04-experiment-brief-variation-step1/PARKED.md`,
and this programme re-measured both:

    ARM B loader notices: ([], [])
    ARM B layouts after   : False
    ARM B VERDICT: a layout declared in a FILE is NOT registered (F2 confirmed)

`load_operator_plugins` has no call site under `src/` (F1) and returned
`([], [])` — no notices at all, so a file that was not loaded is silent.
`register_seat_pack_layout` is reachable only from Python (F2). Without
both, D5–D7 are a code edit, not configuration, and C8 (the modularity
law's enforcement clause) is not satisfiable.

---

## 3. The one adapter

`SectionRequestV1` types `state`, `problem`, `commitments` and `blobs` as
`Any`, so nothing stops mini passing its own objects. What stops it is that
the shipped plugins call `.content_ref`, `.interface`, `.provenance` on what
`state.artifacts[id]` returns, and mini's `State` returns `dict`
(`proof/m3_seat_shell_reach.txt`: `mini State.problems[pid] type: dict |
keys: ['criteria', 'description', 'id', 'provenance']`; adapting that one
value with `Problem.model_validate` made `dr.problem` render 30 bytes).

This is a read-only projection from mini's dict view to the ontology types
the plugins already expect. It writes nothing, changes no digest, and is the
`DR-INV-seat-section-sources` pattern applied to a second engine: a plugin
that needs the record is asking for a SOURCE.

---

## 4. What D2 costs — measured

### 4.1 The fork, stated precisely

R2 wants mini forms with no prose limit, as registered forms alongside — never
replacing — the stored default (R-stored). There are two roads to "a new
form", and the window is right that they are priced very differently.

**Road C2 (the expensive one, already priced by another tranche).** Add the
new form's id to `ContractVersionPolicyV3.conjecturer_turn_contract`
(`run_manifest.py:674`, today `Literal["conjecturer.turn.v6",
"conjecturer.turn.v7"]`) and let `wire_contract_for` return it. The
conjecturer-pluggable-interface tranche measured this road's blast radius
and committed the result at `blast_road_c.json` — **3 of 5 surfaces**:

    "surface": "manifest schemas and validators (run_manifest.py)",   "tier": "DIRECT"
    "surface": "qualification subject digests (qualification.py)",     "tier": "DIRECT"
    "surface": "replay-validation record formats (invariants.py)",     "tier": "SYMBOL_INDIRECT", "target": "wire_contract_for"

and its own PARKED P1 records that the knob cannot be turned anyway: any
manifest whose `control_plane_policy` differs from the repository preset
returns `QUALIFICATION_POLICY_PRESET_MISMATCH` on four committed manifests.

**Road M (the mini-only one).** Mini does not use `wire_contract_for` and
does not use `conjecturer.turn.v6`. It selects
`ReferenceFreeConjecturerWireContract` directly in `compat.py:287-291`, and
its manifest's `ContractVersionPolicyV3()` default is nominal — the field
records `conjecturer.turn.v6` while the dispatch uses
`conjecturer.compact.reference_free.v1`. A mini form registry therefore sits
entirely outside those Literals.

### 4.2 Does a new mini contract id stay replay-valid?

This is the question the whole fork turns on, and it is decidable by
experiment rather than by reading. `proof/m1_new_contract_id.txt`:

    --- ARM1 shipped reference_free.v1
      stop=queue-exhausted cycles=6 problems={'pi-0': 6}
      verify_root violations: 0
    --- ARM2 new id mini.conjecturer.relaxed.v1
      stop=queue-exhausted cycles=6 problems={'pi-0': 6}
      verify_root violations: 0

Arm 2 dispatches a wire contract whose id has never existed, whose wire
model has no required skeleton and no length bound, through mini's real
`run()` into a real root — and `verify_root` returns **zero violations**.

The one thing that could have made this false is the hard-coded mini
allowance at `invariants.py:1258-1265`, which adds
`ReferenceFreeConjecturerWireContract().contract_id` to an authorised set.
That branch is unreachable for a mini root, measured:

    work_orders (legacy branch input): 0
    transaction_work: 0

`h.workflow_state.work_orders` is empty, which is what `invariants.py`'s own
comment at line 1199-1204 predicts ("transactional work lives in
transaction_work instead"). So the authorised-contract-id set is never
consulted for a mini root, and a new mini contract id does not need to be
added to it.

### 4.3 Blast radius, Road M

`proof/blast_mini_declared.json` — declared targets are the mini engine
files, the three seat-shell files the prerequisites touch, and
`src/deepreason/shallow.py`:

    "frozen_surface_verdict": "CLEAR"
    "frozen_surface_contacts": []
    "frozen_adjacent_contacts": []
    "disclosure_summary": "This change touches none of the five frozen
      surfaces. 1 declared symbol(s) already have no live call path today,
      independent of this change: load_operator_plugins. 8 test file(s) and
      6 map document(s) assert on the touched targets today."

A deliberately conservative second run additionally declared
`ReferenceFreeConjecturerWireContract` as a target symbol, to see what the
gate says if the existing mini contract were touched
(`proof/blast_mini_conservative.json`):

    "frozen_surface_verdict": "CONTACT"
    [ { "surface": "replay-validation record formats (invariants.py)",
        "tier": "SYMBOL_INDIRECT",
        "target": "ReferenceFreeConjecturerWireContract",
        "detail": "'ReferenceFreeConjecturerWireContract' referenced in
                   src/deepreason/invariants.py (grep-based; not proof of
                   semantic contact)" } ]

**Disposal, by measurement rather than assurance.** That row appears only
when the EXISTING contract is declared as a target. This programme does not
declare it: R-stored says the current default form is stored, not deleted,
and Road M ADDS a form beside it. And even if it were declared, §4.2 shows
the referencing branch is unreachable for a mini root (`work_orders: 0`) and
a brand-new id verifies clean. The gate states its own method in the detail
string — "grep-based; not proof of semantic contact" — and this is the same
shape as the `clamp` false alarm `DR-INV-frozen-surfaces` already rows.

### 4.4 The answer to D2's stop condition

The window's instruction was: "if only C2 reaches the goal, STOP at that
fork." **C2 is not the only road.** Road M reaches R2's goal — relaxed mini
forms as registered ids, alongside the stored default — with a measured
`CLEAR` verdict and a measured zero-violation replay. No STOP is owed here.

---

## 5. What R3 and R4 cost — measured

R3 wants the cycles run with commitments disabled, and R4 wants a separate
artifact that generates commitments in free prose. Today those two are one
thing: `compile_checks` always prepends the mandatory `skeleton-wf`
commitment, and the conjecturer is the only thing that can produce
commitments at all. `proof/m2_free_prose_today.txt` shows what happens now
to a free-prose conjecture:

    prose chars: 2360
    compile_checks(prose) -> [{"id": "skeleton-wf", "eval": "program:skeleton_wf", ...}]
    run_checks verdict    -> [{'commitment': 'skeleton-wf', ..., 'verdict': 'fail',
                               'error': 'content does not parse as a skeleton'}]
    summary: {'stop': 'queue-exhausted', 'cycles': 3, 'problems': {'pi-0': 0},
              'refuted': 6, 'gate_blocks': 0}
    survivors: []

Six candidates admitted, six refuted on arrival, **zero survivors**, and the
problem declared dry after three cycles. So R2 without R3 produces a run
that cannot survive anything: the relaxed form and the commitment switch are
one change, not two, and neither is optional if the other ships.

Both files are mini-owned (`mini/minireason/checks.py`,
`mini/minireason/loop.py`) and neither is a frozen surface.

---

## 6. Where the pieces land

| requirement | new, or already there | where |
|---|---|---|
| R1, R11 isolation | mostly there — mini already omits the V6 transactional authorities and never touches the qualification cache | `compat.py:94-103`, `shallow.py:1-9` |
| R2 relaxed forms | NEW: a mini form registry (Road M, CLEAR) | `mini/minireason/forms.py` |
| R3 commitments off | NEW: a switch on `compile_checks`' mandatory commitment | `mini/minireason/checks.py` |
| R4 commitment artifact | NEW: a second seat and a second artifact kind | `mini/minireason/seats.py` |
| R5, R6 who sees what | REUSE: layouts, once the adapter exists | `llm/seat_layouts.py` + a mini source |
| R7 one interface | REUSE for the brief half; FINISH for the form half (`form_id` has no consumer) | `llm/seat_sections.py`, `mini/minireason/seats.py` |
| R8 controller hook | NEW, declared only, no-op default | `mini/minireason/seats.py` |
| R9, R10 pluggable flow | NEW: a registered flow definition | `mini/minireason/flow.py` |
| R12 standard input | NEW: accept a bound `RunInputManifestV2` instead of the constant process root | `compat.py:80-90` |
| prerequisites F1, F2 | NEW: the loader's call site and a file-declared layout | `llm/seat_sections.py` |

---

## 7. The residue — what this document does NOT establish

Stated plainly, because "accepted does not mean true".

- **The window's premise that a mini run inside a conjecture call "bought no
  variety at +56% cost" is not located in the committed record.** `grep -rn
  "56%" experiments/ docs/` returns only pytest progress bars, an unrelated
  budget-interruption note, and a criticism-census row. The programme's
  direction does not rest on it — R1 says "mini needs to be tested in
  isolation" in the operator's own words — but the number should not be
  repeated as though the record carried it.
- **Every measurement here is offline, against `MockEndpoint`.** They prove
  what the harness ACCEPTS, not what a model produces. D8's comparison is
  the only thing that can answer whether any of this is better, and it has
  not been run.
- **`verify_root` returning zero violations on a six-cycle mock run is a
  narrow claim.** It says a new contract id is not rejected. It does not say
  a long-horizon mini run with three seats and a new artifact kind stays
  valid; that is what the programme's own regression tests must establish.
