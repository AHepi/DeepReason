<!-- DR-CON-criticism-source -->
Verified-at: 445ca295
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

## Traps

See `DR-SUB-rules`'s Traps for package-wide hazards and `DR-CON-authority`'s
Traps for the authority vocabulary hazards, both of which bind this socket
without being re-derived here. Socket-specific:

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
