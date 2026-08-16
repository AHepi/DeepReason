# Results — manifest sha / doc coupling

## 2026-08-16 — the builder was right; the tests owned inputs they did not own

**What was observed.** On a clean tree the grounded-manifest tests were
green. Appending one comment line to `docs/map/SUB-adjudication.md` turned
exactly two of them red, with `manifest_sha256` moving off the constant
`8e22d0431fd2b98d…`. Two prior explanations were already refuted on record
— a deleted `SpawnTrigger.SUCCESSOR` enum (restoring it did not fix these
two) and a stale container/build cache (`d52c739ff`, `docs/ERRATA.md` E31b).

**What the record shows.** The grounded-extension configuration declares
six local documents as its attached evidence dossier
(`experiments/2026-08-12-live-grounded-extension-expansion/build_manifest.py`,
`DOSSIER_PATHS`), two of them under `docs/map/`. That run's own committed
`evidence-dossier.json` records all six by `content_sha256`, and on a clean
tree today all six live paths still hash to those exact values — which is
the only reason the pinned constant was reproducible at all. The chain from
evidence to identity is recorded end to end in the run's own typed files:
`evidence-dossier.sha256` `3155b3d7…` = `run-input.json`'s
`evidence_dossier_digest`; `run-input.json`'s `run_input_digest`
`f6e488fd…` = `run-manifest.json`'s `run_input_digest`; and
`run-manifest.sha256` is `8e22d043…`.

**What decided it.** An A/B probe, committed as `probe_digests.py` and
self-restoring:

| tree state | evidence_dossier_digest | run_input_digest | manifest_sha256 |
|---|---|---|---|
| clean | `3155b3d7…` | `f6e488fd…` | `8e22d043…` |
| `SUB-scheduler.md` edited (NOT in dossier) | `3155b3d7…` | `f6e488fd…` | `8e22d043…` |
| `SUB-adjudication.md` edited (IN dossier) | `4d59971c…` | `66ea2aed…` | `b92f5d47…` |
| same edit, recompiled | `4d59971c…` | `66ea2aed…` | `b92f5d47…` |

Evidence moves all three digests together; a map document outside the
dossier moves none of them; a fixed input recompiles bit-identically.
Hypothesis (a) — run identity working as a content address over declared
inputs — is confirmed, and hypothesis (b), map bytes reaching identity
through some undeclared path, is refuted rather than merely unfavoured.

**What was fixed.** The tests, and nothing else. `src/` is byte-identical
to the tranche base; `run_manifest.py` (frozen surface 4) was never opened
for edit. The acceptance test now compares the compiled manifest field by
field against the live run's committed `run-manifest.json`, excluding
`run_input_digest` — measured as zero differing keys on a clean tree and
exactly `['run_input_digest']` under a dossier edit — so a mismatch names
the field that drifted instead of printing two hex strings. The determinism
test compares against its own compile. The constant survives only as an
anchor proved against the committed root's `run-manifest.sha256`. A new
sensitivity test freezes copies of the six documents in `tmp_path` and
asserts that editing one MUST move the digest; it was mutation-proved by
severing the edit and confirming it fails.

**What the record now shows.** Full gate 3683 passed, 7 skipped, 0 failed.
The 30-second reproduction reruns green on both arms (11 passed with the
bound document edited, 11 passed with the unbound one edited).
`docs_verify` sits at the 3-failure shallow-clone baseline with `--audit`
0 findings and `--links` 0 dangling; this tranche's new check on
`CON-run-identity.md` passes.

**Residue — what remains unproven.** The `manifest x run-identity` seam
still has no document; its coupling now lives in `CON-run-identity.md`'s
prose and Traps, which is enough for the next reader but is not the seam
write-up (parked, P1). Only `SUB-adjudication.md` was probed as the moving
input and only `SUB-scheduler.md` as the non-moving one — the mechanism is
shared by the dossier's other five documents and by every other map
document, but that is inference from one probe each, not six. And
`build_manifest.py` still resolves live paths, correctly for the record it
belongs to; nothing but the Traps entry warns a future importer.

Accepted does not mean true: what is established is that identity consumed
only declared inputs in every state probed, not that no other path could
exist. The B-probe is the falsifier, and it is committed and rerunnable.
