# Checklist for: remove the 200k per-run token limit
State: next=1 blockers=none
Map ids: DR-CON-run-identity (preparation.py), DR-SUB-periphery (mcp_server.py),
DR-SUB-application (intake_form.py, shallow.py — Owns: gap closed by step 21),
DR-SUB-manifest (frozen surface 4 — confirmed NOT touched, SPEC.md S12).
No SEAM document applies: none of the touched files appear together in any
`SEAM-*.md` "Where it is expressed" table, and none is named in two or more
`SUB-`/`CON-` `Owns:` headers (SCHEMA.md's isolated-vs-seam-guided triage) —
this is an isolated multi-file change, not a seam change.
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order.
One step per dr-execute-step invocation.

- [ ] 1. (S11) Capture the BEFORE `verify_root_report` snapshot on a chosen
      committed, replay-valid root, before any src/ edit in this tranche.
      done-when: `python -c "from deepreason.verification.report import verify_root_report; r = verify_root_report('experiments/live_engaged_2026-07-27/run-f4fa6663e5412d64df943a5a22342baf'); open('/tmp/verify_before.txt','w').write(repr(r.model_dump(mode='json')))"` exits 0 and `r.valid is True` (paste `valid=True`).

- [ ] 2. (S1) Edit `src/deepreason/preparation.py`: delete
      `PUBLIC_MAX_TOKEN_BUDGET = 200_000`; in
      `_public_budget_is_finite_and_bounded`, drop the
      `or self.budget.token_budget > PUBLIC_MAX_TOKEN_BUDGET` branch and its
      mention in the raised message; remove `"PUBLIC_MAX_TOKEN_BUDGET"` from
      `__all__`.
      done-when: `python -c "from deepreason.preparation import RunPreparationRequestV1; r = RunPreparationRequestV1(question='q', budget={'cycles':1,'token_budget':10**9}); assert r.budget.token_budget == 10**9; import deepreason.preparation as p; assert not hasattr(p, 'PUBLIC_MAX_TOKEN_BUDGET')"` exits 0.

- [ ] 3. (S2) Edit `src/deepreason/intake_form.py`: delete
      `INTAKE_TOKEN_BUDGET_CEILING_EXCEEDED` and the
      `_token_budget_within_ceiling` validator; narrow the `preparation`
      import to `PUBLIC_MAX_CYCLES` only.
      done-when: `python -c "from deepreason.intake_form import IntakeFormV1; f = IntakeFormV1(question='q', token_budget=10**9); assert f.token_budget == 10**9; import deepreason.intake_form as m; assert not hasattr(m, 'INTAKE_TOKEN_BUDGET_CEILING_EXCEEDED')"` exits 0.

- [ ] 4. (S3) Edit `src/deepreason/shallow.py`: delete
      `SHALLOW_MAX_TOKEN_BUDGET = 200_000`; narrow the `run_shallow_question`
      guard to `if budget < 1:`; remove `"SHALLOW_MAX_TOKEN_BUDGET"` from
      `__all__`.
      done-when: `python -c "import deepreason.shallow as s; assert not hasattr(s, 'SHALLOW_MAX_TOKEN_BUDGET')"` exits 0.

- [ ] 5. (S4) Edit `src/deepreason/mcp_server.py`: remove
      `"maximum": PUBLIC_MAX_TOKEN_BUDGET` from the `budget.token_budget`
      schema in `_run_tools()`; narrow the `preparation` import to
      `PUBLIC_MAX_CYCLES` only.
      done-when: `python -c "from deepreason.mcp_server import _run_tools; t=[t for t in _run_tools() if t['name']=='start_run'][0]; assert 'maximum' not in t['inputSchema']['properties']['budget']['properties']['token_budget']"` exits 0.

- [ ] 6. (S7) Edit `src/deepreason/error_catalog.py`: remove the
      `_entry("INTAKE_TOKEN_BUDGET_CEILING_EXCEEDED", ...)` block from
      `CATALOG`.
      done-when: `python -c "from deepreason.error_catalog import CATALOG; assert 'INTAKE_TOKEN_BUDGET_CEILING_EXCEEDED' not in CATALOG"` exits 0.

- [ ] 7. (S7) Edit `tests/test_intake_form.py`: drop the
      `INTAKE_TOKEN_BUDGET_CEILING_EXCEEDED` import and
      `test_token_budget_over_ceiling_raises`; replace
      `test_token_budget_at_ceiling_is_fine` with a regression asserting a
      formerly-over-ceiling budget (e.g. `PUBLIC_MAX_TOKEN_BUDGET_LEGACY =
      200_000 + 1` inlined as a literal, since the constant no longer
      exists) is now accepted.
      done-when: file parses and the new/edited tests exist (checked
      together with step 9's full-file run).

- [ ] 8. (S7) Edit `tests/test_error_catalog.py`: drop
      `INTAKE_TOKEN_BUDGET_CEILING_EXCEEDED` from the import and the `real`
      set in `test_catalog_keys_are_real_intake_codes`; change
      `test_catalog_covers_47_entries`'s expected count to `46`.
      done-when: checked together with step 9's full-file run.

- [ ] 9. (S7) Edit `tests/test_shallow_reason.py`: replace the assertion
      that `run_shallow_question("q", token_budget=10**9)` raises
      `SHALLOW_BUDGET_INVALID` with one proving it is now accepted (using
      the file's existing mocked-endpoint fixture pattern, matching how the
      adjacent `SHALLOW_CYCLES_INVALID` case is set up).
      done-when: `python -m pytest tests/test_intake_form.py tests/test_error_catalog.py tests/test_shallow_reason.py -q` output ends "N passed, 0 failed" (paste it).

- [ ] 10. (S8) Compute the new MCP tool-schema sha the same way
      `scripts/wheel_smoke.py::_check_mcp` does (hash of the `tools/list`
      result's `"tools"` array, `sort_keys=True`,
      `separators=(",", ":")`), against the tree as edited by steps 2-5.
      done-when: `python -c "import hashlib, json; from deepreason.mcp_server import _tools; encoded = json.dumps(_tools(), sort_keys=True, separators=(',', ':')).encode(); print(hashlib.sha256(encoded).hexdigest())"` prints a 64-hex-char value (paste it — this is the value steps 11-12 use).

- [ ] 11. (S8) Edit `scripts/wheel_smoke.py`: set
      `EXPECTED_MCP_SCHEMA_SHA256` to step 10's value.
      done-when: `grep -q "$(python -c "import hashlib, json; from deepreason.mcp_server import _tools; print(hashlib.sha256(json.dumps(_tools(), sort_keys=True, separators=(',', ':')).encode()).hexdigest())")" scripts/wheel_smoke.py` exits 0.

- [ ] 12. (S8) Edit `scripts/wheel_operational_smoke.py`: set its own
      `EXPECTED_MCP_SCHEMA_SHA256` to the SAME step-10 value.
      done-when: same grep as step 11 against
      `scripts/wheel_operational_smoke.py`, exits 0.

- [ ] 13. (S8) [COMMIT] Run the wheel smokes for real (they build a fresh
      wheel/venv; no gate runs them automatically, so this tranche must,
      per CLAUDE.md, since it changes the pinned surface).
      done-when: `python scripts/wheel_smoke.py` exits 0 AND `python -u scripts/wheel_operational_smoke.py` exits 0 (paste tail of both). Then commit steps 2-12 together: `git add -A src/deepreason/preparation.py src/deepreason/intake_form.py src/deepreason/shallow.py src/deepreason/mcp_server.py src/deepreason/error_catalog.py tests/test_intake_form.py tests/test_error_catalog.py tests/test_shallow_reason.py scripts/wheel_smoke.py scripts/wheel_operational_smoke.py && git commit -m "remove 200k per-run token ceiling: preparation/intake_form/shallow/mcp_server (R1-R2, R7-R8)"` and push with retry (2s/4s/8s/16s).

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
