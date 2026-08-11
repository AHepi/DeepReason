# Checklist for: sub-tranche (ii) — schema-first intake tool (S3)

State: next=done blockers=none
Map ids: `SUB-manifest.md` owns `run_manifest.py` (frozen, NOT touched
— `IntakeFormV1` is standalone per A3). No dedicated map document for
`intake_form.py`/CLI/MCP glue.
Re-read REQUEST.md + SPEC.md (incl. Addenda 1-2) before every step.
Execute strictly in order. One step per `dr-execute-step` invocation.

- [x] 1. (S3) `src/deepreason/intake_form.py`: `IntakeFormV1`.
      DONE: `question` in `model_fields`, confirmed.
- [x] 2. (S2, S3) 3 new catalog entries.
      DONE: `len(CATALOG) == 47`.
- [x] 3. (S3) [COMMIT] `tests/test_intake_form.py`.
      DONE: commit `67a1dc72c`, `17 passed`.
- [x] 4. (S3) `deepreason validate-intake FILE`.
      DONE: missing `question` -> exit 1, human-readable; valid file
      -> exit 0, "OK".
- [x] 5. (S3) [COMMIT] CLI command.
      DONE: commit `8500630a1`.
- [x] 6. (S3) MCP `validate_intake` tool + dispatch.
      DONE (with a design correction — see Residue below): initial
      registration used the FULL `IntakeFormV1.model_json_schema()`,
      which the full gate (step 14) caught as a real violation of the
      closed MCP facade's own tested boundary (Part A — provider,
      `credential_env`, etc. — must never appear in ANY MCP tool
      schema). Fixed same day, same sub-tranche: added
      `intake_form.HOST_OWNED_FIELDS` (one shared list, also adopted by
      `render_form_dr1.py`, replacing what had been two independent
      copies) and `intake_form.mcp_safe_schema()`, which
      `mcp_server.py`'s `_intake_form_schema()` now uses. Verified: a
      `credential_env` key submitted through `call_tool` is rejected
      BEFORE dispatch reaches any handler code (`_validate_mcp_input`'s
      existing `additionalProperties: false` enforcement), commit
      `d5fa9ae07`.
- [x] 7. (S3) Compute new MCP schema sha256, update both wheel-smoke
      pins.
      DONE, TWICE: once for the initial (later-corrected) schema, once
      more after step 6's fix (`954209256fbffef0fdc6ab5c85d274ba36b67e084c4c6c55f38f864101384c02`
      is the final value, both files match, confirmed by direct
      extraction not eyeballing).
- [x] 8. (S3) [COMMIT] MCP tool + smoke pins together.
      DONE: commit `a843916ff` (initial), `d5fa9ae07` (corrected).
- [x] 9. (S3) `python scripts/wheel_smoke.py`.
      DONE, TWICE (before and after step 6's fix): both real
      build-and-install runs passed; "wheel smoke passed: isolated
      V6-only contents, clean imports, exact entry points, module
      parity, MCP registration, and exact MCP schemas".
- [x] 10. (S3) `tools/render_form_dr1.py`.
      DONE: syntax-checked; one bug found and fixed during writing
      (a blind find-replace for prose arrows corrupted 5 Python
      function-return-type arrows into a syntax error — caught by
      `ast.parse` immediately, fixed before any commit).
- [x] 11. (S3) Regenerate FORM_DR1 Parts A/B1/D.
      DONE: `--check` exits 0. One quality fix during writing: D5's
      three fields (dossier/attach/allow_partial) initially rendered
      alphabetically by field name; changed the sort tiebreak to
      declaration order for a more natural reading order.
- [x] 12. (S3) [COMMIT] Generator + regenerated FORM_DR1.
      DONE: commit `83632e1dc`.
- [x] 13. (all) Subsystem ring: `148 passed in 86.48s`.
- [x] 14. (all) Full gate — ran TWICE:
      First run: `4 failed, 3451 passed, 7 skipped in 627.15s` — 3 NEW
      failures beyond the known pre-existing one
      (`tests/test_mcp.py::test_initialize_and_tools_list_are_truthful_and_exact`,
      `tests/test_mcp_help.py::
      test_help_tools_are_listed_with_exact_closed_schemas_and_annotations`,
      `tests/test_public_v6_facade.py::
      test_mcp_schemas_expose_no_path_manifest_provider_or_credential_authority`).
      Investigated each (not patched blind): the first two were two
      MORE pinned tool-name sets this program's own Item 1 audit never
      found (`tests/test_mcp.py` `SUPPORTED_TOOLS`,
      `tests/test_mcp_help.py` `SUPPORTED_TOOL_NAMES` — four pin
      locations total for one tool addition, not the two wheel-smoke
      scripts alone); fixed by adding `validate_intake` to both. The
      third was the real design defect step 6 describes, fixed at its
      root (schema filtering), not by weakening the test.
      Second run (after all fixes): `1 failed, 3454 passed, 7 skipped
      in 605.26s` — back to exactly the known pre-existing failure.
- [x] 15. (all) Map check: `docs_verify: 3 failed` — identical to
      baseline both times (full mode, 53 documents, 853 checks — this
      tranche's files are outside `docs/map/`'s scanned corpus).
- [x] 16. (all) Push and confirm clean tree: `git status --porcelain`
      empty, HEAD == origin HEAD (`d5fa9ae07`).

## Residue found this sub-tranche (not in PARKED.md — noted here since
## it belongs to this checklist's own step 6/7, not a future item)

Four separate places pin the MCP tool set/schema
(`scripts/wheel_smoke.py`, `scripts/wheel_operational_smoke.py`,
`tests/test_mcp.py`, `tests/test_mcp_help.py`) — Item 1's sweep/smoke
audit (this program, earlier) checked only the first two. The full
gate is what actually catches all four; an instrument-only check (as
Item 1 was scoped) would have missed the two test-suite pins. Worth
folding into a future sweep/smoke follow-up if the operator wants
`tools/root_sweep.py`-style coverage of test-suite-embedded pins too —
not actioned here, this sub-tranche's own gate already caught and fixed
both.
