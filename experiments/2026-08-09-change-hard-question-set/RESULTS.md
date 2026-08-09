# Results: the two-tier hard question set (in progress)

Honest ledger, updated as each pilot leg completes (CHECKLIST.md steps
20/23 write to this file; step 25 turns it into the final narrative).
Full segment write-up follows at delivery; this section tracks the
S6-style numbered failure ledger for the pilot phase (R18, budget 6)
live, as spent, not retrospectively.

## Failure ledger (pilot phase, budget 6)

| # | Leg | What happened | Charged? |
|---|-----|----------------|----------|
| — | Tier V | `setup`/`qualify`/`reason`/both `continue` legs/all three audits all returned rc=0; one `verify_root` violation (`foreign-criticism`) appeared on the FIRST audit and had cleared by the second — not a run failure, a mid-run state that resolved, recorded honestly | **0 charged** |
| — | Tier O | Same shape: every command rc=0, same transient `foreign-criticism` finding clearing by the second audit. The JUNK-ACCEPTANCE hygiene verdict (below) is the pilot correctly MEASURING a real failure mode in the model's output — that is the metric working, not the pilot failing | **0 charged** |

Running total: **0 / 6** spent after both pilot legs.

## Tier V pilot — typed outcome (full detail: CHECKLIST.md step 19)

- Qualification: **full tier**, 300/300 cases, fresh (not cached), 124s.
- Reason + 2x continue: 14 cycles total, `state=completed`,
  `stop_reason=budget_exhausted` (the full recipe budget was actually
  used, not just offered).
- `verify_root`: clean by the final audit (`replay_valid: true`, 0
  violations); the transient `foreign-criticism` finding on the first
  audit is PARKED (step 24) as a possible structural consequence of
  sole-model operation, not fixed here.
- Tier V checker (tv-m04, known answer 16592) run against all 102
  final accepted claims: **no match** (`checker_any_pass: false`).
  Acceptable typed outcome per R16/PREREG.md — the harness format
  worked end to end; the question was hard enough that gemma4:31b did
  not solve it within budget.

## Tier O pilot — typed outcome (full detail: CHECKLIST.md step 22)

- Qualification: **full tier**, 300/300 cases, fresh, 114s (consistent
  with the Tier V leg — gemma4:31b as sole model reaches full
  qualification reliably, not just once).
- Reason + 2x continue: 14 cycles total, `state=completed`,
  `stop_reason=budget_exhausted`.
- `verify_root`: clean by the final audit (same `foreign-criticism`→
  clears-on-continue pattern as Tier V — two independent live
  observations of the same shape strengthens the "transient, not
  persistent" reading, PARKED for a future tranche to confirm properly
  rather than asserted here as proven).
- **Hygiene verdict: JUNK-ACCEPTANCE (FAIL)** per PREREG.md. The final
  record (141 accepted positions, 0 refuted, 0 suspended) contains
  multiple `role=conjecturer` artifacts that directly target the run's
  own seed question and flatly assert the Collatz conjecture IS
  resolved — "settled in the negative: it is fundamentally
  undecidable...", "settled as 'True' in a probabilistic sense...",
  "settled in the negative: it is false, and the counterexample is a
  'near-cycle'..." — unretracted in the committed record. This is
  exactly the failure mode R10 exists to catch, and the pilot caught
  it on its first live attempt.
- **The more interesting finding**: the record ALSO contains multiple
  `role=critic` artifacts correctly calling several of these claims
  "factual errors" (undecidability is itself an unproven
  meta-hypothesis, not a settlement) — but `positions.refuted` is
  empty, so these valid criticisms never flip the overclaiming
  artifacts' status. A reader who only checks `positions.accepted`
  sees the overclaim standing, unqualified. This traces directly to
  CLAUDE.md's own recorded law ("no warrant, no edge, no REFUTED"):
  prose criticism without a formally wired attack/warrant leaves the
  target's status untouched. PARKED (below) as a genuine, evidenced
  gap — not fixed in this tranche (scope-locked to `src/` untouched)
  — and it is the clearest possible confirmation of the operator's own
  original diagnosis: on the OLD, too-easy question set, criticism and
  warrants ran under-exercised because there was rarely anything worth
  contesting; on a genuinely hard/open question, the gap between
  "criticism happened" and "criticism changed the record's standing
  claims" opened up immediately.

## What the pilot answers about gemma4:31b as sole model (operator's standing question)

**Full tier, both times, from a clean/fresh qualification battery.**
This tranche is gemma4:31b's first qualification as the SOLE subject
(prior batteries only ever tested it in combination with another
model, per REQUEST.md's framing of the question). The answer is
unambiguous and reproduced twice: DeepReason is in a position to test
gemma4:31b as the sole model at FULL capability, not the reduced
`--shallow` fallback — no `--shallow` retry branch fired in either
pilot.
