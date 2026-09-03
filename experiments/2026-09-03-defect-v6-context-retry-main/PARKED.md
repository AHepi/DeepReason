# PARKED — found during this tranche, deliberately not worked

The scope contract: one tranche, one goal. Everything below was
observed while proving THIS goal and is left for a future runner, with
the prompt already written so starting it costs a paste.

---

## P1 — `CON-run-identity.md:298` exceeds the docs_verify ceiling even standalone

**What.** The check pairing the integrity-gate greps
(`CONTINUE_RECORD_NOT_VERIFIED`, `record_verification_refusal`,
`AMEND_RECORD_NOT_VERIFIED`) with a whole-file
`python -m pytest tests/test_jailbreak_gate.py -q` measured **346.78 s
standalone, uncontended**, against `docs_verify`'s 300 s per-check
ceiling at `tools/docs_verify.py:185`. `docs/AUDIT_BASELINES.md` rows it
as CONTAINER-CONDITIONAL, disposable by a standalone re-run; on this
container the re-run does not dispose of it, because the standalone
time is already over the ceiling. The CLAIM is sound — the check passes
when given the time, and the full gate ran the same file inside 4694
passed / 0 failed — so this is cost, not rot.

Precedent: `experiments/2026-08-31-defect-jailbreak-gate-closure`
narrowed `SUB-application.md`'s equivalent whole-file run (measured at
160-213 s) to the four node ids that exercise its claim, taking it to
1 s, and `docs/ERRATA.md` E67 records anchoring that row by what the
check RUNS rather than by a line number. This is the same defect in the
same shape, one document over.

**Ready-to-send prompt:**

```
EXECUTOR WINDOW — DEFECT TRANCHE: narrow CON-run-identity.md:298 to the
claim it tests
Read CLAUDE.md, then load deepreason-orchestrator and
dr-explain-to-operator. Base on main at or after the commit carrying
experiments/2026-09-03-defect-v6-context-retry-main/.
GOAL: CON-run-identity.md:298's check proves the same claim — the
2026-08-29 integrity gate is present in both verbs — in seconds rather
than minutes, so it stops timing out.
EVIDENCE: the check runs `python -m pytest tests/test_jailbreak_gate.py
-q` whole-file: measured 346.78 s STANDALONE and uncontended on the
2026-09-03 container, against the 300 s per-check ceiling at
tools/docs_verify.py:185. It PASSES when given the time, so the claim is
intact and this is check cost, not claim rot. docs/AUDIT_BASELINES.md
rows it as container-conditional and prescribes a standalone re-run as
the disposal; on a container this slow that disposal no longer
discriminates, which is the actual finding.
DO: follow experiments/2026-08-31-defect-jailbreak-gate-closure, which
did exactly this for SUB-application.md — identify the node ids in
tests/test_jailbreak_gate.py that exercise the integrity-gate claim,
replace the whole-file run with those node ids, and MEASURE the before
and after. Mutation-prove the narrowed check: deleting
CONTINUE_RECORD_NOT_VERIFIED (or AMEND_RECORD_NOT_VERIFIED) must still
turn it red, or the narrowing bought speed by dropping the claim.
Update docs/AUDIT_BASELINES.md in the SAME commit — the row moves from
container-conditional to a regression signal, exactly as ERRATA E67
records for SUB-application.md — and anchor it by what the check RUNS,
not by a line number.
END STATE: docs_verify's failure list is the five remaining baseline
rows; the narrowed check is mutation-proven; AUDIT_BASELINES and
docs/ERRATA.md both move in that commit. Full gate 0 failed.
NOT IN SCOPE: the other five baseline rows (SEAM-llm-x-rules.md:54 is
parked P3 at experiments/2026-08-29-fix-docs-verify-multiline-checks/;
INV-frozen-surfaces.md:181 is parked P-D3 at
experiments/2026-08-30-fix-rotted-map-checks/; the three
CON-run-identity git-history rows are shallow-clone environment
preconditions, not defects). Do not touch the jailbreak gate's own
behaviour — this is a check-cost tranche, and the gate is the
2026-08-29 security clause.
```
