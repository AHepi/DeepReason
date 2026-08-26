<!-- DR-TRANCHE-F3 -->
# Validation — every acceptance check in SPEC.md, run

Verdict: **PENDING** — filled in below as each instrument returns. The full
gate and the wheel smokes are the last two.

## Per-item acceptance

| item | R | accept | result |
|---|---|---|---|
| S0 | R20 | the verification, recorded before any code | **DONE** — SPEC.md §S0, with M4–M6 |
| S1 | R1–R4, R18, C1, C2 | registry shape, defaults, absences | PASS |
| S2 | R4, R18 | one toggle, typed notice on an unknown id | PASS |
| S3 | R1, R6, C1 | research compiles enabled with a reachable allowlist | PASS |
| S4 | R2, R4 | simulation byte-identical on, empty policy off | PASS |
| S5 | R3, R5, C1, C2 | code-testing declared on, proved by driving the road | PASS |
| S6 | R5, C2 | the website is a declared absence | PASS |
| S7 | R6 | the digest cost, priced | **DONE** — MEASUREMENTS.md |
| S8 | R8, R12, R18 | the knobs, and no digest motion from them | PASS |
| S9 | R9, R12, R18, C6 | the policy interface and its registry | PASS |
| S10 | R9, R10 | candidacy gating, floor holds, never starves | PASS |
| S11 | R10, R12 | the disclosure and the attackable policy artifact | PASS |
| S12 | R11 | the label differential, mutation-proven | PASS — `proof/s12_mutation.txt` |
| S13 | R13 | the four phantoms emit | PASS |
| S14 | R13, R16, R12 | the two new signals declared with producers | PASS |
| S15 | R14 | every configuration class compiles | PASS |
| S16 | R15 | the stub run with an aggressive self-spawner | PASS |
| S17 | R19, R18, C6 | the architecture tests | PASS — `proof/s17_bypass.txt` |
| S18 | R17 | docs_verify full / audit / links | PASS (full: 0 failed) |
| S19 | R21, R9 | the decision reaches the dispatch | PASS |
| S20 | R20, R21 | the regression that keeps it reached | PASS |
| S21 | R22 | the design consequence, stated | **DONE** — SPEC.md §S21 |
| S22 | R23 | the road exists in every launch path | PASS |
| S23 | R24 | prose keeps its full standing | PASS |

## Instruments

| instrument | result |
|---|---|
| `python tools/docs_verify.py` (full) | **0 failed**, 65 documents, 1083 checks |
| `python tools/docs_verify.py --links` | **0 dangling**, 65 documents |
| `python tools/diff_budget.py 4760a32ef --ceiling 1900 --paths src tests docs` | **WITHIN** — 1870 (src 690, tests 699, docs 481) |
| `python -m pytest tests/ -q -n 4` | pending |
| `python scripts/wheel_smoke.py` | pending |
| `python -u scripts/wheel_operational_smoke.py` | pending |

Note on `--audit`: run with the full pass below.

## Fixtures that moved, and the guarantee each still carries

Seven tests across six files. In every case the guarantee is still asserted and
only a constant the design predicted has moved; no assertion was weakened.
The full table, with the reason per row, is in MEASUREMENTS.md.

Two of them are FINDINGS rather than maintenance, and are worth reading as
results of this tranche rather than as costs of it:

- `tests/test_rotation.py::test_attempt_cap_frees_the_rotation` needs twelve
  cycles where it needed eight, because the wander cap gives the self-spawned
  discrimination problem fewer turns. The futility cap still holds at exactly 2,
  now pinned at twelve cycles AND at twenty-four.
- `tests/test_rotation.py::test_legacy_starvation_reproduced` now reproduces its
  defect under `ATTENTION_ALLOCATION_POLICY="open-lineage.v1"`, because the
  shipped cap RESCUES that shape. A new test pins the rescue. The starvation that
  module was written for is a self-spawned lineage crowding out the operator's
  seeded problem — the same failure W6 measured at scale, closed here with no
  rotation machinery involved at all.

## Residue — what remains unproven

Stated plainly, per the honest-ledger rule. Accepted does not mean true.

1. **No live run has witnessed either half.** The wire fix and the wander cap
   are proven offline and mutation-proven; no committed root yet shows a
   controller decision reaching a provider call, or the throttle engaging.
   Parked as P2 and P3 with ready-to-send prompts; they share one ladder.
2. **The code-testing channel has no off-switch.** Delivered ON and checked;
   R4's OFF state is delivered for two channels of three. Parked as P1 with the
   measured blast radius (33 assertions across eleven files) that made
   improvising it the wrong call.
3. **The default research allowlist is an assumption, not an operator ruling.**
   `("arxiv.org", "en.wikipedia.org")` is the smallest honest default for a
   channel that cannot be enabled with an empty list. Changing it costs one
   requalification and one line.
4. **The floor's value is calibrated from ONE run.** 0.5 is the value that
   would have bound on P-C1 ARM H and not before it. One post-mortem is not a
   distribution.
5. **75-odd registry names are still declared and silent**, and eight tags are
   emitted 18 151 times without being declared at all. Parked as P4; the second
   gap is the larger one.
