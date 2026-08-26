# Results — the workflow-call-pairing defect

## 2026-08-25 — a verifier that could not be satisfied, and a run that was never wrong

**What was observed.** Under the repair ladder
(`python -u scripts/cycle_soak.py --case epoch3 --induce-repairs 2`) a run terminated with every
operational signal healthy — `state='completed'`, `stop_reason='budget_exhausted'`, cycle 8 of 8,
no `operational_failure` — and then failed its OWN verifier: `verify_root` reported
`{'check': 'workflow-call-pairing', 'detail': 'event seq=31: provider result differs from its
authorized attempt'}`. Deterministic; parked as P1 by the soak tranche with a byte-identical
violation across two earlier runs.

**What the record showed, before any code was read.** The failing event's `LLMCall` carries
`raw_ref=''`, `tokens=0`, and an attempt trace with `usage_unknown: true`, `valid: false`,
`transport_attempts: 4` and four `HTTPError:HTTP-500` diagnostics. Its paired
`ProviderAttemptV1` carries `raw_ref=None`, `outcome='transport_failure'`, and an
`authorization_bundle_ref` and `prompt_sha256` that MATCH the event exactly. Five of the six
pairing agreements held. The sixth differed only as `None` against `''`.

**The diagnosis, and the fork it settled.** The tranche was required to name one of two opposite
fixes: the repair transaction's WRITER emits an ill-paired record, or the pairing check in
verification over-specifies. **It is the checker.** `ProviderAttemptV1.raw_ref` is `str | None`
and spells absence `None`; `LLMCall.raw_ref` is `str` and spells it `""`.
`record_provider_attempt` bridges them with `call.raw_ref or None`, and so does `replay.py`'s
copy of the same six agreements — `attempt.raw_ref != (call.raw_ref or None)`, which PASSED on
this very root. `invariants.py` was the one site that compared the two raw. Because the writer
ALWAYS applies the translation, `None == ""` is false by construction: the sixth agreement was
**unsatisfiable for the entire `outcome="transport_failure"` class**, whatever the run did.

The strongest evidence came from inside the frozen surface itself. `verify_root`'s `blobs` check
computes `empty_raw_allowed = bool(trace and trace[-1].usage_unknown)` and SKIPS an empty
`e.llm.raw_ref` — the exact fact the pairing check 3,400 lines away rejected. The file
contradicted itself, so one of its two readings had to be wrong on its own terms.

The parking note's own hypotheses were both false, and this is recorded rather than quietly
dropped (`docs/ERRATA.md` E53). P1 reasoned that the adapter's `attempt != 0` clamp "did not
fire" and therefore either had a hole or disagreed with the check about repairs. The event is
`attempt: 0` with four TRANSPORT retries inside one authorized attempt: the clamp had nothing to
fire at, and is sound. `--induce-repairs` was merely the shortest reachable route to a transport
failure, because the inducer answers HTTP 500. The park was right to refuse a diagnosis it had
not earned; what drifted was the hypothesis it volunteered alongside.

**The fix.** One comparison in `invariants.py` — `attempt.raw_ref == call.raw_ref` became
`attempt.raw_ref == (call.raw_ref or None)` — so the writer, replay and the verifier now spell
one rule one way instead of two. Contact with FROZEN surface 3 was unavoidable (the defect IS
that file); the grant was requested in FIX.md before implementation, with `blast_radius.py`'s
`CONTACT` verdict pasted and both rows disposed, and is recorded at
`docs/map/INV-frozen-surfaces.md`. Not widening `LLMCall.raw_ref` to `str | None` instead: that
is the format side, and this surface's governing asymmetry is that readers may be fixed freely
and writers and formats may not.

**What the record now shows.** The induced soak exits 0 with all four assertions PASS and
`repairs == 1` — the repair ladder is still exercised, not bypassed. The bare soak exits 0 at
its baseline. `tests/test_v6_transport_failure_pairing.py` is 7 passed, mutation-proven in both
directions: reverting the fix turns the pairing test RED, and blinding the check (`attempt.raw_ref
is None or ...`) turns the dropped-raw-blob test RED. Full gate 4175 passed, 6 skipped, 0 failed.
A targeted before/after over all 14 committed roots carrying provider attempts diffs EMPTY —
every violation class and count unchanged, including the 21 `foreign-criticism` and 1
`attempt-validity` findings that were already there.

**The residue, which is the honest part.** There is **no natural witness and there may never be
one.** Across those 14 roots and 459 committed provider attempts, ZERO are `transport_failure`
and zero have a null raw blob; the reach-rich epoch-1 root's 17 repair attempts are all
`provider_result` with real blobs, and so is every attempt in the epoch-3 lineage. Live runs
against a healthy provider do not produce transport failures, which is precisely why this sat
unseen. So the fix rests on the **induced witness plus the structural argument** — that the check
could not be satisfied by any record the writer is capable of producing, for a plainly reachable
input (a 500, a timeout, a reset). Accepted does not mean true; what is proven here is that the
verifier's rule was unsatisfiable and is no longer, not that a wild run was ever rescued by it.

Three further pieces of residue: the other five pairing agreements are guarded only by mutation
tests, no committed root pairing a mismatched contract id or lease either; the SEMANTIC repair
shape (a well-formed body invalid against the wire schema) still has no offline witness, parked
as P3; and `D1-seat-contract` still reports `[PART]` on the bare soak, which is not coverage.

**One instrument was cleaned up on the way past.** `cycle_soak.py`'s `EXPECTED_RED` still
carried `D4-reservation-bound` with the comment "a parallel window is fixing" it — nine days
after that window delivered, with the soak reporting `[PASS]` for it and P2's own prompt having
instructed the fixing tranche to delete the entry. Removed; the map is now empty, which makes
exit 3 unreachable rather than merely unearned (`docs/ERRATA.md` E54). The lesson P2 had already
written down and nothing enforced: an expected-red carve-out outlives its reason silently unless
its deletion is a step in the fixing tranche's own checklist.
