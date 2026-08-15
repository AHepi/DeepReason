# State of the Program — 2026-08-14

A briefing for anyone joining the DeepReason project, and the ledger of
what changed in the 2026-08-11 → 08-14 program. Written by the monitor
session at the operator's request. Corrections to this document go in
`docs/ERRATA.md`, never silently here.

---

## 1. What DeepReason is

DeepReason is a **Popperian reasoning harness**: a system that drives
large language models through cycles of conjecture and criticism over an
**append-only, replay-verifiable record**. The record — not the model's
prose — is the only admissible evidence about what a run did.

The core loop: a **problem** (starting from the operator's seed
question) is offered to a **conjecturer** model, which proposes
**artifacts** (candidate ideas). **Critics** attack them. Attacks are
only real when carried by a registered **warrant** with a validity node;
warrants materialize **attack edges** in a graph. Verdicts come from the
**grounded extension** — the skeptical fixed-point semantics of formal
argumentation (accept only what can be defended from unattacked ground;
unique answer, polynomial cost, deterministic). Statuses are *computed
from the record*, never stored or decreed: there is no "accept" event
anywhere in the system, and "accepted does not mean true" — it means
*survived the criticism supplied so far*.

Everything meaningful is **typed**: stops, refusals, budget exhaustion,
capability grants, trial verdicts. Model prose is never evidence; the
typed log (`log.jsonl`), the content-addressed object store, and the
replay validator (`verify_root`) are. Runs use real provider models
(currently via Ollama Cloud) in **seats** — conjecturer, critic,
defender, judges — with a qualification battery that certifies each
model/role pair before a run may spend money on it.

## 2. How the project runs

One human operator (not a developer) directs everything. The operator's
words are the only design authority, and they are **ledgered verbatim**:
every change tranche starts with a `REQUEST.md` quoting the operator and
numbering requirements; every delivery reconciles against those numbers.

Work happens in **tranches** run by disposable AI "executor windows,"
each following a workflow skill family in `.claude/skills/`:

- `dr-change-orchestrator` — operator-suggested changes (capture → spec
  → plan → execute → validate → deliver).
- `deepreason-orchestrator` — defects (diagnose **from the typed
  record before reading code** → reproduce → fix → verify).
- `dr-audit-orchestrator` — read-only audits (broken / dead /
  docs-drift / spec-drift / goal-trace), rated for inexpensive models:
  every step is a command, a paste, or a comparison against
  `docs/AUDIT_BASELINES.md`. Findings become paste-ready fix prompts;
  the audit itself never fixes anything.

A **monitor session** reviews deliveries against commits (never
claims), merges to main, ledgers operator words as laws, and writes the
prompts the operator pastes into new windows. Instruments keep everyone
honest: the full pytest gate (currently **0 failed**), the executable
documentation checks (`tools/docs_verify.py` — the code map's claims
carry shell commands that must exit 0), wheel smokes pinning the public
surface, and a root sweep over committed run records. Two append-only
errata ledgers (`docs/ERRATA.md`, `docs/ERRATA_EXECUTOR.md`) record
every claim later found wrong — corrections are new entries, never
edits.

## 3. The theory stack

Three committed documents govern the theory; they form one line of
descent:

1. **`docs/POIETIC_CALCULUS_v0.1.md`** — the epistemology. Knowledge
   grows only by genesis (GEN) and criticism (CRIT); conjectures are
   never derived from evidence; provenance confers nothing ("genesis
   inertness"); no credences, no acceptance events, no goal functional.
   Its §7 is the project's charter sentence: *an engine that implements
   the bookkeeping faithfully and leaves genesis open* **is** *an
   implementation of the calculus* — DeepReason is the bookkeeping;
   the LLMs are the open genesis.
2. **`docs/COMPUTABLE_CALCULUS.md`** — the executable design. Its
   central contribution is the **two-axis state**: *status*
   (truth-standing under criticism) and *standing* (role in generation
   — is this artifact framed, or does it do the framing?). This makes
   **background knowledge** representable: a framework promoted by
   measured reach that frames every conjecture in its scope, remains
   attackable, can be *refuted and still framing*, and whose fall
   cascades as premise-criticism through every problem posed in its
   terms.
3. **`docs/POIETIC_CALCULUS_FORMALIZED.md`** — the proofs and repairs.
   Confirms the design's theorems and finds its gaps: the
   **frame-separation invariant** (the mention law alone does not
   secure "refuted but still framing"), a **third frame exit**
   (contestation, beyond fall and revocation), the **restored-premise
   gap** (what happens to orphaned problems when a fallen frame is
   reinstated), the **Refuted/Superseded split** (unilateral defeat vs
   comparative replacement), and the minimal axiom basis **A1–A10**.

A fourth document — an exploratory proof system (𝔓⊢) — was reviewed and
deliberately **not** incorporated (operator instruction). Three of its
ideas were judged essential and are queued; see §6.

## 4. The operator design laws (the standing amendments)

Ledgered in `CLAUDE.md`, verbatim, in force for all work:

| Date | Law (kernel) |
|---|---|
| 2026-08-08 | **Formalism is an option, never an obligation.** Nothing may force a conjecture to be formal or penalize it for being informal. |
| 2026-08-08 | **Tokens are cheap; the agent is not.** Prefer live runs and generated evidence over building machinery or reasoning offline. |
| 2026-08-09 | **Seats change how content is GENERATED, never what counts as EVIDENCE.** No seat, mode, or package lets generated prose skip criticism. |
| 2026-08-09 | **A solo run with everything on must be an option.** Single-model operation may never be structurally locked out of any capability. Judge models are suspect-by-default ("they prosecute without any discernable discrimination"). |
| 2026-08-12 | **All configurations should be allowed.** Compile-time denial is abolished; anything that parses compiles, with former refusals recorded as typed disclosures. Impossibility surfaces at runtime, typed. |
| 2026-08-13 | **Operations are available to every configuration.** Every launch path reaches the same typed terminal and accepts the same operations (amend, continue, cancel, result, finalize). Enforced by construction: there is now exactly one run path. |
| 2026-08-14 | **Old runs owe the future nothing; new versions are optimised for new functions.** Cross-version record compatibility is retired. Scope boundary: a current-version run's record remains typed, append-only, and replayable by the code that wrote it — within-version integrity is the epistemology itself. |

## 5. The doctrine amendments to the spec (2026-08-13/14)

The operator corrected the spec's theory of how problems grow, and the
calculus documents largely deliver it. The binding decisions:

- **H1 — failed conjectures do not spawn problems.** The spec's "failed
  verdict ⇒ successor problem" trigger is deleted. A failed conjecture
  records its failed commitments; nothing else. Succession lives on the
  problem layer.
- **H2 — problems are first-class subjects of criticism.** A problem
  can be refuted for a false implicit assumption, unsolvability as
  posed, or a false premise (canonical example, operator verbatim:
  *"What is the colour of a siren"* — flawed before any answer, by
  category error). Mechanism: a critic registers the hidden
  presupposition as an ordinary artifact plus an adjudicated
  *attribution* ("problem π presupposes X"); when both stand and X
  falls, the orphan cascade fires (retire / translate / independence).
  `provenance.frame` becomes the special case of a general **premise
  channel**, derived rather than stored (decision D-3).
- **H3 — status vocabulary.** The calculus's honest terms (*unrefuted*,
  *suspended-unsupported*) are adopted at the view/presentation layer
  only; stored record labels never change.
- **Decisions D-1..D-7** (reconciliation tranche, all answered):
  crisis-as-render-state; the siren example as the worked case; derived
  premises; the knowledge view shipped with its definition printed
  inline; a fixed JSON scope-DSL for frame scopes; **program-first
  succession** (comparative succession adjudicated by programs over the
  incumbent's machine-derivable wound list, judges optional behind the
  trial guard — the only road compatible with the solo law); and the
  signal-contract design absorbed (see §7).
- **Riders from the Formalization:** frame-separation as a required
  invariant; the third exit grade (`premise-contested`); restored
  premises handled as orphanhood-that-deactivates-on-reinstatement
  (exit episodes retained).

## 6. Three essentials, written down (not priority — queued for the spec revision)

Adopted from the reviewed-but-not-incorporated proof system, on the
operator's instruction that they are essential:

1. **Proof debt.** Every derived judgment travels with an explicit,
   itemized, attackable manifest of what it rests on: kernel-checked
   steps, open certificates (attackable conjectures such as slack
   embeddings), and named axioms. Attacking a manifest item invalidates
   dependents on recomputation. The deep point: in proof, computation,
   and experiment alike, a result's authority is exactly the authority
   of its premises and apparatus — the bill of materials stays stapled
   to the package. DeepReason's validity nodes already do this for
   warrants; proof debt generalizes the discipline to all derived
   judgments, with a receipt format (`KERNEL_CHECK / OPEN_CERTIFICATES
   / AXIOM_DEBT`).
2. **Duhem localization.** A problem with an explanatory *bundle*
   (theory + apparatus + interpretation) does not project blame onto a
   member without a *standing localization criticism* — blame
   assignment is adjudicated work, never automatic. Cousin of the H2
   premise channel; slots into the same machinery.
3. **The succession bridge caveat.** A "good rival covering the same
   explicanda" is not yet a strict successor: rigidity,
   non-immunization, and a strictness witness are additionally
   required. The D-6 succession programs must implement the strong
   relation, not the weaker one the prose word "rival" suggests.

## 7. The program of 2026-08-11 → 08-14 (what shipped)

All merged to main, each with its tranche directory under
`experiments/` holding the full ledger (request, spec, checklist,
validation, delivery):

- **Skills overhaul** under an operator-supplied authoring standard
  (`.claude/skills/authoring-skills/`): evidence-required existence,
  operation-shaped wording, mutation-proven gates.
- **Audit family** built and activated; first audit: 124 proof-backed
  findings rows, 82 parked into 13 paste-ready prompts; it also caught
  and fixed a flaw in its own dead-code census method.
- **All-configurations law delivered** (~13 of ~33 denial sites
  converted to typed disclosures; remainder queued), **200k token
  ceiling removed**, **calibration-receipt dead-end converted** to a
  disclosure.
- **One run path.** The bare scheduler-only launch path is deleted;
  every configuration enters the managed service
  (`start_manifest_run`); `deepreason run` is a thin shell. Map checks
  are inverted negations so a second path reappearing fails the gate.
- **Full lifecycle everywhere:** `finalize` (append-only
  terminalization of stranded roots), `amend` (amendment epochs that
  attach evidence properly), `continue`, and `deepreason results` (one
  discoverable, typed way to read a run's outcome).
- **Dynamic token steering fixed:** the controller attached but sat
  inert (envelopes never anchored to configured caps); now anchored,
  with a typed nothing-to-steer record so silent inertness cannot
  recur. Full gate now reads **0 failed** (the long-standing bronze
  census carve-out was deleted on operator ruling).
- **The grounded-extension live run** (the program's evidence
  centerpiece): 24 cycles + 8 continuation cycles, ~1.24M tokens,
  judges genuinely ruling (162 + 104 judge calls through real defended
  trials), 245 surviving artifacts. Its best candidate proposes
  attack-edge-level "defeater warrants" — and was found to rest on a
  false premise (edge-level defeat already exists via validity-node
  closure) that criticism failed to catch *even with sources attached*,
  because citations arrive as prose, not through the verifiable
  quote-checking channel (parked as P4). The run also exposed the
  criticism-debt pathology (2,894 spawns vs 16 criticism dispatches)
  that motivated both the controller fix and the H1/H2 doctrine.
- **Provider operations intelligence** committed
  (`docs/OLLAMA_CLOUD_OPERATIONS.md`): account-level concurrency, 429
  disambiguation, mid-stream 200-with-error hazard, model-retirement
  reproducibility rules.
- **Theory trio committed**; **reconciliation tranche delivered** (the
  calculus-vs-tree drift table, the seven-rung implementation ladder,
  the decision sheet — all decisions answered). **Rung 1 is open.**

## 8. What is yet to be done

- **The v2 ladder** (`experiments/2026-08-14-change-calculus-
  reconciliation-v2/LADDER.md`), seven gated rungs, one tranche each:
  vocabulary groundwork → premise channel + spawn-trigger deletion →
  frame assertions + standing view (with frame-separation) → promotion
  problems + programs → render semantics + departure protocol →
  falls/cascade/orphans (three exit grades, reinstatement handling) →
  rent/nomination/authority-audit + capture diagnostics (adopting the
  Formalization's SC/ATH/Debt/RR/VAR/EGR formulas). The ladder is
  being revised under the 2026-08-14 law (old-root proof obligations
  dropped).
- **The three essentials of §6** — folded into the spec revision as
  their own rung(s) when the operator schedules them.
- **Evidence citability (P4):** make quoted evidence flow through the
  verifiable `EvidenceRefClaimV1` channel so citations are checked
  bytes, not prose claims. The single highest-leverage fix for
  criticism quality.
- **Remaining denial-site conversions (~20) + the seats/evidence
  adversarial law test** (prompt written, window not yet run — the test
  is seeded from the conversion census, in that order by design).
- **Embedder auto-install:** live runs silently degraded to a hash
  fallback because the neural embedder is an optional dependency
  nobody's container installed; prompt written, window not yet run.
- **Signal-contract design** (absorbed into the v2 rungs): the signal
  registry as a producer-agnostic contract, seat-instance keying,
  architecture tests pinning the controller to the signal interface,
  topology-matrix compilation tests, typed open-loop notices.
- **Audit follow-ups:** the remaining parked prompts from the first
  audit (P12's spec-series boundary question among them), and the
  next audit run under the now-corrected census method.

## 9. How to help

Read, in order: `CLAUDE.md` (in full — the laws bind you),
`docs/INDEX.md`, `docs/map/INDEX.md` (the code map; its claims are
re-derived by executable checks, and `docs/map/INV-frozen-surfaces.md`
lists what you may not touch without operator words), the theory trio
(§3), the newest `RESULTS.md` segments under `experiments/`, and both
errata ledgers.

Norms that are enforced, not aspirational: the record over prose;
diagnosis from the typed record before code; one tranche, one goal
(out-of-scope findings are PARKED with a ready-to-send prompt, never
fixed in place); every completion claim carries pasted proof; gates at
0 failed with baselines in `docs/AUDIT_BASELINES.md`; the map moves in
the same commit as the code it describes; corrections are appended to
the errata ledgers, never edited in place; and the operator's verbatim
words outrank everything, including this document.
