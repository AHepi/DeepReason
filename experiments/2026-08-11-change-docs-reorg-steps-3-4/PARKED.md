# Parked (found mid-tranche, not requested, not fixed here)

## P1 — bare `pytest` on PATH resolves to an isolated interpreter without the `deepreason` editable install

Found running CS3 (the full gate). `which pytest` ->
`/root/.local/bin/pytest`, whose shebang points at
`/root/.local/share/uv/tools/uv-managed` interpreter — a `uv`-tool
install, separate from `/usr/local/lib/python3.11/dist-packages` where
`pip install -e . --break-system-packages` puts the editable
`deepreason` package. Running bare `pytest tests/ -q -n 4` (exactly the
command CLAUDE.md's "Build and test" section prints) fails immediately:
`ModuleNotFoundError: No module named 'deepreason'` from
`tests/conftest.py:5`. `python -m pytest tests/ -q -n 4` (using
`/usr/local/bin/python`, confirmed via `pip show deepreason`) runs
correctly.

This is a container/environment PATH quirk, not a DeepReason code
defect — out of scope for a docs-reorg change tranche either way. But
it will cost the next session the same ~10 minutes of misdiagnosis it
cost this one (a `ModuleNotFoundError` reads exactly like a broken
install), and CLAUDE.md's own printed gate command is the one that
fails. Ready-to-send prompt for whoever picks this up:

> Route: `deepreason-orchestrator` (or a `dr-change-orchestrator`
> tranche if the operator wants CLAUDE.md's own command text changed).
> Goal: bare `pytest` on this container's PATH resolves to a uv-tool
> interpreter lacking the `deepreason` editable install, so
> CLAUDE.md's own "Build and test" section's literal `pytest tests/ -q
> -n 4` command fails with `ModuleNotFoundError: No module named
> 'deepreason'` even in a correctly-provisioned container.
> Evidence: `which pytest` -> `/root/.local/bin/pytest` (uv-tool
> shebang); `pip show deepreason` -> `Location:
> /usr/local/lib/python3.11/dist-packages`, i.e. a DIFFERENT
> interpreter's site-packages. `python -m pytest tests/ -q -n 4`
> succeeds using the correct interpreter.
> End state: either CLAUDE.md's gate command is corrected to
> `python -m pytest tests/ -q -n 4` (if this PATH shape is
> container-standard), or the container provisioning is fixed so bare
> `pytest` resolves to the interpreter with the editable install (if
> the uv-tool shadowing is itself the defect). Operator should say
> which is intended before either is changed — this could also be a
> one-off quirk of this particular container instance, not a standing
> fact about the fleet.
