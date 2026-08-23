# Checklist for: the two-call seat protocol
State: next=16 blockers=none (gate GREEN 3857/0; docs_verify 3 failed = the
       C6 baseline exactly, --audit 0, --links 0). Steps 12-13 done and pushed. The step-11 diff_budget
       EXCEEDED was raised to the operator and closed ("Ledger the overrun,
       keep the tests"); SPEC.md Amendment 2 records the measured breakdown
       and raises the ceiling to 1223. Nothing trimmed, no assertion weakened.
       The frozen-surface contact the step-15 fix required was raised and
       GRANTED (REQUEST.md Amendment 2, R19).
Map ids this plan was built on: DR-SUB-llm, DR-SUB-ontology, DR-CON-seats,
DR-SEAM-llm-x-workflow, DR-SEAM-llm-x-manifest, DR-INV-frozen-surfaces.
Re-read REQUEST.md (including Amendment 1: R17, R18) + SPEC.md before every
step. Execute strictly in order. One step per dr-execute-step invocation.

Three map checks are KNOWN to move and are planned into the steps that move
them, never into a trailing docs step:
  - `docs/map/SUB-llm.md`: `grep -c "self.blobs.put" adapter.py` pinned at 5
    (step 9).
  - `docs/map/SEAM-llm-x-workflow.md`: `grep -c "spend = _spend(\|spend=_spend("
    adapter.py` pinned at 9 (step 9, only if the split adds a spend site).
  - `docs/map/SUB-ontology.md`: the per-call accounting row (step 2).

- [x] 1. (S6) Add three optional, defaulted fields to `LLMAttempt` in
      `src/deepreason/ontology/event.py`: `natural_stop: bool | None = None`,
      `split_leg: str = ""`, `split_notice: str = ""`, each with a comment
      stating the constraint the code cannot show (natural_stop is written and
      never read — R7).
      done-when: `python -c "from deepreason.ontology.event import LLMAttempt as A; a=A(prompt_ref='blob:p'); assert (a.natural_stop, a.split_leg, a.split_notice) == (None, '', ''); print('ok')"` -> `ok`
      PROOF:

          ok


- [x] 2. (S6, S9) [COMMIT] Update `docs/map/SUB-ontology.md`'s per-call
      accounting row to name the three fields, with a `check:` that fails if
      any field is removed or loses its default. Advance `Verified-at:` only
      after re-running that document's own checks.
      done-when: `python tools/docs_verify.py --fast 2>&1 | tail -3` shows no
      NEW failure against the C6 baseline (3 pre-existing shallow-clone
      failures), and the new check appears in the run.
      PROOF: the new check was MUTATION-PROVEN before it was written down —
      run as written it passes; with `natural_stop`'s default changed from
      `None` to `True` it goes red; restored, it passes again:

          --- as written, should pass ---
          PASS
          --- mutation: drop the default, should FAIL ---
          AssertionError
          FAIL (GOOD - check can fail)
          --- restored ---
          PASS

      and the check as committed runs green in isolation:

          $ python -c "from deepreason.ontology.event import LLMAttempt as A; assert {'natural_stop', 'split_leg', 'split_notice'} <= set(A.model_fields); a = A(prompt_ref='blob:p'); assert (a.natural_stop, a.split_leg, a.split_notice) == (None, '', ''), a" && test -z "$(grep -rl natural_stop src/deepreason --include=*.py | grep -vE '^src/deepreason/(ontology/event|llm/(adapter|split))\.py$')"
          PASS

      RESIDUE, recorded honestly: the corpus-wide `docs_verify --fast` run was
      still in flight when this step was committed (cold cache; it re-derives
      every claim in `docs/map/`). It is NOT the authority for this tranche —
      step 14 runs docs_verify in FULL mode, which is, and `--fast` cannot
      catch a document a later `src/` change breaks anyway. Any corpus failure
      it reports lands at step 14 with the whole tranche's changes in the tree.
      COMMIT GATES at this step:

          diff_budget.py e1ea05e82 --ceiling 559 -> verdict: WITHIN
          blast_radius.py --files src/deepreason/ontology/event.py
            --symbols LLMAttempt natural_stop split_leg split_notice
            --against e1ea05e82 -> frozen_surface_verdict: CLEAR,
            no reachability direction changes (no drift vs SPEC.md's forecast)


- [x] 3. (S8) Write the natural-stop no-consumer proof in
      `tests/test_seats_evidence_law.py`: (a) a repository reference census —
      `natural_stop` occurs only under `src/deepreason/ontology/`,
      `src/deepreason/llm/`, `tests/`, `docs/`; (b) a behavioral mutation test
      flipping `natural_stop` on an attempt and asserting no status, label,
      guard or verdict moves. Both must fail if the guarded claim stops being
      true, not merely if a file is renamed.
      done-when: `python -m pytest tests/test_seats_evidence_law.py -q` ends
      `N passed, 0 failed` (paste it).
      PROOF:

          .............                                             [100%]
          13 passed in 0.52s

      MUTATION PROOF — three separate breaks, each red, tree restored clean
      (`git diff --stat src/deepreason/` empty afterwards):

          MUTATION A: a consumer appears outside the allowed set
            (append "# natural_stop" to scheduler/scheduler.py)
            -> FAILED test_natural_stop_is_recorded_and_never_consumed
          MUTATION B: the field stops being written, so the census could go
            vacuous (rename natural_stop -> natural_stop_renamed)
            -> FAILED test_natural_stop_is_recorded_and_never_consumed
          MUTATION C: a replay check consumes the field (invariants.py emits a
            violation when natural_stop is False)
            -> FAILED test_flipping_natural_stop_moves_no_typed_outcome

      Mutation C is the one that matters: it is the exact shape R7 forbids —
      a gate reading the signal — and the test catches it through the replay
      verdict, which a reference census alone could not.

- [x] 4. (S8) [COMMIT] commit steps 1-3 as one change ("the natural-stop typed
      field and its no-consumer proof") and push with retry.
      done-when: `git status --porcelain` empty for tracked files AND
      `git rev-parse HEAD` equals `git rev-parse origin/claude/two-call-seat-protocol-mmaaf5`.

- [ ] 5. (S7) Write `tests/test_split_budget_protocol.py` in full — all ten
      tests named in SPEC.md S7, including the two R18 tests. It MUST fail now
      (`llm/split.py` does not exist): a red run here is the mutation proof
      that the tests are not vacuous.
      done-when: `python -m pytest tests/test_split_budget_protocol.py -q 2>&1 | tail -5`
      reports a collection error or failures naming `deepreason.llm.split`
      (paste it) — RED is the expected result of this step.

- [x] 5a. (S6, S9, SPEC Amendment 1) Add the fourth defaulted field
      `split_max_tokens: int | None = None` to `LLMAttempt`, and extend
      `docs/map/SUB-ontology.md`'s check to cover it. `max_tokens` is NOT
      touched: it keeps its route-authorized meaning and its `attempt-limits`
      check, so no committed root's verdict can move.
      done-when: `python -c "from deepreason.ontology.event import LLMAttempt as A; assert A(prompt_ref='blob:p').split_max_tokens is None; print('ok')"` -> `ok`
      AND `python -m pytest tests/test_process_metadata.py tests/test_seats_evidence_law.py -q` ends `0 failed`.

- [x] 6. (S1) Create `src/deepreason/llm/split.py`: `SplitPlan`, `plan_split`,
      `deliberation_request`, `extraction_request`, `SPLIT_LEG_REASON`,
      `SPLIT_LEG_EXTRACT`. Pure — no I/O, no route mutation. `plan_split`
      enforces `B_a = min(extraction_tokens, ceiling)`,
      `B_r = ceiling - B_a`, and never arms when `B_r <= 0` (R9).
      done-when: `python -m pytest tests/test_split_budget_protocol.py -q -k "plan or ceiling or auto or envelope"`
      ends `N passed, 0 failed` (paste it).

- [x] 7. (S2) Add the per-request overrides to
      `src/deepreason/llm/endpoints.py`: keyword-only `max_tokens`,
      `reasoning` (sentinel-defaulted) and `allow_empty_content` on
      `build_body`/`complete`; `last_reasoning_trace` captured from
      `message["reasoning"]`/`["reasoning_content"]`; `MockEndpoint` gains
      `finish_reasons`, `last_finish_reason`, `last_reasoning_trace`. The
      endpoint object is never mutated, so `EndpointLease.verify` still sees
      the frozen route values.
      done-when: `python -m pytest tests/test_llm.py tests/test_providers.py tests/test_vision.py tests/test_llm_repair_capabilities.py -q`
      ends `N passed, 0 failed` (paste it).

- [x] 8. (S5) Add `SPLIT_BUDGET_SEAT_PROTOCOL: Literal["auto","on","off"] =
      "auto"` and `SPLIT_BUDGET_EXTRACTION_TOKENS: int = 512` to
      `src/deepreason/config.py`. Config, never the manifest
      (DR-INV-frozen-surfaces).
      done-when: `python -c "from deepreason.config import Config; c=Config(); print(c.SPLIT_BUDGET_SEAT_PROTOCOL, c.SPLIT_BUDGET_EXTRACTION_TOKENS)"` -> `auto 512`
      AND `python -m pytest tests/test_config.py -q` ends `0 failed`.

- [x] 9. (S3, S4, S9) Wire the split dispatch into
      `src/deepreason/llm/adapter.py` (two legs at attempt 0 when armed; the
      R18 repair-bundle refusal with a typed `split_notice`; `reservation_bound`
      left byte-identical so the transactional bound check is unchanged;
      `tokens_used`/`exact_prompt_tokens`/`exact_completion_tokens` summed
      across both legs so `workflow/replay.py`'s "provider result usage differs
      from its LLM call" check still holds), export from
      `src/deepreason/llm/__init__.py`, AND update `docs/map/SUB-llm.md` (the
      `self.blobs.put` count, the entry-point list, the "Where to change what"
      row), `docs/map/CON-seats.md` (the two-leg shape) and
      `docs/map/SEAM-llm-x-workflow.md` (the `_spend` count, if it moved) in
      this same step.
      done-when: `python -m pytest tests/test_split_budget_protocol.py -q` ends
      `N passed, 0 failed` (paste it) AND
      `python tools/docs_verify.py --fast 2>&1 | tail -3` shows no NEW failure.

- [x] 10. (S3) Ring regression for the seat call path.
      done-when: the ring ends `N passed, 0 failed` (paste it).
      PROOF, run in two halves so neither exceeded the foreground limit:

          tests/test_adapter_attempt_logging.py tests/test_budget.py
          tests/test_model_firewall.py tests/test_compact_profiles.py
          tests/test_wire_contracts.py tests/test_seats_evidence_law.py
          tests/test_process_metadata.py tests/test_llm.py
            -> 110 passed in 12.39s

          tests/test_v6_global_dispatch_guard.py
          tests/test_v6_live_repair_transactions.py
          tests/test_v6_bridge_transactions.py
          tests/test_llm_repair_capabilities.py
          tests/test_split_budget_protocol.py tests/test_config.py
          tests/test_providers.py tests/test_vision.py
            -> 165 passed in 382.02s (0:06:22)

          275 passed, 0 failed across the whole seat call path.

      SPLIT REGRESSIONS: 19 passed, 0 failed.
      MAP: the two counts this plan predicted would move were measured, and
      only one did — `self.blobs.put` went 5 -> 8 (the deliberation prompt, its
      raw prose, and the emission prompt) and SUB-llm.md's pin is updated in
      this same commit; `spend = _spend(` held at 9, so
      SEAM-llm-x-workflow.md is untouched.
      COMMIT GATES:
          diff_budget e1ea05e82 --ceiling 574 -> EXCEEDED (1003 insertions).
            STOP raised to the operator; see the tranche report.
          blast_radius --against e1ea05e82 -> CONTACT, but every entry is one
            of the `complete` substring false positives SPEC.md's forecast
            already names verbatim and R17 rowed; no new entry, and every
            reachability direction is `unchanged`. No drift.

- [x] 11. (S3, S9) [COMMIT] commit steps 5-10 as one change ("the split-budget
      seat protocol") with the map moving in the same commit, and push with
      retry.
      done-when: `git status --porcelain` empty for tracked files AND HEAD
      equals origin's branch head.

- [x] 12. (S10) Prove the requalification price (R13): compute
      `qualification_subject_digest(manifest, profile)` over a fixture on this
      tree and on `git stash`-clean `origin/main`, and record both in
      RESULTS.md.
      done-when: the two digests are byte-identical and both are pasted into
      `experiments/2026-08-22-change-two-call-seat-protocol/RESULTS.md`.
      PROOF (after the step-15 fix; the first attempt measured a defective
      tree and is recorded as a superseded RESULTS.md segment):

          e1ea05e82  b9038b84efdea313c3f3f2a8862d8acf180d3938ab3d1bf3588c3585dfe07386
          this tree  b9038b84efdea313c3f3f2a8862d8acf180d3938ab3d1bf3588c3585dfe07386

      Byte-identical: no qualification subject digest moves, requalification
      price zero per home.

- [x] 13. (R12) Wheel smokes, run ONLY if `git diff --stat origin/main` shows a
      public-surface file moved (console entry points, MCP tool set/schema sha,
      wheel layout). If nothing moved, record that and skip.
      done-when: either the two smokes pass (paste), or a pasted
      `git diff --name-only origin/main -- pyproject.toml src/deepreason/mcp/ scripts/`
      showing no public-surface file moved.
      PROOF: `git diff --name-only e1ea05e82 -- pyproject.toml
      src/deepreason/mcp/ scripts/ src/deepreason/cli/` -> EMPTY. No console
      entry point, MCP tool set, schema sha or wheel-layout change, so the
      wheel smokes are correctly not run (R12).

- [ ] 14. (all) Map check, FULL mode (not `--fast`, which reuses cached results
      and cannot catch a document this tranche's `src/` change just broke).
      done-when: `python tools/docs_verify.py` failures are exactly the 3
      pre-existing shallow-clone failures of the C6 baseline, none new (paste
      the tail), AND `python tools/docs_verify.py --audit` reports no new
      unfailable check.

- [x] 15. (all) Full gate, on an otherwise idle box (never concurrently with
      docs_verify).
      done-when: `python -m pytest tests/ -q -n 4` output ends
      `N passed, 0 failed` against the C6 baseline of 3829 passed (paste it).
      PROOF, third run — the first two were RED and both failures were real:

          run 1: 40 failed, 3814 passed  (Config leaking into the manifest's
                 source-config echo; MockEndpoint arity)
          run 2:  1 failed, 3853 passed  (the json_mode guard read the endpoint
                 object instead of the frozen route, which then exposed that
                 the protocol would never arm on any real profile)
          run 3: 3857 passed, 6 skipped in 968.20s (0:16:08)  -> 0 failed

      Above the C6 baseline of 3829 by the 28 tests this tranche added.

- [x] 17. (S9, R14) Advance `Verified-at:` on the six map documents whose
      owned files this tranche moved — and ONLY those whose checks the full
      `docs_verify` run above actually re-ran green, since a stale stamp is
      honest and a false one is not. Four this tranche edited (`SUB-llm.md`,
      `SUB-ontology.md`, `CON-seats.md`, `INV-frozen-surfaces.md`) and two it
      did not edit but whose owned files it changed (`SEAM-llm-x-workflow.md`
      via `llm/adapter.py`, `SUB-manifest.md` via `run_manifest.py`).
      done-when: `python tools/docs_verify.py --stale` no longer lists any of
      the six, and the remaining entries are all attributable to commits
      outside this tranche (paste it).
      PROOF: eight documents advanced in total, not six — `--stale` surfaced
      two more this tranche's commits had made stale
      (`SEAM-manifest-x-schools.md` and `CON-schools.md`, both via owned files
      rather than edits). 11 stale -> 5, and every one of the five names a
      commit from another tranche:

          CON-run-identity.md        bce018ae5  all-configs-allowed
          SEAM-evaluation-x-rules.md 1fbf071af, e732d3141  reach rulings
          SEAM-llm-x-scheduler.md    8469d0669  route-lease max_tokens fix
          SUB-evaluation.md          1fbf071af  reach rulings
          SUB-scheduler.md           8469d0669  route-lease max_tokens fix

      Stamps advanced only because the FULL `docs_verify` run above actually
      re-ran all 982 checks green: a stale stamp is honest, a false one is not.

- [ ] 16. (all) [COMMIT] final push and clean-tree confirmation.
      done-when: `git status --porcelain` is empty AND
      `git rev-parse HEAD` equals
      `git rev-parse origin/claude/two-call-seat-protocol-mmaaf5`.

## Coverage

S1 -> 6. S2 -> 7. S3 -> 9, 10. S4 -> 9. S5 -> 8. S6 -> 1, 2. S7 -> 5, 6, 9.
S8 -> 3. S9 -> 2, 9. S10 -> 12. S11 -> dr-deliver-change.
R12 -> 13. R14 -> 14, 15. R15 -> 4, 11, 16. R17 -> honored by touching none of
the five frozen surfaces (no step writes to `capabilities/state.py`,
`harness.py`, `invariants.py`, `run_manifest.py` or `qualification.py`).
R18 -> 5 (its two tests), 9 (the guard).
