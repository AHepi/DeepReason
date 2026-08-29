# PARKED — noticed in this tranche, deliberately not fixed

## PT2-A — nine roots whose nonzero spend figure is smaller than their own log

**What.** The census this tranche ran over all 59 committed roots with a
`run-status.json` (`proof/committed_zero_spend_census.txt`) separates the
disagreements into TWO classes. The first — 20 roots reporting `0` against a
real log — is this tranche's defect and is fixed. The second is nine roots
carrying a NONZERO figure that is smaller than their own log's sum
(`proof/nonzero_disagreements.txt`):

```
status_spend   log_spend  calls  root
      90700      119659     29  experiments/live_engaged_2026-07-27/run-f4fa6663e5412d64df943a5a22342baf
     314308      351440     57  experiments/live_research_2026-07-29/narrow/runs/run-7d8723fbe8626c71db880826c244d332
      89385      109935     17  experiments/live_research_2026-07-29/wide/runs/run-5a771259557378224bd68591483817be
     191871      251938     49  experiments/live_tri_2026-07-27/run-15a53aca8a6fc66a39f382fc688c5346
      88966      123845     21  experiments/live_tri_2026-07-27/run-6dab80d615a437a8b3fa489a279df847
      94560      110295     21  experiments/live_tri_2026-07-27/run-9ae94bb478990cbecca373fc3bcb1345
     193361      220682     36  experiments/live_tri_2026-07-27/run-ac1836b6237b6e9d80b3b0cb492b39f5
     178613      244198     22  experiments/live_tri_2026-07-27/run-c5ab654afd1b4aa131aede83bdca0f03
     192000      330396     26  experiments/live_tri_2026-07-27/run-faa5feae126bc2558ea9c6d8d200a90c
```

Every one under-reports, none over-reports, and all nine are July-2026
roots — which is a shape, not noise. Not fixed here because the cause is
different in kind: those sidecars hold a REAL measurement that is merely
stale, where this tranche's defect is an omission asserting a zero that was
never measured. This tranche's reader half is scoped so it does not silently
re-adjudicate them, and a regression pins that scope
(`test_a_nonzero_sidecar_figure_is_reported_as_recorded_and_not_re_derived`).

**Ready-to-send prompt:**

```
Route: deepreason-orchestrator (defect).

Goal, one sentence: establish which of a run's token instruments is
authoritative when two of them disagree by a real margin, and make
`deepreason results` report that one -- so a spend figure an operator uses
to price a configuration cannot silently under-report by 30%.

What is already settled, so do not re-derive it:
  - The FALSE-ZERO class (20 of 59 roots reporting 0 against a real log) is
    FIXED: experiments/2026-08-29-fix-failure-path-token-spend/. Its reader
    consults the log ONLY where the sidecar says zero, precisely so this
    question stayed open rather than being answered by accident. That scope
    is pinned by a regression -- widening it is the thing to do here, but do
    it deliberately and with the evidence, not by deleting the guard.
  - The census instrument exists and is cheap: that tranche's
    proof/committed_zero_spend_census.txt compares every committed root's
    run-status.json against its own log.jsonl in ~2 minutes.

The question to answer first, because it decides the shape of the fix: is
the sidecar STALE (written before the run's last calls landed) or is it
SCOPED (counting a subset of calls the log also carries -- one epoch, one
profile, one role group)? A stale figure is a writer-ordering defect; a
scoped one means two instruments are measuring different things and the
surface is comparing them wrongly. Diff the per-call events of ONE root
(run-f4fa6663, 29 calls, 90700 vs 119659 -- the smallest) against its
progress.jsonl sequence; if the sidecar equals the log sum truncated at some
seq, it is staleness, and the seq says where.

Note all nine are July-2026 roots. Check whether the writer path changed
after that date before concluding the defect is live -- if it is already
fixed, the finding is that the READER still reports the stale figure for
those roots, which is a smaller and different change.

Evidence pointers:
  experiments/2026-08-29-fix-failure-path-token-spend/proof/nonzero_disagreements.txt
  experiments/2026-08-29-fix-failure-path-token-spend/proof/committed_zero_spend_census.txt
  experiments/2026-08-29-fix-failure-path-token-spend/DIAGNOSIS.md (the
      two-class separation, and why only one class was fixed)
  docs/RUN_ANATOMY_SYNTHESIS_2026-08-26.md organ 10 -- "three token
      instruments, 27 disagreements", rated HARMFUL-AS-WIRED, parked as W6-P1
  src/deepreason/application/results.py::_token_spend (the scoped reader)
  DR-SUB-application; DR-INV-frozen-surfaces FIRST (forecast: no contact)

End state: the authoritative instrument is named with evidence rather than
chosen; results reports it; the nine roots' reported figures are explained
(whether or not they change); a regression would fail today; full gate 0
failed; map moved in the same commit.
```

---

## PT2-B — 66 map checks are silently never run, and the tool's own count hides it

**Reported by the operator mid-tranche, 2026-08-29, and CONFIRMED here.**
Not fixed: `tools/docs_verify.py` is outside this window's declared cone, and
this is neither tranche's goal.

**What.** `tools/docs_verify.py:47` is
`_CHECK = re.compile(r"^`check:\s*(?P<cmd>.+?)`\s*$")`, applied per LINE at
`:75` (`_CHECK.match(line)`). A `check:` whose command does not CLOSE its
backtick on the same line matches nothing. It is dropped with no warning, no
error, and no place in the count.

**Measured** (`proof/dropped_checks_census.py`, read-only, ~1 s):

```
column-0 `check: lines           : 1209
SILENTLY DROPPED by the parser   :   67  across 25 documents
actually run                     : 1142
```

One of the 67 (`SCHEMA.md:159`) is prose quoting a check inside a sentence,
so **66 are real, intended checks that have never run.**

**Why this is worse than 66 missing checks.** Three compounding reasons:

1. **The tool's own count is the post-drop number.** `docs_verify` prints
   "1142 checks" — exactly 1209 − 67. Nothing in its output, at any verbosity,
   distinguishes "1142 checks, all we have" from "1142 of 1209, 67 discarded".
2. **`--audit` cannot see them.** That mode exists to refuse checks that
   cannot fail — but it can only judge checks it PARSED. A check that never
   parsed is invisible to the one instrument designed to catch checks that
   prove nothing. The integrity mode has a blind spot exactly where the
   integrity is worst.
3. **The affected documents are the load-bearing ones.**
   `INV-frozen-surfaces.md` carries **7** of the 66 — and the map's own
   reading order sends every designer there FIRST, before anything else, to
   learn what they may not change. `SUB-calculus.md` carries 6,
   `INV-axiom-basis.md` 8, `INV-render-layout.md` 7,
   `INV-evidence-channels.md` 5. The dropped shape is dominated by
   `` `check: python -c " `` — a multi-line `python -c` heredoc — which is
   precisely the form a check takes when the claim is too structural for a
   grep. **The harder the claim, the more likely its check never ran.**

CLAUDE.md states the map's whole epistemology as "documents are authenticated
by RE-DERIVATION, not by signature… this proves the sentence is still true,
which is the property that decays." 66 sentences carry a check that has never
been able to prove anything, and 7 of them are in the frozen-surfaces
document.

**Not yet known, and worth measuring before choosing the fix:** how many of
the 66 would PASS if run. A fix that turns them on may go straight to a large
red count — that is a discovery about the tree, not a reason to leave them
off, but it changes the tranche's shape from "parser fix" to "parser fix plus
a triage of what it reveals", and the runner should budget for it.

**Ready-to-send prompt:**

```
Route: deepreason-orchestrator (defect). High value: this is a defect in the
instrument that authenticates the map, so every tranche that "moved the map in
the same commit" since these checks were written has been trusting a green
docs_verify that never evaluated them.

Goal, one sentence: every column-0 `check: line in docs/map/ is either RUN or
REPORTED as unrunnable -- so a check can no longer be silently discarded, and
docs_verify's count stops overstating what it verified.

Reproduce (read-only, ~1 second, no setup):
  python experiments/2026-08-29-fix-failure-path-token-spend/proof/dropped_checks_census.py
    -> 1209 column-0 `check: lines, 67 dropped across 25 documents, 1142 run
    -> 1142 is EXACTLY what `python tools/docs_verify.py` prints as its
       check count, which is the whole problem: the count is the post-drop
       number, so nothing reveals the gap.

The cause, already traced -- do not re-derive it:
  tools/docs_verify.py:47  _CHECK = re.compile(r"^`check:\s*(?P<cmd>.+?)`\s*$")
  tools/docs_verify.py:75  applied per LINE via _CHECK.match(line)
  A check whose command does not close its backtick on the same line matches
  nothing and is dropped without warning. 66 of the 67 are real checks; the
  67th (SCHEMA.md:159) is prose quoting a check inside a sentence, and a fix
  must keep NOT running that one.

Two decisions to make, in this order, and they are the whole design:

  1. FAIL LOUD FIRST, before making anything run. The minimal, safest change
     is that an unclosed column-0 `check: line is a docs_verify ERROR naming
     the file and line -- never a silent skip. Ship that alone if the second
     decision needs the operator: it converts an invisible hole into a visible
     one, which is strictly better and cannot break a passing check.
  2. THEN decide whether multi-line checks become legal. SCHEMA.md currently
     says a check "rides its own line ... at COLUMN 0", and the column rule is
     load-bearing: it is what lets SCHEMA.md show worked examples inside
     indented code blocks without the verifier running them. So either
       (a) multi-line checks stay ILLEGAL and all 66 are rewritten to one
           line (they are mostly `python -c "` heredocs -- a `python -c` with
           semicolons, or a committed probe script under tools/, both fit on
           one line), or
       (b) the grammar gains an explicit terminator and SCHEMA.md is amended
           in the same commit.
     Do not silently start executing 66 commands that have never run: turn
     them on deliberately, and expect some to be RED. A check that goes red
     when first run is a claim that decayed unnoticed -- report each one, do
     not "fix" it by weakening the check.

Also fix, in the same tranche, because it is the same wound:
  --audit refuses checks that CANNOT FAIL, but only among checks it PARSED.
  Whatever the fix, --audit must account for unparsed lines too, or the
  integrity mode keeps its blind spot exactly where integrity is worst.

Blast radius, stated so it is not discovered late: INV-frozen-surfaces.md has
7 dropped checks, INV-axiom-basis.md 8, INV-render-layout.md 7,
INV-evidence-channels.md 5, SUB-calculus.md 6. These are the documents the
map's reading order puts FIRST.

Evidence pointers:
  experiments/2026-08-29-fix-failure-path-token-spend/proof/dropped_checks_census.py
  experiments/2026-08-29-fix-failure-path-token-spend/proof/dropped_checks_census.txt
      (the full 67-line list, by document and line number)
  tools/docs_verify.py:47, :75          the parser and where it is applied
  docs/map/SCHEMA.md "### Checks"       the grammar this must stay true to
  CLAUDE.md "The map"                   "authenticated by RE-DERIVATION"

End state: an unclosed `check: line fails docs_verify loudly with its file and
line; the count distinguishes parsed from dropped; every one of the 66 is
either running or explicitly recorded as retired with a reason; --audit sees
unparsed lines; SCHEMA.md states whichever grammar wins, in the same commit;
a regression over a fixture document with an unclosed check would fail today;
full gate 0 failed.
```
