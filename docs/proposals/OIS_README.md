# Operator-supplied design documents, filed 2026-09-05 (monitor)

Three documents the operator uploaded, filed so executor windows can cite them.
They are PROPOSALS: none is adopted by being here. What the operator adopted
from each is ledgered in CLAUDE.md (design laws) and in
docs/HANDOVER_MONITOR_2026-08-29.md ("Queued 2026-09-04").

- `CR2_0_revB_Creative_Revision_Event_Semantics.md` — a theory of creative
  processes (event structures, cuts, four-valued evidence). Three adoptions
  queued 2026-09-04; the first (evidence states) shipped 2026-09-05.
- `OIS_LLM_Profile_1_0.md` — how a language model realises the theory's roles.
  Monitor's assessment 2026-09-05: mostly already how the harness works; four
  instruments worth taking (transfer test, per-conjecture newness probe,
  recorder context excludes self-appraisal, mini as a composite); three points
  of friction with operator law, to be made configurable first; one missing
  capability (fork a run from a prefix), which the operator agreed to.
- `OIS_1_1_to_DeepReason_configuration.md` — a repository read at 1f8108c00a
  with ONE tested finding (§0), REPRODUCED by the monitor 2026-09-05 on the
  installed package: a criticism whose essential premise is later refuted keeps
  its target refuted when the premise is a DEPENDENCE ref, and reinstates it
  when the premise is an EVIDENCE ref on the validity node. The critic form has
  no field to declare an essential premise, so the correct branch is
  unreachable from the wire. Also carries template rewrites (§3) and contract
  additions (§4) — NOT adopted for the full harness's default forms (they
  conflict with the formalism-optional law, the form census, and the decision
  to try relaxed forms in mini first); an audit brief (§6) runnable as a
  spec-drift audit once the operator supplies the 1.1 specification it is
  baselined on; and a change-request draft (§7), of which R1 is the defect
  tranche.

## `ois-1.1/` — the specification package, filed 2026-09-05

The zip the operator uploaded as `PopperSemantics_OpenInquiry_Hardened_1_1.zip`,
unpacked verbatim: `PopperSemanticsV1_1.md` (the proposed semantic authority),
`Open_Inquiry_Specification_1_1.md` (the subordinate staged specification the
configuration document above is bound to and the audit brief is baselined on),
`Hardening_Audit.md` (25 findings S01-S24 + A01-A05 against the 1.0 versions),
`manifest.json`, and `verification/` (a standard-library reference checker,
66 tests, two fixture generators, a mutation runner, results).

Monitor's checks on filing: the three documents' SHA-256 match the manifest;
`python -m unittest` in `verification/` passes 66 tests here;
`run_mutations.py` detects 9 of 9 selected mutations here. Those are checks on
the package's own bookkeeping reference, exactly as its report says — not on
DeepReason and not on any semantic claim. The package's own status line:
"Proposed revisions; not automatically user-adopted." Nothing is adopted by
filing. `docs_verify` reads only `docs/map/`; the gate collects only
`tests/` and `mini/tests/`, so nothing here enters either.
