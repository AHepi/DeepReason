# Validation for: T6 — regression, goldens, the record (S10)
Sub-tranche T6 of the mini isolation programme. Phase: `dr-validate-change`.
Base: `14cc5da495` (main, carrying T2) for the programme's `src/` reach;
`c13056c0a` (T5's delivery head) for this sub-tranche. Branch:
`claude/mini-isolation-t3-t5-7tsc6d`. Run 2026-09-06 under REQUEST.md
Amendment 2 ("Do T6").

T6 changes no code. It records, once and at the programme's own boundary,
the five instruments SPEC S10 names — every one of which the three
deliveries before it already ran at their own boundaries.

## Acceptance checks

**S10.1** — the documented gate, idle box, nothing else running.

    $ python -m pytest tests/ -q -n 4
    5084 passed, 6 skipped in 1359.52s (0:22:39)     -> 0 failed

: **PASS**. The same 5084 at T2, T3, T4, T5 and here.

**S10.2** — mini's own suite, explicitly.

    $ python -m pytest mini/tests/ -q
    164 passed, 1 skipped in 14.13s                   -> 0 failed
    $ python -m pytest mini/tests/ --collect-only -q | tail -1
    165 tests collected

: **PASS**. 95 when SPEC.md measured it; the documented gate still collects
none of them (PARKED P1 stands).

**S10.3** — the two legacy goldens.

    $ python -m pytest tests/test_conj_pack_legacy_golden.py tests/test_crit_pack_legacy_golden.py -q
    15 passed in 0.37s

: **PASS** — C4 holds at the programme's boundary.

**S10.4** — the map.

    $ python tools/docs_verify.py          (FULL, at T5 step 44, head 2b6440d28)
    docs_verify [full]: 82 documents, 1417 checks
    docs_verify: 6 failed -- the six known rows
    $ git diff --stat 2b6440d28..HEAD -- docs/map src mini tools scripts pyproject.toml
     2 files changed, 2 insertions(+), 2 deletions(-)
       (the two Verified-at stamps advanced at step 44, nothing else)
    $ python tools/docs_verify.py --fast   -> 6 failed, the same six
    $ python tools/docs_verify.py --audit  -> 1 finding, the known SEAM-llm-x-rules.md:54
    $ python tools/docs_verify.py --links  -> 0 dangling, 82 documents
    $ python tools/docs_verify.py --stale  -> 22, none of them this programme's

: **PASS**. The full run T5 recorded covers this exact map, source and
engine tree: since it, only two stamp lines moved. `--audit` reports 0
findings this programme caused; the one it reports is the window's known
row.

**S10.5** — the record: a mini isolation run verifies and replays.

    flow            : mini.flow.isolation.v1     (3 cycles, vs_k=2, the stub)
    calls           : 15   (3 conjecture + 6 criticism + 6 commitment)
    records by kind : {'mini.commitment-proposal.v1': 6, 'mini.criticism.v1': 6}
    problems        : {'pi-0': 6}  refuted: 0
    meter_equals_log: True
    verify_root violations: 0 []
    replay(root).digest() == Session(root).state.digest(): True
       28844463d7cb14d2cc0b2cc608ab54c5239674dfdd6bcae86aca5b98a982ee89
       28844463d7cb14d2cc0b2cc608ab54c5239674dfdd6bcae86aca5b98a982ee89

: **PASS**. Within-version integrity, the thing the 2026-08-14 law keeps:
the record stays typed, append-only and replayable by the code that wrote it.

## Full gate

Pasted under S10.1: **5084 passed, 6 skipped, 0 failed** : PASS.

## Record-behavior preservation

T6 changes no reader, writer or validator; nothing to preserve beyond what
S10.5 shows. The programme's own reach into `src/` at its boundary:

    $ git diff --stat 14cc5da495..HEAD -- src/
     src/deepreason/llm/packs.py | 29 +++++++++++++++++++++++++++++
     1 file changed, 29 insertions(+)

One file, the two public entries, each one call to its private counterpart.

## Frozen-surface diff

    $ git diff --stat d800b622b..HEAD -- \
        src/deepreason/capabilities/state.py src/deepreason/harness.py \
        src/deepreason/invariants.py src/deepreason/run_manifest.py \
        src/deepreason/qualification.py src/deepreason/verification/ \
        src/deepreason/llm/firewall.py
    (no output)

: **PASS** — and the same command over `14cc5da495..HEAD` is empty too: no
frozen surface moved at any point in this window.

## Packaging surface

Both smokes RUN, because S10 owes them and no gate runs them:

    $ python scripts/wheel_smoke.py
    wheel smoke passed: isolated V6-only contents, clean imports, exact entry
    points, module parity, MCP registration, and exact MCP schemas
    $ python -u scripts/wheel_operational_smoke.py
    wheel operational smoke passed: installed setup, explicit qualification
    (80 qualification calls; 406 total calls), readiness, question-only
    reasoning, replay-verified terminal retrieval, cache reuse, opaque MCP
    restart, budget ceiling, and pre-V6 fail-closed admission

: **PASS**. No pin moved and none was updated: the smokes pin console entry
points, the MCP tool set and its schema sha, and the wheel layout; this
window changed none of them.

## Map

    docs_verify (full, T5 step 44):  6 failed  : PASS (the six known rows)
    docs_verify --audit:             1 finding : PASS (the known one)
    docs_verify --links:             0 dangling, 82 documents : PASS
    docs_verify --coverage (T5):     2 findings, both pre-existing : PASS
    docs_verify --stale:             22, none of them this programme's
    new checks added by T6: none — T6 changed no behaviour and no document,
      so it owes no check; the programme's twenty new checks (T3: 11, T4: 5,
      T5: 4) are listed in their deliveries.
    record observables added vs sweep probes: none added by T6.

## Requirement sweep

T6 is the regression boundary; every R's disposition is T5/VALIDATION.md's,
re-confirmed by the instruments above: R1–R14 and R-stored done or honoured,
R-again and R-history deferred in the operator's own words. R15 (Amendment
2, "Do T6"): **done** — steps 46–51 executed in this window; T7 stays with
the last window, as the amendment's own scope states.

## Assumptions carried

None new. A1–A9 as T5/VALIDATION.md carries them.

## Budget

T6 owes no diff: no file under `mini/minireason/` or `src/` changed.
SPEC's 120 for S10 was for the recording; the record is the checklist's own
pastes and this file.

## Verdict: PASS
