<!-- DR-INV-seat-section-sources -->
Verified-at: 6f9b5614e
Verify: python -m pytest tests/test_seat_section_sources.py tests/test_conj_pack_legacy_golden.py -q
Owns: src/deepreason/seat_sources/registry.py, src/deepreason/seat_sources/shipped.py
Seams: DR-SEAM-packs-and-token-economy-x-rules

# Seat section sources — where a section's content comes from

## What it is

`DR-INV-seat-section-plugins` owns how a brief section is FORMATTED. This
document owns where its content comes from.

The two are separate because a plugin may not call the harness. Nine of the
conjecturer's twenty section slots need the record to exist at all — a dossier
receipt, a fence sequence, a work order, the open-criticism view — so until
2026-09-04 those nine were computed inside `rules/conj.py` and handed to the
renderer as strings. That left the generation side reaching into the admission
code for exactly the sections that carry evidence, which is the boundary the
seat-is-a-shell law's stated purpose — "slowly separate the authority layer" —
is aimed at.

A SOURCE closes it. A source reads the state and the record, computes one
value, appends nothing, and hands the value to the plugin that formats it. It
is registered and versioned exactly as a plugin is, and a seat's SOURCE BUNDLE
is selected by id exactly as its layout is.

## Not in `llm/`, and the reason is a law that predates this layer

`DR-SUB-llm` forbids `llm/` from importing the harness, the scheduler, the
rules, the adjudicator or the amendment machinery, so that a transport bug
cannot become an adjudication bug. A source READS the record, so a source
inside `llm/` would invert that arrow on its first line. The package therefore
sits beside `llm/` rather than inside it: `seat_sources` imports `llm` for the
allocated-pack marker and the menu renderer, and nothing in `llm/` imports
`seat_sources`.
`check: python -c "
import ast, pathlib
for path in pathlib.Path('src/deepreason/llm').rglob('*.py'):
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.ImportFrom):
            assert not (node.module or '').startswith('deepreason.seat_sources'), path
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith('deepreason.seat_sources'), path
found = [p.name for p in pathlib.Path('src/deepreason/seat_sources').rglob('*.py')
         for n in ast.walk(ast.parse(p.read_text()))
         if isinstance(n, ast.ImportFrom) and (n.module or '').startswith('deepreason.llm')]
assert found, 'the arrow points nowhere; this check would pass over an empty package'
"`

## The contract

**READ.** A source may read the log, the state, the blobs, the run root, the
manifest, the config, and whatever call-local state the caller hands over.
Reading the record is not a contact with any frozen surface, and forbidding it
would not make this layer purer — it would make it empty, and leave the
computation where this tranche found it.

**NEVER APPEND.** After any source runs, the run's next event sequence, the
bytes of `log.jsonl`, and the state's status map are unchanged. Measured across
every registered source, with a planted write that turns the measurement red;
and asserted statically as well, because the frozen-evidence source needs a
full v6 run to resolve at all and the dynamic drive cannot reach it.
`check: python -m pytest tests/test_seat_section_sources.py -q`

**ONE DECLARED WRITE.** Content-addressed blob materialisation, and only by a
source declaring `writes_blobs = True`. `pack_dossier` must materialise the
excerpts it selected before its receipt can name them, so the frozen-evidence
value cannot exist without it. A blob put is keyed by the hash of its own
bytes, is idempotent, appends no event, assigns no epistemic status and moves
no digest. Exactly one source declares it, and a source that writes without
declaring fails the check above.

**THE RECEIPT DOES NOT REACH THE RECORD.** `SectionSourceReceiptV1` is
returned to the caller and never written. Writing it would create a new record
object kind, which is frozen surface 2 and needs an operator grant nobody has
asked for.

## Three layers, not interchangeable

**FROZEN — the change protocol.** (a) A source's output is CONTENT for
presentation, never evidence: no source, bundle or stage may change what is
admitted, ranked, immune or refuted. (b) A source never appends. (c) The alias
table is not a source and may not become one — it decides what a citation
RESOLVES TO, which is the evidence side. (d) Only the operator authors a
source.

**VERSIONED — the registries.** Sources keyed `(source_id, source_version)`;
seat source bundles keyed by id. A new assembly is a registration, never a
consumer edit.

**FREE — the values.** Each source's parameters, inside its own declared model,
refused typed at construction rather than silently accepted.

## The five stages, and why there are five

A stage boundary exists only where the CALLER must do something this interface
may not. There are four such acts.

| stage | what the caller does when it ends |
|---|---|
| `pre_contract` | builds the turn contract, which needs to know whether criticism is open |
| `render` | allocates the pack |
| `post_allocation_context` | abandons a pre-issued scratch context if its render failed — a transactional, record-side act |
| `post_allocation` | binds the pack's ALIAS TABLE |
| `post_allocation_after_aliases` | — |

`check: python -c "
from deepreason.seat_sources import (
    POST_ALLOCATION_STAGES, STAGES, STAGE_PRE_CONTRACT, STAGE_RENDER,
    resolve_seat_source_bundle, resolve_section_source)
assert len(STAGES) == 5, STAGES
assert len(POST_ALLOCATION_STAGES) == 3, POST_ALLOCATION_STAGES
bundle = resolve_seat_source_bundle('conjecturer')
assert len(bundle.entries) == 13, len(bundle.entries)
per_stage = {s: [resolve_section_source(e.source_id, e.source_version).supplies
                 for e in bundle.entries_for_stage(s)] for s in STAGES}
assert per_stage[STAGE_PRE_CONTRACT] == ['open_criticism_context'], per_stage
assert len(per_stage[STAGE_RENDER]) == 8, per_stage
assert per_stage['post_allocation_after_aliases'] == ['post_allocation_menus'], per_stage
"`

## The invariants

**Selection is by id, from an argument or the environment — never `Config`,
never the manifest.** The same measured reason `DR-INV-seat-section-plugins`
gives: the manifest dumps every `Config` field into `engine_config_json` and
qualification folds that into every subject digest, so a bundle knob on
`Config` would move the digest of every qualification bundle in the tree.
`check: python -c "
from deepreason.config import Config
from deepreason.seat_sources import SEAT_SOURCE_BUNDLE_ENV
fields = {f.upper() for f in Config.model_fields}
assert SEAT_SOURCE_BUNDLE_ENV not in fields
assert not [f for f in fields if 'SOURCE_BUNDLE' in f or 'SECTION_SOURCE' in f], sorted(fields)
"`

**An unregistered id is a typed refusal, never a load-by-path.** A source runs
inside the harness WITH the harness in its hand, so the only thing that may
introduce one is the operator.
`check: python -c "
from deepreason.seat_sources import SeatSourceError, resolve_section_source
try:
    resolve_section_source('dr.src.nothing.here')
except SeatSourceError as error:
    assert error.code == 'SEAT_SOURCE_UNKNOWN', error.code
else:
    raise AssertionError('an unregistered source id resolved')
"`

**The default render has not moved.** Both seats' briefs are byte-identical to
what they were before this layer existed.
`check: python -m pytest tests/test_conj_pack_legacy_golden.py tests/test_crit_pack_legacy_golden.py -q`

**Shape buys nothing, here too.** No source, result, receipt or bundle entry
carries a score, rank, weight, confidence, priority, authority, status or
immunity field.
`check: python -m pytest tests/test_seat_section_architecture.py -q`

## Where to change what

| To do this | Edit | Test |
|---|---|---|
| change what one record-backed section CONTAINS | that source in `shipped.py`, or register a new version and pin it in the bundle entry | the goldens |
| feed a section from somewhere else | register a source and swap the bundle entry — no consumer edit | `tests/test_seat_section_sources.py` |
| add a block after allocation | register a post-allocation source; the runner does the `AllocatedPack` re-wrap | `tests/test_pack_prefix.py` |
| commit something to the record beside a section | `rules/conj.py`, from the source's `carries` | `tests/test_seat_section_sources.py` |
| select a different assembly for a run | `DEEPREASON_SEAT_SOURCE_BUNDLE=conjecturer=<id>` | `tests/test_seat_section_sources.py` |

## Traps

- **A source that resolves to NOTHING may still need to carry something.** The
  frozen-evidence source carries the run's bound dossiers even on a run with no
  attached evidence, because the citable legend after it is computed over that
  (empty) union either way. Its receipt still says `absent`, because the
  SECTION is what a reader of a receipt is asking about. A runner that dropped
  the carries of a `None`-valued result would silently empty the legend.
- **Order inside a stage is meaningful and is not obvious from the code.** The
  pre-allocation menu source reads the citable blocks the evidence source
  carried; the post-allocation menu source reads the scratch aliases the
  context source carried. The bundle's entry order is the declaration, and a
  reordered bundle renders a different brief without failing anything but the
  goldens.
- **The computation moved; the COMMIT did not.** `pack_dossier` and
  `commit_dossier_pack_receipt` sat next to each other in `rules/conj.py`, and
  the obvious extraction takes both. Taking both would have put an event append
  inside a source. The source computes the receipt and carries it; `conj`
  commits it, on the same path and at the same point in the run as before.
