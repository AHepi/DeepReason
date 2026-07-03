# DeepReason — Conjecture–Criticism Harness

A deterministic epistemology harness implementing the **creativity-calculus** build spec
(v1.3, see [`docs/harness-spec-v1.3.md`](docs/harness-spec-v1.3.md)).

## Core invariant (§0)

- The **harness is deterministic and carries all epistemology**. The LLM is a bounded
  pure function `pack -> schema-validated JSON` — the conjecture operator γ, nothing more.
- **Artifacts are untyped.** Dispatch is on interface structure only.
- **Nothing is deleted.** The append-only event log is the source of truth; graph state
  is a materialized view.
- **Measures never adjudicate.** Search control steers attention, never status.

## Layout

```
config/                     §15  knob file (single file, exposed)
docs/                            normative spec
src/deepreason/
  harness.py                §1–§4 registration, well-formedness, materialized view, replay/time-travel
  canonical.py              §1   canonical JSON + sha256 content addressing
  programs.py               §1   budgeted test programs tau_kappa (predicate/program verdicts)
  loop.py                   P1   single-problem Conj -> Crit -> Adj loop
  ontology/                 §1   one schema: Artifact, Commitment, Warrant, Problem, Event, State
  log/                      §1   append-only JSONL event log; replay / time-travel
  storage/                  §14  content-addressed blobs; merge (P3); holdout namespace
  adjudication/             §4   two-pass labeling (Dung grounded + support cascade); att/dep construction (§1/§2)
  rules/                    §3   transition rules: Conj, Crit, Adj, Spawn, Refl
  rules/guards/             §3   registration guards: anti-relapse, rubric-verdict trial guard
  measures/                 §6   demarcation, hard-to-vary (HV), reach
  unification/              §7   born-connected reflex, isolation floor, hv-floor brake
  views/                    §8   theory(id), prose(id) — views, not types
  llm/                      §9   role adapter, pack renderer, role schemas
  informal/                 §10  skeletons, standards-as-case-law, judge audits, holdout, appellate
  capture/                  §11  schools, capture detection, response ladder, negative atlas, Pareto retention
  research/                 §12  observation-valued commitments → research backends
  scheduler/                §14  rule registry + budgets; school allocation
  experiments/              §11.8 λ dose-response runner (thresholds in /experiments)
  cli/                      §13  frontier / run / why / theory / schools / capture / reseed / trace …
experiments/                §11.8 pre-registered λ-experiment thresholds (committed before first look)
tests/                           acceptance tests per phase (grounded extension, replay, hv-floor, schools, λ)
```

## Phases (§16)

| Phase | Scope | Status |
|-------|-------|--------|
| P0 | deterministic core: schema, event log, two-pass adjudicator, replay | ✅ implemented |
| P1 | single-problem loop: Conj → Crit → Adj, anti-relapse, VS conjecturer | ✅ implemented |
| P2 | scheduler, all Spawn triggers, HV/reach, capture control (§11), λ experiment | ✅ implemented |
| P3 | merge, session namespaces | ✅ implemented |
| P4 | research commitments + backends | ✅ implemented |
| P5 | informal-domain protocol (§10) | ✅ implemented |
| P6 | frontier-model hardening | next |

## Development

```bash
pip install -e ".[dev]"
pytest
```
