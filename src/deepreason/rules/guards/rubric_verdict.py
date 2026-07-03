"""Rubric-verdict trial guard (spec §3) — mandatory before Crit commit of any
rubric-derived warrant.

1. Trial transcript: critic drafts the case for fail citing specific
   clauses/cases; defender answers; judge rules with a ``decisive_point``.
2. Referential integrity (program check): decisive_point must resolve to an
   actual element of the transcript.
3. Order-swap consistency (pairwise/anchored modes): both presentation
   orders must agree, else no warrant.
4. Paraphrase spot-check: TRIAL_PARAPHRASE_N variator paraphrases; any flip
   => no warrant.

Only surviving rulings become warrants; trace_ref = full transcript + all
check results. Blocked rulings are logged, never registered; a streak of
blocks is a critic-gaming signal (Spawn audit-the-critic).
"""


def run_trial(target_id: str, commitment_id: str, state, adapter):
    """Orchestrate the trial; return a warrant or a logged block. TODO(P5)."""
    raise NotImplementedError
