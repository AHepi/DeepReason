# Goal: make the repair `mode` vocabulary one shared type, so a value the producer can emit is never a value the checker rejects

Class: defect

Observed: the repair-turn producer's `mode` field
(`src/deepreason/llm/repair.py:1505`, `V6RepairTurn.mode`) is typed
`Literal["initial", "whole_object_syntax", "patch"]`, while the recovery
authority that reads the same value off a `repair.semantic-task.v1` payload
(`src/deepreason/workflow/nonconjecture_recovery.py:1002`) admits
`{"patch", "full"}`; the two vocabularies intersect in `patch` alone, so any
`whole_object_syntax` repair child that reaches a recovery path raises
`NonConjectureRecoveryAuthorityError("repair mode is invalid")` and kills the
run. Evidence, all committed:
`experiments/2026-08-28-audit-run-problems/AUDIT_REPORT.md` §F-D;
`experiments/2026-08-28-audit-run-problems/probes/q5_repair_vocabulary.py`
(exits 0 today, asserting both halves against live source and all three
records); `experiments/2026-08-28-audit-run-problems/probes/q5_repair_payloads.json`
(56 repair payloads across three roots: 36 `whole_object_syntax`, 20 `patch`,
0 `full`); branch `claude/spec-to-code-technique-k5209o`,
`failed-epoch5-run-456885c5.../run-result.json`, `error_type`
`NonConjectureRecoveryAuthorityError`, detail "repair mode is invalid".

Map preflight (ids resolved before design):
  DR-SEAM-llm-x-workflow  — owns `llm/adapter.py`, `workflow/repair_transaction.py`
                            (the seam that WRITES `mode` into the payload)
  DR-SEAM-rules-x-workflow — owns `workflow/nonconjecture_recovery.py`,
                            `workflow/atomic_recovery.py` (the READERS)
  DR-SEAM-scratch-x-workflow — co-owns `workflow/nonconjecture_recovery.py`
  DR-SUB-llm, DR-SUB-workflow — the two sides
  DR-INV-frozen-surfaces  — read before designing; NONE of the five frozen
                            surfaces (capabilities/state.py, harness.py,
                            invariants.py + verification/, run_manifest.py,
                            qualification.py; frozen-adjacent
                            `route_fingerprint` in llm/firewall.py) is in this
                            cone. `invariants.py:775` READS
                            `payload.get("mode") == "patch"` as a positive
                            filter, not as a vocabulary set, and is not
                            modified.

Success criterion (machine-decidable):
    (1) pytest tests/test_v6_repair_mode_vocabulary.py -q
        -> passes; the new regression test drives a whole_object_syntax
           repair child through `recover_atomic_child_output` and the child is
           admitted rather than raising
           NonConjectureRecoveryAuthorityError("repair mode is invalid"), and
           is mutation-proven (RED on the pre-fix checker set, GREEN after).
    (2) python -c "from deepreason.llm.repair import V6_REPAIR_TASK_MODES;
        from deepreason.workflow import nonconjecture_recovery as n;
        import inspect; assert 'V6_REPAIR_TASK_MODES' in
        inspect.getsource(n._repair_authority)"
        -> exits 0; the checker consumes the producer's type by import, not by
           a retyped literal set.
    (3) grep -rn '"full"' src/deepreason/workflow/nonconjecture_recovery.py
        -> no match; the value nothing emits is gone from the authority
           boundary.
    (4) python -u scripts/cycle_soak.py --case epoch3 --cycles 8
        --induce-repairs 2
        -> the D1-seat-contract seam reports `repairs` > 0 rather than the
           `partial` disposition whose reason is "the deterministic stub always
           returns a schema-valid response". NOTE, recorded at goal time rather
           than discovered late: the brief asked for a schema-invalid stub mode
           to be ADDED; `scripts/cycle_soak.py::install_repair_inducer` and its
           `--induce-repairs N` flag ALREADY EXIST on main (landed cfe8d111c,
           the P-C2 tranche). This criterion therefore VERIFIES the existing
           instrument reaches the repair path rather than building a second
           one; if it does not, building it is back in scope.
    (5) pytest tests/ -q -n 4
        -> 0 failed (baseline 4374 passed).
    (6) python tools/docs_verify.py
        -> failures <= baseline 4 (3 shallow-clone + 1 pre-existing falsified
           census at INV-frozen-surfaces.md:181); a delta beyond four is a
           finding.
    (7) experiments/2026-08-28-audit-run-problems/probes/q5_repair_vocabulary.py
        -> goes RED on the fixed tree (it asserts the DEFECT); its red output
           is recorded in VERIFY.md as the before/after instrument's expected
           inversion. Necessary but not sufficient — (1) is the proof.

In scope:
    src/deepreason/llm/repair.py            (the vocabulary's home)
    src/deepreason/workflow/nonconjecture_recovery.py + atomic_recovery.py
                                             (the readers)
    scripts/cycle_soak.py + tests + docs/map (the soak gap and the record)

NOT in scope: `src/deepreason/invariants.py:775` and any other positive
`mode == "patch"` filter — reading one member of the vocabulary is not owning
the vocabulary, and invariants.py is frozen surface 3. Also NOT in scope: the
parallel windows' cones — `llm/layout.py`, `llm/packs.py`, `llm/roles.py`,
`informal/trial.py` (render-layout); `run_manifest.py`, `preparation.py`
(P10); `premises.py`, `rules/crit.py` (P11).

Budget: <=150 changed lines of production code, phase-boundary commits,
one session.

Stop conditions inherited from orchestrator: yes
