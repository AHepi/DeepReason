# Checklist for: adopt h-EPI's claims mechanism for DeepReason's measures
State: done blockers=none
Map ids this plan was built on: `DR-INDEX`, `DR-INV-frozen-surfaces`,
`DR-SUB-harness`, `DR-CON-evidence-states`, `DR-INV-evidence-channels`,
`DR-SUB-evidence`, `DR-INV-reference-menu`, `DR-SUB-verification`,
`DR-SCHEMA`. No seam document is in play: the change adds a `tools/`
instrument that imports nothing from `src/deepreason/` and joins no two
subsystems.
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order.
One step per dr-execute-step invocation.

- [x] 1. (S6) Write `docs/CLAIMS_SCHEMA.md`: the claims file's shape, the six
      condition keys with one worked example each, the three statuses, the
      two standings, the non-inductive limit, the "what this is not" section
      (not a gate/status/score; no readiness from a person), and the map
      citations R10 names.
      done-when: `python3 -c "import pathlib,sys; t=pathlib.Path('docs/CLAIMS_SCHEMA.md').read_text(); [sys.exit('missing '+m) for m in ['all_of','any_of','not','status','event','measure','control','object','REFUTED','UNREFUTED_FOR_DECLARED_SCOPE','NOT_TESTED','SHOWN_ABLE_TO_FAIL','NOT_SHOWN_ABLE_TO_FAIL','DR-SUB-harness','DR-CON-evidence-states','DR-INV-evidence-channels'] if m not in t]; print('ok')"` -> `ok`

- [x] 2. (S6) [COMMIT] Commit the document alone, so the shape is written
      down before the code that implements it.
      done-when: `git log --oneline -1` names CLAIMS_SCHEMA.md and
      `git status --porcelain docs/` is empty.

- [x] 3. (S2, S3, S4, S5) Write `tools/record_claims.py`: the root reader,
      the claims loader, the fail-closed condition compiler, the evaluator,
      the text and JSON renderers, and the CLI.
      done-when: `python tools/record_claims.py --help` exits 0 and prints
      `--claims`, `--root`, `--json`, `--markdown`.

- [x] 4. (S2, S14) Prove the tool imports nothing from the harness and opens
      nothing for writing.
      done-when: `python3 -c "import pathlib; s=pathlib.Path('tools/record_claims.py').read_text(); assert 'import deepreason' not in s and 'from deepreason' not in s; assert '_refuse_inside_a_root' in s; print('read-only ok')"` -> `read-only ok` (SPEC S2 correction: the guarantee is that nothing is written INTO A ROOT, which `_refuse_inside_a_root` enforces and S12 proves)

- [x] 5. (S7, S8) Write
      `experiments/2026-09-06-change-writers-room-organiser-testing/claims.json`
      with the nine claims of SPEC S7, each proxy claim carrying a `note`
      that says so.
      done-when: `python3 -c "import json; d=json.load(open('experiments/2026-09-06-change-writers-room-organiser-testing/claims.json')); ids=[c['claim_id'] for c in d['claims']]; assert ids==['ORG-CITE-01','ORG-PLAN-01','ORG-PLAN-02','RUN-STOP-01','CRIT-CAP-01','ORG-COND-01','RUN-TERM-01','EVID-EXPOSED-01','ARMH-STOP-01'], ids; print(len(ids),'claims')"` -> `9 claims`

- [x] 6. (S7, S9) Run the claims file against the FAILED ARM R root and
      confirm every expected status and standing in SPEC S7's table.
      done-when: the JSON output's `(claim_id, status, standing)` triples
      equal SPEC S7's expected column, and the process exits 0. Paste the
      text output into the step record.

- [x] 7. (S2, S3, S4, S5, S7, S8, S9) [COMMIT] Commit the tool and the claims
      file together with the pasted output in the message.
      done-when: `git status --porcelain tools/ experiments/2026-09-06-change-writers-room-organiser-testing/` is empty.

- [x] 8. (S10, S12) Write `tests/test_record_claims.py`: synthetic roots for
      each primitive, an `always` refutation, a full survival, both
      standings, `NOT_TESTED`, the fail-closed vocabulary tests, the
      mutation proof, and the read-only proof.
      done-when: `python -m pytest tests/test_record_claims.py -q` ->
      `N passed`, 0 failed (paste the line).

- [x] 9. (S10) Ring: the test files this change could plausibly disturb.
      done-when: `python -m pytest tests/test_record_claims.py tests/test_provider_transport_faults.py -q` -> 0 failed.

- [x] 10. (S10, S12) [COMMIT] Commit the tests.
      done-when: `git status --porcelain tests/` is empty.

- [x] 11. (S11) Append the instrument section to
      `docs/map/INV-frozen-surfaces.md` under "The instruments that prove you
      did not break anything", with a `check:` that runs the tool on the
      committed ARM R root and asserts a specific status.
      done-when: `python tools/docs_verify.py 2>&1 | tail -3` -> 0 failed.

- [x] 12. (S11) Prove the new check can fail: mutate the tool's status
      derivation in a scratch copy, re-run the check, confirm non-zero exit,
      restore.
      done-when: the mutated run exits non-zero, the restored run exits 0,
      and `git diff --stat tools/record_claims.py` is empty afterwards.

- [x] 13. (S11) [COMMIT] Commit the map section.
      done-when: `git status --porcelain docs/map/` is empty.

- [x] 14. (S13) Write `PARKED.md` with the appraisal-labelling entry (first
      line: readiness is read from the record, never marked by a person) and
      its ready-to-send prompt as one fenced block.
      done-when: `python3 -c "import pathlib; t=pathlib.Path('experiments/2026-09-06-change-record-claims/PARKED.md').read_text(); assert 'appraisal.py' in t and 'P4' in t and 'never marked by a person' in t; print('ok')"` -> `ok`

- [x] 15. (S14, R18) Prove `src/deepreason/` is byte-untouched and PREREG.md
      is unedited.
      done-when: `git diff --stat origin/main...HEAD -- src/deepreason/ experiments/2026-09-06-change-writers-room-organiser-testing/PREREG.md` -> empty output.

- [x] 16. (all) Diff budget against SPEC's ceiling.
      done-when: `python tools/diff_budget.py origin/main --ceiling 1100 --paths tools/record_claims.py tests/test_record_claims.py docs/CLAIMS_SCHEMA.md docs/map/INV-frozen-surfaces.md experiments/2026-09-06-change-writers-room-organiser-testing/claims.json` -> verdict not EXCEEDED (paste it).

- [x] 17. (all) Map check: `python tools/docs_verify.py` and
      `python tools/docs_verify.py --audit`.
      done-when: 0 failed, and `--audit` reports no NEW vacuous check
      attributable to this tranche (paste both tails).

- [x] 18. (all) Full gate: `python -m pytest tests/ -q -n 4`. Run ONCE, at
      this boundary, because `tests/` changed (R22).
      done-when: output ends `N passed, 0 failed` (paste it).

- [x] 19. (all) [COMMIT] Push and confirm a clean tree.
      done-when: `git status --porcelain` is empty AND
      `git rev-parse HEAD origin/claude/record-claims-tool-evul4v` prints the
      same hash twice.
