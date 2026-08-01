# Implementation sequence

1. Add characterization and adversarial tests around current scheduler, adapter, stop, scratch, bridge, replay, CLI, MCP and MiniReason behaviour.
2. Define immutable `WorkOrder`, `ProposalResult`, `GuardResult`, `TransitionDecision` and `StopDecision` records and a pure reducer. Run it in shadow mode against the existing scheduler.
3. Add a new manifest version that freezes controller version, workflow graph, explicit school-to-route bindings, capability grants and workflow-level retry policy. Keep v1-v3 loaders and replay unchanged.
4. Emit an event for every enabled, rejected, repaired, exhausted, advanced, paused, resumed and stopped transition. Add state-digest replay assertions.
5. Integrate scratch attention and evidence acquisition as explicit controller states. Converting scratch into a formal candidate must require a fresh typed model call and normal admission; no direct promotion API should exist.
6. Replace broad orchestration prompts role by role with bounded semantic work orders. Keep prompt text as presentation guidance where semantic judgment is desired.
7. Put CLI, MCP, MiniReason and future chat behind the same application services, with client-specific parsing outside the controller.
8. Retain the grounded two-stage bridge as the sole final composer; separately repair the observed compact-ledger handle confusion before production cutover.
