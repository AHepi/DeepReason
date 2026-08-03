# Spec for: the executor-infrastructure errata + standing monitor

## Items

S1 (R1, R2, C1): NEW `docs/ERRATA_EXECUTOR.md` — append-only ledger for
the less-capable-executor infrastructure. Charter states: what "the
process" covers (the two cross-cutting skills, the calibration blocks,
the skills index, the Sonnet-calibrated handover and its per-rung specs);
what an entry is (an infrastructure claim the executor's RECORD showed
wrong, misleading, or load-bearing-and-correct — successes are evidence
too); entry discipline inherited from docs/ERRATA.md (append-only,
evidence pointers, cite the session/tranche/commit); and an explicit
AWAITING-FIRST-RESULTS state — zero entries until an executor session has
committed artifacts (R2).
    accept: file exists; grep hits for "append", "Awaiting",
    "dr-drive-harness", "HANDOVER_2026-08-03"; zero entry headings (E1..)
    present.

S2 (R1, R3): cross-wiring — (a) one line in docs/ERRATA.md's scope note
pointing process-level executor findings to the new ledger; (b) the
handover's calibration section gains a feed-instruction: when a spec here
or a skill misleads you or leaves you silent, append the observation to
docs/ERRATA_EXECUTOR.md with the evidence pointer, then proceed via
dr-ask-the-right-question — the executor itself is the cheapest telemetry
(Q2: yes).
    accept: grep ERRATA_EXECUTOR in docs/ERRATA.md -> 1;
    grep ERRATA_EXECUTOR docs/HANDOVER_2026-08-03.md -> >=1.

S3 (R3): standing monitor — a self-bind Routine (cron, every 2 hours)
waking THIS session to: fetch the remote; detect new branches or new
commits beyond our head; when executor tranches appear, read their typed
artifacts (VALIDATION/DELIVERY/PARKED/ERRATA_EXECUTOR entries), append
infrastructure findings to docs/ERRATA_EXECUTOR.md (evidence-pointed),
push, and report to the operator ONLY when something noteworthy happened;
stay silent otherwise. Cadence 2h chosen as balance (executor rungs are
multi-hour; hourly is the platform minimum) — operator may retune.
    accept: create_trigger returns a trigger id; the id and prompt are
    recorded in DELIVERY.md.

## Assumptions (operator may override)

A1 (Q1): name `docs/ERRATA_EXECUTOR.md`, sibling of docs/ERRATA.md.
A2 (Q2): the executor feeds its own ledger; this session's monitor
verifies and supplements — both write the same append-only file.
A3 (Q3): mechanism = self-bind cron Routine into this session, every 2
hours; silent when nothing changed.

## Out of scope

Writing any verdict about the infrastructure now (R2 forbids it);
executing or reviewing ladder rungs themselves.

## Budget

~90 lines docs, 2 small edits, 1 Routine, 2 commits. No src/. Frozen
surfaces: none.
