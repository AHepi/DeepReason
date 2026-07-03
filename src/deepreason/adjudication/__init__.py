"""Adjudication — two-pass labeling (spec §4).

Inputs are ``att`` and ``dep`` ONLY. Measures, school membership,
novelty/diversity signals, and Pareto rank MUST NOT enter label computation
(§0): they act upstream via Spawn, budgeted commitments, or attention.
"""
