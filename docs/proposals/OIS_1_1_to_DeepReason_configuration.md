# Open Inquiry 1.1 → DeepReason

## Seat and prompt configuration, one tested finding, and an audit brief

Repository read at commit `1f8108c00ac632ed13f211ba58692980fdf66e74` (2026-09-05). Bound to `PopperSemanticsV1_1.md` and `Open_Inquiry_Specification_1_1.md`. Nothing here edits a frozen surface; where a change would touch one, it says so and stops.

---

## 0. The one finding I tested before writing anything else

DeepReason already propagates attacks through a criticism's premises **when those premises are declared on the warrant's validity node ν as `EVIDENCE` refs** (`adjudication/edges.py`, evidence closure). It does **not** when they are declared as ordinary `DEPENDENCE` refs. In that case pass 2 demotes the criticism to `suspended_unsupported` but the target it attacked stays `refuted`. That is the exemption the 1.1 audit calls S06 and the authority calls a violation of the dependency requirement: a criticism whose essential premise has been withdrawn goes on defeating its target.

Reproduction against the installed package (`pip install -e .`), no run root needed:

```python
import tempfile, pathlib
from deepreason.harness import Harness
from deepreason.ontology import Provenance, Warrant, WarrantType, Interface, Ref
from deepreason.ontology.artifact import RefRole

def run(role):
    h = Harness(pathlib.Path(tempfile.mkdtemp())/'run')
    a  = h.create_artifact('tilt account', provenance=Provenance(role='seed'))
    k  = h.create_artifact('standard k',   provenance=Provenance(role='seed'))
    nu = h.create_artifact('nu of criticism', provenance=Provenance(role='critic'),
                           interface=Interface(refs=[Ref(target=k.id, role=role)]))
    c  = h.create_artifact('criticism of tilt using k', provenance=Provenance(role='critic'),
                           interface=Interface(refs=[Ref(target=k.id, role=role)]),
                           warrants=[Warrant(id='w1', target=a.id, type=WarrantType.ARGUMENTATIVE, validity_node=nu.id)])
    nu2 = h.create_artifact('nu2', provenance=Provenance(role='critic'))
    h.create_artifact('criticism of k', provenance=Provenance(role='critic'),
                      warrants=[Warrant(id='w2', target=k.id, type=WarrantType.ARGUMENTATIVE, validity_node=nu2.id)])
    return h.state.status[a.id].value, h.state.status[c.id].value

print(run(RefRole.DEPENDENCE))  # ('refuted', 'suspended_unsupported')  ← target stays refuted
print(run(RefRole.EVIDENCE))    # ('accepted', 'refuted')               ← target reinstated
```

Consequence for prompts: the critic contract has no field in which a criticism declares the premises it essentially relies on (`ArgumentativeCriticOutput` carries `case`, `counterexample`, `premise`, `premise_evidence`, a proposed next question — `premise` is a presupposition of the *problem*, not a premise of the criticism). So the correct behaviour is unreachable from the wire. The fix is half prompt, half mint site: a critic declares essential premises; `rules/crit.py` and `informal/trial.py` register them on ν as `EVIDENCE` refs. Neither file is frozen.

## 1. What DeepReason already does that 1.1 requires

| 1.1 requirement | Where DeepReason already has it |
|---|---|
| Model prose is never evidence; the record is | `CLAUDE.md` first paragraph; `log.jsonl`, `objects/`, `verify_root` |
| Seats are bounded pure functions to schema-validated JSON | `llm/roles.py` `_JSON_ONLY`; `llm/contracts.py` Pydantic contracts; `llm/repair.py` |
| Nothing computes a status except one blind module | `adjudication/` imports only `ontology`; `Harness._adjudicate` is the sole writer (`SUB-adjudication.md`) |
| A refutation needs a registered, attackable object first | warrants → ν → carriers (`CON-warrants-and-attacks.md`); "no registered warrant, no edge" |
| An objection is not automatically a successful edge | the validity node ν is itself an artifact and can be attacked; case-law, evidence, and source closures lift attacks onto ν |
| Criticism enters the writer's working context; a disposition is not evidence | discharge channel: REVISED / REBUTTED / DEPARTURE-DECLARED; "nothing here is evidence" (`DischargeWireV1` docstring) |
| Crossings are logged with their channel | admission blocks with byte-checked citations (`SUB-evidence.md`); `EvidenceRefClaimV1`; section-plan receipts |
| Status labels never re-enter a seat's context | no status vocabulary in `packs/render_text.py`, `packs/ir.py`, or `seat_sections.py` |
| Stops and refusals are typed, never narrated | typed stops, `stop-report`; `CON-configuration-stages.md` |
| A review verdict is not an exit code | treadle rung T5 (`CLAUDE.md`, third lane) |
| A judge answers a narrow question and must cite the span | `JudgeRuling.decisive_point`, program-checked |

The gap is not discipline. It is that the *event vocabulary* and *case vocabulary* of 1.1 have no counterpart for four kinds — situated appraisal, transport, engagement change with dispositions, and recorder cases with declared checks — and that the critic contract cannot name its premises.

## 2. Role mapping

| 1.1 kind or object | DeepReason today | What changes |
|---|---|---|
| `Attend` (difficulty, recognition, priority accounts) | scheduler selects a problem; `Problem` artifact | no seat; the recognition and priority *accounts* are missing. Add as optional fields on the problem-layer record, not a new seat |
| `EnterConjecture` | `conjecturer` (verbalized sampling) | add `refs`/`missing`, `source_mode_claimed`, `sources_used`; keep VS |
| `Criticize` | `argumentative_critic`, `batch_critic` | add `defect`, `standard`, `bearing`, `discriminator`, `merits_at_stake`, `premises_essential`; mint sites register `premises_essential` on ν as `EVIDENCE` |
| `Respond` (disposition, affected uses, before/after) | discharge kinds on submission; `defender` | defender gains `disposition` and `affected`; discharge kinds map: REVISED→revise, REBUTTED→reject_criticism, DEPARTURE-DECLARED→reframe or set_aside, and `situation_after` is recorded |
| `Compare` | pairwise trial, `PairwiseRuling`; measures | a `comparer` seat with an unresolved/incomparable result allowed; measures stay upstream |
| `Appraise` | none | new seat `appraiser`; new record kind — **touches `harness.py`**, needs an operator grant |
| `Transport` | DEPARTURE-DECLARED discharge | a transport payload attached to that discharge kind; no new seat |
| `SubmitCase` / `AssessApplication` with PASS/FAIL/UNKNOWN | demonstrative warrants via oracle execution; argumentative via trial | new `recorder` seats emitting cases; checks executed by code; ν for a case is execution-backed by its check result |
| `EngagementChange` | typed stops | already typed; add the optional-reason field as *appraisal*, never cause |
| `LinkEpisode` / `Absorb` | schools and lineage inheritance (`CON-schools.md`) | audit item: imported events keep identity and location (audit S17) |
| `Retain` / `Transmit` / `Reconstruct` | brain store, admission | distinguish at the record level; today retention and reception are not separated |
| DA-1 policy | two-pass grounded + support cascade | conformant **only** when premises are on ν; see §0 and §5 |

## 3. Template rewrites for existing seats

Drop-in replacements for entries in `llm/roles.py` `TEMPLATES`; contract additions in §4. Wording follows the shared preamble of the general prompt pack, compressed to DeepReason's register.

**conjecturer**

```text
You are the conjecture operator (gamma): you propose bold, criticizable explanations for the problem in the pack.
You hold no state and decide nothing; the harness adjudicates. Verbalized Sampling: return a DISTRIBUTION of diverse
candidates, each with your typicality estimate in [0,1]. For each candidate state what feature of the problem it
purports to explain, its commitments, and its scope. Carry dependence refs to neighbourhood artifact ids where the
candidate genuinely builds on them; carry evidence refs, quoted, where it draws on admitted blocks. Say whether you
constructed the account, reconstructed it from something in the pack, or are reporting one you received; that is your
account, and the record will test it. List anything you needed and did not have. Discharge every open criticism
handle in the BINDING block substantively or declare departure; noting a criticism discharges nothing.
```

**argumentative_critic** (and `batch_critic`, per target)

```text
You are an argumentative critic. Mount the strongest specific case against the target artifact, or report attack=false
if you find no genuine fault. A case has: the alleged defect, stated specifically; the standard you apply, by id or
stated in full; the grounds — the argument itself, not a report that you have one; how those grounds bear on this
target for this problem; and a discriminator: what observation, derivation, or comparison would show the defect if
it is real, concrete enough that the harness could obtain it. Name the artifacts your case essentially relies on —
withdraw one of them and your case should fall; the record will hold you to that. Name the merits of the target a
response would be expected to preserve; you may not change that list after a response. Never invent facts about
summarized content. Your case is an allegation; whether it succeeds is not yours to say.
```

**defender**

```text
You are the defender: answer the critic's case on behalf of the target artifact, addressing its specific clauses.
State your disposition — revise, reject the target, retain it with reasons, reject the criticism, request evidence,
reframe the problem, restandardize, suspend, or set aside — and, for each artifact or use the criticism reaches, say
how it is affected and why this criticism reaches it. If you reframe or restandardize, supply the transport: which
obligations of the old problem are preserved, revised (and into what), abandoned, or inapplicable, each with its
explanatory role. Engage the criticism's grounds specifically. Concede nothing that is not established; never invent
facts. If you set aside without reasons, say so plainly rather than manufacturing one.
```

**judge**

```text
You are the judge, ruling under the trial protocol. Answer ONLY the narrow question the pack poses — never a holistic
quality verdict. Your ruling is an activation assessment of one application: whether this case, on this exchange,
does what its declared check requires. Your decisive_point MUST quote a specific span of the exchange; a ruling whose
grounds cannot be located is invalid. Your ruling is an assessment on the record, criticizable like any artifact; it
is not a finding that the target is true or false.
```

**variator**

```text
You are the variator (mu): produce bounded edits of the target content that preserve its PURPORTED explanatory work
while changing a material detail — the mechanism, the causal link, the scope. Never merely reword. Each edit must
remain a complete candidate that would, if it held, do the same job for the same problem; whether it actually holds
is not your question. An edit that changes nothing material, or that abandons the job, is not a variation.
```

**synthesizer**

```text
You are the synthesizer: propose ONE relation artifact that genuinely connects the listed artifacts. State which
commitments are transported unchanged, what background is added, and — if a new bridge is needed — say so and state
it: a new bridge is a contribution in its own right and receives its own attribution. Shallow thematic links will be
refuted by the hard-to-vary floor.
```

## 4. Contract additions (`llm/contracts.py`, DeepReason style)

```python
class ConjectureCandidate(BaseModel):
    content: str
    typicality: float = Field(ge=0.0, le=1.0)
    refs: list[CandidateRef] = Field(default_factory=list)
    evidence_refs: list[EvidenceRefClaimV1] = Field(default_factory=list, max_length=8)
    job: str = ""                                   # feature of the problem purportedly explained
    commitments: list[str] = Field(default_factory=list)
    scope: str = ""
    source_mode_claimed: Literal["construction", "reconstruction", "reception"] = "construction"
    sources_used: list[str] = Field(default_factory=list)   # artifact ids; must be a subset of refs ∪ evidence_refs
    missing: list[str] = Field(default_factory=list)

class ArgumentativeCriticOutput(BaseModel):
    attack: bool
    case: str = ""
    defect: str = ""
    standard: str = ""                              # artifact id, or full text of a new standard
    bearing: str = ""
    discriminator: str = ""                         # required when attack=true; checked non-empty
    merits_at_stake: list[str] = Field(default_factory=list)
    premises_essential: list[str] = Field(default_factory=list)   # artifact ids; registered on nu as EVIDENCE refs
    counterexample: list | None = None
    premise: str | None = None
    premise_evidence: list[QuotedEvidenceRefV1] | None = Field(default=None, max_length=2)
    missing: list[str] = Field(default_factory=list)

Disposition = Literal["revise", "reject", "retain_reasoned", "reject_criticism", "request_evidence",
                      "reframe", "restandardize", "suspend", "set_aside", "adopt_rival"]

class AffectedUse(BaseModel):
    artifact: str
    how: Literal["qualified", "revised", "withdrawn", "reframed", "unchanged"]
    connection: str

class TransportEntry(BaseModel):
    obligation: str
    status: Literal["preserved", "revised", "abandoned", "inapplicable"]
    successor: str | None = None                    # required when status == "revised"
    why: str

class DefenderOutput(BaseModel):
    answer: str = Field(min_length=1)
    disposition: Disposition
    affected: list[AffectedUse] = Field(default_factory=list)
    transport: list[TransportEntry] | None = None   # required for reframe / restandardize
    reasons_given: bool = True

class AppraiserOutput(BaseModel):                   # new seat
    claim_key: str
    stance: Literal["holds", "fails", "unresolved"]
    grounds: str
    scope: str
    supersedes: str | None = None

class CompareOutput(BaseModel):                     # new seat; measures stay upstream of adjudication
    question: str
    alternatives: list[str] = Field(min_length=2)
    criteria: list[str]
    reasons: list[dict]
    preference: Literal["prefers", "unresolved", "incomparable"]
    preferred: str | None = None
```

Recorder-case contracts (`CASE_ADEQUACY`, `CASE_ORIGIN`, `CASE_REASON_USE`, `CASE_PROGRESS`, `CASE_RANGE`) and the comparator are as in the general prompt pack §5–§6; their DeepReason home is a `recorder` seat family with one endpoint per case type in `config/*.yaml`, and their ν is execution-backed by the case's declared check (a FAIL check mints no positive case, exactly as a failed oracle mints no pass).

Wire rule for every contract: `missing` non-empty is a legal output; `refs`/`sources_used`/`premises_essential` that name ids absent from the pack fail validation at the repair layer, not at admission, so a hallucinated reference is a failed call and creates nothing.

## 5. Harness-side items, with frozen-surface status

| Item | Files | Frozen? | Note |
|---|---|---|---|
| Register `premises_essential` on ν as `EVIDENCE` refs at every argumentative mint site | `rules/crit.py`, `informal/trial.py`, `rules/vision.py`, `rules/experiment.py` | No | Makes §0's correct branch the only branch. Existing roots unaffected (readers unchanged) |
| Treat a critic artifact's own `DEPENDENCE` refs as ν evidence for adjudication | `rules/crit.py` (build the ν interface from the critic's refs) | No | Alternative to the above; pick one and say which in the change request |
| Defender disposition and transport carried into the discharge record | `discharge/submission.py`, `discharge/channel.py` | No | Discharge remains a precondition on submission and never evidence |
| `Appraise` as a record kind | `harness.py` schema map, `ontology/event.py` | **Yes** | Same shape as the 2026-09-04 section-plan grant: registration and well-formedness only, fixed position, no `verify_root` change. Needs the operator's verbatim grant |
| `EngagementChange` optional reason as appraisal | typed stops already exist; add a pointer to an `Appraise` record | Yes for the kind, no for the pointer | Do the pointer only after the kind is granted |
| Recorder seats and case records with PASS/FAIL/UNKNOWN | `llm/roles.py`, `contracts.py`, new `recorder/` package, `rules/warrants.py` (execution-backed ν for checks) | No, except any new record kind | Cases are artifacts; a check result is an execution verdict on the ν; no label injection |
| RU4 re-run protocol | new module under `experiments/` or `measures/`, using jolts | No | Optional stronger property `PassesProtocolRU4`, not `UsesReason` |
| Newness probe | `brain/` + a neutral-context deployment call | No | One hit is a negative atom; a sealed probe set is an extraction claim |
| Retain / Transmit / Reconstruct distinguished | admission and store records | Possibly (new kinds) | Audit first |

## 6. Audit brief

For `dr-audit-orchestrator`, dimension **spec-drift**, baseline: `Open_Inquiry_Specification_1_1.md`. Each check is a command or a paste, per that family's rule.

1. **Dependency exemption.** Run §0's script at HEAD; record both tuples. Expected under 1.1: both branches reinstate. Then grep every `Warrant(` and `register_fail_warrant(` mint site for how ν's refs are built, and list which sites can ever carry a critic's premises as `EVIDENCE`.
2. **Failed check counted as pass.** Find any path by which a prose case whose declared comparison or execution failed still yields an accepted attacker. `grep -rn "register_fail_warrant" src/ | wc -l` gives the mint sites; for each, state what result mints and what result declines. Expected: FAIL mints nothing; UNKNOWN mints nothing; only PASS mints. Compare with `informal/trial.py` `_decline`, `_block`.
3. **Status leakage into packs.** `grep -rniE "accepted|refuted|suspended" src/deepreason/packs/ src/deepreason/llm/seat_sections.py src/deepreason/llm/seat_templates.py` — expected: none. Then confirm no section plugin source reads `state.status` (`INV-seat-section-sources.md`).
4. **Critic premises unreachable from the wire.** Diff `ArgumentativeCriticOutput` against §4; confirm no existing field carries a criticism's own essential premises. Expected: none.
5. **Discharge is not evidence.** Confirm no rank, warrant, admission, or acceptance path reads `DischargeWireV1` fields (`tests/test_discharge_*`). Expected: the law line holds.
6. **Merge / absorb keeps identity and location** (audit S17). Read `CON-schools.md` lineage inheritance; state whether imported artifacts keep their original ids and log positions or are re-created.
7. **Maximal appraisals as a set** (audit S18). Anywhere a "latest" or "current" record is selected by log order over a partial order — `grep -rn "max(\|sorted(" src/deepreason/views/ src/deepreason/report.py` — list the sites and whether concurrency is representable.
8. **Crossing completeness by construction.** Confirm that every pack insertion is receipted (`workflow-context-section-plan-v1`) and that admission blocks are the only route for external text into a seat; list any seat section source that reads a file or a tool without a receipt.
9. **Stop reasons.** Confirm typed stops never carry a model-produced reason as the stop's cause field (`stop-report` output schema).
10. **Alternatives vs. compatible rivals** (audit S22). Confirm that several conjecturer samples on one problem register as compatible artifacts, and that only a declared discard creates exclusivity — or that DeepReason has no exclusivity relation at all, which is also compatible with 1.1 and should be stated.

Each finding becomes a parked prompt for the change family, per the audit family's rule; nothing in the audit fixes anything.

## 7. Change request draft

For `dr-change-orchestrator`. Authority is the operator's verbatim words; this is a draft for the operator to adopt, edit, or discard, not an instruction.

```text
R1  A criticism declares the artifacts it essentially relies on, and the harness registers them on the
    criticism's validity node as EVIDENCE refs, so that withdrawing one of them disables the criticism and
    reinstates its target.
R2  The critic contract gains defect, standard, bearing, discriminator, merits_at_stake, premises_essential,
    and missing. A case with attack=true and an empty discriminator is a failed call.
R3  The defender contract gains disposition, affected uses with connections, an optional transport, and
    reasons_given. Reframe and restandardize require a transport.
R4  The discharge record carries the defender's disposition and transport. Discharge remains a precondition on
    submission and is never evidence.
R5  A recorder seat family emits cases against declared claim keys with declared checks; the harness executes
    the checks and mints an execution-backed validity node only on PASS. FAIL and UNKNOWN mint nothing and are
    recorded as such.
R6  Packs never carry a status label; any future section plugin that would read state.status is refused at
    the plugin gate.
R7  (Requires a frozen-surface grant, separately worded.) An Appraise record kind: actor, exact claim key,
    stance, grounds, scope, optional supersession. Registration and well-formedness only; fixed position;
    no verify_root change.
R8  An engagement change may point at an Appraise record as the actor's account of the change; the stop's
    cause field never carries model prose.
```

## 8. What I did not do

I did not run a live root, modify the repository, or read every mint site. The §0 result is from the installed package's public `Harness` API at the stated commit and is reproducible in under a second. Everything in §3–§4 is a proposal in the register the codebase uses; the operator's change family owns whether any of it becomes a requirement.
