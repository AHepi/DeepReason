# Request: "do it" — make the documents honest on the audit's Part 6

Captured: 2026-09-09, from the operator's one-word approval of the monitor's
recommendation, plus the executor brief that carries the four deliverables.

## Map preflight (recorded per dr-change-orchestrator)

Resolved ids: NONE. `docs/map/INDEX.md` routes subsystems, concepts, seams,
invariants and recipes; every file this tranche touches is a narrative or
operating document outside the map's coverage (`docs/CAN_LLMS_EXPLORE.md`,
`docs/BASIN_REPORT.md`, `docs/ERRATA.md`, `CLAUDE.md`, seven further `docs/*`
narrative files, and `experiments/results/INDEX_2026-07-13.md`).
`docs/map/INV-frozen-surfaces.md` read before designing: none of the five
frozen surfaces (capability state digests, harness event application,
`invariants.py` + `verification/`, run manifest schemas, qualification
subject digests) is a document this tranche touches, and no `src/` path is
touched at all.

## Verbatim

Operator, 2026-09-09, answering the monitor's recommendation to make the
documents honest on the audit's §6.1-§6.4:

> do it

The commissioning brief, quoted in full because it carries the operator's
authority through the monitor and the requirements derive from its words:

> EXECUTOR WINDOW — CHANGE (documents only): act on Part 6 of
> `experiments/2026-09-08-audit-llm-capabilities/AUDIT_REPORT.md`. Route
> through `dr-change-orchestrator` starting with `dr-capture-request`. The
> operator's words, the authority: "do it" (2026-09-09), answering the
> monitor's recommendation to "make the documents honest" on the audit's
> §6.1–§6.4. Read Part 6 in full and every document it names before
> capturing.
>
> Four deliverables, each a small edit that leaves the original text in place
> and adds a dated note (the `INDEX_2026-07-13.md` "withdrawn claims" pattern
> the audit cites as the precedent; never delete a claim, mark it):
>
> 1. §6.4 — In `docs/CAN_LLMS_EXPLORE.md` and `docs/BASIN_REPORT.md`, a note
> at the top and beside Result 1 / the soft-basin claim: the hash-based
> novelty numbers were DEMOTED to unverified by E0.1
> (`experiments/results/INDEX_2026-07-13.md:75-77`, all four predictions
> refuted, contamination 1.0 on both roots), E2.3 was appointed the gate and
> never ran, and the finding stands as "unverified by this repository's own
> ruling". State which numbers the demotion reaches and which it does not
> (the gate-block counts and the 4.3× cost figure do not depend on the
> demoted instrument — the audit §6.4 says why). Also a one-line entry in
> `docs/ERRATA.md` (next free number) recording the demotion's reach.
>
> 2. §6.1 — In each of the nine citing documents the audit names, one line
> saying the data file is archived at commit `3d839b3` (the last commit with
> the complete record) and that a shallow clone cannot follow it; for the ten
> unindexed report files, an index line in
> `experiments/results/INDEX_2026-07-13.md` stating for each whether it is
> recoverable at that commit or not (check `git cat-file -t 3d839b3` and say
> what it returns here).
>
> 3. §6.3 — In CLAUDE.md's judge law (the 2026-08-28 amended entry), split
> "0-2.5% false conviction of sound work" into its two sources with their
> units: 0.0 = the defended court's sustain rate on 42 clean items
> (`court_calibration_v1_report.json`); 2.5% = an unanimous judge pair's flag
> rate on 40 clean items with no defender (`e02_t2_voting_report.json`). Do
> not change the law's meaning; add the sourcing in the same sentence.
> Errata entry.
>
> 4. §6.2 — In `docs/CAN_LLMS_EXPLORE.md` (or the capability-facing document
> the audit deems right, say which), a paragraph citing the eleven-model
> judge zoo (`e02_t3_judge_zoo_report.json`, 1,561 judgments, P3 refuted with
> zero qualifying seats) as the widest capability result in the repository,
> with the audit's own caveat that its unlabelled and clean items were
> authored by one model.
>
> Rules: no instrument run (no gate, no docs_verify, no live call);
> `docs/map` documents touched only if a `check:` you add can be run as a
> single command and you run only that; nothing under `src/`, `tests/`,
> `experiments/` except the index file named. Each edit cites the audit
> section and the primary artifact. Deliver through `dr-validate-change`
> (validation here is reading: every added line points at a committed file
> that exists) and `dr-deliver-change` with the R-by-R table. Commit and push
> with retry (2s/4s/8s/16s). Stop when delivered and pushed.

## Requirements

R1 (artifact): "In `docs/CAN_LLMS_EXPLORE.md` and `docs/BASIN_REPORT.md`, a
note at the top and beside Result 1 / the soft-basin claim: the hash-based
novelty numbers were DEMOTED to unverified by E0.1 ... E2.3 was appointed the
gate and never ran, and the finding stands as 'unverified by this
repository's own ruling'."

R2 (artifact): "State which numbers the demotion reaches and which it does
not (the gate-block counts and the 4.3× cost figure do not depend on the
demoted instrument — the audit §6.4 says why)."

R3 (artifact): "Also a one-line entry in `docs/ERRATA.md` (next free number)
recording the demotion's reach."

R4 (artifact): "In each of the nine citing documents the audit names, one
line saying the data file is archived at commit `3d839b3` (the last commit
with the complete record) and that a shallow clone cannot follow it."

R5 (artifact): "for the ten unindexed report files, an index line in
`experiments/results/INDEX_2026-07-13.md` stating for each whether it is
recoverable at that commit or not (check `git cat-file -t 3d839b3` and say
what it returns here)."

R6 (artifact): "In CLAUDE.md's judge law (the 2026-08-28 amended entry),
split '0-2.5% false conviction of sound work' into its two sources with their
units: 0.0 = the defended court's sustain rate on 42 clean items
(`court_calibration_v1_report.json`); 2.5% = an unanimous judge pair's flag
rate on 40 clean items with no defender (`e02_t2_voting_report.json`). Do not
change the law's meaning; add the sourcing in the same sentence."

R7 (artifact): "Errata entry." (for R6)

R8 (artifact): "In `docs/CAN_LLMS_EXPLORE.md` (or the capability-facing
document the audit deems right, say which), a paragraph citing the
eleven-model judge zoo (`e02_t3_judge_zoo_report.json`, 1,561 judgments, P3
refuted with zero qualifying seats) as the widest capability result in the
repository, with the audit's own caveat that its unlabelled and clean items
were authored by one model."

R9 (process): "each a small edit that leaves the original text in place and
adds a dated note (the `INDEX_2026-07-13.md` 'withdrawn claims' pattern the
audit cites as the precedent; never delete a claim, mark it)."

R10 (process): "Each edit cites the audit section and the primary artifact."

R11 (process): "Deliver through `dr-validate-change` (validation here is
reading: every added line points at a committed file that exists) and
`dr-deliver-change` with the R-by-R table."

R12 (process): "Commit and push with retry (2s/4s/8s/16s). Stop when
delivered and pushed."

## Standing constraints

C1: "no instrument run (no gate, no docs_verify, no live call)" — brief,
Rules paragraph. Reinforced by CLAUDE.md's MANDATORY block: a review-kind
window runs no verification instrument without the operator's permission for
that task, and none was given here.

C2: "`docs/map` documents touched only if a `check:` you add can be run as a
single command and you run only that" — brief, Rules paragraph.

C3: "nothing under `src/`, `tests/`, `experiments/` except the index file
named" — brief, Rules paragraph.

C4: "Route through `dr-change-orchestrator` starting with
`dr-capture-request`" — brief, opening paragraph.

C5: "Develop on branch `claude/audit-part-6-corrections-9c9gsj`" — session
instructions.

## Open questions (for dr-spec-change)

Q1: The brief says "the nine citing documents the audit names", but the
audit's nine and the documents that actually carry a citation to one of the
thirteen retired files are not the same set. Which set gets the note?

Q2: R5 asks whether each unindexed file "is recoverable at that commit or
not", and directs a `git cat-file -t 3d839b3` check whose result must be
reported. If that command cannot resolve the commit here, what may the index
line honestly assert about recoverability?

Q3: R8 offers a choice of destination document ("or the capability-facing
document the audit deems right, say which"). Which one?

Q4: R1 asks for a note "at the top" of two documents whose tops are a title
plus an italic standfirst. Where exactly does the note go so it is read
before the claim it qualifies?

## Amendments

(append-only)
