# The Poietics research program — three runs, one record

Registered 2026-08-25 (REQUEST.md R8, R9). **P-R1 runs in this tranche.
P-R2 and P-R3 are REGISTERED ONLY** — question, dossier, milestones and
launch preconditions written down here before P-R1's outcome is known, so
neither can be quietly reshaped to fit whatever P-R1 happens to produce.
One tranche, one run (C2).

The shared evidence base is `record/` — twelve curated files from the
operator's `POIETICS_FULL_RECORD.zip`, provenance and cautions in
`README.md`. All three runs inherit that README's two cautions: the
report's author is the agent that did the work, so `report/` is an account
and `data/` is the evidence; and the bundle's numbers supersede the git
history's, which still contains two withdrawn figures.

## Why three runs and not one

The record supports three different questions, and collapsing them would
make each answer worse.

P-R1 asks for an EXPLANATION of a result. P-R2 asks which of the record's
own CLAIMS are the kind of thing that could be shown wrong. P-R3 asks the
harness to CHOOSE between whatever rival mechanisms survive the first two.
The first is abductive, the second demarcational, the third comparative;
each has a different success condition, and a single run asked for all
three would satisfy the easiest.

The ordering is a dependency, not a preference: P-R3 needs at least two
surviving rivals, which only P-R1 (and P-R2's pruning) can produce.

---

## P-R1 — the explanation run — **STATUS: RUNS IN THIS TRANCHE**

**Question** (REQUEST.md R10a, verbatim, frozen in `build_manifest_pr1.py`):

> Under what conditions does a test constrain its subject rather than
> describe it? Account for the 3-of-26 result in the attached record and its
> distribution — compile.py 1/9 mutations lost under shown-to-fail-first
> installation, every ordinarily-guarded module 4/4 to 6/7 — same author,
> same week, same care.

**Dossier.** All twelve committed files, admitted at seed: 12 sources, 623
blocks, 0 refusals. Critics cite the bound dossier, and the citation is
byte-checked against the block.

**Configuration.** Cross-family, everything on. `deepseek-v4-pro:0813`
conjecturing, `kimi-k3` criticising, a two-seat judge ensemble of
`qwen3.5:397b` and `glm-5.2`, the remaining seven canonical roles on
`glm-5.2`. 12 cycles, 3 000 000 tokens. Full design and its measured
assumptions: `PREREG.md`.

**Milestones.** `PREREG.md` §5, registered before launch.

**What P-R1 cannot settle.** Whether its account is TRUE. The run produces
accepted-and-surviving conjectures; acceptance is a status inside this
harness, not a fact about guards in another repository. That gap is the
whole reason P-R2 and P-R3 exist.

---

## P-R2 — the premises run — **STATUS: REGISTERED, NOT RUN**

**Question, registered:**

> Which claims in the attached record are demarcated — that is, which could
> be shown wrong by an observation the record itself does not already
> contain, and what observation would do it? Take the record's own stated
> confound as ammunition, not as an excuse: one repository, one author, one
> nine-day window, and a registry whose size the record calls arbitrary.

**Why this question and not "is the record true".** The record is honest
about its own limits (§15.11, and its README's caution 2), and a run asked
to verify it would have nothing to verify against — the bundle contains no
engine tree and no test tree, so *no* pass/fail or CAUGHT/SURVIVED claim in
it is re-executable. Asking which claims are DEMARCATED asks something the
bundle can actually answer: it is a question about the form of the claims,
not about facts outside the bundle.

**The confound, stated as the record states it, and handed to the critics.**
The record's own §15.11 limits, to be bound into the run as registered
ammunition rather than discovered mid-run:

1. The 3-of-26 magnitude is one repository, one author, one week. The
   DIRECTION of the coverage finding is internally over-determined; the
   MAGNITUDE is not established as typical.
2. The 62 mutations were authored by models that had read the acceptance
   record. Whether a record-blind model proposes equally meaningful
   reversals is untested.
3. Nothing shows that closing the 46 survivors would prevent a real defect.
   46 proved guards is a large cost with unmeasured value.
4. The registry's own size is arbitrary, and growing it can only make the
   held-fraction look worse before it gets better — an incentive
   misalignment for any author reporting on their own suite.
5. `compile.py`'s 1-of-9 is a SINGLE module. The shown-to-fail-first rule is
   confounded with everything else that made `compile.py` different.

**Registered demarcation criteria.** A claim counts as demarcated only if
the run names (a) an observation that would refute it, (b) a place that
observation could come from other than this bundle, and (c) what the record
would have to say instead if the observation came back negative. A claim
that survives only because nothing could count against it is registered as
UNDEMARCATED — which is a finding, not a failure.

**Preconditions before P-R2 may launch.** P-R1 committed with a typed
terminal and a clean `verify_root`; P-R1's RESULTS.md written, so P-R2's
dossier can include what P-R1 actually claimed; a soak case for P-R2's own
configuration, green, per R11's law.

**Its own honest limit, registered now.** P-R2 measures the FORM of claims.
A well-formed falsifiable claim can still be false, and a vague claim can
still be right. Demarcation is a property of statements, not a verdict on
the project.

---

## P-R3 — the succession trial — **STATUS: REGISTERED, NOT RUN**

**Question, registered:**

> Of the rival mechanisms still standing after P-R1 and P-R2, which better
> accounts for the record's distribution — and does that answer survive
> swapping which one is presented first?

**Protocol: Rung 7 succession** (`experiments/2026-08-24-change-rung7-
wounds-falls-succession/`). Four properties of that protocol are why it is
the right instrument here, and all four are what P-R3 is registered to
exercise:

- **Both orders are judged.** The two accounts are compared, then compared
  again with the tables swapped (`test_the_program_road_judges_both_orders`).
- **The candidates are presented identically and ordered by content, not by
  arrival** (`test_the_two_candidates_are_presented_identically`,
  `test_the_candidates_are_ordered_by_content_not_by_arrival`).
- **A hung verdict is entered as hung**, never broken by a tiebreak
  (`test_a_constructed_order_disagreement_is_a_no_verdict`).
- **The flip rate is a recorded field, not a derivation**, and an empty rate
  may not be read as a clean one
  (`test_an_empty_rate_cannot_be_read_as_a_clean_one`).

**The thing to say plainly, registered before it can be spun.** Per that
tranche's own PARKED.md, **no live succession has ever happened.** P-R3
would be the first. That makes a hung verdict, or no succession at all, an
informative outcome about the instrument, and it must be reported as such
rather than as a failed run.

**Preconditions before P-R3 may launch.** At least TWO rival mechanisms
surviving P-R1 and P-R2 as accepted-and-surviving conjectures — if only one
survives, there is nothing to try and P-R3 does not launch; the rivals
stated as separable accounts, since a succession trial between two
descriptions of the same mechanism measures nothing; and a green soak on
P-R3's configuration.

**Its own honest limit, registered now.** A succession trial ranks two
accounts against named criteria in a fixed order. It cannot tell you the
winner is right — only that this court, on those criteria, preferred it, and
how often the same court reverses itself when the parties swap tables.

---

## What the program as a whole cannot deliver

None of the three runs can replicate the Poietics result. The bundle carries
no engine tree and no test tree; every CAUGHT/SURVIVED verdict in it is a
claim about an execution nobody here can re-run. The program's ceiling is a
well-criticised ACCOUNT of someone else's evidence, with its own residue
stated. "Accepted does not mean true" applies doubly here, and every
RESULTS.md in this program is required to say so in its own words rather
than by citing this line.
