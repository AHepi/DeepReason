# Diagnosis: the tests pin a content address against inputs the tests do not own

**Verdict: hypothesis (a). The builder is correct; the two tests are brittle.**

Primary cause: the grounded configuration DECLARES six local documents as
its attached evidence dossier, two of which live under `docs/map/`
(`docs/map/CON-warrants-and-attacks.md`, `docs/map/SUB-adjudication.md`).
Identity is a content address over declared inputs, so those documents'
BYTES are inside it by construction, through exactly one channel:
dossier source bytes → `evidence_dossier_digest` → `run_input_digest` →
the manifest's own `run_input_digest` field → `manifest.sha256`. The two
tests re-compile that configuration from the LIVE repository paths and
then assert equality with a hard-coded constant. The constant is
therefore an assertion about the current byte-content of six working-tree
files — files that every map-editing tranche is required to edit — and
not, as the tests' own comment claims, about "the same configuration".
Nothing ingests document bytes outside the declared dossier, so
hypothesis (b) is refuted, not merely unfavoured.

Evidence:

- `experiments/2026-08-12-live-grounded-extension-expansion/run/evidence-dossier.json`
  → the COMMITTED record of the live run declares six `attached-source.v1`
  entries, each with a `content_sha256` and a `source_locator`. Hashing the
  six live paths on a clean tree today reproduces all six digests exactly
  (MATCH ×6, including `a79fb57bd1b49204…` for
  `docs/map/SUB-adjudication.md`). The pinned constant is reproducible
  today only because the working tree still happens to be byte-identical
  to the record; it is not a property of the code.
- `.../run/evidence-dossier.sha256` = `3155b3d79c781e1b…`,
  `.../run/run-input.json` `evidence_dossier_digest` = the same
  `3155b3d79c781e1b…` and `run_input_digest` = `f6e488fd77c89b06…`,
  `.../run/run-manifest.json` `run_input_digest` = the same
  `f6e488fd77c89b06…`, `.../run/run-manifest.sha256` = `8e22d0431fd2b98d…`
  → the whole chain from evidence bytes to run identity is recorded in
  the run's own typed files, dossier-first, four links, no gaps.
- **A-probe** (this container, clean tree + one appended comment line in
  `docs/map/SUB-adjudication.md`, recompiled via the tranche's own
  `build_manifest.py`): all three digests move together —
  `evidence_dossier_digest` `3155b3d7…`→`97b68b09…`,
  `run_input_digest` `f6e488fd…`→`7a5bfaef…`,
  `manifest_sha256` `8e22d043…`→`de84fe98…`. Recompiling a second time
  with the edit still in place returns `de84fe98…` again: determinism is
  intact, only the INPUT changed.
- **B-probe** (the discriminator the tranche prompt specified): the same
  appended comment line applied instead to `docs/map/SUB-scheduler.md`,
  a map document NOT in the dossier → all three digests **unchanged**
  (`3155b3d7…` / `f6e488fd…` / `8e22d043…`). No undeclared ingestion path
  exists.
- Gate observation, clean tree: `python -m pytest
  tests/test_single_run_path.py tests/test_lifecycle_operation_parity.py -q`
  → 21 passed. With the A-probe edit in place → 2 failed, 19 passed
  (56.4s), and both failures are the equality against the constant, at
  `tests/test_single_run_path.py:316` and `:588`.

Implicated code:

- `tests/test_single_run_path.py:59-61` — `GROUNDED_MANIFEST_SHA256`
  constant, and its assertions at `:316`, `:588`, `:614`.
- `experiments/2026-08-12-live-grounded-extension-expansion/build_manifest.py`
  `DOSSIER_PATHS` — six LIVE repo paths, resolved at call time. This is
  correct for the live tranche it was written for (the dossier had to be
  the real documents) and is what makes it unusable as a frozen test
  fixture.
- `src/deepreason/run_manifest.py:3507` — `manifest_values["run_input_digest"]
  = run_input_digest`, the one link that carries evidence into identity.
  **Frozen surface 4. Not touched by this tranche.**

Falsifiable prediction (what `dr-reproduce` must show):

    printf '\n<!-- reproduction probe -->\n' >> docs/map/SUB-adjudication.md
    python -m pytest tests/test_single_run_path.py -q
    # -> exactly 2 failed, both AssertionError comparing a moved
    #    manifest_sha256 against 8e22d0431fd2b98d…, at :316 and :588

    git checkout docs/map/SUB-adjudication.md
    printf '\n<!-- reproduction probe -->\n' >> docs/map/SUB-scheduler.md
    python -m pytest tests/test_single_run_path.py -q
    # -> 10 passed, 0 failed  (a non-dossier map document cannot move it)

Ruled out:

- **Hypothesis (b), an undeclared ingestion path.** Refuted by the
  B-probe above: editing a map document outside the dossier moves
  nothing. Every byte reaching identity arrives through the six
  `DOSSIER_PATHS` the configuration itself declares.
- **The environmental/cache reading** (`04da6c65f`'s report attributed
  the failures to the container). Already falsified on record by
  `d52c739ff`'s close-out and by `docs/ERRATA.md` E31b; independently
  re-falsified here — this container reproduces the failure from a clean
  checkout with a one-line doc edit, and reverting the line restores
  green. The parked prompt's cache framing is superseded and is corrected
  by appendix in this tranche.
- **The enum-deletion reading** (that `SpawnTrigger.SUCCESSOR`'s removal
  moved the digest): refuted on record before this tranche — restoring it
  did not fix these two tests — and structurally excluded here, since the
  B-probe shows only dossier bytes move the sha and no enum is in the
  dossier.
