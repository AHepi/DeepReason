# DELIVERY — the constructive frontier, and P-C1

`VALIDATION.md` verdict: **PASS**. This closes the tranche.

## Requirement-by-requirement reconciliation

Every requirement from `REQUEST.md` §B, against what was actually done.

| # | Requirement (abbreviated) | Delivered | Where |
|---|---|---|---|
| R1 | Redirect to a tough problem forcing imagination | ✅ | Heilbronn N=13; the obvious symmetric answers score exactly 0.000000, measured |
| R2 | Beat one-shot prompting, MEASURED, or the spend is not justified | ✅ **measured — and NOT beaten** | `RESULTS.md`: ARM S 0.0136 vs ARM H 0.0004 at matched budget. Reported as the operator's criterion failing, not hidden |
| R3 | Route through `dr-change-orchestrator` | ✅ | REQUEST → SPEC → CHECKLIST → stepwise → VALIDATION → DELIVERY |
| R4 | Judge on TYPED OUTCOMES ONLY | ✅ | Every figure from `run-status.json`, `run-stop.json`, `verify_root`, or `checker.py` |
| R5 | Amend `PROGRAM.md` to v2 | ✅ | v2 header, series renamed |
| R6 | P-R2/P-R3 CANCELLED, ledger the words | ✅ | Both marked CANCELLED with A1 quoted verbatim; registered text retained |
| R7 | Program becomes CONSTRUCTIVE FRONTIER | ✅ | `PROGRAM.md` title and status block |
| R8 | Register the problem class (packing + Heilbronn) | ✅ | `PROGRAM.md` "The problem class this series works in" |
| R9 | ONE instance, N in 13..16, choice REASONED in SPEC | ✅ | SPEC §S1, Heilbronn N=13 |
| R10 | Prefer simplest checker + unsettled space | ✅ | Both decided by `instance_probe.py`, not assertion |
| R11 | No web access; internal baseline is the comparator | ✅ | No web lookup anywhere; ARM S is the comparator |
| R12 | The checker: one new code file, an EXPERIMENT script not `src/` | ✅ | `checker.py`; `git diff -- src tests` empty |
| R13 | Validity: inside the square, distinctness | ✅ | V1–V4, `OUT_OF_SQUARE` / `DUPLICATE_POINT` / `WRONG_COUNT` / `NO_CLAIM` |
| R14 | Score min triangle area, EXACT arithmetic, declared precision | ✅ | `fractions.Fraction` end to end, no rounding until reporting; A10 policy declared in SPEC §S3 |
| R15 | Checker doubles as demarcation battery; NO JUDGE | ✅ | Three `predicate:` criteria; `JUDGE_SEATS_ENABLED: false`, `rubric_policy: forbid`; **0 judge calls** in the record |
| R16 | Mutation-prove: planted overlap + inflated claim must FAIL; paste RED/GREEN | ✅ | `mutation_proof.py`, RED 5/5 then GREEN 9/9, pasted in CHECKLIST step 3 |
| R17 | Freeze PREREG before any API call | ✅ | Pushed at `9f49e4c5e`; ordering proof stated precisely |
| R18 | The registered question template | ✅ | First sentence verbatim, N and objects instantiated |
| R19 | Two arms, matched budget, registered BEFORE launch | ✅ | PREREG §3/§4; match ratio 1.009 |
| R20 | ARM H: solo, everything on, checker-backed refutation, deep cycles | ✅ **with a deviation** | 24 cycles registered; the run stopped at 15 on a typed seat exhaustion (P3) |
| R21 | ARM S: same model, same budget, blind one-shot, no harness machinery | ✅ | `arm_s.py` imports `checker` + stdlib only |
| R22 | Register honestly that sampling may win | ✅ **and it did** | PREREG §5 registered it; RESULTS reports it as a real result |
| R23 | Value claimed ONLY on margin, sustained on the repeat | ✅ **no value claimed** | `harness_claims_value: false` |
| R24 | Milestones: best score/arm, refutation count, transferable pattern | ✅ | M1 met, M2 met (117 + 15), M3 reported not scored |
| R25 | One repeat pre-authorized; quote with spread | ⚠️ **PARTIAL — repeat NOT run** | Spread IS stated for both arms. The repeat was authorised and not spent; recorded as residue item 1 |
| R26 | Soak law: extend the case table, same commit, exit 0 | ✅ | `pc1` case; exit 0, 24/24 cycles, `verify_root` clean |
| R27 | Ask for the key only after the soak is green | ✅ | Key written to the gitignored `env` only after the soak passed |
| R28 | Launch H detached with snapshot loop; S is a script | ✅ | `setsid nohup`, `snapshot_loop.sh` armed on the driver PID |
| R29 | Commit both records | ✅ | ARM H root, ARM S ledgers and every raw reply |
| R30 | RESULTS.md: both scores, margin, refutation count, residue | ✅ | All four, plus 7 residue items |
| R31 | Survivor counts: quote conjecture-only | ✅ **vacuously — and that is itself a finding** | Both raw and filtered are 0: the failed run wrote NO survivor record. Parked P4 |
| R32 | No `src`/`tests` change beyond the soak case line | ✅ | `git diff --stat 43f408506 HEAD -- src tests` empty |
| R33 | Commit and push every phase boundary, with retry | ✅ | Eight commits, each pushed with 2/4/8/16s backoff |

**One requirement is PARTIAL: R25.** The repeat was pre-authorized and was
not run — the session's live budget went to one voided run and five
qualification batteries. The spread half of R25 IS delivered. Since the
harness is claiming no value, the untested part is whether the LOSS
replicates, which matters less than a untested WIN would have, but it is
untested and is stated as residue rather than glossed.

## Deviations from SPEC, stated plainly

1. **The wire format was corrected after launch.** SPEC §S2's anchored
   regexes were wrong: seats emit `output_mode: json_object`, so
   constructions arrive in a JSON envelope with escaped newlines. Measured:
   anchored matched 0 of 1509 artifacts, unanchored 183. The first run is
   VOID and retained unquoted. PREREG gained an appendix; its frozen
   sections were not edited.
2. **ARM H ran 15 of 24 cycles**, ending on a typed
   `V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY`. Parked P3.
3. **ARM S ran in three segments** (worker restart, then an uncaught
   `RemoteDisconnected`), each carrying the remaining budget, summing to one
   matched arm.
4. **Qualification needed retries** — five batteries, ~50% pass rate, always
   the same contract. Parked P1. The run's green came on a retry, and that
   is stated wherever the run is quoted.

## The operator's own criterion

> results must beat what one-shot prompting buys, measured, or the spend is
> not justified.

**Measured: they did not.** ARM S beat ARM H by 33× at a 1.009 budget
match, on the instance chosen to make the sampler's job hardest. By the
operator's stated criterion, the harness's spend on this problem class is
not justified — and the measurement, not the harness, is what this tranche
was built to produce.

## Parked

P1 intermittent qualification failure · P2 zero token counter · P3 seat
capability exhaustion · P4 no survivor record on a failed run · P5 a
preflight cannot catch a wrong-shape predicate. All five carry
ready-to-send prompts in `PARKED.md`.
