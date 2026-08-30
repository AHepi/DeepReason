<!-- DR-CON-scheduler-ranking -->
Verified-at: 6c65f95e8
Verify: python tools/docs_verify.py
Owns: src/deepreason/scheduler/scheduler.py
Seams: DR-SEAM-scheduler-x-rules
Seams-undocumented: authority x scheduler-ranking, harness x scheduler-ranking, scheduler-ranking x schools

# Scheduler ranking — which problem a cycle works on

## What it is

`Scheduler._select_problem` is the single tie-break authority for "which
problem does this cycle spend its call on". It is a narrower socket than
`DR-SUB-scheduler` (which also covers budgets, capability dispatch and the
whole `step()` sweep): ranking is exactly the ordering decision, expressed
as one sort key under `LIVENESS_QUEUE` and one under the legacy
round-robin path. Both modes hold the same guarantee in different shapes —
the operator's seed question outranks every spawn, always — because a
recorded run (`selfstudy run-9175f0ec`) spent an entire 200k-call budget
inside a connection problem that won cycle 0 on the bare id tie-break
alone, and the operator's own question terminated `budget_denied` having
made zero provider calls.

## The socket contract — what it promises, what it is handed, what it must never do

**Promises:** the operator's `SEED` question always wins a rank tie, in
both selection modes — ranked directly after the age term, before the
reflexive tie-break, in both the `LIVENESS_QUEUE` sort key and the
round-robin pool's sort key.
`check: grep -q "p.provenance.trigger != SpawnTrigger.SEED," src/deepreason/scheduler/scheduler.py && test "$(grep -c "provenance.trigger != SpawnTrigger.SEED" src/deepreason/scheduler/scheduler.py)" -eq 2`

Since 2026-08-29 that promise has one more claimant to hold against.
`SpawnTrigger.SUCCESSOR` can be minted MID-RUN, from a critic's proposed
question behind a default-OFF switch (`DR-CON-successor-questions`), and it
loses the tie by construction rather than by arrangement: the term is a
boolean over the trigger, a successor is not the seed, and `False` sorts before
`True`. No scheduler change was needed and none was made — `scheduler.py` took
a zero-line diff in that tranche.
`check: python -m pytest tests/test_successor_rank_tie.py -q`

**And the honest residue, because a promise stated wider than it holds is worse
than a narrow one.** The seed term decides TIES. In the `LIVENESS_QUEUE` key
the FIRST term is `-(age * weight)`, so a freshly minted problem — never
worked, therefore maximally aged — can out-AGE a seed that HAS been worked.
That is true of every mid-run trigger and is not new with SUCCESSOR; what is
new is that a critic's own words can now create one. The only mitigation on the
tree is the wander cap, which is a CANDIDACY gate under
`SEED_PROBLEM_BUDGET_FLOOR` and not a rank term. Whether the operator wants
STRICT DOMINATION instead of the tie guarantee is parked, with both readings
priced, in `experiments/2026-08-30-change-successor-questions/PARKED.md` (Q4,
prompt P9B-6); closing it means changing this socket's rank key, which is what
the two checks above exist to make expensive.
`check: python -m pytest tests/test_successor_rank_tie.py::test_the_successor_still_gets_worked_once_the_question_has_been -q`

Import-role admission records (attached-source records, source-
reliability assertions) never count as a "survivor" — the aging weight
cannot be depressed by evidence-admission bookkeeping mistaken for a
solved candidate. The socket does not OWN that rule and no longer spells
it: `deepreason.ontology.state.counts_as_survivor` is the one authority,
and every survivor surface calls it (`DR-SUB-ontology`). The check below
used to grep this file for the literal, which is exactly the check that
passed while `run_report`, two hundred lines up in the same file, had no
role clause at all and published 24 admission records as survivors of
`run-1b31f006`.
`check: python -c "
import inspect, pathlib
from deepreason.scheduler.scheduler import Scheduler
src = inspect.getsource(Scheduler._select_problem)
assert 'counts_as_survivor(state, aid)' in src
assert 'ProvenanceRole.IMPORT' not in pathlib.Path(inspect.getfile(Scheduler)).read_text()
"`

Both guarantees are pinned by regression, not only by reading the sort key.
`check: python -m pytest tests/test_controller.py::test_operator_question_outranks_spawns_at_cycle_zero tests/test_scheduler.py::test_focus_family_restricts_selection -q`

**The wound-count term (Rung 7, D-1 answered A), and where it sits.** A
PROMOTION problem rises with the number of wounds its subject carries: more
wounds is a louder open demand for an account of them, and D-1's answer is that
this is the ONLY scheduling consequence a fallen or wounded background gets —
"the incumbent's promotion problem stays on the frontier, ranked by wound
count, attention only". No crisis-problem spawn trigger exists, and its absence
is what the answer chose.

The term sits AFTER the `SEED` term in both sort keys, and the ordering is the
promise above rather than a preference: a background carrying forty wounds must
not outrank the operator's own question. It reads a count over the warrant
table and the problem's own `provenance.from_` — never a standing view, never a
derived problem status — so `DR-SUB-calculus`'s NO SCHEDULER SELECTION row and
`DR-CON-standing-and-background`'s disambiguation check both stay true as
written.

`check: python -m pytest tests/test_scheduler_promotion_rank.py -q`
`check: python -c "
import inspect
from deepreason.scheduler.scheduler import Scheduler
src = inspect.getsource(Scheduler._select_problem)
seed = src.index('provenance.trigger != SpawnTrigger.SEED')
wounds = src.index('promotion_wounds.get(p.id, 0)')
assert seed < wounds, 'the wound term must sit AFTER the seed term'
assert src.count('promotion_wounds.get(p.id, 0)') == 2, 'both sort keys'
"`

**What it is handed:** the harness's `state` (problems, artifacts, status —
read only, never mutated here); `reflexive_problems(state)`, the lineage-
following meta-work set; the `Config` knobs `FOCUS_PROBLEM`, `FOCUS_FAMILY`,
`LIVENESS_QUEUE`, `INTEGRATION_BUDGET_SHARE`, `SEED_PROBLEM_BUDGET_FLOOR` and
`ATTENTION_ALLOCATION_POLICY`; and the scheduler's own per-instance attention
caches `_problem_worked` (liveness ages), `_seed_cycles` (worked cycles on
the seeded lineage) and `_capability_cycles` (cycles the capability step took)
— all rebuildable and non-epistemic.

**The wander cap is a CANDIDACY gate, never a rank term** (F3, 2026-08-26).
This is the sharpest thing to know about it. It sits beside
`INTEGRATION_BUDGET_SHARE` — which gates reflexive problems out of candidacy
when they are over their share — one lineage class higher, and it touches the
sort key not at all. Every guarantee this document pins on that key (the seed's
tie-break win, the wound term's position after it) is therefore untouched by
construction rather than by re-derivation. When the seeded lineage's share of
worked cycles falls below its floor, self-spawned problems yield candidacy FOR
THAT CYCLE — and only while seeded work remains, so no cycle is ever lost.

The policy is selected by id from `wander.LINEAGE_POLICIES` and consumed only
through `wander.decide`; the decision is STASHED, never emitted here, because
selection is read-only (below). Motivated by W6's post-mortem: one run spent
41.2 % of its budget on a problem it invented about its own critic while the
operator's question got 53.2 %
(`experiments/2026-08-26-run-anatomy-program/W6-token-flow/`).

`check: python -c "
import inspect
from deepreason.scheduler.scheduler import Scheduler
src = inspect.getsource(Scheduler._select_problem)
gate = src.index('decision.engaged')
assert 'wander.decide(' in src and 'self._pending_wander = decision' in src
rank = src.index('def rank(p)')
assert gate < rank, 'the wander gate must sit in candidacy, before the rank key'
assert 'decision' not in src[rank:src.index('best = min(')], 'the throttle leaked into the rank key'
"`
`check: python -m pytest tests/test_wander_cap.py -q -k "floor_holds or starves or never_loses or yields"`

**Which cycles the cap is computed over, and which it is disclosed on**
(audit finding F-F, fixed 2026-08-28). `step()` has one branch that advances
`self._cycles` without selecting a problem: the capability step. Those cycles
are counted as their OWN class and are OUT of the policy's denominator —
a candidacy gate has no candidacy to withhold on a cycle that selects nothing,
so a denominator counting them would fall for a reason the gate can never act
on. The scheduler decides none of this: it reports `capability_cycles` on the
reading and `wander_cap_v1` subtracts it, so an alternative accounting (say,
attributing a capability cycle to its proposal's lineage) is a registry entry
under `DR-REC-revise-allocation-policy`, not an edit here.

The exclusion is arithmetic only. The reading is emitted on EVERY cycle that
advanced the counter, capability cycles included, because P-T1 epoch 6 went
silent for 20 of its 24 cycles and a reader cannot tell silence from stability.
The throttle record stays a transition event and cannot fire on a capability
cycle, because neither counter the share is built from moves across one.

`check: python -c "import inspect; from deepreason.scheduler.scheduler import Scheduler as S; src = inspect.getsource(S.step); b = src[src.index('_simulation_capability_step()'):src.index('scan_spawns(')]; assert 'self._disclose_wander()' in b, 'the capability branch stopped disclosing'; assert 'self._capability_cycles += 1' in b, 'capability cycles re-entered the denominator'; assert b.index('_wander_reading()') < b.index('self._capability_cycles += 1')"`
`check: python -m pytest tests/test_wander_cap.py -q -k "dilute or order_independent or inventing or epoch_1" -q`

**Must never do:** write to disk or assign a `Status`/`hv`/`reach` value —
attention and ranking only, exactly like the rest of `DR-SUB-scheduler`
(the package-wide guarantee this socket inherits, not a separate one).

**It must not write to the LOG either, and that is not obvious.** The
prohibition above names disk and labels; a `record_measure` call is neither,
and it still breaks this socket. `_select_problem` is called on a TIME-TRAVEL
harness opened read-only for replay, which refuses every write, and it is
called by callers that only want the ranking. The wander cap's first
implementation emitted its disclosure from inside the ranking function and
turned two committed suites red — one of them precisely on the read-only
harness. The decision is stashed on `_pending_wander`; the cycle body emits it.

`check: python -c "
import inspect
from deepreason.scheduler.scheduler import Scheduler
src = inspect.getsource(Scheduler._select_problem)
for w in ('record_measure', 'create_artifact', '_commit('):
    assert w not in src, w
"`
`check: ! grep -rqE "open\(|write_text|write_bytes|\.mkdir\(" src/deepreason/scheduler/ --include=*.py && ! grep -rqE "state\.(status|hv|reach)\[[^]]*\] *=" src/deepreason/scheduler/ --include=*.py`

Select a `RESEARCH`-triggered problem for ordinary gamma work — research
problems are worked by backends, never by `_select_problem`'s candidate
pool.
`check: grep -q "p.provenance.trigger != SpawnTrigger.RESEARCH" src/deepreason/scheduler/scheduler.py`

Let reflexive (meta-economy) work escape its `INTEGRATION_BUDGET_SHARE`
cap by following only the spawn trigger and not the lineage — the Bronze
Age postmortem: debt/remove-arbitrariness successors escaped the
reflexive set entirely when tracked by trigger alone.
`check: grep -q "self._integration_cycles / self._cycles < self.config.INTEGRATION_BUDGET_SHARE" src/deepreason/scheduler/scheduler.py && python -m pytest tests/test_reflexive_discipline.py::test_reflexive_budget_follows_lineage -q`

## Where it lives

| Aspect | File | Symbol |
|---|---|---|
| The ranking entry point | `scheduler/scheduler.py` | `Scheduler._select_problem` |
| Meta-work set (lineage, not just trigger) | `scheduler/scheduler.py` | `reflexive_problems` |
| Stage isolation for a staged pipeline | `scheduler/scheduler.py` | `problem_family`, `Config.FOCUS_FAMILY` |
| Discrimination backoff feeding the candidate filter | `scheduler/scheduler.py` | `_disc_paused` |
| The attention cache ranking reads | `scheduler/scheduler.py` | `_problem_worked` |
| The two cycle classes the wander cap is computed over | `scheduler/scheduler.py` | `_seed_cycles`, `_capability_cycles`, `_wander_reading` |

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| Which problem a cycle works on, or the rank tie-break | `_select_problem`; `Config.LIVENESS_QUEUE`, `FOCUS_PROBLEM`, `FOCUS_FAMILY` | `tests/test_controller.py::test_operator_question_outranks_spawns_at_cycle_zero`, `tests/test_scheduler.py::test_focus_family_restricts_selection` |
| What counts as reflexive/meta work, or its budget share | `_REFLEXIVE_TRIGGERS`/`reflexive_problems`; `Config.INTEGRATION_BUDGET_SHARE` | `tests/test_reflexive_discipline.py::test_reflexive_budget_follows_lineage` |
| How a cycle counts toward the seed-lineage share | a new entry in `wander.LINEAGE_POLICIES` reading `LineageReading.capability_cycles` — never `_select_problem` or `step()` | `tests/test_wander_cap.py::test_capability_cycles_do_not_dilute_the_floor` |

## Traps

See `DR-SUB-scheduler`'s Traps for the package-wide hazards this socket
also inherits (the capability-state pooling filter, ladder interventions
must not latch). Socket-specific, already covered above and not
re-derived: cycle 0 falling to the bare id tie-break
(`selfstudy run-9175f0ec`), and the meta-economy eating the inquiry
(Bronze Age postmortem).
