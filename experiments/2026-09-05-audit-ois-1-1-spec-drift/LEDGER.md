# LEDGER — spec-drift audit, DeepReason vs Open Inquiry Specification 1.1

Date: 2026-09-05 (UTC)
Model: claude-opus-5
HEAD: `c26c66de7266968157c61e269fb927c5e368d2c3`
Baselines file sha (`git rev-parse HEAD:docs/AUDIT_BASELINES.md`): `d152664f0edcad2ea0372d9d2cade2d993203b4e`
Scope: the twelve checks of the executor window — §6 of
`docs/proposals/OIS_1_1_to_DeepReason_configuration.md` (ten) plus the
monitor's added checks 11 and 12. Read-only.

Dimension: **spec-drift** only. The other four dimensions (broken, dead,
docs-drift, goal-trace) are out of scope for this window; no `ACTIVATION.md`
is claimed for them.

Baseline for the spec side, re-derived on this container before any check:
`python -m unittest` in `docs/proposals/ois-1.1/verification/` → **66 tests, OK**;
`python run_mutations.py` → **Detected 9/9 selected mutations**
(`proof/check00-baseline.txt`).

| id | dimension | target | gate | verdict | proof file | disposition |
|---|---|---|---|---|---|---|
| 1 | spec-drift | dependency exemption, §11.3 | `proof/check01_repro.py` | DIFFERS IN OUTCOME | `proof/check01-repro.txt`, `-census.txt`, `-census2.txt`, `-mintsites.txt` | parked (P1) |
| 2 | spec-drift | failed check counted as pass, §10 | verdict census | CONFORMS | `proof/check02-failwarrant.txt`, `-verdicts.txt` | baseline |
| 3 | spec-drift | status label into a seat, §1 K-REAL | `proof/check03_record.py` | DIFFERS IN OUTCOME | `proof/check03-status-leak.txt`, `-record.txt` | parked (P2) |
| 4 | spec-drift | critic premises on the wire, §11.1 | field census | NOT REPRESENTED | `proof/check04-critic-contract.txt` | parked (P3) |
| 5 | spec-drift | discharge is not evidence, §9/§10 | `proof/check05_record.py` + 21 tests | CONFORMS | `proof/check05-discharge.txt` | baseline |
| 6 | spec-drift | merge keeps identity/location, §9 | `proof/check12_hardening.py` S17 | DIFFERS IN OUTCOME | `proof/check06-merge.txt`, `proof/check12-hardening.txt` | parked (P4) |
| 7 | spec-drift | maximal appraisals as a set, §12.4 | census | NOT REPRESENTED | `proof/check07-maxima.txt` | parked (P5) |
| 8 | spec-drift | crossing receipts, §10 | receipt census + 26 tests | DIFFERS IN OUTCOME | `proof/check08-crossings.txt` | parked (P6) |
| 9 | spec-drift | stop reasons, §9 | 137-record census | CONFORMS | `proof/check09-stops.txt` | baseline |
| 10 | spec-drift | compatible rivals, §9/S22 | `proof/check10_record.py` | CONFORMS | `proof/check10-rivals.txt` | baseline |
| 11 | spec-drift | the DA-1 rule itself, §11.3 | `proof/check11_da1_vs_harness.py` | DIFFERS IN OUTCOME | `proof/check11-da1.txt` | parked (P7) |
| 12 | spec-drift | Hardening S05/S17/S18/S22 | `proof/check12_hardening.py` | DIFFERS IN OUTCOME (2 of 4) | `proof/check12-hardening.txt` | parked (P8, and P4 for S17) |

**12 rows. 4 baseline, 8 parked. 12 proof files plus the baseline, the rings
run and the close gates.**

Rings re-run (no full gate — read-only audit):
`tests/test_adjudication.py tests/test_adjudication_blindness.py` 15 passed;
`tests/test_discharge_law_line.py tests/test_discharge_channel.py` 21 passed;
`tests/test_seat_section_sources.py` 26 passed. `proof/rings.txt`.

Close gates (`proof/close-gates.txt`): `git status --porcelain -- experiments/`
outside this tranche prints nothing; `git diff --stat` prints nothing. No
committed run root was written; nothing outside the tranche directory changed.
