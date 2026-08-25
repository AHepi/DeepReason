# CHECKLIST — the constructive frontier, and P-C1

State: **step 9 of 13 — steps 1-8 done, ARM H ready to launch**

One step per `dr-execute-step` invocation. A step is checked ONLY with its
real done-criterion output pasted beneath it, copied from the terminal. No
step is checked in advance of running it. Every step cites SPEC.md items and
REQUEST.md requirements.

---

- [x] **1. PROGRAM v2** — amend
      `experiments/2026-08-25-poietics-program/PROGRAM.md`: v2 header,
      P-R2/P-R3 CANCELLED with the operator's verbatim words as the
      cancelling authority, the series renamed to CONSTRUCTIVE FRONTIER,
      the problem class registered, P-C1 registered.
      *(S12; R5, R6, R7, R8)*
      **Done-criterion:** greps show the v2 header, both CANCELLED
      markers, the operator's quoted words, the problem class, and P-C1.

- [x] **2. The checker** — `checker.py`: exact-rational scorer, the four
      validity rules, the claim check, `--score` and `--self-test`.
      *(S3; R12, R13, R14)*
      **Done-criterion:** `python checker.py --score` on a known-good
      construction prints `"valid": true` with an exact rational score.

- [x] **3. The checker's mutation proof** — the S4 table, RED then GREEN.
      *(S4; R16)*
      **Done-criterion:** each of M2 and M3 shown FAILING against a
      deliberately weakened checker (RED), then caught by the real one
      (GREEN); `python checker.py --self-test` exits 0.

- [x] **4. The in-run demarcation battery** — the three `predicate:`
      commitments, written to be evaluated by `programs.evaluate`.
      *(S5; R15)*
      **Done-criterion:** all three pass `programs._validate_predicate`.

- [x] **5. The criteria preflight** — `preflight_criteria.py`: validity,
      the mutation table through the harness's own evaluator, the
      float-vs-exact bound, and the discrimination controls.
      *(S6; the `DR-SEAM-evaluation-x-ontology` malformed-predicate trap)*
      **Done-criterion:** `python preflight_criteria.py` exits 0.

- [x] **6. ARM H's configuration and builder** — `run-config.yaml`,
      `build_manifest_pc1.py`, `pc1_run.sh`, `snapshot_loop.sh`.
      *(S7; R20, R28)*
      **Done-criterion:** `DRY_RUN=1 ./pc1_run.sh` exits 0 without a
      provider call.

- [x] **7. The soak case** — one `SoakCase` entry in
      `scripts/cycle_soak.py`, in this same commit.
      *(S11; R26)*
      **Done-criterion:** `python -u scripts/cycle_soak.py --case pc1`
      exits 0, verbatim output pasted.

- [x] **8. PREREG frozen and pushed** — `PREREG.md` carrying the question,
      both arms, the matched-budget rule, the registered prediction, the
      milestones and the repeat authorisation. Pushed BEFORE any provider
      call.
      *(S8, S9, S10; R17, R18, R19, R21, R22, R23, R24, R25)*
      **Done-criterion:** `PREREG.md` committed and pushed; the push
      precedes the first entry in `driver.log`.

- [ ] **9. ARM H launch** — detached, snapshot loop armed. Requires the
      operator's key (R27).
      *(S7; R20, R28)*
      **Done-criterion:** the run reaches a typed terminal; `verify_root`
      clean; `deepreason results` captured.

- [ ] **10. ARM S run** — `arm_s.py` to the measured matched budget.
      *(S8, S9; R21)*
      **Done-criterion:** `arm_s/results.jsonl` exists, cumulative tokens
      within the S9 band of ARM H's actual spend.

- [ ] **11. The census** — `milestone_census.py` decides M1/M2/M3 from the
      typed record and the checker outputs alone.
      *(S10; R4, R24, R31)*
      **Done-criterion:** `milestones.json` written; survivor figures
      conjecture-only.

- [ ] **12. RESULTS.md** — the honest ledger: both best scores, the
      margin, the refutation count, the residue.
      *(S13 C9; R2, R30)*
      **Done-criterion:** every number in it traces to a typed artifact or
      a checker output.

- [ ] **13. VALIDATION.md + DELIVERY.md** — every S13 acceptance check
      proven; R-by-R reconciliation; `git diff --stat` showing one file
      changed outside this directory.
      *(S13; R32)*
      **Done-criterion:** VALIDATION verdict PASS, DELIVERY table complete.

---

## Step outputs

*(Each step's verbatim terminal output is appended here as the step is
executed. Nothing is written here in advance.)*

### Step 1 — PROGRAM v2 (R5, R6, R7, R8) ✅

```
$ grep -c "CONSTRUCTIVE FRONTIER" experiments/2026-08-25-poietics-program/PROGRAM.md
2
$ grep -n "STATUS: CANCELLED" experiments/2026-08-25-poietics-program/PROGRAM.md
148:## P-R2 — the premises run — **STATUS: CANCELLED 2026-08-25**
210:## P-R3 — the succession trial — **STATUS: CANCELLED 2026-08-25**
$ grep -n "I needs to solve a tough problem" experiments/2026-08-25-poietics-program/PROGRAM.md
11:> change the research program a bit. I needs to solve a tough problem.
151:("change the research program a bit. I needs to solve a tough problem.
$ grep -n "Circle packing\|^- \*\*Heilbronn" experiments/2026-08-25-poietics-program/PROGRAM.md
39:- **Circle packing** — maximise the minimum radius of N equal circles
41:- **Heilbronn** — maximise the minimum triangle area over all triples of N
$ grep -n "^## P-C1\|P-C1  construction" experiments/2026-08-25-poietics-program/PROGRAM.md
64:## P-C1 — the first constructive run — **STATUS: RUNS IN THE SUCCESSOR**
285:    P-C1  construction  RUNS in experiments/2026-08-25-change-constructive-
```

P-R2's and P-R3's registered text is RETAINED beneath the CANCELLED
markers (SPEC S12). Both had MET their preconditions, so both are recorded
as redirected, not dropped for cause.

### Step 2 — the checker (R12, R13, R14) ✅

```
$ python checker.py --score fixtures/known_good.txt
{
  "above_floor": true,
  "claim": 0.013307,
  "claim_confirmed": true,
  "code": null,
  "n_points": 13,
  "n_triples": 286,
  "score": 0.013307680842,
  "score_exact": "6653840421/500000000000",
  "valid": true
}
```

286 triples = C(13,3), and the exact rational is carried beside the rounded
figure per SPEC S3's declared A10 precision policy.

**Recorded, because it is evidence the guard bites:** on its first run the
checker REFUTED its own fixture with `CLAIM_INFLATED`. The fixture wrote its
claim with `:.6f`, which rounded 0.0133076808… UP to 0.013308 — above the
exact score. The fixture now truncates instead of rounding, since truncation
can only under-claim and under-claiming is honest (M8).

### Step 3 — the mutation proof (R16) ✅

RED first: each guard was disabled in `checker.py`'s REAL source (a targeted
textual edit, exec'd as a fresh module) and the mutation was shown to slip
past it. A test never observed failing proves only that it runs.

```
$ python mutation_proof.py
=== RED: one guard disabled at a time, the mutation must SLIP THROUGH ===
  M2 planted overlap (duplicate point)       guard off -> code=CLAIM_INFLATED           SLIPPED (as required)
  M3 inflated claim (-> 0.9)                 guard off -> code=None                     SLIPPED (as required)
  M4 point outside the square                guard off -> code=CLAIM_INFLATED           SLIPPED (as required)
  M5 twelve points, not thirteen             guard off -> code=DUPLICATE_POINT          SLIPPED (as required)
  M6 no CLAIM line                           guard off -> code=RAISED TypeError         SLIPPED (as required)

=== GREEN: the unmodified checker must CATCH every one ===
  M1 known-good construction                 valid=True  code=None             score=0.013307680842   OK
  M2 planted overlap (duplicate point)       valid=False code=DUPLICATE_POINT  score=None   OK
  M3 inflated claim (-> 0.9)                 valid=False code=CLAIM_INFLATED   score=0.013307680842   OK
  M4 point outside the square                valid=False code=OUT_OF_SQUARE    score=None   OK
  M5 twelve points, not thirteen             valid=False code=WRONG_COUNT      score=None   OK
  M6 no CLAIM line                           valid=False code=NO_CLAIM         score=None   OK
  M7 collinear triple (valid, worthless)     valid=True  code=None             score=0.0   OK
  M8 honest under-claim                      valid=True  code=None             score=0.013307680842   OK

RED 5/5 slipped through their disabled guards; GREEN 8/8 correct.
$ python checker.py --self-test; echo "exit $?"
8/8 cases correct
exit 0
```

R16's two named mutations are M2 (planted overlap) and M3 (inflated claim);
both are RED-then-GREEN above. Note the RED column shows the guards OVERLAP
— with distinctness off, M2 is still caught downstream by CLAIM_INFLATED.
That is defence in depth, and it is why each guard is disabled singly.

### Step 4 — the demarcation battery (R15) ✅

```
$ python -c "from deepreason.programs import _validate_predicate; import criteria; [ (_validate_predicate(c.eval.split(':',1)[1]), print('SAFE ', c.id)) for c in criteria.CRITERIA ]"
SAFE  frontier-wellformed@v1
SAFE  frontier-claim-honest@v1
SAFE  frontier-above-floor@v1
```

### Step 5 — the criteria preflight (the malformed-predicate trap) ✅

```
$ python preflight_criteria.py; echo "exit $?"
== 1. every predicate is sandbox-legal ==
  SAFE  frontier-wellformed@v1
  SAFE  frontier-claim-honest@v1
  SAFE  frontier-above-floor@v1
  SAFE  criteria.py and checker.py share the same wire regexes

== 2. the S4 mutation table, through programs.evaluate ==
  M1 known-good construction                 wellformed=pass claim=pass floor=pass   OK
  M2 planted overlap (duplicate point)       wellformed=fail claim=fail floor=fail   OK
  M3 inflated claim (-> 0.9)                 wellformed=pass claim=fail floor=pass   OK
  M4 point outside the square                wellformed=fail claim=fail floor=fail   OK
  M5 twelve points, not thirteen             wellformed=fail claim=fail floor=fail   OK
  M6 no CLAIM line                           wellformed=pass claim=fail floor=pass   OK
  M7 collinear triple (valid, worthless)     wellformed=pass claim=pass floor=fail   OK
  M8 honest under-claim                      wellformed=pass claim=pass floor=pass   OK

== 3. float-vs-exact agreement (SPEC S3's declared A10 bound) ==
  20000 configurations at the 6-dp grid
  max |exact - float| = 9.459663954936e-17   bound 1e-12   OK

== 4. discrimination controls ==
  prose with no construction              {'wellformed': 'fail', 'claim-honest': 'fail', 'above-floor': 'fail'}   OK
  random configuration (seeded)           {'wellformed': 'pass', 'claim-honest': 'pass', 'above-floor': 'fail'}   OK
  the plain circle of 13                  {'wellformed': 'pass', 'claim-honest': 'pass', 'above-floor': 'pass'}   OK

PREFLIGHT OK -- the battery discriminates and no predicate is malformed
exit 0
```

The battery is a conjunction, so a candidate is refuted when ANY member
fails; a member is not required to fail for every reason. The random-config
control is the important one: a lucky draw passes well-formedness and its
own honest claim, and the FLOOR is what refutes it.

### Step 6 — ARM H's configuration and builder (R20, R28) ✅

```
$ python build_manifest_pc1.py <tmp-root>
{
  "attached_evidence_enabled": false,
  "compile_notices": [],
  "criteria": ["frontier-wellformed@v1", "frontier-claim-honest@v1", "frontier-above-floor@v1"],
  "dossier_sources": 0,
  "judge_seats_enabled": false,
  "manifest_sha256": "6913328037a61ca68c7599ca0f10ba78de3bab616884503b4d28a110ca6dbca4",
  "problem_id": "question-64b724c4118320989925d111501a8e41",
  "question_sha256": "64b724c4118320989925d111501a8e41cd4518d9b631bb81a6ae048d3cfb5c7e",
  "run_input_digest": "740edc4de464aad2b8b830060af77431825c034d63d6fe67f856961541870327"
}

$ DRY_RUN=1 ./pc1_run.sh; echo "exit $?"
[...] SETUP OK rc=0
[...] PREFLIGHT OK rc=0                 (criteria battery)
[...] CHECKER OK rc=0                   (RED 5/5, GREEN 8/8)
[...] MODEL PREFLIGHT OK rc=0           (11 seats, all glm-5.2, listed in the live catalogue)
[...] DRY RUN: stopping before qualify -- no provider call made, rehearsal root removed, rc=0
exit 0
```

The question was factored into `question.py` after the first build so both
arms read the SAME BYTES rather than each holding a copy; `question_sha256`
and `manifest_sha256` are unchanged across that refactor, which is the proof
it changed nothing.

### Step 7 — the soak case (R26) ✅

One `SoakCase` entry in `scripts/cycle_soak.py`, in the same commit. Full
verbatim output: `soak-pc1.out`.

```
$ python -u scripts/cycle_soak.py --case pc1
CYCLE SOAK -- case pc1
========================================================================
  manifest sha256        c6edfc2a5ae2cb2dd056a27df3c9ee512fd688a720b5dd6411e95a8681dfa5cc
  criteria               frontier-wellformed@v1, frontier-claim-honest@v1, frontier-above-floor@v1
  attached evidence      False
  cycles requested       24
  qualification          rc=0 (2.7s)
  drive                  349.3s, 27 progress events

-- S1 run assertions ---------------------------------------------------
  [PASS] A1-typed-terminal            state='completed' stop_reason='budget_exhausted' typed_error=None
  [PASS] A2-no-operational-failure    stop_reason='budget_exhausted'
  [PASS] A3-verify-root-clean         0 violation(s)
  [PASS] A4-cycles-reached            reached cycle 24 of 24 requested; the deepest recorded death was cycle 2

-- S2/S4 seam coverage -------------------------------------------------
  [PART] D1-seat-contract         seat contracts with repairs
         reason: seat contracts exercised, but zero repair attempts: the deterministic stub always returns a schema-valid response, so attempt_index never advances past 0 offline
  [PASS] D2-route-lease           lease-checked routes with tuning
  [PASS] D3-budget-auth           budget authorization
  [PASS] D4-reservation-bound     reservation/dispatch bounds

[soak] exit 0 (clean)
```

**This settles the one open design risk.** ARM H combines
`ENGAGED_CRITICISM_AUTHORITY: defended_trial` with `JUDGE_SEATS_ENABLED:
false` — a shape no committed run has used (P-R1 ran defended trials with
judge seats ENABLED and simply never called them). The soak drives THIS
shape to cycle 24 of 24 with a typed terminal and a clean `verify_root`, so
the no-judge posture is demonstrated offline rather than assumed. D1's
PART is the stub's standing limitation for every case, not a pc1 finding.

### Step 8 — PREREG frozen and pushed (R17–R25) ✅

`PREREG.md` committed and pushed before any provider call, at commit
`9f49e4c5e`.

**The ordering proof, stated precisely.** `driver.log` DOES exist at that
commit — the dry run of step 6 wrote it. It contains no `QUALIFY` and no
`REASON` line, and ends with `DRY RUN: stopping before qualify -- no
provider call made`. So the correct statement of R17's proof is: at the
commit that froze PREREG.md, no provider inference call had been made, and
the driver log proves it by what it does NOT contain. (The model preflight
does reach the network, but only `https://ollama.com/v1/models`, which
answers unauthenticated and lists model ids; it dispatches no completion
and consumes no tokens.)
