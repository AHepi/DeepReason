# Audit: technologies and methodologies invented in this repository

Date: 2026-08-23. HEAD: `c06aca8d9`. Read-only — this tranche edits nothing
outside its own directory (dr-audit-orchestrator PRECEDENCE 3).

## Scope, method, and the one caveat that governs every row

**Not one of the family's five dimensions.** `dr-audit-orchestrator` routes
broken / dead / docs-drift / spec-drift / goal-trace. A provenance inventory is
none of those, so this runs as a sixth, read-only dimension under the family's
PRECEDENCE rather than pretending to be one of the five. That gap is itself a
finding (F1 below).

**What "invented here" is taken to mean, and what it is NOT.** A row qualifies
when the mechanism is *defined in this tree*, carries no external citation, and
is enforced by a committed check or test. That establishes **origination in this
repository**. It does **not** establish novelty in the world: no literature
search was run, and several of these have obvious neighbours in the wild
(content-addressed logs, capability tokens, literate-programming tests). Where a
row has a known external ancestor the row says so. Read every claim below as
"originated here, unverified against prior art".

**Scale it sits in:** 134,816 lines of Python across 34 packages, 315 test
files, 62 map documents carrying 992 executable checks, 142 experiment
tranches, 24 workflow skills, 85 typed record schemas.

---

## A. Epistemic-record technologies

### A1. The replay-verifiable typed record as the *only* admissible evidence

**What it is.** Every run is an append-only `log.jsonl` plus a content-addressed
object/blob store. `Harness` is the single writer: it validates, persists,
builds an `Event`, applies it to the materialized view, and appends — through
one `_commit`/`_apply_event` path shared **byte-for-byte with replay**.

**What it does.** Reopening a root reconstructs the same state the live session
held. That identity is what makes the log admissible evidence rather than a
diary, and it is the axiom the whole project rests on: "model prose is never
evidence" (CLAUDE.md).

**Evidence.** `src/deepreason/harness.py`; `DR-SUB-harness` "What it is", whose
check pins that the harness imports none of `rules`/`schools`/`scheduler`/`llm`
so the dependency arrow cannot reverse. Frozen surface 2.

### A2. `verify_root` — replay validation with typed findings

**What it is.** A read-only re-derivation that replays a root's log **twice**,
cross-checks every durable projection against the log that produced it, and
returns typed findings (`attempt-limits`, `standing-integrity`,
`adjudication-blindness`, …). `verification/report.py` re-channels the flat list
into five independent dimensions, of which only two decide validity.

**What it does.** Converts "did this run behave" from an opinion into a
recomputation. Two instruments may legitimately disagree, which is why the repo
rule is "always cite the instrument with the number".

**Evidence.** `src/deepreason/invariants.py::verify_root`;
`DR-SUB-verification`, whose check pins that `invariants.py` contains no
`write_text`/`write_bytes`/`open(`. Frozen surface 3.

### A3. Deterministic run identity — a run is a content address

**What it is.** Preparation digests the question, budget, provider profile,
frozen policy preset and evidence dossier into `run-<digest[:32]>`.

**What it does.** The same question under the same configuration lands on the
same directory on any machine at any hour. The consequence is deliberate and
sharp: a relaunch **cannot** silently pick a fresh root, so a leftover root must
be retired by an explicit rename — which is why the lifecycle has exactly four
legal moves (start, continue, amend, retire) plus one repair (finalize).

**Evidence.** `DR-CON-run-identity`; `src/deepreason/preparation.py`.

### A4. Amendment epochs — reshape the question without editing the record

**What it is.** After a run stops, `deepreason amend` appends a *new epoch*
chaining a reshaped question and/or additional evidence to the stopped root;
`continue` then resumes it.

**What it does.** Solves "inject more content and reshape the central question
after a stop, with zero corruption of the ledger" without ever editing a
committed byte. The insight is stated in the proposal: the harness already
treated *answers* as supersedable epochs, so the question and the evidence
dossier are made supersedable by the identical mechanism.

**Evidence.** `docs/proposals/AMENDMENT_EPOCHS.md` (status: implemented,
validated against itself as its own specification); `src/deepreason/amendment/`.

### A5. Two-axis epistemic state — `status` and `standing`

**What it is.** `status` is truth-standing under criticism (is every attack
defeated?). `standing` is role in the economy of generation (is this artifact
one retrieved neighbour, or the coordinate system a whole scope is written in?).
`standing(b)` is a **derived** relation — nothing is stored.

**What it does.** Makes representable the ordinary condition of mature science:
an artifact can be refuted and still framing. A single-axis system cannot
express that.

**Evidence.** `DR-CON-standing-and-background`;
`src/deepreason/calculus/standing.py`; `tests/test_calculus_standing.py`.
**Ancestry, stated:** the two-axis idea is the central contribution of
`docs/COMPUTABLE_CALCULUS.pdf`, which is **operator-supplied theory**. The
implementation, the derived-not-stored decision, and the `standing-integrity`
replay check are this repo's.

### A6. Warrant-and-attack-edge as the only route to REFUTED

**What it is.** Nothing is refuted by being disliked. `Status.REFUTED` is
reachable through exactly one chain: an artifact *carries* a registered
`Warrant` naming a target → carriage materializes an attack edge in `att` → the
grounded extension finds the attacker accepted.

**What it does.** Separates *who may mint a warrant* from *what a warrant does
to the graph*, so no rule can reach a Status except by first putting an
attackable object on the record.

**Evidence.** `DR-CON-warrants-and-attacks`; `src/deepreason/rules/warrants.py`,
`src/deepreason/adjudication/`. **Ancestry:** grounded extensions are Dung's
argumentation semantics (external). The carriage mechanism and the mint-site
guard separation are this repo's.

---

## B. Provider-boundary technologies

### B1. The route lease and the seat firewall

**What it is.** A **seat** is a `(role, seat-index)` pair. `select_lease`
resolves it to an `EndpointLease` that permanently binds that seat to one
immutable `Route` — model, endpoint, provider, family, reasoning, temperature,
output mechanism. `lease.verify(endpoint)` runs immediately before **every**
dispatch and fails closed if code mutated or substituted the endpoint.

**What it does.** Makes "which model answered this" a fact of the manifest
rather than of runtime state, and makes route substitution structurally
impossible rather than merely discouraged.

**Evidence.** `src/deepreason/llm/firewall.py::EndpointLease`, `select_lease`,
`route_fingerprint` (the last treated as frozen-adjacent because recorded roots
depend on its exact serialization); `DR-CON-seats`.

### B2. The model-control-field firewall

**What it is.** Before any validator sees a model response, every field name in
it is checked against `FORBIDDEN_MODEL_CONTROL_FIELDS` — `model`, `endpoint`,
`provider`, `route`, `tool`, `command`, `delegate`, … — and rejected outright.

**What it does.** Enforces the boundary that model output is *untrusted
transport*: it may fill fields in a contract, and it may not choose a route,
name a tool, delegate, or set a status. Rejection happens at the field-name
level, so a novel attack does not need to be anticipated semantically.

**Evidence.** `src/deepreason/llm/firewall.py:26`,
`reject_model_control_fields`; `tests/test_model_firewall.py`.

### B3. Wire contracts, alias tables, and the bounded repair protocol

**What it is.** A *wire contract* is a closed schema plus a compiler from wire
value to canonical model. An `AliasTable` is an immutable, call-local mapping
held **outside** the model response, so the model manipulates opaque local
handles (`ART_1`, `B3`) rather than real ids. `BoundedRepairSession` /
`V6PatchRepairSession` are finite state machines: one initial generation, then
at most a whole-object correction and one smallest-subtree repair.

**What it does.** Bounds the conversation in every direction at once —
what may be said, what may be named, and how many times it may be retried.
`tolerant_patch_value` absorbs exactly the spellings that cost no information
(a container that could never be a valid patch, bytes the harness itself sent)
and refuses those that would mean inventing a value.

**Evidence.** `src/deepreason/llm/wire.py::WireContract`, `AliasTable`;
`src/deepreason/llm/repair.py`; `DR-SUB-llm`;
`tests/test_llm_repair_capabilities.py`.

### B4. Reserve–settle token metering

**What it is.** `TokenMeter.reserve()` books a conservative upper bound
(`ceil(chars/3)` prompt estimate plus the transport `max_tokens`) **before**
dispatch; `Reservation.settle()` replaces it with provider-reported usage;
`release()` returns it untouched when usage is unknown. All transitions under
one lock.

**What it does.** Concurrent dispatchers can never jointly overshoot a hard
ceiling, and an *unboundable* call fails closed rather than being dispatched
against a finite budget.

**Evidence.** `src/deepreason/llm/budget.py`; `tests/test_budget.py`.

### B5. The pack IR and the presentation/epistemics separation

**What it is.** A *pack* is the model-facing body of one call, assembled
deterministically from epistemic state as a **section-aware IR**: parts declare
priorities and per-section droppable/compressible flags, and the allocator
spends budget on optional parts while retaining mandatory ones in full.

**What it does.** Solves a specific hazard the document names outright: *a byte
cut for cost is indistinguishable, from the model's side, from a byte that never
existed*. The one place presentation could have become epistemic — clipping a
critic's target — was closed by making that section mandatory.

**Evidence.** `DR-CON-packs-and-token-economy`; `src/deepreason/llm/packs.py`,
`profiles.py`; `docs/TOKEN_ECONOMY.md`.

### B6. The split-budget seat protocol (2026-08-23, this session)

**What it is.** One seat call becomes two provider legs on the same route, lease
and authorization: a free-prose deliberation leg at `B_r` allowed to be
truncated, then a non-thinking emission leg at `B_a` fed the possibly-truncated
trace. `B_r + B_a == ceiling` by construction.

**What it does.** A reasoning model that spends its whole cap on hidden
reasoning now yields an answer instead of an empty seat failure.

**Evidence.** `src/deepreason/llm/split.py`;
`tests/test_split_budget_protocol.py` (22 tests);
`experiments/2026-08-22-change-two-call-seat-protocol/`.
**Ancestry, stated plainly:** the *finding* is external — the coupling tax and
delayed-structure results in `docs/RESEARCH_FINDINGS_Q1Q10_2026-08-22.md` (Q7)
and `docs/RESEARCH_STRUCTURED_OUTPUT_COERCION_2026-08-22.md`, both
operator-supplied and unverified here. What is this repo's: taking `B_a` *out
of* the ceiling so the lease bound cannot be escaped, the six typed stand-down
notices, and the per-attempt record of which leg produced what.

---

## C. Process and control-plane technologies

### C1. The v6 transactional work lifecycle

**What it is.** No provider call happens without first passing a chain the
workflow package authored: **preparation → token reservation → context exposure
receipt → dispatch authorization**; and no result becomes an effect without a
typed **semantic admission** or **terminal** it authored. The chain is
append-only and reference-only.

**What it does.** A crashed run resumes from the record alone — recovery
modules re-derive an admission from the raw blob a `ProviderAttemptV1` already
names, with the provider boundary *deliberately absent* so recovery cannot
re-dispatch. The package owns no semantics: it never reads a conjecture, scores
a criticism, or moves a status.

**Evidence.** `DR-SUB-workflow`, whose check pins that the package opens **no
file at all** and that the recovery modules import no `llm.endpoints`;
`src/deepreason/workflow/transaction_service.py`, `replay.py`.

### C2. The capability lifecycle — intent is semantic, everything operational is code-authored

**What it is.** The only way a run reaches outside its own reasoning is a
*capability* (run a program, fetch a document). The model may express **semantic
intent and nothing else**; toolchain, runner profile, wall-clock and memory
bounds, domain allowlist and request ceiling are code- or manifest-authored.
Intent becomes action across a ten-state machine: `PROPOSED → VALIDATED →
GRANTED|DENIED → COMPILED → DISPATCHED → SUCCEEDED|FAILED → RESULT_PACKAGED →
CONSUMED`, one typed digest-linked transition per step.

**What it does.** A run's entire outside contact re-derives from the log.

**Evidence.** `src/deepreason/capabilities/enums.py::CapabilityLifecycle` (ten
states, confirmed); `DR-CON-capability-lifecycle`. Frozen surface 1.

### C3. Schools — islands in conjecture, panmixia in criticism

**What it is.** A school is a persistent conditioning regime: a named stance
from a fixed library plus the lineage of artifacts carrying that school id.
From manifest v4 a school may additionally be **bound** to a frozen route seat.
The roster is a deterministic function of the log; rotating a laggard is
*succession* (a new artifact plus a `Reseed` event), never deletion.

**What it does.** Lets rival research programmes compete inside one run instead
of one voice mutating its own echo. Two authorities are deliberately separate:
the **stance** is prompt material and grants nothing; the **binding** is
manifest-owned routing no prompt can move.

**Evidence.** `DR-CON-schools`; `src/deepreason/capture/schools.py`,
`llm/firewall.py::resolve_school_role_lease`.

### C4. The scratchpad — a place the model may be wrong on purpose

**What it is.** An immutable, replayable graph of notes, links, clusters and
guides, retrieved under a budget, rendered behind **opaque local handles** via a
render receipt, and admitted back without ever becoming evidence.

**What it does.** Gives speculation, counterfactuals and outright
contradictions somewhere to live that carries no warrant, status, attack edge
or support. Enforced structurally: the package's entire dependency set is
plumbing, and the map's check is an **allowlist** rather than a denylist,
"because a denylist only forbids what someone already thought of".

**Evidence.** `DR-SUB-scratch`; `src/deepreason/scratch/`.
**Trap this produced:** render-receipt handle maps reload key-sorted
(`B1, B10, B2`), so comparisons must go through `ordered_refs`, never
`.values()` (`scratch/render.py:123`; CLAUDE.md invariants).

### C5. The grounded bridge — turning a record into prose without changing it

**What it is.** A bridge opens at one exact event fence, extracts a bounded
evidence pack, makes the model write a **claim ledger** (one row per claim, each
carrying an epistemic class and canonical backing references), composes the
answer *out of ledger rows only*, validates every span against its row's class,
has a second seat review the grounding, and runs a bounded repair kernel when
review fails.

**What it does.** Makes "the final answer" a derivation from the record rather
than a fresh act of authorship. Bridge events contribute no artifacts, warrants,
edges, statuses or adjudication inputs, and the event ontology **refuses** any
process event carrying a non-empty `StateDiff`. `verify_root` replays the log
twice and fails if the two bridge states differ.

**Evidence.** `DR-SUB-bridge` (its check pins both refusal messages verbatim);
`src/deepreason/bridge/`.

### C6. Qualification: subject digests and a tier ladder

**What it is.** Before a run may use a model, a battery certifies it can fill
each role. The result is cached against a **subject digest** over the manifest,
the pair inventory and the provider profile. Tiers: `full` (a completed reusable
bundle, every frozen route/contract pair qualified), `shallow` (a six-case
fitness battery against the MiniReason compact contract), `unqualified`.

**What it does.** Same home + same profile + same opt-ins is a ~1s cache hit;
change any input and the ~14-minute, ~1,160-call battery re-runs. Certification
is thereby bound to *exactly* what was certified.

**Evidence.** `src/deepreason/qualification.py::qualification_subject_digest`,
`QualificationTier`, `SHALLOW_FITNESS_CASES`. Frozen surface 5.
**Trap this produced, this week:** `Config` reaches the subject *indirectly*
through the manifest's `engine_config_json`, so a new `Config` field silently
moves every digest unless dropped in `_versioned_source_config_data` — eight
knobs already sit in that drop list (`docs/ERRATA.md` E44).

### C7. Typed disclosure instead of compile-time refusal

**What it is.** `CompileNoticeV1` — "a configuration choice a prior gate would
have refused at compile time. Notices describe what the retired gate would have
said; they never block compilation."

**What it does.** Implements the operator law *all configurations should be
allowed*: any input that parses into the configuration model compiles, and what
used to be a refusal becomes a recorded notice or a deterministic resolution
rule. Impossibility still surfaces — typed, at the point of use.

**Evidence.** `src/deepreason/run_manifest.py:1191`;
`experiments/2026-08-12-change-all-configs-allowed/`. The same shape recurs in
the split protocol's stand-down notices (B6) and the signal contract's
"allocation open-loop for signal X" (C8).

### C8. The signal registry as a contract

**What it is.** A signal is a *declaration* — name, unit, producer-agnostic
semantics, staleness bound — keyed by **seat instance**, not role. The
allocation controller consumes only the interface. `SIGNALS` and `PREFIXES` are
**derived** views of `SIGNAL_DECLARATIONS`, because "two hand-maintained copies
of one fact is how a registry stops being a contract".

**What it does.** New setups add signals by declaration, never by teaching a
consumer about a subsystem. Three layers with different change costs: FROZEN
(the protocol, including *allocation touches efficiency, never evidence*),
VERSIONED (registry and policy algorithm), FREE (parameter values).

**Evidence.** `DR-INV-signal-contract`; `src/deepreason/signals.py`,
`allocation.py`; `tests/test_signal_contract.py`.

---

## D. Verification and documentation methodologies

### D1. Documentation authenticated by re-derivation — the strongest invention here

**What it is.** Every load-bearing claim in `docs/map/` carries a shell command
at column 0 that must exit 0. `tools/docs_verify.py` re-runs all of them.

**What it does.** In the tool's own words: *"A map document is authenticated by
RE-DERIVATION, not by a signature… A signature would prove who wrote a
sentence; this proves the sentence is still true, which is the property that
actually decays."* Sub-modes make the method self-policing: `--audit` flags
checks that **cannot fail** (a vacuous check is worse than an admitted gap,
because it reports success), `--links` resolves every cross-reference,
`--coverage` finds enforcement sites a seam omits, `--stale` lists documents
whose owned files moved, and `--self-test` verifies the tool's own parsing.

**Scale.** 62 documents, 992 checks.

**Evidence.** `tools/docs_verify.py`; `docs/map/SCHEMA.md` ("The one rule").
**Ancestry:** literate programming and doctests are the obvious neighbours;
what is distinctive here is that the checks authenticate *architectural claims*
about a 135k-line tree, and that `Verified-at:` may be advanced only if the
checks were actually re-run — "a stale stamp is honest, a false one is not".

### D2. The blast-radius disclosure gate

**What it is.** Given a proposed change's declared target files and symbols,
`tools/blast_radius.py` computes frozen-surface contacts, reachability changes,
consumers (tests, map checks, the qualification digest, wheel-smoke pins) and a
plain-language disclosure summary.

**What it does.** Makes an authorization request impossible to hand-summarize
from memory. The docstring names the failure it closes: seven recorded cases of
an authorized change hiding architecture the request never disclosed —
including one where a tranche's own SPEC.md had already found a frozen-surface
contact *in prose* and the STOP that finding should have forced never happened.
Every fact the gate reports was statically derivable at grant time in all seven;
the gate *is* that derivation, run mechanically.

**Evidence.** `tools/blast_radius.py`;
`experiments/2026-08-10-change-blast-radius-analysis/CENSUS.md`. Its own tiering
(`DIRECT` vs `SYMBOL_INDIRECT`, each carrying "grep-based; not proof of semantic
contact") is what lets a measured false positive be *rowed* rather than
escalated.

### D3. The actual-diff budget gate

**What it is.** `tools/diff_budget.py` measures **real cumulative insertions**
against a ledgered ceiling — not a plan-time estimate.

**What it does.** Closes a recorded failure: a tranche overran its budget twice
because the ceiling was checked against the spec's own headline estimate, and
the headline understated its own itemization by ~135 lines. Insertions only —
"a budget ceiling bounds what is ADDED". The docstring even records the trap
that `git diff` is blind to files git has never seen, which is exactly the miss
that occurred in this week's tranche.

**Evidence.** `tools/diff_budget.py`.

### D4. The probe rule for record observables

**What it is.** Any check reading the typed record must **assert an attribute
exists before reading it**, and treat absence as valid.

**What it does.** A missing attribute otherwise returns a falsy default
"indistinguishable from a real measurement" — a sweep would report a clean bill
for data it never read.

**Evidence.** `tools/root_sweep.py` header. (The sweep itself was **retired** by
operator ruling 2026-08-22; the probe rule outlived it and now governs any
observable-reading check.)

### D5. Two append-only errata ledgers, one for code and one for process

**What it is.** `docs/ERRATA.md` (45 entries) records corrections to committed
*document claims* — so a reader knows which sentences have already been found
wrong. `docs/ERRATA_EXECUTOR.md` (16 entries) tracks **the process, not the
codebase**: the infrastructure built so a less capable model can operate the
harness.

**What it does.** Makes documentation failure a first-class, accumulating
record. The genuinely reusable pattern that emerges from it: *a claim can carry
a passing check and still be false, when the check pins a neighbouring
assertion* (E43, and E44 this week).

**Evidence.** `docs/ERRATA.md`, `docs/ERRATA_EXECUTOR.md`.

---

## E. Agent-operation methodologies

### E1. The three workflow families with a verbatim authority ledger

**What it is.** 24 skills in three families — `deepreason-orchestrator`
(defects), `dr-change-orchestrator` (changes), `dr-audit-orchestrator`
(read-only audits) — each a fixed phase sequence where every phase owns exactly
one artifact, and where the authority is the operator's **verbatim words**
ledgered in `REQUEST.md` as numbered requirements that every later artifact must
cite.

**What it does.** Prevents scope creep, missed steps and forgotten inputs
across long agent sessions. Two rules do most of the work: **cross-routing is
strict** (a defect found mid-change is PARKED, not fixed; a change wished for
mid-defect is PARKED, not implemented), and **a requirement is never deleted**,
only marked superseded — so a fresh session resumes from committed artifacts
with no conversation history.

**Evidence.** `.claude/skills/`; `CLAUDE.md` "Which workflow to use".

### E2. Park-with-prompt

**What it is.** Anything noticed but out of scope goes to `PARKED.md` as one
line of WHAT plus a **ready-to-send prompt** — route, one-goal statement,
evidence pointers, end state — written at park time, for its future runner.

**What it does.** Makes the follow-up cost the operator *a paste*, not an
authoring session. Distinct from an ordinary backlog: the unit is an executable
instruction, not a wish.

**Evidence.** `dr-change-orchestrator` scope contract; every tranche's
`PARKED.md`.

### E3. Mutation-proving as a shipping requirement

**What it is.** Before a test, map check or probe is written down, the guarded
thing is broken, the check is watched go red, and it is restored. For equality
tests a **permanent companion mutation test** ships alongside.

**What it does.** `docs_verify --audit` catches vacuous *checks*; nothing
catches a vacuous *test* but this rule. Five supporting rules make the artifacts
durable: pin to committed immutable evidence; anchor to meaning not form (never
pin line numbers); compare typed outcomes with wall-clock scrubbed
**recursively**; tolerate absence in old records.

**Evidence.** `dr-execute-step` "Durable tests, checks, and probes", each rule
citing the incident that paid for it (`docs/ERRATA.md` E7, commit `863a0fa3`).

### E4. The skill tripwire — a workflow must earn its existence

**What it is.** Before a skill is written, the task is run three times without
it; a dedicated workflow is authorized only after **two recorded recipe
failures**.

**What it does.** Stops process from accreting faster than the thing it
governs. Compression of a skill is a separate, re-gated pass, and *a model swap
reopens the gate*.

**Evidence.** `.claude/skills/authoring-skills/SKILL.md` E1/E2/L2.

### E5. Operator-facing explanation as a checked discipline

**What it is.** Every operator-facing message answers the actual worry in the
first sentence, glosses each technical term in-line, states what a scary finding
does **not** mean before what it does, prices forks as real-world roads with a
recommendation, and closes a final output with exactly one everyday analogy.

**What it does.** Recorded verbatim from the operator and treated as binding,
including on intermediary messages — the anti-pattern it names is "five terse
updates followed by one polished summary", because the intermediaries are when
the operator decides whether to intervene.

**Evidence.** `.claude/skills/dr-explain-to-operator/SKILL.md`; CLAUDE.md
Conventions.

### E6. Honest-ledger experiment narrative

**What it is.** Each tranche's `RESULTS.md` carries dated segments recording
what the record shows **and the residue** — what remains unproven. A negative or
inconclusive result is recorded as one. "Accepted does not mean true."

**What it does.** Makes superseding a prior finding a normal, visible move
rather than a quiet edit — this week's tranche has one segment explicitly marked
"SUPERSEDED next segment. Written from a defective tree."

**Evidence.** CLAUDE.md Conventions; 142 tranche directories.

---

## What is NOT invented here (stated so the boundary is falsifiable)

| Imported | Where it enters |
|---|---|
| Popperian critical rationalism; conjecture/criticism, no induction, no confirmation | the whole design premise; `docs/harness-spec-v1.3.md` |
| Dung argumentation semantics — grounded extension, labelling | `adjudication/`; named as external in `POIETIC_CALCULUS_v0.1.md` §1 |
| Deutsch's epistemology; Marletto/Deutsch constructor theory | `docs/POIETIC_CALCULUS_v0.1.md` strata Φ/Ε/Δ |
| The Computable Calculus, incl. the two-axis status/standing contribution | `docs/COMPUTABLE_CALCULUS.pdf` — **operator-supplied**, authoritative original |
| Verbalized Sampling (2510.01171) | `harness-spec-v1.3.md` §11.6; `VS_K` |
| The coupling tax; delayed-structure / two-call; PhantomFill coerced fabrication; judge-order bias; cosine novelty thresholds | the six `docs/RESEARCH_*_2026-08-22.md` notes, each headed "Operator-supplied … EXTERNAL and unverified by this repository's instruments" |
| Content-addressed storage, Merkle-style digest chaining | `storage/objects.py` |

The repo's own discipline for this boundary is worth noting as a methodology in
its own right: every external note is committed **verbatim below a rule**, with
"design intelligence, never evidence" stamped on it, and a separate
"Consumption points" section naming which decision each finding may touch.

---

## Findings

**F1 — the audit family has no provenance dimension.** This report had to be
run as a sixth dimension outside the five the router knows. If provenance
questions recur, that is a missing worker (`dr-audit-provenance`), and the
`authoring-skills` E1 tripwire says it needs two recorded failures first — this
is one.

**F2 — novelty is unestablished, only origination.** No row here is checked
against prior art. Several inventions (D1, D2, B4) have plausible external
neighbours. A claim of novelty would need a literature pass this audit did not
run, and per the honest-ledger rule that absence is recorded rather than
papered over.

**F3 — the strongest inventions are the boring ones.** By count of downstream
consequence, the three carrying the most weight are D1 (992 executable checks
authenticating a 135k-line tree), A1/A2 (the record and its re-derivation), and
C1 (no provider call without recorded authority). Everything epistemic in the
project stands on those three.

## Gates (PRECEDENCE 1 and 3)

Committed run roots read, never written; this tranche's diff names only its own
directory. Pasted in the delivery message.
