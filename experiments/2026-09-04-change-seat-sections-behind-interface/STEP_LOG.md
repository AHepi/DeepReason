# STEP LOG — done-criterion outputs, pasted

Phase: `dr-execute-step`, one entry per checklist step. A step is checked only
with its output here.

---

## Step 1 — baseline (pre-change)

    $ python -m pytest tests/test_conj_pack_legacy_golden.py \
        tests/test_crit_pack_legacy_golden.py tests/test_seat_section_*.py -q
    90 passed in 1.86s

## Steps 2-4 — the source layer

    $ python -c "import ast;ast.parse(open('.../seat_sources.py').read())"
    parses

## Steps 5-9 — the thirteen sources and the bundle

    $ python -c "... resolve_seat_source_bundle('conjecturer') ..."
    conj-sources.legacy-v0 13
      pre_contract ['dr.src.open_criticism']
      render ['dr.src.frozen_evidence', 'dr.src.citable_evidence',
              'dr.src.frame_slice', 'dr.src.frame_crisis',
              'dr.src.capability_result', 'dr.src.scratch_context',
              'dr.src.generation_context', 'dr.src.reference_menus']
      post_allocation_context ['dr.src.post.scratch_render']
      post_allocation ['dr.src.post.sealed_simulation',
                       'dr.src.post.scratch_workshop']
      post_allocation_after_aliases ['dr.src.post.reference_menus']

## Step 10 — the renderer takes `supplied`

    $ python -m pytest tests/test_conj_pack_legacy_golden.py \
        tests/test_crit_pack_legacy_golden.py -q
    15 passed in 0.43s
    $ git diff --stat tests/fixtures/
    (empty — no fixture touched)

## Step 11 — the caller

    $ python -m pytest tests/test_conj_pack_legacy_golden.py \
        tests/test_conjecturer_turn_v4.py tests/test_conjecture_scratch_context_v4.py \
        tests/test_reference_menu.py tests/test_p4_citable_evidence.py \
        tests/test_evidence_citations.py tests/test_discharge_contract.py \
        tests/test_discharge_law_line.py tests/test_frame_render.py \
        tests/test_seat_section_*.py tests/test_crit_pack_legacy_golden.py -q
    240 passed in 19.01s

**Three location-pinning tests were re-pointed, none weakened.** Each asserted
WHERE a computation lives, and the computation moved; each still fails on the
regression it was written for.

| test | what it pinned | what it pins now |
|---|---|---|
| `test_discharge_contract.py::test_no_consumer_reaches_past_the_interface` | the channel reaches the tree through exactly TWO files | exactly THREE, the third named and explained |
| `test_reference_menu.py::test_a_pre_v6_conjecture_pack_carries_no_v6_menu` | every `menu_renders_for` call in `conj.py` sits under an `active_v6` guard | every menu-building SOURCE consults `active_v6` |
| `test_frame_render.py::test_both_rules_put_the_frame_in_the_pack_they_dispatch` | all three `render_*_pack` call sites pass both frame halves | the critic's two still do; the conjecturer's is asserted over the source bundle |

## Steps 12-14 — the proofs

    $ python -m pytest tests/test_seat_section_sources.py -q
    26 passed in 0.93s

## Step 15 — R7 mutation-proven (R9)

The plant: a generation-side name (`bundle_id`) read inside
`rules/act.py::browser_evidence`, which is an authority function by that test's
own definition (it mints an artifact).

    --- MUTATION: generation-side name inside rules/act.py::browser_evidence ---
    >       assert not offenders, offenders
    E       AssertionError: ['src/deepreason/rules/act.py::browser_evidence: bundle_id']
    FAILED tests/test_seat_section_architecture.py::test_limb3_shape_buys_nothing_on_the_rules_authority_paths
    1 failed, 7 passed in 0.98s
    --- RESTORED ---
    8 passed in 0.91s

A first attempt planted the same read inside `rules/conj.py::conj` and the test
stayed green. That is not a hole: `conj` DISPATCHES, and the check is scoped to
functions that decide standing, deliberately, because a dispatch site
legitimately names its own seat. Recorded because the first reading of a green
mutation is "the check is broken", and here it was the plant that was wrong.

## Step 16 — the map

`docs_verify --links`: 0 dangling references, 79 documents.
Full `docs_verify` and the boundary gate are in `VALIDATION.md`.

**One finding the map produced that no test would have.** The source layer's
first home was `src/deepreason/llm/seat_sources.py`, beside the plugins it
feeds. `DR-SUB-llm`'s check went red: `llm/` may not import the harness, the
scheduler, the rules, the adjudicator or the amendment machinery, so that a
transport bug cannot become an adjudication bug. A source's whole job is to read
the record. The layer moved to its own package, `deepreason.seat_sources`, and
the arrow now points the safe way. The trap is recorded in the seam document.
