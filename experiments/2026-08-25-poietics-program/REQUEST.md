# Request: the Poietics research program — setup and run P-R1, the explanation run
Captured: 2026-08-25 from the operator's session-opening task message,
plus two mid-turn file uploads (Amendments A1, A2 below).

## Map preflight (recorded here so every later phase starts from the same map)

Resolved from `docs/map/INDEX.md` before any design:

| id | why this tranche touches it |
|---|---|
| `DR-SUB-evidence` | attached dossiers, admitted blocks, byte-checked citations — the P-R1 dossier binding (task STEP 3 "DOSSIER") |
| `DR-CON-run-identity` | deterministic run ids, roots on disk, retiring and amending — governs relaunch and the one pre-authorized repeat (STEP 5) |
| `DR-SUB-scheduler` | cycles and budgets — the "cycles sized by the attempt-4 precedent (8+)" and the bounded budget (STEP 3 "CONFIGURATION") |
| `DR-SUB-manifest` | **FROZEN.** RunManifest schema, validators, qualification subjects. The soak case (STEP 4) READS the committed config; it must not restate or alter manifest shape. |
| `DR-CON-seats` | the two-call seat protocol named in STEP 3 as "now shipped" |
| `DR-SUB-llm` | provider profile (glm-5.2), route firewall, packs |

Frozen-surface check against `docs/map/INV-frozen-surfaces.md`, run BEFORE
design: this tranche's only planned source edit is an added row in
`scripts/cycle_soak.py`'s `CASES` table plus a new builder module under
`experiments/`. `scripts/` and `experiments/` are outside all five frozen
surfaces (`capabilities/state.py`, `harness.py`, `invariants.py` +
`verification/`, `run_manifest.py`, `qualification.py`) and outside the
frozen-adjacent `route_fingerprint` in `llm/firewall.py`. R11 below states
the operator's own diff bound, which is stricter still.

## Verbatim

Operator's session-opening task message, quoted whole:

> TARGET REPOSITORY: AHepi/DeepReason — verify before anything else;
> if this session is based elsewhere, ask the operator to attach it
> with push access and STOP until then.
>
> Evidence tranche: the Poietics research program — setup and run
> P-R1, the explanation run. Route the setup through
> dr-change-orchestrator; judge the run on typed outcomes only.
>
> SETUP (fresh container): git fetch origin main && git checkout -B
> <your session-designated branch> origin/main; git merge-base
> --is-ancestor 853bf705c HEAD || re-fetch. pip install -e .
> --break-system-packages -q; pip install pytest pytest-xdist
> jsonschema --break-system-packages -q; deepreason embedder-warmup.
> Read CLAUDE.md in full; load dr-drive-harness,
> dr-explain-to-operator. THE OPERATOR SUPPLIES two things:
> POIETICS_FULL_RECORD.zip now, and the OLLAMA_API_KEY env file at
> the launch step only.
>
> STEP 1 — COMMIT THE RECORD, curated: unpack the zip;
> experiments/2026-08-25-poietics-program/record/ receives VERBATIM:
> README.md, report/00, 12, 14, 15, and data/ (all JSON). The rest
> of the report/ and sources/ trees are NOT committed (the operator
> holds the full zip; note that in the tranche README with the
> zip's name). Provenance header per the repo's research-note
> convention: external material, author is the agent that did the
> work, narrative treated as claims and data/ as evidence — the
> record's own §14 caution, quoted.
>
> STEP 2 — THE PROGRAM DOCUMENT: PROGRAM.md registering all three
> runs (P-R1 explanation; P-R2 premises — the record's claims
> registered with demarcation criteria, the stated confound as
> ammunition; P-R3 succession trial between surviving rival
> mechanisms under the Rung 7 protocol). P-R2 and P-R3 are
> REGISTERED, not run here — one tranche, one run.
>
> STEP 3 — P-R1 DESIGN, frozen in PREREG before any API call:
> - QUESTION, verbatim: "Under what conditions does a test constrain
>   its subject rather than describe it? Account for the 3-of-26
>   result in the attached record and its distribution — compile.py
>   1/9 mutations lost under shown-to-fail-first installation, every
>   ordinarily-guarded module 4/4 to 6/7 — same author, same week,
>   same care."
> - DOSSIER: the six committed documents, bound as attached evidence
>   (the attempt-4 root proved this path live; quoted-evidence
>   citability applies — critics cite the bound dossier).
> - CONFIGURATION: solo, everything on (the operator's standing
>   law), glm-5.2 profile, the two-call seat protocol now shipped;
>   bounded budget stated in PREREG; cycles sized by the attempt-4
>   precedent (8+), since depth is what the record's question needs.
> - REGISTERED MILESTONES: which typed outcomes count — accepted
>   conjectures proposing a mechanism; criticism engaging the
>   dossier's own confound; the §14 corrections cited against any
>   conjecture leaning on a withdrawn number. Stochastic extras
>   named as such.
>
> STEP 4 — SOAK LAW: the P-R1 config is a NEW case — extend
> scripts/cycle_soak.py's case table in the same commit, run it,
> paste exit 0. Then ask for the key.
>
> STEP 5 — LAUNCH: detached, snapshot loop, monitor progress.jsonl +
> rc= lines. SUCCESS: typed terminal, verify_root clean, the
> registered milestones present — commit the root; RESULTS.md names
> what the run's accepted-and-surviving conjectures actually claim,
> with the honest residue ("accepted does not mean true" applies
> doubly to an explanation of someone else's evidence). An
> operational death: park for the soak's ledger and STOP — the
> bench missed it. One repeat pre-authorized. NO src/tests changes
> beyond the soak case line (git diff --stat proves it). Commit and
> push every phase boundary (retry 2s/4s/8s/16s).

## Requirements

R1 (process): "TARGET REPOSITORY: AHepi/DeepReason — verify before anything
else; if this session is based elsewhere, ask the operator to attach it with
push access and STOP until then."

R2 (process): "Route the setup through dr-change-orchestrator; judge the run
on typed outcomes only."

R3 (process): the SETUP block verbatim — "git fetch origin main && git
checkout -B <your session-designated branch> origin/main; git merge-base
--is-ancestor 853bf705c HEAD || re-fetch. pip install -e .
--break-system-packages -q; pip install pytest pytest-xdist jsonschema
--break-system-packages -q; deepreason embedder-warmup. Read CLAUDE.md in
full; load dr-drive-harness, dr-explain-to-operator."

R4 (process): "THE OPERATOR SUPPLIES two things: POIETICS_FULL_RECORD.zip
now, and the OLLAMA_API_KEY env file at the launch step only."

R5 (artifact): "unpack the zip; experiments/2026-08-25-poietics-program/record/
receives VERBATIM: README.md, report/00, 12, 14, 15, and data/ (all JSON)."

R6 (artifact): "The rest of the report/ and sources/ trees are NOT committed
(the operator holds the full zip; note that in the tranche README with the
zip's name)."

R7 (artifact): "Provenance header per the repo's research-note convention:
external material, author is the agent that did the work, narrative treated
as claims and data/ as evidence — the record's own §14 caution, quoted."

R8 (artifact): "PROGRAM.md registering all three runs (P-R1 explanation; P-R2
premises — the record's claims registered with demarcation criteria, the
stated confound as ammunition; P-R3 succession trial between surviving rival
mechanisms under the Rung 7 protocol)."

R9 (process): "P-R2 and P-R3 are REGISTERED, not run here — one tranche, one
run."

R10 (artifact): "P-R1 DESIGN, frozen in PREREG before any API call" — with the
four sub-obligations R10a–R10d below.

R10a (artifact): "QUESTION, verbatim: 'Under what conditions does a test
constrain its subject rather than describe it? Account for the 3-of-26 result
in the attached record and its distribution — compile.py 1/9 mutations lost
under shown-to-fail-first installation, every ordinarily-guarded module 4/4 to
6/7 — same author, same week, same care.'"

R10b (behavior): "DOSSIER: the six committed documents, bound as attached
evidence (the attempt-4 root proved this path live; quoted-evidence
citability applies — critics cite the bound dossier)."

R10c (behavior): "CONFIGURATION: solo, everything on (the operator's standing
law), glm-5.2 profile, the two-call seat protocol now shipped; bounded budget
stated in PREREG; cycles sized by the attempt-4 precedent (8+), since depth is
what the record's question needs."

R10d (artifact): "REGISTERED MILESTONES: which typed outcomes count — accepted
conjectures proposing a mechanism; criticism engaging the dossier's own
confound; the §14 corrections cited against any conjecture leaning on a
withdrawn number. Stochastic extras named as such."

R11 (behavior): "SOAK LAW: the P-R1 config is a NEW case — extend
scripts/cycle_soak.py's case table in the same commit, run it, paste exit 0.
Then ask for the key."

R12 (process): "LAUNCH: detached, snapshot loop, monitor progress.jsonl + rc=
lines."

R13 (process): "SUCCESS: typed terminal, verify_root clean, the registered
milestones present — commit the root; RESULTS.md names what the run's
accepted-and-surviving conjectures actually claim, with the honest residue
('accepted does not mean true' applies doubly to an explanation of someone
else's evidence)."

R14 (process): "An operational death: park for the soak's ledger and STOP —
the bench missed it. One repeat pre-authorized."

R15 (process): "NO src/tests changes beyond the soak case line (git diff
--stat proves it)."

R16 (process): "Commit and push every phase boundary (retry 2s/4s/8s/16s)."

## Standing constraints

C1: "judge the run on typed outcomes only" — R2, and CLAUDE.md's governing
rule that the typed record is the only admissible evidence.

C2: "one tranche, one run" — R9; the cross-routing rule in CLAUDE.md.

C3: "NO src/tests changes beyond the soak case line (git diff --stat proves
it)" — R15. Stricter than the frozen-surface law; it is a hard diff bound on
this tranche.

C4: "solo, everything on (the operator's standing law)" — R10c, invoking the
2026-08-09 standing law recorded in CLAUDE.md ("A solo run with everything on
should be an option").

C5: "frozen in PREREG before any API call" — R10; the pre-registration
discipline. No live call may precede the committed PREREG.

C6: "Then ask for the key" — R11; the key is requested only AFTER a green
soak, never before.

## Open questions (for dr-spec-change)

Q1: **The record has not been supplied.** R4 promises
`POIETICS_FULL_RECORD.zip`. Two files have arrived instead (Amendments A1,
A2), and neither is that bundle. R5, R7, R10b and R10d all name material
that exists only inside it (`report/00`, `report/12`, `report/14`,
`report/15`, `data/*.json`, and the record's own §14 caution to be quoted).
Blocking for STEP 1 and STEP 3; NOT blocking for REQUEST.md or the map
preflight.

Q2: Does the operator intend `treadle0.5.zip` (A1) as a substitute for the
record's `sources/method/` subtree, as an unrelated deliverable for a
different tranche, or as an accidental upload? R6 explicitly excludes
`sources/` from the commit, so on the request's own terms A1 is not
committable material for this tranche.

Q3: Does the operator intend `POIETICS_FINDINGS_REPORT.md` (A2) to be bound
into the P-R1 dossier? On the request's own terms it cannot be: R10b names
"the six committed documents", and A2 is a seventh document — a secondary
analysis OF the record, not part of it.

## Amendments

(append-only; later operator messages land here, each with its verbatim quote)

A1 — 2026-08-25, mid-turn file upload, verbatim:

> @"/root/.claude/uploads/b9b5b238-c8e9-5462-ba05-bacc82425d40/290201ff-treadle0.5.zip"

Contents inspected, not committed: `treadle0.5/` — 24 files, the treadle 0.5.0
method library (README, BUNDLE, FIELD_REPORTS, FORMAT, LEDGER_FORMAT, MODULES,
SETUP, four `checkers/*.py`, `selftest.py`, twelve `skills/*/SKILL.md`). This
is the method library the Poietics record cites as `sources/method/`, which R6
places OUTSIDE the commit set. See Q2.

A2 — 2026-08-25, mid-turn file upload, verbatim:

> @"/root/.claude/uploads/b9b5b238-c8e9-5462-ba05-bacc82425d40/11143328-POIETICS_FINDINGS_REPORT.md"

Contents inspected, not committed: "Findings Report — POIETICS_FULL_RECORD",
332 lines, an independent analyst's pass OVER the bundle. Its own header
states the bundle it analyses is `POIETICS_FULL_RECORD.zip` — "118 files after
extraction: README.md, report/ (16 sections), data/ (7 JSON extracts),
sources/ (docs, zoo, method library, instrument scripts)" — confirming that
the bundle R5 names is a distinct artifact that has not arrived. See Q3.

A3 — 2026-08-25, operator's answer to the judge-seat question, verbatim:

> My bad. Deepseek V4 Pro 0813 for conjecturer, Kimi K3 for critic, Qwen 3.5
> for judge one and GLM 5.2 for judge 3.

Question that drew it (asked because CLAUDE.md requires any design leaning on
LLM judges to consult the committed judge-audit evidence first): whether
"solo, everything on" in R10c included judge seats, given the judge-evidence
review tranche measured cross-family unanimous judges at 0-2.5% false
conviction of sound work but same-family pairing — which a solo glm-5.2 run
is — at 47-60%.

### R17 (behavior) supersedes R10c's "solo"

R10c said "solo, everything on (the operator's standing law)". A3 replaces
the solo posture with a CROSS-FAMILY ensemble. Verbatim seat assignments:

| seat | operator's words |
|---|---|
| conjecturer | "Deepseek V4 Pro 0813" |
| critic | "Kimi K3" |
| judge one | "Qwen 3.5" |
| judge 3 | "GLM 5.2" |

R10c's other clauses are NOT superseded and still bind: "everything on",
"the two-call seat protocol now shipped", "bounded budget stated in PREREG",
"cycles sized by the attempt-4 precedent (8+)".

`R10c: superseded-by:R17` for the "solo, glm-5.2 profile" clause only.

**Consequence recorded, not assumed:** this moves the run OUT of the
same-family regime the judge-audit evidence measured at 47-60% false
conviction and INTO the cross-family regime it measured at 0-2.5%. The
operator's "My bad." is read as accepting the evidence, not as conceding an
argument — the configuration change is the remedy.

## Open questions (second batch, from A3)

Q4: **"judge one" and "judge 3" name two judges and skip judge 2.** Either
the ensemble is three judges with the middle seat unnamed, or "judge 3" is a
slip for "judge 2" and the ensemble is two. The harness's measured
false-conviction floor (0-2.5%) was taken on a UNANIMOUS cross-family
ensemble, so the size of the ensemble is load-bearing, not cosmetic.

Q5: **Eight of the eleven canonical roles are unassigned.** A3 names
conjecturer, critic and the judge seats. `defender`, `variator`,
`summarizer`, `synthesizer`, `vision_critic`, `property_designer`, `thesis`
and `grounding_reviewer` still need routes, since `Config.roles` defaults to
`{}` and any omitted role gets zero routes.

Q6: **The four model identifiers must resolve to exact Ollama Cloud ids**
before the config can compile to a reachable run. Compile no longer refuses
an unreachable model (operator law 2026-08-12, "All configurations should be
allowed"), so a wrong id fails at the point of use, mid-run, not at setup.
