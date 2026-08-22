# Structured-output coercion and the scratchpad — external research note

Operator-supplied 2026-08-22, committed verbatim below the rule.
Claims and citations are EXTERNAL and unverified by this repository's
instruments; design intelligence, never evidence. Same standing as
the prior RESEARCH_ notes. The "you/your form" voice in the text is
the research window addressing a form design in conversation; read it
as addressing this harness's seat-facing schemas.

Why this note bites here: DeepReason COERCES model output into typed
envelopes and enum verdicts by construction. The headline result —
the same model fabricates at 0-2% in prose and 100% under a
required-field schema, because the format removed honesty's slot —
names a hazard in every seat-facing schema this harness ships, and
offers a mechanism for an operator observation already on the ledger:
judges that "prosecute without any discernable discrimination" may be
partly ARTIFACTS OF THE FORM — a verdict enum with no escape value is
a coerced verdict.

Consumption points:

- **The two-call tranche (queued behind the reach chain) absorbs
  this note.** Q7's coupling tax and this note's formatting tax are
  the same shape at two levels (budget, capacity), with the same
  fix: separate deliberation from emission. One tranche implements
  both: reason free at B_r, serialize/extract in a second call. The
  dose-response says heavy schemas in the emission call still tax;
  keep emission schemas light.
- **Schema hedge-impossibility audit, ready to route:** a mechanical
  pass over every seat-facing schema (envelopes, verdict enums,
  intake, capability proposals) flagging required closed-vocabulary
  fields and minimum-count arrays that lack an escape value — the
  paper's linter would have caught every 100%-fabrication cell.
  Read-only audit-shaped tranche; prompt on request.
- **Verdict enums gain a first-class structured refusal.** The
  harness already speaks typed stops, declines, and abstentions
  everywhere else — the disclose-never-die law at the output layer.
  Every seat-facing enum gets an insufficient_evidence road, and the
  two seat-profile numbers from the paper — CFR (Coerced Fabrication
  Rate) and EUR (Escape Utilization Rate) — join natural-stop and
  F_L as per-seat fields. EUR is the number that says whether the
  cheap fix works for a given model at all: open-weight models took
  the escape 0/200 even when it was in the sampler grammar.
- **The refusal tax, measured on our own record (cheap, read-only):**
  models that stay honest by VIOLATING the schema read as crashes.
  This harness records envelope rejections as typed failures with
  blobs — classifying the committed rejection blobs
  (fabrication-shaped vs refusal-shaped) says which currency our
  seats currently pay in. Candidate small measurement tranche.
- **The salted-probe design (CFR on our own tranches) is PARKED as a
  design decision, not adopted:** unanswerable-by-construction
  records salted into runs would make CFR code-scorable here — but
  wiring it into the qualification battery would move every
  qualification subject digest (frozen surface 5). If adopted, it is
  a standalone probe experiment first, qualification change never
  without the operator's word.
- **Scratchpad caveat, and what we already do:** written state is
  not used state (presence decodes at 1.000 even when causally
  inert). The prompt-level lever the note infers — committed fields
  must carry a span reference to the scratchpad line that licenses
  them — is the same design move P4 already shipped for evidence
  (QuotedEvidenceRefV1: quote REQUIRED when citing). External
  support for extending span-binding when a form field claims to
  derive from deliberation; untested beyond evidence citation, so an
  option, not an obligation.
- **Never forced function calling for judgment steps** (10% on
  MATH-Hard); prompt-level "do not fabricate" instructions are
  VOIDED by required schemas — enforcement lives in the schema's
  escape road, not the prompt.
- **Fabrication resistance is per-domain, per-seat:** it does not
  transfer across domains within one model, so any CFR/EUR
  measurement is stamped per seat AND per domain.

---

## Operator-supplied text, verbatim

This has a name, a benchmark, and a deterministic metric. Your
instinct was right, and the research says why — plus one caveat about
scratchpads you should know.

### The failure is caused by the form, not by the model

**PhantomFill** (arXiv 2607.20492) isolates it cleanly. Thirteen
models, same input, same question, **only the output format changes**
across three rungs: free prose → JSON with an escape value → JSON
with required fields. Inputs are unanswerable *by construction* (a
post with engagement counts but no reply text; a ticket whose call
was never transcribed), so scoring is code, not a judge.

The headline flip, GPT-5.5, n=40 per cell:

| Rung | Fabrication |
|---|---|
| Free prose | **2%** |
| JSON with escape value | **0%** |
| JSON with required fields | **100% (40/40)** |

The knowledge didn't change. The honesty didn't change until the
format removed its slot. **Ten of thirteen models hit 100%** under
required fields.

Four findings that bear directly on your form:

**Fabrication concentrates exactly where hedging is impossible.**
Field-level scoring on the support-ticket domain: GPT-5.5 fabricates
the required `customer_sentiment` enum **20 of 20** times, and
fabricates the free-string `representative_quote` **0 of 20** times —
it writes "no quote available" into the string instead. Arrays sit
between at 3/20. The paper's line: *strings can carry a hedge, enums
cannot*. A schema linter flagging every required closed-vocabulary
field lacking an escape value would have caught every 100% cell in
the paper.

**Escape hatches rescue only models that barely need them.** Given a
schema where every field admits `insufficient_evidence`, GPT-5.5 and
Opus take it nearly every time. All nine open-weight models fabricate
anyway at 60-100%; Sonnet 4.6 at 90%. The worst version: under
**grammar-constrained decoding**, with the escape as a legal token in
the sampler's own grammar, five open models fabricated at 100% and
took the escape **0 out of 200 trials**. It's not that they miss it.
They don't take it.

**The schema outranks the instruction.** An explicit "do not infer
sentiment" cuts free-text fabrication from 39% to 4%. Under a
required-field schema it does nothing for four of six models tested,
including GPT-5.5 (100% → 100%). Prompt-level guardrails are silently
voided when JSON mode is adopted.

**Resistance is trained and domain-contingent, not
scale-dependent.** Within one family: Haiku refuses 40/40, Sonnet
fabricates at 90%, Opus mostly refuses. And Sonnet fabricates a crowd
at 90% while refusing to fabricate a customer at 100% — same model,
same rung. Honesty under format pressure doesn't transfer across
domains, so it has to be measured per domain.

### Why the scratchpad works

**Capacity, Not Format** (2606.09410) gives the mechanism and
validates your fix.

The tax is capacity-dependent, not universal. On MATH-Hard: Sonnet
4.6 is neutral under JSON (88.7% vs 89.3% CoT); Haiku 4.5 drops
**−36.2pp** (88.7% → 52.5%); GPT-4o-mini drops **−28.0pp**. On easy
tasks everything is within ±4pp. The tax appears near the capability
boundary and vanishes at the floor.

Their information-matched prose control separates prompt length from
format. For Haiku: CoT 88.7% → detailed prose 80.7% (**prompt length
costs 8pp**) → JSON 52.5% (**format itself costs 28.2pp**, p<0.0001).
Same magnitude in XML, so it isn't JSON parsing.

The delayed-structure ablation — reason freely in phase 1, reformat
in phase 2 — **recovers most of the loss**: 80% for Haiku, 87% for
GPT-4o-mini. GPT-4o actually *exceeds* its own CoT baseline under
delayed prompting (58.3% vs 53.0%), suggesting the two-phase
structure adds scaffolding beyond mere delay.

Their reasoning-freedom spectrum on MATH-Hard, which is a ranking of
interface designs:

| Mechanism | Haiku | GPT-4o | GPT-4o-mini |
|---|---|---|---|
| CoT (free-form) | 87 | 56 | 60 |
| Two-round tool call | 86 | 51 | 59 |
| **Delayed structure (your scratchpad)** | 84 | 59 | 55 |
| API JSON mode | — | 51 | 51 |
| Instruction JSON (heavy schema) | 53 | 40 | 34 |
| **Forced function calling** | — | — | **10** |

And a dose-response on schema weight: Haiku goes 90.3% (light) →
86.0% (medium) → **55.3%** (heavy).

Their formulation — the **Reasoning–Formatting Separation
Principle** — is that structured-output interfaces should preserve an
unconstrained deliberation phase before requiring schema-compliant
output, and the tax scales as reasoning freedom decreases and task
demand approaches capacity.

**This is the coupling tax from Q7 at a different level.** There,
reasoning and answer competed for a token budget; here, reasoning and
serialization compete for generation capacity. Same shape, same fix:
separate the deliberation call from the emission call. You've now
independently rediscovered it twice, which is decent evidence you're
looking at something real.

### The caveat: a scratchpad can be decoration

2606.29522 is the one paper that should temper this. It separates
three things routinely conflated: whether a state is **written**,
whether it is **internally represented**, and whether the model
**computes from it**.

Their test: edit the internal representation of a written state while
leaving the visible scratchpad text fixed, then check whether the
next step follows the transition rule applied to the *edited* value.

- Models given **running-state supervision** use the scratchpad
  causally: 80% and 91% edited-branch agreement across two task
  variants, with move-swap selectivity +0.57/+0.68 and
  conflicting-continuation selectivity +0.59/+0.81 ruling out generic
  steering and copying. Replicates in a second model family.
- Pretrained and **final-answer-only controls stay near baseline** —
  random or orthogonal edits give ~0.02.
- Critically: the written state **decodes from the activation at
  1.000 in every variant**, including the ones that don't use it.
  Presence is not use. A probe that reads your scratchpad
  successfully tells you nothing.

The causal use came from *fine-tuning*, not prompting. So
`[INFERRED]`, not documented: at the prompt level, the closest
available lever is structural — make the form fields **reference the
scratchpad rather than sit beside it**, e.g. each committed field
must carry an index or verbatim span pointing at the scratchpad line
that licenses it. That forces the emission step to compute from the
scratchpad instead of alongside it, which is the prompt-level
analogue of running-state supervision. Untested in that form.

The broader faithfulness literature is worth a glance for the failure
mode you'd be guarding against — 2603.01437 (decoding and steering
pre-committed answers), 2607.16451 (commitment before reasoning),
2606.13603 (epiphenomenal CoT).

### What to change in the form

Ordered by severity:

1. **Audit every field for hedge-impossibility.** Required
   closed-vocabulary enums and minimum-count arrays are the
   fabrication sites. Free strings are comparatively safe because a
   disclaimer fits. This is a mechanical pass over your schema and it
   catches the worst cells.
2. **Add `insufficient_evidence` to every enum, and then measure
   whether your seats take it.** PhantomFill's two numbers — **CFR**
   (Coerced Fabrication Rate) and **EUR** (Escape Utilization Rate) —
   belong in your seat profiles alongside the natural-stop and F_L
   fields from Q7. EUR is the number that tells you whether the cheap
   fix works for your model.
3. **Adopt structured refusal as a first-class outcome.** Opus, faced
   with an impossible required schema, invented
   `{"status": "insufficient_data", "reason": ...}` — valid JSON,
   machine-readable, no lie. The paper proposes this as the training
   target and I'd propose it as your form's fourth outcome. It's the
   same design move as the no-verdict outcome for Rung 7 and the
   no-consensus outcome from the SPRT: **make "I can't fill this
   honestly" a legible, parseable state rather than something the
   pipeline can't represent.**
4. **Keep the scratchpad, and prefer two calls to one.** Delayed
   serialization in a separate emission call beat same-call
   scratchpad in their spectrum, and it composes with the Q7 fix.
5. **Never use forced function calling** for a step that requires
   judgment. 10% on MATH-Hard.
6. **Trim schema weight** wherever simultaneous emission is
   unavoidable. The dose-response is steep and redundant fields are
   pure cost.
7. **Don't rely on "do not fabricate" instructions.** They survive
   prose and die under a required schema.
8. **Measure per domain, not just per seat.** Sonnet at 90% on one
   domain and 0% on another, same rung, same construction.

### The probe worth building

PhantomFill's design is the thing to copy, and it slots straight into
your existing tranche machinery: construct records that are
**unanswerable by construction** — a premise with no stated support,
a conjecture with the criticism field deliberately emptied — and salt
them into tranches. Because absence is the ground truth, CFR is
scorable by code with no judge. That's a false-green probe aimed at
the form itself, and it's the only way you'll notice when a schema
change re-opens the hole.

One more finding worth carrying: **the refusal tax**. Haiku and Opus
achieve their low fabrication rates by *violating the schema* — prose
where JSON was demanded, 40/40 and 39/53. A production parser reads
that as a crash. Across the entire 13-model matrix, exactly one
configuration achieved 0% fabrication with 0% format violations: a
frontier model given an escape-hatch schema. Every other
configuration pays either in fake data or in broken pipelines. Worth
knowing which one you're currently paying in.
