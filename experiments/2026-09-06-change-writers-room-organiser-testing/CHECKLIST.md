# Checklist for: the organiser seat — testing the writer's room on the full harness
State: next=3 blockers=none   <- refreshed at every commit; a fresh session resumes from this line alone
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order. One step per dr-execute-step invocation.
Map ids (from REQUEST.md): DR-INV-frozen-surfaces, DR-SUB-evidence, DR-INV-seat-section-plugins, DR-INV-seat-section-sources, DR-CON-warrants-and-attacks, DR-SEAM-packs-and-token-economy-x-rules, DR-CON-packs-and-token-economy, DR-SUB-llm, DR-SUB-rules, DR-CON-conjecture-source, DR-SUB-minireason, DR-SEAM-llm-x-minireason. Seam read first: DR-SEAM-packs-and-token-economy-x-rules (the nine source-computed contexts and the allocator the evidence sections live under).
Tranche base: `d3f047932` (main). Diff-budget ceiling (SPEC Budget): 450 insertions over `src tests docs/map`.

- [x] 1. (S3) Write `tools/room_to_attachment.py` and run it against the room root into `attachment/` (three plain-text files, one paragraph per record, refuted-if proposals first) with `attachment/CONVERSION.json`.
      done-when: the tool prints `records 94 (12 conjectures, 46 proposals, 36 objections)` and `verbatim 94/94`
      output: `records 94 (12 conjectures, 46 proposals, 36 objections)` / `verbatim 94/94` / `chars 53493` / `01-conjectures.txt: 12 records, 9281 bytes` / `02-proposals.txt: 46 records, 17566 bytes` / `03-objections.txt: 36 records, 33377 bytes`. One deviation from the plan, recorded: a comma in a header line is folded to `;` (one angle label carried one), because the header is the one line that could change how the file is admitted; the body keeps the label verbatim.
- [x] 2. (S4) [COMMIT] Write `attachment/ATTACHMENT.sha256` and commit the converter, the attachment and the digest.
      done-when: `sha256sum -c attachment/ATTACHMENT.sha256` -> every line OK; `git ls-files attachment | wc -l` -> 5
      output: `01-conjectures.txt: OK / 02-proposals.txt: OK / 03-objections.txt: OK / CONVERSION.json: OK`; `git ls-files attachment | wc -l` -> 5 (in this commit)
- [ ] 3. (S1, S7, S14) Register in `src/deepreason/llm/seat_layouts.py`: `seat-pack.conjecturer.organiser-v1` (legacy entries filtered and re-budgeted per S9), `seat-pack.critic.evidence-blind-v1` (legacy minus the two evidence entries), shells `seat.conjecturer.organiser-v1` (form `conjecturer.turn.v6`, wording `role-prompt.organiser-v1`) and `seat.critic.evidence-blind-v1`; the docstring records the compact.v2 contradiction (A1).
      done-when: SPEC S1's first accept command prints four shell ids and exits 0; S14's accept command exits 0
- [ ] 4. (S1, S9) Add `_OrganiserOutputContract` (`dr.output-contract.organiser`, section `output-contract`) to `src/deepreason/llm/seat_plugins.py` and append it to `CONJECTURER_PLUGINS`.
      done-when: `python -c "from deepreason.llm.seat_plugins import ensure_seeded; ensure_seeded(); from deepreason.llm.seat_sections import resolve_section_plugin; print(resolve_section_plugin('dr.output-contract.organiser').section_id)"` -> `output-contract`; `python -m pytest tests/test_conj_pack_legacy_golden.py tests/test_crit_pack_legacy_golden.py tests/test_seat_section_architecture.py -q` -> 0 failed
- [ ] 5. (S1, S9, A11) Register `role-prompt.organiser-v1` in `src/deepreason/llm/role_prompts.py` (legacy dicts copied by reference; only the conjecturer's `standard` and `compact_directive` replaced).
      done-when: `python -c "from deepreason.llm.role_prompts import resolve_role_prompt_template as r; o=r('role-prompt.organiser-v1'); l=r('role-prompt.legacy-v0'); assert o.standard['conjecturer']!=l.standard['conjecturer']; assert all(o.standard[k]==l.standard[k] for k in l.standard if k!='conjecturer'); print('ok')"` -> `ok`; `python -m pytest tests/test_role_prompt_registry.py -q` -> 0 failed
- [ ] 6. (S12, S14) Copy the three attachment files to `tests/fixtures/organiser_room/` (byte-identical) and write `tests/test_organiser_seat.py` (assertions a–f, the blind-critic layout assertion, the wording-identity assertion, the mutation companion).
      done-when: `python -m pytest tests/test_organiser_seat.py -q` -> `N passed` with N >= 8, 0 failed; `cmp tests/fixtures/organiser_room/01-conjectures.txt attachment/01-conjectures.txt` (and the other two) -> silent
- [ ] 7. (S25) [COMMIT] Map: add to `docs/map/INV-seat-section-plugins.md` the four-shells paragraph and a column-0 `check:` (organiser shell pairs `turn.v6` with the organiser layout; the blind critic layout omits `dr.evidence.citable` and `dr.premise-invitation`); run that document's checks; commit steps 3–7 together with `diff_budget` and `blast_radius` pasted.
      done-when: `python tools/docs_verify.py` reports 0 failed (full mode, since `src/` moved); `python tools/diff_budget.py d3f047932 --ceiling 450 --paths src tests docs/map` -> verdict WITHIN; `python tools/blast_radius.py --files src/deepreason/llm/seat_layouts.py src/deepreason/llm/seat_plugins.py src/deepreason/llm/role_prompts.py --symbols register_shipped_layouts ensure_seeded _ensure_seeded --against d3f047932` -> `frozen_surface_contacts: []`
- [ ] 8. (S5) Write `proof/dry_attach.py`; run it; commit its output as `proof/DRY_ATTACH.txt`.
      done-when: the output carries `sources 3 blocks 94 refusals 0`, `legend shown 32 withheld 62`, `frozen pack sources 3 excluded 0`
- [ ] 9. (S11, S6) [COMMIT] Write `proof/render_brief.py`; run it under `PACK_TOKEN_BUDGET=24000` with the organiser shell bound; commit `proof/ORGANISER_BRIEF.txt` and `proof/ORGANISER_RECEIPTS.json`.
      done-when: `wc -c proof/ORGANISER_BRIEF.txt` > 55000; `grep -c 'BEGIN UNTRUSTED SOURCE DATA' proof/ORGANISER_BRIEF.txt` -> 3; the receipts show `frozen-evidence-context` and `citable-evidence-blocks` rendered, not compressed or dropped; the S9 accept greps hold
- [ ] 10. (S6, S8, S13, S14, C3) [COMMIT] Write `PARKED.md`: P1 (managed path does not load the plugin dir), P2 (legend cap and excerpt are code), P3 (cycle-scoped pairing), P4 (a critic that reads the room bodies), P5 (per-countercondition block pointers), each with a ready-to-send prompt.
      done-when: `grep -c '^## P' PARKED.md` -> 5
- [ ] 11. (S16, S17) Write `tools/compose_result.py` with `--self-test` against the committed full-harness root named in SPEC S16.
      done-when: `python tools/compose_result.py --self-test` -> exit 0 and prints a survivor count; `grep -c 'urllib\|requests\|ollama' tools/compose_result.py` -> 0
- [ ] 12. (S16, S18) [COMMIT] Write `tools/judge_organiser.py` (copy of `d8/judge_d8.py`, only `harvest` and paths changed) and `tools/analyse_organiser.py` (D8's estimators over three arms, pairwise R–0 and R–H).
      done-when: the CRITERIA diff against `judge_d8.py` is empty; `python tools/judge_organiser.py --help` and `python tools/analyse_organiser.py --help` exit 0
- [ ] 13. (S2, S20, S21) [COMMIT] Write `runs/config.yaml`, `runs/setup_and_qualify.sh`, `runs/armH.sh`, `runs/armR.sh`, `runs/chain.sh`, `runs/snapshot.sh`; `chmod +x`.
      done-when: `bash -n` on every script exits 0; `deepreason --config runs/config.yaml config | grep '^PACK_TOKEN_BUDGET:'` -> `PACK_TOKEN_BUDGET: 24000`; the S2 greps hold; `git check-ignore -q env`
- [ ] 14. (S15, S19) [COMMIT] Write `PREREG.md` and commit it with `sha256: <digest>` in the commit message.
      done-when: `sha256sum PREREG.md` equals the digest in `git log -1 --format=%B -- PREREG.md`
- [ ] 15. (S20) [COMMIT] Run `python -u scripts/cycle_soak.py --case epoch3 | tee runs/soak.log` (offline; no key needed) and commit the log.
      done-when: `runs/soak.log` ends with a clean exit (`rc=0` appended by the runner line)
- [ ] 16. (S10, S22, S23, S24) [COMMIT] Write `RESULTS.md`: the dated segment (what the record shows offline; what it does not — no arm ran; one question, one model, one room), the 12-of-12 statement, the failure-budget ledger at 0.
      done-when: the S10, S22, S23 (RESULTS half), S24 greps hold
- [ ] 17. (S25) Map check, full: `python tools/docs_verify.py` and `--audit` and `--links`.
      done-when: 0 failed; 0 audit findings; 0 dangling
- [ ] 18. (S25) Full gate: `python -m pytest tests/ -q -n 4`.
      done-when: output ends `N passed, 0 failed` (paste it; the known-flaky set per docs/AUDIT_BASELINES.md re-run serially if it bites)
- [ ] 19. (all) [COMMIT] push and confirm clean tree.
      done-when: `git status --porcelain` is empty AND `git rev-parse HEAD origin/claude/writers-room-organiser-testing-degagn` prints one hash twice
