# Delivered: Rung D — proof debt (E-1). Duhem localization (E-2) parked.

Branch: `claude/calculus-rungd-debt-localization-6c3u9w`, pushed, tree clean.
Tranche base `b10fc5fd2`. 13 commits. 1296 insertions against a ledgered
ceiling of 1480 — `verdict: WITHIN`.

## What changed

A derived judgment can now carry an itemized bill of what it rests on, and that
bill is something a critic can attack. Concretely: `poietic.derivation-manifest.v1`
is an ordinary registered artifact holding three kinds of item —
`KERNEL_CHECK` (deterministic checks the harness re-runs), `OPEN_CERTIFICATES`
(registered artifacts the judgment leans on but has not proved), and
`AXIOM_DEBT` (named axioms it assumes and does not prove). `register_fail_warrant`
gained one optional keyword, `manifest_ref`, which mounts that manifest on the
verdict's validity node as EVIDENCE.

That single ref role is the whole mechanism. `adjudication/edges.py` already
walked the dependence lineage beneath an EVIDENCE ref, so attacking any open
certificate now attacks the validity node, and the existing validity-node
closure disables every carrier of the warrant *before* the grounded pass — the
target reinstates in pass one rather than by any later check. **Not one line of
`adjudication/` changed.**

The receipt itself is never stored. `proof_debt.receipt(harness, warrant_id)`
rebuilds it from replayed state on every call, re-running each runnable kernel
check rather than reading its recorded verdict back, and reporting a
non-runnable one as `not-rerunnable` rather than as a pass. That split is also
why "dependents are invalidated on recomputation rather than retroactively"
needed no invalidation machinery at all: nothing rewrites a past event.

The first live producer is the demarcation rent sweep. Its second reading rests
on a variator SAMPLE that until now lived only in a trace blob — readable, and
inert, so "your sample was unrepresentative" had nowhere to land. The sweep now
registers the sampled variants as a `premise-rent-sample.v1` artifact and files
a manifest naming it as the one open certificate. Attacking the sample
reinstates the premise and un-marks its problem by the same computed predicate
that marked it.

Files: `src/deepreason/proof_debt.py` (new, 264 lines),
`calculus/claims.py`, `calculus/compiler.py`, `calculus/programs.py`,
`calculus/__init__.py`, `programs.py`, `rules/warrants.py`, `premises.py`;
`tests/test_proof_debt.py` (new, 18 tests). 457 insertions in `src/`, and its
4 deletions are one reworded comment, two extended import lines and one
extended docstring line — no behaviour removed.

**The closed claim-name set did not grow.** `poietic.derivation-manifest.v1`
was already declared in `CLAIM_SCHEMAS`; this rung supplied its producer,
exactly as Rung 4 did for frame assertions. `len(CLAIM_SCHEMAS) == 9` before
and after.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "Route through dr-change-orchestrator; the workflow's own stops apply" | **done** | capture → spec → plan → 28 steps → validate → deliver; the step-13 stop fired and was honoured |
| R2 | "the spec phase owns the design" | **done** | `b37fabc7c`; SPEC.md §0–§5 |
| R3 | "AUTHORITY: LADDER.md 'Rung D' IN FULL … plus the source docs it cites" | **done** | `89ad4bba8`; REQUEST.md quotes the section, the E-1/E-2 rows and R58 verbatim |
| R4 | "a receipt format — KERNEL_CHECK / OPEN_CERTIFICATES / AXIOM_DEBT — … itemized and ATTACKABLE, with dependents invalidated on recomputation" | **done** | `b5958ced8`, `ef6a95de3`, `7fc5929db`; VALIDATION S1, S2, S4, S5, S7 |
| R5 | "THE FIRST DESIGN QUESTION … is answered in SPEC.md with reasons, not assumed" | **done-with-assumption A1** | SPEC.md §1 rules out render decisions, labels and measures, each with its reason |
| R6 | "Start narrow; a small scope delivered beats a wide one specced" | **done** | one producer; every other `register_fail_warrant` site byte-unchanged (VALIDATION S11) |
| R7 | "bundle-level problematicity projects to a member ONLY through a standing localization criticism" | **deferred** — *"option B — deliver D1 now, park D2"* | PARKED.md P1 |
| R8 | "REUSE src/deepreason/premises.py's shape … rather than re-deriving it" | **deferred** with R7 | carried verbatim into PARKED.md's prompt as constraint (a) |
| R9 | "blame assignment is NEVER automatic … no measure, no default, no cascade" | **deferred** with R7 | carried verbatim into PARKED.md's prompt as constraint (b) |
| R10 | "receipts recompute from the log (derived, never stored)" | **done** | `7fc5929db`; VALIDATION S5, S6, S7 |
| R11 | "a localization is attackable and its defeat un-implicates the member" | **deferred** with R7 | PARKED.md P1 |
| R12 | "no label moves from a receipt or localization alone" | **half done** (receipt half), **deferred** (localization half) | `bf759de2c`; VALIDATION S20 — behavioural plus an AST guard that the read path holds no writing call and never imports `adjudication` |
| R13 | "MUTATION PROOF on the non-automatic constraint" | **deferred** with R7 | carried verbatim into PARKED.md's prompt as constraint (c). NOT run: its subject `implicated()` does not exist, and a mutation proof with no subject proves nothing |
| R14 | "Axiom ledger: name what this rung PROVES and PRESERVES" | **done** | `6721010d0`; PROVES `A1`/`A2` in the receipt's form; PRESERVES `A3`, `A5` at the manifest, `A9`, `A10`, `Ax 4.1`; does NOT answer for `A5` at the localization, and the `A5` row says so |
| R15 | "FROZEN SURFACES: forecast none beyond Config knobs" | **done** | frozen-surface diff empty; and no `Config` knob was added at all, so no `_versioned_source_config_data` line is owed (A5) |
| R16 | "ledger a ceiling at plan time and STOP if exceeded" | **done** | ceiling 1480 ledgered at `b37fabc7c`, checked at every commit — and it fired at step 13. The requirement working is the proof |
| R17 | "If SPEC shows D1+D2 cannot fit … deliver D2 … and park D1" | **superseded by R20** | REQUEST.md Amendment 1 records why: R17 presupposed the conflict surfacing before either half was written; it surfaced with D1 finished and gated |
| R18 | "ring while iterating; full gate at the boundary; docs_verify full. Map moves in the same commits" | **done** | 13 commits, each pushed; map moved in the same commit every time; two full gates |
| R19 | "Deliver R-by-R with pasted PROOF, closing with one line each" | **done** | this document |
| R20 | "option B — deliver D1 now, park D2" | **done** | this document + PARKED.md |
| R21 | "the answer is to park, not to raise the ceiling … one tranche, one goal" | **done** | the ceiling was not raised; final 1296/1480 |
| R22 | "Close out D1 through validate and deliver as-is" | **done** | `d2732ea70` VALIDATION.md PASS; no D1 code touched after the ruling |
| R23 | "write D2's park with a ready-to-send prompt that inherits the committed SPEC §D2 items, the premises.py-shape constraint, and the never-automatic mutation-proof requirement" | **done** | PARKED.md P1's prompt carries all three as named constraints (a), (b), (c) |
| R24 | "a future window should start at dr-plan-steps, not re-spec" | **done** | the prompt says so in its first paragraph: "your first artifact is CHECKLIST.md, not SPEC.md" |
| C1 | "`python -m pytest`, never bare pytest" | **held** | every pasted command |
| C2 | "Read CLAUDE.md in full; load dr-drive-harness, dr-explain-to-operator" | **held** | — |
| C3 | "if you find yourself editing llm/ or provider profiles, STOP" | **held** | `git diff --stat b10fc5fd2..HEAD -- src/deepreason/llm/` is empty; the STOP never needed to fire |
| C4 | baselines: 0 failed, 3 docs_verify failures, 5 MCP flaky | **held** | gate 3875/0 (delta +18 = this tranche's test file); 3 pre-existing docs failures; no MCP flake across two full runs |
| C5 | parallel windows | **held** | no shared file touched |
| C6 | branch discrepancy in SETUP | **held** | worked on `-6c3u9w` throughout, as REQUEST.md recorded at capture |

**No requirement is `not-done`.**

## Assumptions the operator may override

- **A1** — receipt scope is attack-producing derived judgments only; labels, measures and render decisions are out, each with its reason in SPEC.md §1.
- **A2** — the manifest is a registered artifact and the receipt is the derived view.
- **A3** — a bundle is an artifact that DEPENDS on its members. **Untested in code** — it is the parked half's premise, and it carries into PARKED.md unproven.
- **A4** — the ceiling was 1480. It was reached, and you ruled rather than the number deciding.
- **A5** — no `Config` knob added, so no `_versioned_source_config_data` line owed.
- **A6** — `receipt()` ships with no CLI or MCP reader; its only consumer today is the gate.

## Map delta

**Created (1):** `docs/map/CON-proof-debt-and-localization.md` — the design
agreement for both channels, written BEFORE the code, with its localization
half explicitly marked DESIGNED, PARKED.

**Changed (7):** `INDEX.md`, `SUB-calculus.md`, `CON-warrants-and-attacks.md`,
`CON-problem-layer-lifecycle.md`, `INV-axiom-basis.md`,
`SEAM-evaluation-x-ontology.md`, `SUB-evaluation.md`, plus
`SEAM-evaluation-x-rules.md` at step 28.

**New checks: 15**, every one run before being written down. Two guard against
future drift rather than present behaviour: a check asserting
`deepreason.localization` does NOT exist (so the parked document fails rather
than lies if someone builds it without updating it), and one asserting
`KernelCheckV1` never becomes a decodable claim (the back door through which the
closed set would widen).

**Left stale: none of this tranche's.** `docs_verify --stale` lists three
documents — `CON-run-identity.md`, `SEAM-llm-x-scheduler.md`,
`SUB-scheduler.md` — all naming commits from other tranches (`bce018ae5`,
`8469d0669`) and touching no file this change went near.

**Two architectural pins in the map caught real first-draft violations**, and
both pins were right: `premises.py` must not import the calculus substrate, and
`rules/warrants.py`'s top-level imports stay `{deepreason.ontology}`. Neither
was weakened; both fixes are better code than what they replaced.

## Errata

**`docs/ERRATA.md` E45** — added in this commit. This tranche's own SPEC.md
blast-radius census classified per FILE and so put two exact-set map pins under
a wholesale "MUST NOT MOVE" that they did not obey. The tree was right and the
classification was wrong; both pins were correctly updated in the same commit
as the code. Recorded because the shape recurs — this is its third instance in
this program — with the narrower correctable lesson: a census row naming a FILE
must be expanded to the CHECKS in that file before it is classified, and any
check asserting `==` against a literal set is EXPECTED TO MOVE by default.

## Parked (not done, not promised)

**P1 — Duhem localization (drift row E-2), the whole of D2.** No
`localization.py`, no `poietic.localization.v1` producer, no `implicated()`,
and — the part that matters — no guard test against the automatic version.
Its design is committed and authenticated in
`CON-proof-debt-and-localization.md` and SPEC.md §D2, and
`poietic.localization.v1` is already in the closed name set, so a resuming
window supplies a producer rather than growing the ontology.

The live risk while it is parked, stated plainly: because bundle membership is
readable off `dep`, the automatic projection — "the bundle fell, so implicate
everything under it" — is one line away, and nothing in the tree stops it
today. That is a known absence, recorded in the concept document's Traps.

Its ready-to-send prompt is `PARKED.md` P1, ~90 lines, carrying SPEC §D2's
items, the `premises.py`-shape constraint, the never-automatic constraint and
the mutation-proof requirement as named constraints (a), (b), (c), and routing
the window to `dr-plan-steps` rather than re-spec.

**Recommended next: P1.** Not because E-2 is urgent, but because its cost is
lowest now and rises: the design is fresh, authenticated, and its entry
artifact is committed, so the next window skips capture and spec entirely. The
one item worth your attention before it runs is A3 — "a bundle is an artifact
that depends on its members" is the parked half's load-bearing premise and is
the one assumption this tranche did not get to test.
