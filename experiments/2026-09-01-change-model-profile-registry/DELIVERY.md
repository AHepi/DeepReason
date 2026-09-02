# Delivered: "Take this particular task out of the hands of the machine"

Branch: `claude/model-profile-registry-opkgal` (pushed, tree clean)

## What changed

A model's settings are now a document a human writes, and the harness reads it.

The harness used to carry one constant, `REASONING_OFF = "none"` in
`llm/providers.py`, and `llm/split.py` sent it to every model on every
extraction leg. That constant is gone, along with the predicate that compared
against it. In its place: `src/deepreason/model_profiles/`, which reads one
Markdown document per model — `$DEEPREASON_HOME/model-profiles/<model-id>/agent.md`
— and answers two questions the code used to answer for itself: what the
emission leg should send, and whether a configured value really stops this model
thinking. Nothing ships, so a harness with no documents knows nothing about any
model and says so: the split protocol stands down with a typed notice, no knob
is sent, nothing refuses, and the run's own record stamps a registry with zero
profiles in it.

Five documents are committed as reference copies at `docs/model-profiles/`, for
a human to copy into their home directory. glm-5.3's is the one that answers the
original question: it declares `extraction_value: low`, `thinking_disablable:
false`, `can_compact: false`, and it cites the record that measured each.

Two things were found on the way that the request did not forecast. The CLI
carried a launch REFUSAL demanding `reasoning: none` before it would spend a
provider call — forcing the very value that breaks glm-5.3 and refusing the one
that works. It is now a disclosure that prints and continues. And the same
hard-coded `"none"` survives at `verification/llm_broker.py:225`, inside a
frozen file this tranche may not touch; it is verified and parked, not fixed.

Proven by: 4633 passed / 0 failed on the full gate; RED-then-GREEN mutation
proofs from byte-identical test files; a probe that goes red on a one-byte
change to the claim that matters; and an empty frozen-surface diff.

## Reconciliation, requirement by requirement

Every R in REQUEST.md, in order, including amendments.

| R | the operator's words | disposition |
|---|---|---|
| **R1** | *"an incorrectly coded GLM 5.3 endpoint. For example, writing none for thinking instead of low."* | **done** — `18208049c`. The constant is gone (S2); glm-5.3's document declares `low` (S5); the CLI no longer demands `none` (S2b). Acceptance: VALIDATION.md §1 rows S2, S2b, S5. |
| **R2** | *"Would this work for all unknown models as well?"* | **done** — `18208049c`. Answered below as the question it was. Acceptance: S3. |
| **R3** | *"Surely creating agent.md would be better."* | **done** — `229804d93`, `18208049c`. One Markdown document per model, named `agent.md`, prose a human writes around one machine-readable block. Acceptance: S1, S5. |
| **R4** | *"Take this particular task out of the hands of the machine"* | **done** — `18208049c`. The harness holds no per-model opinion: no defaults, no table, no fallback value. `tests/test_model_profile_registry.py::test_adding_a_model_needs_no_source_edit` describes a model that appears nowhere in the tree, reaches the wire with its declared value, and asserts every `.py` under `src/` byte-unchanged. Shown RED against a planted bypass. Acceptance: S2, S4, S7. |
| **R5** | *"because we don't really know what future LLMs settings will be?"* | **done** — `18208049c`. Nothing in the design enumerates models or values: the declared `model_id` is the key (so `gpt-oss:120b` needs no escaping), every field but three is optional, and the loader supplies no value the author did not write. A dated document plus a re-runnable probe means a stale claim fails a CHECK, not a RUN. Acceptance: S1, S6. |
| **R6** | *"ok next prompt"* | **done** — the tranche ran on the proposal this accepted. Where the proposal and the operator's words diverged (M4), the words won; see R9. |
| **R7** | *"model-profiles/glm-5.3/agent.md"* | **done** — `229804d93`. Directory per model, `agent.md` inside. The declared id, not the directory name, is the key. |
| **R8** | *"Home directory only, nothing ships"* | **done** — `18208049c`. `profiles_root()` is `$DEEPREASON_HOME/model-profiles/`; the installed package contains no document, asserted by `test_the_installed_package_ships_no_profile_of_its_own`. |
| **R9** | *"These questions miss the point. Harness is supposed to accommodate all possible future models and configurations"* | **done, and it SUPERSEDED part of the plan.** No substitution, no veto, no nearest-value logic exists anywhere: a configured `reasoning:` value travels to the provider exactly as written. This retired the monitor's M4 outright and drove S2b. Acceptance: S2b, and the absence is checked by S7. |

**Superseded:** the monitor's M4 ("replaced by the profile's nearest declared
value") — superseded in full by R9. Nothing in the shipped code substitutes a
value.

## R2, answered as the question it was

The operator asked *"Would this work for all unknown models as well?"* — a
question, not an instruction, and REQUEST.md Q3 recorded that it was ambiguous
whether it asked for a guarantee or confirmed one.

The answer is **yes, and it is now the default path rather than an edge case.**
Because nothing ships, every model is unknown until a human writes its
document. An unknown model gets: the reasoning knob omitted entirely, the
split-budget protocol stood down with the typed notice
`split-budget:no-model-profile-for-this-seat`, a run record stamping a registry
of zero profiles, and no refusal anywhere. `resolve()` returns `None` for an
unknown id, an empty id, `None`, and a home directory that does not exist —
never an exception, on any path.

The honest qualifier: "works" here means *runs safely and says what it does not
know*. It does not mean the harness knows the right setting for a model nobody
has described — that is precisely what it stops pretending to know.

## Q5, answered

REQUEST.md Q5 asked whether "where the trace lands per value" could be a typed
vocabulary or was prose for a human. It is typed: `trace_destination` maps each
value to `side_channel`, `content`, or `absent`, and the probe reads it to
verify the claim. No dispatch path reads it — it describes, it does not decide.

## Map delta

Created one document, changed four, added 12 checks.

- **`docs/map/CON-model-profiles.md`** (new, `DR-CON-model-profiles`) — 7
  re-runnable checks. A `CON-` and not a `SUB-` because the package is only the
  loader; the concept spans `llm/`, `scheduler/` and a directory outside the
  repo. Its Traps section names the constant this retired, P-S1's M-1 and M-16,
  and P-A1 run `4565139800f5ca02`.
- **`docs/map/SUB-llm.md`** — the entry-points check no longer pins
  `reasoning_disabled` and now asserts, by AST, that neither retired name
  returns. The "Unset reasoning is not off" trap was REWRITTEN IN PLACE, never
  deleted, to say when and how its premise stopped holding; a second trap was
  added about per-model facts answered by per-provider tables.
- **`docs/map/CON-seats.md`** — its `plan_split` check now covers the required
  `profile` keyword and the unknown-model stand-down.
- **`docs/map/INDEX.md`** — one concept row, one routing row, two seam-matrix
  rows (`llm × model-profiles`, `model-profiles × scheduler`, both "not yet
  written").
- **`docs/map/SEAM-schools-x-scheduler.md`** — flagged by `--stale` and fixed:
  its "Which module built the run" row described the stamp as if it carried
  only the school-population row.

`--stale` still lists 15 documents, 12 of them unrelated to this tranche. The
three it listed for this change were each read and judged;
`SUB-scheduler.md` and `SUB-application.md` carry no claim this change
falsified. `Verified-at` was advanced on exactly the five documents whose
checks were re-run.

**Not closed, and named so it is not mistaken for done:** `INDEX.md`'s seam
matrix still has no row for `llm × qualification`, which the monitor's M8 asked
for. Nothing in this tranche created traffic between those two sides — the
probe is deliberately standalone and `qualification.py` is untouched — so
writing that seam would be documenting an interaction that does not exist.
Parked as **P4** rather than invented.

## Errata

**One entry, `docs/ERRATA.md` E66**, in the same commit as this document.

The P-A1 monitor review's addendum opens with "Ollama's glm-5.3 page:
`reasoning_effort` accepts `low`, `high`, and `max` … `none` is not in the
set", and the executor window carried that sentence forward as evidence. It
conflates two different sets and implies a refusal that never happened: the API
parameter's documented vocabulary DOES include `none`, glm-5.3 accepts it on
the wire, and what is wrong with it is behavioural (0/8 clean content), not a
rejection. The distinction decides the design — it is why a document carries
`documented_values` and `trace_destination` as separate fields, and collapsing
them is the reasoning that produced the constant in the first place. The review
itself is not edited; its central diagnosis was right and is what this tranche
acted on.

## Parked — seven items, each with a ready-to-send prompt

Offered, not promised. Full prompts in PARKED.md.

| | what | why parked |
|---|---|---|
| **P1** | one seat's exhaustion kills the run; the failed terminal is not continuable | out of scope (C5); bears on the 2026-08-29 continuation law |
| **P2** | the ~300 s transport wall and blind identical retries | out of scope (C5); better done AFTER this, so a retry policy can read a declared transport note instead of guessing |
| **P3** | `SPLIT_BUDGET_EXTRACTION_TOKENS` default of 512 | out of scope (C5), and the measurement that would answer it cannot be taken until the thinking prose is gone |
| **P4** | `INDEX.md` has no `llm × qualification` seam row | this tranche created no such traffic |
| **P5** | the same hard-coded `"none"` at `verification/llm_broker.py:225` | frozen surface 3; contact is an immediate stop |
| **P6** | the operational wheel smoke is red at `continuation_resume`, and no gate runs it | pre-dates the tranche (measured); the failure is in the continuation lifecycle |
| **P7** | a document edited mid-run changes behaviour the run's own stamp denies | a freezing decision with real semantics to choose; not requested |

**Recommended next: P5.** It is the same defect as the one just fixed, it is
one line, and it is the only parked item that leaves a known-wrong value on a
live wire. It needs an operator decision before any code, because the file is
frozen — which is exactly why it should be asked now rather than found again
later.

Second choice would be P6: an instrument no gate runs, sitting red, pinning the
public operational surface.

## Where the evidence is

- `VALIDATION.md` — every acceptance check with its pasted output, the gate, the
  frozen-surface diff, and a section on what this does NOT establish.
- `MUTATION_RED.txt` / `MUTATION_GREEN.txt` — byte-identical test files, exit 1
  then exit 0, one line of source apart.
- `BASELINE.txt` — the pre-tranche state, including the finding that BOTH
  pre-authorized red baselines were already green, so neither waiver was
  claimed.
- `price_notice_road.py` / `PRICE_NOTICE_ROAD.txt` — the measurement that
  excluded the two compile-time roads.
- `probe_fixture_glm53.json` — P-S1's measured trials, transcribed, which the
  probe replays.
