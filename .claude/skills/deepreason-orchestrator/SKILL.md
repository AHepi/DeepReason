---
name: deepreason-orchestrator
description: Entry point for any DeepReason problem. Routes work to exactly one subskill at a time and enforces the scope contract. Use when asked to manage, diagnose, or fix anything in DeepReason.
---

# DeepReason problem orchestrator

You are running a tightly bounded workflow. You do not freelance. You
select ONE subskill, execute it to its exit criteria, then return here
to select the next. You never blend phases.

## The scope contract (read before every phase)

1. **One tranche = one goal.** A tranche works exactly one GOAL.md
   (produced by `dr-set-goal`). Anything else you notice goes into
   `PARKED.md` — never into your work. Write the parked entry for its
   FUTURE RUNNER, at park time, while the context is free: one line of
   WHAT, then a ready-to-send prompt (route, one-goal statement,
   evidence pointers, end state). Starting the follow-up should cost
   the operator a paste, not an authoring session.
2. **Evidence over prose.** Claims about DeepReason behavior are only
   admissible if derived from typed records: `log.jsonl`, `objects/`,
   `progress.jsonl`, `run-status.json`, `REPLAY_VALIDATION.json`,
   `verify_root`, or test output. Your own summary of what code
   "probably does" is not evidence.
3. **No phase-skipping.** You may not implement without an approved
   FIX.md. You may not write FIX.md without a DIAGNOSIS.md. You may not
   write DIAGNOSIS.md without a reproduction or record-derived trace.
4. **Stop conditions.** Stop and report (do not improvise) when: a
   command fails twice the same way; evidence contradicts the goal;
   the fix requires touching frozen-record semantics (anything under
   `capabilities/state.py` digests, `harness.py` event application, or
   replay validation record formats); or the diff would exceed ~150
   changed lines. Before any stop becomes a question to the operator,
   load `dr-ask-the-right-question`: route it to the cheapest authority
   first, and ask only what survives the dominance test — batched, with
   a recommendation.

## Map and environment preflight (do this before routing, every time)

Full procedure, canonical: `dr-drive-harness` §1 (session/environment
preflight — branch resync, `deepreason` importable, credential check)
and §4 (map preflight — `docs/map/INDEX.md` → `INV-frozen-surfaces.md`
→ seam document → record the resolved ids in GOAL.md). Load it if this
session has not run the harness before. Also load
`pinker-write-for-readers` once per session, BEFORE your first message
the operator will see (it replaced `dr-explain-to-operator` on
2026-09-03; CLAUDE.md Conventions state what carries over).

The map is maintained by the phases that change code, in the same
commit — see `dr-execute-step` and `dr-implement-fix`. Nothing else may
advance a `Verified-at:` stamp.

## Routing table

Ask: what does the current state of the tranche lack?

| Missing artifact | Route to |
|---|---|
| No GOAL.md for this tranche | `dr-set-goal` |
| GOAL.md exists, no DIAGNOSIS.md | `dr-diagnose` |
| DIAGNOSIS.md names a cause but nothing demonstrates it | `dr-reproduce` |
| Reproduction exists, no FIX.md | `dr-propose-fix` |
| FIX.md exists, code unchanged | `dr-implement-fix` |
| Code changed, outcome unverified | `dr-verify-outcome` |
| dr-verify-outcome reported PASS | Tranche complete: report and stop |

If `dr-verify-outcome` reports FAIL, route back to `dr-diagnose` with
the failure evidence appended — do not patch forward from intuition.

## Tranche working directory

All tranche artifacts live in one directory the goal names, e.g.
`experiments/<date>-<slug>/`: `GOAL.md`, `DIAGNOSIS.md`, `REPRO.md`,
`FIX.md`, `VERIFY.md`, `PARKED.md`. Commit and push this directory at
every phase boundary (the container can vanish at any time):

    git add -A <tranche-dir> && git commit -m "<phase>: <one line>" \
      && git push -u origin <branch>

## Hard prohibitions (apply to every subskill)

- Never modify a committed run root's contents; never commit credential
  material — both procedures (retire-by-rename, `git check-ignore`) are
  canonical in `dr-drive-harness` §1/§3.
- Never run the full live ladder to test a code hypothesis — that is
  `dr-verify-outcome`'s final step only, and only when the goal calls
  for live proof.
- Never widen the goal because the codebase "needs" it. PARKED.md.
