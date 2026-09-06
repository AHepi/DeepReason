# Parked — found in this tranche, deliberately not done here

## P1 — a criticism's citations are dissolved into prose

WHAT: `llm/wire.py::CriticWireContract.compile` resolves
`cited_input_aliases` to real artifact ids and then appends them to the case
STRING (`parts.append("cites: " + ", ".join(cited))`). The structure is
discarded: the record keeps no typed trace of what a criticism pointed at,
so nothing downstream — reach, rank, audits, the map's own census — can read
it. This tranche adds a SEPARATE, essential-premise declaration and does not
touch `cited_input_aliases`; the two mean different things ("I looked at
this" vs "withdraw this and my case falls").

Ready-to-send prompt:

```
EXECUTOR WINDOW — CHANGE TRANCHE: a criticism's citations should survive as
structure, not as a sentence inside its own content

Read CLAUDE.md IN FULL. Load dr-change-orchestrator, dr-drive-harness,
dr-ask-the-right-question and pinker-write-for-readers. Start at
dr-capture-request with this message as the operator's words. Offline.

THE FACT: llm/wire.py CriticWireContract.compile resolves the critic's
cited_input_aliases into artifact ids and then folds them into the case text
as "cites: <id>, <id>". After that line the citation exists only as prose
inside the criticism's content, which is content-addressed, so nothing can
read it as a reference. Batch critic does not carry the field at all.

ONE GOAL: a criticism's citations reach the record as typed refs on the
criticism artifact's own interface (RefRole.MENTION — readable and inert;
they are NOT what the case rests on, which is the separate essential-premise
declaration delivered by
experiments/2026-09-05-criticism-premise-declaration/), and the case text
stops carrying the synthesized "cites:" sentence.

WATCH: the case string is the criticism artifact's CONTENT and therefore its
content address. Removing the "cites:" line changes ids for any run that
would have produced one — that is a FUTURE-run change, which is ordinary
work, but say so in SPEC.md and check no committed fixture pins the string.
End state: pack goldens untouched, full gate 0 failed, docs_verify 0 failed.
```

## P2 — the rest of the OIS 1.1 §4 contract additions

WHAT: `defect`, `standard`, `bearing`, `discriminator`, `merits_at_stake` on
the critic; the whole defender contract (`disposition`, `affected`,
`transport`, `reasons_given`); the recorder-case family; the `Appraise`
record kind. All out of scope here by the one-tranche-one-goal rule; the
`Appraise` kind additionally needs a frozen-surface grant (harness.py schema
map), which the source document itself flags.

Ready-to-send prompt:

```
EXECUTOR WINDOW — the operator decides which of the OIS 1.1 contract
additions to commission next.

Read docs/proposals/OIS_1_1_to_DeepReason_configuration.md §4 and §7. R1 is
DELIVERED (experiments/2026-09-05-criticism-premise-declaration/). R2's
remaining fields, R3, R4, R5, R6, R7 and R8 are unbuilt. R7 needs an
operator frozen-surface grant before any code. Ask the operator which, if
any, to commission; do not start one on your own reading.
```

## P3 — the new field gets no reference menu

WHAT: `INV-reference-menu.md` says a reference-bearing field gets a menu by
appending a `ReferenceFieldDeclaration`, and the census it cites measured
that 62.6% of handle-naming diagnostics were invented handles. The essential-
premise field delivered here is reference-bearing and has NO menu: it is
protected by the schema alias enum (an unknown handle is a failed call) but
the seat is not shown the legal list in the pack. Not done here because a
menu renders INTO the pack, and `tests/fixtures/crit_pack_legacy_v0/*.txt`
must pass untouched under this tranche's own constraint.

Ready-to-send prompt:

```
EXECUTOR WINDOW — CHANGE TRANCHE: give the critic's essential-premise field
its reference menu

Read CLAUDE.md IN FULL. Load dr-change-orchestrator and dr-drive-harness.
Read docs/map/INV-reference-menu.md FIRST, then REC-add-a-section-plugin.md.

ONE GOAL: register a ReferenceFieldDeclaration for the critic contract's
essential-premise field (handle_kind artifact_alias, omission_legal=True with
an omission entry at index 0 — an empty declaration is a complete answer and
the formalism-optional law forbids penalising it), so the seat is SHOWN the
legal set instead of inferring it.

EXPECT: the crit pack goldens (tests/fixtures/crit_pack_legacy_v0/*.txt) WILL
change — one new menu section. That is the point of the tranche; regenerate
them deliberately and say in DELIVERY.md what moved. Full gate 0 failed,
docs_verify 0 failed.
```

## P4 — an UNDECIDED essential premise still leaves its target refuted

WHAT: the OIS 1.1 audit's fixture F2
(`experiments/2026-09-05-audit-ois-1-1-spec-drift/proof/check11_da1_vs_harness.py`).
When a criticism's essential premise is not refuted but UNDECIDED — the premise
K and a rival M attack each other, so both suspend — the criticism goes
`suspended_unsupported` and its target stays `refuted`. Spec §11.3 says an
undecided essential premise should prevent its dependent from becoming in. This
is NOT the defect the 2026-09-05 criticism-premise tranche fixed: that one was a
missing producer at the mint site, this one is pass ORDER inside
`adjudication/`, which that tranche was forbidden to touch. Recorded there as a
tripwire, `tests/test_criticism_premises.py::
test_an_undecided_essential_premise_leaves_its_target_refuted_today`, which
asserts the current labels and will go red when this is fixed.

Ready-to-send prompt:

```
EXECUTOR WINDOW — DEFECT TRANCHE: an UNDECIDED essential premise does not
protect its dependent's target the way a refuted one now does

Read CLAUDE.md IN FULL. Load deepreason-orchestrator, dr-drive-harness,
dr-ask-the-right-question and pinker-write-for-readers. Start at dr-set-goal.
Offline; no key.

THE SYMPTOM, already reproduced and already committed as a test: run
  python -m pytest tests/test_criticism_premises.py -k undecided -q
It PASSES today, and what it asserts is the defect — A refuted, K suspended,
M suspended, C suspended_unsupported. Paste those four labels into GOAL.md.
The audit's own fixture is
experiments/2026-09-05-audit-ois-1-1-spec-drift/proof/check11_da1_vs_harness.py
(F2); run it and paste its table too.

THE RULE IT BREAKS: Open Inquiry 1.1 §11.3 — "an undecided essential premise
prevents its dependent from becoming in". The criticism C is correctly NOT in
(it is suspended_unsupported), but the attack it contributed still stands, so
A stays refuted. Compare F1 in the same file, which the 2026-09-05
criticism-premise tranche fixed by giving the critic a way to declare its
premise on the validity node: there the closure lifts the attack. Here the
premise is not refuted, so no closure fires.

WARNING, READ BEFORE DESIGNING: this one almost certainly IS in
src/deepreason/adjudication/ — pass order between the grounded extension and
the support cascade. That is not a frozen surface, but it is the module the
last tranche was explicitly forbidden to touch, and CON-warrants-and-attacks.md
states the current rule as law with passing checks ("refuting a premise never
refutes its dependents: pass 2 gives them SUSPENDED_UNSUPPORTED, because
orphaned is not false"). Changing how a Status is derived from edges
REINTERPRETS EVERY RECORDED ROOT — the map's own "Where to change what" table
says so. So: DESIGN AND STOP. Produce FIX.md with the pass-order change, its
blast radius, and what it does to committed roots, and STOP for the operator
before writing code. Do not implement on your own reading.

END STATE of this tranche: GOAL.md, DIAGNOSIS.md, REPRO.md, FIX.md committed
and pushed; no production code changed; the stop presented to the operator in
one sentence with priced options and a recommendation.
```
