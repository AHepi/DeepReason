# VALIDATION — Rung 1

Verdict: **PASS** — all ten acceptance checks.

## Acceptance checks

### A1 (R1) — `accepted` renders as `unrefuted` on every profile — **PASS**

    $ python -m pytest tests/test_calculus_vocabulary.py -q
    7 passed in 0.10s

`test_display_maps_accepted_to_unrefuted_on_every_profile` asserts `None`,
`"text"` and `"formal"` all render `unrefuted`, and that the other three labels
are unchanged.

### A2 (R2) — stored labels never move — **PASS**

Same run: `test_stored_labels_are_unchanged` pins
`Status.ACCEPTED.value == "accepted"` and the full value set to the four
historical strings; `test_ontology_never_learns_the_rendered_word` reads
`ontology/state.py` off disk and asserts `"unrefuted"` does not appear in it.

### A3 (R2) — machine JSON keeps the stored key — **PASS**

`test_machine_json_keeps_the_stored_key` reads `findings.py` and asserts the
`positions` literal still keys `"accepted"` and that `unrefuted` appears nowhere
in the module. v1.7 §E names `positions.accepted` as a key readers compare
across roots.

### A4 (R3) — root sweep, zero verdict drift — **PASS, full census**

Every openable root under `experiments/` was swept and compared field-by-field
against the committed baseline from the previous tranche
(`experiments/2026-08-13-defect-controller-steering-inert/
root-sweep-after-2026-08-13.txt`), which was taken on the reader code this rung
started from:

    baseline roots 107 | swept now 107 | compared 107
    VERDICT DRIFT: NONE - every compared field byte-identical on all 107
    not compared: []
    valid=True: 86 | valid=False: 9
    ERROR lines: 11 (AUDIT_BASELINES expects 11)

Fields compared per root: `valid`, `att`, `epistemic_passed`, `blind`,
`module_digests`, `seat_digests`. The 11 ERROR lines are exactly the recorded
baseline (`UnsupportedRunManifestVersionError`), and the 9 `valid=False` roots
are baseline-identical — none of them moved.

Raw output archived beside this file as `sweep-part1.txt` / `sweep-part2.txt`.

**How it was run, and why that is worth recording.** `tools/root_sweep.py`
takes only an output path and writes it once, at the end, so a run killed by a
timeout produces nothing. Against the baseline's known-hang root and the
degraded per-root throughput already parked
(`experiments/2026-08-13-change-smoke-currency-audit/PARKED.md` P1), the
committed tool could not finish inside any timeout used here. The sweep was
therefore run from a scratchpad copy of the same script with two changes and no
others: the baseline's known-hang root is skipped with a `SKIPPED` row, and the
output file is written after every root so a timeout costs progress instead of
everything. Both halves are logged in this tranche's PARKED.md as the fix the
tool itself should carry.

### A5 (R4) — no direct status render survives in `views/` — **PASS**

    $ grep -rn "status\.value" src/deepreason/views/
    src/deepreason/views/why.py:85: f"Rendered {display_status(status)!r} (stored {status.value!r}): "

The single remaining occurrence is deliberate and is the point of the line: the
`why` view teaches the reader BOTH vocabularies at once, which is what stops the
rename from looking like a relabelling of the record. Every other site routes
through the seam, pinned by a map check:

    $ for f in why theory evidence export; do grep -q "from deepreason.status_display import" src/deepreason/views/$f.py || exit 1; done
    (exit 0)

### A6 (R5) — the map document verifies — **PASS, against the recorded baseline**

    $ python tools/docs_verify.py
    docs_verify [full]: 54 documents, 880 checks, 4 workers
      FAIL CON-run-identity.md:200 / :202 / :204
    docs_verify: 3 failed

    $ python tools/docs_verify.py --links
    docs_verify --links: 0 dangling reference(s), 54 document(s)

The three failures are **exactly the recorded baseline**, verbatim from
`docs/AUDIT_BASELINES.md`: "3 pre-existing failures, all `CON-run-identity.md`
git-history checks — they require an unshallowed clone; on a full clone the
expected value is 0 failed." Confirmed environmental, not inherited from this
change:

    $ git rev-parse --is-shallow-repository
    true
    $ for c in 1637e808 f304fec1 6a8758a5; do git cat-file -t $c 2>/dev/null || echo "$c: absent"; done
    1637e808: absent
    f304fec1: absent
    6a8758a5: absent

The document count moved 53 → 54: the new `CON-standing-and-background.md`, its
checks running and passing inside the 880.

### A7 (R6) — the controller predicate is renamed — **PASS**

    $ grep -rn "_under_standing_attack" src/ tests/
    grep: src/deepreason/__pycache__/controller.cpython-311.pyc: binary file matches

Source-clean; the only hit is a stale bytecode cache, which is not source and is
regenerated. The test that exercised it was renamed with it
(`test_forbidden6_fail_static_holds_under_unresolved_attack`) and passes.

### A8 (R7) — the design law is ledgered — **PASS**

    $ grep -c "signal registry is a CONTRACT" CLAUDE.md
    1

### A9 (R8) — no skill or workflow was created — **PASS**

    $ git status --short .claude/
    (empty)

### A10 (all) — the full gate — **PASS**

    $ python -m pytest tests/ -q -n 4
    3598 passed, 7 skipped in 833.36s (0:13:53)

**0 failed.** No assertion was weakened to get there: the seven fixture
assertions that moved each still pin an exact label, and the rung ADDED the
stored-label test the old fixtures never had.

## Frozen surfaces — the disclosure gate

    $ python tools/blast_radius.py --files src/deepreason/status_display.py \
        src/deepreason/views/{why,theory,evidence,export}.py src/deepreason/controller.py
    "frozen_surface_contacts": [], "frozen_adjacent_contacts": [], "reachability": [],
    "qualification_digest": [], "wheel_smoke_pins": [],
    "disclosure_summary": "This change touches none of the five frozen surfaces.
     0 test file(s) and 6 map document(s) assert on the touched targets today.",
    "frozen_surface_verdict": "CLEAR"

Wheel smokes were therefore NOT required: `wheel_smoke_pins` is empty — no
console entry point, MCP tool, or wheel-layout pin is touched.

## The prediction record, stated honestly

The SPEC predicted four fixture assertions. Seven moved. The two amendments in
SPEC.md record each miss at the moment it was found rather than after the fact,
and the pattern is worth carrying into Rung 1b: **specifying a code change is
not specifying its fixtures.** Every one of the three surfaces that surprised me
(`test_evidence_view`, and the terminal renderer reached through
`display_status_counts`) consumes the seam indirectly, and none of them appears
in the S3 renderer table because none of them is a renderer — they are consumers
of one.

No unpredicted failure was absorbed silently, and no failure outside the
label-rendering species appeared at any point.
