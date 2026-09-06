# Request: "the forms needs to change so that the conjecture seat can handle and organise the new log shaped content" — then "test on the full harness"
Captured: 2026-09-06 from the operator's message that closed the writer's room
window (quoted first, verbatim) and the monitor's executor brief carrying it
(quoted in full after it — trimmed context is how inputs get forgotten).
Branch: `claude/writers-room-organiser-testing-degagn`, based on `main` at
`d3f047932` (the writer's room merge).

## Map preflight (recorded here so every later phase starts from one map)

Read in this order, per `dr-drive-harness` §4: `docs/map/INDEX.md` →
`INV-frozen-surfaces.md` → `SUB-evidence.md` → `INV-seat-section-sources.md`
→ `INV-seat-section-plugins.md` → `CON-warrants-and-attacks.md` → the seams
they name.

| id | why it is in scope |
|---|---|
| `DR-INV-frozen-surfaces` | five surfaces, seven paths; every touched path is checked against it (C1) |
| `DR-SUB-evidence` | attachment is not support; blocks; byte-checked citations; the citable legend and its `shown` receipt |
| `DR-INV-seat-section-plugins` | a seat is a shell: `SeatShellV1`, layouts, the seeded plugins, `DEEPREASON_SEAT_SHELL` |
| `DR-INV-seat-section-sources` | where a section's CONTENT comes from — the frozen-evidence and citable-evidence sources the organiser's brief reads through |
| `DR-CON-warrants-and-attacks` | what a commitment can and cannot do to a status — nothing here mints a warrant |
| `DR-SEAM-packs-and-token-economy-x-rules` | the nine source-computed contexts, the allocator, `DISCLOSED_ON_DROP` |
| `DR-CON-packs-and-token-economy` | `PACK_TOKEN_BUDGET`, profiles, the section budgets the evidence sections live under |
| `DR-SUB-llm`, `DR-SUB-rules`, `DR-CON-conjecture-source` | the dispatch site that picks the form (`rules/conj.py`, read-only here) |
| `DR-SUB-minireason`, `DR-SEAM-llm-x-minireason` | the room root's record shape (read-only; `mini/` stays byte-untouched, C2) |

No map id exists for `experiments/` tooling or for `application/text_runs.py`'s
attach binding; neither is a blocker (the converter lives under the tranche,
and the attach road is read, not changed).

## Verbatim — the operator

> the mini window finished. And results look good. Now, to test on the full
> harness. But first, the forms needs to change so that the conjecture seat
> can handle and organise the new log shaped content.

## Verbatim — the executor brief (the monitor's design, carrying the operator's words)

> You are the executor for **the organiser seat: testing the writer's room on the full harness**. Route through `dr-change-orchestrator` starting with `dr-capture-request`. The operator's verbatim words, the authority to ledger:
>
> > the mini window finished. And results look good. Now, to test on the full harness. But first, the forms needs to change so that the conjecture seat can handle and organise the new log shaped content.
>
> Standing rulings that bind this tranche (cite them in REQUEST.md): "within mini, criticism can't overturn anything. The point is content generation for now. Then testing on the full harness." (2026-09-05); "This is a writer's room, not part of the epistemology" (2026-09-06); the success law (2026-09-03: "materially better than what's produced without it"); seat-is-a-shell (2026-09-03); modularity (2026-08-26).
>
> Context the capture cites (read before SPEC.md): `experiments/2026-09-06-change-writers-room-limits-and-forms/` (RESULTS.md, DELIVERY.md, PARKED.md) and its live root `runs/home-room/shallow-runs/shallow-0b47bc7b090854078ddf7559` — 12 conjectures, 36 objections, 46 commitment proposals, three cycles, ~53 000 characters; the room forms in `mini/minireason/forms.py` (`mini.conjecturer.room.v1`, `mini.critic.room.v1`, `mini.commitment.room.v1`; labels ride appended as `[angle: …]`, `[would settle: …]`, `[kind: …]`); the predecessor's D8 arms in `experiments/2026-09-05-change-mini-isolation-programme/d8/` (ARM 0 = three plain calls on the same question; PREREG_D8.md; PARKED P11 on what a measure needs). Map preflight: `docs/map/INDEX.md` → `INV-frozen-surfaces.md` → `SUB-evidence.md` (attachment is not support; blocks; byte-checked citations), `INV-seat-section-sources.md`, `INV-seat-section-plugins.md`, `CON-warrants-and-attacks.md`, and the seams they name. Record the ids in REQUEST.md.
>
> **The design, which SPEC.md refines but does not replace.** No new conjecture form. The full harness already has (a) the attached-evidence road — `deepreason reason --attach` admits files as content-addressed blocks, the seat sees them through the citable-evidence section, and `evidence_refs` on a candidate are checked byte for byte at admission and recorded as measures, never a status — and (b) the commitment-bearing conjecture form `reasoning.conjecturer.compact.v2` (`src/deepreason/llm/wire.py`; the proposal shape is `ReasoningCandidateProposal` in `src/deepreason/workloads/text.py`: claim, mechanism, counterconditions ≥1, typicality, evidence_refs ≤8), whose counterconditions become commitments after admission (`draft_countercondition_commitments`). The room's record maps onto them:
>
> - room conjecture (content + angle) → claim and mechanism, condensed, sharpened by its objections;
> - room proposals about it → one countercondition each: refuted-if as written; "forbids X" / "must not X" → refuted if X; "predicts X" → refuted if not X;
> - objections → read, carried nowhere;
> - the blocks drawn on → `evidence_refs`.
>
> Three moves:
>
> 1. **Converter** (a tool under the tranche, never under `src/`): a room root → an attachment directory, ONE block per room record, body verbatim, headed by the record's kind, id, cycle and (for objections and proposals) its `about` target. Commit the converter, the attachment it wrote from the room root, and the digest. Then confirm with a dry attach (`deepreason reason --attach … --dry-run` or the freeze step, whatever the CLI offers — read `src/deepreason/cli/main.py`) how many blocks were admitted and how many one call can see; the pack receipt is the record of what was withheld. Size the pack so the whole room is visible (about 53 000 characters, a sixth of the context); if the pack budget is configuration, set it; if it is not reachable by configuration, PARK that and run with what the pack shows, disclosed.
>
> 2. **Organiser seat**: a registered pairing (`SeatShellV1`, see `src/deepreason/llm/seat_layouts.py`, shells `seat.conjecturer.legacy-v0` / `seat.critic.legacy-v0`) of the EXISTING form `reasoning.conjecturer.compact.v2` with a NEW brief layout. Prefer a file-declared layout under `<DEEPREASON_HOME>/seat_plugins/` (the T0 road) and a registration that edits no consumer; if a shell pairing can only be registered in `seat_layouts.py`, that file is not frozen — register it there and say so. The brief: the problem; the citable room blocks; a directive that says ORGANISE, DO NOT INVENT — one candidate per room conjecture worth carrying; claim and mechanism condensed from that conjecture's block and sharpened by its objections; every countercondition taken from that conjecture's proposals, cited by block id; a conjecture with no proposal is left out and named in the candidate's uncertainties; typicality 0.5 unless the room gives a reason; nothing that is not in the blocks. The form requires a mechanism and ≥1 countercondition per candidate — on this room root every conjecture has a refuted-if proposal (12 of 12), so state that nothing is excluded by the form on this record. Show the rendered brief in the tranche before any live call. Prove with a stub test that the organiser's candidates admit through the ordinary path, that their counterconditions become commitments, and that a candidate citing a block id not in the pack gets the typed citation-failure measure (the record, not the seat, catches invention). DECIDE AND DISCLOSE: whether the pairing can be cycle-1-only (organise once, then the ordinary conjecturer from cycle 2) through configuration; if it cannot, run the organiser shell for the whole run with the room attached throughout, and park the cycle-scoped pairing with a ready prompt. The full harness's CRITIC does not see the room blocks on this run (its attacks are its own); park the switch that would show them.
>
> 3. **The measure** (PREREG.md sealed by commit + sha256 BEFORE any live call; follow PREREG_D8.md's form and P11's lessons — one unit, one budget, headroom): three arms on the D8 question (`runs/input-d8`, frozen input): ARM 0 = the three plain calls already recorded (reuse; do not respend); ARM H = the full harness alone, default shells, same model, `--cycles` and `--token-budget` matched to ARM R; ARM R = the full harness with the room attached and the organiser seat. The JUDGED UNIT is the run's composed result (`deepreason result` / the final surviving conjectures with their commitments), not one conjecture — that was D8's defect. Criteria written before any output is read; blind panel of 3 judges, keymap opened after; length reported and controlled as in D8, with the overlap clause. Pre-registered verdict: ARM R is MATERIALLY BETTER only if it beats BOTH ARM 0 and ARM H under the rule; report NULL or worse plainly. Before launch: `python -u scripts/cycle_soak.py --case <the launch config's case>` green; launch detached (`setsid nohup … & disown`) with the snapshot loop; judge only typed outcomes (state, stop_reason, `verify_root`, replay digest). Env file discipline: `git check-ignore` first, `chmod 600`, never commit or echo the key. Failure budget 6 live calls beyond the plan, S6-style ledger. If no key is present, deliver moves 1–2 and the sealed PREREG without the runs, and say so.
>
> Scope, hard: no frozen surface (check every touched path against `docs/map/INV-frozen-surfaces.md`, seven paths); `mini/` byte-untouched (the room is done); nothing under `src/deepreason/evidence/`, `rules/`, or the admission code changes — if organising needs a per-countercondition pointer (which block each refuted-if came from), PARK it: per-candidate `evidence_refs` is enough for the first run. Park, never fix, anything else (the room's P1/P2, mini P10/P11 stay parked). Iterate on the ring; the full gate ONCE at the boundary, and only if code under `src/` or `tests/` changed. The map moves in the same commit as any code. Deliver through `dr-validate-change` and `dr-deliver-change` with the R-by-R table; RESULTS.md is the honest ledger — what the record shows, what it does not (one question, one model, one room). Commit and push at every phase boundary with retry (2s/4s/8s/16s). Stop when delivered and pushed.

## Requirements

The operator's two sentences, then the brief's design split into its atomic
obligations. Each keeps the words it came from; nothing is added.

R1 (behavior): "the forms needs to change so that the conjecture seat can handle and organise the new log shaped content."
R2 (process): "Now, to test on the full harness."
R3 (artifact): "**Converter** (a tool under the tranche, never under `src/`): a room root → an attachment directory, ONE block per room record, body verbatim, headed by the record's kind, id, cycle and (for objections and proposals) its `about` target."
R4 (process): "Commit the converter, the attachment it wrote from the room root, and the digest."
R5 (process): "confirm with a dry attach (`deepreason reason --attach … --dry-run` or the freeze step, whatever the CLI offers — read `src/deepreason/cli/main.py`) how many blocks were admitted and how many one call can see; the pack receipt is the record of what was withheld."
R6 (behavior/process): "Size the pack so the whole room is visible (about 53 000 characters, a sixth of the context); if the pack budget is configuration, set it; if it is not reachable by configuration, PARK that and run with what the pack shows, disclosed."
R7 (behavior): "**Organiser seat**: a registered pairing (`SeatShellV1` …) of the EXISTING form `reasoning.conjecturer.compact.v2` with a NEW brief layout." — under "No new conjecture form."
R8 (behavior): "Prefer a file-declared layout under `<DEEPREASON_HOME>/seat_plugins/` (the T0 road) and a registration that edits no consumer; if a shell pairing can only be registered in `seat_layouts.py`, that file is not frozen — register it there and say so."
R9 (behavior): "The brief: the problem; the citable room blocks; a directive that says ORGANISE, DO NOT INVENT — one candidate per room conjecture worth carrying; claim and mechanism condensed from that conjecture's block and sharpened by its objections; every countercondition taken from that conjecture's proposals, cited by block id; a conjecture with no proposal is left out and named in the candidate's uncertainties; typicality 0.5 unless the room gives a reason; nothing that is not in the blocks." With the mapping: "room conjecture (content + angle) → claim and mechanism … room proposals about it → one countercondition each: refuted-if as written; 'forbids X' / 'must not X' → refuted if X; 'predicts X' → refuted if not X; objections → read, carried nowhere; the blocks drawn on → `evidence_refs`."
R10 (artifact): "The form requires a mechanism and ≥1 countercondition per candidate — on this room root every conjecture has a refuted-if proposal (12 of 12), so state that nothing is excluded by the form on this record."
R11 (artifact): "Show the rendered brief in the tranche before any live call."
R12 (artifact): "Prove with a stub test that the organiser's candidates admit through the ordinary path, that their counterconditions become commitments, and that a candidate citing a block id not in the pack gets the typed citation-failure measure (the record, not the seat, catches invention)."
R13 (process): "DECIDE AND DISCLOSE: whether the pairing can be cycle-1-only (organise once, then the ordinary conjecturer from cycle 2) through configuration; if it cannot, run the organiser shell for the whole run with the room attached throughout, and park the cycle-scoped pairing with a ready prompt."
R14 (behavior/process): "The full harness's CRITIC does not see the room blocks on this run (its attacks are its own); park the switch that would show them."
R15 (artifact): "**The measure** (PREREG.md sealed by commit + sha256 BEFORE any live call; follow PREREG_D8.md's form and P11's lessons — one unit, one budget, headroom)".
R16 (process): "three arms on the D8 question (`runs/input-d8`, frozen input): ARM 0 = the three plain calls already recorded (reuse; do not respend); ARM H = the full harness alone, default shells, same model, `--cycles` and `--token-budget` matched to ARM R; ARM R = the full harness with the room attached and the organiser seat."
R17 (artifact): "The JUDGED UNIT is the run's composed result (`deepreason result` / the final surviving conjectures with their commitments), not one conjecture — that was D8's defect."
R18 (artifact): "Criteria written before any output is read; blind panel of 3 judges, keymap opened after; length reported and controlled as in D8, with the overlap clause."
R19 (artifact): "Pre-registered verdict: ARM R is MATERIALLY BETTER only if it beats BOTH ARM 0 and ARM H under the rule; report NULL or worse plainly."
R20 (process): "Before launch: `python -u scripts/cycle_soak.py --case <the launch config's case>` green; launch detached (`setsid nohup … & disown`) with the snapshot loop; judge only typed outcomes (state, stop_reason, `verify_root`, replay digest)."
R21 (process): "Env file discipline: `git check-ignore` first, `chmod 600`, never commit or echo the key."
R22 (process): "Failure budget 6 live calls beyond the plan, S6-style ledger."
R23 (process): "If no key is present, deliver moves 1–2 and the sealed PREREG without the runs, and say so."
R24 (artifact): "RESULTS.md is the honest ledger — what the record shows, what it does not (one question, one model, one room)."
R25 (process): "Deliver through `dr-validate-change` and `dr-deliver-change` with the R-by-R table".

## Standing constraints

C1: "no frozen surface (check every touched path against `docs/map/INV-frozen-surfaces.md`, seven paths)" — the brief, Scope. The seven paths: `capabilities/state.py`, `harness.py`, `invariants.py`, `verification/`, `run_manifest.py`, `qualification.py`, and the frozen-adjacent `route_fingerprint` in `llm/firewall.py` (CLAUDE.md, third lane).
C2: "`mini/` byte-untouched (the room is done)" — the brief, Scope.
C3: "nothing under `src/deepreason/evidence/`, `rules/`, or the admission code changes — if organising needs a per-countercondition pointer (which block each refuted-if came from), PARK it: per-candidate `evidence_refs` is enough for the first run." — the brief, Scope.
C4: "Park, never fix, anything else (the room's P1/P2, mini P10/P11 stay parked)." — the brief, Scope.
C5: "Iterate on the ring; the full gate ONCE at the boundary, and only if code under `src/` or `tests/` changed." — the brief, Scope.
C6: "The map moves in the same commit as any code." — the brief, Scope; CLAUDE.md, The map.
C7: "Commit and push at every phase boundary with retry (2s/4s/8s/16s). Stop when delivered and pushed." — the brief, Scope.
C8: "No new conjecture form." — the brief, The design.
C9 (standing ruling, 2026-09-05): "within mini, criticism can't overturn anything. The point is content generation for now. Then testing on the full harness." — CLAUDE.md, operator design laws.
C10 (standing ruling, 2026-09-06): "This is a writer's room, not part of the epistemology" — the room tranche's REQUEST.md R5, held there as "refuted 0; no authority path touched".
C11 (the success law, 2026-09-03): "a complete answer isn't the goal. Neither is correctness. The condition of success it something materially better than what's produced without it. Correctness is irrelevant. … Poppers epistemology is about progress, not truth." — CLAUDE.md.
C12 (seat-is-a-shell, 2026-09-03): "an artifact truely is determined by input and output, the artifact is just a shell" — CLAUDE.md; the shell governs how content is GENERATED and never what counts as EVIDENCE.
C13 (modularity, 2026-08-26): "There needs to be a priority that enforces modularity. Customisation needs to be easy." — CLAUDE.md; a new arrangement is a registration, never a consumer edit.
C14 (MANDATORY, 2026-09-05): "Don't not ever verify a review without my explicit permission." — CLAUDE.md. This tranche is a change tranche, not a review; it runs its own ring and one gate at the boundary under C5, and verifies nothing on anyone else's behalf.
C15 (never edit a committed root): the room root and the D8 arm-0 files are READ only — CLAUDE.md, Live runs.
C16 (tokens are cheap; the agent is not, 2026-08-08): prefer live evidence over machinery where a key exists — CLAUDE.md.

## Open questions (for dr-spec-change)

Q1: The brief names the form `reasoning.conjecturer.compact.v2` as "the EXISTING form" the organiser pairs with. Which form does the managed full-harness conjecturer call actually dispatch under (the dispatch site chooses inline — `rules/conj.py`), and does that form's candidate carry claim, mechanism, counterconditions ≥1, typicality and evidence_refs? If it is not `compact.v2`, the property the brief wants (a commitment-bearing candidate) must be delivered through the form the harness actually reaches, and the contradiction recorded.
Q2: "Prefer a file-declared layout under `<DEEPREASON_HOME>/seat_plugins/`" — does the managed `deepreason reason` path load that directory at all, or only the reduced engine? If only the reduced engine, the shell must be registered in `seat_layouts.py` and the brief's own fallback clause applies.
Q3: "Size the pack so the whole room is visible" — which of the three ceilings between the attachment and the seat (the attached-evidence policy's sources-per-pack, the citable legend's block cap and excerpt length, the section allocator's `PACK_TOKEN_BUDGET`) are configuration, and which are code? Each must be measured offline against the real attachment before the first live call.
Q4: "ONE block per room record" and `reason --attach` — how many files may one attach admit, and does that bound the layout of the attachment directory (one file per record, or records grouped into files)?
Q5: "cycle-1-only … through configuration" — is any configuration road cycle-scoped (an environment variable is process-wide; `continue` after a one-cycle stop is the operations-parity road), and is that road proven reliable on this tree?
Q6: "The JUDGED UNIT is the run's composed result (`deepreason result` …)" — there is no `deepreason result` command in `cli/main.py`; `deepreason results` prints typed counts, not the surviving conjectures' text. What composes the unit, and from which typed artifacts?
Q7: "the launch config's case" for the soak — no committed soak case drives qwen3.5:397b; which committed case is the launch configuration's SHAPE (solo, attached evidence enabled)?
Q8: No credential is present on this container (`experiments/*/env` absent; `OLLAMA_API_KEY` unset). R23 applies unless one appears before the launch step.

## Amendments

(append-only; later operator messages land here as R<n+1>... or
"R2a supersedes R2", each with its verbatim quote)
