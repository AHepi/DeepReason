# Parked — found by W3, deliberately not fixed here

W3 is a READ-ONLY measurement tranche (GOAL.md: 0 changed lines under `src/`
or `tests/`). Everything below is a finding, not a fix. Each entry is one line
of WHAT, then a ready-to-send prompt for its future runner: starting the
follow-up should cost the operator a paste, not an authoring session.

---

## P4-W3-1 — an attached dossier is silently truncated to 32 blocks

**What.** `evidence/render.py::citable_legend` caps the citable list at
`maximum_blocks=32`. P-R1 bound 623 blocks; 32 were ever rendered; 591
(902,387 bytes, 93 percent of the dossier) were structurally uncitable, and
nothing in the record says so. The operator paid to admit, digest and freeze
text that no seat could ever quote, and no typed disclosure marks it.

```
Route: dr-change-orchestrator.

One goal: when a bound dossier holds more admitted evidence blocks than the
citable legend can render, the run must RECORD that fact as a typed
disclosure, so a reader of the record can tell "the model passed this
section over" from "the model was never shown it".

Authority: operator design law 2026-08-12 ("All configurations should be
allowed") — an over-large dossier must still COMPILE and still run; what is
missing is the disclosure the same law requires in place of a refusal. Do
NOT add a compile-time or runtime refusal.

Evidence, already committed and re-derivable:
  experiments/2026-08-26-run-anatomy-w3-evidence-scratch/RESULTS.md F1
  experiments/2026-08-26-run-anatomy-w3-evidence-scratch/TABLES.md  §1d
  python experiments/2026-08-26-run-anatomy-w3-evidence-scratch/evidence_census.py \
      experiments/2026-08-25-poietics-program/run
  -> exposure_vs_citation.blocks_never_exposed = 591 of 623

Map: DR-SUB-evidence (owns evidence/render.py). Read
docs/map/INV-frozen-surfaces.md FIRST — this touches rendering, not a record
format, but confirm that before designing. The evidence x rules seam has no
map document; see P4-W3-4.

End state: a typed disclosure exists in the record naming how many admitted
blocks were withheld from the legend and why; a regression test proves it
fires when blocks > cap and does NOT fire when blocks <= cap; full gate 0
failed; the map moves in the same commit.
```

---

## P4-W3-2 — a run can be configured to write scratch it cannot read, silently

**What.** P-R1's manifest carries `control_plane_policy.scratch_authoring.
enabled = true` with `scratch_policy.enabled = false`. Seventeen notes were
authored; no retrieval object exists in the root; nothing could ever read
them. Eight committed roots are in this state. HYPOTHESIS, from code reading
and therefore weaker than the record (RESULTS.md R7): `rules/conj.py` (~line
2446) validates a scratch proposal against `control.scratch_authoring` alone,
while `scratch/authoring.py::_validate_v6_authority` — the guard used by
other entry points — also requires `scratch_policy.enabled`.

```
Route: deepreason-orchestrator (this is a defect, not a change).

One goal: establish whether a v6 run whose manifest sets
scratch_policy.enabled=false can still author scratch notes through the
conjecture path, and if so, make the two flags reconcile — by a typed
disclosure at compile ("scratch authoring is on with retrieval off; notes
will be written and never served"), NOT by a refusal.

Authority: operator design law 2026-08-12 ("All configurations should be
allowed") — the configuration must keep compiling and running. What is at
issue is that it is undisclosed, and possibly that one guard is bypassed.

Start from the record, not the code (dr-diagnose):
  experiments/2026-08-25-poietics-program/run/run-manifest.json
    scratch_policy.enabled              = false
    control_plane_policy.scratch_authoring.enabled = true
  17 Scratch events at seqs 992-998, 1373-1376, 2357-2362
  objects/: scratch-block x14, scratch-link x3, and NO
            scratch-advisory-context, scratch-attention-receipt, or
            scratch pack plan.
  python experiments/2026-08-26-run-anatomy-w3-evidence-scratch/scratch_census.py \
      experiments/2026-08-25-poietics-program/run

Reproduce OFFLINE before proposing anything: a manifest with authoring on and
retrieval off, driven far enough to author one note. If the note is written,
the guard question is answered by demonstration rather than by reading.

Map: DR-SUB-scratch, DR-SEAM-rules-x-scratch, DR-SEAM-scratch-x-workflow.
INV-frozen-surfaces.md first: run_manifest.py IS a frozen surface, so a
manifest SCHEMA change is out of scope without explicit operator approval —
a disclosure recorded alongside the compiled result is not.

End state: DIAGNOSIS.md names one cause with record evidence; REPRO.md
demonstrates it offline; the fix is the smallest correct one; full gate 0
failed.
```

---

## P4-W3-3 — `plan_kind="dossier"` names a pack that carries no dossier

**What.** `workflow-context-pack-plan-v1` objects with `plan_kind="dossier"`
carry the run's OWN ARTIFACTS under `SRC_###` aliases. The attached documents
are carried by `plan_kind="citable"` under `EVD_###` aliases. The label
misleads every reader of the record — it misled the first draft of this
census, which reported the wrong exposure set until the `object_ref`s were
resolved against artifact ids.

```
Route: dr-change-orchestrator, but SCOPE IT AS A DOCUMENTATION CHANGE FIRST.

One goal: make a reader of a committed record unable to mistake
plan_kind="dossier" for the attached dossier.

Read INV-frozen-surfaces.md before anything: pack-plan records are part of
the run record, and renaming a stored plan_kind value would change what past
roots mean. Under operator law 2026-08-14 old roots owe the future nothing,
so a rename is PERMITTED — but it is a record-format change and needs the
operator's explicit approval, which this prompt does not carry.

Cheapest correct first move: document the collision in the map
(DR-SUB-evidence and/or DR-SUB-workflow), with a `check:` that would fail if
the two namespaces ever swapped meaning. Propose the rename separately, as a
DESIGN-AND-STOP, and let the operator decide.

Evidence:
  experiments/2026-08-26-run-anatomy-w3-evidence-scratch/evidence_census.py
    (_pack_receipts docstring records the trap and the join that resolves it)
  P-R1: 132 dossier plans -> 112 items resolve to artifact ids, 0 to dossier
  sources; 45 citable plans -> 1238 items, all resolving to dossier blocks.
```

---

## P4-W3-4 — the evidence x rules seam has no map document

**What.** `docs/map/SUB-evidence.md` declares `Seams:` EMPTY and lists
`evidence x rules` among its undocumented pairs. That is the seam where
`rules/conj.py` files `evidence-citation:<CODE>` and `rules/crit.py` files
`premise-citation:<CODE>` — the exact agreement this census measured, and
the one a reader must currently reconstruct from two call sites.

```
Route: dr-change-orchestrator.

One goal: author docs/map/SEAM-evidence-x-rules.md to SCHEMA.md's contract,
covering the small fraction of each side actually involved: which rule files
call check_candidate_citations, the asymmetry in what each records (the
conjecture-side Measure carries [tag, block, artifact_id, problem_id]; the
critic-side carries [tag, block, problem_id] and NO artifact id), the
exposed-set gate each passes, and what the outcome codes mean.

Read docs/map/SCHEMA.md before writing a single line of it.

Every load-bearing claim needs a `check:` that would FAIL if the behaviour
regressed — run it before writing it down, and run
`python tools/docs_verify.py --audit` to confirm no check is unfalsifiable.

Prior art to draw on, already committed:
  experiments/2026-08-26-run-anatomy-w3-evidence-scratch/evidence_census.py
    (its module docstring states each fact's provenance and the three traps
     the record punishes a reader for skipping)
  experiments/2026-08-25-poietics-program/milestone_census.py

Update SUB-evidence.md's Seams / Seams-undocumented lines and INDEX.md's
matrix in the SAME commit.
```

---

## P4-W3-5 — the record cannot distinguish a quoted citation from a bare handle

**What.** `EVIDENCE_CITATION_VERIFIED` is returned both when a model quoted
text that byte-checked against admitted bytes and when it merely named a
block handle and quoted nothing. In P-R1, 146 of 294 refs were bare handles.
`EvidenceCitationCheckV1` carries a `quoted` field, but the `Measure` event
records only `[tag+code, block_id, ...]` — so the split is recoverable ONLY
from the raw response blob. A run's own record is not self-sufficient about
its own citation quality.

```
Route: dr-change-orchestrator.

One goal: make the typed citation record carry whether the citation was
QUOTED, so "212 byte-checked citations" can be read off the record without
reopening provider response blobs.

The value already exists: evidence/citations.py builds
EvidenceCitationCheckV1(quoted=...) on every path. It is simply not carried
into harness.record_measure at rules/conj.py:2408 and rules/crit.py:1368.

Read INV-frozen-surfaces.md FIRST. Adding an input to an existing Measure
event changes what a recorded event looks like. Under operator law
2026-08-14 that is permitted for new runs and owes old roots nothing, but
harness.py event application IS a frozen surface — so establish whether this
needs operator approval BEFORE writing code, and stop and ask if it does.

Evidence:
  experiments/2026-08-26-run-anatomy-w3-evidence-scratch/RESULTS.md F3
  python experiments/2026-08-26-run-anatomy-w3-evidence-scratch/evidence_census.py \
      experiments/2026-08-25-poietics-program/run
  -> citation_quality.breakdown, and its `caveat` field naming this gap

End state: the split is derivable from log.jsonl alone for a NEW run; a
regression test proves both branches record distinguishably; full gate 0
failed.
```

---

## P4-W3-6 — NOT a defect, recorded so nobody re-opens it

**What.** Models emit citation-shaped refs when no dossier is bound at all.
Fourteen roots show this; every attempt is refused typed
(`EVIDENCE_REFS_UNBOUND` where nothing is bound, `EVIDENCE_REF_UNKNOWN_BLOCK`
where an empty dossier is bound). **The harness behaved correctly in every
case.** This is model behaviour the record already catches, and it needs no
change. Recorded here only so a future audit does not read the refusal counts
as a fault.
