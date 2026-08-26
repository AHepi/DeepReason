# The run anatomy synthesis — what 54 committed runs say the harness is

Closing document of the RUN ANATOMY PROGRAM
(`experiments/2026-08-26-run-anatomy-program/PROGRAM.md`), 2026-08-26.

**Nothing in this document refutes the idea the harness was built on.**
What 3 155 provider calls across 54 committed run roots refute is one
particular *wiring* of that idea: the criticism channel was never plugged
into the thing that writes the next conjecture, the allocation
controller's forty-seven decisions never reached a single call to the
model, and the judge road was closed at compile time in fifty-three of
the fifty-four runs — while the part that took the most engineering, the
typed append-only record and its replay verification, passed every
independent check this program could aim at it. The expensive machinery
is intact. Two of the connections that were supposed to carry its output
onward were never made, and until this program measured them, nothing in
the record said so.

Terms, glossed once here because they recur throughout. A **committed
run root** is one directory holding a finished run's evidence —
`log.jsonl` (the append-only event log), `objects/` (the typed records
the events refer to), `blobs/` (the raw model responses), and the
status files. A **provider call** (or "attempt") is one request to a
model. A **dispatch** is one such request made on behalf of one seat. A
**seat** is one instance of a role — conjecturer, critic, judge — so one
role can occupy two structurally different seats. A **wire contract** is
the typed JSON form a seat must fill in, and *valid on arrival* means the
model's reply satisfied that form on the first read, before any repair.
**`verify_root`** is the replay check that re-derives a whole run from
its log and reports whether anything in the record is corrupt or altered.

### What this document is, and what it is not

It is a synthesis. It carries out no measurement and re-derives no
number. Every figure below is quoted from a committed measurement
artifact and cited to it by file and by that artifact's own section,
table or finding label. Where an input labels a claim (`W1 RESULTS.md
§3`, `W2 TABLES.md §3b`, `W3 RESULTS.md F1`, `W4 FUNNEL.md`, `W5
STALENESS.md`, `W6 TABLES.md T12`), the label is the citation unit,
because labels survive edits that line numbers do not.

**This document carries no `check:` lines, deliberately.** Map documents
under `docs/map/` authenticate themselves by re-derivation: each
load-bearing sentence carries a shell command that must exit 0, so the
document proves it is still true rather than proving who wrote it. This
is not a map document. It makes no claim about what the code currently
does that its own command could re-check; it summarises what six
measurement windows found in a frozen set of committed roots. The
windows' own instruments are the re-derivation path, and each is named
where its number is quoted. `python tools/docs_verify.py` therefore has
nothing to check here, which is correct and not an omission.

**Where the inputs live.** Four of the six windows are on `main`, inside
`experiments/2026-08-26-run-anatomy-program/`: `W1-form-census/`,
`W4-judge-road/`, `W5-signals-controller/`, `W6-token-flow/`. Two are
not merged, and every citation to them names the branch:

| window | branch | directory |
|---|---|---|
| W2 — criticism | `claude/criticism-anatomy-w2-1z2029` | `experiments/2026-08-26-run-anatomy-w2-criticism/` |
| W3 — evidence and scratch | `claude/run-anatomy-w3-census-p5pgmb` | `experiments/2026-08-26-run-anatomy-w3-evidence-scratch/` |

A reader who checks a W2 or W3 citation against `main` alone will not
find the file. That is a fact about what has been merged, not about the
evidence, and it is stated here rather than discovered later.

**The frame.** `docs/LESSONS_LEARNED_2026-08-17.md` §1.3 states the rule
this document is written under: *"Accepted does not mean true... Honest
ledgers survived model upgrades, container rollbacks, and doctrine
changes; optimistic summaries would not have."* Several findings below
are unflattering to work I and my predecessors did. They are recorded at
their measured size, and where a finding is smaller than it sounds, that
is said in the same breath.

---

## 1. The organ table

One row per subsystem the program measured. The verdict vocabulary is
fixed, and each value means one thing:

- **WORKS** — it does the job it was built for, and a number in the
  record shows it doing that job.
- **INERT** — it runs, it is recorded, and nothing downstream consumes
  what it produces.
- **HARMFUL-AS-WIRED** — it spends real budget and, as currently
  connected, leaves the run or the record worse than not having it. This
  is a statement about the wiring, never about the idea.
- **PHANTOM** — it is declared in code or in a contract and has no
  referent in any committed run.
- **UNEXERCISED** — the path exists and is believed sound, and no
  committed run has driven it far enough to test it.

The judge road appears as **two** rows rather than one. The record gives
its entry and its guards opposite verdicts — the road was never entered
in 53 of 54 roots, while the guards on the one root that ran them turned
away 114 of 122 trials — and a single verdict would have to suppress one
of those two numbers.

| # | organ | verdict | the one number that earns it | citation |
|---|---|---|---|---|
| 1 | **Forms / wire contracts** — the typed JSON shapes every seat must fill | **WORKS** | **2 743 of 3 155 provider attempts valid on arrival (86.9 %)**; on the first ask, 2 475 of 2 699 (91.7 %) | W1 `AGGREGATE.md`, "Arrival validity by form" and "What the seat spent its calls on"; W1 `RESULTS.md` §5 |
| 2 | **Reference grounding** — the fields whose job is to NAME something that already exists (an evidence block, a scratch note, a neighbouring artifact) | **HARMFUL-AS-WIRED** | **255 of 257 (99.2 %)**: where the record told the seat in plain words that leaving the reference out was legal, the seat invented a handle anyway | W1 `RESULTS.md` §3; `COERCION_PROBE.json` → `coerced_fabrication` |
| 3 | **Criticism channel** — the critic seat's written attacks and what becomes of them | **INERT** | **0 of 196** model-written attacks in the two newest large runs were ever shown to a later conjecture dispatch | W2 `TABLES.md` §3a; W2 `RESULTS.md` segment 1 *(branch `claude/criticism-anatomy-w2-1z2029`)* |
| 4 | **Scratch** — the working notepad a conjecturer may write to and later read back | **WORKS**, where reading back is switched on | **36 of 199 notes (18.1 %)** leave distinctive verbatim wording in a later artifact where retrieval is enabled, against **5 of 115 (4.3 %)** in the retrieval-disabled control; Fisher exact, two-sided, **p = 0.0004** | W3 `RESULTS.md` F8 *(branch `claude/run-anatomy-w3-census-p5pgmb`)* |
| 5 | **Evidence citation** — the attached dossier, the citable legend, and the byte-check that verifies a quote against admitted text | **HARMFUL-AS-WIRED** | **591 of 623 admitted blocks (902 387 bytes, 93 % of the dossier) were never rendered to any model**, and nothing in the record discloses the truncation | W3 `RESULTS.md` F1; W3 `TABLES.md` §1d |
| 6 | **Judge road — entry** — the path from "a criticism exists" to "a defended trial convenes" | **UNEXERCISED** | **1 of 54 roots ever entered a defended trial**; 161 trials in that one root, 0 in the other 53 | W4 `FUNNEL.md`, "The standing fact, re-derived over all 54 roots"; W4 `RESULTS.md` segments 1 and 3 |
| 7 | **Trial guards** — the six gates a convened trial must clear before a prose criticism may refute anything | **WORKS** | **114 of 122 convened trials were turned away by the guards; 8 sustained (6.6 %)** — 39 to formal supremacy, 62 to the two judge families disagreeing, 37 to the defence, 12 to a ruling that did not quote the exchange, 22 to paraphrase | W4 `FUNNEL.md` leg 2; W4 `RESULTS.md` segment 2 |
| 8 | **Signal registry** — the declared contract of named measurements the harness promises to produce | **PHANTOM** | **79 of 111 declared names have never carried a value in any of the 54 roots**, and 84 of 111 declare no staleness bound at all | W5 `RESULTS.md` segment 1, headline 1; W5 `DECLARED_VS_EMITTED.md`; W5 `STALENESS.md` |
| 9 | **Allocation controller** — the loop that reads those signals and tunes each seat's token caps | **INERT** | **47 tuning decisions; 0 of them became the `max_tokens` of any later call.** The conjecturer's cap was driven 32 768 → 20 480 → 12 800 → 8 000 → 5 000 → 3 125 → 1 953 → 1 221 → 800 across sixteen cycles while **every single dispatch went out at 32 768** | W5 `RESULTS.md` segment 1, headline 3 and "What 'tuned and nothing changed' looks like"; W5 `DECISIONS_AND_EFFECT.md`, the `wire` column, `no` in all 47 |
| 10 | **Token economy / metering** — the three counters that each state a run's provider spend | **HARMFUL-AS-WIRED** | **18 of 54 roots report `token_spend: 0`** while the log and the accounting agree exactly on a real figure. P-C1 ARM H — 702 789 tokens — prints zero on `deepreason results`, the one sanctioned retrieval surface | W6 `RESULTS.md`, "three token instruments, 27 disagreements"; W6 `TABLES.md` T10; `METER_RECONCILIATION.json` |
| 11 | **The record and its verification** — the append-only log, the typed objects, and `verify_root` | **WORKS** | **463 of 463** mechanical verdicts re-derive correct, and **60 of 60** re-rule correct under an implementation that imports nothing from `deepreason`; `verify_root` reports **0 violations** on both priority roots; **0 of 3 155** attempts failed to resolve to their own attempt object | W2 `TABLES.md` §2; W4 `RESULTS.md` segment 4 and `ADJUDICATION_SAMPLE.md`; `experiments/2026-08-25-poietics-program/RESULTS.md`; `experiments/2026-08-25-change-constructive-frontier/RESULTS.md`; W1 `RESULTS.md`, join health |

Three rows need a sentence each so the verdict is not read wider than it is.

**Row 1 is dragged by one form, and the fix already exists in the code.**
The 86.9 % hides a spread: the one-field and two-field contracts arrive
valid 100 % of the time, and `conjecturer.turn.v6` — a whole turn in one
form — arrives valid 66.3 % (W1 `AGGREGATE.md`). Held to `glm-5.2`
alone, so the model is controlled, the composite form is 61.9 % valid
over 659 attempts and its atomic decomposition — same role, same seat,
same route, one candidate per call — is **96.8 % over 339**, on a
strictly harder sample, since the atomic form only runs after the
composite one has already failed (W1 `RESULTS.md` §1). One model,
`deepseek-v4-flash:0731`, reverses the effect on small samples, which is
why W1 records it as measured rather than universal.

**Row 5's byte-check is real; its exposure is not.** The check verifies a
claimed quote against the block's full canonical text, and it works: 210
of 234 candidate-side checks in P-R1 came back verified (W2 `TABLES.md`
§2c). But the citable legend renders each block as a 160-character
preview, and every one of the 70 verified quotes lands inside that
preview — maximum end position exactly 160, none beyond (W3 `RESULTS.md`
F2). Meanwhile the code `EVIDENCE_CITATION_VERIFIED` is returned both
when a model quoted checked text and when it merely named a handle and
quoted nothing: 146 of 294 refs were bare handles (W3 `RESULTS.md` F3).
And the critic side is barely checked at all — 55 citations emitted, 3
checked in P-R1; 51 emitted, 0 checked in P-C1 (W2 `TABLES.md` §2c). So
"212 byte-checked citations" is a true sentence that means considerably
less than it sounds like.

**Row 8's phantom names are mostly harmless, and four are not.** Most of
the 79 silent names describe paths no committed run took. Four of the
five signals the allocation policy is said to *read* have no emit site
anywhere in `src/` — they are computed in-process and never written down
— so what the controller acted on is recoverable only from decisions
that produced a change, and a cycle where it held is silent (W5
`RESULTS.md`, "The declared-but-silent census"). Separately, 18 151
Measure events across the corpus carry a tag no registry entry declares,
in eight families, all of which escape the registry's enforcement test
because that test matches an inline literal at the call site (W5
`DECLARED_VS_EMITTED.md`, "Emitted but NOT declared").

---

## 2. The causal story of the 33× loss

The loss, stated once. On the constructive-frontier instance, at matched
measured budget (`T_S / T_H = 1.009`, above the pre-registered 0.95
floor, so the margin is admissible), the harness arm scored **0.0004075**
and a blind-sampling arm — the same model asked the same question
repeatedly with no criticism, no packs and no scheduler — scored
**0.0135949364055**. Thirty-three times better, for 709 454 tokens
against 702 789 (`experiments/2026-08-25-change-constructive-frontier/RESULTS.md`,
2026-08-25 segment). The harness arm produced exactly **one**
non-degenerate construction in 132 attempts; fourteen of its fifteen
checker-valid constructions scored exactly 0.0.

Five contributing causes, ordered as the request orders them, each tied
to the table that measures it, and each labelled by kind:

- **HARNESS-DESIGN** — the harness did this to itself.
- **MODEL-BEHAVIOR the harness failed to defend against** — the model did
  it, and a defence was available and not built.
- **WIRING NEVER BUILT** — the mechanism that would have caught it does
  not exist in the code at all.

### 2.1 — 41.2 % went to a problem the run invented about its own critic. HARNESS-DESIGN.

Of ARM H's 702 789 tokens, **373 903 (53.2 %) went to the operator's seed
question and 289 676 (41.2 %) went to `audit:ritual`** — "audit the
critic: adjudication-ritual flags sustained (§11.3)", a problem the run
spawned for itself at log seq 345 of 3 200, roughly two cycles in, with
provenance `{"trigger": "audit-critic"}`. It then spawned a second
problem off that one at seq 603. The record splits cleanly on the event:
before seq 345, **100.0 %** of spend was on the seed question; after it,
**48.3 %** (W6 `TABLES.md` T12; `PC1_POSTMORTEM.json`). The competing arm
spent 100 % of a matched budget on the instance, because it has no
mechanism for spawning anything. This is harness design working exactly
as specified and not as anyone would want: CLAUDE.md's invariant that
"the operator's seed question always wins scheduler rank ties" is a
tie-break rule, not a budget floor, and nothing in the record suggests
the tie-break failed. W6 parks this as a question and explicitly refuses
to file it as a defect — *the record shows the allocation; it does not
show that the allocation was wrong* (W6 `PARKED.md` P5) — and that
restraint is preserved here. What the record does establish is that a
self-spawned sub-problem can take two fifths of a run's budget, and that
before this window nobody had measured it.

### 2.2 — 24.6 % of every token ever spent bought output the harness then rejected. HARNESS-DESIGN amplifying MODEL-BEHAVIOR.

Program-wide, **2 694 889 of 10 958 450 tokens (24.6 %) went to calls
whose output was rejected into repair**, at a mean of 5 697 tokens per
rejected call against 3 090 for an admitted one (W6 `TABLES.md` T5;
`FLOW_AGGREGATE.json` → `program_by_outcome`). Inside ARM H itself the
figure is 13.4 % rejected into repair plus 3.2 % discarded outright (W6
`TABLES.md` T12). The model half of this is ordinary: a model
occasionally returns malformed JSON. The harness half is the expensive
part. A repair re-ask sends the model its own rejected JSON back
verbatim — 1 115 875 prompt tokens across 456 re-asks, of which 839 301
are the returned rejected value — and it does not work well: a first ask
succeeds 91.7 % of the time and every subsequent ask on the same work
succeeds about six times in ten and **does not improve with repetition**
(58.5 %, 60.9 %, 58.8 %, 55.6 % at attempt indices 1 through 4). Across
the whole record, 224 repair ladders consume 680 of 3 155 attempts —
**21.6 % of all provider spend** — and hit the grant ceiling 97 times
(W1 `RESULTS.md` §5; W6 `RESULTS.md`, "The repair bill"). The harness
already owns the better move and reaches it only after paying for
failure: decomposition to the atomic form, 96.8 % valid on the harder
sample (§1 row 1 above). The defence was in the building.

### 2.3 — Criticism never once improved a score, because it was never put in front of anything that writes the next candidate. WIRING NEVER BUILT.

This is the finding the whole program turns on. The exact question — *132
candidates, criticism running the whole time, best score frozen: did any
criticism event ever precede a score improvement in the criticised
lineage?* — has an exact answer, and it is **no**. The exact rational
checker finds two best-score events in the entire run, at log seq 320
(score 0.0) and seq 1041 (0.0004075, the run's final best). After seq
1041 the run produced **67 further constructions under 251 further
criticism events and not one scored above zero**. Coupled changes that
improved the score: **0 of 32** on the mechanical reading and **0 of 60**
on the quotation reading (W2 `TABLES.md` §5).

The reason is one line, and it is structural rather than a matter of
critique quality. **0 of 196 model-written attacks across the two newest
large runs were ever shown to a later conjecture dispatch** (W2
`TABLES.md` §3a). The critic wrote well: its attacks name a premise 78 %
and 89 % of the time, offer a counterexample 36 % and 25 %, and quote
their target verbatim and accurately about three times in four (W2
`TABLES.md` §1a, §2a). Seventy-three dispatches across the two runs
declined to attack rather than manufacture a fault. And every one of
those attacks was written to a log and routed nowhere. Meanwhile **every
status any criticism moved in either run was moved by the problem's own
admission criteria** — all 118 attack edges in P-R1 and all 345 in P-C1
come from mechanical commitment verdicts, **0 from a model-written
attack**, and no model-written attack in either run carried a warrant at
all (W2 `TABLES.md` §4). Every criticism dispatch ran under
`observe_only`, the authority mode that cannot mint a warrant, so this
was not a near miss.

The external literature predicted exactly this and named the fix.
`docs/RESEARCH_FINDINGS_Q1Q10_2026-08-22.md` Q5 separates detection,
uptake and repair, and finds the entire difference between a protocol
that works and one that does not is **neglect** — the reviewer's signal
entering a separable advice field the solver can acknowledge and bypass,
versus entering the solver's working context where re-submission requires
the criticism to be **discharged**. Its repair path item 3 is a
structural change, not a prompt change; its item 2 is a warning that
adding an acknowledgment requirement *lowered* accuracy in the tested
setting. The channel Q5 says is load-bearing is the channel this harness
does not have.

**Not local to these two runs, and that matters for the roads in §4.** A
structural sweep over all 60 committed roots that recorded criticism
finds only 250 of 3 901 critic artifacts (6.4 %) were ever exposed to a
conjecturer — but **35 of the 60 roots showed at least one**, and the
July and early-August roots routinely fed criticism back (W2 `TABLES.md`
§6). The channel is not architecturally absent. It is absent in the two
newest and largest runs, and W2 explicitly does not establish whether
that is a regression, a configuration difference, or intended for these
problem shapes.

### 2.4 — At the same written precision, the harness arm was ten times more likely to be collinear. MODEL-BEHAVIOR the harness failed to defend against.

The 89 % invalidity of the harness arm is one field and one geometric
fact. Every invalid candidate failed in the *same* field — the single
free string carrying the construction — and **not one failed a schema
constraint, a type, an enum, or a pointer** (W1 `RESULTS.md`, "the P-C1
headline, attributed"). The form was filled correctly and the content it
carried was degenerate, which is the one failure a wire contract is
structurally unable to catch. **126 of 133 constructions place three or
more points on a shared x or y coordinate.** Three points on a line have
zero area, so the minimum over all 286 triples is zero before anything
else in the construction matters; 129 of 133 (97.0 %) had a true minimum
area of exactly zero, against 14 of 52 (26.9 %) in the sampling arm.

And it is not a precision artifact, which is why "conditioning" is the
right word. Holding written precision fixed — 6-decimal coordinates —
the harness arm wrote them on 42 of 133 constructions and **41 of those
still scored zero**; the sampling arm wrote them on 36 of 52 and only 4
scored zero. **At the same written precision, ten times more likely to be
collinear** (W1 `RESULTS.md`, same section). The difference is which
arrangement was chosen — grids, midpoints, symmetric shells — not how
many digits were written down. The harness arm named the trap
correctly: `avoid-collinearity` appears in all 15 of its valid
candidates. It never named a search — zero mentions of
`greedy-or-local`, `symmetry-breaking` or `min-triangle-targeting`
(`experiments/2026-08-25-change-constructive-frontier/RESULTS.md`, M3).
It diagnosed the problem in words and then placed points on a lattice,
126 times. Nothing in the harness noticed that the same failure mode was
recurring, because nothing in the harness compares a candidate to the
lineage's own history of refutations.

### 2.5 — Two thirds of every diagnosable failure is a handle the model made up, and the record had already told it not to. MODEL-BEHAVIOR the harness failed to defend against.

The record wrote 1 434 diagnostics, 1 178 of which name a specific field.
The five commonest are all fields whose job is to name something that
already exists, and together they are **737 of the 1 178 — 62.6 % of
every failure the record can pin on a field is an invented handle** (W1
`RESULTS.md` §2). The models were not failing to reason inside the form;
they were failing to point at things.

The sharper version is the one that echoes the external note. 257
diagnostics carry `omission_or_unknown_legal: true` — the record told the
seat, in the very message it received, *"Omission is legal... never
invent a handle to fill an optional reference."* **In 255 of those 257 the
seat supplied a handle the record classifies as unknown: a value it
invented for a field it had just been told it could leave out. A coerced
fabrication rate of 99.2 %** (W1 `RESULTS.md` §3; `COERCION_PROBE.json`).
Escape utilisation on the next attempt in the same repair ladder was 7 of
120 — **5.8 %**. `docs/RESEARCH_STRUCTURED_OUTPUT_COERCION_2026-08-22.md`
states the mechanism and the remedy: fabrication concentrates exactly
where hedging is impossible, prompt-level "do not fabricate" instructions
are *voided* by required schemas, and enforcement lives in the schema's
escape road rather than in the prompt. Our own record contains the
confirming contrast: the one enum in the corpus that carries an escape
value *in the vocabulary* — `claim_class: unknown` — gets taken 16 times
in 140. Where the escape exists in the type, models use it; where it
exists only in the instruction text, they do not. The salted-probe
experiment that note parked as expensive turned out to be unnecessary:
the harness had been running the experiment for a month and recording the
answer.

### 2.6 — And one cause that is not on the list, because it does not exist: recombination. WIRING NEVER BUILT.

`docs/RESEARCH_SHAPE_CRITIQUE_2026-08-22.md` §(C) makes the strongest
architectural criticism available and it lands here: a
conjecture–criticism loop is **expansion-only** by construction.
Criticism prunes; it does not recombine. Every candidate in the ledger is
a descendant of a single lineage, and the cited result proves
expansion-only search is confined to a narrow entropy shell that
recombination operators escape. The note's consumption entry records the
gap precisely as our own: the strong succession relation is recombinative
for *frames*, and **no typed rule recombines conjectures across
lineages** — a crossover over the ledger, taking the surviving premises
of one defeated candidate and the structure of another, does not exist.
That is not a defect in anything shipped. It is a mechanism that was
never built, and it is the mechanism that would most directly attack the
failure §2.4 measures: 132 attempts that never left the lattice, with no
operator able to splice the one non-degenerate construction into the
others.

---

## 3. What is refuted, what is unexercised, what works

**Refuted-as-wired is not refuted-in-principle.** Where the record kills
a claim only for the current wiring, that is said in the entry itself.
Two entries below are refuted outright, and they are marked.

### 3.1 — Refuted

1. **"Criticism steers the search."** Refuted **as wired**, on the only
   root that has a run-owned scalar to steer toward: 0 of 32 and 0 of 60
   coupled changes improved the score, with the best score frozen at log
   seq 1041 and 251 further criticism events after it (W2 `TABLES.md`
   §5). Not refuted in principle, and the record says why: the channel
   was shut — 0 of 196 attacks reached a conjecturer (§3a) — so what is
   refuted is *criticism that is recorded and not routed*, which is the
   only kind these runs contained.
2. **"The harness beats blind sampling where a checkable baseline
   exists."** Refuted **on this instance**, by 33× at matched budget
   (`experiments/2026-08-25-change-constructive-frontier/RESULTS.md`).
   Not refuted for other instances, other N, other models, or other
   problem families: one instance, one model, one run per arm, and the
   pre-authorised repeat was never spent. It is, however, a direct
   in-house instance of `RESEARCH_FINDINGS_Q1Q10` Q4's pre-registered
   law — *at matched budget, criticism loses to resampling wherever a
   counting baseline exists* — reproduced on our own machine with an
   exact checker standing in for the counting baseline.
3. **"No defended trial has ever run in this repository."** Refuted
   **outright**. That claim is on `main` today, in
   `experiments/2026-08-25-poietics-program/PARKED.md` P5 under
   "STRENGTHENED 2026-08-25". Re-derived over all 54 roots with no
   "reports the field" filter: `experiments/2026-08-12-live-grounded-extension-expansion/run`
   ran **161 defended trials**, spent 342 judge calls across two model
   families, and **8 trials sustained**, minting 8 argumentative warrants
   that refuted 8 artifacts — half that run's 16 refutations (W4
   `RESULTS.md` segment 1; `trial_sweep.json`). The census that produced
   the wrong answer counted only roots whose summary reports the field,
   which silently excluded the one root that had the field set. W4 parks
   the ERRATA correction; it is not made here.
4. **"The allocation controller steers the run."** Refuted **outright**
   for every committed root: 47 decisions, 0 reaching the wire, and the
   dispatch envelope is a route-declared cap in **every dispatch of all
   54 committed roots** (W5 `RESULTS.md`, "Why steering does nothing").
   The chain of causes is fully in the record and each link was a correct
   fix for the failure in front of it; their composition left the
   controller with no consumer. Note the direction of travel: before the
   E43 fix an ineffective steering decision *killed the run and named
   itself in a typed drop*; after it, the same decision is recorded as a
   successful policy and disappears. **The failure mode changed from loud
   to silent**, which is the worse of the two.
5. **"The bound dossier is the run's evidence base."** Refuted **as
   wired**: 93 % of it was never shown to any model, and no typed
   disclosure marks the truncation (W3 `RESULTS.md` F1). The dossier
   machinery is not refuted — the byte-check works — but a claim that a
   run "considered the attached record" is not supported by these roots.
6. **"212 byte-checked citations means the model quoted the record."**
   Refuted: 146 of 294 refs were bare handles that still return
   `EVIDENCE_CITATION_VERIFIED`, and every verified quote lands inside
   the 160-character preview (W3 `RESULTS.md` F2, F3).
7. **"Prompt-level instructions not to fabricate work."** Refuted on our
   own record, 255 of 257 (W1 `RESULTS.md` §3) — an in-house replication
   of the external note's central claim.
8. **"The truncation flag reports truncation."** Refuted: `truncated` is
   `false` on all 3 155 attempts while the record's own diagnostics
   report a length-limit cut-off 52 times (W1 `RESULTS.md` §8).

### 3.2 — Unexercised

Nothing here is broken. Each is a path that exists, is believed sound,
and has never been driven far enough by a committed run to be tested.

1. **The two-call split leg.** 0 of 3 155 attempts carry a non-empty
   `split_leg`; the three split fields are present on 717 attempts in the
   five newest roots and every one is empty (W6 `TABLES.md` T13). See
   §3.3 item 4 — this is one mechanism seen from two sides, not two
   items.
2. **The E43 lease ceiling.** It can only bind on a *widening* proposal,
   and all 47 decisions in the population are narrowings, because
   truncation and repair rates were 0.0 in every policy artifact's
   evidence block. Proven offline, never fired live (W5 `RESULTS.md`,
   "The E43 ceiling binds nothing here").
3. **The allocation open-loop disclosure.** All nine post-landing roots
   carry `open_loop: []`, so the disclosure path has no live instance to
   adjudicate (W5 `RESULTS.md`, "Open-loop notices").
4. **Recombination across lineages.** Does not exist in the code (§2.6).
5. **Judge form filling at the field level.** 342 rulings with their
   `verdict` and `decisive_point` fields sit in one root's blobs, unread:
   W4 counted what judges *did* and not what they *wrote* (W4 `PARKED.md`
   W4-P4).
6. **The defended-trial road, in 53 of 54 roots.** Four run configs asked
   for `defended_trial`; three of the four builders after the one that
   worked dropped the line, and compile emits **no notice** when a config
   asking for it compiles to a manifest with no criticism policy (W4
   `RESULTS.md` segment 3, mutation-proven by `disclosure_probe.py`).
7. **Criticism authority above `observe_only`.** 492 criticism dispatches
   across the tree carry `observe_only`, and no measured run carries
   anything else (W2 `PARKED.md` P4).
8. **The P-C1 repeat.** Pre-authorised in that tranche's PREREG §7 and
   never spent, so the 33× margin is a single-run margin
   (`experiments/2026-08-25-change-constructive-frontier/RESULTS.md`
   residue 1).
9. **Qualification's token cost.** The battery records cases, repairs and
   verdicts and no tokens at all, so no run's end-to-end cost is
   derivable from its record (W6 `RESULTS.md` residue 1).

### 3.3 — Works

1. **The record machinery.** `verify_root` reports **0 violations** on
   both priority roots. **463 of 463** mechanical commitment verdicts
   re-derive correct with the harness's own evaluator, and — because that
   check is circular by construction — **60 of 60** re-rule correct under
   an independent implementation written from the commitments' own `eval`
   text that **imports nothing from `deepreason`** (W4 `RESULTS.md`
   segment 4). Join health across the whole corpus: **0 of 3 155**
   attempts failed to resolve to their attempt object, 0 key collisions
   (W1 `RESULTS.md`). Every window's instruments reproduce their
   committed outputs byte for byte (W6 `VERIFY.md`, 5 of 5 OK). This is
   the organ that took the most engineering and it is the organ that came
   through clean.
2. **Scratch.** 18.1 % against a 4.3 % control, Fisher exact p = 0.0004,
   with the groups matched on note length and the control carrying *more*
   distinctive wording per note, so the length bias runs against the
   effect (W3 `RESULTS.md` F8). The control is free and rare: 8 roots
   were configured to write notes with retrieval switched off, so their
   notes provably could not be read back and their measured reuse rate
   *is* the test's false-positive rate. The 18.1 % is a floor on textual
   influence, not an estimate of influence — paraphrase is invisible to
   an 8-word verbatim test.
3. **The trial guards.** On their one live outing they turned away **114
   of 122** convened trials: 39 to formal supremacy, 62 to the two model
   families disagreeing, 37 to the defence surviving, 12 to a ruling that
   did not quote the exchange it was given, 22 to a ruling that flipped
   under paraphrase. Eight survived (W4 `FUNNEL.md` leg 2). Against the
   operator's standing caution that judges "prosecute without any
   discernable discrimination", this is the opposite failure mode — and
   W4 is careful that 8 sustained trials out of 122 neither confirms nor
   refutes the caution; it means it now has live evidence to be tested
   against for the first time.
4. **The two-call seat protocol.** Shipped 2026-08-22
   (`experiments/2026-08-22-change-two-call-seat-protocol/DELIVERY.md`):
   a seat call becomes two provider legs against the same route, the same
   lease and the same authorisation, with `B_r + B_a == ceiling` by
   construction so neither leg nor their sum can escape the bound.
   Proven by **22 new regressions plus a full gate at 3 857 passed, 0
   failed**, and by a six-ceiling sweep with a wire-level assertion.
   Nothing refuses: a seat that cannot be split runs as before and
   records a typed notice naming the reason — and that decline path is
   the part with live evidence, firing **96 times** on repair
   authorisations (W6 `TABLES.md` T13). The split leg itself has never
   been taken in a committed run, which is §3.2 item 1; the same
   mechanism is in both lists because the record proves one half and is
   silent on the other.
5. **Form decomposition.** Same model, same seat, same route: 61.9 %
   valid on the composite form over 659 attempts against **96.8 % on the
   atomic form over 339**, on a harder sample by construction (W1
   `RESULTS.md` §1).
6. **The mechanical criticism channel.** Every status that moved in
   either priority run moved because a program computed a verdict on the
   artifact's own bytes, and the commitment it named was in the target's
   interface **463 times out of 463** (W2 `TABLES.md` §2). What moved
   statuses was correct.
7. **Typed refusal discipline.** Fourteen roots emitted citation-shaped
   references with no dossier bound at all, and every attempt was refused
   typed, with the refusal code separating "nothing is bound" from "an
   empty dossier is bound and the ref matches nothing in it". W3 records
   this explicitly as **not** a defect so that a later audit does not read
   the refusal counts as a fault (W3 `PARKED.md` P4-W3-6).
8. **The lossless patch-transport fix.** The class it targeted is down
   **94 %** — 79 attempts losing a repair grant to a spelling before the
   fix's commit timestamp, 5 after — and the five survivors fall into
   three named shapes, one of which the fix's own design document
   predicted and deliberately left (W1 `RESULTS.md` §6).
9. **The efficiency-never-evidence boundary.** Zero violations across all
   nine post-landing roots: no signal emission and no allocation decision
   carried a foreign label change in its own event, and all 30 exemptions
   taken are one controller policy artifact's own status moving in the
   event that created it, which the design permits (W5 `LAW_CHECK.md`).
   W5 states the limit plainly — it is a structural check, not a
   correlation test, and with 27 decision cycles there is no power for
   one.

---

## 4. The roads, priced

**No recommendation is made here.** The decision is the operator's, and
this section exists to make it a one-paragraph decision rather than a
research project. Each road states what it costs in *agent* time
(sessions and tranches, the scarce resource by the operator's own law
that tokens are cheap and the agent is not), what it costs in *provider
tokens*, and what evidence would count as success — stated in advance, so
the answer cannot be moved afterwards.

**How the costs were arrived at.** Token figures are arithmetic on
committed measurements and are labelled as estimates, never as
measurements: a matched-budget arm pair on the P-C1 instance cost
**1 412 243 tokens** in fact (702 789 + 709 454,
`experiments/2026-08-25-change-constructive-frontier/RESULTS.md`), and a
qualification cache miss is budgeted at ~1 160 calls and ~14 minutes
(CLAUDE.md). Agent-session figures are estimates from the size of
comparable tranches in this tree and carry no measurement behind them.

### Road (a) — retire the runtime, keep the method

Stop running the harness. Freeze the code and the 54 roots as artifacts,
and carry forward the practices, which are the part of this project with
the best evidence behind it.

**What transfers,** each with the record that earns it:

- *Type everything meaningful; prose is never evidence.* Every finding in
  this document was possible because the answer was in a typed record.
  Where a channel was typed, the census answered exactly; where it was
  not — internal model attention, what a model did with a note it was
  shown — no instrument here could see it, and W3 says so (R1).
- *The honest ledger.* Every window's RESULTS.md ends in a residue
  section naming what it did not establish, and three windows record a
  mistake they made and corrected rather than quietly fixing it: W1
  reproduced ERRATA E42's own false finding before catching it, W4's
  hand-checker silently dropped a conjunct and now refuses to rule when
  its reconstruction is incomplete, W6 reported a shrinking context pack
  that was an averaging artifact. Those admissions are why the numbers
  above can be trusted.
- *Placebos and controls, in a census.* W2 computes every coupling rate
  twice — once on the candidate after the criticism and once on the
  candidate before it, which cannot have been influenced by it — and
  reports only the difference as evidence; three of the four
  placebo-corrected effects turn out zero or negative. W3 found its
  control for free in eight misconfigured roots. This is the single most
  transferable technique in the tree.
- *Authenticate documents by re-derivation, not authority.* The `check:`
  discipline and `docs_verify --audit`'s refusal of checks that cannot
  fail.
- *Independent re-implementation as the test of a checker.* W4's
  `handcheck.py` imports nothing from the system it checks, which is the
  only reason its 60 of 60 means anything that W2's 463 of 463 did not.
- *The parked-prompt convention.* A finding becomes a paste, not an
  authoring session.

**Agent cost.** Estimated 1–2 sessions: one to write the transfer
document (the practices above, with the incident behind each), one to
merge the two unmerged windows so the citations in this document resolve
on `main`, freeze the tree and record the closure. No code is written.

**Token cost.** Effectively zero — no live run.

**What would count as success.** A single document that a sibling project
can follow without reading this repository, in which every practice names
the recorded incident that taught it —
`docs/LESSONS_LEARNED_2026-08-17.md`'s own standard: *"a lesson with no
incident behind it did not make the list."* Success is checkable and
cheap: the two unmerged branches are on `main`, every citation in this
synthesis resolves, and `docs_verify` is green.

**What is given up.** The two dead channels are never tested, so the
question of whether the idea works when it is actually wired stays open
permanently. The record would then say the harness lost 33× on one
instance with its criticism channel disconnected, which is a much weaker
statement than it will look like in a year.

### Road (b) — rebuild the two dead channels, as a last experiment

Build exactly two things, run one registered test, and let it decide.

**Channel 1 — criticism into the working context, with discharge
required.** Criticism enters the conjecturer's own working context rather
than a separable advice field, and re-submission requires the criticism
to be *discharged* rather than noted. This is
`RESEARCH_FINDINGS_Q1Q10` Q5's repair-path item 3, and it comes with a
warning attached that must be honoured: item 2 records that adding an
*acknowledgment* requirement **lowered** accuracy. Discharge is not
acknowledgment. Two cheap prerequisites land first, both already parked:
W2's P2 (establish why criticism stopped reaching the conjecturer in the
newest runs, when 35 of 60 older roots show it reaching one — regression,
config difference, or by design) and W4's W4-P1 (compile must disclose
that it dropped the criticism authority the config asked for).

**Channel 2 — reference grounding with a first-class absent value.** Give
optional reference fields an escape *in the type* rather than in the
prompt, per `RESEARCH_STRUCTURED_OUTPUT_COERCION`'s recommendation 2 and
W1's P2, and keep measuring: the comparison instrument already exists
(`coercion_probe.py`) and the baseline is CFR 99.2 % / EUR 5.8 %. Two
adjacent items belong in the same tranche because they are the same
mechanism: the dossier's silent truncation must become a typed
disclosure (W3 P4-W3-1), and the citation record must carry whether the
citation was *quoted* (W3 P4-W3-5) so a rerun's citation quality is
readable off the log.

**The registered kill-or-cure test: the P-C1 rematch.** Same instance,
same exact rational checker, same model, matched budget against the same
blind-sampling arm, pre-registered before launch as that tranche's PREREG
was. Four arms, not two, because Q5's own ablation protocol says two
cannot separate a form effect from an interface effect: *no-critique*,
*vacuous-critique* (form only), *real-critique-as-advice*,
*real-critique-in-context-with-discharge*. Arm 2 is the one that keeps
the result honest — without it, a working critic is indistinguishable
from argument-shaped text, and the external record already shows vacuous
reasoning moving 20–39 % of otherwise-resistant agents.

**Agent cost.** Estimated 5–8 sessions: two prerequisites (W2-P2 and
W4-P1), one per channel, one to build the four-arm rig and pre-register
it, one to launch and monitor, one to write the result. Each channel
touches code that a frozen-surface reading must clear first; W1's P2 and
W3's P4-W3-5 both carry that warning explicitly.

**Token cost.** Estimated 2.8–3.5 M provider tokens for four arms at the
P-C1 arm size (~706 K each), plus qualification: a cache miss is ~1 160
calls, and any change to the seat profiles reruns it. Add one repeat of
the winning pair — the thing the first P-C1 tranche pre-authorised and
did not spend — and the estimate is ~4.2 M. At the ratios this program
measured, roughly two thirds of that is prompt-side.

**What would count as success — registered in advance.** The
critique-in-context arm's best checker-confirmed score **strictly
exceeds** the blind-sampling arm's, at a budget ratio inside the same
0.95 floor P-C1 used. Secondary, and required for the result to be
interpretable rather than merely favourable: coupling-minus-placebo is
positive on the mechanical operationalisation, and repair rate — coupled
changes that *improved* the score — is above zero, against the current
0 of 32 and 0 of 60. **What would count as failure:** the in-context arm
does not beat the sampler, *or* it beats it by no more than the
vacuous-critique arm does. Either kills the wiring hypothesis, and the
honest reading of that outcome is that the harness's shape — not its
wiring — is what lost, which points at road (a) or (c).

**The known risk, stated because it is registered against.** Q4's law
says that at matched budget criticism loses to resampling *wherever a
counting baseline exists*, and its stated scope limit is that on
open-ended work no such baseline exists, so the comparison cannot be run
in that form. P-C1 is precisely the case where the baseline *does* exist.
A win on this instance would be a strong result; a loss is the outcome
the external prior already predicts, and it should be priced as the
likely one.

### Road (c) — repoint the harness at record-keeping and verification only

Keep the organ that works and delete the ones that do not. The result is
not a reasoning harness: it is a replayable, verifiable ledger for work
that other processes do.

**What stays.** `log.jsonl` and the typed objects; `verify_root`; the
demonstrative commitment evaluator (463 of 463, and 60 of 60 under an
independent implementation); the wire contracts and their decomposition
path (96.8 % on the atomic form); scratch, which measurably works;
amendment epochs; the token meters, once P1 and P2 from W6 are fixed so a
run's spend is readable and every token sits in exactly one counter.

**What gets deleted.** The allocation controller's cap knobs and the
signal names that feed them — 47 decisions that reached nothing and 79
declared names that never carried a value. The argumentative critic seat
and the criticism dispatch path: 2 639 criticism events across the tree
that moved zero statuses. The judge, defender and variator seats and the
whole trial road, which one root in 54 ever entered. Weigh that last
deletion against what §3.3 item 3 records: on its single outing the trial
road's guards behaved *well*, turning away 114 of 122 trials, and
deleting it discards the only live evidence about judge behaviour this
repository has ever produced. Deleting it is defensible; deleting it
without saying that is not.

**Agent cost.** Estimated 4–6 sessions, and the risk is not in the
deletions themselves but in what they are entangled with. Adjudication,
warrants and attack edges are load-bearing for the demonstrative channel
that *is* kept, so "delete criticism" is not one commit; W5's P1 already
carries the frozen-surface warning that `invariants.py` re-derives the
controller's own envelope to decide what a logged policy authorised, and
that is frozen surface 3.

**Token cost.** Near zero for the work. One live run afterwards, ~700 K
tokens, to demonstrate that a stripped configuration still reaches a
typed terminal with a clean `verify_root`.

**What would count as success.** The full gate green at 0 failed; one new
committed root with a clean `verify_root`, a readable token spend, and no
`observe_only` criticism dispatches in it at all; and — the real test —
the deleted surface stays deleted, meaning no test had to be weakened and
no fixture updated to accommodate a removal. If a deletion forces an
assertion to be relaxed, that deletion was load-bearing and the road is
more expensive than this estimate.

---

## Appendix — every parked prompt from W1–W6

Thirty-two findings, one line each, so nothing found is lost whichever
road is chosen. None was fixed: the program fixes nothing in any window
or round. Each line names its route and where the ready-to-send prompt
lives.

**W1 — forms** (`experiments/2026-08-26-run-anatomy-program/W1-form-census/PARKED.md`)

| id | one line | route |
|---|---|---|
| W1-P1 | The composite conjecturer form loses a third of its calls, and the atomic decomposition it already owns is reached only after paying for failure | `dr-change-orchestrator` |
| W1-P2 | Seats invent a handle 255 times in 257 for fields the record has just told them to omit; give the escape a place in the type | `dr-change-orchestrator` |
| W1-P3 | `attempt_trace[].truncated` is false on all 3 155 attempts while the record diagnoses a length cut-off 52 times | `deepreason-orchestrator` |
| W1-P4 | Three named response spellings still cost a repair grant after the lossless fix cut the class 94 % | `dr-change-orchestrator` |
| W1-P5 | 15 asserted attacks carry no case text, and the judge form has no third verdict — two different problems, do not bundle | `dr-change-orchestrator` |
| W1-P6 | 45.7 % of accepted responses are fenced markdown on seats declaring bare JSON; latent risk, no live cost | `dr-audit-orchestrator`, or park |

**W2 — criticism** (`experiments/2026-08-26-run-anatomy-w2-criticism/PARKED.md`, branch `claude/criticism-anatomy-w2-1z2029`)

| id | one line | route |
|---|---|---|
| W2-P1 | `workflow-semantic-admission-v1.admitted_refs` name ids that exist nowhere in the root; 0 of 163 resolve | `deepreason-orchestrator` |
| W2-P2 | Criticism reached no conjecturer in the two newest runs while 35 of 60 older roots show it reaching one — regression, config, or by design? | `deepreason-orchestrator` |
| W2-P3 | A critic's evidence citations are almost never byte-checked: 55 emitted, 3 checked; the candidate side is checked properly | `dr-audit-orchestrator` |
| W2-P4 | Every criticism dispatch in every measured run is `observe_only`; whether that default should stand is the operator's call | operator question |
| W2-P5 | The criticism wire contract silently accepts a misspelled key (`preise` for `premise`), recording an attack without its premise | `dr-audit-orchestrator` |

**W3 — evidence and scratch** (`experiments/2026-08-26-run-anatomy-w3-evidence-scratch/PARKED.md`, branch `claude/run-anatomy-w3-census-p5pgmb`)

| id | one line | route |
|---|---|---|
| W3-P1 | An attached dossier is silently truncated to 32 citable blocks; 591 of 623 were never shown and nothing says so | `dr-change-orchestrator` |
| W3-P2 | A run can be configured to write scratch it can never read, silently; 8 committed roots are in that state | `deepreason-orchestrator` |
| W3-P3 | `plan_kind="dossier"` names a pack that carries the run's own artifacts, not the attached dossier | `dr-change-orchestrator`, documentation first |
| W3-P4 | The evidence × rules seam — the exact seam W3 measured — has no map document | `dr-change-orchestrator` |
| W3-P5 | The record cannot distinguish a quoted citation from a bare handle; the `quoted` flag exists and is not carried into the event | `dr-change-orchestrator` |
| W3-P6 | **Not a defect**, recorded so nobody re-opens it: models emit citation-shaped refs with no dossier bound, and the harness refused every one, typed | none |

**W4 — the judge road** (`experiments/2026-08-26-run-anatomy-program/W4-judge-road/PARKED.md`)

| id | one line | route |
|---|---|---|
| W4-P1 | Compile silently discards `ENGAGED_CRITICISM_AUTHORITY`: no refusal and no disclosure, which the all-configurations law forbids | `dr-change-orchestrator` |
| W4-P2 | The poietics P5 claim "no defended trial has ever run in this repository" is false and is still on `main`; 161 trials ran | `dr-change-orchestrator`, ERRATA |
| W4-P3 | `poietics-installation-mechanism@v1` misses the operator question's own spelling of the distribution; every verdict correct as specified, the criterion at fault | none — a lesson for the next criteria author |
| W4-P4 | Judge form filling (D6) is unmeasured and now measurable: 342 rulings, 62 ensemble splits, 3 paraphrase flips, all unread | a later RUN ANATOMY window |

**W5 — signals and the controller** (`experiments/2026-08-26-run-anatomy-program/W5-signals-controller/PARKED.md`)

| id | one line | route |
|---|---|---|
| W5-P1 | The allocation controller steers nothing, silently: 47 in-envelope decisions, none reaching a dispatch. **Design-and-stop, three priced roads** | `deepreason-orchestrator` |
| W5-P2 | `controller-update` is declared with a real unit and bound, has no emitter, and its only test asserts its absence | `dr-change-orchestrator` |
| W5-P3 | Four of the five `allocation.POLICY_SIGNALS` are auditable from no record; sequence this after P1 | `dr-change-orchestrator` |
| W5-P4 | `capture14.hysteresis-mode.v1` declares a `cycle` bound and is deliberately relied on for the whole run; the declaration is what is wrong | `dr-change-orchestrator` |
| W5-P5 | Eight Measure tags are emitted 18 151 times and no registry entry declares them; widening the enforcement is what lasts | `dr-change-orchestrator` |
| W5-P6 | The E43 lease ceiling has never been exercised live, and cannot be until P1 is settled | `deepreason-orchestrator`, evidence-generation |

**W6 — token flow** (`experiments/2026-08-26-run-anatomy-program/W6-token-flow/PARKED.md`)

| id | one line | route |
|---|---|---|
| W6-P1 | `run-status.json` reports `token_spend: 0` on all 18 non-terminal roots, and `deepreason results` prints that zero for a 702 789-token run | `deepreason-orchestrator` |
| W6-P2 | `token-accounting.v1` has no field for report-pass tokens; 428 624 tokens across 9 roots sit in no counter, and the boundary is inconsistent between roots | `deepreason-orchestrator` |
| W6-P3 | Qualification spends tokens the record does not carry, so no run's end-to-end cost is derivable | `deepreason-orchestrator` |
| W6-P4 | The pack allocator computes its own per-section accounting — including what the budget dropped — and nothing persists it | `dr-change-orchestrator` |
| W6-P5 | 41.2 % of P-C1 ARM H went to a self-spawned audit problem. **Not a defect and must not be sent as one**; it is a design question about a budget floor | `dr-ask-the-right-question` first |

---

This was a workshop where the tools were true and the logbook could not
be forged, and where the drive belt between the motor and the lathe was
never fitted. The motor ran for three months, the log faithfully recorded
it running, and the work came out the same as if nobody had switched it
on. What this program did was open the cabinet and look at the belt.
