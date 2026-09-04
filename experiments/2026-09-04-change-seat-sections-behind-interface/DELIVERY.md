# DELIVERY — the nine caller-computed brief sections move behind the
# seat-section interface

Phase: `dr-deliver-change`. Date: 2026-09-04.
Base: `main` at `0f6bf2c854`. Branch: `claude/seat-sections-interface-d4vjqe`.
`VALIDATION.md` verdict: PASS.

---

## §1 What shipped, in one paragraph

Every section the conjecturer seat is shown is now computed outside the
admission code. A new package, `deepreason.seat_sources`, holds a registered,
versioned SOURCE layer: a source reads the state and the record, computes one
value, appends nothing, and hands the value to the plugin that formats it.
Thirteen sources ship — the nine contexts `rules/conj.py` used to compute, and
the four insertions it used to make after allocation — assembled by a registered
bundle across five stages, each stage boundary an act the interface may not
perform. `conj` hands over the state a source may read and takes the values
back; it names no section, imports no pack type, and calls no content renderer.
Both seats' default briefs render byte-for-byte what they rendered before.

## §2 Gate and instruments

| instrument | result |
|---|---|
| `python -m pytest tests/ -q -n 4` (alone) | **4982 passed, 6 skipped, 0 failed** |
| both goldens | 15 passed, no fixture touched |
| `tools/blast_radius.py` over the actual diff | **CLEAR**, no contacts, no drift |
| `python tools/docs_verify.py` (alone) | 6 failed, every one a C4 baseline row |
| `--links` | 0 dangling, 79 documents |
| `--audit` | 1 finding, the pre-existing C4 unparseable check |
| `tools/diff_budget.py --paths src --ceiling 1600` | 1452, **WITHIN** |

## §3 Requirement-by-requirement reconciliation

Authority is `REQUEST.md` — the operator's verbatim window.

| R | the operator's words | where it landed | honest status |
|---|---|---|---|
| R1 | "the nine brief sections still computed inside the admission code move behind the seat-section interface" | `seat_sources/shipped.py`, nine sources | **DONE** |
| R2 | "no section a seat is shown is COMPUTED inside rules/" | the conjecturer's thirteen | **DONE for the conjecturer; NOT for the critic** — four contexts remain in `rules/crit.py`, parked as P1 with the price. §5. |
| R3 | "a registered SOURCE layer beside the plugins ... registered and versioned like a plugin, writes nothing" | `seat_sources/registry.py` | **DONE, with one disclosed write** — §4.2 |
| R4 | "Decide, in SPEC.md, whether a source may READ the log" | `SPEC.md` §3 | **DONE**: yes for reading, never for appending, one declared write |
| R5 | "prove the 'never appends' clause with an architecture test that goes red on a planted write" | `tests/test_seat_section_sources.py` | **DONE**, dynamically and statically, nine plants between them |
| R6 | "both seats' goldens must pass untouched" | unchanged fixtures | **DONE** |
| R7 | "the existing shape-buys-nothing test still passes" | `tests/test_seat_section_architecture.py` | **DONE**, and extended to the new layer's types and names |
| R8 | "a NEW test proves rules/conj.py no longer imports or constructs any pack section type" | two tests, not one | **DONE, WIDENED** — §4.3 |
| R9 | "Mutation-prove both." | `VALIDATION.md` §3 | **DONE**, with one plant that did not fire and why |
| R10 | "SCOPE: the nine A6 sections and the three appended after allocation" | thirteen, not twelve | **DONE, ONE ITEM WIDER**, disclosed at spec time — §4.1 |
| R11 | "P4 and P5 stay parked unless the same source layer makes one of them a one-step registration — if so, say so in PARKED.md with the price" | `PARKED.md` P2, P3 | **DONE**: neither became one-step; both re-checked rather than assumed, and P3's price is recorded as REDUCED with the line to add to its prompt |
| R12 | "forecast NO CONTACT; run blast_radius over the planned targets before code and paste the verdict in SPEC.md" | `SPEC.md` §6 | **DONE**: forecast NO CONTACT, instrument returned CONTACT on one row, row opened and disposed, actual diff CLEAR |
| R13 | "a new record object kind IS (surface 2) and is a STOP for a grant" | `SPEC.md` §2 S1.6 | **DONE by not doing it**: receipts stay in memory; parked as P4 |
| R14 | "full gate alone, 0 failed, nothing weakened; docs_verify FULL; map moves in the same commit" | §2 above | **DONE**; three tests re-pointed, none weakened, each shown to still bite |
| R15 | "FINAL MESSAGE: plain words..." | the chat reply | **DONE** |
| R16 | read CLAUDE.md in full; load the four skills | — | **DONE** |
| R17 | read the starting point in full | `SPEC.md` §0 map preflight | **DONE** |

## §4 The four things worth reading before the next tranche

**1. The scope is one item wider than R10's sentence, on purpose.** R10 names
"the three appended after allocation". The covering seam document names FOUR
post-allocation re-wraps: three appends and one substitution (the v6 scratch
render replacing its canonical text). The substitution moved too, because R2's
sentence is false while a section's final bytes are computed in `rules/`, and
because leaving one re-wrap behind would split the `AllocatedPack` rule across
two modules — the exact shape its own trap warns about. Disclosed in `SPEC.md`
§5 before any code, not discovered afterwards.

**2. "Writes nothing" is true except for one declared write, and the exception
is stated rather than hidden.** `pack_dossier` materialises the excerpts it
selected into the content-addressed blob store before its receipt can name them,
so the frozen-evidence value cannot exist without it. A source may write blobs
only if it declares `writes_blobs`; exactly one does, and the architecture test
fails if any other source leaves a file behind. A blob put appends no event,
assigns no status and moves no digest. The clause the operator asked to be
proven — never APPENDS — is proven whole.

**3. R8's test as literally worded would have passed before this tranche.**
`rules/conj.py` never imported `PackSection`; what it did was compute the nine
CONTENTS and hand them over as strings. The test therefore has two halves: no
pack-section type imported or constructed (which now bites, because
`AllocatedPack` was imported and used four times), and no call to any of the
nine content renderers (which is the half that measures this tranche). Both are
mutation-proven.

**4. `blast_radius` forecast NO CONTACT and returned CONTACT.** One
`SYMBOL_INDIRECT` row: `'conj'` referenced in `invariants.py`. Opened rather
than waved past, and it does not survive: `invariants.py` imports nothing from
`rules`, calls no bare `conj(...)`, uses no `.conj` attribute, and its single
bare-word `conj` is inside the string literal `"conj-noregister"` — an event
input tag. Over the ACTUAL diff the verdict is CLEAR. No grant was requested and
none was needed.

## §5 What is not done, and what it would cost

The critic still computes four contexts in `rules/crit.py`. Three of the four
are sources this tranche already registers; the blocker is that its two
`render_crit_pack` call sites deliberately supply DIFFERENT SUBSETS — the
atomic-decomposition fallback passes the frame halves and not the premise
invitation, because a batch that exhausted its schema is criticising targets it
never invited premises for. One bundle would supply all four at both sites and
change the bytes of the second. Fixing it needs a per-call subset selector on
the bundle: a protocol addition made for one caller, which is how a protocol
acquires a feature nobody has used. Priced and prompted in `PARKED.md` P1.

## §6 Parked, each with a ready-to-send prompt

| id | what |
|---|---|
| P1 | the critic's four caller-computed contexts (new) |
| P2 | the batch criticism renderer — re-checked, NOT made one-step by this layer |
| P3 | the four seats with hardcoded briefs — price REDUCED, one line to add to its prompt |
| P4 | the source receipts into the record — frozen surface 2, one grant would serve two parked items |
| P5 | the scratch substitution's failure path is shaped by the caller — an observation with a bias against action, no prompt |

## §7 Defects: none new

Nothing in this tranche introduced a defect. Two instrument results that LOOK
like defects and are not, both reproduced and disposed in `VALIDATION.md` §1:
two `tests/test_mcp_run.py` failures under `-n 4` while `docs_verify` competed
for the same cores (a ledgered flaky set, green in serial re-run and green in
the boundary gate run alone), and one `docs_verify` TIMEOUT row under the same
contention (absent when run alone).
