# Checklist for: Rung 7 sub-tranche 7a — the adjudication × authority seam document
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in
order. One step per dr-execute-step invocation.

**Scope fence (R10):** no path under `src/` or `tests/` may be touched
by any step below. 7b and 7c are deferred. A step that wants to edit
`src/` is a planning error, not a licence.

**Map ids this plan was scoped from** (`dr-plan-steps` rule 4b):
- `DR-SEAM-adjudication-x-authority` — **to be created**, this tranche's
  whole deliverable.
- `DR-SUB-adjudication` — side A; today carries `adjudication x
  authority` in `Seams-undocumented:`.
- `DR-CON-authority` — side B; today carries the same pair, and an
  entirely empty `Seams:` header.
- `DR-INDEX` — the seam matrix that must name the new document.
- `DR-SCHEMA` — the contract the new document must satisfy.
- `DR-SEAM-adjudication-x-rules` — the adjacent seam, read at preflight;
  it owns the mint-side story this document must not duplicate.
- `DR-INV-frozen-surfaces` — read before designing (spec phase); the
  governing principle this document exists to make findable.

**Stamp policy, decided here so execution does not have to
improvise** (`DR-SCHEMA`: "If you did not check the document's claims,
do not advance the stamp"): the NEW document gets a `Verified-at:` of
the tranche base `bb508414`, the tree its claims were measured against.
`SUB-adjudication.md` and `CON-authority.md` get a header edit ONLY and
their stamps are deliberately NOT advanced — this tranche does not
re-run their full check sets. That is the rung-4/rung-5 "left stale"
precedent, and it is the honest state.

---

- [x] 1. (S8) Record the `docs_verify` BEFORE baseline for the whole map
      (full mode, not `--fast` — the E10 companion lesson), plus
      `--audit` and `--links` counts.
      done-when: baseline captured in the step record showing document
      count, check count, and `docs_verify: 0 failed`; `--audit` and
      `--links` each 0.

      **DONE, but the baseline is RED — done-criterion partially
      contradicted by the tree. Recorded, not improvised around.**

          docs_verify [full]: 50 documents, 807 checks, 4 workers
          FAIL SEAM-harness-x-verification.md:253 -> AssertionError: (47, {0: 30, 1: 14, 2: 3})
          FAIL SEAM-manifest-x-schools.md:271     -> AssertionError: 44
          docs_verify: 2 failed
          docs_verify --audit: 0 finding(s)
          docs_verify --links: 0 dangling reference(s), 50 document(s)

      Two pre-existing failures, both the root-census checks, both
      caused by rung 5's post-delivery commits `f6d41bff`/`1f20a6bd`
      committing the two live A/B run roots. NOT caused by this tranche
      (`find <tranche-dir> -name log.jsonl` → 0). Full analysis and
      disposition: PARKED.md P1. Fixing it is another tranche's job
      (operator scoped this one to "7a only"; cross-routing parks a
      defect found mid-change).

      **Consequence, declared here rather than discovered at
      validation:** this tranche's acceptance becomes DELTA-based.
      Step 10's criterion is amended below from "0 failed" to "exactly
      these 2 pre-existing failures and no others."

- [x] 2. (S8) Create `docs/map/SEAM-adjudication-x-authority.md` per
      `DR-SCHEMA`: `<!-- DR-SEAM-adjudication-x-authority -->` on line 1,
      `Verified-at: bb508414`, `Verify:`, `Owns:`, `Sides: DR-SUB-adjudication,
      DR-CON-authority`, and a body carrying the M5/M6 asymmetry as
      column-0 checks. No `Sweep:` header, with the reason stated in the
      body (`DR-SCHEMA`: a sweep whose candidates are all readers cries
      wolf; `SEAM-evaluation-x-ontology` is the recorded precedent) —
      here the agreement is an ABSENCE of traffic, so there is no field
      for a sweep to follow.
      done-when: the file exists, line 1 is the DR- id comment, and it
      declares `Sides: DR-SUB-adjudication, DR-CON-authority`.

          <!-- DR-SEAM-adjudication-x-authority -->
          Verified-at: 27e088cb
          Verify: python tools/docs_verify.py
          Owns: src/deepreason/authority.py, src/deepreason/adjudication/support.py
          Sides: DR-SUB-adjudication, DR-CON-authority

      No `Sweep:` header, with the reason in the body: the agreement is
      the ABSENCE of traffic, so there is no field for a sweep to
      follow (`SEAM-evaluation-x-ontology` precedent).

      **Deviation from the plan, recorded not silent:** the stamp policy
      above named `bb508414`; the document carries `27e088cb`, the head
      at the moment the claims were actually measured (the plan was
      written before the step-1 baseline commit moved the head). No
      `src/` file differs between those two commits, so both stamps
      describe the same tree the claims were checked against —
      `27e088cb` is the more precise of the two, which is why it
      stands.

- [x] 3. (S8) Prove every check in the new document passes, in
      isolation, before it is wired into the map.
      done-when: each `check:` line in the new file runs and exits 0;
      the count of checks is pasted.

          checks found: 8
            check 1: rc=0    check 5: rc=0
            check 2: rc=0    check 6: rc=0
            check 3: rc=0    check 7: rc=0
            check 4: rc=0    check 8: rc=0
          all pass

- [x] 4. (S8) Prove the new document's checks CAN fail — the `--audit`
      rule is necessary but not sufficient, and `DR-SCHEMA`'s six
      falsification classes exist because 44 checks that could not fail
      shipped. Falsify at least the two load-bearing ones (the
      label-time and mint-time claims) against a deliberately mutated
      tree, then revert.
      done-when: each falsified check is shown exiting non-zero, and
      `git status --porcelain src/` is empty again afterwards.

      Mutant 1 — `_adjudicate` made a no-op (labels no longer
      recomputed), `__pycache__` cleared first per `DR-SCHEMA`'s
      measurement rule:

          mutant applied
          check 1 correctly FAILED under mutation
          check 1 passes again after revert

      Mutant 2 — `build_att` gutted to `return set()` (graph no longer
      derived):

          mutant applied
          check 2 correctly FAILED under mutation
          check 2 passes again after revert

          $ git status --porcelain src/
          (empty)

      Neither check is vacuous: each is bound to the real derivation it
      claims, not to the sabotage surviving.

- [x] 5. (S8) [COMMIT] Add the `INDEX.md` seam-matrix row for
      `adjudication × authority`, pointing at the new document.
      done-when: `grep -n "adjudication × authority" docs/map/INDEX.md`
      names `SEAM-adjudication-x-authority.md`.

          106:| — | adjudication × authority | `SEAM-adjudication-x-authority.md` |

      The matrix's trailing sentence moved "last six" -> "last seven"
      and now names why this pair is the strongest case of a seam the
      coupling metric cannot see.

- [x] 6. (S8) Update `docs/map/SUB-adjudication.md`'s headers: add
      `DR-SEAM-adjudication-x-authority` to `Seams:`, remove
      `adjudication x authority` from `Seams-undocumented:`. Update its
      seam TABLE row for authority from "undocumented" to documented.
      `Verified-at:` NOT advanced (stamp policy above).
      done-when: `Seams:` contains the new id, `Seams-undocumented:` no
      longer contains `adjudication x authority`, and `Verified-at:` is
      unchanged from `08dcdf3c`.

          Verified-at: 08dcdf3c            <- unchanged, per stamp policy
          Seams: DR-SEAM-adjudication-x-rules, DR-SEAM-adjudication-x-authority
          Seams-undocumented: adjudication x harness, adjudication x ontology, adjudication x schools, adjudication x verification

      Its seam TABLE row for authority moved from "undocumented" to
      naming the document. The row count is pinned by that document's
      own check and is still 6.

- [x] 7. (S8) Update `docs/map/CON-authority.md`'s headers the same way
      (its `Seams:` is currently empty — the ERRATA E9 shape exactly).
      `Verified-at:` NOT advanced.
      done-when: `Seams:` contains the new id, `Seams-undocumented:` no
      longer contains `adjudication x authority`, and `Verified-at:` is
      unchanged from `d057f306`.

          Verified-at: d057f306            <- unchanged, per stamp policy
          Seams: DR-SEAM-adjudication-x-authority
          Seams-undocumented: authority x manifest, authority x rules, authority x scheduler

      Its `Seams:` was entirely EMPTY before this step — the ERRATA E9
      shape. Recorded as PARKED.md P3.

- [x] 8. (S8) `python tools/docs_verify.py --links`
      done-when: `0 dangling reference(s)`, and the document count is
      one higher than step 1's.

          docs_verify --links: 0 dangling reference(s), 51 document(s)
          (step 1 baseline: 50 documents)

- [x] 9. (S8) `python tools/docs_verify.py --audit`
      done-when: `0 finding(s)` — proving in particular that the new
      document is not check-less and carries no vacuous check.

          docs_verify --audit: 0 finding(s)

- [x] 10. (S8) `python tools/docs_verify.py` — FULL mode, never
      `--fast` (E10's companion lesson: `--fast` reuses cached results
      and cannot see a document newly affected).
      done-when (AMENDED at step 1, see PARKED.md P1 — delta-based
      because the baseline was already red): `docs_verify: 2 failed`,
      and the two failures are EXACTLY
      `SEAM-harness-x-verification.md:253` and
      `SEAM-manifest-x-schools.md:271` — the same two, unchanged, from
      step 1. Any third failure, or either of these two changing its
      detail, is a failed step. Document count 51 (was 50) and check
      count higher than 807 by the number this tranche added.

          BEFORE: docs_verify [full]: 50 documents, 807 checks, 4 workers
          AFTER:  docs_verify [full]: 51 documents, 815 checks, 4 workers

          FAIL SEAM-harness-x-verification.md:253
          FAIL SEAM-manifest-x-schools.md:271
          docs_verify: 2 failed

          $ diff <(failing doc:line BEFORE) <(failing doc:line AFTER)
          IDENTICAL -- no new failure, none resolved

      +1 document, +8 checks — exactly the 8 the new document declares
      (step 3 counted 8). The two failures are the same two, unchanged
      in identity and detail. Delta-clean.

- [x] 11. (S8, R10) Prove the 7b/7c fence held: this tranche touched no
      `src/` and no `tests/` path.
      done-when: `git diff --stat bb508414..HEAD -- src tests` is empty,
      and `git status --porcelain src tests` is empty. No pytest gate is
      owed — but the ~180 pytest checks embedded in the map DID run
      under step 10, which is the instrument that actually covers this
      change.

          $ git diff --stat 2cc3fd50..HEAD -- src tests
          (empty)
          $ git status --porcelain src tests
          (empty)

      Fence held across the WHOLE rung-7 tranche, not just 7a: the only
      paths touched since `2cc3fd50` are the two tranche directories and
      four `docs/map/` files.

- [x] 12. (S8) Confirm `adjudication x authority` appears in no
      `Seams-undocumented:` header anywhere in the map.
      done-when: `grep -rn "adjudication x authority" docs/map/` returns
      no hit inside a `Seams-undocumented:` line.

          docs/map/SEAM-adjudication-x-authority.md:7:# adjudication x authority

      The sole remaining hit is the new document's own title. No
      `Seams-undocumented:` header lists the pair anywhere.

- [x] 13. (S8) [COMMIT] Commit the map delta as ONE commit (`DR-SCHEMA`
      rule 1: the map moves with what it documents; here the document IS
      the change), push with retry, confirm clean tree.
      done-when: `git status --porcelain` empty AND the branch head is
      on `origin/claude/delivery-rungs-handover-m22sdy`.

      The map delta landed as ONE commit, `725dcab1` (the new document,
      the INDEX row, and both sides' headers together — `DR-SCHEMA`
      rule 1). Cleanliness proof pasted under VALIDATION.md V6.
