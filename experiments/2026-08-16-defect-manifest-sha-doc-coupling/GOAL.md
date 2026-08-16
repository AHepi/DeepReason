# Goal: two tests pin the grounded manifest sha against live, mutable docs/ bytes

Class: defect

Observed: with a clean tree `tests/test_single_run_path.py` is green
(2 passed on the two sha-pinning tests, 15.5s); appending one comment
line to `docs/map/SUB-adjudication.md` turns exactly two of them red —
`test_the_grounded_tranche_config_enters_through_the_new_door` and
`test_run_identity_is_deterministic_through_the_one_road` — with
`manifest_sha256` moving off the pinned constant
`8e22d0431fd2b98dc915c66f2f3ccc6dc43184b4c326ff5d388a7c013a80989d`
(observed this container: `de84fe98a517…`, 2 failed / 19 passed, 56.4s
over `tests/test_single_run_path.py tests/test_lifecycle_operation_parity.py`).
The documented guarantee the observation contradicts is the tests' own
stated property — that the pinned digest identifies the grounded
configuration — while `docs/map/SUB-adjudication.md` is one of the six
BOUND DOSSIER documents that configuration declares
(`experiments/2026-08-12-live-grounded-extension-expansion/build_manifest.py`
`DOSSIER_PATHS`), i.e. part of the run's evidence, not part of its code.

Success criterion (machine-decidable):

    # 1. clean tree
    python -m pytest tests/test_single_run_path.py -q
    #    -> 10 passed, 0 failed

    # 2. the reproduction, verbatim
    printf '\n<!-- reproduction probe -->\n' >> docs/map/SUB-adjudication.md
    python -m pytest tests/test_single_run_path.py -q
    #    -> 10 passed, 0 failed   (today: 2 failed)
    git checkout docs/map/SUB-adjudication.md

    # 3. the behaviour is asserted as CORRECT, not merely tolerated
    python -m pytest tests/test_single_run_path.py -q -k sensitivity
    #    -> at least 1 passed: editing a FROZEN fixture copy of a bound
    #       dossier document MUST move the manifest sha

    # 4. boundary
    python -m pytest tests/ -q -n 4
    #    -> 0 failed
    python tools/docs_verify.py
    #    -> at the 3-failure shallow-clone baseline (docs/AUDIT_BASELINES.md)

In scope:
- `tests/test_single_run_path.py` (the two pinning tests)
- a frozen fixture copy of the six bound dossier documents, under
  `tests/fixtures/` (new)
- `docs/map/CON-run-identity.md` and/or `docs/map/INV-frozen-surfaces.md`
  — the map moves in the same commit as the code

NOT in scope: `src/deepreason/run_manifest.py` and the evidence-dossier
digest path (`src/deepreason/admission/`, `src/deepreason/evidence/`).
Frozen surface 4 (`INV-frozen-surfaces.md` §4 — manifest schemas AND
their validators) is untouched unless the diagnosis lands on hypothesis
(b), which is a workflow stop, not an edit.

Map ids resolved (preflight):
- `DR-CON-run-identity` — what the identity digest covers
- `DR-SUB-manifest` — RunManifest schema/validators, **frozen**
- `DR-SUB-evidence` — attached dossiers, byte-checked citations
- `DR-INV-frozen-surfaces` §4 — the surface a hypothesis-(b) fix would hit
- Seam `manifest x run-identity` is UNDOCUMENTED (`CON-run-identity.md`
  `Seams-undocumented:`). Recorded as a finding, not a blocker; this
  tranche does not create it (the coupling it would describe —
  dossier bytes → run input digest → manifest sha — is the very thing
  being settled, and belongs in `CON-run-identity.md` first).

Budget: <=150 changed lines, 1 commit per phase boundary, ~2 hours
Stop conditions inherited from orchestrator: yes
