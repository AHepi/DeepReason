# Request: "Is it possible to put this in the workflow? I want to test it's limits."
Captured: 2026-08-23, from the tranche instruction opening this session
(operator verbatim quoted inside it, attributed to the operator, 2026-08-23).

## Verbatim

Operator's own words, as supplied under AUTHORITY in the tranche instruction:

> "Is it possible to put this in the workflow? I want to test it's limits.
> And it gives genuinely independent review with my API key."

The tranche instruction elaborating those words (the operating brief, quoted
in the parts that bind this work):

> Change tranche: install treadle 0.4.1 as the workflow's third lane —
> a deterministic driver for independent review and mechanical tasks —
> then run its four-rung limits pilot. Route through
> dr-change-orchestrator; the workflow's own stops apply.

> THE OPERATOR SUPPLIES the zip (treadle0.4.1.zip) and, at the run step only,
> OLLAMA_API_KEY — never committed, env only.

> INSTALL, per the zip's AGENT_INSTALL.md with TWO recorded deviations (ledger
> both):
> D1 VENDOR, don't ~/tools: containers roll back and wipe gitignored paths, so
>    the treadle SOURCE is committed into the repo at tools/treadle/ (src,
>    repo-assets, tests, pyproject — verbatim, provenance header in a
>    VENDORED.md noting version 0.4.1 and the two deviations). The venv and
>    .treadle/ runtime dirs are gitignored. Its own `pytest -q` must pass from
>    the venv (the doc says 5 passed; report the actual count for 0.4.1).
> D2 The swarm gate installs at scripts/swarm_gate.py per the doc; treadle.toml
>    at repo root; its skills/ tree as shipped (separate from .claude/skills —
>    no collision; verify by listing).
> Then `treadle doctor` — every line OK (WARN on credentials acceptable
> pre-key); paste it verbatim.

> GOVERNANCE, same commit as the install: CLAUDE.md gains a short "Third lane:
> treadle" paragraph — what routes to it (review-kind verdicts on delivered
> tranches; mechanical tasks whose acceptance is a deterministic command), what
> NEVER routes to it (anything touching a frozen surface — no task cone may
> include one; verify the pilot cones against INV-frozen-surfaces.md), and the
> law that ONLY the operator or the monitor authors tasks (acceptance commands
> run with shell; briefs are trusted input). AUDIT_BASELINES.md gains a
> treadle-doctor entry (expected: all OK).

> THE LIMITS PILOT — four rungs, escalating, each a swarm task with cone +
> deterministic acceptance; run each with `treadle run --once` and record the
> board + calls.jsonl state between rungs:
> T1 MECHANICAL: an audit-broken-style instrument task — run docs_verify,
>    compare to the baselines file, write the delta table under
>    experiments/2026-08-23-treadle-pilot/. Acceptance: the table exists and
>    names the 3 pre-existing failures.
> T2 REVIEW-KIND (the independent-review test): a review task over a real
>    delivered diff — Rung D's proof-debt tranche
>    (experiments/2026-08-22-change-rungd-proof-debt-localization/, its commits
>    on main). Feed the reviewer the delivery's claims with their check commands
>    as the "pairs"; verdict recorded via the gate. We learn whether a cheap
>    foreign model can referee a tranche's own evidence.
> T3 GENERATION: author ONE regression-test fixture for an existing committed
>    behavior (pick a P5-ruling boundary case), cone =
>    experiments/2026-08-23-treadle-pilot/*, acceptance = python -m pytest on
>    the new file passes AND its mutation-proof script exits correctly. We learn
>    whether the small model can produce gate-quality work under a
>    deterministic acceptor.
> T4 EXPECTED LIMIT: a spec-drift-style judgment task (compare one doc claim
>    against code where the answer needs reading comprehension, not a command).
>    Pre-register the prediction that this is where it breaks, and record HOW it
>    fails: refine, escalate, or BLOCKED-with-evidence. A clean BLOCKED is the
>    system working; a confident wrong PASS is the finding.
> Judge every rung on typed outcomes only: the board, the gate verdicts,
> calls.jsonl, and the acceptance exits. Model prose is never evidence —
> including the reviewer's.

> DELIVERABLE: install committed; RESULTS.md honest ledger per rung — what the
> driver did, what it cost (calls, tokens from the ledger), where it broke and
> in which of its three failure modes; a closing recommendation table: which
> DeepReason task classes route to treadle tomorrow, which never. Obey every
> REFUSED_* line from its tools; never work around a refusal (its own rule, and
> ours).

## Requirements

R1 (artifact): "install treadle 0.4.1 as the workflow's third lane" — the
   treadle SOURCE is vendored and committed at `tools/treadle/` ("src,
   repo-assets, tests, pyproject — verbatim"), per deviation D1.

R2 (artifact): "provenance header in a VENDORED.md noting version 0.4.1 and the
   two deviations".

R3 (process): "The venv and .treadle/ runtime dirs are gitignored."

R4 (behavior): "Its own `pytest -q` must pass from the venv (the doc says 5
   passed; report the actual count for 0.4.1)."

R5 (artifact): "The swarm gate installs at scripts/swarm_gate.py per the doc;
   treadle.toml at repo root; its skills/ tree as shipped (separate from
   .claude/skills — no collision; verify by listing)." — deviation D2.

R6 (behavior): "Then `treadle doctor` — every line OK (WARN on credentials
   acceptable pre-key); paste it verbatim."

R7 (artifact): "CLAUDE.md gains a short 'Third lane: treadle' paragraph" stating
   what routes to it ("review-kind verdicts on delivered tranches; mechanical
   tasks whose acceptance is a deterministic command"), what never routes to it
   ("anything touching a frozen surface — no task cone may include one"), and
   "the law that ONLY the operator or the monitor authors tasks (acceptance
   commands run with shell; briefs are trusted input)".

R8 (process): governance lands in the "same commit as the install".

R9 (artifact): "AUDIT_BASELINES.md gains a treadle-doctor entry (expected: all
   OK)."

R10 (process): "verify the pilot cones against INV-frozen-surfaces.md" — no
   pilot task cone may include a frozen surface.

R11 (behavior): T1 MECHANICAL — "run docs_verify, compare to the baselines file,
   write the delta table under experiments/2026-08-23-treadle-pilot/.
   Acceptance: the table exists and names the 3 pre-existing failures."

R12 (behavior): T2 REVIEW-KIND — "a review task over a real delivered diff —
   Rung D's proof-debt tranche ... Feed the reviewer the delivery's claims with
   their check commands as the 'pairs'; verdict recorded via the gate."

R13 (behavior): T3 GENERATION — "author ONE regression-test fixture for an
   existing committed behavior (pick a P5-ruling boundary case), cone =
   experiments/2026-08-23-treadle-pilot/*, acceptance = python -m pytest on the
   new file passes AND its mutation-proof script exits correctly."

R14 (behavior): T4 EXPECTED LIMIT — "a spec-drift-style judgment task ...
   Pre-register the prediction that this is where it breaks, and record HOW it
   fails: refine, escalate, or BLOCKED-with-evidence."

R15 (process): "run each with `treadle run --once` and record the board +
   calls.jsonl state between rungs".

R16 (process): "Judge every rung on typed outcomes only: the board, the gate
   verdicts, calls.jsonl, and the acceptance exits. Model prose is never
   evidence — including the reviewer's."

R17 (artifact): "RESULTS.md honest ledger per rung — what the driver did, what
   it cost (calls, tokens from the ledger), where it broke and in which of its
   three failure modes".

R18 (artifact): "a closing recommendation table: which DeepReason task classes
   route to treadle tomorrow, which never."

R19 (process): "Obey every REFUSED_* line from its tools; never work around a
   refusal (its own rule, and ours)."

## Standing constraints

C1: "Route through dr-change-orchestrator; the workflow's own stops apply." —
    tranche instruction, opening line.

C2: "THE OPERATOR SUPPLIES the zip (treadle0.4.1.zip) and, at the run step only,
    OLLAMA_API_KEY — never committed, env only." — tranche instruction, SETUP.

C3: "your blast radius is tools/treadle/, treadle.toml, skills/,
    scripts/swarm_gate.py, and the pilot experiment dir; nothing shared." —
    tranche instruction, KNOWN CURRENT STATE. (CLAUDE.md and
    docs/AUDIT_BASELINES.md are additionally in radius by R7/R9.)

C4: "Full gate at the boundary anyway (the vendored tree must not break
    collection); docs_verify full; map moves in the same commits." — tranche
    instruction, KNOWN CURRENT STATE.

C5: "Commit and push every phase boundary (retry 2s/4s/8s/16s)." — tranche
    instruction.

C6: "gate baseline 0 failed at 5d9b995ce; docs_verify 3 pre-existing
    shallow-clone failures; sweep retired." — tranche instruction, KNOWN CURRENT
    STATE.

C7: "Parallel windows may be working the reservation-bound defect and the
    cycle-soak instrument (src/ and scripts/)" — do not touch those.

## Open questions (for dr-spec-change)

Q1 (BLOCKING): The zip `treadle0.4.1.zip` is not present in this container.
   `/mnt/attach` and `/mnt/user-data/working` are both empty; a filesystem-wide
   search for `*treadle*` and `*.zip` returns nothing matching. C2 makes the
   operator the supplier of this artifact, and R1/R2/R4/R5/R6 and the entire
   four-rung pilot (R11–R18) are downstream of having its source and its
   `AGENT_INSTALL.md`. Nothing in the tranche may be synthesised in its place.

Q2: Tranche directory naming. The change workflow's layout is
   `experiments/<date>-change-<slug>/`, but the instruction names
   `experiments/2026-08-23-treadle-pilot/` explicitly as the pilot's output
   path (R11, R13). Provisionally resolved in favour of the operator's explicit
   path: one directory, `experiments/2026-08-23-treadle-pilot/`, holds both the
   tranche artifacts and the pilot output. Recorded here rather than asked —
   the dominance test kills the fork (no requirement depends on the directory
   name).

Q3: The SETUP line names branch `claude/treadle-install-pilot-n8kw3e`; the
   session's designated branch is `claude/treadle-install-pilot-fqwjt5`.
   Resolved in favour of the designated branch (the session's standing
   instruction forbids pushing elsewhere); both branch off `origin/main` at
   `5d9b995ce`, which is confirmed an ancestor of HEAD. Recorded, not asked.

Q4: "its three failure modes" (R17) names a treadle taxonomy that is stated in
   the shipped documentation. Answerable from the zip once supplied; not an
   operator question.

## Amendments
(append-only; later operator messages land here as R20... or
"R2a supersedes R2", each with its verbatim quote)

### Amendment 1 — 2026-08-24, mid-tranche, after the four rungs had run

Operator, verbatim, attaching `treadle0.5.zip`:

> "Server side issue. Something you did caused a crash
> try again
> [treadle0.5.zip] Here's the updated. Install this and keep going"

R20 (artifact): "Here's the updated. Install this" — install treadle 0.5 from
   the supplied zip (sha256
   1818f7b658c1ffbb23fc7d97dacc54fbfddb790851d6489cbc83d56cb5d18741).

R21 (process): "keep going" — continue the tranche after installing.

**Recorded at capture, not interpreted: 0.5 is not a newer version of the
same artifact.** 0.4.1 shipped a Python package (`src/treadle/`, `pyproject.toml`,
`tests/`, console entry point `treadle`), a swarm board driver
(`repo-assets/swarm_gate.py`), and a config (`treadle.toml`). 0.5 ships none of
those: it is `checkers/` (four Python modules), `skills/` (twelve), `selftest.py`
and documentation, with a manual `SETUP.md` procedure. There is no `treadle`
command, no `doctor`, no `run --once`, and no board.

Consequences carried into SPEC.md rather than decided here:

- Q5: R20 does not say whether 0.5 REPLACES the committed 0.4.1 install or is
  installed beside it. 0.5 cannot replace the driver function, because it has
  no driver.
- Q6: R11-R18 (the four-rung pilot) are written against `treadle run --once`,
  which does not exist in 0.5. Those requirements were satisfied against 0.4.1
  before this amendment arrived; whether the operator wants them re-run under
  some 0.5 equivalent cannot be read off "keep going".
- Q7: the operator reports "Something you did caused a crash". No crash is
  visible from this session's side — the full gate completed 3875 passed, 0
  failed, and every treadle run exited 0. Nothing is inferred about the cause.
