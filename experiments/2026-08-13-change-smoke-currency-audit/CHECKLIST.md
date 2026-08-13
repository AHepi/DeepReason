# Checklist: wheel-smoke re-pin + instrument currency audit

State: executing.

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
