# Coin-system canonicity — glm-5.2 native vs. the harness

Question: given a coin system C = (c_1 > ... > c_n = 1), decide whether
greedy is optimal for every amount, return the smallest counterexample if
not, prove why a finite search suffices, and state the complexity in n.
Verbatim in `QUESTION.txt`.

Both attempts were given the same knowledge. The dossier states
definitions and rules of evidence only — no bounds, no example systems,
no prior results — so the harness had no head start; only the process
differs.

Ground truth is `oracle.py`, written here and independent of both: exact
DP for OPT, direct simulation for greedy, exhaustive enumeration of
strictly decreasing systems with values <= 24 and <= 5 coins (10,902
systems, 10,212 of them non-canonical).

## Native attempt

One call, thinking on, `reasoning_effort: high`. 82 s, 277 prompt +
7,526 completion tokens, `finish_reason: stop`. Verbatim in
`native_response.json`; the visible answer is `native_answer.md`.

It gave a complete, well-organised answer: DP up to a bound W, compare
against greedy, return the first mismatch; correctly named Pearson (2005)
O(n^3) as the polynomial-in-n procedure; correctly labelled its own
procedure pseudo-polynomial; and correctly flagged the bound as the part
it was least sure of.

The bound is wrong. It used W = c_1 + c_3 and defended it with

> "Because the tuple is strictly decreasing, c_3 >= c_{n-1} (for n >= 3)
> ... Therefore, checking up to c_1 + c_3 is strictly safer."

which reads `c_3` in the increasing-index convention of the literature
while the question defines a decreasing one. Under the question's own
convention c_3 is the THIRD LARGEST coin, so c_1 + c_3 <= c_1 + c_2: the
bound is strictly less safe, not more. The self-assessment pointed at the
right sentence and then reassured itself about it.

Consequence, measured: the procedure returns "Canonical" for systems that
are not. On (4, 3, 1) — the textbook case — the smallest counterexample
is 6 (greedy 4+1+1 = 3 coins, optimal 3+3 = 2), and its bound is 5.

## Harness attempt

`run-c5f901f38208e862f4ce2fe60a26e551`, home
`experiments/live_coin_canonicity_2026-07-31/home`. Qualification was a
cache hit against the openchallenge battery (1 s; same profile, same
opt-ins). Reason phase 2,135 s, 26 provider calls, 180,416 tokens of the
200,000 budget, 6 cycles, 29 artifacts, 42 problems. Typed stop:
`budget_exhausted`. `verify_root`: **0 violations**.

Every distinct upper bound that appeared, judged by the oracle against
all 10,212 non-canonical systems:

    claimed bound                       violations   first violating system
    c_1 + c_3      (native)                    868   (4,3,1) w=6 > 5
    c_1 + c_2      (harness c6824f04)            0   -- survives all --
    c_1 + c_2 - 1  (harness 7d65ec73)            0   -- survives all --
    c_2 + c_3      (harness 3cfb0351)          1127   (4,3,1) w=6 > 4
    c_3 + c_{n-1}  (harness 00f8ee2c)          4516   (4,3,1) w=6 > 4
    c_{n-1} + c_n  (harness 4210e2c6)        10212   (4,3,1) w=6 > 4

The harness held the correct bound and four wrong ones side by side, as
rivals, instead of committing to one. It is worth being exact about what
that is worth: it did not SELECT the right one — the run stopped on
budget with 14 candidates still surviving and no adjudication between
them. What it did was refuse to collapse the disagreement prematurely.

It also refuted its own worst bound from inside, twice, by concrete
counterexample rather than by argument:

  - `0bba33fda292`: c_{n-1} + c_n fails on (25, 10, 1) — smallest
    counterexample 30, bound 11. Oracle confirms: 30, greedy 6, optimal 3.
  - `312fecd1888f`: same bound fails on (6, 5, 1) — counterexample 10,
    bound 6. Oracle confirms: 10, optimal 2. The candidate's prose
    miscounts greedy(10) as 6 when it is 5; the refutation survives the
    slip, since optimal is 2 either way.

Both refutations are correct, and neither was checked by machine inside
the run. That is the gap this run did not close.

## The capability channel: zero proposals, and the reason is typed

`capability_requests: 0`, `simulation_requests: 0`,
`simulation_executions: 0`. No research proposal either. Several
candidates say plainly that they lack the mandated simulation — the model
knew the requirement and wrote the omission into its own text.

The record says why, and it is not simply that the model declined.
Counting conjecture work by contract and terminal status:

    coin (this run)          conjecturer.turn.v6           completed x0
                             conjecturer.turn.v6           budget_denied x14
                             conjecturer.turn.v6           rejected x5
                             conjecturer.turn.v6           schema_exhausted x2
                             conjecturer.atomic-candidate  completed x12

    tensorrank (2026-07-30)  conjecturer.turn.v6           completed x1
                             conjecturer.turn.v6           budget_denied x7
                             conjecturer.turn.v6           rejected x2
                             conjecturer.turn.v6           schema_exhausted x2
                             conjecturer.atomic-candidate  completed x12

`conjecturer.turn.v6` is the only contract that carries
`simulation_proposals`. `AtomicConjectureCandidateWireV1` has exactly two
fields, `candidate` and `abstention` — no capability channel at all. In
this run NO v6 turn ever completed, so every surviving candidate was
authored under a contract with no field in which a simulation could have
been filed. In the tensorrank run exactly one v6 turn completed, and that
is where both of its capability proposals came from.

So "the model did not use the channel" understates it: for the twelve
candidates that survived, the channel did not exist on the wire they were
writing to, while the prompt required its use and the critics convicted
them for the omission.

Parked as **D3**: after compact recovery decomposes a conjecture turn
into atomic candidate slots, the capability channels silently disappear,
and candidates are then criticised for failing to use a channel their
contract does not offer. This is the same defect class as D2b — a
mismatch between what is enforced and what the model can see or do — one
layer up.

## What this says about the D2b fix

Nothing yet, and that is the honest answer. D2b put the
`simulate(inputs, rng)` contract into the pack; this run never reached a
state where a program could be submitted, so the disclosure was never
exercised. INCONCLUSIVE for that path, exactly as the tranche's VERIFY.md
predicted it might be.

One thing the comparison does establish, unexpectedly: the two runs have
byte-identical structural profiles — 26 calls, 21 first-pass valid, 5
schema-exhausted, 1 recovery route, 2 contract decompositions, in both.
The pack grew by ~1.2 KB under D2b and the run shape did not move.

## Residue

**The harness did not answer the question.** It stopped on budget with
rivals unadjudicated. A user who wanted a single procedure got a live
disagreement instead — better calibrated than a confident wrong answer,
and less useful than a right one.

**The native answer is more useful and less correct.** It is complete,
readable, and would silently mis-certify systems. Which is preferable
depends on whether the reader will check.

**Neither attempt proved anything about the bound.** The correct bound
appears in the harness only as an attributed memory of Kozen–Zaks, with
no proof and no machine check. My oracle tested it against 10,212
systems and found no violation; that is evidence, not a proof, and the
enumeration is bounded at values <= 24 and <= 5 coins.

**One run, one question.** Capability use is stochastic and this is a
single sample. Nothing here supports a general claim that the harness
beats the native call or that it does not.
