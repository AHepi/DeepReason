# Reproduction

Form: unit-test (offline), with record-replay corroboration

Artifact: `tests/test_adjudication_blindness.py`
  - `::test_a_root_with_no_attacks_reproduces_the_live_shape` — fidelity guard,
    PASSES today.
  - `::test_the_ritual_flag_cannot_fire_when_nothing_was_ever_attacked` —
    FAILS today (sub-cause).
  - `::test_detection_flags_reach_the_epistemic_channel` — FAILS today
    (primary cause, load-bearing).

The live root is gitignored, so the durable artifact is built from
`_engaged_root` (`tests/test_v6_engaged_repair_verification.py`), a real v6
text root. The fidelity guard pins that it reproduces the live shape —
artifacts present, `len(state.att) == 0`, `len(state.carries) == 0`,
`len(warrants) == 0` — so the two failing assertions cannot be blamed on a
fixture that drifted into some other state.

Current output:

    $ python -m pytest tests/test_adjudication_blindness.py -q
    2 failed, 1 passed

Probe output behind those assertions, on the same fixture:

    artifacts: 6   att: 0   carries: 0   warrants: 0

    adjudicator metrics:
      n_attacks 0   refutations 0   attack_target_entropy None
      criticism_debt 0.0   validity_attack_rate None
      reinstatement_rate None   g_churn 0

    raw_flags -> {'lineage_stagnation': True, 'school_convergence': False,
                  'adjudication_ritual': False, 'grounding_decay': False,
                  'attractor_orbiting': False}

    epistemic findings (unforced)                        : 0   valid True
    epistemic findings (adjudication_ritual forced True) : 0   valid True
    epistemic findings (ALL FIVE flags forced True)      : 0   valid True

Confirms diagnosis: yes, both halves.

  - Sub-cause: `adjudication_ritual` is `False` at `n_attacks == 0`.
    `attack_target_entropy` and `validity_attack_rate` are both `None` and
    `refutations` is 0, so of the four conditions only `criticism_debt > 0.5`
    could fire — and it is 0.0 — while the flag needs two.
  - **Primary cause, and the load-bearing result: forcing ALL FIVE flags to
    `True` still yields zero epistemic findings and `valid: True`.** No
    threshold change can produce a finding, because verification never reads
    what the detector returns. This is the observation that makes the
    threshold a sub-cause rather than the cause.

One further fact the probe surfaced, unprompted: `lineage_stagnation` is
already `True` on this root today, under real (unforced) conditions, and
reaches nothing. A flag that is firing right now is being discarded — the
channel is not merely unreachable in the zero-attack corner, it is unreachable
at all.

Post-fix expectation:

    $ python -m pytest tests/test_adjudication_blindness.py -q
    3 passed

with the fidelity guard still passing (the fixture still has zero attacks), and
— per GOAL.md criterion (c) — no previously-valid root flipping to invalid in
the before/after sweep.

Method note, recorded because it nearly produced two false claims in this
tranche alone: the first probe read `flags["ritual"]` and got `None` because the
key is `adjudication_ritual`; an earlier probe read `state.attacks`, which does
not exist, and reported zero attacks for all 31 openable roots. Both are the
same failure — a missing key or attribute returning a falsy default that is
indistinguishable from a real measurement. Any probe of this codebase should
assert the key exists before trusting its value.

Production code untouched: `git diff --stat -- src/` is empty at this phase.
