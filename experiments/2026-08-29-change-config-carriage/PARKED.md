# PARKED.md — config carriage (P15)

Findings this tranche produced and did NOT fix. One tranche, one goal.

---

## P28 — a master gate silently overrides a named setting, and says nothing

**This is the batch's own subject, one layer above where the batch found it.**
Raised by the operator on reading this tranche's delivery, and confirmed by
measurement.

**What.** `Config.ENGAGED_CRITICISM_AUTHORITY` names the mode a prose-only
criticism runs under: `observe_only` records the criticism as evidence but
**cannot change any claim's status**; `defended_trial` sends it to a defended
trial that can. Setting it to `defended_trial` **does nothing on its own**.
`preparation.py:558-566` forces it back:

    authority=(
        config.ENGAGED_CRITICISM_AUTHORITY
        if config.ADJUDICATION_STATUS_AUTHORITY_ENABLED
        else "observe_only"
    )

`ADJUDICATION_STATUS_AUTHORITY_ENABLED` defaults **False**. So a configuration
that names the gate it wants is silently reverted by a second switch, with no
typed notice anywhere. That is the same shape as audit finding P10 and this
whole batch — a configuration silently becoming a different configuration —
and it sits one level above the echo drop P15 just repaired.

It also sits badly with the operator's own 2026-08-28 law: *"configuration of
seats need to be able to turn gates on and off at will … Gates are always
optional: with warnings."* This gate cannot be turned on by the setting that
names it, and it warns nobody.

**Evidence, measured.**

    $ python -c "from deepreason.config import Config; c=Config(); \
        print(c.ENGAGED_CRITICISM_AUTHORITY, c.ADJUDICATION_STATUS_AUTHORITY_ENABLED)"
    observe_only False

A manifest built with `ENGAGED_CRITICISM_AUTHORITY='defended_trial'` and
nothing else compiles `criticism_policy.authority == 'observe_only'`.

The operator has learned to work around it: every committed configuration that
wants a defended trial sets BOTH switches together —
`experiments/2026-08-12-live-grounded-extension-expansion/run-config.yaml:100,102`,
`experiments/2026-08-25-change-constructive-frontier/run-config.yaml:67`,
`experiments/2026-08-27-defect-split-leg-recording/run-config.yaml:85,97`.
A pairing ritual a user must learn is the signature of a silent gate.

**Why it is parked and not fixed here.** Changing the default, or removing the
override, changes what criticism can DO to a claim's status in every future
run. That is a behaviour change needing its own evidence — including the
judge-evidence record the 2026-08-28 judge-law amendment rests on — not a
rider on a carriage tranche. **Operator decision, 2026-08-29: park it as its
own tranche.**

**What this tranche did do in the meantime.** The contradiction carriage would
otherwise have introduced is DISCLOSED rather than left silent: when a
manifest's own carrier field disagrees with the carried value, the notice says
so in words and its `resolution` pointer is dropped, because a pointer that
sends a reader to a field contradicting the value beside it is worse than no
pointer. Pinned by
`test_a_carrier_pointer_that_would_disagree_is_dropped_and_the_note_says_why`.

**Ready-to-send prompt:**

```
Route: deepreason-orchestrator (defect). The record shows a configuration
silently becoming a different configuration -- the P10 shape, one layer up.

Goal, one sentence: make a configuration that sets ENGAGED_CRITICISM_AUTHORITY
either TAKE EFFECT, or say in a typed compile notice that another switch
overrode it and what the run will actually use -- so a named gate can never be
silently reverted.

Evidence, all committed:
  src/deepreason/preparation.py:558-566
      -> the override: authority = X if ADJUDICATION_STATUS_AUTHORITY_ENABLED
         else "observe_only"
  src/deepreason/config.py:484-520
      -> both defaults, and what observe_only vs defended_trial mean
  experiments/2026-08-12-live-grounded-extension-expansion/run-config.yaml:100,102
  experiments/2026-08-25-change-constructive-frontier/run-config.yaml:67
  experiments/2026-08-27-defect-split-leg-recording/run-config.yaml:85,97
      -> every committed config that wants a defended trial sets BOTH, which
         is the workaround a silent gate forces on its user
  experiments/2026-08-29-change-config-carriage/PARKED.md  (this entry)
  experiments/2026-08-29-change-config-carriage/SPEC.md    (the carriage the
      disclosure rides on -- the notice channel already exists, use it)

Read BEFORE designing:
  - CLAUDE.md, the 2026-08-28 seat-configuration law and the 2026-08-28 JUDGE
    LAW AMENDMENT. The amendment matters: in the frozen configuration judges
    UNDER-convict (11.9% sensitivity, 0-2.5% false conviction) while every
    looser configuration measured over-convicts at 47-60%. A tranche that
    makes status-changing criticism easier to switch on must say which of
    those regimes it is putting within reach.
  - experiments/2026-08-09-change-judge-evidence-review/REVIEW.md
  - docs/RESEARCH_JUDGE_BLINDING_2026-08-22.md

The fork to price rather than re-derive, and it is a REAL fork the operator
must decide, not a design detail:
  (a) DISCLOSE ONLY -- keep both defaults, emit a typed notice when the master
      gate overrides a named authority. No run changes behaviour. Smallest,
      and satisfies "with warnings" literally.
  (b) REMOVE THE OVERRIDE -- setting ENGAGED_CRITICISM_AUTHORITY takes effect
      on its own. Satisfies "at will" literally; changes what runs do to
      claim status wherever a config set it and the master gate was off.
  (c) CHANGE THE DEFAULT -- ship with status-changing criticism reachable.
      Largest blast radius; needs the judge evidence argued, not cited.

Do NOT solve it by deleting ADJUDICATION_STATUS_AUTHORITY_ENABLED: a master
reachability gate for status-changing LLM adjudication is worth having. Solve
the SILENCE, and let the operator choose whether the gate also moves.
```

---

## P29 — three of the five headline switches have no run-time reader

**What.** This tranche's acceptance checks measure
`config_from_run_manifest(m).FIELD == configured` — a round trip on the Config
OBJECT. For two of the five switches the batch highlights that is also an
effect on a run (`JUDGE_SEATS_ENABLED` is read at `scheduler.py:1361,2562,2682`
and `authority.py:121`; `ADJUDICATION_STATUS_AUTHORITY_ENABLED` at
`authority.py:80`, `rules/crit.py:61`, `rules/experiment.py:329`,
`imports.py:836`). For the other three — `ENGAGED_CRITICISM_AUTHORITY`,
`LEGACY_CRITICISM_ENABLED`, `SCHOOL_SEATS_ENABLED` — the only readers are in
`preparation.py`, at COMPILE time.

So "the switch is carried" is proven; "the switch is effective at run time" is
proven for two of five and is, for the other three, a statement about the
object rather than about the run. Recorded because `DELIVERY.md` states the
headline as 24 of 25 fields reaching a manifest-launched run, and that is true
of the reconstructed configuration.

**Why parked.** Nothing is broken: a compile-time-only field is consumed
correctly at compile time. Whether those three SHOULD have run-time effect is
a design question about criticism routing, not a carriage defect.

---

## P30 — the end-to-end guard for the serializer lives outside `pytest`

**What.** Deleting the two lines that omit an absent `value` from the dump
reddens exactly ONE pytest test, and that test asserts on a bare model dump
rather than on a digest. The instrument that catches it end-to-end is a map
`check:` (`INV-frozen-surfaces.md`, this tranche's granted-contact entry),
which only `tools/docs_verify.py` runs — and `docs_verify` is not green
(9 baseline failures plus the expected P16 tripwire), so a future regression
here would land in noise.

**Ready-to-send prompt:** add a pytest test that pins the qualification
subject digest of a manifest carrying BOTH a carriage notice and an unrelated
notice against the digest of the same manifest carrying only the unrelated
one. That is the assertion the serializer exists to protect, and it belongs in
the gate every tranche runs, not only in the map.
