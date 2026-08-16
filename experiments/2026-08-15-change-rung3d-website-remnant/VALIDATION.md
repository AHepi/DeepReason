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

---

# Close-out — 2026-08-16, fresh container

Run on a container cloned fresh from
`origin/claude/calculus-rung2-step2-premise-pes36e`, with no build state and no
prior test run. Purpose: verify the tranche's own conclusions from outside the
session that reached them.

## The manifest-sha question, settled from clean ground

The close-out brief inherited the SUPERSEDED reading — that the two failures
were "session-environmental" and traceable to a cache whose key omitted builder
identity. That reading was already corrected by the tranche
(`395668544`), and the fresh container now falsifies it by construction:

| Tree state | `pytest tests/test_single_run_path.py -k "manifest or run_identity"` | Wall |
|---|---|---|
| as committed | **4 passed** | 19.7 s |
| one comment line appended to `docs/map/SUB-adjudication.md` | **2 failed, 2 passed**, sha `8e22d043...` → `711e3f31...` | 7.9 s |

An environment that has never built anything reproduces both failures from a
one-line documentation edit, and the intra-run determinism assert
(`first == second`) passes inside the failing run. Both facts are incompatible
with a caching explanation. The coupling diagnosis in PARKED.md P1 stands, now
with a 30-second reproduction recipe; the probe file was reverted and the tree
is clean.

**No confirmation of the environmental hypothesis was written anywhere**, which
the brief's green road would have called for — it is refuted, not confirmed, and
recording it would have put a false claim into a parked defect prompt.

## Errata checkpoint

The brief asked whether any committed artifact still carries the wrong
attribution. Two answers, because the scan found a second, unrelated staleness:

- **The manifest attribution: nothing to correct.** `VALIDATION.md`,
  `DELIVERY.md` and `PARKED.md` all carry the corrected account. The superseded
  reading survives only in immutable commit messages that `395668544` answers
  directly. The scan is the checkpoint — recorded as `docs/ERRATA.md` E31b.
- **The enum's survival rationale: three artifacts were stale, now fixed.**
  `docs/ERRATA.md` E30's closing paragraph, `ontology/problem.py`'s `SUCCESSOR`
  comment, and `easy.py::seed_component`'s docstring each still asserted that a
  LIVE producer stamps the trigger. Rung 3d made producers zero and none of the
  three was updated with it. Corrected here; ledgered as `docs/ERRATA.md` E31.
  `docs/map/SUB-rules.md:193-194` already told the corrected story and needed
  nothing.

## One artifact gap, recorded rather than papered over

This tranche has **no `SPEC.md` and no `CHECKLIST.md`** — `git log
--diff-filter=A` over the directory returns only `DELIVERY.md`, `PARKED.md` and
`VALIDATION.md`, all added by `395668544`. Its authority and acceptance
requirements live in the v2 program's `REQUEST.md` Amendment 9 (R66–R71)
instead, which is where the operator's verbatim words were ledgered, so no
requirement went unrecorded and the reconciliation below is against those rows.
But `dr-drive-harness` §1 asks that a tranche be resumable from its own
committed artifacts, and this one is resumable only if the reader already knows
to look one directory over. Recorded as the gap it is; not retrofitted, because
inventing a SPEC after the fact would document a plan that never governed the
work.

## Acceptance rows re-verified at close-out HEAD

| SPEC row | End state | Evidence |
|---|---|---|
| producers before = 2, after = **0** | HELD | `easy.py:753-756` stamps `{"trigger": "seed"}` on both branches; `grep -rn "SpawnTrigger.SUCCESSOR" src/` returns only the enum definition itself |
| enum retained with zero producers, **docstringed** | HELD — the docstring is now TRUE | `ontology/problem.py` rewritten this commit: inert vocabulary, retained for replay, "its presence asserts no producer and licenses no new one" |
| four protected channels green and cited | HELD | the four `test_protected_*` rows, unchanged and green in the close-out gate |
| boundary intact | HELD | `advisory_non_grounding` a manifest literal; neither criticism renderer takes a scratch parameter |

## Instruments at close-out HEAD (`1a32fb193` + this commit)

| Instrument | Result |
|---|---|
| `python -m pytest tests/ -q -n 4` | **3682 passed, 7 skipped, 0 failed** (794 s) |
| `python tools/docs_verify.py` (full) | 60 documents, 916 checks, **1 failed** (398 s) |

The single `docs_verify` failure is `CON-run-identity.md:200`, one of that
document's three git-history checks, and it is a SUBSET of the recorded
baseline rather than a new failure: `docs/AUDIT_BASELINES.md` records "3
pre-existing failures, all `CON-run-identity.md` git-history checks — they
require an unshallowed clone; on a full clone the expected value is 0 failed."
This container is a shallow clone (`git rev-parse --is-shallow-repository` →
`true`, 110 commits), and its depth happens to reach the commits that lines 202
and 204 name while not reaching the rename history line 200 needs. So the
failure count moved for a reason that has nothing to do with this tranche —
which is worth stating explicitly, because "fewer failures than baseline" is
the kind of pleasant number that should never be banked without a cause.

Check counts rose from 910 to 916 across 59 → 60 documents because close-out
HEAD is two commits past the tranche (`1a32fb193`, the P4 citable-evidence
work), not because anything here added checks.
