# gpt-oss:20b — testing the prose-into-schema rule on a small model

Same profile values as the glm-5.2 thinking-off profile (context 131072,
completion 24576, reasoning none); the model is the only variable.

## Finding 1 — "none" does not mean off on this model

    reasoning_effort: none   reasoning 528 chars, 150 completion tokens
    reasoning_effort: high   reasoning 986 chars, 255 completion tokens

On glm-5.2 the same "none" yields exactly 0 reasoning characters. So the
neutral off token is honoured differently per model: full off for
glm-5.2, partial for gpt-oss:20b. The binding rule (R4) still fires and
still sets the knob, but "switched off" is not a guarantee the provider
makes uniformly. Recorded rather than assumed.

## Finding 2 — the battery did not fail cleanly, it died opaquely

    qualify_rc=0  qualify_seconds=643  tier: shallow
    QUALIFICATION_EXECUTION_FAILED: injected qualification execution did
      not complete successfully        (at case 144/340)

No doctor report was written, so there are NO per-pair numbers. Compare
glm-5.2, which failed informatively:
`DOCTOR_REPORT_PAIR_UNQUALIFIED at /pairs/14/qualified` plus a full
per-case report naming `scratch.link.compact.v1` at 11/20.

The cause is discarded by the code: `qualification.py:823-829` wraps the
executor in `except Exception: raise QualificationError(...) from None`,
so the real exception — and any traceback — is thrown away. A ~1200-call
battery can fail and leave nothing to diagnose.

Parked as **D5**: qualification execution failure discards its cause.
The fix is narrow (chain the exception, or record its type and message in
the tier record) and it is not this tranche's goal.

## Diagnostic re-run

`diagnose.py` calls `default_qualification_executor` directly with the
traceback intact, concurrency 4 rather than 12 in case the first failure
was rate-limiting. Its result is the evidence for the 20B half of the
rule test; until it lands there are no 20B per-pair numbers and none are
claimed.
