"""Rubric-verdict trial guard (spec §3) — mandatory before Crit commit of
any rubric-derived warrant.

Two enforcement layers:
1. The trial protocol itself lives in deepreason.informal.trial (run_trial):
   critic case -> defender answer -> judge ruling with decisive_point ->
   referential integrity -> order-swap -> paraphrase spot-check -> ensemble
   agreement. Only surviving rulings package warrants.
2. Well-formedness (§2), enforced at registration by the harness: a
   rubric-derived demonstrative warrant whose trace_ref does not contain a
   conforming trial transcript is rejected — so the guard cannot be
   bypassed by constructing warrants directly.
"""

from deepreason.informal.trial import conforming_transcript, run_trial

__all__ = ["conforming_transcript", "run_trial"]
