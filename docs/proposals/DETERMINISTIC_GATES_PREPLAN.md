# Pre-plan: deterministic gates — mechanizing the checks the skills only say

Status: PROPOSED. When picked up, each rung routes through
`dr-change-orchestrator` as its own tranche. Written 2026-08-08 by the
monitor session on the operator's instruction, distilling the external
skills-distillation report (reviewed at commit `02c2c605`) down to
what applies to THIS repository only.

## The thesis, kept; the portfolio, discarded

The one claim from that report worth building here: **prose workflow
skills help an agent choose the right path, but only an executable
gate can prove the path is current, reachable, population-complete,
and testing the intended bytes.** DeepReason's own record confirms it
repeatedly — every rung below cites the recorded failure that a gate
would have caught mechanically and the skills only caught late, by
convention, or not at all.

Discarded deliberately: the report's new general skills, its
cross-repository amendments, and its three workflow blueprints — all
either aimed at other repositories or already encoded in the dr-*
family and CLAUDE.md. Also noted: the report is stale on the seat
program (it reviewed a head where S3 was unexecuted; S3–S5 have since
delivered), so nothing here inherits its seat-program rows.

## Shape rules (all rungs)

- Gates live in `tools/`, never `src/` — zero frozen-surface contact,
  zero harness behavior change, by construction.
- Every gate consumes explicit inputs and emits a versioned typed
  result (`*_RESULT_V1` JSON): stable exit classes distinguish
  "result emitted" / "invalid invocation" / "evidence unavailable";
  semantic verdicts live INSIDE the result, not in the exit code.
- A gate reports facts; the OWNING SKILL decides policy. Each rung
  therefore lands in two parts in one tranche: the tool, and the
  amendment to the owning skill's SKILL.md naming when the gate runs
  and what its verdicts oblige.
- Each gate ships with its own mutation proof (perturb → gate goes
  red → restore) and a `check:` line in the relevant map document, so
  docs_verify holds the gate the way it holds every other claim.
- The map moves in the same commit; full pytest gate + docs_verify at
  every tranche boundary, as always.

## The ladder (ordered by recorded-failure frequency × cheapness)

### Rung G1 — actual-diff budget gate  [EXECUTE, small]
**Recorded failure:** Rung S5 overran its ledgered budget TWICE
(REQUEST.md Amendments 2 and 3, R21/R22), each discovered by the
executor noticing, not by any instrument; the SPEC's own headline
estimate (220–300) contradicted its own itemization (~325–435) and
nothing caught the arithmetic. Precedent tranche:
`2026-08-05-change-budget-ceiling-at-commit`.
**Deliverable:** `tools/diff_budget.py <base> [--ceiling N] [--paths ...]`
→ `DIFF_BUDGET_RESULT_V1` (actual cumulative insertions by area,
ceiling, verdict WITHIN / EXCEEDED / NO_CEILING). Skill amendments:
`dr-spec-change` — the Budget section's headline MUST be the computed
sum of its own itemization (paste the gate run over the itemized
estimates); `dr-execute-step` — run the gate at every [COMMIT] step
against the ledgered ceiling; EXCEEDED is a STOP with priced options,
raised at the commit that crosses the line, never discovered at
delivery.
**Accept:** gate emits correct verdicts on a fixture repo diff;
mutation-proven; S5's own history replayed through the gate flags the
overrun at the step where it actually happened (retrodiction test).

### Rung G2 — mutation attestation  [EXECUTE, small]
**Recorded failure class:** mutants not loaded, or passing/failing for
the wrong reason: editable-install worktree shadowing, the
`docs_verify --fast` cache blindness (ERRATA, 2026-08-04 companion),
invisible indented checks (`2026-08-02-map-falsification`), loopback
`sitecustomize` import shadowing
(`2026-08-05-fix-loopback-fixture-daemon`). Our checklists demand
RED/GREEN paste but nothing proves the mutated bytes were the bytes
executed.
**Deliverable:** `tools/mutation_attest.py` — wraps a mutation proof:
records interpreter path, the mutated file's resolved import origin
(`module.__file__` as actually imported by the test process) and
sha256 before/after, the expected failure identity (test id + error
class), and whether the observed RED matches it →
`MUTATION_ATTEST_RESULT_V1` with verdict KILLED / SURVIVED /
INVALID_EVIDENCE (wrong tree, wrong mechanism, wrong-reason failure).
Skill amendments: `dr-execute-step` and `dr-reproduce` — any
mutation-proof done-criterion is satisfied only by an attested KILLED,
never by pasted output alone.
**Accept:** a deliberate wrong-tree mutation (edit a shadowed copy)
yields INVALID_EVIDENCE, not KILLED; a genuine mutation yields KILLED;
both pasted.

### Rung G3 — evidence-population manifest  [EXECUTE, small]
**Recorded failure class:** censuses that expired while the intended
property stayed true: the module-fingerprints census test (C5's trap,
SEAM-harness-x-verification), `2026-08-05-fix-expired-census-readers`,
qualification totals. The partition-not-census rule is now prose law
(S5 obeyed it); the population itself is still hand-derived each time.
**Deliverable:** `tools/census_manifest.py` — given a population rule
(e.g. "roots under experiments/ tracked by git", "tests collected
under tests/"), emits `CENSUS_MANIFEST_RESULT_V1`: sorted members,
explicit exclusions with reasons, parse/open failures (never silently
dropped), at least one positive and one negative witness, reader
identity, and a manifest hash. `tools/root_sweep.py` consumes it for
the 42-root population instead of deriving its own; new census-shaped
tests cite a manifest hash instead of a count.
**Accept:** the sweep's population comes from the manifest and is
byte-identical to its current derivation; a planted unreadable root
appears as a typed failure, not a silent drop; mutation-proven.

### Rung G4 — final-tree evidence gate  [EXECUTE, medium]
**Recorded failure class:** evidence that was true when captured and
stale at delivery: the rung-5 proof invalidated by later evidence
commits, rung-7's "delta-clean but the whole tree is red", stale
stress audits outranking raw records (`2026-08-02-stress-triplet`).
`dr-deliver-change` reconciles claims R-by-R but nothing re-verifies
that the evidence still describes the FINAL commit.
**Deliverable:** `tools/delivery_evidence.py` — consumes the tranche's
owed-instrument list (gate run, docs_verify, sweep, frozen-surface
diff, budget verdict) with the commit each was captured at → emits
`DELIVERY_EVIDENCE_RESULT_V1`: per-instrument CURRENT (captured at the
delivery head) or STALE (tree moved since), plus the delivery head's
tree hash. Skill amendment: `dr-deliver-change` — DELIVERY.md must
embed a result where every owed instrument is CURRENT; any STALE
instrument is re-run at the head first, not narrated around.
**Accept:** a fixture where evidence predates a later commit yields
STALE; re-capture flips it CURRENT; retrodiction on the rung-5
tranche's history flags the exact staleness that actually occurred.

### Rung G5 — premise-currency preflight  [EXECUTE, medium]
**Recorded failure class:** tranches begun from stale or false
premises: the critic-seat premise correction, the unreachable rung-3
fixture (ERRATA E10), the resumable-guard no-fix outcome
(`2026-08-05-fix-resumable-reason-guard-coverage`). The capture/spec
skills now demand fresh verification as prose (S5's REQUEST did it
exemplarily — at the cost of the executor re-deriving everything by
hand).
**Deliverable:** `tools/premise_currency.py` — given a premise record
(named symbols, cited failing test or run id, claimed
file:line anchors), verifies each against the current head → 
`PREMISE_CURRENCY_RESULT_V1` per premise: CURRENT / MOVED (anchor
drifted, new location reported) / REFUTED (symbol gone, failure no
longer reproduces) / UNVERIFIABLE. Skill amendments:
`dr-capture-request` and `dr-set-goal` — the map-preflight section
embeds a gate result; a REFUTED premise is a candidate terminal
outcome (premise-refuted, no change needed) to surface to the
operator, which the record shows is a real and honorable ending, not
a failure.
**Accept:** retrodiction: pointed at E10's cited fixture premise, the
gate returns REFUTED (unreachable); pointed at a live premise, CURRENT
with anchors; mutation-proven.

## Parked (priced, not scheduled)

- **Skill forward-testing** (the report's validation requirement — our
  skills are validated by grep markers, which proves presence, not
  behavior). Real gap, but the honest cost is fresh-agent evaluation
  runs per skill edit, which is an operator-attended program, not a
  tool. Park until the gate ladder above has proven its own worth;
  revisit with a scoped pilot (one negative-trigger task + one
  stale-premise task against the two orchestrator entry skills).
- **Instrument-stage runner** — the August-5 smoke cascade lesson.
  Mostly already delivered by `2026-08-05-fix-smoke-failure-reporting`
  (typed machine record + sidecar) and the smoke visibility tranche;
  the residual (run stages independently to unmask later defects) is a
  small amendment to the smoke scripts' own docs, not a new tool. Fold
  into whichever tranche next touches the smokes.
- **Check-registration audit** — `docs_verify --audit` and the
  map-falsification fixes already own this ground. No rung.

## Order and cost

G1 → G2 (each ~a day: one small tool + one skill amendment + tests +
map) → G3 (a day; touches root_sweep, so its probe discipline applies)
→ G4 → G5 (each 1–2 days; G4 changes delivery evidence obligations,
G5 changes capture obligations — both are skill-law changes the
operator should read before they bind executors). Every rung is
independently deliverable and independently reversible (delete the
tool, revert the SKILL.md paragraph); the ladder stops safely after
any rung. No rung touches `src/`, frozen surfaces, run identity, or
the record format. Natural scheduling: the queue-drain window's
companion — same "sharpen the shop" character — or interleaved one
rung at a time between research-program tranches.

## What could kill it

- **Gate sprawl** — the failure mode the report itself names: every
  incident becoming another instrument. The ledger above is closed at
  five; a sixth gate requires its own recorded-failure citation and an
  operator word, same as a frozen surface.
- **Gates rotting like the checks they replace** — hence each gate's
  own mutation proof and map `check:` line; a gate nobody can prove
  red is worse than prose.
- **Skill-text drift** — the amendments must name the gate by exact
  tool path and result type; a SKILL.md that says "run the budget
  check" without the contract re-creates the prose problem the gate
  exists to end.
