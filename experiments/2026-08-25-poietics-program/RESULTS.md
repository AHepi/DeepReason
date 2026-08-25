# Results — the Poietics program

Dated, honest-ledger segments. What the record shows, then the residue —
what remains unproven. Accepted does not mean true, and for an explanation
of somebody else's evidence it does not even mean well-evidenced.

---

## 2026-08-25 — P-R1, the explanation run: SUCCESS by PREREG.md §6, on a thinner margin than the headline suggests

**The typed outcome, whole.** `results.txt`, `verify_root.json`,
`milestones.json`, all committed:

    run id            1b31f0065687bd24f64bb08acae1245446b4b31c31b90b141ff95cd5759c9a97
    state             completed
    stop_reason       budget_exhausted        (the CYCLE budget, as designed)
    cycles completed  12 of 12
    tokens            521,838 of 3,000,000    (17 percent)
    accepted/refuted  419 / 104               (suspended 0)
    survivors         82
    frontier          40 artifacts
    verify_root       0 violations
    finding families  completion 120, epistemic 0, integrity 0,
                      operational 22, security 0
    terminal          valid, epoch 0, amend-ready

All three registered milestones hold, M2 on the STRICT reading (below).
This is the first live run in this repository to carry a cross-family seat
matrix and a non-empty dossier bound at seed, and it recorded no
operational failure.

**The seats did the work the operator assigned them.**

    conjecturer            deepseek-v4-pro:0813    37 calls   297,249 tokens
    argumentative_critic   kimi-k3                126 calls   224,589 tokens
    judge (2 seats)        qwen3.5:397b, glm-5.2    0 calls          0 tokens

### What the accepted-and-surviving conjectures actually claim (R13)

82 survivors. **58 are conjectures; 24 are IMPORT-role records** — the
record's own documents, admitted as artifacts and never removed from the
survivor set (see Residue R1). Of the 34 survivors that pass
`poietics-installation-mechanism@v1`, **26 are conjectures and 8 are
imported record sections.** Everything below is drawn from the 26.

They fall into three groups, and the first two are RIVALS — which is
exactly the precondition PROGRAM.md registered for P-R3.

**Group A — deflationary: the record cannot support a general condition.**
The largest group. The 3-of-26 result is read as an artifact of something
other than testing discipline, and the answer to the question is "you
cannot tell from this":

> "The 3-of-26 result is a confound of one-repository, one-author,
> one-week arbitrariness: the distribution … reflects where the author
> happened to install shown-to-fail-first tests as guards, not any general
> condition under which tests constrain rather than describe their
> subjects."

Distinct causal stories are offered inside the group — registry size, the
number of mutations per module, import-graph topology, mutation-proposal
order versus guard-installation order, and selection bias from mutations
authored by models that had read the acceptance record. Several restate the
record's own §15.11 limits back at it. One is sharper than the rest:

> "The question is underdetermined by the record: the 3-of-26 result cannot
> distinguish between 'the test constrained its subject' and 'the subject
> was never mutated in a way that would test the constraint.'"

**Group B — positive: a condition is proposed.** Fewer, and more varied.
The recurring one makes the shown-to-fail-first ritual constitutive rather
than evidential:

> "A test constrains its subject rather than describes it when the test's
> failure mode becomes a required precondition for the subject's
> acceptance — the shown-to-fail-first installation makes the failure part
> of the subject's identity, so the test cannot describe what the subject
> would have been without it."

Four other conditions were proposed and survived, each different in kind:

- **Reflexivity.** "A test constrains … when the test's guard fires on the
  author's own mutation — if a process guard never fires on its author, it
  is probably a description, not a constraint." This is the record's own
  §6.2 rule, arrived at independently.
- **Rejection before acceptance.** "A test constrains when the subject's
  acceptance record is derived from the test's rejection, not from the
  test's acceptance."
- **Independent authority.** "The condition is whether the test and the
  subject share a single authority for their respective validity; when
  they do, the test only describes the authority's self-consistency."
- **Prior failure.** "A test constrains its subject only if a failure of
  the subject would make the test itself fail before any assertion can
  pass."

**Group C — relational claims between rivals, carrying their own refutation
conditions.** Unregistered and unprompted, and the most interesting thing
the run produced. Eight surviving artifacts compare the rival accounts to
each other and state what would kill the relation:

> "SRC_004 integrates SRC_003's arbitrariness claim by adding temporal
> ordering as the operative variable … **Refuted if** a formal policy
> mandated guard-before-mutation ordering and compile.py still showed 1/9,
> or if the same distribution replicated with a different author following
> a different order."

Every one of the eight carries a `Refuted if` clause naming an observation
outside this bundle. That is demarcation performed spontaneously, and it is
the material P-R2 was registered to look for.

### The milestones, as measured

    M1  MET       435 accepted, 82 survivors, 26 CONJECTURE survivors pass
                  poietics-installation-mechanism@v1 (34 including imports)
    M2  MET       212 verified citations into the record, of which
                  2 are CRITIC-side.  Met on the strict reading.
    M3  MET       7 conjectures lean on a withdrawn figure; 20 citations
                  resolve to report/14 against them.

**M3 is the result worth keeping.** It was registered as conditional with
an explicit warning that its trigger might never fire. It fired: conjectures
did lean on the withdrawn "6/6 held" and "59 caught / 3 survived" figures,
and §14 — the record's own catalogue of what it got wrong — was cited back
against them twenty times. The dossier's self-corrections were used as
ammunition, which is what binding the record as evidence was for.

---

## Residue — what this run does NOT establish

**R1 — 24 of the 82 survivors are the record's own documents, not
conjectures.** FIXED 2026-08-25 by
`experiments/2026-08-25-fix-import-role-survivors/`: `deepreason results` now
reports **58** for this root. The stored `run-result.json` is untouched and
still lists 82 ids — the fix changed what the reader counts, not what the
record holds — so every number quoted below remains exactly what this run
published. The residue as originally written follows, unedited. CLAUDE.md states as a hard-won invariant that "import-role
admission records never count as survivors", and the results surface counts
them anyway. M1 survives this easily (26 conjecture survivors pass the
criterion, against a floor of one), but the headline "82 survivors" is
inflated by roughly 29 percent and should not be quoted as a count of
positions. PARKED as P4 — it is a defect in a surface this tranche is not
scoped to change.

**R2 — the judge ensemble never ran.** Zero judge calls, no defended trial,
no trial declined, none blocked. The operator's cross-family judge
specification was built, qualified and paid for, and did no work: no
criticism sustained to a trial in twelve cycles. Two consequences, stated
plainly. Nothing in this run is evidence about cross-family judging. And
the 419 acceptances are acceptances under the LEGACY path — surviving the
criticism that happened to be generated — not adjudicated verdicts.

**R3 — M2 passed on 2 critic-side citations out of 212.** The critic seat
made 126 calls and produced 207 criticism events, but byte-checked citation
into the dossier is overwhelmingly a conjecturer behaviour here. M2 as
registered is MET and I am not moving it; but a milestone met at 2 is a
milestone met at the floor, and a rerun could plausibly miss it. Recorded so
nobody reads M2 MET as "the critic engaged the record throughout".

**R4 — the dossier leakage predicted in PREREG.md §4 materialised.** Three
committed record files pass all three criteria alone, and eight imported
record sections appear among the artifacts passing the mechanism criterion.
The criteria cannot distinguish an account from a quotation. This is why
PREREG registered criteria-PASS as a floor and never as a milestone, and
why M1's honest form is the 26-conjecture figure rather than 34.

**R5 — none of this is evidence about Poietics.** The bundle carries no
engine tree and no test tree; no CAUGHT/SURVIVED verdict in it is
re-executable from these bytes. P-R1 produced a well-criticised ACCOUNT of
someone else's record. Acceptance here is a status inside this harness — it
means a conjecture survived the criticism this run happened to generate,
from one critic seat, in twelve cycles, with no judge ever ruling.

**R6 — Group A may be right, and that is not a comfortable result.** The
largest cluster of surviving conjectures says the question cannot be
answered from this record at all. That is a coherent position, it engages
the confound the question handed it, and this run provides no way to
adjudicate it against Group B — because adjudication is exactly what did
not run (R2). P-R3 exists for this, and its precondition — two or more
surviving separable rivals — is now satisfied.

---

## Program status

    P-R1  explanation   RUN. Success by PREREG.md §6. Root committed.
    P-R2  premises      REGISTERED. Preconditions now met: P-R1 committed
                        with a typed terminal and clean verify_root, and
                        RESULTS.md written. Still needs its own soak case.
    P-R3  succession    REGISTERED. Precondition — two or more surviving
                        separable rival mechanisms — is SATISFIED by
                        Groups A and B above. Still needs its own soak
                        case, and per the Rung 7 tranche's PARKED.md no
                        live succession has ever run.
