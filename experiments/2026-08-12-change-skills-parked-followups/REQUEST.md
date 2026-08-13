# Request: implement the parked skills-overhaul follow-ups

Captured: 2026-08-12, operator message immediately following delivery
of `experiments/2026-08-12-change-skills-overhaul/DELIVERY.md`.

## Verbatim

> Can you implement changes please

## Reading (derived, not assumed silently)

The message names no specific change. It arrived as the very next
message after a delivery report whose own "Parked" section listed
exactly two ready-to-send follow-ups (P1, P2) and whose "recommended
next" line named P1 explicitly; the assistant's own closing message in
that turn also explicitly offered both as "already parked... rather
than acted on unilaterally" and, for P2, "a two-minute follow-up if you
want it." Per `dr-ask-the-right-question`'s reading-the-operator table
("an apparent terse instruction, shape unstated → derive the shape from
repo conventions and proceed; note what was assumed"): the plural
"changes" and the immediate timing are read as authorizing BOTH parked
items, not a request to pick one. This is stated as the reading here,
in writing, per the rule that interpretation happens in `dr-spec-change`
where it is reviewable — not silently.

## Requirements

R1 (behavior): "Can you implement changes please" — read as: implement
   `experiments/2026-08-12-change-skills-overhaul/PARKED.md` P1 — give
   `dr-drive-harness`'s "never generalize an instruction beyond its
   stated scope" negation a mechanical enforcing GATE, per that entry's
   own one-goal statement and its two named candidate resolutions
   (a lint-style scope check, or an operator-accepted judgment-only
   erratum).

R2 (behavior): Same verbatim message, read as also covering PARKED.md
   P2 — trim `dr-ask-the-right-question`'s one remaining W5
   (incident-story) row (`dr-ask-the-right-question-16`) to a rule plus
   a bare citation, matching the pattern already applied to the other
   8 W5 rows in the prior tranche.

## Standing constraints

C1: This is a NEW tranche, not a reopening of the closed
   `2026-08-12-change-skills-overhaul` tranche — `dr-deliver-change`'s
   own exit criterion: "New suggestions start a fresh tranche via
   `dr-change-orchestrator`."
C2: `src/` and `tests/` stay byte-untouched (inherited standing
   constraint from the prior tranche; nothing here touches code).
C3: Author every artifact (including this one) to `authoring-skills`'s
   rules, per CLAUDE.md's binding-authority instruction for this whole
   skill family.

## Open questions (for dr-spec-change)

Q1: PARKED.md P1 names two candidate resolutions for the ungated
   negation — a new lint-style GATE, or an operator-accepted
   judgment-only erratum. Which one R1 means is not stated by "implement
   changes" and is a genuine, non-dominated fork (a new automated check
   vs. a documentation-only acceptance are materially different pieces
   of work) — carried to `dr-spec-change` for the dominance test, not
   answered here.

## Amendments

(append-only; none yet)
