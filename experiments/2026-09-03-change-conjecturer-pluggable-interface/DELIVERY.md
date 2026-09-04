# DELIVERY — the seat as a shell: both briefs and both forms as one
# pluggable, configurable interface

Phase: `dr-deliver-change`. Date: 2026-09-04.
Base: `main` at `e91f4fcc3`. Branch:
`claude/conjecturer-pluggable-interface-7v3es6`.
`VALIDATION.md` verdict: PASS.

---

## §1 What shipped, in one paragraph

Both the conjecturer's brief and the critic's are now assembled from
registered section plugins under a registered layout, and both render
byte-identically to what they rendered before. A seat kind is a registered
pairing of a layout, a form and a wording, so the conjecturer's pairing can be
bound where the critic's is — demonstrated offline, with its real limit
stated. Formatting can be changed with a text file that provably cannot
execute. An operator can add a section from their own directory without
editing any source file, which is measured rather than asserted.

## §2 Gate and instruments

| instrument | result |
|---|---|
| `python -m pytest tests/ -q -n 4` | **4956 passed, 6 skipped, 0 failed** |
| both goldens | 15 passed, no fixture touched |
| `tools/blast_radius.py` over the actual diff | `CLEAR`, no contacts, no drift |
| `INV-frozen-surfaces.md:364` branch tripwire | GREEN |
| `tools/diff_budget.py --ceiling 2400` | 2385, `WITHIN` |
| `python tools/docs_verify.py` | 6 failed, every one a classified baseline |
| `--links` | 0 dangling, 78 documents |

## §3 Requirement-by-requirement reconciliation

Authority is `REQUEST.md` §1, §1a and §1b — the operator's verbatim words.

### From the original request

| R | the operator's words | where it landed | honest status |
|---|---|---|---|
| R1 | "makes conjecturer for a pluggable interface" | `llm/seat_sections.py`, `_walk_seat_layout` | **DONE** |
| R2 | "evidence gets a plugin" | `dr.evidence.frozen`, `dr.evidence.citable` | **DONE** |
| R3 | "history gets a plugin" | `dr.history.v1`, `include_refuted` off by default | **DONE** |
| R4 | "neighbouring conjecturers get a plugin" | `dr.neighbourhood`, `dr.neighbourhood.live` | **DONE** |
| R5 | "the plugin should be generic" | one protocol, 30 plugins, two seats, three shared | **DONE** |
| R6 | "increased or shrunk at will" | plugin parameters + layout entry bounds | **DONE** as a capability; measuring it is the later tranche |
| R7 | "it shouldn't be typed" | `text` is free text the harness never parses | **DONE**, bounded by A4: the RECEIPT stays typed, or the run is unauditable |
| R8 | "formatting can be done with the plugin" | `llm/seat_templates.py` | **DONE** |
| R9 | "test freely how conjecturers respond to various input format" | a `.tmpl` file; `PREREG.md` arm A3 | **DONE** as a capability |
| R10 | "the form ... adaptable ... for an LLMs capabilities" | form selection + role-prompt registry | **PARTIAL** — per-model preference parked as P7, reason below |
| R11 | "configurable with defaults" | every default byte-identical | **DONE** |
| R12 | "feasibility first, then a spec" | the design window | **DONE** |
| R13 | "still unsure what to do with episodes" | `dr.episodes.slot`: registered, unimplemented, in no layout | **DONE by not deciding** |
| R14 | "the input interface materially changes outputs" | premise, FEASIBILITY §6.1 | carried |
| R15 | "form-filling is a weak point" | the experiment recipe | instrument committed, NOT run |
| R16 | "outputs need strict minimum standards" | the parse half does not vary | **DONE** |
| R17 | "adapting the accepted outputs so they compile" | N1-N5 | **DONE, NARROWED** — see §4 |
| R18 | "they respond differently ... in a consistent way" | premise | **STILL OPEN** — the study was never supplied (Q5) |
| R19 | "history first, then the artifact, then measure" | recipe committed; experiment is its own tranche | **DONE** |

### From the amendment

| R | the operator's words | where it landed | honest status |
|---|---|---|---|
| R20 | "the conjecturer seat could be used to replace the critic seat" | `tests/test_seat_shell_swap.py` | **DONE**, with its limit stated |
| R21 | "an artifact truely is determined by input and output" | `SeatShellV1` | **DONE** |
| R22 | "conjecturers will need to be split in two" | not built, by design | parked, P6 |
| R23 | "criticism will need two different types" | not built, by design | parked, P6 |
| R24 | "slowly separate the authority layer" | nothing shipped makes it harder; S11.3 is the check | **DONE in the negative** |

## §4 The four things that did not go as specified

Each is a place the record disagreed with the plan. All four are disposed on
the record; none was smoothed over.

**1. The diff budget was exceeded, and the operator raised it.** At the
step-22 boundary: 1545 `src/` insertions against 1500. 785 of those were the
thirty sections MOVED out of `packs.py` (which shows 549 deletions), so net
growth was +996 and the instrument pays twice for a move — but the ceiling
names that instrument, so EXCEEDED is EXCEEDED. Three roads were priced; the
operator chose to raise the ceiling to ~2400 and finish. Final: 2385.

**2. `blast_radius` returned CONTACT where the amendment forecast CLEAR.**
Declaring `wire_contract_for` a touched symbol contacts surfaces 3 and 4. Both
rows were opened and both are real call sites, not grep artefacts. Disposed
into a fourth binding decision and `tests/test_wire_contract_id_map.py`. The
table in that file was hand-written first and six rows were WRONG; it was
regenerated from the tree rather than the code bent to the guess.

**3. Writing the receipts to the record needs a frozen-surface grant.** A new
object kind edits `harness.py`. PARKED, not taken. The receipts themselves are
built and proven.

**4. N4 was narrowed from what the spec proposed.** `SPEC.md` §8.4 said an
optional field supplied as `null` OR `""` may be dropped. The empty-string
half turned a refusal into an acceptance — the repair protocol's own fixture
is a blank message a contract rejects deliberately. Three doctor tests said
so. A3 makes a verdict change a stop, so the rule was narrowed to `null` only
and the tests were left alone.

## §5 Defects: none new, and one environment finding

**Before writing any defect here it was reproduced against the base commit in
this container**, per the window instruction. Nothing in this tranche
introduced a defect.

One finding that is NOT a defect and NOT this tranche's:
`INV-frozen-surfaces.md:736` fails on this container because its check runs
`git show` against a branch a shallow clone does not carry. All three failing
map documents are byte-identical to base. Proposed as a new shallow-clone
baseline row for `docs/AUDIT_BASELINES.md`; baselines belong to the audit
family, so it is not edited here.

## §6 Parked, each with a ready-to-send prompt

| id | what |
|---|---|
| P1 | the conjecturer form knob is gated by the qualification preset |
| P2 | the cheap form is reachable only after the expensive one fails |
| P3 | two undocumented seam documents (one was written by this tranche) |
| P4 | `render_batch_crit_pack` is a third renderer the shell never reaches |
| P5 | the judge, defender, variator and synthesizer seats |
| P6 | the second conjecturer kind and the second criticism kind |
| P7 | a model profile naming a SHELL, not a form |
| — | the frozen-surface-2 grant for the record write (`CHECKLIST.md` step 24) |

## §7 What this tranche does NOT claim

- That a conjecturer shell in a critic's seat produces useful criticism. It
  proves the shell is SWAPPABLE. Whether the swap is a good idea is an
  experiment, and the answer here is "not measured".
- That any of this makes runs better. The operator's success law is progress
  over a no-harness baseline, and no arm has run. `PREREG.md` says so in the
  document.
- That the brief's shape matters. FEASIBILITY §6.1 measured that forms differ
  by 41 points; nothing here measures that BRIEFS do. `PREREG.md` §5 states
  what would falsify the premise.
