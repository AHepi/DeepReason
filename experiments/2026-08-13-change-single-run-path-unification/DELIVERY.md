# Delivered: one run path — "Get rid of the old one"

Branch: `claude/single-run-path-unification-bhn2ob` (pushed, tree clean).
Base: `origin/main` `fc0d75473`. Eleven commits.

## What changed

DeepReason had two ways to start a reasoning run. `deepreason reason`
went through the managed service — the code that writes the progress
stream, the stop record, the terminal commitment, and everything `amend`,
`continue`, `cancel` and `result` later read. `deepreason run
--run-manifest`, the one path that could express a full custom
configuration, went somewhere else entirely: it called the scheduler
directly and printed. Yesterday's tranche made both call one shared
terminalization. This one removes the second path.

`TextRunApplicationService` gains `start_manifest_run`
(`src/deepreason/application/text_runs.py`): a caller holding a compiled
manifest and a root passes them in, and the method resolves the manifest
(object or path), resolves the workload from the root read-only,
translates an absent token ceiling into the intent vocabulary's
`"unlimited"`, and calls `start`. It validates nothing of its own — which
is precisely why it cannot refuse a configuration for its shape. Whatever
`start` accepts, this accepts.

`deepreason run --run-manifest` keeps its exact parser surface — same
flags, same defaults, same synchronous blocking — and becomes a rendering
shell (`_dispatch_managed_run` in `src/deepreason/cli/main.py`). It
preflights and dry-runs as before, then hands off to the service and
prints the survivors, frontier and theory from the published terminal.
`_execute_bound_run` is deleted, 121 lines of it, along with
`attach_bound_evidence_once`, the bare-path retrofit whose only caller it
was. Production code net: **97 insertions, 166 deletions**, across two
files.

The proof that the configuration space did not narrow is the operator's
own: the acceptance test imports
`experiments/2026-08-12-live-grounded-extension-expansion/build_manifest.py`
from its committed path, compiles `run-config.yaml` to manifest
`8e22d0431fd2b98d…` — the live grounded run's own digest — and drives
that exact root through the new door to a published terminal.

## The lifecycle delta — what every manifest-launched root now gains (R11)

This is the purpose of the tranche, not a side effect, so it is stated
rather than buried.

| Gains | Was it there before? |
|---|---|
| per-cycle progress events, with token spend and status counts | no — the bare path emitted one `loaded` event and nothing more |
| mid-run cancellation at the completed-cycle boundary | no — nothing checked `cancel.requested` between cycles |
| dossier attachment at seed, through `_worker`'s own `attach_bound_evidence` | it had a separate retrofit; now it is the same code every run uses |
| a typed operational-failure terminal when the engine dies | no — a dying scheduler printed and exited 1, publishing nothing |
| `run-result.json` recovery through `result()` | no |
| `run_result_exit_code` at the process boundary: 0 / 3 / 4 / 5 | no — 0 for any completion, 1 for everything else |
| stop record, terminal commitment, `amend`, `continue` | yesterday's tranche gave it these; today they are unconditional |

**One behavior narrows, and it is not hidden.** A second `deepreason run`
on a root that already has `progress.jsonl` or `run-result.json` now
refuses `RUN_ALREADY_STARTED: choose a fresh root or continue_run`,
because that is the managed path's rule for every configuration
(`DR-CON-run-identity`: "A root that has already run may never be started
again"). The bare path used to re-enter such a root silently. The
successor operation is `deepreason continue` — which this same
unification makes available to these roots. Recorded as assumption A5;
the operator may reverse it.

**Two stdout lines are gone**, having lost their source: the scheduler's
`[note]` diagnostics (never persisted anywhere) and the raw
`meter.snapshot()` JSON (the meter is built inside `run_scheduler` and
the worker discards it). Their information survives as `accounting` in
`run-result.json` and `token_spend` in `progress.jsonl`. No committed
test or ladder asserts either line; census in SPEC.md.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "TextRunApplicationService gains a manifest-direct entry" | done | `c9a476130`; VALIDATION S1.1 — parametrized over manifest object and path |
| R2 | "the FULL configuration space… No narrowing" | done | `c9a476130`; VALIDATION S1.2 — judge ensemble + `route_bound` schools + `criticism_policy` reach a terminal; source-inspection map check, mutation-proved |
| R3 | "that exact config must enter through the new door" | done | `c9a476130`; VALIDATION S1.3 — `build_manifest.py` imported from its committed path, digest `8e22d0431fd2b98d…` asserted |
| R4 | "keeps its exact CLI surface but becomes a thin wrapper" | done-with-assumption A2 | `f98075bf2`; VALIDATION S2.1 — full parser action table pinned |
| R5 | "Preserve the rc exit-code contract… regression-pin both" | done-with-assumption A3 | `f98075bf2`; VALIDATION S2.2 — `completed→0`, `failed→4`, refusal `→1` |
| R6 | "Ladders and scripts keep working unmodified" | done | VALIDATION S2.3 — no `.sh` in the diff |
| R7 | "remove the parallel scheduler-only dispatch… and the bare-path lifecycle retrofit" | done | `f98075bf2`; VALIDATION S3.1 + S3.2 — both `_execute_bound_run` and `attach_bound_evidence_once` gone |
| R8 | "Census every deleted symbol with reference proof" | done | `proof/dead-census.txt` — three scans, per-symbol verdict |
| R9 | "every test… MIGRATES… a deleted test is a defect" | done | VALIDATION S3.3 — counts 11/23/18 unchanged, 129 passed, two strengthened |
| R10 | "same manifest, same run id (fixture proof)" | done | `0117ab368`; VALIDATION S4.1 |
| R11 | "state it in DELIVERY.md, don't hide it" | done | the delta table above |
| R12 | "Old committed roots replay byte-unchanged" | done-with-assumption A6 | `377603c19`; `proof/replay.txt` — `verify_root` `[]` before and after on a 12 991-event root |
| R13 | "MCP start_run and the qualification battery… untouched" | done | VALIDATION S4.4 — empty diff |
| R14 | "FROZEN SURFACES: none are expected" | done | frozen-surface diff EMPTY; `blast_radius` `CLEAR` at spec time and every commit; no stop triggered |
| R15 | "ring while iterating; full gate at the boundary; docs_verify full" | done | full gate 1 failed (baseline) / 3562 passed; docs_verify full 3 failed (baseline) |
| R16 | "Map moves in the same commits" | done-with-deviation | `f98075bf2` carries the code AND both map documents. The deviation: `SEAM-application-x-cli` was NOT created, because `SUB-application.md` owns both `application/` and `cli/` — a seam joins two documents, and one document owns both sides. Recorded in REQUEST.md's map preflight and SPEC.md S5.3 |
| R17 | "console entry points unchanged, so pins should not move" | done | `scripts/` diff empty, wheel smoke rc=0 |
| R18 | "any committed document describing the two-path split… gets an entry" | done | `0117ab368` — `docs/ERRATA.md` **E26**, plus CLAUDE.md's mechanism sentence in the same commit |
| R19 | "Commit and push every phase boundary" | done | eleven pushed commits |
| R20 | "Deliver R-by-R with pasted PROOF… one-line census" | done | this table; census line below |
| **Amendment 1** | "The token steering controller that runs through config. Are you wiring that up as well…?" / "Is this operating on the dynamic token allocation system as well?" | answered, and proved | `f98075bf2` — `test_the_door_carries_the_token_steering_authority`. Classified as questions, not new requirements; the operator may reclassify, which would make them R21 |

None deferred. None not-done.

## Answer to Amendment 1, since it is the question most likely to recur

The token-steering controller is `referee.py`'s `run_config_referee`,
whose role prompt names its target as "the harness's dynamic
token-steering configuration". It fires from
`Scheduler._maybe_config_referee`, gated on exactly three things:
manifest schema 6, `config_referee.enabled`, and the cycle cadence. **No
launch path appears in that gate**, and none ever did — both the deleted
dispatch and the surviving one call
`run_scheduler(harness, config_from_run_manifest(manifest), …)`. The same
holds for the `research` allowance and the `simulation` policy, which
travel in the same `InquiryCapabilityPolicyV1`.

So custom configurations got their steering before this tranche, provided
the manifest enabled it (`DEEPREASON_CONFIG_REFEREE=<cadence>`; it
defaults to absent). What this tranche changes is the record around it:
the referee writes advice onto the log, and until today a
`run --run-manifest` root reached no terminal, so `result`, `continue`
and `amend` could not read what it wrote. The new test drives a manifest
with the referee **enabled** through the door and asserts the scheduler
receives it byte-identically, `research` and `simulation` intact, an
absent `--token-budget` still unbounded, the cycle count unchanged.
Mutation-proved: a door that strips `config_referee` fails it.

## Assumptions the operator may override

- **A1** The door takes a precompiled manifest — object or path — not a
  run-config YAML. Compiling YAML needs policy arguments only the caller
  holds.
- **A2** "Exact CLI surface" = verb, flags, defaults, blocking, exit
  contract. Two stdout lines dropped (above).
- **A3** Terminal outcomes exit through `run_result_exit_code`;
  pre-terminal refusals keep exiting `1`. `completed → 0` under both old
  and new, so no ladder can observe the change.
- **A4** The acceptance fixture is `build_manifest.build(root)` under a
  tmp `DEEPREASON_HOME`.
- **A5** A second `run` on an already-started root now refuses
  `RUN_ALREADY_STARTED` (above).
- **A6** R12's "targeted" = `verify_root` on the grounded root plus
  `verify_root_report` on two others, not the 42-root sweep — justified
  because no reader changed.
- **A7** `workload_spec_for_root` opens a read-only harness only when the
  root already carries a `log.jsonl`.

Two budget revisions are also on the record, both measured rather than
guessed: the ceiling moved 400 → 700 → 900 as the test file came in
heavier than estimated and Amendment 1's test was added. Production code
came in UNDER estimate at 97 insertions against 110; the whole overshoot
is test and documentation weight. The cheapest cut, if the operator wants
one, is Amendment 1's ~110-line test — the one line item they alone
should decide about.

## Map delta

changed: `docs/map/SUB-application.md`, `docs/map/CON-run-identity.md`
created: none — and deliberately so. `SEAM-application-x-cli.md` was not
written because `SUB-application.md` owns both sides; writing it would
break `SCHEMA.md`'s ID grammar and leave a reference `--links` cannot
resolve.

new checks: 3, each mutation-proved before being written down. Two of
them are NEGATIONS — `! grep -q "run_scheduler" src/deepreason/cli/main.py`
— replacing checks that asserted the CLI *calls* the terminalization. The
old form could not survive deleting the caller; the new form fails if a
second run path ever comes back. The third asserts, by source inspection,
that `start_manifest_run` names none of `judge` / `school` / `criticism` /
`roles`.

left stale: none. `docs_verify --stale` reports 0 documents. Both touched
documents kept their `Verified-at:` stamps although all 44 of their checks
were re-run and pass — a stale stamp is honest, a false one is not, and
validation may not edit the files it validates. Parked as P2.

## Errata

**E26** — added this tranche, in the same commit as the change it
describes. It records the two committed statements that describe
`terminalize_text_run` as the sequence "both paths" call (CLAUDE.md's
operations-parity law, and `CON-run-identity.md`'s row naming
`cli.main._execute_bound_run`). Neither was false when written; both
describe two launch paths where one now exists. What stands unchanged is
the LAW — operations available to every configuration — and only its
stated mechanism moved, from parity-by-agreement to
parity-by-construction.

## Parked (not done, not promised)

**P1** — two `docs_verify --coverage` findings predating this tranche
(`SEAM-schools-x-scratch.md` does not name `informal/trial.py` as an
enforcement site; 16 seams carry no `Sweep:` header). Neither names a
document this tranche touched. Ready-to-send prompt in `PARKED.md`.

**P2** — `Verified-at:` stamps are not advancing on re-verified map
documents. `SUB-application.md` has read `98a5bc8f` across at least three
tranches that each re-ran its checks. Ready-to-send prompt in `PARKED.md`,
and it deliberately forbids bulk-advancing stamps, which would be the
false-stamp failure `SCHEMA.md` names.

**recommended next: P2.** It is the one with a compounding cost: every
tranche that leaves a stamp behind makes `--stale` less able to tell the
next reader which documents are worth re-reading, and the map's whole
authentication story rests on that signal. P1 is real but static — two
findings that have sat unchanged and will keep sitting unchanged.

---

**Census: paths before = 2, paths after = 1, operations reachable from
it = all.**
