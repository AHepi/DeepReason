# Spec for: does criticism, once connected and allowed to bite, make the harness's output materially better than the plain model?

Traces: every item cites R/C numbers from REQUEST.md. Untraceable items are bugs.
Shape: **DESIGN-AND-STOP** for ARM A (R10/R11/R30 fire), design-complete for
ARMs 0, C and V. Measurements are pasted commands, not recall.

---

## The one-sentence outcome of this phase

Three of the four arms are buildable today with nothing under `src/` or `mini/`
touched; **ARM A as the brief words it cannot bite** — a granted-authority
trial on a one-model run is refused at three independent gates and the map
already records the mode as parked dead weight — so R11's and R30's stops fire
and the operator's words are needed on which road ARM A takes.

---

## Measurements

Every load-bearing claim below is one of these. Commands were run on this
branch head at `origin/main` (38707495a).

**M1 — the two ARM A switches DO reach a rebuilt run configuration.** R11's
named worry (the 2026-08-28 audit's P10, five switches silently reverted by the
manifest echo) does NOT apply to either switch.

    python3 -c "from deepreason.run_manifest import _unconditionally_dropped_config_fields as d, _versioned_source_config_data as v; from deepreason.config import Config; e=set(v(Config(),6)); [print(f,'| in echo:',f in e,'| carried-by-notice:',f in d()) for f in ('ARGUMENTATIVE_AUTHORITY','ADJUDICATION_STATUS_AUTHORITY_ENABLED','DISCHARGE_POLICY')]"
    ARGUMENTATIVE_AUTHORITY | in echo: True | carried-by-notice: False
    ADJUDICATION_STATUS_AUTHORITY_ENABLED | in echo: False | carried-by-notice: True
    DISCHARGE_POLICY | in echo: False | carried-by-notice: True

and the round trip, compile -> echo -> `config_from_run_manifest`:

    echo ARGUMENTATIVE_AUTHORITY   : single_family_trial
    echo ADJUDICATION_..._ENABLED  : <absent>
    rebuilt ARGUMENTATIVE_AUTHORITY: single_family_trial
    rebuilt ADJUDICATION gate      : True
    rebuilt LEGACY_CRITICISM       : True
    manifest criticism_policy      : None
    _authority(rebuilt)            : single_family_trial
    _resolve_authority(non-policy) : single_family_trial
    --- notices mentioning the gate ---
    {"code": "ENGINE_CONFIG_FIELD_NOT_CARRIED", "message": "ADJUDICATION_STATUS_AUTHORITY_ENABLED=True is not carried by this manifest's engine config and is restored at run time from this notice", "pointer": "/engine_config/ADJUDICATION_STATUS_AUTHORITY_ENABLED", "resolution": null, "value": "true"}

That last line IS the typed warning R10 requires captured on the record.
Supports: R10's switch half, and the resolution of Q1.

**M2 — the operator-facing configuration road carries both switches, and the
GUARD that proves it works.** A YAML file passed to `deepreason --config`:

    deepreason --config <cfg>.yaml config | grep -iE "PACK_TOKEN_BUDGET|ARGUMENTATIVE_AUTHORITY|ADJUDICATION_STATUS"
    ADJUDICATION_STATUS_AUTHORITY_ENABLED: true
    ARGUMENTATIVE_AUTHORITY: single_family_trial
    PACK_TOKEN_BUDGET: 24000

Supports: the launch-time guard every ladder must run before spending a
battery (the organiser tranche's `setup_and_qualify.sh` pattern, R25's sibling).

**M3 — a per-role endpoint is HOST-OWNED on the managed `deepreason reason`
path, so ARM V's stub-bound critic cannot be reached there.** From
`src/deepreason/preparation.py:376-380`, verbatim:

> The seven values the HOST owns on this path, whatever the operator's
> configuration says: the provider profile holds the credential and the
> endpoint, and the seat-binding mechanism owns per-role divergence, so a
> configuration file may never redirect a managed run to another endpoint.

`roles` is in that owned set. Supports: the rejection of Option V-b below.

**M4 — no `--seat` group covers the critic**, so the supported per-role
divergence mechanism cannot isolate `argumentative_critic`
(`src/deepreason/seat_bindings.py:51-60`):

    GROUP_ROLES = {"conjecture": {"conjecturer","variator"},
                   "coder": {"property_designer","encoder"},
                   "scratch": {"conjecturer","synthesizer","summarizer"}}
    GROUP_ALIASES = {"simulation": "conjecture"}

The one road that does reach the critic — `--criticism-seat` /
`resolve_criticism_seats` — is gated on `SCHOOL_SEATS_ENABLED` **and** on
`LEGACY_CRITICISM_ENABLED is False` (`preparation.py:522-531`), i.e. it
switches the whole criticism circuit off Road E and onto the school-routed
engaged policy. That changes far more than the critic's content, so it cannot
serve ARM V. Supports: the rejection of Option V-c below.

**M5 — the compiled-manifest road DOES admit per-role endpoints, and it is
live-proven.** `scripts/cycle_soak.py` case `pr1` is "CROSS-FAMILY seats
(deepseek-v4-pro:0813 conjecturer, kimi-k3 critic, a two-seat qwen3.5/glm-5.2
judge ensemble)", built by `build_manifest_pr1` and launched by
`experiments/2026-08-25-poietics-program/pr1_run.sh` as
`doctor --run-manifest --production-contracts` then
`run --run-manifest`. And the soak itself redirects EVERY role to a local
loopback stub (`_loopback_config`, `cycle_soak.py:369-397`) and drives the
managed path to cycle 8 — so "one role at a local stub, the rest live" is a
strictly simpler shape than one an existing committed instrument already
drives. Supports: Option V-a, CHOSEN.

**M6 — ARM A's granted-authority trial is refused at three independent gates
on a one-model run.** Not inferred; each is a committed check or a committed
Trap.

1. **The judge ensemble is unobtainable.** `llm/adapter.py:702-706`:
   `_select_judge_ensemble` takes the cross-SCHOOL substitute only when
   `self.school_judge_bindings` is non-empty AND `is_single_family_run`;
   otherwise `require_cross_family_judge_ensemble`, which raises
   `JudgeEnsemblePolicyError` on a single-family run. And
   `school_judge_bindings` has **no production caller at all** —
   `build_adapter` (the one production construction site,
   `llm/adapter.py:1928-1944`) never passes it:

        grep -rn "school_judge_bindings" src/ tests/
        src/deepreason/llm/adapter.py:270,295,702,704
        tests/test_prose_refutation_boundaries.py:888,918,1011,1285

   The map states it and PINS it — `docs/map/CON-schools.md:151`, verbatim:
   "**A judge school binding cannot reach the system through the manifest, so
   the only surface that accepts one is the adapter constructor** — and no
   in-tree production caller populates it."
   `check: grep -q "school_judge_bindings" src/deepreason/llm/adapter.py && ! grep -rl "school_judge_bindings" src/deepreason --include=*.py | grep -qv "llm/adapter.py"`

2. **The manifest validators refuse a judge school binding at freeze time**
   (`V4_SCHOOL_ROLE_UNSUPPORTED` / `V4_CRITICISM_ROLE_UNSUPPORTED`), and the
   runtime resolver refuses it again (`SCHOOL_ROUTE_ROLE_UNSUPPORTED`) —
   `docs/map/CON-schools.md:140-152`. Those validators live in
   `src/deepreason/run_manifest.py`, **frozen surface 4**.

3. **The mode is already recorded as dead weight.**
   `docs/map/CON-schools.md`'s Traps, verbatim:

   > **`ARGUMENTATIVE_AUTHORITY=single_family_trial` cannot complete a trial.**
   > The `Config` direct-helper path passes no `critic_school_id`, so a school
   > can only arrive through the v4 envelope, and that envelope demands a
   > manifest-bound authority value. Parked as dead weight, not removed.

   and

   > **Mistaking `require_cross_school_judge_ensemble` for the live
   > guarantee.** It and `LLMAdapter.school_judge_bindings` are retained but
   > superseded — correct only for a manifest that authors judge bindings,
   > which the validator does not permit.

Supports: the STOP below. **Note precisely what M6 does and does not say:** the
switches travel (M1, M2), so the 2026-08-28 P10 defect R11 names is NOT the
blocker. The blocker is that the solo road the 2026-08-09 law requires to exist
does not, in fact, reach a run.

**M7 — `compose_result.py` can emit per-position units deterministically**
(R19's condition). Its accepted-position loop
(`.../organiser-testing/tools/compose_result.py:99-115`) renders each surviving
position as its own contiguous, ordered block keyed by `order_key`, so one file
per position is a rendering choice, not a new derivation. The bare essays'
matched-length counterpart is NOT deterministic without a stated rule; the rule
this tranche registers is in PREREG §S8 below. Supports: R19 buildable.

**M8 — the typed result surface already reports most of R23.**
`deepreason results --json --verify` on the organiser root carries
`evidence_states.counts` = `{"contested":0,"open":55,"refuted":1,"supported":32}`
and `adjudication` = `{"judge_calls":0,"ran":false,"trial_blocked":{},
"trial_declined":{},"trial_observations":{}}`. So the census tool owes only the
attack-edge/warrant-by-road split and the placebo coupling table, not the
evidence states. Supports: R23's item, and shrinks S11.

**M9 — a 500 000-token harness run on this question costs about 22 minutes.**
The organiser ARM R: `started 2026-09-06T11:09:45Z`, `finished
...T11:31:32Z`, `token_spend 495362`, `cycles_completed 4`,
`state completed`. Supports: the wall-clock pricing in Budget below. Caveat
recorded: that run carried `PACK_TOKEN_BUDGET 24000` and a 97-block
attachment, so a plain 500k run will spend its ceiling over MORE cycles and
take longer.

**M10 — the model is `qwen3.5:397b`, not CLAUDE.md's `glm-5.2`.**

    grep -rho "--model [a-z0-9.:_-]*" experiments/2026-08-3*/ experiments/2026-09-*/ | sort | uniq -c
         11 --model qwen3.5:397b

`PREREG_D8.md §0` already ruled on the same conflict and chose
`qwen3.5:397b`, reasoning off, cap 8192, context 131072, "and the model the
copied judge panel already scores with". Supports: R4's "the harness's current
model". The stale CLAUDE.md header is PARKED, not fixed (R31).

---

## Items

### The arms

**S1 (R4, C3, M10).** One question, one model, matched ceiling.
Question: `experiments/2026-09-05-change-mini-isolation-programme/runs/input-d8`
`run-input.json` -> `problem.description` verbatim, extracted the way
`armR.sh:22` extracts it (never retyped). Model `qwen3.5:397b` at
`https://ollama.com/v1`, reasoning `none`, completion cap 8192, context
131072, in every seat of every harness arm and every judge. Per-harness-run
ceiling 500 000 tokens.
`accept:` each ladder prints the question's sha256 and it equals the digest
`PREREG.md §0` seals; each ladder's `deepreason --config … config` GUARD (M2)
exits non-zero if any pinned value did not land.

**S2 (R5, Q6).** ARM 0 — plain repeated sampling. `tools/arm0.py`, copied from
`experiments/2026-09-05-change-mini-isolation-programme/d8/arm0.py` and changed
in exactly one place: `K` becomes a required argument instead of 3. One chat
completion per sample: user message = the frozen problem description verbatim,
`max_tokens` 8192, reasoning off, no system prompt, no `response_format`.
K is set AFTER the harness arms terminate, to the harness arms' own
conjecturer-seat call count (Q6's resolution: matching "by number of calls"
cannot be computed before the thing being matched exists, so ARM 0 runs LAST).
Actual spend reported; unused allowance reported, never padded.
`accept:` `tools/arm0/ARM0_RESULT.json` exists with K completed calls, each
carrying `finish_reason` and non-empty content, and RESULTS.md reports
`K == <the measured conjecturer call count>` with both numbers pasted.

**S3 (R6).** ARM C — the harness as it ships, criticism rendered to the next
candidate, `ARGUMENTATIVE_AUTHORITY=observe_only`. `DISCHARGE_POLICY` stays at
its shipped default `discharge-required.v1`, which is what puts open
criticisms in the conjecturer's BINDING block
(`docs/map/CON-discharge-channel.md`).
`accept:` on the terminal root, every conjecturer call whose problem carried an
open criticism has a section-plan receipt naming `dr.open-criticisms`; the
count is reported as `n of m` in the organiser tranche's own form
(`armR.sh:33-35`'s `grep -l … objects/*section-plan*/*.json` shape), and the
same command run on the pre-launch stub root reports non-zero.

**S4 (R7, R8, R9; M3, M4, M5).** ARM V — vacuous criticism, road (a).
`tools/critic_stub.py`: a loopback HTTP endpoint bound to
`roles["argumentative_critic"]` only, importing
`scripts/wheel_operational_smoke.py`'s stub the way `cycle_soak.py:58` does
("the ONE stub, reused") and overriding ONLY the argumentative-critic
response's objection text, drawn round-robin from a fixed bank in
`tools/vacuous_bank.json`. The bank is written AFTER ARM C terminates and is
length-matched to ARM C's measured objection-length distribution (median and
IQR reported). Every bank entry is target-free by construction: it names no
artifact id, no claim text and no mechanism.
`accept (delivery):` on an offline stub root, `dr.open-criticisms` renders the
stub's objections in the SAME section at the SAME priority with the SAME
disposition as ARM C's, proven by diffing the two roots' section-plan receipts
for that section.
`accept (vacuity):` a check over the bank asserts no entry contains any token
appearing in its target's claim body beyond a closed stop-list, and the check
is driven RED by planting one target-specific entry.

**S5 (R10, R11, R30; M1, M6).** ARM A — **STOPPED**. See "Questions for
operator". No ARM A file is written until the operator's words arrive.

**S6 (R12, R13, Q4).** Two runs per harness arm, one home per arm.
Resolution, and it is STRONGER than the nonce R13 offers: vary NOTHING. Run
identity is `question + budget + provider profile + policy preset + dossier`
(`docs/map/CON-run-identity.md`), and `RUN_ALREADY_STARTED` is raised against
*the first run's root*, not against the home. So the second run of an arm is
taken by retiring the first root — `git mv run-<id> completed-epoch1-run-<id>`,
**the rename committed first** (CLAUDE.md, "Live runs") — and relaunching the
identical configuration. Both runs are committed whole; the two share one run
id and are told apart by their committed directory names, which is disclosed in
RESULTS.md. No configuration field moves, so nothing has to be shown not to
have moved.
`accept:` per arm, two committed roots, `completed-epoch1-run-<id>` and
`run-<id>`, with identical `run-manifest.json` sha256 and identical
`source_config_hash`; the rename is its own commit, earlier than the second
root's.

**S7 (R14, Q5).** Three qualification batteries — one per arm home (C, V, A),
because each arm's manifest carries a different subject: ARM C the baseline,
ARM V a different `roles` table, ARM A a different echoed
`ARGUMENTATIVE_AUTHORITY`. Within a home the second run is a cache hit (same
subject digest, same home). If ARM A is dropped or re-shaped, the count moves
and CHECKLIST.md is re-planned.
`accept:` three `qualify`/`doctor` records committed, each reporting its own
subject digest; the second run of each arm logs a cache hit, not a battery.

### The measure

**S8 (R15, R16, R17, R18, R19, R20, R21).** `PREREG.md`, sealed by sha256 in
the commit message of the commit that adds it, **before any live call**,
following `PREREG_D8.md` and the organiser `PREREG.md` Amendments 7-9 for form.
It fixes, and may afterwards be changed only by a dated numbered amendment:
- **§0 what is fixed for every arm** (S1's pins, by digest).
- **§1-§4 the arms**, as S2-S6.
- **§5 the unit.** Each harness run's composed result from
  `tools/compose_result.py` (copied byte-for-byte, then extended only with
  `--per-position`), REFUSED when the root is not `completed` or when its
  `REPLAY_VALIDATION.json` reports any violation — the organiser Amendment 9
  strictness, kept, never loosened. ARM 0's units are its essays.
- **§6 the instrument.** `tools/judge_pairwise.py`, copied; blind pairwise
  forced choice, position swap, three judges, ties refused in the prompt.
  CRITERIA byte-identical to the organiser tranche's, proven by `diff` and by
  the tool's own `criteria-check` sha256
  `fab3fde2f3a2000bd5f7415e7a7ae3be013fd8b83b4fd52395eef4b18327df28`.
- **§7 the pairings.** C vs 0, V vs 0, **C vs V**, A vs C, A vs 0 (A only if
  the operator rules ARM A in).
- **§8 the rule.** Consistent-win share >= 2/3 BETTER, <= 1/3 WORSE, between
  NULL; order-flip = NO PREFERENCE, kept in the denominator; a failed arm
  INCONCLUSIVE; **reported per pair of runs, never pooled** (R21).
- **§9 the length rule and the ceiling registered against it.** 1.5x applied
  to the verdict, AND the raw consistent-win share plus
  `verdict_before_length_rule` reported beside it. Registered in advance: a
  composed unit ran 21 396-46 518 characters against bare units of
  5 875-7 985, so ratios near 3-6x are expected and the rule will very likely
  NULL any BETTER. That is a property of the sealed rule, not a finding. The
  rule is not changed to make the verdict reachable.
- **§10 the secondary comparison the length rule cannot defeat** (R19, M7).
  Units: each surviving position, one file, deterministic. Counterpart: the
  bare essay's paragraphs (split on blank lines, the essay's own order)
  concatenated greedily from the first until within 1.5x of the position
  unit's character count, and the resulting ratio reported. Registered as a
  RULE before any reading, so it cannot be tuned to a result.
- **§11 the predictions**, every one a claim in `claims.json`.
`accept:` `PREREG.md` committed with its sha256 in the commit message; no
provider call from this tranche exists in any earlier commit.

**S9 (R22).** `tools/coupling_placebo.py` — W2's discipline, copied in method:
for every criticism, whether the candidate AFTER it changed and whether the
candidate BEFORE it changed, **the difference reported as the only evidence**,
per arm and per run, with n.
`accept:` the tool's self-test reproduces W2's own published table for the two
roots W2 measured (`experiments/2026-08-26-run-anatomy-w2-criticism/`) to the
tenth of a percentage point; a run of it on a root with zero criticisms prints
`n=0` and no rate.

**S10 (R23, M8).** `tools/record_census.py` — per arm, from the record only:
attack edges minted; warrants split demonstrative / argumentative; refutations;
evidence states open / supported / refuted / contested (read from
`deepreason results --json`, not re-derived).
`accept:` the census's evidence-state row equals `results --json`'s
`evidence_states.counts` byte-for-byte on the same root.

**S11 (R24).** `claims.json` for `tools/record_claims.py`: every prediction in
PREREG §11 as a claim, each with "not shown able to fail" standing.
`accept:` `python tools/record_claims.py <claims.json>` exits 0 and every claim
carries a standing; no claim lacks a falsifier.

### The run

**S12 (R25).** A green `cycle_soak.py` per launch configuration before its
launch. ARM C and ARM A shapes: `--case` on the tranche's own committed
config. ARM V's shape additionally has the critic at the stub, which the soak
already does for every role.
`accept:` a committed soak log per configuration, ending green.

**S13 (R26).** Env discipline. Already satisfied at capture:
`git check-ignore -v experiments/2026-09-09-change-d8-criticism-experiment/env`
-> `.gitignore:50 experiments/**/env`, mode `-rw-------`, 73 bytes, never
committed, never echoed.
`accept:` `git log --all --stat | grep -c "d8-criticism-experiment/env"` is 0.

**S14 (R27, R28).** Detached launch with the snapshot loop
(`experiments/live_research_2026-07-29/snapshot_loop.sh` shape), monitored on
`progress.jsonl` and the driver log's `rc=` lines. Typed outcomes only. One
relaunch per arm for a transport death before cycle 1 completed. Failure
budget 8 live calls beyond the plan, ledgered S6-style. Every root committed
whole.
`accept:` per arm, a committed driver log with its `rc=` lines and a snapshot
log; a `FAILURES.md` ledger, empty or itemized.

**S15 (R29).** `RESULTS.md` as an honest ledger, with the residue stated: one
question, one model, two runs per arm, same-model judges, the length ceiling —
plus whatever ARM A's disposition adds.
`accept:` every section present and every number traceable to a committed
artifact.

**S16 (R31, R32, R33).** Tests only for the tranche's own tools, under
`experiments/2026-09-09-change-d8-criticism-experiment/tests/`. **No file under
the repository's `tests/` changes, so no gate run is owed** — and none will be
run. Delivery through `dr-validate-change` then `dr-deliver-change` with the
R-by-R table. Commit and push at every phase boundary and every `rc=` line,
retry 2s/4s/8s/16s.
`accept:` `git diff --stat origin/main -- src/ mini/ tests/` is empty at
delivery.

---

## Assumptions (operator may override)

**A1 (Q2, from M3/M4/M5).** All three harness arms launch on the
**compiled-manifest road** — a tranche-local builder, then
`doctor --run-manifest --production-contracts`, then `run --run-manifest`
(the `pr1_run.sh` shape) — not `deepreason reason`. Assumed, operator may
override. Why it is the smallest reading and not a shrinking of the design:
ARM V's stub-bound critic is unreachable on the managed `reason` path (M3, M4),
and if ARM C ran on `reason` while ARM V ran on the manifest road, C-vs-V
would confound the critic's content with the launch road — which is the one
comparison the brief calls "the arm that makes this a measurement of
criticism". One road for all three is therefore forced, and the manifest road
is the only one that admits all three. It is the same run path in any case:
the operations-parity law of 2026-08-13 makes `run --run-manifest` a rendering
shell over `start_manifest_run`, the single entry every configuration uses.
DISCLOSED as a limit: R6's words are "the harness as it ships", and the
organiser tranche's verified `dr.open-criticisms` receipts were taken on the
`reason` road, so S3's accept-check re-proves the rendering on this road
before launch rather than inheriting that evidence.

**A2 (Q4).** The second run of an arm varies nothing at all (S6), rather than
the declared nonce R13 offers. Assumed as strictly stronger: a nonce would
have to be shown to move nothing else; varying nothing has nothing to show.

**A3 (Q6).** ARM 0 runs LAST, with K set from the harness arms' measured
conjecturer-seat call count (S2). Assumed: R5 matches spend "by number of
calls", and that number does not exist until the harness arms have run.

**A4 (M10).** `qwen3.5:397b` is "the harness's current model" for R4, on
`PREREG_D8 §0`'s own reasoning. CLAUDE.md's `glm-5.2` header is stale and is
PARKED, not fixed.

**A5 (§10, R19).** The bare-essay counterpart unit is defined by the greedy
paragraph rule in S8 §10. Assumed because R19 requires the comparison to exist
and the essays carry no deterministic section structure; the rule is
registered before any reading so it cannot be tuned.

---

## Questions for operator (STOP — non-empty)

**Q-OP1. ARM A cannot bite as worded. Which road?**

The switches travel — that part of R11's worry is measured clear (M1, M2).
What does not exist is the trial itself: on a one-model run there is no judge
ensemble a granted authority can reach, and the mode the brief names is
already recorded as parked dead weight (M6, three independent gates, two of
them committed map checks). So `ARGUMENTATIVE_AUTHORITY=single_family_trial`
+ `ADJUDICATION_STATUS_AUTHORITY_ENABLED=true` would run, emit its typed
notice, mint zero argumentative warrants, and measure nothing about authority.

Three roads, priced:

- **Road A-cross (RECOMMENDED).** Keep every generation seat on the one model
  and give the JUDGE role a two-seat cross-family ensemble
  (`qwen3.5:397b` + one second family), with
  `ARGUMENTATIVE_AUTHORITY=trial_required`. Cost: **0 lines under `src/`**;
  the compiled-manifest road already carries per-role ensembles and
  `cycle_soak.py --case pr1` already soaks exactly this shape. Deviation from
  R4: the judge seats are not the one model — disclosed, and confined to the
  seats that adjudicate, so ARM A's conjecturer and critic stay byte-identical
  to ARM C's, which is what A-vs-C has to hold still. Why it is recommended:
  it answers R10's actual question at zero code cost, and the judge law as
  amended (2026-08-28) says this exact configuration — cross-family, unanimous
  — is the one measured to UNDER-convict (11.9% sensitivity, false conviction
  0.0-2.5%), so a warrant it mints is conservative rather than trigger-happy.
  Second cost, stated plainly: it spends judge calls, and the operator's 2026-08-09
  caution about judges applies.
- **Road A-code.** Wire the solo road the 2026-08-09 law requires: pass
  `school_judge_bindings` in `build_adapter`, and let the manifest validators
  admit a `role="judge"` school binding. ~10 lines in
  `src/deepreason/llm/adapter.py`, plus `src/deepreason/run_manifest.py` —
  **frozen surface 4** — plus `llm/firewall.py`'s resolver, plus two committed
  map checks that currently PIN the isolation (`CON-schools.md:151` would go
  red by design). The blast-radius gate's own computed result for the
  adapter half alone, verbatim, pasted below in the forecast section:
  `frozen_surface_verdict: CONTACT`. R30 forbids building this here in any
  case; naming it is the point.
- **Road A-park.** Run ARMs 0, C and V now — which answers the brief's own
  "the arm that makes this a measurement of criticism", C vs V — and park ARM
  A with a ready-to-send prompt. Cost: R10, R20's `A vs C` and `A vs 0`
  undelivered; the authority question stays open.

**Q-OP2. One tranche, or two?**

The tooling itemizes to ~1 500 lines (Budget below), five times the ~300-line
figure at which the change workflow says to propose an ordered split, and the
live programme is three batteries plus eight harness runs plus ARM 0 plus
judging — serial, because ARM V's bank must be length-matched to ARM C's
measured objections (S4).

- **Split (RECOMMENDED).** Tranche 1: every instrument, the offline proofs
  (S4's delivery and vacuity checks, S9's W2 reproduction, S12's soaks), and
  `PREREG.md` sealed — **no live call**. Tranche 2: the launches, the judging,
  RESULTS.md. Why: the pre-registration has to be sealed before any live call
  regardless, so that is a real boundary rather than an invented one; and if
  an offline proof fails, no tokens were spent finding out.
- **One tranche.** Matches the brief's "Stop when delivered and pushed", at
  the cost of one very large delivery and no checkpoint between building the
  instruments and spending ~4.5M provider tokens on them.

A word answers each: for Q-OP1, "cross", "code" or "park"; for Q-OP2, "split"
or "one".

---

## Out of scope (explicit)

- Fixing the `single_family_trial` dead weight, the P10 switch defect, or the
  organiser tranche's parked P8/P9 — not requested (R30, R31).
- Correcting CLAUDE.md's `glm-5.2` header — not requested; PARKED.
- A criticism-of-criticism road (audit §5.1 gap 4) — not requested.
- Any change to `tools/root_sweep.py` or the wheel-smoke pins — no `src/`
  target, so no pin moves.

## Frozen-surface contact forecast

**For the design as specified for ARMs 0, C, V (every target under
`experiments/2026-09-09-change-d8-criticism-experiment/`; the copy sources
declared):** `tools/blast_radius.py --files <copy sources> --symbols compose`
computed:

    frozen_surface_verdict: CLEAR
    frozen_surface_contacts: []
    frozen_adjacent_contacts: []

**For Road A-code, if the operator rules it in (it is NOT built here):**
`tools/blast_radius.py --files src/deepreason/llm/adapter.py --symbols
build_adapter school_judge_bindings _select_judge_ensemble
require_cross_school_judge_ensemble` computed, verbatim:

    frozen_surface_verdict: CONTACT
    frozen_surface_contacts: []
    frozen_adjacent_contacts: [
     {
      "surface": "route_fingerprint serialization (llm/firewall.py)",
      "tier": "SYMBOL_INDIRECT",
      "target": "require_cross_school_judge_ensemble",
      "detail": "'require_cross_school_judge_ensemble' referenced in src/deepreason/llm/firewall.py (grep-based; not proof of semantic contact)"
     }
    ]
    reachability: [
     {"symbol": "build_adapter", "status_current": "REACHABLE", "status_base": null, "direction": null},
     {"symbol": "school_judge_bindings", "status_current": "UNKNOWN", "status_base": null, "direction": null},
     {"symbol": "_select_judge_ensemble", "status_current": "REACHABLE", "status_base": null, "direction": null},
     {"symbol": "require_cross_school_judge_ensemble", "status_current": "REACHABLE", "status_base": null, "direction": null}
    ]

`CONTACT` plus one `UNKNOWN` reachability entry: two independent grounds on
which this checkpoint stops the tranche until the operator's words arrive. The
second half of Road A-code — the manifest validators — is frozen surface 4
DIRECTLY, which the tranche has not even priced with the gate because it is
not a road anyone may take without those words.

## Blast-radius census

Every hit from the gate's `consumers` fields, classified.

For the ARM 0/C/V targets (`--files <copy sources> --symbols compose`):

- `consumers.tests` for `compose`: `tests/test_bridge_compose.py:9,68,302,338,
  362,371,411`, `tests/test_bridge_composition_repair.py:24`,
  `tests/test_bridge_diagnostic_matrix.py:20`,
  `tests/test_bridge_retry_failed_terminal.py:224`,
  `tests/test_bridge_two_stage.py:7,77,94,147`,
  `tests/test_bridge_v3_epistemi…` — **MUST NOT MOVE**, every one. These are
  the grounded-application bridge's own `compose`, an unrelated symbol that
  merely shares the copied tool's function name; the tranche has no `src/`
  target, so none of them can move.
- `consumers.map_checks` for `compose`: `docs/map/INDEX.md:60`,
  `SEAM-bridge-x-llm.md:4,40,46,48,65,89,126,148`,
  `SEAM-bridge-x-manifest.md:85,115,119,127`, `SUB-adjudication.md:38`,
  `SUB-bridge.md:71,…` — **MUST NOT MOVE**, same reason. No `Verified-at:`
  stamp is advanced by this tranche.
- `consumers.qualification_digest`: `[]`. `consumers.wheel_smoke_pins`: `[]`.
- `reachability`: `[{"symbol":"compose","status_current":"REACHABLE",
  "status_base":null,"direction":null}]` — nothing UNKNOWN, so no manual
  cross-check is owed here.

For Road A-code (priced only): `consumers.tests` for `build_adapter` hits
`tests/test_adapter_attempt_logging.py:9,477,534,574`,
`tests/test_cli_bridge.py:475`, `tests/test_config.py:155,163`,
`tests/test_engine_profile_dispatch.py:59,89`,
`tests/test_model_firewall.py:247,263`,
`tests/test_prose_refutation_boundaries.py:1229,1233,1235,1248`,
`tests/test_runtime_workload_integration.py:376,422`,
`tests/test_simulation_capability_v5.py:268,286,358` — all **EXPECTED TO
MOVE** only in the sense that a new keyword argument's default keeps them
green; none is a target here. `consumers.map_checks` hits
`docs/map/CON-authority.md:108`, `CON-packs-and-token-economy.md:4,63,64,465`,
`CON-schools.md:151`, `CON-seats.md:4,152,164`,
`INV-frozen-surfaces.md:1388`, `SEAM-bridge-x-llm.md:65,116,126,148`,
`SEAM-bridge-x-manifest.md:144`, `SEAM-evaluation-x-ontology.md:117`,
`SEAM-llm-x-manifest.md:4,102,111,161,177`, `SEAM-llm-x-rules.md:4,…` — of
these **`CON-schools.md:151` is EXPECTED TO MOVE (go red) by design**, since
its check exists precisely to pin the isolation Road A-code would end; every
other one is **MUST NOT MOVE**.

Manual cross-check for the one `UNKNOWN` symbol, as this checkpoint requires
where the gate says in writing that it cannot judge:

    grep -rn "school_judge_bindings" tests/ docs/map/
    tests/test_prose_refutation_boundaries.py:888,918,1011,1285
    docs/map/SEAM-manifest-x-schools.md:221,227
    docs/map/SUB-llm.md:38
    docs/map/CON-schools.md:81,151,240

Four test sites and four map documents — three of which describe the absence
Road A-code would end. Classification: `CON-schools.md:151` and
`SEAM-manifest-x-schools.md:227` **EXPECTED TO MOVE** under Road A-code;
everything else **MUST NOT MOVE**. Under the recommended Road A-cross, all
eight **MUST NOT MOVE**, and nothing in this tranche touches them.

## Options

**ARM V's road.**
- **V-a: a loopback stub bound to the critic role only.** Files: 2 tranche
  tools + 1 bank + 3 configs. Frozen contact: none. ~350 lines. Risk: the
  stub must satisfy the critic contract and the production-contract doctor.
  **CHOSEN**, cites M5 — `cycle_soak.py` already redirects every role to that
  same stub and drives the managed path to cycle 8, and the soak already runs
  the production-contract doctor against it, so the harder version of this is
  a committed, green instrument.
- **V-b: the same, on the managed `deepreason reason` path.** REJECTED, cites
  M3: `roles` is host-owned there, in the code's own words "a configuration
  file may never redirect a managed run to another endpoint".
- **V-c: `--criticism-seat`, the one supported per-role critic lever.**
  REJECTED, cites M4: it is gated on `LEGACY_CRITICISM_ENABLED is False`, so
  taking it moves the whole criticism circuit off Road E onto the
  school-routed policy — ARM V would then differ from ARM C in the circuit as
  well as the content, and C-vs-V would measure the circuit.
- **V-d: a registered critic shell asking for generic objections (the
  brief's road (b)).** REJECTED on the brief's own ground and not re-argued:
  "a model asked to be vacuous may not comply". Kept as the named fallback if
  V-a's stub cannot pass the doctor.

**ARM A's road.** Three, priced in Q-OP1. Recommendation A-cross, citing M6
(A-code is refused at three gates and contacts frozen surface 4) and the
2026-08-28 judge law as amended (A-cross's ensemble is the measured-conservative
configuration).

## Budget

Itemized, tranche-local lines only (no `src/`, no `mini/`, no repo `tests/`):

    python3 -c "print(sum([120,350,150,120,180,250,200,250,60,320,140]))"
    2140

- `tools/arm0.py` (copied + K argument) 120
- `tools/critic_stub.py` + `tools/vacuous_bank.json` 350
- `tools/build_manifest.py` (three configurations) 150
- `tools/compose_result.py` (copied + `--per-position`) 120
- `tools/judge_pairwise.py` (copied + five pairings) 180
- `tools/coupling_placebo.py` 250
- `tools/record_census.py` 200
- `claims.json` 250
- `runs/config-*.yaml` 60
- `PREREG.md` 320
- tranche tests 140

**~2 140 lines, ~14 commits.** Frozen surfaces touched: **none** under the
recommended roads; **flagged** under Road A-code (frozen surface 4 plus
frozen-adjacent `route_fingerprint`), which is why it is a question and not an
item. Live cost, priced from M9: 3 batteries (~14 min, ~1 160 calls each) +
6 harness runs at 500 000 tokens (or 8 with ARM A) + ARM 0 + judging ~ **3.5-4.5
million provider tokens and roughly 5-8 hours of wall clock**, serial.

Because 2 140 exceeds the ~300-line figure by seven times, the split proposed
in Q-OP2 is this section's own recommendation, not an aside.

Rubric: 6/6 yes — every R has an item with a machine-decidable accept (S1-S16
cover R1-R33; R1/R2/R3 are discharged by REQUEST.md and this document
existing, R11/R30 by the STOP); blast-radius census pasted and every hit
classified; frozen-surface contact forecast recorded from the gate's own
output, twice; every mechanism the request names traced to code it reaches
(M1-M8) and the two that do not reach it named as such (M3/M4 for ARM V's
managed road, M6 for ARM A); every claim measured and every option priced;
nothing untraceable to an R or C number.

---

# Amendment 1 (2026-09-09) — the operator answers both questions; the tranche splits

Authority: REQUEST.md Amendment 1, R34-R40, C9. Everything above this line is
UNCHANGED — S1-S16, M1-M10, the census and the two forecasts stand as sealed,
and the STOP they recorded is now answered rather than edited away. This
amendment says what the answers change and nothing else.

## What Q-OP1's answer changes: S5 becomes buildable, on one road

**S5 (R34, R35, R10-partial, C2) — ARM A, Road A-cross. REPLACES the STOPPED
S5 above.** ARM A is ARM C with two differences and no others:

1. `ARGUMENTATIVE_AUTHORITY=trial_required` (R34 supersedes R10's
   `single_family_trial`) and `ADJUDICATION_STATUS_AUTHORITY_ENABLED=true`
   (R10's half, retained: `rules/crit.py::_authority` returns `observe_only`
   whatever the mode says unless this master gate is on).
2. The `judge` role alone carries a two-seat cross-family ensemble. The seats
   are taken VERBATIM from the committed precedent rather than invented —
   `experiments/2026-08-25-poietics-program/run-config.yaml`, measured:

       judge = [('qwen3.5:397b', 'qwen', 'https://ollama.com/v1'),
                ('glm-5.2',      'glm',  'https://ollama.com/v1')]

   which is also the shape `scripts/cycle_soak.py --case pr1` already soaks
   ("a two-seat qwen3.5/glm-5.2 judge ensemble").

Every other seat — conjecturer, argumentative_critic, defender, variator,
summarizer, synthesizer, vision_critic, property_designer, thesis,
grounding_reviewer — stays on `qwen3.5:397b`, byte-identical to ARM C's.
**The defender is a GENERATING seat, not an adjudicating one** — it writes a
defence, it does not rule — so R35's confinement keeps it on the one model.
That reading is recorded here because the opposite one is available and the
precedent run happens to put a different family in that seat.

`accept (route identity):` ARM A's and ARM C's compiled role tables are
compared field by field; every role but `judge` has an identical
`route_sha256`, and `judge` differs by having two seats of two families. The
comparison is a committed tool output, not an eyeballing.
`accept (the gate is really on):` on a dry-run against the stub, the rebuilt
run configuration reports `ARGUMENTATIVE_AUTHORITY=trial_required` AND
`ADJUDICATION_STATUS_AUTHORITY_ENABLED=True`, and
`rules/crit.py::_authority` over that configuration returns `trial_required`
rather than `observe_only` — the same measurement M1 made, re-made on ARM A's
own compiled artifact.
`accept (the ensemble is obtainable):` on the same dry-run,
`_select_judge_ensemble` returns two seats and does NOT raise
`JudgeEnsemblePolicyError`; the check is driven RED by collapsing the judge
role to one seat, so it fails for the reason it claims to test.

**An open question this amendment does NOT assume away.** Whether a defended
trial also requires `JUDGE_SEATS_ENABLED` and a `rubric_policy` other than
`forbid` to dispatch is NOT settled here from reading. It is a done-criterion
of a tranche-1 step: the answer comes from a dry-run and a stub soak, offline,
and whatever it turns out to be is recorded in PREREG §2 before sealing. The
P-C1 soak case runs with `rubric_policy forbid, JUDGE_SEATS_ENABLED false`,
which is evidence that the two settings are independently switchable, not
evidence about what a trial needs.

**S5b (R35).** PREREG §0 carries the deviation as a named, dated disclosure in
its own row — not a footnote — in the form: ARM A's judging seats are not the
one model; its conjecturer and critic are byte-identical to ARM C's; therefore
`A vs C` measures granted authority WITH cross-family adjudication against no
authority, and no claim of a pure one-model comparison may be made from it.

**S5c (R37).** PARKED P1 is untouched and unbuilt. Road A-cross is not a fix
for it and must not be reported as one: the solo road the 2026-08-09 law
requires still does not reach a run, and this tranche routes around that
rather than repairing it — the same move, and the same disclosure, that the
organiser tranche's Amendment 8 made for its own parked defect.

**Q-OP1's other consequence: the frozen-surface forecast for the tranche as
now specified is the CLEAR one.** The `CONTACT` verdict recorded above belongs
to Road A-code, which the operator has ruled out (R37). Nothing in this
tranche declares a target under `src/`, so the forecast that governs is:

    frozen_surface_verdict: CLEAR
    frozen_surface_contacts: []
    frozen_adjacent_contacts: []

## What Q-OP2's answer changes: the tranche is TRANCHE 1, and it spends nothing

**The bound (R38, C9): no live call.** Every instrument in tranche 1 is proven
against the deterministic stub, a committed root, or a fixture. The credential
in the tranche's gitignored `env` is not read by anything tranche 1 runs.
`accept:` at delivery, `grep -rn "ollama.com" experiments/2026-09-09-*/` returns
only configuration files and documents — no executed log; and no tranche-1
artifact carries a provider response.

**Tranche 1 owns:** S1's pins (as declarations), S2's `arm0.py` (built, not
run), S3's and S5's configurations and manifest builder, S4's stub and bank
TOOL, S8's `PREREG.md` sealed, S9's `coupling_placebo.py` with its W2
reproduction, S10's `record_census.py`, S11's `claims.json`, S12's soaks,
S13's env discipline (already met), S16's scope and delivery discipline.

**Tranche 2 owns:** S6's launches and root retirements, S7's three
qualification batteries, S2's ARM 0 execution with K set from the measured
call count, S4's bank MINTED from ARM C's measured objection lengths, S14's
detached runs and failure ledger, S15's RESULTS.md, and the judging.

**S4 is split, and the split is the honest one (R38 × R7/R9).** ARM V's bank
must be length-matched to ARM C's objections, and ARM C has not run. So
tranche 1 ships `tools/make_vacuous_bank.py` — a deterministic generator that
takes a target length distribution and emits the bank — and proves it on the
objection lengths of an ALREADY-COMMITTED root, not on ARM C's. PREREG
registers the RULE that mints the real bank (median and interquartile range of
ARM C's own argumentative-critic objections, both runs pooled, reported before
the bank is generated), so the number is fixed by a rule sealed in advance and
filled in by a measurement, which is what pre-registration is for. The same
pattern covers S2's K.
`accept:` `make_vacuous_bank.py --self-test` reproduces a committed fixture
bank byte-for-byte from a fixed seed and a fixed target distribution.

**PREREG.md is sealed in tranche 1, before tranche 2's first call (R15, R38).**
It therefore states, in §0, exactly which of its values are rules awaiting a
measurement (ARM V's bank, ARM 0's K) and which are fixed numbers — so a reader
can tell a pre-registered rule from a post-hoc choice without trusting anyone's
memory.

## Budget, recomputed for tranche 1 only

    python3 -c "print(sum([120,220,150,120,180,250,200,250,60,320,140]))"
    2010

`tools/critic_stub.py` + `make_vacuous_bank.py` come to 220 rather than S4's
350, because the bank ITSELF (the 130 lines of generated content) is tranche
2's artifact, not tranche 1's. Everything else is unchanged from the itemization
above. **~2 010 lines, ~12 commits, 0 provider tokens, 0 frozen surfaces.**

Rubric: 6/6 yes — R34-R40 each have an item with a machine-decidable accept
(R34/R35 -> S5, S5b; R36 -> S16's accept; R37 -> S5c; R38/C9 -> the no-live-call
accept and the tranche-1/2 table; R39/R40 -> S16's delivery discipline); the
blast-radius census above is unchanged and still classifies every hit, and the
forecast that now governs is the CLEAR one, restated verbatim; every mechanism
this amendment names is traced to committed code or a committed configuration
(the judge ensemble to `poietics/run-config.yaml`, the master gate to
`rules/crit.py::_authority`, the ensemble selection to
`llm/adapter.py:702-706`), and the one thing it could not settle by reading —
whether a trial needs `JUDGE_SEATS_ENABLED` — is written down as an open
done-criterion instead of an assumption; nothing here is untraceable to an R
or C number.

---

# Amendment 2 (2026-09-09) — the budget ceiling counted the wrong thing

Found at step 3, before any instrument was written, by running the gate that
enforces it. Recorded as a correction rather than quietly raised, because
"raise the ceiling until it fits" is the exact failure the change workflow's
S5 precedent names.

**What was wrong.** Amendment 1's `~2 010 lines` itemized only the lines this
tranche WRITES — the delta on a copied instrument, not the instrument. The gate
(`tools/diff_budget.py <base> --paths <declared areas>`) counts every inserted
line in the declared areas against `origin/main`, which includes (a) the three
instruments copied verbatim, whose 784 lines this tranche commits without
authoring, and (b) the workflow's own artifacts — REQUEST.md, SPEC.md,
CHECKLIST.md, PARKED.md, and the VALIDATION.md and DELIVERY.md still to come —
which no earlier itemization listed at all. At step 3 the gate already read
1 486 of a 2 010 ceiling with zero instruments written, so the ceiling would
have tripped mid-tranche on an accounting mismatch rather than on scope.

**The complete itemization, and its arithmetic.**

    python3 -c "print('itemized total =', sum([1190,784,310,250,200,200,120,150,60,140,250,320,200,40]))"
    itemized total = 4214

- workflow artifacts (REQUEST + SPEC with both amendments + CHECKLIST with its
  pasted proofs + PARKED + VALIDATION + DELIVERY) 1190
- the three instruments copied verbatim (`arm0.py` 107, `compose_result.py`
  179, `judge_pairwise.py` 498 — measured, not estimated) 784
- edits to those three (`--per-position`, the five pairings, `K` as an
  argument) 310
- `tools/coupling_placebo.py` 250
- `tools/record_census.py` 200
- `tools/critic_stub.py` 200
- `tools/make_vacuous_bank.py` 120
- `tools/build_manifest.py` 150
- `runs/config-{c,v,a}.yaml` 60
- the tranche's own `tests/` 140
- `claims.json` 250
- `PREREG.md` 320
- `proof/` outputs 200
- three `CASES` rows in `scripts/cycle_soak.py` 40

**Ceiling: 4 400**, which is the itemized 4 214 plus a stated 4% margin for
proof outputs whose length is not knowable before the commands run. Declared
areas, unchanged: `experiments/2026-09-09-change-d8-criticism-experiment` and
`scripts`. Frozen surfaces touched: still **none** — this amendment moves an
accounting number and nothing else, and the CLEAR forecast of Amendment 1
stands.

**What this does NOT license.** The ceiling is not a target. If the tranche
approaches it, that is a signal to split again, not to amend a third time; a
third amendment to this number would be the S5 failure arriving one step later
than usual.

Rubric: 6/6 yes — the correction traces to R38's tranche-1 scope and to the
change workflow's own budget rule; the headline now equals its own pasted
arithmetic; no census, forecast or acceptance check moves.

---

# Amendment 3 (2026-09-09) — a class of false positive in the disclosure gate, declared in advance

Found three times in six steps, so it is named here rather than re-argued each
time. Declaring it is what the checkpoint is for: a contact "already named in
SPEC.md" is disclosed, and a disclosed mechanism is what the operator's words
would be given over. This amendment does NOT waive the gate; it records what
the gate is matching, and keeps the manual cross-check every time.

**The mechanism.** `tools/blast_radius.py` resolves declared SYMBOLS by grep
across `src/`, and says so of itself in every hit: *"grep-based; not proof of
semantic contact"*. A tranche-local tool whose function carries a common
English name therefore trips it. Three instances so far, all in files under
`experiments/2026-09-09-change-d8-criticism-experiment/tools/`:

| symbol | reported surface | what was actually matched |
|---|---|---|
| `table` | replay-validation formats, manifest schemas, `route_fingerprint` | the word in prose |
| `measure` | manifest schemas | the word in prose |
| `render` | replay-validation formats, manifest schemas | the word in prose |
| `question` | replay-validation formats, manifest schemas | `invariants.py:870,872` are COMMENTS; `:889` is an error-message string; `run_manifest.py:2504,2509` are COMMENTS |

**Why contact is impossible here by construction, not merely unlikely.** No
module under `src/deepreason/` imports anything from the repository's
`experiments/` directory. (`src/deepreason/experiments/` is a package inside
`src/` and is a different thing sharing a name — checked, and named here
because it is the one way this claim could be misread.) A tranche tool is not
on any import path the harness can take, so no symbol it defines can shadow,
override, or reach a frozen surface.

**What this tranche does about it, in order.**
1. Where a rename costs nothing, RENAME rather than argue: `table` →
   `render_arm_table`, `measure` → `measure_root`, `render` →
   `render_census_table`. Each was renamed and the gate re-run to `CLEAR`.
   Removing an ambiguity beats explaining it.
2. Where a rename would make a COPIED instrument diverge from its original for
   no reason — `arm0.py::question`, whose name comes from the mini tranche's
   committed file — keep the name, and disclose the hit here with the lines
   the gate matched pasted above.
3. Every remaining instance still gets the manual grep cross-check the
   checkpoint requires, recorded in the step.

**Standing for the rest of this tranche.** A `frozen_surface_contacts` entry
whose `tier` is `SYMBOL_INDIRECT`, whose target is a symbol defined only under
this tranche's `tools/` or `tests/`, and whose matched lines are comments,
docstrings or string literals, is DECLARED HERE and is not new drift. Anything
else — any `DIRECT` tier, any target under `src/`, any match on executable
code, or any `reachability` direction of `newly_dead`/`newly_live` — remains a
STOP requiring the operator's words. The CLEAR forecast of Amendment 1 stands
for the tranche's actual targets, none of which is under `src/`.

Rubric: 6/6 yes — traces to R30/R36 (the scope this gate guards) and to the
change workflow's own frozen-surface checkpoint; the mechanism is measured
(the matched lines are pasted, not summarised); no acceptance check moves; the
gate is not weakened, only its false-positive class disclosed.

---

# Amendment 4 (2026-09-09) — the ceiling is corrected to 6 500, on the operator's word

Authority: REQUEST.md Amendment 2, R41, the operator's "Raise." given after the
step-17 stop was presented with the overrun's two measured causes and three
priced options.

**What Amendment 2 said, and what happens to it.** Amendment 2 closed with:
"If the tranche approaches it, that is a signal to split again, not to amend a
third time; a third amendment to this number would be the S5 failure arriving
one step later than usual." That was this window's own caution and it fired
correctly — the gate tripped, the window stopped, and the decision went to the
operator instead of being taken quietly. The operator has overruled it. The
sentence stands in Amendment 2 unedited, because a caution that was right to
fire is not made wrong by being overruled, and deleting it would hide the fact
that a ceiling was raised a third time.

**The two measured causes of the overrun**, from `git diff --numstat`:

1. **857 lines of copied instruments that no itemization contained**:
   `tools/w2_census.py` (519) and `tools/w2_q5.py` (338), W2's own criticism
   census and placebo-rate instruments, copied verbatim with one line changed
   in each. The decision to copy rather than reimplement was taken at step 4,
   AFTER Amendment 2's itemization was written, and it was the right one: a
   second implementation of the placebo measurement would have been a second
   thing to keep in agreement with the first, which the modularity law exists
   to prevent. The cost of that correctness is 857 lines this tranche commits
   without authoring.
2. **Workflow documents carrying their evidence inline**: SPEC.md 906 (four
   amendments now), CHECKLIST.md 441 (every done-criterion's pasted output),
   REQUEST.md 261, PARKED.md 186 — **1 794 against the 1 190 budgeted for
   those four plus VALIDATION.md and DELIVERY.md**, neither yet written. This
   is the format doing what it is for: a pasted output is what lets a later
   reader check a claim without re-running anything.

**The corrected ceiling, and its arithmetic.**

    python3 -c "print(sum([4498,180,200,120,150,60,140,250,320,200,40,300]))"
    6458

- built and committed at step 17 (measured, not estimated) 4498
- `judge_pairwise.py`'s five pairings and its two refusal tests 180
- `tools/critic_stub.py` 200
- `tools/make_vacuous_bank.py` 120
- `tools/build_manifest.py` 150
- `runs/config-{c,v,a}.yaml` 60
- the tranche's remaining `tests/` 140
- `claims.json` 250
- `PREREG.md` 320
- remaining `proof/` outputs 200
- three `CASES` rows in `scripts/cycle_soak.py` 40
- VALIDATION.md and DELIVERY.md 300

**Ceiling: 6 500**, the itemized 6 458 plus a stated margin of 42. Declared
areas unchanged. Frozen surfaces touched: still none — Amendment 1's CLEAR
forecast and Amendment 3's declared false-positive class both stand.

**What the raise does NOT buy.** Lines only. R38's tranche-1 boundary and C9
are untouched: no live call is made in tranche 1, the credential stays unread,
and the launches remain tranche 2. If the gate trips again, this window stops
again and reports it — the rule that the window does not decide its own ceiling
survives the operator having decided it once.

Rubric: 6/6 yes — traces to R41; the headline equals its own pasted arithmetic,
whose first term is a MEASURED number rather than an estimate; no acceptance
check, census or forecast moves; the superseded caution is preserved rather
than edited.
