# Spec for: Rung O1 of the grounded-overlay program — offline retrodiction
Traces: every item cites R/C numbers. Untraceable items are bugs.

## Map preflight (CLAUDE.md's map-preflight rule)

Resolved ids from `docs/map/INDEX.md` before designing:

- `DR-INV-frozen-surfaces` — checked first; this tranche touches none of
  the five surfaces (measure-only, reads only).
- `DR-CON-warrants-and-attacks` — the warrant -> attack edge -> Status
  chain; O1a/O1d operate directly on `att`/`dep`/`label0`/`final_labels`
  from this concept's own files (`adjudication/edges.py`,
  `adjudication/grounded.py`, `adjudication/support.py`).
- `DR-SUB-adjudication` — the two-pass semantics (`build_att`,
  `grounded_extension`, `label0`, `final_labels`, `build_dep`,
  `toposort`) this whole rung reads, never writes.
- `DR-SUB-verification` — `verify_root`/`verify_root_report`, the
  existing read-only root-verification instrument this tranche's own
  scripts sit alongside (same corpus convention as
  `tools/root_sweep.py`).
- `DR-SUB-ontology` — `Artifact`, `Provenance`, `ProvenanceRole`,
  `Warrant`, `Commitment`, `EpistemicState` — the vocabulary O1a-O1d
  all read fields from.
- `DR-SUB-evaluation` — `oracle.py`/`programs.py`, read by O1b for the
  exec-oracle commitment spec format (`{entry, tests}`) and the
  `evaluate`/`run` execution primitives it reuses for the bounded
  dynamic-fuzz half of the probe.
- No `DR-SEAM-*` document names a not-yet-existing overlay concept;
  this tranche creates no new map document unless a genuinely new,
  durable CONCEPT earns one at delivery time (R13's own conditional —
  see S16 below). If none is created, no map document changes at all.

`check: grep -q "SUB-adjudication.md" docs/map/INDEX.md && grep -q "CON-warrants-and-attacks.md" docs/map/INDEX.md`

## Items

S1 (R1, R2, R3): setup already performed this session (branch head
verify, editable install, CLAUDE.md + dr-explain-to-operator +
skills/README.md read).
    accept: already satisfied — this session's opening transcript;
    `git log --oneline -1 origin/claude/monitor-session-handover-63ajqv` -> `2b0b108c ...`.

S2 (R4): REQUEST.md written and committed.
    accept: `test -f experiments/2026-08-08-change-grounded-overlay-o1/REQUEST.md`
    -> exit 0 (already committed, commit `70dcfb30`).

S3 (R5): no target files under `src/`, `tests/`, `tools/` — the standing
boundary for the whole tranche.
    accept: `git diff --stat origin/claude/monitor-session-handover-63ajqv...HEAD -- src/ tests/ tools/`
    -> empty output at delivery time.

S4 (R6, R11): every analysis script lives under this tranche's own
directory (`experiments/2026-08-08-change-grounded-overlay-o1/scripts/`),
opens roots ONLY via `Harness(root, read_only=True)` (never
`Harness(root)` without `read_only=True`, which would create/mutate),
never imports any provider/LLM client module, never calls
`deepreason.ops.run_scheduler` or anything that appends to a log.
    accept: `grep -rn "Harness(" experiments/2026-08-08-change-grounded-overlay-o1/scripts/*.py`
    -> every call site shows `read_only=True`;
    `grep -rln "llm\.\|ollama\|adapter\." experiments/2026-08-08-change-grounded-overlay-o1/scripts/*.py`
    -> no hits.

S5 (R7): `scripts/o1a_semantics_diff.py` — for every committed root:
    1. Open `Harness(root, read_only=True)`; read `nodes =
       set(harness.state.artifacts)`, `att = list(harness.state.att)`,
       `dep = list(harness.state.dep)`.
    2. PASTE `len(nodes)`, `len(att)` for the root BEFORE any further
       computation (the guardrail's own ordering requirement).
    3. Compute strongly-connected components of the directed graph
       `(nodes, att)` (Tarjan, iterative — no recursion depth risk).
       Compute `label0 = adjudication.grounded.label0(nodes, att)`
       (the SAME function the harness itself calls — reused, not
       reimplemented). The controversy inventory is every SCC of size
       >1, or size 1 with a self-loop, that contains >=1 artifact whose
       `label0` is `"suspended"`: report the SCC's member ids, size,
       and edge count.
    4. Preferred-extension computation, restricted per the standard
       Dung reduction (G = grounded extension is a subset of every
       complete extension, so preferred extensions only vary on the
       `label0 == "suspended"` nodes, and — proved in this spec's own
       derivation, checked against `label0`'s own logic — no attack
       edge crosses between a `label0`-decided node and a `suspended`
       one): build the reduced framework `(undecided_nodes,
       undecided_att)` where `undecided_nodes = {a : label0[a] ==
       "suspended"}` and `undecided_att = {(x,y) in att : x,y in
       undecided_nodes}`. Split into weakly-connected components.
       PASTE each component's node/edge count BEFORE enumerating.
       For a component with `>16` nodes, stop with a typed
       `TOO_LARGE` result for that component ONLY (report its id set
       and size, continue with the other components — a hang in one
       component must not block the whole root).
    5. For each component `<=16` nodes: brute-force every subset,
       filter to admissible (conflict-free AND every member defended:
       for `n` in `S`, every attacker of `n` is itself attacked by some
       member of `S`), keep the maximal ones (preferred extensions of
       that component). Report their count and, if 1-8 of them, their
       member sets; if more than 8, report the count and the first 8
       plus "N more, not enumerated" (a defensive cap so the report
       itself cannot explode, independent of the compute-side TOO_LARGE
       gate).
    6. "Skeptically accepted under preferred but blocked from
       grounded" = nodes in the intersection of every component's
       preferred extensions (unioned across components; the empty
       intersection contributes nothing) that are NOT in the grounded
       extension G — by construction these are exactly the `suspended`
       nodes that every preferred extension of their own component
       accepts. Report the artifact ids, per root.
    accept: script exists; run once per root; per-root output line has
    `nodes=`, `att_edges=`, SCC controversy count, preferred-component
    count (with any TOO_LARGE flagged), and the skeptical-accepted-not-
    grounded id list (possibly empty). Every number traces to the
    pasted per-root command in the report.

S6 (R7 continuation, C3): the TOO-LARGE guardrail itself.
    accept: a synthetic unit check (run directly, not via `pytest`,
    since `tests/` stays untouched) constructs an odd cycle of 20 nodes
    and asserts the script's own component-sizing function returns
    TOO_LARGE for it and does not hang (wall-clock bounded, pasted).

S7 (R8): `scripts/o1b_joint_execution_probe.py` — for every committed
root:
    1. `formally_backed(harness, aid)` (imported directly from
       `deepreason.rules.warrants`, called read-only — it only reads
       `harness.state`/`harness.commitments`, never writes) restricted
       to `aid` with `harness.state.status.get(aid) ==
       Status.ACCEPTED`: the accepted, formally-backed population.
    2. "Machine-comparable input gates" (Q4's resolution, A4 below):
       restricted to PAIRS of accepted-formally-backed artifacts that
       (a) answer the SAME problem (`(aid, pid) in harness.state.addr`
       for a shared `pid`) AND (b) each carry >=1 commitment whose
       `kappa.eval == f"program:{oracle.EXEC_PROGRAM}"` (i.e.
       `"program:exec_oracle"` specifically — NOT
       `programs.program_class`, which only classifies "execution" vs
       "structural" process shape and does not identify exec_oracle by
       name) with the IDENTICAL `entry` string in its frozen `{entry,
       tests}` spec (`oracle._load_spec`). Every
       accepted-formally-backed pair that does NOT meet both (a) and
       (b) is EXCLUDED and counted, never silently dropped, per C3's
       "reports the excluded remainder honestly rather than guessing."
    3. Exact probe (no execution): for every comparable pair's two test
       tables, compare `in` (canonicalized via
       `deepreason.canonical.canonical_json`) across both; any shared
       `in` with differing `out` is a proven `CONTRADICTION` — report
       the artifact ids, commitment ids, and the conflicting input/pair
       of outputs.
    4. Bounded dynamic probe: for comparable pairs with NO literal
       `CONTRADICTION` found, sample up to `min(FUZZ_N, 32)` candidate
       inputs by mutating the literal inputs already present in EITHER
       table (bounded budget, deterministic — no `random`; a fixed seed
       sequence derived from sorted input values, since this tranche's
       own scripts must be exactly re-runnable). For each candidate,
       execute BOTH artifacts' own `content_text(artifact, blobs)` as
       source via `oracle.run(source, entry, tests=[{"in": candidate,
       "out": SENTINEL}])` where `SENTINEL` is a value that can never
       legitimately be returned (a unique string), so the call always
       reports `FAIL` and its own detail dict's `"got"` field is read
       back as the actual computed value (reusing `oracle.run` exactly
       as it exists — no new execution code). If both sides return a
       comparable `"got"` and they DIFFER for every sampled candidate
       (budget exhausted with zero agreement found), report the pair
       `LOOKS_UNSATISFIABLE` with the sampled inputs and both `"got"`
       values pasted. If any candidate produces a sandbox error,
       timeout, or `_short()`-truncated (unreliable-compare) value on
       either side for every sample, report `INCONCLUSIVE` rather than
       guessing either way — never claim more than the probe shows
       (C3).
    accept: script exists; run once per root; report has, per root: the
    accepted-formally-backed count, the comparable-pair count, the
    excluded-pair count (with a one-line reason each), and per
    comparable pair one of `CONTRADICTION` / `SATISFIABLE` (an
    agreeing candidate found) / `LOOKS_UNSATISFIABLE` / `INCONCLUSIVE`
    with its evidence.

S8 (R9): `scripts/o1c_floating_foundations.py` — for every committed
root:
    1. `ground(a) := harness.state.artifacts[a].provenance.role in
       {ProvenanceRole.SEED, ProvenanceRole.IMPORT,
       ProvenanceRole.USER}` (A5 below — the three roles the codebase
       actually uses for seed-question, admitted/attached-evidence, and
       user-authored content; confirmed by grep against every
       `Provenance(role=...)` call site outside `tests/`).
    2. Restrict to `accepted = {a : harness.state.status.get(a) ==
       Status.ACCEPTED}`. Build the dependence graph restricted to
       `accepted` nodes: `dep_a = {(x,y) in harness.state.dep : x,y in
       accepted}`.
    3. `dep` is a DAG by construction (`toposort`/
       `DependenceCycleError` at write time — `DR-SUB-adjudication`'s
       own "Where to change what" row) — no committed root can contain
       a literal cycle. "Self-supporting cluster" (per the preplan's
       own naming, read against this constraint) is therefore a WEAKLY
       connected component of `dep_a` whose transitive closure (via
       `dep_a`, dependents -> dependencies) reaches NO ground artifact
       at all — including the vacuous case of an isolated accepted
       artifact with zero outgoing `dep_a` edges that is not itself
       ground (trivially "supported" by `final_labels`'s own vacuous
       `all([])==True`, per `adjudication/support.py`, without ever
       resting on evidence or admission).
    4. Compute weakly-connected components of `dep_a`; for each, walk
       every member's transitive dependence closure; flag the component
       FLOATING if no member and no transitive dependency is `ground`.
       Report each floating component's members, size, and whether it
       is a single isolated (zero-dep) artifact or a genuine multi-node
       chain/tree.
    accept: script exists; run once per root; report has, per root, the
    accepted-artifact count, `dep_a` edge count, floating-component
    count and member-id lists (possibly zero, a legitimate negative
    result).

S9 (R10): `scripts/o1d_warrant_sensitivity.py` — for every committed
root:
    1. `accepted = {a : harness.state.status.get(a) ==
       Status.ACCEPTED}`. Read `harness.warrants` (every registered
       warrant) and `harness.state.carries` (the carriage relation).
    2. For each warrant `w` in `harness.warrants`: rebuild `att' =
       build_att(harness.state.artifacts, {wid: wv for wid, wv in
       harness.warrants.items() if wid != w}, harness.commitments,
       carries=[c for c in harness.state.carries if c[1] != w])` (the
       graph with exactly warrant `w`'s carriage removed — both the
       legacy `Artifact.warrants` union and the explicit `carries`
       relation, matching `build_att`'s own two input channels).
       Recompute `label0' = label0(nodes, att')`,
       `final' = final_labels(label0', build_dep(harness.state.artifacts))`.
       For every artifact `a` in `accepted`, check whether `final'[a] !=
       Status.ACCEPTED`; if so, `w` is a single-warrant flip for `a`.
    3. Report, per root: for each accepted artifact, the count and id
       list of single-warrant flips (0, 1, or more); the distribution
       (histogram of flip-counts across all accepted artifacts, e.g.
       "N artifacts with 0 flips, M with exactly 1, K with 2+").
       "Minimum set" beyond size 1 is out of scope this rung (A6/Q6a).
    accept: script exists; run once per root; report has, per root, the
    accepted-artifact count, total-warrant count, and the flip-count
    histogram, with at least the artifact ids for every
    exactly-1-flip case (so "how much acceptance rests on one edge" is
    spot-checkable per the preplan's own framing).

S10 (R7-R10 shared): a single driver script,
`scripts/run_all_overlays.py`, that enumerates the committed-root
corpus once (A7 below) and calls all four overlay modules per root,
writing one combined machine-readable report (JSON lines, one per
root) plus the human-readable REPORT.md the deliverable requires.
    accept: `python experiments/2026-08-08-change-grounded-overlay-o1/scripts/run_all_overlays.py`
    exits 0 and writes
    `experiments/2026-08-08-change-grounded-overlay-o1/overlay_results.jsonl`
    with one line per committed root.

S11 (R12): `REPORT.md` in the tranche directory — the measured report:
counts per root per overlay, with the specific artifact/warrant/
commitment ids named so every number is spot-checkable by one pasted
command (reusing `overlay_results.jsonl`'s own rows).
    accept: `test -f experiments/2026-08-08-change-grounded-overlay-o1/REPORT.md`
    -> exit 0; every overlay section has >=1 M-numbered row per overlay
    with a pasted command.

S12 (R12): `RESULTS.md` — honest-ledger segment(s) per CLAUDE.md's own
convention, including the residue the plan names verbatim: "the LLM
consistency patrol is structurally outside offline reach — say so,
don't simulate it" (missing-edge blind spot 1, from the preplan's own
opening section, never attempted here).
    accept: `grep -q "consistency patrol" experiments/2026-08-08-change-grounded-overlay-o1/RESULTS.md`
    -> exit 0; the residue section names every overlay's own structural
    blind spot (O1a: only single-warrant/exact-domain divergence
    proven — a wider preferred-vs-grounded gap could hide behind a
    TOO_LARGE component; O1b: restricted to same-problem exec-oracle
    pairs, every other kind excluded and counted, not probed; O1c:
    "ground" is a fixed three-role definition, not a semantic judgment
    of what SHOULD count as foundational; O1d: single-warrant only, no
    minimal-set-of-size->1 search).

S13 (R13): zero code diff tripwire, full gate at the boundary,
docs_verify if a map document changes.
    accept: `git diff --stat origin/claude/monitor-session-handover-63ajqv...HEAD -- src/ tests/ tools/`
    -> empty (pasted as the tripwire); `python -m pytest tests/ -q -n 4`
    run once at the boundary -> expect "0 failed" per the task's own
    stated new baseline (P1/P3 fixed, confirmed by A3 below) — if
    anything is red, STOP and report rather than reconciling it away;
    `python tools/docs_verify.py` run only if `docs/map/` gained any
    content (S16) — otherwise this line is n/a, stated as such rather
    than run needlessly.

S14 (R14): PARKED.md — any defect noticed during S5-S13 recorded with a
ready-to-send prompt, same shape as prior tranches' own PARKED.md; "no
defects found this tranche" recorded in RESULTS.md instead if none.
    accept: either PARKED.md exists with >=1 entry, or RESULTS.md states
    "no defects found this tranche" (mutually exclusive, one must hold).

S15 (R15): commit and push at every phase boundary (REQUEST.md done;
SPEC.md next; CHECKLIST.md; each executed script/overlay; REPORT.md;
RESULTS.md; VALIDATION.md; DELIVERY.md).
    accept: `git log --oneline origin/claude/grounded-overlay-rung-o1-4hkuoo..HEAD`
    at delivery time -> empty (nothing unpushed).

S16 (R12's conditional, R13): a new map document, `docs/map/CON-
grounded-overlays.md`, is created ONLY IF O1a-O1d's own findings
surface a durable, reusable CONCEPT worth navigating to later (e.g. a
real non-empty controversy inventory, a real contradiction, a real
floating-foundation cluster) — per `SCHEMA.md`'s own triage rule, a
document describing a null result with no reusable vocabulary is not
owed. The decision is made at CHECKLIST execution time from the actual
measured findings, not predicted here.
    accept: if created, `python tools/docs_verify.py`,
    `python tools/docs_verify.py --audit`, and
    `python tools/docs_verify.py --links` all pass, and it is added to
    `docs/map/INDEX.md`'s concept table in the SAME commit; if not
    created, RESULTS.md states why the findings did not warrant one.

S17 (R16): deliver through `dr-validate-change` then `dr-deliver-change`,
then stop.
    accept: VALIDATION.md and DELIVERY.md both exist and are committed.

## Assumptions (operator may override)

A1 (Q1): "attack-graph SCC containing an undecided artifact" = SCCs of
the directed `att` graph (Tarjan) filtered to those containing >=1
`label0 == "suspended"` node — the controversy inventory (S5 step 3).

A2 (Q2): no preferred-extension computation exists in `src/`; this
tranche implements one, offline, in `scripts/` only, using the standard
Dung reduction (grounded extension is a subset of every complete
extension, so only the `suspended` sub-framework needs brute-force
enumeration) with a 16-node-per-component brute-force cap and a typed
TOO_LARGE beyond it (S5 step 4-5, S6's own synthetic-cap check).

A3 (Q7): "P1/P3 is fixed" — confirmed against the current tree before
treating a green gate as expected:
`experiments/2026-08-08-fix-module-fingerprints-double-stamp/RESULTS.md`
("full gate 3400 passed, 0 failed... the first fully green full-gate
run in this program's tranche history") and
`experiments/2026-08-08-fix-l1-continue-resumable-crash/RESULTS.md`
("Full gate: 3385 passed, 1 failed net of the named pre-existing
P1/P3 — 0 failed net of it") both land on this branch's own history
before `2b0b108c`. The task's stated new baseline is accepted as
correct pending this tranche's own boundary gate run (S13), which is
the actual proof, not this citation.

A4 (Q4): "machine-comparable input gates" (O1b) = same-problem accepted-
formally-backed pairs each carrying an exec-oracle-class commitment
with an identical `entry` name in its frozen `{entry, tests}` spec —
the only place in the ontology today where an admissible input domain
is machine-legible as a concrete, comparable set (S7 step 2). Every
other formally-backed pair (predicate-only, property-oracle-only,
dataset-oracle-only, or cross-class) is counted as EXCLUDED with its
reason, never guessed into a verdict — directly following C3's own
instruction.

A5 (Q5): "ground" (O1c) = `Provenance.role` in `{SEED, IMPORT, USER}` —
confirmed by grepping every non-test `Provenance(role=...)`
construction site in `src/deepreason/`: `seed` marks the run's own
seed question and standards; `import` marks admitted/attached evidence
and workload/skeleton ingestion; `user` marks user-authored and
holdout/appellate content. `CONJECTURER`, `CRITIC`, `VARIATOR`,
`SYNTHESIZER`, `CONTROLLER`, `EXPERIMENTER` are all internally-
generated roles, never ground by this definition (S8 step 1).

A6 (Q6a): "single-warrant sensitivity first" (O1d) is read as this
rung's own full scope — multi-warrant minimal sets (size >1) are
explicitly deferred, not attempted, and RESULTS.md's residue section
names this deferral rather than silently narrowing scope (S9 step 3,
S12).

A7 (Q8): the corpus is every `experiments/**/log.jsonl` root (the same
corpus `tools/root_sweep.py` already walks) — checked: `find . -name
log.jsonl -not -path "./experiments/*"` finds nothing outside
`experiments/`, so no `runs/`-rooted corpus exists in this tree today
(S10).

## Questions for operator (STOP if non-empty)

(empty — every open question resolved to a smallest-reasonable-reading
assumption above, each grounded in an actual grep/read of the current
tree rather than a guess; none differ materially enough in files/
effort/behavior to warrant a stop, per `dr-ask-the-right-question`'s
dominance test — the tree itself, the preplan's own guardrail text, and
CLAUDE.md's Operator design laws answer each one.)

## Out of scope (explicit)

- Rung O2 (design-and-stop for whichever overlay(s) show non-trivial
  catches) — not started; O1 is measurement only.
- Any live counterpart (candidate-attack minting, advisory typed
  reports entering the ordinary criticism loop) — O2's job, per the
  preplan's own rung boundary.
- The LLM consistency patrol (missing-edge blind spot 1) — structurally
  outside offline reach per the preplan's own text; named in RESULTS.md
  residue, never simulated.
- Multi-warrant (size >1) minimal sets for O1d — A6, deferred.
- Fixing any defect this tranche's own scripts surface in `src/` — PARKED
  per R14, never fixed; this tranche's own R5 forbids `src/` edits
  regardless.
- Promoting any script to `tools/` — the preplan's own text: "promotion
  to `tools/` only if the numbers earn it," a decision for O2/delivery
  time, not designed here in advance.

## Frozen-surface contact forecast

none expected — checked against `docs/map/INV-frozen-surfaces.md`'s
five surfaces (`capabilities/state.py` digests, `harness.py` event
application, replay-validation record formats in `invariants.py`/
`verification/`, `run_manifest.py` schemas+validators,
`qualification.py`'s subject digest) and the frozen-adjacent
`route_fingerprint`. This tranche's scripts call `Harness(root,
read_only=True)` (a read path already exercised by
`tools/root_sweep.py` and every map-document `check:` line that opens
a root) and pure functions from `adjudication/`, `rules/warrants.py`,
`oracle.py`/`programs.py` — none of these are written to. R5's own
boundary (`src/`, `tests/`, `tools/` byte-untouched) makes write
contact structurally impossible for the whole tranche.

`check: git diff --stat origin/claude/monitor-session-handover-63ajqv...HEAD -- src/deepreason/capabilities/state.py src/deepreason/harness.py src/deepreason/invariants.py src/deepreason/run_manifest.py src/deepreason/qualification.py` -> empty at delivery time.

## Blast-radius census

`grep -rn "GROUNDED_OVERLAY\|grounded-overlay-rung-o1\|grounded_overlay" tests/ docs/map/`
-> no hits (verified 2026-08-08). Classification: MUST NOT MOVE —
nothing in `tests/` or `docs/map/` currently asserts on this tranche's
own names, so nothing can be broken by adding them. If S16 creates
`docs/map/CON-grounded-overlays.md`, `docs_verify --links` begins
checking its own internal references once it exists — intended new
coverage, not drift.

No symbol under `src/`, `tests/`, or `tools/` is targeted for change by
this spec (measure-only, R5), so no further blast-radius rows apply.

## Budget

Estimate, itemized:
- REQUEST.md: ~330 lines (already committed, `70dcfb30`).
- SPEC.md: ~430 lines (this document).
- CHECKLIST.md: ~200 lines.
- 4 overlay scripts + 1 driver + shared helpers: ~150-300 lines each,
  5 files ~ 1100 lines.
- overlay_results.jsonl: generated data, not hand-authored, excluded
  from the line budget (machine output).
- REPORT.md: ~400-700 lines (per-root, per-overlay M-numbered rows with
  pasted commands, D1's own template shape).
- RESULTS.md: ~150-250 lines.
- PARKED.md (if any defect found): ~50-150 lines.
- VALIDATION.md + DELIVERY.md: ~350-500 lines combined (D1's own
  template shape).

`python3 -c "print(330+430+200+1100+550+200+100+425)"` -> 3335

~3335 lines across the whole tranche, ~10-16 commits (one per phase
boundary plus incremental per-overlay commits during execution, D1's
own cadence). Frozen surfaces touched: none. This is a MEASURE ONLY
tranche outside `src/`/`tests/`/`tools/`, so `tools/diff_budget.py`'s
ceiling gate (aimed at `src/` change budgets) is not the controlling
instrument here — the controlling constraint is R5's zero-diff
tripwire (S13), not a line ceiling. Per D1's own precedent (its budget
note: "revised... actual tranche size reached ~1921 lines... driven
entirely by pasted command+output evidence per claim, not scope
creep"), this estimate may move once REPORT.md's real evidence volume
is known; if it moves >2x, that will be raised as a STOP the same way
D1 raised its own, not absorbed silently.

Rubric: 6/6 yes
- every R has a spec item with a machine-decidable accept: yes (S1-S17
  cover R1-R16; R7-R10 given concrete algorithms rather than restated
  prose).
- blast-radius census pasted (or pasted-empty) and every hit
  classified: yes (no hits, classified).
- frozen-surface contact forecast recorded: yes (none expected, with a
  check).
- every mechanism the request names traced to code it actually
  reaches: yes (`Harness(read_only=True)` confirmed as the pattern
  `root_sweep.py` and every map `check:` line already use;
  `formally_backed`/`execution_backed` confirmed pure-read;
  `build_att`/`label0`/`final_labels`/`toposort` signatures confirmed
  against `adjudication/*.py` directly; `oracle.run`'s `"got"` detail
  field confirmed present in its own FAIL-path return, letting O1b
  reuse it without new execution code).
- DESIGN-AND-STOP sections: n/a — this is MEASURE ONLY, not
  DESIGN-AND-STOP; the Measurements/Options template sections are not
  required (same reasoning D1's own SPEC.md recorded for its own
  MEASURE ONLY shape).
- nothing in the spec untraceable to an R/C number: yes (re-read pass
  performed; every S-item's parenthetical cites R/C numbers).
