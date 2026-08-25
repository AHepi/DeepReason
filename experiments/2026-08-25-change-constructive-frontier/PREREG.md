# PREREG — P-C1, the first constructive-frontier run

**Frozen before any provider call** (REQUEST.md R17). This file is
committed and pushed before the operator's key is requested; the git log is
the proof, and `driver.log`'s first entry postdates the push.

Nothing in this document may be edited after launch. If a design turns out
to be wrong, that is recorded in RESULTS.md as a finding, not repaired here.

---

## §1 — The instance and why it was chosen

**Heilbronn, N = 13.** Maximise the minimum area over all 286 triangles
formed by triples of 13 points in the closed unit square.

Chosen by measurement (`instance_probe.py`, output in
`instance_probe.out`), reasoned in `SPEC.md` §S1. The four facts that
decided it:

| Fact | Measurement |
|---|---|
| The checker is simplest | one cross product, no square root, exact in the rationals end to end; packing's validity is coupled to its own claimed radius |
| The band's alternative is degenerate | circle packing at N=16 is the 4x4 grid at r = 1/8 exactly — an instance that measures recall |
| The obvious answers score ZERO | symmetric constructions contain collinear triples; ring+centre 0.000000, corners+edges 0.000000, jittered grid 0.000163, against a plain circle at 0.013308 |
| There is dynamic range | random 13-point draws: median 0.000227, best-of-2000 0.002824; best-known ≈ 0.033 |

**N = 13 is the band's smallest**, which is where the random baseline is
strongest (probe medians fall monotonically 0.000227 → 0.000112 across
13→16). That makes ARM S strongest and the harness's claim under §5 harder
to earn, which is the honest direction to err in.

---

## §2 — The question, frozen

Byte-frozen in `question.py`, shared by both arms so neither can hold a
divergent copy. `question_sha256 = 64b724c4118320989925d111501a8e41cd4518d9b631bb81a6ae048d3cfb5c7e`.

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

The first sentence is REQUEST.md R18's registered template with `N` and
`<objects>` instantiated. The remainder states the scoring rule and the
wire format, without which R15 is not mechanisable.

---

## §3 — The two arms, registered before launch (R19)

### ARM H — the harness

| Field | Value |
|---|---|
| model | `glm-5.2`, solo, all 11 canonical roles |
| cycles | **24** (R20's "cycles sized deep"; double P-R1's 12) |
| token budget | 3 000 000 (cap) |
| judges | **NONE.** `JUDGE_SEATS_ENABLED: false`, `rubric_policy: forbid` |
| criticism | engaged, `ENGAGED_CRITICISM_AUTHORITY: defended_trial`, legacy off |
| dossier | EMPTY; attached evidence OFF |
| everything else | on — school seats, adjudication authority, simulation with the frozen local toolchain, research backend `agent` |

Refutation is DEMONSTRATIVE: the three `predicate:` criteria in
`criteria.py` decide every candidate by computation. No seat rules on a
number, anywhere, at any point.

### ARM S — the sampling baseline

| Field | Value |
|---|---|
| model | `glm-5.2` — the same model |
| prompt | §2's bytes, verbatim, via the shared `question.py` |
| temperature | **1.0, set explicitly** |
| max_tokens | 32768 — the same seat cap as ARM H |
| memory | NONE. Each sample sees no other sample, no score, no history |
| scoring | the same exact `checker.py`; best VALID kept |
| machinery | none — `arm_s.py` imports `checker` and the standard library, nothing from `deepreason` |

**Temperature 1.0 is registered deliberately.** A near-deterministic
sampler would return near-identical replies and make the baseline trivially
weak, which would flatter ARM H for the wrong reason. The baseline must be
allowed to explore.

---

## §4 — Matched budget (R19), registered rule

Matching is on **measured actual spend**, not on the registered cap. A cap
match would let an arm that under-spends look cheap.

1. ARM H runs first; its provider-counted total is `T_H`.
2. ARM S samples until cumulative provider-counted tokens would exceed
   `T_H`.
3. RESULTS.md quotes `T_H` and `T_S` side by side.
4. **If `T_S < 0.95 * T_H` the comparison is reported as UNMATCHED and no
   margin is claimed.**

---

## §5 — The registered prediction, and what counts as value (R22, R23)

**The honest prior is that ARM S may win.**
`docs/RESEARCH_FINDINGS_Q1Q10_2026-08-22.md` Q4 records **zero of 36
comparisons significantly better than repeated sampling at equal cost, ten
significantly worse, 30 of 36 point estimates negative**, with every
self-assessing method below the equal-cost baseline in all 18 of its
comparisons. Q4's pre-registerable form of the law:

> At matched budget, criticism loses to resampling wherever a counting
> baseline exists and the solo anchor is not already failing outright; the
> collaborative advantage appears only above a difficulty threshold where
> the anchor drops below ~70%.

**If ARM S wins, that is a real recorded result, not a failure.** It is the
boundary condition measured on our own machine, on our own harness, and it
is written up as such.

Two things make this instance a genuine test rather than a foregone one,
and both are registered now so neither can be claimed afterwards:

- Q4's scope limit says the strongest competitor to criticism — majority
  voting — does not exist for open-ended work. Here something **stronger**
  exists: an exact checker doing best-of-N. So ARM S is a harder baseline
  than the one Q4 measured, not a weaker one.
- Q4's boundary says the collaborative advantage opens where the solo
  anchor drops below ~70%. On this instance the naive anchor scores
  **exactly zero** (symmetric constructions are collinear). If Q4's
  boundary is real, this is the regime where it should show.

**The harness claims value ONLY on margin:** `best_H > best_S`, sustained
on the one pre-authorized repeat. `best_H == best_S` is NOT a margin.

---

## §6 — Milestones (R24)

| # | Milestone | Status |
|---|---|---|
| **M1** | Best valid checker-confirmed score, per arm | **REQUIRED**: ARM H must produce ≥ 1 valid construction, else the run says nothing about either hypothesis |
| **M2** | Count of checker-refuted claims, split into invalid / inflated / below-floor | **REQUIRED**: ≥ 1, else no criticism occurred |
| **M3** | Any construction PATTERN named by a surviving conjecture that transfers across candidates | **REPORTED, NOT SCORED** — the imagination measure has no threshold (R24c) |

The registered floor for "below-floor" is **0.005** — 1.77x the best of
2000 random draws and 22.0x their median, so luck cannot reach it; ~15% of
best-known, so competence clears it.

---

## §7 — The repeat, and how the comparison may be quoted (R25)

**One repeat is pre-authorized.** Run identity is deterministic, so the
repeat uses a separate `DEEPREASON_HOME` and a distinct root path
(`PC1_HOME` / `PC1_ROOT` in the ladder); the question bytes stay identical,
which is the point of a repeat.

**The arm comparison is quoted only with both runs' spread stated.** A
single-run margin is reported as a single-run margin and never as a result.

---

## §8 — What P-C1 cannot settle, registered in advance

- **It cannot tell you the best-known value was reached.** No published
  record is consulted (R11). ARM S is the comparator; any figure the
  operator later supplies is a stretch line, not a gate.
- **It cannot generalise from one instance.** One N, one problem family,
  one model. A margin here is a margin here.
- **Capability-channel use is stochastic across identical runs**
  (CLAUDE.md). One live attempt that misses a path is inconclusive for that
  path.
- **"Accepted" still does not mean "true"** — but note that on this
  instance it means something unusually strong: a candidate's acceptance is
  a computation over its own bytes, not a status conferred by a seat. What
  acceptance does NOT mean is optimal, or good, or better than what a
  different arm would find.
- **The survivor-count inflation from import-role records is a KNOWN
  ISSUE** (poietics P4, parked). Conjecture-only figures are quoted; the
  raw figure is labelled inflated wherever it appears (R31).

---

## APPENDIX — post-launch correction, 2026-08-25 19:40Z

This appendix is APPENDED, never an edit of the frozen sections above.
§1–§8 stand exactly as registered.

**What was wrong.** SPEC.md §S2 and the first `checker.py` / `criteria.py`
extracted the wire format with LINE-ANCHORED regexes (`(?m)^...$`), on the
assumption that a candidate reaches the record as plain text with real line
breaks. It does not. Every seat runs `output_mode: json_object`, so a
construction arrives inside a JSON envelope —
`{"claim":"POINT 0.5 0.5\nPOINT ..."}` — where the breaks are the two
characters backslash-n. Anchored patterns match nothing there.

**How it was found, and how bad it was.** The first live launch reached
cycle 11 before an interim scoring pass showed **0 candidates out of 1509
artifacts**. The in-run battery had been inert for the entire run: it
refuted every candidate, silently, for a reason invisible in the record.
That is the same failure family as
`DR-SEAM-evaluation-x-ontology`'s "a malformed `predicate:` is a REFUTATION,
not an error" — and my step-5 preflight did not catch it, because every
fixture I wrote was in the plain-text shape I had assumed.

**The fix, and the proof.** The anchors are dropped; the KEYWORD is the
delimiter. Measured on that run's own record: the anchored form matched
**0 of 1509** artifacts, the unanchored form **183**. A new permanent
fixture **M9** carries the JSON-envelope shape and must score identically
to M1; `checker.py --self-test` is 9/9 and `preflight_criteria.py` exits 0.

**Why this is a repair and not a result-fitted change.** The fix is
determined entirely by the record's byte SHAPE, not by any score. What I
had seen when I made it was that zero constructions were being read at all.
For completeness, the void run's post-hoc scores are recorded below and
they argue AGAINST the harness, not for it — so if the fix were motivated
by results it was motivated in the wrong direction.

**The void run is retained as evidence**, at
`void-inert-battery-run-6913328037a61ca6/`, scored in
`void-inert-battery-scores.json`. It is NOT an ARM H result and is never
quoted as one: its criticism never received the checker signal the design
requires. It is, unintentionally, a third condition — *the harness without
checker feedback* — and it is reported as such:

    183 candidates attempted, 24 valid, 159 refuted
    147 CLAIM_INFLATED, 7 WRONG_COUNT, 3 NO_CLAIM, 2 DUPLICATE_POINT
    best valid score 0.0 -- every valid construction was collinear

**What changes for the registered design: nothing.** Both arms are scored
by the same fixed checker, the question bytes are unchanged, the milestones
and the margin rule are unchanged, and ARM H relaunches from cycle 0. The
criteria are part of the run input digest, so the relaunch mints a NEW run
id; the void root keeps its own.
