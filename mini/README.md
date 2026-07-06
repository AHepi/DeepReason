# MiniReason

The measured 20% of DeepReason in ~880 code lines. Every component here earned
its keep in the parent's experiment record; everything else was cut on
measurement, not taste. The construction plan with per-inclusion citations
is [`../docs/MINI_PLAN.md`](../docs/MINI_PLAN.md); the evidence lives in
`../experiments/results/INDEX_2026-07-05.md` and `../docs/BASIN_REPORT.md`.

## What it keeps (and why)

| module | keeps | measurement |
|---|---|---|
| `log.py` | append-only events, content-addressed blobs/objects, byte-replay | the accounting layer caught 3 real spend bugs in the parent |
| `call.py` | schema repair loop, spend on EVERY exit path, hard meter | retry-exhausted spend was 8.4% of a live run; mid-retry death leaked 833 tokens |
| `gate.py` | refuted-relapse gate + gate-rate orbit detector | perfect healthy/orbiting separation on all 15 parent roots; orbiting burned 4.3x tokens |
| `checks.py` | program checks compiled from each candidate's own forbidden cases | the only criticism that measured cost-positive at low base error (zero judge tokens) |
| `rotate.py` | stance rotation (decay 5) + problem turnover (K=8) | fast rotation best on novelty 0.973 AND separation 0.690; turnover was the only novelty-RAISING force (1.12) |
| `judge.py` | criterion-level forced choice, both orders, verbosity penalty, degraded-control gate | control gates +0.478/+0.909/+0.841; naive pairwise judging discarded 8/9 votes to position bias |
| `loop.py` | propose -> gate -> check -> log -> rotate | never loops a dry problem (the 4.3x burn) |

What it deliberately drops (all A/B-refuted or placebo at strong-generator
regimes): the 2-judge trial protocol, paraphrase screens, appellate
machinery, embedding-based convergence detection, the complement directive,
Dung adjudication with reinstatement.

## Run

```python
from minireason.call import HttpEndpoint
from minireason.loop import run

summary = run(
    [("pi-1", "why did X happen?")],
    HttpEndpoint("https://api.deepseek.com", "deepseek-v4-flash", api_key=KEY),
    budget=30_000,
    root="runs/my-run",
)
```

The run summary is a convenience; the log at `root` is the real output.
`minireason.log.replay(root)` rebuilds state from it — twice, byte-equal.

Evaluation is offline, never in the loop: `judge.score_run` scores committed
pairs behind the degraded-control validity gate, and `judge.certify_seat`
re-runs the planted-flaw battery — re-certify seats on every new provider
before trusting a score.

Live smoke (M2, ~30k tokens): `DEEPSEEK_API_KEY=... python mini/scripts/smoke.py`.

## Graduation (mini -> full)

The log is the contract: a MiniReason root is a valid DeepReason root.

```python
from deepreason.harness import Harness
h = Harness("runs/my-run")          # no data conversion
from deepreason.invariants import verify_root
verify_root("runs/my-run")           # ["violations"] == []
```

`mini/tests/test_graduation.py` holds this: the parent replays a mini log
without violations, agrees on every status (mini refuted-by-check ==
parent grounded-semantics refuted; mini survivors == parent accepted), and
the parent's own capture detection reads the mini's `gate:` measures.

Graduate when base error is measurably high (then trial filtering has
something to filter), when reinstatement semantics start to matter, or
when policy demands multi-family judge ensembles.

## Verification

`python -m pytest mini/tests` — no network, no keys. The M3 fixture rescores
the parent's committed instrument reports byte-for-byte; M0/M4 fixtures
generate parent roots in-test and read them with the subset reader (the
plan's committed-root fixtures live under the gitignored `runs/`, so they
are regenerated rather than checked in).

Line budget: the plan said ~800; `minireason/` lands at ~880 code lines
(1,245 with docstrings). The overage
is G6 — the parent-compatible object store and refutation records
(`Session.refute`) that make graduation a no-op — plus the HTTP endpoint.
Both cite their keep: G6 is a plan goal, and the endpoint's retry/usage
normalization each closed a measured accounting hole.
