# CENSUS — how DeepReason renders prompts today, against the four robust rules

Requirement: REQUEST.md R1 (R1a–R1d). Instrument:
`tools/prompt_census.py`, run over every committed run root.
Raw rows: `proof/census_rows.json`. Printed table: `proof/census_table.txt`.

## What the evidence is, and why it is stronger than a reconstruction

R1 asks for "at least one real rendered prompt reconstructed from a committed
root's render receipts". The record turned out to carry something better than a
reconstruction, so this census uses that instead and says so:

**every prompt measured here is a stored blob whose sha256 equals the
`prompt_sha256` of a committed `workflow-provider-attempt-v1` record.** The
bytes measured are therefore the bytes that reached the provider — not a
re-derivation that might drift from the code that wrote them.

    3308 sha-verified dispatched prompts across 59 committed roots
    2836 of them are FIRST TURNS (attempt_index == 0)

Only first turns are tabled. A repair turn's pack is a diagnostic envelope
carrying the model's own rejected output, so its shape measures the repair
protocol, not the layout under test — measuring them together inflated the
conjecturer's block count from 15 to 33 on the first pass of this census.

`ScratchRenderReceiptV1.ordered_refs` was consulted for the handle-map trap
(CLAUDE.md: handle maps reload key-sorted, compare by handle index and never by
`.values()`); this census does not compare handle maps, so the trap does not
bite it, and the accessor is named here so a later reader knows it was checked
rather than missed.

## The renderer code paths (R1's file:line table)

| Path | What it renders | On the section IR? |
|---|---|---|
| `src/deepreason/llm/roles.py:375` `render_role_prompt` | the whole prompt: role template → schema → aliases → example → pack | n/a |
| `src/deepreason/llm/roles.py:26` `TEMPLATES` / `:333` `COMPACT_TEMPLATES` | the standing role instructions | n/a |
| `src/deepreason/llm/adapter.py:811` `_render_request` | assembly, aliasing, profile clip, envelope check | n/a |
| `src/deepreason/llm/packs.py:486` `render_conj_pack` | the conjecturer pack, 18 section slots | **yes** |
| `src/deepreason/llm/packs.py:1088` `render_crit_pack` | the single-target critic pack, 13 section slots | **yes** |
| `src/deepreason/llm/packs.py:818` `render_batch_crit_pack` | the batch critic pack | no — prefix clip |
| `src/deepreason/llm/packs.py:911` `render_experiment_pack` | the experimenter pack | no — prefix clip |
| `src/deepreason/llm/packs.py:973` `render_property_pack` | the property pack | no — prefix clip |
| `src/deepreason/llm/packs.py:1018` `render_cx_retry_pack` | the counterexample retry pack | no — prefix clip |
| `src/deepreason/llm/packs.py:236` `_head` | the 160-char clip every carried-forward artifact goes through | — |
| `src/deepreason/packs/allocate.py:72` `allocate_pack` | retention/compression/drop, in `(priority, id)` order | — |
| `src/deepreason/informal/trial.py:407` `_judge_pack` | the standard-trial judge pack | no |
| `src/deepreason/informal/trial.py:966` (inline) | the argumentative-trial judge pack | no |
| `src/deepreason/informal/trial.py:539` (inline) | the trial critic pack | no |
| `src/deepreason/informal/trial.py:566` (inline) | the defender pack | no |
| `src/deepreason/informal/audits.py:92` `_judge_exchange` | the audit-replay judge pack | no |
| `src/deepreason/informal/audits.py:240` (inline) | the calibration judge pack | no |
| `src/deepreason/measures/hv.py:110` | the variator pack | no |
| `src/deepreason/cli/doctor.py:787` | the QUALIFICATION probe prompts — **not a run renderer** | no |

## The measurements (first turns only)

`instr` = standing instructions (natural-language normative clauses; the
counting rule and its disclosed exclusions are in the instrument's docstring).
`blocks` = delimiter-bounded regions. `small` = median count of blocks under
400 chars. `afterQ` = characters rendered AFTER the question.

| seat (role/contract) | n | question is | instr min–max | blocks min–max | small | afterQ chars |
|---|---:|---|---|---|---:|---|
| `argumentative_critic/batch-critic.v2` | 1286 | `DIRECTIVE:` line, last | 7–24 | 7–13 | 4 | **0** |
| `variator/variator.direct.v1` | 30 | `DIRECTIVE:` line, last | 7–16 | 4–10 | 2 | **0** |
| `argumentative_critic/critic.atomic-target.v1` | 34 | `## problem-context`, first | 8–12 | 10–14 | 6 | **1285–4342** |
| `conjecturer/conjecturer.atomic-candidate.v1` | 390 | `## problem`, first | 5–22 | 8–14 | 5 | **1447–4519** |
| `conjecturer/conjecturer.turn.v6` | 585 | `## problem`, first | 9–28 | 6–15 | 4 | **1214–16091** |
| `conjecturer/conjecturer.turn.v7` | 4 | `## problem`, first | 8–8 | 7–7 | 4 | **914–1604** |
| `judge/judgeruling.direct.v1` | 342 | `QUESTION:` line, mid-pack | 6–25 | 7–21 | 3 | **1253–7503** |
| `defender/defender.direct.v1` | 122 | none in the pack | 4–12 | 4–4 | 2 | — |
| `argumentative_critic/config-referee.v1` | 6 | none in the pack | 9–9 | 4–4 | 0 | — |
| `summarizer/bridge.ledger.v3` | 12 | none in the pack | 16–19 | 7–9 | 3 | — |
| `summarizer/bridge.ledger-batch.v1` | 11 | none in the pack | 12–12 | 5–5 | 4 | — |
| `thesis/bridge.composition.v2` | 10 | none in the pack | 8–9 | 4–7 | 0 | — |
| `thesis/bridge.composition-batch.v1` | 4 | none in the pack | 7–8 | 7–7 | 6 | — |

## R1a — does load-bearing material sit AFTER the question?

**Three shapes, and only the middle one is a gap.**

*Question last (compliant).* `batch-critic.v2` and `variator.direct.v1` end
their pack with the `DIRECTIVE:` line. Zero characters follow it, in all 1316
measured prompts.

*Question first, material after it (THE GAP).* Five seats. The conjecturer's
`## problem` section sits at priority 1 and up to seventeen further sections
follow it — `criteria`, `open-criticisms`, `mandatory-interface`,
`active-properties`, `frozen-evidence-context`, `citable-evidence-blocks`,
`capability-result-context`, `frame-crisis`, `frame-slice`, `school-stance`,
`experimental-generation-context`, `scratch-advisory-context`,
`neighbourhood`, `crossover`, `complement-directive`,
`diversity-specifications`, `output-contract`. The single-target critic is the
same shape with `## problem-context` at priority 1 and six sections after it.
The judge is the largest single case: the `QUESTION:` line is followed by the
whole case and the whole defence — the two things it is being asked to weigh —
for up to 7503 characters.

*No question in the pack at all.* Six seats state their task only in the role
template at the head of the prompt and render the pack as pure material. That
is the note's own recommended slot for a task frame ("System prompt, before
everything"), and nothing is placed after a question because no question is
placed. Recorded as neither met nor violated: **task-frame-only**.

**Verdict: GAP, on five seats.**

## R1b — how many standing instructions does one rendered prompt carry?

Ceiling from the research note: ~40, hard floor 80.

**Maximum observed across all 2836 first-turn prompts: 28**
(`conjecturer.turn.v6`). No seat's minimum exceeds 16. The busiest seats are
the conjecturer (9–28) and the judge (6–25).

Two disclosed exclusions, so the number can be judged rather than trusted:

1. **The JSON Schema is not counted.** It is the largest text in most prompts
   (16 930 of 20 881 characters in the worked example below) and carries 3–154
   machine-checkable constraints per seat, tabled as `schema` in
   `proof/census_table.txt`. It is excluded because the harness VALIDATES it
   and repairs violations through the contract-repair protocol, so its clauses
   do not compete for the adherence budget the research note measured; prose
   clauses, which nothing checks, do. Counted in, `conjecturer.turn.v6` would
   read 163 rather than 28 — past the note's hard floor of 80 — and that
   number would be measuring the wrong thing.
2. **Data lines are not counted** — artifact bodies, `predicate:`/`program:`
   commitment schemas, alias listings.

**Verdict: ALREADY MET.** No seat approaches 40. Per R1's own closure rule, no
restructuring is owed. What is missing is not compliance but a GUARD: nothing
in the gate would notice a future seat crossing the ceiling.

## R1c — is prior-round material carried verbatim or distilled?

Neither. It is **prefix-clipped**, which is the third option the research note
does not consider and the one its mechanism section argues against.

- `packs.py:236` `_head(state, aid, blobs, limit=160)` takes the first 160
  characters of an artifact's content and replaces newlines with spaces. Every
  carried-forward artifact goes through it — `neighbourhood` (`packs.py:721`)
  and `crossover` (`packs.py:742`).
- The cut is **silent**. The section header reads "NEIGHBOURHOOD (accepted
  artifacts; carry dependence refs where natural):" and says nothing about the
  entries being heads. This is the shape the repo already legislates against
  elsewhere — `DR-CON-packs-and-token-economy` requires a cap to "state itself
  in-band wherever it bites", and `frame-crisis` and the reference menus both
  do. The neighbourhood does not.
- **Full text IS retrievable by reference, and the pack never says so.** The
  conjecturer's own output contract admits a `context_request`
  (`llm/wire.py:1396` `ContextRequestWireV1`, served at
  `scratch/conjecture.py:708`), so the model may ask for a truncated entry by
  its alias. Nothing in the rendered pack tells it that the neighbourhood
  entries are the thing worth asking for.
- **Live conjectures are not placed late.** `neighbourhood` sits at priority 8
  of 12 — mid-pack, ahead of `crossover`, `complement-directive`,
  `diversity-specifications` and `output-contract`.
- **Superseded conjectures are omitted entirely.** `packs.py:594` selects
  `status == Status.ACCEPTED`; a REFUTED artifact never renders. The research
  note's own placement table gives "Middle **or omit**" for this row, so
  omission is one of the two options it endorses.

**Verdict: GAP on the live half (prefix-clipped, silent, mid-pack, no
retrieval note). Superseded half is one of the note's own two options,
already taken.**

## R1d — block structure: many small blocks or few large ones?

First-turn prompts carry 4–15 delimiter-bounded blocks, with a median of 2–6
of them under 400 characters. The small ones are concentrated in the compact
prompt HEAD, where every label is its own block:

    "LOCAL REFERENCES (copy aliases, not identifiers):"   (48 chars)  -- block
    "SRC_001\nSRC_002\n..."                                (81 chars)  -- block
    "ONE SYNTAX EXAMPLE:"                                 (19 chars)  -- block
    "{\"abstention\":{\"search_signal\":\"stuck\"}}"           (40 chars)  -- block
    "INPUT:"                                              ( 6 chars)  -- block

Five blocks carrying one label-and-body pair each, plus a bare `INPUT:`
marker. Merging each label with the body it labels removes four delimiter
boundaries per compact prompt with no change to a single word.

The pack's own `## id` headers are a different case and **must not** be
merged: `DR-CON-packs-and-token-economy` makes the presence of a header the
only signal that a section was not dropped ("a dropped section leaves no
header and no placeholder, so absence is the only signal"). Merging pack
sections would destroy that signal. The block-structure rule is therefore
implementable in the head and precluded in the pack.

**Verdict: GAP, in the prompt head only.**

## Worked example — one real dispatched prompt, whole

Root: `experiments/2026-08-25-change-constructive-frontier/`
`void-inert-battery-run-6913328037a61ca6`
Attempt: `conjecturer[0]`, `conjecturer.turn.v6`, prompt_tokens 6226
Blob: `blobs/18/18c67dda60af63e4e267d813b8fca68e1a0f97fafb68f9e57c92cf059442b244`
sha256 of those bytes == that attempt's recorded `prompt_sha256`.

    [ 1] Propose diverse, criticizable candidates for the input. ...   <- task frame
    [ 2] Return ONLY one JSON value matching this closed schema:
    [ 3] {"$defs": ...}                              16 930 chars      <- output contract
    [ 4] LOCAL REFERENCES (copy aliases, not identifiers):
    [ 5] SRC_001 ... SRC_009
    [ 6] ONE SYNTAX EXAMPLE:
    [ 7] {"abstention":{"search_signal":"stuck"}}
    [ 8] INPUT:
    [ 9] ## problem              <- THE QUESTION, 715 chars
    [10] ## criteria             <- binding commitments        \
    [11] ## neighbourhood        <- prior-round material        | 2 949 chars
    [12] ## output-contract      <- the directive              /   AFTER the question

Total 20 881 characters, of which 2 949 are rendered after the question.

## Summary — what R2 owes

| Rule | Verdict | What R2 must do |
|---|---|---|
| R1a nothing load-bearing after the question | **GAP** (5 seats) | restate the question last |
| R1b instruction count ≤ ~40 | **ALREADY MET** (max 28) | no restructuring; add a guard |
| R1c distilled carry-forward, retrievable by reference | **GAP** (live half) | distil, disclose the cap, name the retrieval route, place live material late |
| R1d fewer, larger blocks | **GAP** (head only) | merge label-and-body pairs in the head |
