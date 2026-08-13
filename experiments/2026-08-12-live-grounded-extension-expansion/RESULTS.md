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


## 2026-08-13 — the root reaches a typed terminal, and the six documents enter the record

### What the record shows

This root could not be amended, continued, cancelled, or read as a
result. The cause was not the reader: `deepreason run --run-manifest`
called the scheduler and then **printed**, while the managed
`TEXT_RUN_SERVICE` path calls the same scheduler and then writes ten
further records. Terminal authority therefore never left
`current_open_uncommitted`, and every lifecycle operation refused
correctly against a record that had nothing to read:

    AMEND_NOT_AT_TERMINAL      amendment requires a run standing at a valid
                               typed terminal stop (terminal authority is
                               current_open_uncommitted)
    CONTINUE_STOP_REQUIRED
    RUN_RESULT_NOT_READY       current terminalization is not-started

Fixed by `experiments/2026-08-13-change-lifecycle-operation-parity`: both
launch paths now call one shared `terminalize_text_run`, and a new
`deepreason finalize` brings a root stopped before that fix to its
terminal by APPENDING.

**Finalization (rc=0).** The root now stands at
`current_valid_committed`, terminal epoch 0, reasoning horizon 9947,
commitment `sha256:8c414d5b9af96087e6769b5f2aadc43cb624ce53a7087d8f4ddf0c3312cb0d75`,
stop `budget_exhausted` at cycle 24. Its frontier was re-derived read-only
from the replayed record and reproduces this document's own earlier
numbers exactly: **191 survivors, 87 on the Pareto frontier**, head
`013723d2dbc5`.

**Amendment epoch 1 (rc=0, 2m22s).** The six documents this run bound and
never introduced are now in the record: **6 sources admitted, 0
refusals**, 296 evidence blocks (232 paragraph, 56 section, 8 table),
supplemental dossier
`119e6b8691d3136da887c7215c571a211851697d4bb63148cd16395bd28fc45e`, fence
at seq 9949. All six were verified byte-identical to the frozen dossier
before admission. The question is unchanged — this is an evidence-only
amendment.

**Nothing was edited.** Over both operations, from git:

    git diff --numstat .../run/    ->    log.jsonl   20   0

Twenty appended lines, zero deletions. Every other pre-existing byte of
this root is unchanged; everything else the operations produced is a file
that did not exist before.

**`verify_root` now returns `[]` — zero violations.** The six
`attached-evidence` violations this document reported on 2026-08-13 are
gone. The change tranche predicted they would REMAIN, and that prediction
was wrong; it is corrected here rather than quietly dropped. The
mechanism is that `verify_root`'s attached-evidence check is a UNION check
across epochs (`invariants.py:2157-2161`): it asks whether SOME epoch
introduced each bound source, and epoch 1 introduced all six.

### What this does NOT change about the run above

**Epoch 0 was still not an evidence-informed run.** 485 model calls
happened before any of those six documents existed in this record. The
2026-08-13 finding stands verbatim: that epoch should be read as having
answered the seed question from the question text and the models' own
training knowledge alone. A clean `verify_root` measures the record's
internal consistency — that every source the run's identity binds has been
introduced in some epoch — not the epistemic quality of any epoch. A
reader who wants the latter must look at WHICH epoch introduced a source,
which the record still says exactly.

The 191 survivors are unchanged and uncriticized against the documents.
"Accepted does not mean true," and now also: replay-valid does not mean
well-evidenced.

### Residue — what remains unproven

- **The continuation has not run.** `deepreason continue --budget
  cycles=8 --token-budget 500000` requires real model calls, and the
  container rebuild removed this tranche's gitignored `env`
  (`OLLAMA_API_KEY`). The amendment made the six documents CITABLE; it did
  not make them CITED. Whether criticism engages them, and whether any of
  the 191 survivors survives contact with them, is entirely open.
- Whether any of the five proposals quoted in the 2026-08-13 segment
  actually preserves determinism / polynomial cost / reinstatement /
  root-validity is still not established, and this segment adds nothing
  to that question.
- The driver `experiments/2026-08-13-change-lifecycle-operation-parity/
  live_parity.sh` is idempotent from here: `finalize` refuses
  `FINALIZE_ALREADY_TERMINAL`, `amend` refuses
  `AMEND_SOURCE_ALREADY_ADMITTED` (correctly now — the six ARE
  introduced), so restoring the credential and re-running reaches the
  continuation directly.


## 2026-08-13 (later) — the continuation ran, and the six documents were used

### What the record shows

`deepreason continue --budget cycles=8 --token-budget 500000` completed on
this root — the first continuation ever run on a compiled-config
(`--run-manifest`) root, and the operation that refused
`CONTINUE_STOP_REQUIRED` the same morning.

**Terminal (typed).**

    state                   completed
    stop                    cycle 8, event_seq 12989,
                            digest 036a85c590e03e97
    terminal_commitment_ref sha256:9a39933cfaf7a05d0193af1a709c688b69a04858a61513686b582f9d32f45258
    survivors               245        frontier 87
    completion_status       incomplete
    verification            integrity 0, epistemic 0, security 494,
                            completion 355, operational 8
                            integrity_valid: TRUE
    accounting              metered 263240 == logged 263240, delta 0

This is a SECOND terminal commitment, at epoch 1: the continuation opened
its own epoch and closed it. `integrity: 0` with `integrity_valid: true`
means the record is clean — the six historical `attached-evidence`
violations are gone and the continuation introduced none. `delta: 0`
means every token the meter charged is on the log; no silent spend.

**Work done.** 3 023 events past the amendment fence, 181 real model
calls, 263 240 of the 500 000 authorized tokens. By role: judge 104,
defender 38, argumentative_critic 23, conjecturer 8, variator 8. The
heavy judge share is consistent with `ENGAGED_CRITICISM_AUTHORITY=
defended_trial` routing criticism through real defended trials.

**The six documents were used.** Counted from the model raws under
`blobs/`:

    post-amendment model calls        181
    calls naming an admitted source     48   (27%)
      argumentative_critic  23  (ALL of them)
      defender               9
      conjecturer            8
      variator               7
      judge                  1
    handles cited   SRC_001x62  SRC_002x60  SRC_003x29  SRC_005x19
                    SRC_006x14  SRC_007x14  SRC_008x13  SRC_004x13
                    SRC_009x2

Every argumentative-critic call cited a source. A representative
conjecturer output, verbatim: *"Make the greedy acceptance and
DefenseWitness scans canonical by fixing a total order on arguments
(lexicographic over content hash) as part of the semantics, so every
polynomial scan is enumeration-order independent by construction; the
contradiction in SRC_008 dissolves…"* — a model arguing against a
specific admitted document. This is model prose and therefore not
evidence of correctness; it IS evidence that the delivery path works and
that the seats had the documents in front of them, which the 2026-08-13
segment above recorded as false for epoch 0.

### Finding — the citations are prose, not verifiable records

    calls emitting structured evidence_refs   0 of 181

`EvidenceRefClaimV1 {block, quote}` is the channel
`check_candidate_citations` verifies byte-for-byte against the source.
Not one call emitted one, though the dossier parsed to 296 citable
blocks. So the harness has quote-checking machinery and nothing to check,
and every citation above rests on prose. Whether that is a prompt/contract
gap or the models declining an optional field is NOT established by this
run; parked as P4 in
`experiments/2026-08-13-change-lifecycle-operation-parity/PARKED.md` with
a record-first diagnosis rather than guessed at here.

### Residue — what remains unproven

- **No survivor is shown to have been refuted BY a document.** Refuted
  went 12 → 16 across the continuation, and 48 calls cited sources, but
  this segment does not claim any specific refutation was caused by
  admitted evidence. Establishing that needs the warrant chain per
  refutation, not a citation count.
- **The citations are unverified.** Per P4, no structured claim exists to
  check, so "cited SRC_003" means the model wrote that, not that the
  quoted content is in SRC_003.
- Epoch 0 remains what the earlier segment said it was: 485 model calls
  made before any of these documents existed in the record. The
  continuation does not retroactively inform it.
- Whether any of the five proposals quoted in the first 2026-08-13
  segment preserves determinism / polynomial cost / reinstatement /
  root-validity is still not established, and nothing here bears on it.
- `security 494` and `completion 355` findings are unexamined by this
  tranche. They are not new (the same channels read 344 / 305 at
  finalize, before any continuation cycle) and no claim is made about
  them either way.
