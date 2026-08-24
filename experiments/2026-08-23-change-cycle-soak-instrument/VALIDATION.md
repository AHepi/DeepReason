# VALIDATION — offline cycle soak instrument

Verdict: **PASS**.

## Full pytest gate (boundary, R9)

```
$ python -m pytest tests/ -q -n 4
3875 passed, 6 skipped in 938.34s (0:15:38)
[exited with code 0]
```

**3875 passed, 0 failed.** Baseline (`docs/AUDIT_BASELINES.md`) requires 0
failed and nothing else; met. No test was weakened, and no fixture was
touched — this tranche changes zero `src/` files and adds zero tests, by
design (S3: no gate runs the soak).

## docs_verify (full mode, R9)

```
$ python tools/docs_verify.py
docs_verify [full]: 63 documents, 994 checks, 4 workers
  FAIL CON-run-identity.md:200  (git log over retired selfstudy roots)
  FAIL CON-run-identity.md:202  -> fatal: ambiguous argument '1637e808': unknown revision
  FAIL CON-run-identity.md:204  -> fatal: ambiguous argument 'f304fec1': unknown revision
docs_verify: 3 failed
```

**3 failed — exactly the recorded baseline, no delta.** AUDIT_BASELINES.md:
"3 pre-existing failures, all `CON-run-identity.md` git-history checks — they
require an unshallowed clone; on a full clone the expected value is 0 failed."
This session's checkout is `git clone --depth 1`, and the failures name
`unknown revision` for two commits absent from a shallow pack — the shallow
symptom precisely. None of the three touches a document this tranche edited.

Full mode was used, not `--fast`: `--fast` reuses cached results and cannot
catch a document a change just broke. The two instruments were run ONE AT A
TIME (dr-drive-harness §5b — concurrent fan-out manufactures failures).

## Instrument self-check

Deterministic across repeated runs, which is what makes it usable as a gate
on a launch:

| invocation | runs | outcome | exit |
|---|---|---|---|
| `--cycles 8` | soak8, soak8b | `operational_failure` / reservation bound, cycle 1; `verify_root` 0 violations | 3, 3 |
| `--cycles 8 --induce-repairs 2` | soakrep2, soakrep3 | 1 repair; `verify_root` 1 violation, `workflow-call-pairing` at seq=24 | 1, 1 |
| `--cycles 1` | probe | `completed` / `budget_exhausted`; `verify_root` 0 violations | 1 (A4 only, by construction) |

Byte-identical seam dispositions and violation details across each repeated
pair.

## S3 placement checks

```
$ grep -rn "cycle_soak" tests/
(no output — no pytest gate runs the soak)
```

Script and all three documentation edits land in ONE commit, per R5. The
earlier standalone script commit was squashed into it rather than left as a
separate "update docs" commit — CLAUDE.md's own rule is that the separate
docs commit is the one that gets dropped.

## Frozen surfaces

No contact. Zero `src/` files changed:

```
$ git diff --stat 5d9b995ce..HEAD -- src/
(no output)
```

`SUB-manifest` and `SUB-verification` are DRIVEN and READ by the soak, never
modified. `verify_root`'s output shape is consumed as-is; the P1 finding is
parked precisely because making it green would require touching code this
tranche may not touch.
