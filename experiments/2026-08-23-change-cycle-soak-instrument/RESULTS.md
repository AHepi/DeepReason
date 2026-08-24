# RESULTS — offline cycle soak instrument

Dated, honest-ledger segments. "Accepted does not mean true." What the record
shows, then the residue.

---

## 2026-08-23 — the instrument lands, and catches a death on its first full run

**What the record shows.**

`scripts/cycle_soak.py` compiles a run from the committed reach-rich
`run-config.yaml` (endpoint and `api_key_env` overridden to the loopback,
every other field inherited), carries the three operator-authored
`predicate:` criteria through the manifest surface, enables attached
evidence, and drives `TextRunApplicationService.start_manifest_run` against
the wheel smoke's own stub.

Three measured runs, all on main `5d9b995ce` plus this tranche:

| run | cycles | induction | terminal | verify_root | exit |
|---|---|---|---|---|---|
| probe | 1 | none | `completed` / `budget_exhausted` | 0 violations | 1 (A4 only: depth 1 ≤ 2 by construction) |
| soak8, soak8b | 8 | none | `failed` / `operational_failure` — *transactional reservation bound differs from rendered request*, cycle 1 | 0 violations | 3 (expected-red only) |
| soakrep2, soakrep3 | 8 | 2 schemas | `failed` / same message | **1 violation**: `workflow-call-pairing`, `event seq=24: provider result differs from its authorized attempt` | 1 |

Cost: qualification 3.2 s, drive ~34 s, **zero provider tokens** — the stub is
loopback. R1 prices each live discovery of one of these at ~110k tokens.

**The finding, stated plainly.** The soak reproduced D4 offline on its first
full run. The message is identical to the live root
`failed-attempt3-run-bb045538…`, which died at cycle 2; the soak dies at
cycle 1. That death was previously reachable only by launching.

**The depth result is the load-bearing one, and it is not what I expected.**
The SAME configuration at `--cycles 1` terminates cleanly — `completed`,
`budget_exhausted`, `verify_root` 0 violations. At `--cycles 8` it dies at
cycle **1**. So the seam is not gated on reaching cycle 8; it is gated on the
run being AUTHORIZED to go deeper. A shallow run does not merely miss the
death, it does not have it. This is the precise mechanism by which the
operational smoke stayed green through four consecutive live deaths, and it
means depth of the BUDGET, not depth reached, is what the instrument must
carry.

**A second finding, from the induced probe.** `--induce-repairs` makes the
stub answer the run's first N wire schemas unusably once, so the repair ladder
runs. Under it the run produces a record `verify_root` rejects
(`workflow-call-pairing`), deterministically across two runs. This is
adapter/transaction code, which R8 puts under a stop — parked as **P1** with
a reproduction, not fixed. Its witness is synthetic (a real provider fails
validation for its own reasons), and PARKED.md says so; whoever picks it up
decides first whether an induced fault is admissible here.

**Residue — what remains unproven.**

- Whether P1 is a defect or an artifact of synthetic induction. Not decided
  here, and this tranche is not entitled to decide it.
- Whether the soak stays green once D4 is fixed. **It has never been observed
  green at depth**, because D4 kills every deep run. Exit 0 is the baseline
  this tranche records but not a value it has measured. That is a real gap in
  the evidence, and it closes only when the parallel window's fix lands.
- Whether cycle 8 specifically is the right threshold. The recorded deaths sit
  at cycles 0–2, so any budget above 2 exposes D4; 8 is the committed carrier
  threshold, adopted rather than derived.
- The soak's manifest sha256 varies between runs because the loopback port is
  dynamic and the endpoint is genuinely part of the compiled config. The
  instrument pins no manifest, so nothing depends on it — but a reader
  comparing two soak reports should not read the difference as drift.
- The `reach-rich` case (attached evidence OFF) is defined and selectable but
  was not run for this segment.

---

## Seam coverage — the standing honesty rows (SPEC S4)

Coverage is measured from typed record objects under `<root>/objects/`, never
from prose. A seam that was never reached is reported `not-coverable`, never
as passing: an assertion that only checks for absence goes green on a run that
never reached the code, which is exactly the false comfort this tranche exists
to remove.

| seam | disposition (default soak) | honest reading |
|---|---|---|
| `D1-seat-contract` | **partial** by default; **covered** only under `--induce-repairs` | Seat contracts ARE exercised — 4–5 attempts on `conjecturer.turn.v6`, every one carrying a contract id. The REPAIR half is not: the deterministic stub always returns a schema-valid response, so `attempt_index` never advances past 0. The original death (route-seat capability exhaustion) is reached by repairing against a contract until it exhausts, so the default soak does NOT cover the shape D1 actually died of. `--induce-repairs` reaches the ladder, and immediately surfaces P1. |
| `D2-route-lease` | **covered** | Every attempt carries a complete `route_lease` (role, seat, `route_sha256`); zero attempts lack one. `ROUTE_LEASE_MISMATCH` absent. The "with tuning" half is weaker than the label suggests — no logged controller adjusted `max_tokens` during these runs, so the soak proves the lease is CHECKED, not that it survives tuning. |
| `D3-budget-auth` | **covered** | 5–6 `workflow-dispatch-authorization-v1` records; no budget denial. Note the runs above set no finite token budget, so the denial path itself is not exercised — only the authorization path that precedes it. Passing `--token-budget` would exercise the denial; that was not run for this segment. |
| `D4-reservation-bound` | **failed**, expected-red | Reproduced deterministically; see above and PARKED.md P2. |

Two of the four rows above are weaker than a green tick would suggest (D2's
tuning half, D3's denial half), and D1's default row is weaker still. They are
written here rather than smoothed because a soak that reads as coverage it
does not have is worse than no soak.
