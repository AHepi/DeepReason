# PARKED — found while building this experiment, fixed by nobody here

Scope contract: *"Anything you notice that is broken but not requested: into
`PARKED.md`. Never fix it now."* Each entry is one line of WHAT, then a
ready-to-send prompt, so the follow-up costs the operator a paste.

---

## F1 — the operator's own plugin directory is never loaded by a run

**What.** `load_operator_plugins` is the only loader for
`<DEEPREASON_HOME>/seat_plugins/`, and it has no call site anywhere under
`src/`: seven tests call it and nothing else does. So a `.py` or `.tmpl` file
an operator puts in that directory is registered during the test suite and
never during `deepreason reason`.
`DR-REC-add-a-section-plugin` step 2 tells an operator to put a file there and
step 4 tells them to select it; between those two steps the file is never
read. This tranche supplied the call from its own rig
(`rig/sitecustomize.py`), which is why arm A3 could run at all.

```
Route: dr-change-orchestrator.
Goal: a section plugin or .tmpl the operator places in
<DEEPREASON_HOME>/seat_plugins/ is registered by an ordinary `deepreason
reason` run, so DR-REC-add-a-section-plugin's four steps work end to end
without an experiment rig.
Evidence: `grep -rn "load_operator_plugins" src/` returns exactly one line,
its own definition at src/deepreason/llm/seat_sections.py:558; every other
hit is under tests/. experiments/2026-09-04-experiment-brief-variation-step1/
rig/armrig.py had to call it directly for arm A3.
Watch: the loader is explicitly "disclose, never die" — its notices must reach
the run's record rather than stderr, or a plugin that failed to load is a
brief silently missing a section. Frozen surfaces: check the call site's
package against DR-INV-frozen-surfaces before designing.
End state: a test that puts a .tmpl in a temp home, runs the managed path, and
finds the section in the rendered brief and its notices in the record.
```

## F2 — a NEW seat pack layout cannot be registered without Python

**What.** `DEEPREASON_SEAT_PACK_LAYOUT` selects a layout by id, but only the
two ids `seat_layouts.py` hard-codes are ever in the registry. There is no
file, flag or environment road that ADDS one, so
`DR-REC-add-a-section-plugin` step 3 ("Register a layout that includes it")
has no non-code road, and step 4 can only ever re-select what already ships.
The recipe's own closing check asserts that adding a SECTION needs no source
edit; adding the LAYOUT that carries it does.

```
Route: dr-change-orchestrator.
Goal: an operator can register a seat pack layout from their own directory —
the same trust boundary as a .py plugin — so DEEPREASON_SEAT_PACK_LAYOUT can
select an arrangement that is not one of the two shipped ones, with no code
edit.
Evidence: register_seat_pack_layout is reachable only from Python;
seat_pack_layout_ids() returns exactly the two ids seat_layouts.py registers.
experiments/2026-09-04-experiment-brief-variation-step1/rig/armrig.py builds
its five arm layouts in-process for exactly this reason.
Watch: this is the modularity law's "customisation needs to be easy" clause,
and its enforcement clause too — the architecture test should go red when a
customization point requires a code edit to use. F1 and F2 are the same gap
seen from two sides and are probably one tranche.
End state: a layout declared in a file under <DEEPREASON_HOME> is selectable
by id, with a typed refusal (never a silent fallback) when it does not parse.
```

## F3 — the template channel cannot reach a computed section's content

**What.** A `.tmpl` sees `SectionRequestV1.supplied` and nothing else. Nine of
the conjecturer's sections compute their content inside the plugin from state
and blobs, and `dr.neighbourhood` is one of them: `supplied["accepted"]`
carries artifact IDS, and the distilled claim beside each id is computed in
the plugin. So a template can re-format a computed section only by DROPPING
its content. That is what arm A3 measures, and `PREREG.md` §3.4 says so before
the numbers.

```
Route: dr-change-orchestrator.
Goal: an operator can change the FORMAT of a computed section without losing
its content — the operator's R9 ("same information, different shape") made
reachable for the nine sections whose content is computed rather than supplied.
Evidence: llm/seat_sections.py::_template_plugin builds its context from
request.supplied only; llm/packs.py:793 shows supplied["accepted"] is a tuple
of ids; the A3 diff in
experiments/2026-09-04-experiment-brief-variation-step1/PROVE_ARMS.txt shows
two ids-with-claims becoming four bare ids.
Watch: the obvious road — let a template call the plugin's own helpers — walks
straight through the trust boundary that keeps templates unable to execute.
The likely shape is the opposite: a plugin publishes its computed values INTO
supplied under a declared key, and the template formats those.
End state: a .tmpl re-formats the neighbourhood with every claim still in it,
and a test proves the same artifact ids and claim texts appear under both the
shipped plugin and the template.
```

## F4 — the history tranche's SPEC S10 default is cited as shipped and is not

**What.** `SPEC.md` S10 of `experiments/2026-09-03-change-provenance-history-
channel/` reads "Conjecturer: history ON by default", and the operator's
amendment 3 to this tranche cites it as "the shipped default". That
directory's `CHECKLIST.md` line 3 reads "State: NOT STARTED", and it has no
`VALIDATION.md` and no `DELIVERY.md`. Nothing from that SPEC has shipped; the
tree's actual behaviour is history OFF (`superseded_summary_n = 0` in both
registered arrangements). No code is wrong. What is wrong is that a reader —
including the operator — cannot tell a specified default from a shipped one by
reading the tranche.

```
Route: dr-change-orchestrator (documentation), or an ERRATA entry alone.
Goal: a reader of a tranche's SPEC can tell whether its decisions shipped.
Evidence: that CHECKLIST.md's own line 3, the absent VALIDATION/DELIVERY, and
this tranche's PREREG.md §3.1, which had to establish it by reading source.
End state: docs/ERRATA.md carries the correction, and the SPEC's S10 heading
says SPECIFIED, NOT SHIPPED.
```
