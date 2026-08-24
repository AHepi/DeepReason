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
