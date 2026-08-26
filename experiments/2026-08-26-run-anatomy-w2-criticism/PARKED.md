# PARKED — W2 criticism anatomy

One tranche, one goal (`deepreason-orchestrator` scope contract §1). W2 is
a READ-ONLY measurement tranche: nothing below was fixed here. Each entry is
written for its FUTURE RUNNER — one line of WHAT, then a prompt that can be
pasted whole.

---

## P1 — `workflow-semantic-admission-v1.admitted_refs` resolve to nothing

**WHAT.** The record's own link from a dispatch to the artifacts it produced
is unusable: in P-R1, 0 of 163 admission records' `admitted_refs` resolve to
any object or artifact id on disk (`f92fb38ede23…` appears in exactly one
file, the admission that names it). W2 had to fall back to a
120-character content-prefix match. Route: defect.

```
DeepReason defect. Route through deepreason-orchestrator.

ONE GOAL: find out why `workflow-semantic-admission-v1.admitted_refs` name
ids that exist nowhere else in the root, and either fix the writer or
document what those refs actually address.

EVIDENCE (typed record, no code reading first):
  experiments/2026-08-25-poietics-program/run — 163 semantic-admission
  objects, every one joining cleanly to a work-preparation by `work_id`,
  and NOT ONE of whose `admitted_refs` matches a registered artifact id, an
  object filename, or a blob. Reproduce:
    cd experiments/2026-08-25-poietics-program/run
    python3 - <<'PY'
    import glob, json
    ids = {json.load(open(p))['data']['id'] for p in glob.glob('objects/artifact/*.json')}
    refs = [r for p in glob.glob('objects/workflow-semantic-admission-v1/*.json')
            for r in (json.load(open(p))['data'].get('admitted_refs') or [])]
    print(len(refs), 'refs;', sum(1 for r in refs if r in ids), 'resolve to an artifact')
    PY
  Same shape in experiments/2026-08-25-change-constructive-frontier/run.
  Read docs/map/SUB-workflow.md and its Traps section BEFORE the code.

END STATE: DIAGNOSIS.md naming one cause, and either FIX.md (if the writer
is wrong) or a map-document correction (if the refs are a different
namespace and the map does not say so).
```

---

## P2 — criticism is not routed back to the conjecturer in the newest runs

**WHAT.** 0 of 196 LLM attacks in P-R1 and P-C1 ARM H were exposed to any
later conjecture dispatch, while 35 of the 60 criticism-bearing roots in the
tree DID expose criticism to a conjecturer (July / early-August runs
routinely did). Whether this is a regression, a configuration difference, or
intended for these problem shapes is NOT established by W2. Route: defect
(diagnose first — it may be neither a bug nor a regression).

```
DeepReason defect. Route through deepreason-orchestrator.

ONE GOAL: establish why no criticism artifact entered a conjecture
dispatch's context pack in the two newest live runs, when 35 older roots
show criticism reaching the conjecturer — and say whether that is a
regression, a config difference, or by design for these runs.

EVIDENCE (typed record first):
  experiments/2026-08-26-run-anatomy-w2-criticism/sweep.json  — per-root
    `critic_artifacts_shown_to_conjecture`; 250 of 3901 tree-wide (6.4%),
    0 in experiments/2026-08-25-poietics-program/run, 4 (all mechanical
    verdict stubs, one target) in
    experiments/2026-08-25-change-constructive-frontier/run, but 16 in
    experiments/2026-08-04-change-rung5-dumb-alternative-backend/ab-home/
    runs/run-9a6be78e1e79184a0bd89923b957586c and 15 in
    experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/
    run-6995cd12124d2697030bb4b9e48f79bd.
  The instrument is `sweep.py` in that tranche; re-run it before theorising.
  Map order: docs/map/CON-packs-and-token-economy.md (what a pack may
  contain), then SEAM-llm-x-rules.md, then SUB-scratch.md.

END STATE: DIAGNOSIS.md. If it IS a regression, FIX.md; if it is a config
or problem-shape difference, a map-document sentence saying so, so the next
census does not re-open it.
```

---

## P3 — a critic's evidence citations are almost never byte-checked

**WHAT.** P-R1's critics emitted 55 `premise_evidence` citations; the
harness recorded **3** `premise-citation:*` checks. Of the 55, 5 name a real
dossier block. The candidate-side channel is checked properly (234 checks,
210 verified) — so the machinery exists and this one channel is not reaching
it. `rules/crit.py::_check_premise_citations` runs only when
`_premise_invited_problem(...)` is not None, which is the likely gate.
Route: audit first (it may be exactly as designed).

```
DeepReason audit question. Route through dr-audit-orchestrator
(docs-drift dimension), NOT a fix tranche.

ONE GOAL: decide whether "critics cite the bound dossier, and the citation
is byte-checked against the block" is TRUE of the shipped critic path, or
true only of the candidate path — and correct whichever of the two is wrong.

EVIDENCE:
  experiments/2026-08-26-run-anatomy-w2-criticism/TABLES.md §2b and §2c.
  P-R1: 55 critic evidence citations emitted, 3 checked (2 verified, 1
  quote-mismatch); 5 of 55 name a real block out of 623; 62% quote the
  TARGET under a block id that names nothing (`000000000000` twice).
  P-C1: 51 emitted, 0 checked, 0 dossier blocks in the root at all.
  Candidate side, same root: 234 checks — 210 VERIFIED, 20 QUOTE_MISMATCH,
  2 REF_NOT_EXPOSED, 2 REF_UNKNOWN_BLOCK.
  The claim under audit: experiments/2026-08-25-poietics-program/PROGRAM.md
  ("Critics cite the bound dossier, and the citation is byte-checked against
  the block"). Code pointer, read AFTER the record:
  src/deepreason/rules/crit.py `_check_premise_citations` and its
  `_premise_invited_problem` gate.

END STATE: an AUDIT_REPORT.md row with a verdict, plus either a
documentation correction or a ready-to-send fix prompt. No code change in
the audit tranche.
```

---

## P4 — every criticism dispatch in every measured run is `observe_only`

**WHAT.** 492 criticism dispatches across the tree carry
`dispatch_authority: observe_only`, and no measured run carries anything
else. `observe_only` cannot mint a warrant, so no LLM criticism in any of
these runs could ever move a Status — every status change came from the
problem's own admission criteria. `DR-CON-warrants-and-attacks` already
records this as expected ("text runs default to OBSERVE_ONLY, so almost none
of them ever mint a warrant"). What is NOT recorded anywhere is whether that
default is still what the operator wants now that two large runs have spent
~200 well-formed attacks against it. Route: **operator question**, not a
defect.

```
Operator decision, DeepReason. Do not route to a fix tranche until answered.

W2's census (experiments/2026-08-26-run-anatomy-w2-criticism/) found that in
both of the newest live runs, every criticism dispatch ran under
`observe_only` — the authority mode that cannot mint a warrant — so 196
LLM-written attacks changed no status, and all 463 status changes came from
the problem's own three admission criteria (keyword predicates in P-R1, the
geometric checker in P-C1).

The question is whether that default should stand. It bears directly on your
standing law that "a solo run with everything on should be an option" and on
your caution that judge seats "prosecute without any discernable
discrimination" — this is the opposite failure mode: a critic that cannot
prosecute at all.

Options, priced:
 (a) leave it — criticism stays advisory, refutation stays mechanical;
     costs nothing, and the ~200 attacks per run stay decorative;
 (b) arm criticism authority behind an explicit opt-in for runs whose
     problems have a demonstrative checker (P-C1's shape), so prose can
     only refute where a program could have;
 (c) route criticism back into the conjecture context pack (P2) WITHOUT
     giving it authority — cheapest, changes generation not evidence, and
     is the arm W2 could not test because the channel was shut.
Recommendation: (c) first, then measure again before considering (b).
```

---

## P5 — the criticism wire contract silently accepts a misspelled key

**WHAT.** Three P-C1 criticism replies spelled `premise` as `preise`; the
field parsed as absent and the attack was recorded without its premise. Not
a failure, but a silent one. Route: audit (spec-drift), low priority.

```
DeepReason audit question, low priority. Route through
dr-audit-orchestrator (spec-drift dimension).

ONE GOAL: decide whether an unknown/misspelled key in a criticism reply
should be a typed disclosure rather than silence.

EVIDENCE: experiments/2026-08-26-run-anatomy-w2-criticism/pc1_census.json —
3 dispatches carry `premise_key: "preise"`; the census reads both spellings
only because it was written to. Contract:
src/deepreason/llm/contracts.py `premise_evidence` / the criticism case
model; wire: src/deepreason/llm/wire.py.

END STATE: an AUDIT_REPORT.md row. Under the all-configurations law a
disclosure is the right shape, never a refusal.
```
