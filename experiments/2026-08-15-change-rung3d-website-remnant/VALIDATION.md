# VALIDATION — Rung 3d

Verdict: **PASS. DO-NOT-MERGE lifted.**

| Instrument | Result |
|---|---|
| `python -m pytest tests/ -q -n 4` | **3668 passed, 7 skipped, 0 failed** (987 s) |
| `python tools/docs_verify.py` (full) | 59 documents, 910 checks, **3 failed — all `CON-run-identity`**, the recorded shallow-clone baseline |

## The protection census (R70) — four channels, two scans each, pasted

Deletion set: `easy.py`'s successor provenance; `SpawnTrigger.SUCCESSOR`;
`views/narrate.py`'s narration entry; `capture/schools.py`'s tuple member.

| Channel | Scan A — symbol present in the channel's tree? | Scan B — channel imports the deletion site's module? |
|---|---|---|
| code testing / execution (`oracle.py`, `programs.py`, `rules/crit.py`, `rules/experiment.py`) | **none** | **none** |
| simulation (`capabilities/`) | **none** | **none** |
| research backend (`research/`) | **none** | **none** |
| scratch pad (`scratch/`) | **none** | **none** |

Eight scans, zero hits, **no overlap — so no contradiction-stop was triggered**
and the cut was licensed. Had any channel hit, the instruction was to report
rather than cut.

## Acceptance (R71) — one green cited row per channel

| Channel | Test |
|---|---|
| code testing / execution | `test_protected_code_testing_and_execution_still_mints_evidence` |
| simulation | `test_protected_simulation_still_mints_its_typed_receipts` |
| research backend | `test_protected_research_backend_still_mints_fetch_receipts` |
| scratch pad (live + advisory) | `test_protected_scratch_pad_is_live_and_advisory_with_its_boundary_intact` |

Plus the two that keep the remnant out:
`test_the_successor_trigger_is_inert_vocabulary` and
`test_no_source_file_produces_a_successor_problem` — the second is the
load-bearing one, a source scan that fails the moment any file starts producing
successor problems again.

## The manifest-sha investigation, resolved

Directed as road A. The answer is **not** a cache, and the correction matters
more than the fix:

- **Determinism was never broken.** `first["manifest_sha256"] ==
  second["manifest_sha256"]` passed on every run, which a stale-artifact cache
  could not do.
- **The builder digests an evidence dossier of six files, two of which are MAP
  documents.** I had edited `docs/map/SUB-adjudication.md`. The compiled
  manifest is a content address over it, so the sha moved correctly.
- Reverting that one file restored the pinned sha and both tests, in 14 s of
  real rebuild.
- The 0.5 s-vs-9.5 s timing that suggested caching was pytest failing at an
  early assert, not a skipped build.

The coupling itself is a real defect — documentation the map REQUIRES to change
is welded to a pinned run-identity golden — and is **PARKED**, not fixed here.

## Residue

- `SpawnTrigger.SUCCESSOR` survives as inert vocabulary, deliberately; the
  invariant that matters is zero producers, and it has its own regression.
- The parked coupling defect (PARKED.md P1) will make any future map edit to
  `CON-warrants-and-attacks.md` or `SUB-adjudication.md` fail the same two
  tests until it is fixed.
