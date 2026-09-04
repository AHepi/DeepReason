# Ready-to-send prompts

One prompt per finding this window produced. Each is self-contained: paste it
whole into an executor window. Nothing here is a fix — this tranche fixes
nothing, per the read-only contract of a review window.

---

## P1 — five of the soak's nine cases no longer compile (defect family)

Priority: **first**. It is independent of the missing branch, it restores the
instrument's only demonstrated catch of a recorded death, and it is small.

```
EXECUTOR WINDOW — DEFECT: five of scripts/cycle_soak.py's nine committed
cases no longer compile on main, including the one case that caught a
recorded death.

Read CLAUDE.md IN FULL. Load deepreason-orchestrator, dr-drive-harness and
pinker-write-for-readers. Base on main at or after 643dd8ea1. Write into
experiments/2026-09-04-defect-rotted-soak-cases/ on your own branch.

THE DEFECT, measured 2026-09-04 in a shallow-clone container
(experiments/2026-09-04-review-judge-seat-matrix-soak/VERDICT.md, section
"A FINDING THIS WINDOW DID NOT GO LOOKING FOR", raw output in that
tranche's proof/case_*.txt):

    for c in epoch3 pr1 pc1 pc2 pc2b split-legs hv-grant reach-rich pa1; do
      python -u scripts/cycle_soak.py --case $c --cycles 1
    done

  compiles and runs: epoch3, reach-rich, hv-grant, pa1
  DIES AT COMPILE:   pr1, pc1, pc2, pc2b, split-legs
    pydantic_core.ValidationError: 1 validation error for RunManifest
      Value error, V6_SIMULATION_TOOLCHAIN_REQUIRED: policy must bind one
      frozen toolchain
    raised from src/deepreason/run_manifest.py inside compile_run_manifest,
    via experiments/2026-08-25-change-constructive-frontier/build_manifest_pc1.py

WHY IT MATTERS, in one line each:
  - `split-legs` is the case that CAUGHT the P-C2b replay-invalid death
    (exit 1, [FAIL] A3 260 violations, first violation byte-identical to the
    P-C2b soak's — experiments/2026-08-27-defect-split-leg-recording/REPRO.md:34).
    That catch is currently unreproducible.
  - pc1/pc2/pc2b/split-legs/pr1 are EVERY case that arms llm/split.py's
    two-leg protocol. With all five dead, no committed instrument exercises
    a split seat call at all.
  - docs/AUDIT_BASELINES.md:210 baselines ONLY `--case epoch3`, a survivor,
    so this rot is invisible to the standing baseline and was not caught by it.

DIAGNOSE FROM THE RECORD FIRST, not from code reading: the same
V6_SIMULATION_TOOLCHAIN_REQUIRED shape was diagnosed and repaired for the MAP
CHECKS in experiments/2026-08-30-fix-rotted-map-checks/ (see its DELIVERY.md
around lines 206-250 and 376). Read that before touching run_manifest.py —
the cause may be identical and already written up, which would make this a
recurrence rather than a new defect.

CONSTRAINTS:
  - src/deepreason/run_manifest.py is NOT on the frozen list, but
    "Anything altering qualification subject digests" IS. Check
    docs/map/INV-frozen-surfaces.md BEFORE designing, and if the smallest
    correct fix moves a subject digest, STOP and ask.
  - Prefer fixing the CASE BUILDERS over the compiler if the compiler is
    correct and the committed configs are the things that went stale. Say
    which it is, with evidence, before you change either.
  - Every repaired case must be mutation-proven: show it compiling AND show
    its assertions actually firing on a record that violates them.

ACCEPTANCE:
  1. All nine cases compile. Paste the sweep above with its output.
  2. `--case split-legs` reproduces its historical catch on a record that
     still has the defect, or — if the defect is fixed — exits 0 with A3
     clean, and you show the assertion firing under mutation.
  3. `--case epoch3` still exits 0 (the docs/AUDIT_BASELINES.md:210 baseline).
  4. Full gate 0 failed. Baseline in this container is 4961 passed, 6 skipped
     (measured 2026-09-04 on 643dd8ea1). Install BOTH lines from CLAUDE.md's
     Environment section and use `python -m pytest`, never the `pytest`
     console script — it resolves to a different interpreter and produces a
     ModuleNotFoundError that looks like a code defect.
  5. docs_verify at its recorded baseline (5 or 6 failed on a shallow clone).
  6. Update docs/AUDIT_BASELINES.md so the case inventory itself is baselined,
     not just `--case epoch3`. A rot that the baseline cannot see is a rot
     that recurs.

FINAL MESSAGE: plain words, first sentence is the outcome, one closing analogy.
```

---

## P2 — the soak covers none of the last three recorded deaths (change family)

Priority: **after P1**, and only on the operator's word — this is new
machinery, not a repair.

```
EXECUTOR WINDOW — CHANGE: give scripts/cycle_soak.py the three mechanisms
the last three recorded deaths actually died of.

Read CLAUDE.md IN FULL. Load dr-change-orchestrator, dr-drive-harness and
pinker-write-for-readers. Base on main at or after 643dd8ea1 AND after the
rotted-cases defect tranche lands. Write into
experiments/2026-09-XX-change-soak-fault-mechanisms/ on your own branch.

THE EVIDENCE THAT MOTIVATES IT
(experiments/2026-09-04-review-judge-seat-matrix-soak/VERDICT.md, THE DEATH
TABLE rows 5, 6, 8 — read it before designing):

  - P-A1 (run 4565139800f5ca02): `--case pa1 --cycles 8` — the death's own
    committed config shape — EXITS 0 with every seam green. The death needed
    41 RemoteDisconnected transport faults; the soak has no fault injection
    (grep -i transport scripts/cycle_soak.py returns nothing).
  - P-S1 M-1: needed a completion cut before its JSON (natural_stop false on
    5 of 6 legs). The stub emits exactly ONE finish_reason, hard-coded "stop"
    (scripts/wheel_operational_smoke.py:1285, sole occurrence), and derives
    usage from content length. Truncation and zero-token calls are
    structurally unreachable.
  - P-A2 epoch 4: needed a kill mid-cycle and a resume. The soak's whole
    assertion set is A1-A6 and not one looks at continuability
    (grep -i "terminal_lifecycle\|continuab\|receipt\|outstanding_work"
    scripts/cycle_soak.py returns nothing). Before that defect was fixed, the
    soak reported exit 0 on the very root whose `continue` returned
    CONTINUE_TYPED_STOP_REQUIRED.

THE THREE MECHANISMS, as requirements to spec (do NOT start coding):
  R1. Transport-fault injection: a flag that makes the stub drop connections
      on a named endpoint for N calls, so a seat can be driven to
      `smallest_authorized_contract_schema_exhausted` while a sibling seat
      stays healthy — the P-A1 shape exactly, including the asymmetry.
  R2. Completion truncation: a flag that makes the stub return
      finish_reason "length" with the body cut, so a split extraction leg
      fails to serialize and compact recovery ratchets the cap down.
  R3. A continuability assertion (A7): after the terminal, assert
      terminal_lifecycle_refusal is None, the receipt was taken, and
      `deepreason continue` is admissible. This is the 2026-08-29 operator
      law — "every stop secures continuation" — given an instrument.

DESIGN LAWS THAT BIND THIS WORK:
  - Modularity is enforced and customisation is easy (2026-08-26): each fault
    mechanism is CONFIGURATION or a registered artifact, never a code edit to
    use. Ship an architecture test that goes red if a consumer bypasses the
    interface.
  - All configurations are allowed (2026-08-12): a case that cannot produce a
    fault COMPILES and carries a typed notice; it never refuses.
  - A seam reported not-coverable or partial is NOT coverage. Keep the
    2026-08-23 tranche's standing honesty rows and add rows for the new
    mechanisms in the same style.

ACCEPTANCE: each of R1-R3 goes RED on a root that reproduces its death and
GREEN on one that does not — mutation-proven in BOTH directions. `--case pa1`
under R1 must FAIL with the P-A1 fatal object. Full gate 0 failed.

FINAL MESSAGE: plain words, first sentence is the outcome, one closing analogy.
```

---

## P3 — recover the deleted branch (operator action, not an executor window)

Not a prompt; a message for the operator to send to whoever owns the codex
session:

```
The branch codex/live-full-judge-seat-matrix-20260901 is gone from
ahepi/deepreason — no branch, no PR ref, no commits. If your working tree
still has it:

    git bundle create judge-matrix.bundle \
        codex/live-full-judge-seat-matrix-20260901

and send the bundle. That recovers all 41 commits, the nine live judge-pair
rows, and soak_builder.py. Without it the nine rows are unrecoverable and the
census driver has to be rebuilt from nothing.
```
