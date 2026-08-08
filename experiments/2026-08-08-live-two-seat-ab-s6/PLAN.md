# Rung S6: the live two-seat A/B — work attribution in the typed record

Head under test: `2e009ba7` (Rung S5 delivered — seats stamped into the
typed record; `docs/proposals/ROLE_SEAT_SEPARATION_PLAN.md`'s own Rung
S6 text, lines 119-126, quoted below).

> ### Rung S6 — the dumb-alternative proof [LIVE A/B, rung-5 template]
> Two-seat live run: conjecturer on one real model, coder/simulation
> seat on a different real model (or MockEndpoint for the offline arm).
> Prove from the record alone: (a) which seat produced every attempt
> (work attribution), (b) the seat stamp matches what setup bound,
> (c) verify_root green, (d) a continuation preserves bindings or
> refuses typed. The offline regression is the proof; one live attempt
> is the demonstration (stochasticity rule).

This is a LIVE-RUN tranche, not a code-change tranche: `src/`, `tests/`,
`tools/`, `docs/map/` stay byte-untouched. Rungs S1-S5 already delivered
every mechanism this rung exercises; this tranche's own artifacts (this
directory) are the entire work product.

## Model choice and rationale (recorded before launch, per instruction)

**Conjecturer/default seat: `glm-5.2` via Ollama Cloud** — CLAUDE.md's
own stated current default, confirmed reachable this session (`GET
https://ollama.com/v1/models` lists it; the operator-handed-over
credential authenticates against it — verified via a direct
`chat/completions` probe returning a MODEL-level error, not an auth
error, for a DIFFERENT, retired model id, which is the positive proof
the credential itself is valid).

**Coder seat (`--seat coder=...`): `gemma4:31b`, same host.** Chosen
for three reasons. First, `coder` is this program's own canonical
worked example — Rung S4's own test suite
(`tests/test_run_preparation_service.py::
test_prepare_with_a_seat_binding_overrides_only_the_bound_role`) binds
`--seat coder=...` specifically, and `GROUP_ROLES["coder"] =
{"property_designer"}` is the one role-group that does NOT overlap
`conjecturer`'s own role set — so binding it is the only way to keep
"conjecturer on one model" and "the other seat on a different model"
literally simultaneously true, matching the plan's own sentence
structure. Second, cheap: 31B parameters, a materially smaller/cheaper
model than the 480B-parameter default this environment's OTHER preset
uses. Third, distinct lineage (Google Gemma vs. Zhipu GLM) with an
already-proven-safe settings profile — `easy.py`'s own `"gemma4_31b"`
preset pins `property_designer` to exactly `temperature=0.7,
max_tokens=4000, provider="ollama", reasoning="none"`, which this
tranche's own profile reuses verbatim rather than guessing.

**Recorded deviation from "cheap-but-different from the Ollama Cloud
roster," found and priced before launch, not glossed:** this container
holds exactly ONE working provider credential (confirmed by checking
`env | grep -i api_key`, `find / -iname credentials`, and
`~/.deepreason/credentials` — all empty of any second provider's key;
the only handed-over credential authenticates against `ollama.com`
alone, confirmed by direct HTTP probe). No second, genuinely
different-provider credential exists to reach for. `gemma4:31b` is
therefore "different" at the MODEL level (different vendor lineage,
different `profile_digest`, different `model_id` — everything the
seat-attribution mechanism actually keys on) but not at the
HOSTING-PROVIDER level the plan's prose likely pictured. Since
"attribution, not quality, is what S6 proves" (operator's own framing)
and the seat-binding/stamping/reader mechanism (S2-S5) is entirely
indifferent to which HTTP host served a call — it keys on
`provider`/`model_id`/`profile_digest`, all of which genuinely differ
here — this substitution still exercises the real mechanism end to
end. Not treated as a stop condition: no frozen surface needs touching
to accept it, and the instruction is explicit that needing one means
leaving the rung's scope.

**A second, independently-discovered risk, priced the same way:**
`property_designer` (the `coder` group's sole role) has NEVER fired on
any committed root in this repository's history (checked: no
`log.jsonl` under `experiments/` or `runs/` contains a
`"role": "property_designer"` LLM-call record). Tracing the gate
(`rules/experiment.py::propose_properties` → `oracle.py::
checker_wf_commitment`) shows it fires only when an ACTIVE commitment
with `eval == "program:property_oracle"` already exists in the run's
own graph — itself typically capability-channel-originated — which
CLAUDE.md's own doctrine already documents as STOCHASTIC across
identical live attempts. This is exactly the plan's own named
"stochasticity rule": if this one live attempt does not exercise
`property_designer`, that is an accepted, typed, non-failure outcome
(not one of the ten budgeted failures), and criteria (b)/(c)/(d) plus
criterion (a) FOR WHATEVER ATTEMPTS DO OCCUR remain fully provable
regardless. The already-delivered offline regression
(`tests/test_seat_bindings_record.py::
test_a_two_profile_home_stamps_both_bound_groups_in_one_run`, Rung S5)
is the controlling proof for the `coder` channel specifically, exactly
as the plan's own words prescribe.

## Design: one home, one ladder, four proofs

`s6_run.sh`: setup (glm-5.2 default; `gemma4:31b` bound to `coder` via
a profile file this ladder writes first) → qualify (fresh home, full
battery + the per-profile loop S4 already delivered) → reason on the
QUESTION below → audit (`s6_audit.py`) → continue (`--budget
cycles=2`, only if the first stop is resumable) → re-audit.

## Success criteria (typed outcomes only, written before launch)

1. setup rc=0; qualify reaches tier=full for BOTH the combination
   subject and (if the per-profile loop surfaces one) the coder
   profile's own subject.
2. reason rc=0; `run-status.json` shows state STOPPED with a typed
   stop_reason.
3. `verify_root` on the root: no violations.
4. `recorded_seat_bindings` on the root (Rung S5's own reader): exactly
   one stamp, naming group `"coder"` with `model_id == "gemma4:31b"` —
   proves (b), the stamp matches what setup bound.
5. Every `LLMCall` event in the log, grouped by `role`: `property_
   designer`'s calls (if any) show `model == "gemma4:31b"`; every other
   role's calls show `model == "glm-5.2"` — proves (a), work
   attribution, for whatever attempts occurred.
6. `deepreason --root <root> continue --budget cycles=2`: either the
   run resumes to a second typed stop with `recorded_seat_bindings`
   still naming the SAME `coder`/`gemma4:31b` binding (bindings
   preserved — a second identical stamp is an accepted shape per Rung
   S5's own Q5/A5 design, since the per-instance emission gate is
   copied from the rung-4 template on purpose), or the continuation
   attempt is refused with a typed `CONTINUE_*` error — proves (d).

Any criterion unmet is recorded as the finding, not smoothed. Model
prose is not evidence anywhere in this plan.

## Question (fresh — run identity must not collide with any prior root)

    When a research team splits work across two different reasoning
    engines with different training histories, the SAME engine that
    authors a claim is often trusted to also check it. Argue for or
    against the claim that separating the authoring engine from the
    checking engine is necessary for a result to count as independently
    verified, and identify what evidence within a single run's own
    record would distinguish genuine independent verification from
    mere restatement. Where a claim can be tested by counting or by
    execution, say exactly what to count or execute.

## Mechanics

- Detached launch from this directory: `setsid nohup ./s6_run.sh &
  disown`; a snapshot loop armed on this experiment dir; a monitor on
  the newest root's `progress.jsonl` plus the driver log's `rc=` lines.
- Credential: `env` file (`OLLAMA_API_KEY=...`) in this directory,
  gitignored (`experiments/*/env` is already covered by `.gitignore`),
  recreated from the operator's mid-turn handover this session — NEVER
  committed, never echoed into any committed file.
- RESULTS.md in this directory gets the dated honest-ledger segment —
  what the record shows, and the residue — plus the numbered failure
  ledger required by the operating instructions.
- Failure budget: 10, tracked in RESULTS.md as it is spent, not
  retrospectively. `--maximum-completion-tokens` raises are knob
  adjustments, not code changes. Dead roots are retired by
  `git mv run-<id> failed-epochN-run-<id>`, rename committed FIRST,
  never editing a committed root's contents.
