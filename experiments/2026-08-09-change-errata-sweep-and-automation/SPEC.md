# Spec for: update the Errata (sweep + automation)
Traces: every item cites R/C numbers. Untraceable items are bugs.

## Items

S1 (R1, R2, R4c): append E13 to `docs/ERRATA.md` — CLAUDE.md's directory
map named only the v1.5 spec amendment (before: "specs (harness v1.3 +
v1.5 amendment, ... BASIN_REPORT)"), omitting v1.4/v1.6 which exist and
are current; already fixed in place, commit `1f6c24ab` ("CLAUDE.md:
correct stale spec listing (v1.4/v1.5/v1.6 amendments exist)"), never
ledgered.
    accept: `git log --oneline -1 -- docs/ERRATA.md | grep -q .` (entry
    committed) AND `grep -c "^\*\*E13" docs/ERRATA.md` -> 1

S2 (R1, R2, R4c): append E14 to `docs/ERRATA.md` — CLAUDE.md's
turmite/jolt cycle-0 paragraph carried no dating clause and read as
describing current blockers though both were fixed 2026-08-01; already
fixed in place, commit `7e8f42402` ("CLAUDE.md: date the cycle-0
examples..."), never ledgered.
    accept: `grep -c "^\*\*E14" docs/ERRATA.md` -> 1

S3 (R1, R2, R4e): append E11 to `docs/ERRATA.md` — rung 4
(`experiments/2026-08-04-change-rung4-module-fingerprints/`) moved the
module-fingerprint stamp to `run(cycles > 0)` and added a check
asserting it does NOT fire at construction, but left
`docs/map/SEAM-schools-x-scheduler.md`'s adjacent prose saying it fires
"at construction". Found and corrected in passing by rung 5
(`experiments/2026-08-04-change-rung5-dumb-alternative-backend/
DELIVERY.md:113-116`) the same day; never ledgered.
    accept: `grep -c "^\*\*E11" docs/ERRATA.md` -> 1

S4 (R1, R2, R4e): append E12 to `docs/ERRATA.md` — this ledger's own E5
misidentifies the three no-manifest calibration roots as the
`runs/jolt_positive_headroom_v3_1/` roots (which actually RAISE); the
true no-manifest three are the `experiments/bronze_flat_2026-07-13/*`
roots, which are INSIDE `root_sweep.py`'s glob, not outside it. E5's
headline finding (45-root baseline not reproducible) is unaffected.
Measured and explicitly deferred by
`experiments/2026-08-05-fix-expired-census-readers/PARKED.md` P1a
("suggested disposition: a one-entry append to docs/ERRATA.md"); per
ERRATA.md's own append-only rule, E5 is not edited — this is a new
entry.
    accept: `grep -c "^\*\*E12" docs/ERRATA.md` -> 1

S5 (R1, R2, R4e): append E15 to `docs/ERRATA.md` — S6's pre-registration
(`experiments/2026-08-08-live-two-seat-ab-s6/PLAN.md:83-89`) and first
RESULTS.md segment (lines 98-111) characterized `property_designer`
never firing live as an "accepted, PRE-REGISTERED stochastic miss"
under CLAUDE.md's capability-channel stochasticity doctrine. A dated
correction segment in the same RESULTS.md (lines 168-227) shows this
was wrong: the path is a structural bootstrap circularity
(`property_oracle_commitment`'s only caller,
`admit_counterexample`, itself requires the commitment to already
exist) — probability 0, not low, and not a case the stochasticity
doctrine covers. Corrected 2026-08-08 by the dated RESULTS.md segment
(original not edited) and cross-referenced in PARKED.md P1; PLAN.md
itself stands uncorrected (pre-registration convention). Never ledgered
in `docs/ERRATA.md`.
    accept: `grep -c "^\*\*E15" docs/ERRATA.md` -> 1

S6 (R1, R2, R4e): append E16 to `docs/ERRATA.md` — S6's
`PARKED.md` P3 described the `continue`-crash fixture as having "the
pending item at resume time was an ATOMIC child... two sibling children
already `terminal_status: 'completed'`" (implying an incomplete child
was necessary for the crash).
`experiments/2026-08-08-fix-l1-continue-resumable-crash/
DIAGNOSIS.md:117-124` checked this directly against the fixture's own
record and refuted it: the one recorded decomposition is fully
resolved, and the crash fires on ANY criticism atomic child ever
admitted, pending or not — a broader, different mechanism than P3
described. Corrected 2026-08-08 by the L1 tranche's diagnosis; S6's own
PARKED.md stands as written (closed tranche). Never ledgered.
    accept: `grep -c "^\*\*E16" docs/ERRATA.md` -> 1

S7 (R1, R2, R4b): append E17 to `docs/ERRATA.md` — O1's RESULTS.md
(lines 47-53, 182-183) and DELIVERY.md (lines 29-32) reported "14
genuine multi-node floating chains" as the rung's one positive catch,
using an operationally-proxied "ground" definition. O2's SPEC.md
(lines 195-255), re-running against the spec-derived ground definition
required by the operator's Amendment 1, found the count collapses to
zero for all 48 roots and all 14 of O1's flagged chains, and states
plainly: "R5's premise does not survive the spec-true audit." O1's own
committed documents remain unmodified and still assert the 14-chain
catch; O2 stopped at SPEC.md (a DESIGN-AND-STOP tranche per its own
preplan) and never delivered a closing note back into O1. Correction
stands only in O2's SPEC.md prose until this entry.
    accept: `grep -c "^\*\*E17" docs/ERRATA.md` -> 1

S8 (R3, C2, R4d): verify and correctly EXCLUDE the S5 budget-headline
candidate ("220-300" vs itemization summing to "435", R21/R22). Record
in this SPEC.md's Assumptions/Out-of-scope why no ERRATA.md entry is
written: `experiments/2026-08-07-change-seats-in-record-s5/
REQUEST.md` Amendments 2/3 (R21/R22) are the tranche's OWN stated
correction mechanism ("SPEC.md's own text is not edited — R21 is the
ledgered correction of record") — an in-tranche revision-supersession,
excluded by C2. No document outside the S5 tranche misstates the
episode (every other repo hit — G1's REQUEST/SPEC, `docs/map/
INV-frozen-surfaces.md:156`, `docs/proposals/
DETERMINISTIC_GATES_PREPLAN.md:50`, `.claude/skills/dr-spec-change/
SKILL.md:104` — cites it accurately as history).
    accept: `grep -c "220-300\|220–300" docs/ERRATA.md` -> 0 (no entry
    written for this candidate)

S9 (R5): add a one-paragraph diagnosis, in this SPEC.md, of why the
errata ledger is not automatically updated (used verbatim as the basis
for R6's checkpoint text — no separate artifact needed since R5 asks
only for a diagnosis, not a new document). See "Diagnosis (R5)" below.
    accept: this section exists in SPEC.md and is quoted/paraphrased in
    the CHECKLIST step that edits the two skills

S10 (R6, R7): amend `.claude/skills/dr-deliver-change/SKILL.md` —
add a mandatory "Errata check" step to Procedure (between step 3b "Map
delta" and step 4 "Write DELIVERY.md"), and an "## Errata" section to
the DELIVERY.md template, matching the file's own existing
state-not-silence pattern (step 3b's "'No map change' is a legitimate
answer... say it rather than omitting the section"). Checkpoint
wording per R6 verbatim, adapted only to name DELIVERY.md (this
skill's own artifact) per Q2's resolution (A2 below).
    accept: `grep -c "errata" .claude/skills/dr-deliver-change/SKILL.md`
    -> >=3 (procedure step + template section + exit criterion)

S11 (R6, R7): amend `.claude/skills/dr-verify-outcome/SKILL.md` —
add the same mandatory "Errata check" to the "Closing the tranche (on
PASS)" bullet list, and an "Errata:" line to the VERIFY.md template
(next to the existing "Residue (honest): ... or 'none'" line, the
skill's own existing state-not-silence pattern). Checkpoint wording per
R6 verbatim, adapted to name VERIFY.md per A2.
    accept: `grep -c "errata" .claude/skills/dr-verify-outcome/SKILL.md`
    -> >=2 (closing bullet + template line)

## Assumptions (operator may override)

A1 (Q1): ERRATA_EXECUTOR.md is out of this tranche's scope. The
verbatim request enumerates ordinary-committed-document candidates only
(seat rungs, O rungs, CLAUDE.md, SPEC budget arithmetic) and names
`docs/ERRATA.md` by path throughout; ERRATA_EXECUTOR.md has a
DIFFERENT single-writer rule (monitor-only `X<n>` sequence) that this
executor session is not the holder of. All three sweep agents
independently classified every confirmed finding as ERRATA.md-scoped
(ordinary committed documents), so this assumption has no material
effect on the delivered work — nothing found belongs in
ERRATA_EXECUTOR.md. Assumed, operator may override.

A2 (Q2): the R6 checkpoint's wording is reused near-verbatim in both
skills, substituting only the artifact name each skill actually closes
with (DELIVERY.md for dr-deliver-change, VERIFY.md for
dr-verify-outcome) — matching C3's "follow the file, don't innovate its
format" applied to each skill's own vocabulary (dr-deliver-change
already speaks in "sections added to DELIVERY.md"; dr-verify-outcome
already speaks in "lines added to VERIFY.md"). Assumed, operator may
override.

## Questions for operator

(none — Q1 and Q2 resolved above via dr-ask-the-right-question's
dominance test: the record and C3's own stated principle answer both
without materially different effort/behavior on either reading.)

## Out of scope (explicit)

- Editing docs/ERRATA_EXECUTOR.md (see A1) — not requested, and no
  confirmed finding belongs there.
- Editing docs/proposals/GROUNDED_OVERLAY_PREPLAN.md, S6's PLAN.md, S6's
  PARKED.md, or O1's RESULTS.md/DELIVERY.md themselves — the operator's
  own R2 words are "what the document claimed, where, what the record
  shows, where corrected"; correcting the errata ledger is the task,
  not rewriting the corrected-in-place-elsewhere or closed-tranche
  originals (E15/E16/E17 explicitly document that those originals stand
  unedited, per each tranche's own convention).
- Any NEW code, test, or map-document change — this tranche is
  docs/skills only (R1, R2, R5, R6 are all artifact/process kinds; no
  requirement is `behavior` against `src/`).
- Adding `check:` lines to ERRATA.md entries — C3 says follow the
  file's own convention, and E1-E14 carry zero `check:` lines; none are
  added here either.
- Investigating or ledgering the D1 tranche's PARKED P-D2-3 (a
  pre-existing bronze-report gate/census mismatch) or S1/S3/S4's shared
  module-fingerprint-double-stamp code defect — both are live CODE
  defects, not committed-document claims later found wrong; they belong
  to a future `deepreason-orchestrator` tranche, not this ledger (C2's
  boundary, ERRATA.md's own scope note: "Code defects have tranches").

## Frozen-surface contact forecast

none expected — checked against `docs/map/INV-frozen-surfaces.md`. This
tranche touches `docs/ERRATA.md` (an append-only prose ledger, not
`capabilities/state.py`, `harness.py`, replay-validation formats,
manifest schemas, or qualification-subject digests) and two files under
`.claude/skills/` (process documentation, not `src/deepreason/` at
all). No `src/` line changes anywhere in this tranche.

## Blast-radius census

    grep -rn "dr-deliver-change" tests/ docs/map/
    grep -rn "dr-verify-outcome" tests/ docs/map/
    grep -rn "docs/ERRATA.md" tests/ docs/map/ .claude/skills/

Results:
- `tests/`: no hits for any of the three greps — no test asserts on
  skill file content or ERRATA.md content/line-count. `no hits`.
- `docs/map/`: no hits — `docs/map` documents `src/deepreason/`, per
  its own stated coverage boundary; skills and docs/ERRATA.md are
  outside it (confirmed in REQUEST.md's Map preflight section). `no
  hits`.
- `.claude/skills/`: `docs/ERRATA.md` is referenced by
  `.claude/skills/dr-drive-harness/SKILL.md` (session-preflight reading
  list) and `.claude/skills/dr-ask-the-right-question/SKILL.md` (cites
  ERRATA.md as a record-authority source) — both MUST NOT MOVE (this
  tranche adds entries to ERRATA.md, appended, so its existing content
  and role as a preflight-read target are unchanged; the entries this
  tranche adds cite Section headers that already exist in the file,
  and no cross-reference to a specific E-number in either skill file
  exists to break). Verified: `grep -n "ERRATA" .claude/skills/
  dr-drive-harness/SKILL.md .claude/skills/dr-ask-the-right-question/
  SKILL.md` cites the file by path/role only, never a specific entry
  number.

No hit anywhere requires updating outside the two skill files this
tranche already targets and `docs/ERRATA.md` itself.

## Budget

Itemized: S1-S7 (7 ERRATA.md entries, ~15-25 lines each, one paragraph
in the existing prose style, no new section headers needed beyond one
new dated `##` header) ~140 lines; S10 (dr-deliver-change/SKILL.md:
+1 procedure step ~8 lines, +1 template section ~4 lines, +1 exit
criterion line ~2 lines) ~14 lines; S11 (dr-verify-outcome/SKILL.md:
+1 closing-bullet ~6 lines, +1 template line ~2 lines) ~8 lines.

    python3 -c "print(140 + 14 + 8)"
    162

~162 lines, 1 commit (docs-only tranche; per CLAUDE.md's own "the map
moves in the SAME COMMIT as the code" spirit and this tranche's small
size, ERRATA.md entries and the skill amendments land together — no
`src/` change exists to require the code+map co-commit rule at all).
Frozen surfaces touched: none.

## Diagnosis (R5)

No delivery-phase skill mandates an errata check. `dr-deliver-change/
SKILL.md`'s Procedure has five steps (final tree check, reconciliation
table, assumptions/PARKED surfacing, map delta, write DELIVERY.md) and
none of them asks "did this tranche find a committed document's claim
wrong?" — the closest existing checkpoint, step 3b's map delta, is
scoped to `docs/map/` only, which by the map's own stated coverage
boundary excludes ERRATA.md, CLAUDE.md, and RESULTS.md files entirely.
`dr-verify-outcome/SKILL.md`'s "Closing the tranche (on PASS)" list has
the same gap. Every existing ERRATA.md entry so far was written because
some session happened to remember the ledger existed and appended to it
as an unprompted extra step — E10's own text is explicit that this is
opportunistic ("Found at spec time by the rung-3 executor... Corrected
2026-08-04"), not gated by any phase's exit criteria. A convention with
no enforcing checkpoint is discoverable only by a session that already
knows to look for it, which is exactly why seven genuine corrections
(E11-E17) accumulated across five days and eleven-plus tranches without
being ledgered until this sweep found them by brute-force re-reading —
the mechanism silently starves precisely because nothing routes through
it by default.

## Process requirements (R8, R9, R10)

R8 ("Full gate at the boundary; docs_verify full"), R9 ("Deliver
through validate/deliver; push each boundary; stop when delivered"),
and R10 ("route through dr-change-orchestrator... ledger [the
operator's words] in REQUEST.md") are process-kind requirements with no
dedicated S-item: they are satisfied by following the orchestrator's
own phase sequence (this SPEC.md → CHECKLIST.md → dr-validate-change →
dr-deliver-change) rather than by an artifact this SPEC.md would
itemize. R10 is already satisfied (REQUEST.md's Verbatim section).
R8/R9's acceptance is the validate/deliver phases' own exit criteria,
not a separate check here.

## Rubric pass

- every R has a spec item with a machine-decidable accept, or is a
  process requirement satisfied by phase adherence (R8-R10, above)? yes
- blast-radius census pasted and every hit classified? yes (three
  greps, two hit, both classified MUST NOT MOVE and unaffected)
- frozen-surface contact forecast recorded? yes (none expected,
  checked)
- every mechanism the request names traced to code/record it actually
  reaches? yes — R4's five candidates were each independently verified
  against primary-source quotes (commit diffs, RESULTS.md/PARKED.md/
  SPEC.md line ranges) before being adopted as S1-S7/S8, not copied
  from the operator's list unverified (R4's own words: "do not copy my
  list blind")
- DESIGN-AND-STOP sections (Measurements/Options)? not applicable —
  this is not a [DESIGN-AND-STOP] request
- nothing in the spec untraceable to an R/C number? yes (every S-item
  and A-item cites one)

Rubric: 6/6 yes
