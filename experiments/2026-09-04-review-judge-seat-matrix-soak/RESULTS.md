# RESULTS — review of the judge-seat-matrix soak

Dated, honest-ledger segments. "Accepted does not mean true."

---

## 2026-09-04 — the branch under review does not exist; the half of the question that survived produced a worse answer than expected

**What the record shows.**

The window asked whether `soak_builder.py` on
`codex/live-full-judge-seat-matrix-20260901` catches the eight deaths the
record has seen, and whether its 12 gate failures are its own. Neither can be
answered: the branch is absent from `ahepi/deepreason` as a branch, as any of
the 16 pull-request refs, and as any commit in this clone. `git ls-remote`,
`mcp__github__list_branches` and `mcp__github__list_pull_requests(state=all)`
all agree. The verdict is therefore **DISCARD**, on grounds of absence rather
than on grounds of quality — and the candidate's column in the death table is
left empty rather than guessed at.

**The half that survived, and what it showed.** The eight deaths were judged
against `scripts/cycle_soak.py` on main, which was the comparison arm and is
now the whole table. Of eight recorded deaths, the committed instrument
demonstrably caught **one** (D4, the reservation-bound seam, reproduced offline
on its first full run in 2026-08-23). It caught a second (P-C2b) and has since
lost the ability to: `--case split-legs` now dies at compile. Three (D1–D3)
are asserted but were never demonstrated, exactly as the 2026-08-23 tranche
itself recorded. Three (P-S1 M-1, P-A1, P-A2 epoch 4) are structurally outside
its reach.

**The sharpest single measurement.**
`python -u scripts/cycle_soak.py --case pa1 --cycles 8` **exits 0**, every
assertion and every seam green. That is the committed config shape of run
`4565139800f5ca02`, which died at `V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY`. The
soak carries the death's configuration and none of its mechanism, because the
stub cannot drop a connection. A soak that goes green on a dead run's own
config is the failure mode the 2026-08-23 tranche built the instrument to
remove, recurring one layer up.

**An unlooked-for finding.** Five of the soak's nine committed cases — `pr1`,
`pc1`, `pc2`, `pc2b`, `split-legs` — no longer compile on main
(`V6_SIMULATION_TOOLCHAIN_REQUIRED`). Those five are every case that arms
`llm/split.py`'s two-leg protocol, so no committed instrument now exercises a
split seat call at all. `docs/AUDIT_BASELINES.md:210` baselines only
`--case epoch3`, a survivor, which is why the rot was invisible.

**Baselines, measured on the untouched base.** Full gate on `643dd8ea1`:
**4961 passed, 6 skipped, 0 failed** (22:05). `docs_verify: 6 failed`, which is
exactly the documented shallow-clone baseline at `docs/AUDIT_BASELINES.md:43`
("5 OR 6 failed"); this clone is shallow at 357 commits. Three of the six
failures are themselves caused by missing history — two unknown revisions and
one `git show` against a **deleted branch**, the same failure mode that removed
the branch under review.

**One trap paid in this window.** The first gate run died with
`ModuleNotFoundError: No module named 'deepreason'` because the `pytest`
console script at `/root/.local/bin/pytest` resolves to a different interpreter
than `python`. `python -m pytest` is the fix. This is the interpreter/pip
pairing `docs/AUDIT_BASELINES.md:49-56` prices at 502 spurious failures, and it
is a plausible contributor to the codex container's own 12.

**Residue — what remains unproven.**

- The candidate was never read, run or judged. Nothing in this tranche is
  evidence about `soak_builder.py`, and its table column says so.
- The 12 gate failures stay unadjudicated. A green base in *this* container
  cannot be transported into one that no longer exists.
- The nine live judge-pair rows are unreachable from this repository. Whether
  they survive in a codex-side artifact was not established — only that they
  cannot be cherry-picked from here.
- The 315-row cost in VERDICT.md is an estimate built from P-A1's measured call
  latency, not from the census driver's own numbers, which are on the missing
  branch. Its load-bearing assumption (2 provider calls per row) is a floor.
- Deaths 1–3 are still asserted-only. This window confirmed the 2026-08-23
  residue rather than reducing it.
- Death 8's fix is on main and was verified here indirectly — a soak-green root
  reaches `RUN_CREDENTIAL_MISSING` rather than a lifecycle refusal. The soak
  still asserts nothing about continuability, so a regression would pass.

**What this tranche changed.** Nothing outside its own directory. No merge, no
cherry-pick, no push to main.
