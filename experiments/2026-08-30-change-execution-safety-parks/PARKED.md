# PARKED.md — 2026-08-30 execution-safety parks (lane E, ultracode batch 2)

Every entry is a STOP: work this lane found, priced, and did NOT do, because
doing it would have crossed a frozen surface, left the park's own scope, or
decided a fork that is the operator's to decide. Each carries a ready-to-send
prompt. Nothing here was resolved in-batch.

Parked 2026-08-30, at the moment each was found, and pushed in the same act.

---

## S1 — FROZEN SURFACE 3 — the `filesystem` field claims a jail that does not exist

**Status.** MEASURED this tranche, against the real system, and left unfixed.

`src/deepreason/verification/contained.py:519` returns
`"filesystem": "ephemeral scratch workdir"` as a dict literal.
`proof/filesystem_not_a_jail.out` is this tranche's transcript: the prefix the
backend actually applies is
`('/usr/bin/unshare', '--map-root-user', '--net', '--')` — `--net` only, no
`--mount` — and a real interpreter launched under it with `cwd` set to the
scratch directory reads `/etc/hostname`, lists `/`, and writes a file into the
scratch directory's PARENT. `cwd` is the only confinement, and `cwd` is not a
jail.

**This is not a live escape, and the brief must say so where the transcript is
read.** The language boundary refuses `open` and every other builtin at all
five sandbox call sites (`tests/test_sandbox_guard.py`, the frame-walk tests),
so nothing model-authored code can express reaches the filesystem. What is
false is the FIELD: a reader who trusts it over-estimates the boundary by one
layer, which is the same failure mode that let G1-G3 survive a committed proof.

**Why this lane did not fix it.** P4's own scope sentence is "tests/ only ...
No src changes — if a differential goes RED, that is a finding for a defect
tranche, not something to fix here"
(`experiments/2026-08-27-change-execution-safety/PARKED.md:233-235`), and
`src/deepreason/verification/` is frozen surface 3
(`docs/map/INV-frozen-surfaces.md:47`). The operator has refused verbal grants
on the record (`INV-frozen-surfaces.md:59`).

**Note the overlap.** The 2026-08-27 park P9 already names the honest remedy at
`PARKED.md:481-484` ("keep cwd + RLIMIT_FSIZE and STOP reporting `"filesystem":
"ephemeral scratch workdir"` ... A truthful weaker string beats a false stronger
one"), and gap G2 at `SAFETY.md:396` rates it High. This entry adds the
measurement P9 was written without.

**Prompt:**

```
TARGET REPOSITORY: AHepi/DeepReason.

Route through deepreason-orchestrator. One tranche, one goal: no field of a
verification receipt names a confinement the OS layer does not provide.

THE MEASUREMENT, already taken — cite, do not re-derive:
experiments/2026-08-30-change-execution-safety-parks/proof/filesystem_not_a_jail.out.
A real interpreter under ContainedSimulationBackend.containment_prefix(), cwd
set to the scratch directory, reads /etc/hostname and writes outside that
directory. The prefix carries --net only. resource_limits() reports
"filesystem": "ephemeral scratch workdir" regardless.

READ FIRST, in this order: docs/map/INV-frozen-surfaces.md (this is surface 3
— verification/), then experiments/2026-08-27-change-execution-safety/
PARKED.md P9 and SAFETY.md gap G2, which already price the two roads.

THE FORK, which the design doc must price rather than assume:
  (a) tell the truth — replace the string with what is actually true of the
      scratch directory (a disposable cwd plus RLIMIT_FSIZE), the cheaper road
      P9 already recommends; or
  (b) make the string true — add a mount namespace to the prefix, which is a
      containment change with its own host-availability and fail-closed
      obligations.
Either way `src/deepreason/invariants.py:1854` consumes
`receipt.resource_limits["network"]`, and any receipt-shape change is a
replay-format change: state what a stored receipt from an earlier version does
under the new reader, under the 2026-08-14 law that old roots owe the future
nothing.

FROZEN SURFACE: this tranche CANNOT proceed without a written grant for
src/deepreason/verification/contained.py, requested in FIX.md before a line of
code exists, with tools/blast_radius.py's own contact list pasted verbatim and
each row disposed. The operator has refused verbal grants
(INV-frozen-surfaces.md:59).

TESTS: the effect-based pin already exists —
tests/test_sandbox_guard.py::test_the_contained_scratch_directory_is_the_cwd_and_does_not_survive.
Extend it; do not re-introduce a string assertion. The map check on
DR-SUB-verification's self-report Trap forbids one mechanically.

GATE: pytest tests/ -q -n 4, 0 failed. python tools/docs_verify.py.
```

---

## S2 — FROZEN SURFACE 3 — `resource_limits()` cannot report a containment failure

`resource_limits()["network"]` is the literal `False` at
`contained.py:520`, and `fingerprint()["network_denial"]` is the literal
`"namespace_unshared"` at `:502`. Neither consults `containment_prefix()` and
neither is recomputed at launch, so both survive any regression in the thing
they describe — which is exactly what `proof/mutation_proof.out` shows under
mutations M1 and M2: the network is reachable, or the prefix is not on the
argv, and both fields are unchanged.

This lane's differentials make the property MEASURED. They do not make the
field HONEST, and a consumer that reads the field still learns nothing.
`src/deepreason/invariants.py:1854` is such a consumer: it fails the replay
when the field is not `False`, i.e. it checks the confession.

**Why this lane did not fix it.** Same frozen surface, same scope sentence as
S1. Named separately because the remedy is different: S1 is a string that lies,
S2 is a getter that cannot tell the truth.

**Prompt:**

```
TARGET REPOSITORY: AHepi/DeepReason.

Route through dr-change-orchestrator. One tranche, one goal: a containment
field a replay validator consumes is DERIVED from the containment, not asserted
alongside it.

THE EVIDENCE, already taken — cite, do not re-derive:
experiments/2026-08-30-change-execution-safety-parks/proof/mutation_proof.out,
mutations M1 and M2. Under M1 the backend's probe drops --net, the network is
reachable from inside the prefix, and resource_limits()["network"] is still
False and fingerprint()["network_denial"] is still "namespace_unshared". Under
M2 the launch drops the prefix from the worker argv, and the same two fields
are again unchanged.

THE DESIGN QUESTION the SPEC must answer before code: what should the field say
on a host where containment_prefix() is non-empty but the namespace does not
deny? Fail closed at launch (the backend already fails closed on an EMPTY
prefix, contained.py:572-583) or report the measured state? Note that
invariants.py:1854 currently REFUSES any receipt whose field is not False, so
"report the measured state" changes what replay validation accepts and needs
the 2026-08-14 old-roots law read carefully.

FROZEN SURFACES: src/deepreason/verification/contained.py AND
src/deepreason/invariants.py are both surface 3. A written grant in SPEC.md
before code, per INV-frozen-surfaces.md:55-81. Do not proceed without it.

GATE: pytest tests/ -q -n 4, 0 failed.
```

---

## S3 — the two channels run duplicated probes, and a docstring says otherwise

`src/deepreason/sandbox_os.py:16-19` states that both backends that execute
untrusted Python use the probe that lives there: "``verification/contained.py``
(``sandboxed_python_v1``, opt-in) and ``oracle_sandbox.py``". `contained.py`'s
import block (lines 41-43) contains no `sandbox_os` import; it carries its own
copy of the probe at `contained.py:458-487`.

**This lane MEASURED the consequence rather than inferring it.**
`proof/mutation_proof.out` M1 mutates the contained backend's probe and the
code-testing differential stays GREEN; M7 mutates `sandbox_os`'s probe and the
contained differential stays GREEN. The two are independent subjects. Any
future claim of the form "the network property is proved" must name which
channel, or it is proved for neither.

**Why this lane did not fix it.** Deduplicating means editing
`contained.py` — frozen surface 3. The docstring alone could be corrected in a
docs pass, but correcting the docstring without deduplicating records the
divergence as intended rather than as a defect, which is a judgment call this
lane does not own.

**Prompt:**

```
TARGET REPOSITORY: AHepi/DeepReason.

Route through deepreason-orchestrator. One tranche, one goal: one probe, or two
probes that both documents describe truthfully.

THE CONTRADICTION: src/deepreason/sandbox_os.py:16-19 says
verification/contained.py uses the shared probe. contained.py:41-43 imports no
such thing and carries its own copy at :458-487.

THE MEASURED CONSEQUENCE — cite, do not re-derive:
experiments/2026-08-30-change-execution-safety-parks/proof/mutation_proof.out.
M1 mutates contained.py's probe; the sandbox_os differential stays green. M7
mutates sandbox_os's probe; the contained differential stays green.

THE FORK: (a) deduplicate — contained.py imports network_denial_prefix, which
is a frozen-surface-3 edit and needs a written grant in FIX.md before code;
(b) keep two probes and correct the sandbox_os docstring plus the map to say
so, which is cheap and honest but leaves two things to keep in agreement.
Price both; recommend one. Note the caching: both probes cache per process
(contained.py:466, sandbox_os.py:62) and sandbox_os has
reset_probe_cache(); a merged probe has one cache where there were two.

WHATEVER YOU CHOOSE: the two differentials in tests/test_sandbox_guard.py must
still each name which channel's prefix they exercised, and the mutation proof
above must still go RED per channel.

GATE: pytest tests/ -q -n 4, 0 failed. python tools/docs_verify.py.
```

---

## S4 — an unbacked self-report outside P4's named scope: `test_lean_backend.py:84`

`tests/test_lean_backend.py:84` asserts
`result.fingerprint["network"] is False` against an unconditional literal at
`src/deepreason/verification/lean.py:125`, under a FAKE lean fixture. It is the
same shape P4 names, and it is NOT covered by P4's scope sentence, which names
`verification/contained.py` and `oracle_sandbox.py`.

Reported, not fixed. A differential is not obviously constructible here: the
fixture is a stand-in for a toolchain that is not installed, so there is no real
child whose network access could be observed. The honest options are to give the
lean backend a real containment (large) or to stop reporting a field the backend
does not enforce (frozen surface 3). That is a design question, not a test edit.

**Prompt:**

```
TARGET REPOSITORY: AHepi/DeepReason.

Route through deepreason-orchestrator. One tranche, one goal: the lean backend
either enforces the network property it reports, or stops reporting it.

THE SHAPE, and why it is the same defect P4 named:
src/deepreason/verification/lean.py:125 returns "network": False as an
unconditional literal; tests/test_lean_backend.py:84 asserts it under a FAKE
lean fixture. No probe, no child, no effect. Compare
tests/test_workload_formal.py:133-153, which asserts
detail["network_isolated"] is True and IS safe, because the program under test
calls socket.socket() and raises SystemExit(2) if it succeeds — that is the
positive example.

Read experiments/2026-08-30-change-execution-safety-parks/DELIVERY.md first;
this was found and deliberately not fixed there, with the reason recorded.

FROZEN SURFACE: verification/lean.py is surface 3. Written grant in FIX.md
before code.

GATE: pytest tests/ -q -n 4, 0 failed.
```

---

## S5 — E2's three-road fork: the gate needs two dependencies the install does not declare

**This is the fork this lane was told to price and NOT decide.**

The facts, all verified in-tree this session:

* `pyproject.toml:11-21` declares exactly three runtime dependencies —
  `pydantic>=2.7`, `pyyaml>=6.0`, `fastembed>=0.3`. There is no `setup.py` and
  no `setup.cfg`; `pyproject.toml` is the sole declaration.
* `pyproject.toml:23-27` declares a `dev` extra of exactly `pytest>=8.0` and
  `ruff>=0.4`.
* CLAUDE.md's documented gate is `pytest tests/ -q -n 4`, which requires
  `pytest-xdist`. `pytest-xdist` is not an import anywhere in `tests/`; it is
  required by the `-n 4` flag alone.
* `jsonschema` is imported at exactly one site in the whole repository:
  `tests/test_schema_carries_every_prose_rule.py:170`.
* Twelve lines below that bare import, line 182 reads
  `jsonschema = pytest.importorskip("jsonschema", reason="optional checker")`.
  The bare import at :170 runs first and raises, so the guard never gets to
  work. **MEASURED, not asserted** — `proof/road_c_evidence.out`: with
  `jsonschema` made absent, the file as committed gives
  `1 failed … ModuleNotFoundError: No module named 'jsonschema'`; with line 170
  deleted and nothing else changed, the same node gives
  `SKIPPED [1] … optional checker`, `1 skipped`. Road C closes the `jsonschema`
  half. It does NOT close `-n 4`, which needs `pytest-xdist` and which no
  import guard can reach.
* The gap is not hypothetical and not this container's peculiarity: it was
  measured twice. `experiments/2026-08-27-change-execution-safety/
  DELIVERY.md:127-152` records `1 failed, 4334 passed` on
  `ModuleNotFoundError: No module named 'jsonschema'`, and
  `experiments/2026-08-29-ultracode-batch-2/SETUP.md` records
  `ModuleNotFoundError: No module named 'xdist'` after the documented install
  on the container this batch ran on.

**The three roads, priced.**

| | What it does | Cost | What it leaves | Reversible? |
|---|---|---|---|---|
| **A. Document the gap** (shipped by this lane as E2) | CLAUDE.md's Environment and Build-and-test blocks name the two packages and carry the install line | one doc edit, no gate risk | the install is still insufficient; every fresh container still needs the extra line, it just knows to | trivially |
| **B. Declare the dependencies** in `pyproject.toml`'s `dev` extra | `pip install -e ".[dev]"` becomes sufficient | one line each; the census is already done and is small — `jsonschema` is the ONLY undeclared third-party import in `tests/` and `mini/`, and `pytest-xdist` is not an import at all | nothing; this is the root cause | trivially |
| **C. Delete the redundant bare import** at `tests/test_schema_carries_every_prose_rule.py:170` | the existing `importorskip` at :182 starts working; the suite runs without `jsonschema` at all — **measured, `proof/road_c_evidence.out`** | one deleted line | `-n 4` still needs `pytest-xdist`, so C alone does not close the gap | trivially |

They are not exclusive. **B + C together make A merely historical**: with C the
suite no longer needs `jsonschema`, and with B `pytest-xdist` arrives with the
dev extra.

**Recommendation: B and C, with A kept.** B is the root cause and the census is
already done. C is strictly correct on its own terms — a bare import twelve
lines above its own `importorskip` is a defect in that test regardless of what
`pyproject.toml` says, and it is the only line in the repository that makes
`jsonschema` mandatory. A is kept because CLAUDE.md's Environment section is
what a rolled-back container actually pastes, and a reader who lands there
should not have to re-derive why.

**Why this lane did not do B or C.** E2's scope as briefed is DOCS ONLY.
`pyproject.toml` is not frozen, but it is not docs. C is a `tests/` edit and so
sits inside E1's scope rather than E2's — the parent must say whether E1 was
meant to carry it. This lane did NOT implement C: see DELIVERY.md, E1 residue.

**Prompt (implements B and C in one tranche):**

```
TARGET REPOSITORY: AHepi/DeepReason.

Route through deepreason-orchestrator. One tranche, one goal: the setup
CLAUDE.md documents is sufficient for the gate CLAUDE.md documents, from a
clean environment, with nothing installed by hand.

THE DEFECT, measured twice — cite, do not re-derive:
  experiments/2026-08-27-change-execution-safety/DELIVERY.md:127-152
    (1 failed, 4334 passed; ModuleNotFoundError: No module named 'jsonschema')
  experiments/2026-08-29-ultracode-batch-2/SETUP.md
    (ModuleNotFoundError: No module named 'xdist' after the documented install)

THE CENSUS IS ALREADY DONE — verify it, do not redo it. An AST census over
tests/**/*.py and mini/**/*.py yields exactly four non-stdlib, non-first-party
top-level imports: pydantic (declared), pytest (declared dev), yaml (declared
as pyyaml), jsonschema (NOT declared, one site:
tests/test_schema_carries_every_prose_rule.py:170). pytest-xdist is not an
import at all; the -n 4 flag needs it.

DO BOTH:
  B. pyproject.toml optional-dependencies.dev gains jsonschema and pytest-xdist.
  C. delete the bare `import jsonschema` at
     tests/test_schema_carries_every_prose_rule.py:170. Line 182 twelve lines
     below already reads
     `jsonschema = pytest.importorskip("jsonschema", reason="optional checker")`
     and has never been able to run. C is correct independently of B, and is
     already measured: experiments/2026-08-30-change-execution-safety-parks/
     proof/road_c_evidence.out shows the node FAILING with jsonschema absent
     and SKIPPING once line 170 is gone. Re-run that script rather than
     re-deriving it.

PROOF OBLIGATION: a fresh virtualenv, `pip install -e ".[dev]"`, then the
documented gate, 0 failed. Paste both. Then, in a SECOND fresh virtualenv
without jsonschema, show the guarded test SKIPPING rather than failing — that
is what proves C.

WHILE YOU ARE THERE: reconcile CLAUDE.md's Build-and-test block, which lane E
already edited on 2026-08-30 to name both packages
(experiments/2026-08-30-change-execution-safety-parks/DELIVERY.md, E2). If B
makes the extra install line unnecessary, DELETE it rather than leaving two
instructions that disagree.

GATE: pytest tests/ -q -n 4, 0 failed. python tools/docs_verify.py.
```

---

## S6 — reported, not a work item: the branch tripwire cannot see this lane's frozen surface

`docs/map/INV-frozen-surfaces.md:297`'s check greps the changed-path list for
`capabilities/state\.py|/harness\.py|/invariants\.py|/run_manifest\.py|/qualification\.py|llm/firewall\.py`.
`src/deepreason/verification/` — half of frozen surface 3, and the whole of
this lane's temptation — matches none of those alternatives. RECON-SHARED
measured this independently.

This lane therefore did NOT use the tripwire as its cone check. The cone was
measured against the seven paths CLAUDE.md:92-95 names, over the actual working
diff, and reported in DELIVERY.md. Recording it here so no later reader cites
this lane's green tripwire as evidence that `verification/` was untouched.

No prompt: repairing the tripwire is `INV-frozen-surfaces.md` work, and that
document is another lane's cone this batch.
