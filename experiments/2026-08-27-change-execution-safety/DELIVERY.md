# DELIVERY — execution safety

**Answer to the operator's question, first: NOT safe to switch on today,
and nothing was switched on. Both channels are covered below, and one of
them turns out to have been on the whole time.**

Reconciliation against the operator's verbatim words (REQUEST.md), one
requirement at a time, with the proof for each.

---

## The operator's words, and what each half turned out to mean

> model authored code execution switched off. I need to know if it's safe
> to switch on. Same with simulation. If so switch both on. The last
> window found out it's been off this whole time

| The operator's phrase | What it lands on | State found |
|---|---|---|
| "model authored code execution" | TWO roads, not one: the `sandboxed_python_v1` simulation runner, and the code-testing channel | the first is OFF; **the second has been ON the whole time** |
| "simulation" | the simulation channel | ON since 2026-08-26 — but bound to a runner profile that refuses model-authored Python |
| "If so switch both on" | conditional on the R3 SAFE verdict | **verdict NOT PROVEN — the condition did not fire** |
| "it's been off this whole time" | commit `74d9f71ca`, epoch 4 | **confirmed for the simulation runner; not true of code-testing** |

---

## R1 — CENSUS · **MET**

Proof: SPEC.md's five-row table, every row carrying `file:line` against
commit `6c9efc360`. Two rows execute model-authored code (the
`sandboxed_python_v1` runner, OFF; the code-testing channel, ON and
ungated); one compiles a closed arithmetic DSL and executes no
model-authored code by construction; two are unreachable from a public
text run. Three findings F1–F3 name what the census settled, including
the "everything on" toolchain/profile mismatch that commit `74d9f71ca`
recorded live.

## R2 — SAFETY ASSESSMENT · **MET**

Proof: SAFETY.md, per-property verdict with enforcement citations, the
committed test that covers it (or the statement that none does), and
pasted output. Re-runnable and self-cleaning:
`proof/containment_probe.py`, `proof/network_namespace_differential.sh`.

| Property | Verdict | The decisive line |
|---|---|---|
| (a) no network | **ENFORCED AND PROVEN** | survives a full language escape: `NETWORK_DENIED [Errno 101] Network is unreachable` |
| (b) bounded wall time | **ENFORCED AND PROVEN** | `returncode: -24` (SIGXCPU) on a C-level int bomb |
| (c) bounded memory | **ENFORCED AND PROVEN** | `{"sandbox_abort": "resource containment"}` |
| (d) file confined to sandbox dir | **ABSENT** | `file written OUTSIDE the ephemeral scratch dir: True` |
| (e) no privilege beyond harness | **ABSENT** | `os.system('true')` → `0`, verdict `pass` |

The committed containment suite is green here with nothing skipped:
`15 passed in 1.84s`.

## R3 — VERDICT GATE · **MET, on the NOT PROVEN branch**

Two of five properties are ABSENT by working exploit. Per R3 the tranche
STOPPED: SAFETY.md carries the gap list G1–G5, PARKED.md carries a
ready-to-send hardening prompt for each, and **nothing was switched on**.
No `src/` file was modified in this tranche — `git show --stat` on its
commits shows only `experiments/` and one `docs/map/` document.

## R4 — SWITCH BOTH ON · **NOT PERFORMED**

Correctly not performed. "If so switch both on" authorizes the switch
only on SAFE, and R3 states the gate is not this tranche's to waive.
The authorization is not spent — it stands for the tranche that closes
the gap (PARKED.md P2).

## R5 — OFFLINE PROOF · **NOT PERFORMED**

Gated on R4. Its second obligation ("same for the code-testing channel if
R1 found it gated off") does not apply on its own terms: R1 found that
channel ON, not gated off.

## R6 — PARK EVERY DEFECT · **MET**

Five findings parked with ready-to-send prompts, none fixed here:

| # | Severity | What |
|---|---|---|
| P1 | **CRITICAL, live today** | sandbox escape on the code-testing channel, with no network namespace |
| P2 | **CRITICAL** | the same escape on the contained simulation runner — this is the gate that stopped R4 |
| P3 | HIGH | the "everything on" preset advertises a channel it cannot reach; needs a typed disclosure, not a silent dead channel |
| P4 | MEDIUM | containment tests pin self-reported strings instead of differentials — this is how the escape survived a committed containment proof |
| P5 | LOW | `docs/map/SEAM-capabilities-x-channels.md` does not exist; this tranche's whole subject lives on it |
| P6 | LOW | the documented gate needs `jsonschema` and `pytest-xdist`, which the documented install does not declare; CLAUDE.md's ~3100-passed baseline is stale at 4334 |

---

## Constraints honoured

| # | Constraint | How |
|---|---|---|
| C1 | channels stay ON | nothing was disabled; the standing ruling is untouched |
| C2 | no frozen-surface contact without a grant | no `src/` change at all. `verification/` (surface 3) was READ and probed, never modified. PARKED.md P2 states the grant P2's implementer must request in FIX.md |
| C3 | offline only | no API key requested or used; every probe runs against local subprocesses |
| C4 | mutual stop lines | nothing written under `experiments/2026-08-27-change-technique-run/`; that branch fetched read-only for commit `74d9f71ca`; no running process touched |
| C5 | root sweep retired | not run, not proposed |
| C6 | qualification cost disclosure | see below |

**C6 — the cost that was NOT incurred, and the one that waits.** Changing
capability opt-ins changes the qualification subject, so the first live
run after the switch pays a fresh qualification battery — the ~14-minute,
~1,160-call set of test calls that certifies the provider model can fill
each role. **This tranche did not incur it**, because it changed no
policy: the compiled manifest is byte-identical to before. The cost is
still owed by whichever tranche eventually flips the runner profile, and
it is a price, not a defect.

---

## Gate

### Full gate

```
$ python -m pytest tests/ -q -n 4
1 failed, 4334 passed, 15 skipped in 994.44s (0:16:34)
FAILED tests/test_schema_carries_every_prose_rule.py::test_alias_bearing_fields_name_their_legal_values_in_the_schema
E       ModuleNotFoundError: No module named 'jsonschema'
```

The one failure is an ENVIRONMENT gap in this fresh container, not a code
failure: `pip install -e .` did not pull `jsonschema`, which that test
imports at line 170. Installed and re-run, the file is green:

```
$ pip install jsonschema --break-system-packages -q
$ python -m pytest tests/test_schema_carries_every_prose_rule.py -q
....                                                                     [100%]
4 passed in 0.15s
```

**Effective gate: 0 failed.** No `src/` file changed in this tranche, so
nothing in the suite could have been affected by it. Recorded rather than
smoothed over, because the container-rollback note in CLAUDE.md's
Environment section does not mention `jsonschema` and the next fresh
session will hit the same wall.

Note for the baseline: CLAUDE.md's "expect ~3100 passed" is stale — this
run collected 4334 passed, 15 skipped.

### docs_verify

Appended at the tail of this document.
