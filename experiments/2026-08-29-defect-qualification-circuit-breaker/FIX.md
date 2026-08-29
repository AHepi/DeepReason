# FIX.md — qualification circuit breaker (defect P7-A)

Re-derived 2026-08-29 after the original lane's work was lost with its
container (`experiments/2026-08-29-ultracode-batch-1/LOSS.md`). Nothing here
is inherited: every structural claim was re-measured on this tree.

## 0. Map preflight

Resolved from `docs/map/INDEX.md` before any design, per CLAUDE.md. The seam
is read BEFORE the subsystems.

**Read first:** `DR-SEAM-llm-x-manifest` — its "Where it is expressed" table
(`SEAM-llm-x-manifest.md:67`) owns the battery row naming
`cli/doctor.py :: exercise_production_contract_case`, which is the site this
tranche edits.

**Then:** `DR-SUB-manifest` (`Owns:` cli/doctor.py), `DR-SUB-llm`
(`Owns:` src/deepreason/llm/), `DR-CON-seats` (`Owns:` cli/doctor.py),
`DR-SUB-application` (`Owns:` src/deepreason/cli/), `DR-INV-frozen-surfaces`.

**Constraint-level, not edit targets** — three committed checks that this
tranche must not break: `INV-render-layout.md:171`
(`! grep -q "layout" src/deepreason/cli/doctor.py`),
`SEAM-bridge-x-llm.md:116` (no `request_with_retries` / `.complete(` under
`src/deepreason/bridge/`), and `SUB-llm.md:27`, which pins `cli/doctor.py`
as the ONLY non-llm caller of `.complete(`.

## 1. The frozen-surface disposition, before implementation

`docs/map/INV-frozen-surfaces.md` states FIVE surfaces spanning SEVEN paths
(surface 3 names both `invariants.py` and `verification/`). **Neither
`cli/doctor.py` nor `llm/endpoints.py` is among them** —
`grep -n "doctor\|endpoints" docs/map/INV-frozen-surfaces.md` returns nothing.

The mechanical gate still returns CONTACT, and the discipline the document
records across its five granted-contact entries requires the gate's own
verdict pasted and disposed ROW BY ROW, before a line of code. Verbatim from
`proof/blast_radius.json`, captured on the clean tree at `5b1d701ad`:

```json
{
 "frozen_surface_verdict": "CONTACT",
 "frozen_surface_contacts": [
  {
   "surface": "qualification subject digests (qualification.py)",
   "tier": "SYMBOL_INDIRECT",
   "target": "run_production_contract_doctor",
   "detail": "'run_production_contract_doctor' referenced in src/deepreason/qualification.py (grep-based; not proof of semantic contact)"
  }
 ],
 "frozen_adjacent_contacts": []
}
```

**Row 1, disposed BY MEASUREMENT, not by assurance** — the standard the
2026-08-24 false-alarm precedent sets (`INV-frozen-surfaces.md:283-296`), and
the standard surface 5's own grant states: *"Preservation is measured per
case, not argued"* (`:511`).

- **What moves.** `run_production_contract_doctor`'s control flow, and one
  new OPTIONAL top-level field on `ProductionContractDoctorReportV1`.
- **What cannot move, measured.** The qualification subject digest is a
  function of the MANIFEST and the PROFILE only
  (`qualification.py:289-297`), and is built from
  `production_contract_pairs(manifest)` with
  `_pair_payload(pair) = pair.model_dump(mode="json", exclude={"pair_id"})`
  (`qualification.py:241, 274-279`). **The doctor report never enters it.**
  This tranche edits no manifest and no profile.
- **The bundle digest cannot move either.** `completed_bundle_from_report`
  (`qualification.py:687-705`) builds the bundle from `report.pairs` ALONE,
  and `_production_qualification_evidence_sha256` (`doctor.py:995-1021`)
  digests only `run_manifest_sha256`, the fixed literals, `pairs` and
  `summary` — never the top-level report object. A new TOP-LEVEL field is
  outside both.
- **The boundary this design deliberately does not cross.** A new field on
  `ProductionContractCaseResultV1` WOULD enter `ReusableQualificationPairV1.cases`
  and therefore the bundle digest, invalidating every cached qualification.
  `SUB-manifest.md:305-308` pins the same hazard for `_pair_payload`. The
  design therefore adds NO case-level field: the distinguishing information
  rides `failure_code`, which already exists.
- **Why no committed root changes verdict.** The new report field is
  `| None = None`, and both persist paths dump with `exclude_none=True`
  (`doctor.py:1280` write, `doctor.py:1421` canonical re-check).

  **CORRECTED after adversarial re-run — the first form of this claim was
  over-broad.** What is TRUE and measured: a battery whose cases all succeed
  writes bytes identical to the pre-fix tree's (39510 both sides, `cmp`
  equal, against `git archive 08c2d7bd1` — `proof/byte_identity.out`), and
  the QUALIFICATION SUBJECT DIGEST — the cache key that decides whether a
  home owes a battery — cannot move at all, because
  `ReusableQualificationPairV1.pair_payload()` (`qualification.py:98-102`)
  excludes `cases`.

  What is FALSE as first stated: "a battery that never trips writes the bytes
  it writes today", full stop. A battery with between one and nineteen
  transport failures per block never trips (it needs twenty) and still
  qualifies on the 19/20 gate, yet writes DIFFERENT bytes — because
  `_failure_code`'s output for a transport condition changed, which is the
  point of the legibility half. `cases[].failure_code` reaches the BUNDLE
  digest through `_reusable_pair` (`qualification.py:679-684`) and
  `ReusableQualificationBundleV1.identity_payload()` (`:146-149`). The
  tranche did not add a case-level FIELD, as it undertook not to; it changed
  a case-level VALUE, which has the same reach into the bundle and no reach
  into the subject. Recorded because the disposition presented itself as
  complete and was not.

**No grant is requested and none is needed.** `qualification.py` (surface 5)
stays OUT of the cone — which is also this tranche's own park list (GOAL.md,
finding C4).

**One design fork the surface forces, decided here before code.**
`resolve_completed_qualification` flattens ANY executor exception —
`except Exception: raise QualificationError("QUALIFICATION_EXECUTION_FAILED", ...) from None`
(`qualification.py:830-836`). So a breaker that RAISES an account-level
condition erases the very condition it exists to report, and could only be
fixed by touching surface 5. **The breaker therefore RETURNS a complete,
valid report and never raises.** That is a correctness constraint, not a
preference.

## 2. The monitor's ruling, recorded verbatim before the code lands

> **STOP 1 (Lane C, P7-A — 323 inserted lines against the 150 ceiling):
> BUDGET RE-DECLARED at the measured 323 for this tranche. Grounds: the cone
> and change sites never moved — every added line sits inside a site FIX.md
> enumerated; the overshoot is estimate error, mostly docstrings and the
> constraint comments CLAUDE.md requires; the declared contingency was
> MEASURED and rejected for cause (saves ~6 of 173 lines and makes the fix
> worse); precedent exists (2026-08-05, 193 against 150). Condition: the
> re-declaration and grounds are recorded, and `tools/diff_budget.py` stays
> armed at its normal ceiling for every future tranche — this is a
> re-declaration, not a repeal.**

**Estimated-diff ceiling for this tranche: 323**, applied to the SOURCE
change sites in §4 (`src/deepreason/cli/doctor.py`,
`src/deepreason/llm/endpoints.py`). Stated plainly because the ruling's own
arithmetic is what fixes the scope: it prices `cli/doctor.py` alone at 216 of
the 323 and the rejected contingency at "~6 of the 173 lines needed", which
are source figures. The gate is run at the end against those paths, and the
total including tests and map is reported beside it, unbudgeted but not
hidden.

The contingency stays rejected, and this tranche re-measured it rather than
inheriting the rejection — see §5.

### Second re-declaration, 2026-08-29 — 356, on the review's findings

The first implementation measured **276 / 323, WITHIN**, and was committed
(`70fdef7e6`). An independent skeptic then re-ran its claims rather than
reading them and confirmed **six defects in it**. Fixing them cost **+80
source lines**, taking the total to **356**, and the gate said `EXCEEDED`.

Put to the operator as a STOP with priced options, not absorbed as a
footnote. **Ruling: BUDGET RE-DECLARED at the measured 356.** Grounds, to the
same discipline as the first re-declaration:

- The cone never moved. Every added line sits inside a change site this
  document already enumerated — `_resolve_circuit_policy`,
  `QualificationCircuitPolicyV1`, `_QualificationCircuit.record`.
- The overrun is not scope creep; it is correctness the first pass got wrong.
  Two of the thirteen regression tests were VACUOUS (green on a tree with no
  breaker at all), the resolver CRASHED the battery on a value
  `str.isdigit()` accepts and `int()` refuses, and two roads to the same OFF
  behaviour warned on only one of them.
- The compression option was MEASURED and rejected: rewriting the notice
  chain as a declared table (better design, and kept) came out four lines
  LARGER, not smaller. The content is irreducible.
- The one option that would have fit — dropping the INERT and THRESHOLD
  warnings — was rejected for cause: it reinstates a confirmed violation of
  the 2026-08-28 law, leaving a reconfigured gate that skips twenty live
  cases on a single blip with zero trace in the record.

Condition, carried forward unchanged: the re-declaration and its grounds are
recorded here, and `tools/diff_budget.py` stays armed at its normal ceiling
for every future tranche. **This is a re-declaration, not a repeal.**

### What the review found, recorded because it shipped once

| # | defect in `70fdef7e6` | disposition |
|---|---|---|
| 1 | R7 and R8 were **vacuous** — both pass on the pre-fix tree; neither asserted the breaker existed or fired | strengthened; both now fail pre-fix with `AssertionError` |
| 2 | "a battery that never trips writes the bytes it wrote before" is **over-broad** | corrected in §1; the all-admitted case is proven, the general case is false, and the reach is the BUNDLE digest not the SUBJECT digest |
| 3 | `_resolve_circuit_policy` **crashed the battery** on `'²'` (`isdigit()` true, `int()` raises), contradicting its own docstring and R13 | guarded by the parse itself; regression test sweeps six hostile values |
| 4 | a **reconfigured gate that never fired left zero trace** — the emission rule bought byte-identity with silence | record is emitted for any departure from the shipped policy |
| 5 | `code_prefixes=()` **silently disabled** the gate — same OFF behaviour as `enabled=False`, no warning | typed `..._INERT` notice; both roads to OFF now warn |
| 6 | the explicit road **refused** what the environment road clamped | clamped in the model; the two roads resolve identically |

Two further findings were recorded rather than fixed: `minimum_block_failures
= 20` means a single non-arming failure in a block prevents that block from
opening the circuit, so the bound is guaranteed only for a uniformly-arming
block (the knob lowers it, and lowering it now warns); and
`derive_route_seat_model_classification` consumes synthesized cases, which is
unchanged from pre-fix behaviour but was not analysed in §1's disposition.

## 3. The cause, re-measured on THIS tree

The brief's cited `cli/doctor.py:535-560` HAS moved, as BATCH.md said. That
range is now inside ONE case's repair loop (`exercise_production_contract_case`,
`doctor.py:470-582`, its attempt loop at `:527`). The real battery loop is
`run_production_contract_doctor` (`doctor.py:1121-1252`): `_case_block` at
`:1171-1208` runs one block of twenty, and `for pair in pairs:` at `:1211`
drives the release gate and the bounded re-exercise.

`_RETRYABLE_HTTP` (`endpoints.py:15`) and `request_with_retries`
(`endpoints.py:51-70`) bound EACH CALL at 2s/4s/8s. **Nothing bounds the
battery.** That is the whole defect, and it is one level above where P7
looked.

### The defect in one table, re-measured offline on the CURRENT default subject

Real doctor, real manifest, real endpoint, real ladder; only the socket and
the clock faked. 15 pairs; 300 cases by `summary.case_count`, **360 cases
actually executed** (three pairs re-exercise a fresh block of twenty, and the
first draw is preserved rather than counted in the summary) — the executed
figure is the right basis for a cost. Both rows below are the PRE-FIX mode:
breaker absent AND the legibility branches removed, which is the only
configuration in which the two records can be identical.

| account-level condition | HTTP calls | sleeps | mandated wait | record written |
|---|---|---|---|---|
| **429** (quota — retryable) | 1440 | 1080 | **5040 s (84.0 min)** | `{'ENDPOINT_ERROR': 360}` |
| **401** (credential — not retryable) | 360 | 0 | **0 s** | `{'ENDPOINT_ERROR': 360}` |

Two failures 84 minutes apart in cost — one that clears on its own, one that
never will — leave **byte-identical records**.

### The correction this tranche owes its own dispatch

**The symptom P7-A was dispatched to fix has no surviving committed
instance.** `experiments/2026-08-25-change-constructive-frontier/qualify-attempt2-VOID-agent-error.json`
records 80 cases, `eventual_valid_count: 0`, 3 pairs re-exercised, and
**140 `ENDPOINT_ERROR` and nothing else** — verified by reading the file. Its
own tranche says why, in its author's words
(`.../CHECKLIST.md:350-358`): *"I had written `source env` in a manual
command; without a leading `./`, bash searches PATH first and sources
`/usr/bin/env` — the coreutils BINARY — which sets nothing, so the doctor ran
against an empty key and every call returned HTTP 401."* A 401 is not on the
retryable list, so **the ladder never slept once**.

**Corrected after an independent re-derivation.** An earlier form of this
paragraph said that battery "took about a minute". That was an INFERENCE from
140 calls and zero sleeps, stated as if it were a measurement, and it is not
evidenced: `CHECKLIST.md:356` records that invocation as MANUAL — *"The ladder
itself was never affected (it sources an absolute path)"* — so it has **no
committed timing at all**. What the record does support: no committed timing
exists for it, and the five committed qualification batteries in the same
tranche's driver log (`driver.log:164-165, 256-259, 344-347`) ran 3m19s,
2m58s, 2m28s, 2m05s and 2m41s. The eighteen-minute figure remains unsupported
— the wall-clock interval one audit cites for it (`10:43:39 → 11:01:55`)
appears nowhere in the repository except in that audit's own sentence.

The number was wrong. The defect is real, and is now better evidenced than
the audit had it.

**C1's target list, corrected from two to FOUR.** A repo-wide census of the
committed carriers, so the parked prompt names the right files:

| # | file:line | what it says |
|---|---|---|
| 1 | `experiments/2026-08-28-audit-run-problems/AUDIT_REPORT.md:551` | "80 cases × 4 pairs of bounded ladders is how 18 minutes is spent" |
| 2 | `experiments/2026-08-28-audit-run-problems/PARKED.md:463-464` | "The 18 minutes is 80 bounded ladders, not one unbounded one" |
| 3 | `experiments/2026-08-28-audit-run-problems/second-window/AUDIT_REPORT.md:561-563` | "≈ 19 minutes, against the 18 minutes epoch 2's qualification actually took (10:43:39 → 11:01:55)" |
| 4 | `experiments/2026-08-28-audit-run-problems/second-window/PARKED.md:187-188` | "≈ 19 min, against the measured 18 min" |

Row 3 is the one C1 most needs to name: it is the only carrier that
manufactures a PROVENANCE — a wall-clock interval — and that interval has no
committed source. Rows 2 and 4 are the parked-prompt texts, i.e. the ones a
future runner is actually handed.

Ruled out explicitly: `experiments/2026-08-26-pc2-rematch/PREREG.md:481`
("Eighteen minutes spent") describes a DIFFERENT phenomenon — reason-run
socket timeouts, not a qualification battery — and is not a C1 target.

`docs/ERRATA.md` is outside this cone, so C1 stays parked; what this tranche
owes it is an accurate target list, and that is now on the record.

## 4. The fix — change sites, enumerated before code

### 4a. Legibility comes first, because the breaker needs it

`EndpointError` gains typed provenance, keyword-only with defaults so all
nine committed raise sites keep compiling untouched:

    def __init__(self, message, *, http_status=None, condition="transport")

storing `self.http_status` and `self.condition`. **It must NEVER set
`.code`.** `_failure_code` (`doctor.py:415`) reads `.code` FIRST, and a
numeric one normalises to the string `"429"`, which fails the field's own
`^[A-Z][A-Z0-9_]*$` pattern. Reproduced: setting `e.code = 429` yields
`'429'` and then `String should match pattern '^[A-Z][A-Z0-9_]*$'`. That is
parked finding **C5**, pointed at this fix; R4 pins that we did not step on
it.

Three raise sites then declare what they know: `endpoints.py:60`
(non-retryable) carries `http_status=e.code, condition="http_refusal"`;
`endpoints.py:70` (ladder exhausted) carries
`http_status=getattr(last, "code", None)`; and the read-timeout, protocol,
empty-content and model-resolution terminals name their own condition.

`_failure_code` gains two branches BETWEEN the existing `.code` branch and
the class-name fallback, so `RunManifestError` precedence is unchanged:
an int status in 100..599 becomes `ENDPOINT_HTTP_<status>`; otherwise a
non-empty `condition` becomes `ENDPOINT_<CONDITION>`.

### 4b. The breaker

**What arms it** is not a status list — it is a failure-code family plus a
block-exhaustion threshold, and both are configuration. `code_prefixes`
(default `("ENDPOINT_",)`) selects which typed codes arm it; a contract or
schema failure does not begin `ENDPOINT_` and must not arm it, because that
is genuine model incapacity the battery exists to measure.
`minimum_block_failures` (default 20) is how many of a block's twenty must
have failed with an arming code. **No status is special-cased anywhere**:
401 and 429 travel the same path and differ only in the code they write.

That pins both directions the goal requires. An account-level refusal fails
20/20 and opens. A transient 429 that clears fails fewer than 20 — one
success resets the block — and never opens.

**Evaluated at BLOCK boundaries, never mid-block.** This is the one decision
worth arguing for.
`test_battery_parallelism_changes_wall_clock_never_the_report`
(`tests/test_cli_production_doctor_v6.py:597-641`) asserts
`parallel.model_dump() == sequential.model_dump()` at 8 workers versus 1. A
breaker consulted per case would make WHICH cases are short-circuited depend
on completion order, and that committed determinism guarantee would go red —
or, worse, flake. The price is bounded and measured: at most ONE block of a
dead route is spent, 20 calls for a 401 and 80 calls / 280 s for a 429.

**Keyed per `(endpoint_id, route_sha256)`**, both already carried on
`ProductionContractPairV1`. See §5 for the measurement that keeps this
keying.

**When it trips it returns, never raises** (§1's forced fork).
`open_block(pair)` synthesises the full canonical twenty — the report schema
requires exactly `case-001` through `case-020`
(`doctor.py:176-184`), so truncation is not available and is not wanted —
each carrying `failure_code = "CIRCUIT_OPEN_" + <the code that opened it>`.
The record therefore says WHICH condition opened the circuit, not merely
that one did.

Three wiring points, all in `run_production_contract_doctor`:

1. `_case_block` — the envelope pre-validation loop STAYS AHEAD of the
   short-circuit (it spends no provider call, and
   `test_doctor_requires_complete_route_envelope_before_scripted_case`
   requires it to raise first). The short-circuit then advances the progress
   callback twenty times, keeping it monotone and terminating.
2. After a block is assembled, `circuit.observe(pair, cases)`.
3. The re-exercise decision gains `and circuit.opening(pair) is None`.
   Re-exercise exists for stochastic flake; spending the finite allowance of
   three on a route whose circuit is open both wastes it and misreports
   `re_exercised_pair_count` AS flake evidence.

### 4c. The configuration surface is NOT a `Config` field, and that is load-bearing

A `Config` knob is serialised into every manifest's `engine_config_json` and
hashed into `source_config_hash`, so it moves **every qualification subject
digest** unless it is dropped by a `data.pop` line in
`run_manifest.py::_versioned_source_config_data` — and `run_manifest.py` is
**frozen surface 4**, which this tranche has no grant for. Measured, so the
fork is priced rather than asserted: with a new field kept in the echo the
shipped `source_config_hash` moves
`6c2d01f6…` → `0640d93d…`; with the pop line it is byte-identical.

So the whole surface is one resolver in `cli/doctor.py`, mirroring the
committed precedent in the SAME function — `_qualification_concurrency`
(`doctor.py:1105-1119`), which already resolves a dispatch knob from
`DEEPREASON_QUALIFY_CONCURRENCY`. It clamps and never refuses
(all-configurations law, 2026-08-12): a nonsense value resolves
deterministically instead of stopping a battery.
`run_production_contract_doctor` also gains a `circuit_policy=` keyword, so a
caller can pass a policy object without touching the process environment.

**Stated plainly: the knobs are FREE, and free by construction rather than by
a drop line** — there is no new `Config` field at all, therefore no new
`engine_config_json` key, no `source_config_hash` move, no manifest digest
move, no qualification subject digest move, and **no home owes a ~14-minute
battery.**

**The tension, disposed rather than hidden.**
`tests/test_channel_and_wander_modularity.py:38-42` names, as a bypass it
forbids, *"an environment variable a Config cannot express"*. That is a rule
about CHANNEL toggles, which govern a RUN and must therefore be expressible
in the run's own declared configuration. The breaker governs the
QUALIFICATION BATTERY — a pre-run diagnostic, not run behaviour — and its
setting is recorded in the doctor REPORT, which is that activity's record.
It is never ambient-and-invisible. The Config road remains available at a
measured price (one operator grant on surface 4 plus one pop line), and it
would additionally mint a fresh instance of parked **P25**: the
`ENGINE_CONFIG_FIELD_NOT_CARRIED` notice would read "the run will use
<default>" for a knob the qualify path DOES honour.

### 4d. The typed warning, on the mechanism this area already has

Checked before inventing one. The only committed notice mechanism nearby is
`CompileNoticeV1` (`run_manifest.py:1191-1222`) — compile-time, attached to
the manifest, and unreachable here because it is frozen. The doctor report
has no notice channel today. So the notice is MODELLED on `CompileNoticeV1`
(`code`/`message`/`pointer`) and carried by the report, which is the record
and therefore the only admissible evidence.

Switching the breaker off is a **WARNING, never a refusal** (operator law,
2026-08-28): the battery runs exhaustively exactly as it does today, and the
report carries `QUALIFICATION_CIRCUIT_BREAKER_DISABLED` at pointer
`/circuit_breaker/enabled`.

**Emission rule, so committed reports stay byte-identical:** the record is
`None` unless the breaker is disabled OR at least one circuit opened.

### 4e. Enumerated change sites

| file | anchor | what changes |
|---|---|---|
| `llm/endpoints.py` | `:42` `EndpointError` | typed `__init__`; `http_status`, `condition`; never `.code` |
| `llm/endpoints.py` | `:51` `request_with_retries` | both terminal raises carry the status |
| `llm/endpoints.py` | `:449`, `:481`, `:494`, `:94` | each terminal names its condition |
| `cli/doctor.py` | `:49` module constants | `_DEFAULT_CIRCUIT_CODE_PREFIXES`, `_CIRCUIT_ENV_BY_FIELD` |
| `cli/doctor.py` | `:151` after `_release_gate` | `QualificationCircuitPolicyV1`, `…NoticeV1`, `…OpeningV1`, `…RecordV1` |
| `cli/doctor.py` | `:229` `ProductionContractDoctorReportV1` | one optional `circuit_breaker` field |
| `cli/doctor.py` | `:415` `_failure_code` | two branches, between the existing two |
| `cli/doctor.py` | `:1105` after `_qualification_concurrency` | `_resolve_circuit_policy`, `_QualificationCircuit` |
| `cli/doctor.py` | `:1121` `run_production_contract_doctor` | `circuit_policy=` keyword; three wiring points |
| `cli/doctor.py` | `__all__` | export the policy and record models |

Tests (unbudgeted, reported): `tests/test_cli_production_doctor_v6.py`
(R5-R13), `tests/test_llm.py` (R1-R4), new
`tests/test_qualification_circuit_modularity.py` (the two architecture
tests). Proof: `proof/measure_account_level_battery_cost.py`.

## 5. The declared contingency, re-MEASURED and rejected again

The ruling records that the contingency (dropping the per-endpoint keying)
"saves ~6 of the 173 lines and makes the fix strictly worse". This tranche
did not inherit that: it re-measured it on the committed `_manifest()`
fixture (10 pairs across 5 distinct `endpoint_id`s) with the `critic` route
dead and everything else healthy.

| keying | cases dispatched | pairs qualified |
|---|---|---|
| **per-route** (kept) | critic 20; composer/conjecturer/ledger/reviewer 40 each | **8 of 10** |
| **global** (contingency) | 20 in total | **0 of 10** |

A global key converts ONE dead route into a false verdict on every other
route. It is rejected for cause, again, and by measurement rather than by
citation.

Per-endpoint keying is also reachable on a real subject: a seat-bound
manifest splits the default 15 pairs into a 2-pair route and a 13-pair
route. It is NOT observable on the plain single-profile subject, where all
15 pairs share one key — recorded as a residue, not hidden.

## 6. Success criterion → regression test map

Thirteen tests, each with the ONE source mutation that must redden exactly
it. R1-R4 pin the legibility half and the C5 guard; R5-R7 pin the breaker's
two directions and its keying; R8-R11 pin that the record survives, names
the condition, suppresses the re-exercise allowance and stays byte-identical
when nothing trips; R12-R13 pin the opt-out warning and the clamping
resolver. Two architecture tests (A1, A2) go red if changing the behaviour
ever needs a code edit.

## 7. Decided and NOT done, recorded rather than dropped

- **`429` stays in `_RETRYABLE_HTTP`.** The parked question is answered by
  measurement, not taxonomy: making 429 terminal would kill recoverable
  rate-limited batteries at case 1, whereas the breaker caps the cost of an
  unrecoverable one at a single block. The per-call ladder stays a per-call
  concern; the cross-case bound is what was missing.
- **C4 stays parked.** The provider status now reaches the RECORD, not the
  `deepreason qualify` console line — that needs surface 5.
- **C5 stays parked** and is made strictly less reachable.
- **C1's ERRATA correction** is not written here; `docs/ERRATA.md` is
  outside this cone. The numbers to write it with are in §3 and are stronger
  than the audit's.
