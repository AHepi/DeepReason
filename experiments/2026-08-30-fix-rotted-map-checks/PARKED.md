# PARKED — Lane D, batch 2 — stops bubbled, never resolved in-batch

Eight items. Each is a ready-to-send prompt: paste one whole into an executor
window. Nothing here was decided by this lane. P-D8 was added, and P-D7
amended, on 2026-08-30 after independent review of the delivered work.

Anchor: branch `claude/b2-lane-D`, based on `origin/main` `84514a028`. Every
line number below was measured on 2026-08-30 and will move as documents are
edited — re-locate by the quoted anchor text, never by the number.

---

## P-D1 — NOT FIRED, recorded so the next reader does not re-open it

The lane brief pre-selected road (i) for the `llm × verification` seam: the
code is frozen and stays untouched, the DOCUMENT is corrected. Road (ii) —
removing `src/deepreason/invariants.py`'s module-level
`from deepreason.llm.firewall import route_fingerprint` so the old claim
becomes true — was NOT taken and was never close. It would edit frozen surface
3 and reach the frozen-ADJACENT `route_fingerprint` in `llm/firewall.py`, and
no grant exists on this branch.

Nothing to send. Recorded because a stop that did not fire, and is not written
down, gets re-litigated.

---

## P-D2 — ESCALATION: a granted contact moved a digest and a dark map pin was left behind

**This is a disclosure to the operator, not a decision request.** The edit
itself was granted by the lane brief and is done (commit `41a9180d6`). What is
escalated is the finding underneath it, which PARKED P2 required be surfaced
rather than folded into a one-character diff.

```
The discharge-wire qualification subject digest moved on 2026-08-28:

    b9038b84efdea313c3f3f2a8862d8acf180d3938ab3d1bf3588c3585dfe07386   before
    02ee7e098bb9239011708a4aa0bce4b7479619b3aff28eff46188125a869e713   after

It moved in commit e9457f8ff, tranche
experiments/2026-08-27-change-execution-safety/, under your conditional grant
for that tranche ("Frozen surface changes are permitted as long as you
document what is affected"). The cause is that tranche's own intended change:
the container profile now serves both simulation modes, so the compiled policy
binds python@deepreason-public-contained.v1 rather than the local toolchain,
and the manifest is part of the qualification behaviour subject.

Two things you may want to know.

FIRST, the operational cost is real and unpaid: the next live run against a
home qualified before 2026-08-28 pays a fresh qualification battery, about 14
minutes and ~1160 provider calls. That was priced in that tranche's
DELIVERY.md and has not been spent yet, because no live run has happened since.

SECOND, the discipline held in code and failed in the map. The two committed
TEST pins were updated in the same commit (tests/test_discharge_wire.py,
tests/test_allocation_signal_consumption.py). The pin in
docs/map/INV-frozen-surfaces.md was not -- and could not have argued, because
it spans several lines and docs_verify read checks line by line until
2026-08-29. That document pinned the same expression twice with two different
values for two days.

Fixed 2026-08-30: the pin is re-pinned, the trace (when, which commit, which
tranche, which grant, what it costs) is written at the pin site, and a new
check goes red if the two pins ever disagree again. No decision is being asked
for. If you want the requalification paid before the next ladder rather than
inside cycle 0, say so and it gets a setup step.
```

---

## P-D3 — `INV-frozen-surfaces.md:181`, the falsified transport_failure census — a REAL DESIGN FORK

Pre-existing red, belonging to the 2026-08-25 workflow-call-pairing grant, NOT
to this lane. Untouched here on purpose. Its repair cannot be a count change:
`SCHEMA.md` says counts are claims and the honest repair changes what the
sentence CLAIMS, which is a judgment about a grant's safety argument.

```
docs/map/INV-frozen-surfaces.md carries a check asserting zero committed
transport_failure attempts across the run roots. One exists, in a root
committed 2026-08-26, so the check is red and has been since. Read the
document's section around the check (anchor: the 2026-08-25 workflow-call-
pairing granted contact, which uses this census as its SECOND safety leg) and
decide which of these the document should now say, then implement exactly that
one:

  (a) re-scope the census to roots predating 2026-08-26 and say why that is
      still the right evidence for the grant's safety argument;
  (b) keep the census whole, change the claim from "zero" to the measured
      number, and re-argue -- or withdraw -- the safety leg that rested on
      zero;
  (c) retire the claim and name what replaces it as the grant's second leg.

Do NOT loosen the check's comparison to make it pass; SCHEMA.md's rule 6 makes
a count a claim, and a floor here would hide exactly what the census exists to
show. If (b) or (c) weakens the stated evidence for a granted frozen-surface
contact, STOP and put the fork to the operator rather than choosing.

Prove whichever you pick: show the check RED on the pre-repair claim and GREEN
after, and run the full docs_verify (not --fast) before committing. The map
moves in the same commit. Update docs/AUDIT_BASELINES.md's expected-failure
table in that same commit, since this row leaves it.
```

---

## P-D4 — the end-to-end discharge road E56 names as missing (F-A stays open)

This lane corrected `CON-discharge-channel.md`'s conclusion to exactly what is
measured — the compile → echo → rebuild round trip carries a configured
`DISCHARGE_POLICY` — and deliberately did NOT close
`experiments/2026-08-26-pc2-rematch/PARKED.md` F-A. Closing it is a bubble.

```
docs/ERRATA.md E56 (the discharge entry -- the ledger carries two entries
numbered E56) names one missing check: a configuration file naming a discharge
preset, through the real application/text_runs.py::start_manifest_run,
reaching a scheduler that resolves it. Since lane B2's carriage fix
(9a7b0a625) the compile -> echo -> rebuild half is measured and green
(docs/map/CON-discharge-channel.md, the check under "how far the configuration
road reaches"). The file -> start_manifest_run -> scheduler half has no check
anywhere.

Build that check, offline, against the deterministic stub. It must go RED if
the value stops reaching the scheduler, and it must not be satisfiable by the
round trip alone -- prove that by mutating carriage back out and showing the
new check fails for a DIFFERENT reason than the round-trip check does.

If it passes, experiments/2026-08-26-pc2-rematch/PARKED.md F-A can be closed
and docs/ERRATA.md gains an entry saying so. If it fails, you have found the
remaining break and it is a defect tranche, not a docs one. Either way the
answer is a measurement, not an argument: F-A stays open until a check that
can fail says otherwise.
```

---

## P-D5 — extend `--audit` to catch the shape D4 rotted into (analysis done; implementation is a src/ change)

The lane brief asked whether `--audit`'s vacuous-check detection could catch
D4's shape. **Answer: not by stretching `_VACUOUS`, but yes by adding a second,
advisory lint.** Reported, not implemented — this lane makes no `src/` changes.

Exact locations, measured 2026-08-30:

- `tools/docs_verify.py:78-80` — `_VACUOUS`, a static regex anchored at the
  command's FIRST token (`true|:|echo|test -efd PATH|ls PATH`).
- `tools/docs_verify.py:448-451` — where `cmd_audit` applies it, per check, in
  the only loop where a new lint belongs.
- `tools/docs_verify.py:504` — `cmd_self_test`'s pin on that behaviour, plus
  the fixture-based audit assertions at `:506-524`. This is the only gate the
  file has (`:459-461`: "nothing in tests/ exercises it").

Why `_VACUOUS` cannot be stretched: it detects checks that CANNOT FAIL. D4 is
the opposite defect — a check that FAILS ON A TRUE CLAIM. No widening of a
first-token regex reaches it.

```
Add ONE advisory lint to cmd_audit's per-check loop in tools/docs_verify.py,
and a matching arm in cmd_self_test.

What it flags: a check that derives a STRING from raw source text --
inspect.getsource(...), Path(...).read_text(), or an unanchored
grep -q <bare-identifier> over *.py -- and then makes an identifier-membership
assertion against that string. Comments and docstrings live inside that string,
so the check binds prose as well as code.

It must be ADVISORY, printed and counted separately, NOT a new failure. Two
reasons, both measured: SCHEMA.md itself ships such a check as a worked example
(! grep -q "deepreason.scratch" src/deepreason/rules/crit.py), and
SUB-llm.md's anchored ^[[:space:]]*(from|import) form is comment-immune. A
hard rule would flag legitimate checks.

Prove it two ways before committing: it flags the pre-repair D4 check (its text
is in git at 152c7e204:docs/map/INV-signal-contract.md), and it does NOT flag
the repaired one or SUB-llm.md's anchored grep. Add both directions to
cmd_self_test, because nothing in tests/ covers this file.

Then re-run python tools/docs_verify.py --audit and record the finding count;
docs/AUDIT_BASELINES.md moves in the same commit if the count changes.
```

---

## P-D6 — `SCHEMA.md` states something its own tool does not do

Genuine docs-vs-code drift, in `docs/map/`, but a FIFTH finding beyond this
lane's four. Not touched here: `SCHEMA.md` is the contract every map document
is written against, and correcting it is an edit to the contract.

```
docs/map/SCHEMA.md says, in the "Do not write a check that cannot fail"
paragraph: "tools/docs_verify.py --audit flags checks that pass against a
deliberately mutated tree."

cmd_audit does no such thing. It never mutates and never executes: it applies a
static regex (_VACUOUS) to each check command's leading token, reports
documents with no checks, and reports unparseable openers. Its own docstring
says so -- "Flag checks that cannot fail, and documents with no checks at all."

Correct the sentence in SCHEMA.md to what the tool does, and -- because this is
the contract document -- say plainly what it does NOT do, so nobody again reads
"--audit is green" as "these checks were falsified". Mutation proof remains a
manual discipline, and SCHEMA.md's own rule about it (do not measure the tree
while a falsification pass is running) is what carries it.

While in there: SCHEMA.md's self-test check pins map-wide multi-line checks at
>= 70. Re-run it after any edit, and do not collapse multi-line checks to
single-line form without re-counting.
```

---

## P-D7 — `SUB-llm.md`'s negative grep has TWO holes, and it is the only other thing policing this seam

Noted in `SEAM-llm-x-verification.md`'s body as part of D1. Widening the grep
is arguably a separate change, so it is parked rather than folded in.

**Amended 2026-08-30 after independent review.** This entry first said "the
only thing that would now catch a new import is `SEAM-llm-x-verification.md`'s
crossing check". That premise was FALSE WHEN WRITTEN: the crossing check
resolved an `ImportFrom` on its module path alone, so it missed
`from deepreason import invariants` and four sibling forms — nine of sixteen
planted forms passed it. The check was repaired in this tranche and the
sixteen-form table (`proof/d1_crossing_forms.py`) now shows every form red, so
the premise is true as of the repair. The second hole below was found in the
same review and is still open.

```
docs/map/SUB-llm.md carries a check forbidding src/deepreason/llm/ from
importing a named list of packages: harness, scheduler, rules, adjudication,
capture, informal, verification, amendment. It has two independent holes.

(1) The list omits `invariants`, so an llm/ module doing
    `from deepreason.invariants import verify_root` passes it.

(2) The pattern is `^[[:space:]]*(from|import) +deepreason\.(...)\b`, which
    requires the package to sit in the DOTTED path. So even for the packages
    it does name, the leaf form `from deepreason import verification` passes
    it -- and src/ uses that leaf form 29 times across 24 files while
    containing no relative imports at all, so it is the form a real regression
    would most likely take. Widening the LIST alone does not close hole (2).

Measured 2026-08-30: the reverse direction of the llm x verification seam is
EMPTY in every form tested (16 forms, proof/d1_crossing_forms.py), and after
this tranche's repair SEAM-llm-x-verification.md's crossing check catches all
sixteen. SUB-llm.md's grep catches only the dotted ones for the packages it
names.

Fix both: add `invariants` (and consider `signals_read`, which
SUB-verification.md also Owns) to the list, AND make the pattern reach the
leaf form -- either a second alternation branch
`from +deepreason +import +(...)`, or an AST resolver like the one
SEAM-llm-x-verification.md now carries. Prove it with the same sixteen-form
table: every form RED against the widened grep, and GREEN on the real tree.
Do not edit src/deepreason/llm/ -- llm/firewall.py is frozen-adjacent and
nothing here needs a code change.
```

---

## P-D8 — `SUB-application.md:421` is a 300-second check that costs 161-213 seconds, and the audit baseline pays for it

Raised by independent review of this lane's own baseline edit, and NOT decided
here: narrowing another document's check changes what that claim is defended
by, which is a judgment about someone else's claim and outside this lane's
four targets. The baseline now records the row honestly instead
(`docs/AUDIT_BASELINES.md`, CONTAINER-CONDITIONAL row); this prompt asks
whether the underlying cost should be removed.

```
docs/map/SUB-application.md carries a check (the one anchored on
"fence_seq > current_resume.resume_event_seq") that ends with

    python -m pytest tests/test_continuation.py \
                     tests/test_v6_resumed_terminal_revalidation.py -q

i.e. two entire test FILES. Measured cost of that check alone, run serially on
the 4-CPU cloud container, five independent measurements across two days:

    160.88 s   2026-08-29, idle box
    182.8  s   2026-08-30
    186.9  s   2026-08-30
    195    s   2026-08-30
    213.1  s   2026-08-30, independent reviewer

docs_verify's per-check ceiling is 300 s (tools/docs_verify.py:185) and its
default worker count is min(16, os.cpu_count()) = 4 here. So this one check
sits at 54-71% of its own ceiling BEFORE sharing 4 CPUs with 3 other checks,
and the documented baseline command self-contends: the check has been observed
to report `TIMEOUT after 300s` with no foreign load required. That makes the
instrument's TOTAL two-valued on this container, which is exactly what an
audit baseline must not be.

docs_verify's own timeout message prescribes the repair: "this check is too
expensive; narrow it to the claim it actually tests". Decide whether to do
that, and if so, what the claim actually is. The claim in the document is
about ONE branch -- prepare_continuation's `current_resume is not None`
recovery branch, measured on grounded-extension run 8e22d0431fd2b98d -- while
the check runs both files whole.

Constraints on whoever takes this:
  - Do NOT weaken the defense to make a number stable. If the narrowed set
    would not have caught the original defect, do not narrow it.
  - Prove the narrowed set is not a loosening: show it RED on the reverted
    code shape (restore the `!=` inequality and drop the grep guard), and
    GREEN on the real tree, in the same commit.
  - Re-time the narrowed check and record the new margin against 300 s.
  - Whatever is decided, update docs/AUDIT_BASELINES.md's CONTAINER-CONDITIONAL
    row in the same commit -- it is the thing this cost is currently being
    paid out of.

Alternatives if narrowing is refused: pin a worker count in the documented
baseline command so the total is reproducible (costs wall time -- a 4-worker
run is ~29 minutes here, and -j 1 would be roughly 4x that), or raise
CHECK_TIMEOUT_S, which is a tools/ change and masks cost rather than removing
it.
```

---

## Not a stop, but recorded: `SEAM-llm-x-rules.md:54` stays red

The unparseable check (a `check:` opener with no closing backtick) is the
single finding keeping `docs_verify --audit` above zero. It is upstream-parked
as P3 in `experiments/2026-08-29-fix-docs-verify-multiline-checks/PARKED.md`
and is NOT one of this lane's four; it remains in
`docs/AUDIT_BASELINES.md`'s expected-failure table. Any lane whose workflow
demands "--audit reports 0 findings" must record this pre-existing finding
rather than treat it as its own failure.
