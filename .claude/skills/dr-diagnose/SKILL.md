---
name: dr-diagnose
description: Locate the cause of a DeepReason defect from the typed record, not from code reading. Produces DIAGNOSIS.md naming one primary cause with evidence pointers. Use only after GOAL.md exists.
---

# Diagnose from the record

Input: GOAL.md. Output: DIAGNOSIS.md naming ONE primary cause. You
read the record first and the code second. You change nothing.

## Step 1 — run the stop report, and open DIAGNOSIS.md with it

Run this before reading any code, any log, and any run-config file:

    deepreason stop-report <root-or-home>

Paste its section 4 (`THE STOP, CLASSIFIED`) verbatim as the FIRST
section of DIAGNOSIS.md, before writing anything of your own. Cite a
report line by section number for every claim naming a defect, a seat, or
a model as the cause.

GATE, run before you commit DIAGNOSIS.md:

    grep -q "THE STOP, CLASSIFIED" DIAGNOSIS.md

Exit 0 = pass. Exit 1 = the phase is `not-done`; STOP and report that.

The report accepts three source kinds, so a run that never opened a log
still has one: a run root, a run directory that compiled a manifest and
failed its qualification gate (`root-no-log`), and a home whose
qualification is cached (`home-no-root`).

When the failure has no run root and no home at all — a smoke harness, a
build, a tool — write one line in DIAGNOSIS.md naming which of the three
kinds was absent, and paste that instrument's own typed failure envelope
in place of section 4. The GATE above still applies to everything else.

Outlets, one per prohibition:

| You cannot... | Then |
|---|---|
| produce the report | STOP; report `not-done` with the command's stderr |
| cite a report line for a cause | PARK the hypothesis; diagnose what you can cite |
| find any typed source | paste the instrument's failure envelope, and say which kind was absent |

This displaces the old ordering, in which `run-status.json` and
`REPLAY_VALIDATION.json` were rows 1 and 4 of "Where the truth lives"
and each reader re-derived them by hand. The report derives all of it,
plus the qualification rows and provider health that hand-reading
skipped. Those rows below are now the DEEPER DIVE, entered after the
report names a box.

## Read the map's Traps SECOND — it is cheaper than the record

After the report names a box, read the `Traps` section of the map document
covering the suspect subsystem (`docs/map/SUB-*.md`, `CON-*.md`,
`SEAM-*.md`). Traps are the accumulated memory of what has actually
gone wrong there, and a recurrence is the cheapest diagnosis available.

This costs one file read and can end the phase. It is not a substitute
for the record: the record still decides, and a trap that merely LOOKS
like your symptom is a hypothesis to test against the blob, not an
answer. But a defect matching a recorded trap is the single most likely
explanation, and checking is nearly free.

If the diagnosis turns out to be a NEW failure mode, `dr-implement-fix`
will add it to that document's Traps as part of the fix commit.

## Where the truth lives — the deeper dive

Enter this after the stop report names a box, to establish the mechanism
the box only points at. For a failed or suspect run root `<root>`:

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

    ## Stop report, section 4 (pasted verbatim, before anything of mine)
    <the output of `deepreason stop-report <root-or-home>`, section 4>

    Primary cause: <mechanism, one paragraph max; every clause naming a
      defect, a seat, or a model cites a report line above>
    Evidence:
      - <record pointer: file/seq/object id> -> <what it shows>
      - <repeat; minimum 2 pointers, at least 1 non-code>
    Implicated code: <file:line, max 3 sites>
    Falsifiable prediction: <what dr-reproduce must show if this
      diagnosis is right, as a command + expected observation>
    Ruled out: <the one alternative you checked and why it fails>

## Exit criteria

- `grep -q "THE STOP, CLASSIFIED" DIAGNOSIS.md` exits 0.
- Every cause naming a defect, a seat, or a model cites a report line.
- DIAGNOSIS.md committed and pushed; PARKED.md updated if applicable.
- No code modified. No fix sketched beyond the mechanism name.
- Return to the orchestrator.
