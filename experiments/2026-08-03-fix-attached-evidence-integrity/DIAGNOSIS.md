# Diagnosis: the `attached-evidence` candidate set is selected by `mention` alone, so any later artifact citing the source record breaks the check

Verdict: **R** (reader over-demands). GOAL.md's alternative W is ruled out below.

Primary cause: `verify_root` identifies "the reliability-dependent candidate
evidence artifact" for a bound source as *every artifact in the materialized
state carrying a `mention` ref to that source's source-record artifact*, then
demands the set have exactly one member
(`invariants.py:2156-2171`). But `mention -> source_record` is not a
discriminating predicate for that artifact — it is the ordinary way ANY artifact
cites attached evidence. The writer
(`evidence/render.py:113-164`) registers a fixed
import-time triple per source: the source record, an attackable
`source-reliability` claim, and the candidate evidence artifact whose interface
is exactly `[dependence -> reliability, mention -> source_record]`. The moment a
cycle-time artifact also mentions the source record — a conjecture citing the
evidence it was given, which is the system working as intended — the set has two
members, `len(candidates) != 1` fires, and the run's own record is declared
invalid. The detail text then asserts the opposite of the truth: it says the
source *lacks* a reliability-dependent candidate evidence artifact when that
artifact exists, is well-formed, and is sitting in the set that was rejected for
being too large.

Evidence:

- `experiments/2026-08-02-stress-triplet/home-triage/runs/run-0a3e93d6e8031e2e6d1d21dde2fa93cc`,
  artifacts by provenance (read-only `Harness`, materialized state):
      seq  2  6f33b9f0  role=IMPORT       refs=[]                                  <- source record
      seq  3  9319c0bc  role=IMPORT       refs=[]                                  <- source-reliability claim
      seq  4  b6006b31  role=IMPORT       refs=[dependence->9319c0bc, mention->6f33b9f0]   <- candidate evidence
      seq 43  b1752fe9  role=CONJECTURER  refs=[mention->6f33b9f0]                  <- the model citing its evidence
  The check's candidate set for `src-56d86e9b...` is `{b6006b31, b1752fe9}` —
  size 2. The artifact the finding claims is missing is `b6006b31`.
- `b1752fe9`'s content is a conjecture, not an evidence import:
  `"Test #1: a direct assertion that the append-only record's _reset() guard
  fires on a failed control append..."`. It is a legitimate cycle-time product
  carrying one `mention`, and nothing else about it is irregular.
- The same run's OTHER bound source passes: `src-a281e468...` has candidate set
  size 1 (`5b84cff5`, `dependence`+`mention`), because no conjecture happened to
  cite it. One root, one code path, two sources, opposite verdicts — decided
  entirely by whether the model cited the source.
- Sibling roots agree. `home-orbit/runs/run-6472629d...`: one bound source,
  candidate set size 1, `valid=true`.
  `home-workshop/runs/run-1a0d4168...`: no attached sources, `valid=true`.
  Both are in the same triplet and the same ladder. The variable that separates
  the invalid root from the valid ones is the downstream citation, not anything
  about how evidence was bound.
- `REPLAY_VALIDATION.json` reports exactly one violation and it is this one, so
  nothing else about the root is in dispute.

Implicated code:

- `src/deepreason/invariants.py:2156-2163` — the candidate set comprehension,
  filtered on `ref.target == record_ref and ref.role == "mention"` only.
- `src/deepreason/invariants.py:2164-2171` — the `len(candidates) != 1` demand
  and the misleading detail string.
- `src/deepreason/evidence/render.py:146-159` — the writer, which is CORRECT and
  is the source of the discriminating shape the reader should have used. Named
  for reference; this tranche does not change it.

Falsifiable prediction (what `dr-reproduce` must show):

    Build a minimal root: register a problem, bind a one-source dossier,
    call attach_bound_evidence.
      python -c "... verify_root(root)['violations']"
      -> []   (no attached-evidence finding; the triple alone is accepted)

    Then create ONE further artifact with
    Interface(refs=[Ref(target=<source_record_id>, role="mention")]).
      -> exactly one violation:
         check  = "attached-evidence"
         detail = "bound source <id> lacks one reliability-dependent
                   candidate evidence artifact"

    Deleting nothing and adding nothing else, that second artifact is the
    whole cause. If verify_root stays clean after it is added, this
    diagnosis is wrong.

Ruled out: **W**, that the write path bound a source without attaching its
required artifact. The artifact exists and satisfies the contract in full —
`b6006b31` at seq 4, provenance role `import`, `dependence` to the
`source-reliability` claim, `mention` to the source record, and
`content_ref` equal to the source's own content digest
(`56d86e9b3a1d59413e02c76cdf675f84f6288fa7aea8b9fee7ab47668ed94040`). That is
byte-for-byte the shape `attach_bound_evidence` constructs. There is nothing for
the writer to fix, and no version of W survives the seq-4 artifact's existence.

Note for `dr-propose-fix` (mechanism only, not a design): the `!= 1` demand does
catch a real fault — a writer that registered two candidate evidence artifacts
for one source — so the fix must narrow the candidate PREDICATE without dropping
the uniqueness demand. The writer supplies at least two discriminators the
reader currently ignores: `provenance.role == "import"`, and the presence of the
`dependence` ref (which the check already tests, but only after it has counted).

Documentation consequence (operator-granted scope, see GOAL.md): this is a NEW
failure mode, not a recurrence of any recorded trap. `DR-SUB-verification` and
`DR-SEAM-harness-x-verification` gain a Traps entry in the fix commit.
