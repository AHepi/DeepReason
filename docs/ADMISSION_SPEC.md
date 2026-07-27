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
   into a schema/statistics projection — §6). Adapters MUST be pure:
   no network, no clock, no environment reads.
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

## 11. Open decisions (owner)

1. **v1 format set.** Proposal: text, markdown, CSV/TSV in core; PDF
   and EPUB behind the `admit` extra; images/OCR deferred.
2. **Dataset oracle in v1?** The sidecar+program-check interface (§6)
   is the differentiating feature but is the largest single piece.
   Proposal: yes for CSV/TSV, bounded to declarative checks.
3. **Evidence-tier default.** Admit prose blocks as `evidence` by
   default, or as `workshop` with explicit `--evidence` promotion?
   Proposal: evidence by default for user-supplied sources (they chose
   to supply them), workshop for anything derived.
4. **Amendment placement.** Ship as this standalone spec, or fold into
   the harness spec as a numbered amendment (with the four v1.7 items
   already catalogued)? Proposal: standalone now, amendment reference
   later.
