# The verdict census — every committed root, before and after

`census.py` runs `verify_root` over every directory in the tree containing a
`log.jsonl` (94 of them) and records each root's violations as a sorted list of
`<check>::<detail>` strings. Run twice on 2026-09-09:

    after.json   the fixed tree, in place
    before.json  a `git worktree` at this branch's pre-fix head
                 (`cd <worktree> && PYTHONPATH=<worktree>/src python census.py before.json`)

Both runs read the SAME 94 roots; no root was written to.

## The diff

    python - <<'PY'
    import json
    b = json.load(open("before.json")); a = json.load(open("after.json"))
    for k in sorted(set(b) | set(a)):
        if b.get(k) != a.get(k):
            print(k, "\n  before:", b[k], "\n  after :", a[k])
    PY

Two roots move, both from dirty to clean, and they are exactly the four calls
FIX.md's census predicted:

| root | before | after |
|---|---|---|
| `…organiser-testing/…/run-c3f3bf10bc57d63e224a9f1c68bf1057` | 3 × `attempt-validity` (seqs 142, 215, 295) | `[]` |
| `…rung5-dumb-alternative-backend/…/run-9a6be78e1e79184a0bd89923b957586c` | 1 × `attempt-validity` (seq 17) | `[]` |

**67 roots verified clean before; all 67 verify clean after.** Nothing moved
from clean to dirty, which is what FIX.md's superset argument predicted:
`SEMANTIC_REJECTION` accepts `valid_indexes in ([], [len(trace) - 1])` where
`FAILURE_REQUIRED` accepts only `[]`.

The 25 roots that carry violations after the fix carry the SAME violations they
carried before, string for string. One of them still names `attempt-validity` —
`…constructive-frontier/void-inert-battery-run-6913328037a61ca6`, "event
seq=2413: successful call must have one final valid attempt, got []". That is
the `SUCCESS_REQUIRED` clause, a different rule inside the same check, and this
tranche does not touch it.

This is a targeted census, not the retired root sweep: it is the instrument the
2026-08-25 grant's precedent calls for, and it answers one question — does any
root's verdict move that FIX.md did not predict.
