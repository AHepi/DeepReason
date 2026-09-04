# SPEC — the nine caller-computed brief sections move behind the seat-section
# interface

Phase: `dr-spec-change`. Date: 2026-09-04.
Authority: `REQUEST.md` (R1-R17, C1-C6). Every section below cites the
requirement it serves.

---

## §0 Map preflight (resolved ids, recorded here so every later phase starts
## from the same map — R17)

| id | why it is in scope |
|---|---|
| `DR-SEAM-packs-and-token-economy-x-rules` | THE seam this tranche moves. Read first, before either side. Owns `llm/packs.py` and `rules/conj.py` jointly; names the nine caller-computed contexts and the four post-allocation re-wraps. |
| `DR-INV-seat-section-plugins` | the interface the sections must arrive through; owns `llm/seat_sections.py`, `seat_plugins.py`, `seat_layouts.py`, `seat_templates.py`, `role_prompts.py` |
| `DR-REC-add-a-section-plugin` | its step 1 states the exact gap this tranche closes: "if your content is of the second kind ... this recipe does not cover you" |
| `DR-SUB-rules` | the side losing the computation |
| `DR-CON-packs-and-token-economy` | the budgeting side; NO SILENT CAPS and `DISCLOSED_ON_DROP` |
| `DR-INV-reference-menu` | two of the moved values are menus; a menu may change what the seat is SHOWN, never what the harness ACCEPTS |
| `DR-INV-render-layout` | the sibling pattern the registry copies |
| `DR-INV-frozen-surfaces` | read before designing (§6) |
| `DR-CON-conjecture-source` | already forbids `conj` from writing outside its own channel; the source layer inherits that prohibition |

## §1 The problem, stated once

`rules/conj.py::conj` computes nine of the conjecturer brief's twenty section
slots and hands them to the renderer as strings, then appends three more
blocks and substitutes a fourth after allocation. The prior tranche made every
section RENDER through a registered plugin but left these nine COMPUTED in the
admission code, because a plugin may not call the harness
(`DR-INV-seat-section-plugins`, FROZEN clause; the prior `SPEC.md` A6). So the
recipe for adding a section stops at the door for exactly the sections that
carry evidence: `DR-REC-add-a-section-plugin` step 1 says so in as many words.

The consequence is not cosmetic. The operator's stated purpose for the
seat-is-a-shell law is to "slowly separate the authority layer"; while the
generation side must reach into the admission code for its content, the two
layers cannot come apart.

## §2 What ships — S1: a registered SOURCE layer beside the plugins (R3)

A new module, `src/deepreason/llm/seat_sources.py`, holding four things.

**S1.1 The request — what a source may read.** `SectionSourceRequestV1`,
frozen, `extra="forbid"`, carrying `harness`, `run_manifest`, `config`,
`problem`, and three mappings: `inputs` (call-local state the caller hands
over), `supplied` and `carries` (what earlier sources in this bundle already
produced). A source reads; it holds no reference it may write through by
contract, and §3 states the contract and the check that enforces it.

**S1.2 The protocol.**

```
class SeatSectionSourceV1(Protocol):
    source_id: str            # "dr.src.frozen_evidence", ...
    source_version: str       # semver; part of the receipt
    supplies: str             # the key its value lands under
    parameters_model: type[BaseModel]
    requires: tuple[str, ...] # input keys it cannot resolve without
    writes_blobs: bool        # declared, see §3

    def resolve(self, request, params) -> SectionSourceResultV1 | None: ...
```

`None` is a legal absence — exactly the `if <context>:` guards `conj` uses
today — and is recorded as `absent`, never as an empty value.

**S1.3 The result.** `SectionSourceResultV1(supplies, value, text,
substitutes, carries)`. A RENDER-stage source sets `value` — the thing the
plugin formats. A POST-ALLOCATION source sets `text`, and additionally
`substitutes` when its text replaces existing pack bytes rather than being
appended. `carries` holds by-products a later source or the caller may read
(the dossier receipt, the scratch alias map), and is the mechanism by which
the record-side act that must stay in `rules/` still gets what it needs
(§4, Q4).

**S1.4 The registries — the VERSIONED layer.** Sources keyed
`(source_id, source_version)`, resolved pinned or to the highest version, an
unregistered id a typed refusal and never a load-by-path — the same shape and
the same security reason as `resolve_section_plugin`. A `SeatSourceBundleV1`
is one seat's ordered list of `SeatSourceBundleEntryV1(source_id,
source_version, stage, params)`, registered by id, selected by argument, then
`DEEPREASON_SEAT_SOURCE_BUNDLE`, then the seat's default. **Never `Config`,
never the manifest** — the measured reason is already on the record
(`DR-INV-seat-section-plugins`: the manifest dumps every `Config` field into
`engine_config_json` and qualification folds that into every subject digest),
and an architecture check asserts the absence.

**S1.5 The runner.** `assemble_sources(seat_id, stage=..., request=...,
prior=...)` walks the bundle's entries for one stage, in order, and returns a
frozen `SourceAssemblyV1(supplied, carries, receipts)`.
`apply_post_allocation(seat_id, stage=..., pack=..., request=...)` does the
same for a post-allocation stage and returns the new pack, **re-wrapped in
`AllocatedPack` by the runner**. That re-wrap moves here from `conj.py`; the
seam's Traps entry ("a fifth insertion added later inherits nothing") moves
with it and its count check is re-pointed at this module.

**S1.6 The receipts.** `SectionSourceReceiptV1(source_id, source_version,
supplies, parameters_digest, value_bytes, disposition)`, returned to the
caller and NOT written to the log. Writing them would be a new record object
kind — frozen surface 2, an explicit STOP under R13, and the thing the
previous build already parked. Nothing here asks for that grant.

**S1.7 The seeded sources.** `src/deepreason/llm/seat_source_plugins.py`,
mirroring `seat_plugins.py`, with an `ensure_seeded()` and the shipped
bundle `conj-sources.legacy-v0`. Thirteen sources (§5).

## §3 S2 — may a source read the log? (R4, R5)

**DECISION: YES for reading; NEVER for appending; ONE declared write.**

**A source MAY read the log, the state, the blobs and the run root.** The
window states the principle and this repo's own epistemology backs it:
"reading the record is not a contact". Four of the nine values cannot exist
otherwise — `dossier_exposure_counts` walks the log, `dossier_union` reads the
root's amendment epochs, the frame slice reads consulted assertions, the
discharge channel reads open criticisms. Forbidding the read would not make
the layer purer; it would make it empty, and the computation would stay in
`rules/` where this tranche found it.

**A source may NEVER append.** Precisely: after any source runs, the run's
event sequence number, the bytes of `log.jsonl`, and the state digest are
unchanged. This is the clause R5 asks to be proven, and §7's architecture test
proves it by measuring all three before and after every registered source, and
goes red when a write is planted in one.

**ONE write is permitted and it is declared, not hidden.** `pack_dossier`
materialises the excerpts it selected into the content-addressed blob store
before the receipt can name them, and the frozen-evidence value cannot be
rendered without that receipt. So a source may write CONTENT-ADDRESSED BLOBS
and nothing else, must declare `writes_blobs = True` to do it, and the
architecture test asserts that every source NOT declaring it adds no file
under `blobs/`. Why this is not a hole in the clause: a blob put is
idempotent, keyed by the hash of its own bytes, appends no event, assigns no
epistemic status, and moves no digest — it is materialisation, not record.
Stated plainly because the operator's word was "writes nothing": one source
writes blobs, exactly where `rules/conj.py` writes them today, at the same
point in the run.

## §4 S3 — where the split falls at the one source that touches the record
## (answers Q4)

`rules/conj.py` today runs `pack_dossier` → `commit_dossier_pack_receipt` →
`render_dossier_pack`. The middle step appends an event.

**The source computes; the caller commits.** `dr.src.frozen_evidence` does
`pack_dossier` and `render_dossier_pack`, and CARRIES the receipt.
`rules/conj.py` reads the carried receipt and commits it, on exactly the path
it commits it on today. The generation side never appends; the record side
never formats.

**Why the reordering is safe, and it is checked rather than argued.**
`render_dossier_pack` reads `receipt.receipt_digest` and the excerpt blobs
`pack_dossier` wrote; it reads nothing the commit produces. Between today's
commit point and the point the caller will commit at, `conj` appends no other
event — the intervening lines compute the citable legend, two frame contexts
and the pre-allocation menus, all pure reads. **The order of events in the log
is therefore unchanged**, and the golden fixtures plus the existing
dossier-receipt tests are what say so.

## §5 S4 — the thirteen sources and the five stages (R1, R10)

A stage boundary exists only where the CALLER must do something the interface
may not do. There are four such acts, so there are five stages.

| stage | the sources | why the stage ends here |
|---|---|---|
| `pre_contract` | `dr.src.open_criticism` | the caller builds the turn contract next, and needs `discharge_enabled` — a contract that pruned discharges while the pack listed open handles would ask for something the reply cannot express (`conj.py`'s own comment) |
| `render` | `dr.src.frozen_evidence`, `dr.src.citable_evidence`, `dr.src.frame_slice`, `dr.src.frame_crisis`, `dr.src.capability_result`, `dr.src.scratch_context`, `dr.src.generation_context`, `dr.src.reference_menus` | the renderer allocates next |
| `post_allocation_context` | `dr.src.post.scratch_render` (substitute) | on failure the caller must ABANDON the pre-issued scratch context — a transactional, record-side act |
| `post_allocation` | `dr.src.post.sealed_simulation`, `dr.src.post.scratch_workshop` | the caller must bind the pack's ALIAS TABLE next |
| `post_allocation_after_aliases` | `dr.src.post.reference_menus` | end |

**The alias table is NOT a source and never will be.** It decides what a
citation RESOLVES TO, which is the evidence side; a registered, swappable
alias binder would let a brief configuration change what the harness accepts —
the one thing `DR-INV-seat-section-plugins`' FROZEN clause (a) forbids. It
stays in `rules/conj.py`, which is why the last stage exists.

**Ordering inside a stage is meaningful and declared.**
`dr.src.reference_menus` reads `citable_blocks_shown` carried by
`dr.src.citable_evidence`; `dr.src.post.reference_menus` reads
`scratch_aliases` carried by `dr.src.post.scratch_render` and the alias table
the caller bound. The bundle's entry order is the declaration.

**Scope note, disclosed rather than absorbed (R10, R11).** R10's scope is "the
nine A6 sections and the three appended after allocation". The seam document
names FOUR post-allocation re-wraps; three are APPENDS and the fourth is a
SUBSTITUTION (the v6 scratch render replacing its canonical text). This tranche
moves the substitution as well — thirteen sources, not twelve — because R2's
sentence ("no section a seat is shown is COMPUTED inside rules/") is false
while a section's final bytes are computed there, and because leaving one of
the four re-wraps behind would split the `AllocatedPack` rule across two
modules, which is the exact shape its Trap warns about. Cost: one source, ~35
lines. Decided without asking, dominant under the operator's recorded values
(smallest change that makes the stated goal true).

## §6 S5 — frozen surfaces (R12, R13)

**Forecast before running the instrument: NO CONTACT.** Nothing here touches
digests, event application, replay formats, manifest schemas or qualification
subjects; the new layer reads the record and appends nothing, and its receipts
stay out of the log precisely so no new record object kind is created.

`tools/blast_radius.py` over the planned targets, verbatim:

```
python tools/blast_radius.py \
  --files src/deepreason/rules/conj.py src/deepreason/llm/packs.py \
          src/deepreason/llm/seat_sections.py \
          src/deepreason/llm/seat_plugins.py \
          src/deepreason/llm/seat_layouts.py \
  --symbols conj render_conj_pack _walk_seat_layout AllocatedPack \
            pack_dossier render_dossier_pack citable_legend \
            render_frame_slice_context render_frame_crisis_context \
            render_open_criticism_context menu_renders_for \
            render_v6_conjecture_context

"frozen_surface_verdict": "CONTACT"
"frozen_surface_contacts": [
  {
    "surface": "replay-validation record formats (invariants.py)",
    "tier": "SYMBOL_INDIRECT",
    "target": "conj",
    "detail": "'conj' referenced in src/deepreason/invariants.py
               (grep-based; not proof of semantic contact)"
  }
]
"frozen_adjacent_contacts": []
```

**The verdict is CONTACT and the forecast was NO CONTACT, so the row is
opened rather than waved past.** It is a grep artefact, and that is measured,
not asserted: `invariants.py` imports nothing from `rules`, contains zero
calls to a bare `conj(...)`, zero `.conj` attribute uses, and exactly ONE
bare-word occurrence of `conj` in the whole file — inside the string literal
`"conj-noregister"` at line 2410, an event input tag. The tool's own honesty
limit names this class: "SYMBOL_INDIRECT contact is a grep-based reference,
not proof of semantic contact — report it as plausible, not confirmed."

```
python - <<'PY'
import ast, pathlib, re
src = pathlib.Path('src/deepreason/invariants.py').read_text()
tree = ast.parse(src)
print('imports naming rules/conj:',
      [(getattr(n,'module',None), [a.name for a in n.names])
       for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom))
       and ('rules' in (getattr(n,'module',None) or '')
            or any(a.name=='conj' for a in n.names))])
print('bare conj() calls:',
      len([n for n in ast.walk(tree) if isinstance(n,ast.Call)
           and getattr(n.func,'id',None)=='conj']))
print('.conj attribute uses:',
      len([n for n in ast.walk(tree) if isinstance(n,ast.Attribute)
           and n.attr=='conj']))
print('bare-word conj lines:',
      [src[:m.start()].count('\n')+1
       for m in re.finditer(r'(?<![A-Za-z_])conj(?![A-Za-z_])', src)])
PY
imports naming rules/conj: []
bare conj() calls: 0
.conj attribute uses: 0
bare-word conj lines: [2410]
```

**Disposition: no grant is requested and none is needed.** The row does not
survive being opened. `blast_radius` is re-run against the ACTUAL diff at
validation (R14's boundary), and a contact that survives that run is a STOP,
not a footnote.

**The one thing that would be a real contact, and is refused here:** writing
the source receipts into the record. That is a new record object kind, frozen
surface 2, and R13 makes it a STOP for a grant. §2's S1.6 keeps the receipts
in memory for exactly this reason; parking it is the same disposal the
previous build made.

## §7 S6 — acceptance checks, one per requirement

| # | requirement | check | how it can fail |
|---|---|---|---|
| A1 | R6 | `pytest tests/test_conj_pack_legacy_golden.py tests/test_crit_pack_legacy_golden.py -q` with `git diff --stat tests/fixtures/` empty | any byte of either default render moves |
| A2 | R1, R10 | a new `tests/test_seat_section_sources.py` asserts the shipped bundle supplies all nine keys and all four post-allocation slots, resolved through the registry | a section left behind in `rules/` |
| A3 | R2, R8 | a new architecture test: `rules/conj.py` imports and constructs no pack-section type (`PackSection`, `PackIR`, `SectionRenderV1`, `AllocatedPack`, `_pack_section`, `allocate_pack`) AND calls none of the nine content renderers | planting any one back goes red |
| A4 | R5 | a new architecture test drives EVERY registered source against a prepared run root and asserts `_next_seq`, `log.jsonl` bytes and the state digest are unchanged; a planted-write source is registered inside the test and the same assertion goes red | the clause is proven, not asserted |
| A5 | R5 | the same test asserts that a source not declaring `writes_blobs` creates no file under `blobs/` | an undeclared write |
| A6 | R7 | `pytest tests/test_seat_section_architecture.py -q` unchanged and passing; mutation-proven by planting a seat-name read on an authority path | the shape-buys-nothing law |
| A7 | R3 | selection is by argument/env only: no `Config` field, no manifest field mentions a source or a bundle | a knob that would move every qualification digest |
| A8 | R14 | `pytest tests/ -q -n 4` → 0 failed, nothing weakened | the gate |
| A9 | R14 | `python tools/docs_verify.py` → only C4's six classified rows fail; `--links` 0 dangling | the map moved with the code |
| A10 | R12 | `blast_radius` over the ACTUAL diff at validation | a contact introduced by the code that the plan did not forecast |

## §8 S7 — what the renderer's signature does, and does not, become

`render_conj_pack` keeps its nine keyword arguments. Twenty-odd test call
sites pass them and the golden cases are among those call sites; removing them
would rewrite the very fixtures A1 exists to protect. It GAINS one optional
`supplied: Mapping | None`, merged over the mapping it builds itself, and
takes `reference_menus` from that mapping when the argument is not given.
`rules/conj.py` then passes `supplied=assembly.supplied` and names no section
key at all.

`render_crit_pack` is untouched.

## §9 Assumptions recorded (the smallest reading, where REQUEST.md is silent)

- **A1.** "The three appended after allocation" means the three APPENDS; the
  fourth re-wrap is a substitution. §5 says what happens to it and why.
- **A2.** R2's "rules/" is read as the CONJECTURER'S admission code for this
  tranche. `rules/crit.py` still computes four contexts, and they are NOT
  moved here — see §10 for the price and the park. R10's SCOPE names the nine
  and the three, and the critic's call sites need a per-call subset selector
  the source bundle does not have (the batch fallback deliberately supplies
  two of the four and not the other two). Widening here would be the scope
  creep the ledger rule exists to prevent.
- **A3.** A source's receipts stay in memory (S1.6). Not a grant request.
- **A4.** Byte-identity is the arbiter of every judgement call inside a move:
  where a mechanical extraction and a tidier rewrite differ, the extraction
  wins.
- **A5.** No live run (C3). Every acceptance check is offline.

## §10 Parked at spec time (R11)

| id | what | one-step under this layer? |
|---|---|---|
| P4 | the batch critic renderer | NO — still needs a per-target repetition construct the plugin protocol lacks. Unchanged by this tranche. |
| P5 | four seats with hardcoded briefs | NO — still needs a layout, a shell and a golden per seat. |
| NEW | `rules/crit.py`'s four caller-computed contexts | ALMOST — three of the four sources are the ones this tranche registers, and only `premise_invitation` is new. The blocker is per-call subset selection, priced in `PARKED.md`. |
| NEW | source receipts into the record | needs a frozen-surface-2 grant. Not requested. |

## §11 Budget

`src/` insertions ceiling for this tranche: **1600**. The instrument
(`tools/diff_budget.py`) pays twice for a move — the prior tranche measured
that — so the ceiling is stated against the instrument, and exceeding it is a
STOP that goes to the operator with roads priced, not a number to explain
away.
