# RESULTS.md — grounded-extension expansion, live run (third launch attempt)

## 2026-08-13 — full ladder run: qualify passed, reason completed, verify_root NOT clean

### What the record shows

**Setup.** `build_manifest.py` compiled deterministically (verified against
a scratch root before any provider call — identical
`manifest_sha256`/`run_input_digest`/`evidence_dossier_digest` on a repeat
run). Zero compile notices — the all-configs-allowed law's disclosure
mechanism had nothing to report against this config.

**Qualify.** `deepreason doctor --production-contracts` against the
compiled manifest: **8/8 route/contract pairs qualified**, 160/160 cases
valid on the first pass, 0 repairs, 0 scope violations, 0 alias failures
(`qualify.json`). Real Ollama Cloud calls at concurrency 2, ~4m17s
wall-clock.

**Reason.** `deepreason run --budget cycles=24 --token-budget 1000000`
completed with **rc=0** — no crash, no typed early stop. Real Ollama
Cloud calls throughout, concurrency 2:

- 485 LLM calls, 981,354 of 1,000,000 tokens spent (622,107 prompt /
  359,247 completion) — the meter's accounting delta was zero (no
  metered tokens missing from the log).
- All 4 schools genuinely route-bound and exercised roughly evenly:
  school-0 41 calls, school-1 32, school-2 31, school-3 37 — confirms
  `route_bound_school_execution_policy`'s topology actually dispatched,
  not just compiled.
- 162 of the 485 calls were `judge` calls — the two-member cross-family
  ensemble (qwen3.5:397b, mistral-large-3:675b) was heavily exercised,
  consistent with `ENGAGED_CRITICISM_AUTHORITY=defended_trial` actually
  routing criticism through real defended trials rather than sitting
  idle.
- 231 total artifacts: 219 accepted, 12 refuted. 191 final survivors.
- Cycles 18–23 show `budget_denied` notes as the token meter tightened
  (some late-cycle candidate reservations were declined), and cycle 23
  carries a `lineage_stagnation` flag with a `stagnation-recruit`
  response — both are typed, graceful scheduler behavior, not failures.
  The run reached its full requested cycle count.

**Content.** The generated theory (rooted at frontier survivor
`013723d2dbc5`, one of 191) is substantively on-topic for the seed
question. Representative accepted proposals, verbatim from the record:

- *RESIDUE label*: "a fourth derived label, RESIDUE, recording the
  standing reason a node is suspended... computed as a pure annotation
  over the final grounded labels and the graph — not a second fixpoint.
  Determinism and polynomial cost are untouched because the annotation
  is a function of the already-unique labeling."
- *Standing-residue BFS*: "mark an undecided node as standing if it has
  no path of length <= k to an accepted defender, computed by a bounded
  BFS from the accepted set (O(V+E) for fixed k)... does not enter the
  fixpoint, so determinism and polynomial cost hold."
- *DefenseWitness artifacts*: "materialize a DefenseWitness artifact for
  each accepted node x: one greedy polynomial set of accepted defenders
  that together attack all attackers of x... a deterministic post-pass
  over final labels and attack graph."
- *Typed attack edges*: "make attack edges typed: each edge materialized
  from a warrant carriage carries a warrant-type tag (undercut vs.
  rebut vs. validity-closure)... the resulting label assignment [stays
  a pure function]."
- *Warrant-chain provenance*: "extend [carriage] with a provenance
  ledger recording, per attack edge, the chain of warrants and closures
  that produced it. Acceptance labels stay a pure function of the
  graph, so the fixpoint is untouched."

Every quoted proposal explicitly argues its own preservation of
determinism and/or polynomial cost — the exact guarantees the seed
question named. This is model prose, not evidence of correctness (per
CLAUDE.md, model prose is never evidence) — but it is evidence that the
question text alone carried enough of the spec's constraint language to
keep the conjecturer on-topic, independent of whatever the dossier did
or did not contribute (see finding below).

### Finding — `verify_root` returned 6 violations, not 0

All 6 are the same check family, one per bound dossier source:

    {"check": "attached-evidence", "detail": "bound source src-... has no unique source record"}

**Diagnosis (code read, not guessed):** `attach_bound_evidence`
(`src/deepreason/evidence/render.py:89`) is the function that turns a
bound dossier's sources into the harness-log artifacts (`schema:
attached-source-record.v1`, provenance role `import`) that
`verify_root`'s attached-evidence check requires to exist, arriving
before the run's first LLM call. It is called from exactly two places
in the whole tree: `application/text_runs.py` (the friendly managed-run
`TEXT_RUN_SERVICE.start()` path) and `amendment/apply.py` (the `amend`
flow). **It is never called by `ops.run_scheduler` or `cli/main.py
_cmd_run`** — the low-level `deepreason run --run-manifest` entry point
this ladder used for the reason phase because the friendly `reason`
command cannot express this run's judge ensemble and school-routed
criticism (`PREREG.md`, "Launch mechanics").

**What this means, plainly:** the six admitted background documents
(`STATE_OF_THE_THEORY.md`, `harness-spec-v1.3.md` §4,
`GROUNDED_OVERLAY_PREPLAN.md`, `PATROL_DETERMINISM_REPORT.md`,
`CON-warrants-and-attacks.md`, `SUB-adjudication.md`) were correctly
bound into the run's frozen identity — they are part of what qualification
and the compiled manifest reference, and `build_manifest.py`'s own
blob-staging step (verified before launch) put their exact bytes on
disk under the root. But they were never turned into evidence the
running models could actually see or cite. The scheduler ran a real,
mechanically sound 24-cycle Popperian process — the violation is scoped
exactly to the attached-evidence check family and nothing else failed —
but this run should be read as if it had answered the seed question
from the question text and the models' own training knowledge alone,
**not** as a run informed by the six documents its own design intended
to hand them.

**Root cause is this tranche's ladder design, not DeepReason production
code.** No `src/` file changed in this tranche; nothing here touches a
frozen surface. This is recorded as a gap in `build_manifest.py`/
`grounded_run.sh`'s own choice to drive the reason phase through the bare
CLI `run` command instead of also calling `attach_bound_evidence`
explicitly between problem registration and scheduler dispatch. Parked
as a ready-to-send follow-up in `PARKED.md` (P2) rather than fixed here —
the root is complete and committed, and CLAUDE.md's append-only rule
means it is not this tranche's place to edit it even if the fix were
trivial.

### Residue — what remains unproven

- This root is **not** a validated "attached-evidence" run in the
  strict replay sense: 6 of `verify_root`'s checks fail. Every other
  dimension checked (replay determinism, school routing, defended-trial
  activity, judge ensemble diversity, qualification) passed clean.
- The generated proposals are informal (prose, not formalized specs or
  executable programs) and were never criticized against the actual
  dossier content — only against each other and the schools' internal
  criticism/defended-trial machinery. "Accepted" here means "survived
  this run's criticism," not "verified correct" — per CLAUDE.md,
  accepted does not mean true.
- Whether any of the five quoted proposals actually preserves
  determinism/polynomial-cost/reinstatement/root-validity as claimed is
  not established by this run — that would require a formal follow-up
  (e.g. the `dr-change-orchestrator` family, spec-checking each proposal
  against `docs/harness-spec-v1.3.md` §4 directly), which is out of
  scope for a live research run.

### Compile notices

Zero, matching the pre-registered expectation in `PREREG.md`.
