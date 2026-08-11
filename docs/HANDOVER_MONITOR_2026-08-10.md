# Monitor-session handover — 2026-08-10

You are the MONITOR: you review executor tranches from their branches
(commits, never claims), write the prompts the operator pastes into
executor windows, ledger operator words as laws/amendments, merge
delivered work into main, and run occasional docs-only work yourself.
The operator (Aaron, they/them) drives by pasting your prompts and
relaying results; executor windows are cheaper models. Standing law:
tokens are cheap, YOU are not — prefer experiments and executor
windows over monitor-side work.

Read first, in order: CLAUDE.md IN FULL (the Operator design laws and
conventions sections are all binding; several were ledgered this
session), `.claude/skills/dr-explain-to-operator/SKILL.md` (BINDING for
every operator-facing message: worry first, gloss every term
conservatively on intermediaries, exactly one closing analogy on final
outputs), then this file, then `docs/ERRATA.md` +
`docs/ERRATA_EXECUTOR.md` (newest entries), then the newest RESULTS.md
segments named below.

## Branches (the part that bites)

- **main is the single source of truth** (consolidated 2026-08-09; the
  old three-branch mirror ritual is RETIRED). Every delivered tranche
  merges to main; `git push origin HEAD:main` works from the monitor
  session. Ref DELETION is blocked for agent credentials — the
  operator deletes stale branches via the GitHub UI when asked.
- Your session gets its own designated `claude/...` branch; keep it
  equal to main (push both after each merge).
- **Prompt-writing rule learned the hard way**: fresh windows start on
  a default checkout — every prompt must do `git fetch origin main &&
  git checkout -B <branch> origin/main` (with a
  `merge-base --is-ancestor <recent-sha>` check) BEFORE any
  CLAUDE.md/skill reading, and preflight `pip install pytest
  pytest-xdist jsonschema --break-system-packages -q` (containers roll
  back and lose them; jsonschema is a known undeclared test dep).

## Live threads RIGHT NOW

1. **The opt-in/adjudication tranche** —
   `origin/claude/adjudication-judge-seats-optins-4nb7ov`, the largest
   tranche of the program, grown under ELEVEN in-window operator
   amendments. Delivered so far on-branch: judge seats opt-in
   (`--judge-seats`, surfaces judge-audit evidence at setup),
   `--blind-same-model-judges` (the SOLO adjudication road:
   content-blindness substitutes for family diversity), legacy
   school-free criticism circuit with `LEGACY_CRITICISM_ENABLED`
   default FLIPPED TO ON (Road E), school seats both sides
   (`--school-seat school-N=PROFILE` conjecture-side,
   `--criticism-seat school-N=PROFILE` criticism-side, independent),
   config-referee confirmed LIVE. Still executing Part E tail; stops
   after dr-validate-change. REVIEW CAREFULLY when it stops: R-by-R
   across all 11 amendments; frozen tripwire — the ONLY grant is
   run_manifest.py additive `.pop(...)` lines in
   `_versioned_source_config_data` (R19-style wording, ledgered);
   wheel-smoke re-pin owed (new CLI flags); then merge to main.
2. **The seven-item cleanup program** — a complete paste-ready prompt
   was handed to the operator (also summarized in the plan file
   `/root/.claude/plans/there-a-few-things-snoopy-yeti.md`): six
   sequential tranches in one window — (1) sweep/smoke currency +
   errata compliance sweep, (2) spec-drift measurement with ONE
   batched stop (v1.7 amendment is the recommended road), (3)
   human-readable error-code catalog (design-and-stop), (4)
   schema-validated run-request file + validating intake command +
   MCP wrapper + FORM DR-1 regenerated from schema (design-and-stop),
   (5) docs/ reorganization proposal (stop before moves), (6) S4b
   per-role qualification (frozen surface 5, DESIGN-AND-STOP, fresh
   words mandatory). The operator may launch it any time; review each
   tranche as it lands.
3. **Blast-radius spec** —
   `origin/claude/blast-radius-analysis-design-3avwew`, DELIVERED
   spec + `HIDDEN_LEGACY_INVENTORY.md`, STOPPED awaiting operator
   words. Recommendations (monitor concurs): F1 Road B, F2 A, F3 A
   (B next), F4 B (inventory to docs/), F5 B. NOT merged — it's a
   design stop. The operator's "approve as recommended" un-blocks the
   implementation window (tools/blast_radius.py + skill checkpoints).
4. **Full-power matrix** —
   `origin/claude/full-power-matrix-2026-jbmd8n`, live window (best
   models per seat, dual OFF, solo baseline arm), still running last
   checked. Review its decision table when it lands.
5. **LLM-probe channel spec** —
   `origin/claude/research-backend-audit-spec-ilryya`, delivered
   spec-and-stop, **STILL UNREVIEWED BY THE MONITOR — owed**. The
   operator's design intent (ledgered in its REQUEST): isolated LLMs
   as laboratory APPARATUS for testing conjectures about LLM limits,
   reachable from scratchpad and critics; NOT judges, NOT sources.
6. **Hidden-legacy inventory item 2** —
   `ARGUMENTATIVE_AUTHORITY=single_family_trial`, a dead config value
   for solo-compatible trials, queued for investigation behind thread
   1's delivery (blind-same-model-judges may partly supersede it —
   check before commissioning).

## State of the science (what the record now proves)

- **Patrol/contradiction program**: 9,277 pairs patrolled, 1,941
  candidates (20.9%); CP1-M confirmed **570 on strong evidence alone**
  (execution + ground truth, 51.1% of eligible strata), 1,385 blended.
  Corpus is shallow (depth-0/1 only). CP2-CP4 queued; the matrix arms
  double as CP2 corpora. Patrol judgment is non-deterministic (inputs
  deterministic; embeddings corroborate — see
  docs/PATROL_DETERMINISM_REPORT.md and the three-reading
  decomposition of "deterministic grounded extension for prose").
- **Dual-mode is LIVE**: v7 opt-in contract wired end-to-end (CP1-M
  follow-on tranche; real v7 dispatch, zero replay violations).
  Checker-authoring: ~49% discrimination, ~87% compile-pass.
- **Judges**: memorized-flaw catch 93-97%, novel-flaw median ratio
  0.475, none of 11 models threads novel-catch vs clean-FP —
  suspect-by-default is LAW; adjudication-blindness finding
  self-reports toothless criticism in every observe_only run.
- **Gate baseline**: 0 failed (two environment-only caveats parked:
  jsonschema undeclared dep; bronze-census env-coupled reconciliation
  — `experiments/2026-08-08-parked-bronze-census-env/PARKED.md`).
- **Grounded-overlay program**: CLOSED healthy-negative under
  spec-true groundedness (the 14 "floating chains" dissolved);
  re-run tripwires recorded in the pre-plan.

## Standing rules (old ones still bind; new ones from this session)

- Verify executor claims against commits; check the branch BEFORE
  writing any "next prompt"; blob-first on cycle-0 deaths; judge only
  typed outcomes; never predict pending background results.
- **Frozen surfaces: words BEFORE touch, and approval for a named
  surface never extends to unnamed surfaces the same fix needs**
  (within-tranche non-transitivity — see ERRATA_EXECUTOR 2026-08-09;
  ratification-by-disposition happened once and is NOT precedent).
- Qualification cost arithmetic: ONE battery per distinct
  COMBINATION (S4 Option 2b), not per profile — the monitor
  overcounted once; don't repeat. S4b (per-role provenance) is the
  parked fix for roster iteration, now in cleanup tranche 6.
- Budget stops: the diff_budget gate (G1) fires at commits; operators
  pre-authorize overnight windows with standing continue-and-report
  words. Errata checkpoints bind every delivery ("errata: none" or an
  entry, same commit).
- The operator reuses windows to avoid branch explosion; prompts for
  continuing windows assume context, prompts for fresh windows are
  self-contained.
- Laws ledgered this session (all in CLAUDE.md, verbatim-quoted):
  explain-to-operator binding on every message; formalism optional
  (R-g, with its Goodhart clause); solo-with-everything-on + judges
  suspect-by-default; tokens-cheap-agent-expensive; plus the gates
  doctrine (docs/proposals/GATES_AND_PACKAGES_PREPLAN.md — Stage 2
  dynamic flips BENCHED by the operator, static mint-time gates only).

## Parked/queued (beyond the live threads)

Deterministic gates G2-G5 (G1 delivered); L3 seat-bindings-in-run-
identity spec (operator words needed); property_designer fate;
criticism-symmetry full program (needs third model + hard corpus —
both now exist); CP2-CP4; the benched anti-attractor package (Stage
2); Tier-O adjudication follow-ups now largely superseded by thread
1's opt-ins. `experiments/2026-08-09-parked-full-power-matrix/` is
LAUNCHED (thread 4) — update its status on merge.

## The operator's style (BINDING — load dr-explain-to-operator)

Answer their actual worry in sentence one. Gloss every technical term
inline on intermediary messages. Price forks as roads with a
recommendation. Own your part plainly when process caused confusion.
Exactly ONE closing analogy on final outputs, none on intermediaries.
They answer with a word; make stops cost them one word.
