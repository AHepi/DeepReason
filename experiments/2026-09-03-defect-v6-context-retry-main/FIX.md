# FIX — one owner for dispatch-time conjecture-context planning

Transplanted verbatim from `06b0d9fd9` on branch
`claude/model-profile-registry-opkgal`. No redesign: the fix is
already proven, and re-deriving it here would only risk drift.

## The change

`src/deepreason/scheduler/scheduler.py` gains one method,
`_dispatch_conjecture_context_plan`, which is the ONLY source of a
dispatch-time context plan:

```python
def _dispatch_conjecture_context_plan(self, problem, school_id: str | None):
    if self.run_manifest is not None and self.run_manifest.schema_version == 6:
        return None
    return self._plan_conjecture_context(problem, school_id)
```

Both call sites — the primary dispatch and the
`ConjectureContextStale` retry — call it. There is nowhere left for
the two to drift.

Note what the v6 branch now does differently from the old primary
path: it SKIPS the planner rather than running it and discarding the
result. A v6 retry no longer spends work building a plan that Conj
will refuse.

## Why the smallest correct fix is not "add the null-out to the retry"

Adding a second copy of the guard fixes this instance and leaves the
defect's shape intact: two expressions, one rule, and nothing that
fails when a third site appears. The recorded defect is the DRIFT, not
the missing line. The regression file therefore carries a structural
half — `_plan_conjecture_context` has exactly one caller, and every
`context_plan` assignment comes from the owner — which a
behaviour-only test cannot express.

## Bounds

- Files: `src/deepreason/scheduler/scheduler.py` (one method added, two
  call sites rewritten) and the new
  `tests/test_scheduler_v6_context_plan_retry.py`, byte-identical to
  the originating commit's copy.
- Map, same commit: `SUB-scheduler.md` Traps entry;
  `SEAM-scheduler-x-workflow.md` row + check re-expressed against the
  owner; `SEAM-schools-x-scratch.md` check re-expressed likewise.
  Neither check's CLAIM changes and neither is weakened — both must
  still fail if the v6 rule is removed, proven by the same mutation.
- Frozen surfaces: none touched. `scheduler/scheduler.py` is on no
  frozen surface (DIAGNOSIS.md §Frozen-surface check).
- Deliberately NOT taken from the originating commit: its
  `experiments/` payload, `mini/`, and the env-var generator hook in
  `rules/conj.py`.
