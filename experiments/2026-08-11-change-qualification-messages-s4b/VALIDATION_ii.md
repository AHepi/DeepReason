# Validation for: sub-tranche (ii) — schema-first intake tool (S3)

## Acceptance checks

S3, first clause: `deepreason validate-intake <a file missing question>`
-> `question: this field is required.`, exit 1 : PASS (human-readable,
no stack trace, no raw Pydantic jargon).

S3, second clause: `python tools/render_form_dr1.py --check` ->
`/home/user/DeepReason/docs/FORM_DR1_RUN_APPLICATION.md is fresh.`,
exit 0 : PASS.

## Full gate

Ran TWICE this sub-tranche (CHECKLIST_ii.md step 14 has the full
narrative). First run surfaced 3 NEW failures beyond the known
pre-existing one — investigated, not patched blind:

- Two were previously-unknown pinned MCP tool-name sets
  (`tests/test_mcp.py` `SUPPORTED_TOOLS`, `tests/test_mcp_help.py`
  `SUPPORTED_TOOL_NAMES`) this program's own Item 1 sweep/smoke audit
  never found (it checked only the two `scripts/wheel_*.py` pins).
  Fixed by adding `validate_intake` to both.
- One was a REAL design defect:
  `tests/test_public_v6_facade.py::
  test_mcp_schemas_expose_no_path_manifest_provider_or_credential_authority`
  caught that the MCP tool's inputSchema included Part A (`provider`,
  `credential_env`, etc.) — a real violation of the closed MCP
  facade's own stated and TESTED design boundary ("Endpoint models
  never receive MCP tools and cannot select providers, routes,
  policies, credentials"). Fixed at the root: `intake_form.
  HOST_OWNED_FIELDS` + `mcp_safe_schema()` strip Part A from the
  MCP-exposed schema entirely; the CLI's `validate-intake` keeps the
  full schema (a human/developer may legitimately describe their own
  setup). Verified directly (not just by the test passing): a
  `credential_env` key submitted through `call_tool` is rejected by
  `_validate_mcp_input`'s existing `additionalProperties: false`
  enforcement BEFORE dispatch reaches any handler code.

Second (final) run:

    1 failed, 3454 passed, 7 skipped in 605.26s (0:10:05)

The one failure is the confirmed pre-existing `test_bronze_report.py`
census mismatch (unchanged across this entire program). +17 passed vs.
the program's earlier full-gate baseline (3437) = 6 catalog tests
(sub-tranche i) + 11 intake_form tests (this sub-tranche). Verdict:
PASS.

## Record-behavior preservation

n/a — no reader or validator of the append-only record was touched.

## Frozen-surface diff

    git diff --stat ccfe59c3d..HEAD -- src/deepreason/capabilities/state.py \
      src/deepreason/harness.py src/deepreason/invariants.py \
      src/deepreason/run_manifest.py src/deepreason/qualification.py
    (empty)

PASS.

## Packaging-surface check

Packaging surface DID move (a new MCP tool) — smoke owed and run,
twice:

    wheel smoke passed: isolated V6-only contents, clean imports,
    exact entry points, module parity, MCP registration, and exact
    MCP schemas

First run confirmed the corrected schema (post-fix) matches what a
REAL built-and-installed wheel serves over the MCP protocol — not just
what the editable install's `_tools()` returns locally. Both
`scripts/wheel_smoke.py` and `scripts/wheel_operational_smoke.py`
pins (`EXPECTED_MCP_TOOLS`, 21 entries; `EXPECTED_MCP_SCHEMA_SHA256`,
`954209256fbffef0fdc6ab5c85d274ba36b67e084c4c6c55f38f864101384c02`)
updated in the same commit as the corrected schema, per CLAUDE.md's
rule.

## Map

    docs_verify [full]: 53 documents, 853 checks, 4 workers
    docs_verify: 3 failed

Identical to the program's established baseline (`CON-run-identity.md`
shallow-clone failures). PASS.

    docs_verify --audit: 0 finding(s) : PASS
    docs_verify --links: 0 dangling reference(s), 53 document(s) : PASS
    docs_verify --coverage: 6 seam(s) swept, 16 without a Sweep: header,
      0 finding(s) : PASS (pre-existing, unrelated)
    docs_verify --stale: 0 document(s) worth re-reading : PASS

new checks added by this change: none in `docs/map/`'s ID grammar
(same reasoning as sub-tranche (i) — this tranche's files are outside
that system's scope); the behavior added is proven by
`tests/test_intake_form.py` (11 tests) plus the wheel-smoke pins
(packaging-surface behavior, proven by a real build).

record observables added vs sweep probes: none — `IntakeFormV1`
validation is stateless and never touches the append-only log.

wheel smoke: see Packaging-surface check above — run and passed twice.

## Requirement sweep

R3/R4 ("a tool should be the default... for small models" -> resolved
to "default for everyone" per Amendment 1): demonstrated by S3's
acceptance checks above; `IntakeFormV1`/`validate-intake`/
`validate_intake` exist and work for every caller (CLI for humans/
developers, MCP for model callers, both sharing the identical
`IntakeFormV1.model_validate` + `render_intake_validation_errors`
code path).
R5/C3/C4 ("researching accepted standards... a validated file beats a
wizard for every caller"): demonstrated by SPEC.md's M1/M4
measurements (already run at design time) plus this sub-tranche's
actual delivery of the file-based path with zero interactive-dialog
code.
Q4 ("Is the tool a CLI command, MCP tool, or both?" -> both):
demonstrated — both exist, share one validator.

## Assumptions carried

A3 (standalone model, never touches `RunManifest`): held — confirmed
by the empty frozen-surface diff.
The MCP-schema-filtering fix introduces a NEW assumption, recorded
here for the operator: the CLI's `validate-intake` and the MCP's
`validate_intake` now validate against two DIFFERENT schemas (full vs.
Part-A-filtered) even though both call the SAME `IntakeFormV1.
model_validate` underneath — the underlying validator is one code
path, but the ADVERTISED/ENFORCED input shape differs by caller. This
was not anticipated in the original SPEC (which said "same code path,
not a re-implementation," true of the validator, but did not
anticipate the MCP surface needing a narrower schema) — recorded as
Addendum 2's own late-breaking finding, not silently absorbed.

## Verdict: PASS
