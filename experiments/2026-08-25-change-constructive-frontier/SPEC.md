# SPEC — the constructive frontier, and P-C1

Authority: `REQUEST.md` R1–R33. Every item below cites the requirements it
discharges. Assumptions recorded where A3 is silent; nothing here invents a
requirement.

Map ids in scope are frozen in `REQUEST.md` §C and not restated.

---

## S1 — the instance (R9, R10)

**Chosen: the Heilbronn triangle problem, N = 13.** Maximise the minimum
area over all triangles formed by triples of 13 points in the closed unit
square. C(13,3) = 286 triangles.

R10 gives two selection criteria. Both are decided by measurement here, not
by preference: `instance_probe.py` is committed alongside this spec and its
verbatim output is `instance_probe.out`. Every number quoted below comes
from that file and re-running the probe reproduces it (every draw is
seeded).

**(a) The checker is simplest.** Heilbronn's score is one expression —
`|cross product| / 2` — over triples, and it is *entirely* rational: no
square roots anywhere, so exact arithmetic is available at every step
(R14). Circle packing's score is `min(half the least pairwise distance,
the least distance to a wall)`, which introduces a square root, and its
validity condition (`r <= x <= 1-r`, `d_ij >= 2r`) is *coupled to the score
itself* — the claimed radius appears on both sides. Heilbronn's validity
(inside the square, all distinct) is independent of its score. Strictly
less machinery, strictly more exactness.

**(b) The search space is unsettled.** Heilbronn optima are proven only for
very small n; n = 13 is best-known-only, from numerical search. Circle
packing in a square is the opposite case, and at the top of the authorised
band it is *degenerate*: N = 16 is the 4x4 grid at r = 1/8 exactly, which
the probe reproduces (`0.125`). An instance whose answer is a tabulated
grid measures recall, not imagination, and would defeat R1.

**Two further measured reasons, both recorded because they are what makes
the instance discriminating:**

**(c) The obvious answers score exactly zero.** Regular and symmetric
constructions contain collinear triples, and a collinear triple has area 0,
which is the minimum, so the whole configuration scores 0. Measured:

    circle of 13, r=0.5                    0.013308
    8-ring + 4-ring + centre               0.000000
    4 corners + 4 edge midpoints + 5 inner 0.000000
    jittered 4x4 grid                      0.000163

This is the property that forces imagination (R1): the intuitive symmetric
answer is the *worst* answer, and nothing but the checker will say so.

**(d) There is dynamic range, and no floor effect.** Random uniform 13-point
draws (2000 samples, `instance_probe.py`): median 0.000227, best 0.002824.
Best-known for n=13 is ≈ 0.033. So there are more than two orders of
magnitude between chance and the frontier — room for two arms to separate.

**Why N = 13 and not 14/15/16.** N = 13 is the smallest in the authorised
band, which means (i) the fewest triples (286), keeping the in-run predicate
cheap, and (ii) the *highest* random baseline in the band. The probe's
medians fall monotonically across it — 0.000227, 0.000174, 0.000137,
0.000112 for n = 13, 14, 15, 16 — so chance does best at n = 13. Point (ii)
is the honest direction: N = 13 is where ARM S is STRONGEST, so choosing it
makes the harness's claim under R23 harder to earn, not easier.

*Correction, recorded rather than quietly fixed:* an earlier scratch run of
this probe reseeded once for the whole band instead of once per n, and I
read a monotonic decline in the best-of-2000 column off it. The committed
`instance_probe.py` seeds per n and shows that column is NOT monotonic
(n = 14 peaks at 0.003156). Only the MEDIAN column is monotonic, and only
the median claim is made above.

**Assumption A-S1** (A3 silent): "unsettled" is asserted from the structure
of the problem, not from a literature lookup — R11 forbids needing web
access and makes ARM S the comparator. Any published record the operator
later supplies is a stretch line, not a gate (R11).

---

## S2 — the wire format (assumption A-S2, A3 silent)

A3 requires only that "every candidate must state its coordinates and
claimed score". A candidate must be machine-readable for R15 to be possible
at all, so the format is fixed here and frozen into the question:

    POINT <x> <y>        one line per point, exactly 13 lines
    CLAIM <v>            one line, the claimed minimum triangle area

`<x>`, `<y>`: decimals in `[0, 1]` with **at most 6 decimal places**.
`<v>`: a decimal, exponent notation permitted.

Line-anchored keywords are used rather than bare parenthesised pairs so
that prose elsewhere in a candidate cannot be misparsed as a construction.

**Extraction is defined once**, as the regex pair below, and is byte-shared
between the offline checker and the in-run predicate:

    (?m)^[ \t]*POINT[ \t]+([0-9]*\.?[0-9]+)[ \t]+([0-9]*\.?[0-9]+)[ \t]*$
    (?m)^[ \t]*CLAIM[ \t]+([-+0-9.eE]+)[ \t]*$

If more than one `CLAIM` line is present the LAST is authoritative.

---

## S3 — the checker (R12, R13, R14)

**One new file: `checker.py`, in this experiment directory. Not `src/`.**
R32 forbids anything else, and `git diff --stat` proves it at delivery.

**Validity (R13), in this order:**

| # | Rule | Refusal code |
|---|---|---|
| V1 | Exactly 13 `POINT` lines parse | `WRONG_COUNT` |
| V2 | Every coordinate lies in `[0, 1]` | `OUT_OF_SQUARE` |
| V3 | All 13 points are pairwise distinct | `DUPLICATE_POINT` |
| V4 | A `CLAIM` line parses | `NO_CLAIM` |

Distinctness is Heilbronn's form of R13's "no overlaps": two coincident
points make a degenerate triangle with every third point.

**Score (R14).** `score = min over all 286 triples of |cross| / 2`, where
`cross = (bx-ax)(cy-ay) - (cx-ax)(by-ay)`.

**Precision policy — declared, per A10 (R14).** A10 requires the rounding
rule and precision to be part of the POLICY, not a by-product of the
implementation. Two arithmetics exist here and the split is deliberate:

- **The offline checker is EXACT.** Coordinates are parsed as
  `fractions.Fraction` from their decimal strings, so `cross` is an exact
  rational and `score` is an exact rational. No rounding occurs anywhere in
  the computation. **Every number reported in RESULTS.md comes from this
  path**, and it is the authority for both arms.
- **Reporting rounds once, at the end**, to 12 significant figures, and the
  exact rational is retained alongside in the JSON output.
- **The in-run predicate is float64**, because `programs.py::_SAFE_NAMES`
  offers no rational type (`DR-SUB-evaluation`). It is an ADMISSION gate
  inside the run, never a source of a reported number.
- **The disagreement between the two is MEASURED, not assumed**
  (`preflight_criteria.py`, S6): over ≥ 20 000 random configurations at the
  6-decimal-place grid the maximum `|exact - float|` is recorded and must
  be below `1e-12`, which is `1e-9` of the registered floor. Coordinates
  are capped at 6 decimal places precisely so this bound holds.

**Interface.** `python checker.py --score FILE` prints the typed JSON
verdict; `python checker.py --self-test` runs S4.

---

## S4 — the checker's mutation proof (R16)

R16 names two mutations. Both are implemented, plus the rest of the
validity table, so no refusal code is asserted without a case that trips it.

| Case | Expectation |
|---|---|
| M1 a known-good construction | `valid`, and `score` equals the independently computed value |
| **M2 a planted overlap (a duplicated point)** | **FAIL — `DUPLICATE_POINT`** (R16) |
| **M3 an inflated score claim** | **FAIL — `CLAIM_INFLATED`** (R16) |
| M4 a point outside the square | FAIL — `OUT_OF_SQUARE` |
| M5 twelve points, not thirteen | FAIL — `WRONG_COUNT` |
| M6 no `CLAIM` line | FAIL — `NO_CLAIM` |
| M7 a collinear triple | `valid`, `score == 0` — a *valid* construction that is worthless, not an invalid one |
| M8 an under-claim (claims less than achieved) | `valid` — honest under-claiming is not refuted; the checker reports the achieved score |

RED/GREEN is pasted into `CHECKLIST.md`: each mutation is first shown to
FAIL against the fixed checker, and the checker is then shown to catch it.
A test that has never been seen to fail proves nothing (`docs_verify
--audit` discipline).

---

## S5 — the in-run demarcation battery (R15)

R15: the candidate's commitment IS its claimed score, checked by program —
demonstrative criticism, **no judge anywhere**. Three `Commitment`s with
`predicate:` evals, carried in the run manifest's problem criteria:

| id | What it decides |
|---|---|
| `frontier-wellformed@v1` | exactly 13 distinct `POINT` lines, all inside the square |
| `frontier-claim-honest@v1` | the achieved minimum triangle area is **not less than** the `CLAIM` — i.e. the claim is not inflated |
| `frontier-above-floor@v1` | the achieved minimum triangle area is **≥ 0.005** |

**The registered floor is 0.005**, and the number is chosen from the S1
probe, not by feel: it is 1.77x the best of 2000 random draws (0.002824) and
22.0x their median (0.000227), so luck cannot reach it; and it is ~15% of the best-known
value, so a competent construction clears it easily (the plain circle
scores 0.0133, i.e. 2.7x the floor). It discharges R20's "checker-backed
refutation of ... underperforming claims".

**Sandbox constraints these expressions must respect** (`DR-SUB-evaluation`,
carried into `REQUEST.md` §C.2): no underscore-prefixed name or attribute,
no `**`, and only `len any all min max abs sum str int float sorted re json`
plus `content` and `codec`. `range` and `enumerate` do NOT exist. The triple
loop is therefore written over a `sorted(set(...))` list and orders its
triples by **tuple comparison** (`if t < u < v`), which on a sorted list of
distinct tuples is exactly index order — no `range` required.

**No judge (R15).** `JUDGE_SEATS_ENABLED: false` and
`ARGUMENTATIVE_AUTHORITY: observe_only` in ARM H's config; `rubric_policy`
is `forbid` at compile. Status change comes only from the engaged criticism
engine driving these demonstrative predicates. This also honours the
operator's standing caution that judge seats "prosecute without any
discernable discrimination" (CLAUDE.md design laws).

---

## S6 — the criteria preflight (forced by the map, R16 by extension)

`DR-SEAM-evaluation-x-ontology` Traps: **a malformed `predicate:` is a
REFUTATION, not an error** — `evaluate` catches every exception and returns
`fail`, so one typo would silently fail every artifact in the run with full
confidence. That failure mode is invisible in the record and would look
like "the models could not do it".

`preflight_criteria.py` therefore runs BEFORE qualify and must exit 0:

1. Each expression passes `programs._validate_predicate`.
2. Each is evaluated through `programs.evaluate` against planted artifacts
   and must return the registered verdict — S4's mutation table again, this
   time through the *harness's own* evaluator rather than the script.
3. The float-vs-exact agreement bound of S3 is measured and asserted.
4. **Discrimination:** the battery must not pass on prose that contains no
   construction, and must not pass on a random configuration.

---

## S7 — ARM H (R20)

Solo run, everything on except judges (S5), over
`TextRunApplicationService` by the one run path.

| Field | Value | Why |
|---|---|---|
| model | `glm-5.2`, all 11 canonical roles | R20 "solo run"; the profile with the most live evidence here |
| cycles | **24** | R20 "cycles sized deep — the imagination is in iteration"; double P-R1's 12 |
| token budget | 3 000 000 | matches P-R1's registered cap; R19 |
| dossier | EMPTY | a construction problem admits no external evidence; also sidesteps parked P1 (the soak's blind spot is only for non-empty dossiers) |
| `rubric_policy` | `forbid` | R15, no judge |
| simulation | ON, with the frozen local toolchain | "everything on" |
| research backend | `agent` | "everything on" |

Files: `run-config.yaml`, `build_manifest_pc1.py`, `pc1_run.sh`,
`snapshot_loop.sh` (R28).

The question, frozen byte-for-byte in the builder (R17, R18) — one byte of
drift mints a different run id:

> Construct a configuration of 13 points in the unit square achieving the
> largest minimum triangle area you can; every candidate must state its
> coordinates and claimed score, and survives only if the checker confirms
> it. Score = the smallest area among all 286 triangles formed by triples
> of your 13 points; every point must lie in [0,1]x[0,1] and all 13 points
> must be distinct. State the construction in exactly this form, one point
> per line: a line "POINT x y" for each of the 13 points, with x and y
> written as decimals with at most 6 decimal places, then a final line
> "CLAIM v" giving your claimed minimum triangle area as a decimal. A claim
> the checker cannot confirm is refuted.

The first sentence is R18's template verbatim with `N` and `<objects>`
instantiated. The remainder states the scoring rule and S2's wire format,
without which R15 is not mechanisable. **Assumption A-S7**, recorded because
A3 gave the template and not the format.

---

## S8 — ARM S, the sampling baseline (R21)

`arm_s.py`, a plain script in this directory. **No harness machinery** — it
imports `checker.py` and an HTTP client, nothing from `deepreason`.

- Same model (`glm-5.2`), same endpoint, same `max_tokens`, same
  `reasoning: none`.
- **Blind**: every sample is an independent one-shot request carrying the
  same prompt. No sample sees any other sample, any score, or any history.
- The prompt is ARM H's question text **verbatim** — the same bytes, so the
  arms differ in machinery and not in what was asked.
- Every reply is scored by `checker.py`; the best VALID score is kept.
- Every raw reply is preserved to `arm_s/samples/NNNN.txt`, and a
  `arm_s/results.jsonl` line per sample records tokens, verdict, score.

---

## S9 — matched budget (R19)

Matching is on **measured actual spend**, which is the form Q4's methodology
uses and the only form that cannot be gamed by an arm that under-spends its
cap.

1. ARM H runs first. Its total tokens (prompt + completion, as counted in
   the typed record) is `T_H`.
2. ARM S then samples until its cumulative provider-counted tokens would
   exceed `T_H`; the sample that would cross the line is not issued.
3. Both arms additionally carry the same registered cap, 3 000 000.
4. RESULTS.md quotes `T_H` and `T_S` side by side. If `T_S < 0.95 * T_H`
   the comparison is reported as UNMATCHED and the margin is not claimed.

Registered before launch, per R19.

---

## S10 — milestones (R24) and the prediction (R22, R23)

**Registered prediction (R22), stated before launch and not hedged
afterwards:** `docs/RESEARCH_FINDINGS_Q1Q10_2026-08-22.md` Q4 records zero
of 36 comparisons beating repeated sampling at equal cost, ten significantly
worse, with self-assessing methods below baseline in all 18 of theirs. **The
honest prior is therefore that ARM S may win.** If it does, that is the
boundary condition measured on our own machine and it is recorded as a real
result, not a failure. Q4's own scope limit is what makes this instance
worth running at all: majority voting does not exist for open-ended
construction, so the strongest competitor to criticism is unavailable —
here "best-of-N by an exact checker" replaces it, which is a *stronger*
baseline than counting, not a weaker one.

**M1 — best valid score per arm.** Both arms report their best
checker-confirmed score. REQUIRED: ARM H produces at least one valid
construction (else the run says nothing about either hypothesis).

**M2 — checker-refuted claims.** The count of candidates whose claim the
battery refuted: invalid constructions, inflated claims, and below-floor
achievements, counted separately. This is the harness's criticism doing
countable work (R24b). REQUIRED: ≥ 1, else no criticism occurred.

**M3 — transferable construction PATTERN.** Any pattern named by a
surviving conjecture that recurs across candidates. **Reported, not
scored** (R24c) — it is the imagination measure and it has no threshold.

**The margin (R23).** The harness claims value ONLY if
`best_H > best_S`, sustained on the one pre-authorized repeat (R25).
`best_H == best_S` is not a margin. One repeat only; the arm comparison is
quoted only with both runs' spread stated (R25).

**Run identity for the repeat (R25, `DR-CON-run-identity`).** Run ids are
deterministic, so the repeat cannot reuse the same question and config in
the same home. It uses a separate `DEEPREASON_HOME` and a distinct root
path; the question bytes stay identical, which is the point of a repeat.

---

## S11 — the soak case (R26)

ARM H is a new config shape, so `scripts/cycle_soak.py`'s `CASES` table
gains one entry, **in the same commit**, and the soak is run to exit 0
before the key is requested (R27):

    "pc1": SoakCase(
        id="pc1",
        config_path=<this dir>/run-config.yaml,
        builder="build_manifest_pc1",
        builder_dir=<this dir>,
        attached_evidence=False,
        delegates_to_builder=True,
        default_cycles=24,
        default_token_budget=3_000_000,
    )

`delegates_to_builder=True` because the builder owns root construction; the
soak's default path would bind a different manifest shape and report green
on a configuration the launch never uses.

This is the ONLY change outside this experiment directory (R32).

---

## S12 — PROGRAM.md v2 (R5, R6, R7, R8)

`experiments/2026-08-25-poietics-program/PROGRAM.md` is amended in place:

- A **v2 header** recording that the program was redirected on 2026-08-25.
- **P-R2 and P-R3 marked CANCELLED**, with the operator's verbatim words
  (A1) as the cancelling authority (R6). Their registered text is NOT
  deleted — a registered question that is cancelled stays legible, or the
  record loses the fact that it was ever registered. This follows
  REQUEST.md's own never-delete rule.
- The program renamed to the **CONSTRUCTIVE FRONTIER series** (R7).
- The **problem class registered** (R8): geometric construction on small
  open instances — circle packing (max min radius, N circles in the unit
  square) and Heilbronn (max min triangle area, N points).
- P-C1 registered, pointing at this tranche's `PREREG.md`.

---

## S13 — acceptance checks

| # | Requirement | Check |
|---|---|---|
| C1 | R5, R6, R7, R8 | `PROGRAM.md` carries the v2 header, P-R2/P-R3 CANCELLED with A1 quoted, the series renamed, the problem class registered |
| C2 | R9, R10 | `INSTANCE_CHOICE.md` exists with the probe outputs; SPEC S1 reasons the choice |
| C3 | R12, R32 | `git diff --stat` shows exactly one changed file outside this directory: `scripts/cycle_soak.py` |
| C4 | R13, R14, R16 | `python checker.py --self-test` exits 0; RED/GREEN for M2 and M3 pasted in CHECKLIST.md |
| C5 | R15, and the map trap | `python preflight_criteria.py` exits 0 |
| C6 | R17, R18, R19 | `PREREG.md` committed and pushed BEFORE any provider call; question matches R18's template |
| C7 | R26, R27 | `python -u scripts/cycle_soak.py --case pc1` exits 0, pasted, before the key is requested |
| C8 | R20, R21, R28 | ARM H reaches a typed terminal with a clean `verify_root`; ARM S produces `results.jsonl` |
| C9 | R4, R24, R30, R31 | `RESULTS.md` quotes only typed outcomes and checker outputs, gives both best scores, the margin, the refutation count, the residue, and uses conjecture-only survivor figures |
| C10 | R2, R22, R23 | The margin is stated with both arms' actual token spend; no value claimed without `best_H > best_S` |

---

## S14 — budget and stop conditions

Estimated diff: ~7 new files in this directory, ~1300 lines, plus one
`SoakCase` entry (≈ 12 lines) in `scripts/cycle_soak.py`, plus the
`PROGRAM.md` amendment. Anything beyond that is a stop.

Standing stops (`dr-change-orchestrator`): a step failing twice the same
way; any contact with a frozen surface; a requirement contradicting the
record. Tranche-specific stop: **if the criteria preflight (S6) cannot be
made to pass, STOP and report** — launching over a battery that fails every
artifact would burn the budget and produce a record that means nothing.
