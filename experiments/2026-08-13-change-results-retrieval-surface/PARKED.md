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

CORRECTION to an earlier draft of this prompt: do NOT propose "a test that
every verb NOT in _ROOT_ADMISSION_COMMANDS is provably read-only". That test is
false on its face — 20 verbs sit outside the gate and most of them write
(`run`, `reason`, `setup`, `admit`, `brain`, `config`, `input`, `doctor`,
`scratch`, `bridge`, `web`). The gate's actual scope is verbs that touch an
EXISTING root; verbs that CREATE one are a different category and are correctly
outside it. Re-derive the two lists before scoping:

    python -c "import argparse; from deepreason.cli.main import build_parser, \
      _ROOT_ADMISSION_COMMANDS as g; p=build_parser(); \
      s=[a for a in p._actions if isinstance(a,argparse._SubParsersAction)][0]; \
      print(sorted(set(s.choices)-g))"

Decide, in writing, ONE of: (a) the gate is for verbs that INTERPRET or MUTATE
an existing root, and pure readers are correctly outside it — in which case make
that the stated rule in SUB-application.md and pin the READER set explicitly
(`findings`, `results`) with a test that each is read-only, rather than pinning
the complement; or (b) readers belong inside too — in which case admission gains
a read-only tier that REPORTS the manifest state instead of refusing, both
readers move into it, and all 26 existing gated verbs need regression cover
proving their behaviour did not change; or (c) readers go inside and refuse
pre-V6 roots outright — price this one honestly, because it makes `results`
unusable on 11 committed roots and re-creates the retrieval problem the
2026-08-13 tranche was opened to fix. Price all three before choosing.

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

---

## P3 — `results_summary` replays the log twice per call

**What.** Found 2026-08-13 answering an operator question after delivery, by
counting `Harness.__init__` calls:

```
python - <<'PY'
import deepreason.harness as H
calls = []
orig = H.Harness.__init__
def counting(self, *a, **k):
    calls.append((str(a[0])[-30:], k.get("read_only"))); return orig(self, *a, **k)
H.Harness.__init__ = counting
from deepreason.application.results import results_summary
results_summary("<any committed root>")
print(len(calls), calls)
PY
```

→ `2 Harness opens`. `results_summary` opens one read-only harness for the
adjudication walk, and `findings.findings_summary` opens a second for the
status counts. Each open is a full replay, O(run length).

Two consequences, neither a correctness bug on a FINISHED root (which is
immutable, so both replays see identical bytes):

1. **Cost.** Two full replays where one would do. On the largest committed root
   (6.5 MB log) that is the difference between one and two multi-second reads.
2. **Snapshot skew on a LIVE root.** Against a run still appending, the two
   replays and the sidecar reads happen at different instants, so the reported
   numbers can straddle a cycle boundary. Nothing crashes and nothing is
   corrupt — the figures are each true of the moment they were read, but not
   necessarily of one single moment.

This was not a requirement of the results-retrieval tranche and is not a defect
in what it delivered; R4 asked that `findings_summary` be COMPOSED rather than
duplicated, and composing it via its public function is what produced the
second open.

**Prompt to send:**

```
Change tranche: make `deepreason results` replay a run's log once, not twice.
Route through dr-change-orchestrator.

AUTHORITY: no operator words yet — found 2026-08-13 answering a question after
the results-retrieval tranche closed
(experiments/2026-08-13-change-results-retrieval-surface/PARKED.md P3). Capture
that provenance in REQUEST.md.

The fact: results_summary opens Harness(root, read_only=True) for its
adjudication walk, and findings.findings_summary opens a second one for the
status counts — two full O(run length) replays per call. Re-derive the count
with the script in P3 of that PARKED.md before scoping. Harmless on a finished
root (immutable, so both replays agree); on a live root the two replays plus
the sidecar reads happen at different instants, so the reported figures can
straddle a cycle boundary.

Deliver ONE replay per call while keeping R4's composition rule intact — the
status counts must still come from findings.py's derivation, not a second copy
of it. The likely shape is an internal findings entry point that accepts an
already-open read-only harness, with the existing public findings_summary(root)
kept byte-identical for its own callers; price that against alternatives before
choosing. Add a test that counts Harness opens per results_summary call and
pins it at 1 — the same instrumentation used to find this.

RAILS: `deepreason findings` output must not change by one byte (pin it).
Read-only against roots stays absolute — tests/test_results_command.py::
test_results_summary_writes_nothing_into_a_committed_root must keep passing
unchanged. Frozen surfaces: none expected (readers only). GATE: ring
(tests/test_results_command.py tests/test_findings_command.py) while iterating;
full gate at the boundary; docs_verify full against docs/AUDIT_BASELINES.md.
Map moves in the same commit (docs/map/SUB-application.md).
```
