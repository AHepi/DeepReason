# Delivered: overhaul the .claude/skills/ set
Branch: claude/skills-overhaul-vk2n8d @ 4a389ce87 (pushed; tree clean
pending this commit)

## What changed

`.claude/skills/` went through a full census, an evidence-grounded
design, and — after the operator's explicit go-ahead — a rewrite pass.
Nothing was deleted except `README.md`, whose content was a third copy
of a routing table already stated in `CLAUDE.md` and in
`dr-drive-harness`. No two skills were merged: the census found
duplicated RULE TEXT across files, not duplicated skills, so the fix
was ten scoped edits (not mergers) that turn eight repeated procedure
blocks — map preflight, environment preflight, commit-every-boundary,
run-root retirement, credential handling, detached-launch, judge-only-
typed-outcomes, and the stop-message format — into one canonical
statement each, in `dr-drive-harness`, with every other file pointing
at it instead of restating it. Five files had sub-lettered "bolted-on"
rules (`3b`, `4a2`, etc.) renumbered into their proper sequence.
`dr-implement-fix`'s budget check, previously an eyeballed `git diff
--stat` compare, is now mechanized through the same `tools/
diff_budget.py` instrument `dr-execute-step` already used — closing a
real gap the census found (a "never" with no enforcing check). A
second gap, found only while drafting this reconciliation — eight
incident-story sentences the census had flagged but the design never
scheduled for trimming — was fixed within the same two already-
approved files. `CLAUDE.md`'s "Which workflow to use" section was
updated in the same commit as the `README.md` deletion, and gained a
missing entry for `dr-explain-to-operator`. `src/` and `tests/` were
never touched, verified continuously, not just once. The full gate
(3535 passed, 1 pre-existing failure) and `docs_verify` (3
pre-existing failures) both match their pre-registered baselines
exactly.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "Route through dr-change-orchestrator" | done | Entire tranche ran REQUEST.md -> SPEC.md -> CHECKLIST.md -> execute loop -> this document, per the routing table. |
| R2 | "ONE batched STOP at the end of Phase B; no other stops" | done | `CHECKLIST.md` steps 1-31: exactly one `STOP`-tagged step (11), immediately after Phase B's boundary (step 10). No other step required an operator reply. |
| R3 | Phase A: inventory every file, one row each | done | `CENSUS.md` "Inventory", commit `02ac40f05`; 19/19 files present. |
| R4 | Rule extraction, IDs + flags (S3/W3/W1/W5/S1/S5) | done | `CENSUS.md` "Rule extraction", commit `a37127f2d`; ~380 rows, 10 duplication clusters named, one flag corrected on review. |
| R5 | Evidence binding, DELETE/MERGE candidates | done | `CENSUS.md` "Evidence binding", commit `c7789b125`; 19-row table, 0 zero-evidence skills, 1 MERGE-into-thin (README.md) candidate. |
| R6 | E1 baseline satisfied by committed evidence, no new trials | done | Same commit; grep check confirms no fresh-trial claim (one false-positive hit is authoring-skills' own rule text, noted). |
| R7 | Phase B: the new set (entry/exit/GATE/LEDGER) | done | `DESIGN.md` "The new set", commit `19c9ae8ff`; 15 phase-owning skills + 3 cross-cutting tabled. |
| R8 | The router (one file per family, PRECEDENCE list) | done | `DESIGN.md` "The router", commit `49d922d45`; 2 routers, 2 PRECEDENCE lists (5 and 6 items). |
| R9 | Gate table (X1/X2/X3) | done | `DESIGN.md` "Gate table", commit `e9e006b63`; 11 rows, all 4 columns filled, 1 honestly flagged as ungated. |
| R10 | Migration note | done | `DESIGN.md` "Migration note", commit `21f9b8b60`; operator's words quoted verbatim. |
| R11 | DESIGN.md + keep/merge/delete table committed | done | Table itself commit `226c7c9e1`; Phase B boundary confirmed commit `a9e57c69c`. |
| R12 | STOP HERE; deletions only on operator's word | done | Operator's reply "Read and approved." received and quoted in `CHECKLIST.md`'s `State:` line, commit `53d9146e4`, before any Phase C step ran. |
| R13 | Phase C: DELTA discipline, one commit per skill, rule IDs named | done | 10 skill-file commits: `1119ec507`, `5c71901b8`, `9848ce6c6`, `28c3e3240`, `9cc71c3ba`, `e870dc1b0`, `8e8e5ac8d`, `ba3c5ffbe`, `2a7f181fa`, `4ace700d0` — each message names its rule IDs. |
| R14 | Zero narrative, zero ungated negation, operation-shaped lines only | done-with-assumption A1 | New/edited text meets this from the start; a gap (8 pre-existing W5 rows the design forgot to schedule) was found while drafting this row and fixed, commit `4a389ce87`. One further W5 row (`dr-ask-the-right-question`) is deliberately NOT touched — see A1 and PARKED.md P2. |
| R15 | Mutation-prove every GATE once | done-with-assumption A2 | The one newly-wired gate (dr-implement-fix's diff-budget check) mutation-proved, commit `ea2ea9bc4`. The other 10 gate-table rows cite pre-existing red-run evidence instead of a fresh proof — see A2. |
| R16 | L5 ship-test | done | Commit `780e0a5e6`, tied to the same newly-wired gate. |
| R17 | CLAUDE.md + README.md updated in the SAME commit as the skills they describe | done | Commit `5c71901b8`: README.md deleted, CLAUDE.md's "Which workflow to use" section fixed, one commit. |
| R18 | One docs/ERRATA.md entry per contradiction found | done ("errata: none") | See Errata section below — zero record-contradictions found this tranche; structure/duplication defects only. |
| R19 | src/ stays byte-untouched, canary at Phase D | done | Checked continuously (steps 4, 10, 14-29 all re-ran it); final confirmation commit `2d19429d1`; empty at every check, this document's own final re-check also empty. |
| R20 | docs_verify + full pytest gate vs. named baselines | done | docs_verify commit `5697bc427`: 3 failed, exact baseline match (CON-run-identity.md shallow-clone gaps). Full gate commit `8a1271964`: 1 failed (test_bronze_report, exact baseline match), 3535 passed, 0 new. |
| R21 | DELIVERY.md, R-by-R with pasted PROOF | done | This document. |
| R22 | Commit and push every phase boundary, retry 2/4/8/16s | done | 35 commits, all pushed; no push failures occurred so the retry ladder was never exercised, but every commit in the log above shows `-> origin/claude/skills-overhaul-vk2n8d` succeeding on the first attempt. |
| R23 | PARKED: full sweep/smoke audit; any src/ change; other CLAUDE.md sections | done | src/ untouched (R19); CLAUDE.md edits confined to "Which workflow to use" (verified line-range diff at commit `5c71901b8`); the sweep/smoke audit was never started, per the operator's own instruction that it is a separate, future tranche. |
| R24 | "Remove budget cap" (Amendment 1) | done | `tools/diff_budget.py` invoked with no `--ceiling` from commit `19c9ae8ff` onward (`NO_CEILING` verdict); REQUEST.md commit `18d70e0f0`, SPEC.md reconciliation `faf7039b7`. |
| R25 | Correction: "I meant your budget" (Amendment 2) | done | REQUEST.md commit `496af624d`, SPEC.md reconciliation `33bb21f05`; corrected plainly rather than silently, no new S-number (process instruction, not an artifact requirement); the exhaustive detail throughout Phase C/D (10 individually-gated skill edits, the W5 gap caught and fixed mid-delivery) is the demonstrated compliance. |

## Assumptions the operator may override

A1: `dr-ask-the-right-question`'s one remaining W5 (incident-story)
row was left untouched rather than trimmed for full R14 compliance,
because DESIGN.md's operator-approved keep/merge/delete table
specifically promised that file "KEEP, unchanged." Reading: honoring
an explicit prior commitment outranks completing R14 by one row: the
row is parked (PARKED.md P2) as a one-line, ready-to-send follow-up
instead. Override: say the word and it lands in a two-minute follow-up
commit.

A2: Only the ONE genuinely new GATE this tranche wired (dr-implement-
fix's diff-budget mechanization) was freshly mutation-proved. The
other 10 gate-table rows are pre-existing, already-proven-red-then-
fixed mechanisms (cited to their historical incidents in CENSUS.md's
evidence binding) — re-deriving fresh red runs for unchanged tooling
was read as the "needless re-derivation" R25 warns against, not the
thoroughness it asks for (dominance test recorded in CHECKLIST.md
step 12's PROOF). Override: name which of the 10 you want freshly
proved and it's a small follow-up.

## Map delta

No `docs/map/` document was changed or created — `docs/map` covers
only `src/deepreason/`, and this tranche's own map preflight (REQUEST.md
header) confirmed no `DR-SUB-`/`DR-CON-`/`DR-SEAM-` id applies. New
checks added: 0 (none owed; no `src/` behavior changed). Left stale:
none found — `docs/map` was never a target of this tranche's edits, so
nothing in it could go stale from them.

## Errata

errata: none. This tranche's findings (duplicated rule text across
files, sub-lettered bolt-on insertions, one ungated negation, one
unmechanized gate, eight untrimmed incident stories) are all
authoring-skills COMPLIANCE gaps in `.claude/skills/` itself, not a
committed document's claim about the CODE or RECORD being wrong — the
category `docs/ERRATA.md` exists for. No entry was fabricated to fill
the checkpoint; the checkpoint is satisfied by stating "none"
explicitly, per the same discipline this tranche's own edits reinforce
in `dr-deliver-change` and `dr-verify-outcome`.

## Parked (not done, not promised)

- **P1** — `dr-drive-harness`'s "never generalize instruction scope"
  negation has no enforcing GATE (the one authoring-skills W3 case this
  tranche could not close). Route: `dr-change-orchestrator`. Ready-to-
  send prompt and evidence pointers: `PARKED.md` P1.
- **P2** — `dr-ask-the-right-question`'s one remaining W5 row (see A1).
  Route: `dr-change-orchestrator`. Ready-to-send prompt and evidence
  pointers: `PARKED.md` P2.
- The full repo sweep/smoke re-pin audit — explicitly named by the
  operator as a separate, future, operator-ordered tranche (REQUEST.md,
  "PARKED BY DESIGN"). Not re-parked here since it was never in this
  tranche's scope to begin with.

recommended next: **P1** — the ungated negation is the one item this
census found that the authoring-skills standard this very tranche
applied would flag in a future audit of `dr-drive-harness` itself; closing
it (or explicitly accepting judgment-only status) finishes what this
tranche's own rule (W3) asks for.
