# Validation for: Rung 7 — authority as a declared policy (sub-tranche 7a only)

Scope validated: **7a**, the seam document. 7b (S3) and 7c (S4) are
DEFERRED by the operator (R10) and are validated here only as
*not-executed*, which is their correct state.

Tranche base for every diff below: `2cc3fd50` (rung 6's last commit),
so the fences cover the WHOLE rung-7 tranche, not just 7a.

## Acceptance checks

**S1 (route + original DESIGN-AND-STOP fence)** — partially superseded
by R11, as SPEC.md records. The `src/`/`tests/` half is the live fence
and is checked under S8(b). The "REQUEST.md + SPEC.md only" half was
correct until the operator authorized 7a; the tranche now legitimately
holds CHECKLIST/VALIDATION/DELIVERY/PARKED. : **PASS (as amended)**

**S2 (the frozen-surface forecast is measured, not asserted)** — every
row of SPEC.md's forecast table cites an `M<n>`; the one option that
contacts a frozen surface (Option A, label-time) is rejected on M5, a
pasted measurement on committed bytes, not on judgement. Mechanically
confirmed by 4a2 below. : **PASS**

**S3 (7b — the declared policy object)** : **NOT EXECUTED — deferred by
R10.** Not a failure; its acceptance criteria stand for a future
tranche.

**S4 (7c — the two ungated argumentative mint sites)** : **NOT EXECUTED
— deferred by R10.** Their present state is now DOCUMENTED and checked
by the new seam document (check 8), which is 7a's contribution to it.

**S5 (scope fence: P7 parked, no rung-6 work)**

    $ grep -rn "attempt-validity" experiments/2026-08-04-change-rung7-.../*.md
    REQUEST.md:72   C3, the constraint parking it
    SPEC.md:137     S5, the exclusion
    SPEC.md:139     S5's own accept line
    SPEC.md:199     Out-of-scope bullet

Four hits, all exclusions; none proposes work. No rung-6 execution
occurred (rung 6's directory still holds REQUEST.md + SPEC.md only).
: **PASS**

**S6 (stop after committing and present)** — discharged at the SPEC
gate; this tranche resumed only on the operator's explicit
authorization, quoted verbatim as Amendment 1. : **PASS**

**S7 (precondition: rungs 1-4 delivered)** — DELIVERY.md exists for
rungs 1, 2 (×3), 3 (×2), 4 and 5. : **PASS**

**S8 (execute 7a and nothing else)**

(a) `docs_verify` full / `--audit` / `--links`: see Map below.
: **PASS, delta-based** (see PARKED.md P1)

(b) the 7b/7c fence:

    $ git diff --stat 2cc3fd50..HEAD -- src tests
    (empty)
    $ git status --porcelain src tests
    (empty)

: **PASS**

(c) `adjudication x authority` in no `Seams-undocumented:` header:

    $ grep -rn "Seams-undocumented:.*adjudication x authority" docs/map/
    (no hit)

: **PASS**

(d) program report per R12: delivered in DELIVERY.md and to the
operator. : **PASS**

## Full gate

    $ python -m pytest tests/ -q -n 4
    FAILED tests/test_module_fingerprints.py::test_every_committed_root_reads_as_having_no_module_fingerprints
    FAILED tests/test_module_fingerprints.py::test_the_census_of_committed_roots_is_unchanged
    2 failed, 3336 passed, 7 skipped in 663.27s (0:11:03)

: **PASS for this tranche — both failures proven pre-existing.**

Proof, per this skill's own rule for pre-existing failures (a `git
stash` was impossible — the tree was already clean and committed — so
the stronger form was used): the same two tests fail at the tranche
base `2cc3fd50` in a **clean detached worktree** containing none of
this tranche's work.

    $ git worktree add --detach <wt> 2cc3fd50 && python -m pytest tests/test_module_fingerprints.py -q
    2 failed, 18 passed in 27.25s

Bisected to the first bad commit:

    a4c52c5b (rung 5, roots deferred)     20 passed
    f6d41bff (rung 5 A/B arm A)           2 failed, 18 passed   <- first bad
    1f20a6bd (rung 5 A/B complete)        2 failed, 18 passed

These are NOT the parallel-load flake the handover warns about
(`test_v6_nonconjecture_recovery.py`); that test passed. They are the
same root cause as the two map failures, and the cause is a
mis-specified test rather than a bad commit — full analysis in
PARKED.md P1, which this result upgraded from two red instruments to
four.

This tranche changed **zero** `src/` and `tests/` files, so no failure
here is attributable to it. Recorded, routed to P1, does not block —
exactly the disposition the procedure prescribes.

## Frozen-surface diff (4a2 — the mechanical tripwire)

    $ git diff --stat 2cc3fd50..HEAD -- \
        src/deepreason/capabilities/state.py src/deepreason/harness.py \
        src/deepreason/invariants.py src/deepreason/run_manifest.py \
        src/deepreason/qualification.py
    (empty)

Empty, as SPEC.md's forecast predicted. Stronger than required here:
the whole `src/` tree is untouched by this tranche, so the tripwire
could not have fired. : **PASS**

## Record-behavior preservation

This change touched no reader and no validator — 0 `src/` files — so
strictly n/a. Spot-checked anyway, because the new document's checks
OPEN two committed roots and would be worthless if those roots' derived
state moved:

| root | result |
|---|---|
| `run-f4fa6663…` (engaged) | `att=1`, one `REFUTED` — exactly what the two new checks assert. Also carries **6 pre-existing `foreign-criticism` violations**, `valid=None` |
| `run-6472629d…` (stress-triplet orbit) | `verify_root` 0 violations |

**Correction to my own earlier wording:** I called `run-f4fa6663`
"known-good" while setting up. That is imprecise. It is a root with a
real attack edge and one refuted artifact — which is what these checks
need — and it is NOT replay-clean: 6 `foreign-criticism` violations,
all pre-existing (this tranche changed no `src/` file) and depended on
by nothing. No map check anywhere asserts `verify_root` validity on it
(`grep` → 0). The new checks bind its graph derivation, not its
verdict, so the violations do not weaken them.

## Map

    docs_verify:            51 documents, 815 checks, 2 failed  : PASS (delta)
    docs_verify --audit:    0 finding(s)                        : PASS
    docs_verify --links:    0 dangling reference(s), 51 docs    : PASS
    docs_verify --coverage: 6 seams swept, 16 without a Sweep:
                            header, 0 finding(s)                : PASS
    docs_verify --stale:    23 document(s) worth re-reading     : judged below

**Why `2 failed` is a PASS here, and what would make it a FAIL.** The
baseline at tranche base was ALREADY 2 failed (step 1, PARKED.md P1) —
both root-census checks, both broken by rung 5's post-delivery commits
`f6d41bff`/`1f20a6bd`, neither caused by this tranche. The instrument
that matters is the delta:

    BEFORE: 50 documents, 807 checks, 2 failed
    AFTER:  51 documents, 815 checks, 2 failed
    $ diff <(failing doc:line BEFORE) <(failing doc:line AFTER)
    IDENTICAL

+1 document, +8 checks (exactly the 8 the new document declares), and
the two failures are the same two, unchanged in identity and detail.
A third failure, or either of these changing, would have been a FAIL.
Per the skill's own rule for pre-existing failures: proven to pre-date
the change, recorded, routed to PARKED.md (P1), does not block.

**`--coverage`:** the new document deliberately carries no `Sweep:`
header, and its body says why — a sweep follows one FIELD across an
agreement, and this agreement is the ABSENCE of traffic, so every
candidate site would be a reader. `SEAM-evaluation-x-ontology` is the
recorded precedent for exactly this. It joins the 16 unswept seams
rather than shipping a spec that cries wolf. 0 findings. : **PASS**

**`--stale`, every entry this tranche touched, judged:**

- `CON-authority.md` — LISTED (6 commits to owned files since
  `d057f306`). **Dismissed, deliberately.** The staleness predates this
  tranche by rungs 2-5; 7a edited only its `Seams:`/`Seams-undocumented:`
  headers and did NOT re-run its check set, so advancing the stamp
  would be the one dishonest state `DR-SCHEMA` names and ERRATA E3
  records. A stale stamp is honest; a false one is not.
- `SUB-adjudication.md` — not listed (`src/deepreason/adjudication/`
  has not moved since `08dcdf3c`). Header edit only; stamp correctly
  unchanged.
- `SEAM-adjudication-x-authority.md` — not listed; new, stamped
  `27e088cb`, the head its claims were measured against.
- `INDEX.md` — not listed (no `Owns:` files).

The remaining ~19 entries belong to earlier rungs and are outside this
tranche's scope; they were surveyed, none names a document 7a touched.

**New checks added by this change:** 8, all in
`docs/map/SEAM-adjudication-x-authority.md` — the two load-bearing ones
(label-time hazard, mint-time safety) were **mutation-proven failable**
before being written down (CHECKLIST step 4), which `--audit` cannot
prove and nothing else would have.

**Record observables added vs sweep probes:** none. This tranche adds
no field, record type or finding to the typed record — it is docs-only
— so no `root_sweep.py` probe is owed. (Contrast rung 4, which did add
an observable and owed its probe a separate commit.)

## Requirement sweep

| R | Demonstrated by |
|---|---|
| R1 route via `dr-change-orchestrator` | phase artifacts in order: REQUEST → SPEC → (stop) → CHECKLIST → execution → VALIDATION |
| R2 DESIGN-AND-STOP through `dr-spec-change` ONLY | held at the SPEC gate; resumed only on Amendment 1's explicit authorization |
| R3 STOP after committing SPEC.md and present | done at `e1e23990`; presented; tranche resumed only after the operator replied |
| R4 the frozen-surface forecast is where it lives or dies | S2 + 4a2 (empty diff) + M5/M6 now executable as checks 1-2 of the new document |
| R5 one rung only | S5; rung 6's directory unchanged, no rung-8 invented |
| R6 SPEC for routing status changes through one gate consulting a declared policy | SPEC.md's finding (half 1 already exists — M1; half 2 forbidden — M5) + Option D; now permanently recorded in the map by 7a |
| R7 the three regions (CON-authority, adjudication, frozen-adjacent) | all three read at preflight and named in the new document's `Sides:`/body |
| R8 do not write before rungs 1-4 delivered | S7 |
| R9 SPEC approved, A1-A5 stand, mint-time placement settled | Amendment 1; the placement is now enforced by check 1, not just asserted |
| R10 do NOT execute 7b or 7c | S8(b) — empty `src/`+`tests/` diff across the whole tranche |
| R11 MAY execute 7a only | S8(a)(c) + the map delta at `725dcab1` |
| R12 stop and confirm the program is complete | DELIVERY.md's program table + the report to the operator |

No requirement is unmet or silently dropped. R6's status is the one
worth reading twice: the SPEC it asked for exists and is approved, and
what 7a delivered is its *finding* made re-runnable — the design itself
(7b) is deferred by the operator's own instruction, not incomplete.

## Assumptions carried

- **A1** — the scatter worth consolidating is the LLM-mediated-text
  authority decision only; deterministic/execution/formal paths stay
  exempt (measured: M4d, M9b). Now documented and checked (checks 6-7).
- **A2** — "declared" means `Config`-projected, not manifest-declared.
- **A3** — the policy object adds no new `Config` field, so the
  `_versioned_source_config_data` trap does not apply. Untested until
  7b runs.
- **A4** — no typed reason string moves (M10).
- **A5** — authority does NOT become a registered module in the
  rung-3/5 sense; rung 6's registry-agnostic framework would apply if
  the operator later wants that.

All five were confirmed by the operator in Amendment 1 (R9) and are
carried into 7b unchanged.

## Verdict: **PASS**

7a is complete and delta-clean against every instrument: +1 document,
+8 checks, no new map failure, no new test failure, empty frozen-surface
diff, and zero `src/`/`tests/` contact.

**But the tree it landed in is not clean, and that is the more
important sentence.** Four instruments are red — 2 map checks and 2 gate
tests — all four traced to `f6d41bff` (rung 5's A/B arm A), all four
proven to pre-date this tranche, and all four rooted in one
mis-specified test rather than in bad evidence. Two of rung 5's
delivered proof claims are consequently stale. PARKED.md P1 holds the
bisect, the diagnosis and the suggested fix.

Per the procedure, pre-existing failures are recorded and do not block
this verdict. They DO block any claim that the rung program finished
green, and DELIVERY.md says so plainly rather than reporting 7a's own
cleanliness as if it were the program's.
