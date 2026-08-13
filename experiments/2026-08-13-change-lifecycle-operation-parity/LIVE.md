# LIVE.md — the parity proof on the REAL grounded-extension root

Satisfies R7 and R8 for the two credential-free stages. Every number is a
pasted typed outcome; nothing here is model prose. The third stage
(`continue`) is blocked and the block is stated, not glossed.

Subject: `experiments/2026-08-12-live-grounded-extension-expansion/run`
· `manifest_sha256 = 8e22d0431fd2b98dc915c66f2f3ccc6dc43184b4c326ff5d388a7c013a80989d`
· 9 947 events at the start · launched by `deepreason run --run-manifest`.

Driver: `live_parity.sh` in this directory, committed before it was run.

---

## Timeline (from `live_parity.log`)

    [12:56:45Z] === STAGE 1: finalize (appends only; no model call) ===
    [13:10:06Z] === STAGE 1: finalize (appends only; no model call) ===
    [13:10:39Z] FINALIZE rc=1 -- see finalize.stderr.log
    [13:31:00Z] FINALIZE OK rc=0 -- see finalize.json
    [13:31:00Z] === STAGE 2: amend, admitting the six bound documents ===
    [13:33:22Z] AMEND OK rc=0 -- see amend.json
    [13:33:22Z] === MEASURE: verify_root after the amendment epoch ===

The 13:10 line is a SECOND driver launched while the first still held the
root. Its refusal is evidence, not noise:

    FINALIZE_RUN_ACTIVE: another operator owns this run root

Two operators cannot terminalize one root at once, and the guard says so
typed rather than racing.

---

## Stage 1 — `finalize` (rc=0)

    authority               current_valid_committed
    terminal_status         completed
    terminal_epoch          0
    reasoning_event_horizon 9947
    terminal_commitment_ref sha256:8c414d5b9af96087e6769b5f2aadc43cb624ce53a7087d8f4ddf0c3312cb0d75
    stop                    {"reason": "budget_exhausted", "event_seq": 9947,
                             "metrics": {"cycle": 24, ...},
                             "digest": "a02da10aee3f9a431d569afd808b24e5458395ba34478035a3a194ecf2017d9b"}
    survivors               191
    frontier                87
    completion_status       incomplete
    canonical_bridge_eligible False
    verification finding_counts
                            {"integrity": 6, "security": 344,
                             "completion": 305, "epistemic": 0,
                             "operational": 8}

`survivors: 191` and the frontier head `013723d2dbc5` reproduce
`RESULTS.md`'s own reported numbers exactly — the frontier was re-derived
from the replayed record, not carried over from anywhere.

**`integrity: 6` is the six pre-existing `attached-evidence` violations,
unchanged.** Finalization introduced no new integrity finding, which is
what C5 required. The `security` (344) and `completion` (305) counts are
NOT new damage: `verify_root` returns only `violations`, which is the
integrity channel; the other channels have always existed and simply had
no terminal to be reported against until now. This is the first time the
run's full verification report has been derivable at all.

**`canonical_bridge_eligible: False` is correct and expected**: a bridge
requires a clean replay, and this root's six attached-evidence violations
are recorded history.

---

## Stage 2 — `amend` (rc=0, 2 minutes 22 seconds)

    epoch                          1
    sources_admitted               6
    refusals                       []
    blocks                         {"paragraph": 232, "section": 56, "table": 8}
    tiers                          {"evidence": 296}
    supplemental dossier digest    119e6b8691d3136da887c7215c571a211851697d4bb63148cd16395bd28fc45e
    successor run_input_digest     5765db054ace1fba3e62bb339c2ea58535779d2c576976e5bc4dd851a16b1c6a
    amendment_digest               8ab719c2ca35f2cbef65869a31b05153b8a98c5c13c3d941b9d104b4a36dc7e1
    fence_seq                      9949
    problem_id                     null   (evidence-only amendment; the question stands)

The six documents are the exact ones the run bound and never introduced.
Verified byte-identical to the frozen dossier before the run:

    MATCH src-95e7a2acb742b1d6 docs/STATE_OF_THE_THEORY.md
    MATCH src-9116c8592387ce22 docs/harness-spec-v1.3.md
    MATCH src-ce2f8390bf7df646 docs/proposals/GROUNDED_OVERLAY_PREPLAN.md
    MATCH src-2e640db15637b4ac experiments/2026-08-08-corpus-enrichment-patrol-pilot/PATROL_DETERMINISM_REPORT.md
    MATCH src-8ddb400f3c2d52a6 docs/map/CON-warrants-and-attacks.md
    MATCH src-a79fb57bd1b49204 docs/map/SUB-adjudication.md

`sources_admitted: 6` with `refusals: []` is the S6 narrowing working on
the real subject: before this tranche every one of those six would have
been refused `AMEND_SOURCE_ALREADY_ADMITTED`, because each was bound —
even though not one had ever been introduced.

---

## The append-only proof (R4, C1)

From git, over both stages combined:

    $ git diff --numstat experiments/2026-08-12-live-grounded-extension-expansion/run/
    20   0   run/log.jsonl

**Twenty insertions, zero deletions.** Two events for the terminal (the
typed STOPPED receipt at seq 9947 and the terminal commitment) and
eighteen for the amendment epoch. Every other pre-existing byte of the
committed root is unchanged; everything else the operations produced is a
file that did not exist before (`run-stop.json`, `run-stops/`,
`checkpoint.json`, `workflow-checkpoint.json`, `run-result.json`,
`REPLAY_VALIDATION.json`, `run-request.json`, `text-workload.json`,
`run-epochs/`, `run-amendments.jsonl`, the capability audits, and five new
object directories).

Caveat stated rather than hidden: `git status` also shows
`.run-operator.lock` and `.make-operator.lock` as modified. Those are
operator locks — control files, never record content — rewritten by any
legitimate lock acquire. That they are tracked at all is PARKED as P3.

---

## Stage 3 — `continue`: BLOCKED, not skipped

    STAGE 3 SKIPPED: experiments/2026-08-12-live-grounded-extension-expansion/env
    (OLLAMA_API_KEY) is absent

The container was rebuilt mid-tranche and took the gitignored credential
file with it. `continue --budget cycles=8 --token-budget 500000` makes
real model calls and cannot run without it. Everything R7 asks for that
does NOT require a model call has been done on the real root; the
continuation is one line away:

    printf 'OLLAMA_API_KEY=<key>\n' > experiments/2026-08-12-live-grounded-extension-expansion/env
    cd experiments/2026-08-13-change-lifecycle-operation-parity && ./live_parity.sh

The driver is idempotent at that point: stage 1 refuses
`FINALIZE_ALREADY_TERMINAL`, stage 2 refuses
`AMEND_SOURCE_ALREADY_ADMITTED` (correctly now — the six ARE introduced),
so a re-run reaches stage 3 directly. Those refusals are the point: the
operations are exactly-once.

---

## The measurement C5 asked for — and it did not go as predicted

    $ cat verify_root_after_amend.json
    []

**Zero violations. The six went to none.** The tranche's expected end
state said "the original epoch's 6 attached-evidence violations REMAIN as
recorded history — report, don't chase". They did not remain, and this is
reported as measured, not chased: no code in this tranche was written to
force either outcome, and SPEC assumption A4 flagged this exact
possibility in advance, before the run.

**Why, mechanically.** `verify_root`'s attached-evidence check is a UNION
check (`invariants.py:2157-2161`): it accumulates `source_records` across
every epoch and then asks, for each source in the union of all bound
dossiers, whether SOME epoch introduced it. Epoch 1 introduced all six. So
the union is satisfied and the six "has no unique source record" findings
disappear. The per-epoch window check still passed too, because a fresh
amendment epoch holds no LLM event yet, so its `first_llm_seq` defaults to
the window's end and the appended records arrive strictly before it.

**What "zero violations" does NOT mean.** It does not mean epoch 0 was an
evidence-informed run. It was not: 485 model calls happened before any of
those six documents existed in the record, and `RESULTS.md`'s finding
stands unchanged — that epoch should still be read as having answered the
seed question from the question text and the models' own training
knowledge alone. What the clean verdict says is narrower and true: **the
root as a whole is now replay-valid, and every source its identity binds
has been introduced in some epoch.** The evidence is citable from here
forward. It was not citable behind the fence, and nothing about this
verdict changes that.

The honest reading, then: `verify_root` measures the record's internal
consistency, not the epistemic quality of any epoch. A reader wanting the
latter must look at WHICH epoch introduced a source, which the record
still says exactly.

---

## What this run proved, and what it did not

**Proved.** A root launched from a compiled configuration reaches a valid
typed terminal and accepts `amend`, by appending records only. The
operations that were `broken` in `INVENTORY.md` rows 13, 14 and 15 now
work on the real subject that motivated the tranche. The root is
replay-valid: `verify_root` returns `[]`.

**Not proved.** Whether criticism actually engages the admitted evidence —
that is the continuation's job and it has not run. No claim is made here
about the six documents changing any survivor's status, because no cycle
has yet seen them. The amendment made them citable; it did not make them
cited.

**Residue.** Epoch 0's reasoning remains uninformed by the six documents,
and no verification verdict changes that. Whether the continuation's
criticism will cite them is open. Whether any of the 191 survivors
survives contact with them is open. "Accepted does not mean true," and
"replay-valid" does not mean "well-evidenced".
