# Systematic schema sweep: every mechanically-enforceable rule made mechanical

Tranche: 2026-07-31. Commits `e71df940`..`18a78bf8` (8), on
`claude/amendment-epochs-om0ztb`.

## The rule this serves

Operator rule A2 (`../2026-07-31-change-critic-seats-and-thinking/REQUEST.md`,
R9-R12): with reasoning disabled the JSON Schema is the model's only source of
structural truth, so a constraint living only in prose is an ambiguity in the
CONTRACT, not a model failure.

Measured, not assumed. `scratch.link.compact.v1` scored 11/20 then 9/20
first-pass with 18 and 22 repairs on glm-5.2 with thinking off, failing
production qualification twice and dropping the whole engine to `shallow`.
Encoding one cross-field rule took it to 20/20 with zero repairs, tier `full`,
with the Python validators untouched.

The operator's instruction for this tranche: apply the same treatment to every
contract where a pattern applies, "not just the ones that happened to fail. No
exceptions unless you flag a good reason."

---

## 1. Prose-only constraints found, and their verdict

### Encoded

| Rule | Where it lived | Pattern applied |
|---|---|---|
| "at least one meaningful outcome" + abstention exclusivity | `_meaningful_*_outcome`, `llm/wire.py` v4/v5/v6 x2 chains | `outcome_shape_schema` |
| "a query, visible alias, or channel" | `_has_semantic_selector`, `llm/wire.py:915,955` | `outcome_shape_schema` |
| per-class grounding minimums (5 classes) | `_epistemic_minimums`, `bridge/ledger.py:585` | `discriminated_shape_schema` |
| action shape (3 correction modes) | `_action_shape`, `bridge/repair.py:112` | `discriminated_shape_schema` |
| verdict/recommendation biconditional | `_menu_coherence`, `referee.py:239` | `discriminated_shape_schema` |
| amendment is a distinct outcome | `_amendment_is_a_distinct_outcome`, `bridge/compose.py:280,321` | `discriminated_shape_schema` |
| a named winner needs a located point | `_winner_has_a_located_point`, `llm/wire.py:1923` | `discriminated_shape_schema` |
| no duplicate references (~40 arrays) | `_freeze_unique`, `_unique_values`, `_unique_handles`, `_unique_sequences`, `_local_refs`, `_members_are_local`, `_unique_citations` | `uniqueItems` |
| alias namespaces `[ABCLG]#`, `(?:SRC\|SCR)_###`, `(?:SCR\|NEW)_###` | `_visible_alias_syntax`, `_local_refs`, `_members_are_local` | `pattern` |
| https-only research URLs | `_https_and_unique`, `capabilities/models.py:513` | `pattern` |
| "must be a call-local alias" | `AliasTable.resolve` raising `UnknownAliasError` | enum binding |

### Not expressible — prose retained deliberately

JSON Schema cannot state any of these without `$data`, which is not in the
standard. Encoding half of one would be worse than nothing.

| Rule | Where | Why not |
|---|---|---|
| `_one_case_per_target` | `llm/wire.py:1706` | uniqueness *by a field of an object*, not by whole item |
| `_keys_are_unique` | `bridge/ledger.py:688` | same shape, over `entry_key` |
| premise forward-reference / key shadowing | `bridge/ledger.py` | "must name an EARLIER entry in this document" |
| `_local_namespace_is_closed` | `scratch/proposals.py:107` | "`NEW_*` must be declared elsewhere in this same response" |
| `_not_a_self_link` | `scratch/proposals.py:59` | equality between two sibling fields |
| `desired_length_chars` budget | workloads | arithmetic over a supplied budget |
| process-observation byte identity | `bridge/ledger.py` | compares against harness-held bytes |
| simulation program structure | `SIMULATION_MODEL_SOURCE_CONTRACT` | Python AST shape, not JSON shape |
| observable-set agreement | `SIMULATION_REQUESTED_OBSERVABLES_CONTRACT` | keys of what the program *returns* |

---

## 2. Contracts changed, by commit

| Commit | Contracts | Pattern |
|---|---|---|
| `e71df940` | v6 turn, all 8 capability combinations | `prune_property` + branch-shape primitives |
| `f3069384` | all 6 turn classes | `outcome_shape_schema` on both chain bases |
| `6d51cbf7` | `ContextRequestWireV1/V2` | `outcome_shape_schema` |
| `6544210c` | `bridge.ledger.v3` | **new** `discriminated_shape_schema`; satisfiability narrowing |
| `6d10d0f5` | `groundingrepairwirev1.direct.v1` | `discriminated_shape_schema`; `restrict_discriminator_values` |
| `53f7ca6e` | `bridge.composition.v1/v2`, `config-referee.v1` | `discriminated_shape_schema` |
| `57e5e2af` | ~40 arrays across 6 modules | `uniqueItems` |
| `18a78bf8` | context requests, scratch refs, research urls; critic/judge/pairwise/synthesizer/defender | `pattern`; alias enum binding |

### Four defects found on the way — three live before the sweep

1. **`_omit_property` never walked `allOf`** (`e71df940`). Capability-gated
   properties were removed from `properties`/`required` only, so **7 of 8**
   combinations of the v6 turn shipped `allOf` branches offering
   `simulation_proposals`, `scratch_proposal` or `research_proposals` as ways
   to satisfy the schema while `additionalProperties: false` forbade emitting
   them. Live on every run with a channel off, which is the common case.
2. **`ReasoningConjecturerTurnWireV6` carried no encoding at all** (`f3069384`)
   — the live reasoning v6 path still advertised `{}` as a valid turn, the
   exact hole that gave `conjecturer.turn.v6` five rejections and zero
   completions in the coin canonicity run.
3. **The repair contract's prompt example was invalid** (`6d10d0f5`).
   `minimal_skeleton` cannot read `allOf`, so it took the first enum value
   (`correct_wording`) and omitted the `replacement_text` that action requires
   — invalid for 3 of 5 finding statuses, long before this sweep.
4. **Two contracts deferred their rules to `compile()`** (`53f7ca6e`,
   `18a78bf8`). `ConfigRefereeWireV1` carried neither `_menu_coherence` nor
   `_unique_citations`; `ResearchFetchProposalWireV1`'s docstring claimed to
   mirror its draft while accepting non-https and duplicate URLs. Both refused
   *after* the response had been accepted and paid for.

### Two contradictions fixed — the defect read backwards

Where the schema advertised MORE than the harness would ever accept:

- **`GroundingRepairWireV1`** offered the whole `CorrectionMode` enum on every
  call, though the pack's `permitted_actions` is narrower for every finding
  status, and offered `resolution: "answered"`, which
  `BRIDGE_REPAIR_RESOLUTION_TOO_STRONG` rejects unconditionally.
- **`ClaimLedgerEntryWireV2.claim_class`** offered all seven classes while
  `_bind_schema_enum` pins an empty channel to `maxItems: 0`, leaving some
  classes unsatisfiable. Narrowing drops only the unreachable ones;
  `premise_keys` and `source_conflict_keys` are not catalog-bound, so
  `supported_inference`, `conflict`, `assumption` and `unknown` are never
  retired. A test pins that no catalog can take away the last two — they are
  how a run stays honest about what it cannot cover.

---

## 3. Prose: nothing trimmed, and why

The operator authorised reporting trim candidates without applying them, on
this ground:

**The qualification battery does not render production prose.** The doctor
probes (`cli/doctor.py`) build their own generic tasks; they never call
`render_conj_pack` or the scratch service packs. So the R11 oracle — 20/20
first-pass, zero repairs — is structurally blind to a bad trim. A trim that
removed necessary context would show up only in a live reasoning run, which
means shipping it here would be shipping it unverified: the scratch.link trap
read backwards.

**A hard blocker regardless.** `SCRATCH_CONTRACT_INSTRUCTIONS`
(`scratch/contracts.py:33-42`) is byte-pinned by `invariants.py:2898-2905`.
Editing it breaks replay validation of every existing root, which is wrong by
definition.

**Trim candidates, for separate approval.** Each is now un-violatable in the
schema, so the English is redundant *as a rule* — but each also names a reason,
which is the part that may still earn its place:

- `ScratchLinkWireV1` docstring, "Exactly one representation is legal for each
  endpoint" — carried by `oneOf`. The following sentence explains *why* a
  handle is preferred over an index; that should stay.
- `ClaimLedgerEntryWireV1.premise_keys` description, "Earlier entry_key values
  or supplied prior-entry keys only" — the *namespace* half is now carried by
  `pattern`, but "earlier" is a forward-reference rule the schema cannot state,
  so this one must stay largely intact.
- `_repair_pack`'s `constraints` list, "A class change can only request a
  separate ledger amendment" — partly carried by the action enum narrowing, but
  it explains an epistemic boundary the schema only enforces mechanically.

Recommendation: leave all three. In every case the schema now carries the rule
and the prose carries the reason, which is the division that made the
scratch.link fix work rather than a redundancy to remove.

---

## 4. New helper required

One genuinely new pattern, covering five separate validators:

    discriminated_shape_schema(*clauses)     # llm/wire.py
    FieldIn(name, values) / FieldPresent(name)
    ShapeClause(when=, requires=, requires_any=, forbids=, field_values=)

"One field's value decides the shape of the others." Three encoding decisions,
each of which was a real trap:

- Clauses append under `allOf`, so `_reject_unknown_fields` — which inspects
  only a TOP-LEVEL `anyOf`/`oneOf` before falling through to `properties` —
  keeps its previous behaviour exactly.
- Negation is spelled as the positive complement. Every discriminator here is a
  closed `Literal`, so `FieldIn` can enumerate, which keeps the emitted schema
  inside the `anyOf`/`enum` subset that constrained-decoding backends actually
  implement.
- A clause naming a value outside the rendered enum RAISES. Silently vacuous
  clauses look encoded and enforce nothing.

Supporting pieces added in the same family:

    prune_property                            # omission that repairs its own constraints
    present_and_nonempty / absent_or_empty / require_absent
    restrict_discriminator_values             # narrow to what THIS call permits
    narrow_unsatisfiable_discriminator_values # drop what no catalog can satisfy
    WireContract.ALIAS_ARRAY_FIELDS / ALIAS_SCALAR_FIELDS

`uniqueItems` needed no helper — the field-level idiom
`Field(json_schema_extra={"uniqueItems": True})` already existed at
`mcp_scratch_bridge.py:114`. Namespaces use native `Field(pattern=)`.

### Two correctness traps inside the helpers, both found by measurement

- A **nullable array** renders as `{"anyOf": [{"type": "array"}, {"type":
  "null"}]}` with no top-level `type` and no `items`. The naive array test
  misses it and emits `{"not": {"type": "null"}}` — which admits `[]` and drops
  the rule. Every reference array on the claim ledger has that shape.
- `minItems`/`minLength` constrain only their own instance type, so on a
  nullable field an explicit `null` satisfies them and the branch admits
  exactly what it meant to forbid. The type has to be pinned.

---

## 5. Deliberate exception, flagged

**The ~20 nonblank (`\S`) rules on free-prose fields are NOT encoded.** Three
reasons, in order of weight:

1. **No measured failure was ever a whitespace-only string.** Not one of the
   glm-5.2 or 20B qualification failures had this shape. This would be encoding
   against an imagined defect.
2. **It would be the first regex ever applied to free prose here.**
   `test_semantic_freedom_constitution.py` encodes a constitutional rule that
   the semantic payload stays open. `\S` is a form constraint rather than a
   vocabulary one, but it invites the next one.
3. **Real downside risk.** Under `native_json_schema` strict mode and GBNF, an
   unanchored `pattern` on a 262 144-character field is compiled into the
   sampling grammar by some backends. The cost of being wrong is a wrecked
   generation; the benefit is preventing a failure mode never observed.

`minLength: 1` already renders wherever pydantic declares it, which covers the
identifier fields where blankness would actually matter.

---

## 6. Divergences introduced, stated rather than buried

Per the operator's decision that the schema may lead a silently-permissive
runtime, **no Python validator was loosened anywhere in this sweep**. The
schema is now stricter than the runtime in exactly these places:

- `uniqueItems` on arrays whose *wire* model had no uniqueness validator but
  whose canonical model does (`SimulationProposalWireV1`,
  `ResearchFetchProposalWireV1`). Both previously refused in `compile()`; the
  refusal is now visible to the model instead of arriving after acceptance.
- `claim_class` narrowing: the Python validator still accepts a class the
  catalog cannot ground. The harness refuses such an entry anyway, because the
  handles it would cite do not exist.
- `action`/`resolution` narrowing on the repair contract: the Python validator
  still accepts any `CorrectionMode`; `BRIDGE_REPAIR_ACTION_FORBIDDEN` refuses
  the difference immediately after.

In every case the schema now describes what the *harness* will keep, not what
one layer of it will parse. Nothing that previously validated end-to-end now
fails.

---

## 7. Verification

Every commit carries a differential test in the shape established by
`test_the_turn_outcome_rules_are_carried_by_the_schema_and_agree_with_the_validator`:
enumerate the product of field shapes, run `jsonschema.validate` and
`model_validate` on each, assert the disagreement list is empty. The fatal
direction is **schema-invalid AND validator-valid** — a false reject, which
under strict `native_json_schema` *prevents* the provider emitting a response
the harness would have taken.

**Result: zero disagreements, in every contract tested.**

| Contract | Product tested |
|---|---|
| 6 turn classes | 5 outcome fields x present/empty/omitted |
| context requests | 2 versions + empty-catalog rendering |
| `bridge.ledger.v3` | 7 claim classes x 10 channels x 4 values x 2 encodings |
| `groundingrepairwirev1` | 5 actions x 2^3 field presence x 2 encodings |
| `bridge.composition.v1/v2` | sections x amendment x reason x 6 resolutions |
| `config-referee.v1` | exhaustive: 2 verdicts x 4 recommendations x citations |
| `CompactPairwiseJudge` | exhaustive: 3 winners x 3 alias shapes |
| 5 alias-bound contracts | legal/illegal alias vs. the compiler |

Two coverage guards (`tests/test_schema_carries_every_prose_rule.py`) pin the
`uniqueItems` set and the cross-field encodings by class and field name, so a
later array or refactor cannot quietly return a contract to the prose-only
state that failed qualification.

### One baseline moved, and the evidence that it was allowed to

`tests/.../DR-2026-07-16-AUTONOMOUS-INQUIRY-WAVE-A/PROVENANCE.json`,
`generated_root_sha256["A3"]`:
`11b5aa701464` -> `c10ccf2be588`. A1 and A2 did not move.

That root is BUILT by the test from a descriptor using current code, and its
bytes include rendered contract schemas — so it moves whenever a schema does.
It is not a committed run root. Three checks before regenerating it, because
"a change that invalidates existing replay-valid roots is wrong by definition":

1. **Determinism holds.** The test's own `first == second` assertion passed
   throughout; only the recorded digest disagreed. The generator did not become
   nondeterministic.
2. **The move is caused by this sweep.** Checked out `4246137d` (pre-sweep) in
   a worktree and ran the test with `PYTHONPATH` pointed at that tree's `src`:
   it PASSES there and fails here. The first attempt at this check was
   worthless — plain `pytest` in the worktree resolved `deepreason` through the
   editable install back to the main checkout, so it re-tested the new code and
   "confirmed" a pre-existing failure that was not one.
3. **`verify_root` on real committed roots is unmoved.** Ran it on
   `run-f4fa6663e5412d64df943a5a22342baf` and
   `run-ac1836b6237b6e9d80b3b0cb492b39f5` before and after: the violation lists
   are byte-identical (6 pre-existing `foreign-criticism` entries each, about
   run content and nothing to do with schemas). No existing replay-valid root
   was invalidated.

`descriptor_sha256` was not touched: the descriptors are unchanged and their
assertions passed. Only the derived digest was regenerated.

### Residue — what is NOT yet proven

- **The full gate has not completed in this session.** Per-area runs before
  each commit totalled roughly 2,400 passing with zero failures, which is not
  the same thing. A full run is in flight.
- **No live battery has yet certified the sweep.** A `gemma4:31b` run is in
  flight (`../live_gemma4_schema_2026-07-31/`); glm-5.2 thinking-off and the
  20B re-run remain outstanding.
- **`if`/`then` has no completed battery behind it.** `allOf` has production
  precedent from the atomic and scratch-link encodings; `if`/`then` does not.
  Every clause emitted here is mechanically rewritable as `{"anyOf":
  [{"properties": {d: {"enum": complement}}}, consequent]}` using only
  `anyOf`/`enum`, since all discriminators are closed Literals. The fallback is
  noted in the encoder docstring.

Accepted does not mean true.

---

## 8. A defect this sweep uncovered and did not fix

**The qualification cache cannot see a schema change.**

`qualification_subject_payload` (`qualification.py:248`) digests the manifest,
the pair inventory and the provider profile. The pair record
(`ProductionContractPairV1`, `cli/doctor.py:57`) carries `contract_id`, `role`,
`seat`, `endpoint_id`, `route_sha256`, `model_id`, `provider`, `family` and
`output_mechanism` — and **no schema bytes at all**.

So changing a rendered wire schema does not move the qualification subject
digest. A home carrying a cached bundle will hit, and report the behaviour of
the contract as it was before the change. Every battery run for this tranche
must therefore use a fresh or cleared `qualification-cache`, or it certifies
nothing — the `gemma4` driver documents this at its head and uses a fresh home.

This is a real defect in its own right: the cache can certify a contract whose
model-facing bytes have since changed. It is not fixed here because the fix
alters a qualification subject digest, which CLAUDE.md lists as a frozen
surface requiring explicit operator approval. **Parked, for a decision.**
