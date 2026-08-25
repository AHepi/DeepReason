# PARKED — Rung 8

Noticed and NOT fixed here. Each entry is one line of WHAT plus a
ready-to-send prompt, so the follow-up costs the operator a paste rather than
an authoring session. Nothing on this list was in Rung 8's scope.

## P1 — the IAF target-scoped edge-relevance diagnostic (R14's park half)

**What.** `experiments/2026-08-22-measure-grounded-flip-rate/` measured that a
whole-graph stability certificate is worthless on this corpus (97.71 % of
candidate edges relevant; `k = 0` on 0 of 96 roots) while a SEED-TARGETED one
carries real information (96.15 % of candidate spurious edges irrelevant to the
seed; `k = 0` for deletions on 18 of 20 roots). Rung 8 rows the recommendation
and parks the build. Two reasons, both stated in SPEC.md §3 D2: it is a SEARCH
rather than a formula over the window, estimated 250–350 insertions on top of a
tranche already at its ceiling; and the measurement's own caveat — re-run the
battery on post-Rung-7 roots before finalizing — is unpaid, so building first
would validate a design on graphs 76 of whose 96 have an EMPTY attack relation.

**Prompt:**

> Route through `dr-change-orchestrator`. GOAL, in two parts, in this order.
> (1) PAY THE CAVEAT FIRST, and it is a battery run rather than a code change:
> re-run `cache_graphs.py`, `battery_a.py`, `battery_b.py`, `battery_c.py` and
> `analyze.py` in `experiments/2026-08-22-measure-grounded-flip-rate/` against
> the CURRENT committed root corpus, which now includes the roots Rungs 5, 6, 7
> and 8 produced. Report the same three numbers that carried the original Rung 8
> decision — single-edge stability mass, seed-question stability, and the share
> of flips escaping the Dung attack cone — plus the new share of roots whose
> attack relation is non-empty, which is the number that decides whether the
> corpus can support the design at all. (2) ONLY IF the refreshed seed-targeted
> numbers still look like a certificate that fires: scope a target-scoped
> edge-relevance diagnostic as a SEVENTH §14-style signal — "of N uncertain
> edges, k are relevant to the seed question" — over the fixed sequence-number
> window `capture/diagnostics.py::window` already defines, declared through
> `DR-REC-add-signal`, canonically rounded like the six, and bounded by an
> explicit candidate-space cap with `overrun` semantics (it is a SEARCH, not a
> formula, and an unbounded one breaks Prop 12.1). DO NOT build the uncertain-
> edge layer over `dep`: the measured exposure is there, but Dung's framework
> does not model support and that is a separate operator scope decision.
> JUDGE ON `battery_c_relevance.json`'s own table, never on prose.

## P2 — `blast_radius.py`'s symbol tier fires on generic English words

**What.** Running the Rung 8 disclosure gate with the two new capture modules
and their natural symbol names returned `frozen_surface_verdict: CONTACT` with
eleven `frozen_surface_contacts` and one `frozen_adjacent_contact` — every one
of them a `SYMBOL_INDIRECT` hit on the words `mode`, `window`, `step` and
`diagnostics` appearing somewhere in `harness.py`, `invariants.py`,
`run_manifest.py`, `qualification.py` and `llm/firewall.py` for entirely
unrelated reasons. The tool says so itself in every `detail` string
("grep-based; not proof of semantic contact"), and semantic contact was
DISPROVED by direct measurement in the same session:

```
$ for f in capabilities/state.py harness.py invariants.py run_manifest.py \
           qualification.py llm/firewall.py; do grep -c "from deepreason.capture" $f; done
0  0  1  0  0  0
$ grep -n "from deepreason.capture" src/deepreason/invariants.py
4094:        from deepreason.capture.detection import raw_flags     <- pre-existing, untouched
$ grep -rln "capture.diagnostics\|capture.hysteresis" src/ tests/
src/deepreason/capture/diagnostics.py  src/deepreason/capture/hysteresis.py
tests/test_capture14_diagnostics.py    tests/test_capture14_hysteresis.py
```

This is not a false alarm that costs a shrug. `dr-execute-step` makes any
unforecast `frozen_surface_contacts` entry a STOP, and the whole point of that
rule is that a real contact is never outrun — a verdict that returns eleven
false entries for one ordinary tranche is the condition under which a twelfth,
real one gets skimmed past. The 2026-08-09 incident this gate was built for was
exactly a stop that was written and not obeyed.

**Confirmed by controlled comparison, in the same session.** The tranche's FULL
final file list, with DISTINCTIVE symbol names, returns exactly one contact —
the pre-authorized `run_manifest.py` one — and zero name-collision entries:

```
$ python tools/blast_radius.py --files <all 15 changed src files> \
    --symbols authority_audit promotion_rent slice_budgets \
              promotion_conditioning stream_contraction exogenous_grounding_ratio \
    --against 462d6091d
verdict: CONTACT
DIRECT contacts: [run_manifest.py]        <- the one SPEC.md section 1 named
SYMBOL_INDIRECT count: 0
frozen_adjacent: 0
```

Same tree, same base, MORE files declared — and the eleven contacts vanish. The
variable is the symbol names alone: `mode`, `window`, `step`, `diagnostics`
against `authority_audit`, `promotion_rent`, `slice_budgets`. So the tier's
output is a function of how ordinary an author's vocabulary is, which is not a
property of the change.

**Prompt:**

> Route through `deepreason-orchestrator`. GOAL: one bounded tranche — make
> `tools/blast_radius.py`'s `SYMBOL_INDIRECT` tier discriminate, so a CONTACT
> verdict means something. REPRODUCE FIRST, from
> `experiments/2026-08-25-change-rung8-rent-audit-diagnostics/PARKED.md` P2:
> `python tools/blast_radius.py --files src/deepreason/capture/hysteresis.py
> src/deepreason/capture/diagnostics.py --symbols step mode slice_budgets
> diagnostics window --against 462d6091d` returns eleven frozen contacts and
> one frozen-adjacent contact, and every one is a bare-word grep hit. The
> semantic truth — no frozen file imports either module — is three greps away
> and the tool does not take them. CANDIDATE FIXES, cheapest first: resolve a
> declared symbol to its DEFINING module and report a contact only when a
> frozen file imports that module or references the qualified name; or keep the
> grep tier but return it under a separate `symbol_name_collisions` key that is
> NOT part of `frozen_surface_verdict`, so the verdict stays a claim about
> contact. DO NOT simply lower the tier's severity: the tier exists because a
> real indirect contact is the one the author does not see. END STATE: a
> regression test built from THIS tranche's exact invocation, asserting it
> returns no frozen-surface contact, plus one built from a genuinely contacting
> change asserting it still does — the mutation proof the tool's own README
> standard asks for.

## P3 — `Provenance.event_seq` is 0 on every artifact in the tree

**What.** `Provenance` carries an `event_seq` field, it defaults to 0, and
almost no caller sets it — measured during Rung 8 on five freshly registered
conjectures, all five reading 0. Any consumer that reads it as "when was this
registered" gets a silently wrong answer that never raises. Rung 8's criticism
debt was one line from being that consumer; it now derives age from the events
inside the age floor instead, and ships
`test_the_age_floor_actually_discriminates` to fail against the vacuous
version. What is NOT done is auditing every OTHER reader of the field.

**Prompt:**

> Route through `dr-audit-orchestrator`, dimension `broken`. GOAL: a
> census of every read of `Provenance.event_seq` in `src/`, each classified as
> (a) the writer sets it at this call site, so the read is sound; (b) the read
> tolerates 0; or (c) the read treats 0 as a real sequence number and is
> therefore wrong. Evidence that class (c) exists: Rung 8 measured five
> freshly-registered conjectures all reporting `event_seq = 0`
> (`experiments/2026-08-25-change-rung8-rent-audit-diagnostics/PARKED.md` P3).
> Report the census as a table in AUDIT_REPORT.md with a ready-to-send fix
> prompt per class-(c) finding. FIX NOTHING — the audit family never fixes.

## P4 — the SPEC-estimate / diff-budget unit mismatch, THIRD occurrence

**What.** Rung 6 overran (759 against 560) and Rung 7 overran (1027 against
700), both because the SPEC estimated EXECUTABLE lines while
`tools/diff_budget.py` counts INSERTIONS. Rung 7 parked it as its own P4. Rung 8
estimated in insertions from the start, using Rung 7's measured 1.90 ratio —
and still overran on the single largest new module (`capture/diagnostics.py`:
470 against 350), because the ratio is not constant: a module whose comments
carry constraints rather than narration runs richer than one that does not.
Three tranches, three overruns, one cause. `authoring-skills`'s E1 tripwire is
TWO recorded failures of a recipe before a dedicated instrument is built; this
is past it.

**Prompt:**

> Route through `dr-change-orchestrator`. GOAL: make a tranche's size estimate
> checkable BEFORE the code is written, not after. Three recorded overruns with
> one cause: Rung 6 (759/560), Rung 7 (1027/700, parked as its own P4), Rung 8
> (`capture/diagnostics.py` 470 against a 350 estimate derived from Rung 7's own
> measured 1.90 insertion/executable ratio). SMALLEST CANDIDATE, and price it
> against the alternatives before choosing: teach `tools/diff_budget.py` a
> `--forecast <n>` mode that records the SPEC's per-item estimate alongside the
> realised insertions per file, so the ratio becomes a measured series instead
> of a number each tranche re-guesses; then have `dr-spec-change` require the
> forecast be stated per FILE rather than per item. DO NOT raise the ceilings:
> the ceiling is doing its job — it is the estimate that is not.
