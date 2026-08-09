# SPEC — the isolated-LLM probe apparatus

Traces `REQUEST.md` R4-R9 (the amendment's framing, which supersedes the
original R3 "expand access" decision sheet). SPEC ONLY — per C1/R12, no
code changes happen in this tranche; this document is the stopping point.

## 0. What Phase A proved, and why this is new construction

`AUDIT.md` found no code path anywhere in the tree that dispatches a
request to another LLM's inference endpoint and captures its output as
material for the run — "research" always means fetching a DOCUMENT. The
closest existing thing (docket/`submit_evidence`) is an ungoverned manual
side door for a human/external agent, not a typed apparatus. So this SPEC
is not "extend the research backend to also query LLMs" — it is a new
capability, DESIGNED to reuse the containment DOCTRINE the research
capability already proved live (frozen allowlist, requests-denominated
budget, typed exhaustion, content-digested receipts, replay-never-
re-executes), not its code.

## 1. Shape, in one paragraph

A new capability kind — call it the **probe capability** — lets a
conjecturer or a critic dispatch ONE fixed prompt, under fixed sampling
parameters, to ONE model on a frozen allowlist, and get back a receipted,
content-digested set of completions. The dispatch is a typed, budgeted,
replay-verified event exactly like a research fetch. What differs from
research is what happens to the RESULT: from the scratchpad, a probe
result is a note the conjecturer can read and think about, never
evidence (R5a). From the criticism path, a probe result can settle a
`program:` commitment a conjecture declared about LLM behavior — a
DEMONSTRATIVE, judge-free refutation exactly like `crit_program`
refuting an `exec_oracle`/`candidate_checker` commitment today (R5b, R6).
The probed model is a SOURCE the harness observes, never a SEAT and
never a judge (§4).

## 2. R4 — the typed probe protocol

### 2.1 Policy: model allowlist frozen like the domain allowlist

New manifest surface, `ProbeCapabilityPolicyV1` (sibling of
`ResearchCapabilityPolicyV1` in `capabilities/policy.py`, joining
`InquiryCapabilityPolicyV1`'s five-field topology as a sixth):

    class ProbeModelIdentityV1(BaseModel):
        provider: str          # mirrors Route.provider
        family: str            # mirrors Route.family
        model_id: str          # mirrors Route.model_id
        endpoint_id: str       # mirrors Route.endpoint_id
        base_url: str          # mirrors Route.base_url

    class ProbeCapabilityPolicyV1(_PolicyModel):
        enabled: bool = False
        backend_identity: str = "disabled"          # e.g. "isolated.probe.v1"
        model_allowlist: tuple[ProbeModelIdentityV1, ...] = ()
        maximum_requests: int = 0        # run-cumulative dispatch budget
        maximum_prompt_bytes: int = ...  # containment on the outbound prompt
        maximum_response_bytes: int = ...
        maximum_samples_per_request: int = ...   # bounds fan-out per dispatch

The identity fields deliberately mirror `Route` (`run_manifest.py:164`)
rather than inventing a new shape — a probe target is described the same
way a seat's route already is, minus the seat-only fields (`temperature`,
`max_tokens`, `context_window_tokens`), which are PER-PROBE sampling
parameters, not identity, and travel on the draft instead (§2.2). This
is a manifest surface: `DR-INV-frozen-surfaces` surface 4 applies in
full — both the Pydantic model AND its validator must agree, and any
field added later needs `_versioned_source_config_data` told about it
explicitly (the `ENGAGED_CRITICISM_AUTHORITY` Trap in
`INV-frozen-surfaces.md` is the exact failure mode to avoid). A `V6`
gate mirroring `V6_RESEARCH_UNAVAILABLE`'s conditional shape
(`run_manifest.py:2869-2874`) admits exactly one backend identity;
anything else stays refused.

### 2.2 Draft: prompt + sampling params recorded

    class ProbeDraftV1(BaseModel):
        model: ProbeModelIdentityV1      # must be in the policy allowlist
        prompt: str                      # bounded by maximum_prompt_bytes
        temperature: float | None
        top_p: float | None
        max_tokens: int | None
        sample_count: int                # 1..maximum_samples_per_request

Every field the model may set is bounded by a manifest ceiling exactly
the way `SimulationProposalDraftV1`/`ResearchFetchProposalDraftV1` are —
the wire schema and the record share one constraint (`llm/wire.py`
importing types FROM `capabilities/models.py`, never restating them —
the pattern `DR-SEAM-capabilities-x-rules` names as load-bearing:
"the model-facing schema and the recorded record share one constraint,
not two copies").

### 2.3 Budget: requests-denominated, typed exhaustion

Identical denomination to research: ONE dispatched round-trip (success,
refusal, or failure) spends one request; a validation refusal (off-
allowlist model, malformed draft) spends nothing. Run-cumulative,
re-derived from replayed receipts exactly like
`ResearchCapabilityController._requests_already_used` (`research.py:250-265`)
— never a stored counter. Exhaustion mints a typed `PROBE_BUDGET_EXHAUSTED`
receipt carrying `requests_used`/`requests_limit`, mirroring
`RESEARCH_BUDGET_EXHAUSTED`'s "count and limit together, the grounded
shape" (`RESEARCH_BACKEND.md` §1, decision 2).

### 2.4 Receipts with content digests

    class ProbeCompletionV1(BaseModel):     # one sampled completion
        index: int
        content_sha256: str
        byte_count: int
        finish_reason: str

    class ProbeExecutionReceiptV1(_IdentifiedCapabilityRecord):
        proposal_ref: str
        model: ProbeModelIdentityV1          # verbatim, from the dispatched draft
        prompt_sha256: str                   # the EXACT prompt dispatched
        sampling: dict                       # temperature/top_p/max_tokens/sample_count, echoed
        completions: tuple[ProbeCompletionV1, ...]
        requests_used_total: int
        requests_limit: int
        outcome: Literal["completed", "nothing_returned", "budget_exhausted"]

Mirrors `ResearchExecutionReceiptV1`/`FetchReceiptV1` field-for-field
where the analogy holds (`capabilities/models.py:648-679`,
`research/fetch.py:101-121`): every dispatch is sanitized, receipted,
content-digested, and the arithmetic (`requests_used` non-decreasing,
final total matches the receipt) is validated the same way
`ResearchExecutionReceiptV1._receipt_arithmetic` is
(`capabilities/models.py:681-686`).

### 2.5 "Probes are attested observations, never re-executed at replay" — the fetch-receipt precedent, applied precisely

This is not a new property to invent; it is the SAME property every
capability transition already has. `verify_root` never re-fetches a URL
to check a `FetchReceiptV1` — it re-derives EVENT ARITHMETIC (digest
chains, budget counts, `state.apply`'s authority-narrowing checks) from
the log, and trusts the recorded receipt bytes as the observation
(`DR-INV-frozen-surfaces` surface 1: `capabilities/state.py`'s `.apply`
is the one validator every capability event passes through; it is
content-addressed, not re-executed). The SAME discipline that already
makes `execution_backed`/`formally_backed` safe to re-consult on every
`crit_program` call for `exec_oracle` (`rules/warrants.py:24-38`: "the
oracle re-runs the candidate against its frozen tests... a pure function
of content") is exactly what breaks for a probe: an LLM completion is
NOT a pure function of (model, prompt, params) — re-dispatching the same
prompt twice can yield different bytes. So a probe-checkable commitment
(§4) must NEVER re-dispatch at evaluation time; its verdict function
reads the ALREADY-RECORDED receipt's `content_sha256`/`completions` and
applies a deterministic predicate over those FIXED bytes — the dispatch
happens exactly once, at proposal-execution time, budgeted and
receipted, the same moment `ResearchCapabilityController.execute`
dispatches a fetch. This is the one piece of `oracle.py`'s existing
machinery that does NOT transfer as-is (§4.2 explains the resulting
commitment-minting order).

## 3. R5 — two access points, priced separately against the seam docs

### 3.1 Scratchpad (conjecturer-side exploration) — advisory tier

**What it is.** The conjecturer proposes a probe on its own wire turn
(mirroring `research_proposals`'s gating idiom exactly:
`ConjecturerTurnWireV6.probe_proposals`, schema-visible only when
`policy.enabled`, `_omit_property` pruning it otherwise — `llm/wire.py`
§C2 pattern). The dispatch executes in the same turn (mirroring
research's in-turn execution, `DR-SEAM-capabilities-x-rules`'s
"Research return path" row). The receipt's content — the model's
sampled completions — is written into the scratchpad as an ordinary
`ScratchBlockBodyV1` (via `ScratchService.create_block`, the existing
entry point, `scratch/service.py`), never as an `Artifact`.

**Why this is genuinely advisory, not evidence wearing a disguise.**
`SUB-scratch.md`'s frozen manifest literal
`epistemic_boundary: Literal["advisory_non_grounding"]`
(`run_manifest.py`, `scratch/proposals.py::SCRATCH_EPISTEMIC_BOUNDARY`)
already enforces this for every scratch write: nothing in scratch
carries a warrant, a status, or support for one, and criticism receives
NONE of it structurally (`DR-SEAM-rules-x-scratch`: "the scratchpad
offers `conj` a bounded, single-use view of prior thinking; criticism
receives none of it"). A probe result landing in scratch inherits this
for free — no new guard is needed, only a new WRITER (the probe
controller calling `ScratchService.create_block` the way any other
scratch mutation does) and a new scratch-side ceiling
(`maximum_probe_blocks_per_turn`, alongside the existing
`maximum_new_blocks_per_turn`/`maximum_total_bytes` on the manifest's
scratch-authoring policy).

**Price.** Cheap relative to §3.2: reuses `ScratchService`'s existing
mutation path, adds one new proposal field plus one new manifest ceiling
on an ALREADY-scratch-owned policy (not a frozen surface by itself —
`ScratchPolicy` is already a manifest field, so this is an ordinary
field addition to an already-versioned policy, not a new frozen surface
class). The dispatch machinery itself (§2) is the expensive part and is
SHARED with §3.2 — building it once serves both access points.

### 3.2 Criticism path (critic-side counterexample probes) — execution-grade

**What it is.** This is new construction, not a reuse of an existing
critic-read pattern. `DR-SEAM-capabilities-x-rules` states, for the two
EXISTING capability kinds, that "Criticism may READ filed simulations
and may not FILE one, and the refusal is structural" — that sentence
describes what simulation and research are built to do TODAY; it is not
a universal law the probe apparatus must also obey. Nothing in R-g, the
seats/evidence guardrail, or the solo law forbids a critic from filing a
capability draft — the operator's own words name this explicitly as the
point ("It would help with broadening the attack surface of
conjectures"). The correct template is NOT "give criticism the
simulation/research filing door" — it is the mechanism that ALREADY
lets a critic execute something grounded against a target:
`oracle.py::admit_counterexample` (§8.1 of the judge-evidence review
names this "Counterexample execution... give a critic a GROUNDED,
non-judge route to refute a proposed property... produces a verdict
from execution, which the record treats as EXEC_PROGRAMS-grade
evidence, immune to a prose case").

`admit_counterexample` cannot be reused byte-for-byte because it assumes
a cheaply-re-runnable checker (`_run_isolated`, deterministic,
milliseconds); a probe dispatch is neither cheap nor deterministic
(§2.5). The shape it DOES transfer: the critic proposes a NEW instance —
here, a probe VARIANT (a different prompt, or the same prompt with
different sampling) — against an ALREADY-DECLARED base commitment's
spec (§4.1), and admission is split into two phases the way the
capability lifecycle already splits staging from materialization
(`DR-SEAM-capabilities-x-rules` "Filing is therefore two-phase"):

1. **Admission gate (cheap, no dispatch).** The critic's proposed
   variant is checked against the base commitment's spec — same model
   identity (a critic cannot switch to an off-allowlist or different
   model than the conjecture's own claim was about), same allowlist and
   byte ceilings as §2.1-2.2. This step spends no budget and mints
   nothing, mirroring `admit_counterexample`'s own gate step
   (`oracle.py:437-461`) and the capability lifecycle's staging phase
   (`DR-SEAM-capabilities-x-rules`: "Staging appends nothing").
2. **Execution (budgeted, receipted).** Only once admitted does the
   variant dispatch through the SAME probe controller §2 uses,
   producing a `ProbeExecutionReceiptV1` exactly like a conjecturer's
   own probe. The counterexample commitment is minted content-addressed
   over `{base spec, critic's variant, receipt content digest}` — AFTER
   the receipt exists, never before, so its id is stable under replay
   and its verdict never re-dispatches (§2.5, §4.2).

**Where the authority is published and re-derived.** This needs a NEW
authority block on the CRITICISM turn's own semantic task payload —
`payload["probe_authority"]`, sibling of `research_authority`
(`rules/conj.py`) but written by whichever module builds the criticism
transaction payload — since today's criticism side publishes no
capability authority at all (there is nothing for `crit.py` to
re-derive; its entire capabilities surface today is one read of
`harness.capability_state`, per `DR-SEAM-capabilities-x-rules`'s own
measured claim: "Exactly one rules module reaches the capabilities
package... `crit.py` is the second and last... its entire surface is
one read"). Building this authority-publish/re-derive pair for
criticism, mirroring `_stage_transactional_proposal`'s
`research_authority.get("policy_digest") != self.policy.digest` check
(`research.py:361-373`), is the single largest new-construction item in
this SPEC — everything else in §2-§3.1 is closely modeled on code that
already exists; this is not.

**Why the result is execution-grade, not judge-mediated.** The probe's
OWN completions never get INTERPRETED by another model call — the
verdict is a deterministic predicate over the receipt's already-recorded
bytes (§2.5), evaluated by `crit_program`, the SAME kind-blind,
unconditional dispatcher that already refutes `exec_oracle` and
`candidate_checker` targets today (`rules/crit.py:895-923`, "runs on
EVERY target, formal or informal — there is no code-level branch that
skips a target because of its kind"). No judge role is consulted at any
point in this path.

**Price.** The expensive item above (authority publish/re-derive for
criticism) plus the two-phase admission gate; the dispatch machinery
itself is shared and already priced in §2.

## 4. R6 — the commitment shape: probe-checkable claims about LLM limits

### 4.1 The dual-mode candidate-checker precedent, applied

`oracle.py::candidate_checker_commitment` (`oracle.py:234-248`) is
exactly the template the amendment names: the carrying artifact's own
content is PROSE (a conjecture that never has to be code), and the
CHECKER lives in `Budget.extra["spec"]`, content-addressed off that spec
so the commitment id is stable. A new sibling:

    PROBE_CHECK_PROGRAM = "probe_check"   # PROGRAMS["probe_check"]

    def probe_checkable_commitment(model, prompt, sampling, predicate_spec) -> Commitment:
        """Declares WHAT WOULD SETTLE this claim about LLM behavior, before
        any dispatch happens. The spec names the model/prompt/sampling to
        run and the deterministic predicate to apply to the resulting
        receipt — it does NOT embed a receipt yet."""
        spec = {"model": model, "prompt": prompt, "sampling": sampling,
                "predicate": predicate_spec, "min_samples": ...}
        digest = sha256_hex(canonical_json(spec))[:12]
        return Commitment(
            id=f"probe-check@{digest}",
            eval=f"program:{PROBE_CHECK_PROGRAM}",
            budget=Budget(extra={"spec": json.dumps(spec, sort_keys=True)}),
        )

Two candidate contracts attach it exactly the way `ForbiddenCase.
checker_spec`/`Countercondition.checker_spec` already attach
`candidate_checker` (`CON-conjecture-kinds.md` §"Two candidate contracts
can attach this commitment to their OWN prose") — a conjecturer claiming
something about an LLM's limits may (never must, per R-g) declare a
`probe_check` commitment naming exactly how the claim could be tested.

### 4.2 The ordering problem `candidate_checker` does not have, and its resolution

`candidate_checker_commitment` is minted ONCE, up front, and
`crit_program` re-executes its (cheap, deterministic) checker on every
evaluation. A `probe_check` commitment CANNOT work that way (§2.5): the
spec above names WHAT to run but the receipt does not exist yet at
declaration time. Two legal states, both typed:

- **Undispatched** (`receipt_ref` absent from spec): `program.evaluable`
  is `False` for this commitment — `crit_program` skips it exactly the
  way it already skips any commitment `programs.evaluable` returns
  `False` for (`rules/crit.py:901`, "programs.evaluable(kappa)"),
  matching `formally_backed`'s "no protection, not a penalty" rule for
  an unevaluable commitment (`rules/warrants.py`, `CON-conjecture-kinds.md`
  §"Must never do"). A conjecture carrying an undispatched `probe_check`
  is exactly as protected/unprotected as one carrying no commitment at
  all — R-g is satisfied by construction, not by a special case.
- **Dispatched** (`receipt_ref` present, minted by whichever path in §3
  ran the probe first): a NEW, second `Commitment` instance, content-
  addressed over `{spec, receipt content digest}` — never the SAME id as
  the undispatched one, so a `program:probe_check` commitment always
  names a receipt it can read, and `evaluate()` is a pure, replay-safe
  function over that receipt's bytes (§2.5). This mirrors
  `admit_counterexample`'s own "content-addressed, so the same proposal
  replays to the same commitment" property (`oracle.py:427-429`) — the
  same idea, applied to a commitment minted from an observation instead
  of from a fixed spec.

Which side (§3.1 conjecturer-declared or §3.2 critic-initiated) actually
TRIGGERS the dispatch that turns undispatched into dispatched is a
decision this SPEC records as an assumption, not a forced design: the
conjecturer's own probe (run in scratch, §3.1) is advisory ONLY and does
NOT by itself mint a dispatched `probe_check` commitment — surfacing an
advisory receipt as if it settled a formal commitment would be exactly
the "scratch establishes grounding" violation `SUB-scratch.md` exists to
prevent. The dispatched, EVALUABLE commitment is minted only through the
criticism path (§3.2) — matching the operator's own framing that the
critic's probe is what "broadens the attack surface," i.e., what makes
the claim actually attackable/settleable, not the conjecturer's own
scratch exploration.

### 4.3 Mechanically adjudicable in solo runs, no judge anywhere

Once a `probe_check` commitment is dispatched, `crit_program`
(unconditional, kind-blind, requires no seat beyond the one that already
exists for every criticism cycle) evaluates it and, on a FAIL verdict,
calls `register_fail_warrant` exactly as it does for `exec_oracle`
today (`rules/crit.py:911-922`) — a DEMONSTRATIVE refutation, never an
ARGUMENTATIVE one, so no judge, no `require_cross_family_judges`, no
rubric trial is ever consulted for this domain. This is the direct
answer to the amendment's opening sentence — "I want the harness to
figure out how to run without having to keep review only mode on for
solo runs" — for the SPECIFIC domain of claims about LLM behavior:

- **Solo law** (CLAUDE.md, "A solo run with everything on must be an
  option... judge seats are suspect-by-default"): satisfied structurally
  — `crit_program`'s dispatch has never required a judge seat for ANY
  `program:` commitment, and `probe_check` adds no new requirement.
  Nothing about the probe apparatus touches `select_lease`'s
  `(role, seat)` lookup (`CON-seats.md`) or any judge role; the probed
  model is dispatched through its own narrow transport (§2), the same
  way `cli/doctor.py`'s qualification battery already dispatches OUTSIDE
  `select_lease` on purpose (`CON-seats.md`: "The qualification battery
  never calls `select_lease`; it builds its own `EndpointLease`... A
  real divergence from the ordinary dispatch path, not an oversight").
- **Seats/evidence guardrail** ("Seats change how content is GENERATED,
  never what counts as EVIDENCE"): the probed model is never bound to
  any canonical role (`conjecturer`, `argumentative_critic`, `judge`,
  ...) — it has no seat, generates nothing that becomes this run's
  reasoning content, and its output only ever becomes EVIDENCE (about
  itself, as a claim's subject) through the ordinary, kind-blind
  `crit_program` path. This is the load-bearing distinction the
  amendment itself draws: "the queried models are SOURCES, never seats
  and never judges."
- **R-g** (formalism is an option, never an obligation): §4.2's
  undispatched/no-protection-no-penalty state makes this true by
  construction — a conjecture about LLM limits with no `probe_check`
  commitment ranks, survives, and gets accepted exactly as it would
  today; ATTACHING one only ever adds a NEW way to lose (mechanical
  refutation) or gain protection (`formally_backed`'s wider set,
  §4.4), never a rank/admission advantage for having attached it.
- **Judge-review §8** (`2026-08-09-change-judge-evidence-review/
  REVIEW.md` §8.1's "program/predicate commitments" entry): explicitly
  names this exact mechanism class as "NECESSARY infrastructure" whose
  gap is COVERAGE, not design — "the gap is coverage (how many
  conjectures ship a machine-decidable commitment at all), not
  mechanism." `probe_check` is new coverage for a domain (claims about
  LLM behavior) the existing `EXEC_PROGRAMS` set cannot reach at all
  (code execution answers nothing about what a THIRD PARTY model does).
  §8.3's first open fork — "whether the operator wants a genuinely new
  non-judge-mediated status-changing path built for prose specifically"
  — is answered YES by this tranche, for this one domain, not for prose
  adjudication in general (§8.2's finding — no mechanism here judges
  open-ended prose quality — still stands; see §5).

### 4.4 Execution supremacy: narrow, not automatic

Following `CON-conjecture-kinds.md`'s own precedent for
`candidate_checker` (`oracle.py:52-55`: deliberately NOT a member of
`EXEC_PROGRAMS`, because that supremacy is earned by ALSO carrying a
counterexample-admission/fuzz-probe attack channel), `probe_check`
should NOT join `EXEC_PROGRAMS` on day one either, even though §3.2
gives it a counterexample-shaped attack channel — the two differ in one
respect `EXEC_PROGRAMS` membership does not yet account for anywhere in
the tree: STOCHASTICITY (§5). `probe_check` DOES join `formally_backed`'s
wider substantive set (the same set `candidate_checker` joins), so a
target carrying a passing, dispatched `probe_check` commitment is immune
to a bare prose case against it, while remaining refutable by a
STRONGER probe result (a critic's counterexample variant that flips the
predicate) exactly as `candidate_checker` remains refutable by a
stronger checker.

## 5. R7 — stochasticity honesty

A probe's completions are sampled behavior, not a pure function of
(model, prompt) — the SAME LLM given the SAME prompt twice can answer
differently. This is not new to DeepReason: CLAUDE.md's own live-run
doctrine already states it for the existing capability-channel research
("Capability-channel use... is STOCHASTIC across identical runs; one
live attempt that misses a path is inconclusive for that path"). This
SPEC makes that doctrine mechanical rather than advisory prose, for
probes specifically:

- **How many samples ground a claim.** `sample_count` (§2.2, bounded by
  `maximum_samples_per_request`) is DECLARED in the spec before
  dispatch, and `min_samples` (§4.1) is the predicate's own stated
  threshold — e.g. "the model refuses in at least 4 of 5 samples." The
  predicate function reads `ProbeExecutionReceiptV1.completions` (§2.4)
  and evaluates deterministically over whatever was actually returned;
  if `len(completions) < min_samples` (a `nothing_returned` or partial
  outcome), the verdict is `OVERRUN` (the same "no verdict, no warrant"
  disposition `oracle.py` already uses for a sandbox abort,
  `rules/crit.py:907-909`) rather than a false PASS or FAIL — a probe
  that could not gather enough evidence settles nothing, exactly as an
  oracle sandbox abort settles nothing today.
- **How variance is recorded.** The receipt records EVERY sampled
  completion's digest, not a summary statistic — `completions` is the
  full tuple (§2.4), so a reader can always re-derive the exact
  agreement rate the predicate saw. The predicate's verdict and its
  observed rate (e.g. `4/5`) both go into the `crit_program` trace blob
  (mirroring the existing `trace` argument to `register_fail_warrant`,
  `rules/crit.py:920`), so a rejected conjecture's record shows the
  actual sample split, not just PASS/FAIL.
- **What a probe can NEVER do.** A probe's predicate may only test
  MACHINE-CHECKABLE properties of the completion bytes — a fixed string
  pattern, a length bound, a refusal-marker match, a structured-output
  parse-and-compare (the same class of "pure function of content" tests
  `programs.py`/`oracle.py` already run) — it may NEVER rule on PROSE
  QUALITY: no probe predicate may score coherence, argument strength,
  relevance, or any judgment call a human or another LLM would have to
  make about whether the completion is GOOD reasoning. That job is
  categorically a judge's (or a human's), and this apparatus's entire
  reason for existing is to give solo runs a route that does NOT need
  one (§4.3) — a predicate that smuggled prose-quality judgment back in
  would either (a) require an LLM call to evaluate it, silently
  reintroducing a judge under a new name, or (b) be a non-deterministic
  human-coded heuristic masquerading as a mechanical check, which
  `formally_backed`'s "structural well-formedness proves nothing about
  the subject, so it protects nothing" reasoning
  (`rules/warrants.py:79-81`) already condemns for exactly this shape
  of trick. This is a design-time CONSTRAINT this SPEC states, not
  merely a suggestion: `probe_checkable_commitment`'s `predicate_spec`
  should be restricted (at admission, in `dr-plan-steps`/`dr-execute-fix`
  when this is built) to a small closed vocabulary of mechanical
  predicates — string/regex match, length/count comparison, structured
  field equality — the same closed, auditable shape `programs.py`'s
  existing predicate grammar already uses, never an open "ask a model
  whether this is good" escape hatch.

## 6. Frozen-surface forecast

| Surface | Touched? | How |
|---|---|---|
| 1. `capabilities/state.py` (digests, `.apply`) | **YES** | A third capability kind pools into the SAME `CapabilityReplayState` maps (`SUB-capabilities.md`'s own table: "Add a third capability kind... every row above plus the `capability-*` schema map... AND the per-kind branches in `invariants.py` — a frozen-surface change requiring explicit operator approval") — OR a deliberately SEPARATE, non-pooled state class is chosen instead (a real design fork, priced in §7 as Option B) specifically to avoid re-opening this surface. Either choice touches something `DR-INV-frozen-surfaces` governs; there is no zero-touch path once dispatch/receipt/budget machinery this heavy is built. |
| 2. `harness.py` (event application) | **YES**, additively | A new `record_probe_transition` (or a generalized `record_capability_transition` that already accepts a `kind` discriminant) — same shape as `record_capability_transition`'s existing `expected` map, extended, not altered, for existing kinds. |
| 3. Replay-validation formats (`invariants.py`, `verification/`) | **YES** | New `capability-origin`-style checks for probe authority (mirroring the existing per-turn ceiling checks) and a new `verify_root` branch reading `ProbeExecutionReceiptV1` arithmetic — additive, but still surface-3 contact per the map's own definition ("their output shape is compared across runs and across time"). |
| 4. Manifest schemas AND validators (`run_manifest.py`) | **YES** | `ProbeCapabilityPolicyV1` joins `InquiryCapabilityPolicyV1`; the v6 gate needs its own conditional admit (mirroring `V6_RESEARCH_UNAVAILABLE`'s exact shape, `run_manifest.py:2869-2874`) — both the model AND the validator, per surface 4's own stated trap ("Reading a model and not its validator"). |
| 5. Qualification subject digests (`qualification.py`) | **YES**, once enabled | Adding `ProbeCapabilityPolicyV1` to the manifest moves the qualification subject digest the SAME way `ResearchCapabilityPolicyV1` did in 2026-07-28 ("this drifts the engaged preset digest and therefore invalidates cached qualifications — schedule it with a requalification window," `RESEARCH_BACKEND.md` Tranche 2). Disabled-by-default with `exclude_if` serialization (the same technique `ResearchCapabilityPolicyV1`/`ConfigRefereePolicyV1` already use, `SUB-capabilities.md` Traps) keeps every EXISTING home's digest untouched until an operator opts a run in. |

**Consequence:** this is not a small change. Every one of the five
frozen surfaces is touched by the full build, though four of the five
touches are ADDITIVE (new kind, new fields, new checks) rather than
alterations to existing recorded semantics — the discipline `DR-INV-
frozen-surfaces.md` itself distinguishes ("a change that alters what a
FUTURE run may do is ordinary work; a change that alters how a PAST run
verifies is a defect"). None of the five items above alter how an
EXISTING committed root replays. All five still require the explicit
operator approval `SUB-capabilities.md` names for "add a third
capability kind," and that approval is what this SPEC is stopping to
ask for, not assuming.

## 7. Decision sheet, priced

| Option | What it buys | Cost / risk | Recommendation |
|---|---|---|---|
| **A. Full capability-lifecycle apparatus** (§2-§4 as specified: pooled `CapabilityReplayState`, third kind, both access points, `probe_check` commitment) | Everything the amendment asked for: typed protocol, scratch exploration, critic-side execution-grade evidence, solo-run adjudication for LLM-limit claims | Largest option. Touches all 5 frozen surfaces (§6); the new criticism-side authority-publish/re-derive pair (§3.2) is genuinely new construction with no direct precedent to copy line-for-line, unlike §2/§3.1/§4.1 which are close mirrors of existing code; requalification window on first enable (§6 row 5); full gate + root-sweep instrument required before/after per `INV-frozen-surfaces.md`'s own protocol | **Recommended** — it is the only option that satisfies R5's explicit "TWO access points" requirement and R6's solo-adjudication requirement in full. Everything else below is a smaller, incomplete version of this. |
| **B. Non-pooled, standalone probe state** (same protocol, but its OWN `ProbeReplayState`/object-store namespace instead of extending `CapabilityReplayState`) | Avoids re-opening surface 1's EXISTING pooled-map hazard (`SUB-capabilities.md` Traps: "The replayed maps pool BOTH capabilities; a per-capability budget that counts them raw is wrong" — already a measured defect class for TWO kinds; a third kind widens the blast radius of that exact trap) | Still touches surfaces 2-5; duplicates transition-chaining/digest-chaining machinery `capabilities/state.py` already has, rather than reusing it — more NEW code, less reused code, but the reused code it avoids reusing is exactly the code carrying the known hazard | Worth pricing seriously at `dr-spec-change` time for the eventual build (not decided here) — trades "more code" for "does not compound a documented hazard." A `dr-plan-steps` phase should cost both A and B's actual diff size before choosing. |
| **C. Criticism path only (§3.2 + §4), no scratch access** | The part of R5 that changes what runs can DO (solo-run adjudication, R6) | Smaller diff (skips §3.1's scratch writer, one manifest ceiling, one wire field) but explicitly VIOLATES REQUEST.md R5 ("TWO access points... priced separately") and the amendment's own words ("Preferably reachable from scratch pad, as well as critics") | Not recommended as the shipped design — recorded because it is the cheapest subset if the operator later wants to phase delivery, not because it satisfies this tranche's request. |
| **D. Scratch-only (§3.1), no criticism/commitment path** | Cheapest possible slice — conjecturer exploration only, nothing execution-grade | Fails R6 entirely (no solo-run adjudication for LLM-limit claims — the operator's STATED motivating problem: "run without having to keep review only mode on for solo runs") | Not recommended — solves the least important half of the amendment for the least cost, in the wrong direction: the SCRATCH half was already the "advisory, no new law needed" half; the CRITICISM half is what the operator actually asked to broaden. |

**Sequencing note, if Option A is approved.** The dependency order this
SPEC's own sections expose: §2 (protocol) has no dependency and should
be built and gated first — everything else calls it. §3.1 (scratch)
depends only on §2 and is the cheaper of the two access points — natural
second step, with its own gate. §3.2 (criticism) depends on §2 and adds
the genuinely-new authority-publish/re-derive pair — third step, largest
single item. §4 (`probe_check` commitment + `crit_program` wiring)
depends on §3.2's dispatched receipts existing and is the step that
actually delivers R6's solo-adjudication promise — natural fourth and
final step. A `dr-plan-steps` phase for this build should very likely
be MULTIPLE tranches along exactly this boundary, each gated
independently, rather than one large diff — consistent with
`DR-INV-frozen-surfaces.md`'s diff-budget gate (Rung G1) and this
project's own recorded lesson against big-bang capability changes.

## 8. Recorded assumptions (SPEC's to make, per dr-spec-change's scope contract)

A1 (resolves REQUEST.md Q1): the probed model pool is DISJOINT from the
run's seated roles. `ProbeModelIdentityV1` (§2.1) is a frozen policy
field, never resolved through `select_lease`/`EndpointLease`'s
`(role, seat)` lookup (`CON-seats.md`) — the probe apparatus gets its
OWN narrow transport, following the qualification battery's own
precedent for a deliberate second dispatch path outside the ordinary
seat mechanism (`CON-seats.md`: "cli/doctor.py's qualification battery
... never calls select_lease... A real divergence from the ordinary
dispatch path, not an oversight to paper over"). This is the only
reading consistent with the seats/evidence guardrail (§4.3) and with the
amendment's own words ("isolated LLM").

A2: probe dispatch credentials are provisioned the same way the run's
OWN provider credentials are today (an operator-supplied endpoint/API
key outside the manifest, analogous to `ProviderProfileV1`) — the
ALLOWLIST is frozen in the manifest (§2.1), but the actual bearer
token/base URL wiring is deployment configuration, not a manifest field,
mirroring how `Route` carries `base_url`/`endpoint_id` but no credential
(`run_manifest.py:164`: "one exact provider route, with no credential
value"). Not designed further here — it is ordinary provider-profile
plumbing, not new epistemic machinery.

A3: `probe_check`'s predicate vocabulary (§5) is scoped to mechanical,
closed-form checks only, enforced at commitment-construction time (a
`model_validator` on the predicate spec, mirroring `ForbiddenCase`'s own
`model_validator`-not-`field_validator` lesson, `CON-conjecture-kinds.md`
Traps) — not left to be discovered as a policy question later. This is
recorded as an assumption because REQUEST.md R7 states the CONSTRAINT
("never rule on prose quality") but not the enforcement MECHANISM; the
enforcement mechanism is this SPEC's own choice.

## 9. What is explicitly out of scope here

Per C1/R12 — no `dr-plan-steps`, no code, no test. Also out of scope by
the amendment's own framing: general LLM-as-research-SOURCE access (the
superseded R3 framing) is not designed or recommended here; any future
"expand research to also cite third-party model output as EVIDENCE
directly" request would need its OWN spec, separately, since it (unlike
this apparatus) would put another model's prose into the run's ordinary
evidentiary graph and would need to satisfy the injection-posture rules
`RESEARCH_BACKEND.md` already states for fetched web text.
