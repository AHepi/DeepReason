# Parked — repo-level gaps found while falsifying the map

One line each; found 2026-08-02, none fixed here.

- `SCHOOL_ROUTE_LEASE_MISMATCH` / `SCHOOL_ROUTE_ENDPOINT_MISMATCH`: disabling
  the firewall's lease-mismatch refusal leaves the entire test suite green;
  no test asserts either code (found via SEAM-manifest-x-schools).
- `resolve_conjecture_route` and `compile_criticism_assignments` are imported
  by no test anywhere (same seam).
- `test_failed_control_append_rolls_live_materialization_back` passes with
  `_commit`'s `_reset()` deleted — `WorkflowReplayState.digest` cannot see a
  failed append (found via SEAM-harness-x-workflow).
- No test covers a context receipt without scratch exposure; deleting that
  recovery guard passes the suite (found via SEAM-rules-x-scratch).
- Writer-side torn-tail repair was uncovered by the ring the seam doc named;
  the doc's ring now includes test_torn_append.py, but the gate-level gap is
  worth its own look (found via SEAM-harness-x-verification).
- The sweep instrument vs direct-load census delta (11 ERROR vs 14 raising
  manifests): three pre-v6 roots surface through verify_root_report as
  verdicts rather than errors — unexplained, measured only.
