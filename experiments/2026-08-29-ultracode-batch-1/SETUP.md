# Batch setup — measured baselines, 2026-08-29

Orchestrator record for the ultracode batch. Everything here was MEASURED on
`origin/main` at `25a3a0687` before any lane started, so that every later
verdict compares against a number this file can be re-derived from. The batch
brief's own figures are quoted where they differ, and the measurement wins.

## Anchor

    git merge-base --is-ancestor 25a3a0687 origin/main   -> exit 0
    origin/main == 25a3a0687 == session branch head at batch start

## Environment defect found and closed BEFORE any lane ran

`pytest` was not installed in this container. `pip install -e .` carries only
the runtime dependencies; the test runner lives in the `dev` extra. The
consequence was not a missing convenience — it silently falsified the map's
own authentication instrument:

    python tools/docs_verify.py     -> 508 failed      (pytest absent)
    pip install -e '.[dev]' && pip install pytest-xdist
    python tools/docs_verify.py     -> 4 failed        (the true baseline)

504 of those 508 were `No module named pytest`, not stale claims. A lane that
had taken the first number as its floor would have had no way to see a real
regression. Recorded because the next session in a fresh container will hit
it again.

## docs_verify baseline — 4 failed, unchanged from the stated stop-line

Raw output: `evidence/docs_verify_baseline_main.out` (69 documents, 1150
checks, 4 workers).

| Failure | Kind |
|---|---|
| `CON-run-identity.md:200` | shallow clone — history not present in this container |
| `CON-run-identity.md:202` | shallow clone — `1637e808` unresolvable here |
| `CON-run-identity.md:204` | shallow clone — `f304fec1` unresolvable here |
| `INV-frozen-surfaces.md:181` | pre-existing falsified census |

A fifth failure, or any different failure, is a finding. One exception is
FORECAST below.

## Forecast fifth failure — P16, not a delta

`docs/map/INV-frozen-surfaces.md:297` carries

    check: ! git diff --name-only origin/main...HEAD | grep -qE "capabilities/state\.py|/harness\.py|/invariants\.py|/run_manifest\.py|/qualification\.py|llm/firewall\.py"

It is green on `main` only because `origin/main...HEAD` is empty there, and it
cannot distinguish a GRANTED contact from an ungranted one. Lane B holds a
conditional grant on surface 4 (`run_manifest.py`), so this check is expected
to fire on lane B's branch and on the integrated session branch. That is the
already-parked defect **P16**
(`experiments/2026-08-28-defect-manifest-config-disclosure/PARKED.md`), firing
as designed. It is NOT to be filed down: a tripwire another tranche just landed
is not something to weaken because it caught you.

## Full-gate baseline — 4438, not the brief's 4419

    python -m pytest tests/ -q --collect-only   -> 4438 tests collected

The batch brief states 4419. The tree has moved since that figure was taken.
Growth at fan-in is priced against **4438**.

## Lane isolation, and the defect it would otherwise have had

Four git worktrees, one per lane, outside the repository:

    /home/user/dr-lanes/a-p11     lane/a-p11
    /home/user/dr-lanes/b-config  lane/b-config
    /home/user/dr-lanes/c-p7a     lane/c-p7a
    /home/user/dr-lanes/d-seam    lane/d-seam

Worktrees alone are NOT sufficient isolation here. The editable install is a
plain path file:

    /usr/local/lib/python3.11/dist-packages/_editable_impl_deepreason.pth
        /home/user/DeepReason/mini
        /home/user/DeepReason/src

so `import deepreason` from inside a lane worktree resolves to the
ORCHESTRATOR's checkout, and every lane would have tested code it had not
written. Because the editable install is a `.pth` (path entries appended by
site processing) rather than a `sys.meta_path` finder, `PYTHONPATH` takes
precedence. Verified:

    cd /home/user/dr-lanes/d-seam && \
      PYTHONPATH=/home/user/dr-lanes/d-seam/src:/home/user/dr-lanes/d-seam/mini \
      python -c "import deepreason; print(deepreason.__file__)"
    -> /home/user/dr-lanes/d-seam/src/deepreason/__init__.py

Every lane runs with that prefix and aborts if the sanity check resolves
elsewhere.

## Concurrency

`nproc` = 4, so the workflow's concurrency cap is `min(16, 4-2) = 2`. Four
lanes were declared; two run at a time and the rest queue. This costs
wall-clock, not correctness — lane B's two tranches were already sequential by
construction because they share `preparation.py`.

## Offline

No `OLLAMA_API_KEY` and no provider reachable. Every lane proves its case
offline against the committed record, fixtures, or the deterministic stub. No
live run is attempted.
