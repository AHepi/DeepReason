# PARKED — noticed in this tranche, deliberately not fixed

## PT1-A — `cycle_soak.py --case pc1` cannot build a manifest on `main`

**What.** `python -u scripts/cycle_soak.py --case pc1` dies before any
soak runs:

```
File "experiments/2026-08-25-change-constructive-frontier/build_manifest_pc1.py", line 125, in build
File "src/deepreason/run_manifest.py", line 3845, in compile_run_manifest
pydantic_core._pydantic_core.ValidationError: 1 validation error for RunManifest
  Value error, V6_SIMULATION_TOOLCHAIN_REQUIRED: policy must bind one frozen toolchain
```

One of the seven soak cases is therefore unrunnable, which matters
because CLAUDE.md makes a green soak on the launch config a precondition
for every live launch: a launch whose shape is P-C1's cannot satisfy that
precondition at all. Not diagnosed here — out of cone (`run_manifest.py`
is frozen surface 4, and a manifest tranche was live in a parallel window
when this was found).

**Ready-to-send prompt:**

```
Route: deepreason-orchestrator (defect).

Goal, one sentence: make `python -u scripts/cycle_soak.py --case pc1`
build its manifest again, so the P-C1 constructive shape can satisfy
CLAUDE.md's "no live launch without a green soak on the launch config"
precondition.

Reproduce (offline, no credential, ~2s):
  python -u scripts/cycle_soak.py --case pc1 --cycles 3 --keep --out /tmp/x
  -> V6_SIMULATION_TOOLCHAIN_REQUIRED: policy must bind one frozen toolchain

The question to answer first, because it decides the shape of the fix:
did the manifest REQUIREMENT move (run_manifest.py now demands a frozen
simulation toolchain a P-C1-shaped policy never bound), or did the CASE
BUILDER drift from the committed P-C1 config it claims to reproduce?
`git log` over src/deepreason/run_manifest.py and
experiments/2026-08-25-change-constructive-frontier/build_manifest_pc1.py
since 2026-08-25 is the cheapest place to look. If the requirement moved,
note that a committed live config stopped compiling, which the
all-configurations law (CLAUDE.md, 2026-08-12) makes a finding in its own
right -- every input that PARSES must COMPILE, with impossibility surfacing
at the point of use, not at compile.

Evidence pointers:
  scripts/cycle_soak.py --list-cases          (seven cases; pc1 is one)
  experiments/2026-08-25-change-constructive-frontier/build_manifest_pc1.py:125
  src/deepreason/run_manifest.py:3845          FROZEN SURFACE 4 -- read
      docs/map/INV-frozen-surfaces.md before designing; if the fix needs
      to touch the validator, request the grant in the design document
      BEFORE writing code, per the operator's standing instruction.
  experiments/2026-08-28-fix-swallowed-terminal-lifecycle-refusal/REPRO.md
      (where this was met; the P6 tranche did not pursue it)

End state: `--case pc1` soaks green to its requested cycle count; a
regression test would fail today; the other six cases still build; full
gate 0 failed; map moved in the same commit.
```

## PT1-B — P6's parked recipe names a soak case that does not exist

**What.** P6's ready-to-send prompt (branch
`claude/spec-to-code-technique-k5209o`, PARKED.md §P6) gives its offline
reproduction as `--case pt1`. `main`'s soak has no such case. Not a code
defect and not fixed here; recorded in this tranche's REPRO.md with the
working substitute (`--case epoch3`) so the next reader does not lose the
time twice. No follow-up tranche is warranted — the correction lives in
REPRO.md, which is where a future runner of P6 will look.
