# CHECKLIST — W7

One step, one done-criterion. Nothing is marked done without its pasted
output. Authority: `SPEC.md`, which cites `REQUEST.md` R1–R25.

- [ ] **S1 — Environment and repository.** `git remote -v` names
      `AHepi/DeepReason`; `be9bcff54` is an ancestor of HEAD;
      `deepreason`, `pytest`, `xdist` and `jsonschema` import.
      *Done when:* the four outputs are pasted into VALIDATION.md. (R1, R4)

- [ ] **S2 — Read every named input in full.** W1/W4/W5/W6 from `main`;
      W2 and W3 from their own branches (A1); PROGRAM.md; P-R1 RESULTS
      and the strengthened P5; P-C1 RESULTS; the three RESEARCH_ notes;
      LESSONS_LEARNED.
      *Done when:* VALIDATION.md carries the read log, file by file. (R7, R9–R12)

- [ ] **S3 — Write `docs/RUN_ANATOMY_SYNTHESIS_2026-08-26.md`:** header
      (worry-first opening; the no-`check:`-lines statement; the A1
      branch note), §1 organ table, §2 causal story, §3 three lists,
      §4 roads, appendix.
      *Done when:* the file exists; heading audit shows exactly four
      `## ` sections plus header and appendix; every organ row carries a
      number and a citation; `grep -c '^check:'` is 0. (R6, R13–R21)

- [ ] **S4 — The docs gate.** `python tools/docs_verify.py` full run.
      *Done when:* 0 failed, pasted. (R22)

- [ ] **S5 — The diff gate.** `git diff --stat origin/main` shows exactly
      one new file under `docs/` plus the tranche directory; nothing
      under `src/` or `tests/`.
      *Done when:* both outputs pasted. (R2, R3, R23)

- [ ] **S6 — VALIDATION.md**, requirement by requirement, with pasted
      proof for each acceptance check in SPEC.md.
      *Done when:* the verdict line reads PASS or FAIL, with no
      unproven row. (all R)

- [ ] **S7 — DELIVERY.md**, R-by-R reconciliation, closing with the
      document's own worry-first opening sentence, quoted.
      *Done when:* the quotation matches the document byte for byte. (R25)

Commit and push after every step (R24).
