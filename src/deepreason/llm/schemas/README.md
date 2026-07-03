# Role output schemas (spec §9)

Contracts live as Pydantic models in `../contracts.py`; the JSON Schema shown
to the model is derived via `model_json_schema()`. The adapter validates every
raw against the contract; invalid output gets bounded repair retries
(`RETRY_MAX`), then the cycle is dropped and logged.

Implemented (P1): `ConjecturerOutput` (Verbalized Sampling, §11.6),
`ArgumentativeCriticOutput`.

Planned: variator (bounded edits under µ / µ_struct, P2), judge (trial ruling
with mandatory `decisive_point`, P5), defender (P5), summarizer,
synthesizer (P2), embedder (P2).
