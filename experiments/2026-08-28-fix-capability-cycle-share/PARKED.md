# PARKED — found in this tranche, not fixed in it

One tranche, one goal. Each entry is written for its future runner: what it
is, and a prompt to paste.

---

## Q1 — `docs_verify` silently never runs 67 of the map's 1 210 checks

**What.** `tools/docs_verify.py` parses a `check:` LINE BY LINE
(`parse_text`, line 75, against `_CHECK = re.compile(r"^`check:\s*(?P<cmd>.+?)`\s*$")`
at line 47). A check whose command spans several lines — the shipped style for
every `python -c "` block in the map — never matches, is never collected, and
is never reported as missing. It is not a failure and not a skip; it is
absence. `docs_verify --audit` cannot see it either, because `--audit` iterates
the same already-truncated `doc.checks`.

Census, run on this tranche's tree:

    check: lines at column 0: 1210; parsed by docs_verify: 1143; DROPPED: 67

Worst affected: `INV-axiom-basis.md` 8, **`INV-frozen-surfaces.md` 7**,
`INV-render-layout.md` 7 (of 11), `SUB-calculus.md` 6,
`INV-evidence-channels.md` 5 (of 10), `SEAM-llm-x-verification.md` 3 (of 4),
`SCHEMA.md` 1 (of 2). Four documents have MOST of their checks dropped. The
document that owns the frozen-surface list has seven claims that nobody has
re-derived since they were written.

This tranche flattened its own two new checks to single lines and mutation-
proved both rather than adding to the pile; it did not touch the tool, which is
another window's file and a different goal.

**Ready-to-send prompt:**

```
Route: deepreason-orchestrator (DEFECT tranche).

Goal, one sentence: make `docs_verify` run every `check:` block in the map,
including the multi-line ones it currently drops without saying so.

Evidence, committed:
  experiments/2026-08-28-fix-capability-cycle-share/PARKED.md section Q1
  tools/docs_verify.py:47   _CHECK, anchored ^...$ against a single line
  tools/docs_verify.py:75   parse_text, iterating text.splitlines()
  tools/docs_verify.py:380  --audit, iterating the same truncated list

Reproduce it in one command before designing anything:
  python -c "
import sys, pathlib, re; sys.path.insert(0,'tools'); import docs_verify as dv
L=P=0
for f in sorted(pathlib.Path('docs/map').glob('*.md')):
    t=f.read_text(); L+=len(re.findall(r'(?m)^\`check:', t)); P+=len(dv.parse_text(t,str(f)).checks)
print(L, P, L-P)"
It prints 1210 1143 67 on 90b1347f4 plus this tranche.

The design question to answer FIRST: a multi-line check is a BLOCK, and a
parser that accepts blocks must also decide what closes one. Read
docs/map/SCHEMA.md's own statement of the check syntax before choosing --
SCHEMA.md is itself one of the affected documents (1 of its 2 checks is
dropped), so the syntax as documented and the syntax as parsed already
disagree, and which one is authoritative is the operator's call if the answer
is not obvious from SCHEMA.md.

Expect the 67 newly-collected checks to include some that FAIL. That is the
point and it is not this change's defect: report them, park each as its own
finding, and do NOT fix map claims inside this tranche. Run
`python tools/docs_verify.py --self-test` -- it currently asserts the
single-line behaviour at tools/docs_verify.py:406-409 and will need a case for
blocks.

End state: every `check:` at column 0 is collected; a check the parser cannot
understand is REPORTED, never dropped; --audit sees the full set; --self-test
covers a block; the newly-red checks are parked, not patched; full gate 0
failed.
```

---

## Q2 — the manifest echo still drops the two attention knobs (audit P10)

**What.** `run_manifest.py:2386-2387` pops `SEED_PROBLEM_BUDGET_FLOOR` and
`ATTENTION_ALLOCATION_POLICY` from the versioned-source echo, so a
`--run-manifest` launch rebuilds them at their defaults. P-T1 epoch 6 got the
wander cap only because the defaults are on; a run that deliberately set a
different floor or selected `open-lineage.v1` would have lost it silently,
exactly as audit finding F-A's five switches were lost.

This tranche did NOT need it — its regression tests set the floor on `Config`
directly — and `run_manifest.py` belongs to the parallel manifest window. It
is recorded here because the fix landing here makes the knob WORTH setting: a
share that now reads honestly is a share an operator may want to configure.

**Ready-to-send prompt:** this is audit finding P10, already parked with a
prompt at `experiments/2026-08-28-audit-run-problems/PARKED.md` §P10. Add to
it, when it is taken: the two attention knobs above join P10's five switches,
and `tests/test_wander_cap.py`'s P12 block is the suite that shows what a run
does with them once they arrive.

---

## Q3 — the audit probe field `cycles_that_bypassed_the_cap` reads 0 for a run
## where 20 of 24 cycles bypassed the cap

Corrected on the record rather than parked as work: `docs/ERRATA.md` E57. No
action is owed; the audit's verdict was reached on the correct field.
