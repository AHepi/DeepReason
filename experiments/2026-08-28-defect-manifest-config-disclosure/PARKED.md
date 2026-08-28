# PARKED — found while fixing P10, deliberately not fixed here

One tranche, one goal. Everything below is a ready-to-send prompt for a future
runner. Numbering continues the run-problems audit's own `PARKED.md`, which ends
at P13. ERRATA and PARKED numbering may collide at merge with the parallel
render-layout and criticism windows; mint from the tail and note it.

---

## P14 — `deepreason reason` never reads the operator's run config at all

**What.** The managed path does not merely drop the operator's `Config`
switches; it never loads their config file. `RunPreparationService().prepare`
→ `preparation.build_preparation_manifest` →
`preparation._config_for_profile` (`preparation.py:308-352`) CONSTRUCTS a
fresh `Config` from the provider profile, with every field at its default
except `engine_profile`, `model_profile`, `scratchpad`, `bridge`,
`EMBEDDER_MODEL`, `CHANNELS_DISABLED` and `roles`. The global `--config` file
reaches `compile_run_manifest` only through `deepreason config compile` and
through hand-written builders. So on the supported product path, a
`run-config.yaml` naming `JUDGE_SEATS_ENABLED: true` has no effect of any kind
— not dropped, not disclosed, not read.

This is a strictly larger statement of the seat-config-ungated law's second
limb than P10 fixed: P10 makes the loss visible; this is the loss of the
ability to configure at all on the managed path.

**Ready-to-send prompt:**

```
Route: deepreason-orchestrator (defect). Sequence AFTER the P10 disclosure
tranche (experiments/2026-08-28-defect-manifest-config-disclosure/), whose
notices are the instrument that will tell you whether a fix here worked.

Goal, one sentence: make `deepreason reason` compile its manifest from the
operator's own Config -- the file `--config` names -- rather than from a Config
synthesised out of the provider profile, so that a seat/gate setting written in
run-config.yaml reaches the run or is disclosed as not reaching it.

Evidence, all committed:
  experiments/2026-08-28-defect-manifest-config-disclosure/REPRO.md
      -> the finding, with the call chain
  src/deepreason/preparation.py:308-352  _config_for_profile
      -> Config(engine_profile=..., model_profile=..., scratchpad=...,
         bridge=..., EMBEDDER_MODEL=None, CHANNELS_DISABLED=..., roles=...)
         and nothing else; every other field takes its default
  src/deepreason/preparation.py:499-511
      -> the criticism_policy wiring, which therefore reads the SYNTHESISED
         config's LEGACY_CRITICISM_ENABLED (True) and compiles no policy
  src/deepreason/cli/main.py:2395  _cmd_reason -> RunPreparationService().prepare

Price the qualification cost FIRST and report it before designing: the
qualification subject is built from the manifest, so admitting operator Config
values into preparation moves the subject digest for every non-default config.
That is a real cost per home (~14 minutes, ~1160 calls) and it may be the
correct one -- a genuinely different behaviour contract SHOULD requalify -- but
it is the operator's call, not the runner's.

End state: a stated verdict on whether the managed path reads the operator's
Config, a disclosure or a carriage for every switch it does not, the
qualification price measured and reported before any re-pin, full gate 0
failed, map moved in the same commit.
```

---

## P15 — the disclosure warns; nothing yet CARRIES the 22 behavioural switches

**What.** `experiments/2026-08-28-defect-manifest-config-disclosure/` fixes the
SILENCE, which is the first limb of the 2026-08-28 operator law ("Gates are
always optional: with warnings"). It does not fix the second limb: 22
behavioural `Config` fields still cannot be carried into a manifest-launched
run by any route, so a configuration still cannot turn those gates on. The
disclosure names them; it does not deliver them.

Carriage was parked rather than attempted because it changes what seven
committed configurations would DO, and because it prices qualification subject
digests for every non-default config. Both are the operator's call.

**Ready-to-send prompt:**

```
Route: dr-change-orchestrator (a design change: nothing is broken, a capability
is absent). Sequence AFTER P14, which decides whether the operator's Config
reaches the compile at all -- carriage is pointless until it does.

Goal, one sentence: let a configuration actually turn on the 22 behavioural
gates the manifest's engine-config echo does not carry, without paying a
qualification battery for a configuration that turned none of them on.

Evidence, all committed:
  experiments/2026-08-28-defect-manifest-config-disclosure/DIAGNOSIS.md
      -> the 25 dropped fields, classified 22 BEHAVIOURAL / 3 IDENTITY-ONLY,
         with each field's run-time consumption site
  .../MEASUREMENTS.md
      -> what each carriage design costs in subject digests, measured
  .../probe/census_dropped_fields.py
      -> re-runnable: which committed configs lose which fields

The one road that was designed and not taken, offered so it can be priced
rather than re-derived: the disclosure notice already names the field
(`pointer`) and its configured value (`message`), and rides a manifest field
that survives serialisation. `config_from_run_manifest` could restore the value
from it, making the notice a CARRIER as well as a disclosure -- with zero
effect on any manifest that has no such notice, which is all 79 committed ones.
Its price is that the qualification subject would then vary with the carried
knob, which the P10 tranche deliberately avoided (see that tranche's surface-5
request). Judge it against the alternative of a second typed policy field.

Do NOT design this before reading the drop list's own comments and the three
committed exclusion tests (Parts C/D/E, S2a/S2b/S2d, C9 in
tests/test_reusable_qualification.py): they state, correctly, that a
dispatch-gating knob must not cost a home a battery. A carriage design has to
answer them, not route around them.

End state: a verdict on whether carriage is wanted, and if so a design whose
qualification price is measured and reported before implementation.
```

---

## P16 — the new frozen-surface tripwire cannot express a GRANTED contact, so it is red on every branch that has one

**What.** `docs/map/INV-frozen-surfaces.md:297`, added by `925b17f62` (merged to
main in `90b1347f4`), carries:

```
check: ! git diff --name-only origin/main...HEAD | grep -qE "capabilities/state\.py|/harness\.py|/invariants\.py|/run_manifest\.py|/qualification\.py|llm/firewall\.py"
```

It is GREEN on `main` for the trivial reason that `origin/main...HEAD` is empty
there, and RED on any working branch that touches a frozen-surface file — a
granted contact and an ungranted one alike, because the check cannot tell them
apart. This tranche turned it red with two contacts the monitor granted on the
record (`run_manifest.py`, surface 4, forecast and granted; `qualification.py`,
surface 5, requested in FIX.md and granted on the measurements). Not worked
around and not edited: a tripwire another tranche just landed is not something
to file down because it caught you.

Six of the seven granted contacts already recorded in that document would each
have turned it red on their own branch. The document is BUILT on the premise
that contact is permitted when it is forecast, named before implementation, and
recorded with re-runnable checks; a check that forbids contact outright
contradicts the section it sits in.

**Ready-to-send prompt:**

```
Route: deepreason-orchestrator (defect). Small and self-contained.

Goal, one sentence: make the frozen-surface branch tripwire at
docs/map/INV-frozen-surfaces.md:297 distinguish a GRANTED contact from an
ungranted one, so it stays a real tripwire on main and stops being red by
construction on every branch that legitimately touches a frozen surface.

Evidence:
  docs/map/INV-frozen-surfaces.md:297      -> the check
  git log -1 925b17f62                     -> the commit that added it
  experiments/2026-08-28-defect-manifest-config-disclosure/probe/docs_verify_merged.out
      -> it firing on two contacts the monitor granted on the record
  docs/map/INV-frozen-surfaces.md          -> the seven granted contacts already
      recorded; six of them would have turned this check red on their own branch

The shape that would work, offered so it is priced rather than re-derived: the
check has to consult the same thing a human reviewer does -- whether the
touched file appears in a "Granted contact" section of THIS document, added in
the same branch. A check keyed on the branch diff alone cannot know that, which
is why it currently answers a question nobody asked ("did anything change?")
instead of the one the section asks ("was it forecast, named and recorded?").

Do NOT solve it by deleting the check: a tripwire over these six paths is worth
having. Solve it by making it able to pass for the case the document's own
discipline permits. Also check tools/docs_verify.py --audit still accepts the
replacement (a check that cannot fail is worse than no check).

End state: green on main, green on a branch whose contact is recorded, RED on a
branch that touches a frozen path with no recorded grant -- the last of those
demonstrated by a mutation, not asserted. Full gate 0 failed; map moved in the
same commit.
```
