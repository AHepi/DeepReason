<!-- DR-CON-criticism-source -->
Verified-at: 3688713ee
Verify: python tools/docs_verify.py
Owns: src/deepreason/rules/crit.py
Seams: DR-SEAM-rules-x-scratch
Seams-undocumented: criticism-source x authority, criticism-source x llm, criticism-source x manifest, criticism-source x scheduler

# Criticism source — where a target is attacked or scrutinised

## What it is

`rules/crit.py` is where a target artifact meets an attempt to refute it:
deterministic (`crit_program`, `crit_fuzz`, `try_counterexample` — no LLM)
and argumentative (`crit_argumentative`, `crit_argumentative_batch` — one
prose case per call, or one call over K targets). Every demonstrative path
constructs its warrant through one shared constructor; every argumentative
path is gated by `Config.ARGUMENTATIVE_AUTHORITY`/the manifest's frozen
`CriticismPolicyV1.authority` (`DR-CON-authority`) before a case can ever
become a status change. The socket is this module's contract, distinct
from `DR-SUB-rules`'s package-wide concern and from `DR-CON-authority`'s
concern (which governs ALL text adjudication, not only criticism's).

## The socket contract — what it promises, what it is handed, what it must never do

**Promises:** every demonstrative fail warrant this module mints goes
through the one shared constructor — never hand-built.
`check: test "$(grep -c 'register_fail_warrant(' src/deepreason/rules/crit.py)" -eq 5 && ! grep -q "WarrantType.DEMONSTRATIVE" src/deepreason/rules/crit.py`

`observe_only` records scrutiny and mints nothing: a critic-role artifact
with no warrants and a `["scrutiny", target, critic]` Measure — the
target's `Status` is untouched.
`check: python -m pytest tests/test_text_authority_policy.py -q -k 'keeps_prose_criticism_as_scrutiny or keeps_infrastructure_review_as_scrutiny'`

A manifest-bound (policy) call never rediscovers authority from a mutable
`Config`; passing no explicit policy value on a policy call raises rather
than defaulting.
`check: python -c "import pytest; from deepreason.rules.crit import _resolve_authority as r; pytest.raises(ValueError, r, None, None, policy_call=True)"`

**What it is handed:** the target artifact's id and its evaluable
commitments (for `crit_program`); the accepted generators and active/
promoted properties from `rules/experiment.py` (for `crit_fuzz`); the
critic's OWN school conditioning when school-routed — `critic_school_id`
and `critic_school_context` — never the target's school, author or
provenance, which the pack signature has no parameter to carry; and,
already resolved before the call, the authority mode governing whether a
sustained case may reach a trial at all.
`check: python -c "import inspect;from deepreason.llm import packs;s=inspect.signature(packs.render_crit_pack);assert 'school' not in ' '.join(s.parameters) and 'author' not in ' '.join(s.parameters), list(s.parameters)"`

**Must never do:** receive scratch content — no parameter exists to pass
it, not merely no caller that does.
`check: python -m pytest tests/test_prose_refutation_boundaries.py::test_the_criticism_pack_cannot_be_given_scratch -q`

Let a school criticise its own work.
`check: python -m pytest tests/test_prose_refutation_boundaries.py -q -k "the_criticism_prompt_never_names_an_author_or_a_school or a_school_can_never_be_scheduled_to_criticise_its_own_work"`

Test a specific trial mode rather than the coarse observe-or-try branch —
a new authority mode must not acquire a second, parallel route to a
warrant.
`check: ! grep -q 'if authority == "trial_required"' src/deepreason/rules/crit.py && test "$(grep -c 'if authority in _TRIAL_MODES:' src/deepreason/rules/crit.py)" = 2`

## Where it lives

| Aspect | File | Symbol |
|---|---|---|
| Deterministic entry points (no LLM) | `rules/crit.py` | `crit_program`, `crit_fuzz`, `try_counterexample` |
| Argumentative entry points | `rules/crit.py` | `crit_argumentative`, `crit_argumentative_batch` |
| The shared warrant constructor | `rules/warrants.py` | `register_fail_warrant` |
| Observe-only recording | `rules/crit.py` | `_observe_case` |
| Authority resolution (manifest word -> Config word) | `rules/crit.py` | `_resolve_authority`, `_authority` |
| Critic-side school conditioning | `rules/crit.py` | `_critic_execution` |
| What `crit_fuzz` probes with | `rules/experiment.py` | `accepted_generators`, `active_properties`, `promoted_properties` |

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| Whether a sustained prose case changes a status or is only recorded | `_resolve_authority`/`_TRIAL_MODES` here and `Config.ARGUMENTATIVE_AUTHORITY` — never the manifest (`DR-INV-frozen-surfaces`) | `tests/test_criticism_authority.py::test_observe_only_no_status_change` |
| What `observe_only` files | `_observe_case` (Measure inputs are compared against recorded roots) | `tests/test_text_authority_policy.py -k scrutiny` |
| Counterexample admission or its retry reason | `try_counterexample`; `Config.CX_RETRY_MAX` | `tests/test_criticism_authority.py::test_execution_counterexample_still_refutes_under_observe_only` |
| Which generators/properties `crit_fuzz` probes with | `rules/experiment.py` `accepted_generators`/`active_properties`/`promoted_properties` | `tests/test_experiment.py::test_refuted_generators_are_never_used` |
| Whether criticism may read the scratchpad | `DR-SEAM-rules-x-scratch` — a seam change, not isolated; follow `docs/map/REC-change-a-seam.md` | `tests/test_prose_refutation_boundaries.py -k scratch` |
| What a filed premise may cite, and how the citation is checked | `_file_attribution` / `_check_premise_citations` here; the checker itself is `DR-SUB-evidence` | `tests/test_p4_citable_evidence.py -k quote` |
| What an invited dispatch records about how the seat ANSWERED | `_file_attribution`'s `premise-answer:` Measure here; the tag's meaning is declared in `signals.py` under `DR-REC-add-signal`, never redefined here | `tests/test_premise_channel_loop.py -k "declined or uncited"` |
| What a critic may PROPOSE as the next question, and where that proposal goes | the OPTIONAL `successor_question` field on `ArgumentativeCriticOutput`/`BatchCase` (`DR-SEAM-llm-x-rules`); its DESTINATION is not here at all but a registered row in `DR-CON-successor-questions` | `tests/test_successor_law_line.py::test_the_contract_field_is_optional_on_both_criticism_outputs` |

This socket owns the FIELD and never the destination, and the separation is
structural rather than stylistic: a critic proposes in words, and where those
words go is a run's configuration.
`check: python -c "from deepreason.llm.contracts import ArgumentativeCriticOutput as O, BatchCase as B; assert 'successor_question' in O.model_fields and 'successor_question' in B.model_fields" && grep -q "^def crit_argumentative(" src/deepreason/rules/crit.py && ! grep -q "deepreason.successor" src/deepreason/rules/crit.py`

## Where an `observe_only` criticism goes next

Until 2026-08-26 the answer was NOWHERE, and that was measured rather than
suspected: across the two newest and largest committed roots, 0 of 196 LLM
attacks were ever exposed to a later conjecture dispatch
(`experiments/2026-08-26-run-anatomy-w2-criticism/RESULTS.md`). `_observe_case`
was writing a correct, durable record that nothing which makes the next
candidate ever read.

It is now read. `DR-CON-discharge-channel` walks the
`["scrutiny", target, critic]` Measures this module writes, together with
`state.att`, and renders what it finds into the conjecturer's binding block.
Nothing about this module changed — the channel is a READER of what
`_observe_case` already records — but the record shape it writes is now
LOAD-BEARING for a second consumer, so a change to those Measure inputs
silently empties the channel rather than merely altering a diagnostic.
`check: python -m pytest tests/test_discharge_channel.py::test_an_observe_only_criticism_is_open -q`
`check: grep -q 'inputs = \["scrutiny", target_id, critic.id\]' src/deepreason/rules/crit.py`

## Traps

See `DR-SUB-rules`'s Traps for package-wide hazards and `DR-CON-authority`'s
Traps for the authority vocabulary hazards, both of which bind this socket
without being re-derived here. Socket-specific:

- **A proposed successor question must stay UNREADABLE by anything that
  decides.** The field is optional and, unlike `premise`, carries no
  invitation and no disposition receipt on this side: there is nothing to
  decline, so declining costs nothing and filling it earns nothing (operator
  law 2026-08-29; the formalism-optional pattern). The failure mode this
  guards is quiet — a rank, admission or acceptance path that read the field
  would turn "the critic bothered to propose something" into a score, which is
  exactly what the law forbids and what no reviewer would notice in a diff.
  The absence is pinned over the four deciding packages, and the pin is
  mutation-proved
  (`experiments/2026-08-30-change-successor-questions/proof/law_line_pin1_red.txt`).
`check: python -m pytest tests/test_successor_law_line.py::test_nothing_that_labels_ranks_or_admits_reads_a_successor_question tests/test_successor_law_line.py::test_the_contract_field_is_optional_on_both_criticism_outputs -q`

- **A criticism topology that COMPILES is not one that can run.** Since
  2026-08-16 (`experiments/2026-08-16-change-configs-complete-seats-test/`,
  the all-configurations law) an incomplete critic binding roster, a
  non-critic role in a binding, an unsatisfiable foreign-coverage number, a
  `defended_trial` with no defender route, and a single-family judge matrix
  all COMPILE, each carrying a typed compile notice. None of them can produce
  a warrant: `informal/trial.py` `_block`s on a missing critic/defender/judge
  role before any call, `require_cross_family_judge_ensemble` raises
  `JudgeEnsemblePolicyError` from the immutable leases, and
  `workflow/criticism.py` raises `V4_CRITICISM_FOREIGN_COVERAGE_UNSATISFIED`.
  If you are diagnosing "the criticism policy compiled but nothing was
  criticised", read `compile_notices` on the manifest FIRST — the answer is
  usually already recorded there.
`check: python -m pytest "tests/test_all_configs_allowed_remainder.py::test_defended_trial_without_a_defender_compiles_with_a_notice" "tests/test_all_configs_allowed_remainder.py::test_defended_trial_with_a_single_family_judge_matrix_compiles_with_a_notice" -q && grep -q "SCHOOL_ROUTE_CRITIC_ROLE_MISSING" src/deepreason/scheduler/scheduler.py`
- **The two supremacy guards are not interchangeable.** `crit.py` consults
  `execution_backed` (narrow) because its guard also decides whether a case
  is RECORDED as scrutiny; `informal/trial.py` consults `formally_backed`
  (wide) because its guard decides a STATUS. Widening `crit.py`'s guard to
  match the trial's deletes scrutiny evidence for every target carrying a
  passing problem criterion.
`check: grep -q "formally_backed" src/deepreason/informal/trial.py && ! grep -q "formally_backed" src/deepreason/rules/crit.py`
- **The separation from the scratchpad is enforced by an AST walk, not a
  header grep.** A function-local `import deepreason.scratch...` inside
  `crit.py` would pass a naive check and still couple them; the single
  legitimate appearance of the word is `scratch_fence_seq`, ordering only.
`check: python -m pytest tests/test_prose_refutation_boundaries.py::test_the_criticism_rule_imports_no_scratch_module tests/test_prose_refutation_boundaries.py::test_the_criticism_rule_touches_scratch_only_as_an_ordering_fence -q`

- **This socket can now CITE, and a citation the critic never saw does not
  verify.** Under a standing premise invitation the pack carries the admitted-
  block legend and the contract carries `premise_evidence`, whose quote cannot
  be null. The check resolves against the blocks THIS call's exposure receipt
  records, so a real block id quoted from memory or from another call's context
  is `EVIDENCE_REF_NOT_EXPOSED` rather than a pass. A verified citation becomes
  an artifact the attribution DEPENDS on; an unverified one becomes a Measure
  and grounds nothing — the premise is still filed either way, because a bad
  citation is not a reason to lose the presupposition (P4, R62).
`check: python -m pytest tests/test_p4_citable_evidence.py -k "quote or attribution" -q && python -c "
from deepreason.llm.contracts import ArgumentativeCriticOutput as O, BatchCase as B
for model in (O, B):
    assert 'premise_evidence' in model.model_fields, sorted(model.model_fields)
"`

- **An invited dispatch always leaves a disposition; an uninvited one never
  does.** `_file_attribution` resolves the invitation BEFORE the premise text,
  and every invited call records exactly one
  `premise-answer:{DECLINED|UNCITED|CITED}` Measure — the seat's answer to a
  question the run actually asked. The order is the whole content of the fix:
  the earlier code returned on an empty premise without ever asking whether an
  invitation stood, so `_check_premise_citations` (which records nothing when
  `refs` is empty) was not even reached, and a seat that was ASKED and said
  nothing recorded what a seat that was NEVER ASKED recorded. Measured across
  the four committed technique roots, that made 93 never-asked dispatches
  indistinguishable from 4 asked-and-silent ones and 1 asked-and-uncited one
  (`experiments/2026-08-28-audit-run-problems/AUDIT_REPORT.md` §F-B). Silence
  is now a fact rather than an ambiguity, so DO NOT add a receipt to the
  uninvited path: it would destroy the very difference the receipt records.
  `CITED` says an array was submitted, never that it verified — the byte-check's
  own outcome stays on `premise-citation:`, which is what the M2 census counts,
  and this signal deliberately does not touch it.
`check: python -m pytest tests/test_premise_channel_loop.py::test_a_declined_invitation_is_typed_on_the_record tests/test_premise_channel_loop.py::test_a_premise_filed_without_citations_is_typed_as_uncited tests/test_premise_channel_loop.py::test_an_uninvited_dispatch_records_no_disposition tests/test_premise_channel_loop.py::test_a_declined_invitation_moves_no_status -q`
`check: python -c "import ast, inspect; from deepreason.rules.crit import _file_attribution; body = ast.parse(inspect.getsource(_file_attribution)).body[0].body; stmts = [n for n in body if not isinstance(n, (ast.Expr, ast.ImportFrom))]; first = ast.unparse(stmts[0]); assert '_premise_invited_problem' in first, first"`
