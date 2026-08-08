# Delivered: Rung O1 of the grounded-overlay program — offline retrodiction
Branch: claude/grounded-overlay-rung-o1-4hkuoo @ efb29119 (pushed, tree clean)

## What changed

This tranche measured, and changed no code. Four read-only overlay
scripts (`experiments/2026-08-08-change-grounded-overlay-o1/scripts/`)
were built and run over every one of the 48 committed roots under
`experiments/**/log.jsonl` (37 openable at schema v6; 11 pre-v6 roots
raise the same `UnsupportedRunManifestVersionError` `tools/root_sweep.py`
already documents as its own baseline). O1a implements Dung's
preferred-extension semantics offline for the first time in this
program (it does not exist in `src/`) and diffs it against the
existing grounded extension, restricted per component to a 16-node
brute-force cap with a typed TOO_LARGE stop; O1b probes accepted
formally-backed artifact pairs for joint-execution unsatisfiability,
restricted to pairs with a machine-comparable input domain; O1c finds
weakly-connected clusters of accepted artifacts whose dependence graph
never reaches admitted evidence or a seed/user artifact; O1d
recomputes the attack graph once per warrant to find single-warrant
acceptance sensitivity. `REPORT.md` is the measured report (48-row
per-root table plus 7 M-numbered claims, each with a pasted command
and real output); `RESULTS.md` is the honest-ledger segment, including
the residue the preplan itself names (the LLM consistency patrol is
structurally outside offline reach, never simulated). Of the four
overlays, three (O1a, O1b, O1d) found zero divergence/catches on this
corpus — a genuine negative result, not a script defect, independently
verified by Dung-textbook sanity checks and cross-corpus consistency
with `tools/root_sweep.py`'s own known baselines. O1c found the
tranche's one real positive catch: 14 multi-node "floating foundation"
clusters (accepted artifacts citing each other but never reaching real
evidence), up to 28 artifacts, across 12 roots. The full gate ran
green at the boundary: 3400 passed, 0 failed, 7 skipped — the
program's stated new baseline, confirmed directly rather than assumed.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "Setup FIRST... verify the head is 2b0b108c" | done | this session's opening verification |
| R2 | "run the preflight" | done | `pip install -e .` this session's opening |
| R3 | "THEN read CLAUDE.md... dr-explain-to-operator... skills/README.md" | done | this session's opening reads |
| R4 | "Route through dr-change-orchestrator starting with dr-capture-request" | done | REQUEST.md, commit `70dcfb30` |
| R5 | "src/, tests/, tools/ stay byte-untouched" | done | VALIDATION.md S3/S13, empty diffs |
| R6 | "analysis scripts... read committed roots only — no LLM calls..." | done | VALIDATION.md S4 |
| R7 | "O1a grounded-vs-preferred diff plus... SCC controversy inventory" | done | REPORT.md M1/M2 |
| R8 | "O1b joint-execution unsatisfiability probing..." | done | REPORT.md M3/M4 |
| R9 | "O1c floating-foundation clusters on the dependence graph" | done | REPORT.md M5/M6 |
| R10 | "O1d load-bearing-warrant sensitivity distributions" | done | REPORT.md M7 |
| R11 | "Reuse the harness's own read-only readers..." | done | VALIDATION.md S4, every script's imports |
| R12 | "Deliverables: the scripts, a measured report... RESULTS.md" | done | REPORT.md, RESULTS.md |
| R13 | "Accept: zero code diff... full gate... docs_verify green if..." | done | VALIDATION.md S13, Full gate: 0 failed |
| R14 | "Anything broken you notice: PARKED... never fixed" | done | RESULTS.md — no defects found, no PARKED.md needed |
| R15 | "Commit and push at every phase boundary with retry" | done | 16 commits, every push confirmed on origin |
| R16 | "Deliver through dr-validate-change and dr-deliver-change, then stop" | done | VALIDATION.md (PASS), this document |

## Assumptions the operator may override

A1: SCC controversy inventory = SCCs of the attack graph containing at
least one `label0=="suspended"` artifact.
A2: preferred extensions computed offline via the standard Dung
reduction (grounded extension is a subset of every complete extension,
so only the undecided sub-framework needs brute-force search), capped
at 16 nodes per weakly-connected component, typed TOO_LARGE beyond it.
A3: "P1/P3 is fixed" confirmed directly by this tranche's own full-gate
run (0 failed), not merely cited from the two prior fix tranches.
A4: "machine-comparable input gates" (O1b) = same-problem, identical-
entry, `program:exec_oracle`-class commitment pairs only — the one
case comparable without semantic judgment. This excluded the entire
corpus (265 formally-backed artifacts, 0 comparable pairs, 2772 of
3074 excluded pairs failing specifically because they carry
`predicate:`/`program:property_oracle` commitments instead) — a real
finding about this program's own committed data pointing at where a
future rung would need to widen the gate, not a design flaw in this
one.
A5: "ground" (O1c) = `Provenance.role` in `{SEED, IMPORT, USER}`.
A6: single-warrant sensitivity only for O1d; multi-warrant minimal
sets (size >1) deferred, named as residue.
A7: corpus = every `experiments/**/log.jsonl` root (48 total).

## Map delta

None. `docs/map/` is untouched by this tranche — confirmed by an empty
`git diff --stat` against `docs/map/` at validation. RESULTS.md's own
"No new map document" section records why: the map's stated charter
(`docs/map/INDEX.md`'s "Coverage, stated honestly" section) describes
`src/deepreason/` only, and this rung's four overlay scripts own no
`src/` file and add no `src/` symbol — every function they call
(`build_att`, `label0`, `final_labels`, `formally_backed`,
`ProvenanceRole`, `oracle.run`) is already documented in `DR-CON-
warrants-and-attacks` and `DR-SUB-adjudication`. Forcing a `CON-`
document into existence with an `Owns:` header pointing at
`experiments/` would misfit `SCHEMA.md`'s own anatomy rather than serve
a real reader; the tranche directory itself is the map's own stated
home for this kind of work ("`experiments/` is navigated by
convention").

## Parked (not done, not promised)

None. No defect in `src/`, `tests/`, or `tools/` was found during this
tranche — RESULTS.md states this explicitly ("No defects found this
tranche"), and no `PARKED.md` was created, following this program's own
convention of not writing an empty one.

**Recommended next:** Rung O2 is decided by this rung's own numbers,
per the preplan's own text ("Rung O2 — decided by O1's numbers
[DESIGN-AND-STOP]"). O1c is the one overlay with a non-trivial catch
(14 multi-node floating chains) and is the strongest candidate for a
live counterpart; O1a and O1d are structurally sound but found nothing
on this corpus's own small, cycle-free attack graphs, so a live
counterpart for either would need to be justified against a richer
future corpus rather than this one's numbers; O1b's own restriction
excluded the entire corpus, and REPORT.md's "What this means for the
program" section names the concrete widening (property-oracle
`generator`/`input_contract` fields) that would need to be designed
before a live counterpart could catch anything at all. Per the
preplan's own closure rule, if the operator judges O1a/O1b/O1d's
near-zero counts not worth a live build, Rung O2 may instead be the
one-paragraph closure the preplan itself names as a legitimate
outcome — "the graph closure is healthy" — for those three, with O1c
alone carried forward.

This tranche is closed. Rung O2 is a fresh tranche, not a continuation
of this one.
