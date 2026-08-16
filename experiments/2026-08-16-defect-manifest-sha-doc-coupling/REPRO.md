# Reproduction

Form: record-replay + in-memory (paired with the live gate observation)

Artifact: `experiments/2026-08-16-defect-manifest-sha-doc-coupling/probe_digests.py`
— recompiles the grounded configuration through its own committed
`build_manifest.py` under three tree states and prints the digest chain
each time; restores both probed files in a `finally`. Exits 0 only on
hypothesis (a).

## Current output — the artifact

    $ python experiments/2026-08-16-defect-manifest-sha-doc-coupling/probe_digests.py
    --- committed record vs live paths (evidence-dossier.json)
        MATCH  95e7a2acb742b1d6  docs/STATE_OF_THE_THEORY.md
        MATCH  9116c8592387ce22  docs/harness-spec-v1.3.md
        MATCH  ce2f8390bf7df646  docs/proposals/GROUNDED_OVERLAY_PREPLAN.md
        MATCH  2e640db15637b4ac  experiments/2026-08-08-corpus-enrichment-patrol-pilot/PATROL_DETERMINISM_REPORT.md
        MATCH  8ddb400f3c2d52a6  docs/map/CON-warrants-and-attacks.md
        MATCH  a79fb57bd1b49204  docs/map/SUB-adjudication.md
    --- BASELINE (clean tree)
        evidence_dossier_digest  3155b3d79c781e1b0866623934de6ae7ca10ca0c9aae0f776a535c16ef505c31
        run_input_digest         f6e488fd77c89b067283ca2bb38658e91022e9e39a27b8edb8ba7b0417d25377
        manifest_sha256          8e22d0431fd2b98dc915c66f2f3ccc6dc43184b4c326ff5d388a7c013a80989d
    --- B-PROBE (edited SUB-scheduler.md, NOT in dossier)
        evidence_dossier_digest  3155b3d79c781e1b0866623934de6ae7ca10ca0c9aae0f776a535c16ef505c31
        run_input_digest         f6e488fd77c89b067283ca2bb38658e91022e9e39a27b8edb8ba7b0417d25377
        manifest_sha256          8e22d0431fd2b98dc915c66f2f3ccc6dc43184b4c326ff5d388a7c013a80989d
    --- A-PROBE (edited SUB-adjudication.md, IN dossier)
        evidence_dossier_digest  4d59971cf2fce8cd82ec55c18be60b36d5e0bc61e3ff3f57f54c585bbf1488c5
        run_input_digest         66ea2aed85a6497d0bdb93e46ed0ee1ecf4694749182bd712c93677d390761ff
        manifest_sha256          b92f5d4761b3cf133bf7d470c2ba590d4ef8e449d45e1a2f6180721c08c0f475
    --- A-PROBE recompiled (determinism under the same input)
        evidence_dossier_digest  4d59971cf2fce8cd82ec55c18be60b36d5e0bc61e3ff3f57f54c585bbf1488c5
        run_input_digest         66ea2aed85a6497d0bdb93e46ed0ee1ecf4694749182bd712c93677d390761ff
        manifest_sha256          b92f5d4761b3cf133bf7d470c2ba590d4ef8e449d45e1a2f6180721c08c0f475
    --- verdict
        non-dossier edit moved identity : False   (hypothesis (b) iff True)
        dossier edit moved identity     : True
        determinism under fixed input   : True
        => hypothesis (a): identity consumes ONLY declared inputs.
    rc=0

(The A-probe digests differ from `DIAGNOSIS.md`'s `de84fe98…` only
because the appended comment text differs between the two probe runs.
That is the point: the digest tracks the bytes.)

## Current output — the gate, both arms

    $ printf '\n<!-- reproduction probe -->\n' >> docs/map/SUB-adjudication.md
    $ python -m pytest tests/test_single_run_path.py -q
    tests/test_single_run_path.py:588: AssertionError
    FAILED tests/test_single_run_path.py::test_the_grounded_tranche_config_enters_through_the_new_door
    FAILED tests/test_single_run_path.py::test_run_identity_is_deterministic_through_the_one_road
    2 failed, 8 passed in 28.40s
    $ git checkout docs/map/SUB-adjudication.md

    $ printf '\n<!-- reproduction probe -->\n' >> docs/map/SUB-scheduler.md
    $ python -m pytest tests/test_single_run_path.py -q
    10 passed in 41.45s
    $ git checkout docs/map/SUB-scheduler.md

Confirms diagnosis: yes — the defect fires if and only if the edited
document is one of the configuration's six declared `DOSSIER_PATHS`, and
under a fixed input the compile is bit-for-bit repeatable. Identity is
behaving as a content address over declared inputs; the constant in
`tests/test_single_run_path.py:59` is what does not survive editing them.

Post-fix expectation:

- `probe_digests.py` keeps printing the SAME verdict (unchanged: the
  builder is not being touched, and the behaviour it demonstrates is
  correct).
- `python -m pytest tests/test_single_run_path.py -q` → `10 passed`
  under BOTH arms above, i.e. with or without an appended line in
  `docs/map/SUB-adjudication.md`.
- A new sensitivity test asserts the A-probe behaviour as CORRECT
  against a FROZEN fixture copy: editing a bound dossier document MUST
  move the manifest sha, so that a future reader cannot re-diagnose this
  as a bug.
