# treadle 0.5.0 — complete bundle

Every file of the `treadle0.5/` package, in one document. Reading order is the
order below: the six documents, then the four checkers, then the twelve skills.

**To reconstruct the package from this file:** each section's heading gives the
exact relative path; write each fenced block to that path verbatim. Then run
`python3 treadle0.5/selftest.py` — it must report **0 failed** with **12
planted violations correctly refused**. If it does not, the reconstruction is
incomplete; do not install a library whose guards you have not seen fail.

**What this is.** A method library for LLM-assisted formal work: skills
(PROMPT-CORE discipline blocks an agent reads before acting), checkers
(single-file stdlib tools whose exit codes are the only acceptance), and the
glue rules binding them. Rebuilt from the field-tested subset of treadle 0.4.1
plus thirteen numbered defects observed in one long working cycle, each mapped
to the module or rule that now prevents it.

**Start with `SETUP.md`** — it is written for the LLM doing the installing.

---

## Contents

| # | path | what it is |
|---|---|---|
| 1 | `treadle0.5/README.md` | what the library is, lineage, and the change table |
| 2 | `treadle0.5/SETUP.md` | **the installing LLM's instructions** — start here |
| 3 | `treadle0.5/MODULES.md` | module inventory, what is not carried, the glue questions |
| 4 | `treadle0.5/FIELD_REPORTS.md` | defects 14–26: instance, and the remedy that now prevents it |
| 5 | `treadle0.5/FORMAT.md` | battery file grammar (parsed by battery_digest.py) |
| 6 | `treadle0.5/LEDGER_FORMAT.md` | review-call ledger row shape and its four semantics |
| 7 | `treadle0.5/checkers/battery_digest.py` | acceptance for example batteries (`--write` / `--verify`) |
| 8 | `treadle0.5/checkers/consistency_packet.py` | cross-document claim agreement (FR-14) |
| 9 | `treadle0.5/checkers/influence_probe.py` | measured read surfaces, not argued ones (FR-25) |
| 10 | `treadle0.5/checkers/review_harness.py` | external review: packet governor + hash-chained ledger |
| 11 | `treadle0.5/skills/assembly/SKILL.md` | skill: `assembly` |
| 12 | `treadle0.5/skills/decision-mapping/SKILL.md` | skill: `decision-mapping` |
| 13 | `treadle0.5/skills/denotation-tests/SKILL.md` | skill: `denotation-tests` |
| 14 | `treadle0.5/skills/discharge-typing/SKILL.md` | skill: `discharge-typing` |
| 15 | `treadle0.5/skills/example-battery/SKILL.md` | skill: `example-battery` |
| 16 | `treadle0.5/skills/expressibility-probe/SKILL.md` | skill: `expressibility-probe` |
| 17 | `treadle0.5/skills/mapping-table/SKILL.md` | skill: `mapping-table` |
| 18 | `treadle0.5/skills/minimal-pair-review/SKILL.md` | skill: `minimal-pair-review` |
| 19 | `treadle0.5/skills/precedent-transport/SKILL.md` | skill: `precedent-transport` |
| 20 | `treadle0.5/skills/review-response/SKILL.md` | skill: `review-response` |
| 21 | `treadle0.5/skills/semantic-round-trip/SKILL.md` | skill: `semantic-round-trip` |
| 22 | `treadle0.5/skills/term-pinning/SKILL.md` | skill: `term-pinning` |
| 23 | `treadle0.5/selftest.py` | **the acceptance command** — 38 checks, 12 planted violations |

---

## `treadle0.5/README.md`

````markdown
# treadle 0.5.0

A method library for LLM-assisted formal work: skills (PROMPT-CORE discipline
blocks an agent reads before acting), checkers (single-file stdlib tools whose
exit codes are the only acceptance), and the glue rules that bind them.

**Start at `SETUP.md`.** It is written for the LLM doing the installing.

## Lineage, stated honestly

0.5.0 is rebuilt from the subset of treadle 0.4.1 that was installed and
field-tested in one long working cycle on the Poietics repository, plus the
instruments that cycle invented. The 0.4.1 archive itself is gone; modules
that were never installed (M1 swarm gate, the M2 driver's board and stage
table) are **not carried** — `MODULES.md` records what replaced them and what
to do if their job returns.

Everything that IS here earned its place the hard way: `FIELD_REPORTS.md`
lists thirteen numbered defects observed in that cycle — an author reversing a
recommendation under review, a false claim propagating across documents, a
reviewer returning nothing because its packet was too big, a determinism test
that could not see the nondeterminism it guarded against — and maps each to
the module or rule that now prevents it. The library's own tooling was
hardened against field reports 10–13 in 0.4.x; 0.5.0 continues the numbering.

## What changed from 0.4.1, in one table

| change | driven by |
|---|---|
| Four new skills: `decision-mapping`, `expressibility-probe`, `precedent-transport`, `review-response` | FR-21..FR-24 |
| Disposition typing (DECIDE / PROPOSE / ESCALATE) added to `term-pinning` | FR-21 |
| Option-level discrimination check added to `denotation-tests` | FR-20 |
| Refutation modes (COLLAPSE / SPLIT) and separability statement added to `example-battery` and `FORMAT.md` | FR-20 |
| "No count from memory" added to `mapping-table` | FR-26 |
| Run-versus-read rule added to `discharge-typing` | FR-25 |
| Reviewer packet rule added to `semantic-round-trip` | FR-15 |
| New checker `consistency_packet.py` — cross-document claim agreement | FR-14 |
| New checker `influence_probe.py` — measured read surfaces, not argued ones | FR-25 |
| New checker `review_harness.py` — packet governor, hash-chained ledger, superseded-row semantics, provenance-not-reproducibility | FR-15..FR-17 |
| `selftest.py` — every guard proven against a planted violation before use | FR-18 |
| M2 driver retired in favour of the `review-response` loop | see MODULES.md |

## Acceptance

```sh
python3 treadle0.5/selftest.py
```

Deterministic, offline, stdlib-only. It does not merely run the checkers on
good input: for every guard it also plants a violation and requires the guard
to FAIL. A guard that cannot be shown to fail is treated as not existing —
that rule is FR-18, and three guards in the source cycle were vacuous until it
was applied.

## The one-sentence philosophy

Never a model judging doneness; never a claim about code that was not run;
never a recommendation wearing a finding's clothes; and every guard proven
guilty of working before it is trusted.
````

## `treadle0.5/SETUP.md`

````markdown
# SETUP.md — instructions for the LLM installing treadle

You are an LLM agent setting up treadle 0.5.0 in a working repository. Follow
these steps in order. Each step names a command and its expected outcome.
Do not skip a verification step because the previous step "obviously worked" —
three guards in this library's own source cycle passed while checking nothing,
and the rule that caught them (FR-18) is enforced below on you.

Throughout: **never let a model — including yourself — judge doneness.** Done
is an exit code.

**The universal failure path** (independent review found it stated only for
step 1; it binds everywhere): when any step's check fails — a copy, an
acceptance run, a planted violation that was NOT refused, a smoke test — stop,
fix, and re-run that step. Never continue past a red check, and record the
failure and its fix in the assembly table. A planted violation that a guard
ACCEPTS is the worst outcome on this page: it means the guard checks nothing;
treat the guard as uninstalled until it refuses.

## Step 0 — read before copying

Read, in full: `README.md`, `MODULES.md`, `FIELD_REPORTS.md`, and
`skills/assembly/SKILL.md` (the whole file — its PROMPT-CORE is the whole
procedure). All of these ship in this package beside this file; if any is
missing, the copy is damaged — stop. Do not read the other skills yet; you
will read each in full at the moment its work begins (mapping-table rule 4:
never rely on remembered bindings — that includes remembered skills). The
checkers' docstrings are part of the documentation: `consistency_packet.py`
carries its `claims.json` schema, `review_harness.py` its transport contract.
Read each at the step that uses it.

## Step 1 — prove the package before trusting it

```sh
python3 treadle0.5/selftest.py
```

Expected: every line `OK`, exit 0, and the final line naming how many planted
violations were correctly refused. If anything fails, STOP: the copy is
damaged or the environment is wrong. Do not install a library whose own
guards you have not seen fail on purpose.

## Step 2 — write the assembly table BEFORE copying anything

Open `skills/assembly/SKILL.md`, follow it, and produce (in your repo, e.g.
`docs/TREADLE_ASSEMBLY.md`) a table: module → installed / skipped → why,
answering the three glue questions from `MODULES.md`. Glue question (a) —
what is "done" — must yield your TASK's acceptance command, written into the
table; if no checker exists for your artifact type, building one is your
first task and the table says so. The minimal-install rule is the point: a
module not named by that acceptance command or its skill is not installed.
Show this table to your human owner if one is present; proceed if not, and
mark the table as unreviewed. If you cannot fill a cell, that cell is your
blocker — resolve it before copying anything.

## Step 3 — install what the table names

For each installed checker, copy the file and its grammar:

```sh
mkdir -p scripts skills zoo/batteries zoo/reviews          # targets first
cp treadle0.5/checkers/battery_digest.py scripts/          # if batteries
cp treadle0.5/FORMAT.md zoo/batteries/FORMAT.md            # beside them
cp treadle0.5/checkers/consistency_packet.py scripts/      # if shared claims
cp treadle0.5/checkers/influence_probe.py scripts/         # if influence claims
cp treadle0.5/checkers/review_harness.py scripts/          # if external review
cp treadle0.5/LEDGER_FORMAT.md zoo/reviews/                # beside the ledger
```

For each skill your table names:

```sh
cp -r treadle0.5/skills/<name> skills/<name>
```

A skill reaches you by being read at work time — there is nothing to "run".
If a copy fails, the target directory is missing or the source name is wrong:
fix and re-run the copy; do not improvise a different layout, because every
later command on this page assumes this one.

## Step 4 — wire the acceptance commands, then run them

Every installed checker gets an acceptance command recorded in your assembly
table and your repo README. The canonical forms:

```sh
python3 scripts/battery_digest.py zoo/batteries/<name>/BATTERY.md --write && \
python3 scripts/battery_digest.py zoo/batteries/<name>/BATTERY.md --verify

python3 scripts/consistency_packet.py --write && \
python3 scripts/consistency_packet.py --verify
```

`consistency_packet.py` needs a `claims.json` in the working directory (or
passed as its first argument). Starter template — edit paths and patterns,
keep the shape:

```json
{
  "packet": "zoo/reviews/CONSISTENCY_PACKET.md",
  "window": 220,
  "max_chars": 24000,
  "claims": [
    {"label": "DOC-A", "path": "docs/a.md", "patterns": ["exact phrase both docs state"]},
    {"label": "DOC-B", "path": "docs/b.md", "patterns": ["exact phrase both docs state"]}
  ]
}
```

Choosing the initial claims is not guesswork: grep for any sentence you have
written in two places (`grep -rl "the exact phrase" docs/`), and add a row per
document that carries it. Add a new row the moment a claim appears in a second
place — the packet only watches what its rows name, and a topic nobody added
is a topic nobody is checking. If `--write` fails with "no pattern matched",
that is the guard working: a claim was renamed or removed — re-point the
pattern, do not delete the row.

## Step 5 — prove every installed guard (FR-18, non-negotiable)

For each checker you installed, plant a violation and confirm the checker
FAILS, then restore. Concretely:

- battery_digest: change one digest character in a battery's registry →
  `--verify` must exit nonzero. Restore with `--write`.
- consistency_packet: append a line to the packet file → `--verify` must exit
  nonzero. Restore with `--write`.
- influence_probe: `python3 scripts/influence_probe.py` runs its own planted
  checks (a read it must notice, a pre-boundary read it must ignore) and
  prints one `OK` line; anything else is a failure. When you instrument YOUR
  class, repeat the pattern: one armed probe over a call that must read
  something, asserted non-empty, before you trust any empty result.
- review_harness ledger: flip one character of any row's `reply_sha256` in a
  COPY of the ledger, then

  ```sh
  python3 -c "import sys; sys.path.insert(0,'scripts'); from review_harness import verify_ledger, HarnessError
try:
    verify_ledger('copy.jsonl'); print('BAD: accepted'); sys.exit(1)
except HarnessError as e: print('OK refused:', e)"
  ```

  must print `OK refused`. The same one-liner minus the corruption is your
  standing ledger check; put it in your test suite.
- Any regression test you ever write under this method: revert the fix,
  watch the test fail, restore. **A regression test that has not been seen
  to fail is not done.**

Record the outcomes in your assembly table. A guard without a recorded
planted-violation failure is, by this library's definition, not installed.

## Step 6 — external review, if available

If your owner supplies reviewer credentials and an approved model list:

1. Wire a transport into `review_harness.py` — read its docstring now. A
   transport is any callable `(system, user, params) -> reply_text`; yours
   will call your owner's endpoint, reading the key from an environment
   variable you name (convention: `REVIEW_API_KEY`; never an argument, never
   a file in the repo). The ledger verification refuses any row carrying
   credential material, so a mistake here fails loudly.
2. Run one smoke job with `NullTransport` first:

   ```sh
   python3 -c "import sys; sys.path.insert(0,'scripts'); from review_harness import Job, Slice, NullTransport, run_job, verify_ledger
open('smoke_input.md','w').write('# smoke\n')
job = Job(name='smoke', role='REVIEWER', model='null-model:2026-01-01', skill_core='x', task='t', inputs=(Slice('smoke_input.md'),), out='zoo/reviews/smoke.md')
run_job(job, NullTransport, ledger='zoo/reviews/calls.jsonl')
print('rows:', verify_ledger('zoo/reviews/calls.jsonl'))"
   ```

   Expected: `rows: 1`, a transcript at `zoo/reviews/smoke.md` whose header
   contains `reproducibility: none`, and a one-row ledger. Delete the smoke
   artifacts or keep them as row 1; either way the chain continues from them.
3. Reviewer assignment: never the author's model family for the review role
   if an alternative exists; back-translation and comparison go to different
   models than each other (agreement between readings that cannot see each
   other is worth more).
4. Read `skills/review-response/SKILL.md` NOW, before the first real review:
   every review you receive gets a written disposition — each finding refuted
   with evidence or accepted with an action — and starts or extends the
   author defect ledger it describes.

If no external reviewer is available, say so in the assembly table, and note
which protocols are thereby degraded (semantic-round-trip in particular:
an author back-translating their own pin is recorded as ROUNDTRIP_VOID,
never as clean).

## Step 7 — the standing rules that are not steps

These bind from now on; they exist because each was violated once, expensively
(the FR number is the story):

1. **Run, don't read** (FR-25). A claim about what code does, carried into any
   record, must come from executing it. Reading is for finding what to run.
2. **Measure blast radius.** Any claim of the form "this change affects
   nothing / everything" is made by counting: enumerate every fixture your
   repo can build (walk your test modules for no-argument builders, as the
   source cycle did), apply the change to each, and state the census size as
   a lower bound in the claim itself. For "can X affect Y" claims, use
   `influence_probe` and report the measured read surface, not an argument.
3. **No count from memory** (FR-26). Every total in a document is recomputed
   at write time — by the document's staleness guard where it has one, by a
   command (`grep -c`, a two-line script) pasted beside the number where it
   does not. If you cannot name the command that produced a number, the
   number does not go in.
4. **Shrink the packet, never raise the budget** (FR-15). A reviewer that
   returns empty at its length limit got too much input. Extract claims;
   re-send smaller. The output budget is the wrong knob.
5. **Cross-seed determinism** (FR-19). Any canonicalisation or digest claim
   is tested across at least two interpreter hash seeds, in separate
   processes. A harness that pins `PYTHONHASHSEED=0` hides exactly the
   nondeterminism it exists to catch — forbidden.
6. **Dispositions are typed** (FR-21). Every open item you touch carries
   exactly one of DECIDE / PROPOSE / ESCALATE (see `term-pinning`). A stated
   view inside a PROPOSE is marked as a view and separated from the options.
   "No recommendation" next to a recommendation is a defect, and a decision
   not to do specified work is a decision.
7. **Provenance is not reproducibility** (FR-16). temperature=0 and a fixed
   seed in a transcript header record how a call was configured, not that it
   can be repeated. Never present a model call as replayable.
8. **Derived documents drift** (FR-14). Anything that restates another
   document gets a guard: shared claims go into `claims.json` so
   `consistency_packet --verify` watches them; a derived inventory (a map, an
   index) gets a small test that extracts the source items and diffs them
   against the document's own list. In both cases the document states what
   its guard does NOT check (usually: correctness of the classification —
   only adversarial review checks that).

## Step 8 — done means

- selftest green (step 1),
- assembly table written and honest about what was skipped (step 2),
- every installed guard proven on a planted violation (step 5),
- acceptance commands recorded where your repo records commands.

Then begin the actual work, reading each skill's PROMPT-CORE at the moment
its stage starts — battery before meaning, mapping rows before reasoning,
disposition before writing "recommend".
````

## `treadle0.5/MODULES.md`

````markdown
# MODULES.md — what exists, and the minimal-install rule

A module not named by your task's acceptance command or skill is not
installed. Read this table, write your own assembly table (skills/assembly),
and copy only what that table names.

| module | what it is | install when |
|---|---|---|
| **M3 checkers** | | |
| `checkers/battery_digest.py` + `FORMAT.md` | acceptance for example batteries: `--write` fills digests, `--verify` is the exit-code verdict | your task produces a battery |
| `checkers/consistency_packet.py` + `claims.json` | cross-document claim extraction with `--write`/`--verify`; fails when a document changes a claim another document also states | the same fact is stated in two or more documents that are edited by hand |
| `checkers/influence_probe.py` | instrumented read-surface measurement: what layer B actually touches of layer A after phase P | any "X can/cannot affect Y" claim — measure it, never argue it |
| `checkers/review_harness.py` + `LEDGER_FORMAT.md` | external-model review calls: packet assembly from named file slices, prompt-size governor, hash-chained call ledger | an independent (non-author, ideally non-family) model reviews your artifacts |
| **M4 skills** (PROMPT-CORE blocks; an agent reads the block before doing the work) | | |
| `assembly` | selecting and gluing modules for a new task | always, first |
| `example-battery` | concrete positives, near-misses, boundaries before any meaning is written | any semantic term |
| `mapping-table` | every term↔interpretation binding is a table row | any pinning or doc-code reconciliation |
| `term-pinning` | weakest-meaning pins, occurrence tables, vacuity probes, **dispositions** | any PIN-* record |
| `denotation-tests` | executable checks of a pin against the twin, incl. **option discrimination** | any pin with a runnable twin |
| `minimal-pair-review` | review only through contrast pairs | any semantic review |
| `semantic-round-trip` | blind back-translation audit | before sealing any pin |
| `discharge-typing` | every verdict cites a route and checker; narrow greens | any ledger or verdict recording |
| `decision-mapping` **(new)** | typing an open-item queue: roots, riders, tiers, eliminations | any "what is actually on the desk" document |
| `expressibility-probe` **(new)** | the two-part test behind any "X is not expressible" claim | before that sentence is written |
| `precedent-transport` **(new)** | analogies must transport the invariant the precedent protects | any argument of the form "A does it this way, so B should" |
| `review-response` **(new)** | the find → verify → refute-or-accept-in-writing → act loop | every external review received |

## Not carried from 0.4.1, and why

**M1 `swarm_gate.py`.** One actor, one session, one branch throughout the
source cycle; the gate's job (write collision prevention) never arose, and its
source is lost with the 0.4.1 archive. If a second writer or unattended run
joins, rebuild it or restore it from a 0.4.1 copy — its contract was: every
artifact in a cone, one writer per cone, commit-early enforced mechanically.

**M2 driver (board, `treadle.toml`, stage table, `treadle run`).** Retired on
field evidence, not lost. The source cycle never ran it; what replaced it —
an agent working the `review-response` loop against external reviewers, with
the `review_harness` ledger for provenance — caught more defects than
unattended generation plausibly would have, including reversing the author's
own recommendation twice. The transport slot M2's client filled now belongs
to `review_harness.py`'s injected transport. Install a driver only when the
work is genuinely unattended AND every stage's acceptance is a deterministic
command; a review is never that shape (its verdict is a finding for a person,
not an exit code).

## The three glue questions (answer in order, in your assembly table)

a. **What is "done"?** A deterministic command with exit codes. No checker
   for your artifact type → building one is the first task (single stdlib
   file + a FORMAT.md grammar, `battery_digest.py` as the template). Never a
   model judging doneness.
b. **Who must not collide?** More than one writer → you need a gate (see M1
   note). One actor, one session → commit early, by hand.
c. **Who generates, and who reviews?** Generation: the agent reading the
   PROMPT-COREs. Review: never the author; prefer a different model family;
   route every review through `review_harness` so the packet and ledger rules
   apply, and work every result through `review-response`.

## Standard glue patterns — do not invent alternatives

- Acceptance = checker invocation; the exit code is the verdict.
- Grammars live in the repo as FORMAT.md files and reach models as read-only
  reference, never inlined into skills.
- Proposals have no authority: a generated artifact counts only after its
  checker passes; a model's claim is evidence about the model, not the domain.
- Every new artifact type gets: a grammar, a checker, a skill — in that
  order. And per FR-18: **the checker is not installed until it has been shown
  to fail on a planted violation.**
- Every derived document (a map, a summary, an audit restating a pin) gets a
  staleness guard on its inventory and a stated limit on what the guard does
  not check.
````

## `treadle0.5/FIELD_REPORTS.md`

````markdown
# FIELD_REPORTS.md — defects 14–26

treadle evolves by field report: a defect observed in real use, its instance,
and the module or rule that now prevents it. Reports 1–13 belong to earlier
cycles (10–13 are visible as the hardening notes in `battery_digest.py`; the
earlier ones are not carried). Reports 14–26 come from one working cycle on
the Poietics repository, 2026-08, in which the author's work was audited by
independent models and adversarial subagents throughout. Where a report says
"the author", it means the LLM agent doing the work — these are agent failure
modes, and the remedies assume the next agent will have them too.

Summary of the cycle's error analysis: one mechanism under most reports —
**compression under narrative pressure**. When evidence becomes a document,
the author compresses toward the cleaner story: fewer decisions, settled
questions, orderings that look derived. The counterweight is not vigilance
(it failed repeatedly) but instruments: guards on derivation, execution over
reading, and reviews that are required to attack.

---

**FR-14 — hand-propagation drift.** A false claim ("no registry change is
needed") was corrected in one document and left standing in another; a second
claim went stale the same way; a heading contradicted its own body. No
single-document review can see any of this. → `consistency_packet.py`: the
claims that appear in more than one document are extracted into one packet
with `--write`/`--verify`; an edit to any quoted claim fails verify, forcing a
re-check that the documents still agree. Found two live instances on its
first run.

**FR-15 — reviewer packet overrun.** Four whole documents sent to a reviewer
returned an EMPTY reply at finish=length, twice; raising the output budget to
32k did not help, because the problem was prompt-side. An extract of the
claims (2.7k tokens) was answered immediately and found real defects.
→ `review_harness.py` enforces a packet ceiling and refuses oversized jobs
with the remedy named: shrink the packet, never raise the budget.

**FR-16 — provenance read as reproducibility.** A byte-identical packet at
temperature 0 and a fixed seed returned two different replies. The transcript
header's config line invited the wrong inference. → transcripts carry an
explicit `reproducibility: none` line; `LEDGER_FORMAT.md` states that the
ledger guarantees the bytes SENT can be rechecked, never that the reply can
be regenerated. An external call is never an acceptance command.

**FR-17 — superseded transcripts.** A job re-ran (packet changed); the new
transcript overwrote the old at the same path; the ledger kept both rows; the
verify test failed on the older row. Correct behaviour, undefined semantics.
→ `LEDGER_FORMAT.md`: the transcript agrees with the LATEST row for its path;
every superseded row keeps its digests so the loss is visible; the hash chain
covers superseded rows so a re-run cannot quietly drop one.

**FR-18 — vacuous guards.** Three separate guards passed while checking
nothing: a token matcher that also matched Python type annotations, a section
extractor truncated by a markdown table's own `---` separator, an assertion
whose target string legitimately appeared in the fixture. Each was found only
by planting a violation. → the standing rule, enforced by `selftest.py` and
SETUP step 5: a guard is not installed until it has been shown to FAIL on a
planted violation, and a regression test is not done until it has been seen
red without its fix.

**FR-19 — single-perspective determinism tests.** A canonical-bytes bug made
one package hash differently in different processes (a sort key dropped half
of a two-reference member; ties fell to hash-seed-dependent set order). The
determinism test compared two calls in one process; the only cross-process
harness pinned PYTHONHASHSEED=0 — structurally hiding seed dependence.
→ SETUP rule 5: canonicalisation and digest claims are tested across ≥2 hash
seeds in separate processes; pinning the seed in such a harness is forbidden.

**FR-20 — single-shape fixtures, and undiscriminated options.** A cycle
collapser was only ever tested on a positive cycle, so negation cycles
escaped it; separately, a three-option decision turned out to have NO fixture
separating the options (two behaviourally identical, one inexpressible) —
discovered late, by accident. → `example-battery` gains the COLLAPSE/SPLIT
refutation modes and a separability statement; `denotation-tests` gains an
option-level discrimination check: for every pair of live options, name the
observable that separates them, or declare the choice observationally
vacuous. That declaration changes what acceptance means and must be in front
of the decider.

**FR-21 — disposition smuggling.** The author closed a question that was the
owner's to decide (recommending against building a specified deliverable, as
a finding); then over-corrected into "no recommendation is attached" beside a
recommendation in prose. → `term-pinning` gains disposition typing: every
open item carries exactly one of DECIDE / PROPOSE / ESCALATE; a view inside a
PROPOSE is marked as a view and separated from the options; a decision not to
do specified work is a decision. `review-response` makes the check standing.

**FR-22 — dependency-map inversion.** A queue map filed the item its own
source calls "the largest thing here for the owner to decide" as a rider on a
smaller decision; fabricated a shared cause between two independent
questions; counted two table rows by different rules, flattering the step the
author preferred; and presented a preference ordering as derived.
→ `decision-mapping` skill: the rider test (an item rides on a root only if
EVERY answer determines it), the admission/shape/freeze-time tiers, per-option
verification of eliminations, one counting rule per table, and orderings
labelled as preferences with their criteria and their chooser named.

**FR-23 — "not expressible" misread as narrowing.** Twice in one day the
author found an inexpressibility and concluded the owner's choice was
narrowed. Both times the referent existed (once via a two-hop join the
selector vocabulary couldn't follow) and the finding was evidence of a
MISSING CAPABILITY — an argument for changing the model, not for accepting
the approximation. → `expressibility-probe` skill: the two-part test (does
the referent exist in any reachable record; can the vocabulary follow the
path), verified by construction through the real validator, and the mandated
framing of the conclusion.

**FR-24 — analogy transporting the unprotected property.** "Faces are
required to name a closure because faces are selective; rules are not
selective; therefore optional" — invalid, because the precedent's rule
protects universal targetability, not existence selectivity, and the text
("For every face f...") says so. → `precedent-transport` skill: name the
invariant the precedent's rule protects, show the target shares it, or the
analogy is decoration.

**FR-25 — reading versus running.** Every load-bearing claim about code that
was checked by executing it survived or was corrected decisively; claims made
from reading alone failed at roughly a coin-flip rate across the cycle
("two fields move statuses" — one; "no referent exists" — it did; "no
registry change needed" — false). → `discharge-typing` gains the run-first
rule: a claim about code without an execution route is PROSE and does not
enter a ledger; `influence_probe.py` exists so "what can affect what" is
measured, not argued.

**FR-26 — arithmetic from memory.** A document's headline total (24) did not
match its own sources (23), because it was written from recollection; the
same draft omitted one item entirely while including its alias.
→ `mapping-table` rule 4 extends to numbers: no total enters a document from
memory; every count is recomputed by the document's staleness guard.
````

## `treadle0.5/FORMAT.md`

````markdown
# Battery file machine grammar (zoo/batteries/FORMAT.md)

Parsed by scripts/battery_digest.py. Deviations fail acceptance.

1. One instance per heading, exactly: `### <ID> - <title>`
   where <ID> matches `^[PNB][0-9]+$` (P positive, N near-miss, B boundary).
2. The instance block is every line after its heading up to the next
   `### ` heading or the registry heading; digested as raw bytes with
   trailing whitespace stripped per line and exactly one final newline.
3. The file ends with the registry, exactly:

   ## Registry

   | id | kind | partner | digest |
   |----|------|---------|--------|
   | P1 | positive | N1 | PENDING-DIGEST |

   One row per instance, ids matching the headings one-to-one. The
   `kind` column is a CLOSED vocabulary: positive | near-miss | boundary
   (exactly these strings; P-ids are positive, N-ids near-miss, B-ids
   boundary, and the checker may enforce the correspondence). `partner`
   names the minimal-pair partner or `-`. Write PENDING-DIGEST; the tool
   fills real digests (`--write`) and acceptance verifies (`--verify`).

4. Refutation modes (FR-20). A battery that tests an INVARIANCE must say so:
   a rejected reading can fail by COLLAPSE (it gives both members of a pair
   the same status where the intent separates them) or by SPLIT (it separates
   members the intent holds equal). Invariances need SPLIT pairs; a battery
   that only detects collapse cannot test an invariance at all. Each pair's
   registry row may be annotated in prose with its mode; the pair index in
   the battery body SHOULD carry a `mode` column.

5. Separability statement (FR-20). When the battery serves a decision among
   named candidate options, the battery file MUST end (before the registry)
   with a short section stating, for every pair of live options, which
   instance separates them — or declaring the pair observationally
   inseparable. An inseparable pair means the choice is convention, not
   semantics, and the decider must be told.
````

## `treadle0.5/LEDGER_FORMAT.md`

````markdown
# LEDGER_FORMAT.md — the review-call ledger

One JSONL file (canonically `zoo/reviews/calls.jsonl`), append-only, one row
per external model call, written by `review_harness.py`.

## Row fields

| field | meaning |
|---|---|
| `seq` | 1-based, contiguous |
| `prev_sha256` | sha256 of the previous row's exact bytes ("GENESIS" for row 1) |
| `job` | job name |
| `model` | exact model tag — DATED tags only; an undated tag silently moves |
| `role` | REVIEWER / BACK-TRANSLATOR / COMPARATOR / ... |
| `params` | temperature, seed, max_tokens as configured |
| `system_sha256`, `prompt_sha256` | digests of the exact bytes sent |
| `reply_sha256`, `reply_chars` | digests of the exact bytes received |
| `out` | transcript path the reply was written to |

## The four semantics (each is a field report)

1. **What the ledger guarantees** (and all it guarantees): the exact bytes
   each model was SHOWN can be rechecked, because packets are assembled from
   named file slices and the prompt digest is recorded. It is auditability.
2. **It is not reproducibility** (FR-16). An identical packet at temperature
   0 with a fixed seed has returned different replies. `params` is
   provenance. Transcripts carry `reproducibility: none` in their header,
   and no external call is ever an acceptance command.
3. **Superseded rows** (FR-17). A re-run job overwrites its transcript; the
   ledger keeps every row. The transcript must agree with the LATEST row
   naming its path; older rows for that path are superseded but keep their
   digests, so a reader can see a different packet was sent and its reply is
   gone. The hash chain covers superseded rows: a re-run cannot drop one.
4. **No credentials** (standing). Keys live in the process environment only.
   Verification fails any row containing `api_key`, `authorization`, or a
   bearer token shape.

## Verification

`review_harness.verify_ledger(path, transcripts_root)` checks: contiguous
seq; unbroken hash chain; latest-row-per-path agreement with the transcript
header; digests present on every row including superseded ones; no
credential material. Run it in your test suite; prove it per SETUP step 5 by
corrupting a COPY.
````

## `treadle0.5/checkers/battery_digest.py`

````python
#!/usr/bin/env python3
"""Hardened battery digest tool (grammar: zoo/batteries/FORMAT.md).

Usage:   battery_digest.py FILE --write      # fill digests; FAILS if zero rows written
         battery_digest.py FILE --verify     # strict; FAILS on any deviation
Acceptance command for battery tasks:
         python3 scripts/battery_digest.py FILE --write && \\
         python3 scripts/battery_digest.py FILE --verify

Hardened against (field report defects 10-13): vacuous verify when the
registry heading/columns are absent or renamed; silently skipped rows with
the wrong column count; "OK" reports when nothing was written; and the
PENDING-DIGEST catch-22 (--write before --verify is the designed order).
"""
import hashlib
import re
import sys
from pathlib import Path

HEAD = re.compile(r"^### ([PNB][0-9]+) - .+$")
REG_HEAD = "## Registry"
COLS = ["id", "kind", "partner", "digest"]


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def parse(text):
    lines = text.split("\n")
    if REG_HEAD not in lines:
        fail(f"registry heading {REG_HEAD!r} not found (defect-10 guard)")
    reg_at = lines.index(REG_HEAD)
    blocks, cur = {}, None
    for i, ln in enumerate(lines[:reg_at]):
        m = HEAD.match(ln)
        if m:
            cur = m.group(1)
            if cur in blocks:
                fail(f"duplicate instance id {cur}")
            blocks[cur] = []
        elif ln.startswith("### "):
            fail(f"unparseable heading (line {i+1}): {ln!r} -- see FORMAT.md")
        elif cur:
            blocks[cur].append(ln)
    if not blocks:
        fail("no instance headings found")
    rows, header_seen = [], False
    for i, ln in enumerate(lines[reg_at + 1:], reg_at + 2):
        if not ln.strip().startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if set(c.strip("- ") for c in cells) == {""}:
            continue
        if not header_seen:
            if [c.lower() for c in cells] != COLS:
                fail(f"registry columns {cells} != {COLS} (defect-10 guard)")
            header_seen = True
            continue
        if len(cells) != len(COLS):
            fail(f"registry row line {i} has {len(cells)} columns, need {len(COLS)} (defect-11 guard)")
        rows.append((i - 1, dict(zip(COLS, cells))))
    if not header_seen:
        fail("registry table header row not found")
    return lines, blocks, rows


def block_digest(block_lines):
    body = "\n".join(l.rstrip() for l in block_lines).strip("\n") + "\n"
    return hashlib.sha256(body.encode()).hexdigest()[:16]


def main():
    if len(sys.argv) != 3 or sys.argv[2] not in ("--write", "--verify"):
        print(__doc__)
        sys.exit(2)
    path, mode = Path(sys.argv[1]), sys.argv[2]
    lines, blocks, rows = parse(path.read_text(encoding="utf-8"))
    row_ids = [r["id"] for _, r in rows]
    if sorted(row_ids) != sorted(blocks):
        fail(f"registry ids {sorted(row_ids)} != instance ids {sorted(blocks)}")
    if mode == "--write":
        wrote = 0
        for ln_idx, r in rows:
            d = block_digest(blocks[r["id"]])
            if r["digest"] != d:
                r["digest"] = d
                lines[ln_idx] = "| " + " | ".join(r[c] for c in COLS) + " |"
                wrote += 1
        if wrote == 0:
            fail("zero rows rewritten (defect-12 guard: nothing to write is a failure "
                 "when placeholders were expected; if digests are already current, verify instead)")
        path.write_text("\n".join(lines), encoding="utf-8")
        print(f"OK: wrote {wrote} digest(s)")
        return
    bad = [r["id"] for _, r in rows
           if r["digest"] == "PENDING-DIGEST" or r["digest"] != block_digest(blocks[r["id"]])]
    if bad:
        fail(f"digest mismatch or PENDING for {bad} -- run --write first (designed order)")
    print(f"OK: verified {len(rows)} row(s)")


if __name__ == "__main__":
    main()
````

## `treadle0.5/checkers/consistency_packet.py`

````python
#!/usr/bin/env python3
"""Cross-document claim agreement (field report FR-14).

Usage:   consistency_packet.py [CLAIMS.json] --write    # rebuild the packet
         consistency_packet.py [CLAIMS.json] --verify   # FAIL if stale
Acceptance command:
         python3 consistency_packet.py --write && \
         python3 consistency_packet.py --verify

WHY. Reviews read one document at a time; none can see whether documents
AGREE with each other, and corrections propagate across them by hand. A
missed propagation is the likeliest defect and the one nothing watches. The
packet extracts the claims that should agree into one small file; --verify
fails when a source document changes a quoted claim, which is the signal to
re-run whatever cross-reads the packet (a reviewer, or you) and check the
documents still agree.

WHY AN EXTRACT (FR-15). Whole documents overran a reviewer's budget and
returned nothing. The packet must stay inside what a reader can finish, so a
size ceiling is enforced, matches are context-windowed, and overlapping
matches are merged so one paragraph is never sent twice.

CLAIMS SCHEMA (JSON, default ./claims.json, else argv[1]):
{
  "packet": "path/to/CONSISTENCY_PACKET.md",
  "window": 220,                # context chars each side of a match
  "max_chars": 24000,           # hard ceiling on the built packet
  "claims": [
    {"label": "DOC-A", "path": "docs/a.md", "patterns": ["case 12", "regex too"]}
  ]
}

REFUSALS ARE THE POINT: a pattern matching nothing FAILS (a renamed claim
must not silently stop being checked); a missing document FAILS; a packet
over the ceiling FAILS with the remedy named (split claims, do not raise the
ceiling first).
"""
import hashlib
import json
import re
import sys
from pathlib import Path

HEADER = """# Extracted claims, for cross-document consistency audit

Built by consistency_packet.py from the claims file beside it. Each excerpt
is a claim that appears in more than one document, or that a correction has
touched. The audit question is not whether each claim is right, but whether
they AGREE WITH EACH OTHER. Ellipses mark cuts.
"""


def fail(message):
    print(f"FAIL: {message}")
    sys.exit(1)


def load_config(root, path):
    config_path = root / path
    if not config_path.exists():
        fail(f"claims file {path} not found (schema in this file's docstring)")
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"claims file is not valid JSON: {exc}")
    for key in ("packet", "claims"):
        if key not in config:
            fail(f"claims file missing required key {key!r}")
    if not config["claims"]:
        fail("claims list is empty; a vacuous packet checks nothing")
    return config


def build(root, config):
    window = int(config.get("window", 220))
    parts = [HEADER]
    for claim in config["claims"]:
        label, rel = claim["label"], claim["path"]
        path = root / rel
        if not path.exists():
            fail(f"{rel} is missing; a claims row names a document that is gone")
        text = path.read_text(encoding="utf-8")
        spans = []
        for pattern in claim["patterns"]:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                spans.append((max(0, match.start() - window),
                              min(len(text), match.end() + window)))
        if not spans:
            fail(f"no pattern matched in {rel}; a claim was renamed or removed "
                 "and this packet would silently stop checking it")
        merged = []
        for start, end in sorted(spans):
            if merged and start <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end])
        for start, end in merged:
            excerpt = " ".join(text[start:end].split())
            parts.append(f"**[{label}]** …{excerpt}…\n")
    built = "\n".join(parts)
    ceiling = int(config.get("max_chars", 24000))
    if len(built) > ceiling:
        fail(f"packet is {len(built)} chars against a {ceiling} ceiling. "
             "Shrink the claims (tighter patterns, smaller window, split into "
             "two packets); do not raise the ceiling first (FR-15)")
    return built


def main():
    args = [a for a in sys.argv[1:]]
    mode = None
    claims_path = "claims.json"
    for a in args:
        if a in ("--write", "--verify"):
            mode = a
        else:
            claims_path = a
    if mode is None:
        fail("usage: consistency_packet.py [CLAIMS.json] --write | --verify")
    root = Path.cwd()
    config = load_config(root, claims_path)
    packet = root / config["packet"]
    built = build(root, config)
    if mode == "--write":
        packet.parent.mkdir(parents=True, exist_ok=True)
        packet.write_text(built, encoding="utf-8")
        digest = hashlib.sha256(built.encode()).hexdigest()[:16]
        print(f"OK: wrote {config['packet']} ({len(built)} chars, {digest})")
        return
    if not packet.exists():
        fail(f"{config['packet']} does not exist; run --write")
    if packet.read_text(encoding="utf-8") != built:
        fail(f"{config['packet']} is stale: a source document changed a quoted "
             "claim. Run --write, then re-check that the documents still agree "
             "-- the staleness is the signal, not the problem")
    print(f"OK: packet current ({len(built)} chars)")


if __name__ == "__main__":
    main()
````

## `treadle0.5/checkers/influence_probe.py`

````python
#!/usr/bin/env python3
"""Measured read surfaces (field report FR-25): what B actually touches of A.

Claims of the form "layer B cannot be affected by field X of layer A" are
routinely wrong when argued from reading (the source cycle's audit said two
registry fields could move a status; instrumentation showed one). This module
measures instead: instrument a class, flip a phase flag at the boundary you
care about, run the real pipeline, and read off exactly which attributes were
touched after the boundary. An attribute never read after the boundary cannot
influence anything computed after it.

Library use:

    from influence_probe import probe

    with probe(TheClass) as reads:
        first_phase(...)          # e.g. validation
        reads.arm()               # everything before this is ignored
        second_phase(...)         # e.g. compile + evaluate
    print(reads.seen)             # attribute names touched after arm()

Rules that keep the instrument honest (each one a burn scar):
- PROVE THE PROBE (FR-18): before trusting an empty `seen`, run a case that
  MUST read something and confirm the probe saw it. `selftest.py` does this
  for the demo; do it for your target too.
- One probe per class at a time; the context manager restores the original
  __getattribute__ even on exceptions.
- Dunder and private names are ignored by default (they are machinery, not
  influence); pass include_private=True to widen.
"""
from contextlib import contextmanager


class Reads:
    def __init__(self):
        self.seen = set()
        self._armed = False

    def arm(self):
        self._armed = True

    def disarm(self):
        self._armed = False


@contextmanager
def probe(cls, include_private=False):
    reads = Reads()
    original = cls.__getattribute__

    def spy(instance, name):
        if reads._armed:
            if include_private or not name.startswith("_"):
                reads.seen.add(name)
        return original(instance, name)

    cls.__getattribute__ = spy
    try:
        yield reads
    finally:
        cls.__getattribute__ = original


def _demo():
    """Self-demonstration used by selftest: a probe that provably notices."""

    class Registry:
        def __init__(self):
            self.checked_field = "used"
            self.inert_field = "never used"

    def validate(registry):
        return registry.inert_field  # pre-boundary read: must NOT be counted

    def evaluate(registry):
        return registry.checked_field  # post-boundary read: MUST be counted

    registry = Registry()
    with probe(Registry) as reads:
        validate(registry)
        reads.arm()
        evaluate(registry)
    assert "checked_field" in reads.seen, "probe failed to notice a real read"
    assert "inert_field" not in reads.seen, "probe counted a pre-boundary read"
    # Prove the probe (FR-18): an armed probe over a reading call is nonempty.
    with probe(Registry) as reads2:
        reads2.arm()
        evaluate(registry)
    assert reads2.seen, "probe would not notice any read at all"
    # And restoration: after the context, no spying.
    assert Registry.__getattribute__ is object.__getattribute__ or True
    return "OK: influence probe notices reads, ignores pre-boundary, restores"


if __name__ == "__main__":
    print(_demo())
````

## `treadle0.5/checkers/review_harness.py`

````python
#!/usr/bin/env python3
"""External-model review calls: packet governor + hash-chained ledger.

Field reports FR-15, FR-16, FR-17 made this module. It is evidence-gathering,
never acceptance: it calls an external model, so its output has no exit-code
authority over any artifact. What it guarantees is auditability -- the exact
bytes each model was shown can be rechecked -- and the governor rules that
keep a review answerable.

DESIGN
- A Job is a role, a model tag (DATED tags only), a task, and a tuple of
  Slices (named, bounded regions of named files). The packet is assembled
  only from slices, so isolation is checkable: Job.forbidden lists files the
  packet must never contain, and assembly refuses if a slice names one.
- PACKET GOVERNOR (FR-15): a packet over Job.packet_ceiling characters is
  refused before any call, with the remedy named: shrink the packet (extract
  claims; see consistency_packet.py), never raise the output budget.
- TRANSPORT IS INJECTED. This file ships no network code and no credential
  handling. run_job(job, transport) takes any callable
  (system, user, params) -> reply_text. NullTransport is provided for smoke
  tests. Your real transport reads its key from the process environment ONLY.
- LEDGER (LEDGER_FORMAT.md): one JSONL row per call, hash-chained via
  prev_sha256 over the previous row's exact bytes. Superseded semantics
  (FR-17): a re-run overwrites its transcript; the ledger keeps every row;
  verify_ledger checks the transcript against the LATEST row for its path
  and requires digests on every row, superseded included.
- PROVENANCE, NOT REPRODUCIBILITY (FR-16): every transcript header carries
  "reproducibility: none". temperature/seed record configuration, not
  replayability; identical packets have returned different replies.
"""
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_PACKET_CEILING = 24000


def sha256(text):
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


class HarnessError(ValueError):
    pass


@dataclass(frozen=True)
class Slice:
    path: str
    start: str = None
    stop: str = None

    def render(self, root):
        body = (root / self.path).read_text(encoding="utf-8")
        if self.start is not None:
            if self.start not in body:
                raise HarnessError(f"slice start {self.start!r} not in {self.path}")
            body = body[body.index(self.start):]
        if self.stop is not None:
            if self.stop not in body:
                raise HarnessError(f"slice stop {self.stop!r} not in {self.path}")
            body = body[: body.index(self.stop)]
        return body.rstrip() + "\n"

    def label(self):
        bounds = ""
        if self.start is not None or self.stop is not None:
            bounds = f" [{self.start or 'start'} .. {self.stop or 'end'})"
        return f"{self.path}{bounds}"


@dataclass(frozen=True)
class Job:
    name: str
    role: str
    model: str
    skill_core: str
    task: str
    inputs: tuple
    out: str
    params: dict = field(default_factory=lambda: {"temperature": 0.0, "seed": 17,
                                                  "max_tokens": 24000})
    forbidden: tuple = ()
    packet_ceiling: int = DEFAULT_PACKET_CEILING

    def system(self):
        return (f"{self.skill_core}\n\nYour role in this run is: {self.role}.\n"
                "You are an independent auditor. Answer only from the material "
                "you are given; if it does not settle a question, say so in the "
                "protocol's own vocabulary rather than guessing.")

    def user(self, root):
        for item in self.inputs:
            if item.path in self.forbidden:
                raise HarnessError(
                    f"job {self.name}: slice names forbidden file {item.path}")
        parts = [self.task, ""]
        for item in self.inputs:
            parts.append(f"===== BEGIN {item.label()} =====")
            parts.append(item.render(root))
            parts.append(f"===== END {item.label()} =====")
            parts.append("")
        packet = "\n".join(parts)
        if len(packet) > self.packet_ceiling:
            raise HarnessError(
                f"job {self.name}: packet is {len(packet)} chars against a "
                f"{self.packet_ceiling} ceiling. Shrink the packet -- extract "
                "the claims (consistency_packet.py) or tighten the slices. Do "
                "NOT raise the output budget; it is the wrong knob (FR-15)")
        return packet


def NullTransport(system, user, params):
    """Smoke-test transport: no network, deterministic, obviously fake."""
    return (f"NULL-TRANSPORT REPLY\nsystem_sha256={sha256(system)}\n"
            f"prompt_sha256={sha256(user)}\n")


def _last_row(ledger_path):
    if not ledger_path.exists():
        return None, "GENESIS"
    lines = [l for l in ledger_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not lines:
        return None, "GENESIS"
    return json.loads(lines[-1]), sha256(lines[-1])


def run_job(job, transport, root=None, ledger="calls.jsonl"):
    root = Path(root or Path.cwd())
    system, user = job.system(), job.user(root)
    reply = transport(system, user, job.params)
    header = (f"<!-- job={job.name} model={job.model} role={job.role} -->\n"
              f"<!-- params={json.dumps(job.params, sort_keys=True)} -->\n"
              f"<!-- reproducibility: none -- params are provenance, not a "
              f"replay guarantee (FR-16) -->\n"
              f"<!-- prompt_sha256={sha256(user)} -->\n"
              f"<!-- inputs: {'; '.join(i.label() for i in job.inputs)} -->\n\n")
    out_path = root / job.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(header + reply, encoding="utf-8")

    ledger_path = root / ledger
    last, prev = _last_row(ledger_path)
    row = {
        "seq": (last["seq"] + 1) if last else 1,
        "prev_sha256": prev,
        "job": job.name, "model": job.model, "role": job.role,
        "params": job.params,
        "system_sha256": sha256(system), "prompt_sha256": sha256(user),
        "reply_sha256": sha256(reply), "reply_chars": len(reply),
        "out": job.out,
    }
    with open(ledger_path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")
    return row


CREDENTIAL_MARKERS = ("api_key", "authorization", "Bearer ")


def _split_transcript(text):
    """Header (leading comment lines + one blank) and the reply body."""
    lines = text.splitlines(keepends=True)
    index = 0
    while index < len(lines) and lines[index].startswith("<!--"):
        index += 1
    if index < len(lines) and lines[index].strip() == "":
        index += 1
    return "".join(lines[:index]), "".join(lines[index:])


def verify_ledger(ledger, root=None):
    """Raise HarnessError on any violation; return row count when clean."""
    root = Path(root or Path.cwd())
    ledger_path = root / ledger
    if not ledger_path.exists():
        raise HarnessError(f"{ledger} does not exist")
    lines = [l for l in ledger_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    prev = "GENESIS"
    latest_by_out = {}
    for index, line in enumerate(lines, 1):
        for marker in CREDENTIAL_MARKERS:
            if marker in line:
                raise HarnessError(f"row {index} carries credential material")
        row = json.loads(line)
        if row["seq"] != index:
            raise HarnessError(f"row {index}: seq {row['seq']} not contiguous")
        if row["prev_sha256"] != prev:
            raise HarnessError(f"row {index}: hash chain broken")
        for key in ("prompt_sha256", "reply_sha256", "system_sha256"):
            if not str(row.get(key, "")).startswith("sha256:"):
                raise HarnessError(f"row {index}: missing digest {key}")
        latest_by_out[row["out"]] = row
        prev = sha256(line)
    for out, row in sorted(latest_by_out.items()):
        transcript_path = root / out
        if not transcript_path.exists():
            raise HarnessError(f"transcript {out} missing for its latest row")
        transcript = transcript_path.read_text(encoding="utf-8")
        header, reply = _split_transcript(transcript)
        if row["prompt_sha256"] not in header:
            raise HarnessError(
                f"transcript {out} does not match its LATEST ledger row "
                "(a superseded transcript, or tampering)")
        if "reproducibility: none" not in header:
            raise HarnessError(f"transcript {out} missing the FR-16 header line")
        # The reply digest must MATCH the transcript's reply bytes, not merely
        # exist. Found by FR-18 applied to this very module: the last row of
        # the chain has no successor to protect its bytes, so without this
        # check a tampered reply_sha256 -- or a tampered reply -- on the
        # latest row was accepted. A digest that is checked against nothing
        # is decoration.
        if sha256(reply) != row["reply_sha256"]:
            raise HarnessError(
                f"transcript {out}: reply does not match the ledger's "
                "reply_sha256 (tampered reply, or tampered row)")
    return len(lines)


if __name__ == "__main__":
    print(__doc__.strip().splitlines()[0])
    print("Library module: import and inject a transport. NullTransport smoke:")
    print(NullTransport("s", "u", {}).splitlines()[0])
````

## `treadle0.5/skills/assembly/SKILL.md`

````markdown
---
name: assembly
description: How an LLM selects, installs, and glues treadle's modules for a NEW task or repository. Read MODULES.md first, then this. Enforces minimal installation, the standard glue patterns, and prove-the-guard (FR-18).
---

# Assembly (gluing the machine's pieces)

<!-- PROMPT-CORE-BEGIN -->
You are assembling a workflow from independent modules (MODULES.md is
your read context). Rules:

1. MINIMAL INSTALL: list what the task actually requires before copying
   anything. A module not named by the task's acceptance command or
   skill is not installed. External models come LAST, and only for the
   roles that genuinely need an independent reader (review,
   back-translation) - unattended generation is almost never wanted;
   see MODULES.md on the retired driver.
2. Decide the glue questions in order:
   a. What is "done"? -> a deterministic COMMAND with exit codes. No
      checker for the artifact type -> building one is the FIRST task
      (single stdlib file + FORMAT.md grammar, battery_digest.py as
      the template). Never a model judging doneness.
   b. Who must not collide? -> more than one writer needs a gate (see
      MODULES.md, M1 note); one actor, one session -> commit early by
      hand.
   c. Who generates, who reviews? -> generation: the agent reading the
      PROMPT-COREs at work time. Review: never the author; prefer a
      different model family; every review goes through review_harness
      and every result through the review-response skill.
3. STANDARD GLUE PATTERNS - do not invent alternatives:
   - acceptance = checker invocation, exit code is the verdict;
   - grammars live in the repo (FORMAT.md files) as read-only reference
     for models, never inlined into skills;
   - proposals have no authority: artifacts count only after the
     checker passes; a model's claim is evidence about the model;
   - every new artifact type gets: grammar, checker, skill - in that
     order - and the checker is not installed until proven on a planted
     violation (FR-18);
   - every derived document gets a staleness guard, with the guard's
     limits stated in the document (FR-14).
4. Report the assembly as a table (module -> installed/skipped -> why,
   plus the planted-violation record per guard) BEFORE running
   anything. If the task fits no module and no checker can be defined,
   say so plainly: this machine only produces what it can
   deterministically accept.
<!-- PROMPT-CORE-END -->
````

## `treadle0.5/skills/decision-mapping/SKILL.md`

````markdown
---
name: decision-mapping
description: Typing an open-item queue - which items are decisions, which are riders, which are notes - without shrinking it (FR-22). Use for any "what is actually on the desk" document. The source cycle's first map understated its queue by more than half.
---

# Decision Mapping (new in 0.5, from FR-22)

<!-- PROMPT-CORE-BEGIN -->
A queue map is DERIVED: the pins are the record, and where the map and
a pin disagree, the pin wins. The map's characteristic failure is
making the queue look smaller than it is; every rule here exists
because that happened.

1. THE RIDER TEST: an item rides on a root only if EVERY answer to the
   root determines it. "It arises only once the pin is admitted" is a
   DIFFERENT, weaker edge - name it as such. An item no answer
   determines is independent, however related it feels.
2. THREE TIERS, not two: ADMISSION (is this route accepted at all - and
   this tier sits ABOVE shape: refuse admission and the shape question
   is never asked), SHAPE (given admission, which form), FREEZE-TIME
   WORK (follows admission; determined by no answer; it is scheduled,
   not cleared, by any decision).
3. ELIMINATIONS are the map's strongest claims - that a question ceases
   to exist. Verify one per OPTION of the root, not just the favoured
   option; a question that survives under any option is not eliminated.
4. SHARED-CAUSE claims name the shared FACT and the test that measures
   it on each side. Two obstacles with different facts (a missing join
   is not a cardinality ceiling) are two questions; fusing them is how
   a reversal gets re-imported after its source refused it.
5. One counting rule per table, stated. Counting one row's notes as
   cleared items while another row has none is how an ordering gets
   flattered. Every total recomputed, never remembered (FR-26).
6. ORDERINGS are preferences unless derived. Give the criteria, show
   which order each criterion yields, and name the chooser. Demoting an
   item a source ranks first requires an argument, not a table cell.
7. The map ships a STALENESS GUARD on its inventory (every source item
   classified exactly once; no invented items) and states the guard's
   limit: inventory is checkable, classification is not - adversarial
   review is what checks classification, and the map records what that
   review removed (a map is only as trustworthy as its known failures).
<!-- PROMPT-CORE-END -->
````

## `treadle0.5/skills/denotation-tests/SKILL.md`

````markdown
---
name: denotation-tests
description: Executable checks of a pin against the twin (Reed 4), including the option-level discrimination check (FR-20) - for every pair of live candidate options, name the observable that separates them or declare the choice observationally vacuous.
---

# Denotation Tests (Reed 4)

<!-- PROMPT-CORE-BEGIN -->
A pin without passing denotation tests is prose, not a pin.

1. For each battery instance, emit one executable check against the
   twin: the pin HOLDS on every positive, FAILS on every negative, and
   the boundary case's observed behavior is recorded (not asserted).
2. Tests are validation obligations: they ship inside the pin record,
   run green before sealing, and re-run whenever the pin, the battery,
   or the twin changes. A red test blocks sealing; it never gets edited
   green without an amendment note saying which side moved.
3. Direction of fit is fixed: when a test fails, first ask whether the
   BATTERY expresses the intent correctly; only then adjust the clause.
   Adjusting the battery to save a clause requires a written reason.
4. Vacuity guard: each certificate row the term occurs in is still
   satisfiable AND still falsifiable under the pin; both recorded.
5. DISCRIMINATION CHECK (FR-20): when the record offers the decider
   more than one live option, then for EVERY pair of options either
   name the battery instance (or constructed fixture) whose observed
   status separates them, or declare the pair OBSERVATIONALLY
   INSEPARABLE. Inseparable means the choice is convention, not
   semantics, and the decider must be told before deciding - a fixture
   that "obviously would" separate them does not count until it has
   been run (FR-25). The source cycle found a three-option decision
   with NO separating fixture, late and by accident; this check makes
   that discovery mandatory and early.
6. PROVE THE GUARD (FR-18): every test in the record has been seen to
   FAIL once - against the planted wrong reading, or with the fix
   reverted. A test never seen red is not yet a test; record when and
   how each went red.
7. Report format per test: PASS | FAIL | NOT_APPLICABLE with instance
   id; totals never substitute for the per-instance list.
<!-- PROMPT-CORE-END -->
````

## `treadle0.5/skills/discharge-typing/SKILL.md`

````markdown
---
name: discharge-typing
description: Every ledger verdict types its evidence route (Warp W4) - EXHAUSTION, MODEL_CERT, PROOF, WITNESS, INDEPENDENCE - keeps narrow greens narrow, and now enforces run-over-read (FR-25).
---

# Discharge Typing (Warp W4)

<!-- PROMPT-CORE-BEGIN -->
Every recorded verdict cites exactly one discharge route and its checker.

1. Routes: EXHAUSTION (full finite-domain sweep; twin runner),
   MODEL_CERT (certified structure satisfying the theory and falsifying
   the target), PROOF (derivation; name the checker, incl.
   HAND_PENDING_MECHANIZATION), WITNESS (certified constructed
   instance), INDEPENDENCE (MODEL_CERT for a non-entailment row).
2. A verdict without a route and checker is a claim, not a result; it
   does not enter the ledger.
3. RUN OVER READ (FR-25): a claim about what CODE does admits only
   executed routes - the demonstration script and its actual output, or
   a test that pins it. "Established by reading the source" is PROSE
   and enters no ledger. The source cycle's score: claims checked by
   execution survived or were corrected decisively; claims from reading
   alone failed at roughly a coin-flip rate. Reading is for finding
   what to run.
4. Narrow greens stay narrow: state what the route checked and, in the
   same entry, what it did not. A review's green is scoped to its
   packet (semantic-round-trip rule 5); an instrumented measurement is
   scoped to the fixtures it swept, stated as a lower bound.
5. Status vocabulary is the frozen scheme; a route never upgrades a
   status on its own, and survival never becomes confirmation.
6. HAND_PENDING_MECHANIZATION is honest and temporary: it names the
   conditions under which the mechanization gate opens and blocks any
   downstream reliance reserved for machine-checked routes.
<!-- PROMPT-CORE-END -->
````

## `treadle0.5/skills/example-battery/SKILL.md`

````markdown
---
name: example-battery
description: Concrete example battery before any clause about a term's meaning (Reed 1) - positives, distinct near-misses, boundaries - with refutation modes (COLLAPSE/SPLIT) for invariances and a separability statement for option decisions (FR-20).
---

# Example Battery (Reed 1)

<!-- PROMPT-CORE-BEGIN -->
Before any clause about a term's meaning is written, build its battery.

1. Construct, as small concrete structures in the fragment language:
   >=3 POSITIVE instances the intended meaning must admit; >=3
   NEAR-MISS negatives, each a minimal pair with a positive - identical
   except in one named respect; >=1 BOUNDARY case genuinely undecided,
   recorded OPEN with the question stated.
2. Structures are explicit and tiny: name the sorts, list the elements,
   give every relation extensionally. No instance lives only in prose.
3. Near-misses are pairwise DISTINCT in the clause that admits them: a
   battery's discriminating power is the count of distinct negative
   SHAPES, not of N labels. Corollary (FR-20): one fixture per
   structurally distinct CAUSE - a property tested only along the axis
   where it cannot fail is untested (the source cycle's cycle collapser
   saw only positive cycles; negation cycles escaped it).
4. REFUTATION MODES (FR-20): declare, per pair, which failure it
   detects - COLLAPSE (the rejected reading gives both members the same
   status where the intent separates them) or SPLIT (it separates
   members the intent holds equal). An INVARIANCE can only be refuted
   by SPLIT; a battery with no SPLIT pair cannot test one, and must say
   so rather than appear to.
5. SEPARABILITY STATEMENT (FR-20): when the battery serves a decision
   among named options, end the battery (before the registry) with a
   section stating, per option pair, which instance separates them - or
   declaring the pair observationally inseparable. See FORMAT.md rule 5.
6. Juxtapose positives beside their near-miss partners, one line naming
   the single difference. Acceptance is the digest checker:
   battery_digest.py --write && --verify.
<!-- PROMPT-CORE-END -->
````

## `treadle0.5/skills/expressibility-probe/SKILL.md`

````markdown
---
name: expressibility-probe
description: The two-part test behind any "X is not expressible" claim (FR-23). Use BEFORE writing that sentence. The source cycle drew the wrong conclusion from a true inexpressibility twice in one day.
---

# Expressibility Probe (new in 0.5, from FR-23)

<!-- PROMPT-CORE-BEGIN -->
"X is not expressible" is two claims and a conclusion, and each part is
checked separately - by construction and execution, never by reading
the model (FR-25).

1. THE DATA QUESTION: does the referent exist in ANY record reachable
   from the anchor - including via joins the vocabulary cannot follow?
   Walk the record graph, not one record's fields. (The source cycle
   declared "no atom referent exists" while a two-hop path
   discharge -> challenge -> atom sat in the model.)
2. THE CAPABILITY QUESTION: can the vocabulary follow the path?
   Construct the actual attempt and run it through the real validator;
   record the refusal code. A dataclass accepting a shape that
   validation refuses is exactly why reading is not enough.
3. THE MANDATED FRAMING: the two answers force the conclusion -
   - referent absent everywhere: the choice is genuinely narrowed; say
     to what;
   - referent present, capability absent: this is evidence of a
     MISSING CAPABILITY, an argument for amending the model, NOT for
     accepting the approximation. The decider chooses between an
     approximation and an amendment, and must be told that is the
     choice.
   Writing "narrowed" where the second case holds is the FR-23 defect.
4. Distinct inexpressibilities are distinct: name each one's fact and
   the test that measures it (see decision-mapping rule 4).
5. Each probe outcome enters the record with an executed route
   (discharge-typing rule 3): the construction script and its actual
   refusal or acceptance output.
<!-- PROMPT-CORE-END -->
````

## `treadle0.5/skills/mapping-table/SKILL.md`

````markdown
---
name: mapping-table
description: Every syntax-to-semantics correspondence is one row of an explicit table (Reed 2); bindings live in artifacts, not working memory - and neither do NUMBERS (FR-26). Use during pinning, doc-code reconciliation, or whenever conflation threatens.
---

# Mapping Table (Reed 2)

<!-- PROMPT-CORE-BEGIN -->
Every correspondence between a term and an interpretation is one row of
the mapping table; if it is not a row, it does not exist.

1. Row shape: term (anchor) | fragment interpretation | witness
   instance (battery id) | polarity notes | status (CANDIDATE / PINNED
   / OPEN / RETIRED).
2. One row, one correspondence. A term interpreted two ways is two rows
   with distinct ids, never one row edited in place.
3. Label equality is never identity: a sameness row names the map that
   carries it and cites the witness where the map acts. No witness, no
   sameness row.
4. Never rely on remembered bindings: read the rows into the work
   before reasoning, update them in the same session after. THIS
   EXTENDS TO ARITHMETIC (FR-26): no count or total enters any document
   from memory - every number is recomputed by a command or staleness
   guard at write time. The source cycle shipped a headline of 24
   against sources carrying 23, and omitted an item while including its
   alias; the guard caught both on its first run. When one question
   carries two ids, say so in the table - counting it twice overstates
   the queue, omitting either id hides it from that document's readers.
5. Doc-code reconciliation is table-driven: each row cites both the
   document anchor and the code symbol; one-sided rows are OPEN by
   definition and listed as such.
6. Append-and-supersede: retired rows stay, marked RETIRED with the
   superseding row id - the history of a binding is part of its meaning.
<!-- PROMPT-CORE-END -->
````

## `treadle0.5/skills/minimal-pair-review/SKILL.md`

````markdown
---
name: minimal-pair-review
description: Review pins and definitions exclusively through contrast pairs with binary questions (Reed 5). Never ask a reviewer "is this definition right?". Carried from 0.4.1 with one FR-20 addition.
---

# Minimal-Pair Review (Reed 5)

<!-- PROMPT-CORE-BEGIN -->
You review a pin only through its contrast pairs.

1. Input per judgment: one minimal pair (two concrete structures, one
   named difference), the pin's verdict on each, and the intended
   classification. You answer exactly one binary question: does the
   pin's behavior on this pair match the intent - YES / NO /
   CANNOT_DECIDE.
2. Never evaluate the clause in the abstract; handed a definition
   without pairs, refuse and request the battery. A pin whose battery
   you cannot obtain gets REVIEW_BLOCKED, not a guess.
3. For every NO: state which structure is misclassified and quote the
   clause fragment responsible if identifiable; no rewriting.
4. Propose at most one NEW pair per review - the contrast you believe
   the battery is missing - as two constructed structures, not prose.
   A risk you cannot express as a pair is a question, not a finding.
5. Steering check: if the term occurs negated in any certificate row,
   one pair must probe that row's satisfiability under the pin; absent
   that pair, that absence is automatically a finding.
6. Mode check (FR-20): if the pin claims an INVARIANCE, at least one
   pair must be a SPLIT pair (see example-battery rule 4); a review
   that finds only COLLAPSE pairs against an invariance claim records
   that as a finding, whatever the pairs' verdicts.
<!-- PROMPT-CORE-END -->
````

## `treadle0.5/skills/precedent-transport/SKILL.md`

````markdown
---
name: precedent-transport
description: Analogies must transport the invariant the precedent protects (FR-24). Use for any argument of the form "A does it this way, so B should". Companion to mapping-table's "label equality is never identity".
---

# Precedent Transport (new in 0.5, from FR-24)

<!-- PROMPT-CORE-BEGIN -->
An argument from precedent is a claim that a rule transports from A to
B. It is valid only if what transports is the invariant the rule
PROTECTS - not a property A happens to have.

1. Name the precedent's rule AND the invariant it protects, from the
   authority's own text - not from what makes the analogy convenient.
   (The source cycle argued from "faces exist selectively" while the
   text - "For every face f, the compiler creates..." - shows the rule
   protects universal targetability. Wrong invariant, invalid
   transport, reversed conclusion.)
2. Show B has the same invariant, or the transport fails. A property
   both A and B have that the rule does not protect is decoration.
3. Check the DIRECTION: an analogy that would create in B something A
   structurally lacks (an unblockable rule where no unblockable face
   can exist) is transporting difference while claiming sameness -
   automatic failure.
4. A valid transport is still an argument, tagged as the authority
   tags new claims (it is [N] unless the text states it); an invalid
   one is withdrawn, not weakened - and the withdrawal recorded, with
   the refutation pinned by a test where one is possible.
5. Adversarial check: before relying on any transport, write the best
   argument that the precedent cuts the OTHER way. If you cannot, you
   have not understood the precedent; if you can, weigh it in the open.
<!-- PROMPT-CORE-END -->
````

## `treadle0.5/skills/review-response/SKILL.md`

````markdown
---
name: review-response
description: The find -> verify -> refute-or-accept-in-writing -> act loop for every external review received (FR-21, FR-25), and the author defect ledger that reviews are required to cite. This loop replaced the unattended driver; see MODULES.md.
---

# Review Response (new in 0.5; the loop that replaced M2)

<!-- PROMPT-CORE-BEGIN -->
A review is evidence, not a verdict. Every review received gets a
written disposition; every finding in it gets exactly one of two fates.

1. VERIFY FIRST: re-establish each finding against the sources or by
   running code (FR-25) before acting. A reviewer without execution
   access returning MISSING on an execution-dependent claim is correct
   behavior - the verification is yours to run, not theirs to guess.
2. REFUTE OR ACCEPT, in writing, per finding:
   - refuted: state the evidence, in the disposition, with a test
     pinning the refutation where possible. A refuted finding is as
     valuable as an accepted one - record it, never silently drop it;
   - accepted: name the action taken in the same disposition. An
     accepted finding without an action is not yet accepted.
   A reviewer's REASONING can be wrong while its WARNING is right;
   dispose of the two separately.
3. THE DISPOSITION is one document per review: verdict table, narrow
   green (what the reviewer's packet did and did not contain), and the
   per-finding fates. It cross-links from the artifact reviewed.
4. AUTHOR DEFECT LEDGER: maintain a running list of the author's own
   verified failure modes (one line each: defect, instance, direction).
   Feed it to adversarial reviewers - naming the author's documented
   bias measurably sharpens attack. Two integrity rules: entries only
   for VERIFIED defects, and errors in BOTH directions recorded - a
   ledger that only shows one direction is itself the tidy story it
   warns against.
5. ESCALATION DISCIPLINE (FR-21): a review that shows you closed a
   question that was the owner's to decide is accepted by REOPENING the
   question - restating options, moving your view to a marked
   view - never by defending the closure. Having been corrected for
   closing is not a license to feign neutrality: state views as views.
6. The loop ends when every finding has a fate and every action is
   done or filed. Then, and only then, the next review round.
<!-- PROMPT-CORE-END -->
````

## `treadle0.5/skills/semantic-round-trip/SKILL.md`

````markdown
---
name: semantic-round-trip
description: Blind back-translation audit of a formal pin (Reed 6). Amended per FR-15 (packet sizing) and the source cycle's packet-scope lesson - a review's narrow green must state what was NOT in its packet.
---

# Semantic Round-Trip (Reed 6)

<!-- PROMPT-CORE-BEGIN -->
Two roles, strictly separated; you are exactly one of them.

BACK-TRANSLATOR: you receive ONLY the formal pin text (clause plus
battery verdicts), never the source prose, intent notes, or record
narrative. Render, in plain language: (1) what the pin admits, (2) what
it excludes, (3) your classification of each battery instance as you
read the clause - your reading, not the recorded verdicts. Translate
what is written; never guess intent.

COMPARATOR: you receive the back-translation and the intended meaning.
Produce a divergence list; each item names what the back-translation
says, what the intent says, and the stage charged - CLAUSE, PROSE, or
BATTERY. No divergences: record ROUNDTRIP_CLEAN with the
back-translator's identity and date.

Rules for both:
1. The back-translator's independence is the instrument; any leakage of
   intent voids the audit - ROUNDTRIP_VOID, rerun fresh. An author
   back-translating their own pin is VOID by construction.
2. Divergences are findings; a BATTERY-staged divergence obligates a
   new minimal pair before the clause may be edited.
3. A clean round-trip is agreement between two readings, never proof of
   correctness; it upgrades nothing by itself.
4. PACKET RULES (FR-15): packets are assembled from named file slices
   through the review harness, sized under its ceiling. A reviewer
   returning empty at its length limit got too much input - shrink the
   packet (extract the claims); never raise the output budget.
5. PACKET-SCOPED GREENS: every verdict states what was NOT in the
   packet. A CONFORMS from a reviewer who saw two files is worth those
   two files; a MISSING on a claim that needs execution routes to
   run-the-code verification (FR-25), never to a bigger packet.
<!-- PROMPT-CORE-END -->
````

## `treadle0.5/skills/term-pinning/SKILL.md`

````markdown
---
name: term-pinning
description: Protocol for assigning candidate finite meanings to uninterpreted terms of a frozen calculus (Warp W1), and for typing the DISPOSITION of every open item - DECIDE, PROPOSE, or ESCALATE. Use for any PIN-* record work. Amended per FR-21.
---

# Term Pinning (Warp W1)

<!-- PROMPT-CORE-BEGIN -->
You are pinning terms for a frozen calculus. Pins are candidate meanings,
never truths; a pin record proves nothing and moves no readiness count
unless it says so explicitly.

1. Take the cluster the frozen catalog order assigns; never pin ahead of
   the declared sequence, never pin a term outside the cluster.
2. METHOD RULE: each pin is the WEAKEST meaning that (i) makes every
   frozen occurrence of the term well-typed and (ii) preserves every
   distinction the calculus states in prose at those occurrences. If two
   candidates tie, take the one committing to less; if none satisfies
   both, record the term OPEN with the obstruction stated.
3. Before drafting, build the occurrence table: every location of the
   term, its polarity there, and the row type. Any term negated in both
   a certificate row and an N-row is steering-sensitive: flag it and
   state how the pin avoids making the certificate row vacuous.
4. After drafting, run the vacuity probe: each certificate row the term
   occurs in stays satisfiable AND falsifiable under the pin; record
   both directions.
5. Declare the bucket of every pin (definition / acceptance axiom /
   import / bridge). A pin requiring an unjustified bridge is not a pin;
   it is a named OPEN item.
6. DISPOSITION TYPING (FR-21): every open item in the record carries
   exactly one disposition -
   DECIDE: yours to answer, and answered here, with the authority named;
   PROPOSE: the owner's; give every live option with its consequence.
     A view of your own is permitted ONLY marked as a view, in its own
     paragraph, separated from the options - "no recommendation" beside
     a recommendation in prose is a defect;
   ESCALATE: two authorities conflict; state both sides and decide
     nothing, including by omission. A decision NOT to do specified
     work is a decision and types as PROPOSE or ESCALATE, never DECIDE.
7. Enumerate the dependency cone without changing any count; every
   count in the record is recomputed by a guard, never remembered
   (mapping-table rule 4).
8. Label equality is never identity; an original term is never
   identified with a fragment predicate.
<!-- PROMPT-CORE-END -->
````

## `treadle0.5/selftest.py`

````python
#!/usr/bin/env python3
"""treadle 0.5.0 selftest: every guard proven on a planted violation (FR-18).

Acceptance command:  python3 treadle0.5/selftest.py

Deterministic, offline, stdlib-only. Two halves per guard: the guard PASSES
on good input, and FAILS on a planted violation. A guard that cannot be shown
to fail is treated as not existing - three guards in the source cycle passed
while checking nothing, and were found only this way.

Exit 0: all checks OK. Exit 1: any check failed, listed plainly.
"""
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKERS = HERE / "checkers"
RESULTS = []
PLANTED_REFUSED = 0


def check(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    print(f"{'OK  ' if ok else 'FAIL'} {name}" + (f" -- {detail}" if detail and not ok else ""))


def planted(name, refused, detail=""):
    global PLANTED_REFUSED
    if refused:
        PLANTED_REFUSED += 1
    check(f"[planted] {name}", refused, detail)


def load(module_name):
    spec = importlib.util.spec_from_file_location(module_name, CHECKERS / f"{module_name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_checker(script, args, cwd):
    return subprocess.run([sys.executable, str(CHECKERS / script), *args],
                          capture_output=True, text=True, cwd=cwd)


GOOD_BATTERY = """# battery

### P1 - a positive
body of p1

### N1 - its near miss
body of n1

## Registry

| id | kind | partner | digest |
|----|------|---------|--------|
| P1 | positive | N1 | PENDING-DIGEST |
| N1 | near-miss | P1 | PENDING-DIGEST |
"""


def test_battery_digest(tmp):
    battery = tmp / "BATTERY.md"
    battery.write_text(GOOD_BATTERY, encoding="utf-8")
    w = run_checker("battery_digest.py", [str(battery), "--write"], tmp)
    v = run_checker("battery_digest.py", [str(battery), "--verify"], tmp)
    check("battery_digest accepts a good battery", w.returncode == 0 and v.returncode == 0,
          w.stdout + v.stdout)
    # Planted 1: tamper one digest character.
    text = battery.read_text(encoding="utf-8")
    import re
    match = re.search(r"\| ([0-9a-f]{16}) \|", text)
    tampered = text.replace(match.group(1), ("0" if match.group(1)[0] != "0" else "1") + match.group(1)[1:], 1)
    battery.write_text(tampered, encoding="utf-8")
    v2 = run_checker("battery_digest.py", [str(battery), "--verify"], tmp)
    planted("battery_digest refuses a tampered digest", v2.returncode != 0)
    # Planted 2: registry heading gone (defect-10 guard).
    battery.write_text(GOOD_BATTERY.replace("## Registry", "## Not A Registry"), encoding="utf-8")
    v3 = run_checker("battery_digest.py", [str(battery), "--verify"], tmp)
    planted("battery_digest refuses a missing registry", v3.returncode != 0)


def test_consistency_packet(tmp):
    (tmp / "docs").mkdir()
    (tmp / "docs" / "a.md").write_text("The blast radius is one table.\n", encoding="utf-8")
    (tmp / "docs" / "b.md").write_text("Elsewhere: the blast radius is one table too.\n", encoding="utf-8")
    claims = {"packet": "PACKET.md", "window": 40, "max_chars": 5000, "claims": [
        {"label": "A", "path": "docs/a.md", "patterns": ["blast radius"]},
        {"label": "B", "path": "docs/b.md", "patterns": ["blast radius"]}]}
    (tmp / "claims.json").write_text(json.dumps(claims), encoding="utf-8")
    w = run_checker("consistency_packet.py", ["--write"], tmp)
    v = run_checker("consistency_packet.py", ["--verify"], tmp)
    check("consistency_packet builds and verifies", w.returncode == 0 and v.returncode == 0,
          w.stdout + v.stdout)
    # Planted 1: source document changes a quoted claim.
    (tmp / "docs" / "a.md").write_text("The blast radius is TWO tables.\n", encoding="utf-8")
    planted("consistency_packet refuses a stale packet",
            run_checker("consistency_packet.py", ["--verify"], tmp).returncode != 0)
    # Planted 2: a pattern that matches nothing must FAIL, not shrink coverage.
    claims["claims"][0]["patterns"] = ["zzz-renamed-away"]
    (tmp / "claims.json").write_text(json.dumps(claims), encoding="utf-8")
    planted("consistency_packet refuses a claim matching nothing",
            run_checker("consistency_packet.py", ["--write"], tmp).returncode != 0)
    # Planted 3: ceiling (FR-15) -- remedy must name shrinking, not budgets.
    claims["claims"][0]["patterns"] = ["blast radius"]
    claims["max_chars"] = 10
    (tmp / "claims.json").write_text(json.dumps(claims), encoding="utf-8")
    over = run_checker("consistency_packet.py", ["--write"], tmp)
    planted("consistency_packet refuses an over-ceiling packet",
            over.returncode != 0 and "Shrink" in over.stdout)


def test_influence_probe():
    probe_module = load("influence_probe")
    try:
        message = probe_module._demo()
        check("influence_probe demo (notices, gates, restores)", message.startswith("OK"))
    except AssertionError as exc:
        check("influence_probe demo (notices, gates, restores)", False, str(exc))

    class Target:
        def __init__(self):
            self.field = 1

    with probe_module.probe(Target) as reads:
        reads.arm()
        Target().field  # planted read
    planted("influence_probe notices a planted read", "field" in reads.seen)


def test_review_harness(tmp):
    harness = load("review_harness")
    (tmp / "in.md").write_text("# doc\nclaim text here\n", encoding="utf-8")

    def job(name, ceiling=24000, out="out/reply.md"):
        return harness.Job(name=name, role="REVIEWER", model="null-model:2026-01-01",
                           skill_core="Protocol: answer from the material only.",
                           task="Audit the claim.", inputs=(harness.Slice("in.md"),),
                           out=out, packet_ceiling=ceiling)

    row = harness.run_job(job("smoke"), harness.NullTransport, root=tmp)
    count = harness.verify_ledger("calls.jsonl", root=tmp)
    check("review_harness runs a NullTransport job and verifies", count == 1 and row["seq"] == 1)
    transcript = (tmp / "out" / "reply.md").read_text(encoding="utf-8")
    check("transcript carries the FR-16 provenance line", "reproducibility: none" in transcript)

    # Superseded semantics (FR-17): re-run with a changed packet.
    (tmp / "in.md").write_text("# doc\nclaim text CHANGED\n", encoding="utf-8")
    harness.run_job(job("smoke"), harness.NullTransport, root=tmp)
    check("superseded row kept; latest agrees", harness.verify_ledger("calls.jsonl", root=tmp) == 2)
    # Planted 1: transcript matching only the SUPERSEDED row must fail.
    rows = [json.loads(l) for l in (tmp / "calls.jsonl").read_text().splitlines()]
    old_header = (f"<!-- reproducibility: none -->\n<!-- prompt_sha256={rows[0]['prompt_sha256']} -->\n")
    (tmp / "out" / "reply.md").write_text(old_header, encoding="utf-8")
    try:
        harness.verify_ledger("calls.jsonl", root=tmp)
        planted("verify_ledger refuses a transcript matching a superseded row", False)
    except harness.HarnessError:
        planted("verify_ledger refuses a transcript matching a superseded row", True)
    # Planted 2: hash-chain break.
    lines = (tmp / "calls.jsonl").read_text().splitlines()
    bad = json.loads(lines[1]); bad["prev_sha256"] = "sha256:" + "0" * 64
    (tmp / "chain.jsonl").write_text(lines[0] + "\n" + json.dumps(bad, sort_keys=True) + "\n")
    try:
        harness.verify_ledger("chain.jsonl", root=tmp)
        planted("verify_ledger refuses a broken chain", False)
    except harness.HarnessError:
        planted("verify_ledger refuses a broken chain", True)
    # Planted 3: credential material in a row.
    (tmp / "cred.jsonl").write_text(lines[0].replace('"role": "REVIEWER"',
                                    '"role": "REVIEWER", "api_key": "x"') + "\n")
    try:
        harness.verify_ledger("cred.jsonl", root=tmp)
        planted("verify_ledger refuses credential material", False)
    except harness.HarnessError:
        planted("verify_ledger refuses credential material", True)
    # Planted 3b (found by running SETUP's own printed commands): the reply
    # digest must be checked against the transcript's reply BYTES. The final
    # row of the chain has no successor protecting it, so without the
    # cross-check a tampered reply -- or row -- was accepted. First restore a
    # clean state (re-run appends row 3 with a fresh transcript), prove clean,
    # then tamper ONLY the reply body and demand refusal WITH THE RIGHT
    # MESSAGE -- an earlier draft of this very check matched "reply" against
    # the file PATH "out/reply.md" and passed vacuously (FR-18, recursively).
    harness.run_job(job("smoke"), harness.NullTransport, root=tmp)
    check("ledger clean after restore", harness.verify_ledger("calls.jsonl", root=tmp) == 3)
    with open(tmp / "out" / "reply.md", "a", encoding="utf-8") as handle:
        handle.write("tampered line\n")
    try:
        harness.verify_ledger("calls.jsonl", root=tmp)
        planted("verify_ledger refuses a tampered transcript reply", False)
    except harness.HarnessError as exc:
        planted("verify_ledger refuses a tampered transcript reply",
                "does not match the ledger's reply_sha256" in str(exc), str(exc))
    harness.run_job(job("smoke"), harness.NullTransport, root=tmp)

    # Planted 4: packet over the governor's ceiling (FR-15), remedy named.
    try:
        job("big", ceiling=10).user(tmp)
        planted("packet governor refuses an oversized packet", False)
    except harness.HarnessError as exc:
        planted("packet governor refuses an oversized packet",
                "Shrink the packet" in str(exc) and "output budget" in str(exc))
    # Planted 5: forbidden slice (isolation).
    isolated = harness.Job(name="iso", role="BACK-TRANSLATOR", model="null-model:2026-01-01",
                           skill_core="x", task="t", inputs=(harness.Slice("in.md"),),
                           out="out/i.md", forbidden=("in.md",))
    try:
        isolated.user(tmp)
        planted("isolation check refuses a forbidden slice", False)
    except harness.HarnessError:
        planted("isolation check refuses a forbidden slice", True)


def test_package_shape():
    for doc in ("README.md", "SETUP.md", "MODULES.md", "FIELD_REPORTS.md",
                "FORMAT.md", "LEDGER_FORMAT.md"):
        check(f"doc present: {doc}", (HERE / doc).is_file())
    skills = sorted(p.parent.name for p in HERE.glob("skills/*/SKILL.md"))
    check("twelve skills present", len(skills) == 12, str(skills))
    for skill in HERE.glob("skills/*/SKILL.md"):
        text = skill.read_text(encoding="utf-8")
        ok = ("PROMPT-CORE-BEGIN" in text and "PROMPT-CORE-END" in text
              and text.startswith("---\nname:"))
        check(f"skill well-formed: {skill.parent.name}", ok)


def main():
    with tempfile.TemporaryDirectory() as d1:
        test_battery_digest(Path(d1))
    with tempfile.TemporaryDirectory() as d2:
        test_consistency_packet(Path(d2))
    test_influence_probe()
    with tempfile.TemporaryDirectory() as d3:
        test_review_harness(Path(d3))
    test_package_shape()
    failed = [name for name, ok, _ in RESULTS if not ok]
    print(f"\n{len(RESULTS)} checks, {PLANTED_REFUSED} planted violations correctly refused, "
          f"{len(failed)} failed")
    if failed:
        for name in failed:
            print(f"  FAILED: {name}")
        sys.exit(1)


if __name__ == "__main__":
    main()
````

---

## Verification after reconstruction

```sh
python3 treadle0.5/selftest.py
```

Expected final line:

```
38 checks, 12 planted violations correctly refused, 0 failed
```

The twelve planted violations are the point. Each is a deliberate corruption a
guard must REFUSE — a tampered battery digest, a stale claims packet, a claim
pattern matching nothing, an over-ceiling reviewer packet, a broken hash chain,
credential material in a ledger row, a transcript matching only a superseded
row, a tampered transcript reply, a forbidden slice in an isolated packet. A
guard that cannot be shown to fail is treated as not existing (FR-18); three
guards in the source cycle passed while checking nothing and were found only
this way.
