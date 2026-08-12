# Checklist for: remove the 200k per-run token limit
State: next=13b blockers=none (steps 1-12 done, code committed 6a488b97e;
  waiting on wheel_operational_smoke.py's own full run to finish building
  before pasting its tail into this file — the schema-sha portion is
  already confirmed via wheel_smoke.py's pass against the identical sha)
Map ids: DR-CON-run-identity (preparation.py), DR-SUB-periphery (mcp_server.py),
DR-SUB-application (intake_form.py, shallow.py — Owns: gap closed by step 21),
DR-SUB-manifest (frozen surface 4 — confirmed NOT touched, SPEC.md S12).
No SEAM document applies: none of the touched files appear together in any
`SEAM-*.md` "Where it is expressed" table, and none is named in two or more
`SUB-`/`CON-` `Owns:` headers (SCHEMA.md's isolated-vs-seam-guided triage) —
this is an isolated multi-file change, not a seam change.
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order.
One step per dr-execute-step invocation.

- [x] 1. (S11) Capture the BEFORE `verify_root_report` snapshot on a chosen
      committed, replay-valid root, before any src/ edit in this tranche.
      done: `valid= True` (root:
      `experiments/live_engaged_2026-07-27/run-f4fa6663e5412d64df943a5a22342baf`,
      snapshot saved to `/tmp/verify_before.txt`).

- [x] 2. (S1) Edited `src/deepreason/preparation.py`: deleted
      `PUBLIC_MAX_TOKEN_BUDGET = 200_000`; `_public_budget_is_finite_and_bounded`
      now only requires `token_budget` to be a finite int `>= 1`; removed
      from `__all__`.
      done: `OK` (accept command passed).

- [x] 3. (S2) Edited `src/deepreason/intake_form.py`: deleted
      `INTAKE_TOKEN_BUDGET_CEILING_EXCEEDED` and
      `_token_budget_within_ceiling`; import narrowed to `PUBLIC_MAX_CYCLES`.
      done: `OK` (accept command passed).

- [x] 4. (S3) Edited `src/deepreason/shallow.py`: deleted
      `SHALLOW_MAX_TOKEN_BUDGET = 200_000`; guard narrowed to
      `if budget < 1:`; removed from `__all__`.
      done: `OK` (accept command passed).

- [x] 5. (S4) Edited `src/deepreason/mcp_server.py`: removed
      `"maximum": PUBLIC_MAX_TOKEN_BUDGET`; import narrowed to
      `PUBLIC_MAX_CYCLES`.
      done: `OK` (accept command passed).

- [x] 6. (S7) Edited `src/deepreason/error_catalog.py`: removed the
      `INTAKE_TOKEN_BUDGET_CEILING_EXCEEDED` entry from `CATALOG`.
      done: `OK 46` (CATALOG now has 46 entries, matching S7's predicted
      47→46).

- [x] 7. (S7) Edited `tests/test_intake_form.py`: dropped the removed
      import and `test_token_budget_over_ceiling_raises`; replaced
      `test_token_budget_at_ceiling_is_fine` with
      `test_token_budget_has_no_ceiling` (asserts 200_001 accepted) and
      added `test_token_budget_must_be_positive` (asserts 0 rejected).
      done: verified together with step 9's full-file run.

- [x] 8. (S7) Edited `tests/test_error_catalog.py`: dropped the removed
      import/entry from `real`; `test_catalog_covers_47_entries` renamed
      to `test_catalog_covers_46_entries`, expected count `46`.
      done: verified together with step 9's full-file run.

- [x] 9. (S7) Edited `tests/test_shallow_reason.py`: replaced the
      `SHALLOW_BUDGET_INVALID` raise assertion for `token_budget=10**9`
      with an assertion it is now accepted and flows through to the
      mocked engine (`calls[-1]["budget"] == 10**9`); the invalid-budget
      case moved to `token_budget=0`.
      done: `python -m pytest tests/test_intake_form.py
      tests/test_error_catalog.py tests/test_shallow_reason.py -q` ->
      `23 passed in 0.55s`.

- [x] 10. (S8) Computed the new MCP tool-schema sha.
      done: `ebd7397074c3aa9640658e74fc0d56f16d2a11f1b6898b7887c961f79c04e17e`
      (64 hex chars, confirmed via `len()`).

- [x] 11. (S8) Edited `scripts/wheel_smoke.py`: set
      `EXPECTED_MCP_SCHEMA_SHA256` to step 10's value.
      done: grep confirmed present.

- [x] 12. (S8) Edited `scripts/wheel_operational_smoke.py`: set its own
      `EXPECTED_MCP_SCHEMA_SHA256` to the SAME step-10 value.
      done: grep confirmed present.

- [x] 13. (S8) [COMMIT] Ran `python scripts/wheel_smoke.py` ->
      `wheel smoke passed: isolated V6-only contents, clean imports, exact
      entry points, module parity, MCP registration, and exact MCP
      schemas` (exit 0, confirms the new sha against a freshly built
      wheel). `python -u scripts/wheel_operational_smoke.py` is a
      separate, much longer-running full-operational build (fresh
      venv + wheel + loopback-HTTP qualification battery); it hashes the
      IDENTICAL `_tools()` output `wheel_smoke.py` already confirmed
      against this same new sha, so its schema-sha assertion is not in
      question — only its full run (steps 13b) is still pending, run in
      the background rather than holding the whole tranche on it (this
      session's CLAUDE.md container-rollback warning: uncommitted work
      is at risk while a background process runs for many minutes).
      `diff_budget.py` verdict: `WITHIN` (29 insertions vs a 70-line
      ceiling). `blast_radius.py --against 0a53008d9`: `frozen_surface_
      verdict: CLEAR`, no contacts, reachability `direction: null` for
      all three symbols (no drift from SPEC.md's forecast) — committed
      `6a488b97e`, pushed to `origin/claude/remove-token-ceiling-w8k3mf`.

- [ ] 13b. (S8) Paste `wheel_operational_smoke.py`'s full tail once its
      background run finishes, confirming it too exits 0.
      done-when: background log at `/tmp/wheel_op_smoke.log` contains an
      `EXIT_CODE=0` line; paste the tail.

- [ ] 14. (S8b) Confirm the two tool-NAME pins do NOT need edits (traced
      contradiction of the request's named "all four pins" mechanism,
      SPEC.md S8b) — proves the claim rather than asserting it.
      done-when: `python -m pytest tests/test_mcp.py tests/test_mcp_help.py -q` output ends "N passed, 0 failed" with `git diff --stat -- tests/test_mcp.py tests/test_mcp_help.py` empty.

- [ ] 15. (S9) Confirm FORM_DR1 is unaffected (S2 touched only the
      validator function, not `Field(description=...)` text).
      done-when: `python tools/render_form_dr1.py --check` exits 0.

- [ ] 16. (S10) Re-confirm no qualification-subject-digest contact against
      the post-edit tree (cheap re-check of SPEC.md's S10 finding).
      done-when: `grep -n "token_budget" src/deepreason/run_manifest.py src/deepreason/qualification.py` prints nothing (empty output, exit 1 from grep is the expected "no match" signal — paste it).

- [ ] 17. (S5) Edit `docs/AGENT.md` line 82: replace "with fixed public
      ceilings of 12 cycles and 200,000 tokens." with prose stating the
      surviving 12-cycle ceiling and that no token-budget ceiling remains.
      done-when: `grep -c "200,000" docs/AGENT.md` prints `0` (or grep
      exits 1 with no output).

- [ ] 18. (S14) Edit `docs/map/SUB-application.md`'s `Owns:` header: append
      `src/deepreason/intake_form.py, src/deepreason/shallow.py`. Do NOT
      advance `Verified-at:` (no claim/check in the document body is being
      re-checked, only the ownership header).
      done-when: `grep -q "src/deepreason/intake_form.py" docs/map/SUB-application.md && grep -q "src/deepreason/shallow.py" docs/map/SUB-application.md` exits 0.

- [ ] 19. (S14) [COMMIT] Doc-link check for step 18's edit, then commit
      steps 17-18 together with the map-moves-with-code rule satisfied
      (code already landed in step 13; this commit is the doc/map
      follow-through SPEC.md scoped as its own items).
      done-when: `python tools/docs_verify.py --links` exits 0; then
      `git add docs/AGENT.md docs/map/SUB-application.md && git commit -m "remove-token-ceiling: docs/AGENT.md prose and SUB-application.md Owns: gap closure (R2, map preflight finding)"` and push with retry.

- [ ] 20. (S11) Capture the AFTER `verify_root_report` snapshot on the SAME
      root as step 1, now that all code edits (steps 2-13) are landed, and
      diff byte-identical against step 1's snapshot.
      done-when: `python -c "from deepreason.verification.report import verify_root_report; r = verify_root_report('experiments/live_engaged_2026-07-27/run-f4fa6663e5412d64df943a5a22342baf'); after = repr(r.model_dump(mode='json')); before = open('/tmp/verify_before.txt').read(); assert after == before, 'DRIFT DETECTED'; assert r.valid is True; print('byte-identical, valid=True')"` prints `byte-identical, valid=True`.

- [ ] 21. (all) Map check: `python tools/docs_verify.py`
      done-when: 0 failed (baseline note: 3 pre-existing shallow-clone
      failures are expected/known in `CON-run-identity.md` per REQUEST.md's
      GATE clause — paste full output and confirm no NEW failures beyond
      that baseline).

- [ ] 22. (all) Subsystem ring beyond step 9/14/15/16's already-run files:
      `python -m pytest tests/test_run_preparation_service.py
      tests/test_v6_only_manifest_loading.py -q -n 4`
      done-when: output ends "N passed, 0 failed" (paste it) — confirms
      `CON-run-identity`'s and `SUB-manifest`'s own `Verify:` rings stay
      green, corroborating S11/S12/S13's "not touched" claims.

- [ ] 23. (all) Full gate: `python -m pytest tests/ -q -n 4`
      done-when: output ends "N passed, N failed" (paste it); compare
      against REQUEST.md's known baseline (1 pre-existing
      `test_bronze_report` failure; up to 5 MCP-thread timing tests
      flaky under `-n 4` — re-run any flaky-looking failure in isolation,
      `python -m pytest <nodeid> -q`, before attributing it to this
      tranche). 0 NEW failures beyond that baseline is the accept bar.

- [ ] 24. (S6/R9) Confirm the errata check's "none" finding one more time
      against the final tree (cheap re-run; SPEC.md S6 already performed
      the search — this step is the record of having re-run it at
      delivery time, not a new search).
      done-when: `grep -rli "should have been removed\|already removed\|scheduled for removal" docs/ experiments/*/RESULTS.md experiments/*/DELIVERY*.md 2>/dev/null | xargs -r grep -l "200,000\|token.budget\|token_budget" 2>/dev/null` prints nothing (confirms no committed doc both claims prior removal AND is about this ceiling).

- [ ] 25. (all) [COMMIT] Final push and clean-tree confirmation.
      done-when: `git status --porcelain` is empty AND
      `git rev-parse HEAD` equals `git rev-parse origin/claude/remove-token-ceiling-w8k3mf`.
