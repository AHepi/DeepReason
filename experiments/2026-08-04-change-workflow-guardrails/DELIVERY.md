# Delivered: the rung-4/5 guardrails, promoted to general workflow rules

Branch: both branches (operator sync policy); head is the commit
carrying this file. Zero src/, tests/, or docs/map/ lines.

## What changed

`dr-spec-change` now carries three rules every future change obeys:
(1) a mandatory written frozen-surface contact forecast at spec time,
with a hard stop for operator words BEFORE planning when contact is
plausible — the generalization of rung 4's DESIGN-AND-STOP clause and
the lesson of X9/XE1; (2) request-named mechanisms must be verified to
reach the changed code before adoption, with the no-silent-adoption /
no-silent-deviation rule — the generalization of E10/Q3 and X11; (3)
reader-before-writer for any change adding data to the typed record —
rung 4's other guardrail, generalized (X8 precedent). The SPEC template
gains a "Frozen-surface contact forecast" section so the forecast
cannot be skipped invisibly. `dr-drive-harness` now states the
`docs_verify --fast` limitation and the full-mode-before-src-commit
rule (evidence: 55b16ce9).

## Reconciliation

| R | Disposition | Proof |
|---|---|---|
| R1 forecast-at-spec-time | done | dr-spec-change step 3 + template section; accept S1 pass (3 hits) |
| R2 reachability of named mechanisms | done | dr-spec-change step 2; accept S2 pass |
| R3 --fast caveat + full-before-src-commit | done | dr-drive-harness instruments paragraph; accept S3 pass (3 hits) |
| R4 reader-before-writer | done | dr-spec-change step 3 closing guardrail |
| C1 skills only | done | diff stat: 2 skill files, 36 insertions |
| C2 evidence cited inline | done | E10, X8, X9, X11, XE1, 55b16ce9 all named at their rules |
| C3 both branches | done | push records below this commit |

## Assumptions the operator may override

A1: the handover's rungs 4-5 text stays as written — it now restates
rules the workflow itself carries, which is redundancy in the safe
direction.

## Parked

Nothing new.

## Amendment 1 (2026-08-04, operator: "Fix it")

Follow-up to the operator's question "do the workflow skills have
instructions on how to tell when sweep and verify need new tests
added?" Answer was: docs_verify yes (three skills carry the trigger),
root_sweep no. Fixed, addition-triggers only (removal explicitly
deferred by the operator): `dr-spec-change`'s reader-before-writer
paragraph now requires a sweep probe to be PROPOSED for any new
typed-record observable, in its own separate commit (a sweep change
resets the byte-identity baseline — own commit, own before/after
capture on an unchanged tree, assert-before-read probe rule);
`dr-validate-change` step 4 now fails an observable with no probe and
no written justification, and the template gains the "record
observables added vs sweep probes" line. Timely: rung 4 (module
fingerprints — exactly a new typed-record observable) is at capture
phase; these rules reach its branch before its spec phase.

## Amendment 2 (2026-08-04, operator: tests "need to survive dramatic repo changes")

The prior amendments said WHEN a test/check/probe is required, not HOW
to build one that lasts. `dr-execute-step` now carries the single
authoritative "Durable tests, checks, and probes" doctrine — five rules,
each citing the incident that paid for it: (1) pin only to committed
evidence (E7); (2) anchor to meaning not form, minimal invariant
markers, never line numbers (rung 3's marker shortening + two
form-brittle check replacements); (3) mutation-prove failability before
writing down, permanent companion mutation tests for equality claims
(rung 3's reversed-allocation backend); (4) typed-outcome comparison
with RECURSIVE wall-clock scrubbing (863a0fa3); (5) absence-tolerance
for old roots (probe rule; rung-4 guardrail). `dr-spec-change` and
`dr-implement-fix` point at it from their test-authoring steps. One
doctrine, one home, two pointers.
