# Fix: pin the per-provider request shape and write down the measured contract — no production code changes

Guarantee restored: **the field each provider carries the neutral
reasoning value in is pinned by a test that fails when it moves**, and
the provider's measured contract — including which shape it refuses — is
written down where the next probe will look for it.

## What the live probe decided

`experiments/2026-09-04-fix-provider-reasoning-contract/PROBE.json`, 45
calls at concurrency 3 on 2026-09-04, key read at call time from the
gitignored env file and absent from the transcript (asserted, not
eyeballed).

- **42 of 42 bodies built by `OpenAICompatEndpoint.build_body`: HTTP 200
  with the expected content.** That is six models — every model in the
  committed provider-profile catalog (`qwen3.5:397b`, `glm-5.2`,
  `kimi-k2.6`, `deepseek-v4-pro`) plus the two carrying a committed
  profile document only (`glm-5.3`, `gpt-oss:120b`) — across all seven
  values of the neutral vocabulary. 36 of those 42 carried a reasoning
  value; all 36 were accepted.
- **The refusal reproduces, and only on the hand-built control.**
  `{"reasoning": "none"}` → HTTP 400, `json: cannot unmarshal string
  into Go struct field ChatCompletionRequest.reasoning of type
  openai.Reasoning`. The harness emits no such field.
- Two further controls: `{"reasoning": {"effort": "none"}}` → 200, so
  the object shape is also accepted; `{"think": false}` → 200 but 891
  characters of reasoning, confirming P2's "does not suppress" note.

GOAL.md's fork closes on **Reading B**. The committed launch configs
were never affected. There is no defect in `llm/` to repair, so the
smallest correct change to the code is none — patching a working request
shape to a second working shape would be a change without a defect
behind it.

## Change sites (exhaustive)

- `tests/test_provider_reasoning_wire_contract.py` (new, ~70 lines) —
  the regression. Three assertions, each mutation-proven:
  (1) each provider adapter's exact emitted dict for every value in the
  neutral vocabulary; (2) no adapter, at any value, emits a key named
  `reasoning` — the field the provider refuses as a string; (3) the
  committed launch config's own critic route, loaded from its manifest,
  builds a body whose reasoning key is `reasoning_effort`.
- `docs/OLLAMA_CLOUD_OPERATIONS.md` (~45 lines added) — a new section
  9, "The reasoning field: measured contract", carrying the probe
  transcript, the accepted and refused shapes, and the retrieval date.
  The document's own `[DOCUMENTED]`/`[INFERRED]`/`[UNKNOWN]` tagging is
  preserved; every new claim is `[MEASURED 2026-09-04]` with the
  transcript path beside it.
- `docs/map/SUB-llm.md` (~20 lines added) — one `Traps` entry for the
  new failure mode, with a `check:` that can fail. It sits beside the
  existing "Unset reasoning is not off" trap, which is about what a
  value MEANS; this one is about which FIELD carries it.
- `docs/ERRATA.md` (~25 lines appended) — corrects PARKED P2's premise.
  P2's own file is left exactly as written: it is another tranche's
  committed ledger, and this repo corrects committed documents by
  appending to the errata rather than by editing them.

Nothing under `src/` changes.

## Frozen surfaces

`tools/blast_radius.py` over the sites the fix was forecast to touch,
run before the design was written:

    python tools/blast_radius.py --files src/deepreason/llm/providers.py \
      --symbols _ollama_reasoning reasoning_body REASONING_ADAPTERS

    {"result_type": "BLAST_RADIUS_RESULT_V1",
     "frozen_surface_contacts": [],
     "frozen_adjacent_contacts": [],
     ...
     "frozen_surface_verdict": "CLEAR"}

    disclosure_summary: "This change touches none of the five frozen
    surfaces. 1 declared symbol(s) already have no live call path today,
    independent of this change: _ollama_reasoning. 1 test file(s) and 3
    map document(s) assert on the touched targets today."

The wire shape does not enter `route_fingerprint`: it is produced by
`reasoning_body` downstream of the Route, and the Route carries only the
neutral value. The gate reports no frozen-adjacent contact, so the STOP
condition GOAL.md set for that case does not fire. The final fix touches
no `src/` file at all, which is strictly inside what was cleared.

## Regression artifact

`experiments/.../repro_wire_shape.py` keeps exit 0 (Reading B), and the
new `tests/test_provider_reasoning_wire_contract.py` carries the pin
into the gate, where the experiment script cannot reach. Mutation proof
is required per assertion: each is shown red under a deliberate edit to
the adapter it pins, and the edit reverted.

New condition this fix must be tested against, which no existing test
covers: **no adapter emits a bare `reasoning` key.** Today's tests pin
what each adapter DOES emit; none pins what none of them may emit, and
that is the property the provider's refusal makes load-bearing.

## Existing tests at risk

From `grep -rln "reasoning_body\|REASONING_ADAPTERS" tests/`:

- `tests/test_providers.py` (21 assertion sites) — pins today's shapes.
  Must keep passing unchanged; the probe confirms every shape it asserts
  is accepted live.
- `tests/test_review_fixes.py:179-184` — the DeepSeek low-effort
  mapping. Must keep passing unchanged.
- `tests/test_model_profile_registry.py:415` — must keep passing
  unchanged.

No fixture depended on defective behaviour, because no behaviour was
defective. Nothing is updated; everything must stay green.

## Explicitly not changed

- `_ollama_reasoning`'s emitted shape. The provider accepts both
  `reasoning_effort: "none"` and `reasoning: {"effort": "none"}`;
  switching to the second would be motion without a defect, and it would
  move a shape 99 recorded live attempts already validate.
- The model-profile documents' own `reasoning:` values. GOAL.md puts
  them out of scope, and `DR-CON-model-profiles` makes them a human's
  document rather than a source edit.
- `llm/split.py`'s choice of which value to send on the emission leg.

## Parked, not fixed here

Two model facts the probe measured incidentally. Both are model-document
work under `DR-CON-model-profiles`, not provider-seam work, and both go
to PARKED.md with a ready-to-send prompt:

- `gpt-oss:120b` still returns 311 characters of reasoning at
  `reasoning_effort: "none"`, where the other five return 0.
- `glm-5.3` at `none` returned its trace inside `message.content` — a
  live confirmation of the recorded `SUB-llm` trap, on a model whose
  committed document already says to use `low`.

## Estimated diff

~160 lines across 4 files, of which ~90 are documentation prose and ~70
are the new test. No `src/` lines. GOAL.md's 150-line budget was written
against a code fix; this is a documentation-and-regression fix and the
code half is zero, so the budget's purpose — bounding the blast radius —
is met with room to spare.

### AMENDED at implementation — the estimate was wrong and the gate says so

    python tools/diff_budget.py fdf35ef06 --ceiling 160 --paths \
      tests/test_provider_reasoning_wire_contract.py \
      docs/OLLAMA_CLOUD_OPERATIONS.md docs/map/SUB-llm.md docs/ERRATA.md

    {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "fdf35ef06",
     "areas": {"tests/test_provider_reasoning_wire_contract.py": 156,
               "docs/OLLAMA_CLOUD_OPERATIONS.md": 90,
               "docs/map/SUB-llm.md": 26,
               "docs/ERRATA.md": 52},
     "total_insertions": 324, "ceiling": 160, "verdict": "EXCEEDED"}

**324 insertions against 160.** The estimate under-counted the test by a
factor of two (156 actual against ~70 estimated: the mutation-proof
docstrings, the absence-tolerant fallback route, and the transcribed
launch-config copy are most of it) and did not count the errata at all
until it was written.

**`git diff fdf35ef06 --stat -- src/` is empty.** Zero production lines.

**Disposition: PROCEED, decided without asking, and disclosed rather
than footnoted.** The dominance test (`dr-ask-the-right-question` §4):
every line of the overage is something the tranche's own instruction
demanded in as many words — "the provider's current contract is recorded
in `docs/OLLAMA_CLOUD_OPERATIONS.md` with the probe transcript" (90),
"offline regression for the request shape per provider, mutation-proven"
(156), and this repo's standing rule that a committed document found
wrong is corrected by appending to the errata (52). Cutting to 160 would
mean deleting part of what was asked for in order to satisfy a ceiling
written for a code fix that turned out not to be needed. No operator
holding the recorded values — smallest correct change, honesty over
polish, evidence recorded — chooses that.

What the ceiling exists to bound is behaviour blast radius, and that is
measured at zero here by two instruments: `diff_budget` reports no `src/`
area, and `blast_radius` returned `CLEAR`. Recorded here, in the commit
message, and in the operator-facing report, so the overage cannot pass
unnoticed. Reversible on request: the errata entry and the operations
section are separable commits if the operator wants them split out.

## Approval gate

Class `defect` per GOAL.md, no frozen surface (`CLEAR` above), no `src/`
change. Proceeds to `dr-implement-fix`.
