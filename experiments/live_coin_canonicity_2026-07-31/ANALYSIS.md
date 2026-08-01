# Log trace: criticism without refutation, and the simulate exposures

Both analyses read `run-c5f901f38208e862f4ce2fe60a26e551` only. Claims
here are traceable to log seqs, typed objects, or prompt blobs.

## Part 1 — there are no refuted artifacts

Typed status over all 29 artifacts: `Counter({'Status.ACCEPTED': 29})`.
`verify_root` stats: `accepted: 29, refuted: 0`. There is not a single
`Rule.REFUTE` event in the 364-event log. What exists is 9 `scrutiny`
MEASURE records (seqs 93, 95, 106, 108, 119, 220, 222, 224, 244), each
pairing a target artifact with a criticism artifact, plus 10 criticism
assignments, 10 attempts (all `outcome: completed`), and 15
coverage-debt records all reading `termination_reason: coverage_complete`.

So criticism ran to completion, was recorded, and changed nothing.

### The nine criticisms and their grounds

    seq 93  -> 4210e2c6  bound c_{n-1}+c_n
      "the standard Kozen-Zaks bound is c_1 + c_2 (largest plus
       second-largest coin), not the sum of the two smallest ... would
       miss counterexamples above this too-small bound"
    seq 95  -> c6824f04  bound c_1+c_2 (the CORRECT one)
      criticised not for the bound but for hedging requirement 3:
      "expressed uncertainty about a known result is a substantive
       failure to meet requirement 3"
    seq 106 -> 5731f737  O(n^3) claim
      "Building a DP table ... requires time proportional to that
       magnitude ... directly contradicting the target's own claim of a
       bound polynomial in n alone"
    seq 108 -> ceeb35d2  Pearson attribution
      "vaguely says it examines 'structural differences' ... without
       specifying which combinations, how candidate witnesses are
       generated ... No proof is given"
    seq 119 -> 86dd1519  Pearson O(n^3)
      "never proves the bounded-set theorem required by Requirement 2
       ... Its own countercondition lists exactly the failure mode"
    seq 220 -> 00f8ee2c  bound c_3+c_{n-1}
      "asserts the finite bound ... but provides no proof ... states the
       bound as a bare claim with zero derivation"
    seq 222 -> 3cfb0351  bound c_3+c_2
      "conflates Pearson's algorithm ... with the Kozen-Zaks finite
       bound, producing an incoherent mechanism"
    seq 224 -> 7d65ec73  range [c_2+1, c_1+c_2-1]
      "search range begins at c_2+1, which systematically misses
       counterexamples smaller than c_2 ... C=(100,10,4,3,1) ... the
       smallest counterexample is w=6"
    seq 244 -> 312fecd1  bound c_{n-1}+c_n
      "For C=(6,5,1) ... the smallest counterexample is w=10: greedy
       gives 6+1+1+1+1 = 5 coins while optimal is 5+5 = 2"

Two of these are machine-checkable, and both check out against
`oracle.py`:

  - seq 224's `(100, 10, 4, 3, 1)` -> smallest counterexample 6, greedy
    3, optimal 2, and the proposed range `[11, 109]` never looks at 6.
    CONFIRMED exactly as stated.
  - seq 244's `(6, 5, 1)` -> smallest counterexample 10, greedy 5,
    optimal 2. CONFIRMED, and the critic's `5` corrects the conjecturer's
    own prose, which had said 6.

The critic seat also identified the correct bound (`c_1 + c_2`, seq 93),
which survives all 10,212 enumerated non-canonical systems.

### Thesis: the run could criticise but was structurally unable to refute

The record shows the criticism side working and the adjudication side
absent, and the absence is typed rather than inferred.

**One.** Criticism is entered as a MEASURE signal (`scrutiny`), not as a
status verdict. Nine were entered. None carries a disposition.

**Two.** The phase that would convert scrutiny into a status change never
ran. Log seqs 261-274 are fourteen consecutive
`v6-model-phase-deferred.v1` events, one per survivor, every one reading:

    ['v6-model-phase-deferred.v1', 'hv-spot-check', 'variator',
     '<artifact id>', '-', 'transaction-contract-unavailable']

**Three.** That unavailability is not a runtime accident; it is fixed at
qualification. In the run manifest's route-seat model classifications,
`variator`, `judge`, `defender`, `grounding_reviewer`,
`property_designer`, and `vision_critic` all carry
`selected_class: inactive_no_authorized_contract` with
`authorized_contract_ids: []`. Only `argumentative_critic`,
`conjecturer`, `summarizer`, `synthesizer`, and `thesis` were qualified
with contracts. The seats that criticise were live; every seat that could
adjudicate a criticism was dark before the first cycle.

**Four.** The consequence is visible in the survivors. Fourteen artifacts
survive, and they assert mutually contradictory bounds — `c_1+c_2`,
`c_3+c_{n-1}`, `c_2+c_3`, `c_{n-1}+c_n` — with the record marking every
one ACCEPTED, including the one whose refutation by explicit
counterexample sits in the same log four seqs later. Under the harness's
own evidentiary rule, "accepted" here means only "not adjudicated", and
this run is a clean demonstration that the two are different things.

**Five.** Budget then closed the run before any of it could be revisited:
`stop_reason: budget_exhausted`, 180,416 of 200,000 tokens, criticism
debt 0 (every assignment satisfied), frontier still 14 wide.

The Popperian claim the harness makes is that the typed record, not
model prose, decides what a run established. This run satisfies that
claim on the input side — the criticism is typed, complete, and in two
cases exactly right — and cannot satisfy it on the output side, because
no live seat had authority to turn a correct criticism into a refutation.
Criticism was epistemically decisive and procedurally inert.

Parked as **D4**: a run can qualify with every adjudicating seat
`inactive_no_authorized_contract` and still report `accepted` for
artifacts that its own recorded criticism refutes. Whether the fix is a
launch-time refusal, a typed warning in the run status, or a status other
than ACCEPTED for a scrutinised-but-unadjudicated artifact, is a design
question this run does not settle. Its evidence is `accepted: 29,
refuted: 0` beside nine criticisms, two of which are confirmed correct by
independent enumeration.

## Part 2 — how often the model could actually propose a simulation

26 provider calls. For each, the prompt was resolved from
`workflow-provider-attempt-v1.prompt_sha256` to its blob and searched.

    contract                        calls  simulation_proposals present
    conjecturer.turn.v6                 7   6
    conjecturer.atomic-candidate.v1    12   0
    batch-critic.v2                     6   0
    config-referee.v1                   1   0

**Six calls of twenty-six carried the channel, across three distinct
prompts:**

  - `4c599529`, 24,753 chars — the full conjecture turn. Question,
    requirements, CRITERIA, the admitted dossier blocks (with citable
    block ids, inside UNTRUSTED SOURCE DATA delimiters), and the whole v6
    JSON schema beginning at char 510. `SimulationProposalWireV1` at char
    10,370; the D2b disclosure text at char 11,117.
  - `b6e5f440`, 24,591 chars — the second conjecture turn, same shape.
  - `f35a7506`, 6,832 chars, used 4 times — a `repair.patch.v1` prompt.
    It carries the schema and therefore the channel and the D2b text, but
    no question, no criteria and no dossier. Its instruction is "Return
    exactly one repair.patch.v1 JSON object ... repair only one now".

So the model was invited to REASON with the simulation channel available
exactly **twice**. The other four channel-bearing calls asked it to patch
one field of a JSON document it had already produced.

**What was alongside, in the two real turns:** the question (which
explicitly demands a typed sandboxed simulation), the requirement list,
the run's criteria, both dossier sources as citable admitted blocks —
including CAPABILITY_CONTRACT.md's prose describing the simulate contract
in words — and the complete wire schema. Both the prose description and
the schema description of the same contract were present together.

**What happened to those six calls:** every one failed the contract.

    prompt     p_tok  c_tok   terminal
    4c599529    6788  24576   rejected / conjecture_repair_requested
    b6e5f440    6750   4691   rejected / conjecture_repair_requested
    f35a7506    1968   4849   rejected / conjecture_repair_step_rejected
    f35a7506    1968  10716   rejected / conjecture_repair_step_rejected
    f35a7506    1968   4314   rejected / conjecture_repair_step_rejected
    f35a7506    1968   5923   schema_exhausted / conjecture_schema_exhausted
    fd49e505     101    325   schema_exhausted / conjecture_repair_unrepairable

The first turn returned `completion_tokens: 24576` — exactly the
configured cap. That is the documented glm-5.2 reasoning-burn signature,
here on the one call that mattered most.

**The mirror image: 12 of 26 calls carried the question's instruction to
"file a typed sandboxed Python simulation" in a prompt with no
`simulation_proposals` field anywhere in it.** Those are the twelve
`conjecturer.atomic-candidate.v1` calls that produced every surviving
candidate. This is D3, quantified.

**Incidental, and the first live confirmation of D2b:** the disclosure
shipped in that tranche appears verbatim in a real production pack at
char 11,117 of prompt `4c599529`. It reached the model. The model never
reached a state in which it could act on it.
