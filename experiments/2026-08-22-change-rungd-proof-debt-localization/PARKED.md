# Parked from the Rung D tranche

One entry. It is not a defect and not a wish: it is half of a rung the operator
deliberately deferred at a measured budget stop, with its design already
committed and authenticated.

---

## P1 — Duhem localization (drift row E-2), the whole of D2

**What.** Bundle-level problematicity must project to a member ONLY through a
standing localization criticism — an ordinary attackable artifact. None of it
is built: there is no `src/deepreason/localization.py`, no
`poietic.localization.v1` producer, no `implicated()` predicate, and — the part
that matters most — **no guard test against the automatic version.**

**Why it is parked.** The Rung D tranche's diff-budget ceiling (1480 insertions,
ledgered at plan time) was consumed to 1218 by D1. D2 needs ~690. The operator
ruled option B at the step-13 STOP: *"option B — deliver D1 now, park D2. The
checklist's own step-2 pre-registration ('the answer is to park, not to raise
the ceiling') stands; one tranche, one goal."* (REQUEST.md Amendment 1, R20/R21.)

**What is NOT parked, and is why the resuming window is cheap.** The design is
committed and authenticated:

- `docs/map/CON-proof-debt-and-localization.md` — the full design agreement for
  both channels, with its localization sections marked DESIGNED, PARKED. It
  carries a live check asserting `deepreason.localization` does NOT exist, so
  the document fails rather than lies if someone builds it without updating it.
- `SPEC.md` §D2 — items S12–S19 and S20's localization half, each with a
  machine-decidable acceptance command, plus §3's answer to "what is a bundle"
  and §5's answer on the readout guard.
- `poietic.localization.v1` is ALREADY in `CLAIM_SCHEMAS`. The resuming window
  supplies a producer for a declared name; it does not grow the closed set.

**The live risk while it is parked, stated plainly.** Because bundle membership
is readable off `dep`, the automatic projection — "the bundle fell, so
implicate everything under it" — is one line away, and nothing in the tree
stops it today. That is a known absence, recorded in the concept document's
Traps, not a defect in what shipped.

**Route.** `dr-change-orchestrator`, resuming at **`dr-plan-steps`** — not
`dr-capture-request` and not `dr-spec-change`. The operator's own words:
*"a future window should start at dr-plan-steps, not re-spec"* (R24).

### Ready-to-send prompt

```
Change tranche: Rung D2 of the v2 calculus program — Duhem localization
(drift row E-2). This is the PARKED half of the Rung D tranche; D1 (proof
debt, E-1) shipped 2026-08-23. Do NOT re-capture and do NOT re-spec:
route through dr-change-orchestrator and RESUME AT dr-plan-steps.

SETUP (fresh container): git fetch origin main && git checkout -B
claude/calculus-rungd2-duhem-localization origin/main. Confirm D1 is
present: python -c "from deepreason.proof_debt import receipt; print('D1
present')". pip install -e . --break-system-packages -q; pip install
pytest pytest-xdist jsonschema --break-system-packages -q. Use `python -m
pytest`, never bare pytest. Read CLAUDE.md in full; load
dr-drive-harness, dr-explain-to-operator.

AUTHORITY, in this order — all three are committed, none is to be
rewritten:
 1. experiments/2026-08-22-change-rungd-proof-debt-localization/SPEC.md,
    items S12-S19 and S20's localization half, plus §1, §3 and §5. These
    ARE your spec. Your first artifact is CHECKLIST.md, not SPEC.md.
 2. experiments/2026-08-22-change-rungd-proof-debt-localization/
    REQUEST.md — the operator's verbatim words, including Amendment 1
    which parked this work and its disposition table. R7, R8, R9, R11,
    R13 and R12's localization half are YOUR requirements now.
 3. docs/map/CON-proof-debt-and-localization.md — the design agreement,
    already authenticated. Its DESIGNED, PARKED sections become built;
    its check asserting deepreason.localization does not exist MUST be
    replaced in the same commit that creates the module.

WORK, per SPEC §D2:
 S12 LocalizationV1 in calculus/claims.py — bundle_ref, member_ref,
     derivation_manifest_ref. Extend _IMPLEMENTED to 5. CLAIM_SCHEMAS
     STAYS AT 9: the name is already declared, and a rung that grows the
     closed set while claiming to build one producer is the exact drift
     SUB-calculus.md exists to stop.
 S13 Compiler rule — MENTION on the bundle, MENTION on the member,
     DEPENDENCE on the manifest.
 S14 localization_wf, registered "structural", naming the mention law in
     its own verdict.
 S15 src/deepreason/localization.py — file_localization, bundle_members
     (the DEPENDENCE targets), standing_localizations.
 S16 implicated(harness) -> {member: grade}, derived and never stored.
 S17 the two locks. S18 a non-member is never blamed. S19 N1: defeating
     the localization un-implicates. S20 no label moves. S21 the
     mutation proof.

THREE CONSTRAINTS INHERITED VERBATIM — none is negotiable:

 (a) REUSE premises.py's SHAPE, do not re-derive it (R8). BOTH endpoints
     are MENTIONS, and each half fails differently if got wrong. Depend
     on the BUNDLE and pass two suspends the localization the moment the
     bundle becomes problematic — erasing the relation that identifies
     the blame at exactly the moment it is needed. Depend on the MEMBER
     and refuting the member suspends the localization — un-implicating
     the member at the moment the implication mattered. Mirror
     standing_attributions / premise_orphaned / open_orphans, and mirror
     premises.py's TWO LOCKS structure exactly.

 (b) BLAME ASSIGNMENT IS NEVER AUTOMATIC (R9, and the ladder's own
     warning: "both rows exist because the automatic version is the
     tempting one"). A member is implicated only when ALL THREE hold: a
     CONSULTED localization names it, its bundle is PROBLEMATIC
     (REFUTED -> BUNDLE_REFUTED, SUSPENDED_UNSUPPORTED ->
     BUNDLE_UNACCREDITED), and the member is genuinely in
     bundle_members(bundle). No measure, no default, no cascade.
     Membership is checked in the DERIVED PREDICATE, not the wf program
     — the program is handed (text, budget, artifact) and no harness
     state, so it cannot see membership. That placement is a decision;
     SPEC.md S18 records why.

 (c) MUTATION PROOF, and it is the deliverable, not a formality (R13).
     In a SCRATCH COPY of the tree — never the repo — wire implicated()
     to project automatically (every member of a problematic bundle,
     no localization consulted). Watch
     test_a_problematic_bundle_implicates_no_member_without_a_localization
     go RED. Restore. Watch it go GREEN. Paste BOTH runs into
     VALIDATION.md. This is the one guard standing between the harness
     and the automatic version, and because members are readable off
     dep, that version is one line away.

GATE PROVES: a localization is attackable and its defeat un-implicates
the member (N1/Lemma 6.1 at this layer); no label moves from a
localization alone (behavioural AND the standing.py-style structural
guard — the read path holds no call that could write, and the module
does not import adjudication); the mutation proof above. Axiom ledger:
this rung PROVES A5 at its third site (a localization mentions but does
not depend on its subject) — INV-axiom-basis.md's A5 row already names
that site as parked and must be updated when it lands.

FROZEN SURFACES: forecast none. Run tools/blast_radius.py over your
declared targets at spec-confirm time and paste its
frozen_surface_contacts verbatim; D1's run over the same package
returned CLEAR.

SIZE: ~690 insertions by D1's measurement (claim body ~45, compiler ~30,
wf ~35, localization.py ~170, exports ~10, tests ~320, map ~80). Ledger
that as your ceiling and STOP if exceeded. NOTE THE CALIBRATION D1
PAID FOR: its test file was estimated at 280 lines and written at 524.
Estimate your tests from the number of PROPERTIES to pin, not from a
line count, or you will make the same error.

MAP: docs/map/CON-proof-debt-and-localization.md is yours to complete —
unmark the DESIGNED, PARKED sections, add check: lines over the built
half, replace the find_spec-is-None check with real ones, and advance
Verified-at only if you re-ran them. INV-axiom-basis.md's A5 row.
SUB-calculus.md's _IMPLEMENTED check 4 -> 5. Map moves in the same
commits.

GATE: ring while iterating; full gate at the boundary (baseline 3875
passed, 0 failed at the D1 delivery); docs_verify full — 3 pre-existing
shallow-clone failures are expected, anything else is yours. Commit and
push every phase boundary (retry 2s/4s/8s/16s). Deliver R-by-R with
pasted PROOF, closing with one line: what it takes to blame a bundle
member.
```
