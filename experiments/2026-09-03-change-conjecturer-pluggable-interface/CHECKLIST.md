# Checklist for: the conjecturer's brief and form as a pluggable, configurable interface

State: next=4 blockers=none — SPEC.md APPROVED by the operator 2026-09-03,
verbatim: "Given what read from the other windows, the plugin one. Since all
three other windows have completed." Build window open; branch
`claude/conjecturer-pluggable-interface-7v3es6` (substituted for the design
window's branch wherever step 42 names it).

Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order.
One step per `dr-execute-step` invocation. Never mark a step done without
pasting its done-criterion output.

**Map ids this plan was built on** (`REQUEST.md` §4; read the seam before
either subsystem): `DR-INV-frozen-surfaces`, `DR-INV-render-layout`,
`DR-INV-signal-contract`, `DR-INV-reference-menu`, `DR-SEAM-llm-x-rules`,
`DR-SUB-llm`, `DR-CON-packs-and-token-economy`, `DR-CON-conjecture-source`,
`DR-CON-model-profiles`, `DR-CON-seats`, `DR-CON-conjecture-kinds`,
`DR-SUB-manifest`, `DR-SUB-verification`. The seam
`packs-and-token-economy x rules` does NOT exist and is created at step 3,
before any code.

**Three decisions that keep this tranche at `frozen_surface_verdict:
CLEAR`** (SPEC §13). If a step cannot hold one, STOP and request the grant
in that step's own document before code:
(1) selection by argument/env, never `Config`, never the manifest;
(2) no new contract id; (3) no new `verify_root` check.

---

## Phase 0 — preflight and the golden that everything is measured against

- [x] 1. (all) Session preflight per `dr-drive-harness` §1: resync the
      branch, `pip install -e . --break-system-packages -q`, then
      `python -m pip install pytest pytest-xdist jsonschema
      --break-system-packages -q` (the gate's own deps; `pyproject.toml`
      declares neither — CLAUDE.md, Environment).
      done-when: `python -c "import deepreason, xdist, jsonschema; print('ok')"`
      -> `ok`

      DONE 2026-09-03. Base `7d7996302` (>= the required `7d7996302e`).
      `pip install -e . --break-system-packages -q` and
      `python -m pip install pytest pytest-xdist jsonschema
      --break-system-packages -q` both returned clean.
      ```
      $ python -c "import deepreason, xdist, jsonschema; print('ok')"
      ok
      ```

- [x] 2. (S10.4) Capture the byte-identical-default GOLDEN from the BASE
      COMMIT, before any refactor exists. Write
      `tests/fixtures/conj_pack_legacy_v0/` holding, for a fixed committed
      record and a fixed set of `render_conj_pack` arguments, the exact
      bytes `2d84a86cd` produces — at minimum one MINIMAL case (problem +
      criteria only) and one MAXIMAL case (every optional context
      supplied, menus included, a budget tight enough to force a
      `context-withheld` notice).
      done-when: `python -c "import pathlib; d=pathlib.Path('tests/fixtures/conj_pack_legacy_v0'); fs=sorted(d.glob('*.txt')); print(len(fs)); assert len(fs)>=2"`
      -> `2` or more, AND one fixture file contains the literal
      `CONTEXT WITHHELD FOR BUDGET`

      DONE 2026-09-03. `git diff --stat 2d84a86cd..HEAD -- src/deepreason/llm/packs.py
      src/deepreason/packs/ src/deepreason/llm/layout.py` is EMPTY, so the
      golden captured from this window's base `7d7996302` is byte-identical to
      the one the spec's base `2d84a86cd` would have produced.
      Inputs live in `tests/conj_pack_golden_cases.py` as literals (artifact
      ids are content-derived, so the state is reproducible on any machine).
      FIVE cases, which between them reach all twenty section slots, the menu
      section, the withheld notice and the restated question:
      `minimal` (a bare first cycle), `maximal`, `withheld`, `legacy_layout`,
      `superseded`.
      ```
      $ python -c "import pathlib; d=pathlib.Path('tests/fixtures/conj_pack_legacy_v0'); fs=sorted(d.glob('*.txt')); print(len(fs)); assert len(fs)>=2"
      5
      $ grep -l "CONTEXT WITHHELD FOR BUDGET" tests/fixtures/conj_pack_legacy_v0/*.txt
      tests/fixtures/conj_pack_legacy_v0/withheld.txt
      ```

- [x] 3. (S10.4) [COMMIT] Write `tests/test_conj_pack_legacy_golden.py`
      asserting `render_conj_pack` reproduces each fixture byte-for-byte,
      and prove it can FAIL by running it against a one-character mutation
      of a fixture.
      done-when: `python -m pytest tests/test_conj_pack_legacy_golden.py -q`
      -> `0 failed`, AND the pasted RED run of the mutated fixture

      DONE 2026-09-03. GREEN on the tree:
      ```
      $ python -m pytest tests/test_conj_pack_legacy_golden.py -q
      ........                                                          [100%]
      8 passed in 0.28s
      ```
      RED against a ONE-CHARACTER mutation of `maximal.txt`
      (`PROBLEM p-golden` -> `PROBLEM p-golded`), then restored:
      ```
      E           ## problem
      E         - PROBLEM p-golded
      E         + PROBLEM p-golden
      FAILED tests/test_conj_pack_legacy_golden.py::
        test_the_default_render_is_byte_identical_to_the_committed_golden[maximal]
      1 failed, 7 passed in 0.31s
      ```
      Instruments at the commit boundary:
      `DIFF_BUDGET_RESULT_V1 ... "areas": {"src/*": 0}, "verdict": "WITHIN"`;
      `blast_radius.py --against 7d7996302` -> `frozen_surface_verdict: CLEAR`,
      contacts `[]`, adjacent `[]`, no reachability drift.

## Phase 1 — the map, written before the code it describes

- [ ] 4. (S13) Create `docs/map/SEAM-packs-and-token-economy-x-rules.md`,
      describing the agreement as it stands TODAY: which of the twenty
      brief sections `rules/conj.py` computes rather than the renderer
      (FEASIBILITY §2), the three appended AFTER allocation, and the
      `AllocatedPack` marker rule that keeps the adapter from re-clipping.
      Read `docs/map/SCHEMA.md` first; every load-bearing claim carries a
      column-0 `check:` that can fail.
      done-when: `python tools/docs_verify.py --audit` -> 0 findings, AND
      `python tools/docs_verify.py --links` -> 0 unresolved

- [ ] 5. (S13) [COMMIT] Add the row for the new seam to
      `docs/map/INDEX.md`'s seam matrix and remove it from
      `CON-packs-and-token-economy.md`'s `Seams-undocumented:` header.
      done-when: `python tools/docs_verify.py` (FULL mode) -> `0 failed`

## Phase 2 — the section-plugin interface

- [ ] 6. (S1.1, S1.2, S1.3, S1.4) Add `src/deepreason/llm/conj_sections.py`
      with `ConjecturerSectionPluginV1`, `SectionRequestV1` (frozen),
      `SectionRenderV1`, `SectionReceiptV1`. NO registry and NO consumer
      yet — types only.
      done-when: `python -c "from deepreason.llm.conj_sections import SectionRequestV1, SectionRenderV1, SectionReceiptV1; SectionRequestV1.model_config['frozen'] or exit(1); print('ok')"`
      -> `ok`

- [ ] 7. (S1.3) Write `tests/test_conj_section_contract.py`: an empty
      `text` is an ERROR while `None` is a legal absence — the distinction
      the allocator's drop signal depends on (`DR-INV-render-layout`
      Traps).
      done-when: `python -m pytest tests/test_conj_section_contract.py -q`
      -> `0 failed`

- [ ] 8. (S2.1, S2.2, S2.3) [COMMIT] Add `SECTION_PLUGIN_REGISTRY`,
      `register_section_plugin`, `resolve_section_plugin` — modelled on
      `llm/layout.py::register_layout_policy`. Version resolution: pinned
      exact, unpinned highest.
      done-when: `python -m pytest tests/test_conj_section_registry.py -q`
      -> `0 failed`, including a case asserting an unregistered id is a
      TYPED refusal and not a load-by-path (S3.2)

## Phase 3 — the layout, and the twenty seeded plugins

- [ ] 9. (S10.1) Add `ConjecturerPackLayoutV1` with per-entry
      `priority`/`droppable`/`compressible`/`min_tokens`/`max_render_bytes`
      /`params`, envelopes refused typed at construction, never clamped
      (SPEC §9, FREE layer).
      done-when: `python -m pytest tests/test_conj_pack_layout.py -q`
      -> `0 failed`, including one out-of-envelope value raising rather
      than clamping

- [ ] 10. (S10.2, S9.4) Add selection: argument -> `DEEPREASON_CONJ_PACK_LAYOUT`
      -> default. Add the guard test that NO layout knob reaches `Config`,
      copying `DR-INV-render-layout`'s own check shape.
      done-when: `python -c "
from deepreason.config import Config
assert not [f for f in Config.model_fields if 'CONJ_PACK' in f.upper() or 'SECTION_PLUGIN' in f.upper()]
from deepreason.llm.conj_sections import CONJ_PACK_LAYOUT_ENV
assert CONJ_PACK_LAYOUT_ENV == 'DEEPREASON_CONJ_PACK_LAYOUT'
print('ok')"` -> `ok`

- [ ] 11. (S1.5) [COMMIT] Seed the twenty `dr.*` plugins, one per row of
      FEASIBILITY §1's table, each a mechanical extraction of the existing
      text at default parameters. NO renderer change yet.
      done-when: `python -c "
from deepreason.llm.conj_sections import SECTION_PLUGIN_REGISTRY
ids={k[0] for k in SECTION_PLUGIN_REGISTRY}
print(len(ids)); assert len(ids)>=20, sorted(ids)"` -> `20` or more

- [ ] 12. (S1.6) Add `dr.history.v1` with `include_refuted` defaulting
      `false` (today's `layout.superseded_summary_n == 0`), rendering
      prior-round material as evidence.
      done-when: `python -m pytest tests/test_conj_section_history.py -q`
      -> `0 failed`, including a case proving `include_refuted=false`
      renders no REFUTED artifact

- [ ] 13. (S1.7) Register `dr.episodes.slot`: present in the registry,
      absent from every shipped layout, `render` returns `None`,
      docstring states the operator has not decided what episodes are
      (`R13`).
      done-when: `python -c "
from deepreason.llm.conj_sections import resolve_section_plugin, CONJ_PACK_LAYOUT_LEGACY_V0
p=resolve_section_plugin('dr.episodes.slot')
assert 'dr.episodes.slot' not in {e.plugin_id for e in CONJ_PACK_LAYOUT_LEGACY_V0.entries}
print('ok')"` -> `ok`

- [ ] 14. (S10.3) [COMMIT] Define `conj-pack.legacy-v0` reproducing
      FEASIBILITY §1's table exactly — same twenty ids, priorities, flags
      and caps.
      done-when: `python -m pytest tests/test_conj_pack_layout.py -k legacy -q`
      -> `0 failed`

## Phase 4 — the renderer walks the layout (the load-bearing refactor)

- [ ] 15. (S1, S2.3, S10.3) Rewrite `render_conj_pack` to resolve every
      section through `resolve_section_plugin` and walk the layout, with
      `A6` respected: the nine caller-computed contexts arrive in
      `SectionRequestV1.supplied` and their plugins FORMAT them. Update
      `DR-CON-packs-and-token-economy` and `DR-INV-render-layout` IN THIS
      SAME COMMIT (map moves with code, `docs/map/SCHEMA.md`).
      done-when: `python -m pytest tests/test_conj_pack_legacy_golden.py -q`
      -> `0 failed` — **the byte-identical default (S10.4). If this cannot
      pass, the refactor is wrong: STOP, do not update the fixture.**

- [ ] 16. (S1) Run the affected test ring (iterate on the ring, gate at
      the boundary — CLAUDE.md).
      done-when: `python -m pytest tests/test_render_layout_rules.py
      tests/test_render_layout_policy.py tests/test_frame_render.py
      tests/test_discharge_channel.py tests/test_reference_menu.py
      tests/test_pack_prefix.py -q` -> `0 failed`

- [ ] 17. (S5, S6) [COMMIT] Wire `declared_handle_kinds`: the REGISTRY, not
      the plugin, renders menus through `menu_renders_for` at priority 4;
      an evidence-family plugin outside `DISCLOSED_ON_DROP` is a typed
      refusal at layout construction.
      done-when: `python -m pytest tests/test_conj_section_citation.py -q`
      -> `0 failed`, including a case proving a free-text evidence plugin
      still yields a pack in which every bound `citable_block_ids` entry
      appears literally (`A1`)

## Phase 5 — the record

- [ ] 18. (S7.1, S7.2) Add the `workflow.context-section-plan.v1` object
      kind and write one per rendered conjecturer pack.
      done-when: `python -m pytest tests/test_conj_section_record.py -q`
      -> `0 failed`, including a case asserting `disposition` is `dropped`
      for a section the allocator cut

- [ ] 19. (S7.3, S13-decision-3) [COMMIT] Prove surface 3 is untouched: no
      new `verify_root` check, and `invariants.py`/`verification/` do not
      mention the new kind.
      done-when: `python -c "
import pathlib
s=pathlib.Path('src/deepreason/invariants.py').read_text()+pathlib.Path('src/deepreason/verification/report.py').read_text()
assert 'context-section-plan' not in s and 'section_plan' not in s
print('ok')"` -> `ok`

## Phase 6 — the template layer

- [ ] 20. (S4.1) Add the template kind: `{{ name }}` and
      `{% for %}…{% endfor %}` ONLY. Write the refusal tests FIRST — an
      expression, an import, a two-dot traversal, a code-calling filter
      must each be a typed refusal (`S3.2`'s trust boundary is a reason to
      keep this small, not to widen it).
      done-when: `python -m pytest tests/test_conj_section_template.py -k refus -q`
      -> `0 failed`, with each refusal case listed

- [ ] 21. (S4.3) [COMMIT] Add the `max_render_bytes` ceiling: overrun is a
      typed error naming the template, never a silent clip (NO SILENT
      CAPS).
      done-when: `python -m pytest tests/test_conj_section_template.py -q`
      -> `0 failed`, including the overrun case

## Phase 7 — operator-authored plugins from the home directory

- [ ] 22. (S3.1) Add home-directory loading from
      `<provider_state_dir>/conj_plugins/`, mirroring
      `model_profiles/registry.py::profiles_root`.
      done-when: `python -m pytest tests/test_conj_section_home.py -q`
      -> `0 failed`, including "a harness with no plugin directory has
      exactly the seeded set"

- [ ] 23. (S3.2) Add the trust-boundary tests: a plugin loads ONLY from
      that directory; no configuration value, model reply or record field
      may name a plugin PATH; an unresolvable id is a typed refusal.
      done-when: `python -m pytest tests/test_conj_section_home.py -k trust -q`
      -> `0 failed`

- [ ] 24. (S3.4) [COMMIT] Add the disclosure path: an unloadable plugin
      file yields a typed notice naming file and error, and the run
      continues with what loaded (disclose, never die).
      done-when: `python -m pytest tests/test_conj_section_home.py -k disclos -q`
      -> `0 failed`

## Phase 8 — the form (C1 only)

- [ ] 25. (S8.2) Make the role-prompt wrapper selectable: `roles.py`
      `TEMPLATES`/`COMPACT_TEMPLATES` become a registered, versioned
      template registry; the shipped default reproduces today's bytes.
      done-when: `python -m pytest tests/test_role_prompt_registry.py -q`
      -> `0 failed`, including a byte-identical-default case

- [ ] 26. (S8.2, S9.4, S13-decision-2) Add form SELECTION among the three
      ids ALREADY in every `Literal` — `conjecturer.turn.v6`,
      `conjecturer.turn.v7`, `conjecturer.atomic-candidate.v1` — by
      argument/env only. **No new contract id; `run_manifest.py`,
      `qualification.py`, `cli/doctor.py` and `verification/` are NOT
      opened.**
      done-when: `git diff --name-only <base>..HEAD` contains none of
      `src/deepreason/run_manifest.py`, `src/deepreason/qualification.py`,
      `src/deepreason/cli/doctor.py`,
      `src/deepreason/verification/report.py`

- [ ] 27. (S9.1, S9.2, S9.3) [COMMIT] Add the optional
      `preferred_conjecturer_form` to the model-profile document, the
      four-step resolution order, and the typed NOTICE on selection
      (never a refusal — the ungated-seats law). Create
      `docs/map/SEAM-llm-x-model-profiles.md` in the SAME commit
      (`PARKED.md` P3's first half; this step is what crosses it).
      done-when: `python -m pytest tests/test_model_profile_form_selection.py -q`
      -> `0 failed`, AND `python tools/docs_verify.py --links` -> 0
      unresolved

- [ ] 28. (S8.4, S8.5) Add normalisations N1-N5 to `validate_value`, each
      recording its rule id in the attempt's diagnostic trail. N1 and N3
      already partly ship — extend, do not duplicate.
      done-when: `python -m pytest tests/test_wire_normalisation.py -q`
      -> `0 failed`

- [ ] 29. (S11.4) [COMMIT] Prove leniency changes no verdict: for each of
      N1-N5, a strict reply and its loosened twin compile to the SAME
      canonical artifact byte-for-byte.
      done-when: `python -m pytest tests/test_wire_normalisation.py -k identical -q`
      -> `0 failed`, five cases

## Phase 9 — the architecture tests (the modularity law's "enforced")

- [ ] 30. (S11.1) `tests/test_conj_section_architecture.py` limb 1: RED if
      `render_conj_pack` constructs a section other than through
      `resolve_section_plugin` — a pinned call COUNT, the shape
      `DR-INV-render-layout` uses for its `_head` bypass trap.
      done-when: the test passes on the tree AND is pasted RED against a
      deliberately bypassing mutation

- [ ] 31. (S11.2) Limb 2: register a brand-new plugin from a temp home
      directory, render a pack with it, assert its text appears and its
      receipt is written — touching no file under `src/`.
      done-when: `python -m pytest tests/test_conj_section_architecture.py -k no_source_edit -q`
      -> `0 failed`

- [ ] 32. (S11.3) Limb 3: shape buys nothing (`M9`, the formalism-optional
      law). RED if `plugin_id`, `layout_id`, `form_id` or any
      `SectionReceiptV1` field appears anywhere in `scheduler/`,
      `adjudication/` or `rules/` admission, rank or acceptance paths.
      done-when: `python -m pytest tests/test_conj_section_architecture.py -k shape_buys_nothing -q`
      -> `0 failed`

- [ ] 33. (S11) [COMMIT] Create `docs/map/INV-conj-section-plugins.md`
      (SPEC §9's three layers + these four checks) and
      `docs/map/REC-add-a-section-plugin.md`, and add both to
      `INDEX.md`. Every claim carries a column-0 `check:` that can fail.
      done-when: `python tools/docs_verify.py --audit` -> 0 findings

## Phase 10 — the experiment recipe, committed as an instrument

- [ ] 34. (S12.0, S12.1) Write `PREREG.md` for STEP 1 (hold the form, vary
      ONE brief parameter), on the shape of
      `experiments/2026-08-28-diversity-generation/PREREG.md`: arms,
      frozen questions and digests, budget, and the outcome measures
      chosen BEFORE any call.
      done-when: file exists containing `## §6 — Outcome measures (frozen
      before any call)` and the four measures of SPEC S12.3

- [ ] 35. (S12.3) Add `analyse_form_arms.py` computing admission rate
      (re-running `census_conjecturer_failures.py` over the new roots) and
      M1/M2/M3 by calling the committed diversity instrument — not a
      reimplementation of it.
      done-when: `python .../analyse_form_arms.py --self-test` -> `ok`

- [ ] 36. (S12.4, S12.5) [COMMIT] Add the two binding rules as CHECKS, not
      prose: provenance fields (`layout_id`, `form_id`) are OMITTED
      ENTIRELY from any judged render — not blanked; and no model
      self-reported number enters any metric, rank, filter or ordering.
      done-when: `python -m pytest tests/test_form_experiment_binding.py -q`
      -> `0 failed`, both rules pasted RED against a violating mutation

## Phase 11 — the gate and delivery

- [ ] 37. (S13) Frozen-surface disclosure: re-run the gate's own
      instrument over the ACTUAL diff and paste the result.
      done-when: `python tools/blast_radius.py --files $(git diff
      --name-only <base>..HEAD -- 'src/*') --against <base>` ->
      `"frozen_surface_verdict": "CLEAR"`. **Anything else is a STOP**:
      request the grant in a document before proceeding.

- [ ] 38. (all) Diff budget check (SPEC §15, ~900 lines of `src/`).
      done-when: `python tools/diff_budget.py` -> within budget, or a
      stated, operator-visible overrun

- [ ] 39. (all) Map check, FULL mode — `--fast` reuses cached results and
      CANNOT catch a document a `src/` change just broke
      (`dr-drive-harness` §4). Run on an otherwise idle box: never
      concurrently with the gate (§5b).
      done-when: `python tools/docs_verify.py` -> `0 failed`, AND
      `python tools/docs_verify.py --audit` -> 0 findings

- [ ] 40. (all) Full gate, alone on the box.
      done-when: `python -m pytest tests/ -q -n 4` -> output ends
      `N passed, 0 failed` (paste it). Compare N against
      `docs/AUDIT_BASELINES.md`; 0 failed is the only acceptable result
      and no assertion is weakened to get there.

- [ ] 41. (all) [COMMIT] Tranche commit: one change, message stating what,
      why, the live evidence, and `Full gate: N passed, 0 failed`.
      done-when: `git log -1 --stat` shows the tranche and the message
      carries the gate line

- [ ] 42. (all) Push with retry (2s/4s/8s/16s backoff) and confirm clean.
      done-when: `git status --porcelain` is EMPTY and
      `git rev-parse HEAD origin/claude/conjecturer-pluggable-interface-bnyrhx`
      prints the same sha twice

- [ ] 43. (all) Route to `dr-validate-change` (VALIDATION.md), then
      `dr-deliver-change` (DELIVERY.md with the R-by-R reconciliation).
      **The live experiment of Phase 10 runs in its OWN tranche** — a
      multi-step programme runs one step per tranche (`dr-drive-harness`
      §6), and finishing this one early is not a reason to start it.
      done-when: VALIDATION.md exists with verdict PASS

---

## Coverage

Every S-number has at least one step: S1 (6,7,11,15), S1.1-1.4 (6),
S1.5 (11), S1.6 (12), S1.7 (13), S2 (8), S3 (22,23,24), S4 (20,21),
S5 (17), S6 (17), S7 (18,19), S8 (25,26,28), S9 (26,27), S10a/§9 (9,33),
S10 (9,10,14), S10.4 (2,3,15), S11 (30,31,32,33), S12 (34,35,36),
S13 (4,5,15,27,33).

## Not in this checklist, on purpose

- Road C2 (an open form registry, a NEW contract id) — SPEC §0, three
  frozen surfaces, needs its own grant.
- The critic seat — SPEC §14 names the seam and designs nothing.
- Episodes beyond the registered empty slot — `R13`.
- `PARKED.md` P1, P2 and the `model-profiles x scheduler` half of P3.
