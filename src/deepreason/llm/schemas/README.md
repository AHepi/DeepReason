# Role output schemas (spec §9)

One JSON Schema per role output. The adapter validates every raw against the
role's schema; invalid output gets bounded repair retries (`RETRY_MAX`), then
the cycle is dropped and logged.

Planned files (P1):

- `conjecturer.json` — Verbalized Sampling contract (§11.6): `VS_K` candidates,
  each with a stated probability/typicality estimate.
- `argumentative_critic.json`
- `defender.json`
- `variator.json` — bounded edits under µ / µ_struct.
- `judge.json` — trial ruling with mandatory `decisive_point`.
- `summarizer.json`
- `synthesizer.json` — proposed relation artifacts.
- `embedder.json` — content → vector (raws logged).
