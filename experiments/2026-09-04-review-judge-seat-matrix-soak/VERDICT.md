# VERDICT — the judge-seat-matrix soak, judged against the deaths the record has seen

Tranche: `experiments/2026-09-04-review-judge-seat-matrix-soak/`
Kind: review, read-only. Nothing merged, nothing cherry-picked, no push to main.
Base: `643dd8ea1` (main, after `0f6bf2c85` as the window required).
Branch: `claude/judge-seat-matrix-soak-review-fgz7ud`.
Container: shallow clone, 357 commits, 4 CPUs.

Map preflight: `DR-SUB-scripts` (the soak instrument), `DR-CON-run-identity`,
`DR-INV-frozen-surfaces`. No frozen surface is touched — this window writes
one directory of its own and nothing else.

---

## VERDICT

**DISCARD — the branch does not exist, and the review question cannot be
answered on any artifact this repository holds.**

This is not a judgement about the quality of the work on that branch. It is a
statement about what is reachable. `codex/live-full-judge-seat-matrix-20260901`
is absent from `ahepi/deepreason` as a branch, as a pull-request ref, and as
any commit in this clone. So `soak_builder.py` could not be run against a
single one of the eight deaths, the 12 gate failures could not be separated
into environment and branch, and the nine live judge-pair rows could not be
filed because there is nothing to cherry-pick from.

The recommendation the operator can act on is therefore **not** about merging.
It is: **keep `scripts/cycle_soak.py` and repair it**, because measuring it
against the same eight deaths — the half of the task that survived — shows the
committed instrument catches far less than its green exit suggests, and two of
its nine cases-worth of coverage have rotted away since they were written.

### Evidence that the branch is absent

    $ git ls-remote --heads origin | grep -c codex
    0
    $ git fetch origin refs/heads/codex/live-full-judge-seat-matrix-20260901
    fatal: couldn't find remote ref refs/heads/codex/live-full-judge-seat-matrix-20260901

`mcp__github__list_branches(ahepi/deepreason)` returns 11 branches; none is a
`codex/` branch. `mcp__github__list_pull_requests(state=all)` returns PRs 1–16;
none has that head. `git ls-remote origin 'refs/pull/*/head'` returns 16 refs,
matching those PRs exactly. No commit in this clone adds any file under
`experiments/2026-09-01-change-live-full-judge-seat-matrix/`.

One prior `codex/` branch is visible in the PR history — `codex/judge-canary-
compile-gap-20260901`, PR #15, closed, and now also gone from the branch list.
Codex branches in this repository are deleted after their PR closes. The most
probable history is that this branch was deleted the same way, or never pushed.
That is an inference and is marked as one; what is measured is only its absence.

---

## THE DEATH TABLE

A soak is worth exactly the recorded deaths it would have caught. Eight deaths,
two instruments, one table. Every disposition below is a command and its output,
never "would in principle". Raw output for each row is in `proof/`.

| # | Death (run id / record) | `scripts/cycle_soak.py` on main | `soak_builder.py` (candidate) |
|---|---|---|---|
| 1 | **D1 seat-contract** — route-seat capability exhaustion (2026-08-22) | **ASSERTED, not demonstrated.** Declared with fatal object `workflow-route-seat-insufficient-capability-v1`. Default run: `[PART] D1-seat-contract` — "zero repair tasks recorded". Goes `[PASS]` only under `--induce-repairs 2 --induce-repair-kind alternate`, which reaches the repair *ladder* but never drives a seat to *exhaustion*. | **UNJUDGEABLE** — artifact absent |
| 2 | **D2 route-lease** — lease-checked routes with tuning (2026-08-22) | **ASSERTED, not demonstrated.** `[PASS] D2-route-lease`, 63 attempts all carrying a complete lease. Proves the lease is *checked*; no controller tuned `max_tokens` during the run, so the "with tuning" half is untested. | **UNJUDGEABLE** |
| 3 | **D3 budget-auth** — budget authorization (2026-08-22) | **ASSERTED, not demonstrated.** `[PASS] D3-budget-auth`, 63 `workflow-dispatch-authorization-v1` records. The runs set no finite token budget, so the *denial* path never executes — only the authorization that precedes it. | **UNJUDGEABLE** |
| 4 | **D4 reservation-bound** — "transactional reservation bound differs from rendered request" (2026-08-22, live `failed-attempt3-run-bb045538…`) | **CAUGHT (historically, demonstrated).** Reproduced offline on the instrument's first full run, message identical to the live root; live death at cycle 2, soak death at cycle 1 (`experiments/2026-08-23-change-cycle-soak-instrument/RESULTS.md`). Fixed since; now `[PASS]`. **This is the one real catch of the four.** | **UNJUDGEABLE** |
| 5 | **P-S1 M-1** — 512-token extraction leg with `reasoning: "none"` on glm-5.3 (`experiments/2026-09-01-live-all-modules-p-a1/MONITOR_REVIEW.md`, lines 81–96; the P-S1 tranche dir is not in this clone) | **NOT CAUGHT — structurally unreachable.** The death needs a completion cut before its JSON (`natural_stop: false` on 5 of 6 legs). The stub emits exactly one `finish_reason`, hard-coded `"stop"` (`scripts/wheel_operational_smoke.py:1285`, the only occurrence in the file), and derives `usage` from content length, so it can produce neither a truncated leg nor a zero-token call. Worse: the five cases that arm the split protocol at all no longer compile (below). | **UNJUDGEABLE** |
| 6 | **P-A1** — run `4565139800f5ca02`; seat 1 (glm-5.3) exhausts its ladder after a 10-call transport-fault streak while seat 0 (deepseek) stays healthy | **NOT CAUGHT — and this is the sharpest row in the table.** `python -u scripts/cycle_soak.py --case pa1 --cycles 8` — *the death's own config shape, a committed case* — **exits 0**, with A1–A4 all `[PASS]` and every seam green. `grep -i "transport\|RemoteDisconnected" scripts/cycle_soak.py` returns nothing: the instrument has no fault injection, so the 41 `RemoteDisconnected` events that are in the root cause cannot occur. The soak carries the *configuration* of this death and none of its *mechanism*. | **UNJUDGEABLE** |
| 7 | **P-C2b** — split legs replay-invalid (`BLOCKER.md` at `ee0563cf1`, branch `claude/p-c2-rebuild-harness-n9mguu`, also deleted) | **CAUGHT, THEN ROTTED.** It was a genuine catch: `--case split-legs` → exit 1, `[FAIL] A3-verify-root-clean 260 violation(s)`, first violation byte-identical to the P-C2b soak's (`experiments/2026-08-27-defect-split-leg-recording/REPRO.md:34`). **That catch is no longer reproducible on main**: the case now dies at compile — `V6_SIMULATION_TOOLCHAIN_REQUIRED: policy must bind one frozen toolchain`. | **UNJUDGEABLE** |
| 8 | **P-A2 epoch 4** — run killed mid-cycle, not resumable (`experiments/2026-09-03-defect-stopped-run-resumption/`) | **NOT CAUGHT — no assertion exists.** `grep -i "terminal_lifecycle\|continuab\|receipt\|outstanding_work" scripts/cycle_soak.py` returns nothing. The soak's whole assertion set is A1–A6; not one looks at continuability. That tranche used the soak as a *substrate* and supplied the SIGKILL from its own `proof/three_shapes.py`. Before the fix, the soak reported exit 0 on the very root whose `continue` returned `CONTINUE_TYPED_STOP_REQUIRED`. | **UNJUDGEABLE** |

**Score for the committed instrument: one death demonstrably caught (D4), one
caught and since rotted (P-C2b), three asserted but never demonstrated (D1–D3),
three structurally outside its reach (P-S1 M-1, P-A1, P-A2).**

### The commands, in full

    $ python -u scripts/cycle_soak.py --case reach-rich --cycles 8
    [PASS] A1-typed-terminal      state='completed' stop_reason='budget_exhausted'
    [PASS] A2-no-operational-failure   [PASS] A3-verify-root-clean  0 violation(s)
    [PASS] A4-cycles-reached      reached cycle 8 of 8
    [PART] D1-seat-contract   [PASS] D2  [PASS] D3  [PASS] D4      → exit 0

    $ python -u scripts/cycle_soak.py --case pa1 --cycles 8         → exit 0
    [PASS] A1  [PASS] A2  [PASS] A3  [PASS] A4
    [PART] D1  [PASS] D2  [PASS] D3  [PASS] D4

    $ python -u scripts/cycle_soak.py --case reach-rich --cycles 8 \
          --induce-repairs 2 --induce-repair-kind alternate         → exit 0
    [PASS] D1-seat-contract   (all four seams green)

    $ python -u scripts/cycle_soak.py --case split-legs             → exit 1
    pydantic_core.ValidationError: 1 validation error for RunManifest
      Value error, V6_SIMULATION_TOOLCHAIN_REQUIRED: policy must bind one frozen toolchain

Both green results (`reach-rich`, `--induce-repairs`) sit exactly on the
recorded baseline at `docs/AUDIT_BASELINES.md:210-232`, so nothing above is a
regression against that document — which is the point. The instrument is
behaving exactly as baselined, and the baseline still misses five of eight
deaths.

---

## A FINDING THIS WINDOW DID NOT GO LOOKING FOR

**Five of the soak's nine committed cases no longer compile on main.**

    $ for c in epoch3 pr1 pc1 pc2 pc2b split-legs hv-grant reach-rich pa1; do
        python -u scripts/cycle_soak.py --case $c --cycles 1; done

| case | compiles? | note |
|---|---|---|
| `epoch3` | yes | the baselined case |
| `reach-rich` | yes | |
| `hv-grant` | yes | |
| `pa1` | yes | death 6's shape — and it runs green |
| `pr1` | **no** | `V6_SIMULATION_TOOLCHAIN_REQUIRED` |
| `pc1` | **no** | `V6_SIMULATION_TOOLCHAIN_REQUIRED` |
| `pc2` | **no** | `V6_SIMULATION_TOOLCHAIN_REQUIRED` |
| `pc2b` | **no** | `V6_SIMULATION_TOOLCHAIN_REQUIRED` |
| `split-legs` | **no** | `V6_SIMULATION_TOOLCHAIN_REQUIRED` — **the case that caught death 7** |

(The exit-1 every case returns at `--cycles 1` is the documented
by-construction A4 failure — depth 1 is not past the deepest recorded death at
cycle 2 — and is not the signal here. The signal is the compile crash, which
happens before any assertion runs.)

`docs/AUDIT_BASELINES.md` baselines only `--case epoch3`, which is one of the
four survivors, so this rot is invisible to the standing baseline. Every case
that arms `llm/split.py`'s two-leg protocol is in the dead half — which is why
deaths 5 and 7 have no live instrument today. `V6_SIMULATION_TOOLCHAIN_REQUIRED`
is a known recurring shape elsewhere in the map checks
(`experiments/2026-08-30-fix-rotted-map-checks/`), but its presence in the soak's
own case inventory is not recorded anywhere this window could find.

---

## SECOND — the 12 gate failures

**Reproduced on the untouched base in this container: 0.**

    $ python -m pytest tests/ -q -n 4
    4961 passed, 6 skipped in 1325.43s (0:22:05)      → rc 0

    $ python tools/docs_verify.py
    docs_verify: 6 failed

**The count that is the branch's own cannot be determined, because the branch
is gone.** What this window can state:

- Main at `643dd8ea1` is **green in this container** — 0 failed. So the 12 are
  not inherent to the code the branch was based on.
- `docs_verify: 6 failed` is **exactly the documented baseline**:
  `docs/AUDIT_BASELINES.md:43` — "On this container's SHALLOW clone the total
  is 5 OR 6 failed; on a full clone, 2 or 3." This clone is shallow
  (`.git/shallow` present, 357 commits). The branch's reported 7 is one above
  a two-valued baseline, which is within the noise this repo has already
  measured and written down.
- Three of my six docs failures are caused by the shallow clone itself —
  `CON-run-identity.md:213` and `:215` fail on `unknown revision 1637e808` /
  `f304fec1`, and `INV-frozen-surfaces.md:761` fails trying to
  `git show origin/claude/deepreason-p-s1-commitments-wowcib:…`, a **deleted
  branch**. That is the same failure mode that removed the branch under review.

The standing rule — a failure that reproduces on the base **under the same
container** is environment — cannot be applied here, because the codex container
is not this container and cannot be re-entered. Under the rule as written, the
12 are unadjudicable. My reading, stated as a reading and not a measurement: a
codex container that produced 7 docs failures against a 5-or-6 baseline was
almost certainly also producing gate failures of the same environmental kind
(the `xdist`/`jsonschema` gap and the interpreter/pip pairing that
`docs/AUDIT_BASELINES.md:49-56` prices at 502 spurious failures). I hit the
interpreter trap myself in this window: the `pytest` console script resolves to
a different interpreter than `python`, and the first gate run died with
`ModuleNotFoundError: No module named 'deepreason'` until I switched to
`python -m pytest`.

---

## THIRD — filing the nine live judge-pair rows

**They cannot be filed. There is nothing to cherry-pick from.**

The road the window anticipated — "cherry-pick of the results directory alone"
— requires the commits to exist. They do not, in this clone or on the remote.
Typed evidence that exists only in a deleted branch is, for present purposes,
not in the record at all.

**What the operator can do, in order of cost:**

1. **Ask whoever ran the codex window for the container or the branch.** If the
   codex session still has its working tree, `git bundle create judge-matrix.bundle
   codex/live-full-judge-seat-matrix-20260901` and attaching the bundle recovers
   everything — 41 commits, the nine rows, `soak_builder.py`, and the ability to
   answer this window's question properly. This is the only road that recovers
   the *evidence*; everything else re-earns it.
2. **If the branch is truly gone, re-run the nine rows rather than mourn them.**
   Nine rows of a 324-row census is 2.8% of it; at the cost estimated below the
   nine are roughly 20 minutes of provider time. The expensive artifact was
   never the nine rows, it was the census *driver* — and the driver is what the
   deletion actually cost.

**What the 315 pending rows would cost — an estimate, with its assumption named.**
The per-row cost is a property of the census driver, which lived only on the
missing branch, so this is derived from the harness's own measured judge
behaviour and not from the branch's numbers. Treat it as an order of magnitude.

- Anchor: P-A1 (`run/TOKEN_ACCOUNTING.json`) — 71 provider calls, 1,093,086
  tokens, 4.94 h wall clock. glm-5.3 alone took 3.99 h across 25 calls (10 of
  them dead on transport). The remaining 46 calls took ~0.95 h → **~74 s per
  healthy call**. The judge seats in that run (qwen3.5:397b, gpt-oss:120b) had
  **zero** transport faults, so 74 s is the right anchor for judge traffic.
- Floor: a judge-pair row needs at minimum one ruling from each of the two
  seats → 2 calls. 315 rows × 2 = **630 calls**.
- Serial: 630 × 74 s ≈ **13 hours**. At 4-way parallelism ≈ **3.2 hours**.
- Tokens: at P-A1's ~15.4k tokens/call, 630 calls ≈ **9.7 M tokens**.
- Add one qualification battery per distinct judge model. 324 = 18², so the
  roster is plausibly 18 models in all ordered pairs; at ~14 min and ~1160 calls
  per uncached battery that is **~4 h and ~21k calls** more, paid once, and
  cached thereafter by subject digest.

So: **roughly 3–13 hours of wall clock and ~10 M tokens for the census proper,
plus a one-time ~4 h qualification tail.** Under the operator's standing law
that tokens are cheap and the agent is not, the census is affordable; what is
not affordable is rebuilding the driver from nothing, which is the part to ask
for before re-deriving.

---

## RECOMMENDATION

1. **Do not attempt to merge anything.** There is nothing to merge.
2. **Ask for the bundle** (road 1 above) before writing off 41 commits. One
   message to the codex window's owner is cheaper than any other road here.
3. **Repair `scripts/cycle_soak.py`'s five rotted cases** as a small defect
   tranche. This is the highest-value work this window found and it is
   independent of the missing branch: it restores the instrument's only
   demonstrated catch of death 7 and the only cases that arm the split protocol
   at all. A ready-to-send prompt is in `PROMPTS.md`.
4. **Then decide whether the soak should grow three new mechanisms** —
   transport-fault injection, completion truncation, and a continuability
   assertion — since those are precisely the three that deaths 5, 6 and 8 died
   of and that no committed instrument now covers. This is a change tranche,
   not a defect one, and it is the operator's call, not this window's.

---

## RESIDUE — what remains unproven

- **Everything about the candidate.** `soak_builder.py` was never read, never
  run, never judged. Its column in the death table is empty and honest. If the
  bundle is recovered, this window's table is the fixture to re-run it against.
- **The 12 gate failures are unadjudicated**, and will stay so. My base is green
  and my docs count is on baseline, but neither fact can be transported into a
  container I cannot enter.
- **Deaths 1, 2 and 3 remain asserted-only**, exactly as the 2026-08-23 tranche
  recorded them. This window did not improve on that; it confirmed it a year of
  tranches later, which is itself worth knowing.
- **The nine live judge-pair rows are lost unless the bundle exists.** I did not
  verify that they are unrecoverable from a codex-side artifact — only that they
  are unreachable from this repository.
- **The 315-row cost is an estimate, not a measurement.** Its load-bearing
  assumption — 2 calls per row — is a floor; a census that re-runs a full
  reasoning cycle per pair would be an order of magnitude more.
- **Death 8's fix is on main and verified here** (a soak-green root reaches
  `RUN_CREDENTIAL_MISSING`, not a lifecycle refusal), but the soak still asserts
  nothing about continuability, so a regression of it would pass unnoticed.

Accepted does not mean true. This verdict is about what could be reached from
this repository on 2026-09-04, and says so.
