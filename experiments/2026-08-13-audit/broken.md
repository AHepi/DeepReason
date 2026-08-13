# broken.md — 2026-08-13 audit

Instruments run per `dr-audit-broken`; deltas compared to
`docs/AUDIT_BASELINES.md` § Instruments (recorded 2026-08-12 at main
`074ef1549`).

| id | dimension | target | gate | verdict | proof file | disposition |
|---|---|---|---|---|---|---|
| B1 | broken | full pytest gate | pass | baseline | proof/broken-pytest.txt | baseline |
| B2 | broken | docs_verify (default) | pass | baseline | proof/broken-docsverify.txt | baseline |
| B3 | broken | wheel_smoke.py | pass | baseline | proof/broken-wheelsmoke.txt | baseline |
| B4 | broken | wheel_operational_smoke.py | pass | baseline | proof/broken-wheeloperational.txt | baseline |
| B5 | broken | root_sweep.py census | pass | baseline (unchanged reader, unchanged answer) | proof/broken-sweep-comparison-2026-08-12.txt | baseline |
| B6 | broken | `tools/root_sweep.py` CLI vs `dr-audit-broken`'s documented invocation | pass (instrument itself, not a target file) | broken | proof/broken-sweep.txt | parked |

## Detail

**B1 — full pytest gate.** `python -m pytest tests/ -q -n 4`:
`3539 passed, 7 skipped, 1 failed` — the one failure is
`tests/test_bronze_report.py::test_census_totals_internally_consistent`,
`assert 159 == 165`, matching the baseline's parked failure verbatim
(same assertion, same numbers). None of the baseline's known-flaky
`test_mcp_run.py` / `test_mcp_scratch_bridge.py` tests failed this
run. **Verdict: baseline.**

**B2 — docs_verify (default).** `python tools/docs_verify.py`:
`53 documents, 861 checks, 4 workers`, `3 failed` — all three are
`CON-run-identity.md` git-history checks (lines 195, 197, 199),
matching the baseline's "3 pre-existing failures, all
`CON-run-identity.md` git-history checks... on a full clone the
expected value is 0 failed" note (this clone is not a full/unshallowed
clone, same as the baseline's recorded condition). **Verdict:
baseline.**

**B3 — wheel_smoke.py.** Exit 0: "isolated V6-only contents, clean
imports, exact entry points, module parity, MCP registration, and
exact MCP schemas". **Verdict: baseline** (expected exit 0; the
baseline's "known stale, re-pin tranche in flight" note does not
apply — no MCP-schema-sha or tool-set-pin failure occurred).

**B4 — wheel_operational_smoke.py.** Exit 0: "installed setup,
explicit qualification (80 qualification calls; 418 total calls),
readiness, question-only reasoning, replay-verified terminal
retrieval, cache reuse, opaque MCP restart, budget ceiling, and
pre-V6 fail-closed admission". **Verdict: baseline.**

**B5 — root_sweep.py census.** Two direct invocations were attempted
(both saved in `proof/broken-sweep.txt`):

1. The `dr-audit-broken` skill's documented command,
   `timeout 900 python tools/root_sweep.py > proof/broken-sweep.txt`
   — crashed immediately, `IndexError: list index out of range`. The
   installed `tools/root_sweep.py` requires an explicit output-path
   *argument* (`sys.argv[1]`), not stdout redirection. See B6.
2. The corrected invocation,
   `timeout 900 python tools/root_sweep.py <path>` — killed by the
   900 s timeout (`exit 124`) without writing any output.
   `root_sweep.py` accumulates every root's line in memory and calls
   `out.write_text(...)` exactly once, after the loop finishes, so a
   hang on any single root loses the whole sweep's output, not just
   that root's row. This reproduces the baseline's documented "known
   hang" (`experiments/live_tri_2026-07-27/
   run-c5ab654afd1b4aa131aede83bdca0f03`) — the timeout fired, and
   that root is exactly the one the baseline names as expected to
   hang, so this is confirmation, not a new finding.

Per CLAUDE.md's own instruction ("A committed root is immutable, so
its verdict can only move if the READER moved; when no reader
changed, the previous sweep IS the current answer" / "The 42-root
sweep obeys the same rule"): `tools/root_sweep.py` was last modified
2026-08-11 (`48506b4e0`) and is byte-identical between the baseline's
recording commit (`074ef1549`, 2026-08-12) and this audit's `HEAD`
(`git diff 074ef1549 HEAD -- tools/root_sweep.py` is empty). The
newest committed sweep,
`experiments/2026-08-12-change-all-configs-allowed/
root-sweep-after-all-configs-allowed.txt` (copied in as
`proof/broken-sweep-comparison-2026-08-12.txt`), is therefore still
the current answer: 103 rows, 11 `ERROR` lines, all
`UnsupportedRunManifestVersionError` on pre-v6 schema roots — matching
the baseline's "11 ERROR lines, all `UnsupportedRunManifestVersionError`"
exactly, row for row. **Verdict: baseline** (via unchanged-reader
carry-forward, not fresh re-derivation — re-deriving would require
either the known hang to be fixed/parked-around or the hanging root
to be excluded, neither of which this read-only audit may do).

**B6 — instrument invocation mismatch.** `.claude/skills/
dr-audit-broken/SKILL.md` step 5 documents
`timeout 900 python tools/root_sweep.py > proof/broken-sweep.txt`
(stdout redirection, no argument). The actual `tools/root_sweep.py`
(unchanged since 2026-08-11) requires `sys.argv[1]` as an output-path
argument and crashes with `IndexError` if invoked as documented. This
is not itself a defect in `root_sweep.py` — the script's own file
header ("Re-run verbatim before and after") implies a stable, argument
based CLI — but the *skill's documented command* is stale relative to
it. **Verdict: broken** (instrument invocation, per the worker's own
Outlets: "Instrument itself crashes → row verdict `broken`, target =
instrument, PARK"). **Disposition: parked** — see `PARKED.md` P-B6.
