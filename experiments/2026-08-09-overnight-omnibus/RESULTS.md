# Overnight omnibus — 2026-08-09

Honest-ledger segments, one per block, plus a final omnibus decision
table. Judged from typed records only (`run-status.json`,
`REPLAY_VALIDATION.json`/`verify_root`, `progress.jsonl`, audit JSON
under each block's own directory). Model prose is never evidence.

Sibling window: a 2026-08-09 pre-flight search (`git branch -a`,
`git log --all --grep`) found no "corpus-enrichment + patrol pilot"
branch anywhere in this repo. This tranche made no patrol calls and
ran no dual-mode enrichment, per the operator's instruction not to
duplicate that window regardless of whether it is visible here.

## Process note (self-caught, fixed forward)

`snapshot_loop.sh`'s exclude pathspec
(`":!.../home-*/runs"`) matched only the `runs` directory entry
itself under git's default pathspec matching, not its recursive
contents — it needed a trailing `/**`. Before this was caught, one
manual commit (`f2606b53`) and one auto-snapshot committed a CROSS-cell
run root mid-append (lock files included). No working data was lost —
the run reached its own terminal state in a later snapshot — but this
is a real violation of this repo's "never commit a run mid-append"
rule, recorded here rather than silently ignored. Not rewritten: this
is a private working branch with no open PR, and CLAUDE.md's own
convention for a caught process error is fix-forward, not history
rewrite. `snapshot_loop.sh` was fixed and relaunched at commit
`d7fdec85`; everything after that commit is clean (verified by
`git diff --cached --name-only | grep /runs/` before every subsequent
commit in this tranche).

<!-- Block A segment: filled in once all 12 runs (2 cells x 2
questions x 3 seeds) have completed or been judged closed. -->

## Block A — criticism-symmetry pilot cells

(pending — runs in flight as of this segment's drafting)

## Block B — capability-channel stochasticity funnel

(pending — runs in flight as of this segment's drafting)

## Block C — reasoning-token completion-cap curve

(pending — runs in flight as of this segment's drafting)

## Block D — qualification battery re-sampling

(pending — runs in flight as of this segment's drafting)

## Block E — end-of-night overlay sweep

(pending — runs last, after A-D)

## Omnibus decision table

(filled in at the end: every number, its block, what it decides)

## Failure ledger

(ledgered S6-style; budget 15)

## Residue

(what remains unproven, honestly stated)
