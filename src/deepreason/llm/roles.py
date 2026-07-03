"""Role definitions (spec §9): prompt template + JSON schema + temperature +
endpoint, per role.

conjecturer returns a VS_K-candidate distribution with typicality estimates
(schema-enforced, §11.6) — never a single point.
"""

ROLES = (
    "conjecturer",
    "argumentative_critic",
    "defender",
    "variator",
    "judge",
    "summarizer",
    "synthesizer",
    "embedder",
)

# TODO(P1): prompt templates + per-role JSON schemas (see llm/schemas/).
