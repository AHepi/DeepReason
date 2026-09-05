# PARKED — found while designing this programme, fixed by nobody here

Scope contract (`dr-change-orchestrator` §2): *"Anything you notice that is
broken but not requested: into `PARKED.md`. Never fix it now."* Each entry
is one line of WHAT, then a ready-to-send prompt — the follow-up should cost
the operator a paste, not an authoring session.

---

## P1 — mini's own 95 tests are outside the gate every tranche runs

**What.** `pyproject.toml:58` declares `testpaths = ["tests", "mini/tests"]`,
but the documented gate is `pytest tests/ -q -n 4` (CLAUDE.md, "Build and
test"), and an explicit path argument overrides `testpaths`. Measured:
`python -m pytest mini/tests --collect-only` -> **95 tests collected**;
`python -m pytest tests/ --collect-only` -> 5 078. So every "0 failed"
this repo has recorded for a tranche touching `mini/` was silent about 95
tests. `tools/blast_radius.py` has the same blind spot from the other side —
it greps `tests/` only, so its census for `compile_checks` and `run_checks`
reported nothing while all their consumers sit in `mini/tests/`.

**Not a defect in any code.** It is an instrument that does not cover what a
reader would assume it covers.

```
EXECUTOR WINDOW — DEFECT TRANCHE: the documented gate does not run mini's tests

Read CLAUDE.md in full, then load deepreason-orchestrator, dr-drive-harness,
dr-ask-the-right-question and pinker-write-for-readers. Start at dr-set-goal.
Work on your window's assigned branch; commit and push at every phase
boundary.

REPRODUCE FIRST, do not theorise:
  python -m pytest mini/tests --collect-only | tail -2     -> 95 tests
  python -m pytest tests/     --collect-only | tail -2     -> 5078 tests
  grep -n testpaths pyproject.toml                         -> ["tests", "mini/tests"]
and note that CLAUDE.md's own gate line passes `tests/` explicitly.

THE FORK to write into GOAL.md before reading code: either the gate command
is wrong (it should be `pytest tests/ mini/tests/ -q -n 4`, or bare `pytest
-q -n 4` so testpaths decides), or mini's suite is deliberately outside the
gate and CLAUDE.md should say so. Decide on the record.

SECOND HALF, same tranche: tools/blast_radius.py's consumer census greps
`tests/` only (see its consumers computation). A symbol whose only consumers
live in mini/tests/ censuses as having none, which is how a spec can predict
"no fixture drift" and be wrong. Whatever the gate decision is, the census
should cover the same ground the gate does.

WATCH: changing the gate command changes the passed count docs/
AUDIT_BASELINES.md records; re-baseline there in the same tranche.
FROZEN SURFACES: forecast NONE. Paste tools/blast_radius.py's own rows into
FIX.md regardless.
END STATE: one command that runs everything the repo claims to gate, its
number re-baselined, and the census covering the same paths.
```

---

## P2 — mini's manifest names a conjecturer contract its dispatch never uses

**What.** `mini/minireason/compat.py:168` binds `ContractVersionPolicyV3()`,
whose `conjecturer_turn_contract` defaults to `"conjecturer.turn.v6"`
(`run_manifest.py:674`). Mini's actual dispatch selects
`ReferenceFreeConjecturerWireContract`, contract id
`conjecturer.compact.reference_free.v1` (`compat.py:287-291`). So a mini
root's frozen manifest states one form and its `attempt_trace` records
another, for the whole life of the record.

**Why it is not being fixed here.** This programme depends on that gap
being harmless — it is exactly why a mini form registry sits outside the V6
Literals — and the measurement says it IS harmless today: a mini run with a
contract id that has never existed returns `verify_root violations: 0`
(`proof/m1_new_contract_id.txt`), because the branch that would check it
(`invariants.py:1258-1265`) sits behind `h.workflow_state.work_orders`,
which is empty for a mini root (`work_orders: 0`). Harmless is not the same
as truthful, and a manifest field that says something untrue about its own
run is a reader's trap.

```
EXECUTOR WINDOW — DEFECT TRANCHE: a mini manifest states a conjecturer
contract the run does not use

Read CLAUDE.md in full, then load deepreason-orchestrator, dr-drive-harness,
dr-ask-the-right-question and pinker-write-for-readers. Start at dr-set-goal.

THE SYMPTOM, from the record: compile a mini root and read its manifest's
control_plane_policy.contract_versions.conjecturer_turn_contract, then read
any conjecturer call's attempt_trace contract_id in the same root. They
differ: conjecturer.turn.v6 against conjecturer.compact.reference_free.v1.
experiments/2026-09-05-change-mini-isolation-programme/proof/
m1_new_contract_id.txt shows the run verifying clean regardless.

THE FORK for GOAL.md, before any code: is this a manifest that should
declare mini's real contract (a WRITER change, and the field is inside a
frozen surface, so a grant), or a field that has no meaning for engine_
profile=mini and should be recorded as such in the map (a DOCUMENT change,
no code)? Decide on the record; the cheap road may well be the right one.

FROZEN SURFACES: the field lives in run_manifest.py (surface 4) and any
change to what a manifest declares reaches qualification subjects (surface
5). Paste tools/blast_radius.py's BLAST_RADIUS_RESULT_V1 rows into FIX.md
and dispose of each BEFORE code. DESIGN AND STOP at FIX.md for the grant.

OUT OF SCOPE: the mini isolation programme
(experiments/2026-09-05-change-mini-isolation-programme/); adding any id to
ContractVersionPolicyV3.
```

---

## P3 — `SeatShellV1.form_id` is a registered field nothing reads

**What.** `grep -rn "form_id" src/ --include=*.py` returns three lines: the
field's declaration (`llm/seat_sections.py:711`) and the two shipped shells
(`llm/seat_layouts.py:116,124`). No consumer anywhere. So the shell pairs a
layout with a form declaratively while the form is still chosen at each
dispatch site — the half of the seat-is-a-shell law (CLAUDE.md, 2026-09-03)
that says a seat's OUTPUT defines it is registered but not wired.

**Partly addressed here, and only partly.** SPEC.md S6 gives the field its
first consumer for mini's three seats. The full harness's two seats keep
choosing their form at the dispatch site, because changing that reaches
`wire_contract_for`, whose answers are folded into a replay authority set
(`invariants.py`) and a qualification subject (`run_manifest.py`) — road C2,
three surfaces.

```
EXECUTOR WINDOW — CHANGE TRANCHE: let the full harness's seats resolve their
form through the shell that already names it

Read CLAUDE.md in full, including the seat-is-a-shell law (2026-09-03). Then
load dr-change-orchestrator, dr-drive-harness, dr-ask-the-right-question and
pinker-write-for-readers. Start at dr-capture-request. Base on main at or
after the merge of the mini isolation programme, whose S6 did this for
mini's three seats and is the worked example to copy.

WHAT EXISTS: SeatShellV1(seat_id, layout_id, form_id, role_prompt_
template_id) with a registry and resolution order (argument ->
DEEPREASON_SEAT_SHELL -> the seat's default). form_id has exactly one
consumer, in mini.

WHAT TO ADD: the conjecturer's and the critic's dispatch sites resolve their
form through the shell instead of naming it inline, with the shipped shells'
values chosen so the resolved form is IDENTICAL to today's for every input.
Byte-identical goldens are the acceptance test, not a nice-to-have:
tests/test_conj_pack_legacy_golden.py and tests/test_crit_pack_legacy_
golden.py.

FROZEN SURFACES: expect CONTACT. wire_contract_for's answers are folded into
a replay authority set (invariants.py) and a qualification subject
(run_manifest.py), pinned by tests/test_wire_contract_id_map.py. Paste
tools/blast_radius.py's own rows into SPEC.md and DESIGN AND STOP there for
the grant. The prior tranche priced this as road C2, three surfaces:
experiments/2026-09-03-change-conjecturer-pluggable-interface/
blast_road_c.json.

OUT OF SCOPE: adding any new contract id; the four seats parked as P5 there.
```

---

## P4 — `_walk_seat_layout` is the only road to a brief and it is private

**What.** `docs/map/INV-seat-section-plugins.md` calls it "THE ONE LEGAL WAY
a brief section is constructed", and it is named with a leading underscore in
`llm/packs.py:422`. Any consumer outside `packs.py` — mini being the first —
either reaches into a private function or gets a second renderer, and the
architecture test that is supposed to catch a bypass cannot distinguish the
two.

**Partly addressed here.** SPEC.md S6 adds `render_seat_brief` as the public
entry. What is NOT addressed is whether anything else in the tree already
reaches past it.

```
Route: dr-audit-orchestrator (dead/spec-drift dimensions), or a small
dr-change-orchestrator tranche if the census finds bypasses.
Goal: every construction of a brief section in the tree goes through the one
declared public entry, and an architecture test goes red when a new one does
not.
Evidence: docs/map/INV-seat-section-plugins.md's own "Both renderers walk a
layout" check parses only render_conj_pack and render_crit_pack;
PARKED P4 of experiments/2026-09-03-change-conjecturer-pluggable-interface/
records render_batch_crit_pack as a third renderer the shell never reaches.
End state: a census of every section-building site, and the architecture
test widened to cover all of them rather than two named functions.
```

---

## P5 — the "+56% cost, no variety" premise is not in the committed record

**What.** The window instruction for this programme states, as an
established fact, that a mini run inside a conjecture call "bought no
variety at +56% cost", and directs the reader to "the episodes evidence".
`grep -rn "56%" experiments/ docs/` returns pytest progress bars, one
budget-interruption note, and one criticism-census row — nothing measuring a
mini-inside-a-conjecture-call arm. No experiment directory matches
`*episode*`.

**Nothing is wrong with the programme's direction.** R1 says "mini needs to
be tested in isolation" in the operator's own words, and that stands without
the number. What is wrong is that a number with no instrument behind it has
started circulating as though the record carried it — the exact failure
`dr-ask-the-right-question` §1 names ("a number without its instrument is
not a fact yet").

```
Route: an ERRATA entry alone, or a five-minute record search if the measuring
tranche exists under a name the grep missed.
Goal: either cite the instrument and the tranche that measured +56%, or
record in docs/ERRATA.md that the figure has no committed source so nobody
repeats it.
Evidence: grep -rn "56%" experiments/ docs/ ; ls experiments/ | grep -i episode
End state: docs/ERRATA.md carries either the citation or the correction.
```

---

## P6 — the map covers `src/deepreason/` and says so, but nothing says where
##      `mini/` is documented

**What.** `docs/map/INDEX.md`'s coverage section states "`docs/map`
describes `src/deepreason/`", which is honest. What it does not say is that
`mini/minireason/` — 2 213 lines of engine reached by a public CLI flag —
has no document anywhere, so a reader who follows the map's own routing
table for a mini question lands nowhere and cannot tell whether they missed
a file or the file does not exist.

**Addressed by this programme, at step 12.** `SUB-minireason.md` and
`SEAM-llm-x-minireason.md` are created by T1 and T3. This entry exists so
the gap is on the record even if the programme is not approved.

```
Route: dr-change-orchestrator (documentation only), if the mini isolation
programme does not proceed.
Goal: docs/map/INDEX.md names where mini is documented, or says plainly that
it is not, so a reader can tell a gap from a miss.
Evidence: no docs/map/*.md contains "minireason" in an Owns: header;
INDEX.md's coverage section says the map describes src/deepreason/.
End state: INDEX.md's coverage section names mini/ explicitly, and either
routes to SUB-minireason.md or records its absence as a known gap.
```
