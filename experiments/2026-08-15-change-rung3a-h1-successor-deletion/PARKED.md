# Parked — Rung 3a

## P1 — is `easy.py`'s repair-successor a SECOND H1 site?

**What.** H1 deleted the refuted⇒successor branch from `scan_spawns`. A census
run while executing this rung found a second, live producer of the same trigger
that H1 was never stated about:

    src/deepreason/easy.py::seed_component
        {"trigger": "successor", "from": [repair_of]}
    src/deepreason/workflows/website.py:1643, 1717   the two live call sites

It is arguably the same shape — integration criticism implicates a component,
and a problem is minted from that implication. It is also arguably not: H1 was
stated about the reasoning loop's failed verdict, the staged website workflow is
a deterministic pipeline rather than a frontier, and its repair problems are
bounded by the manifest's component list rather than growing without limit.

**Why it is parked and not decided.** The operator said this rung ships ALONE,
and answering either way changes `easy.py` and `workflows/website.py`. Deciding
it here would have broken the one constraint the rung exists under. It is also
genuinely the operator's: H1 is a pre-decided doctrine item, and its reach is a
doctrine question, not an implementation detail.

**It is why the enum member survives.** Not compatibility — the 2026-08-14 law
retired that — but liveness. Reading `SpawnTrigger.SUCCESSOR`'s survival as "H1
was not applied" is the specific misreading `DR-SUB-rules` now warns against.

### Ready-to-send prompt

```
Decide whether H1 reaches the staged website pipeline.

H1 deleted the refuted-verdict successor trigger from the reasoning loop
(experiments/2026-08-15-change-rung3a-h1-successor-deletion/). A second
producer of trigger: "successor" survives, in a different subsystem:
easy.py::seed_component mints a component REPAIR problem when integration
criticism implicates a component, called from workflows/website.py:1643
and :1717.

Same shape (a problem minted from a failure) or not (a bounded pipeline
step over a fixed manifest, not a growing frontier)?

Road A -- H1 reaches it: re-found repair problems on a non-failure trigger,
or remove the auto-mint and let the pipeline re-pose explicitly. ~150-250
lines across easy.py, workflows/website.py, tests/test_chunked.py,
tests/test_website_state_machine.py. THEN SpawnTrigger.SUCCESSOR can be
deleted and the v2 trigger vocabulary matches the behaviour.

Road B -- H1 stops at the reasoning loop: record the boundary in
docs/map/SUB-rules.md and CON-problem-layer-lifecycle, keep the enum
member permanently, and state in one sentence why a pipeline repair is
not a conjecture's failure. ~30 lines, documentation only.

Recommendation: B, with the boundary written down. H1's recorded purpose
is that a failed conjecture must not grow the frontier without anyone
posing the question; a component repair problem is posed by the pipeline
against a fixed manifest and cannot cascade. But this is doctrine, and
doctrine is yours.
```
