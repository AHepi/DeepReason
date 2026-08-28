# SPEC — the robust attention-layout rules, as this tree will implement them

Authority: REQUEST.md R1–R4, C1–C8. Census: CENSUS.md.
Map: `DR-CON-packs-and-token-economy` (primary), `DR-SUB-llm`,
`DR-INV-reference-menu`, `DR-CON-discharge-channel`, `DR-INV-frozen-surfaces`.

## 0. What the census changed about the scope

R1's closure rule ("if the harness ALREADY satisfies a rule, that requirement
closes as already-met — do not churn code") fires once, and it removes the
largest piece of speculative work in the tranche:

**R2b closes as ALREADY-MET.** The maximum standing-instruction count over
2836 real first-turn prompts is 28, against a ceiling of ~40 and a hard floor
of 80. No seat is restructured, no instruction is dropped, and there is
nothing to disclose under R2b's "any dropped instruction is a disclosed
decision in SPEC.md" — because none is dropped. What ships instead is a
GUARD (S6), so a future seat crossing the ceiling fails the gate rather than
going unnoticed.

The other three rules are gaps and are implemented: S2/S3 (R2a), S4 (R2c),
S5 (R2d), all under the policy of S1 (R2e).

## 1. Frozen surfaces and the C3 stop line — disposed BEFORE design

C3 forbids moving a qualification subject digest or any committed digest pin,
with no exception pre-granted. Three contacts were checked and all three are
avoided by construction, not by hope:

**1.1 No `Config` field is added.** `run_manifest.py:2355 _source_config_data`
dumps EVERY `Config` field into `engine_config_json`, which
`qualification.py:274 qualification_subject_payload` folds into
`manifest_behavior`. A new `Config` knob therefore moves every qualification
subject digest unless it is also popped in
`run_manifest.py:2363 _versioned_source_config_data` — which is the path the
2026-08-26 F3 tranche took under an explicit operator forecast, and which
would put this tranche inside frozen surface 4. **This design does not go
there.** The layout policy is a VERSIONED ARTIFACT selected by id, resolved
from an explicit argument or the `DEEPREASON_RENDER_LAYOUT_POLICY`
environment variable — the established idiom in this tree for operational
configuration that must not enter a manifest digest (`easy.py:338`,
`admission/store.py:31`, `cli/doctor.py:1116`). R2e allows exactly this:
"configuration **or a versioned artifact**".

**1.2 No committed root can change verdict.** `verify_root` and
`workflow/replay.py` never re-render a pack; they compare recorded
`prompt_sha256` values against each other for internal consistency
(`invariants.py:397`, `replay.py:2450`, `:2498`). Nothing in verification
imports `render_conj_pack`, `render_crit_pack` or `render_role_prompt` —
the only importers are `rules/conj.py`, `rules/crit.py`, `llm/adapter.py` and
`cli/doctor.py`. Proven at S9 by re-verifying committed roots before and
after.

**1.3 `cli/doctor.py` is NOT touched.** It builds the qualification battery's
own probe prompts, including a judge probe that mirrors the shape S3 changes.
Leaving it alone keeps the battery's subjects byte-identical. The divergence
this creates — the qualification probe carrying the old judge shape while the
run carries the new one — is a DISCLOSED CONSEQUENCE, recorded in PARKED.md
as a follow-up for the operator to schedule, because closing it means
touching a qualification subject and C3 forbids that here.

Result: **no frozen-surface contact, no digest movement.** `tools/
blast_radius.py` is run at S9 and its verdict is pasted into VALIDATION.md.

## 2. S1 — the layout policy (R2e)

New module `src/deepreason/llm/layout.py`, on the signal-contract pattern the
modularity law names (FROZEN protocol / VERSIONED registry / FREE parameters).

    LAYOUT_POLICY_SCHEMA = "render-layout.v1"

    class RenderLayoutPolicyV1(frozen, extra="forbid"):
        policy_id: str
        question_last: bool              # R2a
        instruction_ceiling: int         # R2b, 1..80
        live_verbatim_n: int             # R2c, 0..8
        distilled_head_chars: int        # R2c, 32..4096
        superseded_summary_n: int        # R2c, 0..8
        retrieval_note: bool             # R2c
        merge_head_label_blocks: bool    # R2d

**VERSIONED registry**, two entries, both shipped:

| id | what it is |
|---|---|
| `render-layout.v1` | the robust rules ON — `question_last=True`, `instruction_ceiling=40`, `live_verbatim_n=2`, `distilled_head_chars=160`, `superseded_summary_n=0`, `retrieval_note=True`, `merge_head_label_blocks=True`. The default. |
| `render-layout.legacy-v0` | the pre-tranche arrangement, every flag off and `superseded_summary_n=0`. Shipped so the old layout stays reachable as CONFIGURATION rather than by reverting code — which is the modularity law's actual demand. |

`resolve_layout_policy(policy_id=None)` resolves explicit argument →
`DEEPREASON_RENDER_LAYOUT_POLICY` → `DEFAULT_LAYOUT_POLICY_ID`, and raises a
typed `RenderLayoutPolicyError("RENDER_LAYOUT_POLICY_UNKNOWN", ...)` on an
unregistered id. `register_layout_policy(policy)` adds one without editing any
consumer. FREE parameters are envelope-clamped by the model's own validators;
a value outside its envelope is a typed refusal at construction, never a
silent clamp.

**Acceptance A1:** `resolve_layout_policy()` returns `render-layout.v1`;
`DEEPREASON_RENDER_LAYOUT_POLICY=render-layout.legacy-v0` returns the legacy
policy; an unknown id raises `RENDER_LAYOUT_POLICY_UNKNOWN`; every FREE
parameter refuses a value outside its envelope.

## 3. S2 — nothing load-bearing after the question, on the two IR renderers (R2a)

`render_conj_pack` and `render_crit_pack` gain `layout: RenderLayoutPolicyV1`
(defaulting to the resolved policy). When `layout.question_last`, each appends
one final section:

    _pack_section("question", <restatement>, _QUESTION_PRIORITY,
                  droppable=False, compressible=False)

with `_QUESTION_PRIORITY = 100`, so `(priority, id)` ordering places it after
every other section including the `context-withheld` notice at 99.

The restatement carries **no new content**: it is the same text as the
priority-1 section (`problem` for the conjecturer, `problem-context` for the
critic), under a header line stating that it is the question, restated last.
For the critic it additionally names the target id, because "what am I being
asked about" is the critic's question and the target sits at priority 4.

Mandatory and exact, for the reason `target` and `open-criticisms` are: a
droppable question restatement would let budget pressure silently restore the
arrangement this section exists to abolish, and a compressible one would cut
its middle while still looking present.

**PREDICTED FIXTURE UPDATE, declared here because CLAUDE.md permits one only
when the design predicted it.**
`tests/test_frame_render.py::test_the_withheld_notice_sorts_last_and_leaves_the_cache_prefix_intact`
asserts `headers[-1] == "## context-withheld"`. The claim that test protects
is stated in its own docstring — the notice "must not lead the pack", because
a per-call volatile section at the head invalidates the cacheable prefix. That
claim is untouched. The assertion is stronger than the claim, so it is
minimally updated to: the notice is last among the CONTEXT sections
(`headers[-2]`), and only the question restatement follows it
(`headers[-1] == "## question"`). The `headers[0]` assertion is unchanged. The
map's own sentence in `CON-packs-and-token-economy.md` moves with it, in the
same commit.

**Acceptance A2:** for both renderers, with `render-layout.v1` the last `## `
header is `question` and the census instrument reports
`after_question_chars == 0`; with `render-layout.legacy-v0` there is no
`question` section and `after_question_chars > 0`.

## 4. S3 — nothing load-bearing after the question, on the judge (R2a)

`informal/trial.py:407 _judge_pack` and the inline pack at `:966` place the
`QUESTION:` line BEFORE the case and the defence — the two things the judge is
asked to weigh — for up to 7503 characters, across 342 recorded prompts. Both
become question-last when `layout.question_last`:

    TARGET: ...            THE CASE FOR FAIL: ...
    THE CASE FOR FAIL: ... THE DEFENCE: ...
    THE DEFENCE: ...   ->  QUESTION: ...
    QUESTION: ...          Rule on the exchange; decisive_point MUST quote a span of it.
    Rule on the exchange...

**This is a reordering and only a reordering** — the same lines, the same
words, in a different order. Nothing is added and nothing is dropped.

**DISCLOSED CONE EXTENSION.** `informal/` is `DR-SUB-evaluation`, not the
render/pack/scratch surface the tranche instruction forecast. It is included
because it is a rendered prompt, it is the single largest measured R2a
violation outside the two IR renderers, and the fix is positional. The risk is
stated rather than hidden: the operator's standing ruling is that judge seats
are suspect-by-default, and moving a judge's question is a change to a seat
they distrust. It is therefore gated on the same policy flag as everything
else, so `render-layout.legacy-v0` restores the old judge pack byte-for-byte
without a code change.

`informal/audits.py:92` and `:240` were checked and are ALREADY question-last;
they are not touched.

**Acceptance A3:** both judge packs end with the question and the ruling
instruction; the census instrument reports `after_question_chars == 0` for a
rendered judge pack under `render-layout.v1` and `> 0` under
`render-layout.legacy-v0`.

## 5. S4 — carry-forward: distilled, disclosed, retrievable, late (R2c)

Three changes, all in `render_conj_pack`, all policy-gated.

**5.1 Distillation replaces prefix clipping.** `packs.py:236 _head` takes the
first 160 characters of an artifact's serialized content — a cut through the
middle of a JSON envelope. The research note's row asks for a "One-line
**claim** summary, no prose", and this tree's artifacts have a `claim` field:
distillation is therefore STRUCTURAL and deterministic, not a model call.
`_distilled(state, aid, blobs, layout)` parses the content and renders the
`claim` field clipped to `layout.distilled_head_chars`; an artifact with no
parseable claim falls back to today's prefix head, so nothing loses its entry.

**5.2 The cap states itself in-band, and names the retrieval route.** When
`layout.retrieval_note`, a clipped entry ends with a marker and the section
header says what the entries are and how to get the rest. The retrieval route
is real and already served: `llm/wire.py:1396 ContextRequestWireV1` lets the
conjecturer request material by alias, and `scratch/conjecture.py:708` serves
it. This is the repo's own "no silent caps" discipline
(`DR-CON-packs-and-token-economy`) applied to the one section that lacked it.

**5.3 Live conjectures render verbatim, late.** A new `live-neighbourhood`
section carries the `layout.live_verbatim_n` most recent ACCEPTED artifacts
VERBATIM, explicitly labelled live, at priority 12 — beside `output-contract`
and immediately before the question restatement, which is "late, near the
question". Those artifacts are removed from the distilled `neighbourhood` list
so nothing renders twice. Droppable AND compressible, as the NEGATIVE rule
requires of every droppable section, so budget pressure degrades it to today's
behaviour rather than overshooting the target.

**5.4 Superseded conjectures — a knob, defaulting to today's behaviour, and
the reason is recorded rather than assumed.** `packs.py:594` renders only
`Status.ACCEPTED`, so a REFUTED artifact never appears. The research note's own
placement table gives "Middle **or omit**" for superseded material, so
omission is one of the two options it endorses, and rendering refuted
conjectures back into the conjecturer's context is an EPISTEMIC change — it
puts dead lines back in front of the seat whose job is to leave them — not a
layout one. R2c's words nonetheless ask for the distilled form. Both readings
are served by shipping the capability and defaulting it off:
`superseded_summary_n=0` renders exactly what ships today, and any value above
0 renders that many REFUTED artifacts as one-line distilled claim summaries
with the retrieval note, in a `superseded-conjectures` section at priority 8
(the note's "middle"). The knob is tested at `n>0`; the default is byte-
identical to today. Whether to raise it is a question R3's calibration
experiment can settle with tokens rather than argument (C7).

**Acceptance A4:** with `render-layout.v1`, a neighbourhood entry whose
artifact has a claim renders that claim and not a mid-JSON cut; a clipped
entry carries its in-band marker; the header names the retrieval route; the
`live-neighbourhood` section carries `live_verbatim_n` artifacts whole and
sorts after `neighbourhood`; `superseded_summary_n=0` renders no
`superseded-conjectures` section and `>0` renders one. With
`render-layout.legacy-v0` every one of those is absent.

## 6. S5 — fewer, larger blocks in the prompt head (R2d)

`roles.py:375 render_role_prompt`'s compact branch emits every label as its own
`\n\n`-separated block. When `layout.merge_head_label_blocks`, each label is
joined to the body it labels with a single newline:

    before: 9 head blocks, five of them under 100 chars
    after:  5 head blocks, none of them a bare label

Not one word changes. The pack's own `## id` headers are NOT merged, and that
is forced rather than chosen: `DR-CON-packs-and-token-economy` makes the
presence of a header the only signal that a section was not dropped ("a
dropped section leaves no header and no placeholder, so absence is the only
signal"), so merging pack sections would destroy the drop signal.

**Acceptance A5:** the census instrument's block count for a rendered compact
prompt falls under `render-layout.v1` versus `render-layout.legacy-v0`, and
the set of words in the two prompts is identical.

## 7. S6 — the instruction-count guard (R2b, already-met)

No seat is restructured. A test measures every entry in `TEMPLATES` and
`COMPACT_TEMPLATES` plus a rendered pack with the census counter and asserts
the total is at or under `layout.instruction_ceiling`. A companion test proves
the counter can fire, on a synthetic prompt carrying 50 clauses.

**Acceptance A6:** the guard passes on the tree as shipped; the counter
returns >40 on the synthetic prompt; a template mutated with 20 extra
imperative clauses turns the guard RED.

## 8. S7 — the architecture test (R2e's "check that can fail")

`tests/test_render_layout_policy.py`, three limbs:

1. **Bypass detector.** For each of the four rules, render the same inputs
   under `render-layout.v1` and `render-layout.legacy-v0` and assert the
   outputs differ in the way that rule names. A consumer that ignores the
   policy renders identically under both and turns this RED. This is the limb
   that would actually catch a bypass, and it is mutation-proven by making one
   consumer ignore its `layout` argument.
2. **No hard-coded layout constants.** An AST scan asserting the literals the
   policy owns appear only inside `llm/layout.py`.
3. **Customisation without a code edit.** `register_layout_policy` a fresh
   policy, select it through `DEEPREASON_RENDER_LAYOUT_POLICY`, and assert the
   render follows it — with no edit to `packs.py`, `roles.py` or `trial.py`.

## 9. S8 — R3's parked calibration prompt

The research note's §(b) items — which pre-question slot, which rendering
format, how much retrieval depth — are NOT implemented. One ready-to-send
calibration-experiment prompt lands in PARKED.md and is reproduced inline in
the delivery reply as a single fenced block (operator request, 2026-08-11). It
is parked, not run.

## 10. S9 — proof obligations (R4)

Every behavior change gets a regression test shown RED against the old
behaviour and GREEN against the new, with both outputs committed under
`proof/`. Additionally:

- `tools/blast_radius.py` verdict pasted into VALIDATION.md.
- `verify_root` re-run on committed roots before and after, diffed empty.
- the qualification subject digest computed before and after on the same
  manifest, byte-identical.
- the census instrument re-run after the change, before → after tabled in
  DELIVERY.md from the same root as CENSUS.md (C8).
- the map moves in the same commits: `CON-packs-and-token-economy.md` gains
  the new sections and their checks; a new `INV-render-layout.md` declares the
  FROZEN/VERSIONED/FREE layers; `INDEX.md` routes to it.
- full gate 0 failed; `docs_verify` full with no delta beyond C5's four.

## 11. Recorded assumptions

- **A-1.** "Standing instruction" is a natural-language normative clause; the
  JSON Schema and data lines are excluded. Disclosed and quantified in
  CENSUS.md R1b. If the operator counts schema constraints instead, the
  conjecturer reads 163 and R2b becomes a gap — the assumption is load-bearing
  and is stated here for that reason.
- **A-2.** "The question" is the seat's task-and-subject statement: `problem`
  for the conjecturer, `problem-context` plus the target for the critic, the
  `QUESTION:` line for the judge. The output contract is the FRAME around the
  question, not material after it, and the note's own table puts it "before
  everything" — so it stays where it is and the question moves past it.
- **A-3.** The six seats that state no question in the pack (defender,
  config-referee, two summarizer contracts, two thesis contracts) are left
  alone. They place their task frame in the role template ahead of everything,
  which is the note's recommended slot; adding a late restatement to them
  would be work R1's closure rule does not license.

## 12. Budget

Roughly 500 lines of production code and map, 400 lines of test. Stop and
report if it exceeds double that, or if any acceptance check cannot be made to
fail against the old behaviour.
