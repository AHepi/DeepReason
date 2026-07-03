"""Judge audits (spec §10.4) — program-checked attacks on rubric
infrastructure, every AUDIT_PERIOD cycles, budgeted.

- Paraphrase invariance: flips are hits.
- Premise-deletion sensitivity: a verdict surviving removal of its own
  decisive_point is easy to vary.
- Planted-flaw calibration: constructed flaw set + clean controls; error
  rate > JUDGE_ERR_MAX => audit-the-critic Spawn.
- Bias probes: planted self-preference and verbosity pairs.
- Ensemble disagreement: cross-family judges disagreeing is a critic-gaming
  signal, never averaged away.

Outputs enter as ordinary demonstrative warrants (eval:program) against the
relevant nu nodes or standards.
"""


def audit_sweep(state, adapter, config):
    """Run one audit sweep; register warrants. TODO(P5)."""
    raise NotImplementedError
