<!-- DR-TRANCHE-F3 -->
# Measurements — the qualification-digest cost of turning research on (S7, R6)

R6, the operator's own instruction: "Report the qualification-digest cost per
the standing rule (defaults changing the profile means new subject digests —
price it, don't stop)."

## The cost, in one table

| what | before (4760a32ef) | after |
|---|---|---|
| inquiry-capability policy digest | `b1aa948f8aa0201b551a5f1bdbd6e7f6def4f5e51bfdb7ce670c448910fdd431` | `6fb099ad932fa1afe06e4321936b5f797f0204d8f6ef0a39b49510f87a6c0b08` |
| shipped qualification subject digest | `d47cb2bf27021474aa17933bc3dcfeeb5dfb1c23b0cfe49452941aace39088dc` | `f3bb65623852cf7c5387ba4ef745dc4ebeadb62ca3493416fecfb475c6d80f9e` |
| `source_config_hash`, every schema version | `6c2d01f6…` (v1/v2), `2624603035bc335e59da63f25426d3ae6619bf7f84d48657e8f25310de49edc5` (v3–v6) | **identical** |

**One cause, not two, and the separation is checked rather than argued.** The
subject digest moved because research now compiles ENABLED with a frozen
allowlist — the operator's own change. The three new `Config` knobs moved
NOTHING: each has an unconditional `data.pop` line in
`_versioned_source_config_data`, so `source_config_hash` is byte-identical at
every schema version, and `test_the_shipped_qualification_subject_digest_does_not_move`
now asserts both facts side by side so a future move cannot be misattributed.

## What it costs an operator

One full requalification battery per `DEEPREASON_HOME` — roughly 14 minutes
and ~1160 provider calls (CLAUDE.md, "Live runs"; the shipped ceiling is
`production_qualification_maximum_provider_calls(manifest) == 1140` plus the
bounded flake re-exercise allowance). Nothing is lost: an existing home's
cached verdict simply refers to a subject that no longer exists, and the next
`deepreason qualify --yes` rebuilds it.

Naming a different research allowlist costs the same battery again, which is
by design — a different list is a different containment authority and
therefore a different subject.

## Goldens updated, and why each was predicted

| golden | why it moved |
|---|---|
| `tests/test_allocation_signal_consumption.py::test_the_shipped_qualification_subject_digest_does_not_move` | the subject digest above; the test's two structural assertions are unchanged |
| `tests/test_v6_policy_preset.py::test_engaged_research_policy_is_on_by_default_and_the_env_names_the_list` | renamed from `..._is_operator_opted_and_default_silent`; the OFF state it pinned is still pinned, now through the channel registry |
| `tests/test_v6_policy_preset.py::test_engaged_simulation_policy_is_declarative_local_and_modest` | one line: `topology.research.enabled` is now True |
| `tests/test_v6_engaged_public_defaults.py::test_public_manifest_enables_declarative_local_simulation` | the same line, plus three ROAD assertions (non-empty allowlist, positive request and source budgets) that were not there before |
| `tests/test_v6_reservation_bound_authority.py` (2 tests) | Phase A, unrelated to the digest: the booked completion envelope is now the settled cap. The equality chain each test guarantees is intact; only the constant moved |
| `tests/test_single_run_path.py::test_the_grounded_tranche_config_enters_through_the_new_door` | the recompiled manifest differs from an August 2026 committed one in exactly `inquiry_capability_policy.research`, and the test now PINS that delta rather than waiving the field |

Six test files, seven tests. No assertion was weakened: in every case the
guarantee the test carries is still asserted, and only a constant the design
predicted would move has moved.

## One naming decision this measurement forced

`SEED_LINEAGE_BUDGET_FLOOR` and `LINEAGE_ALLOCATION_POLICY` became
`SEED_PROBLEM_BUDGET_FLOOR` and `ATTENTION_ALLOCATION_POLICY`. Every `Config`
field is echoed BY NAME inside `run_manifest.py`'s versioned-source drop list,
and `DR-SEAM-manifest-x-schools` holds — with a `check:` — that the words
`stance`, `lineage`, `crossover` and `reseed` do not occur in that file at all.
That tripwire keeps the manifest unable to describe what a SCHOOL is. The
concept here is a PROBLEM lineage and has nothing to do with schools, but a
blunt tripwire is worth more than a word: the alternative was carving an
exception into a check whose whole value is that it has none. `wander.py` keeps
the operator's own vocabulary throughout, and no committed root carries either
name.
