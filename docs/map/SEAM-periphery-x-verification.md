<!-- DR-SEAM-periphery-x-verification -->
Verified-at: df0fd0fd
Verify: python -m pytest tests/test_attached_evidence_citation.py tests/test_evidence_dossier_replay.py -q
Owns: src/deepreason/evidence/render.py, src/deepreason/evidence/state.py
Sides: DR-SUB-periphery, DR-SUB-verification
Sweep: "attached-source-record\.v1" && attach_bound_evidence|source_records|candidate|dossier

# periphery x verification

## The agreement

The evidence machinery (periphery) and replay validation (verification) agree
on one durable shape: for every source bound into a run's identity, the writer
registers an import-time triple, and the reader later re-derives that triple
from materialized state alone. `attach_bound_evidence` creates, per source and
before any cycle work: a **source record** (`attached-source-record.v1`
inline JSON binding the run-input digest, the dossier digest, and the source's
own payload), an attackable **source-reliability claim**, and one **candidate
evidence artifact** whose interface is exactly `[dependence -> reliability,
mention -> source_record]` — all three with `import` provenance, which
rule-driven (model-shaped) creation can never carry. `verify_root`'s
`attached-evidence` findings demand the mirror image: a unique source record
per bound source, arrived before the epoch's first LLM call and byte-equal to
its dossier entry, and **exactly one import-role artifact mentioning that
record and carrying a dependence ref**. Neither side imports a second
implementation of the other: the reader re-derives from `h.state.artifacts`,
never from the writer's return value.

The writer stamps the triple with import provenance, in the shape the reader
demands.
`check: grep -q "def attach_bound_evidence(" src/deepreason/evidence/render.py && grep -q 'Ref(target=reliability.id, role="dependence")' src/deepreason/evidence/render.py && grep -q 'Ref(target=source_record.id, role="mention")' src/deepreason/evidence/render.py && test "$(grep -c 'role="import"' src/deepreason/evidence/render.py)" -eq 3`

The reader's candidate predicate includes the import discriminator, and there
is exactly one such comprehension.
`check: python -c "import ast,pathlib;q=chr(39);T=ast.parse(pathlib.Path('src/deepreason/invariants.py').read_text());L=[n for n in ast.walk(T) if isinstance(n,ast.ListComp) and 'record_ref' in ast.unparse(n)];assert len(L)==1,len(L);s=ast.unparse(L[0]);assert ('artifact.provenance.role == '+q+'import'+q) in s and ('ref.role == '+q+'mention'+q) in s,s"`

The uniqueness and dependence demands sit downstream of that predicate and
survive it: a writer fault (two candidates, or a candidate that lost its
reliability dependence) is still a finding.
`check: grep -q "if len(candidates) != 1 or not any(" src/deepreason/invariants.py && grep -q 'ref.role == "dependence"' src/deepreason/invariants.py`

The whole agreement is pinned behaviourally — a citing conjecture leaves the
root valid, the committed defect root verifies clean, and a duplicate import
candidate still fails.
`check: python -m pytest tests/test_attached_evidence_citation.py -q`

## Where it is expressed

| Site | File | Symbol | What it enforces |
|---|---|---|---|
| The triple, written once | `evidence/render.py` | `attach_bound_evidence` | one record + one reliability claim + one candidate per source, import provenance, registered at binding time |
| Record identity | `evidence/render.py` | `source_record_content` | the record binds `run_input_digest`, `dossier_digest`, and the source payload byte-for-byte |
| Run-input binding | `evidence/state.py` | `bind_run_input` / `verify_run_input` / `load_run_input` | the digests both sides compare |
| Record window | `invariants.py` | the per-epoch fence-window loop in `verify_root` | records arrive before the epoch's first LLM seq, match their dossier, are unique per source |
| Candidate demand | `invariants.py` | the `candidates` comprehension after `source_records` | exactly one import-role, dependence-bearing candidate per bound source |
| Audit projection | `capabilities/audit.py` | the `RESEARCH_SOURCE_AUDIT.md` source listing | reporting only — it lists record artifacts by schema tag and belongs to `DR-SUB-capabilities`, not to this agreement |

## Why the coupling metric never saw this seam

Every `deepreason.evidence` import in `invariants.py` is function-local (the
same cycle-breaking idiom `DR-SEAM-harness-x-verification` documents for the
harness), so the measured import matrix shows zero traffic between the two
packages and `INDEX.md` carried no row for the pair. The agreement was real
the whole time — which is exactly the class of seam `INDEX.md` warns needs a
written document because no metric will ever surface it.
`check: python -c "import ast,pathlib;T=ast.parse(pathlib.Path('src/deepreason/invariants.py').read_text());top=[n for n in T.body if isinstance(n,(ast.Import,ast.ImportFrom))];assert not any('evidence' in (getattr(n,'module','') or '') for n in top),'module-level evidence import appeared';inner=[n for n in ast.walk(T) if isinstance(n,ast.ImportFrom) and (n.module or '').startswith('deepreason.evidence')];assert len(inner)>=2,len(inner)"`

## What is deliberately absent

**The verifier never judges reliability or truth.** The reliability claim is
an ordinary attackable artifact; the record's own text says attachment
establishes neither reliability nor truth. A valid root means the triple is
intact, not that the evidence is good — "accepted does not mean true" applies
to attached evidence twice over.
`check: grep -q "does not establish source reliability or factual truth" src/deepreason/evidence/render.py && grep -q "attachment does not establish it" src/deepreason/evidence/render.py`

**The writer never consults the verifier.** Same asymmetry as the harness
seam, same reason: a verifier bug must produce a wrong finding, never
suppressed evidence.
`check: grep -q "def attach_bound_evidence(" src/deepreason/evidence/render.py && ! grep -rE "deepreason\.(invariants|verification)|from \.\.(invariants|verification)" src/deepreason/evidence/`

**Citation confers nothing.** A `mention` ref to a source record from any
non-import artifact is invisible to the `attached-evidence` check — it is how
the model cites what it was given, it creates no support (the ontology already
says mention is non-grounding), and since 2026-08-03 it no longer creates
candidacy either. See Traps.

## How to change it

1. Both ends are constrained: the reader is frozen surface 3
   (`DR-INV-frozen-surfaces` — the `attached-evidence` NAME and the return
   shape are compared across recorded roots) and the writer's output becomes
   part of every future root's bytes. READERS may be fixed; FORMATS may not.
2. Reader before writer, as everywhere on the record: a new field on the
   record or the triple gets a defaulted reader that decides what ABSENCE
   means for old roots, then a writer that emits it.
3. Any new "exactly one artifact shaped like X" demand must key on a
   discriminator the model cannot emit (provenance role, not interface
   shape). That is the lesson of the one defect recorded here.
4. Run the 45-root sweep (`tools/root_sweep.py`) before and after; no root's
   `valid` may move except one a FIX.md predicted.

## Traps

- **A candidate predicate keyed on citation shape selects citations.** Until
  2026-08-03 the reader built its candidate set from `mention -> record`
  alone and demanded size 1, so the first live run whose conjecture cited its
  own attached evidence — stress-triplet
  `run-0a3e93d6e8031e2e6d1d21dde2fa93cc`, completed, rc=5 — was invalidated
  by the citation while the true candidate sat two seqs from the record. The
  finding's detail ("lacks one reliability-dependent candidate evidence
  artifact") named an artifact that existed. Fixed in tranche
  `experiments/2026-08-03-fix-attached-evidence-integrity` by narrowing the
  predicate to import provenance; the detail string kept its exact spelling
  (frozen format), and under the narrowed predicate it is now truthful.
`check: grep -q "Regression (stress-triplet run-0a3e93d6)" tests/test_attached_evidence_citation.py && grep -q "stress-triplet run-0a3e93d6" src/deepreason/invariants.py`
