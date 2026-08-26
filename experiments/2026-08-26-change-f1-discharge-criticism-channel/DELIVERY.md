# Delivered: the discharge-required criticism channel (REBUILD tranche F1)

Branch: `claude/rebuild-discharge-criticism-channel-2b8z8i` (pushed, tree clean).
Base: `origin/main` at `4760a32ef`. VALIDATION.md verdict: **PASS**.

## What changed

Criticism on this tree was recorded and then routed nowhere. W2 measured the
consequence exactly: across the two newest and largest committed roots, **0 of
196 LLM attacks ever reached a later conjecture dispatch**, and every status a
criticism moved was moved by the problem's own admission criteria rather than by
anything a critic seat wrote.

F1 closes that. Open criticisms on a problem now render **inside the
conjecturer's binding block** — at pack priority 2, beside `criteria`, above
`mandatory-interface` and far above every advisory section — each carrying its
claim, its cited span and a stable handle. A candidate submitted on such a
problem must carry a typed discharge per handle: `revised`, `rebutted` or
`departure_declared`. A submission with undischarged handles is returned **once**
with the open list and then **accepted with the gap recorded** — there is no
verdict that refuses.

New package `src/deepreason/discharge/` (interface, versioned kind registry and
policy presets, record reader and render, submission screen). `llm/packs.py`
gains one non-droppable section and the output-contract precondition;
`llm/contracts.py` gains `DischargeWireV1` and a registry-derived kind enum;
`CompactConjectureCandidate` and `ReasoningCandidateProposal` each gain one
optional `discharges` field, pruned from the emitted schema when the channel is
off; `rules/conj.py` renders and screens; `config.py` gains `DISCHARGE_POLICY`
with its `run_manifest.py` versioned-source line; `signals.py` declares the
three Measures the channel emits.

**Proven, by W2's own committed instruments run unmodified on two stub-driven
roots differing only in `Config.DISCHARGE_POLICY`:**

| arm | n | CouplingRate | PlaceboRate | **Coupling − Placebo** | NeglectRate |
|---|---|---|---|---|---|
| channel **on** | 6 | 1.0 | 0.0 | **+1.0** | 0.0 |
| channel **off** | 11 | 0.0 | 0.0 | **0.0** | 1.0 |

The off arm reproduces W2's finding on this tree. The on arm is the first
nonzero placebo-corrected coupling this repository has recorded. **The channel
ships OFF** — turning it on is a Config default and belongs to F3.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "open criticisms … render INSIDE the conjecturer's working section … the claim, the cited span, and a stable discharge handle" | **done-with-assumption A1, A3** | `73301eca1`; VALIDATION S3 |
| R2 | "Rung 6's render machinery is the vehicle; renders every cycle until discharged, asserted at terminal" | **done-with-assumption A5** | `73301eca1`; S3 `…still_renders_at_the_terminal_cycle` |
| R3 | "a new candidate … must carry, per criticism handle, a typed discharge: REVISED, REBUTTED, or DEPARTURE-DECLARED" | **done** | `311371182`, `439175375`; S4 + S5 |
| R4 | "returned ONCE with the open list … then accepted WITH a typed undischarged disclosure — disclose, never die" | **done-with-assumption A4** | `439175375`; S5 |
| R5 | "THE LAW LINE, stated in SPEC and pinned by test" | **done** | SPEC S7 states it; `f1a…`/S7 pins it |
| R6 | "a REBUTTED discharge is just a criticism artifact entering the ordinary graph" | **done** | `439175375`; S6 |
| R7 | "Mutation-prove the boundary (wire a discharge into label computation … RED, restore)" | **done** | `proof/c3_red.txt`; S7 |
| R8 | "Formalism-optional also binds: discharge kinds carry no rank or admission weight" | **done** | S7 (no numeric field; admission byte-identical) |
| R9 | "the coupling instrument from W2 … coupling must be measurably nonzero with the channel on" | **done-with-assumption A6** | `coupling.json`; S9, **+1.0 / 0.0** |
| R10 | "the disclosure road works; C3's mutation proof; no label differs …; Full gate 0 failed; docs_verify full; map moves in the same commits" | **done** | S5, S7, S10; gate 4231/0; docs_verify at baseline |
| R11 | "do NOT build an acknowledgment requirement — ACK-required measurably HURT" | **done** | S5 `test_no_kind_is_satisfied_by_acknowledgment` + its permanent mutation companion |
| R12 | "the discharge policy … is a registered, config-selectable policy — new discharge kinds enter by declaration" | **done** | S1, S8 `…fourth_kind_enters_by_declaration_alone` |
| R13 | "Every knob … reachable as CONFIGURATION or a REGISTERED VERSIONED ARTIFACT" | **done** | S8 (toggle and cap both pure configuration) |
| R14 | "a DECLARED INTERFACE … and you ship an ARCHITECTURE TEST that goes RED when a consumer bypasses the interface" | **done** | S8 + `proof/arch_red.txt` (two checks fire) |
| R15 | "At any design fork … the interface wins" | **done** | SPEC Options: the 40-line tighter coupling REJECTED citing R15 |
| R16 | "GRANTED: the one-line versioned-source entry … [four riders]" | **done** | `8404bf842`; S13, all four riders |
| R17 | "read C6 as 'F2's fields' — that reading is the intent" | **done** | SPEC S14; `311371182` |
| R18 | "record it in SPEC so F2's window or a successor finds it" | **done** | `CON-discharge-channel` §"The F2 composition note" |
| R19 | "a typed STOP if it grows beyond what SPEC now declares, not silent growth" | **done** | Two EXCEEDED events, both raised; S15 |
| R20 | "F1 claims DELIVERY, not response" | **done** | RESULTS.md segment 3, eight residue items; S16 |
| R21 | "900" | **superseded by R22** | ledgered, REQUEST Amendment 4 |
| R22 | "raise approved. keep going" | **done** | ceiling 960; final `WITHIN` at 943 |

**Nothing deferred. Nothing not-done.**

## Assumptions the operator may override

- **A1** "inside the working section" = pack priority 2 beside `criteria`,
  non-droppable and non-compressible, plus the output-contract precondition.
- **A2** "open" = an `observe_only` scrutiny Measure **or** an attack edge, on a
  target addressed to the problem, neither discharged nor itself REFUTED.
- **A3** the handle IS the critic artifact id.
- **A4** the ONCE is counted per conjecture DISPATCH.
- **A5** the terminal assertion is Rung 6's, applied to this section.
- **A6** "nonzero" read on R1_mechanical placebo-corrected; R2 not quoted as a
  rate (W2's own residue rules it inadmissible).
- **A7** `Config.DISCHARGE_POLICY` defaults to `"off"` — the default is F3's.
- **A8** a kind may require only `note`/`where`; anything else is a wire change.

## Map delta

**Created:** `docs/map/CON-discharge-channel.md` — **18 checks**, each run
individually before commit.
**Changed:** `INDEX.md` (concept table + routing row),
`CON-packs-and-token-economy` (section count 17→18, the new section's flags and
ordering, the output-contract precondition), `CON-criticism-source` (where an
`observe_only` criticism now goes, and that its Measure inputs are now
load-bearing for a second consumer), `CON-conjecture-source` (the submission
precondition and the unchanged provider-call census), `SEAM-llm-x-rules` (the
new boundary crossing), `INV-frozen-surfaces` (the granted contact, 3 checks).

`docs_verify` FULL: **3 failed**, identical to the tranche baseline and all
three the pre-existing `CON-run-identity` shallow-clone failures. `--audit`:
**0 findings** — no check this tranche added is one that cannot fail.
`--links`: clean over 65 documents.

**Left stale:** 13 entries, all dismissed with reasons in VALIDATION.md. Eight
belong to another tranche's commit. Five are this change's: two UNDER-claim
(updated in-tranche, stamp left at the parent commit, which `SCHEMA.md` calls
honest) and three describe agreements this change does not touch, verified by
reading their prose rather than assumed.

## Errata

**E55 added** in this tranche's final commit. CLAUDE.md's full-gate expectation
("~8 min", "expect ~3100 passed") understates the suite by 36% and its duration
by half: measured **4231 passed, 6 skipped in 15:58** on an idle box. Recorded
uncorrected-in-place and deliberately so — the count drifts with every tranche,
so replacing one stale number with another only resets the clock on the same
error. The cost is real: `~8 min` invites killing a gate at ten minutes, which
on this container is halfway through.

## Parked (not done, not promised)

Three entries in PARKED.md, each with a ready-to-send prompt.

- **P1 — `workflow-semantic-admission-v1.admitted_refs` resolve to nothing on
  disk.** W2 found 0 of 163 resolving in P-R1 and worked around it with a
  120-character content-prefix match. F1 does not depend on that pointer, so
  the defect is untouched. Route: `deepreason-orchestrator`.
- **P2 — the live four-arm A/B.** The proof F1 cannot substitute for. Must be
  four arms (no-critique / vacuous-critique / real-as-advice /
  real-in-context), because without the vacuous arm a working critic cannot be
  told from argument-shaped text. Route: a measurement tranche.
- **P3 — F1's stated modularity boundary.** A discharge kind may require only
  `note`/`where`; a kind needing another field is a wire change. A limit, not a
  defect.

**Recommended next: P2.** F1 proves the channel CARRIES criticism and that the
off-state cannot; it does not prove a live model responds, and Q1's finding
forbids assuming it. P2 is the only thing that converts this tranche's
`+1.0` from a property of the plumbing into a claim about reasoning. F3 must
land first if the arms are to be selected by configuration rather than by hand.
