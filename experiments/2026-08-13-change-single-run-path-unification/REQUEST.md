# Request: one run path — "Get rid of the old one"

Captured: 2026-08-13 from the tranche-opening operator message (single
message; it quotes an earlier operator statement of the same date as its
AUTHORITY, and cites the standing law ledgered by the immediately
preceding tranche). A second operator message later the same day answered
this tranche's own opening gate.

## Verbatim

### Source 1 — the AUTHORITY quoted inside the tranche-opening message

Operator, 2026-08-13, quoted verbatim by the tranche prompt under the
heading "AUTHORITY for REQUEST.md, operator verbatim (2026-08-13)":

> Why not retrofit the newer reason path? Get rid of the old one. The new
> one has a lot of machinery that needs to work every run.

### Source 2 — the tranche-opening message, verbatim and in full

> Change tranche: one run path — the managed reason service runs every
> configuration, the bare dispatch is deleted. Parity by construction.
> Route through dr-change-orchestrator; the workflow's own stop conditions
> apply, nothing else stops.
>
> SETUP (fresh container): git fetch origin main && git checkout -B
> claude/single-run-path-unification-y83rdk origin/main. pip install -e .
> --break-system-packages -q; pip install pytest pytest-xdist jsonschema
> --break-system-packages -q. Use `python -m pytest`, never bare pytest.
> Read CLAUDE.md in full; load dr-drive-harness, dr-explain-to-operator.
> GATE before any work: grep -q terminalize_text_run
> src/deepreason/application/text_runs.py || report "lifecycle-parity
> tranche not yet on main" and hold — this tranche builds on its shared
> terminalization and supersedes its bare-path retrofit.
>
> AUTHORITY for REQUEST.md, operator verbatim (2026-08-13): "Why not
> retrofit the newer reason path? Get rid of the old one. The new one has
> a lot of machinery that needs to work every run." Companion standing law
> (ledgered by the lifecycle tranche): the flags and operations available
> to the newer reason runs are available to all configurations. This
> tranche is that law's structural enforcement: one path means nothing can
> diverge.
>
> SCOPE, in order:
> S1 WIDEN THE DOOR: TextRunApplicationService gains a manifest-direct
>    entry — accept a precompiled RunManifest (and/or a run-config file
>    compiled via compile_run_manifest) covering the FULL configuration
>    space the all-configs law admits: judge role ensembles, school-routed
>    conjecture/criticism, criticism_policy, everything build_manifest.py
>    had to hand-feed. No narrowing: any manifest the compiler emits, the
>    service runs. The grounded run's committed run-config.yaml +
>    build_manifest.py (experiments/2026-08-12-live-grounded-extension-
>    expansion/) is the acceptance fixture: that exact config must enter
>    through the new door.
> S2 ALIAS THE VERB: `deepreason run --run-manifest` keeps its exact CLI
>    surface but becomes a thin wrapper that routes into the managed
>    service. Preserve the rc exit-code contract
>    (application/models.py run_result_exit_code) and flag behavior —
>    regression-pin both. Ladders and scripts keep working unmodified.
> S3 DELETE THE OLD ROAD: remove the parallel scheduler-only dispatch in
>    cli/main.py (_execute_bound_run's direct implementation) and the
>    bare-path lifecycle retrofit the lifecycle tranche added to it —
>    that code is superseded by this unification, which is why it goes,
>    not because it was wrong. Census every deleted symbol with reference
>    proof (the dr-audit-dead two-scan discipline); every test that
>    exercised the old road MIGRATES to assert the same behavior through
>    the alias — a deleted test is a defect, a migrated one is the point.
> S4 PROVE NOTHING MOVED THAT MUST NOT: run identity is deterministic
>    through the new road — same manifest, same run id (fixture proof).
>    Every root now gains the full lifecycle (stop record, terminal
>    commitment, progress, dossier attachment at seed) — that delta is
>    the PURPOSE; state it in DELIVERY.md, don't hide it. Old committed
>    roots replay byte-unchanged: targeted verify_root_report pasted at
>    validation. MCP start_run and the qualification battery's own
>    deliberate separate dispatch are out of scope and untouched.
>
> FROZEN SURFACES: none are expected — this is application-layer
> consolidation. If the spec census finds genuine contact (manifest
> schema, replay formats), that is the workflow's own stop condition:
> report with the census, priced options, one recommendation.
>
> GATE: ring while iterating; full gate at the boundary; docs_verify full
> (baselines per docs/AUDIT_BASELINES.md). Map moves in the same commits —
> SUB-application, SUB-cli's covering doc, and SEAM-application-x-cli (or
> first-time-document it if the matrix says unwritten). Wheel smokes:
> console entry points unchanged, so pins should not move — if one does,
> all four pin locations in the SAME commit. Errata: any committed
> document describing the two-path split as permanent design, or the bare
> path as lifecycle-complete, gets an entry (next free number — check the
> ledger tail). Commit and push every phase boundary (retry 2s/4s/8s/16s).
> Deliver R-by-R with pasted PROOF; DELIVERY.md closes with the one-line
> census: paths before = 2, paths after = 1, operations reachable from
> it = all.

### Source 3 — the operator's answer to this tranche's opening gate

Operator, 2026-08-13, second message of the session, in full:

> it is now in main.

Context (not the operator's words): the session's first act was the
mandated GATE, which found `terminalize_text_run` absent from
`origin/main` and reported "lifecycle-parity tranche not yet on main" and
held. Source 3 is the operator's release of that hold. Re-run of the gate
after `git fetch origin main` (`origin/main` `fc0d75473`) found the symbol
at `src/deepreason/application/text_runs.py:290`, so the gate is
SATISFIED and the hold is lifted.

### Source 4 — the companion standing law, already ledgered

Cited by Source 2 as "Companion standing law (ledgered by the lifecycle
tranche)". Its ledgered form, `CLAUDE.md:284-301`, quotes the operator
verbatim:

> The flags and operations available to the newer reason runs should be
> available to all configurations.

Source 2 states this tranche's relation to it verbatim: "This tranche is
that law's structural enforcement: one path means nothing can diverge."

## Requirements

R1 (behavior): "TextRunApplicationService gains a manifest-direct entry —
accept a precompiled RunManifest (and/or a run-config file compiled via
compile_run_manifest)".

R2 (behavior): that entry covers "the FULL configuration space the
all-configs law admits: judge role ensembles, school-routed
conjecture/criticism, criticism_policy, everything build_manifest.py had
to hand-feed. No narrowing: any manifest the compiler emits, the service
runs."

R3 (behavior): "The grounded run's committed run-config.yaml +
build_manifest.py (experiments/2026-08-12-live-grounded-extension-
expansion/) is the acceptance fixture: that exact config must enter
through the new door."

R4 (behavior): "`deepreason run --run-manifest` keeps its exact CLI
surface but becomes a thin wrapper that routes into the managed service."

R5 (behavior): "Preserve the rc exit-code contract (application/models.py
run_result_exit_code) and flag behavior — regression-pin both."

R6 (behavior): "Ladders and scripts keep working unmodified."

R7 (behavior): "remove the parallel scheduler-only dispatch in cli/main.py
(_execute_bound_run's direct implementation) and the bare-path lifecycle
retrofit the lifecycle tranche added to it — that code is superseded by
this unification, which is why it goes, not because it was wrong."

R8 (artifact): "Census every deleted symbol with reference proof (the
dr-audit-dead two-scan discipline)".

R9 (behavior): "every test that exercised the old road MIGRATES to assert
the same behavior through the alias — a deleted test is a defect, a
migrated one is the point."

R10 (behavior): "run identity is deterministic through the new road — same
manifest, same run id (fixture proof)."

R11 (artifact): "Every root now gains the full lifecycle (stop record,
terminal commitment, progress, dossier attachment at seed) — that delta is
the PURPOSE; state it in DELIVERY.md, don't hide it."

R12 (behavior): "Old committed roots replay byte-unchanged: targeted
verify_root_report pasted at validation."

R13 (process): "MCP start_run and the qualification battery's own
deliberate separate dispatch are out of scope and untouched."

R14 (process): "FROZEN SURFACES: none are expected — this is
application-layer consolidation. If the spec census finds genuine contact
(manifest schema, replay formats), that is the workflow's own stop
condition: report with the census, priced options, one recommendation."

R15 (process): "GATE: ring while iterating; full gate at the boundary;
docs_verify full (baselines per docs/AUDIT_BASELINES.md)."

R16 (artifact): "Map moves in the same commits — SUB-application,
SUB-cli's covering doc, and SEAM-application-x-cli (or first-time-document
it if the matrix says unwritten)."

R17 (artifact): "Wheel smokes: console entry points unchanged, so pins
should not move — if one does, all four pin locations in the SAME commit."

R18 (artifact): "Errata: any committed document describing the two-path
split as permanent design, or the bare path as lifecycle-complete, gets an
entry (next free number — check the ledger tail)."

R19 (process): "Commit and push every phase boundary (retry
2s/4s/8s/16s)."

R20 (artifact): "Deliver R-by-R with pasted PROOF; DELIVERY.md closes with
the one-line census: paths before = 2, paths after = 1, operations
reachable from it = all."

## Standing constraints

C1: "Route through dr-change-orchestrator; the workflow's own stop
conditions apply, nothing else stops." — Source 2, opening paragraph.

C2: "GATE before any work: grep -q terminalize_text_run
src/deepreason/application/text_runs.py || report 'lifecycle-parity
tranche not yet on main' and hold — this tranche builds on its shared
terminalization and supersedes its bare-path retrofit." — Source 2,
SETUP. SATISFIED at `origin/main` `fc0d75473` (see Source 3).

C3: "Use `python -m pytest`, never bare pytest." — Source 2, SETUP.

C4: "Read CLAUDE.md in full; load dr-drive-harness,
dr-explain-to-operator." — Source 2, SETUP. Done before this file was
written.

C5: "Parity by construction." — Source 2, opening. The stated design
criterion: parity is to be achieved structurally (one path), not by
keeping two paths in agreement.

C6: "The flags and operations available to the newer reason runs should be
available to all configurations." — Source 4, the standing operator design
law this tranche structurally enforces (`CLAUDE.md:284-301`).

C7: "All configurations should be allowed." — the 2026-08-12 standing
operator design law (`CLAUDE.md:265-283`), named by Source 2 as "the
all-configs law" whose admitted configuration space R2 must cover.

C8 (repo law, not this message): the append-only record. "fix READERS so
old roots stay valid; a change that invalidates existing replay-valid
roots is wrong by definition." — CLAUDE.md, Frozen surfaces.

C9 (branch): the session's designated development branch is
`claude/single-run-path-unification-bhn2ob`. Source 2's SETUP names
`claude/single-run-path-unification-y83rdk`; the session's own standing
branch instruction names `-bhn2ob` and forbids pushing elsewhere without
explicit permission. Both were reset from the same `origin/main`
(`fc0d75473`), so the content is identical and only the name differs.
Recorded here rather than silently resolved; flagged to the operator at
the first phase boundary.

## Map ids (preflight, per dr-drive-harness §4)

Resolved from `docs/map/INDEX.md` before any design:

- `DR-SUB-application` — the covering document for BOTH sides of this
  change. Its `Owns:` line is
  `src/deepreason/application/, src/deepreason/workflows/,
  src/deepreason/cli/, src/deepreason/runtime/, src/deepreason/easy.py,
  src/deepreason/intake_form.py, src/deepreason/shallow.py`, so `cli/` is
  not a separate subsystem: R16's "SUB-cli's covering doc" IS
  `SUB-application.md`.
- `DR-CON-run-identity` — deterministic run ids, roots on disk (R10).
- `DR-INV-frozen-surfaces` — read before design, per §4. None of the five
  surfaces (`capabilities/state.py`, `harness.py`, replay-validation
  formats, `run_manifest.py` schemas+validators, qualification subjects)
  is in `application/` or `cli/`. R14's stop condition is armed but not
  triggered at capture time; the spec census re-checks it.
- SEAM `application x cli`: the INDEX seam matrix contains no such pair,
  and cannot — a seam joins two map documents, and one document owns both
  sides. This is recorded for `dr-spec-change` as the reason R16's
  "SEAM-application-x-cli (or first-time-document it...)" resolves to the
  no-seam branch rather than the write-one branch. `SUB-application.md`'s
  own `Seams-undocumented:` list (`application x bridge`,
  `application x run-identity`, `application x scratch`,
  `application x verification`, `application x workflow`) is the real
  candidate set; whether this change touches one is a spec question.

## Open questions (for dr-spec-change)

Q1: R1 says "a precompiled RunManifest (and/or a run-config file compiled
via compile_run_manifest)". "And/or" leaves undetermined whether the new
door must accept a run-config YAML path directly, or only an
already-compiled manifest. Cost and surface differ materially.

Q2: R4 says the alias preserves "its exact CLI surface" and R6 says
ladders keep working unmodified, while R11 says every root "now gains the
full lifecycle". `deepreason run` is synchronous and prints survivors,
frontier, meter snapshot and a rendered theory; the managed service
launches a daemon thread and returns. What "exact CLI surface" covers —
stdout bytes, exit code, blocking behavior, or all three — is
undetermined.

Q3: R5 says "Preserve the rc exit-code contract (application/models.py
run_result_exit_code)". The current `_cmd_run` does NOT use
`run_result_exit_code`; it returns 0 on success and 1 on typed failure.
Whether "preserve" means keep `run`'s observed 0/1 behavior or adopt the
`run_result_exit_code` mapping is undetermined, and the two differ (that
function can return 5).

Q4: R7 names "_execute_bound_run's direct implementation" for deletion.
`_cmd_run` also performs admission, budget parsing, `--dry-run`
rendering, `--problem` preflight and operator locking before calling it.
How much of `_cmd_run` is "the parallel scheduler-only dispatch" and how
much is the CLI surface R4 preserves is undetermined.

Q5: R3 makes the grounded tranche's `run-config.yaml` + `build_manifest.py`
the acceptance fixture. `build_manifest.py` writes files into a root
(evidence-dossier.json, run-input.json, run-manifest.json, problem.json)
and is not importable as a library without executing its module-level
`sys.path` mutation. Whether "that exact config must enter through the new
door" means the YAML, the compiled manifest bytes, or a test that calls
`build_manifest.build()` is undetermined.

Q6: R12 says "Old committed roots replay byte-unchanged: targeted
verify_root_report". Which roots are "targeted" — the grounded-extension
root only, a sample, or the full 42-root sweep — is undetermined, and the
sweep costs ~10 minutes.

## Amendments

(append-only; later operator messages land here as R21... or "R4a
supersedes R4", each with its verbatim quote)

### Amendment 1 — 2026-08-13, mid-execution (after CHECKLIST step 18)

Two operator messages, verbatim and in order:

> The token steering controller that runs through config. Are you wiring
> that up as well so that it runs with custom configuration setups?

> Is this operating on the dynamic token allocation system as well?

**Classified as QUESTIONS about existing scope, not new requirements.**
Both ask whether something already in the tranche's scope holds; neither
adds an obligation. Recorded verbatim per the ledger rule before being
acted on. If the operator's intent was an obligation rather than a
question, it becomes R21 on their word.

**Answered from the record** (`dr-ask-the-right-question`: cheapest
authority first — this one is answerable from the code, not from the
operator):

The token-steering controller is `src/deepreason/referee.py`
(`run_config_referee`), whose own module docstring calls it "recorded
token-steering machinery (the research allowance and its signals)", and
whose role prompt (`llm/roles.py:51-53`) names its target as "the
harness's dynamic token-steering configuration". It is authorized by
manifest data: `InquiryCapabilityPolicyV1.config_referee`
(`ConfigRefereePolicyV1`), compiled by
`v6_policy.engaged_config_referee_policy` and defaulting to ABSENT
unless `DEEPREASON_CONFIG_REFEREE` names a cadence.

It fires from inside the scheduler, `Scheduler._maybe_config_referee`
(`scheduler/scheduler.py:695`, called at `:1897`), gated on exactly
three things: manifest schema 6, `policy.enabled`, and the cycle
cadence. It is gated on NOTHING about the launch path — no CLI verb,
no service method, no intent field appears in that gate.

Consequence for this tranche, in both directions:

1. **It was never launch-path-dependent**, and this tranche does not
   change that. Both the deleted dispatch and the surviving one call
   `run_scheduler(harness, config_from_run_manifest(manifest), ...)`.
   Whatever the manifest authorizes, the scheduler runs.
2. **The door must not narrow it**, and that is R2's existing
   obligation, now proved for this specific lever rather than assumed:
   a new acceptance test drives a manifest with `config_referee`
   ENABLED through `start_manifest_run` and asserts the referee is
   reached. Added under R2, not as new scope.
3. **What DOES change for these runs is the record around it.** The
   referee writes advice onto the log; before this tranche a
   `run --run-manifest` root reached no terminal, so `result`,
   `continue` and `amend` could not read what it wrote. That is R11's
   delta, and the referee's output is one of the things it makes
   reachable.

The same three points hold for the `research` allowance and the
`simulation` policy, which travel in the same
`InquiryCapabilityPolicyV1` and are gated the same way.
