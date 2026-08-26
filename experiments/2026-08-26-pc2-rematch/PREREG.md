# PREREG — P-C2, THE REMATCH: the rebuilt harness against blind sampling

**Frozen before any provider call.** This file is committed and pushed
before the operator's key is used; the git log is the proof, and
`driver.log`'s first entry postdates the push.

Nothing in §1–§10 may be edited after launch. If a design turns out to be
wrong, that is recorded in RESULTS.md as a finding, or APPENDED here as a
dated appendix, never repaired in place.

Registered kill-or-cure for the REBUILD program.

---

## §1 — Authority, and what this tranche is for

The REBUILD program's registered bargain, operator 2026-08-26:

> "rebuild. These are massive issues that may explain why the results are
> terrible."

P-C1 is the committed defeat that bargain answers. On Heilbronn N = 13, at
matched measured budget, blind repeated sampling beat the harness **33×**
(0.0135949364055 vs 0.0004075) and the harness's own PREREG condition for
claiming value was NOT met. `experiments/2026-08-25-change-constructive-
frontier/RESULTS.md` is the record; it was read in full before this file
was written.

Three tranches were then built to fix three named organs. P-C2 is the
rematch that says whether they did.

---

## §2 — The instance, the question, and the checker: ALL REUSED, UNCHANGED

**Nothing about the problem may move**, or the rematch measures the
instance instead of the rebuild.

| input | source | how reuse is enforced |
|---|---|---|
| instance | Heilbronn N = 13, unit square | inherited, not re-chosen |
| question bytes | `../2026-08-25-change-constructive-frontier/question.py` | IMPORTED, never copied; `question_sha256` asserted equal to `64b724c4118320989925d111501a8e41cd4518d9b631bb81a6ae048d3cfb5c7e` by `preflight_pc2.py`, which exits non-zero on any drift |
| exact checker | `.../checker.py` | IMPORTED; `checker.py --self-test` (9/9) and `mutation_proof.py` re-run in the ladder |
| in-run battery | `.../criteria.py` | IMPORTED; `preflight_criteria.py` re-run in the ladder |
| ARM S script | `.../arm_s.py` | INVOKED DIRECTLY, no wrapper: it already takes `--token-budget` and `--out`, so P-C2 adds nothing to it. `preflight_pc2.py` does not need to guard a copy because no copy exists |
| registered floor | 0.005 | inherited |

**The checker is NOT rewritten.** P-C1's split stands and is restated so no
reader has to re-derive it: `criteria.py` is the IN-RUN admission battery
(float64, inside the sandbox, which offers `re` and no rational type);
`checker.py` is the OFFLINE AUTHORITY (exact rationals, `Fraction`) for
every number this document reports. The measured float-vs-exact gap is
9.46e-17 over 20 000 configurations and the battery's slack is 1e-12, i.e.
one-sided in the permissive direction, so float error can never refute an
honest construction.

**A stronger road was checked and is closed, and it is recorded rather than
worked around.** Running `checker.py` ITSELF in-run through the
`candidate_checker` program would give exact arithmetic inside the cycle.
`oracle.py`'s sandbox forbids imports (`_guard`: "imports are not
allowed"), and `checker.py` needs `fractions`, `re` and `itertools`. So the
in-run battery stays the float64 predicate form, exactly as P-C1 froze it.

---

## §3 — What is actually different this time, stated mechanically

P-C1 already EXECUTED every candidate on arrival: `rules/crit.py::
crit_program` evaluated each commitment and, on FAIL, minted a
DEMONSTRATIVE fail warrant through `rules/warrants.py::
register_fail_warrant`. It did that 117 times. **The refutations then went
nowhere** — W2 measured the general form of this exactly: 0 of 196 LLM
attacks ever reached a later conjecture dispatch.

The operator's design line for P-C2 is "Otherwise how is an LLM supposed to
test code". The mechanical content of that line, on this tree, is that the
refutation must reach the writer IN THE CYCLE IT IS MINTED. Three delivered
tranches supply that, and each is verified present on main before launch:

1. **F1 — the discharge channel.** `register_fail_warrant`'s critic
   artifact carries a `Warrant` whose `target` is the candidate, which
   `adjudication/edges.py::build_att` turns into an ATTACK EDGE, which
   `discharge/channel.py::_open_with_total` reads. With the channel on, the
   refutation renders as an OPEN CRITICISM inside the conjecturer's binding
   block at pack priority 2 (beside `criteria`, non-droppable,
   non-compressible), and the next candidate must carry a typed discharge —
   `revised`, `rebutted` or `departure_declared` — per handle. So an
   inflated claim is executed, refuted by computation, and put in front of
   the writer as something it must answer. **That is the whole change.**
2. **F2 — reference menus.** Legal handle sets render next to every
   reference-bearing field. No configuration; on by construction.
3. **F3 — channels on by default + the wander floor.** Research,
   simulation and code-testing default ON; the wander cap defaults to 0.5.
   No configuration; on by construction.

### FINDING F-A, registered before launch, and the deviation it forces

**F1's channel could not be turned on by any run on this tree.** Proven by
compilation, not by reading:

    source config DISCHARGE_POLICY = discharge-required.v1
    engine_config_json has DISCHARGE_POLICY: False
    RUNTIME config DISCHARGE_POLICY = off

`run_manifest.py` pops `DISCHARGE_POLICY` from the manifest's config echo
(deliberately, to keep every qualification subject digest still), and the
one run path — `application/text_runs.py::start_manifest_run`, the
operations-parity law's single entry — rebuilds Config with
`config_from_run_manifest`. The field therefore falls back to its code
default, `"off"`, whatever any YAML says. `Config` is a plain `BaseModel`
with no environment source, so there is no env road either.

This is a FINDING AGAINST R12–R15 (the modularity law: every behaviour
reachable as CONFIGURATION or a REGISTERED VERSIONED ARTIFACT, never by
editing code). F1's own DELIVERY.md states the hand-off — "The channel
ships OFF — turning it on is a Config default and belongs to F3" — and F3
did not take it: `grep -i discharge` over the whole F3 tranche returns
nothing.

**DEVIATION D1, ledgered.** The smallest lawful wiring is the one-line
default F1 named and F3 dropped: `Config.DISCHARGE_POLICY` becomes
`"discharge-required.v1"`. It touches no frozen surface, moves no manifest
byte, changes no qualification subject digest, and is exactly the decision
F1 deferred. It is a `src/` change, which this tranche's brief otherwise
forbids; it is taken under the brief's own clause ("the smallest lawful
wiring is used with the deviation ledgered") and is recorded here, in
RESULTS.md, and in `docs/ERRATA.md`.

**What D1 does NOT do:** it does not make the channel reachable as
configuration. A run that wanted the channel OFF still cannot express that
through a manifest. F-A therefore stays OPEN as a defect after this
tranche, and PARKED.md carries its fix prompt. P-C2 works around F-A; it
does not close it.

---

## §4 — ARM H2, the rebuilt harness

Identical to P-C1's ARM H in every field except the discharge channel, so
that any difference in outcome is attributable to the rebuild and not to a
re-tuned launch.

| field | value | same as P-C1? |
|---|---|---|
| model | `glm-5.2`, solo, all 11 canonical roles, one route | yes |
| cycles | **24** | yes |
| token budget | 3 000 000 (cap) | yes |
| judges | **NONE** — `JUDGE_SEATS_ENABLED: false`, `rubric_policy: forbid` | yes |
| criticism | `ENGAGED_CRITICISM_AUTHORITY: defended_trial`, legacy off | yes |
| dossier | EMPTY; attached evidence OFF | yes |
| max_tokens | 32768 | yes |
| **discharge channel** | **`discharge-required.v1` — ON** | **NO. This is the tranche.** |
| reference menus (F2) | on by construction | NO — new since P-C1 |
| evidence channels (F3) | research / simulation / code-testing default ON | NO — new since P-C1 |
| wander floor (F3) | 0.5 | NO — new since P-C1 |

Refutation remains DEMONSTRATIVE. No seat rules on a number, anywhere.

**A NEW OPERATIONAL DEATH IS A PARKED DEFECT, NOT A RESULT.** If ARM H2
dies in a way the soak did not predict, it is reported plainly as a defect
the soak missed, the tranche STOPS, and no verdict under §6 is claimed.

---

## §5 — ARM S2, the sampling baseline, re-run

The identical script, at the matched budget, on FRESH SAMPLES. P-C1's
cached best is NOT reused: a rematch against a stored number would be a
rematch against one draw of the baseline's luck.

| field | value |
|---|---|
| model | `glm-5.2` — the same model |
| prompt | §2's bytes, verbatim, through the shared `question.py` |
| temperature | 1.0, set explicitly (P-C1's registered reason stands: a near-deterministic sampler is a trivially weak baseline and would flatter the harness for the wrong reason) |
| max_tokens | 32768 — the same seat cap as ARM H2 |
| memory | NONE. No sample sees another sample, its score, or any history |
| scoring | the same exact `checker.py`; best VALID kept |
| machinery | none — `arm_s.py` imports `checker` and the standard library, nothing from `deepreason` |

### Matched budget, registered rule (unchanged from P-C1 §4)

Matching is on **measured actual spend**, never on the registered cap.

1. ARM H2 runs first; its provider-counted total is `T_H`.
2. ARM S2 samples until cumulative provider-counted tokens would exceed
   `T_H`.
3. RESULTS.md quotes `T_H` and `T_S` side by side.
4. **If `T_S < 0.95 * T_H` the comparison is reported as UNMATCHED and no
   margin is claimed.**

`T_H` is summed from the log's `llm` blocks, not from `deepreason results`'
token counter, which read 0 after 292 provider calls in P-C1 and is parked
as that tranche's P2.

---

## §6 — THE REGISTERED VERDICT, kill-or-cure

Stated verbatim, and written here so nobody can soften it later:

> **Value is claimed if and only if `best_H2 > best_S2`. If that condition
> is not met, the REBUILD program's answer is CURE FAILED, and the
> retirement road is the operator's next decision.**

`best_H2 == best_S2` is NOT a margin. A loss is a loss whatever the report
card in §7 says.

---

## §7 — THE REPORT CARD

Secondary metrics, each measured with a COMMITTED instrument run unmodified
on the new root, each against its stated P-C1 baseline. These do not change
the §6 verdict; they say WHICH ORGAN the rebuild fixed, so that a loss with
validity at 60 % and positive coupling is legible as a DIFFERENT loss from
P-C1's.

Each row names its baseline precisely, because two different "validity
rates" exist in the committed record and conflating them would manufacture
a result.

| # | metric | instrument (reused, not rewritten) | P-C1 baseline | source of the baseline |
|---|---|---|---|---|
| C1 | **construction validity rate** — checker-confirmed constructions / constructions the model wrote | `W1-form-census/pc1_headline.py` (`constructions_from_root` → `mechanism`, which runs the committed checker) | **ARM H 11.28 %** — 15 VALID of 133, the MECHANISM census, which is what runs on a bare root. The 11.36 % / 43.4 % figures elsewhere are ARTIFACT-level (15 of 132; 23 of 53) and are quoted separately; the two are not interchangeable | `W1-form-census/PC1_HEADLINE.json` (`mechanism.arm_h` and `arm_h`/`arm_s`) |
| C2 | **invented-handle rate** — `V6_WIRE_REFERENCE_INVALID` + `SCRATCH_ALIAS_UNKNOWN` + `BRIDGE_WIRE_REFERENCE_INVALID` as a share of wire failures | `W1-form-census/census.py::census_root`, against the COMMITTED `MESSAGE_CODE_TABLE.json` | **on P-C1's own root: 2 of 77 wire failures = 2.6 %; wire validity 87.67 % over 292 attempts.** The 62.6 %-dominant figure F2 cites is a 54-ROOT POPULATION figure (737 of 1 178), NOT P-C1's root. Both are quoted; neither is substituted for the other | `W1-form-census/CENSUS_PER_ROOT.json`; F2 DELIVERY.md |
| C3 | **placebo-corrected coupling** — does criticism change the next candidate more than a placebo would | `2026-08-26-run-anatomy-w2-criticism/q5.py` + F1's `coupling.py` | **R1_mechanical `CouplingRate − Placebo` = +0.0587** (coupled 32, neglected 309, NeglectRate 90.6 %); **R2_prose_quote = 0.0 and is INADMISSIBLE as a rate** by W2's own residue. The brief's "was ≤ 0" is W2's LLM-attack sub-population finding — 0 of 196 attacks reaching a later conjecture dispatch — and is quoted as that | `w2-criticism/pc1_q5.json`; F1 DELIVERY.md |
| C4 | **operator-question budget share** | `W6-token-flow/pc1_postmortem.py` | **53.2 %** (61 calls, 373 903 tokens); `audit:ritual` took 41.2 %; repair re-asks 5.6 % | `W6-token-flow/RESULTS.md`, `PC1_POSTMORTEM.json` |
| C5 | **tokens per valid candidate** | derived: `T_H / valid_constructions` | **702 789 / 15 = 46 853** | P-C1 RESULTS.md |

A metric whose instrument cannot run on the new root is reported as NOT
MEASURED, with the reason. It is never estimated.

---

## §8 — The repeat, and how any margin may be quoted

**One repeat is pre-authorized.** Run identity is deterministic, so a
repeat uses a separate `DEEPREASON_HOME` and a distinct root path
(`PC2_HOME` / `PC2_ROOT`); the question bytes stay identical, which is the
point of a repeat.

**Any single-run margin is quoted as a single-run margin, with BOTH arms'
spread of valid scores stated** — the control-vs-control clause. P-C1's
residue records that its own repeat was authorized and never spent; if this
one is not spent either, RESULTS.md says so in those words.

---

## §9 — HONESTY LINE, pre-registered

**This run bears on, but does not replace, the parked four-arm criticism
A/B** (F1's PARKED.md P2: no-critique / vacuous-critique / real-as-advice /
real-in-context). P-C2 has TWO arms, and its ARM H2 changes THREE organs at
once plus a deviation. Therefore:

- A P-C2 win cannot attribute itself to the discharge channel, or to the
  reference menus, or to the evidence channels. It says the rebuilt harness
  beat sampling; it does not say which organ did it.
- A P-C2 loss cannot acquit any one of them either.
- Without the VACUOUS-CRITIQUE arm, a working critic cannot be
  distinguished from argument-shaped text. P-C2 does not contain that arm
  and cannot make that distinction.

P2 remains the proof this tranche is not a substitute for, and RESULTS.md
repeats this sentence.

---

## §10 — What P-C2 cannot settle, registered in advance

- **One instance, one N, one model, one problem family.** A margin here is
  a margin here.
- **Capability-channel use is stochastic across identical runs**
  (CLAUDE.md). One live attempt that misses a path is inconclusive for that
  path; the offline regression remains the proof.
- **It cannot say the best-known value was reached.** No published record
  is consulted. ARM S2 is the comparator.
- **"Accepted" still does not mean "true"** — though on this instance
  acceptance is a computation over the candidate's own bytes, not a status
  a seat conferred.
- **F-A is not closed by this tranche.** The channel is on because a code
  default was changed, not because a configuration can select it.
- **The soak is not full coverage.** `cycle_soak.py` has REPRODUCED one of
  the four 2026-08-22 operational deaths offline; the other three are
  asserted, not demonstrated. A green soak licenses the launch; it does not
  guarantee it.

---

## APPENDIX A — 2026-08-26, post-launch: ARM H3, the harness with thinking ON

**Appended, never an edit.** §1–§10 stand exactly as registered, and the
ARM H2 / ARM S2 comparison they govern is reported as registered.

### What was found, after ARM H2 had run

**The two arms were not running the same model configuration.** Measured by
two calls to the same endpoint with the same frozen question bytes,
differing in exactly one field (`reasoning_probe.md`):

| | ARM S2's shape (no reasoning field) | ARM H2's shape (`reasoning_effort: "none"`) |
|---|---|---|
| completion tokens | **9 712** | **177** |
| visible content | 326 chars | 326 chars |
| reasoning payload | **24 409 chars** | **0** |

The harness runs glm-5.2 with THINKING DISABLED; the sampler runs it with
THINKING ON. `reasoning: "none"` is inherited unchanged from P-C1's
`run-config.yaml` — §4 required P-C2 to differ from P-C1 in exactly one
field, and it does — and `arm_s.py` has never sent a reasoning parameter.
The codebase had already measured this and recorded it at
`llm/providers.py::reasoning_disabled` ("Unset is NOT off"); nobody
connected that note to this experiment.

**Scope: P-C1's committed 33x result carries the same confound**, and so
does anything derived from it.

### The operator's ruling, 2026-08-26

Presented as a four-way fork with a recommendation. The operator chose
**"Re-run the harness with thinking ON"** — the fairer test of the harness at
full strength, over the cheaper matched-sampler road this document's author
recommended. That ruling is the authority for everything below.

### ARM H3, registered before any provider call

Identical to ARM H2 in every field except the one named:

| field | ARM H2 | ARM H3 |
|---|---|---|
| `reasoning` on every seat | `"none"` (thinking OFF) | **UNSET (thinking ON)** |
| everything else | — | unchanged: solo glm-5.2 across 11 roles, 24 cycles, 3 000 000 token cap, no judges, `rubric_policy: forbid`, empty dossier, `max_tokens` 32768, `DISCHARGE_POLICY: discharge-required.v1` |

`preflight_pc2.py`'s S2 check is amended for this arm ONLY, to assert a
TWO-field delta from P-C1's config (`DISCHARGE_POLICY` and `reasoning`) and
to fail on any third. S1, S3 and S4 are unchanged and still binding.

**The ARM H2 root is NOT overwritten and NOT renamed.** It stays at `run/`,
where committed evidence already references it; ARM H3 takes `run_h3/`. A
new `reasoning` value mints a new manifest and therefore a new run id, so
the two roots cannot contend.

**NO SOAK. Operator ruling, 2026-08-26, verbatim: "No new soak. just
requalification".** The soak law ("the rebuilt config is a NEW case ... run
it, paste exit 0") is WAIVED for ARM H3 by the operator, on the record, and
this is what that costs, stated so nobody has to reconstruct it later:

- The soak is what licenses a launch against the four 2026-08-22 cycle-0-to-2
  operational deaths. ARM H3 launches without that licence.
- It is a smaller gap here than it would be in general, and the reason is
  measured rather than argued: ARM H3's shape differs from the shape the
  `pc2` case DID soak (exit 0, 24 of 24 cycles, verify_root clean, A5/A6
  green) in exactly one field, `reasoning`, which changes what the PROVIDER
  does with a request and touches no harness code path. The soak's stub
  ignores the field entirely, so a `pc3` soak would have driven byte-identical
  machinery and returned the same green.
- What a soak could NOT have caught here anyway is the death ARM H2 actually
  hit — `conjecturer.atomic-candidate.v1` seat exhaustion — because a
  deterministic stub always answers schema-valid and can never drive a repair.
  §10 registered that limit before launch and the soak states it in its own
  output.

**Requalification is NOT waived** and is the operator's stated requirement.
`reasoning` is part of the route spec and therefore of the manifest, so the
qualification subject digest moves and the full battery reruns (~14 min,
~1160 calls). That is by design, not a fault.

**Re-qualification is expected and budgeted.** `reasoning` is part of the
route spec and therefore of the manifest, so the qualification subject
digest moves and the full battery reruns (~14 min, ~1160 calls). That is by
design, not a fault.

### How ARM S is matched to TWO harness arms — REGISTERED NOW, BEFORE T_H3 IS KNOWN

This rule is written down before ARM H3 runs so it cannot be chosen after
the numbers are in.

ARM S2's samples are i.i.d., blind and one-shot: no sample sees another, and
none sees a score. §5's rule is "sample until cumulative provider-counted
tokens would exceed `T_H`". That rule is applied to the SAME sample stream
at each arm's own `T_H`:

- **ARM H2's comparison** uses the prefix of the stream whose cumulative
  tokens do not exceed `T_H2` = 1 193 009.
- **ARM H3's comparison** uses the prefix whose cumulative tokens do not
  exceed `T_H3`, measured the same way after ARM H3 stops. If `T_H3` exceeds
  what the stream has reached, the sampler is RESUMED with the remainder,
  exactly as P-C1's ARM S was resumed three times.

**The cut is by CUMULATIVE TOKENS ONLY, never by score**, and the
admissibility floor `T_S / T_H >= 0.95` of §5.4 applies unchanged to each
comparison separately. A prefix chosen for its best score would be
fabrication, and `merge_arm_s2.py` takes the cut as a parameter so no human
picks it.

### What ARM H3 can and cannot settle

- It CAN say whether the harness, at the model's full strength, beats blind
  sampling at matched measured budget on this instance.
- It CANNOT rescue §6's verdict for ARM H2. That verdict was registered and
  is reported as registered, whatever ARM H3 does.
- It CANNOT isolate the discharge channel, the menus or the wander cap from
  each other; §9's honesty line binds ARM H3 exactly as it binds ARM H2.
- **Thinking ON changes the budget shape.** ARM H2 spent 27.5 % of its
  tokens on completion; with thinking on that share should rise sharply, so
  ARM H3 may reach FEWER cycles inside the same 3 000 000 cap. A shallower
  run is a real outcome and is reported as one, not as a fault of the cap.

### APPENDIX A — AMENDMENT 1, 2026-08-26: the completion cap

**Appended, never an edit.** Appendix A's ARM H3 table is amended in one
field, on the operator's instruction, and the first ARM H3 attempt is
RETIRED rather than deleted.

**What happened.** ARM H3 launched at ARM H2's `max_tokens: 32768` and
truncated **2 of 2 calls**: reasoning alone consumed 32 445 and 32 632 of
the 32 768 cap, so the reply was cut off mid-JSON and arrived invalid both
times (`truncated=True`, `natural_stop=False`, `arrival_valid=False`). It
was still at cycle 0 after ~40 minutes at 60 757 tokens per call, which the
3 000 000 cap would have exhausted in ~49 calls. That is not the harness at
full strength; it is the harness strangled by a cap sized for thinking-OFF.

CLAUDE.md's ledgered response to exactly this signature: **"a bigger cap,
not a diagnosis."**

**The operator's instructions, verbatim, in order:**

> "No new soak. just requalification"
> "pump to 100000"
> "no just do it. tokens are cheap"

**The amendment.** `max_tokens` becomes **100 000** on every seat, for ARM H3
only. ARM H3's registered delta from P-C1's config is therefore now TWO seat
fields — `reasoning` REMOVED and `max_tokens` raised — plus
`DISCHARGE_POLICY`. `preflight_pc2.py`'s S2 asserts both VALUES, not just the
field names, so a cap that drifted to a third number fails.

**No soak, again on the operator's ruling.** Requalification is not waived:
`max_tokens` is part of the route spec, so the subject digest moves and the
battery reruns.

**A CONSTRAINT NOBODY ENFORCES, recorded before launch so it is not a
surprise afterwards.** `Adapter._completion_cap` books
`min(settled, route ceiling)` and does NOT subtract the prompt. A 100 000
completion cap against a 131 072 context window leaves **31 072 tokens for
the prompt**, and the retired attempt's second call already carried a
**45 045-token prompt**. Whether the provider caps, errors, or truncates when
prompt + cap exceeds the window is UNMEASURED. The operator declined a probe
("no just do it. tokens are cheap"), so this is registered as a live risk: if
it bites it will surface as a typed seat failure, and RESULTS.md will report
it as this amendment's own cost rather than as a property of the harness.

**The retired attempt is kept as evidence**, at
`retired-truncation-cap32768-run-58fb0d20488be869/`. It is NOT an ARM H3
result and is never quoted as one — it produced no cycle and no valid
candidate. It is the measurement that motivated this amendment, and it
stands as a recorded fact in its own right: **at 32 768, thinking-ON glm-5.2
cannot answer this question at all** — reasoning alone fills the cap.

**ARM S2 was stopped in the same operation** that stopped ARM H3 and is
RESUMED, not restarted: `arm_s.py` appends to `results.jsonl`, 34 samples and
226 986 tokens were already on disk, and P-C1's ARM S was resumed three times
by the same mechanism. The §5.4 admissibility rule and Appendix A's
shared-stream rule are unchanged and still bind.
