# Reproduction

Form: in-memory (part 1, decided) + a guarded live probe held ready (part 2, blocked on the key)

Artifact:
  - `experiments/2026-09-04-fix-provider-reasoning-contract/repro_wire_shape.py`
    — offline, deterministic, exit 0 = part 1 confirmed.
  - `experiments/2026-09-04-fix-provider-reasoning-contract/probe_reasoning.py`
    — the live probe. Written, dry-checked, NOT RUN: it refuses without a
    credential rather than guessing.

## Part 1 — current output (pasted verbatim)

    $ python experiments/2026-09-04-fix-provider-reasoning-contract/repro_wire_shape.py
    committed route     : ollama https://ollama.com/v1 qwen3.5:397b
    configured value    : 'none'
    body the harness sends: {"max_tokens": 8192, "messages": "<elided>", "model": "qwen3.5:397b", "reasoning_effort": "none", "response_format": {"type": "json_object"}}

    keys carrying the reasoning value, per provider, for the value 'none':
      deepseek  {"thinking": {"type": "disabled"}}
      generic   {}
      ollama    {"reasoning_effort": "none"}
      openai    {"reasoning_effort": "minimal"}

    harness sends 'reasoning_effort'          : True
    harness sends bare 'reasoning' (P2's field) : False
    ANY adapter, ANY value, sends 'reasoning'   : False

    PART 1 OF THE PREDICTION: CONFIRMED
    PART 2 (does the provider still accept this body?): NOT DECIDABLE OFFLINE
    RC=0

Confirms diagnosis: yes — the field the recorded refusal names
(`ChatCompletionRequest.reasoning`) is emitted by no provider adapter at
any value in the neutral vocabulary, so the committed launch config's
`reasoning: "none"` reaches the wire as `reasoning_effort`, and P2's
"binds exactly that value" is true of the value and false of the field.

## Part 2 — the live probe, and why it is not run here

`dr-reproduce` forbids reproducing by launching a live provider run, and
this is not one: it is 45 single-turn chat completions at a 2000-token
cap, which the goal explicitly commissions ("probe the live provider ...
rather than reasoning about it") and which `dr-verify-outcome` will
re-run as the outcome proof. It is held rather than run because the
container carries no credential.

What it sends, dry-checked without a key (`build_cases()`, 45 cases,
concurrency capped at 3):

    kind     reasoning value                                 keys on the wire
    harness  None                                            max_tokens+response_format
    harness  none                                            max_tokens+reasoning_effort+response_format
    harness  low                                             max_tokens+reasoning_effort+response_format
    harness  medium                                          max_tokens+reasoning_effort+response_format
    harness  high                                            max_tokens+reasoning_effort+response_format
    harness  max                                             max_tokens+reasoning_effort+response_format
    harness  512                                             max_tokens+reasoning_effort+response_format
    control  bare-reasoning-string (the 2026-09-04 probe's)   reasoning
    control  reasoning-object                                 reasoning
    control  think-false                                      think

The `harness` rows use `OpenAICompatEndpoint.build_body` itself, over
every model in the committed catalog (`qwen3.5:397b`, `glm-5.2`,
`kimi-k2.6`, `deepseek-v4-pro`) plus the two models carrying a committed
profile document but no committed provider profile (`glm-5.3`,
`gpt-oss:120b`). The three `control` rows are hand-built, are labelled as
such in the output and in `PROBE.json`, and exist to reproduce the
recorded refusal and to test the two shapes P2 says the provider wants.

## Blocked

`OLLAMA_API_KEY` is unset and no `experiments/*/env` file exists — the
container is fresh and the credential is gitignored by design
(`.gitignore` lines 47-51). The probe refuses rather than proceeding:

    $ python experiments/2026-09-04-fix-provider-reasoning-contract/probe_reasoning.py
    no credential: set OLLAMA_API_KEY or pass --env-file pointing at a
    gitignored env file containing OLLAMA_API_KEY=...

`git check-ignore experiments/2026-09-04-fix-provider-reasoning-contract/env`
exits 0, so the path the probe reads by default cannot be committed.

Post-fix expectation (part 1, after whatever the live probe decides):
`repro_wire_shape.py` keeps exit 0 under Reading B; under Reading A its
"body the harness sends" line changes to the accepted shape and the
script's assertions move with it, with the mutation-proven regression in
`tests/` carrying the pin either way.
