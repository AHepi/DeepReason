# Reducing Token Burn Without Sacrificing the Epistemology

*Research report, 2026-07-05. Combines an empirical audit of our own
~2.5M-token run history (every number below is recomputed from the
replayable logs) with external research on provider mechanics. Angles are
ordered by measured leverage, not by how interesting they sound.*

---

## 0. The one chart that matters

Per-role economics across every logged live run:

| Role | Calls | Tokens | Share | Avg/call |
|---|---|---|---|---|
| conjecturer | 115 | 707,367 | **84%** | 6,151 |
| argumentative_critic | 72 | 103,905 | 12% | 1,443 |
| variator | 5 | 26,687 | 3% | 5,337 |
| judge | 1 | 1,717 | <1% | 1,717 |

And the anatomy of a single conjecturer call from the λ v2 run:
**12,646 tokens total, of which the visible JSON answer was ~55 tokens and
the prompt ~800.** The missing ~11,800 tokens — **93% of the call** — were
v4-pro's invisible reasoning trace.

So the token problem is not prompts, not schemas, not retries, not
logging. It is **one role's chain-of-thought**, which we never asked for
and never controlled. Everything else is a second-order optimization.

## 1. Angle: reasoning-token control (the dominant lever)

DeepSeek V4 exposes explicit thinking control at the API level: a
Non-think mode (`extra_body: {"thinking": {"type": "disabled"}}`), effort
levels (none/high/max), and a `budget_tokens` cap on the reasoning trace
([thinking modes](https://framia.converge.ai/page/en-US/news/deepseek-v4-thinking-modes),
[DataCamp tutorial](https://www.datacamp.com/tutorial/deepseek-v4-api-tutorial)).
We used none of it — every call ran at the default thinking level.

**Why this is epistemologically free:** the spec's D2 principle
(generator-agnostic) says γ's quality affects *efficiency*, never
*soundness*. A dumber conjecturer produces worse candidates; worse
candidates get refuted by programs and critics; the graph stays correct.
Reasoning depth on the conjecturer is a pure cost/quality dial with no
epistemic downside — and the harness *measures* the quality side
(valid-JSON rate, admission rate, survivor counts per token), so the dial
can be set empirically instead of by vibes.

Where reasoning plausibly *does* pay: tasks the model must internally
verify (the letter-counting oracle — v4-pro one-shot it precisely because
it could reason) and judge rulings. Policy, not blanket cuts:

- conjecturer on prose/skeleton tasks: **thinking disabled or low**
  (est. saves 60–75% of *total* system burn, from the 84% × 93% math)
- conjecturer on self-verifiable puzzle tasks: thinking on, `budget_tokens`
  capped (bounded, not open-ended)
- judge: thinking low + the trial guard's program screens as the real
  quality control — the guard already catches confabulated rulings
- variator/summarizer/spec-generator/defender: thinking disabled

## 2. Angle: role→model routing (pro → flash)

Current pricing ([DeepSeek docs](https://api-docs.deepseek.com/quick_start/pricing),
[cloudzero](https://www.cloudzero.com/blog/deepseek-pricing/),
[devtk](https://devtk.ai/en/blog/deepseek-api-pricing-guide-2026/)):
v4-flash at $0.14/$0.28 per MTok in/out versus v4-pro at $0.435/$0.87
(under the promotional 75% discount — note that discount is listed as
expiring, after which pro is $1.74/$3.48 and the gap becomes 12x). Flash
is 3x cheaper today and up to 12x cheaper at list price.

**The epistemologically principled procedure is "downgrade, then audit."**
This is where the harness earns its keep: it already contains the
instruments that certify whether a cheaper model degrades anything that
matters — valid-JSON rate per role, planted-flaw judge error rate,
paraphrase-flip rate, self-preference probes, trial-guard block rates.
Downgrading a role is safe *by measurement*, not by hope: switch the role
to flash, run the audit battery, keep the downgrade if the error rates
hold. No other part of the stack has to trust the substitution.

Suggested routing: flash for variator, summarizer, spec-generator,
defender, and one judge seat (it already is the alternate); pro only for
the conjecturer on hard tasks and the primary judge seat — pending audit
results, possibly flash everywhere.

## 3. Angle: prefix caching (free 10x on repeated input)

DeepSeek applies context caching automatically: input tokens matching a
previously seen prefix are billed at **1/10 the input price**
([pricing docs](https://api-docs.deepseek.com/quick_start/pricing),
[chat-deep.ai](https://chat-deep.ai/pricing/)). This rewards prompt
*ordering*, which we already half-do: every prompt starts with the stable
role template + JSON schema (~200–800 chars). To maximize hits, keep the
pack's stable sections (problem description, criteria) before the
volatile ones (neighbourhood, directives) — a pure reordering, zero
epistemic content. Caveat on magnitude: input is only a large cost share
*after* reasoning is tamed (today reasoning dwarfs it); post-Angle-1 this
becomes a first-order saving on the repeated-pack workload (30 cycles ×
near-identical packs).

## 4. Angle: call elimination (architecture)

- **The gate already saves money.** In λ v2, anti-relapse blocked 6–36
  failing candidates per grounded run *before* they could consume critic
  calls and successor work. Criticism avoided is tokens avoided — the
  epistemology and the economy point the same direction here.
- **Batch criticism**: one argumentative-critic call over K candidates
  instead of K calls (contract returns per-target cases; warrants remain
  per-target with their own ν — the *call* structure is not the
  epistemology, the warrant structure is). Saves most of the 12% critic
  share; prompt grows sublinearly since the criteria/context are shared.
- **Verbalized Sampling is already an amortization**: K candidates share
  one prompt and one reasoning session. Keep VS_K ≥ 2 for this reason
  alone.
- **Verdict reuse is already maximal-and-bounded**: battery-equivalence
  reuses refuters' work across equivalent candidates (that is what the
  gate *is*); anything more aggressive — reusing a judge ruling across
  non-equivalent targets — would be a warrant without a trial and is
  forbidden. This is a real floor, not an optimization opportunity.

## 5. Angle: prompt and output diet (real but small)

- The auto-generated JSON schema costs ~50–210 tokens per call
  (ConjecturerOutput: 836 chars). Hand-written compact contract
  descriptions would save ~2–3% of prompt spend. Worth doing during P6
  polish; irrelevant next to Angle 1.
- Completion caps: already learned the hard way — three separate live
  failures came from caps set *too low* (truncated skeletons, truncated
  judge prose, empty reasoning-exhausted content). Caps must be
  per-role-calibrated with the truncation-aware retry we built; they bound
  disasters, they are not a savings strategy. With thinking control
  (Angle 1), `budget_tokens` bounds the reasoning separately, which is the
  correct tool.
- Retry overhead is now small (187 attempts / 115 conjecturer calls,
  almost all from the pre-fix truncation era; current valid-JSON rate is
  ~100%).

## 6. Angle: scheduling and attention (spend γ-calls where they matter)

All attention-layer, all §0-clean:

- **Focus funding**: the Pareto frontier and unsolved-first selection
  already concentrate spend; `FOCUS_PROBLEM` (built for the λ v2
  experiment) generalizes to a configurable seed-problem share so
  derivative problems can't quietly eat the budget (the pilot's dilution
  cost ~90% of its γ-calls).
- **A brownout ladder**: mirror the capture ladder with budget triggers —
  as the meter approaches its ceiling, step down VS_K, pause lazy-HV
  spot-checks, defer reach sweeps and audits (all measures/attention,
  never verdicts). The run ends with a smaller *frontier*, not a corrupted
  one. This is the difference between degrading gracefully in attention
  space versus degrading in epistemic space, and the architecture makes
  the safe kind natural.

## 7. The floor: what must never be cut, and why it's cheap anyway

The epistemology's non-negotiables are almost all **deterministic and
free**: adjudication, replay, the event log, content addressing, the
anti-relapse gate's hash/battery stages, warrant/ν structure. Token cost
lives entirely in LLM calls, and of those, only a few are
epistemically load-bearing:

1. **Per-target warrants** — never batch a *verdict* across targets, only
   the call.
2. **The trial-guard screens** (order-swap, paraphrase spot-check,
   ensemble agreement) — these are warrant-validity conditions. They cost
   ~4–6 extra calls per rubric conviction; that is the price of a valid
   conviction, bounded per warrant, and `TRIAL_PARAPHRASE_N` is already
   the sanctioned knob for it.
3. **Judge ensemble ≥ 2 seats** — one seat may be cheap (it already is),
   but the second opinion is what makes disagreement detectable.
4. **The gate always runs** — it saves money anyway.

The meta-principle that falls out of this whole analysis: **in this
architecture, cost reduction and epistemic integrity are not in tension —
they are aligned, because every economy is generator-side or
attention-side, and the audit instruments certify each downgrade.** The
only genuinely dangerous cuts (skipping guards, reusing verdicts, letting
metrics gate acceptance) are also the ones §0 already forbids.

## 8. Ranked plan with estimates

| # | Action | Est. saving (vs today) | Effort | Epistemic risk |
|---|---|---|---|---|
| 1 | Per-role thinking control (disable/budget reasoning) | **60–75% of total** | ~20 lines (endpoint `extra_body`) + policy table | none (D2) — verify with report metrics |
| 2 | Route aux roles + one judge seat to v4-flash | 30–60% of what remains | config only | none if audit battery passes |
| 3 | Batch criticism contract | most of the critic's 12% share | contract + crit refactor | none (warrants stay per-target) |
| 4 | Stable-prefix pack ordering for cache hits | ~90% off repeated input | reorder render sections | none |
| 5 | Brownout ladder + seed-focus share | prevents waste, hard to est. | small scheduler addition | none (attention only) |
| 6 | Compact hand-written schemas | ~2–3% | tedious | none |

Compounded, a realistic **5–10x cost reduction per unit of epistemic
output** (surviving, verified artifacts per dollar) — with item 1 alone
delivering most of it, and every item verifiable by the harness's own
instruments before being trusted.

## Sources

- [DeepSeek API pricing docs](https://api-docs.deepseek.com/quick_start/pricing)
- [DeepSeek V4 thinking modes](https://framia.converge.ai/page/en-US/news/deepseek-v4-thinking-modes)
- [DataCamp: DeepSeek V4 API tutorial (thinking control)](https://www.datacamp.com/tutorial/deepseek-v4-api-tutorial)
- [CloudZero: DeepSeek pricing 2026](https://www.cloudzero.com/blog/deepseek-pricing/)
- [DevTk: DeepSeek API pricing guide 2026](https://devtk.ai/en/blog/deepseek-api-pricing-guide-2026/)
- [chat-deep.ai pricing overview](https://chat-deep.ai/pricing/)
- Internal: per-role economics and call anatomy recomputed from the
  replayable run directories (`runs/lambda_v2`, `runs/republic`,
  `runs/live`); pilot/definitive λ reports in `experiments/results/`.
