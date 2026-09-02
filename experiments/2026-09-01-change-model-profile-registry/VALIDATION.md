# Validation: "Take this particular task out of the hands of the machine"

Verdict: **PASS**

Every acceptance check in SPEC.md was re-run against the assembled whole, in
item order, after the last code change — not trusted from the checklist steps
that first ran them. Outputs below are pasted, not summarised.

## 1. Acceptance checks, in item order

| item | check | result |
|---|---|---|
| S1 | a document written to a temp home resolves by its declared id; an undescribed model resolves to `None` | `S1 accept: OK` (exit 0) |
| S2 | no `REASONING_OFF` / `reasoning_disabled` survives anywhere under `src/` (bound by AST, not grep); `plan_split` raises `TypeError` naming `profile` when the keyword is omitted | `S2 accept: OK` (exit 0) |
| S2b | exactly one `_reasoning_disclosure`, exactly two call sites, no `_reasoning_disabled_refusal` anywhere | `S2b accept: OK — one disclosure function, two call sites, no refusal` (exit 0) |
| S3 | an undescribed model stands the split down with `split-budget:no-model-profile-for-this-seat`, disclosed | `S3 accept: OK` (exit 0) |
| S3 | the protocol's own ring | `22 passed in 0.30s` (exit 0) |
| S4 | `_record_module_fingerprints` names the registry and calls `registry_fingerprint` | exit 0 |
| S4 | the stamp reaches the record | `2 passed, 23 deselected` (exit 0) |
| S5 | five documents, each dated and citing evidence | `S5 accept: OK, 5 documents, every one dated and citing evidence` (exit 0) |
| S6 | the probe's self-test | exit 0 |
| S6 | the probe against P-S1's true glm-5.3 fixture | `10/10 claims hold` (exit 0) |
| S6 | the probe against a fixture mutated to contradict ONE claim | `FAIL extraction_value low expected=8/8 clean observed=7/8 clean` → **exit 1** |
| S7 | the architecture tests | `36 passed in 4.93s` (exit 0) |
| S8 | `docs_verify --links` | `0 dangling reference(s), 72 document(s)` (exit 0) |

S6's pair is the one that matters most and is stated as a pair on purpose: a
probe that cannot go red is not a probe.

## 2. The full gate

    $ python -m pytest tests/ -q -n 4
    4633 passed, 6 skipped in 803.93s (0:13:23)

**0 failed.** Run alone on an idle box, `__pycache__` cleared first
(`docs/map/SCHEMA.md`: stale bytecode survives a revert, and has manufactured a
phantom failure here before).

The 6 skips are the container's own, not this tranche's: `test_browser.py`
cannot import `playwright`, recorded in BASELINE.txt before any edit.

**Neither pre-authorized waiver was used, and neither was needed.** The window
pre-authorized two known-not-yours reds. Measured before any edit, both were
already GREEN on this container: `bc` is installed at `/usr/bin/bc`, and
`test_the_shipped_qualification_subject_digest_does_not_move` passed. It passes
still, inside the 4633.

## 3. Frozen-surface diff — the one mechanical tripwire

    $ git diff --stat dd0916fb5..HEAD -- \
        src/deepreason/capabilities/state.py src/deepreason/harness.py \
        src/deepreason/invariants.py src/deepreason/run_manifest.py \
        src/deepreason/qualification.py src/deepreason/verification/ \
        src/deepreason/llm/firewall.py
    (no output)

Empty, including the two paths the tranche's own constraints add to the
standard five (`verification/` and the frozen-adjacent `llm/firewall.py`).

The run-level disclosure reaches the append-only record instead through a
second `ModuleFingerprintV1` row on the existing module-fingerprints event —
the extension point that payload's own docstring declares ("further registries
can be stamped later without a schema change") and whose payload materializes
no state, so replay applies it by ignoring it.

Both compile-time roads were measured and rejected rather than argued away:

    $ python experiments/.../price_notice_road.py
    manifest sha BASE    1950b3d0ee2281137ee3a54def61252b129a955ff30a938feb9044d5ed7ff628
    subject BASE         b3f807f386f29cd83e69993beaed2a91723fc14d59eb93b5122c68acc2eee79b
    manifest sha +NOTICE b6afc4045d8125bea069c6cbb9452eaca5ac787692074ab0bd1d9d69003febea
    subject      +NOTICE 29bcca270c006ec5687037b20eab597942fb0261e107ffe58186e4ad20d43bd8

One added compile notice, nothing else changed, and BOTH digests move.

## 4. Behaviour preservation on the record

This change touches a WRITER of the typed record (one extra fingerprint row)
and no reader or validator of it. `verify_root`'s `split-legs` family reads
every field a leg writes; no field was added or changed. The two new strings
are notice VALUES, and `LLMSplitLegV1.notice` is an open `str` with no
`Literal` (`ontology/event.py:90-91`), read by exactly one limb, which tests it
for emptiness (`invariants.py:4338`). The full gate includes
`tests/test_split_leg_recording.py`'s seven `split-legs` limb tests and
`test_verify_root_accepts_a_thinking_on_record`; all pass.

## 5. Packaging surface

The surface DID move — a new package directory and a new script — so the smokes
are owed and were run.

    $ python scripts/wheel_smoke.py
    wheel smoke passed: isolated V6-only contents, clean imports, exact entry
    points, module parity, MCP registration, and exact MCP schemas

    $ python -u scripts/wheel_operational_smoke.py
    "stage":"continuation_resume"  "failure_kind":"assertion_failed"   FAILS

**The operational smoke's failure pre-dates this tranche, and that was
measured, not assumed.** The same script run against an archive of the
pre-tranche base `dd0916fb5` fails at the SAME stage with the SAME failure
kind. Two further facts make the attribution safe rather than convenient: the
pin on the surface this tranche actually moves (`wheel_smoke.py`) PASSES, so the
new package really is in the wheel and the entry points really are unchanged;
and the operational smoke's fixture runs `--provider generic`, for which
`reasoning_knob_available` is False — so `_reasoning_disclosure` returns before
consulting any document and `plan_split` returns `NOTICE_NO_REASONING_KNOB`
exactly as before. There is no path by which this change reaches the failing
stage. Parked as PARKED.md **P6**.

## 6. Map validation

    $ python tools/docs_verify.py
    72 documents, 1302 checks, 4 workers ... 5 failed
    $ python tools/docs_verify.py --audit
    1 finding(s)
    $ python tools/docs_verify.py --links
    0 dangling reference(s), 72 document(s)
    $ python tools/docs_verify.py --coverage
    7 seam(s) swept, 19 without a Sweep: header, 2 finding(s)
    $ python tools/docs_verify.py --stale
    15 document(s) worth re-reading

**Every one of those failures and findings pre-dates the tranche, each proven
against the base rather than asserted** (BASELINE.txt addendum 1):

- `SEAM-llm-x-rules.md:54` unparseable check — line 54 is BYTE-IDENTICAL at the
  base. It is also the single `--audit` finding. A document-authoring error in
  a file this tranche never opened.
- `CON-run-identity.md:211/213/215` — `git log 1637e808` returns "unknown
  revision" in this container's clone. Repo-global, independent of the tree.
- `INV-frozen-surfaces.md:181` — 1 matching file at the base, 1 now.
- `--coverage`'s two findings name `SEAM-periphery-x-verification.md` and
  `SEAM-schools-x-scratch.md`, neither touched here; the 19 missing `Sweep:`
  headers are all pre-existing.

Every check in the five documents this tranche DID touch passes: 7/7 in
`CON-model-profiles.md`, 23/23 in `SUB-llm.md`, 13/13 in `CON-seats.md`, 1/1 in
`INDEX.md`, 11/11 in `SEAM-schools-x-scheduler.md`.

**`--stale` earned its keep and was acted on, not just read.** It flagged three
documents owning files this tranche changed. Two (`SUB-scheduler.md`,
`SUB-application.md`) make no claim the change falsified — checked by reading,
not by assuming: `SUB-application.md` owns `cli/` and mentions neither
`REASONING_MUST_BE_DISABLED` nor `reasoning_disabled` anywhere. The third,
`SEAM-schools-x-scheduler.md`, did carry a claim gone stale: its "Which module
built the run" row described the module-fingerprint stamp as if it carried only
the school-population row. It now says the payload carries a second
`model-profiles` row and that a change there must not assume a list of length
one. Its 11 checks were re-run before its `Verified-at` was advanced.

`Verified-at` was advanced on exactly the five documents whose checks were
actually re-run, and on no others.

## 7. Budget — EXCEEDED, and accounted for rather than excused

    $ python tools/diff_budget.py dd0916fb5 --ceiling 1416
    {"result_type": "DIFF_BUDGET_RESULT_V1", "total_insertions": 2910,
     "ceiling": 1416, "verdict": "EXCEEDED"}

2910 against a ledgered 1416 — 106% over. Two distinct causes, and only one of
them is an estimation error:

**(a) 335 lines the budget never counted at all.** The tranche's own ledger —
BASELINE.txt, MUTATION_RED/GREEN.txt, PARKED.md's seven entries, the price
probe, SPEC.md's own growth — is required by the workflow and was itemized
nowhere. The budget priced deliverables and forgot the evidence.

**(b) The deliverables themselves came in at ~2x their estimate.** The largest
misses, in order: `tests/test_model_profile_registry.py` 220 → 659 (the
estimate priced one file's worth of architecture checks; the file ended up
carrying S1's resolution tests, S2/S3's behaviour tests, S4's record-stamp
tests AND S7's four architecture checks — eight sections);
`scripts/model_profile_probe.py` 150 → 323; `tests/test_model_profiles_document.py`
170, omitted from the itemization entirely though S1's own accept implied it;
`docs/map/CON-model-profiles.md` 130 → 240. Under-estimates, not
over-delivery: the shipped code carries this repo's comment density, and the
estimates were made as if writing terse code.

Two things came in UNDER: `docs/model-profiles/` at 288 against 380, and
`tests/test_split_budget_protocol.py` at 49 against 60.

**It is not scope creep, and that is checkable rather than assertable.** Every
one of the 32 changed files traces to a numbered spec item: the only file not
forecast at spec time is `src/deepreason/cli/main.py`, which is S2b, recorded
in SPEC.md with its own acceptance check and its own reasoning before it was
written. No file in the diff lacks an S number.

## 8. Assumptions carried into delivery

A1 (reference copies live in `docs/model-profiles/`, loader never reads them),
A2 (two of M1's field names changed — `extraction_value` rather than
"most-off", and `disabling_values` added — because on glm-5.3 the value that
produces a clean answer is neither the most-off value nor a disabling one),
A3 (R9: no substitution, no veto, anywhere), A4 (`--trials` default 8, matching
P-S1's own trial count), A5 (`SPLIT_BUDGET_SEAT_PROTOCOL` keeps its `auto`
default). Each is in SPEC.md and each is the operator's to override.

## 9. What this validation does NOT establish

Stated because a validation that only lists passes is a validation that has not
been read.

- **No live run was made.** C5 forbids one. That the emission leg now sends
  `low` on glm-5.3 is proven offline; that `low` produces clean content on
  glm-5.3 rests entirely on P-S1's committed 8-trial table, which this tranche
  cites and did not re-measure.
- **The probe has never been run against a provider.** Its live path is
  committed and its offline path is proven both green and red; the live path is
  untested code.
- **`docs/model-profiles/` is not on any loader's search path**, so the five
  authored documents change nothing until a human copies one into
  `$DEEPREASON_HOME`. A container that installs this change and runs the
  harness gets the unknown-model path for every seat — which is the designed
  behaviour under R8, and is not the same thing as glm-5.3 being fixed for a
  run that has not had its document installed.
- **The same hard-coded value survives at `verification/llm_broker.py:225`**, in
  a frozen file this tranche may not touch. Verified first-hand, parked as P5.

Verdict: **PASS**. No acceptance check failed, the gate is 0 failed, and every
red found anywhere was measured against the pre-tranche base before being
attributed elsewhere.
