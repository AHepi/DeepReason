# Goal: make the reasoning field the harness sends a shape Ollama Cloud accepts today, and record the provider's current contract

Class: defect

Observed: Every committed provider profile in the catalog is
`provider: ollama` at `https://ollama.com/v1`, and every seat of the
newest committed launch config binds `reasoning: "none"`
(`experiments/2026-09-03-change-provenance-history-channel/runs/home-m3/runs/run-5565bd1ef7011e3d25fef3197bdf1cdb/run-manifest.json`,
all eleven roles; `.../runs/home-m3/provider.yaml` line `reasoning: none`).
A four-model probe on 2026-09-04 recorded that Ollama Cloud now refuses
`"reasoning": "none"` sent as a bare string —
`json: cannot unmarshal string into Go struct field
ChatCompletionRequest.reasoning of type openai.Reasoning` — and that
`think: false` does not suppress reasoning either
(`experiments/2026-09-04-experiment-blind-critic/SPEC.md` M5, lines
518-533; parked as that tranche's PARKED.md P2).

## The fork this tranche decides (framed before any fix is designed)

The recorded probe names a field called `reasoning`. The harness's own
adapter names a different field. Both readings are live until a probe
decides between them, and the tranche is decidable under either:

- **Reading A — the harness is broken.** The shape the harness actually
  puts on the wire for a seat carrying `reasoning: "none"` is ALSO
  refused by the provider today. Then every committed launch config
  fails typed at its first seat call, and `llm/providers.py` must send
  the shape the provider now expects.
  *Falsified by:* one authenticated live call carrying the harness's own
  request body returning HTTP 200 with content.
- **Reading B — the probe and the harness send different things.** The
  refusal applies only to a bare `reasoning` string, which the probe
  sent by hand and the harness does not send. Then no committed launch
  config was ever affected, the defect is in P2's premise rather than in
  the code, and the deliverable is the recorded contract plus a
  regression that pins the shape so it cannot drift.
  *Falsified by:* the same live call returning HTTP 400 with the
  unmarshal error.

Which reading holds is NOT decidable from the committed record: the
record contains no request pack for a reasoning-carrying call, and
`https://ollama.com/v1` rejects on authentication BEFORE it parses the
body, so an unkeyed probe cannot discriminate the shapes. Measured this
session, three shapes, all HTTP 401:

    "reasoning":"none"            -> 401 {"error":{"message":"Unauthorized",...}}
    "reasoning_effort":"none"     -> 401 {"error":{"message":"Unauthorized",...}}
    "reasoning":{"effort":"none"} -> 401 {"error":{"message":"Unauthorized",...}}

Success criterion (machine-decidable):

    # 1. Offline, the request shape per provider is pinned and mutation-proven
    python -m pytest tests/test_provider_reasoning_wire_contract.py -q
    -> 0 failed; each assertion fails when the adapter under it is mutated

    # 2. Live, one guarded call per model profile in the committed catalog
    python experiments/2026-09-04-fix-provider-reasoning-contract/probe_reasoning.py
    -> every row HTTP 200 with non-empty content, for a request body built
       by the harness's own endpoint with a reasoning value set

    # 3. The provider's contract is written down with its transcript
    grep -q "ChatCompletionRequest.reasoning" docs/OLLAMA_CLOUD_OPERATIONS.md

    # 4. Nothing else moved
    python -m pytest tests/ -q -n 4      -> 0 failed
    python tools/docs_verify.py          -> 0 failed

In scope: `src/deepreason/llm/providers.py`,
`src/deepreason/llm/endpoints.py`, `docs/OLLAMA_CLOUD_OPERATIONS.md`
(plus the map document covering whichever of those moves).

NOT in scope: the model-profile documents' own `reasoning:` values
(`docs/model-profiles/*/agent.md`) — which value a model needs is a
human's document to write and this tranche does not touch it; and
`llm/split.py`'s choice of which value to send on the emission leg.

Budget: <=150 changed lines, 1 commit, ~3 hours.

Stop conditions inherited from orchestrator: yes.

## Map preflight (ids resolved before designing)

- `DR-SUB-llm` — `docs/map/SUB-llm.md`: adapter, route firewall, packs,
  wire contracts, profiles. The owning subsystem.
- `DR-CON-model-profiles` — where a model's own settings live; states
  that a configured `reasoning:` value "travels to the provider exactly
  as written", so the wire SHAPE is this tranche's business and the
  VALUE is not.
- `DR-CON-seats` — how a role becomes a provider request.
- `DR-INV-frozen-surfaces` — read before designing. Forecast: NO CONTACT.
  The five frozen surfaces are `capabilities/state.py`, `harness.py`,
  `invariants.py` + `verification/`, `run_manifest.py`, and
  `qualification.py`; this tranche's scope is `llm/` only.
- Frozen-ADJACENT: `route_fingerprint` in `llm/firewall.py`. It hashes
  `Route.model_dump()`, whose `reasoning` field carries the NEUTRAL
  value. Whether the wire shape enters that hash is a question this
  tranche must answer with the instrument, not by reading: if it does,
  STOP at FIX.md with `tools/blast_radius.py` rows pasted.
- **Map finding:** the seam this tranche sits on, `llm x model-profiles`,
  is listed in `docs/map/INDEX.md` as "not yet written". Per
  `dr-drive-harness` §4.5 that is a finding, not a blocker; whether this
  tranche writes it is decided at FIX.md, once the fork above is closed.

## Blocked, and on what

The live half of the success criterion needs the Ollama Cloud key. The
container is fresh: no `experiments/*/env` file exists and
`OLLAMA_API_KEY` is unset. CLAUDE.md's Environment section says to
recreate it from the operator's handover; there is no handover in this
session. Every offline phase proceeds without it.
