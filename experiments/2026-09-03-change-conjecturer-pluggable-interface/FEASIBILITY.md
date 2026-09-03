# FEASIBILITY — how the conjecturer's brief and form could become pluggable

Tranche: `experiments/2026-09-03-change-conjecturer-pluggable-interface/`
Phase: STEP 1 of the design window (`R12`: "figuring out how it might be
achieved is the first step").
Authority: `REQUEST.md` §1 (the operator's verbatim words) and §1a
(Amendment 1). Requirement numbers below are that file's.
Base: `main` at `2d84a86cd`.

**Nothing here is implemented.** This document maps what exists, measures
what fails, prices three roads with the gate's own numbers, and recommends
one. `SPEC.md` follows; `CHECKLIST.md` after that.

Map ids in force (resolved in `REQUEST.md` §4, read in that order):
`DR-INV-frozen-surfaces`, `DR-INV-render-layout`, `DR-SEAM-llm-x-rules`,
`DR-SUB-llm`, `DR-CON-conjecture-source`, `DR-CON-packs-and-token-economy`,
`DR-INV-reference-menu`, `DR-CON-model-profiles`, `DR-CON-seats`,
`DR-CON-conjecture-kinds`, `DR-SUB-manifest`, `DR-SUB-verification`.

---

## 1. How the brief is assembled TODAY

`src/deepreason/llm/packs.py::render_conj_pack` (lines 567-969) builds a
list of `PackSection` values and hands them to `_allocate_sections`
(414-500), which runs `packs/allocate.py::allocate_pack` to a fixed point.
A section is a frozen pydantic record — `packs/ir.py::PackSection`
(6-23) — carrying `id`, `text_ref`, `priority`, `min_tokens`,
`max_tokens`, `droppable`, `compressible`, `cache_group`,
`provenance_refs`. `_pack_section` (320-345) pins `max_tokens` to the
source size, so a section never renders more than it has.

**Every section slot, in construction order.** "Cap" is the `min_tokens`
floor a droppable/compressible section is admitted on; a blank cap means
the section is retained whole.

| # | id | line | source | prio | droppable | compressible | cap |
|---|---|---|---|---|---|---|---|
| 1 | `problem` | 604 | `problem.id` + `problem.description` | 1 | no | no | — |
| 2 | `criteria` | 618 | `problem.criteria` → `commitments[cid].eval` | 2 | no | no | — |
| 3 | `open-criticisms` | 645 | `open_criticism_context` (caller) | 2 | no | no | — |
| 4 | `mandatory-interface` | 658 | `_lineage_foundation` (162-200) | 3 | no | no | — |
| 5 | `active-properties` | 670 | `_active_property_claims` (133-161) | 4 | yes | yes | 24 |
| 6 | `school-stance` | 700 | `school["stance_text"]` | 5 | no | yes | 24 |
| 7 | `experimental-generation-context` | 712 | `generation_context` (caller) | 6 | no | no | — |
| 8 | `scratch-advisory-context` | 726 | `RenderedScratchPackV1.text` | 7 | no | no | — |
| 9 | `frozen-evidence-context` | 736 | `frozen_evidence_context` (caller) | 4 | yes | yes | 64 |
| 10 | `citable-evidence-blocks` | 747 | `citable_evidence_context` (caller) | 4 | yes | yes | 64 |
| 11 | `capability-result-context` | 758 | `capability_result_context` (caller) | 3 | no | no | — |
| 12 | `frame-crisis` | 781 | `frame_crisis_context` (caller) | 4 | no | no | — |
| 13 | `frame-slice` | 794 | `frame_slice_context` (caller) | 4 | no | yes | 96 |
| 14 | `neighbourhood` | 817 | accepted artifacts, `_distilled` (278-295) | 8 | yes | yes | 32 |
| 15 | `live-neighbourhood` | 835 | `accepted[-layout.live_verbatim_n:]`, whole | 12 | yes | yes | 32 |
| 16 | `superseded-conjectures` | 868 | REFUTED artifacts, `_distilled` | 8 | yes | yes | 24 |
| 17 | `crossover` | 891 | `school["crossover"]`, `_distilled` | 9 | yes | yes | 24 |
| 18 | `complement-directive` | 903 | literal (§11.4 stagnation) | 10 | no | no | — |
| 19 | `diversity-specifications` | 914 | `specs` (llm/specs.py) | 11 | no | no | — |
| 20 | `output-contract` | 949 | the DIRECTIVE literal, 936-948 | 12 | no | no | — |
| + | `<menu>.*` | 961 | `_menu_sections(reference_menus, 4)` (382-413) | 4 | no | no | — |
| + | `context-withheld` | 457 | `_withheld_notice` (373-380) | 99 | no | no | — |
| + | `question` | 964 | `problem` restated, `_question_section` (296-317) | 100 | no | no | — |

That is `DR-CON-packs-and-token-economy`'s "20 section slots + the
question", re-derived rather than quoted.

**The allocator.** `_allocate_sections` (414-500) is not a single pass. It
allocates, and if any section in `DISCLOSED_ON_DROP` (352-360 —
`citable-evidence-blocks`, `frozen-evidence-context`, `premise-invitation`,
`standing-attacks`) was cut, it re-allocates with a mandatory
`context-withheld` notice naming the cut. It runs to a fixed point bounded
by `len(sections) + 1`; convergence is MEASURED (at most three passes
across 115 budgets), not proved, because the dropped set is not monotone in
the remaining budget. The notice is ABSENT when nothing disclosed is cut —
an always-present "withheld: none" line was rejected on the blinding
research's own finding that an empty slot draws more attention than a
filled one.

**The layout policy.** `llm/layout.py::RenderLayoutPolicyV1` is resolved
PER CALL (`render_conj_pack:600`, `layout or resolve_layout_policy()`), by
argument then `DEEPREASON_RENDER_LAYOUT_POLICY` then default. Two
arrangements ship: `LEGACY_LAYOUT_POLICY` and `ROBUST_LAYOUT_POLICY`. It
governs `question_last`, `live_verbatim_n`, `distil_carry_forward`,
`distilled_head_chars`, `superseded_summary_n`, `retrieval_note`,
`merge_head_label_blocks`, `instruction_ceiling`.
`register_layout_policy` adds an arrangement with no consumer edit.

**This is the precedent that decides this tranche.** `DR-INV-render-layout`
states, and pins with a check, why it is NOT a `Config` field: "a layout
knob on `Config` would move the subject digest of every qualification
bundle in the tree, or would need a companion pop inside `run_manifest.py`
— a frozen surface. Selection by id, from an argument or the environment,
reaches neither." Measured confirmation is in §6.2 below.

**Presentation profiles.** `llm/profiles.py::ModelProfile` is a
three-valued `StrEnum` (`COMPACT`, `STANDARD`, `FRONTIER`) with a frozen
`ProfileSpec` each (`pack_tokens_min/max`, `vs_k`, `direct_contracts`,
`batching`, `examples`, …). `llm/roles.py::render_role_prompt` (376-412)
wraps the pack: for non-compact it is `TEMPLATES[role].format(schema=…,
pack=…)` (roles.py:27); for compact it assembles directive + schema +
aliases + one syntax example + `INPUT:`, joined per
`layout.merge_head_label_blocks`. **The role templates are literals in a
module-level dict keyed by role** — formatting that today requires a source
edit to change.

## 2. The conditional sections built OUTSIDE the renderer

`rules/conj.py::conj` computes six of the twenty slots before calling the
renderer, and appends three more AFTER allocation. This split matters: a
plugin interface that only reaches inside `render_conj_pack` would leave
nine slots un-pluggable.

| what | where | how it reaches the pack |
|---|---|---|
| frozen evidence (dossier) | `conj.py:1313-1393` — `pack_dossier` + `render_dossier_pack`, gated on `inquiry_capability_policy.attached_evidence.enabled`, cumulative across amendment epochs (`dossier_union`) | `frozen_evidence_context=` |
| citable legend | `conj.py:1394-1414` — `citable_legend(_union_blocks(bound_dossiers) + consumed_research_blocks(harness))`; deliberately NOT gated on `bound_dossier`, because gating it there left every derived problem unable to name a resolvable block (P4, R62) | `citable_evidence_context=` |
| frame slice / frame crisis | `conj.py:1415-1421` — `render_frame_slice_context`, `render_frame_crisis_context` | two arguments, exact vs compressible |
| pre-allocation menus | `conj.py:1422-1437` — `menu_renders_for("conjecturer.turn.v6", …, handle_kinds=("citable_block",))`, v6 only | `reference_menus=` |
| simulation follow-up | `conj.py:1448` — `capability_result_context=v6_capability_result_context` | argument |
| scratch context plan | `conj.py:1450-1455` — `conjecture_context_plan.rendered_context` | argument |

**Appended AFTER allocation**, each re-wrapping in `AllocatedPack` so the
adapter does not re-clip a pack already budgeted section by section:

| what | where |
|---|---|
| the v6 scratch render substituted in place | `conj.py:1466-1489` (`pack.replace(canonical, rendered, 1)`, with a "must contain canonical scratch context once" assertion) |
| SEALED SIMULATION INPUTS | `conj.py:1493-1511` |
| `V6_SCRATCH_WORKSHOP_PROMPT` | `conj.py:1512-1513` |
| post-allocation menus (artifact aliases, scratch handles) | `conj.py:1522-1544` |

**The worked example of "append a section" is `generation_context`**
(`render_conj_pack:578`, section 7 at line 712). A caller passes a string;
the renderer wraps it with a fixed header — "GENERATION CONTEXT (attention
only; truth, admission, and verifier standards are unchanged)" — and gives
it priority 6, non-droppable, non-compressible. It is the closest thing in
the tree to what R1-R5 ask for, and it shows both the shape and the limit:
ONE anonymous slot, one hardcoded header, one hardcoded priority, and
`conj.py:818` refuses it on the active v6 path ("active Conj requires typed
context; raw generation_context is not permitted"). The instruction's
"branch-only experimental pool hook" is not on this base: `git branch -a`
shows only `main` and this window's branch, so the worked example is read
from `generation_context` as it stands on `2d84a86cd`.

## 3. The FORM today

**The two halves already exist in code.**
`llm/wire.py::WireContract` (861-1032) is constructed with
`(contract_id, wire_model, canonical_model)` and offers
`model_json_schema()` → `validate_json` → `compile` → `parse_compile`.
`validate_json` produces the WIRE model; `compile` maps it to the CANONICAL
model. That is exactly M3/M7's wire/parse split — **the structure the
operator is asking for is present; what is missing is that it is not
selectable and not open.**

**Which contract a conjecturer call gets.** `wire_contract_for`
(wire.py:2828-2889) is an `if`/`elif` ladder keyed on `(role,
output_model, spec.direct_contracts)`. The canonical model itself is chosen
by a seven-branch conditional in `conj.py:1550-1568`
(`ReasoningConjecturerTurnV6` / `ConjectureTurnV6` / …V5 / …V4 /
`ConjecturerOutput`). **Adding a form means editing both.** The contract
ids in play: `conjecturer.turn.v6`, `conjecturer.turn.v7`,
`conjecturer.atomic-candidate.v1` (wire.py:84-90).

**How the schema reaches the prompt.** `render_role_prompt(role,
schema=…, pack=…, example=…, aliases=…)` (roles.py:376) interpolates the
contract's `model_json_schema()` into the role template. On the split
protocol the SAME schema is re-sent on leg two:
`llm/split.py::extraction_request` (257-266) returns
`_SERIALIZE + schema + _TRACE_HEADER + trace` and nothing else —
"deliberately minimal … the tax a structured-output interface charges
rises steeply with schema weight". A varying wire schema therefore flows
through the extraction leg unchanged; no second form exists to keep in
sync.

**The wire schema is already computed, not written.** `model_json_schema`
(893-897) runs `_strict_schema`, then `_bind_alias_fields` (918-963) which
writes the legal alias set into the schema as an `enum`, then
`_bind_discharge_field` (899-916) which PRUNES the `discharges` property
and its `$def` entirely unless `discharge_enabled` — so a run with nothing
to discharge emits the bytes it emitted before the channel existed. This is
the existing proof that a per-run wire-schema variation can be made
byte-neutral by default.

**Reply handling.** `validate_value` (1002-1027) tolerates an unambiguous
single-element array wrapper, runs `_reject_control_fields` then
`_reject_unknown_fields`, then `_resolve_menu_indices` (a seat's `[2]`
becomes the handle the menu showed at index 2 — it can only replace an
index token with a value the menu already listed), then the wire model.
`DR-SEAM-llm-x-rules` states the guarantee: `reject_model_control_fields`
runs before any contract validator, so nothing the model writes becomes
process authority.

**Qualification binds the contract id (frozen surface 5).**
`qualification.py::qualification_subject_payload` (248-289) dumps the WHOLE
manifest into `manifest_behavior` and folds
`production_contract_pairs(manifest)` (cli/doctor.py:384-445) into
`pair_inventory`. `ProductionContractPairV1.contract_id`
(doctor.py:81-100+) is a closed `Literal` naming every contract the battery
may qualify. `run_manifest.py:2009` puts
`(contracts.conjecturer_turn_contract, "conjecturer", seat)` into the
behavioral assignments those pairs are projected from. So a new conjecturer
form id must be added to at least: the manifest `Literal`
(run_manifest.py:674), the doctor `Literal`, `CONJECTURER_TURN_CONTRACTS`
(run_manifest.py:2188), the doctor probe list (doctor.py:82-83, 886-912),
`workflow/legacy_phase_contracts.py:47`, the conjecture ceiling map
(run_manifest.py:3045), and `verification/report.py:793`, which compares a
recorded conjecture task's contract against `versions
.conjecturer_turn_contract`.

**And qualification refuses a non-preset control plane.**
`qualification_subject_payload:259-263` raises
`QUALIFICATION_POLICY_PRESET_MISMATCH` unless
`manifest.control_plane_policy == engaged_control_plane_policy_v3()`. Since
`conjecturer_turn_contract` lives INSIDE `control_plane_policy
.contract_versions`, selecting a different form through the manifest is not
merely a digest move — on today's code it makes the run unqualifiable
unless the repository-owned preset itself changes. Measured in §6.2.

## 4. The record — what a plugin-based pack would need it to carry

Two families exist and are close to, but not, what M1 needs.

- `workflow-context-pack-plan-v1` (`schema: workflow.context-pack-plan.v1`)
  carries `plan_kind`, `items[]` (alias, namespace, `content_sha256`,
  `object_ref`), `maximum_bytes`, `rendered_bytes`, `work_id`,
  `attempt_index`.
- `workflow-context-exposure-v2` (`workflow.context-exposure-receipt.v2`)
  carries `exposed_items[]`, `context_plan_refs[]`, `prompt_sha256`,
  `work_id`, `attempt_index`.

Census over the committed corpus (`census_output.txt`, the `plan_kind`
table): **1 905 `dossier`, 1 406 `combined`, 177 `scratch`, 45
`citable` — four kinds, none of them per-section.** The family accounts
for CHANNELS (which evidence bytes were exposed), not for SECTIONS (which
part of the brief rendered, from which plugin, at which version, at what
size).

**Finding.** M1's typed receipt ("which plugins, which version, which
parameters, how many bytes each rendered") is NOT already covered by
this family. It is an ADDITIVE need. Two shapes are available and
`SPEC.md` must choose one:

- **(a) a new object kind**, e.g. `workflow.context-section-plan.v1`, one
  per rendered pack, listing every section id with its plugin id, plugin
  version, parameter digest, `rendered_bytes`, and whether it was dropped
  or compressed. New kinds are additive to a root and invisible to every
  reader that does not ask for them.
- **(b) a new `plan_kind` on the existing family**, e.g. `sections`, with
  the section rows in `items[]`. Cheaper, but it overloads a field whose
  four current values all mean "an evidence channel", and
  `items[].namespace`/`alias` do not fit a section row.

(a) is the honest shape; (b) is the smaller diff. Neither touches
`invariants.py` unless a new `verify_root` check is wanted — and none is
NEEDED, because the allocator's existing accounting already binds what is
rendered. Recommendation: (a), with NO new `verify_root` check in the
first tranche (surface 3 stays untouched).

## 5. Citation — can a free-text evidence plugin keep handles citable?

R7 says the plugin is "not typed". Citation is the one place where free
text could silently cost the run a capability, so this section answers it
directly.

**How citation works today.** `citable_legend(...)` builds a legend whose
`shown` blocks become `MenuBinding.citable_block_ids`, which
`menu_renders_for("conjecturer.turn.v6", …)` renders as a menu, and which
`ConjecturerTurnWireContractV6(citable_block_ids=…)` binds into the
schema's enum. The seat then writes a block id (or a menu index, resolved
by `_resolve_menu_indices`).

**The decisive fact is `DR-INV-reference-menu`'s FROZEN clause (b):** *"A
menu changes what the model is SHOWN. It may never change what the harness
ACCEPTS."* Validity is decided by the contract's enum and the §4 checker,
NOT by the rendered prose. `INV-reference-menu` states this as "the exact
analogue of the signal contract's 'allocation touches EFFICIENCY, NEVER
EVIDENCE'".

**Therefore:** a free-text evidence plugin CANNOT break citation validity —
it can only break citation USE, by failing to print handles the schema
still accepts. That is a real cost and it is measurable: the same document
records that 62.6% of field-attributed diagnostics are invented handles,
and P4 measured the other side of it — 0 of 36 sub-problem prompts carried
citable blocks. The allocator already treats this class as special:
`citable-evidence-blocks` is in `DISCLOSED_ON_DROP` precisely because "a
dropped `citable-evidence-blocks` costs the ability to cite at all, and the
pack then looks exactly like a run with no admitted evidence in it".

**Feasible answer, no operator ruling needed:** keep handle rendering
OUTSIDE the plugin's discretion. A section plugin declares which handle
kinds it exposes; the registry renders the menu for those kinds through
`menu_renders_for` as it does now, and the architecture test asserts that a
plugin declaring `citable_block` handles produces a pack in which every
bound `citable_block_ids` entry appears literally. A plugin that wants to
render evidence its own way still may — it just cannot ALSO suppress the
menu. This keeps R7 (plugin output is free text) and citation both.
**Q2 is therefore answered from the framework, not escalated** — see §9.

## 6. What the record says, measured

Two instruments are committed in this directory. Both are read-only.

### 6.1 The failure census — Amendment 1's premise is confirmed

`census_conjecturer_failures.py`, output in `census_output.txt`.
**59 committed roots; 3 308 provider attempts; 1 342 on a conjecturer
contract.** Instruments named per number, per
`dr-ask-the-right-question` §1.

Semantic admission (`workflow-semantic-admission-v1.outcome`):

| contract | admitted | rejected | schema_exhausted | total | admission rate |
|---|---|---|---|---|---|
| `conjecturer.turn.v6` | 454 | 356 | 72 | 882 | **51.5%** |
| `conjecturer.atomic-candidate.v1` | 382 | 23 | 7 | 412 | **92.7%** |
| `conjecturer.turn.v7` | 4 | 0 | 0 | 4 | (n too small) |

Completion tokens (`workflow-provider-attempt-v1.completion_tokens`):
`conjecturer.turn.v6` min 0, median 1 420, **max 32 768** — the cap itself,
i.e. at least one attempt burned the entire completion budget; and a MIN OF
ZERO, the recorded shape of a reasoning model spending the whole cap on
hidden reasoning and emitting nothing. `conjecturer.atomic-candidate.v1`:
min 23, median 675, max 23 678.

**Held to one contract, the endpoint changes the outcome.** From the
terminal table (`workflow-work-terminal-v1.status/reason_code`), on
`conjecturer.turn.v6`: `provider-profile-a3e4b48c…` 101 complete
against 91 rejected and 14 exhausted, out of 210 (**48.1%**);
`provider-profile-bc6ec472…` 3 complete out of 38 (**7.9%**);
`provider-profile-e800ce9c…` 16 complete out of 49 (**32.7%**). Different
inputs, consistently different responses — R18's claim, on this record's
own numbers rather than on the unsupplied study.

**This replicates a finding the repo already holds**, which strengthens it
rather than duplicating it. `experiments/2026-08-26-run-anatomy-program/
W1-form-census/RESULTS.md` §1, over 54 roots, held to glm-5.2 and to the
same seat, route and problem:

| | attempts | valid on arrival |
|---|---|---|
| glm-5.2 on `conjecturer.turn.v6` | 659 | 61.9% |
| glm-5.2 on `conjecturer.atomic-candidate.v1` | 339 | 96.8% |

35 points, and the smaller form runs on the HARDER sample by construction
(it exists only because the composite form already failed), so 35 points is
a lower bound. That same census records the honest counter-case:
`deepseek-v4-flash:0731` REVERSES it (84.6% composite vs 63.6% atomic, on
52 and 22 attempts) — small samples, but enough to forbid calling the
effect universal. It also records **CFR 99.2%**: told in the diagnostic
that omission was legal, seats invented a handle in 255 of 257
opportunities; and **repair costs 21.6% of all provider spend** in the
committed record.

**What this settles for the design.** R15 ("success at filling out forms
appears to be a weak point") is not a suspicion — it is a measured 41-point
spread between two forms carrying the same content on the same seats. R14
("the input interface materially changes outputs") holds on this record.
And the reversal case is why the deliverable must be an EXPERIMENT
INSTRUMENT, not a decision: the right form is per-model, so it has to be
configuration.

**What it does NOT settle.** The census cannot say whether an admitted
candidate is BETTER, only that it was admitted. Quality is
`dr-validate-change`'s blind-judging instruments' question, and the
experiment recipe in `SPEC.md` must carry it.

### 6.2 The digest price of each road — measured, not asserted

`price_form_registry.py`, output in `price_output.txt`. Four committed
manifests (constructive-frontier, poietics, pc2-rematch, pc2-rematch-h3).
Identical verdict on all four:

| road | what it does | qualification subject digest |
|---|---|---|
| A — selection off the manifest (the `DR-INV-render-layout` shape) | argument, then env var, then default | **unchanged — price 0** |
| B — one knob on `Config`, CARRIED into `engine_config_json` | reaches `manifest_behavior` | **MOVES — every home reruns the ~14-min, ~1 160-call battery** |
| B' — one knob on `Config`, unconditionally DROPPED | `_versioned_source_config_data` pops it; the `ENGINE_CONFIG_FIELD_NOT_CARRIED` notice is the exact code `qualification_subject_payload` strips | **unchanged — price 0** |
| C — the form id selected through `control_plane_policy.contract_versions` | v6 → v7 | **REFUSED: `QUALIFICATION_POLICY_PRESET_MISMATCH`** |

Road B' is not a trick: `run_manifest.py:2560-2580` and the comment above
it document the mechanism, and the three F3 knobs (2026-08-26) took exactly
this route with the operator's forecast — "Their presence in the echo would
move every qualification subject digest and every frozen manifest golden;
their absence PRESERVES both." `_CARRIAGE_REQUALIFIES`
(run_manifest.py:2553) is the data table naming the fields whose carriage
DOES cost a battery, which is what keeps that price a configuration concern
rather than a code edit.

Road C's refusal is the sharper finding, and it bears on the operator's
own laws: the conjecturer's form id sits inside a repository-owned frozen
preset, so today a run cannot select a different form AND qualify. Under
the ungated-seats law (2026-08-28) and all-configurations-allowed
(2026-08-12) that is a defect-shaped fact. It is NOT this tranche's to fix
— it goes to `PARKED.md`.

### 6.3 Blast radius, per road

`tools/blast_radius.py`, `BLAST_RADIUS_RESULT_V1`, captured in
`blast_road_{a,b,c}.json`.

**Road A** — targets `llm/packs.py`, `packs/ir.py`, `packs/allocate.py`,
`llm/layout.py`; symbols `render_conj_pack`, `_pack_section`,
`_allocate_sections`:

> `"frozen_surface_verdict": "CLEAR"` — *"This change touches none of the
> five frozen surfaces. 4 test file(s) and 7 map document(s) assert on the
> touched targets today."*

`frozen_surface_contacts: []`, `frozen_adjacent_contacts: []`,
`qualification_digest: []`, `wheel_smoke_pins: []`.

**Road B** — adds `llm/roles.py`, `config.py`, `run_manifest.py`;
symbol `_versioned_source_config_data`:

> `"frozen_surface_verdict": "CONTACT"` — 1 of 5.

| surface | tier | target |
|---|---|---|
| manifest schemas and validators (`run_manifest.py`) | DIRECT | `src/deepreason/run_manifest.py` |
| manifest schemas and validators | SYMBOL_INDIRECT | `_versioned_source_config_data` |

`qualification_digest`: `run_manifest.py` CONFIRMED,
`_versioned_source_config_data` PLAUSIBLE.

**Road C** — adds `llm/wire.py`, `llm/contracts.py`, `qualification.py`,
`cli/doctor.py`, `verification/report.py`; symbols `wire_contract_for`,
`ConjecturerTurnWireContractV6`, `qualification_subject_payload`,
`production_contract_pairs`:

> `"frozen_surface_verdict": "CONTACT"` — **3 of 5**: manifest schemas and
> validators (`run_manifest.py`); qualification subject digests
> (`qualification.py`); replay-validation record formats
> (`invariants.py`).

Seven contact rows: two DIRECT (`run_manifest.py`, `qualification.py`) and
five SYMBOL_INDIRECT (`wire_contract_for` ×2, `qualification_subject_payload`
×2, `production_contract_pairs`). `qualification_digest` names
`qualification.py` and `run_manifest.py` CONFIRMED.

The gate states its own method in each detail string — "grep-based; not
proof of semantic contact" — so the SYMBOL_INDIRECT rows are disclosures to
dispose of one by one in a build tranche's SPEC, not verdicts.

## 7. The three roads

### Road A — section plugins inside the renderer, selection off the manifest

**Shape.** A `ConjecturerSectionPlugin` protocol: given the run's state and
the problem (plus the already-computed conditional contexts of §2), return
`(free text, typed receipt)`. A VERSIONED registry maps plugin id →
implementation, seeded with one plugin per existing slot in §1's table. A
`ConjecturerPackLayoutV1` — the direct sibling of `RenderLayoutPolicyV1` —
names an ordered list of `(plugin_id, priority, droppable, compressible,
min_tokens, params)`. `render_conj_pack` becomes the loop that walks it.
`CONJ_PACK_LAYOUT_LEGACY_V0` reproduces §1's table exactly. Selection:
argument → `DEEPREASON_CONJ_PACK_LAYOUT` → default. Operator plugins load
from the home directory the way `model_profiles` does
(`registry.py:58-100`, `provider_state_dir`).

**Covers:** R1-R9, R11, and R6's knobs (each plugin's `params`).
**Frozen surfaces:** none — `CLEAR`, measured (§6.3).
**Qualification price:** 0, measured on four manifests (§6.2).
**Byte-identical default (M2):** testable, and cheaply — `render_conj_pack`
has 4 test files and 7 map documents asserting on it today, and a golden
over a fixed record pins it.
**What it does not cover:** the FORM (R10, R16, R17) and formatting without
code (R8's fuller reading).

**Risk it carries.** Nine of the twenty slots are computed in `conj.py`
(§2), three of them appended after allocation. Road A must either (i) leave
those as caller-supplied arguments a plugin merely FORMATS, or (ii) move
their computation behind the plugin interface, which drags `rules/conj.py`
— and with it the dossier receipt, the fence seqs and the work-order
plumbing — into the tranche. **(i) is the right first cut**, and the
architecture test can still forbid a NEW section from being added by a
source edit.

### Road B — Road A plus a template layer (formatting without code)

**Shape.** Every plugin exposes a structured value; formatting is a small
template (a restricted, non-executing substitution + iteration language,
NOT Jinja — an operator template must not be able to execute). Templates
live beside plugins in the home directory. A new FORMAT then costs a text
file, not a Python file — which is what R8 and R9 read most naturally as.

**Covers:** everything in A, plus R8 fully and R9 cheaply.
**Frozen surfaces:** none REQUIRED. The `CONTACT` in §6.3's road-B run
comes from `run_manifest.py`, and it is optional: it is needed ONLY if a
knob is put on `Config`. If layout and template selection go the
`DR-INV-render-layout` way (argument/env), `run_manifest.py` is never
opened and road B is `CLEAR` too. If a knob IS wanted on `Config`, the
DROPPED variant (B') prices at 0 with one documented, precedented contact.
**Cost:** a template language is a new surface with its own escaping,
error-reporting and injection questions. It also creates a second way to
express formatting, which competes with the plugin's own.

### Road C — the form as a registered artifact with wire/parse halves

**Shape.** A `ConjecturerFormV1` registry: form id → (wire model, schema
transform, canonical compiler). The PARSE half is fixed — every form
compiles to the SAME canonical turn model, so the artifact entering the
epistemic state does not vary (M3, M7, R16). Per-seat selection, with the
model profile document (`CON-model-profiles`) the natural place to name a
model's preferred form.

**Covers:** R10, R16, R17, and Amendment 1's C and D.
**Frozen surfaces: 3 of 5, measured** — `run_manifest.py`,
`qualification.py`, `invariants.py`/`verification` (§6.3). Plus the closed
`Literal`s enumerated in §3 and, above all, §6.2's refusal: the form id
lives inside the repository-owned control-plane preset, so a run selecting
a different form **cannot qualify today at all**.
**This is a PRICED STOP, per the window instruction.** It cannot proceed
without an explicit operator grant, and the grant must be requested in a
build tranche's SPEC.md BEFORE code, per the documented discipline
(`INV-frozen-surfaces`, every granted contact since 2026-08-21).

**But most of C is reachable without any of that.** Three observations:

1. `conjecturer.atomic-candidate.v1` already exists, is already in every
   `Literal`, is already qualified, and already admits at 92.7% against
   the turn form's 51.5%. The decomposition controller already selects it
   at runtime. **A form-selection experiment can be run TODAY on the two
   already-registered forms**, with zero frozen-surface contact, by making
   the choice configurable rather than only reachable through repair
   exhaustion.
2. `_bind_discharge_field` (wire.py:899-916) is the existing proof that a
   contract's wire schema can vary per run, byte-neutrally by default,
   under a fixed contract id. Wire-form variation that does not change the
   contract ID contacts nothing.
3. R17's leniency (adapting accepted outputs so they compile) is a change
   to `validate_value`'s normalisation, not to the contract id, the
   canonical model, or any admission check — and `validate_value` already
   does exactly one such normalisation (the single-element array wrapper,
   wire.py:1003-1013), with its live justification recorded inline.

So road C splits cleanly into **C1 (no frozen contact)** — selection among
already-registered forms, per-seat wire variation under a fixed id, and
lenient normalisation — and **C2 (3 surfaces, priced stop)** — an open form
registry admitting NEW contract ids.

## 8. Recommendation

**Build A + B(template layer, selection off the manifest) + C1. Park C2
behind an explicit, separately-requested operator grant.**

Reasons, in the order they decide it:

1. **The measured prices are not close, so this is not a fork worth the
   operator's attention** (`dr-ask-the-right-question` §4, the dominance
   test). A and C1 cost ZERO frozen-surface contact and ZERO qualification
   batteries, measured on four manifests. C2 costs three surfaces and a
   preset change. Every reasonable reading of the operator's recorded
   values — smallest correct change, no frozen surface without explicit
   approval — takes the free road first.
2. **C1 alone can answer the operator's actual question.** Amendment 1
   asks how conjecturer behaviour changes with the form. The record already
   holds a 41-point admission gap between two REGISTERED forms. Making that
   choice configurable is the whole experiment, and it is free.
3. **The sequence the operator gave (R19) fits it exactly.** History
   injections first — that is a section plugin, road A. Then change the
   artifact — that is form selection, C1. Then measure. Road A is also the
   prerequisite: you cannot hold the brief constant while varying the form
   until the brief is a thing you can hold constant.
4. **The modularity law's "enforced" clause needs A anyway.** An
   architecture test that goes red when adding a section requires a source
   edit is only writable once sections are registry entries.

**What this defers, said plainly:** an operator-authored plugin proposing a
genuinely NEW form (not a variation of a registered one) needs C2, and C2
needs a grant. That is a real limit of the recommendation, not an
oversight.

## 9. Questions — disposed

Per `dr-ask-the-right-question` §4, each fork is derived first and only
escalated if it survives the dominance test AND changes real stakes.

**DECIDED without asking (dominant under the operator's recorded values):**

- **Q1, the road choice.** Not close: 0 surfaces vs 3, measured (§6.2,
  §6.3). Decided: A + B + C1, C2 parked. Override any time.
- **Q2, may a free-text evidence plugin break citation?** Answered by the
  FRAMEWORK, not the operator: `DR-INV-reference-menu` FROZEN clause (b)
  — a menu changes what is SHOWN, never what is ACCEPTED. Validity cannot
  break; only citation USE can, and §5 gives the mechanism that prevents
  it (handle rendering stays outside plugin discretion, asserted by the
  architecture test). Not escalated.
- **Q3, may the form's PARSE half vary per model?** NO. This is not a
  judgment call: the operator's own R16 ("outputs need strict minimum
  standards") and the standing law that seats change how content is
  GENERATED, never what counts as EVIDENCE, both decide it. Recorded as an
  assumption in SPEC.md, not asked.

**CARRIED to the operator (they survive the test and change real stakes):**

- **Q4 — R17's leniency, how far.** The monitor's reading (M7) admits
  normalisation that yields the SAME typed artifact and refuses anything
  that changes what is admitted. The operator hedged this clause ("maybe
  … worth doing"), and it is the boundary the whole amendment turns on.
  SPEC.md will state M7 as the assumption and name the exact
  normalisations proposed, so confirmation costs a reading rather than a
  design session.
- **Q5 — the study.** Amendment 1's study of why LLMs keep failing was not
  supplied. §6.1 answers the same question from the record, so nothing is
  blocked; the study is still wanted, to be quoted into REQUEST.md §1a as
  operator-supplied evidence and checked against §6.1's numbers.

**A STOP, if the operator wants C2:** an open form registry contacts three
frozen surfaces and requires the repository-owned control-plane preset to
change. Not requested here. If it is wanted, the grant is requested in that
build tranche's SPEC.md before code, with §6.3's contact rows disposed one
by one.

## 10. Parked (findings, not this tranche's work)

Written for their future runner, per the change orchestrator's scope
contract; the ready-to-send prompts are in `PARKED.md`.

- **P1 — the conjecturer's form id is inside a frozen preset, so no run can
  select a different form and still qualify** (§6.2: road C returns
  `QUALIFICATION_POLICY_PRESET_MISMATCH`). This is in tension with the
  ungated-seats law (2026-08-28) and all-configurations-allowed
  (2026-08-12).
- **P2 — `conjecturer.turn.v6` admits at 51.5% while
  `conjecturer.atomic-candidate.v1` admits at 92.7%** on the same seats
  (§6.1), and the smaller form is reachable only through repair
  exhaustion — i.e. the run pays for the expensive failure first, every
  time. 21.6% of all provider spend in the committed record is repair.
- **P3 — the map has no seam document for `llm x model-profiles` or
  `packs-and-token-economy x rules`**, and both are where this work sits
  (`REQUEST.md` §4).

---

**Status: STEP 1 complete.** `SPEC.md` next, tracing every requirement to a
finding here.
