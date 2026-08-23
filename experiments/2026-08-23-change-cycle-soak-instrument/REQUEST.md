# REQUEST — offline cycle soak instrument

Tranche opened 2026-08-23. Route: `dr-change-orchestrator`.
Branch: `claude/cycle-soak-instrumentation-8e0vp7`. Base: main `5d9b995ce`.

Authority is the operator's words, verbatim, below. Every later artifact
cites requirement numbers from this file. A requirement is never deleted,
only marked `superseded-by:<n>` or `deferred (operator approved <where>)`.

## Map preflight (dr-drive-harness §4)

Resolved before routing, recorded here so every later phase starts from the
same map.

| id | why this tranche touches it |
|---|---|
| `DR-SUB-llm` | seat contracts, route firewall, leases, repair, and the reservation bound at `llm/adapter.py:1400` — the code the soak DRIVES |
| `DR-SUB-workflow` | v6 transactional work lifecycle: dispatch authorization, reservation, budget denial |
| `DR-SUB-scheduler` | cycles and budgets — the soak's N-cycle axis |
| `DR-SUB-manifest` | `compile_run_manifest` renders the config shape under test. **FROZEN** — read only |
| `DR-SUB-verification` | `verify_root` is a soak assertion. **FROZEN** — read only |
| `DR-CON-seats` | `select_lease` / `EndpointLease` — D1 and D2 both land here |
| `DR-SEAM-llm-x-workflow` | coupling 33; the seam D3 and D4 die on |
| `DR-SEAM-scheduler-x-workflow` | coupling 16; cycle advance across the transactional boundary |
| `DR-SEAM-llm-x-manifest` | coupling 24; route/lease fields originate in the compiled manifest |

`INV-frozen-surfaces.md` read first, per the ordering rule. **This tranche
requests no frozen-surface contact.** It adds a script, a docs baseline row,
and two documentation sentences; it changes no `src/` file. The two frozen
subsystems above are DRIVEN and READ, never modified. If any step turns out
to require a `src/` edit, that is a stop condition (R11).

## Requirements

### R1 — the motivating record (authority for the whole tranche)

> four consecutive live runs died before cycle 3 with four DIFFERENT typed
> operational causes (V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY,
> ROUTE_LEASE_MISMATCH, WorkBudgetDenied, WorkflowAuthorizationError —
> roots committed under experiments/2026-08-22-live-reach-rich-run/ and
> .../2026-08-22-change-epoch3-second-lineage/), while the operational
> smoke passes — because the smoke's stub path never renders this
> configuration's shape (operator-authored predicate: criteria,
> attached-evidence manifest, supplements) and never runs past its short
> stage. Each live discovery cost ~110k tokens; the bench version costs
> zero.

Verified against the committed roots before this file was written. The four
typed terminals, quoted from their `run-status.json`:

| # | root | cycle | `message` |
|---|---|---|---|
| D1 | `live-reach-rich-run/failed-epoch1-run-40e713b3…` | 2 | `V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY at /workflow/insufficient_capability_by_route_seat: route seat has terminally exhausted its smallest authorized contract` |
| D2 | `live-reach-rich-run/run` | 2 | `ROUTE_LEASE_MISMATCH role='conjecturer' seat=0 field=max_tokens expected=32768 actual=20480` |
| D3 | `change-epoch3-second-lineage/failed-attempt2-run-bb045538…` | 0 | `token budget denied transactional work sha256:32af1d16…` |
| D4 | `change-epoch3-second-lineage/failed-attempt3-run-bb045538…` | 2 | `transactional reservation bound differs from rendered request` |

All four carry `state: failed`, `stop_reason: operational_failure`,
`phase: stop`. All four died at cycle 0 or 2 — before cycle 3, as R1 states.

### R2 — the instrument's purpose

> Instrument tranche: an offline cycle soak — drive the full managed run
> path to cycle 8+ against the deterministic stub provider, with THIS
> configuration's shape, so seam defects die on the bench instead of on the
> meter.

### R3 (S1) — the soak

> a script (scripts/ alongside the wheel smokes) that compiles a run from a
> REAL config shape — parameterized, with the epoch-3 config as the first
> case — and drives the managed path (TextRunApplicationService, the one run
> path) against the existing deterministic stub provider for N cycles
> (default 8, the committed carrier threshold), asserting a typed terminal
> or typed completion, verify_root clean, and NO operational_failure. Reuse
> the operational smoke's stub machinery — do not mint a second stub.

### R4 (S2) — the regression seat

> the four recorded death shapes become soak assertions — each formerly-fatal
> seam is exercised (seat contracts with repairs, lease-checked routes with
> tuning, reservation/dispatch bounds, budget authorization) so a regression
> on any of them fails the soak by NAME.

### R5 (S3) — gate placement

> per the smoke precedent: NO pytest gate runs the soak (it is minutes-long);
> it joins the wheel smokes as a pre-launch instrument, and
> docs/AUDIT_BASELINES.md gains its entry (expected: exit 0) in the same
> commit. dr-drive-harness's preflight section gains one line: no live launch
> without a green soak on the launch config. CLAUDE.md's live-run section
> gains the same sentence — same commit.

### R6 (S4) — honesty

> if the soak CANNOT reproduce a recorded death shape offline (some seams may
> need real transport), row it as not-coverable with the reason — a soak that
> silently skips a seam reads as coverage it does not have.

### R7 — known current state / the parallel window

> baselines as of main 5d9b995ce; sweep retired; a parallel window is FIXING
> the reservation-bound seam in llm/adapter.py — you DRIVE that code, you do
> not modify it; expect S2's bound case to fail until their fix merges, and
> mark it expected-red-until-<their-branch> rather than skipping.

### R8 — the stop condition on adapter/transaction code

> If you need to edit adapter/transaction code, STOP and say so.

### R9 — gate discipline

> GATE: ring while iterating; full gate at the boundary; docs_verify full.
> Map moves in the same commits. Commit and push every phase boundary (retry
> 2s/4s/8s/16s).

### R10 — delivery form

> Deliver R-by-R with pasted PROOF, closing with one line: what a launch now
> requires that it did not before, and what the soak caught on its first full
> run.

### R11 — setup (executed; recorded for reproducibility)

> pip install -e . --break-system-packages -q; pip install pytest pytest-xdist
> jsonschema --break-system-packages -q. Use `python -m pytest`, never bare
> pytest. Read CLAUDE.md in full; load dr-drive-harness,
> dr-explain-to-operator.

## Recorded deviations from the operator's setup text

Both are facts about the environment, not choices, and neither changes any
requirement above.

- **D-a — branch.** The operator's SETUP names
  `claude/cycle-soak-instrument-m2xf9d`; this window's standing directive
  designates `claude/cycle-soak-instrumentation-8e0vp7`. Put to the operator
  and answered: `claude/cycle-soak-instrumentation-8e0vp7`. Base is
  `origin/main` = `5d9b995ce`, exactly as SETUP requires.
- **D-b — repository.** The window opened on `AHepi/Poietics`, where no
  anchor in this request exists on any ref (`5d9b995ce` is not a valid
  object there; `TextRunApplicationService`, `docs/AUDIT_BASELINES.md`, the
  `dr-*` skills and both cited experiment roots are all absent). Put to the
  operator and answered: `AHepi/DeepReason`, whose `main` head IS
  `5d9b995ce9021855d6470d2f3d43456b813885e5`. Work proceeds there.
