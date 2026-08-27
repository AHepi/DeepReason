# FIX — the attribute boundary, and the frozen surfaces it touched

Authority: REQUEST.md Amendment 1 (R7, C7) and Amendment 2 (C8). The operator
granted frozen-surface contact **conditional on documentation**: "Frozen
surface changes are permitted as long as you document what is affected."
This document is that condition being met, and it is written to the standard
`docs/map/INV-frozen-surfaces.md` already records for the 2026-08-21,
2026-08-22, 2026-08-24, 2026-08-25 and 2026-08-27 grants — what moved, why,
and what it can and cannot change about any committed root.

---

## The defect, in one line

Every AST guard over model-authored Python in this repository rejected
attributes whose name begins with an underscore, and nothing else.
`gg.gi_frame.f_back.f_back.f_globals` contains no underscore.

Demonstrated, not inferred: SAFETY.md E1–E3, reproduced by
`proof/containment_probe.py`, whose pre-fix output is committed verbatim at
`proof/containment_probe_BEFORE.out`.

## The design

**One boundary, in one module.** `src/deepreason/sandbox_guard.py` owns the
rule. Five call sites consume it; none carries a private copy.

**A prefix denylist over a CLOSED set, not a name allowlist.** The allowlist
shape is the one that first suggests itself and it is wrong here: model code
legitimately reaches `math.sqrt`, `rng.randint`, `append`, `join`, `items` —
a set with no boundary, where every omission is a false rejection the operator
would feel (C8). The set that *does* have a boundary is CPython's introspection
surface, which is namespaced under a small number of fixed prefixes:

    _   f_   gi_   cr_   ag_   tb_   co_   func_   im_        plus the name `mro`

**Closure is proved, not asserted.**
`tests/test_sandbox_guard.py::test_the_prefix_set_covers_every_public_introspection_attribute`
walks the real `dir()` of a generator, coroutine, async generator, traceback,
frame, code object, function, bound method and `type` in the running
interpreter, and pins the surviving residue to exactly eight names:

    close  send  throw  aclose  asend  athrow  clear  replace

Each is either a protocol method that resumes an object you must ALREADY hold,
or (`clear`, `replace`) a name shared with ordinary container and string
methods — and a sibling test asserts none of the first six appears on anything
the sandbox actually hands to model code. A future CPython that adds an
introspection attribute under a new prefix turns that test RED, which is the
property a hand-maintained denylist cannot have. That distinction is the whole
argument: the old rule was a denylist over an OPEN set.

---

## Frozen surfaces touched — the C7 disposition, row by row

### Surface 3 (`verification/`) — `verification/contained.py`

**What moved.** Two things, and only these:

1. The frozen worker's `guard()` now tests `forbidden_attribute(node.attr)`
   instead of `node.attr.startswith("_")`. One condition, replaced.
2. The worker source literal became `_CONTAINED_WORKER_TEMPLATE`, and
   `CONTAINED_WORKER_SOURCE_V1` is that template with one sentinel replaced by
   `sandbox_guard.WORKER_GUARD_SOURCE`. The worker runs in a scrubbed
   environment with no `PYTHONPATH` and cannot import this repository, so it
   receives the rule as generated source rather than by import. Generated, not
   hand-copied:
   `test_the_frozen_worker_carries_the_same_boundary_not_a_copy` executes both
   and asserts they agree on every probe.

**`CONTAINED_WORKER_SHA256` MOVES.** Deliberately, and it is the design
working rather than a cost to route around — that module's own docstring says
so: "a changed worker is a changed runtime identity, visible in each immutable
receipt". No test pins a literal digest; every one asserts the digest equals
the hash of the source, which stays true.

**What did NOT move, and why no committed root can change verdict.**
No record format. No digest ALGORITHM. No manifest schema. No
`_EPISTEMIC_CHECKS` entry, no `verify_root` finding, no `report.py` channel.
The changed code runs INSIDE the worker at execution time; it decides whether
a *future* proposal's source is admitted. A committed root's stored
`SimulationVerificationResult` — its verdict, fingerprint, blob refs and
`worker_sha256` — is bytes on disk that no code path in this change reads,
writes or re-derives. The distinction `INV-frozen-surfaces.md` draws in its
governing principle applies exactly: this alters what a FUTURE run may do,
which is ordinary work, not how a PAST run verifies.

`check: python -c "import ast, inspect; from deepreason.verification import contained; assert 'forbidden_attribute(node.attr)' in contained.CONTAINED_WORKER_SOURCE_V1; assert '__DEEPREASON_SANDBOX_GUARD__' not in contained.CONTAINED_WORKER_SOURCE_V1; ast.parse(contained.CONTAINED_WORKER_SOURCE_V1)"`

### Surface 3 (`verification/`) — `verification/simulation.py`

**What moved.** The attribute and name conditions inside `_guard`, from local
`startswith("_")` tests to the shared `forbidden_attribute` /
`forbidden_name`. Nothing else in the module; the worker protocol, the
resource limits, the IPC shape and every returned field are untouched.

**Blast radius on committed roots: none.** Same argument as above — `_guard`
decides admission of source at execution time and appears in no reader of a
stored record.

### Surface 3 — `verification/brokered.py`: NOT TOUCHED, and it still changed

`BROKERED_WORKER_SOURCE_V2` is derived from `CONTAINED_WORKER_SOURCE_V1` by
`_derive_v2`, so the brokered worker inherited the boundary without a line
being edited, and `BROKERED_WORKER_SHA256_V2` moves with it. This is recorded
rather than left implicit because a derivation that silently stopped deriving
would reopen the hole in a worker nobody thought to check;
`test_the_brokered_worker_inherits_the_boundary_by_derivation` pins it.

### Surfaces NOT touched

`capabilities/state.py`, `harness.py`, `invariants.py`, `run_manifest.py`,
`qualification.py`, and `route_fingerprint` in `llm/firewall.py` are
unmodified by this tranche.

`check: git diff --name-only origin/main...HEAD | grep -Ev '^(experiments|docs|tests)/' | sort > /dev/null; ! git diff --name-only origin/main...HEAD | grep -qE 'capabilities/state\.py|/harness\.py|/invariants\.py|/run_manifest\.py|/qualification\.py|llm/firewall\.py'`

---

## Non-frozen changes

| File | What | Why |
|---|---|---|
| `sandbox_guard.py` (new) | the one boundary definition | five copies of one rule is how one hole became five |
| `sandbox_os.py` (new) | the network-namespace probe, shared | a containment property resting on ONE layer is one bug away from absent — this tranche measured that |
| `oracle.py` | `_guard` consumes the shared boundary | the code-testing channel, where the escape reached the open internet |
| `programs.py` | `_validate_predicate` consumes it | predicate `eval()`, same escape family |
| `oracle_sandbox.py` | worker runs behind the network namespace; rlimits fail CLOSED | this channel is ON by default and carried NO OS boundary; its limits swallowed every `setrlimit` failure, so a host that refused one got an unlimited worker in silence |

`oracle_sandbox` DEGRADES where namespaces are unavailable rather than
refusing, unlike the opt-in contained runner which fails closed. The asymmetry
is deliberate and stated in the module: a host without user namespaces must
still be able to test code (operator, 2026-08-26, "Otherwise how is an LLM
supposed to test code"). Degrading is only safe because it is VISIBLE —
`sandbox_os.network_denial_available()` is what the tests assert, so the two
states are a fact a reader checks rather than an assumption they make.

---

## Two changes that were MINE to undo, recorded rather than quietly fixed

**1. A Name rule I added beyond the fix.** I gave the contained worker an
underscore-NAME rule for parity with its three siblings. It broke
`tests/test_brokered_simulation.py`, which documents a deliberate intention:
`__import__`, `open` and `eval` LOAD and then fail at runtime because the
whitelist does not define them. That design is safe, and my change moved the
refusal earlier for no security gain while contradicting a committed
intention. Removed. The contained worker's guard change is now the attribute
boundary and nothing else.

**2. A diagnostic string that had to change.**
`tests/test_security.py` asserted the word `"dunder"` appeared in the refusal
message. The rule is deliberately no longer dunder-shaped — that is the fix —
so the message could not keep the word. Minimally updated to assert the
property instead: that the access is refused, and that the diagnostic names
the offending attribute. This is the one fixture updated in this tranche, and
`CLAUDE.md`'s rule for that ("a fixture that depended on defective behavior
may be minimally updated only when the fix's design doc predicted it") is met
by this paragraph.

---

## Proof obligations and how each is discharged

| Obligation | Instrument |
|---|---|
| the escape is closed at every call site | `proof/containment_probe.py`, `_BEFORE.out` vs `_AFTER.out` from the same unchanged script |
| RED before, GREEN after | `proof/mutation_proof.sh` — reverts the boundary to the historical rule: 8 red, then 17 green |
| the rejected set is closed | `test_the_prefix_set_covers_every_public_introspection_attribute` — re-derived from the live interpreter |
| the worker's copy cannot drift | `test_the_frozen_worker_carries_the_same_boundary_not_a_copy` |
| no consumer reimplements the rule | `test_every_guard_call_site_consults_the_shared_boundary` — the architecture check the modularity law asks for |
| the OS layer is real, not self-reported | `test_the_network_namespace_actually_denies_network` — a differential, the shape SAFETY.md G5 says was missing |
| C8: nothing else breaks | full gate, plus a positive test per guard, plus the closure test |
