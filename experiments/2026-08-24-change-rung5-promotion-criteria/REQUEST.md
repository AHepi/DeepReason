# Request: Rung 5 of the v2 calculus program — promotion problems and their criteria as programs
Captured: 2026-08-24 from the operator's single task message opening this session.

Map preflight (recorded here so every later phase starts from the same map):
`DR-SUB-calculus` (the typed claim substrate and the standing view),
`DR-SUB-evaluation` (programs, measures), `DR-SUB-rules` (spawn),
`DR-SEAM-evaluation-x-rules` (the seam the ladder names as this rung's exit
artifact), `DR-CON-standing-and-background`, `DR-CON-problem-layer-lifecycle`,
`DR-INV-frozen-surfaces` (read before designing), `DR-INV-axiom-basis`
(A8 is this rung's obligation; A4 and Ax 4.1 are preserved).

## Verbatim

> TARGET REPOSITORY: AHepi/DeepReason — verify before anything else;
> if this session is based elsewhere, ask the operator to attach it
> with push access and STOP until then.
>
> Change tranche: Rung 5 of the v2 calculus program — promotion
> problems and their criteria as programs. Route through
> dr-change-orchestrator; the workflow's own stop conditions apply,
> nothing else stops.
>
> SETUP (fresh container): git fetch origin main && git checkout -B
> <your session-designated branch> origin/main; git merge-base
> --is-ancestor ade214037 HEAD || re-fetch. pip install -e .
> --break-system-packages -q; pip install pytest pytest-xdist
> jsonschema --break-system-packages -q. Use `python -m pytest`,
> never bare pytest. Read CLAUDE.md in full; load dr-drive-harness,
> dr-explain-to-operator.
>
> AUTHORITY: experiments/2026-08-14-change-calculus-reconciliation-v2/
> LADDER.md, Rung 5 — read the section IN FULL before SPEC.md, plus
> DECISIONS.md D-6 (answered: program-first `accounts-for`, judges
> optional — succession works solo; a rubric ruling enters only
> through the existing trial guard) and REQUEST.md R57 (the STRONG
> succession relation, Rider 4). Entry conditions met: Rung 4
> delivered (frame assertions, standing view), and the live-run gate's
> fixture now EXISTS: experiments/2026-08-22-change-epoch3-second-
> lineage/run (run id bb045538..., one recorded reach_set event,
> verify_root clean) — read its RESULTS.md 2026-08-24 segment for
> exactly what it contains.
>
> WORK, per the ladder:
> - NOMINATION as a measure-rule over the log (C5 channel (a)): reach
>   events for one subject spanning >= K_frame distinct problem
>   lineages over a coherent candidate scope => Spawn a promotion
>   problem. The measure DETECTS; it never decides — promotion itself
>   is an ordinary Conj->Crit->Adj pass. K_frame ships as a Config
>   knob with its _versioned_source_config_data line for EVERY schema
>   version (the ENGAGED_CRITICISM_AUTHORITY trap).
> - The five pinned criteria as programs: subject-demarcation,
>   reach-integrity (against the log's own timestamps, reusing the
>   sealed-holdout machinery, I-6), scope-determinism, compatibility
>   (an overlapping consulted assertion routes to discrimination —
>   rivals never co-frame), accounts-for.
> - accounts-for implements the STRONG succession relation (R57;
>   Formalization §3.5): four parts, ALL required — recovery
>   (X(e) ⊆ X(e'), or an unrefuted account of why e worked over its
>   restricted domain), rigidity (no easier to vary over the shared
>   explicanda), non-immunization (no proper functional component of
>   e' removable while preserving every registered accounting and
>   criticism outcome), and a strictness witness (at least one of
>   recovery, criticism survival, or rigidity STRICT). Building the
>   weak form first is FORBIDDEN by the rider — this program has paid
>   twice for that ordering.
> - Remark 9.5's default-consult closure: criteria instantiated at
>   registration generate demonstrative program warrants BEFORE the
>   renderer's next consultation; the renderer consults only
>   assertions addressed to promotion problems.
> - The §12.2 closing clause Rung 2 could not meet: for empirical
>   scopes, at least one commitment must be observation-valued
>   (drift row S-5); reuse Rung 2's cost answer (cache per subject,
>   one sample per run life, typed abstention when the variator seat
>   is absent).
> - Prop 12.6, D-4 answered A: the knowledge view, always rendered
>   with its definition inline ("knowledge (unrefuted ∧ active ∧
>   reach > 0)"), never the bare word.
>
> GATE PROVES (each named in VALIDATION.md):
> - THE STRONG RELATION REFUSES, four ways: a rival that merely
>   recovers the incumbent's explicanda is refused as a successor
>   (the test that passes under the weak reading and must fail under
>   this one); an easier-to-vary rival refused on rigidity; a rival
>   with an excisable idle part refused on non-immunization; a rival
>   meeting every clause non-strictly refused for want of a
>   strictness witness. Mutation proof on at least the first.
> - M-4 BOTH HALVES, and the live root is the negative half:
>   nomination fires on constructed lineage-spanning reach fixtures
>   at the K_frame threshold — and does NOT fire on the committed
>   attempt-4 root, whose one reach event spans ONE lineage. That
>   no-fire on real live data is as load-bearing as the fire.
> - Remark 9.5: an assertion registered outside a promotion problem
>   is an ordinary artifact the renderer ignores; an unattacked one
>   addressed to a promotion problem does not silently frame its
>   scope, because its criteria fire first.
> - Prop 12.1: every criterion terminates inside its declared budget;
>   overrun means unobtainable, never slow (C2).
> - L-3: the whole promotion path completes on a SOLO configuration.
> - L-6: nomination measured on the committed attempt-4 root (the
>   negative control above) rather than on synthetic data alone.
> - Axiom ledger (§5b): this rung PROVES A8 (reach can spawn
>   promotion problems but cannot directly alter labels); PRESERVES
>   A4, Genesis Inertness (no criterion reads WHO produced content).
>
> FROZEN SURFACES (ladder row): surface 4 zero — new knobs on Config
> only, each with its versioned-source line; surfaces 1, 2, 3, 5
> zero; NO new LLM role (a design wanting one must STOP and ask — it
> moves every qualification digest). Public surface unchanged — no
> wheel re-pin expected.
>
> SIZE: ladder estimates 400-600 lines. If SPEC.md's plan exceeds
> ~800, STOP and say what grew.
>
> KNOWN CURRENT STATE: gate baseline 0 failed (3879 + soak tranche
> additions at ade214037 — re-derive the count at your base);
> docs_verify 3 pre-existing CON-run-identity.md shallow-clone
> failures (0 on an unshallowed clone); 5 MCP-thread tests
> known-flaky under -n 4; both wheel smokes green; the cycle soak
> (scripts/cycle_soak.py --case epoch3) expects exit 0 and is a
> pre-LAUNCH instrument only — this rung launches nothing, so it is
> not owed. The sweep is retired. A parallel window may be running
> the treadle install pilot (tools/treadle/, skills/, its own
> experiment dir) — no shared files; if you find yourself editing
> treadle paths, STOP.
>
> GATE: ring while iterating; full gate at the boundary; docs_verify
> full. Map moves in the same commits (promotion lifecycle updates
> DR-SEAM-evaluation-x-rules per the ladder; new checks that would
> fail on regression, run before written). Commit and push every
> phase boundary (retry 2s/4s/8s/16s). Deliver R-by-R with pasted
> PROOF, closing with two lines: what now causes a promotion problem
> to exist, and what a rival must survive to be called a successor.

## Requirements

R1 (behavior): "NOMINATION as a measure-rule over the log (C5 channel (a)): reach
events for one subject spanning >= K_frame distinct problem lineages over a
coherent candidate scope => Spawn a promotion problem."

R2 (behavior): "The measure DETECTS; it never decides — promotion itself is an
ordinary Conj->Crit->Adj pass."

R3 (behavior): "K_frame ships as a Config knob with its
_versioned_source_config_data line for EVERY schema version (the
ENGAGED_CRITICISM_AUTHORITY trap)."

R4 (behavior): "The five pinned criteria as programs: subject-demarcation,
reach-integrity (against the log's own timestamps, reusing the sealed-holdout
machinery, I-6), scope-determinism, compatibility (an overlapping consulted
assertion routes to discrimination — rivals never co-frame), accounts-for."

R5 (behavior): "accounts-for implements the STRONG succession relation (R57;
Formalization §3.5): four parts, ALL required — recovery (X(e) ⊆ X(e'), or an
unrefuted account of why e worked over its restricted domain), rigidity (no
easier to vary over the shared explicanda), non-immunization (no proper
functional component of e' removable while preserving every registered
accounting and criticism outcome), and a strictness witness (at least one of
recovery, criticism survival, or rigidity STRICT)."

R6 (process): "Building the weak form first is FORBIDDEN by the rider — this
program has paid twice for that ordering."

R7 (behavior): "Remark 9.5's default-consult closure: criteria instantiated at
registration generate demonstrative program warrants BEFORE the renderer's next
consultation; the renderer consults only assertions addressed to promotion
problems."

R8 (behavior): "The §12.2 closing clause Rung 2 could not meet: for empirical
scopes, at least one commitment must be observation-valued (drift row S-5);
reuse Rung 2's cost answer (cache per subject, one sample per run life, typed
abstention when the variator seat is absent)."

R9 (behavior): "Prop 12.6, D-4 answered A: the knowledge view, always rendered
with its definition inline ("knowledge (unrefuted ∧ active ∧ reach > 0)"), never
the bare word."

R10 (process): "THE STRONG RELATION REFUSES, four ways: a rival that merely
recovers the incumbent's explicanda is refused as a successor (the test that
passes under the weak reading and must fail under this one); an easier-to-vary
rival refused on rigidity; a rival with an excisable idle part refused on
non-immunization; a rival meeting every clause non-strictly refused for want of
a strictness witness. Mutation proof on at least the first."

R11 (process): "M-4 BOTH HALVES, and the live root is the negative half:
nomination fires on constructed lineage-spanning reach fixtures at the K_frame
threshold — and does NOT fire on the committed attempt-4 root, whose one reach
event spans ONE lineage. That no-fire on real live data is as load-bearing as
the fire."

R12 (process): "Remark 9.5: an assertion registered outside a promotion problem
is an ordinary artifact the renderer ignores; an unattacked one addressed to a
promotion problem does not silently frame its scope, because its criteria fire
first."

R13 (process): "Prop 12.1: every criterion terminates inside its declared
budget; overrun means unobtainable, never slow (C2)."

R14 (process): "L-3: the whole promotion path completes on a SOLO
configuration."

R15 (process): "L-6: nomination measured on the committed attempt-4 root (the
negative control above) rather than on synthetic data alone."

R16 (process): "Axiom ledger (§5b): this rung PROVES A8 (reach can spawn
promotion problems but cannot directly alter labels); PRESERVES A4, Genesis
Inertness (no criterion reads WHO produced content)."

R17 (process): "Deliver R-by-R with pasted PROOF, closing with two lines: what
now causes a promotion problem to exist, and what a rival must survive to be
called a successor."

## Standing constraints

C1: "FROZEN SURFACES (ladder row): surface 4 zero — new knobs on Config only,
each with its versioned-source line; surfaces 1, 2, 3, 5 zero; NO new LLM role
(a design wanting one must STOP and ask — it moves every qualification digest).
Public surface unchanged — no wheel re-pin expected." — operator message,
FROZEN SURFACES.

C2: "SIZE: ladder estimates 400-600 lines. If SPEC.md's plan exceeds ~800, STOP
and say what grew." — operator message, SIZE.

C3: "GATE: ring while iterating; full gate at the boundary; docs_verify full.
Map moves in the same commits (promotion lifecycle updates
DR-SEAM-evaluation-x-rules per the ladder; new checks that would fail on
regression, run before written). Commit and push every phase boundary (retry
2s/4s/8s/16s)." — operator message, GATE.

C4: "Route through dr-change-orchestrator; the workflow's own stop conditions
apply, nothing else stops." — operator message, Change tranche.

C5: "A parallel window may be running the treadle install pilot
(tools/treadle/, skills/, its own experiment dir) — no shared files; if you find
yourself editing treadle paths, STOP." — operator message, KNOWN CURRENT STATE.

C6: "the cycle soak (scripts/cycle_soak.py --case epoch3) expects exit 0 and is
a pre-LAUNCH instrument only — this rung launches nothing, so it is not owed.
The sweep is retired." — operator message, KNOWN CURRENT STATE.

C7: "DECISIONS.md D-6 (answered: program-first `accounts-for`, judges optional —
succession works solo; a rubric ruling enters only through the existing trial
guard)" — operator message, AUTHORITY.

## Open questions (for dr-spec-change)

Q1: "distinct problem lineages" has no definition anywhere in the tree — the
word `lineage` currently names school lineage and the `lineage_ref` commitment,
neither of which is a problem ancestry. The rung must define it, and the
definition decides whether the live root fires or not (R11 requires it does
NOT).

Q2: "a coherent candidate scope" — what makes a candidate scope coherent, and
who authors it during nomination, given that nomination is a measure-rule and
`FrameAssertionV1.scope` is authored content.

Q3: the five criteria are "programs", but a criterion in this tree is a
`Commitment` whose `eval` names a registry program taking `(text, budget,
artifact)`. Several of the five need HARNESS state (the log, addr, reach,
statuses), which that signature does not carry. Q: how do the criteria reach
run state without widening the program signature or the frozen event surface.

Q4: "recovery (X(e) ⊆ X(e'))" — what set X is, concretely, over this record.

Q5: whether the knowledge view (R9) is a new CLI/MCP surface (which would touch
the public surface C1 says is unchanged) or a library-level view only.

Q6: whether the demonstrative program warrants of R7 fire through
`register_fail_warrant` (the tree's one warrant constructor) and therefore need
a criterion-instantiation site at promotion-problem registration.

## Amendments
(append-only)

### Amendment 1 — 2026-08-24, the size ceiling is EXCEEDED (C2, self-reported)

No new operator words. This amendment records a breach of a constraint the
operator set, at the moment it was measured, rather than at delivery.

C2, verbatim: "SIZE: ladder estimates 400-600 lines. If SPEC.md's plan exceeds
~800, STOP and say what grew."

SPEC.md's PLAN was 686 production lines — under the threshold, so no stop was
owed at spec time, and none was taken. The DELIVERED production diff is **1 442
insertions across `src/`**, against that 686. Measured by
`python tools/diff_budget.py ade214037`: 4 503 insertions in total against the
ledgered all-paths ceiling of 1 900, verdict **EXCEEDED**.

**What grew, itemized rather than summarized:**

| Area | Planned | Actual | Why |
|---|---|---|---|
| `calculus/nomination.py` | 170 | 463 | the certificate BUILDER — freezing problems, criterion specs, the candidate pool with its demarcation/HV/accounting/wound readings, and the reveal seqs — is most of the file. SPEC.md itemized the certificate's SHAPE under S3 (95 lines, in `claims.py`) and never separately costed the code that fills it |
| `calculus/promotion.py` | 275 (S4–S9) | 587 | five criteria plus the shared frozen-input contract, the succession relation as a standalone function, and the closure sweep |
| `claims.py` + `compiler.py` + `calculus/programs.py` | 95 | 160 | four `_Part` models the criteria turned out to need (`FrozenProblemV1`, `FrozenCommitmentV1`, `FrozenSubjectV1`, `ReachRecordV1`, `FrozenGrantV1`) |
| `programs.py` registration | 35 | 71 | the dual-registration wrappers and their reason |
| everything else (`config`, `run_manifest`, `scheduler`, `cli`, `views/knowledge`) | 111 | 161 | close to plan |

**The honest part of the account.** 268 of `nomination.py`'s 463 lines and 357
of `promotion.py`'s 587 are CODE; the remainder is docstrings, comments and
blank lines, which this repository's own convention asks for ("comments state
constraints the code cannot show"). By that measure the two new modules are 625
lines of code against a 445-line plan for them — still over, by ~40 percent, and
still an overrun. The line count is not what was underestimated; the frozen
certificate's builder was.

**No scope was added to buy this.** Every line traces to an S-number and an
R-number; nothing outside REQUEST.md was implemented. The overrun is an
estimating failure at SPEC time, not scope creep at execution time, and it is
reported here rather than at delivery so the operator sees it while the tranche
is still open.
