# SPEC — the writer's room: limits, forms, and a census of what is ejected

Phase `dr-spec-change`, 2026-09-06. Authority: REQUEST.md R1–R5, R-fix.

## What the record shows (the premise, re-derived, not assumed)

D8's live root (`…/shallow-b4dcb1c81ea7af2e5ecd5faa`): 7 of 8 commitment
briefs and 2 of 3 conjecture briefs reached the model with the directive cut
off; every critic brief (~2 400 chars) kept it. Mechanism, from
`mini/minireason/`:

1. `loop.py` hands the everything-so-far section `brief_share` (0.6) of the
   prompt limit (`profile.pack_budget() * 4` = 4 800 on compact) and the
   retention rule keeps entries under that budget — but the WITHHELD notice
   it then writes lists every withheld id (65 chars each: 22 ids ≈ 1 500
   chars) and is not counted (`sources.py:366-369`).
2. The other sections (problem ~500, target ~700, directive ~300, headers)
   are not reserved; the share is a fixed fraction, not a remainder.
3. `call.py:317` clips the assembled brief with `clip_pack` from the TAIL,
   and every mini layout sorts the directive LAST. So overrun = lost
   instruction.
4. The managed shallow path never forwards the provider profile's
   `model_profile` (`provider.yaml` says `standard`; mini ran `compact`).

## Design

### S1 — the limits (R1, R-fix)

**S1a — mandatory sections are reserved; the free section gets the
remainder.** `render_mini_brief` renders the mandatory sections first, then
gives the everything-so-far section `budget_chars = limit − (rendered
mandatory chars + section headers + the notice's own worst-case size)`, never
less than a floor that shows at least the newest entry. The notice shrinks to
a COUNT plus at most the three newest withheld ids ("… and 19 more; every id
is in the record"): the ids were provenance the record already holds, and at
65 characters each they were the thing eating the budget.

**S1b — the limit is configurable and larger.** (i) The managed shallow path
forwards the provider profile's `model_profile` to mini (standard = 10 000
chars, frontier = 12 000), so `deepreason setup`'s existing field decides the
room's limit with no new knob; (ii) `MiniFlowV1` gains a FREE parameter
`brief_budget_chars: int | None` (default None = the profile's), so a flow can
declare its own; the room flow (S2) declares 12 000. The manifest keeps
binding `model_profile`, so a root stays bound to the limit it ran under.

**S1c — the clip becomes a never-fires.** The marker `mini:brief-clipped`
stays (the record must say if it ever happens), and a test drives a long
synthetic run and asserts every brief ≤ limit AND every seat's directive
byte-intact — RED today on the current allocation (the reproduction), green
after S1a. The call layer's `clip_pack` is untouched (it is `llm`'s).

### S2 — the forms, for a writer's room (R2, R5)

Three NEW forms, registered beside the stored ones (R-stored), bound by a
new flow `mini.flow.room.v1` (isolation.v1 and legacy-v0 stay):

- `mini.conjecturer.room.v1` — `{"candidates": [{"content": str, "angle": str | None}]}`;
  `angle` is an optional one-line label of the stance taken, free text.
  No typicality: the room does not estimate its own typicality.
- `mini.critic.room.v1` — `{"objections": [{"about": id, "body": str, "would_settle": str | None}]}`;
  `would_settle` optional: what observation or argument would settle the objection.
- `mini.commitment.room.v1` — `{"proposals": [{"about": id, "body": str, "kind": str | None}]}`;
  `kind` optional free text such as "refuted-if", "forbids", "must-not",
  "predicts". Never required, never validated against a list (formalism-optional).

**The seat's task travels in the form.** Each form's top-level schema
`description` states the seat's job in one sentence, so the instruction is
present even if a brief were ever cut: the schema is prepended AFTER the
clip (`call.py:318-321`) and cannot be clipped. The layout directive stays
too — belt and braces, both on the record.

Nothing in any room form carries score, rank, weight, confidence, priority,
authority or severity; the predecessor's enumeration test is extended to
the new forms. No status changes; the room flow declares both commitment
channels OFF like isolation.v1 (R5).

### S3 — R4 enforced

`mini/tests/test_mini_room_separation.py`: after a room run, every
conjecture artifact's content and digest are what its Conj event registered,
no artifact carries a warrant or commitment from a mini record, and every
proposal and objection is a record whose `about` resolves to an artifact.
Mutation-proven: a planted write of a proposal body into an artifact's
content turns it red.

### S4 — the census of what is ejected (R3)

Pre-registered in `PREREG_CENSUS.md` before the run: one live room run,
3 cycles, same standard input as D8, same provider profile (standard model
profile → 10 000-char limit; reasoning off through the predecessor's
disclosed override, P10 still parked). `census.py` reads the ROOT only:

- per seat: calls, outputs, characters (min/mean/max);
- every brief: limit, size, directive byte-intact (must be 19 of 19 — else
  S1 failed live and the tranche stops);
- per output: on-target (`about` resolves), commitment-shaped
  (refuted-if / forbids / must-not / predicts markers), duplicate (exact,
  and ≥3 shared six-word phrases with any other output), echo (shares ≥3
  six-word phrases with its own target);
- the commitment seat first, with every proposal quoted in RESULTS.md.

No verdict on quality; a census, not a judgement (R5). Recorded honestly.

## Assumptions (operator may override)

**A1** "the limits" = the brief limit of S1, not the token budget or cycle
count (message 4 follows the report that the brief clip cut the
instructions).
**A2** The room forms keep `about` as an id: the record needs it to say what
a proposal is about; it is the one required field besides the body.
**A3** The everything-so-far section stays in the conjecturer's and the
commitment seat's briefs and stays out of the critic's (R5 of the
predecessor); S2 changes forms, not who sees what.

## Frozen surfaces — forecast

CLEAR. Files: `mini/minireason/{sources,seats,forms,flow,loop}.py`,
`src/deepreason/shallow.py` (not frozen), tests under `mini/tests/` and
`tests/test_shallow_reason.py`. `blast_radius` at every [COMMIT].

## Budget

Code ~260 lines, tests ~220, docs ~120, scripts ~150. Lower bounds (P7 of
the predecessor); overrun disclosed, not absorbed.
