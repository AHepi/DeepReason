# Request: maximum modularity, open exploration, and no formalism rank

Captured: 2026-09-01 from the operator's three consecutive messages following
the four review documents and the accepted design response.

## Verbatim

> What are your thoughts about using these for improvements? Remember maximum modularity and configurability is essential. As well as usability by other humans.

> Hmm. A standing rule is that formalism shouldn't out rank valid prose. And since prose isn't always mechanically valid, I'm afraid that vocabulary will wipe almost everything from the board. Also, the harness is inherently anti inductivist and tries to avoid mechanically defining optimisation targets or statistical tightening of any sort. It's also meant to allow open exploration without the mechanical constraint that may hinder it. Heuristics imply something about the problem space being known, but in popperian epistemology, that's reductionist and inductivist and inherently hinders creativity. Which is what I was trying to create with DeepReason.

> Perfect! Can you get started?

## Requirements

R1 (behavior): "using these for improvements"

R2 (behavior): "maximum modularity and configurability is essential"

R3 (behavior): "usability by other humans"

R4 (behavior): "formalism shouldn't out rank valid prose"

R5 (behavior): "prose isn't always mechanically valid"

R6 (behavior): "the harness is inherently anti inductivist and tries to avoid mechanically defining optimisation targets or statistical tightening of any sort"

R7 (behavior): "It's also meant to allow open exploration without the mechanical constraint that may hinder it."

R8 (behavior): "Heuristics imply something about the problem space being known, but in popperian epistemology, that's reductionist and inductivist and inherently hinders creativity."

R9 (behavior): "Which is what I was trying to create with DeepReason."

R10 (process): "Perfect! Can you get started?"

## Standing constraints

C1: "There shouldn't be any reasons why defended trial is rejected." — operator clarification earlier in this conversation

C2: "The point is maximum configurability. Observe only should be easily switched off." — operator clarification earlier in this conversation

C3: "If you're trying to ensure previous runs are compatible, don't. It's not a guarantee yet" — operator clarification earlier in this conversation

## Map preflight

The operator's words name a cross-cutting design boundary rather than a source
file. The candidate map route, to be narrowed by `dr-spec-change` before any
code design, is:

- `DR-CON-conjecture-source`
- `DR-CON-criticism-source`
- `DR-CON-conjecture-kinds`
- `DR-CON-authority`
- `DR-SUB-ontology`
- `DR-SUB-rules`
- `DR-SUB-evaluation`
- `DR-SEAM-ontology-x-rules`
- `DR-SEAM-evaluation-x-ontology`
- `DR-SEAM-evaluation-x-rules`
- `DR-SEAM-adjudication-x-authority`
- `DR-SEAM-adjudication-x-rules`
- `DR-INV-frozen-surfaces`

No frozen-surface contact is authorized by the messages captured here.

## Open questions (for dr-spec-change)

Q1: Which concrete first increment is contained by "using these for improvements" and the immediately preceding response the operator called "Perfect"?

Q2: Does "get started" authorize the first implementable tranche or only a design artifact?

Q3: Which human-facing surface should make the resulting configuration understandable?

Q4: Can the first increment be completed without contact with any frozen surface?

## Amendments

(none yet)
