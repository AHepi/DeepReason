# CHECKLIST — one step, one done-criterion

State: step 10 next.
Spec: SPEC.md. Request: REQUEST.md.

- [x] 1. S1 — `src/deepreason/llm/layout.py`: `RenderLayoutPolicyV1`, the two
      registered policies, `resolve_layout_policy`, `register_layout_policy`,
      envelope validators, typed unknown-id refusal.
      DONE WHEN: A1's four assertions pass in a new
      `tests/test_render_layout_policy.py::test_the_policy_registry_resolves_and_refuses`.

- [x] 2. S2 — question-last on `render_conj_pack` and `render_crit_pack`.
      DONE WHEN: A2 passes, RED against the pre-change tree, and the predicted
      minimal update to
      `test_the_withheld_notice_sorts_last_and_leaves_the_cache_prefix_intact`
      is made with the map sentence in the same commit.

- [x] 3. S3 — question-last on the two `informal/trial.py` judge packs.
      DONE WHEN: A3 passes, RED against the pre-change tree.

- [x] 4. S4 — carry-forward: `_distilled` replaces `_head` under the policy,
      the in-band cap marker and retrieval note, the `live-neighbourhood`
      section, the `superseded-conjectures` section defaulting to absent.
      DONE WHEN: A4 passes, RED against the pre-change tree.

- [x] 5. S5 — head block merging in `render_role_prompt`'s compact branch.
      DONE WHEN: A5 passes, RED against the pre-change tree.

- [x] 6. S6 — the instruction-count guard.
      DONE WHEN: A6 passes and the mutated-template run is RED.

- [x] 7. S7 — the three-limb architecture test.
      DONE WHEN: all three limbs pass and limb 1 is RED against a consumer
      patched to ignore its `layout` argument.

- [x] 8. Map — `CON-packs-and-token-economy.md` gains the new rules and their
      executable checks; new `docs/map/INV-render-layout.md`; `INDEX.md`
      routes to it.
      DONE WHEN: `python tools/docs_verify.py` full run shows no delta beyond
      C5's four known failures, and `--audit` accepts the new checks.

- [x] 9. S8 — PARKED.md with R3's ready-to-send calibration prompt and the
      two disclosed follow-ups (the qualification-probe divergence, the
      task-frame-only seats).
      DONE WHEN: PARKED.md committed with one fenced, paste-ready prompt.

- [ ] 10. S9 — the proof set: blast_radius verdict, verify_root before/after,
      qualification subject digest before/after, census before/after, full
      gate.
      DONE WHEN: every artifact is under `proof/` and VALIDATION.md can cite
      it.
