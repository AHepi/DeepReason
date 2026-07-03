"""Standards as case law (spec §10.3).

Every rubric:<spec-id> resolves to a registered standard artifact: rubric
text, evaluation mode (absolute | anchored | pairwise), and mention refs to
exemplars with one-line holdings. Standards are ordinary artifacts —
attackable, reinstateable, succeedable. The closure extension (§1) is the
teeth: refute a standard and every verdict under it falls, every target
reinstates, computed in pass 1.
"""


def resolve_standard(spec_id: str, state):
    """Resolve a rubric spec-id to its standard artifact. TODO(P5)."""
    raise NotImplementedError
