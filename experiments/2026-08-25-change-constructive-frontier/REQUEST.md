# REQUEST — redirect the research program to the constructive frontier

Captured 2026-08-25. Authority for this tranche is the operator's words,
reproduced verbatim below. Every later artifact cites requirement numbers
from this file. A requirement is never deleted, only marked
`superseded-by:<n>` or `deferred (operator approved <where>)`.

---

## A. The operator's words, verbatim

### A1 — the redirect (2026-08-25, quoted in the tranche instruction)

> change the research program a bit. I needs to solve a tough problem.
> Something that prompts the LLMs to have to be imaginative.

### A2 — the standing spend criterion, same exchange

> results must beat what one-shot prompting buys, measured, or the spend
> is not justified.

### A3 — the tranche instruction, verbatim

> Change tranche: redirect the research program to the constructive
> frontier — then run P-C1. Route setup through dr-change-orchestrator;
> judge the run on typed outcomes only.
>
> SETUP (fresh container): git fetch origin main && git checkout -B
> <your session-designated branch> origin/main; git merge-base
> --is-ancestor 43f408506 HEAD || re-fetch. pip install -e .
> --break-system-packages -q; pip install pytest pytest-xdist
> jsonschema --break-system-packages -q; deepreason embedder-warmup.
> Read CLAUDE.md in full; load dr-drive-harness, dr-explain-to-operator.
> THE OPERATOR SUPPLIES the OLLAMA_API_KEY env file at the launch step
> only.
>
> AUTHORITY for REQUEST.md, operator verbatim (2026-08-25): "change the
> research program a bit. I needs to solve a tough problem. Something
> that prompts the LLMs to have to be imaginative." Plus the standing
> spend criterion from the same exchange: results must beat what
> one-shot prompting buys, measured, or the spend is not justified.
>
> STEP 1 — PROGRAM v2: amend
> experiments/2026-08-25-poietics-program/PROGRAM.md — P-R2 and P-R3
> are CANCELLED by operator ruling (ledger the words); the program
> becomes the CONSTRUCTIVE FRONTIER series. Register the problem class:
> geometric construction on small open instances — circle packing
> (maximize minimum radius, N circles in the unit square) and Heilbronn
> (maximize minimum triangle area, N points). P-C1 uses ONE instance,
> chosen at spec time from N in 13..16, with the choice reasoned in
> SPEC.md (prefer the instance whose checker is simplest and whose
> search space is believed unsettled; no web access needed — the
> internal baseline below is the comparator, any published record the
> operator later supplies is a stretch line, not a gate).
>
> STEP 2 — THE CHECKER, the tranche's one piece of new code, and it is
> an EXPERIMENT script, not src/: a deterministic scorer (validity: all
> objects inside the square, no overlaps / distinctness; score: min
> radius or min triangle area, exact arithmetic where feasible, else
> declared fixed precision per the A10 discipline). It doubles as the
> demarcation battery: a candidate construction's commitment IS its
> claimed score, checked by program — demonstrative criticism, no judge
> anywhere. Mutation-prove the checker (a planted overlap and an
> inflated score claim must both FAIL; paste RED/GREEN).
>
> STEP 3 — P-C1 DESIGN, frozen in PREREG before any API call:
> - THE QUESTION: "Construct a configuration of N <objects> achieving
>   the largest score you can; every candidate must state its
>   coordinates and claimed score, and survives only if the checker
>   confirms it."
> - TWO ARMS, matched token budget, registered BEFORE launch:
>   ARM H (harness): solo run, everything on, conjecture-criticism over
>   candidates, checker-backed refutation of invalid or underperforming
>   claims, cycles sized deep (the imagination is in iteration).
>   ARM S (sampling baseline): the same model, the same total token
>   budget, blind repeated one-shot construction prompts, every reply
>   scored by the same checker, best kept. Driven by a plain script in
>   the experiment dir — no harness machinery.
> - REGISTERED PREDICTION, honestly: the ledgered external evidence
>   (RESEARCH_FINDINGS Q4) says sampling may WIN at matched budget; if
>   it does, that is the boundary measured on our own machine and is
>   recorded as a real result, not a failure. The harness claims value
>   ONLY on margin: best-H > best-S, sustained on the one
>   pre-authorized repeat.
> - MILESTONES: valid best-of-run score per arm; number of
>   checker-refuted claims (the harness's criticism doing countable
>   work); any construction PATTERN named by a surviving conjecture
>   that transfers across candidates (the imagination measure —
>   reported, not scored).
> - CONTROL-VS-CONTROL note: one repeat pre-authorized; arm comparison
>   quoted only with both runs' spread stated.
>
> STEP 4 — SOAK LAW: new config shape — extend scripts/cycle_soak.py's
> case table in the same commit, run it, paste exit 0. Then ask for the
> key.
>
> STEP 5 — LAUNCH both arms (H detached with snapshot loop; S is a
> script). JUDGE ON TYPED OUTCOMES + CHECKER OUTPUTS ONLY. Commit both
> records; RESULTS.md appends the honest ledger: both best scores, the
> margin, the refutation count, the residue. KNOWN ISSUE, report don't
> diagnose: survivor counts inflate with import-role records (parked
> P4) — quote conjecture-only figures. NO src/tests changes beyond the
> soak case line (git diff --stat proves it); defects parked. Commit
> and push every phase boundary (retry 2s/4s/8s/16s).

---

## B. Numbered requirements

Derived from A1–A3 without interpretation. Where A3 is silent, SPEC.md
records the assumption; it does not invent a requirement here.

| # | Requirement | Source |
|---|---|---|
| R1 | The research program is redirected to a TOUGH problem that forces the models to be imaginative. | A1 |
| R2 | Results must beat what one-shot prompting buys, MEASURED, or the spend is not justified. | A2 |
| R3 | Route the setup through `dr-change-orchestrator`. | A3 |
| R4 | Judge the run on TYPED OUTCOMES ONLY. | A3, STEP 5 |
| R5 | Amend `experiments/2026-08-25-poietics-program/PROGRAM.md` to v2. | A3, STEP 1 |
| R6 | P-R2 and P-R3 are CANCELLED by operator ruling; ledger the operator's words as the cancelling authority. | A3, STEP 1 |
| R7 | The program becomes the CONSTRUCTIVE FRONTIER series. | A3, STEP 1 |
| R8 | Register the problem class: geometric construction on small open instances — circle packing (max min radius, N circles in the unit square) and Heilbronn (max min triangle area, N points). | A3, STEP 1 |
| R9 | P-C1 uses ONE instance, chosen at spec time from N in 13..16, with the choice REASONED in SPEC.md. | A3, STEP 1 |
| R10 | Prefer the instance whose checker is simplest and whose search space is believed unsettled. | A3, STEP 1 |
| R11 | No web access needed; the internal baseline (ARM S) is the comparator. Any published record the operator later supplies is a STRETCH LINE, not a gate. | A3, STEP 1 |
| R12 | Write THE CHECKER: a deterministic scorer. It is the tranche's ONE piece of new code and it is an EXPERIMENT script, NOT `src/`. | A3, STEP 2 |
| R13 | Checker validity rules: all objects inside the square; no overlaps / distinctness. | A3, STEP 2 |
| R14 | Checker score: min radius or min triangle area; EXACT arithmetic where feasible, else declared fixed precision per the A10 discipline. | A3, STEP 2 |
| R15 | The checker doubles as the DEMARCATION BATTERY: a candidate's commitment IS its claimed score, checked by program. Demonstrative criticism, NO JUDGE ANYWHERE. | A3, STEP 2 |
| R16 | Mutation-prove the checker: a planted overlap and an inflated score claim must both FAIL. Paste RED/GREEN. | A3, STEP 2 |
| R17 | Freeze the P-C1 design in PREREG BEFORE any API call. | A3, STEP 3 |
| R18 | THE QUESTION follows the registered template: "Construct a configuration of N <objects> achieving the largest score you can; every candidate must state its coordinates and claimed score, and survives only if the checker confirms it." | A3, STEP 3 |
| R19 | TWO ARMS, matched token budget, registered BEFORE launch. | A3, STEP 3 |
| R20 | ARM H: solo run, everything on, conjecture-criticism over candidates, checker-backed refutation of invalid or underperforming claims, cycles sized DEEP. | A3, STEP 3 |
| R21 | ARM S: the same model, the same total token budget, BLIND repeated one-shot construction prompts, every reply scored by the same checker, best kept. A plain script in the experiment dir — NO harness machinery. | A3, STEP 3 |
| R22 | Register the honest prediction: sampling MAY WIN at matched budget (RESEARCH_FINDINGS Q4); if it does, that is a real recorded result, not a failure. | A3, STEP 3 |
| R23 | The harness claims value ONLY on margin: best-H > best-S, sustained on the one pre-authorized repeat. | A3, STEP 3 |
| R24 | MILESTONES: (a) valid best-of-run score per arm; (b) number of checker-refuted claims; (c) any construction PATTERN named by a surviving conjecture that transfers across candidates — reported, not scored. | A3, STEP 3 |
| R25 | CONTROL-VS-CONTROL: one repeat pre-authorized; arm comparison quoted only with both runs' spread stated. | A3, STEP 3 |
| R26 | SOAK LAW: new config shape → extend `scripts/cycle_soak.py`'s case table IN THE SAME COMMIT, run it, paste exit 0. | A3, STEP 4 |
| R27 | Ask the operator for the API key only AFTER the soak is green. | A3, STEP 4 |
| R28 | LAUNCH both arms: H detached with a snapshot loop; S is a script. | A3, STEP 5 |
| R29 | Commit both records. | A3, STEP 5 |
| R30 | RESULTS.md appends the honest ledger: both best scores, the margin, the refutation count, the residue. | A3, STEP 5 |
| R31 | KNOWN ISSUE — report, do not diagnose: survivor counts inflate with import-role records (parked P4). Quote CONJECTURE-ONLY figures. | A3, STEP 5 |
| R32 | NO `src/` or `tests/` changes beyond the soak case line; `git diff --stat` proves it. Defects are PARKED. | A3, STEP 5 |
| R33 | Commit and push at every phase boundary, with retry backoff 2s/4s/8s/16s. | A3, STEP 5 |

---

## C. Map preflight (CLAUDE.md, `dr-drive-harness` §4)

Resolved before designing, so every later phase starts from the same map.

| Map id | Why it is in scope |
|---|---|
| `DR-INV-frozen-surfaces` | Read FIRST. **Result: this tranche makes NO contact with any of the five frozen surfaces.** The only `src/`-adjacent edit authorised by R26 is one entry in `scripts/cycle_soak.py`'s `CASES` table, which is an instrument script, not a frozen surface, and R32 forbids everything else. |
| `DR-SEAM-evaluation-x-ontology` | Read BEFORE its subsystems, per the one ordering rule. Owns `programs.py` + `ontology/commitment.py` — the seam where a `Commitment`'s `predicate:` string becomes a machine verdict. R15 makes the checker a `predicate:` battery, so this seam is the one the design actually rests on. |
| `DR-SUB-evaluation` | Owns `programs.py`: `_validate_predicate`, `_SAFE_NAMES`, `evaluate`. Bounds what the in-run checker predicate may contain. |
| `DR-CON-run-identity` | Deterministic run ids, roots on disk, retiring and amending. Governs ARM H's root and the one pre-authorized repeat (R25). |
| `DR-SUB-manifest` | **Frozen.** Read-only use: `compile_run_manifest` / `bind_run_manifest` are CALLED by the ARM H builder, never modified. |
| `DR-CON-packs-and-token-economy` | Token budgets — R19's matched-budget requirement is defined against this. |
| `DR-CON-scheduler-ranking` | R20's "cycles sized deep"; the operator's seed question wins rank ties. |

**Binding constraints carried forward from the map into SPEC.md:**

1. `DR-SEAM-evaluation-x-ontology` Traps — **a malformed `predicate:` is a
   REFUTATION, not an error.** `evaluate` catches EVERY exception from
   `_validate_predicate` and `eval` and returns `fail` with the error in the
   trace. A typo in the checker predicate would therefore fail every
   artifact in the run, silently and with full confidence. This forces a
   pre-launch preflight over the criteria (R16's mutation proof, applied to
   the in-run battery, not only to the offline script).
2. `DR-SUB-evaluation` — the predicate sandbox: no underscore-prefixed name
   or attribute, no `**`, and only `_SAFE_NAMES`
   (`len any all min max abs sum str int float sorted re json`) plus
   `content` and `codec`. Notably **`range` and `enumerate` are NOT
   available**, which constrains how the scorer's triple loop is written.
3. `DR-CON-run-identity` — run identity is deterministic (same question +
   config → same id). R25's repeat therefore cannot reuse the question and
   config byte-for-byte in the same home without tripping
   `RUN_ALREADY_STARTED`.

No map document is missing for anything this tranche touches, so no map
document needs to be created here.

---

## D. Amendments

None yet. New operator messages are appended here VERBATIM as new numbered
requirements (or as `Rn-a supersedes Rn`) BEFORE being acted on, then
reconciled through `dr-spec-change`.
