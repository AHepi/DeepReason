# PARKED — found during the design phase, deliberately not done here

Scope contract (`dr-change-orchestrator` §2): a defect found mid-change is
PARKED, not fixed. Each entry is one line of WHAT, then a ready-to-send
prompt — the follow-up should cost the operator a paste, not an authoring
session.

---

## P1 — a run cannot select a different conjecturer form and still qualify

**What.** `ContractVersionPolicyV3.conjecturer_turn_contract`
(`run_manifest.py:674`) already offers two values, but it lives inside
`control_plane_policy`, and `qualification.py::qualification_subject_payload`
(259-263) refuses any manifest whose `control_plane_policy` is not the
repository-owned preset `engaged_control_plane_policy_v3()`. Measured, four
committed manifests, identical verdict: `QUALIFICATION_POLICY_PRESET_MISMATCH`
(`price_form_registry.py`, `price_output.txt`, road C). So the one form knob
the manifest exposes cannot be turned without making the run unqualifiable.

**Why it matters.** This is in tension with two standing operator laws:
"All configurations should be allowed" (2026-08-12) and "seat configuration
is ungated, gates are optional-with-warnings" (2026-08-28) — a configuration
that parses, compiles and then cannot qualify is a gate the configuration
cannot turn on.

```
EXECUTOR WINDOW — DEFECT TRANCHE: the conjecturer form knob is gated by the
qualification preset

Read CLAUDE.md fully, then load deepreason-orchestrator, dr-drive-harness,
dr-ask-the-right-question and dr-explain-to-operator. Start at dr-set-goal.
Base on main at or after 2d84a86cd. Work on your window's assigned branch;
commit and push at every phase boundary.

THE SYMPTOM, from the typed record. RunManifest exposes
ContractVersionPolicyV3.conjecturer_turn_contract with two legal values
("conjecturer.turn.v6", "conjecturer.turn.v7", run_manifest.py:674), but the
field sits inside control_plane_policy, and
qualification.py::qualification_subject_payload lines 259-263 raise
QUALIFICATION_POLICY_PRESET_MISMATCH unless control_plane_policy equals
engaged_control_plane_policy_v3(). Selecting v7 therefore makes the run
unqualifiable.

REPRODUCE FIRST, do not theorise:
  python experiments/2026-09-03-change-conjecturer-pluggable-interface/\
price_form_registry.py
Read the road_C_qualification_refusal field on all four cases.

THE LAWS AT STAKE (CLAUDE.md, Operator design laws): "All configurations
should be allowed" (2026-08-12) -- what used to be a compile-time refusal
becomes a typed disclosure, never a stop; and "seat configuration is
ungated, gates are optional-with-warnings" (2026-08-28). Decide, on the
record, whether this refusal is a defect under those laws or a deliberate
integrity boundary, and say which in GOAL.md as a falsifiable fork before
reading any more code.

FROZEN SURFACES: this touches surfaces 4 (run_manifest.py) and 5
(qualification subjects). Paste tools/blast_radius.py's own
BLAST_RADIUS_RESULT_V1 rows into FIX.md and dispose of each before any
code. DESIGN AND STOP at FIX.md for the operator's grant.

OUT OF SCOPE: the pluggable-interface tranche
(experiments/2026-09-03-change-conjecturer-pluggable-interface/); adding any
new contract id.
```

---

## P2 — the cheap conjecturer form is reachable only after the expensive one fails

**What.** Over 59 committed roots, `conjecturer.turn.v6` reaches semantic
admission 51.5% of the time (454 of 882) while
`conjecturer.atomic-candidate.v1` reaches it 92.7% (382 of 412), on the same
seats and routes (`census_conjecturer_failures.py`, `census_output.txt`).
The W1 census measured the controlled pair a year's-worth tighter — glm-5.2,
same seat, route and problem: 61.9% against 96.8%
(`experiments/2026-08-26-run-anatomy-program/W1-form-census/RESULTS.md` §1).
The atomic form is entered only when the turn form EXHAUSTS its repair
grant, so every run pays the expensive failure first. Repair consumes 21.6%
of all provider spend in the committed record.

**Not a defect on its face** — the decomposition ladder is deliberate. What
is unmeasured is whether starting at the atomic form costs anything the
composite form buys (candidate diversity per call, cross-candidate
consistency). That is an experiment, not a fix.

```
EXECUTOR WINDOW — CHANGE TRANCHE: measure what the composite conjecturer
form buys, against starting at the atomic one

Read CLAUDE.md fully, then load dr-change-orchestrator, dr-drive-harness,
dr-ask-the-right-question and dr-explain-to-operator. Start at
dr-capture-request with THIS prompt as the operator's authority. Base on
main at or after 2d84a86cd.

THE MEASURED PREMISE, from the record, not from theory:
  python experiments/2026-09-03-change-conjecturer-pluggable-interface/\
census_conjecturer_failures.py
  conjecturer.turn.v6            454/882 admitted (51.5%)
  conjecturer.atomic-candidate.v1 382/412 admitted (92.7%)
and the controlled glm-5.2 pair in
experiments/2026-08-26-run-anatomy-program/W1-form-census/RESULTS.md sec 1:
61.9% vs 96.8%, with the atomic form running on the HARDER sample by
construction. The same census records ONE model reversing the effect
(deepseek-v4-flash:0731, 84.6% composite vs 63.6% atomic) -- so the question
is per-model, and the answer must be too.

THE QUESTION: does the composite turn form buy anything the atomic one does
not -- candidate diversity within one call, cross-candidate consistency,
abstention quality -- that justifies paying its 41-point admission gap and
its share of the 21.6% of provider spend that repair consumes?

Tokens are cheap and the agent is not (CLAUDE.md, operator design law
2026-08-08): answer this with live runs, not with machinery. Use the
committed blind-judging and per-problem diversity instruments; pre-register
the comparison before any run.

OUT OF SCOPE: changing which form the controller selects (that is a
configuration question the pluggable-interface tranche owns); adding any new
contract id; anything touching frozen surfaces.
```

---

## P3 — two seam documents the map does not have, and this work sits on both

**What.** `docs/map/INDEX.md`'s seam matrix lists `llm x model-profiles` and
`model-profiles x scheduler` as "not yet written", and
`CON-packs-and-token-economy.md` declares
`packs-and-token-economy x rules` undocumented. The form's per-model
selection sits on the first; the nine brief sections computed in
`rules/conj.py` rather than in the renderer (FEASIBILITY.md §2) sit on the
third. Per `dr-drive-harness` §4, a missing id is a finding rather than a
blocker — recorded here, and scoped into this tranche's own CHECKLIST.md
rather than deferred, for the seam the build actually crosses.

**Disposition.** `packs-and-token-economy x rules` is written by THIS
tranche's build phase (it is the seam road A crosses). `llm x
model-profiles` is only crossed if C1's per-model form selection ships, and
is written by that step. `model-profiles x scheduler` is untouched by this
work and stays parked.

```
EXECUTOR WINDOW — MAP TRANCHE: write SEAM-model-profiles-x-scheduler.md

Read CLAUDE.md fully, then docs/map/SCHEMA.md before writing a line, then
docs/map/INDEX.md and CON-model-profiles.md. Base on main.

WHAT: docs/map/INDEX.md's seam matrix lists model-profiles x scheduler as
"not yet written". CON-model-profiles.md says the concept spans
scheduler/scheduler.py, "which stamps the installed set into the run's
record" -- that stamping IS the seam and nothing describes it.

The document must carry a `check:` shell command at column 0 for every
load-bearing claim, each of which must exit 0 and each of which must be able
to FAIL (python tools/docs_verify.py --audit refuses a check that cannot).
Run python tools/docs_verify.py in FULL mode before committing.

OUT OF SCOPE: any src/ change; the other two undocumented seams.
```

---

## P4 — `render_batch_crit_pack` is a third renderer the shell never reaches

**What.** `llm/packs.py::render_batch_crit_pack` (line 972) renders a
batched criticism call under its own contract (`batch-critic.v2`) with its
own section set. Amendment 2's build converts `render_conj_pack` and
`render_crit_pack` into layout walks and leaves this one a hardcoded
renderer, so one of the three brief renderers in the tree is still a code
edit away from every change.

**Why it is parked and not done.** The batch renderer's sections are keyed
to a batch of targets rather than one, so its layout entries would need a
per-target repetition construct the section-plugin protocol does not have
(`SPEC.md` §2 `S1.1`: one `render` call, one section). That is a protocol
extension, not an extraction, and extending a protocol inside the tranche
that first ships it is how a protocol acquires a feature nobody has used.

```
EXECUTOR WINDOW — CHANGE TRANCHE: bring the batch criticism renderer onto
the seat shell

Read CLAUDE.md fully, including the seat-is-a-shell law (2026-09-03). Then
load dr-change-orchestrator, dr-drive-harness, dr-ask-the-right-question and
pinker-write-for-readers. Start at dr-capture-request with THIS prompt as
the authority. Base on main at or after the merge of
claude/conjecturer-pluggable-interface-7v3es6.

WHAT EXISTS. That branch made llm/packs.py::render_conj_pack and
render_crit_pack walks over a registered SeatPackLayoutV1 of seeded dr.*
section plugins, with SeatShellV1 pairing a layout, a form and a role-prompt
template per seat. render_batch_crit_pack (packs.py, the batch-critic.v2
contract) was left out: its sections repeat per target, and one plugin
render call produces one section.

THE QUESTION TO DECIDE FIRST, in SPEC.md, before code: does the
section-plugin protocol gain a repetition construct (a plugin returning a
tuple of SectionRenderV1), or does the batch renderer compose N single-target
plugin renders in the walk? Price both against the byte-identical-default
acceptance test, which applies here exactly as it did there: capture a golden
for render_batch_crit_pack from the base commit BEFORE any refactor, and if
it cannot pass, the refactor is wrong -- never update the fixture.

FROZEN SURFACES: forecast NO CONTACT, same as the parent tranche. Paste
tools/blast_radius.py's own verdict into SPEC.md and hold the parent's three
decisions: selection by argument/env never Config never the manifest, no new
contract id, no new verify_root check.

OUT OF SCOPE: the judge, defender, variator and synthesizer seats (P5); any
second conjecturer or criticism KIND (P6).
```

---

## P5 — four seats still have hardcoded briefs

**What.** The judge, defender, variator and synthesizer seats dispatch
through `wire_contract_for` with their own renderers and role-prompt
templates. Amendment 2 covers the conjecturer and the critic; these four are
untouched, so the seat-is-a-shell law holds for two seats out of six.

**Why it is parked.** The operator's amendment named one swap — the
conjecturer's shell in the critic's place — and the two-seat build is what
makes that swap demonstrable. Extending to four more seats in the same
tranche would widen a change already at ~1500 lines of `src/`, and the
judge seat in particular sits under a live operator caution
(CLAUDE.md's amended judge law) that deserves its own reading.

```
EXECUTOR WINDOW — CHANGE TRANCHE: bring the remaining four seats onto the
seat shell

Read CLAUDE.md fully, including the seat-is-a-shell law (2026-09-03) and the
AMENDED judge law (2026-08-28) -- the judge seat is the one with measured
evidence attached, and any design touching it consults that evidence first.
Then load dr-change-orchestrator, dr-drive-harness,
dr-ask-the-right-question and pinker-write-for-readers. Start at
dr-capture-request. Base on main at or after the merge of
claude/conjecturer-pluggable-interface-7v3es6.

WHAT: the judge, defender, variator and synthesizer seats each have a
hardcoded brief renderer and a module-literal role-prompt template. Bring
each onto SeatPackLayoutV1 + SeatShellV1 exactly as that branch did for the
conjecturer and the critic: seeded dr.* plugins per section, a
seat-pack.<seat>.legacy-v0 layout, a seat.<seat>.legacy-v0 shell, and a
byte-identical-default golden per seat captured from the base commit BEFORE
any refactor. If a golden cannot pass, the refactor is wrong -- STOP, never
update the fixture.

BLINDING CONSTRAINT for the judge seat: docs/RESEARCH_JUDGE_BLINDING_
2026-08-22.md measured that provenance exposure carries the bias and that a
present-but-blank slot is worse than a filled one, so a judge layout must
OMIT provenance sections entirely rather than render them empty. shell_id and
layout_id are provenance for this purpose.

OUT OF SCOPE: the batch criticism renderer (P4); any second conjecturer or
criticism KIND (P6); any new contract id.
```

---

## P6 — the second conjecturer kind and the second criticism kind

**What.** The operator's Amendment 2 states future intent twice: "conjecturers
will need to be split in two" (`R22`) and "criticism will need two different
types" (`R23`). Neither says WHAT the two kinds are, and the amendment's own
framing — "I'm thinking in the future that..." — is intent, not a request.

**Disposition.** `SeatShellV1` is built so that each of these is a THIRD
registered pairing rather than a code edit; that is the whole reason the
registry exists (`SPEC.md` §17.4). Nothing is built for them here, and
nothing should be until the operator says what the two kinds are — a
registry entry guessed at is a shape that will have to be un-shipped.

```
EXECUTOR WINDOW — DESIGN TRANCHE: what are the two conjecturer kinds and the
two criticism kinds?

Read CLAUDE.md fully, including the seat-is-a-shell law (2026-09-03). Then
load dr-change-orchestrator, dr-drive-harness, dr-ask-the-right-question and
pinker-write-for-readers. Start at dr-capture-request. Base on main at or
after the merge of claude/conjecturer-pluggable-interface-7v3es6.

THIS TRANCHE NEEDS AN OPERATOR ANSWER BEFORE IT NEEDS A DESIGN. The operator
said, verbatim (2026-09-03): "I'm thinking in the future that conjecturers
will need to be split in two and criticism will need two different types."
They did not say what the two are. Do not guess: ask ONE batched question,
with the record's own evidence attached, and stop.

WHAT TO ATTACH TO THE QUESTION, because it makes the answer cheaper. The
record already measures two conjecturer FORMS behaving very differently:
conjecturer.turn.v6 admits at 51.5% and conjecturer.atomic-candidate.v1 at
92.7% over 59 committed roots (experiments/2026-09-03-change-conjecturer-
pluggable-interface/census_conjecturer_failures.py), and the atomic form is
reachable only after the composite one exhausts its repair grant (PARKED.md
P2). And criticism already has two structurally different sources: the
argumentative critic and the criticism-source socket. So the operator may be
naming a split the tree half-has already, or a new one.

WHAT NOT TO DO: register a SeatShellV1 for a kind nobody has defined. The
registry exists so this costs a registration when the answer arrives; a
guessed entry costs an un-shipping.

OUT OF SCOPE: everything in P4 and P5; any new contract id; any frozen
surface.
```

---

## P7 — a model profile that names a SHELL, not a form

**What.** `SPEC.md` S9.1 proposed an optional `preferred_conjecturer_form` on
the model-profile document, so a model could name the form it does best with.
It is NOT shipped, and the reason is a conflict the build surfaced rather than
a shortage of time: the SEAT SHELL already names the form
(`SeatShellV1.form_id`). A profile naming a form directly would create a
second place that decides the same thing, which is exactly the disagreement
the registry exists to prevent — and the resolution order would then have to
arbitrate between a shell that says one form and a profile that says another.

**Disposition.** Per-model preference belongs one level up: a model profile
naming a SHELL. That composes (the shell still pairs a layout, a form and a
wording) and it needs no arbitration. It also crosses the `llm x
model-profiles` seam, which `docs/map/INDEX.md` still lists as not yet
written, so the seam document is written by that tranche rather than this one.

```
EXECUTOR WINDOW — CHANGE TRANCHE: let a model profile name the seat shell it
does best with

Read CLAUDE.md fully, including the seat-is-a-shell law (2026-09-03). Then
load dr-change-orchestrator, dr-drive-harness, dr-ask-the-right-question and
pinker-write-for-readers. Start at dr-capture-request. Base on main at or
after the merge of claude/conjecturer-pluggable-interface-7v3es6.

WHAT EXISTS. That branch shipped SeatShellV1(seat_id, layout_id, form_id,
role_prompt_template_id) with a registry and resolution: argument ->
DEEPREASON_SEAT_SHELL -> the seat's default. Two shells ship, reproducing
today's conjecturer and today's critic.

WHAT TO ADD: an OPTIONAL preferred_shell on the model-profile document
(docs/map/CON-model-profiles.md; the operator's own agent.md in their home
directory), and a resolution step between the environment and the seat
default. Optional, and its absence means nothing -- that concept's own stance
is that the harness "holds no per-model opinion of its own" and "says so
rather than guessing". Selecting one emits a typed NOTICE, never a refusal
(the ungated-seats law, 2026-08-28).

DO NOT put a form id on the profile. The shell already names the form, and two
places naming it is the disagreement the registry exists to prevent -- that is
why the parent tranche parked this instead of shipping SPEC S9.1 as written.

MAP: write docs/map/SEAM-llm-x-model-profiles.md in the SAME commit;
docs/map/INDEX.md lists that seam as not yet written and this is the work that
crosses it.

FROZEN SURFACES: forecast NO CONTACT. Hold the parent's four decisions:
selection by argument/env never Config never the manifest; no new contract id;
no new verify_root check; and wire_contract_for keeps returning the same
contract_id for every input it resolves today (its answers are folded into a
replay authority set at invariants.py:1233 and a qualification subject at
run_manifest.py:2074 -- tests/test_wire_contract_id_map.py pins them).

OUT OF SCOPE: everything in P4, P5 and P6.
```
