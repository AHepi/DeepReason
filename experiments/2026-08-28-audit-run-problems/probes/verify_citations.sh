#!/bin/sh
# Every file:line this audit asserts, re-checked against the tree at HEAD.
# Exits 0 only if all of them still point where the report says they do.
set -u
fail=0
chk() { # chk <label> <file> <line> <expected substring>
  got=$(sed -n "${3}p" "$2")
  case "$got" in *"$4"*) echo "OK   $1  ($2:$3)";;
  *) echo "MISS $1  ($2:$3) -> $got"; fail=1;; esac
}
chk "config_from_run_manifest"      src/deepreason/run_manifest.py 4287 "def config_from_run_manifest"
chk "criticism_policy default None" src/deepreason/run_manifest.py 1251 "criticism_policy: CriticismPolicyV1 | None = None"
chk "criticism_policy popped"       src/deepreason/run_manifest.py 1363 'payload.pop("criticism_policy", None)'
chk "drop list start"               src/deepreason/run_manifest.py 2363 "_versioned_source_config_data"
chk "SEED_PROBLEM_BUDGET_FLOOR pop" src/deepreason/run_manifest.py 2393 'data.pop("SEED_PROBLEM_BUDGET_FLOOR", None)'
chk "ATTENTION_ALLOCATION pop"      src/deepreason/run_manifest.py 2394 'data.pop("ATTENTION_ALLOCATION_POLICY", None)'
chk "JUDGE_SEATS_ENABLED default"   src/deepreason/config.py 542 "JUDGE_SEATS_ENABLED: bool = False"
chk "ENGAGED_CRITICISM default"     src/deepreason/config.py 520 'ENGAGED_CRITICISM_AUTHORITY: Literal'
chk "SEED floor default"            src/deepreason/config.py 295 "SEED_PROBLEM_BUDGET_FLOOR: float"
chk "ATTENTION policy default"      src/deepreason/config.py 310 'ATTENTION_ALLOCATION_POLICY: str = "wander-cap.v1"'
chk "_TRIAL_MODES"                  src/deepreason/rules/crit.py 79 "_TRIAL_MODES = frozenset"
chk "observe_only returns"          src/deepreason/rules/crit.py 1600 "observe_only"
chk "judge seats gate"              src/deepreason/scheduler/scheduler.py 1346 "JUDGE_SEATS_ENABLED"
chk "judge summons gate"            src/deepreason/scheduler/scheduler.py 1060 "_judge_summons_admitted"
chk "premise_work_invited"          src/deepreason/premises.py 625 "def premise_work_invited"
chk "PREMISE_INVITE_AFTER"          src/deepreason/premises.py 68 "PREMISE_INVITE_AFTER = 2"
chk "the latch"                     src/deepreason/premises.py 638 "standing_attributions(harness)"
chk "_premise_invited_problem"      src/deepreason/rules/crit.py 1268 "def _premise_invited_problem"
chk "_check_premise_citations"      src/deepreason/rules/crit.py 1368 "def _check_premise_citations"
chk "_file_attribution"             src/deepreason/rules/crit.py 1401 "def _file_attribution"
chk "_citable_blocks"               src/deepreason/rules/crit.py 1283 "def _citable_blocks"
chk "exposed_block_ids_for_call"    src/deepreason/rules/crit.py 1341 "def _exposed_block_ids_for_call"
chk "lifecycle refusal"             src/deepreason/workflow/lifecycle.py 217 "STOPPED refuses unfinished workflow authority"
chk "RESUMABLE_STOP_REASONS"        src/deepreason/workflow/lifecycle.py 28 "RESUMABLE_STOP_REASONS = frozenset"
chk "the swallow"                   src/deepreason/application/text_runs.py 246 "return None"
chk "the swallow except"            src/deepreason/application/text_runs.py 245 "except ValueError:"
chk "success token_spend"           src/deepreason/application/text_runs.py 1442 "token_spend=sum("
chk "progress default 0"            src/deepreason/runtime/progress.py 55 "token_spend: int = Field(default=0"
chk "results reads status"          src/deepreason/application/results.py 172 'status.get("token_spend"'
chk "results prints"                src/deepreason/application/results.py 510 "tokens spent vs budget"
chk "WorkBudgetDenied"              src/deepreason/workflow/transaction.py 691 "class WorkBudgetDenied"
chk "atomic re-raise"               src/deepreason/workflow/atomic_recovery.py 39 "raise WorkBudgetDenied"
chk "atomic repair branch"          src/deepreason/workflow/atomic_recovery.py 68 'task_kind.value == "repair"'
chk "repair mode check"             src/deepreason/workflow/nonconjecture_recovery.py 1002 '"repair mode is invalid"'
chk "repair authority call"         src/deepreason/workflow/nonconjecture_recovery.py 1194 "_repair_authority"
chk "producer Literal"              src/deepreason/llm/repair.py 1505 'Literal["initial", "whole_object_syntax", "patch"]'
chk "producer emit"                 src/deepreason/llm/repair.py 1612 'mode="whole_object_syntax"'
chk "retryable http"                src/deepreason/llm/endpoints.py 15 "_RETRYABLE_HTTP"
chk "request_with_retries"          src/deepreason/llm/endpoints.py 51 "def request_with_retries"
chk "EndpointError class"           src/deepreason/llm/endpoints.py 42 "class EndpointError"
chk "_failure_code"                 src/deepreason/cli/doctor.py 415 "def _failure_code"
chk "capability early return"       src/deepreason/scheduler/scheduler.py 2052 "_simulation_capability_step()"
chk "cycles increment"              src/deepreason/scheduler/scheduler.py 2053 "self._cycles += 1"
chk "select_problem call"           src/deepreason/scheduler/scheduler.py 2056 "self._select_problem()"
chk "disclose_wander call"          src/deepreason/scheduler/scheduler.py 2061 "self._disclose_wander()"
chk "wander decide"                 src/deepreason/scheduler/scheduler.py 1130 "wander.decide"
chk "count_lineage"                 src/deepreason/scheduler/scheduler.py 1214 "def _count_lineage"
chk "SpawnTrigger enum"             src/deepreason/ontology/problem.py 20 "class SpawnTrigger"
chk "SUCCESSOR inert"               src/deepreason/ontology/problem.py 30 'SUCCESSOR = "successor"'
chk "AUDIT_CRITIC"                  src/deepreason/ontology/problem.py 34 'AUDIT_CRITIC = "audit-critic"'
chk "spawn conn:"                   src/deepreason/rules/spawn.py 172 'f"conn:'
chk "spawn disc:"                   src/deepreason/rules/spawn.py 80 'f"disc:'
chk "preparation wiring"            src/deepreason/preparation.py 506 "ENGAGED_CRITICISM_AUTHORITY"
echo
[ $fail -eq 0 ] && echo "ALL CITATIONS RESOLVE" || echo "SOME CITATIONS MISSED"
exit $fail
