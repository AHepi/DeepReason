# PARKED — found while preparing the reach-rich run, deliberately not fixed

This tranche is READ-ONLY on `src/` and `tests/` by operator instruction.

---

## P1-reach — `_STRUCTURAL_PROGRAMS` omitting `reasoning-envelope-wf` is what blocks reach in every text run

**STATUS 2026-08-22: FIXED.** Landed by
`experiments/2026-08-22-reach-structural-programs-fix` and confirmed live in
this tranche's epoch-1 root: the reach census records
`reasoning-envelope-wf` once, classified `structural`, blocking nothing. The
prompt below is kept as the record of what was asked for; it is not open work.

This is not a new finding. It is
`experiments/2026-08-21-measure-reach-firing/PARKED.md` **P1**, upgraded:
that tranche measured P1 as *latent* ("the direction of this defect is
PERMISSIVE ... Latent, not yet active"). This tranche's rehearsal shows it
is **load-bearing** — it is the single reason a text run cannot produce a
reach event, and fixing it makes one fire on the first attempt.

**The new evidence** (`rehearsal.json`, committed here):

- **S8a** `E4 criterion-fail` — a prose `conn:` candidate carrying novel
  subject criteria is rejected by `reasoning-envelope-wf` before any
  subject criterion is read.
- **S8b** **HIT**, 1 recorded `reach_set` event — the same candidate, same
  criteria, with `reasoning-envelope-wf` counted structural (as
  `programs.PROGRAMS` already declares it). Coverage 2/3.
- **S8c** `E4` — an on-form but off-SUBJECT candidate still does not hit,
  so the fix grounds reach on subject, not on form.

The fix TIGHTENS the substantive/structural boundary. It lowers no
threshold and widens no vocabulary, so it does not relax the Bronze Age
discipline — it applies it to a gate the discipline already names.

```
Route: deepreason-orchestrator (defect).

One goal: make measures/reach.py::_substantive agree with the structural
class programs.PROGRAMS already declares, so a well-formedness gate can
never ground reach or confer prose immunity.

Why this is now urgent rather than latent: reach is Rung 5's nomination
signal, and this defect is the sole reason no text run can produce one.
  - experiments/2026-08-22-live-reach-rich-run/rehearsal.json, scenarios
    S8a / S8b / S8c: the same prose connection candidate against the same
    seed criteria takes exit E4 as shipped and records a full reach hit
    with the fix applied, while an off-subject control still takes E4.
    rehearsal.py simulates the fix by rebinding _STRUCTURAL_PROGRAMS
    in-process; re-run it after the real fix and S8a must become a HIT
    with no in-process rebind (delete the wf_structural argument and the
    two scenarios must agree).
  - experiments/2026-08-21-measure-reach-firing/CENSUS.md, "The qualifying
    vocabulary": reasoning-envelope-wf appears as a QUALIFYING foreign
    criterion in 793 gate pairs across 46 roots.
  - Re-derive the divergence in one command:
      python -c "from deepreason.programs import programs_by_class; from
      deepreason.measures.reach import _STRUCTURAL_PROGRAMS as S;
      d=set(programs_by_class()['structural']); print(sorted(d-S))"
    prints ['component_wf','generator_wf','integration_wf','manifest_wf',
    'reasoning-envelope-wf'].
  - experiments/2026-08-21-measure-reach-firing/probe_immunity.json:
    backed_only_by_declared_structural = 0 over 3528 candidate artifacts,
    so no committed root's adjudication moves. Re-run that probe as the
    before/after measurement.

Read first: docs/map/CON-warrants-and-attacks.md (the "What counts as
substantive rather than structural" row and its check), docs/map/
SUB-evaluation.md Traps ("Structural well-formedness protects nothing"),
docs/map/INV-frozen-surfaces.md.

Design question the tranche must answer, not assume: whether the fix is to
DERIVE _STRUCTURAL_PROGRAMS from programs_by_class()['structural'] (single
source of truth, but it silently re-classifies any future program by its
declaration) or to add the five names and add a gate test asserting the two
sets agree (explicit, but still two sources). CON-warrants-and-attacks.md
line 142 already carries a check over this pair -- extend it either way.

Do NOT lower REACH_COVERAGE_MIN, widen the qualifying vocabulary, or
reclassify any predicate as part of this. The census
(experiments/2026-08-21-measure-reach-firing/DIAGNOSIS.md) already ruled
all three out: E5 coverage rejected 0 pairs and E2 non-qualifying rejected
0 pairs.

End state: the two sets agree by construction or by an asserting test; the
map document's check is extended so a future divergence fails docs_verify;
a regression test names this tranche in its docstring; probe_immunity.py
re-run shows no committed root's formally_backed verdict moved; full gate
0 failed. Then re-run
experiments/2026-08-22-live-reach-rich-run/reach_run.sh to mint the
reach-rich root Rung 5's gate needs.
```

---

## P4-reach — a text run cannot seed a second problem with its own criteria

**What:** `workloads/text.py::seed_reasoning_workload` seeds exactly one
problem, and every route that could add a second with DIFFERENT criteria is
closed: `deepreason amend` copies `criteria=parent_input.problem.criteria`
verbatim (`amendment/apply.py:465-470`), `deepreason input freeze` binds one
run input per root, `deepreason merge` refuses any source carrying `Control`
events (`storage/merge.py:70-78`) and every v6 run is full of them, and
`deepreason run` refuses a non-`text` workload profile, so the multi-problem
`website` decomposition — the only structure that ever recorded reach
(`experiments/gemma4_dna_unattended_2026-07-12`: `pi-plan` / `pi-design` /
`pi-comp-*`, each with its own criteria) — has no launch path.

This is not the blocker for THIS tranche (P1-reach is, and fixing it makes
a single-seed run fire). It is parked because Rung 5 counts reach events
across **distinct problem lineages**, and one seed gives one lineage plus
its own spawn cascade. If `K_frame >= 3`, nomination needs independently
seeded problems and none can be seeded.

```
Route: dr-change-orchestrator (change, design-first -- expect to stop at
SPEC.md and report rather than implement).

One goal: decide and record whether a text run may seed more than one
independent problem, each with its own criteria, and if so through which
surface -- so Rung 5's lineage count can exceed one.

Evidence, already committed:
  - experiments/2026-08-22-live-reach-rich-run/rehearsal.json S3: two
    problems that both carry reasoning-envelope-wf but differ in their
    subject predicates produce a full reach hit. That is the shape a
    multi-seed run would have.
  - experiments/gemma4_dna_unattended_2026-07-12 (out of scope for the
    current reader, kept as an artifact of its own version): the only
    roots that ever recorded reach did it across pi-plan / pi-design /
    pi-comp-* -- separately seeded problems with per-problem criteria.
  - experiments/2026-08-21-measure-reach-firing/VERDICT.md, item 5:
    "the run must seed independent problems rather than rely on the
    connection/integration spawn cascade to manufacture them".

Read first: docs/map/SUB-workloads.md, docs/map/SUB-application.md (the
single run path), docs/map/INV-frozen-surfaces.md, and the operator law
"Operations are available to every configuration" (CLAUDE.md, 2026-08-13):
whatever surface this lands on, it must be ONE run path, not a second one
kept in agreement.

Constraint the tranche must respect, not design around: run identity is
deterministic from question + config, and qualification caches by subject
digest. A multi-problem workload changes what "the question" is, so the
design must say what the run id and the subject digest are functions of.

End state: SPEC.md naming one mechanism (a workload spec carrying several
problems? a typed seed operation on the running root? nothing, with the
reason recorded), its effect on run identity and the qualification subject
digest, and the measurement that would prove it. Implementation only on
explicit operator approval.
```

---

## P7-reach — the conjecturer seat exhausts its repair budget by patching the SIBLING pointer, and ends the run

**What:** the epoch-1 live run terminated at cycle 2 of 24 with
`state=failed`, `stop_reason=operational_failure`, message
`V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY at
/workflow/insufficient_capability_by_route_seat: route seat has terminally
exhausted its smallest authorized contract`. The typed cause object
(`objects/workflow-route-seat-insufficient-capability-v1/80f0c2db…`) gives
`reason: smallest_authorized_contract_schema_exhausted`, role `conjecturer`,
seat 0, `contract_id conjecturer.atomic-candidate.v1`,
`observed_provider_calls 5 / maximum 5`, `attempt_index 4 /
maximum_schema_repairs 4`, after the same seat had already spent five calls
on `conjecturer.turn.v6`.

**This is NOT the ledgered glm-5.2 cap-burn, and the ledgered remedy does not
apply.** CLAUDE.md's known provider fact — a reasoning model can burn the
whole completion cap on hidden reasoning and emit nothing — has a signature:
zero completion tokens. `epoch1-repair-census.json` (produced by
`repair_census.py`, read-only over the committed root) records
`attempts_with_zero_completion_tokens: 0` across all 41 provider attempts.
The seat emitted output every time.

What it emitted is the finding. Of the 17 attempts carrying a repair
diagnostic, **2 returned a well-formed patch addressed to a pointer OUTSIDE
the authorized set, and both are the SIBLING INDEX of the authorized one**:

    attempt 3  conjecturer.turn.v6
      authorized  /scratch_proposal/unresolved_questions/1/related_refs
      patched     /scratch_proposal/unresolved_questions/0/related_refs
      completion_tokens 40

    attempt 4  conjecturer.atomic-candidate.v1
      authorized  /candidate/checker_specs/1/id
      patched     /candidate/checker_specs/0/terms
      completion_tokens 23

Both are the FINAL repair attempt of their contract, so each off-target patch
is what actually consumed the last repair and drove the seat to terminal
exhaustion. The diagnostic envelope for the second
(`blobs/11/11659d8c…`, `repair.diagnostic-envelope.v2`) asked for exactly one
thing — `extra field at /candidate/checker_specs/1/id` — and the raw provider
output (`blobs/9b/9b29d126…`) is verbatim
`{"op": "remove", "path": "/candidate/checker_specs/0/terms"}`.

**Why this is parked and not fixed here.** This tranche is READ-ONLY on
`src/` and `tests/` by operator instruction, and it is a live-run tranche
with one goal. It is also NOT a reach defect: it ended the run before the
reach hypothesis could be exercised over its 24-cycle budget, which is a
different failure from reach not firing.

```
Route: deepreason-orchestrator (defect, design-first -- expect to stop at
DIAGNOSIS.md and report; the cause may be prompt-side, contract-side, or
simply a provider limitation to be absorbed rather than fixed).

One goal: decide and record why a repair-authorized seat returns a patch for
the sibling index of its authorized pointer, and whether the repair loop
should reject an off-target patch WITHOUT consuming a repair attempt -- so a
model that answers the wrong question does not spend the budget reserved for
answering the right one.

Evidence, already committed:
  - experiments/2026-08-22-live-reach-rich-run/failed-epoch1-run-40e713b30a147dfc1a0f73feb91fa67a493454f6103a452888b8e08713368c4c/
    objects/workflow-route-seat-insufficient-capability-v1/80f0c2db472148a39df59dc3c641e585a836e8ff54f6b5253328d8ee1036a00c.json
    -- the typed cause: reason smallest_authorized_contract_schema_exhausted,
    role conjecturer, seat 0, 5/5 provider calls, attempt 4/4 repairs.
  - .../blobs/11/11659d8c45a0c60c2391062e1ad671c14534ee655873156c81940f3e316a40e5
    -- the repair.diagnostic-envelope.v2 with authorized_pointers
    ["/candidate/checker_specs/1/id"].
  - .../blobs/9b/9b29d126c95169f48b657bb5f61c7260cb7ae58500f71a912c6be6d2b7d58471
    -- the verbatim provider output patching /candidate/checker_specs/0/terms.
  - experiments/2026-08-22-live-reach-rich-run/epoch1-repair-census.json and
    repair_census.py -- re-derive both off-target repairs and the
    attempts_with_zero_completion_tokens = 0 fact in one command:
      python repair_census.py <root> out.json

Read first: docs/map/INDEX.md for the workflow subsystem and the
route-seat/contract-decomposition seam, docs/map/INV-frozen-surfaces.md
(the workflow v6 transaction record formats are not to be reshaped), and
CLAUDE.md's known provider fact about glm-5.2 -- the point of this finding is
that the signature does NOT match it, so do not reach for a bigger completion
cap.

Do NOT respond by raising --maximum-completion-tokens or max_tokens. The
census shows every attempt emitted output and none emitted zero tokens; a
bigger cap addresses a failure that did not occur here, and it would change
the provider profile, the qualification subject digest and the run identity
for no reason.

Constraint the design must respect: whatever is decided, an off-target patch
must remain a TYPED outcome in the record. Silently retrying it, or widening
authorized_pointers so the wrong patch becomes acceptable, would trade a
recorded refusal for an unrecorded one.

End state: DIAGNOSIS.md naming one cause and one of -- (a) correct as
written, the seat is simply not capable and the typed terminal is the right
answer, with the reason recorded; (b) an off-target patch should be rejected
without consuming a repair attempt, with the guard named; (c) the repair
prompt does not make the authorized pointer unambiguous, with the change
named. Implementation only on explicit operator approval.
```

---

## P8-reach — the ladder asks `deepreason results` for a root with `--root`, and records a path error instead of the run summary

**What:** `reach_run.sh`'s audit block runs

    python -m deepreason --root "$ROOT" results > "$HERE/results.txt"

but `results` takes its target as a POSITIONAL argument (`deepreason results
ROOT-OR-HOME`, README / dr-drive-harness §2). With none given it falls back
to `DEEPREASON_HOME`, which the ladder points at `$HERE/home` — a
qualification home holding no run. `epoch1-results.txt` therefore reads, in
full:

    RESULTS_ROOT_NOT_FOUND: /home/user/DeepReason/experiments/2026-08-22-live-reach-rich-run/home
    is neither a run root (no log.jsonl) nor a home holding one

The typed retrieval surface answered correctly; the ladder asked it the wrong
question. Running `python -m deepreason results <root>` by hand against the
same root returns the full summary, so nothing was lost — but the committed
audit artifact of a live run is an error string, and the ONE retrieval
surface the driving manual names is the one the ladder failed to capture.

Not fixed here: this tranche's ladder is part of a frozen pre-registered
design, and editing it mid-tranche would change the instrument between epoch
1 and epoch 2 of the same experiment.

```
Route: dr-change-orchestrator (change, one-line, experiment tooling only --
no src/ or tests/ involvement).

One goal: make the reach-rich ladder capture the run's typed results instead
of a path error, so the committed audit artifact of a live run carries the
run summary.

Evidence, already committed:
  - experiments/2026-08-22-live-reach-rich-run/reach_run.sh, the AUDIT block:
    `python -m deepreason --root "$ROOT" results` -- --root is not how
    results is addressed.
  - experiments/2026-08-22-live-reach-rich-run/epoch1-results.txt -- the
    resulting RESULTS_ROOT_NOT_FOUND line, naming $HERE/home.
  - The same root answered correctly when addressed positionally
    (state failed, stop_reason operational_failure, verify_root violations 0,
    embedder neural) -- quoted in RESULTS.md's epoch-1 segment.

Read first: README.md's public CLI lifecycle and .claude/skills/
dr-drive-harness/SKILL.md section 2, which both give the positional form.

Check whether any OTHER committed ladder carries the same invocation before
fixing just this one; a one-line defect copied across experiment scripts is
worth fixing everywhere it was copied.

End state: the ladder invokes `python -m deepreason results "$ROOT"`, a
re-run (or a replay against a retired root) produces a results.txt carrying
the run summary, and any sibling ladder with the same invocation is fixed in
the same commit.
```
