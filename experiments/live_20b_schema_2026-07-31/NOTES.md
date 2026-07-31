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

---

## The 20B battery, completed: three more prose-only constraints found

The first attempt died opaquely at concurrency 12. At concurrency 4 the
battery completes, so the original failure was transport/concurrency, not
the model. (My own diagnostic script then threw the report away on a
`json.dumps` of a pydantic object — the executor had succeeded.)

Code as of this battery: scratch.link and atomic-conjecture schema-
enforced; the v6 turn NOT yet. So this is a genuine BEFORE for the turn.

    contract                            first  eventual  repairs  gate
    scratch.cluster-guide.compact.v1    13/20     15/20       12  FAIL
    conjecturer.turn.v6                 17/20     17/20       12  FAIL
    scratch.link.compact.v1             19/20     20/20        2  FAIL
    bridge.ledger.v3                    19/20     19/20        1  pass
    (12 others)                         20/20     20/20        0  pass

The release gate (`doctor.py:129`) needs eventual >= 19 AND zero alias
failures AND zero scope violations AND semantic admission on every
eventual pass. Reading the three failures by that gate:

    conjecturer.turn.v6              eventual 17, scope_violations 8
    scratch.cluster-guide.compact.v1 eventual 15, alias_failures 4, scope 4
    scratch.link.compact.v1          eventual 20, alias_failures 2

`scratch.link.compact.v1` is the important one. Its endpoint rule — the
one this tranche encoded — is FIXED: 20/20 eventual, 2 repairs, down from
11/20 with 18 repairs on glm-5.2 before the fix. It now fails for a
DIFFERENT reason: 2 alias failures. The schema fix worked and uncovered
the next prose-only constraint underneath it.

### The next constraint, and it is the operator's own third bullet

"Enumerations or namespaces described in prose but not captured in regex
patterns." The scratch contracts are constructed WITH the legal alias
table and the compiler rejects anything outside it, but the rendered
schema said only `{"type": "string"}` for a handle. A model reading the
schema had no way to know which strings were legal, so it invented one.

Corroboration from the same battery, and it is decisive: the MINIMAL
cluster guide has no handle field at all and scored 20/20; the COMPACT
one, which has `entry_points`, scored 13/20 with 4 alias failures.

Fixed by binding the legal handles as an `enum` in the schema, exactly as
`ConjecturerTurnWireContractV6._bind_alias_array` already does for its
alias arrays. Runtime is unchanged — the compiler already refused unknown
handles; the schema now says so.

    from_handle before  {"maxLength": 64, "minLength": 1, "type": "string"}
    from_handle after   {"type": "string", "enum": ["SCR_001", "SCR_002"]}

### Still to measure

This battery predates both the v6 turn encoding and the handle enums. The
re-measurement is the next step; nothing about the 20B's post-fix numbers
is claimed until it runs.

`conjecturer.turn.v6`'s 8 scope violations are NOT addressed by either
fix — scope violations are handle-namespace errors inside nested
structures (candidate `neighbours`, context-request aliases), and the v6
contract already enum-binds those arrays. That one needs its own
diagnosis and is not claimed as fixed.
