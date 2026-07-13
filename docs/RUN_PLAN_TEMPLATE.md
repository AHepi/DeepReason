# Run Plan: ______________________________________

*A fill-in-the-blanks plan for attacking one hard problem with DeepReason.
Copy this file, fill every blank, and hand it to the operating agent (the
"driver") together with `docs/AGENT.md`, which defines the rules of
engagement and the tool surface. Blanks look like `____` or `<like this>`.
Sections marked DRIVER are instructions the driver executes; sections
marked PLANNER are filled in by the human before the run.*

---

## 0. Mission (PLANNER)

- **The question:** ____________________________________________
- **Why it matters / who it's for:** ____________________________________________
  (State the intent, not just the request — the driver and the engine both
  perform better knowing what the output enables.)
- **What "done" looks like:** ____________________________________________
  (e.g. "a committed thesis defending the best-supported explanation," or
  "a frontier of ≥N argued survivors with the deciding evidence named.")
- **Total token budget:** ____________ (hard ceiling across all phases)
- **Deadline / wall-clock limit:** ____________

Sanity check before proceeding (see README "When *not* to use it"): the
question must be open, explanatory, and falsifiable in structure. If it is
a lookup, a closed computation, or nothing could count as evidence against
a candidate answer, stop here and use a plain LLM call instead.

---

## 1. Where MiniReason fits (read once, then use throughout)

MiniReason (`mini/`) is the measured reduced engine profile: generate →
shared anti-relapse guard → canonical program checks → stance rotation.
It writes through the same Harness, ontology, grounded/support adjudicator,
warrant plumbing, and append-only log as full DeepReason. The full harness
opens a Mini root with no conversion (`Harness("runs/<root>")`) and keeps
going; `mini/tests/test_graduation.py` holds this guarantee. That makes Mini
safe to use liberally: nothing done in Mini is throwaway.

Use it in three places in this plan:

1. **Problem formulation (Phase 1).** Before spending full-harness tokens,
   run cheap Mini passes over 2–4 rival phrasings of the question. A good
   phrasing produces diverse, falsifiable conjectures; a bad one produces
   paraphrases or candidates whose forbidden cases can't be stated. Pick
   the phrasing with the healthiest spread and carry its root forward.
2. **Stuck-case probes (Phase 4).** When the full run stalls — novelty
   fading, or gate blocks climbing (the orbit signature: a refuted
   attractor the generator can't rotate away from) — spin a fresh Mini run
   on a rotated stance or a re-cut version of the problem instead of
   funding more cycles into the stall. Mini's fast stance rotation and
   problem turnover are the two interventions that measurably restore
   novelty (0.973 vs 0.846 control; turnover 1.12). If the probe finds new
   territory, graduate its root or seed its survivors as follow-up
   problems.
3. **Seat certification (Phase 2).** `judge.certify_seat` re-runs the
   planted-flaw battery against any new provider/model. Re-certify every
   seat before trusting a score from it — certification does not transfer
   across model families.

Graduate from Mini to the full harness when (from `mini/README.md`): base
error is measurably high (trial filtering then has something to filter), or
the workload needs research, informal trials, websites, capture control,
long-horizon scheduling, or a normative cross-family judge ensemble.

---

## 2. Engine configuration (PLANNER)

Config file: `config/____________.yaml` (copy `config/deepseek.yaml`).

| Role | Endpoint | Model | Reasoning | max_tokens | Notes |
|---|---|---|---|---|---|
| conjecturer | ____________ | ____________ | ____ | ______ | json_mode: true |
| critic | ____________ | ____________ | ____ | ______ | |
| defender | ____________ | ____________ | ____ | ______ | |
| judge seat 1 | ____________ | ____________ | ____ | ______ | temperature 0 where supported |
| judge seat 2 | ____________ | ____________ | ____ | ______ | **different model family than seat 1** (§9 cross-family rule) |

Hard requirements (from `docs/AGENT.md`):

- [ ] Every role sets `reasoning` **explicitly** and a `max_tokens` with
      headroom — reasoning-mode models silently burn the completion budget
      and return empty output; suspect the cap before the model.
- [ ] Model ids are pinned (no `auto`) if the run must be reproducible.
- [ ] API keys via environment variables only: `____________`, `____________`
- [ ] Seats certified against the planted-flaw battery on ____ (date),
      results at: ____________

---

## 3. Phase plan

### Phase 1 — Formulate with Mini (DRIVER)

Budget: ____________ tokens. Root(s): `runs/<name>-scout-{a,b,c}`.

1. Draft ____ candidate phrasings of the mission question (planner may
   pre-fill some): 
   - (a) ____________________________________________
   - (b) ____________________________________________
   - (c) ____________________________________________
2. Run each through MiniReason (`mini/scripts/` or `minireason.loop.run`)
   with an equal budget slice.
3. Compare: surviving-conjecture count and distinctness, gate-block count
   (should be ~0 on a healthy problem), and whether forbidden cases were
   statable for most candidates.
4. **Decision gate:** carry forward phrasing ____ because ____________.
   If all phrasings produce paraphrase clusters or unfalsifiable
   candidates, report back to the planner instead of proceeding — the
   question needs re-cutting, and no budget will fix that.

### Phase 2 — Seed the full harness (DRIVER)

Budget: ____________ tokens. Root: `runs/____________`.

1. Either graduate the winning scout root (`Harness("runs/<scout-root>")`)
   or `seed_problem` fresh with:
   - Problem statement: (from Phase 1)
   - Commitments: ____________________________________________
   - Rubric standard: ____________ (e.g. `std-explain`)
2. `verify_root` on the starting root — violations must be `[]`.
3. Fund a small first tranche: `run_cycles(budget=____________)`.

### Phase 3 — Main loop (DRIVER)

Budget: ____________ tokens, funded in tranches of ____________.

Repeat per tranche, per the AGENT.md operating loop:
`run_cycles` → `eval_report` + `frontier` → read `theory`/`why` on
survivors → clear the `docket` (rulings budget: ____ rulings) → decide
where to fund next. Metrics steer attention, never status; verdicts are
computed, never set.

After every tranche, record in the run journal (`____________`):
- tokens spent vs metered (reconciliation must match — stop and
  investigate any divergence before trusting metrics),
- gate blocks this window,
- survivor count and one-line delta.

### Phase 4 — Stuck playbook (DRIVER)

Check these signals every tranche; act on the first that fires.

| Signal | Threshold | Action |
|---|---|---|
| Gate blocks per window | > ____ (healthy is ~0) | Orbit: do NOT fund more cycles. Launch a Mini probe (Section 1.2) with a rotated stance; graduate or seed what it finds. |
| Novelty fading (late ideas paraphrasing early ones) | driver's judgment / late-early < ____ | Problem turnover: seed the strongest open sub-question as a new problem and shift funding to it. |
| Empty/truncated engine output | any | Raise the role's `max_tokens` / check `reasoning` pinning before blaming the model. |
| A verdict the driver believes is wrong | — | Criticize the critic (attack ν via more cycles), never look for an override. |
| Budget ≥ ____% spent, "done" not in sight | — | Stop, write an interim report, return to planner. |

### Phase 5 — Conclude (DRIVER)

Budget: ____________ tokens.

1. `verify_root` one final time.
2. Produce the thesis view (`scripts/thesis.py --root ____ --problem ____`)
   or, if the mission asked only for a mapped frontier, render `frontier` +
   `theory` for each survivor.
3. Deliverables to the planner:
   - [ ] The committed root at `runs/____________` (the log is the real output)
   - [ ] Thesis / frontier report
   - [ ] Run journal with per-tranche accounting
   - [ ] ____________________________________________

---

## 4. Stop conditions (PLANNER)

The driver stops immediately and reports when any of these hold:

- Total budget reaches ____________ tokens.
- Accounting reconciliation diverges and can't be explained.
- ____ consecutive tranches produce no new surviving conjecture and no
  Mini probe finds new territory (exhaustion — an honest terminal state).
- ____________________________________________

Remember when reading the outcome: an empty frontier on a hostile problem
is success; refutations are progress; a budget stop is graceful — the same
root can always be funded further later.
