# Validation for: reference grounding — the model chooses handles from a menu

Run against `78db79251` (branch `claude/rebuild-f2-reference-menu-i94dq9`),
tranche base `4760a32ef`. Every command below was run; every output is
pasted from the real run.

## Acceptance checks

S1 (R1, R16, R19) — the interface, registry and policy
`python -m pytest tests/test_reference_menu.py -q` → `39 passed in 0.42s`
`python -c "...REFERENCE_FIELD_DECLARATIONS..."` → `registry: 10
declarations, keyed by field_id` : **PASS**

S2 (R1, R2, R6) — the rendered menu, omission at index 0
`-k "omission_is_entry_zero or index_grammar or long_list_is_the_same_grammar"`
→ `4 passed, 35 deselected in 0.04s` : **PASS**

S3 (R11) — the token economy, bounded and disclosed
`-k "truncation_is_disclosed or menu_tokens_are_counted or
menu_sections_are_exact_and_mandatory"` → `3 passed, 36 deselected in 0.04s`
: **PASS**
*(mechanism corrected from the spec's — see Deviations D1.)*

S4 (R1, R4) — the menu reaches the conjecturer's first ask
`-k "conj_pack_carries_the_menu_on_the_first_ask"` → `1 passed, 38
deselected in 0.05s` : **PASS**

S5 (R1, R4) — the same for the critic
`-k "batch_crit_pack_carries_the_menu"` → `1 passed, 38 deselected in
1.67s` : **PASS**

S6 (R5, R10) — the diagnostic sources from the same authority
`-k "menu_and_diagnostic_are_one_set or consumes_the_resolver"` → `2
passed, 37 deselected in 0.04s` : **PASS**

S7 (R5) — the two `block` fields gain a legal-set owner
`-k "block_field_diagnostic_lists_legal_blocks or
batch_critic_block_diagnostic"` → `2 passed, 37 deselected in 0.07s`
: **PASS**

S8 (R8) — the wire schema does not move
`-k "wire_schema_sha_does_not_move"` → `1 passed, 38 deselected in 0.07s`
: **PASS**

S9 + S15 (R9) — a seat replying by index resolves to the right handle
`-k "index_reply_resolves or index_zero_takes_the_omission or
index_grammar_never_shadows_a_legal_handle or seat_replying_by_index"` →
`4 passed, 35 deselected in 0.08s` : **PASS**

S10 (§1) — the reuse claim is pinned
`-k "the_reused_modules_are_not_modified"` → `1 passed, 38 deselected in
0.05s` : **PASS**
*(form corrected from the spec's — see Deviations D2.)*

S11 (R16 FROZEN (b)) — a menu never decides validity
`-k "a_menu_never_changes_what_is_valid"` → `1 passed, 38 deselected in
0.19s` : **PASS**

S12 (R17, R19) — the customisation check, both limbs
`-k "a_new_field_gets_a_menu_by_registering or
consumers_reach_the_legal_set_only_through_the_interface"` → `2 passed, 37
deselected in 0.07s` : **PASS**

S13 (R3) — index order, not key order
`-k "menu_order_is_index_order_not_key_order"` → `1 passed, 38 deselected
in 0.04s` : **PASS**

S14 (R10) — the mutation proof
`grep -c FAILED proof/s14_forked_red.txt` → `1`;
`grep -c "2 passed" proof/s14_unforked_green.txt` → `1` : **PASS**
The forked run's FAILED line is
`test_the_diagnostic_consumes_the_resolver_rather_than_agreeing_with_it`.
Recorded in `proof/README.md`: under the fork, the SET-EQUALITY test still
passes. Set equality samples; it cannot establish that there is one list.

S16 (R12) — the map moves in the same commits : **PASS** (see Map below)

S17 (R12, R14) — the gate : **PASS** (see Full gate below)

S18 (R7) — nothing is measured here
`git diff --stat 4760a32ef..HEAD -- src/deepreason/signals.py
tools/root_sweep.py src/deepreason/config.py` → **empty** : **PASS**

## Full gate

`python -m pytest tests/ -q -n 4` →
`4214 passed, 6 skipped in 762.85s (0:12:42)` : **PASS**

**The first gate run failed, and the failure was a real defect rather than
a fixture that needed updating.**
`tests/test_semantic_freedom_constitution.py::
test_offline_semantic_freedom_baseline_is_measurable` failed on
`tokens_per_admitted_useful_candidate` moving 784.5 → 875.0, with every
epistemic metric that fixture records identical. The tempting reading —
"menus cost tokens, update the baseline" — was wrong: the post-allocation
menus were appended OUTSIDE the `active_v6` guard, so a pre-v6 run received
a menu for `optional_refs`, a field its own form does not have. Gating both
menu builds on `active_v6` restored the fixture EXACTLY. **No fixture was
weakened**, and the guard ships with a mutation-proven regression test
(`test_a_pre_v6_conjecture_pack_carries_no_v6_menu`; forcing the guard true
turns it red, verified).

That fixture was NOT in SPEC §7's blast-radius census. Recorded as a census
miss with its generalizable lesson in SPEC Amendment 2.

## Frozen-surface diff

```
$ git diff --stat 4760a32ef..HEAD -- \
    src/deepreason/capabilities/state.py src/deepreason/harness.py \
    src/deepreason/invariants.py src/deepreason/run_manifest.py \
    src/deepreason/qualification.py
(no output)
```

**Empty. PASS.** The R3-named reuse modules are likewise byte-unchanged:

```
$ git diff --stat 4760a32ef..HEAD -- \
    src/deepreason/scratch/render.py src/deepreason/evidence/render.py
(no output)
```

`tools/blast_radius.py` was run at every `[COMMIT]` step against
`4760a32ef` and returned `frozen_surface_verdict: CLEAR`,
`frozen_surface_contacts: []`, `frozen_adjacent_contacts: []` and no
`newly_dead`/`newly_live` reachability drift, every time.

## Record-behavior preservation

**n/a, and the reason is structural rather than an omission.** This change
adds NO data to the typed record: no new field, no new record type, no new
signal, no new finding (S18, empty diff above). Menus are prompt text; index
resolution runs before validation and emits nothing. No reader or validator
of the append-only record was touched — `invariants.py` and
`verification/` are byte-unchanged — so no committed root's `verify_root`
verdict can have moved.

The root sweep is RETIRED as an instrument (operator ruling 2026-08-22,
CLAUDE.md). Its replacement obligation — targeted, mutation-proven
regression tests in the same tranche — is carried by S8 (schema pin,
mutation-proven), S14 (one authority, mutation-proven), S3 (truncation
disclosure, mutation-proven) and the pre-v6 guard (mutation-proven).

## Map

- `python tools/docs_verify.py` → `65 documents, 1085 checks, 4 workers` /
  `docs_verify: 0 failed` : **PASS**
- `python tools/docs_verify.py --audit` → `0 finding(s)` : **PASS**
- `python tools/docs_verify.py --links` → `0 dangling reference(s), 65
  document(s)` : **PASS**
- `python tools/docs_verify.py --coverage` → `7 seam(s) swept, 17 without a
  Sweep: header, 2 finding(s)` : **PASS, pre-existing.** Proven rather than
  asserted: the tool was re-run on the tranche base `4760a32ef` and returned
  the IDENTICAL line — `7 seam(s) swept, 17 without a Sweep: header, 2
  finding(s)`. The two findings are
  `SEAM-schools-x-scratch.md: enforcement site not named:
  src/deepreason/informal/trial.py` and one other on the same sweep; neither
  touches this tranche's files. → PARKED.md is not the right home for a
  pre-existing map gap that no requirement names; recorded here.
- `python tools/docs_verify.py --stale` → `37 document(s) worth re-reading`.
  Judged one by one:
  - **`SUB-llm.md`, and the six other documents this tranche EDITED**
    (`INV-reference-menu`, `SUB-periphery`, `SEAM-llm-x-rules`,
    `SEAM-rules-x-scratch`, `INDEX`, `CON-packs-and-token-economy`):
    **UPDATED.** Each document's own `Verify:` command was re-run before
    its stamp moved, then advanced to `d40d3de3e` (checklist step 36).
  - **`SUB-rules.md`: DISMISSED, with reason.** This tranche changed files
    it owns (`rules/conj.py`, `rules/crit.py`) but no claim it makes: its
    subject is the epistemic moves, and the agreement that moved — what
    those two rules put in a pack — is `DR-SEAM-llm-x-rules`', which was
    updated in the same commit as the behaviour. A stale stamp is honest;
    a false one is not, so it was not advanced.
  - **The remaining 30 entries** name commits that PRE-DATE this tranche
    (`SUB-evidence` ← P4, `SUB-harness` ← the seat-bindings rung,
    `SUB-manifest` ← the Config-knobs rung, `SUB-workflow` ← the defended-
    trial wiring, and so on). Not this tranche's to answer, and not
    silently ignored: they are listed here so the next reader sees they
    were looked at.
- **New checks added by this change:** `docs/map/INV-reference-menu.md`
  carries nine `check:` lines, all new and all naming tests that did not
  exist before this tranche. `SEAM-llm-x-rules.md` gains a `-eq` count
  check on the names crossing the boundary and an updated firewall-adjacency
  regex; `SEAM-rules-x-scratch.md` gains a check that no critic menu can
  carry scratch content; `SUB-llm.md` and `CON-packs-and-token-economy.md`
  each gain one. Every one would fail if the behaviour it names regressed.
- **Record observables added vs sweep probes:** none added, so none owed
  (S18's empty diff is the proof, not the claim).
- **Wheel smoke:** the packaging surface did not move and the smokes were
  run anyway, because R8 predicted no re-pin and a prediction is worth
  checking:
  `wheel smoke passed: isolated V6-only contents, clean imports, exact entry
  points, module parity, MCP registration, and exact MCP schemas` (rc 0);
  `wheel operational smoke passed: installed setup, explicit qualification
  (80 qualification calls; 416 total calls), readiness, question-only
  reasoning, replay-verified terminal retrieval, cache reuse, opaque MCP
  restart, budget ceiling, and pre-V6 fail-closed admission` (rc 0). No pin
  moved : **PASS**

## Deviations from SPEC.md, each corrected in writing

**D1 (S3) — menu sections are EXACT and MANDATORY, not droppable.** The
spec specified `droppable=True` plus `DISCLOSED_ON_DROP` membership. That
pairing is forbidden by `DR-CON-packs-and-token-economy`'s NEGATIVE rule,
which carries its own exhibiting check: a droppable section that is also
exact is admitted on its `min_tokens` and then rendered at full source size,
overshooting the budget with no accounting signal. `docs_verify` went RED
on it. Menus are now `droppable=False, compressible=False`, which is the
only pairing that neither compresses the truncation notice out of a menu's
tail nor drops the menu leaving no header, and it is affordable because the
menu is bounded at `MenuRenderPolicy.maximum_entries`. `DISCLOSED_ON_DROP`
is left byte-unchanged. **The map caught a defect in the spec's own
mechanism, before it shipped.**

**D2 (S10) — a structural pin, not a byte pin.** The spec asked for a test
asserting three files byte-identical to the base commit. That test would go
RED the day a later, unrelated tranche edits `invariants.py` legitimately,
which violates the durability rule (fail only when the guarded claim stops
being true). The durable claim is read-only reach, and that is what the test
asserts. The tranche-scoped byte proof is recorded at
`proof/s10_reused_modules_unchanged.txt` and re-pasted under
Frozen-surface diff above.

**D3 (S6/S19) — the binding test is a CONSUMPTION test.** The spec's
divergence test (menu set == diagnostic set) PASSED on the unrefactored
tree, because two independently maintained lists agree on every fixture
their authors thought of. Both tests ship; the consumption test is the one
that holds R5, and the mutation proof demonstrates the asymmetry.

**D4 (S9) — `omission_scope` was added to the declaration.** Not foreseen
by the spec. Dropping `evidence_refs/*/block` alone leaves a `{quote}` with
no block — a legal escape turned into a fresh validation failure — so a
declaration now states whether an omission removes the key or the object
containing it.

**D5 (S9) — index resolution runs AFTER the control-field firewall.**
`DR-SEAM-llm-x-rules` pins the firewall-before-validation adjacency, and
the first implementation put resolution upstream of it. Resolution reads
model output, so it belongs downstream of the firewall that exists to stop
model output becoming process authority. The seam's pinned regex was
updated and gained a row saying why.

## Requirement sweep

| R | demonstrated by |
|---|---|
| R1 legal handle set rendered adjacent to the field | S1, S2, S4, S5 |
| R2 short inline, long as an indexed table selected by index | S2 (`long_list_is_the_same_grammar_as_a_short_one`) |
| R3 reuse the render-receipt handle-map indexing, compare by `ordered_refs` | S13 + S10 (the reuse test asserts `ordered_refs` IS still called); A6 records that it provably cannot reach the citable-block menus |
| R4 the menu moves to the FIRST ask | S4, S5 |
| R5 the repair diagnostic's list is identical to the menu shown | S6, S7, S14 |
| R6 omission is a menu entry, spelled concretely | S2 (`omission_is_entry_zero_where_legal`); both spellings owned by the declaration |
| R7 measure nothing here | S18 — empty diff against `signals.py`, `root_sweep.py`, `config.py` |
| R8 no wire schema shape changes | S8, mutation-proven; both wheel smokes green with no pin moved |
| R9 a seat replying by index resolves to the right handle | S9, end-to-end through the real contract |
| R10 the menu and the diagnostic derive from ONE source, mutation-proven | S14, with `proof/README.md` |
| R11 token cost logged by the token economy, bounded, truncation disclosed | S3 |
| R12 full gate 0 failed; docs_verify full; map in the same commits | Full gate 4214/0; docs_verify 0 failed / 0 audit / 0 dangling; every map edit rode its behaviour's commit |
| R13 STOP if F1's or F3's work is needed | Neither was needed and it is proven, not asserted: `git diff` against `config.py` is empty (S18), and F2 adds no criticism section — its parameters live in `MenuRenderPolicy`, a registered artifact |
| R14 commit and push every phase boundary | Six commits pushed: REQUEST, SPEC+PARKED, CHECKLIST, F2-a, F2-b, F2-c, F2-d, stamps |
| R15 every knob reachable as configuration or a registered artifact | S1 + S12 — `MenuRenderPolicy` and `REFERENCE_FIELD_DECLARATIONS`; **no `config.py` knob and no code edit is needed to customise anything** |
| R16 declared interface on the signal-contract pattern | S1, S11 — three layers stated in `INV-reference-menu.md` and the FROZEN clause made failable |
| R17 an architecture test that goes RED when a consumer bypasses the interface | S12 limb 2 + S6's consumption test, whose RED is demonstrated in `proof/s14_forked_red.txt` |
| R18 at a design fork, the interface wins | Exercised twice and recorded: the policy artifact was chosen over three `config.py` constants; `scratch_existing` was made a separate handle KIND rather than a flag on the declaration |
| R19 the menu renderer is an interface keyed by field kind | S12 limb 1 — a synthetic field whose name appears nowhere in `src/` gets a correct menu by registering |
| R20 SPEC.md answers the modularity law explicitly | SPEC §2 (the three layers) and §4/§5 (the fork R18 decided), both written before implementation |

**Every R demonstrated. None deferred.**

## Assumptions carried (operator may override)

- **A1** "Every reference-bearing field" means every REGISTERED one; this
  tranche registers the census-attested set plus its free siblings (ten
  declarations covering all five fields behind 737 of 1 178 field-attributed
  failures). Registration is the extension point R19 names.
- **A2** `inline_threshold` 12 and `maximum_entries` 32 are FREE parameters.
  32 is inherited from `_MAX_DIAGNOSTIC_LEGAL_HANDLES` and
  `citable_legend`'s own cap rather than invented.
- **A3** "Identical" is identity of the SET, not of the bytes: one
  `legal_handles_for` result rendered for two readers.
- **A4** The existing token-economy mechanism suffices; no new typed record.
- **A5** The omission entry has two spellings (first-ask and repair), both
  owned by the declaration.
- **A6** `ordered_refs` is reused as a MODULE where a render receipt exists
  and as a DISCIPLINE where none does — evidence block ids have no receipt,
  so `ordered_refs` provably cannot be called for them. Recorded rather than
  adopted silently, per the named-mechanism rule.
- **A7** (added during execution, D4) An omission's SCOPE is declared per
  field: "self" drops the key, "parent" drops the containing object.

## Budget

`python tools/diff_budget.py 4760a32ef --ceiling 2400 --paths src/deepreason
tests docs/map` →
`{"areas": {"src/deepreason": 1123, "tests": 1140, "docs/map": 242},
"total_insertions": 2505, "ceiling": 2400, "verdict": "EXCEEDED"}`

**EXCEEDED by 105 insertions (4.4%).** Itemized and disposed in SPEC
Amendment 2; raised to the operator as a decision in the delivery message,
not absorbed silently. All 105 are defect-driven work inside files the spec
already named — no scope moved, nothing left PARKED.md, and the
Out-of-scope list is unchanged.

## Verdict: **PASS**

Every acceptance check passes with pasted output; the full gate is
4 214 passed / 0 failed; the frozen-surface diff is empty; the map is
0 failed, 0 audit findings, 0 dangling links; every requirement R1–R20 is
demonstrated and none deferred.

The budget verdict is EXCEEDED and is carried into delivery as an open
decision for the operator. It is not a validation failure: no acceptance
check, gate, or requirement is unmet by it.
