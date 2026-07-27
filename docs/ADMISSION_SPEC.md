# Evidence Admission (draft for review)

Status: DRAFT v0.1 — for owner review before any implementation.
Scope: how a body of user-supplied input (a study, a book, a dataset, a
mixed corpus) becomes durable material a DeepReason run may reason over.

This subsystem is named **admission**: documents are admitted into
evidence with provenance, or refused with a typed reason. Nothing enters
silently.

## 1. Why admission needs its own spec

The evidence dossier digest participates in frozen run identity
(`RunInputManifestV2.evidence_dossier_digest` and the preparation request
digest). Whatever produces that digest therefore mints canonical
authority, the same class of act as manifest compilation. Three
obligations follow:

1. **Determinism.** The same input bytes MUST produce the same dossier
   digest on every machine, forever. The parser is a pure function of
   its inputs and its own declared version.
2. **Boundary discipline.** Admitted content divides into material that
   may ground adjudication and material that may only advise. That
   division is normative, not stylistic.
3. **Adversarial posture.** Admitted text is untrusted input that will
   condition models. It is data, never instructions.

## 2. Vocabulary

- **Source**: one input artifact as supplied (a PDF file, a CSV file, a
  directory of markdown). Identified by the sha256 of its raw bytes.
- **Admission block**: one canonical, content-addressed unit extracted
  from a source (a section, a paragraph run, a table, a schema summary),
  carrying an exact span reference into the source bytes.
- **Dossier**: the frozen `EvidenceDossierV1` binding a problem to a set
  of sources and their admission blocks. Addressed by digest; immutable.
- **Tier**: where a block's content is allowed to act:
  - `evidence` — citable by conjectures; attackable by critics;
    participates in evidence invalidation (`att` construction).
  - `workshop` — mirrored into the scratchpad under the existing
    `advisory_non_grounding` boundary; retrievable, never grounding.
  - `memory` — optionally ingested into a brain store for cross-run
    advisory reuse. Never run-canonical.

## 3. The admission pipeline

Stages are strictly ordered; every stage is deterministic.

1. **Fingerprint.** Hash raw bytes; record byte count, media type by
   content sniffing (never by filename alone), and supplied provenance
   (`AttachedSourceProvenanceV1`: who supplied it, acquisition method,
   note).
2. **Extract.** A format adapter converts the source into normalized
   UTF-8 text plus a span map back to source bytes (or, for datasets,
   into a schema/statistics projection — §6). Text formats (plain
   text, markdown, CSV/TSV) are handled by the core parser natively;
   every other format is handled by a plugin adapter under the
   adapter contract (§3a). Adapters MUST be pure: no network, no
   clock, no environment reads — enforced, not attested (§3a.2).
3. **Segment.** Chunk by structure (headings, paragraph boundaries,
   table boundaries, row groups), bounded by per-block byte ceilings.
   Segmentation parameters are frozen constants of the parser version.
4. **Mint blocks.** Each block gets a content-addressed id over
   (parser version, source digest, span, normalized text, kind).
5. **Compile dossier.** Blocks + sources + provenance + parser version
   → `EvidenceDossierV1`; print the dossier digest. The dossier is
   stored under managed state, never inside a run root; runs reference
   it by digest.

**No model in the canonical path.** LLM-assisted enrichment (summaries,
claim extraction, table narration) is permitted only as a separate,
clearly derived layer that lands in the `workshop` tier with
`derived_from` provenance. Derived material MUST Not be able to enter
the `evidence` tier.

### 3a. The adapter contract (plugins)

Non-text formats are admitted through plugin adapters. The contract is
strict because adapters mint canonical authority:

1. **Version-bound identity.** Every adapter declares `adapter_id` and
   `adapter_version`; both bind into the dossier per-source alongside
   the core `parser_version`. A different adapter or version mints a
   different dossier digest. Inspecting or reproducing a dossier
   without the recorded adapter version is a typed refusal
   (`ADMISSION_ADAPTER_VERSION_UNAVAILABLE`), never silent divergence.
2. **Sandboxed execution.** Adapters run in the harness's existing
   sandboxed subprocess regime (seccomp, no network, resource limits):
   raw bytes in, normalized text + span map (or dataset projection)
   out, over a closed wire schema. Purity is enforced by the sandbox,
   not promised by documentation.
3. **Span fidelity gates tier eligibility.** The `evidence` tier
   requires byte-span-verifiable extraction — that is what makes
   quotes checkable and citations attackable. An adapter declares its
   span fidelity class (`exact_spans`, `approximate`, `none`); blocks
   from adapters below `exact_spans` are capped at the `workshop`
   tier. Strict by default, degradable with the degradation recorded.
4. **Declared registration.** Adapters register through the
   `deepreason.admission.adapters` entry-point group with a
   closed-schema adapter manifest: claimed media types (by content
   signature, not extension), version, span fidelity class, bounded
   output ceilings. An unadmittable format is a typed refusal naming
   the adapter that would handle it.
5. **First-party adapters use the same contract.** PDF and EPUB
   support ship as first-party plugins behind the `admit` extra, going
   through the identical registration, sandbox, and version-binding
   path as third-party adapters. The interface's first consumer is the
   project itself.

### Parser version binding

Every dossier records `parser_version` (a single monotonic identifier
covering all adapters and segmentation constants). Replaying or reusing
a dossier never re-parses; the dossier is the frozen artifact. A new
parser version admits the same source to a NEW dossier digest. Two
parser versions never share a digest — improvement is never silent
mutation.

## 4. Citation and grounding contract

- A conjecture citing admitted evidence MUST reference block ids (never
  free-text quotes alone). The wire contract gains an optional
  `evidence_refs` field bounded per candidate.
- The verifier byte-checks any quoted span against the referenced
  block's canonical text; a mismatched quote is a finding
  (`EVIDENCE_QUOTE_MISMATCH`), and criticism may attack the citation
  itself.
- Evidence invalidation composes with the existing closure rules: an
  accepted attack on a block's fidelity (e.g. an extraction-error
  finding) invalidates warrants that relied on it, exactly as the
  existing `evidence` closure lifts invalidation into `att`.
- Coverage: dossier blocks feed the scratch channel ladder's
  `coverage`/`underexposed` slots so criticism can ask what the rest of
  the corpus says. Budget arithmetic (§7) keeps this bounded.

## 5. Injection posture (normative)

- Admitted text reaches prompts only inside the closed wire envelopes,
  framed as quoted data. It is never concatenated into instruction
  positions, role text, or policy text.
- Rubric-bearing or predicate-bearing content inside admitted text has
  no special status: the existing skeleton contract rejection of inline
  `predicate:` expressions applies to document-derived strings
  identically.
- A model output that appears to obey document-embedded instructions is
  a semantic-admission concern for critics, not a parser concern; the
  parser's job ends at faithful, framed extraction.
- Source names and paths never enter prompts; blocks are referenced by
  id, titled by extracted headings only.

## 6. Dataset admission

Prose tells; datasets can be interrogated. For tabular sources (CSV,
TSV, Parquet behind an extra):

- Admitted blocks are: a schema block (columns, dtypes, null counts), a
  bounded statistics block per column (deterministic summary stats),
  and stratified sample blocks (seeded, deterministic sampling).
- The full dataset is retained as a managed sidecar addressed by source
  digest — not as blocks — and exposed ONLY through the existing
  sandboxed oracle: model-authored claims about the data compile to
  bounded `program:` checks (the existing check machinery) executed
  against the sidecar under the same seccomp/no-network regime.
- This makes claims about data falsifiable rather than argued: a
  conjecture asserting a correlation carries a falsification commitment
  a critic can run.

## 7. Budgets and limits (frozen in the dossier)

- Per-source and total byte ceilings; per-block ceilings; block-count
  ceilings. Refusal on breach is typed (`ADMISSION_SOURCE_TOO_LARGE`,
  `ADMISSION_BLOCK_BUDGET_EXCEEDED`) — never silent truncation. Partial
  admission requires an explicit `--allow-partial` acknowledgment
  recorded in provenance.
- A run's context never assumes the whole corpus fits: retrieval-based
  exposure (initial blocks + expansions under the engaged context
  policy) is the only path to prompts.

## 8. Fidelity floors

- Extraction confidence is recorded per block (e.g. PDF text layer
  present vs OCR-quality heuristics). Blocks below the floor are
  refused (typed), not admitted degraded; the refusal names the spans
  so the user can supply a better source.
- Refusals are per-source where possible: one unreadable appendix does
  not sink a corpus, but its absence is recorded in the dossier.

## 9. CLI surface

    deepreason admit STUDY.pdf data.csv notes/ --problem "..."
      → prints dossier digest + admission report (blocks, tiers,
        refusals)
    deepreason reason "question" --dossier sha256:...
      → binds the dossier into preparation; the dossier digest joins
        the request identity
    deepreason admit --inspect sha256:...
      → lists sources, blocks, tiers, refusals for a stored dossier

Ingest-first is the primary flow (parse once, reason many). A
convenience `reason --attach FILE` MAY wrap admit+reason in one step
but MUST print the minted dossier digest so the run is reproducible.

## 10. Wheel and dependency policy

Core wheel stays pydantic+pyyaml. Format adapters beyond plain
text/markdown/CSV live behind an extra (`deepreason[admit]`), and a
missing adapter is a typed refusal naming the extra — the graceful
`toolchain_missing` pattern, not a crash.

## 11. Decisions (owner-resolved 2026-07-27)

1. **v1 format set — DECIDED.** Text formats (plain text, markdown,
   CSV/TSV) are handled by the core parser natively. All other
   formats go through plugin adapters under the §3a contract; PDF and
   EPUB ship as first-party plugins behind the `admit` extra.
   Images/OCR deferred (and would enter as a `none`/`approximate`
   span-fidelity adapter, workshop-capped, when they do).
2. **Dataset oracle in v1 — DECIDED: yes.** CSV/TSV sidecar +
   program-check interface (§6), bounded to declarative checks.
3. **Evidence-tier default — DECIDED.** User-supplied sources admit
   as `evidence` by default (subject to §3a.3 span fidelity);
   anything derived admits as `workshop`.
4. **Amendment placement — DECIDED.** Standalone spec now; a harness
   spec amendment references it later (alongside the four catalogued
   v1.7 items).
