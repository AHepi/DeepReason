# AUDIT — DeepReason against Open Inquiry Specification 1.1

**Family:** `dr-audit-orchestrator`, dimension **spec-drift**. Read-only.
**Baseline:** `docs/proposals/ois-1.1/Open_Inquiry_Specification_1_1.md`,
authority `PopperSemanticsV1_1.md`, `Hardening_Audit.md`, and the package's own
`verification/` reference checker.
**Base commit:** `c26c66de7266968157c61e269fb927c5e368d2c3`
**Date:** 2026-09-05. **Model:** claude-opus-5.

**Nothing in the specification is adopted** (`docs/proposals/OIS_README.md`).
This audit measures distance. It fixes nothing, and it never treats the
specification as authority over an operator law: where the two conflict, the
conflict is the row.

## Map preflight

| id | document | why it is in scope |
|---|---|---|
| `DR-SUB-adjudication` | `docs/map/SUB-adjudication.md` | warrants → attack edges → status labels (checks 1, 11, 12) |
| `DR-SUB-rules` | `docs/map/SUB-rules.md` | every warrant mint site (checks 1, 2) |
| `DR-SUB-llm` | `docs/map/SUB-llm.md` | packs, wire contracts (checks 3, 4) |
| `DR-CON-warrants-and-attacks` | `docs/map/CON-warrants-and-attacks.md` | no warrant, no edge, no REFUTED (checks 1, 10) |
| `DR-CON-discharge-channel` | `docs/map/CON-discharge-channel.md` | discharge is never evidence (check 5) |
| `DR-INV-seat-section-plugins` | `docs/map/INV-seat-section-plugins.md` | what a seat is shown, as configuration (checks 3, 8) |
| `DR-INV-seat-section-sources` | `docs/map/INV-seat-section-sources.md` | where a section's content comes from (check 8) |
| `DR-INV-frozen-surfaces` | `docs/map/INV-frozen-surfaces.md` | read before designing anything (every parked prompt) |
| `DR-SEAM-adjudication-x-rules` | `docs/map/SEAM-adjudication-x-rules.md` | the seam checks 1 and 11 both sit on |

## Baseline reproduced before any check

```
$ git rev-parse HEAD
c26c66de7266968157c61e269fb927c5e368d2c3

$ cd docs/proposals/ois-1.1/verification && python -m unittest
Ran 66 tests in 0.073s
OK

$ cd docs/proposals/ois-1.1/verification && python run_mutations.py
Detected 9/9 selected mutations
```

`proof/check00-baseline.txt`. **66 tests, 9/9 mutations** — the specification's
own executable reading of its own rules, on this container. Those are checks on
the package's bookkeeping reference, not on DeepReason.

Rings re-run to reproduce the checks (no full gate; this is a read-only audit):
`tests/test_adjudication.py tests/test_adjudication_blindness.py` — **15 passed**;
`tests/test_discharge_law_line.py tests/test_discharge_channel.py` — **21 passed**;
`tests/test_seat_section_sources.py` — **26 passed**. (`proof/rings.txt`,
`proof/check05-discharge.txt`, `proof/check08-crossings.txt`.)

---

## Summary table

| # | Check | Spec clause | Verdict |
|---|---|---|---|
| 1 | Dependency exemption | §11.3, §26 "Essential dependency" | **DIFFERS IN OUTCOME** |
| 2 | Failed check counted as pass | §10, §26 "Body outcome checking" | CONFORMS |
| 3 | Status leakage into a seat's context | §1 K-REAL, §12.1 | **DIFFERS IN OUTCOME** |
| 4 | Critic premises unreachable from the wire | §11.1 | **NOT REPRESENTED** |
| 5 | Discharge is not evidence | §9 `Respond`, §10 | CONFORMS |
| 6 | Merge / absorb keeps identity and location | §9, audit S17 | **DIFFERS IN OUTCOME** |
| 7 | Maximal appraisals retained as a set | §9, §12.4, audit S18 | **NOT REPRESENTED** |
| 8 | Crossing completeness by construction | §10 receipts | **DIFFERS IN OUTCOME** |
| 9 | Stop reasons | §9 `EngagementChange` | CONFORMS |
| 10 | Alternatives vs. compatible rivals | §9 `Compare`, audit S22 | CONFORMS |
| 11 | The DA-1 labelling rule itself | §11.3 | **DIFFERS IN OUTCOME** |
| 12 | Hardening S05 / S17 / S18 / S22 | §§10, 11, 9, 12.4 | **DIFFERS IN OUTCOME** (2 of 4 exhibited) |

**4 conform. 6 differ in outcome. 2 are not represented.**
Parked prompts for all 8 non-conforming rows are in `PROMPTS.md`.

---

## 1 — Dependency exemption · DIFFERS IN OUTCOME

**Clause.** §11.3: *"For an argument labeled in, each declared essential
application is in. Consequently a dependent cannot remain in when one of those
applications is withdrawn as out in a recomputed appraisal. … This applies to
criticisms and other arguments without exception."* §26, row "Essential
dependency": exempting criticisms from dependency withdrawal must be detected.

**Command and output** (`proof/check01-repro.txt`, script `proof/check01_repro.py`):

```
$ python proof/check01_repro.py
DEPENDENCE ('refuted', 'suspended_unsupported')
EVIDENCE   ('accepted', 'refuted')
```

Reproduced at HEAD, matching the monitor's 2026-09-05 run exactly. Read the
first tuple: the criticism has lost its own standing (`suspended_unsupported`)
and its target is **still refuted**.

**Mint-site census, as the check asks** (`proof/check01-census.txt`,
`check01-census2.txt`, `check01-mintsites.txt`):

| site | warrant type | what ν's interface carries | can it ever carry a critic's own essential premise? |
|---|---|---|---|
| `informal/trial.py:1066` (argumentative trial) | ARGUMENTATIVE | nothing — ν is created with no `Interface` | no |
| `informal/trial.py:1401` (pairwise) | ARGUMENTATIVE | nothing | no |
| `rules/relatedness.py:145` | ARGUMENTATIVE | nothing | no |
| `rules/experiment.py:385` | ARGUMENTATIVE | nothing | no |
| `rules/vision.py:99` | ARGUMENTATIVE | `EVIDENCE` refs to the recorded screenshots | only the shots, never a declared premise |
| `rules/crit.py:1041,1224` (via `register_fail_warrant`) | DEMONSTRATIVE | `MENTION` refs (generator, proposal) — inert, no closure | no |
| `informal/trial.py:822` (case law) | DEMONSTRATIVE | `MENTION` ref to the applied standard — reached by the rubric case-law extension only | the standard, not the critic's premises |
| `rules/act.py:178` | DEMONSTRATIVE | `EVIDENCE` ref to the evidence artifact | no |
| `premises.py:569` | DEMONSTRATIVE | `EVIDENCE` ref to a derivation manifest | no |

Three `EVIDENCE` sites exist and the evidence closure in
`adjudication/edges.py:158-170` works correctly on all three. **None of them is
reachable from a critic's own declaration** — see check 4.

**Record evidence.** No committed root exercises the correct branch: across all
86 committed roots, `RefRole.EVIDENCE` appears on a ν only through
`rules/vision.py`, and no root ran a vision criticism. The 27
`register_fail_warrant` call sites are the record's whole supply of
premise-bearing νs.

**Distance verdict: DIFFERS IN OUTCOME.** A defect tranche is already
commissioned for the behaviour; this row's contribution is the census, which
says the fix has nine sites, not one.

---

## 2 — Failed check counted as pass · CONFORMS

**Clause.** §10: *"`PASS` means that a declared, executable check passed. `FAIL`
means that it failed. `UNKNOWN` means that the check is unavailable or its input
is insufficient. … admission alone cannot turn that body into successful
evidence through that schema."* §26, "Body outcome checking".

**Command and output** (`proof/check02-failwarrant.txt`, `check02-verdicts.txt`):

```
$ grep -rn "register_fail_warrant" src/ | wc -l
27
$ grep -n "PASS, FAIL, OVERRUN" src/deepreason/programs.py
33:PASS, FAIL, OVERRUN = "pass", "fail", "overrun"
```

DeepReason's `OVERRUN` is the spec's `UNKNOWN`: the harness saying it obtained
no verdict. Every consumer declines on it.

| verdict | what it mints |
|---|---|
| `PASS` | nothing (the commitment held) |
| `FAIL` | a DEMONSTRATIVE fail warrant + ν + critic |
| `OVERRUN` | **nothing** — `rules/crit.py:893` "the property oracle was unusable on this input and produced no verdict — the proposed input grounds nothing"; `rules/crit.py:1145` quarantines and continues |
| sandbox abort | nothing (`rules/crit.py:887`) |

The prose sides match: `informal/trial.py:_decline` and `_block` (lines 323-336)
record a `Measure` and return `None` — never a warrant. `scheduler.py:259`
excludes `OVERRUN` from the denominator on the same reasoning.

**Distance verdict: CONFORMS.**

---

## 3 — Status labels re-entering a seat's context · DIFFERS IN OUTCOME

**Clause.** §1, K-REAL, prohibited substitution: *"A record label becomes
truth."* §12.1: *"A software API must not alias an `in` label or a positive-case
summary to a field called `is_creative`, `true`, or `universality_verified`."*
The configuration document's own row asserts DeepReason already has this.

**Command and output** (`proof/check03-status-leak.txt`). The configuration
document's grep, exactly as written, passes:

```
$ grep -rniE "accepted|refuted|suspended" src/deepreason/packs/ \
      src/deepreason/llm/seat_sections.py src/deepreason/llm/seat_templates.py
(no output)
```

It passes because it names three files that do not render the label. The two
that do:

```
$ grep -rn "state.status" src/deepreason/llm/
src/deepreason/llm/packs.py:151:        if state.status.get(aid) != Status.ACCEPTED:
src/deepreason/llm/packs.py:780:        for aid, status in state.status.items()
src/deepreason/llm/packs.py:900:                status = state.status.get(x)
src/deepreason/llm/seat_plugins.py:388:            for aid, status in request.state.status.items()
src/deepreason/llm/seat_plugins.py:619:            status = request.state.status.get(x)
```

`packs.py:900` and `seat_plugins.py:619` both write `f"- {x} [{status.value}]"`.
The plugin carrying line 619 is `dr.standing-attacks`, and it sits in
`CRITIC_LEGACY_LAYOUT` at priority 5 (`seat_layouts.py:88`) — the **shipped
default** for the critic seat. `seat_plugins.py:388-395` is `dr.history.v1`,
which selects on `Status.REFUTED` and prints the word "refuted" in its header
(off by default since the 2026-09-05 history ruling, but registered).

**Record evidence, arm 1** — the shipped renderer against a committed root's own
state, read-only (`proof/check03-record.txt`, script `proof/check03_record.py`):

```
$ python proof/check03_record.py experiments/2026-09-02-live-p-a2-corrected/run
root            : experiments/2026-09-02-live-p-a2-corrected/run
artifacts       : 94
attack edges    : 12
target chosen   : 61e8fb27e67697a5d0ccb1e8bde257a21109975528254617bb5a864edd9a8318
attacker labels : 045499e53e23=accepted

--- verbatim slice of the pack the shipped default critic layout renders ---
standing attacks (do not repeat these):
- 045499e53e23206fa66ba030ed2fa50488e702772c4cff8984d05f9831821060 [accepted]: critic: pa1-scaling-law@v1 failed on 61e8fb27e676
```

**Record evidence, arm 2** — the history arms of
`experiments/2026-09-03-change-provenance-history-channel/`. The rendered block
(`runs/history-real.txt`) reads:

```
WHAT HAS ALREADY BEEN REFUTED ON THIS PROBLEM
  - REFUTED: Kind: Abstraction. The isolated node represents an abstract instance of the 'Error Elimination Principle' …
      refuted by: critic: relation-form@578e42df713e failed on 364e5e24a2b2
```

and it is in the record, inside a conjecturer's own prompt, in **33 blobs** of
root `runs/home-m1/runs/run-f23da86ddfd5ab820957221cfebe4b2e` — not as prose but
under the heading `## citable-evidence-blocks`, as block `[426c91fb917ad6f1]`,
i.e. a status label the seat was invited to **cite as evidence**. The critic arm
(`runs/critic-real.txt`) does the same with `SUSTAINED` / `NOT SUSTAINED`.

**Distance verdict: DIFFERS IN OUTCOME.** The configuration document's row
"status labels never re-enter a seat's context" is false twice over: once in
shipped default code, once in the record.

---

## 4 — Critic premises unreachable from the wire · NOT REPRESENTED

**Clause.** §11.1: *"An application identifies a use of a content, a provisional
premise, or an inferential step … An essential premise cannot be reclassified as
an annotation merely to keep its dependent standing."*

**Command and output** (`proof/check04-critic-contract.txt`):

```
$ grep -rn "premises_essential|essential_premise|essential_uses" src/
(no output)
```

`ArgumentativeCriticOutput` (`llm/contracts.py:112-145`) carries `attack`,
`case`, `counterexample`, `premise`, `premise_evidence` and the successor
question. `premise` is documented in the code itself as *"A presupposition of the
PROBLEM that forbids nothing"* — the problem's presupposition, not the
criticism's own load-bearing premises. No field carries what §11.1 calls
`essential_application_ids`.

**Distance verdict: NOT REPRESENTED.** This is the wire half of check 1: even
where a mint site could register an `EVIDENCE` ref, there is nothing for it to
register.

---

## 5 — Discharge is not evidence · CONFORMS

**Clause.** §9: *"Neither a disposition name nor the creation of a reason token
establishes reason use."* §10's separation of receipt, case and assessment.

**Command and output** (`proof/check05-discharge.txt`):

```
$ python -m pytest tests/test_discharge_law_line.py tests/test_discharge_channel.py -q
21 passed in 0.60s
```

`DischargeWireV1`'s own docstring states the law line: *"NOTHING here is
evidence. A discharge is a precondition on SUBMISSION; no field, kind or count
may feed a label, a warrant, a rank or an admission decision."* The type is
imported at exactly two sites outside its definition (`llm/wire.py`,
`workloads/text.py`) — neither is an adjudication, rank or admission path.

**Record evidence** (script `proof/check05_record.py`):

```
$ python proof/check05_record.py experiments/2026-08-26-pc2-rematch/run
root                                  : experiments/2026-08-26-pc2-rematch/run
discharge-tagged record events        : 1612
tags                                  : {'discharge-reask': 44, 'discharge-undischarged': 1568}
rule of every event mentioning discharge : ['Measure']
discharge events that minted an artifact, an att/dep edge, or an LLM call: 0
```

1 612 discharge occurrences in one root; every one is a `Measure` with empty
`outputs` and an empty `state_diff`. The record shows the law holding, not just
the code claiming it.

**Distance verdict: CONFORMS.**

---

## 6 — Merge / absorb keeps identity and location · DIFFERS IN OUTCOME

**Clause.** §9: *"Absorption references a selected earlier contribution or
snapshot of an episode, together with a connection account. Imported events
retain their original identity and location. A merge does not require imported
events to occur after the merge."* Audit S17.

**Command and output** (`proof/check12-hardening.txt`, S17 block; also
`proof/check06-merge.txt`):

```
  source   id 81f29b00799c334398d6a5d4  log seq 0  role conjecturer
  imported id 81f29b00799c334398d6a5d4  log seq 2  role import
  identity kept      : True   (ids are content-addressed)
  original log location kept : False
  original role kept : False
```

`Artifact.compute_id(content_ref, codec, interface)` (`harness.py:412`) means an
imported contribution keeps its **identity** for free. It does not keep its
**location**: `imports.py` calls `harness.create_artifact(...,
provenance=Provenance(role="import"))` at nine sites (lines 372-628), so the
import is a new event in the importing run's own sequence, after the merge, and
the originating role is overwritten.

**Record evidence.** Zero of the 86 committed roots carry import-role
provenance: the path has never run live, so nothing in the record contradicts or
confirms the offline demonstration.

**Distance verdict: DIFFERS IN OUTCOME** on location and originating role;
identity conforms. Note this is entangled with a standing DeepReason invariant —
*"import-role admission records never count as survivors"* (CLAUDE.md) — which
is a deliberate reason for the role rewrite. Any change here must keep it.

---

## 7 — Maximal appraisals retained as a set · NOT REPRESENTED

**Clause.** §9: *"Concurrent maximal appraisals and engagement reports are
retained as a set. A display must report disagreement or incompleteness rather
than arbitrarily choose a maximum."* §12.4. Audit S18.

**Command and output** (`proof/check07-maxima.txt`):

```
$ grep -rn "max(|sorted(" src/deepreason/views/ src/deepreason/report.py
… 33 sites, none of which selects a "current" judgment by log order …

$ grep -rni "appraise|appraisal" src/ --include=*.py
src/deepreason/calculus/render.py:106:    appraisal may not read origin (Ax 4.1).
src/deepreason/calculus/succession.py:157: … (comments only)
```

`EpistemicState.status` is `dict[str, Status]` — exactly one label per artifact,
**computed** by `adjudication/` from the attack graph, never **selected** from
competing records. The specific S18 defect (an arbitrary maximum chosen by log
or upload order) is therefore absent. So is the thing it is a defect in: there
is no `Appraise` record, no appraiser identity, no supersession, and no way for
two inquirers to disagree on the record.

**Distance verdict: NOT REPRESENTED.**

---

## 8 — Crossing completeness by construction · DIFFERS IN OUTCOME

**Clause.** §10: *"A receipt records material supplied to the system, including
material that cannot be parsed by its current schema."* The receipting
obligation, applied to every insertion into a seat's context.

**Command and output** (`proof/check08-crossings.txt`):

```
$ grep -rn "section_plan|SectionPlan" src/ --include=*.py
src/deepreason/rules/conj.py:1777:        section_plans = _section_plans(
src/deepreason/workflow/transaction_service.py:347:    def section_plan(
… and nothing else that CREATES one …

$ grep -rn "open(|Path(|requests\.|subprocess|urllib" src/deepreason/seat_sources/
(none — no source reads a file or a tool)

$ python -m pytest tests/test_seat_section_sources.py -q
26 passed in 0.67s
```

The receipt itself is real and detailed. From a committed root
(`experiments/2026-09-03-change-provenance-history-channel/runs/home-m1-r3/runs/run-f23da86ddfd5ab820957221cfebe4b2e/objects/workflow-context-section-plan-v1/`):

```json
{"data": {"layout_id": "seat-pack.conjecturer.legacy-v0", "layout_version": "1.0.0",
  "sections": [
    {"disposition": "rendered", "plugin_id": "dr.problem",          "rendered_bytes": 500,  "source_bytes": 500},
    {"disposition": "rendered", "plugin_id": "dr.open-criticisms",  "rendered_bytes": 3922, "source_bytes": 3922},
    {"disposition": "absent",   "plugin_id": "dr.mandatory-interface", "rendered_bytes": 0, "source_bytes": 0}, …]}}
```

**But only `rules/conj.py` emits one.** The critic, experiment, property and
counterexample-retry packs are built by `render_batch_crit_pack`,
`render_crit_pack`, `render_experiment_pack`, `render_property_pack` and
`render_cx_retry_pack` (`llm/packs.py:719-1180`) and receipt nothing. In the
record: **5 of 86 committed roots** carry section-plan receipts at all, and all
five are conjecturer-side.

The narrower claim the check also asks about does hold: no seat section source
reads a file or a tool, so no unreceipted external text enters that way, and
admission blocks remain the only route for external text.

**Distance verdict: DIFFERS IN OUTCOME** — receipting is real but covers one
seat of several, so "every pack insertion is receipted" is false today.

---

## 9 — Stop reasons · CONFORMS

**Clause.** §9: *"`EngagementChange` — Active, suspended, interrupted, or
closed-for-now engagement; reason optional unless a reason-sensitive attribution
is claimed."* §33: a release may not infer semantic failure from an unsupported
format.

**Command and output** (`proof/check09-stops.txt`):

```
$ sed -n "16,30p" src/deepreason/runtime/stop.py
StopReason = Literal["completed", "converged", "stuck", "budget_exhausted",
    "operator_cancelled", "operational_failure", "provider_unavailable",
    "workload_terminal"]

$ sed -n "296,300p" src/deepreason/runtime/stop.py
    if reason not in StopReason.__args__:
        raise ValueError("stop record has an invalid reason")
```

**Record evidence** — every stop record written by every committed root:

```
stop records read: 137
    94  budget_exhausted
    41  operational_failure
     2  converged
stop reasons OUTSIDE the closed vocabulary (i.e. free text / model prose): 0
```

**Distance verdict: CONFORMS.** The optional appraisal-reason pointer of §9 is
absent, which the clause expressly permits ("reason optional"); it becomes
required only if DeepReason ever claims a reason-sensitive attribution about a
stop, which it does not.

---

## 10 — Alternatives vs. compatible rivals · CONFORMS

**Clause.** §9 `Compare`: *"Alternatives, question and criteria of comparison,
reasons, and preference relation or unresolved result. No winner is mandatory."*
Audit S22: rival contents must be recordable compatibly.

**Command and output** (`proof/check10-rivals.txt`, script
`proof/check10_record.py`):

```
$ python proof/check10_record.py experiments/2026-09-02-live-p-a2-corrected/run
problem                                         n  accepted  refuted  attacked
question-933313a5d9ca6dd86f3052aec6e1f05f      34        24       10        10
conn:1191498e4fe5                              22        21        1         1

  attack edges           : 12
  warrant targets        : 12
  attacked-but-unwarranted targets: 0
```

Twenty-four rivals on one problem, all accepted at once. Every attack edge in
the root traces to a registered warrant; co-presence on a problem creates
nothing. The offline fixture agrees (`proof/check12-hardening.txt`, S22): two
contradictory contents both register `accepted` with zero edges.

**Distance verdict: CONFORMS**, and by the route the check names as also
acceptable — DeepReason has **no exclusivity relation over rivals at all**.
Preference exists only through the pairwise trial, which mints an ordinary
warrant against the loser and is criticizable like any other.

---

## 11 — The DA-1 labelling rule itself · DIFFERS IN OUTCOME

**Clause.** §11.3, in full: an `UNKNOWN` check never becomes `PASS`; an
undecided essential premise prevents its dependent from becoming `in`; an `out`
essential premise makes its dependent `out`.

**The structural difference, stated before the fixtures.** DA-1 reaches ONE
fixed point over attacks and dependencies simultaneously. DeepReason runs TWO
passes in order: `adjudication/grounded.py` labels the attack graph first, then
`adjudication/support.py` walks the dependence DAG. A criticism whose premise is
withdrawn has therefore already landed its attack by the time the support pass
notices. DeepReason also has no readiness value: every registered artifact is
implicitly `PASS`.

**Command and output** (`proof/check11-da1.txt`, script
`proof/check11_da1_vs_harness.py` — each fixture built twice, once as DA-1
applications for the specification's own `reference_kernel.appraise`, once as
harness artifacts through the public API):

```
fixture                            node  DA-1 (§11.3)  DeepReason               verdict
--------------------------------------------------------------------------------------
F1 refuted essential premise       A     in            refuted                  DIFFERS IN OUTCOME
F1 refuted essential premise       C     out           suspended_unsupported    DIFFERS IN OUTCOME
F1 refuted essential premise       D     in            accepted                 same
F1 refuted essential premise       K     out           refuted                  same

F2 undecided essential premise     A     undecided     refuted                  DIFFERS IN OUTCOME
F2 undecided essential premise     C     undecided     suspended_unsupported    differs in name
F2 undecided essential premise     K     undecided     suspended                same
F2 undecided essential premise     M     undecided     suspended                same

F3 reinstatement                   A     in            accepted                 same
F3 reinstatement                   C     out           refuted                  same
F3 reinstatement                   D     in            accepted                 same

F4 unknown readiness, unattacked   A     undecided     accepted                 DIFFERS IN OUTCOME
F4 unknown readiness, unattacked   U     undecided     accepted                 DIFFERS IN OUTCOME
```

The classifier is stated in the script before any fixture runs: `IN` (DA-1
`in` / DeepReason `accepted`), `OUT` (`out` / `refuted`), `NEITHER`
(`undecided` / `suspended` / `suspended_unsupported`). Same class, same label →
`same`; same class, different label → `differs in name`; different class →
`DIFFERS IN OUTCOME`.

Reading the rows:

- **F1** is check 1 in its general form. DA-1 reinstates the target; DeepReason
  leaves it refuted.
- **F2** is sharper than F1 and is not covered by the commissioned defect
  tranche. The criticism's premise is merely *unresolved*, and DeepReason still
  reports the target **refuted** — a definitive elimination resting on an open
  question.
- **F3** is the shared case. Grounded reinstatement agrees with DA-1 exactly.
- **F4** is the readiness gap. DeepReason has no `UNKNOWN`, so an unattacked use
  whose declared check is unavailable labels `accepted`. §11.3's sentence *"An
  `UNKNOWN` check does not become `PASS` because its application is
  unattacked"* has no counterpart.

**Distance verdict: DIFFERS IN OUTCOME** — 5 outcome differences, 1 name
difference, 6 agreements over 13 node labels.

---

## 12 — The Hardening_Audit S-items with a DeepReason analogue

Script `proof/check12_hardening.py`, output `proof/check12-hardening.txt`.

### S05 — admitted material counts although its own test failed · **EXHIBITED**

```
  declared check              : predicate:'impossible-token' in content
  its verdict on this artifact: fail
  registered attacks on it    : []
  adjudicated status          : accepted
  S05 pre-hardening behaviour EXHIBITED: True
```

S05's own words: *"The grounded characteristic function checks attacks, not
whether the body satisfied its declared finite checks."* That is exactly
`adjudication/grounded.py`. An artifact carrying a commitment whose declared
predicate FAILS labels `accepted` until some criticism rule happens to run and
mint a warrant. DeepReason's mitigation is that the rules do run — but the
LABEL never consults the check, so between the two the artifact is a survivor.

### S17 — merge keeps identity and location · **PARTLY EXHIBITED** (see check 6)

Identity survives (content-addressed ids); location and originating role do not.

### S18 — a unique temporal maximum is assumed · **NOT EXHIBITED**

The single label per artifact is computed by one policy, never selected from
competing records by log order — which is the specific defect S18 names. It is
not exhibited because there are no situated appraisals at all (check 7).

### S22 — alternatives vs. compatible rivals · **NOT EXHIBITED**

```
  rival one status : accepted
  rival two status : accepted
  attack edges     : []
```

There is no branch, cut, or exclusivity relation over rivals. Incompatible
content never makes two records incompatible.

**Distance verdict for row 12: DIFFERS IN OUTCOME** — two of the four
pre-hardening behaviours are present.

---

## Conflicts between the specification and an operator law

Reported as rows, per the brief; the specification is not authority here.

| Spec item | Operator law it would touch | Reading |
|---|---|---|
| §11.1 essential premises as a required critic field; the configuration document's R2 "a case with `attack=true` and an empty `discriminator` is a failed call" | **Formalism is an option, never an obligation** (2026-08-08) | A REQUIRED premise or discriminator field penalizes an informal criticism at the wire. The premise channel must be optional-and-unpenalized, exactly as `premise` and the successor question already are. The audit does **not** import the configuration document's §3/§4 rewrites — the operator declined them for the default forms. |
| §11.3 `local_readiness ∈ PASS/FAIL/UNKNOWN`, and §12.1's `undecided` display | **Frozen surface 3** (`invariants.py`, `verification/`) | A fifth status value, or a readiness field feeding the label, changes `verify_root`'s epistemic-check report shape. `adjudication/` itself is not frozen; its OUTPUT SHAPE is. |
| §9 `Appraise` as a record kind | **Frozen surface 2** (`harness.py` event application) | Same shape as the granted 2026-09-04 section-plan contact: registration and well-formedness only. Needs the operator's verbatim grant. |
| §9's requirement that a display report disagreement | **Within mini, criticism overturns nothing** (2026-09-05) | Compatible: mini already generates content whose worth is decided later. An appraisal set is the natural home for mini's criticisms, which change no status by ruling. |
| §12.1 status labels never aliased into a seat's field | **Seats change how content is GENERATED, never what counts as EVIDENCE** | Check 3's leak is a violation of DeepReason's own law before it is a distance from the specification. |

## Precedence gates (audit family, S4)

```
$ git status --porcelain -- experiments/ | grep -v 2026-09-05-audit-ois-1-1-spec-drift
(no output — no committed run root was written)

$ git diff --stat
(no output — no tracked file outside the tranche directory was modified)
```

Every verdict row above cites a file under `proof/`. 12 rows, 12 proof files
plus the baseline.
