# Spec for: Rung D — proof debt (E-1) and Duhem localization (E-2)

Traces: every item cites R/C numbers from REQUEST.md. Untraceable items are bugs.

Re-read before writing: REQUEST.md in full (no amendments yet), `INV-frozen-surfaces.md`,
`INV-axiom-basis.md`, `SUB-calculus.md`, `CON-warrants-and-attacks.md`,
`CON-problem-layer-lifecycle.md`.

---

## 0. The design finding that decides the shape of this rung

**Both names this rung needs are ALREADY in the closed claim set, and one of
their refs is already compiled.** Measured, not recalled:

    $ grep -n "derivation-manifest\|localization" src/deepreason/calculus/claims.py
    27:    "poietic.derivation-manifest.v1",
    32:    "poietic.localization.v1",

    $ grep -n "derivation_manifest_ref" src/deepreason/calculus/claims.py src/deepreason/calculus/compiler.py
    claims.py:95:    derivation_manifest_ref: str | None = None
    compiler.py:55:        if body.derivation_manifest_ref is not None:

So Rung D is what Rung 4 was for `poietic.frame-assertion.v1`: it supplies
PRODUCERS for names the substrate already declared. **The closed name set does
not grow** (`len(CLAIM_SCHEMAS) == 9` before and after), and that is the
property `SUB-calculus.md` exists to protect — "an ontology addition riding in
on a rung meant only to build one is exactly what the closure exists to stop".

Second finding, and it is why D1 needs no adjudication change at all: the
EVIDENCE closure R58 asks for is already implemented.

    $ sed -n '157,171p' src/deepreason/adjudication/edges.py
                # Evidence closure: the nu explicitly declares which recorded
                # evidence is load-bearing. An attack anywhere in that evidence's
                # dependency lineage is an attack on the nu's validity.
                ...
                    for ref in nu_artifact.interface.refs:
                        if ref.role == RefRole.EVIDENCE:
                            evidence.update(evidence_lineage(ref.target))

`evidence_lineage` walks DEPENDENCE refs transitively. So: a manifest declared
as EVIDENCE on ν, DEPENDING on its open certificates, makes an attack on a
certificate an attack on ν, and (by the existing validity-node closure) an
attack on every critic carrying that warrant. R58's regression — "target
refuted → manifest item attacked → critic loses validity pre-grounded → target
reinstated → replay identical" — is reachable with **zero** lines changed in
`adjudication/`.

---

## 1. Q1 answered with reasons (R5) — which derived judgments are in scope

The operator's own question named three candidates. Each is answered, and the
answer is a scope, not a preference.

| candidate | verdict | reason |
|---|---|---|
| **render decisions** | **OUT** | they do not exist. Rung 6 (render + departures) is undelivered — LADDER.md §3's execution table shows Rungs 5–8 outstanding. A receipt format for a layer with no producer is `docs/ERRATA.md` E28's exact pattern: a mechanism nobody triggers |
| **labels** (`Status`) | **OUT** | a label's whole authority already IS its warrants, and every warrant already carries a validity node — the one class E-1 names as the model. A receipt bolted onto a label would restate what `att`/`dep` already compute, and R12 forbids it from changing anything, so it would be inert by construction. Worse, it would be a SECOND account of what a label rests on, which is how two instruments come to disagree |
| **measures** | **OUT of the writer, IN as a reader** | measures act only through attention (A9). A measure that mints no warrant blames nobody, so it has no proof debt anyone can be wronged by. `receipt()` will read any warrant, including one a measure produced; no measure gains a receipt of its own |
| **attack-producing derived judgments** — i.e. every DEMONSTRATIVE fail warrant registered through `rules/warrants.py::register_fail_warrant` | **IN — the whole of D1's scope** | this is the class that *does something to somebody*: it is the only derived judgment in the tree that can move another artifact's `Status`. It is also literally the class E-1 names ("the harness already does this for ONE class — warrants carry validity nodes"), so generalising it means making the bill of materials on that node ITEMIZED and ATTACKABLE rather than a readable blob. And it is R58's ledgered target, word for word |

**The narrow scope, stated once (R6):** a receipt travels with a demonstrative
fail warrant. The first producer is `premises.py::premise_rent_sweep`, chosen
because it is the one shipped site whose verdict already rests on a SAMPLE it
records only as an unattackable blob — R58's own complaint ("a blob is
readable, an evidence ref is ATTACKABLE"). Every other `register_fail_warrant`
site gains the CAPACITY to carry a manifest and is left unchanged; passing no
manifest is the unchanged path.

---

## 2. Q2 answered (R4 + R10) — how a receipt both travels and stays derived

R4 says a receipt TRAVELS WITH the judgment; R10 says receipts RECOMPUTE FROM
THE LOG, derived, never stored. Those are not in tension once the two things
are named apart:

- The **derivation manifest** is a registered ARTIFACT. It must be, because R4
  requires it to be attackable, and in this harness only registered artifacts
  can be attacked. It is on the log; that is not "storing a receipt", that is
  the bill of materials being a thing you can argue with.
- The **receipt** is the itemized STATEMENT OF WHAT STILL STANDS — each kernel
  check re-run, each open certificate's current `Status`, each axiom named. It
  is a pure function of replayed state, built on every call, never written.
  Exactly `standing()`'s and `premise_orphaned()`'s discipline (C4).

"Dependents invalidated ON RECOMPUTATION rather than retroactively" then needs
no mechanism at all, and that is the point: nothing rewrites a past event. The
next `build_att` sees the new attack and the critic loses; the log before that
attack is unchanged and replays to what it always replayed to.

### The three item kinds, concretely

| kind | what it is | how it enters the interface | attackable? |
|---|---|---|---|
| `KERNEL_CHECK` | a deterministic check the harness can RE-RUN — `(name, verdict)`. The receipt recomputes it rather than trusting the record | content only; no ref | not directly — it is re-derived, so arguing with it means changing the input, not the record |
| `OPEN_CERTIFICATES` | refs to registered artifacts the judgment LEANS ON but has not proved — a sample, a slack embedding, an admitted conjecture | `DEPENDENCE` ref (so `evidence_lineage` reaches it from ν) | **yes** — this is the attackable half |
| `AXIOM_DEBT` | names from `INV-axiom-basis.md` (`A1`…`A10`, `Ax 4.1`) that the judgment assumes | content only; no ref | no, by construction — an axiom is what you do not prove. Naming it is the whole deliverable: the bill is visible |

---

## 3. Q3 answered (R7) — what a bundle IS in this codebase

Measured first, because the word is already taken — in senses that have
nothing to do with Duhem:

    $ grep -rin "\bbundle\b" --include=*.py src/deepreason/ | wc -l
    95

    $ ... | awk ... | sort | uniq -c | sort -rn | head -4
     22 src/deepreason/qualification.py      # ReusableQualificationBundleV1
     14 src/deepreason/workflow/transaction_service.py
     12 src/deepreason/imports.py
      9 src/deepreason/workflow/replay.py

Every one of those 95 is a qualification bundle, a transaction bundle or an
import bundle. **There is no EPISTEMIC bundle in the tree**, and the collision
is a second reason not to mint a `Bundle` type: a third meaning of a word that
already carries two would make every future grep ambiguous.

The answer that adds no ontology: **a bundle is any artifact that DEPENDS on
its members.** Dependence already IS composition in this harness — an artifact
whose `Interface` carries `DEPENDENCE` refs to a theory, an apparatus and an
interpretation is exactly E-2's bundle, and `bundle_members(harness, b)` is the
set of those targets.

This answer is chosen over a new `poietic.bundle.v1` schema for two reasons and
one of them is the mutation proof:

1. It does not grow the closed name set — §0's property.
2. **It makes the tempting automatic version wireable, which is what makes
   R13's mutation proof mean anything.** If members were only knowable from a
   localization, "project blame automatically" would be unimplementable and the
   guard would be guarding nothing. With members read off `dep`, the automatic
   version is one line — "the bundle fell, so implicate everything under it" —
   and the guard test is the only thing standing between the harness and it.
   That is the honest shape of the danger E-2 names.

Note the direction carefully, because it is the whole of Duhem: `dep` licenses
the fall of a DEPENDENT when a dependency falls. It does not license the
converse. From a failed whole to a faulty part is not a calculus step; it is
adjudicated work.

---

## 4. Q4 answered — R58 is IN

R58 is ledgered "Rung D (E-1)" in the v2 program's own REQUEST.md and its
regression is the concrete form of R10 + R12. It is delivered here (S8, S12).

## 5. Q6 answered — R12 needs a guard, and the guard is structural

Cheapest authority is the code, so it was consulted rather than assumed:
`calculus/standing.py` already carries the precedent guard —

    check: ... assert not any(isinstance(n,ast.Call) and 'create_artifact' in ...)
           ... assert not any('adjudication' in m for m in mods)

The same two-part structural check is applied to both new modules' READ paths
(S13). Structural, not behavioural, because a behavioural test proves a label
did not move on the one input it tried; a structural check proves the module
holds no call that COULD move one.

---

## Items

### D1 — proof debt

**S1 (R4, R5).** `src/deepreason/calculus/claims.py` | before: `_IMPLEMENTED`
is the three Rung-3c/4 names; `DerivationManifestV1` does not exist | after:
`DerivationManifestV1` body — `kernel_checks: list[KernelCheckV1]`,
`open_certificate_refs: list[str]`, `axiom_debt: list[str]`, `subject_ref`
(the artifact the judgment is about) — added to `_IMPLEMENTED`. `CLAIM_SCHEMAS`
is UNCHANGED.
    accept: `python -c "from deepreason.calculus import CLAIM_SCHEMAS; from deepreason.calculus.claims import _IMPLEMENTED; assert len(CLAIM_SCHEMAS)==9 and 'poietic.derivation-manifest.v1' in _IMPLEMENTED"`

**S2 (R4).** `src/deepreason/calculus/compiler.py` | before: no rule for a
manifest body | after: `DerivationManifestV1` → `DEPENDENCE` on every
`open_certificate_ref`, `MENTION` on `subject_ref`, no ref for kernel checks or
axiom debt. `MENTION` on the subject and not `DEPENDENCE`, for the mention
law's own reason: a manifest that depended on the judgment's subject would be
suspended the moment the subject was refuted — i.e. exactly when the bill of
materials is being read.
    accept: `python -m pytest tests/test_proof_debt.py::test_open_certificates_are_dependences_and_the_subject_is_a_mention -q`

**S3 (R4).** `src/deepreason/calculus/programs.py` +
`src/deepreason/programs.py` | before: two claim wf programs registered | after:
`derivation_manifest_wf` registered as `"structural"`, with
`DERIVATION_MANIFEST_COMMITMENT`. Structural means it grounds no reach and
confers no prose immunity — a well-formed receipt must not immunise its own
judgment.
    accept: `python -c "from deepreason.programs import PROGRAMS; assert PROGRAMS['derivation_manifest_wf'].kind=='structural'"`

**S4 (R4, R10).** `src/deepreason/proof_debt.py` (NEW) | before: does not exist
| after: `file_derivation_manifest(harness, subject_ref, *, kernel_checks,
open_certificate_refs, axiom_debt, provenance)` registering the manifest
artifact; `KERNEL_CHECK` / `OPEN_CERTIFICATES` / `AXIOM_DEBT` as the three
itemization constants; `manifests_for(harness, subject_ref)`.
    accept: `python -m pytest tests/test_proof_debt.py -q` → 0 failed

**S5 (R10).** `src/deepreason/proof_debt.py` | after: `receipt(harness,
warrant_id)` → a frozen `Receipt` with `kernel_checks` (each RE-RUN now, not
read back), `open_certificates` (each with its CURRENT `Status`), `axiom_debt`,
and `standing: bool`. DERIVED: built on every call, never written.
    accept: `python -m pytest tests/test_proof_debt.py::test_a_receipt_is_recomputed_from_the_log_and_never_stored tests/test_proof_debt.py::test_a_receipt_reruns_its_kernel_checks_rather_than_reading_them_back -q`

**S6 (R10).** `src/deepreason/proof_debt.py` | after: replay determinism — a
root whose log contains a manifest, a certificate and an attack on the
certificate replays to identical labels and identical receipt content.
    accept: `python -m pytest tests/test_proof_debt.py::test_the_log_replays_identically_after_a_certificate_is_attacked -q`

**S7 (R4).** `src/deepreason/proof_debt.py` | after: recomputation, not
retroactivity — the labels BEFORE the certificate attack are re-derivable from
the prefix of the log, unchanged.
    accept: `python -m pytest tests/test_proof_debt.py::test_dependents_are_invalidated_on_recomputation_not_retroactively -q`

**S8 (R4, Q4/R58).** `src/deepreason/rules/warrants.py` | before:
`register_fail_warrant` builds ν from `nu_interface` alone | after: new keyword
`manifest_ref: str | None = None`; when given, ν's interface gains
`Ref(manifest_ref, RefRole.EVIDENCE)`, merged with any caller-supplied
`nu_interface` rather than replacing it. Default `None` — every existing call
site is byte-unchanged.
    accept: `python -m pytest tests/test_proof_debt.py::test_a_manifest_is_wired_to_the_validity_node_as_evidence -q`

**S9 (R4, Q4/R58).** R58's pinned regression, end to end: target refuted →
certificate attacked → ν attacked by the evidence closure → the critic loses →
the target is reinstated → replay identical.
    accept: `python -m pytest tests/test_proof_debt.py::test_attacking_a_manifest_item_disables_the_attack_before_pass_one -q`

**S10 (R4, R5).** `src/deepreason/premises.py` | before: `premise_rent_sweep`
records its sampled variants in a `trace_ref` BLOB, which is readable and not
attackable | after: when the verdict rests on the `load` sample, the sweep also
registers a sample-certificate artifact and a manifest naming it as the one
open certificate, with `demarcation.crit` as the kernel check and `A2`, `A10`
as the axiom debt; the manifest is passed as `manifest_ref`. The `trace_ref`
blob is UNCHANGED — the certificate is added beside it, not instead of it.
    accept: `python -m pytest tests/test_premise_channel.py tests/test_proof_debt.py::test_the_rent_sweep_files_a_manifest_whose_sample_is_attackable -q`

**S11 (R5, R6).** Every other `register_fail_warrant` site is unchanged.
    accept: `git diff --stat` at the D1 boundary shows no other call site edited; `python -m pytest tests/test_easy.py tests/test_evidence_view.py tests/test_scheduler.py tests/test_simulation_backend.py tests/test_workload_formal.py -q` → 0 failed

### D2 — Duhem localization

**S12 (R7, R8).** `src/deepreason/calculus/claims.py` | after: `LocalizationV1`
— `bundle_ref`, `member_ref`, `derivation_manifest_ref: str | None`. Added to
`_IMPLEMENTED`; `CLAIM_SCHEMAS` still 9. `derivation_manifest_ref` is where D1
and D2 meet: a localization is itself a derived judgment and may carry its own
bill.
    accept: `python -c "from deepreason.calculus.claims import _IMPLEMENTED; from deepreason.calculus import CLAIM_SCHEMAS; assert len(CLAIM_SCHEMAS)==9 and len(_IMPLEMENTED)==5"`

**S13 (R7, R8).** `src/deepreason/calculus/compiler.py` | after: `LocalizationV1`
→ `MENTION` on `bundle_ref`, `MENTION` on `member_ref`, `DEPENDENCE` on
`derivation_manifest_ref` when present. **Both endpoints are mentions, and that
is `premises.py`'s shape reused rather than re-derived (R8):** a localization
that DEPENDED on its bundle would be suspended by pass two exactly when the
bundle became problematic — erasing the relation that identifies the blame; a
localization that depended on its MEMBER would be suspended the moment the
member fell — un-implicating the member at the moment the implication mattered.
    accept: `python -m pytest tests/test_localization.py::test_a_localization_mentions_both_its_bundle_and_its_member_and_depends_on_neither -q`

**S14 (R7).** `src/deepreason/calculus/programs.py` +
`src/deepreason/programs.py` | after: `localization_wf` registered as
`"structural"`, with `LOCALIZATION_COMMITMENT`. Like `frame_assertion_wf`, it
names the mention law in its own verdict so a reader can tell a violated
separation from a botched registration.
    accept: `python -m pytest tests/test_localization.py::test_a_localization_that_depends_on_its_member_is_refused_by_name -q`

**S15 (R7, R8).** `src/deepreason/localization.py` (NEW) | after:
`file_localization(harness, bundle_ref, member_ref, *, manifest_ref,
provenance)`; `bundle_members(harness, bundle_id)` = the DEPENDENCE targets;
`standing_localizations(harness)` = the CONSULTED (i.e. `ACCEPTED`) ones,
mirroring `premises.standing_attributions`.
    accept: `python -m pytest tests/test_localization.py -q` → 0 failed

**S16 (R7, R9).** `src/deepreason/localization.py` | after: `implicated(harness)`
→ `{member_id: grade}`, DERIVED and never stored, mirroring
`premises.premise_orphaned`. A member is returned only when ALL THREE hold: a
localization naming it is CONSULTED, its bundle is PROBLEMATIC (`REFUTED` →
`BUNDLE_REFUTED`; `SUSPENDED_UNSUPPORTED` → `BUNDLE_UNACCREDITED`), and the
member is genuinely in `bundle_members(bundle)`.
    accept: `python -m pytest tests/test_localization.py::test_implication_needs_a_consulted_localization_a_problematic_bundle_and_real_membership -q`

**S17 (R9) — the two locks, which ARE the hard constraint.** Lock one: filing a
localization moves nothing on its own (bundle sound → no implication). Lock two:
a bundle becoming problematic moves nothing on its own (no localization → no
implication, however many members it has).
    accept: `python -m pytest tests/test_localization.py::test_a_localization_alone_implicates_nobody tests/test_localization.py::test_a_problematic_bundle_implicates_no_member_without_a_localization -q`

**S18 (R9).** A localization whose member is NOT a member of the named bundle
projects nothing — blame may not land outside the bundle. Checked in the
derived predicate rather than in the wf program, because the wf program is
handed `(text, budget, artifact)` and no harness state, so membership is not
visible to it. Recorded here so the placement is a decision, not an oversight.
    accept: `python -m pytest tests/test_localization.py::test_a_localization_cannot_blame_a_non_member -q`

**S19 (R11).** N1 at this layer: refuting the localization un-implicates the
member, and nothing is deleted — the refuted localization stays on the record.
    accept: `python -m pytest tests/test_localization.py::test_defeating_the_localization_unimplicates_the_member -q`

**S20 (R12).** No label moves from a receipt or a localization alone: filing
either changes no artifact's `Status`, and both modules' read paths hold no
call that could write one and do not import `adjudication` (the
`standing.py` precedent guard, §5).
    accept: `python -m pytest tests/test_proof_debt.py::test_filing_a_manifest_moves_no_label tests/test_localization.py::test_filing_a_localization_moves_no_label tests/test_localization.py::test_the_read_path_holds_no_call_that_could_write -q`

### Cross-cutting

**S21 (R13) — MUTATION PROOF.** In a scratch copy of the tree (never the repo),
`implicated()` is wired to project automatically: every member of a problematic
bundle implicated, no localization consulted. `test_a_problematic_bundle_implicates_no_member_without_a_localization`
must go RED. Restore; it must go GREEN. Both runs pasted into VALIDATION.md.
    accept: both pasted runs present in VALIDATION.md, RED then GREEN

**S22 (R14) — axiom ledger.** `docs/map/INV-axiom-basis.md` gains Rung D's row
in each affected axiom's Proved/Preserved columns. What this rung **PROVES**:
**A5** at a third site (the mention law, for localizations — a claim that
mentions but does not depend on its subject) and **A1**/**A2** in the specific
form R10 demands (a receipt is a pure fold, recomputed under a finite
deterministic budget). What it **PRESERVES**: **A3** (status is still the
grounded attack pass then the support pass — a receipt adds evidence refs, never
a label), **A8**-in-spirit and **A9** (a receipt and an implication act only
through attention — neither has a rule of its own), and **Ax 4.1** (Genesis
Inertness: neither `receipt()` nor `implicated()` reads provenance).
    accept: `python tools/docs_verify.py` → 0 failed; the Rung D rows present

**S23 (R18, map).** The map moves in the SAME commits: new
`docs/map/CON-proof-debt-and-localization.md` with executable `check:` lines;
`SUB-calculus.md`'s `_IMPLEMENTED == 3` check advanced to 5 and its `Owns:`
line extended; `CON-warrants-and-attacks.md` gains the manifest→ν EVIDENCE path;
`CON-problem-layer-lifecycle.md` gains the rent sweep's certificate;
`INDEX.md` gains the new concept row.
    accept: `python tools/docs_verify.py` (full) → no NEW failures vs C4's 3 pre-existing shallow-clone failures; `python tools/docs_verify.py --links` → 0 failed

**S24 (R19).** DELIVERY.md carries the R-by-R table with pasted proof and the
two closing lines.
    accept: DELIVERY.md exists with 19 rows and both closing lines

---

## Assumptions (operator may override)

- **A1 (Q1)** — scope is attack-producing derived judgments only; labels,
  measures and render decisions are out, each with its reason in §1. Assumed,
  operator may override.
- **A2 (Q2)** — the manifest is a registered artifact and the RECEIPT is the
  derived view; §2. Assumed, operator may override.
- **A3 (Q3)** — a bundle is an artifact that depends on its members; no new
  schema name, no bundle registry; §3. Assumed, operator may override.
- **A4 (Q5)** — the diff-budget ceiling is set below, from the itemization.
- **A5** — no `Config` knob is added by this rung. Nothing here is a dial: the
  channel is either present or absent, and R15's `_versioned_source_config_data`
  obligation therefore has nothing to attach to. Recorded so its absence is a
  decision, not a forgotten line.
- **A6** — D2 ships with NO scheduler, CLI or MCP consumer. C3 bounds the blast
  radius to "warrants/validity, a new localization module, and map docs", and a
  reader surface would move the MCP tool-set/schema-sha wheel-smoke pins. This
  is the same shape Rung 4 shipped in — `standing()` landed before its render
  consumer — and it is recorded as a KNOWN ABSENCE with a ready prompt in
  PARKED.md rather than as an oversight. E28 (a mechanism nobody triggers) is
  answered for D1 by a live producer in `premise_rent_sweep`, and for D2 by the
  gate exercising the whole channel including the mutation proof.

## Questions for operator (STOP if non-empty)

**Empty.** Every candidate question was routed through
`dr-ask-the-right-question` and answered by the cheapest authority available:
Q1 by the ladder's own execution table plus `ERRATA` E28 (the record); Q2 by
C4's derived-never-stored discipline (the framework); Q3 by `dep`'s existing
semantics (the code); Q4 by the v2 REQUEST.md's own R58 ledger row (the
record); Q5 by the itemization below; Q6 by `standing.py`'s precedent guard
(the code). None survived the dominance test, so none is spent on the operator.

## Out of scope (explicit)

- A `poietic.bundle.v1` schema or any bundle registry — not requested, and §3
  shows it is not needed.
- Receipts for labels, measures or render decisions — §1, not requested at this
  scope.
- A CLI/MCP/scheduler reader for `implicated()` or `receipt()` — not requested;
  parked with a ready prompt (A6).
- Teaching `verify_root` about manifests or localizations — not requested, and
  it would be frozen-surface contact for no stated requirement.
- Producers for the four still-unbuilt claim names (`reach-certificate`,
  `problem-retirement`, `problem-translation`, `succession`) — not requested;
  `succession` belongs to Rung 5 by LADDER.md §5.

## Frozen-surface contact forecast

**none expected — and computed, not hand-checked.** `tools/blast_radius.py`,
run over every planned target file and symbol, verbatim:

    "frozen_surface_contacts": [],
    "frozen_adjacent_contacts": [],
    "frozen_surface_verdict": "CLEAR"

    "disclosure_summary": "This change touches none of the five frozen
    surfaces. 4 test file(s) and 10 map document(s) assert on the touched
    targets today. ..."

No grant is requested under R15: the receipt design wants no
verification-format contact, because R10 is proved by tests over replayed
state, not by teaching `verify_root` a new record shape. `adjudication/edges.py`
is NOT edited — §0 measured that the EVIDENCE closure already exists.

`reachability` reported `CLAIM_SCHEMAS` as `UNKNOWN`, so the manual grep
cross-check the skill requires for exactly that case was run; its hits are
classified in the census below.

## Blast-radius census

From the same `blast_radius.py` run (`consumers.tests`, `consumers.map_checks`),
every hit classified. No hit omitted.

**Tests**

| target | hits | classification |
|---|---|---|
| `register_fail_warrant` | `test_easy.py:332,333`, `test_evidence_view.py:171,177`, `test_scheduler.py:155,156`, `test_simulation_backend.py:10,125`, `test_workload_formal.py:16,222` | **MUST NOT MOVE** — S8 adds a keyword defaulting to `None`; every existing call is byte-unchanged |
| `premise_rent_sweep` | `test_calculus_frame_separation.py:124`, `test_premise_channel.py:31,393,405,408,425,449` | **EXPECTED TO MOVE (counts only)** — S10 makes the sweep register two more artifacts on the sampled path. Any assertion counting artifacts or asserting a critic's ν has no refs moves; assertions on the sweep's VERDICTS must not. Predicted precisely because rung 4's and rung 5's specs each predicted too narrowly here (PARKED P6) |
| `compile_interface` | `test_calculus_claim_substrate.py:18,102,115,174`, `test_calculus_frame_assertions.py:24,141,151,180`, `test_reflexive_discipline.py:80,339,367`, `test_relapse_domains.py:15,166`, `test_review_fixes.py:475`, `test_runtime_workload_integration.py:25,140` | **MUST NOT MOVE** — S2/S13 add two `isinstance` branches ahead of the existing raise; no existing body's compilation changes |
| `CLAIM_SCHEMAS` | `test_calculus_claim_substrate.py:14,65`, `test_calculus_frame_assertions.py:190,192,193` | **MUST NOT MOVE** — `len == 9` is the property this rung preserves. `:65` uses `poietic.succession.v1`, which stays unbuilt, so `claim-schema-not-implemented` still fires there |

Manual cross-check for the `UNKNOWN` symbol (`grep -rn "CLAIM_SCHEMAS" tests/
docs/map/ src/`) added no test hit beyond the four rows above and no map hit
beyond the two below.

**Map documents**

| target | hits | classification |
|---|---|---|
| `SUB-calculus.md:38` (`len(_IMPLEMENTED) == 3`) | 1 | **EXPECTED TO MOVE** → 5, in the same commit as S1/S12 |
| `SUB-calculus.md:17` (`len(CLAIM_SCHEMAS) == 9`) | 1 | **MUST NOT MOVE** |
| `SUB-calculus.md:4` (`Owns:`), `:124,155,182,184,189` | 6 | **EXPECTED TO MOVE** — `Owns:` extended; prose gains the two producers |
| `CON-warrants-and-attacks.md:4,32–35,54,88,91,197` | 9 | **EXPECTED TO MOVE** — the manifest→ν EVIDENCE path is this document's subject |
| `CON-problem-layer-lifecycle.md:4,63,109` | 3 | **EXPECTED TO MOVE** — the rent sweep's certificate |
| `INV-axiom-basis.md:108,110,112` | 3 | **EXPECTED TO MOVE** — S22's ledger rows |
| `SEAM-adjudication-x-rules.md`, `SEAM-evaluation-x-rules.md`, `SEAM-evaluation-x-ontology.md`, `SEAM-capabilities-x-rules.md`, `SEAM-llm-x-rules.md`, `SEAM-rules-x-scratch.md`, `SEAM-scheduler-x-rules.md`, `SEAM-rules-x-workflow.md`, `SEAM-ontology-x-rules.md`, `SUB-rules.md`, `SUB-evaluation.md`, `SUB-periphery.md`, `CON-conjecture-kinds.md`, `CON-conjecture-source.md`, `CON-criticism-source.md`, `SEAM-adjudication-x-authority.md` | all remaining | **MUST NOT MOVE** — they assert on `register_fail_warrant`'s existing behaviour, which S8 leaves default-unchanged |

`qualification_digest: []` and `wheel_smoke_pins: []` — no public-surface pin
moves (A6 is what keeps that true).

## Record-observable guardrails

The manifest and the localization are ordinary artifacts, not new record types,
new event kinds, or new fields on an existing typed record. No absence-tolerant
reader is needed and no root-sweep probe is proposed: the sweep is RETIRED as an
instrument (operator ruling 2026-08-22, CLAUDE.md), and there is no new typed
observable for one to look at. Proof of the new behaviour is targeted,
mutation-proven regression tests (S21) on fixtures, which CLAUDE.md names as
both cheaper and stronger.

## Budget

Itemized, then summed by machine:

| item | lines |
|---|---|
| S1/S12 `calculus/claims.py` | 80 |
| S2/S13 `calculus/compiler.py` | 45 |
| S3/S14 `calculus/programs.py` | 45 |
| S3/S14 `programs.py` (registration) | 20 |
| S1/S12 `calculus/__init__.py` (exports) | 15 |
| S4–S7 `proof_debt.py` (new) | 200 |
| S15–S19 `localization.py` (new) | 190 |
| S8 `rules/warrants.py` | 30 |
| S10 `premises.py` | 45 |
| **src subtotal** | **670** |
| `tests/test_proof_debt.py` | 280 |
| `tests/test_localization.py` | 300 |
| **tests subtotal** | **580** |
| `docs/map/CON-proof-debt-and-localization.md` (new) | 140 |
| map edits (SUB-calculus, CON-warrants, CON-problem-layer, INV-axiom-basis, INDEX) | 90 |
| **docs subtotal** | **230** |

    $ python3 -c "src=[80,45,45,20,15,200,190,30,45]; tests=[280,300]; docs=[140,90]; print('src',sum(src),'tests',sum(tests),'docs',sum(docs),'TOTAL',sum(src)+sum(tests)+sum(docs))"
    src 670 tests 580 docs 230 TOTAL 1480

**Ceiling: 1480 insertions (R16, Q5/A4).** Checked at every `[COMMIT]` step with
`python tools/diff_budget.py e1ea05e82 --ceiling 1480 --paths src tests docs`.
STOP if exceeded.

**On the >300-line split rule:** D1 and D2 are ordered SUB-DELIVERIES inside one
tranche, not one sprawl — the checklist runs D1 to a committed, green boundary
(S1–S11) before D2 begins (S12–S20). R17's fork does not fire: §0 measured that
both names and one of the two compiler refs already exist, which is why the
combined rung fits where an ontology-growing version would not. If the D1
boundary overruns the ceiling, R17's fork fires there and D1 is what gets
parked — the operator's instruction says deliver D2 and park D1, and the
checklist orders D1 first only because D2 reuses its manifest ref.

6 commits: D1-tests, D1-code+map, D1-boundary-gate, D2-tests, D2-code+map,
validation.

Frozen surfaces touched: **none** (computed, `frozen_surface_verdict: CLEAR`).

---

Rubric: 6/6 yes — every R (R1–R19) has a spec item or a process item with a
machine-decidable accept; blast-radius census pasted from the tool and every hit
classified, with the manual grep run for the one `UNKNOWN` symbol;
frozen-surface forecast recorded with the tool's own verbatim list; every
mechanism the request names traced to code it actually reaches (`premises.py`'s
mention-law shape → S13; warrants' validity node → S8, measured against
`edges.py`'s existing EVIDENCE closure in §0); not a DESIGN-AND-STOP request, so
those two sections are the §0–§5 measurements instead; nothing in this spec
untraceable to an R or C number.
