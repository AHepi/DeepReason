# DIAGNOSIS — three defects, one family: the soak reported green over a population it never examined

Tranche: `experiments/2026-09-04-defect-rotted-soak-cases/`
Base: `f7ea93d3b` (main + the read-only review tranche).
Map preflight: `DR-SUB-scripts`, `DR-CON-run-identity`, `DR-INV-frozen-surfaces`.

The operator's instruction was to repair the five rotted soak cases, and
first to "establish whether the soak runs everything. Not just the first two
lines. That was a major fault with verify." The investigation found the
answer is **no**, and found two further defects beneath the one reported.

## The precedent that names the family

`docs/AUDIT_BASELINES.md`, the superseded `docs_verify` entry, states it
exactly:

> It undercounted BY CONSTRUCTION. The parser required a check's opening and
> closing backtick on one line, and the parse loop had no `else`: a column-0
> `check:` opener it could not read was discarded with no output at all. 72
> such openers stood across 27 map documents. So the old "0 failed on a full
> clone" was a statement about 1141 checks presented as a statement about the
> map.

An instrument that discards what it cannot handle reports a green total over
a population it never examined. All three defects below are that shape.

---

## D-A — the primary defect: five of nine cases cannot compile

**Symptom.** `pr1`, `pc1`, `pc2`, `pc2b`, `split-legs` all die before any
assertion runs:

    pydantic_core.ValidationError: 1 validation error for RunManifest
      Value error, V6_SIMULATION_TOOLCHAIN_REQUIRED: policy must bind one
      frozen toolchain

**Cause, measured not inferred.** `run_manifest.py:3621-3628` requires exactly
one manifest toolchain whose `id` equals `policy.python_toolchain_identity`.
The default simulation runner is the CONTAINED one
(`v6_policy.py:369-370`, "Return the named runner profile, defaulting to the
contained one"), so the policy asks for `python@deepreason-public-contained.v1`.
The four healthy builders call `engaged_simulation_toolchain()`, which follows
the runner choice. The five broken cases sit on four builders that call
`engaged_local_simulation_toolchain()`, which returns
`python@deepreason-public-local.v1` whatever the policy wants.

Measured directly (`proof/root_cause.txt`):

    policy.python_toolchain_identity: python@deepreason-public-contained.v1
    what the 5 BROKEN builders pin  : python@deepreason-public-local.v1
    what the 4 WORKING builders pin : python@deepreason-public-contained.v1
    MATCH (broken)  : False
    MATCH (working) : True

The builders pinned ONE RUNNER instead of asking the policy which runner this
configuration names. They kept returning `local` after the default moved.

**Why nothing caught it.** `docs/AUDIT_BASELINES.md:210` baselines exactly one
invocation — `--case epoch3` — and `epoch3` is one of the four survivors. No
gate runs the soak at all (also documented). So five cases could rot without
moving a single recorded number.

---

## D-B — two of seven assertions had not run on any case

**Symptom.** `assess_run` declares A5 (`in-run-checker-fired`) and A6
(`discharge-channel-carried-them`), but emits them only when
`case.id in IN_RUN_EVALUATION_CASES`. That set is:

    IN_RUN_EVALUATION_CASES = frozenset({"pc2", "pc2b"})   # cycle_soak.py:405

Both members are in D-A's broken five. So A5 and A6 were emitted by **no
runnable case**, and were not reported as skipped — they simply were not in
the output. Measured across all four cases that ran (`proof/A5A6_never_run.txt`):

    epoch3      assertions emitted: A1 A2 A3 A4
    reach-rich  assertions emitted: A1 A2 A3 A4
    hv-grant    assertions emitted: A1 A2 A3 A4
    pa1         assertions emitted: A1 A2 A3 A4

**Why it matters more than the count suggests.** A5/A6 are the assertions that
catch a battery which is "present, configured and INERT" — the failure
`_channel_facts`'s own docstring says P-C1 "paid a whole run for". The soak's
only guard against silent inertness was itself silently inert.

**A compounding property.** `partial` and `not-coverable` seams do not affect
the exit code (`_verdict` counts only `failed`), and `D1-seat-contract` is
`partial` by default on every run. So exit 0 was never a coverage statement,
and with A5/A6 absent it was a statement about four assertions presented as
the whole instrument.

---

## D-C — builders silently inherit another experiment's question

Found while writing the regression that compiles all nine cases in one
process: `pc2` and `pc2b` failed with

    SystemExit: QUESTION BYTES DRIFTED from the value PREREG.md §2 froze:
      933313a5d9ca6dd8… != 64b724c4118320989…

**Cause.** Builders import BARE sibling names — `from question import QUESTION`,
`from criteria import CRITERIA`. Three experiment directories define a
`question.py`, and their bytes differ (`proof/root_cause.txt`):

    64b724c411832098   2026-08-25-change-constructive-frontier   (what pc2b needs)
    933313a5d9ca6dd8   2026-09-01-live-all-modules-p-a1          (what pc2b got)
    933313a5d9ca6dd8   2026-09-02-live-p-a2-corrected

`_case_module` did `sys.path.insert(0, builder_dir)` — never removed — and
`__import__(case.builder)`, which returns whatever `sys.modules` already holds.
So the first case built in a process wins, and every later case compiles
against another experiment's question.

**The sharp edge.** `pc2`/`pc2b` carry a frozen question digest and fail
LOUDLY. The other seven cases carry no such guard, so they would have compiled
a manifest for a shape nobody asked for, in silence, and the soak would have
driven it and reported on it. In single-case CLI use — the only way the soak
has ever been run — this is inert. It becomes live the moment anything
enumerates the case inventory, which is precisely what D-A's absence of a
gate check requires.

---

## Frozen-surface check, done BEFORE any code was written

`docs/map/INV-frozen-surfaces.md` surface 5 is "Anything altering
qualification subject digests — `qualification.py`", and its check is
`grep -q "def qualification_subject_payload" src/deepreason/qualification.py`.
The subject payload does include the whole manifest dump, so a manifest's
toolchain entry does enter its digest.

**This tranche does not contact that surface**, for two reasons stated so a
later reader can falsify them rather than trust them:

1. The surface protects the DERIVATION — what enters the digest — in
   `qualification.py`. Nothing here changes that function or its inputs' shape.
   A config change that moves one experiment's manifest digest is ordinary;
   were it not, the all-configurations law could not hold.
2. The five repaired cases compiled to **nothing** before this change. There is
   no prior digest to move and no cached qualification verdict to invalidate,
   because no manifest existed to key one.

Verified rather than asserted: the full gate is the instrument that would go
red in ~40 places if a committed subject digest moved (surface 5's own Traps
entry records exactly that signature). See VERIFY.md.

No other frozen surface is touched: no record format, no event application, no
manifest schema or validator, no `route_fingerprint`.
