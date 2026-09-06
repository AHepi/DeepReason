# Delivered: the writer's room — limits, forms, and a census of what is ejected
Run 2026-09-06 on the operator's message 4 ("the limits need changing ...
permission to change the forms completely ... only if the commitments exist
outside conjecture artifacts"). Branch `claude/mini-isolation-t3-t5-7tsc6d`
(pushed, tree clean; head in the step-13 commit). Validation: PASS.

## What changed

**No seat loses its instruction any more.** The everything-so-far section is
budgeted as it renders, its notice names a count and three ids instead of
every id, the mandatory sections are reserved before the free one gets the
rest, and the call layer clips at the same figure the loop kept the brief
under. A flow may declare its own brief limit, and `deepreason setup`'s
model profile now reaches the reduced engine (it never did). In the live
room run every one of 27 briefs carried its instruction; in the D8 run, 9
of 19 had.

**Three room forms, registered beside the stored ones.** Conjecture
(content, optional angle), objection (about, body, optional what-would-
settle-it), proposal (about, body, optional kind). Each form's schema
states the seat's task, so the task is on the wire whatever happens to the
brief. `mini.flow.room.v1` runs them with both commitment gates off under a
12 000-character limit. Who sees what did not move.

**The condition is a test.** A conjecture artifact is its content (its id
recomputes); no conjecture carries a warrant or commitment; every proposal
and objection is its own record about an existing conjecture, written after
it. A planted write of a proposal into the conjecture space turns it red.

**The census answers the question.** Forty-six proposals, every one binding
its conjecture in its first sentence — refuted-if, forbids, must-not,
predicts — every one on target, mean 306 characters. Three pairs are
byte-identical, so the rule sealed before the run withholds its "anything
in them" on that clause; the content is quoted in full so the operator can
read it either way.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "the limits need changing" | **done** | `test_mini_brief_limits.py` (red → green); live 27/27 intact |
| R2 | "permission to change the forms completely to fit the writers room" | **done** — three room forms, stored ones kept | `test_mini_room_forms.py`; goldens 15 passed |
| R3 | "a measure of the types of contents ejected ... do the commitment artifacts actually have anything in them?" | **done** — RESULTS.md; yes with one sealed clause failing (duplicates) | census table; all 46 quoted |
| R4 | "only if the commitments exist outside conjecture artifacts" | **held and enforced** | verified on the D8 root first; `test_mini_room_separation.py` + caught mutation |
| R5 | "a writer's room, not part of the epistemology" | **honoured** | refuted 0; no authority path touched |
| R-fix | "the fix you mentioned earlier" | read as R1 | REQUEST.md |

## Assumptions the operator may override

- **The room's everything section is capped at 60 % of a 12 000-character
  limit.** Under it a seat reads the newest tenth of a three-cycle pool
  (RESULTS §6). Reading the whole pool is a flow setting (P1's prompt).
- **A profile with no candidate count asks for four.** The compact preset,
  applied to standard and frontier.
- **Optional labels ride appended to the prose** (`[kind: …]`, `[angle: …]`),
  so the record keeps one body per output.

## Map delta

changed: `SUB-minireason.md` (the limit and the reserve rule; the room forms;
the room flow; a Traps entry), `SEAM-llm-x-minireason.md` (the clip
paragraph; the P8 trap's "then it bit anyway … fixed"). new checks: 5.
Verified-at → 391d5bb31 (the full run's tree).

## Errata

errata: none.

## Parked

P1 (read the whole room: a flow setting), P2 (duplicate proposals: habit or
kinship), both with prompts in PARKED.md. The predecessor's P10 (the
reasoning field mini's transport drops) still stands; the room ran through
the same disclosed override.

**recommended next: P1**, one live run, no code: it is the cheapest way to
see whether a seat that reads the whole room repeats itself less — which is
the one thing the census found wrong with the content.
