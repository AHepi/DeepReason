# CHECKLIST — offline cycle soak instrument

State: step 1 in progress
Traces: SPEC.md S1-S4.

One step per `dr-execute-step` invocation. A step is done only when its
done-criterion output is PASTED under it. Commit and push at every step.

- [ ] **1. Root builder + stub wiring.** `scripts/cycle_soak.py` builds the
      epoch-3 root (dossier, run-input, manifest, problem.json) from the
      committed config with the loopback overrides, and starts the smoke's
      stub server.
      *Done:* the script prints a manifest sha256 and the three criteria
      ids, and a loopback `GET`/`POST` round-trip succeeds.

- [ ] **2. Qualification.** The doctor subprocess produces
      `production-contract-qualification.json` in the root against the
      loopback.
      *Done:* doctor exits 0; the report file exists and
      `require_v6_production_qualification` accepts it.

- [ ] **3. Drive the managed path.** `start_manifest_run` runs to the
      requested cycle depth and terminalizes.
      *Done:* `run-status.json` shows a typed terminal; cycle > 2.

- [ ] **4. S1 terminal assertions.** A1-A4 implemented and evaluated.
      *Done:* pasted assertion block with each of A1-A4 and its verdict.

- [ ] **5. S2 seam census + naming.** The four seams measured from
      `<root>/objects/`, each with reached-by and fails-by-name.
      *Done:* pasted coverage table with a disposition per seam.

- [ ] **6. S4 report + honesty rows.** `soak-report.json` written; any
      `not-coverable` seam carries its reason.
      *Done:* pasted `soak-report.json` coverage section.

- [ ] **7. S3 gate placement.** `docs/AUDIT_BASELINES.md` row,
      `dr-drive-harness` §1 line, `CLAUDE.md` §Live runs sentence — same
      commit as the script. No `tests/` reference to the soak.
      *Done:* pasted diff stat and `grep -rn cycle_soak tests/` empty.

- [ ] **8. Boundary gate.** Full pytest gate + `docs_verify` full mode
      (never concurrently — dr-drive-harness §5b).
      *Done:* pasted `N passed, 0 failed` and docs_verify summary.
