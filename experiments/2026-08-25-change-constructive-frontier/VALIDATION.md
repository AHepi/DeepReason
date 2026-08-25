# VALIDATION — the constructive frontier, and P-C1

Verdict: **PASS**.

Every SPEC.md §S13 acceptance check is proven below against a committed
artifact or a pasted command output. A PASS here means the CHANGE was
delivered as specified; it says nothing about whether the experiment's
result favoured the harness. It did not, and that is a result, not a
validation failure (PREREG §5 registered it as the honest prior).

| # | Requirement | Check | Verdict |
|---|---|---|---|
| C1 | R5–R8 | `PROGRAM.md` carries the v2 header, both CANCELLED markers with the operator's verbatim ruling, the renamed series, the registered problem class, and P-C1 | **PASS** — CHECKLIST step 1 |
| C2 | R9, R10 | `instance_probe.py` + `instance_probe.out` committed; SPEC §S1 reasons the choice from those numbers | **PASS** |
| C3 | R12, R32 | `git diff --stat 43f408506 HEAD -- src tests` is EMPTY; exactly one file changed outside the tranche dirs (`scripts/cycle_soak.py`) | **PASS** — CHECKLIST step 13 |
| C4 | R13, R14, R16 | `checker.py --self-test` 9/9 exit 0; `mutation_proof.py` RED 5/5, GREEN 9/9; M2 (planted overlap) and M3 (inflated claim) both RED-then-GREEN | **PASS** — CHECKLIST step 3 |
| C5 | R15, map trap | `preflight_criteria.py` exit 0, including fixture M9 (JSON envelope) | **PASS** — CHECKLIST step 5, after the correction below |
| C6 | R17, R18, R19 | `PREREG.md` committed and pushed at `9f49e4c5e`, before any provider inference call; question matches R18's template | **PASS** — with the ordering proof stated precisely in CHECKLIST step 8 |
| C7 | R26, R27 | `cycle_soak.py --case pc1` exit 0 (24/24 cycles, verify_root clean), pasted, before the key was used | **PASS** — CHECKLIST step 7 |
| C8 | R20, R21, R28 | ARM H reached a typed terminal with `verify_root` 0 violations; ARM S produced `results.jsonl` | **PASS** — see the note on ARM H's terminal below |
| C9 | R4, R24, R30, R31 | `RESULTS.md` quotes only typed outcomes and checker outputs; both best scores, margin, refutation count, residue present; survivor figures conjecture-only | **PASS** |
| C10 | R2, R22, R23 | Margin stated with both arms' MEASURED spend (702 789 vs 709 454); no value claimed — `harness_claims_value: false` | **PASS** |

## Two things a reader should not have to dig for

**C8 passed on a FAILED run, and that is the correct reading.** ARM H
terminated `failed` / `operational_failure` at cycle 15 of 24. The
acceptance check asks for a TYPED terminal and a clean `verify_root`, and
it got both: a terminal was committed (`terminal_committed`, seq 3199) and
`verify_root` reports 0 violations. A typed failure is a recorded outcome,
not an absence of one. The underlying capability exhaustion is parked as
P3, and the incomplete 24-cycle run is stated as residue in RESULTS.md
rather than smoothed over.

**C5 passed only after a correction that cost a whole run.** The first
`preflight_criteria.py` passed while the battery it guarded matched 0 of
1509 artifacts live, because every fixture was in the plain-text shape the
criteria assumed rather than the JSON envelope the seats emit. Fixture M9
now pins the envelope shape and the run that produced these results had a
working battery (132 constructions read). The first root is retained,
unquoted, at `void-inert-battery-run-6913328037a61ca6/`. The general gap —
a preflight cannot catch a well-formed predicate aimed at the wrong shape —
is parked as P5.

## Gate

**Not run, and deliberately.** `git diff --stat 43f408506 HEAD -- src
tests` is empty: no production code and no test changed in this tranche.
CLAUDE.md's gate discipline binds commits that change code ("Full gate: N
passed, 0 failed" when code changed); this one does not. The single edit
outside the experiment directories is one `SoakCase` entry in
`scripts/cycle_soak.py`, and its own instrument was run to exit 0 on that
entry (CHECKLIST step 7), which is a stronger check of that line than the
suite provides.
