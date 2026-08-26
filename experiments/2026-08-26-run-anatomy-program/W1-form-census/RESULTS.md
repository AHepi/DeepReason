# RESULTS — W1, the form-filling census

Dated honest-ledger segments. Every number below is produced by a committed
instrument in this directory and re-derivable by running it:

    python3 ../inventory.py        # 54 roots -> ROOT_INVENTORY.json
    python3 census.py              # one row per provider attempt
    python3 aggregate.py           # CENSUS_AGGREGATE.json, the two tables
    python3 pc1_headline.py        # PC1_HEADLINE.json
    python3 coercion_probe.py      # COERCION_PROBE.json
    python3 exemplars.py           # EXEMPLARS.md

"Accepted does not mean true" — and here it does not even mean answered: the
largest single finding is that the forms accept content they cannot check.

---

## 2026-08-26 — the census

**54 committed run roots. 3 155 provider attempts. 2 743 valid on arrival
(86.9%).** Nine models, twelve contracts, seven roles.

Join health, reported rather than assumed, because a census is only as good
as its keys: 0 attempts failed to resolve to their attempt object, and 0 key
collisions, across all 54 roots. Cycle attribution is exact on 48 roots and
unavailable on 6 — those six completed no cycle, so per-cycle numbers for
them are absent, not estimated.

### 1. Form size moves validity far more than anything else measured here

| contract | attempts | valid on arrival |
|---|---|---|
| `defender.direct.v1` (1 field) | 122 | **100%** |
| `variator.direct.v1` (1 field) | 30 | **100%** |
| `judgeruling.direct.v1` (2 fields) | 342 | **100%** |
| `critic.atomic-target.v1` (one target) | 34 | **100%** |
| `conjecturer.atomic-candidate.v1` (one candidate) | 373 | 94.9% |
| `batch-critic.v2` (a batch of targets) | 1 384 | 92.6% |
| `conjecturer.turn.v6` (a whole turn) | 816 | **66.3%** |

The controlled comparison is not that table — it is the pair of rows that
share a model, a seat instance, a route and a problem. When
`conjecturer.turn.v6` exhausts its repair grant, the controller decomposes it
into `conjecturer.atomic-candidate.v1`: same everything, one candidate per
call instead of a whole turn. Held to **glm-5.2**, which is 75% of the
corpus:

| | attempts | valid |
|---|---|---|
| glm-5.2 on `conjecturer.turn.v6` | 659 | **61.9%** |
| glm-5.2 on `conjecturer.atomic-candidate.v1` | 339 | **96.8%** |

35 points, on a thousand calls, with the smaller form running on the HARDER
sample by construction — it exists only because the composite one already
failed. That makes 35 points a lower bound, not a selection effect.

**And one model reverses it.** `deepseek-v4-flash:0731` goes the other way:
84.6% on the composite form (52 attempts) against 63.6% on the atomic one
(22). On those sample sizes that is not evidence against the effect, but it
is evidence against calling the effect universal, and it is recorded here
rather than left out of the table.

**The by-model table must NOT be read as a model ranking.** Models did not
run the same forms. `qwen3.5:397b`'s 100% is 171 calls, every one of them the
two-field judge form; `glm-5.2`'s 85% is 2 378 calls across seven contracts
including the hardest one. Held to the same hard form, the models do differ —
glm-5.2 61.9% (659 attempts), deepseek-v4-flash 84.6% (52), gemma4:31b 88.2%
(34), deepseek-v4-pro:0813 96.8% (31) — but only the first has a sample worth
quoting, so the honest statement is that form size is measured and model
effect is suggested.

This is an in-house replication of the coercion research's schema-weight
dose-response (`docs/RESEARCH_STRUCTURED_OUTPUT_COERCION_2026-08-22.md`,
recommendation 6), measured on our own seats rather than cited.

### 2. What fails is almost always a REFERENCE, not a judgment

The record wrote 1 434 diagnostics in total, of which 1 178 name a specific
field. The five commonest of those are all fields whose job is to NAME
something that already exists:

| count | contract | field | class |
|---|---|---|---|
| 244 | `conjecturer.turn.v6` | `/candidates/*/evidence_refs/*/block` | `string_pattern_mismatch` |
| 230 | `conjecturer.turn.v6` | `/scratch_proposal/unresolved_questions/*/related_refs` | `value_error` |
| 129 | `batch-critic.v2` | `/cases/*/premise_evidence/*/block` | `string_pattern_mismatch` |
| 70 | `conjecturer.turn.v6` | `/scratch_proposal/links/*/to_ref` | `string_pattern_mismatch` |
| 64 | `conjecturer.turn.v6` | `/candidates/*/optional_refs/*` | `V6_WIRE_REFERENCE_INVALID` |

That is 737 of the 1 178 field-attributed diagnostics — **62.6% of every
failure the record can pin on a field is a handle the model made up** (51.4%
of all 1 434 diagnostics, counting the object-wide ones that name no field).
The models are not failing to reason inside the form; they are failing to
point at things.

### 3. CFR: told that omission was legal, the seat invented a value 255 times out of 257

The record does not merely reject an invented handle. It writes, in the
diagnostic the seat then receives:

> Use only a listed legal handle for this reference field. Omission is legal:
> a remove operation at this path, or a replace that drops the offending
> entry, is a valid repair; **never invent a handle to fill an optional
> reference.**

257 diagnostics carry `omission_or_unknown_legal: true` — absence was a legal
answer and the record said so. In **255** of them the seat supplied a handle
the record classifies as `unknown`: a value it invented for a field it had
just been told it could leave out.

**CFR = 99.2%.** This is PhantomFill's Coerced Fabrication Rate made
code-scorable on our own record, with no judge involved, because absence is
the ground truth by construction. The coercion research
(`docs/RESEARCH_STRUCTURED_OUTPUT_COERCION_2026-08-22.md`) parked the
salted-probe design as expensive; this needed no probe, because the
harness had already been running the experiment for a month and recording
the answer.

Escape utilization, measured on the next attempt in the same repair ladder:
of 120 ladders where an escape was offered, **7 took it** (a `remove`
operation), 78 repaired by supplying a different value, and 35 stayed
invalid. **EUR ≈ 5.8%.**

The one enum in the corpus that carries an escape value behaves differently:
`claim_class` on the bridge ledger contracts offers `unknown`, and the models
use it — 6 of 85 on `bridge.ledger.v3`, 10 of 55 on `bridge.ledger-batch.v1`.
Where the escape exists in the vocabulary it gets taken; where it exists only
in the instruction text it does not.

### 4. The judge form cannot say "I don't know", and never tried to

`JudgeRuling` declares `verdict` as `enum: [fail, pass]` and
`decisive_point` with `min_length: 1`. **342 rulings, 194 fail, 148 pass,
zero abstentions, because there is no value for one.** Not one decisive_point
contains a phrase in which the judge declines. All 342 arrived valid on the
first attempt.

Read against the operator's standing position on judges — that they
"prosecute without any discernable discrimination" — this census cannot say
whether the verdicts were right. It can say the form gave no way to record
an honest inability, and that in 342 opportunities nobody found a way around
it.

The same shape appears on the critic. `batch-critic.v2` requires a boolean
`attack` per target with no third value, and lets `case` default to the empty
string. **15 of 1 453 asserted attacks carry no case text at all** — the form
records an attack that was never argued.

**A correction to my own first measurement, recorded rather than quietly
fixed:** the first version of this hedge test used a loose marker list and
reported that 7.4% of asserted attacks hedged in their prose. That number was
wrong. A critic writing "the target provides no evidence for X" is making an
attack, not declining to make one, and the list was counting the substance of
criticisms as refusals. The strict measure — phrases in which the SPEAKER
declines, word-boundary matched — gives 1 case out of 1 453, and it is quoted
in full in `EXEMPLARS.md` because even that one is arguable. The
false-positive exemplars are committed in `COERCION_PROBE.json` rather than
deleted.

### 5. Repair costs a fifth of everything, and a retry is close to a coin flip

**224 repair ladders consume 680 of 3 155 attempts — 21.6% of all provider
spend in the entire committed record.** Ladder lengths: 104 of length 2, 47
of 3, 14 of 4, 54 of 5.

| workflow attempt index | attempts | valid |
|---|---|---|
| 0 (first ask) | 2 699 | **91.7%** |
| 1 | 219 | 58.5% |
| 2 | 115 | 60.9% |
| 3 | 68 | 58.8% |
| 4 | 54 | 55.6% |

A first ask succeeds nine times in ten. Every subsequent ask on the same work
succeeds about six times in ten and does not improve with repetition. The
grant ceiling is reached in 97 ladders.

**What the diagnostic asked vs what came back: the repairs are ON TARGET.**
Of 456 patch-mode repair attempts, 359 patched only pointers inside their own
authorized set, 12 went outside it, 19 returned no pointer, and 66 were
whole-object reissues with no pointers by design. The seats are answering the
question they were asked; they are simply not answering it correctly.

### 6. The E42 lossless-spelling class after its fix: down 94%, and the survivors are characterisable

`experiments/2026-08-22-fix-repair-patch-transport` (commit `97a964583`,
2026-08-22T16:09:24Z) absorbs four container names, three harness echoes and
the `pointer`→`path` rename. Cutting the corpus at that COMMIT TIMESTAMP —
not at the day, which puts the two runs that motivated the fix on the wrong
side of it:

- **before: 79 attempts** lost a repair grant to a spelling
  (`/patch` 29, `/pointer` 26, `/baseline_sha256` 13, `/contract` 4,
  `/operations` 4, `/patches` 2, `/repair_patch_v1` 1)
- **after: 5 attempts**, across 2 roots
  (`/contract` 3, `/patch` 1, `/repair_patch_v1` 1)

All five are quoted whole in `EXEMPLARS.md`, and each falls outside the fix's
closed key set for a nameable reason:

1. `{"repair_patch_v1": {...}}` — a container name the fix's closed set does
   not list (it lists `repair.patch.v1`, not the underscored spelling).
2. `{"contract": "repair.patch.v1", …}` ×3 — the echo drop is exact-equality
   only, and the model wrote the SCHEMA name where the CONTRACT name belongs,
   so the value differs from what the harness sent and the fix deliberately
   leaves it. The fix's own design document predicted this case.
3. `{"patch": [...], "version": "repair.patch.v1"}` — `patch` IS in the
   closed set, but the unwrap applies only to a single-key dict, and this one
   has two.

The class is not eliminated. It is reduced 94% and reduced to three named
shapes, which is a much better place to stand than where E42 found it.

### 7. Almost half of accepted responses are wrapped in a markdown fence

Of 2 743 valid arrivals: 1 484 bare JSON, **1 254 fenced in ```json (45.7%)**,
3 wrapped in prose around a fence, 2 wrapped in prose around bare JSON. Every
one of these seats is configured `output_mode: json_object`. The harness
tolerates the fence, so it costs nothing today; it is recorded because it
means the models are not doing what the mode asks, and a stricter reader
would reject 46% of currently-good traffic.

### 8. The truncation flag never fires, and the record disagrees with it

`attempt_trace[].truncated` is **false on all 3 155 attempts**. The record's
own diagnostics say otherwise **52 times**: "your output hit the length limit
and was CUT OFF mid-JSON". Separately, 11 attempts (all glm-5.2) record
`natural_stop: false`.

So truncation is detected semantically, after the fact, by noticing the JSON
does not close — and the transport-level flag that exists to report it is
inert. Parked as a finding, not diagnosed here.


### 9. The two priority roots, read individually

The census covers all 54 roots (`PER_ROOT.md`). The two the W1 prompt names
as priority read as follows.

**P-C1 ARM H — `experiments/2026-08-25-change-constructive-frontier/run`,
run `1950b3d0ee228113`, 292 attempts, 256 valid (87.7%).** One model
(glm-5.2), two roles. It is the only root in the corpus that died of
`V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY` — "route seat has terminally
exhausted its smallest authorized contract" — and the census shows the whole
descent: `conjecturer.turn.v6` 44/63 valid, decomposed seven times into
`conjecturer.atomic-candidate.v1` (38/41) — with three further
`batch-critic.v2` → `critic.atomic-target.v1` decompositions on the critic
seat — and then the atomic contract itself exhausted. The terminal object records the ladder verbatim:
`attempted_contract_ids: [turn.v6, turn.v6, atomic-candidate.v1,
atomic-candidate.v1]`. Its dominant wire failures are not field failures at
all — 18 `WIRE_TRAILING_CONTENT`, 16 `TRUNCATED_MID_JSON`, 8
`WIRE_NO_COMPLETE_JSON`: 42 of its 77 diagnostics are the JSON not arriving
whole. Note also that `run-status.json` reports `token_spend: 0` for this
root because it failed operationally, while the log's own attempts sum to
702 789 — the figure that tranche measured and matched ARM S against.

**P-R1 — `experiments/2026-08-25-poietics-program/run`, run
`1b31f0065687bd24`, 163 attempts, 146 valid (89.6%), completed on
`budget_exhausted` at cycle 12.** Two models on one route family (kimi-k3
126 attempts, deepseek-v4-pro:0813 37) and the only priority root with
`attached_evidence` enabled. Its failure profile is almost entirely ONE
class: **51 of its 64 diagnostics are `string_pattern_mismatch`**, and they
are evidence-block handles failing `^[0-9a-f]{12,64}$`. This is the
reference-fabrication finding of §2 concentrated in a single root — the run
that was given a dossier is the run that spent its errors inventing citations
into it. 18 repair attempts, 16 patch-mode, **all 16 on target**; 4
decompositions to atomic contracts; 3 works abandoned with
`context_capability_not_granted`. Zero coerced-fabrication diagnostics fire
here, because this root's failures are pattern mismatches rather than
handle-kind rejections — the CFR measure of §3 is silent on it, which is
exactly the residue item 2 below.

### 10. Seats, not roles

Keyed by seat INSTANCE as the signal-registry contract requires, the corpus
has 8 seats across 7 roles, and one role runs two seats:

| seat | attempts | valid |
|---|---|---|
| `argumentative_critic#seat0` | 1 424 | 92.8% |
| `conjecturer#seat0` | 1 189 | 75.3% |
| `judge#seat0` | 171 | 100% |
| `judge#seat1` | 171 | 100% |
| `defender#seat0` | 122 | 100% |
| `summarizer#seat0` | 31 | 64.5% |
| `variator#seat0` | 30 | 100% |
| `thesis#seat0` | 17 | 76.5% |

The two judge seats are split exactly 171/171 and behave identically at the
form level. `summarizer#seat0` is the worst seat in the corpus at 64.5%, on
only 31 attempts — flagged as a small sample, not a finding.

---

## 2026-08-26 — the P-C1 headline, attributed

**ARM H 15 valid of 132 (11.4%). ARM S 23 of 53 (43.4%).** Both reproduced
from that tranche's own committed scoring artifacts, so this cannot drift
from the RESULTS.md it explains.

### The 89% is one field and one geometric fact

Every one of ARM H's invalid candidates failed in the SAME field: the single
free string carrying the construction. **Not one failed a schema constraint,
a type, an enum, or a pointer.** The form was filled correctly and the
content it carried was degenerate — which is the one failure a wire contract
is structurally unable to catch.

| cause | count | what the field did |
|---|---|---|
| `CLAIM_INFLATED` | 114 | the `CLAIM v` line claims an area the construction's own points do not have |
| `WRONG_COUNT` | 3 | 12 `POINT` lines where the instance requires 13 |
| valid but below the registered 0.005 floor | 15 | obeyed the rules and lost |

And `CLAIM_INFLATED` is not an arithmetic overclaim. **All 114 had a true
minimum triangle area of exactly ZERO.** ARM H never once produced a
non-degenerate construction and then overstated it; when its geometry was
sound, its arithmetic was too.

### The mechanism, read from the raw blobs

`arm_h_scores.json` stores construction text only for candidates the checker
CONFIRMED (`score_run.py:157`), so the 117 refuted constructions — the whole
subject of the headline — are not in it. Read instead from the run root's raw
provider blobs and re-scored with that tranche's own committed `checker.py`:

| | ARM H (133 constructions in blobs) | ARM S (52 committed samples) |
|---|---|---|
| minimum area exactly zero | **129 (97.0%)** | **14 (26.9%)** |
| …with three or more points sharing an x or y coordinate | **126** | 10 |
| …collinear only obliquely | 3 | 4 |

**126 of ARM H's 133 constructions place three or more points on a shared
x or y coordinate.** Three points on a line have zero area, so the minimum
over all 286 triples is zero before any of the rest of the construction
matters. That is the named field-level cause of the 89%.

The signature carries a falsifier: an axis-aligned triple with a NONZERO
minimum is impossible, so a nonzero count there would mean the signature is
being read wrong and every number in this table must be discarded. It fired
on the first pass, on the three `WRONG_COUNT` candidates the checker never
scores at all; the classification was corrected and the falsifier is now
empty.

It is not a precision problem. ARM H wrote 6-decimal coordinates on 42 of
133 constructions and 41 of those still scored zero; ARM S wrote 6-decimal
coordinates on 36 of 52 and only 4 scored zero. **At the same written
precision, ARM H is ten times more likely to be collinear.** The difference
is which arrangement was chosen — grids, midpoints, symmetric shells — not
how many digits were written down.

This corroborates that tranche's own M3 vocabulary finding from the opposite
direction. It recorded that ARM H named the trap ("avoid-collinearity" in all
15 valid candidates) and never named a search. The census shows what that
looked like in the other 117: the run said "avoid collinearity" and then
placed points on a lattice, 126 times.

---

## Residue — what this census does NOT establish

Stated because a measurement tranche that reports only what it found is
reporting half of what it knows.

1. **Enum vocabularies are OBSERVED, not DECLARED.** The enum-like fields in
   `CENSUS_AGGREGATE.json` are inferred from values models wrote. A field
   whose schema offers an escape that no model ever chose is indistinguishable
   here from a field that offers none. The two enums quoted against their
   contracts in §3–4 (`claim_class`, `verdict`) are exceptions; the rest are
   candidates.
2. **CFR is measured only where the record ANNOUNCED the escape.** 257
   diagnostics carry `omission_or_unknown_legal`. Forms that coerce a
   fabrication without ever saying omission was legal produce no such
   diagnostic and are invisible to this measure. The true fabrication rate is
   at least 99.2% of the announced cases and unknown elsewhere.
3. **"Valid on arrival" is a wire-and-schema verdict, not a truth verdict.**
   §5's 91.7% first-ask validity and the P-C1 headline are the same fact seen
   twice: a form can be perfectly filled and completely wrong. Nothing here
   measures whether a criticism was correct, a judge fair, or a conjecture
   good — those are D4, D5 and D8, and they are not W1's.
4. **The single arguable refusal (§4) is reported as one case and quoted, not
   counted.** A word list cannot settle whether "I cannot" is a critic
   declining or a critic criticising, and this census does not pretend it can.
5. **Cycle attribution rests on a token-sum join**, exact on 48 roots and
   absent on 6. It reconciles to the byte on P-C1 (702 789 cumulative log
   tokens against that tranche's independently measured 702 789), which is
   evidence the join is sound but not proof it is sound everywhere.
6. **The model comparison is confounded and is reported as such.** Models
   did not run the same contracts, so the by-model validity table is a
   statement about workload mix, not capability. The one within-form
   comparison with real power is glm-5.2 on `conjecturer.turn.v6`; every
   other model has between 10 and 52 attempts on it. A window that wants a
   model ranking needs runs designed for one.
7. **Blob-level and artifact-level construction counts differ by one** in
   P-C1 (133 vs 132). The artifact-level count remains authoritative for the
   headline; the extra blob construction is a restatement the scorer
   deduplicated differently. Not chased.
8. **This census reproduced E42's own mistake before avoiding it.** The first
   patch-pointer extractor read only the canonical `operations`/`path`
   spelling and scored 398 repairs off-target — the identical false finding
   `docs/ERRATA.md` E42 records. Read against the eight container names the
   record actually shows, the answer inverts to 359 on-target and 12 off. The
   instrument then independently reproduces E42's committed correction on its
   own subject root (13 repair turns, 0 off-target). The lesson generalises
   past E42: it is not enough to join on the frozen key; you must also read
   the model's answer in every spelling the record contains, or a convergent
   answer scores as a wrong one.
