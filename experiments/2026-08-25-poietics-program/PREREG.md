# PREREG — P-R1, the explanation run

**Frozen before any provider call** (REQUEST.md C5). Everything below was
settled offline against the compiler, the live model catalogue and a
discrimination control; the only step this document does not cover is the
launch itself, which waits on the operator's credential file (R4: the key
arrives at the launch step only, and R11: not before a green soak).

Map ids: `DR-SUB-evidence`, `DR-CON-run-identity`, `DR-SUB-scheduler`,
`DR-SUB-manifest` (FROZEN, read not touched), `DR-CON-seats`, `DR-SUB-llm`.

## 1. The question (R10a, verbatim)

> Under what conditions does a test constrain its subject rather than
> describe it? Account for the 3-of-26 result in the attached record and its
> distribution — compile.py 1/9 mutations lost under shown-to-fail-first
> installation, every ordinarily-guarded module 4/4 to 6/7 — same author,
> same week, same care.

Frozen as `build_manifest_pr1.py::QUESTION`. Run identity is deterministic
in this question and this configuration, so one byte of drift mints a
different root and a different dossier `problem_ref`.

Derived and frozen: `problem_id = question-aa835741bebc4b4cb189f4b08bef649a`.

## 2. The dossier (R10b)

All twelve committed files under `record/`, admitted through
`admission.attach.admit_attachment_paths` — the one shared admission path
every end-user surface uses — and bound AT SEED rather than at an amendment.

Measured, not assumed:

    sources admitted   12
    blocks             623   (section 119, paragraph 496, table 8)
    tiers              evidence 623
    refusals           none  (no --allow-partial needed)
    dossier digest     5e04e375de86528f5ee343c88f566f54ee4f94e90e0e6e6a18519109f3acb327

Blocks are the point, not a side effect: quoted-evidence citability means a
critic cites a BLOCK and `evidence.citations.check_candidate_citations`
byte-checks the quotation against it. A dossier bound as twelve opaque files
would give critics nothing citable.

Source ids are derived from content, so they are stable across rebuilds. The
four that milestones below name:

| source id | file |
|---|---|
| `src-a0a64514712b0c27859f1da10c66db2201d86b59` | `README.md` |
| `src-550763b627cd359492773e94cfd58e7976e3bc81` | `report/00_EXECUTIVE_SUMMARY.md` |
| `src-ab642b0f57bb5c1012438da340025e37387ba608` | `report/12_MUTATION_TESTING.md` |
| `src-557948f391fc1194569555e2bf71a72ecaaa034f` | `report/14_CORRECTIONS_AND_WITHDRAWN_CLAIMS.md` |

**Declared deviation D1.** R10b says "the six committed documents". The
committed set is twelve FILES forming six DOCUMENTS — `README.md`, four
`report/` sections, and `data/` as one seven-file evidence bundle. All
twelve are bound as separate sources, which is inside the policy's
`maximum_sources=16` and gives each file its own citable identity. Binding
`data/` as one concatenated source would have exceeded
`maximum_excerpt_bytes_per_source` and destroyed per-file citability.

## 3. The configuration (R10c as amended by R17)

Cross-family, everything on. Every model id below was checked against the
LIVE catalogue at `https://ollama.com/v1/models`, which answers
unauthenticated; all four are in its nineteen. This check was worth running
because compile no longer refuses an unreachable model (operator law
2026-08-12) — a wrong id would first surface mid-run.

| seat | model | family |
|---|---|---|
| conjecturer | `deepseek-v4-pro:0813` | deepseek |
| argumentative_critic | `kimi-k3` | kimi |
| judge seat 1 | `qwen3.5:397b` | qwen |
| judge seat 2 | `glm-5.2` | glm |
| defender, variator, summarizer, synthesizer, vision_critic, property_designer, thesis, grounding_reviewer | `glm-5.2` | glm |

"Everything on", written out because several of these ship the other way:
`JUDGE_SEATS_ENABLED`, `ADJUDICATION_STATUS_AUTHORITY_ENABLED`,
`SCHOOL_SEATS_ENABLED` true; `ENGAGED_CRITICISM_AUTHORITY: defended_trial`;
`LEGACY_CRITICISM_ENABLED` false so the engaged engine actually runs;
`RESEARCH_BACKEND: agent`; inquiry policy engaged with attached evidence,
simulation, research and config referee all enabled.

Compiled manifest, measured: `manifest_sha256
1b31f0065687bd24f64bb08acae1245446b4b31c31b90b141ff95cd5759c9a97`,
`rubric_policy require_cross_family`, **zero compile notices**.

**Budget: 12 cycles, 3 000 000 tokens.** Sized so the CYCLE budget binds
first, as it did in the attempt-4 precedent — a token-bound stop truncates
mid-cycle, a cycle-bound stop does not. attempt-4 spent 371 169 tokens over
8 cycles solo with no dossier and no judges; P-R1 adds dossier packs, a
judge ensemble and school seats, so per-cycle cost is expected several times
higher. 8 is R10c's floor; 12 is the depth the question needs.

**Declared deviation D2 — the judge ensemble is TWO seats.** A3 named "judge
one" and "judge 3" and skipped judge 2. Two seats is the smallest reading
that compiles, and it satisfies the gate exactly:
`firewall.py::require_cross_family_judge_ensemble` requires ≥2 seats AND ≥2
families. A third seat would need a model the operator did not name.

**Declared deviation D3 — seven roles were not named and stay on
`glm-5.2`.** `Config.roles` defaults to `{}`, so silence would give them
zero routes. This is the profile R10c originally named.

**Recorded consequence of R17, not a claim of merit.** The judge-audit
evidence in this repository (`experiments/2026-08-09-change-judge-evidence-
review/`) measured cross-family unanimous judges at 0-2.5% false conviction
of sound work, and same-family pairing at 47-60%. R17's ensemble is
cross-family, so P-R1 sits in the measured-low regime. That is a reason the
acceptance set should be READABLE; it is not evidence that any particular
verdict is right. The same review scored the CRITIC's raw objection stage as
genuinely content-blind — objecting to ~100% of everything shown to it —
and nothing in R17 changes that.

## 4. The criteria, and what they can and cannot do

Three `predicate:` commitments over the artifact's own bytes, frozen in
`build_manifest_pr1.py::CRITERIA`:

- `poietics-constraint-condition@v1` — a conditional claim plus at least two
  constrain/describe terms.
- `poietics-installation-mechanism@v1` — at least two installation terms
  plus a term from the record's actual distribution.
- `poietics-confound@v1` — at least two of the record's own stated limits.

**Control 1 — discrimination. HOLDS**, measured by
`preflight_criteria.py`: an off-subject text about urban heat islands passes
**0 of 3**; an on-subject text passes **3 of 3**. The battery discriminates
on subject, not on form.

**Control 2 — dossier leakage. REPORTED, NOT ENFORCED, and it is the
weakest point in this design.** Each committed file was evaluated alone.
Three pass all three criteria: `data/extracted_episodes.json`,
`report/00_EXECUTIVE_SUMMARY.md`, `report/15_INSIGHTS.md`. So an artifact
could clear the whole battery by quoting one of those files.

This is stated rather than designed away because a term predicate cannot
tell a quotation from an account, and narrowing the criteria until the
record failed them would produce criteria the right answer also fails. The
consequence for reading the run: **criteria PASS is a floor, not a
milestone.** No milestone in §5 is satisfied by criteria alone.

## 5. Registered milestones (R10d)

Typed outcomes only (C1). Each names the artifact and field that decides it.
Registered BEFORE launch; nothing here may be renegotiated afterwards.

### M1 — accepted conjectures proposing a mechanism  [REQUIRED]

`deepreason results <root>` reports a non-zero accepted count and a non-zero
survivor count, AND at least one accepted-and-surviving artifact whose
program evaluation records `poietics-installation-mechanism@v1` = PASS in
the run's own log.

*Decided by:* the `results` surface plus the typed program-evaluation
verdicts in `log.jsonl`. Not by reading the prose.

### M2 — criticism engaging the dossier's own confound  [REQUIRED]

At least one criticism artifact in the record that (a) is addressed to a
conjecture and (b) carries a citation whose `check_candidate_citations`
receipt resolves to a block of a `record/` source.

*Decided by:* citation receipts in `log.jsonl` naming a `src-` id from §2.
A criticism that merely contains confound vocabulary does NOT satisfy M2 —
the citation must byte-check.

### M3 — the §14 corrections cited against a withdrawn number  [REQUIRED IF TRIGGERED]

If any conjecture in the run leans on a withdrawn figure — "6/6 held", "59
caught", "3 survived" — then at least one criticism cites a block of
`src-557948f391fc1194569555e2bf71a72ecaaa034f` (`report/14`) against it.

*Decided by:* a text scan of accepted conjectures for the withdrawn figures,
then citation receipts naming that source id.

**Registered honestly: M3 is CONDITIONAL, and its trigger may never fire.**
If no conjecture leans on a withdrawn number, M3 is NOT MET and NOT FAILED —
it is UNTRIGGERED, and the run is not judged worse for it. Recording this
now so an untriggered M3 cannot later be read either as a pass or as a
failure.

### Stochastic extras — named as such, and none of them is a success condition

Capability-channel use is stochastic across identical runs (CLAUDE.md): one
live attempt that misses a path is inconclusive for that path. Registered as
NICE-IF-PRESENT only:

- a typed simulation proposal reaching a SUCCEEDED event;
- a typed research proposal admitted through the research controller;
- a defended trial reaching a judge verdict rather than declining;
- any `reach_set` event;
- a succession trial of any kind — which, per the Rung 7 tranche's own
  PARKED.md, has never happened live.

**None of these five may be cited as evidence that P-R1 succeeded, and their
absence may not be cited as evidence that it failed.**

## 6. Success, and the two failure shapes

**SUCCESS (R13):** a typed terminal; `verify_root` with 0 violations; M1 and
M2 both met; M3 met or untriggered. Then the root is committed and RESULTS.md
names what the accepted-and-surviving conjectures actually claim, with the
residue.

**TYPED FAILURE:** the run reaches a terminal but M1 or M2 is unmet. This is
a recorded negative result, written up as one. Not retried.

**OPERATIONAL DEATH (R14):** the run dies before a typed terminal. The cause
is PARKED for the soak's ledger and the tranche STOPS — the bench missed it,
and that is a finding about the bench. One repeat is pre-authorized.

## 7. What this run cannot establish, registered in advance

P-R1 produces accepted-and-surviving conjectures. Acceptance is a STATUS
inside this harness — it means a conjecture survived the criticism this run
happened to generate, from one critic seat, under one judge ensemble, in
twelve cycles. It is not a fact about guards in the Poietics repository, and
it is not a replication: the bundle carries no engine tree and no test tree,
so no CAUGHT/SURVIVED verdict in it is re-executable from these bytes.

"Accepted does not mean true" applies doubly to an explanation of someone
else's evidence, and RESULTS.md is required to say so in its own words.
