# Goal: determine whether tools/root_sweep.py and scripts/wheel_smoke.py / wheel_operational_smoke.py are current against main's actual record vocabulary and public surface, and whether any main-history commit violated CLAUDE.md's same-commit pin-update rule

Class: capability-gap (this is a staleness/coverage AUDIT of two instruments,
not a report of an already-observed behavioral contradiction; any same-commit
violation found becomes its own recorded fact via ERRATA, per the operator's
verbatim directive: "Sweep and smoke need to be checked. If they are out of
date, that's a debugging error that goes into errata.")

Observed: the operator asked, as part of a seven-item program, whether the
two non-gate instruments (root sweep, wheel smokes) still cover what main
actually emits/exposes today, and whether CLAUDE.md's own stated rule ("any
commit changing that surface updates the pins and re-runs the smoke in the
same commit") was honored across main's history. No specific failure is
alleged yet — this tranche measures, it does not assume drift.

Success criterion (machine-decidable):
    python tools/root_sweep.py --help   (confirms tool runs; then read its
        source for the event-type/record-field vocabulary it iterates and
        diff that list against harness.py's actual typed vocabulary)
    python scripts/wheel_smoke.py --help / read source for pinned console
        entry points, MCP tool set, wheel layout; diff against
        pyproject.toml's actual entry points and the live MCP tool
        registration
    git log --oneline -- <surface-defining files> vs git log --oneline --
        tools/root_sweep.py scripts/wheel_smoke.py
        scripts/wheel_operational_smoke.py, aligned by commit, to find any
        commit touching the former without the latter in the SAME commit
    Output: a coverage table (sweep: covered / not covered per vocabulary
        item, with reason) and a violations list (commit sha, what surface
        changed, why no pin update) — each violations-list entry becomes a
        docs/ERRATA.md or docs/ERRATA_EXECUTOR.md entry in Item 2.

In scope: tools/root_sweep.py, scripts/wheel_smoke.py,
scripts/wheel_operational_smoke.py, and the git history of the files that
define the public/record surface they pin (harness.py event types,
capabilities/state.py seat-bindings, pyproject.toml entry points,
mcp_server tool registration).
NOT in scope: fixing src/ code to close any coverage gap found; that is a
separate tranche unless the fix is mechanical and confined to the
instruments themselves (tools/, scripts/) with zero src/ changes.

Budget: <=150 changed lines if any mechanical instrument fix is made this
tranche (audit + errata otherwise touches 0 lines of tools/scripts code),
1 commit for the audit report, 1 commit for the map/errata update, ~1 hour.
Stop conditions inherited from orchestrator: yes
