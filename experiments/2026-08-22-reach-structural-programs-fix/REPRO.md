# Reproduction

Form: offline unit reproduction (real `Harness`, real `reach_sweep`, real
`formally_backed`, nothing monkeypatched)

Artifact: `experiments/2026-08-22-reach-structural-programs-fix/repro.py`
-> `repro.json`. Exit code is the assertion: 0 iff all three invariants hold.
Run: `python repro.py` from this directory.

The committed rehearsal (`experiments/2026-08-22-live-reach-rich-run/
rehearsal.py`) demonstrates the same mechanism but SIMULATES the fix by
rebinding `_STRUCTURAL_PROGRAMS` in-process for scenarios S8b/S8c. This
reproduction removes that: every check runs against the shipped module
constant, so it shows the defect as a live run meets it and inverts cleanly
once the constant is right.

## Current output (HEAD `0e8e0f6a6`, exit 1)

    VIOLATED  R1 declared structural class == reach's structural set
               declared_minus_reach = ['component_wf', 'generator_wf', 'integration_wf', 'manifest_wf', 'reasoning-envelope-wf']
               reach_minus_declared = []
    VIOLATED  R2 a declared-structural gate never enters reach's qualifying set, so it can neither ground nor veto a hit
               carried = ['hv-floor@2a45b7988522', 'lineage-ref@5adb8c3d4260', 'relation-form@578e42df713e']
               coverage = 1.0
               hits = []
               qualifying = ['reasoning-envelope-wf', 'uhi-energy-balance@r1', 'uhi-nocturnal-release@r1']
               recorded_reach_events = 0
               verdicts = {'reasoning-envelope-wf': 'fail', 'uhi-energy-balance@r1': 'pass', 'uhi-nocturnal-release@r1': 'pass'}
               wf_in_qualifying = True
    VIOLATED  R3 a passing declared-structural gate confers no formally_backed prose immunity
               commitments = ['reasoning-envelope-wf']
               formally_backed = True
               wf_verdict = pass

Confirms diagnosis: yes.

  - **R1** is the drift itself, and its direction is one-way
    (`reach_minus_declared` is empty), which is what identifies it as a stale
    copy rather than a deliberate disagreement.
  - **R2** reproduces `rehearsal.json` S8a verdict-for-verdict — the wf gate
    is IN the qualifying set, it `fail`s on prose, and both subject predicates
    `pass` in the same row — with no rebind anywhere. This is the load-bearing
    reproduction: it shows the well-formedness gate deciding a reach outcome
    that the subject criteria had already settled in the artifact's favour.
  - **R3** is the second consumer, and it is the sharper demonstration of the
    two. The committed corpus measurement
    (`probe_immunity.json`: `backed_only_by_declared_structural` = 0) says no
    committed root's verdict currently rests on this. R3 shows the mechanism
    is nonetheless live and one artifact away: an artifact whose ONLY
    commitment is `program:reasoning-envelope-wf`, passing, is
    `formally_backed` = True today — prose-immune purely for being well
    formed. That is exactly the self-immunisation hole
    `docs/map/CON-warrants-and-attacks.md` says `_STRUCTURAL_PROGRAMS` exists
    to close.

Post-fix expectation: `python repro.py` exits 0 with

    HOLDS  R1 ...  declared_minus_reach = []           reach_minus_declared = []
    HOLDS  R2 ...  qualifying = ['uhi-energy-balance@r1', 'uhi-nocturnal-release@r1']
                   wf_in_qualifying = False   coverage = 0.667
                   hits = [[<artifact>, 'foreign']]    recorded_reach_events = 1
    HOLDS  R3 ...  wf_verdict = pass                   formally_backed = False

Production code untouched in this phase: `git diff --stat src/ tests/` is empty.
