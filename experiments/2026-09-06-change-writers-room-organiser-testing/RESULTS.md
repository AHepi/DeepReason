# RESULTS — the organiser seat: testing the writer's room on the full harness

Honest-ledger segments, dated. Nothing here claims more than the record
shows. "Accepted does not mean true."

## 2026-09-06 — moves 1 and 2 delivered offline; the measure sealed; no arm run (no credential)

**What this tranche proves, and what it does not.** The writer's room's
record (12 conjectures, 36 objections, 46 commitment proposals; 53 493
characters) now reaches a full-harness conjecturer seat WHOLE, through the
attached-evidence road, under a registered pairing that asks the seat to
organise rather than invent; the seat's candidates admit through the
ordinary path, their refutation conditions become the commitments they
carry, and an invented or unshown citation is caught by the record as a
typed measure. All of that is proven offline against the stub — twelve
assertions in `tests/test_organiser_seat.py`, the rendered brief in
`proof/ORGANISER_BRIEF.txt`, the dry attach in `proof/DRY_ATTACH.txt`. What
is NOT shown: whether any of it makes the composed answer materially better.
No live arm ran. This container holds no credential (`experiments/*/env`
absent, `OLLAMA_API_KEY` unset — SPEC M10), so the measure is delivered
SEALED and NOT RUN (R23): PREREG.md, the three arms' scripts, the composer,
the judge and the analyser are committed, and `runs/chain.sh` is the one
command that runs the whole plan once `env` exists.

### 1. The room as an attachment (R3–R5)

| | |
|---|---|
| converter | `tools/room_to_attachment.py`; `records 94 (12 conjectures, 46 proposals, 36 objections)`, `verbatim 94/94`, `chars 53493` |
| files | `attachment/01-conjectures.txt` 9 281 bytes · `02-proposals.txt` 17 566 · `03-objections.txt` 33 377; digests in `attachment/ATTACHMENT.sha256` |
| admission (the function `reason --attach` calls) | `sources 3 blocks 94 refusals 0`, dossier digest `2a49cd52…` (`proof/DRY_ATTACH.txt`) |
| one call sees | all 3 sources whole (frozen-evidence section 63 538 bytes, nothing excluded); legend 32 of 94 blocks (6 113 bytes); 62 withheld from the legend only |

Two things the record corrected on the way. `--attach <directory>` admits
every file under it: the directory form admitted 5 sources and 105 blocks
(the conversion manifest and the digest file too), so the arm script names
the three files. And the citable legend's 32 are NOT the first 32 in file
order: admission sorts a dossier's blocks by content id, so they are a
hash-ordered sample — 7 conjectures, 13 proposals (1 refuted-if), 12
objections (SPEC Amendment 1). The seat READS every body and can CITE a
third of them; the rest are the typed `EVIDENCE_REF_NOT_EXPOSED` measure if
cited. Parked as P2 with the cap.

### 2. What the form excludes on this record (R10)

Nothing. Every one of the 12 room conjectures has a refuted-if proposal
about it — 12 of 12 (`attachment/CONVERSION.json`; the SPEC S10 check prints
`12 12`) — so the form's requirements of a mechanism and at least one
countercondition per candidate exclude no room conjecture. The 46 proposals
are 12 refuted-if, 12 forbids, 12 must-not, 10 predicts.

### 3. The organiser seat (R7–R9, R11–R14)

Registered in `src/deepreason/llm/seat_layouts.py` (the layout
`seat-pack.conjecturer.organiser-v1` and the shell
`seat.conjecturer.organiser-v1`; beside them `seat-pack.critic.evidence-blind-v1`
/ `seat.critic.evidence-blind-v1`), `llm/seat_plugins.py` (the directive
`dr.output-contract.organiser`) and `llm/role_prompts.py` (the wording
`role-prompt.organiser-v1`) — said so, because the managed path never opens
`<DEEPREASON_HOME>/seat_plugins/` (one call site, mini's; PARKED P1). The
form is `conjecturer.turn.v6`, the form the managed conjecturer fills; the
brief named `reasoning.conjecturer.compact.v2`, which does not reach that
path and compiles to the same proposal (SPEC A1).

The rendered brief (`proof/ORGANISER_BRIEF.txt`, 91 795 bytes, under
`PACK_TOKEN_BUDGET 24000`): the organiser wording; problem; criteria; the
three room sources whole; the legend; the directive — ORGANISE, DO NOT
INVENT; one candidate per room conjecture worth carrying, at most 6 this
turn; claim and mechanism from the conjecture's block sharpened by its
objections; every countercondition from its proposals (refuted-if as
written; forbids/must-not → refuted if; predicts → refuted if not);
`evidence_refs` only from the legend; a conjecture with no proposal named in
`uncertainties`; typicality 0.5; nothing not in the blocks. Nothing
compressed, nothing dropped (`proof/ORGANISER_RECEIPTS.json`).

The stub (`tests/test_organiser_seat.py`, 12 passed): two organiser
candidates admit through the ordinary path as ACCEPTED conjecturer
artifacts; each carries `reason-counter@…` commitments, one per
countercondition, `program:reasoning_observation_pending`; the first's two
citations verify; the second's citation of a block the legend withheld is
one `EVIDENCE_REF_NOT_EXPOSED` measure and its status does not move; an id
naming no block is `EVIDENCE_REF_UNKNOWN_BLOCK`; unbound, the seat renders
the legacy brief byte for byte; the blind critic layout is the legacy one
minus the two evidence entries; the wording moves the conjecturer alone;
the two defaults have not moved (both goldens green).

Decided and disclosed (R13): no configuration is cycle-scoped; the organiser
runs the whole run and its directive handles later turns; PARKED P3. The
critic on ARM R is evidence-blind (R14); the switch that would show it the
room's bodies does not exist and is PARKED P4.

### 4. The measure, sealed (R15–R19)

`PREREG.md`, sealed by sha256 in its commit message: three arms on the D8
question; ARM 0 reused by digest; ARM H and ARM R matched (`--cycles 4
--token-budget 800000`, `runs/config.yaml`, one home and one battery each);
the judged unit is the run's composed result (`tools/compose_result.py`,
deterministic, no model — on a committed 4-cycle root: 43 surviving
positions, 53 423 characters); three blind judges under the copied criteria
(byte-identical to D8's); length reported for every unit and controlled by
the n = 1 rule (a BETTER whose unit is > 1.5× longer is NULL,
length-uncontrolled); ARM R MATERIALLY BETTER only if BETTER than BOTH ARM 0
and ARM H by ≥ 2 of 15; NULL and WORSE reported in those words.

### 5. Failure budget (R22)

Six live calls beyond the plan. **Spent: 0.** No live call of any kind was
made from this tranche.

| # | call | reason | cost | decided |
|---|---|---|---|---|
| — | — | — | — | — |

### 6. Residue

- **Not run.** ARM H and ARM R did not run; no verdict exists. The offline
  proofs show the road is open, not that it leads anywhere better.
- One question, one model, one room; n = 1 per harness unit by the design's
  own unit (PREREG §11).
- The seat cites a third of what it reads (P2); the soak covers the managed
  shape, not the shell (PREREG §10).
- The soak on the launch configuration's shape ran green here (`runs/soak.log`: `epoch3`, 8 cycles, `exit 0 (clean)`); it proves the box and the managed path, not the organiser shell (PREREG §10).
- The full gate and `docs_verify` on this tree: see VALIDATION.md.

## 2026-09-06, later — the test run: ARM R failed at cycle 3, the two bare arms tied at the rubric's ceiling, verdict INCONCLUSIVE

**The measure did not decide anything, and the run said why twice.** ARM R —
the full harness with the room attached and the organiser seat — ran three
cycles and then died a typed operational death in the CRITIC seat; under the
sealed rule that is a FAILED arm, its unit is not judged, and the verdict for
both pairs involving it is INCONCLUSIVE. The two bare arms were judged and
tied: every one of the eighteen judge readings scored 15 of 15, which is the
rubric ceiling PREREG §11 registered as a risk before launch. So the run
produced no verdict, and two findings worth more than the verdict would have
been: **a seam defect this tranche's own configuration created**, and
**a measuring instrument that cannot discriminate on this question**.

### 1. What ran (typed outcomes only)

| | |
|---|---|
| soak | `cycle_soak --case epoch3` → `exit 0 (clean)`, immediately before the launch (`runs/soak.log`) |
| battery | attached-evidence subject, `Qualification tier: full`, 08:56:30 → 09:02:42Z |
| ARM R | root `runs/home-r/runs/run-36d9a22c3e2045ae1b8c7bfb9d95d092`; `state: failed`, `stop_reason: operational_failure`, cycle 3, `token_spend 464359` of `token_limit 500000`; `verify_root` **0 violations**; `valid: true`, `integrity_valid: true`, `epistemic_checks_passed: true`, `operational_checks_passed: false` |
| ARM 0R | three calls, all `finish_reason: stop`, 47 345 tokens, 5 875 / 7 334 / 6 879 characters; prompt 14 375 tokens each (`runs/arm0R/`) |
| ARM 0 | the three D8 calls, reused by digest, not respent |
| ARM H | deferred (PREREG Amendment 3) |

The organiser rendered on every conjecturer call: the section plans name
`dr.output-contract.organiser` and never `dr.output-contract.conjecturer`,
with `dr.evidence.frozen` and `dr.evidence.citable` rendered, not compressed
and not dropped. The arm is valid on that test; it failed for another reason.

**The dossier digest pin.** The launch admitted 3 sources, 94 evidence-tier
paragraph blocks, 0 refusals — the dry attach's content exactly — under
digest `d2120e7d…`, not the `2a49cd52…` §0 pinned. The pin was wrong, not the
arm: the dossier digest binds provenance, problem reference and locators, and
no offline computation could have matched it (PREREG Amendment 5, with the
measurement). What proved the bytes is `armR.sh`'s own check, which passed on
all four files before any call.

### 2. Why ARM R died, from the record

`V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY … route seat has terminally exhausted
its smallest authorized contract`. `deepreason stop-report` ruled out
CONFIGURATION and ENVIRONMENT (no 429, no transport fault, no carriage
notice) and supported MODEL, noting that the critic had passed qualification
20 of 20 first-pass on both its forms with zero repairs. The record says what
the model actually did:

- the rejected pointers are `/cases/0/premise_evidence/0/block` and
  `/cases/0/premise_evidence/1/block` (`workflow-semantic-admission-v1`, the
  repair protocol's `authorized_pointers`);
- the critic's raw replies cite `a0b919ae506615d2` — **a room conjecture's own
  record id**, which appears in the header lines of the room text and inside
  the organiser's candidates — and two 12-hex strings of block shape. None is
  an admission block id; the dossier holds 94 and none of these.

**The cause is this tranche's own configuration, not the harness.** The
evidence-blind critic shell (`seat.critic.evidence-blind-v1`, built for R14 so
the critic's attacks would be its own) removes `dr.evidence.citable` and
`dr.premise-invitation` from the critic's BRIEF. It cannot remove the
`premise_evidence` field from the critic's FORM, and `rules/crit.py` binds the
citable block menu into the contract from its own legend, independently of the
layout (`crit.py` line 358, `citable_block_ids=tuple(block.id for block in
citable_blocks)`, fed from `batch_legend.shown`). So the critic was asked for
block ids by a schema while the brief showed it none, filled the field with the
only ids it could see, was rejected, was authorized to repair exactly those
pointers, failed, decomposed to the atomic contract, and exhausted it. A brief
and a form that disagree about evidence is the defect; the harness enforced the
form exactly as documented. Parked as P6 with three priced roads.

### 3. What the organiser did with the room

From the record (`runs/armR/CENSUS.json`), before the critic seat died:

| | |
|---|---|
| room conjectures carried | **7 of 12**, by verified citation (`055185d5 20b35eec 76f24493 92968bc0 a0b919ae d8dfb83a e0959a2b`) |
| positions on the seed question | 16 accepted, 0 refuted (25 in all, 9 on derived sub-questions) |
| counterconditions registered as commitments | **54**, three or four per position, every one drawn from the room's proposals |
| citation checks | 21 `EVIDENCE_CITATION_VERIFIED`, 7 `EVIDENCE_QUOTE_MISMATCH`, 58 `EVIDENCE_REF_UNKNOWN_BLOCK` |
| seed positions with at least one verified citation | 10 of 16 |

The composed unit is 21 396 characters and reads as the organiser was asked to
write: claim, mechanism, and refutation conditions in the room's own words (an
appendix below quotes it whole). **The 58 unknown-block citations are the same
defect as the critic's, on the other seat**: the brief puts TWO id systems in
front of one seat — the room's record ids inside the frozen text's headers,
and the admission block ids in the legend — and the model mixed them. It cited
legend ids 21 times and header ids 58 times. Nothing was invented from
nothing; the record caught every one, assigned no status to any of them, and
the run continued, which is the design working.

### 4. Spend, against the registered prediction

| seat | calls | tokens | share |
|---|---|---|---|
| conjecturer (organiser) | 22 | 392 916 | 85% |
| argumentative_critic | 42 | 71 443 | 15% |

Organiser calls on the seed problem cost 30 678 – 34 339 tokens each; on
derived problems 13 568 – 15 649; the atomic decompositions 4 248 – 6 503.
PREREG Amendment 1 predicted "**the 500 000 ceiling ends the run in CYCLE 3**".
The run did end in cycle 3, at 464 359 tokens — 93% of the ceiling — though by
a seat failure rather than by the ceiling itself. The prediction held on the
cycle and was not tested on the terminal.

### 5. The judging, and the ceiling

`ORGANISER_VERDICT_V1`, six units, three judges each, keymap opened only
after `blind/scores.json` existed:

    ARM0-single-call   units=3  score=15.0  worst judge=15  chars=7688  contested=0
    ARM0R-room-bare    units=3  score=15.0  worst judge=15  chars=6879  contested=0
    ARMH-harness       n=0  -- deferred (PREREG Amendment 3)
    ARMR-organiser     n=0  -- no usable unit
    VERDICT (PREREG §7 as amended): INCONCLUSIVE -- an arm has no usable unit (§7 floor)

**Eighteen readings, eighteen 15s.** `0R vs 0` — handing the bare model the
whole room — moved nothing the panel could see, because the panel had no room
to move in. PREREG §11 named this in advance: "If ARM 0 scores 15 again,
'R BETTER than 0' is unreachable by construction". It is now measured on both
bare arms rather than feared, so the next launch needs a harder rubric or a
harder question before it needs anything else. The pre-registered reading of
"R better than 0 but not better than 0R" was never reachable and is not
claimed.

### 6. Failure budget (R22)

Six live calls beyond the plan. **Spent: 0.** ARM R's failure consumed only
planned calls; no arm was relaunched, no probe was made.

| # | call | reason | cost | decided |
|---|---|---|---|---|
| — | — | — | — | — |

### 7. Residue — what this does NOT show

- **It does not show the organiser is worth anything.** No harness unit was
  judged. The measure is INCONCLUSIVE, and INCONCLUSIVE is not a null result
  about the harness; it is the absence of one.
- **It does not show the harness is broken.** The stop is a defect in this
  tranche's own critic configuration, and the harness enforced its own
  documented contract; `verify_root` reports 0 violations on the failed root.
- One question, one model, one room, one run. Same-model judging throughout.
- ARM H (the harness alone, no room) is deferred, so nothing here separates
  the harness from the room even in principle.
- The rubric is saturated at 15 of 15 on both bare arms, so this instrument
  cannot rank anything better than a single call on this question.
- The legend cap and its content-id order (P2) are unchanged, and the id
  duality this run exposed (P7) sits on top of them.

### Appendix — ARM R's composed unit, whole (not judged; a failed arm's record)

The unit `tools/compose_result.py` derived from ARM R's root at its stop. It
is quoted whole because the operator asked what the organiser did with the
room, and because a failed arm's content is still evidence about the seat
even when it is not evidence about the measure.

```
QUESTION: Popper held that corroboration is not probability: a theory that has survived severe tests is not thereby made more probable. Yet working scientists, and Popper himself when choosing which theory to act on, prefer the better-corroborated theory. Is that preference defensible on Popper's own terms, or does it smuggle back in the induction he rejected? Make the strongest case for each answer, then say which one survives and what accepting it costs.

SURVIVING POSITIONS (16):
1. The preference for better-corroborated theories is defensible without induction because it functions as a pragmatic wager: while past success guarantees nothing about the future, choosing the theory that has demonstrated 'fitness' by surviving severe tests is the only rational choice available if one must act.
   Mechanism: The mechanism distinguishes between epistemic probability (which Popper rejects as increased by corroboration) and pragmatic rationality. It argues that acting on the best-tested theory is akin to betting on a horse that has won every race; the agent does not believe the horse will win (no inductive leap), but recognizes it as the unique rational option given the constraint of necessary action.
   Refuted if:
   - refuted if it can be demonstrated that preferring the better-corroborated theory logically entails an assumption that the future will resemble the past, thereby making the 'pragmatic wager' indistinguishable from the inductive principle Popper explicitly rejects
   - refuted if the very act of selecting a theory based on past survival implicitly assumes that past performance is a reliable indicator of future utility
   - refuted if the analogy of betting on a horse fails because, unlike a horse race, scientific theories face an unknown reality where survival demonstrates no positive 'fitness'
   - refuted if the phrase 'educated guesswork' is a contradiction in terms within a strictly non-inductive framework, rendering the preference an arbitrary psychological habit

2. The preference is defensible by shifting the goal from 'probability' to 'verisimilitude' (truth-likeness): a highly corroborated theory is not more probable, but is a better candidate for being closer to the truth because it has withstood attempts to show it is false.
   Mechanism: The mechanism posits that science aims at truth rather than certainty. Therefore, selecting the theory with the highest empirical content that has not yet been refuted is the only methodological move consistent with increasing verisimilitude. This avoids induction by treating corroboration as a logical relation of content and truth rather than a statistical likelihood.
   Refuted if:
   - refuted if it can be shown that the concept of 'verisimilitude' cannot be formally defined without implicitly relying on inductive probability
   - refuted if Popper's own formal definition of verisimilitude was proven logically incoherent by Tichý and Miller, rendering the argument internally inconsistent
   - refuted if asserting that a theory which has survived severe tests is a 'better candidate' for being true presupposes the 'uniformity of nature'
   - refuted if reducing the justification to a 'regulative ideal' that cannot be logically proven concedes that the choice is ultimately irrational or arational

3. The preference is indefensible on Popper's own terms and constitutes a performative contradiction: by advising scientists to 'prefer' the better-corroborated theory for action, Popper implicitly asserts that past performance is a reliable guide to future reliability, which is the definition of inductive reasoning he sought to destroy.
   Mechanism: The mechanism argues that if corroboration reports only past history and implies nothing about the future, then preferring Theory A over Theory B for future application is irrational within Popper's system. Accepting this view costs the coherence of Popper's philosophy, reducing his methodology to a description of psychological habit rather than a logical framework.
   Refuted if:
   - refuted if a coherent account can be provided where preferring a better-corroborated theory is justified solely as a method to maximize the severity of future tests without any assumption that the theory will actually succeed
   - refuted if Popper explicitly distinguishes between the logical status of a theory and the pragmatic decision to act upon it, allowing preference without belief in future reliability
   - refuted if the claim that Popper's system reduces to 'psychological habit' ignores his argument for the superiority of severe testing as a deductive consequence of the goal to eliminate error
   - refuted if the conjecture commits a straw man fallacy by suggesting Popper advises preference based on 'past performance' as a guide to 'future reliability' rather than acknowledging the necessity of decision-making under uncertainty

4. The preference is defensible because corroboration functions as a measure of informational content rather than likelihood: we choose the better-corroborated theory not because we think it will hold true, but because it offers the most detailed map of the world currently available, providing the richest basis for further criticism.
   Mechanism: The mechanism redefines 'action' as purely experimental. We act on the bold theory specifically to try to break it, meaning our 'preference' is actually a preference for the most efficient path to potential falsification, not for successful prediction.
   Refuted if:
   - refuted if it can be demonstrated that the 'informational content' or 'boldness' of a theory cannot be assessed independently of its probability of being true
   - refuted if the assertion that 'action becomes purely experimental' fails to account for the stakes involved in real-world application where agents act on the expectation that the theory will hold
   - refuted if the target conflates 'informational content' with 'practical viability', as scientists prefer corroborated theories for accurate predictions, not merely to 'break them' faster
   - refuted if preferring a theory for its 'boldness' presupposes that past survival under severe tests is a reliable indicator of future utility

5. The preference is defensible on Popperian terms through the asymmetry of risk: rejecting a well-corroborated theory in favor of a poorly tested one increases the likelihood of immediate error without offering any compensatory increase in testability.
   Mechanism: The mechanism frames the preference as a logical deduction about the current state of knowledge rather than an inductive prediction. The better-corroborated theory is simply the one that has not yet been falsified despite greater exposure. Choosing it minimizes 'known unknowns' relative to alternatives, a defensive posture requiring no belief in future validity.
   Refuted if:
   - refuted if it could be demonstrated that the concept of 'minimizing known unknowns' logically entails a probabilistic assessment of future performance
   - refuted if claiming that choosing a poorly tested theory carries a higher 'likelihood of error' assigns a probabilistic weight to theories based on history, contradicting Popper's core thesis
   - refuted if the 'defensive posture' is illusory because action inherently aims at future results, and preferring theory A over theory B for action logically entails believing A is a better guide to those results
   - refuted if Popper explicitly denied that past survival implies future reliability, making any deduction that one *should* act on the well-corroborated theory an inductive leap

6. The tension dissolves if we strictly segregate corroboration as a purely historical report from the act of choosing a theory for action: the preference is defensible as a non-rational, psychological commitment necessary for life, distinct from scientific logic.
   Mechanism: The mechanism argues that while corroboration says nothing about the future, the act of preferring the best-tested theory is a biological or pragmatic imperative for survival. This admits that science alone cannot dictate action without an extra-logical leap, thus avoiding the charge of smuggling induction into the logic of science itself.
   Refuted if:
   - refuted if Popper explicitly argued in his published works that the preference for well-corroborated theories in practical action is a 'non-rational' or purely 'psychological' commitment, rather than a methodologically rational choice
   - refuted if the proposal to segregate corroboration as a 'purely historical report' ignores Popper's concept of corroboration as a measure of testability and explanatory power that provides a rational basis for expectation
   - refuted if the conjecture creates a false dichotomy between 'strict rationality' and 'pragmatic imperative', whereas Popper's philosophy integrates these via the logical asymmetry between verification and falsification
   - refuted if Popper explicitly argued that preferring the better-corroborated theory is a rational decision based on critical discussion and the aim of finding truth, not a blind biological impulse

7. The preference for better-corroborated theories is defensible on Popper's terms as a methodological rule to maximize the severity of future falsification, not as an inductive prediction of success.
   Mechanism: Choosing the theory that has withstood the severest tests provides the most informative target for error detection; if it is false, this choice reveals the error fastest, accelerating knowledge growth without assuming the theory will hold true.
   Refuted if:
   - refuted if it can be shown that Popper explicitly justified the preference for better-corroborated theories in practical, life-or-death decisions on the grounds of safety or reliability rather than solely on the grounds of maximizing testability and information content
   - refuted if the argument that we choose highly corroborated theories because they are the 'most informative target for future falsification' is internally inconsistent with scientific practice where robust theories are used as stable foundations
   - refuted if the assumption that a theory which has survived severe tests is the 'most likely to reveal its falsehood quickly' is circular because such a theory has demonstrated resilience

8. The preference for better-corroborated theories is indefensible on Popper's own terms and constitutes a performative contradiction that smuggles induction back in through the pragmatic necessity of action.
   Mechanism: Acting on a well-corroborated theory (e.g., building a bridge) implicitly relies on the premise that past survival indicates future stability, which is the definition of inductive reasoning; no semantic distinction between 'corroboration' and 'probability' can mask this inductive leap when leaving abstract methodology for real-world application.
   Refuted if:
   - refuted if a coherent account can be provided where preferring a better-corroborated theory is justified solely as a method to maximize the severity of future tests without any assumption that the theory will actually succeed
   - refuted if Popper explicitly distinguishes between 'preference for action' and 'belief in future reliability' allowing for rational choice without inductive inference
   - refuted if the charge of 'performative contradiction' fails because acting on a theory does not necessitate believing it is probable

9. The preference is defensible only by accepting a non-probabilistic metaphysical commitment to verisimilitude (truth-likeness), shifting the goal from predictive reliability to structural approximation.
   Mechanism: Severe testing logically increases a theory's content and proximity to truth; while we cannot know a theory is true, we can rationally prefer the one closer to truth based on test survival, provided we accept the metaphysical hope that nature rewards boldness with truth-likeness.
   Refuted if:
   - refuted if it can be demonstrated that the concept of 'verisimilitude' cannot be formally defined without implicitly relying on inductive probability
   - refuted if it can be demonstrated that Popper explicitly grounded the preference in a pragmatic decision rule without invoking any metaphysical assumption about proximity to truth
   - refuted if the claim that accepting verisimilitude costs the framework its claim to 'pure logic' mischaracterizes critical rationalism as requiring no non-logical commitments

10. The preference for better-corroborated theories is indefensible on Popper's own terms and constitutes a performative contradiction: acting on a well-corroborated theory (e.g., bridge design) relies on the implicit premise that past survival indicates future stability, which is the very definition of inductive reasoning Popper sought to destroy.
   Mechanism: Popper's system collapses into crypto-induction whenever it leaves abstract methodology; no semantic maneuvering around 'corroboration' vs. 'probability' can mask that acting on corroboration requires an inductive leap, reducing his methodology to a description of psychological habit rather than a logical framework.
   Refuted if:
   - refuted if a coherent account can be provided where preferring a better-corroborated theory is justified solely as a method to maximize the severity of future tests without any assumption that the theory will actually succeed or remain unfalsified in the future
   - refuted if Popper explicitly distinguished 'pragmatic preference for action' from 'assertion of future reliability' such that one can choose the best-tested map without assuming the territory will not change
   - refuted if it can be demonstrated that Popper explicitly justified the preference for better-corroborated theories in practical decisions solely on the grounds of maximizing testability and information content, without invoking any expectation of future success based on past performance

11. The preference for better-corroborated theories is defensible without induction because it is a pragmatic wager, not an epistemic probability claim: choosing the theory that has survived severe tests is the only rational choice available if we must act, as it has demonstrated a capacity to withstand falsification that others lack.
   Mechanism: Past success guarantees nothing about the future (rejecting induction), but the theory surviving severest tests proves its 'fitness' in the specific environment of reality so far; choosing it is akin to betting on the horse that has won every race—we do not know it will win the next, but it is the only rational bet.
   Refuted if:
   - refuted if it can be demonstrated that preferring the better-corroborated theory logically entails an assumption that the future will resemble the past, thereby making the 'pragmatic wager' indistinguishable from the inductive principle Popper explicitly rejects
   - refuted if the analogy of betting on a horse fails because scientific theories face an unknown reality where surviving tests demonstrates no positive 'fitness'
   - refuted if the phrase 'educated guesswork' is a contradiction in terms within a strictly non-inductive framework, rendering the preference an arbitrary psychological habit

12. The preference is defensible only by accepting a non-probabilistic metaphysical commitment to verisimilitude (truth-likeness), arguing that while we cannot know a theory is true, severe testing logically increases its content and proximity to truth.
   Mechanism: This stance survives Popper's anti-induction critique by shifting the goal from 'predictive reliability' to 'structural approximation,' positing that surviving severe tests correlates with truth-likeness.
   Refuted if:
   - refuted if it can be shown that the concept of 'verisimilitude' cannot be formally defined without implicitly relying on inductive probability
   - refuted if Popper's own formal definition of verisimilitude was proven logically incoherent by Tichý and Miller, rendering the argument internally inconsistent
   - refuted if it can be demonstrated that Popper explicitly grounded the preference in a pragmatic decision rule without invoking any metaphysical assumption about proximity to truth

13. The preference is defensible because corroboration functions as a measure of informational content rather than likelihood: we choose the better-corroborated theory because it offers the most detailed map of the world currently available, providing the richest basis for further criticism and testing.
   Mechanism: A theory that survives severe tests is one that took a greater risk of being wrong; preferring it is a preference for boldness and precision, acting specifically to try to break it, meaning our 'preference' is actually a preference for the most efficient path to potential falsification.
   Refuted if:
   - refuted if it can be demonstrated that the 'informational content' or 'boldness' of a theory cannot be assessed independently of its probability of being true
   - refuted if the target conflates 'informational content' with 'practical viability', as scientists prefer corroborated theories for accurate predictions, not just to break them
   - refuted if the assertion that 'action becomes purely experimental' fails to account for the stakes involved in real-world application where failure results in catastrophic loss

14. The preference for better-corroborated theories is indefensible on Popper's own terms and constitutes a performative contradiction: acting on corroboration requires an inductive leap that smuggles the principle of uniformity back into the system, reducing the methodology to psychological habit.
   Mechanism: The act of choosing a well-corroborated theory for action (e.g., a bridge design) implicitly asserts that past survival indicates future stability, which is the definition of inductive reasoning Popper sought to destroy; no semantic distinction between 'corroboration' and 'probability' can mask this reliance on past performance as a guide to future reliability.
   Refuted if:
   - refuted if a coherent account can be provided where preferring a better-corroborated theory is justified solely as a method to maximize the severity of future tests without any assumption that the theory will actually succeed or remain unfalsified in the future
   - refuted if Popper explicitly distinguished 'pragmatic preference for action' from 'assertion of future reliability' such that one can choose the best-tested map without assuming the territory will not change
   - refuted if it can be demonstrated that no non-inductive logical rule (such as the methodological rule to test the boldest surviving hypothesis) can govern the preference for better-corroborated theories

15. The preference for better-corroborated theories is defensible without induction because it functions as a methodological rule to maximize the severity of future falsification, selecting the theory that offers the most informative target for error detection rather than the one most likely to succeed.
   Mechanism: Choosing the best-corroborated theory is not a prediction of future truth but a strategic decision to expose the boldiest surviving hypothesis to new risks; if it fails, we learn more than if a weaker theory fails, making the preference a tool for accelerating knowledge growth even if practical application fails.
   Refuted if:
   - refuted if it can be shown that Popper explicitly justified the preference for better-corroborated theories in practical, life-or-death decisions on the grounds of safety or reliability rather than solely on the grounds of maximizing testability
   - refuted if the concept of 'severity' of a test cannot be measured and valued without invoking the inductive assumption that passing severe tests makes a theory more likely to pass future tests
   - refuted if evidence shows researchers consistently choosing less established, riskier hypotheses over well-corroborated ones solely to accelerate falsification

16. The preference is defensible only by accepting a non-probabilistic metaphysical commitment to verisimilitude (truth-likeness), arguing that severe testing logically increases a theory's proximity to truth, but this costs the framework its claim to pure logic by smuggling in a rationalist faith that nature rewards boldness.
   Mechanism: Shifting the goal from 'predictive reliability' to 'structural approximation' allows the preference to survive anti-induction critiques, but it requires the metaphysical hope that surviving severe tests correlates with truth-likeness, a correlation Popper admits cannot be logically proven.
   Refuted if:
   - refuted if it can be demonstrated that the concept of 'verisimilitude' cannot be formally defined without implicitly relying on inductive probability
   - refuted if it can be demonstrated that Popper explicitly grounded the preference in a pragmatic decision rule without invoking any metaphysical assumption about the theory's proximity to truth
   - refuted if a rigorous demonstration shows that a coherent, non-probabilistic measure of verisimilitude exists which successfully ranks theories such that higher corroboration strictly implies greater closeness to the truth

REFUTED POSITIONS (0):
(Positions on 1 derived sub-questions, 9 in all, are not part of this answer.)
```

## 2026-09-06, third segment — the second launch window: the bad configuration withdrawn, the measure re-armed, no arm run (no credential)

**Nothing was measured in this window, and one thing was decided.** The
operator's "failure again. Bad config." named the configuration, and the
configuration was the monitor's own: the evidence-blind critic asked for by
R14. This window WITHDRAWS it rather than repairing it, fixes the two other
things the failed run measured, seals the new rules before any call, and then
stops — the credential the launch needs is not on this container, and R46 says
to stop for that rather than improvise a key. The tranche is one command from
launching.

### 1. What changed, and what each change is answerable for

| change | what it is answerable for |
|---|---|
| ARM R selects the organiser shell for the CONJECTURER only; the critic runs the shipped `seat.critic.legacy-v0` | the death. The blind shell removed the legend from the critic's brief while `rules/crit.py` went on binding the same legend into its form; the critic filled `premise_evidence` with the only ids it could see, was rejected, exhausted its repair ladder and killed the run at cycle 3. Brief and form now agree. P6 stays parked — the defect that lets a blind brief meet a sighted form is untouched; only this tranche's use of it is withdrawn |
| the attachment's headers carry no room record id (P7 road A) | the 58 `EVIDENCE_REF_UNKNOWN_BLOCK` measures. The seat had two id systems in front of it and mixed them 58 times to 21. Now the only ids it can see are the legend's |
| pairwise forced choice replaces the 0–3 rubric for this launch | the ceiling. Eighteen readings, eighteen 15s: the rubric cannot rank anything above a single call on this question. The rubric instrument and its scores are untouched, because they are the record of that |

**What the default critic will and will not see**, from
`src/deepreason/llm/seat_layouts.py:82-106` and `evidence/render.py:192-198`:
it sees the premise invitation and the citable legend — 32 of the 97 admitted
blocks at 160 characters each — and its form's `premise_evidence` menu is
bound from exactly those 32. It does NOT see `dr.evidence.frozen`, the room
whole: that entry is absent from its layout at every priority, so the blocks'
bodies never reach it, and the other 65 arrive only as a withheld count. So
the critic is no longer blind and is not sighted on the room either. It is a
DIFFERENT critic from the failed arm's, which means the two ARM R runs differ
in two places at once — the critic's shell and the attachment's headers — and
neither difference is isolated by the next launch. That is disclosed, not
controlled.

### 2. The attachment, re-measured offline

The 94 room records are byte-identical to the sealed ones (`verbatim 94/94`,
53 493 characters). Three preamble paragraphs are added — one per file,
carrying the header shape and the rule that only the legend's ids resolve —
because the organiser's directive still describes the old `id=` header and
lives under `src/`, which this window may not edit; R40's own fallback says
where the instruction goes instead. Admission therefore mints **97 blocks**
from 3 sources with 0 refusals.

Every block's content id moved with its header, so the legend's hash-ordered
32 is redrawn: **4 conjectures / 17 proposals / 11 objections**, against 7 /
13 / 12 before, with 6 refuted-if proposals visible where 1 was. That is a
measured consequence with a measuring consequence: the census's strict "room
conjectures carried" count resolves only citations of a conjecture's OWN
block, and only 4 of the 12 are citable, so that number is now capped by the
legend rather than by the seat. `tools/organiser_census.py` reports a second
count beside it — conjectures REACHED, named by a verified citation of the
conjecture's block or of a proposal or objection about it. Re-derived on the
retired root, the rewritten census reproduces the recorded seven carried
exactly and adds one reached, which is what proves the new mapping reads the
same record the old one did.

### 3. The predictions this window registered before the launch

From PREREG Amendment 7, sealed by sha256 in commit `8a579f1e6`:
`EVIDENCE_REF_UNKNOWN_BLOCK` **0** (it was 58); `EVIDENCE_CITATION_VERIFIED`
**≥ 21** (it was 21); a CLEAN typed terminal where the first launch died
`operational_failure`; and Amendment 1's cycle prediction unchanged — the
500 000 ceiling ends the run in cycle 3. Nothing is predicted about quality.

### 4. The new instrument, and the ceiling it walks into

`tools/judge_pairwise.py` shows every ARM R unit against every bare unit —
3 pairs against ARM 0, 3 against ARM 0R — to three judges in both orders: six
readings per pair, 36 in total, 18 per bare arm. A judge whose choice flips
when the texts swap places has NO PREFERENCE on that pair. ARM R is MATERIALLY
BETTER only if its consistent-win share is ≥ 2/3 against both bare arms; ≤ 1/3
is WORSE; between is NULL. The control — ARM 0R against ARM 0, 9 pairs, 54
readings — is reported beside the rule and is not part of it.

**Registered in advance, because it is foreseeable and was foreseen for the
rubric too:** the sealed length rule (PREREG §6) reports any BETTER whose
winning unit is more than 1.5× the other's length as NULL
(length-uncontrolled). The first ARM R composed unit was 21 396 characters
against bare units of 5 875–7 985 — ratios of about 2.7× to 3.6×. If this
one is of the same order, **a 9-of-9 sweep for ARM R still reports NULL**, and
the offline proof of the instrument shows exactly that happening. The rule was
not changed to make the verdict reachable; instead the raw consistent-win
share and the verdict-before-the-length-rule are printed and recorded beside
the verdict, so the reader can see what the panel chose and what the rule did
with it. This is the second instrument in a row that can be expected to return
no verdict, and it is stated here before the run rather than after it.

### 5. What ran, and what did not

| | |
|---|---|
| soak | `python -u scripts/cycle_soak.py --case epoch3` → `[soak] exit 0 (clean)` on this tree (`runs/soak.log`) |
| retirement | the failed root renamed to `runs/home-r/runs/failed-epoch1-run-36d9a22c…` and committed alone (`783054bfd`); epoch 1's arm outputs and logs moved whole to `runs/armR-epoch1/`, never overwritten |
| sealed | REQUEST.md Amendment 2 (R37–R51), SPEC.md Amendment 4 (S37–S45), PREREG.md Amendment 7, sha256 `0f76eef1…` in `8a579f1e6`'s message |
| ARM R | **not run** — no credential |
| ARM 0R | not respent by design (reused by digest); its recorded calls pasted the PRE-CHANGE attachment, whose 94 record bodies are byte-identical and whose headers are not; disclosed, not controlled |
| live calls this window | **0** |

### 6. Failure budget (R22)

Six live calls beyond the plan. **Spent: 0**, and none was available to spend.

| # | call | reason | cost | decided |
|---|---|---|---|---|
| — | — | — | — | — |

### 7. Residue — what this segment does NOT show

- It shows nothing about the organiser. No arm ran; there is no unit, no
  census, no verdict.
- It does not show that the critic change fixes the death. It shows that the
  brief and the form now ask for the same thing; whether the run survives is
  what the launch would measure.
- It does not show that one id system removes the 58 unknown-block citations.
  That is a registered prediction, not a result.
- P1–P7 stay parked. P6 in particular is untouched: a blind brief can still
  meet a sighted form anywhere else in the harness, and both of the sections
  this critic depends on are droppable under budget pressure, which would
  re-create the same shape from the allocator rather than the shell.
- ARM H is still deferred, so nothing here separates the harness from the room
  even in principle.
