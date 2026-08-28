# PARKED — found here, not fixed here

Nothing in this file was implemented. Each entry is one line of WHAT and a
ready-to-send prompt, so the follow-up costs the operator a paste rather than
an authoring session.

---

## P1 — R3's calibration experiment: settle the three model-specific items locally

**What.** The research note's §(b) items are explicitly NOT implemented on the
papers' word: which pre-question slot is best, which rendering format, and how
much retrieval depth. All three "need local re-testing per model. None
transfer." This tranche fixed only the four robust rules. Three knobs on
`RenderLayoutPolicyV1` — `live_verbatim_n`, `distilled_head_chars`,
`superseded_summary_n` — are set from judgement, not measurement, and
`superseded_summary_n` ships at 0 precisely so a run can settle it.

**Route.** A standalone live experiment (not a change tranche): pre-register,
run, record, stop. It writes only in its own experiment directory.

```
Run a pre-registered live calibration sweep that settles, on the bench model
(glm-5.2 on Ollama Cloud), the three model-specific layout items this tree
deliberately did not implement on the research literature's word.

SETUP
- git fetch origin main && git checkout -B claude/layout-calibration origin/main
- pip install -e . --break-system-packages -q; pip install jsonschema
  --break-system-packages -q
- deepreason embedder-warmup   (pay the ~523 MB fetch where you can see it)
- Recreate experiments/*/env (OLLAMA_API_KEY=...) from the operator's
  handover; it is gitignored and never committed.
- Read CLAUDE.md in full. Read docs/map/INV-render-layout.md and
  experiments/2026-08-28-change-render-layout-robust/CENSUS.md before
  designing anything: the census is the BEFORE measurement and this sweep is
  the AFTER, so use its instrument (tools/prompt_census.py) unchanged.

AUTHORITY
The operator, 2026-08-28: "tokens are cheap. You are not. So any experiments
with token spend that can settle things is preferred." This is a token-spend
experiment by design; do not economise it into inconclusiveness.

WHAT IS ALREADY SETTLED, AND IS NOT UNDER TEST
The four robust rules ship and are gated by render-layout.v1: nothing
load-bearing after the question, an instruction ceiling of 40 (measured
maximum 28, already met), distilled carry-forward with an in-band retrieval
note, and merged head label blocks. Do NOT re-test those. Test only the
three below, each of which is a knob whose value was chosen by judgement.

THE THREE FACTORS
F1  Pre-question slot. The tree puts the task frame in the role template
    ahead of everything and the question last. The untested question is where
    the INSTRUCTION BLOCK sits relative to the schema and the pack head.
    Arms: instructions-first (today), instructions-immediately-before-the-
    question, instructions-in-both-places.
F2  Rendering format of the carried-forward block. Arms: the shipped
    "- <id>: <claim>" line list; a markdown table; plain prose sentences.
    Record token overhead per arm as well as outcome -- the note's own
    numbers are markdown +26%, prose +22%, table +37% over plain, and whether
    that holds here is itself worth knowing.
F3  Retrieval depth: how much prior round is shown. Arms are policy values,
    registered through register_layout_policy so no consumer is edited:
      live_verbatim_n in {0, 2, 4}
      superseded_summary_n in {0, 3}
    The second factor is the one this tranche most wants settled: superseded
    material ships omitted, and whether showing refuted claims as one-line
    summaries helps a conjecturer avoid repeating them, or merely revives
    them, is an empirical question nobody here has answered.

DESIGN
- Pre-register BEFORE the first call: arms, seed questions, cycle count,
  budgets, and the decision rule for each factor, in PREREG.md, committed.
  A result that was not pre-registered is not a result.
- Run each arm as a separate DEEPREASON_HOME with its own root. Run identity
  is deterministic (same question + config -> same run id), so vary the
  policy id, not the question, and retire any leftover root by git mv before
  relaunch -- committing the rename FIRST.
- No live launch without a green soak: python -u scripts/cycle_soak.py
  --case <case> on each launch configuration's own shape.
- Launch detached from the ladder's directory: setsid nohup ./<ladder>.sh &
  disown. Arm the snapshot loop and a monitor on progress.jsonl.
- At least 3 seed questions x every arm, so a single hard question cannot
  carry a factor. Prefer more arms over more cycles per arm.

MEASUREMENT -- typed outcomes only, and state the unit
- Primary: cycles to first ACCEPTED artifact, and survivor count at the
  terminal cycle, from deepreason results --json.
- Secondary, and the one the literature is thinnest on (the note's own
  section (c) names this exact gap): DISTINCT-hypothesis count across
  cycles, measured on the committed artifacts, not on model prose.
- Cost: prompt tokens per cycle per arm, from the recorded attempts.
- Run tools/prompt_census.py over the new roots and table it against
  CENSUS.md's numbers. That is the before -> after this tranche could not
  produce, because it has no live run of its own.
- Model prose is NEVER evidence. log.jsonl, objects/, run-status.json,
  verify_root and the audit JSON are.

WHAT TO DELIVER
RESULTS.md as a dated honest-ledger segment: what the record shows, and the
residue -- what remains unproven. A negative or inconclusive result is
recorded as one; "accepted does not mean true". If a factor does not
separate, say so and say what sample would have separated it. Then, and only
then, one follow-up change tranche per factor that DID separate, each
proposing the specific RenderLayoutPolicyV1 default to move and citing the
run ids that justify it.

DO NOT change any default in llm/layout.py in this experiment. Register new
policies; leave render-layout.v1 alone. Changing a shipped default is a
change tranche, and it needs this experiment's evidence first.
```

---

## P2 — the qualification probe carries the old judge shape

**What.** `src/deepreason/cli/doctor.py:900` builds the qualification
battery's judge probe with the pre-2026-08-28 arrangement — `QUESTION:` before
the case and the defence. The runs now use question-last. The battery
therefore qualifies a model on an arrangement the run no longer sends.

**Why it was not fixed here.** Changing that string changes what the battery
tests, and the tranche instruction's C3 forbids moving a qualification subject
without stopping to ask. It was left alone deliberately, and
`INV-render-layout.md`'s Traps section carries a check that pins the
divergence so it cannot be forgotten.

```
Bring the qualification battery's judge probe into line with the arrangement
runs actually dispatch.

Route: dr-change-orchestrator (this is a change, not a defect).

One goal: src/deepreason/cli/doctor.py's judgeruling probe renders
question-last, matching informal/trial.py since 2026-08-28.

BEFORE ANY CODE, establish and report to the operator whether this moves a
qualification subject digest. The evidence is already gathered:
qualification.py::qualification_subject_payload folds the compiled MANIFEST
into the subject, not doctor.py's probe prose, so the digest may well be
untouched -- but the 2026-08-28 tranche did not need to prove it and so did
not. Compute the digest before and after on the same manifest and paste both.
If it moves, STOP and ask; the operator has granted no exception.

Evidence pointers:
- experiments/2026-08-28-change-render-layout-robust/SPEC.md section 1.3
- docs/map/INV-render-layout.md, Traps, third entry (its check pins the
  divergence and must be updated in the same commit)
- src/deepreason/cli/doctor.py:887-906

End state: the probe and the run agree, the digest question is answered with
a pasted computation either way, and INV-render-layout.md's Traps entry is
rewritten to say when it was closed rather than deleted.
```

---

## P3 — six seats state no question in their pack at all

**What.** The census found six seats — defender, config-referee, two
summarizer contracts, two thesis contracts — whose pack carries no question
and whose task lives only in the role template at the head of the prompt.
That is the research note's own recommended slot for a task frame, so it is
not a violation of the robust negative rule, and R1's closure rule forbade
churning it. But it means those seats read every byte of their material after
being told the task once, at the top, and none of them gets the late
restatement the conjecturer, critic and judge now get.

**Why it was not fixed here.** Adding a late restatement to a seat that does
not violate the rule is work the requirement did not license. It is also the
seat set that is NOT on the section IR — `render_batch_crit_pack`,
`render_experiment_pack`, `render_property_pack`, `render_cx_retry_pack` all
return a raw prefix clip — so the work is entangled with moving them onto the
IR, which `DR-CON-packs-and-token-economy` already names as its own task.

```
Decide whether the six seats that state no question in their pack should get
a late restatement, and if so, move them onto the section IR first.

Route: dr-change-orchestrator. This is a DESIGN-AND-STOP: the deliverable at
the gate is a committed design document and an ended turn, not code.

One goal: a written recommendation, with evidence, on whether
render_batch_crit_pack, render_experiment_pack, render_property_pack and
render_cx_retry_pack should move onto the section IR -- and only then whether
the question-last rule should extend to them.

Evidence already on the record:
- experiments/2026-08-28-change-render-layout-robust/CENSUS.md, R1a, the
  "task-frame-only" row: 165 real dispatched prompts across those six seats.
- docs/map/CON-packs-and-token-economy.md, "Only two renderers are on the
  IR", and its "Where to change what" row for moving a legacy renderer.
- docs/map/INV-render-layout.md for the policy the extension would use.

The batch critic is the one to weigh first: it is 1286 of the 2836 measured
first-turn prompts -- by far the most-dispatched seat in the tree -- and it
gets prefix truncation where the single-target critic gets section
allocation. Price that separately from the question-last question.
```
