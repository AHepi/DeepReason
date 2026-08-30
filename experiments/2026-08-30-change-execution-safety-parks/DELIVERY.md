# DELIVERY.md — 2026-08-30 execution-safety parks (lane E, ultracode batch 2)

Two parks from `experiments/2026-08-27-change-execution-safety/PARKED.md`,
worked strictly in order: **E1 = P4** (containment tests pin self-reported
strings) finished and committed before **E2 = P6** (the documented gate needs
two dependencies the documented install does not declare) began.

This document is written to stand alone for a per-tranche review. Everything a
reviewer needs to disbelieve it is in `proof/`, as commands with recorded
output, not as claims.

## Map preflight

Resolved before any file was opened, per CLAUDE.md's map-preflight rule. The
seam was read before the subsystems and `INV-frozen-surfaces.md` before
anything was designed.

| id | why it is in this lane | citation |
|---|---|---|
| `DR-INV-frozen-surfaces` | read FIRST, always. Establishes that `src/deepreason/verification/` is inside surface 3, which is what makes E1 a tests-and-probes lane rather than a fix | `docs/map/INV-frozen-surfaces.md:29` ("The five frozen surfaces"), `:47` ("### 3. Replay-validation record formats — `invariants.py`, `verification/`") |
| `DR-INV-evidence-channels` | the AUTHORITY P4 itself cites for the standard | `docs/map/INV-evidence-channels.md:173-178` — "The flag is the cheap half. Assert the values a dispatch or a controller would actually CONSUME" |
| `DR-SEAM-capabilities-x-channels` | the seam this work sits on: a channel that reports ON over a capability road that may be severed | `docs/map/INDEX.md:25` |
| `DR-SUB-verification` | owns `verification/` and `invariants.py`; carries the Trap that already stated P4's rule without a check | `docs/map/SUB-verification.md` header `Owns:`; the self-report Trap, formerly checkless |

**The surface-3 boundary, in one sentence:** every file whose behaviour this
lane measures — `verification/contained.py`, `verification/simulation.py`,
`invariants.py` — is inside frozen surface 3, so this lane reads them, launches
them, and mutates COPIES of them, and edits none of them.

---

# E1 — P4: containment tests pinned self-reported strings

## What was asked

Verbatim, `experiments/2026-08-27-change-execution-safety/PARKED.md:213-240`:
"every containment property claimed by `verification/contained.py` and
`oracle_sandbox.py` is pinned by a DIFFERENTIAL that can fail, never by a string
the backend reports about itself." Scope: "tests/ only, plus whatever docs/map
check makes the standard enforceable. No src changes — if a differential goes
RED, that is a finding for a defect tranche, not something to fix here."

Why it matters, in the record's own words: this is how the escape survived a
committed containment proof. `SAFETY.md:295-298` — "**No committed test covers
this.** `tests/test_contained_simulation_runner.py:134` asserts
`reported["filesystem"] == "ephemeral scratch workdir"` — a string the backend
reports about itself". Gap `G5` at `SAFETY.md:399` rates it Medium **"— this is
why G1–G3 went unnoticed"**.

## The ten confessions, and what replaced each

A confession is an assertion whose subject is a value the backend states about
itself. All ten were dict literals with no consumer that could contradict them:
`contained.py:502` (`fingerprint()["network_denial"]`), `:519`
(`resource_limits()["filesystem"]`), `:520` (`["network"]`), `:521`
(`["network_denial"]`).

| # | was | file:line (before) | now measured by |
|---|---|---|---|
| 1 | `reported["network"] is False` | `test_contained_simulation_runner.py:146` | D1 |
| 2 | `reported["filesystem"] == "ephemeral scratch workdir"` | `:147` | D4 |
| 3 | `fingerprint["network_denial"] == "namespace_unshared"` | `:114` | D3 |
| 4 | `receipt.resource_limits["network"] is False` | `:376` | D1 (+ kept as CARRIAGE, below) |
| 5 | `receipt.resource_limits["filesystem"] == …` | `:377` | D4 |
| 6 | `limits["network"] is False` | `test_simulation_runner_default.py:241` | D1 |
| 7 | `limits["network_denial"] == "namespace_unshared"` | `:242` | D3 |
| 8 | `result.fingerprint["network_denial"] == …` | `:243` | D3 |
| 9 | `attempt.fingerprint["network_denial"] == …` | `:327` | D3 |
| 10 | `receipt.resource_limits["network"] is False` | `:328` | D1 (+ kept as CARRIAGE) |

Also retired: the self-to-self comparison at
`test_contained_simulation_runner.py:148-149`, which asserted
`resource_limits()[k] == _containment_limits(…)[k]` — the same pure function on
both sides of the equals sign, true whether or not one `setrlimit` ever runs.
Replaced by D5.

**Two assertions were deliberately KEPT, and must not be mistaken for leftovers.**
`tests/test_contained_simulation_runner.py` and
`tests/test_simulation_runner_default.py` each still assert
`receipt.resource_limits["network"] is False`, each under a comment naming why:
`src/deepreason/invariants.py:1854` fails the replay with `capability-receipt`
when that field is anything but `False`, so the receipt must keep CARRYING it.
That is a coupling check on a field a reader consumes, not a containment check.
Whether the field is TRUE is now measured by D1.

## The seven differentials

All seven live in `tests/test_sandbox_guard.py`'s
`--- the OS layer, which does not depend on the guard being right ---` section,
which is where the two pre-existing genuine differentials already were.

| | test | the concrete observable |
|---|---|---|
| D1 | `test_the_contained_backend_prefix_actually_denies_network` | the kernel's interface table (`socket.if_nameindex()`) and the errno a `connect` returns, inside and outside `ContainedSimulationBackend.containment_prefix()` |
| D2 | `test_the_network_namespace_actually_denies_network` (existing, now two-armed) | the same, for `sandbox_os.network_denial_prefix()` — the code-testing channel |
| D3 | `test_the_contained_worker_argv_really_carries_the_probed_prefix` | the actual `argv` of a real `Popen` inside a real `verify()` |
| D4 | `test_the_contained_scratch_directory_is_the_cwd_and_does_not_survive` | the launch's `cwd=`, the `HOME`/`TMPDIR` the worker is given, and whether the directory exists on disk afterwards |
| D5 | `test_the_contained_child_really_receives_every_declared_rlimit` | `getrlimit` read back out of a real child launched through `_apply_containment_limits`, against a child launched without it |
| D6 | `test_the_contained_worker_environment_reaches_the_child_scrubbed` | `os.environ` as a real child sees it, launched under the `env=` of the real contained launch |
| D7 | `test_the_code_testing_worker_environment_reaches_the_child_scrubbed` | the same for `oracle_sandbox._worker_environment()`, which had NO test anywhere in `tests/` before this tranche |

**Every differential is two-armed and cannot pass on one arm.** D1 and D2
measure the OUTSIDE arm first and `pytest.skip` when the host itself has only
loopback; D5 asserts every one of five limits DIFFERS between the contained and
the bare child; D6 and D7 assert the same secret IS visible to an unscrubbed
child before asserting it is not visible to the scrubbed one.

## RED/GREEN — the transcript for every differential

`proof/mutation_proof.sh`, output at `proof/mutation_proof.out`, exit 0.

The mutation is applied to a COPY of `src/` in a temporary directory and reached
through `PYTHONPATH`; the repository's own `src/` is never written to. That is a
deliberate departure from the 2026-08-27 tranche's in-place-with-a-trap
`mutation_proof.sh`: every module these mutations touch except `sandbox_os.py`
is inside frozen surface 3, and this lane holds no grant to edit one even
transiently.

| mutation | what it weakens | differential that goes RED | the confession, under the SAME mutation |
|---|---|---|---|
| M1 | `contained.py`'s probe drops `--net` (prefix still non-empty, so the backend still believes it is contained) | **D1** — `assert ['eth0','ifb0','ifb1','lo'] == ['lo']` | `resource_limits()["network"] -> False`, `fingerprint()["network_denial"] -> namespace_unshared`. **Both unchanged while the network is reachable.** |
| M2 | the launch drops the prefix from the worker argv | **D3** | same two fields, again unchanged. And D1 stays GREEN — it probes the prefix, not the launch, so D3 is the only thing that catches this |
| M3 | `_apply_containment_limits` stops applying `RLIMIT_NOFILE` | **D5** — `assert 20000 == 64` | the retired self-to-self comparison still holds for all five keys |
| M4 | the ephemeral scratch directory stops being removed | **D4** | `resource_limits()["filesystem"] -> 'ephemeral scratch workdir'`, unchanged |
| M5 | the launch stops passing `env=`, so the worker inherits ours | **D6** | `test_worker_environment_is_a_fixed_allowlist` still PASSES — it asserts the dict, not the child |
| M6 | `oracle_sandbox._worker_environment` keeps `OLLAMA_API_KEY` | **D7** — `assert 'OLLAMA_API_KEY' not in [...]` | (no prior test existed to stay green) |
| M7 | `sandbox_os`'s probe drops `--net` | **D2** | — and D1 stays GREEN, so neither channel's differential says anything about the other |

Every mutation is followed by a `GREEN restored` line in the same transcript,
each `1 passed`.

**The vacuity demonstration, section V of the same transcript.** The whole
pytest process is re-run inside `unshare --map-root-user --net`, i.e. on a host
whose only interface really is `lo`:

    --- the two differentials, inside a lo-only namespace ---
    ss
    SKIPPED [1] code-testing channel: host itself has only loopback, nothing to deny
    SKIPPED [1] contained simulation backend: host itself has only loopback, nothing to deny
    2 skipped, 24 deselected
    --- the retired one-armed assertion, in the same namespace ---
      one-armed assertion inside["interfaces"] == ["lo"]: PASSED, vacuously

That is the argument for the second arm, measured rather than asserted: where
the two-armed form reports "no evidence", the one-armed form the tree carried
until this tranche reports "pass".

## A differential that went RED against the REAL system — recorded, not fixed

`proof/filesystem_not_a_jail.sh`, output at `proof/filesystem_not_a_jail.out`.

    the prefix the backend actually applies : ('/usr/bin/unshare', '--map-root-user', '--net', '--')
    mount-namespace flag present            : False
    resource_limits()["filesystem"]         : 'ephemeral scratch workdir'

    inside the prefix, cwd=the scratch dir:
      {"cwd": "/tmp/deepreason-jail-probe-5jtkdwsm", "read_/etc/hostname": "vm",
       "wrote_outside_scratch": "/tmp/deepreason-jail-probe-marker",
       "root_listing_visible": ["bin", "bin.usr-is-merged", "boot", "container_info.json", "dev", "etc"]}
      the marker exists outside the scratch dir: True
      its contents                             : WRITTEN FROM INSIDE THE PREFIX

**This is not a live escape**, and the transcript carries that sentence beside
the measurement. The language boundary refuses `open` and every other builtin at
all five sandbox call sites, so nothing model-authored code can express reaches
the filesystem. What is falsified is the FIELD. Per P4's own scope sentence it is
a finding for a defect tranche: parked as `PARKED.md` **S1**, with the
frozen-surface grant it needs spelled out. No `src/` change was made.

Consequently D4 pins what is observably TRUE of the scratch directory — it is
the launch `cwd`, it is what `HOME` and `TMPDIR` point at, and it does not
survive `verify()` — and asserts no string at all.

## The map half

`docs/map/SUB-verification.md`'s self-report Trap already STATED P4's rule and
was the only Trap in its neighbourhood carrying no `check:`. It now carries one,
and the Trap text is rewritten (never deleted) to say when the rule was
addressed, by what, and what residue remains.

    check: python -m pytest tests/test_sandbox_guard.py -q -k "denies_network or
    argv_really_carries or scratch_directory_is_the_cwd or every_declared_rlimit or
    environment_reaches_the_child" && test "$(grep -c 'def test_the_contained\|def
    test_the_network_namespace\|def test_the_code_testing_worker_environment'
    tests/test_sandbox_guard.py)" -eq 7 && ! grep -rqE "assert .*(ephemeral scratch
    workdir|network_denial)" tests/ --include=*.py

Three clauses: the differentials pass; all seven still exist under their names;
and no test asserts a self-reported containment string again. **The third clause
is what makes the standard enforceable rather than merely stated** — a future
test that re-introduces one turns the map red.

`docs_verify --audit` refuses a check that cannot fail, so each clause is shown
failing: `proof/map_check_falsifiable.sh`, output at
`proof/map_check_falsifiable.out`, exit 0.

    --- unmutated: expect exit 0 ---            exit=0
    --- F1: one differential renamed away ---   exit=1 (non-zero required)
    --- F2: a self-reported filesystem string asserted again --- exit=1 (non-zero required)
    --- restored ---                            exit=0
    restoration: byte-identical to the pre-run file

Clause 1 is not re-proved there: `proof/mutation_proof.out` already shows all
seven of those tests going RED under source mutations, and the check runs exactly
those tests.

## Ring results, exact

    $ python -m pytest tests/test_sandbox_guard.py \
        tests/test_contained_simulation_runner.py \
        tests/test_simulation_runner_default.py -q
    51 passed in 6.19s

    $ python -m pytest tests/test_sandbox_guard.py -q
    26 passed in 1.95s      (18 before this tranche, 26 after; +7 differentials,
                             D2 rewritten in place)

    $ ruff check tests/test_sandbox_guard.py \
        tests/test_contained_simulation_runner.py tests/test_simulation_runner_default.py
    All checks passed!

No full gate was run by this lane. The batch's integration step owns the single
full gate and the single `docs_verify` on an otherwise idle box
(`dr-drive-harness` §5b: never run them concurrently). Stated plainly so the
number is not assumed: **this lane did not measure a full-gate count.**

## The cone, as measured

    $ git diff --name-only
    docs/map/SUB-verification.md
    tests/test_contained_simulation_runner.py
    tests/test_sandbox_guard.py
    tests/test_simulation_runner_default.py
    $ git ls-files --others --exclude-standard
    experiments/2026-08-30-change-execution-safety-parks/…

Frozen-surface contact, tested against the SEVEN paths CLAUDE.md:92-95 names
rather than against the `INV-frozen-surfaces.md:297` tripwire:

    $ { git diff --name-only; git ls-files --others --exclude-standard; } \
        | grep -E "src/deepreason/(capabilities/state\.py|harness\.py|invariants\.py|verification/|run_manifest\.py|qualification\.py|llm/firewall\.py)"
    (no output)   rc=1

The line-297 tripwire also exits 0 — with `git rev-parse origin/main` resolving
to `84514a0280f45d29e5066bb3be3d273ba73798db`, so it is not the vacuous-on-a-
missing-ref case. **That green is not this lane's evidence**, and `PARKED.md` S6
records why: the tripwire's regex does not match `src/deepreason/verification/`
at all, so it could not have caught the contact this lane was most at risk of
making.

## Honest residue for E1

* **`"filesystem": "ephemeral scratch workdir"` is still false in the shipped
  code.** Measured, transcribed, parked (S1). Not fixed: frozen surface 3.
* **`resource_limits()` still cannot report a containment failure** — the fields
  are literals that no launch recomputes. The property is now measured; the
  field is still a confession, and `invariants.py:1854` still consumes the
  confession. Parked (S2).
* **The two channels still run duplicated probes**, and `sandbox_os.py:16-19`
  still claims otherwise. M1/M7 measure the independence. Parked (S3).
* **`tests/test_lean_backend.py:84` is the same shape and was left alone** —
  outside P4's named scope, and no differential is obviously constructible
  against a FAKE lean fixture. Parked (S4), with the reason.
* **A differential this lane could NOT make fail: none.** All seven were shown
  RED. What could not be shown is a mutation for D2's *outside* arm specifically
  — M7 reds D2 through its inside arm — and the outside arm's necessity is
  therefore demonstrated by the vacuity section V rather than by a mutation.
* **Two `resource_limits["network"] is False` assertions survive by design**, as
  carriage checks for `invariants.py:1854`. A reader who counts confessions will
  find two; the comment beside each says why it is not one.
* **`seccomp` (`verification/_sandbox.py`) was not measured.** It is named in
  `SUB-verification.md`'s routing row for the containment shape, and no
  differential in this tranche touches it.
* **No live run.** This batch is offline by construction
  (`experiments/2026-08-29-ultracode-batch-2/SETUP.md`: no `OLLAMA_API_KEY`, no
  `env` file). Every measurement here is local process behaviour, which is what
  the property is about.
