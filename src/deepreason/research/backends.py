"""Pluggable research backends (spec §12): web-search | local-RAG | ask-user
(doubles as the appellate channel, §10.6).

Evidence enters as an artifact carrying a source-reliability validity_node —
attackable like anything else.
"""


class ResearchBackend:
    def fetch(self, query: str):
        """Return evidence bytes + source metadata. TODO(P4)."""
        raise NotImplementedError
