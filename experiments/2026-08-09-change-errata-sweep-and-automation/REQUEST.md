# Request: update the Errata (sweep + automation)
Captured: 2026-08-09 from the task-launch operator message (single message,
routed through the executor-session harness as "the operator's verbatim
words, the authority to ledger").

## Map preflight

Read `docs/map/INDEX.md` and `docs/map/INV-frozen-surfaces.md`. This
tranche's targets — `docs/ERRATA.md`, `.claude/skills/dr-deliver-change/
SKILL.md`, `.claude/skills/dr-verify-outcome/SKILL.md` — are not
`src/deepreason/` modules; `docs/map` states its own coverage boundary
explicitly ("`docs/map` describes `src/deepreason/`. `tests/` and
`experiments/` are navigated by convention"), and the skills directory is
outside that boundary too. No `DR-SUB-`/`DR-CON-`/`DR-SEAM-` id applies —
this is a documentation/process-ledger tranche, not a code-surface one.
Finding recorded per the preflight's own instruction ("If the map has no
id for something the work touches, that is a finding, not a blocker").
`INV-frozen-surfaces.md`'s five frozen surfaces (capability state digests,
harness event application, replay-validation formats/manifest schemas,
qualification-subject digests, the append-only record itself) are
untouched by this tranche's scope.

## Verbatim

> The second window needs to update the Errata. It hasn't been touched and
> isn't automatically updated for some reason.

> You are the executor for the ERRATA update tranche. [...] Route through
> dr-change-orchestrator. Two deliverables:

> (1) The sweep. ERRATA.md's last entry is dated 2026-08-04. Sweep every
> tranche delivered since (the seat rungs S4–S6, D1–D4, G1, L1, the O
> rungs, the omnibus, the hard-set, the investigations — their
> RESULTS/PARKED/DELIVERY files name their own corrections) for claims in
> COMMITTED documents that were later found wrong, and append properly
> dated, append-only entries per the file's own conventions. Known
> candidates to verify and write up (verify each against the record — do
> not copy my list blind): the S6 RESULTS "pre-registered stochastic miss"
> characterization corrected to structural (PARKED P1's bootstrap
> circularity); O1's "14 genuine floating chains" superseded by the
> spec-true re-run's zero (GROUNDED_OVERLAY_PREPLAN's R5 premise, corrected
> at closure); CLAUDE.md's stale spec listing (v1.5-only → v1.4/v1.5/v1.6,
> fixed 1f6c24ab) and stale turmite/jolt currentness (fixed 7e8f42402) —
> both already fixed in place but never ledgered as errata; the S5-era SPEC
> budget headline arithmetic (R21/R22 amendments); and any others your
> sweep surfaces. Every entry: what the document claimed, where, what the
> record shows, where corrected. Do NOT invent errata for in-tranche
> revision supersessions that followed the spec-revision convention
> (rev-2-supersedes-rev-1 inside one SPEC is process, not error).

> (2) The "why isn't it automatic" fix. Diagnose in one paragraph from the
> skills themselves: no delivery-phase skill mandates an errata check — the
> ledger is pure convention, so it silently starves. Then amend
> dr-deliver-change/SKILL.md and dr-verify-outcome/SKILL.md (docs-only,
> non-frozen) with a mandatory closing checkpoint: "before DELIVERY/VERIFY
> is committed: did this tranche find any committed document's claim to be
> wrong? If yes, the ERRATA.md entry lands in the same commit; if no, state
> 'errata: none' explicitly in the artifact." State-not-silence, the same
> pattern every other checkpoint in those skills uses. The operator's words
> above are the authority for this amendment; ledger them in REQUEST.md.

> Full gate at the boundary; docs_verify full (ERRATA gets check: lines
> only if its conventions already use them — follow the file, don't
> innovate its format). Deliver through validate/deliver; push each
> boundary; stop when delivered.

## Requirements

R1 (artifact): "Sweep every tranche delivered since [ERRATA.md's last
entry, dated 2026-08-04] (the seat rungs S4–S6, D1–D4, G1, L1, the O
rungs, the omnibus, the hard-set, the investigations — their
RESULTS/PARKED/DELIVERY files name their own corrections) for claims in
COMMITTED documents that were later found wrong, and append properly
dated, append-only entries per the file's own conventions."

R2 (artifact): "Every entry: what the document claimed, where, what the
record shows, where corrected."

R3 (process): "Do NOT invent errata for in-tranche revision supersessions
that followed the spec-revision convention (rev-2-supersedes-rev-1 inside
one SPEC is process, not error)."

R4 (behavior/artifact): verify each of the operator's named candidates
against the record and write up genuine ones — "verify each against the
record — do not copy my list blind": (a) the S6 RESULTS "pre-registered
stochastic miss" characterization corrected to structural (PARKED P1's
bootstrap circularity); (b) O1's "14 genuine floating chains" superseded
by the spec-true re-run's zero (GROUNDED_OVERLAY_PREPLAN's R5 premise,
corrected at closure); (c) CLAUDE.md's stale spec listing (v1.5-only →
v1.4/v1.5/v1.6, fixed 1f6c24ab) and stale turmite/jolt currentness (fixed
7e8f42402), both already fixed in place but never ledgered as errata; (d)
the S5-era SPEC budget headline arithmetic (R21/R22 amendments); (e) "any
others your sweep surfaces."

R5 (artifact): diagnose, in one paragraph, from the skills themselves, why
the errata ledger is not automatically updated — "no delivery-phase skill
mandates an errata check — the ledger is pure convention, so it silently
starves."

R6 (behavior): amend `dr-deliver-change/SKILL.md` and
`dr-verify-outcome/SKILL.md` (docs-only, non-frozen) with a mandatory
closing checkpoint: "before DELIVERY/VERIFY is committed: did this tranche
find any committed document's claim to be wrong? If yes, the ERRATA.md
entry lands in the same commit; if no, state 'errata: none' explicitly in
the artifact."

R7 (process): "State-not-silence, the same pattern every other checkpoint
in those skills uses" — the checkpoint's wording/shape should match the
existing checkpoint conventions already present in those two skill files.

R8 (process): "Full gate at the boundary; docs_verify full (ERRATA gets
check: lines only if its conventions already use them — follow the file,
don't innovate its format)."

R9 (process): "Deliver through validate/deliver; push each boundary; stop
when delivered."

R10 (process): route through `dr-change-orchestrator`; "The operator's
words above are the authority for this amendment; ledger them in
REQUEST.md" (satisfied by this document).

## Standing constraints

C1: "Route through dr-change-orchestrator." — top-level routing
instruction.

C2: "Do NOT invent errata for in-tranche revision supersessions that
followed the spec-revision convention (rev-2-supersedes-rev-1 inside one
SPEC is process, not error)." — scope limit on R1/R4.

C3: "(ERRATA gets check: lines only if its conventions already use them —
follow the file, don't innovate its format)" — constrains HOW R1/R2/R4 are
written.

C4: setup instructions (outside the operator's ERRATA-specific words, but
binding as session process): "git fetch origin main && git checkout -B
claude/<your-branch-name> origin/main, verify git merge-base
--is-ancestor b5921b3a HEAD succeeds, preflight as usual. THEN read
CLAUDE.md, .claude/skills/dr-explain-to-operator/SKILL.md (follow for
every message), and — before anything else in scope — docs/ERRATA.md and
docs/ERRATA_EXECUTOR.md in full: their conventions govern everything you
write." — satisfied at session start, before this document.

## Open questions (for dr-spec-change)

Q1: `docs/ERRATA_EXECUTOR.md` is a sibling ledger with its own scope note
("Corrections to ordinary committed documents stay in `docs/ERRATA.md`")
and its own single-writer rule (monitor-only `X<n>` sequence). Does R1's
"sweep" include ERRATA_EXECUTOR.md-scoped findings (the less-capable-
executor infrastructure), or only docs/ERRATA.md-scoped ones (ordinary
committed documents)? The verbatim request never names ERRATA_EXECUTOR.md
and enumerates ordinary-document candidates only (S-rungs, O-rungs,
CLAUDE.md, SPEC budget arithmetic) — resolve by the dominance test in
dr-ask-the-right-question before treating this as a question requiring
the operator.

Q2: R6's checkpoint text is given verbatim for both skills, but the two
skills close differently (VALIDATION.md vs VERIFY.md content, PASS/FAIL
vs pass/fail semantics) — does the checkpoint wording adapt per skill's
own vocabulary, or land byte-identical in both? Resolve via C3's principle
("follow the file, don't innovate its format") applied to each skill's
existing checkpoint phrasing.

## Amendments

(none yet)
