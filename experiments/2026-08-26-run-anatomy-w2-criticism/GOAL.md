# GOAL — W2, criticism anatomy (RUN ANATOMY PROGRAM)

**Tranche dir.** `experiments/2026-08-26-run-anatomy-w2-criticism/`
**Route.** `deepreason-orchestrator`, measurement variant: GOAL → record
census (the `dr-diagnose` slot, evidence from the typed record only) →
RESULTS.md honest ledger. **READ-ONLY on `src/` and `tests/`.** No fix
phase exists in this tranche; defects found become PARKED.md prompts.
**Date.** 2026-08-26. **Branch.** `claude/criticism-anatomy-w2-1z2029`.

## The one question

Over every committed root that recorded criticism: **what did criticism
attack, was it correct where correctness is mechanically checkable, and
did it ever do causal work on what the run produced next?**

"Causal work" is the research ledger's Q5 triple, measured on our own
records for the first time:

- **CouplingRate** — of criticized candidates, the fraction whose seat's
  NEXT candidate changed in the criticized respect.
- **RepairRate** — of those coupled changes, the fraction that helped by
  the run's own measure (checker score in P-C1; survival in P-R1).
- **NeglectRate** — of criticized candidates, the fraction where the
  criticism was carried on the record and the next candidate ignored it.

## Priority roots (derived here; W1 owns the program inventory)

W1's root inventory is **not yet pushed** to `origin/main` at branch
creation (`git ls-remote --heads origin` shows no W1 branch, `bdb516ae4`
carries no run-anatomy program directory). This tranche therefore derives
its own root list and records the derivation so the synthesis round can
diff the two.

| Root | Crit events | Why |
|---|---|---|
| `experiments/2026-08-25-poietics-program/run` (P-R1) | 207 | the priority root; 104 refuted |
| `experiments/2026-08-25-change-constructive-frontier/run` (P-C1 ARM H, attempt-4) | 189 (grep proxy) | the only root whose criticism is checkable against a deterministic program verdict |

Derivation command (committed, re-runnable):

    for f in $(find experiments -name log.jsonl); do d=$(dirname $f); \
      echo "$(python3 -c "import json,sys;print(sum(1 for l in open('$f') if json.loads(l).get('rule')=='Crit'))")  $d"; done | sort -rn

Roots beyond the two priorities are censused for the TARGETS dimension
only if they carry Crit events; the Q5 rates need a per-seat candidate
sequence and a run-owned score, which only the two priority roots have.

## Success criterion (falsifiable)

The tranche succeeds if, for each priority root, all four census
dimensions below produce a table whose every cell is derived by a
committed script from `log.jsonl` + `objects/` (no hand counting), and
the three Q5 rates are stated with their denominators and their
unmeasurable residue named.

1. **TARGETS** — attack-target taxonomy with counts.
2. **COMMITMENT ATTACKS** — correct / misquoted / attacked-nonexistent /
   unverifiable, judged mechanically.
3. **CAUSAL WORK** — CouplingRate, RepairRate, NeglectRate per root.
4. **LABEL WORK** — which criticisms moved a status; of the refutations,
   demonstrative (program verdict) vs prose-only.
5. **THE P-C1 QUESTION** — 132 candidates, best score frozen from cycle
   10: did any criticism event ever precede a score improvement in the
   criticized lineage? One number.

The tranche FAILS honestly (and says so) if a dimension cannot be derived
from the record — e.g. if the record does not link a criticism to the
seat's next candidate. An unmeasurable dimension is recorded as
unmeasurable, not estimated.

## Map preflight (ids resolved before any measurement)

Read in this order, per `dr-drive-harness` §4:

- `docs/map/INDEX.md` — routing.
- `docs/map/INV-frozen-surfaces.md` — five surfaces. **Not applicable to
  this tranche by construction**: nothing under `src/` or `tests/` is
  modified, and the gate is `git diff --stat origin/main` proving it.
- `DR-CON-warrants-and-attacks` — read BEFORE the record, because it owns
  the definition of "refutation" this census must not invent:
  *"an artifact reaches `Status.REFUTED` through one chain and no other:
  some artifact CARRIES a registered `Warrant` naming it as target, that
  carriage materializes an attack edge in `att`, and the grounded
  extension finds the attacker accepted."* Consequences this census
  obeys: the edge builder is **blind to `WarrantType`**, so demonstrative
  vs prose is a fact about the MINT SITE, not about force; `state.carries`
  (not `Artifact.warrants`) is the carriage authority; and mutual attack
  is `suspended`, never refuted.
- `DR-CON-criticism-source` — the socket that attacks a target
  (`rules/crit.py`).
- `DR-SUB-adjudication` — warrants → attack edges → status labels.
- `DR-SEAM-adjudication-x-rules` — the seam the census reads across.
- `DR-SUB-ontology` — `Artifact`, `Commitment`, `Warrant`, `Interface`.

## Scope contract

- READ-ONLY on `src/` and `tests/`. Gate: `git diff --stat origin/main`
  names no path under either.
- Committed run roots are never modified; every root is opened
  `read_only=True` (a writable open repairs, i.e. destroys, the evidence).
- One tranche, one goal. Anything else noticed → `PARKED.md` with a
  ready-to-send prompt.
- Model prose is not evidence — including the criticism prose this census
  quotes. Quoted prose is the OBJECT of measurement; every COUNT comes
  from the typed record.
