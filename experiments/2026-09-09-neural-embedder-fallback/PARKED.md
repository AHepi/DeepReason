# Parked — found while diagnosing the silent hashing fallback, not worked here

## P1 — the other six host-owned configuration values are silent in the same way

**What.** `preparation._config_for_profile`'s `owned` dictionary takes SEVEN
values whatever the operator's configuration says, and
`preparation.py:505-508` exempts all seven from the compiler's
`ENGINE_CONFIG_FIELD_NOT_CARRIED` disclosure channel. This tranche fixes the
embedder one, because that is the one the record shows silently changing a
measurement scale. Whether `engine_profile`, `model_profile`, `scratchpad`,
`bridge`, `CHANNELS_DISABLED` or `roles` also drops an operator value without
saying so is a separate question with its own evidence, and answering it here
would widen a defect tranche into a survey.

```
Route: dr-audit-orchestrator (the operator asks what is silently out of date),
dimension goal-trace — the 2026-08-28 ungated-seats law says every gate is
switchable per run and switching one produces a typed WARNING, never silence,
and audit finding P10 (five switches silently reverted by the manifest echo
with zero notices) is the recorded precedent.
Goal: for each of the six remaining host-owned values in
`preparation._config_for_profile`'s `owned` dict, table whether a manifest
compiled from an operator configuration that sets it differently records ANY
typed notice, and whether the silence is load-bearing (the host owns the
credential and the endpoint) or an oversight.
Evidence: src/deepreason/preparation.py:376-394 and :505-508;
docs/map/CON-configuration-stages.md stages 2 and 3;
docs/map/CON-seats.md:116, which already names the seven;
tests/test_managed_path_config_read.py and
tests/test_manifest_config_disclosure.py, which pin the disclosure behaviour
for the fields that ARE disclosed.
End state: AUDIT_REPORT.md rows, one per value, each either "silence is the
security boundary, and here is the test that pins it" or a ready-to-send fix
prompt. No code changes.
```

## P2 — the five sealed arm roots measured on the hashing scale and cannot be re-derived

**What.** The five arms of
`experiments/2026-09-04-experiment-brief-variation-step1/` are sealed committed
roots. Their M2 (mean pairwise embedding distance) and novelty readings are on
the hashing scale. Nothing in this tranche changes them, and nothing may: a
committed root's contents are never edited. The fix here makes FUTURE runs say
which scale they used; it does not retro-fit these five.

```
Route: none needed unless the operator wants the step-1 numbers on the neural
scale, in which case it is a new live tranche, not a repair of these roots.
Goal: if wanted — re-run the step-1 arms on a configuration that carries the
neural embedder and compare M2 against the sealed hashing readings.
Evidence: experiments/2026-09-04-experiment-brief-variation-step1/RESULTS.md
§5 item 4 (the fallback was held CONSTANT across arms deliberately, so the
between-arm comparison is unaffected); RUNLOG.md:24-32.
End state: either a decision that the sealed readings stand as they are, or a
new tranche with its own pre-registration. Note the noise floor finding
(d_noise = 1.312 of 15) first: a scale change may not be the binding limit.
```
