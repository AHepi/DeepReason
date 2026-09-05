# Verify: does a criticism whose ground is gone let its target back?

Outcome: **PASS**, with the ceiling stated plainly — the road is built and
proven offline; no live run has taken it.

## GOAL.md's success criterion, item by item

### 1. The wire road exists and reaches the documented branch

    $ python experiments/2026-09-05-criticism-premise-declaration/s0_wire.py
    critic DECLARED the premise essential    ('accepted', 'refuted')
    critic declared nothing (today's path)   ('refuted', 'accepted')

    PASS: a criticism whose declared ground is refuted no longer defeats its
    target, and one that declares nothing is untouched.
    rc=0

The §0 DEPENDENCE scenario, rewritten as the critic declaring the premise
essential THROUGH THE CONTRACT, returns the EVIDENCE tuple. Criterion met.

The second line is the half that is easy to forget: a criticism that declares
nothing behaves exactly as it did before this tranche. That is the
formalism-optional law, measured rather than promised.

### 2. The regression test, mutation-proven

    $ python -m pytest tests/test_criticism_premises.py -q
    9 passed

Nine tests: the ν carries exactly one `EVIDENCE` ref naming the declared
premise; refuting that premise returns the target to `accepted` in the same
pass; a criticism declaring nothing keeps today's behaviour and is NOT weakened
by an unrelated refutation; an empty declaration records no decline and costs
nothing; an id absent from the record declines typed (`unknown-premise`), mints
nothing and leaves the target `accepted`; the compact contract names the legal
premises in its schema enum and refuses an unknown handle; the field is optional
on BOTH criticism outputs; an undeclared criticism canonicalises to the bytes it
always did; and the F2 known gap is recorded.

Mutation proof — three independent mutations, each turning the tranche's own
tests red, each reverted:

| mutation | result |
|---|---|
| delete the ν-interface construction in `_argument_trial_steps` | 2 failed (registration + reinstatement) |
| change `RefRole.EVIDENCE` to `RefRole.DEPENDENCE` on that same interface | 2 failed — the closure, not the ref, is what does the work |
| delete `premises_essential=` from `crit_argumentative`'s trial dispatch | 3 failed — the threading is load-bearing, not decoration |

Also mutation-proved: the narrowed successor test. Adding
`from deepreason.successor import route` to `crit.py` goes red, and so does
rewriting an existing `scratch` mention away — the second is why the pinned
counts were kept beside the added-line scan rather than replaced by it.

### 3. No regression

Full gate, run on an otherwise idle box, never concurrently with `docs_verify`:

    $ python -m pytest tests/ -q -n 4
    5081 passed, 6 skipped in 1094.92s (0:18:14)

That run predates the F2 tripwire and the map's Verified-at stamps. Re-run over
the delivered tree, everything in place:

    $ python -m pytest tests/ -q -n 4
    5082 passed, 6 skipped in 1079.44s (0:17:59)

One more test than the earlier run, which is the F2 tripwire. 0 failed both
times.

Map gate:

    $ python tools/docs_verify.py
    80 documents, 1384 checks -> 7 failed        (first run)
    $ python tools/docs_verify.py --failed
    6 failed                                     (after the repair below)
    $ python tools/docs_verify.py --audit
    1 finding
    $ python tools/docs_verify.py --links
    0 dangling reference(s), 80 document(s)

**Delta against `docs/AUDIT_BASELINES.md`: ZERO.** That file gives 5 OR 6 failed
on a shallow clone (this container reports `is-shallow-repository true`), and
names every row: `SEAM-llm-x-rules.md:54` (unparseable check, parked P3 — and
the single finding that keeps `--audit` above zero), `CON-run-identity.md:211`,
`:213`, `:215` (git-history checks needing a full clone),
`INV-frozen-surfaces.md:206` (the `transport_failure` census, parked P-D3), and
`INV-frozen-surfaces.md:876` (the judge-canary row, which reads a branch ref
this container was not cloned with). All six present, nothing else.

**The seventh was mine, and it is repaired.**
`SEAM-evaluation-x-ontology.md:216` pins the import census across the evaluation
side: `assert len(I)==14`. Adding `from deepreason.ontology.artifact import
RefRole` to `informal/trial.py` made it 15. Re-derived before touching the
document: the same TWELVE names cross the seam and the same FOURTEEN stay out —
only the statement count moved, and `RefRole` was already among the twelve. So
the load-bearing claim ("evaluation cannot author a log line") is untouched and
the incidental count is corrected in prose and in the check, in this tranche's
commit. This is the map working as designed: a claim rotted the moment the code
moved, and said so.

### 4. The stored critic form renders unchanged when the field is absent

    $ python -m pytest tests/test_crit_pack_legacy_golden.py \
        tests/test_conj_pack_legacy_golden.py tests/test_role_prompt_registry.py -q
    passed, with tests/fixtures/*_pack_legacy_v0/*.txt UNEDITED

No golden file was touched. This is why no reference-menu declaration was
registered for the new field — a menu renders INTO the pack and would have moved
them. PARKED P3 carries that as its own tranche.

## Frozen surfaces

    $ python tools/blast_radius.py --files <the four> --symbols <the seven>
    "frozen_surface_contacts": []
    "frozen_adjacent_contacts": []
    "frozen_surface_verdict": "CLEAR"

NO CONTACT, as forecast. No grant was needed and none was requested.

## Budget

    $ python tools/diff_budget.py 323fefb53 --ceiling 150 --paths <the five source files>
    {"total_insertions": 81, "ceiling": 150, "verdict": "WITHIN"}

## Map obligations

`CON-warrants-and-attacks.md` gains the rule with two checks, a
`Where to change what` row, and a Traps entry naming this tranche;
`CON-criticism-source.md` gains a table row and a check;
`SEAM-rules-x-scratch.md` re-words rule 6's measurement, follows the rename and
gains a Traps entry; `SEAM-evaluation-x-ontology.md` carries the count repair;
`docs/ERRATA.md` gains E80. All in the same commits as the code.

`Verified-at:` advanced to `696c4fd89` on those four documents. Honest reading
of that stamp: every check in all four ran in this session — three green in the
full run at that tree, the fourth green after its own repair, which lands in the
delivery commit rather than in `696c4fd89`. The stamp is therefore conservative
by one commit, which SCHEMA.md permits ("a stale stamp is honest, a false one is
not").

## What this does NOT establish

- **No live evidence.** Everything above is offline: mock endpoints, a stub
  root, the public `Harness` API. The audit's own census over 86 committed roots
  found `RefRole.EVIDENCE` on a ν only through `rules/vision.py`, and no root
  ran a vision criticism — so the branch has never been taken by any run, and
  after this fix it is REACHABLE rather than TAKEN. How often a real critic
  fills the field, and whether what it names is any good, is unmeasured.
- **Nothing about progress over a no-harness baseline.** The 2026-09-03 success
  law is not what this measures. A documented rule now has a producer; whether
  criticisms that can be undermined make the harness's output materially better
  than one model call is a separate experiment.
- **F2 is unfixed and recorded as such.** An UNDECIDED essential premise still
  leaves its target refuted. Different cause (pass order in `adjudication/`),
  out of scope by GOAL.md and by the monitor's instruction, asserted as a
  tripwire and parked as P4 with a ready-to-send prompt.
- **The direct transport pays more for a bad id than the compact one.** A
  hallucinated premise on the compact road is a repair ladder; on the direct
  road it declines the whole criticism. Correct ("creates nothing, never a
  silent drop") but blunter, and recorded in RESULTS.md as the shape a later
  reader would want to improve.
