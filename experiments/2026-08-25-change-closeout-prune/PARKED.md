# PARKED — close-out prune

Found while executing the prune, deliberately not fixed here. Fixing
either item would widen this tranche past what the operator approved.

## P1 — 26 deleted directories are still cited from `docs/` prose

WHAT: the prune removed 70 directories. 26 of them are named in `docs/`
prose that survives — chiefly `docs/ERRATA.md` and
`docs/ERRATA_EXECUTOR.md`, plus three handovers,
`docs/HIDDEN_LEGACY_INVENTORY.md`,
`docs/proposals/DETERMINISTIC_GATES_PREPLAN.md`,
`docs/AUTONOMOUS_SIMULATION_MIGRATION.md`, `docs/INDEX.md`, and
`docs/harness-spec-v1.7-amendment.md`. Those citations now point at paths
that are no longer in the working tree.

This is not a census miss. The operator's Q-E1 scoped the reference grep
to `tests/`, `src/`, `scripts/`, `tools/`, `docs/map/`; `docs/` prose was
deliberately outside it, because `docs/` narrative is the target of the
separate docs census. No instrument reads these citations — `docs_verify`
checks map `check:` lines and `DR-` links, not prose paths into
`experiments/` — so both gates stayed green. The cost is that a reader
following one needs `git show 6e64330fe:<path>` rather than `ls`.

Two of the 26 sit in documents that are normative or navigational rather
than narrative, and should be handled first:

- `docs/harness-spec-v1.7-amendment.md:12` cites
  `experiments/2026-08-11-spec-drift-measurement/DRIFT_TABLE.md` as
  evidence for a spec claim. The spec series is append-only — the fix is
  a note, never an edit to the amendment's existing text.
- `docs/INDEX.md:4` and `:149` cite the same directory. `INDEX.md` is the
  navigation layer and rowed KEEP.

Full list: `proof/dangling-docs-citations.txt`.

READY-TO-SEND PROMPT:

    Route: dr-change-orchestrator.
    Goal (one): make docs/ citations of pruned experiment directories
    resolvable again, without deleting a single ERRATA entry.
    Evidence pointers:
      experiments/2026-08-25-change-closeout-prune/proof/dangling-docs-citations.txt
        -- all 26 directories with their citing files.
      The content of every pruned directory lives at 6e64330fe:
        git show 6e64330fe:experiments/<tranche>/<file>
    Approach (smallest that works): add ONE line to each citing document,
    or one shared note in docs/INDEX.md, saying that experiment tranches
    pruned on 2026-08-25 are retrievable at 6e64330fe and naming the
    prune tranche. Do NOT rewrite the citations themselves -- they are
    accurate about what happened; only the retrieval instruction is
    missing.
    THE ERRATA RULE, absolute: never delete or reword an ERRATA entry.
    Errata are append-only forever. An entry recording that a claim was
    found wrong stays true whether or not the document it cites survives.
    The spec series is append-only too: harness-spec-v1.7-amendment.md's
    existing text is not edited; if it needs anything, it is a new
    amendment, not a correction in place.
    Natural pairing: run this INSIDE the docs-prune tranche
    (experiments/2026-08-25-audit/PARKED.md P5), which already carries a
    requirement to fix docs/INDEX.md links in the same commit.
    End state: a reader hitting any of the 26 citations can retrieve the
    cited material in one command. Gate: python tools/docs_verify.py full,
    plus --links.

## P2 — the audit's park count was 60; the true count is 71

WHAT: `experiments/2026-08-25-audit` counted open park items with a regex
matching `P<n>` labels, and reported 60. The structural extraction this
tranche ran — every heading below the title starts an item — found **71**.
The 11 missed items carry non-`P` labels: `## D2a`, `## D1a`, `## Q1`,
`## D2c`, `## D2e`, `## Resolution (R25)`, and bullet-form entries.

No work was lost — stage 1 extracted all 71 before any deletion, and
proved it two ways. But the audit's own artifacts still say 60, and a
later reader comparing the registry against the audit will find a
discrepancy with no explanation on the audit's side.

READY-TO-SEND PROMPT:

    Route: dr-change-orchestrator.
    Goal (one): correct the park count in the 2026-08-25 audit's
    artifacts from 60 to 71, and record why the first count was low.
    Evidence pointers:
      experiments/2026-08-25-change-closeout-prune/proof/extraction-fidelity.txt
        -- PART 3 lists every item the label regex missed.
      experiments/OPEN_PARKS.md -- the registry, 71 items.
    Files to correct: experiments/2026-08-25-audit/AUDIT_REPORT.md (the
    three-numbers table and the closing picture), experiments-census.md
    (the counts block), LEDGER.md row CE2, PARKED.md P4's stage-1 text.
    Also worth doing, since it is the durable half: dr-audit-orchestrator
    and the census methodology should count park items STRUCTURALLY
    (every heading below the title) rather than by label, so the next
    audit does not repeat this.
    End state: the audit says 71, says the first count used a label regex,
    and the counting rule is fixed where the next audit will read it.

## P3 — Q-E1 is structurally blind to dynamically-discovered run roots

WHAT: the prune removed 53 of 113 committed run roots. One of them was
load-bearing and the census could not have known: no source file names its
path, because the test that needs it *discovers* roots at runtime
(`git ls-files experiments`) and selects by SIZE and PROPERTY.

`experiments/live_compare_2026-07-28` was restored and rowed KEEP per R5.
Only that one broke — measured, not assumed: the full gate found exactly
1 failure in 4162, and `docs_verify` exactly 1 non-baseline failure. But
the other 52 removed roots survived by luck, not by design. Any future
test whose selector shifts could hit the same wall.

The selector family in `tests/test_results_command.py` alone:
`_tracked_roots`, `_smallest_root_with`, `_smallest_root_without`,
`_smallest_root_publishing`, `_smallest_root_logging_no_embedder`. Each
picks a root by property. None names a path.

This is a defect in the CENSUS METHOD, not in the code. Q-E1 cannot be
tightened to catch it — a path grep has no path to find. It needs a fifth
question.

READY-TO-SEND PROMPT:

    Route: dr-change-orchestrator.
    Goal (one): add a fifth census question to the experiments-audit
    method so dynamically-discovered fixture roots can never again be
    pruned invisibly.
    Proposed Q-E5 (HOLDS A COMMITTED RUN ROOT?): a directory containing
    any `log.jsonl` tracked by git is KEEP by default, because the test
    suite reaches run roots by enumeration
    (`git ls-files experiments | grep '/log.jsonl$'`) and selects among
    them by size and property, never by path. Pruning such a directory
    can silently change which root a selector returns. Overriding Q-E5
    for a specific directory requires showing that no selector's result
    moves when it is removed -- which in practice means running the full
    gate, so the honest default is KEEP.
    Evidence pointers:
      experiments/2026-08-25-change-closeout-prune/proof/r5-remedy.txt
        -- the worked failure, with both roots and their sizes.
      tests/test_results_command.py lines 37-106 -- the selector family.
    Scope note: 6 directories holding 52 run roots were pruned in this
    tranche WITHOUT breaking anything. Q-E5 would have kept them. Decide
    deliberately whether to restore them under the new rule or leave them
    pruned with the measurement as the warrant -- that is an operator
    call about how much fixture surface to keep, not a defect.
    Where the rule lives: the close-out audit brief's Q-E1..Q-E4 list,
    and .claude/skills/dr-audit-orchestrator (or the audit brief template)
    so the next census inherits it.
    End state: the census method names Q-E5, and the 2026-08-25 census
    carries a note saying which of its PRUNE rows Q-E5 would have changed.
