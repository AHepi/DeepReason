# Reproduction

Form: unit-test (native — the real adapter, the real `conj` rule, the real transaction service;
no hand-written record), corroborated by the committed record-level reproduction the tranche
inherited.

Artifact: `tests/test_v6_transport_failure_pairing.py`
Inherited artifact (unchanged, re-run at this base):
`python -u scripts/cycle_soak.py --case epoch3 --induce-repairs 2`

## Current output — the defect

    $ python -m pytest tests/test_v6_transport_failure_pairing.py -q
    >       assert verify_root(root)["violations"] == []
    E       AssertionError: assert [{'check': 'w...zed attempt'}] == []
    E         Left contains one more item: {'check': 'workflow-call-pairing',
    E          'detail': 'event seq=5: provider result differs from its authorized attempt'}
    1 failed, 6 passed in 3.92s

The reproduction takes the committed `_canonical_root` controller-v3 fixture and loses the
transport on the FIRST dispatch (`MockEndpoint.complete` raises `EndpointError` once). `conj`
takes its `except EndpointError` arm at `rules/conj.py:1901`, the transaction service writes the
`ProviderAttemptV1` at `transaction_service.py:529`, and the resulting root carries exactly the
shape the live soak produced:

    call.raw_ref    = ''                     (LLMCall.raw_ref: str)
    attempt.raw_ref = None                   (ProviderAttemptV1.raw_ref: str | None)
    attempt.outcome = 'transport_failure'
    attempt.authorization_bundle_ref == event.llm.dispatch_authorization_ref
    attempt.prompt_sha256            == event.llm.prompt_ref

The soak's violation is at seq=31 and this one at seq=5; the check name and the detail string
are identical, and so is the mechanism. The unit reproduction is 4 seconds against the soak's
~160, and needs no stub provider process.

Confirms diagnosis: yes — the only field that differs between the durable attempt and the call
it was built from is `raw_ref`, and it differs only as `None` vs `''`, which is precisely the
translation the writer performed one line before recording and the verifier's copy of the six
agreements omits (`invariants.py:398`).

## The mutation proof, and what it is worth at each stage

Six mutation tests each break exactly ONE of the six agreements and require the finding back.
They are GREEN today, which proves almost nothing — on the unfixed tree the check fires on any
transport-failure root, so they pass trivially. **Their evidential value is entirely
post-fix**: once test 1 shows the unmutated root verifying clean, every violation a mutated copy
produces is attributable to its mutation and nothing else. Both directions are therefore
covered, and the second one is the one that matters:

  - `..._a_dropped_raw_blob_still_fails_closed` — call carries a body, attempt is `None`.
    This is the case a careless normalization would swallow. `None` must equal an ABSENT call
    raw, never a present one.
  - `..._an_invented_raw_blob_still_fails_closed` — the mirror: attempt claims a body the call
    never carried.
  - `..._a_mismatched_contract_still_fails_closed`
  - `..._a_mismatched_prompt_digest_still_fails_closed`
  - `..._a_mismatched_authorization_bundle_still_fails_closed`
  - `..._a_call_bound_to_another_work_item_still_fails_closed`

`_rewrite_attempt` re-anchors the lifecycle transition and the event outputs onto the mutated
attempt's new content address, so a mutation trips `workflow-call-pairing` and not
`workflow-decision` — a mutation that fails a different check would prove nothing about this one.

Post-fix expectation:

    python -m pytest tests/test_v6_transport_failure_pairing.py -q      ->  7 passed
    python -u scripts/cycle_soak.py --case epoch3 --induce-repairs 2    ->  exit 0,
                                                                            A3-verify-root-clean PASS
