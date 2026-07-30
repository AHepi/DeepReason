---
name: dr-diagnose
description: Locate the cause of a DeepReason defect from the typed record, not from code reading. Produces DIAGNOSIS.md naming one primary cause with evidence pointers. Use only after GOAL.md exists.
---

# Diagnose from the record

Input: GOAL.md. Output: DIAGNOSIS.md naming ONE primary cause. You
read the record first and the code second. You change nothing.

## Where the truth lives (in priority order)

For a failed or suspect run root `<root>`:

1. `<root>/run-status.json` — state, stop_reason, message. The message
   often IS the answer (e.g. a KeyError'd source id, a typed
   V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY).
2. Cycle heartbeats — which problem each cycle actually worked:

        python3 - <root> <<'PY'
        import sys; from pathlib import Path
        from deepreason.harness import Harness
        h = Harness(Path(sys.argv[1]), read_only=True)
        for e in h.log.read():
            ins = [str(v) for v in (e.inputs or [])]
            if ins and ins[0] == 'cycle':
                print(e.seq, 'cycle', ins[1], '->', ins[2])
        PY

3. Work attribution — join `objects/workflow-work-preparation-v1/*`
   (`task_payload_value.problem_ref`, `contract_id`,
   `formal_fence_seq`) with `objects/workflow-work-terminal-v1/*`
   (`work_id`, `status`, `reason_code`) and
   `objects/workflow-provider-attempt-v1/*` (`work_id`,
   `prompt_tokens`, `completion_tokens`, `raw_ref`). This tells you who
   spent every token and who got denied. A problem with ZERO provider
   attempts was never dispatched — that is a scheduler fact, not a
   model fact.
4. `REPLAY_VALIDATION.json` / `verify_root(<root>)` — violations with
   check names and seqs. Characterize a violation before explaining
   it: same set vs. permuted order vs. missing is three different bugs.
5. Raw model output — resolve a provider attempt's `raw_ref` in
   `<root>/blobs/<2-char>/<hash>`. `completion_tokens == cap` with
   empty text means reasoning burn, not a schema bug.
6. Capability chain — `harness.capability_state`: proposals,
   `current_transition_by_request`, transition lifecycle + reason_code.
   Denials name their gate.

Only after the record narrows the cause to a mechanism do you open the
implicated source file, and only that file plus at most two neighbors.

## Discipline

- Attribute, don't infer: "cycle 0 selected conn:X (seq 32)" beats any
  reading of `_select_problem`.
- When a prior attempt failed differently, diff the two records, not
  the two vibes.
- If you find a SECOND independent cause, put it in PARKED.md and
  continue with the primary (the one the success criterion needs).
- If the record contradicts GOAL.md's Observed line, stop and return
  to the orchestrator saying so.

## DIAGNOSIS.md template

    # Diagnosis: <one line naming the mechanism>
    Primary cause: <mechanism, one paragraph max>
    Evidence:
      - <record pointer: file/seq/object id> -> <what it shows>
      - <repeat; minimum 2 pointers, at least 1 non-code>
    Implicated code: <file:line, max 3 sites>
    Falsifiable prediction: <what dr-reproduce must show if this
      diagnosis is right, as a command + expected observation>
    Ruled out: <the one alternative you checked and why it fails>

## Exit criteria

- DIAGNOSIS.md committed and pushed; PARKED.md updated if applicable.
- No code modified. No fix sketched beyond the mechanism name.
- Return to the orchestrator.
