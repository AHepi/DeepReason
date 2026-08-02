<!-- DR-REC-change-a-seam -->
Verified-at: 08dcdf3c
Verify: python tools/docs_verify.py
Owns: docs/map/
Seams: DR-SEAM-rules-x-scratch

# Recipe: change how two parts of the system interact

Most large changes are seam changes. The work is rarely inside one subsystem —
it is in what two of them have agreed, and the cost is in finding every place
that agreement is expressed. This recipe turns that search into a lookup.

**Worked example throughout: "change the way schools interact with the
scratchpad."** Neither side is a package: schools is `DR-CON-schools`, the
scratchpad is `DR-SUB-scratch`. That is the normal case, not a hard one.

## Step 1 — name both sides as IDs

Do not start from filenames. Start from `INDEX.md`'s routing table and turn the
request into two IDs. "Schools" → `DR-CON-schools`. "Scratchpad" →
`DR-SUB-scratch`.

If a side has no ID, it is either not a thing (rephrase the request) or the map
is incomplete (see Step 7).

## Step 2 — read the seam document, not the subsystems

    ls docs/map/ | grep -i schools

The seam file is `SEAM-<a>-x-<b>.md`, sides in alphabetical order. Read it
first. It exists to tell you which *fraction* of each side the change touches —
usually small. Reading both subsystem documents first means reading ten times
more than you need.

If no seam document exists, check `INDEX.md`'s seam matrix. Absent from the
matrix means the two genuinely do not interact, and a request to change their
interaction is a request to CREATE one — a different and larger job, which needs
a new seam document as part of the work.

`check: test -f docs/map/INDEX.md`

## Step 3 — check the invariants before you design anything

    docs/map/INV-frozen-surfaces.md

This is the step that is cheap now and expensive later. For the worked example
the binding constraint is stated in the scratchpad's own boundary: storage never
makes a note into evidence.

`check: grep -q "advisory_non_grounding" src/deepreason/scratch/proposals.py`

A design that routes scratch content into anything that decides what stands is
not a design that needs review — it is already refused.

## Step 4 — enumerate the call sites, mechanically

The seam document names the sites. Verify them rather than trusting them; the
document may be stale even when its stamp is fresh.

    # every file that mentions both sides
    for f in $(grep -rl "school" src/deepreason --include=*.py); do
      grep -ql "scratch" "$f" && echo "$f"
    done

For schools × scratchpad that is 20 files today. **Most of them are
coincidence** — a module that happens to mention both. The seam document's job
is to separate the ~4 that carry the agreement from the ~16 that merely name
both sides. Do that separation once, and record it back into the seam document.

`check: test $(for f in $(grep -rl school src/deepreason --include=*.py); do grep -ql scratch "$f" && echo x; done | wc -l) -ge 10`

## Step 5 — find the tests that pin the current agreement

A seam that matters is already pinned somewhere. Search for the negative
assertions first: they are what will break, and breaking them is how you learn
the change is bigger than you thought.

    grep -rln "scratch" tests/ | head

For this seam, the criticism side's separation from the scratchpad is pinned
explicitly, including against function-local imports:

`check: python -m pytest tests/test_prose_refutation_boundaries.py -q -k scratch`

If your change makes one of these fail, stop and re-read Step 3. A pinned
negative assertion is a decision someone already made; overturning it is an
operator's call, not an implementer's.

## Step 6 — write the change with its receipts

Follow `dr-change-orchestrator`. The map-specific obligations are:

1. The seam document is updated **in the same commit** as the code.
2. `Verified-at:` advances only if you actually re-ran the checks.
3. Any call site you added or removed changes the site list in the seam doc.
4. `python tools/docs_verify.py` passes.
5. A new agreement between the two sides gets a new check, in the seam doc,
   that would fail if the agreement were broken.

`check: python tools/docs_verify.py --self-test`

## Step 7 — if the seam document did not exist

Create it as part of the change, before writing code:

    <!-- DR-SEAM-<a>-x-<b> -->
    Verified-at: <the commit you are making>
    Verify: python tools/docs_verify.py
    Owns: <the files that carry the agreement, not every file that mentions both>
    Sides: DR-CON-schools, DR-SUB-scratch

    # <a> x <b>

    ## The agreement          -- what each side promises the other, in prose
    ## Where it is expressed  -- table: | Site | File | Symbol | What it enforces |
    ## What is deliberately absent -- the non-interactions, with their checks
    ## How to change it       -- the order of operations, and what must move together
    ## Traps

**"What is deliberately absent" is the most valuable section of a seam
document**, and the one people skip. For schools × scratchpad the load-bearing
fact is a NON-interaction: the criticism side receives no scratch context at
all, and that is deliberate rather than accidental. A reader who does not know
which absences are deliberate will read them as gaps and "fix" them.

## Traps

- **Starting from grep instead of from the map.** grep finds mentions; the seam
  document distinguishes mentions from agreements. Twenty files mention both
  schools and scratch; far fewer carry the contract.
- **Treating an absence as an omission.** See above. Check
  "What is deliberately absent" before adding an interaction that looks missing.
- **Updating the subsystem docs and not the seam.** The seam is the file the
  next reader opens first. A correct pair of subsystem documents with a stale
  seam between them is worse than either being stale alone.
- **Assuming the guard is on the side you are editing.** A rule about what
  criticism may act on may be enforced in the trial rather than in the criticism
  rule, because those two answer different questions — one decides what is
  recorded, the other what changes a status.
`check: grep -q "formally_backed" src/deepreason/informal/trial.py`
