# Checklist for: sub-tranche (ii) — schema-first intake tool (S3)

State: next=1 blockers=none
Map ids: `SUB-manifest.md` owns `run_manifest.py` (frozen, NOT touched
— `IntakeFormV1` is standalone per A3). No dedicated map document for
`intake_form.py`/CLI/MCP glue, same reasoning as sub-tranche (i)'s
header.
Re-read REQUEST.md + SPEC.md (incl. Addendum 2) before every step.
Execute strictly in order. One step per `dr-execute-step` invocation.

- [ ] 1. (S3) Write `src/deepreason/intake_form.py`: `IntakeFormV1
      (BaseModel)` with Part A fields (all `str | int | None`,
      optional — Part A is filed once via `deepreason setup`, not
      necessarily present in every intake file), Part B1 `seats:
      dict[str, str] | None` (GROUP=PROFILE), Part D mandatory fields
      (`question: str`, `cycles: int | None`, `token_budget: int |
      None`, `shallow: bool = False`, `dossier: str | None`, `attach:
      list[str] | None`, `allow_partial: bool = False`). A
      `field_validator` on `seats` implementing B1a (using
      `seat_bindings.GROUP_ALIASES`) and `field_validator`s on
      `cycles`/`token_budget` implementing D2/D3 (using
      `preparation.PUBLIC_MAX_CYCLES`/`PUBLIC_MAX_TOKEN_BUDGET`), each
      raising a `ValueError` string-formatted as `f"{CODE}: {message}"`
      matching the codebase's existing convention (`QualificationError`
      etc.) so violations can route through the error catalog (S2).
      done-when: `python -c "from deepreason.intake_form import
      IntakeFormV1; assert 'question' in IntakeFormV1.model_fields"`.
- [ ] 2. (S2, S3) Add 3 new catalog entries to `error_catalog.py`:
      `INTAKE_SEAT_CONFLICT`, `INTAKE_CYCLES_CEILING_EXCEEDED`,
      `INTAKE_TOKEN_BUDGET_CEILING_EXCEEDED` — same `ErrorCatalogEntry`
      shape as the 44 existing entries.
      done-when: `python -c "from deepreason.error_catalog import
      CATALOG; assert len(CATALOG) == 47"`.
- [ ] 3. (S3) [COMMIT] Write `tests/test_intake_form.py`: a valid
      minimal file passes; a missing `question` fails; a seat conflict
      (`{"conjecture": "a", "simulation": "b"}`) raises with code
      `INTAKE_SEAT_CONFLICT`; `cycles=13` raises
      `INTAKE_CYCLES_CEILING_EXCEEDED`; `token_budget=200001` raises
      `INTAKE_TOKEN_BUDGET_CEILING_EXCEEDED`;
      `IntakeFormV1.model_json_schema()` returns a dict with
      `"question"` in `properties`.
      done-when: `python -m pytest tests/test_intake_form.py
      tests/test_error_catalog.py -q` passes; commit + push.
- [ ] 4. (S3) Add `deepreason validate-intake FILE` CLI command
      (`cli/main.py`): loads JSON (or YAML if `pyyaml` available and
      extension is `.yaml`/`.yml`, else JSON-only — check what's
      already a dependency before adding one), calls
      `IntakeFormV1.model_validate`, on `pydantic.ValidationError`
      prints each violation (parsing a `CODE: message` prefix from
      custom-validator errors and rendering via `error_catalog.lookup`
      when present; falling back to Pydantic's own `loc`/`msg` for
      plain "missing field" errors), exits 1; on success prints "OK"
      and exits 0.
      done-when: a JSON file missing `question` -> non-zero exit,
      human-readable message; a valid minimal file -> exit 0, "OK".
- [ ] 5. (S3) [COMMIT] Commit the CLI command.
      done-when: `git push` succeeds.
- [ ] 6. (S3) Add `validate_intake` to `mcp_server.py`'s `_run_tools()`
      list (inputSchema derived from `IntakeFormV1.model_json_schema()`
      trimmed to `additionalProperties: False`) and `_RUN_TOOL_NAMES`;
      wire dispatch in `call_tool` (before the `_admit_v6_root` line,
      since it needs no `run_id`) calling the SAME
      `IntakeFormV1.model_validate` path the CLI command uses.
      done-when: `python -c "from deepreason.mcp_server import _tools;
      assert 'validate_intake' in {t['name'] for t in _tools()}"`.
- [ ] 7. (S3) Compute the new MCP schema sha256 locally (no wheel build
      needed — `mcp_server.py`'s `tools/list` handler returns `_tools()`
      verbatim): `python3 -c "import json,hashlib; from
      deepreason.mcp_server import _tools; print(len(_tools()));
      print(hashlib.sha256(json.dumps(_tools(), sort_keys=True,
      separators=(',',':')).encode()).hexdigest())"` and update BOTH
      `scripts/wheel_smoke.py` and
      `scripts/wheel_operational_smoke.py`'s `EXPECTED_MCP_TOOLS`
      (add `"validate_intake"`, 21 total) and
      `EXPECTED_MCP_SCHEMA_SHA256` (the computed hash) in the SAME
      commit as step 6.
      done-when: both files' `EXPECTED_MCP_TOOLS` contain
      `"validate_intake"` and both share the identical new sha256
      string.
- [ ] 8. (S3) [COMMIT] Commit the MCP tool + both smoke pins together.
      done-when: `git push` succeeds.
- [ ] 9. (S3) Run `python scripts/wheel_smoke.py` (builds and installs
      the wheel fresh, verifies the pins actually match a real
      install — the local hash computation in step 7 used the
      editable install, not a built wheel, so this step is the real
      proof).
      done-when: exits 0, paste the output.
- [ ] 10. (S3) Write `tools/render_form_dr1.py`: reads
      `IntakeFormV1`'s fields (name, type, description via Pydantic
      `Field(description=...)`) and renders Parts A/B1/D of
      `FORM_DR1_RUN_APPLICATION.md` from them; `--check` mode diffs
      against the committed file and exits 1 on any difference (0 if
      identical); default mode writes the file.
      done-when: `python -c "import ast; ast.parse(open(
      'tools/render_form_dr1.py').read())"` exits 0.
- [ ] 11. (S3) Regenerate `FORM_DR1_RUN_APPLICATION.md`'s Parts A/B1/D
      sections from the schema (Parts B2-H remain hand-maintained
      prose — out of scope per SPEC.md's explicit "Out of scope:
      rewriting FORM_DR1's CONTENT" for the `†`-marked/unmodeled
      parts); `python tools/render_form_dr1.py --check` exits 0
      against the result.
      done-when: `python tools/render_form_dr1.py --check` exits 0
      (paste output).
- [ ] 12. (S3) [COMMIT] Commit the generator + regenerated FORM_DR1
      sections together.
      done-when: `git push` succeeds.
- [ ] 13. (all) Subsystem ring: `python -m pytest
      tests/test_intake_form.py tests/test_error_catalog.py
      tests/test_cli*.py -q`
      done-when: 0 failed (paste summary).
- [ ] 14. (all) Full gate: `python -m pytest tests/ -q -n 4`
      done-when: failure count matches the program's established
      baseline (1: `test_bronze_report.py`, confirmed unrelated) —
      paste the full line.
- [ ] 15. (all) Map check: `python tools/docs_verify.py`
      done-when: failure count unchanged from baseline (3, all
      `CON-run-identity.md`).
- [ ] 16. (all) [COMMIT] Push and confirm clean tree.
      done-when: `git status --porcelain` empty AND
      `git rev-parse HEAD` equals `git rev-parse origin/<branch>`.
