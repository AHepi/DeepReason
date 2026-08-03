# Delivered: "a handover for a fresh window that can go through this step by step"

Branch: `claude/handover-defect-audit-33pv3d` (pushed, tree clean; head is
the commit carrying this file).

## What changed

`docs/HANDOVER_2026-08-03.md` now exists: the modularisation ladder as a
seven-rung program a fresh Sonnet 5 session can execute rung by rung. Each
rung is a complete specification — which workflow family to route through,
goal, in-scope and not-in-scope, machine-decidable acceptance, and stop
conditions — because the research says Sonnet 5 executes complete specs
near Opus-level but does not generalize past their stated scope. The rungs
carry execution classes matched to that judgment: rungs 1–3 (sockets on
paper merged with the parked R8 job, Config switches preserving defaults,
a registry in front of school population) are EXECUTE; rungs 4–5
(fingerprints in the typed record, the dumb alternative) are EXECUTE WITH
GUARDRAILS — hard rules against touching manifest schemas or qualification
digests, and live runs only with operator-provided credentials; rungs 6–7
(plugin qualification, authority policy) are DESIGN-AND-STOP — the
deliverable is a SPEC and the tranche ends until you reply. The handover
also carries the environment traps verified this session (the rollback
dev-dependency trap that produced two spurious failures, the sweep's
two-instrument census, the known flake) and the open items that are
deliberately NOT part of the program. One slight documentation change per
your conditional: `dr-drive-harness` gains a "Calibration for less capable
executors" block making literal-execution discipline part of the driving
manual itself.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "a handover for a fresh window that can go through this step by step" | done-with-assumption A1, A2 | commit 5b5afeb6; VALIDATION S1 (seven rungs, complete per-rung specs) |
| R2 | "it will be completed by Sonnet 5" | done | executor-calibration section + per-rung execution classes; VALIDATION R2 |
| R3 | "do some research on Sonnet 5" | done-with-assumption A3 | SPEC.md "R3" section, sourced from the repo's sanctioned model reference; VALIDATION S2 |
| R4 | "make slight modifications to the documentation if you aren't hopeful about it's capabilities" | done — condition fired at "slight" | judgment: hopeful for bounded execution (rungs 1–3), not for frozen-adjacent design (rungs 6–7 gated); dr-drive-harness calibration block; VALIDATION S3 |

## Assumptions the operator may override

- A1: location `docs/HANDOVER_2026-08-03.md`, by the 2026-08-02 precedent.
- A2: "step by step" = rung-by-rung with per-rung gates; rungs 6–7 always
  stop for your approval; one rung per tranche.
- A3: the sanctioned in-repo Claude model reference was the research
  source; no web search added.
- A4: "documentation" = the handover plus one dr-drive-harness block;
  CLAUDE.md/README untouched (refreshed earlier today; nothing in the
  findings invalidates them).

## Map delta

No map change — the handover and the skill are outside `docs/map/`'s
charter; zero `src/` changes. docs_verify 0 failed / 0 audit findings /
0 dangling. Gate disposition: src/tests diff against the tranche base is
EMPTY; standing gate 3290 passed, 0 failed at tree `a31f1082` cited with
the delta analysis (VALIDATION, "Full gate").

## Parked (not done, not promised)

Nothing new parked by this tranche. The program's own exclusions (census
delta, ladder-audit fixes, flake, prose-immunity price, dead Config value,
batch-pack clip, Sweep ratchet) are listed in the handover's "Open items"
section, each already carried by an earlier ledger.
