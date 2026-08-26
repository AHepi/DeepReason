<!-- DR-CON-discharge-channel -->
Verified-at: a5a435e3e
Verify: python -m pytest tests/test_discharge_contract.py tests/test_discharge_channel.py tests/test_discharge_submission.py tests/test_discharge_wire.py -q
Owns: src/deepreason/discharge/__init__.py, src/deepreason/discharge/policy.py, src/deepreason/discharge/channel.py, src/deepreason/discharge/submission.py
Seams: DR-SEAM-llm-x-rules
Seams-undocumented: discharge-channel x adjudication, discharge-channel x workflow

# The discharge channel — criticism in the writer's working context

## What it is

Criticism that is recorded and then routed nowhere does no causal work. W2
measured exactly that on this tree: across the two newest and largest roots,
**0 of 196 LLM attacks were ever exposed to a later conjecture dispatch**, and
every status a criticism moved was moved by the problem's own admission
criteria rather than by anything a critic seat wrote
(`experiments/2026-08-26-run-anatomy-w2-criticism/RESULTS.md`). The external
protocol it points at names the fix as structural rather than a prompt change:
criticism entering a separable ADVICE field gets neglected; criticism entering
the solver's WORKING CONTEXT, with re-submission requiring it DISCHARGED, is
the interface that coupled
(`docs/RESEARCH_FINDINGS_Q1Q10_2026-08-22.md` Q5).

This channel is that structure. Open criticisms on a problem render inside the
conjecturer's BINDING block — beside the criteria a candidate must satisfy, not
among the advisory sections — each carrying its claim, its cited span, and a
stable handle. A candidate submitted on a problem carrying open handles must
discharge each one: REVISED, REBUTTED, or DEPARTURE-DECLARED. An undischarged
submission is returned ONCE with the open list and then ACCEPTED with a typed
undischarged disclosure.

Two things it is deliberately NOT, both because the evidence says so:

- **It is not an acknowledgment requirement.** ACK-required was tested and
  measurably LOWERED final accuracy (Q5, "A failed compliance control"). Every
  discharge kind requires substantive content; there is no kind, and no field,
  by which merely noting a criticism discharges it.
- **It is not a gate that can kill a submission.** Disclose, never die — the
  all-configurations law at the submission boundary. No candidate is ever
  refused for an undischarged handle.

## The three layers (`DR-INV-signal-contract`'s own vocabulary)

| Layer | Holds | What it takes to change |
|---|---|---|
| **FROZEN** | the interface `deepreason.discharge` exports, and the law that a discharge never reaches a label, a warrant, a rank or an admission decision | an operator design law |
| **VERSIONED** | `DISCHARGE_KIND_DECLARATIONS` and `DISCHARGE_POLICY_PRESETS` — declarations with digests, not wiring | a declaration plus a recorded decision |
| **FREE** | which preset `Config.DISCHARGE_POLICY` names, and the caps inside a preset's envelope | ordinary configuration |

The derivation is the point, exactly as it is for signals: two hand-maintained
copies of one fact is how a registry stops being a contract.

`check: python -c "from deepreason.discharge.policy import DISCHARGE_KIND_DECLARATIONS, KINDS; assert KINDS == {n: d.asserts for n, d in DISCHARGE_KIND_DECLARATIONS.items()}"`

A NEW discharge kind enters by DECLARATION. It reaches the wire schema's enum,
the submission screen and the pack render without `rules/conj.py`,
`llm/packs.py` or `llm/wire.py` being edited — which is checkable, and is
checked, because a modularity claim without a failable check is decoration.
The check is not merely green — it was driven RED by hard-coding the enum in
`llm/contracts.py` and green again on restore
(`experiments/2026-08-26-change-f1-discharge-criticism-channel/proof/arch_red.txt`).

`check: python -m pytest tests/test_discharge_contract.py::test_a_fourth_kind_enters_by_declaration_alone -q`


The three consumers name no kind literally; if one did, adding a kind would
mean editing the submission path, which is what the operator's law forbids.

`check: test -f src/deepreason/rules/conj.py && test -f src/deepreason/llm/packs.py && test -f src/deepreason/llm/wire.py && ! grep -qE '"(revised|rebutted|departure_declared)"' src/deepreason/rules/conj.py src/deepreason/llm/packs.py src/deepreason/llm/wire.py`

## Interface-only consumption

Nothing outside the package imports a submodule of it. `controller.py`'s
boundary test is the model: the check exists to fail the day the boundary
stops holding, not because it is in danger today.

`check: python -m pytest tests/test_discharge_contract.py::test_no_consumer_reaches_past_the_interface -q`

The package's own `deepreason` imports are confined to `ontology`, `config`
and `programs`. It does NOT import `llm`, `rules`, `adjudication`, `scheduler`
or `informal` — the render returns a string and `llm/packs.py` decides what to
do with it, so the pack layer learns nothing about criticism and this package
learns nothing about packs.

`check: python -m pytest tests/test_discharge_contract.py::test_the_package_consumes_only_what_it_declares -q`

## THE LAW LINE

> Discharge constrains how content is GENERATED — a precondition on SUBMISSION,
> nothing more. It never constrains what counts as EVIDENCE. No discharge
> field, kind, count or record may feed a label, a warrant, a rank, an
> admission decision, or any adjudication pass. A REBUTTED discharge enters the
> ordinary graph as an ordinary artifact and is judged there, by criticism,
> like anything else. Discharge kinds carry no rank and no admission weight.

This is the operator's standing seats guardrail — "seats change how content is
GENERATED, never what counts as EVIDENCE" (CLAUDE.md) — and the
formalism-optional law (`DR-CON-conjecture-kinds`'s R-g) applied here. It is
pinned as an ABSENCE, in the shape `DR-CON-conjecture-kinds`'s sibling uses,
with every negative grep paired against a positive anchor on the same tree so
a moved directory fails the test rather than making it vacuous.


R8's half is structural rather than promised: the declaration record has no
numeric field, so there is no weight for any configuration to set.

`check: python -c "from deepreason.discharge.policy import DischargeKindDeclaration as D; assert not [n for n, f in D.model_fields.items() if f.annotation in (int, float)], sorted(D.model_fields)"`

## Where it lives

| Aspect | File | Symbol |
|---|---|---|
| The declared interface | `discharge/__init__.py` | the module's `__all__` |
| Kind registry (VERSIONED) | `discharge/policy.py` | `DischargeKindDeclaration`, `DISCHARGE_KIND_DECLARATIONS`, `KINDS` |
| Policy presets (VERSIONED) | `discharge/policy.py` | `DischargePolicyV1`, `DISCHARGE_POLICY_PRESETS`, `resolve_policy` |
| Reading the record | `discharge/channel.py` | `open_criticisms`, `discharged_handles` |
| The render | `discharge/channel.py` | `render_open_criticism_context` |
| The pack section | `llm/packs.py` | `open-criticisms`, priority 2 |
| The submission screen | `discharge/submission.py` | `screen_submission`, `record_discharges` |
| The wire shape | `llm/contracts.py`, `workloads/text.py` | `DischargeWireV1`, `discharge_kind_enum`, the two `discharges` fields |
| The two call sites | `rules/conj.py` | render threading; the screen before `candidate_rows` |
| Which preset is in force (FREE) | `config.py` | `Config.DISCHARGE_POLICY` |

## What makes a criticism OPEN

BOTH channels, because the population W2 measured as unrouted is the
`observe_only` one, and reading only attack edges would leave the motivating
defect in place: an `observe_only` criticism mints no warrant, so it produces
no `state.att` edge at all — only a critic-role artifact and a
`["scrutiny", target, critic]` Measure (`DR-CON-criticism-source`).

A criticism is open when it targets an artifact addressed to the problem
(`state.addr`) and is neither discharged nor itself REFUTED. A defeated
attacker is an attack that was MADE AND LOST, not an open indictment — the same
rule `DR-SEAM-calculus-x-rules`'s crisis slice already applies.

`check: python -m pytest tests/test_discharge_channel.py -q -k "observe_only_criticism_is_open or a_refuted_critic_is_not_open"`

## The handle

The handle IS the critic artifact id. Stable by content-addressing, unique by
construction, re-derivable on replay, and needing no handle map — which keeps
the recorded key-sort trap (handle maps reload `B1, B10, B2`; compare by index,
never by `.values()` — CLAUDE.md) out of this channel entirely. A short ordinal
was rejected because it renumbers when a lower-sorting criticism arrives, which
is the one thing a handle may not do.

`check: python -m pytest tests/test_discharge_channel.py::test_a_handle_is_the_critic_artifact_id_and_does_not_renumber -q`

## Why the section is non-droppable AND non-compressible

Both were learned by measurement on the frame slice, and the same two failures
are available here. A DROPPABLE section leaves no header and no placeholder
when the budget cuts it, so a problem whose criticisms were cut is
byte-indistinguishable from a problem with none. A COMPRESSIBLE one fails more
quietly still: Rung 6's first version carried the wounds and the digest in one
compressible section, and at a tight budget `_bounded_view` cut the STANDING
ATTACKERS block out of a pack that still showed a frame
(`DR-CON-packs-and-token-economy`).

Exact is affordable only because the section is bounded BY CONSTRUCTION —
`policy.handles_n` handles, `claim_head_chars` and `span_head_chars` each — and
where it will not fit, the allocator reports `mandatory_overflow` rather than
cutting quietly.

`check: python -m pytest tests/test_discharge_channel.py::test_the_open_criticism_section_is_bounded_by_construction -q`

## Persistence

A handle renders every cycle until it is discharged, and this needs no
mechanism of its own: `open_criticisms` re-derives from the record on every
render. What makes the claim worth anything is WHERE it is asserted — at the
TERMINAL cycle, under a budget already dropping optional sections, never at
injection. A renderer that quietly stopped carrying a criticism would look
identical at cycle 1 to one that carries it forever.

`check: python -m pytest tests/test_discharge_channel.py::test_a_criticism_at_cycle_k_still_renders_at_the_terminal_cycle -q`

## The submission boundary

A submission with undischarged handles is returned ONCE with the open list and
then ACCEPTED with a typed disclosure. **There is no verdict that refuses.**
`SubmissionScreening.verdict` is `"reask"` or `"accept"`, and that vocabulary
IS the promise — disclose, never die, the all-configurations law at the
boundary it names.
`check: python -c 'import inspect, re; from deepreason.discharge import screen_submission as s; src = inspect.getsource(inspect.getmodule(s)); v = set(re.findall(r"verdict=.([a-z]+).", src)); assert v == {"reask", "accept"}, v'`
`check: python -m pytest tests/test_discharge_submission.py::test_no_candidate_is_ever_refused tests/test_discharge_submission.py::test_the_second_submission_is_accepted_with_a_disclosure -q`

**The re-ask is not a repair grant**, and the distinction is not pedantry.
Repair exists to fix a reply the SCHEMA rejected; a re-asked submission is
schema-valid and the objection is epistemic. Treating them alike would spend a
budget meant for transport faults on an epistemic one, and would let a repair
ceiling silently cap how often criticism can be pressed. The re-ask re-enters
`conj()` on the same recursion shape `_context_expansion_index` uses, so no new
provider call site exists.
`check: test "$(cat src/deepreason/rules/conj.py src/deepreason/rules/crit.py | grep -c 'adapter\.call(')" -eq 8`

**A discharge counts only when it names a listed handle AND carries the content
its kind declares.** One definition of that rule serves both the screen and the
recorder; two copies would be two chances for what a run discloses and what it
records to disagree.
`check: python -c 'import inspect; from deepreason.discharge import screen_submission as s; src = inspect.getsource(inspect.getmodule(s)); assert src.count("def _answers(") == 1 and src.count("_answers(") >= 3, src.count("_answers(")'`

## What a REBUTTED discharge does to the graph

It registers the rebuttal as an ORDINARY artifact carrying two MENTION refs —
the criticism and the candidate — and no warrant. That is R6 in full: nothing
protects it, so a critic attacks it exactly as they would attack anything else.

The label-safety is structural rather than promised: `build_att` lifts attackers
through EVIDENCE refs, never through mentions, so there is no edge along which a
discharge could reach a pre-existing label. `file_departure_declaration` earned
the same guarantee the same way, and declines the same temptation this does — no
check runs on whether the rebuttal is EARNED, because refusing one would make
the authoring path a judge of the criticism it answers.
`check: python -m pytest tests/test_discharge_submission.py::test_a_rebuttal_carries_only_mention_refs tests/test_discharge_submission.py::test_a_rebuttal_is_itself_attackable tests/test_discharge_submission.py::test_a_rebuttal_moves_no_existing_label -q`

## The wire field, and why it is pruned rather than merely unused

`DischargeWireV1` lives in `llm/contracts.py`, not `llm/wire.py`: `wire.py`
imports `ReasoningCandidateProposal` from `workloads/text.py`, and that model
carries the field, so defining it in `wire.py` would close an import cycle.

With the channel off the field is PRUNED from the emitted schema — the property,
the constraints that still name it, and the `$def` — so a channel-off schema is
byte-indistinguishable from one built before the field existed. That is a
REQUIREMENT rather than an optimisation: `CompactConjectureCandidate` is embedded
by contracts this channel has no business changing, and committed tests read its
`$def` properties directly.
`check: python -m pytest tests/test_discharge_wire.py -q`

## The F2 composition note

Recorded at the operator's instruction (REQUEST.md Amendment 2, R18) so F2's
window or a successor finds it without having to reconstruct the reasoning.

> `DischargeWireV1.handle` is a REFERENCE-BEARING field. Its legal set is not
> free text: it is exactly `deepreason.discharge.open_criticisms(harness,
> problem_id, policy)`, in that call's own order, capped at
> `policy.handles_n` — ONE authority, computed from the record, and already the
> single source the pack section renders from. F1 deliberately leaves `handle`
> as a plain `str` on the wire rather than inventing a private enum or menu, so
> that F2's menu renderer can key on this field by REGISTERING against that
> one-authority legal set, without F2 touching `discharge/` and without F1
> touching F2's renderer. If F2 lands first, F1's field registers into it; if
> F1 lands first, F2 finds a field already shaped for it. That is the
> modularity law doing the work it was stated to do — neither side had to learn
> about the other's subsystem.

The `str` annotation is the load-bearing part, so it is checked rather than
described: a private enum here would close the seam F2 needs.
`check: python -c 'from deepreason.llm.wire import DischargeWireV1; assert DischargeWireV1.model_fields["handle"].annotation is str'`
`check: python -m pytest tests/test_discharge_channel.py::test_a_handle_is_the_critic_artifact_id_and_does_not_renumber -q`

## Traps

- **Reading only `state.att` and calling it "the open criticisms."** That is
  the exact shape of the defect this channel exists to close: `observe_only` is
  the authority mode that cannot mint a warrant, so the population W2 measured
  as 0-of-196-unrouted has NO attack edge to find. Read the scrutiny Measures
  too, or the channel ships carrying only the criticism that was already acting.
- **Reaching for an acknowledgment field.** It is the obvious design and it is
  the measured-worse one (Q5: ACK-required LOWERED accuracy). If a future
  change wants "the writer confirms it read this", that is the thing not to
  build.
- **Making the section droppable "because budget".** See above; the failure is
  silent by construction, which is why the allocator's disclosure loop exists
  and why this section does not rely on it.
- **Letting a discharge count become a signal.** A rate over discharges looks
  like a natural Measure and would cross the law line the moment anything
  ranked on it. Allocation touches efficiency, never evidence
  (`DR-INV-signal-contract`); this channel touches generation, never evidence.
- **Reaching for a repair budget to fund the re-ask.** They are different
  failures with different remedies, and the re-ask must not be capped by a
  ceiling that exists for transport faults.
- **Adding a rate over discharges.** A `DischargeRate` is the obvious next
  Measure and is exactly what would cross the law line the moment anything
  ranked on it. The uncapped open-criticism count is deliberately private to
  the renderer for the same reason.
- **Reading the channel's own record as proof that it worked.** F1 proves
  DELIVERY — that the channel carries, and that the off-state cannot. Whether a
  live provider model RESPONDS is a separate question, parked as P2, and Q1's
  finding forbids assuming it: a pack's own claim to have honoured a standing
  instruction is the least reliable artifact in the trajectory.
