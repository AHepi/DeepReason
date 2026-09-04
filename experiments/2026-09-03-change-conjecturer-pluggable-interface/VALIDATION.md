# VALIDATION — the seat as a shell

Phase: `dr-validate-change`. Date: 2026-09-04.
Base: `main` at `e91f4fcc3`. Branch:
`claude/conjecturer-pluggable-interface-7v3es6`.

**VERDICT: PASS**, with two items explicitly INCOMPLETE and both stated below
rather than buried. This document validates; it patched nothing.

---

## §1 The acceptance test the tranche turns on

`SPEC.md` S10.4, extended to both seats by §17.3: the default rendering must
not move. It did not, and no fixture was touched.

```
$ python -m pytest tests/test_conj_pack_legacy_golden.py \
      tests/test_crit_pack_legacy_golden.py -q
15 passed
```

Both goldens were captured from the base commit BEFORE any refactor existed
(steps 2, 7), and both are proven able to fail: a one-character mutation of
either maximal fixture turns its file RED, pasted at steps 3 and 8. The nine
fixtures between them reach all twenty conjecturer section slots, all thirteen
critic ones, both menu sections, the withheld notice and the restated question.

## §2 The gate

```
$ python -m pytest tests/ -q -n 4
4961 passed, 6 skipped in 942.26s (0:15:42)
```

0 failed, with the granted record write in. Run three times across the
tranche; the pre-grant tree was 4956 passed.

**No assertion was weakened.** Eight checks went red during the build. Three
were tests and five were map checks; every one of them pinned the LOCATION of
a decision that legitimately moved, and every one was RE-AIMED at where its
subject now lives — in four cases at something stronger than before (per-file
`_head` counts rather than one file; individually pinned plugin classes rather
than three fields against one function; layout data rather than parsed source;
an AST call count rather than a text count). Each is recorded at its own step
with its reason.

Two further reds were fixed in the CODE rather than in the check, which is the
direction that matters:

- **N4 was narrowed.** As `SPEC.md` §8.4 specified it, the rule deleted an
  optional field supplied as `null` OR `""`. Three tests in
  `tests/test_cli_production_doctor_v6.py` went red: the repair protocol's own
  fixture is `{"finding": "supported", "message": ""}`, an empty string a
  contract rejects deliberately so the model tries again, and deleting it
  turned a REFUSAL into an ACCEPTANCE. That is a verdict change, which
  assumption A3 makes a STOP rather than a judgment call. N4 now applies to
  `null` only.
- **A class name was changed.** A plugin I named `_Problem` tripped
  `SEAM-llm-x-rules`' regex for ontology constructors (`Problem\(`). The class
  was renamed rather than someone else's invariant loosened.

## §3 Frozen surfaces

```
$ python tools/blast_radius.py --files $(git diff --name-only e91f4fcc3..HEAD -- 'src/*') \
      --against e91f4fcc3
verdict: CLEAR   contacts: []   adjacent: []   drift: []
```

**AMENDED 2026-09-04, after the operator's grant.** The branch now touches
frozen surface 2 deliberately, so both instruments say so:

```
$ python tools/blast_radius.py --files <the working tree's src/ changes> \
      --symbols record_transaction_transition SectionPlanV1 --against e91f4fcc3
verdict: CONTACT
 - harness.py event application and well-formedness | DIRECT | src/deepreason/harness.py
 - harness.py event application and well-formedness | SYMBOL_INDIRECT | record_transaction_transition
 - harness.py event application and well-formedness | SYMBOL_INDIRECT | SectionPlanV1
```

And `INV-frozen-surfaces.md:364`'s branch tripwire now FIRES, which is the
tripwire doing its job rather than a regression: it fires on any branch
touching a frozen path, and this one does, under `REQUEST.md` §1c. It was
GREEN through steps 1-45 and turned red only at the granted commit. **The
check is not weakened to silence it** — a tripwire that exempts the case it
was built for is not a tripwire.

Surface 3 is UNTOUCHED and that proof matters more now than before, because
surface 2 was opened: neither `invariants.py` nor `verification/report.py`
mentions the new kind, and no `verify_root` check was added (step 25).

The pre-grant reading is kept below for the record.

The forecast held, but NOT by luck: the instrument disagreed with it twice and
both disagreements are disposed on the record rather than argued away.

1. **`wire_contract_for`** (SPEC §17.9). Declaring it a touched symbol returns
   CONTACT on surfaces 3 and 4. Both rows were opened and read; both are real
   call sites (`invariants.py:1233` builds a replay authority set from its
   contract ids, `run_manifest.py:2074` folds them into a qualification
   subject). Disposed into a FOURTH binding decision — the function's mapping
   is frozen by its callers, form selection happens at the dispatch site — and
   pinned by `tests/test_wire_contract_id_map.py`, which is mutation-proven.
2. **A new record object kind** (step 24). Writing section receipts to the run
   record needs one, and that is a DIRECT contact with surface 2
   (`harness.py`). PARKED for a grant rather than taken. The cheaper road was
   checked and is worse: reusing the existing pack-plan family would mean
   widening an alias pattern and a four-value channel enum that 3 533
   committed rows already use.

## §4 The map

```
$ python tools/docs_verify.py
docs_verify [full]: 78 documents, 1356 checks, 4 workers
docs_verify: 6 failed
```

All six are rows step 5 classified against `docs/AUDIT_BASELINES.md`:
`SEAM-llm-x-rules.md:54`; `CON-run-identity.md:211/213/215` (shallow clone —
`git rev-parse --is-shallow-repository` is `true` here);
`INV-frozen-surfaces.md:181`; and `INV-frozen-surfaces.md:736`.

**`INV-frozen-surfaces.md:736` is a row the window instruction did NOT list,
and it is not this tranche's.** Reproduced as environment rather than assumed:
its check runs `git show origin/claude/deepreason-p-s1-commitments-wowcib:...`
and that branch is absent from this shallow clone (`git rev-parse --verify` on
it: `fatal: Needed a single revision`). All three failing documents are
byte-identical to the base commit. **Proposed as a new shallow-clone baseline
row**; not fixed here, because baselines belong to the audit family.

`--links`: 0 dangling over 78 documents. `--audit`: the one baseline finding,
none naming a document this tranche wrote.

## §5 Per-requirement acceptance

| R | acceptance check | result |
|---|---|---|
| R1 | S11.1, S11.2 | PASS — neither renderer builds a section; adding one edits no source file, measured by mtime |
| R2 | S10.4 golden | PASS — `dr.evidence.frozen`, `dr.evidence.citable` |
| R3 | S10.4 golden | PASS — `dr.history.v1`, with `include_refuted` |
| R4 | S10.4 golden | PASS — `dr.neighbourhood`, `dr.neighbourhood.live` |
| R5 | S11.2 | PASS — one protocol, 30 seeded plugins, both seats |
| R6 | S12.1 varies one | PASS as a capability; the measurement is the later tranche |
| R7 | S11.3 | PASS — `text` is free text; the harness parses none of it |
| R8 | S11.2 | PASS — plugin or `.tmpl`, no code required |
| R9 | S4, S12 | PASS — a format is a text file |
| R10 | S11.4, S12.2 | PARTIAL — the wrapper and the form are selectable; per-model preference is parked as P7, with its reason |
| R11 | S10.4 | PASS — every default is byte-identical |
| R12 | operator approval | PASS (design window) |
| R13 | — | PASS — `dr.episodes.slot` registered, unimplemented, in no layout |
| R14 | premise | carried; FEASIBILITY §6.1 |
| R15 | S12.2 | instrument committed, not run |
| R16 | S11.3, S11.4 | PASS — the parse half does not vary |
| R17 | S11.4 | PASS, NARROWED — five rules, N4 reduced on measured evidence |
| R18 | premise; Q5 | still open — the operator's study was never supplied |
| R19 | step ordering | PASS — the recipe is committed; the experiment is its own tranche |
| R20 | §17.5 | PASS — the swap is demonstrated offline, with its limit stated |
| R21 | §17.1, §17.4 | PASS — a seat kind is a registered pairing |
| R22 | — | not built, by design; `PARKED.md` P6 |
| R23 | — | not built, by design; `PARKED.md` P6 |
| R24 | — | PASS in the negative: nothing shipped makes the separation harder, and S11.3 is the check |

## §6 What is INCOMPLETE, stated plainly

1. ~~**Section receipts are built but not written to the run record.**~~
   **CLOSED 2026-09-04 by the operator's grant** (`REQUEST.md` §1c, `R25`).
   Written for the CONJECTURER seat. NOT written for the critic, and that
   half is structural rather than unfinished: its transactional dispatch reads
   its pack out of a blob written earlier, so the receipts do not exist where
   the transaction is issued. Parked as P8.
2. **`preferred_conjecturer_form` (SPEC S9.1) is not shipped**, and
   `SEAM-llm-x-model-profiles.md` is therefore not written. Parked as P7 with
   the reason: the shell already names the form, and a second place naming it
   would be the disagreement the registry exists to prevent.

Neither is a silent omission and neither blocks the tranche's own acceptance
test.

## §7 The diff budget, after the grant

**EXCEEDED, and disclosed rather than absorbed: 2575 `src/` insertions against
the 2400 the operator raised it to.** The whole 190-line overrun is the granted
work — the record model, its four registrations, the service builder, the
canonical-shape position and the conjecturer's write path. Nothing else grew.

**VERDICT: PASS**, with the budget overrun and the two parked halves (P7, P8)
stated rather than absorbed.
