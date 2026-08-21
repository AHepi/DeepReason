# PARKED — Rung 3b

Noticed while scoping. Neither is fixed here: a change wished for mid-change is
parked, not implemented.

---

## P1 — `premises.py::standing_attributions` is a `Consult_L` that does not check separation

**What.** `standing_attributions` is the codebase's only existing consultation
predicate ("Consulted means unrefuted"), and it applies the MENTION law without
the SEPARATION invariant this rung ships. Definition 7.2's whole point is that
mention is necessary but not sufficient: one critic artifact that attacks both an
attribution ρ and its premise X puts them in one adjudication component, and from
there refuting that critic moves both labels together — the cascade can be
disarmed through a path the mention law does not see.

**Why parked, not fixed.** R64's subject is a consulted FRAME ASSERTION, and
LADDER §5b's A5 row assigns attributions to Rung 2 and frame assertions to Rung
4. Wiring separation into `standing_attributions` would change Rung 2's DELIVERED
cascade semantics inside a rung whose instruction is "deliberately small; do not
grow it". It is a real question about whether the premise channel wants the
stronger condition — and that question deserves its own tranche and its own
evidence, not a rider.

**Ready-to-send prompt:**

```
Change tranche: decide whether the premise channel's consultation predicate
should carry the frame-separation invariant, not only the mention law. Route
through dr-change-orchestrator.

AUTHORITY: experiments/2026-08-21-change-rung3b-frame-separation/PARKED.md P1,
and docs/POIETIC_CALCULUS_FORMALIZED.md Definition 7.2 / Theorem 7.3.

THE QUESTION: src/deepreason/premises.py::standing_attributions treats an
attribution as consulted when it is ACCEPTED. Rung 3b shipped
deepreason.calculus.separation.consultability(harness, assertion, subject),
which additionally requires Comp(rho) ∩ Comp(X) = ∅ over the undirected
att ∪ dep graph. Should standing_attributions gate on it?

WHAT MUST BE MEASURED BEFORE DECIDING — this is a measurement tranche first:
over the committed roots that exercise the premise channel, count how many
consulted attributions would BECOME unconsultable under the separation gate,
and for each, name the node that joins the components. If the answer is zero,
the change is free and the gate is a regression guard. If it is not zero, the
change silently disarms live cascades and needs the operator's words.

DO NOT change premises.py before that count exists and is pasted.

END STATE: a tranche with the census pasted, a recommendation, and either the
wired gate with its regression, or a recorded decision not to wire it with the
measurement that decided it.
```

---

## P2 — `docs/map/INDEX.md`'s concept table omits two CON documents

**What.** `docs/map/CON-standing-and-background.md` and
`docs/map/CON-problem-layer-lifecycle.md` exist and are current, but neither
appears in `INDEX.md`'s "Concepts" routing table. `INDEX.md` is the map's stated
entry point ("**`docs/map/INDEX.md` is the entry point** and routes to
everything else", CLAUDE.md), so a document it does not list is a document a
reader finds only by `ls`. Found by grep while scoping this rung:
`grep -n "standing-and-background\|problem-layer-lifecycle" docs/map/INDEX.md`
returns nothing.

**Why parked, not fixed.** Two table rows is a two-line fix, and it is still not
this tranche's — a docs defect found mid-change is parked. It also wants a
completeness check rather than two rows, which is design work: `INDEX.md`
currently has no check that would fail when a `CON-`/`SUB-` document exists and
is unlisted, which is why the gap survived two document additions.

**Ready-to-send prompt:**

```
Change tranche: make docs/map/INDEX.md's routing tables provably complete.
Route through dr-change-orchestrator.

AUTHORITY: experiments/2026-08-21-change-rung3b-frame-separation/PARKED.md P2.

FINDING: CON-standing-and-background.md and CON-problem-layer-lifecycle.md
exist in docs/map/ and are absent from INDEX.md's Concepts table. Verify with
grep -n "standing-and-background\|problem-layer-lifecycle" docs/map/INDEX.md
(expect: no output).

SCOPE: (1) add the missing rows; (2) add a check at column 0 in INDEX.md that
FAILS when any docs/map/{SUB,CON,INV,REC}-*.md file is not referenced by its
own filename stem somewhere in INDEX.md — the two rows alone leave the next
addition to fall out the same way. Run the check against the tree BEFORE the
rows are added and confirm it goes RED, then add the rows and confirm GREEN;
paste both. That mutation proof is the deliverable, not the rows.

GATE: python tools/docs_verify.py FULL, baselines per docs/AUDIT_BASELINES.md
(3 pre-existing CON-run-identity.md shallow-clone failures). No src/ change.
```
