"""The discharge-required criticism channel (REBUILD F1) -- the whole interface.

Criticism recorded and routed nowhere does no causal work. W2 measured that on
this tree: 0 of 196 LLM attacks were ever exposed to a later conjecture
dispatch (`experiments/2026-08-26-run-anatomy-w2-criticism/RESULTS.md`). This
package is the structural answer the external protocol names -- criticism in
the writer's WORKING CONTEXT, with submission requiring it DISCHARGED
(`docs/RESEARCH_FINDINGS_Q1Q10_2026-08-22.md` Q5) -- and NOT the obvious
alternative, an acknowledgment requirement, which the same source measured as
actively harmful.

**This module is the only thing consumers may import.** Reaching into
`policy`, `channel` or `submission` directly is what
`tests/test_discharge_contract.py::test_no_consumer_reaches_past_the_interface`
exists to fail on. The package's own dependencies are confined to
`deepreason.ontology`, `deepreason.config` and `deepreason.programs`: the
render returns a plain STRING, so the pack layer never learns that criticism
is what it is rendering, and this package never learns what a pack is.

See `DR-CON-discharge-channel` for the three layers, the law line, and why
reading only `state.att` would reproduce the very defect this closes.
"""

from deepreason.discharge.channel import (
    OpenCriticism,
    open_criticisms,
    render_open_criticism_context,
)
from deepreason.discharge.submission import (
    SubmissionScreening,
    record_discharges,
    screen_submission,
)
from deepreason.discharge.policy import (
    DECLARED_FIELDS,
    DISCHARGE_KIND_DECLARATIONS,
    DISCHARGE_POLICY_PRESETS,
    DischargeKindDeclaration,
    DischargePolicyV1,
    UnknownDischargeKindError,
    UnknownDischargePolicyError,
    declaration,
    discharge_kind_names,
    resolve_policy,
)

__all__ = [
    "DECLARED_FIELDS",
    "OpenCriticism",
    "SubmissionScreening",
    "DISCHARGE_KIND_DECLARATIONS",
    "DISCHARGE_POLICY_PRESETS",
    "DischargeKindDeclaration",
    "DischargePolicyV1",
    "UnknownDischargeKindError",
    "UnknownDischargePolicyError",
    "declaration",
    "discharge_kind_names",
    "open_criticisms",
    "record_discharges",
    "render_open_criticism_context",
    "screen_submission",
    "resolve_policy",
]
