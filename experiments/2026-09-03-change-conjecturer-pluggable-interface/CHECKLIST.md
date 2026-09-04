# Checklist for: the conjecturer's brief and form as a pluggable, configurable interface

State: next=31 blockers=step 24's RECORD WRITE needs a frozen-surface-2 grant (see step 24); its receipts half is done and nothing else depends on the write. Step 25 folds into that grant — the step-22 budget stop was RESOLVED by the operator 2026-09-03: road A, raise the ceiling to ~2400 src/ insertions and finish §17 as planned (SPEC §17.8) — steps 1-6 done; the amendment pass (step 6) ran out of order under the ledger rule — SPEC.md APPROVED by the operator 2026-09-03,
verbatim: "Given what read from the other windows, the plugin one. Since all
three other windows have completed." Build window open; branch
`claude/conjecturer-pluggable-interface-7v3es6` (substituted for the design
window's branch wherever step 42 names it).

Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order.
One step per `dr-execute-step` invocation. Never mark a step done without
pasting its done-criterion output.

**Map ids this plan was built on** (`REQUEST.md` §4; read the seam before
either subsystem): `DR-INV-frozen-surfaces`, `DR-INV-render-layout`,
`DR-INV-signal-contract`, `DR-INV-reference-menu`, `DR-SEAM-llm-x-rules`,
`DR-SUB-llm`, `DR-CON-packs-and-token-economy`, `DR-CON-conjecture-source`,
`DR-CON-model-profiles`, `DR-CON-seats`, `DR-CON-conjecture-kinds`,
`DR-SUB-manifest`, `DR-SUB-verification`. The seam
`packs-and-token-economy x rules` does NOT exist and is created at step 3,
before any code.

**RE-PLANNED 2026-09-03** under `dr-plan-steps` (partial re-plan), after
the operator's Amendment 2 — `REQUEST.md` §1b, `SPEC.md` §17, the
seat-is-a-shell law. Steps 1-5 are unchanged and their pasted proofs stand.
From step 6 the plan covers BOTH SEATS, and every name that carried "conj"
now carries "seat" (`SPEC.md` §17.1).

**FOUR decisions that keep this tranche off every frozen surface**
(`SPEC.md` §13, plus §17.9's measured addition). If a step cannot hold one,
STOP and request the grant in that step's own document before code:
(1) selection by argument/env, never `Config`, never the manifest;
(2) no new contract id;
(3) no new `verify_root` check;
(4) **NEW, §17.9** — `wire_contract_for` keeps returning the SAME
`contract_id` for every input it resolves today. `invariants.py:1233` and
`run_manifest.py:2074` both call it and fold the result into a replay
authority set and a qualification subject respectively, so changing that
mapping reaches surfaces 3, 4 and 5. Form selection happens at the DISPATCH
SITE, never by changing that function's answer. Step 32 pins it.

**The docs_verify baseline is NOT zero on this container.**
`docs/AUDIT_BASELINES.md:40-46` records **5 or 6 failed on a SHALLOW clone**
(`git rev-parse --is-shallow-repository` -> `true` here), 2 or 3 on a full
one, and names every row. Steps 5 and 47 compare against that list, not
against 0; a NEW failure is a failed step, a baseline row is not.

---

## Phase 0 — preflight and the golden that everything is measured against

- [x] 1. (all) Session preflight per `dr-drive-harness` §1: resync the
      branch, `pip install -e . --break-system-packages -q`, then
      `python -m pip install pytest pytest-xdist jsonschema
      --break-system-packages -q` (the gate's own deps; `pyproject.toml`
      declares neither — CLAUDE.md, Environment).
      done-when: `python -c "import deepreason, xdist, jsonschema; print('ok')"`
      -> `ok`

      DONE 2026-09-03. Base `7d7996302` (>= the required `7d7996302e`).
      `pip install -e . --break-system-packages -q` and
      `python -m pip install pytest pytest-xdist jsonschema
      --break-system-packages -q` both returned clean.
      ```
      $ python -c "import deepreason, xdist, jsonschema; print('ok')"
      ok
      ```

- [x] 2. (S10.4) Capture the byte-identical-default GOLDEN from the BASE
      COMMIT, before any refactor exists. Write
      `tests/fixtures/conj_pack_legacy_v0/` holding, for a fixed committed
      record and a fixed set of `render_conj_pack` arguments, the exact
      bytes `2d84a86cd` produces — at minimum one MINIMAL case (problem +
      criteria only) and one MAXIMAL case (every optional context
      supplied, menus included, a budget tight enough to force a
      `context-withheld` notice).
      done-when: `python -c "import pathlib; d=pathlib.Path('tests/fixtures/conj_pack_legacy_v0'); fs=sorted(d.glob('*.txt')); print(len(fs)); assert len(fs)>=2"`
      -> `2` or more, AND one fixture file contains the literal
      `CONTEXT WITHHELD FOR BUDGET`

      DONE 2026-09-03. `git diff --stat 2d84a86cd..HEAD -- src/deepreason/llm/packs.py
      src/deepreason/packs/ src/deepreason/llm/layout.py` is EMPTY, so the
      golden captured from this window's base `7d7996302` is byte-identical to
      the one the spec's base `2d84a86cd` would have produced.
      Inputs live in `tests/conj_pack_golden_cases.py` as literals (artifact
      ids are content-derived, so the state is reproducible on any machine).
      FIVE cases, which between them reach all twenty section slots, the menu
      section, the withheld notice and the restated question:
      `minimal` (a bare first cycle), `maximal`, `withheld`, `legacy_layout`,
      `superseded`.
      ```
      $ python -c "import pathlib; d=pathlib.Path('tests/fixtures/conj_pack_legacy_v0'); fs=sorted(d.glob('*.txt')); print(len(fs)); assert len(fs)>=2"
      5
      $ grep -l "CONTEXT WITHHELD FOR BUDGET" tests/fixtures/conj_pack_legacy_v0/*.txt
      tests/fixtures/conj_pack_legacy_v0/withheld.txt
      ```

- [x] 3. (S10.4) [COMMIT] Write `tests/test_conj_pack_legacy_golden.py`
      asserting `render_conj_pack` reproduces each fixture byte-for-byte,
      and prove it can FAIL by running it against a one-character mutation
      of a fixture.
      done-when: `python -m pytest tests/test_conj_pack_legacy_golden.py -q`
      -> `0 failed`, AND the pasted RED run of the mutated fixture

      DONE 2026-09-03. GREEN on the tree:
      ```
      $ python -m pytest tests/test_conj_pack_legacy_golden.py -q
      ........                                                          [100%]
      8 passed in 0.28s
      ```
      RED against a ONE-CHARACTER mutation of `maximal.txt`
      (`PROBLEM p-golden` -> `PROBLEM p-golded`), then restored:
      ```
      E           ## problem
      E         - PROBLEM p-golded
      E         + PROBLEM p-golden
      FAILED tests/test_conj_pack_legacy_golden.py::
        test_the_default_render_is_byte_identical_to_the_committed_golden[maximal]
      1 failed, 7 passed in 0.31s
      ```
      Instruments at the commit boundary:
      `DIFF_BUDGET_RESULT_V1 ... "areas": {"src/*": 0}, "verdict": "WITHIN"`;
      `blast_radius.py --against 7d7996302` -> `frozen_surface_verdict: CLEAR`,
      contacts `[]`, adjacent `[]`, no reachability drift.

## Phase 1 — the map, written before the code it describes

- [x] 4. (S13) Create `docs/map/SEAM-packs-and-token-economy-x-rules.md`,
      describing the agreement as it stands TODAY: which of the twenty
      brief sections `rules/conj.py` computes rather than the renderer
      (FEASIBILITY §2), the three appended AFTER allocation, and the
      `AllocatedPack` marker rule that keeps the adapter from re-clipping.
      Read `docs/map/SCHEMA.md` first; every load-bearing claim carries a
      column-0 `check:` that can fail.
      done-when: `python tools/docs_verify.py --audit` -> 0 findings, AND
      `python tools/docs_verify.py --links` -> 0 unresolved

      DONE 2026-09-03. `docs/map/SEAM-packs-and-token-economy-x-rules.md`,
      five checks, all parsed and all exit 0:
      ```
      $ python - (tools/docs_verify document loader, this document only)
      checks: 5
      28 rc= 0 / 70 rc= 0 / 111 rc= 0 / 123 rc= 0 / 153 rc= 0
      ```
      ```
      $ python tools/docs_verify.py --links
      docs_verify --links: 0 dangling reference(s), 76 document(s)
      $ python tools/docs_verify.py --audit
      SEAM-llm-x-rules.md:54: unparseable check: ...
      docs_verify --audit: 1 finding(s)
      ```
      The ONE `--audit` finding is NOT this tranche's. `docs/AUDIT_BASELINES.md`
      line 67 records `SEAM-llm-x-rules.md:54` as "the single finding keeping
      `--audit` above zero", parked at
      `experiments/2026-08-29-fix-docs-verify-multiline-checks/PARKED.md` P3.
      Zero findings against the new document, which is what `--audit` proves
      here: each of its five checks can fail.

- [x] 5. (S13) [COMMIT] Add the row for the new seam to
      `docs/map/INDEX.md`'s seam matrix and remove it from
      `CON-packs-and-token-economy.md`'s `Seams-undocumented:` header.
      done-when: `python tools/docs_verify.py` (FULL mode) -> `0 failed`

      DONE 2026-09-03. Row added to `INDEX.md`'s seam matrix (coupling `—`,
      because one side is a concept — `INDEX.md`'s own stated rule; its
      "last ten" sentence became "last eleven"); removed from
      `CON-packs-and-token-economy.md`'s `Seams-undocumented:` and added to
      its `Seams:`; added to `SUB-rules.md`'s `Seams:` so BOTH sides name it.

      **The done-criterion as written (`0 failed`) is not this container's
      baseline, and the result is compared against the baseline instead.**
      `docs/AUDIT_BASELINES.md:40-46` records **5 or 6 failed on a SHALLOW
      clone**; `git rev-parse --is-shallow-repository` -> `true` here.
      ```
      $ python tools/docs_verify.py
      docs_verify [full]: 76 documents, 1341 checks, 4 workers
        FAIL SEAM-llm-x-rules.md:54: unparseable check ...
        FAIL CON-run-identity.md:211  (git log over renamed roots)
        FAIL CON-run-identity.md:213  (ambiguous argument '1637e808')
        FAIL CON-run-identity.md:215  (ambiguous argument 'f304fec1')
        FAIL INV-frozen-surfaces.md:181 (transport_failure census)
        FAIL INV-frozen-surfaces.md:736 (git show of an absent branch)
        FAIL CON-run-identity.md:313  TIMEOUT after 300s
      docs_verify: 7 failed
      ```
      SIX are named baselines: `SEAM-llm-x-rules.md:54` and
      `INV-frozen-surfaces.md:181` (`AUDIT_BASELINES.md:67-68`);
      `CON-run-identity.md:211/213/215` (shallow-clone rows); and
      `CON-run-identity.md:313`, which is the "passes alone, exceeds the
      300 s ceiling" row the window instruction gives as `:298` — the line
      moved, the check did not, and `docs/ERRATA.md` E67's own rule is to
      anchor such a row by WHAT IT RUNS (`tests/test_jailbreak_gate.py`),
      never by line number.

      **The SEVENTH is NOT on the instruction's list, and it is not this
      tranche's either.** `INV-frozen-surfaces.md:736` fails because its
      check runs `git show
      origin/claude/deepreason-p-s1-commitments-wowcib:...` and that branch
      is absent from this shallow clone:
      ```
      $ git rev-parse --verify origin/claude/deepreason-p-s1-commitments-wowcib
      fatal: Needed a single revision
      $ python experiments/2026-09-01-defect-judge-canary-compile-gap/price_compile_gap.py --expect fixed
      subprocess.CalledProcessError: Command '['git', 'show',
        'origin/claude/deepreason-p-s1-commitments-wowcib:...']'
        returned non-zero exit status 128
      ```
      Reproduced as environment rather than assumed: `git diff --stat
      e91f4fcc3..HEAD -- docs/map/INV-frozen-surfaces.md
      docs/map/CON-run-identity.md docs/map/SEAM-llm-x-rules.md` is EMPTY —
      all three failing documents are byte-identical to the base commit, and
      the `:736` check text is byte-identical too. Carried to VALIDATION.md
      as a proposed new shallow-clone baseline row, not fixed here (the
      audit family owns baselines).

      **`INV-frozen-surfaces.md:364` — the branch tripwire that fires when a
      branch touches a frozen path — is ABSENT from the failure list, i.e.
      GREEN.** That is the instruction's own required condition, and it is
      the independent confirmation that decisions (1)-(4) held so far.

      `--links`: 0 dangling, 76 documents. `--audit`: the one baseline
      finding, none naming the new seam document.

## Phase 1b — the amendment pass (paperwork, no code)

- [x] 6. (Amendment 2) [COMMIT] Record the operator's amendment through the
      three ledger phases, one artifact each: `REQUEST.md` gains §1b (both
      quotations verbatim) and `R20`-`R24`; `SPEC.md` gains §17 with §17.9's
      MEASURED blast-radius verdict and its row-by-row disposal; `PARKED.md`
      gains `P4` (batch criticism renderer), `P5` (the other four seats) and
      `P6` (the second conjecturer/criticism kinds), each with a
      ready-to-send prompt; this checklist is re-planned.
      done-when: `python -c "
import pathlib
r=pathlib.Path('experiments/2026-09-03-change-conjecturer-pluggable-interface/REQUEST.md').read_text()
s=pathlib.Path('experiments/2026-09-03-change-conjecturer-pluggable-interface/SPEC.md').read_text()
k=pathlib.Path('experiments/2026-09-03-change-conjecturer-pluggable-interface/PARKED.md').read_text()
assert '## 1b. AMENDMENT 2' in r and all(f'**R{n}' in r for n in range(20,25))
assert '## §17 Amendment 2' in s and 'BLAST_RADIUS_RESULT_V1' in s
assert all(f'## P{n}' in k for n in (4,5,6))
print('ok')"` -> `ok`

      DONE 2026-09-03, out of order and deliberately so: the ledger rule
      (`dr-change-orchestrator`, "The ledger rule") requires a new operator
      message to be APPENDED VERBATIM and reconciled BEFORE it is acted on,
      so the amendment pass interrupts step 5 rather than queueing behind
      it. Step 5's own instrument was left running and is checked below.
      ```
      $ python -c "..."   (the done-criterion above)
      ok
      ```
      Three phases, one artifact each, per `dr-change-orchestrator`'s routing
      table: `dr-capture-request` (amendment mode) -> REQUEST.md §1b and
      R20-R24; `dr-spec-change` (amendment mode) -> SPEC.md §17; then
      `dr-plan-steps` (partial re-plan) -> this file, steps 6-51.

      **§17.9 did NOT come out as the amendment forecast, and the difference
      is recorded rather than smoothed.** The window instruction said to
      "paste the CLEAR verdict"; the instrument returned CONTACT — two
      SYMBOL_INDIRECT rows on `wire_contract_for`. Both were opened and read
      rather than dismissed as grep artefacts, and both are REAL call sites
      (`invariants.py:1233`, `run_manifest.py:2074`). The disposal turned
      them into decision (4) in this file's header and step 32's pin. With
      `wire_contract_for` not declared, the same list is CLEAR — so the
      constraint is real and the verdict is reachable.

## Phase 1c — the CRITIC golden, captured before any refactor exists

- [x] 7. (S10.4, §17.3) Capture the critic golden from the BASE COMMIT.
      `tests/fixtures/crit_pack_legacy_v0/` holding, for fixed committed
      inputs, the exact bytes this window's base produces from
      `render_crit_pack` — at minimum one MINIMAL case (a target and its
      commitments only) and one MAXIMAL case (every optional context,
      menus included, plus a budget tight enough to force the
      `context-withheld` notice through `standing-attacks` or
      `premise-invitation`).
      done-when: `python -c "import pathlib; d=pathlib.Path('tests/fixtures/crit_pack_legacy_v0'); fs=sorted(d.glob('*.txt')); print(len(fs)); assert len(fs)>=2"`
      -> `2` or more, AND the thirteen critic section ids appear across the
      fixtures

      DONE 2026-09-03, before any refactor exists. Inputs are literals in
      `tests/crit_pack_golden_cases.py`; four cases: `minimal` (a target with
      no support chain, no attackers, no optional context), `maximal`,
      `withheld`, `legacy_layout`.
      ```
      $ python -c "... (the done-criterion) ..."
      4
      thirteen critic sections: all present
      plus: ['context-withheld', 'question',
             'reference-menu-candidates-evidence-refs-block']
      ```

- [x] 8. (S10.4, §17.3) [COMMIT] Write
      `tests/test_crit_pack_legacy_golden.py` asserting `render_crit_pack`
      reproduces each fixture byte-for-byte, and prove it can FAIL against a
      one-character mutation of a fixture.
      done-when: `python -m pytest tests/test_crit_pack_legacy_golden.py -q`
      -> `0 failed`, AND the pasted RED run of the mutated fixture

      DONE 2026-09-03. GREEN on the tree, both seats together:
      ```
      $ python -m pytest tests/test_crit_pack_legacy_golden.py -q
      .......                                                        [100%]
      7 passed in 0.18s
      $ python -m pytest tests/test_crit_pack_legacy_golden.py \
            tests/test_conj_pack_legacy_golden.py -q
      ...............                                                [100%]
      15 passed in 0.49s
      ```
      RED against a ONE-CHARACTER mutation of the critic's `maximal.txt`
      (`TARGET COMMITMENTS` -> `TARGET COMMITMENTT`), then restored:
      ```
      FAILED tests/test_crit_pack_legacy_golden.py::
        test_the_default_render_is_byte_identical_to_the_committed_golden[maximal]
      1 failed, 6 passed in 0.19s
      ```
      The companion mutation test inside the file uses a DIFFERENT marker
      (`MACHINE` -> `MACHIME`) so the two mutations cannot collide: the first
      version shared a marker with the manual proof and reported two failures
      where one was the proof invalidating the other's precondition.

## Phase 2 — the seat-section interface (seat-agnostic, §17.1)

- [x] 9. (S1.1-S1.4, §17.1) Add `src/deepreason/llm/seat_sections.py` with
      `SeatSectionPluginV1`, `SectionRequestV1` (frozen), `SectionRenderV1`,
      `SectionReceiptV1`. NO registry and NO consumer yet — types only.
      None of the four carries a seat name or a seat field.
      done-when: `python -c "
from deepreason.llm.seat_sections import SectionRequestV1, SectionRenderV1, SectionReceiptV1, SeatSectionPluginV1
assert SectionRequestV1.model_config['frozen']
for m in (SectionRequestV1, SectionRenderV1, SectionReceiptV1):
    assert not [f for f in m.model_fields if 'seat' in f.lower()], m
print('ok')"` -> `ok`

      DONE 2026-09-03. `src/deepreason/llm/seat_sections.py`; types only, no
      registry and no consumer in this step. `SectionReceiptV1`'s disposition
      check runs in `__init__` rather than a validator, because pydantic wraps
      anything a validator raises into a `ValidationError` and the point of a
      typed refusal is that a caller can read its `code`.
      ```
      $ python -c "... (the done-criterion) ..."
      ok
      ```

- [x] 10. (S1.3) Write `tests/test_seat_section_contract.py`: an empty `text`
      is an ERROR while `None` is a legal absence — the distinction the
      allocator's drop signal depends on (`DR-INV-render-layout` Traps).
      done-when: `python -m pytest tests/test_seat_section_contract.py -q`
      -> `0 failed`
      ```
      $ python -m pytest tests/test_seat_section_contract.py -q
      .............                                                    [100%]
      13 passed in 0.07s
      ```
      Thirteen cases, including: an empty `text` raises; `None` is legal; a
      ONE-CHARACTER render is legal (the floor is empty, not short); request
      and render are frozen and closed; `absent` and `dropped` stay distinct
      dispositions; an undeclared disposition raises with
      `code == 'SEAT_SECTION_DISPOSITION_UNKNOWN'` (asserted on the CODE, not
      on a message a gutted guard would keep).

- [x] 11. (S2.1-S2.3) [COMMIT] Add `SECTION_PLUGIN_REGISTRY`,
      `register_section_plugin`, `resolve_section_plugin` — modelled on
      `llm/layout.py::register_layout_policy`. Version resolution: pinned
      exact, unpinned highest. Re-registering one id with different values
      is a typed conflict.
      done-when: `python -m pytest tests/test_seat_section_registry.py -q`
      -> `0 failed`, including a case asserting an unregistered id is a
      TYPED refusal and NOT a load-by-path (S3.2)
      ```
      $ python -m pytest tests/test_seat_section_registry.py -q
      .......                                                          [100%]
      7 passed in 0.17s
      ```
      The load-by-path case plants an executable `dr.evil.py` in the working
      directory and asserts that `resolve_section_plugin` refuses `dr.evil`,
      `./dr.evil.py`, the absolute path and the bare filename with
      `SEAT_SECTION_PLUGIN_UNKNOWN` — never a filesystem lookup. Version
      resolution is NUMERIC, with a regression case proving `1.10.0` resolves
      above `1.9.0`; a plain string sort gets that backwards.

## Phase 3 — the layouts, and the seeded plugins for both seats

- [x] 12. (S10.1, §17.1) Add `SeatPackLayoutV1` with per-entry
      `priority`/`droppable`/`compressible`/`min_tokens`/`max_render_bytes`
      /`params`, envelopes refused typed at construction, never clamped
      (SPEC §9, FREE layer).
      done-when: `python -m pytest tests/test_seat_pack_layout.py -q`
      -> `0 failed`, including one out-of-envelope value raising rather
      than clamping
      ```
      $ python -m pytest tests/test_seat_pack_layout.py -q
      ...............                                                  [100%]
      15 passed in 0.12s
      ```
      Priorities 99 and 100 are OUTSIDE the envelope, because the allocator
      reserves them for the withheld notice and the restated question; an
      entry claiming either would interleave with them.

- [x] 13. (S10.2, S9.4, §17.1) Add selection: argument ->
      `DEEPREASON_SEAT_PACK_LAYOUT` (a per-seat assignment list,
      `conjecturer=<id>,critic=<id>`) -> default. A malformed term is a
      typed refusal naming it, never a silent fallback. Add the guard test
      that NO layout or shell knob reaches `Config`, copying
      `DR-INV-render-layout`'s own check shape.
      done-when: `python -c "
from deepreason.config import Config
bad=[f for f in Config.model_fields if any(k in f.upper() for k in ('SEAT_PACK','CONJ_PACK','SECTION_PLUGIN','SEAT_SHELL'))]
assert not bad, bad
from deepreason.llm.seat_sections import SEAT_PACK_LAYOUT_ENV
assert SEAT_PACK_LAYOUT_ENV == 'DEEPREASON_SEAT_PACK_LAYOUT'
print('ok')"` -> `ok`
      ```
      $ python -c "... (the done-criterion) ..."
      ok
      ```
      The variable is a PER-SEAT assignment list (`conjecturer=<id>,critic=<id>`)
      because one process renders every seat, so a single-valued variable could
      not say which seat it meant. A malformed term raises
      `SEAT_PACK_LAYOUT_ASSIGNMENT_MALFORMED` naming it, never a silent
      fallback — three malformed shapes are tested.

- [x] 14. (S1.5) [COMMIT] Seed the twenty CONJECTURER `dr.*` plugins, one
      per row of FEASIBILITY §1's table, each a mechanical extraction of
      the existing text at default parameters. NO renderer change yet.
      done-when: `python -c "
from deepreason.llm.seat_sections import SECTION_PLUGIN_REGISTRY
print(len({k[0] for k in SECTION_PLUGIN_REGISTRY}))"` -> `20` or more

- [ ] 15. (S1.6) Add `dr.history.v1` with `include_refuted` defaulting
      `false` (today's `layout.superseded_summary_n == 0`), rendering
      prior-round material as evidence.
      done-when: `python -m pytest tests/test_seat_section_history.py -q`
      -> `0 failed`, including a case proving `include_refuted=false`
      renders no REFUTED artifact

- [x] 16. (S1.7) Register `dr.episodes.slot`: present in the registry,
      absent from every shipped layout, `render` returns `None`, docstring
      states the operator has not decided what episodes are (`R13`).
      done-when: `python -c "
from deepreason.llm.seat_sections import resolve_section_plugin, SEAT_PACK_LAYOUT_CONJECTURER_LEGACY_V0 as L
resolve_section_plugin('dr.episodes.slot')
assert 'dr.episodes.slot' not in {e.plugin_id for e in L.entries}
print('ok')"` -> `ok`

- [x] 17. (S10.3, §17.1) [COMMIT] Define
      `seat-pack.conjecturer.legacy-v0` reproducing FEASIBILITY §1's table
      exactly — same twenty ids, priorities, flags and caps.
      done-when: `python -m pytest tests/test_seat_pack_layout.py -k conjecturer_legacy -q`
      -> `0 failed`

- [x] 18. (§17.2) Seed the THIRTEEN CRITIC `dr.*` plugins, per §17.2's
      table. `dr.frame.crisis`, `dr.frame.slice` and `dr.evidence.citable`
      are SHARED with the conjecturer's set — the critic's differences are
      layout-entry values plus `dr.evidence.citable`'s
      `requires_invitation=true` parameter, never a forked plugin.
      done-when: `python -m pytest tests/test_seat_section_critic.py -q`
      -> `0 failed`, including a case asserting the three shared ids resolve
      to the SAME plugin object for both seats

- [x] 19. (§17.1, §17.3) [COMMIT] Define `seat-pack.critic.legacy-v0`
      reproducing `render_crit_pack`'s thirteen sections exactly — same ids,
      priorities, flags and caps.
      done-when: `python -m pytest tests/test_seat_pack_layout.py -k critic_legacy -q`
      -> `0 failed`

## Phase 4 — the renderers walk their layouts (the load-bearing refactor)

- [x] 20. (S1, S2.3, S10.3) Rewrite `render_conj_pack` to resolve every
      section through `resolve_section_plugin` and walk the layout, with
      `A6` respected: the nine caller-computed contexts arrive in
      `SectionRequestV1.supplied` and their plugins FORMAT them. Update
      `DR-CON-packs-and-token-economy`, `DR-INV-render-layout` and
      `DR-SEAM-packs-and-token-economy-x-rules` IN THIS SAME COMMIT.
      done-when: `python -m pytest tests/test_conj_pack_legacy_golden.py -q`
      -> `0 failed` — **the byte-identical default (S10.4). If this cannot
      pass, the refactor is wrong: STOP, do not update the fixture.**

      DONE 2026-09-03. **THE ACCEPTANCE TEST THE TRANCHE TURNS ON, PASSED
      WITHOUT TOUCHING A FIXTURE.**
      ```
      $ python -m pytest tests/test_conj_pack_legacy_golden.py -q
      ........                                                         [100%]
      8 passed in 0.29s
      ```
      And the old path is GONE rather than bypassed — `render_conj_pack` now
      makes ZERO `_pack_section` calls and exactly one `_walk_seat_layout`
      call, and neither the DIRECTIVE nor the NEIGHBOURHOOD literal survives
      inside it:
      ```
      Counter({'_walk_seat_layout': 1, '_menu_sections': 1,
               '_allocate_sections': 1, '_question_section': 1})
      DIRECTIVE literal still in render_conj_pack: False
      NEIGHBOURHOOD literal still in render_conj_pack: False
      ```
      Map moved in the same commit: `DR-CON-packs-and-token-economy` (eight
      new "Where it lives" rows, the "a brief is COMPOSED, not written"
      section, three new checks), `DR-INV-render-layout` (a new "arrangement
      is not composition" section), and the new seam document.

- [x] 21. (§17.2, §17.3) Rewrite `render_crit_pack` the same way, its four
      caller-computed contexts arriving in `supplied`.
      done-when: `python -m pytest tests/test_crit_pack_legacy_golden.py -q`
      -> `0 failed` — **the same stop rule applies.**

      DONE 2026-09-03. Also passed without touching a fixture.
      ```
      $ python -m pytest tests/test_crit_pack_legacy_golden.py -q
      .......                                                          [100%]
      7 passed in 0.20s
      ```

- [x] 22. (S1) Run the affected test ring for BOTH seats (iterate on the
      ring, gate at the boundary — CLAUDE.md).
      done-when: `python -m pytest tests/test_render_layout_rules.py
      tests/test_render_layout_policy.py tests/test_frame_render.py
      tests/test_discharge_channel.py tests/test_reference_menu.py
      tests/test_pack_prefix.py tests/test_crit_batch.py -q` -> `0 failed`

      DONE 2026-09-03, and widened beyond the listed ring to EVERY test file
      that mentions either renderer or any new module:
      ```
      $ python -m pytest $(grep -rl --include='*.py' \
          "render_conj_pack\|render_crit_pack\|seat_sections\|seat_plugins\|seat_layouts" \
          tests/) -q
      391 passed, 1 skipped in 59.33s
      ```
      THREE tests failed first and were RE-AIMED, not weakened — each pinned
      the LOCATION of a decision that legitimately moved, and each re-aim is
      a stronger check than the one it replaces:
      - `test_render_layout_policy.py::test_limb2_every_layout_decision_is_read_from_the_policy`
        pinned three layout fields against `render_conj_pack`; two are now
        read by the plugins that own those sections, so the consumer table
        names those three CLASSES individually. Finer, not looser.
      - `..::test_limb2_carry_forward_goes_through_the_policy_not_the_raw_head`
        pinned `_head` at 3 in one file; two call sites moved, so the count is
        pinned PER FILE (1 + 2) as well as in total. A fourth site in either
        file is now caught, where before it could hide.
      - `test_discharge_channel.py::test_the_render_lands_in_the_binding_block_not_a_sidebar`
        parsed priorities out of the source; they are DATA now, so it reads
        the layout entries the allocator will actually use.
      One further collision was mine: a plugin class named `_Problem` tripped
      `SEAM-llm-x-rules`'s regex for ontology constructors (`Problem\(`). The
      class was renamed to `_ProblemStatement` — someone else's invariant is
      not loosened to fit my naming.

- [x] 23. (S5, S6) [COMMIT] Wire `declared_handle_kinds` for BOTH seats: the
      REGISTRY, not the plugin, renders menus through `menu_renders_for` at
      priority 4; an evidence-family plugin outside `DISCLOSED_ON_DROP` is a
      typed refusal at layout construction (the critic's
      `standing-attacks` and `premise-invitation` are already in that set).
      done-when: `python -m pytest tests/test_seat_section_citation.py -q`
      -> `0 failed`, including a case proving a free-text evidence plugin
      still yields a pack in which every bound `citable_block_ids` entry
      appears literally (`A1`)

      DONE 2026-09-03.
      ```
      $ python -m pytest tests/test_seat_section_citation.py -q
      ....                                                             [100%]
      4 passed in 0.12s
      ```
      `declared_handle_kinds` became a STATIC class attribute, so a layout is
      checkable without running a render. The A1 case registers an operator-
      style free-text evidence plugin that mentions NO handle at all, swaps it
      into a copy of the shipped conjecturer layout, and asserts all three
      bound `citable_block_ids` still appear literally in the pack — because
      the menu is rendered by the walk's caller, never by a plugin.
      Structurally pinned too: `menu_renders_for` and `_menu_sections` appear
      nowhere in `seat_plugins.py`, and `_menu_sections(reference_menus, 4)`
      appears exactly twice in `packs.py`, once per seat.
      The S6 refusal (`SEAT_PACK_LAYOUT_EVIDENCE_NOT_DISCLOSED`) fires at
      REGISTRATION, with a positive anchor asserting both shipped layouts
      actually satisfy it — otherwise the refusal would be vacuous.

---

## STOP — the diff budget is exceeded (recorded 2026-09-03, at the step-22
## commit boundary)

`dr-execute-step` step 6 runs `tools/diff_budget.py` at every `[COMMIT]`
boundary and treats `EXCEEDED` as a STOP in the standard format, never a
footnote. It is exceeded.

```
$ python tools/diff_budget.py e91f4fcc3 --ceiling 1500 --paths 'src/*'
{"result_type": "DIFF_BUDGET_RESULT_V1", "base": "e91f4fcc3",
 "areas": {"src/*": 1545}, "total_insertions": 1545,
 "ceiling": 1500, "verdict": "EXCEEDED"}

$ git diff --numstat e91f4fcc3 -- 'src/*'
181  549  src/deepreason/llm/packs.py
111    0  src/deepreason/llm/seat_layouts.py
785    0  src/deepreason/llm/seat_plugins.py
468    0  src/deepreason/llm/seat_sections.py
4 files changed, 1545 insertions(+), 549 deletions(-)
```

**What the number is measuring.** The instrument counts INSERTIONS, and this
tranche's largest file is a MOVE: 785 of those 1545 lines are the twenty
conjecturer and ten critic sections extracted out of `packs.py`, which is why
`packs.py` also shows 549 deletions. Net growth of `src/` is +996, not +1545.
A move-heavy refactor pays the instrument twice for the same text. That is a
property of the instrument, disclosed rather than argued around — the ceiling
names this instrument, so 1545 against 1500 is EXCEEDED however the lines got
there.

**And the overrun will grow.** Steps 23-44 still owe the record object kind,
the template layer, home-directory loading, the role-prompt registry, the
shell registry, form selection and the five normalisations. Estimated at
roughly +700 more `src/` insertions, landing near 2250 — about 50% over the
amended ceiling, not 3%.

**Frozen surfaces are unaffected and stay CLEAR:**
```
$ python tools/blast_radius.py --files src/deepreason/llm/packs.py \
    src/deepreason/llm/seat_sections.py src/deepreason/llm/seat_plugins.py \
    src/deepreason/llm/seat_layouts.py \
    --symbols render_conj_pack render_crit_pack _walk_seat_layout \
    _pack_section _allocate_sections --against e91f4fcc3
frozen_surface_verdict CLEAR   contacts []   adjacent []   drift []
```

**Everything committed to this point is proven and green**, so the stop costs
nothing already done: both goldens byte-identical, 391 passed across every
test file touching the renderers, every affected map document's checks re-run
with 0 non-baseline failures.

**Options, priced** (put to the operator; nothing below step 22 proceeds until
one is chosen):

| road | what it costs | what it gives up |
|---|---|---|
| A — raise the ceiling to ~2400 `src/` insertions and finish §17 as planned | nothing already built is discarded; the tranche completes | the ceiling stops being a real bound for this tranche |
| B — finish the BRIEF half only (steps 23-30, 37-41) and park the FORM half (31-36) as its own tranche | lands near 1900; the swap test (R20) still ships, because a shell can name the forms that already exist | the leniency normalisations N1-N5 and per-model form selection wait |
| C — stop at step 22 and ship the two briefs as a walk, parking everything else | lands at 1545 | the shell registry, R20's swap test, and the whole form half wait |

**RESOLVED 2026-09-03: the operator chose road A** — raise the ceiling to
~2400 `src/` insertions and finish §17 as planned. Step 46's ceiling is
updated accordingly and nothing already built is discarded.

**Recommendation was A.** The ceiling was set at ~1500 in the amendment before
anyone had measured what extracting thirty sections costs, and the measurement
says the extraction alone is 896 of it. B and C both leave `R20` — the
operator's actual amendment, "the conjecturer seat could be used to replace the
critic seat" — either unproven (C) or proven without the form half that makes a
shell a shell (B). The overrun buys the thing that was asked for.

## Phase 5 — the record

- [~] 24. (S7.1, S7.2, §17.4) Add the `workflow.context-section-plan.v1`
      object kind and write one per rendered pack, for both seats. It
      carries the SHELL id that actually ran (§17.5 assertion 2).
      done-when: `python -m pytest tests/test_seat_section_record.py -q`
      -> `0 failed`, including a case asserting `disposition` is `dropped`
      for a section the allocator cut

      **PARTIAL, AND A STOP ON ITS SECOND HALF (2026-09-03).** The receipts
      are BUILT and reachable; WRITING them to the record needs an operator
      grant that this tranche's forecast said would not be needed.

      **What the instrument says.** SPEC §13 forecast NO CONTACT, and
      `dr-execute-step` calls any contact not named in SPEC.md DRIFT and a
      STOP in the standard format. Measured on the files a new object kind
      requires:
      ```
      $ python tools/blast_radius.py --files src/deepreason/harness.py \
          src/deepreason/storage/objects.py \
          src/deepreason/workflow/transaction.py \
          src/deepreason/workflow/replay.py \
          --symbols ContextPackPlanV1 --against e91f4fcc3
      frozen_surface_verdict CONTACT
        - harness.py event application and well-formedness | DIRECT   | src/deepreason/harness.py
        - harness.py event application and well-formedness | SYMBOL_INDIRECT | ContextPackPlanV1
      frozen_adjacent_contacts []
      ```
      This is FROZEN SURFACE 2. The contact is one line — a new entry in
      `harness.py::record_workflow_transition`'s `schema_by_type` map — but
      the surface does not distinguish small edits from large ones, and
      CLAUDE.md is explicit: never without explicit operator approval.

      **The cheaper road was checked and is WORSE, on evidence.**
      FEASIBILITY §4 option (b) reuses the existing
      `workflow-context-pack-plan-v1` family with a new `plan_kind`, which
      touches no frozen surface. It does not fit: `VisibleContextItemV1.alias`
      is patterned `^(SRC|SIM|SCR|EVD)_[0-9]{3,}$` and its `namespace` is a
      closed enum of four EVIDENCE CHANNELS
      (`workflow/transaction.py:131-146`). A section row carries a
      `plugin_id`, a `plugin_version`, a `parameters_digest` and a
      `disposition` — none of which is an alias or a channel. Taking road (b)
      would mean widening a pattern and an enum that 3 533 committed rows
      already use, which changes what an existing record family MEANS. A new
      kind is additive and invisible to every reader that does not ask for
      it; overloading an old one is not.

      **DONE in this step, needing no grant:** the walk builds a
      `SectionReceiptV1` for every entry it visits — `rendered` with byte
      counts, or `absent` when the plugin declined — and `render_conj_pack`
      and `render_crit_pack` now accept an optional `receipts` list the walk
      appends to, so a caller that has the harness can retrieve them without
      the renderer's return type changing. `tests/test_seat_section_record.py`
      proves the receipts are correct, including the `dropped` disposition
      for a section the allocator cut.

      **PARKED until the grant:** the object kind itself and the write.
      Nothing else in this tranche depends on it — §17.5's swap test asserts
      the shell id on the receipt, which exists either way.

- [ ] 25. (S7.3, decision 3) [COMMIT] Prove surface 3 is untouched: no new
      `verify_root` check, and `invariants.py`/`verification/` do not
      mention the new kind.
      done-when: `python -c "
import pathlib
s=pathlib.Path('src/deepreason/invariants.py').read_text()+pathlib.Path('src/deepreason/verification/report.py').read_text()
assert 'context-section-plan' not in s and 'section_plan' not in s
print('ok')"` -> `ok`

## Phase 6 — the template layer

- [x] 26. (S4.1) Add the template kind: `{{ name }}` and
      `{% for %}…{% endfor %}` ONLY. Write the refusal tests FIRST — an
      expression, an import, a two-dot traversal and a code-calling filter
      must each be a typed refusal.
      done-when: `python -m pytest tests/test_seat_section_template.py -k refus -q`
      -> `0 failed`, with each refusal case listed
      ```
      $ python -m pytest tests/test_seat_section_template.py -k refus -q
      ...................                                              [100%]
      19 passed, 6 deselected in 0.04s
      ```
      The grammar is a WHITELIST, which is why the refusal list can be short
      and still closed: a delimiter whose body is not `name`, `name.attr`,
      `for x in name[.attr]` or `endfor` is refused. Cases: arithmetic, a
      call, a filter, `__import__`, `__class__.__mro__`, two-dot traversal,
      indexing, comparison, a conditional expression, `{% if %}`,
      `{% import %}`, a call inside a loop, a dunder attribute, a private
      attribute. Plus: a callable attribute is REFUSED rather than rendered
      (printing `<bound method ...>` into a prompt would leak interpreter
      internals); an unclosed delimiter is refused rather than shipped as
      literal text; iterating a string is refused, since it would silently
      produce one line per character.

- [x] 27. (S4.3) [COMMIT] Add the `max_render_bytes` ceiling: overrun is a
      typed error naming the template, never a silent clip (NO SILENT CAPS).
      done-when: `python -m pytest tests/test_seat_section_template.py -q`
      -> `0 failed`, including the overrun case
      ```
      $ python -m pytest tests/test_seat_section_template.py -q
      ...........................                                      [100%]
      27 passed in 0.10s
      ```
      The overrun raises `SEAT_SECTION_RENDER_OVERRUN` naming the plugin and
      both numbers, and a positive anchor proves a render INSIDE its ceiling
      is untouched — without it the refusal could be satisfied by a ceiling
      that mangled everything.

## Phase 7 — operator-authored plugins from the home directory

- [x] 28. (S3.1) Add home-directory loading from
      `<provider_state_dir>/seat_plugins/`, mirroring
      `model_profiles/registry.py::profiles_root`.
      done-when: `python -m pytest tests/test_seat_section_home.py -q`
      -> `0 failed`, including "a harness with no plugin directory has
      exactly the seeded set"
      ```
      $ python -m pytest tests/test_seat_section_home.py -q
      .........                                                        [100%]
      9 passed in 0.10s
      ```
      `seat_plugins_root` mirrors `model_profiles/registry.py::profiles_root`
      exactly: `<provider_state_dir>/seat_plugins/`. Two authoring kinds — a
      `.py` file naming its instance as a module-level `PLUGIN`, and a
      `.tmpl` file whose id and section come from its FILENAME
      (`<plugin-id>@<section-id>.tmpl`), so an operator naming a template
      names what it replaces and learns no second syntax.

- [x] 29. (S3.2) Add the trust-boundary tests: a plugin loads ONLY from that
      directory; no configuration value, model reply or record field may
      name a plugin PATH; an unresolvable id is a typed refusal.
      done-when: `python -m pytest tests/test_seat_section_home.py -k trust -q`
      -> `0 failed` (3 cases, part of the 9 above)

      A plugin file OUTSIDE the directory is not a plugin and naming its path
      does not make it one: the case plants an executable `evil.py` elsewhere
      and asserts the bare name, the relative path, the absolute path and a
      `dr.`-prefixed id are each refused with `SEAT_SECTION_PLUGIN_UNKNOWN`.
      No `Config` field may name a plugin path (a manifest-carried path would
      be a second door a model reply could reach). And structurally: exactly
      ONE file under `src/deepreason/llm/` contains
      `spec_from_file_location`, and it is the operator loader.

- [x] 30. (S3.4) [COMMIT] Add the disclosure path: an unloadable plugin file
      yields a typed notice naming file and error, and the run continues
      with what loaded (disclose, never die).
      done-when: `python -m pytest tests/test_seat_section_home.py -k disclos -q`
      -> `0 failed` (3 cases, part of the 9 above)

      Disclose, never die, and never SILENTLY SKIP — which would be worse than
      either, because the operator would see a brief missing a section with no
      reason given. A directory with one good and one broken file loads the
      good one and returns exactly one `SEAT_PLUGIN_UNLOADABLE` notice naming
      the file and the error; a file declaring no `PLUGIN` is named the same
      way; and a template that cannot expand is refused when it runs, with its
      own typed code.

## Phase 8 — the form (C1 only), both seats

- [ ] 31. (S8.2) Make the role-prompt wrapper selectable: `roles.py`
      `TEMPLATES`/`COMPACT_TEMPLATES` become a registered, versioned
      template registry; the shipped default reproduces today's bytes.
      done-when: `python -m pytest tests/test_role_prompt_registry.py -q`
      -> `0 failed`, including a byte-identical-default case

- [ ] 32. (§17.9, decision 4) Pin `wire_contract_for`'s existing mapping.
      A committed table of `(role, output_model, profile) -> contract_id`
      captured from the base commit, asserted unchanged — this is what keeps
      `invariants.py:1233`'s replay authority set and
      `run_manifest.py:2074`'s qualification subject off this tranche's
      diff. Mutation-prove it by changing one returned id and watching it
      go RED.
      done-when: `python -m pytest tests/test_wire_contract_id_map.py -q`
      -> `0 failed`, AND the pasted RED run of the mutation

- [ ] 33. (S8.2, S9.4, decision 2) Add form SELECTION at the DISPATCH SITE,
      both seats, among ids ALREADY registered: conjecturer —
      `conjecturer.turn.v6`, `conjecturer.turn.v7`,
      `conjecturer.atomic-candidate.v1`; critic —
      `argumentative_critic.compact.v1`, `critic.atomic-target.v1`. By
      argument/env only. **No new contract id; `run_manifest.py`,
      `qualification.py`, `cli/doctor.py`, `invariants.py` and
      `verification/` are NOT opened.**
      done-when: `git diff --name-only e91f4fcc3..HEAD` contains none of
      `src/deepreason/run_manifest.py`, `src/deepreason/qualification.py`,
      `src/deepreason/cli/doctor.py`, `src/deepreason/invariants.py`,
      `src/deepreason/verification/report.py`

- [ ] 34. (§17.4, S9.1-S9.3) [COMMIT] Add `SeatShellV1` and its registry,
      the two shipped shells (`seat.conjecturer.legacy-v0`,
      `seat.critic.legacy-v0`), the optional
      `preferred_conjecturer_form` on the model-profile document, the
      four-step resolution order, and the typed NOTICE on selection (never
      a refusal — the ungated-seats law). `SeatShellV1` carries NO score,
      rank, weight, confidence, priority or authority field. Create
      `docs/map/SEAM-llm-x-model-profiles.md` in the SAME commit
      (`PARKED.md` P3's first half).
      done-when: `python -m pytest tests/test_seat_shell_registry.py
      tests/test_model_profile_form_selection.py -q` -> `0 failed`, AND
      `python tools/docs_verify.py --links` -> 0 unresolved

- [ ] 35. (S8.4, S8.5) Add normalisations N1-N5 to `validate_value`, each
      recording its rule id in the attempt's diagnostic trail. N1 and N3
      already partly ship — extend, do not duplicate.
      done-when: `python -m pytest tests/test_wire_normalisation.py -q`
      -> `0 failed`

- [ ] 36. (S11.4) [COMMIT] Prove leniency changes no verdict: for each of
      N1-N5, a strict reply and its loosened twin compile to the SAME
      canonical artifact byte-for-byte.
      done-when: `python -m pytest tests/test_wire_normalisation.py -k identical -q`
      -> `0 failed`, five cases

## Phase 9 — the architecture tests (the modularity law's "enforced")

- [ ] 37. (S11.1) `tests/test_seat_section_architecture.py` limb 1: RED if
      either renderer constructs a section other than through
      `resolve_section_plugin` — a pinned call COUNT, the shape
      `DR-INV-render-layout` uses for its `_head` bypass trap.
      done-when: the test passes on the tree AND is pasted RED against a
      deliberately bypassing mutation

- [ ] 38. (S11.2) Limb 2: register a brand-new plugin from a temp home
      directory, render a pack with it, assert its text appears and its
      receipt is written — touching no file under `src/`.
      done-when: `python -m pytest tests/test_seat_section_architecture.py -k no_source_edit -q`
      -> `0 failed`

- [ ] 39. (S11.3 widened, §17.6) Limb 3: shape buys nothing. RED if
      `seat_id`, `shell_id`, `layout_id`, `form_id` or any
      `SectionReceiptV1` field is read in `scheduler/`, `adjudication/` or
      `rules/` admission, rank, immunity, refutation or acceptance paths.
      done-when: `python -m pytest tests/test_seat_section_architecture.py -k shape_buys_nothing -q`
      -> `0 failed`, AND the pasted RED run against a PLANTED read

- [ ] 40. (§17.5, R20) [COMMIT] The swap test: bind the CONJECTURER shell at
      the critic's dispatch site against the deterministic stub, and assert
      (1) the call renders under that shell's layout, (2) the section-plan
      object records the shell id, (3) the reply is parsed by the FIXED
      parse half of whichever form the shell names, (4) `expected_target`
      and the alias binding are unchanged. The docstring states what the
      test does NOT claim: that the swapped seat produces useful criticism.
      done-when: `python -m pytest tests/test_seat_shell_swap.py -q`
      -> `0 failed`

- [ ] 41. (S11, §17) [COMMIT] Create `docs/map/INV-seat-section-plugins.md`
      (SPEC §9's three layers, the seat-is-a-shell law's scope boundary, and
      these four checks) and `docs/map/REC-add-a-section-plugin.md`, and add
      both to `INDEX.md`. Every claim carries a column-0 `check:` that can
      fail.
      done-when: `python tools/docs_verify.py --audit` -> no finding NAMING
      either new document (the `SEAM-llm-x-rules.md:54` baseline row stands)

## Phase 10 — the experiment recipe, committed as an instrument

- [ ] 42. (S12.0, S12.1) Write `PREREG.md` for STEP 1 (hold the form, vary
      ONE brief parameter), on the shape of
      `experiments/2026-08-28-diversity-generation/PREREG.md`.
      done-when: file exists containing `## §6 — Outcome measures (frozen
      before any call)` and the four measures of SPEC S12.3

- [ ] 43. (S12.3) Add `analyse_form_arms.py` computing admission rate
      (re-running `census_conjecturer_failures.py` over the new roots) and
      M1/M2/M3 by CALLING the committed diversity instrument — not a
      reimplementation of it.
      done-when: `python .../analyse_form_arms.py --self-test` -> `ok`

- [ ] 44. (S12.4, S12.5) [COMMIT] Add the two binding rules as CHECKS, not
      prose: provenance fields (`layout_id`, `form_id`, `shell_id`) are
      OMITTED ENTIRELY from any judged render — not blanked; and no model
      self-reported number enters any metric, rank, filter or ordering.
      done-when: `python -m pytest tests/test_form_experiment_binding.py -q`
      -> `0 failed`, both rules pasted RED against a violating mutation

## Phase 11 — the gate and delivery

- [ ] 45. (§13, §17.9) Frozen-surface disclosure: re-run the gate's own
      instrument over the ACTUAL diff and paste the result.
      done-when: `python tools/blast_radius.py --files $(git diff
      --name-only e91f4fcc3..HEAD -- 'src/*') --against e91f4fcc3` ->
      `"frozen_surface_verdict": "CLEAR"`. **Anything else is a STOP**:
      request the grant in a document before proceeding.

- [ ] 46. (all) Diff budget check (SPEC §17.8, ~2400 lines of `src/` — raised
      by the operator 2026-09-03 on the measured step-22 overrun).
      done-when: `python tools/diff_budget.py e91f4fcc3 --ceiling 2400
      --paths 'src/*'` -> `"verdict": "WITHIN"`, or a stated,
      operator-visible overrun

- [ ] 47. (all) Map check, FULL mode — `--fast` reuses cached results and
      CANNOT catch a document a `src/` change just broke. Run on an
      otherwise idle box: never concurrently with the gate.
      done-when: `python tools/docs_verify.py` -> failures are the
      `docs/AUDIT_BASELINES.md` shallow-clone rows and NOTHING ELSE (5 or 6
      expected here; each row named), AND `python tools/docs_verify.py
      --audit` -> no finding naming a document this tranche wrote

- [ ] 48. (all) Full gate, alone on the box.
      done-when: `python -m pytest tests/ -q -n 4` -> output ends
      `N passed, 0 failed` (paste it). Compare N against
      `docs/AUDIT_BASELINES.md`; 0 failed is the only acceptable result and
      no assertion is weakened to get there.

- [ ] 49. (all) [COMMIT] Tranche commit: one change, message stating what,
      why, the evidence, and `Full gate: N passed, 0 failed`.
      done-when: `git log -1 --stat` shows the tranche and the message
      carries the gate line

- [ ] 50. (all) Push with retry (2s/4s/8s/16s backoff) and confirm clean.
      done-when: `git status --porcelain` is EMPTY and
      `git rev-parse HEAD origin/claude/conjecturer-pluggable-interface-7v3es6`
      prints the same sha twice

- [ ] 51. (all) Route to `dr-validate-change` (VALIDATION.md), then
      `dr-deliver-change` (DELIVERY.md with the R1-R24 reconciliation).
      **The live experiment of Phase 10 runs in its OWN tranche** — a
      multi-step programme runs one step per tranche (`dr-drive-harness`
      §6), and finishing this one early is not a reason to start it.
      done-when: VALIDATION.md exists with verdict PASS

---

## Coverage

Every S-number and every §17 clause has at least one step:
S1 (9,10,14,20), S1.1-1.4 (9), S1.5 (14), S1.6 (15), S1.7 (16), S2 (11),
S3 (28,29,30), S4 (26,27), S5 (23), S6 (23), S7 (24,25), S8 (31,33,35),
S9 (33,34), S10a/§9 (12,41), S10 (12,13,17,19), S10.4 (2,3,7,8,20,21),
S11 (37,38,39,41), S12 (42,43,44), S13 (4,5,20,34,41).
§17.1 (9,12,13,17,19), §17.2 (18,21), §17.3 (7,8,19,21), §17.4 (24,34),
§17.5 (40), §17.6 (39), §17.7 (6 — parked with prompts), §17.8 (46),
§17.9 (32,45).

## Not in this checklist, on purpose

- Road C2 (an open form registry, a NEW contract id) — SPEC §0.
- `render_batch_crit_pack` — `PARKED.md` P4.
- The judge, defender, variator and synthesizer seats — `PARKED.md` P5.
- A SECOND conjecturer kind or criticism kind (`R22`, `R23`) —
  `PARKED.md` P6. The registry exists so each is a registration; guessing
  one now costs an un-shipping.
- Episodes beyond the registered empty slot — `R13`.
- `PARKED.md` P1, P2 and the `model-profiles x scheduler` half of P3.
