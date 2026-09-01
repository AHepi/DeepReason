# Request: "Take this particular task out of the hands of the machine"
Captured: 2026-09-01, executor window "CHANGE TRANCHE: model profile registry",
from the operator's messages of 2026-09-01 as relayed verbatim in that window.

Status: capture phase complete. Nothing below is interpreted; the monitor's
reading is quarantined in its own section and is NOT operator authority.

## Map preflight (recorded here so every later phase starts from the same map)

Resolved from `docs/map/INDEX.md`, read in the order `dr-drive-harness` §4
prescribes (INDEX -> INV-frozen-surfaces -> seam -> subsystems):

| id | document | why it is in scope |
|---|---|---|
| `DR-INV-frozen-surfaces` | `INV-frozen-surfaces.md` | read FIRST; owns the five surfaces and the two instruments |
| `DR-SEAM-llm-x-manifest` | `SEAM-llm-x-manifest.md` | seam read BEFORE either side; coupling 24 |
| `DR-SEAM-llm-x-verification` | `SEAM-llm-x-verification.md` | what `attempt_trace` MEANS to its only reader; the split-leg recording precedent |
| `DR-SEAM-llm-x-workflow` | `SEAM-llm-x-workflow.md` | coupling 33; where split-leg records land |
| `DR-SEAM-llm-x-scheduler` | `SEAM-llm-x-scheduler.md` | route lease vs allocation controller |
| `DR-SUB-llm` | `SUB-llm.md` | owns `llm/providers.py`, `llm/split.py`, profiles, wire contracts |
| `DR-SUB-manifest` | `SUB-manifest.md` | RunManifest schema + validators + qualification. **Frozen** |
| `DR-CON-seats` | `CON-seats.md` | `select_lease`, `EndpointLease`, the one-profile-per-run mint |
| `DR-CON-packs-and-token-economy` | `CON-packs-and-token-economy.md` | section allocation and budgets (the 512-token extraction budget) |

**Map gap found at preflight, recorded as a finding rather than a blocker**
(`dr-drive-harness` §4 step 5): the seam matrix in `INDEX.md` carries NO row for
`llm x qualification` in any form -- not a documented pair, not a dash, not a
"not yet written" entry. It is absent from the table entirely, which by that
table's own stated convention means "no measured import traffic at all", not
"uninteresting". `llm x split` is intra-package (both files are owned by
`DR-SUB-llm`) and therefore has no seam document by construction. Both facts
are inputs to M8 below, not conclusions about it.

## Verbatim

The operator's words of 2026-09-01, in the order given, each quoted whole.

Position 1 -- the operator's suspicion about the cause:

> "I suspect it has something to do with an incorrectly coded GLM 5.3
>  endpoint. For example, writing none for thinking instead of low."

Position 2 -- the operator's proposed remedy and its reason:

> "Would this work for all unknown models as well? Surely creating agent.md
>  would be better. Take this particular task out of the hands of the
>  machine because we don't really know what future LLMs settings will be?"

Position 3 -- the operator accepting the monitor's proposal:

> "ok next prompt"

## Requirements

Each keeps the operator's own words. Kind is `behavior` (code must act
differently), `artifact` (a file/document must exist), or `process` (how the
work must be done).

R1 (behavior): "an incorrectly coded GLM 5.3 endpoint. For example, writing
   none for thinking instead of low."
   -- the value the harness sends for GLM 5.3's thinking knob must stop being
   the wrong one.

R2 (behavior): "Would this work for all unknown models as well?"
   -- whatever is built must have a defined, working behaviour for models the
   harness does not know.

R3 (artifact): "Surely creating agent.md would be better."
   -- the remedy the operator asks for is a DOCUMENT, not a code fix.

R4 (behavior + process): "Take this particular task out of the hands of the
   machine"
   -- deciding a model's settings must not be the machine's job.

R5 (constraint on design): "because we don't really know what future LLMs
   settings will be?"
   -- the design may not rest on knowing what a future model's settings are.

R6 (process): "ok next prompt"
   -- the operator has accepted the monitor's proposal (reproduced verbatim in
   the next section) and authorised this tranche to proceed on it.

## Monitor's operational reading -- NOT the operator's words

Reproduced verbatim from the executor window. The window itself labels this
"MONITOR'S OPERATIONAL READING (not the operator's words; REQUEST.md must keep
the two separate)". It is authority for the shape of the work only because R6
accepts it; where it and the operator's words could diverge, the operator's
words in the section above win.

> "The harness must never GUESS a model's settings. Per-model facts -- which
>  reasoning values the provider accepts, which is "most off", whether
>  thinking can be disabled at all, where the trace lands, measured speed,
>  whether the model can obey "respond more compactly", transport quirks --
>  live in a REGISTERED, VERSIONED, HUMAN-AUTHORED artifact, one per model,
>  authored only by the operator or the monitor. The harness READS it. A
>  model with no profile runs with every knob OMITTED (provider default),
>  the split protocol stands down for that seat, and the run carries a typed
>  "model-profile-missing" notice: disclose, never refuse, never send a value
>  the profile does not declare. Each profile carries the date it was
>  measured and a re-runnable probe that re-verifies its key claims, so a
>  stale profile fails a CHECK rather than a RUN."

### Monitor's proposed decomposition (M1..M8)

Numbered M-, not R-, so that no later artifact can mistake the monitor's
decomposition for the operator's words. The window states: "SPEC.md may refine
but every item traces to a REQUEST.md requirement number" -- the trace column
is that mapping.

| id | monitor's requirement (abridged; full text in the window, quoted below) | traces to |
|---|---|---|
| M1 | a model-profile registry: one versioned document per model id, typed schema (loader + validator), documented location, named minimum field set | R3, R4, R5 |
| M2 | the harness consumes profiles ONLY through a declared interface; `providers.py`/`split.py` become READERS; hard-coded `REASONING_OFF` retired; extraction leg sends the profile's most-off value, never a literal | R1, R4 |
| M3 | unknown model: knob omitted, split stands down with a typed notice, `model-profile-missing` on the record, no refusal anywhere | R2, R5 |
| M4 | never send an undeclared value: an out-of-set `reasoning:` compiles with a typed disclosure and is replaced by the nearest declared value -- OR STOP AND ASK if that silent substitution violates "deterministic yet configurable" | R1, R4 |
| M5 | profiles for every model with committed live evidence, glm-5.3 first; every declared value cites the record that measured it; nothing declared from memory | R1, R3 |
| M6 | a live probe script that exercises each declared reasoning value and exits non-zero when a profile claim fails; wired so qualification or preflight can run it per seat and record the result typed; STOP with a priced disposition if that wiring touches frozen surface 5 | R3, R5 |
| M7 | an architecture test that goes RED if any consumer reads a model-specific setting from outside the registry interface, and RED if adding a model requires a source edit; shown RED against a planted bypass, then GREEN | R4 |
| M8 | map: a new CON-/SUB- document with re-runnable `check:` lines, updated seam entries for llm x split and llm x qualification, INDEX.md routing, in the SAME commit as the code; Traps entry naming P-S1 (M-1, M-16) and P-A1 run 4565139800f5ca02 | R3, R4 |

The monitor's requirement texts, verbatim from the window, so that no later
phase works from the abridgement above:

> "R1  A model-profile registry: one versioned document per model id, with a
>     typed schema (loader + validator) and a documented location. Fields at
>     minimum: provider wire vocabulary for the reasoning knob (accepted
>     values; the most-off value; whether thinking is disablable; where the
>     trace lands per value), context window, max output, measured tokens/s,
>     can_compact (can it obey "respond more compactly"), transport notes,
>     measured-on date, evidence pointers, and a probe command.
>  R2  The harness consumes profiles ONLY through a declared interface.
>     providers.py and split.py become READERS of the registry; the
>     hard-coded REASONING_OFF is retired. The extraction leg sends the
>     profile's most-off value, never a literal.
>  R3  Unknown model (no profile): knob omitted, split stands down with a typed
>     notice, "model-profile-missing" typed notice on the run's record. No
>     refusal anywhere (all-configurations law, 2026-08-12).
>  R4  Never send an undeclared value: a run-config `reasoning:` value outside
>     the profile's accepted set compiles with a typed disclosure and is
>     replaced by the profile's nearest declared value -- or, if you judge that
>     silent substitution violates "deterministic yet configurable", STOP and
>     ask; do not decide it alone.
>  R5  Profiles for every model with committed live evidence: glm-5.3 FIRST
>     (most-off = low; not disablable; can_compact = false per M-16; the
>     ~300 s transport drop at max effort from P-A1), then deepseek-v4-pro:0813,
>     qwen3.5:397b, gpt-oss:120b (cannot disable; low/medium/high only, per
>     Ollama docs), glm-5.2. Every declared value cites the record that
>     measured it; nothing is declared from memory.
>  R6  A live probe script (tokens are cheap): for one model id, send each
>     declared reasoning value on a fixed prompt N times and report clean-
>     content rate, trace location, completion tokens, latency; exit non-zero
>     when a profile claim fails. This is the profile's `check:`. Wire it so
>     qualification or preflight can run it per seat and record the result
>     typed; if that wiring touches frozen surface 5 (qualification.py), STOP
>     with a priced disposition -- do not edit it.
>  R7  Architecture test (modularity law: "enforced means a check that can
>     fail"): RED if any consumer reads a model-specific setting from anywhere
>     but the registry interface, and RED if adding a new model requires a
>     source edit. Show it RED against a planted bypass, then GREEN.
>  R8  Map: a new CON- or SUB- document for the registry with re-runnable
>     single-line `check:` lines, updated SEAM entries for llm x split and
>     llm x qualification, INDEX.md routing, in the SAME COMMIT as the code.
>     Traps entry naming P-S1 (M-1, M-16) and P-A1 run 4565139800f5ca02."

### The evidence the monitor cites for "what it replaces" (verbatim)

> "- `src/deepreason/llm/providers.py:70` REASONING_OFF = "none", a constant,
>    hard-coded onto every extraction leg by `llm/split.py:163`. No config
>    value can change what that leg sends -- a modularity-law violation on its
>    own.
>  - Ollama's glm-5.3 page: reasoning_effort accepts low / high / max, default
>    max. "none" is not in the set. P-S1 measured what "none" does on glm-5.3
>    (branch claude/deepreason-p-s1-commitments-wowcib,
>    experiments/2026-08-31-p-s1-commitments/SEAT_REASONING_FINDINGS.md):
>    0/8 clean at none, 8/8 clean at low.
>  - P-A1 re-ran that exact failure: every glm-5.3 extraction-leg blob opens
>    with thinking prose, cut at 512 tokens, then the cap ratchet exhausted the
>    seat. experiments/2026-09-01-live-all-modules-p-a1/MONITOR_REVIEW.md on
>    main (addendum) has the seq numbers and commands.
>  - MISTAKES.md M-1 and M-16 on the P-S1 branch: glm-5.3 cannot shorten its
>    output on request; the same inability has now killed three runs.
>  - providers.py's own docstring calls itself "the model-change seam" where a
>    model "gains its quirks by adding one entry" -- i.e. a code edit. That is
>    the thing being retired."

Every one of these is a CLAIM TO BE RE-DERIVED in `dr-spec-change`, not a fact
this phase may assume. Line numbers especially: they are the monitor's, taken
from a branch state, and must be re-checked against this branch's HEAD.

## Standing constraints

C1 (branch): "Develop on branch `claude/model-profile-registry-opkgal`" and
   "NEVER push to a different branch without explicit permission" -- window
   preamble.

C2 (frozen surfaces, forecast obligation): "FROZEN SURFACES -- forecast BEFORE
   the first edit, in SPEC.md: If the profile id/digest must be stamped into
   the run manifest for replayability, that is surface 4 (run_manifest.py)
   contact and moves manifest and qualification identities. Measure the price
   the way the compile-gap tranche did (its price_compile_gap.py is the
   template) and PRICED STOP before editing. An alternative that records the
   profile digest as a typed log event without a schema change avoids the
   contact; prefer it if it preserves replayability, and say why in SPEC.md."

C3 (frozen surfaces, hard no-touch): "qualification.py (surface 5),
   capabilities/state.py, harness.py, invariants.py, verification/, and the
   frozen-adjacent route_fingerprint in llm/firewall.py: NOT touched. Any
   contact is an immediate stop."

C4 (read-only): "Committed run roots and the P-S1 / P-A1 branches: read-only."

C5 (out of scope -- park, do not fix): "F4: one seat's exhaustion kills the
   run; failed terminal not continuable. F6: the ~300 s transport wall and
   blind identical retries in llm/endpoints.py::request_with_retries.
   SPLIT_BUDGET_EXTRACTION_TOKENS default 512 being too small for the
   conjecturer schema (a config-default question; note it in PARKED.md).
   Any new live reasoning run."

C6 (validation): "Mutation proofs RED/GREEN committed for R2, R3, R7. Full
   gate; 0 failed is the target. Pre-authorized known-not-yours baselines,
   record them, do not stop on them: the `bc`-dependent map check (container
   has no bc), and
   test_the_shipped_qualification_subject_digest_does_not_move (container
   toolchain-path digest). Anything else red is yours to explain or fix."

C7 (delivery): "DELIVERY.md reconciles requirement by requirement against the
   operator's verbatim words above."

C8 (stop conditions): "STOP AND ASK: R4's substitution question; any
   frozen-surface contact; any need to edit a committed root; and the
   registry's on-disk location and document naming if the map's SCHEMA.md does
   not already settle it (the operator said "agent.md"; the monitor suggested
   "model profile" because "agent" already names executor windows here -- the
   operator decides)."

C9 (standing repo law, not restated here): CLAUDE.md's operator design laws
   bind this tranche in full. The four that bear directly on it are the
   all-configurations law (2026-08-12: everything that parses compiles;
   impossibility surfaces at the point of use, never at compile), the
   operations-parity law (2026-08-13), the modularity law (2026-08-26:
   "enforced" means a check that can fail; every varying behaviour reachable
   as configuration or a registered, versioned artifact), and the
   ungated-seats law (2026-08-28: any model in any seat; every gate
   switchable, switching one off emits a typed WARNING, never a refusal and
   never silence).

## Open questions (for dr-spec-change -- NOT answered here)

Q1: The operator wrote "agent.md". The monitor proposed "model profile"
    because "agent" already names executor windows in this repo. C8 routes
    this to the operator. What is the registry's on-disk location, the
    document naming convention, and the file format? `docs/map/SCHEMA.md`
    governs map documents; whether it governs THIS document class is itself
    part of the question.

Q2: M4's substitution question, which the window explicitly refuses to let
    this window decide alone: when a run config names a `reasoning:` value the
    profile does not declare, is the correct behaviour (a) silent substitution
    with the nearest declared value plus a typed disclosure, (b) omission of
    the knob plus a typed disclosure, or (c) something else? The window's own
    wording flags (a) as possibly violating "deterministic yet configurable".

Q3: R2 asks "would this work for all unknown models as well?" -- the operator's
    question form. The monitor's M3 answers it one way (knobs omitted, split
    stands down, typed notice). Whether the operator's question was a request
    for that guarantee or a request for confirmation that it already holds is
    not determinable from the words; M3 is the reading this tranche builds to,
    and DELIVERY.md must report back against the question as asked.

Q4: M6 requires the probe to be "wired so qualification or preflight can run
    it per seat and record the result typed". C3 forbids touching
    qualification.py. Whether a non-qualification preflight seat exists that
    can carry this is an empirical question for `dr-spec-change`; if none
    does, C8's priced-stop applies.

Q5: M1's minimum field set names "where the trace lands per value". Whether
    the harness has any existing typed vocabulary for trace location, or
    whether this field is descriptive prose for a human reader only, is
    undetermined by the words.

## Amendments

(append-only; later operator messages land here as R7... or "R2a supersedes
R2", each with its verbatim quote)

None as of capture.
