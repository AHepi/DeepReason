<!-- DR-INV-render-layout -->
Verified-at: 5f7e413d6
Verify: python tools/docs_verify.py
Owns: src/deepreason/llm/layout.py
Seams: 
Seams-undocumented: llm x scratch, packs-and-token-economy x rules, packs-and-token-economy x scratch

# The render layout policy — where a rendered prompt puts what it carries

## What it is

A rendered prompt is not just a set of bytes, it is an ARRANGEMENT of them,
and the arrangement is a decision. This document is the one authority for
those decisions: which element a seat reads last, how much of a prior round it
carries and in what form, how many standing instructions it may hold, and how
many delimiter-bounded blocks it is cut into. Before 2026-08-28 every one of
those was a literal somewhere in a renderer, which meant the arrangement could
not be changed without editing code and could not be compared against an
alternative at all.

The rules come from an external research note
(`docs/RESEARCH_ATTENTION_LAYOUT_2026-08-28.md`) and specifically from the
four items on its own "robust across models" list. **That note is not
evidence in this record's sense**, and nothing here rests on it being right:
what rests on the record is that the tree renders what the policy says, which
is what the checks below bind. Whether an arrangement is BETTER is a question
for a calibration run, and the parked prompt for one is at
`experiments/2026-08-28-change-render-layout-robust/PARKED.md`.

## Three layers, not interchangeable

**FROZEN — the change protocol.** A layout decision is a policy a renderer
READS, never a constant a renderer HOLDS. Layout touches PRESENTATION, never
EVIDENCE: no flag here may change which artifacts exist, what a commitment
means, or what counts as a refutation — only where the bytes sit and how much
of one artifact is shown.

**VERSIONED — the registry.** Every arrangement the tree can render is a
named, registered policy. `render-layout.legacy-v0` reproduces the
arrangement every committed root was rendered under, so a rollback is a
configuration change rather than a revert.

**FREE — the parameter values**, inside envelopes, refused typed at
construction rather than silently clamped.

`check: python -c "
from deepreason.llm.layout import ROBUST_LAYOUT_POLICY as r, LEGACY_LAYOUT_POLICY as l
assert r.question_last and not l.question_last
assert r.distil_carry_forward and not l.distil_carry_forward
assert r.retrieval_note and not l.retrieval_note
assert r.merge_head_label_blocks and not l.merge_head_label_blocks
assert r.live_verbatim_n == 2 and l.live_verbatim_n == 0
"`
`check: python -m pytest tests/test_render_layout_policy.py -q`

## Entry points

| What | Where |
|---|---|
| the policy type | `llm/layout.py` `RenderLayoutPolicyV1` |
| the two shipped arrangements | `llm/layout.py` `ROBUST_LAYOUT_POLICY`, `LEGACY_LAYOUT_POLICY` |
| selection | `llm/layout.py` `resolve_layout_policy` — argument, then `DEEPREASON_RENDER_LAYOUT_POLICY`, then the default |
| adding an arrangement | `llm/layout.py` `register_layout_policy` |
| the unit the instruction ceiling is in | `llm/layout.py` `count_standing_instructions` |
| consumers | `llm/packs.py` `render_conj_pack`/`render_crit_pack`, `llm/roles.py` `render_role_prompt`, `informal/trial.py` `argument_trial_judge_pack`/`_judge_pack` |

## The invariants

**It is NOT a `Config` field, and that is a constraint rather than a
preference.** `run_manifest.py` `_source_config_data` dumps every `Config`
field into `engine_config_json`, and `qualification.py`
`qualification_subject_payload` folds that into `manifest_behavior`. A layout
knob on `Config` would move the subject digest of every qualification bundle
in the tree, or would need a companion pop inside `run_manifest.py` — a
frozen surface. Selection by id, from an argument or the environment, reaches
neither.
`check: python -c "
from deepreason.config import Config
assert not [f for f in Config.model_fields if 'LAYOUT' in f.upper()], 'a layout knob reached Config'
from deepreason.llm.layout import LAYOUT_POLICY_ENV
assert LAYOUT_POLICY_ENV == 'DEEPREASON_RENDER_LAYOUT_POLICY'
"`

**Changing an arrangement cannot change a committed root's verdict**, because
verification never re-renders a pack. `verify_root` and `workflow/replay.py`
compare recorded `prompt_sha256` values against each other for internal
consistency; neither imports a renderer. This is the property that let the
2026-08-28 tranche ship a layout change with no frozen-surface contact, and it
is the property that would have to be re-established before any future one.
`check: python -c "
import pathlib
src = pathlib.Path('src/deepreason/invariants.py').read_text()
src += pathlib.Path('src/deepreason/workflow/replay.py').read_text()
assert 'render_conj_pack' not in src
assert 'render_crit_pack' not in src
assert 'render_role_prompt' not in src
assert 'verify_root' in pathlib.Path('src/deepreason/invariants.py').read_text()
"`

**The question sorts after everything, including the withheld notice.**
Allocation orders by `(priority, id)`, so a priority above every other section
IS the mechanism — there is no separate ordering pass to get wrong.
`check: python -c "
from deepreason.llm.packs import _QUESTION_PRIORITY, _WITHHELD_PRIORITY
assert _QUESTION_PRIORITY > _WITHHELD_PRIORITY > 12
"`
`check: python -m pytest tests/test_render_layout_rules.py -q`

**Superseded material stays omitted by default, and the default is the
point.** Rendering refuted artifacts back to the seat whose job is to leave
them is an EPISTEMIC change, not a layout one. The knob exists so the question
can be settled by a calibration run rather than by argument; it ships at zero.
`check: python -c "
from deepreason.llm.layout import ROBUST_LAYOUT_POLICY as r
assert r.superseded_summary_n == 0
"`

**The instruction ceiling is measured, never enforced by truncation.** Nothing
here drops an instruction: dropping one silently is the failure the bound
exists to make visible. The ceiling's envelope stops at 80 — the research
note's own hard floor — because a ceiling above the floor cannot bind.
`check: python -c "
from deepreason.llm.layout import RenderLayoutPolicyV1, INSTRUCTION_CEILING_FLOOR
assert INSTRUCTION_CEILING_FLOOR == 80
try:
    RenderLayoutPolicyV1(policy_id='probe', instruction_ceiling=81)
except ValueError:
    pass
else:
    raise AssertionError('the ceiling envelope does not bind')
"`

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| whether a seat asks last | `llm/layout.py` `question_last`, or register a policy | `tests/test_render_layout_rules.py` |
| how much of a prior round is carried, and in what form | `live_verbatim_n`, `distil_carry_forward`, `distilled_head_chars`, `superseded_summary_n` | `tests/test_render_layout_rules.py` |
| whether a cap discloses itself | `retrieval_note` | `tests/test_render_layout_rules.py` |
| head block structure | `merge_head_label_blocks` | `tests/test_render_layout_rules.py` |
| add a whole new arrangement | `register_layout_policy`, no consumer edit | `tests/test_render_layout_policy.py` limb 3 |
| add a NEW layout decision | a field here, a `layout.<field>` read in the consumer, and a row in `_CONSUMERS` | `tests/test_render_layout_policy.py` limb 2 |

## Traps

- **The pack's `## id` headers may not be merged, however small the
  sections.** A dropped section leaves no header and no placeholder, so the
  header's presence is the ONLY signal that a section survived allocation
  (`DR-CON-packs-and-token-economy`). The block-structure rule is therefore
  implementable in the prompt HEAD and precluded in the pack, and a future
  reader who "finishes the job" by merging pack sections would silently
  destroy the drop signal.
`check: python -m pytest tests/test_frame_render.py::test_a_dropped_citable_legend_is_disclosed_in_the_pack -q`
- **Adding a carry-forward site with `_head` instead of `_distilled` bypasses
  the policy without touching it.** The remaining `_head` call sites are the
  three that are NOT carry-forward of prior conjectures — the retry pack,
  standing attacks, and support content — and their count is pinned rather
  than their intent asserted, because a fourth would be a bypass.
`check: python -c "
import pathlib
src = pathlib.Path('src/deepreason/llm/packs.py').read_text()
assert src.count('_head(state,') == 3, src.count('_head(state,')
assert 'def _distilled(' in src
"`
- **`cli/doctor.py`'s qualification probes carry the OLD judge shape on
  purpose.** Changing them would move a qualification subject digest, which
  the 2026-08-28 tranche was forbidden to do, so the battery tests a judge
  arrangement the run no longer uses. Disclosed rather than closed; the
  follow-up is parked at
  `experiments/2026-08-28-change-render-layout-robust/PARKED.md`.
`check: grep -q "QUESTION: does the case establish a " src/deepreason/cli/doctor.py && ! grep -q "layout" src/deepreason/cli/doctor.py`
