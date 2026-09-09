# PREREG AMENDMENT — 2026-09-09: the head this tranche runs on, and what
# moved underneath it between the seal and the launch

Written 2026-09-09, **BEFORE ANY PROVIDER CALL ON ANY ARM**, in the executor
window the operator opened with "do it" (`REQUEST.md` §4).

`PREREG.md` is sealed by digest (`SEALED.txt`) and is not edited. This file is
the only permitted amendment, and its own permitted scope is narrow, stated by
the window that authorised it: *the head commit you run on and any file the
arms depend on that main has changed since sealing*. It changes no arm, no
measure, no decision rule and no prediction. Its digest is appended to
`SEALED.txt` in the same commit that carries it.

---

## A1 — The head

| | |
|---|---|
| sealed at | `8f4410159` — "PREREG sealed with the operator's three amendments, before any provider call", 2026-09-04 23:48:22 UTC |
| **runs at** | **`d7c87473e`**, 2026-09-09 00:52:44 UTC |
| commits on `main` between them | 254 |

`PREREG.md`'s recorded base was `main` at `33f92e88c`. The arms now run five
days and 254 commits later. Every arm — A0, A1, A1P, A2, A3 and B0 — runs on
this one head, so no comparison inside the experiment is confounded by the
move; what the move changes is which VERSION of the harness the result speaks
about, and this section is the record of that.

## A2 — What the arms depend on, and which of it moved

The arm scripts read: `src/deepreason/**` (the run itself), `scripts/
cycle_soak.py` (R20's gate), `tests/conj_pack_golden_cases.py` (the fixture
`prove_arms.py` renders over), and five committed instruments in other
tranches that `judge.py` and `analyse_arms.py` import rather than reimplement.
Each was checked with `git log 8f4410159..HEAD -- <path>`.

| dependency | commits since seal | verdict |
|---|---|---|
| `scripts/cycle_soak.py` | 0 | unchanged |
| `tests/conj_pack_golden_cases.py` | 0 | unchanged |
| `…provenance-history-channel/judge.py` | 0 | unchanged — the copied protocol's `_ask` and criteria string |
| `…provenance-history-channel/analyse_length_bias.py` | 0 | unchanged — every estimator §5 pins |
| `…provenance-history-channel/JUDGING_PREREG_COPIED.md` | 0 | unchanged |
| `…2026-08-28-diversity-generation/analyse.py` | 0 | unchanged — M1/M2/M3 |
| `…pluggable-interface/census_conjecturer_failures.py` | 0 | unchanged |
| `…provenance-history-channel/measure_diversity_per_problem.py` | 1 | **changed, additively** — see A2.1 |
| `src/deepreason/llm/layout.py` | 0 | unchanged — §3.1's `superseded_summary_n = 0` still holds |
| `src/deepreason/llm/{seat_layouts,seat_plugins,seat_sections,packs}.py` | 3 | **changed, additively** — see A2.2 |
| `src/deepreason/` elsewhere (scheduler, budget, config, shallow, views, …) | 18 | changed; see A2.3 |

### A2.1 `measure_diversity_per_problem.py` — additive, default OFF

`5e44a650e` adds a `--survivors-only` flag and a `survivors_only()` helper.
`judge.py harvest` imports `conjectures` and `_seed_problem` from this module,
and neither function changed by a byte; the new flag is off unless passed and
this tranche never passes it. **No meaning change.**

### A2.2 The four files the arms actually vary — additive, and measured

Three commits touch them (`db5cc16ff`, `d661aadc1`, `8946abeec`), and all
three ADD:

- `seat_sections.py` gains a `.layout.json` road, so `load_operator_plugins`
  now also globs `*.layout.json` and returns a coded notice instead of a
  flattened one on a refusal. **This partly closes `PARKED.md` F2** — a NEW
  layout can now be declared in a file. The rig is not changed to use it: an
  arm rig that changed between the seal and the launch would be a different
  experiment. A3's home carries one `.tmpl` and no `.layout.json`, so the new
  glob finds nothing, and `armrig.install`'s check (`op.neighbourhood.v1` must
  appear in `loaded`) is unaffected.
- `packs.py` gains `render_seat_brief` / `allocate_seat_brief`, declared public
  entries over the private walk and allocator. The two shipped renderers still
  call the walk directly; no byte of the shipped path moves.
- `seat_layouts.py` and `seat_plugins.py` gain the organiser pairing
  (`seat-pack.conjecturer.organiser-v1`, `dr.output-contract.organiser`) and an
  evidence-blind critic layout. Both are **registered, never default**; a run
  reaches them only through `DEEPREASON_SEAT_SHELL`, which no arm sets.

**Measured, not asserted.** `prove_arms.py` re-run on `d7c87473e` prints the
byte counts and diff line counts of `PROVE_ARMS.txt` **identically**:

    A0 control: 5511 bytes
    A1     5886 bytes  differs, 4 lines
    A1P    5511 bytes  IDENTICAL TO A0
    A2     5511 bytes  IDENTICAL TO A0
    A3     5323 bytes  differs, 9 lines

So every claim §3 makes about the arms — A1 is the one real history
treatment, A1P and A2 are the noise floor, A3 loses content — is still true
of the code that will run them. §3.2's falsifiable clause is unchanged and
still live.

### A2.3 The rest of `src/` — changed, and NOT claimed to be inert

Eighteen commits touch the scheduler, the budget, the criticism dispatch and
budget policy, `results`, `stop_report`, `shallow`, `signals`,
`views/evidence_states` and the informal trial. These change how a run
BEHAVES, and this amendment does not pretend otherwise. Two consequences,
both registered here before any number exists:

1. **Inside the experiment, nothing is confounded.** All six arms run on
   `d7c87473e`. A difference between arms cannot come from a difference in
   harness version, because there is only one.
2. **Across tranches, the comparison is not free.** Numbers from this
   tranche are not directly comparable to `RESULTS_M1_QUALITY.md`'s, which
   came off a different head. `PREREG.md` never registered such a comparison
   as a measure — §7 compares A1 against THIS tranche's own pooled null arms,
   and §4 compares every arm against THIS tranche's own B0 — so nothing in
   the design depends on cross-tranche comparability. RESULTS.md states this
   again in the residue.

R20's gate is re-run on this head before any provider call, per the launch
window's instruction and CLAUDE.md's own rule; `SOAK.md` is superseded only in
its dates, not in its case (`reach-rich`) or its per-arm structure. The
re-run's output is recorded in `SOAK_2026-09-09.md`.

## A3 — What this amendment does NOT do

It does not change the arms (§2), the primary measure (§4), the length control
(§5), the decision rule (§7), the predictions (§8) or the measures and their
instruments (§9). It does not resolve `PARKED.md` F1-F4; F2's partial closure
on main is recorded above as a fact about the tree, not as a change to this
tranche. And it registers no expectation about any number.
