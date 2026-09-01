# P-S1 run forensics — Half B setup

Date: 2026-09-01 UTC
Mode: read-only forensics
Delivery branch: `codex/ps1-forensics-b-20260901`
Investigator model: `gpt-5.6-sol` (`ultracode` request)

## Repository and anchors

- Repository: `AHepi/DeepReason`
- Origin: `https://github.com/AHepi/DeepReason.git`
- Linked GitHub permission check: `pull=true`, `push=true`, `maintain=true`, `admin=true`
- Analysis base: `origin/main` at `3cb51b14e4c7c74cc4d058b467588c1c55cc3eab`
- Required anchor: `3cb51b14e` is an ancestor of `HEAD` (indeed, it is `HEAD` at setup)
- Read-only P-S1 evidence branch: `origin/claude/deepreason-p-s1-commitments-wowcib` at `6338c48cbd4cc7b257a9b45ad45f412bd2527dec`

## Binding boundaries

- Typed record and source code are evidence. Model prose is only a claim to verify.
- No investigation of Half A: criticism-to-problem spawning, problem acceptance conditions, frontier definition, criticism's measurable effect, or anomaly sweep.
- No writes outside `experiments/2026-09-01-ps1-forensics-B/`.
- No edits to committed roots, `src/`, `tests/`, or `docs/`.
- No `pytest` and no `tools/docs_verify.py`.
- Record handles are paired by handle index / `ordered_refs`, never by dictionary `.values()` order.
- Every reported claim must end in a code `file:line` pointer or record `root/event-seq/field` pointer. Unsettled claims are `UNDETERMINED` with the exact deciding measurement.

## Map preflight

Global boundary: `DR-INV-frozen-surfaces`.

- B1/B2: `DR-SEAM-llm-x-workflow`, `DR-SEAM-bridge-x-llm`, `DR-INV-render-layout`, `DR-CON-packs-and-token-economy`, `DR-CON-conjecture-source`.
- B3: `DR-SEAM-rules-x-scratch`, `DR-SEAM-scratch-x-workflow`, `DR-CON-successor-questions`, `DR-SUB-scratch`.
- B4: `DR-SEAM-adjudication-x-rules`, `DR-SEAM-adjudication-x-authority`, `DR-SEAM-scheduler-x-rules`, `DR-CON-warrants-and-attacks`, `DR-SUB-adjudication`, `DR-SUB-scheduler`.
- B5: `DR-SEAM-capabilities-x-rules`, `DR-SEAM-capabilities-x-channels`, `DR-SEAM-periphery-x-verification`, `DR-CON-capability-lifecycle`, `DR-SUB-capabilities`, `DR-SUB-verification`.

Each lane reads its covering seams before its subsystem documents or source.

## Review topology

Five independent investigators answer B1 through B5 in parallel. After their evidence is assembled, two fresh skeptics review every load-bearing finding: one re-opens every cited pointer and one grants the facts but attacks the inference. Refuted findings are labelled `CORRECTED` in the final report.
