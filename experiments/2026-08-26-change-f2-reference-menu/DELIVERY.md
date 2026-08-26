# Delivered: reference grounding — the model chooses handles from a menu

Branch: `claude/rebuild-f2-reference-menu-i94dq9` (pushed, tree clean).
Tranche base `4760a32ef`. Tranche F2 of the REBUILD program.

## What changed

Across 54 committed run roots, 62.6% of every failure the record can pin on
a field is a reference handle the model made up — 737 of 1 178 diagnostics —
and when the record explicitly told a seat that leaving a field out was
legal, the seat invented a handle anyway 255 times out of 257. This tranche
stops asking seats to remember handles and starts showing them the list.

A new module, `src/deepreason/llm/reference_menu.py`, owns the single answer
to "what may this reference-bearing field contain". Ten declarations cover
all five fields behind those 737 failures plus their free siblings. The
prompt now carries a REFERENCE MENU next to each such field, listing the
legal handles by index, with the omission form as entry `[0]` where leaving
the field out is legal — the escape road as something to select rather than
advice to follow. A seat may answer with the handle or with `[2]`, and the
index resolves to the handle before validation, so the form the model reads
is unchanged.

The same resolver feeds the repair diagnostic. Before, `wire.py` attached
the scratch namespace to a validation error, `repair.py` independently
re-derived a list from it, and the prompt showed a third thing — three
copies of one fact. The two evidence-block fields, which produce 373 of the
737, had no legal-set owner anywhere in the tree; both contracts now carry
one.

Touched: `llm/reference_menu.py` (new), `llm/packs.py`, `llm/repair.py`,
`llm/wire.py`, `rules/conj.py`, `rules/crit.py`,
`tests/test_reference_menu.py` (new, 39 tests),
`docs/map/INV-reference-menu.md` (new) and six existing map documents.

Proven by: full gate **4 214 passed, 6 skipped, 0 failed**; `docs_verify`
full **1 085 checks, 0 failed**, `--audit` 0 findings, `--links` 0 dangling;
both wheel smokes green with no pin moved; the frozen-surface diff empty.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "every wire-contract field that references a handle gets its LEGAL HANDLE SET rendered adjacent to the field in the prompt" | done-with-assumption **A1** | `d6a771467`, `2a4b8edd6`; VALIDATION S1/S2/S4/S5 |
| R2 | "short lists inline, long lists as an indexed table the field selects from by index" | done | `d6a771467`; VALIDATION S2 |
| R3 | "reuse it, compare by ordered_refs per the ledgered invariant" | done-with-assumption **A6** | `d6a771467`; VALIDATION S13 + S10 |
| R4 | "The menu moves to the FIRST ask." | done | `2a4b8edd6`; VALIDATION S4/S5 |
| R5 | "guaranteed identical to the menu shown (one authority… never two lists kept in agreement)" | done-with-assumption **A3** | `b9ed880db`; VALIDATION S6/S7/S14 |
| R6 | "the menu's first entry IS the omission form, spelled concretely" | done-with-assumptions **A5**, **A7** | `d6a771467`, `b9ed880db`; VALIDATION S2 |
| R7 | "Measure nothing here; the rematch measures it." | done | VALIDATION S18 — empty diff vs `signals.py`, `root_sweep.py`, `config.py` |
| R8 | "prompt rendering + validation sourcing only. NO wire schema shape changes" | done | `b9ed880db`; VALIDATION S8, mutation-proven; both wheel smokes, no pin moved |
| R9 | "a seat replying by index resolves to the right handle" | done | `b9ed880db`; VALIDATION S9, end-to-end through the real contract |
| R10 | "the menu and the diagnostic derive from ONE source (mutation-prove…)" | done | `b9ed880db`; `proof/s14_forked_red.txt`, `proof/README.md` |
| R11 | "the menu's token cost is logged by the token economy and bounded… no silent caps" | done-with-assumption **A4**; **deviation D1** | `2a4b8edd6`; VALIDATION S3 |
| R12 | "Full gate 0 failed; docs_verify full; map moves in the same commits" | done | VALIDATION Full gate + Map |
| R13 | "If you need the pack's criticism sections (F1's) or Config defaults (F3's), STOP and say so" | done — **neither was needed, and it is proven** | `git diff` vs `config.py` empty; F2 adds no criticism section. Its parameters live in a registered policy artifact, which is what R18's fork rule selected |
| R14 | "Commit and push every phase boundary (retry 2s/4s/8s/16s)" | done | Nine pushes: REQUEST, SPEC+PARKED, CHECKLIST, F2-a, F2-b, F2-c, F2-d, stamps, VALIDATION |
| R15 | "reachable as CONFIGURATION or a REGISTERED VERSIONED ARTIFACT — if customizing it would require editing code, the design is wrong" | done | VALIDATION S1 + S12; **no `config.py` knob and no code edit customises anything** |
| R16 | "a DECLARED INTERFACE on the signal-contract pattern" | done | `docs/map/INV-reference-menu.md`'s three-layer table; VALIDATION S1/S11 |
| R17 | "an ARCHITECTURE TEST that goes RED when a consumer bypasses the interface" | done | VALIDATION S12 limb 2 + S6's consumption test; its RED is demonstrated, not asserted, in `proof/s14_forked_red.txt` |
| R18 | "the interface wins — the operator has priced this and chosen" | done | Exercised twice and recorded: the policy artifact over three `config.py` constants; `scratch_existing` as a separate handle KIND over a flag on the declaration |
| R19 | "a new reference-bearing field type gets a menu by registering, not by touching the renderer" | done | VALIDATION S12 limb 1 — a synthetic field whose name appears nowhere in `src/` gets a correct menu by registering |
| R20 | "Amend your REQUEST.md with it as a requirement and let SPEC.md answer it explicitly" | done | REQUEST.md Amendment A1 (captured verbatim before SPEC existed); SPEC §2 and §4/§5 |

**Twenty of twenty done. None deferred, none not-done.**

## Assumptions the operator may override

- **A1** "Every reference-bearing field" means every REGISTERED one. Ten
  declarations ship, covering all five census-attested failing fields;
  registration is the extension point R19 asked for, so "every" is satisfied
  structurally rather than by enumeration.
- **A2** `inline_threshold` 12, `maximum_entries` 32 — FREE parameters. 32 is
  inherited from the diagnostic's existing cap and `citable_legend`'s, not
  invented.
- **A3** "Identical" means identity of the SET, not of the bytes.
- **A4** The existing token-economy mechanism suffices; no new typed record.
- **A5** The omission entry has two spellings — first-ask and repair — both
  owned by the declaration, so one escape road cannot be spelled two ways.
- **A6** `ordered_refs` is reused as a MODULE where a render receipt exists
  and as a DISCIPLINE where none does. Evidence block ids have no render
  receipt, so `ordered_refs` provably cannot be called for them; recorded
  rather than adopted silently.
- **A7** An omission's SCOPE is declared per field ("self" drops the key,
  "parent" drops the containing object). Added during execution: dropping a
  nested handle alone leaves its composite malformed.

## Five deviations from SPEC, each forced by evidence

1. **Menu sections are EXACT and MANDATORY, not droppable.** The map's own
   NEGATIVE rule forbids droppable-and-exact — such a section is admitted on
   its `min_tokens` then rendered at full size, overshooting the budget with
   no accounting signal. `docs_verify` went red on the spec's mechanism.
   **The map caught a defect in the design before it shipped.**
2. **The reuse pin is structural, not byte-wise.** A byte pin on
   `invariants.py` would fail the day a later unrelated tranche edits it
   legitimately — a test that fails for a reason other than its own claim.
3. **The one-authority test is a CONSUMPTION test.** Set equality passed on
   the unrefactored tree; two independently maintained lists agree on every
   fixture their authors thought of.
4. **`omission_scope` was added** (A7 above).
5. **Index resolution runs downstream of the control-field firewall**, so
   the step that reads model output sits after the firewall that exists to
   stop model output becoming process authority.

## Map delta

- **created:** `docs/map/INV-reference-menu.md` — nine `check:` lines, all
  new, all naming tests that did not exist before this tranche.
- **changed:** `SEAM-llm-x-rules.md` (crossing-name count corrected and
  pinned with `-eq`; firewall-adjacency regex updated; two rows added),
  `SEAM-rules-x-scratch.md` (both `AllocatedPack` counts 3→4, and the
  criticism-gets-no-scratch refusal re-established for the new parameter),
  `CON-packs-and-token-economy.md` (menus as a section family),
  `SUB-llm.md`, `SUB-periphery.md` (a check that was stricter than its own
  claim, tightened), `INDEX.md`.
- **new checks:** 14 across those documents. `docs_verify` full: 1 085
  checks, 0 failed; `--audit` 0 findings.
- **left stale:** `SUB-rules.md`. This tranche changed files it owns but no
  claim it makes; the agreement that moved is `DR-SEAM-llm-x-rules`', updated
  in the same commit as the behaviour. A stale stamp is honest; a false one
  is not. The other 30 `--stale` entries name commits that predate this
  tranche and are listed in VALIDATION.md so the next reader sees they were
  looked at.
- **`--coverage`:** 2 findings, 17 seams without a `Sweep:` header —
  IDENTICAL at the tranche base, proven by re-running the tool there. Not
  this tranche's.

## Errata

**E55** — `SEAM-llm-x-rules.md` said "Thirty-nine names cross the boundary"
while the tree carried FORTY at the tranche base, before this tranche
touched anything. The document's own check asserts `seen >= {...}`, a
SUPERSET test, which structurally cannot fail on an addition — so the number
could drift upward indefinitely with every check green. `SCHEMA.md` already
states the rule this violated ("counts are claims… pin it with `-eq`").
Corrected in place with an equality check that fails in both directions.

## Budget — an open decision for the operator

`diff_budget` reports **2 505 insertions against the 2 400 ceiling — over by
105, 4.4%.** Itemized in SPEC Amendment 2: the `omission_scope` discovery
(~35), the `active_v6` guard and its regression test (~45), and the critic
scratch guard (~40). All three are defect-driven work inside files the spec
already named. No scope moved, nothing left PARKED.md, and the Out-of-scope
list is unchanged.

Two of the three were invisible to the blast-radius census, and one of them
is the kind the census exists to catch — `test_semantic_freedom_constitution`
names no target symbol; it reaches the pack through the conjecture rule and
pins a token cost. This is the third consecutive recorded instance of that
class, so Amendment 2 records the generalizable lesson: a change that adds
bytes to any pack should census on pinned-metric fixtures, not only on
callers.

## Parked (not done, not promised)

Four entries in `PARKED.md`, each with a ready-to-send prompt:

- **P1 — the judge and critic forms cannot say "I don't know."** 342 rulings,
  zero abstentions, because the enum has no value for one; 15 of 1 453
  asserted attacks carry no case text. A wire schema change, which R8
  forbade here.
- **P2 — measure CFR and EUR after the menu lands.** R7 reserved this for the
  rematch. Its prompt carries the warning that matters: a menu that prevents
  the rejection also removes the diagnostic the measure counts, so a fall in
  CFR's denominator is the expected first-order effect and is not by itself
  evidence that fabrication stopped.
- **P3 — `attempt_trace[].truncated` is inert.** False on all 3 155 attempts
  while the record's own diagnostics report truncation 52 times. A defect,
  so it routes to the other family.
- **P4 — a legal sentinel handle instead of omission.** Deliberately gated on
  P2's numbers; its prompt says so in its first line.

**Recommended next: P2.** It is the only one that tells anyone whether this
tranche worked. F2 shipped a structural defense and, on R7's instruction,
measured nothing; until the rematch runs, the honest statement is that the
menu is present and correct, not that it changed what seats do.
