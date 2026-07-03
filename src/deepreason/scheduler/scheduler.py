"""Rule-registry scheduler (spec §14).

Frontier of problems + global budgets. Short horizon: one problem, N cycles,
return the Pareto frontier of G-members. Long horizon: persistent frontier
across sessions. Integration capped by INTEGRATION_BUDGET_SHARE; audits by
AUDIT_PERIOD; user queue by USER_RULINGS_BUDGET; Reveal events per holdout
policy.
"""


class Scheduler:
    def __init__(self, state, log, adapter, config) -> None:
        self.state = state
        self.log = log
        self.adapter = adapter
        self.config = config

    def step(self) -> None:
        """Apply one enabled rule under budget. TODO(P2)."""
        raise NotImplementedError

    def run(self, budget) -> None:
        """Run until budget exhaustion. TODO(P2)."""
        raise NotImplementedError
