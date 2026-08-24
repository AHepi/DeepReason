# DISPOSITION — external consistency review, rung T5

Per `skills/review-response/SKILL.md`: a review is evidence, not a verdict.
Every finding below was re-established against the sources BEFORE any action
(FR-25), and every one has exactly one fate.

Reviewed artifact: `zoo/reviews/CONSISTENCY_PACKET.md` (and its planted twin).
Reviewer: `deepseek-v4-pro:0813` on the operator's Ollama Cloud endpoint —
not the author, not the author's family.
Ledger: `zoo/reviews/calls.jsonl`, 5 rows, `verify_ledger` clean.

## Narrow green — what the reviewer's packet did and did not contain

**Contained:** eight excerpts, 6 202 characters, drawn by `claims.json` from
`CLAUDE.md`, `docs/map/INV-frozen-surfaces.md`, `docs/AUDIT_BASELINES.md`,
`docs/ERRATA.md` and this experiment's `RESULTS.md`. Each excerpt is a ±200
character window around a matched pattern.

**Did NOT contain:** any whole document; any code; any claim not named by a
`claims.json` row. The reviewer therefore cannot have found — and its silence
is not evidence about — any inconsistency between claims this packet does not
watch, or between a claim and the code it describes. `docs_verify` covers the
second of those; nothing covers the first except adding rows.

## Verdict table

| cell | packet | typed verdict | `disagreements` | `worst:` names |
|---|---|---|---|---|
| A | the real packet | `INCONSISTENT` | 2 | the seven-paths / five-surfaces tension |
| B | one claim falsified | `INCONSISTENT` | 2 | **the same tension** |

## The discriminating result, stated precisely

Cell B's packet was byte-identical to A's except that `CLAUDE.md`'s excerpt
named `scheduler/scheduler.py` where `INV-frozen-surfaces`' excerpt names
`qualification.py` — a flat contradiction between two documents in the packet.

**The reviewer DID catch the plant, in prose.** Cell B's body says: "One
document says seven paths including `verification/` and `scheduler/scheduler.py`;
another says five frozen surfaces and includes `qualification.py`." That is the
plant, named.

**The typed fields did NOT move.** `overall`, `disagreements` and `worst:` are
identical across the two cells. Any consumer reading only the typed verdict —
which is exactly what rung T2's gate recorded, and exactly what an automated
lane would store — would have seen no difference between a true document set
and a falsified one.

That is the finding, and it refines rather than reverses T2's: the reviewer's
discrimination is real, and it lives in the part of the reply that the typed
channel throws away.

## Per-finding fates

### F1 — the frozen-surface list is stated inconsistently. **ACCEPTED.**

Verified: `docs/map/INV-frozen-surfaces.md` has exactly five `### <n>` headings
and says "The five frozen surfaces"; `CLAUDE.md`'s third-lane paragraph said
"the seven paths are ...". Both were true — the seven are the five surfaces
expanded (surface 3 spans `invariants.py` AND `verification/`) plus the
frozen-adjacent `route_fingerprint` — but a reader meeting both sentences meets
a contradiction, and the tranche that wrote the "seven" sentence was this one.

**Action taken:** `CLAUDE.md`'s paragraph now states the owning document's five,
explains why they span seven paths, and says which count to use when
("count paths when testing a cone; cite the owning document's five when citing
the law"). Fixed in this tranche because this tranche introduced it.

### F2 — `INV-frozen-surfaces.md` still prescribes the retired root sweep. **ACCEPTED, and PARKED.**

Verified by grep, not by reading: the document says "the 42-root sweep below is
the instrument" (line 27), carries a `### The root sweep` section prescribing
`tools/root_sweep.py` (line 217), and contains **zero** mentions of the
retirement — while `CLAUDE.md:161` and `docs/AUDIT_BASELINES.md:52` both record
the 2026-08-22 operator ruling. A change author told to read this document
FIRST is told to run a retired instrument.

**This is a real, pre-existing defect, and it is not this tranche's.** The
change workflow's scope contract parks what it did not request rather than
fixing it. **Action taken:** `PARKED.md` P1, with a ready-to-send prompt
carrying all five evidence pointers and the precedent for retiring a row
without deleting its history. The operator pays a paste, not an authoring
session.

### F3 — the "old runs owe the future nothing" law is marked SUPERSEDED. **REFUTED.**

The reviewer read `docs/ERRATA.md`'s excerpt as saying the 2026-08-14 operator
law is itself superseded. It says the opposite. `docs/ERRATA.md:864` marks the
OLD governing principle — "fix READERS so old roots stay valid; a change that
invalidates existing replay-valid roots is wrong by definition" — as
**SUPERSEDED BY** the 2026-08-14 law, and quotes the law as the superseding
text. The direction is inverted in the finding.

No action. Recorded rather than dropped, per rule 2: a refuted finding is as
valuable as an accepted one. Its cause is instructive — the packet's ±200-char
window cut the sentence mid-clause ("no tranche owes a replay-byte-uncha…"), so
the reviewer saw `SUPERSEDED` adjacent to the law's name without the governing
"quotes that exact sentence and marks it". **The window is a packet parameter,
and this is what too small looks like.**

## Author defect ledger (rule 4) — verified failures of THIS author, both directions

| # | defect | instance | direction |
|---|---|---|---|
| A1 | diagnosed a symptom's cause from the first plausible mechanism instead of measuring | Rung T2: attributed two FAIL verdicts to context truncation; the cause was `--sha` order, and the diff was 16 359 chars, under even the default budget | over-explained: reached for the sophisticated cause over the boring one |
| A2 | wrote a cross-document claim in a form that contradicted the document that owns it | F1 above: "the seven paths" against "The five frozen surfaces" | over-compressed: flattened a 5-with-a-nuance into a 7 |
| A3 | pre-registered a prediction that the evidence refuted, and the task was too easy by construction | Rung T4: predicted refine→escalate→BLOCKED; got a correct answer on the first generation, because the deciding code was handed over in the excerpt | under-estimated the model; over-estimated my own task design |
| A4 | staged a deviation from a shipped install doc without checking it against this repo's gate | D3 committed `.swarm/log.jsonl`; three tests opened it as a DeepReason Event log and the full gate went red | over-trusted an external document's instructions inside a repo with its own laws |

Errors in both directions are recorded, per rule 4's integrity requirement:
A1 and A2 are compressions toward a tidier story; A3 is the opposite — an
over-cautious prediction the evidence beat.

## The loop's end condition (rule 6)

Every finding has a fate: F1 accepted with the action done, F2 accepted with the
action filed as `PARKED.md` P1, F3 refuted with the quote that refutes it. The
loop is closed; a next round would need a new packet, and the first row it
should gain is a wider `window` for the OLDRUNS claim.
