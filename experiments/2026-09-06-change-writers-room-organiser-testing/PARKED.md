# PARKED — the organiser seat tranche

Defects and wishes noticed during this tranche, not done here (C4). Each
entry is one line of WHAT and a ready-to-send prompt for its own tranche.

## P1 — the managed path never opens `<DEEPREASON_HOME>/seat_plugins/`

**What.** `load_operator_plugins` — the loader for operator `.py`, `.tmpl`
and `.layout.json` files — has one call site in `src/`, `shallow.py:71`,
the reduced engine's setup. `deepreason reason` (the managed full-harness
path, `application/text_runs.py`) never calls it, so the documented
operator directory is read by mini only, and a file-declared layout cannot
reach a full-harness seat. That is why this tranche registered the organiser
in `llm/seat_layouts.py` (SPEC A2) rather than as a file.

```
EXECUTOR WINDOW — DEFECT: the managed path does not load the operator's seat plugins
Read CLAUDE.md. Load deepreason-orchestrator and pinker-write-for-readers.
GOAL: `deepreason reason` loads `<DEEPREASON_HOME>/seat_plugins/` the way the
reduced engine does (`src/deepreason/shallow.py:71-73`) and records the
loader's two lists (loaded, notices) on the run, so a file-declared layout or
shell reaches a full-harness seat without a source edit (the modularity law,
2026-08-26). Evidence: `grep -rn 'load_operator_plugins(' src/deepreason`
shows one call site. Reproduce with a `.layout.json` under a temporary home
and a stub managed run that does not render it. Frozen surfaces: none
expected (the record kind for the notices may need a grant — check
tools/blast_radius.py and stop in FIX.md if it reports CONTACT). End state:
a regression test on the managed path, docs/map/INV-seat-section-plugins.md
moved in the same commit.
```

## P2 — the citable legend's cap (32) and excerpt (160 chars) are code, and its order is by content id

**What.** `citable_legend(maximum_blocks=32, excerpt_chars=160)` is called
with its defaults by `dr.src.citable_evidence` (`seat_sources/shipped.py`),
which declares no parameters; and a dossier's blocks are sorted by content
id at admission (`admission/parse.py:577`), so the 32 shown are a hash-
ordered sample of the room — measured on the committed attachment: 7 of 12
conjectures, 13 of 46 proposals (1 refuted-if), 12 of 36 objections; 62
withheld. The organiser READS the whole room (the frozen-evidence section
renders every body) but can CITE only that sample; a citation outside it is
the typed `EVIDENCE_REF_NOT_EXPOSED` measure. Disclosed in this tranche's
PREREG §11 and RESULTS.md; not fixed (C3: no change under `evidence/`; the
brief: "if it is not reachable by configuration, PARK that").

```
EXECUTOR WINDOW — CHANGE: make the citable legend's size a source parameter
Read CLAUDE.md (modularity: FROZEN protocol / VERSIONED registry / FREE
parameters). Load dr-change-orchestrator and pinker-write-for-readers.
Register `dr.src.citable_evidence` 1.1.0 in src/deepreason/seat_sources/
shipped.py with a declared parameters model (maximum_blocks, excerpt_chars,
and an `order` of `admission` | `content_id`), and a second conjecturer
source bundle that pins it, selectable by DEEPREASON_SEAT_SOURCE_BUNDLE; the
default bundle keeps 1.0.0 so both goldens stay byte-identical. The exposure
receipt must follow the legend (conj.py reads `shown`; touch nothing under
rules/ — if the receipt needs a change there, stop and say so). Prove with a
stub that a 94-block dossier under (maximum_blocks=128) exposes all 94 and
that a candidate citing the 94th verifies. OUT OF SCOPE: evidence/,
admission/, the legend's text.
```

## P3 — a cycle-scoped seat pairing (organise once, then the ordinary conjecturer)

**What.** `DEEPREASON_SEAT_SHELL` is read at every render for the whole
process; nothing configuration-shaped is cycle-scoped. The operations-parity
road — `reason --cycles 1`, then `continue --budget cycles=N-1` with the
variable unset — is a configuration road in principle, and the history
tranche recorded `continue` refused between cycles
(`experiments/2026-09-03-change-provenance-history-channel/PARKED.md` P1).
This tranche ran the organiser for the whole run (SPEC A5) with the
directive handling later turns (carry what is not yet on the record, else
abstain).

```
EXECUTOR WINDOW — CHANGE: a seat pairing that is cycle-scoped by configuration
Read CLAUDE.md (modularity; operations parity). Load dr-change-orchestrator
and pinker-write-for-readers. Two roads, price both in SPEC before choosing:
(A) prove offline, against the stub, that `deepreason reason --cycles 1`
followed by `deepreason --root <root> continue --budget cycles=3` with a
different DEEPREASON_SEAT_SHELL renders cycle 1 under one shell and cycles
2–4 under the other, and that the record shows which (section plans name the
plugins); (B) a per-cycle shell schedule declared in configuration
(`conjecturer=seat.conjecturer.organiser-v1@1,seat.conjecturer.legacy-v0`),
resolved by the walk from the cycle the request carries, recorded on the run.
Prefer A if it holds (no code); B otherwise. OUT OF SCOPE: any frozen surface.
```

## P4 — a critic that reads the room

**What.** On this tranche's ARM R the critic is `seat.critic.evidence-blind-v1`
— the legacy critic layout without the premise invitation and the citable
legend — so its attacks are its own (R14). The switch that would show the
critic the room's BODIES does not exist: no critic layout carries
`dr.evidence.frozen`, and the source that computes it
(`dr.src.frozen_evidence`) is in the conjecturer's bundle only.

```
EXECUTOR WINDOW — CHANGE: a critic pairing that is shown the writer's room
Read CLAUDE.md (seat-is-a-shell; the critic's brief and form are a registered
pairing). Load dr-change-orchestrator and pinker-write-for-readers. Register
`seat-pack.critic.room-aware-v1` (the legacy critic layout plus
`dr.evidence.frozen` at an exact priority) and a critic source bundle that
adds `dr.src.frozen_evidence` for the critic seat, selectable by
DEEPREASON_SEAT_SHELL / DEEPREASON_SEAT_SOURCE_BUNDLE; prove with a stub that
a critic brief carries the three room sources whole and that the critic's
parse half and target binding are unchanged (tests/test_seat_shell_swap.py's
assertions 3 and 4). Then one live ARM beside this tranche's ARM R, same
PREREG form, to measure whether a room-aware critic changes the composed
result. OUT OF SCOPE: rules/crit.py.
```

## P5 — per-countercondition block pointers

**What.** The organiser cites blocks per CANDIDATE (`evidence_refs`, ≤ 8);
which proposal block each countercondition came from is not on the wire —
the form has no per-countercondition reference field. C3 says park it: per-
candidate `evidence_refs` is enough for the first run.

```
EXECUTOR WINDOW — CHANGE: which block each refuted-if came from
Read CLAUDE.md (the wire contract is frozen by two callers — see
docs/map/INV-seat-section-plugins.md "wire_contract_for's answers are
frozen"; the additive-optional pattern `checker_specs` took). Load
dr-change-orchestrator and pinker-write-for-readers. Add an OPTIONAL,
additive `countercondition_refs` (paired by index, `EvidenceRefClaimV1`
each, empty allowed) to `ReasoningCandidateProposal` in
src/deepreason/workloads/text.py, checked by the same citation checker at
admission and recorded as measures; the wire TYPE must not change (no
contract-version bump). Run tools/blast_radius.py first: the proposal model
is read by `invariants.py`'s replay authority set — if it reports CONTACT,
stop in SPEC and ask. Prove with the organiser stub test extended by one
case.
```

## P6 — a seat's brief and its form must agree about evidence (the defect that killed ARM R)

**What.** `seat.critic.evidence-blind-v1` removes `dr.evidence.citable` and
`dr.premise-invitation` from the critic's BRIEF, but `rules/crit.py` binds the
citable block menu into the critic's CONTRACT from its own legend
(`crit.py:358`, fed by `batch_legend.shown`), independently of the layout. So
the critic is asked by a schema for block ids that its brief never shows it.
On the 2026-09-06 launch it filled `premise_evidence[].block` with the room's
own record ids, was rejected at those pointers, exhausted its repair ladder,
decomposed to `critic.atomic-target.v1`, exhausted that, and the run died
`V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY` at cycle 3 with 464 359 of 500 000
spent. Evidence: `runs/home-r/runs/run-36d9a22c3e2045ae1b8c7bfb9d95d092`,
its `run-status.json`, `deepreason stop-report`, the
`workflow-semantic-admission-v1` `authorized_pointers`, and the raw replies.

```
EXECUTOR WINDOW — DEFECT: a blind brief against a sighted form
Read CLAUDE.md. Load deepreason-orchestrator and pinker-write-for-readers.
GOAL: a critic that is shown no evidence legend is not asked for evidence
ids. Diagnose from the record named above BEFORE reading code. Three roads,
price all three in FIX.md and pick the smallest: (A) the critic seat's
SOURCE bundle supplies an empty legend when the bound layout carries no
`dr.evidence.citable` entry, so `crit.py`'s menu is empty and the schema
stops asking (check whether an empty menu is legal for
`BatchCriticWireContractV2` before proposing it); (B) a registered critic
form whose `premise_evidence` is absent, paired by the blind shell — a new
wire contract, which is frozen by two callers, so read
docs/map/INV-seat-section-plugins.md's "wire_contract_for's answers are
frozen" first and STOP in FIX.md if it needs a grant; (C) declare the blind
shell unusable with an evidence-bound run and refuse the pairing at
resolution with a typed error, which costs nothing and prevents the death.
Prove with a stub: the blind critic dispatched on a root with a bound
dossier must not be able to fail this way. OUT OF SCOPE: the organiser.
```

## P7 — one seat, two id systems: the room's record ids and the admission block ids

**What.** The organiser's brief shows the room whole (whose paragraph headers
carry `id=<room record id>`) and a legend of admission BLOCK ids. On the
2026-09-06 launch the seat cited legend ids 21 times and room header ids 58
times (`EVIDENCE_REF_UNKNOWN_BLOCK`), and the critic died of the same
confusion (P6). Nothing was invented and the record caught every one, but the
seat cannot be expected to keep two id systems apart when both are in front
of it.

```
EXECUTOR WINDOW — CHANGE: give the organiser ONE id system
Read CLAUDE.md. Load dr-change-orchestrator and pinker-write-for-readers.
Two roads, price both: (A) the converter stops writing `id=` into the
attachment's header lines (the room record id moves to a trailing line the
legend never mirrors, or goes away entirely) — a tranche-local change to
experiments/2026-09-06-change-writers-room-organiser-testing/tools/
room_to_attachment.py, re-run, re-digest, and the organiser directive drops
its "cite by block id" sentence in favour of the legend's own handles;
(B) the legend is made to show the room's record id beside each block id so
the two are aligned rather than rival (a parametrised citable-evidence
source, which is PARKED P2's road). Prefer A: it is configuration under the
tranche and touches no src/. Measure on a re-run: the unknown-block count
must fall to 0 and the verified count must rise.
```

## P8 — a budget denial at 99% of the ceiling is typed `operational_failure`, not `budget_exhausted`

**What.** ARM R's relaunch reached cycle 3 with 495 362 of its 500 000-token
ceiling spent — 99.07% — and the next transactional work unit was denied by
the budget. The run terminated `state: failed`, `stop_reason:
operational_failure`, message `token budget denied transactional work
sha256:dcd8fa45…`. The operator's law of 2026-08-29 says exactly the
opposite: "a budget denial on an exhausted budget terminates as
`budget_exhausted` (clean), never `operational_failure`" (CLAUDE.md, operator
design laws; the operator's own words: "clean stop. with an assurance that
continuing is possible"). The assurance half HELD — the record carries
`stop_reason_resumable: true` and `verify_root` re-derived 0 violations — so
the checkpoint obligation is met and only the CLASSIFICATION is wrong.

The cost of the misclassification is not cosmetic: PREREG §3 makes an
`operational_failure` a FAILED arm whose unit is not judged, so a run that was
stopped by the ceiling the operator set is disposed of as a breakage. Two
launches in a row have now produced no verdict, the second for a labelling
reason rather than a substantive one.

Evidence: `runs/home-r/runs/run-c3f3bf10bc57d63e224a9f1c68bf1057` —
`run-status.json`, `progress.jsonl` seq 8, `deepreason stop-report` (§4 rules
out CONFIGURATION and ENVIRONMENT; no 429, no transport fault), and
`runs/armR/ARMR_RESULTS.json` (`"violations": 0`, `"valid": true`,
`"source": "rederived"`).

```
EXECUTOR WINDOW — DEFECT: a budget stop typed as a breakage
Read CLAUDE.md, including the operator law of 2026-08-29. Load
deepreason-orchestrator and pinker-write-for-readers.
GOAL: a denial issued because the run's token budget has nothing left
terminates `budget_exhausted` (clean), not `operational_failure`. Diagnose
from the record above BEFORE reading code: the stop message is `token budget
denied transactional work`, the spend is 495362 of 500000, and
`stop_reason_resumable` is already true. Then find where the denial is
classified and what distinguishes "denied because the budget is spent" from
"denied for any other reason" — a denial with budget remaining must NOT
become a clean stop, so the fix turns on that distinction and needs a
regression test for both sides. Check `INV-frozen-surfaces.md` first: run
records and their stop reasons sit close to frozen ground, and if the fix
needs a grant, STOP in FIX.md and say so. OUT OF SCOPE: the organiser, the
measure, and anything under experiments/.
```
