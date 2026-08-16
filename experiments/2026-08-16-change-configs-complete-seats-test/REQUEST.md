# REQUEST — finish all-configs-allowed (Part A), pin seats/evidence (Part B)

Tranche dir: `experiments/2026-08-16-change-configs-complete-seats-test/`
Branch: `claude/configs-complete-seats-test-7wg7fu`
Opened: 2026-08-16
Base: `5f648ebc9` (`origin/main` at session start; `git merge-base
--is-ancestor 5f648ebc9 HEAD` → 0)

## 0. Map preflight (recorded before any design, per CLAUDE.md)

Resolved ids, from `docs/map/INDEX.md`:

| id | why it is in scope |
|---|---|
| `DR-SUB-manifest` | `run_manifest.py` — the great majority of Part A's denial sites and the `CompileNoticeV1` mechanism. **FROZEN surface 4** (manifest schema + validators); operator pre-grant covers model AND validator together for this tranche. |
| `DR-CON-seats` | `seat_bindings.py`, `select_lease` — Part B's subject; also the already-converted seat-binding rows Part A must row `already-done`. |
| `DR-CON-schools` | `_validate_v4_control_plane_policy`'s school topology; `capture/schools.py` is the downstream typed-guard question P1(a) makes a precondition. |
| `DR-CON-criticism-source` | `rules/crit.py` — the downstream side of `_validate_v4_criticism_policy`; Part B's "criticism cannot be skipped" mechanism. |
| `DR-CON-authority` | `authority.py`'s `text_status_authority_issues`, the L2/warrant-status boundary Part B asserts against. |
| `DR-SUB-scratch` | `_compile_scratch_policy`'s embedder fallback (P1(d)); `advisory_non_grounding`, which is itself a seats/evidence guard Part B attacks. |
| `DR-SEAM-manifest-x-schools` | read BEFORE either side, per the ordering rule — the v4 school/criticism cluster is exactly this seam. |
| `DR-SEAM-adjudication-x-authority` | Part B's law lives here: who may change a Status. |
| `DR-INV-frozen-surfaces` | read before designing; surface 4 is pre-granted for Part A, no other surface is. |

## 1. The operator's words, verbatim

Reproduced exactly as sent. Requirement numbers are assigned in §2; the
text below is never edited.

> Change tranche, two parts in strict order: (A) finish the
> all-configurations law — convert the ~20 remaining compile-time denial
> sites to typed disclosures; then (B) pin the seats/evidence law with an
> adversarial regression test written over the CONVERTED surface, seeded
> from Part A's own census. Route through dr-change-orchestrator; no stops.
>
> SETUP (fresh container): git fetch origin main && git checkout -B
> claude/configs-complete-seats-test-h27nqe origin/main; git merge-base
> --is-ancestor 5f648ebc9 HEAD || re-fetch. pip install -e .
> --break-system-packages -q; pip install pytest pytest-xdist jsonschema
> --break-system-packages -q. Use `python -m pytest`, never bare pytest.
> Read CLAUDE.md in full; load dr-drive-harness, dr-explain-to-operator.
>
> AUTHORITY for REQUEST.md, ledger all three verbatim:
> (1) The standing law (CLAUDE.md §Operator design laws, 2026-08-12):
> "All configurations should be allowed." — Part A completes its
> delivery; the delivering tranche
> (experiments/2026-08-12-change-all-configs-allowed/) converted ~13 of
> ~33 censused denial sites and SELF-PARKED the remainder; its own parked
> list is Part A's worklist. Cross-check against the audit's
> confirmation (experiments/2026-08-13-audit/goal-trace.md L5 row and
> PARKED.md) that the park is still open.
> (2) The standing law (CLAUDE.md, seats/evidence): "Seats change how
> content is GENERATED, never what counts as EVIDENCE" — Part B builds
> the test that makes violating it visible; the audit's L2 row records
> that no test currently pins the claim.
> (3) The operator's sequencing decision (2026-08-13, this tranche's
> reason for existing as ONE window): convert first, then test over the
> converted surface — a test written before the conversion asserts the
> wrong layer and breaks when the conversion lands.
>
> PART A — finish the conversion:
> - Worklist: the delivering tranche's own parked remainder (~20 sites).
>   Re-derive the list fresh (grep the denial/raise sites it names and
>   confirm each still refuses on current main — pasted proof per site);
>   a site already converted by an intervening tranche is rowed
>   `already-done`, not re-converted.
> - Each site converts to the SAME pattern already on main: input that
>   parses compiles; the former refusal becomes a typed compile notice
>   (CompileNoticeV1 / compile_notices) recorded alongside the result;
>   genuinely contradictory configurations get a deterministic resolution
>   rule stated in SPEC.md, never a refusal. Parse/shape errors stay
>   refused (they are not configurations).
> - Runtime stays unchanged: point-of-use typed failures are correct and
>   out of scope.
> - Tests pinning each old refusal flip to asserting compile + notice,
>   enumerated in SPEC.md before any is touched.
> - CENSUS ARTIFACT (feeds Part B): a table of every site converted or
>   confirmed-converted, with the configuration shape each one now
>   admits. This file is Part B's input, not an afterthought.
>
> PART B — the adversarial seats/evidence test (only after Part A's gate
> is green):
> - One new test file (e.g. tests/test_seats_evidence_law.py) whose
>   docstring names the law verbatim and this tranche.
> - Attack list = every configuration shape from Part A's census that
>   touches seat binding, school routing, criticism policy, judge roles,
>   or scratch — PLUS the previously-constructible shapes the audit's L2
>   proof file names. For each: construct the configuration, compile it
>   (it must compile, per Part A), then prove the LAW at the point of
>   use — any path by which a generation seat's output could acquire
>   evidence/warrant status without passing through the criticism
>   machinery must come back typed-refused or criticism-routed. Assert
>   the mechanism, not the prose: the test inspects the typed record
>   (warrants, attack edges, criticism transactions), never model output.
> - MUTATION PROOF (the gate that makes this test worth having): break
>   the guarded thing once — e.g. in a scratch copy, disable the
>   criticism-routing check the test leans on — run the test, watch it go
>   RED, restore, paste both runs. A test never seen red proves nothing.
> - The test joins the ordinary gate (no special marks); if any attack
>   case exposes a REAL current violation of the law, that is a finding,
>   not a fix: PARK it with a deepreason-orchestrator prompt and mark the
>   test case xfail-with-pointer so the gate stays honest about it.
>
> PRE-GRANTED (scoped): surface 4 (run_manifest.py model AND validator
> together) for Part A's conversions — the standing law is the ledgered
> authority, same grant shape as the original tranche. If IntakeFormV1's
> schema moves: all FOUR pins in the SAME commit (wheel_smoke.py,
> wheel_operational_smoke.py, tests/test_mcp.py, tests/test_mcp_help.py)
> + regenerate FORM_DR1 (--check clean). Cross-version replay proofs are
> retired (CLAUDE.md 2026-08-14 law); current-version record integrity is
> covered by the ordinary gate. Qualification-digest drift: REPORT the
> cost, don't stop.
>
> KNOWN CURRENT STATE, so you do not misattribute it: the installed-wheel
> operational smoke is FLAKY at its `reason` stage on an unmodified tree
> (pre-existing, parked with evidence in experiments/2026-08-16-change-
> embedder-auto-install/PARKED.md P1). If it fails at that stage with
> "terminal verification is incomplete", that is the parked defect, not
> your change — say so and move on; any OTHER smoke failure is yours.
>
> GATE: ring while iterating; full gate at the boundary (baselines per
> docs/AUDIT_BASELINES.md — expectation is 0 failed; 5 MCP-thread tests
> known-flaky under -n 4, isolate before attributing). docs_verify full
> (3 pre-existing CON-run-identity.md shallow-clone failures). Map moves
> in the same commits. Errata check: any committed document claiming the
> all-configs conversion is COMPLETE gets an entry (next free number —
> check the ledger tail); otherwise the scan and its output are the
> checkpoint. Commit and push every phase boundary (retry 2s/4s/8s/16s).
> Deliver R-by-R with pasted PROOF; DELIVERY.md's close states, in one
> line each: how many sites now emit notices vs how many existed, and how
> many attack cases the law's test holds against.

### 1a. The three ledgered authorities, verbatim

**A1 — the all-configurations law** (CLAUDE.md § Operator design laws,
2026-08-12), operator's words verbatim:

> All configurations should be allowed.

**A2 — the seats/evidence law** (CLAUDE.md § Operator design laws),
stated verbatim as CLAUDE.md carries it:

> Seats change how content is GENERATED, never what counts as
> EVIDENCE

with its own binding clause, verbatim:

> no seat, mode, or package may let a generation seat's prose skip
> criticism.

**A3 — the sequencing decision** (2026-08-13), operator's words verbatim
from this tranche's own prompt (§1, "AUTHORITY" item 3):

> convert first, then test over the converted surface — a test written
> before the conversion asserts the wrong layer and breaks when the
> conversion lands.

### 1b. Branch-name discrepancy, recorded not silently resolved

The prompt's SETUP line names `claude/configs-complete-seats-test-h27nqe`.
The session's own designated development branch (harness assignment, which
is where a push is permitted) is `claude/configs-complete-seats-test-7wg7fu`.
Both name the same tranche; the suffix differs. Work proceeds on
`...-7wg7fu` because that is the branch this session is authorized to push,
and its base is verified identical to what SETUP asks for
(`origin/main` = `5f648ebc9`). Recorded here rather than decided silently.

## 2. Numbered requirements

### Part A — finish the conversion

- **R1** Convert the remaining compile-time denial sites (~20) to typed
  disclosures. Worklist = the delivering tranche's own parked remainder
  (`experiments/2026-08-12-change-all-configs-allowed/PARKED.md`, P1–P4,
  plus its SPEC.md §3 CONVERT-SPEC'D rows).
- **R2** Re-derive the worklist FRESH: grep each named denial/raise site
  and confirm it still refuses on current main, with pasted proof per
  site. A site converted by an intervening tranche is rowed
  `already-done`, never re-converted.
- **R3** Each conversion uses the SAME pattern already on main: input
  that parses compiles; the former refusal becomes a `CompileNoticeV1`
  recorded in `compile_notices` alongside the result.
- **R4** Genuinely contradictory configurations get a deterministic
  resolution rule STATED IN SPEC.md — never a refusal.
- **R5** Parse/shape errors stay refused (they are not configurations).
- **R6** Runtime stays unchanged: point-of-use typed failures are
  correct and out of scope.
- **R7** Tests pinning each old refusal flip to asserting compile +
  notice, ENUMERATED IN SPEC.md before any is touched.
- **R8** Produce a CENSUS ARTIFACT: a table of every site converted or
  confirmed-converted, with the configuration shape each one now admits.
  This file is Part B's declared input.

### Part B — the adversarial seats/evidence test

- **R9** Part B starts only after Part A's full gate is green.
- **R10** One new test file (`tests/test_seats_evidence_law.py`) whose
  module docstring names the law verbatim and this tranche.
- **R11** Attack list = every census configuration shape touching seat
  binding, school routing, criticism policy, judge roles, or scratch,
  PLUS the previously-constructible shapes named in
  `experiments/2026-08-13-audit/proof/goal-L2.txt`.
- **R12** For each attack: construct the configuration, compile it (it
  MUST compile, per Part A), then prove the law at the point of use —
  any path by which a generation seat's output could acquire
  evidence/warrant status without passing through the criticism
  machinery must come back typed-refused or criticism-routed.
- **R13** Assert the MECHANISM, not the prose: inspect the typed record
  (warrants, attack edges, criticism transactions); never model output.
- **R14** MUTATION PROOF: break the guarded thing once in a scratch
  copy, run the test, watch it go RED, restore, paste both runs.
- **R15** The test joins the ordinary gate (no special marks).
- **R16** If an attack case exposes a REAL current violation: that is a
  FINDING, not a fix — park it with a `deepreason-orchestrator` prompt
  and mark the case `xfail` with a pointer, so the gate stays honest.

### Cross-cutting

- **R17** Pre-granted scope: frozen surface 4 (`run_manifest.py` model
  AND validator together) for Part A's conversions. No other frozen
  surface is granted.
- **R18** If `IntakeFormV1`'s schema moves: all FOUR pins in the SAME
  commit (`scripts/wheel_smoke.py`, `scripts/wheel_operational_smoke.py`,
  `tests/test_mcp.py`, `tests/test_mcp_help.py`) + regenerate FORM_DR1
  (`--check` clean).
- **R19** Cross-version replay proofs are retired (CLAUDE.md 2026-08-14
  law); current-version record integrity is covered by the ordinary gate.
- **R20** Qualification-digest drift: REPORT the cost, do not stop.
- **R21** Gate: ring while iterating; full gate at each phase boundary,
  baselines per `docs/AUDIT_BASELINES.md`; expectation 0 failed, 5
  MCP-thread tests known-flaky under `-n 4` (isolate before attributing).
  `python tools/docs_verify.py` full (3 pre-existing `CON-run-identity.md`
  shallow-clone failures).
- **R22** The map moves in the SAME commits as the code.
- **R23** Errata check: any committed document claiming the all-configs
  conversion is COMPLETE gets an entry at the next free number (ledger
  tail is E32, so E33); otherwise the scan and its output are the
  checkpoint.
- **R24** Commit and push at every phase boundary (retry 2s/4s/8s/16s).
- **R25** Deliver R-by-R with pasted PROOF. DELIVERY.md's close states,
  in one line each: how many sites now emit notices vs how many existed,
  and how many attack cases the law's test holds against.
- **R26** No stops. Route through `dr-change-orchestrator`.

## 3. Known-state acknowledgements (not requirements — facts to not misattribute)

- `scripts/wheel_operational_smoke.py` is FLAKY at its `reason` stage on
  an unmodified tree (parked, `experiments/2026-08-16-change-embedder-
  auto-install/PARKED.md` P1). A failure there reading "terminal
  verification is incomplete" is the parked defect, not this tranche's.
  Any OTHER smoke failure is this tranche's.
- `docs/AUDIT_BASELINES.md` is the baseline authority for the gate.

## 4. Cross-check: is the park still open? (R1's own precondition)

`experiments/2026-08-13-audit/goal-trace.md` L5 row, verbatim:

> | L5 | All configurations should be allowed | partially-enforced |
> `CompileNoticeV1`/`compile_notices` (`run_manifest.py` + 4 more sites) |
> many (`test_run_manifest.py`, `test_seat_bindings.py`,
> `test_config_scratch_bridge.py`, `test_manifest_integration.py`,
> `test_intake_form.py`, `test_run_manifest_scratch_bridge.py`) |
> proof/goal-L5.txt | parked |

L2 row, verbatim:

> | L2 | Seats change GENERATED, never EVIDENCE | partially-enforced |
> generation/criticism seat-binding separation (`seat_bindings.py`) |
> `tests/test_seat_bindings.py` + 4 more | proof/goal-L2.txt | parked |

Both dispositions are `parked` — the park is open, and this tranche is
its authorized closer for the scope §2 states.

## 5. Amendments

None yet. New operator messages are appended here verbatim BEFORE being
acted on.
