# RESULTS — the organiser seat: testing the writer's room on the full harness

Honest-ledger segments, dated. Nothing here claims more than the record
shows. "Accepted does not mean true."

## 2026-09-06 — moves 1 and 2 delivered offline; the measure sealed; no arm run (no credential)

**What this tranche proves, and what it does not.** The writer's room's
record (12 conjectures, 36 objections, 46 commitment proposals; 53 493
characters) now reaches a full-harness conjecturer seat WHOLE, through the
attached-evidence road, under a registered pairing that asks the seat to
organise rather than invent; the seat's candidates admit through the
ordinary path, their refutation conditions become the commitments they
carry, and an invented or unshown citation is caught by the record as a
typed measure. All of that is proven offline against the stub — twelve
assertions in `tests/test_organiser_seat.py`, the rendered brief in
`proof/ORGANISER_BRIEF.txt`, the dry attach in `proof/DRY_ATTACH.txt`. What
is NOT shown: whether any of it makes the composed answer materially better.
No live arm ran. This container holds no credential (`experiments/*/env`
absent, `OLLAMA_API_KEY` unset — SPEC M10), so the measure is delivered
SEALED and NOT RUN (R23): PREREG.md, the three arms' scripts, the composer,
the judge and the analyser are committed, and `runs/chain.sh` is the one
command that runs the whole plan once `env` exists.

### 1. The room as an attachment (R3–R5)

| | |
|---|---|
| converter | `tools/room_to_attachment.py`; `records 94 (12 conjectures, 46 proposals, 36 objections)`, `verbatim 94/94`, `chars 53493` |
| files | `attachment/01-conjectures.txt` 9 281 bytes · `02-proposals.txt` 17 566 · `03-objections.txt` 33 377; digests in `attachment/ATTACHMENT.sha256` |
| admission (the function `reason --attach` calls) | `sources 3 blocks 94 refusals 0`, dossier digest `2a49cd52…` (`proof/DRY_ATTACH.txt`) |
| one call sees | all 3 sources whole (frozen-evidence section 63 538 bytes, nothing excluded); legend 32 of 94 blocks (6 113 bytes); 62 withheld from the legend only |

Two things the record corrected on the way. `--attach <directory>` admits
every file under it: the directory form admitted 5 sources and 105 blocks
(the conversion manifest and the digest file too), so the arm script names
the three files. And the citable legend's 32 are NOT the first 32 in file
order: admission sorts a dossier's blocks by content id, so they are a
hash-ordered sample — 7 conjectures, 13 proposals (1 refuted-if), 12
objections (SPEC Amendment 1). The seat READS every body and can CITE a
third of them; the rest are the typed `EVIDENCE_REF_NOT_EXPOSED` measure if
cited. Parked as P2 with the cap.

### 2. What the form excludes on this record (R10)

Nothing. Every one of the 12 room conjectures has a refuted-if proposal
about it — 12 of 12 (`attachment/CONVERSION.json`; the SPEC S10 check prints
`12 12`) — so the form's requirements of a mechanism and at least one
countercondition per candidate exclude no room conjecture. The 46 proposals
are 12 refuted-if, 12 forbids, 12 must-not, 10 predicts.

### 3. The organiser seat (R7–R9, R11–R14)

Registered in `src/deepreason/llm/seat_layouts.py` (the layout
`seat-pack.conjecturer.organiser-v1` and the shell
`seat.conjecturer.organiser-v1`; beside them `seat-pack.critic.evidence-blind-v1`
/ `seat.critic.evidence-blind-v1`), `llm/seat_plugins.py` (the directive
`dr.output-contract.organiser`) and `llm/role_prompts.py` (the wording
`role-prompt.organiser-v1`) — said so, because the managed path never opens
`<DEEPREASON_HOME>/seat_plugins/` (one call site, mini's; PARKED P1). The
form is `conjecturer.turn.v6`, the form the managed conjecturer fills; the
brief named `reasoning.conjecturer.compact.v2`, which does not reach that
path and compiles to the same proposal (SPEC A1).

The rendered brief (`proof/ORGANISER_BRIEF.txt`, 91 795 bytes, under
`PACK_TOKEN_BUDGET 24000`): the organiser wording; problem; criteria; the
three room sources whole; the legend; the directive — ORGANISE, DO NOT
INVENT; one candidate per room conjecture worth carrying, at most 6 this
turn; claim and mechanism from the conjecture's block sharpened by its
objections; every countercondition from its proposals (refuted-if as
written; forbids/must-not → refuted if; predicts → refuted if not);
`evidence_refs` only from the legend; a conjecture with no proposal named in
`uncertainties`; typicality 0.5; nothing not in the blocks. Nothing
compressed, nothing dropped (`proof/ORGANISER_RECEIPTS.json`).

The stub (`tests/test_organiser_seat.py`, 12 passed): two organiser
candidates admit through the ordinary path as ACCEPTED conjecturer
artifacts; each carries `reason-counter@…` commitments, one per
countercondition, `program:reasoning_observation_pending`; the first's two
citations verify; the second's citation of a block the legend withheld is
one `EVIDENCE_REF_NOT_EXPOSED` measure and its status does not move; an id
naming no block is `EVIDENCE_REF_UNKNOWN_BLOCK`; unbound, the seat renders
the legacy brief byte for byte; the blind critic layout is the legacy one
minus the two evidence entries; the wording moves the conjecturer alone;
the two defaults have not moved (both goldens green).

Decided and disclosed (R13): no configuration is cycle-scoped; the organiser
runs the whole run and its directive handles later turns; PARKED P3. The
critic on ARM R is evidence-blind (R14); the switch that would show it the
room's bodies does not exist and is PARKED P4.

### 4. The measure, sealed (R15–R19)

`PREREG.md`, sealed by sha256 in its commit message: three arms on the D8
question; ARM 0 reused by digest; ARM H and ARM R matched (`--cycles 4
--token-budget 800000`, `runs/config.yaml`, one home and one battery each);
the judged unit is the run's composed result (`tools/compose_result.py`,
deterministic, no model — on a committed 4-cycle root: 43 surviving
positions, 53 423 characters); three blind judges under the copied criteria
(byte-identical to D8's); length reported for every unit and controlled by
the n = 1 rule (a BETTER whose unit is > 1.5× longer is NULL,
length-uncontrolled); ARM R MATERIALLY BETTER only if BETTER than BOTH ARM 0
and ARM H by ≥ 2 of 15; NULL and WORSE reported in those words.

### 5. Failure budget (R22)

Six live calls beyond the plan. **Spent: 0.** No live call of any kind was
made from this tranche.

| # | call | reason | cost | decided |
|---|---|---|---|---|
| — | — | — | — | — |

### 6. Residue

- **Not run.** ARM H and ARM R did not run; no verdict exists. The offline
  proofs show the road is open, not that it leads anywhere better.
- One question, one model, one room; n = 1 per harness unit by the design's
  own unit (PREREG §11).
- The seat cites a third of what it reads (P2); the soak covers the managed
  shape, not the shell (PREREG §10).
- The full gate and `docs_verify` on this tree: see VALIDATION.md.
