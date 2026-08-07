# Monitor-session handover — 2026-08-06

You are the MONITOR: you review executor tranches, draft the operator's
prompts, promote workflow lessons into skills, and run occasional work
yourself (test phase, pre-plans). The operator (Aaron, they/them)
drives by pasting prompts you write into executor windows and relaying
results. Executor sessions are Sonnet 5; they work the rung ladders.

Read first, in this order: CLAUDE.md (including the operator's
recorded explanation style — answer their worry FIRST, price forks as
roads, one closing analogy; it's repo law now), then this file, then
the newest RESULTS/DELIVERY files named below.

## Branches (the part that bites)

- `claude/handover-defect-audit-33pv3d` — YOUR branch. Push here.
- `claude/delivery-rungs-handover-m22sdy` — the executor program
  branch. Standing rule: every monitor commit is pushed to BOTH
  (fetch→merge→push pattern; remote warns about merge commits but
  accepts). Retry pushes 2s/4s/8s/16s.
- `claude/seat-census-rung-s1-7gphj9` — the CURRENT executor branch
  (its fresh window minted it; base was current, verified). After each
  rung delivery, fast-forward the delivery branch to it. Last synced
  head: `49814376` (both monitor+delivery branches).
- Heddle repo (`ahepi/heddle`, clone at /workspace/heddle if still
  alive): branch `claude/heddle-skills-organization-d9yika`. Separate
  project — the operator's harness-for-skills. You fixed its skills,
  ported guardrails, fixed its red gate. Another session ships there
  actively; rebase-don't-clobber.

## Live thread RIGHT NOW: Rung S5 (seats in the typed record)

The role-seat separation program (docs/proposals/
ROLE_SEAT_SEPARATION_PLAN.md — read it) is at S5. S1-S4 delivered:
census; binding design (Option A/2a); binding wired (--seat
GROUP=PATH on setup); qualification per seat delivered as **Option 2b**
— multi-model launch WORKS via combination-subject qualification,
proven by measurement M5 (battery cases dispatch to their own role's
bound endpoint; committed regression test). S4b (per-role provenance,
frozen-surface-5, ~400-700 lines) is PARKED as the optimization that
makes model-swapping cheap; its design needs a DESIGN-AND-STOP and
operator words when picked up.

S5 status: executor asked (screenshot relayed) whether "follow the
rung-4 template exactly" inherits rung 4's harness.py authorization.
You advised: type explicit words, never inherit frozen grants
(non-transitivity is settled repo law). Operator was given this text
to send:

> Explicit authorization for Rung S5 only: you may add the
> record_seat_bindings appender plus one _commit keyword to harness.py
> — zero change to _apply_event or well-formedness. This grant is not
> transitive to any later rung.

Next after S5: **S6** — live two-model A/B. Needs from the operator:
(1) choice of second model (cheap-but-different is the right
demonstration; attribution, not quality, is the point — "two
signatures on one document"), (2) OLLAMA_API_KEY again if the
container rolled (env files are gitignored under experiments/*/env —
a pattern YOU added; check `git check-ignore` before writing any env).
Each distinct model/combination = its own full qualification battery
(~6-14 min live). S7 (packages) joins
docs/proposals/BEHAVIOR_MODES_PREPLAN.md later.

## Review discipline (what you actually do per rung)

Fetch executor branch; read the delivery/spec COMMITS not the claims;
run the frozen-surface tripwire yourself (`git diff --stat <base>..
<head> -- src/deepreason/capabilities/state.py src/deepreason/
harness.py src/deepreason/invariants.py src/deepreason/run_manifest.py
src/deepreason/qualification.py`); check R-by-R reconciliation; then
write the operator a verdict in their style + the exact reply/prompt
to paste. DESIGN-AND-STOP specs: verify measurements are pasted, not
argued, before recommending approval.

## State of everything else

- **Program 1 (7-rung modularization handover)**: complete, live-
  validated. Testphase: experiments/2026-08-05-testphase-live-
  validation/ — PASS 6/6 (fingerprint stamp live; continuation of
  budget_exhausted live). Rung 6 impl + 7b/7c: approved designs,
  deferred by operator.
- **Gate**: ~3366 passed; ONE known pre-existing failure P1 =
  jsonschema undeclared test dependency (environment-only, parked
  with repro in the S1 census tranche). Expect executors to name it.
- **Queue-drain window**: prompt already written (in chat history and
  reproducible: triage every PARKED across 2026-08-04/05 tranches —
  W2 cancel race, V4 failing-line visibility, P7 verify_root defect
  [frozen surface 3 — operator words at fix], U1 flake, + small fry —
  do-now/schedule/retire, drain do-nows). Operator postponed it for
  the seat program; offer it again when the ladder pauses.
- **Pre-plans parked in docs/proposals/**: BEHAVIOR_MODES_PREPLAN.md
  (modes+bundles+mini-harness pointer), ROLE_SEAT_SEPARATION_PLAN.md
  (needs amendment: insert S4b as a formal rung — you promised this
  and haven't done it; do it on your next quiet moment).
- **Jargon-to-prose layer**: operator's declared NEXT project. The
  style convention in CLAUDE.md is its first brick.
- **General skills**: 16 generalized SKILL.md files delivered to the
  operator as flat files (in chat); source of truth for the method is
  DISCIPLINE.md-style spec captured in Heddle's repo.

## Standing rules learned the hard way (do not relearn)

- Frozen-surface approval is NEVER transitive and correctness never
  substitutes for authorization (X9).
- Verify executor claims against commits; never relay unverified.
- Never predict/fabricate results of pending background tasks.
- Kill by PID never pattern; one worker-spawning instrument at a time.
- Push failures: fetch→merge→push, never force without operator words
  (force-with-lease needed explicit lease value once via proxy).
- The operator's "next prompt please" sometimes arrives before the
  executor has pushed — CHECK THE BRANCH FIRST, report honestly if
  nothing landed.
- Credentials: recreate from operator only, chmod 600, verify
  check-ignore, never in any commit.
- Every stop to the operator: decision in one sentence, roads priced,
  recommendation, analogy. They answer with a word.

## Your unfinished small items

1. Amend ROLE_SEAT_SEPARATION_PLAN.md to insert S4b formally.
2. Offer the queue-drain window when the seat ladder pauses.
3. S6 prompt needs writing when S5 closes (template: S5 accepted →
   operator picks model 2 + provides key → ladder mirrors
   experiments/2026-08-05-testphase-live-validation/testphase_run.sh
   but with --seat bindings; audits assert per-seat attribution from
   typed attempt records).
