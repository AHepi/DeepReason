"""prose(id) view (spec §8, §10.1).

For skeleton-codec artifacts, render the readable narrative from the skeleton
via the summarizer role — cached and logged. Never adjudicated.
"""


def prose(artifact_id: str, state, adapter) -> str:
    """Render prose from a skeleton. TODO(P5)."""
    raise NotImplementedError
