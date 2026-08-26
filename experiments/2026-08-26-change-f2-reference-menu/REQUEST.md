# Request: "reference grounding — the model chooses handles from a menu instead of inventing them"

Captured: 2026-08-26 from the operator's tranche instruction (session-opening
message) and the operator's mid-turn amendment message (same session, sent
during map preflight, before SPEC.md existed).

Tranche: F2 of the REBUILD program. Siblings F1 and F3 run in parallel.

---

## Verbatim — message 1 (session-opening tranche instruction)

> TARGET REPOSITORY: AHepi/DeepReason — verify before anything else;
> if based elsewhere, ask the operator to attach it with push access
> and STOP until then.
>
> Change tranche F2 of the REBUILD program: reference grounding —
> the model chooses handles from a menu instead of inventing them.
> Route through dr-change-orchestrator; the workflow's own stops
> apply.
>
> SETUP (fresh container): git fetch origin main && git checkout -B
> <your session-designated branch> origin/main; git merge-base
> --is-ancestor be9bcff54 HEAD || re-fetch. pip install -e .
> --break-system-packages -q; pip install pytest pytest-xdist
> jsonschema --break-system-packages -q. Use `python -m pytest`,
> never bare pytest. Read CLAUDE.md in full; load dr-drive-harness,
> dr-explain-to-operator.
>
> AUTHORITY for REQUEST.md, operator verbatim (2026-08-26):
> "rebuild. These are massive issues that may explain why the
> results are terrible." The motivating evidence, cite it: W1's
> census — 62.6% of every field-attributed failure across 54 roots
> is an INVENTED reference handle, and the CFR finding: told
> explicitly that omission was legal, seats invented a value 255 of
> 257 times (experiments/2026-08-26-run-anatomy-program/
> W1-form-census/RESULTS.md). The external context:
> docs/RESEARCH_STRUCTURED_OUTPUT_COERCION_2026-08-22.md — escape
> roads that exist but are not taken are decoration; the defense
> must be structural.
>
> THE CHANGE:
> C1 THE MENU: every wire-contract field that references a handle
>    (refs, related_refs, checker ids, evidence handles) gets its
>    LEGAL HANDLE SET rendered adjacent to the field in the prompt —
>    short lists inline, long lists as an indexed table the field
>    selects from by index (the render-receipt handle-map machinery
>    already owns key-sorted handle indexing; reuse it, compare by
>    ordered_refs per the ledgered invariant).
> C2 VALIDATE-WITH-MENU: when a handle field fails validation, the
>    diagnostic ALREADY lists legal handles (W1 quotes it) — but
>    arrives only after a wasted attempt. The menu moves to the
>    FIRST ask. The repair diagnostic keeps its list, now
>    guaranteed identical to the menu shown (one authority for the
>    legal set — never two lists kept in agreement, E26's law).
> C3 OMISSION AS A MENU ENTRY: where omission is legal, the menu's
>    first entry IS the omission form, spelled concretely ("write
>    remove at <path>") — the escape road as a selectable item, not
>    prose advice. Measure nothing here; the rematch measures it.
> C4 SCOPE: prompt rendering + validation sourcing only. NO wire
>    schema shape changes (no re-pin expected — if IntakeFormV1 or
>    the MCP surface somehow moves, all four pins same commit, but
>    the design should not move them).
>
> GATE PROVES: offline stub regressions — a seat replying by index
> resolves to the right handle; the menu and the diagnostic derive
> from ONE source (mutation-prove: fork the lists in a scratch
> copy, a divergence test goes RED); pack budget: the menu's token
> cost is logged by the token economy and bounded (long-list
> truncation is DISCLOSED, no silent caps). Full gate 0 failed;
> docs_verify full; map moves in the same commits.
>
> CONCURRENCY: F1 (pack criticism sections, submission path) and F3
> (Config defaults, allocation) run in parallel. Your blast radius:
> form/prompt rendering of contract fields, validation-message
> sourcing. If you need the pack's criticism sections (F1's) or
> Config defaults (F3's), STOP and say so. Commit and push every
> phase boundary (retry 2s/4s/8s/16s).

## Verbatim — message 2 (mid-turn, during map preflight)

> NEW OPERATOR LAW, ledgered on main 2026-08-26 (CLAUDE.md §Operator
> design laws — re-read it): "There needs to be a priority that
> enforces modularity. Customisation needs to be easy." Amend your
> REQUEST.md with it as a requirement and let SPEC.md answer it
> explicitly. What it means for this tranche:
>
> - Every knob, policy, and behavior your tranche introduces is
>   reachable as CONFIGURATION or a REGISTERED VERSIONED ARTIFACT —
>   if customizing it would require editing code, the design is
>   wrong; rework it before implementing.
> - Your new machinery sits behind a DECLARED INTERFACE on the
>   signal-contract pattern (frozen protocol / versioned artifact /
>   free parameters), and you ship an ARCHITECTURE TEST that goes
>   RED when a consumer bypasses the interface — a modularity claim
>   without a failable check is decoration.
> - At any design fork between a tighter coupling that is smaller
>   and a declared interface that is larger, the interface wins —
>   the operator has priced this and chosen.
>
> Binding it to your specific tranche:
> - F1: the discharge policy (kinds, the re-ask behavior, the
>   disclosure road) is a registered, config-selectable policy —
>   new discharge kinds enter by declaration, not by editing the
>   submission path.
> - F2: the menu renderer is an interface keyed by field kind —
>   a new reference-bearing field type gets a menu by registering,
>   not by touching the renderer; the one-authority legal-set
>   source is the interface's contract.
> - F3: you are closest to compliant already — the wander cap is a
>   policy artifact and the channels are config defaults; add the
>   architecture test that a channel toggle and a floor change are
>   pure configuration, and strike-or-emit the phantom signals so
>   the registry never lies about what is customizable.

---

## Requirements

R1 (behavior): "every wire-contract field that references a handle
(refs, related_refs, checker ids, evidence handles) gets its LEGAL
HANDLE SET rendered adjacent to the field in the prompt".

R2 (behavior): "short lists inline, long lists as an indexed table the
field selects from by index".

R3 (behavior): "the render-receipt handle-map machinery already owns
key-sorted handle indexing; reuse it, compare by ordered_refs per the
ledgered invariant".

R4 (behavior): "The menu moves to the FIRST ask." — the legal-handle
list, which today "arrives only after a wasted attempt", is present on
the initial request.

R5 (behavior): "The repair diagnostic keeps its list, now guaranteed
identical to the menu shown (one authority for the legal set — never
two lists kept in agreement, E26's law)."

R6 (behavior): "where omission is legal, the menu's first entry IS the
omission form, spelled concretely ("write remove at <path>") — the
escape road as a selectable item, not prose advice."

R7 (process): "Measure nothing here; the rematch measures it." — F2
ships no new measurement instrument for escape utilization.

R8 (process): "SCOPE: prompt rendering + validation sourcing only. NO
wire schema shape changes (no re-pin expected — if IntakeFormV1 or the
MCP surface somehow moves, all four pins same commit, but the design
should not move them)."

R9 (behavior): "offline stub regressions — a seat replying by index
resolves to the right handle".

R10 (artifact): "the menu and the diagnostic derive from ONE source
(mutation-prove: fork the lists in a scratch copy, a divergence test
goes RED)".

R11 (behavior): "pack budget: the menu's token cost is logged by the
token economy and bounded (long-list truncation is DISCLOSED, no
silent caps)".

R12 (process): "Full gate 0 failed; docs_verify full; map moves in the
same commits."

R13 (process): "If you need the pack's criticism sections (F1's) or
Config defaults (F3's), STOP and say so."

R14 (process): "Commit and push every phase boundary (retry
2s/4s/8s/16s)."

R15 (behavior): "Every knob, policy, and behavior your tranche
introduces is reachable as CONFIGURATION or a REGISTERED VERSIONED
ARTIFACT — if customizing it would require editing code, the design is
wrong; rework it before implementing."

R16 (behavior): "Your new machinery sits behind a DECLARED INTERFACE
on the signal-contract pattern (frozen protocol / versioned artifact /
free parameters)".

R17 (artifact): "you ship an ARCHITECTURE TEST that goes RED when a
consumer bypasses the interface — a modularity claim without a
failable check is decoration."

R18 (process): "At any design fork between a tighter coupling that is
smaller and a declared interface that is larger, the interface wins —
the operator has priced this and chosen."

R19 (behavior): "F2: the menu renderer is an interface keyed by field
kind — a new reference-bearing field type gets a menu by registering,
not by touching the renderer; the one-authority legal-set source is
the interface's contract."

R20 (process): "Amend your REQUEST.md with it as a requirement and let
SPEC.md answer it explicitly." — SPEC.md must answer R15–R19
explicitly, not merely comply.

## Standing constraints

C1: "rebuild. These are massive issues that may explain why the
results are terrible." — the operator's stated authority for the
REBUILD program, quoted in message 1 as the authority for this
REQUEST.md.

C2: "62.6% of every field-attributed failure across 54 roots is an
INVENTED reference handle" — message 1, motivating evidence,
`experiments/2026-08-26-run-anatomy-program/W1-form-census/RESULTS.md`
§2. Must be cited.

C3: "told explicitly that omission was legal, seats invented a value
255 of 257 times" — message 1, motivating evidence, same RESULTS.md
§3 (CFR = 99.2%, EUR ≈ 5.8%). Must be cited.

C4: "escape roads that exist but are not taken are decoration; the
defense must be structural." — message 1, on
`docs/RESEARCH_STRUCTURED_OUTPUT_COERCION_2026-08-22.md`.

C5: "Route through dr-change-orchestrator; the workflow's own stops
apply." — message 1.

C6: "Use `python -m pytest`, never bare pytest." — message 1.

C7: "Your blast radius: form/prompt rendering of contract fields,
validation-message sourcing." — message 1, CONCURRENCY.

C8: "There needs to be a priority that enforces modularity.
Customisation needs to be easy." — message 2, the ledgered operator
design law of 2026-08-26 (CLAUDE.md, "Operator design laws").

## Map ids (resolved in preflight, per CLAUDE.md's MAP PREFLIGHT rule)

Seams first, then subsystems, then the invariants read before design.

- `DR-SEAM-llm-x-rules` — the pack-construction seam: `rules/conj.py`
  and `rules/crit.py` assemble contexts, `llm/packs.py` renders them.
  This is where a menu section is added.
- `DR-SEAM-rules-x-scratch` — the scratch handle namespace (SCR/NEW)
  that `scratch_proposal` reference fields select from.
- `DR-SUB-llm` — packs, wire contracts, repair. Owns both the menu
  render site (R1–R3) and the diagnostic's legal-handle list (R5).
- `DR-SUB-evidence` — `citable_legend`, the citable-block universe the
  `evidence_refs`/`premise_evidence` handle fields resolve against.
- `DR-SUB-scratch` — `render.py`'s `ordered_refs`, the key-sorted
  handle indexing R3 names.
- `DR-CON-packs-and-token-economy` — section allocation, the
  `DISCLOSED_ON_DROP` no-silent-caps rule R11 must obey.
- `DR-INV-frozen-surfaces` — read before design. F2 touches NONE of
  the five: no state digests, no harness event application, no
  replay-validation formats, no manifest schemas, no qualification
  subjects. R8 forbids wire schema shape changes, which keeps
  `llm/wire.py`'s `model_json_schema` output stable.
- `DR-INV-signal-contract` — the three-layer pattern R16 names
  (FROZEN protocol / VERSIONED registry+policy / FREE parameters) and
  the interface-only-consumption architecture test R17 names.

No missing map document was found for the work; a new `INV-` document
for the menu contract is expected to be CREATED by this tranche (R16,
R19), which SPEC.md must schedule.

## Open questions (for dr-spec-change)

Q1: R1 says "every wire-contract field that references a handle" and
gives four examples ("refs, related_refs, checker ids, evidence
handles"). The corpus has more reference-bearing fields than four.
Does "every" mean every such field in every contract this tranche can
reach, or the census-attested failing set (W1 §2's five fields plus
their siblings)? R8's scope limit and R19's "register, don't edit"
interface interact with the answer.

Q2: R2's "short lists inline, long lists as an indexed table" gives no
threshold. What count separates short from long, and is that threshold
a FREE parameter under R16's three layers?

Q3: R5 says the diagnostic's list is "guaranteed identical to the menu
shown". Identical in CONTENT (same handle set) or identical in
RENDERING (same bytes)? Truncation under R11 can make a shown menu a
strict subset of the legal set, at which point content-identity and
render-identity diverge.

Q4: R11 says the menu's token cost is "logged by the token economy".
The token economy's existing instrument is `PackSection` +
`approximate_tokens` + `DISCLOSED_ON_DROP`. Is membership in that
existing mechanism sufficient, or is a new typed record required?

Q5: R6's omission entry must be spelled "write remove at <path>". On
the FIRST ask there is no repair patch and therefore no JSON-Pointer
patch operation — `remove` is a repair-mode verb. What is the concrete
spelling of the omission entry on an initial (non-repair) ask?

Q6: R3 says to reuse the render-receipt handle-map machinery. That
machinery lives in `DR-SUB-scratch` and is bound to a committed render
receipt. Reference fields outside the scratch namespace (evidence
block ids) have no render receipt. Does R3 mean reuse the MODULE, or
reuse the key-sorted indexing DISCIPLINE (`ordered_refs`-style index
ordering) for menus built elsewhere?

## Amendments

(append-only)

A1 — 2026-08-26, message 2, ledgered above verbatim. Adds R15–R20 and
C8. Supersedes nothing; it constrains the design of R1–R14 rather than
replacing any of them. Received during map preflight, BEFORE SPEC.md
existed, so it is captured as original requirements rather than as a
mid-flight amendment to a written spec.
