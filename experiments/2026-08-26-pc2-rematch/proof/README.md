# proof/ — the checks that had to be shown to fail

A check that cannot fail is not a check. Two things in this tranche are the
only guard against a specific silent failure, so each is driven to RED here
rather than asserted to work.

## `s3_red.txt` — the preflight that stands between P-C2 and a silent P-C1

`preflight_pc2.py`'s S3 refuses the launch if REBUILD F1's discharge channel
will be OFF at runtime. Without it, a P-C2 whose channel never engaged would
produce a typed, verify_root-clean record that reads exactly like a second
P-C1, and nothing in that record would say the organ under test was dark.
That is the same failure family P-C1 paid a whole run for (an inert
`predicate:` battery for eleven cycles).

`mutate_s3.py` removes deviation D1 — restoring `Config.DISCHARGE_POLICY`'s
default to `"off"` — and drives S3. Output in `s3_red.txt`:

    [FAIL] S3-discharge-channel-live-at-runtime: runtime
           DISCHARGE_POLICY='off' enabled=False reask='never' handles_n=0

The mutation is applied IN MEMORY, never to the file on disk: an
edit-and-revert can be interrupted, and this proof is meant to be runnable
beside a live launch.

## The soak's A5/A6 — proven by their own first run, not by a mutation

`soak-pc2.out` is the passing run. The FAILING run is the honest half of the
evidence and is recorded here in words because it was a real one: the first
`--case pc2` soak returned **exit 1** with

    [FAIL] A5-in-run-checker-fired   AttributeError: 'EpistemicState' object
                                     has no attribute 'warrants'
    [FAIL] A6-discharge-channel-carried-them   (same exception)

A1–A4 passed in that same run — typed terminal, `budget_exhausted`,
verify_root clean, cycle 24 of 24 — which is precisely the point: **the four
universal assertions cannot tell a live channel from a dead one.** A5 and A6
exist because of that gap, and their first act was to go red.

The bug was in the reader, not the harness; the underlying facts were
confirmed by hand against the same root (3 fail warrants naming this case's
criteria, 95 `discharge-reask` Measures) before the reader was fixed. The fix
also split the two counts into independent readers, so one reader's exception
can never report the other's count as absent — "the channel carried nothing"
is exactly the finding an instrument must never manufacture.
