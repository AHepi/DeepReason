# Checklist for: Rung O1 of the grounded-overlay program — offline retrodiction
State: next=21 blockers=none
Map ids scoped (per SPEC.md's map preflight): DR-INV-frozen-surfaces,
DR-CON-warrants-and-attacks, DR-SUB-adjudication, DR-SUB-verification,
DR-SUB-ontology, DR-SUB-evaluation. No SEAM document names this
tranche's own (not-yet-existing, conditional) `CON-grounded-overlays`;
S16 of SPEC.md defers its creation to a findings-driven decision at
step 19 below.
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in
order. One step per dr-execute-step invocation.

- [x] 1. (S1, S2, S3) SPEC.md committed and pushed; confirm zero `src/`/
      `tests/`/`tools/` diff exists BEFORE any script is written (the
      tripwire's own starting baseline).
      done-when: `git diff --stat origin/claude/monitor-session-handover-63ajqv...HEAD -- src/ tests/ tools/`
      -> empty.
      DONE — empty output confirmed (exit 0, no diff lines).
- [x] 2. (S4) Create `experiments/2026-08-08-change-grounded-overlay-o1/scripts/`
      and a shared `overlay_common.py` module: root-corpus enumeration
      (`sorted({p.parent for p in pathlib.Path("experiments").rglob("log.jsonl")})`,
      matching `tools/root_sweep.py`'s own convention per SPEC.md A7),
      and a thin `open_root(root) -> Harness` wrapper that always passes
      `read_only=True` (so every overlay script imports one audited
      open path instead of five independent call sites).
      done-when: `grep -n "read_only=True" experiments/2026-08-08-change-grounded-overlay-o1/scripts/overlay_common.py`
      -> exit 0, and `python3 -c "import sys; sys.path.insert(0,'experiments/2026-08-08-change-grounded-overlay-o1/scripts'); import overlay_common; print(len(overlay_common.corpus()))"`
      prints a positive integer (paste it).
      DONE — 48 committed roots found under experiments/.
- [x] 3. (S5) Write `scripts/o1a_semantics_diff.py`: per-root node/edge
      count paste, SCC controversy inventory (Tarjan over `att`, filtered
      to SCCs containing a `label0=="suspended"` member), the
      undecided-subgraph reduction, weakly-connected component split,
      per-component node/edge paste, 16-node brute-force cap with a
      typed `TOO_LARGE` result beyond it, preferred-extension
      enumeration for components at or under the cap, and the
      skeptical-accepted-not-grounded id list.
      done-when: `python3 -c "import ast; ast.parse(open('experiments/2026-08-08-change-grounded-overlay-o1/scripts/o1a_semantics_diff.py').read())"`
      -> exit 0 (syntactically valid).
      DONE — syntax OK; additionally sanity-tested `tarjan_scc`,
      `weakly_connected_components`, and `admissible_and_preferred`
      against two known Dung-semantics textbook cases (odd 3-cycle:
      single SCC, one preferred extension = empty set, matching theory
      exactly; even 2-cycle/mutual attack: two singleton SCCs post-WCC-
      split, two preferred extensions {a} and {b}, matching theory
      exactly) — all assertions passed.
- [x] 4. (S6) Synthetic TOO_LARGE guardrail check: a standalone snippet
      (run directly, not via `pytest`) that builds a 20-node odd-attack
      structure and asserts the component-sizing function reports
      TOO_LARGE without attempting brute force, wall-clock bounded
      (paste the elapsed time).
      done-when: the snippet's own printed output includes `TOO_LARGE`
      and an elapsed time under 5 seconds (paste both).
      DONE — `scripts/check_o1a_too_large_guardrail.py` printed
      `TOO_LARGE reported for component size 20 in 0.0002s`.
- [x] 5. (S3, S5, S6) [COMMIT] Commit and push `overlay_common.py` and
      `o1a_semantics_diff.py` plus its guardrail check.
      done-when: pushed, confirmed on origin (retry 2s/4s/8s/16s on
      failure).
- [x] 6. (S7) Write `scripts/o1b_joint_execution_probe.py`: accepted +
      `formally_backed` population, same-problem + exec-oracle +
      identical-entry pairing (the machine-comparable-gate filter),
      excluded-pair counting with reasons, the exact literal-overlap
      CONTRADICTION probe, and the bounded deterministic-fuzz
      dynamic probe reusing `oracle.run`'s own FAIL-path `"got"` field
      (SENTINEL trick, no new execution code) capped at
      `min(FUZZ_N, 32)` samples per pair with a typed `INCONCLUSIVE`
      fallback.
      done-when: `python3 -c "import ast; ast.parse(open('experiments/2026-08-08-change-grounded-overlay-o1/scripts/o1b_joint_execution_probe.py').read())"`
      -> exit 0.
      DONE — syntax OK; import-time sanity check passed
      (`_candidate_inputs`, `_literal_overlap_contradiction` both
      produce correct, JSON-serializable results on hand-built cases;
      a bytes-key bug in the contradiction evidence was caught and
      fixed during this same step, before committing).
- [x] 7. (S7) [COMMIT] Commit and push `o1b_joint_execution_probe.py`.
      done-when: pushed, confirmed on origin.
- [x] 8. (S8) Write `scripts/o1c_floating_foundations.py`: the
      `ground()` predicate (SEED/IMPORT/USER roles), the accepted-only
      dependence subgraph, weakly-connected components, and the
      floating-component flag (no member's transitive closure reaches a
      ground artifact), including the vacuous isolated-artifact case.
      done-when: `python3 -c "import ast; ast.parse(open('experiments/2026-08-08-change-grounded-overlay-o1/scripts/o1c_floating_foundations.py').read())"`
      -> exit 0.
      DONE — syntax OK; `weakly_connected_components` sanity-checked on
      a 3-node/1-edge graph, correctly split into `{a,b}` and `{c}`.
- [x] 9. (S8) [COMMIT] Commit and push `o1c_floating_foundations.py`.
      done-when: pushed, confirmed on origin.
- [x] 10. (S9) Write `scripts/o1d_warrant_sensitivity.py`: per-warrant
      `build_att`/`label0`/`final_labels` recomputation with that
      warrant's carriage removed (both `Artifact.warrants` union and
      explicit `state.carries`), the single-warrant-flip detection per
      accepted artifact, and the flip-count histogram.
      done-when: `python3 -c "import ast; ast.parse(open('experiments/2026-08-08-change-grounded-overlay-o1/scripts/o1d_warrant_sensitivity.py').read())"`
      -> exit 0.
      DONE — syntax OK, module imports cleanly.
- [x] 11. (S9) [COMMIT] Commit and push `o1d_warrant_sensitivity.py`.
      done-when: pushed, confirmed on origin.
- [x] 12. (S10) Write `scripts/run_all_overlays.py`: enumerate the
      corpus once via `overlay_common.corpus()`, run all four overlay
      modules per root, write `overlay_results.jsonl` (one JSON line per
      root) capturing every number named in SPEC.md S5/S7/S8/S9's own
      accept criteria.
      done-when: `python3 -c "import ast; ast.parse(open('experiments/2026-08-08-change-grounded-overlay-o1/scripts/run_all_overlays.py').read())"`
      -> exit 0.
      DONE — syntax OK.
- [x] 13. (S10) [COMMIT] Commit and push `run_all_overlays.py`.
      done-when: pushed, confirmed on origin.
- [x] 14. (S5, S7, S8, S9, S10) Run the driver over the full corpus;
      paste the per-root node/edge counts (O1a's own ordering
      requirement: pasted BEFORE any TOO_LARGE-gated computation is
      trusted) and the wall-clock total.
      done-when: `python3 experiments/2026-08-08-change-grounded-overlay-o1/scripts/run_all_overlays.py`
      exits 0; `wc -l experiments/2026-08-08-change-grounded-overlay-o1/overlay_results.jsonl`
      matches the corpus count from step 2 (paste both numbers).
      DONE — 48/48 roots processed, `overlay_results.jsonl` has 48
      lines (matches step 2's corpus count exactly); wall-clock
      4m6.408s. Before this run, each overlay module was independently
      timed standalone on the full corpus to de-risk the sweep (o1a
      ~fast/bounded by the 16-node cap; o1c fast; o1d fast — every
      accepted artifact's flip-histogram bucket landed at 0 across
      every root, a genuine measured finding, not a script bug; o1b
      fast because `comparable_pairs=0` on every root — spot-checked
      on the largest formally-backed root
      (`live_research_2026-07-29/selfstudy/.../completed-epoch3-...`,
      48 formally-backed artifacts, 1128 excluded pairs) and confirmed
      the exclusion reason is 100% `"not both exec-oracle-class"` —
      this corpus's formally-backed artifacts are predicate:/
      property_oracle:-class, not exec_oracle:-class, so O1b's own
      machine-comparable-gate restriction (SPEC.md A4) excludes the
      whole corpus honestly rather than a bug silently zeroing it).
      A defensive per-root wall-clock/pair-count budget
      (`ROOT_WALLCLOCK_BUDGET_S=60`, `MAX_DYNAMIC_PROBES_PER_ROOT=15`)
      was added to `o1b_joint_execution_probe.py` before this run,
      discovered as a genuine gap while de-risking (SPEC.md S7's own
      "bounded budget" requirement was under-specified in the first
      draft) — a mid-step correction, not scope creep. Confirmed the
      known 11-ERROR baseline (`UnsupportedRunManifestVersionError`)
      matches `docs/map/INV-frozen-surfaces.md`'s own documented sweep
      baseline exactly, cross-validating this tranche's own corpus
      enumeration against the existing instrument.
- [x] 15. (S10) [COMMIT] Commit and push `overlay_results.jsonl`.
      done-when: pushed, confirmed on origin.
- [x] 16. (S11) Write `REPORT.md`: per-root, per-overlay M-numbered rows
      with pasted commands reading back `overlay_results.jsonl` (or
      re-running the relevant script on one root), naming every
      artifact/warrant/commitment id the report's own prose claims
      exist.
      done-when: `test -f experiments/2026-08-08-change-grounded-overlay-o1/REPORT.md`
      -> exit 0; every one of the four overlay sections has >=1
      M-numbered row with a fenced command+output block.
      DONE — REPORT.md has a full 48-row per-root table plus 7
      M-numbered claims (M1-M7), each with a pasted command + real
      output. Headline findings: O1a/O1d both zero-divergence across
      the whole corpus (0 controversy SCCs, 0 skeptical-not-grounded,
      0 single-warrant flips); O1b's machine-comparable-gate excludes
      100% of the corpus's 265 formally-backed pairs (predicate:/
      property_oracle:-class, not exec_oracle:-class); O1c found the
      corpus's one genuine positive catch — 14 multi-node floating
      chains (up to 28 artifacts) across 12 roots, spot-checkable by
      root + member id.
- [x] 17. (S11) [COMMIT] Commit and push `REPORT.md`.
      done-when: pushed, confirmed on origin.
- [x] 18. (S12) Write `RESULTS.md`: honest-ledger segment naming what
      each overlay found (including a genuine zero/negative result
      where that is what the corpus shows), and the residue section
      naming the LLM-consistency-patrol blind spot verbatim plus each
      overlay's own structural limit (per SPEC.md S12's four named
      residue items).
      done-when: `grep -q "consistency patrol" experiments/2026-08-08-change-grounded-overlay-o1/RESULTS.md`
      -> exit 0.
      DONE — grep found the phrase; RESULTS.md also names each
      overlay's own narrower residue.
- [x] 19. (S16) Decide, from REPORT.md/RESULTS.md's actual findings,
      whether a new map document `docs/map/CON-grounded-overlays.md` is
      warranted (SPEC.md's own triage: a durable, reusable concept, not
      a null result). If yes: write it per `docs/map/SCHEMA.md`'s
      anatomy with a `check:` per load-bearing claim, and add it to
      `docs/map/INDEX.md`'s concept table in the SAME commit. If no:
      record the "why not" one-liner in RESULTS.md instead.
      done-when: either `test -f docs/map/CON-grounded-overlays.md` ->
      exit 0 with its checks individually verified passing, or
      RESULTS.md contains a one-line "no new map document" rationale.
      DONE — decided NO new map document: `docs/map/INDEX.md`'s own
      "Coverage, stated honestly" section states the map describes
      `src/deepreason/` only, and `experiments/` tranches are
      "navigated by convention" instead. This rung's scripts own no
      `src/` file and add no `src/` symbol, so a `SCHEMA.md`-anatomy
      `Owns:` header would have nothing real to point at. RESULTS.md's
      own "No new map document" section states the full reasoning.
- [x] 20. (S16) [COMMIT] Commit and push `RESULTS.md` (and the map
      document + `INDEX.md` edit, if step 19 created one).
      done-when: pushed, confirmed on origin.
- [ ] 21. (S14) Record any defect noticed during steps 3-20 in
      PARKED.md with a ready-to-send `dr-set-goal` prompt. If none
      found, state that explicitly in RESULTS.md instead of creating an
      empty PARKED.md.
      done-when: either `test -f experiments/2026-08-08-change-grounded-overlay-o1/PARKED.md`
      -> exit 0 with >=1 entry, or RESULTS.md states "no defects found
      this tranche" (mutually exclusive, one must hold).
- [ ] 22. (S13) Zero-diff tripwire, re-pasted at the boundary (not
      trusted from step 1 alone — the whole tranche ran since then).
      done-when: `git diff --stat origin/claude/monitor-session-handover-63ajqv...HEAD -- src/ tests/ tools/`
      -> empty (paste it).
- [ ] 23. (S13) Map check, ONLY if step 19 created a map document;
      otherwise this step is n/a and is recorded as such.
      done-when: `python tools/docs_verify.py` -> "0 failed";
      `python tools/docs_verify.py --audit` -> 0 findings;
      `python tools/docs_verify.py --links` -> 0 dangling references
      (paste all three), OR RESULTS.md/this line states "n/a — no map
      document created."
- [ ] 24. (S13) Full gate: `python -m pytest tests/ -q -n 4`
      done-when: output ends "N passed, 0 failed" (paste it verbatim).
      Per the task's own stated new baseline (P1/P3 fixed, SPEC.md A3),
      anything red is a STOP: report it plainly in RESULTS.md rather
      than reconciling it into a pre-existing-failure narrative that
      does not actually apply on this branch.
- [ ] 25. (S13) [COMMIT] Commit and push the gate result (folded into
      RESULTS.md if not already captured there).
      done-when: pushed, confirmed on origin.
- [ ] 26. (S15, all) [COMMIT] push and confirm clean tree — the last
      commit before handing off to `dr-validate-change`/
      `dr-deliver-change` (S17).
      done-when: `git status --porcelain` is empty AND
      `git log --oneline -1 origin/claude/grounded-overlay-rung-o1-4hkuoo`
      matches local HEAD.

## Amendments
(none yet — re-planning after a validation failure appends here, never
rewrites checked steps above)
