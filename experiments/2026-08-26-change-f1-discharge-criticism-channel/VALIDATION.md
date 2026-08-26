# Validation for: the discharge-required criticism channel (REBUILD F1)

REQUEST.md (4 amendments), SPEC.md (16 items) and CHECKLIST.md (32 steps, 3
re-sequenced) re-read in full before this phase. Every check below was RUN here,
including ones a checklist step already ran: a step proves local progress, this
phase proves the assembled whole.

## Acceptance checks

    S1  (R12-R15) declared interface + VERSIONED registry, KINDS derived
        $ python -c "...KINDS == {n: d.asserts ...}; kind names == the three..."
        -> exit 0                                                        : PASS

    S2  (R1,R2,C1) open criticisms read from BOTH channels
    S3  (R1,R2)    the render, inside the binding block
        $ python -m pytest tests/test_discharge_channel.py -q
        15 passed in 0.58s                                               : PASS

    S4  (R3,C5,C6) the typed discharge on the wire, pruned when off
        $ python -m pytest tests/test_discharge_wire.py -q
        11 passed in 0.39s                                               : PASS
        $ python -c "...qualification_subject_digest == b9038b84efdea313..."
        -> exit 0  (subject digest unmoved)                              : PASS

    S5  (R3,R4)  discharge-required submission, re-ask once, then disclose
    S6  (R3,R6)  discharge records, and the rebuttal in the ordinary graph
        $ python -m pytest tests/test_discharge_submission.py -q
        18 passed in 0.44s                                               : PASS

    S7  (R5,R7,R8) THE LAW LINE, pinned four ways
    S10 (R10)      no label differs, channel on vs off
        $ python -m pytest tests/test_discharge_law_line.py -q
        6 passed in 2.29s                                                : PASS
        $ grep -c FAILED proof/c3_red.txt   ->  1                        : PASS
        (the mutation: a discharge import wired into
         adjudication/support.py::final_labels. RED, then green on restore.)

    S8  (R12,R13,R14) the architecture test that can go RED
        $ python -m pytest tests/test_discharge_contract.py -q
        6 passed in 3.93s                                                : PASS
        $ grep -c FAILED proof/arch_red.txt ->  2                        : PASS
        (two checks fire on the hard-coded enum, not one -- the second was
         not designed for it and caught it anyway.)

    S9  (R9) the coupling instrument, channel on vs off
        $ python coupling.py out.json
         on: [W2 instrument] n=6   coupling=1.0 placebo=0.0
                                   coupling-placebo=1.0 neglect=0.0
                                   [reproduction agrees: True]
        off: [W2 instrument] n=11  coupling=0.0 placebo=0.0
                                   coupling-placebo=0.0 neglect=1.0
                                   [reproduction agrees: True]
        $ python -c "...on > 0; off == 0; cross-check agrees..."
        -> exit 0                                                        : PASS

    S11 (R10) the map moves in the same commits            -> see ## Map : PASS
    S12 (R10) the gate                                -> see ## Full gate : PASS

    S13 (R16) the granted contact and its four riders
        $ python -c "...source_config_hash v1..v6 unmoved..."  -> exit 0  : PASS
        $ grep -c 'data.pop("DISCHARGE_POLICY", None)' run_manifest.py = 1: PASS
        $ diff proof/digest_before.txt proof/digest_after.txt
        (empty, exit 0)                                                  : PASS

    S14 (R17,R18) the C6 disposition and the F2 composition note
        $ grep -qi "reference-bearing" ... && handle annotation is str
        -> exit 0                                                        : PASS

    S15 (R19,R21,R22) the ceiling, and the typed STOP if it moves
        $ python tools/diff_budget.py 4760a32ef --paths src/ --ceiling 960
        {"areas": {"src/": 943}, "ceiling": 960, "verdict": "WITHIN"}     : PASS
        Both EXCEEDED events were raised as typed STOPs, never absorbed:
        907/900 resolved by DELETING dead code (no raise spent), and 943/900
        resolved by the operator's ruling after the number was proved final.

    S16 (R20) what RESULTS.md may claim
        $ grep -q "What this does NOT establish" && ! grep -qi "<overclaim>"
        -> exit 0                                                        : PASS

## Full gate

    $ python -m pytest tests/ -q -n 4
    4231 passed, 6 skipped in 958.70s (0:15:58)                          : PASS

0 failed. 4231 against 4225 measured mid-tranche; the +6 is exactly
`tests/test_discharge_law_line.py`, which landed after that run. This tranche's
five test files collect **56 tests**. No assertion anywhere was weakened: two
existing pins were CORRECTED to the truth with the correction recorded (the pack
section count 17->18, the architecture test's consumer list one->two), and one
pin that caught something real was OBEYED rather than adjusted (the signal
contract's three declarations).

## Record-behavior preservation

**n/a for readers, and that is checked rather than assumed.** The change touches
no reader or validator of the append-only record: `invariants.py`,
`verification/`, `harness.py` and `capabilities/state.py` are untouched (see the
frozen-surface diff below). The one frozen-surface file that moved,
`run_manifest.py`, gained a line whose entire effect is to keep a digest STILL,
proven by the empty before/after diff at S13.

The channel WRITES three new Measure kinds. They are additive: no committed root
contains them, every existing root replays unchanged, and the reader
(`discharged_handles`) treats their absence as valid — which is the
reader-before-writer guardrail, satisfied trivially here because the reader
ships in the same tranche and tolerates absence by construction.

## Frozen-surface diff

    $ git diff --stat 4760a32ef..HEAD -- \
        src/deepreason/capabilities/state.py src/deepreason/harness.py \
        src/deepreason/invariants.py src/deepreason/run_manifest.py \
        src/deepreason/qualification.py
     src/deepreason/run_manifest.py | 9 +++++++++
     1 file changed, 9 insertions(+)

NON-EMPTY, and **explained by an operator grant quoted verbatim in REQUEST.md
Amendment 2 (R16)**: *"GRANTED: the one-line versioned-source entry for
DISCHARGE_POLICY in run_manifest.py. This is not an exception to the frozen
surface — it is the documented recipe."* Four riders, all discharged (S13).
Nine insertions, zero deletions; the line is one `data.pop` plus its comment.
The other four surfaces are EMPTY, as expected.

## Map

    docs_verify (FULL):      3 failed                                    : PASS
    docs_verify --audit:     0 finding(s)                                : PASS
    docs_verify --links:     0 dangling, 65 document(s)                  : PASS
    docs_verify --coverage:  7 swept, 17 without Sweep:, 2 finding(s)    : PASS
    docs_verify --stale:     13 document(s) — dismissed below

**The 3 FULL failures are the pre-existing `CON-run-identity` shallow-clone
failures** (lines 200/202/204), identical to the baseline captured at step 1 on
the untouched tree. They reach for commits this container's shallow clone does
not carry; Rung 6's DELIVERY.md records the same three.

**The 2 coverage findings pre-date this change, and that is measured rather than
argued**: checking out the tranche base `4760a32ef` and re-running `--coverage`
gives byte-identical output — `SEAM-schools-x-scratch` (enforcement site not
named) and `SEAM-scratch-x-workflow` (no `Sweep:` header). Neither seam is one
this tranche touched.

**`--audit` 0 findings is the load-bearing line here**, not the failure count.
It refuses checks that CANNOT fail, and this tranche added ~20 across four
documents. Two were rewritten during execution precisely because they would have
been decoration: the granted contact's indent check (mutation M-B proved the
first version vacuous) and two multi-line checks the runner could not execute.

### `--stale`: every entry dismissed with its reason

Eight are stale because of ANOTHER tranche's commit (`4e9af3405`, the poietics
program) and are not this change's to answer: `CON-run-identity`,
`CON-standing-and-background`, `SEAM-evaluation-x-rules`, `SEAM-llm-x-scheduler`,
`SUB-adjudication`, `SUB-calculus`, and the poietics halves of
`INV-signal-contract` and `SUB-periphery`.

Five are stale because of THIS change. Each was examined for a decayed unchecked
claim; none needs updating, so none is a FAIL:

- `CON-packs-and-token-economy` — UPDATED by this tranche at step 7/8 (section
  count 17->18, the new section's rules, the output-contract precondition) and
  its checks re-run there. The stamp sits at the parent commit, so it
  UNDER-claims. `DR-SCHEMA`: "a stale stamp is honest, a false one is not."
- `INV-frozen-surfaces` — UPDATED at step 2b with the granted contact and three
  new checks, all run. Stamp not advanced; under-claims, same rule.
- `SEAM-llm-x-rules` — UPDATED at step 7/8 with the new boundary row. Later
  commits touched files it owns, so its prose was re-read: the "thirty-nine
  names cross the boundary" census counts `rules/` importing `deepreason.llm`,
  and this tranche added NO such import (`rules/conj.py` imports
  `deepreason.discharge`). Its two pinned counts still read 8 and 8.
- `SEAM-scheduler-x-rules`, `SEAM-capabilities-x-rules` — own `rules/conj.py`.
  They describe the scheduler and capability agreements, neither of which this
  change touches; all their checks pass. Nothing to update.
- `SUB-periphery` — owns `workloads/text.py`, which gained one optional field.
  Read: it enumerates function and class EXISTENCE, never
  `ReasoningCandidateProposal`'s field set. Nothing to update.

### New checks added by this change

`docs/map/CON-discharge-channel.md` — **NEW document, 18 checks**, every one run
individually before commit. Plus new checks in `CON-packs-and-token-economy`
(the section's flags and ordering), `CON-criticism-source` (where an
`observe_only` criticism now goes), `CON-conjecture-source` (the submission
precondition and the unchanged call census), and `INV-frozen-surfaces` (three
for the granted contact). Behaviour this change ADDED is therefore covered by
falsifiable map checks, not only by tests.

### Record observables added vs sweep probes

Three: the Measures `discharge:<kind>`, `discharge-reask`,
`discharge-undischarged`. **No sweep probe is owed, and the reason is
structural rather than an exemption.** `tools/root_sweep.py` compares
`valid`, `epistemic_checks_passed`, `len(state.att)`, adjudication-blindness,
module digests and seat digests. A Measure reaches none of them: it mints no
attack edge (pinned by
`test_a_discharge_measure_is_not_an_attack_edge`), moves no label (pinned by
`test_no_label_differs_between_channel_on_and_channel_off`), and changes no
digest. The observables ARE covered — by the three `SignalDeclaration` entries
the signal registry demanded, which is this repository's own typed channel for
exactly this, and by `tests/test_signals.py`, which fails on any emitted signal
that is not declared. Recorded here rather than left silent.

### Wheel smoke

    $ python scripts/wheel_smoke.py
    wheel smoke passed: isolated V6-only contents, clean imports, exact entry
    points, module parity, MCP registration, and exact MCP schemas
    $ python -u scripts/wheel_operational_smoke.py
    wheel operational smoke passed: ... (80 qualification calls; 418 total
    calls) ...
    $ git diff -- scripts/    (empty)

The packaging surface was NOT moved — no entry point, MCP tool or wheel-layout
change — so the smokes were not strictly owed. They were run anyway, as proof
rather than assurance, because no gate runs them. "exact MCP schemas" is the
line that matters: a `discharges` field leaking into the published tool schema
would have failed there and nowhere else. "80 qualification calls", unchanged,
is the operational restatement of S13.

## Requirement sweep

| R | Demonstrated by |
|---|---|
| R1 open criticisms render in the writer's section, claim + span + handle | S3 (`test_the_render_carries_the_claim_the_span_and_the_handle`, `..._lands_in_the_binding_block_not_a_sidebar`) |
| R2 Rung 6's machinery; renders every cycle until discharged, asserted at terminal | S3 (`test_a_criticism_at_cycle_k_still_renders_at_the_terminal_cycle`, cycle 8 at a budget measured to bite) |
| R3 per-handle typed discharge: REVISED / REBUTTED / DEPARTURE-DECLARED | S4 + S5 |
| R4 returned ONCE with the open list, then accepted with a typed disclosure | S5 (`..._returned_once_with_the_open_list`, `..._second_submission_is_accepted_with_a_disclosure`, `test_no_candidate_is_ever_refused`) |
| R5 the law line stated in SPEC and pinned by test | SPEC S7 states it; S7 pins it |
| R6 a REBUTTED discharge is an ordinary criticism artifact in the graph | S6 (`test_a_rebuttal_is_itself_attackable`, `..._carries_only_mention_refs`) |
| R7 mutation-prove the boundary | S7, `proof/c3_red.txt` |
| R8 formalism-optional: no rank, no admission weight | S7 (no numeric field; admission byte-identical) |
| R9 coupling nonzero with the channel on, W2's operationalization R1 | S9, **+1.0 on / 0.0 off**, by W2's own instruments |
| R10 disclosure works; C3 proof; no label differs; gate; docs_verify; map in same commits | S5, S7, S10, Full gate, Map |
| R11 do NOT build an acknowledgment requirement | S5 (`test_no_kind_is_satisfied_by_acknowledgment` + its permanent mutation companion) |
| R12 discharge policy is a registered, config-selectable policy | S1, S8 (`test_a_fourth_kind_enters_by_declaration_alone`) |
| R13 every knob reachable as configuration or a versioned artifact | S8 (`..._channel_toggle_is_pure_configuration`, `..._cap_change_...`) |
| R14 declared interface + an architecture test that goes RED | S8 + `proof/arch_red.txt` |
| R15 at a design fork, the interface wins | S1 and SPEC's Options: the tighter 40-line coupling REJECTED citing R15 |
| R16 the granted contact and its four riders | S13 (all four discharged) |
| R17 read C6 as "F2's fields" | S14; SPEC S14 records the disposition |
| R18 record the F2 composition note | S14; `CON-discharge-channel` §"The F2 composition note" |
| R19 typed STOP if it grows beyond what SPEC declares | S15 — two EXCEEDED events, both raised, neither absorbed |
| R20 F1 claims DELIVERY, not RESPONSE | S16; RESULTS.md segment 3, eight residue items |
| R21 ceiling 900 | superseded by R22; ledgered |
| R22 ceiling 960 | S15 |

**Every R is demonstrated. None deferred.**

## Assumptions carried (SPEC.md, operator may override)

- **A1** "inside the working section" = pack priority 2 beside `criteria`,
  non-droppable, non-compressible, plus the output-contract precondition.
- **A2** "open" = an `observe_only` scrutiny Measure OR an attack edge, on a
  target addressed to the problem, neither discharged nor itself REFUTED.
- **A3** the handle IS the critic artifact id.
- **A4** the ONCE is counted per conjecture DISPATCH.
- **A5** the terminal assertion is Rung 6's, applied to this section.
- **A6** "nonzero" read on R1_mechanical placebo-corrected; R2 not quoted.
- **A7** `Config.DISCHARGE_POLICY` defaults to `"off"` — turning it on is F3's.
- **A8** a kind may require only `note`/`where`; anything else is a wire change
  (PARKED P3).

## Verdict: PASS

Every acceptance check ran with pasted output; the full gate is 0 failed; the
map is at its baseline with `--audit` clean; the one frozen-surface contact is
covered by a verbatim operator grant with all four riders discharged; every
requirement is demonstrated; no requirement deferred.
