# Spec for: adopt h-EPI's claims mechanism for DeepReason's measures
Traces: every item cites R/C numbers from REQUEST.md. Untraceable items are bugs.

Map ids resolved at preflight (CLAUDE.md map-preflight rule):
`DR-INDEX`, `DR-INV-frozen-surfaces` (read FIRST, before design),
`DR-SUB-harness` (the append-only log and what an event carries),
`DR-CON-evidence-states` (survivor vs untested, and the declaration that says
whether a criticism pass ran), `DR-INV-evidence-channels` (the three
evidence-minting channels), `DR-SUB-evidence` (admitted dossiers and
byte-checked citations), `DR-INV-reference-menu` (legal handle sets),
`DR-SUB-verification` (`verify_root`), `DR-SCHEMA` (how a map check is
written and why a check that cannot fail is worse than none). R10 asked for
`DR-SUB-harness`, `DR-CON-evidence-states` and `DR-INV-evidence-channels` by
name; the other five were reached from `DR-INDEX`'s routing table and are
cited where they carry a decision below.

The read-only clone of the operator's repository is at `/home/user/h-epi`,
head `f97239fc38f52b664fb56ad518a8ac60ac959482` (R1). Nothing in this tranche
copies its code (R3); the SHAPE below is stated in DeepReason's own terms.

---

## What the record actually carries (measured, not recalled)

Every design decision below rests on a census of the FAILED ARM R root
`experiments/2026-09-06-change-writers-room-organiser-testing/runs/home-r/runs/run-36d9a22c3e2045ae1b8c7bfb9d95d092`
(R8; the tree was read — the re-launch window has not renamed it).

M1 — `log.jsonl`, 976 events, one JSON object per line, each carrying `seq`,
`ts`, `rule`, `inputs`, `outputs`, `llm`, `state_diff`. Rule census:
`Measure` 466, `Control` 314, `Spawn` 76, `Register` 71, `Crit` 33, `Refl` 8,
`Conj` 8. (`DR-SUB-harness` owns this shape.)

M2 — a `Measure` event names its measure code in `inputs[0]`. Census of the
466: `reach-provisional` 123, `discharge-undischarged` 104,
`evidence-citation:EVIDENCE_REF_UNKNOWN_BLOCK` 58,
`v6-model-phase-deferred.v1` 37, `scrutiny` 32,
`evidence-citation:EVIDENCE_CITATION_VERIFIED` 21, `criticism.dispatch.v1` 8,
`evidence-citation:EVIDENCE_QUOTE_MISMATCH` 7, `discharge-reask` 6,
`allocation.seat-truncation.v1` 6, `allocation.seat-repair.v1` 6, and 20
further codes at 4 or fewer.

M3 — a `Control` event carries `control.schema` `control.event.v3` and
`control.action`. Census of the 314: `work_transition` 244,
`provider_result` 64, `contract_decomposition_activated` 2,
`classification_bound` 1, `contract_decomposition_completed` 1,
`lifecycle_stopped` 1, `terminal_committed` 1.

M4 — `objects/` is one directory per record kind, each holding
`<sha256>.json` with `{"data": ..., "id": ..., "schema": ...}`. 25 kinds
present; the load-bearing ones here are
`workflow-work-lifecycle-transition-v1` 308, `workflow-context-pack-plan-v1`
86, `problem` 76, `artifact` 76, `workflow-provider-attempt-v1` 64,
`workflow-context-section-plan-v1` 15,
`workflow-route-seat-insufficient-capability-v1` 1.

M5 — `run-status.json` carries the typed terminal:
`state: failed`, `stop_reason: operational_failure`, `cycle: 3`,
`token_spend: 464359`, `token_limit: 500000`, and the message
`V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY at
/workflow/insufficient_capability_by_route_seat: route seat has terminally
exhausted its smallest authorized contract`.

M6 — the one `workflow-route-seat-insufficient-capability-v1` object carries
`route_lease.role: conjecturer`, `reason:
smallest_authorized_contract_schema_exhausted`, `contract_id:
conjecturer.atomic-candidate.v1`. **The seat that exhausted its smallest
contract was the conjecturer, not the critic.** This is the fact that makes
the required "not shown able to fail" standing (R11) fire on a real record
rather than on a fixture.

M7 — all 15 `workflow-context-section-plan-v1` objects carry `layout_id:
seat-pack.conjecturer.organiser-v1`, and all 15 name `dr.output-contract.organiser`
as a rendered section. None names `dr.output-contract.conjecturer`. This is
PREREG.md §8's own operational prediction, and it held.

M8 — the citation measure is emitted at `src/deepreason/rules/conj.py:2468`
with `inputs = [ "evidence-citation:<code>", block_id-or-ref, artifact.id,
problem_id ]`, inside the CONJECTURER rule. So a citation check is
attributable to the conjecturer (here, organiser) seat by the site that
records it, without the tool having to infer a seat. `DR-SUB-evidence` owns
the eight codes (`src/deepreason/evidence/citations.py:24-31`):
`EVIDENCE_CITATION_VERIFIED`, `EVIDENCE_REFS_UNBOUND`,
`EVIDENCE_REF_UNKNOWN_BLOCK`, `EVIDENCE_REF_AMBIGUOUS`,
`EVIDENCE_REF_TIER_INELIGIBLE`, `EVIDENCE_QUOTE_MISMATCH`,
`EVIDENCE_BLOCK_UNRECOVERABLE`, `EVIDENCE_REF_NOT_EXPOSED`.

M9 — **`EVIDENCE_REF_NOT_EXPOSED` appears NOWHERE in this record.** PREREG.md
§8 predicted it would ("≥ 1 `EVIDENCE_REF_NOT_EXPOSED` measure appears in the
record"). A claim written on it therefore survives for a reason the reader
must be told, which is exactly what the standing is for.

M10 — **"countercondition" is not a typed field anywhere in the record.** It
occurs only inside `artifact.data.content_ref` prose (13 artifacts) and in
`src/deepreason/skills/`. There is no record of a countercondition being
"registered", and none of a proposal it "came from". R7's fifth named claim
therefore has no literal typed form; S8 below states the nearest typed
re-statement and marks it a proxy in the claim's own note, the way h-EPI's
`docs/what-the-records-refute.md` marks its proxies.

---

## The shape adopted (R3), stated in DeepReason's terms

- The unit of observation is ONE RUN ROOT. A claim's scope selects roots by
  their own typed status fields; its condition is a predicate over one root's
  record.
- A `never` claim is refuted by one root where its condition holds; an
  `always` claim by one root where it does not.
- Statuses: `REFUTED`, `UNREFUTED_FOR_DECLARED_SCOPE`, `NOT_TESTED`.
  h-EPI's fourth status, `REFUTED_ON_CONTESTED_READING`, is NOT adopted: it
  exists only to carry the appraisal layer's verdict, which R15 parks.
- Standing: `SHOWN_ABLE_TO_FAIL` when the refuting condition held on at least
  one supplied root, in or out of scope; `NOT_SHOWN_ABLE_TO_FAIL` when it
  held on none (R11).
- Survival is never confirmation. Every report prints the non-inductive limit
  in its own words.
- No readiness is read from, or asked of, a person anywhere (R25). The tool
  reads the record and nothing else; it has no argument graph, no readiness
  field, and no place to put one.

## Items

**S1 (R1, R2).** The clone at `/home/user/h-epi`, head
`f97239fc38f52b664fb56ad518a8ac60ac959482`, read-only; the five named files
read. Nothing vendored, nothing modified.
    accept: `cd /home/user/h-epi && git rev-parse HEAD && git status --porcelain`
    -> the head above and empty porcelain output.

**S2 (R4, R14).** New file `tools/record_claims.py`. A read-only reader over
one or more run roots. It opens `run-status.json`, `log.jsonl` and
`objects/<kind>/*.json` for the kinds a claim actually names, and nothing
else. It writes NOTHING into any run root, and it imports no DeepReason
module, so no code path exists by which it could append to a record.

CORRECTION, 2026-09-06, made while executing CHECKLIST step 3 and recorded
rather than applied silently: this item first read "It opens no file for
writing anywhere", which contradicts S3's own `--markdown <out>` option in
the same spec. The obligation R14 states is that the tool "writes nothing
into any root and changes no status" — not that it cannot write a report
where the operator asks for one. The wording above is corrected to R14's
own scope, and the guarantee is enforced in code: `_refuse_inside_a_root`
walks the destination's parents and refuses any path inside a directory
holding `run-status.json` and `log.jsonl`. The digest test (S12) proves the
roots are untouched; a separate test proves the refusal fires.
    accept: no `import deepreason`; every write goes through the
    `--markdown` destination and `_refuse_inside_a_root` guards it; plus
    S12's digest test over a committed root.

**S3 (R5).** CLI:

    python tools/record_claims.py --claims <file> --root <root> [--root <root> ...]
                                 [--json] [--markdown <out>] [--quiet]

Prints, per claim: `<claim_id>: <STATUS>`, the statement and kind, how many
roots were tested, the refuting record ids **capped at five** each with one
witness locator, and the standing sentence. `--json` prints the same as one
object. Exit 0 whenever the run completed, whatever the statuses — it is not
a gate (R14, C4). Exit 2 on a usage error, an unreadable root, or a claims
file that does not validate.
    accept: running it on the ARM R root with the tranche claims file prints
    at least one `REFUTED`, at least one `UNREFUTED_FOR_DECLARED_SCOPE`, at
    least one `NOT_TESTED`, and exits 0.

**S4 (R9).** The condition vocabulary, fixed and fail-closed — an unknown key
raises, never evaluates to false. Exactly one key per condition object:

| key | reads | shape |
|---|---|---|
| `all_of` / `any_of` / `not` | — | nesting |
| `status` | `run-status.json` | `{field, eq\|in\|gt\|gte\|lt\|lte\|present\|absent}` |
| `event` | `log.jsonl` | `{rule, min_count}` |
| `measure` | `log.jsonl` `Measure` events | `{code \| code_prefix, min_count}` |
| `control` | `log.jsonl` `Control` events | `{action, min_count}` |
| `object` | `objects/<kind>/` | `{kind, where: [[path, op, value]...], min_count}` |

`where` paths are dotted over the object's `data`, with `[]` for a list and
an explicit quantifier prefix `any:` (default) or `every:`. Ops: `eq`, `ne`,
`in`, `not_in`, `contains`, `present`, `absent`, `gt`, `gte`, `lt`, `lte`.
Every primitive is a field the record already carries (M1-M8); nothing is
derived, computed or judged.
    accept: `python -m pytest tests/test_record_claims.py -k vocabulary -q`
    -> passed, including one test that an unknown condition key RAISES.

**S5 (R11).** Standing. For each claim the tool counts roots outside the
declared scope on which the refuting predicate held (`witnesses_outside_scope`)
and roots inside it (`refuting`). `SHOWN_ABLE_TO_FAIL` iff either is
non-zero. An unrefuted claim with neither prints, in these words: *the
refuting condition held on no supplied root, in or out of scope; this check
has not been shown able to fail, and the survival should be read
accordingly.*
    accept: `python -m pytest tests/test_record_claims.py -k standing -q`
    -> passed; and the tranche claims file prints that sentence for
    `CRIT-CAP-01` against the real root (M6).

**S6 (R6).** New file `docs/CLAIMS_SCHEMA.md`: the claims file's shape, the
full condition vocabulary with one worked example per key, the three
statuses, the two standings, the non-inductive limit, and an explicit
"what this is not" section (not a gate, not a status, not a score — R14; no
readiness from a person — R25). It cites `DR-SUB-harness`,
`DR-CON-evidence-states`, `DR-INV-evidence-channels` and `DR-SUB-evidence`
for the record vocabulary (R10).
    accept: `test -f docs/CLAIMS_SCHEMA.md` and a grep for each of the six
    condition keys, the three statuses and both standings.

**S7 (R7, R13).** New file
`experiments/2026-09-06-change-writers-room-organiser-testing/claims.json`,
re-stating PREREG.md §8's registered predictions as claims. Every claim is
about what the record shows a seat or the harness DID; none is about whether
any answer is correct (R13, C5). The five R7 names, plus four more from
§8 that the record can actually decide:

| id | kind | the R7 name or §8 prediction it re-states | expected |
|---|---|---|---|
| `ORG-CITE-01` | never | "the organiser never cites an id outside the legend" | REFUTED (58 + 0) |
| `ORG-PLAN-01` | always | "every seat's section plan names its directive" — §8: names `dr.output-contract.organiser` on every conjecturer call | UNREFUTED |
| `ORG-PLAN-02` | never | §8: "and never `dr.output-contract.conjecturer`" | UNREFUTED, NOT_SHOWN_ABLE_TO_FAIL |
| `RUN-STOP-01` | never | "a run never stops `operational_failure`" | REFUTED |
| `CRIT-CAP-01` | never | "the critic never exhausts its smallest contract" | UNREFUTED, NOT_SHOWN_ABLE_TO_FAIL (M6) |
| `ORG-COND-01` | never | "every countercondition registered came from a room proposal" — typed proxy, S8 | REFUTED |
| `RUN-TERM-01` | always | §8: "both arms reach a clean typed terminal" | REFUTED |
| `EVID-EXPOSED-01` | never | §8: "≥ 1 `EVIDENCE_REF_NOT_EXPOSED` measure appears" | UNREFUTED, NOT_SHOWN_ABLE_TO_FAIL (M9) |
| `ARMH-STOP-01` | never | §2/Amendment 3: ARM H's own terminal | NOT_TESTED (ARM H deferred) |

    accept: `python tools/record_claims.py --claims <that file> --root <the
    ARM R root> --json` -> every row above matches its expected column.

**S8 (R7, R13).** `ORG-COND-01`'s typed re-statement, and why. M10: the
record types no countercondition and no proposal-provenance, so the literal
sentence has no typed form. The nearest thing the record DOES type is the
citation check a candidate's evidence references get at
`rules/conj.py:2468` (M8): a countercondition traceable to a room proposal is
one whose citation resolves and whose quote matches. The claim is therefore
written as *a candidate never registers an evidence citation that fails its
check* — condition `measure code_prefix "evidence-citation:"` minus the
verified code — and its `note` says, in the claim file itself, that it is a
PROXY and what it cannot see. This follows h-EPI's own proxy caution
(`docs/what-the-records-refute.md`, the second caution) rather than
pretending to a reading the record cannot support.
    accept: the claim's `note` field is non-empty and contains the word
    "proxy"; a test asserts every proxy claim in the file carries one.

**S9 (R8).** The claims file is run against the FAILED root, by its committed
path, and the output is pasted into VALIDATION.md and DELIVERY.md.
    accept: pasted output showing `RUN-STOP-01: REFUTED` with the root's own
    run id as the refuting record id.

**S10 (R12).** New file `tests/test_record_claims.py`. Synthetic roots built
in `tmp_path` from the record's real shapes (M1-M5), never from a copy of a
committed root:
  - one root that refutes a `never` claim of each primitive kind (`status`,
    `event`, `measure`, `control`, `object`);
  - one root that refutes an `always` claim;
  - one root on which every claim survives;
  - one pair where the refuting condition holds only OUT of scope, so the
    standing reads `SHOWN_ABLE_TO_FAIL` with zero refutations;
  - one where it holds nowhere, so the standing reads
    `NOT_SHOWN_ABLE_TO_FAIL`;
  - `NOT_TESTED` when scope admits no supplied root;
  - the fail-closed vocabulary tests (S4);
  - a mutation proof: each synthetic refutation flips to a survival when the
    one field it reads is changed, and back — so no test passes for a reason
    other than the field it names;
  - the read-only proof (S12).
    accept: `python -m pytest tests/test_record_claims.py -q` -> passed,
    0 failed.

**S11 (R21, C-SCHEMA).** `docs/map/INV-frozen-surfaces.md` gains one section
under "The instruments that prove you did not break anything", which is the
map's own home for `tools/` instruments (it already owns `root_sweep.py`,
`diff_budget.py` and `blast_radius.py` there, each with its `check:` lines).
The section says plainly that this instrument proves nothing about frozen
surfaces and is not a gate (R14) — it sits there because that is where the
map keeps `tools/`, not because it guards anything. Its `check:` runs the
tool on the committed ARM R root and asserts a specific status, so the check
can fail (`DR-SCHEMA`: "Do not write a check that cannot fail").
    accept: `python tools/docs_verify.py` -> 0 failed; and the new check
    fails when the tool's status derivation is mutated.

**S12 (R14).** Read-only proof. A test hashes every file under a committed
root before and after a full run of the tool and asserts the two manifests
are identical, and asserts the tool's source contains no write-mode `open`
and no `import deepreason`.
    accept: `python -m pytest tests/test_record_claims.py -k read_only -q`
    -> passed.

**S13 (R15, R16, C6).** `PARKED.md` gains one entry for the appraisal
labelling rule, whose FIRST line says readiness in DeepReason is read from
the record — warrant checks, judge verdicts, criticism dispatch — never
marked by a person (R25). It points
`experiments/2026-09-05-criticism-premise-declaration/PARKED.md` P4 (the
UNDECIDED-essential-premise fork, which is the
"UNDECIDED-premise-still-refutes" question by its own heading) at
`/home/user/h-epi/src/creib/forge/conformance/appraisal.py` for the
LABELLING RULE ALONE. The entry carries a ready-to-send prompt as ONE fenced
block, delivered inline in the final chat reply (C6).
    accept: `grep -n "readiness" PARKED.md | head -1` -> the first line of
    the entry; and the entry names both P4 and `appraisal.py`.

**S14 (R17, R18, R20).** Nothing under `src/deepreason/` changes; PREREG.md
is not edited; anything found is parked, not fixed.
    accept: `git diff --stat origin/main...HEAD -- src/deepreason/` -> empty;
    `git diff --stat origin/main...HEAD -- experiments/2026-09-06-change-writers-room-organiser-testing/PREREG.md`
    -> empty.

**S15 (R22, R23, R24).** Ring while iterating
(`python -m pytest tests/test_record_claims.py -q`), the full gate ONCE at
the validation boundary because `tests/` changed. Delivery through
`dr-validate-change` then `dr-deliver-change` with the R-by-R table. Commit
and push at every phase boundary with 2s/4s/8s/16s retry.
    accept: VALIDATION.md carries the pasted full-gate line with `0 failed`;
    DELIVERY.md carries a row for every R1-R25.

## Assumptions (operator may override)

A1 (Q1) — assumed, operator may override: the measures the brief names map to
the record as follows, read from the record and the code that writes it, not
chosen: citation checks = `Measure` `inputs[0]` with prefix
`evidence-citation:` (M2, M8); seat retirements and capability exhaustion =
`workflow-route-seat-insufficient-capability-v1` objects (M6); transport
faults = `workflow-provider-attempt-v1` objects with a `transport_failure`
outcome (the census in `DR-INV-frozen-surfaces` counts committed roots
carrying them; this root carries none); budget denials = `run-status.json`
`stop_reason` plus `workflow-token-reservation-v2` objects; judge verdicts =
`Measure` codes and artifact provenance roles; criticism dispatch
declarations = `Measure` code `criticism.dispatch.v1` (M2). The tool does not
hard-code any of these: they are what a claims file WRITES, using the six
generic primitives. That is the smallest reading — the vocabulary stays
generic and the mapping lives in claims files, where it can be argued with.

A2 (Q2) — assumed, operator may override: "every seat's section plan names
its directive" is read as PREREG.md §8's own operational prediction, which is
the only form of it the record can decide: every `workflow-context-section-plan-v1`
object names `dr.output-contract.organiser` as a rendered section and none
names `dr.output-contract.conjecturer` (M7). Only the organiser layout
appears on this root, so "every seat's" and "every conjecturer call's" are
the same set here; the claim is scoped and worded so that a later root with a
second layout would test it honestly rather than pass by accident.

A3 (Q3) — assumed, operator may override: a `claims.json` added beside
PREREG.md does not amend it and is not presented as an amendment. The claims
file's own `title` and a header comment field say so, and PREREG.md is not
touched (S14, R17). The claims file RE-STATES sealed predictions in a form a
machine can test; the sealed document remains the authority for what was
predicted.

A4 (Q4) — recorded, not asked: `.claude/skills/README.md` does not exist in
this checkout (C3). Nothing in the brief depends on it. Not created — that
would be inventing an artifact the operator did not ask for.

A5 — assumed, operator may override: the tranche exceeds `dr-spec-change`
step 7's ~300-line split threshold (Budget below). It is NOT split into
sub-tranches: the threshold exists to stop a change sprawling across a live
surface, and this change adds one new file with no existing consumer, its
tests, its document and one claims file. It is split into five ORDERED
COMMITS instead (Budget), each with its own done-criterion, which buys the
same reviewability without four deliveries.

## Questions for operator (STOP if non-empty)

None. Every fork above was decided from the record (M1-M10) or from the
operator's own recorded laws, per `dr-ask-the-right-question`'s cheapest-
authority rule. The one fork that looked material — whether to build h-EPI's
appraisal standing — is decided by the operator's own words in REQUEST.md
("Actually that ruling was old", "no the rule from the other harness") and
by R15/R25: it is parked, not built.

## Out of scope (explicit)

- The appraisal layer in any form (R15). Parked at S13. Not requested.
- Any human-readiness field, flag, or file (R25). Not requested; forbidden.
- Making this a gate, a status, a score, or a CI step (R14). Not requested.
- Writing claims results into a run root (R14). Not requested.
- Fixing the ARM R failure, or anything else found (R20). Not requested.
- Editing PREREG.md (R17). Not requested.
- Vendoring or importing any h-EPI code (R1, R3). Not requested.
- A claims file for any other tranche. Not requested.

## Frozen-surface contact forecast

`python tools/blast_radius.py --files tools/record_claims.py
tests/test_record_claims.py docs/CLAIMS_SCHEMA.md
docs/map/INV-frozen-surfaces.md
experiments/2026-09-06-change-writers-room-organiser-testing/claims.json`,
its own computed fields pasted verbatim:

    "frozen_surface_contacts": []
    "frozen_adjacent_contacts": []
    "reachability": []
    "frozen_surface_verdict": "CLEAR"
    "disclosure_summary": "This change touches none of the five frozen
    surfaces. 1 test file(s) and 1 map document(s) assert on the touched
    targets today."

**None of the five frozen surfaces is touched** (R19), stated after reading
`docs/map/INV-frozen-surfaces.md` and running its own gate: the five surfaces
are `capabilities/state.py`, `harness.py`, `invariants.py` + `verification/`,
`run_manifest.py` and `qualification.py`, plus the frozen-adjacent
`route_fingerprint` in `llm/firewall.py`. This tranche writes one file under
`tools/`, one under `tests/`, one under `docs/`, one claims file under
`experiments/`, and appends one section to a map document. `src/deepreason/`
is byte-untouched (R18, S14).

## Blast-radius census

The gate's own `consumers` fields, pasted, every hit classified:

    "consumers": {
      "tests": [{"target": "docs/map/INV-frozen-surfaces.md",
                 "hits": ["tests/test_provider_transport_faults.py:491"]}],
      "map_checks": [{"target": "docs/map/INV-frozen-surfaces.md",
                      "hits": ["docs/map/INV-frozen-surfaces.md:495",
                               "docs/map/REC-change-a-seam.md:44",
                               "docs/map/SUB-harness.md:33"]}],
      "qualification_digest": [],
      "wheel_smoke_pins": []
    }

- `tests/test_provider_transport_faults.py:491` — reads the document's
  transport-fault census to select a committed root. **MUST NOT MOVE**: S11
  appends a section about a `tools/` instrument and touches no census.
- `docs/map/INV-frozen-surfaces.md:495` — the document's own granted-contact
  parser inside a check. **MUST NOT MOVE**: S11 adds no `**Granted contact`
  block.
- `docs/map/REC-change-a-seam.md:44`, `docs/map/SUB-harness.md:33` —
  references to the document by ID. **MUST NOT MOVE**: the ID is unchanged.

Manual cross-check, required by `dr-spec-change` step 5 for anything the gate
reports `UNKNOWN` (it reported none) and for symbol shapes the gate cannot
resolve — the new files have no symbol consumers because they do not exist
yet:

    grep -rn "record_claims\|CLAIMS_SCHEMA" tests/ docs/ src/ tools/   -> no hits

## Measurements

M1-M10 above. Every load-bearing claim in this document is one of them.

## Budget

Itemized:

    tools/record_claims.py                          ~430
    tests/test_record_claims.py                     ~300
    docs/CLAIMS_SCHEMA.md                           ~190
    experiments/.../claims.json                     ~150
    docs/map/INV-frozen-surfaces.md (appended)       ~30

    python3 -c "print(sum([430, 300, 190, 150, 30]))"  -> 1100

**~1100 lines, 5 commits** (S6 doc; S2+S4+S5 tool; S7+S8 claims file;
S10+S12 tests; S11 map — the map section lands in the SAME commit as the
tool's final form, per CLAUDE.md's map rule). Ceiling for
`tools/diff_budget.py` at each `[COMMIT]` step: 1100 over the deliverable
paths above; the tranche's own `experiments/2026-09-06-change-record-claims/`
documents are workflow artifacts and are excluded by `--paths`.

Frozen surfaces touched: none.

Rubric: 6/6 yes — every R has a spec item with a machine-decidable accept
(R1-R25 appear at S1-S15); the blast-radius census is pasted and every hit
classified; the frozen-surface contact forecast is recorded with the gate's
own verdict; every mechanism the request names was traced to the record that
carries it (M1-M10, and M10 records the one that does NOT exist); this is not
a DESIGN-AND-STOP; nothing in this spec is untraceable to an R or C number.

---

## Budget amendment 1 (2026-09-06, at CHECKLIST step 16) — the estimate was wrong by roughly two-fold

`tools/diff_budget.py` reported EXCEEDED against the ~1100-line ceiling above.
Its own output, pasted:

    {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "origin/main",
     "against": null,
     "areas": {"tools/record_claims.py": 831,
               "tests/test_record_claims.py": 877,
               "docs/CLAIMS_SCHEMA.md": 269,
               "docs/map/INV-frozen-surfaces.md": 51,
               "experiments/.../claims.json": 228},
     "total_insertions": 2256, "ceiling": 1100, "verdict": "EXCEEDED"}

**This is an estimation error in the Budget section above, not scope creep,
and the difference matters.** Measured: the delivered files are 831, 877, 269,
228 and 51 lines, and `git diff --numstat origin/main...HEAD` reports the same
numbers with ZERO deletions — so 2 256 is the size of the delivered work, not
churn from rewriting it. Every line traces to an item S1-S15 and through it to
an R number; the anti-invention pass was re-run over both new files and found
nothing to delete.

Where the estimate went wrong, item by item:

- `tools/record_claims.py`: estimated ~430, actual 831. The gap is almost
  entirely R9's fail-closed rule. Every primitive validates its own shape and
  raises a message naming the offending path, because a condition that
  evaluates to false on a typo becomes a survival — the failure mode this
  instrument exists to make visible. Validation and its messages are roughly
  half the file.
- `tests/test_record_claims.py`: estimated ~300, actual 877. The gap is the
  mutation proofs. SPEC S10 asked for one, and there is one per refutation:
  each of the six primitive tests builds the refuting root AND the root with
  the single field changed, so no test can pass for a reason other than the
  field it names. That doubles the fixture code in every test.
- The other three came in at 269, 228 and 51 against 190, 150 and 30 — the
  ordinary margin of a hand estimate.

Ceiling revised to **2 300**:

    python3 -c "print(sum([831, 877, 269, 228, 51]))"   -> 2256

Not split into sub-tranches. Assumption A5's reasoning is unchanged by the new
number and is if anything stronger: the threshold exists to stop a change
sprawling across a live surface, and this one adds a file with no consumer,
its tests, its document, one claims file, and one appended map section.
Splitting it now would produce four deliveries of the same diff.

Reported to the operator in the delivery message rather than absorbed silently
(`dr-change-orchestrator`: report the contradiction, do not pick a side).
