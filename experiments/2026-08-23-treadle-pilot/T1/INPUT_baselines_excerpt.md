# Excerpt of docs/AUDIT_BASELINES.md — the docs_verify baseline row
# (verbatim copy, staged into the task cone by the monitor so the
#  driver's model can read it; the authoritative file is docs/AUDIT_BASELINES.md)

- **docs_verify** (`python tools/docs_verify.py`): 3 pre-existing
  failures, all `CON-run-identity.md` git-history checks — they
  require an unshallowed clone; on a full clone the expected value
  is 0 failed.
- **treadle doctor** (`tools/treadle/.venv/bin/treadle --repo . doctor`,
  with `OLLAMA_API_KEY` exported): expected **exit 0 and every line OK**
  — no `MISS`, no `WARN`. Recorded 2026-08-23 at install: 5 environment
  lines, 2 stage lines (`pilot`, `review`), credentials, and 3 model-tag
  lines (`gpt-oss:120b`, `deepseek-v4-pro:0813` twice). A `WARN
  credentials` line is baseline ONLY when the key is unset — with the key
  exported it is a finding. A `WARN model tag ... NOT on endpoint` is
  always a finding: hosted checkpoints are retired without notice, and
  that line is how this repo learns. `NOTE model-tag check skipped` means
  the endpoint was unreachable, which is a network fact, not a verdict —
  re-run before rowing it. If `tools/treadle/.venv` is absent the
  container has rolled back; rebuild it per `tools/treadle/VENDORED.md`
  before treating anything here as a delta.
