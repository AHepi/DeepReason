# Corpus-enrichment + consistency-patrol pilot — RESULTS (living document)

Dated, honest-ledger segments per house convention. This file is updated
incrementally as each phase boundary lands; earlier segments are never
rewritten, only appended to or corrected with a new dated note.

## 2026-08-08 — Pre-registration and setup

Frozen `prereg.yaml` and `PARKED.md` committed before any Phase 1/2/3
call (`b4859d48`). One deviation from the task's own instructions was
found and recorded before spending any budget on it: **the "dual-mode"
opt-in (`conjecturer.turn.v7`) the task asked to switch on for Phase 1
does not work for any live run today.** `ContractVersionPolicyV3`
accepts the label, but the code that would grant a v7 manifest the
authority to actually validate (`_compile_contract_schema_repair_policy`,
`src/deepreason/run_manifest.py:2473-2545`) hardcodes that authority for
`conjecturer.turn.v6` only — a manifest asking for v7 is refused with a
typed error, `V6_BEHAVIORAL_REPAIR_GRANT_REQUIRED`, before any run can
even start. Confirmed by direct construction, not assumed. A second,
independent gap was found alongside it: the `encoder` role's own dispatch
function (`rules/encoding.py::draft_encoded_commitment`) has zero
callers anywhere in `src/` — it would not fire even if v7 worked. Both
are parked as **P-CEPP-1** (`PARKED.md`) rather than fixed — this
tranche's scope keeps `src/`/`tests/`/`tools/` byte-untouched. Phase 1
therefore runs on the harness's current default (v6); **zero
candidate-checker commitments across every Phase 1 root is the
EXPECTED, reported outcome, not a live-run miss.**

A second correction, made before launch: the task referred to an
"encoder seat," but `seat_bindings.py`'s `GROUP_ROLES` shows `"encoder"`
is a ROLE, not a seat GROUP — the only CLI-addressable group reaching it
is `--seat coder=PATH` (which also covers `property_designer`). The
prereg and ladder scripts were corrected to use `coder` before any run,
recorded in commit `2aa317d1`.

**Pre-enrichment Phase 3 baseline**, captured before Phase 1 could add
any roots (`0ad1cefb`): 48 committed roots, `attack_edge_density =
0.013354` (sum of attack edges / sum of nodes across the corpus),
`mean_cycle_count = 6.212` (over the 33/48 roots whose `run-status.json`
carries a `cycle` field — the rest predate that field). 11/48 roots
predate the RunManifest v6 schema and are unopenable by any script using
`Harness(root, read_only=True)` — same treatment O1's own `overlay_common
.open_root` already gives them (confirmed: they error the same way in a
byte-for-byte comparison against O1's own committed
`overlay_results.jsonl`). A secondary methodology note: a fresh
`run_all_overlays.py` re-run is **not byte-reproducible** against O1's
committed file — 37/48 rows differ, but only in JSON list ORDER (Python's
hash-randomized `set()` iteration order across separate processes),
never in content. Confirmed by hand on one root: identical counts, edges,
and SCC membership once compared as sets rather than as raw list order.
Comparisons in this pilot are always done on canonicalized summaries,
never raw diffs, for exactly this reason.

**Phase 2 sizing.** A dry run of `phase2_patrol.py` against the
pre-enrichment corpus (49 roots — Phase 1's first run had already landed
one root by the time this ran) found 6426 candidate pairs (6065
historical, 361 already-enriched), with 938 accepted artifacts excluded
as unaddressed (no `state.addr` problem entry, so no locality signal).
11 roots were unopenable, matching Phase 3's own count exactly. The
patrol mechanism was smoke-tested on one real pair before committing to
the full run: a genuine-sounding candidate contradiction was found on
the very first pair tried (Rule 90 width-8/10 pass/fail claims from two
different problems in the same root) — auth, endpoint, and JSON parsing
all confirmed working end to end.

## 2026-08-08 — Phase 1 failure ledger (budget: 10)

The cloud container has rolled back or reaped detached background
processes **three times** in this tranche's Phase 1 window so far, each
inside a 15-30 minute span — a documented risk (CLAUDE.md's
"Environment" section) that turned out to recur far more often than a
single-incident read would suggest. Recovery method each time: read the
record before touching anything (`run-status.json`, `progress.jsonl`,
`log.jsonl`'s tail, `verify_root`, and — critically — whether the dead
process's PID is actually gone via `ps -p`) before deciding whether a
root is salvageable or must be discarded.

- **Failure #1** — `base-q01`'s `continue --budget cycles=2` step was
  killed mid-flight. Diagnosis: `run-status.json`/`progress.jsonl` were
  stale (`state: "running"`), but `log.jsonl` (1369 events) ended in the
  standard clean-stop signature (`lifecycle_stopped` then
  `terminal_committed`, seq 1367-1368, timestamped 22:21:05Z — exactly
  matching the requested 10+2=12 cycle budget). `verify_root`:
  replay_valid=true, before AND after removing six stale lock files
  whose owning PID (26937) was confirmed dead. **Outcome: root is real
  and complete** — committed as-is (`9e05622a`), run-status.json's
  staleness left uncorrected (never hand-edited a cache file to make it
  agree with my own reading; the log is what I cite as evidence, not my
  patched version of the summary).
- **Failure #2** — the first retry of `base-q13` was killed at cycle 3.
  Diagnosis: `verify_root` came back **replay_valid=false** (6
  foreign-criticism violations — a genuinely invalid mid-state, not a
  stale-cache illusion), and the log's tail sat inside an active
  `contract_decomposition_activated`/`work_transition` sequence — the
  EXACT shape CLAUDE.md already names as a known crash risk for
  `continue` (S6's P3: "continue can crash resuming a mid-decomposition
  stop"). Given that specific documented risk plus this tranche's own
  rule against touching `src/` to fix anything, the root was confirmed
  never-committed (`git log --all`: no history) and discarded rather
  than resumed.
- **Failure #3** — the SECOND retry of `base-q13` was also killed, at
  cycle 3, again `replay_valid=false`, again never committed, again
  discarded. Same diagnosis, same disposition.

**Root cause identified after failure #3, not just patched around**: a
raw OS-level detached process (`setsid nohup ... & disown`) is not
surviving in this container between tool-call turns, independent of
whether any run-level event triggers it — the pattern held even with no
visible container-rollback signal in between. Strategy changed
accordingly: Phase 1's remaining questions now run one at a time as a
harness-TRACKED background Bash call (`run_in_background: true`) inside
this session, rather than a raw detached shell driver. This is watched
directly by the tool layer (a completion notification arrives
automatically) instead of relying on a Unix process surviving on its
own, which is the mechanism that kept failing. `base-q13` is retrying
under this new mechanism now; further progress is appended below.

## 2026-08-09 — first non-crash finding: budget_exhausted stops can land replay_valid=false

`hard-h01`'s first `reason` call completed cleanly (`reason_rc=0`, state
`completed`, `stop_reason: budget_exhausted`, no process interruption
involved at all) — but `verify_root` still returned `replay_valid:
false`, citing two accepted artifacts with `foreign-criticism: 0 foreign
schools; policy requires 1`. Checked whether this was somehow caused by
this tranche's own coder-seat binding before treating it as a general
harness fact: `llm_calls_by_role` on this root shows ONLY
`argumentative_critic`/`conjecturer` on `glm-5.2` — `gemma4:31b` never
fired (consistent with the coder/encoder dead-seat finding), so the
seat binding is not the cause. This matches a pattern already named in
CLAUDE.md/S6's own RESULTS.md ("foreign-criticism verify violations
...  at natural stop points") for a different root cause (there,
gemma4:31b-as-conjecturer outpacing the critic) — here the same
SYMPTOM shows up for the mundane reason CLAUDE.md's own Live-runs
section predicts: a budget ceiling can be hit before every accepted
claim has accumulated its required cross-school criticism. This is not
evidence corruption and not a crash; it is the intended trigger for the
prereg's own resume policy (`continue --budget cycles=2` on any
`budget_exhausted`/`converged` stop) — applied here exactly as
pre-registered, not as an improvised workaround.

**Update 2026-08-09**: by hard2-h2-15 (the 8th of 10 questions), 5 of the
8 completed first-`reason`-call stops hit this same `replay_valid=false`
foreign-criticism gap (base-q13, hard-h05, hard-h10 stayed clean on the
first stop; hard-h01, hard-h15, hard2-h2-01, hard2-h2-08, hard2-h2-15 did
not). This is the NORM for this cycles=10/token-budget=180000
configuration, not an edge case — every instance closed cleanly with one
`continue --budget cycles=2` top-up, consistent with the prereg's own
resume policy, applied identically each time.

## 2026-08-08 — Phase 1 progress (running table, updated per root)

| run id | question tier | status | cycles | accepted | candidate_checker_count | notes |
|---|---|---|---|---|---|---|
| base-q01 | base | committed | 12 (10+2 continue) | 110/113 | 0 (expected, P-CEPP-1) | recovered from failure #1, see above |
| base-q13 | base | committed | 10 | 93/94 | 0 (expected) | 3rd attempt succeeded under tracked-background strategy (task beb9axlw2) |
| hard-h01 | hard | committed | 12 (10+2 continue) | 95/97 | 0 (expected) | continue closed the foreign-criticism gap, see note above |
| hard-h05 | hard | committed | 10 | 91/91 | 0 (expected) | clean on first stop |
| hard-h10 | hard | committed | 10 | 83/85 | 0 (expected) | clean on first stop |
| hard-h15 | hard | committed | 12 (10+2 continue) | 99/100 | 0 (expected) | second foreign-criticism-gap case, closed by continue same as hard-h01 |
| hard2-h2-01 | hard2 | committed | 12 (10+2 continue) | 95/95 | 0 (expected) | third foreign-criticism gap case, closed by continue |
| hard2-h2-08 | hard2 | committed | 12 (10+2 continue) | 100/100 | 0 (expected) | fourth foreign-criticism gap case, closed by continue |
| hard2-h2-15 | hard2 | committed | 12 (10+2 continue) | 115/116 | 0 (expected) | fifth foreign-criticism gap case, closed by continue |
| hard2-h2-22 | hard2 | committed | 12 (10+2 continue) | 93/94 | 0 (expected) | sixth foreign-criticism gap case (final question), closed by continue |

**Phase 1 complete: 10/10 questions committed.** All zero on
`candidate_checker_commitment_count` and on `encoder_calls`/
`property_designer_calls` (P-CEPP-1, expected throughout). Failure
ledger: 3 spent (container/process deaths; see above). 6 of 10 first
stops needed one `continue --budget cycles=2` top-up for a
foreign-criticism gap; all 6 closed cleanly on the first try, 0 needed a
second.
