# Validation for: make the critic's byte-checked citation channel reachable, and stop it latching shut

Every command below was re-run in this phase, in SPEC.md item order, on an idle
box, with the map instruments and the gate run SEQUENTIALLY and never
concurrently (`dr-drive-harness` §5b).

## Acceptance checks

**S1 (R1, R2, C1) — the ladder**

    $ python -m pytest tests/test_premise_channel.py -k "producer or ladder" -q
    4 passed, 25 deselected in 0.29s
                                                                        : PASS

    $ python -c "from deepreason.premises import PREMISE_INVITE_AFTER; assert PREMISE_INVITE_AFTER == 2"
    (exit 0 — the threshold is untouched, C1)                           : PASS

**S2 (R3, C5) — the disposition receipt**

    $ python -m pytest tests/test_premise_channel_loop.py -k "declined or disposition" -q
    4 passed, 12 deselected in 0.73s
                                                                        : PASS

    $ python -m pytest tests/test_premise_channel_loop.py::test_a_declined_invitation_moves_no_status -q
    1 passed in 2.31s
                                                                        : PASS

    $ python -c "<the M2-census namespace check, SPEC.md S2 accept 3>"
    M2 census namespace untouched OK                                    : PASS

**S3 (R3) — the signal declaration**

    $ python -m pytest tests/test_signal_contract.py tests/test_signals.py -q
    19 passed in 3.66s
                                                                        : PASS

    $ python -c "from deepreason.signals import describe, is_known; assert is_known('premise-answer:DECLINED'); assert 'invitation' in describe('premise-answer:DECLINED')"
    declared OK                                                         : PASS

**S4 (R5) — the named regression, mutation-proven**

    proof/s4_red.txt   (UNCHANGED tree):  7 failed, 38 passed in 3.23s
    proof/s4_green.txt (CHANGED tree):    45 passed in 3.04s

Same command both sides. The seven that flipped are what the change buys; the
five that were green in BOTH are the guards on behaviour it must not move —
`test_the_ladder_is_the_shipped_rule_when_no_attribution_stands`,
`test_refuting_an_attribution_lowers_the_rung`,
`test_an_uninvited_dispatch_records_no_disposition`,
`test_the_producer_fires_after_enough_refutations`,
`test_the_producer_stands_down_once_a_premise_is_attributed`.
                                                                        : PASS

**S5 (R6) — map, in the same commits.** See the Map section below.  : PASS

**S6 (R2, R3, R4, R7, R8) — the written answers**

    $ grep -c "^## " ANSWERS.md
    5
    $ grep -o "THE LATCH|THE EMPTY-REFS SILENCE|THE UNINVITED SCHEMA FIELD" ANSWERS.md | sort -u
    THE EMPTY-REFS SILENCE
    THE LATCH
    THE UNINVITED SCHEMA FIELD
                                                                        : PASS

    $ git diff --stat origin/main -- src/deepreason/llm/contracts.py src/deepreason/llm/wire.py
    (empty)
                                                                        : PASS
    R4's answer is NO, and it is decided by leaving the contract alone. The
    empty diff IS the acceptance output.

**S7 (R6, C7) — the gate.** See the Full gate section below.           : PASS

**S8 (R8, R9) — parked and delivered**

    $ grep -c "Ready-to-send prompt" PARKED.md
    3                                                                   : PASS

## Full gate

    $ python -m pytest tests/ -q -n 4
    4384 passed, 6 skipped in 879.80s (0:14:39)
                                                                        : PASS

0 failed. The C7 baseline is 4374; +10 is exactly the ten tests this tranche
added (four gate-arithmetic tests in `test_premise_channel.py`, six loop tests
in `test_premise_channel_loop.py`). No pre-existing failure to record, so
nothing goes to PARKED.md on that account.

## Record-behavior preservation

**n/a, and the reason is checkable rather than asserted.** This change touches
no reader or validator of the append-only record: `invariants.py`,
`verification/`, `harness.py`, `capabilities/state.py`, `run_manifest.py` and
`qualification.py` are all untouched (see the frozen-surface diff below). What
it adds to the record is one new Measure family, and a Measure carries no
state diff — `test_a_declined_invitation_moves_no_status` asserts that no
status moves and no artifact is minted on the receipt's own events.

The root sweep is RETIRED as an instrument (operator ruling 2026-08-22), so no
sweep is owed and none was run; the targeted regression on committed roots is
`probes/p11_ladder_counterfactual.py`, which replays all four committed
technique roots read-only with `Harness.at()` and is the stronger instrument
here because it looks at the exact predicate that changed.

## Frozen-surface diff

    $ git diff --stat origin/main..HEAD -- \
        src/deepreason/capabilities/state.py src/deepreason/harness.py \
        src/deepreason/invariants.py src/deepreason/run_manifest.py \
        src/deepreason/qualification.py src/deepreason/verification/ \
        src/deepreason/llm/firewall.py
    (empty)

Empty, as SPEC.md's forecast predicted and `tools/blast_radius.py` computed
(`"frozen_surface_verdict": "CLEAR"`, `"frozen_surface_contacts": []`). All
seven paths of the five surfaces are covered, plus the frozen-ADJACENT
`route_fingerprint` file.                                               : PASS

## Parallel-window cones (C4)

    $ git diff --stat origin/main..HEAD -- \
        src/deepreason/llm/layout.py src/deepreason/llm/packs.py \
        src/deepreason/llm/roles.py src/deepreason/informal/trial.py \
        src/deepreason/preparation.py
    (empty)

The render-layout tranche's and the manifest tranche's cones are untouched.
`llm/packs.py` was READ (its `DISCLOSED_ON_DROP` set is what bounds the
invitation's pack cost) and never written.                              : PASS

## Map

    $ python tools/docs_verify.py
    docs_verify: 4 failed                                               : PASS

    The four are exactly the C7 baseline and none names a file this tranche
    touched: CON-run-identity.md:200/202/204 (three shallow-clone failures —
    `fatal: ambiguous argument '1637e808'`, a revision this clone does not
    carry) and INV-frozen-surfaces.md:181 (the pre-existing falsified
    `transport_failure` census). Delta beyond four: ZERO.

    $ python tools/docs_verify.py --audit
    docs_verify --audit: 0 finding(s)                                   : PASS

    $ python tools/docs_verify.py --links
    docs_verify --links: 0 dangling reference(s), 68 document(s)        : PASS

    $ python tools/docs_verify.py --coverage
    docs_verify --coverage: 7 seam(s) swept, 18 without a Sweep: header, 2 finding(s)
                                                                        : PASS (pre-existing)

    Both findings name files outside this cone — `SEAM-periphery-x-verification.md:
    enforcement site not named: src/deepreason/amendment/apply.py` and
    `SEAM-schools-x-scratch.md: enforcement site not named:
    src/deepreason/informal/trial.py`. Neither file is in this tranche's diff
    (trial.py is a PARALLEL tranche's cone, C4), so neither finding can be
    this change's, and neither is this change's to fix.

    $ python tools/docs_verify.py --stale
    docs_verify --stale: 8 document(s) worth re-reading

    Every entry, judged rather than passed over:

    - `SEAM-rules-x-scratch.md` — lists THIS tranche's commit 9b4801d2f,
      because it owns `rules/crit.py`. **Dismissed with reason:** the document's
      concern is the criticism/scratchpad separation, and the change adds no
      scratch import and no pack parameter. Both of its enforcing tests are
      green (`test_the_criticism_rule_imports_no_scratch_module`,
      `test_the_criticism_rule_touches_scratch_only_as_an_ordering_fence`), and
      its pinned `render_crit_pack`/`render_batch_crit_pack` parameter lists are
      unchanged — which is exactly why no pack parameter was added.
    - `CON-run-identity.md`, `INV-reference-menu.md`, `SEAM-llm-x-scheduler.md`,
      `SUB-periphery.md`, `SUB-scheduler.md` — all list only cfe8d111c, a
      commit from ANOTHER tranche (P-C2) that predates this branch.
      **Dismissed:** not this tranche's staleness, and not this tranche's to
      clear; also listed against `SEAM-rules-x-scratch.md` above.
    - `SUB-llm.md`, `SUB-manifest.md` — list aa3e9cbc2 / ba4720a95 / 8240f8b95 /
      b6727ceea / debff8d9b, all from earlier tranches. **Dismissed:** predate
      this branch entirely.

    None of the eight is stale BECAUSE of this change except
    `SEAM-rules-x-scratch.md`, and that one is dismissed on its own green
    checks rather than on assertion.

    new checks added by this change:
      docs/map/CON-problem-layer-lifecycle.md — 2 (the four ladder tests; the
        arithmetic pin `refuted >= after * (standing + 1)` plus `A == 2`)
      docs/map/CON-criticism-source.md — 2 (the four disposition tests; an AST
        pin that the invitation lookup is the FIRST statement of
        `_file_attribution`, which is the thing that would silently regress)
      Both were RUN by hand before being written down, per DR-SCHEMA.

    record observables added vs sweep probes:
      One observable — the `premise-answer:{DECLINED|UNCITED|CITED}` Measure
      family. Its probe is `probes/p11_ladder_counterfactual.py`, committed in
      this tranche and re-run against the CHANGED tree, which reads the shipped
      predicate directly (`"shipped_agrees_with_new": true` on all four roots).
      The root sweep itself is RETIRED (operator ruling 2026-08-22) and is
      therefore not owed; SPEC.md's step-4 guardrail is met by the absence-
      tolerant direction of the change — the receipt is ADDITIVE, so every
      committed root reads correctly with it absent, which is what
      `test_an_uninvited_dispatch_records_no_disposition` and the four
      historical roots (0 `premise-answer:` events, all still replayable)
      demonstrate.

    wheel smoke:
      $ python scripts/wheel_smoke.py
      wheel smoke passed: isolated V6-only contents, clean imports, exact entry
      points, module parity, MCP registration, and exact MCP schemas

      Run even though the packaging surface did not move (no change to
      pyproject.toml, console entry points, the MCP tool set or the wheel
      layout), because no gate runs it and the cost of being wrong about
      "untouched" is a silently rotted instrument.
      `wheel_operational_smoke.py` NOT run and NOT owed: the operational
      provider-facing surface did not move — no contract, no contract id, no
      role, no endpoint and no manifest field changed.

## Requirement sweep

| R | demonstrated by |
|---|---|
| R1 (a problem can invite premise work more than once under a stated rule) | S1's four ladder tests; the shipped predicate replayed over four committed roots — epoch 6 goes from 2 to 10 open dispatches, `"shipped_agrees_with_new": true` |
| R2 (answer the latch question, with the price) | ANSWERS.md §(1): the rule, all three alternatives refuted on measurements, and the price read from the prompt bytes (~1 035 tokens per invited dispatch; ~1.1 % of the epoch-6 run) |
| R3 (type the invited-and-declined case; agree or refute) | ANSWERS.md §(2) AGREES and strengthens (four cases, not two); S2 + S3's tests; `test_an_uninvited_dispatch_records_no_disposition` proves silence still means never-asked |
| R4 (decide the uninvited schema field) | ANSWERS.md §(3): NO, on four reasons, two of them read from source (the hardcoded contract id; the closed Literal → `pair_inventory` → qualification digest chain). Acceptance output is the EMPTY contract diff |
| R5 (a regression driving a run where the channel opens after a late refutation) | `test_a_late_refutation_reopens_the_channel_in_the_real_loop`, driving `Scheduler.step` three times; mutation-proven in proof/s4_red.txt → proof/s4_green.txt |
| R6 (full gate 0 failed; map in the same commit) | 4384 passed, 6 skipped, 0 failed; commits 13ed9b50f and 9b4801d2f each carry their map documents |
| R7 (note that live M2 re-measurement waits for both tranches) | SPEC.md "R7 — live re-measurement of M2"; ANSWERS.md §R7 |
| R8 (park the planted-presupposition probe) | PARKED.md P14, unstarted, with a ready-to-send prompt |
| R9 (R-by-R delivery with pasted proof) | DELIVERY.md (next phase), built on this table |

No R is deferred. Every one has an acceptance output above.

## Assumptions carried (SPEC.md, for the operator to overrule)

- **A1** — the reopen rule is the multiplicative ladder rather than "any new
  refutation reopens". Chosen because the bare version is unbounded in
  invitations per problem (~43 000 tokens on epoch 6 alone) and the brief asked
  for the cost of re-asking to be priced.
- **A2** — the disposition gets its own `premise-answer:` tag namespace. Forced
  rather than chosen: `premise-citation:` IS the M2 census's definition.
- **A3** — no committed digest pin moves. Verified: `qualification_digest: []`,
  `wheel_smoke_pins: []`, and the frozen-surface diff is empty.
- **A4** — `PREMISE_INVITE_AFTER` stays a module constant. The modularity law
  wants it reachable as configuration and frozen surface 4 stands in the way;
  parked as P16 rather than resolved silently.
- **A5** — the disposition is derived from the same `_premise_invited_problem`
  lookup the filing gate uses, not from the invitation the PACK carried, so the
  record holds one answer to one question.

Two budget overruns are also carried, both recorded as dated amendments in
SPEC.md with the tool's own output pasted rather than by rewriting the headline
to match the diff: total 416 insertions against an original 233 (the overrun is
entirely in the regression tests R5/R6 mandate), and source 73 against 60, of
which **10 are executable statements** and the remaining 63 are the signal
declaration's required semantics and two docstrings naming the run ids the
change answers to.

## Verdict: PASS
