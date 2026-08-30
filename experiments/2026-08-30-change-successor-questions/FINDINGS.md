# FINDINGS — the adversarial skeptic pass lane B never had
Recorded 2026-08-30 by the pickup window, as its first act after the pass
returned. `HANDOFF-lane-B.md` named the missing skeptic pass as "the single
most important thing on this page"; this file is its result.

Five lenses ran, each an independent skeptic in its own git worktree, each
RE-RUNNING lane B's claims rather than reading them. **35 findings, every one
reproduced by the skeptic that raised it**, from 155 re-run claims and 33+
source mutations. All five worktrees finished byte-clean.

The operator removed the second (verify) phase on the ground that verification
is already done, so each finding below stands on the commands and output of the
lens that raised it. Where a lens could not fully establish something it was
required to say so; none of the 35 is marked partial.

| severity | count | meaning |
|---|---|---|
| **blocking** | 3 | the branch must not be integrated until fixed |
| **major** | 20 | a claim must be corrected, or a real gap exists |
| **minor** | 12 | accurate but imprecise |

**The headline.** All three blocking findings are the same defect wearing three
faces: `tests/test_successor_law_line.py` — the deliverable `DELIVERY.md` offers
as proof of the operator's "never penalized" law — is a set of SUBSTRING
SEARCHES over source text, not a behavioural guarantee. A rank penalty, an
admission rejection and a status flip that each punish a critic for filling the
optional field were all constructed, all changed real behaviour, and all left
the 42 tests green.

## Lens coverage

| lens | findings | claims re-run | tree clean |
|---|---|---|---|
| S1 never-penalized | 8 | 21 | True |
| S2 configurability | 5 | 20 | True |
| S3 scope+numbers | 9 | 29 | True |
| S4 mutation-proof | 7 | 55 | True |
| S5 map checks | 6 | 30 | True |

One lens is qualified: S4's assigned worktree was checked out at `84514a028`
(base `main`), which does not contain lane B at all. It disclosed this, took a
read-only `git archive` of `d296ca2bd` into the scratchpad and measured there,
leaving its worktree untouched at an empty `git status`. Its findings are
therefore measured on this branch's content, by a different path than the other
four.

---

## F1 — A rank penalty on the optional field survives all four law-line pins

**BLOCKING** · lens S1 never-penalized · `tests/test_successor_law_line.py:93`

**The claim under test.** tests/test_successor_law_line.py, module docstring: "No successor field, destination row, receipt or minted problem may feed a label, a warrant, a rank, an admission decision, or any adjudication pass." DELIVERY.md R1 row: "done | tests/test_successor_law_line.py (8 tests, 4 pins)".

**Commands.**

```
cd /home/user/DeepReason/.claude/worktrees/wf_9b72aacb-3ed-1
export PYTHONPATH=$PWD/src:$PWD/mini

# MUTATION: in src/deepreason/scheduler/scheduler.py, inside the LIVENESS_QUEUE
# rank() closure (~line 1177), after the `weight = 1.0 if not survivors...` line insert:
#
#                 _proposed = any(
#                     getattr(b.body, "unfinished", None) == "Successor question"
#                     and getattr(b.provenance, "origin", None) == p.id
#                     for b in self.harness.scratch_state.blocks.values()
#                 )
#                 if _proposed:
#                     weight = weight * 0.1
#
# (no forbidden name from FORBIDDEN_NAMES appears anywhere in the patch)

python -m pytest tests/test_successor_law_line.py -q
python -m pytest tests/test_successor_law_line.py tests/test_successor_registry.py \
  tests/test_successor_questions.py tests/test_successor_minting.py \
  tests/test_successor_rank_tie.py -q -p no:randomly
python -m pytest tests/test_scheduler.py tests/test_controller.py -q -p no:randomly

# behavioural probe (rank_demo.py, run under the same PYTHONPATH):
#   two seed problems p-a and p-b, identical, cycle 0, Config(LIVENESS_QUEUE=True, N_SCHOOLS=0);
#   run once with nothing routed, once after
#   route(h, _Cfg(), problem_id="p-a", question="what would settle this?");
#   print Scheduler(h, LLMAdapter({}, h.blobs), cfg)._select_problem().id each time
python rank_demo.py
```

**Observed.**

```
$ python -m pytest tests/test_successor_law_line.py -q
........                                                                 [100%]
8 passed in 0.12s

$ python -m pytest <the five successor files> -q -p no:randomly
..........................................                               [100%]
42 passed in 2.22s

$ python -m pytest tests/test_scheduler.py tests/test_controller.py -q -p no:randomly
....................                                                     [100%]
20 passed in 12.20s

$ python rank_demo.py          # MUTATED tree
no question routed               -> scheduler picks p-a
question routed under p-a        -> scheduler picks p-b
DIFFERENT: filling the optional field moved the rank

$ python rank_demo.py          # after revert, SHIPPED tree (control)
no question routed               -> scheduler picks p-a
question routed under p-a        -> scheduler picks p-a
SAME PICK: rank did not move
```

**Why it is a defect.** Pin 1 is the ONLY pin that covers rank, and it is a substring search over source text for 11 literal names. Nothing in the 42-test deliverable observes ranking behaviour with and without a routed question, so any rank read spelled without one of those 11 substrings passes. The shipped code is clean (the control run proves that), but the artifact DELIVERY.md offers as proof of the operator's "never penalized" law cannot detect its violation on the rank surface — which is precisely the surface the law names first. The mutation here is not contrived: it reads the routed scratch block through the ordinary public block marker the tranche itself writes (route.py line 69, `"unfinished": "Successor question"`), which is how a future consumer would naturally find it.

**Proposed fix.**

Add a BEHAVIOURAL rank pin to tests/test_successor_law_line.py, beside pin 4:

    def test_a_routed_question_does_not_move_problem_selection(tmp_path):
        for liveness in (True, False):
            picks = []
            for routed in (None, "p-a"):
                h = Harness(tmp_path / f"{liveness}-{routed}")
                h.register_commitment(Commitment(id="k-q", eval="predicate:True"))
                for pid in ("p-a", "p-b"):
                    h.register_problem(Problem(id=pid, description=pid, criteria=["k-q"],
                        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []})))
                if routed:
                    route(h, _Config(), problem_id=routed, question="what settles it?")
                s = Scheduler(h, LLMAdapter({}, h.blobs),
                              Config(LIVENESS_QUEUE=liveness, N_SCHOOLS=0))
                picks.append(s._select_problem().id)
            assert picks[0] == picks[1], (liveness, picks)

This test goes red under the mutation above (which pin 1 misses) and is cheap (<1s).

---

## F2 — An admission rejection triggered by the optional field survives all four pins when written one call-frame above the guard

**BLOCKING** · lens S1 never-penalized · `tests/test_successor_law_line.py:195`

**The claim under test.** tests/test_successor_law_line.py line 195, pin 3: "R1, behaviourally. The gate decides on CONTENT, and a proposed question is not content: the same candidate must receive the same verdict and the same reason string whether a successor question was routed beside it or not."

**Commands.**

```
cd /home/user/DeepReason/.claude/worktrees/wf_9b72aacb-3ed-1
export PYTHONPATH=$PWD/src:$PWD/mini

# MUTATION: src/deepreason/rules/conj.py, immediately after
#   `admitted, reason = anti_relapse.check(...)` (~line 2489) and before
#   `if diagnostics is not None:` insert:
#
#         if admitted and any(
#             getattr(b.body, "unfinished", None) == "Successor question"
#             and getattr(b.provenance, "origin", None) == problem_id
#             for b in harness.scratch_state.blocks.values()
#         ):
#             admitted, reason = False, "proposal-pending"
#
# rules/conj.py IS one of pin 1's four DECIDING_PACKAGES; the patch contains
# no name from FORBIDDEN_NAMES.

python -m pytest tests/test_successor_law_line.py tests/test_successor_registry.py \
  tests/test_successor_questions.py tests/test_successor_minting.py \
  tests/test_successor_rank_tie.py -q -p no:randomly

# behavioural probe (admission_demo.py): seed problem pi-1 + commitment k-true,
# LLMAdapter({"conjecturer": MockEndpoint(lambda p: _vs("one idea","another idea"))}),
# conj(h, "pi-1", adapter, Config(VS_K=2, NEAR_DUP_EPS=None)); count h.state.artifacts.
# Run once with nothing routed, once after route(h,_Cfg(),problem_id="pi-1",question=...).
python admission_demo.py
```

**Observed.**

```
$ python -m pytest <the five successor files> -q -p no:randomly
..........................................                               [100%]
42 passed in 2.28s

$ python admission_demo.py     # MUTATED tree
no question routed          -> 2 artifact(s) admitted
question routed under pi-1  -> 0 artifact(s) admitted
DIFFERENT: filling the optional field changed the admission decision

$ python admission_demo.py     # after revert, SHIPPED tree (control)
no question routed          -> 2 artifact(s) admitted
question routed under pi-1  -> 2 artifact(s) admitted
SAME: admission did not move
```

**Why it is a defect.** Pin 3 probes exactly one function, `anti_relapse.check`, called directly. The admission DECISION in production is made by the caller: `rules/conj.py` reads `admitted` and does `observe_candidate(..., "reject", reason); harness.record_measure(inputs=[f"gate:{reason}", ...]); continue`. A penalty applied there is a real admission rejection of every candidate under a problem whose critic filled the optional field — the operator's law violated on the admission surface — and the whole 42-test deliverable stays green. (I confirmed pin 3 does catch the same penalty when it is written INSIDE `anti_relapse.check`; see checks_run. The gap is the frame, not the concept.)

**Proposed fix.**

Extend pin 3 from the guard to the DECISION. Add to tests/test_successor_law_line.py:

    def test_a_routed_question_does_not_change_what_conj_admits(tmp_path):
        admitted = []
        for routed in (None, "pi-1"):
            h = Harness(tmp_path / f"run-{routed}")
            h.register_commitment(Commitment(id="k-true", eval="predicate:True"))
            h.register_problem(Problem(id="pi-1", description="seed", criteria=["k-true"],
                provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []})))
            if routed:
                route(h, _Config(), problem_id=routed, question="what settles it?")
            adapter = LLMAdapter({"conjecturer": MockEndpoint(
                lambda p: json.dumps({"candidates": [{"content": c, "typicality": 0.5}
                                     for c in ("one idea", "another idea")]}))},
                h.blobs, retry_max=2)
            conj(h, "pi-1", adapter, Config(VS_K=2, NEAR_DUP_EPS=None))
            admitted.append(len(h.state.artifacts))
        assert admitted[0] == admitted[1], admitted

It runs in well under a second and goes red under the mutation above.

---

## F3 — Pin 4 does not detect a status change: a critic that fills the field can be made to lose its refutation (REFUTED -> ACCEPTED) with all 42 tests green

**BLOCKING** · lens S1 never-penalized · `tests/test_successor_law_line.py:236`

**The claim under test.** tests/test_successor_law_line.py line 236, pin 4: "R1. 'Never penalized' means the graph cannot tell the difference." and the module docstring's pin list: "4. no status label differs between a field-filled and a field-absent run on one graph."

**Commands.**

```
cd /home/user/DeepReason/.claude/worktrees/wf_9b72aacb-3ed-1
export PYTHONPATH=$PWD/src:$PWD/mini

# MUTATION, two hunks, both idiomatic and containing no FORBIDDEN_NAMES literal
# inside a deciding package:
#
# (a) src/deepreason/llm/contracts.py, after ArgumentativeCriticOutput:
#         PROPOSAL_FIELD = "successor_question"
#
# (b) src/deepreason/rules/crit.py, replace
#         if not output.attack or not output.case.strip():
#     with
#         from deepreason.llm.contracts import PROPOSAL_FIELD
#         if (
#             not output.attack
#             or not output.case.strip()
#             or getattr(output, PROPOSAL_FIELD, None)
#         ):

python -m pytest tests/test_successor_law_line.py tests/test_successor_registry.py \
  tests/test_successor_questions.py tests/test_successor_minting.py \
  tests/test_successor_rank_tie.py -q -p no:randomly

# behavioural probe (exposure_demo.py), mirroring tests/test_criticism_authority.py::_court:
#   Config(ARGUMENTATIVE_AUTHORITY="trial_required",
#          ADJUDICATION_STATUS_AUTHORITY_ENABLED=True, TRIAL_PARAPHRASE_N=2),
#   endpoints argumentative_critic / judge x2 (gemma-test, qwen-test) / variator / defender,
#   critic payload {"attack": true, "case": CASE} run once bare and once with
#   "successor_question" added; print harness.state.status[target.id].
python exposure_demo.py

# also probe what pin 4's own fixture contains (pin4_probe.py):
#   rebuild _graph() from the test and print the labels and the att edge set.
python pin4_probe.py
```

**Observed.**

```
$ python -m pytest <the five successor files> -q -p no:randomly
..........................................                               [100%]
42 passed in 2.20s

$ python exposure_demo.py      # MUTATED tree
successor_question EMPTY  -> target status Status.REFUTED
successor_question FILLED -> target status Status.ACCEPTED
DIFFERENT: filling the optional field cost the critic its refutation

$ python exposure_demo.py      # after revert, SHIPPED tree (control)
successor_question EMPTY  -> target status Status.REFUTED
successor_question FILLED -> target status Status.REFUTED
SAME: the optional field cost the critic nothing

$ python pin4_probe.py         # what pin 4 actually compares, on the shipped tree
off labels: [<Status.ACCEPTED: 'accepted'>, <Status.ACCEPTED: 'accepted'>]
on  labels: [<Status.ACCEPTED: 'accepted'>, <Status.ACCEPTED: 'accepted'>]
off att edges: set()
on  att edges: set()
distinct label values in the comparison: {<Status.ACCEPTED: 'accepted'>}
```

**Why it is a defect.** Pin 4's fixture builds a graph with ZERO attack edges, so every artifact in both runs is trivially `accepted` and the comparison `off_labels == on_labels` ranges over a single label value. The one thing that could move a label — a criticism that actually attacks — never exists in either run, so the pin cannot observe a penalty applied to a status contest. This is the sharpest form of the operator's law ("filling it earns a critic nothing and leaving it empty costs a critic nothing", quoted verbatim in src/deepreason/llm/contracts.py lines 137-145) and it is exactly what the mutation breaks: the same case, same court, same rulings, and the target ends ACCEPTED instead of REFUTED purely because the optional field was filled. All 42 tests, including pin 4 and its companion attack-edge test, stay green.

**Proposed fix.**

Give pin 4 a graph that has a status contest in it. Add to tests/test_successor_law_line.py a test that drives the same court as tests/test_criticism_authority.py::test_trial_required_needs_court, once with and once without `successor_question` set on the critic payload, and asserts the target's final Status, the att edge set and the warrant count are identical:

    def test_filling_the_field_costs_the_critic_no_authority(tmp_path):
        out = []
        for question in (None, "what would settle the echo reading?"):
            payload = {"attack": True, "case": CASE}
            if question:
                payload["successor_question"] = question
            h = Harness(tmp_path / f"run-{bool(question)}")
            ...  # _court(...) as in test_criticism_authority.py
            crit_argumentative(h, target.id, adapter, config)
            out.append((h.state.status[target.id], set(h.state.att), len(h.warrants)))
        assert out[0] == out[1], out

Keep the existing attack-free comparison as well — it is not wrong, it is just not sufficient — and correct the module docstring's pin-4 line to say what it covers: "4. routing adds no artifact and no attack edge, so no status label on the shared graph can move."

---

## F4 — Pin 1's DECIDING_PACKAGES omits two files that make admission decisions; four forbidden names appear there literally and the pin stays green

**MAJOR** · lens S1 never-penalized · `tests/test_successor_law_line.py:67`

**The claim under test.** tests/test_successor_law_line.py lines 63-72: "The packages that DECIDE something: what a status is, what a problem is worth working on, whether a candidate is admitted, whether a prose case survives a trial. There is NO permitted exception, and that is the point." Repeated in docs/map/CON-successor-questions.md line 74: "The four packages that DECIDE anything -- scheduler, adjudication, informal, rules -- name no part of this machinery."

**Commands.**

```
cd /home/user/DeepReason/.claude/worktrees/wf_9b72aacb-3ed-1
export PYTHONPATH=$PWD/src:$PWD/mini

# which files call the admission gate and branch on its answer?
grep -rn "anti_relapse.check" src/deepreason/

# MUTATION: src/deepreason/workflow/conjecture_recovery.py, before `if not admitted:`
# (~line 561), insert -- deliberately using the FORBIDDEN literals:
#
#         from deepreason.successor import SuccessorDeclaration, resolve  # noqa: F401
#
#         if admitted and any(
#             b.body.unfinished == "Successor question"
#             for b in harness.scratch_state.blocks.values()
#         ):
#             # successor_question filled -> SUCCESSOR_MINTING_ENABLED
#             admitted, reason = False, "minting_notices"

python -m pytest tests/test_successor_law_line.py -q -p no:randomly
grep -c "successor_question\|deepreason.successor\|SuccessorDeclaration\|minting_notices" \
  src/deepreason/workflow/conjecture_recovery.py
```

**Observed.**

```
$ grep -rn "anti_relapse.check" src/deepreason/
src/deepreason/workflows/website.py:1233:        admitted, reason = anti_relapse.check(
src/deepreason/rules/conj.py:2489:        admitted, reason = anti_relapse.check(
src/deepreason/rules/synth.py:78:    admitted, _ = anti_relapse.check(
src/deepreason/workflow/conjecture_recovery.py:553:            admitted, reason = anti_relapse.check(

$ python -m pytest tests/test_successor_law_line.py -q -p no:randomly
........                                                                 [100%]
8 passed in 0.13s

$ grep -c "successor_question|deepreason.successor|SuccessorDeclaration|minting_notices" src/deepreason/workflow/conjecture_recovery.py
3
```

**Why it is a defect.** Four of the eleven FORBIDDEN_NAMES appear verbatim in a file that decides whether a candidate is admitted, and pin 1 passes, because `src/deepreason/workflow/` is not in DECIDING_PACKAGES. Two of the four production callers of `anti_relapse.check` (workflow/conjecture_recovery.py, workflows/website.py) sit outside the four listed packages, so the pin's own stated scope -- "whether a candidate is admitted" -- is not covered even for a maximally careless implementer. This makes the map claim at CON-successor-questions.md:74 narrower than it reads: the four packages naming nothing does not entail that nothing that admits names it.

**Proposed fix.**

Derive the package list from the callers instead of hard-coding four names. In tests/test_successor_law_line.py replace the DECIDING_PACKAGES tuple with the four packages PLUS the two admission callers, and add a positive anchor that the caller census is complete:

    DECIDING_PACKAGES = (
        pathlib.Path("src/deepreason/scheduler"),
        pathlib.Path("src/deepreason/adjudication"),
        pathlib.Path("src/deepreason/informal"),
        pathlib.Path("src/deepreason/rules"),
        pathlib.Path("src/deepreason/workflow"),
        pathlib.Path("src/deepreason/workflows"),
    )

and assert the anchor that keeps it honest:

    callers = {p.parts[2] for p in pathlib.Path("src/deepreason").rglob("*.py")
               if "anti_relapse.check" in p.read_text()}
    assert callers <= {pkg.name for pkg in DECIDING_PACKAGES}, callers

Also correct docs/map/CON-successor-questions.md line 74 to name six packages, or to say "the packages that decide anything, taken as the four rule/adjudication packages plus every caller of the admission gate".

---

## F5 — Pin 2's claim that no shipped row can carry a weight is false: a subclassed declaration carries rank_bonus=2.5 and the pin passes

**MAJOR** · lens S1 never-penalized · `tests/test_successor_law_line.py:156`

**The claim under test.** tests/test_successor_law_line.py lines 136-157: "Checked over the MODEL rather than over today's rows, so a destination added tomorrow cannot introduce one." and "Every shipped row is an instance of that model, so no row can carry a field the model does not declare." Echoed in src/deepreason/successor/registry.py lines 29-31: "There is no numeric field on a declaration, so there is no rank, weight or admission score for any configuration to set."

**Commands.**

```
cd /home/user/DeepReason/.claude/worktrees/wf_9b72aacb-3ed-1
export PYTHONPATH=$PWD/src:$PWD/mini

# CONTROL first -- pin 2 does catch a numeric on the base model:
#   add `rank_bonus: float = 0.0` to SuccessorDeclaration in
#   src/deepreason/successor/registry.py, then:
python -m pytest tests/test_successor_law_line.py -q -p no:randomly

# INVERSION -- same weight, reached by subclass. Revert the above, then in
# src/deepreason/successor/registry.py, just before the DESTINATIONS dict:
#
#   @dataclass(frozen=True)
#   class WeightedDeclaration(SuccessorDeclaration):
#       rank_bonus: float = 2.5
#
# and change the shipped row's constructor from SuccessorDeclaration( to
# WeightedDeclaration(  .

python -m pytest tests/test_successor_law_line.py tests/test_successor_registry.py \
  tests/test_successor_questions.py tests/test_successor_minting.py \
  tests/test_successor_rank_tie.py -q -p no:randomly

# pin2_probe.py: print declaration_field_types(), its numeric subset,
# isinstance(row, SuccessorDeclaration), type(row).__name__, row.rank_bonus
python pin2_probe.py
```

**Observed.**

```
CONTROL (numeric on the base model) -- pin 2 fires:
>       assert not numeric, numeric
E       AssertionError: ['rank_bonus']
E       assert not ['rank_bonus']
tests/test_successor_law_line.py:149: AssertionError
1 failed, 7 passed in 0.14s

INVERSION (same numeric, via subclass):
$ python -m pytest <the five successor files> -q -p no:randomly
..........................................                               [100%]
42 passed in 2.24s

$ python pin2_probe.py
declaration_field_types() -> ['authority', 'default', 'enforcement', 'id', 'routes', 'warning']
numeric annotations on the model -> []
isinstance(row, SuccessorDeclaration) -> True
type(row) -> WeightedDeclaration
row.rank_bonus -> 2.5
```

**Why it is a defect.** `declaration_field_types()` reads `get_type_hints(SuccessorDeclaration)` and `dataclasses.fields(SuccessorDeclaration)` -- the BASE class only -- while the row assertion uses `isinstance`, which a subclass satisfies. So the shipped default destination row can carry a float weight and both of pin 2's assertions pass. The pin's own docstring promise ("a row added tomorrow cannot introduce a weight the model does not allow") is therefore false, and it is false in exactly the direction the modularity law makes easy: `register_destination()` performs no type check at all, so a third-party destination row may be any object.

**Proposed fix.**

In tests/test_successor_law_line.py::test_a_successor_declaration_carries_no_number, replace the isinstance loop (line 156) with an exact-type check plus a value census over each row:

    for row in (*DESTINATIONS.values(), *GATES.values()):
        assert type(row) is SuccessorDeclaration, (row, type(row))
        numeric_values = [
            name for name, value in vars(row).items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        ]
        assert not numeric_values, (row.id, numeric_values)

Optionally also make register_destination() refuse a non-exact type, so the guarantee holds for rows registered at runtime as well as for the shipped two.

---

## F6 — Pin 3 never leaves the anti-relapse gate's degraded early return, so a penalty in the gate's real stages is invisible to it

**MAJOR** · lens S1 never-penalized · `tests/test_successor_law_line.py:206`

**The claim under test.** tests/test_successor_law_line.py line 195, pin 3: "the same candidate must receive the same verdict and the same reason string whether a successor question was routed beside it or not. The reason string matters as much as the boolean."

**Commands.**

```
cd /home/user/DeepReason/.claude/worktrees/wf_9b72aacb-3ed-1
export PYTHONPATH=$PWD/src:$PWD/mini

# (A) penalty BEFORE the degraded early return, in src/deepreason/rules/guards/
#     anti_relapse.py::check, right after `status = harness.state.status`:
#
#     if any(getattr(b.body, "unfinished", None) == "Successor question"
#            for b in harness.scratch_state.blocks.values()):
#         return False, "hash: a question was proposed here"
python -m pytest tests/test_successor_law_line.py -q -p no:randomly

# (B) the SAME penalty moved five lines down, immediately after
#     `return True, "admitted-degraded:" + ",".join(missing)` (i.e. into the
#     stage-2/3 body the gate actually runs in production):
python -m pytest tests/test_successor_law_line.py -q -p no:randomly
```

**Observed.**

```
(A) before the early return -- pin 3 fires:
E       AssertionError: ((True, 'admitted-degraded:domain,embedder,near_dup_eps'), (False, 'hash: a question was proposed here'))
tests/test_successor_law_line.py:214: AssertionError
FAILED tests/test_successor_law_line.py::test_admission_is_byte_identical_with_and_without_a_successor_question
1 failed, 7 passed in 0.17s

(B) the same penalty five lines lower -- pin 3 is blind:
........                                                                 [100%]
8 passed in 0.13s
```

**Why it is a defect.** Pin 3 calls `anti_relapse.check(artifact, [], harness)` with domain, embedder and near_dup_eps all defaulting to None, so it always takes the `if missing:` fail-open branch and returns `(True, 'admitted-degraded:domain,embedder,near_dup_eps')`. It therefore exercises roughly the first twenty lines of a ~120-line gate and never reaches the semantic-trigger or battery-equivalence stages that decide admission in a configured run. The reason string it pins is the DEGRADED one, not the one a real run produces. This is measured, not inferred: the identical penalty is caught above the early return and missed below it.

**Proposed fix.**

Make pin 3 exercise the configured gate. In tests/test_successor_law_line.py, pass a real scope to both calls so the probe reaches stages 2-3 (the repo already ships a deterministic embedder for exactly this):

    from deepreason.llm.embedder import HashingEmbedder
    from deepreason.rules.guards.anti_relapse import relapse_domain

    domain = relapse_domain(artifact, harness, workload_profile="text",
                            problem_family=problem.id, contract_id="conjecturer.v1")
    kwargs = dict(embedder=HashingEmbedder(), near_dup_eps=0.2, domain=domain)
    first = anti_relapse.check(artifact, [], harness, **kwargs)
    ...
    second = anti_relapse.check(artifact, [], harness, **kwargs)
    assert first == second, (first, second)

and assert the probe is not degraded, so a future default change cannot silently return it to the fail-open path:

    assert not first[1].startswith("admitted-degraded"), first

---

## F7 — The law-line docstring's mutation-proof claim overstates the committed transcript: the mutant reads no field and moves no ranking

**MAJOR** · lens S1 never-penalized · `tests/test_successor_law_line.py:29`

**The claim under test.** tests/test_successor_law_line.py lines 28-30: "Pin 1 is mutation-proved (experiments/2026-08-30-change-successor-questions/proof/law_line_pin1_red.txt): THE FIELD wired into the scheduler's own rank key turns it red." (emphasis on "the field"; VALIDATION.md S3b and docs/map/CON-successor-questions.md line 66 both say "the REGISTRY", which is accurate.)

**Commands.**

```
cd /home/user/DeepReason/.claude/worktrees/wf_9b72aacb-3ed-1
export PYTHONPATH=$PWD/src:$PWD/mini

sed -n '1,20p' experiments/2026-08-30-change-successor-questions/proof/law_line_pin1_red.txt

# Re-apply the transcript's own mutant verbatim to src/deepreason/scheduler/scheduler.py:
#                 weight = 1.0 if not survivors_by_problem.get(p.id) else 0.3
# +               from deepreason.successor import resolve as _successor_resolve
# +               bonus = 1.0 if _successor_resolve(self.config).default else 0.0
#                 return (
# -                   -(age * weight),
# +                   -(age * weight) - bonus,

python -m pytest tests/test_successor_rank_tie.py tests/test_scheduler.py \
  tests/test_controller.py -q -p no:randomly
python rank_demo.py    # the differential rank probe from finding 1
```

**Observed.**

```
The committed mutant, from proof/law_line_pin1_red.txt:
+                from deepreason.successor import resolve as _successor_resolve
+                bonus = 1.0 if _successor_resolve(self.config).default else 0.0

Under that mutant, on this tree:
$ python -m pytest tests/test_successor_rank_tie.py tests/test_scheduler.py tests/test_controller.py -q -p no:randomly
.......................                                                  [100%]
23 passed in 5.66s

$ python rank_demo.py
no question routed               -> scheduler picks p-a
question routed under p-a        -> scheduler picks p-a
SAME PICK: rank did not move
```

**Why it is a defect.** The mutant reads `resolve(self.config).default`, which is a module constant (True for the shipped row) and identical for every candidate problem, so `bonus` is the same constant subtracted from every rank key: no ordering changes anywhere, and the successor_question field is never read. It is a syntactic mutant that makes the string `deepreason.successor` appear inside a deciding package -- which is all pin 1 tests. Calling it proof that "the field wired into the rank key turns it red" claims coverage the transcript does not contain, and it is the sentence a later reader will rely on when deciding this surface is protected. The map document and VALIDATION.md say "the registry", which is exact; only the test docstring overstates it.

**Proposed fix.**

Correct tests/test_successor_law_line.py lines 28-30 to match the transcript and add the missing caveat. Replace:

    Pin 1 is mutation-proved (`experiments/2026-08-30-change-successor-questions/
    proof/law_line_pin1_red.txt`): the field wired into the scheduler's own rank
    key turns it red.

with:

    Pin 1 is mutation-proved for SPELLING only
    (`experiments/2026-08-30-change-successor-questions/proof/law_line_pin1_red.txt`):
    naming the registry inside the scheduler's rank key turns it red. That
    mutant reads no successor_question and changes no selection; pin 1 is a
    source-text search, so a rank read spelled without one of FORBIDDEN_NAMES
    passes it. The behavioural guarantee is pinned by
    test_a_routed_question_does_not_move_problem_selection, not by this test.

(If finding 1's behavioural test is not added, the honest wording is the first
two sentences alone, with the last clause dropped.)

---

## F9 — Five of the new map document's fourteen `check:` lines are indented, so docs_verify silently never runs them

**MAJOR** · lens S2 configurability · `docs/map/CON-successor-questions.md:154`

**The claim under test.** CON-successor-questions.md: "A NEW destination enters by REGISTRATION ... which is checkable, and is checked, because a modularity claim without a failable check is decoration." VALIDATION.md: "docs_verify --audit: `1 finding(s)` ... No finding names any document this tranche touched, and none names a vacuous check : PASS". CLAUDE.md: "Every load-bearing claim carries a `check:` shell command at column 0 that must exit 0."

**Commands.**

```
cd /home/user/DeepReason/.claude/worktrees/wf_9b72aacb-3ed-2
export PYTHONPATH=$PWD/src:$PWD/mini
python - <<'PY'
import pathlib, re, sys
sys.path.insert(0, "tools")
import docs_verify as dv
text = pathlib.Path("docs/map/CON-successor-questions.md").read_text(encoding="utf-8")
doc = dv.parse_text(text)
print("checks docs_verify WILL run :", len(doc.checks))
print("parse errors it reports     :", doc.errors)
print("checks WRITTEN in document  :", len(re.findall(r"^[ \t]*`check:", text, re.M)))
for i, l in enumerate(text.splitlines(), 1):
    if re.match(r"^[ \t]+`check:", l):
        print("  dropped at line", i, l.strip()[:70])
PY
sed -n '59p;496,497p' tools/docs_verify.py
bash -c 'test "$(grep -rn "ProblemProvenance.model_validate" --include=*.py src/deepreason/rules/ | wc -l)" -eq 999'; echo "rc=$?"
```

**Observed.**

```
checks docs_verify WILL run : 9
parse errors it reports     : []
checks WRITTEN in the document : 14
checks SILENTLY DROPPED        : 5
dropped, by line:
  line 154: `check: test "$(grep -rn "ProblemProvenance.model_validate" --include=*.py src/deepreason/rules/ | w
  line 160: `check: python -c "from deepreason.llm.contracts import ArgumentativeCriticOutput as O; assert O.mod
  line 168: `check: python -c "import inspect;from pydantic import BaseModel;from deepreason.llm import wire;K=[
  line 175: `check: python -m pytest tests/test_successor_questions.py::test_a_scratch_disabled_run_discloses_in
  line 196: `check: grep -q 'block_role: Literal\["conjecturer", "synthesizer"\]' src/deepreason/run_manifest.py

-- tools/docs_verify.py --
59:_CHECK = re.compile(r"^`check:\s*(?P<cmd>.+?)`\s*$")
496:    assert parse_text("    `check: false`").checks == []
497:    assert parse_text("    `check: false`").errors == []

-- the dropped check IS discriminating when actually run --
rc with -eq 999 (would-be-red) = 1
```

**Why it is a defect.** docs_verify's parser anchors `check:` at column 0 and its own self-test asserts that an indented check yields NO check AND NO error ("An indented check is an EXAMPLE, not a claim"). All five of the document's Traps checks are indented two spaces, so five load-bearing guarantees this tranche wrote — the ONE-producer/outside-rules location invariant, the field-defaults-to-None trap, the wire-field-naming trap, the scratch-disabled disclosure trap, and the author_block frozen-surface trap — are never executed by any gate, are invisible to `--audit` (which is what the tranche cites as proof that none of its checks is vacuous), and cannot fail. Across all 71 map documents there are 1266 column-0 checks and only 10 indented ones; five of those ten are this lane's. The document itself says a claim without a failable check is decoration, and CLAUDE.md states the column-0 rule explicitly.

**Proposed fix.**

In docs/map/CON-successor-questions.md, unindent the five `check:` lines at lines 154, 160, 168, 175 and 196 so each begins at column 0 (the same shape as the already-correct check at line 188). No other text changes. Then re-run each of the five to confirm they exit 0.

---

## F10 — The "17 new checks" split in DELIVERY.md and VALIDATION.md re-measures as 9 + 8, not 12 + 5, and 22 checks were actually written

**MAJOR** · lens S2 configurability · `experiments/2026-08-30-change-successor-questions/DELIVERY.md`

**The claim under test.** DELIVERY.md and VALIDATION.md, identical wording: "new checks: 17, counted mechanically rather than by hand — `git diff 3688713ee..HEAD -- docs/map | grep -c '^+`check:'` -> 17 ... Twelve in `CON-successor-questions.md` (the modularity claim, the row-id absence, the interface `__all__`, the law line, the empty permitted-exception list, the link, the visibility, the shipped defaults, and four Traps checks) and five across the amended documents"

**Commands.**

```
cd /home/user/DeepReason/.claude/worktrees/wf_9b72aacb-3ed-2
git diff 3688713ee..HEAD -- docs/map | grep -c '^+`check:'
git diff 3688713ee..HEAD -- docs/map | grep -cE '^\+[[:space:]]*`check:'
for f in $(git diff 3688713ee..HEAD --name-only -- docs/map); do
  a=$(git diff 3688713ee..HEAD -- "$f" | grep -cE '^\+[[:space:]]*`check:')
  c=$(git diff 3688713ee..HEAD -- "$f" | grep -c '^+`check:')
  printf "%-45s added=%-3s col0added=%s\n" "$f" "$a" "$c"
done
grep -cE '^[[:space:]]*`check:' docs/map/CON-successor-questions.md
```

**Observed.**

```
17
22
docs/map/CON-criticism-source.md              added=2   col0added=2
docs/map/CON-problem-layer-lifecycle.md       added=1   col0added=1
docs/map/CON-scheduler-ranking.md             added=2   col0added=2
docs/map/CON-successor-questions.md           added=14  col0added=9
docs/map/INDEX.md                             added=0   col0added=0
docs/map/SEAM-ontology-x-rules.md             added=1   col0added=1
docs/map/SEAM-rules-x-scratch.md              added=2   col0added=2
--- checks present in the NEW doc (any indent) ---
14
```

**Why it is a defect.** The mechanical total 17 is reproducible, but the narrative that explains it is wrong in BOTH components and the sum is right only by coincidence: the new document contributes 9 tool-visible checks (not twelve) and the five amended documents contribute 8 (not five). The enumeration in the parenthetical also miscounts the Traps section as "four Traps checks" when the document has six. 22 checks were written in total; 17 are executed. The head commit fdfe8a6e4 is titled "correct the new-check count to a measured 17", so this number has already been corrected once and is still wrong; a reader auditing the map's coverage from this sentence would look for twelve guarantees in the new document and find nine running and five dead.

**Proposed fix.**

In both experiments/2026-08-30-change-successor-questions/DELIVERY.md (Map delta section) and VALIDATION.md (Map section), replace "Twelve in `CON-successor-questions.md` (...) and five across the amended documents" with: "Nine in `CON-successor-questions.md` and eight across the five amended documents. The new document also carries five further `check:` lines that are INDENTED and therefore not executed by docs_verify (its parser anchors `check:` at column 0 and treats an indented one as an example, reporting neither a check nor an error) — 22 written, 17 run." If the indentation is fixed per the previous finding, restate as "fourteen in `CON-successor-questions.md` and eight across the five amended documents, 22 total" and re-run the mechanical count.

---

## F11 — The rank-tie regression's LIVENESS_QUEUE arm is vacuous: it passes with the liveness-mode seed term deleted, and its fixture docstring states a false reason

**MAJOR** · lens S2 configurability · `tests/test_successor_rank_tie.py:56`

**The claim under test.** tests/test_successor_rank_tie.py docstring: "in both of them `p.provenance.trigger != SpawnTrigger.SEED` is False for the seed and True for a successor ... So a minted successor loses every TIE to the operator's question, in both selection modes, by construction"; and the fixture comment "Spawn-order and id-order both favour the successor, as live: \"succ:...\" sorts before \"question-...\" and it is registered first." DELIVERY.md R5 proof: "tests/test_successor_rank_tie.py (3 tests, both selection modes)". CON-successor-questions.md: "a minted successor loses every rank TIE to the operator's seed question, in both selection modes, by construction."

**Commands.**

```
cd /home/user/DeepReason/.claude/worktrees/wf_9b72aacb-3ed-2
export PYTHONPATH=$PWD/src:$PWD/mini
python -c "print('question-98a0e3a77a0e' < 'succ:0e26d6be54fd')"
# MUTATION A -- delete the seed term from the LIVENESS key ONLY (line 1182):
sed -n '1182p' src/deepreason/scheduler/scheduler.py
sed -i '1182d' src/deepreason/scheduler/scheduler.py
python -m pytest tests/test_successor_rank_tie.py -q -p no:randomly 2>&1 | tail -3
git checkout -- src/deepreason/scheduler/scheduler.py
# MUTATION B -- delete it from the ROUND-ROBIN key ONLY (line 1204):
sed -i '1204d' src/deepreason/scheduler/scheduler.py
python -m pytest tests/test_successor_rank_tie.py -q -p no:randomly 2>&1 | tail -4
git checkout -- src/deepreason/scheduler/scheduler.py
```

**Observed.**

```
$ python -c "print('question-98a0e3a77a0e' < 'succ:0e26d6be54fd')"
True                      # the SEED id sorts FIRST -- the docstring says the opposite

-- MUTATION A (liveness-mode seed term deleted) --
FAILED tests/test_successor_rank_tie.py::test_the_successor_trigger_sorts_after_the_seed_in_the_rank_term
1 failed, 2 passed in 0.27s
    (test_a_minted_successor_loses_the_rank_tie_to_the_seed_question PASSED)

-- MUTATION B (round-robin seed term deleted) --
FAILED tests/test_successor_rank_tie.py::test_a_minted_successor_loses_the_rank_tie_to_the_seed_question
FAILED tests/test_successor_rank_tie.py::test_the_successor_trigger_sorts_after_the_seed_in_the_rank_term
2 failed, 1 passed in 0.22s

-- direct probe, still under MUTATION A, successor id changed to 'aaa:0e26d6be54fd' --
liveness=True: selected question-98a0e3a77a0e     # with the test's own ids: seed wins anyway
ALT liveness=True: selected aaa:0e26d6be54fd  (seed wins? False)   # seed term WAS load-bearing
ALT liveness=False: selected question-98a0e3a77a0e  (seed wins? True)
```

**Why it is a defect.** The behavioural test loops over both selection modes but only the ROUND-ROBIN arm can fail. With the seed term removed from the LIVENESS_QUEUE rank key alone, the test still passes, because the fixture's ids make the final `p.id` tie-break decide in the seed's favour: 'question-98a0e3a77a0e' < 'succ:0e26d6be54fd'. The docstring asserts the exact opposite of that measured fact ("'succ:...' sorts before 'question-...'"), which is why the vacuity was not noticed. The tranche's own transcript proof/rank_tie_red.txt mutates BOTH keys at once, which masks it — the only test that goes red for the liveness key is the source-text grep in test 2, i.e. that half of the guarantee is pinned by spelling, not by behaviour. Substituting an id that sorts before the seed ('aaa:...') shows the seed term genuinely is load-bearing in liveness mode and the fixture simply never exercises it. The shipped behaviour is correct; the guard for half of it is not.

**Proposed fix.**

In tests/test_successor_rank_tie.py: (1) replace the false fixture comment "Spawn-order and id-order both favour the successor, as live: \"succ:...\" sorts before \"question-...\" and it is registered first." with "Registration order favours the successor. Note a real 'succ:' id sorts AFTER 'question-', so the id tie-break already favours the seed and cannot prove the seed term on its own." (2) Add a second minted problem to _register under an id that sorts BEFORE the seed (e.g. "aaa:0e26d6be54fd", successor trigger) and assert in test_a_minted_successor_loses_the_rank_tie_to_the_seed_question that the seed still wins — that arm goes red under deletion of line 1182 alone. (3) Regenerate proof/rank_tie_red.txt with the two sort keys mutated SEPARATELY so each arm is shown dying on its own. If (2) is declined, instead correct DELIVERY.md R5 to "done for the TIE in round-robin mode; in LIVENESS_QUEUE mode the seed term is pinned by source-text count only" and amend the same sentence in CON-successor-questions.md's Invariants bullet.

---

## F12 — The map document's own customisation recipe raises when followed, and the minting gate's `enforcement` string names a Config attribute that does not and cannot exist

**MAJOR** · lens S2 configurability · `docs/map/CON-successor-questions.md:181`

**The claim under test.** CON-successor-questions.md, "Where to change what": "| Send questions somewhere other than the scratchpad | register a row + writer via `registry.register_destination`; select it by `SUCCESSOR_QUESTION_DESTINATION` |". registry.py docstring: "``enforcement`` names where the row is actually READ, so a declaration can never claim a switch no consumer consults -- the failure mode this repo has already paid for once, in an allocation controller whose 47 decisions reached no dispatch." DELIVERY.md R6 proof: `tests/test_successor_registry.py::test_adding_a_destination_requires_no_edit_to_any_consumer`.

**Commands.**

```
cd /home/user/DeepReason/.claude/worktrees/wf_9b72aacb-3ed-2
export PYTHONPATH=$PWD/src:$PWD/mini
python - <<'PY'
from deepreason.config import Config
from deepreason.successor import resolve
from deepreason.successor.registry import (SuccessorDeclaration, register_destination,
                                           GATES, MINTING_GATE_ID)
register_destination(SuccessorDeclaration(id="elsewhere.v1", routes="a second destination",
                     default=False, enforcement="plugin", authority="operator"),
                     lambda *a, **k: "written-elsewhere")
try:
    print("select by field ->", resolve(Config(SUCCESSOR_QUESTION_DESTINATION="elsewhere.v1")).id)
except Exception as e:
    print(type(e).__name__, "|", str(e).splitlines()[1].strip(), "|", str(e).splitlines()[2].strip())
print("gate enforcement string   :", repr(GATES[MINTING_GATE_ID].enforcement))
print("Config carries it?        :", hasattr(Config(), "SUCCESSOR_MINTING_ENABLED"))
try:
    Config(SUCCESSOR_MINTING_ENABLED=True); print("settable? yes")
except Exception as e: print("settable? no ->", type(e).__name__)
PY
python -c "import yaml,pathlib,tempfile; from deepreason import config as c; p=pathlib.Path(tempfile.mkdtemp())/'p.yaml'; p.write_text(yaml.safe_dump({'SUCCESSOR_QUESTION_DESTINATION':'elsewhere.v1'})); c.load(str(p))" 2>&1 | tail -2
sed -n '270,273p' src/deepreason/config.py
grep -rn "deepreason.successor" --include=*.py src/ | grep -v "^src/deepreason/successor/" | wc -l
```

**Observed.**

```
STEP 1 register: OK -> True
STEP 2 select it by SUCCESSOR_QUESTION_DESTINATION on the run's Config:
   ValidationError: SUCCESSOR_QUESTION_DESTINATION | Extra inputs are not permitted [type=extra_forbidden]

The gate row's own `enforcement` string:
    'deepreason.successor.mint.mint -> Config.SUCCESSOR_MINTING_ENABLED'
   does Config actually carry that attribute?  False
   can any run put it there?                   no -> ValidationError

YAML-profile road (config.load), same key:
   ValidationError: 1 validation error for Config

src/deepreason/config.py:270  class Config(BaseModel):
                        271      model_config = ConfigDict(
                        272          extra="forbid", validate_assignment=True, hide_input_in_errors=True
                        273      )

production importers of deepreason.successor: 0
```

**Why it is a defect.** The document's "Where to change what" table is the recipe a customiser follows, and it states the selection step without qualification. Following it verbatim raises pydantic ValidationError "Extra inputs are not permitted", because `Config` is `extra="forbid", validate_assignment=True` and no `SUCCESSOR_QUESTION_DESTINATION` field exists (Q1 parked); attribute assignment and the YAML-profile road fail identically. Re-aiming therefore works only when a non-`Config` object is passed, which no run does — and nothing in production imports the package at all. Separately, the `minting.v1` row's `enforcement` field literally reads `Config.SUCCESSOR_MINTING_ENABLED`, an attribute `Config` does not carry and cannot be given, which is precisely the failure the registry's own docstring says a declaration "can never claim"; nothing checks the enforcement strings, so this claim is unfalsifiable as shipped. DELIVERY.md's R6 evidence is `test_adding_a_destination_requires_no_edit_to_any_consumer`, which selects through a hand-made `_Selects` stub, so the cited measurement never touches a real configuration. The tranche does disclose the missing Config field in DELIVERY.md's residue and in the document's Invariants section — this finding is about the recipe and the enforcement string, which contradict that disclosure in the two places a customiser and a checker actually look.

**Proposed fix.**

(1) docs/map/CON-successor-questions.md, "Where to change what", row 1: append to the Edit cell " — NOTE: no `Config` field carries this selector yet (Q1 pending); a real `Config` refuses it with `extra_forbidden`, so today only a non-`Config` configuration object can select a row." (2) src/deepreason/successor/registry.py, the `minting.v1` row: change `enforcement=f"deepreason.successor.mint.mint -> Config.{SUCCESSOR_MINTING_FIELD}"` to `enforcement=f"deepreason.successor.mint.mint -> getattr(config, {SUCCESSOR_MINTING_FIELD!r}, False); no Config field exists until the Q1 frozen-surface-4 grant"`. (3) experiments/2026-08-30-change-successor-questions/DELIVERY.md, R6 row, Proof cell: append " — measured against a stub configuration object, NOT `deepreason.config.Config`, which refuses the selector with `extra_forbidden`."

---

## F14 — The diff-budget headline does not re-derive: 2486 claimed, 3222 measured by the tranche's own prescribed command

**MAJOR** · lens S3 scope+numbers · `experiments/2026-08-30-change-successor-questions/DELIVERY.md:114`

**The claim under test.** DELIVERY.md:114 "**The diff budget verdict is EXCEEDED** — 2486 insertions against SPEC.md's ceiling of 1169" and VALIDATION.md:243 "The diff-budget gate returns EXCEEDED (2486 vs 1169)". DELIVERY.md:119 adds "It lands in the tests (1140 insertions against an itemised ~490) and in the new map document (183 against 98)".

**Commands.**

```
cd /home/user/DeepReason/.claude/worktrees/wf_9b72aacb-3ed-3
mkdir -p /tmp/laneB && git archive fdfe8a6e4 | tar -x -C /tmp/laneB
# SPEC.md:1375 prescribes exactly this gate invocation, with these --paths:
python /tmp/laneB/tools/diff_budget.py 3688713ee --against fdfe8a6e4 --ceiling 1169 \
  --paths src/deepreason tests docs/map experiments/2026-08-30-change-successor-questions
# and for the two sub-numbers:
git diff --numstat 3688713ee fdfe8a6e4 -- docs/map tests
```

**Observed.**

```
{"result_type": "DIFF_BUDGET_RESULT_V1", "base": "3688713ee", "against": "fdfe8a6e4", "areas": {"src/deepreason": 556, "tests": 1160, "docs/map": 337, "experiments/2026-08-30-change-successor-questions": 1169}, "total_insertions": 3222, "ceiling": 1169, "verdict": "EXCEEDED"}

(numstat) 196\t0\tdocs/map/CON-successor-questions.md
(numstat tests) 291+224+300+112+233 = 1160
```

**Why it is a defect.** 2486 is not reproducible by any invocation I could construct. The gate returns 3222 at the delivered head fdfe8a6e4 and 3216 at b690b814b (the commit DELIVERY.md names). The sub-numbers 1140 and 183 are the values at the FIRST implementation commit 6ce1f202f only ({"tests": 1140, "docs/map": 318}, and 183 insertions for CON-successor-questions.md); both grew before delivery, to 1160 and 196. The error runs entirely in the self-serving direction: it understates the overrun by 736 lines, about 30%. SPEC.md:1377 makes EXCEEDED "a STOP and a re-plan", so the size of the overrun is the number a reviewer prices that stop against.

**Proposed fix.**

In experiments/2026-08-30-change-successor-questions/DELIVERY.md line 114, replace "2486 insertions against SPEC.md's ceiling of 1169" with "3222 insertions against SPEC.md's ceiling of 1169, re-measured at the delivered head with SPEC.md's own command (python tools/diff_budget.py 3688713ee --against HEAD --ceiling 1169 --paths src/deepreason tests docs/map experiments/2026-08-30-change-successor-questions)". In line 119, replace "the tests (1140 insertions against an itemised ~490)" with "the tests (1160 insertions against an itemised ~490)", and "the new map document (183 against 98)" with "the new map document (196 against 98)". In VALIDATION.md line 244, replace "(2486 vs 1169)" with "(3222 vs 1169)".

---

## F15 — The two new signal declarations are unguarded: deleting both leaves every test and every map check in the tranche green

**MAJOR** · lens S3 scope+numbers · `docs/map/CON-successor-questions.md:122`

**The claim under test.** docs/map/CON-successor-questions.md:122 "DR-INV-signal-contract — the registry sits in its VERSIONED layer, and its receipts are declared signals with a real unit and a real staleness." and VALIDATION.md:204 "two typed Measure families (successor-question: with three dispositions, and successor-problem-minted), both DECLARED in signals.py with a real unit and staleness under DR-REC-add-signal".

**Commands.**

```
cd /tmp/laneB && export PYTHONPATH=$PWD/src:$PWD/mini
# delete BOTH new declarations from src/deepreason/signals.py (the
# successor-question: entry from _DECLARED_PREFIXES and the
# successor-problem-minted entry from _DECLARED), then:
python -m pytest tests/test_signal_contract.py tests/test_signals.py \
  tests/test_successor_questions.py tests/test_successor_minting.py \
  tests/test_successor_law_line.py tests/test_successor_registry.py \
  tests/test_successor_rank_tie.py -q -p no:randomly
# plus every check in the tranche's own map document and in the invariant it cites
# (sigcheck.py loads tools/docs_verify.py and runs one document's checks):
python sigcheck.py CON-successor-questions.md
python sigcheck.py INV-signal-contract.md
```

**Observed.**

```
--- the tranche ring under the mutant
.............................................................            [100%]
61 passed in 6.08s
--- CON-successor-questions checks under the mutant
CON-successor-questions.md:49 exit=0
CON-successor-questions.md:55 exit=0
CON-successor-questions.md:72 exit=0
CON-successor-questions.md:80 exit=0
CON-successor-questions.md:97 exit=0
CON-successor-questions.md:113 exit=0
CON-successor-questions.md:119 exit=0
CON-successor-questions.md:133 exit=0
CON-successor-questions.md:188 exit=0
(INV-signal-contract.md: 22 of 23 checks exit=0; the only exit=1 is :243
 "AssertionError: LINEAGE_POLICIES", which VALIDATION.md Appendix C already
 lists as a pre-existing baseline failure)
```

**Why it is a defect.** The lane added two receipt emitters (route.py's RECEIPT_PREFIX and mint.py's MINT_RECEIPT) plus two matching declarations, and its map document asserts as an INVARIANT that those receipts are declared with a real unit and staleness. Nothing goes red when the declarations are deleted, so under the operator's modularity law ("'enforced' means a check that can fail") and docs/map/SCHEMA.md ("New behaviour needs a new check that would fail if the behaviour regressed") the claim at CON-successor-questions.md:122 ships with no failable check. The nearest check, at line 133, only asserts the shipped Config defaults and says nothing about signals. The document's own 'Where to change what' row at line 142 also points a future editor at tests/test_signal_contract.py as the test for these receipts, and that file passes with both declarations removed. The guard is partial rather than absent: emptying a declaration's unit or staleness while keeping the declaration DOES turn test_signal_contract.py red (2 failed, 17 passed, both times). It is the EXISTENCE of the two declarations that nothing pins.

**Proposed fix.**

In docs/map/CON-successor-questions.md, immediately after the Invariants bullet at line 124, add a column-0 check. I ran this exact assertion: it prints "PROPOSED CHECK OK" and exits 0 on the shipped tree, and exits 1 with "AssertionError: successor-question:ROUTED" once the declarations are deleted —

`check: python -c "from deepreason.signals import declaration; from deepreason.successor.route import RECEIPT_PREFIX; from deepreason.successor.mint import MINT_RECEIPT;\nfor n in (RECEIPT_PREFIX + 'ROUTED', MINT_RECEIPT):\n    d = declaration(n)\n    assert d is not None and d.unit and d.staleness, n"`

Advance that document's Verified-at: only after re-running its checks.

---

## F16 — R3 is marked plain "done", but with the shipped Config no run can select a registered alternative destination — movement elsewhere needs a code edit today

**MAJOR** · lens S3 scope+numbers · `experiments/2026-08-30-change-successor-questions/DELIVERY.md:42`

**The claim under test.** DELIVERY.md:42 reconciliation row: "| R3 | \"must function like a plugin that allows for movement elsewhere as well\" | done | tests/test_successor_registry.py (10 tests); adding a row needs no consumer edit ... |" — the only row in the table marked done with no assumption attached.

**Commands.**

```
cd /tmp/laneB && export PYTHONPATH=$PWD/src:$PWD/mini
python -c "
from deepreason.config import Config
try:
    c = Config(SUCCESSOR_QUESTION_DESTINATION='nope')
    print('accepted:', c.SUCCESSOR_QUESTION_DESTINATION)
except Exception as e:
    print('REFUSED:', type(e).__name__, str(e)[:200])
"
python -c "
from deepreason.config import Config
c = Config()
print('has SUCCESSOR_QUESTION_DESTINATION:', hasattr(c,'SUCCESSOR_QUESTION_DESTINATION'))
print('has SUCCESSOR_MINTING_ENABLED:', hasattr(c,'SUCCESSOR_MINTING_ENABLED'))
"
```

**Observed.**

```
REFUSED: ValidationError 1 validation error for Config
SUCCESSOR_QUESTION_DESTINATION
  Extra inputs are not permitted [type=extra_forbidden]
    For further information visit https://errors.pydantic.dev/2.13/v/extra_forbidde

has SUCCESSOR_QUESTION_DESTINATION: False
has SUCCESSOR_MINTING_ENABLED: False
```

**Why it is a defect.** The registry test carrying R3 (test_adding_a_destination_requires_no_edit_to_any_consumer) proves the claim only against a hand-rolled _Selects stub class defined inside the test file. With the real deepreason.config.Config, which forbids extra fields, the selector cannot be set at all, so today the only way to route elsewhere is to add a Config field — a code edit, which is exactly what the modularity law forbids and what the operator's own P9 words ("the option to switch it on with a flag") ask for. The tranche knows this and says so under R6 ("the selector FIELD is blocked on Q1"), A5, PARKED.md and the residue, which is why this is a claim-consistency defect rather than a concealment: R3 alone is stated at full strength while the identical limitation downgrades R4 and R6 to done-with-assumption. The shipped DEFAULT road is genuinely correct against a real Config — resolve(Config()).id == 'scratchpad.v1' and minting_enabled(Config()) is False both hold (map check line 133, re-run, exit 0) — so SPEC.md's frozen-surface-4 grant really was not needed for what shipped.

**Proposed fix.**

In experiments/2026-08-30-change-successor-questions/DELIVERY.md line 42, change the R3 disposition cell from "done" to "done-with-assumption A5" and extend the proof cell with: "— the plugin point is real (a row registers and routes with no consumer edit), but deepreason.config.Config forbids extra fields (extra_forbidden), so no run can SELECT a registered alternative until Q1's field lands; the test proves the claim against a _Selects stub, not against Config."

---

## F17 — "all five tests in test_h1_no_spawn_from_refutation.py" — the file has four; and the parked S19/S20 accept criteria are unsatisfiable as written

**MAJOR** · lens S3 scope+numbers · `experiments/2026-08-30-change-successor-questions/VALIDATION.md:121`

**The claim under test.** VALIDATION.md:121 "Everything else in that file and all five tests in tests/test_h1_no_spawn_from_refutation.py are expected GREEN."; PARKED.md:152 "The four protected-channel tests and all five H1 tests are byte-unchanged and green."; SPEC.md:321 "accept: python -m pytest tests/test_h1_no_spawn_from_refutation.py -q -> 5 passed"; SPEC.md:310 "accept: python -m pytest tests/test_decommissioned_pipeline_stays_out.py -q -> 5 passed".

**Commands.**

```
cd /tmp/laneB && export PYTHONPATH=$PWD/src:$PWD/mini
python -m pytest tests/test_h1_no_spawn_from_refutation.py -q --collect-only | tail -2
python -m pytest tests/test_h1_no_spawn_from_refutation.py -q -p no:randomly | tail -2
python -m pytest tests/test_decommissioned_pipeline_stays_out.py -q --collect-only | tail -2
# then apply PARKED.md P9B-7's four-line rewrite verbatim and re-run:
python -m pytest tests/test_decommissioned_pipeline_stays_out.py -q -p no:randomly | tail -2
```

**Observed.**

```
4 tests collected in 0.07s
....                                                                     [100%]
4 passed in 0.19s

6 tests collected in 0.04s

(with the P9B-7 rewrite applied)
......                                                                   [100%]
6 passed in 0.12s
```

**Why it is a defect.** VALIDATION.md's "Full gate" section is the document the batch fan-in reads to decide what is predicted versus surprising, and it names a test count that does not exist. More consequentially, the same wrong count is baked into the parked acceptance criteria: S19's accept demands `5 passed` from a 6-test file, and S20's demands `5 passed` from a 4-test file. A future tranche that applies P9B-7's rewrite correctly — which I verified does work; see the checks_run entry where it passes on the shipped tree and goes red under a second producer elsewhere, a second producer inside mint.py, and a producer that MOVES — would still read its own accept as unmet. The aggregate figures the lane leans on are right: baseline `10 passed` and after `1 failed, 9 passed` both re-measure exactly.

**Proposed fix.**

In VALIDATION.md line 121 replace "all five tests in" with "all four tests in". In PARKED.md line 152 replace "all five H1 tests" with "all four H1 tests". In SPEC.md line 310 change S19's accept expectation from `5 passed` to `6 passed`, and in line 321 change S20's from `5 passed` to `4 passed`.

---

## F23 — The criteria-inheritance assertion in test_the_minted_problem_carries_the_trigger_and_names_both_parents cannot fail — mint() may return an empty criteria list and the test still passes

**MAJOR** · lens S4 mutation-proof · `tests/test_successor_minting.py:149`

**The claim under test.** tests/test_successor_minting.py:146-149 — "# Criteria are inherited AT REGISTRATION because `Problem` is immutable: a\n    # successor registered without them could be addressed before anything\n    # could refuse it.\n    assert list(minted.criteria) == list(parent.criteria)". Same guarantee restated in src/deepreason/successor/mint.py:83-85 ("Inherited rather than invented ... a successor registered without them could be addressed before anything could refuse it") and counted by DELIVERY.md's R4 row: "the road, the gate and the warning are built and proven | `tests/test_successor_minting.py` (12 tests)".

**Commands.**

```
# from a checkout of claude/lane-b-stack-window-9teltn @ d296ca2bd
export PYTHONPATH=$PWD/src:$PWD/mini
sed -i 's/            criteria=list(parent.criteria) if parent is not None else \[\],/            criteria=[],/' src/deepreason/successor/mint.py
python -m pytest "tests/test_successor_minting.py::test_the_minted_problem_carries_the_trigger_and_names_both_parents" -q -p no:randomly
python -m pytest tests/test_successor_minting.py -q -p no:randomly
git checkout -- src/deepreason/successor/mint.py
```

**Observed.**

```
===== E1: criteria inheritance mutation =====
85:            criteria=[],
.                                                                        [100%]
1 passed in 0.06s
--- and the whole file: ---
............                                                             [100%]
12 passed in 0.13s

(and, from a direct probe of the fixture:)
the test's own _seed() parent.criteria = []
minted.criteria                       = []
equal? True
POPPER_BATTERY                        = []
```

**Why it is a defect.** The test's `_seed()` registers the parent problem with NO criteria, and POPPER_BATTERY is empty in this build, so `parent.criteria` is `[]`. The assertion therefore evaluates `[] == []` and holds for ANY implementation of mint — including `criteria=[]`, which is precisely the behaviour the comment two lines above calls dangerous ("a successor registered without them could be addressed before anything could refuse it"). Production behaviour is in fact correct — a separate probe with a parent carrying `criteria=['k-own']` shows the minted problem inheriting it — but nothing in the 42 tests would notice if that stopped being true. This is the same shape as the two vacuous regression tests this program has already shipped: the test passes on a tree where the guarantee is absent.

**Proposed fix.**

In tests/test_successor_minting.py, give the seed problem a real criterion so the comparison is non-trivial. Add `Commitment` to the ontology import on line 34, and change `_seed` (lines 55-64) to register one commitment and pass it:

    from deepreason.ontology import Commitment, Problem, ProblemProvenance

    def _seed(harness) -> Problem:
        harness.register_commitment(
            Commitment(id="k-tide", eval="predicate:'tide' in content")
        )
        return harness.register_problem(
            Problem(
                id=PROBLEM_ID,
                description="explain the tide table for this harbour",
                criteria=["k-tide"],
                provenance=ProblemProvenance.model_validate(
                    {"trigger": "seed", "from": []}
                ),
            )
        )

VALIDATED: with this edit and no source mutation, `python -m pytest tests/test_successor_minting.py -q` gives `12 passed in 0.16s`; with this edit plus `criteria=[]` in mint.py it gives `1 failed` on exactly test_the_minted_problem_carries_the_trigger_and_names_both_parents.

---

## F24 — The modularity guard misses the natural spelling of the anti-pattern it names: a route() that branches on `== DEFAULT_DESTINATION_ID` passes all 42 tests

**MAJOR** · lens S4 mutation-proof · `tests/test_successor_registry.py:219`

**The claim under test.** tests/test_successor_registry.py:197-204 — "The producer-agnostic rule, as an ABSENCE over the whole tree. A consumer that asks \"is this the scratchpad row?\" has stopped consuming the interface and started knowing the subsystem, and the next destination would have to teach it about itself." and :123-130 — "THE modularity claim, made failable. ... if `route` ever grew a branch on which row it got, this would be the test that could not be written." DELIVERY.md R3: "adding a row needs no consumer edit, mutation-proved in `proof/registry_modularity_red.txt`".

**Commands.**

```
export PYTHONPATH=$PWD/src:$PWD/mini
python - <<'PY'
import pathlib
p = pathlib.Path("src/deepreason/successor/route.py"); t = p.read_text()
p.write_text(t.replace("    writer = writer_for(destination.id)",
  "    if destination.id == DEFAULT_DESTINATION_ID:\n        writer = _write_scratch_block\n    else:\n        writer = writer_for(destination.id)"))
PY
python -m pytest tests/test_successor_registry.py tests/test_successor_law_line.py tests/test_successor_questions.py tests/test_successor_minting.py tests/test_successor_rank_tie.py -q -p no:randomly
git checkout -- src/deepreason/successor/route.py
```

**Observed.**

```
===== E2: modularity guard vs '== DEFAULT_DESTINATION_ID' =====
    if destination.id == DEFAULT_DESTINATION_ID:
        writer = _write_scratch_block
    else:
        writer = writer_for(destination.id)
    if writer is None:
        harness.record_measure(
            inputs=[f"{RECEIPT_PREFIX}UNAVAILABLE", destination.id, problem_id]
        )
..........................................                               [100%]
42 passed in 2.11s

(the same mutation written with a split literal, `"scratch" + "pad.v1"`, is likewise 42 passed)
```

**Why it is a defect.** `test_no_module_compares_against_a_registered_row_id` only flags `ast.Constant` operands, and `test_a_row_id_literal_appears_in_the_registry_and_nowhere_else` only greps for the literal string — so a consumer that compares against the registry's own exported constant `DEFAULT_DESTINATION_ID` (already imported by route.py at line 24) evades both. `test_adding_a_destination_requires_no_edit_to_any_consumer` also stays green because the mutated `else` branch still serves the throw-away row. The result is that route() can do the exact thing all three tests exist to forbid — branch on which row it got, so that a second destination would need a consumer edit — with nothing red. The shipped code does not do this; the enforcement claim ("made failable", "enforced means a check that can fail", operator modularity law 2026-08-26) is what does not hold.

**Proposed fix.**

In tests/test_successor_registry.py, extend the AST walk in `test_no_module_compares_against_a_registered_row_id` (lines 217-220) to treat the registry's exported id constants as offenders outside their owning module:

            for operand in operands:
                if isinstance(operand, ast.Constant) and operand.value in ids:
                    offenders.append((str(path), node.lineno, operand.value))
                if (
                    isinstance(operand, ast.Name)
                    and operand.id in {"DEFAULT_DESTINATION_ID", "MINTING_GATE_ID"}
                    and path.name != "registry.py"
                ):
                    offenders.append((str(path), node.lineno, operand.id))

VALIDATED: with this edit and no source mutation the test is `1 passed in 1.72s`; with this edit plus the `== DEFAULT_DESTINATION_ID` branch in route.py it is `1 failed`. (registry.py must be exempted because its own `unregister_destination` legitimately compares `destination_id == DEFAULT_DESTINATION_ID` at line 136.)

---

## F25 — The wire-to-contract carry of successor_question is completely unguarded: dropping it at both conversion sites leaves 97 tests green

**MAJOR** · lens S4 mutation-proof · `src/deepreason/llm/wire.py:2600`

**The claim under test.** DELIVERY.md: "A criticism can now propose the question it thinks should be asked NEXT, in one optional field on both criticism output contracts"; VALIDATION.md S2a cites `tests/test_wire_contracts.py tests/test_crit_batch.py tests/test_v6_patch_repair_and_wire.py ... -> 56 passed` as the evidence that the wire layer is sound, and R1 is marked "done" against `tests/test_successor_law_line.py` (which only inspects the contract models' field defaults, never the wire conversion).

**Commands.**

```
export PYTHONPATH=$PWD/src:$PWD/mini
sed -i 's/                    successor_question=item.successor_question,/                    successor_question=None,/' src/deepreason/llm/wire.py
sed -i 's/            successor_question=wire.successor_question,/            successor_question=None,/' src/deepreason/llm/wire.py
python -m pytest tests/test_successor_law_line.py tests/test_successor_minting.py tests/test_successor_questions.py tests/test_successor_rank_tie.py tests/test_successor_registry.py tests/test_wire_contracts.py tests/test_crit_batch.py tests/test_v6_patch_repair_and_wire.py -q -p no:randomly
git checkout -- src/deepreason/llm/wire.py
```

**Observed.**

```
########## M51 wire.py drops successor_question in BOTH conversions ##########
SUMMARY: 97 passed in 3.29s
  >>> NO TEST FAILED
  reverted: src/deepreason/llm/wire.py=d5297c5b
```

**Why it is a defect.** src/deepreason/llm/wire.py:2600 and :2668 are the only two places where a model's filled successor_question crosses from the wire object into the contract object that anything downstream can read. Both can be replaced with `None` and neither the 42 new tests nor any of the three wire test files VALIDATION.md cites goes red. The tranche's only wire-side pin is the map check at docs/map/CON-successor-questions.md:168, which asserts the FIELD EXISTS on a wire critic model — not that its value is carried. The practical consequence is precise: when Q3 is answered and a dispatch site is added (`route(..., question=case.successor_question)`), a silently-dropped carry would make the whole channel a no-op with every test still green — which is the same failure class as the vacuous regression tests this audit exists to catch.

**Proposed fix.**

Add one test to tests/test_successor_questions.py (or a new tests/test_successor_wire.py) that round-trips a filled field through both conversions, e.g.:

    def test_the_wire_carries_a_filled_successor_question_to_the_contract():
        from deepreason.llm import wire as w
        # batch path (wire.py:2600)
        batch = <the BatchCriticWire model> with one case carrying
                successor_question="what next?"
        assert batch.to_contract(...).cases[0].successor_question == "what next?"
        # atomic path (wire.py:2668)
        assert <atomic wire>.to_contract(...).successor_question == "what next?"

If that is judged out of this lane's cone, the honest alternative is to DOWNGRADE the claim: add to DELIVERY.md's residue list a sixth entry reading "**The wire carry is unguarded.** `llm/wire.py:2600` and `:2668` pass `successor_question` from wire to contract and no test fails if either is replaced with `None` (measured: 97 passed). The field's existence is pinned by CON-successor-questions.md:168; its VALUE is not pinned anywhere."

---

## F30 — Five of the fourteen `check:` spans in the new map document are indented, so tools/docs_verify.py never parses them, never runs them, and never reports them

**MAJOR** · lens S5 map checks · `docs/map/CON-successor-questions.md:154`

**The claim under test.** docs/map/CON-successor-questions.md presents fourteen `check:` spans, six of them in Traps, e.g. line 175: "**Routing into a run whose workshop is OFF must DISCLOSE, not discard.** ... `check: python -m pytest tests/test_successor_questions.py::test_a_scratch_disabled_run_discloses_instead_of_discarding -q`". VALIDATION.md counts "Twelve in `CON-successor-questions.md` (... and four Traps checks)". docs/map/SCHEMA.md: "A check must start at **column 0**"; experiments/2026-08-29-ultracode-batch-2/recon/RECON-B.md:345 told this lane "The contract for writing any map change: checks at column 0, must be able to fail, Verified-at only advanced if re-run."

**Commands.**

```
# from a checkout of claude/lane-b-stack-window-9teltn @ d296ca2bd
export PYTHONPATH=$PWD/src:$PWD/mini
grep -c '`check:'  docs/map/CON-successor-questions.md      # spans written
grep -c '^`check:' docs/map/CON-successor-questions.md      # spans at column 0
grep -n '^[[:space:]][[:space:]]*`check:' docs/map/CON-successor-questions.md
python -c "import sys; sys.path.insert(0,'tools'); import docs_verify as dv; from pathlib import Path; d=dv.parse(Path('docs/map/CON-successor-questions.md')); print('parsed',len(d.checks),'errors',len(d.errors))"
# are the two claims covered by any other map check?
grep -rn 'test_a_scratch_disabled_run_discloses_instead_of_discarding' docs/
grep -rn 'author_block' docs/map/CON-successor-questions.md docs/map/SUB-scratch.md
```

**Observed.**

```
written  (any indent) : 14
at column 0 (parsed)  : 9
indented, therefore invisible to tools/docs_verify.py:
154:  `check: test "$(grep -rn "ProblemProvenance.model_validate" --include=*.py src/deepreason
160:  `check: python -c "from deepreason.llm.contracts import ArgumentativeCriticOutput as O; a
168:  `check: python -c "import inspect;from pydantic import BaseModel;from deepreason.llm impo
175:  `check: python -m pytest tests/test_successor_questions.py::test_a_scratch_disabled_run_d
196:  `check: grep -q 'block_role: Literal\["conjecturer", "synthesizer"\]' src/deepreason/run_

parsed 9 errors 0

(and, map-wide) docs/map/CON-proof-debt-and-localization.md:2
docs/map/CON-successor-questions.md:5
docs/map/SCHEMA.md:3

(coverage elsewhere) docs/map/CON-successor-questions.md:175:  `check: python -m pytest ...test_a_scratch_disabled_run_discloses_instead_of_discarding -q`   <- the ONLY occurrence in docs/
```

**Why it is a defect.** docs_verify's grammar treats a `check:` span that is not at column 0 as a worked EXAMPLE: it produces neither a check nor an error (tools/docs_verify.py cmd_self_test asserts exactly this — "An indented check is an EXAMPLE, not a claim: no check AND no error"). So five claims in the tranche's flagship new document carry a check that a reader sees and the instrument never executes — the same silence class the repo fixed one day earlier in experiments/2026-08-29-fix-docs-verify-multiline-checks/, re-introduced five times in one document (more than the rest of the map combined, excluding SCHEMA.md's deliberate examples). Two of the five — line 175 (a scratch-disabled run must disclose, not discard) and line 196 (`author_block` is the wrong door) — are covered by no other check anywhere in docs/map/, so those claims are enforced by docs_verify by nothing at all. It also makes VALIDATION.md's "four Traps checks" and "Twelve in CON-successor-questions.md" arithmetic wrong (see the separate finding). I ran all five by hand and all five currently pass, so nothing in the document is presently false — what is missing is the authentication the document claims to have.

**Proposed fix.**

In docs/map/CON-successor-questions.md, remove the two-space indent from the `check:` line of each of the five Traps entries (lines 154, 160, 168, 175, 196) so each span starts at column 0, exactly as the sixth Traps check at line 188 already does. No other text changes. Re-run `python tools/docs_verify.py --ring successor` and `python -c "import sys;sys.path.insert(0,'tools');import docs_verify as dv;from pathlib import Path;print(len(dv.parse(Path('docs/map/CON-successor-questions.md')).checks))"` and confirm it prints 14. Then correct VALIDATION.md and DELIVERY.md's new-check counts to the re-measured values.

---

## F31 — `Verified-at: 3688713ee` on all seven touched map documents is a FALSE stamp: at that commit the package, the tests and the document itself do not exist

**MAJOR** · lens S5 map checks · `docs/map/CON-successor-questions.md:2`

**The claim under test.** All seven touched documents carry `Verified-at: 3688713ee`. VALIDATION.md: "`Verified-at:` was advanced to `3688713ee` on all seven touched documents (...) because their checks were actually re-run — the run pasted above executes every check in every document, and none of the seven appears in its failure list. The stamp names the commit the tree was based on, which is the convention every other document in `docs/map/` follows." DELIVERY.md: "left stale: none — `Verified-at:` was advanced on all six to the commit their checks were re-run against". docs/map/SCHEMA.md: "2. **Update `Verified-at:`** to the commit you are making. If you did not check the document's claims, do not advance the stamp — a stale stamp is honest, a false one is not."

**Commands.**

```
export PYTHONPATH=$PWD/src:$PWD/mini
git log --oneline -1 3688713ee
git ls-tree -r --name-only 3688713ee -- src/deepreason/successor tests/test_successor_law_line.py docs/map/CON-successor-questions.md
# run the new document's own Verify: line against the tree it is stamped at
mkdir -p /tmp/stamp && git archive 3688713ee | tar -x -C /tmp/stamp
cd /tmp/stamp && PYTHONPATH=/tmp/stamp/src:/tmp/stamp/mini python -m pytest \
  tests/test_successor_law_line.py tests/test_successor_registry.py \
  tests/test_successor_questions.py tests/test_successor_minting.py \
  tests/test_successor_rank_tie.py -q; echo "exit=$?"
# the claimed convention, measured over every stamp resolvable in this checkout
# (for each doc: does its stamped commit contain that document?)
git show 6ce1f202f:docs/map/CON-criticism-source.md | head -2   # stamp before b690b814b
```

**Observed.**

```
3688713ee lane B: REQUEST.md and SPEC.md for successor questions (operator P9 law, 2026-08-29)

$ git ls-tree -r --name-only 3688713ee -- src/deepreason/successor tests/test_successor_law_line.py docs/map/CON-successor-questions.md
(no output — none of the three exist at that commit)

$ (the document's own Verify: line, run at its stamped commit)
exit code: 4
no tests ran in 0.00s
ERROR: file or directory not found: tests/test_successor_law_line.py

$ (the claimed convention, over the 24 stamps resolvable in this shallow checkout)
  stamp commit CONTAINS the document : 21
  stamp commit does NOT contain it   : 3
  (the 3: CON-successor-questions.md, INV-render-layout.md, SEAM-llm-x-scheduler.md)

$ git show 6ce1f202f:docs/map/CON-criticism-source.md | head -2
<!-- DR-CON-criticism-source -->
Verified-at: 499886a3e
```

**Why it is a defect.** The stamp asserts the commit the document's claims were last checked against. At 3688713ee the successor package, all five test files and the document itself are absent, so the checks provably could not have run there — the document's own `Verify:` line exits 4 with "file or directory not found". SCHEMA.md's rule is "the commit you are making" and RECON-B.md:458 restated it ("advanced ONLY if its checks were actually re-run"); the stamp names a commit two commits BEFORE the code. The stated justification is also not the map's practice: of the 24 stamps resolvable in this checkout, 21 name a commit that contains their own document, and CON-successor-questions is one of only three that do not. Worse, commit b690b814b actively rewrote six previously honest stamps (499886a3e, 6c65f95e8, 5f7e413d6, f9fcd1136, 08dcdf3c) to this one, so the tranche moved six stamps from honest-stale to false. Concrete downstream cost: `docs_verify --stale` computes `git log <stamp>..HEAD -- <Owns files>`, so CON-successor-questions.md is reported stale on arrival, naming the very commits that created the files it owns (`git log --oneline 3688713ee..d296ca2bd -- src/deepreason/successor/*.py` returns b690b814b and 6ce1f202f).

**Proposed fix.**

Set `Verified-at:` on all seven documents to the commit the map change is actually being made in — the final lane-B commit whose tree the checks were run against (b690b814b for the shipped branch, or whatever commit carries the repair). Replace VALIDATION.md's sentence "The stamp names the commit the tree was based on, which is the convention every other document in `docs/map/` follows." with "The stamp names the commit this change is made in, per SCHEMA.md's rule 2." If the lane prefers not to restamp, the honest alternative is to restore the six pre-existing documents' original stamps (499886a3e, 6c65f95e8, 5f7e413d6, f9fcd1136, 08dcdf3c) and drop DELIVERY.md's "left stale: none" claim.

---

## F32 — Two documents pin "nothing that decides names this channel" with a check whose whole body is `assert PERMITTED == ()` — it stays green when scheduler.py and rules/crit.py import the channel

**MAJOR** · lens S5 map checks · `docs/map/CON-successor-questions.md:80`

**The claim under test.** docs/map/CON-successor-questions.md:76-80: "The four packages that DECIDE anything — `scheduler`, `adjudication`, `informal`, `rules` — name no part of this machinery, and the permitted-exception list is EMPTY. ... `check: python -m pytest tests/test_successor_law_line.py::test_the_channel_has_no_permitted_exception_inside_a_deciding_package -q`". docs/map/SEAM-rules-x-scratch.md:228-230: "Until it is answered, nothing under `rules/` names the channel, and that emptiness is itself checked." followed by a check whose only successor-related node id is the same test.

**Commands.**

```
export PYTHONPATH=$PWD/src:$PWD/mini
# baseline
python -m pytest tests/test_successor_law_line.py::test_the_channel_has_no_permitted_exception_inside_a_deciding_package -q
# mutate the SUBJECT the sentence names
printf '\nfrom deepreason.successor import route as _successor_route  # noqa: E402\n' >> src/deepreason/scheduler/scheduler.py
python -m pytest tests/test_successor_law_line.py::test_the_channel_has_no_permitted_exception_inside_a_deciding_package -q; echo "cited check rc=$?"
python -m pytest tests/test_successor_law_line.py::test_nothing_that_labels_ranks_or_admits_reads_a_successor_question -q; echo "absence check rc=$?"
git checkout -- src/deepreason/scheduler/scheduler.py
# and inside rules/, which the SEAM sentence names explicitly
printf '\nfrom deepreason.successor import route as _successor_route  # noqa: E402\n' >> src/deepreason/rules/crit.py
python -m pytest tests/test_successor_law_line.py::test_the_channel_has_no_permitted_exception_inside_a_deciding_package tests/test_prose_refutation_boundaries.py -q && test "$(grep -c scratch src/deepreason/rules/crit.py)" -eq 2; echo "SEAM check rc=$?"
git checkout -- src/deepreason/rules/crit.py
sed -n '117,131p' tests/test_successor_law_line.py
```

**Observed.**

```
[N04a-cited-check-vs-scheduler-import] baseline rc=0 mutated rc=0 restored rc=0 restore_ok=True -> *** CANNOT FAIL ***
[N04b-absence-check-vs-scheduler-import] baseline rc=0 mutated rc=1 restored rc=0 restore_ok=True -> CAN FAIL
      | FAILED tests/test_successor_law_line.py::test_nothing_that_labels_ranks_or_admits_reads_a_successor_question
[N04c-cited-check-vs-rules-import] baseline rc=0 mutated rc=0 restored rc=0 restore_ok=True -> *** CANNOT FAIL ***
[N16-seam-check-vs-rules-import] baseline rc=0 mutated rc=0 restored rc=0 restore_ok=True -> *** CANNOT FAIL ***

(the cited test's entire body, tests/test_successor_law_line.py)
def test_the_channel_has_no_permitted_exception_inside_a_deciding_package():
    ...
    assert PERMITTED == ()
```

**Why it is a defect.** The cited test asserts one module-level constant declared six lines above it in the same test file (`PERMITTED: tuple[pathlib.Path, ...] = ()`). No change to src/ can turn it red — I imported `deepreason.successor` into `scheduler.py` and into `rules/crit.py`, the two packages both sentences name, and both checks stayed green. The sentence has two conjuncts and the check pins only the weaker one: "the permitted-exception list is EMPTY" is checked, "the four packages name no part of this machinery" / "nothing under `rules/` names the channel" is not. The test that DOES pin it, `test_nothing_that_labels_ranks_or_admits_reads_a_successor_question`, goes red on the same mutation and is already cited at column 0 in CON-criticism-source.md — so the property is enforced somewhere in the map, but not by either check that claims to enforce it. This is the exact failure class SCHEMA.md's check-writing rule 2 was written for ("Never bind a guard by its message string alone... call the code and demand the typed refusal").

**Proposed fix.**

Add the absence test to both check commands. docs/map/CON-successor-questions.md line 80 becomes: ``check: python -m pytest tests/test_successor_law_line.py::test_nothing_that_labels_ranks_or_admits_reads_a_successor_question tests/test_successor_law_line.py::test_the_channel_has_no_permitted_exception_inside_a_deciding_package -q``. docs/map/SEAM-rules-x-scratch.md line 230 becomes: ``check: python -m pytest tests/test_successor_law_line.py::test_nothing_that_labels_ranks_or_admits_reads_a_successor_question tests/test_successor_law_line.py::test_the_channel_has_no_permitted_exception_inside_a_deciding_package tests/test_prose_refutation_boundaries.py -q && test "$(grep -c scratch src/deepreason/rules/crit.py)" -eq 2``.

---

## F33 — The wire-mirror positive anchor is satisfied by a CONTRACTS class leaking into wire's namespace — renaming `successor_question` on BOTH wire models leaves the check green, and leaves all 42 tests green too

**MAJOR** · lens S5 map checks · `docs/map/SEAM-rules-x-scratch.md:262`

**The claim under test.** docs/map/CON-successor-questions.md:162-168: "`DR-SEAM-rules-x-scratch` enumerates Critic-named wire models DYNAMICALLY and forbids any field whose name contains it, so the mirror field is `successor_question` on both `CompactCritic` and `BatchCriticCaseWireV2` rather than anything naming its destination", with `... assert any('successor_question' in c.model_fields for c in M)`. The same clause is the parsed check at docs/map/SEAM-rules-x-scratch.md:262.

**Commands.**

```
export PYTHONPATH=$PWD/src:$PWD/mini
CHK='python -c "import inspect;from pydantic import BaseModel;from deepreason.llm import wire;K=[getattr(wire,n) for n in dir(wire) if '"'"'Critic'"'"' in n and inspect.isclass(getattr(wire,n))];M=[c for c in K if issubclass(c,BaseModel)];assert M;assert not [(c.__name__,f) for c in M for f in c.model_fields if '"'"'scratch'"'"' in f];assert any('"'"'successor_question'"'"' in c.model_fields for c in M)"'
# what does M actually contain?
python -c "import inspect;from pydantic import BaseModel;from deepreason.llm import wire;\
M=[getattr(wire,n) for n in dir(wire) if 'Critic' in n and inspect.isclass(getattr(wire,n)) and issubclass(getattr(wire,n),BaseModel)];\
[print(c.__name__, c.__module__, 'successor_question' in c.model_fields) for c in M]"
# mutate the SUBJECT: rename the field on both wire models (2 occurrences)
sed -i 's/^    successor_question: str | None = None$/    successor_q: str | None = None/' src/deepreason/llm/wire.py
eval "$CHK"; echo "map check rc=$?"
python -m pytest tests/test_successor_law_line.py tests/test_successor_registry.py tests/test_successor_questions.py tests/test_successor_minting.py tests/test_successor_rank_tie.py -q; echo "tranche ring rc=$?"
git checkout -- src/deepreason/llm/wire.py
```

**Observed.**

```
Critic-named model classes visible in deepreason.llm.wire:
  ArgumentativeCriticOutput              defined in deepreason.llm.contracts           successor_question=True
  BatchCriticCaseWireV2                  defined in deepreason.llm.wire                successor_question=True
  BatchCriticOutput                      defined in deepreason.llm.contracts           successor_question=False
  BatchCriticWireV2                      defined in deepreason.llm.wire                successor_question=False
  CompactCritic                          defined in deepreason.llm.wire                successor_question=True

[CON168-rename-both-wire-fields] baseline rc=0 mutated rc=0 restored rc=0 restore_ok=True -> *** CANNOT FAIL ***
[wire-field-gone-vs-successor-tests] baseline rc=0 mutated rc=0 restored rc=0 restore_ok=True -> *** CANNOT FAIL ***
[N17b-wire-field-renamed] baseline rc=0 mutated rc=0 restored rc=0 restore_ok=True -> *** CANNOT FAIL ***

(control) [fixed-anchor-catches-rename] baseline rc=0 mutated rc=1 -> CAN FAIL
(control) [neg-half-scratch-named-wire-field] baseline rc=0 mutated rc=1 -> CAN FAIL
```

**Why it is a defect.** `M` is built from `dir(wire)`, which includes classes wire.py merely IMPORTS. `ArgumentativeCriticOutput` is defined in deepreason/llm/contracts.py, carries `successor_question`, and satisfies the `any(...)` anchor all by itself. So the anchor is vacuous with respect to the wire module the sentence is about: I renamed the field on both `CompactCritic` and `BatchCriticCaseWireV2` and the check stayed green. `grep -rn successor_question tests/` shows no test in the repo names either wire model's field, so the mutation also leaves all 42 tranche tests green — the wire mirror (both field declarations plus the two copy sites at wire.py:2600 and :2668) is pinned by nothing on this branch. SCHEMA.md check-writing rule 4 names exactly this trap ("a new sibling class (`AtomicCriticWireContractV2`) evaded spot-greps; pin the full parameter list"). The negative half of the same check is sound — I confirmed a `scratch`-named field on `CompactCritic` turns it red — so only the anchor needs replacing.

**Proposed fix.**

Replace the trailing `assert any('successor_question' in c.model_fields for c in M)` with an explicit two-class assertion in BOTH copies of the check — docs/map/SEAM-rules-x-scratch.md:262 and docs/map/CON-successor-questions.md:168: `assert {'CompactCritic','BatchCriticCaseWireV2'} <= {c.__name__ for c in M if 'successor_question' in c.model_fields}`. I verified this variant goes red on the rename and green on restore.

---

## F34 — The new map document describes a routing behaviour in the present tense that no production code path can reach, and never says so

**MAJOR** · lens S5 map checks · `docs/map/CON-successor-questions.md:10`

**The claim under test.** docs/map/CON-successor-questions.md:10-16: "A criticism may propose the question it thinks should be asked NEXT. The proposal is one OPTIONAL string on the criticism output contracts, and this package decides what happens to it: by default it becomes one advisory scratch block linked to the problem it was proposed under, where a conjecturer seat meets it through the ordinary attention pack." Its "## Entry points" section (SCHEMA.md: "the functions an outside caller actually calls") lists `resolve`, `route`, `mint`, `unknown_destination_notices`, `minting_notices`.

**Commands.**

```
export PYTHONPATH=$PWD/src:$PWD/mini
# any production import of the package outside the package itself?
grep -rn 'deepreason.successor\|from deepreason import successor' --include=*.py src/deepreason | grep -v '^src/deepreason/successor/'
echo "exit=$?  (no output = no production caller)"
# who names route/mint/resolve at all
grep -rln 'successor import\|successor\.route\|successor\.mint' --include=*.py src tests tools scripts
# does crit.py, which owns the field, do anything with it?
grep -n successor src/deepreason/rules/crit.py; echo "crit.py exit=$?"
```

**Observed.**

```
$ grep -rn 'deepreason.successor|from deepreason import successor' --include=*.py src/deepreason | grep -v '^src/deepreason/successor/'
(no output)

$ grep -rln 'successor import|successor.route|successor.mint' --include=*.py src tests tools scripts
src/deepreason/successor/__init__.py
src/deepreason/successor/registry.py
tests/test_successor_registry.py
tests/test_successor_minting.py
tests/test_successor_law_line.py
tests/test_successor_questions.py

$ grep -n successor src/deepreason/rules/crit.py
crit.py exit=1   (no match — the field is parsed into the contract and never read again)
```

**Why it is a defect.** SCHEMA.md: the map "says what the code *is*", "Aspiration... If it is not in `src/`, it is not in the map", and Entry points are "the functions an outside caller actually calls". Nothing under src/deepreason outside the package imports `deepreason.successor`, so in any real run a filled `successor_question` reaches the contract object and stops: no block is written, no conjecturer sees it, no receipt is recorded. The document states the opposite in the indicative and repeats it in "State it owns" ("The default destination writes one ordinary `scratch-block` object plus one `BLOCK_CREATED` scratch event"). DELIVERY.md states the gap plainly as residue #1 ("Nothing in production calls `route` or `mint`... This is the single largest gap between 'delivered' and 'working'") — so this is an omission in the map specifically, and it is the sentence a future reader will act on when asking "where does a successor question go?". The omission is not covered by any check: every green check in the document exercises the library from tests.

**Proposed fix.**

In docs/map/CON-successor-questions.md, immediately after the "## What it is" paragraph (before "Three things it is deliberately NOT"), insert: "NOTHING IN PRODUCTION CALLS THIS YET. The road is built, tested and mutation-proved, but no module outside `src/deepreason/successor/` imports it: a live run today records the field on the criticism contract and routes nothing. The one dispatch site is exactly what the tranche's parked Q3 decides (`experiments/2026-08-30-change-successor-questions/PARKED.md`)." and add, at column 0 on the following line, a check that will go red the day it is wired — forcing this paragraph to be rewritten then: ``check: ! grep -rq "deepreason.successor" --include=*.py src/deepreason --exclude-dir=successor && python -c "import deepreason.successor"`` (the second conjunct is the positive anchor SCHEMA.md rule 1 requires). Change the "## Entry points" heading to "## Entry points (library surface; no production caller yet)".

---

## F8 — A map `check:` line that cannot fail on any production change, and --audit does not flag it

**MINOR** · lens S1 never-penalized · `docs/map/CON-successor-questions.md:80`

**The claim under test.** docs/map/CON-successor-questions.md line 80: "`check: python -m pytest tests/test_successor_law_line.py::test_the_channel_has_no_permitted_exception_inside_a_deciding_package -q`", authenticating the sentence "the permitted-exception list is EMPTY. That emptiness is the current answer to the tranche's parked Q3."

**Commands.**

```
cd /home/user/DeepReason/.claude/worktrees/wf_9b72aacb-3ed-1
export PYTHONPATH=$PWD/src:$PWD/mini

sed -n '73,74p;120,133p' tests/test_successor_law_line.py    # PERMITTED and the test body
python tools/docs_verify.py --audit --jobs 2
```

**Observed.**

```
$ sed -n '73,74p' tests/test_successor_law_line.py
PERMITTED: tuple[pathlib.Path, ...] = ()

$ sed -n '120,133p' tests/test_successor_law_line.py   (test body, last line)
    assert PERMITTED == ()

$ python tools/docs_verify.py --audit --jobs 2
SEAM-llm-x-rules.md:54: unparseable check: a column-0 `check: opener must close with a trailing backtick ...
docs_verify --audit: 1 finding(s)

Observed across all eight mutations run in this audit (rank, admission,
exposure, registry subclass, registry numeric, anti_relapse x2, route x2):
test_the_channel_has_no_permitted_exception_inside_a_deciding_package never
failed once, including in the runs where its sibling pin-1 test went red.
```

**Why it is a defect.** The check re-runs a test whose entire body is `assert PERMITTED == ()`, where PERMITTED is a constant declared 47 lines above it in the same file. No change to any production file, and no change to any other test, can make it fail; only editing that one literal can. It therefore authenticates nothing about the code, which is the property `docs/map/SCHEMA.md` requires of a `check:` line -- and `docs_verify --audit`, whose job is "flag checks that cannot fail", does not name it (its single finding is the pre-existing unparseable opener in SEAM-llm-x-rules.md, which VALIDATION.md already attributes to baseline).

**Proposed fix.**

Either (a) drop the `check:` at docs/map/CON-successor-questions.md line 80 and leave the sentence as an unchecked statement of intent, or (b) replace it with a check that can actually rot -- one that re-derives the emptiness from the tree rather than from the test's own constant:

    `check: test "$(grep -rlE "deepreason\.successor|successor_question" --include=*.py src/deepreason/rules/ src/deepreason/scheduler/ src/deepreason/adjudication/ src/deepreason/informal/ | wc -l)" -eq 0`

Option (b) goes red the moment any dispatch site is added inside a deciding package, which is the event the sentence claims to be watching for.

---

## F13 — Nothing emits either typed notice, and DELIVERY.md's residue names only `route` and `mint`

**MINOR** · lens S2 configurability · `experiments/2026-08-30-change-successor-questions/DELIVERY.md:110`

**The claim under test.** DELIVERY.md residue 1: "**Nothing in production calls `route` or `mint`.** ... This is the single largest gap between 'delivered' and 'working', and it is one call site wide." CLAUDE.md P9 law, operational reading: "the minting road ... is BUILT and gated by a per-run flag, OFF by default, whose enablement emits the operator's own warning text".

**Commands.**

```
cd /home/user/DeepReason/.claude/worktrees/wf_9b72aacb-3ed-2
grep -rn "minting_notices\|unknown_destination_notices" --include=*.py src/ | grep -v "^src/deepreason/successor/"; echo "rc=$?  (1 == no hits outside the package)"
grep -rn "minting_notices\|unknown_destination_notices" --include=*.py src/deepreason/successor/
```

**Observed.**

```
$ grep -rn "minting_notices\|unknown_destination_notices" --include=*.py src/ | grep -v "^src/deepreason/successor/"
rc=1  (1 == no hits outside the package)

$ grep -rn ... src/deepreason/successor/
src/deepreason/successor/__init__.py:12:- `unknown_destination_notices` discloses a selector naming no registered row,
src/deepreason/successor/__init__.py:29:    minting_notices,
src/deepreason/successor/__init__.py:47:    "unknown_destination_notices",
src/deepreason/successor/registry.py:177:def unknown_destination_notices(config):
src/deepreason/successor/registry.py:211:def minting_notices(config):

(the only other references anywhere are the two test files)
```

**Why it is a defect.** The gap is wider than residue 1 states: besides `route` and `mint`, neither notice function has a caller anywhere in `src/`, so the operator's warning text — which the law says enablement must EMIT — reaches no CLI stream, no compile-notice list and no run record. PARKED.md's Q2 offers Road A (printed by the CLI) and Road B ("recorded on the run's own append-only record") and neither is built, but that is stated only inside the Q2 decision block, not in the residue section where a reader is told what the branch does and does not do. The functions are correct and return the verbatim text when called; nobody calls them. This is a completeness gap in the disclosure, not a behavioural defect.

**Proposed fix.**

In experiments/2026-08-30-change-successor-questions/DELIVERY.md, change residue 1's heading sentence to "**Nothing in production calls `route`, `mint`, `minting_notices` or `unknown_destination_notices`.**" and add after it: "So neither typed disclosure — the operator's warning text on the minting gate, and the unknown-destination fallback notice — reaches any CLI stream or any run record today; Q2 decides which road carries them, and neither road is built."

---

## F18 — The "counted mechanically" new-check attribution is wrong in both directions (12+5 claimed, 9+8 measured), and the map-document count is stated as six and as seven in the same tranche

**MINOR** · lens S3 scope+numbers · `experiments/2026-08-30-change-successor-questions/VALIDATION.md:197`

**The claim under test.** VALIDATION.md:197 and DELIVERY.md:83-90: "Twelve in CON-successor-questions.md (...) and five across the amended documents (CON-criticism-source.md row + trap, SEAM-rules-x-scratch.md rule 6 + trap, CON-problem-layer-lifecycle.md H1, SEAM-ontology-x-rules.md trap, CON-scheduler-ranking.md x 2)." Plus DELIVERY.md:24 "Six map documents move in the same commit" against VALIDATION.md:179 "all seven touched documents".

**Commands.**

```
cd /home/user/DeepReason/.claude/worktrees/wf_9b72aacb-3ed-3
git diff 3688713ee fdfe8a6e4 -- docs/map | grep -c '^+`check:'
git diff 3688713ee fdfe8a6e4 -- docs/map | grep -E '^(\+\+\+|\+`check:)' | sed 's/^+`check:.*/    +check/'
git diff --numstat 3688713ee fdfe8a6e4 -- docs/map | wc -l
# and with docs_verify's own parser, in /tmp/laneB:
python census.py
```

**Observed.**

```
17

+++ b/docs/map/CON-criticism-source.md
    +check
    +check
+++ b/docs/map/CON-problem-layer-lifecycle.md
    +check
+++ b/docs/map/CON-scheduler-ranking.md
    +check
    +check
+++ b/docs/map/CON-successor-questions.md
    +check   (nine of these)
+++ b/docs/map/INDEX.md
+++ b/docs/map/SEAM-ontology-x-rules.md
    +check
+++ b/docs/map/SEAM-rules-x-scratch.md
    +check
    +check

7    (files changed under docs/map)

(census via tools/docs_verify.py's own parser)
documents: 71
total checks: 1265
 touched: CON-successor-questions.md checks: 9
```

**Why it is a defect.** The headline 17 is correct and re-derives exactly, but the breakdown offered as its explanation is wrong in both halves — 9 rather than twelve in the new document, 8 rather than five across the amended ones — and the two errors happen to cancel. The sentence contradicts itself as written, since its own parenthetical enumeration already sums to 8 (2+2+1+1+2) while being labelled "five". Separately, the tranche calls the touched-document set "six" at DELIVERY.md:24, DELIVERY.md:85, VALIDATION.md:190 and VALIDATION.md:338, and "seven" at VALIDATION.md:179; the measured figure is seven, six amended plus one new.

**Proposed fix.**

In VALIDATION.md line 197 and the matching sentence in DELIVERY.md, replace "Twelve in CON-successor-questions.md ... and five across the amended documents" with "Nine in CON-successor-questions.md and eight across the amended documents (CON-criticism-source.md row + trap, SEAM-rules-x-scratch.md rule 6 + trap, CON-scheduler-ranking.md x 2, CON-problem-layer-lifecycle.md H1, SEAM-ontology-x-rules.md trap)". In DELIVERY.md line 24 replace "Six map documents move in the same commit" with "Seven map documents move in the same commit", and make VALIDATION.md lines 190 and 338 say "seven" to match line 179.

---

## F19 — S16b's own arithmetic is off by one: seven comment lines removed, not eight

**MINOR** · lens S3 scope+numbers · `experiments/2026-08-30-change-successor-questions/VALIDATION.md:85`

**The claim under test.** VALIDATION.md:85 "S16b: git diff -- src/deepreason/ontology/problem.py | grep '^-[^-]' -> eight comment lines and ONE code line."

**Commands.**

```
cd /home/user/DeepReason/.claude/worktrees/wf_9b72aacb-3ed-3
git diff 3688713ee fdfe8a6e4 -- src/deepreason/ontology/problem.py | grep -c '^-[^-]'
git diff 3688713ee fdfe8a6e4 -- src/deepreason/ontology/problem.py | grep '^-[^-]' | grep -c '^-\s*#'
```

**Observed.**

```
8
--- of which comment lines:
7
```

**Why it is a defect.** The removal is eight lines total: seven comments plus the one code line `SUCCESSOR = "successor"` (removed only because its trailing comment changed). "eight comment lines and ONE code line" says nine. The substantive part of S16b — that the enum member's NAME and VALUE are byte-identical and only the trailing comment moved — is correct, and is independently confirmed by S16a, which I re-ran to exit 0.

**Proposed fix.**

In experiments/2026-08-30-change-successor-questions/VALIDATION.md line 85, replace "-> eight comment lines and ONE code line" with "-> eight removed lines: SEVEN comment lines and ONE code line".

---

## F20 — DELIVERY.md names the wrong branch head and the wrong commit count, in the very commit that claimed to correct the head hash

**MINOR** · lens S3 scope+numbers · `experiments/2026-08-30-change-successor-questions/DELIVERY.md:3`

**The claim under test.** DELIVERY.md:3 "Branch: claude/b2-lane-B @ b690b814b (pushed, tree clean). Two commits: 6ce1f202f carries the change and the map; b690b814b carries the fix for a defect this tranche's own docs_verify run found in it, plus VALIDATION.md."

**Commands.**

```
cd /home/user/DeepReason/.claude/worktrees/wf_9b72aacb-3ed-3
git log --format='%H %s' origin/claude/b2-lane-B -1
git log --oneline 152c7e204..origin/claude/b2-lane-B
git show 3d0041010 -- experiments/2026-08-30-change-successor-questions/DELIVERY.md | head -25
```

**Observed.**

```
fdfe8a6e495da3c27c07ec130711571959f7a393 successor questions: correct the new-check count to a measured 17

fdfe8a6e4 successor questions: correct the new-check count to a measured 17
3d0041010 successor questions: close the tranche -- DELIVERY head hash and checklist correction
b690b814b successor questions: read the scratch policy from the configuration, and record what docs_verify caught
6ce1f202f successor questions: the optional field, its pluggable destination, and the gated minting road
3688713ee lane B: REQUEST.md and SPEC.md for successor questions (operator P9 law, 2026-08-29)

(3d0041010's diff to DELIVERY.md)
-Branch: `claude/b2-lane-B` @ (see final commit; pushed, tree clean)
+Branch: `claude/b2-lane-B` @ `b690b814b` (pushed, tree clean). Two commits:
```

**Why it is a defect.** origin/claude/b2-lane-B is at fdfe8a6e4, and the tranche is four commits, not two. The commit titled "DELIVERY head hash and checklist correction" replaced an honest placeholder ("@ (see final commit)") with a specific claim that was already stale when written and grew staler at fdfe8a6e4 — the correction made the document less accurate than the placeholder it removed. A reviewer who diffs 3688713ee..b690b814b as instructed misses two commits; here both are documentation-only, so the practical harm is bounded, but the delivered head hash is exactly the field a delivery report exists to get right.

**Proposed fix.**

In experiments/2026-08-30-change-successor-questions/DELIVERY.md line 3, replace the sentence with: "Branch: `claude/b2-lane-B` @ `fdfe8a6e4` (pushed, tree clean). Four commits: `6ce1f202f` carries the change and the map; `b690b814b` carries the fix for a defect this tranche's own docs_verify run found in it, plus VALIDATION.md; `3d0041010` and `fdfe8a6e4` are artifact-only corrections to this file and CHECKLIST.md."

---

## F21 — The branch wheel-smoke transcript records exit 0, the exact artifact VALIDATION.md's own caution says invalidates such a measurement

**MINOR** · lens S3 scope+numbers · `experiments/2026-08-30-change-successor-questions/proof/wheel_operational_smoke_branch.txt:3`

**The claim under test.** VALIDATION.md Appendix D: "python -u scripts/wheel_operational_smoke.py — FAILS ... Both transcripts are committed at proof/wheel_operational_smoke_branch.txt and proof/wheel_operational_smoke_base.txt", closing with "the shell idiom `... | tail -8; echo \"EXIT=$?\"` reports TAIL's status, not the smoke's, and prints EXIT=0 over a failed run. The measurement above was taken by redirecting to a file and capturing $? directly."

**Commands.**

```
cd /tmp/laneB/experiments/2026-08-30-change-successor-questions/proof
wc -l wheel_operational_smoke_branch.txt wheel_operational_smoke_base.txt
grep -v '^::error' wheel_operational_smoke_branch.txt
grep -v '^::error' wheel_operational_smoke_base.txt
grep -n '::error title=DeepReason installed-wheel operational smoke failed' -B4 /tmp/laneB/scripts/wheel_operational_smoke.py
```

**Observed.**

```
   4 wheel_operational_smoke_branch.txt
   2 wheel_operational_smoke_base.txt

(branch, non-JSON lines)
OPERATIONAL_SMOKE_EXIT=0

[exited with code 0]

(base, non-JSON lines)
EXIT=1
```

**Why it is a defect.** The base transcript records EXIT=1, consistent with the stated capture method; the branch transcript records OPERATIONAL_SMOKE_EXIT=0 and [exited with code 0], which is not a direct $? capture and is precisely the misleading reading the appendix warns the next reader about. The substantive claim survives: the branch transcript does contain the `::error title=DeepReason installed-wheel operational smoke failed::` payload, which scripts/wheel_operational_smoke.py:3061 emits only on failure, with "stage":"continuation_resume" and "failure_kind":"assertion_failed" byte-identical to the base transcript, so the "fails identically at base and branch" conclusion holds on the payload. I did NOT re-run the smoke (it builds and installs a wheel and drives a full run lifecycle — too expensive for a shared 4-CPU box), so I establish only what the committed transcripts contain.

**Proposed fix.**

In experiments/2026-08-30-change-successor-questions/VALIDATION.md Appendix D, replace "The measurement above was taken by redirecting to a file and capturing $? directly." with "The BASE measurement was taken by redirecting to a file and capturing $? directly (EXIT=1). The BRANCH transcript's trailing OPERATIONAL_SMOKE_EXIT=0 is a pipeline status, not the smoke's; the branch failure is established by the ::error payload (failure_kind assertion_failed, stage continuation_resume), which the script emits only on failure, not by that line." Alternatively, re-capture proof/wheel_operational_smoke_branch.txt with a direct $?.

---

## F22 — Two mutation transcripts declare a "Mutant diff:" and contain none, so the mutation cannot be re-applied from the transcript

**MINOR** · lens S3 scope+numbers · `experiments/2026-08-30-change-successor-questions/proof/law_line_pin2_red.txt:5`

**The claim under test.** proof/law_line_pin2_red.txt: "Mutant: a numeric field (rank_bonus: int) added to SuccessorDeclaration ... Mutant diff:" followed immediately by "Command:". proof/registry_modularity_red.txt: "Mutant: route() branches on the row id instead of dispatching through the registered writer ... Mutant diff:" followed immediately by "Command:". DELIVERY.md cites both as the mutation proofs for R1 pin 2 and R3.

**Commands.**

```
cd /tmp/laneB/experiments/2026-08-30-change-successor-questions/proof
sed -n '1,8p' law_line_pin2_red.txt
sed -n '1,8p' registry_modularity_red.txt
grep -c '^diff --git' law_line_pin1_red.txt rank_tie_red.txt route_mutants_red.txt law_line_pin2_red.txt registry_modularity_red.txt
```

**Observed.**

```
MUTATION PROOF — pin 2 of tests/test_successor_law_line.py
Date: 2026-08-30T04:42:23Z
Mutant: a numeric field (rank_bonus: int) added to SuccessorDeclaration —
        the weight the formalism-optional law forbids anyone to be able to set.
Mutant diff:

Command: python -m pytest tests/test_successor_law_line.py -q

(registry_modularity_red.txt has the same shape: "Mutant diff:", a blank line, then "Command:")
```

**Why it is a defect.** Five of the seven transcripts carry a real unified diff; these two carry the header and nothing under it, so the mutation is recoverable only from a prose sentence. That matters in this program specifically, because the point of a committed mutation transcript is that a later skeptic can re-apply it. The reds themselves are genuine: I reconstructed the registry mutant from the failure text (a `destination.id == "scratchpad.v1"` branch inside route()) and reproduced the transcript's exact verdict — 3 failed, 7 passed, the same three test names, the same AssertionError ('scratchpad.v1', [registry.py, route.py]). A smaller related wrinkle: all four mutant diffs in route_mutants_red.txt also include the Appendix-B `_workflow_manifest` -> `getattr(config, "scratchpad")` hunk, which is the tranche's own FIX and not part of any mutation, because they were regenerated against the pre-fix commit.

**Proposed fix.**

Regenerate the two transcripts with their diffs, or — if the mutants are no longer to hand — replace the empty "Mutant diff:" header in each with the exact edit in words. proof/registry_modularity_red.txt: "Mutant (no diff captured; reconstructable): in src/deepreason/successor/route.py, replace `writer = writer_for(destination.id)` with `if destination.id == \"scratchpad.v1\": writer = _write_scratch_block` / `else: writer = None`." proof/law_line_pin2_red.txt: "Mutant (no diff captured): add `rank_bonus: int = 0` to SuccessorDeclaration in src/deepreason/successor/registry.py." Also add one line to route_mutants_red.txt noting that the first hunk of each diff is the Appendix-B configuration-read fix, not part of the mutant.

---

## F26 — test_the_channel_has_no_permitted_exception_inside_a_deciding_package is a tautology on a constant in its own file, and a map check: line cites it as enforcement

**MINOR** · lens S4 mutation-proof · `tests/test_successor_law_line.py:130`

**The claim under test.** tests/test_successor_law_line.py:18-27 — "Pinned four ways, because each closes a different route in"; :120-130 the test itself, whose docstring says "The exception list is EMPTY, and emptiness is the claim ... which is the alarm working, not failing". docs/map/CON-successor-questions.md:80 — "`check: python -m pytest tests/test_successor_law_line.py::test_the_channel_has_no_permitted_exception_inside_a_deciding_package -q`", counted among VALIDATION.md's "new checks added by this change: 17".

**Commands.**

```
export PYTHONPATH=$PWD/src:$PWD/mini
sed -n '73p;120,131p' tests/test_successor_law_line.py
python -m pytest tests/test_successor_law_line.py::test_the_channel_has_no_permitted_exception_inside_a_deciding_package -q -p no:randomly
# and: it stayed green under every one of the 33 source mutations applied in this audit
```

**Observed.**

```
===== E3: the PERMITTED tautology =====
PERMITTED: tuple[pathlib.Path, ...] = ()

def test_the_channel_has_no_permitted_exception_inside_a_deciding_package():
    """The exception list is EMPTY, and emptiness is the claim.
    ...
    """
    assert PERMITTED == ()

--- CON-successor-questions.md:80 (the PERMITTED tautology check) ---
.                                                                        [100%]
1 passed in 0.04s
```

**Why it is a defect.** `PERMITTED` is a module constant declared `PERMITTED: tuple[pathlib.Path, ...] = ()` at line 73 of the same test file, and the test's only statement is `assert PERMITTED == ()`. No change to any file under src/ can redden it — confirmed across all 33 source mutations in this audit, in every one of which it stayed green. It is therefore one of the 42 "tests" that guards nothing about production. The map check at CON-successor-questions.md:80 promotes that tautology into a docs_verify enforcement line, which contradicts the map's own check-writing rule ("New behaviour needs a new check that would fail if the behaviour regressed"), and `docs_verify --audit` — which VALIDATION.md reports "names no finding for CON-successor-questions" — did not catch it. The real alarm the docstring describes is already carried by the sibling test on line 93, which does redden when a deciding package names the machinery (verified).

**Proposed fix.**

Two-line repair. (1) Delete the `check:` line at docs/map/CON-successor-questions.md:80 — the whole-file check at line 72 (`python -m pytest tests/test_successor_law_line.py -q`) already covers the law line, and the failable half of this claim is test_nothing_that_labels_ranks_or_admits_reads_a_successor_question. (2) In tests/test_successor_law_line.py, add one sentence to that test's docstring stating plainly what it is: "This assertion cannot be reddened by any change to src/: it is a tripwire on this file's own constant, so that adding a path to PERMITTED is a deliberate edit here rather than a silent widening. The failable guard is test_nothing_that_labels_ranks_or_admits_reads_a_successor_question above."

---

## F27 — test_the_successor_trigger_sorts_after_the_seed_in_the_rank_term asserts a substring count and three Python tautologies; an inverting mutation that keeps the substring leaves it green

**MINOR** · lens S4 mutation-proof · `tests/test_successor_rank_tie.py:95`

**The claim under test.** tests/test_successor_rank_tie.py:81-98 — "The mechanism, asserted directly, so a reader need not re-derive it. The rank term is a BOOLEAN over the trigger, and this is the whole content of the guarantee: a successor is not the seed, `True` sorts after `False`, and no configuration can change either fact."

**Commands.**

```
export PYTHONPATH=$PWD/src:$PWD/mini
python - <<'PY'
import pathlib
p = pathlib.Path("src/deepreason/scheduler/scheduler.py"); t = p.read_text()
t = t.replace("                    p.provenance.trigger != SpawnTrigger.SEED,\n                    # AFTER the seed term",
              "                    not (p.provenance.trigger != SpawnTrigger.SEED),\n                    # AFTER the seed term")
t = t.replace("                p.provenance.trigger != SpawnTrigger.SEED,\n                -promotion_wounds.get(p.id, 0),",
              "                not (p.provenance.trigger != SpawnTrigger.SEED),\n                -promotion_wounds.get(p.id, 0),")
p.write_text(t)
PY
python -m pytest tests/test_successor_rank_tie.py -q -p no:randomly -rf
git checkout -- src/deepreason/scheduler/scheduler.py
```

**Observed.**

```
===== E5: rank-term substring survives an inverting mutation =====
F.F                                                                      [100%]
=========================== short test summary info ============================
FAILED tests/test_successor_rank_tie.py::test_a_minted_successor_loses_the_rank_tie_to_the_seed_question
FAILED tests/test_successor_still_gets_worked_once_the_question_has_been
2 failed, 1 passed in 0.16s

(the one that PASSED is test_the_successor_trigger_sorts_after_the_seed_in_the_rank_term — the middle '.' in 'F.F')
```

**Why it is a defect.** Its first three assertions (`assert (SpawnTrigger.SEED != SpawnTrigger.SEED) is False`, `assert (SpawnTrigger.SUCCESSOR != SpawnTrigger.SEED) is True`, `assert sorted([True, False]) == [False, True]`) are properties of Python and of the enum, not of this repo; no change anywhere can redden them. Its fourth is `source.count("provenance.trigger != SpawnTrigger.SEED") == 2` — a substring count, which survives wrapping both occurrences in `not (...)`, i.e. survives an edit that reverses the guarantee the file exists to protect. The guarantee itself is NOT lost: the two sibling behavioural tests both went red under the same mutation. So this is an over-claim in the docstring rather than an unguarded behaviour.

**Proposed fix.**

In tests/test_successor_rank_tie.py, delete the three tautological assertions on lines 88-90 and correct the docstring's opening to say what the remaining assertion does: "The rank key's TEXT, pinned so a change to the seed term's arity is visible. This is a source-count check, not a behavioural one — an edit that keeps the substring but inverts its sense passes here and is caught by the two behavioural tests in this file instead."

---

## F28 — test_the_producer_is_outside_scan_spawns is a spelling check: a genuine H1 relapse spelled SpawnTrigger("successor") leaves all 42 tests green

**MINOR** · lens S4 mutation-proof · `tests/test_successor_minting.py:216`

**The claim under test.** tests/test_successor_minting.py:21-24 — "What did NOT change, and is asserted here rather than assumed: the producer lives outside `src/deepreason/rules/` and is never reached from `scan_spawns`, so H1's deletion -- nothing mints a problem AUTOMATICALLY FROM A REFUTATION -- stands exactly as it was." and :208-212 — "H1 forbade minting AUTOMATICALLY FROM A REFUTATION inside `scan_spawns`, and that is untouched". DELIVERY.md: "the ONE producer of `SpawnTrigger.SUCCESSOR` ... lives outside `src/deepreason/rules/` so that H1's deletion stays deleted".

**Commands.**

```
export PYTHONPATH=$PWD/src:$PWD/mini
# re-insert an H1 refutation->successor loop into scan_spawns, spelled without the literal:
python - <<'PY'
import pathlib
p = pathlib.Path("src/deepreason/rules/spawn.py"); t = p.read_text()
loop = ('    for _aid, _st in sorted(status.items()):\n'
        '        if _st == Status.REFUTED:\n'
        '            for _pid in sorted(addressed.get(_aid, ())):\n'
        '                _spawn(\n'
        '                    SpawnTrigger("successor"),\n'
        '                    [_pid, _aid],\n'
        '                    f"successor to refuted {_aid[:12]}",\n'
        '                    problem_id=f"succ:{_aid[:12]}",\n'
        '                )\n\n')
p.write_text(t.replace("    # Discrimination: >=2 surviving rivals for one problem. A discrimination",
                       loop + "    # Discrimination: >=2 surviving rivals for one problem. A discrimination"))
PY
python -m pytest tests/test_successor_law_line.py tests/test_successor_minting.py tests/test_successor_questions.py tests/test_successor_rank_tie.py tests/test_successor_registry.py tests/test_h1_no_spawn_from_refutation.py tests/test_decommissioned_pipeline_stays_out.py -q -p no:randomly -rf
git checkout -- src/deepreason/rules/spawn.py
```

**Observed.**

```
########## M47 scan_spawns DOES mint from a refutation, spelled SpawnTrigger('successor') ##########
SUMMARY: ['2 failed, 50 passed in 2.25s']
  RED: tests/test_h1_no_spawn_from_refutation.py::test_refutation_alone_cannot_grow_the_problem_frontier
  RED: tests/test_decommissioned_pipeline_stays_out.py::test_no_source_file_produces_a_successor_problem

(all 42 of the tranche's own tests, including test_the_producer_is_outside_scan_spawns, stayed GREEN)
```

**Why it is a defect.** The test's assertions are `"SpawnTrigger.SUCCESSOR" not in inspect.getsource(scan_spawns)`, `"deepreason.successor" not in source`, `"H1" in source`, and a path check on `inspect.getsourcefile(mint)`. All four are about spelling and location; none executes scan_spawns. A relapse written as `SpawnTrigger("successor")` — the H1 loop actually restored — passes every one of them. The guarantee survives only because a PRE-EXISTING test outside this tranche, tests/test_h1_no_spawn_from_refutation.py::test_refutation_alone_cannot_grow_the_problem_frontier, catches it behaviourally. So the module docstring's "asserted here rather than assumed" is not accurate: what is asserted here is a spelling, and the assumption is carried elsewhere. (The second red above, test_no_source_file_produces_a_successor_problem, is already red at baseline and carries no additional signal.)

**Proposed fix.**

In tests/test_successor_minting.py, correct the two over-claims rather than adding machinery. Change the module docstring lines 21-24 to: "What did NOT change: the producer lives outside `src/deepreason/rules/` and is never reached from `scan_spawns`. This file pins that by LOCATION and SPELLING; the behavioural guard on H1 -- nothing mints a problem automatically from a refutation -- is tests/test_h1_no_spawn_from_refutation.py::test_refutation_alone_cannot_grow_the_problem_frontier, which is where a relapse spelled around this file's literals is caught." And change test_the_producer_is_outside_scan_spawns's docstring line 210-212 from "and that is untouched" to "and this test pins the producer's location, not scan_spawns' behaviour -- see test_h1_no_spawn_from_refutation.py for the behavioural half."

---

## F29 — src/deepreason/successor/__init__.py claims __all__ is "pinned by tests/test_successor_registry.py"; no test pins it — removing two names from __all__ leaves all 42 green

**MINOR** · lens S4 mutation-proof · `src/deepreason/successor/__init__.py:40`

**The claim under test.** src/deepreason/successor/__init__.py:38-40 — "# The DECLARED interface. `minting_notices` and the registration helpers are\n# reachable beside it as ordinary module attributes; this tuple is the surface a\n# consumer may rely on, pinned by tests/test_successor_registry.py."

**Commands.**

```
export PYTHONPATH=$PWD/src:$PWD/mini
python - <<'PY'
import pathlib
p = pathlib.Path("src/deepreason/successor/__init__.py"); t = p.read_text()
p.write_text(t.replace('    "mint",\n    "resolve",\n    "route",\n', '    "route",\n'))
PY
python -m pytest tests/test_successor_law_line.py tests/test_successor_minting.py tests/test_successor_questions.py tests/test_successor_rank_tie.py tests/test_successor_registry.py -q -p no:randomly
git checkout -- src/deepreason/successor/__init__.py
grep -rn "__all__" tests/test_successor_*.py
```

**Observed.**

```
########## M45 __all__ loses two declared names ##########
SUMMARY: ['42 passed in 2.29s']
  >>> NO TEST FAILED (all green under this mutation)

--- grep __all__ across the five new test files: ---
(no match)
```

**Why it is a defect.** No file among tests/test_successor_*.py contains the string `__all__`, so the source comment points a future maintainer at enforcement that is not there. The property IS in fact guarded — by the map check at docs/map/CON-successor-questions.md:97 (`python -c "import deepreason.successor as s; assert set(s.__all__) == {...}"`), which I ran and which exits 0 — but that check runs only under docs_verify, not under the pytest gate, and the comment names the wrong instrument. Under this audit's rule ("a claim whose cited evidence does not contain the measurement"), the cited evidence does not contain it.

**Proposed fix.**

In src/deepreason/successor/__init__.py, change line 40 from "consumer may rely on, pinned by tests/test_successor_registry.py." to "consumer may rely on, pinned by the `__all__` check in docs/map/CON-successor-questions.md (docs_verify), not by the pytest gate." If a gate-level pin is wanted instead, add four lines to tests/test_successor_registry.py:

    def test_the_declared_interface_is_exactly_six_names():
        import deepreason.successor as s
        assert set(s.__all__) == {
            "DESTINATIONS", "SUCCESSOR_DESTINATION_REGISTRY_VERSION",
            "mint", "resolve", "route", "unknown_destination_notices",
        }, s.__all__

---

## F35 — The per-document split of the 17 new map checks is wrong in both DELIVERY.md and VALIDATION.md: measured 9 and 8, not 12 and 5

**MINOR** · lens S5 map checks · `experiments/2026-08-30-change-successor-questions/DELIVERY.md:1`

**The claim under test.** DELIVERY.md: "new checks: 17, counted mechanically — `git diff 3688713ee..HEAD -- docs/map | grep -c '^+`check:'` -> 17 (twelve in the new document, five across the five amended ones)". VALIDATION.md restates it: "Twelve in `CON-successor-questions.md` (the modularity claim, the row-id absence, the interface `__all__`, the law line, the empty permitted-exception list, the link, the visibility, the shipped defaults, and four Traps checks) and five across the amended documents".

**Commands.**

```
git diff 3688713ee..d296ca2bd -- docs/map | grep -c '^+`check:'                        # total
git diff 3688713ee..d296ca2bd -- docs/map/CON-successor-questions.md | grep -c '^+`check:'  # new document
export PYTHONPATH=$PWD/src:$PWD/mini
python - <<'PY'
import subprocess, sys; sys.path.insert(0,'tools')
import docs_verify as dv; from pathlib import Path
for n in ["CON-successor-questions.md","CON-criticism-source.md","CON-problem-layer-lifecycle.md",
          "CON-scheduler-ranking.md","SEAM-ontology-x-rules.md","SEAM-rules-x-scratch.md","INDEX.md"]:
    def at(rev):
        p=subprocess.run(["git","show",f"{rev}:docs/map/{n}"],capture_output=True,text=True)
        return [c for _,c in dv.parse_text(p.stdout,Path(n)).checks] if p.returncode==0 else []
    old,new=at("84514a028"),at("d296ca2bd")
    print(n, "added=", len([c for c in new if c not in old]))
PY
```

**Observed.**

```
$ git diff 3688713ee..d296ca2bd -- docs/map | grep -c '^+`check:'
17
$ git diff 3688713ee..d296ca2bd -- docs/map/CON-successor-questions.md | grep -c '^+`check:'
9

== CON-successor-questions.md: old=0 new=9 added=9
== CON-criticism-source.md: old=15 new=17 added=2
== CON-problem-layer-lifecycle.md: old=21 new=22 added=1
== CON-scheduler-ranking.md: old=13 new=15 added=2
== SEAM-ontology-x-rules.md: old=16 new=17 added=1
== SEAM-rules-x-scratch.md: old=20 new=22 added=2
== INDEX.md: old=0 new=0 added=0
TOTAL ADDED CHECKS: 17
```

**Why it is a defect.** The total 17 is correct, but the split re-measures as 9 in the new document and 8 across the five amended ones. The error is not cosmetic — it is the visible symptom of the indented-check defect above: VALIDATION.md's enumeration counts "four Traps checks" in the new document when the mechanical command it cites sees only one (the six Traps entries carry six spans, five of them indented and therefore uncounted by `grep -c '^+`check:'` and unrun by docs_verify). Also, the sentence says "five across the FIVE amended ones" while SIX documents were amended; INDEX.md gained a row but no check.

**Proposed fix.**

In DELIVERY.md replace "(twelve in the new document, five across the five amended ones)" with "(nine in the new document, eight across the five amended documents that gained checks; INDEX.md gained a row and no check)", and in VALIDATION.md replace the matching paragraph with the same measured split. If the indented-check fix is applied first, re-run `git diff <base>..HEAD -- docs/map | grep -c '^+`check:'` and use the new number in both files rather than editing the split by hand.

---

