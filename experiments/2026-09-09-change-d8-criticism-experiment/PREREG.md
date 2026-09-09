# Pre-registration — does criticism, once connected and allowed to bite, make the harness's output materially better than the plain model?

Written 2026-09-09, in TRANCHE 1, **before any live call has been made from
this tranche against any provider**. Sealed by the sha256 in the commit message
of the commit that adds it. Nothing below may be edited after tranche 2's first
live call except by a dated, numbered amendment at the end saying what it
changes and why.

Authority: REQUEST.md R1–R42 (Amendments 1–3), SPEC.md and its five amendments,
and the operator's success law (CLAUDE.md, 2026-09-03): success is output
MATERIALLY BETTER than what the same model produces WITHOUT the harness on the
same question; correctness is irrelevant.

What motivates it, from the record rather than from an intuition
(`experiments/2026-09-08-audit-llm-capabilities/AUDIT_REPORT.md`): **0 of 196
model-written attacks were ever exposed to a later conjecture dispatch** in the
two roots examined (§2.3a); the harness has been measured against the plain
model four times and has not won once (§3.5); and every one of those four ran
with criticism disconnected or observe-only, so *"every statement in this report
about what criticism did or did not achieve should be read as a statement about
criticism that could not have achieved anything."* §5.1's third gap names this
experiment as the missing measurement.

---

## 0. What is fixed for every arm

| | |
|---|---|
| Question | The D8 question, from the frozen input `experiments/2026-09-05-change-mini-isolation-programme/runs/input-d8`, `problem.description` VERBATIM, never retyped. sha256 `e8e720d251b3cab2cddd548cb5064a74575404c8ae47f347f840faa6021a19b1`, 450 bytes. Criteria EMPTY, exactly as the frozen input carries them — the D8 standard lives in the judging instrument, not in the problem. |
| Model, every GENERATING seat, every arm | `qwen3.5:397b` at `https://ollama.com/v1`, reasoning OFF, completion cap 8192, context 131072 — the profile every committed live launch since 2026-09-03 uses. `reasoning: none` is load-bearing: without it this model spends its cap on hidden reasoning and returns empty content. CLAUDE.md's header names glm-5.2; the newest committed launches say `qwen3.5:397b`, and `PREREG_D8.md §0` already ruled the same conflict the same way. The stale header is PARKED (P2), not fixed. |
| **DISCLOSURE — the one place an arm is not the one model** | **ARM A's JUDGE role, and only that role, carries a two-seat CROSS-FAMILY ensemble: `qwen3.5:397b` (qwen) + `glm-5.2` (glm), taken verbatim from `experiments/2026-08-25-poietics-program/run-config.yaml`.** Every generating seat in ARM A — conjecturer, critic, defender, variator, summarizer, synthesizer, vision critic, property designer, thesis, grounding reviewer — is byte-identical to ARM C's, proven by route fingerprint on the compiled manifests (`proof/ARM_A_ROUTE_IDENTITY.txt`). CONSEQUENCE, stated before any reading: **`A vs C` measures granted authority WITH cross-family adjudication against no authority. No claim of a pure one-model comparison may be made from it.** Why it is unavoidable: on a one-model run no judge ensemble is obtainable at all, so a one-model ARM A would run, emit its notices and mint nothing — measuring nothing about authority. The operator ruled this road on 2026-09-09; `PARKED.md` P1 keeps the unreachable solo road open as its own defect. |
| Token ceiling per harness run | 500 000, the figure the operator set. |
| Launch road | The compiled-manifest road: build → `doctor --run-manifest --production-contracts` → `run --run-manifest`, the `pr1_run.sh` shape. NOT `deepreason reason`. DISCLOSED, with its reason: ARM V's stub-bound critic is unreachable on the managed path, where role endpoints are host-owned; if ARM C ran on one road and ARM V on another, `C vs V` would confound the critic's content with the launch road, and that is the one comparison this experiment exists to make. The operations-parity law of 2026-08-13 makes both roads the same run path. |
| Credential | One key, in the gitignored `experiments/2026-09-09-change-d8-criticism-experiment/env` (`.gitignore:50`), mode 600, read at launch, never committed and never echoed. |
| Instruments | Every one committed in tranche 1, before any live call: `tools/{arm0,build_manifest,critic_stub,make_vacuous_bank,check_vacuity,compose_result,essay_counterparts,judge_pairwise,judge_organiser,coupling_placebo,record_census,w2_census,w2_q5}.py`, `runs/config-{c,v,a}.yaml`, and `tests/`. |

### 0a. Two values that are RULES here and NUMBERS in tranche 2

Registered explicitly so a reader can tell a pre-registered rule from a
post-hoc choice without trusting anyone's memory.

- **ARM V's bank lengths.** The rule: the median and interquartile range of ARM
  C's own argumentative-critic objection lengths, over BOTH ARM C runs pooled,
  reported BEFORE the bank is generated. The bank is then minted by
  `tools/make_vacuous_bank.py` from those numbers and a fixed seed, and its
  digest recorded. The generator REFUSES to run without them: they have no
  defaults.
- **ARM 0's K.** The rule: the harness arms' own measured conjecturer-seat call
  count. `tools/arm0.py` requires K as an argument and has no default, so a
  stale 3 cannot stand in for a measurement. ARM 0 therefore runs LAST.

### 0b. A notice ARM A WILL carry that means nothing about whether it acts

Registered now because it is designed to be misread. ARM A's compile emits
`CALIBRATION_RECEIPT_REQUIRED: text prose status authority requires
CALIBRATION_RECEIPT`. It is a DISCLOSURE, not a suppression:
`authority.py::text_status_authority_issues` says so in its own docstring, the
receipt reaches neither `rules/crit.py`, nor `informal/trial.py`, nor the
scheduler, and **no `CALIBRATION_RECEIPT` value can ever clear it because
`calibration_receipt_is_verified` has no verifier**. A later reader finding this
notice on ARM A's record must not read it as the authority having been refused.

---

## 1. ARM 0 — the same model, no harness

One chat completion per sample: user message = the frozen problem description
verbatim, `max_tokens` 8192, reasoning off, no system prompt, no
`response_format` — a plain answer is what "without the harness" means. K
independent calls per §0a. Each call's request (key omitted), response, usage,
finish reason and wall time recorded. A transport failure retries with backoff
up to 4 attempts; a completed call whose content is empty or truncated is
recorded AS SUCH and kept, never replaced. Actual spend is reported; unused
allowance is reported and never padded.

## 2. ARM C — the harness as it ships

`runs/config-c.yaml`. `ARGUMENTATIVE_AUTHORITY=observe_only`, stated explicitly
rather than left to a default. The discharge channel at its shipped default
(`discharge-required.v1`), which is what puts open criticisms in the
conjecturer's binding block.

## 3. ARM V — the same, with CONTENTLESS criticism

`runs/config-v.yaml`. Identical to ARM C except the `argumentative_critic`
role's endpoint, which is a local loopback answering from a fixed bank
(`tools/critic_stub.py`, the shared `wheel_operational_smoke` fixture with one
thing overridden). Objections are filed with `attack=True`, exactly as ARM C's
are, so the two arms differ in CONTENT and not in ROUTE.

## 4. ARM A — the same, with authority GRANTED

`runs/config-a.yaml`. ARM C plus `ARGUMENTATIVE_AUTHORITY=trial_required`,
`ADJUDICATION_STATUS_AUTHORITY_ENABLED=true`, `JUDGE_SEATS_ENABLED=true`, and
the two-seat cross-family judge ensemble of §0's disclosure.
`JUDGE_SEATS_ENABLED` is REQUIRED, established by reading the gate rather than
assuming a default: `scheduler/scheduler.py:1450` skips the trial without it,
and `:2833` gates the audit path the same way. `rubric_policy` is not involved.

## 5. Repeats, and how the second run of an arm is taken

Every harness arm runs TWICE — six harness runs plus ARM 0. E78 is why: across
three paired runs with every input identical the control arm alone ranged
314 220 to 541 666 tokens and 4.71 to 6.70 of 15, "a run-to-run spread
comparable to every between-arm difference the experiment has reported."

The second run varies **NOTHING**. Run identity is question + budget + profile +
policy + dossier, and `RUN_ALREADY_STARTED` is raised against the first run's
ROOT. So the second run is taken by retiring the first — `git mv run-<id>
completed-epoch1-run-<id>`, **the rename committed first** — and relaunching
the identical configuration. Both roots are committed whole; the two share one
run id and are told apart by their committed directory names. This is stronger
than the declared nonce the brief offered: a nonce must be shown to move
nothing else, and varying nothing has nothing to show.

## 6. The judged unit

Each harness run's composed result (`tools/compose_result.py`), REFUSED unless
the run BOTH reached `state: completed` AND its `REPLAY_VALIDATION.json`
reports zero violations. Both refusals are the organiser tranche's, carried
over unchanged and mutation-proved (`proof/JUDGE_REFUSALS_RED.txt`). The second
is not defensive: that tranche's own ARM R reached `completed` over a record
carrying three violations, composition succeeded on it regardless, and without
the check its positions would have been scored as though the record stood.
ARM 0's units are its essays.

## 7. The instrument

`tools/judge_pairwise.py`. Blind pairwise forced choice, position swap, three
judges, ties refused in the prompt, units addressed by uuid4 with the keymap
unopened until the choices exist. The standard is the D8 criteria, READ from
`tools/judge_organiser.py` at run time rather than retyped, sha256
`fab3fde2f3a2000bd5f7415e7a7ae3be013fd8b83b4fd52395eef4b18327df28` — byte-identical
to the organiser tranche's, proven by `diff` of the whole file.

## 8. The five comparisons

`C vs 0`, `V vs 0`, **`C vs V`**, `A vs C`, `A vs 0`. C vs V is the one that
makes this a measurement of criticism rather than of a pipeline: its two arms
differ only in whether the objections carry content about their targets.

## 9. The decision rule

A judge's two readings of one pair are undone of their position and compared.
Both naming the same unit is a CONSISTENT preference; a choice that flips with
the order counts as NO PREFERENCE and is neither a win nor a loss, and stays in
the denominator. CONSISTENT-WIN SHARE ≥ 2/3 is **BETTER**, ≤ 1/3 is **WORSE**,
between is **NULL**. A failed arm is **INCONCLUSIVE**.

**Reported per pair of runs, never pooled.** The six harness runs are named run
by run and the instrument buckets by the treatment's own name, so no key exists
under which two runs of one arm could be summed. Mutation-proved.

## 10. The length rule, and a ceiling registered against it in advance

The 1.5× length rule applies to the verdict: a BETTER whose winning unit is
more than 1.5× the other's length is reported as **NULL (length-uncontrolled)**,
and the mirror for WORSE. The raw consistent-win share and
`verdict_before_length_rule` are reported BESIDE the verdict.

**Registered before any reading:** composed units in this corpus have run
21 396–46 518 characters against bare units of 5 875–7 985. If these are of the
same order, every ratio is roughly 3–6× and the rule will DOWNGRADE ANY BETTER
TO NULL before it is reported. So "MATERIALLY BETTER" is very likely unreachable
on the primary comparison, and that is a property of the sealed rule, not a
finding about the harness. **The rule is not changed to make the verdict
reachable.**

## 11. The secondary comparison the length rule cannot defeat

Units: each surviving position, emitted deterministically by `compose_result.py
--per-position` and byte-identical to its own paragraph inside the composed
unit (one renderer, called twice).

Counterpart: the bare essay's SENTENCES, in the essay's own order, taking the
PREFIX whose character count is closest to the position unit's; ties to the
shorter. The match is TWO-SIDED — a counterpart matches only when the ratio lies
within [1/1.5, 1.5], because a piece far shorter is as unmatched as one far
longer. Unmatched pairs are reported and excluded, never padded.

Recorded because it bears on how much to trust the rule: this rule was written
three times, and each correction came from its own self-test. Taking the first
paragraph prefix at or above the target overshot (ratios 1.73, 1.84, 1.94 —
every pair unmatched). Taking the closest paragraph prefix was still empty:
measured on the first committed essay, the paragraph prefixes are 358, 464,
469, 579, 741, 2212 … and not one lies in the [800, 1800] window a
1200-character position allows. Sentences are fine enough — six prefixes in
that window — and on the 36 real position units against the three committed
essays, **108 of 108 pairs fall inside the length rule**.

## 12. What is measured from the RECORD, per arm, beside the judging

- **Coupling with its placebo** (`tools/coupling_placebo.py`, W2's own
  instruments copied with one line changed each). For every criticism, whether
  the candidate AFTER it changed and whether the candidate BEFORE it changed —
  **and only the difference is reported as evidence.** Both operationalizations
  (mechanical, prose-quote) side by side, never averaged. The instrument
  re-derives W2's published table to the field.
- **The record census** (`tools/record_census.py`): attack edges minted;
  warrants split demonstrative / argumentative; refutations; evidence states
  open / supported / refuted / contested, read from `deepreason results --json`.

**Registered before ARM A runs:** across the 20 most criticism-heavy committed
roots in this repository there are **1 141 warrants and every one is
demonstrative — not one argumentative warrant has ever been minted here.** So
the census's argumentative column has never returned a non-zero value on any
real root, and a fixture positive control with a mutation proof ships for
exactly that reason (`proof/ARGUMENTATIVE_COLUMN_LIVE.txt`). **If ARM A
terminates cleanly with 0 argumentative warrants, that is a FINDING about
granted authority on this configuration — not a broken instrument and not a
failed arm.**

## 13. Predictions

Every one is a claim in `claims.json`, each with a falsifier and "not shown able
to fail" standing until its evidence exists.

1. Criticism REACHES the next candidate in ARM C: at least one conjecturer
   dispatch on a problem carrying an open criticism has a section-plan receipt
   naming `dr.open-criticisms`.
2. ARM V's objections reach it by the SAME route: same section, same priority,
   same disposition, differing only in text.
3. ARM A mints at least one ARGUMENTATIVE warrant. **Registered as the
   prediction most likely to be refuted**, and §12 says what a refutation means.
4. The placebo-corrected coupling difference is reported for every arm, and no
   coupling rate is reported without it.
5. No direction is predicted for any of the five comparisons. The primary
   comparison is expected to be NULLed by length (§10); no prediction is made
   about the secondary one.
6. Each harness run reaches a clean typed terminal — `completed` with
   `stop_reason` in {`max_cycles`, `budget_exhausted`}.

## 14. What this experiment cannot settle, registered in advance

One question; one model in every generating seat; two runs per arm against a
run-to-run spread comparable to every effect this corpus reports; judges of the
same family as the generating seats; a length rule expected to null the primary
comparison; ARM A's adjudication not one-model, per §0's disclosure. A NULL here
is a null on one question, not a general finding — and given §5's variance, a
BETTER would need replication before it meant much either.
