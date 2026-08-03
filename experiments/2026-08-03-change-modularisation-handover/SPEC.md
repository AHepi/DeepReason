# Spec for: "a handover for a fresh window that can go through this step by step"

Traces: every item cites R/C numbers from REQUEST.md.

## R3 — the Sonnet 5 research, and the R4 condition

Source: the repo's sanctioned model reference (claude-api skill, cached
2026-06-24, cross-checked against its migration guide). Findings that bear on
this handover:

- `claude-sonnet-5`: 1M context, 128K output; near-Opus quality on coding
  and agentic work; the recommended Sonnet-tier model. Materially below
  Opus 5 / Fable 5 on the deepest long-horizon autonomous work — which is
  exactly what a multi-tranche engineering program is.
- **Interprets instructions literally and explicitly.** It does not
  silently generalize an instruction from one item to another, and does not
  infer requests that were not made. Scope must be stated explicitly
  wherever an instruction should apply broadly.
- **Well-specified up-front prompts maximize its autonomy and intelligence;
  ambiguous or progressively-revealed instructions reduce efficiency and
  sometimes performance.** Complete per-step specifications beat hints.
- Strong instruction-following means guardrails written down are actually
  honored — the inverse risk is under-generalization, not disobedience.

Capability judgment (the R4 condition): **hopeful with guardrails, not
unconditionally.** Sonnet 5 executing THIS repo's machinery — checklists,
machine-decidable criteria, typed records, the two orchestrators plus the
two cross-cutting skills — is a good fit for well-bounded execution (ladder
rungs 1–3). It is a poor fit for unsupervised design judgment near frozen
surfaces (rungs 6–7) and for improvising when a spec is silent. The
condition FIRES, at "slight" magnitude: the handover itself is written
Sonnet-calibrated, and one small documentation modification is made
(S3 below). No wholesale doc rewrites — this session already built the
onboarding path (C4) and the question discipline Sonnet 5 will need.

## Items

S1 (R1, R2, C1, C3, C5): NEW `docs/HANDOVER_2026-08-03.md` — the handover,
structured for a literal executor:
  a. Read-first list (CLAUDE.md → dr-drive-harness → skills README →
     ERRATA → newest RESULTS → this file), each with one line on why.
  b. Executor calibration section addressed to Sonnet 5, derived from R3:
     complete specs are provided per rung — execute them exactly; where a
     spec is silent, that is a question (dr-ask-the-right-question), never
     a license to generalize; one rung per tranche minimum; never begin
     rung N+1 in a tranche that touched rung N.
  c. THE PROGRAM: the seven-rung modularisation ladder, each rung with:
     route (which orchestrator/skill), goal, in-scope, NOT-in-scope,
     machine-decidable acceptance, and stop conditions. Execution classes
     stated per rung: rungs 1–3 EXECUTE; rungs 4–5 EXECUTE WITH NAMED
     GUARDRAILS (no manifest/digest fields without operator approval —
     fingerprints ride Config/typed records; live A/B needs
     operator-provided credentials); rungs 6–7 DESIGN-AND-STOP (produce
     SPEC/FIX and await the operator; frozen-adjacent).
     Rung 1 absorbs the parked R8 job (C5).
  d. Standing rules across all rungs: frozen surfaces, the two instruments
     (gate + 42-row sweep, cite the instrument with the number), commit
     cadence, PARKED discipline.
  e. Environment facts that bit this session: rollback resync,
     `python -m pytest` only, dev deps not restored by bare
     `pip install -e .` (jsonschema/pytest/pytest-xdist — ERRATA-adjacent),
     credentials gone (recreate from operator), sweep baseline 42 rows by
     the committed instrument, the parallel-load flake.
  f. Open items carried forward, explicitly NOT part of the program
     (census delta, ladder-audit fixes, flake, prose-immunity price, dead
     Config value, batch-pack clip, Sweep ratchet).
    accept: file exists; grep hits for `claude-sonnet-5` or "Sonnet 5",
    all seven rungs, "DESIGN-AND-STOP", `dr-drive-harness`,
    `dr-ask-the-right-question`, both orchestrator names, `R8`;
    read-first list present.

S2 (R3): the research and judgment are recorded — this section is the
artifact; DELIVERY reconciles R3 against it.
    accept: SPEC.md contains "## R3 — the Sonnet 5 research".

S3 (R4, condition fired, "slight"): ONE addition to
`.claude/skills/dr-drive-harness/SKILL.md` — a short "Calibration for
less capable executors" block before the exit criterion (~10 lines,
model-agnostic wording): documents here are complete by design — execute
them literally; never generalize an instruction beyond its stated scope;
a silent spec is a question, not an invitation; multi-step programs run
one step per tranche; stop conditions are hard stops.
    accept: `grep -c "Calibration for less capable executors"
    .claude/skills/dr-drive-harness/SKILL.md` -> 1; docs_verify stays
    green.

## Assumptions (operator may override)

A1 (location): `docs/HANDOVER_2026-08-03.md`, by the precedent of
`docs/HANDOVER_2026-08-02.md` which the operator called well-structured.

A2 ("go through this step by step"): the fresh window executes the ladder
rung by rung with the per-rung gates above — NOT the whole ladder in one
session, and rungs 6–7 never without operator approval. Smallest reading
consistent with C1 (the orchestrator ceremony) and the frozen-surface law.

A3 (research scope): the sanctioned in-repo model reference suffices; no
web search added. It is the repo's own designated authority for Claude
model facts and is current past Sonnet 5's release.

A4 ("documentation" in R4): the handover plus one slight dr-drive-harness
addition. CLAUDE.md and README are untouched — they were refreshed this
session and nothing in the R3 findings invalidates them.

## Questions for operator

None (all four assumptions dominant under recorded values — smallest
correct change, tight integration, operator attention conserved).

## Out of scope (explicit)

- Executing any ladder rung — this tranche writes the handover only.
- New skills or workflow changes — not requested.
- Web research beyond the sanctioned reference — A3.
- Re-tuning existing skills' wording for Sonnet 5 beyond S3 — the skills
  were already written for less capable readers (the two prior tranches'
  stated purpose).

## Budget

~260 lines (handover ~200, skill block ~12, tranche artifacts), zero
`src/` changes, 3 commits. Frozen surfaces touched: none.
