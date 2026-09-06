# Validation — record claims

Verdict: **PASS**. Full gate 5147 passed, 6 skipped, 0 failed; every SPEC
acceptance check green; no frozen surface touched; every docs_verify failure on
the recorded baseline list.

REQUEST.md, SPEC.md and CHECKLIST.md were re-read in full before this phase.
Every acceptance check in SPEC.md was re-run here in item order, even the ones
a checklist step already ran: a step proves local progress, this proves the
assembled whole.

## Acceptance checks, in item order

**S1 (R1, R2) — the clone is read-only and untouched.**

    $ cd /home/user/h-epi && git rev-parse HEAD && git status --porcelain
    f97239fc38f52b664fb56ad518a8ac60ac959482
    (porcelain output empty)

PASS. Nothing vendored: `grep -rn "creib" tools/record_claims.py
tests/test_record_claims.py docs/CLAIMS_SCHEMA.md` returns three hits and no
code — two prose sentences naming where the shape came from, and one string
in `test_a_claims_file_with_the_wrong_schema_version_is_refused`, which feeds
the other harness's schema version in as input a DeepReason claims file must
REFUSE.

**S2 (R4, R14) — read-only, and no harness import.**

    $ python -c "s=open('tools/record_claims.py').read(); \
        assert 'import deepreason' not in s and 'from deepreason' not in s; \
        assert '_refuse_inside_a_root' in s; print('read-only ok')"
    read-only ok

PASS, under the corrected wording recorded in SPEC.md's S2 correction: the
guarantee is that nothing is written INTO A ROOT. Proven three ways —
`_refuse_inside_a_root` in the code, `test_read_only_the_root_is_byte_
identical_after_a_full_run` hashing every file under the committed ARM R root
before and after a full run, and `test_read_only_a_markdown_destination_
inside_a_root_is_refused` asserting exit 2 and no file created.

**S3 (R5) — the CLI and its statuses.**

    $ python tools/record_claims.py --claims <tranche claims.json> --root <ARM R root>
    ... ; EXIT=0

PASS: the run prints REFUTED (4 claims), UNREFUTED_FOR_DECLARED_SCOPE (4) and
NOT_TESTED (1), and exits 0. Full output pasted in DELIVERY.md.

**S4 (R9) — the vocabulary, fail-closed.**

    $ python -m pytest tests/test_record_claims.py -k vocabulary -q
    8 passed

PASS. Among them `test_vocabulary_refuses_an_unknown_condition_key`, which
asserts a typo RAISES rather than evaluating to false.

**S5 (R11) — the standing.**

    $ python -m pytest tests/test_record_claims.py -k standing -q
    3 passed

PASS. And on the real record `CRIT-CAP-01` prints
`NOT_SHOWN_ABLE_TO_FAIL` with the required sentence, because the seat that
exhausted its smallest authorized contract was the conjecturer, not the
critic (SPEC M6).

**S6 (R6) — `docs/CLAIMS_SCHEMA.md`.**

Every one of the six condition keys, the three statuses, both standings, and
the four map ids R10 names are present (grep, all `ok`). PASS.

**S7 (R7, R13) — the nine claims, against the committed root.**

    ORG-CITE-01      REFUTED                       SHOWN_ABLE_TO_FAIL
    ORG-PLAN-01      UNREFUTED_FOR_DECLARED_SCOPE  NOT_SHOWN_ABLE_TO_FAIL
    ORG-PLAN-02      UNREFUTED_FOR_DECLARED_SCOPE  NOT_SHOWN_ABLE_TO_FAIL
    RUN-STOP-01      REFUTED                       SHOWN_ABLE_TO_FAIL
    CRIT-CAP-01      UNREFUTED_FOR_DECLARED_SCOPE  NOT_SHOWN_ABLE_TO_FAIL
    ORG-COND-01      REFUTED                       SHOWN_ABLE_TO_FAIL
    RUN-TERM-01      REFUTED                       SHOWN_ABLE_TO_FAIL
    EVID-EXPOSED-01  UNREFUTED_FOR_DECLARED_SCOPE  NOT_SHOWN_ABLE_TO_FAIL
    ARMH-STOP-01     NOT_TESTED                    SHOWN_ABLE_TO_FAIL

Every row equals SPEC S7's expected column. PASS. Pinned as a regression by
`test_the_tranche_claims_file_reports_what_the_committed_record_shows`, which
selects the root by property (its own `operational_failure`) so a rename
cannot break it.

**S8 (R7, R13) — the proxy declares itself.**

    $ python -m pytest tests/test_record_claims.py -k proxy -q
    1 passed

PASS. `ORG-COND-01`'s note opens with the word PROXY and states what it
cannot see.

**S9 (R8) — run against the FAILED root.** PASS; `RUN-STOP-01: REFUTED` names
run id `0d7f086102aac868f4400c0f50bca02741c8b03b71571f968729e18db7c9c7cb` and
the locator `run-status.json:stop_reason='operational_failure'`.

**S10 (R12) — the tests.**

    $ python -m pytest tests/test_record_claims.py -q
    41 passed in 0.55s

PASS. Every claim kind refuted by a synthetic root, one root where all
survive, both standings, `NOT_TESTED`, the fail-closed vocabulary, and a
mutation proof per refutation.

**S11 (R21) — the map.** The instrument section is appended to
`docs/map/INV-frozen-surfaces.md` in the same commit as the tool's final
form. Its check runs the tool on the committed root and asserts three claim
verdicts. See "Map validation" below.

**S12 (R14) — read-only proof.**

    $ python -m pytest tests/test_record_claims.py -k read_only -q
    3 passed

PASS.

**S13 (R15, R16) — the park.** `PARKED.md` P1's first line reads "Readiness
in DeepReason is read from the record — warrant checks, judge verdicts,
criticism dispatch — never marked by a person." It names
`experiments/2026-09-05-criticism-premise-declaration/PARKED.md` P4 and
`src/creib/forge/conformance/appraisal.py`, and carries its prompt as one
fenced block. PASS.

**S14 (R17, R18, R20) — nothing in `src/`, nothing in PREREG.**

    $ git diff --stat origin/main...HEAD -- src/deepreason/ \
        experiments/2026-09-06-change-writers-room-organiser-testing/PREREG.md
    (empty)

PASS.

**S15 (R22, R23, R24) — process.** Ring while iterating, the full gate once
at this boundary, five commit boundaries each pushed with retry. PASS.

## The full gate

    $ python -m pytest tests/ -q -n 4
    5147 passed, 6 skipped in 1159.24s (0:19:19)

## Frozen-surface diff — pasted, empty

    $ git diff --stat origin/main...HEAD -- \
        src/deepreason/capabilities/state.py src/deepreason/harness.py \
        src/deepreason/invariants.py src/deepreason/run_manifest.py \
        src/deepreason/qualification.py
    (empty output — no frozen surface touched)

Empty, as SPEC.md's contact forecast predicted (`blast_radius.py`:
`frozen_surface_verdict: CLEAR`, both contact lists `[]`).

## Behaviour-preservation spot-check

Not owed, and the skip is a decision rather than an omission: the change
touches no reader or validator of the append-only record. `tools/record_claims.py`
is a new file that imports nothing from `deepreason`, so no code path that
`verify_root` or any replay validator reaches was altered. The stronger
statement is already proven by S12: a committed root is byte-identical before
and after a full run of the tool.

## Packaging surface

Packaging surface untouched — smoke not owed. No change to `pyproject.toml`,
console entry points, the MCP tool set, or the wheel layout;
`tools/record_claims.py` is not a console script and is not packaged.

    $ git diff --stat origin/main...HEAD -- pyproject.toml src/deepreason/mcp_server.py
    (empty)

## Map validation

    $ python tools/docs_verify.py
    docs_verify: 6 failed

The six, listed by `--failed`, every one on `docs/AUDIT_BASELINES.md`'s
recorded list for this container's shallow clone (which the baseline states as
"5 OR 6 failed"):

| where | class | baseline row |
|---|---|---|
| `SEAM-llm-x-rules.md:54` | unparseable check (lost closing backtick) | yes — the single known `--audit` finding, parked P3 |
| `CON-run-identity.md:211` | git history absent from a shallow clone | yes — the three git-history rows |
| `CON-run-identity.md:213` | git history absent from a shallow clone | yes |
| `CON-run-identity.md:215` | git history absent from a shallow clone | yes |
| `INV-frozen-surfaces.md:206` | the transport_failure census asserting zero; one exists | yes — parked P-D3 |
| `INV-frozen-surfaces.md:876` | needs branch `origin/claude/deepreason-p-s1-commitments-wowcib`, absent from this clone | git-history class, same cause as the three above |

**Neither of the two checks this tranche added is among them.** Both were run
in the same pass and both passed; the one that runs the tool was separately
mutation-proven (forcing every claim to `REFUTED` makes it exit 1, restoring
makes it exit 0), so it is a check that can fail.

    $ python tools/docs_verify.py --audit
    SEAM-llm-x-rules.md:54: unparseable check: ...
    docs_verify --audit: 1 finding(s)

One finding, the recorded baseline one. This tranche added no vacuous check.

    $ python tools/docs_verify.py --links
    docs_verify --links: 0 dangling reference(s), 82 document(s)

    $ python tools/docs_verify.py --coverage
    docs_verify --coverage: 7 seam(s) swept, 22 without a Sweep: header, 2 finding(s)

Pre-existing and untouched: the two findings are
`SEAM-schools-x-scratch.md` (enforcement site not named) and
`SEAM-rules-x-scratch.md`; this tranche adds no seam document and changes no
seam's enforcement sites.

    $ python tools/docs_verify.py --stale
    docs_verify --stale: 24 document(s) worth re-reading

Judged, as the skill requires. All 24 entries name commits from OTHER
tranches touching those documents' `Owns:` files — the writer's-room, mini
isolation, criticism-premise and transport-fault programmes. None is caused
by this change: this tranche owns no `Owns:` file, because it adds no
subsystem and touches no `src/deepreason/` path. Dismissed for this tranche,
and every one of them is a pre-existing item for the tranche that made it
stale.

**`Verified-at:` on `docs/map/INV-frozen-surfaces.md`** is advanced to this
tranche's head, because this phase did re-run that document's checks. Recorded
alongside it so the stamp is not read as more than it says: two of that
document's checks fail, both on the baseline list above, and neither is new.

**New behaviour is covered by a new map check** (SCHEMA's rule): the section
carries two, one of which executes the instrument against a committed root and
asserts three specific verdicts.

**No typed-record observable was added**, so no sweep probe is owed. This
tranche writes nothing to any record; the sweep has nothing new to read, and
the "sweep byte-identical" trap does not apply.

## Requirement sweep

Every R, and what demonstrates it, is the R-by-R table in DELIVERY.md.
Nothing is deferred; no R lacks a demonstration.

## Assumptions carried to the operator

- **A1** — how the brief's named measures map to the record (citation checks,
  seat retirements, transport faults, budget denials, judge verdicts,
  criticism dispatch). The tool hard-codes none of them: the mapping lives in
  claims files, where it can be argued with. Operator may override.
- **A2** — "every seat's section plan names its directive" is read as
  PREREG §8's own prediction about `dr.output-contract.organiser`, which is
  the only form of it this record can decide. Operator may override.
- **A3** — a `claims.json` beside PREREG.md does not amend it; the file's own
  title says so and PREREG.md is untouched. Operator may override.
- **A4** — `.claude/skills/README.md` does not exist; nothing was created.
  Recorded, not asked.
- **A5** — not split into sub-tranches. Reinforced by Budget amendment 1: the
  spec's line estimate was wrong by roughly two-fold, and the amendment says
  where and why. Reported, not absorbed.

## Deviations from SPEC.md, both recorded in SPEC.md itself

1. **S2's wording** contradicted S3's own `--markdown` option. Corrected in
   place with a dated CORRECTION paragraph naming the contradiction, and the
   guarantee narrowed to R14's own scope (nothing written into a root),
   enforced by `_refuse_inside_a_root` and proven by two tests.
2. **The budget** was EXCEEDED at ~1100 and is amended to 2 300 with the
   measured arithmetic. Not scope creep: `git diff --numstat` reports zero
   deletions, so 2 256 is the size of the delivered work, and the
   anti-invention pass found nothing untraceable to an R.
