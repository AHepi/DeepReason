# EXEMPLARS — the P-C2b dropped construction, traced end to end

The opening case. `experiments/2026-08-27-pc2b-symmetric-reasoning/RESULTS.md`
says it in one sentence:

> **The harness wrote a good, honestly-claimed construction and never scored
> it.**

This file answers the question that sentence leaves open: **where exactly did
it fall out, and was it dropped for being prose?**

The short answer, stated first because it is the answer the audit was
commissioned to find: **no.** It was not dropped for its kind. It was dropped
by an all-or-nothing decomposition that ran out of token budget, and the four
candidates that WERE scored are the same kind of object as the one that was
lost — prose claims with prose counterconditions, no checker attached to any of
them. Nothing in the trace reads a formal/informal distinction at any step.

---

## 1. Reproducing the two populations

`report_card.json` records 6 blob-level constructions, 1 VALID.
`arm_h_scores.json` records 4 artifact-level candidates, 0 valid.
Re-derived here with the committed instruments, unmodified
(`pc1_headline.constructions_from_root` + `checker.check`):

| # | log seq | role | checker verdict | score (exact) | claim |
|---|---|---|---|---|---|
| 1 | **58** | conjecturer | **VALID** | `127781713/10000000000` | 0.01276 |
| 2 | 63 | conjecturer | CLAIM_INFLATED | 0 | 0.005 |
| 3 | 90 | conjecturer | CLAIM_INFLATED | 0 | 0.005 |
| 4 | 90 | conjecturer | CLAIM_INFLATED | 0 | 0.005 |
| 5 | 90 | conjecturer | CLAIM_INFLATED | 0 | 0.005 |
| 6 | 90 | conjecturer | CLAIM_INFLATED | 0 | 0.005 |

The good one is **seq 58**. The four that became artifacts are the four from
**seq 90**.

## 2. The dropped construction, verbatim

`blobs/24/240404148efc5c5ab5613ecb5aaac7823f06afa7fb44cf1eedd7ea77ab082c19`,
the raw provider response at seq 58, in full:

````
```json
{
  "candidate": {
    "claim": "POINT 0.990000 0.500000\nPOINT 0.933870 0.727710\nPOINT 0.778350 0.903260\nPOINT 0.559060 0.986430\nPOINT 0.326250 0.958150\nPOINT 0.133230 0.824930\nPOINT 0.024240 0.617260\nPOINT 0.024240 0.382740\nPOINT 0.133230 0.175070\nPOINT 0.326250 0.041850\nPOINT 0.559060 0.013570\nPOINT 0.778350 0.096740\nPOINT 0.933870 0.272290\nCLAIM 0.012760",
    "mechanism": "Thirteen points are placed evenly on a circle of radius 0.49 centered at (0.5, 0.5), which maximizes the minimum area of any triangle formed by three consecutive points while keeping all points within the unit square. The minimum area triangle is formed by three adjacent points, yielding a score of approximately 0.01276.",
    "counterconditions": [
      "Any three points are collinear, reducing the minimum area to 0.",
      "A point falls outside the unit square [0,1]x[0,1].",
      "The claimed minimum area exceeds the actual computed minimum area from the 286 triangles."
    ],
    "typicality": 0.8,
    "sidecar": {
      "search_signal": "productive",
      "requested_context_aliases": []
    }
  }
}
```
````

Three prose counterconditions. No `checker_specs`. This is a **prose-kind**
candidate by every operationalization in `kind_census.py` — and so are the four
that were scored.

## 3. Where it fell out

`log.jsonl`, seq 58, `llm.attempt_trace[0]`:

```
contract_id : conjecturer.atomic-candidate.v1
valid       : true
tokens      : 8888
```

**Wire-valid.** It passed the contract. The candidate object exists, admitted,
in the record.

The state diff at seq 58 is empty (`"A+": []`). Walking every artifact addition
in the whole root:

| log seq | rule | artifacts added |
|---|---|---|
| 6–9, 75, 136, 147, 190, 233 | `Refl` | reflexive infrastructure |
| **99** | **`Conj`** | **the four scored candidates** |
| 102–117 | `Register`/`Crit` | critics and their validity nodes |

**One `Conj` event in the entire run**, at seq 99, and it carries the four
seq-90 candidates. Ten conjecturer calls were made (seq 27, 32, 37, 42, 47, 52,
58, 63, 90, 249); eight of them minted nothing.

The reason is in `objects/workflow-contract-decomposition-transition-v1`:

```
atomic_contract_id : conjecturer.atomic-candidate.v1
maximum_children   : 6
child_keys         : candidate-slot-000 .. candidate-slot-005
source_contract_id : conjecturer.turn.v6      (attempt_index 4)
coverage           : all_deterministically_assigned_children
```

A full `conjecturer.turn.v6` turn had failed four times, so the harness
decomposed it into **six single-candidate child calls**. The work terminals
tell the rest:

| status | reason_code | count |
|---|---|---|
| budget_denied | `token_budget_denied` | **50** |
| rejected | `conjecture_repair_step_rejected` | 3 |
| completed | `semantic_admission_complete` | 2 |
| rejected | `conjecture_repair_requested` | 2 |
| **completed** | **`atomic_conjecture_output_admitted`** | **2** |
| schema_exhausted | `conjecture_schema_exhausted` | 1 |

**Exactly two children were admitted** — seq 58 and seq 63 — and the rest hit
the token budget.

`rules/conj.py::_v6_atomic_conjecture_fallback` (line 450) accumulates children
in a local list and returns only after the loop over ALL of them:

```python
for child_index in range(child_count):
    ...
    authorized = service.issue(preparation, ...)      # raises WorkBudgetDenied
    ...
    candidates.extend(output.candidates)
...
return combined, calls
```

There is no `except WorkBudgetDenied` inside that loop. When child 2 was
denied, the exception unwound past the accumulated `candidates` list, and the
two admitted children — including the run's best construction — went with it.
The run later made a fresh `conjecturer.turn.v6` call (seq 90), which
succeeded, and those four became the scored artifacts.

## 4. Was it a prose penalty?

No, and the trace rules it out three separate ways:

1. **The two populations are the same kind.** The dropped candidate and the
   four scored ones all carry prose counterconditions with no `checker_spec`;
   none is battery-carrying on its own authored surface. If kind were doing the
   work, all six would have gone the same way.
2. **No kind signal is read anywhere on the path.** `_v6_atomic_conjecture_fallback`
   reads `transition.route_lease`, `atomic_contract_id`, `maximum_children`,
   and the reservation. It does not consult `execution_backed`,
   `formally_backed`, `programs.evaluable`, or any commitment.
3. **The failing terminal names the cause.** `token_budget_denied`, 50 times.

The defect is real and it is expensive — the run's best answer was lost — but
it is a **budget-and-transaction defect, not a formalism one**. It is parked as
`PARKED.md` P1, with a ready-to-send prompt.

## 5. What the incident DOES show about prose

One thing, and it is worth stating because it is what the operator noticed.
The construction that got lost was the honest one: it claimed 0.01276 against a
true 0.0127781713, under-stating by 0.00002. The four that survived all claimed
exactly 0.005 — the registered floor — against a true 0.0. The harness's
surviving population was, by accident of budget, the dishonest half. Nothing in
the code chose that. But a run whose admission path can drop two of six
children on a budget denial has no guarantee that what reaches scoring is what
was best, and the record cannot distinguish "the model wrote nothing better"
from "the better thing was written and dropped" unless someone reads the blobs.
