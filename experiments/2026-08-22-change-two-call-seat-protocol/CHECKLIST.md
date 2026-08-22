# Checklist for: the two-call seat protocol
State: next=1 blockers=none
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

- [ ] 1. (S6) Add three optional, defaulted fields to `LLMAttempt` in
      `src/deepreason/ontology/event.py`: `natural_stop: bool | None = None`,
      `split_leg: str = ""`, `split_notice: str = ""`, each with a comment
      stating the constraint the code cannot show (natural_stop is written and
      never read — R7).
      done-when: `python -c "from deepreason.ontology.event import LLMAttempt as A; a=A(prompt_ref='blob:p'); assert (a.natural_stop, a.split_leg, a.split_notice) == (None, '', ''); print('ok')"` -> `ok`

- [ ] 2. (S6, S9) [COMMIT] Update `docs/map/SUB-ontology.md`'s per-call
      accounting row to name the three fields, with a `check:` that fails if
      any field is removed or loses its default. Advance `Verified-at:` only
      after re-running that document's own checks.
      done-when: `python tools/docs_verify.py --fast 2>&1 | tail -3` shows no
      NEW failure against the C6 baseline (3 pre-existing shallow-clone
      failures), and the new check appears in the run.

- [ ] 3. (S8) Write the natural-stop no-consumer proof in
      `tests/test_seats_evidence_law.py`: (a) a repository reference census —
      `natural_stop` occurs only under `src/deepreason/ontology/`,
      `src/deepreason/llm/`, `tests/`, `docs/`; (b) a behavioral mutation test
      flipping `natural_stop` on an attempt and asserting no status, label,
      guard or verdict moves. Both must fail if the guarded claim stops being
      true, not merely if a file is renamed.
      done-when: `python -m pytest tests/test_seats_evidence_law.py -q` ends
      `N passed, 0 failed` (paste it).

- [ ] 4. (S8) [COMMIT] commit steps 1-3 as one change ("the natural-stop typed
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

- [ ] 6. (S1) Create `src/deepreason/llm/split.py`: `SplitPlan`, `plan_split`,
      `deliberation_request`, `extraction_request`, `SPLIT_LEG_REASON`,
      `SPLIT_LEG_EXTRACT`. Pure — no I/O, no route mutation. `plan_split`
      enforces `B_a = min(extraction_tokens, ceiling)`,
      `B_r = ceiling - B_a`, and never arms when `B_r <= 0` (R9).
      done-when: `python -m pytest tests/test_split_budget_protocol.py -q -k "plan or ceiling or auto or envelope"`
      ends `N passed, 0 failed` (paste it).

- [ ] 7. (S2) Add the per-request overrides to
      `src/deepreason/llm/endpoints.py`: keyword-only `max_tokens`,
      `reasoning` (sentinel-defaulted) and `allow_empty_content` on
      `build_body`/`complete`; `last_reasoning_trace` captured from
      `message["reasoning"]`/`["reasoning_content"]`; `MockEndpoint` gains
      `finish_reasons`, `last_finish_reason`, `last_reasoning_trace`. The
      endpoint object is never mutated, so `EndpointLease.verify` still sees
      the frozen route values.
      done-when: `python -m pytest tests/test_llm.py tests/test_providers.py tests/test_vision.py tests/test_llm_repair_capabilities.py -q`
      ends `N passed, 0 failed` (paste it).

- [ ] 8. (S5) Add `SPLIT_BUDGET_SEAT_PROTOCOL: Literal["auto","on","off"] =
      "auto"` and `SPLIT_BUDGET_EXTRACTION_TOKENS: int = 512` to
      `src/deepreason/config.py`. Config, never the manifest
      (DR-INV-frozen-surfaces).
      done-when: `python -c "from deepreason.config import Config; c=Config(); print(c.SPLIT_BUDGET_SEAT_PROTOCOL, c.SPLIT_BUDGET_EXTRACTION_TOKENS)"` -> `auto 512`
      AND `python -m pytest tests/test_config.py -q` ends `0 failed`.

- [ ] 9. (S3, S4, S9) Wire the split dispatch into
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

- [ ] 10. (S3) Ring regression for the seat call path.
      done-when: `python -m pytest tests/test_adapter_attempt_logging.py tests/test_budget.py tests/test_model_firewall.py tests/test_compact_profiles.py tests/test_wire_contracts.py tests/test_v6_global_dispatch_guard.py tests/test_v6_live_repair_transactions.py tests/test_v6_bridge_transactions.py tests/test_seats_evidence_law.py -q`
      ends `N passed, 0 failed` (paste it).

- [ ] 11. (S3, S9) [COMMIT] commit steps 5-10 as one change ("the split-budget
      seat protocol") with the map moving in the same commit, and push with
      retry.
      done-when: `git status --porcelain` empty for tracked files AND HEAD
      equals origin's branch head.

- [ ] 12. (S10) Prove the requalification price (R13): compute
      `qualification_subject_digest(manifest, profile)` over a fixture on this
      tree and on `git stash`-clean `origin/main`, and record both in
      RESULTS.md.
      done-when: the two digests are byte-identical and both are pasted into
      `experiments/2026-08-22-change-two-call-seat-protocol/RESULTS.md`.

- [ ] 13. (R12) Wheel smokes, run ONLY if `git diff --stat origin/main` shows a
      public-surface file moved (console entry points, MCP tool set/schema sha,
      wheel layout). If nothing moved, record that and skip.
      done-when: either the two smokes pass (paste), or a pasted
      `git diff --name-only origin/main -- pyproject.toml src/deepreason/mcp/ scripts/`
      showing no public-surface file moved.

- [ ] 14. (all) Map check, FULL mode (not `--fast`, which reuses cached results
      and cannot catch a document this tranche's `src/` change just broke).
      done-when: `python tools/docs_verify.py` failures are exactly the 3
      pre-existing shallow-clone failures of the C6 baseline, none new (paste
      the tail), AND `python tools/docs_verify.py --audit` reports no new
      unfailable check.

- [ ] 15. (all) Full gate, on an otherwise idle box (never concurrently with
      docs_verify).
      done-when: `python -m pytest tests/ -q -n 4` output ends
      `N passed, 0 failed` against the C6 baseline of 3829 passed (paste it).

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
