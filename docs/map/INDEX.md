<!-- DR-INDEX -->
Verified-at: b41c5cf10
Verify: python tools/docs_verify.py --links

# The map — start here

This routes. It does not explain. Follow a row to the document that does.

`docs/map/` describes what the code IS and where it lives, so a large change can
be scoped by reading a few files instead of 125 000 lines. It is not a spec —
`docs/harness-spec-*.md` says what the system ought to do. When the two
disagree, the code is what the map must describe.

**Read `SCHEMA.md` once**, before you write or change anything here. It is the
contract: ID grammar, the check rule, and how a document is updated.

## Route by what you are trying to do

| You want to... | Go to |
|---|---|
| find where something lives | the subsystem table below |
| change how two things interact | the seam table, then `REC-change-a-seam.md` |
| know whether you are allowed to change it | `INV-frozen-surfaces.md` — **first, always** |
| understand a cross-cutting idea (schools, authority, warrants) | the concept table |
| diagnose a defect | the `Traps` section of the covering document, then the record |
| know which rung answers for a calculus axiom | `INV-axiom-basis.md` |
| know why an artifact is (or is not) framing its problems | `CON-standing-and-background.md`, then `SUB-calculus.md` |
| know what a pack shows about the frame it is posed in | `SEAM-calculus-x-rules.md`, then `CON-packs-and-token-economy.md` |
| write or update a map document | `SCHEMA.md` |

**The one ordering rule:** read the SEAM before the subsystems it joins. A seam
document tells you which *fraction* of each side your change touches, and it is
usually small. Reading both subsystem documents first is reading ten times more
than you need.

## Subsystems

| Document | Covers |
|---|---|
| `SUB-ontology.md` | Artifact, Commitment, Warrant, Problem, Interface, EpistemicState — the vocabulary everything speaks |
| `SUB-harness.md` | the append-only log, event application, state materialization. **Frozen** |
| `SUB-rules.md` | conjecture, criticism, warrants, spawn, guards — the epistemic moves |
| `SUB-adjudication.md` | warrants → attack edges → status labels |
| `SUB-scheduler.md` | problem selection, cycles, budgets, school and capability dispatch |
| `SUB-llm.md` | adapter, route firewall, packs, wire contracts, repair, profiles |
| `SUB-scratch.md` | the imaginative workshop, declared `advisory_non_grounding` |
| `SUB-capabilities.md` | simulation and research lifecycles. State digests are **frozen** |
| `SUB-workflow.md` | the v6 transactional work lifecycle, replay, recovery |
| `SUB-bridge.md` | the grounded-application bridge: ledger, compose, evidence packs |
| `SUB-evidence.md` | attached dossiers, admitted blocks, and byte-checked citations |
| `SUB-verification.md` | `verify_root`, replay validation, epistemic checks. **Frozen** |
| `SUB-manifest.md` | RunManifest schema and validators, qualification. **Frozen** |
| `SUB-evaluation.md` | programs, oracles, measures, informal trials — where formal meets informal |
| `SUB-calculus.md` | the typed claim substrate: a CLOSED body union and the one controller-owned compiler that assigns every ref role; also nomination (what makes a promotion problem exist) and the six promotion criteria |

## Concepts (not packages — that is why they need documents)

| Document | Covers |
|---|---|
| `CON-schools.md` | a stance, a lineage, and sometimes a route |
| `CON-authority.md` | who may change a Status, and the two authority vocabularies |
| `CON-warrants-and-attacks.md` | the chain: no warrant, no edge, no REFUTED |
| `CON-run-identity.md` | deterministic run ids, roots on disk, retiring and amending |
| `CON-capability-lifecycle.md` | typed proposal → admission → work order → result |
| `CON-packs-and-token-economy.md` | prompt construction, section allocation, budgets |
| `CON-conjecture-source.md` | the socket that proposes candidate artifacts (`rules/conj.py`) |
| `CON-criticism-source.md` | the socket that attacks or scrutinises a target (`rules/crit.py`) |
| `CON-scheduler-ranking.md` | which problem a cycle works on (`Scheduler._select_problem`) |
| `CON-seats.md` | how a role becomes a provider request: `select_lease`, `EndpointLease`, and today's one-profile-per-run mint |
| `CON-conjecture-kinds.md` | formal vs informal, where kind is signaled, and the R-g guardrail against ranking/admission/acceptance on kind |
| `CON-proof-debt-and-localization.md` | what a derived judgment rests on (`KERNEL_CHECK`/`OPEN_CERTIFICATES`/`AXIOM_DEBT`), and what it takes to blame one member of a bundle |

## Invariants and recipes

| Document | Covers |
|---|---|
| `INV-frozen-surfaces.md` | the five surfaces you may not change, and the two instruments that prove you did not |
| `INV-axiom-basis.md` | the eleven axioms the calculus rests on, which rung proves each, and which rungs must not break it |
| `REC-change-a-seam.md` | the recipe for the commonest large change, worked on schools × scratchpad |

## Seam matrix

Coupling is measured: directed `deepreason.*` imports between the files each
document declares it `Owns:`, summed both ways. High coupling is a reason to
document a seam, not a proof that one matters — and a low number does not mean
the agreement is unimportant.

**A pair listed here without a document has NOT been shown to be
uninteresting.** It has only not been written yet. That is different from a pair
absent from this table entirely, which is a pair with no measured import
traffic at all.

| Coupling | Pair | Document |
|---|---|---|
| 37 | rules × workflow | `SEAM-rules-x-workflow.md` |
| 33 | llm × workflow | `SEAM-llm-x-workflow.md` |
| 29 | evaluation × rules | `SEAM-evaluation-x-rules.md` |
| 24 | llm × manifest | `SEAM-llm-x-manifest.md` |
| 22 | llm × rules | `SEAM-llm-x-rules.md` |
| 21 | bridge × manifest | `SEAM-bridge-x-manifest.md` |
| 18 | ontology × rules | `SEAM-ontology-x-rules.md` |
| 18 | rules × scratch | `SEAM-rules-x-scratch.md` |
| 16 | scheduler × workflow | `SEAM-scheduler-x-workflow.md` |
| 16 | bridge × llm | `SEAM-bridge-x-llm.md` |
| 15 | bridge × ontology | — not yet written |
| 14 | evaluation × ontology | `SEAM-evaluation-x-ontology.md` |
| 13 | scratch × workflow | `SEAM-scratch-x-workflow.md` |
| 11 | harness × workflow | `SEAM-harness-x-workflow.md` |
| 11 | rules × scheduler | `SEAM-scheduler-x-rules.md` |
| 11 | capabilities × workflow | — not yet written |
| 11 | manifest × workflow | — not yet written |
| 10 | llm × scratch | — not yet written |
| — | schools × scratch | `SEAM-schools-x-scratch.md` |
| — | manifest × schools | `SEAM-manifest-x-schools.md` |
| — | adjudication × authority | `SEAM-adjudication-x-authority.md` |
| — | adjudication × rules | `SEAM-adjudication-x-rules.md` |
| — | capabilities × rules | `SEAM-capabilities-x-rules.md` |
| — | harness × verification | `SEAM-harness-x-verification.md` |
| — | periphery × verification | `SEAM-periphery-x-verification.md` |
| — | llm × scheduler | `SEAM-llm-x-scheduler.md` |
| — | calculus × rules | `SEAM-calculus-x-rules.md` |

The last nine carry no import-count because at least one side is a concept
rather than a package, the agreement is enforced without a direct import, or —
the periphery × verification and calculus × rules cases — every import between
the sides is function-local, which the coupling metric cannot see. The adjudication ×
authority case is the strongest form of that: the agreement IS the absence of
traffic, and the measured consequence of breaking it is that committed roots
change meaning.
**That is exactly why they need documents**: coupling metrics cannot see them,
so nothing but a written seam will tell the next reader they exist.
The llm × scheduler case is the newest and was the most expensive: the
`scheduler/` package does import `deepreason.llm`, but the agreement that
document covers — the allocation controller against the route lease — is
carried entirely by `controller.py`, which imports nothing from `llm/` and
reaches the leases duck-typed off the adapter. A count taken over the packages
would have read 10 and pointed at the wrong traffic.

`check: python tools/docs_verify.py --links`

## Reading order for someone new

1. `SCHEMA.md` — how to read everything else.
2. `INV-frozen-surfaces.md` — the boundaries, before you form any plan.
3. `CON-warrants-and-attacks.md` — the central causal chain of the system.
4. `SUB-ontology.md`, then `SUB-harness.md` — the vocabulary and the record.
5. Whatever your task needs, via the tables above.

## Coverage, stated honestly

The map does not yet cover everything, and pretending otherwise would make it
untrustworthy where it *is* good.

- Modules under no subsystem document's `Owns:` are listed by
  `python tools/docs_verify.py --stale` only if their document exists at all;
  to find uncovered ground, compare `Owns:` headers against `src/deepreason/`.
- Seam documents exist for the pairs marked above and no others.
- `docs/map` describes `src/deepreason/`. `tests/` and `experiments/` are
  navigated by convention: a test file mirrors the module it guards, and a
  tranche directory is named `<date>-<fix|change>-<slug>`.

Closing a gap is ordinary work: `SCHEMA.md` says how, and the orchestrator
skills require the map to move with the code that changes it.
