# Pre-registration D8 — the measure (SPEC S12, C6)

Written 2026-09-06, BEFORE any arm has been launched and before any call has
been made against the provider from this tranche. Sealed by the sha256 in the
commit message of the commit that adds it. Nothing below may be edited after a
launch except by a dated, numbered amendment at the end that says what it
changes and why.

Authority: REQUEST.md (R1–R16; Amendment 3 "go for it jack!"), SPEC.md S12,
CHECKLIST.md steps 52–57, and the operator's success law (CLAUDE.md,
2026-09-03): success is output MATERIALLY BETTER than what the same model
produces WITHOUT the harness on the same question; correctness is irrelevant.

The programme's own ruling that binds the measure (SPEC §Q-A, Amendment 1):
within mini criticism overturns nothing, so this measure compares
BETTER-CRITICISED conjectures against a single call — never eliminated ones.
That is the weaker, honest first result the operator chose knowingly.

---

## 0. What is fixed for both arms

| | |
|---|---|
| Model, every call, every seat, every judge | `qwen3.5:397b` at `https://ollama.com/v1`, reasoning OFF (`reasoning: {"effort": "none"}`), completion cap 8192, context 131072 — the profile every committed live launch since 2026-09-03 uses (`experiments/2026-09-03-change-provenance-history-channel/runs/setup_and_qualify.sh`), and the model the copied judge panel already scores with. CLAUDE.md's header names glm-5.2 as the current provider model; the newest committed launches and the judging protocol say qwen3.5:397b, and comparability with the copied panel decides it. |
| Standard input | the seed question of the history-channel tranche, `experiments/2026-09-03-change-provenance-history-channel/QUESTION.txt`, sha256 `626e8f780bb7838a2e244ec8df0492ef565cff7495e5d18ed080a622d14f1c9c`, chosen so the copied judging criteria (written for exactly this question) transfer verbatim. Frozen once as the STANDARD input (R12) with `deepreason input freeze`, problem id `question-corroboration-d8`, criteria `[]` (an empty list is accepted: probed 2026-09-06, rc=0, `run_input_digest 63d2a653…` on a scratch root). Both arms receive the problem description text and nothing else of substance: ARM 0 as the whole user message; ARM M as the `mini.problem` section, whose header line and the seat directives ARE the harness under test. |
| Provider reasoning field | Both arms send `"reasoning": {"effort": "none"}`. This is load-bearing, not tidy: without it this model spends its completion cap on hidden reasoning and returns empty content (measured in `judge.py`, 2026-09-04). FINDING, recorded here before launch: mini's transport (`mini/minireason/call.py::HttpEndpoint.complete`) builds its request from `model`, `messages`, `temperature`, `max_tokens`, `response_format` only, and the managed shallow entry (`src/deepreason/shallow.py::_endpoint`) forwards `endpoint`, `model_id`, the key and `maximum_completion_tokens` — the profile's `reasoning` setting is written by `deepreason setup` and never reaches a mini call. That is a defect found mid-change: PARKED as P10, not fixed here. ARM M therefore runs through a tranche-local driver (`d8/armM_driver.py`) that replaces the shallow entry's endpoint factory with a subclass of the same `HttpEndpoint` adding exactly that one field to the request body; everything else on the managed path is unchanged. No production code changes for the measure. |
| Temperature | provider default in both arms (mini's transport sends none; ARM 0 sends none). |
| Credential | one key, in the gitignored `experiments/…/env` (`.gitignore:50`), read at launch by `set -a; . env; set +a`; never committed, never quoted. |
| Instruments | `d8/arm0.py`, `d8/armM.sh` + `d8/armM_driver.py`, `d8/probe_transport.py`, `d8/judge_d8.py`, `d8/analyse_d8.py` — all committed in the same commit as this document, before any launch. |
| Budget | ARM 0 ≤ ~30k tokens; ARM M ≤ 400 000 tokens (its own typed ceiling); judging ≤ ~250k. Well under 1 M in total. |

---

## 1. ARM 0 — the same model, no harness

**What one sample is.** ONE chat completion: user message = the frozen problem
description, verbatim; `max_tokens` 8192; reasoning off; no `response_format`
(a plain answer is what "without the harness" means); no system prompt.

**How many samples.** K = 3 independent calls, one per ARM M cycle, so the
single-call arm is a distribution rather than a point and its conjecturer-side
spend is matched to ARM M's conjecturer seat call for call. Each of the three
is, on its own, exactly "one call, no harness"; nothing links them.

**What is recorded**, per call, in `d8/arm0/call-<k>.json`: the request body
(key omitted), the full response JSON, `usage`, `finish_reason`, wall time,
transport attempts. `d8/arm0/ARM0_RESULT.json` summarises all three.

**Typed terminal.** A call is COMPLETE when the response carries a
`finish_reason` and non-empty `content`. A transport failure (HTTP 5xx/429,
timeout) is retried with backoff up to 4 attempts, as `judge.py` does — that is
transport, not a re-run for a number. A completed call whose content is empty
or whose `finish_reason` is `length` is recorded AS SUCH and kept; it is not
replaced.

---

## 2. ARM M — `mini.flow.isolation.v1`

**Launch.** `d8/armM.sh`: `DEEPREASON_HOME=<tranche>/runs/home-m`;
`deepreason setup` with the profile line in §0; the standard input frozen into
`<tranche>/runs/input-d8`; `DEEPREASON_MINI_FLOW=mini.flow.isolation.v1`;
then `d8/armM_driver.py`, which calls the managed shallow entry
`run_shallow_question(run_input_root=…, cycles=3, token_budget=400000)` with
the endpoint override of §0. No qualification battery: the shallow path never
consults it. Detached (`setsid nohup … & disown`), the snapshot loop armed.

**Shape.** Model profile `compact` (mini's default): `vs_k` = 4 candidates
requested per conjecture call; prompt clip 4 800 characters, the everything
section handed 60 % of it by `brief_share`. Per cycle: 1 conjecture call →
up to 4 admitted `mini.conjecture.v1` artifacts → 1 critic call per admitted
artifact this cycle → 1 commitment call per admitted artifact this cycle. Three
cycles: at most 3 + 12 + 12 = 27 calls. Both commitment channels OFF with the
typed warning in the record (the flow declares it). Criticism overturns
nothing: `refuted` is expected 0 and reported either way.

**What is recorded.** The mini root under
`<tranche>/runs/home-m/shallow-runs/shallow-<id>/` (`log.jsonl`, `blobs/`,
`run-manifest.json`, `run-input.json`), committed after the run; the shallow
result JSON to `d8/armM/ARMM_RESULT.json`; the driver log.

**Typed terminal.** ARM M is COMPLETE when all of: the shallow result JSON has
`completed: true`; `summary.stop` is one of the loop's typed stops
(`max-cycles`, `queue-exhausted`, `budget` — the loop's own names; a budget stop is a clean
typed stop and its record is judged like any other); `summary.meter_equals_log`
is true; `verify_root(root)` reports 0 violations; and `replay(root).digest()`
equals the live session digest — the same five instruments T6 S10.5 ran.
`deepreason results <root>` on a mini root prints typed absences
(`NO_RUN_STATUS_JSON`, `NO_REPLAY_VALIDATION_JSON`, …) because a shallow root
writes neither file; that output is pasted as what it is and is NOT the
terminal — the five instruments above are. An `endpoint-error` stop
(`completed: false`) is a FAILED arm, recorded as failed; it is not relaunched
to get a number (one relaunch is allowed ONLY if the failure is a transport
death before cycle 1 completed — no conjecture artifact in the record — and the
relaunch is disclosed with the dead root kept).

---

## 3. Judging — the copied protocol, unchanged

Protocol: `experiments/2026-09-03-change-provenance-history-channel/
JUDGING_PREREG_COPIED.md`, sha256
`ef3d4f95d68c6777f19a3b8dc4ce684ed2d2ecae56756926c116e026b7444aef`, executed
by `d8/judge_d8.py`, a copy of that tranche's `judge.py` whose ONLY changes are
the harvest (which arms, and where their candidates live) and the paths. The
five criteria, the 0–3 scoring, the median-of-three aggregation, the contested
flag (>4 of 15 spread), the blinding, the keymap-shut-until-scored rule, the
judge model and its `reasoning: none`, `max_tokens` 900, the backoff and the
batched runner are adopted verbatim.

**The judged unit is a text that answers the question.**
- ARM 0: each call's `content`, whole — 3 candidates.
- ARM M: each `mini.conjecture.v1` artifact admitted to the record (the
  candidate's `content` prose; provenance role `conjecturer`; seed artifacts
  excluded) — at most 12 candidates. Criticism and commitment-proposal RECORDS
  are NOT judged: the criteria score an answer to the question, and the
  programme's ruling makes those records content shown to later seats, not
  answers. They are reported (counts, lengths, spend) and quoted in RESULTS.md,
  and their effect, if any, is visible only through the later cycles'
  conjectures — which is exactly the "better-criticised conjectures" the SPEC
  says this measure can see.

**Blinding.** `d8/blind/candidates.jsonl` carries `{bid, text}` only, `bid` a
uuid4, rows sorted by `bid`; `d8/blind/keymap.json` is not opened until
`d8/blind/scores.json` exists (`reveal` refuses otherwise). Nothing per-arm is
written before reveal.

**Same-model judging** (the candidates' model judges them) is a stated
residue, as it was in the source tranche: self-preference bias has no live
measurement in this repo; both arms are exposed to it equally.

---

## 4. Length held constant — the control that decides the verdict

The panel pays for length: Spearman ρ = +0.797, R² = 0.589 between candidate
characters and judged total (`RESULTS_M1_QUALITY.md` §3.4), and the
replication found "indistinguishable once length is held constant"
(`RESULTS_M1_REPLICATION.md`). A relaxed, unbounded conjecture form is the
change most likely to buy length and be scored for it; a single essay-length
call is the arm most likely to be long. So the raw gap is reported but does
not decide anything.

`d8/analyse_d8.py` (a port of the committed `analyse_length_bias.py`, same
estimators, seed 20260906) reports, in this order:

1. Per arm: n, mean, median, min, max characters, and the length quintile
   boundaries of the pooled candidates.
2. Pooled Spearman ρ(chars, median total) and the `total ~ log(chars)` fit.
3. The raw gap: mean(M) − mean(0) of the 0–15 medians, permutation p
   (100 000 label shuffles).
4. The length-adjusted gap: the arm coefficient of
   `total ~ 1 + log(chars) + [arm = M]`, permutation p over 20 000 shuffles.
5. The quintile-held gap over the pooled quintiles in which BOTH arms have at
   least one candidate, with the number of such strata stated. If no stratum
   holds both arms, this estimator is UNDEFINED and is reported as such.

**Decision rule, fixed now.**
- **M BETTER** iff the raw gap > 0, the length-adjusted coefficient > 0 with
  p < 0.05, and the quintile-held gap is > 0 or undefined.
- **M WORSE** iff the mirror image (all three ≤ 0, adjusted p < 0.05).
- **INDISTINGUISHABLE** iff usable counts meet the floor below and neither
  rule fires.
- **INCONCLUSIVE** iff fewer than 8 usable ARM M candidates, or fewer than 2
  usable ARM 0 candidates, or the length distributions do not overlap (no
  pooled quintile holds both arms) — because then the adjusted term is an
  extrapolation and the stratified term does not exist.

"Usable" = scored by at least one judge. The verdict names the rule that fired.

**Predictions, registered before launch.**
- **Quality: NO DIRECTION PREDICTED.** Whether mini's relaxed, blinded,
  criticism-shown flow yields conjectures the panel scores higher than a single
  call is exactly what nobody knows; registering a direction would invent a
  prior (the source tranche's own words, adopted).
- **Length, directional:** ARM 0's candidates are LONGER (mean characters)
  than ARM M's — one call writes one essay; a conjecture call splits its
  completion across four candidates.
- **Cost, directional:** ARM M's TOTAL tokens exceed 3 × ARM 0's total (the
  critic and commitment seats are pure added spend), while ARM M's
  conjecturer-seat tokens are within a factor of 2 of ARM 0's total.
- **Operational, not success:** ARM M reaches `max-cycles` at cycle 3 with
  `refuted == 0`, `verify_root` clean, replay digest equal.

---

## 5. Per-seat spend — reported, never inferred

From ARM M's record, every event carrying an `llm` receipt is attributed:

| seat | how it is recognised in the record |
|---|---|
| conjecturer | a Rule event that registers `mini.conjecture.v1` artifacts, or a Measure event marked `all-blocked` / `workflow-conjecture-call` — the conjecture road's receipts |
| critic | a Measure event whose inputs begin `mini:record`, `kind:mini.criticism.v1` |
| commitment | a Measure event whose inputs begin `mini:record`, `kind:mini.commitment-proposal.v1` |
| stage-empty / dropped | `mini:stage-empty` (stage id named) and `dropped-call` receipts — listed on their own row, never folded into a seat |

Columns: calls, tokens (`llm.tokens`, the record's own field), share of the
run. Cross-check, required: the rows sum to `summary.logged_tokens_this_run`
and `meter_equals_log` is true. ARM 0's row is the sum of its three `usage`
totals. `d8/analyse_d8.py` prints the table; RESULTS.md pastes it.

---

## 6. Order of operations, and what counts as "no arm has run"

1. This document and the six instruments committed (sha in the message).
2. Step 53: `python -u scripts/cycle_soak.py --case epoch3` — the solo,
   same-provider-shape case of the full harness. DISCLOSED NOW: every soak
   case drives the MANAGED FULL-HARNESS path; none drives mini, so the soak
   proves the box and the install, not ARM M's path. ARM M's own offline
   proof is re-run beside it: the T6 isolation run against the stub
   (`verify_root` 0, replay digest equal), and `d8/probe_transport.py` — ONE
   throwaway call ("return the JSON object {\"ok\": true}") through the §0
   endpoint override to show the reasoning field is honoured and content
   is non-empty. The probe is not an arm: different prompt, nothing judged,
   its output recorded in `d8/PROBE.txt`.
3. Step 54: ARM 0, then ARM M, detached, snapshot loop armed. Roots and
   results committed as they complete.
4. Step 55: harvest → score (batched) → reveal; `analyse_d8.py`; RESULTS.md.
5. Step 56: the verdict by §4's rule, its residue, and the sealed sha of
   `d8/blind/scores.json`.

**No arm is re-run to get a number.** The one exception is §2's disclosed
pre-cycle-1 transport death. An inconclusive result is recorded as
inconclusive (C6; CLAUDE.md Conventions).

## 7. Residue stated in advance

- Same-model judging; self-preference and verbosity bias unmeasured beyond §4.
- n is small (3 vs ≤12): the floor in §4 is a floor, not power.
- ARM M is judged on conjectures only; whatever the critic and commitment
  seats are worth is visible here only through cycles 2–3's conjectures.
- Mini's reasoning-field gap (P10) means ARM M ran through an override, not
  the bare managed path; the override adds one request field and nothing else,
  and its class is in the committed driver.
- The compact profile's 4 800-character clip bounds what later seats are
  shown; `mini:brief-clipped` and `WITHHELD UNDER RULE` notices are counted
  and reported.
