<!-- DR-TRANCHE-F3 -->
# Delivered: "turning research and, simulation and coding permanently on" + the wander cap

Branch: `claude/deepreason-f3-rebuild-9tf39b` (pushed, tree clean)

## What changed

**The three evidence-minting channels are on by default, through a registry
rather than three scattered opt-ins.** `src/deepreason/channels.py` declares
research, simulation and code-testing — each with what it mints in the
operator's own 2026-08-14 words, its default (on), the one `Config` field that
turns it off, WHERE that toggle is read, and the ruling behind it. Research was
previously off for every run that did not set an environment variable, which is
a channel that does not exist for anyone who did not know to look. The
decommissioned website pipeline is a declared ABSENCE, so the registry answers
about it instead of being silent.

**The wander cap is a selectable allocation policy, not a new mechanism.**
`src/deepreason/wander.py` takes four numbers and returns a decision; the
scheduler applies it as a CANDIDACY gate in exactly the shape
`INTEGRATION_BUDGET_SHARE` already used, one lineage class higher, and never
touches the rank key. Two policies ship (`wander-cap.v1` and the null
`open-lineage.v1`) because a registry with one entry cannot show that selection
works. The floor defaults to 0.5 — the value that would have bound on the run
W6 measured and not before it.

**The allocation controller's decisions now reach the wire.** W7 found 47
recorded tuning decisions across the whole committed population, none of which
became the `max_tokens` of any later call. Verified on the current tree before
any code was written (SPEC.md §S0): `Adapter._completion_cap` returned the route
ceiling on every qualified route, so the only field the controller writes had no
reader. One expression now books the seat's SETTLED cap bounded by that ceiling.

**All four phantom allocation signals emit, and none was struck** — each is
genuinely consumed, so striking one would make the registry less true. The
census is a test now rather than an audit.

Files: `channels.py`, `wander.py` (new); `config.py`, `run_manifest.py`,
`v6_policy.py`, `preparation.py`, `allocation.py`, `signals.py`,
`controller.py`, `scheduler/scheduler.py`, `llm/adapter.py`. Three new test
files, four amended. Eight map documents, one of them new.

## Reconciliation

Every R in REQUEST.md, in order, including all four amendments.

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "turning research ... permanently on" | done | S1/S3; `test_evidence_channels.py`, `test_v6_policy_preset.py` |
| R2 | "turning ... simulation ... permanently on" | done | S1/S4; simulation byte-identical when on, empty policy when off |
| R3 | "turning ... coding permanently on" | done-with-assumption **A1, A3** | S1/S5; declared ON with `enforcement="unconditional"`, proved by DRIVING an exec-oracle to PASS and FAIL |
| R4 | "Turning one OFF remains a lawful configuration ... nothing refuses" | done for research + simulation; **PARKED P1 for code-testing** | S2/S4; `CHANNELS_DISABLED`, typed `CHANNEL_UNKNOWN` notice, all-three-off compiles |
| R5 | "Website stays decommissioned" | done | S6; `DECOMMISSIONED`, and naming it in the toggle still yields False |
| R6 | "Report the qualification-digest cost ... price it, don't stop" | done | S7; MEASUREMENTS.md — `d47cb2bf…` → `f3bb6562…`, one battery per home |
| R7 | one SPEC line on why this belongs in the REBUILD | done | SPEC.md headline, and S21 at length |
| R8 | "declared budget-share FLOOR (Config knob, versioned-source line for every schema version)" | done | S8; `SEED_PROBLEM_BUDGET_FLOOR` + its `data.pop`, digest byte-identical at every version |
| R9 | "deprioritized by the existing attention/allocation machinery" | done-with-assumption **A5, A6** | S9/S10; candidacy gate beside `INTEGRATION_BUDGET_SHARE`, rank key untouched |
| R10 | "a typed disclosure when throttling engages" | done | S11; share every cycle, throttle once per engagement, plus an attackable policy artifact |
| R11 | "attention only, never labels ... mutation-prove it" | done | S12; `proof/s12_mutation.txt` — both mutations RED, baseline and restore GREEN |
| R12 | "Ship it through the revise-allocation-policy recipe" | done | S9/S11/S14; the recipe now documents two policy families |
| R13 | "make the policy you ship emit the signals it consumes, or strike the phantoms" | done — **all four EMITTED, none struck** | S13/S14; and the census is a test |
| R14 | "every configuration class still compiles" | done | S15; eight classes including all-three-off and a typo |
| R15 | "the floor holding, the throttle disclosed, and ZERO label differences" | done | S16 + S12; the stub run, the control arm, the differential |
| R16 | "the shipped policy's signals emit on a stub run" | done | S14/S16 |
| R17 | "Full gate 0 failed; docs_verify full; map moves in the same commits" | done | 4233 passed / 0 failed; docs_verify 0 failed, --audit 0 findings, --links 0 dangling |
| R18 | every knob reachable as CONFIGURATION or a registered versioned artifact | done | S1/S2/S8/S9/S17; a channel toggle and a floor change are pure configuration, checked |
| R19 | "an ARCHITECTURE TEST that goes RED when a consumer bypasses the interface" | done | S17; `proof/s17_bypass.txt` — a scheduler reaching past `wander.decide` turns it RED |
| R20 | "VERIFY the decision-to-dispatch connection ... say which is true now" | done | SPEC.md §S0 with M4–M6: **W7 is true now**, E43 reconciled not contradicted |
| R21 | "wiring it IS in scope for H2" | done | S19/S20; regression written first and run RED, reproducing W5's table |
| R22 | the design consequence, stated | done | SPEC.md §S21 |
| R23 | "the road exists in every launch path, not merely that the flags default true" | done | S22; both launch shapes, plus the controller constructing and the code road returning a verdict |
| R24 | "This doesn't demote prose as legitimate criticism" | done | S23; prose differential + kind-blindness check |

No requirement is `not-done`. R4 is delivered for two channels of three; the
third is PARKED with its reason and a ready-to-send prompt, and A3 records why
improvising it would have been the wrong call.

## Assumptions the operator may override

- **A1** — "coding" is the CODE-TESTING/EXECUTION channel, the operator's own
  2026-08-14 name for it, not model-authored Python inside simulation.
  `DEEPREASON_SIMULATION_RUNNER=contained` is untouched.
- **A2** — the default research allowlist is `("arxiv.org", "en.wikipedia.org")`.
  Research cannot be enabled with an empty list (its validator refuses it), so
  a default-ON channel required *some* default. Changing it costs one line and
  one requalification.
- **A3** — code-testing ships declared-ON with no off-switch. Its live entry
  points are commitment compilers whose ids are content-addressed digests over
  the compiled shape, so gating there changes what a record CONTAINS. Parked.
- **A4** — the floor defaults to 0.5, calibrated from ONE run.
- **A5** — "deprioritized" is candidacy gating for the cycle, not rank demotion.
- **A6** — the seed lineage is `SpawnTrigger.SEED`, not the family closure.
  `problem_family` would have swallowed `audit:ritual` and the floor would never
  have bound on the record that motivated it.
- **A7** — all four phantoms are EMITTED, none struck.

One naming decision was forced rather than chosen: `SEED_LINEAGE_BUDGET_FLOOR`
and `LINEAGE_ALLOCATION_POLICY` became `SEED_PROBLEM_BUDGET_FLOOR` and
`ATTENTION_ALLOCATION_POLICY`, because every `Config` field is echoed by name
inside `run_manifest.py` and `DR-SEAM-manifest-x-schools` holds with a check
that `stance`/`lineage`/`crossover`/`reseed` never appear there. `wander.py`
keeps the operator's vocabulary throughout.

## Two results that were not asked for

1. **The wander cap closes a recorded starvation defect.**
   `tests/test_rotation.py::test_legacy_starvation_reproduced` now needs
   `open-lineage.v1` to reproduce its defect, because the shipped cap rescues
   that shape — with no rotation machinery involved (`DISC_ATTEMPTS_MAX=None`,
   `DISC_COOLDOWN=0`, legacy round-robin). A new test pins the rescue. The
   starvation that module was written for is a self-spawned lineage crowding
   out the operator's seeded problem, which is W6's finding at small scale.
2. **The public surface did not move.** Both wheel smokes pass unchanged
   despite two new modules and three new settings — the right outcome for a
   change that adds configuration rather than surface.

## Budget

**1870 insertions against a 1602 plan — EXCEEDED, recorded, ceiling raised to
1900.** SPEC.md Budget amendment 1 carries the per-file itemization. The
overrun is docstrings in three test files and one map document; every line
traces to an R number. Scaling that down is the operator's call, which is why
the number is here rather than absorbed.

## Map delta

created: `docs/map/INV-evidence-channels.md` (197 lines, 9 checks).
changed: `INV-signal-contract.md`, `INV-frozen-surfaces.md`,
`CON-scheduler-ranking.md`, `SEAM-llm-x-scheduler.md`,
`REC-revise-allocation-policy.md`, `SUB-capabilities.md`, `INDEX.md`.
new checks: **25** (1105 → 1130 across the map).
`Verified-at:` advanced on `SUB-scheduler.md`, `SUB-llm.md`, `SUB-manifest.md`
— their owned files moved and their checks were re-run green in the full pass.
left stale: 36 documents `--stale` still lists, all pre-existing and none from
this tranche's commits.

## Errata

**E54** — `DR-SEAM-llm-x-scheduler` documented the allocation seam as a
two-party agreement and omitted the party that CONSUMES it; a seam document
listing only who can REFUSE whom misses this failure class every time.

**E55** — `DR-CON-scheduler-ranking`'s "Must never do" named disk and labels and
omitted the LOG; an implementer who obeyed it exactly still broke a read-only
replay harness.

## Parked (not done, not promised)

- **P1** — the code-testing channel has no off-switch. Blast radius measured:
  33 assertions across eleven files.
- **P2** — the wire fix has no live instance yet (proven offline, never
  witnessed).
- **P3** — the wander cap has no live instance either. Shares a ladder with P2.
- **P4** — ~75 registry names are still declared and silent, and eight tags are
  emitted 18 151 times without being declared at all.

Each carries a ready-to-send prompt in PARKED.md.

**recommended next: P2+P3 as ONE evidence-generation tranche.** One live ladder
run answers both — a run long enough for the controller to settle a seat is a
run long enough to spawn a lineage — and both halves of this tranche are
currently proven but unwitnessed, which is the exact gap the operator's own
"tokens are cheap, you are not" law says to close with a run rather than with
more machinery.

## Residue

Stated plainly: no live run has witnessed either half; code-testing's OFF state
is undelivered; the allowlist and the floor are assumptions calibrated from one
measurement each; and most of the signal registry is still silent. Accepted does
not mean true. VALIDATION.md carries the full list.
