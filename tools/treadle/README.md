# treadle

Deterministic driver for evidence-disciplined formal programmes: point it at
a repo with a swarm board, hit play. It walks READY tasks in routed order,
claims through the repo's own swarm_gate.py, calls exactly one Ollama-cloud
model per stage (system prompt = the stage skill's PROMPT-CORE), writes
artifacts only inside the task's cone, runs the task's deterministic
acceptance command, and commits only what passes. Failures refine with the
verification output (MathForm pattern), escalate once to the stage's bigger
model, then requeue as BLOCKED with evidence. Review-kind stages send the
committed diff to a reviewer model and record the verdict via the gate.
No LLM orchestrator anywhere: order, gating, and merging are code
(LeanMarathon's two-stage shape — fidelity first, then gated discharge).

Provenance: every model call is hash-chained into .treadle/calls.jsonl
(model tag, params, prompt/reply hashes) — hosted checkpoints drift, the
ledger notices.

Install: see AGENT_INSTALL.md (written for the LLM agent doing the install).
Commands: `treadle doctor` | `treadle plan` | `treadle run [--once|--task ID]`.

Limits, stated: sequential across tasks by design (parallel candidates
within a stage only) — multi-worker concurrency stays with the swarm under
the gate; acceptance commands run with shell access, so briefs are trusted
input; the driver never seals records — owner act, always.
