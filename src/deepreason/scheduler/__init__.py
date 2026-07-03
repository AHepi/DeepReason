"""Scheduler (spec §14): thin custom scheduler over a rule registry.

Control flow is "apply enabled rules under budget" — NOT a fixed node graph
(do not use LangGraph as the spine). School allocation per §11.2; focus per
Pareto retention (§11.7); capture-response rules per §11.4 with hysteresis.
"""
