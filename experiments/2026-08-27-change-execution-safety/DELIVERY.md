# DELIVERY — execution safety

**Answer to the operator's question, first: it was NOT safe, it is now, and
both are on.** The escape that made it unsafe is closed at all five call
sites and the switch-on is the shipped default. One of the two channels
turns out to have been on the whole time — with weaker containment than the
one that was off.

This document was written on 2026-08-27 against a NOT PROVEN verdict, then
extended on 2026-08-28 after the operator said "can you fix please". The
original R1-R6 reconciliation is kept verbatim below because it is the record
of what was true before the fix; **R7, R8 and the revised R3/R4/R5 are at the
end of this document** and supersede it.

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
| P7 | HIGH | the 2026-08-25 frozen-surface grant's census ("zero roots carry a `transport_failure` attempt") was falsified by a root committed 2026-08-26; `docs_verify` red on it since |

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

```
$ python tools/docs_verify.py
docs_verify [full]: 68 documents, 1126 checks, 4 workers
  FAIL CON-run-identity.md:200  (git log over retired run roots)
  FAIL CON-run-identity.md:202  fatal: ambiguous argument '1637e808': unknown revision
  FAIL CON-run-identity.md:204  fatal: ambiguous argument 'f304fec1': unknown revision
  FAIL INV-frozen-surfaces.md:181
      test "$(find experiments runs -path '*workflow-provider-attempt-v1/*.json' \
              -exec grep -l 'transport_failure' {} + 2>/dev/null | wc -l)" -eq 0
docs_verify: 4 failed
```

**Four, not the three the tranche instruction forecast.** The three
`CON-run-identity.md` failures are the known shallow-clone ones — they walk
git history for commits this clone does not carry, and two say so verbatim
(`unknown revision`).

**The fourth is not a shallow-clone failure and is not this tranche's.**
It is a real, falsified census. Confirmed by measurement:

```
$ find experiments runs -path '*workflow-provider-attempt-v1/*.json' \
      -exec grep -l 'transport_failure' {} + 2>/dev/null
experiments/2026-08-26-pc2-rematch/retired-transport-timeout180-run-42ad288038dd606c/objects/workflow-provider-attempt-v1/f750d2979c3e248e549efb5754bfb11b947cba1cfa7fb2bb8c1d77babad3b570.json

$ git log --oneline -1 origin/main -- <that path>
50885d29f P-C2 Appendix A Amendment 2: raise ARM H3's seat timeout to 900s

$ git diff --name-only origin/main...HEAD | grep -c "workflow-provider-attempt-v1"
0
```

The file is on `origin/main`, committed 2026-08-26; this tranche added no
file matching that path. It matters beyond a red line: that check is the
census carrying the safety argument for the 2026-08-25 frozen-surface grant
in `INV-frozen-surfaces.md` — "zero with `outcome: transport_failure`", which
is why that one-line reader change could not move any committed verdict. The
census is now false. Parked as P7.

**Effective docs_verify: 3 known shallow-clone failures + 1 pre-existing
falsified census, none introduced here.** The map edit this tranche made
(two Traps entries in `INV-evidence-channels.md`) introduced no failure, and
`Verified-at:` was deliberately not advanced — that document's checks were
not re-derived.


---

# PART TWO — 2026-08-28: the fix, and the switch it unblocked

Authority: REQUEST.md Amendment 1 ("can you fix please. Frozen surface
changes are permitted as long as you document what is affected") and
Amendment 2 ("oh and it doesn't break other modules").

## R7 — FIX THE CONTAINMENT · **MET**

One boundary, in `src/deepreason/sandbox_guard.py`, consumed by five call
sites. It denies CPython's whole introspection prefix set — `_ f_ gi_ cr_
ag_ tb_ co_ func_ im_`, plus `mro` — rather than the three attribute names
the exploit happened to use.

**Closure is proved, not asserted.** `tests/test_sandbox_guard.py` walks the
live `dir()` of a generator, coroutine, async generator, traceback, frame,
code object, function, bound method and `type`, and pins the surviving
residue to exactly eight names (`close send throw aclose asend athrow clear
replace`), each either a protocol method on an object you must already hold
or a name shared with ordinary container/string methods. A future CPython
adding an introspection attribute under a new prefix turns that RED. That is
the property the old rule — a denylist over an OPEN set — could never have.

**The five consumers.** `oracle.py`, `programs.py` and
`verification/simulation.py` import it. The frozen contained worker cannot
import anything from this repository (scrubbed environment, no `PYTHONPATH`),
so it receives the rule as GENERATED source, with a test executing both and
asserting they agree on every probe. `verification/brokered.py` derives its
worker from the contained one and inherited the fix untouched — a fifth call
site found only by running the wider ring, now pinned by its own test.

**A second layer, because a property resting on one layer is one bug away
from absent — which is what this tranche measured.**
`src/deepreason/sandbox_os.py` holds the network-namespace probe, and
`oracle_sandbox.py` now runs the code-testing worker behind it; that channel
is on by default and carried no OS boundary at all. Its resource limits also
now fail CLOSED, where they had swallowed every `setrlimit` failure so a host
that refused a limit got an unlimited worker in silence.

| Proof | Result |
|---|---|
| `proof/containment_probe_BEFORE.out` vs `_AFTER.out`, same unchanged script | E1 file-outside-scratch `True → False`; E2 shell command `pass → refused`; E3 `NETWORK_REACHED → marker not written` |
| `proof/mutation_proof.sh` M1 — boundary reverted to the historical rule | 9 red, then 20 green |
| `proof/mutation_proof.sh` M2 — default reverted to `declarative` | 6 red, then 9 green |

## C7 — FROZEN SURFACES DOCUMENTED · **MET**

The grant was conditional, and the condition is the deliverable. Full
disposition: **`FIX.md`**. Recorded as a granted contact in
`docs/map/INV-frozen-surfaces.md` under surface 3, to the standard the five
prior grants set.

| Surface | Touched | What moved |
|---|---|---|
| 3 `verification/contained.py` | **yes** | the worker's `guard()` condition; the worker source became a template interpolating the one boundary. `CONTAINED_WORKER_SHA256` moves — by design, a changed worker is a changed runtime identity visible in every receipt |
| 3 `verification/simulation.py` | **yes** | the two conditions inside `_guard`, attribute rule only |
| 3 `verification/brokered.py` | no — but changed | derives from the contained worker; `BROKERED_WORKER_SHA256_V2` moves with it |
| 3 `invariants.py` | **no** | pairs work-order profile against policy profile and re-derives source by MODE; neither couples mode to profile |
| 1 `capabilities/state.py` | **no** | |
| 2 `harness.py` | **no** | |
| 4 `run_manifest.py` | **no** | |
| 5 `qualification.py` | **no** | its SUBJECT moves; its code does not |
| adjacent `llm/firewall.py` | **no** | |

**Why no committed root can change verdict**, stated as a category rather
than a census: the changed code runs INSIDE a worker at EXECUTION time and
decides whether a future proposal's source is admitted. It is not a reader.
No record format, digest algorithm, manifest schema, `_EPISTEMIC_CHECKS`
entry, `verify_root` finding or `report.py` channel changed. A committed
root's stored `SimulationVerificationResult` is bytes no code path in this
change reads, writes or re-derives.

## C8 — "IT DOESN'T BREAK OTHER MODULES" · **MET, three ways**

1. **Full gate**, 0 failed — see the gate section below.
2. **A positive test per hardened guard**: `math`, `rng`, container and string
   methods, nested functions, closures and comprehensions all still run;
   verdicts still come back both PASS and FAIL. A guard that closed the escape
   by rejecting everything would pass the negative tests and fail the operator.
3. **The closure test**, so "does not break other modules" is re-derivable
   rather than a claim about today's suite.

**Three things the ring caught that I had gotten wrong, each recorded rather
than quietly fixed:**

- I added an underscore-NAME rule to the contained worker beyond what the
  escape needed. It contradicted a committed intention that `__import__`,
  `open` and `eval` LOAD and fail at runtime. Removed; the guard change is now
  the attribute boundary and nothing else.
- `test_security.py` pinned the word `"dunder"` in a diagnostic that
  deliberately can no longer say it. Updated to assert the refusal and the
  offending attribute — the one fixture updated in the fix commit, predicted
  in FIX.md as CLAUDE.md requires.
- **The switch-on nearly shipped the same defect backwards.** With the
  contained runner as the default, every `declarative_numeric_v1` proposal was
  denied `runner_profile_mismatch`. Found by the ring, not by reading. Fixed
  in `capabilities/simulation.py`: model-authored Python still requires the
  contained runner, but a declarative-numeric document runs under either
  profile, because its executed source is HARNESS-compiled — making the
  container profile the stronger home for it, not a weaker one.

## R3 (revised) — VERDICT · **SAFE**

`SAFETY.md`'s 2026-08-28 re-assessment. All five properties code-enforced and
demonstrated; the 2026-08-27 NOT PROVEN verdict is kept verbatim beneath it,
because the before/after pair is the evidence.

| Property | 2026-08-27 | 2026-08-28 |
|---|---|---|
| (a) no network | ENFORCED | **ENFORCED** — and it survived the escape, with `os.system` in hand |
| (b) bounded wall | ENFORCED | **ENFORCED** |
| (c) bounded memory | ENFORCED | **ENFORCED** |
| (d) file confined | **ABSENT** | **ENFORCED** |
| (e) no privilege | **ABSENT** | **ENFORCED** |

Residue stated rather than buried: (d) and (e) rest on the language boundary
alone. Parked as P9, recommended and explicitly not a blocker.

## R4 — SWITCH BOTH ON · **MET**

- **On by default, no code edit and no environment variable.**
  `DEEPREASON_SIMULATION_RUNNER` unset now means the contained runner. The
  setting names WHICH runner, never WHETHER simulation runs — the shape
  `DEEPREASON_RESEARCH_ALLOWLIST` already uses.
- **The declarative profile survives as a named choice**, not a deletion.
- **The toolchain pairs with the profile on both branches**, asserted both
  ways, so no configuration carries a toolchain its runner cannot dispatch to.
- **Everything-on means everything.** The container profile serves BOTH
  simulation modes. Anything less would have been a trade, not a switch-on.
- **Never a new compile-time refusal — and one existing one removed.** An
  unrecognised runner value used to raise `ValueError`. It now resolves to the
  default and is disclosed as `SIMULATION_RUNNER_UNKNOWN`. A host that cannot
  create the namespace gets `SIMULATION_RUNNER_UNAVAILABLE` rather than a
  silently dead channel, and a well-formed configuration on an equipped host
  emits nothing — a disclosure that fires on every run is noise.

## R5 — OFFLINE PROOF · **MET**

`tests/test_simulation_runner_default.py`, end to end on the shipped default:
`engaged_simulation_policy({})` and the real toolchain builder, through the
real `Scheduler` and `SimulationCapabilityController` — proposal admitted with
**no DENIED transition**, dispatched, executed, **SUCCEEDED** lifecycle,
contained-backend fingerprint carrying `network_denial: namespace_unshared`,
and the written root **replay-validates with zero violations**. Mutation M2
turns 6 of its 9 tests red, that one included.

R5's second obligation ("same for the code-testing channel if R1 found it
gated off") does not apply on its own terms — R1 found that channel ON. It
was nonetheless hardened, which is P1's substance delivered rather than
parked.

## R8 — THE GATE SURVIVED THE FIX · **MET**

R3 was re-run against the fixed tree rather than assumed. Had it returned
NOT PROVEN again, R4 and R5 would not have fired.

## Gate, 2026-08-28

```
$ python -m pytest tests/ -q -n 4
4374 passed, 6 skipped in 823.17s (0:13:43)
```

**0 failed.** Three runs were needed to get there and each intervening
failure is recorded above rather than smoothed away — the wider ring caught
two mistakes of mine in the fix, and the full gate caught a third in the
switch-on (`test_single_run_path`, a committed manifest compared field by
field against a fresh compile). The count rose from 4334 at the start of the
tranche to 4374: 29 new tests across
`tests/test_sandbox_guard.py` and `tests/test_simulation_runner_default.py`,
plus the `jsonschema` test that had been failing on a missing dependency
(parked as P6).

## R6 — PARK · **MET, nine entries**

P1 and P2 were **fixed** under Amendment 1 rather than left parked; their
entries stay, because a parked entry is never deleted. P3–P9 remain parked
with ready-to-send prompts. P8 and P9 were added on 2026-08-28: P8 records
that model-authored simulations cannot define classes — verified identical on
the pre-fix tree, so a standing limit and not a cost of this fix.

## The cost, disclosed where it was priced

The compiled manifest changed, and the manifest is part of the qualification
behavior subject, so **the first live run after this pays a fresh
qualification battery** (~14 min, ~1160 calls). Two committed digest pins
moved to match, each recording its before/after and its reason in its own
docstring:

    f3bb6562...  ->  83454b08...   shipped qualification subject
    b9038b84...  ->  02ee7e09...   discharge-wire subject

Their structural assertions are untouched: `compile_notices` is still `None`
on the shipped path, so no notice leaks into the compiled manifest.

## A correction to this tranche's own record

`SPEC.md` F2 first read — following commit `74d9f71ca`'s framing — that the
old default bound a Python toolchain the declarative profile could never
dispatch to. That is wrong, and it is corrected in place. The two always
paired: `engaged_simulation_toolchain` reads the same runner choice the policy
does, and the declarative runner genuinely uses that local toolchain. The
defect was only the mode-to-profile refusal. The sharper-sounding version
would have sent the next reader to fix a pairing that was never broken.
