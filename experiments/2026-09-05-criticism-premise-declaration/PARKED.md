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
