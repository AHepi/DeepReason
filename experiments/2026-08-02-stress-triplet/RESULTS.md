# Stress triplet — 2026-08-02, honest ledger

Three concurrent live runs, glm-5.2 thinking-off, fresh homes, operator's new
key. What the record shows, then the residue. Accepted does not mean true.

## Typed outcomes (the only admissible evidence)

| run | root | state | rc | replay |
|---|---|---|---|---|
| triage | run-0a3e93d6 | completed, 692s | **5** | **1 violation: attached-evidence** |
| orbit | run-6472629d | completed, 585s | 0 | clean |
| workshop | run-1a0d4168 | completed, 727s | 0 | clean |

Qualification: four full batteries across the triplet (two workshop attempts),
199–337s each, concurrent, zero 429s on the new key.

## What moved, per requirement

- **parser**: three thinking-off runs end-to-end; four batteries tier=full;
  workshop and orbit terminally clean.
- **cross-school criticism**: LIVE. triage: 47 Crit events, critic artifacts
  from all four schools (12/10/13/11 + 2 unschooled), author school excluded
  by construction. workshop: 45 Crit events. Authority observe_only
  (engaged_criticism_policy hard-codes it), so no argumentative warrants —
  by design, recorded, the defended-trial flip stays an operator decision.
- **scratchpad**: LIVE in triage (10 blocks, 2 links, 9 attention receipts)
  and workshop (3 blocks, 3 links, 8 receipts) — the scratch.link contract
  from the schema sweep exercised in production.
- **adjudication**: one LIVE attack edge in triage — DEMONSTRATIVE
  relation-form warrant → REFUTED. The warrants→att→REFUTED chain moves in
  production, against a 26/42 historically-blind baseline.
- **simulation**: channel present (inquiry-capabilities.v2 on all manifests),
  ZERO proposals filed. Stochastic channel, one attempt, inconclusive for the
  path. The offline regression remains the proof.
- **coding oracles**: NOT exercised — `deepreason reason` compiles no
  exec-oracle commitments from question text alone. A run-shape limit
  discovered, not a defect.

## Live catches (defect-tranche candidates, none fixed here)

1. **attached-evidence integrity violation** (triage): bound source
   src-56d86e9b lacks its reliability-dependent candidate evidence artifact.
   Caught independently by BOTH instruments: exit contract rc=5
   (application/models.py:1269, integrity_valid False) and verify_root.
2. **jolt-lineage audit probe-rule violation**: verify_root returns
   {stats, violations} — no `valid` key — so every jolt-descended ladder
   audit has printed `replay_valid: null` since written. Validity is
   `violations == []`. Second probe-rule catch: v6 scratch activity rides
   object records, not `scratch*` log measures; an audit counting the old
   instrument reports zero against a root full of scratch objects.
3. Two ladder config errors caught at the fence by typed refusals in 1s
   each, before any spend: REASONING_MUST_BE_DISABLED (unset ≠ off) and
   QUALIFICATION_NOT_CONFIGURED (qualify/reason opt-in mismatch).

## The operator deliverable

TRIAGE_ANSWER.md: eight surviving conjectures from the test-gap triage
question. Headline: the run independently reduced the parked census delta to
"verify_root_report routes three pre-v6 roots to a verdict path instead of an
error path" with its refutation condition stated — a testable diagnosis of a
defect its own harness carries.

## Residue

- No skeleton parsed in workshop (0 forbidden-case commitments): the model
  never emitted parse_skeleton-conformant text. Question-shaping, not harness.
- Simulation path unproven live this attempt.
- rc=5 root is committed evidence of the attached-evidence defect; it stays
  as-is (never edit a committed root).
- 42-root prior-baseline sweep running at close; result appended when done.
