# The repair loop can oscillate forever between two invalid states

Notes for the operator. Diagnosed from `run-bc3e8797b3e0609eddb324299c8257bd`
(turmite ladder, glm-5.2, thinking off). One instance is fixed; the CLASS is
not, and the class is the part worth your attention.

## First, a correction

I initially recorded the completion-token sequence

    2735, 7151, 7150, 78, 38, 25, 67, 19, 32, 38

as the model "collapsing toward empty" under accumulating repair prompts, and
wrote that into RESULTS.md. **That was wrong.** The small responses are JSON
patches, which is exactly what `RepairPatchWireContract` requests; 19-78 tokens
is the right size for one. Nothing degraded. The raw blobs say so directly and
I should have read them before characterising the pattern.

## What actually happens

The model's `to_ref` values, in attempt order:

    attempt 1   "2469e57fb1b8d91d"   rejected: outside the SCR/NEW namespace
    attempt 2   "NEW_001"            rejected: self-link (from_ref is NEW_001)
    attempt 3   "2469e57fb1b8d91d"   rejected: namespace
    attempt 4   "NEW_001"            rejected: self-link  -> schema_exhausted

Two invalid states, alternating. The patches themselves are well formed and
correctly targeted — the model is doing exactly what it is asked, competently.

The reason it cannot escape is structural. That proposal declared exactly ONE
new block, `NEW_001`. A link's `to_ref` must be either a visible `SCR_###`
handle or a `NEW_###` key declared in the same response. With one block and no
visible scratch handles, **every possible value is invalid**: any other key is
undeclared, and the only declared key makes a self-link. The field is
unsatisfiable, and the sole correct repair is to REMOVE the link.

The model never tries that, and cannot be expected to. Each diagnostic reports
the violation of the state the document is currently in, so patching away the
violation it is told about lands it in the other one. Nothing in the repair
channel can express "no value works here; delete this element". It is not a
capability gap — the model used `remove` on `/simulation_proposals/1` in the
same run, so it knows the operation exists and when to reach for it.

## Cost

The run died at cycle 0 having already written a correct answer. The discarded
candidate says:

> CLAIM H is false. The rule string LR provides a structural refutation. Under
> the (c+1) stride, the rules {L, R} are exact inverses.

`oracle_table.txt` agrees. It also avoided the recall trap the question was
built around. All of that was thrown away over a self-referential scratch link.

## What is fixed

Self-links are now dropped deterministically at the scratch-proposal container
rather than refusing the turn. A self-link is inert — it adds no edge between
distinct blocks — so removing it cannot change what the graph says.

Two implementation notes worth keeping, because the obvious versions are wrong:

- **It cannot be a `mode="before"` validator.** The first attempt was, and it
  broke JSON-boundary coercion for the whole model: `ConjecturerTurnWireV6`
  validates via `model_validate_json`, and adding a before-validator made
  unrelated tuple fields (`new_blocks`, `unresolved_questions`) start rejecting
  JSON arrays. Eight tests caught it. It is a `mode="after"` validator on the
  container.
- **The link model can no longer RAISE.** A raise from a nested item aborts the
  whole model before any container validator runs, which is the behaviour being
  removed. The judgement stays on the link as `is_self_link`; the disposal
  lives on the container, which is the only place an element can be removed.

Ordering is checked: the drop runs before `_local_namespace_is_closed`, and a
self-link naming an undeclared key is dropped rather than becoming a route to
smuggle unknown keys past admission.

## What is NOT fixed — the class

Any repair diagnostic that is **locally satisfiable but globally
unsatisfiable** will loop until exhaustion. Self-links were one instance. The
general shape is: field F has a constraint set whose intersection is empty
given the rest of the document, and the protocol reports one member of that set
at a time.

Other places the same shape can arise, none of them investigated:

- a `premise_keys` entry that must name an EARLIER entry when no earlier entry
  of the right class exists;
- a ledger `claim_class` whose grounding channels are all bound to
  `maxItems: 0` (the satisfiability narrowing added in this tranche removes the
  advertised class, so this specific one should now be unreachable — untested
  in a live run);
- a `decisive_point_alias` when the alias table is empty.

## Two candidate fixes, neither implemented

1. **Report the whole violation set, not one member.** If the diagnostic for
   attempt 2 had said "self-link AND the only alternative is undeclared", the
   model has enough to conclude the field is unsatisfiable. This is the smaller
   change and stays inside the existing protocol.
2. **Let a diagnostic mark a pointer unsatisfiable**, so the repair prompt can
   direct a `remove` explicitly. This is a protocol change to
   `RepairDiagnosticEnvelopeV2` and a larger commitment.

A cheaper mitigation, orthogonal to both: **detect the cycle**. The repair
session already holds the attempt history; if a patch returns the document to a
value it previously held at the same pointer, that is a loop and no further
attempt at that pointer can succeed. Failing fast there would at least convert
a silent exhaustion into a typed, diagnosable outcome — and would have saved
this run's answer rather than discarding it.

I have not implemented any of the three. Pick one and I will.
