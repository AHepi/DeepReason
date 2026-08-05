# Goal: the wheel smoke's entry-point reader is section-blind; make both smokes run to completion
Class: defect
Observed: `scripts/wheel_smoke.py` has been red since `4940b5f7`
(2026-07-28, "Ship the first-party EPUB adapter under the identical §3a
contract"), which added a `[project.entry-points."deepreason.admission.adapters"]`
group to `pyproject.toml`. The smoke's reader collects every non-blank,
non-`[`-prefixed line of the wheel's `entry_points.txt` into ONE set and
compares it against the two console scripts, so the `epub`/`pdf` adapter
lines land in the same bucket and the equality fails. The packaging is
correct; the reader is wrong. Evidence:
`experiments/2026-08-05-change-smoke-instrument-visibility/DELIVERY.md`
("red since `4940b5f7` … its entry-point reader lumps the custom
`deepreason.admission.adapters` group in with console scripts"), and
`scripts/wheel_smoke.py`'s `observed = {...}` comprehension, which has no
section state. Because the reader raises there, everything the smoke
checks AFTER that point — the MCP tool set and its schema sha — has been
unverified since 2026-07-26, and `scripts/wheel_operational_smoke.py`'s
status is unknown.

Success criterion (machine-decidable):

    python scripts/wheel_smoke.py
    -> exits 0

    python -u scripts/wheel_operational_smoke.py
    -> exits 0

    python -m pytest tests/ -q -n 4
    -> ends "0 failed" (3338 today; no existing assertion weakened)

    python tools/docs_verify.py
    -> "docs_verify: 0 failed"

In scope (3):
- `scripts/wheel_smoke.py` — the section-blind reader, and any pin it
  surfaces as stale once it runs past the failure point (MCP tool set,
  schema sha).
- `scripts/wheel_operational_smoke.py` — status unknown; whatever it
  surfaces once run to completion.
- The pinned expectations inside those two scripts ONLY.

NOT in scope: `pyproject.toml`. The operator states the packaging is
correct and the reader is wrong, and the record agrees — the adapters
group is a deliberate first-party extension point shipped by
`4940b5f7`. Making the smoke pass by removing or renaming that group
would be fixing the evidence to suit the instrument. Also not in scope:
the five frozen surfaces, `src/` behaviour of any kind, and the P1
tranche's parked items (P1a/P1b/P1e), which stay parked.

Budget: <=150 changed lines, 1 commit, ~2 hours.
Stop conditions inherited from orchestrator: yes

## Map preflight (resolved ids)

`docs/map/` describes `src/deepreason/`; `scripts/` is navigated by
convention and no map document owns it (`grep -rl "wheel_smoke"
docs/map/` → no hits). That is a finding, not a blocker: the smokes are
now named in `CLAUDE.md` as the third instrument (`20f2c8d1`), so the
gap is newly visible. Creating a map document for `scripts/` is NOT
part of this tranche — the fix touches no `src/` file, so nothing the
map describes changes.

Ids that bound the change even so:
- `DR-INV-frozen-surfaces` — read before designing; the smokes pin the
  PUBLIC surface (console entry points, MCP tool set + schema sha,
  wheel layout), which is adjacent to, but not the same as, the five
  frozen surfaces. Updating a smoke PIN is not a frozen-surface change;
  changing what the wheel SHIPS would be.
- `DR-SUB-periphery` — owns the MCP server surface the operational
  smoke exercises, if a pin there turns out to be stale.

## Note on a rule that landed today

`CLAUDE.md` and `dr-implement-fix` gained a same-commit pin rule at
`20f2c8d1`: a commit changing the public surface updates the pins and
re-runs the smoke in the same commit. This tranche is the inverse case —
the surface changed at `4940b5f7` and the pin was never updated — so the
rule is what should have prevented it, and this tranche is its first
exercise.
