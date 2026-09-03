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
