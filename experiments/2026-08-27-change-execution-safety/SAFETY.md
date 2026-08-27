# SAFETY — is it safe to switch model-authored code execution on?

**Verdict: NOT PROVEN.** Three of the five containment properties hold and
are demonstrated. Two do not hold, and they do not hold by working exploit
rather than by missing paperwork.

Subject: `ContainedSimulationBackend` (`src/deepreason/verification/contained.py`),
the backend that runs `sandboxed_python_v1` under
`runner_profile="simulation.container.v1"` — the road R4 would have opened.
Assessed alongside it, because SPEC.md's census found it already executing
model-authored code with no switch: the **code-testing channel**
(`oracle.py` + `oracle_sandbox.py`).

Every verdict below was produced on this host at commit `6c9efc360`.
Re-run: `python experiments/2026-08-27-change-execution-safety/proof/containment_probe.py`
and `experiments/2026-08-27-change-execution-safety/proof/network_namespace_differential.sh`.
Both are self-cleaning: every marker file they write, they remove.

---

## The single defect behind both failures

`ContainedSimulationBackend`'s language boundary rests on two rules, both
in the frozen worker source (`verification/contained.py:80-87`):

```
def guard(source, label):
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal)):
            raise ValueError(label + " may not import or mutate scope")
        if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            raise ValueError(label + " may not traverse private attributes")
```

plus a 34-name `ALLOWED_BUILTINS` whitelist (`contained.py:69-73`) that
contains no `open`, `__import__`, `eval`, `exec`, `getattr`, `type`,
`dir`, `vars` or `globals`.

The escape needs none of those, and touches no leading-underscore
attribute:

```python
def simulate(inputs, rng):
    box = []
    def g():
        box.append(gg.gi_frame.f_back.f_back.f_globals)
        yield 1
    gg = g()
    for v in gg:
        break
    w = box[0]                    # the WORKER MODULE's own globals
```

`gi_frame`, `f_back` and `f_globals` are all public attribute names. While
the generator is running, its frame's `f_back` is `simulate`'s frame, and
`f_back.f_back` is the worker's own `run()` frame, whose `f_globals` is the
worker module namespace — which holds the real `builtins`, `sys`, `json`,
`random` and `math` modules. From there `w['builtins'].open` and
`w['sys'].modules['os'].system` are ordinary lookups.

`oracle.py`'s guard (`oracle.py:92-110`) is strictly stronger — it also
rejects leading-underscore NAMES, `**`, and large int literals — and it
does not help: the escape uses no underscore name either. The same three
attributes carry it.

---

## Property-by-property

### (a) No network access — **ENFORCED AND PROVEN** ✅ (contained runner only)

**Enforced by:** `verification/contained.py:450-483` probes
`unshare --map-root-user --net --` by running the real interpreter inside
the candidate namespace, and `contained.py:564-575` refuses to execute at
all when the probe comes back empty — fail CLOSED, not a softer run.
`contained.py:632-642` launches the worker behind that prefix.

**Pre-existing committed test:** `tests/test_contained_simulation_runner.py:152`
`test_missing_network_namespace_fails_closed` — proves the refusal path.

**Created by this tranche (the OS-layer half the committed tests did not
carry):** `proof/network_namespace_differential.sh`. The committed suite
asserts `reported["network"] is False`, which is the backend describing
itself; this is a differential.

```
=== INSIDE the backend's own probed prefix (unshare --map-root-user --net) ===
CONNECT_DENIED OSError [Errno 101] Network is unreachable
INTERFACES [(1, 'lo')]
=== OUTSIDE (host namespace) ===
CONNECT_OK
INTERFACES [(1, 'lo'), (2, 'ifb0'), (3, 'ifb1'), (4, 'eth0')]
```

**And it survives the escape** — the strongest form of this verdict. With
a full language escape in hand and arbitrary subprocess spawning available,
the network is still gone:

```
A HOLDS (a): the network namespace survives a full language escape
  verdict=pass
    b'[{"input_index":0,"metrics":{},"observables":{"value":"NETWORK_DENIED [Errno 101] Network is unreachable"},"passed":true,"seed":7}]'
```

This is the one property that does not depend on the language boundary at
all, which is exactly why it is the one that held.

**On the code-testing channel this property is ABSENT.**
`oracle_sandbox.py:80-133` uses no namespace and no seccomp filter — see
the E3 finding below.

### (b) Bounded wall time — **ENFORCED AND PROVEN** ✅

**Enforced by:** `RLIMIT_CPU` applied in the child before `exec`
(`contained.py:398-400`), `communicate(timeout=maximum_wall_ms + 2000ms)`
(`contained.py:653-656`), and `_kill_group` over the `os.setsid()` process
group (`contained.py:411-418`, `contained.py:396`). Failure to apply any
limit propagates out of `preexec_fn` and becomes a typed refusal
(`contained.py:644-654`) — fail closed.

**Pre-existing committed tests:**
`tests/test_contained_simulation_runner.py:134` (limit table),
`:161` `test_unappliable_resource_limits_fail_closed`,
`:219` `test_runaway_sandboxed_python_hits_the_deterministic_step_budget`.

**Created by this tranche:** a C-level hang the line-event tracer cannot
see — the contained worker's `guard()`, unlike `oracle.py`'s, does not
reject `**`:

```
  int bomb (C-level)     -> overrun  {"sandbox_abort": "worker terminated by resource containment", "returncode": -24, ...}
  infinite loop          -> fail     {"error": "deterministic step limit exceeded", "steps": 100001}
```

`returncode -24` is `SIGXCPU`: the CPU rlimit fired. The gap in the AST
guard is covered by the OS limit below it.

### (c) Bounded memory — **ENFORCED AND PROVEN** ✅

**Enforced by:** `RLIMIT_AS` at `contained.py:401-403`, from
`_containment_limits` (`contained.py:373-384`), fail-closed on the same
`preexec_fn` path as (b).

**Pre-existing committed test:**
`tests/test_contained_simulation_runner.py:236`
`test_memory_hungry_sandboxed_python_is_contained`.

**Re-run here:**

```
  memory bomb            -> overrun  {"sandbox_abort": "resource containment"}
```

### (d) File access confined to the run's own sandbox directory — **ABSENT** ❌

**What is there:** `contained.py:624` makes an ephemeral
`tempfile.mkdtemp(prefix="deepreason-contained-")`, `:635` sets it as the
worker's `cwd`, `:361-371` points `HOME` and `TMPDIR` at it, `:682`
`shutil.rmtree`s it, and `RLIMIT_FSIZE` caps any single file at 8 MB
(`contained.py:404-406`).

**Why that is not confinement:** `cwd` is a starting directory, not a jail.
There is **no mount namespace** — the probe prefix is `--net` only
(`contained.py:463`) — so the entire host filesystem is visible at the
worker's own privilege. The only thing standing between model-authored code
and that filesystem is the absence of `open` from the builtins whitelist,
and the escape above supplies `open` from the real `builtins` module.

**Demonstrated, not inferred:**

```
E1 BROKEN (d): file access is NOT confined to the sandbox directory
  verdict=pass  trace={"samples_passed": 1, "steps": 2285}
  file written OUTSIDE the ephemeral scratch dir: True
  contents: 'ESCAPED'
```

The simulation returned **`pass`**. Nothing in the typed record marks the
write.

**No committed test covers this.** `tests/test_contained_simulation_runner.py:134`
asserts `reported["filesystem"] == "ephemeral scratch workdir"` — a string
the backend reports about itself, which is exactly the shape
`DR-INV-evidence-channels`'s first Trap warns about.

### (e) No privilege beyond the harness process — **ABSENT** ❌

**What is there:** `os.setsid()` (`contained.py:396`), `RLIMIT_NPROC` 2048
and `RLIMIT_NOFILE` 64 (`contained.py:407-408`), `RLIMIT_CORE` 0
(`contained.py:397`), and a six-entry environment allowlist that drops
every credential and every `DEEPREASON_*` variable
(`contained.py:361-371`).

**Why that is not the property:** those bound how MUCH the worker may
consume, not WHAT it may do. Once the escape hands over the real `sys`
module, `sys.modules['os'].system` runs arbitrary shell commands at the
harness process's own uid.

**Demonstrated:**

```
E2 BROKEN (e): arbitrary shell commands run at harness privilege
  verdict=pass  os.system('true') returncode in output:
    b'[{"input_index":0,"metrics":{},"observables":{"value":0},"passed":true,"seed":7}]'
```

Return code 0 — the command ran. The environment scrub still holds (no
credentials in the worker's own environment), and the network namespace
still holds, so the blast radius is: **the whole local filesystem and
arbitrary local process execution, at harness privilege, with no network.**

**No committed test covers this.**
`tests/test_contained_simulation_runner.py:117` proves the environment
allowlist, which is a different and weaker claim.

---

## What HELD, so the picture is not worse than it is

Every attack that the design anticipated was stopped:

```
HELD: the guard and the limits stop the obvious attacks
  import socket          -> fail     "simulation may not import or mutate scope"
  __import__             -> fail     "name '__import__' is not defined"
  dunder walk            -> fail     "simulation may not traverse private attributes"
  open() absolute        -> fail     "name 'open' is not defined"
  infinite loop          -> fail     "deterministic step limit exceeded"
  int bomb (C-level)     -> overrun  "worker terminated by resource containment"
  memory bomb            -> overrun  "resource containment"
```

The committed suite is green here, with nothing skipped — containment IS
available on this host, so the execution tests really ran:

```
$ python -m pytest tests/test_contained_simulation_runner.py -q
...............                                                          [100%]
15 passed in 1.84s
```

The failure is one specific hole in one specific guard, not a design that
was never taken seriously.

---

## E3 — the finding this tranche did not go looking for

**The same escape works against the code-testing channel, which is ON
today, ungated, and has been executing model-authored Python the whole
time — and it has no network namespace.**

```
E3 BROKEN: the SAME escape on the code-testing channel, which is ON
  exec-oracle verdict on the hostile candidate: pass
  marker written: True
  network result from inside the sandbox: 'NETWORK_REACHED'
```

That is a real outbound TCP connection to 1.1.1.1:80, opened by
model-authored Python, from inside `oracle_sandbox`'s worker, while the
exec-oracle commitment returned **`pass`**.

`oracle_sandbox.py` has no namespace, no seccomp filter
(`verification/_sandbox.py::seccomp_available` exists but
`oracle_sandbox.py` never calls it), and its rlimits are best-effort:
`_apply_worker_limits` (`oracle_sandbox.py:135-166`) wraps every
`setrlimit` in `except (AttributeError, ValueError, OSError): pass` — it
fails OPEN, the exact posture `contained.py:386-395` was written to
invert.

So on containment, the ordering is the opposite of what the operator's
question assumes: **the channel that is OFF is the better-contained one.**

---

## Gap list — what must be true before the switch is safe

| # | Gap | Where | Severity |
|---|---|---|---|
| G1 | Frame-object attributes (`gi_frame`, `cr_frame`, `ag_frame`, `tb_frame`, and every `f_*` attribute of a frame) are not rejected by the AST guard, so model code reaches the worker module's globals and the real `builtins`. | `contained.py:80-87` (worker `guard`); `oracle.py:92-110` (`_guard`) | **Critical — both channels** |
| G2 | No mount namespace or filesystem jail: `cwd` is the only confinement, and `resource_limits()` reports `"filesystem": "ephemeral scratch workdir"` as though it were one. | `contained.py:463`, `:508-515`, `:624-642` | **High** |
| G3 | No process-execution boundary: nothing prevents `os.system`/`fork`/`exec` once the language boundary is crossed. No seccomp filter is applied even though `verification/_sandbox.py` provides one. | `contained.py:386-408`; `_sandbox.py:23-29` | **High** |
| G4 | The code-testing channel runs model-authored code with NO network namespace and FAIL-OPEN rlimits, and is on by default with no switch. | `oracle_sandbox.py:80-133`, `:135-166`; `channels.py:92-104` | **Critical — live today** |
| G5 | Containment properties are pinned by self-reported strings (`"network": False`, `"filesystem": "ephemeral scratch workdir"`) rather than by differentials that could fail. | `tests/test_contained_simulation_runner.py:134-149` | **Medium — this is why G1–G3 went unnoticed** |

Ready-to-send hardening prompts for G1–G5: **`PARKED.md`**.

---

## Residue — what this assessment does NOT establish

- It does not establish that G1 is the ONLY hole in either guard. It
  establishes that one hole exists and is trivially exploitable. A guard
  built on an attribute-name denylist is the wrong shape for the job; the
  right fix is an allowlist of AST node kinds, and until that lands, the
  next probe may find a second path.
- It does not establish anything about hosts where
  `containment_available()` is False. There the contained runner refuses to
  execute at all (`contained.py:564-575`), which is the correct behaviour,
  but the code-testing channel keeps running with no namespace anywhere.
- The privilege statement (e) is measured on this container, where the
  harness runs as root. On a host where it runs as an ordinary user, the
  blast radius is that user's — still "whatever the harness process can
  do", which is the property as stated, and still not confinement.
- "Accepted does not mean true." A green
  `tests/test_contained_simulation_runner.py` meant, before this tranche,
  only that the anticipated attacks were anticipated.
