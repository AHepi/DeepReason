# Verify: the goal's two halves, against GOAL.md's own criteria

Outcome: **PASS** on both halves, offline, with no live call.

## The criteria, one by one

**(1) `repro_managed_override.py` inverts.** Before: exit 1, `neither carried
nor disclosed: 7 of 7`, geometry `hashing (hashing-128)` with an
`embedder-unconfigured` record. After: exit 0, `neither carried nor disclosed:
0 of 7`, `compiled scratch policy: backend='neural'
model='nomic-ai/nomic-embed-text-v1.5'`, `Measure kinds on the log:
['embedder']`, and `deepreason results would print: embedder: neural
(nomic-ai/nomic-embed-text-v1.5)`. Both outputs are committed
(`REPRO_OUTPUT.txt`, `REPRO_OUTPUT_POSTFIX.txt`). The script's control
observation — the same rebuilt configuration with the field restored by hand —
printed neural before AND after, which is what says the fix moved the
configuration rather than the container.

**(2) Seven cases, one per host-owned value.**
`tests/test_managed_path_host_owned_values.py` — 23 tests, 0 failed. Every one
of `engine_profile`, `model_profile`, `scratchpad`, `bridge`,
`EMBEDDER_MODEL`, `CHANNELS_DISABLED` and `roles` is either carried into the
run or named by exactly one typed notice. Mutation-proven against four
separate reversions of the fix, each run and recorded:

    mutation                              new-file result
    embedder carriage reverted            4 failed, 19 passed
    disclosure suppressed                18 failed,  5 passed
    notice made to carry a value         12 failed, 11 passed
    notices never reach the manifest     18 failed,  5 passed
    (unmutated)                           0 failed, 23 passed

**(3) The qualification subject digest holds still where it must.** One
parametrised case per disclosed value asserts the digest is byte-identical to
the default managed subject's while the notice is present — six cases, all
green, and all six go red when the disclosure is suppressed. The one digest
that DOES move has its own named test saying so: a configuration that states
an embedder compiles a different scratch policy, so it is a different subject
and that home owes one battery. That is the configuration taking effect, not a
code change altering what enters the digest.

**(4) Full gate.** `pytest tests/ -q -n 4` — **5215 passed, 0 failed, 6
skipped** in 1333 s, exit 0 (`probe/full_gate.out`). Run on an idle box, alone:
an earlier attempt was killed at 71% when the watcher holding it timed out, and
two before that were starved by running `docs_verify` concurrently on a 4-CPU
container — which `docs/AUDIT_BASELINES.md` and `dr-drive-harness` §5b both
warn against and which this window did anyway before correcting it.

**The map's own runner: `python tools/docs_verify.py` — 9 failed, and none of
them is this tranche's.** Full output at `probe/docs_verify.out`. The
disposition, against `docs/AUDIT_BASELINES.md`'s failure LIST, which is what a
delta is measured against rather than the total:

- SIX match the recorded baseline exactly: `SEAM-llm-x-rules.md`'s unparseable
  check (a lost closing backtick, parked P3); `INV-frozen-surfaces.md`'s
  `transport_failure` census (rotted claim, parked P-D3 — recorded at `:181`,
  now at `:206`, same check text); the judge-canary row, which does
  `git show origin/claude/deepreason-p-s1-commitments-wowcib:…` and dies with
  exit 128 on a container cloned for another branch; and the three
  `CON-run-identity.md` git-history rows, which need `git fetch --unshallow`
  (`git cat-file -t 1637e808` returns "Not a valid object name" here). The
  baseline's expected total on this container is 5 or 6.
- THREE are a DELTA from that list, and the tranche base carries all three.
  Measured in a worktree at the base commit `de4d7abd4`, not argued:
  `CON-successor-questions.md:305` and `SEAM-scratch-x-workflow.md:51` both
  assert a file census `-eq 50` and both read **51 at the base and 51 at
  HEAD** — identical. Neither of this tranche's two changed files is in that
  set (`preparation.py` contains "scratch" but not "workflow";
  `stop_report.py` contains neither), and the commit adds no file under
  `src/deepreason`, so it cannot have contributed a row.
  `INV-frozen-surfaces.md:1414` runs `record_claims.py` against
  `experiments/2026-09-06-change-writers-room-organiser-testing/runs/home-r/runs/run-36d9a22c…`,
  which does not exist in this checkout — the same environment class as the
  judge-canary row, reported as a JSON decode error because the tool got no
  output to parse.

Reported, not fixed: a pre-existing failure this tranche did not cause is not
this tranche's to repair (`dr-implement-fix`'s own rule). The three delta rows
are worth someone's attention — the two `-eq 50` census checks have rotted by
one file since the 2026-08-30 re-baselining — and they are parked with a
ready-to-send prompt at `PARKED.md` P7.

None of the three documents this tranche edited — `CON-configuration-stages.md`,
`CON-seats.md`, `SUB-llm.md` — appears anywhere in the failure list, and both
new checks pass when run directly.

## Frozen surfaces: measured CLEAR, not asserted

`tools/blast_radius.py` on each change site returns
`frozen_surface_verdict: CLEAR` — "This change touches none of the five frozen
surfaces" — for `src/deepreason/preparation.py` and
`src/deepreason/application/stop_report.py` alike (`probe/blast_radius.out`).
No line of `run_manifest.py` or `qualification.py` moved, no notice code was
added, no schema, validator, model or record format was touched.

`tools/diff_budget.py --ceiling 150 --paths src/deepreason` returns
`total_insertions: 121, verdict: WITHIN`. It returned `176, EXCEEDED` on the
first implementation; FIX.md Amendment 1 records the refusal and the smaller
shape that replaced it, which is also the more correct one.

## What this changes the reading of, in the committed record

**Every managed root's embedding-distance reading is on the hashing scale, and
stays there.** `probe/census.out`: 63 of 63 committed managed roots compiled
`deterministic_hashing`. Nothing in this tranche retro-fits them and nothing
may — a committed root's contents are never edited. What changes is what a
reader may conclude going forward: before this fix, a managed root's hashing
geometry was consistent with an operator having configured the neural scale
and been silently overruled; after it, a managed root is on hashing because
its configuration said so or said nothing, and if a stated value was taken the
manifest names it. The five brief-variation arms
(`experiments/2026-09-04-experiment-brief-variation-step1/`) are the roots the
tranche brief names, and their own RESULTS.md §5 already states two things
that bound the damage: the fallback was held CONSTANT across all five arms
rather than changed mid-experiment, and the secondary M1/M2/M3 diversity
measures were never computed at all. Their primary measure and decision rule
are blind-judged, not embedding-based, so the between-arm comparison those
runs were built to make is untouched. The noise floor is the binding limit
there, not the scale: `d_noise = 1.312 of 15` exceeds every treatment effect
that tranche measured.

**The demotion this does NOT re-argue.** The standing of every hash-based
novelty number in this repository was settled by the capability audit at
`experiments/2026-09-08-audit-llm-capabilities/AUDIT_REPORT.md` §6.4, on the
project's own pre-registered E0.1 recalibration: all four predictions refuted,
"what hashing scored as variation is near-duplication at neural scale", every
novelty level and late/early ratio demoted to unverified, and the gate-block
counts and the 4.3x cost figure explicitly NOT demoted. That section is the
authority; this tranche adds nothing to it and takes nothing away. What it
does add is a road: E2.3, the experiment that section records as gating any
repetition of the basin claim and as never having run, needs a managed run
that can measure on the neural scale. Until 2026-09-10 no managed run could.
That is a precondition removed, not a claim restored — and re-running the
demoted measurements is a new tranche with its own pre-registration, not a
consequence of this one.

## Residue — what remains unproven

- **Four of the six stay unreachable from a managed configuration.**
  `engine_profile`, `scratchpad`, `bridge` and `CHANNELS_DISABLED` are now
  disclosed and still not carried. `roles` and `model_profile` should stay
  host-owned — they bind the endpoint and the credential — but the other four
  have no such argument, and whether the managed preset should be a starting
  point the operator refines is the operator's call (PARKED.md P5).
- **No live run.** Every measurement here is offline against the deterministic
  stub or the committed record. That a live `deepreason reason` with a
  neural-naming configuration stamps the neural fingerprint follows from the
  same code path the offline proof exercises end to end, but it has not been
  observed live, and this document does not claim it has.
- **The weights are still a container property.** A managed run that names a
  model on a machine whose fastembed cache is cold records `embedder-fallback`
  and measures on hashing. That is correct behaviour and typed, and it means
  "the configuration names neural" and "the run measured neural" remain two
  different facts a reader must check separately.
- **`config.apply_overrides` still reports every field as explicitly set.**
  The fix reads `model_fields_set`, and that function destroys it. It has no
  caller in `src/`, so nothing today feeds it; a future `--set` road would
  make this a live defect (PARKED.md P4).
