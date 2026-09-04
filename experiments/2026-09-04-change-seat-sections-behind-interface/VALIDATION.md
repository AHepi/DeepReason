# VALIDATION — the nine caller-computed sections behind the interface

Phase: `dr-validate-change`. Date: 2026-09-04.
Base: `main` at `0f6bf2c854`. Branch: `claude/seat-sections-interface-d4vjqe`.

## Verdict: **PASS**

Every acceptance check in `SPEC.md` §7 was run and every one passed. Two things
did not go as the plan said and both are disposed below rather than smoothed
over: the source layer could not live where the plan put it, and the first
mutation plant did not turn its check red.

---

## §1 The instruments

| instrument | result |
|---|---|
| `python -m pytest tests/ -q -n 4` (alone, at the boundary) | **4982 passed, 6 skipped, 0 failed** in 17:59 |
| both goldens | 15 passed; `git diff --stat tests/fixtures/` empty — no fixture touched |
| `tools/blast_radius.py` over the ACTUAL diff, `--against 0f6bf2c854` | `"frozen_surface_verdict": "CLEAR"`, no contacts, no adjacent contacts, no reachability drift |
| `python tools/docs_verify.py` (full, alone) | **6 failed, every one a `REQUEST.md` C4 row** |
| `--links` | 0 dangling references, 79 documents |
| `--audit` | 1 finding: `SEAM-llm-x-rules.md:54`, the same pre-existing unparseable check C4 names. No new unfailable check. |
| `tools/diff_budget.py 0f6bf2c854 --ceiling 1600 --paths src` | 1452, **WITHIN** |

**One earlier gate run showed 2 failures and is reported rather than buried.**
Run concurrently with `docs_verify`, the suite failed
`tests/test_mcp_run.py::test_start_poll_result_and_progress_notifications` and
`::test_typed_v6_stop_can_continue_and_append`, both on a two-second thread
join. `docs/AUDIT_BASELINES.md:22-23` names `tests/test_mcp_run.py` as
known-flaky under `-n 4` and green in serial re-run; both passed serially
(`7 passed in 13.88s`) and both passed in the boundary gate above, which was run
alone. Recorded because "flake" is not a root cause unless the record already
says so, and here it does.

**The same contention produced the one extra `docs_verify` row.** A run
concurrent with the gate reported 7 failed, the seventh being
`CON-run-identity.md:313` TIMEOUT after 300s — a check that runs a pytest file.
Run alone, `docs_verify` reports exactly the six C4 rows.

## §2 Acceptance checks, one per requirement

| # | requirement | result |
|---|---|---|
| A1 | R6 — byte-identical defaults | **PASS**. Both goldens pass; no fixture edited, and the fixture diff is empty. |
| A2 | R1, R10 — the bundle feeds every slot | **PASS**. `test_the_bundle_supplies_every_caller_computed_slot` asserts the nine and the four by set equality, so a slot left behind fails it. |
| A3 | R2, R8 — the admission code computes no section | **PASS**, in two halves. `rules/conj.py` imports and constructs no pack-section type (it imported `AllocatedPack` and re-wrapped four times before), and calls none of the nine content renderers. Four mutation plants, each turning one half red. |
| A4 | R5 — never appends | **PASS**. Measured over every registered source: next event sequence, `log.jsonl` bytes and the status map unchanged; a planted-write source turns the same measurement red. Asserted statically as well, because the frozen-evidence source needs a full v6 run to resolve and the dynamic drive cannot reach it — eight mutation plants, one per record-writing verb. |
| A5 | R5 — one declared write | **PASS**. Exactly one source declares `writes_blobs`, named in the assertion; every other source leaves the blob store unchanged. |
| A6 | R7 — shape buys nothing | **PASS** and extended: the check now covers the source layer's own types and names. Mutation-proven (§3). |
| A7 | R3 — selection is configuration | **PASS**. No `Config` field and no manifest field names a source or a bundle; the environment selects one without a restart; a malformed assignment is a typed refusal, not a silent default. |
| A8 | R14 — the gate | **PASS**. 0 failed, nothing weakened. Three location-pinning tests were re-pointed at the new address, each still failing on the regression it was written for (`STEP_LOG.md` has the table). |
| A9 | R14 — the map moved with the code | **PASS**. Thirteen map documents changed in the same commits as the code. |
| A10 | R12 — blast radius over the actual diff | **PASS**. `CLEAR`. |

## §3 The mutation proofs (R9), pasted

**R8's check, planted with `AllocatedPack(pack)` and with each of three content
renderers** — `tests/test_seat_section_sources.py::
test_the_no_section_checks_go_red_on_a_planted_call`, four parameterisations,
all passing (each asserts the check raises).

**R7's check, planted with a generation-side name on a rules authority path:**

    E       AssertionError: ['src/deepreason/rules/act.py::browser_evidence: bundle_id']
    FAILED tests/test_seat_section_architecture.py::test_limb3_shape_buys_nothing_on_the_rules_authority_paths
    1 failed, 7 passed in 0.98s

**The plant that did NOT go red, and why that is not a hole.** The first attempt
put the same name inside `rules/conj.py::conj` and the test stayed green.
`conj` DISPATCHES; the check is scoped to functions that decide standing,
deliberately, because a dispatch site legitimately names its own seat. The plant
was wrong, not the check. Recorded because the first reading of a green mutation
is "the check is broken".

## §4 The two departures from SPEC.md

**1. The source layer could not live where SPEC §2 put it.** The plan said
`src/deepreason/llm/seat_sources.py`, beside the plugins it feeds. `DR-SUB-llm`'s
own check went red on the first `docs_verify` run: `llm/` may not import the
harness, the scheduler, the rules, the adjudicator or the amendment machinery,
so that a transport bug cannot become an adjudication bug. A source's whole job
is to read the record. The layer moved to its own package,
`deepreason.seat_sources`, which imports `llm/` rather than being imported by
it. Nothing else in the design changed. The trap is written into the seam
document, because the pull to put it beside the plugins is strong and the arrow
it would invert is not visible from the code.

**2. `SPEC.md` §5 said the tranche moves thirteen sources where R10's scope
names twelve.** The fourth post-allocation re-wrap is a SUBSTITUTION rather than
an append, and R10's "three appended after allocation" does not name it. It was
moved anyway: R2's sentence is false while a section's final bytes are computed
in `rules/`, and leaving one of the four behind would have split the
`AllocatedPack` rule across two modules — the exact shape its own trap warns
about. Cost: one source. Disclosed at spec time, not discovered here.

## §5 What this tranche did NOT achieve, stated plainly

R2's sentence — "no section a seat is shown is COMPUTED inside `rules/`" — is
now true for the CONJECTURER and false for the CRITIC. `rules/crit.py` still
computes four contexts. The reason is not fatigue: its two call sites supply
different subsets on purpose, so a single bundle would change the bytes of one
of them, and the selector that would fix it is a protocol addition made for one
caller. Parked as `PARKED.md` P1 with the price and a ready-to-send prompt. The
seam document says the same thing where a reader will meet it.
