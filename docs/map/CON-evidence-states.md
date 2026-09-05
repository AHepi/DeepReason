<!-- DR-CON-evidence-states -->
Verified-at: 5e44a650e
Verify: python -m pytest tests/test_evidence_states.py tests/test_evidence_states_law_line.py tests/test_criticism_dispatch_declaration.py -q
Owns: src/deepreason/views/evidence_states.py, src/deepreason/runtime/criticism_dispatch.py
Seams: 
Seams-undocumented: adjudication x evidence-states, application x evidence-states, scheduler x evidence-states

# Evidence states — telling a survivor from an untested conjecture

## What it is

An admitted conjecture nobody ever attacked and one that beat off a warranted
attack both carry `Status.ACCEPTED`, and the label cannot tell them apart. The
operator's success criterion is progress — "survivors harder to vary, bolder
conjectures that survived criticism" — so a reader that cannot separate those
two cannot measure the thing the project is for. This concept is the separation:
one of four readings per admitted artifact, DERIVED from facts already on the
record, changing nothing.

It is not a `Status` and it is not a fifth label. Nothing admits, ranks,
immunises or refutes on it, and the packages that decide those things may not
name it at all. The reading is downstream of everything, which is exactly what
lets it be added without touching a frozen surface.

The second half of the concept is a DECLARATION, because the first half has a
hole without it. "Nothing attacked this" means two incompatible things: the
critics looked and found nothing, or the critics never got to it. Only the first
is evidence. So a criticism pass now states on the record whether it made every
call it planned, and the absence of an attack reads as a measurement only for
the targets a pass that ran in full actually named.

## Where it lives

| Aspect | File | Symbol |
|---|---|---|
| The four readings | `src/deepreason/views/evidence_states.py` | `EvidenceState` |
| The reading, per artifact | `src/deepreason/views/evidence_states.py` | `evidence_states` |
| The reading as a surface section | `src/deepreason/views/evidence_states.py` | `evidence_state_summary` |
| The per-artifact frontier column | `src/deepreason/views/evidence_states.py` | `frontier_column` |
| The declaration's name and closed vocabulary | `src/deepreason/runtime/criticism_dispatch.py` | `CRITICISM_DISPATCH_SIGNAL`, `OUTCOMES` |
| The one writer | `src/deepreason/runtime/criticism_dispatch.py` | `declare_criticism_dispatch` |
| Where a pass declares itself | `src/deepreason/scheduler/scheduler.py` | `_arg_crit` (three exits), `_foreign_arg_crit` (entry) |
| What a warranted attack IS | — | `DR-CON-warrants-and-attacks` |
| The law line | `tests/test_evidence_states_law_line.py` | `DECIDING_PACKAGES`, `PERMITTED` |

## The rules it obeys

**Four readings, in this order, and no fifth.** The order is the evaluation
order: a refuted artifact is REFUTED whatever else is true of it.
`check: python -c "from deepreason.views.evidence_states import EvidenceState; assert [s.value for s in EvidenceState] == ['open','supported','refuted','contested'], [s.value for s in EvidenceState]"`

**A critic CALL is not criticism.** The blind-critic bench of 2026-09-04
measured a critic that attacked every target it was shown — rate 1.000 in all
four cells (`experiments/2026-09-04-experiment-blind-critic/RESULTS.md`) — so
counting calls would read a saturated instrument as universal survival. Only a
REGISTERED warrant that became an attack edge (`DR-CON-warrants-and-attacks`:
no warrant, no edge) or a trial that reached a ruling moves an artifact off
OPEN. A bare objection artifact carrying no warrant leaves the target exactly
where it was.
`check: python -c "
import tempfile, pathlib
from deepreason.harness import Harness
from deepreason.ontology import Provenance
from deepreason.views.evidence_states import EvidenceState, evidence_states
with tempfile.TemporaryDirectory() as d:
    h = Harness(pathlib.Path(d) / 'run')
    t = h.create_artifact('a conjecture', provenance=Provenance(role='seed'))
    for i in range(6):
        h.create_artifact(f'critic: objection {i}', provenance=Provenance(role='critic'))
        h.record_measure(inputs=['trial-blocked:guard', t.id])
    assert h.state.att == [], h.state.att
    assert evidence_states(h)[t.id] is EvidenceState.OPEN, 'an objection that minted no warrant moved the target'
"`

**THE COMPLETENESS RULE: an absence is evidence only when a pass that ran in
full says so.** Without a declaration, and under any declaration that is not
`complete`, an un-attacked artifact stays OPEN. A `complete` declaration
licenses only the targets it NAMES — a pass that ran in full says nothing about
a conjecture it never looked at.
`check: python -c "
import tempfile, pathlib
from deepreason.harness import Harness
from deepreason.ontology import Provenance
from deepreason.runtime.criticism_dispatch import (
    OUTCOME_COMPLETE, OUTCOME_CUT_BUDGET, declare_criticism_dispatch)
from deepreason.views.evidence_states import EvidenceState, evidence_states
with tempfile.TemporaryDirectory() as d:
    h = Harness(pathlib.Path(d) / 'run')
    a = h.create_artifact('looked at', provenance=Provenance(role='seed'))
    b = h.create_artifact('never visited', provenance=Provenance(role='seed'))
    assert evidence_states(h)[a.id] is EvidenceState.OPEN
    declare_criticism_dispatch(h, cycle=0, outcome=OUTCOME_CUT_BUDGET,
                               planned=2, dispatched=1, targets=[a.id])
    assert evidence_states(h)[a.id] is EvidenceState.OPEN, 'a cut pass licensed an absence'
    declare_criticism_dispatch(h, cycle=1, outcome=OUTCOME_COMPLETE,
                               planned=1, dispatched=1, targets=[a.id])
    assert evidence_states(h)[a.id] is EvidenceState.SUPPORTED
    assert evidence_states(h)[b.id] is EvidenceState.OPEN, 'the licence leaked past its targets'
"`

**The outcome vocabulary is CLOSED, and only `complete` licenses anything.** A
future road that ends a criticism pass some other way has to add a member; it
may not inherit `complete` by silence, which would license an absence nobody
measured. The writer refuses an outcome outside the set before it reaches the
record.
`check: python -c "
from deepreason.runtime.criticism_dispatch import OUTCOMES, OUTCOME_COMPLETE
assert set(OUTCOMES) == {'complete','cut:budget','cut:seat','cut:call','cut:foreign'}, OUTCOMES
assert OUTCOME_COMPLETE == 'complete'
import tempfile, pathlib
from deepreason.harness import Harness
from deepreason.runtime.criticism_dispatch import declare_criticism_dispatch
with tempfile.TemporaryDirectory() as d:
    h = Harness(pathlib.Path(d) / 'run')
    try:
        declare_criticism_dispatch(h, cycle=0, outcome='ran_fine', planned=1, dispatched=1)
    except ValueError:
        pass
    else:
        raise AssertionError('an unknown outcome reached the record')
"`

**The reading decides nothing, and no deciding package may name it.** The law
line has an EMPTY permitted-exception list, and it is pinned twice: by spelling
over `scheduler/`, `adjudication/` and `rules/`, and behaviourally — computing
the reading appends no event and moves no status label.
`check: python -c "
import pathlib
FORBIDDEN = ('deepreason.views.evidence_states','evidence_states','evidence_state_summary','EvidenceState','frontier_column')
packages = [pathlib.Path('src/deepreason/scheduler'), pathlib.Path('src/deepreason/adjudication'), pathlib.Path('src/deepreason/rules')]
seen = 0
for package in packages:
    files = list(package.rglob('*.py'))
    assert files, package
    seen += len(files)
    for path in files:
        text = path.read_text()
        assert not [n for n in FORBIDDEN if n in text], (str(path), [n for n in FORBIDDEN if n in text])
assert seen > 5, seen
" && python -m pytest tests/test_evidence_states_law_line.py -q`

**The declaration rides the existing notice channel.** It is a Measure event
with no outputs, like the seat-retirement and trial signals, so no new record
object kind exists and `DR-INV-frozen-surfaces` surface 2 is untouched. It is
declared in the signal registry per `DR-REC-add-signal`, with a real unit and
staleness rather than the migration marker.
`check: python -c "
from deepreason.signals import SIGNAL_DECLARATIONS
from deepreason.runtime.criticism_dispatch import CRITICISM_DISPATCH_SIGNAL
d = SIGNAL_DECLARATIONS[CRITICISM_DISPATCH_SIGNAL]
assert d.unit != 'unspecified' and d.staleness != 'unspecified', (d.unit, d.staleness)
assert 'scheduler' not in d.semantics, 'the declaration names its producer'
" && python -m pytest tests/test_criticism_dispatch_declaration.py::test_the_declaration_adds_no_record_object_kind -q`

**A record that predates the declaration says so.** Every committed root does.
The reading over one names the absence in the operator's own words and reads no
artifact as SUPPORTED merely because nothing attacked it — while still reading
SUPPORTED where the record carries a real survival, because an attacker the
graph itself refuted is positive evidence that needs no declaration.
`check: python -c "
import pathlib
from deepreason.harness import Harness
from deepreason.views.evidence_states import evidence_state_summary
blind = Harness(pathlib.Path('experiments/live_tri_2026-07-27/run-6dab80d615a437a8b3fa489a279df847'), read_only=True)
s = evidence_state_summary(blind)
assert s['completeness']['absent'] is True
assert s['completeness']['reason'] == 'NO_CRITICISM_DISPATCH_DECLARATION'
assert s['counts']['supported'] == 0, s['counts']
pa2 = Harness(pathlib.Path('experiments/2026-09-02-live-p-a2-corrected/run'), read_only=True)
c = evidence_state_summary(pa2)['counts']
assert c['open'] > 0 and c['supported'] > 0 and c['refuted'] > 0, c
"`

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| What separates a survivor from an untested conjecture | `evidence_states`'s four branches in `views/evidence_states.py` | `tests/test_evidence_states.py` |
| What counts as a warranted attack | NOT here: `DR-CON-warrants-and-attacks` owns the chain, and this reading only consumes `state.att` and `state.status` | `tests/test_adjudication.py` |
| What licenses reading an absence as evidence | the CLOSED vocabulary in `runtime/criticism_dispatch.py`, and the exits that emit it in `_arg_crit` / `_foreign_arg_crit` | `tests/test_criticism_dispatch_declaration.py` |
| Which packages may not name the reading | `DECIDING_PACKAGES` in `tests/test_evidence_states_law_line.py`; `PERMITTED` is empty and emptiness is the claim | `tests/test_evidence_states_law_line.py` |
| How the reading is shown to a reader | `application/results.py`, `application/stop_report.py` (`DR-SUB-application`) | `tests/test_results_command.py`, `tests/test_stop_report.py` |
| How an artifact is attributed to a cycle | `_walk`'s heartbeat tracking; the `pre-cycle` bucket is deliberate, not a fallback | `tests/test_evidence_states.py::test_per_cycle_buckets_artifacts_by_the_heartbeat_that_preceded_them` |

## Traps

**The blind-critic saturation (2026-09-04).** The first instinct is to read
"this artifact was criticised" off the fact that a critic call named it. The
bench that measured critic behaviour found the critic attacked 240 of 240
targets it was shown, including the sound ones — so that reading would have
called every artifact in every run a survivor. The design consequence is the
warrant requirement above, and it is the reason CONTESTED includes an
ensemble-split trial: a split is the one guard outcome that is itself evidence
both ways rather than a trial that never ran.

**The named fixture that did not exist (2026-09-04).** The tranche's own
authorization named "the blind-critic roots" as the canonical OPEN case. That
experiment committed no run root — it is a bench over direct provider calls,
which is precisely why its 480 attacks carry zero warrants: no harness was there
to register one. The canonical OPEN case therefore comes from
`experiments/live_tri_2026-07-27/run-6dab80d615a437a8b3fa489a279df847`, whose
criticism ran 11 times and produced no attack at all, and which
`tests/test_adjudication_blindness.py` already pins for that shape. Verify a
named fixture reaches the code before adopting it.

**The signal the registry gate cannot see (2026-09-04).**
`tests/test_signals.py` AST-scans for LITERAL heads at `record_measure` call
sites, so a signal emitted through a named constant — this one, and
`seat.retired.v1` — is invisible to it and can ship undeclared with the gate
green. This signal is declared anyway and pinned by
`tests/test_criticism_dispatch_declaration.py::test_the_signal_is_declared_in_the_registry`;
the general hole is parked at
`experiments/2026-09-04-change-evidence-states/PARKED.md` P1.

**The foreign road licenses nothing, on purpose (2026-09-04).**
`_foreign_arg_crit` declares `cut:foreign` at entry and never `complete`,
because manifest-owned criticism counts coverage by foreign school identity in
its own receipts — a different question from "was every planned call made".
A run using foreign criticism therefore gets no SUPPORTED reading from an
absence. That is the conservative failure and it is the right one; deriving a
real declaration from the coverage receipts is parked as
`experiments/2026-09-04-change-evidence-states/PARKED.md` P2.
