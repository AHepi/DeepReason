<!-- DR-CON-standing-and-background -->
Verified-at: e3a6cadf5
Verify: python -m pytest tests/test_calculus_vocabulary.py -q
Owns: src/deepreason/status_display.py, src/deepreason/calculus/standing.py
Seams: 
Seams-undocumented: application x standing-and-background, scheduler x standing-and-background

# Standing and background — the second axis, and the vocabulary it needs

## What it is

Two different questions can be asked about an artifact, and the harness today
answers only one. **Status** is truth-standing under criticism: is every attack
on it defeated? **Standing** is its role in the economy of generation: is it one
node among the retrieved neighbours, or is it the coordinate system every
conjecture in a scope is written in? An artifact can be refuted and still
framing — that is the ordinary condition of mature science, and a single-axis
system cannot represent it.

**The mechanism landed 2026-08-22 (Rung 4).** This document used to say "exists
ahead of the mechanism"; what remains true of that sentence is only the
vocabulary half — the word "standing" was already taken three times over, which
is why the groundwork had to precede the axis.

`standing(b)` now exists, in `DR-SUB-calculus` (`calculus/standing.py`), as
Def 9.3's DERIVED relation: b is background over sigma exactly when some
consulted frame assertion has b as its subject. Nothing is stored. The four
conditions for "consulted" are Def 9.2's — recognised as a frame assertion,
addressed to a promotion problem, `final(fa) = unrefuted`, and separated from
its subject (Def 7.2, via Rung 3b's own predicate).

`check: python -c "from deepreason.calculus import standing_of, standing_view, consultability_of, frames" && python -m pytest tests/test_calculus_standing.py -q`

## Why one axis cannot carry it

The argument is Proposition 9.1 of `docs/COMPUTABLE_CALCULUS.md` (the rigidity
dilemma), and it is the reason this is a concept document rather than a
preference. Suppose frame role were a function of status, so that an accepted
violation of a framework's commitments removed its framing role. Then either

1. framing toggles with the adjudication of each contested observation — and
   since observation-acceptance is revisable, framing over the scope oscillates
   with every attack and reinstatement of the evidence, re-orienting every open
   problem in scope at each toggle; or
2. the system prevents the toggle by delaying, suppressing, or immunising —
   which abandons criticism as the sole selector, theory-ladenness, or
   fallibilism respectively.

The alternatives are exhaustive. So the axes are separated, and they are
separated by EDGE ROLE rather than by a new node type: a frame assertion
*mentions* its subject and *depends on* its reach case, so a wound to the
subject cannot drag the frame down (Law 9.4), and refuting the case cuts the
frame's support. Both axes stay inside `att`/`dep`.

## State it owns

**None that persists**, and the mechanism did not change that. Standing IS a
derived view (calculus C4: computed, never stored) — no field was added to
`Problem`, `EpistemicState` or `Event`, and no relation table was introduced.
The vocabulary mapping `status_display.py` owns remains pure rendering.

`check: python -m pytest tests/test_calculus_standing.py::test_no_field_was_added_to_problem_state_or_event tests/test_calculus_standing.py::test_standing_is_recomputed_from_the_log_and_never_stored -q`

## The two vocabularies

The stored vocabulary and the rendered vocabulary are different on purpose.

| stored (frozen; in every committed root) | rendered to a reader | gloss |
|---|---|---|
| `accepted` | `unrefuted` | every attack so far is defeated — survival, not endorsement |
| `refuted` | `refuted` | a warranted attack stands |
| `suspended` | `suspended` | under unresolved attack |
| `suspended_unsupported` | `suspended_unsupported` | orphaned, not false — it lost its ground, it was not shown wrong |

The rule that decides every case: **a string written into a root stays
`accepted`; a string rendered to a reader says `unrefuted`.** Machine JSON keeps
the stored label — `positions.accepted` is compared across roots and spec v1.7
§E names it explicitly.

`check: python -c "from deepreason.ontology import Status; assert Status.ACCEPTED.value == 'accepted'"`
`check: python -c "from deepreason.ontology import Status; from deepreason.status_display import display_status; assert display_status(Status.ACCEPTED, 'text') == display_status(Status.ACCEPTED, 'formal') == 'unrefuted'"`

The calculus names the label `unrefuted` deliberately (§6): "membership in the
grounded extension means every attack on the node is currently defeated —
survival under the criticism so far supplied, nothing stronger. The calculus has
no stronger word to offer and refuses to imply one." The harness has recorded
evidence that the weaker word misleads: `adjudication-blindness`
(`verification/report.py`, spec v1.7 §E) exists because readers of
`positions.accepted` were treating acceptance as adjudicated.

## Entry points

`display_status(status, workload_profile=None, authority_policy=None)` — the one
seam. `status_gloss(status)` — the plain-language meaning, for surfaces with
room for it. `display_status_counts(harness, ...)` — the counts that reach
`progress.jsonl` and the text-run result projection.

Every status-rendering view routes through the seam rather than printing the
enum value.

`check: for f in why theory evidence export; do grep -q "from deepreason.status_display import" src/deepreason/views/$f.py || exit 1; done`

## Invariants

`DR-INV-frozen-surfaces` — this module contacts none of the five surfaces. It
renders; it never writes a stored label, an event payload, or a machine key.

**Frame-separation (Definition 7.2)** is the invariant the mechanism must be
BUILT against rather than prove afterwards, and it exists already: the axes are
separated by EDGE ROLE, but edge role alone does not separate the adjudication
COMPONENTS, and a frame sharing a component with its subject loses exactly the
wound persistence this axis is for. The predicate and its enforcement live in
`DR-SUB-calculus` (`calculus/separation.py`, Rung 3b), and **Rung 4 wired the
consultation site on 2026-08-22**: `standing.py::consultability_of` CALLS
`separation.consultability` and returns its `FRAME_NOT_SEPARATED` code
unchanged, so Theorem 7.3 is invoked rather than re-argued. A consulted
assertion sharing an adjudication component with its subject is UNCONSULTABLE
and moves no edge, no warrant and no label.

`check: python -c "from deepreason.calculus import consultability, frame_separated" && python -m pytest tests/test_calculus_frame_separation.py tests/test_calculus_frame_assertions.py::test_an_unseparated_assertion_is_unconsultable_with_rung3bs_own_code tests/test_calculus_frame_assertions.py::test_an_unconsultable_assertion_moves_no_edge_no_warrant_no_label -q`

**Prop 12.5 (standing never adjudicates) — PROVED at Rung 4**, in the strongest
form the tranche instruction asked for: two runs over the same graph, one
carrying frame assertions and one carrying none, produce IDENTICAL labels. The
subject is REFUTED in both roots deliberately — an earlier version framed an
accepted subject and a mutation leaking standing into `compute_label0` passed
it, because the subject was already accepted. "Refuted and still framing" is
both the interesting case and the only one with anything to catch.

Two structural companions guard what the behavioural test cannot: `_adjudicate`
names no standing symbol, and nothing in `adjudication/` imports the view.

`check: python -m pytest tests/test_calculus_standing.py::test_frame_assertions_do_not_move_a_single_label tests/test_calculus_standing.py::test_label_computation_names_no_standing_symbol tests/test_calculus_standing.py::test_no_adjudication_module_imports_the_standing_view -q`

**Prop 12.4 (axis independence) — PROVED at Rung 4, both directions.** Status
moves without standing moving (refute the SUBJECT: it only MENTIONS b, so pass
two never reaches the assertion). Standing moves without status moving (attack
the REACH CASE: the assertion loses support, falls to
`suspended_unsupported`, and stops being consulted, while b's own label is
untouched). One direction alone proves nothing — it passes under coupling in
the other.

`check: python -m pytest tests/test_calculus_standing.py::test_status_changes_without_standing_changing tests/test_calculus_standing.py::test_standing_changes_without_status_changing -q`

## Where to change what

| To do this | Edit | Test |
|---|---|---|
| change how a status reads to a human | `status_display.py::display_status` | `tests/test_calculus_vocabulary.py` |
| add or reword a gloss | `status_display.py::_GLOSS` | `tests/test_calculus_vocabulary.py::test_every_status_has_a_gloss` |
| render a status in a new view | call `display_status`, never `status.value` | `tests/test_calculus_vocabulary.py::test_views_render_the_calculus_vocabulary` |
| add a scope-predicate operation | `calculus/scope.py::OPS` (`DR-SUB-calculus`) | `tests/test_calculus_scope_predicate.py` |
| change what makes an assertion consulted | `calculus/standing.py::consultability_of` | `tests/test_calculus_frame_assertions.py` |
| change what the standing view shows | `calculus/standing.py::standing_view` | `tests/test_calculus_standing.py` |
| change what separates a frame from its subject | `calculus/separation.py::frame_separated` (`DR-SUB-calculus`) | `tests/test_calculus_frame_separation.py` |

## How an artifact comes to have standing at all (Rung 5)

Rung 4 gave the consult predicate; it did not say how a promotion problem comes
to exist, so in practice nothing had standing unless a test filed it by hand.
Rung 5 closes that: **reach nominates.** Reach events for one subject spanning
at least `Config.K_FRAME` distinct problem LINEAGES, over a coherent candidate
scope, spawn a promotion problem, and a frame assertion addressed to it is a
candidate answer that must survive five pinned criteria before it is consulted.

Two things this deliberately is NOT. It is not reach granting standing — reach
spawns a PROBLEM, and A8 is the axiom that says it can do nothing else. And it
is not a promotion phase: what happens on the spawned problem is the ordinary
Conj→Crit→Adj pass the scheduler already runs on every problem.

`check: python -m pytest tests/test_calculus_nomination.py::test_nomination_fires_at_the_K_frame_threshold -q`

**An unattacked assertion no longer frames by default.** This was the live hole
after Rung 4 and it was silent: accepted plus addressed-to-a-promotion-problem
was sufficient for consultation, so a claim nobody had examined became the
coordinate system for its whole scope. Remark 9.5's closure is an ORDER, not a
new rule — the criteria fire before anything consumes standing, a `fail` mints a
demonstrative warrant, and the assertion stops being unrefuted.

`check: python -m pytest tests/test_promotion_closure.py::test_an_unattacked_assertion_does_not_frame_because_its_criteria_fire_first -q`

## Traps

- **The word "standing" was already taken, three times, in three different
  senses, none of them the calculus's.** Found while scoping Rung 1 of the v2
  program (2026-08-14). (1) `status_display` rendered `accepted` as
  **`"standing"`** for text workloads — the most dangerous of the three, because
  it is what a reader of a text run actually saw. Fixed: it renders `unrefuted`.
  (2) `controller.py::_under_standing_attack` meant *under an unresolved
  attack*. Fixed: renamed `_under_unresolved_attack`. (3)
  `scheduler.py::_standing_recrit_pool` and `Config.RECRIT_STANDING` mean the
  pool of still-*standing* survivors to re-criticize. **Deliberately NOT
  renamed**: `RECRIT_STANDING` is a `Config` field name, pinned by a check in
  `DR-SUB-scheduler` and readable from profile YAML, so renaming it is a
  compatibility decision rather than vocabulary work. **The collision became REAL on 2026-08-22**, when Rung 4 gave "standing" its
  calculus meaning. The rename did NOT happen and was not supposed to: it is a
  compatibility decision, not vocabulary work, and it was not in that tranche's
  scope (`experiments/2026-08-22-change-rung4-frame-assertions/SPEC.md` A4;
  parked with its price at that tranche's PARKED.md P1). So the disambiguation
  is now the standing rule rather than a waiting period, and it has TWO senses
  to keep apart, not one:

  - `Config.RECRIT_STANDING` / `scheduler._standing_recrit_pool` mean **still
    standing** — a survivor not yet re-criticized. Nothing to do with frames.
  - `calculus/standing.py` means **frame role** (Def 9.3) — the calculus sense,
    and the only one the word carries in `DR-SUB-calculus`.

  The two never meet in code: the scheduler imports nothing from `calculus/`,
  which is also `DR-SUB-calculus`'s own NO SCHEDULER INTEGRATION row.
`check: ! grep -q '"standing"' src/deepreason/status_display.py`
`check: ! grep -q "_under_standing_attack" src/deepreason/controller.py`
`check: grep -q "_standing_recrit_pool" src/deepreason/scheduler/scheduler.py && grep -q "def standing_of" src/deepreason/calculus/standing.py && ! grep -rq "deepreason.calculus" src/deepreason/scheduler/`
- **Rendering is not the whole story: packs render to the MODEL, not to a
  reader.** Pack vocabulary was deliberately left alone by Rung 1 — changing
  what the generator is shown is a behavioural change with live-run
  consequences, and it belongs to the rung that changes pack sections. Do not
  "finish the job" by editing pack renderers without pricing that.
- **`display_status_counts` output is persisted** (`ProgressEvent.
  display_status_counts` → `progress.jsonl`, and the text-run result's
  `status_counts`). So the RENDERED vocabulary does reach a file on disk, in
  runs made from now on. That does not violate the stored-label rule — no status
  value moved — but a reader comparing progress files ACROSS roots will meet
  `standing` in older ones and `unrefuted` in newer ones. Compare stored
  statuses, never display counts, when comparing roots.
