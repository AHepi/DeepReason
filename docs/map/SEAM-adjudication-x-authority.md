<!-- DR-SEAM-adjudication-x-authority -->
Verified-at: 27e088cb
Verify: python tools/docs_verify.py
Owns: src/deepreason/authority.py, src/deepreason/adjudication/support.py
Sides: DR-SUB-adjudication, DR-CON-authority

# adjudication x authority

## The agreement

Authority decides whether a judgement may MINT a status-bearing warrant.
Adjudication decides what warrants, once minted, do to the graph. The two
never meet: `adjudication/` imports nothing but `deepreason.ontology`, no
authority symbol reaches it, and `Harness._adjudicate` reads only
artifacts, warrants, commitments and carriage. By the time a warrant
arrives at `build_att`, authority's decision is already baked into the
record — the warrant exists or it does not, and nothing downstream can
tell which policy allowed it.

That indirection looks like a missing feature and is in fact the load-
bearing property of the whole record. **Labels are RECOMPUTED on every
open, never replayed from the log.** So anything the label computation
consults becomes part of what a committed root MEANS — retroactively,
for every root already on disk. Authority, being per-run configuration,
is exactly the kind of thing that must never enter there.

The asymmetry is measurable at both ends, and the two measurements are
this document's reason to exist:

**A policy consulted at LABEL time reinterprets committed evidence.**
Making `final_labels` policy-dependent and reopening `run-f4fa6663`'s
UNCHANGED bytes moves its recorded `REFUTED` count from 1 to 0.
`check: python -W ignore -c "import deepreason.harness as H; from deepreason.harness import Harness; from deepreason.ontology import Status; r='experiments/live_engaged_2026-07-27/run-f4fa6663e5412d64df943a5a22342baf'; base=sum(1 for s in Harness(r,read_only=True).state.status.values() if s==Status.REFUTED); assert base==1, base; orig=H.final_labels; H.final_labels=(lambda o: lambda l,d: {k:(Status.ACCEPTED if v==Status.REFUTED else v) for k,v in o(l,d).items()})(orig); moved=sum(1 for s in Harness(r,read_only=True).state.status.values() if s==Status.REFUTED); H.final_labels=orig; assert moved==0, moved"`

**A policy consulted at MINT time cannot.** Sabotaging
`register_fail_warrant` so that any execution raises, then reopening the
same root, changes nothing — replay never executes `rules/`.
`check: python -W ignore -c "import deepreason.rules.warrants as W; W.register_fail_warrant=lambda *a,**k: (_ for _ in ()).throw(AssertionError('mint executed during replay')); from deepreason.harness import Harness; from deepreason.ontology import Status; r='experiments/live_engaged_2026-07-27/run-f4fa6663e5412d64df943a5a22342baf'; h=Harness(r,read_only=True); assert len(h.state.att)==1, len(h.state.att); assert sum(1 for s in h.state.status.values() if s==Status.REFUTED)==1"`

So the agreement, in one line: **authority may be consulted where a
warrant is minted, and never where a label is computed.**

This document carries no `Sweep:` header, deliberately. A sweep follows
one FIELD across an agreement (`DR-SCHEMA`); here the agreement is the
ABSENCE of traffic between the two sides, so there is no field to
follow and every candidate site a sweep could flag would be a reader.
`SEAM-evaluation-x-ontology` is the recorded precedent for leaving the
header off and saying why in the body rather than shipping a spec that
cries wolf.

## Where it is expressed

| Site | File | Symbol | What it enforces |
|---|---|---|---|
| The label gate | `harness.py` | `_adjudicate` | the sole writer of `state.status`, and the only caller of the label function; reads artifacts, warrants, commitments, carriage — no `Config`, no policy |
| The label function | `adjudication/support.py` | `final_labels` | the only producer of `Status` values in the codebase |
| The authority decision | `authority.py` | `trial_authority_for`, `argumentative_authority_mode` | surface knob → per-call mode, consulted upstream of every mint it governs |
| Mint sites that DO consult it | `rules/crit.py`, `informal/trial.py` | `_resolve_authority`, `_coerce_trial_authority` | the LLM-mediated text paths — the only ones the policy governs |
| Mint sites that deliberately do NOT | `skills/adoption.py`, `measures/hv.py`, `workloads/formal.py`, `informal/audits.py`, `rules/act.py`, `rules/experiment.py` | their `register_fail_warrant` calls | deterministic, execution, formal and audit paths keep their established status-changing behaviour and never consult authority |
| Argumentative mints gated by the master flag directly, not through `authority.py` | `imports.py`, `rules/experiment.py` | `register_epistemic_import_failure`, `relevance_trial` | FIXED 2026-08-10 (S2a/R1): each reads `ADJUDICATION_STATUS_AUTHORITY_ENABLED` inline — not a `workload_profile == "text"` judgement, so not routed through `trial_authority_for`/`argumentative_authority_mode` |
| The workload exemption | `authority.py` | `trial_authority_for`'s `workload_profile` branch | a `code` or `formal` run receives `STATUS` without reading any knob |

**Nothing in `adjudication/` knows authority exists.** Its whole import
surface is `deepreason.ontology` plus itself, read from the AST so a
relative or aliased import cannot slip past.
`check: python -c "import ast,pathlib; d=pathlib.Path('src/deepreason/adjudication'); ps=sorted(d.glob('*.py')); assert len(ps)==4, ps; names=[x for p in ps for n in ast.walk(ast.parse(p.read_text())) for x in ([a.name for a in n.names] if isinstance(n,ast.Import) else ([(n.module or '')] if isinstance(n,ast.ImportFrom) else []))]; assert not any('authority' in x for x in names), names; assert any('deepreason.ontology' in x for x in names)"`

**The gate the rung-7 goal asked for already exists, and is one line.**
One writer of `state.status`, one call to the label function.
`check: python -c "src=open('src/deepreason/harness.py').read(); assert src.count('self.state.status = ')==1, src.count('self.state.status = '); assert src.count('final_labels(')==1, src.count('final_labels('); assert 'def _adjudicate' in src"`

**`_adjudicate` consults no policy**, asserted on its AST rather than on
its text, with a positive anchor so a rename or deletion fails rather
than passes.
`check: python -c "import ast,inspect,textwrap; from deepreason.harness import Harness; t=ast.parse(textwrap.dedent(inspect.getsource(Harness._adjudicate))); names={n.id for n in ast.walk(t) if isinstance(n,ast.Name)}|{n.attr for n in ast.walk(t) if isinstance(n,ast.Attribute)}; assert 'build_att' in names and 'final_labels' in names; assert not any('authorit' in x.lower() or x=='config' for x in names), sorted(names)"`

**Of the eight modules that mint demonstrative warrants, exactly two
consult authority.** The other six are the deterministic and execution
paths, and their silence is the design rather than an oversight. Counts
are claims (`DR-SCHEMA`), and every listed module must really mint, so a
move or rename fails the check instead of quietly shrinking it.
`check: python -c "import pathlib; mods=['skills/adoption.py','measures/hv.py','workloads/formal.py','informal/audits.py','informal/trial.py','rules/act.py','rules/experiment.py','rules/crit.py']; texts={m: pathlib.Path('src/deepreason/'+m).read_text() for m in mods}; missing=[m for m,t in texts.items() if 'register_fail_warrant(' not in t]; assert not missing, missing; consult=sorted(m for m,t in texts.items() if 'deepreason.authority' in t); assert consult==['informal/trial.py','rules/crit.py'], consult"`

**The policy governs text workloads only.** A `code` or `formal` run's
rubric trial gets `STATUS` without consulting a text-authority knob, even
with the knob set the other way and a receipt declared -- but, like the
text branch, only once `JUDGE_SEATS_ENABLED` (Part D's master judge-
dispatch gate, off by default) is on; at the default `False` every
workload gets `OBSERVE_ONLY`.
`check: python -c "from deepreason.authority import AuthoritySurface as S, TrialAuthority as T, trial_authority_for as f; from deepreason.config import Config; c=Config(TEXT_RUBRIC_AUTHORITY='calibrated_status', CALIBRATION_RECEIPT='sha256:x'); assert f(c,'text',S.RUBRIC)==T.OBSERVE_ONLY; assert f(c,'code',S.RUBRIC)==T.OBSERVE_ONLY and f(c,'formal',S.RUBRIC)==T.OBSERVE_ONLY; c2=Config(TEXT_RUBRIC_AUTHORITY='calibrated_status', CALIBRATION_RECEIPT='sha256:x', JUDGE_SEATS_ENABLED=True); assert f(c2,'code',S.RUBRIC)==T.STATUS and f(c2,'formal',S.RUBRIC)==T.STATUS"`

**Two argumentative mint sites now consult the same master flag the text
policy shares, but NOT through `trial_authority_for`/
`argumentative_authority_mode` themselves** (adjudication-judge-seats-
optins tranche, S2a/R1, 2026-08-10 — FIXES the "no gate at all" state
this check used to pin). An import-plan violation and a property-
relevance ruling are not `workload_profile == "text"` judgements — the
two functions above stay scoped to that surface — so each site reads
`config.ADJUDICATION_STATUS_AUTHORITY_ENABLED` directly rather than
routing through `authority.py`. When False, `register_epistemic_import_
failure` mints a scrutiny observation (no warrant, mirrors `crit.py`'s
`observe_only`) and `relevance_trial` dispatches no judge and leaves the
property's `Status` untouched (mechanically-admitted stays mechanically-
admitted; the relevance question is left unadjudicated, not answered
either way) — the same "target status untouched" principle as
`observe_only`, applied without formally being one of its four text
surfaces.
`check: python -c "import inspect; from deepreason import imports; from deepreason.rules import experiment; a=inspect.getsource(imports.register_epistemic_import_failure); b=inspect.getsource(experiment.relevance_trial); assert 'WarrantType.ARGUMENTATIVE' in a and 'WarrantType.ARGUMENTATIVE' in b; assert 'ADJUDICATION_STATUS_AUTHORITY_ENABLED' in a, 'imports still ungated'; assert 'ADJUDICATION_STATUS_AUTHORITY_ENABLED' in b, 'relevance_trial still ungated'; assert 'deepreason.authority' not in a and 'deepreason.authority' not in b, 'these two sites read the flag directly, not through authority.py'" && python -m pytest tests/test_imports.py::test_import_failure_gated_by_adjudication_master_flag tests/test_properties.py::test_relevance_trial_gated_by_adjudication_master_flag -q`

## What is deliberately absent

**There is no policy object, and no single place that answers "may this
judgement change a status".** The decision is assembled per call from six
`Config` knobs across two closed vocabularies that share exactly one word
(`observe_only`), through three entry points. `DR-CON-authority` holds
the full vocabulary breakdown; it is not re-derived here, to avoid a
second driftable copy. The consolidation designed for it is
`experiments/2026-08-04-change-rung7-authority-as-declared-policy/SPEC.md`
(Option D, approved, sub-tranche 7b), and it lands at MINT time for the
reason the two measurements above establish.

**There is no record of WHY a status did not change.** A guard declining,
an authority mode set to `observe_only`, a duplicate verdict skipped and
a critic that simply found nothing all leave `att` identically empty.
That is `DR-SEAM-adjudication-x-rules`'s trap in its authority form, and
it is why the adjudication-blindness detector lives in
`verification/report.py` rather than in either side of this seam.

## How to change it

1. **Read `DR-INV-frozen-surfaces` first.** The governing principle — fix
   readers, so old roots stay valid — is what the label-time measurement
   above enforces concretely.
2. **A new authority mode goes on `Config` and is consulted at a mint
   site.** Never on the manifest (`DR-INV-frozen-surfaces` surface 4:
   every qualification subject digest derives from it), and never in
   `adjudication/`. A new top-level `Config` field is additionally not
   done until `_versioned_source_config_data` has an explicit
   unconditional line for it — that trap has already refuted one
   tranche's first fix.
3. **Never make the label computation depend on anything outside the
   record.** The check above is the instrument; it flips a real committed
   root and will catch the attempt. This is the single most expensive
   mistake available at this seam, because it passes every test written
   against a fresh run and fails only against evidence already on disk.
4. **Gating the two ungated argumentative sites is a real change, not a
   tidy-up.** Their check above pins the current state; a change that
   gates them must UPDATE that check in the same commit, and must decide
   whether an import-plan violation and a relevance ruling are the kind
   of judgement the text policy was written for. `DR-SCHEMA`: never
   delete such a claim, rewrite it to say when it changed.
5. **Do not widen the policy to the deterministic paths without saying
   so out loud.** Six of the eight demonstrative-minting modules are
   exempt by design, and a `code` or `formal` workload bypasses the
   policy entirely. Bringing them in makes a deterministic oracle's
   verdict configurable, which is a much larger claim than "authority is
   declared in one place".

## Traps

- **Reading "route every status change through one narrow gate" as a
  change to the label computation.** It is the natural reading of the
  rung-7 goal and it is the one mistake this document exists to prevent.
  The gate already exists (one writer, one call, checked above); what
  does not exist is a declared policy, and putting one at the label gate
  reinterprets every recorded root. Measured on
  `run-f4fa6663`: `REFUTED` 1 → 0 on unchanged bytes. Evidence:
  `experiments/2026-08-04-change-rung7-authority-as-declared-policy/SPEC.md`
  M5 (the hazard), M6 (the safe placement), M6c (the exposure — 6
  att-bearing roots and 26 recorded `REFUTED` verdicts by the
  git-tracked-`log.jsonl` instrument on 2026-08-04; cite the instrument
  with the number, per `docs/ERRATA.md` E5/E8).
- **Assuming "already gated" means "gated everywhere".** Two
  argumentative mint sites reach a warrant with no authority consulted
  and no supremacy guard. `DR-CON-warrants-and-attacks` records the same
  fact from the warrant side; this seam records it because it is where
  the authority story is incomplete.
- **Assuming the absence of an `authority` import in `adjudication/`
  means the seam is unimportant.** It is the opposite: the absence IS
  the agreement, which is precisely why the coupling metric cannot see
  this pair and why `INDEX.md` lists it without an import count.
- **Looking in `adjudication/` for the reason a target was not
  refuted.** Finding nothing is the expected result, not evidence that
  the boundary is unguarded. Every such reason lives upstream, at the
  mint site, and `DR-SEAM-adjudication-x-rules` holds the guard-by-guard
  version of the same warning.
