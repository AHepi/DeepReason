# Results — Rung O1 of the grounded-overlay program (offline retrodiction)

Honest-ledger segments. "Accepted does not mean true." Model prose is
never evidence; `REPORT.md`'s pasted commands and
`overlay_results.jsonl` are.

## 2026-08-08 — the four overlays, run over every committed root

**What was measured.** Four read-only overlays over the grounded
extension's attack graph, computed offline against every one of the
48 roots under `experiments/**/log.jsonl` (37 openable at schema v6;
11 pre-v6 roots raise `UnsupportedRunManifestVersionError` on open —
the same baseline `docs/map/INV-frozen-surfaces.md` documents for
`tools/root_sweep.py`'s own corpus, cross-validating this tranche's
enumeration against the existing instrument rather than inventing a
new one):

- **O1a (semantics diff).** Implemented Dung's preferred-extension
  computation offline (it does not exist in `src/` today), restricted
  by the standard reduction to the `label0=="suspended"` sub-framework,
  bounded per weakly-connected component at 16 nodes with a typed
  `TOO_LARGE` stop beyond it. Result: **zero divergence across the
  whole corpus** — 0 controversy SCCs, 0 undecided artifacts, 0
  artifacts skeptically-accepted-under-preferred-but-blocked-from-
  grounded, 0 components ever hit `TOO_LARGE`. Grounded and preferred
  coincide on every committed root. This is a genuine negative result:
  the corpus's total attack-edge volume is small (26 edges across 37
  roots) and every observed edge forms a simple chain, never a cycle —
  the exact structural condition under which grounded and preferred
  provably agree.
- **O1b (joint-execution probe).** Restricted to accepted,
  formally-backed artifact pairs sharing a problem AND both carrying
  an identical-entry `program:exec_oracle` commitment (the only
  ontology field today that makes an input domain machine-legible —
  see Residue below). Result: **265 accepted+formally-backed artifact
  instances found corpus-wide, zero pairs met the comparability gate**
  — 2772 of 3074 excluded pairs failed specifically because they carry
  `predicate:`/`program:property_oracle` commitments instead of
  `program:exec_oracle`. The probe's dynamic-fuzz half (real code
  execution via `oracle.run`'s own reused FAIL-path `"got"` field) was
  therefore never exercised on live data this rung — verified correct
  only by hand-built unit checks (CHECKLIST.md step 6), not by the
  sweep.
- **O1c (floating foundations).** Weakly-connected components of the
  accepted-only dependence graph whose transitive closure never
  reaches a `SEED`/`IMPORT`/`USER` (ground) artifact. Result: **2360
  vacuous isolated singletons (expected, low-signal) and 14 genuine
  multi-node floating chains across 12 roots, sizes up to 28
  artifacts** — accepted artifacts that DO cite each other via
  `dependence` refs but whose whole chain never bottoms out at
  evidence or admission. This is the rung's one positive catch;
  `REPORT.md` M6 names the five largest chains by root and member id
  prefix, spot-checkable against the committed roots directly.
- **O1d (load-bearing warrants).** Recomputed `build_att`/`label0`/
  `final_labels` once per warrant with that warrant's carriage removed
  (both the legacy `Artifact.warrants` union and the explicit
  `state.carries` relation), single-warrant sensitivity only. Result:
  **zero single-warrant flips across all 1921 accepted artifacts and
  26 warrants corpus-wide** — no accepted artifact's status depends on
  any one warrant's presence. Consistent with the corpus's small,
  cycle-free attack graph (M2): no observed attack is the sole thing
  standing between an artifact and a different label.

**What this means for the program.** Of O1a/O1b/O1c/O1d, only O1c
found a real, non-trivial catch on the current committed corpus. This
does NOT mean the other three overlays are worthless — O1a and O1d's
own machinery is independently verified correct (Dung-textbook sanity
checks for O1a, direct reuse of `build_att`/`label0`/`final_labels` for
O1d) and simply found nothing to catch on THIS corpus's actual attack
graphs, which are small and acyclic; a future corpus with richer
mutual-attack structure or a denser warrant graph could surface real
findings from either. O1b's restriction is the narrowest of the four
by design (SPEC.md A4, the preplan's own guardrail: "restricts to
pairs with machine-comparable input gates... reports the excluded
remainder honestly rather than guessing") and its near-total exclusion
rate is itself informative for Rung O2's design: if joint-execution
probing is to catch anything in this program, "machine-comparable
input gates" will need to widen beyond exec-oracle's literal test
tables — the most promising unexplored extension is
`property_oracle_commitment`'s own `generator`/`input_contract`
fields (oracle.py:341-342), which DO declare a shared-domain signal for
property-oracle-class commitments and were out of this rung's own
scope (SPEC.md A4 restricted to exec-oracle only, the sole case
requiring no semantic judgment to compare).

## Residue — what offline analysis structurally cannot see

Per the preplan's own naming: **the LLM consistency patrol is
structurally outside offline reach — say so, don't simulate it.**
Missing-edge blind spot 1 (two accepted artifacts that contradict each
other but no one minted the attack edge) requires a semantic judgment
call — reading two artifacts' content and deciding they conflict — that
no offline script can make without itself being an LLM call, which
R6/C1 forbid this rung from making. This rung never attempted it, and
nothing in O1a-O1d substitutes for it: all four overlays reason only
over the RECORDED graph (`att`, `dep`, `warrants`, `commitments`), never
over artifact CONTENT semantics. A future rung (Rung O2's own
"consumer" naming requirement, or a live counterpart) is the only place
this blind spot can be addressed, and only with real provider calls.

Each overlay's own narrower residue, beyond the shared one above:

- **O1a**: only EXACT divergence (a node in every preferred extension
  but not grounded) was computed and searched; nothing found because
  no root's undecided sub-framework was ever non-empty. A root with a
  genuine cycle would exercise the 16-node `TOO_LARGE` cap for the
  first time in this program's history — the cap's correctness is
  proven only synthetically (`check_o1a_too_large_guardrail.py`), never
  against real data, because no real data has needed it yet.
- **O1b**: restricted to exec-oracle-class commitments only (SPEC.md
  A4); every predicate:/property_oracle:/dataset_oracle:-class pair is
  counted as excluded, never probed — see "What this means for the
  program" above for the concrete widening this points at. The
  dynamic-fuzz execution path exists, is reused correctly from
  `oracle.run`, and is unit-tested, but has never run against a real
  committed artifact pair in this rung.
- **O1c**: "ground" is a fixed three-role definition (`SEED`, `IMPORT`,
  `USER` — SPEC.md A5), not a semantic judgment of what SHOULD count as
  epistemically foundational. An artifact with a `USER`-role provenance
  that is itself unsubstantiated prose would count as "ground" here
  even though nothing mechanically verifies it — this overlay measures
  structural grounding (does a dependence chain reach an admission-type
  artifact), not epistemic grounding (is that artifact actually true).
- **O1d**: single-warrant sensitivity only (SPEC.md A6) — minimal sets
  of size >1 (e.g. two warrants that TOGETHER, but not individually,
  flip an artifact's status) were never searched. Zero single-warrant
  flips found does not mean zero multi-warrant load-bearing sets exist;
  it means this rung did not look for them.

## No new map document

`docs/map/` describes `src/deepreason/` — `docs/map/INDEX.md`'s own
"Coverage, stated honestly" section: "`docs/map` describes
`src/deepreason/`. `tests/` and `experiments/` are navigated by
convention: ... a tranche directory is named `<date>-<fix|change>-
<slug>`." This rung's four overlay scripts live entirely under
`experiments/2026-08-08-change-grounded-overlay-o1/scripts/`, own no
`src/deepreason/` file, and add no new `src/` symbol — every `src/`
function they call (`build_att`, `label0`, `final_labels`,
`formally_backed`, `ProvenanceRole`, `oracle.run`) is already
documented in `DR-CON-warrants-and-attacks` and `DR-SUB-adjudication`.
A `SCHEMA.md`-anatomy `CON-` document requires an `Owns:` header naming
the files it is authoritative for; this rung owns no `src/` file, so
forcing a `CON-grounded-overlays.md` into existence would misfit the
schema (an `Owns:` line pointing at `experiments/`, which the map's own
charter excludes) rather than serve a real reader. The tranche
directory itself — `REQUEST.md` through this `RESULTS.md` — is the
correct, convention-navigated home for this rung's methodology, per
`INDEX.md`'s own words. `docs/map/INDEX.md` is therefore unchanged by
this tranche.

## Not fixed here

**No defects found this tranche.** No defect was found in `src/`,
`tests/`, or `tools/` during this tranche, so no `PARKED.md` is
created (per this program's own convention: an empty `PARKED.md` is
not written when nothing was found). The `_candidate_inputs`/
`_literal_overlap_contradiction` bytes-key bug and the O1b per-root
wall-clock/pair-count budget gap were both caught and fixed WITHIN
this tranche's own scripts (`scripts/`, not `src/`) before being run
over the corpus — normal script-development iteration, not a defect
against the harness.

## Verdict

O1 complete: four overlays built, run over the full committed-root
corpus, and reported with pasted, recomputable evidence per root. Three
of four (O1a, O1b, O1d) return a genuine negative result on this
corpus; O1c returns a genuine positive one (14 multi-node floating
chains). Zero `src/`/`tests/`/`tools/` diff throughout. Rung O2's own
decision — which overlay(s), if any, earn a live counterpart — is
informed directly by these numbers, not guessed ahead of them.
