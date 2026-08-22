# Goal: census every downstream consumption of an adjudication result and classify each site
Class: regression-risk

Observed: External research supplied 2026-08-22
(`docs/RESEARCH_SHAPE_CRITIQUE_2026-08-22.md` §2(A), operator-supplied
verbatim block) reports that holding judge, candidate pool, prompts and
budget fixed and varying ONLY the decision rule's position moves the same
judge from -10.0 EM below majority vote (unconstrained scalar ranking, n=30
frozen-rule split) to +16.7 EM above its unconstrained self
(evidence-locked non-compensatory gate). The note's directed audit: "the
moment anything downstream consumes the adjudication as a ranking, a
confidence, or a weighted score, you have rebuilt the version that scored
-10pp. Audit your pipeline for any point where a Dung result gets
scalarised."

DeepReason's adjudication is natively a PARTITION: `label0` returns three
strings and `final_labels` is "the only producer of `Status` values in the
codebase" (`docs/map/SUB-adjudication.md`, Entry points). Whether that
partition SURVIVES to the point of use is not established anywhere in the
committed record — it is currently a belief, not a checked statement.

Success criterion (machine-decidable):
    A committed CENSUS.md in this tranche directory enumerating every
    consumption site of adjudication output in `src/deepreason/`, where:

    (1) The producer set is closed by re-derivation, not by grep judgement.
        The two checks already committed in `docs/map/SUB-adjudication.md`
        that pin the producer boundary must exit 0:

        python -c "import pathlib; imp=sorted(str(p) for p in pathlib.Path('src').rglob('*.py') if 'from deepreason.adjudication' in p.read_text() and 'deepreason/adjudication/' not in str(p)); assert imp==['src/deepreason/harness.py','src/deepreason/invariants.py'], imp"
        [ "$(grep -rc 'self.state.status = ' src/deepreason/harness.py)" = 1 ]

        -> both exit 0 (only harness.py and invariants.py call the package;
           `Harness._adjudicate` is the sole writer of `state.status`), so
           the census's producer boundary is `state.status` + `state.att` +
           `state.conn` + `state.dep` and nothing else.

    (2) Every site in the census carries file:line, what is consumed, what
        it becomes downstream, and exactly one of the four classes
        {ATTENTION/SCHEDULE, RENDER, SELECTION-BY-SCORE, EVIDENCE/LABEL
        FEEDBACK}.

    (3) The census's own closure is checkable by a committed command whose
        output is reconciled line-by-line against the census table, with
        zero unexplained residue (no sampling, no silent cap).

    (4) Verdict per class recorded, with the EVIDENCE/LABEL FEEDBACK count
        stated explicitly (expected ZERO; any hit is the most severe
        finding available to this tranche).

    (5) git diff --stat origin/main touches no path under src/ or tests/.

In scope (read-only):
    - `src/deepreason/` — every consumer of `state.status`, grounded
      extension membership, accepted/refuted sets, wound counts
    - `docs/map/SUB-adjudication.md` + `CON-scheduler-ranking.md` +
      `INV-signal-contract.md` (the map preflight, read before grep)
    - `experiments/2026-08-22-audit-scalarization/` (the only writable path)

NOT in scope: fixing anything. This tranche is READ-ONLY on `src/` and
`tests/` by operator instruction. A SELECTION-BY-SCORE or FEEDBACK finding
becomes ONE parked ready-to-send prompt in PARKED.md, never a patch. The
nearest tempting neighbor is `rules/rank.py`/Pareto machinery: measures
that never touched adjudication are OUT — the census is about adjudication
OUTPUT only, and a scalar with no adjudication input is not this tranche's
business.

Budget: 0 changed lines under src/ or tests/, 1 tranche directory,
multiple commits at phase boundaries.
Stop conditions inherited from orchestrator: yes

## Map ids resolved (map preflight, per CLAUDE.md / dr-drive-harness §4)

Producer:
- `DR-SUB-adjudication` — `src/deepreason/adjudication/`; the entirety of
  status semantics; `final_labels` the only `Status` producer.

Seams read BEFORE the subsystems (the one ordering rule, INDEX.md):
- `DR-SEAM-adjudication-x-rules` — a rule's entire power over status is
  the right to put warrant/target/validity-node on an artifact, never a
  `Status` value itself.
- `DR-SEAM-adjudication-x-authority` — authority gates whether a warrant
  may be minted at all, upstream; adjudication never imports it.
- adjudication x harness — UNDOCUMENTED but load-bearing: `harness.py` is
  the only caller of `build_att`/`build_dep`/`toposort`, and
  `Harness._adjudicate` is the sole writer of `state.status`. The census's
  producer boundary sits exactly here.
- adjudication x verification — UNDOCUMENTED: `invariants.py` re-derives
  `dep` and reruns `toposort` independently.

Consumers named by the operator's directive, resolved to map ids:
- `DR-CON-scheduler-ranking` — `Scheduler._select_problem`; the
  operator-seed tie-break is the repo's model of a LAWFUL typed tie-break.
- `DR-SUB-scheduler` — budgets, capability dispatch, the `step()` sweep.
- `DR-SUB-application` — the results surface (best-candidate selection).
- `DR-INV-signal-contract` — allocation signals, interface-only since
  Rung 1b; the claim is to be verified FROM THE CONSUMER SIDE.
- `DR-SUB-verification`, `DR-SUB-bridge`, `DR-SUB-periphery` — render and
  report surfaces.

Frozen surfaces read before designing (`DR-INV-frozen-surfaces`): this
tranche designs nothing and changes nothing, so no frozen surface is
approached. Recorded because the map preflight requires the read, not
because a grant is sought.

## Map gap noted (a finding, not a blocker — dr-drive-harness §4.5)

`docs/map/INDEX.md`'s Subsystems table lists 15 documents.
`docs/map/` contains 18 `SUB-` files: `SUB-application.md`,
`SUB-amendment.md` and `SUB-periphery.md` exist but are absent from the
routing table. `SUB-application.md` covers the results surface the
operator's directive names explicitly, so the census reaches it by
filename rather than by routing. Parked, not fixed.
