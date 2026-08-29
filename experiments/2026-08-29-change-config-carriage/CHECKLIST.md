# CHECKLIST.md — config carriage (change P15)

Every step has one done-criterion, and each was proven before the next began.

- [x] **1. Map preflight.** DR- ids resolved from `INDEX.md`, seam before
      subsystems. *Done:* `SPEC.md` §0.
- [x] **2. Frozen-surface disposition BEFORE any code.** `blast_radius.py`'s
      CONTACT verdict pasted verbatim, all four rows disposed.
      *Done:* `SPEC.md` §1, committed at `63167a110` — one commit BEFORE
      `run_manifest.py` was touched.
- [x] **3. Measure the naive variant, before choosing the design.** A bare
      optional field on `CompileNoticeV1` moves the manifest sha256 and the
      subject digest for a manifest carrying an unrelated notice.
      *Done:* `proof/notice_digest_probe.py`; `1b6ab4e6→62c6ddc0`,
      `cdb59e87→3db1bc26`.
- [x] **4. `CompileNoticeV1.value` + the omitting wrap serializer.**
      *Done:* the probe re-run returns the HEAD digests unchanged.
- [x] **5. `_emit_compile_notice` carries `value`.** *Done:* every other emit
      site keeps its exact call shape, so its bytes are unchanged.
- [x] **6. The `_CARRIAGE_REQUALIFIES` table and the two carriage constants.**
      *Done:* the priced field's warning is a table row, not a branch.
- [x] **7. Delete `_dropped_field_effect_is_compiled`.** *Done:* emission is
      uniform — every configured non-default dropped field emits exactly one
      carriage notice, no third state.
- [x] **8. Rewrite the write half**, dropping the two now-dead parameters.
      *Done:* leaving a dead parameter is the "one missed helper" shape that
      overran this tranche's budget the first time.
- [x] **9. Collapse the single call site.** *Done:* one caller, so emission
      stays compile-time only.
- [x] **10. Add `_carried_config_values`, fail-closed.** *Done:* three typed
      refusals; a tampered record buys nothing.
- [x] **11. Wire the read, BEFORE the roles injection.** *Done:* a carried key
      cannot become a second route authority.
- [x] **12. R1 — every reachable dropped field round-trips.** *Done:* 24 of
      25 (`proof/roundtrip_carriage.out`); 0 of 25 at HEAD before.
- [x] **13. R2 — no unpriced field moves a subject digest.** *Done:*
      `proof/price_carriage_after.out`, identical to the pre-carriage run.
- [x] **14. R3 — the priced switch compiles with its price visible.** *Done:*
      the notice message names the requalification.
- [x] **15. R4 — nothing retroactive.** *Done:* 72 committed manifests, 2
      differ, and the SAME 2 differ on the pre-change tree
      (`proof/manifest_inertness_probe.py`) — delta zero.
- [x] **16. Update the three fixtures that asserted the defect.** *Done:*
      predicted by `SPEC.md` §3; the single-run-path one now proves all five
      switches reach the run on the operator's own committed config.
- [x] **17. Update the three map checks that ASSERT the defect.** *Done:*
      `CON-authority.md`, `CON-discharge-channel.md`,
      `SEAM-capabilities-x-channels.md` — same commit as the code.
- [x] **18. Record the surface-4 granted contact with a re-runnable check.**
      *Done:* `INV-frozen-surfaces.md`; check proven RED under three
      mutations, tree byte-identical after.
- [x] **19. Budget gate.** *Done:* EXCEEDED 113/94 and 515/513, raised as a
      STOP, re-declared at the measured figures (`SPEC.md` §6).
- [x] **20. Ring.** *Done:* 161 → 187 passed, 0 failed.
