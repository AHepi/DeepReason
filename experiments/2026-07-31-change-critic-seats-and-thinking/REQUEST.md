# Request: turn the critic roles back on, expose simulation to both, thinking off

Captured: 2026-07-31, from the operator message immediately following the
Mini roles analysis.

## Verbatim

> I suspect why all of the critic roles were switched off. So you need to
> turn them back on, properly expose the simulation option to both
> conjecture and critic artifacts, ensuring the form of the contract is
> also exposed. and create a binding rule that thinking or reasoning mode
> must be switched off when it's available. GLM 5.2 should have had
> thinking off.

## Requirements

R1 (behavior): "turn them back on" — the critic roles that "were switched
off" must be on.

R2 (behavior): "properly expose the simulation option to both conjecture
and critic artifacts" — the simulation option must be exposed to the
critic path as well as the conjecture path.

R3 (behavior): "ensuring the form of the contract is also exposed" — not
merely the option, but the FORM of the contract, exposed alongside it.

R4 (artifact + behavior): "create a binding rule that thinking or
reasoning mode must be switched off when it's available."

R5 (behavior): "GLM 5.2 should have had thinking off." — the provider
profile used in this repository's live runs must have thinking off.

## Standing constraints

C1: "Never touch run-root records or replay validation." — operator, D2b
approval, still standing and never withdrawn.

C2: "the full gate must end 0 failed" — operator, D2b approval; and
CLAUDE.md: "Gate discipline: 0 failed is the only acceptable result.
Never weaken an assertion to get green."

C3: CLAUDE.md frozen surfaces — `capabilities/state.py` digests and event
application, `harness.py` event application, replay-validation record
formats, manifest schemas, "Anything altering qualification subject
digests" — need explicit operator approval. R1 and R2 are both likely to
touch manifest/qualification surfaces; SPEC.md must establish whether
they do and stop if so.

C4: CLAUDE.md: "one defect or one change per commit".

## Open questions (for dr-spec-change)

Q1: WHICH roles does "all of the critic roles" name? The record shows the
`argumentative_critic` seat was ON and productive in the coin run (6
`batch-critic.v2` calls, 9 recorded criticisms). The seats that were OFF
(`inactive_no_authorized_contract`) were `defender`, `judge`,
`grounding_reviewer`, `property_designer`, `variator`, `vision_critic` —
the ADJUDICATING seats, not the criticising one. Separately, MiniReason
seats only `conjecturer` (+ `summarizer`, `thesis` for the bridge) and
has no critic seat at all by design. The request is answerable in three
different scopes and they are different pieces of work.

Q2: "switched off" — by what mechanism? The coin run's seats were
`inactive_no_authorized_contract` at qualification, which is a
classification outcome, not a config switch. Whether R1 means "qualify
those contracts", "change the config that selects them", or "stop the
classifier from deactivating them" is undetermined.

Q3: "the simulation option ... to critic artifacts" — the critic wire
contract (`batch-critic.v2`) has no simulation channel today. Does R2
mean the critic may FILE simulation proposals, or that the critic is
SHOWN what simulations the conjecturer filed/could file? These are
different contracts and different budgets.

Q4: "the form of the contract" — the `simulate(inputs, rng)` +
`requested_observables` disclosure shipped in D2b, or something broader
(the declarative_numeric_v1 document shape, parked as D2c)?

Q5: R4 "binding rule" — binding at which layer? A launch-time refusal, a
manifest/profile validator, a qualification-time check, a test in the
gate, or a documented operating rule in CLAUDE.md? "Binding" implies
enforcement, not documentation, but the enforcement point is
undetermined.

Q6: R4 "when it's available" — how is availability detected? Per-provider
(the `REASONING_ADAPTERS` table knows deepseek/openai/ollama), or
per-model, or by probing the endpoint?

Q7: R5 — the current profile has `reasoning: null`, which means the
neutral knob is UNSET, so no reasoning field is sent at all. Measured
this session: glm-5.2 on Ollama Cloud returns a populated `reasoning`
field regardless, so unset ≠ off. What value actually turns thinking off
for this provider is an empirical question SPEC.md must settle.

## Amendments

(append-only)

## Amendments

### A1 — operator answers to SPEC.md's three decision points (2026-07-31, verbatim)

D-1 (R1 scope), answering "judge + grounding_reviewer only":

> The first option. But don't push. Change here, do another GLM run with
> thinking off and no qualification. Then return the results of interest.

D-2 (R2 reading):

> Show the critic the contract + filed proposals (Recommended)

D-3 (R5 cost / R4 binding point):

> Authorise re-qualification; bind at launch (P2) (Recommended)

New requirements derived from A1, in the operator's own words:

R6 (process): "don't push" — commit locally; do NOT push to the remote
for this tranche. Supersedes the orchestrator's standing
"commit and push at every phase boundary" for this tranche only.

R7 (process): "do another GLM run with thinking off and no qualification"

R8 (artifact): "Then return the results of interest."

R1 is hereby narrowed to R1a (judge + grounding_reviewer). R1b
(variator/property_designer/vision_critic/defender) is NOT approved and
moves to PARKED.md.

### Conflict recorded, not resolved silently

R7 says "no qualification". SPEC F6 measured that thinking off moves the
provider profile digest, and R1a moves the policy preset digest and the
pair inventory; either alone changes the qualification subject, so the
cached battery cannot apply. D-3 authorises the re-qualification, and R7
asks for none. The two cannot both hold with the full engine, because the
only no-battery tier is `shallow`, whose next action is
`reason --shallow` — the reduced engine, which has no capability
channels and so cannot exercise R2 at all.

Recorded here; put to the operator before the live run, not resolved by
assumption.

### A2 — new operator rule (2026-07-31, verbatim)

> Rule: Prose-only constraints must be enforced in the schema
>
> Principle
> When reasoning/thinking is disabled, the model relies on the JSON Schema as the sole source of structural truth. If a constraint exists only in natural-language prose—and the schema permits a violation—the model will often violate it. This is not a model capability failure; it's an ambiguity in the contract specification.
>
> Detection
> Look at any contract that fails with thinking off but passes with thinking on (especially the ones that show repair churn). Check for:
>
> · Constraints described in English but not expressed via JSON Schema keywords (oneOf, dependentRequired, not, if/then/else, pattern, additionalProperties, etc.).
> · Optional/nullable fields that should be mutually exclusive.
> · Enumerations or namespaces described in prose but not captured in regex patterns.
> · Handle/reference forms that should forbid mixing index-based and handle-based endpoints, but don't.
>
> Required action
> Mechanically enforce every known constraint in the contract's JSON Schema. Make the schema the definitive, machine-readable source of validity. The contract must be impossible to violate without producing invalid JSON.
>
> Common fixes
>
> · Mutual exclusion: Use oneOf with required lists. For example:
>   "oneOf": [ { "required": ["from_index", "to_index"] }, { "required": ["from_handle", "to_handle"] } ]
>   Remove nullable escapes and disable additionalProperties if not already done.
> · Identifier namespaces: Replace "must match ^CLM_…" prose with a pattern property.
> · Conditional dependencies: Replace "if field X is provided, field Y must be a source handle" with if/then blocks.
> · Disallowed combinations: Use not with required to forbid co-occurrence of fields.
>
> Validation before acceptance
> After amending the schema, run the qualification battery with thinking off. The contract must pass at a level indistinguishable from the thinking-on baseline (20/20 first-pass, zero repairs). If it doesn't, the schema still contains a loophole—fix it and retest.
>
> Why this works
> It transforms the contract from "follow both my instructions and my schema" to "just generate valid JSON against this schema." The schema becomes self-policing, removing the need for hidden reasoning to hold an extra-textual rule in memory. It also makes the contract more robust against future model updates or temperature changes.

R9 (behavior): "Mechanically enforce every known constraint in the
contract's JSON Schema ... impossible to violate without producing
invalid JSON."

R10 (process): detection target — "any contract that fails with thinking
off but passes with thinking on (especially the ones that show repair
churn)". Measured this session: `scratch.link.compact.v1` (11/20 then
9/20, 18 then 22 repairs) and `scratch.link.minimal.v1` (18/20 then
17/20). No other contract is below 19/20.

R11 (process): "run the qualification battery with thinking off. The
contract must pass at a level indistinguishable from the thinking-on
baseline (20/20 first-pass, zero repairs)."

R12 (process): "If it doesn't, the schema still contains a loophole—fix
it and retest."

## Correction to the operator's worked example, recorded before acting

The rule's example is

    "oneOf": [ {"required": ["from_index","to_index"]},
               {"required": ["from_handle","to_handle"]} ]

That pairs the endpoints, and the enforced rule does not.
`_require_one_reference_per_endpoint`
(`src/deepreason/scratch/contracts.py:86-111`) tests each endpoint
independently:

    if (link.from_index is None) == (link.from_handle is None): problem
    if (link.to_index   is None) == (link.to_handle   is None): problem

So `from_index=0, to_handle="SCR_002"` is LEGAL today, and the paired
`oneOf` would reject it — the schema would then be stricter than the
validator in a way that forbids valid links. Encoded per endpoint
instead, which is what the prose ("exactly one representation is legal
for each endpoint") actually says.

Second deviation, forced by the codebase: the example says to express
branches with `required` lists, and that is exactly right here for a
reason the example does not state. `_strict_schema`
(`src/deepreason/llm/wire.py:179-195`) walks the whole schema and sets
`additionalProperties: false` on EVERY subschema carrying a `properties`
key. A `oneOf` branch written with `properties` would therefore be
rewritten into a closed object that rejects `relation_hint` and every
other field. Branches must use `required`/`not` only.
