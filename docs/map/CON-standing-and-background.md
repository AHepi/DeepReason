<!-- DR-CON-standing-and-background -->
Verified-at: 5deec374
Verify: python -m pytest tests/test_calculus_vocabulary.py -q
Owns: src/deepreason/status_display.py
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

This document exists ahead of the mechanism. The standing axis arrives at Rung 4
of the v2 calculus program
(`experiments/2026-08-14-change-calculus-reconciliation-v2/LADDER.md`); what
exists today is the **vocabulary groundwork** that had to precede it, because
the word "standing" was already taken three times over.

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

None that persists. Standing will be a DERIVED view (calculus C4: computed,
never stored), and the vocabulary mapping this module owns is pure rendering.

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
`DR-SUB-calculus` (`calculus/separation.py`, Rung 3b); Rung 4 wires the
consultation site and may then invoke Theorem 7.3 rather than re-argue it.

`check: python -c "from deepreason.calculus import consultability, frame_separated" && python -m pytest tests/test_calculus_frame_separation.py -q`

Prop 12.5 of the calculus (standing never adjudicates) is the invariant the
mechanism will have to prove when it lands: label computation reads `att` and
`dep` only, and standing is consumed by render and schedule alone.

## Where to change what

| To do this | Edit | Test |
|---|---|---|
| change how a status reads to a human | `status_display.py::display_status` | `tests/test_calculus_vocabulary.py` |
| add or reword a gloss | `status_display.py::_GLOSS` | `tests/test_calculus_vocabulary.py::test_every_status_has_a_gloss` |
| render a status in a new view | call `display_status`, never `status.value` | `tests/test_calculus_vocabulary.py::test_views_render_the_calculus_vocabulary` |
| add the standing axis itself | Rung 4 — not here yet | — |
| change what separates a frame from its subject | `calculus/separation.py::frame_separated` (`DR-SUB-calculus`) | `tests/test_calculus_frame_separation.py` |

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
  compatibility decision rather than vocabulary work. It is parked to Rung 4,
  where the collision becomes real. Until then, a reader meeting "standing" in
  the scheduler should read it as "still standing", not as frame role.
`check: ! grep -q '"standing"' src/deepreason/status_display.py`
`check: ! grep -q "_under_standing_attack" src/deepreason/controller.py`
`check: grep -q "_standing_recrit_pool" src/deepreason/scheduler/scheduler.py`
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
