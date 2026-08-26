<!-- DR-INV-reference-menu -->
Verified-at: 4760a32ef
Verify: python -m pytest tests/test_reference_menu.py -q
Owns: src/deepreason/llm/reference_menu.py
Seams: DR-SEAM-llm-x-rules, DR-SEAM-rules-x-scratch
Seams-undocumented: evidence x llm

# The reference menu — one authority for every legal handle set

## What it is

A reference-bearing field is one whose value must NAME something that
already exists: an evidence block id, a scratch handle, an artifact alias.
Across 54 committed roots the harness recorded 1 178 diagnostics that name
a field, and **737 of them — 62.6% — are a handle the model made up**
(`experiments/2026-08-26-run-anatomy-program/W1-form-census/RESULTS.md`
§2). The models were not failing to reason inside the form; they were
failing to point at things.

This module is the fix's shape rather than the fix's content. It declares
which fields reference a handle, resolves each field's legal set through
ONE function, and renders that set as a menu the model selects from. The
prompt menu and the repair diagnostic are two renderings of one resolution,
so they cannot drift apart.

Ledgered at `experiments/2026-08-26-change-f2-reference-menu/`.

## Why a menu rather than better instructions

Because the record already measured what instructions buy. The repair
diagnostic told seats, in words, that omission was legal — 257 times. In
**255 of them the seat invented a handle anyway** (CFR 99.2%). Of 120
repair ladders that offered an escape, 7 took it (EUR 5.8%).

The contrast in the same census is the design argument: `claim_class` on
the bridge contracts offers `unknown` **inside the enum**, and models take
it (6 of 85, 10 of 55). Where an escape lives in the vocabulary it is
taken; where it lives only in instruction text it is not. So the omission
form is a MENU ENTRY at index 0, not a sentence.

`check: python -m pytest tests/test_reference_menu.py -k "omission_is_entry_zero" -q`

## The three layers (the signal-contract pattern, DR-INV-signal-contract)

Operator design law, 2026-08-26 (CLAUDE.md, "Operator design laws"): "There
needs to be a priority that enforces modularity. Customisation needs to be
easy."

| Layer | What it holds | What it takes to change it |
|---|---|---|
| **FROZEN** | (a) one resolver per field, consumed through the interface by both the menu and the diagnostic; (b) a menu is PRESENTATION, never validity; (c) no silent truncation | an operator design law |
| **VERSIONED** | `REFERENCE_FIELD_DECLARATIONS` and `MenuRenderPolicy` | registering a declaration / revising the policy — never a renderer edit |
| **FREE** | `inline_threshold`, `maximum_entries`, `excerpt_chars` inside declared envelopes | ordinary configuration |

### FROZEN (b) is the clause to guard hardest

A menu changes what the model is SHOWN. It may never change what the
harness ACCEPTS. This is the harness's oldest invariant — measures never
adjudicate — wearing the menu's clothes, and it is the exact analogue of
the signal contract's "allocation touches EFFICIENCY, NEVER EVIDENCE".

The check empties the registry, which removes every menu and every index
resolution, and demands the validators return identical verdicts over a
corpus that includes a legal handle, a malformed one, an unknown alias and
a wrong-case handle. A menu that started admitting or rejecting anything
goes red.

`check: python -m pytest tests/test_reference_menu.py -k "a_menu_never_changes_what_is_valid" -q`

### FROZEN (a): one authority, and why two lists is the failure mode

`legal_handles_for` is the only function that answers "what may this field
contain". Before this module, `wire.py` attached the scratch namespace to a
validation error and `repair.py` independently re-derived a legal list from
it, while the prompt showed a third thing — three copies of one fact. Two
copies is how a registry stops being a contract (E26's law, the same
reasoning that collapsed the two run paths into one).

**Set equality is not enough to hold this, and the tranche measured why.**
Two independently maintained lists agree on every fixture their authors
thought of; a test asserting the menu's set equals the diagnostic's set
passes unchanged when the two are forked apart (the mutation proof at
`experiments/2026-08-26-change-f2-reference-menu/proof/`). So the binding
check is a CONSUMPTION check: divert the resolver to a sentinel and demand
the diagnostic follow it. A consumer re-deriving the set locally cannot.

`check: python -m pytest tests/test_reference_menu.py -k "menu_and_diagnostic_are_one_set or consumes_the_resolver" -q`

### FROZEN (c): truncation is disclosed inside the menu text

A menu longer than `maximum_entries` is cut, and the cut is announced in
the rendered text itself rather than alongside it — so no consumer can
separate the menu from the fact that it is partial. This is
`DR-CON-packs-and-token-economy`'s no-silent-caps rule applied to a new
section family.

`check: python -m pytest tests/test_reference_menu.py -k "truncation_is_disclosed" -q`

## Customisation is a check, not a claim

A new reference-bearing field gets a menu by appending a
`ReferenceFieldDeclaration`; a new source of handles gets one by
registering a `LegalHandleSource` under a new kind. **The renderer is not
edited in either case.** The check registers a synthetic declaration for a
field name that appears nowhere in `src/` and demands a correct menu for
it, so a renderer that hard-codes field names or handle kinds goes red.

`check: python -m pytest tests/test_reference_menu.py -k "a_new_field_gets_a_menu_by_registering" -q`

The other half of "enforced" is that consumers may not reach around the
interface. An AST scan of `packs.py` and `repair.py` fails the day either
stops consuming the resolver — the move `repair.py` made before this module
existed.

`check: python -m pytest tests/test_reference_menu.py -k "consumers_reach_the_legal_set_only_through_the_interface" -q`

## Index order, never key order

Menu entries are emitted and compared by INDEX: 1, 2, ..., 10, 11. A
key-sorted implementation yields 1, 10, 11, 2 and fails the check below.

This is CLAUDE.md's ledgered `ordered_refs` invariant generalized. Where a
render receipt exists — the scratch namespace — the module calls
`ScratchRenderReceipt.ordered_refs`, which is that invariant's own
accessor. Evidence block ids have no render receipt, so `ordered_refs`
cannot be called for them and the same discipline is applied directly; the
module never iterates a handle mapping's `.values()`.

`check: python -m pytest tests/test_reference_menu.py -k "menu_order_is_index_order_not_key_order" -q`

## The wire schema does not move

This layer is prompt rendering and validation-message sourcing. No property
is added, removed or re-typed on any contract: a seat replying by index is
resolved to a handle BEFORE validation, so the schema the model reads is
the schema that was already there, and the citable-block set a contract
carries is diagnostic sourcing that `model_json_schema` never reads. The
check builds each touched contract's schema with and without that set and
pins the canonical sha equal.

`check: python -m pytest tests/test_reference_menu.py -k "wire_schema_sha_does_not_move" -q`

An index token can never shadow a legal handle, because no field's own
grammar admits one: block ids are `^[0-9a-f]{12,64}$`, scratch handles are
`^(?:SCR|NEW)_[0-9]{3,}$`, artifact aliases are `A<n>`/`SRC_<nnn>`. The
check asserts that over every registered declaration, so a future field
whose handles are bare integers turns it red — which is the correct
outcome: such a field must not use index replies.

`check: python -m pytest tests/test_reference_menu.py -k "index_grammar_never_shadows_a_legal_handle" -q`

## Where to change what

| To do this | Edit | Test |
|---|---|---|
| give a new field a menu | `REFERENCE_FIELD_DECLARATIONS` | `tests/test_reference_menu.py -k registering` |
| add a new SOURCE of handles | `register_handle_source` at import | `tests/test_reference_menu.py -k registering` |
| change how long a menu may be | `MenuRenderPolicy` | `tests/test_reference_menu.py -k truncation` |
| change the omission wording | the declaration's `omission_first_ask` / `omission_repair` | `tests/test_reference_menu.py -k omission` |
| change WHAT IS LEGAL | not here — the wire validators own validity | `tests/test_reference_menu.py -k never_changes_what_is_valid` |

## Traps

- **A menu is not an enum.** `optional_refs` already carried a schema enum
  (`_bind_alias_array`) and still produced 64 invented-handle rejections in
  the census. Adding a value to a schema is not the same act as putting it
  in front of the model at the point of choice; do not treat one as
  evidence for the other.
- **The alias table does not exist when the pack is rendered.**
  `aliases_for_pack` derives from the RENDERED pack, so an
  `artifact_alias` menu can only be appended after allocation — and any
  post-allocation append must be re-wrapped in `AllocatedPack`, or the
  adapter re-clips the whole prompt (`DR-SEAM-llm-x-rules`).
- **CFR's denominator moves with the fix.** The census measures coerced
  fabrication only where the record ANNOUNCED an escape. A menu that
  prevents the rejection also removes the diagnostic the measure counts, so
  a fall in CFR is not by itself evidence that fabrication stopped. Say
  which of numerator and denominator moved
  (`experiments/2026-08-26-change-f2-reference-menu/PARKED.md` P2).
