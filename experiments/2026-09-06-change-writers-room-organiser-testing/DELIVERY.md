# Delivered: the organiser seat — the writer's room carried onto the full harness, and its measure sealed but not run
Branch: `claude/writers-room-organiser-testing-degagn` @ the delivery commit on top of `8c6d425b4` (pushed, tree clean). Validation: PASS — full gate `5106 passed, 6 skipped, 0 failed`.

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


---

# Delivered (launch window): the test run — ARM R failed at cycle 3, the bare arms tied at the rubric's ceiling, verdict INCONCLUSIVE
Branch: `claude/writers-room-organiser-testing-degagn` @ the delivery commit (pushed, tree clean). Validation: PASS (the window); the measure's own verdict: INCONCLUSIVE.

## What happened

**The run went off as sealed and produced no verdict.** The soak was green, the
attached-evidence battery qualified full, and ARM R launched at the operator's
500 000 ceiling with the room attached and the organiser seat bound. It ran
three cycles, carried 7 of the room's 12 conjectures into 16 positions on the
question, registered 54 refutation conditions as commitments — and then died
in the CRITIC seat, `V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY`, at 464 359 of the
500 000. Under the sealed rule that is a failed arm: its unit is not judged and
the verdict for both pairs involving it is INCONCLUSIVE. ARM 0R ran clean —
three calls, the whole room pasted into the user message — and was judged
against the three recorded plain calls. Every one of the eighteen judge
readings scored 15 of 15.

**Two findings the run bought, both worth more than the verdict would have been.**
First, the failure is a defect in this tranche's own configuration, not in the
harness: the evidence-blind critic shell removes the evidence legend from the
critic's brief, but `rules/crit.py` still binds the citable block menu into the
critic's contract, so the seat was asked by a schema for ids its brief never
showed it. It answered with the room's own record ids, was rejected, exhausted
its repair ladder and its atomic fallback, and the run stopped. Second, the
rubric is saturated: with both bare arms at a perfect score on every reading,
this instrument cannot rank anything above a single call on this question, so
"materially better" was unreachable by construction before ARM R ever failed.

**What the organiser itself did, which the record shows plainly.** It rendered
on all 15 conjecturer plans, never the legacy contract; it read the whole room
and cited the legend 21 times; it wrote 16 positions whose refutation
conditions are the room's proposals in the room's words. It also cited the
room's header ids 58 times, which the record caught as unknown blocks and
assigned no status — the same id confusion that killed the critic, on the
other seat.

## Reconciliation (launch window)

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R26 | "It needs a test run now." | done | chain.log; the two arms' records |
| R27 | "Propose some for a single model run and test against bare model." | done — ARM R against ARM 0 and the new ARM 0R; ARM H deferred, not deleted | PREREG Amendments 2–3; VALIDATION S26, S30 |
| R28 | "500k tokens" | done — ceiling 500000, cycles 4; the cycle prediction registered and held | Amendment 1; VALIDATION S27; RESULTS §4 |
| R29 | amend PREREG before any live call, re-seal | done — six amendments, each dated and sealed by sha256 in its commit | VALIDATION S28 |
| R30 | extend the judge and the analyser; CRITERIA byte-identical; pin digests | done | VALIDATION S29; Amendments 4 and 6 |
| R31 | edit armR.sh and chain.sh; say which lines moved; ARM 0R's script and calls | done | VALIDATION S27, S30; Amendments 1–3 |
| R32 | credential discipline | done — placed by the operator in chat, written to the ignored `env` at mode 600, never printed, never committed | VALIDATION S31 |
| R33 | launch discipline; typed outcomes; the organiser-rendered count; one relaunch only | done — no relaunch was taken; the failure was not the transport case the rule allows | VALIDATION S26, S32; PREREG Amendment 6 |
| R34 | harvest, score, reveal, analyse; keymap shut until scores | done | VALIDATION S33; RESULTS §5 |
| R35 | RESULTS.md with terminals, spend, scores, verdicts, the appendix, what the organiser did, the residue | done | RESULTS §§1–7 and the appendix |
| R36 | scope; commit and push at every boundary; deliver with the table | done — `src`, `mini`, `tests` byte-untouched; the attachment verified; PREREG edited only by amendment; no gate run | VALIDATION S35, S36 |

R1–R25 (the build) stand as delivered above, unchanged by this window.

## Assumptions the operator may override (launch window)
A12: ARM 0R's message is the question, a blank line, then the three files verbatim, with no label or instruction.
A13: ARM 0R's three calls are the plan, not the failure budget; the battery is not counted in the 500 000.
A14: the pre-launch base for the diff checks is the commit that sealed Amendments 1–4.
Amendment 5: §0's dossier-digest pin was mis-specified and is corrected to a content check; the arm was sound.
Amendment 6: a failed arm's unit is not harvested, and the judge now enforces it.

## Map delta
No `docs/map/` document moved: no behaviour under `src/` changed in this window.

## Errata
errata: none in `docs/ERRATA.md`. The two corrections this window made are to
this tranche's own sealed document and are recorded there as Amendments 5 and
6, which is where a reader of the measure will look.

## Parked (not done, not promised)
P1–P5 from the build, unchanged. New:
P6 — a seat's brief and its form must agree about evidence (the defect that killed ARM R); three roads priced, prompt in PARKED.md.
P7 — one seat, two id systems: the room's record ids and the admission block ids; two roads priced, prompt in PARKED.md.

recommended next: **P6 first, then relaunch.** The measure cannot answer the
operator's question until a harness arm reaches a terminal, and P6 is what
stopped it; road C in its prompt (refuse the blind pairing on an
evidence-bound run) costs nothing and prevents the death, road A is the real
fix. P7 rides with it, because the same id duality is why 58 of the
organiser's 79 citations failed. And before the next launch is judged, the
rubric needs headroom: eighteen readings at 15 of 15 mean this one cannot see
a difference even if there is one.

---

# Delivered (second launch window): the bad configuration withdrawn, the seat's citations fixed and measured, the arm INCONCLUSIVE twice over on the harness's own bookkeeping

## What happened

The operator said "failure again. Bad config." The bad configuration was the
monitor's own — a critic seat asked by its form for evidence ids its brief had
been built to hide (R14, PARKED P6). This window withdrew that pairing, gave
the seat one id system instead of two, replaced a judging rubric measured
saturated, relaunched, and — on the operator's ruling — continued the arm to a
clean terminal.

**What worked.** Every prediction registered before the run held, several by a
wide margin: not one citation failed, of any kind (64 verified, 0 unknown-block
where there had been 58, 0 quote mismatches where there had been 7); the critic
made 53 calls and did not die; 10 of the room's 12 conjectures were reached and
109 refutation conditions registered; the arm ran on the operator's own 500 000
and spent 495 362 of it.

**What did not.** The arm has still not been judged, and both times the reason
was the harness's bookkeeping rather than its reasoning. First a budget denial
at 99% of the ceiling was typed `operational_failure`, which the operator's own
2026-08-29 law forbids (P8). Then the ruled continuation reached
`completed`/`budget_exhausted` — and the same record that had verified clean
verified dirty afterwards, over three events the continuation never touched
(P9). PREREG §3 wants a clean stop AND a clean verification; the two failures
took one each.

**What was measured anyway.** The control — the bare model handed the whole
room, against the bare model alone — under the new forced-choice instrument:
consistent-win share 17 of 27 = 0.63 against a pre-registered bar of 0.67.
NULL, reported as NULL. The same two arms scored eighteen identical 15s under
the old rubric, so the new instrument discriminates where the old one could
not.

## Reconciliation (second launch window)

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R37 | "failure again. Bad config." | done — the evidence-blind critic pairing withdrawn; the two other measured defects fixed | SPEC Amendment 4; `8a579f1e6` |
| R38 | the default critic; state in SPEC exactly what it sees | done | SPEC Amendment 4's table; `grep -c 'argumentative_critic=' runs/armR.sh` → 0; VALIDATION S37 |
| R39 | one id system (P7 road A); re-run, re-digest, re-prove | done | `747edc25…` converter; 0 room record ids in the attached text; VALIDATION S38, S40 |
| R40 | change the directive only if it names record ids; else the preamble | done — the citation sentence names only legend ids and was NOT changed; the header-shape sentence lives in `src/` and was not touched; the instruction went to the preamble | SPEC Amendment 4; `grep -c 'PREAMBLE' attachment/*.txt` → 1 each |
| R41 | register the prediction: unknown-block 0, verified ≥ 21 | done, and **held**: 0 and 64 | PREREG Amendment 7; `runs/armR/CENSUS.json` |
| R42 | pairwise forced-choice instrument | done | `tools/judge_pairwise.py`; VALIDATION S42 |
| R43 | pre-register share, order-consistency, length rule, decision rule | done | PREREG Amendment 7 §(c) |
| R44 | pre-register the bare-vs-bare control; pin the sha | done, and the control is the one pair judged | PREREG Amendment 7; `runs/PAIRWISE_VERDICT.json` |
| R45 | retire the failed root first, commit the rename | done | `783054bfd` |
| R46 | credential discipline | done — gitignored, mode 600, never committed, never echoed | VALIDATION; `git check-ignore -q env` |
| R47 | chain: soak → cached warm-up → ARM R → stop; detached; monitored | done — soak `exit 0`, warm-up a cache hit (~2 s), ARM R detached, snapshot loop armed | `runs/chain.log` |
| R48 | typed outcomes only; a failed arm is not relaunched for a number | done — no relaunch; the stop-report and the record read before any claim | RESULTS fourth segment §2; VALIDATION S44 |
| R49 | census, then harvest / choose / reveal, then the verdict | done | `runs/armR/CENSUS.json`; `blind/pairwise_*`; `runs/PAIRWISE_VERDICT.json` |
| R50 | RESULTS segment with every listed content; a NULL recorded as a NULL | done — three dated segments; NULL and INCONCLUSIVE both in those words | RESULTS fourth and fifth segments |
| R51 | scope; PREREG only by amendment; the rubric record untouched; no gate | done | two empty scope diffs in VALIDATION |

The measure's own question — is the organiser's output materially better than
the bare model's — is **NOT answered**, for the third time. It is not answered
because no harness unit has ever reached a terminal the sealed rule accepts,
and this window's two blockers (P8, P9) are both in the harness's bookkeeping.

## Assumptions the operator may override (second launch window)

A15 the conjecture's ordinal and angle as the target reference; A16 one
preamble per file (three admitted blocks that are not room records); A17 the
window base `8093b70fa`; A18 the stop-report read only because the arm failed.

## Parked (not done, not promised)

P1–P7 unchanged. New:
P8 — a budget denial at 99% of the ceiling typed `operational_failure`, against the operator's own 2026-08-29 law; prompt in PARKED.md.
P9 — the same three events verify clean before a continuation and violate after it; prompt in PARKED.md.

recommended next: **P8 and P9 before any fourth launch, in that order.** Both
are cheap to state and both are load-bearing: until a budget stop is typed
clean and a verification verdict is stable across a resume, no ARM R will ever
satisfy the terminal test, however well the seat performs — and this window
showed the seat performing well. The organiser itself needs nothing: its
citations are clean, its commitments register, and its brief renders on every
call. What it needs is a harness that will let a finished run be called
finished.
