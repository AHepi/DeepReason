# Delivery — record claims: pre-registered universal statements tested against a run's record

Branch `claude/record-claims-tool-evul4v`. Validation verdict PASS.
Full gate **5147 passed, 6 skipped, 0 failed** (19:19).
`src/deepreason/` byte-untouched; no frozen surface touched; PREREG.md unedited.

## What shipped

| file | lines | what it is |
|---|---|---|
| `tools/record_claims.py` | 831 | the instrument: reads run roots and a claims file, prints each claim's status, its refuting record ids (at most five) and its standing |
| `docs/CLAIMS_SCHEMA.md` | 269 | the claims file's contract |
| `tests/test_record_claims.py` | 877 | 41 tests; every refutation mutation-proven |
| `experiments/2026-09-06-change-writers-room-organiser-testing/claims.json` | 228 | nine claims re-stating that tranche's sealed PREREG predictions |
| `docs/map/INV-frozen-surfaces.md` | +51 | the instrument section, with two checks, one of which runs the tool on a committed root |

## What the instrument says about the FAILED ARM R root

Run against
`experiments/2026-09-06-change-writers-room-organiser-testing/runs/home-r/runs/run-36d9a22c3e2045ae1b8c7bfb9d95d092`
(run id `0d7f0861…`, `state: failed`, `stop_reason: operational_failure`,
cycle 3, 464 359 of 500 000 tokens):

| claim | status | standing |
|---|---|---|
| `ORG-CITE-01` the organiser never cites an id outside the legend | REFUTED | SHOWN_ABLE_TO_FAIL |
| `ORG-PLAN-01` every conjecturer section plan names the organiser's contract | UNREFUTED_FOR_DECLARED_SCOPE | NOT_SHOWN_ABLE_TO_FAIL |
| `ORG-PLAN-02` never names the ordinary conjecturer contract | UNREFUTED_FOR_DECLARED_SCOPE | NOT_SHOWN_ABLE_TO_FAIL |
| `RUN-STOP-01` a run never stops `operational_failure` | REFUTED | SHOWN_ABLE_TO_FAIL |
| `CRIT-CAP-01` the critic never exhausts its smallest contract | UNREFUTED_FOR_DECLARED_SCOPE | NOT_SHOWN_ABLE_TO_FAIL |
| `ORG-COND-01` a candidate never registers a citation that fails its check | REFUTED | SHOWN_ABLE_TO_FAIL |
| `RUN-TERM-01` a run reaches a completed terminal | REFUTED | SHOWN_ABLE_TO_FAIL |
| `EVID-EXPOSED-01` never cites a block admitted but withheld from the legend | UNREFUTED_FOR_DECLARED_SCOPE | NOT_SHOWN_ABLE_TO_FAIL |
| `ARMH-STOP-01` the harness-alone arm never stops `operational_failure` | NOT_TESTED | SHOWN_ABLE_TO_FAIL |

Four refutations, each naming its counterexample: `RUN-STOP-01` points at
`run-status.json:stop_reason='operational_failure'`; `ORG-CITE-01` at
`log.jsonl:seq=42`, the first of 58 `EVIDENCE_REF_UNKNOWN_BLOCK` measures;
`ORG-COND-01` at `seq=41`; `RUN-TERM-01` at the absence of a completed state.

**Two of the four survivals are the reason the standing exists**, and they are
the interesting result of running this at all:

- `CRIT-CAP-01` survives because the seat that terminally exhausted its
  smallest authorized contract was the CONJECTURER, not the critic. The root
  does carry a `workflow-route-seat-insufficient-capability-v1` record —
  `route_lease.role: conjecturer`, `contract_id:
  conjecturer.atomic-candidate.v1`, `reason:
  smallest_authorized_contract_schema_exhausted`. The claim is about the
  critic and no supplied record could have refuted it.
- `EVID-EXPOSED-01` survives because `EVIDENCE_REF_NOT_EXPOSED` appears
  NOWHERE in the record, though PREREG §8 predicted in as many words that at
  least one would ("the seat reads 94 blocks and can cite 32"). The
  prediction did not come true, and a reader who saw only the survival would
  have read the opposite.

Neither is a test the harness passed. The report says so in its own words:
*the refuting condition held on no supplied root, in or out of scope; this
check has not been shown able to fail, and the survival should be read
accordingly.*

## Requirement-by-requirement reconciliation

| R | what it asked | where it landed | evidence |
|---|---|---|---|
| R1 | clone h-EPI read-only beside this one, record its head, never modify or vendor | `/home/user/h-epi`, head `f97239fc38f52b664fb56ad518a8ac60ac959482` | VALIDATION S1: `git status --porcelain` empty; `grep -rn creib` finds prose and one negative-test string, no code |
| R2 | read the five named files | SPEC.md's "What the record actually carries" and "The shape adopted" | SPEC M1-M10 and the shape section, each tracing to what was read |
| R3 | take the SHAPE, not the code | never/always, declared scope, one record refutes, `UNREFUTED_FOR_DECLARED_SCOPE`, standing | `tools/record_claims.py`; no import, no copied line |
| R4 | a read-only tool over run roots and the typed measures | `tools/record_claims.py` | VALIDATION S2, S12 |
| R5 | print status, refuting record ids (≤5), standing | the text and JSON reports | VALIDATION S3; `test_refuting_record_ids_are_capped_at_five_and_the_rest_are_counted` |
| R6 | `docs/CLAIMS_SCHEMA.md` | 269 lines | VALIDATION S6 |
| R7 | a first claims file re-stating the PREREG predictions, the five named among them | 9 claims | VALIDATION S7; the five names map to `ORG-CITE-01`, `ORG-PLAN-01`, `RUN-STOP-01`, `CRIT-CAP-01`, `ORG-COND-01` |
| R8 | run it against the FAILED root so the output shows real refutations | four refutations | VALIDATION S9; the table above |
| R9 | conditions over the record's own typed fields | six primitives: status fields, event rules, measure codes, control actions, object kinds and paths | VALIDATION S4; SPEC M1-M8 measured each |
| R10 | read and cite `DR-SUB-harness`, `DR-CON-evidence-states`, `DR-INV-evidence-channels` | cited in SPEC.md's header and in `docs/CLAIMS_SCHEMA.md`'s closing section | both documents |
| R11 | "not shown able to fail" is REQUIRED | `NOT_SHOWN_ABLE_TO_FAIL` plus the sentence | VALIDATION S5; four claims print it on the real record |
| R12 | tests: refutes each kind, one survives, one where the standing fires | `tests/test_record_claims.py`, 41 tests | VALIDATION S10 |
| R13 | no claim about correctness of any answer | every claim reads a status field, a measure code, an object field or a section plan | the nine statements; none mentions an answer |
| R14 | not a gate, not a status, not a score; writes nothing into any root | exit 0 with everything refuted; `_refuse_inside_a_root`; no harness import | VALIDATION S2, S12; `test_the_cli_exits_zero_even_when_every_claim_is_refuted` |
| R15 | not h-EPI's appraisal layer; only its labelling rule is of interest | not built | `PARKED.md` P1; `REFUTED_ON_CONTESTED_READING` deliberately not adopted (SPEC, "The shape adopted") |
| R16 | park it with a prompt pointing the UNDECIDED-premise fork at `appraisal.py`, first line saying readiness is read from the record | `PARKED.md` P1 | VALIDATION S13; the prompt is one fenced block, repeated inline in the delivery message |
| R17 | not a change to any sealed PREREG | PREREG.md untouched; the claims file's own title says it does not amend it | VALIDATION S14 |
| R18 | `src/deepreason/` byte-untouched | empty diff | VALIDATION S14 |
| R19 | no frozen surface; say so after checking `INV-frozen-surfaces.md` | none of the five; `blast_radius.py` verdict `CLEAR`, both contact lists `[]` | SPEC "Frozen-surface contact forecast"; VALIDATION's empty frozen diff |
| R20 | park, never fix, anything found | three parks, no fixes | `PARKED.md` P1, P2, P3 |
| R21 | add the tool to the map document owning `tools/` instruments, with a `check:` that runs it on a committed root and exits 0, in the same commit | `docs/map/INV-frozen-surfaces.md`, the fourth instrument section | VALIDATION "Map validation"; mutation-proven falsifiable |
| R22 | ring while iterating; the full gate ONCE at the boundary | ring at steps 8-9, gate at step 18 | 60 passed on the ring; 5147 passed, 0 failed at the gate |
| R23 | deliver through validate then deliver, with the R-by-R table | `VALIDATION.md` verdict PASS; this table | both files |
| R24 | commit and push at every phase boundary with retry | eight pushes, all first-attempt | `git log --oneline origin/main..HEAD` |
| R25 | no human-readiness step anywhere | none built | `test_the_tranche_claims_file_carries_no_readiness_field`; the schema has no such field and the map section states the rule |

Nothing deferred. Every R has a demonstration.

## Two deviations, both recorded where they happened

1. **SPEC S2's wording contradicted SPEC S3.** S2 said the tool "opens no file
   for writing anywhere" while S3 specified `--markdown <out>` in the same
   document. Corrected in SPEC.md with a dated CORRECTION paragraph naming the
   contradiction rather than a silent rewrite. The obligation R14 actually
   states — nothing written INTO A ROOT — is enforced by
   `_refuse_inside_a_root` and proven twice over.
2. **The budget was EXCEEDED.** SPEC estimated ~1 100 lines; the delivered
   work is 2 256, with ZERO deletions in `git diff --numstat`, so it is size
   and not churn. Two items account for almost all of it: the fail-closed
   validation and its error messages in the tool (R9), and one mutation proof
   per refutation in the tests (S10's own requirement). Amended to 2 300 in
   SPEC.md with the arithmetic, and reported here rather than absorbed.

## Residue — what this does not do

- **One root, nine claims.** Every survival above is a survival for exactly
  one record. The standing says which of them the records could not have
  refuted; it says nothing about the next root.
- **`ORG-COND-01` is a declared proxy.** The record types no countercondition
  and no proposal provenance (`PARKED.md` P2). The claim can be refuted; it
  cannot be confirmed.
- **The claims file re-states predictions; it does not seal them.** PREREG.md
  remains the authority for what was predicted before the launch. A claim
  written after the record is read is not a pre-registration, and this file's
  value rests entirely on those predictions having been sealed first.
- **No appraisal.** When a refutation rests on a reading that is itself under
  criticism, this instrument has nothing to say. That is `PARKED.md` P1, and
  it is parked as HALF a mechanism on purpose.
