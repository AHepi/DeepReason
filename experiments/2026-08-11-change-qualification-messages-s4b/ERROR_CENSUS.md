# Error-code census (evidence for SPEC.md S2)

Census run 2026-08-11 across src/deepreason/ (read-only). Full detail
below; SPEC.md's Family-grouped counts table is the summary.

## Raise/refusal infrastructure

No central `exceptions.py`. ~140 exception classes scattered per-module
(`harness.py: WellFormednessError`, `qualification.py:
QualificationError`, `run_manifest.py: RunManifestError`,
`admission/store.py: AdmissionStoreError`, `llm/firewall.py:
SchoolRouteResolutionError`, etc). Three raise conventions coexist:

(a) plain `ValueError(f"CODE_NAME: prose")`, single string, majority
    convention (e.g. `runtime/terminal_authority.py`);
(b) `(code: str, message: str)` two-positional-arg `__init__`, shared
    by several hand-rolled classes (`QualificationError`,
    `AdmissionStoreError`, `SchoolRouteResolutionError`,
    `WorkflowRetryBoundaryError`) — `self.code` becomes catchable;
(c) `RunManifestError(code, message, pointer="")` — a third
    convention, adding a JSON-pointer to the offending manifest field
    (`run_manifest.py:90-95`), used for `DOCTOR_*` and
    `V6_PRODUCTION_QUALIFICATION_*`.

Separately, `AdmissionRefusalV1` (`evidence/models.py:222-238`) is a
genuinely TYPED refusal record — Pydantic, `code: Literal[6 values]` +
`detail: str`, meant to live IN the record, not just be thrown. A
handful of other models follow the same `code: Literal[...]` shape
(`workflows/manifest_compiler.py:133`, `evidence/citations.py:45`,
`bridge/ledger.py:1678`, `bridge/operations.py:36,73`); `application/
bridge.py:216` has a pattern-constrained `error_code: str` field.

`verification/registry.py`'s `VerifierRegistry` registers verifier
BACKENDS (fingerprinted check plugins), not error codes — its own
errors (`UnknownVerifier`, `VerifierRegistryError`) are untyped prose.
`mcp_registration.py` only resolves the installed `deepreason-mcp`
executable path; not a code registry either. **No human-readable
catalog exists anywhere** — greps for `CATALOG`, `_MESSAGES =`,
`_DESCRIPTIONS =`, "glossary" found only unrelated hits.

## Worked examples (verbatim current "message")

- `runtime/terminal_authority.py:169` — `raise
  ValueError("TERMINAL_RESULT_UNSAFE")`. No prose beyond the code
  itself.
- `admission/store.py:76-78` — `raise AdmissionStoreError
  ("ADMISSION_DOSSIER_INVALID", "dossier digest is not a sha256")` →
  `str(e)` = `"ADMISSION_DOSSIER_INVALID: dossier digest is not a
  sha256"` — code + one clause, no remediation.
- `llm/firewall.py:574-578` — `SchoolRouteResolutionError
  ("SCHOOL_ROUTE_LEASE_MISMATCH", f"runtime lease for {role}[{seat}]
  differs from the manifest route")` — jargon-laden ("lease",
  "manifest route").
- `qualification.py:813-822` — `QUALIFICATION_TIER_SHALLOW`: 'this
  provider/model is qualified at tier "shallow" only; full V6
  reasoning is refused. Use: deepreason reason --shallow "YOUR
  QUESTION"' — the BEST-written message in the codebase (states
  consequence + remediation); the exception, not the rule.
- `evidence/models.py:222-236` — `AdmissionRefusalV1`: typed record,
  never rendered to prose anywhere found; consumers get the bare code
  + a free-text `detail` a caller wrote.
- `cli/bridge.py:272,449,466` — prints the raw UPPERCASE
  `error_code`/`terminal.error_code`, unglossed, as the entire
  user-facing error line for bridge failures. Worst-case today.

## Qualification-specific codes (R1's immediate complaint area)

`QualificationError` (`qualification.py`, `code, message`):
`QUALIFICATION_V6_REQUIRED`, `QUALIFICATION_POLICY_PRESET_MISMATCH`,
`QUALIFICATION_SUBJECT_INVALID`, `QUALIFICATION_NOT_CONFIGURED`,
`QUALIFICATION_CACHE_UNAVAILABLE`, `QUALIFICATION_CACHE_UNSAFE`,
`QUALIFICATION_INCOMPLETE`, `QUALIFICATION_CACHE_INVALID`,
`QUALIFICATION_CACHE_NONCANONICAL`, `QUALIFICATION_SUBJECT_MISMATCH`,
`QUALIFICATION_CACHE_CONFLICT`, `QUALIFICATION_TIER_NOT_RECORDED`,
`QUALIFICATION_TIER_INVALID`, `QUALIFICATION_TIER_NONCANONICAL`,
`QUALIFICATION_TIER_SUBJECT_MISMATCH`, `QUALIFICATION_PROFILE_MISMATCH`,
`QUALIFICATION_PAIR_INVENTORY_MISMATCH`, `QUALIFICATION_TIER_SHALLOW`,
`QUALIFICATION_TIER_UNQUALIFIED`, `QUALIFICATION_EXECUTION_FAILED`,
`QUALIFICATION_EXECUTION_INVALID` — 21 codes total, exact line numbers
and current raw text in the agent transcript this file summarizes;
re-derive with `grep -n "QualificationError(" src/deepreason/
qualification.py` before S2 executes.

`RunManifestError` from `runtime/launch_policy.py:176-242`:
`V6_PRODUCTION_QUALIFICATION_MANIFEST_REQUIRED`,
`V6_PRODUCTION_QUALIFICATION_POLICY_REQUIRED`,
`V6_PRODUCTION_QUALIFICATION_ROOT_REQUIRED` (raised 4x, identical code,
different failure modes).

`DOCTOR_*` from `cli/doctor.py` (21 total, `RunManifestError`):
`DOCTOR_REPORT_MISSING`, `DOCTOR_REPORT_UNSAFE`,
`DOCTOR_REPORT_TOO_LARGE`, `DOCTOR_REPORT_INVALID`,
`DOCTOR_REPORT_NONCANONICAL`, `DOCTOR_REPORT_MANIFEST_MISMATCH`,
`DOCTOR_REPORT_CLASSIFICATION_MISMATCH`,
`DOCTOR_REPORT_PAIR_INVENTORY_MISMATCH`, `DOCTOR_REPORT_PAIR_UNQUALIFIED`,
`DOCTOR_REPORT_QUALIFIED_PAIR_COUNT_MISMATCH`,
`DOCTOR_REPORT_REPAIR_GRANT_EXCEEDED`,
`DOCTOR_REPORT_SCHEMA_VERSION_MISMATCH`, `DOCTOR_REPORT_SUMMARY_UNQUALIFIED`,
`DOCTOR_RUN_MANIFEST_V6_REQUIRED`,
`DOCTOR_BEHAVIORAL_CAPABILITY_PLAN_REQUIRED`,
`DOCTOR_BEHAVIORAL_CONTRACT_GRANT_REQUIRED`,
`DOCTOR_PRODUCTION_CONTRACT_MISMATCH`,
`DOCTOR_REQUEST_ENVELOPE_CAPACITY_REQUIRED`,
`DOCTOR_CLASSIFICATION_PAIR_INVENTORY_MISMATCH`,
`DOCTOR_CLASSIFICATION_FOREIGN_ROUTE`, `DOCTOR_CONTRACT_REPAIR_GRANT_EXCEEDED`,
`DOCTOR_OUTPUT_CONFLICT`.

`cli/main.py:1724 _print_qualify_failure` is the one existing
precedent for code-triggered human prose: it prefix-matches
`"QUALIFICATION_EXECUTION_FAILED"`/`"DOCTOR_"` and appends one static
remediation sentence. S2 generalizes this into a registry.

## Files most load-bearing for the future catalog

`src/deepreason/qualification.py`, `src/deepreason/cli/doctor.py`,
`src/deepreason/runtime/launch_policy.py`,
`src/deepreason/run_manifest.py:90-95` (the `(code, message, pointer)`
shape to standardize on — the most complete of the three conventions),
`src/deepreason/evidence/models.py:222-238` (the `Literal[...]`
typed-refusal pattern to extend), `src/deepreason/cli/main.py:1724`
(the one existing precedent for code-triggered human-facing prose).
