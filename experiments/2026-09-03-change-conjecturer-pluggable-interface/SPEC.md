# SPEC — the conjecturer's brief and form as a pluggable, configurable interface

Tranche: `experiments/2026-09-03-change-conjecturer-pluggable-interface/`
Phase: STEP 2 of the design window (`R12`: "Then creating a spec that can be
worked on later").
Authority: `REQUEST.md` §1 and §1a. Every requirement here cites an R-number
from that file and a finding from `FEASIBILITY.md`.
Base: `main` at `2d84a86cd`.

**This spec is written to be EXECUTED BY SOMEONE ELSE, LATER, FROM THE
ARTIFACTS ALONE.** No conversation context is assumed. Read `REQUEST.md`,
then `FEASIBILITY.md`, then this, then `CHECKLIST.md`.

**No production code is written in this window.** Approval by the operator
is the gate between this document and any implementation.

**APPENDED 2026-09-03, build window** (a pointer, not a revision of anything
above it): the operator approved this spec and amended it the same day.
The amendment is `REQUEST.md` §1b and **§17 below**, which REPLACES §14's
"designs nothing for the critic" and changes nothing else. Read §17 after
§16. Build base: `main` at `e91f4fcc3`.

---

## §0 Scope

**In scope: the CONJECTURER seat** (`M5`). Two things become configurable:

1. **THE BRIEF** — the material the seat is shown. Today
   `llm/packs.py::render_conj_pack` (FEASIBILITY §1). Becomes an ordered
   list of registered SECTION PLUGINS, each owning one information source
   and its own formatting.
2. **THE FORM** — what the seat is asked to return. Today a hardcoded
   dispatch (`wire.py::wire_contract_for`, `conj.py:1550-1568`;
   FEASIBILITY §3). Becomes a selectable, versioned artifact with two
   halves kept apart.

**Out of scope, stated so a later executor does not drift into it:**
implementing the critic seat (`M5` — this spec NAMES the seam and stops);
deciding episodes (`R13`, `M6` — a plugin slot is left, and nothing more is
said); the transport, F4, F7 and hv tranches; the P1/P2/P3 items in
`PARKED.md`; and **road C2** — an OPEN form registry admitting new contract
ids, which contacts three frozen surfaces (FEASIBILITY §6.3, §7) and needs
its own grant.

**Road chosen: A + template layer + C1** (FEASIBILITY §8). C1 is the half of
form work reachable with zero frozen-surface contact: selection among
already-registered forms, per-run wire variation under a FIXED contract id,
and lenient normalisation into the unchanged canonical artifact.

## §1 Assumptions, recorded

`dr-change-orchestrator` §1: where REQUEST.md is silent, the smallest
reasonable interpretation is taken and RECORDED here.

- **A1 (decides Q2).** A section plugin's output is free text (`R7`), but
  HANDLE RENDERING is not the plugin's to suppress. Derived from
  `DR-INV-reference-menu` FROZEN clause (b) — "a menu changes what the model
  is SHOWN; it may never change what the harness ACCEPTS" — so a free-text
  evidence plugin cannot break citation VALIDITY, only citation USE
  (FEASIBILITY §5). Mechanism in `S6` below. Not escalated to the operator.
- **A2 (decides Q3).** The form's PARSE half NEVER varies per model. Derived
  from `R16` ("outputs need strict minimum standards") and the standing law
  that seats change how content is GENERATED, never what counts as EVIDENCE
  (CLAUDE.md). `M3`, `M7`. Not escalated.
- **A3 (Q4, CARRIED — the operator hedged this clause).** `R17`'s "adapting
  the accepted outputs so they compile" is read as `M7`: normalisation that
  yields the SAME typed canonical artifact is in scope; any leniency that
  changes what is admitted, ranked, immune, or refuted is OUT of scope and a
  STOP. `S8` names every normalisation proposed, so confirming or narrowing
  costs the operator a reading rather than a design session.
- **A4.** "Not typed" (`R7`) constrains the plugin's OUTPUT, not its
  RECEIPT. The record of what ran stays typed (`M1`). A plugin that emitted
  nothing typed at all would make the run unauditable, which contradicts the
  repo's own epistemology ("the record is the only admissible evidence").
- **A5.** Today's rendering is the DEFAULT (`M2`). The build ships with
  `conj-pack.legacy-v0`, a layout whose default render is BYTE-IDENTICAL to
  `2d84a86cd`'s on a fixed record. Nothing changes unless someone configures
  it. This is `S10`, the acceptance test the whole tranche turns on.
- **A6.** The nine brief sections computed in `rules/conj.py` rather than in
  the renderer (FEASIBILITY §2) stay computed there in this tranche. Their
  plugins FORMAT a value the caller supplies; they do not acquire the
  dossier receipt, fence-seq and work-order plumbing. Moving that
  computation behind the interface is a later step, and `S11`'s architecture
  test still forbids adding a NEW section by source edit.

## §2 The section-plugin interface — S1

**S1.1 The protocol.** One generic interface serves every section (`R5`):

```
class ConjecturerSectionPluginV1(Protocol):
    plugin_id: str        # "dr.evidence.frozen", "dr.history.v1", ...
    plugin_version: str   # semver; part of the receipt
    parameters_model: type[BaseModel]   # this plugin's knobs (R6)

    def render(self, request: SectionRequestV1, params: BaseModel)
        -> SectionRenderV1 | None
```

**S1.2 Input** (`R1`): `SectionRequestV1` is a frozen record carrying the
run's state and the problem — `problem`, `state`, `commitments`, `blobs`,
`layout` (the existing `RenderLayoutPolicyV1`), and `supplied`, a mapping of
the caller-computed contexts of FEASIBILITY §2 keyed by their existing
argument names (`frozen_evidence_context`, `citable_evidence_context`,
`frame_slice_context`, `frame_crisis_context`, `open_criticism_context`,
`capability_result_context`, `scratch_context`, `generation_context`,
`reference_menus`). Read-only: the request model is `frozen=True` and
`render` may not call the harness or write the log — the same prohibition
`DR-CON-conjecture-source` already places on `conj`.

**S1.3 Output** (`R7`, `R8`, `A4`): `SectionRenderV1` carries

| field | meaning |
|---|---|
| `text` | FREE TEXT. The harness does not parse it, does not interpret it, and asserts nothing about its content. The plugin formats it (`R8`). |
| `section_id` | the pack section id, for the `## id` header |
| `priority`, `droppable`, `compressible`, `min_tokens` | the `PackSection` fields, defaulted from the layout entry and overridable by the plugin |
| `provenance_refs` | as today |
| `declared_handle_kinds` | which reference-menu handle kinds this section's content makes citable (`A1`, `S6`) |

Returning `None` means "this section has nothing this cycle" — exactly
today's `if <context>:` guards. A returned empty `text` is an ERROR, not an
absence: the distinction between "no content" and "content that rendered
empty" is the one the allocator's drop signal already depends on
(`DR-INV-render-layout` Traps, the `## id` header rule).

**S1.4 The typed receipt** (`M1`, `A4`). Every `render` call produces a
`SectionReceiptV1`: `section_id`, `plugin_id`, `plugin_version`,
`parameters_digest` (sha256 over the canonical JSON of the resolved
params), `source_bytes`, `rendered_bytes`, and `disposition` ∈ `{rendered,
compressed, dropped, absent}`. Written to the record per `S7`.

**S1.5 The seeded plugins.** One per row of FEASIBILITY §1's table, ids
namespaced `dr.*`, each reproducing that row's text byte-for-byte at default
parameters. The three the operator named explicitly get first-class ids:
`dr.evidence.frozen` + `dr.evidence.citable` (`R2`), `dr.history.v1`
(`R3`), `dr.neighbourhood` + `dr.neighbourhood.live` (`R4`).

**S1.6 History** (`R3`, and the operator's opening line "History should be
in evidence"). `dr.history.v1` renders prior-round material as EVIDENCE
rather than as narration, and its parameters include `include_refuted`
(default `false` — today's `layout.superseded_summary_n == 0`). It is a
SEPARATE plugin from the evidence pair, per the operator's own list, and
both may be present at once.

**S1.7 The episode slot** (`R13`, `M6`). The registry admits a plugin id
`dr.episodes.slot` that is REGISTERED AND UNIMPLEMENTED: it is not in any
shipped layout, renders `None` if invoked, and carries a docstring saying
the operator has not decided what episodes are. Nothing else in this spec
mentions episodes.

## §3 The registry and its versioning — S2

**S2.1** `llm/conj_sections.py` holds `SECTION_PLUGIN_REGISTRY`, keyed
`(plugin_id, plugin_version)`, with `register_section_plugin(plugin)` and
`resolve_section_plugin(plugin_id, version=None)`. Modelled on
`llm/layout.py::register_layout_policy`, which `DR-INV-render-layout` proves
needs no consumer edit.

**S2.2 Versioning.** A plugin's id is stable; its version moves when its
DEFAULT RENDER changes. A layout entry may pin a version; unpinned resolves
to the highest registered. A receipt always records the resolved version, so
"which bytes did this run actually show" is answerable from the record
alone.

**S2.3 The one legal consumer.** `render_conj_pack` resolves plugins ONLY
through `resolve_section_plugin`. Asserted by `S11`.

## §4 Operator-authored plugins from the home directory — S3

**S3.1** Operator plugins load from `<provider_state_dir>/conj_plugins/`,
the way `model_profiles/registry.py::profiles_root` (58-65) resolves
`<provider_state_dir>/<PROFILES_DIRNAME>` (`M4`). Nothing ships in the
repo: a harness with no plugin directory has exactly the seeded `dr.*` set,
and says so rather than guessing — `DR-CON-model-profiles`' own stance.

**S3.2 Trust boundary, stated because it is a security boundary and not a
courtesy** (`M4`). An operator's plugin is TRUSTED — the operator authors
treadle tasks on the same basis (CLAUDE.md, "Who may author a task").
**Nothing model-authored is ever a plugin, ever.** A plugin file is loaded
only from that directory; no run, no model reply, no fetched document and no
tool result may write into it or name a plugin path. A plugin id appearing
in a configuration that does not resolve in the registry is a typed refusal
at resolution, never a load-by-path.

**S3.3 Two authoring kinds.** A `.py` file registering a
`ConjecturerSectionPluginV1` (full power, executed), or a `.tmpl` template
(`S4` — no code). The template kind exists so that changing a FORMAT costs a
text file rather than a Python file (`R8`, `R9`).

**S3.4 Load failures are disclosed, never silent.** A plugin directory
holding an unloadable file yields a typed notice naming the file and the
error, and the run continues with the plugins that did load — the
all-configurations-allowed law's "disclose, never die" shape, applied here.

## §5 The template layer — S4

**S4.1** A template is a text file whose body is the section's `text`, with
two constructs and no others: `{{ name }}` substitution and
`{% for x in list %}…{% endfor %}` iteration, over a bounded, plugin-declared
context. **No expression evaluation, no attribute traversal beyond one dot,
no imports, no filters that call code.** An operator template must not be
able to execute; the trust granted in `S3.2` is a reason to keep the
template's power small, not a reason to widen it.

**S4.2** Templates resolve from the same home directory
(`<provider_state_dir>/conj_plugins/*.tmpl`) and register as ordinary
plugins whose `render` is "bind the context, expand the template".

**S4.3 Rendering is bounded.** Expansion has a hard output ceiling
(the layout entry's `max_render_bytes`, default = the source size, matching
`_pack_section`'s existing `max_tokens = approximate_tokens(text)` pin).
Overrun is a typed error naming the template, never a silent clip — the
NO SILENT CAPS rule `_allocate_sections` already enforces.

## §6 Citation stays intact — S5, S6

**S5** (`A1`). A plugin declares `declared_handle_kinds`. The registry — not
the plugin — renders the reference menu for those kinds through the existing
`reference_menu.menu_renders_for`, at the existing priority 4
(`packs.py:961`). A plugin may render evidence however it likes; it cannot
ALSO suppress the menu.

**S6.** `citable-evidence-blocks` and `frozen-evidence-context` stay in
`DISCLOSED_ON_DROP` (`packs.py:352-360`) under their plugin ids, so a
budget-cut evidence section still produces the `context-withheld` notice.
A layout that registers an evidence-family plugin OUTSIDE that set is a
typed refusal at layout construction.

**Nothing here touches validity.** The contract's enum and the §4 checker
decide what is accepted, exactly as today (FEASIBILITY §5).

## §7 The record — S7

**S7.1** A new object kind `workflow.context-section-plan.v1` (FEASIBILITY
§4 option (a)), one per rendered conjecturer pack, carrying `work_id`,
`attempt_index`, `layout_id`, `layout_version`, and `sections[]` of
`SectionReceiptV1` (`S1.4`).

**S7.2 Why a new kind and not a new `plan_kind`.** The existing
`workflow-context-pack-plan-v1` family's four `plan_kind` values —
measured over the corpus at 1 905 `dossier`, 1 406 `combined`, 177
`scratch`, 45 `citable` (`census_output.txt`) — all mean "an evidence
channel exposed these bytes". A section row is a different thing, and
`items[].namespace`/`alias` do not fit it. A new kind is additive to a root
and invisible to every reader that does not ask for it.

**S7.3 No new `verify_root` check.** Frozen surface 3 is NOT touched
(FEASIBILITY §4). The allocator's existing accounting already binds what
rendered; a replay check would be new format, and this tranche does not
need one.

## §8 The form — S8, S9

### S8 — the two halves, and the leniency boundary (`R10`, `R16`, `R17`, `A2`, `A3`)

**S8.1** The halves already exist in code: `WireContract(contract_id,
wire_model, canonical_model)` with `validate_json` → wire, `compile` →
canonical (FEASIBILITY §3). This tranche does not invent them; it makes the
WIRE half selectable and leaves the PARSE half fixed.

**S8.2 What may vary (WIRE):**
- **which registered form a seat uses** — among ids ALREADY in every
  `Literal` today: `conjecturer.turn.v6`, `conjecturer.turn.v7`,
  `conjecturer.atomic-candidate.v1`. Selection per seat.
- **the schema presentation under a FIXED contract id** — field pruning and
  enum binding, the mechanism `_bind_discharge_field` (wire.py:899-916) and
  `_bind_alias_fields` (918-963) already use, and which is already proven
  byte-neutral when the feature is off.
- **the prose wrapper** — `roles.py::TEMPLATES` / `COMPACT_TEMPLATES`
  (roles.py:27, 287) become registered, selectable role-prompt templates
  rather than module literals. This is the "adjusted for an LLM's
  capabilities" half of `R10`.

**S8.3 What may NEVER vary (PARSE, `A2`):** the canonical model every form
compiles to; `_reject_control_fields` and `_reject_unknown_fields`; the
anti-relapse gate; interface compilation from the problem's own criteria;
admission, rank, immunity and refutation. `M7`'s "strict minimum standards"
IS this list.

**S8.4 Lenient normalisation (`R17`, `A3` — the exact list, so the operator
can confirm or narrow by reading).** Proposed additions to
`validate_value`, each of which must yield a canonical artifact IDENTICAL to
one a strictly-conforming reply would have produced:

| # | normalisation | precedent |
|---|---|---|
| N1 | a single-element array wrapping the one expected object | ALREADY SHIPS, wire.py:1003-1013, with its live justification inline |
| N2 | a scalar supplied where a one-element array is required, on a field whose item type it matches | none — new |
| N3 | a menu INDEX where a handle is required | ALREADY SHIPS as `_resolve_menu_indices`; N3 only extends it to fields the menu covers but the resolver does not yet visit |
| N4 | an absent OPTIONAL field supplied as `null` or `""` | none — new |
| N5 | the whole object wrapped in one redundant key naming the contract | none — new; the E42 spelling class (W1 census §6) is this shape |

**Every one of N1-N5 is a SHAPE normalisation on the transport, and none
touches a VALUE.** A normalisation that would change which handle is cited,
which commitment is discharged, or whether a candidate abstains is refused
and is a STOP — that is `A3`'s boundary made checkable, and `S11.4` is the
check.

**S8.5 Failure is recorded per normalisation.** Each application writes its
rule id into the attempt's diagnostic trail, so "how much did leniency buy"
is answerable from the record rather than from argument — the same standard
`census_conjecturer_failures.py` applies to everything else.

### S9 — per-model form selection (`R10`, `M3`)

**S9.1** A model's profile document (`CON-model-profiles`, `agent.md` in the
operator's home directory) gains an OPTIONAL `preferred_conjecturer_form`
naming a registered form id. Optional, and its absence means nothing — the
harness "holds no per-model opinion of its own" and "says so rather than
guessing", which is that concept's own stated stance.

**S9.2 Resolution order:** explicit per-seat configuration → the model
profile's preference → the layout default → `conjecturer.turn.v6`. Every
step recorded in the section plan (`S7.1`) and in the run's own record.

**S9.3 The gate that is not one.** Selecting a form emits a typed NOTICE,
never a refusal (the ungated-seats law, 2026-08-28). If a selected form is
not registered, the refusal is typed AT THE POINT OF USE, not at compile —
the all-configurations-allowed law's own shape.

**S9.4 The frozen-surface boundary, restated where an executor will hit
it.** `S8.2`'s three ids are the ONLY ones selectable. Adding a NEW
contract id is road C2 and is OUT OF SCOPE (§0): it contacts
`run_manifest.py`, `qualification.py` and `verification/`, and
`price_form_registry.py` measures that selecting a form through the manifest
returns `QUALIFICATION_POLICY_PRESET_MISMATCH` on all four committed
manifests tested. **Selection in this tranche therefore goes the
`DR-INV-render-layout` way — argument, then environment, then default — and
never through `Config` or the manifest.** That single decision is what keeps
the whole tranche at `frozen_surface_verdict: CLEAR`.

## §9 The three layers — S10a (`R11`, `M4`, modularity law)

Per `DR-INV-signal-contract`'s pattern, as `DR-INV-reference-menu` and
`DR-INV-render-layout` both state it:

| layer | what it holds | what changing it takes |
|---|---|---|
| **FROZEN** | (a) a plugin's output is presentation, never evidence — no plugin may change what is admitted, ranked, immune or refuted; (b) the parse half does not vary (`A2`); (c) no silent truncation; (d) only the operator authors a plugin (`S3.2`) | an operator design law |
| **VERSIONED** | `SECTION_PLUGIN_REGISTRY`, the form registry, the role-prompt template registry, and the shipped layouts | registering an entry — never a consumer edit |
| **FREE** | every plugin's `params`, and the layout's per-entry `priority`/`droppable`/`compressible`/`min_tokens`/`max_render_bytes`, inside declared envelopes, refused typed at construction rather than silently clamped | ordinary configuration |

## §10 The per-seat layout configuration — S10

**S10.1** `ConjecturerPackLayoutV1`: `layout_id`, `layout_version`, and
`entries[]` of `(plugin_id, plugin_version | None, priority, droppable,
compressible, min_tokens, max_render_bytes, params)`.

**S10.2 Selection** (`S9.4`): argument → `DEEPREASON_CONJ_PACK_LAYOUT` →
default. **NOT a `Config` field and NOT a manifest field** — the reason is
measured, not preferred (FEASIBILITY §6.2: the carried variant MOVES every
qualification subject digest; the off-manifest variant does not move any).

**S10.3 `conj-pack.legacy-v0` ships as the default** and reproduces
FEASIBILITY §1's table exactly — same twenty ids, same priorities, same
droppable/compressible flags, same caps.

**S10.4 THE ACCEPTANCE TEST THIS TRANCHE TURNS ON** (`A5`, `M2`): on a
fixed committed record, `render_conj_pack` under `conj-pack.legacy-v0`
returns bytes IDENTICAL to `2d84a86cd`'s output for the same inputs.
Implemented as a golden captured from the base commit BEFORE any refactor
and committed in the same tranche. If this test cannot be made to pass, the
refactor is wrong and the tranche stops — it does not get a fixture update.

## §11 The architecture tests — S11 (`R11`, modularity law: "enforced"
## means a check that can fail)

Four tests, each RED under a specific bypass. A test that cannot fail is not
a check (`docs_verify --audit`'s own standard, owed here too).

- **S11.1 — no consumer bypasses the registry.** RED if `render_conj_pack`
  constructs a section other than through `resolve_section_plugin`.
  Implemented as a source assertion pinning the call COUNT, the shape
  `DR-INV-render-layout` already uses for its `_head` bypass trap.
- **S11.2 — adding a plugin needs no source edit.** The test registers a
  brand-new plugin from a temp home directory, renders a pack with it in
  the layout, asserts its text appears and its receipt is written, and
  touches no file under `src/`. RED if any source edit is required.
- **S11.3 — shape buys nothing** (`M9`, `R-g` formalism-optional law). RED
  if any of admission, rank, criticism exposure, immunity or acceptance
  reads a `plugin_id`, `layout_id`, `form_id` or `SectionReceiptV1` field.
  Implemented as a reachability assertion over the scheduler, adjudication
  and rules packages: those names must not appear there at all.
- **S11.4 — leniency changes no verdict** (`A3`, `S8.4`). For each of
  N1-N5, a strictly-conforming reply and its loosened twin compile to the
  SAME canonical artifact, byte-for-byte. RED if any pair diverges.

## §12 The experiment recipe — S12 (`R9`, `R19`, `M10`, Amendment 1 C+D)

The deliverable is an INSTRUMENT, not a conclusion. The record already shows
one model reversing the form effect (FEASIBILITY §6.1), so the right form is
per-model and must stay configuration.

**S12.0 Sequence, per the operator's own words (`R19`):** history
injections first, THEN the artifact, then measure. Each is its own measured
step; step 2 does not start until step 1's measurement is committed.

**S12.1 STEP 1 — hold the form, vary the brief.** Fix the form at
`conjecturer.turn.v6`. Vary ONE plugin parameter per arm — e.g.
`dr.history.v1.include_refuted`, or `dr.neighbourhood.n`, or a `.tmpl`
formatting variant of the same content. Pre-register before any call, on
the shape of `experiments/2026-08-28-diversity-generation/PREREG.md`.

**S12.2 STEP 2 — hold the brief, vary the form.** Fix the winning brief.
Vary the form across `S8.2`'s three registered ids, and across the
role-prompt templates.

**S12.3 The measures**, all committed instruments, none invented here:

| measure | instrument |
|---|---|
| admission rate, per contract and per endpoint | `census_conjecturer_failures.py` (this directory), re-run over the new roots |
| M1 — distinct-idea count per cell | `experiments/2026-08-28-diversity-generation/analyse.py` |
| M2 — mean pairwise embedding distance | same |
| M3 — yield per cell | same |
| criticism outcomes | the run's own typed record: warrants, attack edges, status labels |

**S12.4 Blind judging is STRUCTURAL, not prompt-level.** Any judged
comparison renders with provenance fields OMITTED ENTIRELY — not blanked.
`docs/RESEARCH_JUDGE_BLINDING_2026-08-22.md` measured that a present-but-
blank slot draws more attention than a filled one, and CLAUDE.md's amended
judge law states the finding: label/provenance exposure carries the bias,
and no prompt-level fix substitutes. The arm's `layout_id` and `form_id` are
provenance for this purpose.

**S12.5 The binding rule, carried from the diversity PREREG:** no
self-reported number the model writes may enter any metric, rank, filter or
ordering. Arms are compared on the instruments above and on nothing else.

**S12.6 Tokens are cheap; the agent is not** (operator law, 2026-08-08).
These are LIVE RUNS, not offline synthesis. Every launch obeys the ladder
rules — green `cycle_soak.py` on the launch config first, detached launch,
snapshot loop armed (CLAUDE.md, "Live runs").

## §13 Frozen surfaces — the forecast

**This tranche's build forecast is: NO CONTACT.** Measured, not asserted:
`tools/blast_radius.py` over road A's targets returns
`"frozen_surface_verdict": "CLEAR"`, with `frozen_surface_contacts: []`,
`frozen_adjacent_contacts: []`, `qualification_digest: []` and
`wheel_smoke_pins: []` (`blast_road_a.json`, quoted in FEASIBILITY §6.3).

Held by three decisions, each of which an executor could accidentally
reverse:

1. **Layout and form selection go by argument/env, never `Config`, never the
   manifest** (`S9.4`, `S10.2`). Reversing this moves every qualification
   subject digest — measured on four manifests, FEASIBILITY §6.2.
2. **No new contract id** (`S8.2`, §0). Adding one contacts three surfaces.
3. **No new `verify_root` check** (`S7.3`). Adding one contacts surface 3.

**If a build step finds it cannot hold one of these, that is a STOP**, and
the grant is requested in that step's own document BEFORE code, with
`blast_radius.py`'s own contact rows pasted and disposed one by one — the
discipline every granted contact since 2026-08-21 followed.

**The wheel smokes** (`scripts/wheel_smoke.py`,
`scripts/wheel_operational_smoke.py`) pin the public surface and NO gate
runs them. This tranche adds no console entry point and no MCP tool, so it
owes them nothing — but a step that adds a CLI surface re-runs and re-pins
them in the SAME commit.

## §14 The seam this spec names and does not design — S13

`M5`: the critic seat follows on the same interface. `render_crit_pack`
(`packs.py:1242-1476`) has the same shape — 13 section slots + the question,
the same `_pack_section` / `_allocate_sections` / `_menu_sections(…, 4)` /
`_question_section` machinery. The section-plugin protocol (`S1`) is
therefore designed to be seat-agnostic: `SectionRequestV1` carries no
conjecturer-specific field, and the registry is keyed by plugin id, not by
seat. **This spec designs nothing for the critic and ships nothing for it.**

**Map obligations** (`REQUEST.md` §4, `PARKED.md` P3). Moving in the SAME
commit as the code, per `docs/map/SCHEMA.md`:

- `DR-CON-packs-and-token-economy` — the section table and the plugin
  indirection.
- `DR-INV-render-layout` — a sibling row: layout policy governs
  ARRANGEMENT, the pack layout governs COMPOSITION.
- A NEW `INV-conj-section-plugins.md` carrying §9's three layers, `S11`'s
  four checks, and a `REC-add-a-section-plugin.md` recipe.
- `SEAM-packs-and-token-economy-x-rules.md` — currently undocumented, and
  it is the seam the nine caller-computed sections (`A6`) sit on.

Every load-bearing claim carries a `check:` at column 0 that can FAIL, and
`python tools/docs_verify.py` runs in FULL mode before any commit touching
`src/`.

## §15 Budget and stop conditions

**Diff budget:** ~900 lines of `src/` across the build, dominated by the
twenty seeded plugins, which are mechanical extractions of existing text.
`tools/diff_budget.py` is the instrument. Exceeding it is a stop
(`dr-change-orchestrator` §3).

**Stop conditions, in addition to the standing ones:**

- `S10.4` (byte-identical default) cannot be made to pass.
- Any of §13's three decisions cannot be held.
- A normalisation in `S8.4` turns out to change a verdict (`S11.4` RED).
- The operator's answer to Q4 narrows `A3` below what `S8.4` proposes.

## §16 Requirement trace

| R | operator's words (source) | where satisfied | acceptance check |
|---|---|---|---|
| R1 | brief becomes a pluggable interface | S1, S2, S10 | S11.1, S11.2 |
| R2 | evidence gets a plugin | S1.5 (`dr.evidence.frozen`, `dr.evidence.citable`) | S10.4 golden |
| R3 | history gets a plugin | S1.5, S1.6 (`dr.history.v1`) | S10.4 golden |
| R4 | neighbouring conjecturers get a plugin | S1.5 (`dr.neighbourhood`, `.live`) | S10.4 golden |
| R5 | the plugin is generic | S1.1 — one protocol, all sections | S11.2 |
| R6 | information increased or shrunk at will | S1.1 `parameters_model`; S10.1 per-entry knobs | S12.1 varies one and measures |
| R7 | it shouldn't be typed | S1.3 — `text` is free text the harness never parses (A4 bounds it to the OUTPUT) | S11.3 |
| R8 | formatting can be done with the plugin | S1.3 (plugin formats), S4 (template layer, no code) | S11.2 |
| R9 | test freely how conjecturers respond to input format | S4, S12 | S12.1 runs and measures |
| R10 | the form is adaptable to capability / desired behaviour | S8.2, S9 | S11.4, S12.2 |
| R11 | configurable with defaults | S9 layers, S10.2 selection, S10.3 default | S10.4 |
| R12 | feasibility first, then a spec | FEASIBILITY.md, then this | operator approval |
| R13 | episodes not decided | S1.7 — a registered, unimplemented slot and nothing more | — |
| R14 | input interface materially changes outputs | FEASIBILITY §6.1 (measured, 51.5% vs 92.7%) | premise, not a build item |
| R15 | form-filling is a weak point the machine doesn't accommodate | S8, S9, S12 | S12.2 |
| R16 | outputs need strict minimum standards | S8.3 — the list that never varies | S11.3, S11.4 |
| R17 | adapt accepted outputs so they compile | S8.4 (N1-N5), bounded by A3 | S11.4 |
| R18 | LLMs respond differently to different inputs, consistently | FEASIBILITY §6.1 per-endpoint spread (48.1% / 32.7% / 7.9%) | premise; Q5 still open |
| R19 | history first, then the artifact, then measure | S12.0, S12.1, S12.2 | step ordering in CHECKLIST.md |

**Monitor's readings** `M1`→S1.4+S7, `M2`→S10.3+S10.4, `M3`→S8+A2,
`M4`→S3+§9, `M5`→S13, `M6`→S1.7, `M7`→S8.3+S8.4, `M8`→FEASIBILITY §6.1,
`M9`→S11.3, `M10`→S12.0.

---

**Status: STEP 2 complete.** `CHECKLIST.md` next. Then STOP for the
operator's approval — no implementation in this window.

---

## §17 Amendment 2 — the seat is a shell

Authority: `REQUEST.md` §1b, the operator's words of 2026-09-03, ledgered the
same day as the standing law "A seat is a shell: its input and its output
define it" (CLAUDE.md; commits `8dc11da15`, `e91f4fcc3`).

**This section REPLACES §14's "This spec designs nothing for the critic and
ships nothing for it." It changes nothing else in this document.** Every
decision in §0-§16 stands, including the road (A + template layer + C1), the
three frozen-surface decisions of §13, the assumptions of §1, and the
leniency boundary of §8.4. What changes is the SCOPE: both seats, and a
registered pairing that names which brief goes with which form.

### §17.0 Why the amendment is small in code and large in meaning

§14 already designed the section-plugin protocol to be seat-agnostic —
`SectionRequestV1` carries no conjecturer-specific field and the registry is
keyed by plugin id rather than by seat. The amendment collects on that: the
critic's renderer has the same shape as the conjecturer's (thirteen section
slots plus the menus and the question, the same `_pack_section` /
`_allocate_sections` / `_menu_sections(…, 4)` / `_question_section`
machinery), so extending the walk to it adds a second layout and a second
seeded plugin set rather than a second mechanism.

### §17.1 (a) Seat-agnostic names

Every name that would have carried "conj" carries "seat" instead.

| §0-§16 name | §17 name |
|---|---|
| `ConjecturerSectionPluginV1` | `SeatSectionPluginV1` |
| `llm/conj_sections.py` | `llm/seat_sections.py` |
| `ConjecturerPackLayoutV1` | `SeatPackLayoutV1` |
| `SECTION_PLUGIN_REGISTRY` | unchanged — it never carried a seat name |
| `conj-pack.legacy-v0` | `seat-pack.conjecturer.legacy-v0` |
| — | `seat-pack.critic.legacy-v0` |
| `DEEPREASON_CONJ_PACK_LAYOUT` | `DEEPREASON_SEAT_PACK_LAYOUT` |

`SectionRequestV1`, `SectionRenderV1` and `SectionReceiptV1` carry NO seat
name and no seat field — a receipt that named its seat would be the evidence
side learning a generation-side fact, which `S11.3` (widened at §17.6) makes
a failing check.

**Decision (1) of §13 still binds, and the environment form carries the seat
because one process renders both.** Selection is argument → environment →
default, and the environment variable is a per-seat assignment list:

    DEEPREASON_SEAT_PACK_LAYOUT=conjecturer=<layout_id>,critic=<layout_id>

Never a `Config` field, never a manifest field. The measured reason is
unchanged (FEASIBILITY §6.2: the carried variant moves every qualification
subject digest; the off-manifest variant moves none), and it is reinforced by
what the transport tranche measured — a `Config` field holding a pydantic
model cannot round-trip through the manifest's carriage notice at all.
A malformed assignment is a typed refusal at resolution naming the offending
term, never a silent fallback to the default.

### §17.2 (b) `render_crit_pack` walks a layout

`packs.py:1242` becomes the same loop `render_conj_pack` becomes, under the
same `A6` rule: the caller-computed contexts arrive in
`SectionRequestV1.supplied` and their plugins FORMAT them; nothing moves out
of `rules/crit.py`.

The critic's four caller-supplied contexts are `premise_invitation`,
`citable_evidence_context`, `frame_slice_context`, `frame_crisis_context`,
plus `reference_menus` — a subset of the conjecturer's nine, so `supplied`
needs no new key.

Its thirteen sections become seeded `dr.*` plugins. **A plugin id is SHARED
when the section's text is the same section, and separate when it is not** —
priority, drop/compress flags and caps live in the LAYOUT ENTRY, so two seats
may share one plugin at different priorities without either bending.

| critic section | plugin | shared with the conjecturer? |
|---|---|---|
| `problem-context` | `dr.problem.context` | no — the conjecturer's `problem` is the problem statement, this is a multi-problem context block |
| `target-commitments` | `dr.target.commitments` | no |
| `machine-evaluation-boundary` | `dr.machine-evaluation-boundary` | no |
| `target` | `dr.target` | no |
| `target-support-chain` | `dr.target.support-chain` | no |
| `target-support-content` | `dr.target.support-content` | no |
| `standing-attacks` | `dr.standing-attacks` | no |
| `frame-crisis` | `dr.frame.crisis` | **YES** — both render the caller's context verbatim |
| `frame-slice` | `dr.frame.slice` | **YES** — same |
| `citable-evidence-blocks` | `dr.evidence.citable` | **YES**, with a parameter: the critic's entry sets `requires_invitation=true` (default `false`), because the critic renders the legend only alongside the premise invitation it serves |
| `premise-invitation` | `dr.premise-invitation` | no |
| `counterexample-recourse` | `dr.counterexample-recourse` | no |
| `output-contract` | `dr.output-contract.critic` | no — a different directive; the conjecturer's is `dr.output-contract.conjecturer` |

The menu sections and the restated question are rendered by the registry and
the layout exactly as for the conjecturer (`S5`, and the question's
`_question_section` rule). `standing-attacks` and `premise-invitation` are
already in `DISCLOSED_ON_DROP`, so `S6`'s refusal — an evidence-family plugin
registered outside that set is a typed refusal at layout construction —
covers the critic's side unchanged.

### §17.3 (c) `S10.4` applies to BOTH seats

The byte-identical-default acceptance test is now two goldens, each captured
from the build window's BASE COMMIT before any refactor exists, with a
minimal and a maximal case per seat — four fixture files at least.

**If EITHER golden cannot pass, the refactor is wrong and the tranche STOPS.
A fixture is never updated to make a test pass** (`S10.4`, unchanged).

### §17.4 (d) The seat-kind registry

    class SeatShellV1(BaseModel):          # frozen, extra="forbid"
        shell_id: str
        seat_id: str                       # the dispatch role: "conjecturer",
                                           # "argumentative_critic"
        layout_id: str
        form_id: str
        role_prompt_template_id: str

Registered and versioned like the section-plugin registry and the layout
registry (§9's VERSIONED layer): `register_seat_shell`, `resolve_seat_shell`,
a shell id names ONE pairing or two runs citing it do not mean the same
thing. Two shells ship, reproducing today's behaviour exactly:

| shell_id | seat_id | layout_id | form_id |
|---|---|---|---|
| `seat.conjecturer.legacy-v0` | `conjecturer` | `seat-pack.conjecturer.legacy-v0` | `conjecturer.turn.v6` |
| `seat.critic.legacy-v0` | `argumentative_critic` | `seat-pack.critic.legacy-v0` | `argumentative_critic.compact.v1` |

**R22/R23 are the reason this registry exists.** A second conjecturer kind or
a second criticism kind is a THIRD registered pairing, added by registering
it; neither is built here (§17.7).

`SeatShellV1` carries NO score, rank, weight, confidence, priority or
authority field — the standard the criticism-source socket set, owed here
too, and `S11.3` (widened) is the check that goes red when one is added.

### §17.5 (e) The test that makes `R20` checkable

`R20` is an obligation on the DELIVERABLE, so it gets a demonstration and not
a shape argument. Offline, against the deterministic stub, at the critic's
dispatch site in `rules/crit.py`: bind the CONJECTURER shell where the
critic's is bound, and assert four things.

1. the call renders under the bound shell's layout, not the critic's;
2. the section-plan object (`S7.1`) records the shell id that actually ran;
3. the wire reply is parsed by the FIXED parse half of whichever form the
   shell names (`A2`, `S8.3`);
4. `expected_target` and the alias binding are UNCHANGED — the critic's
   target-binding is authority-side, and swapping a shell may not move it.

**What the test does NOT claim, stated in its own docstring:** that a
conjecturer shell in a critic's seat produces useful criticism. It proves the
SHELL IS SWAPPABLE. Whether the swap is a good idea is an experiment
(`S12`), and this tranche's answer to it is "not measured".

### §17.6 (f) `S11.3` widens to the law's own "enforced" clause

RED if `seat_id`, `shell_id`, `layout_id`, `form_id` or any
`SectionReceiptV1` field is read anywhere in `scheduler/`, `adjudication/` or
`rules/` admission, rank, immunity, refutation or acceptance paths.
Mutation-proven by planting one such read and watching it go red — a
reachability assertion that has never been shown to fail is not a check
(`docs_verify --audit`'s own standard).

This is the law's SCOPE BOUNDARY made checkable: the shell is about how
content is GENERATED, and what counts as evidence does not vary with it.

### §17.7 (g) Out of scope, parked with prompts

- `render_batch_crit_pack` (`packs.py:972`) — a third renderer with its own
  batching contract.
- The judge, defender, variator and synthesizer seats.
- Any SECOND conjecturer kind or SECOND criticism kind (`R22`, `R23`).
- Everything §0 already excluded, road C2 above all.

Each gets a ready-to-send prompt in `PARKED.md`.

### §17.8 (h) Budget and the frozen-surface forecast

**Diff budget amended: ~1500 lines of `src/`** (was ~900), the increase being
the critic's thirteen seeded plugins, its layout, the shell registry and the
seat-agnostic renames. `tools/diff_budget.py` is the instrument; exceeding it
is a stop.

**Frozen-surface forecast: still NO CONTACT.** Measured over the amended
target list — `llm/packs.py`, `packs/ir.py`, `packs/allocate.py`,
`llm/layout.py`, `llm/roles.py`, `llm/wire.py`, `rules/conj.py`,
`rules/crit.py`, `model_profiles/registry.py`, with symbols
`render_conj_pack`, `render_crit_pack`, `_pack_section`,
`_allocate_sections`, `wire_contract_for`, `validate_value` — the result is
pasted at §17.9. The three decisions of §13 are unchanged and still hold the
verdict: selection by argument/env only, no new contract id, no new
`verify_root` check.

The critic's form selection is `C1` on the critic's side: among ids ALREADY
registered — `argumentative_critic.compact.v1` (what `wire_contract_for`
assigns the `argumentative_critic` role today, `wire.py:2638`) and
`critic.atomic-target.v1` (`ATOMIC_CRITIC_CONTRACT_V1`, `wire.py:2677`).
**No new contract id** (§13 decision 2).

### §17.9 `blast_radius.py` over the amended target list

Measured on the build window's base `7d7996302`, over the §17.8 target
list. **The verdict depends on ONE declared symbol, and that dependence is
itself the finding.**

**Run 1 — the full amended list, INCLUDING the symbol `wire_contract_for`:**

    "result_type": "BLAST_RADIUS_RESULT_V1",
    "frozen_surface_verdict": "CONTACT",
    "frozen_adjacent_contacts": [],
    "frozen_surface_contacts": [
      {"surface": "replay-validation record formats (invariants.py)",
       "tier": "SYMBOL_INDIRECT", "target": "wire_contract_for",
       "detail": "'wire_contract_for' referenced in
                  src/deepreason/invariants.py
                  (grep-based; not proof of semantic contact)"},
      {"surface": "manifest schemas and validators (run_manifest.py)",
       "tier": "SYMBOL_INDIRECT", "target": "wire_contract_for",
       "detail": "'wire_contract_for' referenced in
                  src/deepreason/run_manifest.py
                  (grep-based; not proof of semantic contact)"}
    ]

**Run 2 — the same list with `wire_contract_for` NOT declared:**

    "frozen_surface_verdict": "CLEAR",
    "frozen_surface_contacts": [], "frozen_adjacent_contacts": [],
    "disclosure_summary": "This change touches none of the five frozen
      surfaces. 9 test file(s) and 14 map document(s) assert on the touched
      targets today."

**Disposal, one row at a time, and NEITHER is a comment mention.** The gate
labels its own method "grep-based; not proof of semantic contact", so both
rows were opened and read rather than dismissed. Both are REAL call sites:

- `invariants.py:1233` calls `wire_contract_for("conjecturer", output_model,
  transport_profile, AliasTable())` and takes `.contract_id` from the result
  to build the AUTHORIZED CONTRACT ID SET a replay validates a conjecturer
  call against. If that function returned a different id for an unchanged
  input, committed roots would change replay verdict. **That is frozen
  surface 3, and it is a genuine dependency, not a grep artefact.**
- `run_manifest.py:2074` calls it for the defender, judge and variator seats
  and folds each `.contract_id` into the manifest's behavioral assignments,
  which `production_contract_pairs` projects into the qualification subject.
  **That is frozen surfaces 4 and 5, and it is also genuine.**

**The binding constraint this produces — new, and stronger than the spec's
forecast.** `wire_contract_for`'s existing mapping is FROZEN BY THESE TWO
CALLERS: for every `(role, output_model, profile, aliases, expected_target)`
tuple that resolves today, it must keep returning the same `contract_id`
after this tranche.

Form selection is therefore implemented at the DISPATCH SITE — the seat
shell names a `form_id`, and `rules/conj.py` / `rules/crit.py` choose which
already-registered contract to ask for — and NEVER by changing what
`wire_contract_for` returns for an input it already handles. That keeps the
build on run 2's CLEAR verdict, and it is the same shape as §13 decision 1
(selection by argument/env rather than by moving a value that is folded into
a digest).

Checkable, not promised: a new step pins the whole
`(role, output_model, profile) -> contract_id` table against the base
commit's values, and steps 19 and 26 already assert that
`src/deepreason/invariants.py`, `src/deepreason/verification/report.py`,
`src/deepreason/run_manifest.py`, `src/deepreason/qualification.py` and
`src/deepreason/cli/doctor.py` appear nowhere in this tranche's diff.

**If a build step finds it cannot hold that constraint, that is a STOP** —
the grant is requested in that step's own document, before code, with run 1's
rows pasted and disposed one by one (§13's own rule, applied to itself).
