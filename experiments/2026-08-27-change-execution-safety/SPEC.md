# SPEC — execution safety: census, verdict, and the switch that did not happen

Traces to REQUEST.md R1–R6. Map ids resolved in REQUEST.md.

**Status: STOPPED AT THE R3 VERDICT GATE.** R1 (census) and R2 (safety
assessment) are complete. R3 returns **NOT PROVEN**. R4 (switch on) and
R5 (offline proof of the switched-on path) are therefore NOT performed —
"If so switch both on" authorizes the switch only on SAFE, and the gate
is not this tranche's to waive.

---

## R1 — CENSUS: every path that can execute model-authored code

Read `file:line` against commit `6c9efc360`. "Model-authored" means the
executed bytes are, or are derived from, text the provider model wrote
on the wire.

| # | Path | Executes model-authored code? | Default state on main | The exact switch | Backend that runs it | Matches the standing ruling? |
|---|---|---|---|---|---|---|
| 1 | **simulation, declarative profile** `simulation.declarative.v1` | **No.** The model authors a JSON document; `simulation/compiler.py:93-146` compiles it from a CLOSED operator set (`add mul sub div neg abs min max lt le gt ge eq select`) into a `return {...}` of arithmetic. No `def`, no generator, no attribute access, no raw passthrough. | **ON** — this is what a run gets today | `DEEPREASON_SIMULATION_RUNNER` unset or `declarative` → `v6_policy.py:314-322`; policy at `v6_policy.py:378-402` | `verification/simulation.py` local subprocess | Channel ON: **yes**. Model-authored code execution: **no, by construction** |
| 2 | **simulation, contained profile** `simulation.container.v1` | **Yes** — `sandboxed_python_v1`, the model's own Python source | **OFF** | `DEEPREASON_SIMULATION_RUNNER=contained` → `v6_policy.py:314-322`, policy at `v6_policy.py:356-377` | `verification/contained.py` (`ContainedSimulationBackend`) | **NO** — this is the road the operator says is off, and it is |
| 3 | **code-testing channel** | **Yes** — an artifact whose content is Python (`codec="code:python"`), and the model-authored `checker_spec.source` on the `program:candidate_checker` road (`workloads/text.py:74-91,196`; `informal/skeleton.py:67-73`; `oracle.py:234-249`) | **ON, and ungated** | none — `channels.py:92-104` declares `enforcement="unconditional — no gate exists"` | `oracle.py` guard (`oracle.py:57-101`) + `oracle_sandbox.py::run_isolated` subprocess (`oracle_sandbox.py:80-133`) | Channel ON: **yes** — and it has been executing model-authored code the whole time |
| 4 | code-workload `CheckSpec` checks | No — commands are copied verbatim from a frozen `CheckSpec`; `verification/runner.py:1-6` states candidate output never reaches `argv`/`cwd`/`env` | not reachable from a public text run (`workloads/code.py` only) | n/a | `verification/runner.py` | n/a for this tranche |
| 5 | Lean kernel verification | Model-authored Lean source, not Python | operator-invoked CLI only (`cli/main.py:2744,2788`) | n/a — not a capability channel | `verification/lean.py` | n/a for this tranche |

### The three census findings

**F1 — The operator's premise is right about row 2 and wrong about row 3.**
Model-authored code execution has NOT been off "this whole time". Row 3,
the code-testing channel, executes model-authored Python today, on every
run, with no switch anywhere. What is off is row 2: the `sandboxed_python_v1`
simulation runner. Both descriptions in the operator's message land on real
things; they land on different rows.

**F2 — The "everything on" mismatch is real and is exactly as commit
`74d9f71ca` recorded it.** `engaged_simulation_policy` returns
`runner_profile="simulation.declarative.v1"` while binding
`python_toolchain_identity=PUBLIC_SIMULATION_TOOLCHAIN_ID`
(`v6_policy.py:292, 378-382`) — a Python toolchain the declarative profile
can never dispatch to. `capabilities/simulation.py:581-587` computes
`expected_profile` from the proposal's mode and denies with terminal reason
`runner_profile_mismatch` when they differ. A `sandboxed_python_v1` proposal
therefore can never be admitted under the default policy. Each half is
correct on its own; together they advertise a channel that is closed.

**F3 — `DR-INV-evidence-channels` is accurate and was never the problem.**
The simulation CHANNEL is on by default and always has been since 2026-08-26.
What that document's own first Trap warns about is precisely this case: "A
default that is `True` over a road that is severed. The flag is the cheap
half." The channel flag is on; the road to model-authored Python is severed
by the runner profile, one layer below the flag.

---

## R2 — SAFETY ASSESSMENT

Full per-property verdicts, citations and pasted output: **`SAFETY.md`**.
Summary of the five properties for `ContainedSimulationBackend`, the
backend R4 would have switched on:

| Property | Verdict |
|---|---|
| (a) no network access | **ENFORCED AND PROVEN** |
| (b) bounded wall time | **ENFORCED AND PROVEN** |
| (c) bounded memory | **ENFORCED AND PROVEN** |
| (d) file access confined to the run's own sandbox directory | **ABSENT — demonstrated escape** |
| (e) no privilege beyond the harness process | **ABSENT — demonstrated escape** |

---

## R3 — VERDICT: **NOT PROVEN**

Two of five properties are absent, and absent by demonstration rather than
by inference: `proof/containment_probe.py` writes a file outside the
ephemeral scratch directory and runs an arbitrary shell command, both from
inside model-authored Python, both while the simulation returns `pass`.

Per R3, this tranche therefore STOPS. Nothing is switched on. The
deliverable is this census, `SAFETY.md`'s gap list, and the ready-to-send
hardening prompts in `PARKED.md`.

---

## Recorded assumptions (per the scope contract — where REQUEST.md is silent)

**A1 — "code-enforced and test-proven" is read as "code-enforced and
demonstrable".** R2 defines ABSENT as "enforced only by docstring,
convention, or the model's good behavior", which is a test of ENFORCEMENT.
R3 disqualifies a property that is "absent or unprovable". A property with
enforcing code but no committed test is therefore neither: this tranche
resolves it by trying to demonstrate the property and recording what
happened. Every demonstration this tranche created is labelled as created
in SAFETY.md, never presented as pre-existing proof. The assumption never
had to carry weight for a favourable verdict: the two failing properties
failed by exploit, not by missing paperwork.

**A2 — the assessed subject is the backend R4 would switch on**
(`ContainedSimulationBackend`), with the currently-ON backends assessed
alongside because the census found row 3 already executing model-authored
code. R3's gate governs the switch. Row 3's gaps are reported and parked
(R6), not fixed here: fixing them is a defect tranche, and this tranche's
one goal is the census, the verdict, and — had it been SAFE — the switch.

**A3 — the declarative profile is out of the assessment's scope** because
census row 1 establishes it does not execute model-authored code. The
closed operator set at `simulation/compiler.py:93-146` is the reason, and
it is checkable rather than asserted.

---

## Acceptance checks

| Requirement | Check | State |
|---|---|---|
| R1 | census table above; every row carries `file:line` | **MET** |
| R2 | `SAFETY.md` per-property verdict + citations + pasted output; `proof/` re-runnable | **MET** |
| R3 | verdict recorded, nothing switched on, gap list + hardening prompt committed | **MET (NOT PROVEN branch)** |
| R4 | — | **NOT PERFORMED** — gate returned NOT PROVEN |
| R5 | — | **NOT PERFORMED** — gate returned NOT PROVEN |
| R6 | `PARKED.md` carries a ready-to-send prompt per finding | **MET** |
