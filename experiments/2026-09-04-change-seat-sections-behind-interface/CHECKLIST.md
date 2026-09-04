# CHECKLIST — the nine caller-computed sections move behind the interface

Phase: `dr-plan-steps`. Authority: `SPEC.md` (S1-S7, A1-A10), `REQUEST.md`.
One done-criterion per step; a step is checked only with its output pasted
into `STEP_LOG.md`.

## Group 1 — the baseline that makes byte-identity checkable

- [x] 1. Record the pre-change baseline: both goldens pass, the seam and
      plugin map documents' checks pass, `_next_seq`/log-bytes probe works.
      DONE: `pytest tests/test_conj_pack_legacy_golden.py
      tests/test_crit_pack_legacy_golden.py tests/test_seat_section_*.py -q`
      → 0 failed, and the count recorded.

## Group 2 — the source layer (S1)

- [x] 2. `src/deepreason/llm/seat_sources.py`: request, result, receipt,
      protocol, `SeatSectionSourceError`.
      DONE: `python -c "from deepreason.llm.seat_sources import *"` imports;
      a malformed source is refused with a code.
- [x] 3. Same module: the source registry and the bundle registry, with
      argument/env/default resolution and typed refusals.
      DONE: a round-trip register/resolve, a pinned resolve, an unknown id
      refusal, and an env assignment all demonstrated from one script.
- [x] 4. Same module: `assemble_sources` and `apply_post_allocation`,
      including the `AllocatedPack` re-wrap and the stage vocabulary.
      DONE: a two-source bundle assembles across two stages and a
      post-allocation append returns an `AllocatedPack`.

## Group 3 — the thirteen seeded sources (S4)

- [x] 5. `src/deepreason/llm/seat_source_plugins.py`: the five pure-read
      render-stage sources (`open_criticism`, `frame_slice`, `frame_crisis`,
      `capability_result`, `generation_context`, `scratch_context`).
      DONE: each resolves to the same value the corresponding line of
      `conj.py` produces, on a prepared root.
- [x] 6. The two evidence sources (`frozen_evidence`, `citable_evidence`),
      with `writes_blobs` declared on the first and the receipt CARRIED.
      DONE: on a prepared v6 root with attached evidence, the source's value
      equals `conj.py`'s `frozen_evidence_context` byte for byte.
- [x] 7. `dr.src.reference_menus` (pre-allocation).
      DONE: equals `menu_renders_for(...)` for the same binding.
- [x] 8. The four post-allocation sources (`post.scratch_render`,
      `post.sealed_simulation`, `post.scratch_workshop`,
      `post.reference_menus`).
      DONE: each returns the same text `conj.py` appends today, and the
      substitute source declares its target.
- [x] 9. The shipped bundle `conj-sources.legacy-v0`, registered as the
      conjecturer's default, in the order S4's table states.
      DONE: `resolve_seat_source_bundle("conjecturer")` returns 13 entries
      across 5 stages in that order.

## Group 4 — the renderer and the caller

- [x] 10. `render_conj_pack` gains `supplied:` and takes `reference_menus`
      from it when the argument is absent.
      DONE: both goldens still pass, untouched.
- [x] 11. `rules/conj.py` calls the runner at all five stages and computes
      no section: the nine computations and the four re-wraps are deleted,
      the dossier commit and the alias binding stay.
      DONE: `pytest tests/test_conj_pack_legacy_golden.py
      tests/test_conjecturer_turn_v4.py tests/test_conjecture_scratch_context_v4.py
      tests/test_reference_menu.py tests/test_p4_citable_evidence.py
      tests/test_evidence_citations.py tests/test_discharge_contract.py -q`
      → 0 failed.

## Group 5 — the proofs (S6)

- [x] 12. `tests/test_seat_section_sources.py`: the bundle covers all
      thirteen slots (A2); selection is argument/env only (A7).
      DONE: the file passes and each assertion is shown to fail on a
      planted change.
- [x] 13. The never-appends architecture test (A4, A5), with the planted
      write.
      DONE: passes; and with the planted write registered it goes RED —
      output pasted.
- [x] 14. The no-section-in-rules test (A3/R8), mutation-proven.
      DONE: passes; planting `AllocatedPack` back into `conj.py` goes RED —
      output pasted.
- [x] 15. R7's shape-buys-nothing test still passes and is mutation-proven
      (R9).
      DONE: `pytest tests/test_seat_section_architecture.py -q` → 0 failed;
      a planted seat-name read on an authority path goes RED.

## Group 6 — the map, the gate, the delivery

- [x] 16. Map: `SEAM-packs-and-token-economy-x-rules.md` rewritten for the
      new agreement; `INV-seat-section-plugins.md` cross-referenced; a new
      `INV-seat-section-sources.md`; `REC-add-a-section-plugin.md` step 1
      re-pointed; `INDEX.md` rows. Every check re-derived.
      DONE: `python tools/docs_verify.py` → only the six C4 rows fail;
      `--links` 0 dangling.
- [x] 17. Boundary gate: `pytest tests/ -q -n 4` alone → 0 failed;
      `blast_radius` over the actual diff; `diff_budget` against 1600.
      DONE: all three outputs pasted.
- [x] 18. `VALIDATION.md`, then `PARKED.md` and `DELIVERY.md`; commit and
      push.
      DONE: verdict recorded, R-by-R table complete.

---

## Amendments to the plan, recorded (never silently absorbed)

- **Step 2's home changed.** `src/deepreason/llm/seat_sources.py` became
  `src/deepreason/seat_sources/` (a package with `registry.py`, `shipped.py`
  and an interface `__init__.py`) after `DR-SUB-llm`'s check went red:
  `llm/` may not import the harness side. `VALIDATION.md` §4.1.
- **Step 8 moved four sources, not three.** The fourth post-allocation re-wrap
  is a substitution rather than an append; `SPEC.md` §5 states the decision and
  its reason before any code was written.
- **Step 11 required re-pointing three location-pinning tests.** None weakened;
  the table is in `STEP_LOG.md`.
