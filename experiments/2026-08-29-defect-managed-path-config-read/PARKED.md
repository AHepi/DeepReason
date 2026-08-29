# PARKED — found while diagnosing P14, deliberately not fixed here

One tranche, one goal. Everything below is a ready-to-send prompt for a future
runner. Numbering continues `experiments/2026-08-28-defect-manifest-config-disclosure/PARKED.md`,
which ends at P16. Numbering may collide at merge with parallel windows; mint
from the tail and note it.

---

## P17 — `docs/map/INDEX.md` routes to none of eight existing map documents

**What.** `INDEX.md` declares itself the entry point ("This routes"), and eight
committed map documents appear in none of its tables: `SUB-application.md`,
`SUB-amendment.md`, `SUB-periphery.md`, `CON-problem-layer-lifecycle.md`,
`INV-signal-contract.md`, `REC-add-signal.md`, `REC-revise-allocation-policy.md`,
`SEAM-schools-x-scheduler.md`. A document the entry point does not route to is a
document the next reader does not find; the map preflight that CLAUDE.md
requires cannot reach it. Two of the eight are load-bearing for work already
running: `SUB-application.md` owns the `cli/main.py` dispatch rows, and
`INV-signal-contract.md` is the invariant document the 2026-08-14 signal-registry
law says governs its own change protocol.

Not fixed here: `INDEX.md` is outside this lane's file cone and other windows
are editing it concurrently.

**Ready-to-send prompt:**

```
Route: deepreason-orchestrator (defect — a documented guarantee, "INDEX.md
routes", is contradicted by the tree). Small and self-contained.

Goal, one sentence: make docs/map/INDEX.md route to every committed map
document, so the map preflight CLAUDE.md requires can reach all of them.

Evidence, re-runnable:
  for d in SUB-application SUB-amendment SUB-periphery \
           CON-problem-layer-lifecycle INV-signal-contract REC-add-signal \
           REC-revise-allocation-policy SEAM-schools-x-scheduler; do \
    grep -q "$d" docs/map/INDEX.md || echo "UNROUTED: $d"; done
  -> eight lines today, zero when fixed

Place each in the table its kind belongs to (subsystem / concept / invariant
and recipe / seam matrix), with the one-line "Covers" column the existing rows
carry. SEAM-schools-x-scheduler.md needs a coupling row; measure it the way the
matrix says it is measured rather than guessing, and if the pair carries no
measurable import traffic say so in the row, as the last ten rows already do.

Add a check to INDEX.md that would FAIL if a ninth document went unrouted --
the generic form, not the eight names -- and confirm
`python tools/docs_verify.py --audit` accepts it. Single-line check form only.

End state: docs_verify at its stated baseline, the new check demonstrated RED
by mutation (add a throwaway map document, watch it fail, remove it), map moved
in the same commit.
```

---

## P18 — the managed path's run identity does not cover the run's configuration

**What.** Found while pricing P14, not by design. `RunPreparationService.prepare`
digests the REQUEST (`_request_digest(request, profile)`), and
`RunPreparationRequestV1` carries question, budget, profile path, managed run id
and dossier digest — no configuration. So today two runs of the same question on
the same profile are the same run id, which is correct only because
configuration cannot vary. THE MOMENT configuration can vary (P14's fix), two
materially different runs collide on one managed run id and the second refuses
`RUN_ALREADY_STARTED` or, worse, resumes the first.

This is not a defect TODAY — nothing can vary — so it is recorded rather than
fixed. It becomes a defect the instant P14 lands, which is why it is written
down before that lands rather than after.

Whoever fixes P14 must dispose of this in FIX.md, in writing, before code:
either the operator config's digest enters `_request_digest`, or the fix states
why identity may stay configuration-blind and what stops the collision.

**Ready-to-send prompt:**

```
Route: whoever holds the P14 tranche (experiments/2026-08-29-defect-managed-path-config-read/).
Not a separate tranche -- a MANDATORY disposition inside P14's FIX.md.

Goal, one sentence: decide, in writing and before code, whether the operator
configuration a managed run is prepared from enters that run's identity.

Evidence:
  src/deepreason/preparation.py:722   request_digest = _request_digest(request, profile)
  src/deepreason/preparation.py:108-130  RunPreparationRequestV1 -- no config field
  src/deepreason/preparation.py:_load_existing  PREPARATION_INPUT_CONFLICT /
      PREPARATION_PROFILE_CONFLICT -- the typed refusals that fire when an
      existing root disagrees with the request, and the ones that would NOT
      fire on a configuration difference
  docs/map/CON-run-identity.md   the owning document ("Run identity is
      deterministic. Same question + config -> same run id" -- CLAUDE.md says
      "+ config" already; the code does not implement that half)

Note the wording collision: CLAUDE.md's live-run section already states
"Same question + config -> same run id". On the managed path there IS no
config input today, so the sentence is vacuously true. It stops being vacuous
the moment P14 lands.
```

---

## P19 — `docs_verify` check `SUB-application.md:403` is 54% of its own timeout on an IDLE box, so it goes red whenever the box is busy

**What.** Reported here because the batch's stated `docs_verify` baseline is
**4 failed** and this lane measured **5**, and the fifth is neither the P16
tripwire (which correctly stayed green — this lane's branch diff touches no
frozen-surface path) nor anything this lane changed. This lane changed no
`src/` file and no map document.

    FAIL SUB-application.md:403: grep -q "fence_seq > current_resume.resume_event_seq"
      src/deepreason/runtime/continuation.py && ! grep -q '...' && python -m pytest
      tests/test_continuation.py tests/test_v6_resumed_terminal_revalidation.py -q
      -> TIMEOUT after 300s - this check is too expensive; narrow it to the claim
         it actually tests

Full output: `proof/docs_verify.out`.

**It is a load artefact of a real fragility, not a false alarm and not a broken
claim.** Re-run standalone on an otherwise-idle box
(`proof/subapp403_recheck.out`): **15 passed in 160.88s**, exit 0. The claim the
check makes is TRUE. But 161s against a 300s cap leaves no headroom, and
`docs_verify` itself fans out to 4 workers — so the instrument can starve its
own most expensive check, and this batch runs several lanes concurrently on one
container. `dr-drive-harness` §5b already states the general rule this is an
instance of: *"Never run the full gate concurrently with docs_verify … the
contention manufactures failures."*

Not fixed here: `tools/docs_verify.py` is off-limits to this batch (an external
operator window is live on it), the fix belongs to whoever owns
`SUB-application.md`, and it is a different goal from this tranche's.

**Ready-to-send prompt:**

```
Route: deepreason-orchestrator (defect — an instrument that reports failure
without a failure). Small and self-contained.

Goal, one sentence: make the docs check at docs/map/SUB-application.md:403
prove its claim in a fraction of its 300s budget, so it stops going red on a
busy box while the behaviour it describes is intact.

Evidence:
  experiments/2026-08-29-defect-managed-path-config-read/proof/docs_verify.out
      -> the TIMEOUT, on a tree where no src/ file and no map document changed
  experiments/2026-08-29-defect-managed-path-config-read/proof/subapp403_recheck.out
      -> 15 passed in 160.88s, exit 0, standalone on an idle box
  .claude/skills/dr-drive-harness §5b -> the recorded rule about contention

The check's own failure message names the fix: "narrow it to the claim it
actually tests". The claim is about ONE resume-fence comparison in
runtime/continuation.py. Two whole test FILES (15 tests, 161s) are not that
claim; the one or two node ids that would fail if the comparison were mutated
are. Find them by mutating the comparison and recording which tests go red
(commit that output), then pin exactly those node ids.

Do NOT solve it by raising the timeout, and do NOT edit tools/docs_verify.py:
the 300s cap is a property of the instrument, and a check that needs more than
300s to prove a one-line claim is the thing that is wrong.

End state: the narrowed check passes in seconds, is demonstrated RED by the
same mutation that selected its node ids, `python tools/docs_verify.py --audit`
still accepts it, and docs_verify returns to its stated baseline. Map moved in
the same commit.
```
