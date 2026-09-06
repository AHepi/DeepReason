# Pre-registration — the census of what the writer's room ejects (S4, R3)

Written before the room run it describes is launched; sealed by the sha256
in its commit message. Amendments are dated and appended, never edited in.

## The question (R3, the operator's words)

"a measure of the types of contents ejected. I'm particularly interested to
see if the commitment artifacts actually have anything in them?"

## What runs

ONE live run of `mini.flow.room.v1` (S2: the three room forms, both
commitment channels off, the flow's own brief limit) for 3 cycles on the
same standard input as D8 (`experiments/2026-09-05-change-mini-isolation-
programme/runs/input-d8`, problem `question-corroboration-d8`, criteria
`[]`), through the managed shallow entry with the predecessor's disclosed
reasoning-field override (P10 stays parked), provider profile
`qwen3.5:397b`, reasoning off, cap 8192, `model_profile: standard`.
Detached, snapshot loop armed. Typed terminal as PREREG_D8 §2 defined it:
`completed`, a typed stop, meter equals log, `verify_root` 0, replay digest
equal.

## What is counted (`tools/census.py`, committed with this document)

The instrument reads the ROOT only and prints one table:

- **briefs**: total; how many carried the seat's directive byte-intact (the
  tail of each seat's directive text, found in the prompt blob); how many
  `mini:brief-clipped` markers the record holds.
- per seat (**commitment first**): calls, outputs, tokens; output length
  min/mean/max; **on-target** (the `about` id resolves to a conjecture);
  **mentions** (any commitment marker anywhere: refute/falsify, forbid, must
  not/cannot/prohibit, predict); **binds-1st** (the STRICT shape: the first
  sentence itself binds the conjecture — must, forbids, refuted if, cannot,
  predicts); **exact-dup** (byte-identical to another output);
  **near-dup** (≥3 shared six-word phrases with another output);
  **echo** (≥3 shared six-word phrases with its own target).

RESULTS.md quotes EVERY commitment proposal verbatim, then a sample of
objections and conjectures, and states for each proposal in one line whether
a reader would call it a commitment (what would refute / what it forbids /
what it must not do) or something else. That reading is the assistant's and
is labelled as such; the table is the instrument's.

## What decides "anything in them"

Stated now so the answer is not fitted afterwards. The commitment seat has
"something in it" for this run iff ALL of:

1. directive intact on every commitment brief (else S1 failed live and the
   census is void — the tranche stops and says so);
2. on-target = outputs (every proposal names an existing conjecture);
3. binds-1st ≥ half the proposals, AND exact-dup = 0;
4. at least one proposal per conjecture states a refutation condition that
   is NOT a restatement of the conjecture's own conclusion (the assistant's
   line-by-line reading, quoted).

Anything less is reported as exactly what it is; no re-run for a number.
The D8 root, run through the same instrument before this tranche's fix,
reads: briefs 19 / intact 9 / clipped 10; commitment 14 outputs, binds-1st
8, exact-dup 6 — the "before" row RESULTS.md carries beside the "after".

## Predictions

- Directive intact 19 of 19 (or however many calls), clipped markers 0.
- exact-dup among proposals: 0 (the duplicated triple was an uninstructed
  seat copying the last thing it saw).
- The conjecturer returns the requested number of candidates every cycle.
- No direction predicted for binds-1st or for what the proposals say.

## Residue stated in advance

One run, one question, one model: a census of a sample, not a rate. The
markers are keyword tests; the quoted proposals are the evidence, the
columns are the index.
