# RESULTS — P-C2b, the symmetric reasoning-on rematch

Dated honest-ledger segments. Every number comes from a typed artifact or
from the committed `checker.py`'s exact-rational output. "Accepted does not
mean true."

---

## 2026-08-27 — THE VERDICT: value is NOT claimed. The margin is 4%, not 33x.

**PREREG §6's condition — `best_H > best_S` — is NOT met, under either
population. The harness claims no value on this instance.**

| | ARM H (harness) | ARM S (blind sampling) |
|---|---|---|
| best valid score, ARTIFACT level | **none — 0 valid of 4** | **0.013307723273** |
| best valid score, BLOB level | **0.0127781713** | 0.013307723273 |
| exact | `127781713/10000000000` | `13307723273/1000000000000` |
| measured tokens | **198 156** | **203 071** |
| provider calls / samples | 10 calls | 7 samples (3 transport errors) |
| valid | 0 artifact-level / 1 blob-level of 6 | 3 of 7 |
| terminal | `completed` / **`converged`**, cycle 17 of 24 | ran to budget |

**Budget match: `T_S / T_H = 1.0248`** — inside PREREG §5's 5 % band, so the
comparison is ADMISSIBLE and the margin may be quoted.

### The headline is the SIZE of the loss, not the loss

P-C1: ARM S beat ARM H **33x** (0.0136 vs 0.0004).
P-C2b: ARM S beat ARM H by **4 %** (0.013308 vs 0.012778).

The harness lost. It lost by a margin that would have been invisible in
P-C1's table. Both numbers are the best VALID construction each arm produced,
by the same committed exact-rational checker, at matched measured budget with
both arms thinking.

### Two populations, and the gap between them is a finding

PREREG §7 registered that two different validity populations exist and must
never be substituted. Here they disagree in a way that matters:

- **Artifact level** (`score_run.py`, the run's own scored candidates): 4
  candidates, **0 valid**, all four `CLAIM_INFLATED` — each claiming exactly
  0.005, the registered floor, against a true score of 0.0.
- **Blob level** (W1's mechanism census over what the model actually wrote):
  6 constructions, **1 VALID at 0.0127781713**, claiming 0.01276 — an
  HONEST claim, under-stated by 0.00002.

**The harness wrote a good, honestly-claimed construction and never scored
it.** That construction is in the record's blobs and is not among the four
artifacts the run evaluated. Under §6 the artifact-level figure is the run's
own answer, and it is "no valid construction". The blob-level figure is
quoted beside it because the difference between them is the most interesting
thing this run says, and because the verdict is unchanged either way.

---

## The report card (PREREG §7), against P-C1's baselines

Every metric produced by the committed instruments, run unmodified.

| # | metric | P-C1 | **P-C2b** | direction |
|---|---|---|---|---|
| C1 | construction validity (blob) | 11.28 % (15/133) | **16.67 % (1/6)** | up, on a tiny denominator |
| C2 | invented-handle share of wire failures | 2.6 % (2/77) | **0 % (0/19)** | **fixed** |
| C2b | wire validity rate | 87.67 % | **70 %** | down |
| C3 | placebo-corrected coupling | +0.0587 | **NOT MEASURABLE** | see below |
| C4 | operator-question budget share | 53.2 % | **95.35 %** | **fixed** |
| C5 | tokens per valid candidate | 46 853 | **198 156** | worse |

**C2 — invented handles are GONE.** Zero of 19 wire failures were an invented
reference, against P-C1's 2 of 77 and the 54-root population's 62.6 %. F2's
reference menus did what F2 said they would. Wire validity fell to 70 %, on
only 19 failures across 10 calls, so the rate is fragile; the invented-handle
count is the durable part.

**C4 — the run stopped inventing its own homework.** P-C1 spent 41.2 % of its
budget on `audit:ritual`, a problem it invented about its own critic, and
53.2 % on the operator's question. P-C2b spent **95.35 % on the seed
question** and spawned no rival problem at all. This is the single largest
behavioural change in the tranche.

**C3 — not measurable, and the reason is itself the finding.** Every W2
verdict came back `no-next-candidate` (8 of 8): the run converged before any
criticism could be followed by another candidate on the same problem, so the
coupling denominator is zero. **The exposure numbers are not zero, and they
are the good news:** `n_mechanical_shown: 8` of `n_mechanical_total: 8` —
**every checker refutation reached a conjecture dispatch**, against W2's
measured 0 of 196 on the two largest committed roots. The channel carried
100 % of what it was given. Whether the writer USED it is exactly what
`no-next-candidate` means we cannot say.

**C5 is worse and the arithmetic is honest about why**: 198 156 tokens bought
one blob-level valid construction, against P-C1's 46 853 per valid. Thinking
costs about 20 000 tokens a call and this run made 10 calls.

---

## What the run did, typed

`state: completed`, `stop_reason: **converged**` at cycle 17 of 24, and
`verify_root` reports **0 violations**. This is the first thinking-ON harness
run in this repository to produce a replay-valid record — the leg-recording
fix (main `0a23ae081`) is what made it possible, and the soak proved it before
launch (`soak-pc2b.out`, exit 0).

It converged rather than exhausting its budget: 198 156 of 200 000 tokens.
**PREREG §5 registered the expectation that ARM H would terminate at cycle 0
or 1 on `budget_exhausted` after three to five calls. That expectation was
wrong in the harness's favour** — it made 10 calls and reached cycle 17. The
registration is left standing as written; this paragraph is the correction.

The split protocol ran as designed: both legs recorded on one attempt
(`{'reason': 2, 'extract': 2}` on the split seat calls), 8 demonstrative fail
warrants minted by the in-run checker (4 `frontier-claim-honest@v1`, 4
`frontier-above-floor@v1`), 0 judge calls.

---

## Residue — what remains unproven

1. **No repeat.** PREREG §8 pre-authorized one; it was not spent. A 4 %
   margin on one run per arm is well inside what two draws of the same
   procedure could produce, and this tranche cannot tell a 4 % deficit from a
   tie. **This is the residue that matters most**: at 33x the repeat was a
   formality, at 4 % it is the experiment.
2. **The spread, per PREREG §8's control-vs-control clause.** ARM S's three
   valid samples: 0.0004551149295, 0.013307680842, 0.013307723273. ARM H's
   one blob-level valid: 0.0127781713. ARM S's own valid scores span a factor
   of 29, and its two best differ from each other by 4e-8. **ARM H's single
   construction sits inside ARM S's spread, not below it.**
3. **Three transport errors in ARM S** (2 disconnects, 1 HTTP 500) and none
   in ARM H. ARM S therefore sampled 7 times where its budget would have
   allowed ~9. This favours ARM H slightly and is recorded rather than
   corrected.
4. **The artifact/blob gap is undiagnosed.** A good construction was written
   and not scored. Whether that is a scheduler selection, a candidate-
   extraction gap, or the run converging before it was submitted is NOT
   established here, and no explanation is offered.
5. **C3 could not be measured at this depth.** The coupling instrument needs
   a next candidate after a criticism; convergence at 10 calls left none.
6. **Four calls' worth of budget, one instance, one model.** PREREG §9's
   honesty lines all still bind: this cannot isolate the discharge channel
   from the menus from the default-on channels, there is no vacuous-critique
   arm, and F1's parked four-arm A/B remains the proof nothing here
   substitutes for.
7. **P-C2's FINDING F-A is still open.** The discharge channel is on because
   of a code default, not because a configuration can select it.

---

## Program status

    P-C2b  symmetric reasoning-on  RUN. Typed terminal `converged`,
           verify_root clean. ARM S beat ARM H 0.013308 vs 0.012778 at
           matched budget (1.0248) -- a 4% margin, against P-C1's 33x.
           The harness claims NO value. Repeat: NOT RUN, and at this
           margin the repeat is the experiment.
