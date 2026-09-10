# Parked — found during this tranche, not fixed here

The change workflow's rule: a defect found mid-change is PARKED, never fixed.
Each entry is one line of WHAT plus a ready-to-send prompt, so the follow-up
costs the operator a paste rather than an authoring session.

---

## P1 — the solo road the 2026-08-09 law requires does not reach a run

**What.** `ARGUMENTATIVE_AUTHORITY=single_family_trial` exists in `Config` and
in `rules/crit.py::_TRIAL_MODES`, and the cross-school judge substitute exists
in `llm/adapter.py`, but no launchable configuration can complete the trial:
`build_adapter` never populates `school_judge_bindings` (no production caller
at all), the manifest validators refuse a `role="judge"` school binding at
freeze time, and `llm/firewall.py::resolve_school_route` refuses it again at
run time. `docs/map/CON-schools.md` already records the mode as "parked as dead
weight, not removed". The operator's law of 2026-08-09 requires that "designs
gated on multi-family judge ensembles need a solo-compatible road"; today that
road is declared and unreachable.

**Ready-to-send prompt.**

```
Route through dr-change-orchestrator (dr-capture-request first). One goal:
make the solo-model criticism-authority road the operator's 2026-08-09 law
requires actually reach a run, or retire the declaration that says it exists.

Evidence, all read-only:
- experiments/2026-09-09-change-d8-criticism-experiment/SPEC.md M6 — the three
  gates that refuse it, each cited to a committed check or map Trap.
- docs/map/CON-schools.md Traps ("single_family_trial cannot complete a
  trial"; "Mistaking require_cross_school_judge_ensemble for the live
  guarantee") and its line-151 check, which PINS the current isolation and is
  expected to go red if the road is wired.
- src/deepreason/llm/adapter.py:270,295,702-706,1928-1944 — the parameter and
  the one production construction site that never passes it.
- docs/map/CON-schools.md:140-152 — the manifest validators
  (V4_SCHOOL_ROLE_UNSUPPORTED) and the runtime resolver
  (SCHOOL_ROUTE_ROLE_UNSUPPORTED).

Frozen-surface reading FIRST: the validator half lives in
src/deepreason/run_manifest.py, which is frozen surface 4. Run
tools/blast_radius.py on every declared target and paste its computed list; a
CONTACT verdict stops at SPEC.md for the operator's words. The adapter half
alone already computes CONTACT (frozen-adjacent route_fingerprint) plus one
UNKNOWN reachability entry.

Two roads to price, and the tranche must price BOTH before choosing: (a) wire
the cross-school judge substitute end to end, accepting frozen-surface-4
contact and the two map checks that must be rewritten; (b) retire the
declaration — remove single_family_trial from Config's Literal and from
_TRIAL_MODES, delete the adapter's dead parameter, and record in
docs/ERRATA.md that the 2026-08-09 law's solo road is served by a cross-family
judge ensemble on the generation-seat-uniform configuration instead. Road (b)
is smaller and may be the honest one; the operator decides, because road (b)
narrows what the law's own words asked for.

End state: either the road runs and a test proves an argumentative warrant
minted on a one-model generation configuration, or the declaration is gone and
ERRATA says why. Nothing in between.
```

---

## P2 — CLAUDE.md names a provider model no committed launch has used since 2026-08

**What.** CLAUDE.md's header says DeepReason drives "currently glm-5.2 on
Ollama Cloud". Every `--model` flag in every committed launch under
`experiments/2026-08-3*/` and `experiments/2026-09-*/` names `qwen3.5:397b`
(11 of 11). `PREREG_D8.md §0` already noticed the same conflict and resolved it
in favour of the newer launches, so the header has been known stale since
2026-09-06 and is still read first by every session.

**Ready-to-send prompt.**

```
Route through dr-change-orchestrator. One goal: CLAUDE.md's provider-model
sentence tells a new session the truth.

Evidence: grep -rho "--model [a-z0-9.:_-]*" experiments/2026-08-3*/
experiments/2026-09-*/ | sort | uniq -c  ->  11 --model qwen3.5:397b, and
experiments/2026-09-05-change-mini-isolation-programme/PREREG_D8.md §0, which
records the conflict and chose qwen3.5:397b on the grounds that the newest
committed launches and the judging protocol both use it.

Smallest change: the header sentence, plus a docs/ERRATA.md entry saying which
tranches were launched under which model, so a reader of an older RESULTS.md is
not misled in the other direction. Do NOT sweep every historical mention —
those are accurate about their own runs. One commit. No gate is owed (no file
under tests/ changes); run python tools/docs_verify.py if any map document
moves, which it should not.
```

---

## P3 — `.claude/skills/README.md` does not exist

**What.** This window's opening brief instructed it to read
`.claude/skills/README.md`. There is no such file: `.claude/skills/` holds 26
skill directories and no index. Every skill's own SKILL.md exists and
`dr-drive-harness` §6 carries the routing index, so nothing was blocked — but a
brief written for a fresh window pointed at a file that is not there, and the
next brief will point at it again.

**Ready-to-send prompt.**

```
Route through dr-change-orchestrator. One goal: decide whether
.claude/skills/README.md should exist, and either write it or stop pointing
briefs at it.

Evidence: ls .claude/skills/ -> 26 directories, no README.md. The routing
content a README would carry already exists in two places: CLAUDE.md's "Which
workflow to use" and .claude/skills/dr-drive-harness/SKILL.md §6.

Load the authoring-skills skill first — its rule against a document that only
restates another document applies directly here, and the honest outcome may be
road (b). Two roads: (a) write a thin index that says only what the other two
do not (which skills exist, which are entry points, which are dimensions of an
orchestrator) and nothing they already say; (b) write nothing, and correct the
executor-brief template that names it. Recommend (b) unless a measurement
shows a window actually lost time for want of the index.
```

---

## Not parked here, because another tranche already owns them

- The organiser tranche's **P8** (a budget denial typed `operational_failure`
  instead of `budget_exhausted`, against the operator's 2026-08-29 law) and
  **P9** (three `attempt-validity` violations appearing over log bytes a
  continuation never touched) —
  `experiments/2026-09-06-change-writers-room-organiser-testing/PARKED.md`.
  Both bear directly on this tranche's own risk: eight harness runs each have
  to reach a clean terminal AND replay clean to be judgeable at all, and P9 is
  a recorded case of a run that did the first and failed the second. Recorded
  here as an inherited risk, not re-parked.
- The discharge channel's **E56** gap — no check anywhere for a configuration
  file naming a preset reaching a scheduler through the real
  `start_manifest_run` — `experiments/2026-08-26-pc2-rematch/PARKED.md` F-A.
- The `pyproject.toml` dependency-declaration gap (`pytest-xdist`,
  `jsonschema`) — `experiments/2026-08-30-change-execution-safety-parks/PARKED.md`
  S5.

---

## P4 — the disclosure gate matches comment prose, and says CONTACT

**What.** `tools/blast_radius.py` resolves declared symbols by grep across
`src/`, so a symbol whose name is a common English word matches occurrences
inside COMMENTS, DOCSTRINGS and STRING LITERALS and is reported as a
frozen-surface contact. Measured four times in six steps of this tranche
(`table`, `measure`, `render`, `question`); for `question` the matched lines
are `src/deepreason/invariants.py:870,872` (comments), `:889` (an error
message) and `src/deepreason/run_manifest.py:2504,2509` (comments). The tool
labels every hit "grep-based; not proof of semantic contact", so the behaviour
is disclosed — but a checkpoint whose rule is "any unnamed contact is a STOP"
converts a disclosed imprecision into a stop that must be argued past, which is
the shape that erodes a gate people are supposed to obey.

**Ready-to-send prompt.**

```
Route through dr-change-orchestrator. One goal: blast_radius.py's symbol
matching stops reporting comment and string-literal occurrences as
frozen-surface contacts, without becoming less strict about real ones.

Evidence: experiments/2026-09-09-change-d8-criticism-experiment/SPEC.md
Amendment 3 carries the four measured instances and the matched line numbers.
The tool's own detail string already says "grep-based; not proof of semantic
contact".

Smallest change to price first: resolve symbols with ast.parse over each
source file and match only NAME-BEARING nodes (definitions, references,
attribute access), falling back to the current grep when a file does not
parse -- so the tool never becomes blind on a file it cannot read. Keep the
detail string honest about which mode produced each hit.

Frozen-surface reading first: blast_radius.py is an instrument, not a surface,
but it READS the surface list, so run the tool on itself and paste the result.
Mutation-prove the new matcher: plant a real reference to a frozen symbol in a
test fixture and show it is still reported, then plant the same word in a
comment and show it is not. A change that only silences the false positives,
without a test proving the true positives survive, is worse than the defect.
```

---

## P5 — eight map checks fail on `main`, and one of them is only expensive

**What.** `python tools/docs_verify.py` reports 8 failures on `origin/main`,
independent of any branch. Proved pre-existing by re-running each at
`origin/main` in a worktree (`VALIDATION.md` § Map): `SEAM-llm-x-rules.md:54`
(a `check:` opener that never closes, so the tool cannot parse it),
`CON-run-identity.md:211/213/215` (git-history queries about a 2026-07 root's
retirement chain), `INV-frozen-surfaces.md:206` (expects zero committed
`transport_failure` provider-attempt records; four tranches carry them),
`INV-frozen-surfaces.md:1000` (the judge-canary compile-gap price script),
`INV-frozen-surfaces.md:1365` (a `record_claims` assertion over the organiser
tranche's root), and `CON-run-identity.md:313`, which TIMES OUT after 300 s and
whose own diagnostic says "this check is too expensive; narrow it to the claim
it actually tests".

Two different kinds are mixed here and should not be fixed as one batch: a
check that cannot PARSE and a check that TIMES OUT are faults in the
instrument's inputs, while the six that exit non-zero are claims about the tree
that may have genuinely stopped being true — which is exactly what the map is
for, and means the map is currently telling the truth about being out of date.

**Ready-to-send prompt.**

```
Route through dr-audit-orchestrator (docs-drift dimension), NOT the change
family: this is a census of what has rotted, and the fixes are separate
tranches afterwards.

One goal: docs_verify reports 0 failed on main, or every remaining failure is a
recorded, dated decision.

Evidence: experiments/2026-09-09-change-d8-criticism-experiment/VALIDATION.md
§ Map carries all eight with their line numbers and the origin/main re-run that
proves each pre-dates that branch.

Triage into three kinds before fixing anything, because they need different
remedies and lumping them produces one commit nobody can review:
(a) SEAM-llm-x-rules.md:54 — an unterminated check opener. The tool cannot
    parse it, so the claim it was written to guard is CURRENTLY UNGUARDED and
    has been for as long as it has been malformed. Fix the syntax, then run the
    check and find out whether the claim is even still true.
(b) CON-run-identity.md:313 — a 300s timeout. Its own diagnostic names the
    remedy: narrow it to the claim it actually tests. Do not raise the timeout;
    an expensive check that nobody can afford to run is a check that does not
    run.
(c) the six that exit non-zero — for each, decide whether the DOCUMENT is now
    wrong or the TREE is. INV-frozen-surfaces.md:206 is the interesting one: it
    asserts no committed root carries a transport_failure provider-attempt
    record, and four tranches now do. Either that invariant was abandoned
    deliberately and the document should say so, or those roots are evidence of
    something. Read the tranches before rewriting the check.

Do NOT weaken a check to make it pass. A check rewritten until it is green is
the failure mode docs_verify exists to prevent, and docs_verify --audit is the
instrument that catches it.
```
