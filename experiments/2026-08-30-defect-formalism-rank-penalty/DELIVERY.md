# DELIVERY — lane C, ultracode batch 2

Branch: `claude/b2-lane-C` (pushed at every phase boundary).
Tranche: `experiments/2026-08-30-defect-formalism-rank-penalty/`.
Date: 2026-08-30.

This document stands alone. Everything it claims is either pasted verbatim
below or names the file that holds the pasted output.

---

## 0. Map preflight — the ids this work was scoped from

| id | why |
|---|---|
| `DR-CON-conjecture-kinds` | owns the promise the defect violates ("must never do: weight a conjecture's rank ... on its kind") and co-owns `scheduler/scheduler.py` |
| `DR-SUB-scheduler` | owns `scheduler/`, documents `run_report` and the Pareto axis row |
| `DR-SUB-periphery` | owns `src/deepreason/capture/`, i.e. `capture/pareto.py` |
| `DR-INV-frozen-surfaces` | read before designing (map law) — no cone path appears in it |
| `DR-CON-scheduler-ranking` | read to confirm it owns `_select_problem` only, NOT `run_report`, so it does not move for this change |

Undocumented seam noted, not written: `CON-conjecture-kinds x scheduler-ranking`
(named at `docs/map/CON-conjecture-kinds.md:6`).

---

## 1. What was asked, and what shipped

| # | Asked | Shipped |
|---|---|---|
| 1 | Fresh re-measurement at HEAD; confirm or refute the brief's live-footprint numbers | Done. Both instruments run and pasted below. The numbers are **CONFIRMED**, exactly. |
| 2 | Law-based narrowing: test each of the three priced roads against R-g; show the argument | Done. `road_law_probe.py`, four probes derived from quoted clauses, table pasted below. Only road (a) passes all four. |
| 3 | The mutation-proven equal-standing test, landed honestly, not red in the gate | Done. Standalone script `proof_equal_standing.py` (choice justified in §5), mutation-proven in both directions. |
| 4 | The recommended road built and proven, NOT integrated, its own commit | Done. Commit `fe6b29ed2`, whose subject line begins "BUILT AND PARKED, NOT INTEGRATED". |
| 5 | Site (b) = P3: report it, carry its question verbatim, do NOT implement | Done. `PARKED.md` L2. Zero writes to `config.py` or `informal/trial.py` — see the cone in §7. |
| 6 | Verify and report the cone; re-verify no frozen surface is touched | Done, and one surprise resolved with evidence — see §7. |

**The decision itself is NOT shipped, and must not be.** See `STOP.md`.

---

## 2. What is parked and why — read this before reading anything else

The batch asked for both unlawful-penalty sites fixed in one tranche. The brief
the batch designated as the authority says otherwise, in its own words, and this
lane obeyed the brief:

- **Site (a) = P2** (the coverage Pareto axis) opens
  `experiments/2026-08-27-audit-formalism-optional/PARKED.md:73` with
  "OPERATOR DECISION NEEDED FIRST, then the change:", prices three roads at
  `:78-90`, and routes itself to `dr-change-orchestrator` rather than a defect
  family "-- the operator decides what coverage should mean" (`:70-71`). That is
  a real design fork on a scored axis. **This lane did not choose it.** It
  measured it, narrowed it by law, built the road it recommends, and PARKED the
  choice in `STOP.md`, which is answerable with one word.
- **Site (b) = P3** (prose criticism) is filed by its own heading as "an
  operator decision, not a defect" (`PARKED.md:117`) and its brief says "Route
  through dr-ask-the-right-question FIRST" and "THE QUESTION FOR THE OPERATOR
  (do not design before it is answered)" (`:132-136`). **Not implemented, not
  designed.** Carried forward verbatim in this tranche's `PARKED.md` L2.

A note on the brief's own arithmetic, so a reader does not go looking for a
second fix: `SITES.md:15` counts "2" UNLAWFUL-PENALTY rows, but rows `:25` and
`:26` are two adjacent LINES of the same F1 finding (`scheduler.py:221` collects
the evaluable commitments; `:222` is the predicate feeding the `else 0.0`), and
`PARKED.md:61` itself calls P2 "the audit's one UNLAWFUL-PENALTY". There is one
unlawful-penalty code site in the audit, not two.

---

## 3. Measurement 1 — the penalty is still live at HEAD (verbatim)

Command: `python experiments/2026-08-27-audit-formalism-optional/repro_coverage_rank.py`
run against this branch's tree at commit `152c7e204` (before any source change).
Saved at `proof/repro_head_2026-08-30.txt`.

```
PARETO_AXES = ['hv', 'reach', 'coverage']  (frontier maximises each)
  formal survivor: {'hv': 0.0, 'reach': 0.0, 'coverage': 1.0}
  prose  survivor: {'hv': 0.0, 'reach': 0.0, 'coverage': 0.0}
  frontier keeps : ['formal']
  prose dropped from the frontier: True

live root: /tmp/formalism-audit-d6esi3py
  statuses : 0ada8ef8e2fe=accepted, f4b88d77cb50=accepted
  survivors: 2
  frontier : ["0ada8ef8e2fe50490ce394c1e450137758c7c17b53d60c4868cceb171dc86e24"]
  formal id in frontier: True
  prose  id in frontier: False

mutation proof (prose given one passing evaluable commitment): frontier keeps ['formal', 'prose'] -> penalty disappears: True

REPRODUCED
EXIT=0
```

Three legs, one of them a mutation control, all as the brief describes.

---

## 4. Measurement 2 — the live footprint, re-derived, not inherited

`measure_footprint.py` opens each root `read_only=True`, recomputes the survivor
set and every score triple from that root's own replayed state through the
shipped `run_report`, and compares against the frontier stored in
`run-result.json`. It writes nothing. Saved at `proof/footprint_2026-08-30.txt`
(before) and `proof/footprint_AFTER_2026-08-30.txt` (after).

### The brief's claim, and this lane's verdict on it

> LIVE FOOTPRINT: experiments/2026-08-12-live-grounded-extension-expansion/run
>   -- exactly two score triples among 233 survivors: 146 prose at
>      (0.0, 0.0, 0.0), 87 formal at (0.0, 0.0, 1.0); frontier == the 87.
> — `experiments/2026-08-27-audit-formalism-optional/PARKED.md:99-101`

**CONFIRMED, in every particular.** Measured output, before the change:

```
{
  "root": "experiments/2026-08-12-live-grounded-extension-expansion/run",
  "survivors": 233,
  "empty_battery": 146,
  "shipped_score_triples": {
    "(0.0, 0.0, 0.0)": 146,
    "(0.0, 0.0, 1.0)": 87
  },
  "stored_frontier_len": 87,
  "current_frontier_len": 87,
  "current_equals_stored": true,
  "current_frontier_is_exactly_the_battery_carriers": true,
  "empty_battery_survivors_on_current_frontier": 0,
  "road_a_frontier_len": 233,
  "road_b_frontier_len": 233
}
```

Reading it line by line: 233 survivors; exactly two score triples; 146 of them
at `(0.0, 0.0, 0.0)` and every one of those 146 carries no evaluable commitment
(`empty_battery: 146`); 87 at `(0.0, 0.0, 1.0)`; the recomputed frontier equals
the stored one; and it is **exactly** the set of battery carriers, with **zero**
of the 146 on it. Both candidate behaviour-changing roads move it to 233.

(The field `shipped_score_triples` was renamed
`score_triples_under_the_pre_2026_08_30_rule` after the fix landed, because the
shipped rule no longer emits a 0.0 there; the pre-fix transcript keeps the old
name, since it records what was actually run.)

### The control root

```
{
  "root": "experiments/2026-08-25-poietics-program/run",
  "survivors": 58,
  "empty_battery": 0,
  "shipped_score_triples": {"(0.0, 0.0, 1.0)": 40, "(0.0, 0.0, 0.5)": 11,
                            "(0.0, 0.0, 0.5714285714285714)": 7},
  "stored_frontier_len": 40,
  "current_frontier_len": 40,
  "current_equals_stored": true,
  "road_a_frontier_len": 40,
  "road_b_frontier_len": 40
}
```

This is the root that `tests/test_import_role_survivors.py:109-112` pins by
recomputing its frontier and asserting equality with the stored 40. It has ZERO
commitment-free survivors, so no road moves it. After the change,
`current_equals_stored` is still `true` for this root — pasted at
`proof/footprint_AFTER_2026-08-30.txt` — and the test passes in the ring (§8).

### What moved, after the change

`experiments/2026-08-12-live-grounded-extension-expansion/run`:
`current_frontier_len` 87 → **233**, `empty_battery_survivors_on_current_frontier`
0 → **146**, `current_equals_stored` `true` → **false**.

That last one is not a regression and is worth stating plainly: the RECOMPUTED
frontier over a historical root now differs from the frontier that root stored
when it ran. The 2026-08-14 operator law disposes of this in advance — "old runs
do not need to be valid or returnable" — and `PARKED.md:105-106` says so
explicitly for this very decision. **No committed root's bytes were modified.**
Both roots were opened `read_only=True`.

---

## 5. The law-based narrowing (item 2), and the argument shown

The binding text, quoted exactly from
`docs/proposals/DUAL_MODE_CONJECTURE_PREPLAN.md:42-57`:

> R-g (BINDING GUARDRAIL, operator's words 2026-08-08, "something I've repeated
> endlessly": "as long as the existing infrastructure does not force formalism
> and penalize conjectures that are not formal"): no mechanism in this program —
> nor anywhere in the harness — may require formal encoding for a conjecture to
> enter, rank, survive, or be accepted; may weight ranking, scheduling, or
> acceptance on a conjecture's KIND; or may escalate the formal-channel option
> into pressure ... Formal backing may confer PROTECTION (prose-immunity, as
> today); its absence confers no disadvantage. D3's and D4's regressions must
> prove kind-blindness: an informal conjecture's rank, criticism exposure, and
> acceptance path are byte-identical whether or not the formal channel exists in
> the build ...

Four probes, each a direct consequence of a quoted clause. `road_law_probe.py`
runs every road against all four and prints the frontier it computed, so this is
a measurement rather than an opinion.

| probe | the clause it comes from |
|---|---|
| L1 equal standing | "its absence confers no disadvantage" |
| L2 kind-blindness | "byte-identical whether or not the formal channel exists in the build" |
| L3 no reverse weight | "may weight ranking ... on a conjecture's KIND" — direction-neutral |
| L4 axis keeps meaning | not R-g: the operator's own question at `PARKED.md:73-77` |

Output at HEAD, before the change (`proof/road_law_probe_HEAD_2026-08-30.txt`):

```
road               L1    L2    L3    L4
today (no change)  FAIL  FAIL  PASS  PASS
(a) not-measured   PASS  PASS  PASS  PASS
(b) neutral 1.0    PASS  PASS  FAIL  PASS
(b) neutral mean   PASS  FAIL  PASS  PASS
(c) disclose only  FAIL  FAIL  PASS  PASS

SHIPPED (the tree this script was run against):
    L1 equal standing        FAIL  frontier=['formal']
    L2 kind-blindness        FAIL  prose_on_frontier: with_formal_channel=False without=True  (with=['pass'])
    L3 no reverse weight     PASS  frontier=['formal_partial']
    L4 axis keeps meaning    PASS  frontier=['passed']
    -> the shipped tree matches road: today (no change)
```

The argument, not the assertion:

- **Road (c) fails L1 and L2 for precisely the reason today's tree does**, because
  road (c) IS today's tree plus a typed note (`PARKED.md:88-90`: "No behaviour
  change"). Its computed frontier is `['formal']` — the prose survivor is still
  excluded. R-g says absence of formal backing "confers no disadvantage", not
  "confers a disclosed disadvantage". **A road that changes no behaviour cannot
  remove a behavioural penalty.** It remains a coherent ADDITION to a road that
  does remove it, which is why `STOP.md` offers `a+c` as an answer.
- **Road (b) at 1.0 fails L3.** Its computed frontier for "commitment-free
  artifact vs formally-backed artifact whose battery half-passed" is `['prose']`
  — the formal one is gone. That is a rank weight that reads kind, with its sign
  flipped, and R-g's clause is direction-neutral. Note this is stricter than
  CLAUDE.md's headline sentence, which forbids only the penalty on prose; the
  narrowing is grounded on R-g's wording, and this document says so rather than
  quietly using the stronger reading.
- **Road (b) at the population mean fails L2 instead.** Its fill value is
  computed from how the formally-backed artifacts in that same run happened to
  score, so whether a prose conjecture is published depends on the formal
  channel's contents — the exact thing "byte-identical whether or not the formal
  channel exists in the build" forbids. (It escapes L3 only because L3's
  two-element population makes the mean equal the single measured value; that is
  an artifact of the probe, and L2 is the probe that binds it. Stated so a
  reader does not think the mean variant survived on merit.)
- **Road (a) passes all four**, and L4 shows why that is not vacuous: "checked
  and failed" is still dominated by "checked and passed", so the axis keeps its
  discriminating power exactly where it has something to discriminate with.

**This narrows the fork; it does not close it.** Two live sub-choices remain the
operator's and are not law questions: whether to add road (c)'s note on top
(`a+c`), and whether the two consequences named in `STOP.md` are acceptable.

One road was considered and is NOT offered, so the operator's menu stays the
three that were priced: dropping `coverage` from `PARETO_AXES` entirely. It
removes the penalty, but it also destroys the discrimination among formally
backed artifacts that L4 exists to protect (on the poietics root it would put
all 58 survivors on the frontier instead of 40). Strictly worse than road (a)
for the axis's own purpose.

---

## 6. The defect's proof (item 3) — form chosen, and why

**Chosen: a standalone re-runnable script,
`proof_equal_standing.py`, not `xfail(strict=True)`.**

The reason is specific to this lane, not a general preference. Item 4 asks for
the recommended road to be BUILT on this same branch. `xfail(strict=True)` means
"this must fail; if it passes, that is a FAILURE" — so the moment the road (a)
commit lands on this branch, the marker XPASSes and **this lane turns the batch
red**, which the batch forbids. A script under the tranche directory is outside
the gate's collection path in both states and reports a typed verdict either
way. The equal-standing assertions still exist as ordinary pytest tests: they
landed GREEN, in the same commit as the behaviour that makes them true
(`tests/test_formalism_optional_rank.py`, 11 tests).

### Mutation proof of the script, in both directions

The script carries four legs and prints one of three typed verdicts
(`PENALTY_PRESENT` exit 0, `PENALTY_ABSENT` exit 1, `INSTRUMENT_BROKEN` exit 2).
Legs 2 and 3 are controls that must hold on EVERY tree; leg 4 re-scores the same
real artifacts under road (a)'s rule.

Before the change (`proof/equal_standing_BEFORE_2026-08-30.txt`):

```
LEG 1  frontier : ['formal']            both on the frontier: False
LEG 2  frontier : ['formal', 'prose']   control holds: True
LEG 3  frontier : ['passed']            control holds: True
LEG 4  frontier : ['formal', 'prose']   the exclusion disappears under the fix: True
VERDICT: PENALTY_PRESENT            EXIT=0
```

After the change (`proof/equal_standing_AFTER_2026-08-30.txt`):

```
LEG 1  frontier : ['formal', 'prose']   both on the frontier: True
LEG 2  frontier : ['formal', 'prose']   control holds: True
LEG 3  frontier : ['passed']            control holds: True
LEG 4  frontier : ['formal', 'prose']   the exclusion disappears under the fix: True
VERDICT: PENALTY_ABSENT             EXIT=1
```

It detects the present defect AND reacts to a fix — the simulated one (leg 4,
which fires on both trees) and the real one (the verdict flipping end to end).
Leg 3 is the control that stops a false green: a road that simply put every
survivor on the frontier would fail it, and the script would report
`INSTRUMENT_BROKEN` rather than a verdict.

### The pytest tests, proven red before and green after

`tests/test_formalism_optional_rank.py` against the PRE-FIX source tree
(`proof/tests_RED_before_fix_2026-08-30.txt`). The shipped module cannot even be
imported there, because the pre-fix tree has no `pareto_scores` seam, so section
B of that transcript runs a copy with that one import and that one test removed
and every other test byte-identical:

```
FAILED ...::test_informal_and_formal_of_equal_standing_rank_equally
FAILED ...::test_a_partly_passing_battery_is_not_out_ranked_by_nothing_to_check
FAILED ...::test_kind_blindness_prose_ranks_the_same_with_and_without_a_formal_channel
FAILED ...::test_frontier_treats_a_missing_score_as_not_measured[scored3-expected3]
4 failed, 6 passed in 0.76s
```

The 6 that pass are the controls — including
`test_control_b_a_failed_battery_is_still_dominated`, which must hold on both
trees. After the change: **11 passed**.

### Both architecture tests mutation-proven

`proof/tests_MUTATION_2026-08-30.txt`, two source mutants built in the
scratchpad (never in the repo):

```
### MUTANT 1 -- a fourth Pareto axis ('novelty') added to Config.PARETO_AXES
E       AssertionError: assert {'coverage', ...lty', 'reach'} == {'coverage', 'hv', 'reach'}
FAILED tests/test_formalism_optional_rank.py::test_architecture_every_pareto_axis_declares_its_commitment_free_state
1 failed, 10 passed

### MUTANT 2 -- the penalty reintroduced: pareto_scores emits coverage 0.0 for an empty battery
FAILED ...::test_informal_and_formal_of_equal_standing_rank_equally
FAILED ...::test_a_partly_passing_battery_is_not_out_ranked_by_nothing_to_check
FAILED ...::test_kind_blindness_prose_ranks_the_same_with_and_without_a_formal_channel
FAILED ...::test_architecture_axes_that_must_not_be_zeroed_are_omitted_instead
4 failed, 7 passed

### CONTROL -- the real tree
11 passed
```

This is P2's END STATE requirement — "an architecture test that goes red if a new
Pareto axis is added whose zero value is reachable by carrying no commitment" —
discharged, and shown to be able to fail.

---

## 7. The cone as measured, and the frozen-surface re-verification (item 6)

Measured, not inherited from the recon. Full transcript at
`proof/cone_and_frozen_surfaces_2026-08-30.txt`.

**Every path this lane writes:**

```
docs/map/CON-conjecture-kinds.md
docs/map/SUB-periphery.md
docs/map/SUB-scheduler.md
experiments/2026-08-27-audit-formalism-optional/repro_coverage_rank.py
experiments/2026-08-30-defect-formalism-rank-penalty/**
src/deepreason/capture/pareto.py
src/deepreason/scheduler/scheduler.py
tests/test_formalism_optional_rank.py
```

Two source files. `src/deepreason/config.py` was NOT written — deliberately; it
is the only file this lane could have collided with lane B on, and road (a) is a
semantics repair to an existing axis, not a new customization point (recorded in
`PARKED.md` L5). `src/deepreason/informal/trial.py` was NOT written — site (b)'s
forbidden ground.

**Frozen surfaces: none touched. Three independent instruments agree.**

1. The `INV-frozen-surfaces.md:297` branch tripwire, run verbatim over this
   cone: **exit 0** (pass).
2. `dr-validate-change`'s five-path frozen diff: **empty**. And the two paths
   that command omits (`RECON-SHARED.md:176` flags this gap): `verification/`
   and `llm/firewall.py` — also **empty**.
3. `grep` of every cone path against `docs/map/INV-frozen-surfaces.md`: **no
   hits**.

**One surprise, resolved with evidence rather than dismissed.**
`python tools/blast_radius.py --files src/deepreason/scheduler/scheduler.py
src/deepreason/capture/pareto.py --symbols run_report pareto_scores frontier`
reports `"frozen_surface_verdict": "CONTACT"`, naming two surfaces. Both entries
are tier `SYMBOL_INDIRECT`, which the tool's own `detail` field describes as
"grep-based; not proof of semantic contact". It is a **name collision**, and here
is the proof:

- Every occurrence of the word `frontier` inside `invariants.py` and
  `run_manifest.py` is the MODEL-PROFILE TIER name
  `Literal["compact", "standard", "frontier"]`, plus one prose word in a comment
  at `invariants.py:4234` ("takes a problem off the frontier"). Not one is the
  Pareto frontier or the `run-result.json` `frontier` field.
- Neither `pareto` nor `run_report` occurs **anywhere** in ANY frozen surface
  (`invariants.py`, `run_manifest.py`, `verification/`, `harness.py`,
  `capabilities/state.py`, `qualification.py`) — the grep returns nothing.
- `frontier` does not occur in `src/deepreason/verification/` **at all**, so the
  replay-validation reader cannot be reading the published frontier.

Recorded here as a finding in its own right: `blast_radius.py`'s
`SYMBOL_INDIRECT` tier will report CONTACT for any change touching a symbol
named `frontier`, because this codebase uses that word for a model tier. A
future lane should resolve it the same way rather than either trusting the
verdict or waving it away.

**No grant was requested and none is owed.**

---

## 8. The ring

Only the ring, never the full gate: four lanes share a 4-CPU box, and a
measurement taken under load is not a measurement.

RING 1 — the 12 test files that recompute or consume a Pareto frontier
(`proof/ring1_2026-08-30.txt`):

```
python -m pytest tests/test_formalism_optional_rank.py tests/test_scheduler.py \
  tests/test_loop.py tests/test_import_role_survivors.py tests/test_results_command.py \
  tests/test_lifecycle_operation_parity.py tests/test_amendment_epochs.py \
  tests/test_single_run_path.py tests/test_attached_evidence_citation.py \
  tests/test_failure_terminal_reports_real_token_spend.py tests/test_mcp_run.py \
  tests/test_signals.py -q

117 passed in 496.39s (0:08:16)
```

`tests/test_import_role_survivors.py` is in there, and it is the only test in the
repository that recomputes a frontier over a committed root and pins it against
the stored payload. It passes.

RING 2 — the recon's remaining named files plus everything that reads the stop
decision, since `frontier_delta` is a `StopMetrics` input
(`proof/ring2_2026-08-30.txt`):

```
python -m pytest tests/test_prose_refutation_boundaries.py tests/test_oracle.py \
  tests/test_stop_policy.py tests/test_workflow_stop_lifecycle_c4.py \
  tests/test_bridge_after_typed_stop.py tests/test_v6_resumed_terminal_revalidation.py -q

129 passed in 269.58s (0:04:29)
```

**Ring total: 246 passed, 0 failed across 18 files.**

**Both rings were RE-RUN after the review repairs** (`bool(shared)` deleted from
`capture/pareto.frontier`, docstring rewritten), and both transcripts are
appended to the same proof files: RING 1 `117 passed in 487.65s` at load average
5.29 → 9.41, RING 2 `129 passed in 260.95s` at load average 9.41 → 9.14. Same
246, 0 failed.

**`tests/test_mcp_run.py` is LOAD-FLAKY on this box, and it is not this lane's.**
A reviewer running RING 1 concurrently with another ring measured `2 failed, 115
passed`, both failures in that file on a hard
`_RUN_THREADS[...].join(timeout=2)` deadline
(`assert 'running' == 'completed'`, `ValueError: RUN_RESULT_NOT_READY`), and
reproduced the same failures on the PRE-FIX tree, which contains none of this
lane's source change. This lane's own re-runs — under load average 5.3 to 9.4 —
were green both times, and `tests/test_mcp_run.py` alone is `7 passed in 13.64s`.
So the flake is intermittent and load-dependent, not deterministic. **At fan-in,
re-run those two node ids in isolation before charging a red to any lane.** The
durable repair (a polled deadline instead of `join(timeout=2)`) belongs to a
tranche that owns that file; §11, finding 6.

### Every map check this lane added or changed, run INDIVIDUALLY

`docs_verify` as a whole is the fan-in's instrument, so each new or edited
`check:` was executed on its own. **SEVEN `check:` lines were added or changed**
— `git diff 152c7e204 -- docs/map/ | grep -c '^+`check'` → 7, of which three
replace a removed original. An earlier version of this section said six, because
the transcript counted a pre-existing re-run as one of them and omitted the
`SUB-scheduler.md` "Where to change what" pytest chain entirely (§11, finding 5).
`proof/map_checks_2026-08-30.txt` is now GENERATED by enumerating the seven from
that diff and running each verbatim, so the count cannot drift from the diff
again. All seven exit 0:

| # | document / clause | result |
|---|---|---|
| 1 | `CON-conjecture-kinds.md:102` "Must never do" (NEW, four node ids) | `4 passed`, exit 0 |
| 2 | `CON-conjecture-kinds.md:242` Traps (NEW) | `11 passed`, exit 0 |
| 3 | `SUB-periphery.md:231` Traps (NEW) | `5 passed`, exit 0 |
| 4 | `SUB-scheduler.md:73` Entry points (CHANGED — `pareto_scores` added to the grep chain) | `1 passed`, exit 0 |
| 5 | `SUB-scheduler.md:177` "Where to change what" pytest chain (CHANGED — the new row's node id appended) | `12 passed`, exit 0 |
| 6 | `SUB-scheduler.md:179` "Where to change what" symbol-grep chain (CHANGED — `pareto_scores` appended) | exit 0 |
| 7 | `SUB-scheduler.md:206` Traps (NEW) | `11 passed`, exit 0 |

Rows 5 and 6 had to be edited because that table states in its own words that
"Every Test cell above is a node id this check runs by name ... every Edit cell
names a symbol the check greps for" — adding a row without adding its node id
and its symbol would have falsified that sentence.

Listed separately because it is NOT one of the seven: `CON-conjecture-kinds.md`'s
pre-existing kind-guard grep, whose clause prose this lane extended, was re-run
to prove the edit did not falsify it — exit 0.

Every `check:` line in all three documents was also parsed with `docs_verify`'s
own `_CHECK` grammar: 21 / 24 / 20 column-0 openers respectively, with the only
non-matches being two PRE-EXISTING multi-line `python -c "` blocks that this lane
did not touch. None of the new checks begins with a token `--audit`'s vacuity
regex would flag.

**Owed at fan-in, not run here:** `pytest tests/ -q -n 4` (the full gate),
`python tools/docs_verify.py`, `--audit`, `--links`. The batch's load rule
forbids running them inside a lane.

---

## 9. The map moved in the same commit as the code

| document | what changed |
|---|---|
| `docs/map/CON-conjecture-kinds.md` | the "Must never do" clause now says WHY its existing check was never sufficient (kind can be read without naming a kind guard) and carries a NEW behavioural check; a "Where it lives" row for the kind-conditional RANKING term; a "Where to change what" row for `pareto_scores`; two Traps entries |
| `docs/map/SUB-scheduler.md` | `pareto_scores` added to Entry points and to that section's check; the `run_report` bullet states the frontier-length and stop-timing consequence; a "Where to change what" row, with its node id added to the table's own check so the table's promise ("every Test cell is a node id this check runs by name") stays true, and `pareto_scores` added to the symbol-grep check for the same reason; one Traps entry |
| `docs/map/SUB-periphery.md` | a "Where to change what" row for `capture/pareto.frontier`'s missing-score contract; one Traps entry, which names the second-order trap — two points sharing NO axis must still never dominate, and what carries that is the STRICTNESS clause `any(a[x] > b[x] ...)`, which is False over an empty `shared`. REWRITTEN after review: the first version blamed a `bool(shared)` guard whose removal the attached check could not detect (§11, finding 2) |

New checks that can fail, each mutation-proven in §6:
`tests/test_formalism_optional_rank.py` whole-file (two documents) and the
four-node-id list on `CON-conjecture-kinds.md`'s "Must never do" clause.

**No `Verified-at:` stamp was advanced on any of the three documents.** This lane
did not re-run their full check sets — `docs_verify` is the batch's fan-in
instrument, not a lane's. A stale stamp is honest; a false one is not.

---

## 10. Honest residue

- **The decision is not made.** Road (a) is BUILT AND PARKED, NOT INTEGRATED.
  Nothing in §3-§7 is wasted if the operator answers "b" or "c": the
  measurements and the law analysis apply to whichever road is chosen.
  **Dropping the road is NOT a single revert**, and this document said it was
  until a skeptic re-ran it (§11, finding 1). Road (a)'s code is in
  `fe6b29ed2`; two `docs/map/SUB-scheduler.md` `check:` lines that grep for
  `pareto_scores` and run
  `tests/test_formalism_optional_rank.py::test_architecture_axes_that_must_not_be_zeroed_are_omitted_instead`
  were added by the delivery commit `ce362b2e3` after it, so `git revert
  fe6b29ed2` alone leaves both of them RED (reproduced:
  `proof/drop_road_a_2026-08-30.txt` §A). The drop is one act through
  `drop_road_a.sh`, which reverses this lane's contribution to the road's eight
  files, refuses on a moved tree, and re-runs those two checks before reporting
  DROPPED.
- **This is a behaviour change, not a report change.** `frontier_delta` feeds
  `StopMetrics` — `Scheduler._stop_metrics`, at the
  `frontier_delta=len(before["frontier"] ^ after["frontier"])` assignment, and
  `runtime/stop.py:34/164`, with `frontier_delta_max` defaulting to 0 — so a
  run whose survivors include commitment-free artifacts can now stop at a
  different cycle. (Cited by symbol because the line number this bullet
  originally carried, `scheduler.py:3003`, was the PRE-fix line and was already
  stale when it was written; §11, finding 4.) No live run has
  been performed to observe this; it is derived from the wiring and disclosed
  rather than measured.
- **The penalty does not generalise across the record, and saying so is part of
  the finding.** The audit's own residue (`VERDICT.md:106-114`) measured prose on
  the frontier at 36.7% (92/251) against formal's 32.1% (747/2 324) over 2 575
  pooled candidate-role artifacts — prose slightly AHEAD. The case for the repair
  is the code fact and the one root where it bit hard, never an aggregate. This
  lane did not re-derive those pooled percentages; they are quoted from the audit
  and are the audit's claim, not this lane's measurement.
- **Only two roots were measured, and that is deliberate.** The root sweep is
  retired (operator ruling 2026-08-22). The two chosen are the one the brief
  names as the live footprint and the one a test pins.
- **`hv` and `reach` still have the same 0.0-default shape** and were NOT fixed
  here. In both roots measured they are 0.0 for every survivor of both kinds, so
  no penalty is measurable through them today; a run where a formally-backed
  artifact earns `hv > 0` would reproduce the same domination on a different
  axis. Parked as L3 with the specific first question to ask. **Do not read the
  coverage repair as having closed the class.**
- **Road (a) cuts both ways, and the operator should hear it from this document
  rather than from a run.** Not competing on coverage also means not defending
  with it: a prose artifact scoring higher on `hv` can now dominate a formal one
  whose coverage is 1.0, because coverage is not in their shared comparison. Not
  reachable in either committed root (all `hv`/`reach` are 0.0), but reachable in
  principle. Stated in `STOP.md` as consequence 2.
- **The full gate and `docs_verify` have not been run by this lane.** Ring only.
- **`docs_verify --audit` already reports a pre-existing finding**
  (`SEAM-llm-x-rules.md:54` unparseable, per `RECON-SHARED.md:7`), which lane D
  owns. Do not attribute it to this lane at fan-in.
- **What the record cannot settle**: whether the 146 excluded conjectures were
  any good. The finding is that they were excluded for their KIND, not that they
  deserved to be published. Accepted does not mean true, and neither does
  "on the frontier".

---

## 11. What independent skeptics found, and what was done (2026-08-30)

Reviewers who did not write this tranche re-ran its claims against this branch.
They confirmed **two MAJOR defects and six minor ones**, each with the command
that proved it. Every one was reproduced HERE before it was fixed — nothing was
taken on the reviewer's word, nothing was narrowed to make a finding go away,
and no assertion was weakened. None was refuted; all eight stood.

### Finding 1 (MAJOR) — the park could not be unwound in one act

**What they showed.** §10 of this document, `RESULTS.md` and `STOP.md` all said
answering "b" or "c" discards commit `fe6b29ed2`. It does not. The delivery
commit `ce362b2e3` that followed edited two `docs/map/SUB-scheduler.md` `check:`
lines to grep for `pareto_scores` and to run
`tests/test_formalism_optional_rank.py::test_architecture_axes_that_must_not_be_zeroed_are_omitted_instead`;
both symbols exist only inside `fe6b29ed2`. Reverting it alone leaves two RED
map checks on the branch.

**Reproduced here** (`proof/drop_road_a_2026-08-30.txt` §A): `git revert
--no-edit fe6b29ed2` in a throwaway clone exits 0, and the two surviving check
lines then exit 4 and 1.

**What was done.** The commits were NOT restructured, and the reason is
deliberate: `STOP.md` hands the operator the hash `fe6b29ed2`, so squashing the
map hunk into it would rewrite that hash and leave the operator's own copy of
the question pointing at a commit that no longer exists. Instead the claim was
corrected everywhere it appeared (`STOP.md`, `DELIVERY.md` §10, `RESULTS.md`)
and the drop was made a genuine single act:
`drop_road_a.sh` reverses this lane's contribution to the road's eight files
since the park base `736b50839`, refuses on a dirty or moved tree, and re-runs
the two checks before it reports `DROPPED`. Verified by running it on a
throwaway clone (`proof/drop_road_a_2026-08-30.txt` §B): after the drop,
`docs/map/`, `src/` and `tests/` are **byte-identical** to `736b50839` and both
checks exit 0, and the tranche's proof transcripts survive — which a plain
`git revert` does not leave, because `fe6b29ed2` added them (§A). Every guard
is exercised in §C: dirty tree, road already gone, a later change that renamed
the function, a later change that edited inside the road's hunk, an empty
reverse patch (all `REFUSED`, exit 1), and a drop the road survives
(`DROP_UNSOUND`, exit 2, with the undo command printed). A first draft of §C
claimed a refusal the script did not make; that draft committed its "later
change" onto the lane branch itself, which put the change inside the patch.
Re-run with the later change on a separate branch — the fan-in's real shape —
and recorded with the correction visible rather than silently replaced.

**Residue.** The default fan-in action is still to merge the branch, which
integrates road (a). That is a batch-level decision this lane cannot make; what
this lane owes is a cheap, proven way OUT, and that now exists.

### Finding 2 (MAJOR) — a map Traps entry named a guard that was dead code

**What they showed.** `docs/map/SUB-periphery.md`'s new Traps entry said a
"shared axes only" rule written without the `bool(shared)` guard "silently makes
every P1 survivor dominate every other". It does not: with `shared == []`,
`all(...)` is True and `any(...)` is False, so dominance is already False
without the term. Deleting the guard left every attached check green — a map
claim authenticated by re-derivation whose check could not detect its falsity,
which is exactly what the map law exists to prevent. The same attribution was in
`capture/pareto.py`'s docstring.

**Reproduced here** (`proof/pareto_mutation_2026-08-30.txt` §3): the mutant with
only `bool(shared) and` removed passes the Traps entry's own check (`5 passed`,
exit 0), and an exhaustive enumeration over all 64 point shapes the three axes
admit finds **zero** pairs where the guard changes the answer.

**What was done.** `bool(shared)` was deleted as dead code. The docstring and the
Traps entry now attribute the no-shared-axis property to the STRICTNESS clause
`any(a[x] > b[x] for x in shared)`, which is what actually carries it, and name
the two mutations that turn the attached check RED — both run before the
sentence was written, per the map law: deleting the strictness clause
(`5 failed`) and short-circuiting an empty `shared` to `True` (`3 failed`).

**Correction to the record, unfixable in place.** `fe6b29ed2`'s commit message
carries the same wrong attribution ("Two points sharing no axis still never
dominate, which is what keeps loop.py's P1 frontier equal to its survivor set"
offered as the guard's justification). A commit message cannot be edited without
rewriting the hash the operator holds; the correction lives here and in the map.

### Finding 3 (minor) — `PARKED.md` L3's own line-rot correction had rotted

L3 said the `SITES.md` row for `scheduler.py:1330` "has rotted to :1345". After
this lane's own road commit it sits at `:1357`. Fixed by citing both sites by
SYMBOL — `grep -n "if not carried:" src/deepreason/measures/reach.py` (:131) and
`grep -n "if is_hv_floor(kappa):" src/deepreason/scheduler/scheduler.py` (:1357)
— so the citation cannot rot a third time.

### Finding 4 (minor) — `scheduler.py:3003` was the pre-fix line

`DELIVERY.md` §10 and `RESULTS.md` cited `scheduler.py:3003` for the
`frontier_delta` → `StopMetrics` wiring. On this tree that line is
`event.llm.raw_ref`; the assignment is at `:3015`, inside `_stop_metrics`
(`:2977`). The substantive disclosure is TRUE and unchanged — only the pointer
was wrong, and it was already wrong when written, because the road commit had
already moved the line. Both citations are now by symbol.

### Finding 5 (minor) — six checks evidenced, seven added or changed

`proof/map_checks_2026-08-30.txt` held six sections, one of which was a
PRE-EXISTING check re-run, while `git diff 152c7e204 -- docs/map/` shows seven
added-or-changed `check:` lines. The unevidenced one was
`SUB-scheduler.md`'s "Where to change what" table pytest chain. The transcript is
now generated by enumerating the seven mechanically from that diff and running
each verbatim; the pre-existing re-run is kept, labelled as a bonus rather than
counted.

### Finding 6 (minor) — RING 1's green is conditional on load, and it is not this lane's defect

Under concurrent load from the other lanes on this 4-CPU box,
`tests/test_mcp_run.py::test_start_poll_result_and_progress_notifications` and
`::test_typed_v6_stop_can_continue_and_append` fail on a hard
`_RUN_THREADS[...].join(timeout=2)` deadline. The reviewer reproduced the same
failures on the PRE-FIX tree, which contains none of this lane's source change,
and green on this tree when the box is quiet. Recorded, not fixed: the file is
outside this lane's cone. **At fan-in, re-run those two node ids in isolation
before charging a red to any lane.**

### Finding 7 (minor) — `road_law_probe.py`'s SHIPPED column failed silently

The SHIPPED column is the only part of that instrument that reads the real tree;
the modelled rows are a re-implementation and print identically on every tree. It
was wrapped in a bare `except Exception` that printed one line and returned 0, so
a tree whose `run_report` raises produced a run that looked complete and carried
no information at all. It now prints a traceback and
`VERDICT: INSTRUMENT_BROKEN` and exits 2, matching `proof_equal_standing.py`'s
convention. Proven both ways in `proof/road_law_probe_INSTRUMENT_2026-08-30.txt`:
unchanged output and exit 0 on this tree, exit 2 against a mutant whose
`run_report` raises.

