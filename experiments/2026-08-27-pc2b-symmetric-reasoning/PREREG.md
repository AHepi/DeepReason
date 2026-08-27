# PREREG — P-C2b, the SYMMETRIC reasoning-on rematch

**Frozen before any provider call.** Committed and pushed before the key is
used; the git log is the proof, and `driver.log`'s first entry postdates the
push.

Nothing in §1–§10 may be edited after launch. A design that turns out wrong
is recorded in RESULTS.md as a finding, or APPENDED here, never repaired in
place.

---

## §1 — Authority

The operator's controlling instruction, 2026-08-27, quoted in the parts that
bind:

> "I want the two-arm comparison run WITH THE MODEL'S REASONING MODE ENABLED
> IN BOTH ARMS, at 200,000 tokens per arm."
>
> "'Reasoning on' means: glm-5.2's thinking/reasoning mode is ENABLED in the
> provider profile for BOTH arms — the model gets to think before answering.
> It does NOT mean anything about the harness's criticism machinery; it is
> the per-call reasoning toggle. In ARM H (harness), enable it in the run's
> provider profile, using the shipped two-call split-budget protocol so a
> long reasoning trace still yields an extractable answer. In ARM S
> (sampling script), enable the same reasoning mode on its raw calls, with a
> completion cap sized so answers survive (mirror the same reasoning/emission
> split the profile uses). The two arms must be SYMMETRIC in this: same
> model, same reasoning setting, same effective caps."
>
> "BUDGET: 200,000 tokens per arm, measured as total logged tokens (reasoning
> tokens count — they are paid tokens). Same admissibility rule as before:
> the arms' measured totals within 5% of each other or the comparison is not
> quoted."
>
> "EVERYTHING ELSE UNCHANGED from the P-C2 design."
>
> "If your PREREG is already frozen or an arm has launched, register this as
> the paired follow-on (P-C2b) with its own PREREG inheriting everything
> above, and run it after — do not overwrite a frozen registration."

P-C2's PREREG **is** frozen and both its arms **had** launched, so this is
the paired follow-on, registered separately. P-C2's registration stands
untouched.

**Why the tranche exists.** P-C2 discovered, after ARM H2 had run, that its
two arms were not running the same model configuration: the harness had
thinking OFF (`reasoning_effort: "none"`, inherited from P-C1) and the
sampler had it ON (no reasoning field, which is not the same as off).
Measured, same question bytes, one field apart: **9 712 completion tokens
and a 24 409-character reasoning payload vs 177 tokens and none**. P-C2b is
that confound removed.

---

## §2 — What is REUSED, unchanged

| input | source | how reuse is enforced |
|---|---|---|
| instance | Heilbronn N = 13, unit square | inherited |
| question bytes | P-C1's `question.py` | IMPORTED; digest asserted against `64b724c4…` by `preflight_pc2b.py` S1 |
| exact checker | P-C1's `checker.py` | IMPORTED by both the ladder and `arm_s_split.py` |
| in-run battery | P-C1's `criteria.py` | IMPORTED by the builder |
| registered floor | 0.005 | inherited |
| report-card instruments | W1 / W2 / W6, and P-C2's `report_card.py` | run unmodified; its self-check against P-C1's own root still binds |

---

## §3 — Reasoning ON, in both arms, through the SHIPPED protocol

**ARM H.** `reasoning` is REMOVED from every seat. Unset is not off
(`providers.reasoning_disabled`), so the model thinks. Removing it is also
the whole of the split wiring: `SPLIT_BUDGET_SEAT_PROTOCOL` defaults to
`"auto"`, which arms exactly the seats whose route says they think. No Config
knob, no code edit.

**ARM S.** `arm_s_split.py` makes the SAME two calls. It does not restate the
budgets — it **imports `deepreason.llm.split.plan_split`**, the shipped
planner, and calls it with the same mode, ceiling, extraction size and
provider. Two hand-written numbers would be two numbers to keep in agreement.

**The plan both arms get, computed by that planner and asserted by preflight
S5:**

    armed=True   B_r = 32 256   B_a = 512   extraction leg: thinking OFF
    B_r + B_a == 32 768 == the ceiling

**The completion cap STAYS at P-C1's 32 768**, and that is a decision with
evidence behind it, not an inherited default. P-C2's `CORRECTION.md`: at this
ceiling the split ran three seat calls and **all three extraction legs
returned valid, with a natural stop**. P-C2's Amendment 1 raised it to
100 000 on a misdiagnosis, which gave the reason leg 99 488 tokens and pushed
it past the socket timeout. 32 768 is also ARM S's existing cap, so holding
it is what makes "same effective caps" true.

**`timeout_s` rises 180 → 900 in BOTH arms.** Measured wall clock per seat
call at this ceiling, both legs: **737 s, 420 s, 460 s (mean 539 s)**. Every
one exceeds 180 s. `arm_s_split.py` carries the same 900, and preflight S5
asserts the two agree.

---

## §4 — The two arms

| field | ARM H | ARM S |
|---|---|---|
| model | `glm-5.2` | `glm-5.2` |
| reasoning | ON (field omitted) | ON (field omitted on the reason leg) |
| split | `llm/split.py`, auto | the same planner, imported |
| B_r / B_a | 32 256 / 512 | 32 256 / 512 |
| extraction leg | thinking off | thinking off |
| ceiling | 32 768 | 32 768 |
| timeout | 900 s | 900 s |
| temperature | route default | 1.0, explicit (P-C1's registered reason stands) |
| memory | full harness state | NONE — no sample sees another |
| scoring | in-run `criteria.py`, then offline `checker.py` | offline `checker.py` |
| machinery | solo, everything on, NO judges, discharge channel ON | none |

---

## §5 — Budget and admissibility

**200 000 tokens per arm**, measured as TOTAL LOGGED TOKENS. Reasoning tokens
count — they are paid tokens. ARM H's total comes from W6's committed flow
scan over the log; ARM S's is the sum of both legs' usage per sample.

**If the arms' measured totals are not within 5 % of each other, the
comparison is NOT quoted.**

### What 200 000 buys, registered BEFORE the run

At the measured ~44 000 tokens per seat call, 200 000 buys roughly **four to
five calls per arm**. ARM H2 needed **135 calls to reach cycle 11**.

**ARM H is therefore expected to terminate at cycle 0 or 1 on
`budget_exhausted`, and that is registered as the expectation, not discovered
as a disappointment.** P-C2b is a SYMMETRIC-CONDITIONS run: it establishes
that a reasoning-on comparison runs at all, on identical terms, and produces
the first numbers from one. It is not a depth run.

---

## §6 — THE REGISTERED VERDICT

Unchanged from P-C2 §6, stated verbatim:

> **Value is claimed if and only if `best_H > best_S`.**

`best_H == best_S` is NOT a margin. **But see §9**: at this depth the verdict
is reported as the registered arithmetic and is NOT read as the REBUILD
programme's kill-or-cure answer, which P-C2's own §6 owns.

---

## §7 — Report card

P-C2's `report_card.py`, run unmodified, against the same P-C1 baselines
(C1 construction validity, C2 invented-handle rate, C3 placebo-corrected
coupling, C4 operator-question budget share, C5 tokens per valid candidate).
Its self-check — reproducing every baseline on P-C1's own root — still binds
before any number is quoted. A metric whose instrument cannot run on a
4-call root is reported NOT MEASURED, with the reason, never estimated.

---

## §8 — The repeat

**One repeat pre-authorized**, separate `DEEPREASON_HOME` and root path.
Any single-run margin is quoted as a single-run margin with BOTH arms' spread
of valid scores stated.

---

## §9 — HONESTY LINES, pre-registered

1. **P-C2b does not replace P-C2's verdict, and does not rescue it.** P-C2's
   ARM H2 / ARM S2 comparison was registered and is reported as registered.
2. **P-C2b cannot answer the REBUILD kill-or-cure question at four calls per
   arm.** Whatever it shows, the programme's verdict needs depth this budget
   does not buy.
3. **It still cannot isolate one organ.** The discharge channel, the
   reference menus and the default-on evidence channels all move together,
   and there is no vacuous-critique arm — so a working critic cannot be told
   from argument-shaped text. F1's parked four-arm A/B remains the proof
   nothing here substitutes for.
4. **Symmetry is asserted at the REQUEST level, not the provider's internals.**
   S5 proves both arms send the same legs with the same budgets and the same
   reasoning settings. It cannot prove the provider treats two structurally
   identical requests identically.

---

## §10 — What P-C2b cannot settle

- One instance, one N, one model, one problem family.
- Capability-channel use is stochastic across identical runs; one attempt
  that misses a path is inconclusive for that path.
- No published record is consulted; ARM S is the comparator.
- **"Accepted" does not mean "true"** — though here acceptance is a
  computation over the candidate's own bytes.
- **P-C2's FINDING F-A is not closed.** The discharge channel is on because
  of a code default, not because a configuration can select it.
