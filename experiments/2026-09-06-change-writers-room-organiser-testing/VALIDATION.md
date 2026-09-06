# Validation for: the organiser seat — testing the writer's room on the full harness
Tranche base `d3f047932`; validated head: the commit that adds this file. Every
acceptance check in SPEC.md re-run on the assembled whole, in item order,
outputs pasted (the full listing is the same run's transcript, kept in the
checklist's step outputs where it is long).

## Acceptance checks

S1: four shells resolve — `('seat.conjecturer.legacy-v0', 'seat.conjecturer.organiser-v1', 'seat.critic.evidence-blind-v1', 'seat.critic.legacy-v0')`; the organiser pairs `conjecturer.turn.v6` / `seat-pack.conjecturer.organiser-v1` / `role-prompt.organiser-v1`; the blind critic keeps `argumentative_critic.compact.v1`; goldens + role-prompt registry: part of the full gate below and the step-4 ring (`167 passed`) : PASS
S2: `bash -n` ×5 silent; `env-line-count=1`; `selector ok`; ARM H binds no selector — SPEC's literal grep `! grep -q DEEPREASON_SEAT_SHELL runs/armH.sh` FAILS because armH.sh deliberately `unset`s the variable as a guard; the property (no shell bound) holds: `! grep -q 'DEEPREASON_SEAT_SHELL=' runs/armH.sh` → `armH binds no selector (it unsets the variable as a guard)` : PASS (accept refined to the property; recorded)
S3: `records 94 (12 conjectures, 46 proposals, 36 objections)` / `verbatim 94/94` (CHECKLIST step 1) : PASS
S4: `sha256sum -c` → `01-conjectures.txt: OK / 02-proposals.txt: OK / 03-objections.txt: OK / CONVERSION.json: OK`; `git ls-files attachment | wc -l` → 5 : PASS
S5: `sources 3 blocks 94 refusals 0` / `legend shown 32 withheld 62` / `frozen pack sources 3 excluded 0` (`proof/DRY_ATTACH.txt`) : PASS
S6: `PACK_TOKEN_BUDGET: 24000`; `BEGIN UNTRUSTED SOURCE DATA` ×3; receipts `[('frozen-evidence-context', 'rendered'), ('citable-evidence-blocks', 'rendered')]`; `## P2` present : PASS
S7: `form ok` (the v6 reasoning turn's candidate is `ReasoningCandidateProposal`); `grep -c compact.v2 seat_layouts.py` → 2 : PASS
S8: `load_operator_plugins(` call sites in src → 1 (unchanged); `## P1` present : PASS
S9: `ORGANISE, DO NOT INVENT=1`, `refuted if not=1`, `uncertainties=2`, `0.5=42`; `COMPLEMENT DIRECTIVE=0`, `DIVERSITY SPECIFICATIONS=0`, `Include atypical candidates=0` : PASS
S10: `12 12`; `12 of 12` in RESULTS.md : PASS
S11: `91795` bytes; brief commit `8528b3a62` precedes PREREG commit `0d50134a5` (`git merge-base --is-ancestor` → `brief precedes prereg`) : PASS
S12: `tests/test_organiser_seat.py` → `12 passed` (step 6; in the full gate below) : PASS
S13: `## P3` present; `continue` count in armR.sh → 0 : PASS
S14: `blind ok`; `## P4` present : PASS
S15: PREREG commit body carries `sha256: 3d51b88eec4ada2dec51cad6ba63c8f73ac612043cc2c47897b217012feae4c0`; `sha256sum PREREG.md` → the same : PASS
S16: `self-test: 43 surviving, 0 refuted, 53423 chars, seed positions 43`; `judge help ok`; `CRITERIA identical` : PASS
S17: transport-word grep in `compose_result.py` → 0 : PASS
S18: keymap in the judge, quintile (the stated reason it is not run) in the analyser : PASS
S19: `MATERIALLY BETTER` in PREREG.md → 2 : PASS
S20: `chain ok`; `runs/soak.log` ends `[soak] exit 0 (clean)` / `rc=0` : PASS
S21: `env ignored`; `no key committed` : PASS
S22: `Failure budget` in RESULTS.md → 1 (spent 0) : PASS
S23: `no credential` in DELIVERY.md; `not run` in RESULTS.md (both present in the delivery commit) : PASS
S24: `## 2026-09-06` in RESULTS.md → 1 : PASS
S25: this document; gate and map below : see verdict

## Full gate
`python -m pytest tests/ -q -n 4` (from the repository root; the first launch from the tranche directory collected nothing and was discarded) → `5106 passed, 6 skipped in 1218.39s (0:20:18)`, rc=0 — 0 failed : PASS

## Record-behavior preservation
n/a — no reader or validator of the append-only record changed (the diff is
three registration modules under `llm/`, one test file, one map document).

## Frozen-surface diff
    git diff --stat d3f047932..HEAD -- src/deepreason/capabilities/state.py src/deepreason/harness.py \
      src/deepreason/invariants.py src/deepreason/run_manifest.py src/deepreason/qualification.py \
      src/deepreason/verification/ src/deepreason/llm/firewall.py
→ empty (0 lines). Seven paths, per C1. Also empty for `mini/`, `src/deepreason/evidence/`, `src/deepreason/rules/`, `src/deepreason/admission/` (C2, C3).

## Packaging surface
untouched — no CLI, MCP, entry-point or wheel-layout change; smoke not owed.

## Map
docs_verify (full): 82 documents, 1426 checks, **6 failed** — all six are the recorded baseline on this container's SHALLOW clone (`docs/AUDIT_BASELINES.md`: "5 OR 6 failed"): `SEAM-llm-x-rules.md:54` (malformed check, parked P3 of the multiline-checks fix), `INV-frozen-surfaces.md:206` (the transport_failure census, parked P-D3; the line moved from 181 as the document grew), `CON-run-identity.md:211/213/215` (three git-history rows that need commits a shallow clone lacks; `git rev-parse --is-shallow-repository` → `true`), `INV-frozen-surfaces.md:876` (the judge-canary row reads a branch this container has not fetched). Zero failures in any document this tranche touched; the new `INV-seat-section-plugins.md` checks ran and passed : PASS (baseline)
docs_verify --audit: 1 finding (`SEAM-llm-x-rules.md:54`, baseline) : PASS (baseline)
docs_verify --links: 0 dangling, 82 documents : PASS
docs_verify --coverage: 7 seams swept, 22 without a Sweep header, 2 findings (`SEAM-schools-x-scratch.md` enforcement site; `SEAM-scratch-x-workflow.md` no Sweep header) — both pre-existing, neither document touched : PASS (baseline)
docs_verify --stale: 25 documents listed. `INV-seat-section-plugins.md` — UPDATED (stamp advanced to `8946abeec` after the full run executed its checks). `SUB-llm.md` and `CON-packs-and-token-economy.md` list this tranche's commit among others: DISMISSED — neither makes a claim the four-shell registration falsifies (grep for shell counts finds none; their checks passed in the full run), and their stamps are not advanced because their other listed commits are not this tranche's to vouch for. The remaining 22 predate this tranche and are dismissed for the same reason: not touched here, their checks passed.
new checks added by this change: `INV-seat-section-plugins.md` — one multi-line `check:` (the organiser pairs `turn.v6` with the organiser layout; the blind critic layout is the legacy minus two; the defaults unmoved) and one `check: python -m pytest tests/test_organiser_seat.py -q`.
record observables added vs sweep probes: none — no new field, record kind or finding; the section plan already records the plugin ids the organiser layout renders.
wheel smoke: packaging surface untouched — smoke not owed.

## Requirement sweep
R1: demonstrated by S1, S7, S9, S12 — the organiser pairing renders the room whole and its candidates admit with commitments.
R2: sealed and ready (S15, S16, S2), NOT RUN — deferred under R23 (operator's brief: "If no key is present, deliver moves 1–2 and the sealed PREREG without the runs, and say so").
R3: S3. R4: S4. R5: S5. R6: S6 (the configurable half set; the code half parked P2, disclosed).
R7: S7 (A1 recorded). R8: S8 (registered in `seat_layouts.py`, said so; P1). R9: S9. R10: S10. R11: S11. R12: S12.
R13: S13 (decided: whole run; P3). R14: S14 (blind critic on ARM R; P4).
R15: S15. R16: S16 and S2 (scripts ready; arms not run — R23). R17: S16/S17. R18: S18. R19: S19.
R20: S20 (soak green; launch discipline in chain.sh — not exercised live, R23). R21: S21. R22: S22 (spent 0).
R23: S23. R24: S24. R25: this document and DELIVERY.md.

## Assumptions carried
A1: the organiser pairs `conjecturer.turn.v6`, the form the managed conjecturer fills; the brief's `compact.v2` does not reach that path.
A2: registered in code (`seat_layouts.py`, `seat_plugins.py`, `role_prompts.py`); the operator plugin directory is mini-only (P1).
A3: three files; ordering steers nothing (Amendment 1); `PACK_TOKEN_BUDGET: 24000` in BOTH arms' config.
A4: `VS_K` stays 6; the organiser carries ≤ 6 per turn.
A5: whole-run organiser; cycle-scoped pairing parked (P3).
A6: the judged unit is `compose_result.py`'s deterministic composition of the seed problem's positions.
A7: `epoch3` is the soak case; it proves the shape, not the shell.
A8: no key on this container; the arms did not run.
A9: cycles 4, token budget 800 000 per harness arm.
A10: labels stay inside the verbatim bodies; the header carries kind and label separately (a comma in a header label is folded to `;`).
A11: the organiser wording moves the conjecturer's prose alone.
Amendment 2: the diff-budget ceiling raised 450 → 800 (fixture copy removed; the twelve-proof test file kept whole).

## Verdict: PASS
