# PARKED — W7

Two things this tranche noticed and did not fix. W7 writes one document
and nothing else (`REQUEST.md` R2), so both are prompts, not changes.
Each is written for its future runner: starting the follow-up should cost
a paste, not an authoring session.

---

## W7-P1 — `docs_verify` reports a red gate on a shallow clone, and the failure looks real

**WHAT.** This container's checkout is a shallow clone (138 commits
reachable at session start). `docs/map/CON-run-identity.md` carries three
`check:` commands that address commits by hash — `1637e808`, `f304fec1`,
`6a8758a5` — none of which is in a shallow fetch. `python
tools/docs_verify.py` therefore reported **3 failed**, in a document this
tranche never touched, with the underlying cause visible only as
`fatal: ambiguous argument '1637e808': unknown revision`. After
`git fetch --unshallow origin` (5.3 s, 138 → 2 536 commits) the same run
reports **1 073 checks, 0 failed**.

**WHY IT MATTERS.** A red gate that is not the window's fault costs a
diagnosis every time it is met, and the failure text does not say
"shallow clone" — it says a revision is unknown, which reads like a
deleted commit or a bad hash. CLAUDE.md already warns that the container
can roll back; it does not warn that the clone can be too shallow for the
docs gate.

```
Route through dr-change-orchestrator.

REQUEST: `python tools/docs_verify.py` fails three checks in
docs/map/CON-run-identity.md on a shallow clone, because those checks
address commits by hash and a shallow fetch does not carry them. The
failure text names an unknown revision, not a shallow clone, so every
window that meets it pays for the diagnosis again.

Reproduce:
  git rev-parse --is-shallow-repository      # true
  python tools/docs_verify.py                # 3 failed, all
                                             # CON-run-identity.md
  git fetch --unshallow origin               # ~5 s
  python tools/docs_verify.py                # 1073 checks, 0 failed

SPEC the smallest correct change. The candidates, in the order I would
price them:
 (a) a preflight in tools/docs_verify.py: if the repository is shallow,
     say so once, up front, naming `git fetch --unshallow origin` as the
     remedy. Cheapest; changes no check.
 (b) additionally, classify a check whose only error is an unknown
     revision on a shallow clone as SKIPPED-WITH-REASON rather than
     FAILED — but read tools/docs_verify.py --audit's rule FIRST: it
     refuses checks that cannot fail, and a skip road is a way for a
     check to stop failing. If (b) risks that, do only (a).
 (c) a line in CLAUDE.md's "Environment (cloud container)" section, next
     to the existing rollback resync recipe.

Do NOT weaken or rewrite the three checks themselves. They are correct
and they pass on a complete clone; the gate's REPORTING is what is at
fault, not what it checks.

End state: on a shallow clone the gate either passes or says plainly why
it cannot, and `python tools/docs_verify.py --audit` still refuses every
check that cannot fail.
```

---

## W7-P2 — the synthesis cites two windows that are not on `main`

**WHAT.** `docs/RUN_ANATOMY_SYNTHESIS_2026-08-26.md` cites W2
(`experiments/2026-08-26-run-anatomy-w2-criticism/`) and W3
(`experiments/2026-08-26-run-anatomy-w3-evidence-scratch/`), which exist
only on `claude/criticism-anatomy-w2-1z2029` and
`claude/run-anatomy-w3-census-p5pgmb`. The document names the branch at
every such citation and states the fact in its header, so no reader is
misled — but a reader on `main` cannot follow those citations to their
evidence, and W2's and W3's parked prompts are not discoverable from
`main` either.

**NOT A DEFECT, and not this tranche's to fix.** Merging two windows is a
different scope from writing one document, and both branches are behind
`main` on other paths (each deletes the other windows' directories in a
plain diff), so the merge needs its own window and its own care.

```
Route through dr-change-orchestrator.

REQUEST: bring the two unmerged RUN ANATOMY windows onto main so the
synthesis's citations resolve there.

  W2  claude/criticism-anatomy-w2-1z2029
      experiments/2026-08-26-run-anatomy-w2-criticism/   (17 files)
  W3  claude/run-anatomy-w3-census-p5pgmb
      experiments/2026-08-26-run-anatomy-w3-evidence-scratch/ (12 files)

READ FIRST, because a naive merge is wrong: both branches predate the
W4/W5/W6 merges, so `git diff origin/main <branch>` shows them DELETING
W1/W4/W5/W6 and touching scripts/cycle_soak.py, src/deepreason/
invariants.py and tests/test_v6_transport_failure_pairing.py. Those
deletions are an artifact of the base, not an intention. The two window
directories are additive and are the only paths that should move.

Both windows are READ-ONLY tranches: nothing under src/ or tests/ is
theirs to bring. Prove that after the merge with
`git diff --name-only origin/main | grep -E '^(src|tests)/'` returning
nothing.

While there, consider whether PROGRAM.md's concurrency contract should
gain a dated amendment recording that W2 and W3 named their own
top-level directories rather than W2-/W3- subdirectories of the program
directory, since that naming is why they are easy to miss. PROGRAM.md is
W1's; a later window APPENDS a dated amendment and never edits what is
above it.

End state: both directories on main, docs_verify green, and every
citation in docs/RUN_ANATOMY_SYNTHESIS_2026-08-26.md resolving on main.
Update that document's header table in the same commit to say the
windows are merged — it is the one place that currently says they are
not.
```
