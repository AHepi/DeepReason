# VENDORED — treadle 0.4.1

**Provenance.** Unpacked from `treadle0.4.1.zip`, supplied by the operator on
2026-08-23 for `experiments/2026-08-23-treadle-pilot/`.

    zip sha256: e4d329e8f7ac130eb46ec5131db5bcd802ac87f9a789d858a4ea24f37d80596b
    version:    0.4.1 (pyproject.toml [project].version)
    entry point: treadle = "treadle.cli:main"

**Everything below `tools/treadle/` except the ignored runtime paths is the
zip's content, unmodified.** Verified byte-for-byte at install time:

    diff -r --exclude=.venv --exclude=treadle.egg-info <unpacked-zip> tools/treadle
    -> no output

Do not edit files here. treadle's configuration for THIS repository lives at
`/treadle.toml` and `/skills/`; its behaviour is changed there, never by
patching the vendored source. If the vendored source ever must change, the
change belongs upstream and a new version is vendored whole.

## Deviations from the shipped `AGENT_INSTALL.md`

The shipped instructions install to `~/tools/treadle`. Two deviations were
directed by the operator, and three more were forced by this repository; all
five are recorded here and specified in
`experiments/2026-08-23-treadle-pilot/SPEC.md`.

**D1 — vendored into the repo, not `~/tools/`.** This project runs in a cloud
container that can roll back silently, taking every gitignored path with it. A
home-directory install would not survive the session that depends on it, so the
SOURCE is committed here. Only the venv (`tools/treadle/.venv/`), the build
metadata (`src/treadle.egg-info/`) and the driver's runtime state (`.treadle/`
at repo root) are gitignored.

Consequence for anyone re-entering the repo: the source is present, the venv is
not. Rebuild it with

    python3 -m venv tools/treadle/.venv
    tools/treadle/.venv/bin/pip install -e "tools/treadle[dev]"

**D2 — repo assets at their documented locations.** `scripts/swarm_gate.py`,
`/treadle.toml`, `/skills/` — exactly as `AGENT_INSTALL.md` §2 places them. The
shipped `skills/` tree is a sibling of, and has no name in common with,
`.claude/skills/` (DeepReason's own workflow skills); the two do not collide.

**D3 — `.swarm/` is committed.** Per `AGENT_INSTALL.md` §2's own `git add`
line. The board and its hash-chained log are the coordination record; a
rollback that ate them would leave the gate's history unreplayable.

**D4 — `/treadle.toml` is adapted, not copied verbatim.** The shipped file's
`context_files` point at another programme's tree (`zoo/batteries/FORMAT.md`,
`zoo/derivations/FORMAT.md`, `rules/rules.json`). None exists here, and
`treadle doctor` prints a `WARN ... MISSING (dangling read reference)` for each,
which the install's acceptance condition (every line OK) does not permit. Those
entries were removed. The shipped original is preserved unmodified at
`tools/treadle/repo-assets/treadle.toml`, so the adaptation is a diff away.

**D5 — one added stage.** `[stage.pilot]`, routed from the `PIL-` prefix, with
its system prompt at `skills/pilot-task/SKILL.md`. The five shipped generate
stages carry PROMPT-CORE text written for a formal-methods programme; routing a
DeepReason instrument task through one would measure the mismatch rather than
the driver. The shipped `review` stage is used UNMODIFIED, because the
independent-review question is only answered honestly if the reviewer runs
treadle's own reviewer prompt.

## Its own test suite

    cd tools/treadle && .venv/bin/python -m pytest -q
    -> 34 passed

`AGENT_INSTALL.md` says "must print: 5 passed". That number is from 0.1.0, which
is also the filename the shipped doc still unzips (`treadle-0.1.0.zip`). For
0.4.1 the count is 34. The doc is stale on the count, not wrong about the
obligation: the suite must pass.
