# REQUEST — close-out prune of `experiments/`

Tranche: `experiments/2026-08-25-change-closeout-prune/`
Opened: 2026-08-25. Model: `claude-opus-5`.
Base HEAD: `6e64330fe`.
Authority artifact: `experiments/2026-08-25-audit/PARKED.md` P4, approved.

## The operator's words, VERBATIM

Standing authority, from the close-out audit brief:

> "all experiments and tests need to be audited so I can get rid of them."

Approval of P4, in full:

> "Approved. Do both stages. Do not report back unless you find a real
> block. After both stages are complete. I'll tell you what next."

## Requirements

- **R1** — Do BOTH stages of `experiments/2026-08-25-audit/PARKED.md` P4,
  in its stated order. Stage 1 (extract) before Stage 2 (delete); the
  prompt states the order is load-bearing.
- **R2** — Stage 1: create ONE standing registry,
  `experiments/OPEN_PARKS.md`, and move every open park item from the 18
  EXTRACT-THEN-PRUNE directories into it VERBATIM, each row naming its
  originating tranche and the git sha where its full text lives.
  Explicitly: "Do not summarize an item; a park is a ready-to-send
  prompt and loses its value when compressed."
- **R3** — Stage 2: remove the 52 PRUNE directories plus the 18 EXTRACT
  directories once R2 has re-homed them. 70 directories total.
- **R4** — Do NOT touch the 82 directories rowed KEEP in
  `experiments-census.md`.
- **R5** — Gate, both required, after the removal:
  `python tools/docs_verify.py` (FULL mode, not `--fast`) and
  `python -m pytest tests/ -q -n 4` (0 failed; baseline 4162 passed,
  6 skipped). Either instrument going red means something load-bearing
  left the tree: restore it, row it in `experiments-census.md` as a KEEP
  the census missed, and say which of Q-E1..Q-E4 failed to catch it.
- **R6** — Do not report back unless a real block is found. Report on
  completion of both stages, then stop and await direction.

## Scope boundary, recorded so it cannot drift

P5 (the docs prune, 13 files under `docs/`) is **NOT** in this tranche.
"Both stages" names P4's two stages; P5 has no stages. The operator's
closing sentence — "After both stages are complete. I'll tell you what
next." — reserves the next instruction to them. P5 is left untouched and
still parked.

## Assumption recorded at capture time

**A1 — the git sha R2 requires.** The prompt says each row must name
"the git sha where its full text lives". Taken as: the sha of the last
commit that MODIFIED that tranche's `PARKED.md`, obtained per file via
`git log -1 --format=%H -- <path>`. That is stable, precise, and
survives this tranche's own commits, where naming the pre-deletion HEAD
would not distinguish one park file from another.

## A1a — SUPERSEDES A1 (recorded at step 1, not silently changed)

A1 proposed a per-file sha via `git log -1 --format=%H -- <path>`. **That
does not work in this container and A1 is withdrawn.**

Measured at step 1: all 18 `PARKED.md` files returned the SAME sha,
`c1f96ae36`. That is the shallow-clone graft boundary — the oldest commit
in a 59-commit shallow clone — not the commit that last touched each file.
`git log` cannot see past the graft, so it attributes every unmodified
file to the boundary. A per-file sha here would be uniform, uninformative,
and wrong about provenance.

**A1a, used instead:** record the PRE-DELETION HEAD,
`6e64330fea8822fb6ce9f32a13073b8798fd1114`. Every one of the 70
directories demonstrably exists in full at that commit, so
`git show 6e64330fe:<path>` retrieves any deleted file's exact bytes.
Verified at step 1 against
`experiments/2026-08-24-change-rung5-promotion-criteria/PARKED.md`
(7153 bytes retrieved).

This satisfies R2's purpose — "the git sha where its full text lives" —
with a sha that is true rather than one that merely looks per-file.
Proof: `proof/pre-state.txt`, `proof/sha-correction.txt`.
