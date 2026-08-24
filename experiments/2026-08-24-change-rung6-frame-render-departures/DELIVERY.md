# DELIVERED — Rung 6: frame render semantics and the departure protocol

VALIDATION.md verdict: **PASS**. `claude/frame-render-departure-protocol-u4dnn7` (pushed, tree clean).
Base: `origin/main` at `7ad1b273f`. Tranche:
`experiments/2026-08-24-change-rung6-frame-render-departures/`.

## What changed

Before this tranche a consulted frame was invisible to the models working
inside it. Rung 4 built the frame assertion, Rung 5 made promotion problems
exist so that anything could be consulted at all — but the packs that
generation and criticism actually receive said nothing about the coordinate
system the problem was posed in, and nothing about the open indictments
against it. A frame therefore arrived as settled by default, which is the
one presentation §9.5 exists to abolish.

Three mechanisms close that, and the interesting thing about all three is
that **none of them relies on the model complying with an instruction**.

**The frame slice.** For every consulted assertion whose σ admits the
problem, the pack carries two sections: `frame-crisis` — the subject's
standing attackers plus the departure directive, rendered EXACT — and
`frame-slice` — the subject's articulation digest, compressed and expandable
through `deepreason standing --json`. The crisis sorts first. Both are
NON-DROPPABLE, which is the mechanism rather than the position: a dropped
section leaves no header and no placeholder, so a frame whose wounds the
budget cut would be byte-indistinguishable from a frame with none.

**The departure protocol.** A departure is declared as an ordinary artifact
carrying `poietic.departure-declaration.v1` — subject, departing artifact,
the subject's commitment ids broken with, and a rationale. Declaring
subtracts those ids from what the candidate still implicitly holds, and the
subtraction is done by the harness from the record
(`held_frame_obligations`), not claimed in a reply. Nothing scores a
departure, and the guarantee is structural: the compiler gives the body two
MENTIONS and no dependence, so neither adjudication pass has an edge through
which a declaration could move a label.

**Three exit grades, not two.** `FrameDecisive` is not adopted. `fall`
(`R`), `revocation` (`SU`) and `contestation` (`S`) are each reachable by
their own registration, and the render distinguishes all three with what
each MEANS rather than only its name.

Alongside them, P4's render half: the section allocation that decides
whether an inherited-context problem can cite anything now SAYS what it
decided, instead of producing a pack that silently lists no ids.

New file: `calculus/render.py`. `claims.py`, `compiler.py`, `programs.py`
and `operations.py` gain the departure body and its producer; `llm/packs.py`
gains two sections and the drop-disclosure loop; `rules/conj.py` and
`rules/crit.py` supply the slice at all three call sites; `standing.py` and
the CLI gain the exit grades. New map document:
`DR-SEAM-calculus-x-rules`.

## Reconciliation, requirement by requirement

| R | The operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "the pack carries the subject's articulation digest … AND the subject's standing attackers — wounds render in-frame, in every pack in scope" | **DONE** | VALIDATION §1; `test_a_consulted_frame_renders_its_digest_and_its_standing_attackers`, and a census showing all THREE `render_*_pack` call sites supply it |
| R2 | "the slice carries the standing directive that departures are permitted and must be declared as a list of broken assumption/commitment ids" | **DONE** | `test_the_slice_carries_the_departure_directive_and_the_protocol` |
| R3 | "Declaration removes the hidden-premise criticism's target; the declaration is itself attackable" | **DONE** | `test_declaring_a_departure_removes_the_held_obligation`, `test_a_departure_declaration_is_itself_attackable` |
| R4 | "NOTHING scores departures" | **DONE**, structurally | two mentions, no dependence — mutation-proven (VALIDATION §3) |
| R5 | "scope predicates NEVER read departure declarations" | **DONE**, structurally | σ's evaluation domain is five `Problem` fields; there is no leaf to add |
| R6 | "P4's RENDER HALF: the same deterministic section allocation settles what an inherited-context problem may cite" | **DONE** | `DISCLOSED_ON_DROP` + the fixed-point notice; `test_a_dropped_citable_legend_is_disclosed_in_the_pack` |
| R6 | "P4b (quote wording) stays parked — do not absorb it" | **HONOURED** | PARKED.md carries it with a ready-to-send prompt; not touched |
| R7 | "do NOT adopt FrameDecisive … The render distinguishes all three and never rounds contestation to either neighbour" | **DONE** | three grades from three graphs; two anti-`FrameDecisive` mutations both RED |
| R8 | (Amendment 1) "continue and disclose" | **DONE** | VALIDATION §5; the ceiling stands unre-baselined |
| N1 | "provenance-shaped fields are ABSENT … A check pins that the renderer emits no empty provenance slots" | **DONE** | `test_the_frame_slice_emits_no_provenance_shaped_slot`, and an absent frame renders NOTHING rather than a "no frame" notice |
| N2 | "persistence is asserted AT THE TERMINAL step, never at injection" | **DONE** | eight cycles, wound at 2, question at 8, against the real pack at a budget measured to bite |
| N3 | "where a frame obligation can be a deterministic gate the pack must pass, build the gate; render position is a hedge, recorded as such" | **DONE** | two gates (non-droppable sections; record-side subtraction), and the position recorded as a hedge in `DR-CON-packs-and-token-economy` |

## The instruments

| Instrument | Result |
|---|---|
| `python -m pytest tests/ -q -n 4` | **3976 passed, 6 skipped, 0 failed** (base 3939 + 6; +37 is this tranche's own test file) |
| `python tools/docs_verify.py` (FULL) | **3 failed** — all three the pre-existing `CON-run-identity` shallow-clone failures, unchanged from the base |
| `tools/blast_radius.py` | `"frozen_surface_verdict": "CLEAR"` |
| `python scripts/wheel_smoke.py` | PASS, pins unchanged |
| `python -u scripts/wheel_operational_smoke.py` | PASS — 80 qualification calls, the number that would have moved had a new LLM role been added |

## Frozen surfaces

**All five at ZERO, measured.** `tools/blast_radius.py` returns
`"frozen_surface_verdict": "CLEAR"`. No new LLM role, so surface 5 never
came into question and the STOP-and-ask condition was never triggered; no
new `Config` field, so surface 4 owes no versioned-source line; and
SPEC.md's constraint F1 kept `consulted()` and `StandingGrant` untouched
because `invariants.py` reads them.

## Public surface

**No `frame`/`pack` inspection view shipped**, so the wheel-smoke pins are
not owed and none moved — `git diff -- scripts/` is empty. The richer
standing view rides the existing `deepreason standing --json` and MCP
`run_standing`; the pinned sha is over `tools/list`, so a richer result
moves nothing. Both smokes run green anyway, as proof rather than
assurance.

## Size, disclosed rather than re-baselined (R8)

`src/` grew **810** lines against SPEC.md's ledgered ceiling of **560**. The
per-file breakdown and the three causes are in VALIDATION §5. Two of the
three were forced by measurement — a failing test split one section into
two, and a call-site census found a third caller SPEC.md did not know about
— and the third is documentation density under the repo's own convention.
The overrun was raised at the step-9 checkpoint, priced against two
alternatives, and the operator ruled *continue and disclose*.

## Residue — what this did NOT prove

Seven items in VALIDATION §8. The three worth reading before building on
this:

- **What persists past the attacker cap is the CRISIS, not any particular
  attacker.** Beyond `FRAME_SLICE_ATTACKERS_N`, an early wound can be
  displaced by later ones whose ids sort lower. It is disclosed by the
  count, never silent, and the limit is a committed test rather than a
  caveat in prose.
- **No live run.** Whether a real provider model ACTS on the departure
  directive is untested, and per Q1 should not be assumed. That is exactly
  why the load-bearing parts are the allocator flags and the record-side
  subtraction rather than the directive's wording.
- **One defect shipped and was caught by review, not by the gate.**
  `declared_departures` overwrote instead of unioning, so a candidate that
  departed on two counts silently un-declared one. Fixed and pinned — but
  every test in the file filed one declaration per candidate, so the suite
  as written would not have found it. Do not read this file's coverage as
  exhaustive.

## The two closing lines the operator asked for

**What a pack now shows about a consulted frame that it did not before:**
the frame's own open indictments — every standing attacker of the subject,
in-frame, in every pack in its scope, in a section the budget cannot
silently cut — together with the articulation the frame asserts, the
commitment ids a candidate may declare it breaks with, and what has already
been declared against it.

**The three ways a frame can leave standing, none rounded away:** it can
FALL, defeated on its own merits (`refuted`); its accreditation can be
REVOKED when the reach records it rests on stop being unrefuted
(`suspended_unsupported`) — unearned rather than wrong; or it can stand in
CONTESTATION, attacked and undecided, where nobody has won yet
(`suspended`). The third is the one the two-exit claim assumed away, and
the render never lets it be read as either of its neighbours.
