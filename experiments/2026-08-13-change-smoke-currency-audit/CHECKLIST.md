# Checklist: wheel-smoke re-pin + instrument currency audit

State: complete. See DELIVERY.md for the reconciliation and final report.

## Step 1 — Part 1: run both smokes as-is, capture output

Done-criterion: verbatim stdout/stderr from both instruments on branch
tip `074ef1549`, pasted.

```
$ python scripts/wheel_smoke.py
wheel smoke passed: isolated V6-only contents, clean imports, exact entry
points, module parity, MCP registration, and exact MCP schemas
```

```
$ python -u scripts/wheel_operational_smoke.py
wheel operational smoke passed: installed setup, explicit qualification
(80 qualification calls; 418 total calls), readiness, question-only
reasoning, replay-verified terminal retrieval, cache reuse, opaque MCP
restart, budget ceiling, and pre-V6 fail-closed admission
```

**Finding: both instruments pass cleanly on first execution.** No
failure was reproduced. This contradicts the operator's diagnosis
("smoke is behind again... failing big time") as of THIS branch tip —
recorded honestly per CLAUDE.md ("model prose is never evidence... the
record is"). Step 2 below still does the full direct-extraction
reconciliation the tranche asked for, since a passing smoke run only
proves the instrument's OWN assertions hold, not that every pin is
independently correct (two wrong numbers can still compare equal).

## Step 2 — Part 1: direct-extraction reconciliation of all four pin locations

Done-criterion: every pin traced to a live value, not eyeballed.

Console entry points (`pyproject.toml` `[project.scripts]` /
`[project.entry-points."deepreason.admission.adapters"]`) — byte-compared
against `scripts/wheel_smoke.py`'s `REQUIRED_ENTRY_POINT_GROUPS`: exact
match, both groups, both entries each.

MCP tool-name set, direct extraction:

```
$ python3 -c "
import json, hashlib
from deepreason.mcp_server import _tools
tools = _tools()
names = sorted(t['name'] for t in tools)
print('COUNT', len(names))
print('NAMES', names)
encoded = json.dumps(tools, sort_keys=True, separators=(',', ':')).encode()
print('SHA256', hashlib.sha256(encoded).hexdigest())
"
COUNT 21
NAMES ['amend_run', 'bridge_claims', 'bridge_result', 'bridge_status',
'cancel_run', 'continue_run', 'get_capabilities', 'get_help_topic',
'get_readiness', 'get_request_requirements', 'run_findings', 'run_result',
'run_status', 'scratch_attention', 'scratch_map', 'scratch_open',
'scratch_related', 'scratch_search', 'start_bridge', 'start_run',
'validate_intake']
SHA256 ebd7397074c3aa9640658e74fc0d56f16d2a11f1b6898b7887c961f79c04e17e
```

Compared against all four pin locations:

| Location | Tool-name set | Schema sha256 |
|---|---|---|
| `scripts/wheel_smoke.py` `EXPECTED_MCP_TOOLS` | identical (21/21) | `ebd739...4e17e` — match |
| `scripts/wheel_operational_smoke.py` `EXPECTED_MCP_TOOLS` | identical (21/21) | `ebd739...4e17e` — match |
| `tests/test_mcp.py` `SUPPORTED_TOOLS` | identical (21/21) | n/a (no schema pin there) |
| `tests/test_mcp_help.py` `SUPPORTED_TOOL_NAMES` | identical (14 named + `*HELP_TOOL_NAMES`) | n/a |

Required wheel modules (`scripts/wheel_smoke.py` `REQUIRED_MODULES`,
`scripts/wheel_operational_smoke.py`'s narrower six-module subset):
every named file confirmed present on disk (`deepreason/__main__.py`,
`provider_profile.py`, `qualification.py`, `preparation.py`,
`readiness.py`, `mcp_registration.py`, `shallow.py`,
`minireason/__init__.py`, `minireason/loop.py`).

**Verdict: no pin is stale. All four locations agree with each other and
with the live surface, byte for byte.** No re-pin is needed; R3/R4 are
satisfied by this reconciliation standing in place of a fix (there is
nothing to fix). `test_mcp.py`/`test_mcp_help.py` were also run directly
to confirm: `89 passed in 1.22s`.

## Step 3 — Part 2: same-commit attribution scan

Done-criterion: scan command + full output pasted; every touched commit
judged violation/not, with the reason.

```
$ git log --oneline a9d9b31a3..HEAD -- scripts/wheel_smoke.py \
    scripts/wheel_operational_smoke.py tests/test_mcp.py \
    tests/test_mcp_help.py src/deepreason/mcp_server.py \
    src/deepreason/intake_form.py src/deepreason/cli/main.py pyproject.toml
e9a1a878c Claude/all configs allowed r54a3b (#11)
```

Only one commit in the range touches any of the eight named files.
Full commit range since `a9d9b31a3` (2026-08-12 11:03, "remove token
ceiling") is six commits:

```
074ef1549 Grounded-extension run: operator-authored run-config.yaml (verbatim)
6e1623db2 Claude/calibration receipt notice b6wp3k (#14)
85717580f Claude/v6 defended trial wiring 07hs1u (#13)
5683bc404 Claude/skills overhaul vk2n8d (#12)
49486fe5f authoring-skills: operator-supplied authority for the skills overhaul
e9a1a878c Claude/all configs allowed r54a3b (#11)
```

Judged individually against what the pins actually track (console entry
points, the MCP tool-name set, the MCP schema shape, required wheel
modules — NOT arbitrary internal behavior):

- **e9a1a878c** — touches `src/deepreason/cli/main.py` and
  `src/deepreason/intake_form.py`, neither a pin file. Diff read in
  full: removes the `JUDGE_FAMILY_AND_BLIND_SAME_MODEL_CONFLICT` CLI
  refusal (replaced by a printed `NOTICE` line) and changes
  `validate-intake`'s exit code for semantic-only violations (1 → 0);
  `intake_form.py` drops a cross-group seat-conflict validator. None of
  this adds, removes, or renames a console entry point, an MCP tool, the
  MCP schema shape, or a required wheel module — the `IntakeFormV1`
  field set (which `_intake_form_schema()` feeds into the MCP
  `validate_intake` tool's `inputSchema`) is unchanged, confirmed by the
  schema-sha256 match in Step 2. **Not a violation** — this commit did
  not touch anything the pins cover.
- **074ef1549, 6e1623db2, 85717580f** — touch `src/`
  (`run_manifest.py`, `authority.py`, `cli/doctor.py`,
  `informal/trial.py`, `rules/crit.py`, `workflow/*.py`) but none of
  these files are console entry points, MCP tool registrations, or
  wheel-module pins; `cli/doctor.py` is not `cli/main.py` and adds no
  console script. **Not a violation** — out of the pins' scope by
  construction (confirmed: none of these three commits appear in the
  filtered `git log` above, i.e. they did not even touch the eight named
  files).
- **5683bc404, 49486fe5f** — skills/docs only (`.claude/skills/`,
  `CLAUDE.md`, `docs/ERRATA.md`, experiment ledgers). No `src/` change
  at all. **Not a violation.**

**Verdict: zero same-commit violations found in the scanned range.**
The scan command and its complete output are the proof; R5/R6 are
satisfied by this negative result. No `docs/ERRATA_EXECUTOR.md` entry is
written — the ledger's own entry discipline records confirmed
violations, and appending a "nothing found" entry would misrepresent an
absence of evidence as a finding. The scan command + this reasoning
chain stand as the record instead, per REQUEST.md R6's own fallback
("the scan command and output are the proof either way").

## Step 4 — Part 3a: root_sweep.py full-tree run

Done-criterion: every committed root swept (minus the excluded hang
root), compared against the last committed sweep, verdict drift
attributed to a named reader change or explicitly none found.

**Exclusion.** `experiments/live_tri_2026-07-27/run-c5ab654afd1b4aa131aede83bdca0f03`
is excluded by a path filter in a scratch wrapper copy of
`tools/root_sweep.py`'s exact per-root logic (not a change to the
committed tool) — not diagnosed here, per instruction. 103 roots
discovered on disk; 102 swept, 1 excluded.

**Performance finding, not a silent workaround.** The FIRST attempt ran
`tools/root_sweep.py`'s logic serially, exactly as committed, and was
killed by a 45-minute wall-clock guard at 34/102 roots — individual
roots were taking 30-125 seconds EACH (`experiments/2026-08-04-change-
rung5-dumb-alternative-backend/ab-home` root: 47.5s; `.../overnight-
omnibus/block-a-criticism-symmetry/...run-bf30545893...`: 125.7s), far
slower than any documented prior run. This is a second, separate
"instrument currency" finding beyond the one named hang root: general
sweep throughput has degraded, which plausibly explains the operator's
"the workflow is failing big time" as much as any pin drift does. NOT
diagnosed or fixed here (out of this tranche's scope — pin/instrument
currency, not `src/` performance); PARKED below (P1) as a ready-to-send
investigation prompt. Worked around, for THIS run only, by parallelizing
the independent, read-only per-root checks across 4 worker processes
(each root's `verify_root_report`/`Harness(read_only=True)` touches only
its own directory — safe to parallelize; `tools/root_sweep.py` itself is
untouched). Completed in `SWEEP COMPLETE: 102 roots` well inside a
50-minute budget.

**Verdict comparison.**

```
11 ERROR (all UnsupportedRunManifestVersionError) — baseline: 11. MATCH.
83 valid=True — baseline 84, minus 1 for the excluded root = 83. MATCH.
8 valid=False — baseline: 8. MATCH.
102 total swept (103 discovered - 1 excluded).
```

Line-by-line diff against the last COMMITTED raw sweep file
(`experiments/2026-08-12-change-all-configs-allowed/root-sweep-after-
all-configs-allowed.txt`, pre-dating both `85717580f` and `6e1623db2`'s
reader changes), whitespace-normalized, hang root excluded from the old
file:

```
$ diff <(grep -v "^experiments/live_tri_2026-07-27/run-c5ab654afd1b4aa131aede83bdca0f03 " \
    experiments/2026-08-12-change-all-configs-allowed/root-sweep-after-all-configs-allowed.txt \
    | sed 's/  */ /g' | sort) \
  <(sed 's/  */ /g' root-sweep-after-2026-08-13.txt | sort)
(no output)
$ echo $?
0
```

**Zero bytes of difference, per-root, across every column** (valid,
epistemic_checks_passed, att count, blind count, modules, module
digests, seats, seat digests) for all 102 swept roots. **No verdict
moved.** Two reader changes landed in the interim —
`85717580f` (v6 defended-trial wiring, `run_manifest.py` +
`rules/crit.py` + `workflow/*.py`) and `6e1623db2` (calibration-receipt
notice, `authority.py` + `run_manifest.py`, converting a compile-time
refusal to a disclosure notice) — and neither moved a single committed
root's verdict. This is the complete, re-derived answer to REQUEST.md
R7's "which reader change moved which verdict": **none did**. Raw output
committed as `root-sweep-after-2026-08-13.txt` alongside this file.

## Step 5 — Part 3b: docs_verify full, --audit, --links

Done-criterion: all three modes run, compared against the documented
baseline.

```
$ python tools/docs_verify.py
docs_verify [full]: 53 documents, 861 checks, 4 workers
  FAIL CON-run-identity.md:195: ... (shallow-clone git log check)
  FAIL CON-run-identity.md:197: ... fatal: ambiguous argument '1637e808'
  FAIL CON-run-identity.md:199: ... fatal: ambiguous argument 'f304fec1'
docs_verify: 3 failed
EXIT: 1
```

```
$ python tools/docs_verify.py --audit
docs_verify --audit: 0 finding(s)
EXIT: 0
```

```
$ python tools/docs_verify.py --links
docs_verify --links: 0 dangling reference(s), 53 document(s)
EXIT: 0
```

**Verdict: matches the documented baseline exactly** (CLAUDE.md: "3
pre-existing CON-run-identity.md shallow-clone failures") — all three
failures are the same shallow-clone `git log`/`git show` checks over
commits this container's clone does not carry, named identically to the
2026-08-13-change-defended-trial-wiring tranche's own baseline run.
`--audit` and `--links` both clean. **0 unexplained deviation.**

## Step 6 — Part 3c: full pytest gate, once

Done-criterion: one run, compared against the documented baseline,
MCP-thread failures isolated before attribution.

```
$ python -m pytest tests/ -q -n 4
FAILED tests/test_bronze_report.py::test_census_totals_internally_consistent
  assert counts["gate_blocked"] == census["streams"][stream]["gate_measures"]
  assert 159 == 165
1 failed, 3539 passed, 7 skipped in 775.26s (0:12:55)
EXIT: 1
```

**Verdict: matches the documented baseline exactly** (CLAUDE.md: "1
pre-existing test_bronze_report failure"; same `159 == 165` assertion as
the 2026-08-13-change-calibration-receipt-notice tranche's own
VALIDATION.md run). Grepped the full log for any MCP/thread-named
failure: zero matches — none of the 5 documented known-flaky
MCP-thread tests failed this run, so no isolation re-run was needed.
**0 unexplained deviation.**

## Summary — what moved, what did not, what was excluded

| Instrument | Result | vs. baseline |
|---|---|---|
| `wheel_smoke.py` | passed, first try | no re-pin needed |
| `wheel_operational_smoke.py` | passed, first try | no re-pin needed |
| 4-location pin reconciliation (direct extraction) | all agree | no drift found |
| same-commit attribution scan (`a9d9b31a3`..HEAD) | 1 touching commit, not a violation | 0 violations |
| `root_sweep.py` (102/103 roots, 1 excluded) | byte-identical to last committed sweep | 0 verdicts moved |
| `docs_verify` full/--audit/--links | 3/0/0 | matches documented baseline |
| full pytest gate | 1 failed/3539 passed/7 skipped | matches documented baseline |

**Excluded:** `experiments/live_tri_2026-07-27/run-c5ab654afd1b4aa131aede83bdca0f03`
(pre-existing parked performance defect — not diagnosed).

**What moved:** nothing verdict-wise. The one thing that DID change is
process, not outcome: `root_sweep.py`'s serial per-root cost is now high
enough (30-125s/root) that a straight re-run needs either a much longer
budget or parallelization — parked as P1 in `PARKED.md`.

State: all steps complete.
