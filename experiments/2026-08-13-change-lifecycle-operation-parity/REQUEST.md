# Request: lifecycle-operation parity — "The flags and operations available to the newer reason runs should be available to all configurations"

Captured: 2026-08-13 from the tranche-opening operator message (single
message; it quotes two earlier operator statements of the same date and
the typed evidence they were made against).

## Verbatim

Tranche-opening message, verbatim:

> Change tranche: lifecycle-operation parity — every operation available to
> managed reason runs (amend, continue, append, terminal finalization)
> works on runs launched from ANY configuration path, including
> `deepreason run --run-manifest`. Route through dr-change-orchestrator;
> no stops beyond the one gate below.
>
> SETUP (fresh container): git fetch origin main && git checkout -B
> claude/lifecycle-parity-amend-d59k2v origin/main; git merge-base
> --is-ancestor 6b1e23d56 HEAD || re-fetch. pip install -e .
> --break-system-packages -q; pip install pytest pytest-xdist jsonschema
> --break-system-packages -q. Use `python -m pytest`, never bare pytest.
> Read CLAUDE.md in full; load dr-drive-harness, dr-explain-to-operator.
> Read experiments/2026-08-12-live-grounded-extension-expansion/RESULTS.md
> — this tranche unblocks that run's amendment.
>
> AUTHORITY for REQUEST.md, operator verbatim (2026-08-13), with the typed
> evidence: "AMEND_NOT_AT_TERMINAL: amendment requires a run standing at a
> valid typed terminal stop (terminal authority is
> current_open_uncommitted)" / "The new generic reason run doesn't
> recognise the new config style nor does 'append'. This needs fixing
> next. The flags and operations available to the newer reason runs should
> be available to all configurations." Ledger the last sentence as a
> standing operator design law in CLAUDE.md §Operator design laws, same
> commit as the fix (the operations-parity sibling of the 2026-08-12
> all-configurations law).
>
> DIAGNOSE FROM THE RECORD FIRST (the root, not the code): open the
> grounded-extension root under that tranche's home. Enumerate its
> terminal-state records against what amendment/apply.py's terminal
> authority (current_open_uncommitted) requires — name the exact missing
> or unrecognized record. Two hypotheses to separate with the record: (a)
> the bare `run` path never WRITES the terminal-commit record the managed
> path writes at stop; (b) amend's reader does not RECOGNIZE the records
> this run's config style produced. The fix differs; the root decides.
>
> SCOPE, in order:
> (1) OPERATION INVENTORY: table every lifecycle operation the managed
>     path (application/text_runs.py TEXT_RUN_SERVICE) offers vs what a
>     manifest-launched root can actually use — amend, continue, append,
>     finalize/commit-terminal, attach_bound_evidence, anything else the
>     census finds. Each row: works / broken / never-wired, with proof.
> (2) FIX: close every gap so the operations work on manifest-launched
>     roots. For the stopped grounded root specifically: the path to
>     amendable MUST be appended typed records (a finalize/commit
>     operation the root legitimately reaches its terminal through) —
>     the committed root's existing bytes are never edited (CLAUDE.md
>     append-only law; this is the one design constraint not open).
> (3) LIVE PROOF (tokens are cheap; this is the verification): on the
>     REAL grounded-extension root — finalize it through the new typed
>     path, then `deepreason amend` admitting the six dossier documents
>     as attached evidence, then `deepreason continue` with
>     --token-budget 500000, +8 cycles, concurrency 2, the
>     OLLAMA_CLOUD_OPERATIONS.md 429/stream rules. Expected end state
>     (typed outcomes only): amendment epoch shows 6 attached source
>     records with import provenance and zero NEW violations; the
>     original epoch's 6 attached-evidence violations REMAIN as recorded
>     history — report, don't chase; continued cycles show criticism
>     engaging the admitted evidence (count citations of imported
>     sources); RESULTS.md gains a dated segment — survivors refuted
>     with the documents visible, new proposals, judge verdict counts,
>     and the residue.
>
> GATE (the one hold): if diagnosis shows reaching terminal for this root
> is impossible without editing committed bytes, STOP with the record
> evidence, priced options, one recommendation. Otherwise proceed.
>
> PRE-GRANTED (scoped, additive/widening only): surface 2 (harness.py)
> and surface 3 (replay readers) as far as writing/recognizing the
> terminal and amendment records for manifest-launched runs requires —
> same additive shape as the defended-trial wiring grants; surface 4 if a
> manifest field is needed, model and validator together. Every committed
> root replays byte-unchanged: targeted verify_root_report on a
> known-good root at validation, pasted. Qualification-digest drift:
> REPORT the cost, don't stop.
>
> TESTS: regression pair — a manifest-launched fixture run reaches a
> typed terminal and accepts amend; an interrupted one still refuses with
> AMEND_NOT_AT_TERMINAL (the refusal stays correct for genuinely open
> runs). Tests asserting the old gap flip with SPEC.md's prediction.
> GATE: ring while iterating; full gate at the boundary; docs_verify full
> (baselines per docs/AUDIT_BASELINES.md). Map moves in the same commits
> (SUB-application, SUB-amendment or its covering doc, SEAM contacts).
> Errata check: any committed doc claiming amend/continue work for all
> run types gets an entry (next free number — check the ledger tail).
> Commit and push every phase boundary (retry 2s/4s/8s/16s). Deliver
> R-by-R with pasted PROOF throughout.

Operator statements quoted inside that message, verbatim (2026-08-13):

> "The new generic reason run doesn't recognise the new config style nor
> does 'append'. This needs fixing next. The flags and operations
> available to the newer reason runs should be available to all
> configurations."

Typed evidence quoted inside that message, verbatim:

> "AMEND_NOT_AT_TERMINAL: amendment requires a run standing at a valid
> typed terminal stop (terminal authority is current_open_uncommitted)"

## Requirements

R1 (behavior): "every operation available to managed reason runs (amend,
continue, append, terminal finalization) works on runs launched from ANY
configuration path, including `deepreason run --run-manifest`."

R2 (artifact): "OPERATION INVENTORY: table every lifecycle operation the
managed path (application/text_runs.py TEXT_RUN_SERVICE) offers vs what a
manifest-launched root can actually use — amend, continue, append,
finalize/commit-terminal, attach_bound_evidence, anything else the census
finds. Each row: works / broken / never-wired, with proof."

R3 (behavior): "FIX: close every gap so the operations work on
manifest-launched roots."

R4 (behavior): "For the stopped grounded root specifically: the path to
amendable MUST be appended typed records (a finalize/commit operation the
root legitimately reaches its terminal through) — the committed root's
existing bytes are never edited."

R5 (process): "DIAGNOSE FROM THE RECORD FIRST (the root, not the code):
open the grounded-extension root under that tranche's home. Enumerate its
terminal-state records against what amendment/apply.py's terminal
authority (current_open_uncommitted) requires — name the exact missing or
unrecognized record."

R6 (process): "Two hypotheses to separate with the record: (a) the bare
`run` path never WRITES the terminal-commit record the managed path
writes at stop; (b) amend's reader does not RECOGNIZE the records this
run's config style produced. The fix differs; the root decides."

R7 (behavior): "LIVE PROOF ... on the REAL grounded-extension root —
finalize it through the new typed path, then `deepreason amend` admitting
the six dossier documents as attached evidence, then `deepreason
continue` with --token-budget 500000, +8 cycles, concurrency 2, the
OLLAMA_CLOUD_OPERATIONS.md 429/stream rules."

R8 (artifact): "Expected end state (typed outcomes only): amendment epoch
shows 6 attached source records with import provenance and zero NEW
violations; the original epoch's 6 attached-evidence violations REMAIN as
recorded history — report, don't chase; continued cycles show criticism
engaging the admitted evidence (count citations of imported sources);
RESULTS.md gains a dated segment — survivors refuted with the documents
visible, new proposals, judge verdict counts, and the residue."

R9 (artifact): "Ledger the last sentence as a standing operator design
law in CLAUDE.md §Operator design laws, same commit as the fix (the
operations-parity sibling of the 2026-08-12 all-configurations law)." The
sentence to ledger: "The flags and operations available to the newer
reason runs should be available to all configurations."

R10 (behavior): "TESTS: regression pair — a manifest-launched fixture run
reaches a typed terminal and accepts amend; an interrupted one still
refuses with AMEND_NOT_AT_TERMINAL (the refusal stays correct for
genuinely open runs). Tests asserting the old gap flip with SPEC.md's
prediction."

R11 (process): "GATE: ring while iterating; full gate at the boundary;
docs_verify full (baselines per docs/AUDIT_BASELINES.md)."

R12 (artifact): "Map moves in the same commits (SUB-application,
SUB-amendment or its covering doc, SEAM contacts)."

R13 (artifact): "Errata check: any committed doc claiming amend/continue
work for all run types gets an entry (next free number — check the ledger
tail)."

R14 (process): "Every committed root replays byte-unchanged: targeted
verify_root_report on a known-good root at validation, pasted."

R15 (process): "Qualification-digest drift: REPORT the cost, don't stop."

R16 (process): "Commit and push every phase boundary (retry
2s/4s/8s/16s). Deliver R-by-R with pasted PROOF throughout."

## Standing constraints

C1: "the committed root's existing bytes are never edited (CLAUDE.md
append-only law; this is the one design constraint not open)." — SCOPE
(2), tranche-opening message.

C2: "GATE (the one hold): if diagnosis shows reaching terminal for this
root is impossible without editing committed bytes, STOP with the record
evidence, priced options, one recommendation. Otherwise proceed." —
tranche-opening message.

C3: "PRE-GRANTED (scoped, additive/widening only): surface 2 (harness.py)
and surface 3 (replay readers) as far as writing/recognizing the terminal
and amendment records for manifest-launched runs requires — same additive
shape as the defended-trial wiring grants; surface 4 if a manifest field
is needed, model and validator together." — tranche-opening message.

C4: "Route through dr-change-orchestrator; no stops beyond the one gate
below." — tranche-opening message.

C5: "the original epoch's 6 attached-evidence violations REMAIN as
recorded history — report, don't chase" — SCOPE (3), tranche-opening
message.

C6: "Use `python -m pytest`, never bare pytest." — SETUP,
tranche-opening message.

## Map preflight (ids resolved before any design)

- `DR-SUB-application` — owns `src/deepreason/application/`,
  `src/deepreason/cli/`, `src/deepreason/runtime/`. Both the managed
  path (`text_runs.py`) and the bare `run` path (`cli/main.py`) sit
  inside this one document's `Owns:` set.
- `DR-SUB-amendment` — owns `src/deepreason/amendment/`; the reader that
  raises `AMEND_NOT_AT_TERMINAL`.
- `DR-SUB-verification` — owns `src/deepreason/invariants.py`,
  `src/deepreason/verification/`; `verify_root` and the post-commit
  report.
- `DR-SUB-manifest` — owns the RunManifest schema and validators.
  **Frozen** (INV surface 4).
- `DR-SUB-harness` — owns `harness.py` event application. **Frozen**
  (INV surface 2).
- `DR-CON-run-identity` — owns `preparation.py`,
  `application/text_runs.py`, `runtime/continuation.py`,
  `runtime/progress.py`, `amendment/*`, `ui/status.py`; the concept
  document covering exactly this tranche's subject.
- `DR-SUB-periphery` — owns `src/deepreason/evidence/` (where
  `attach_bound_evidence` lives) and `src/deepreason/ui/`.
- `DR-INV-frozen-surfaces` — read before designing; C3 pre-grants
  scoped, additive widening on surfaces 2, 3, and 4.
- Seams: `DR-SEAM-harness-x-verification`,
  `DR-SEAM-periphery-x-verification` exist. The pairs this change
  actually spans — application × run-identity, application ×
  verification, amendment × application, amendment × verification,
  amendment × periphery — are all listed `Seams-undocumented:` on the
  covering subsystem documents. **Finding, not blocker** (per
  `dr-drive-harness` §4.5): no seam document exists for the pair this
  tranche changes.

## Open questions (for dr-spec-change)

Q1: "append" is quoted as an operation name but there is no `deepreason
append` subcommand in `cli/main.py`. Which operation does it name — the
amendment's evidence append (`amend --attach`), the append-only record
write itself, or something else?

Q2: R1 says operations must work on runs launched from "ANY configuration
path". Does that include making `deepreason reason` accept the compiled
run-manifest config style (the other half of the quoted operator
sentence, "doesn't recognise the new config style"), or only making the
lifecycle operations work on roots launched by `deepreason run
--run-manifest`?

Q3: R7 names "concurrency 2, the OLLAMA_CLOUD_OPERATIONS.md 429/stream
rules" but the grounded root's manifest is frozen; whether continuation
concurrency is settable at continue time, or is fixed by the bound
manifest, is undetermined by the words.

Q4: R8 requires "zero NEW violations" for the amendment epoch. Whether
`verify_root`'s attached-evidence check can be satisfied by source
records appended after the run's reasoning events (as an amendment
necessarily does) is a property of the reader, not of the words.

## Amendments

(append-only; later operator messages land here)
