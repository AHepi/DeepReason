# REQUEST — Rung 3a: delete the successor spawn trigger (H1)

Route: `dr-change-orchestrator`. **Rung 3a of the v2 calculus program**
(`experiments/2026-08-14-change-calculus-reconciliation-v2/LADDER.md`).
Date: 2026-08-15. Branch: `claude/calculus-rung2-step2-premise-pes36e`.

## 1. Authority

Operator, verbatim, RIDER 5 item (6):

> confirm the delivered Rung 2 removed scan_spawns' refuted⇒successor loop and
> carries the frontier-unchanged-under-refutation regression with its mutation
> proof — if absent, it is the next step, alone

**Checked: ABSENT** (`RECONCILIATION.md` §2P). So this tranche exists, and
"alone" is a scope constraint with teeth: it forced Rung 3 to split, and 3b
(frame-separation) does not ride along.

Operator, verbatim, closing the same exchange:

> just continue autonomously until complete.

Substantive authority, all previously ledgered:

- **H1** (pre-decided): a failed conjecture mints nothing. Failure may redirect
  ATTENTION only.
- **Rung 2's DELIVERY**: the replacement exists — *translate* is the remaining
  path by which a problem is replaced, and it fires from an adjudicated
  resolution rather than from a refutation.
- **The external advice** (`docs/proposals/CALCULUS_IMPLEMENTATION_ADVICE.md`,
  "H1 must land before problem subjects"), advisory: remove the loop, keep the
  enum, prove refutation alone cannot grow the frontier, prove every other
  structural trigger still works, and mutation-prove the regression.
- **The 2026-08-14 law**: old roots are owed neither validity nor readability.

## 2. Requirements

| # | Requirement | Source |
|---|---|---|
| N1 | The refuted⇒successor branch is REMOVED from `rules/spawn.py::scan_spawns`. | H1, R63 |
| N2 | **The decisive regression, from the advice verbatim**: `before = set(problems)`; refute a candidate; `scan_spawns`; `assert set(problems) == before`. | R63 |
| N3 | **A MUTATION proof**: restoring the old loop must FAIL N2's test. A deletion is exactly the change whose test passes vacuously. | R63 |
| N4 | Every OTHER structural spawn trigger still fires — connection, discrimination, debt, remove-arbitrariness, research. "Nothing spawns" must not be able to masquerade as success. | R63 |
| N5 | No addressability is lost: every problem addressable before the deletion is addressable after. | LADDER Rung 3a |
| N6 | The map moves in the SAME COMMIT — `SUB-rules.md`'s successor-inheritance row and `SEAM-ontology-x-rules`' `test_successor_descriptions_do_not_nest` check. | SCHEMA.md |
| N7 | Errata for the two documents this falsifies: `harness-spec-v1.3.md` §3 + §7, and `COMPUTABLE_CALCULUS.md` §5 + §9.6. | EC-1, EC-2 |
| N8 | **ALONE.** Nothing else ships in this tranche — not frame-separation (3b), not problem subjects, not P4. | R63, operator's word |

## 3. Map preflight

`DR-INV-frozen-surfaces` first — this touches none of the five.
`DR-SEAM-ontology-x-rules` (owns `ontology/problem.py` + `rules/spawn.py`, and
carries the nesting check), `DR-SEAM-scheduler-x-rules` (`scan_spawns` is the
one rule the scheduler runs unconditionally), then `DR-SUB-rules`,
`DR-SUB-ontology`, `DR-CON-scheduler-ranking` (reflexive lineage reads the
trigger), `DR-CON-schools` (ownership-by-provenance reads it too).

## 4. Amendments

(none yet)
