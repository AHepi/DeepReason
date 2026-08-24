# CHECKLIST — offline cycle soak instrument

State: COMPLETE — all 8 steps done, VALIDATION.md verdict PASS
Traces: SPEC.md S1-S4.

- [x] **1. Root builder + stub wiring.**
```
[soak] stub provider on 127.0.0.1:37303 (reused from wheel_operational_smoke)
[soak] built root: manifest 5cecca56f28fe0d7…  criteria ['uhi-energy-balance@v1',
       'uhi-nocturnal-release@v1', 'uhi-cross-city-modulator@v1']
attached_evidence_enabled: True
```

- [x] **2. Qualification.**
```
[soak] qualified in 3.2s          (doctor rc=0, production-contract-qualification.json written)
```

- [x] **3. Drive the managed path.** Terminalizes typed on every run.
```
1 cycle : state='completed' stop_reason='budget_exhausted'
8 cycles: state='failed'    stop_reason='operational_failure'
          message='transactional reservation bound differs from rendered request'
```

- [x] **4. S1 terminal assertions.** (default soak, --cycles 8)
```
[PASS] A1-typed-terminal            state='failed' stop_reason='operational_failure' typed_error=None
[FAIL] A2-no-operational-failure    message='transactional reservation bound differs from rendered request'
[PASS] A3-verify-root-clean         0 violation(s)
[FAIL] A4-cycles-reached            reached cycle 1 of 8; deepest recorded death was cycle 2
```
A2/A4 fail because the expected-red seam killed the run; both are downstream
of that terminal, so the verdict downgrades them and the soak exits 3, not 1.

- [x] **5. S2 seam census + naming.**
```
[PART] D1-seat-contract    reached {contract-decomposition:0, provider-attempt:4}; repairs 0
[PASS] D2-route-lease      reached {provider-attempt:4}; 0 attempts without a complete lease
[PASS] D3-budget-auth      reached {dispatch-authorization:5}
[FAIL] D4-reservation-bound  reached {token-reservation:5}  (EXPECTED RED)
       reason: transactional reservation bound differs from rendered request
```

- [x] **6. S4 report + honesty rows.** `soak-report.json` written each run;
      RESULTS.md carries the standing rows, including the two rows (D2 tuning,
      D3 denial) that are weaker than their green tick suggests.

- [x] **7. S3 gate placement.**
```
 .claude/skills/dr-drive-harness/SKILL.md |  7 +++++++
 CLAUDE.md                                |  7 +++++++
 docs/AUDIT_BASELINES.md                  | 22 ++++++++++++++++++++++
$ grep -rn "cycle_soak" tests/
none — S3 holds (no pytest gate runs the soak)
```

- [x] **8. Boundary gate.** Full pytest gate + `docs_verify` full mode, run
      one at a time (dr-drive-harness §5b).
```
$ python -m pytest tests/ -q -n 4
3875 passed, 6 skipped in 938.34s (0:15:38)

$ python tools/docs_verify.py
docs_verify [full]: 63 documents, 994 checks, 4 workers
docs_verify: 3 failed   <- exactly the recorded baseline (CON-run-identity.md
                           git-history checks; this checkout is --depth 1)
```
