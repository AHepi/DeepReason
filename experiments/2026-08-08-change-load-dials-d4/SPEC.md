# Spec for: the load dials — Rung D4 of the dual-mode conjecture program
Traces: every item cites R/C numbers. Untraceable items are bugs.
DESIGN-AND-STOP: no file under `src/`, `tests/`, or `tools/` changes in
this document or this tranche.

## Map preflight

`DR-SUB-scheduler` (problem selection, cycles, budgets — where every
period/ceiling knob fires), `DR-SUB-manifest` (RunManifest schema and
validators, qualification — **frozen**, surfaces 4 and 5 below),
`DR-SUB-capabilities` (simulation/research lifecycles — surface 1,
the shared proposal/work-order pooling C13/R13 needs), `DR-SUB-scratch`
(the scratchpad's own `AttentionPolicyV1` — the one family the census
already found fully manifest-embedded), `DR-CON-conjecture-kinds` (D2/D3's
delivered design — where the encoder/candidate-checker mechanism this
design must cover actually lives), `DR-CON-seats` (the `"coder"` group,
`property_designer`/`"encoder"`), `DR-CON-scheduler-ranking` (`_select_
problem`'s rank key — the R-g enforcement boundary), `INV-frozen-
surfaces.md` (read first, per house law — surfaces 4 and 5 both
implicated, section below).

## New measurements this tranche (D1's census cited by M1-M14, D2's by
## M15-M30; new ones continue at M31)

### M31 — the census's own knob count is 54, not 43; every row this
### tranche dispositions is the measured 54, not the task's own "43"

```
$ python3 -c "
import re, pathlib
text = pathlib.Path('experiments/2026-08-08-change-pipeline-census-d1/CENSUS.md').read_text()
sec5 = text.split('## 5. Load-knob inventory')[1].split('## 6.')[0]
rows = [l for l in sec5.splitlines() if l.startswith('| \`') or (l.startswith('|') and '---' not in l and 'Knob' not in l and l.count('|') >= 5)]
print('table rows found:', len(rows))
"
table rows found: 54
```
The census's own written summary (`CENSUS.md` line ~1209) states this
explicitly: "26 `Config` knobs ... and 28 manifest-embedded knobs (17
capability-policy fields, 2 `CriticismPolicyV1` fields, 9 scratch
`AttentionPolicyV1` fields)" = 54. Resolves Q1: "43" in this tranche's
own opening instruction does not match any grouping this tranche can
reconstruct from the census's own text; A1 below adopts the census's
own measured 54 and dispositions every one, per R10's own words
("silent omission is a bug").

### M32 — every Config knob's docstring, read in full, to assign a family without guessing from its name

```
$ sed -n '247,530p' src/deepreason/config.py
```
(quoted and classified per-knob in Item 1's disposition table below;
representative finds that overturn a name-based guess: `PROP_PROPOSE_
PERIOD`/`PROP_MAX` (config.py:433-434) gate `property_designer` — the
`"coder"` seat's own role (`seat_bindings.py:36`) — so despite the
"PROP" prefix reading like "proposal", these are CODING-family knobs,
not conjecture-family; `GEN_PROPOSE_PERIOD`/`GEN_MAX` (config.py:424-425)
gate fuzz-input-generator authoring for an EXISTING property oracle
(config.py:419-421: "ask the EXPERIMENTER ... to propose def gen(k)
input generators for a property oracle") — CRITICISM-family (it feeds
`FUZZ_N`'s mechanical fuzz criticism), not conjecture, despite sharing a
call-site pattern with property proposal.)

### M33 — `draft_encoded_commitment` (the D3-landed encoder delegation) and `relatedness_trial` are DORMANT: zero callers in `src/` today

```
$ grep -rn "draft_encoded_commitment\|relatedness_trial" --include=*.py src/deepreason/scheduler src/deepreason/rules/conj.py
(no output — exit 1, zero hits)
```
```
$ sed -n '176,181p' docs/map/SEAM-rules-x-workflow.md
```
> `rules/relatedness.py::relatedness_trial` and
> `rules/encoding.py::draft_encoded_commitment`, are unbracketed for a
> DIFFERENT reason — not deferred, DORMANT: neither has any caller
> anywhere in `src/` yet ... so both are unreachable from every
> scheduler path, v6 or not, until a future tranche wires a call site.

This is R7's own load-bearing finding: the coding-family mechanism D3
landed has **zero live call sites**, therefore **zero existing load
knob** meters it (unlike simulation/research/criticism, which are all
dispatched from live scheduler code paths already carrying period/
ceiling knobs). A mix cannot "cover" a family with no scheduler entry
point by re-weighting an existing knob — there is none to re-weight.
Resolves Q2: Item 1 below proposes a NEW knob NAME and semantics for
this family, explicitly marked "driven when built, currently inert",
and treats WIRING the call site itself as out of scope (Out of scope
section) — that is a scheduler-wiring tranche, not a load-dial design.

### M34 — the ONLY existing coding-family knob (`PROP_PROPOSE_PERIOD`/`PROP_MAX`) gates a path D1 already proved dead

```
$ grep -n "def propose_properties" -A 3 src/deepreason/rules/experiment.py
433:def propose_properties(harness, base, problem, adapter, config) -> list:
```
Reused verbatim from `CENSUS.md` M3 (this tranche re-verifies the same
line numbers hold, unchanged, on this branch):
```
$ grep -n "GROUP_ROLES\s*=\|\"property_designer\"" src/deepreason/seat_bindings.py
36:    "coder": frozenset({"property_designer", "encoder"}),
$ grep -n "def checker_wf_commitment" src/deepreason/oracle.py
776:def checker_wf_commitment(base: Commitment) -> Commitment | None:
```
`propose_properties` early-returns `[]` unless an ACTIVE property-oracle
commitment already exists (M3's circularity: minting the first one
requires an existing one). `PROP_PROPOSE_PERIOD`/`PROP_MAX` therefore
gate a call that, on the live path, always returns early today — the
ONE pre-existing coding-family knob has zero observable effect, same as
the zero knobs for the D3 mechanism. Both facts land in Item 1's coding
disposition, neither silently glossed.

### M35 — conjecture has NO existing period/ceiling knob: it is the scheduler's unconditional per-cycle default, not an optional periodic activity

```
$ sed -n '1806,1834p' src/deepreason/scheduler/scheduler.py
```
`Scheduler.step` proceeds to `scan_spawns` → `_select_problem` →
(discrimination special-case) → conjecture on the selected problem,
every cycle, with no `if cycles % N == 0`-shaped gate anywhere in this
path — unlike `RESEARCH_PERIOD`, `GEN_PROPOSE_PERIOD`, `PROP_PROPOSE_
PERIOD` (all periodic, all gated). None of the 26 Config knobs read in
M32 carries a docstring mentioning conjecture cadence (headers present:
§7 unification, §10 informal domains, §11 capture control, §12
research, §14 budget triage, §9 LLM adapter — no "§X conjecture
cadence" section exists). **Conjecture is structurally the baseline
activity every other family's periodic work competes against, not a
sibling with its own throttle.** This is the measured reason Item 1's
`conjecture` family dial cannot be "driven" the way the other four are;
it needs one new knob (a per-cycle skip probability) with no existing
precedent, priced as its own fork in the decision sheet.

### M36 — the shared capability-state pooling invariant (C13/R13), read at its exact site

```
$ sed -n '225,255p' src/deepreason/capabilities/state.py
```
`self.proposals[proposal.id] = proposal` and `self.work_orders[phase_
record.id] = phase_record` are two dicts shared across EVERY capability
type (`isinstance(phase_record, SimulationWorkOrderV1)` and
`isinstance(phase_record, ResearchWorkOrderV1)` both write into the
same `self.work_orders`). This is CLAUDE.md's own hard-won invariant
("Per-capability budgets meter only their own capability's records —
the shared capability-state maps pool ALL capabilities' proposals and
work orders; always filter by type") made concrete at its exact call
site. Confirms R13: any new `simulation`-family multiplier this design
applies to `maximum_simulation_requests`/`maximum_sources` (research)
MUST be read by code that already filters this shared map by type
(the existing controllers already do — `SimulationController`/
`ResearchController` each read only their own proposal type); the mix
introduces no new pooling risk because it changes CEILING VALUES, never
the counting code that reads them.

### M37 — the manifest-evolution precedent this design's field addition follows, proven live by D3 itself

```
$ sed -n '655,660p' src/deepreason/run_manifest.py
658:        conjecturer_turn_contract: Literal["conjecturer.turn.v6", "conjecturer.turn.v7"] = (
659:            "conjecturer.turn.v6"
660:        )
```
D3's own delivered evidence (`experiments/2026-08-08-change-pipeline-
design-d2/REQUEST.md` R51, quoted in full above under Amendment 3):
"step 28's old-digest-unchanged / new-digest-differs measurement is
mandatory evidence, pasted" — i.e. D3 itself proved, live, that widening
a `Literal` on the v6 manifest with a new option (default unchanged)
leaves every existing manifest's digest byte-identical while a manifest
that actually opts in gets a new one. This design's own `load_mix:
LoadMixPolicyV1 | None = None` field addition is the SAME shape
(a new optional value, default `None`, unused by every existing
manifest) and inherits the same proof obligation for the eventual
EXECUTE rung — named in the Frozen-surface contact forecast below.

### M38 — `qualification_subject_payload` hashes the WHOLE manifest dump — surface 5 is ALSO touched, not surface 4 alone

```
$ sed -n '248,266p' src/deepreason/qualification.py
264:    behavior = manifest.model_dump(mode="json", by_alias=True)
```
`model_dump(mode="json", ...)` serializes EVERY field on the manifest,
including one newly added with `default=None` — Pydantic includes an
explicit `null` for an unset Optional field in `model_dump()`'s output
by default; it does not omit it. Therefore adding `load_mix` to the v6
`RunManifest` class changes `qualification_subject_payload`'s output
for EVERY profile/home, even one that never sets a mix — forcing a
ONE-TIME requalification (~14 min, ~1160 calls per CLAUDE.md's own
cost note) the first time any run compiles against the widened v6
class, regardless of whether that run's own compiled manifest carries
`load_mix: null` (byte-identical mix semantics) or an actual mix. This
directly echoes D2's own M20 finding ("confirming surface 5 contact is
unavoidable for any contract-version bump") but is STRONGER here: it is
unavoidable for ANY new v6 field at all, not only a contract-version
bump. **This overturns the task's own framing ("expect this to be the
design's one frozen-surface question, surface 4") — surface 5 is a
second, independently STOP-worthy contact, reported plainly rather than
silently absorbed to match what was expected.**

### M39 — surfaces 1, 2, 3 confirmed clear: none of the three frozen files enumerates the manifest's fields exhaustively

```
$ grep -n "model_dump\|model_fields" src/deepreason/capabilities/state.py src/deepreason/invariants.py src/deepreason/harness.py
(no output across all three files — exit 1)
```
No frozen-surface-1/2/3 file reads the manifest by dumping or
enumerating its fields; each reads only the specific fields it already
names (e.g. `manifest.criticism_policy`, `manifest.schema_version`).
Adding one new Optional field with no consumer in these three files
changes nothing they compute. Resolves Q4: exactly two surfaces (4 and
5), not one, and not three or five — measured, not assumed.

### M40 — the "engaged" preset is the ONE place today's fixed manifest-embedded values get compiled, and the natural preset-application point

```
$ sed -n '364,407p' src/deepreason/preparation.py
```
`build_preparation_manifest` (the function `deepreason reason` calls to
mint a run's manifest) passes `criticism_policy=engaged_criticism_
policy(...)`, `inquiry_capability_policy=engaged_inquiry_capability_
policy(...)`, `control_plane_policy=engaged_control_plane_policy_v3()`,
`toolchains=(engaged_simulation_toolchain(),)` — every manifest-
embedded family's value is ALREADY a named-function call today, just
with exactly one hardcoded preset ("engaged") and no operator-facing
choice. A load-mix preset multiplies the ARGUMENTS these `engaged_*`
functions already receive; it does not need a new compilation
mechanism, only a new argument threaded through an existing one.

### M41 — the CLI surface: `reason` mints the run (where mint-time freezing must attach), `setup` binds persistent per-seat routing (a different lifecycle)

```
$ sed -n '36,65p' src/deepreason/cli/main.py
$ sed -n '181,187p' src/deepreason/cli/main.py
```
`setup` (`--provider`, `--seat GROUP=PATH`, ...) configures a
reusable, cross-run provider profile / seat-binding file — it mints
nothing. `reason` (`question`, `--cycles`, `--token-budget`, `--dossier`,
`--attach`) is the command that calls `build_preparation_manifest`
(M40) and therefore the command that actually compiles+freezes a
RunManifest per run. The mix flag belongs on `reason` (mint-time),
not `setup` (persistent config) — resolving the "setup/reason flag
shape" framing precisely rather than picking one arbitrarily.

### M42 — the existing `--profile` flag on `config compile` is the closest working precedent for a named-choice, manifest-facing CLI flag

```
$ sed -n '106,109p' src/deepreason/cli/main.py
108:    compile_cmd.add_argument("--profile", choices=("compact", "standard", "frontier"),
109:                             default=None, help="model-facing presentation profile "
```
A `choices=(...)`-constrained `argparse` flag with `default=None`
already exists for a DIFFERENT named-preset axis (sampling
presentation, not load-mix) — this design's `--load-mix` flag follows
the identical `choices=(...)`/`default=None` shape rather than
inventing a new CLI convention.

### M43 — BEHAVIOR_MODES_PREPLAN and ROLE_SEAT_SEPARATION_PLAN S7 both explicitly wait for D4's mix; neither is a captured request today

```
$ head -5 docs/proposals/BEHAVIOR_MODES_PREPLAN.md
Status: PARKED — idea only, not a captured request. No tranche exists.
```
`DUAL_MODE_CONJECTURE_PREPLAN.md`'s own D4 rung text: "surfaced as
named presets (BEHAVIOR_MODES_PREPLAN's modes; S7's packages consume
these later)" — both cited docs are forward pointers, not authority
this tranche must satisfy today. This design borrows their SKETCHED
mode shapes (explore/argument/creative/critical, S7's brainstorm/
prove/referee) as illustrative preset names/values only — the actual
preset table is a decision-sheet fork (F3 below), not a requirement,
since neither source document is itself a captured request.

## Items

S1 (R1): process — no target files this window; the DESIGN-AND-STOP
boundary. accept: `git diff --stat origin/claude/monitor-session-
handover-63ajqv -- src/ tests/ tools/` -> empty.

S2 (R2, R3): setup/preflight/reading already performed this session.
accept: historical (this session's own transcript).

S3 (R4): route dr-capture-request -> dr-spec-change -> STOP. accept:
REQUEST.md committed before this file; this file ends at "Decision
sheet", no `dr-plan-steps` phase begun.

S4 (R5): authority = preplan Rung D4 + R-f + R-g, quoted verbatim in
REQUEST.md; every item below cites the D1/D4 census rows or a new
M-numbered measurement, never an unmeasured claim. accept: `grep -c
"^M3[1-9]\|^M4[0-3]" SPEC.md` -> 13 (M31-M43).

S5 (R6): measurement base = D1 CENSUS.md section 5, re-measured only
where M31-M43 above found the pre-D3/pre-count-check tree insufficient
(the knob count itself, and the coding family D3 added). accept: M31
above pastes the reconciled count; A1 below records the resolution.

S6 (R7): Item 1's coding-family row (M33, M34) covers the D3-landed
mechanism explicitly — driven-when-built, currently inert, wiring out
of scope. accept: Item 1's disposition table has a `coding` row citing
M33/M34.

S7 (R8): Item 1 below — the typed load-mix policy's shape, `share` vs
`priority` semantics derived from M32's own per-knob docstrings (A3
resolves Q3).

S8 (R9): Item 2 below — mint-time freezing into the RunManifest, the
rung-7 placement law, surfaces 4 AND 5 (M37, M38 — Q4 resolved: two
surfaces, not the task's expected one).

S9 (R10): Item 1's disposition table — every one of the 54 rows
(M31) gets `driven` / `independent` / `deprecated-by-this-design` /
`driven-when-built (new knob, currently inert)`, none omitted.

S10 (R11): Item 3 below — named presets as the `reason` CLI surface
(M41, M42), default preset = today's byte-identical behavior (M40's
existing `engaged_*` call sites, multiplier 1.0 = unchanged arguments).

S11 (R12): Item 4 below — the R-g argument (work families vs
conjecture kind) plus its enforcement test, citing `_select_problem`'s
own rank key (already proven kind-blind, CENSUS.md section 4(a)) and
`_standing_recrit_pool`'s existing regression
(`test_R_g_no_scheduling_term_reads_the_candidate_checker_kind`, D3's
own R36 — blast-radius census below).

S12 (R13): Item 5 below — the per-capability budget interaction, citing
M36's exact pooling-map code.

S13 (R14): Frozen-surface contact forecast section — both surfaces
named, neither assumed away.

S14 (R15): Budget section — headline computed from the itemization,
pasted arithmetic, no hand-restated number.

S15 (R16): Decision sheet section, closing this document, every fork
priced with a recommendation.

S16 (R17): commit and push this file (and REQUEST.md, already pushed)
with retry, then STOP.

S17 (R18, dr-explain-to-operator): every operator-facing message this
session worries-first, glosses in intermediaries, one analogy on the
final message. accept: this tranche's own chat transcript.

## Design decisions

### Item 1 (R7, R8, R10): the typed load-mix policy's shape, and the disposition of every one of the 54 knobs

**The record.** One new manifest sub-model:

    class FamilyDialV1(BaseModel):
        model_config = ConfigDict(extra="forbid", frozen=True)
        share: float = Field(default=1.0, gt=0.0, le=4.0)
        priority: float = Field(default=1.0, gt=0.0, le=4.0)

    class LoadMixPolicyV1(BaseModel):
        model_config = ConfigDict(extra="forbid", frozen=True)
        conjecture: FamilyDialV1 = FamilyDialV1()
        criticism: FamilyDialV1 = FamilyDialV1()
        scratchpad: FamilyDialV1 = FamilyDialV1()
        simulation: FamilyDialV1 = FamilyDialV1()
        coding: FamilyDialV1 = FamilyDialV1()

`share` and `priority` are MULTIPLIERS on a family's existing driven
knobs' existing default values — never replacement absolute values.
`1.0` on every dial (the type's own default) reproduces every existing
default exactly; this is what makes "no-mix-specified run is byte-
identical to today" (the preplan's own D4 accept criterion) true by
CONSTRUCTION rather than by a separate code path (A2 below).

**`share` vs `priority` (A3, resolving Q3), derived from M32's own
per-knob text, not assumed:**
- `share` multiplies FRACTION- and CEILING-shaped knobs — a knob whose
  unit is already "how much of a shared pool" (`INTEGRATION_BUDGET_
  SHARE`, `HOLDOUT_SHARE`, `CRIT_DEBT_CEILING`, `ARG_CRIT_PER_CYCLE`,
  every `maximum_*` capability-policy ceiling, `CriticismPolicyV1.
  max_batch_size`). `new_value = round_to_type(default_value *
  dial.share)`, clamped to the field's own existing validator bounds
  (e.g. a `Field(ge=1, le=256)` ceiling clamps after multiplying, never
  raises past its own frozen-manifest bound).
- `priority` multiplies FREQUENCY-shaped knobs — a knob whose unit is
  "cycles between activations" (`RESEARCH_PERIOD`, `GEN_PROPOSE_PERIOD`,
  `PROP_PROPOSE_PERIOD`, `AUDIT_PERIOD`, `coverage_slot_every_n_packs`).
  `new_period = max(1, round(default_period / dial.priority))` — higher
  priority shortens the period (more frequent), matching R-f's own
  words ("which gets priority and by how much") to the one axis that
  already means frequency in this codebase.
- A knob that is neither shape (a size/count with no period or fraction
  meaning, e.g. `NEIGHBOURHOOD_N`, `TRIAL_PARAPHRASE_N`) is assigned to
  whichever of the two reads naturally from its own docstring (below,
  per-row) — never both, and the choice is written down, not implicit.

**Disposition of every one of the 54 knobs (M31), grouped by family.**
"Driven" means the mix's family dial multiplies this knob per the rule
above; "independent" means the mix never touches it (with the specific
reason); "deprecated" means this design proposes removing the knob's
independent existence in favor of the mix (used exactly twice, both
justified below); "driven-when-built" means the design names the future
knob's family now but no live code exists yet to multiply (M33/M34).

| Knob | Family | Disposition | Reason (cites M-number or docstring) |
|---|---|---|---|
| `INTEGRATION_BUDGET_SHARE` | — | independent | governs reflexive-PROBLEM selection share, not a work-family's own load (§7 unification; problem selection is already proven kind-blind, CENSUS §4(a)) |
| `TRIAL_PARAPHRASE_N` | criticism | independent | a trial QUALITY guard (paraphrase-invariance count), not a volume/frequency knob — multiplying it would change trial STRICTNESS, an R-g-adjacent risk this design declines to touch |
| `AUDIT_PERIOD` | — | independent | system-level audit cadence, not tied to any one of the 5 families |
| `USER_RULINGS_BUDGET` | — | independent | user-facing appellate budget, operator-not-mix territory |
| `HOLDOUT_SHARE` | criticism | independent | evaluation holdout fraction (§10), a measurement-integrity knob, not a work-volume knob — multiplying it would change what counts as held-out evidence, out of scope for a LOAD dial |
| `XEXAM_SHARE` | criticism | independent | capture-control cross-examination share (§11), same measurement-integrity reasoning as `HOLDOUT_SHARE` |
| `RESEED_RATIO_MAX` | — | independent | stagnation-detection threshold (school convergence ratio), not a load knob |
| `NEIGHBOURHOOD_N` | conjecture | driven (share) | "exemplars shown per conj pack" (config.py:299) — directly sizes the conjecture pack's own content budget |
| `CAPTURE_W` | — | independent | orbiting-school gate-block window, stagnation detection, not a load knob |
| `CRIT_DEBT_CEILING` | criticism | driven (share) | adjudication-ritual debt fraction — directly meters how much unresolved criticism debt is tolerated |
| `RESEARCH_PERIOD` | simulation | driven (priority) | "cycles between research fetches" — capability-channel cadence (A4 below folds research into `simulation`) |
| `RESEARCH_ATTEMPTS_MAX` | simulation | driven (share) | capability-channel retry ceiling |
| `CX_RETRY_MAX` | criticism | driven (share) | counterexample-feedback retry budget against execution-backed targets |
| `FUZZ_N` | criticism | driven (share) | mechanical fuzz-input ceiling per property-oracle commitment |
| `GEN_PROPOSE_PERIOD` | criticism | driven (priority) | feeds `FUZZ_N`'s own generator authoring (M32) — criticism-family, not conjecture, despite the "GEN" name |
| `GEN_MAX` | criticism | driven (share) | ceiling on accepted fuzz-generators, same family as above |
| `PROP_PROPOSE_PERIOD` | coding | driven (priority), dead path | gates `property_designer` (the `"coder"` seat) but the call site is provably dead today (M34) — the multiplier applies to a period that currently never matters |
| `PROP_MAX` | coding | driven (share), dead path | same call site, same caveat |
| `DISC_ATTEMPTS_MAX` | — | independent | futility/starvation guard (discrimination backoff), not a volume knob — its job is to STOP infinite retry, not to allocate more or less of it |
| `HV_CONTENT_MAX_CHARS` | — | independent | a size SAFETY gate (skip oversized artifacts to avoid a dropped call), not a share of anything |
| `CHUNK_MAX_CHARS` | — | independent | website/code artifact fragment-size shape, a document-decomposition parameter, not a scheduling load knob |
| `PACK_TOKEN_BUDGET` | — | independent (A5) | applies uniformly to EVERY role's prompt pack today, cross-cutting infrastructure, not family-specific — see A5 |
| `RETRY_MAX` | — | independent | global LLM transport retry ceiling, applies to every call uniformly |
| `ARG_CRIT_PER_CYCLE` | criticism | driven (share) | "cap argumentative-critic TARGETS per cycle" — the direct criticism-volume ceiling |
| `CRIT_BATCH_K` | criticism | driven (share) | criticism throughput/cost knob (targets sharing one call) |
| `RECRIT_STANDING` | criticism | driven (share, boolean floor) | feature gate for leftover-capacity re-criticism; `share <= 0` after rounding is read as `False`, `> 0` as `True` — the one boolean-shaped driven knob |
| `maximum_simulation_requests` | simulation | driven (share) | capability-policy ceiling |
| `maximum_simulation_executions` | simulation | driven (share) | capability-policy ceiling |
| `maximum_proposals_per_turn` | simulation | driven (share) | capability-policy ceiling |
| `maximum_generated_code_bytes` | simulation | driven (share) | capability-policy ceiling |
| `maximum_input_bytes` | simulation | driven (share) | capability-policy ceiling |
| `maximum_output_bytes` | simulation | driven (share) | capability-policy ceiling |
| `maximum_wall_ms` | simulation | driven (share) | capability-policy ceiling |
| `maximum_memory_bytes` | simulation | driven (share) | capability-policy ceiling |
| `maximum_steps` | simulation | driven (share) | capability-policy ceiling |
| `maximum_samples` | simulation | driven (share) | capability-policy ceiling |
| `maximum_follow_up_reasoning_turns` | simulation | driven (share) | capability-policy ceiling |
| `maximum_sources` (research) | simulation | driven (share) | A4 folds research into `simulation` — capability-policy ceiling |
| `maximum_excerpt_bytes_per_source` | simulation | driven (share) | same fold |
| `maximum_total_excerpt_bytes` | simulation | driven (share) | same fold |
| `maximum_requests` (inquiry) | simulation | driven (share) | same fold — the third typed capability lifecycle (A4) |
| `cadence_cycles` | — | independent | `ConfigRefereePolicyV1` — a config-audit referee's own cadence, cross-cutting oversight unrelated to any one family |
| `window_events` | — | independent | same `ConfigRefereePolicyV1` pairing as `cadence_cycles` |
| `minimum_foreign_school_coverage` | criticism | driven (share) | `CriticismPolicyV1` — cross-family judge coverage requirement, sizes criticism's own diversity floor |
| `max_batch_size` | criticism | driven (share) | `CriticismPolicyV1` — the manifest-frozen twin of `CRIT_BATCH_K`; both driven by the SAME dial (a pre-existing near-duplication this design does not create and does not fix — PARKED, see PARKED.md) |
| `max_blocks_per_pack` | scratchpad | driven (share) | `AttentionPolicyV1` |
| `max_guides_per_pack` | scratchpad | driven (share) | `AttentionPolicyV1` |
| `coverage_slot_every_n_packs` | scratchpad | driven (priority) | `AttentionPolicyV1` — the one period-shaped attention knob |
| `exploratory_fraction` | scratchpad | driven (share) | `AttentionPolicyV1` |
| `underexposed_fraction` | scratchpad | driven (share) | `AttentionPolicyV1` |
| `dormant_after_events` | scratchpad | independent | an event-age THRESHOLD (when a thread is considered dormant), not a volume/frequency knob — multiplying it would change the MEANING of "dormant", not the scratchpad's load |
| `similarity_top_k` | scratchpad | driven (share) | `AttentionPolicyV1` |
| `guide_max_open_threads` | scratchpad | driven (share) | `AttentionPolicyV1` |
| `guide_max_entry_points` | scratchpad | driven (share) | `AttentionPolicyV1` |
| (new, not yet named) coder-delegation cadence | coding | driven-when-built | M33 — no live knob exists; this design names the family now, wiring is out of scope |

Count check: 54 rows tabled (M31) = 26 Config + 28 manifest-embedded,
plus 1 extra `driven-when-built` row for the new coding knob this
design names but that has no line number to measure (M33) — 55 rows
total. Every one of the 54 MEASURED rows has exactly one disposition:
38 `driven` (3 `driven (priority)`, 32 `driven (share)`, 1 `driven
(share, boolean floor)` — `RECRIT_STANDING`, 1 `driven (priority), dead
path`, 1 `driven (share), dead path` — the two `PROP_*` rows, M34), 16
`independent`. 0 are `deprecated` in this revision (the two
near-duplicate `CRIT_BATCH_K`/`max_batch_size` rows are flagged, not
removed — PARKED, not fixed here per C1/C2 of REQUEST.md).

```
$ python3 -c "
rows = {'driven (priority)': 3, 'driven (share)': 32, 'driven (share, boolean floor)': 1,
        'driven (priority), dead path': 1, 'driven (share), dead path': 1, 'independent': 16}
measured = sum(rows.values())
print('measured 54 rows:', measured)
print('plus 1 driven-when-built placeholder =', measured + 1, 'table rows total')
"
measured 54 rows: 54
plus 1 driven-when-built placeholder = 55 table rows total
```

### Item 2 (R9): mint-time freezing, the rung-7 placement law, and BOTH frozen-surface contacts

`load_mix: LoadMixPolicyV1 | None = None` is added to the v6
`RunManifest` class (`run_manifest.py`), following the SAME shape as
the already-existing `simulation_capability_policy: SimulationCapability
PolicyV1 | None = None` (an optional, None-defaulting sub-model field on
the same class) and the SAME proof obligation D3 already discharged for
its own new `Literal` option (M37). At `deepreason reason` (mint time,
M41), `build_preparation_manifest` resolves the `--load-mix` flag (Item
3) to a `LoadMixPolicyV1` (or `None` for the default preset) and passes
it through `compile_run_manifest(..., load_mix=resolved)`, exactly the
same argument-threading shape `criticism_policy`/`inquiry_capability_
policy` already use (M40) — no new compilation mechanism, one new
argument on an existing one.

**The rung-7 placement law ("a continuation continues under the mix it
was minted with")** is satisfied by the SAME mechanism every other
manifest field already gets: `deepreason continue` resumes from the
STORED, frozen `RunManifest` (unconditionally immutable per the append-
only record's own governing principle, `INV-frozen-surfaces.md`); the
mix is read back from that stored manifest, never re-resolved from a
fresh `--load-mix` flag at continue time. `Config`'s own driven fields
are then reconstructed by applying Item 1's pure multiplier function to
the SAME frozen `LoadMixPolicyV1` — deterministic given the same code
(no run-state dependency), so mint and every later continue apply
byte-identical multipliers as long as the code computing them has not
itself changed (the same limitation every other Config knob already
has across `continue` today — not a new one this design introduces).

**Frozen-surface contact forecast (both named, neither assumed away —
resolves Q4):**

- **Surface 4 (`run_manifest.py` schemas AND validators).** Contact:
  YES. One new field (`load_mix`) plus two new small models
  (`FamilyDialV1`, `LoadMixPolicyV1`), added the same way `simulation_
  capability_policy` already exists on the class. Per `INV-frozen-
  surfaces.md`'s own Trap ("Adding a `Config` field is not
  automatically invisible to replay ... `_versioned_source_config_
  data` ... must be told about each one, per schema version,
  explicitly"): `load_mix` lives on `RunManifest` directly, not inside
  `Config`, so it does NOT go through `_versioned_source_config_data`
  at all (that function pops keys out of `Config`'s own dump, a
  different surface) — but the EXECUTE rung must still prove, live,
  the SAME old-digest-unchanged / new-digest-differs pair D3 proved for
  its own new field (M37), because `RunManifest`'s own compiled
  `sha256` — a SEPARATE hash from `source_config_hash`/`engine_config_
  json` — is computed over the model's own serialized shape, which one
  new None-defaulting field DOES perturb for the byte-for-byte
  comparison even if the semantically-meaningful bytes are unchanged.
  This is the SAME class of proof, at a DIFFERENT hash surface, and
  the EXECUTE rung must not assume M37's proof at the `Config`-digest
  surface substitutes for one at the manifest-`sha256` surface.
- **Surface 5 (`qualification_subject_payload`).** Contact: YES —
  found by this tranche's own measurement (M38), not by the task's own
  framing, which named surface 4 alone. `manifest.model_dump(mode=
  "json", by_alias=True)` is the WHOLE subject; adding any new field
  changes it for every profile, forcing one ~14-minute requalification
  per home the first time a run compiles against the widened class —
  paid ONCE per home regardless of whether that run's own mix is the
  default (`None`) or a named preset. This is a cost, not a
  correctness risk (CLAUDE.md: "Changing the profile ... reruns the
  full battery ... This is by design; budget for it") — but it is a
  contact this design's operator words must authorize alongside
  surface 4, priced in the Budget section below.
- **Surfaces 1, 2, 3.** Contact: NO (M39, M36) — none of `capabilities/
  state.py`, `harness.py`, `invariants.py`/`verification/` enumerates
  or dumps the manifest's fields; each reads only the specific fields
  it already names. `capabilities/state.py`'s own shared pooling maps
  (M36) are unaffected because the mix changes CEILING VALUES the
  existing typed controllers already read, never the map/filtering
  code itself.

Both contacts are named to the operator in the Decision sheet below
as one combined fork (F1) — this design assumes NO grant for either,
per R9's own instruction, and the EXECUTE rung cannot proceed past its
own frozen-surface-contact stop without the operator's words, worded
in the Amendment-3 precedent shape (C11/C12, quoted in REQUEST.md).

### Item 3 (R10): named presets as the operator surface

`reason_cmd.add_argument("--load-mix", choices=(...), default=None)`
(M41, M42's own `--profile` shape). `default=None` compiles to
`load_mix=None` on the manifest — R11's own accept criterion ("default
preset = today's behavior byte-identical") holds by CONSTRUCTION (Item
1: every dial defaults to `1.0`, and `None` skips dial application
entirely rather than applying a no-op 1.0× — the two are behaviorally
identical but `None` is the cheaper, more legible choice: it also means
a manifest compiled without `--load-mix` is IDENTICAL, field-for-field,
to a pre-D4 manifest wherever the field is entirely absent from an old
schema class, which it is, since old schema versions are separate
classes that never gain the field at all).

The actual preset TABLE (names beyond `default`, and their per-family
`share`/`priority` values) is priced as fork F3 in the Decision sheet
— `BEHAVIOR_MODES_PREPLAN.md`/`ROLE_SEAT_SEPARATION_PLAN.md` S7 (M43)
supply illustrative shapes (explore/argument/critical, brainstorm/
prove/referee) but neither is a captured request, so this design does
not commit to a specific preset table without the operator choosing
one.

### Item 4 (R12): the R-g argument, work families vs conjecture KIND, and its enforcement test

**The distinction, stated precisely.** Every knob Item 1 disposes
`driven` governs HOW OFTEN or HOW MUCH a WORK FAMILY's machinery runs
— a period, a ceiling, a fraction of a shared pool. None of them reads,
or can read, any individual artifact's `Interface.commitments`,
`Status`, or kind signal: `RESEARCH_PERIOD`/`ARG_CRIT_PER_CYCLE`/
`max_blocks_per_pack`/etc. are scalar knobs consumed by `Config`/the
manifest BEFORE any cycle runs, with no per-artifact branch anywhere in
their own read sites (CENSUS.md section 4(c): the foundational
acceptance computation "has no parameter through which a commitment...
could reach it even if someone wanted it to" — the SAME structural fact
applies to every period/ceiling knob Item 1 multiplies: they gate WHEN
a family's machinery is CALLED, never WHICH artifact within that call
gets favored). A mix that scales `ARG_CRIT_PER_CYCLE` changes how many
targets criticism attempts THIS cycle; it cannot change WHICH targets
get selected by kind, because the target-selection code
(`Scheduler._arg_crit`'s `eligible` list, CENSUS.md M6) reads `admitted_
ids` filtered on `Status.ACCEPTED`, not on kind, both before and after
this design.

The ONE place today's system already reads kind for a scheduling
decision — `_standing_recrit_pool`'s execution-backed-first ordering
(CENSUS.md section 4(a)) — is explicitly NOT touched: no Item 1 dial
multiplies anything `_standing_recrit_pool` itself reads (it has no
period/ceiling knob of its own; it consumes whatever `ARG_CRIT_PER_
CYCLE` slots are LEFT OVER after `_arg_crit`'s own pass, and the mix's
`criticism.share` dial changes the SIZE of that leftover pool, never
the kind-ordering rule that sorts within it).

**The enforcement test.** D3 already delivered `test_R_g_no_scheduling_
term_reads_the_candidate_checker_kind` (R36, D3's DELIVERY.md). This
design's own EXECUTE rung must add a sibling regression: two runs
identical except for `--load-mix` (default vs a criticism-heavy
preset) produce IDENTICAL `_standing_recrit_pool` ordering for the same
artifact set (same execution-backed-first order, same members) —
proving the mix shifted VOLUME (how many slots existed) without
shifting the ORDERING RULE (which is a pure function of each
artifact's own kind, untouched by any Item 1 dial). This is the R-g
argument's own falsifiable form, not an assertion.

### Item 5 (R13): interaction with per-capability budgets

M36's own pooling code confirms the interaction is SAFE by
construction: the mix's `simulation.share` dial multiplies the
CEILING VALUES on `SimulationCapabilityPolicyV1`/`ResearchCapability
PolicyV1` (A4 folds both, plus `InquiryCapabilityPolicyV1`, under one
family dial) — it never touches `capabilities/state.py`'s own
`self.proposals`/`self.work_orders` maps or their `isinstance`-based
type filtering. Every existing controller (`SimulationController`,
`ResearchController`) already reads only its own proposal type from
the shared maps; a wider or narrower ceiling changes how many of THAT
controller's own proposals get admitted, never which type a shared-map
entry belongs to. No new pooling risk; the mix is a pure ceiling-value
transform upstream of code that already respects the invariant.

## Assumptions (operator may override)

A1 (Q1): this tranche's own re-derivation of `CENSUS.md` section 5
finds 54 knobs, not the task's own "43" — adopted as the measured
base; every one of the 54 gets a disposition in Item 1 (M31).

A2 (Q3 shape choice): `share`/`priority` are MULTIPLIERS on existing
knob defaults (never replacement absolute values) — the smallest
mechanism that makes "default preset = byte-identical" true by
construction rather than by a parallel code path, and the one that
composes with every knob's own existing validator bounds without this
design needing to re-derive a new unit convention per knob.

A3 (Q3 semantics): `share` = fraction/ceiling multiplier; `priority` =
frequency multiplier (inverse on periods) — derived from M32's own
per-knob docstrings, not assumed; a knob that is neither shape is
assigned by its own nearest docstring reading, written down per-row in
Item 1's table.

A4 (folding research and inquiry into the `simulation` family): R-f
names exactly {conjecture, criticism, scratchpad, simulation, coding} —
no separate "research" or "inquiry" axis. `capabilities/state.py`'s own
shared proposal/work-order maps (M36) already treat simulation,
research, and inquiry as the SAME typed capability-channel lifecycle
(`PROPOSED -> ... -> CONSUMED`), dispatched from the SAME two `conj.py`
call sites (CENSUS.md M1) — the only structural grouping the tree
itself offers. Folded under `simulation` rather than inventing a sixth
family R-f's own words do not name. Operator may override by splitting
this into its own family in a later revision.

A5 (`PACK_TOKEN_BUDGET`/`RETRY_MAX` independence): both apply
uniformly to every role's call today (M32, config.py:527-529, "LLM
adapter (§9)" — no per-role branch in either knob's own read site).
Making either `driven` would require inventing a NEW per-family
token/retry budget the mix could scale, which is more mechanism than
R-f's words ask for this rung; left independent, flagged as a natural
D5-or-later extension, not built here.

A6 (coding family's `driven-when-built` row): this design NAMES the
family and its multiplier semantics for a knob that does not exist yet
(M33) rather than leaving `coding` with only its two dead-path rows
(M34) — the operator may instead choose to leave `coding` fully
`independent` until a future tranche wires the call site AND its own
knob in the same tranche; priced as fork F2 below.

## Questions for operator (STOP if non-empty)

(none — every open question in REQUEST.md was resolved above by
measurement or by the dominance test: Q1 by M31, Q2 by M33/M34 + Item
1's `driven-when-built` disposition, Q3 by M32's per-knob docstrings
(A2/A3), Q4 by M38/M39, Q5 by quoting Amendment 3 verbatim in
REQUEST.md already. The Decision sheet below carries the forks where
the record underdetermines a DESIGN CHOICE rather than a factual
question — those are priced with recommendations, not asked blind.)

## Out of scope (explicit)

- **Wiring `draft_encoded_commitment`/`relatedness_trial` into the
  scheduler.** M33 found both dormant; making them reachable is a
  scheduler-wiring tranche (new call sites, new bracketing decisions
  per `SEAM-rules-x-workflow.md`'s own transactional-guard rules), not
  a load-dial design. "Not requested" — R7 asks the dial set to COVER
  the coding load that now exists, which Item 1 does (naming the
  family and its future knob), not to MAKE it exist.
- **Fixing `PROP_MAX`/`PROP_PROPOSE_PERIOD`'s dead call site (M3/M34).**
  A defect, not a change; PARKED per CLAUDE.md's cross-routing rule
  (C1/C2 of REQUEST.md) rather than fixed mid-design.
- **Deduplicating `CRIT_BATCH_K` and `CriticismPolicyV1.max_batch_
  size`.** Both already exist, both get the SAME dial in Item 1; their
  own redundancy predates this tranche and is PARKED, not resolved
  here.
- **The final preset table's exact names/values (beyond `default`).**
  Priced as fork F3; `BEHAVIOR_MODES_PREPLAN`/S7 are forward pointers,
  not captured requests this tranche must satisfy verbatim.
- **A per-family token/retry budget for `PACK_TOKEN_BUDGET`/`RETRY_
  MAX`.** A5 — more mechanism than this rung's own words ask for.
- **Splitting `simulation`/`research`/`inquiry` into separate mix
  families.** A4 — R-f names five families, not six or eight.

## Frozen-surface contact forecast

Surface 4 (`run_manifest.py` schemas AND validators): contact expected
— **STOP, operator words required before `dr-plan-steps`** (Item 2,
M37). Follows the same shape as the existing `simulation_capability_
policy`/`conjecturer_turn_contract` v7 additions; needs its own
old-digest-unchanged / new-digest-differs proof at the manifest-`sha256`
surface (a different hash than D3's own `Config`-digest proof).

Surface 5 (`qualification.py::qualification_subject_payload`): contact
expected — **STOP, operator words required before `dr-plan-steps`**
(Item 2, M38). Forces one ~14-minute requalification per home the
first time any run compiles against the widened v6 class, regardless
of whether that run uses the default (`None`) mix or a named preset.
This is the finding that overturns the task's own "surface 4 alone"
expectation — reported here rather than absorbed silently.

Surfaces 1, 2, 3: no contact (M39, M36) — checked against `INV-frozen-
surfaces.md`, not assumed.

## Blast-radius census

```
$ grep -rn "LoadMixPolicy\|load_mix\|LOAD_MIX\|FamilyDialV1" tests/ docs/map/ src/
(no output — exit 1, zero hits: no naming collision anywhere in the tree)
```
```
$ grep -rl "schema_version == 6\|schema_version=6" tests/ | wc -l
40
```
40 files (listed in full in this tranche's own research; representative:
`test_run_manifest.py`, `test_v6_engaged_public_defaults.py`, every
`test_v6_*` file) — **EXPECTED TO MOVE**: each is expected to keep
passing UNCHANGED once `load_mix` is added with `default=None`,
because none of them constructs a manifest via a route that would
newly require the field; a genuine MUST-NOT-MOVE violation would be
any one of these failing after the field's addition, which the EXECUTE
rung's own gate run proves or disproves, not this design.
```
$ grep -rl "canonical_bytes\|canonical_shapes_and_hashes\|source_config_hash\|engine_config_json" tests/ | wc -l
31
```
31 files (representative: `test_run_manifest.py`, `test_v6_contract_
schema_repair_policy.py`, `test_v6_engaged_public_defaults.py`) —
**MUST NOT MOVE** for every EXISTING pinned hash (a manifest compiled
with `load_mix` absent/`None` must reproduce byte-identical
`source_config_hash`/`engine_config_json` to before, per the Traps
section's own `_versioned_source_config_data` precedent — `load_mix`
lives on `RunManifest`, not `Config`, so this specific pop mechanism
does not apply to it, but the SAME "unconditionally byte-identical
absent" property must hold at whichever surface actually governs it,
proven live at the EXECUTE rung, not assumed here) — any NEW pinned
hash these tests gain for a manifest that DOES set `load_mix` is
**EXPECTED TO MOVE** (a new golden, not a changed one).

```
$ grep -rln "engaged_criticism_policy|engaged_simulation_toolchain|engaged_inquiry_capability_policy|engaged_control_plane_policy_v3" tests/ | wc -l
4
```
4 files reference the `engaged_*` preset functions Item 3 threads a new
argument through — **EXPECTED TO MOVE** only in the sense that any test
calling these functions directly (not through `build_preparation_
manifest`) may need a new optional keyword-argument default added at
the EXECUTE rung if the mix multiplier is applied inside the `engaged_*`
functions themselves rather than at their call site in `preparation.py`
(a Step-level choice for `dr-plan-steps`, not decided here) — MUST NOT
MOVE for their own existing assertions about the "engaged" preset's
CURRENT fixed values, which stay the default-preset behavior.

## Measurements

All load-bearing measurements for this design are M31 through M43,
pasted in full above under "New measurements this tranche"; D1's
M1-M14 and D2's M15-M30 are cited by number, not re-pasted, per R6's
own "cite its rows, re-measure only what the design turns on."

## Options (forks)

**Where to apply the multiplier — three candidate sites, priced:**

- A: inside each `engaged_*` function itself (`v6_policy.py`) — each
  function gains an optional `mix: FamilyDialV1 | None = None`
  parameter. Files touched: `v6_policy.py` (~5 functions), `preparation.
  py` (thread the argument through). Frozen contact: none beyond Item
  2's own surface-4/5 contact (these functions are not themselves
  frozen). ~40 lines. Risk: LOW — each function already owns exactly
  the values it would scale, no cross-file coupling. **CHOSEN** — cites
  M40 (every family's manifest-embedded value is already a named-
  function call; scaling inside the function keeps the "one value, one
  owner" property M40 found already true).
- B: a single central `apply_load_mix(manifest_kwargs, mix)` function
  called once in `preparation.py` before `compile_run_manifest`. Files
  touched: one new function, `preparation.py`. ~60 lines (needs its own
  per-field dispatch table duplicating Item 1's disposition table).
  Risk: MEDIUM — a second place (beyond Item 1's own table) that must
  stay in sync with which knobs are driven; a knob added later to
  either table without the other silently desyncs. Rejected: cites M40
  — the `engaged_*` functions already ARE the per-family dispatch
  point; a second one duplicates rather than reuses it.
- C: apply the multiplier at `Config`-construction time only, leaving
  every manifest-embedded knob (capability policies, `CriticismPolicyV1`,
  `AttentionPolicyV1`) unmultiplied. Files touched: `config.py`'s own
  construction site only, ~15 lines. Frozen contact: NONE (Item 2's
  surfaces 4/5 contact disappears entirely). Risk: LOW mechanically,
  but rejected: cites M31 — 28 of the 54 knobs (the entire manifest-
  embedded half, including 100% of the `scratchpad` family) would be
  silently excluded from R-f's own five named families, contradicting
  R10's "every knob dispositioned explicitly ... silent omission is a
  bug." A cheaper mechanism that cannot cover `scratchpad` at all does
  not satisfy the request; not a real option once R10 is read in full.

## Budget

Item 1 (record + disposition table, no code): 0 lines (design-only).
Item 2 (frozen-surface forecast + rung-7 mechanism, no code): 0 lines.
Item 3 (CLI flag design, no code): 0 lines.
Item 4 (R-g argument + enforcement-test design, no code): 0 lines.
Item 5 (capability-budget interaction argument, no code): 0 lines.
This document itself: REQUEST.md + SPEC.md, the only artifacts this
tranche produces.

```
$ python3 -c "print(0 + 0 + 0 + 0 + 0)"
0
```

**Headline: 0 lines of `src/`/`tests/`/`tools/` diff this tranche —
DESIGN-AND-STOP produces no code (S1/C1).** The EXECUTE rung's own
budget (Item 1's ~5 `engaged_*` function edits, two new Pydantic
models, one new CLI flag, one new sweep-probe-shaped regression per
the Blast-radius census above, plus the two frozen-surface proofs
Item 2 names) is NOT estimated here — `dr-plan-steps` prices it against
this SPEC once the operator's words on Item 2's two-surface fork (F1)
are in hand, per R9/`INV-frozen-surfaces.md`'s own STOP-before-plan
rule. Frozen surfaces touched: 4 and 5 (flagged, operator words
required — see Frozen-surface contact forecast).

Rubric: 6/6 yes — every R has a spec item with a machine-decidable
accept (S1-S17 above map every R1-R18, several sharing one item where
the request itself grouped them); blast-radius census pasted and every
hit classified; frozen-surface contact forecast recorded (both
surfaces, not assumed to be one); every mechanism the request names
(the D1 census, the Amendment-3 precedent shape, `deepreason setup`/
`reason`) traced to code it actually reaches (M32-M43); DESIGN-AND-STOP
measurements are all pasted commands, every option priced against a
measurement, not a preference; nothing above is untraceable to an R/C
number.

## Decision sheet — every fork priced as roads, with a recommendation

**F1 — grant surface-4 AND surface-5 contact for the EXECUTE rung, or
decline.**
- Road A (grant both, scoped like Amendment 3's own C11/C12 shape):
  the EXECUTE rung adds `load_mix`/`FamilyDialV1`/`LoadMixPolicyV1` to
  `run_manifest.py` (surface 4) and accepts the one-time-per-home
  requalification cost `qualification_subject_payload`'s whole-manifest
  hash forces (surface 5, M38) the first time any run compiles against
  the widened class. Cost: ~14 minutes once per home, paid whether or
  not that run's own mix is the default. Unlocks: the mix as a real,
  frozen, continuation-safe per-run setting — R-f's own request.
- Road B (decline): the load dials stay a documented design with no
  live mechanism; `--load-mix` never ships. Cost: R-f remains unbuilt.
  No frozen contact, no requalification cost.
- **Recommendation: Road A**, scoped exactly like Amendment 3's own
  grant (one named field/model addition, nothing else in `run_manifest.
  py`, the requalification cost stated up front rather than discovered
  live) — the preplan's own D4 rung explicitly expects a frozen-surface
  question here; declining leaves R-f permanently unmet.

**F2 — the `coding` family's `driven-when-built` placeholder (A6), or
leave it fully independent until wiring lands.**
- Road A (name it now, as this design does): the mix's own record
  already carries a `coding` dial from day one; a later wiring tranche
  only needs to name and consume ONE new Config knob, not also decide
  which family it belongs to.
- Road B (independent until wired): simpler EXECUTE rung today (one
  fewer disposition to defend), but the wiring tranche later must
  itself decide the family assignment, without this tranche's own
  measured docstring-reading discipline (M32) informing it.
- **Recommendation: Road A** — cheap now (a documentation-only row,
  M33/M34 already did the measurement), and keeps R7's own "must cover
  the coding load that now exists" satisfied in the record even before
  any code exists to drive.

**F3 — the preset table beyond `default` (names + per-family values).**
- Road A (ship `default` only this rung, add named presets in a
  follow-up once the operator picks values): smallest EXECUTE rung;
  R11's own "default preset = today's behavior byte-identical" is
  fully satisfiable with `default` alone.
- Road B (design a starter table now, e.g. `explore`/`argument`/
  `prove`, borrowing BEHAVIOR_MODES_PREPLAN's/S7's sketched shapes):
  ships something usable immediately, but commits to specific numbers
  neither cited preplan actually specifies (both are explicitly
  "sketched"/"idea only", M43) — risks the operator needing a second
  round to correct values this design guessed.
- **Recommendation: Road A** — `default` alone discharges R11's own
  accept criterion; a starter table is cheap to add in the SAME
  EXECUTE rung once the operator has seen this design and can hand
  concrete numbers, rather than this document guessing them now.

**Overall recommendation:** grant F1 Road A (both surfaces, scoped),
build F2 Road A (name `coding` now) and F3 Road A (`default` only,
presets follow) in the same EXECUTE rung — the smallest tranche that
fully discharges R7-R13 while leaving the preset table's actual
numbers as the operator's own choice rather than this design's guess.
