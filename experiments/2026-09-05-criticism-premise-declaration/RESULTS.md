# A criticism can declare what it rests on — results

Honest-ledger segments, dated. What the record shows, and the residue.

## 2026-09-05 — the defect, reproduced and isolated

The OIS 1.1 §0 finding reproduces at `323fefb53` on the editable install,
byte for byte with the monitor's report:

    DEPENDENCE ('refuted', 'suspended_unsupported')
    EVIDENCE   ('accepted', 'refuted')

A criticism whose essential premise had been refuted went on defeating its
target. The cause was NOT in `adjudication/`. Both closures behave as
`docs/map/CON-warrants-and-attacks.md` documents; what was missing was a
producer. The one argumentative mint site fed by a critic's prose case
(`informal/trial.py::_argument_trial_steps`) created its validity node with no
interface, and `ArgumentativeCriticOutput` had no field in which a criticism
could name its own premises — so the documented branch was unreachable from
the wire and no live run could ever have taken it.

The isolation is a three-arm script (`repro_nu_evidence.py`) over one
four-artifact graph. Arm C changes exactly one thing against the failing arm A
— the validity node declares the premise as `EVIDENCE` — and the target
reinstates. That is the evidence for "the mint site is the fix site", and it
is why no adjudication edit was proposed or made.

Census, for the next reader: six hand-built `Warrant(...)` constructions and
eighteen `register_fail_warrant` call sites in the tree. Five of the six are
ARGUMENTATIVE. Exactly one of those five (`rules/vision.py`) already declared
its ground on ν as `EVIDENCE`; the road existed and one caller used it.

## 2026-09-05 — the fix

A criticism now declares the artifacts it essentially relies on
(`premises_essential`, optional, on BOTH criticism outputs), the alias-bearing
wire field carries it under the schema enum that makes an unknown handle a
failed call, and the defended trial mounts each declared premise on its
validity node as `RefRole.EVIDENCE`. Refuting a declared premise then lifts
the attack onto ν and reinstates the target in the same fixpoint pass.

`s0_wire.py` shows the same result through the wire rather than by hand:

    critic DECLARED the premise essential    ('accepted', 'refuted')
    critic declared nothing (today's path)   ('refuted', 'accepted')

Three deliberate limits, each one a decision rather than an omission:

- **Optional, and an empty declaration costs nothing.** The source document's
  "an empty discriminator is a failed call" rule was NOT adopted and its
  analogue here was not invented. A criticism that declares nothing builds ν
  with no interface, exactly as before — asserted, not promised
  (`test_a_criticism_that_declares_nothing_keeps_todays_behaviour`).
- **Never on a demonstrative verdict's ν.** Those verdicts rest on an
  execution. Mounting a prose premise there would let a prose attack disable a
  refutation that actually ran.
- **No reference menu.** The field is reference-bearing and
  `INV-reference-menu.md` says such a field should be shown its legal set. It
  is not, because a menu renders into the pack and the goldens had to pass
  untouched. PARKED P3 carries it as its own tranche, and until it lands the
  seat learns the legal set from the schema enum rather than from a menu.

## Residue — what remains unproven

- **No live evidence.** Everything here is offline: mock endpoints, a stub
  root, and the public `Harness` API. No live run has yet produced a criticism
  that filled the field, so how OFTEN a real critic declares a premise — and
  whether what it declares is any good — is unmeasured. The offline regression
  proves the road works when taken, not that it is taken.
- **The success law is untouched by this tranche.** Progress over a no-harness
  baseline (operator law, 2026-09-03) is not what this measures. What is
  measured is that a documented rule now has a producer; whether criticisms
  that can be undermined make the harness's output materially better than a
  single model call is a separate question and a separate experiment.
- **The direct transport is protected by a decline, not by a menu.** A profile
  using direct contracts carries raw ids with no alias table; an id naming
  nothing declines typed (`unknown-premise`) and mints nothing. That is
  "creates nothing, never a silent drop", but it costs the whole criticism
  rather than repairing the one field, which is a worse outcome for the run
  than the compact path's repair ladder. Recorded here because it is the shape
  a future reader will want to improve.
