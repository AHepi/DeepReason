# Responsibility map

This is the strongest surviving conjectural boundary. The grounded bridge did not validate it as a final answer.

| Concern | Deterministic software or immutable policy | Bounded model responsibility | Interface |
|---|---|---|---|
| Routes, budgets, phase graph, permissions, retry ceilings, stopping | Compile and enact | None | Versioned policy plus route lease |
| Work scheduling | Select enabled typed transition and emit work order | None | `WorkOrder` with one task and capability set |
| Conjecture and reframing | Bound, persist, and admit | Generate open semantic proposals | Role-specific proposal contract |
| Evidence acquisition | Authorize connectors, log request/result, validate identity | Formulate query or inspect evidence | `EvidenceRequest` / `EvidenceResult` |
| Formal epistemic state | Register artifacts and warrants; verify; adjudicate; replay | Propose only | Canonical ontology contracts and guard result |
| Scratch | Persist separately; retrieve; cover; fence | Author provisional blocks and links | Advisory-context receipt; no promotion primitive |
| Criticism | Assign foreign critics; execute deterministic checks | Find semantic defects and counterexamples | Typed scrutiny or executable counterexample |
| Repair | Localize rejection; cap and log attempts/exhaustion | Repair only the rejected payload or subtree | Typed diagnostic and immutable repair budget |
| Final composition | Freeze catalog; validate ledger and claim uses | Ledger classification, composition, review | Canonical two-stage grounded bridge |
| Client interaction | Shared application services translate intent to commands | Optional conversational interpretation | CLI/MCP/chat adapters with equivalent events |

The key mechanism is a capability-typed, event-sourced control plane with a pure transition reducer. Models return proposals; they never return executable controller decisions. Open-endedness is preserved inside proposal content, query formulation, semantic criticism, analogy, decomposition and reframing.
