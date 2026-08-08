# Request: Rung O1 of the grounded-overlay program — offline retrodiction, MEASURE ONLY

Captured: 2026-08-08 from this session's opening task message, plus its
cited source document `docs/proposals/GROUNDED_OVERLAY_PREPLAN.md` (Rung
O1 section and the guardrails section, both verbatim as scope).

## Verbatim

This session's task message, opening instruction (full text):

> Setup FIRST, before any reading: git fetch origin
> claude/monitor-session-handover-63ajqv && git checkout -B
> claude/<your-branch-name> origin/claude/monitor-session-handover-63ajqv
> and verify the head is 2b0b108c — if it isn't, stop and say so. Then
> run the preflight (which deepreason || pip install -e .
> --break-system-packages -q). THEN read CLAUDE.md in full from this
> checkout (the Operator design laws section is binding), read
> .claude/skills/dr-explain-to-operator/SKILL.md directly with the Read
> tool and follow it for every message, and read
> .claude/skills/README.md.
> You are the executor for Rung O1 of the grounded-overlay program:
> offline retrodiction, MEASURE ONLY. Authority:
> docs/proposals/GROUNDED_OVERLAY_PREPLAN.md — Rung O1 verbatim as your
> scope, its guardrails section binding throughout. Route through
> dr-change-orchestrator starting with dr-capture-request; the D1 census
> tranche (experiments/2026-08-08-change-pipeline-census-d1/) is your
> delivery template.
> Scope, hard: src/, tests/, tools/ stay byte-untouched. Your analysis
> scripts live in the tranche directory and read committed roots only —
> no LLM calls, no provider, no new typed records, no home mutation.
> Build and run the four overlays over every committed root's final
> state: O1a grounded-vs-preferred diff plus attack-graph SCC
> controversy inventory (paste per-root node/edge counts BEFORE
> computing; a typed TOO-LARGE stop beats a hang); O1b joint-execution
> unsatisfiability probing for accepted formally-backed pairs with
> machine-comparable input gates (bounded budget, typed INCONCLUSIVE
> when it dies, excluded pairs reported not guessed); O1c
> floating-foundation clusters on the dependence graph; O1d
> load-bearing-warrant sensitivity distributions. Reuse the harness's
> own read-only readers (Harness(root, read_only=True), the
> warrant/attack-state accessors) rather than re-parsing log.jsonl by
> hand — the reader IS the contract; a hand parser is a second,
> unverified one.
> Deliverables: the scripts, a measured report with counts per root per
> overlay and the specific artifact ids (every number recomputable by
> one pasted command), and RESULTS.md honest-ledger segments including
> the residue the plan names (the LLM consistency patrol is structurally
> outside offline reach — say so, don't simulate it). Accept: zero code
> diff (paste the tripwire), full gate once at the boundary — expect the
> program's new baseline: 0 failed, NO exceptions (P1/P3 is fixed; if
> anything is red, that is a finding, stop and report), docs_verify
> green if any map document gains the concept. Anything broken you
> notice: PARKED with a ready-to-send prompt, never fixed. Commit and
> push at every phase boundary with retry. Deliver through
> dr-validate-change and dr-deliver-change, then stop.

`docs/proposals/GROUNDED_OVERLAY_PREPLAN.md` Rung O1 section, quoted
verbatim:

> ## Rung O1 — offline retrodiction  [MEASURE ONLY, no src/ change]
>
> Before building anything live: compute, over EVERY committed root's
> final state, what each overlay WOULD have caught. Read-only analysis
> scripts in the tranche directory (promotion to `tools/` only if the
> numbers earn it), no LLM calls, no provider, no new records:
>
> - **O1a — semantics diff.** Grounded vs preferred extensions; report
>   every artifact skeptically-accepted-under-preferred but blocked from
>   grounded, and every attack-graph SCC (cycle cluster) containing an
>   undecided artifact: the controversy inventory, per root.
> - **O1b — joint-execution probe.** For every PAIR of accepted
>   formally-backed artifacts within one root whose executable
>   commitments declare overlapping admissible input domains: fuzz for
>   inputs where both checkers can be satisfied; report pairs where the
>   conjunction looks unsatisfiable (bounded budget, typed
>   INCONCLUSIVE when it dies — never claim more than the probe
>   shows).
> - **O1c — floating foundations.** Dependence-graph SCCs of accepted
>   artifacts with no support path from ground (evidence/admission):
>   self-supporting clusters, per root.
> - **O1d — load-bearing warrants.** For each accepted artifact, the
>   minimum set of warrants whose invalidation flips its label
>   (single-warrant sensitivity first; report the distribution — how
>   much acceptance rests on one edge).
>
> Deliverable: analysis scripts + a measured report (counts per root
> per overlay, with the specific artifact ids so spot-checks are one
> command) + RESULTS.md honest-ledger segment including the residue —
> what offline analysis structurally cannot see (missing edges needing
> semantic judgment, i.e. the LLM consistency patrol, which is
> inherently live and deliberately NOT in this rung). Accept: every
> number recomputable from committed bytes; zero `src/`/`tests/`/
> `tools/` diff; full gate untouched (run once at the boundary to
> prove it; expect the program's new baseline: 0 failed, no
> exceptions); docs_verify green if any map doc gains the concept.

`docs/proposals/GROUNDED_OVERLAY_PREPLAN.md` "What could kill it"
section, quoted verbatim (the guardrails this task calls binding
throughout):

> ## What could kill it
>
> - **Preferred-extension computation cost** — worst case exponential;
>   the attack graphs per root are small (hundreds of artifacts), and
>   O1a must PASTE per-root node/edge counts before computing, stopping
>   with a typed TOO-LARGE rather than hanging.
> - **Joint-domain inference (O1b)** — deciding two checkers share an
>   input domain may itself need judgment; O1b restricts to pairs with
>   machine-comparable input gates and reports the excluded remainder
>   honestly rather than guessing.
> - **Overlay drift** — an advisory report nobody consumes rots; O2
>   must name the consumer (scheduler attention, criticism budget, or
>   operator report) before any live build.

Also quoted verbatim, the epistemology guardrails standing over the
whole grounded-overlay program (from the preplan's opening section, "The
baseline and its three blind spots"):

> Epistemology guardrails, standing: a second pass may MINT candidate
> attack edges (which enter the ordinary criticism loop) or emit typed
> ADVISORY reports (attention routing) — it may never relabel, never
> bypass criticism, and per R-g/operator law must be kind-blind in
> anything that touches rank or exposure.

CLAUDE.md "Operator design laws" section, quoted verbatim (cited by the
task's setup instruction as binding):

> - **Formalism is an option, never an obligation** (2026-08-08,
>   repeated by the operator "endlessly" — do not make them repeat it
>   again): nothing may force a conjecture to be formal, and nothing
>   may penalize a conjecture for being informal — not admission, not
>   rank, not criticism exposure, not acceptance. Formal backing may
>   grant protection (prose-immunity); its absence grants no
>   disadvantage. Any design that weights outcomes on conjecture KIND
>   violates this law. See DUAL_MODE_CONJECTURE_PREPLAN.md R-g for the
>   full binding form.
> - **Seats change how content is GENERATED, never what counts as
>   EVIDENCE** (the modes/packages guardrail, BEHAVIOR_MODES_PREPLAN /
>   ROLE_SEAT_SEPARATION_PLAN S7): no seat, mode, or package may let a
>   generation seat's prose skip criticism.

## Requirements

R1 (process): "Setup FIRST, before any reading: git fetch origin
claude/monitor-session-handover-63ajqv && git checkout -B
claude/<your-branch-name> origin/claude/monitor-session-handover-63ajqv
and verify the head is 2b0b108c — if it isn't, stop and say so." — done
this session: verified.

R2 (process): "Then run the preflight (which deepreason || pip install
-e . --break-system-packages -q)." — done this session.

R3 (process): "THEN read CLAUDE.md in full from this checkout (the
Operator design laws section is binding), read
.claude/skills/dr-explain-to-operator/SKILL.md directly with the Read
tool and follow it for every message, and read
.claude/skills/README.md." — done this session.

R4 (process): "Route through dr-change-orchestrator starting with
dr-capture-request; the D1 census tranche
(experiments/2026-08-08-change-pipeline-census-d1/) is your delivery
template." — in progress (this document; D1 read in full as template).

R5 (process): "Scope, hard: src/, tests/, tools/ stay byte-untouched."

R6 (process): "Your analysis scripts live in the tranche directory and
read committed roots only — no LLM calls, no provider, no new typed
records, no home mutation."

R7 (behavior): "Build and run the four overlays over every committed
root's final state: O1a grounded-vs-preferred diff plus attack-graph
SCC controversy inventory (paste per-root node/edge counts BEFORE
computing; a typed TOO-LARGE stop beats a hang)."

R8 (behavior): "O1b joint-execution unsatisfiability probing for
accepted formally-backed pairs with machine-comparable input gates
(bounded budget, typed INCONCLUSIVE when it dies, excluded pairs
reported not guessed)."

R9 (behavior): "O1c floating-foundation clusters on the dependence
graph."

R10 (behavior): "O1d load-bearing-warrant sensitivity distributions."

R11 (process): "Reuse the harness's own read-only readers (Harness(root,
read_only=True), the warrant/attack-state accessors) rather than
re-parsing log.jsonl by hand — the reader IS the contract; a hand parser
is a second, unverified one."

R12 (artifact): "Deliverables: the scripts, a measured report with
counts per root per overlay and the specific artifact ids (every number
recomputable by one pasted command), and RESULTS.md honest-ledger
segments including the residue the plan names (the LLM consistency
patrol is structurally outside offline reach — say so, don't simulate
it)."

R13 (process): "Accept: zero code diff (paste the tripwire), full gate
once at the boundary — expect the program's new baseline: 0 failed, NO
exceptions (P1/P3 is fixed; if anything is red, that is a finding, stop
and report), docs_verify green if any map document gains the concept."

R14 (process): "Anything broken you notice: PARKED with a ready-to-send
prompt, never fixed."

R15 (process): "Commit and push at every phase boundary with retry."

R16 (process): "Deliver through dr-validate-change and dr-deliver-change,
then stop."

## Standing constraints

C1: "src/, tests/, tools/ stay byte-untouched" (R5) — hard boundary; no
edit to any file under those three trees for the duration of this
tranche.

C2: "the D1 census tranche
(experiments/2026-08-08-change-pipeline-census-d1/) is your delivery
template" — M-numbered rows, pasted commands, no claim without evidence
(same shape this tranche's own template read confirmed).

C3 (the preplan's "What could kill it" section, quoted above in full) —
binding guardrails: O1a must paste per-root node/edge counts before
computing preferred extensions and stop TOO-LARGE rather than hang; O1b
restricts to machine-comparable input gates and reports the excluded
remainder honestly rather than guessing; overlay outputs are advisory
only (O2's problem, not this rung's).

C4 (the preplan's epistemology guardrails, quoted above in full) —
standing over the whole grounded-overlay program: a second pass "may
never relabel, never bypass criticism, and per R-g/operator law must be
kind-blind in anything that touches rank or exposure." Applies to this
rung as: nothing this tranche measures may become a de facto Status
change (MEASURE ONLY means the official grounded semantics is
untouched), and no overlay may be built or reported in a way that
weights a finding by a conjecture's formal/informal kind.

C5 (CLAUDE.md, standing, quoted above): the two Operator design laws —
formalism-optional/no-informal-penalty, and seats-change-generation-
never-evidence. Relevant here because O1b's "formally-backed" pairing
criterion must not be read or reported as "formal is more suspect" —
it is a scope restriction (which pairs are machine-checkable at all),
not a judgment on kind.

C6 (CLAUDE.md, standing): "The map moves in the SAME COMMIT as the
code — a separate 'update docs' commit is the commit that gets
dropped." — applies only if this tranche's report earns a new map
document (R13's own conditional: "docs_verify green if any map
document gains the concept").

## Open questions (for dr-spec-change)

Q1: "attack-graph SCC (cycle cluster) containing an undecided artifact"
(O1a) — needs a precise algorithm: compute strongly-connected components
of the directed attack graph `att`, then filter to SCCs containing at
least one artifact whose grounded label is "suspended" (undecided).
Needs fixing in dr-spec-change as the exact per-root computation.

Q2: "preferred extensions" (O1a) — the codebase implements only Dung's
GROUNDED extension (`adjudication/grounded.py`); no preferred-extension
computation exists anywhere in `src/`. This tranche must implement one
itself, offline, in the tranche directory only (not `src/`), reusing
`att`/`dep` read from `Harness(root, read_only=True)`. Needs a concrete,
bounded algorithm (worst-case exponential per the guardrail) fixed in
dr-spec-change, plus the TOO-LARGE threshold.

Q3: "formally-backed" (O1b) — `rules/warrants.py::formally_backed(harness,
target_id)` is the existing, exact predicate; needs confirming it is
directly reusable (read-only, no mutation) from an offline script.

Q4: "executable commitments declare overlapping admissible input
domains" / "machine-comparable input gates" (O1b) — no field in
`Commitment` or the ontology declares an input domain or schema
explicitly (confirmed: `Commitment` has only `id`, `eval`, `budget`,
`observation_valued`). "Machine-comparable" must be defined
operationally in dr-spec-change from what IS mechanically comparable
today — the leading candidate is exec-oracle commitments' frozen
`{entry, tests}` spec (`oracle.py::exec_oracle_commitment`,
`budget.extra["spec"]`), where two commitments' `tests` lists can share
literal `in` inputs with different `out` expectations — a PROVEN
contradiction, not a fuzzed one. Needs deciding in dr-spec-change
whether "fuzz" (the preplan's own word) requires generating NEW inputs
beyond the two test tables' own literal overlap, and if so, how,
bounded, and what counts as "the conjunction looks unsatisfiable" versus
INCONCLUSIVE.

Q5: "self-supporting clusters" / "no support path from ground
(evidence/admission)" (O1c) — needs a precise definition of "ground":
candidates are artifacts with `ProvenanceRole.SEED`, or artifacts
carrying an `EVIDENCE`-role ref target, or artifacts with no outgoing
`dep` edge at all (a leaf is trivially grounded). Needs fixing in
dr-spec-change which definition (or combination) the algorithm uses,
and the SCC computation is over `dep` (the dependence graph), separate
from O1a's SCC-on-`att`.

Q6: "the minimum set of warrants whose invalidation flips its label"
(O1d) — the preplan itself scopes this down: "single-warrant sensitivity
first; report the distribution." Needs fixing in dr-spec-change as: for
each ACCEPTED artifact, for each warrant in the root, recompute
`build_att` with that one warrant's carriage removed, recompute
`grounded_extension`/`final_labels`, and check whether the artifact's
status changes — report the count of single-warrant flips per accepted
artifact as a distribution. "Minimum set" beyond size 1 is explicitly
out of scope per the preplan's own "first" qualifier, pending Q6a.

Q6a: whether multi-warrant minimal sets (beyond single-warrant) are
in scope at all for O1a-O1d's boundary, or deferred entirely to a later
rung — the preplan's "single-warrant sensitivity first" phrasing reads
as sequencing within O1d, not as a promise this rung computes anything
beyond size 1. Needs an explicit assumption in dr-spec-change.

Q7: "P1/P3 is fixed" — needs confirming against the current tree
(`experiments/2026-08-08-fix-module-fingerprints-double-stamp/RESULTS.md`
and `experiments/2026-08-08-fix-l1-continue-resumable-crash/RESULTS.md`
both report full-gate PASS) before treating a fully-green gate as the
expected outcome rather than a surprise.

Q8: "every committed root's final state" — needs a defined corpus:
every `experiments/**/log.jsonl` root (the same corpus `root_sweep.py`
already walks, and the same corpus the D1 census used for its own
historical-evidence section) is the leading candidate; needs confirming
in dr-spec-change whether any additional roots (e.g. under `runs/`, if
any exist) belong in scope.

## Amendments

(none yet)
