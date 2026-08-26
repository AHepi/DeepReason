# Spec for: reference grounding — the model chooses handles from a menu

Traces: every item cites R/C numbers from REQUEST.md. Untraceable items are
bugs and are deleted by the anti-invention pass (§Anti-invention).

Tranche: `experiments/2026-08-26-change-f2-reference-menu/`, F2 of REBUILD.

---

## 0. The problem this spec answers, in the record's own numbers

C2/C3, from `experiments/2026-08-26-run-anatomy-program/W1-form-census/
RESULTS.md`:

- §2 — 1 178 of 1 434 recorded diagnostics name a field. **737 of those
  1 178 (62.6%) are a handle the model made up.** The five commonest
  field-attributed failures in the whole 54-root corpus are all
  reference-bearing fields.
- §3 — **CFR 99.2%**: 257 diagnostics announced that omission was legal;
  in **255** the seat supplied an invented handle anyway. **EUR ≈ 5.8%**:
  of 120 ladders offering an escape, 7 took it.
- §3, the decisive contrast — `claim_class` offers `unknown` **in the
  enum** and models take it (6/85, 10/55). The omission escape exists
  **only in instruction text** and is taken 7/120. C4's words: "escape
  roads that exist but are not taken are decoration; the defense must be
  structural."

The five census-attested failing fields, with their legal-set owners as
they exist in the tree today:

| W1 rank | pointer | contract | who owns the legal set today |
|---|---|---|---|
| 244 | `/candidates/*/evidence_refs/*/block` | `conjecturer.turn.v6` | **nobody** — `Field(pattern=r"^[0-9a-f]{12,64}$")`, `wire.py:2340` |
| 230 | `/scratch_proposal/unresolved_questions/*/related_refs` | `conjecturer.turn.v6` | `scratch_reference_context`, `wire.py:2276` |
| 129 | `/cases/*/premise_evidence/*/block` | `batch-critic.v2` | **nobody** — same pattern field |
| 70 | `/scratch_proposal/links/*/to_ref` | `conjecturer.turn.v6` | `scratch_reference_context`, `wire.py:2276` |
| 64 | `/candidates/*/optional_refs/*` | `conjecturer.turn.v6` | `self.aliases` (AliasTable), `wire.py:2046` |

Two facts this table makes decidable, and both shape the design:

1. **`optional_refs` already carries a schema enum** (`_bind_alias_array`,
   `wire.py:1998`) and still produced 64 invented-handle rejections. A
   schema enum alone is not the fix; R8 forbids schema changes anyway.
   The menu must be in the PROMPT.
2. **The two `block` fields have no legal-set owner at all.** Their
   rejections are bare `string_pattern_mismatch`, which is why the
   diagnostic can offer no list for them — 373 of the 737. R5's
   "one authority" therefore has to CREATE the authority for these two,
   not merely share an existing one.

## 1. Frozen-surface contact forecast — computed, pasted verbatim

Two runs of `tools/blast_radius.py`, both pasted. The first declares
`ordered_refs` and `citable_legend`, which R3 NAMES as mechanisms to
reuse; the second declares only the symbols this design will MODIFY.

**Run 1 — targets include the R3-named reuse mechanisms.**

```
--files src/deepreason/llm/packs.py src/deepreason/llm/repair.py
        src/deepreason/llm/wire.py src/deepreason/rules/conj.py
        src/deepreason/rules/crit.py src/deepreason/evidence/render.py
--symbols render_reference_menu legal_handles_for ReferenceFieldDeclaration
          REFERENCE_FIELD_DECLARATIONS MenuRenderPolicy citable_legend
          _handle_fields_from_error _scratch_reference_guidance
          diagnostic_from_error render_conj_pack render_batch_crit_pack
          render_crit_pack ordered_refs _pack_section DISCLOSED_ON_DROP

"frozen_surface_contacts": [{"surface": "replay-validation record formats
  (invariants.py)", "tier": "SYMBOL_INDIRECT", "target": "ordered_refs",
  "detail": "'ordered_refs' referenced in src/deepreason/invariants.py
  (grep-based; not proof of semantic contact)"}]
"frozen_adjacent_contacts": []
"frozen_surface_verdict": "CONTACT"
```

**Run 2 — targets are the symbols this design modifies.**

```
--files src/deepreason/llm/packs.py src/deepreason/llm/repair.py
        src/deepreason/llm/wire.py src/deepreason/rules/conj.py
        src/deepreason/rules/crit.py
--symbols _handle_fields_from_error _scratch_reference_guidance
          diagnostic_from_error render_conj_pack render_batch_crit_pack
          render_crit_pack _pack_section DISCLOSED_ON_DROP

"frozen_surface_contacts": []
"frozen_adjacent_contacts": []
"frozen_surface_verdict": "CLEAR"
"consumers.qualification_digest": []
"consumers.wheel_smoke_pins": []
```

**Disposition, stated so it can be checked rather than believed.** Run 1's
CONTACT is produced entirely by declaring `ordered_refs`, a symbol R3 tells
this tranche to REUSE. This design calls `ordered_refs`; it modifies
neither it nor `invariants.py`. `citable_legend` and
`src/deepreason/evidence/render.py` are likewise dropped from run 2 because
the design consumes `CitableLegend.shown` — which conj.py already captures
as `citable_blocks_shown` (`rules/conj.py:1380-1381`) — and writes nothing
in `evidence/`. Run 2 is therefore the tranche's real surface, and it is
CLEAR.

The disposition is pinned rather than asserted: **S10** commits a check
that `src/deepreason/invariants.py`, `src/deepreason/scratch/render.py` and
`src/deepreason/evidence/render.py` are byte-unchanged by this tranche, so
the claim "reuse, not modification" fails the gate the moment it stops
being true. Should implementation discover that any of the three must move,
that check goes RED and the tranche STOPS for the operator's words before
the change lands — which is the frozen-surface checkpoint enforced at
execution time rather than remembered from here.

**`reachability: UNKNOWN`**, disposed one by one. `render_reference_menu`,
`legal_handles_for`, `ReferenceFieldDeclaration`,
`REFERENCE_FIELD_DECLARATIONS`, `MenuRenderPolicy` — do not exist yet, so
there is nothing for the gate to resolve and no consumer to census.
`DISCLOSED_ON_DROP` — a module-level frozenset, which the gate says in
writing it cannot judge as a call target. The required manual cross-check
was run; its hits are in §7.

## 2. The design, in three layers (R16, R19, C8)

R16 requires the signal-contract pattern. `docs/map/INV-signal-contract.md`
names the three layers; this is F2's instance of them.

| Layer | F2's content | What it takes to change it |
|---|---|---|
| **FROZEN** — the protocol | (a) a reference-bearing field's legal set has exactly ONE resolver, and the prompt menu and the repair diagnostic both consume it through the interface; (b) **a menu is presentation, never validity** — no menu may admit or reject a value; (c) no silent truncation | an operator design law |
| **VERSIONED** — registry + policy | `REFERENCE_FIELD_DECLARATIONS` (which fields have menus, and of what kind) and `MenuRenderPolicy` (a recorded artifact) | registering a declaration / revising the policy artifact — no renderer edit |
| **FREE** — parameters | `inline_threshold`, `maximum_entries`, `excerpt_chars` inside declared envelopes | ordinary configuration |

Layer FROZEN clause (b) is F2's analogue of the signal contract's
"allocation touches EFFICIENCY, NEVER EVIDENCE". A menu changes what the
model is SHOWN. It must never change what the harness ACCEPTS — validity
stays with the wire validators exactly as today. S11 makes that failable.

**The interface, keyed by field kind (R19).** One protocol, three
implementations, registered:

```
class LegalHandleSource(Protocol):
    def handles(self, binding: MenuBinding) -> tuple[str, ...]: ...
```

| handle kind | source implementation | reads |
|---|---|---|
| `citable_block` | `CitableBlockHandles` | `binding.citable_block_ids` (from `CitableLegend.shown`) |
| `scratch_local` | `ScratchLocalHandles` | `binding.scratch_handles` + `binding.new_block_keys` |
| `artifact_alias` | `ArtifactAliasHandles` | `binding.aliases` (the call's `AliasTable`) |

A new reference-bearing field type gets a menu by appending a
`ReferenceFieldDeclaration` and, if its handles come from somewhere new, by
registering one `LegalHandleSource` under a new kind. **The renderer is not
edited in either case** — S12 proves this with a synthetic declaration
registered at test time.

**Ordering discipline (R3, Q6).** `ordered_refs`' ledgered invariant
(CLAUDE.md: "Render-receipt handle maps reload key-sorted (B1, B10, B2,
...); compare by handle index, never by `.values()`") is honoured two ways.
Where a render receipt exists — the scratch namespace — `ScratchLocalHandles`
calls `receipt.ordered_refs(...)` when the binding carries a receipt, which
is R3's literal instruction. Where none exists — evidence block ids have no
render receipt — the same DISCIPLINE is applied: menu entries are emitted in
declared index order and index order is the only order any consumer compares
by; the module never iterates a handle mapping's `.values()`. S13 pins the
second half with a lexicographic-trap fixture (entries 1, 2, ..., 10, 11)
that a key-sorted implementation fails.

## 3. Items

### S1 (R1, R16, R19, C8) — the interface, registry and policy

**New file** `src/deepreason/llm/reference_menu.py`. Before: no such
module; each consumer that knows a legal handle set knows it privately.
After: one module declaring

- `HandleKind` — `Literal["citable_block", "scratch_local",
  "artifact_alias"]`, extended by registration.
- `ReferenceFieldDeclaration(frozen dataclass)` — `field_id`,
  `pointer_template` (the JSON Pointer with `*` for indices, matching the
  spelling the record already writes), `contract`, `handle_kind`,
  `omission_legal: bool`, `omission_first_ask: str`,
  `omission_repair: str`. `__post_init__` refuses an incomplete
  declaration, mirroring `SignalDeclaration.__post_init__`.
- `REFERENCE_FIELD_DECLARATIONS: dict[str, ReferenceFieldDeclaration]` —
  the VERSIONED registry, seeded with the five census-attested fields of
  §0 plus the three free siblings in the same namespaces
  (`/scratch_proposal/links/*/from_ref`,
  `/scratch_proposal/cluster_suggestions/*/member_refs`,
  `/scratch_proposal/revisions/*/target_alias`) and
  `/cases/*/target_alias`. Ten declarations.
- `MenuBinding(frozen dataclass)` — the call-local facts a menu is built
  from: `citable_block_ids`, `scratch_handles`, `new_block_keys`,
  `aliases`, `render_receipt`. Every field defaults empty, so a caller
  that has none of a kind produces no menu rather than an error.
- `LegalHandleSource` protocol + the three implementations + a
  `register_handle_source(kind, source)` entry point.
- `MenuRenderPolicy(frozen dataclass)` with `DEFAULT_MENU_POLICY` — the
  FREE parameters and their envelopes.
- `legal_handles_for(field_id, binding, *, policy) -> LegalHandleSet` —
  **the one authority** (R5). Returns the ordered handle tuple, the
  omission entry when legal, and `total`/`shown`/`truncated`.
- `render_reference_menu(field_id, binding, *, policy) -> MenuRender |
  None` — the renderer. Consumes `legal_handles_for` and nothing else.
- `menu_renders_for(contract, binding, *, policy)` — every declared menu
  for one contract, in registry order.

`accept:` `python -m pytest tests/test_reference_menu.py -q` → 0 failed,
and `python -c "from deepreason.llm.reference_menu import
REFERENCE_FIELD_DECLARATIONS as D; assert len(D) == 10; assert all(d.field_id
== k for k, d in D.items())"` → exit 0.

### S2 (R1, R2, R6, A2) — the rendered menu

`render_reference_menu` emits, for a field with handles:

```
REFERENCE MENU — /candidates/*/evidence_refs/*/block
Choose a value for this field from this list ONLY. Any value not listed
is rejected; do not write a handle that is not here.
  [0] OMIT — leave "evidence_refs" out of this candidate entirely.
      This is a legal, complete answer. Prefer it to a guess.
  [1] a3f19c2b8e04
  [2] 7d0c1149ab52
You may answer with the handle itself or with its [index].
```

Short lists (`<= policy.inline_threshold`) render inline as above; long
lists render as the same indexed table with a header row and the same
index grammar (R2). One renderer, one grammar — the "short/long" fork
changes layout density only, so a seat that learned to answer `[2]` on a
short menu answers `[2]` on a long one.

The omission entry is **index 0 and always first** where
`omission_legal` (R6), and its text is the declaration's own
`omission_first_ask` — spelled concretely per field, never as prose
advice. `omission_repair` carries the repair-mode spelling ("write a
remove operation at `<pointer>`"), which is what A5 resolves.

`accept:` `python -m pytest
tests/test_reference_menu.py -k "omission_is_entry_zero or index_grammar
or long_list_is_the_same_grammar" -q` → 0 failed.

### S3 (R11, A4, C7) — the token economy, bounded and disclosed

`MenuRender` carries `text`, `tokens` (from `packs.approximate_tokens`,
the token economy's own unit), `total`, `shown`, `truncated`.

Truncation is DISCLOSED inside the rendered text, so the disclosure cannot
be separated from the menu by any consumer:

```
(+37 further legal handles not shown — this menu was truncated to fit the
 pack budget; the full legal set is larger than what is listed here.)
```

Menus whose handle set is known before allocation (`citable_block`,
`scratch_local`) enter `_allocate_sections` as real `PackSection`s via
`_pack_section` and are added to `DISCLOSED_ON_DROP`, so a menu dropped
whole is announced by the existing no-silent-caps machinery
(`packs.py:267-296`). Menus whose handle set exists only after allocation
(`artifact_alias`, because `aliases_for_pack` derives from the rendered
pack, `rules/conj.py:1474`) are appended as post-allocation suffixes — the
idiom `rules/conj.py:1440-1465` already establishes and byte-accounts —
with their `tokens` recorded the same way.

`accept:` `python -m pytest tests/test_reference_menu.py -k
"truncation_is_disclosed or menu_tokens_are_counted or
menu_sections_are_disclosed_on_drop" -q` → 0 failed.

### S4 (R1, R4) — the menu reaches the conjecturer's FIRST ask

`src/deepreason/llm/packs.py`: `render_conj_pack` gains
`reference_menus: tuple[MenuRender, ...] = ()` and emits each as a
`_pack_section` next to the section that carries the field's content —
the evidence-block menu adjacent to `citable-evidence-blocks`, the
scratch menus adjacent to the scratch context. Before: the legal set
appears only in a repair diagnostic, after a wasted attempt (W1 §5: attempt
0 is 91.7% valid, every later attempt ~58%). After: it is in the first
prompt.

`src/deepreason/rules/conj.py`: builds one `MenuBinding` from facts it
already holds — `citable_blocks_shown` (:1381), `scratch_aliases` (:1425),
`aliases` (:1470/:1474) — and passes the renders down. The
`artifact_alias` menu is appended after `aliases` exists, as
`AllocatedPack(pack + ...)`.

`accept:` `python -m pytest tests/test_reference_menu.py -k
"conj_pack_carries_the_menu_on_the_first_ask" -q` → 0 failed, and the
assertion names the field pointer and a legal handle, both present in the
pack text with no provider call made.

### S5 (R1, R4) — the same for the critic

`src/deepreason/llm/packs.py`: `render_batch_crit_pack` and
`render_crit_pack` gain the same `reference_menus` parameter, for
`/cases/*/premise_evidence/*/block` and `/cases/*/target_alias`.
`src/deepreason/rules/crit.py` builds the binding from `single_legend`
/ the batch legend (:1464, :1729) and the `aliases` it already computes.

Adjacency note (C7, R13): this adds NEW sections to the critic packs. It
does not modify the criticism sections F1 owns, and F2 needs nothing from
F1 — see §5.

`accept:` `python -m pytest tests/test_reference_menu.py -k
"batch_crit_pack_carries_the_menu" -q` → 0 failed.

### S6 (R5, R10) — the diagnostic sources from the same authority

`src/deepreason/llm/repair.py`: `_scratch_reference_guidance` and
`_handle_fields_from_error` stop composing their own legal list and call
`legal_handles_for` with a binding rebuilt from the error's attached
state. Before: `wire.py` attaches `scratch_reference_context` and
`repair.py` re-derives `legal` from it independently of anything the
prompt showed (`repair.py:958-965`) — two lists kept in agreement, which
is exactly what E26's law forbids. After: one call, one set.

The diagnostic's `instruction` for an omission-legal field becomes the
declaration's `omission_repair`, so the escape road's spelling has one
owner too.

**Identity is in CONTENT, not bytes (A3).** The prompt menu and the
diagnostic list are the same SET, rendered for two different readers. Where
the shown menu was truncated, the diagnostic's list is the same
`legal_handles_for` result under the same policy — so they truncate
identically — and `_MAX_DIAGNOSTIC_LEGAL_HANDLES` is derived from
`policy.maximum_entries` rather than kept as an independent 32.

`accept:` `python -m pytest tests/test_reference_menu.py -k
"menu_and_diagnostic_are_one_set" -q` → 0 failed; plus the mutation proof
in S14.

### S7 (R5) — the two `block` fields gain a legal-set owner

`src/deepreason/llm/wire.py`: the two contracts that carry
`QuotedEvidenceWireV1` accept `citable_block_ids: tuple[str, ...] = ()` at
construction and attach it to the validation error the same way
`_attach_scratch_reference_context` already attaches scratch state
(`wire.py:2249-2280`). Before: a bad `block` raises a bare
`string_pattern_mismatch` with no list — 373 of W1 §2's 737. After: the
diagnostic carries the same legal set the menu showed.

**This is validation-message sourcing, not a schema change (R8).**
`model_json_schema()` output is unchanged: no property is added, removed,
or re-typed, and the new constructor argument is never read by
`model_json_schema`. S8 pins that.

`accept:` `python -m pytest tests/test_reference_menu.py -k
"block_field_diagnostic_lists_legal_blocks" -q` → 0 failed.

### S8 (R8) — the wire schema does not move

New test: for each touched contract, `model_json_schema()` is built on the
pre-change constructor arguments and on the post-change ones, and the
canonical-JSON sha256 of the two is asserted equal. Before: nothing pins
this. After: any schema drift fails the gate in the same commit that
causes it.

`accept:` `python -m pytest tests/test_reference_menu.py -k
"wire_schema_sha_does_not_move" -q` → 0 failed, and
`python scripts/wheel_smoke.py` → unchanged pins (no re-pin expected, per
R8).

### S9 (R9, A5) — a seat replying by index resolves to the right handle

`src/deepreason/llm/wire.py` preflight: for a field with a declared menu,
a value that is not already a legal handle and that matches the index
grammar (`[2]`, `2`, `#2`) resolves to the handle at that index in the same
`legal_handles_for` ordering the menu rendered. Index 0 where omission is
legal resolves to OMISSION — the field is dropped, which is the escape road
being taken structurally rather than advised (C4).

**Why this is safe, measured rather than assumed.** An index token is not a
legal handle under any of the three namespaces' own grammars: `block` is
`^[0-9a-f]{12,64}$` (`wire.py:2340`), scratch handles are
`^(?:SCR|NEW)_[0-9]{3,}$` (`repair.py:892`), artifact aliases are
`A<n>`/`SRC_<nnn>`. No value that resolves as an index could have been
valid as a handle, so resolution cannot capture a previously-valid value.
S15 pins that as a property test over the registry.

Resolution runs BEFORE validation and emits no new record observable (R7).

`accept:` `python -m pytest tests/test_reference_menu.py -k
"index_reply_resolves or index_zero_takes_the_omission or
index_grammar_never_shadows_a_legal_handle" -q` → 0 failed.

### S10 (§1) — the reuse claim is pinned

New test asserting `src/deepreason/invariants.py`,
`src/deepreason/scratch/render.py` and `src/deepreason/evidence/render.py`
are byte-identical to their `origin/main` content at this tranche's base
commit. Before: §1's disposition is a promise. After: it is a check that
goes RED if the tranche ever modifies a file it declared it would only
call.

`accept:` `python -m pytest tests/test_reference_menu.py -k
"the_reused_modules_are_not_modified" -q` → 0 failed.

### S11 (R16 FROZEN clause (b), R17) — a menu never decides validity

Architecture test: for a corpus of values, `validate_value` returns the
same verdict with the menu machinery present and with
`REFERENCE_FIELD_DECLARATIONS` emptied. A menu that started admitting or
rejecting anything turns this RED. This is F2's instance of "allocation
touches efficiency, never evidence".

`accept:` `python -m pytest tests/test_reference_menu.py -k
"a_menu_never_changes_what_is_valid" -q` → 0 failed.

### S12 (R17, R19, C8) — the customisation check

Architecture test, in two limbs, both of which must go RED if the
interface is bypassed:

1. **Register-don't-edit.** A synthetic `ReferenceFieldDeclaration` for a
   field name that appears nowhere in `src/` is registered at test time
   with a synthetic `LegalHandleSource`, and the renderer produces a
   correct menu for it. A renderer that hard-codes field names or handle
   kinds fails.
2. **Interface-only consumption.** An AST scan of `packs.py` and
   `repair.py` asserts that neither reaches a legal handle set except
   through `deepreason.llm.reference_menu` — mirroring
   `tests/test_signal_contract.py::
   test_the_allocation_controller_consumes_only_the_interface`
   (`tests/test_signal_contract.py:107`). The forbidden move is a
   consumer re-deriving `legal`/`scratch_handles`/`expected_aliases`
   itself, which is what `repair.py:958-965` does today and what S6
   removes.

`accept:` `python -m pytest tests/test_reference_menu.py -k
"a_new_field_gets_a_menu_by_registering or
consumers_reach_the_legal_set_only_through_the_interface" -q` → 0 failed.

### S13 (R3) — index order, not key order

Test with a menu of eleven entries asserting the rendered order is
1, 2, ..., 10, 11 and that comparison is by index. An implementation that
sorts keys lexicographically yields 1, 10, 11, 2, ... and fails. This is
CLAUDE.md's ledgered `ordered_refs` invariant applied to menus that have
no render receipt (Q6/A6).

`accept:` `python -m pytest tests/test_reference_menu.py -k
"menu_order_is_index_order_not_key_order" -q` → 0 failed.

### S14 (R10) — the mutation proof

A scratch copy of `reference_menu.py` is forked so the diagnostic path and
the menu path resolve from two independent lists, the divergence test from
S6 is run against it, and its RED output is captured to
`proof/s14_forked_red.txt` in this tranche. Before: "one authority" is a
claim. After: the claim has a demonstrated falsifier — per R10's own words,
"fork the lists in a scratch copy, a divergence test goes RED".

The fork happens in the session scratchpad, never in the repo (CLAUDE.md);
only the captured output is committed.

`accept:` `proof/s14_forked_red.txt` exists, contains a `FAILED` line for
the divergence test, and `proof/s14_unforked_green.txt` shows the same test
passing on the unforked tree.

### S15 (R9) — the index grammar cannot shadow a legal handle

Property test over every declaration in the registry: no string matching
the index grammar is a legal value under that field's own handle grammar.
Adding a future field whose handles are bare integers turns this RED, which
is the correct outcome — such a field must not use index replies.

`accept:` covered by S9's `accept`.

### S16 (R12) — the map moves in the same commits

- **New** `docs/map/INV-reference-menu.md` (`DR-INV-reference-menu`): the
  three layers of §2, the one-authority rule, the never-decides-validity
  rule, `Owns: src/deepreason/llm/reference_menu.py`, with a `check:` per
  load-bearing claim, each of which must be able to fail
  (`docs_verify.py --audit`).
- **Updated** `docs/map/INDEX.md` (invariants table row),
  `docs/map/SUB-llm.md` (the new module),
  `docs/map/CON-packs-and-token-economy.md` (menus as sections, the new
  `DISCLOSED_ON_DROP` members), and `docs/map/SEAM-llm-x-rules.md`.

  The seam update is REQUIRED, not optional, and was found by reading the
  seam before the subsystems (CLAUDE.md's map preflight order). That
  document's second `check:` asserts the set of names crossing
  `rules/` → `llm/` with `mods >= {...}` and `seen >= {...}` — superset
  tests, so a new `deepreason.llm.reference_menu` import from `conj.py`
  and `crit.py` passes it. What does NOT survive unattended is the
  document's own prose count, "Thirty-nine names cross the boundary",
  and its "Where it is expressed" table, which has a row for every pack
  renderer. Both move in the same commit as S4/S5.

  Two constraints that document imposes on this design, recorded here
  because discovering them at implementation time would be the expensive
  order: (a) **`AllocatedPack` must be re-applied** to any post-allocation
  suffix, or the adapter re-clips the whole prompt — which is exactly what
  S3's `artifact_alias` suffix path does; (b) bytes a rule prepends come
  out of the pack budget BEFORE rendering (`_conditioned_budget`), not
  after, which is the shape S3's pre-allocation menus follow by entering
  `_allocate_sections` as real sections.

`accept:` `python tools/docs_verify.py` (FULL, not `--fast`) → 0 failed;
`python tools/docs_verify.py --audit` → 0 refused; `python
tools/docs_verify.py --links` → 0 unresolved.

### S17 (R12, R14) — the gate

`accept:` `python -m pytest tests/ -q -n 4` → 0 failed; every phase
boundary committed and pushed with the 2s/4s/8s/16s retry.

### S18 (R7) — nothing is measured here

No CFR/EUR instrument, no new signal, no new record observable ships in
F2. Stated as an item so its absence is deliberate and checkable rather
than forgotten: R7's words are "Measure nothing here; the rematch measures
it."

`accept:` `git diff --stat origin/main -- src/deepreason/signals.py
tools/root_sweep.py` → empty.

## 4. Assumptions (operator may override)

Each resolves an open question from REQUEST.md. Every one was routed to the
record or the framework first, per `dr-ask-the-right-question`; none
survived to need operator attention, and §5 says so explicitly.

**A1 (Q1) — "every reference-bearing field" means every REGISTERED one,
and this tranche registers the census-attested set plus its free
siblings.** Assumed, operator may override. R19 settles it: "a new
reference-bearing field type gets a menu by registering, not by touching
the renderer." Registration IS the extension point, so "every" is
satisfied structurally rather than by exhaustive enumeration. Ten
declarations ship (§S1), covering all five fields that produce 737 of the
1 178 field-attributed failures.

**A2 (Q2) — `inline_threshold` is a FREE parameter of
`MenuRenderPolicy`, default 12; `maximum_entries` default 32.** Assumed,
operator may override. §2's three layers put parameter values in FREE.
32 is not invented: it is `_MAX_DIAGNOSTIC_LEGAL_HANDLES`
(`repair.py:901`) and `citable_legend`'s `maximum_blocks`
(`evidence/render.py:196`), so the menu inherits a bound the tree already
chose rather than adding a third number. 12 is chosen as the largest list
that reads as a sentence-like block rather than a table; it is a
presentation parameter with no effect on validity (§2 FROZEN (b)).

**A3 (Q3) — identity is in the SET, not the bytes.** Assumed, operator
may override. R5's stated reason is "one authority for the legal set —
never two lists kept in agreement". The authority is the set; the prompt
menu and the diagnostic are two renderings of one `legal_handles_for`
result under one policy, so truncation applies identically to both.
Byte-identity is impossible anyway — the prompt menu carries index
grammar and an omission entry that the diagnostic's `legal_handles` tuple
field cannot hold.

**A4 (Q4) — the existing token-economy mechanism is sufficient; no new
typed record.** Assumed, operator may override. R11 asks for the cost to
be "logged by the token economy and bounded", and the token economy's own
instruments are `approximate_tokens`, `_pack_section` and
`DISCLOSED_ON_DROP` (`docs/map/CON-packs-and-token-economy.md`). A new
typed record would also collide with R7 ("measure nothing here") and would
add a record observable this tranche has no reader-guardrail budget for.

**A5 (Q5) — the omission entry has two spellings, both owned by the
declaration.** Assumed, operator may override. R6's parenthetical
("write remove at `<path>`") is the REPAIR-mode spelling; a first ask has
no patch to remove from. So `ReferenceFieldDeclaration` carries
`omission_first_ask` ("leave `evidence_refs` out of this candidate
entirely") and `omission_repair` ("write a remove operation at
`/candidates/0/evidence_refs`"). One declaration owns both, so the escape
road cannot be spelled two ways by two authors — which is R5's law applied
to R6's content.

**A6 (Q6) — reuse the MODULE where a render receipt exists, the
DISCIPLINE where none does.** Assumed, operator may override. Traced, per
the skill's "a mechanism the request NAMES is a suggestion, not a
requirement — verify it actually reaches the code this change touches":
`ordered_refs` lives on `ScratchRenderReceipt` (`scratch/render.py:123`)
and is reachable only from a committed render receipt. Evidence block ids
have no receipt, so `ordered_refs` **cannot** be called for the
`citable_block` menus — this is a named mechanism that does not reach part
of the code the change touches, recorded here rather than adopted
silently. The PROPERTY R3 wants (index order, never key order) is
delivered for those menus by the same discipline and pinned by S13.

## 5. Questions for operator

**None.** Q1–Q6 all resolved above against the record or the framework.

R13 requires an explicit statement about the sibling tranches, and the
honest answer is that F2 needs neither:

- **F1 (pack criticism sections, submission path)** — F2 ADDS new sections
  to the critic packs (S5) and reads none of F1's. F2 does not touch the
  submission path. Textual adjacency in `packs.py` is a merge concern, not
  a dependency.
- **F3 (Config defaults, allocation)** — F2 adds **no `config.py` knob**.
  Its parameters live in `MenuRenderPolicy`, a registered policy artifact
  (§2 VERSIONED/FREE), which is both what R15 asks for and what keeps F2
  out of F3's blast radius. This was a real design fork and R18 decided
  it: the smaller coupling (three constants in `config.py`) loses to the
  declared interface (a policy artifact).

## 6. Out of scope (explicit)

- **Wire schema changes of any kind**, including adding an
  `insufficient_evidence` enum member as the coercion research
  recommends (`RESEARCH_STRUCTURED_OUTPUT_COERCION_2026-08-22.md`,
  recommendation 2). R8 forbids it. → PARKED.md.
- **Measuring CFR or EUR after the menu lands.** R7: "the rematch measures
  it." → PARKED.md.
- **The judge form's missing abstention** (W1 §4: 342 rulings, zero
  abstentions, no value for one) — a real finding, not requested, and a
  schema change. → PARKED.md.
- **The inert `attempt_trace[].truncated` flag** (W1 §8) — a defect, not a
  change; belongs to `deepreason-orchestrator`. → PARKED.md.
- **`run_manifest.py`** — a frozen surface, and the natural-looking home
  for a new policy. Not touched; `MenuRenderPolicy` lives in the new
  module instead.

## 7. Blast-radius census

Tool-backed, from run 2 of §1 plus the required manual cross-check for the
one `UNKNOWN` the gate said in writing it cannot judge.

`consumers.tests`, classified — every hit, none omitted:

| target | hits | classification |
|---|---|---|
| `render_conj_pack` | `test_easy.py:275,284,292`; `test_frame_render.py:337,346,368,372,488,495,502,519,522,545,549,582,600,601,604,628,645,1195,1203`; `test_harness_fixes.py:15,99,115,281`; `test_jolt_trigger_pilot.py:31,495,503`; `test_pack_prefix.py:9,107`; `test_properties.py:504,510`; `test_prose_refutation_boundaries.py:81,86`; `test_runtime_workload_integration.py:13,259` | **MUST NOT MOVE** — `reference_menus` defaults to `()`, so every existing call renders byte-identically |
| `render_batch_crit_pack` | `test_crit_batch.py:312,339,340,341`; `test_decommissioned_pipeline_stays_out.py:123`; `test_prose_refutation_boundaries.py:88,219` | **MUST NOT MOVE** — same default |
| `render_crit_pack` | `test_decommissioned_pipeline_stays_out.py:123`; `test_frame_render.py:337,351,368,378,583,1195,1207`; `test_oracle.py:763,772,829,832,842`; `test_pack_prefix.py:9,45,46,60,61,87`; `test_prose_refutation_boundaries.py:88,219,240,481` | **MUST NOT MOVE** — same default |
| `diagnostic_from_error` | `test_bridge_composition_repair.py:37,254`; `test_bridge_stage_a_v2.py:27,166,398`; `test_llm_repair_capabilities.py:13,83`; `test_v6_live_multi_pointer_repair.py:32,379` | **MUST NOT MOVE** — S6 changes where the scratch/handle list is SOURCED, not the diagnostic's shape; bridge and capability paths are untouched |
| `_handle_fields_from_error`, `_scratch_reference_guidance` | no direct test hits | **EXPECTED TO MOVE** — private, rewritten by S6; their observable behaviour is pinned through `diagnostic_from_error` above |
| `src/deepreason/rules/conj.py` | `test_frame_render.py:582` | **MUST NOT MOVE** |
| `src/deepreason/rules/crit.py` | `test_frame_render.py:583` | **MUST NOT MOVE** |
| `_pack_section` | no direct test hits | **MUST NOT MOVE** — used as-is |
| `DISCLOSED_ON_DROP` | `test_frame_render.py:488,512,545,555,557` | **EXPECTED TO MOVE** — S3 adds menu section ids to the frozenset. `:512` and `:555-557` assert on membership/withheld-notice content and are the likely movers. Manual cross-check (`grep -rn DISCLOSED_ON_DROP tests/ docs/map/`) confirms these five and `docs/map/CON-packs-and-token-economy.md:46,89,114` are the complete set |

`consumers.map_checks`, classified: **EXPECTED TO MOVE** —
`docs/map/CON-packs-and-token-economy.md` (:46 `DISCLOSED_ON_DROP`, :37-43
the section table, :131/:172 `_pack_section`), `docs/map/SUB-llm.md` (:95
the module list), `docs/map/INDEX.md` (new invariant row). **MUST NOT
MOVE** — every other map hit listed by run 1 (`SEAM-llm-x-rules`,
`SEAM-rules-x-scratch`, `SEAM-capabilities-x-rules`, `CON-schools`,
`CON-conjecture-source`, `CON-criticism-source`, `SUB-evidence`,
`SUB-scratch`, `SEAM-bridge-x-llm`, `SEAM-llm-x-workflow`,
`SEAM-periphery-x-verification`, `SUB-periphery`, `SUB-rules`,
`SUB-amendment`, `SUB-workflow`, `SEAM-*-x-rules`, `SCHEMA.md`): their
checks are on behaviour this design leaves alone, and
`tools/docs_verify.py` full mode (S16) is the instrument that decides,
not this prediction.

`consumers.qualification_digest: []` and `consumers.wheel_smoke_pins: []`
— consistent with R8's "no re-pin expected". S8 pins the schema sha so a
surprise re-pin fails the gate rather than surfacing at delivery.

## 8. Record-observable guardrails

**None required, and the reason is structural rather than an omission.**
This change adds NO data to the typed record: no new field, no new record
type, no new signal, no new finding (S18). Menus are prompt text; index
resolution runs before validation and emits nothing. Every committed root
therefore reads exactly as it did.

No sweep probe is proposed: the root sweep is RETIRED as an instrument
(operator ruling 2026-08-22, CLAUDE.md). The replacement obligation —
targeted, mutation-proven regression tests in the same tranche — is what
S14 and S8 carry.

## 9. Budget

Itemized in INSERTIONS, `tools/diff_budget.py`'s own unit, per the
correction ledgered by Rung 8's SPEC (Rungs 6 and 7 both overran by
estimating executable lines against a gate that counts docstrings,
comments and blanks).

```
$ python3 -c "
items = [
  ('S1  reference_menu.py: registry, policy, sources, resolver', 330),
  ('S2  the renderer and its grammar',                            90),
  ('S3  token accounting + truncation disclosure',                70),
  ('S4  conj pack menus + conj.py binding',                      110),
  ('S5  crit packs menus + crit.py binding',                      85),
  ('S6  repair.py sources from the interface',                    75),
  ('S7  wire.py citable-block error state',                       60),
  ('S9  index resolution in preflight',                           70),
  ('S8,S10-S15  tests/test_reference_menu.py',                   380),
  ('S16 INV-reference-menu.md + three map updates',              150),
]
print(sum(n for _, n in items), 'insertions across', len(items), 'items')
for label, n in items: print(f'{n:5d}  {label}')
"
1420 insertions across 10 items
  330  S1  reference_menu.py: registry, policy, sources, resolver
   90  S2  the renderer and its grammar
   70  S3  token accounting + truncation disclosure
  110  S4  conj pack menus + conj.py binding
   85  S5  crit packs menus + crit.py binding
   75  S6  repair.py sources from the interface
   60  S7  wire.py citable-block error state
   70  S9  index resolution in preflight
  380  S8,S10-S15  tests/test_reference_menu.py
  150  S16 INV-reference-menu.md + three map updates
```

**~1 420 insertions** as first estimated; corrected to **2 400** by measurement at stage F2-a — see Amendment 1 at the end of this document. Over the skill's ~300-line threshold, so the split
it asks for is declared here as four ORDERED, INDIVIDUALLY GATED stages,
each its own commit with its own green gate. They are stages of one
tranche rather than four REQUEST ledgers, because CLAUDE.md's cross-routing
rule is one tranche, one goal, and splitting the operator's single F2 into
four requests would fragment the authority R1–R20 all trace to.

| stage | items | insertions | delivers |
|---|---|---|---|
| **F2-a** | S1, S2, S3, S13, S15, and S12's limb 1 | ~560 | the interface, the registry, the policy, the renderer — with the customisation check green before any consumer exists |
| **F2-b** | S4, S5, S10 | ~215 | the menu on the first ask, both roles |
| **F2-c** | S6, S7, S8, S9, S11, S12 limb 2, S14 | ~400 | one authority, index replies, the mutation proof |
| **F2-d** | S16, S17, S18 | ~245 | the map, the full gate, the deliberate non-measurement |

Frozen surfaces touched: **none** (§1, run 2 CLEAR; pinned by S10).

## 10. Anti-invention pass

Re-read as a reviewer. Every item traces: S1←R1/R16/R19, S2←R1/R2/R6,
S3←R11, S4←R1/R4, S5←R1/R4, S6←R5/R10, S7←R5, S8←R8, S9←R9, S10←§1's own
disposition (a check on a claim this spec makes, not new behaviour),
S11←R16, S12←R17/R19, S13←R3, S14←R10, S15←R9, S16←R12, S17←R12/R14,
S18←R7. R20 is answered by §2 and §4 existing at all — the spec answers
the modularity law explicitly rather than merely complying with it.

Two candidates were deleted by this pass and moved to PARKED.md: a CFR
counter on the new path (R7 forbids it) and an `insufficient_evidence`
enum member (R8 forbids it).

Rubric: 6/6 yes — every R has a machine-decidable accept (R1 S1/S2/S4/S5,
R2 S2, R3 S13, R4 S4/S5, R5 S6/S7, R6 S2, R7 S18, R8 S8, R9 S9/S15,
R10 S14, R11 S3, R12 S16/S17, R13 §5, R14 S17, R15 S1, R16 S1/S11,
R17 S12, R18 §5, R19 S1/S12, R20 §2+§4); blast-radius census pasted and
every hit classified (§7); frozen-surface forecast recorded with the
tool's own lists verbatim, both runs (§1); every named mechanism traced —
`ordered_refs` reaches the scratch menus and provably does not reach the
citable-block menus (A6), `_pack_section`/`DISCLOSED_ON_DROP` reach the
pack path (S3); not a DESIGN-AND-STOP request, so Measurements/Options are
not required — the load-bearing counts in §0 are pasted from W1's
committed artifacts regardless; nothing untraceable to an R/C number (§10).

---

## Amendment 1 — the budget ceiling was wrong, measured at stage F2-a

Recorded at the F2-a commit rather than at the commit that would have
tripped it, because a ceiling discovered by breaking it is a ceiling that
already failed to do its job.

**What was measured.** `tools/diff_budget.py 4760a32ef --ceiling 1420
--paths src/deepreason tests docs/map` at the end of stage F2-a:

```
{"result_type": "DIFF_BUDGET_RESULT_V1", "base": "4760a32ef",
 "areas": {"src/deepreason": 706, "tests": 339, "docs/map": 142},
 "total_insertions": 1187, "ceiling": 1420, "verdict": "WITHIN"}
```

Stage F2-a was itemized at 490 src insertions (S1 330 + S2 90 + S3 70) and
landed 706. **Measured ratio 1.44**, on the first stage of four, with
1 187 of a 1 420 ceiling already spent.

**Why, stated so it is not repeated a fourth time.** This is the same
error `docs/ERRATA.md`-adjacent Rungs 6 and 7 both made (759 against 560;
1 027 against 700) and that Rung 8's SPEC corrected by switching the unit
to insertions. Switching the UNIT was necessary and not sufficient: this
spec estimated in insertions and still under-counted, because the estimate
was made against machinery while the file is roughly half docstring and
comment — which this repo's conventions require, and which
`diff_budget.py` counts. The correction is to the RATIO, not the unit.

**The revised ceiling, derived rather than wished.** Remaining itemization
at the original estimate: src S4 110 + S5 85 + S6 75 + S7 60 + S9 70 =
400; tests ~250; map ~120.

```
$ python3 -c "print(1187 + round(400*1.44) + round(250*1.44) + round(120*1.44))"
2266
```

**New ceiling: 2 400 insertions** (2 266 plus a 6% margin), replacing
1 420. Every later `[COMMIT]` step checks against 2 400.

**What this does NOT mean.** No scope moved. The four stages, the eighteen
spec items and the ten declarations are exactly as specified; the
Out-of-scope list is unchanged and nothing left PARKED.md. The overrun is
in explanatory prose inside files the spec already named, not in machinery
the spec did not name — which is the distinction a sprawl ceiling exists
to police, and it is why this is recorded as a corrected estimate rather
than as a scope change.
