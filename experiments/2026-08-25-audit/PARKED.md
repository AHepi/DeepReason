# PARKED — 2026-08-25 close-out audit

Ready-to-send prompts. The audit family never fixes anything: every
finding leaves here as a prompt the operator pastes into an executor
window. Nothing below has been executed.

---

## P1 — two skills still require the root sweep the operator retired

Route: `dr-change-orchestrator`. Proof: `goal-trace.md` GT1,
`proof/goal-L7.txt`.

    Route: dr-change-orchestrator.
    Goal (one): make the skill files agree with the operator's 2026-08-22
    ruling that the root sweep is retired as an instrument.
    Authority: CLAUDE.md, "Build and test" -- "The root sweep is RETIRED as
    an instrument (operator ruling 2026-08-22: 'it just wastes time'). No
    tranche, gate, audit, or frozen-surface grant may require sweeping
    committed roots."
    Evidence pointers:
      .claude/skills/dr-drive-harness/SKILL.md:139 lists
        `python tools/root_sweep.py` under "Instruments that prove you broke
        nothing", with the obligation "no committed root's verdict may move".
      .claude/skills/dr-spec-change/SKILL.md:79 treats it as a live baseline
        instrument.
      Already correct, do not touch: .claude/skills/dr-audit-broken/SKILL.md
        step 5, and docs/AUDIT_BASELINES.md's retirement entry.
    End state: neither skill requires or recommends running the sweep;
    each says instead what CLAUDE.md says -- reader changes are proven by
    targeted, mutation-proven regression tests. tools/root_sweep.py itself
    is NOT deleted by this tranche (that is a separate decision).
    Gate: python tools/docs_verify.py full, 0 non-baseline failures.

---

## P2 — the four 2026-08-13 spec-orphan prompts are still unexecuted

Route: `dr-change-orchestrator`. Proof: `spec-drift.md` SD1-SD4.

    Route: dr-change-orchestrator.
    Goal (one): close the four spec-orphan terms the 2026-08-13 audit
    parked as P6-P9 and that this audit re-measured as unchanged.
    The four: `ContextRequest` (code has ContextRequestV1), `codec:json`,
    `novel-case`, `workflow-resume-decision.v1` (3-way spelling drift).
    Evidence pointers: experiments/2026-08-25-audit/spec-drift.md rows
    SD1-SD4; proof/spec-orphan-wordbound.txt;
    experiments/2026-08-13-audit/PARKED.md P6-P9 for the original
    per-term detail.
    End state: each term either appears in the tree under the spec's own
    spelling, or a v1.8 amendment records the rename. Append-only: never
    edit existing spec text.
    Gate: full pytest gate 0 failed; docs_verify full.

---

## P3 — 40 new shipped surface items have no spec coverage

Route: `dr-change-orchestrator`. Proof: `spec-drift.md` SD7-SD9.

    Route: dr-change-orchestrator.
    Goal (one): draft ONE append-only harness-spec v1.8 amendment covering
    the shipped surface that grew since 2026-08-13 without spec coverage:
    14 new config fields and 26 new typed error/refusal strings, all
    spec-silent (the +1 CLI flag is already covered).
    Evidence pointers: experiments/2026-08-25-audit/proof/
    tree-config-fields-silent.txt and tree-error-strings-silent.txt;
    spec-drift.md's delta table.
    Scope note: this tranche covers the DELTA since the last audit, not
    the whole 243-item spec-silent backlog -- that backlog is the standing
    condition the 2026-08-13 audit already parked, and widening this
    tranche to it would make it unshippable.
    End state: docs/harness-spec-v1.8-amendment.md exists, states what it
    does and does not change, and the 40 items resolve against it.
    Gate: docs_verify full.

---

## P4 — THE EXPERIMENTS DELETION TRANCHE

Route: `dr-change-orchestrator`. Proof: `experiments-census.md` (all 152
rows). This is the prompt the operator's close-out instruction asks for.

**It runs in two stages and the order is load-bearing.** Stage 1 re-homes
60 open park items out of 18 directories. Stage 2 deletes. Running stage 2
first destroys work the operator deliberately deferred.

    Route: dr-change-orchestrator.
    Goal (one): remove 70 experiment directories from the working tree,
    after re-homing every open park item they carry.

    Authority (operator, verbatim): "all experiments and tests need to be
    audited so I can get rid of them."

    STAGE 1 -- EXTRACT. These 18 directories carry 60 park items that no
    later tranche's execution artifact ever cited, so they are still open.
    Create ONE standing registry, experiments/OPEN_PARKS.md, and move every
    open item into it verbatim, each row naming its originating tranche and
    the git sha where its full text lives. Do not summarize an item; a park
    is a ready-to-send prompt and loses its value when compressed.
      experiments/2026-07-30-change-amendment-epochs  (4 open items)
      experiments/2026-07-30-fix-citation-quote-check  (1 open item)
      experiments/2026-07-30-fix-sandbox-contract  (1 open item)
      experiments/2026-08-01-fix-decomposition-merge-pairing  (9 open items)
      experiments/2026-08-02-map-falsification  (6 open items)
      experiments/2026-08-03-change-driving-skill  (3 open items)
      experiments/2026-08-03-change-rung1-sockets-on-paper  (6 open items)
      experiments/2026-08-03-change-rung2-bridge-unification  (4 open items)
      experiments/2026-08-03-change-rung2-config-inventory  (6 open items)
      experiments/2026-08-05-fix-smoke-entry-point-reader  (5 open items)
      experiments/2026-08-08-change-rung-g1-actual-diff-budget  (1 open item)
      experiments/2026-08-09-change-errata-sweep-and-automation  (1 open item)
      experiments/2026-08-11-change-docs-reorg-steps-3-4  (1 open item)
      experiments/2026-08-14-change-rung1-vocabulary-groundwork  (3 open items)
      experiments/2026-08-15-change-rung2-premise-channel  (1 open item)
      experiments/2026-08-15-change-rung3a-h1-successor-deletion  (1 open item)
      experiments/2026-08-22-audit-scalarization  (3 open items)
      experiments/2026-08-24-change-rung5-promotion-criteria  (4 open items)

    STAGE 2 -- DELETE. Remove these 52 directories, plus the 18 above once
    stage 1 has re-homed them:
      experiments/2026-07-31-change-critic-seats-and-thinking
      experiments/2026-07-31-schema-sweep
      experiments/2026-08-01-fix-adjudication-blindness
      experiments/2026-08-03-change-executor-errata
      experiments/2026-08-03-change-modularisation-handover
      experiments/2026-08-03-change-question-skill
      experiments/2026-08-04-change-rung6-plugin-conformance
      experiments/2026-08-04-change-spec-judgment-guardrails
      experiments/2026-08-04-change-workflow-guardrails
      experiments/2026-08-05-change-budget-ceiling-at-commit
      experiments/2026-08-05-change-smoke-instrument-visibility
      experiments/2026-08-05-change-unstick-guardrails
      experiments/2026-08-05-fix-loopback-fixture-daemon
      experiments/2026-08-05-fix-qualification-inventory-pins
      experiments/2026-08-05-fix-smoke-failure-reporting
      experiments/2026-08-05-testphase-live-validation
      experiments/2026-08-06-change-seat-binding-design-s2
      experiments/2026-08-06-change-seat-binding-wired-s3
      experiments/2026-08-08-change-grounded-overlay-o1
      experiments/2026-08-08-change-grounded-overlay-o2
      experiments/2026-08-08-change-load-dials-d4
      experiments/2026-08-08-fix-l1-continue-resumable-crash
      experiments/2026-08-08-parked-bronze-census-env
      experiments/2026-08-09-change-adjudication-judge-seats-optins
      experiments/2026-08-09-change-hard-question-set
      experiments/2026-08-09-change-llm-probe-apparatus
      experiments/2026-08-09-cp1m-stratification-retrodiction
      experiments/2026-08-09-overnight-omnibus
      experiments/2026-08-09-parked-full-power-matrix
      experiments/2026-08-11-change-remove-token-ceiling
      experiments/2026-08-11-change-spec-v17-and-docs-index
      experiments/2026-08-11-errata-checkpoint-audit
      experiments/2026-08-11-program-closeout
      experiments/2026-08-11-spec-drift-measurement
      experiments/2026-08-11-sweep-smoke-currency
      experiments/2026-08-12-change-skills-overhaul
      experiments/2026-08-12-change-skills-parked-followups
      experiments/2026-08-13-change-defended-trial-wiring
      experiments/2026-08-13-change-smoke-currency-audit
      experiments/2026-08-15-change-rung3c-claim-substrate
      experiments/2026-08-15-change-rung3d-website-remnant
      experiments/2026-08-23-audit-invention-inventory
      experiments/autonomous_inquiry_preflight_2026-07-16
      experiments/bronze_feedback_v1_superseded_2026-07-14
      experiments/bronze_repertoire_v2_2026-07-14
      experiments/live_20b_schema_2026-07-31
      experiments/live_coin_canonicity_2026-07-31
      experiments/live_coin_thinkingoff_2026-07-31
      experiments/live_compare_2026-07-28
      experiments/live_gemma4_schema_2026-07-31
      experiments/live_turmite_2026-07-31
      experiments/tier_v_checkers

    DO NOT TOUCH the 82 directories rowed KEEP in experiments-census.md.
    79 of them are load-bearing for instruments that are green today --
    docs/map check: lines execute against committed run roots inside them
    (for example experiments/2026-08-02-stress-triplet/home-orbit/runs/
    run-6472629dbc5d408a733d472040671752 appears inside four separate
    executable checks), and tests open others as fixtures.

    GATE, both required, after the removal:
      python tools/docs_verify.py          # FULL mode, not --fast.
                                           # --fast reuses cached results
                                           # and cannot see a check whose
                                           # target you just deleted.
      python -m pytest tests/ -q -n 4      # 0 failed. Baseline for this
                                           # tree is 4162 passed, 6 skipped.
    Either instrument going red means something load-bearing left the tree:
    restore it, row it in experiments-census.md as a KEEP the census missed,
    and say which of Q-E1..Q-E4 failed to catch it.

    Nothing is lost by deleting: git history keeps every byte, and each
    census row cites the sha.


---

## P5 — THE DOCS PRUNE TRANCHE

Route: `dr-change-orchestrator`. Proof: `docs-census.md` (all 131 rows).

    Route: dr-change-orchestrator.
    Goal (one): remove 13 documents from docs/ that a later ledger absorbed
    or that document a subsystem no longer in the tree.

    Authority (operator): the test and experiment REPORTS that accumulated
    in docs/ are "a lot of data with no structure."

    THE LIST (13 files):
      docs/HANDOVER_2026-07-27.md
      docs/HANDOVER_2026-08-02.md
      docs/HANDOVER_2026-08-03.md
      docs/HANDOVER_MONITOR_2026-08-06.md
      docs/POIETIC_CALCULUS_v0.1.md
      docs/RESEARCH_CONVERGENCE_LOOPS_2026-08-22.md
      docs/RESEARCH_PROGRAM_2026-08-22.md
      docs/RUNTIME_IMPORTS.md
      docs/proposals/CODER_AS_TOOL_PREPLAN.md
      docs/proposals/CRITICISM_SYMMETRY_RESEARCH_PREPLAN.md
      docs/proposals/GROUNDED_OVERLAY_PREPLAN.md
      docs/proposals/HARD_QUESTION_SET_PROMPT.md
      docs/proposals/RECORD_LIFECYCLE_DEFECT_PLAN.md

    ALSO REQUIRED IN THE SAME COMMIT: docs/INDEX.md is a pointer layer over
    this tree and links several of the files above by name. Every link to a
    removed file must go in the same commit, or docs_verify --links breaks.
    INDEX.md itself is rowed KEEP -- it is the navigation, not a report.

    THE ERRATA RULE, absolute: this tranche never deletes a docs/ERRATA.md
    entry. Errata are append-only forever. If a pruned document is cited by
    an ERRATA entry, the entry stays exactly as written -- an errata entry
    is a record that a claim was found wrong, and it stays true whether or
    not the document survives.

    DO NOT TOUCH the 14 files rowed KEEP-UNTIL-ABSORBED. Nothing absorbed
    them yet, so deleting them loses the only copy in the working tree. What
    a one-page absorption would need is named in AUDIT_REPORT.md's closing
    picture.

    GATE: python tools/docs_verify.py    # FULL mode. This is the proof
                                         # that no living check and no
                                         # DR- link broke.
           python tools/docs_verify.py --links

    Nothing is lost by deleting: git history keeps every byte.


---

## P6 — `treadle doctor` has not run since the container rolled back

Route: `dr-change-orchestrator`. Proof: `broken.md` B6,
`proof/treadle-doctor.txt`.

    Route: dr-change-orchestrator (environment restoration, not a code fix).
    Goal (one): get `treadle doctor` running again and record its verdict
    against docs/AUDIT_BASELINES.md.
    Why it matters beyond tidiness: the baseline says a
    "WARN model tag ... NOT on endpoint" line "is always a finding: hosted
    checkpoints are retired without notice, and that line is how this repo
    learns." That early-warning channel is currently dark -- if a hosted
    checkpoint the treadle lane depends on were retired today, nothing in
    this repo would notice.
    Two blockers, both environmental:
      1. tools/treadle/.venv is absent (container rollback). Rebuild per
         tools/treadle/VENDORED.md.
      2. OLLAMA_API_KEY is unset and no experiments/*/env file exists to
         recreate it from. Needs the operator's handover value; it is
         gitignored and never committed.
    End state: `tools/treadle/.venv/bin/treadle --repo . doctor` runs with
    the key exported, and its output is compared line-by-line against the
    baseline's recorded expectation (5 environment lines, 3 stage lines,
    credentials, 4 model-tag lines). Compare the OK/WARN/MISS verdicts,
    NOT the arithmetic -- the line count moves whenever treadle.toml gains
    or loses a stage or a context_files entry.
    If a model tag comes back NOT on endpoint, that is a finding: row it
    and park a replacement-checkpoint prompt, do not silently re-pin.

---

## P7 — CLAUDE.md's stated gate expectation is out of date

Route: `dr-change-orchestrator`. Proof: `broken.md` B1,
`proof/broken-gate.txt`.

    Route: dr-change-orchestrator.
    Goal (one): correct CLAUDE.md's "Build and test" section, which tells
    every incoming session to "expect ~3100 passed, 0 failed". The gate on
    main is 4162 passed, 6 skipped, 0 failed.
    Why it is worth a line of work: the number is what a fresh session
    compares its first gate run against, so a stale one invites either a
    false alarm or, worse, a shrug at a real 1000-test discrepancy.
    Evidence pointer: experiments/2026-08-25-audit/proof/broken-gate.txt
    ("4162 passed, 6 skipped in 998.65s").
    End state: the number matches the tree, and the line says it is
    approximate and moves. Consider whether it should cite the audit that
    last measured it, so the next drift is dateable.
    Gate: none needed -- this is a one-line documentation correction.
