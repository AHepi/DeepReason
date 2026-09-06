# RESULTS — the writer's room: limits, forms, and a census of what is ejected

Honest-ledger segments, dated. Nothing here claims more than the record
shows.

## 2026-09-06 — the census (S4, R3): do the commitment artifacts have anything in them?

**Yes, now — and the sealed test still fails on one of its four clauses.**
After the limit fix and the room forms, one live three-cycle room run
(`runs/home-room/shallow-runs/shallow-0b47bc7b090854078ddf7559`) produced 12 conjectures,
36 objections and 46 commitment proposals. Every one of the
27 briefs reached the model with its instruction intact (the D8
run: 9 of 19). Every proposal names an existing conjecture, every proposal's
first sentence binds it — "is refuted if", "forbids", "must not", "predicts",
in 12/12/12/10 proposals — and every conjecture
received a refutation condition that is not a restatement of its own
conclusion. What fails is PREREG_CENSUS §"What decides" clause 3's second
half: `exact-dup = 0`. Three pairs of proposals are byte-identical — the
commitment seat wrote the same must-not, forbids and predicts for two of
cycle 2's four conjectures. The rule was sealed with that clause; the answer
is reported as the rule reads it, and the duplicates are quoted below.

### 1. Sealed before the run

| | |
|---|---|
| PREREG_CENSUS.md | sha256 `40ff8f8e8142b8e4bf806481e2fff578f4a817da2c7a3b44b96ffc534ca6c6f6`, commit `482b5f4b5` |
| tools/census.py | sha256 `0d871946c42fb4c8e03158bf0f5582227c9392e6971a2f972da75c0a1d92f792`, same commit; unchanged since |
| soak | `cycle_soak --case epoch3` exit 0 (clean) on this tree, immediately before the launch (`room/soak.log`) |
| launch | `room/run_chain.sh`, detached, snapshot loop; 06:06:54Z → 06:10:34Z |

### 2. The run's typed terminal (`room/ROOM_TERMINAL.json`)

    completed true   stop queue-exhausted   cycles 3   flow mini.flow.room.v1
    model profile standard (forwarded from the provider profile; the flow's own limit 12 000 chars binds)
    conjectures 12 (4 / 4 / 4 by cycle -- the requested count, every cycle)   refuted 0
    records: mini.criticism.v1 36   mini.commitment-proposal.v1 46
    calls 27 (3 conjecture + 12 critic + 12 commitment)   tokens 70336 of 400 000
    meter_equals_log true   verify_root 0 violations   replay digest == live   TYPED_TERMINAL COMPLETE

### 3. The census (`tools/census.py`, the instrument's table)

**After** (this run) and **before** (the D8 root through the same instrument):

| seat | calls | outputs | tokens | chars min/mean/max | on-target | mentions | binds-1st | exact-dup | near-dup | echo |
|---|---|---|---|---|---|---|---|---|---|---|
| commitment | 12 | 46 | 43520 | 234/306/398 | 46 | 46 | 46 | 6 | 25 | 1 |
| critic | 12 | 36 | 17723 | 622/864/1038 | 36 | 25 | 7 | 0 | 16 | 4 |
| conjecturer | 3 | 12 | 9093 | 592/694/813 | – | 8 | 2 | 0 | 8 | – |

    briefs 27   directive intact 27   clipped markers 0

| before: D8 root, seat | calls | outputs | tokens | chars | on-target | mentions | binds-1st | exact-dup | near-dup | echo |
|---|---|---|---|---|---|---|---|---|---|---|
| commitment | 8 | 14 | 24280 | 302/647/1242 | 14 | 12 | 8 | 6 | 14 | 2 |
| critic | 8 | 24 | 8561 | 512/624/775 | 24 | 12 | 2 | 0 | 11 | 3 |
| conjecturer | 3 | 8 | 6736 | 458/546/628 | – | 6 | 1 | 0 | 7 | – |

    briefs 19   directive intact 9   clipped markers 10

Reading the columns. `binds-1st` is the strict shape (the first sentence
itself binds the conjecture): 46 of 46 now, 8 of 14 before — and the
before-row's 8 includes essays whose opening sentence happened to contain
"must". `near-dup` is loose by construction (three shared six-word phrases,
on one question with a fixed vocabulary — "the preference for
better-corroborated theories" alone is six words); `exact-dup` is the number
that means something, and it is 6 (three pairs) against 6 (one triple filed
twice) before. Proposals are SHORT now (mean 306 characters against 647):
one binding sentence each, no essay.

### 4. The sealed rule, clause by clause (PREREG_CENSUS §"What decides")

| clause | requirement | this run | holds |
|---|---|---|---|
| 1 | directive intact on every commitment brief | 12 of 12 (27 of 27 overall) | yes |
| 2 | on-target = outputs | 46 of 46 | yes |
| 3 | binds-1st ≥ half the proposals AND exact-dup = 0 | 46 of 46; exact-dup 6 | **no** — the second half |
| 4 | a non-restating refutation condition per conjecture | 12 of 12 (the *refuted-if* proposals in the appendix; the assistant's reading) | yes |

So: **three of four clauses hold; the commitment seat's output has real
content; the rule as sealed does not grant "anything in them" because of
three duplicated pairs.** Not re-run. The duplicates, verbatim, are in the
appendix under cycle 2's conjectures `d8dfb83a` and `055185d5`: the seat wrote
one refutation condition per conjecture (those differ) and then the same
must-not / forbids / predicts for both — two conjectures that are close
relatives (the "verisimilitude gamble" and the "performative contradiction"
charge), which the seat treated as one.

### 5. Predictions (PREREG_CENSUS §Predictions)

| prediction | outcome |
|---|---|
| directive intact on every call, clipped markers 0 | **HELD**: 27 / 27, 0 |
| exact-dup among proposals 0 | **FALSIFIED**: 6 (three pairs) |
| the conjecturer returns the requested number every cycle | **HELD**: 4 / 4 / 4 |
| binds-1st: no direction | 46 of 46, recorded |

### 6. What else the record shows

- **"Everything so far" is still not everything, and now the record says
  how far from it.** The pool after three cycles is 53,493 characters of
  content (12 conjectures, 36 objections, 46 proposals). Under the room's
  12 000-character limit the everything section — capped by its stage share
  at 60 % of the limit — showed the newest entries and withheld, with the
  count in the brief, 10 entries at the first commitment call and 79 at the last
  (briefs 9,047–9,875 characters, all inside the limit, none clipped).
  To show a three-cycle pool whole the flow would need about
  53,000 characters — a sixth of the model's context window, and a
  one-line configuration change (`brief_budget_chars` on the flow, and a
  `brief_share` of 1.0 on the commitment and conjecture stages). Not done
  here: R1 asked for the limit that cut instructions to change, and it has;
  how much of the room a seat should see is the operator's setting.
- **The objections are on target and mostly bind too**: 36 of 36 name their
  conjecture, 7 open with a binding sentence, 25 mention a refutation or
  prohibition; mean 864 characters. Sample: "The 'pragmatic wager' defense
  collapses because the very act of selecting a theory based on past survival
  implicitly assumes that past performance is a reliable indicator of future
  utility…"
- **The conjecturer used its optional `angle` label on all 12**: The
  Pragmatic Wager · Verisimilitude as a Regulative Ideal · The Performative
  Contradiction · Corroboration as Informational Content · The Methodological
  Rule Defense · The Verisimilitude Gamble · The Pragmatic Inconsistency Charge
  · The Decision-Theoretic Void · The Pragmatic Wager without Induction · The
  Verisimilitude Trap · Corroboration as a Historical Report, Not a Future
  Guide · The Asymmetry of Risk. Cycle 3's four are variations on cycle 1's —
  the room converges; nothing in it is built to stop that, by the operator's
  ruling.
- **Spend**: 70336 tokens; commitment 43520 (61 %), critic 17723 (25 %), conjecturer 9093 (12 %). Every
  call landed first time.
- **R4 held live**: the separation test's checks pass on this root as on
  the stub (`mini/tests/test_mini_room_separation.py::assert_separated`).

### 7. Residue

- One run, one question, one model: a census of a sample.
- The duplicate pairs are the one measured defect of the room's content;
  whether they are the seat's habit or an artefact of two near-identical
  targets is one more run's question, not this one's.
- The room ran through the reasoning-field override (predecessor P10, still
  parked).
- The proposals' worth as commitments is for the full harness to decide
  (Amendment 1 of the predecessor); this census says they have the SHAPE and
  the SPECIFICITY of commitments, not that they are good ones.

### Appendix — every commitment proposal, verbatim, by the conjecture it binds

**Cycle 1 · conjecture `a0b919ae` · angle: The Pragmatic Wager** — 4 proposals

> The preference for better-corroborated theories is defensible without induction because it is a pragmatic wager, not an epistemic probability claim. Popper argues that while past success guarantees nothing about the future (rejecting induction), the theory that has survived the severest tests has proven its 'fitness' in the specific environment of reality so far. Choosing it is akin to betting on the horse that has won every race; we do not know it will win the next, but it is the only rational choice available if we must act, as it has demonstrated a capacity to withstand falsification that o…

- *refuted-if*: The conjecture is refuted if it can be demonstrated that preferring the better-corroborated theory logically entails an assumption that the future will resemble the past, thereby making the 'pragmatic wager' indistinguishable from the inductive principle Popper explicitly rejects.
- *forbids*: The conjecture forbids attributing any increased likelihood of future success or truth to a theory solely on the basis of its survival of past tests; it must maintain that the preference is entirely devoid of predictive probability.
- *must-not*: The conjecture must not claim that the 'fitness' demonstrated by surviving severe tests provides a rational basis for action if that basis secretly relies on the unstated premise that nature is uniform enough for past fitness to matter for future outcomes.
- *predicts*: The conjecture predicts that a consistent Popperian agent, when forced to choose between two unfalsified theories where one is better corroborated, will always choose the better-corroborated one while simultaneously asserting they have no reason to believe it will perform better in the next instance.

**Cycle 1 · conjecture `92968bc0` · angle: Verisimilitude as a Regulative Ideal** — 4 proposals

> The defense lies in shifting the goal from 'probability' to 'verisimilitude' (truth-likeness). A highly corroborated theory is not more probable, but it is a better candidate for being closer to the truth because it has withstood attempts to show it is false. The preference is defensible because science aims at truth, not certainty; therefore, selecting the theory with the highest empirical content that has not yet been refuted is the only methodological move consistent with the aim of increasing verisimilitude. The cost here is the admission that we can never verify this progress; we must ope…

- *refuted-if*: The conjecture is refuted if it can be shown that the concept of 'verisimilitude' (truth-likeness) cannot be formally defined without implicitly relying on inductive probability, thereby making the shift from probability to verisimilitude merely a semantic disguise for the very induction Popper rejected.
- *forbids*: The conjecture forbids claiming that surviving severe tests provides a rational basis for preferring one theory over another unless it can demonstrate a logical connection between test survival and increased truth-likeness that does not itself assume the uniformity of nature.
- *must-not*: The conjecture must not treat the 'metaphysical hope' that surviving tests correlates with truth-likeness as a sufficient defense against the charge of cryptic inductivism if that hope functions identically to an inductive premise in guiding practical scientific action.
- *predicts*: The conjecture predicts that a scientist acting strictly on this verisimilitude-based preference will choose the better-corroborated theory for critical applications while simultaneously maintaining that this choice offers no greater expectation of predictive success than choosing a random unfalsified theory.

**Cycle 1 · conjecture `67873974` · angle: The Performative Contradiction** — 4 proposals

> The preference is indefensible on Popper's own terms and indeed smuggles induction back in through the back door. By advising scientists to 'prefer' the better-corroborated theory for action, Popper implicitly asserts that past performance is a reliable guide to future reliability, which is the very definition of inductive reasoning he sought to destroy. If corroboration reports only past history and implies nothing about the future, then preferring Theory A over Theory B for future application is irrational within his system. Accepting this view costs the coherence of Popper's philosophy, red…

- *refuted-if*: The conjecture is refuted if a coherent account can be provided where preferring a better-corroborated theory is justified solely as a method to maximize the severity of future tests (i.e., choosing the theory most likely to fail quickly if false) without any assumption that the theory will actually succeed or remain unfalsified in the future.
- *forbids*: The conjecture forbids equating the pragmatic choice of a theory for application with an epistemic belief in its truth or future reliability; it must maintain that acting on a corroborated theory is a decision to expose it to new risks, not a prediction of its safety.
- *must-not*: The conjecture must not claim that Popper's framework reduces to mere psychological habit unless it first demonstrates that no non-inductive logical rule (such as the methodological rule to test the boldiest surviving hypothesis) can govern the preference for better-corroborated theories.
- *predicts*: The conjecture predicts that if its interpretation is correct, a consistent Popperian scientist would be unable to rationally distinguish between choosing a well-tested bridge design and a randomly selected unfalsified design for actual construction, as both choices would carry identical expectations regarding future performance.

**Cycle 1 · conjecture `e0959a2b` · angle: Corroboration as Informational Content** — 4 proposals

> The preference is defensible because corroboration functions as a measure of informational content rather than likelihood. A theory that survives severe tests is one that took a greater risk of being wrong; preferring it is a preference for boldness and precision. We choose the better-corroborated theory not because we think it will hold true, but because it offers the most detailed map of the world currently available, providing the richest basis for further criticism and testing. The cost of this stance is that 'action' becomes purely experimental; we act on the bold theory specifically to t…

- *refuted-if*: The conjecture is refuted if it can be demonstrated that the 'informational content' or 'boldness' of a theory cannot be assessed independently of its probability of being true, thereby collapsing the distinction between preferring a bold theory and preferring a probable one.
- *forbids*: The conjecture forbids attributing any pragmatic advantage to the better-corroborated theory regarding its reliability in future applications, such as bridge building or medical treatment, beyond its utility as a tool for generating new tests.
- *must-not*: The conjecture must not claim that acting on a theory solely to falsify it constitutes a coherent defense for scientific practice in domains where failure results in catastrophic loss rather than merely new knowledge.
- *predicts*: The conjecture predicts that a scientist strictly adhering to this view would choose the most precise, high-risk theory for critical real-world decisions even when a vaguer, safer, and equally unfalsified alternative exists, provided the choice is framed as an experiment.

**Cycle 2 · conjecture `da6f74be` · angle: The Methodological Rule Defense** — 4 proposals

> Popper's preference for better-corroborated theories is defensible without induction because it functions not as an epistemic probability claim but as a methodological rule of thumb: we choose the theory that has withstood the severest tests simply because it is the most informative target for future falsification. This preference does not assume the theory will succeed in the future; rather, it assumes that if the theory is false, this specific candidate is the most likely to reveal its falsehood quickly, thereby accelerating the growth of knowledge even if the practical application fails.…

- *refuted-if*: The conjecture is refuted if it can be shown that Popper explicitly justified the preference for better-corroborated theories in practical, life-or-death decisions (such as crossing a bridge) on the grounds of safety or reliability rather than solely on the grounds of maximizing testability and information content.
- *must-not*: The conjecture must not imply that a scientist acting on a well-corroborated theory expects it to work in the future; if the defense requires any expectation of future success derived from past performance, it smuggles in the very induction it claims to avoid.
- *forbids*: The conjecture forbids the interpretation that corroboration serves as a proxy for truth-likeness or verisimilitude in decision-making contexts; it restricts the function of corroboration strictly to identifying the best candidate for immediate falsification.
- *predicts*: The conjecture predicts that if one were to choose a less-corroborated theory over a better-corroborated one purely for practical action, Popper would criticize this not as irrational risk-taking, but as a methodological failure to prioritize the speed of error detection.

**Cycle 2 · conjecture `d8dfb83a` · angle: The Verisimilitude Gamble** — 4 proposals

> The preference is defensible only by accepting a non-probabilistic metaphysical commitment to verisimilitude (truth-likeness), arguing that while we cannot know a theory is true or probable, severe testing logically increases its content and proximity to truth. This stance survives Popper's anti-induction critique by shifting the goal from 'predictive reliability' to 'structural approximation,' but it costs the framework its claim to pure logic, smuggling in a rationalist faith that nature rewards boldness with truth-likeness rather than random chaos.

- *refuted-if*: The conjecture is refuted if it can be demonstrated that Popper explicitly grounded the preference for better-corroborated theories in a pragmatic decision rule (such as minimizing immediate risk or maximizing informational content) without invoking any metaphysical assumption about the theory's proximity to truth or verisimilitude.
- *must-not*: The conjecture must not conflate the methodological rule of preferring bold, testable theories with a metaphysical belief that nature is structured to reward such boldness with truth; the defense must remain agnostic regarding nature's actual response to boldness. **[byte-identical to proposal `7bba8c75`]**
- *forbids*: The conjecture forbids the interpretation that accepting verisimilitude as a guide for action necessarily reintroduces probabilistic induction, provided that verisimilitude is treated as a logical relation of content rather than a statistical likelihood of future success. **[byte-identical to proposal `87fd1b23`]**
- *predicts*: The conjecture predicts that if the preference for corroborated theories were based solely on past performance without the 'verisimilitude gamble,' Popper would be unable to distinguish rational scientific choice from arbitrary selection in cases where two theories have survived an equal number of tests but differ in content. **[byte-identical to proposal `79f08521`]**

**Cycle 2 · conjecture `055185d5` · angle: The Pragmatic Inconsistency Charge** — 4 proposals

> The preference is indefensible on Popper's own terms and constitutes a performative contradiction: when Popper chooses a well-corroborated bridge design over an unfalsified but untested one, he acts exactly as an inductivist would, relying on the implicit premise that past survival indicates future stability. This candidate argues that no amount of semantic maneuvering around 'corroboration' vs. 'probability' can mask the fact that acting on corroboration requires an inductive leap, meaning Popper's system collapses into crypto-induction whenever it leaves the realm of abstract methodology.…

- *refuted-if*: The conjecture is refuted if it can be demonstrated that Popper explicitly justified the preference for better-corroborated theories in practical decisions solely on the grounds of maximizing testability and information content, without invoking any expectation of future success based on past performance.
- *must-not*: The conjecture must not conflate the methodological rule of preferring bold, testable theories with a metaphysical belief that nature is structured to reward such boldness with truth; the defense must remain agnostic regarding nature's actual response to boldness. **[byte-identical to proposal `3c12f1ad`]**
- *forbids*: The conjecture forbids the interpretation that accepting verisimilitude as a guide for action necessarily reintroduces probabilistic induction, provided that verisimilitude is treated as a logical relation of content rather than a statistical likelihood of future success. **[byte-identical to proposal `860860e7`]**
- *predicts*: The conjecture predicts that if the preference for corroborated theories were based solely on past performance without the 'verisimilitude gamble,' Popper would be unable to distinguish rational scientific choice from arbitrary selection in cases where two theories have survived an equal number of tests but differ in content. **[byte-identical to proposal `a32e11e9`]**

**Cycle 2 · conjecture `20b35eec` · angle: The Decision-Theoretic Void** — 4 proposals

> Popper's framework offers no rational basis for preference in single-case decisions, rendering the scientist's choice between theories arbitrary unless they secretly reintroduce induction. If one strictly adheres to Popper's denial that corroboration implies future success, then choosing the better-corroborated theory for a critical application is logically indistinguishable from flipping a coin, as both options possess equal logical status regarding future performance; thus, the 'preference' scientists feel is merely a psychological habit that Popper mistakenly tried to rationalize as a philo…

- *refuted-if*: The conjecture is refuted if Popper can be shown to have explicitly grounded the preference for better-corroborated theories in a non-inductive decision rule, such as maximizing informational content or minimizing the risk of immediate falsification, without invoking any expectation of future success based on past performance.
- *must-not*: The conjecture must not conflate the methodological imperative to test bold theories with a metaphysical belief that nature rewards such boldness with truth; it must remain agnostic regarding whether the universe is structured to favor high-content theories.
- *forbids*: The conjecture forbids the interpretation that accepting verisimilitude (truth-likeness) as a guide for action necessarily reintroduces probabilistic induction, provided that verisimilitude is treated strictly as a logical comparison of content rather than a statistical prediction of future reliability.
- *predicts*: The conjecture predicts that if the preference for corroborated theories were based solely on past survival without a 'verisimilitude gamble' or similar non-inductive heuristic, Popper would be unable to distinguish rational scientific choice from arbitrary selection in cases where two theories have survived an equal number of tests but differ significantly in empirical content.

**Cycle 3 · conjecture `6b78e82f` · angle: The Pragmatic Wager without Induction** — 3 proposals

> Popper's preference for the better-corroborated theory is defensible not because it predicts future success (which would be induction), but because it represents the only rational 'bet' available to an agent who must act. Since we cannot know the truth, choosing the theory that has withstood the most severe tests maximizes the informational content at risk; if it fails, we learn more than if a weaker theory fails. The preference is a methodological rule for maximizing learning potential in the face of ignorance, not a probabilistic claim about the world's stability.…

- *refuted-if*: The conjecture would be refuted if it could be demonstrated that maximizing 'informational content at risk' logically necessitates an assumption that the future will resemble the past, thereby collapsing the proposed distinction between a methodological rule for learning and a probabilistic claim about the world's stability.
- *forbids*: The conjecture forbids interpreting the preference for better-corroborated theories as having any predictive power regarding the specific success of the theory in the next immediate test case; it must strictly limit the justification to the value of the potential falsification itself.
- *must-not*: The conjecture must not imply that an agent acting on this 'rational bet' expects a higher rate of successful outcomes compared to choosing a less corroborated theory, as such an expectation would reintroduce the inductive principle of uniformity that the conjecture explicitly seeks to avoid.

**Cycle 3 · conjecture `6bdc16fc` · angle: The Verisimilitude Trap** — 3 proposals

> The preference for better-corroborated theories inevitably smuggles induction back into Popper's system because 'verisimilitude' (truth-likeness) functions as a covert proxy for probability. To prefer Theory A over Theory B on the grounds that A is 'closer to the truth' based on past tests is to assume a uniformity in nature: that the structural features which allowed A to survive will continue to align with reality. Without this inductive assumption, the concept of verisimilitude offers no actionable guide for the future, rendering Popper's advice to scientists practically empty.…

- *refuted-if*: The conjecture would be refuted if Popper explicitly distinguished 'verisimilitude' as a logical relation of content comparison rather than a predictive expectation, demonstrating that one can prefer a theory with higher verisimilitude solely to maximize the severity of future tests without assuming the future will resemble the past.
- *forbids*: The conjecture forbids the interpretation that acting on a theory with greater verisimilitude entails a belief that this theory is more likely to yield true predictions in specific future applications compared to a less corroborated rival.
- *must-not*: The conjecture must not conflate the methodological rule of choosing the best-tested theory for the purpose of critical discussion with the psychological act of expecting successful practical outcomes, as doing so would misrepresent Popper's separation of the context of justification from the context of discovery.

**Cycle 3 · conjecture `e8cdaadd` · angle: Corroboration as a Historical Report, Not a Future Guide** — 4 proposals

> The tension dissolves if we strictly segregate corroboration as a purely historical report from the act of choosing a theory for action. Popper can defend the preference by arguing that while corroboration says nothing about the future, the *act* of preferring the best-tested theory is a non-rational, psychological commitment necessary for life, distinct from scientific logic. On this view, the preference is defensible as a biological or pragmatic imperative for survival, but it constitutes a departure from strict rationality, admitting that science alone cannot dictate action without an extra…

- *refuted-if*: The conjecture would be refuted if Popper explicitly argued in his published works that the preference for well-corroborated theories in practical action is a 'non-rational' or purely 'psychological' commitment, rather than a methodologically rational choice based on critical discussion.
- *forbids*: The conjecture forbids the interpretation that Popper considered the act of choosing the best-tested theory for action to be a logical extension of scientific rationality; it must maintain that this specific choice lies outside the bounds of strict scientific logic.
- *must-not*: The conjecture must not imply that the 'biological or pragmatic imperative' cited as the basis for action retains any epistemic weight regarding the truth-likeness or future reliability of the theory, as this would reintroduce the inductive element the conjecture claims to isolate.
- *predicts*: The conjecture predicts that any attempt to justify the preference for corroborated theories in action solely through Popperian scientific logic will fail, necessitating an appeal to extra-logical factors such as instinct, convention, or pragmatic survival needs.

**Cycle 3 · conjecture `76f24493` · angle: The Asymmetry of Risk** — 4 proposals

> The preference is defensible on Popperian terms through the asymmetry of risk: rejecting a well-corroborated theory in favor of a poorly tested one increases the likelihood of immediate error without offering any compensatory increase in testability. While this looks like induction, it is actually a logical deduction about the current state of knowledge; the better-corroborated theory is simply the one that has not yet been falsified despite greater exposure to falsification. Choosing it minimizes the 'known unknowns' relative to alternatives, a defensive posture that requires no belief in the…

- *refuted-if*: The conjecture would be refuted if it could be demonstrated that the concept of 'minimizing known unknowns' logically entails a probabilistic assessment of future performance, thereby collapsing the distinction between a deductive statement about past tests and an inductive expectation of future reliability.
- *forbids*: The conjecture forbids the interpretation that choosing the better-corroborated theory provides any rational basis for expecting it to succeed in the next specific instance; the justification must remain strictly limited to the logical asymmetry of having survived more severe tests thus far.
- *must-not*: The conjecture must not imply that the 'defensive posture' of avoiding immediate error is functionally equivalent to a strategy for maximizing long-term predictive success, as such an equivalence would smuggle in the principle of the uniformity of nature that Popper rejected.
- *predicts*: The conjecture predicts that a consistent Popperian agent can prefer Theory A over Theory B for action while simultaneously maintaining that there is no logical reason to believe Theory A is more likely to be true or to yield correct predictions than Theory B in any future trial.
