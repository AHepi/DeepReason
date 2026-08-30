# Request: successor questions — optional to propose, routed by pluggable destination, minting gated off-by-default

Captured: 2026-08-30 from CLAUDE.md lines 537-559, the standing operator design
law dated 2026-08-29 that decides the parked P9 question
(`experiments/2026-08-28-audit-run-problems/` F-G / PARKED.md P9). Ultracode
batch 2, lane B.

## Map preflight (recorded here so every later phase starts from the same map)

Resolved from `docs/map/INDEX.md` and each document's own `Owns:` header. The
seam documents were read before the subsystem documents, per INDEX.md's one
ordering rule.

| id | why this tranche touches it |
|---|---|
| `DR-INV-frozen-surfaces` | read first, always. Owns the five surfaces; surface 4 (`run_manifest.py`) is contacted by the Config-field recipe. |
| `DR-SEAM-ontology-x-rules` | owns `ontology/problem.py` (the dormant `SpawnTrigger.SUCCESSOR`) and `rules/spawn.py`. Rule 5: a `SpawnTrigger` needs its consumer in the same commit. |
| `DR-SEAM-rules-x-scratch` | owns `rules/crit.py` + `scratch/conjecture.py`. The binding constraint document: the criticism/scratch asymmetry, the exact `scratch`/`fence` counts in `crit.py`, the pinned pack signatures, and the "An unresolved question is not a problem" section. |
| `DR-CON-problem-layer-lifecycle` | states invariant H1 ("`translate` is the only path that mints a problem") and carries a stale Traps sentence about `scan_spawns` minting SUCCESSOR problems. |
| `DR-CON-criticism-source` | owns `rules/crit.py` as a socket; the `premise`/`premise_evidence` channel is this change's shipped precedent. |
| `DR-CON-scheduler-ranking` | owns the seed rank-tie promise and its two-occurrence check — R5's authority. |
| `DR-INV-signal-contract` | the FROZEN/VERSIONED/FREE layering the destination registry must sit in; owns `signals.py`. |
| `DR-REC-add-signal` | the recipe any new receipt tag follows (real `unit`, real `staleness`; `unspecified` is unavailable to a new signal). |
| `DR-INV-evidence-channels` | owns `channels.py` — the shipped registry template (declaration dataclass with an `enforcement` field, a registry version, unknown ids as typed notices imported at call time). |
| `DR-CON-discharge-channel` | the closest shipped analogue end to end: a per-run channel with a law line, a versioned registry, a `Config`-selected policy, and a failable architecture test. |
| `DR-CON-conjecture-kinds` | owns `llm/contracts.py`; states the formalism-optional prohibition (R-g) the successor field must inherit. |
| `DR-SEAM-llm-x-rules` | owns `llm/contracts.py`, `llm/wire.py` and `rules/crit.py` — the contract/wire mirror pair. |
| `DR-CON-authority` | owns `config.py`, where a per-run flag is allowed to live. |
| `DR-SUB-ontology`, `DR-SUB-rules`, `DR-SUB-scratch`, `DR-SUB-llm`, `DR-SUB-manifest` | the subsystem documents behind the seams above. |
| `DR-CON-run-identity` | problem ids and `config_digest` feed run identity; a new `Config` field changes the run id of every `--config`-bearing run. |

**FINDING (recorded, not a blocker): the map has no id for the module this
change must create.** The lawful home for a destination registry and a mint
site is a new package outside `rules/` and outside `scratch/`, and no existing
`SUB-`/`CON-` document's `Owns:` header covers it. The precedent is
`src/deepreason/discharge/`, which is owned by `DR-CON-discharge-channel` — a
package with its own concept document rather than a row on an existing one. This
tranche therefore proposes a NEW map document, `DR-CON-successor-questions`,
owning `src/deepreason/successor/`. Secondary finding, already recorded by this
batch's shared reconnaissance: `docs/map/INDEX.md`'s tables are incomplete
(they omit `SUB-application`, `SUB-amendment`, `SUB-periphery`,
`CON-problem-layer-lifecycle`, `CON-standing-and-background`,
`INV-signal-contract`, `REC-add-signal`, `REC-revise-allocation-policy` and
`SEAM-schools-x-scheduler`), so ownership above was derived from each
document's own `Owns:` header rather than from INDEX.md alone.

## Verbatim

Reproduced byte-for-byte from `CLAUDE.md` lines 537-559. The operator's own
words are the material inside the double quotes; the sentence beginning
"Operational reading:" is the ledger's reading of them and is quoted here only
so nothing is silently dropped.

> - **Successor questions: optional to propose, routed by pluggable
>   destination, minting gated off-by-default** (2026-08-29, operator's
>   words verbatim, deciding the parked P9 question): "This should be an
>   optional field the LLM can fill in. Not enforceable. If it is filled
>   in, it goes to scratchpad by default, linked to the problem it was
>   proposed under and visible by conjecturers. But build the wiring to
>   mint, with the option to switch it on with a flag saying something
>   like 'may cause critics to fully consume conjecturer role'. Switch
>   off by default. Again, maximum configurable surface. The scratch pad
>   option must function like a plugin that allows for movement
>   elsewhere as well. Again, the modularity thing and Max config
>   thing." Operational reading: the successor-question field is
>   OPTIONAL on criticism output — never required, never penalized
>   (formalism-optional pattern applies); a filled proposal routes to
>   the scratchpad by default, linked to its originating problem and
>   rendered visible to conjecturer seats; the DESTINATION is a
>   versioned, registered routing point (plugin-shaped, per the
>   signal-contract pattern) so it can be re-aimed by configuration;
>   the minting road (criticism → new problem, the SUCCESSOR trigger)
>   is BUILT and gated by a per-run flag, OFF by default, whose
>   enablement emits the operator's own warning text; every piece is
>   configuration, none is a code edit ("maximum configurable
>   surface").

## Requirements

Every requirement quotes the operator. Nothing here is inferred beyond the
quoted words; where the words leave something undetermined it is an Open
question below, not a requirement.

R1 (behavior): "This should be an optional field the LLM can fill in. Not
enforceable." — the successor-question field is OPTIONAL on criticism output.
Never required (a criticism with the field absent is legal and unchanged), and
never penalized: nothing that RANKS, ADMITS or ACCEPTS may read it. The
"never penalized" half is proved by an architecture test that goes red if any
ranking, admission or acceptance path reads the field — the formalism-optional
pattern (C1), made structural rather than promised.

R2 (behavior): "If it is filled in, it goes to scratchpad by default, linked to
the problem it was proposed under and visible by conjecturers." — a filled
proposal routes to the SCRATCHPAD as the default destination; the routed record
is LINKED to the problem the criticism was posed under; and the routed record is
VISIBLE to conjecturer seats (reachable by the attention planner that builds a
conjecturer's advisory context, not merely stored).

R3 (artifact): "The scratch pad option must function like a plugin that allows
for movement elsewhere as well. Again, the modularity thing and Max config
thing." — the DESTINATION is a versioned, REGISTERED routing point, declared on
the signal-contract pattern (C4) and re-aimable BY CONFIGURATION. Re-aiming the
destination must never require a code edit, and "enforced" means a check that
can fail (C3).

R4 (behavior): "But build the wiring to mint, with the option to switch it on
with a flag saying something like 'may cause critics to fully consume
conjecturer role'. Switch off by default." — the MINTING road (a criticism's
successor question becomes a new problem, carrying the dormant
`SpawnTrigger.SUCCESSOR`) is BUILT, and gated by a per-run flag that defaults
OFF. Enabling the flag EMITS the operator's own warning text — "may cause
critics to fully consume conjecturer role" — as a TYPED disclosure. Never a
refusal and never silence (C2).

R5 (behavior): a minted successor problem must never outrank the operator's
seed question. Not quoted from the P9 law itself: it is the standing invariant
C8, "The operator's seed question always wins scheduler rank ties", applied to
the problems this change can now mint. Recorded as a requirement because the
minting road is what makes it newly reachable.

R6 (process): "Again, maximum configurable surface." and "every piece is
configuration, none is a code edit" — every behaviour this change introduces
(which destination, whether minting is on) is reachable as configuration or as
a registered, versioned artifact, and none of it requires editing code to use.

## Standing constraints

C1: "nothing may force a conjecture to be formal, and nothing may penalize a
conjecture for being informal — not admission, not rank, not criticism
exposure, not acceptance." — CLAUDE.md, "Formalism is an option, never an
obligation" (2026-08-08). The pattern R1's architecture test copies.

C2: "Gates are always optional: with warnings." and "every gate
(qualification, criticism authority, judge invocation, admission screens) is
switchable per run, and switching one off produces a typed WARNING, never a
refusal and never silence" — CLAUDE.md, "Seat configuration is ungated, gates
are optional-with-warnings" (2026-08-28).

C3: "every behavior a run can vary is reachable as CONFIGURATION or a
REGISTERED, VERSIONED ARTIFACT — never by editing code ... and 'enforced'
means a check that can fail: each module carries an architecture test that goes
red when a consumer bypasses its interface or when a customization point
requires a code edit to use." — CLAUDE.md, "Modularity is enforced, and
customisation is easy" (2026-08-26).

C4: "The signal REGISTRY is a CONTRACT, not a wiring: a signal is anything
declaring name, unit, producer-agnostic semantics, and a staleness bound; new
setups add signals by declaration through this typed channel, never by teaching
a consumer about a subsystem." — CLAUDE.md, "The signal registry is a CONTRACT"
(2026-08-14). Its three layers (FROZEN change protocol, VERSIONED registry and
policy, FREE parameters) are the shape R3's registry must sit in.

C5: "All configurations should be allowed." — CLAUDE.md (2026-08-12). An
unknown destination id must not refuse at compile; it falls back to the shipped
default and DISCLOSES.

C6: "Frozen surfaces (never touch without explicit operator approval) ...
Manifest schemas" — CLAUDE.md. `run_manifest.py` is surface 4. The operator has
refused verbal grants: "Don't grant it verbally in chat"
(`docs/map/INV-frozen-surfaces.md`).

C7: "Gate discipline: 0 failed is the only acceptable result. Never weaken an
assertion to get green. A fixture that depended on defective behavior may be
minimally updated only when the fix's design doc predicted it." — CLAUDE.md.
Binding on the two guard tests this change trips.

C8: "The operator's seed question always wins scheduler rank ties;
import-role admission records never count as 'survivors'." — CLAUDE.md,
Hard-won invariants. R5's authority.

C9: "The map moves in the SAME COMMIT as the code — a separate 'update docs'
commit is the commit that gets dropped." — CLAUDE.md.

C10: "There was a website development pipeline that I decommissioned a while
ago. That needs to stay decommissioned." — the operator's ruling of 2026-08-15,
quoted verbatim in `tests/test_decommissioned_pipeline_stays_out.py`'s module
docstring. The SUCCESSOR trigger's producer count is zero BECAUSE of this
ruling. The P9 law is later and revives one gated producer; whether that ruling
is superseded, and how far, is Q5.

C11: "Never widen the criticism side to close the asymmetry. The asymmetry is
the design. Overturning it is an operator's call, not an implementer's." —
`docs/map/SEAM-rules-x-scratch.md`, How to change it, rule 6. Companion
sentence in the same document: "An unresolved question is not a problem ... No
edge joins the two, and none should. A spawn is a commitment to spend the run's
budget; a question in the workshop is explicitly allowed to be idle, wrong, or
unanswerable."

C12: "H1. Nothing here mints a problem from a conjecture's failure. `translate`
is the only path that mints a problem, and it fires from an adjudicated
resolution, not from a refutation." — `docs/map/CON-problem-layer-lifecycle.md`,
Invariants.

C13: "Ollama API tokens are cheap, you are not." — CLAUDE.md (2026-08-08). And
the recorded cost precedent for this exact shape: `AUDIT_CRITIC`, the only
other trigger that reacts to criticism behaviour, consumed 41.2% of one run's
budget (`experiments/2026-08-28-audit-run-problems/PARKED.md`). The default-OFF
flag is the mitigation; it may not be weakened.

## Open questions (for dr-spec-change)

Q1 (STOP 1 — frozen surface 4): R4 and R6 need per-run `Config` fields, and
`docs/map/INV-frozen-surfaces.md` states that a `Config` field is not done
without an unconditional `data.pop` line in
`run_manifest.py::_versioned_source_config_data` — which is frozen surface 4.
The operator has already called that line "the documented recipe (a Config
field is not done WITHOUT that line)", but every one of the prior contacts was
still REQUESTED in the tranche's SPEC.md before implementation. Requested in
SPEC.md §Frozen-surface contact forecast; standing precedent is not the grant.

Q2 (STOP 2 — where the warning is emitted): R4 says enabling the flag emits the
operator's warning text. The shipped compile-notice emitter builds its message
from a table (`_CARRIAGE_REQUALIFIES`) that lives INSIDE `run_manifest.py`, so
putting the words on the compile-notice stream costs a SECOND frozen-surface-4
edit. Composing the warning from the successor-destination registry instead
(outside `run_manifest.py`) collapses that contact to Q1 alone. Both roads are
priced in SPEC.md; the choice is the operator's.

Q3 (STOP 3 — REAL DESIGN FORK): reviving SUCCESSOR contradicts two standing
written positions that are not defects — C12 (H1) and C11 (the criticism/scratch
asymmetry, whose own prose says overturning it is an operator's call). The P9
law IS that call and IS later than both documents. What it does not settle is
WHICH guarantee survives: may the criticism dispatch itself WRITE the successor
question to the workshop, or must it reach the scratchpad through a
non-criticism intermediary that READS what the criticism recorded? Both roads
are priced in SPEC.md. Anything built before the answer is provisional on it.

Q4 (STOP 4 — how strong is R5): the seed's rank guarantee is a TIE-break, and a
minted successor loses that tie by construction. But the rank key's FIRST term
is age*weight, so a fresh, never-worked successor can outrank a seed that has
already been worked. Does the operator want the tie guarantee (already true,
provable now, no code change) or STRICT DOMINATION (a change to
`Scheduler._select_problem`'s rank key, a socket pinned by two map checks and a
regression)?

Q5 (STOP 5 — the scope of a superseded ruling): this change deliberately trips
`tests/test_decommissioned_pipeline_stays_out.py::test_no_source_file_produces_a_successor_problem`,
whose docstring calls itself "THE load-bearing invariant: producers = 0 ... If a
producer comes back, this fails -- which is the alarm that matters", founded on
C10. SPEC.md predicts the fixture change BEFORE the edit and states the
supersession narrowly: the 2026-08-29 P9 law supersedes the 2026-08-15 ruling
FOR THE SUCCESSOR TRIGGER ALONE, while the website development pipeline itself
stays decommissioned. That supersession statement is bubbled for confirmation;
an implementer may not decide the scope of a superseded operator ruling.

## Amendments

(append-only; later operator messages land here as R7... or "R2a supersedes R2",
each with its verbatim quote)

(none yet)
