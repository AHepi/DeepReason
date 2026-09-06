# Delivered: the organiser seat — the writer's room carried onto the full harness, and its measure sealed but not run
Branch: `claude/writers-room-organiser-testing-degagn` @ <HEAD> (pushed, tree clean). Validation: <VERDICT>.

## What changed

**The room reaches a full-harness seat, whole.** A converter under the tranche
turns the writer's-room root into three plain-text files — one paragraph per
record, body verbatim, headed by its kind, id, cycle and the conjecture it is
about — and `deepreason reason --attach` admits them as 94 content-addressed
blocks with no refusal. On every conjecturer call all three sources render in
the frozen-evidence section, nothing compressed, nothing dropped, under a
24 000-token pack budget that is one line of configuration.

**The organiser is a registered pairing, not a form.** `seat.conjecturer.organiser-v1`
pairs a new brief layout, a new directive (organise, do not invent: one candidate
per room conjecture worth carrying; claim and mechanism from its block, sharpened
by its objections; every refutation condition from its proposals; cite only what
the legend shows; name what you could not) and a new wording with the form the
managed conjecturer already fills, `conjecturer.turn.v6`, whose candidate is the
same commitment-bearing proposal the brief's named form compiles to. Beside it,
`seat.critic.evidence-blind-v1` keeps the critic's attacks its own. Both live in
`src/deepreason/llm/seat_layouts.py`, `seat_plugins.py` and `role_prompts.py` —
registered there because the managed path never opens the operator's plugin
directory (parked P1) — and neither is a default: both goldens are byte-identical.

**The record, not the seat, catches invention.** Twelve offline assertions: the
organiser's candidates admit through the ordinary path as accepted conjecturer
artifacts; each countercondition becomes a commitment the artifact carries; a
citation to a block the legend did not show is a typed `EVIDENCE_REF_NOT_EXPOSED`
measure and no status moves; an id naming no block is `EVIDENCE_REF_UNKNOWN_BLOCK`;
unbound, the seat renders the legacy brief.

**The measure is sealed and ready, and did not run.** This container holds no
credential, so PREREG.md (three arms on the D8 question, the run's composed
result as the judged unit, three blind judges under the copied criteria, a
length rule for one unit per arm, MATERIALLY BETTER only if better than both
the plain calls and the harness alone) is committed with its sha256 in the
commit message, the arm scripts, composer, judge and analyser beside it, and
the soak on the launch shape is green. One command runs the plan once `env`
exists: `runs/chain.sh`.

**Two things the record corrected on the way.** The citable legend's 32
blocks are a hash-ordered sample of the 94 (admission sorts blocks by content
id), so the seat reads the whole room but can cite a third of it — disclosed,
and parked with the cap (P2). And `--attach <directory>` admits every file
under it, so the arm script names the three files.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "the forms needs to change so that the conjecture seat can handle and organise the new log shaped content" | done-with-assumption A1 (no new form; a registered pairing on `turn.v6`) | `8946abeec`; VALIDATION S1, S7, S9, S12 |
| R2 | "Now, to test on the full harness" | deferred — operator's brief: "If no key is present, deliver moves 1–2 and the sealed PREREG without the runs, and say so" | PREREG sealed `0d50134a5`; scripts `2ecb513da`; RESULTS §"not run" |
| R3 | converter, one block per record, verbatim, headed | done | `9554abfe4`; S3 |
| R4 | commit converter, attachment, digest | done | `9554abfe4`; S4 |
| R5 | dry attach: admitted, seen, withheld | done | `8528b3a62`; S5 |
| R6 | size the pack; park what is not configuration | done-with-assumption A3 (budget set; legend cap parked P2) | S6 |
| R7 | pairing of the EXISTING form with a NEW layout | done-with-assumption A1 | S7 |
| R8 | file-declared if possible, else `seat_layouts.py` and say so | done (registered in code; said so; P1) | S8 |
| R9 | the brief: organise, do not invent … | done | S9; `proof/ORGANISER_BRIEF.txt` |
| R10 | state that nothing is excluded by the form on this record | done (12 of 12) | S10; RESULTS §2 |
| R11 | show the rendered brief before any live call | done (committed before PREREG) | S11 |
| R12 | stub test: admit, commitments, citation failure | done | S12; `tests/test_organiser_seat.py` |
| R13 | decide and disclose cycle-1-only | done (whole run; P3) | S13 |
| R14 | the critic does not see the room; park the switch | done (blind critic on ARM R; P4) | S14 |
| R15 | PREREG sealed before any live call | done | S15 |
| R16 | three arms: 0 reused, H default, R organiser | done (instruments and scripts); arms deferred under R23 | S16, S2 |
| R17 | judged unit = composed result | done-with-assumption A6 | S16, S17 |
| R18 | criteria before output; 3 blind judges; length with overlap clause | done (n = 1 form of the clause, PREREG §6) | S18 |
| R19 | MATERIALLY BETTER only if better than both | done | S19 |
| R20 | soak green; detached launch; typed outcomes | done (soak green; launch discipline in chain.sh, not exercised) | S20 |
| R21 | env discipline | done | S21 |
| R22 | failure budget 6, ledger | done (spent 0) | S22 |
| R23 | no key → deliver moves 1–2 and PREREG, say so | done | this document; RESULTS §"not run" |
| R24 | RESULTS.md honest ledger | done | S24 |
| R25 | validate and deliver with the R-by-R table | done | VALIDATION.md; this table |

## Assumptions the operator may override
A1: `conjecturer.turn.v6` is the form the organiser pairs — the brief's `reasoning.conjecturer.compact.v2` does not reach the managed path and compiles to the same proposal.
A2: registered in code; the operator plugin directory is read by the reduced engine only (P1).
A3: three attachment files; `PACK_TOKEN_BUDGET: 24000` in BOTH arms' config; the legend's order steers nothing (Amendment 1).
A4: `VS_K` 6 in both arms; the organiser carries at most 6 per turn.
A5: the organiser runs the whole run; later turns carry what is not yet carried, else abstain (P3).
A6: the judged unit is the deterministic composition of the seed problem's positions (`tools/compose_result.py`).
A7: `epoch3` is the soak case (the shape, not the shell).
A8: no key here; `runs/chain.sh` is the one command once `env` exists.
A9: cycles 4, token budget 800 000 per harness arm.
A10: labels stay inside the verbatim bodies; a comma in a header label is folded to `;`.
A11: the organiser wording moves the conjecturer's prose alone.
Amendment 2: the code ceiling raised 450 → 800 rather than trimming the twelve-proof test.

## Map delta
changed: `docs/map/INV-seat-section-plugins.md` (the four-shells paragraph; the entry-point and where-to-change rows; `Verified-at` → `8946abeec`)   created: none   new checks: 2
left stale: `SUB-llm.md`, `CON-packs-and-token-economy.md` — this tranche's commit is among the commits since their stamps, but neither makes a claim the registration falsifies and their checks pass; not advanced because their other listed commits are not this tranche's to vouch for. 22 further stale entries predate this tranche.

## Errata
errata: none. (The brief's naming of `reasoning.conjecturer.compact.v2` and of `deepreason result` were instructions, not committed documents; both are recorded as assumptions A1 and A6.)

## Parked (not done, not promised)
P1 — the managed path does not load `<DEEPREASON_HOME>/seat_plugins/` (defect; prompt in PARKED.md).
P2 — the citable legend's cap and excerpt are code, and its order is by content id (change; prompt in PARKED.md).
P3 — a cycle-scoped seat pairing (change; two roads priced; prompt in PARKED.md).
P4 — a critic that reads the room (change; prompt in PARKED.md).
P5 — per-countercondition block pointers (change; prompt in PARKED.md).
Standing from earlier tranches, untouched: the room's P1/P2, mini's P10/P11.

recommended next: **run the measure** — place `env` (`OLLAMA_API_KEY=…`, `chmod 600`) and launch `runs/chain.sh` detached; it soaks, qualifies both homes, runs ARM H then ARM R, and the judge and analyser follow PREREG §10. Nothing else in the queue answers the operator's question; P2 is the first thing to fix if the run shows the seat citing too little of what it reads.
