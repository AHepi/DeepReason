# Request: implement the research note's "robust across models" attention-layout list, and nothing more

Captured: 2026-08-28, from the operator's approval of the monitor's staged plan
and the tranche instruction that carries it.

## Verbatim

Operator, 2026-08-28, approving the monitor's staged plan:

> Ok. Do it.

Operator, same exchange, verbatim:

> tokens are cheap. You are not. So any experiments with token spend that can
> settle things is preferred.

The tranche instruction (the monitor's staged plan the operator approved),
verbatim in the parts that bind this work:

> Design input: docs/RESEARCH_ATTENTION_LAYOUT_2026-08-28.md — read IN FULL.
> It is an external research note, NEVER evidence; its authority here is that
> the operator approved a tranche implementing exactly its
> "robust across models" list and nothing more. Scope from docs/map/INDEX.md
> (read the covering SEAM documents before the subsystems; the render/pack/
> scratch surface is the subject).

> SCOPE — the robust rules only. Numbered requirements, each with its proof:

> R1 (artifact) CENSUS FIRST: how the harness renders prompts today, against
> the four robust rules. For each seat's rendered prompt: (a) does any
> load-bearing material sit AFTER the question/task statement; (b) how many
> standing instructions does one rendered prompt carry (the research note's
> ceiling is ~40, hard floor 80); (c) is prior-round material carried verbatim
> or distilled, and is full text retrievable by reference (the reference-menu
> pattern is the repo's existing shape for this); (d) block structure — many
> small delimiter-bounded blocks or few large ones. Proof: a table with
> file:line for the renderer code paths AND at least one real rendered prompt
> reconstructed from a committed root's render receipts (handle maps reload
> key-sorted; compare by ordered_refs, never .values()). If the census finds
> the harness ALREADY satisfies a rule, that requirement closes as
> already-met — do not churn code to re-implement what exists.

> R2 (behavior): implement the census's gaps, robust rules only:
> - Nothing load-bearing rendered after the question.
> - Standing-instruction count per rendered prompt at or under ~40; if a seat
>   exceeds it, restructure (split across turns or move to reference), never
>   silently delete semantics — any dropped instruction is a disclosed
>   decision in SPEC.md.
> - Superseded prior-round conjectures carried as one-line distilled
>   summaries with the full text retrievable by reference; LIVE conjectures
>   and binding refutations verbatim, placed late (near the question).
> - Prefer fewer, larger rendered blocks over many small ones.
> Per the modularity law: the layout policy ships as configuration or a
> versioned artifact, not hard-coded arrangement — with an architecture test
> that fails if a consumer bypasses it.

> R3 (artifact): the model-specific items in the research note's §(b) —
> which pre-question slot, rendering format, retrieval depth — are NOT
> implemented on the papers' word. Produce instead ONE parked, ready-to-send
> calibration-experiment prompt (cheap live API sweep on the bench model)
> that would settle them locally. Park it; do not run it.

> R4 (process): regression tests for every behavior change, mutation-proven
> (shown RED against the old behavior, GREEN against the new, output
> committed). The map moves in the same commits as the code.

## Requirements

R1 (artifact): "CENSUS FIRST: how the harness renders prompts today, against
the four robust rules." Four sub-obligations, each answered per seat:
- R1a: "does any load-bearing material sit AFTER the question/task statement"
- R1b: "how many standing instructions does one rendered prompt carry (the
  research note's ceiling is ~40, hard floor 80)"
- R1c: "is prior-round material carried verbatim or distilled, and is full
  text retrievable by reference"
- R1d: "block structure — many small delimiter-bounded blocks or few large
  ones"
Proof obligation, verbatim: "a table with file:line for the renderer code
paths AND at least one real rendered prompt reconstructed from a committed
root's render receipts (handle maps reload key-sorted; compare by
ordered_refs, never .values())."
Closure rule, verbatim: "If the census finds the harness ALREADY satisfies a
rule, that requirement closes as already-met — do not churn code to
re-implement what exists."

R2 (behavior): "implement the census's gaps, robust rules only". Four rules:
- R2a: "Nothing load-bearing rendered after the question."
- R2b: "Standing-instruction count per rendered prompt at or under ~40; if a
  seat exceeds it, restructure (split across turns or move to reference),
  never silently delete semantics — any dropped instruction is a disclosed
  decision in SPEC.md."
- R2c: "Superseded prior-round conjectures carried as one-line distilled
  summaries with the full text retrievable by reference; LIVE conjectures
  and binding refutations verbatim, placed late (near the question)."
- R2d: "Prefer fewer, larger rendered blocks over many small ones."
- R2e: "Per the modularity law: the layout policy ships as configuration or a
  versioned artifact, not hard-coded arrangement — with an architecture test
  that fails if a consumer bypasses it."

R3 (artifact): "the model-specific items in the research note's §(b) — which
pre-question slot, rendering format, retrieval depth — are NOT implemented on
the papers' word. Produce instead ONE parked, ready-to-send
calibration-experiment prompt (cheap live API sweep on the bench model) that
would settle them locally. Park it; do not run it."

R4 (process): "regression tests for every behavior change, mutation-proven
(shown RED against the old behavior, GREEN against the new, output
committed). The map moves in the same commits as the code."

## Standing constraints

C1: "the robust rules only" / "implementing exactly its 'robust across
models' list and nothing more" — the tranche instruction, SCOPE. Anything in
the research note's §(b) or §(c) is out of scope for code.

C2: "It is an external research note, NEVER evidence" — the tranche
instruction, Design input. The note may motivate a change; it may not be
cited as proof that the change works.

C3: "FROZEN-SURFACE FORECAST: none expected — this tranche's cone is the
render/pack/scratch surface, tests, and map. HOWEVER: if any change turns
out to move a qualification subject digest or any committed digest pin,
STOP and report to the operator before proceeding. No exception is
pre-granted in this tranche." — the tranche instruction.

C4: "Do not write in either directory, do not touch the branch
claude/spec-to-code-technique-k5209o, and expect docs/ERRATA.md numbering
collisions at merge — mint numbers from the tail and note the risk." — the
tranche instruction, PARALLEL WINDOWS. The two forbidden directories are
`experiments/2026-08-28-audit-run-problems/` and
`experiments/2026-08-28-diversity-generation/`.

C5: "KNOWN CURRENT STATE: main = 29e33f702; gate baseline 4374 passed 0
failed (CLAUDE.md's ~3100 note is stale, parked); docs_verify baseline 3
shallow-clone failures + 1 pre-existing falsified census
(INV-frozen-surfaces.md:181, parked) — a delta beyond those four is a
finding. Root sweep RETIRED. Never work around a REFUSED_* or typed stop."
— the tranche instruction.

C6: "GATE: ring while iterating, full gate at the boundary (0 failed only),
docs_verify full, commit and push at every phase boundary (retry
2s/4s/8s/16s)." — the tranche instruction.

C7: "tokens are cheap. You are not. So any experiments with token spend that
can settle things is preferred." — the operator, 2026-08-28. Standing
preference: settle a question by spending tokens rather than agent
reasoning, where a token-spend can settle it.

C8: "DELIVERY: requirement-by-requirement reconciliation with pasted proof;
DELIVERY.md states, for each robust rule, before → after with a rendered
example from the same root as R1's census." — the tranche instruction.

## Map ids resolved (map preflight, per dr-drive-harness §4)

Read before design, in this order:

- `docs/map/INDEX.md` — routing.
- `docs/map/INV-frozen-surfaces.md` — the five surfaces (seven paths). None
  is in this cone; C3 governs if that changes.
- `DR-CON-packs-and-token-economy` — the PRIMARY covering document.
  Owns `llm/packs.py`, `packs/allocate.py`, `packs/ir.py`, `llm/budget.py`,
  `llm/profiles.py`, `llm/adapter.py`, `rules/crit.py`.
- `DR-SUB-llm` — adapter, route firewall, packs, wire contracts, profiles.
- `DR-SUB-scratch` — the imaginative workshop, `advisory_non_grounding`.
- `DR-INV-reference-menu` — the one authority for legal handle sets; the
  repo's existing "retrievable by reference" shape, named by R2c.
- `DR-CON-discharge-channel` — why `open-criticisms` sits where it does;
  the one place ordering is NOT presentation-only.
- Seams, read BEFORE the subsystems they join, per the one ordering rule:
  `DR-SEAM-llm-x-rules` (22), `DR-SEAM-rules-x-scratch` (18),
  `DR-SEAM-llm-x-workflow` (33).

Seam gaps noted as findings, not blockers (`INDEX.md`'s own matrix says so):
`llm × scratch` (coupling 10) is NOT YET WRITTEN, and
`packs-and-token-economy × scratch` and `packs-and-token-economy × rules`
are listed `Seams-undocumented` on the packs document itself. This tranche's
cone sits exactly on those undocumented pairs.

## Open questions (for dr-spec-change)

Q1: R1b says "standing instructions" without defining the unit. What counts
as one instruction in a rendered DeepReason prompt — a numbered rule, a
sentence in the imperative, a JSON-schema constraint, a bullet? The count is
the requirement's whole content, so the counting rule must be fixed and
mechanised before the census reports a number.

Q2: R2a says "nothing load-bearing rendered after the question". DeepReason
packs do not have one syntactic "question" — a conjecture pack has a
`problem` section and a `directive`; a criticism pack has a `target` and a
directive. Which rendered element is "the question" for each seat, and is
the output contract (JSON schema, worked example, alias table) "load-bearing
material after the question" or the frame around it?

Q3: R2e says the layout policy ships "as configuration or a versioned
artifact". The repo has both shapes already (`Config` fields; recorded
policy artifacts like `capture14-hysteresis.v1`). Which shape does this
policy take, and what exactly does the architecture test assert to make
"bypassed" mechanically detectable?

Q4: R1's proof requires "at least one real rendered prompt reconstructed
from a committed root's render receipts". Which committed root, and do its
receipts in fact carry enough to reconstruct a full prompt rather than a
pack body?

## Amendments

(append-only)
