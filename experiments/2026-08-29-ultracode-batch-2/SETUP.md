# SETUP.md — ultracode batch 2

Recorded 2026-08-29 at batch open, before any lane work.

## Target and anchor

    $ git remote -v
    origin  https://github.com/AHepi/DeepReason (fetch)
    origin  https://github.com/AHepi/DeepReason (push)

    $ git log --oneline -1 origin/main
    84514a028 batch: fan-in evidence for lanes C and B2 -- 4486 passed 0 failed, docs_verify +1 forecast

    $ git merge-base --is-ancestor 84514a028 HEAD && echo OK
    OK

Session branch `claude/deepreason-ultracode-batch-2-l9vj55`, created from
`origin/main` at `84514a028`. Zero commits ahead at open.

## Environment, as measured (not as assumed)

`pip install -e . --break-system-packages -q` succeeded; `deepreason`
resolves to `/usr/local/bin/deepreason`. Two packages the gate needs were
NOT installed by that command on this fresh container:

    $ python -c "import xdist"
    ModuleNotFoundError: No module named 'xdist'

`jsonschema` likewise required its own `pip install`. Both were installed
by hand before any lane ran. This is the empirical confirmation of lane
E2's P6 finding, observed at minute one of this session rather than
argued from the brief; it is cited as evidence in that lane.

No `OLLAMA_API_KEY` and no `env` file anywhere: this batch is OFFLINE by
construction, and no lane may claim live evidence.

## The rule batch 1 paid for

`experiments/2026-08-29-ultracode-batch-1/LOSS.md` records two lanes whose
STOP briefs and implementation patches died with the container because a
withheld lane felt like work in progress. Its lesson is binding here:

> **A STOP is a phase boundary.** Work parked for an operator decision is
> finished work awaiting a verdict, and it must be pushed at the moment it
> is parked, not at the moment the verdict arrives.

Accordingly: this session pushes the session branch and every lane's work
at every phase boundary, and a parked STOP is pushed with its brief in the
same act that parks it.

## Lane roster

| Lane | Family | Goal |
|---|---|---|
| A | dr-change-orchestrator | Checkpoint hardening — P2 law limbs 2 and 3 |
| B | dr-change-orchestrator | Successor questions — P9 law |
| C | deepreason-orchestrator | F1 rank-penalty fix — formalism-optional violation |
| D | (docs/map + measurement) | Four rotted map checks |
| E | (tests/probes, then docs) | Two execution-safety parks: P4, P6 |

Integration order is cheapest-first — D, E, C, B, A — with a ring after
each, then ONE full gate and ONE `docs_verify` at fan-in.
