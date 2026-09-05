# Diagnosis: the defended trial mints its criticism's validity node with an EMPTY interface, and no wire field exists to fill it

## THE STOP, CLASSIFIED

**No typed run source exists for this defect, and all three kinds are absent.**
The failure is in the installed package's public `Harness` API, not in any run:
there is no run root, no `root-no-log` directory, and no home with a cached
qualification. `deepreason stop-report` says so in its own words:

```
$ deepreason stop-report experiments/2026-09-05-criticism-premise-declaration
experiments/2026-09-05-criticism-premise-declaration is neither a run root
(no log.jsonl) nor a home holding one or a qualification record
```

In place of section 4, the instrument's own typed envelope — the §0 script of
`docs/proposals/OIS_1_1_to_DeepReason_configuration.md`, re-run by this window
at `323fefb53` against the editable install, verbatim:

```
$ python scratchpad/s0.py
DEPENDENCE ('refuted', 'suspended_unsupported')
EVIDENCE   ('accepted', 'refuted')
```

Both tuples reproduce the monitor's 2026-09-05 report exactly. The pair is the
whole evidence base for what follows: the same four artifacts, the same
refutation of the premise, and the only difference is the ROLE on the ref the
criticism's validity node carries.

---

Primary cause: the two branches differ only in which closure in
`adjudication/edges.py` `build_att` can see the criticism's ground.
`RefRole.EVIDENCE` on the validity node ν enters the evidence closure, which
walks the ref's dependence lineage, lifts the attack on the premise ONTO ν, and
then — by the ordinary validity-node closure — disables every carrier of the
warrant beneath ν before the grounded pass, so the target reinstates in pass
one. `RefRole.DEPENDENCE` enters no closure at all: it is a support edge in
`dep`, so pass 2 demotes the criticism itself to `SUSPENDED_UNSUPPORTED` and
leaves the attack edge it already contributed standing, which is why the target
stays `refuted`. **Neither closure is defective.** The defect is upstream and is
a MISSING PRODUCER: the one argumentative mint site that carries a prose case —
`informal/trial.py::_argument_trial_steps` — creates ν with no interface at all,
and `llm/contracts.py::ArgumentativeCriticOutput` has no field in which a critic
names the artifacts its case essentially relies on, so nothing could fill that
interface even if the site accepted one. The correct branch is unreachable from
the wire, exactly as the source proposal states.

The comparison that makes this a defect rather than a design choice is inside
the tree: `rules/vision.py:104` — another argumentative mint site — already
builds its ν as
`Interface(refs=[Ref(target=s, role=RefRole.EVIDENCE) for s in shot_ids])`,
declaring the screenshots its case rests on. And
`rules/warrants.py::register_fail_warrant`'s `manifest_ref` keyword does the
same thing for demonstrative verdicts, with a docstring that states the reason
in full ("That role and no other ... a MENTION would be readable and inert").
The road is built, documented, tested and used. The prose criticism road is the
one that does not take it.

Evidence:

- **Record-derived, non-code (the reproduction above):** `('refuted',
  'suspended_unsupported')` vs `('accepted', 'refuted')` over the identical
  four-artifact graph. Only the `RefRole` moved. This rules out every
  explanation that does not live in the closure selection.
- `docs/map/CON-warrants-and-attacks.md`, the rule "A verdict may declare what
  it rests on, and that declaration is the evidence closure's ONLY entry point
  (Rung D / E-1)" — with its two passing `check:` lines. The closure is
  documented as the entry point; nothing on the criticism road enters it.
- `docs/map/CON-warrants-and-attacks.md`, the rule "Four closure rules widen
  `att`, all of them by lifting an existing attack onto a validity node and
  then onto every carrier of the warrant beneath it ... the closures run to
  convergence, so a refuted standard reinstates its victims in the same pass."
  Reinstatement in one pass is the documented behaviour the EVIDENCE tuple
  shows and the DEPENDENCE tuple does not reach.
- Mint-site census, run this window over the whole tree
  (`grep -rn "Warrant(" src/deepreason --include=*.py` and
  `grep -rn "register_fail_warrant" src/deepreason --include=*.py`):
  six hand-built `Warrant(...)` constructions and eighteen
  `register_fail_warrant` call sites. Of the five ARGUMENTATIVE hand-built
  sites, exactly one (`rules/vision.py`) declares its ground on ν; the other
  four (`informal/trial.py` ×2, `rules/experiment.py`, `rules/relatedness.py`)
  create a bare ν. Only ONE of those four is fed by an LLM critic's prose case
  against a single target: `_argument_trial_steps`. The pairwise site rules on
  a rivalry, and the experiment/relatedness sites carry harness-composed
  rulings, not a critic's declared premises.
- `llm/wire.py::CompactCritic` — the form the `argumentative_critic` seat
  actually fills — carries `cited_input_aliases`, and
  `CriticWireContract.compile` resolves those aliases and then **folds them
  into the case TEXT** (`parts.append("cites: " + ", ".join(cited))`). So the
  seat can already point at artifacts, and the pointing is dissolved into prose
  before any mint site could register it. This is the nearest existing thing to
  the missing field, and it is not it: "cited" is not "essential", and its
  resolution is discarded as structure.

Implicated code:
  - `src/deepreason/informal/trial.py:1064-1076` — ν built with no interface;
    the argumentative warrant beneath it.
  - `src/deepreason/llm/contracts.py:112-145` — `ArgumentativeCriticOutput`;
    no field names the criticism's own essential premises (`premise` is a
    presupposition of the PROBLEM, as its own comment says).
  - `src/deepreason/llm/wire.py:2692-2755` — `CompactCritic` /
    `CriticWireContract`; `ALIAS_ARRAY_FIELDS` is the existing, working road
    by which an alias-bearing field becomes a schema enum and an unknown
    handle becomes a failed call rather than a silent drop.

Falsifiable prediction (what `dr-reproduce` must show):
  Taking the §0 DEPENDENCE scenario and changing NOTHING except adding one
  `Ref(target=k.id, role=RefRole.EVIDENCE)` to the criticism's validity-node
  interface — leaving the criticism artifact's own DEPENDENCE ref exactly where
  it is — must flip the pair to `('accepted', 'refuted')`.

      python .../repro_nu_evidence.py
      # expected: DEPENDENCE-on-criticism + EVIDENCE-on-nu -> ('accepted', 'refuted')

  If it does not flip, this diagnosis is wrong and the cause is inside the
  closure rather than at the mint site — which would be the STOP condition
  GOAL.md names, because `adjudication/` is out of scope.

Ruled out: **that pass 2's `SUSPENDED_UNSUPPORTED` rule is the defect.**
`CON-warrants-and-attacks.md` states it as law — "refuting a premise never
refutes its dependents: pass 2 gives them `SUSPENDED_UNSUPPORTED`, because
orphaned is not false" — with a passing check
(`f({'d':'accepted','p':'refuted'}, [('d','p')]) == {'p':REFUTED,'d':SUSPENDED_UNSUPPORTED}`).
That rule is about what happens to the DEPENDENT; it says nothing about the
attack the dependent already carried, and the EVIDENCE branch shows the tree
already handles that case correctly by a different road. Changing pass 2 would
be an `adjudication/` edit, and it would break the documented rule to fix a
defect that is not there.

Second, independent finding — PARKED, not pursued here: a criticism's
`cited_input_aliases` are resolved and then flattened into the case string, so
the record keeps no structured trace of what a criticism pointed at even when
the critic did point. See PARKED.md P1.
