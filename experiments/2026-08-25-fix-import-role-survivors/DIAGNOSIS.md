# Diagnosis: survivorship is derived twice, and only the scheduler's copy carries the invariant

Primary cause: **there is no single authority for what counts as a "survivor".**
The membership rule — ACCEPTED, addressed, and **not** an import-role admission
record — is written out by hand in `Scheduler._select_problem`, where it was
installed after the `selfstudy run-9175f0ec` defect, and is written out again,
WITHOUT the role clause, in `run_report`, the module-level function that builds
the survivor set published into every root's `run-result.json`. `deepreason
results` then reports that published set's length verbatim
(`len(result["survivors"])`). So the invariant holds exactly where it was
patched and nowhere else: the scheduler declines to call an import record a
survivor when ranking problems, and the reporting path calls the same record a
survivor when telling the operator what the run produced. This is the failure
mode E26 names — two derivations of one fact, kept in agreement by nothing.

Evidence (record first; the code sites are named afterwards, not as the
argument):

  - `experiments/2026-08-25-poietics-program/run/run-result.json` -> lists
    **82** survivor ids. Re-deriving each id's role over the replayed state
    (`Harness(root, read_only=True).state.artifacts[aid].provenance.role`)
    gives **58 `CONJECTURER` + 24 `IMPORT`**. This is the number `deepreason
    results` prints under the gloss "positions still standing at the end"
    (`application/results.py::render_results`).
  - `run/log.jsonl` seqs **5–40** -> each of the 24 IMPORT survivors enters on
    its own `Register` event whose `inputs` is the operator's seed problem
    `question-aa835741bebc4b4cb189f4b08bef649a` and whose `state_diff`
    changes its status in the same event. The first LLM-bearing event in the
    whole log is **seq 85** (`Rule.CONTROL`, role `conjecturer`). **All 24
    "survivors" were accepted before any model was consulted.** They did not
    survive criticism; there was none yet to survive.
  - `state.addr` -> all 24 are addressed to that same seed problem, which is
    precisely the shape `DR-SUB-scheduler`'s Traps entry describes: "evidence
    admission had already auto-accepted import-role records ADDRESSING the
    question".
  - `docs/map/CON-scheduler-ranking.md:32` -> states the rule as a socket
    promise and pins it with `check: grep -q "provenance.role !=
    ProvenanceRole.IMPORT" src/deepreason/scheduler/scheduler.py`. A grep for a
    literal in one function is exactly the check that passes while a second
    derivation two hundred lines up in the same file has no role clause at all.
  - `run/run-result.json` `frontier` -> 40 ids, **all `CONJECTURER`**, and
    none of the 24 IMPORT ids carries an `hv` or a `reach` entry in replayed
    state. The frontier is therefore already free of them: they are dominated
    points, and dropping a dominated point cannot move a Pareto front.

Implicated code:
  - `src/deepreason/scheduler/scheduler.py:212` — `run_report`'s
    `survivors = sorted({aid for aid, _ in state.addr if state.status.get(aid)
    == Status.ACCEPTED})`. The writer. No role clause.
  - `src/deepreason/scheduler/scheduler.py:1083` — `_select_problem`'s
    `survivors_by_problem`, the ONE site that enforces the invariant.
  - `src/deepreason/application/results.py:218` — `_artifacts` sets
    `counts["survivor_count"] = len(result["survivors"])`. The reader, which
    inherits the writer's membership whole.

Falsifiable prediction (what `dr-reproduce` must show):

    python - <<'PY'
    from deepreason.application.results import results_summary
    s = results_summary("experiments/2026-08-25-poietics-program/run")
    print(s["artifacts"]["survivor_count"])
    PY
    # expected on the UNFIXED tree: 82
    # and an independent role census over the same root's replayed state
    # must partition those 82 as 58 CONJECTURER + 24 IMPORT,
    # with 24 == the count the scheduler's own predicate already excludes.

Ruled out: **"the invariant governs only the scheduler's aging weight, and
CLAUDE.md merely states it unqualified"** — the alternative reading P4's prompt
asked to separate before proposing anything. It fails on the record, not on
wording. The scheduler's reason for excluding import records is that admission
bookkeeping must not be *mistaken for a solved candidate*; the reporting
surface makes the identical mistake, on the identical artifacts, and states it
to the operator in the identical vocabulary ("positions still standing"). The
seq evidence closes it: an artifact accepted at seq 5–40 and never criticised
before seq 85 is not a position that survived anything under any reading of the
word. The narrow reading would also have to explain why `run_report`'s set —
which is not an aging weight, and which the scheduler itself never consults for
ranking — should differ from `_select_problem`'s. Nothing in the record or the
map offers such a reason.

Second cause found and PARKED (not primary, does not block the criterion):
`src/deepreason/report.py::eval_report` and `src/deepreason/loop.py::
run_problem` each derive a third and fourth survivor set of their own. See
PARKED.md P1.
