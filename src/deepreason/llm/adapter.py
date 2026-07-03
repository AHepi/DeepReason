"""Role -> endpoint routing (spec §9).

Config maps role to endpoint (frontier APIs | ollama | llama.cpp |
OpenAI-compatible); mix freely. Schema-invalid output => feed error back,
RETRY_MAX bounded retries, then drop the cycle (logged). Every call is
logged with prompt_ref + raw_ref so replay consumes logged raws (§0).
"""


class LLMAdapter:
    def __init__(self, role_config: dict, blob_store, event_log) -> None:
        self.role_config = role_config
        self.blob_store = blob_store
        self.event_log = event_log

    def call(self, role: str, pack: str, schema: dict) -> dict:
        """One logged, schema-validated, bounded-retry role call. TODO(P1)."""
        raise NotImplementedError
