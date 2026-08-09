# Phase A — wiring audit: is "endpoints querying isolated LLM output" wired?

Traces R1/R2/R10 of `REQUEST.md`. All numbers below were re-derived live
against the committed tree and committed run roots on 2026-08-09, not
copied from prose. Commands are pasted so this is re-derivable.

## 1. `docs/RESEARCH_BACKEND.md`'s "tranche 2 gated" claim — STALE, contradicted by the tree and by the rest of the same document

The document's own status line (line 6) says:

    Status: tranche 1 IMPLEMENTED — ... V6 in-run enablement remains
    gated (V6_RESEARCH_UNAVAILABLE) and is tranche 2.

That is not what the code does today, and it is not what the REST of the
same document says either — the document was never updated after its own
later sections record tranche 2 shipping. The gate is conditional, not a
blanket refusal:

    $ sed -n '2869,2874p' src/deepreason/run_manifest.py
        if capabilities.research.enabled and (
            capabilities.research.backend_identity != "web.contained.v1"
        ):
            # The contained directed-fetch runtime is the only implemented
            # research authority; any other backend identity stays refused.
            raise ValueError("V6_RESEARCH_UNAVAILABLE")

`V6_RESEARCH_UNAVAILABLE` fires only when research is enabled with a
backend OTHER than `web.contained.v1`. With that one implemented backend,
research is admitted, not gated. The same document's own later sections
say so explicitly and are accurate:

- "Tranche 2 (A, B, C1, C2) is complete." (line 170)
- "Status after C2 ... Increment C2 is implemented and gated (full suite:
  3059 passed, 7 skipped)" (line 149-151)
- "The backend is live-proven. `DEEPREASON_RESEARCH_ALLOWLIST` opts
  prepared runs into the contained backend" (line 177-178)

**Verdict: the document's header Status line is stale.** It was written
before tranche 2 shipped and never re-synced; the body below it is
current and correct. This is exactly the failure mode
`docs/ERRATA.md` exists to record (R10) — filed as Errata entry E-next
in the same commit as this audit (see `ERRATA_ENTRY.md` staged below,
folded into `docs/ERRATA.md` in this phase's commit).

## 2. Live proof: the in-run capability channel is reachable in a managed run TODAY

Not inferred from prose — re-verified directly against a committed root
this session, chosen because `DR-SUB-capabilities`'s own map document
already cites it as the replay-pinned regression fixture
(`tests/test_research_root_replay.py`):

    $ python -c "
    from deepreason.harness import Harness
    from deepreason.invariants import verify_root
    from deepreason.run_manifest import load_run_manifest
    from deepreason.capabilities.models import (
        ResearchFetchProposalV1, ResearchGrantV1,
        ResearchExecutionReceiptV1, ResearchResultPackageV1,
        ResearchConsumptionV1,
    )
    R = 'experiments/live_research_2026-07-29/wide/runs/run-0c3ce902cc5bca75a709b04e2473d100'
    print('verify_root violations:', verify_root(R)['violations'])
    m = load_run_manifest(R + '/run-manifest.json')
    print('schema_version:', m.schema_version)
    p = m.inquiry_capability_policy.research
    print('enabled:', p.enabled, 'backend:', p.backend_identity,
          'allowlist:', p.domain_allowlist, 'max_requests:', p.maximum_requests)
    h = Harness(R, read_only=True)
    s = h.capability_state
    print('proposals:', sum(isinstance(x, ResearchFetchProposalV1) for x in s.proposals.values()))
    print('grants:', sum(isinstance(x, ResearchGrantV1) for x in s.grants.values()))
    print('receipts:', sum(isinstance(x, ResearchExecutionReceiptV1) for x in s.receipts.values()))
    print('consumptions:', sum(isinstance(x, ResearchConsumptionV1) for x in s.consumptions.values()))
    "
    verify_root violations: []
    schema_version: 6
    enabled: True backend: web.contained.v1
      allowlist: ('en.wikipedia.org', 'www.rfc-editor.org') max_requests: 6
    proposals: 3
    grants: 3
    receipts: 3
    consumptions: 1

This root replays clean (`verify_root` finds zero violations) with the
model (glm-5.2) having proposed three directed fetches on the v6
conjecture wire, all three granted under the frozen allowlist, dispatched
through `ContainedFetcher`, receipted, and one consumed into citable
evidence blocks. Typed containment fired live in the same root: one
`www.rfc-editor.org` fetch hit `RESEARCH_RESPONSE_TOO_LARGE` (4194305
bytes against the 4194304-byte ceiling) and was refused without
crediting content.

Typed budget exhaustion, live, in a sibling root from the same campaign:

    $ python -c "
    from deepreason.harness import Harness
    from deepreason.capabilities.enums import CapabilityLifecycle
    from collections import Counter
    h = Harness('experiments/live_research_2026-07-29/wide/runs/run-5a771259557378224bd68591483817be', read_only=True)
    s = h.capability_state
    print(Counter(t.lifecycle for t in s.transitions.values()))
    print(Counter(t.reason_code for t in s.transitions.values() if t.lifecycle == CapabilityLifecycle.DENIED))
    "
    Counter({PROPOSED: 3, VALIDATED: 3, DENIED: 2, GRANTED: 1, COMPILED: 1,
             DISPATCHED: 1, FAILED: 1, RESULT_PACKAGED: 1})
    Counter({'requests_budget_exhausted': 2})

**Verdict: the in-run research capability is live, not merely coded.**
Two of three proposals in this root were denied with the typed reason
`requests_budget_exhausted` after the run-cumulative request budget was
spent — the denial is a durable record, never silence, matching
`DR-SUB-capabilities`'s stated design.

Note on the task description's "enrichment corpus's research records":
no directory, file, or code symbol named "enrichment corpus" exists
anywhere in the tree (`grep -rli enrichment docs experiments/*.md
experiments/*/*.md` finds nothing of that name). The live evidence above
— `live_research_2026-07-29`'s nine committed roots — is what the task
description's phrase most plausibly meant; there is no second corpus by
that name to reconcile against. Recorded here as an unresolved textual
reference rather than silently substituted.

## 3. What the in-run capability channel actually IS — and is not

Important scoping fact for Phase B: `ContainedFetcher`'s transport is a
raw HTTP GET (`_urllib_transport`, `research/fetch.py:217-230`) against
an allowlisted **document** host. There is no code path anywhere in
`src/deepreason/` that dispatches a request to another LLM's inference
endpoint and captures its output as research material. "Research" in
this codebase, everywhere it is wired, means **fetching a document**,
never **querying a model**. This is the load-bearing finding for Phase
B: the operator's "isolated LLM" apparatus is new construction, not an
extension of an existing LLM-query wire — none exists to extend.

## 4. Every access point, enumerated, with containment properties

| # | Access point | Code | Who can trigger it | What it can fetch/submit | Containment |
|---|---|---|---|---|---|
| 1 | In-run capability channel (model-proposed directed fetch) | `capabilities/research.py::ResearchCapabilityController`, wired through `ConjecturerTurnWireV6.research_proposals` (`llm/wire.py:1755-1816`) | The seated conjecturer model, ONLY when `manifest.inquiry_capability_policy.research.enabled` (opt-in per run via `DEEPREASON_RESEARCH_ALLOWLIST`, `v6_policy.py:325-333`) and `backend_identity == "web.contained.v1"` | Explicit `https://` URLs the model names, ≤2 proposals/turn (`MAXIMUM_PROPOSALS_PER_TURN`, wire-frozen constant, `research.py:148`), ≤3 URLs/proposal | Frozen domain allowlist checked at grant AND replay (`state.apply`, `DR-SUB-capabilities` Traps); run-cumulative requests budget, typed exhaustion; 4 MiB per-response byte ceiling; every fetch is a receipted, content-digested, replay-verified event; the maps are pooled with simulation's budget counters but filtered by record type (the pooled-map Trap) |
| 2 | Docket / `submit_evidence` (§12 "agent" mode) | `ops.py::research_docket` (read-only view), `ops.py::submit_evidence` (registration); dispatched via `scheduler.py::_research_step` when `Config.RESEARCH_BACKEND == "agent"` — **the config default** (`config.py:346`) | The OPERATING agent — a human or an external session driving the harness process; NOT the seated model inside the run | Arbitrary `content: str \| bytes` and an arbitrary `source` string naming provenance, no URL structure required | **No allowlist, no request budget, no byte ceiling.** The only structural guard is that `problem_id` must name an open research problem (`SpawnTrigger.RESEARCH`) and `role` is `import`/`user`; content becomes an ordinary artifact, attackable through the same criticism machinery as any other candidate, and is content-digested once stored — but nothing bounds WHERE the operating agent got the bytes. This is the closest existing thing to "an endpoint querying an isolated LLM": the harness never makes the call itself, but nothing stops the human/agent operating the docket from pasting in text they obtained by querying any LLM they like, out of band, and it enters exactly like any other researched evidence |
| 3 | Ladder-level `run_research` / `WebBackend` / `StaticBackend` / `AskUserBackend` (§12, `research/backends.py`) | `research/backends.py::run_research`, dispatched by the SAME `_research_step`, sharing no code with capability 1 (`DR-SUB-capabilities` states this explicitly: "an unrelated, older subsystem of the same name") | The scheduler itself, on a periodic cadence (`RESEARCH_PERIOD`, default 5 cycles), only when `Config.RESEARCH_BACKEND` names an internal backend (`static:`/`web:`) | `WebBackend` mirrors capability 1's containment (same `ContainedFetcher`, allowlist config file) but is directed by the RESEARCH PROBLEM'S OWN TEXT, not a model wire field, and is invoked by the scheduler rather than proposed inside a conjecture turn; `StaticBackend` reads a curated offline fixture file only; `AskUserBackend` is a no-op unless the run is explicitly attended | Same allowlist+receipt containment as capability 1 where `web:` is configured; `static:` is fully offline/deterministic; none of the three query an LLM endpoint either |

Access point 2 is the one that actually matches the operator's original
framing ("endpoints... query the output of isolated LLMs") in spirit —
but only because it is UNSTRUCTURED enough to let an external operator
do that manually outside the harness's own containment. It is not a
typed, receipted, replay-verified probe the way access points 1 and 3's
`web:` backend are. This gap — a manual, uncontained side door standing
in for what should be a typed apparatus — is the load-bearing evidence
for Phase B (R4-R7): the amendment's probe apparatus is not decorating
an existing wire, it is building the typed, contained version of
something that today only exists as an ungoverned manual pathway.

## 5. Security posture, summarized

- Access point 1 (in-run capability): SECURE by the same containment
  doctrine as the rest of the harness — frozen allowlist, run-cumulative
  typed budget, per-response byte ceiling, full replay verification.
  Live-proven both for successful fetches and for containment firing
  (oversize response, budget exhaustion).
- Access point 3's `web:` backend: same containment as 1, different
  trigger (scheduler-paced, problem-text-directed rather than
  model-wire-proposed). SECURE by the same argument.
- Access point 2 (docket/`submit_evidence`, the CONFIG DEFAULT mode):
  NOT contained in the same sense. No allowlist, no budget, no per-fetch
  receipt — the only record is the registered evidence artifact itself.
  It is not "insecure" in the sense of an exploitable vulnerability (an
  operating agent already controls the harness process and its inputs by
  definition), but it is the one access point with no typed containment
  properties to audit, because it was designed as a hand-off to a human
  or external agent, not as a machine-to-machine channel.

## 6. Answer to the operator's three questions

1. **"Is the ability for endpoints to query the output of isolated LLMs
   for research purposes still wired?"** No literal LLM-query mechanism
   is wired anywhere in the tree — every "research" access point fetches
   a DOCUMENT (or, for the docket, accepts arbitrary operator-submitted
   text), never queries a model's inference endpoint. The nearest
   existing thing is access point 2, which is an ungoverned manual side
   door, not a built LLM-query wire.
2. **"Check where it can be accessed from."** Table above: three access
   points, one of them (docket/`submit_evidence`) reachable by any agent
   or human driving the harness process with no allowlist/budget, and
   two (the in-run capability and the `web:` ladder backend) reachable
   only under frozen containment and only for document fetches.
3. **"Decide whether its access points are worth expanding."** Superseded
   by the amendment: Phase B below is not an "expand access" decision
   sheet for the existing (document-only) wiring, it is a fresh SPEC for
   the LLM-probe apparatus the operator actually wants, per the amended
   framing.
