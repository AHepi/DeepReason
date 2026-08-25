# Section 14 — Corrections, withdrawn claims, and measurements that were wrong

*This section exists because the project's own diagnosed failure mechanism is
**compression under narrative pressure** (`treadle0.5/FIELD_REPORTS.md`, header). Every
claim below was made in good faith, recorded, and later found wrong. They are kept rather
than deleted: the record of how a measurement went wrong is worth more than the measurement.*

---

## 14.1 Withdrawn quantitative claims about test coverage

### "6/6 decisions held" — WITHDRAWN

**Made:** 2026-08-25, first seeded run of the mutation probe.
**Claimed:** six mutations, six caught, six decisions held.
**Why it was worthless:** all six were edits *already proved by hand that same day*. It
measured only that six known-good guards work. It said nothing about the other twenty
decisions or the other 12,000 lines of engine.

### "59 caught, 3 survived" — WITHDRAWN, the instrument lying about itself

**Made:** 2026-08-25, first full 62-mutation run.
**Actual mechanism of the error:** the probe applies a mutation by replacing `old` with
`new`. The registry's own applicability test (`test_every_mutation_still_applies_to_this_tree`)
then asked whether every registered `old` still appears in the tree, found that one did not
— *because the probe had just replaced it* — and failed the suite. So **every non-additive
mutation was recorded CAUGHT** whether or not any real guard fired.

**Why the error was nearly invisible:** the three survivors that did surface were the three
whose `new` text *contains* its `old` — purely additive edits, the one shape that can slip
past its own defusal.

**The dangerous direction was not noise but masking:** a mutation that no guard catches was
still reported CAUGHT.

**How it was caught:** by reading the *attribution line* — which test caught each mutation —
rather than the verdict. Three mutations were attributed to the registry's own check.

**Corrected result:** 16 caught, 46 survived.

### "13 survivors in 26" — superseded, not wrong

An in-tree partial run reached mutation 26 before being killed. Its verdicts agree exactly
with the final sandboxed run on all 26 shared mutations. The final rate was worse because
the survivor density rises later in the registry, not because the earlier run was faulty.

---

## 14.2 Measurements that were narrower than stated

### The RT-1 blast radius was a lower bound presented as a measurement

**Claimed:** taking `RuleRecord.blocker_closure` as `required` would invalidate **22
packages**.
**Actual on implementation:** **346 failing tests**.
**Source:** `docs/RT1_IMPLEMENTATION_FINDINGS_V0.1.md`.
**Mechanism:** the measurement counted *packages built by no-argument fixture builders*. It
could not count packages constructed inline inside test bodies, nor the second-order effects
on tests that assert on compiled output.
**Standing lesson:** a measurement instrument that enumerates a *reachable* subset reports a
lower bound; saying so is part of reporting the number.

### "The hash covers the registry" — narrowed to "covers `registry_id`"

Conformance case 16 originally claimed the package hash bound the registry. It binds the
registry **id string** only. Registry *content* — including the discharge compatibility
table that can change an admitted package's status — is not covered. This narrowing
propagated into REG-1's stated limit.

---

## 14.3 Claims about prose that two independent reviewers refused

### REG-1's "consequence, not the reason" — WITHDRAWN

**The sentence as written:**

> That zero-migration outcome is a consequence of the convention, not the reason for it —
> the alternative convention … would force `pff-core+empirical/1` and change every package
> hash, **which is the cost this reading was chosen to avoid.**

The sentence denies in its first clause what it concedes in its last.

- `kimi-k2.7-code`: "largely rhetorical."
- `deepseek-v4-pro:0813`: "not real", quoting the contradiction back verbatim.

**Corrected:** the denial is withdrawn in `docs/ACCEPTANCE_V0.1.md`. Of the two conventions
available, the cheaper one was chosen partly *because* it was cheaper. The record now states
what that does and does not license.

### "The version already encoded in the id" — overstated

`deepseek-v4-pro:0813`: the mechanism "does not establish that the id was already a version
carrier." Correct — it imposes a convention and enforces it going forward. The docstring now
says *imposed* rather than *already encoded*.

### The content-edit hole was in the code but not plainly in the record

`deepseek-v4-pro:0813`, re-reading after the above correction: the acceptance record "does
not say it plainly enough." An author who edits the discharge compatibility table without
bumping `registry.version` defeats the check completely, **today**, not only in some future
separately-published world. Now stated plainly.

---

## 14.4 A comment that made a false claim about its own guard

`src/poietics/explain/report.py`, beside `_CYCLE_SETTLING_EDGE_KINDS`:

> Written as data rather than as a branch so the decision can be READ and guarded —
> `tests/test_accepted_no_change_decisions.py` holds it, and **a silent addition here fails
> there.**

**The claim was false.** Mutation `contrary-to-collapses-cycles` adds an `elif` branch
*beside* the frozenset, in the only place that consults cycle-forming relations, leaving the
frozenset untouched. All 691 tests passed. The data guard sees a declaration; the mutation
added behaviour next to it.

Fixed by a **behavioural** test that runs `_collapse_cycles` and asserts a mutual contrary
pair is not collapsed, with a positive control showing the same shape under `BLOCKS` *is*.

---

## 14.5 A guard that checked declared data and missed added behaviour

Two mutations survived 691 tests by adding public members:

- `DiscernmentReport.accepted` — a `@property` returning `self.status is Status.LIVE`.
- `Evaluation.holds(atom)` — returning `atom in self.live`.

Both publish exactly the inference the specification forbids. The existing guard inspected
`DiscernmentReport.__dataclass_fields__`; **a property is not a dataclass field**, and a
method is not either.

Fixed by checking the **public surface** — every public name any engine module defines —
scoped to modules where a `Status` is actually reachable.

### A correction *to that fix*, before it shipped

The first vocabulary swept up `registry.py`'s six `accepts(...)` methods — a grade policy
accepting a grade, a value type accepting a value. Those are **admission questions about a
contract**, in a module that cannot reach a `Status` at all. That is the "forbidden list
growing into a style guide" failure the file's own control test now watches for. The rule was
re-scoped: the strict vocabulary applies exactly where the forbidden inference is *possible*.

---

## 14.6 A review packet defect misread as a code finding

The first `accepted-rt` review returned **MISSING** on its two most load-bearing rows. Neither
was a claim about the code: `model.py` and the challenge-kind constants simply were not in the
packet, and the reviewer said so rather than guessing. Evidence supplied, same question asked
again, both rows CONFORM.

**The instructive disagreement:** on a DF row, `glm-5.2` answered CONFORMS from a packet that
did not contain the evidence, reasoning from a role name. `deepseek-v4-pro:0813` returned
MISSING and declined to. **deepseek was right and glm was over-claiming.** Recorded because a
disagreement between reviewers is worth more than either verdict.

---

## 14.7 A correction to a coverage critic

The mutation coverage critic reported the **adapter profile** as carried by no mutation. It
is carried by `adapter-temperature-sampling`, which predates the critic and was outside the
material the critic was shown. **A packet error by the author, not a reasoning error by the
critic.** Struck rather than deleted in `zoo/mutations/BACKLOG.md`.

---

## 14.8 Instrument failures during this cycle

| failure | mechanism | fix |
|---|---|---|
| Probe left a planted defect in the working tree | 10-minute command timeout killed it mid-mutation; `finally` covers exceptions, not signals | SIGTERM/SIGINT/SIGHUP handlers that restore and re-raise |
| Probe left a planted defect again | SIGKILL when the process group was reaped — no handler runs | Run in a **throwaway copy**; the working tree is never mutated |
| Probe reported false CAUGHTs | Its own applicability check tripped over its own edit | Check stands down while a mutation is in flight |
| A `pgrep` waiter never terminated | The waiter's own command line contained the pattern it was grepping for — it waited on itself | Killed; pattern made specific |
| Two dead extraction patterns survived for cycles | The consistency-packet build checked per-*document*, not per-*pattern* | FR-28: assert on the smallest declared unit, never the container |
| A review returned EMPTY three times at `finish=length` | Diagnosed initially as an oversized packet; actually an **unbounded question** with no stopping rule | FR-27: rebuilt as 11 numbered bounded pairs |
| A consistency audit returned a false CONTRADICT | A fixed 200-character excerpt window cut four lines before the document's own qualification | FR-29: a qualification is part of the claim |

---

## 14.9 Two errata raised against the specification, not fixed in it

The core specification is byte-pinned by SHA-256 and **nothing in the repository edits it**.
Two conclusions that a specification sentence should change are recorded as errata to raise
upstream (`docs/SPEC_ERRATA_V0.1.md`):

- **E-1** — the closed-negative-literal example, printed inside the *Package model* section,
  names a `__pff__:` atom where a package record is required. `validate_package` refuses it
  with `unresolved_reference`. The implementation keeps the validator strict and reads the
  example as compiled form.
- **E-2** — "The implementation SHALL be split into the following modules" followed by a
  table of eleven. Sixteen exist. Two independent reviewers, each asked to argue *both*
  readings before answering, both chose the partition reading and both answered DEVIATES, by
  different arguments.

**A caveat recorded against the project's own evidence:** both reviewers were told the extra
module was *one*. It is *five*. The argument is about whether the enumeration is closed
rather than about how many sit outside it, but the record says what they were shown.

The distinction drawn: an **erratum** is where the specification's text is internally
inconsistent or misleading; a **divergence** is where the implementation makes a choice the
specification permits or does not reach. Only the first belongs upstream.
