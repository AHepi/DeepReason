# Pre-registration — the organiser seat on the full harness (SPEC S15–S19; R15–R19)

Written 2026-09-06, BEFORE any arm of this tranche has been launched and
before any call has been made against the provider from this tranche. Sealed
by the sha256 in the message of the commit that adds it. Nothing below may be
edited after a launch except by a dated, numbered amendment at the end that
says what it changes and why.

Authority: REQUEST.md (R1–R25), SPEC.md (S15–S19, A3–A9), and the operator's
success law (CLAUDE.md, 2026-09-03): success is output MATERIALLY BETTER than
what the same model produces WITHOUT the harness on the same question;
correctness is irrelevant. The room ruling that binds the input (2026-09-05):
within mini, criticism overturns nothing; the point was content generation;
"then testing on the full harness" — this is that test.

Follows PREREG_D8.md's form and P11's three lessons: ONE UNIT the rubric fits
(the run's composed result, §4), ONE BUDGET under which the seat reads the
whole room (§0, §3), and HEADROOM stated honestly (§11: the copied rubric was
maxed by the single call in D8; this design does not fix that, and says so).

---

## 0. What is fixed for every arm

| | |
|---|---|
| Model, every call, every seat, every judge | `qwen3.5:397b` at `https://ollama.com/v1`, reasoning OFF (`--reasoning none`; the launch-time disclosure prints what that means for this model), completion cap 8192, context 131072 — the profile every committed live launch since 2026-09-03 uses and the profile ARM 0 was recorded under. |
| Standard input | the D8 frozen input, `experiments/2026-09-05-change-mini-isolation-programme/runs/input-d8` — problem id `question-corroboration-d8`, `run_input_digest 63d2a653a8ec473c8d3ddd715e19ae46feacadc20958aff49141708d28a82c60`, `run-input.json` sha256 `cdc0c98459792ae12eea49ae633986bf2866d3b854b16397235f5d61ee41197b`. Both harness arms receive its `problem.description` verbatim as the question (sha256 of the text `e8e720d251b3cab2cddd548cb5064a74575404c8ae47f347f840faa6021a19b1`, printed by each arm script). |
| Configuration, both harness arms | `runs/config.yaml` (sha256 `84562bd6e0f1b76b0251260c226c84a2157944bdcb86e9150fabfd4e6d2eabc4`): `PACK_TOKEN_BUDGET: 24000`, nothing else. Everything else is the shipped default — `VS_K` 6 (SPEC A4), the engaged v6 policy, both evidence channels as shipped. The knob moves the qualification subject digest, so each arm's home pays one battery (`runs/setup_and_qualify.sh`). |
| Cycles and ceiling, both harness arms | `--cycles 4 --token-budget 800000` (SPEC A9). A `budget_exhausted` stop is a CLEAN typed terminal (operator law 2026-08-29) and its record is judged like any other. |
| The attachment (ARM R only) | the three files under `attachment/`, by name: `01-conjectures.txt` `feb1dc480421d1cdb26260223a82ea82d88d9e14ff761ad63ec9662acd4088bb`, `02-proposals.txt` `cf7a4a2edcc19307e7be923623676cd7db80f8722d58f584fda30fad65062452`, `03-objections.txt` `87163fb464c30da6e06e4daf475245637aad04de8a7f92d6e482b1cb734e0ded` — 94 records, 53 493 characters, verbatim from the room root `shallow-0b47bc7b090854078ddf7559`. Admitted, they mint 94 blocks, 3 sources, 0 refusals, dossier digest `2a49cd527ce88f6fb18a81eede88b456d73d37388816345955ed020526e495a3` (`proof/DRY_ATTACH.txt`). The run's own admission at launch must print the same digest; a different digest is a FAILED arm. |
| The selectors (ARM R only) | `DEEPREASON_SEAT_SHELL=conjecturer=seat.conjecturer.organiser-v1,argumentative_critic=seat.critic.evidence-blind-v1` and `DEEPREASON_ROLE_PROMPT_TEMPLATE=role-prompt.organiser-v1`. Neither is `Config`; neither moves a run id or a subject digest. |
| Credential | one key in the gitignored `env` (`.gitignore:50`, checked by `chain.sh` and `snapshot.sh` before anything runs), mode 600, read at launch by `set -a; . env; set +a`; never committed, never printed. |
| Instruments, committed before any launch | `tools/compose_result.py` `7c2835448886465ffd07ffadc9d057ac0a83da5f58d30dbff96509b4d81b9c62`; `tools/judge_organiser.py` `c686e907c386abbe0c5a358266d651458337423fe2ffe40e82ff392c69823fd4`; `tools/analyse_organiser.py` `30b29f03062f0c49c07ac374ccfdb23d52f18bb50cd5e243e2a89b6b45d46ad0`; `runs/setup_and_qualify.sh` `80883131065dc906f50b5ce9cbdf7e0aa9ba89fe979c5b13c0fe63f92729f097`; `runs/armH.sh` `fced0bf137c03a69456d27d4098fcc1dc8194e39d560b2feba8199fe7b44d1e7`; `runs/armR.sh` `e62adf3cd5eb4d993bd3b535e403148956ac2786176910347e8f98097a671613`; `runs/chain.sh` `8e516dc492f4722f5a9f6e3f4bf30983e280ceb75c4c227f9075b9ccf0a51131`. |
| The rendered brief, before any live call | `proof/ORGANISER_BRIEF.txt` `06a5956ef962ed90bb83970b81d25fbe344bfbba8165314b65375aca2a90fb1d`, 91 795 bytes; its section receipts `proof/ORGANISER_RECEIPTS.json`. |
| Budget | ARM 0: 0 (recorded). Each battery: ≤ ~1 200 calls. ARM H: ≤ 800 000 tokens. ARM R: ≤ 800 000 tokens. Judging: 5 units × 3 judges, the longest unit ~55 000 characters, ≤ ~300 000 tokens. Under 3 M in total. |

## 1. ARM 0 — the same model, no harness (recorded; reused, never respent)

The three D8 calls, exactly as recorded and committed:
`experiments/2026-09-05-change-mini-isolation-programme/d8/arm0/call-1.json`
sha256 `13fbff724bc51a1f55a635d928c40892f763562689959a3ef7a320c953339d08`
(7 262 characters, `finish_reason` stop, 1 631 tokens); `call-2.json`
`0de4306afcd807046f8365b1c1e49599ecb739d522def05a8f7e1f90b307c9e3` (7 688,
stop, 1 804); `call-3.json`
`21b0c63dbd38baed41a79ca979b49d92d0099e0ec9914b070e702e2c7caaaf71` (7 985,
stop, 1 804). Each is one chat completion: the frozen problem description as
the whole user message, `max_tokens` 8192, reasoning off, no schema, no
system prompt (PREREG_D8 §1). R16: reuse; do not respend. If any file's
sha256 differs at harvest, the harvest REFUSES.

## 2. ARM H — the full harness alone

`runs/armH.sh` under home `runs/home-h`: `deepreason --config runs/config.yaml
reason --cycles 4 --token-budget 800000 "<question>"`, default shells
(`seat.conjecturer.legacy-v0`, `seat.critic.legacy-v0`), default wording, no
attachment, the question-only qualification subject. The critic's premise
invitation may render as a note with no legend (no dossier); that is the
default shell's behaviour and is reported (§5 spend table's "invitation"
row), not changed.

## 3. ARM R — the full harness with the room attached and the organiser seat

`runs/armR.sh` under home `runs/home-r`: the same command with the three
attachment files (`--attach` ×3; never the directory — its two non-text
files would be admitted too, measured in `proof/DRY_ATTACH.txt`), the
attached-evidence qualification subject, and the two selectors of §0. The
organiser runs for the WHOLE run (SPEC A5; PARKED P3): on later turns its
directive carries only room conjectures not yet under NEIGHBOURHOOD, else
abstains. The critic is evidence-blind (SPEC S14; PARKED P4).

What the seat sees, measured offline on the stub with this exact attachment
and configuration (`proof/ORGANISER_BRIEF.txt`, `proof/DRY_ATTACH.txt`): all
three sources rendered WHOLE in the frozen-evidence section (63 538 bytes,
`excluded_source_ids` absent), the legend of 32 citable blocks (6 113 bytes;
7 conjectures, 13 proposals of which 1 refuted-if, 12 objections — a hash-
ordered sample, SPEC Amendment 1), the organiser directive (1 838 bytes),
problem and criteria; nothing compressed, nothing dropped. 62 blocks are
withheld from the LEGEND and only from it: the seat reads every body and can
cite a third of them.

**Typed terminal, both harness arms.** COMPLETE when: `run-status.json`
`state` is `completed` with `stop_reason` in {`max_cycles`, `budget_exhausted`}
or the run's other clean typed stops; `deepreason results <root> --json
--verify` reports the stored `verify_root` verdict with 0 violations; the
replay digest equals the live one (the same report); and for ARM R the
admission summary printed at launch carries dossier digest `2a49cd52…`. An
`operational_failure` or a refused launch is a FAILED arm, recorded as
failed; it is not relaunched to get a number — ONE relaunch is allowed only
for a transport death before cycle 1 completed (no conjecturer artifact on
the record), disclosed, with the dead root kept.

## 4. The judged unit — the run's composed result, never one conjecture

D8 compared a part against a whole (P11). Here the unit for a harness arm is
ONE text per arm: `tools/compose_result.py <root>`, a deterministic rendering
of the seed problem's positions at the terminal — every surviving position
(claim, mechanism, the refutation conditions it committed to, its
uncertainties), then every refuted position with the case that refuted it,
then a footer counting the positions on derived sub-questions that are NOT
part of the answer. No model composes; nothing is chosen or ranked; a
survivor is one because the record says so. ARM 0's units are the three
essays, whole. Measured on a committed 4-cycle root of the same model and
question family (`compose_result.py --self-test`): 43 surviving positions,
53 423 characters — so a harness unit is expected to be several times the
length of an essay, which §6 handles by rule rather than by regression.

## 5. Judging — the copied protocol, unchanged

`tools/judge_organiser.py`: a copy of `d8/judge_d8.py` whose ONLY changes
are `harvest` (three arms; the composed units) and the paths; its `CRITERIA`
block is byte-identical to D8's (checked by `diff` in CHECKLIST step 12). The
five criteria, the 0–3 scoring, 3 judges per unit, median-of-three, the
contested flag (> 4 of 15 spread), reasoning off, `max_tokens` 900, the
backoff and the pacing — verbatim. Blinding: `blind/candidates.jsonl` carries
`{bid, text}` only, rows sorted by uuid4 `bid`; `blind/keymap.json` is not
opened until `blind/scores.json` exists (`reveal` refuses otherwise). Nothing
per-arm is written before reveal. Same-model judging is a stated residue
(§11), as in D8.

## 6. Length — reported for every unit, controlled by a rule

The panel pays for length (D8 §4: ρ = +0.716; the history replication:
"indistinguishable once length is held constant"). D8's regression and
quintile strata need a DISTRIBUTION per arm; a composed unit gives one point
per harness arm, so those estimators are unidentified here and are NOT run
(a coefficient on one point is a number nobody should read). The control is
a rule, fixed now: for each pairwise comparison the length ratio
`chars(treatment unit) / chars(control unit)` (ARM 0's control length is the
median of its three essays) is reported, and a BETTER whose better unit is
more than 1.5× the other's length is reported as **NULL (length-
uncontrolled)** — never as BETTER. The mirror holds for WORSE. This is the
overlap clause in its n = 1 form: with no overlap in length there is no
verdict in the winner's favour.

## 7. The decision rule, fixed now

An arm's score is the median of its units' medians (ARM 0: three units; a
harness arm: one). Pairwise, treatment T against control C:
- **T BETTER than C** iff score(T) − score(C) ≥ 2 of 15 and §6 does not downgrade it;
- **T WORSE than C** iff score(C) − score(T) ≥ 2 of 15 and §6 does not downgrade it;
- **NULL** otherwise.

**ARM R is MATERIALLY BETTER** iff it is BETTER than ARM 0 AND BETTER than
ARM H. **ARM R WORSE** iff it is WORSE than either. **NULL** otherwise — and
NULL is reported as NULL, in those words. **INCONCLUSIVE** iff any arm has
no usable unit (a failed arm; a unit no judge could score). `H vs 0` is
reported beside the rule for the reader and is not part of it.
`tools/analyse_organiser.py` prints the table and the verdict; RESULTS.md
pastes them.

## 8. Predictions, registered before launch

- **Quality: NO DIRECTION PREDICTED** for R vs H or R vs 0. Whether a seat
  that organises a room's content into commitment-bearing positions and hands
  them to the harness's own criticism produces a composed answer the panel
  scores higher than the harness alone, or than one essay, is what nobody
  knows.
- **Length, directional:** both harness units are LONGER than the median
  essay (a composed list of survivors against one essay); ARM R's unit is
  not predicted longer or shorter than ARM H's.
- **Cost, directional:** ARM R's conjecturer-seat prompt tokens exceed ARM
  H's by at least the room's size per call (~23 000 tokens × the number of
  conjecturer calls); ARM R's total tokens exceed ARM H's.
- **Citations, directional:** every ARM R candidate carries ≥ 1 verified
  citation, and ≥ 1 `EVIDENCE_REF_NOT_EXPOSED` measure appears in the record
  (the seat reads 94 blocks and can cite 32 — SPEC Amendment 1).
- **Operational, not success:** both arms reach a clean typed terminal at
  cycle 4 or on budget; `verify_root` 0 violations; replay digest equal;
  ARM R's section plans name `dr.output-contract.organiser` on every
  conjecturer call and never `dr.output-contract.conjecturer`.

## 9. Failure budget (R22)

Six live calls beyond the plan, ledgered S6-style in RESULTS.md ("Failure
budget"): every unplanned call (a probe, a re-ask, a relaunch's calls) is a
row with its reason, its cost and what it decided. A seventh is a STOP.
Batteries are the plan, not the budget. Judge retries under the copied
backoff are transport, not calls beyond the plan.

## 10. Order of operations

1. This document and the instruments of §0 committed (this document's sha256 in the commit message), AFTER `proof/ORGANISER_BRIEF.txt` (R11: the brief shown before any live call).
2. `python -u scripts/cycle_soak.py --case epoch3` green (CHECKLIST step 15; `chain.sh` refuses to launch on red). DISCLOSED: `epoch3` is the launch configuration's SHAPE — solo, attached evidence enabled — not its model, and no soak case binds a non-default shell; the organiser's offline proof is `tests/test_organiser_seat.py` (12 assertions) and the two proofs under `proof/`.
3. `chain.sh`, detached (`setsid nohup … & disown`): two batteries, ARM H, ARM R; the snapshot loop armed; roots and logs committed as they complete.
4. `judge_organiser.py harvest` → `score` → `reveal`; `analyse_organiser.py`; RESULTS.md.
5. The verdict by §7, its residue, and the sealed sha of `blind/scores.json`.

**No arm is re-run to get a number.** The one exception is §3's disclosed
pre-cycle-1 transport death. An inconclusive or NULL result is recorded as
such.

## 11. Residue stated in advance

- One question, one model, one room, one run per harness arm: n = 1 per
  harness unit. The rule in §7 is a rule, not power.
- Headroom: D8's nine judge readings of ARM 0 were nine 15s on this rubric.
  If ARM 0 scores 15 again, "R BETTER than 0" is unreachable by construction
  and the verdict can only be NULL or WORSE on that pair; that is reported
  as the rubric's ceiling, not as the harness's failure, and the R vs H pair
  still decides something.
- Same-model judging; self-preference and verbosity bias unmeasured beyond §6's ratio rule.
- The seat cites a third of what it reads (the legend cap and its content-id order, PARKED P2); a candidate's countercondition can come from a proposal it could not cite, and the record marks that as a failed citation, not as invention.
- The critic-side difference between the arms (ARM H's invitation note; ARM R's blind critic) is disclosed, not controlled.
- The organiser runs every cycle; cycles 2–4 are its "carry what is not yet carried, else abstain" turns, not the ordinary conjecturer's (PARKED P3).
- The soak covers the managed path's shape, not the organiser shell.
- If no credential is present when this is delivered, none of §10's steps 3–5 has run, RESULTS.md says so, and this document stands sealed for the operator to launch with one command (`chain.sh`).

---

## Amendments (dated, numbered, append-only; the document above is unchanged)

**Amendment 1 (2026-09-06, the launch window — before any live call): ARM R's ceiling is 500 000.**
The operator: "It needs a test run now. Propose some for a single model run
and test against bare model. 500k tokens". §0's row "Cycles and ceiling"
becomes, for ARM R, `--cycles 4 --token-budget 500000`; cycles stay 4 as
sealed. A `budget_exhausted` stop is a CLEAN terminal (operator law
2026-08-29) and the run is judged as it stands at that stop. What moved:
`runs/armR.sh` line 26, `--token-budget 800000` → `--token-budget 500000`, and
nothing else in that file. Prediction, registered now from the record: the M1
control arm (same model and question family, 4 cycles, pack 2 500) spent
541 666 tokens — ~135 000 per cycle, 48 conjecturer calls at a mean of 8 210
and 88 critic calls; ARM R's organiser brief is ~23 000 prompt tokens
(`proof/ORGANISER_RECEIPTS.json`) but only the seed problem's calls render
the room (derived problems get the 6 113-byte legend only), so a cycle costs
~135 000 plus ~17 000 per seed-problem conjecturer call. **The 500 000
ceiling ends the run in CYCLE 3** (the registered prediction); in cycle 2 if
the seed problem is called more than ~4 times a cycle; reaching cycle 4
falsifies the estimate that the room costs at least 35 000 tokens per cycle.
Budget (§0): ARM R ≤ 500 000; the attached-evidence battery is the plan and
not counted in it.

**Amendment 2 (same date): ARM 0R — the bare model with the room pasted in.**
A fourth arm, `ARM0R-room-bare`: the same model and profile as §0, the same
frozen question, and the user message = the problem description, one blank
line, then the three attachment files' bytes VERBATIM in name order separated
by blank lines — no harness, no schema, no system prompt, reasoning off,
`max_tokens` 8192 — PREREG_D8 §1's call shape plus the room text. Three
independent calls; each is on its own "one call, no harness, plus the room".
Measured before launch (`runs/arm0R.py --dry-run`): the prompt is 60 675
characters (60 680 bytes), sha256
`03a8280867a704459d835e9facc6d81573e7a755ea27c3bc561218732e050f5e`; the
attachment digests are §0's. Recorded per call in `runs/arm0R/call-<k>.json`
(request with key omitted, response, usage, finish_reason, content, the
prompt's sha256, the attachment digests) and summarised in
`runs/arm0R/ARM0R_RESULT.json`; each file's sha256 is pinned into the keymap
at harvest. Typed terminal: as §1's — a completed call carries a
`finish_reason` and non-empty content; transport failures retry with backoff
up to 4 attempts; an empty or length-truncated completion is recorded as such
and kept. Script: `runs/arm0R.sh` → `runs/arm0R.py`, run by `chain.sh` after
ARM R. ARM 0R's three calls are the plan, not the failure budget. Budget
(§0): ≤ ~60 000 tokens.

**Amendment 3 (same date): ARM H deferred.** §2 stands as written and ARM H
is NOT run in this window; it remains in this document as a deferred arm for
a later launch (its script `runs/armH.sh` and its setup line are unchanged
under `runs/`). What moved: `runs/chain.sh` — line 14 (`mkdir -p
$D/runs/armH $D/runs/armR` → `mkdir -p $D/runs/armR $D/runs/arm0R`), line 21
(ARM H's `setup_and_qualify.sh … home-h plain` — removed), line 23 (`armH.sh`
— removed), and `arm0R.sh` appended after `armR.sh`; the header comment
rewritten to say so. `tools/judge_organiser.py harvest` treats a missing
`runs/armH/COMPOSED.txt` as a printed notice ("ARM H deferred") and harvests
three arms; `tools/analyse_organiser.py` prints ARM H as deferred and reports
`R vs H` only when its unit exists, never as part of the rule.

**Amendment 4 (same date): the rule, applied pairwise against the two bare arms.**
§6 and §7 are applied exactly as written to two pairs: `R vs 0` and
`R vs 0R`. **ARM R is MATERIALLY BETTER iff it is BETTER than ARM 0 AND
BETTER than ARM 0R** under §7's 2-of-15 margin and §6's length rule (a BETTER
whose unit is more than 1.5× the other's length is NULL, length-
uncontrolled). **ARM R WORSE** iff WORSE than either. **NULL** otherwise,
reported in that word. `0R vs 0` is reported beside the rule for the reader
and is not part of it. **The one new reading the extra arm buys, stated in
advance:** R BETTER than 0 but NOT BETTER than 0R means the ROOM'S CONTENT,
not the harness, carried the gain — `tools/analyse_organiser.py` prints that
sentence when the pattern occurs and RESULTS.md repeats it in those words.
The judged units are unchanged: ARM 0's three essays, ARM 0R's three replies
(each whole), ARM R's one composed result. §8's predictions gain one line:
**no direction predicted for R vs 0R**; and one directional line: ARM 0R's
replies are LONGER than ARM 0's (the room gives the bare model more to say).

**Instruments pinned at this amendment (committed before the launch):**
`tools/judge_organiser.py` `af4af1f1bc899f9ddda78289a8260573c44fac60c557e5f608b7173a6a8e136a`
(its `CRITERIA` block byte-identical to D8's — the sealed `diff` re-run empty);
`tools/analyse_organiser.py` `71e831c94941ae15eb64886ee5ca8fd853761813f09f677a5125b55153ba8237`;
`tools/compose_result.py` unchanged, `7c2835448886465ffd07ffadc9d057ac0a83da5f58d30dbff96509b4d81b9c62`;
`runs/arm0R.py` `78f95ae585a4436d4c3b230a68acc7b44394b7c54f7201e65655433cc399da9d`;
`runs/arm0R.sh` `9a4f3209fa815fd370ca0542a98d22e17dc3ea7ea45d86001328bfeea85eb24b`;
`runs/armR.sh` `99fe726e96018d47af00b3f9fa77c557b9beff53c679a8fcbaf49a0b863489c0`;
`runs/chain.sh` `442a8ceeea96c341da4a18ed1b4c20587e12fb4be701f102a4c2cb5e7e234df5`.
§10's order becomes: this amendment sealed → soak → the attached-evidence
battery → ARM R → ARM 0R → harvest, score, reveal, analyse → RESULTS.md.
Residue added to §11: ARM 0R's three calls and ARM R's one unit are n = 3 and
n = 1; the pasted room and the attached room are the same bytes, but the bare
model reads them as one message while the seat reads them as frozen evidence
with a legend — the comparison isolates the harness's organising and
criticism from the content, not the presentation.

**Amendment 5 (2026-09-06, during ARM R's launch — a correction to §0's own pin, decided by measurement).**
§0 pinned "the run's own admission at launch must print the same digest
[`2a49cd52…`]; a different digest is a FAILED arm". The live launch printed
`d2120e7dcb90332b0ebd4eea71996b705b895d7604fd67bbe6db8a510f04275f` with
`sources_admitted 3`, `blocks {paragraph: 94}`, `tiers {evidence: 94}`,
`refusals []`. **The pin was wrong, and the arm is sound.** Measured rather
than argued: admitting the same three files twice offline, changing only the
provenance label, gives `2fc5dde83b853f83…` under `supplied_by="dry attach"`
and `b1c80cc7cbcf102f…` under `supplied_by="deepreason.reason.attach"`, both
with 3 sources, 94 blocks, 0 refusals. The dossier digest therefore binds the
PROVENANCE, the problem reference and the source locators — not the room's
bytes alone — and `proof/DRY_ATTACH.txt` computed its value under a different
provenance, a different problem_ref and different locators from the live
path. No digest computed offline could ever have matched.

What proves the room reached the run unchanged, and did:
(a) `runs/armR.sh` verified the committed attachment before launching —
`01-conjectures.txt: OK`, `02-proposals.txt: OK`, `03-objections.txt: OK`,
`CONVERSION.json: OK` (a mismatch exits 6 and no call is made);
(b) the admission summary's content is identical to the dry attach's: 3
sources, 94 evidence-tier paragraph blocks, 0 refusals.

§0's row is amended to read: **the launch must print 3 sources, 94 blocks,
0 refusals, and armR.sh's digest check must pass**; the dossier digest is
recorded as a fact of the run, not compared to an offline value. Nothing else
in §0 moves, and the decision rule is untouched.

**Also recorded, a defect in this window's own instrument, not in the run:**
`runs/armR.sh` line 25 echoes "reason, 4 cycles, 800000 token ceiling" while
line 26 passes `--token-budget 500000`. The sed that applied Amendment 1
moved the command and not the banner. The RUN is correct — the live process
line carries `--token-budget 500000` and the root's own `progress.jsonl`
records `token_limit: 500000` — and the log line is wrong. The banner is
fixed after ARM R terminates, never while bash is reading the script.

**Amendment 6 (2026-09-06, after ARM R terminated — the disposition of a failed arm).**
ARM R terminated `state: failed`, `stop_reason: operational_failure`,
`V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY … route seat has terminally exhausted
its smallest authorized contract`, at cycle 3, having spent 464 359 of the
500 000 (root
`runs/home-r/runs/run-36d9a22c3e2045ae1b8c7bfb9d95d092`). Under §3 that is a
FAILED ARM, recorded as failed and NOT relaunched to get a number: the one
relaunch §3 allows is a transport death before cycle 1 completed, and this is
neither. Under §7 an arm with no usable unit makes the verdict INCONCLUSIVE.
So: **ARM R's composed unit is NOT harvested and NOT judged**; the verdict for
`R vs 0` and `R vs 0R` is INCONCLUSIVE; `0R vs 0` is judged and reported as
Amendment 4 already provides. `tools/judge_organiser.py` now reads the arm's
root `run-status.json` and refuses a unit whose run is not `completed`,
printing a notice — that IMPLEMENTS §3 rather than changing it (composition
succeeds on a partial record, so without the check a failed run's positions
would be scored as if it had reached a terminal). Its `CRITERIA` block is
unchanged and still byte-identical to D8's; its digest becomes
`ea2003851dc51dc50eb9acd9f06a6cf14cd7fa60780bd45eeccc39095bd952f1`.
The failure's cause, its evidence and its disposition are written up in
RESULTS.md and parked as P6; nothing here changes the decision rule.

**Amendment 7 (2026-09-06, the SECOND launch window — before any live call of this window).**
The operator: "failure again. Bad config." Three changes, all configuration or
tranche-local tooling; nothing under `src/`, `tests/`, `mini/` or `docs/`
moves. The document above and Amendments 1–6 are unchanged; §5's rubric
instrument and `blind/`'s scores stay exactly as sealed, as the record of the
ceiling §11 predicted and RESULTS.md measured.

**(a) The critic is no longer blind.** §3 fixed ARM R's selectors as
`DEEPREASON_SEAT_SHELL=conjecturer=seat.conjecturer.organiser-v1,argumentative_critic=seat.critic.evidence-blind-v1`.
For this launch the second half is WITHDRAWN: `runs/armR.sh` selects the
organiser for the conjecturer only and the critic runs the shipped
`seat.critic.legacy-v0`. What that critic sees of the room, measured from
`src/deepreason/llm/seat_layouts.py:82-106` and `evidence/render.py:192-198`:
the premise invitation, and the CITABLE EVIDENCE BLOCKS legend — 32 of the 97
admitted blocks, 160 characters each, hash-ordered — and its form's
`premise_evidence` menu bound from exactly those 32
(`rules/crit.py:1306-1322`). What it does NOT see: `dr.evidence.frozen`, the
room whole; that entry is absent from its layout at every priority, so the
bodies of the 97 blocks are never rendered to the critic, and the 65 blocks
outside the legend reach it only as a withheld count. Brief and form now agree
about evidence, which was the defect (PARKED P6). DISCLOSED: the two ARM R
runs therefore differ in TWO places — the critic's shell and the attachment's
headers — so neither difference is isolated by this launch, and P4 and P6 stay
parked and unfixed. Registered as a named risk, not defended against: the
invitation and the legend are both DROPPABLE at priority 6, so a budget that
drops the invitation would take the legend with it and re-create P6's shape
from the allocator instead of the shell; the critic's pack renders no frozen
dossier and is the small pack of the two, so this is unlikely here, and if it
happens the record will say so.

**(b) One id system, and what it moved.** `tools/room_to_attachment.py` writes
NO room record id into the attached text (PARKED P7 road A). Headers are now
`CONJECTURE n=<ordinal> cycle=<n> angle=<angle>`, `PROPOSAL cycle=<n>
kind=<label> about-n=<ordinal> about-angle=<angle>` and `OBJECTION cycle=<n>
about-n=<ordinal> about-angle=<angle>`; the record ids are in
`CONVERSION.json`, which is not attached. Each file opens with ONE preamble
paragraph carrying the header shape and the rule that only the legend's ids
resolve — R40's own fallback, taken because the organiser directive's
header-shape sentence lives in `src/` and this window may not edit it (the
directive's CITATION sentence names only legend ids and needed no change).

§0's attachment row is amended. The three files and the conversion, by
sha256: `01-conjectures.txt`
`3e41fbafb44a00d9aebfe9aba55731fd3326eac0c4359ab187ff45b6b4047655`,
`02-proposals.txt`
`27f092c191ce94042559c5bd961d1675b2eca43091e9d3b1377b38ca0c66ec0b`,
`03-objections.txt`
`8fde979b1b6eab3e1fa1a959a3e56939ea74d5223a64326a9258e057d1f709fc`,
`CONVERSION.json`
`99d4f7d09a0a1c83d534e8b852c3ee682482b88d497eec0c7abb8ca3282c5851`. The room's
94 records are byte-identical to the sealed ones (`verbatim 94/94`, 53 493
characters); the three preambles are the only added text, and they take the
admitted block count from 94 to **97**. The launch must print **3 sources, 97
blocks, 0 refusals** and `armR.sh`'s digest check must pass; the dossier
digest is recorded as a fact of the run and not compared to an offline value
(Amendment 5's ruling, unchanged). The rendered brief, before any live call:
`proof/ORGANISER_BRIEF.txt`
`810163f876c6004cab9b1ebc55d3e3dd8b294140228dbaef0a555bdb8f46d4cd`, 95 071
bytes; `proof/DRY_ATTACH.txt` re-measured.

**Measured before the launch, and disclosed.** Every block's content id moved
with its header, so the legend's hash-ordered 32 is redrawn: **4 conjectures /
17 proposals / 11 objections**, against 7 / 13 / 12 before, with 6 refuted-if
proposals visible where 1 was. Consequence for the census, stated now so it is
not read as a result: the strict "room conjectures carried" count resolves
only citations of a CONJECTURE's own block, and only 4 of the 12 are citable,
so that count is capped at 4 by PARKED P2's legend and not by the seat.
`tools/organiser_census.py` therefore reports a second count beside it —
conjectures REACHED, named by a verified citation of the conjecture's block or
of a proposal or objection written about it. Both are reported; neither
replaces the other.

**The predictions this window registers (R41), before the launch:**
- `EVIDENCE_REF_UNKNOWN_BLOCK` count **0** (it was 58);
- `EVIDENCE_CITATION_VERIFIED` count **>= 21** (it was 21);
- the run reaches a CLEAN typed terminal — `completed` with `stop_reason` in
  {`max_cycles`, `budget_exhausted`} — where the first launch died
  `operational_failure` in the critic seat;
- the cycle prediction of Amendment 1 stands unchanged: the 500 000 ceiling
  ends the run in CYCLE 3.
Nothing is predicted about quality; that is what the instrument below is for.

**(c) Pairwise forced choice replaces the 0–3 rubric for this launch.**
`tools/judge_pairwise.py`. §5's rubric measured saturated — eighteen readings,
eighteen 15s on both bare arms — so it cannot rank anything above a single
call on this question; it and `blind/scores.json` stay untouched as the record
of that.

*The units.* ARM R: the one composed result (`tools/compose_result.py`, §4's
unit), REFUSED when the root's `run-status.json` is not `completed` — a FAILED
arm has no usable unit (§3, §7, Amendment 6). The bare arms: ARM 0's three
recorded D8 essays and ARM 0R's three recorded replies, both reused BY DIGEST
and never respent. DISCLOSED: ARM 0R's recorded calls pasted the PRE-CHANGE
attachment; the room's 94 record bodies in it are byte-identical to this
window's, and the difference is confined to the header lines and the three
preambles, so ARM 0R is reused rather than respent and the difference is
stated rather than controlled.

*The readings.* Every ARM R unit against every bare unit: 1 × 3 = 3 pairs
against ARM 0 and 3 against ARM 0R, **6 measured pairs**; each shown to 3
judges in BOTH orders (ARM R as Text A and as Text B), **6 readings per pair,
36 readings in total, 18 per bare arm**. (The brief's arithmetic — "6 pairs ×
3 judges × 2 orders = 36 readings per bare arm" — cannot hold with one ARM R
unit and three bare units per arm; it is resolved here as 6 pairs and 36
readings IN TOTAL, 18 per bare arm, and recorded as a resolution rather than
a silent correction.) Same model, reasoning off, `max_tokens` 300, blind:
units are addressed by uuid4 and `blind/pairwise_keymap.json` is not opened
until `blind/pairwise_choices.json` exists (`reveal` refuses otherwise). The
standard is the rubric's own five criteria, READ FROM `judge_organiser.py` at
run time rather than retyped (`judge_pairwise.py criteria-check` prints them,
sha256 `fab3fde2f3a2000bd5f7415e7a7ae3be013fd8b83b4fd52395eef4b18327df28`);
the scoring sentences are replaced by ONE forced choice plus a one-line
reason, and a tie is refused in the prompt.

*Order consistency.* A judge's two readings of one pair are undone of their
position and compared: if both name the same unit the judge has a CONSISTENT
preference; **if the choice flips with the order it counts as NO PREFERENCE**
and is neither a win nor a loss. The count of no-preference readings is
reported per pairing.

*The share, and the rule.* CONSISTENT-WIN SHARE of ARM R against a bare arm =
consistent wins for ARM R ÷ all judge-pairs read for that arm (3 pairs × 3
judges = 9); no-preference judge-pairs stay in the denominator. **ARM R is
MATERIALLY BETTER only if its consistent-win share is >= 2/3 against BOTH ARM
0 and ARM 0R; <= 1/3 is WORSE; between is NULL.** A failed arm is
INCONCLUSIVE, exactly as Amendment 6 says. §6's length rule is applied to the
verdict: the length ratio is reported per pair, and a BETTER whose winning
unit is more than 1.5× the other's length is reported as **NULL
(length-uncontrolled)**, the mirror for WORSE.

**A ceiling registered in advance, as §11 registered the rubric's.** The first
ARM R composed unit was 21 396 characters against bare units of 5 875–7 985.
If this one is of the same order, every measured ratio is about 2.7×–3.6×, and
§6's rule DOWNGRADES ANY BETTER TO NULL (length-uncontrolled) before it is
reported. So "MATERIALLY BETTER" is very likely unreachable on this
instrument too, and that is a property of the sealed length rule, not a
finding about the harness. The rule is not changed to make the verdict
reachable. To keep the signal visible under it, `reveal` prints and
`PAIRWISE_VERDICT.json` records the raw consistent-win share and
`verdict_before_length_rule` beside the verdict; those are REPORTED, and the
verdict is the rule's.

*The control.* ARM 0R against ARM 0 by the same instrument: 3 × 3 = **9
pairs, 54 readings**, reported beside the rule and never part of it, so the
reader can see whether the room alone moves a forced choice.

**(d) Instruments pinned at this amendment (committed before the launch).**
`tools/judge_pairwise.py`
`7bdb106ef3d78307afd44e68230a1359c11fd0f807beea7ce6b6224ce88d4862`;
`tools/room_to_attachment.py`
`747edc25786223b8754b732fc99507d410c7d653c4b1b92154197e9fab3e7a6d`;
`tools/organiser_census.py`
`24548d7d62afd687aa042bf2ca469c00a8ce61647563cfd006aef677e44a606f`;
`tools/compose_result.py` unchanged,
`7c2835448886465ffd07ffadc9d057ac0a83da5f58d30dbff96509b4d81b9c62`;
`runs/armR.sh` `a19a9edc8640f370040584a7c158d0138abf3f120a7e16e958b7e7663a25fdd1`;
`runs/chain.sh` `961f3f288ef439b70ece9f12f0ccf3bc4c659184f415f0e55bea19d6619918ba`;
`proof/dry_attach.py` `3b614bc5bf1a4444c61a17c65ff662eafea08422e209eca5327891c43b6bdf0c`;
`proof/render_brief.py` `63b0713e60bab93810fcdd8d9261a92ec02e7f1d3b1f3499f01b480c8d615b4b`.
`tools/judge_organiser.py` and `tools/analyse_organiser.py` keep the digests
Amendment 6 and Amendment 4 pinned and are NOT edited.

**What moved in the scripts, line by line.** `runs/armR.sh`: line 25's
selector loses `,argumentative_critic=seat.critic.evidence-blind-v1`; line 28's
banner "800000 token ceiling" becomes "500000" (Amendment 5 recorded that
defect and deferred the fix to after the arm — this is that fix); the header
comment says which critic runs and why. `runs/chain.sh`: `mkdir -p …
$D/runs/arm0R` becomes `mkdir -p $D/runs/armR` plus `rm -f
$D/runs/STOP_SNAPSHOT` (the committed stop file would have stopped the
snapshot loop on its first pass), the ARM 0R line is removed, and the closing
line names the census and the pairwise instrument. Epoch 1's outputs are moved
whole rather than overwritten: `runs/armR/` → `runs/armR-epoch1/`, with
`chain.log`, `soak.log` and `snapshot.log` beside them; the failed root is
retired as `runs/home-r/runs/failed-epoch1-run-36d9a22c…`.

**§10's order for this window.** this amendment sealed (its sha256 in the
commit message) → the failed root retired and committed → the new attachment,
brief and instruments committed → soak `epoch3` green → the attached-evidence
battery (expected to CACHE: same home, same profile, same `runs/config.yaml`,
same opt-ins; if it re-runs, the log says so and it runs) → ARM R at 4 cycles
and 500 000 → `tools/organiser_census.py` → `judge_pairwise.py harvest`,
`choose`, `reveal` → RESULTS.md. §9's failure budget is unchanged: six live
calls beyond the plan, ledgered; the 0 spent so far carries over.

**Residue this amendment adds to §11.** The critic differs between the two ARM
R runs as well as the attachment, so a difference in outcome has two possible
causes; the legend's redrawn sample changes which blocks are citable, so the
citation counts are not comparable block-for-block with the first launch; the
judges are the same model as the seats, as before; ARM H stays deferred; and
the length rule above will very likely make "materially better" unreachable
whatever the panel chooses.
