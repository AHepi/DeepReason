# Validation for: the stop report — the harness writes the first failure report

REQUEST.md (incl. Amendments 1 and 2), SPEC.md and CHECKLIST.md re-read in
full before running any of this. Every output below is real and pasted.

## Acceptance checks

**S1 (R1, R2, C2)** — read-only, deterministic, Markdown + JSON.
    $ python -m pytest tests/test_stop_report.py -q
    18 passed
Determinism and Markdown/JSON parity are two of those 18. **PASS**

Deviation recorded: S1's secondary accept was
`grep -c 'read_only=True' src/deepreason/application/stop_report.py >= 1`.
The module opens NO `Harness` at all — it reads durable sidecars and
delegates `--verify` to `invariants.verify_root`, which itself opens
`read_only=True` — so the string does not appear, and the grep would fail
while the property it stood for is strictly better satisfied. The
property is proven directly by S2 instead, and by a map check asserting
`'Harness(' not in src`. Recorded, not silently dropped.

**S2 (R1)** — writes nothing into a root, proven on the real 1360-file
P-A1 root:
    files before/after: 1360 / 1360
    combined sha256 before: 775a1f021281f027b410e48c9608e344284d4a1350f1321451375eab377a814d
    combined sha256 after : 775a1f021281f027b410e48c9608e344284d4a1350f1321451375eab377a814d
    $ python -m pytest tests/test_stop_report.py -k writes_nothing -q
    1 passed, 17 deselected
**PASS**

**S3 (R2)** — a YAML is read only for the diff. Structural, by AST:
`test_a_run_config_yaml_is_read_only_when_one_is_passed` asserts the
`yaml` import is reachable from `_config_diff` and nothing else. The same
assertion is a `check:` line in `CON-configuration-stages.md` stage 1 and
in `SUB-application.md`. **PASS**

**S4 (R3)** — section 1 on the P-A1 root:
    gates restored: 6
    defender reasoning: omitted → provider default
    embedder: nomic-ai/nomic-embed-text-v1.5
**PASS**

**S5 (R4)** — section 2, the row that answers the operator's own example:
    | conjecturer#0 | conjecturer.turn.v6 | 20/20 | 20 | 0 | True |
**PASS**

**S6 (R5)** — section 3, P-A1 (41 RemoteDisconnected, one endpoint):
    ('conjecturer', 'ollama-glm-5.3', {'HTTPError': 1, 'RemoteDisconnected': 23})
    ('defender',    'ollama-glm-5.3', {'RemoteDisconnected': 18})
and the phase-1 429 root reports 48 `HTTP-429` with the provider message
`HTTP Error 429: Too Many Requests`. **PASS**

**S7 (R6-R11)** — four boxes, ranked, never asserting a defect. P-A1:
    ranked: ENVIRONMENT > HARNESS > CONFIGURATION > MODEL
The four box fixtures, the harness-negative and the
never-asserts-a-defect test all pass in the 18. **PASS**

**S8 (R9)** — the vindication rule:
    MODEL says "passed qualification 20/20": True
    CONFIGURATION ranked above MODEL:        True
**PASS**

**S9 (R7)** — the CONFIGURATION probes:
    notes "reasoning omitted → provider default": True
    notes "split protocol armed":                 True
**PASS**

**S10 (R12)** — section 5 on M1-H0:
    refusal:   STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY
    continue:  REFUSED
**PASS**

**S11 (R1)** — Markdown and JSON carry the same five sections:
    ['classification', 'continuability', 'pre_run_check',
     'provider_health', 'what_actually_ran']
**PASS**

**S12 (R27)** — rootless mode. Three source kinds resolve: `root`,
`root-no-log`, `home-no-root`. P-A2 epochs 1 and 2 report as
`root-no-log`; Phase-1 M3-C0 as a home. All three appear as PASS rows in
the regression below. **PASS**

**S13/S14 (R13-R15)** — the refusal:
    $ grep -c "stop-report" .claude/skills/dr-diagnose/SKILL.md   -> present
    $ grep -q "THE STOP, CLASSIFIED" ...                          -> the GATE
`dr-drive-harness` §5's table opens with the stop-report row, above
`run-status.json`. The operator's verbatim incident is in
`docs/ERRATA_EXECUTOR.md` X12 (see the R15/W5 note under "Assumptions").
**PASS**

**S15/S16 (R16, R17)** — `docs/map/CON-configuration-stages.md`, 163
lines, four stages each with its revealing command, seven traps stated
flatly. `docs_verify` runs its checks (they are in the 1326) and `--audit`
does not name it. **PASS**

**S17 (R23, C7)** — registered in `INDEX.md`; `SUB-application.md` carries
the new module's entry-point block and its check. `SUB-periphery.md`
checked and correctly NOT edited: it owns `mcp_server.py`, not `cli/`.
    $ python tools/docs_verify.py --links
    docs_verify --links: 0 dangling reference(s), 75 document(s)
**PASS**

**S18/S20 (R18, R19)** — the regression and the mutation proof:
    SHIPPED: 8/8 correct, 0 misfiled
    NAIVE:   1/8 correct, 7 misfiled
**PASS**

**S19 (R20)** — one unit fixture per box, gate-runnable, committed in
`tests/`: `test_configuration_box_ranks_first...`,
`test_environment_box_ranks_first_on_a_429_streak`,
`test_model_box_ranks_first_when_the_seat_failed_its_form_in_qualification`,
`test_harness_box_ranks_first_only_when_the_other_three_are_ruled_out`.
**PASS**

**S21 (R21)** — see "wheel smoke" below. **PASS**

**S22 (R22)** — see "Full gate". **PASS**

**S23 (R24)** — DELIVERY.md's reconciliation is the delivery phase's
output; the requirement sweep below is its input. **PASS (deferred to
delivery by design)**

**S24 (C3)** — `PARKED.md` exists with three entries; P1 and P2 each
carry a complete paste-ready prompt, P3 deliberately carries none (its
remedy would be an `authoring-skills` rule, and that skill's E1 tripwire
requires two instances; this is one). **PASS**

## Full gate

    $ python -m pytest tests/ -q -n 4
    4707 passed, 6 skipped in 1204.07s (0:20:04)

**0 failed. PASS.** Run on an otherwise idle box, never concurrently with
`docs_verify` (`dr-drive-harness` §5b).

## Record-behavior preservation

The change touches a READER of the record, so prior verdicts must be
unchanged. `verify_root` on one known-good and one defect-era root:

    run-9175f0ecb055e57455af3c50df153c5a    violations=0
    failed-epoch1-run-8e22d0431fd2b98d      violations=0

Unchanged. The report CALLS `verify_root` and edits nothing.

## Frozen-surface diff

    $ git diff --stat 7653b04393..HEAD -- \
        src/deepreason/capabilities/state.py src/deepreason/harness.py \
        src/deepreason/invariants.py src/deepreason/run_manifest.py \
        src/deepreason/qualification.py src/deepreason/verification/
    (empty)

Empty, as forecast. `tools/blast_radius.py` over every target agrees:
    "frozen_surface_contacts": []
    "frozen_adjacent_contacts": []
    "frozen_surface_verdict": "CLEAR"

## Map

    docs_verify:            75 documents, 1326 checks, 3 failed
    docs_verify --audit:    1 finding
    docs_verify --links:    0 dangling, 75 documents            PASS
    docs_verify --coverage: 7 seams swept, 20 without a Sweep: header,
                            2 findings
    docs_verify --stale:    56 documents worth re-reading

**The 3 failures and the 1 audit finding are RECORDED BASELINES, matched
by name against `docs/AUDIT_BASELINES.md` rather than by counting** — the
window prompt pre-authorizes recording known-not-yours baselines rather
than stopping on them:

  * `SEAM-llm-x-rules.md:54` — baselines line 67, a lost closing backtick;
    parked P3. It is also the single `--audit` finding, which that line
    says explicitly ("the single finding keeping `--audit` above zero").
  * `INV-frozen-surfaces.md:181` — baselines line 68, the census asserting
    zero committed `transport_failure` attempts when one exists; parked
    P-D3. Verified not ours: the single matching file is under
    `experiments/2026-08-26-pc2-rematch/retired-transport-timeout180-run-42ad288038dd606c/`,
    and this tranche commits no run root.
  * `CON-run-identity.md:211` — baselines line 90, a SHALLOW-clone-only
    git-history row.

None is in a document this tranche touched. The count fell 6 → 3 during
step 17: one of the three repaired WAS ours — see "new checks" below —
and two were cleared by `git fetch origin
claude/deepreason-p-s1-commitments-wowcib`, the remedy the baselines name
at line 83.

`--coverage`: 2 findings, both on seams this tranche does not touch
(`SEAM-schools-x-scratch.md`'s unnamed enforcement site, and seams with
no `Sweep:` header). Pre-existing; this change adds no seam.

`--stale`: 56 documents, advisory. Dismissed with reason, not silence —
none is stale BECAUSE of this tranche. `SUB-application.md` appears with
"9 commit(s) to owned files since a82872b38"; its `Verified-at:` is
deliberately NOT advanced, because this tranche did not re-run that
document's full `Verify:` line (five pytest files), and a false stamp is
worse than an honest one. `CON-configuration-stages.md` does not appear:
it is new, and its stamp names the commit its checks were run against.

**New checks added by this change:** four. Two in
`CON-configuration-stages.md` (the AST assertion that `yaml` is reachable
only from `_config_diff`; the assertion that the four attempt-trace
fields section 4 reads are present), one pinning
`"restored at run time from notice"`, one pinning
`"omitted → provider default"`; plus one in `SUB-application.md` asserting
the three public functions exist, that `Harness(` never appears in the
module, that the CLI dispatches `stop-report`, and running
`tests/test_stop_report.py`. Each would go red if the behaviour regressed.

**Record observables added:** NONE. The report is a pure reader; it adds
no field, record type or finding to the typed record, so no sweep probe
is owed. This is the reason SPEC.md's A1 could answer Q2 without a
frozen-surface stop.

**wheel smoke:**
    $ python scripts/wheel_smoke.py
    wheel smoke passed: isolated V6-only contents, clean imports, exact
    entry points, module parity, MCP registration, and exact MCP schemas
    rc 0
No pin moved: the pinned surface is console-script entry-point NAMES, the
MCP tool set and the MCP schema sha; this tranche adds a SUBCOMMAND and no
MCP tool. Verified by running, not assumed.

    $ python -u scripts/wheel_operational_smoke.py
    rc 1, "stage": "continuation_resume", "failure_kind": "assertion_failed"
**NOT OURS, measured.** The same smoke in a clean worktree at the tranche
base `7653b04393` fails identically. Envelope committed at
`proof/wheel_operational_base_failure.json`. Parked as P2; not a FAIL of
this change.

## Requirement sweep

| R | demonstrated by |
|---|---|
| R1 | S1, S2, S11 — one command, read-only, deterministic, Markdown + JSON |
| R2 | S3 — every line from the record; the YAML reachable only from `_config_diff` |
| R3 | S4 — 6 restored gates, `omitted → provider default`, embedder named |
| R4 | S5 — per seat × form rows; cached qualification names its subject digest (rootless test) |
| R5 | S6 — attempts, faults by kind, zero-token returns, last fault, 429 message |
| R6 | S7 — four boxes with evidence for and against, ranked |
| R7 | S9 — notice-restored fields, YAML diff, reasoning probe, split probe |
| R8 | S6 + regression rows for P-A2 epoch 2 and the phase-1 429 root |
| R9 | S8 — the attempt ladder beside that seat's row, and the 20/20 sentence |
| R10 | S7 — HARNESS supported only with the other three RULED OUT (P-A2 epoch 3) |
| R11 | S1 — `test_report_never_asserts_a_defect` |
| R12 | S10 — state, stop_reason, refusal, verify_root summary, continue verdict |
| R13 | S13/S14 — both skills amended |
| R14 | S13 — the GATE `grep -q "THE STOP, CLASSIFIED" DIAGNOSIS.md` and the outlet table |
| R15 | S13 — written per `authoring-skills`; the incident quoted in ERRATA_EXECUTOR X12 (see A7) |
| R16 | S15 — `CON-configuration-stages.md` with re-runnable `check:` lines |
| R17 | S16 — the traps, all seven |
| R18 | S18 — 8/8, including the three rootless cases and the vindication case |
| R19 | S20 — NAIVE 1/8 RED vs SHIPPED 8/8 GREEN |
| R20 | S19 — one committed unit fixture per box |
| R21 | S21 — both smokes run; no pin moved |
| R22 | Full gate 4707 passed, 0 failed; baselines recorded by name |
| R23 | S23 — reconciliation is DELIVERY.md's output |
| R24 | R25 discharged before the first commit; scan re-run clean |
| R25 | credential scan: zero hits over tracked files |
| R26 | S12 + `deepreason stop-report --help` — a new subcommand, `results` unedited |
| R27 | S12 — rootless mode, three source kinds |
| R28 | two commit groups; one DELIVERY.md reconciles all |
| R29 | diff_budget 1905 WITHIN the raised 2100 ceiling |

Note on R24/R25 numbering: REQUEST.md's R24 is the DELIVERY reconciliation
and R25 the credential scan; the table above lists them in that order.

## Assumptions carried

- **A1 (Q2)** — no new record kind was needed. Confirmed: every section
  reads fields that already exist; no frozen-surface contact.
- **A2 (Q3)** — nothing writes into a root. Proven by S2, not assumed.
- **A3** — report logic in `application/`, CLI thin. Forced by an existing
  architecture test, and that test passes.
- **A4** — the stored `verify_root` verdict by default, re-derived only on
  `--verify`. Operator may override.
- **A5** — "deterministic" means byte-identical output for the same root
  and flags; the report carries no timestamp of its own.
- **A6** — R18's "39 RemoteDisconnected" is bound at the instrument's
  number, **41**, with "one endpoint" confirmed.
- **A7 (new, raised during execution)** — R15 ("the incident is quoted")
  and `authoring-skills` W5 ("delete the story; history lives in ERRATA")
  conflict. Resolved by splitting rather than by picking a side: the rule
  and its GATE are in `dr-diagnose/SKILL.md`, the operator's verbatim
  words are in `docs/ERRATA_EXECUTOR.md` X12 — the ledger whose own stated
  scope is `.claude/skills/`. Operator may override.
- **A8 (new)** — three of R18's six named roots do not exist as run roots,
  and a fourth is miscast. Delivered the PROPERTY (every box demonstrated
  on committed evidence) rather than the literal naming; reconciled in
  SPEC.md's "THE MATERIAL CONTRADICTION" and parked as P3.

## Verdict: PASS

Full gate 0 failed; every acceptance check green; frozen-surface diff
empty and the gate CLEAR; the map's three failures and one audit finding
matched by name to recorded baselines in documents this tranche did not
touch; the one map failure that WAS ours — consuming
`LLMAttempt.natural_stop`, which the seats/evidence law forbids — found by
the gate and fixed before commit, with
`tests/test_seats_evidence_law.py` green and all 8 regression cases still
landing correctly.
