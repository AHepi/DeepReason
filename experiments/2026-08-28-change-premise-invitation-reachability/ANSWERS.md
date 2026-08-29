# The three answers (P11)

The brief asks three questions "explicitly, in this order". They are answered
here in that order, each on a measurement rather than a preference. SPEC.md
holds the same answers bound to acceptance checks; this file is the
free-standing argument, with the evidence pasted.

Every number below comes from the record: the four committed technique roots
read out of `origin/claude/spec-to-code-technique-k5209o` (never written), the
audit's own committed probes, and `probes/p11_ladder_counterfactual.py`, which
replays each root with the harness's own time-travel reader `Harness.at(root,
seq)` at every `argumentative_critic` dispatch.

---

## (1) THE LATCH

**The question.** `premises.py:638` closed a problem to further invitations the
moment one attribution stood. Should the gate reopen — on a new refutation, on a
new attribution being refuted, on nothing at all? Say why, and price the cost of
re-asking.

**The answer: it reopens, on a LADDER.**

> A problem stands an invitation when its refuted candidates number at least
> `PREMISE_INVITE_AFTER × (standing attributions + 1)`. The first invitation is
> bought by `after` refutations; every re-invitation is bought by another
> `after`. An attribution that is itself refuted stops standing, which lowers
> the rung rather than deleting it.

### Why not "nothing at all"

Because the record already tried it and lost. Per critic dispatch, over all four
committed roots:

| root | critic dispatches | shown the invitation | a problem stood one — shipped gate | — under the ladder |
|---|---|---|---|---|
| epoch 0 | 29 | 0 | 0 | 0 |
| epoch 1 | 15 | 0 | 0 | 0 |
| epoch 5 | 10 | 3 | 9 | 9 |
| epoch 6 | 44 | 2 | 2 | 10 |
| **total** | **98** | **5** | **11** | **19** |

Epochs 0 and 1 are untouched by this change: their gate never opened at all
(max 1 refuted candidate on any problem, against a threshold of 2). That is the
first thing the table settles — **the latch, not the threshold, is what this
change is about**, because the two roots a threshold change would have moved are
exactly the two the ladder leaves alone.

Epoch 6 is where the wound is. The seqs at which a problem stood an invitation:

    shipped gate:  141, 180
    ladder:        141, 180, 695, 700, 705, 747, 754, 801, 808, 813

An attribution was filed at seq 186. From seq 187 to the run's end at 989 the
shipped gate was shut. At **seq 779**, in surviving conjecture
`aadd39655456…`, that run established that its own question was malformed — 593
events after the only channel for saying so had closed. Under the ladder the
channel is open at seqs 695, 700, 705, 747 and 754, all before 779.

**The honest limit, stated here rather than discovered later.** The probe asks
"did SOME problem stand an invitation at this seq", not "would THIS dispatch's
pack have carried it": a pack also needs the dispatch's own target addressed to
that problem, and every critic dispatch in these roots is a batch
(`contract_id: batch-critic.v2`), so it also needs `_batch_premise_invitation`'s
unanimity rule to hold. So 10 is an upper bound on epoch-6 packs. The measured
shown/open ratio is the honest conversion — 2/2 on epoch 6 itself, 3/9 on epoch
5, 5/11 pooled — which puts the number of packs actually carrying the reopened
invitation before seq 779 between 2 and 5. Against the shipped gate's **zero**,
in every reading.

The probe prices FREQUENCY. It is not a prediction of a different run's outcome:
a re-invited critic that files a premise changes the graph downstream, and the
counterfactual holds the graph fixed. That is a limit of the instrument, not a
hedge on the finding — the finding is that the channel was shut, and it is shut
in the record whatever a re-run would have done.

### Why not "on a new attribution being refuted"

Because that is already the behaviour, and it is not enough.
`standing_attributions` (`premises.py:187`) counts only ACCEPTED attributions,
so attacking an attribution — "the problem never assumed that" — already
reopened the gate before this change. It requires someone to attack the
attribution, which is rarer than the refutations that actually accumulate: it
happened **zero times in 98 dispatches across four roots**. A reopen rule that
fires on nothing is a reopen rule in name only.

It is preserved, not replaced: `test_refuting_an_attribution_lowers_the_rung`
pins it, and it now composes with the ladder instead of being the only road.

### Why not "on any new refutation", unpriced

Because it is unbounded. Epoch 6's problem accumulated 6 refutations; a free
reopen would have re-invited on essentially every dispatch after seq 186 — 42 of
44 — at ~1 035 tokens of pack each, ~43 000 tokens. The brief asks for the cost
of re-asking to be priced, and "as often as anything is refuted" is not a price.

The ladder is the same rule with a price attached: the number of invitations one
problem can ever stand is `floor(refuted / PREMISE_INVITE_AFTER)`, bought by
refutations the run had to produce anyway.

### The price of re-asking, measured from the prompt bytes

Not estimated — read from the blobs the calls were actually made on:

    invitation paragraph            589 chars
    CITABLE EVIDENCE BLOCKS legend  3 550 chars (epoch 6) / 4 157 (epoch 5)
    an invited critic prompt        11 805 chars
    a median uninvited one          3 498 chars

So **~4 139 characters ≈ ~1 035 tokens per invited dispatch**. Epoch 6's eight
extra open dispatches cost at most ~33 100 characters ≈ **~8 300 tokens, ~1.1 %
of that run's 772 482**.

Two things bound it further, and both are structural rather than hopeful:

- The ladder itself caps invitations at `floor(refuted / after)` per problem.
- Both sections are already members of `packs.DISCLOSED_ON_DROP`:

      $ python -c "from deepreason.llm.packs import DISCLOSED_ON_DROP; print(sorted(DISCLOSED_ON_DROP))"
      ['citable-evidence-blocks', 'frozen-evidence-context', 'premise-invitation', 'standing-attacks']

  so under budget pressure the pack allocator drops them and SAYS SO, rather
  than displacing the critic's actual target material in silence.

### What the change does NOT do

`PREMISE_INVITE_AFTER` is untouched at 2. The brief forbade lowering it as the
whole fix and was right to: a threshold change without a reopen rule still
yields one invitation per problem per run, which is the case the record shows is
not enough. With zero standing attributions the ladder is byte-for-byte the rule
it replaces, so no run that never files a premise sees any difference at all —
pinned by `test_the_ladder_is_the_shipped_rule_when_no_attribution_stands`.

---

## (2) THE EMPTY-REFS SILENCE

**The question.** `crit.py:1368` returns `()` without a Measure when
`premise_evidence` is empty, so the record cannot distinguish "invited and
declined" from "never invited". The brief says this "is probably worth doing
even if nothing else here is" and asks for agreement or refutation.

**The answer: AGREED — and the silence is wider than the brief states.**

`_check_premise_citations` is not merely silent on empty refs; on the commonest
case it is **never reached**. `_file_attribution` returned on an empty premise
text BEFORE resolving the invitation, so a seat that filed no premise at all
never got as far as the citation checker. That makes four cases, not two, and
all four recorded zero:

| case | across the four roots | distinguishable before |
|---|---|---|
| never invited | 93 of 98 dispatches | no |
| invited, no premise text at all | 4 of 5 | no |
| invited, premise filed, nothing cited | 1 of 5 (epoch 6 seq 180) | no |
| invited, premise filed, citations submitted | 0 of 5 | n/a |

Source: `experiments/2026-08-28-audit-run-problems/probes/q1_invited_replies.json`
and `probes/q1_citation_census.py` (critic-side verified citations 0/0/0/0).

So the brief's "this is cheap and probably worth doing even alone" is endorsed
and strengthened: without it, the audit's own headline number — 5 invited of 98
— had to be reconstructed from PROMPT BYTES, because the event record could not
answer it. A record that cannot say whether its own channel was offered is not
doing the job the record exists to do.

**The fix.** The invitation is resolved first, and every invited dispatch
records exactly one typed disposition at the single choke point both critic
paths already pass through (`_file_attribution`, called from
`crit_argumentative` and from the batch path, both before the attack branch):

    ["premise-answer:DECLINED", problem_id, target_id]   # no premise text
    ["premise-answer:UNCITED",  problem_id, target_id]   # a premise, no refs
    ["premise-answer:CITED",    problem_id, target_id]   # a premise with refs

An uninvited dispatch still records **nothing**, deliberately. Silence now means
NEVER ASKED and only that; a receipt on the uninvited path would destroy the
exact difference the receipt exists to record. That is pinned by
`test_an_uninvited_dispatch_records_no_disposition`, which was GREEN before the
change and stays green after — the guard that the fix did not overshoot.

**Why a new namespace and not `premise-citation:`.** `premise-citation:` is
what `milestone_census.py:185` counts as M2. Adding disposition rows to it would
change what M2 means, and the brief's own guardrail (and the operator's standing
law) is that this channel may change how criticism is generated and checked,
never what counts as evidence. `premise-answer:` is a separate family, declared
through the signal contract (`DR-REC-add-signal`) with a real unit, a real
staleness bound, and semantics that say what it is NOT evidence of. `CITED` says
an array was submitted, never that it verified; the byte-check's own verdict
stays where it was.

**Why it is not a penalty.** The problem layer's C5/H1 invariant is that
declining an invitation costs a critic nothing. The receipt is a Measure: it
mints no artifact, moves no status, enters no rank, and nothing in the tree
reads it. `test_a_declined_invitation_moves_no_status` asserts that rather than
asserting it in prose.

---

## (3) THE UNINVITED SCHEMA FIELD

**The question.** On 93 of 98 dispatches `premise_evidence` sits in the wire
contract with no legend and no legal value. Should the field be ABSENT from the
contract when the invitation is absent?

**The answer: NO. It stays present, unconditionally. No code changes.**

### Reason 1 — there is no measured harm to fix

The audit's own reading: the field is nullable, so "they nulled it instead,
which is the good outcome" — 98 nulls in 98 dispatches, zero fabrications.
`RUN_ANATOMY_SYNTHESIS` §2.5's 255-of-257 fabrication finding is about REQUIRED
fields a model cannot satisfy. This field is neither required nor, when the
invitation stands, unsatisfiable. Removing it would be a change with a cost and
no defect behind it.

### Reason 2 — doing it honestly moves a qualification subject digest

This is the load-bearing reason, and it was read rather than assumed:

    src/deepreason/llm/wire.py:2635        "argumentative_critic.compact.v1"   <- a hardcoded id,
                                                                                 not derived from the schema
    src/deepreason/cli/doctor.py:61        contract_id: Literal[...]            <- a CLOSED enum
    src/deepreason/cli/doctor.py:337-347   production_contract_pairs -> ProductionContractPairV1(contract_id=...)
    src/deepreason/qualification.py:267    pairs = (... for pair in production_contract_pairs(manifest))
    src/deepreason/qualification.py:281    "pair_inventory": pairs
    src/deepreason/qualification.py:285    qualification_subject_digest = sha256(canonical_json(subject_payload))

A conditional schema under the existing id would ship TWO shapes under ONE
`contract_id`, so a stored contract id — which every call in every record
carries — would stop determining the schema the call was made on. That is a
record that lies about itself, which is a worse outcome than a tidier prompt.

Doing it without that lie means a second contract id, which must be added to the
closed Literal, which flows into `pair_inventory`, which is hashed into
`qualification_subject_digest`. That is CLAUDE.md's frozen surface "Anything
altering qualification subject digests", and a ~14-minute / ~1 160-call
qualification battery per home and profile. The dispatch's frozen-surface rule
(C3) makes that a STOP, not a design choice available in this window.

The map said the same thing when the channel was built, which is corroboration
rather than coincidence — `docs/map/CON-problem-layer-lifecycle.md`: "no new
role, no new `contract_id`, so no qualification subject digest moves."

### Reason 3 — it treats the symptom of the thing answer (1) fixes

The 93 uninvited dispatches are uninvited because the gate was shut. Answer (1)
opens it. Removing a field to make a closed channel tidier is work on the wrong
end of the problem.

### Reason 4 — a schema that varies with graph state is a behaviour path that varies without configuration

The operator's 2026-08-28 law: "behaviour path should be deterministic, yet also
configurable." Configuration is the sanctioned axis of variation. A wire
contract whose shape depends on how many candidates happen to have been refuted
is neither deterministic-looking to a reader nor configurable by the operator.

### What this answer costs, stated plainly

The uninvited seat keeps seeing a field it cannot fill. That is ~30 characters
of schema on 93 of 98 dispatches, and the measured behavioural consequence of it
so far is: null, 98 times out of 98. If a future run ever shows fabrication in
that field, this answer should be revisited — and the disposition receipt from
answer (2) is exactly what would make that visible, because a fabricated
citation on an uninvited dispatch would now be a `premise-answer:` gap rather
than another silence.

Verified by leaving it alone:

    $ git diff --stat origin/main -- src/deepreason/llm/contracts.py src/deepreason/llm/wire.py
    (empty)

---

## R7 — when M2 can be re-measured live

Any live re-measurement of M2 waits until BOTH this tranche and P10 are merged.
P10 established that a manifest-launched run executed with five configuration
switches at their OFF defaults, `ENGAGED_CRITICISM_AUTHORITY` and
`LEGACY_CRITICISM_ENABLED` among them — so until it lands, a live M2 number
would be taken on a criticism authority the configuration did not name, and
could not be attributed to this change. The offline counterfactual above is this
tranche's proof, and it is a proof about frequency, not about what a future run
will conclude.

## R8 — what was NOT done

The planted-presupposition probe (the audit's residue item 2 — the same replay
with a deliberately malformed presupposition planted in the problem text, where
a correct seat MUST fill `premise`) is NOT authorized in this window and was not
started. It is parked with a ready-to-send prompt in `PARKED.md`.

Consistent with C2, nothing here is designed against a claim that the seat "will
not cite": the live probe cannot separate declining the channel from seeing no
malformed presupposition, and `PREREG_LITE.md` said so before it ran.
