# Spec for: Rung O2 of the grounded-overlay program — DESIGN-AND-STOP
Traces: every item cites R/C numbers. Untraceable items are bugs.

## Map preflight (CLAUDE.md's map-preflight rule)

- `DR-INV-frozen-surfaces` — checked; this design's report-channel
  option touches surface #3 ("Replay-validation record formats" —
  `verification/report.py`); the scheduler-channel option touches
  `scheduler/scheduler.py`, NOT a frozen surface but governed by
  `DR-CON-scheduler-ranking`'s own socket contract; the scratch/
  attention option is ruled OUT before any frozen-surface question
  arises (see Evidence base, below).
- `DR-SUB-verification` — the report channel's actual mechanics
  (`VerificationReportV2.epistemic`, `_adjudication_blindness_findings`
  precedent, `_EPISTEMIC_CHECKS` classification).
- `DR-CON-scheduler-ranking` — the scheduler channel's actual socket
  (`Scheduler._select_problem`'s package-wide guarantee: "attention and
  ranking only... must never... write to disk or assign a Status/hv/
  reach value").
- `DR-SUB-scratch` — read in full; its own Seams table states
  "scheduler x scratch — **deliberately absent**" and
  "criticism receives none of it, structurally" (`DR-SEAM-rules-x-
  scratch`'s own "Where it is expressed" table: `render_crit_pack`'s
  parameter list has no scratch parameter AT ALL — enforced twice,
  pack-side and record-side).
- `DR-CON-warrants-and-attacks`, `DR-SUB-adjudication` — the `att`/
  `dep`/`build_att`/`toposort` machinery this design reads, never
  writes; the DAG-enforcement evidence base for R19 (below).

`check: grep -q "SUB-verification.md" docs/map/INDEX.md && grep -q "CON-scheduler-ranking.md" docs/map/INDEX.md && grep -q "SUB-scratch.md" docs/map/INDEX.md`

## Evidence base: the spec-derived definition of "ground" (R15a, R16, R16a, R19, C7)

All five documents named in REQUEST.md Amendment 1/2 were read in full
this tranche before any design item below was written:
`docs/harness-spec-v1.3.md`, `docs/harness-spec-v1.4-amendment.md`,
`docs/harness-spec-v1.5-amendment.md`, `docs/harness-spec-v1.6-
amendment.md`, `docs/ADMISSION_SPEC.md`.

### The three spec-named exogenous anchors (v1.3 §11.3, untouched by v1.4/v1.5/v1.6)

`harness-spec-v1.3.md` §11.3 ("Detection — grounding ratio λ") is the
ONE place the spec text defines what "grounded" means for a support
chain, verbatim: "fraction of **accepted artifacts whose support
chains bottom out in an exogenous anchor (evidence, program check,
user ruling)** rather than pure conjecture." None of v1.4, v1.5, or
v1.6 touches §11.3 or redefines λ — v1.4 adds the scratch ontology and
the grounded-bridge OUTPUT stage (a different mechanism, see below);
v1.5 separates school/route/scratch/authority concepts and does not
mention λ; v1.6 adds the v5 simulation/inquiry boundary and does not
mention λ. §11.3's three anchors are therefore the CURRENT, unamended
definition, cited to v1.3 alone.

Mapped onto the current tree's own vocabulary, each of the three:

1. **Evidence.** `harness-spec-v1.3.md` §1 (`refs[].role == "evidence"`
   on a warrant validity node) and §12 ("Evidence enters as an artifact
   depending on a source-reliability assertion"). `docs/ADMISSION_SPEC.md`
   §2 (Vocabulary, `Tier` table): admitted content at the `evidence` tier
   is "citable by conjectures; attackable by critics; participates in
   evidence invalidation (`att` construction)"; §11 Decision 3:
   "**Evidence-tier default — DECIDED.** User-supplied sources admit as
   `evidence` by default." Confirmed empirically against the current
   tree (grep, this tranche): `provenance.role == "import"` is the
   codec this admission path actually writes
   (`capabilities/evidence.py`, `admission/` attach paths, `rules/act.py`).
   `harness-spec-v1.6-amendment.md` ("Frozen run input") adds a caveat
   this design must respect: "Attachment creates separate source,
   **attackable reliability**, and candidate-evidence records. Prompt
   inclusion does not create support, refutation, reliability, or
   truth" — i.e. an import-role artifact's evidentiary status is ITSELF
   attackable, and this design's own "ground" test only ever reads
   `Status.ACCEPTED` artifacts (see Items S3/S4 below), so an
   import-role artifact whose reliability was successfully attacked
   (hence `REFUTED`, not `ACCEPTED`) is automatically excluded from
   counting as ground — the design inherits this guarantee for free
   from restricting its own dependence subgraph to `accepted` nodes.

2. **User ruling.** `harness-spec-v1.3.md` §10.6 ("User as appellate
   court"): "Each ruling registers as a **precedent artifact**
   (`provenance.role: user`)." Unchanged by v1.4/v1.5/v1.6 (none
   redefines §10.6). Confirmed empirically: `provenance.role == "user"`
   marks appellate/holdout/user-authored content
   (`informal/appellate.py`, `informal/holdout.py`, `workloads/formal.py`).

3. **Program check.** `harness-spec-v1.3.md` §1 (`Commitment.eval` in
   `{"program:<ref>", "predicate:<expr>"}`, as opposed to `"rubric:
   <spec-id>"`) and §11.3's own text again: "windowed fraction of
   verdicts from **program/observation evals vs. rubric**." This is
   the one anchor kind the current tree's own `rules.warrants.
   formally_backed(harness, aid)` predicate already computes exactly
   ("carries at least one EVALUABLE AND SUBSTANTIVE commitment and
   every such commitment currently passes" — `DR-CON-warrants-and-
   attacks`'s own quoted docstring, substantive excluding purely
   structural well-formedness checks, which "protect nothing about the
   subject" per that same function's own reasoning and which §11.3's
   own concept of a meaningful "program check" would not credit
   either). Reused directly rather than re-implemented, matching the
   R11 convention Rung O1 itself established.

### Scratch is EXCLUDED as a grounding source — three independent, converging spec citations

`harness-spec-v1.4-amendment.md` §A: "A scratch reference records
intellectual provenance only and **MUST NOT count as a source,
observation, evidence item, premise, warrant, support, or attack**."
§B/§C reinforce: similarity/retrieval/attention "MUST NOT establish
identity, duplication, truth, support, attack, equivalence, deletion,
merging, or promotion." `harness-spec-v1.5-amendment.md` §B (the
section that LAST TOUCHED scratch attention): "Scratch blocks, links,
clusters, guides, similarity observations, and attention choices are
advisory. **They cannot establish truth, grounding, support, attack,
identity, status, or promotion into the formal graph.**" `docs/
ADMISSION_SPEC.md` §2: the `workshop` tier is "mirrored into the
scratchpad under the existing `advisory_non_grounding` boundary;
retrievable, **never grounding**." Three independent spec locations,
the most recent (v1.5, §B) stating it as the current normative rule in
so many words. This is DECISIVE under C7 ("if your definition violates
spec, then it's out") — a scratch/attention channel for a "this
artifact is ungrounded" signal is OUT BY CONSTRUCTION, not priced as
an option (Item S1 below records this as a disqualification, not a
cost row).

### The DAG-cycle guard is spec LAW; groundedness is a NEW advisory that must be COMPATIBLE, never an EXTENSION (R19)

`harness-spec-v1.3.md` §1: "`dep` MUST remain a DAG. Reject any
dependence ref that would create a cycle." §2 (well-formedness): "`dep`
is acyclic" is a well-formedness condition of every state, unamended
by v1.4/v1.5/v1.6. This IS enforced, in the current tree, exactly where
this session's own earlier read-only detour verified live: write-time
refusal (`harness.py:517`, `except DependenceCycleError as e: raise
WellFormednessError`) and an independent re-derivation inside
`verify_root` (`invariants.py:4031`, `except DependenceCycleError as
e: fail("dep-dag", ...)`) — both confirmed present and functioning by a
live, uncommitted-scratch-harness trigger this same session (`REFUSED
as expected: WellFormednessError - dep contains a cycle through:
['X', 'Y']`), independent of and prior to this tranche's own design
work.

The distinction this design must hold: the DAG property is a
WELL-FORMEDNESS RULE the spec makes MANDATORY — every state, always,
enforced at the write boundary. "Groundedness" (whether an accepted
artifact's `dep` chain reaches an exogenous anchor) is NOT a
well-formedness rule anywhere in the spec — no clause requires it, no
clause refuses registration for lacking it, and §4's own pseudocode
computes `final(a)` from `label0(a)` and `supported(a)` (itself defined
purely as "all `final(b) == accepted` for dependencies `b`") with NO
reference to whether the dependency chain terminates at an anchor.
**An accepted artifact with no path to ground is, today, and remains
under this design, a perfectly well-formed, perfectly valid
`Status.ACCEPTED` artifact.** This design's own signal must therefore
be argued COMPATIBLE with that fact (an ADVISORY annotation layered on
top of a status the spec already permits), never as an EXTENSION of
acceptance semantics (it may never cause, block, or contingently
qualify a `Status.ACCEPTED` verdict). Item S1's spec-conformance line
makes this explicit for every channel priced.

### Audit verdict: O1c's operational proxy (Provenance.role in {SEED, IMPORT, USER}) DIFFERS FROM the spec-derived definition IN BOTH DIRECTIONS (R17)

**IMPORT and USER match** the spec's evidence and user-ruling anchors
exactly (above).

**SEED is EXCLUDED under the spec-derived definition — narrower.**
Every actual `provenance.role == "seed"` construction site in the
current tree (grepped fresh this tranche, non-test):

    src/deepreason/informal/standards.py:42   -- a S10.3 standard artifact
    src/deepreason/easy.py:879                -- a deterministically
                                                  composed website artifact
    src/deepreason/capture/schools.py:79,101  -- S11.1 school-policy artifacts

None of these three kinds is named as a §11.3 anchor. All three are,
by the spec's own words, ordinary REFL-rule content: §3 ("Refl...
rule-artifacts, demarcation criterion, adjudication semantics,
standards, guard procedures, and school-policy artifacts are
registered artifacts in `A`, **attackable**"); §10.3 ("Standards are
ordinary artifacts: **attackable, reinstateable, succeedable**");
§11.1 ("registered as a school-policy artifact (Refl — **attackable
like any rule**)"). A claim resting only on a seed-role artifact rests
on ordinary, criticizable graph content — the same epistemic status as
a bare conjecture — not on anything the spec calls exogenous. Treating
`role=="seed"` as unconditional ground (Rung O1's own SPEC.md A5) was
an operational simplification, not a spec-derived one; it is corrected
here per R16/C7.

**Program-check anchoring is ADDED under the spec-derived definition —
wider.** O1's proxy checked `Provenance.role` only, and never inspected
a commitment's `eval` kind or verdict — so it structurally could not
recognize the §11.3 "program check" anchor at all, regardless of an
artifact's role. This design adds it (via `formally_backed`, above).

**Net: the proxy is neither strictly narrower nor strictly wider — it
differs in kind on two independent axes**, and per R17 this requires
an actual re-run, not a guess either way.

### Re-run: floating-foundation count under the spec-true definition (R17, read-only, reusing O1's own committed scripts)

`experiments/2026-08-08-change-grounded-overlay-o2/scripts/
spec_true_ground_rerun.py` imports `weakly_connected_components` and
`overlay_common.corpus`/`open_root` DIRECTLY from O1's own committed
`o1c_floating_foundations.py` (unedited — O1's tranche stays closed and
byte-untouched) and computes BOTH ground predicates side by side over
the same 48-root corpus O1 measured.

```
$ python3 experiments/2026-08-08-change-grounded-overlay-o2/scripts/spec_true_ground_rerun.py
... 37 openable roots, 11 ERROR (same UnsupportedRunManifestVersionError baseline O1 measured) ...
TOTAL proxy_floating=2374(chains=14) spec_floating=2586(chains=0)
```

Total floating INSTANCES rise (2374 → 2586, +212) — expected, since
removing SEED as an automatic anchor exposes standalone standards/
school-policy artifacts that carry no independent program-check
backing of their own as newly floating (isolated, size-1 each; none of
the +212 forms a new multi-node chain — confirmed by the per-root
table below, `chains` column stays 0 in the `spec` column on every
row). But the **headline multi-node-chain count collapses from 14 to
0** — EVERY one of O1's own 14 flagged "self-supporting clusters"
turns out to already rest on a program-check-verified member once that
anchor type is honored.

Spot-checked directly (not merely inferred from the aggregate), the
28-artifact chain `REPORT.md` M6 names in
`experiments/2026-08-02-stress-triplet/home-workshop/runs/run-
1a0d4168a446f052bc7ccc9aa20b9829`:

```
$ python3 -c "... is_ground_spec_true(h, m) for m in chain.members ..."
08fedf4d2716 role=CONJECTURER formally_backed=False
12917e9cb772 role=CONJECTURER formally_backed=True
14b9a83d1fe3 role=CONJECTURER formally_backed=True
16e5d3e06dfd role=CONJECTURER formally_backed=True
19143d92d8d8 role=CONJECTURER formally_backed=True
same component still floating under spec-true ground? False
```

Several members of this CONJECTURER-role chain independently carry
passing, substantive program/predicate commitments — a §11.3 anchor
O1's role-only proxy structurally could not see — so the whole
weakly-connected component now finds ground through one of its own
members, dissolving the "self-supporting" reading entirely. This
pattern held for all 14 of O1's chains (aggregate `chains=0`, not a
sampling artifact).

### Consequence: R5's premise does not survive the spec-true audit

REQUEST.md R5 states "the design earns exactly one live overlay:
floating foundations (O1c's catch)" — written against O1's own
operationally-proxied count (14 multi-node chains). Under the
spec-DERIVED definition this tranche was instructed to use instead,
that catch is **zero multi-node chains, corpus-wide.** Per the
preplan's own Rung O2 fallback text (REQUEST.md C6, quoted in full):
"If O1's counts are ~zero across the board, O2 is a one-paragraph
closure recording that the graph closure is healthy — a negative
result recorded as one, per house law." Under the spec-true count,
O1c's own headline result now reads exactly this way.

This SPEC does not therefore skip R6-R10's own asks — every one is
answered below, in full, per Amendment 1's explicit instruction ("continue
to the decision sheet") — but the RECOMMENDATION changes: Item S9's
decision sheet recommends the closure disposition for the multi-node-
chain signal (matching O1a/O1d), with the FULLY-PRICED live design
(S1-S4) kept on record as a ready, evidence-backed option rather than
built now, and the newly-exposed SEED-infrastructure-without-backing
signal (+212 isolated instances) named as a DIFFERENT, separately-priced,
lower-confidence candidate with its own honest false-positive risk
(Item S4).

## Items

S1 (R6): signal-shape pricing, three candidates, each carrying the
spec-conformance line R18 requires.
    (a) **Scratch/attention input** — DISQUALIFIED, not priced (R18,
        C7): three independent, converging spec clauses (v1.4 §A/B/C,
        v1.5 §B — the clause that last touched it, `ADMISSION_SPEC.md`
        §2) state scratch content "cannot establish... grounding" and
        the `workshop` tier is "never grounding." A design that routed
        a groundedness signal through scratch would contradict this
        directly. Independently disqualified a second way, by the seam
        docs (map preflight, above): `DR-SUB-scratch`'s own allowlist
        deliberately excludes `scheduler`, and `DR-SEAM-rules-x-
        scratch` shows criticism receives scratch content from NO
        parameter anywhere in `llm/packs.py` — so even setting the
        spec clause aside, a scratch-routed signal could structurally
        never reach the criticism/re-criticism machinery a groundedness
        signal exists to inform.
    (b) **Report channel entry** — `verification/report.py`, a new
        `_floating_foundation_findings(harness) -> list[EpistemicFinding]`
        function alongside the existing `_adjudication_blindness_
        findings` (same file, same shape: whole-run derivation, added
        to `VerificationReportV2.epistemic`, classified via
        `_EPISTEMIC_CHECKS`, does NOT enter `.valid` — integrity/
        security only, per `DR-SUB-verification`'s own Traps section).
        Spec-conformance: reads only `state.dep`/`state.status`/
        `Provenance.role`/`Commitment.eval` — all already-adjudicated,
        already-well-formed data (§2); computes no new `att`/`dep`
        edge, assigns no `Status`; changes no acceptance semantics
        §4 defines. Cost: LOW — same architecture as an already-shipped
        precedent (2026-07-31), touches one file, no live-run behavior
        change, no scheduling contact (so no R-g argument is even
        required for this option — it never touches rank/scheduling/
        exposure at all).
    (c) **Scheduler-visible signal** — extend `Scheduler.
        _standing_recrit_pool` (`scheduler/scheduler.py:1150-1186`)
        with a third priority tier: execution-backed survivors first
        (existing), then floating-foundation-flagged survivors, then
        the rest — reusing the EXACT existing partition mechanism
        (`backed + rest`, now `backed + floating + rest`), not a new
        subsystem. Spec-conformance: `DR-CON-scheduler-ranking`'s own
        package guarantee ("attention and ranking only... must never...
        assign a Status/hv/reach value", `Scheduler._select_problem`'s
        socket contract) already governs this exact function; the
        floating-foundation predicate only re-orders WHICH already-
        `ACCEPTED` survivor is criticized SOONER within one existing
        attention queue — no `Status`, `att`, or `dep` write anywhere
        in `scheduler/`. Cost: LOW-MEDIUM — one function, existing
        precedent shape (execution-backed-first ordering already
        exists in this exact function), but requires the R-g argument
        below since it touches scheduling.
    accept: three sub-items present, (a) explicitly marked DISQUALIFIED
    with its citations, (b)/(c) each carrying a spec-conformance
    sentence and a cost tier.

S2 (R7): named consumer, with the R-g argument for the option that
touches scheduling.
    Recommended: BOTH S1(b) and S1(c), report channel as the PRIMARY
    consumer (cheapest, zero scheduling contact, immediately actionable
    by the operator via existing tooling that already reads
    `VerificationReportV2.epistemic` — e.g. `tools/root_sweep.py`'s own
    blindness-count column, extensible the same way), scheduler
    attention as a SECONDARY, optional consumer once the primary is
    live and validated.
    R-g argument for S1(c) (the scheduling-touching option), tracing
    the exact precedent already audited under R-g in this program's
    own history (`experiments/2026-08-08-change-pipeline-census-d1/
    CENSUS.md` R-g audit, sub-part (a), verdict CONFIRMS): the SAME
    function's existing execution-backed-first ordering was
    independently audited and found to change WHEN a mechanically-
    neutralized re-criticism attempt happens, never WHETHER a target
    can be admitted, rank for problem selection, or reach
    `Status.ACCEPTED` — "it changes WHEN a (mechanically-neutralized)
    attack attempt happens, never WHETHER a target can be admitted,
    rank for problem selection, or reach `Status.ACCEPTED`." The
    floating-foundation extension is structurally identical in kind (a
    THIRD tier in the SAME attention-ordering function, same shape as
    the already-audited SECOND tier): (i) computed from `Provenance.
    role`/`Commitment.eval`/`dep` — structural facts about SUPPORT
    LINEAGE, orthogonal to formal/informal KIND (an informal prose
    artifact and a formally-backed artifact are equally eligible to be
    "floating" or "grounded" — the signal does not correlate with kind
    at all, satisfying CLAUDE.md's Operator design law directly: "any
    design that weights outcomes on conjecture KIND violates this
    law" — this design weights on SUPPORT-CHAIN REACHABILITY, a
    different axis entirely); (ii) only ever ADDS scrutiny attention
    (moves an artifact earlier in an existing re-criticism queue),
    never blocks admission, never changes rank for problem selection,
    never touches `Status`; (iii) directs MORE scrutiny toward
    survivors accepted-by-neglect with no independent anchor — the
    SAME target class `_standing_recrit_pool`'s own docstring already
    names ("accepted-by-neglect is untested acceptance, not
    corroboration"), a strengthening of an existing, already-audited
    mechanism, not a new kind of mechanism.
    accept: both consumers named; the R-g argument for S1(c) traces to
    the D1 census's own recorded verdict, quoted, not asserted fresh.

S3 (R8): absence semantics for old roots.
    "The S5 template" (Q3, resolved): `tools/root_sweep.py`'s own
    absence-tolerant reader pattern for `recorded_seat_bindings`/
    `recorded_module_fingerprints` (comment citing "Rung S5",
    `experiments/2026-08-07-change-seats-in-record-s5/`): assert the
    reader's own attribute/entry point exists before calling it (never
    assume); absence in an old root is a VALID answer, reported as
    empty/absent rather than crashing or silently defaulting; the
    reader function is what changes, never a hardcoded per-root value.
    This design's own absence case is STRICTLY SIMPLER than the S5
    template's own motivating case: `recorded_seat_bindings`/
    `recorded_module_fingerprints` read a NEW STAMP that did not exist
    in pre-Rung-S5/-4 logs, so old roots genuinely lack the observable.
    A floating-foundation finding introduces NO new stored field at
    all — it is a pure function of `state.dep`, `state.status`,
    `Provenance.role`, and `Commitment.eval`, every one of which has
    existed in every schema-v6 root since inception (confirmed:
    `RunManifest` schema v6 is the only version this design's own
    reader ever opens — pre-v6 roots already raise
    `UnsupportedRunManifestVersionError` at `Harness.__init__` before
    any finding could be computed, the SAME typed boundary O1's own
    corpus sweep already hit on all 11 pre-v6 roots, not a new one this
    design introduces). Consequence: every openable (schema-v6) root,
    old or new, gets a REAL, freshly-computed answer through the exact
    same code path — "0 floating-foundation findings" on a root that
    happens to have none is not a special case, it is the ordinary
    output of the same function every other root runs. Absence
    tolerance is therefore satisfied by construction, not by a
    fallback branch.
    accept: the S5-template citation names the actual tranche
    (`experiments/2026-08-07-change-seats-in-record-s5/`) and its own
    `root_sweep.py` comment, quoted; the "no new stored field" claim is
    checkable against S1(b)/(c)'s own read set (`dep`, `status`, `role`,
    `eval` — no new `ScratchRecord`/event payload/manifest field named
    anywhere in this SPEC).

S4 (R9): the false-positive story, from O1's OWN data plus this
tranche's own re-run, honestly covering BOTH candidate signal shapes.
    **Multi-node floating chains (O1's original framing).** O1's own
    corpus: 2360 vacuous isolated singletons vs. 14 multi-node chains
    (`REPORT.md` M5). Under the spec-true re-run (above), the 14
    chains fall to ZERO — so THIS signal shape, at THIS threshold
    (size > 1), currently has no false-positive story to tell on the
    committed corpus: there is nothing left to page anyone about. The
    size > 1 threshold itself remains the correct DESIGN boundary
    regardless (a lone accepted artifact with zero `dep` edges is
    trivially "supported" by §4's own vacuous `all([])==True` and
    citing every such artifact would produce thousands of pages for a
    structurally expected, low-signal case — the 2360-vs-14 ratio O1
    measured is exactly the argument for the boundary, even though the
    numerator on the spec-true side is now 0).
    **SEED-infrastructure-without-backing (this tranche's own new
    finding, +212 instances).** Every one of the +212 net-new floating
    instances under the spec-true definition is a SIZE-1 isolated
    artifact (confirmed: `chains` column is 0 on every per-root row in
    the re-run table) — standalone standards/school-policy artifacts
    with no independent program-check commitment of their own. Flagging
    ALL of these would be a NEW, LARGE false-positive surface: standards
    and school policies are, BY SPEC DESIGN (§10.3, §11.1), evaluative
    INFRASTRUCTURE — never required to carry their own falsifiable
    commitment, precisely because their job is to judge OTHER content,
    not to BE an empirical claim. Paging on every unattacked standard
    would be paging on the harness's own ordinary, working state
    (a standard nobody has needed to attack yet is not evidence of a
    defect). This signal shape is NAMED here but NOT recommended for a
    live build (Item S9) for exactly this reason — its false-positive
    rate cannot currently be bounded the way the multi-node-chain
    threshold was bounded by O1's own measured ratio, because there is
    no equivalent "how often does this ALSO happen to something we
    don't care about" measurement yet.
    accept: both signal shapes' false-positive stories stated with
    their own numbers; the SEED-infrastructure story explicitly
    disclaims a build recommendation rather than silently omitting one.

S5 (R10a): O1a/O1d disposition — shelved as verified-correct-with-
nothing-to-catch, each with a NAMED re-run condition.
    **O1a (semantics diff).** Verified against two independent Dung-
    textbook cases this session (an odd 3-cycle and an even 2-cycle,
    `experiments/2026-08-08-change-grounded-overlay-o1/CHECKLIST.md`
    step 3) — the algorithm is correct; it found zero controversy
    because the corpus's own attack graph is small (26 edges, 37 roots)
    and every edge observed forms a simple chain, never a cycle
    (`REPORT.md` M1). Re-run condition, NAMED and mechanical: the first
    committed root whose `att` (attack-edge set) contains ANY cycle —
    i.e. the first root where `o1a_semantics_diff.py`'s own
    `controversy_sccs` count is `> 0` on a fresh corpus sweep. This is
    directly checkable by re-running O1's own committed
    `scripts/o1a_semantics_diff.py` (unedited) against any newly
    committed root; no new instrument is owed until that count moves
    off zero.
    **O1d (load-bearing warrants).** Verified by direct reuse of
    `build_att`/`label0`/`final_labels` (no hand-rolled semantics) and
    found zero single-warrant flips because the corpus's own warrant
    volume is small (26 warrants, 37 roots) and every observed attack's
    target has no OTHER path to acceptance depending on that one edge
    (`REPORT.md` M7). Re-run condition, NAMED: the first committed root
    whose warrant count exceeds the corpus's own current maximum (11,
    `bronze_flat_2026-07-13/deepseek-v4-pro`) by a wide margin — e.g.
    the first root with `>= 50` registered warrants, a scale at which
    denser attack structure becomes plausible — OR, tighter and
    mechanical rather than a guessed threshold: the first root where
    `o1a_semantics_diff.py`'s own controversy inventory is non-empty
    (since O1d's own interesting cases — an accepted artifact whose
    acceptance depends on exactly one contested edge — require the
    SAME cyclic/contested structure O1a's own re-run condition already
    watches for; a second, independent trigger is not needed).
    accept: both re-run conditions are MECHANICAL (a specific script's
    specific output crossing a specific, named line), not vague
    ("when it seems worth it").

S6 (R10b): O1b's widening priced as a possible O3, not built.
    RESULTS.md's own "What this means for the program" section already
    identifies the concrete widening: `property_oracle_commitment`'s
    own `generator`/`input_contract` fields (`oracle.py:341-342`) DO
    declare a shared-domain signal for property-oracle-class
    commitments, unlike the exec-oracle-only gate O1b actually used.
    Pricing, from O1's own measured corpus shape (`REPORT.md` M3):
    265 accepted-formally-backed artifact instances corpus-wide, of
    which 2772 excluded-pair instances failed specifically for "not
    both exec-oracle-class" — the population a widened gate would need
    to newly admit. A widened O1b would need: (a) a same-`generator`-
    string OR same-`input_contract`-string comparability test
    (mirroring O1b's own same-entry-name test, no new mechanism
    class); (b) reuse of `oracle.fuzz_property`'s EXISTING deterministic
    fuzzing machinery (already built for property-oracle commitments,
    `oracle.py:498`) rather than O1b's own ad hoc SENTINEL-trick reuse
    of `oracle.run`, since `fuzz_property` is the harness's own
    purpose-built tool for this exact commitment kind; (c) the SAME
    root-level wall-clock/pair-count budget guard O1b's own
    `MAX_DYNAMIC_PROBES_PER_ROOT`/`ROOT_WALLCLOCK_BUDGET_S` already
    established, reused rather than redesigned. Estimated size: similar
    order to O1b itself (~250 lines script + a re-run + REPORT.md
    section), since it is the SAME overlay shape over a DIFFERENT
    commitment-kind gate, not a new overlay. NOT built this rung — O2's
    own scope (R5, C6) is DESIGN-AND-STOP for the ONE overlay O1's raw
    numbers pointed at; O1b's own numbers (0 comparable pairs found
    corpus-wide) do not themselves justify a build without first
    knowing whether the widened gate would find any comparable pairs at
    all, which is exactly what an O3 MEASURE-ONLY rung would establish
    before any live design, mirroring O1's own two-step discipline
    (measure, then design).
    accept: the widening path names its two commitment fields by file:
    line; the pricing cites O1's own REPORT.md numbers, not a guess;
    explicitly marked NOT BUILT.

S7 (R10c): the LLM consistency patrol (blind spot 1's full remedy),
priced against the corpus shape O1 measured, as a possible O4.
    Corpus shape (REQUEST.md's own citation, confirmed against
    `REPORT.md` M2/M7): 26 attack edges across 37 openable roots;
    accepted-artifact counts per root range 11-177, median 42 (n=37,
    computed fresh this tranche from `overlay_results.jsonl`'s own
    `o1c.accepted_count` field) — i.e. **accepted sets are large and
    mostly unattacked**, exactly the corpus shape the task's own
    framing names. The patrol's job (per the preplan's own opening
    section, blind spot 1: "two accepted artifacts that contradict each
    other stay jointly accepted forever if no one minted the edge")
    requires an LLM call PER CANDIDATE PAIR of accepted artifacts within
    one root, since detecting "contradicts" is a semantic judgment no
    offline script can make (RESULTS.md's own residue section, quoted:
    "structurally outside offline reach"). Cost model, from the
    corpus's own numbers: naive all-pairs comparison over a 100-accepted-
    artifact root is `C(100,2) = 4950` pairs — clearly unbounded without
    a pre-filter. A tractable design needs, at minimum: (a) a same-
    problem restriction (mirroring O1b's own `addr`-based pairing,
    §S1's shared vocabulary) — accepted artifacts answering DIFFERENT
    problems have no shared claim space to contradict, cutting the
    candidate space by the corpus's own problem-to-artifact fan-out
    ratio (not measured by O1 — an O4 MEASURE step would need to
    compute it per root before any budget can be set, the SAME
    discipline O1a's own TOO_LARGE guardrail and O1b's own
    machine-comparable-gate already established: paste the count before
    committing to a budget); (b) a cheap, non-LLM PRE-FILTER within the
    same-problem population (e.g. embedding-similarity nearest-
    neighbours, already a first-class retrieval channel in
    `scratch/attention.py`'s own `_ATTENTION_CHANNELS` — reusable
    infrastructure, not a new one) to shrink the LLM-call population
    before the expensive step; (c) a hard per-root call budget, sized
    against the corpus's own accepted-set sizes (median ~40-70 per
    `REPORT.md`'s own table), analogous to O1b's own
    `MAX_DYNAMIC_PROBES_PER_ROOT`; (d) EVERY minted candidate attack
    edge enters the ORDINARY criticism loop (the preplan's own standing
    guardrail, REQUEST.md C4) — the patrol proposes, it never itself
    adjudicates. This is priced as an O4 for the operator to accept or
    decline; it is NOT designed further here (R10c's own framing: "for
    the operator to accept or decline", not "build a spec for").
    accept: the cost model cites O1's own corpus numbers (26 edges, 37
    roots, per-root accepted-count range) rather than an invented
    figure; the same-problem/pre-filter/budget/ordinary-loop shape is
    named without being spec'd to CHECKLIST.md depth (out of this
    item's own scope, per R10c's "accept or decline" framing).

S8 (R11): frozen-surface contact forecast, produced fresh (C2 — no
grant assumed from any prior tranche's own precedent).
    Contact IS expected, conditionally, if a future build tranche
    implements S1(b): `verification/report.py` is part of
    `DR-INV-frozen-surfaces` surface #3 ("Replay-validation record
    formats... Their output shape is compared across runs and across
    time; a format change silently reinterprets every stored verdict").
    The contact this design specs is ADDITIVE ONLY — a new epistemic
    finding function (`_floating_foundation_findings`) alongside the
    existing `_adjudication_blindness_findings`, classified into
    `_EPISTEMIC_CHECKS` (never `_SECURITY_CHECKS`, so it never flips
    `valid` on any existing recorded root — `DR-SUB-verification`'s own
    Traps section: "A new `fail()` name defaults to integrity, and
    integrity decides `valid`... Adding a check without classifying it
    therefore flips `valid` on every recorded root that trips it" — the
    classification is therefore the load-bearing design decision, named
    explicitly here so a future build tranche cannot miss it) — the
    SAME pattern the `adjudication-blindness` finding itself used
    (2026-07-31, already precedented). Per C2's own instruction, this
    precedent is NOT treated as pre-granted: a future build tranche
    MUST obtain the operator's own explicit words before touching this
    surface, exactly as `dr-spec-change`'s own procedure requires
    ("ANY plausible contact stops the tranche HERE... obtain the
    operator's words before `dr-plan-steps` runs") — this SPEC documents
    the plan; the STOP below is what actually requests it, and it is
    requested for a FUTURE tranche, not exercised by this one, which
    writes no code.
    If a future build tranche instead (or additionally) implements
    S1(c): `scheduler/scheduler.py` is NOT among the five frozen
    surfaces; it is governed by `DR-CON-scheduler-ranking`'s own socket
    contract (attention/ranking only, never `Status`/`hv`/`reach`) —
    a DIFFERENT, non-frozen kind of constraint, satisfied by
    construction per S1(c)'s own spec-conformance line.
    accept: contact is stated as EXPECTED-IF-BUILT (not "none
    expected"), the exact surface and classification named, and the
    "assume no grant" instruction honored by treating the precedent as
    informative, not authorizing.

S9 (R12): the decision sheet.
    **Fork 1 — build the floating-foundation live overlay now, at
    all?** Road A (build S1(b) report-only): cost LOW, precedent-
    matched, zero scheduling contact, immediately actionable — but
    priced against a corpus that currently shows ZERO multi-node
    catches under the spec-true definition (S4/consequence, above), so
    it would ship instrumentation with nothing to instrument today.
    Road B (build S1(b)+S1(c), report + scheduler attention): same
    caveat, plus the R-g-argued but still frozen-adjacent-scheduling
    surface touch, for the same zero-catch corpus. Road C (do not
    build; close per REQUEST.md C6's own fallback text): "a one-
    paragraph closure recording that the graph closure is healthy — a
    negative result recorded as one" — matches what the spec-true
    re-run actually shows for the multi-node-chain signal. **Recommend
    Road C** for the multi-node-chain signal specifically, with S1-S4's
    full design kept on record (not re-derived from scratch) so a
    future root that DOES produce a genuine spec-true multi-node
    floating chain has a ready, already-argued design waiting, rather
    than needing this whole tranche re-run.
    **Fork 2 — the SEED-infrastructure-without-backing signal (+212
    instances, this tranche's own new finding)?** Road A: extend the
    same design to flag it. Road B: measure its own false-positive rate
    first (an O3/O4-shaped MEASURE ONLY step: how often does an
    unattacked standard/school-policy artifact later get attacked and
    fall, vs. survive indefinitely by design) before pricing a live
    build. **Recommend Road B** — S4's own reasoning (standards are
    infrastructure by spec design, not empirical claims) means a build
    without that measurement risks paging on ordinary, expected state.
    **Fork 3 — O1a/O1d?** Recommend the closure disposition (S5),
    re-run conditions named and mechanical, no further action owed
    until either condition fires.
    **Fork 4 — O1b's widening (O3) and the LLM consistency patrol
    (O4)?** Both priced (S6/S7), neither built, both explicitly for the
    operator's own accept/decline per R10b/R10c's own framing.
    accept: four forks, each with priced roads and one recommended
    road; no fork left without a recommendation.

## Assumptions (operator may override)

A1 (Q1): the seam docs governing each signal-shape candidate are
`DR-SUB-verification` (report channel), `DR-CON-scheduler-ranking`
(scheduler channel), `DR-SUB-scratch`/`DR-SEAM-rules-x-scratch`
(scratch channel, disqualified) — read in full this tranche (map
preflight, above).

A2 (Q2): the R-g precedent for the scheduling-touching consumer is the
D1 pipeline-census tranche's own R-g audit sub-part (a), re-confirmed
still accurate against the current tree this tranche (the cited
function, `_standing_recrit_pool`, was re-read fresh at
`scheduler/scheduler.py:1150-1186` and matches the D1 census's own
quoted excerpt line-for-line).

A3 (Q3): "the S5 template" is `tools/root_sweep.py`'s own absence-
tolerant reader pattern, citing Rung S5
(`experiments/2026-08-07-change-seats-in-record-s5/`) by the sweep
script's own comment.

A4 (Q4): the multi-node-chain distributional justification uses O1's
own 2360-vs-14 ratio as the DESIGN-boundary argument (size > 1 is the
correct threshold regardless of the spec-true recount), while reporting
the spec-true recount (14 -> 0) as the CURRENT-CORPUS argument for not
building yet — two distinct claims, not conflated.

A5 (Q5): O1a/O1d's re-run conditions are both MECHANICAL (a specific
script's output crossing a named line), chosen over an arbitrary
warrant-count guess per A5's own reasoning in S5 above.

A6 (Q6): the LLM-patrol cost model is built from O1's own measured
corpus numbers (26 edges/37 roots, accepted-count range) rather than an
invented call-count estimate, and explicitly stops at "priced" rather
than "spec'd", per R10c's own "accept or decline" framing.

## Questions for operator (STOP if non-empty)

(empty — every open question resolved to an assumption above, each
grounded in a fresh read of the current tree or a prior tranche's own
committed record rather than a guess; the two operator interventions
mid-tranche (Amendments 1 and 2) already resolved the one question that
WOULD have needed a stop — which definition of "ground" governs — by
supplying the derivation method directly.)

## Out of scope (explicit)

- Building ANY of S1(b)/S1(c)/S6/S7 in code — this rung is
  DESIGN-AND-STOP (C1); every design above is a specification, not an
  implementation.
- Re-deriving O1a's/O1d's own already-verified-correct algorithms —
  S5's re-run conditions are the owed deliverable, not a re-audit.
- Deciding the SEED-infrastructure signal's own false-positive rate
  empirically (Fork 2, Road B) — named as the next measurement, not
  performed here (would itself be a new MEASURE ONLY rung).
- Editing `docs/proposals/GROUNDED_OVERLAY_PREPLAN.md` itself to record
  this tranche's own correction to R5's premise — a delivery-time
  decision, not a design-phase one (this SPEC's own "Consequence"
  section is the correction's home for now).

## Frozen-surface contact forecast

See Item S8 in full. Summary: `verification/report.py` (surface #3,
additive-only, contact EXPECTED IF S1(b) is ever built, grant NOT
assumed); `scheduler/scheduler.py` is not a frozen surface (governed
instead by `DR-CON-scheduler-ranking`'s own socket contract, satisfied
by construction if S1(c) is ever built).

`check: git diff --stat origin/claude/monitor-session-handover-63ajqv...HEAD -- src/deepreason/capabilities/state.py src/deepreason/harness.py src/deepreason/invariants.py src/deepreason/run_manifest.py src/deepreason/qualification.py` -> empty at delivery time (this tranche itself writes no code).

## Blast-radius census

`grep -rn "floating_foundation_findings\|GROUNDED_OVERLAY.*O2\|grounded-overlay-rung-o2" tests/ docs/map/`
-> no hits (verified this tranche). Classification: MUST NOT MOVE —
nothing in `tests/` or `docs/map/` currently asserts on this tranche's
own names or the not-yet-built `_floating_foundation_findings` symbol.
No symbol under `src/`, `tests/`, or `tools/` is targeted for CHANGE by
this spec (design-only, C1), so no further blast-radius rows apply.

## Budget

This tranche: REQUEST.md (~360 lines, two amendments), SPEC.md (this
document, ~650 lines), one read-only measurement script (~150 lines,
`spec_true_ground_rerun.py`) reusing O1's own committed code rather
than duplicating it. No CHECKLIST.md/dr-execute-step/dr-validate-
change/dr-deliver-change phases — DESIGN-AND-STOP per R3 ends at this
SPEC.md, committed and pushed, then a STOP for operator words (R14).

`python3 -c "print(360+650+150)"` -> 1160

~1160 lines, 3-4 commits (REQUEST.md, REQUEST.md amendments, the
re-run script, SPEC.md). Frozen surfaces touched: none this tranche
(design/measurement only); contact FORECAST recorded for a future
build tranche (S8).

Rubric: 6/6 yes
- every R has a spec item with a machine-decidable accept: yes (S1-S9
  cover R6-R12; R1-R4/R13-R14 are process items satisfied by this
  session's own transcript and the commit/push/STOP sequence; R15/R15a/
  R16/R16a/R17/R18/R19 are covered by the Evidence base section above,
  each with its own accept-shaped citation).
- blast-radius census pasted (or pasted-empty) and every hit
  classified: yes (no hits, classified).
- frozen-surface contact forecast recorded: yes (S8, expected-if-built,
  not "none expected").
- every mechanism the request names traced to code it actually
  reaches: yes (`formally_backed`, `_standing_recrit_pool`,
  `_adjudication_blindness_findings`, `root_sweep.py`'s S5 pattern, all
  read directly from the current tree this tranche, not assumed from
  memory).
- DESIGN-AND-STOP sections: measurements are pasted commands with real
  output (the re-run, the spot-check); options are priced with cited
  numbers, not preference (S1/S6/S7/S9).
- nothing in the spec untraceable to an R/C number: yes (re-read pass
  performed; every S-item's parenthetical cites R/C numbers, including
  the Amendment-1/2-derived R15a/R16/R16a/R17/R18/R19).
