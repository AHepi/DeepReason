verdict: HOLDS
request_budget: ORDINAL
execution_budget: COUNT
filter: isinstance

# Justification

**request_budget** is determined by an ordinal position in a sorted list:

- The code builds `ordered_requests` sorted by `(item.source_call_seq, item.proposal_index, item.id)`.
- It then computes the ordinal with the exact expression:

```python
request_ordinal = ordered_requests.index(proposal) + 1
```

- The budget check uses that ordinal:

```python
if request_ordinal > self.policy.maximum_simulation_requests:
    reason = "request_budget_exhausted"
```

Thus the request budget is based on an **ORDINAL** (position), not a simple count.

**execution_budget** is determined by counting matching work orders:

- The code counts with the exact expression:

```python
simulation_executions = sum(
    1
    for order in self.harness.capability_state.work_orders.values()
    if isinstance(order, SimulationWorkOrderV1)
)
```

- The budget check compares this count:

```python
if (
    reason is None
    and simulation_executions >= self.policy.maximum_simulation_executions
):
    reason = "execution_budget_exhausted"
```

Thus the execution budget is based on a **COUNT** of items.

**filter**: The code filters by type using the Python builtin `isinstance` on two capability classes:

- For proposals:

```python
if isinstance(item, SimulationProposalV1)
```

- For work orders:

```python
if isinstance(order, SimulationWorkOrderV1)
```

Therefore the filter builtin is `isinstance`, and the two class names tested are `SimulationProposalV1` and `SimulationWorkOrderV1`.

**What could not be established:** None; all required facts are directly observable in the provided code.

