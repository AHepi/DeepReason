# Validation for: Rung D — proof debt (E-1) delivered, Duhem localization (E-2) parked

Scope note, first, because it decides how every row below is read: the operator
ruled **option B** at the step-13 diff-budget STOP — deliver D1, park D2
(REQUEST.md Amendment 1, R20). So this validates the D1 half and records the D2
half as deferred with the operator's words, never as passed.

Tranche base for every diff: `b10fc5fd2` (the merge of `origin/main` into this
branch). All checks re-run here from the assembled tree, not quoted from the
steps that first ran them.

## Acceptance checks

| item | command | output | verdict |
|---|---|---|---|
| **S1** | `python -c "...len(CLAIM_SCHEMAS)==9 and 'poietic.derivation-manifest.v1' in _IMPLEMENTED"` | `S1 ok` | **PASS** |
| **S2** | `pytest ...::test_open_certificates_are_dependences_and_the_subject_is_a_mention` | `1 passed in 0.06s` | **PASS** |
| **S3** | `python -c "...PROGRAMS['derivation_manifest_wf'].class_=='structural'"` | `S3 ok` | **PASS** |
| **S4** | `pytest tests/test_proof_debt.py -q` | `18 passed in 1.31s` | **PASS** |
| **S5** | `pytest ...::test_a_receipt_is_recomputed_from_the_log_and_never_stored ...::test_a_receipt_reruns_its_kernel_checks_rather_than_reading_them_back` | `2 passed in 0.22s` | **PASS** |
| **S6** | `pytest ...::test_the_log_replays_identically_after_a_certificate_is_attacked` | `1 passed in 0.18s` | **PASS** |
| **S7** | `pytest ...::test_dependents_are_invalidated_on_recomputation_not_retroactively` | `1 passed in 0.20s` | **PASS** |
| **S8** | `pytest ...::test_a_manifest_is_wired_to_the_validity_node_as_evidence` | `1 passed in 0.16s` | **PASS** |
| **S9** | `pytest ...::test_attacking_a_manifest_item_disables_the_attack_before_pass_one` | `1 passed in 0.19s` | **PASS** |
| **S10** | `pytest tests/test_premise_channel.py ...::test_the_rent_sweep_files_a_manifest_whose_sample_is_attackable` | `26 passed in 1.79s` | **PASS** |
| **S11** | `git diff --stat b10fc5fd2..HEAD -- src/deepreason/` + the five-file consumer ring | 8 files, `457 insertions(+), 4 deletions(-)`; ring `51 passed, 1 skipped in 6.48s` | **PASS** |
| **S12–S19** | — | **DEFERRED** (operator: *"option B — deliver D1 now, park D2"*) | **DEFERRED** |
| **S20** (D1 half) | `pytest ...::test_filing_a_manifest_moves_no_label ...::test_the_read_path_holds_no_call_that_could_write` | `2 passed in 0.11s` | **PASS** |
| **S20** (localization half) | — | **DEFERRED** with S12–S19 | **DEFERRED** |
| **S21** | mutation proof | **DEFERRED** — its subject `implicated()` does not exist. A mutation proof with no subject is the vacuous check `--audit` exists to refuse | **DEFERRED** |
| **S22** | `python tools/docs_verify.py` + the Rung D axiom rows | `docs_verify: 3 failed` (all pre-existing); rows present and scoped to what D1 proves | **PASS** |
| **S23** | `docs_verify` full + `--links` | `3 failed` (pre-existing) / `0 dangling reference(s), 63 document(s)` | **PASS** |
| **S24** | DELIVERY.md with the R-by-R table | produced by `dr-deliver-change` | **PASS** |

**S11's four deletions, inspected line by line** so "457 insertions, 4
deletions" is not taken on trust:

    -# The three with a producer. The rest are declared above and refused below,
    -from deepreason.ontology import Commitment, Interface, Ref, Status
    -from deepreason.ontology import Artifact, Interface, Provenance, Rule, Warrant, WarrantType
    -    (None when skip_if_on_record and the verdict is already on the graph)."""

One comment reworded, two import lines extended, one docstring line extended.
No behaviour was removed anywhere in the tranche.

## Full gate

    $ python -m pytest tests/ -q -n 4
    3875 passed, 6 skipped in 764.14s (0:12:44)
    [exited with code 0]

**PASS — 0 failed.** Baseline in REQUEST.md C4 was 3857 at main `67cc732fd`;
the delta of +18 is exactly `tests/test_proof_debt.py`. Run on an otherwise
idle box with every background instrument stopped first (CLAUDE.md's
one-instrument-at-a-time rule). None of the 5 MCP-thread tests C4 flagged flaky
under `-n 4` flaked, across two independent full-gate runs this session
(956s at the D1 boundary, 764s here).

## Record-behavior preservation

**n/a, and mechanically proven so.** The change touched no reader or validator
of the append-only record — the frozen-surface diff below is empty, which
includes `invariants.py` and the whole `verification/` surface. No committed
root's verdict can move, because no code that reads a root changed.

## Frozen-surface diff

    $ git diff --stat b10fc5fd2..HEAD -- \
        src/deepreason/capabilities/state.py src/deepreason/harness.py \
        src/deepreason/invariants.py src/deepreason/run_manifest.py \
        src/deepreason/qualification.py
    (no output)

**PASS — empty**, as SPEC.md's forecast predicted and as `blast_radius.py`
computed at spec time (`frozen_surface_verdict: CLEAR`, `frozen_surface_contacts: []`).
No grant was requested and none was needed.

## Map

| check | result | verdict |
|---|---|---|
| `docs_verify` | `63 documents, 3 failed` | **PASS** — all 3 are C4's pre-existing shallow-clone failures (`CON-run-identity.md:200/202/204`), `git log` lookups of commits this clone does not carry. 0 new |
| `docs_verify --audit` | `0 finding(s)` | **PASS** — no check added by this change is vacuous |
| `docs_verify --links` | `0 dangling reference(s), 63 document(s)` | **PASS** |
| `docs_verify --coverage` | `7 seam(s) swept, 16 without a Sweep: header, 2 finding(s)` | **PASS — proven pre-existing.** Checked out `b10fc5fd2` and re-ran: byte-identical result (`7 swept, 16 without, 2 findings`). Neither finding names a file this change touched |
| `docs_verify --stale` | `3 document(s) worth re-reading` | **PASS** — see below |

**`--stale`, entry by entry** (the skill forbids silence about any of them):

- `SEAM-evaluation-x-rules.md` — **was listed, now UPDATED.** It owns
  `rules/warrants.py` and `programs.py`, both changed. Routed back to
  `dr-execute-step` as step 28 rather than patched during validation, and it
  gained the paragraph its stamp would otherwise have vouched for (the fourth
  in-function import, and why it is in-function). Stamp advanced to `6721010d`
  only after its checks were re-run.
- `SUB-evaluation.md` — **was listed, now UPDATED.** Its `programs.evaluate`
  caller pin was edited at step 6 without the stamp advancing. Same step 28.
- `SEAM-evaluation-x-ontology.md` — not listed by the tool, but its dispatch-set
  pin was edited at step 6, so its stamp was advanced in step 28 too. Recorded
  because relying on the tool to notice would have left a false stamp.
- `CON-run-identity.md` — **DISMISSED, pre-existing.** Names `bce018ae5`
  ("all-configs-allowed"), a commit from another tranche. Untouched here.
- `SEAM-llm-x-scheduler.md`, `SUB-scheduler.md` — **DISMISSED, pre-existing.**
  Both name `8469d0669` (the route-lease/`max_tokens` fix), another tranche.
  This change went nowhere near `llm/` or the scheduler — C3's own STOP
  condition, never triggered.

**New checks added by this change:** 15 `check:` lines across five documents —
`CON-proof-debt-and-localization.md` (new), `CON-warrants-and-attacks.md`,
`CON-problem-layer-lifecycle.md`, `INV-axiom-basis.md`, `SUB-calculus.md` —
plus the two exact-set pins updated in `SEAM-evaluation-x-ontology.md` and
`SUB-evaluation.md`. Every one was RUN before being written down. Two deserve
naming because they guard against future drift rather than present behaviour:

- `assert importlib.util.find_spec('deepreason.localization') is None` — the
  parked half's own tripwire. If a future window builds the module without
  updating the document, the document FAILS rather than lies.
- `assert KernelCheckV1 not in _MODELS.values() and len(CLAIM_SCHEMAS) == 9` —
  a body's internal part must never become a decodable claim, which is how the
  closed set would be widened by the back door.

**Record observables added vs sweep probes:** none added. The manifest and the
sample certificate are ordinary artifacts — not a new record type, event kind,
or field on a typed record — so there is no new observable for a probe to look
at. The root sweep is retired as an instrument (operator ruling 2026-08-22),
and SPEC.md's "Record-observable guardrails" section recorded this before any
code was written.

**Wheel smoke:** packaging surface untouched — smoke not owed. Proven, not
assumed:

    $ git diff --stat b10fc5fd2..HEAD -- pyproject.toml \
        src/deepreason/mcp_server.py src/deepreason/cli/main.py scripts/
    (no output)

`blast_radius.py` agrees: `wheel_smoke_pins: []`, `qualification_digest: []`.

## Requirement sweep

| R | disposition |
|---|---|
| **R1** route through `dr-change-orchestrator`, workflow's stops apply | **DEMONSTRATED** — capture → spec → plan → 28 executed steps → this validation. The workflow's own stop fired at step 13 and was honoured, not outrun |
| **R2** the spec phase owns the design | **DEMONSTRATED** — SPEC.md §0–§5 answer all six open questions with measurements; the ladder's outline is quoted, never extended |
| **R3** authority is LADDER.md "Rung D" in full plus its sources | **DEMONSTRATED** — REQUEST.md quotes the section, the E-1/E-2 reconciliation rows, and R58, verbatim |
| **R4** receipt format `KERNEL_CHECK / OPEN_CERTIFICATES / AXIOM_DEBT`, itemized and attackable, dependents invalidated on recomputation | **DEMONSTRATED** by S1, S2, S4, S5, S7 |
| **R5** the scope question answered in SPEC.md with reasons | **DEMONSTRATED** — SPEC.md §1's table rules out render decisions, labels and measures each with its reason; A1 records it as overridable |
| **R6** start narrow | **DEMONSTRATED** — one producer (`premise_rent_sweep`); every other `register_fail_warrant` site byte-unchanged (S11) |
| **R7** localization channel | **DEFERRED** (operator: *"option B — deliver D1 now, park D2"*) → PARKED.md P1 |
| **R8** reuse `premises.py`'s shape | **DEFERRED** with R7; carried verbatim into PARKED.md's prompt as constraint (a), per R23 |
| **R9** blame never automatic | **DEFERRED** with R7; carried verbatim into PARKED.md's prompt as constraint (b), per R23 |
| **R10** receipts recompute from the log, derived never stored | **DEMONSTRATED** by S5, S6, S7 |
| **R11** a localization's defeat un-implicates the member | **DEFERRED** with R7 |
| **R12** no label moves from a receipt or localization alone | **HALF DEMONSTRATED** by S20's D1 half (behavioural + the AST guard that the read path holds no writing call and the module never imports `adjudication`); the localization half **DEFERRED** with R7 |
| **R13** mutation proof on the non-automatic constraint | **DEFERRED** with R7; carried verbatim into PARKED.md's prompt as constraint (c), per R23. Explicitly NOT run: its subject does not exist, and a mutation proof with no subject proves nothing |
| **R14** axiom ledger per LADDER.md §5b | **DEMONSTRATED** by S22 — and scoped honestly: PROVES `A1`/`A2` in the receipt's form; PRESERVES `A3`, `A5` at the manifest, `A9`, `A10`, `Ax 4.1`; does NOT answer for `A5` at the localization, and the `A5` row says so |
| **R15** frozen surfaces: none beyond `Config` knobs | **DEMONSTRATED** — empty frozen diff; and no `Config` knob was added at all, so no `_versioned_source_config_data` line is owed (SPEC.md A5 recorded that as a decision, not an omission) |
| **R16** ledger a ceiling, STOP if exceeded | **DEMONSTRATED** — ceiling 1480 ledgered at plan time, checked at every commit, and it DID fire: the step-13 STOP is the requirement working |
| **R17** if both cannot fit, deliver D2 and park D1 | **SUPERSEDED by R20** — recorded in REQUEST.md Amendment 1 with the reason (it presupposed the conflict surfacing before either half was written) |
| **R18** ring / full gate / docs_verify / map in same commits / push each boundary | **DEMONSTRATED** — 12 commits, each pushed; map moved in the same commit every time; two full gates and full `docs_verify` |
| **R19** deliver R-by-R with pasted proof and two closing lines | **PASS pending** `dr-deliver-change` (S24) |
| **R20** option B | **DEMONSTRATED** — this document |
| **R21** step-2 pre-registration stands; one tranche, one goal | **DEMONSTRATED** — the ceiling was not raised |
| **R22** close out D1 through validate and deliver as-is | **DEMONSTRATED** — this document; no D1 code was touched after the ruling |
| **R23** park prompt inherits SPEC §D2, the `premises.py` shape, and the mutation-proof requirement | **DEMONSTRATED** — PARKED.md P1's prompt carries all three as named constraints (a), (b), (c) |
| **R24** a future window starts at `dr-plan-steps`, not re-spec | **DEMONSTRATED** — the prompt says so in its first paragraph and names SPEC.md §D2 as the spec, with "your first artifact is CHECKLIST.md, not SPEC.md" |
| **C1** `python -m pytest`, never bare | **HELD** — every pasted command uses it |
| **C2** read CLAUDE.md; load `dr-drive-harness`, `dr-explain-to-operator` | **HELD** |
| **C3** blast radius; STOP if editing `llm/` or provider profiles | **HELD** — `git diff --stat b10fc5fd2..HEAD -- src/deepreason/llm/` is empty; the STOP never needed to fire |
| **C4** known baselines | **HELD** — 3 pre-existing `docs_verify` failures confirmed; gate delta +18 accounted for; no MCP flake |
| **C5** parallel windows | **HELD** — no shared file touched |
| **C6** branch discrepancy | **HELD** — worked on `claude/calculus-rungd-debt-localization-6c3u9w` throughout, as REQUEST.md recorded |

## Assumptions carried

- **A1** — receipt scope is attack-producing derived judgments only. Operator may override.
- **A2** — the manifest is a registered artifact; the receipt is the derived view. Operator may override.
- **A3** — a bundle is an artifact that depends on its members. **Untested in code**: it is the parked half's premise, so it carries into PARKED.md unproven and should be re-read there rather than assumed settled.
- **A4** — the ceiling was 1480. It was reached; the operator ruled rather than the number deciding.
- **A5** — no `Config` knob added, so no `_versioned_source_config_data` line owed.
- **A6** — D2 ships with no CLI/MCP/scheduler reader. Now moot for D2 (parked); still true of D1, whose `receipt()` has no reader surface either. **Recorded as residue**: proof debt is reachable from code and tests, not from the CLI. That is a known absence, and the honest reading is that `receipt()`'s only consumer today is the gate.

## Residue — what remains unproven

Stated because "accepted does not mean true", and a green gate is not a claim
about the world:

1. **No live run exercised any of this.** Every proof is offline, against
   fixtures. The rent sweep's new certificate path has never run against a real
   provider, and a live run could still surface an interaction the gate cannot.
2. **`receipt()` has no reader.** Nothing in the CLI, the MCP surface, or the
   scheduler calls it. It is exercised by tests and by nothing else, which is
   one step short of `docs/ERRATA.md` E28's pattern — the producer half is
   live (the rent sweep files bills on every sampled verdict), the consumer
   half is not.
3. **The automatic-projection guard does not exist.** Because bundle membership
   is readable off `dep`, the tempting version is one line away and nothing in
   the tree stops it. Recorded in the concept document's Traps as a warning to
   a future author, not as a live protection.
4. **One estimate in SPEC.md was wrong by 87%** (280 → 524 lines for one test
   file). The ceiling caught it, but only at the D1 boundary; a per-property
   estimate rather than a line-count estimate would have caught it at plan
   time, and PARKED.md's prompt says so to the resuming window.

## Verdict: **PASS**

Every D1 acceptance check passes, the full gate is 0 failed, the frozen-surface
diff is empty, and every requirement is either demonstrated by a pasted output
or deferred with the operator's own words. No D2 item is recorded as passed.
