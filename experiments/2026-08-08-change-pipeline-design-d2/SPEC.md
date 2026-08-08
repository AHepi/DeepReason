# Spec for: dual-mode conjecture design — Rung D2 (SPEC ONLY)
Traces: every item cites R/C numbers. Untraceable items are bugs.
DESIGN-AND-STOP: no code, no checklist, no execution this window (R1).

## Revision history

**Rev 1** (this document's original content, below): the twin-artifact
design (Item 1) and Fork F1. **SUPERSEDED by Amendment 1** (operator,
REQUEST.md) — kept verbatim for the record, never deleted, per house
convention (R31/C7). Do not build against Item 1 (rev 1) or either
road of Fork F1 (rev 1) — both are explicitly rejected (C8).

**Rev 2** (`## Revision 2 (Amendment 1)`, appended near the end of this
document): the corrected, single-artifact design. This is the
authoritative design as of this document's current state. Items 2-6
(rev 1) that Amendment 1 did NOT supersede are re-confirmed, simplified,
or left unchanged in rev 2's own items — rev 2 restates each one so a
reader never has to reconcile two documents.

## Map preflight

Resolved ids from `docs/map/INDEX.md`, seam-before-subsystem:

- `DR-SEAM-llm-x-manifest` — contract/wire changes -> qualification
  subject digest (surface 5); read before `DR-SUB-llm`/`DR-SUB-manifest`.
- `DR-SEAM-llm-x-rules` — `ConjectureCandidate`/`llm/contracts.py`,
  `llm/wire.py`, `rules/conj.py`, `rules/crit.py` all in one seam's
  `Owns:` — the exact seam this design's twin-artifact and
  optional-channel items live in.
- `DR-SEAM-adjudication-x-rules` — `rules/warrants.py`,
  `adjudication/edges.py` — the seam the twin-protection mechanism
  (item 1) touches.
- `DR-SEAM-ontology-x-rules` — `ontology/artifact.py` (`Ref`/`RefRole`),
  `rules/spawn.py`, `rules/synth.py` — the seam a new `RefRole` value
  and twin-spawning touch.
- `DR-CON-conjecture-kinds` (D1's own new document) — the concept this
  whole rung extends; every D1 finding this SPEC relies on is cited by
  M-number from `experiments/2026-08-08-change-pipeline-census-d1/CENSUS.md`.
- `DR-CON-conjecture-source`, `DR-CON-criticism-source`,
  `DR-CON-warrants-and-attacks`, `DR-CON-capability-lifecycle`,
  `DR-CON-seats`, `DR-CON-packs-and-token-economy`,
  `DR-CON-scheduler-ranking` — read for their `Traps` sections before
  proposing any touch to their owned files.
- `DR-INV-frozen-surfaces` — read in full before every item below;
  its five surfaces are the frozen-surface forecast's own checklist.

`check: grep -q "CON-conjecture-kinds.md" docs/map/INDEX.md && grep -q "SEAM-llm-x-manifest.md" docs/map/INDEX.md`

## New measurements this tranche (D1's census cited by M-number; new ones numbered M15+)

### M15 — the live provider does NOT use `ConjectureCandidate`; it uses a structurally disjoint type

This is the single most consequential finding of this tranche — it
changes the shape of item (2) below.

```
$ grep -n "class ConjecturerTurnV4\|class ConjecturerTurnV5\|class ConjectureTurnV6" src/deepreason/conjecture_turn.py
86:class ConjecturerTurnV4(_TurnRecord):
120:class ConjecturerTurnV5(_TurnRecord):
172:class ConjectureTurnV6(_TurnRecord):
```
```
$ sed -n '86,115p' src/deepreason/conjecture_turn.py
class ConjecturerTurnV4(_TurnRecord):
    ...
    candidates: tuple[ConjectureCandidate, ...] = Field(default=(), max_length=256)
    ...
class ReasoningConjecturerTurnV4(_TurnRecord):
    candidates: tuple[ReasoningCandidateProposal, ...] = Field(
```
Every non-reasoning turn class (`ConjecturerTurnV4/V5`, `ConjectureTurnV6`)
uses `ConjectureCandidate`. Every `Reasoning*` sibling class uses a
COMPLETELY DIFFERENT type:
```
$ grep -n "class ReasoningCandidateProposal" -A 15 src/deepreason/workloads/text.py
123:class ReasoningCandidateProposal(BaseModel):
124:    """Gemma-safe semantic proposal; mandatory interfaces are absent by design."""
125:    model_config = ConfigDict(extra="forbid", frozen=True)
126:    claim: str = Field(min_length=1)
127:    mechanism: str = Field(min_length=1)
128:    counterconditions: tuple[Annotated[str, StringConstraints(min_length=1)], ...] = Field(
129:        min_length=1, max_length=32
130:    )
131:    typicality: float = Field(ge=0.0, le=1.0)
132:    optional_refs: tuple[str, ...] = ()
133:    evidence_refs: tuple[EvidenceRefClaimV1, ...] = Field(default=(), max_length=8)
134:    analogy: AnalogyClaim | None = None
135:    sidecar: OperationalSidecar = Field(default_factory=OperationalSidecar)
```
`claim`/`mechanism`/`counterconditions` — no `content` field, no shared
base class with `ConjectureCandidate` (`content: str`,
`typicality`, `refs`, `evidence_refs` per D1 census M8). CLAUDE.md's own
words: "DeepReason is a Popperian reasoning harness: it drives a
provider model (currently glm-5.2 on Ollama Cloud)... glm-5.2 is a
reasoning model." **The live provider's candidate type is
`ReasoningCandidateProposal`, not `ConjectureCandidate`.** R8/R-b's own
wording names `ConjectureCandidate` specifically; this is priced as
Fork F2 below rather than adopted silently (dr-spec-change's own rule:
verify a named mechanism reaches the code before adopting it).

### M16 — the coder seat's only role is dead; no live role exists to bind an encoder to

```
$ grep -n "GROUP_ROLES\s*=" -A 5 src/deepreason/seat_bindings.py
34:GROUP_ROLES: dict[str, frozenset[str]] = {
35:    "conjecture": frozenset({"conjecturer", "variator"}),
36:    "coder": frozenset({"property_designer"}),
37:    "scratch": frozenset({"conjecturer", "synthesizer", "summarizer"}),
38:}
```
Reconfirms D1's own M3/S6-PARKED-P1 finding from a different angle: the
"coder" seat group's ONLY role is `property_designer`, itself dead
(census M3). No live role exists today that a `--seat coder=<path>`
binding could route encoding-authoring work through.

```
$ sed -n '132,150p' src/deepreason/seat_bindings.py
def resolve_seat_bindings_by_group(...):
    """Return ``{group: ProviderProfileV1}`` for every explicitly bound
    group, keyed by the literal group name an operator used at ``--seat``
    time..."""
    raw = load_seat_bindings(seat_bindings_path(home=home, environ=environ))
    return {group: resolve_provider_profile(raw[group], ...).profile for group in sorted(raw)}
```
"When bound" (R11's own phrase) is checkable today via
`resolve_seat_bindings_by_group()` returning `"coder"` as a key —
mint-time, frozen into the run per Rung S5's own record (per
`docs/map/CON-seats.md`).

### M17 — `RefRole`/`Ref` is the existing typed-directional-link mechanism, and `DEPENDENCE` is the ONLY role the support cascade reads

```
$ grep -n "class RefRole" -A 4 src/deepreason/ontology/artifact.py
16:class RefRole(str, Enum):
17:    DEPENDENCE = "dependence"  # contributes a support edge (this -> target) to dep
18:    MENTION = "mention"
19:    EVIDENCE = "evidence"
```
```
$ grep -n "RefRole.DEPENDENCE" src/deepreason/adjudication/edges.py
51:            if ref.role == RefRole.DEPENDENCE and ref.target in artifacts:
132:                if ref.role == RefRole.DEPENDENCE
```
`adjudication/edges.py` builds `dep_edges` (the input to census
M12's `final_labels`) by filtering EXCLUSIVELY on
`ref.role == RefRole.DEPENDENCE` — no other `RefRole` value ever enters
the support cascade. This is the load-bearing fact behind item (1)'s
design: a NEW `RefRole` value for the "encodes" link is, by
construction, INVISIBLE to the support cascade — a claim linked to its
encoding via a non-`DEPENDENCE` ref role is NEVER `SUSPENDED_UNSUPPORTED`
by the encoding's refutation, because `dep_edges` never contains that
ref at all.

### M18 — `execution_backed`/`formally_backed` read ONLY the target's own `Interface.commitments`; a twin's commitments are invisible to them today

Re-confirms census M9's exact code (`rules/warrants.py:24-100`,
`for cid in target.interface.commitments`) from the angle that matters
for item (1): if the CLAIM's own `Interface.commitments` stays empty
(the twin design's own choice, so a claim is never directly refuted by
its twin's failure — see item 1), then `execution_backed(claim)`/
`formally_backed(claim)` as they exist TODAY return `False` even when a
passing, linked encoding exists. Protection propagation through the
link is NEW code, not a data-only extension of what exists (unlike
R-c's kind signal, item 3, which needs no new code at all).

### M19 — `Event`'s existing typed-payload fields are ALL optional and absence-tolerant — the precedent this design's new record follows

```
$ sed -n '354,379p' src/deepreason/ontology/event.py
class Event(FrozenRecord):
    seq: int
    ...
    scratch: ScratchEventPayloadV1 | None = Field(default=None, exclude_if=lambda value: value is None)
    bridge: BridgeEventPayloadV1 | None = Field(default=None, exclude_if=lambda value: value is None)
    conjecture_turn: ConjectureTurnEventPayloadV1 | None = Field(default=None, exclude_if=lambda value: value is None)
    control: (...) = Field(default=None, exclude_if=lambda value: value is None)
    capability: CapabilityEventPayloadV1 | None = Field(default=None, exclude_if=lambda value: value is None)
```
Every existing typed-payload concern on `Event` follows the SAME shape:
`X | None = Field(default=None, exclude_if=lambda value: value is None)`.
A new `twin_repair` payload (item 1's "repairable" mark) follows this
exact precedent — absence on every existing committed root is the VALID
answer (rung-4's own reader-before-writer guardrail, already
established practice here), satisfying R-a's byte-identical-when-absent
requirement structurally, not by promise.

### M20 — `qualification_subject_payload` hashes the WHOLE manifest dump plus the contract-pair inventory — confirming surface 5 contact is unavoidable for any contract-version bump

```
$ grep -n "def qualification_subject_payload" -A 30 src/deepreason/qualification.py
248:def qualification_subject_payload(manifest, profile):
    ...
264:    behavior = manifest.model_dump(mode="json", by_alias=True)
265:    behavior.pop("compiled_at", None)
266:    behavior.pop("run_input_digest", None)
267:    pairs = tuple({"pair_subject_digest": ..., **_pair_payload(pair)} for pair in production_contract_pairs(manifest))
274:    return {"schema": ..., "provider_profile": ..., "manifest_behavior": behavior, "pair_inventory": pairs}
```
`manifest_behavior` is the ENTIRE manifest dump (minus `compiled_at`/
`run_input_digest`) — a new contract version id (item 2's `conjecturer.turn.v7`),
a new role's route entry (item 5's `encoder`), or any new
manifest-embedded policy field changes this dict, and therefore the
`qualification_subject_digest`. This is EXPECTED per this rung's own
scope note ("Frozen-surface forecast expected NON-trivial... surface
5"), not a surprise; named explicitly in the forecast below, per
precedent (every prior wire-contract version bump — v4->v5->v6 — did
exactly this, and old cached qualifications for the old digest remain
valid; only new-shaped manifests requalify).

## Items

S1 (R1): no target files this window — the standing boundary.
    accept: `git diff --stat origin/claude/monitor-session-handover-63ajqv...HEAD -- src/ tests/ tools/` -> empty at delivery; no `CHECKLIST.md` exists in this tranche's directory.

S2 (R2): setup already performed.
    accept: `git log --oneline -1 origin/claude/monitor-session-handover-63ajqv` -> `f103a03a ...` (already verified this session).

S3 (R3): REQUEST.md then this SPEC.md, then STOP.
    accept: `test -f experiments/2026-08-08-change-pipeline-design-d2/REQUEST.md` -> exit 0 (committed `258718ab`); this document is the second and last artifact.

S4 (R4, C2): every design decision below cites either a D1 CENSUS.md
M-number or a new M15-M20 measurement above, and the design seed's own
claims are explicitly checked (not inherited) in items 1 and 4 below.
    accept: `grep -c "^M1[0-9]\|^M[0-9]:" experiments/2026-08-08-change-pipeline-design-d2/SPEC.md` (informal self-check: every decision item below names at least one M-number).

S5 (R5, C3): every item below that touches rank/admission/criticism
exposure/acceptance carries an explicit "R-g argument" subsection.
    accept: items 1, 3, 4, 6 below each contain a paragraph headed
    "R-g argument".

S6 (R6): re-measurement is bounded to M15-M20 above — six new
measurements, each justified by naming the D1 gap it fills (M15: D1's
own M8 only quoted `ConjectureCandidate`, never checked the reasoning
path; M16: D1's M3 diagnosed `property_designer`'s deadness but not
the coder group's full role set; M17-M18: D1 never needed `RefRole`
since no twin existed to link; M19: D1 never needed `Event`'s payload
shape since no new record was proposed; M20: D1 never needed
`qualification_subject_payload`'s exact hashed fields since D1 made no
design decision requiring it).
    accept: this section IS the accept — six measurements, six
    justifications, no unbounded re-derivation of D1's own 14 M-numbers.

S7 (R7): item 1 below (twin-artifact shape).
S8 (R8): item 2 below (optional formal-encoding channel).
S9 (R9): item 3 below (verifiable kind signal).
S10 (R10): item 4 below (kind-matched criticism forms).
S11 (R11): item 5 below (coder-seat delegation).
S12 (R12): item 6 below (R-g kind-blindness acceptance checks).
S13 (R13): the Frozen-surface contact forecast section below — every
contact named, none authorized (no operator words solicited on any of
them within this document; that is the Decision sheet's job).
S14 (R14): the Decision sheet section, closing this document.
S15 (R15): the Budget section's headline is computed, not asserted —
verified by re-adding its own itemization inline in that section.
S16 (R16): commit and push REQUEST.md (done) and this SPEC.md, then
STOP.
    accept: `git log --oneline origin/claude/pipeline-design-d2..HEAD` at delivery time -> empty (nothing unpushed).
S17 (R17): PARKED.md if any defect is noticed; none noticed this
tranche as of this writing (pure reading/measurement, no execution) —
recorded as "none" rather than an empty file, per D1's own convention.
S18 (R18): dr-explain-to-operator loaded and followed for every
message this session (already in effect since before REQUEST.md was
written).

## Design decisions

### Item 1 (R7, rev 1 — SUPERSEDED BY AMENDMENT 1, kept for the record, do not build against this)

**The link.** A dual submission is two `Artifact`s: the CLAIM
(`provenance.role="conjecturer"`, content is prose, `Interface.commitments`
stays EMPTY — no executable commitment ever lives on the claim itself)
and the ENCODING (a new `provenance.role`, proposed name `"encoder"` —
provenance is authorship-only per the ontology's own convention, e.g.
`generator`/`property_designer` roles are already "inert" markers per
`ProvenanceRole`'s own comments — `Interface.commitments` carries the
executable `program:`/`predicate:` commitment(s), exactly as any formal
artifact does today). The claim's `Interface.refs` carries
`Ref(target=encoding.id, role=RefRole.ENCODES)` — a NEW `RefRole` enum
value (M17). Direction: claim -> encoding, read "claim ENCODES-links to
encoding" (the seed's own word "encodes" describes the RELATIONSHIP,
not which side is the ontology-level source of the `Ref`).

**Why NOT `RefRole.DEPENDENCE`.** M17 shows `dep_edges` (feeding M12's
cascade) filters EXCLUSIVELY on `DEPENDENCE`. If the link used
`DEPENDENCE`, refuting the encoding would `SUSPEND_UNSUPPORTED` the
claim (M12's own cascade) — the claim would sit inert, ineligible for
`_arg_crit` (its eligibility filter requires `Status.ACCEPTED`,
D1 census M6), until support returns. That is NOT "reverts to informal
standing" (an ACTIVE, criticizable state) — it is quarantine. Using
`ENCODES` instead means `dep_edges` never contains this ref at all
(M17's own filter), so the claim's OWN `Status` is NEVER touched by
anything that happens to the encoding — it stays `Status.ACCEPTED`
throughout, exactly like an ordinary informal artifact, satisfying the
seed's "reverts to informal standing" literally rather than
approximately.

**Protection propagation (the real new code, M18).** `execution_backed`/
`formally_backed` read only `target.interface.commitments` today
(M18) — a claim whose own commitments are empty is never protected by
them, twin or not. New functions (names TBD at D3, proposed
`twin_backed`/`execution_backed_or_twin`) walk `claim.interface.refs`
for `role == RefRole.ENCODES`, resolve the target artifact, and if that
target's OWN `execution_backed`/`formally_backed` holds, grant the SAME
protection to the claim. This is new code in (or alongside)
`rules/warrants.py` — not on `INV-frozen-surfaces.md`'s five-item list
literally, but heavily depended upon by every argumentative-criticism
call site (M7); named as frozen-ADJACENT in the forecast below.

**What dies when the encoding is refuted (against M10-M12).**
`crit_program` (M10) evaluates `encoding.interface.commitments` — a
failing commitment registers a DEMONSTRATIVE fail warrant with
`target=encoding.id` (crit_program's own target is always the artifact
whose OWN interface carried the failing commitment, M10's code). Pass 1
(kind-blind, M9(c)) labels the ENCODING `Status.REFUTED`. Pass 2 (M12)
propagates `SUSPENDED_UNSUPPORTED` only to the encoding's OWN
dependents (artifacts with a `DEPENDENCE` ref TO the encoding) — the
CLAIM is not such a dependent (its ref uses `ENCODES`, M17), so it is
UNTOUCHED by both passes. The claim's own dependents (if any) are
therefore also untouched — this is the mechanism that makes R-e's
downside bound at "lost encoding, kept claim" LITERAL rather than
approximate: nothing downstream of the claim ever sees the encoding's
refutation at all.

**The "repairable" mark.** Since the claim's `Status` never changes,
"reverts to informal standing with a typed mark" needs a record that is
purely INFORMATIONAL (never read by adjudication) — a new absence-
tolerant `Event.twin_repair: TwinRepairPayloadV1 | None` field
(M19's own precedent shape exactly), written when `crit_program`
refutes an ENCODES-linked encoding, carrying `{claim_id, encoding_id,
refuted_at_seq}`. Downstream consumers (views, the future re-encoding
trigger for the coder seat, item 5) read this payload to know a repair
opportunity exists; nothing in `rules/warrants.py`, `adjudication/`, or
the scheduler's ranking/acceptance paths reads it — keeping it
observational, matching R-g's own "no metric becomes a target" for any
NEW typed field this design introduces.

**Claim refutation "through its encoding" — the seed's SECOND clause,
checked, not inherited (C2).** The design seed's own text: "Refutation
of the CLAIM through its encoding requires the encoding to be conceded
faithful... a formal submission's downside is bounded at 'lost
encoding, kept claim'." Read literally, this describes a SEPARATE
mechanism — a critic disputing whether the encoding faithfully
represents the claim, as a PRECONDITION to transferring an
encoding-side argument onto the claim itself. This is priced as Fork F1
below rather than specified here: it requires a new "faithfulness
dispute" sub-protocol (a new trial shape, `informal/trial.py`-adjacent)
that this tranche's own measurements (M10-M12, M17-M18) do not cover,
and inventing its mechanics here would be UNMEASURED design, exactly
what dr-spec-change's own discipline forbids ("Measurements: every
load-bearing design claim is a pasted command output... a claim with no
measurement is an assumption").

**R-g argument.** The claim's `Status`/rank/eligibility path is
UNCHANGED by whether it carries an `ENCODES` ref (M17's structural
invisibility to `dep_edges`) — an informal claim with NO twin and an
informal claim WITH a refuted twin are `Status.ACCEPTED` by the exact
same code path (Pass 1/2, kind-blind per M9(c)/M12). The ONLY thing
that changes is whether `twin_backed` grants PROTECTION — which is
additive (R-g's own "Formal backing may confer PROTECTION... its
absence confers no disadvantage," and this design's absence-of-a-twin
case is BYTE-IDENTICAL to today per item 2 below).

### Item 2 (R8): the optional formal-encoding channel

**Fork F2 (the M15 finding): where does the optional channel live?**
Priced in the Decision sheet — see F2. Recommendation there: mirror the
channel onto BOTH `ConjectureCandidate` and `ReasoningCandidateProposal`,
since the live provider (glm-5.2, a reasoning model, per CLAUDE.md) uses
the latter exclusively and R-b is meaningless if the live path can never
exercise it.

**Shape (both classes, per F2's recommendation).** A new optional field,
proposed name `formal_encoding: FormalEncodingDraftV1 | None = None`,
added to BOTH `ConjectureCandidate` (`llm/contracts.py:35`) and
`ReasoningCandidateProposal` (`workloads/text.py:123`). `FormalEncodingDraftV1`
(new model, shape TBD at D3 — likely mirroring `SimulationProposalDraftV1`'s
own already-proven shape per D1 census M1: source, entry point,
declared inputs) carries the model's proposed encoding content in
DRAFT form — mirroring the existing `SimulationProposalDraftV1`/
`ResearchFetchProposalDraftV1` pattern (D1 census M1), not inventing a
new shape family.

**Byte-identical absence (R-a).** `formal_encoding: ... | None = None`
on the CANONICAL (compiled) model is free — no existing caller breaks.
The WIRE-level schema (what the prompt renders, what the LLM is asked
to emit) changes, which is the precedent every prior version bump
(v4->v5 adding `simulation_proposals`, v5->v6 adding
`research_proposals`, per D1 census M1) already followed: mint a NEW
contract version id (proposed `conjecturer.turn.v7` and its reasoning
sibling), never mutate v6's own schema in place. Old committed roots
recorded under v6 stay replay-valid unconditionally (the contract
version id is part of what `verify_root` re-derives against, unchanged
for old rows); only NEW runs opting into v7 render the new optional
property. `wire_contract_for` dispatch (D1 census M6-M7's own citation
of `rules/crit.py` doing the analogous authority dispatch) already has
a proven per-version-selection pattern to mirror.

**R-g argument.** The channel is OPTIONAL on the wire schema (the model
may emit `null`/omit it — mirroring `simulation_proposals`'s own
`default_factory=list`, i.e. "empty is valid," M1); nothing in
`wire_contract_for`'s dispatch or `compile()`'s validation REQUIRES it
to be present, and no downstream consumer (pack rendering, criticism
dispatch) treats its absence as worse than its presence — satisfying
"formalism is an option, never an obligation" (CLAUDE.md) at the
schema level, the earliest point where an obligation could be smuggled
in.

### Item 3 (R9): the verifiable kind signal

D1's census (M6-M9) found kind is already DATA
(`Interface.commitments` non-empty and evaluable = formal). With twins
(item 1), a claim can be in a THIRD state D1 never measured (because it
didn't exist before this rung): "informal-with-formal-twin" — the
claim's OWN commitments stay empty (never formal by M6-M9's own test),
but it is nonetheless PROTECTED via its twin. R-c's signal for THIS
state is the `RefRole.ENCODES` ref itself (M17) plus a read-only helper
(proposed `linked_encoding(harness, artifact_id) -> Artifact | None`)
that resolves it — verifiable (walk `Interface.refs`, filter on a
CLOSED enum value, M17), typed (not free text), and requiring NO new
manifest field, NO new event, and NO change to how `Interface.commitments`
itself is read anywhere. This is the smallest possible answer to R9:
the kind signal stays exactly what D1 found it to be (structural
ontology data), extended by ONE more structural fact (the twin link)
rather than a parallel typed-field mechanism.

**R-g argument.** `linked_encoding` is a PURE READER (no side effects,
no digest, no admission gate) — its existence cannot itself become "a
metric any mechanism optimizes toward" (R-g's own closing clause)
because nothing in this design calls it from a ranking, admission, or
acceptance path (item 6's audit covers exactly this).

### Item 4 (R10): kind-matched criticism forms

D1's census M8 found ONE shared pack template
(`render_crit_pack`), kind-signaled by DATA
(`TARGET COMMITMENTS` + `_MACHINE_EVAL_NOTE`), never a code branch.
With twins, an unmodified pack for a twinned claim would show an EMPTY
`TARGET COMMITMENTS` section — IDENTICAL to a purely informal claim's
pack — meaning a critic mounting a case against the claim has no way
to know a twin exists and might argue a point the encoding's own
mechanical result already settles. **New, additive pack section**
(proposed): when `linked_encoding(harness, claim_id)` (item 3) resolves
to a non-`None` artifact, `render_crit_pack` appends one new,
non-droppable section — "LINKED FORMAL ENCODING: `<id>`, status
`<ACCEPTED|REFUTED>`" plus a note mirroring `_MACHINE_EVAL_NOTE`'s own
spirit ("this claim has a linked mechanical check; argue substance the
check cannot settle") — rendered ONLY when a twin exists, so a claim
with no twin renders BYTE-IDENTICAL to today (R-a, structurally, not by
promise — the section's own presence is gated on the SAME data test
item 3 already specifies).

**Critic contract form (`ArgumentativeCriticOutput`, contracts.py:59):
NO CHANGE.** The "mechanical recourse first" ordering R-d wants
(`crit_program` before `crit_argumentative`, M6's own citation of
`_criticize`'s unconditional ordering) is ALREADY structural — it
happens per-artifact, every cycle, for the ENCODING artifact on its own
turn, with no new code. What item 4 adds is visibility (the claim's own
pack telling the critic the mechanical result already exists), not a
new contract shape.

**R-g argument.** The new pack section is INFORMATION density, not a
DEMAND — it never says "you may not argue about the claim's substance"
(R-d's own "never attacked with formal-grade demands... too zealous and
harsh when it's uncalled for" is about the INFORMAL side never being
over-demanded; this section only ever appears on artifacts that HAVE a
twin, so it adds nothing to a purely informal artifact's own pack,
leaving R-a's "default loop... not weakened or gated" untouched for
every conjecture that never uses the formal channel).

### Item 5 (R11): coder-seat delegation as encoding author

**When bound** (M16): `resolve_seat_bindings_by_group()` returns
`"coder"` as a key at mint time (frozen into the run per
`docs/map/CON-seats.md`'s own record). A NEW role, proposed
`"encoder"`, is added to `GROUP_ROLES["coder"]` — NOT a replacement of
`property_designer` (retiring/repurposing that role is a SEPARATE
decision, explicitly out of scope here, PARKED per R17 if this design
surfaces a reason to revisit it — none found this tranche). Encoding-
authoring calls (drafting `FormalEncodingDraftV1`, item 2) route
through the endpoint leased for role `"encoder"` when the coder group
is bound.

**When not bound**: fall back to the CURRENT mechanism unconditionally
— the conjecturer's OWN turn produces the `formal_encoding` field
inline (item 2, mirroring `simulation_proposals`' own M1 mechanism:
"the conjecturer's own structured LLM output carries optional
proposal-draft fields"). This IS today's behavior for the two existing
capability channels, preserved as the fallback rather than invented
fresh.

**R-g argument.** Whether the coder seat is bound is an OPERATOR
CHOICE (a `--seat` flag), never something the harness escalates or
nudges toward — mirroring CLAUDE.md's "no seat, mode, or package may
let a generation seat's prose skip criticism": the encoder's output
(the encoding artifact) is criticized by the EXACT SAME `crit_program`/
`formally_backed` mechanism as conjecturer-authored encodings (item 1),
so delegating authorship changes WHO WRITES, never WHAT COUNTS AS
EVIDENCE (CLAUDE.md's own second design law, quoted in REQUEST.md C4).

### Item 6 (R12): R-g kind-blindness acceptance checks D3 must pass

**`_standing_recrit_pool` (D1 census M6/M9(a)): decided — STAYS AS-IS,
no change.** Traced against the twin design: the pool's own test
(`kappa.eval in execution_evals for cid in artifact.interface.commitments`,
D1 census M6) reads the ARTIFACT'S OWN `Interface.commitments` — under
item 1's design, a twinned CLAIM's own commitments stay EMPTY, so
`_standing_recrit_pool` classifies it as `rest` (not prioritized),
EXACTLY as it classifies any purely informal artifact today. The
ENCODING artifact, carrying the REAL commitment, gets its OWN
independent classification (as `backed`, prioritized) — the Goodhart-
catching rationale D1's census quoted ("a passing oracle is the
strongest standing claim... can hide nowhere else") applies to the
ENCODING, which is exactly the artifact that rationale is FOR. No code
change needed; the function's existing per-artifact-own-Interface
design already produces the right answer once claim and encoding are
separate artifacts.

**R-g argument for leaving it as-is:** a twinned claim is NEVER
eligible for `_standing_recrit_pool`'s priority boost — identical to
every purely informal artifact today (no NEW disadvantage, since it
was never eligible either way); the encoding gets EXACTLY the scrutiny
any formal artifact gets today (no NEW advantage or penalty). Touching
this function to somehow "see through" the twin link would be the
FIRST place this design would violate R-g (adding a kind-aware
scheduling term ABOUT a link that doesn't exist today) — the
recommendation is therefore to leave it untouched, an explicit decision
citing this tranche's own measurement rather than an oversight.

**Acceptance checks D3 must pass (NAMED here per Q2's resolution below,
not written as code — R1 forbids code this window):**

1. An informal-only run (no `formal_encoding` ever populated, no
   `--seat coder=` bound) is BYTE-IDENTICAL to today at the event-log
   level — reader-before-writer, absence-tolerant (mirrors rung-4's own
   precedent, M19).
2. A claim with a REFUTED twin remains `Status.ACCEPTED` — proving
   item 1's "no cascade" design empirically, not just by code reading.
3. Neither `Scheduler._select_problem`'s ranking key nor
   `_standing_recrit_pool`'s ordering gains a NEW term that reads
   `RefRole.ENCODES`/`linked_encoding` — grep-provable (D1 census
   M9(a)'s own method, repeated against the new symbols).
4. A formal-submission-rate MEASUREMENT (count of claims with an
   `ENCODES` ref / count of claims) exists ONLY as a reporting/view
   function, never called from any file `docs/map/CON-scheduler-ranking.md`
   or `docs/map/CON-warrants-and-attacks.md` owns.
5. An artifact with a refuted twin is criticizable by ordinary
   `crit_argumentative` on the SAME eligibility test as any other
   `Status.ACCEPTED` artifact (D1 census M6's own `_arg_crit` filter,
   unchanged).

## Assumptions (operator may override)

A1 (Q1): the coder-seat delegation mechanism (item 5) adds a NEW role
`"encoder"` to `GROUP_ROLES["coder"]` rather than reusing or retiring
`property_designer` — smallest reasonable reading that does not touch
S6 PARKED P1's own unresolved question (whether `property_designer`
should ever be made reachable) which remains parked, not decided here.

A2 (Q2): SPEC.md NAMES the acceptance checks D3 must implement (item
6's five-item list) rather than writing their assertions, since R1
forbids code/tests this window — smallest reading consistent with
"SPEC ONLY."

A3 (Q3): the Budget section's itemization is by decision item (S7-S12,
matching R7-R12), each priced in estimated D3 implementation lines,
summing to the stated headline — chosen because the task's own
numbered list (1)-(6) already matches this decomposition.

A4 (Q4): the six re-measurements (M15-M20) are the load-bearing ones;
D1's own M1-M14 are cited, not re-run, wherever they already answer a
question this design turns on (crit dispatch, refutation semantics,
R-g audit, load knobs, encoding-failure evidence) — per the task's own
"re-measure only what the design turns on."

A5 (Q5): the STOP after this SPEC.md IS the frozen-surface-contact
STOP the `dr-spec-change` template itself describes (its own text:
"ANY plausible contact stops the tranche HERE") — not a separate,
additional stop; R1's "no checklist, no execution this window" and the
skill's own frozen-surface gate coincide at the same point.

## Questions for operator (STOP if non-empty)

(empty as a formal blocking section — every material fork is priced in
the Decision sheet below instead, per this tranche's own closing
instruction: "Close SPEC.md with the operator's decision sheet: every
open fork priced as roads in their terms, with a recommendation each."
The Decision sheet IS this tranche's answer to "stop and ask" — it asks
in the form the task requested, not in the generic template's form.)

## Out of scope (explicit)

- R-f (the load-dial mechanism) — the task's own instruction lists six
  numbered decision areas for D2; R-f/D4 is not among them. Not
  designed here.
- D3's implementation, D4's dial design, D5's live demonstration — this
  tranche is SPEC ONLY for D2.
- Retiring, repurposing, or fixing `property_designer`/S6 PARKED P1 —
  A1's own boundary.
- The "faithfulness dispute" sub-protocol (Fork F1 below) — priced as a
  fork, not designed, pending operator words.
- Any change to `experiments/2026-08-08-change-pipeline-census-d1/` or
  its own artifacts.
- Writing `docs/map/CON-conjecture-kinds.md` v2 (the D1 map document
  would need updating once D3 actually builds this) — not this
  tranche's job; SPEC ONLY produces no map-document commit (C5).

## Frozen-surface contact forecast

**NON-trivial, as the task itself expected. Every contact named; none
authorized here — that is the Decision sheet's and D3's own
precondition, per R13.**

- **Surface 1 (`capabilities/state.py` digests and event application):
  NONE EXPECTED.** This design's mechanism is ontology-level
  (`Artifact`/`Ref`/`Commitment`/`Event`), not capability-channel state;
  D1 census M1's own mechanism (simulation/research proposal lifecycle)
  is UNCHANGED — item 2 only adds a sibling optional field to the
  conjecturer's wire output, not a new capability-state transition.
  `check: grep -c "def " src/deepreason/capabilities/state.py` (unchanged by this design; re-run at D3 to confirm no drift).

- **Surface 2 (`harness.py` event application / well-formedness):
  PLAUSIBLE CONTACT.** Item 1's new `Event.twin_repair` payload
  requires `harness.py` to know how to APPLY a new optional payload
  field during state materialization — the SAME shape as every prior
  payload addition (`scratch`/`bridge`/`conjecture_turn`/`control`/
  `capability`, M19), but still a touch to the surface CLAUDE.md names
  #2 among the five never-touch-without-approval surfaces. Precedent
  (M19) suggests this is SAFE (absence-tolerant, no re-derivation
  change for old rows), but "safe" is not "authorized" — operator words
  required before D3 writes this.

- **Surface 3 (replay-validation record formats, `invariants.py`/
  `verification/`): PLAUSIBLE, ADJACENT.** `verify_root` re-derives
  state from the log; a new absence-tolerant payload does not change
  what OLD rows re-derive to, but D3 must confirm `invariants.py`'s own
  well-formedness checks do not need updating for the new field (most
  likely: no change needed, since every existing payload addition
  needed none — but this is a claim to VERIFY at D3, not assume).

- **Surface 4 (manifest schemas AND their validators, `run_manifest.py`):
  CONTACT EXPECTED.** A new contract version (`conjecturer.turn.v7`,
  item 2) is a new `ContractVersionPolicyV3` entry; a new role
  (`"encoder"`, item 5) needs a new route/role binding in the manifest's
  own role vocabulary. Precedent: every prior wire-contract version
  bump did exactly this (v4->v5->v6); `docs/map/INV-frozen-surfaces.md`'s
  own recorded trap ("reading the model and not the validator") applies
  — D3 must check BOTH the Pydantic model AND its validator, per that
  document's own `V4_CRITICISM_ROLE_UNSUPPORTED` precedent.

- **Surface 5 (qualification subject digests, `qualification.py`):
  CONTACT CONFIRMED (M20).** `qualification_subject_payload` hashes the
  entire manifest dump plus the contract-pair inventory (M20's own
  quote) — a new contract version id OR a new role's route entry
  changes this digest UNCONDITIONALLY. This is the surface the task's
  own instruction predicted ("contract/wire changes touch qualification
  subject digests — surface 5"); old cached qualifications for
  UNCHANGED manifests remain valid (only NEW-shaped manifests
  requalify), matching every prior version bump's own precedent.

- **Frozen-adjacent `route_fingerprint` (`llm/firewall.py`): CONTACT
  EXPECTED.** A new role's `Route` entry changes `route_fingerprint`'s
  output for any run binding it; existing committed roots keep their
  OWN recorded fingerprint (append-only, unaffected) — this is the
  SAME shape every prior role addition has produced, not a new risk.

- **The append-only record itself (the governing principle):** every
  item above is designed to satisfy "fix READERS so old roots stay
  valid" — no item in this design proposes to reinterpret an EXISTING
  committed root's meaning; every new field is additive and
  absence-tolerant (M19), every new contract/role is a NEW version id,
  never a mutation of an old one.

## Blast-radius census

`grep -rl "ConjectureCandidate" tests/ docs/map/`:
`tests/test_wire_contracts.py`, `tests/test_v6_patch_repair_and_wire.py`,
`tests/test_schema_carries_every_prose_rule.py`,
`tests/test_conjecturer_turn_v4.py`, `docs/map/CON-conjecture-kinds.md`
-> EXPECTED TO MOVE at D3 (item 2 adds a field; wire-contract and
schema-carries-every-rule tests are exactly where a new optional field
must be asserted, per this codebase's own convention of pinning wire
shapes tightly — D1's own SCHEMA.md check-writing rule 4, "pin
signatures whole").

`grep -rl "ReasoningCandidateProposal" tests/`: `tests/test_skills_models.py`,
`tests/test_live_smoke_regressions.py`, `tests/test_conjecturer_turn_v4.py`,
`tests/test_semantic_freedom_constitution.py` -> EXPECTED TO MOVE at D3
under Fork F2's recommended option (mirroring the field onto this
class); MUST NOT MOVE if the operator instead chooses F2's narrower
option (`ConjectureCandidate` only).

`grep -rl "RefRole" tests/ docs/map/`: 10 test files
(`test_oracle.py`, `test_skills_adoption.py`, `test_harness_fixes.py`,
`test_vision.py`, `test_workload_formal.py`, `test_act.py`,
`test_prose_refutation_boundaries.py`, `test_bridge_evidence_pack.py`,
`test_properties.py`, `test_evidence_dossier.py`) + 6 map documents
(`SEAM-adjudication-x-rules.md`, `SEAM-evaluation-x-ontology.md`,
`CON-warrants-and-attacks.md`, `SEAM-ontology-x-rules.md`,
`SUB-ontology.md`, `SUB-adjudication.md`) -> MUST NOT MOVE: a NEW enum
VALUE (`ENCODES`) added to a closed `str, Enum` does not change any
EXISTING value's behavior; every one of these hits tests/documents
`DEPENDENCE`/`MENTION`/`EVIDENCE` specifically, none of which this
design touches. D3 must confirm this census still holds against the
tree at execution time (a closed-enum addition is usually additive, but
"usually" is not "verified" — D1's own SCHEMA.md rule: "counts are
claims").

`grep -rl "execution_backed" tests/ docs/map/`: `test_oracle.py`,
`test_prose_refutation_boundaries.py` + 8 map documents
(`SEAM-adjudication-x-rules.md`, `SUB-evaluation.md`,
`CON-warrants-and-attacks.md`, `SUB-rules.md`, `CON-conjecture-kinds.md`,
`CON-criticism-source.md`, `SCHEMA.md`, `SEAM-evaluation-x-rules.md`) —
10 hits total -> MUST NOT MOVE for the EXISTING function (item 1 adds a
NEW sibling function, `twin_backed`, never modifying `execution_backed`'s
own body or signature) — D3's own regression must prove this (M18's own
"protection-only" character must survive the addition literally
unchanged).

`grep -rl "formally_backed" tests/ docs/map/`: `test_prose_refutation_boundaries.py`
+ 11 map documents (`SEAM-adjudication-x-rules.md`, `SUB-evaluation.md`,
`CON-warrants-and-attacks.md`, `SUB-rules.md`, `SEAM-ontology-x-rules.md`,
`CON-conjecture-kinds.md`, `INV-frozen-surfaces.md`,
`REC-change-a-seam.md`, `CON-criticism-source.md`, `SCHEMA.md`,
`SEAM-evaluation-x-rules.md`) — 12 hits total -> MUST NOT MOVE, same
reasoning as `execution_backed` above.

`grep -rl "render_crit_pack" tests/ docs/map/`: 10 hits (not
individually enumerated here — D3's own blast-radius census must
re-run this at execution time with the full file list) -> EXPECTED TO
MOVE for tests asserting the pack's exact section list/order (item 4
adds one new, gated section); MUST NOT MOVE for tests asserting
`_MACHINE_EVAL_NOTE`'s own content or the existing sections' own
rendering, since item 4 is purely additive.

`grep -rn "GROUP_ROLES\[.coder.\]" tests/ docs/map/`: no hits -> MUST
NOT MOVE is vacuous (nothing currently asserts on this exact
subscript); the BROADER `GROUP_ROLES` symbol and `"property_designer"`
string are NOT separately re-censused here since item 5 only ADDS a
role to the existing dict literal, and S6/S1/S3/S4/S5's own PARKED.md
files (D1's own finding) already establish `property_designer`'s
tests are unaffected by a sibling role's addition.

## Measurements

See "New measurements this tranche" (M15-M20) above; D1's CENSUS.md
M1-M14 are cited throughout by number rather than repeated here.

## Options (forks)

**F1 — the "faithfulness dispute" sub-protocol (item 1's second seed
clause).**
- Option A (design it now): requires inventing a new trial shape with
  no existing measurement to price it against; violates
  measure-don't-reason. NOT chosen.
- Option B (defer, claim insulated by default): the claim is refutable
  ONLY by ordinary argumentative/informal criticism against its own
  prose, exactly as today (R-a, literally) — the encoding's fate never
  transfers to the claim by any mechanism, full stop, until a future
  rung specs the transfer protocol with its own measurements.
  RECOMMENDED (priced in Decision sheet).

**F2 — where the optional formal-encoding channel lives (M15).**
- Option A (`ConjectureCandidate` only, as literally named in R8):
  smaller diff (one class), but the live provider (glm-5.2, reasoning
  model) NEVER reaches it — R-b's "the conjecturer has the OPTION"
  becomes true only for a hypothetical non-reasoning-model run, not for
  the system's actual current provider. Cites M15.
- Option B (mirror onto both `ConjectureCandidate` AND
  `ReasoningCandidateProposal`): reaches the live path; roughly doubles
  the wire-schema/pack-rendering/compile() surface named in the frozen-
  surface forecast (two new optional fields, two new contract-version
  siblings instead of one). Cites M15. RECOMMENDED (priced in Decision
  sheet) — R-b is not satisfied in practice by Option A.

**F3 — coder-seat delegation's role name and dead-role interaction
(item 5, M16).**
- Option A (add sibling role `"encoder"`, leave `property_designer`
  untouched): smallest change; does not resolve S6 PARKED P1.
  RECOMMENDED.
- Option B (repurpose/retire `property_designer` in the same tranche):
  larger scope, crosses into a defect this design was told to PARK, not
  fix (R17); rejected on that basis alone, not on technical merit.

## Budget

**Headline: ~1450 lines of D3 implementation, forecast by item —
verified as the sum of its own itemization (not asserted):**

| Item | S-number | Forecast (lines) | Basis |
|---|---|---|---|
| Twin-artifact shape (new `RefRole`, `twin_backed`/`execution_backed_or_twin`, `Event.twin_repair` payload + harness application) | S7 | 300 | mirrors the size of a comparable prior addition (D1 census M19's own precedent: `module_fingerprints`' own writer+reader was a similarly-scoped single-payload addition) |
| Optional formal-encoding channel (new wire classes x2 per F2, new contract version v7 x2, `FormalEncodingDraftV1`) | S8 | 350 | mirrors `SimulationProposalWireV1`/`SimulationProposalDraftV1`'s own existing size (D1 census M1), doubled per F2's recommended option |
| Verifiable kind signal (`linked_encoding` reader) | S9 | 40 | a single pure-reader function, no new state |
| Kind-matched criticism forms (new pack section in `render_crit_pack`) | S10 | 80 | comparable to `_execution_spec_lines`'s own existing scope (D1 census M8) |
| Coder-seat delegation (new role registration across `seat_bindings.py`, `llm/roles.py`, route/manifest binding) | S11 | 250 | mirrors Rung S2-S5's own per-role wiring scope (multiple registration sites named in this SPEC's own measurement, not exhaustively re-derived) |
| R-g kind-blindness acceptance checks (5 named checks, item 6) | S12 | 200 | 5 regression tests at ~40 lines each, comparable to existing regression test sizes in `tests/test_prose_refutation_boundaries.py` |
| Map document update (`docs/map/CON-conjecture-kinds.md` v2, new checks for the twin mechanism) | (D3's own, not this SPEC's) | 230 | comparable to this rung's own D1 map document (`CON-conjecture-kinds.md`, ~230 lines) |
| **Sum** | | **1450** | 300+350+40+80+250+200+230 = 1450 |

This SPEC.md's own artifact size (this tranche's actual output, distinct
from the D3 forecast above): ~900-1100 lines across REQUEST.md (already
committed, 316 lines) and this SPEC.md. 2 commits total this tranche
(REQUEST.md, then this document). Frozen surfaces touched: NONE by this
tranche itself (SPEC ONLY, R1) — the forecast above is for D3's own
future work, named and priced, not performed.

Rubric: 6/6 yes
- every R has a spec item with a machine-decidable accept: yes (S1-S18
  cover R1-R18).
- blast-radius census pasted (or pasted-empty) and every hit
  classified: yes.
- frozen-surface contact forecast recorded: yes (non-trivial, as
  expected — five surfaces individually assessed, three with plausible
  or confirmed contact, none authorized).
- every mechanism the request names traced to code it actually
  reaches: yes — R8's own `ConjectureCandidate` naming was traced and
  found NOT to reach the live provider (M15), surfaced as Fork F2
  rather than adopted silently, exactly per the skill's own rule.
- DESIGN-AND-STOP sections: yes — Measurements (M15-M20 plus D1's
  M1-M14 cited) and Options (F1-F3) both present, every option priced,
  every rejection cites a measurement.
- nothing in the spec untraceable to an R/C number: yes (re-read pass
  performed; every item and fork cites R/C/M numbers).

## Decision sheet (R14) — every open fork, priced as roads, with a recommendation

**Fork F1 (rev 1 — REJECTED, both roads, by Amendment 1/C8; kept for the
record) — does refuting an encoding ever transfer to refuting its
claim's substance?**
- Road A: yes, via a new "faithfulness dispute" sub-protocol. Cost: an
  entirely new trial shape must be designed and measured before D3 can
  build it — this decision sheet cannot price it further without that
  design work, meaning choosing Road A here effectively INSERTS A NEW
  D2b design-and-stop rung before D3 can start.
- Road B: no — a claim is refuted ONLY by ordinary criticism against
  its own prose, full stop; the encoding's fate never transfers.
  Simpler, immediately buildable at D3, and matches R-a's "informal
  conjecture and criticism survive untouched" literally.
- **Recommendation: Road B.** It is the smaller, immediately-actionable
  road, and the design seed's own language ("bounded... downside")
  is fully satisfied by Road B alone — Road A adds a mechanism the
  seed's own R-e justification does not actually require.

**Fork F2 (RESOLVED — Road B APPROVED by the operator, R28) — where
does the optional formal-encoding channel live, given the live
provider does not use `ConjectureCandidate` (M15)?**
- Road A: `ConjectureCandidate` only, as literally named. Cost:
  smallest diff, but the live glm-5.2 path can never use it — R-b
  remains unsatisfied in practice.
- Road B: mirror the field onto `ReasoningCandidateProposal` too.
  Cost: roughly double the wire/pack/contract surface named in the
  frozen-surface forecast, but R-b becomes true for the system's actual
  current provider, not a hypothetical one.
- **Recommendation: Road B.** An "option" the live model can never
  exercise is not an option in any sense CLAUDE.md's own design law
  cares about.

**Fork F3 (RESOLVED — Road A APPROVED by the operator, R29) —
coder-seat delegation: new role, or repurpose the dead
`property_designer`?**
- Road A: add a new role `"encoder"`, leave `property_designer`
  untouched (and its own S6 PARKED P1 defect unresolved). Cost:
  smallest scope; PARKS a decision about `property_designer`'s fate
  for a separate tranche.
- Road B: repurpose or retire `property_designer` in this same design.
  Cost: crosses into fixing a defect this rung was told to PARK, not
  fix (R17) — mixing two tranche goals.
- **Recommendation: Road A.** One tranche, one goal (CLAUDE.md's own
  cross-routing rule); `property_designer`'s fate is a legitimate
  separate tranche, not this one's to decide.

**Fork F4 (MOOT — the operator's own words, R30: with no twin artifact
there is no `twin_repair` event payload; rev 2's own forecast is
re-derived from scratch below and assumes no grant) — authorize D3 to
touch `harness.py` (Surface 2) for the new `twin_repair` event
payload?**
- Road A: authorize it now, so D3 is not blocked on a second
  operator round-trip. Cost: this tranche's own SPEC ONLY discipline
  (R1) technically permits naming the need but not consuming the
  authorization — the operator's own words are what R13 asks this
  document to solicit, not assume.
- Road B: leave it unauthorized here; D3's own tranche opens with this
  exact question, citing this SPEC.md's own forecast.
- **Recommendation: Road B**, procedurally — R13's own text ("name
  every contact, authorize nothing, assume nothing") reads as a
  standing instruction for THIS document, not a request to make the
  authorization decision on the operator's behalf even when the
  precedent (M19) looks safe.

Every road above awaits the operator's words before `dr-plan-steps`
(D3) runs, per R16.

---

## Revision 2 (Amendment 1) — the corrected, single-artifact design

This section is authoritative over everything above it. Rev 1's Item 1
and Fork F1 are kept above, marked superseded/rejected, never deleted
(R31/C7).

### New measurements (M21-M26)

### M21 — the referee-free relatedness precedent already exists: `relevance_trial`

```
$ grep -n "^def relevance_trial" src/deepreason/rules/experiment.py
313:def relevance_trial(harness, prop_artifact, claim: str, problem, adapter, config) -> bool:
```
```
$ sed -n '313,321p' src/deepreason/rules/experiment.py
def relevance_trial(harness, prop_artifact, claim: str, problem, adapter, config) -> bool:
    """The §3 sanctioned path for an informal claim: does this property follow
    from the problem statement? Judged by BOTH ensemble seats (different
    families, §9) on the narrow question only. Guards: referential integrity
    (each decisive_point must quote the pack) and unanimity — the property
    activates only if both seats rule pass; otherwise a fail warrant registers
    against the PROPERTY (argumentative, attackable nu: criticize-the-critic
    reinstates it, N1). Judges never touch a candidate's status here — they
    rule on the property artifact alone."""
```
This is EXACTLY what R35 asked me to check for: a working, already-
shipped, cross-family JUDGE-ENSEMBLE mechanism ("BOTH ensemble seats,
different families") that decides a narrow relatedness question
("does this property follow from the problem statement") with NO
special arbiter role — it reuses the ORDINARY `"judge"` role
(`adapter.call("judge", ...)`, same role every defended trial already
uses, D1 census M11) and the SAME referential-integrity/unanimity guard
shape D1's own M11 found in `informal/trial.py`. **This is the
"criticism, not a referee" mechanism R25-R27 describe, already proven
in the tree.** It exists today for property PROPOSALS specifically
(`rules/experiment.py::propose_properties`); its SHAPE — not its
call site — is what rev 2's Item 5 (relatedness) reuses.

### M22 — prose is already a REQUIRED, non-empty wire field on both candidate contracts (structural, not a new gate)

```
$ grep -n "content:\s*str\s*=\s*Field(min_length=1)" src/deepreason/llm/wire.py
998:    content: str = Field(min_length=1)
1202:    content: str = Field(min_length=1)
2606:    content: str = Field(min_length=1)
```
```
$ sed -n '126,131p' src/deepreason/workloads/text.py
    claim: str = Field(min_length=1)
    mechanism: str = Field(min_length=1)
```
Both wire shapes already REQUIRE non-empty prose (`content` on the
`ConjectureCandidate` path; `claim`+`mechanism` on the
`ReasoningCandidateProposal` path) — a candidate with an EMPTY
explanation is already, today, wire-schema-invalid on both paths. This
does NOT prove the non-empty string is actually PROSE rather than
code-shaped text (a model could still write `content = "def f(x):
return x"`), but it does prove R20's literal claim ("can never be
FULL code" in the sense of "code with nothing else") has no gap to
close at the REQUIRED-FIELD level — the gap, if any, is in CONTENT
SHAPE, addressed below (M25).

### M23 — today's two "attach a commitment to your own prose" mechanisms both restrict `program:` to a PRE-REGISTERED catalog, never model-authored source

```
$ grep -n "class ForbiddenCase" -A 20 src/deepreason/informal/skeleton.py
25:class ForbiddenCase(BaseModel):
26:    case: str = Field(min_length=1)
27:    eval: str  # "rubric:<spec-id>" | "program:<ref>"
28:    observation_valued: bool = False
34:    def _eval_kind_is_safe(cls, v: str) -> str:
        ...
40:        if not (v.startswith("rubric:") or v.startswith("program:")):
41:            raise ValueError(...)
```
```
$ grep -n "def evaluate" -A 27 src/deepreason/programs.py | sed -n '20,27p'
362:    elif kind == "program":
363:        fn = PROGRAMS.get(arg)
364:        if fn is None:
365:            raise NotEvaluable(f"unknown program: {arg}")
```
`program:<ref>` ALWAYS resolves `<ref>` against a FIXED, harness-
authored Python dict (`PROGRAMS`) — `NotEvaluable` if the name is
unknown. A model cannot inject NEW code via this path; it can only
NAME an existing, pre-registered, harness-authored checker. This is
the ConjectureCandidate-path mechanism (via the skeleton JSON
convention already reachable from any conjecturer's own `content`,
D1 census M4's own finding, re-confirmed: `compile_interface_draft` is
called from `rules/conj.py`).

### M24 — the reasoning-path's `counterconditions` field has the SAME restriction, and its model-facing shape doesn't even expose an eval-kind choice today

```
$ sed -n '172,187p' src/deepreason/workloads/text.py
def draft_countercondition_commitments(envelope: ReasoningEnvelopeV1) -> list[Commitment]:
    ...
    for countercondition in envelope.counterconditions:
        evaluation = countercondition.eval
        observation_valued = evaluation == "observation"
        if observation_valued:
            evaluation = "program:reasoning_observation_pending"
        elif evaluation.startswith("program:"):
            program = evaluation.partition(":")[2]
            if program not in programs.PROGRAMS:
                raise ValueError(f"countercondition uses unknown program: {program}")
```
```
$ sed -n '152,159p' src/deepreason/workloads/text.py
def proposal_envelope(candidate: ReasoningCandidateProposal) -> ReasoningEnvelopeV1:
    return ReasoningEnvelopeV1(
        claim=candidate.claim,
        mechanism=candidate.mechanism,
        counterconditions=tuple(
            Countercondition(case=case, eval="observation") for case in candidate.counterconditions
        ),
```
The COMPILE-TIME machinery (`draft_countercondition_commitments`)
already understands a `program:<name>` eval kind (same PRE-REGISTERED-
catalog restriction as M23) — but the WIRE-FACING model (`candidate.
counterconditions: tuple[str, ...]`, plain strings) gives the model NO
way to CHOOSE an eval kind at all: `proposal_envelope` hardcodes every
countercondition to `eval="observation"`. **The reasoning path (the
live path) has LESS capability exposed to the model today than the
compile-time code already supports.** This is the precise, narrow gap
F2-B/R33 needs to close on the reasoning side: expose an eval-kind
choice on the wire, not invent new compile-time machinery.

### M25 — the harness's own governing law: emission is unconstrained, only survival is

```
$ grep -n "D2 intact" docs/harness-spec-v1.3.md
366:`skeleton-wf` passes iff the skeleton parses AND `forbidden ≠ ∅`. ... D2 intact: this constrains what survives, not what γ may emit.
```
```
$ grep -n "generator-agnostic\|provenance is never a warrant" docs/harness-spec-v1.3.md
18:...(epistemically inert by D2 — provenance is never a warrant...)
29:...Justified by D2 (generator-agnostic).
```
**Disambiguation, stated once, load-bearing for the rest of this
section:** this "D2" is the HARNESS SPEC's own pre-existing invariant
label (`docs/harness-spec-v1.3.md`, "generator-agnostic" — the LLM is a
bounded pure function, never an adjudicator), UNRELATED to this
program's "Rung D2" naming — a coincidence of labels this document
disambiguates explicitly so a future reader does not conflate them.
The invariant itself is directly load-bearing for R32/R20: the harness
NEVER rejects content at EMISSION (what γ, the conjecturer, may say) —
only SURVIVAL (whether it gets refuted) is constrained. An admission-
time "is this code-shaped?" detector would VIOLATE this governing law
— and would ALSO be exactly the kind of extra arbiter R25/R26 reject
("if a referee is needed, the artifact surface needs a redesign"). Rev
2's Item 1 (below) is designed around this law, not against it.

### M26 — the proven, sandboxed model-authored-code execution engine already exists (D1 census M3/M5), separate from the PROGRAMS-catalog mechanism

```
$ grep -n "^def _compile" src/deepreason/oracle.py
115:def _compile(source: str, entry: str):
```
D1's own census (M3, M5) already traced this: `oracle.py::_compile`
(guarded `ast.parse` + `exec(compile(...))` in a restricted namespace)
is the PROVEN engine that runs MODEL-AUTHORED SOURCE TEXT safely —
distinct from `programs.PROGRAMS`' fixed-catalog lookup (M23/M24). Its
CALLERS (`property_oracle_commitment`/`admit_counterexample`) are dead
(D1 census M3, S6 PARKED P1) because of a BOOTSTRAP CIRCULARITY specific
to THOSE functions' own precondition chain — the EXECUTION ENGINE
itself (`_compile`, `oracle_sandbox.py`'s process isolation) has no
such circularity; it is a pure function of source text. Rev 2's Item 2
reuses the ENGINE, never the dead minting functions, avoiding
inheriting S6 PARKED P1's own defect (Fork F5 below).

### Item 1 (rev 2, R20-R22, R25-R27, R32): one artifact, prose is required, no admission-time code detector

**The artifact.** ONE `Artifact` per conjecture, always (no twin).
`content` (`ConjectureCandidate` path) or `claim`+`mechanism`
(`ReasoningCandidateProposal` path) remain REQUIRED, non-empty fields
(M22) — unchanged, already true today. `Interface.commitments` MAY
carry zero or more commitments (unchanged mechanism, M9).

**Enforcement of "never full code" (R20, R32) — NOT an admission
gate.** M25's own governing law ("this constrains what survives, not
what γ may emit") forecloses building a content-shape detector at
admission: doing so would be a NEW arbiter deciding "is this prose or
code" BEFORE criticism ever runs — precisely the "referee" R25/R26
reject. The actual enforcement is TWO-FOLD, both already-existing
mechanisms, zero new code:
1. **Structural**: the wire schema already requires non-empty prose
   fields (M22) — there is no wire-valid way to submit a candidate with
   NO prose field populated at all.
2. **Criticism, not detection**: if a model nonetheless writes
   code-shaped text INTO the prose field, `crit_argumentative`
   (unchanged, D1 census M6-M7) already lets any critic argue "this
   offers no explanation" as an ordinary case — exactly R25's "that's
   what criticism is for." No new contract field, no new guard, no new
   role.

**R-g argument.** Nothing here reads a candidate's content SHAPE to
rank, admit, or gate it — the wire's own required-field structure and
ordinary argumentative criticism are both KIND-BLIND mechanisms
(neither one branches on "is this formal or informal"), satisfying the
corrected, prose-only-protected direction of R-g (R19/R36) trivially:
there is no new mechanism here that could disfavor prose, because
there is no new mechanism here at all.

### Item 2 (rev 2, R23, R24, R33, R34): the optional code-commitment channel

**Shape.** A new optional wire field on BOTH candidate contracts (F2
Road B, approved, R28):
- `ConjectureCandidate` path: extend the EXISTING skeleton/
  `ForbiddenCase` mechanism's `eval` vocabulary (M23) with a new kind
  (proposed `program:candidate-checker`, name TBD at D3) whose `<ref>`
  is a content-addressed pointer into `harness.blobs` (mirroring how
  `oracle.py`'s own checker/property sources are already stored, D1
  census M3) rather than a `PROGRAMS`-dict name. This is an EXTENSION
  of an existing, already-reachable mechanism, not a new field.
- `ReasoningCandidateProposal` path: expose the eval-kind CHOICE M24
  found missing — `Countercondition`-shaped entries gain a way to
  declare `program:candidate-checker` (mirroring the SAME new kind
  above) instead of `proposal_envelope`'s current hardcoded
  `eval="observation"`.

**Execution.** Reuses `oracle.py::_compile`/`oracle_sandbox.py`'s
PROVEN sandboxed engine (M26) as the evaluator for the new kind — NOT
`property_oracle_commitment`/`admit_counterexample` (M3's own dead,
circular functions) and NOT a new sandbox implementation. Guarded by
the SAME safety discipline `ForbiddenCase` already enforces for
untrusted content (M23's own docstring: never an inline `predicate:`
for model-authored text; the new kind is a `program:` variant, keeping
that same discipline).

**Where it lives, and what refuting it does (R23, R34) — the whole
point of this correction.** The commitment lives DIRECTLY on the SAME
artifact's `Interface.commitments` — exactly like today's skeleton/
countercondition commitments (M23/M24), never a separate artifact.
`crit_program` (D1 census M10, UNCHANGED, zero new code) evaluates it
on the artifact's own cycle; a FAILING commitment registers a
DEMONSTRATIVE fail warrant with `target_id = this same artifact`,
refuting the WHOLE conjecture — **and this is CORRECT, not a problem
to bound or soften** (R34's own words: "failing ones refute
demonstratively, exactly as criticism should"). `execution_backed`/
`formally_backed` (D1 census M9, UNCHANGED, zero new code, no wrapper
function) already grant PROTECTION while the commitment passes, read
directly from `Interface.commitments` exactly as they do today for any
other commitment kind — the "incentive story" R34 asks for is fully
supplied by the EXISTING mechanism, unmodified.

**R-a (byte-identical absence).** The field is optional
(`default=None`/empty), mirroring `simulation_proposals`' own
`default_factory=list` precedent (D1 census M1) — a candidate that
never populates it behaves byte-identically to today on every existing
path (`_compile`/`crit_program`/`execution_backed` all already handle
"zero commitments" as their baseline case).

**R-g argument.** The new `eval` kind is READ by the exact same
functions that read every other kind today (`programs.evaluate`,
`execution_backed`, `formally_backed`, `crit_program`) — none of them
branch on WHICH kind a commitment is when deciding rank, admission, or
acceptance; they only ever ask "does this pass." Prose-only candidates
(no commitment at all) are UNCHANGED and UNTOUCHED by this item's own
code, satisfying R19's corrected, one-directional guardrail.

### Item 3 (rev 2, R9 — largely unchanged from rev 1, simplified): the verifiable kind signal

D1's census (M6-M9) already found kind is DATA
(`Interface.commitments` non-empty+evaluable = formal). Rev 2's
single-artifact model needs NOTHING new here — unlike rev 1's twin
(which needed a NEW `linked_encoding` reader for a cross-artifact
signal), a rev-2 candidate's kind is fully legible from ITS OWN
`Interface.commitments`, exactly as D1 measured. **R-c is satisfied by
the pre-existing mechanism, unextended.**

### Item 4 (rev 2, R10 — unchanged from rev 1's own finding, no twin-specific addition needed): kind-matched criticism forms

D1's census M8 found ONE shared pack template
(`render_crit_pack`), signaling kind via DATA
(`TARGET COMMITMENTS`/`_MACHINE_EVAL_NOTE`) already generic over ANY
commitment kind — a candidate carrying the new `program:candidate-
checker` commitment (Item 2) is shown to the critic by the EXISTING
rendering code with ZERO changes (the loop over
`target.interface.commitments` in `render_crit_pack`, D1 census M8,
does not special-case `eval` values). **R-d is satisfied by the
pre-existing pack mechanism.** No pack change, no contract change —
rev 2 needs none of rev 1's Item 4 pack addition (that addition existed
only to signal a CROSS-ARTIFACT twin link, which no longer exists).

### Item 5 (rev 2, R24, R35): relatedness, without a referee

"Directly related to the explanation" (R24) is enforced by REUSING
`relevance_trial`'s own shape (M21) — a cross-family JUDGE ENSEMBLE
ruling the narrow question "does this commitment's case follow from
the claim's own explanation," referential-integrity- and unanimity-
guarded, exactly as `rules/experiment.py::relevance_trial` already does
for property proposals. This is triggered the SAME way `relevance_trial`
is today: as a CRITICIZABLE CHALLENGE (a critic or the harness's own
relevance check may invoke it), never as a MANDATORY pre-admission gate
— consistent with M25's own law (nothing new constrains EMISSION) and
R25-R27 (ordinary criticism, no referee). A commitment whose relatedness
is never challenged simply stands, exactly as an unrefuted claim stands
today.

**R-g argument.** `relevance_trial`'s own docstring: "Judges never
touch a candidate's STATUS here — they rule on the property artifact
alone" (M21) — reused verbatim in spirit: a relatedness ruling affects
whether THIS SPECIFIC COMMITMENT counts as substantive, never a
rank/admission/scheduling term. Kind-blind by the same construction
D1's own R-g audit already validated for the underlying mechanism.

### Item 6 (rev 2, R36): R-g re-anchored to prose, `_standing_recrit_pool` re-decided

**R-g's corrected, one-directional guardrail (R19):** the ONLY
protected party is prose/informal — nothing protects FORMAL artifacts
from receiving MORE scrutiny than informal ones; that was never the
worry.

**`_standing_recrit_pool` (D1 census M6/M9(a)): STAYS AS-IS — decision
unchanged from rev 1, R-g argument now cleaner.** Under the corrected,
one-directional R-g, a mechanism that gives EXECUTION-BACKED artifacts
MORE re-criticism scrutiny (D1's own finding) is not even a candidate
violation — R-g never protected formal artifacts from extra scrutiny,
only prose from being disfavored. D1's own exhaustive attempt to find
a penalty against PROSE from this function (D1 census section 4(a))
found none; that finding is untouched by this amendment and is
RE-CONFIRMED, not merely carried over.

**Acceptance checks D3 must pass (re-derived from rev 1's own list,
R36; R1 forbids writing them as code this window):**
1. An informal-only run (no candidate ever populates the new
   commitment field) is BYTE-IDENTICAL to today — trivially true here
   since Item 1/Item 2 add nothing to the zero-commitment path (unlike
   rev 1, no new absence-tolerant Event field needs proving — there
   isn't one, R30).
2. A candidate whose new-kind commitment FAILS is refuted exactly like
   any other `crit_program` failure today — SAME test shape as
   `tests/test_oracle.py::test_crit_program_refutes_wrong_code_by_running_it`
   (D1 census M10's own citation), extended to the new `eval` kind.
3. A candidate whose new-kind commitment PASSES gains
   `execution_backed`/`formally_backed` protection exactly like any
   other passing commitment today — SAME test shape as
   `tests/test_oracle.py::test_execution_backed_true_only_when_passing`.
4. Neither `Scheduler._select_problem` nor `_standing_recrit_pool`
   gains a new term reading the new `eval` kind specifically (grep-
   provable, D1's own M9(a) method).
5. A relatedness challenge via the reused `relevance_trial` shape
   (Item 5) never mutates a candidate's `Status` directly — only
   whether ITS COMMITMENT counts as substantive.

### Test implications (R37)

**Existing tests that MOVE (new cases/assertions owed, not new files
necessarily):**
- `tests/test_wire_contracts.py`, `tests/test_conjecturer_turn_v4.py`,
  `tests/test_v6_patch_repair_and_wire.py`,
  `tests/test_schema_carries_every_prose_rule.py` — the new optional
  field on `ConjectureCandidate`'s wire shape (D1's own SCHEMA.md rule:
  "pin signatures whole").
- `tests/test_skills_models.py`, `tests/test_live_smoke_regressions.py`,
  `tests/test_semantic_freedom_constitution.py` — the new eval-kind
  choice on `ReasoningCandidateProposal`'s `counterconditions`.
- `tests/test_workload_formal.py` — the extended `ForbiddenCase`/
  skeleton eval vocabulary (new `program:candidate-checker` kind).

**Existing tests that MUST NOT MOVE (regression proof the correction
didn't leak anywhere):**
- `tests/test_oracle.py`, `tests/test_prose_refutation_boundaries.py`
  — `execution_backed`/`formally_backed`'s own body/signature, per D1's
  rev-1 blast-radius census, UNCHANGED (rev 2 needs this even more
  strongly than rev 1 did, since there is no wrapper function at all
  now — these functions are reused completely as-is).
- `tests/test_adjudication.py` — Pass 1/Pass 2 (D1 census M9(c)/M12),
  untouched by rev 2 exactly as by rev 1 (no new `RefRole`, no new
  cascade interaction — rev 2 doesn't even need M17's `RefRole` finding
  anymore, since there is no cross-artifact link to make invisible to
  it).

**New tests owed (none exist yet, named per item 6's five acceptance
checks above):** a `program:candidate-checker`-kind commitment refuting
its own artifact on failure; the same kind granting protection on
success; the R-g grep-provable absence of a new scheduling term; a
relatedness-challenge test proving it never touches `Status` directly.

### Item 7 (rev 2, R38): encoder-role delegation, corrected meaning

F3 Road A (approved, R29): new role `"encoder"`, `property_designer`
untouched. Corrected meaning (R38): **the coder seat authors commitment
CODE for the conjecturer's ALREADY-ADMITTED prose** — not a separate
encoding artifact (rev 1's own framing). Two-phase, mirroring the SAME
draft-then-register shape M23/M24 already use: (1) the conjecturer's
own turn is admitted first, prose-only or with a commitment it authored
itself, exactly as today; (2) if the `"coder"` seat is bound (M16,
mint-time, per `docs/map/CON-seats.md`), a follow-up call to the
`"encoder"` role, given the ADMITTED artifact's own prose as input,
drafts commitment source text, which is then attached to the SAME
artifact via the SAME two-phase draft/register compilation path
(`compile_interface_draft`, unchanged) — never a new artifact, never a
new event. When NOT bound: the conjecturer's own turn embeds the
commitment inline (Item 2's own fallback, mirroring M1's existing
capability-channel pattern).

**R-g argument (CLAUDE.md's second design law, REQUEST.md C4).** The
encoder's output is criticized by the EXACT SAME `crit_program`/
`execution_backed` mechanism as a conjecturer-authored commitment (Item
2) — delegating AUTHORSHIP never changes what counts as EVIDENCE.

### Frozen-surface contact forecast, re-derived from scratch (R30 — assumes NO grant)

- **Surface 1 (`capabilities/state.py`): NONE.** Unchanged from rev 1's
  own finding — this design never touches capability-channel state.
- **Surface 2 (`harness.py` event application): NONE EXPECTED —
  IMPROVED FROM REV 1.** Rev 1 needed a new `twin_repair` Event payload
  (plausible contact). Rev 2 needs NO new Event payload at all: the new
  commitment attaches via the EXISTING two-phase draft/register
  compilation path at ordinary artifact-admission time (M23/M24's own
  precedent), the same way skeleton/countercondition commitments
  already do today. `harness.py`'s event-application logic sees nothing
  new to apply.
- **Surface 3 (replay-validation formats): NONE EXPECTED — IMPROVED
  FROM REV 1.** No new record TYPE; the new commitment is an ordinary
  `Commitment` (already a first-class, existing type) with a new `eval`
  KIND STRING, not a new schema shape.
- **Surface 4 (manifest schemas + validators): CONTACT EXPECTED,
  narrower than rev 1.** A new wire-contract version (the optional
  field + new eval-kind vocabulary entry on both candidate contracts)
  is a new `ContractVersionPolicyV3` entry, mirroring every prior
  version bump; a new role (`"encoder"`) needs a route/role binding
  entry. No twin-related manifest field is needed (rev 1's own
  speculative addition is gone).
- **Surface 5 (qualification subject digests): CONTACT CONFIRMED
  (M20, unchanged reasoning).** Same mechanism as rev 1 — a new
  contract version or role changes `qualification_subject_payload`'s
  hashed manifest dump. Old cached qualifications for unchanged
  manifests remain valid.
- **Frozen-adjacent `route_fingerprint`: CONTACT EXPECTED,** for the
  new `"encoder"` role's route entry — unchanged reasoning from rev 1.
- **`oracle.py`/`oracle_sandbox.py` (not a frozen surface, but load-
  bearing infrastructure being REUSED, not modified):** rev 2 proposes
  reusing `_compile`'s existing guarded-exec engine as-is (M26) — no
  change to its own body is proposed; only a NEW CALLER (the new `eval`
  kind's dispatch in `programs.evaluate`) is named, which touches
  `programs.py` (not itself one of the five frozen surfaces, but
  central enough to name explicitly).

**Net effect versus rev 1: two of five surfaces (2 and 3) drop from
"plausible contact" to "none expected" — the single-artifact
correction is measurably smaller in frozen-surface footprint, not only
simpler in shape.**

### Blast-radius census (rev 2 additions to rev 1's own census)

```
$ grep -rl "programs\.evaluate\|programs\.py" tests/ docs/map/ 2>/dev/null | grep -v pycache | grep "docs/map"
docs/map/SEAM-evaluation-x-ontology.md
docs/map/SUB-evaluation.md
docs/map/SUB-periphery.md
docs/map/SEAM-evaluation-x-rules.md
```
`programs.py::evaluate`'s own dispatch (`if kind == "predicate"... elif
kind == "program"...`) gains one new `elif` branch for the new kind —
all 4 map documents above EXPECTED TO MOVE (new dispatch branch is new
behavior, needs a new check per SCHEMA.md's own rule "new behaviour
needs a new check that would fail if the behaviour regressed").
`SUB-periphery.md`'s own hit is incidental (a `programs.py` mention
unrelated to `evaluate`'s dispatch) — D3 must confirm this at execution
time before assuming it moves too.

```
$ grep -rln "oracle\._compile\|from deepreason.oracle import _compile" tests/ 2>/dev/null
(no output — exit 1, zero hits)
```
`oracle.py::_compile` is a PRIVATE function, never imported or tested
by name directly — it is exercised only indirectly through
`programs.evaluate`'s public dispatch (`tests/test_oracle.py`'s own
property/checker execution tests). MUST NOT MOVE for `_compile`'s OWN
body (rev 2 proposes a NEW CALLER via a new `programs.evaluate` dispatch
branch, never a change to the guarded-exec function itself) — D3's own
regression is therefore an ADDITION to `test_oracle.py`'s existing
coverage pattern, not a change to any existing assertion.

```
$ grep -rl "relevance_trial" tests/ docs/map/ 2>/dev/null | grep -v pycache
tests/test_judge_ensemble_boundary.py
tests/test_properties.py
docs/map/SEAM-llm-x-rules.md
docs/map/CON-warrants-and-attacks.md
docs/map/SEAM-adjudication-x-authority.md
docs/map/SUB-rules.md
```
MUST NOT MOVE for all 6 — Item 5 proposes reusing `relevance_trial`'s
own SHAPE at a NEW call site (candidate-commitment relatedness), never
modifying the function itself or its existing property-relevance call
site.

### Options (forks) — rev 2

**F5 — how does the new commitment's execution engine get wired in
without inheriting S6 PARKED P1's circularity (M26)?**
- Option A: reuse `property_oracle_commitment`/`admit_counterexample`
  directly (M3's own dead functions). REJECTED — inherits the exact
  bootstrap circularity D1 diagnosed (minting the first commitment of
  this shape requires an existing one).
- Option B: reuse ONLY `oracle.py::_compile`/`oracle_sandbox.py`'s
  EXECUTION ENGINE via a NEW dispatch branch in `programs.evaluate`,
  never touching the dead minting functions. RECOMMENDED — no
  precondition chain to bootstrap; the new kind is minted directly by
  `compile_interface_draft` (already reachable, M23/M24), same as
  every other commitment kind.

**F6 — is the relatedness check (Item 5) mandatory pre-admission or
purely reactive?**
- Option A: mandatory pre-check before a commitment is accepted at all.
  REJECTED-leaning — this IS the referee shape R25/R26 warn against: a
  gate deciding relatedness BEFORE ordinary criticism ever runs.
- Option B: purely reactive — a relatedness challenge is available
  (reusing `relevance_trial`'s shape) but never required; an
  unchallenged commitment simply stands. RECOMMENDED — matches M25's
  own governing law (emission unconstrained) and R25-R27 exactly.

**F7 — does the new `eval` kind join `execution_backed`'s NARROW
`EXEC_PROGRAMS` set, or only `formally_backed`'s wider substantive
set?**
- Option A: add it to `EXEC_PROGRAMS` (D1 census M9's own set:
  `exec_oracle`/`property_oracle`/`dataset_oracle`). REJECTED-leaning —
  that set's own semantics include counterexample admission
  (`admit_counterexample`, M3), machinery this design does not build or
  need; adding to it silently promises behavior not designed here.
- Option B: the new kind counts toward `formally_backed`'s wider
  substantive-and-evaluable test (M9) ONLY, not `execution_backed`'s
  narrower counterexample-eligible set. RECOMMENDED — grants the
  PROTECTION incentive (R34's own "shield") without silently extending
  counterexample machinery this tranche never measured or specced.

## Budget (rev 2)

**Headline: ~950 lines of D3 implementation, forecast by item —
computed as the sum below (rev 1's ~1450-line forecast is superseded;
kept above for the record):**

| Item | Forecast (lines) | Basis |
|---|---|---|
| Item 1 (no admission gate — zero new code, documentation of existing behavior only) | 0 | M25: nothing is built |
| Item 2 (new eval kind + wire field on both candidate contracts + `programs.evaluate` dispatch branch) | 280 | mirrors M23/M24's own existing mechanism size, extended |
| Item 3 (kind signal) | 0 | M9: pre-existing, unextended |
| Item 4 (pack rendering) | 0 | M8: pre-existing, unextended |
| Item 5 (relatedness, reusing `relevance_trial`'s shape at a new call site) | 120 | a new call site wiring an EXISTING function's shape, smaller than authoring a new mechanism |
| Item 6 (R-g acceptance checks, 5 named) | 200 | same basis as rev 1: ~40 lines/regression test |
| Item 7 (encoder role registration) | 250 | unchanged from rev 1's own F3 estimate |
| Map document update (`CON-conjecture-kinds.md` v2) | 100 | smaller than rev 1's 230-line estimate — no twin/RefRole/Event sections needed |
| **Sum** | **950** | 0+280+0+0+120+200+250+100 = 950 |

This SPEC.md's own rev-2 addition size: this appended section. Total
tranche commits: REQUEST.md (2, capture + amendment), SPEC.md rev 1
(1), SPEC.md rev 2 (this commit) — 4 total. Frozen surfaces touched by
THIS tranche itself: NONE (SPEC ONLY, R1) — the forecast above is for
D3's own future work.

Rubric (rev 2): 6/6 yes
- every new R (R19-R40) has a spec item or is explicitly resolved
  (R28-R30 resolved directly by operator approval, not re-derived):
  yes.
- blast-radius census pasted and classified: yes (rev 2 additions
  above; rev 1's own census entries for `execution_backed`/
  `formally_backed`/adjudication apply unchanged and are cited, not
  repeated).
- frozen-surface contact forecast re-derived from scratch, assuming no
  grant: yes (R30's own instruction followed literally).
- every mechanism the amendment names traced to code before being
  adopted: yes (M21's `relevance_trial`, M23/M24's existing commitment-
  attachment mechanisms, M26's execution engine — all verified to exist
  and reach the relevant call sites before being designed around).
- DESIGN-AND-STOP: yes — six new measurements (M21-M26), three new
  forks (F5-F7) each priced with a recommendation citing a measurement.
- nothing untraceable to an R/C/M number: yes (re-read pass performed).

## Decision sheet (rev 2) — remaining forks

**F5 — execution engine wiring.** Recommendation: Option B (reuse
`_compile`/`oracle_sandbox.py` directly via a new `programs.evaluate`
dispatch branch, never the dead minting functions). See F5 above for
the full pricing.

**F6 — relatedness check timing.** Recommendation: Option B (purely
reactive, no mandatory pre-admission gate). See F6 above.

**F7 — which protection set the new kind joins.** Recommendation:
Option B (`formally_backed` only, not `EXEC_PROGRAMS`). See F7 above.

Every road above (F5-F7) awaits the operator's words before
`dr-plan-steps` (D3) runs, per R16/R40. REQUEST.md and this SPEC.md
(rev 2) are committed and pushed; this tranche STOPS here again, per
R40.
