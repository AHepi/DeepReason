# Spec for: judge-evidence review — read-only archaeology over committed runs
Traces: every item cites R/C numbers. Untraceable items are bugs.

Inventory used to write this spec (background sweep, 2026-08-09): every
committed file mentioning judge-audit tags, the tranches named in R5a-e, and
their line numbers, are listed below per item. Re-verified against the repo
by direct read where the item says so.

## Items

S1 (R1, R9, R6): Create `REVIEW.md` in this tranche directory. Top section
states the question verbatim ("what do the committed runs and experiments
actually prove about LLM-judge discrimination?") and previews the answer in
one paragraph, then sections S2-S9 below in order. Every numeric claim in
every section carries its source as `path:line` or `path` (for a JSON
field) inline, per R6.
    accept: `test -f REVIEW.md && head -5 REVIEW.md | grep -q "LLM-judge discrimination"`

S2 (R5a, R6): **Judge audit machinery section.** Describe
`src/deepreason/informal/audits.py`'s four audit functions
(`planted_flaw_calibration` L228, `bias_probes` L273,
`paraphrase_invariance_audit` L116, `premise_deletion_audit` L184) and their
typed log tags (`judge-error-rate:`, `judge-self-preference:`,
`judge-verbosity-bias:`, `audit-hit:`, `audit-blocked:ensemble-split`).
Then pull every number these tags or their result-JSON counterparts produced
in the committed record:
  - `experiments/results/judge_liability_index_report.json`
  - `experiments/results/e02_judge_redteam_t1_report.json` (+
    `e02_t1_items/judgments.jsonl`, `toothless_funnel.json`)
  - `experiments/results/e02_t2_voting_report.json`
  - `experiments/results/e02_t2b_readjudication_report.json`
  - `experiments/results/e02_t3_judge_zoo_report.json`
  - `experiments/results/glm_judge_v1_report.json` +
    `glm_judge_v1_forensic_addendum.json`
  - `experiments/results/bronze_flat_v1_report.json` + its
    `_forensic_addendum.json`, `_correction1.json`,
    `_counterfactual_forensics.json`
  - `experiments/results/bronze_pilot_v1_report.json`,
    `bronze_repertoire_v2_report.json`, `bronze_court_cross_v1_report.json`,
    `court_calibration_v1_report.json`
  - `experiments/results/gemma4_dna_unattended_report.json` +
    `_3_report.json`
  - `tests/test_audits.py` pinned numbers (L131 `rate == 0.25`, L154
    `self_preference == 1.0`) — these are synthetic/offline fixtures, not
    live-run evidence; label them as such, separately from the live numbers.
    accept: `grep -c '\.json' REVIEW.md` includes every file above at least
    once (manual check against the list at validation)

S3 (R5b, R6): **Trial-protocol section.** Describe the guard design in
`src/deepreason/informal/trial.py`: order-swap consistency (`_trial_steps`
L383-434, `pairwise_discriminate` L874-897, both `outcome="blocked:order-swap"`),
paraphrase screen (`_paraphrase_screen` L513, called L440 and L682). Read
`experiments/2026-08-01-change-prose-can-refute/` (CHECKLIST.md, DELIVERY.md,
SPEC.md, VALIDATION.md) and report what its live evidence actually is —
DELIVERY.md L44 records a *mocked* judge family (`{'mock:glm'}`), not a live
model, so state plainly whether this tranche's proof is a live-run number or
a test-harness demonstration. Then search the committed logs for actual
`trial-llm` / `pairwise-observation` / `blocked:order-swap` /
`blocked:paraphrase` occurrences (`glm_judge_2026-07-14/log.jsonl`, the e02
run logs/judgments.jsonl files, bronze run logs) and report counts. Cite
`tests/test_trial.py`'s behavioral (non-numeric) pins
(`test_paraphrase_flip_blocks_warrant` L129,
`test_order_swap_inconsistency_blocks_pairwise` L196,
`test_consistent_pairwise_registers_indexed_warrant` L214) as design
evidence, explicitly labeled as test fixtures, not live-run counts.
    accept: REVIEW.md section explicitly separates "live-run count" from
    "test-fixture demonstration" for every number in this section

S4 (R5c, R6): **Adjudication-blindness tranche section.** Read
`experiments/2026-08-01-fix-adjudication-blindness/{DIAGNOSIS,FIX,GOAL,
REPRO,VERIFY}.md`. State what the defect was (build_att skipping unresolved
warrant pairs silently, per `docs/map/SUB-adjudication.md`'s Traps section)
and whether it is evidence about judge discrimination at all, or about a
different failure mode (a run with warrants absent entirely looking
"perfect") — this bears on the operator's hypothesis only if judges were
involved in producing the warrants that went missing; say plainly if they
were not.
    accept: REVIEW.md states explicitly whether this tranche is/is not
    judge-discrimination evidence, with the reason

S5 (R5d, R6): **Stress-triplet and lambda section.** Report the inventory
finding that all three stress-triplet run roots
(`experiments/2026-08-02-stress-triplet/home-{orbit,triage,workshop}/runs/
run-*/log.jsonl`) have zero `trial-llm`/judge event hits — these are
rule-engine traces with no judge involvement, so they contribute nothing to
the discrimination question; state this as a negative finding, not silence.
Check the tranche's `{orbit,triage,workshop}-audit.json` files for judge
content (not yet grepped by the inventory pass) and report. For lambda:
confirm via `experiments/lambda_preregistration*.yaml` and a repo-wide
search whether `src/deepreason/experiments/lambda_run.py` was ever run to a
committed result; report the prereg-only status as a finding, not an
assumption, if confirmed.
    accept: REVIEW.md states the stress-triplet zero-hit finding with the
    grep command used, and lambda's run status with the check performed

S6 (R5e, R6): **EXPERIMENT_PROGRAM_2026-07.md section.** Read and quote its
judge items: L52-54 (certified-judges rule), L63-67 (cross-family
precondition gap in `config/deepseek.yaml`), L153-200 (E0.2 judge/skeleton
red-team: predictions P1 unknown-flaw catch rate ≥0.8x known-flaw, P2
toothless-forbidden-case admission ≤10%, with falsifiers), L257-320/
L415-528/L747-789 (judge seat assignments across tiers), L810-826 (action
items). Cross-reference P1/P2 against the e02_judge_redteam and e02_t3
results from S2 — did the committed results confirm, falsify, or leave the
predictions untested? State which.
    accept: REVIEW.md states P1 and P2's outcome (confirmed/falsified/
    untested) each with the result file cited

S7 (R7, R6): **Three-way scoring section**, one subsection per reading of
the operator's phrase, each scored ONLY from numbers already pasted in S2-S6
(no new claims introduced here):
  (a) judges rule incorrectly — planted-flaw / unknown-flaw error rates
  (b) judges rule without discrimination — paraphrase-flip and order-swap
      block rates (pass/fail insensitive to case quality)
  (c) judges over-prosecute — self-preference/verbosity bias rates and
      fail-rate vs constructed ground truth
Each subsection ends with one line: SUPPORTED / CONTRADICTED / MIXED /
INSUFFICIENT EVIDENCE, and why, in the operator's terms.
    accept: REVIEW.md has three subsections, each ending in one of the four
    verdict words with a cited reason

S8 (R8): **Design-consequence section.** Given S7's verdicts, describe what
a judge-free or judge-minimal road to status-changing criticism in SOLO runs
would need. Enumerate, for each candidate mechanism already in the tree:
  - program/predicate commitments (`programs.py::evaluate`, `EXEC_PROGRAMS`)
    — what they can adjudicate (machine-decidable commitments) and cannot
    (anything requiring judgment of prose quality/relevance)
  - counterexample execution (`oracle.py::admit_counterexample`,
    `fuzz_property`) — same axis
  - the trial guard's non-judge program checks used as standalone screens:
    referential integrity (cite `docs/AUTONOMICS_REPORT.md` L17's "88
    referential-integrity" blocked-attempt count as evidence this check
    already fires without invoking a judge) and order-swap consistency
    (note precisely: order-swap catches judge SELF-inconsistency, it does
    not remove the judge from the loop — state this distinction explicitly,
    it is easy to overstate)
For each: what it CAN adjudicate, what it CANNOT, a rough price (agent/
implementation effort per the operator's "tokens are cheap, the agent is
not" law — CLAUDE.md), and a recommendation. Close with "decisions not
made" — forks this review surfaces but does not resolve, e.g. whether
`observe_only` (already the safe default per `docs/map/CON-authority.md`)
is sufficient for solo runs today or whether a new non-judge status path is
needed.
    accept: REVIEW.md section enumerates ≥3 mechanisms, each with can/
    cannot/price/recommendation, and a non-empty "decisions not made" list

S9 (R9): Create `RESULTS.md` — the honest-ledger segment per CLAUDE.md
convention: what the record shows (pointer to REVIEW.md's numbers,
summarized), and the residue — what remains unproven (lambda's untested
status, any INSUFFICIENT EVIDENCE verdicts from S7). Dated segment format
matching other tranches' RESULTS.md style.
    accept: `test -f RESULTS.md && grep -q "residue" RESULTS.md`

S10 (R2, R11, C1, C2): No file under `src/` is created, edited, or deleted
by this tranche. The tripwire check is a `git diff` against `src/` scoped
to this branch, pasted empty in VALIDATION.md.
    accept: `git diff origin/main...HEAD -- src/ | wc -l` -> `0`

S11 (R3, R10, R12, R13): Process compliance — routed through
dr-capture-request → dr-spec-change → dr-plan-steps → dr-execute-step →
dr-validate-change → dr-deliver-change, tranche directory committed and
pushed at every phase boundary, session stops after DELIVERY.md.
    accept: `git log --oneline` shows a commit at each phase boundary listed
    above (checked at delivery, not here)

## Assumptions (operator may override)

A1 (Q1): "long since redundant runs" is read as the sweep's SUBJECT
(archives to read as evidence), not an instruction to retire anything —
assumed, operator may override. R9's deliverable list names only REVIEW.md
+ RESULTS.md, and R2/C1 forbid touching runs. If S5 or S2 surface a run that
is genuinely stale and worth retiring, it is named in REVIEW.md/PARKED.md as
a candidate for a future `dr-change-orchestrator` tranche — the retirement
itself is out of scope here.

A2 (Q2): "the committed record" means git-tracked content only (what `git
log`/`git show` can see on this branch's ancestry) — assumed, operator may
override. Matches R2's "no new runs" and C1: anything not committed would
not survive the container's rollback risk (CLAUDE.md) and is not "the
record" in the CLAUDE.md sense ("the record is the only admissible evidence
about what a run did").

A3 (Q3): "priced" in S8 means agent/implementation effort (a rough
size/complexity estimate: small/medium/large plus what kind of work),
consistent with CLAUDE.md's operator design law ("Tokens are cheap; the
agent is not") — not a literal dollar or token-count figure. Assumed,
operator may override.

## Questions for operator (STOP if non-empty)

(empty — all three open questions resolved as minor-detail assumptions
above; none differ materially in effort or behavior)

## Out of scope (explicit)

- Retiring, renaming, or `git mv`-ing any run root — R2/C1 forbid new
  actions on runs; A1 records why "redundant runs" is read as evidence
  scope, not a cleanup instruction.
- Any live call to a provider (Ollama Cloud / glm-5.2) to re-test judge
  behavior — R2 forbids live calls; this review scores only what is
  already committed.
- Designing or implementing the judge-free/judge-minimal mechanism itself
  — R8 asks only for the enumerated design-consequence analysis, not code.
  A future `dr-change-orchestrator` tranche would implement it.
- Auditing every one of the ~45 files in `experiments/results/` for
  unrelated (non-judge) content — S2 names the judge-relevant subset found
  by the inventory sweep; the non-judge files (`e01_embedder_recalibration`,
  `e03_detector_calibration`, `schema_comparator_v1`, `live_smoke_v1`,
  `small_model_compat_local_verification_v1`, `embedder_install_
  verification`) are out of scope for this review.

## Frozen-surface contact forecast

none expected — checked against `docs/map/INV-frozen-surfaces.md`. This
tranche creates only Markdown files under
`experiments/2026-08-09-change-judge-evidence-review/`; it touches none of
the five frozen surfaces (`capabilities/state.py`, `harness.py`,
`invariants.py`/`verification/`, `run_manifest.py`, `qualification.py`) nor
`route_fingerprint`. No `src/` file is read-then-edited; several are
read-only for citation (`informal/audits.py`, `informal/trial.py`,
`programs.py`, `oracle.py`) and none of those four is on the frozen list.

## Blast-radius census

No symbol or file under `src/` is changed by this tranche (S10), so the
standard "what tests/map documents assert on the changed symbol" census
does not apply in its usual form. Census run anyway, over the files this
review CITES, to confirm none of them is mid-flux elsewhere on this branch:

    git status --porcelain src/deepreason/informal/audits.py \
      src/deepreason/informal/trial.py src/deepreason/programs.py \
      src/deepreason/oracle.py docs/map/SUB-evaluation.md \
      docs/map/SUB-adjudication.md docs/map/CON-authority.md
    -> (empty; confirmed clean at spec time, S10 re-confirms at validation)

## Measurements

(not a DESIGN-AND-STOP tranche — S1-S9 above already require every claim to
carry its pasted source, which is this tranche's form of "measurement";
no separate Measurements section)

## Budget

Documentation only, 0 lines touching `src/`. Itemized (`experiments/
2026-08-09-change-judge-evidence-review/` only):
  REVIEW.md ~500 lines (S1 header ~10, S2 ~150, S3 ~90, S4 ~40, S5 ~40,
    S6 ~70, S7 ~60, S8 ~90 — sum below)
  RESULTS.md ~60 lines (S9)
  CHECKLIST.md ~60 lines (already required by process, not itemized above)
  VALIDATION.md, DELIVERY.md ~80 lines each (process artifacts)

    python3 -c "print(10+150+90+40+40+70+60+90 + 60 + 60 + 80 + 80)"
    -> 830

~830 lines, ~9 commits (one per CHECKLIST step boundary plus phase
boundaries). Frozen surfaces touched: none.

Rubric: 6/6 yes — every R has a spec item with a machine-decidable accept
(S1-S11 cover R1-R13); blast-radius census pasted and classified (no `src/`
change, census run over cited files, clean); frozen-surface contact
forecast recorded (none, checked); no mechanism named by the request goes
unverified (R8's three named mechanisms — program/predicate commitments,
counterexample execution, trial-guard non-judge screens — are traced to
real functions in S8, not assumed); DESIGN-AND-STOP sections N/A (not that
shape) and skipped correctly; nothing in the spec is untraceable to an R/C
number (S1-S11 each cite R-numbers; A1-A3 cite Q-numbers).
