# REQUEST — W7, the RUN ANATOMY PROGRAM synthesis

Route: `dr-change-orchestrator`. Tranche dir:
`experiments/2026-08-26-change-run-anatomy-synthesis-w7/`.
Date: 2026-08-26. Branch: `claude/run-anatomy-synthesis-w7-fxpifz`.
Base: `origin/main` at `be9bcff54`.

This tranche WRITES ONE DOCUMENT and nothing else. READ-ONLY on `src/`
and `tests/`.

## The operator's words, VERBATIM

Reproduced rather than paraphrased, because a scope whose authority is a
paraphrase is a scope nobody can audit later.

> TARGET REPOSITORY: AHepi/DeepReason — verify before anything else;
> if based elsewhere, ask the operator to attach it with push access
> and STOP until then.
>
> Synthesis tranche W7 — the close of the RUN ANATOMY PROGRAM: turn
> nine organ reports into one document. Route through
> dr-change-orchestrator (this tranche WRITES one document and
> nothing else). READ-ONLY on src/ and tests/.
>
> SETUP (fresh container): git fetch origin main && git checkout -B
> <your session-designated branch> origin/main; git merge-base
> --is-ancestor be9bcff54 HEAD || re-fetch. pip install -e .
> --break-system-packages -q; pip install pytest pytest-xdist
> jsonschema --break-system-packages -q. Read CLAUDE.md in full;
> load dr-drive-harness, dr-explain-to-operator — and W7 is an
> operator-facing FINAL document, so the communication discipline
> binds it fully: worry-first, every technical term glossed inline,
> one closing analogy.
>
> INPUTS, read IN FULL before writing a word — no new measurement,
> no re-derivation; every claim in the synthesis cites one of these
> by file and line/table:
> - experiments/2026-08-26-run-anatomy-program/ — PROGRAM.md and all
>   six W directories (W1 forms, W2 criticism, W3 evidence/scratch,
>   W4 judge road, W5 signals, W6 token flow), their RESULTS,
>   tables, and parked prompts.
> - experiments/2026-08-25-poietics-program/ RESULTS.md (P-R1 and
>   the strengthened P5) and the P-C1 arm comparison in
>   experiments/2026-08-25-constructive-frontier (or wherever the
>   program doc names it — follow its pointers).
> - The external research notes the findings echo:
>   docs/RESEARCH_STRUCTURED_OUTPUT_COERCION (the 255/257 escape
>   refusal), RESEARCH_FINDINGS_Q1Q10 Q4/Q5 (matched-budget,
>   coupling), RESEARCH_SHAPE_CRITIQUE (expansion-only).
> - docs/LESSONS_LEARNED_2026-08-17.md, for the frame the close
>   should honor: honest ledgers outlive optimistic summaries.
>
> THE DOCUMENT: docs/RUN_ANATOMY_SYNTHESIS_2026-08-26.md, four
> sections, nothing else:
> (1) THE ORGAN TABLE — one row per subsystem the program measured
>     (forms/wire contracts, reference grounding, criticism channel,
>     scratch, evidence citation, judge road + guards, signals,
>     allocation controller, token economy, record/verification):
>     verdict WORKS / INERT / HARMFUL-AS-WIRED / PHANTOM /
>     UNEXERCISED, the one number that earns the verdict, and the
>     citation. No verdict without its number.
> (2) THE CAUSAL STORY OF THE 33x LOSS — a single narrative
>     paragraph per contributing cause, ordered by measured size
>     (the 41.2% self-spawned audit problem; the 24.6% rejected-
>     output share; zero criticism-to-improvement coupling; the 10x
>     collinearity conditioning effect; the invented-handle rate),
>     each tied to its table. State plainly which causes are
>     HARNESS-DESIGN, which are MODEL-BEHAVIOR the harness failed
>     to defend against, and which are WIRING never built (the
>     discharge-required criticism channel; recombination).
> (3) WHAT IS REFUTED, WHAT IS UNEXERCISED, WHAT WORKS — three
>     honest lists. Refuted-as-wired is not refuted-in-principle;
>     say which claims the record actually kills. The record
>     machinery, scratch, the guards, and the two-call protocol
>     belong in WORKS with their numbers.
> (4) THE ROADS, PRICED, NO RECOMMENDATION MADE FOR THE OPERATOR —
>     lay out (a) retire the runtime, keep the method (what
>     transfers, what it costs to close out); (b) rebuild the two
>     dead channels (criticism-into-working-context with discharge
>     required, reference grounding) as a LAST experiment with the
>     P-C1 rematch as its registered kill-or-cure test; (c) repoint
>     the harness at record-keeping/verification only (what gets
>     deleted). For each: agent cost, token cost, and what evidence
>     would count as success. The decision is the operator's; the
>     document's job is to make it a one-paragraph decision.
> Every parked prompt from W1-W6 gets one line in an appendix so
> nothing found is lost, whatever road is chosen.
>
> GATE: docs_verify full (the new document carries NO check: lines —
> it is a synthesis, not a map document; say so in its header);
> git diff --stat origin/main shows exactly one new file under
> docs/ plus the tranche directory. Commit and push every phase
> boundary (retry 2s/4s/8s/16s). DELIVERY closes with the document's
> own worry-first opening sentence, quoted.

## The numbered requirements

| R | The requirement, from the words above |
|---|---|
| **R1** | Verify the target repository is `AHepi/DeepReason` before anything else; STOP if it is elsewhere. |
| **R2** | Route through `dr-change-orchestrator`. This tranche writes ONE document and nothing else. |
| **R3** | READ-ONLY on `src/` and `tests/`. |
| **R4** | Setup: branch from `origin/main`, `be9bcff54` an ancestor of HEAD; editable install plus `pytest`, `pytest-xdist`, `jsonschema`. |
| **R5** | Read `CLAUDE.md` in full; load `dr-drive-harness` and `dr-explain-to-operator`. |
| **R6** | W7's document is an operator-facing FINAL output: worry-first, every technical term glossed inline, ONE closing analogy. |
| **R7** | Read every named input IN FULL before writing a word. |
| **R8** | No new measurement and no re-derivation. Every claim cites one of the named inputs by file and line/table. |
| **R9** | Inputs: `experiments/2026-08-26-run-anatomy-program/` PROGRAM.md and all six W directories (W1 forms, W2 criticism, W3 evidence/scratch, W4 judge road, W5 signals, W6 token flow), their RESULTS, tables and parked prompts. |
| **R10** | Inputs: `experiments/2026-08-25-poietics-program/RESULTS.md` (P-R1 and the strengthened P5) and the P-C1 arm comparison, at the path the program doc names. |
| **R11** | Inputs: `docs/RESEARCH_STRUCTURED_OUTPUT_COERCION*` (the 255/257 escape refusal), `RESEARCH_FINDINGS_Q1Q10*` Q4/Q5, `RESEARCH_SHAPE_CRITIQUE*` (expansion-only). |
| **R12** | Input: `docs/LESSONS_LEARNED_2026-08-17.md`, for the frame — honest ledgers outlive optimistic summaries. |
| **R13** | The document is `docs/RUN_ANATOMY_SYNTHESIS_2026-08-26.md`, FOUR sections, nothing else. |
| **R14** | §1 THE ORGAN TABLE: one row per measured subsystem (forms/wire contracts, reference grounding, criticism channel, scratch, evidence citation, judge road + guards, signals, allocation controller, token economy, record/verification); verdict from {WORKS, INERT, HARMFUL-AS-WIRED, PHANTOM, UNEXERCISED}; the ONE number that earns it; the citation. **No verdict without its number.** |
| **R15** | §2 THE CAUSAL STORY OF THE 33x LOSS: one narrative paragraph per contributing cause, ordered by measured size — the 41.2% self-spawned audit problem; the 24.6% rejected-output share; zero criticism-to-improvement coupling; the 10x collinearity conditioning effect; the invented-handle rate — each tied to its table. |
| **R16** | §2 states plainly which causes are HARNESS-DESIGN, which are MODEL-BEHAVIOR the harness failed to defend against, and which are WIRING never built (the discharge-required criticism channel; recombination). |
| **R17** | §3 THREE HONEST LISTS: refuted, unexercised, works. Refuted-as-wired is not refuted-in-principle; say which claims the record actually kills. |
| **R18** | §3: the record machinery, scratch, the guards and the two-call protocol belong in WORKS with their numbers. |
| **R19** | §4 THE ROADS, PRICED, with NO RECOMMENDATION MADE FOR THE OPERATOR: (a) retire the runtime, keep the method; (b) rebuild the two dead channels — criticism-into-working-context with discharge required, and reference grounding — as a LAST experiment with the P-C1 rematch as its registered kill-or-cure test; (c) repoint the harness at record-keeping/verification only (what gets deleted). |
| **R20** | §4: for each road — agent cost, token cost, and what evidence would count as success. The decision is the operator's; the document's job is to make it a one-paragraph decision. |
| **R21** | Every parked prompt from W1–W6 gets ONE LINE in an appendix so nothing found is lost, whatever road is chosen. |
| **R22** | Gate: `docs_verify` full. The new document carries NO `check:` lines — it is a synthesis, not a map document — and its header SAYS SO. |
| **R23** | Gate: `git diff --stat origin/main` shows exactly one new file under `docs/` plus the tranche directory. |
| **R24** | Commit and push at every phase boundary, with retry backoff 2s/4s/8s/16s. |
| **R25** | DELIVERY closes with the document's own worry-first opening sentence, QUOTED. |

## Amendments

None yet. A later operator message is APPENDED here verbatim as new
numbered requirements (or as `Rn-a supersedes Rn`) BEFORE it is acted on.
A requirement is never deleted, only marked superseded or deferred.
