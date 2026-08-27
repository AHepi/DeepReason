# GOAL — a split leg is not a repair attempt

Tranche: `experiments/2026-08-27-defect-split-leg-recording/`
Branch: `claude/split-budget-leg-recording-z9xcas`
Base: `ba4720a95` (= `origin/main` at tranche open)
Opened: 2026-08-27

## The one goal

**Make the split-budget seat protocol write a record that `verify_root`
accepts, by recording its two legs as a declared leg shape on ONE attempt
rather than as two entries in the repair ladder — and teach `verify_root`
to read that shape with checks of its own.**

Nothing else. Everything else observed goes to `PARKED.md`.

## Success criterion (falsifiable, decided by typed output)

1. A managed run driven against the deterministic stub with the model's
   reasoning mode ON — which is the whole of the wiring that arms
   `llm/split.py` under its `auto` default — reaches its requested cycle
   depth and `verify_root` returns **0 violations**.
   Instrument: `python -u scripts/cycle_soak.py --case split-legs`
   exits 0, with A2 (no operational failure), A3 (verify_root clean) and
   A4 (cycles reached) all PASS.
2. The literal acceptance the P-C2b STOP registered — `cycle_soak.py
   --case pc2b` exits 0 — is demonstrated on this tree. (That case's two
   files live only on `claude/p-c2-rebuild-harness-n9mguu`; they are
   materialised UNCOMMITTED for the run, because this tranche may not
   touch that paused window's directory. See §Constraints.)
3. A run carrying BOTH split legs AND a genuine schema repair verifies
   clean, and the repair ladder's own semantics are unchanged for that
   repair: the two shapes coexist rather than one displacing the other.
4. Every new check is mutation-proven in BOTH directions: it fires on a
   record that violates it, and is silent on a record that does not.
5. Full gate 0 failed; `docs_verify.py` full mode at its recorded
   baseline; both wheel smokes green (the operational smoke exercises
   reason-stage terminals).

## The defect, as the record states it

Diagnosis is ALREADY COMMITTED and is cited, not re-derived:
`experiments/2026-08-27-pc2b-symmetric-reasoning/BLOCKER.md` at commit
`ee0563cf1` on `claude/p-c2-rebuild-harness-n9mguu`.

`llm/split.py`'s two legs are written into `attempt_trace`, where
`invariants.py::verify_root` reads that list as a REPAIR LADDER. Every
thinking-ON run is therefore replay-invalid. `cycle_soak.py --case pc2b`
exits 1 with 50 violations across exactly four checks, plus an
`LLMAttempt.prompt_ref=None` crash:

| check | `invariants.py` | why a leg trips it |
|---|---|---|
| `attempt-accounting` | L3720 | the trace sums BOTH legs; the call records one |
| `attempt-order` | L3801 | both legs carry `attempt_index=0`, at list indices 0,1 |
| `attempt-blobs` | L3814 | a diagnostic ref is required when `not valid` — the reason leg is invalid BY DESIGN and is not a validation failure |
| `repair-metadata` | L4019 | `attempts > 1` ⇒ `DIAGNOSTIC:` in the final prompt; the extract leg's prompt carries the reasoning trace |

**No committed root constrains the shape.** 0 of 54 roots in
`ROOT_INVENTORY.json` carry a `split_leg` — the protocol has never run
live. Under the operator's 2026-08-14 law (old runs owe the future
nothing) the record format may take the shape the truth wants; here it
does not even have to, because nothing old is touched.

## Map ids resolved (map preflight, per dr-drive-harness §4)

- `DR-SUB-llm` — `llm/adapter.py`, `llm/split.py`: the WRITER.
- `DR-SUB-verification` — `invariants.py::verify_root`: the READER.
  **Frozen surface 3.**
- `DR-SUB-ontology` — `ontology/event.py`: `LLMAttempt`, the record the
  two sides disagree about.
- `DR-INV-frozen-surfaces` — read before design; grant requested in
  FIX.md before any code, per the standing discipline and the four
  precedent grants recorded there (2026-08-21, -22, -24, -25).

**FINDING — the covering seam document does not exist.** `INDEX.md`'s
matrix has no `llm × verification` row: not "not yet written", but
absent, i.e. no measured import traffic at all. That is exactly the
shape of this defect — `invariants.py` imports nothing from `llm/` and
the agreement between them is carried entirely by the `LLMAttempt`
record, so no coupling metric could see it and no document told the
protocol's author what `attempt_trace` already meant. Creating
`SEAM-llm-x-verification.md` is therefore part of this tranche, not
scope creep: it is the document whose absence let the defect ship.

## Constraints binding this tranche

- **Frozen surface 3** (`invariants.py` / `verification/`) is touched.
  The grant is requested in `FIX.md` BEFORE implementation, with the
  writer/reader design stated and `tools/blast_radius.py`'s own contact
  verdict pasted and disposed row by row. The monitor reviews it there.
- **`harness.py` event application must need ZERO contact.** If the
  design wants it, that is a STOP and a question, not a patch.
- **The paused P-C2/P-C2b window is not touched**: not its branch, not
  `experiments/2026-08-26-pc2-rematch/`, not
  `experiments/2026-08-27-pc2b-symmetric-reasoning/`. Neither directory
  exists on `main`; neither is created here. The durable regression is a
  soak case authored in THIS tranche's directory; criterion 2's literal
  `--case pc2b` run materialises that window's two files from
  `git show` into the worktree for the run and removes them before any
  commit, so nothing of theirs is authored, committed, or conflicted.
- Nothing is cherry-picked from that branch. All work is from `main`.

## Baselines to re-derive at this base (not assumed)

- Full gate: reported 4231 passed / 0 failed at `ba4720a95`.
- `docs_verify.py`: 3 pre-existing shallow-clone failures (0 when
  unshallowed).
- 5 MCP-thread tests flaky under `-n 4`.
- Both wheel smokes green. The root sweep is RETIRED and is not run.

## Out of scope (PARKED on sight)

Anything about whether the split protocol is the right mechanism, its
budget division, its notices, P-C2b's experimental design, or the
provider-side behaviour of glm-5.2. This tranche fixes how the two legs
are RECORDED and READ, and nothing else.
