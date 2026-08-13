# PARKED — found during the results-retrieval tranche, deliberately not fixed

One tranche, one goal (CLAUDE.md cross-routing rule). Each entry below is a
ready-to-send prompt: the follow-up should cost the operator a paste, not an
authoring session.

---

## P1 — `deepreason findings` reads a run root but skips the V6 admission gate

**What.** `_ROOT_ADMISSION_COMMANDS` (`src/deepreason/cli/main.py:556`) lists 26
verbs that pass `_admit_v6_root` before their own code runs. `findings` reads a
run root (`findings.findings_summary` opens `Harness(root, read_only=True)`) and
is NOT in that set. `docs/map/SUB-application.md`'s prose states the rule
without the exception: "Admission precedes interpretation. Every CLI verb that
touches an existing run root passes through one V6 gate". This tranche
CORRECTED that sentence to name the reader exception (SPEC.md S18c) and added
`results` as a second deliberate exception (SPEC.md A8), but did NOT decide
whether `findings` — or read-only verbs generally — *should* be admitted. That
is a design question about what admission is for, not a defect this tranche
may settle.

**Prompt to send:**

```
Change tranche: decide whether read-only run-root readers belong inside the V6
admission gate. Route through dr-change-orchestrator.

AUTHORITY: no operator words yet — this is a design question surfaced by the
2026-08-13 results-retrieval tranche
(experiments/2026-08-13-change-results-retrieval-surface/PARKED.md P1). Capture
that provenance in REQUEST.md and ask the operator for their words before
dr-spec-change decides anything.

The fact: `_ROOT_ADMISSION_COMMANDS` (src/deepreason/cli/main.py:556) admits 26
verbs. `findings` and `results` both read a run root and are deliberately
outside it, because a reader that refused pre-V6 roots would refuse exactly the
roots a session most needs to inspect (11 committed roots raise
UnsupportedRunManifestVersionError — docs/AUDIT_BASELINES.md records that as
baseline). docs/map/SUB-application.md now names the exception rather than
denying it.

Decide, in writing, ONE of: (a) admission is for verbs that INTERPRET or MUTATE
a root, and pure readers are correctly outside it — in which case make that the
stated rule in SUB-application.md, and add a test that every verb NOT in
_ROOT_ADMISSION_COMMANDS is provably read-only; or (b) readers belong inside
too — in which case admission must gain a read-only tier that reports the
manifest state instead of refusing, and both `findings` and `results` move into
it. Price both before choosing.

RAILS: no behaviour change to `findings`' current output without the operator's
words. Frozen surfaces: none expected (cli/ dispatch + map). GATE: ring while
iterating; full gate at the boundary; docs_verify full against
docs/AUDIT_BASELINES.md.
```

---

## P2 — `docs/map/` covers no top-level reader module

**What.** 21 top-level `src/deepreason/*.py` modules appear in no map
document's `Owns:` header, including `findings.py`, `error_catalog.py`,
`report.py`, `signals.py` and `status_display.py` — every one of them a reader
or a reader's vocabulary. `docs/map/INDEX.md`'s "Coverage, stated honestly"
section already declares uncovered ground as a known gap, so this is not a lie
in the map; it is unwritten ground. This tranche AVOIDED widening it by placing
its new reader at `src/deepreason/application/results.py`, which
`DR-SUB-application`'s `Owns:` already covers.

Re-derive the list:

```
python - <<'EOF'
import pathlib
owns=set()
for p in pathlib.Path("docs/map").glob("*.md"):
    for line in p.read_text().splitlines():
        if line.startswith("Owns:"):
            owns.update(x.strip() for x in line[5:].split(","))
for f in sorted(pathlib.Path("src/deepreason").glob("*.py")):
    if str(f) not in owns: print(f)
EOF
```

**Prompt to send:**

```
Change tranche: close the map's top-level-module coverage gap. Route through
dr-change-orchestrator.

AUTHORITY: no operator words yet — surfaced by the 2026-08-13
results-retrieval tranche
(experiments/2026-08-13-change-results-retrieval-surface/PARKED.md P2). Capture
that provenance in REQUEST.md.

The fact: 21 top-level src/deepreason/*.py modules are in no map document's
Owns: header — findings.py, error_catalog.py, report.py, signals.py,
status_display.py, referee.py, controller.py, loop.py, indexes.py, locking.py,
canonical.py, manifest.py, mcp_help.py, mcp_registration.py,
mcp_scratch_bridge.py, browser.py, conjecture_events.py, conjecture_turn.py,
shallow_fitness.py, __main__.py, __init__.py. docs/map/INDEX.md's "Coverage,
stated honestly" section already declares this class of gap; the work is
closing it, not discovering it. Re-derive the list with the script in P2 of
that PARKED.md before scoping.

Assign each module to an EXISTING covering document by extending its Owns:
header where the fit is real, and record explicitly which modules do not fit
any existing subsystem and therefore need a new SUB- or CON- document. Every
newly-owned module needs at least one `check:` that would fail if the claim
regressed (docs/map/SCHEMA.md is the contract). Do NOT create a document per
module.

RAILS: docs only — no src/ change. Frozen surfaces: none. GATE: python
tools/docs_verify.py full (3 pre-existing CON-run-identity git-history failures
are baseline on a shallow clone — docs/AUDIT_BASELINES.md), plus --links and
--audit.
```
