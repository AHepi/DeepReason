# Request: one discoverable way to retrieve run results — `deepreason results`
Captured: 2026-08-13 from the operator's single tranche-opening message
(this window, first message), which itself quotes an operator statement
dated 2026-08-13.

## Map preflight (resolved before any phase)

- `DR-SUB-application` — owns `src/deepreason/cli/`, `src/deepreason/application/`,
  `src/deepreason/runtime/`. The CLI verb surface (`build_parser`, `_main`,
  `_ROOT_ADMISSION_COMMANDS`, `_admit_v6_root`) and every run-root control file
  (`progress.jsonl`, `run-status.json`, `run-result.json`,
  `REPLAY_VALIDATION.json`) live here. **There is no `SUB-cli.md`; the covering
  document for the CLI is `SUB-application.md`.**
- `DR-SUB-periphery` — owns `src/deepreason/mcp_server.py` (the MCP tool surface,
  relevant only if R14's optional MCP tool is taken).
- `DR-SUB-verification` — owns `verify_root` / replay validation (**frozen**;
  read-only use only).
- `DR-CON-run-identity` — deterministic run ids, roots on disk, amendment epochs.
- `DR-INV-frozen-surfaces` — read before designing. The five frozen surfaces are
  `capabilities/state.py`, `harness.py`, replay-validation record formats
  (`invariants.py`, `verification/`), manifest schemas + validators
  (`run_manifest.py`), qualification subject digests (`qualification.py`), plus
  frozen-adjacent `route_fingerprint`. None is expected to be touched: this
  tranche adds a READER and an additive CLI verb.
- Seam documents: none exists for `application x verification` or
  `application x run-identity` (both listed `Seams-undocumented` in
  `SUB-application.md`). That absence is a finding to note in SPEC.md, not a
  blocker.

## Verbatim

Operator message (this window, opening message), quoted in full:

> Change tranche: one discoverable way to retrieve run results —
> `deepreason results` — so sessions stop guessing at flags that don't
> exist. Route through dr-change-orchestrator; the workflow's own stop
> conditions apply, nothing else stops.
>
> SETUP (fresh container): git fetch origin main && git checkout -B
> claude/results-retrieval-surface-f72wqm origin/main. pip install -e .
> --break-system-packages -q; pip install pytest pytest-xdist jsonschema
> --break-system-packages -q. Use `python -m pytest`, never bare pytest.
> Read CLAUDE.md in full; load dr-drive-harness, dr-explain-to-operator.
>
> AUTHORITY for REQUEST.md, operator verbatim (2026-08-13): "When
> retrieving run results, Opus 5 keeps grepping for flags that dont
> exist." Root cause to fix: the result-retrieval surface is scattered
> across root files (findings.json, run-status.json,
> REPLAY_VALIDATION.json, progress.jsonl, verify_root) with no CLI verb
> or --help path naming it, so every session reinvents an interface and
> hallucinates flags.
>
> PHASE 1 — CENSUS FIRST (the fix may partly exist): table every current
> way to read a run's outcome — every cli/main.py subcommand and flag
> that touches results/status (paste the argparse census), every
> root-file artifact and its schema, the MCP tools that poll/report. If
> an existing command already does part of this, the fix is surfacing and
> completing it, not duplicating it (one implementation, per the map's
> own drift rule).
>
> PHASE 2 — THE COMMAND: `deepreason results <root-or-home>` emitting the
> typed outcome, nothing model-authored:
> - run id, state, stop_reason, cycles completed, token spend vs budget;
> - artifact counts (accepted / refuted / suspended), final survivor
>   count, frontier id;
> - defended-trial verdict counts and judge-call count when adjudication
>   ran;
> - verify_root verdict (violations count, families) — read the stored
>   record, do not re-derive unless --verify is passed;
> - amendment epochs present, and whether the root stands at a valid
>   typed terminal (the amend-readiness fact sessions keep needing).
> Two output modes: human-readable (glossed labels) and --json (stable
> keys, documented). Unknown/absent facts print as typed absences, never
> omitted. Errors route through the error catalog (new entries for e.g.
> RESULTS_ROOT_NOT_FOUND), so `deepreason explain-error` covers them.
>
> PHASE 3 — DISCOVERABILITY (the actual defect): the top-level
> `deepreason --help` names the command with one line ("read a run's
> typed results"); dr-drive-harness's CLI-lifecycle section gains the
> retrieval row in the SAME commit; FORM DR-1/docs mentions regenerate if
> touched. Acceptance test for the defect itself: a session given only
> `deepreason --help` output can name the command that retrieves results
> — pin with a test asserting the help text contains the verb and its
> one-line description.
>
> RAILS: read-only against roots — the command NEVER writes into a run
> root (pin with a test: run it against a committed root fixture, assert
> tree unchanged). Frozen surfaces: none expected (readers only, additive
> CLI); the workflow's stop condition covers surprises. Wheel smokes:
> console entry points unchanged; if the MCP surface gains a results
> tool (worth doing so model callers stop grepping too — window's call,
> record either way), ALL FOUR pin locations in the SAME commit +
> schema sha recomputed. Old roots replay byte-unchanged.
>
> GATE: ring while iterating; full gate at the boundary; docs_verify full
> (baselines per docs/AUDIT_BASELINES.md). Map moves in the same commits
> (SUB-cli covering doc; SUB-application if the reader lives there).
> Errata: if any committed document instructs sessions to retrieve
> results via a flag or command that does not exist, that is an entry
> (next free number — check the ledger tail). Commit and push every phase
> boundary (retry 2s/4s/8s/16s). Deliver R-by-R with pasted PROOF,
> including one demonstration run of `deepreason results` against the
> grounded-extension root with its output pasted.

## Requirements

R1 (behavior): "one discoverable way to retrieve run results —
`deepreason results` — so sessions stop guessing at flags that don't exist."

R2 (process): "Route through dr-change-orchestrator; the workflow's own stop
conditions apply, nothing else stops."

R3 (process, CENSUS): "table every current way to read a run's outcome — every
cli/main.py subcommand and flag that touches results/status (paste the argparse
census), every root-file artifact and its schema, the MCP tools that
poll/report."

R4 (process, CENSUS): "If an existing command already does part of this, the fix
is surfacing and completing it, not duplicating it (one implementation, per the
map's own drift rule)."

R5 (behavior): "`deepreason results <root-or-home>` emitting the typed outcome,
nothing model-authored".

R6 (behavior): "run id, state, stop_reason, cycles completed, token spend vs
budget".

R7 (behavior): "artifact counts (accepted / refuted / suspended), final survivor
count, frontier id".

R8 (behavior): "defended-trial verdict counts and judge-call count when
adjudication ran".

R9 (behavior): "verify_root verdict (violations count, families) — read the
stored record, do not re-derive unless --verify is passed".

R10 (behavior): "amendment epochs present, and whether the root stands at a
valid typed terminal (the amend-readiness fact sessions keep needing)."

R11 (behavior): "Two output modes: human-readable (glossed labels) and --json
(stable keys, documented)."

R12 (behavior): "Unknown/absent facts print as typed absences, never omitted."

R13 (behavior): "Errors route through the error catalog (new entries for e.g.
RESULTS_ROOT_NOT_FOUND), so `deepreason explain-error` covers them."

R14 (behavior): "the top-level `deepreason --help` names the command with one
line ("read a run's typed results")".

R15 (artifact): "dr-drive-harness's CLI-lifecycle section gains the retrieval row
in the SAME commit; FORM DR-1/docs mentions regenerate if touched."

R16 (behavior): "Acceptance test for the defect itself: a session given only
`deepreason --help` output can name the command that retrieves results — pin
with a test asserting the help text contains the verb and its one-line
description."

R17 (behavior): "read-only against roots — the command NEVER writes into a run
root (pin with a test: run it against a committed root fixture, assert tree
unchanged)."

R18 (process): "Frozen surfaces: none expected (readers only, additive CLI); the
workflow's stop condition covers surprises."

R19 (process): "Wheel smokes: console entry points unchanged; if the MCP surface
gains a results tool (worth doing so model callers stop grepping too — window's
call, record either way), ALL FOUR pin locations in the SAME commit + schema sha
recomputed."

R20 (behavior): "Old roots replay byte-unchanged."

R21 (process, GATE): "ring while iterating; full gate at the boundary;
docs_verify full (baselines per docs/AUDIT_BASELINES.md)."

R22 (artifact): "Map moves in the same commits (SUB-cli covering doc;
SUB-application if the reader lives there)."

R23 (artifact): "Errata: if any committed document instructs sessions to
retrieve results via a flag or command that does not exist, that is an entry
(next free number — check the ledger tail)."

R24 (process): "Commit and push every phase boundary (retry 2s/4s/8s/16s)."

R25 (process): "Deliver R-by-R with pasted PROOF, including one demonstration
run of `deepreason results` against the grounded-extension root with its output
pasted."

## Standing constraints

C1: "When retrieving run results, Opus 5 keeps grepping for flags that dont
exist." — operator verbatim, 2026-08-13, quoted in the tranche message as the
AUTHORITY for this REQUEST.md. This is the defect the change must remove.

C2: "the result-retrieval surface is scattered across root files (findings.json,
run-status.json, REPLAY_VALIDATION.json, progress.jsonl, verify_root) with no
CLI verb or --help path naming it, so every session reinvents an interface and
hallucinates flags." — the operator's stated root cause, in the tranche message.

C3: "Use `python -m pytest`, never bare pytest." — SETUP section of the tranche
message.

C4: "Read CLAUDE.md in full; load dr-drive-harness, dr-explain-to-operator." —
SETUP section of the tranche message.

C5: "the workflow's own stop conditions apply, nothing else stops." — opening
paragraph of the tranche message.

C6 (standing, CLAUDE.md, not restated by the operator here but binding on this
tranche): all configurations should be allowed; formalism is an option never an
obligation; tokens are cheap and the agent is not. Recorded here because a
reader-only command must not become a new denial surface.

## Open questions (for dr-spec-change)

Q1: `deepreason results <root-or-home>` — the argument is stated as
"root-or-home". What resolution rule applies when a HOME (not a root) is given
and it contains more than one run root? (Newest? All? Refuse typed?) The words
do not say.

Q2: "final survivor count, frontier id" (R7) — which typed record supplies
these, and what is emitted when a run stopped before any frontier existed? The
words assume both exist.

Q3: "defended-trial verdict counts and judge-call count when adjudication ran"
(R8) — what is the typed source, and what is the typed absence when adjudication
did not run?

Q4: R19 leaves the MCP results tool explicitly to this window ("window's call,
record either way"). Decide and record.

Q5: R22 names "SUB-cli covering doc" — no `SUB-cli.md` exists; the CLI is owned
by `SUB-application.md` (verified in the map preflight above). The requirement's
own alternative ("SUB-application if the reader lives there") appears to be the
live branch; confirm in SPEC.md.

Q6: R25 names "the grounded-extension root" — which committed root is that, and
does it satisfy the V6 admission gate the new verb will pass through?

## Amendments

(none yet)
