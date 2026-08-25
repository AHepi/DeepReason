# Results — the import-role survivor invariant

Dated, honest-ledger segments. What the record shows, then the residue.
Accepted does not mean true.

---

## 2026-08-25 — the invariant held only where it was patched; now it has one home

**What was observed.** `deepreason results` reported **82 survivors** for the
poietics P-R1 root (`run 1b31f0065687bd24`), of which **24 were IMPORT-role
admission records** — sections of the operator's own attached dossier. CLAUDE.md
carries the contradicted rule verbatim, in the list whose violations were "real,
recorded defects": *"import-role admission records never count as 'survivors'."*
The finding was already committed as
`experiments/2026-08-25-poietics-program/` RESULTS.md **R1** and PARKED.md
**P4**; this tranche is that prompt executed.

**What the record showed, before any code was read.** All 24 IMPORT members
enter on their own `Register` events at **log seqs 5–40**, each addressed to the
operator's seed problem `question-aa835741…`. The log's **first LLM-bearing
event is seq 85**. Every one of the 24 was accepted before a model was
consulted — they survived no criticism because there was none yet to survive.
That single fact closed the reading P4 asked to separate: no interpretation of
"survivor" reaches an artifact accepted before the first provider call.

**The cause was a duplicated rule, not a wrong one.** `selfstudy run-9175f0ec`
installed the exclusion in `Scheduler._select_problem` and spelled it out there
by hand. `run_report` — the writer of every root's published survivor set, two
hundred lines up **in the same file** — had no role clause, and the results
surface reported that set's length verbatim. The map's own check could not see
it: it grepped the file for the literal, and the file held one site that had the
clause and one that did not.

**What was done.** The rule moved to `ontology/state.py`:
`is_import_admission` is now the only place in `src/` that names
`ProvenanceRole.IMPORT` for this purpose, and `counts_as_survivor` composes it
with ACCEPTED. `run_report` and `_select_problem` build membership through it;
the results reader uses `is_import_admission` alone, so it can only SUBTRACT
what the invariant bars from what the record published — never re-derive a
survivor the record never listed, never re-adjudicate a status that moved after
the payload was written. Six map documents moved in the same commit, two of
which turned out to pin the moved literal themselves.

**What the record now shows.**

    deepreason results <P-R1 root>   survivors  82 -> 58
    frontier                                    40 -> 40   (unchanged)
    stored run-result.json                      82 ids, untouched
    verify_root (re-derived)                    valid, 0 violations

Twelve of the 37 git-tracked roots publishing a survivor set move. **Every
delta equals that root's own IMPORT count exactly**, and the 25 roots with no
import-role survivor are byte-identical — the property the fix had to have,
measured rather than argued. The largest correction after P-R1 is
`live-grounded-extension-expansion` (245 → 233).

**The result worth keeping.** `run-9175f0ec` — the run that motivated the
invariant in the first place — was itself over-reporting **22 survivors where
12 are supported**. The rule was installed for that run, in that run's
postmortem, and that run's own results surface never received it. A rule
written at one site is a rule that holds at one site; nothing but a single
authority makes it a rule about the system.

**Instruments.** Full gate 4168 passed / 6 skipped / **0 failed** (baseline
re-derived in-session at `43f408506`: 4162 / 6 / 0; the delta is exactly the 6
new tests, and no assertion was weakened). `docs_verify` full: 3 failed, all
three pre-existing shallow-clone git-history checks, identical to the baseline.
`--audit` 0 findings, `--links` 0 dangling. `tools/blast_radius.py`: frozen
surfaces **CLEAR**, no contact. Mutation-proven: re-admitting imports in the
authority turns the reader and writer tests RED, restoring turns them GREEN;
both outputs pasted in VERIFY.md.

---

## Residue — what this tranche does NOT establish

**R1 — one authority in `src/`, pinned by a check that names two files.**
`test_one_authority_names_the_rule_and_every_survivor_surface_calls_it` asserts
that neither `scheduler.py` nor `results.py` spells the rule. It does not scan
the tree, so a fifth consumer added elsewhere would not trip it.

**R2 — two known derivations were left alone on purpose.**
`report.py::eval_report` and `loop.py::run_problem` each build a survivor set of
their own. Neither number moves on the P-R1 root today, because 0 of the 24
IMPORT survivors carries an `hv` or a `reach` entry — they are excluded by
ABSENCE, not by rule, which is a weaker guarantee than the one this tranche
installed. PARKED P1.

**R3 — the `accepted` count still includes import-role records** (435 accepted
on the P-R1 root, 36 of them IMPORT). The invariant names survivors; this
tranche took it literally and said so in GOAL.md before reading code. Whether
ACCEPTED should mean the same thing is an authority question, not a reporting
one.

**R4 — the diff-budget gate returned EXCEEDED.** Against FIX.md's own 150-line
ceiling, the actual diff was 319 insertions. `src/` was 72, across exactly the
three sites specified before implementation; the overrun is the regression test
and six map documents, both of which this workflow makes mandatory. Disclosed
and re-priced in FIX.md Amendment 1 rather than outrun. Recorded here because a
budget overrun that only appears in a tool's JSON is a budget overrun nobody
read.

**R5 — an unrelated disagreement was found and not chased.** The P-R1 root's
stored finding-family breakdown (completion 120, operational 22) and a fresh
re-derivation (121/23) differ. The re-derivation is identical at `43f408506`
and at this tranche's head, so it predates this work. PARKED P3.

**R6 — nothing here is evidence about what the P-R1 run concluded.** The 58
conjectures are the same 58 they always were; only the count that was quoted
changes. RESULTS.md's own analysis of Groups A/B/C was already drawn from the
26 conjecture survivors passing the mechanism criterion, and is untouched.
