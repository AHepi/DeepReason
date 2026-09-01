# R4 live-canary preregistration

Status: frozen before any live provider use. R4 remains optional and disabled
unless the operator supplies an API key after this file is committed and pushed.

## Registered outcome

The live canary will report exactly one of these outcomes:

1. provider results are recorded, in order, for the argumentative critic,
   defender, judge seat 0, and judge seat 1; or
2. the first typed refusal encountered on that path is recorded verbatim, and
   execution stops without attempting to repair or bypass it.

## Frozen limits

- Compile a fresh v6 manifest with an explicit defended-trial criticism policy.
- Use a fresh `DEEPREASON_HOME`; never reuse or alter a committed run root.
- Preseed one accepted target that is not formally backed and submit one valid
  ungrounded attack.
- Drive one scheduler cycle only.
- Budget approximately ten provider calls; one repeat is pre-authorized.
- Do not change code, policy, routing, guards, or fixtures in response to a
  refusal.

No credential is present in this record, and no live run is authorized merely
by committing it. Operator-supplied credentials after the pushed freeze are a
separate gate.
