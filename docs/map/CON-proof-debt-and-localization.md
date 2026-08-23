<!-- DR-CON-proof-debt-and-localization -->
Verified-at: 03b1edf4
Verify: python -m pytest tests/test_proof_debt.py -q
Owns: src/deepreason/proof_debt.py
Seams: 
Seams-undocumented: calculus x adjudication, calculus x problem-layer-lifecycle

# Proof debt and Duhem localization — what a judgment owes, and who may be blamed

**One half is BUILT, one half is DESIGNED AND PARKED, and the split is stated
here so no reader mistakes an agreement for a mechanism.**

- **Proof debt (E-1) is built.** Every claim about it below carries a `check:`
  that runs today.
- **Duhem localization (E-2) is designed and PARKED** — no `localization.py`
  exists, and the sections describing it carry NO checks, deliberately: there
  is nothing to authenticate. The operator parked it at the Rung D tranche's
  step-13 diff-budget stop and ruled that a future window should resume at
  `dr-plan-steps` rather than re-spec, so this document IS that window's
  entry artifact. See
  `experiments/2026-08-22-change-rungd-proof-debt-localization/PARKED.md`.

Nothing in the parked half is speculative in the sense of unexamined — the
design was measured against the tree before it was written down (both claim
names are already in the closed set; `dep` already supplies bundle membership).
It is simply not code yet, and this document says which sentences are which.

## What it is

Two channels that answer two different questions about a derived judgment, and
one rule they share.

**Proof debt (E-1)** answers *what does this judgment rest on?* A derivation
manifest is an ordinary registered artifact that itemizes a judgment's bill of
materials in three kinds — `KERNEL_CHECK`, `OPEN_CERTIFICATES`, `AXIOM_DEBT` —
and is wired to the judgment's validity node as EVIDENCE. Attacking an item in
that bill disables the judgment BEFORE pass one, by the ordinary `att`/`dep`
calculus and with no adjudication rule of its own.

**Duhem localization (E-2)** answers *when a bundle fails, who is at fault?* A
localization is an ordinary registered artifact saying "the fault in bundle b
lies with member m". A member is implicated only through a CONSULTED
localization. There is no automatic projection, no measure, no default and no
cascade — and that absence is the deliverable, not an omission.

The shared rule is the one both rows exist for: **a derived judgment may state
what it rests on and who it blames, and neither statement moves a label by
itself.** Only attacks move labels, and both artifacts are attackable like any
other.

## Why these are one document

They are two halves of one discipline. Proof debt makes a judgment's grounds
attackable; localization makes a judgment's BLAME attackable. Neither is a new
node type, neither has an event rule, and both are compiled by the one
controller-owned compiler in `calculus/compiler.py` — so the properties that
had to be re-proven for a new graph layer do not have to be re-proven at all.

They also meet in the data: `LocalizationV1.derivation_manifest_ref` lets a
localization carry its own bill, because deciding which member of a bundle is at
fault is itself a derived judgment and owes the same account.

## The receipt, and why it is derived rather than stored

The MANIFEST is an artifact on the log. It has to be: in this harness only
registered artifacts can be attacked, and an unattackable bill of materials is
the blob that R58 complained about ("a blob is readable, an evidence ref is
ATTACKABLE").

The RECEIPT is not stored anywhere. It is the itemized statement of what STILL
STANDS — each kernel check re-run now, each open certificate's current `Status`
read from replayed state, each axiom named — and it is rebuilt on every call.
That is the same discipline `calculus/standing.py::standing_of` and
`premises.py::premise_orphaned` already keep (C4: computed, never stored).

This is also the whole of "dependents are invalidated ON RECOMPUTATION rather
than retroactively". Nothing rewrites a past event. The next `build_att` sees
the new attack and the judgment loses; the log's prefix before that attack
replays to exactly what it always replayed to.

### The three item kinds

| kind | what it is | interface role | attackable |
|---|---|---|---|
| `KERNEL_CHECK` | a deterministic check the harness can re-run, as `(name, verdict)` | content only — no ref | not directly; it is re-derived, so arguing with it means changing the input |
| `OPEN_CERTIFICATES` | registered artifacts the judgment leans on but has not proved: a sample, an embedding, an admitted conjecture | `DEPENDENCE` | **yes** — this is the attackable half, and `evidence_lineage` reaches it from the validity node |
| `AXIOM_DEBT` | names from `DR-INV-axiom-basis` (`A1`…`A10`, `Ax 4.1`) the judgment assumes | content only — no ref | no, by construction: an axiom is what you do not prove. Naming it IS the deliverable |

## What is in scope for a receipt, and what is not

Scope is **attack-producing derived judgments** — the demonstrative fail
warrants registered through `rules/warrants.py::register_fail_warrant`. That is
the only class in the tree that can move another artifact's `Status`, so it is
the only class whose proof debt anyone can be wronged by.

Out, each for a reason rather than for brevity:

- **Render decisions** — Rung 6 is undelivered, so there is no producer. A
  receipt format for a layer that does not exist is `docs/ERRATA.md` E28's
  pattern exactly.
- **Labels** — a label's authority already IS its warrants, and every warrant
  already carries a validity node. A second account of what a label rests on is
  how two instruments come to disagree.
- **Measures** — they act only through attention (`A9`), so a measure that mints
  no warrant blames nobody. `receipt()` will READ a warrant a measure produced;
  no measure gains a receipt of its own.

## What a bundle is — DESIGNED, PARKED

**A bundle is any artifact that DEPENDS on its members.** Dependence already is
composition here: an artifact whose interface carries `DEPENDENCE` refs to a
theory, an apparatus and an interpretation is E-2's bundle, and
`localization.bundle_members` is the set of those targets.

No `poietic.bundle.v1` schema is minted, for two reasons. It would grow the
closed claim-name set, which `DR-SUB-calculus` exists to keep shut. And the word
is already taken twice over — qualification bundles, transaction bundles,
import bundles — so a third meaning would make every future grep ambiguous.

Note the direction, because it is the whole of Duhem: `dep` licenses the fall of
a DEPENDENT when a dependency falls. It does not license the converse. From a
failed whole to a faulty part is not a calculus step; it is adjudicated work.

## The two locks — DESIGNED, PARKED

Implication requires all three of: a CONSULTED localization naming the member, a
PROBLEMATIC bundle (`REFUTED` → `BUNDLE_REFUTED`, `SUSPENDED_UNSUPPORTED` →
`BUNDLE_UNACCREDITED`), and genuine membership. So:

1. **Filing a localization moves nothing on its own.** A sound bundle implicates
   nobody however many localizations name its members.
2. **A bundle becoming problematic moves nothing on its own.** With no
   localization consulted, no member is implicated, however many members it has.

Lock 2 is the one the harness would break first, and it is the one held by a
permanent mutation-proven guard test rather than by intention.

## Why both endpoints of a localization are MENTIONS — DESIGNED, PARKED

This is `premises.py`'s shape reused, not re-derived, and each half of it fails
differently if got wrong:

- Depend on the BUNDLE, and pass two suspends the localization the moment the
  bundle becomes problematic — erasing the relation that identifies the blame at
  exactly the moment it is needed. This is Law 9.4' in the same shape the
  premise attribution needed it.
- Depend on the MEMBER, and refuting the member suspends the localization —
  un-implicating the member at the moment the implication mattered.

The manifest is the one `DEPENDENCE`: if what the localization was derived from
falls, the localization should lose its support.

## Entry points

| you want | call |
|---|---|
| file a bill of materials for a judgment | `proof_debt.file_derivation_manifest` |
| read what a judgment still rests on | `proof_debt.receipt(harness, warrant_id)` |
| attach a bill to a fail warrant | `rules/warrants.register_fail_warrant(..., manifest_ref=...)` |
| file a blame statement | `localization.file_localization` — **parked** |
| read a bundle's members | `localization.bundle_members` — **parked** |
| read who is implicated | `localization.implicated(harness)` — **parked** |

`check: python -c "from deepreason.proof_debt import file_derivation_manifest, receipt, manifests_for; import inspect; from deepreason.rules.warrants import register_fail_warrant; assert 'manifest_ref' in inspect.signature(register_fail_warrant).parameters"`
`check: python -c "import importlib.util; assert importlib.util.find_spec('deepreason.localization') is None, 'localization is parked; if it now exists this document is stale'"`

## State it owns

None. The module is pure functions over replayed state plus one authoring
operation that calls `harness.create_artifact`. Nothing here writes a `Status`,
and it does not import `adjudication` — the same structural guard
`calculus/standing.py` carries, for the same reason. The parked module inherits
the identical obligation.

`check: python -m pytest tests/test_proof_debt.py -k "moves_no_label or read_path" -q`

## Invariants

`DR-INV-frozen-surfaces` — no surface is touched. `DR-INV-axiom-basis` — the
BUILT half proves `A1`/`A2` in the form the receipt demands (a receipt is a
pure fold over the log, recomputed under a finite deterministic budget) and
preserves `A3`, `A9` and `Ax 4.1`. The parked half would prove `A5` at a third
site (the mention law, for localizations); it does not yet.

`check: python -m pytest tests/test_proof_debt.py -k "replays_identically or recomputation_not_retroactively" -q`

## Where to change what

| to do X | edit Y | test Z |
|---|---|---|
| add an item kind to a receipt | `calculus/claims.py` + `calculus/compiler.py` | `tests/test_proof_debt.py` |
| change what makes a bundle problematic | `localization.py` (parked) | `tests/test_localization.py` (parked) |
| give another warrant site a manifest | that site only; `register_fail_warrant` already takes it | that site's own tests |
| add a reader for `implicated()` | a new consumer; nothing here | its own tests |

## Traps

- **The tempting automatic version is one line away, and NOTHING GUARDS IT
  TODAY.** Because members are read off `dep`, "the bundle fell, so implicate
  everything under it" is trivially writable. The guard that must stop it —
  `test_a_problematic_bundle_implicates_no_member_without_a_localization`,
  mutation-proven — is parked with the rest of E-2. Until that test exists,
  this trap is a warning to a future author and not a live protection, and
  saying so is the difference between a limitation and a defect.
- **A receipt is not a warrant.** Filing a manifest changes no label. If a
  change makes a manifest move a label directly, the change is wrong however
  useful it looks — only attacks move labels.
- **`structural` on `derivation_manifest_wf` is load-bearing.** Reach derives
  its structural set from it, so a well-formed receipt grounds no reach and
  confers no prose immunity. Reclassifying it would let an artifact buy
  protection from criticism by admitting debt.
  `check: python -c "from deepreason.programs import PROGRAMS; assert PROGRAMS['derivation_manifest_wf'].class_ == 'structural'"`
- **Only the SAMPLED rent path files a bill.** A premise felled for an empty
  attack surface rests on `crit` alone, which is re-derivable and owes no
  certificate. A bill filed there would be debt against a judgment that needs
  none.
  `check: python -m pytest tests/test_proof_debt.py -k "undecided_rent_verdict_files_no_manifest" -q`
- **Membership is checked in the derived predicate, not in the
  well-formedness program.** The program is handed `(text, budget, artifact)`
  and no harness state, so it cannot see whether the member is in the bundle.
  Blame landing outside its bundle is stopped by `implicated()`, and that
  placement is a decision, not an oversight.
