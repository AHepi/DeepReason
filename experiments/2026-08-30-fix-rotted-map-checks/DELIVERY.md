# DELIVERY — Lane D, batch 2 — four rotted map checks, repaired

Tranche: `experiments/2026-08-30-fix-rotted-map-checks/`
Branch: `claude/b2-lane-D`, based on `origin/main` `84514a028` (lane base
`152c7e204`). Offline by construction — no `OLLAMA_API_KEY`, no live run, no
live evidence claimed anywhere in this document.

This document stands alone. It states what was asked, what was done for each of
D1–D4, the before/after transcript for every repaired check, the cone as
measured, every bubbled stop, and the residue.

**Second round, 2026-08-30.** Independent reviewers re-ran this lane's claims
after delivery `7fbbf2bc2` and confirmed three MAJOR defects and four minor
ones. None was refuted; all reproduced on first attempt. §11 is the ledger of
that round, and §§2, 7.2, 7.2a, 7.3, 7.4, 7.6, 7.7, 8, 9 and 10 carry the
corrections in place rather than only at the end. The two that matter: D1's
crossing check enforced two import forms out of six, and this lane's
`docs_verify` baseline recorded the lowest of four observations as a fixed
value.

---

## 1. What was asked

Repair four checks in `docs/map/` that the 2026-08-29 multi-line-parser fix
caused to be EXECUTED for the first time, and that failed on that first
execution. `docs/map` + measurement only; **no `src/` changes at all**. Every
repaired check must be shown FAILING on its broken form and PASSING on the
repaired one — a check that cannot be made to fail is vacuous and does not
count as repaired. `docs/AUDIT_BASELINES.md`'s expected-failure list moves in
this lane's own commits, with the measurement that justifies it.

| id | target | what was rotted |
|---|---|---|
| D1 | `SEAM-llm-x-verification.md` | the core CLAIM was false: "no import in either direction" |
| D2 | `INV-frozen-surfaces.md` | a stale qualification-digest PIN (asserted `b9038b84`, measured `02ee7e09`) |
| D3 | `CON-discharge-channel.md` | the check's FIXTURE was wrong; the check died before either assertion |
| D4 | `INV-signal-contract.md` | the check was defeated by a COMMENT; the claim it defends is true |

---

## 2. D1 — the seam's claim was false in one direction

**What was wrong.** The document said: "Between them there is **no import in
either direction** — `invariants.py` names nothing from `llm/`, and `llm/`
names nothing from `invariants.py`." One half of that is true. The other is
false, and had been for as long as the check existed — the check had never once
been executed, because it spans several lines and `docs_verify` read checks
line by line until 2026-08-29.

**What is actually true**, measured by AST over the files each side declares it
`Owns:` (`invariants.py`, `verification/`, `signals_read.py` on one side; all
of `llm/` on the other), resolving relative imports through their package
level rather than by substring:

    verification -> llm      7 symbol crossings across 6 import statements
      invariants.py            route_fingerprint            MODULE LEVEL
      invariants.py            ConjecturerOutput            function-local
      invariants.py            AliasTable                   function-local
      invariants.py            wire_contract_for            function-local
      invariants.py            ReferenceFreeConjecturerWireContract  function-local
      invariants.py            HashingEmbedder              function-local
      verification/report.py   route_fingerprint            function-local

    llm -> verification      0, in every form: dotted absolute, dotted
                             relative, package-leaf absolute, package-leaf
                             relative, plain import, and each of those written
                             inside a function
      (prefixes tested: deepreason.invariants, deepreason.verification,
       deepreason.signals_read; 16 planted forms, proof/d1_crossing_forms.py)

So the true relationship is **asymmetric, not absent**. The seventh crossing —
`verification/report.py` — was missed by the predecessor tranche's own finding,
which named five sites in `invariants.py` only.

**What polices it now.** The document states the relationship as
one-directional, gives every crossing the re-derivation it performs (route
digest; wire-contract authority set; detection totality), and carries a
replacement check that pins the exact crossing SET **in both directions** —
the empty direction included, because an assertion that something stays absent
is the only thing that keeps it absent. The document says in prose that the
set is deliberately brittle, so the next author widens it on purpose rather
than deleting the check.

**The first version of that replacement check did not enforce what this
section claimed for it, and that is recorded in full in §11.** It resolved an
`ImportFrom` on its module path alone, so nine of sixteen planted import forms
passed it GREEN — including `from deepreason import invariants`, the leaf form
`src/` itself uses 29 times across 24 files. The state claim above was never
in doubt (the reverse direction is genuinely empty, re-confirmed under all
sixteen forms); what was over-claimed was the ENFORCEMENT. The check now
resolves each alias both ways and carries the module-level/function-local flag
on every crossing, and the sixteen-form table is committed beside it as
`proof/d1_crossing_forms.py` and wired in as a check of its own.

**The frozen code was not touched.** Both verification-side files are frozen
surface 3 and `llm/firewall.py` is frozen-ADJACENT. Removing the import to
make the old claim true was named as a HARD STOP in this lane's recon and was
not taken (`PARKED.md` P-D1).

**Companions, same commit.** `INDEX.md`'s matrix row (dash → 1, and the
paragraph that repeated the false premise) and `SUB-verification.md`'s
"deliberately absent" seam row. The `Traps` entry was rewritten, never deleted:
its lesson — zero import traffic is not zero coupling — survives its false
premise, and now carries the date and how it was found.

**The `Sweep:` ratchet was settled by WITHHOLDING the header**, which
`SCHEMA.md` permits when every candidate spec would flag readers rather than
enforcement sites, provided the body says why. It does. Measured: three
candidate specs over `attempt_trace|split_legs` return ZERO enforcement sites
between them and four readers, because `--coverage` recognises enforcement as
`FIELD ==`, `== FIELD` or `raise ... FIELD` while `verify_root` reads values
OFF the field and calls `fail` — and never names `LLMAttempt` or
`LLMSplitLegV1` at all. `--coverage`'s finding count did not move (2 before, 2
after).

### D1 transcript — `proof/d1_seam_crossings.txt`

    [1] BROKEN FORM (the committed check, on the real tree): rc=1
        AssertionError: ('src/deepreason/invariants.py', 'deepreason.llm.firewall')
    [2] REPAIRED FORM (on the real tree):                    rc=0
    [3] REPAIRED FORM on an unmutated scratch copy:          rc=0
    [4] M1 eighth forward crossing added:                    rc=1
        AssertionError: ['src/deepreason/invariants.py::deepreason.llm.packs::build_pack']
    [5] M2 reverse crossing added (absolute):                rc=1
        AssertionError: ['src/deepreason/llm/adapter.py::deepreason.invariants::verify_root']
    [6] M3 reverse crossing added (relative):                rc=1
        AssertionError: ['src/deepreason/llm/adapter.py::deepreason.verification.report::verification_report']
    [7] scratch copy restored:                               rc=0
    repo tree status: (no src/ changes)

M3 is the one that matters most for the check's durability: a relative import
(`from ..verification.report import ...`) is exactly what a substring grep
walks past, and `SCHEMA.md`'s check-writing rule 3 records that this has
already cost a seam its core dependency-arrow claim once.

**That set of three mutations was not enough, and §11 records why.** All three
plant a DOTTED module path, which is the form the check's author had in mind;
none plants the package-leaf form the repo actually uses. The transcript above
is kept as written and the sixteen-form table is appended beneath it in the
same file.

---

## 3. D2 — the stale digest pin, and the escalation under it

**This lane owned this one re-pin, and it was granted by the lane brief.** What
was NOT granted, and is therefore reported rather than folded into the diff, is
the finding underneath it. PARKED P2 said: if the digest actually MOVED while
one pin was updated and another was not, "that is a different and larger
finding, and it goes to the operator before any edit." That is what the record
shows.

**Before / after.**

    b9038b84efdea313c3f3f2a8862d8acf180d3938ab3d1bf3588c3585dfe07386   before
    02ee7e098bb9239011708a4aa0bce4b7479619b3aff28eff46188125a869e713   after

**The tracing, now recorded at the pin site in the document itself.**

| question | answer |
|---|---|
| when did it move | 2026-08-28 |
| which commit | `e9457f8ff` — "switch on: the container profile serves BOTH simulation modes, not one" |
| which tranche | `experiments/2026-08-27-change-execution-safety/` |
| under which grant | the operator's conditional frozen-surface grant for that tranche, verbatim: "Frozen surface changes are permitted as long as you document what is affected" (its `REQUEST.md`, constraint C7) |
| why it moved | the default simulation runner became the CONTAINED one, so the compiled policy binds `python@deepreason-public-contained.v1`; the manifest is part of the qualification behaviour subject |
| what it costs | the first live run after it pays a fresh qualification battery — ~14 minutes, ~1160 provider calls. Priced in that tranche's `DELIVERY.md`; **not yet spent**, because no live run has happened since |
| what was updated | `tests/test_discharge_wire.py` and `tests/test_allocation_signal_consumption.py`, in that same commit |
| what was NOT updated | this map pin — it was DARK (multi-line, unreadable by the parser of the day), so nothing made it argue with the pin a hundred lines above it that already asserted the post-move value |

The discipline held in code and failed in the map. That is the finding, and it
is surfaced as `PARKED.md` P-D2 as well as recorded here and in the document.

**What the repair does.** Re-pins the assertion to the measured value; keeps
the `DISCHARGE_POLICY` leak assertion; writes the trace above the pin; corrects
the F1 prose that still stated the old value as current; dates the 2026-08-22
historical mention so it cannot be read as current; and adds a `Traps` entry
with a NEW check that goes red if the document's two pins ever disagree again.

### D2 transcript — `proof/d2_digest_pin.txt`

    [1] BROKEN FORM (committed pin, asserting b9038b84...): rc=1  AssertionError
    [2] REPAIRED PIN (asserting 02ee7e09...):               rc=0
    [3] TWIN CHECK on the repo tree:                        rc=0
    [4] TWIN CHECK on an unmutated scratch copy:            rc=0
    [5] M1 first pin reverted to the stale value:           rc=1  ... [762]
    [6] M2 second pin reverted to the stale value:          rc=1  ... [612]
    [7] M3 one pin deleted outright:                        rc=1  ... [612]
    [8] scratch copy restored:                              rc=0

M1 is the half-repair that actually happened on 2026-08-28. It is now a red
line rather than a silence.

**No other pin moved — the lane's stop condition, tested rather than assumed.**
Every check in `INV-frozen-surfaces.md` was run. Verdicts in §7.

---

## 4. D3 — the fixture was wrong, and the conclusion moved with it

**What was wrong.** The check bound `engaged_local_simulation_toolchain()`
while `engaged_inquiry_capability_policy()` names the CONTAINED toolchain, and
`compile_run_manifest` requires exactly one bound toolchain matching the
policy's identity. So the manifest construction raised
`V6_SIMULATION_TOOLCHAIN_REQUIRED` and the check died BEFORE either assertion —
testing nothing, in a document that read as though it tested something. It was
written when local WAS the default and went wrong on 2026-08-28 when the
container profile switched. Nothing noticed, for the same reason as D2: the
check had never been executed.

**The repair** binds `engaged_simulation_toolchain()`, which returns whichever
toolchain the engaged policy actually names. That binding cannot drift with the
default.

**The second half — the claim reversal — was taken to the recommended
disposition and no further.** With the check runnable, what it measures is:

    code default             discharge-required.v1
    source config            off
    in engine_config_json    False
    rebuilt via manifest     off
    compile notices          [('ENGINE_CONFIG_FIELD_NOT_CARRIED',
                               '/engine_config/DISCHARGE_POLICY')]
    engaged toolchain id     python@deepreason-public-contained.v1
    policy names toolchain   python@deepreason-public-contained.v1

So the document's own conclusion — "the FREE layer of this document's own
three-layer table is, today, reachable only by editing code" — is FALSE since
lane B2's carriage fix (`9a7b0a625`): the pop still keeps the field out of the
echo, so no qualification subject digest moves, but the
`ENGINE_CONFIG_FIELD_NOT_CARRIED` notice now carries the value and
`config_from_run_manifest` restores it from there.

**What is NOT claimed, stated in the document in these words.** The
compile → echo → rebuild round trip is ONE LINK. The road `docs/ERRATA.md` E56
(the discharge entry — the ledger carries two entries numbered E56) names as
missing is a configuration file naming a preset, through the real
`start_manifest_run`, reaching a scheduler that resolves it. That has no check
anywhere and is not proven here. **`experiments/2026-08-26-pc2-rematch/PARKED.md`
F-A is explicitly left OPEN**, and the document says so, with a sentence telling
the reader not to read the check as closing it. Closing F-A is bubbled as
`PARKED.md` P-D4.

### D3 transcript — `proof/d3_discharge_measurement.txt`, `proof/d3_discharge_mutation.txt`

    [1] BROKEN FORM (committed fixture, local toolchain): rc=1
        Value error, V6_SIMULATION_TOOLCHAIN_REQUIRED: policy must bind one frozen toolchain
    [2] REPAIRED FORM (policy-tracking toolchain):        rc=0

    scratch import resolves to: /tmp/tmp.../src/deepreason/__init__.py
    [0] unmutated scratch:                               rc=0
    [1] M1 carriage removed (P15 returns):               rc=1
        AssertionError: carriage no longer restores the configured value --
        P15 may have regressed; re-read this section
    [2] M2 pop removed (the echo leaks the field):       rc=1  AssertionError
    [3] scratch restored:                                rc=0
    repo src/ untouched: (clean)

Both halves of the check fail on their own real regression, and the assertion
messages distinguish them — which matters, because a toolchain-default change
and a carriage regression would otherwise surface as the same red line.

---

## 5. D4 — a check defeated by a comment

**What was wrong.** The check asserted that the `Scheduler` class source never
names `LINEAGE_POLICIES`, `wander_cap_v1` or `open_lineage_v1`. The claim is
TRUE. The check was RED, because `inspect.getsource` returns comments and one
comment in that class explains the decoupling BY NAMING the registry it is
decoupled from. The check read its own explanation as a violation.

Measured: `LINEAGE_POLICIES` occurs once in the raw class source; every
occurrence is inside a comment; it occurs zero times in the unparsed AST; and
`wander.decide(` and `wander.reading_from(` both survive the round trip.

**The repair** parses the dedented class source, drops docstrings in docstring
position, and asserts over `ast.unparse` output. Comments and docstrings are
not code, and the claim is about what the code reaches. The paragraph above the
check now states the qualification rather than leaving it to be discovered by a
red check.

`src/deepreason/scheduler/scheduler.py` is another lane's cone and carries a
claim that is true. It was not touched.

### D4 transcript — `proof/d4_lineage_policies.txt`

    [1] BROKEN FORM (raw getsource text):                  rc=1
        AssertionError: LINEAGE_POLICIES
    [2] REPAIRED FORM (comments/docstrings stripped, AST): rc=0
        LINEAGE_POLICIES in raw source : 1
          ... and every occurrence is in a comment: True
        LINEAGE_POLICIES in unparsed AST: 0
        wander.decide( survives         : True
        wander.reading_from( survives   : True
    [3] REPAIRED FORM on an unmutated scratch copy:        rc=0
    [4] M1 scheduler reaches LINEAGE_POLICIES by id:       rc=1  AssertionError: LINEAGE_POLICIES
    [5] M2 reading_from call renamed away:                 rc=1  AssertionError
    [6] M3 docstring names the symbols (must stay GREEN):  rc=0
        same M3 tree under the BROKEN form (must be RED):  rc=1  AssertionError: wander_cap_v1
    [7] scratch restored:                                  rc=0
    repo src/ untouched: (clean)

M1 is the real regression the claim exists to forbid: the scheduler reaching
`wander.LINEAGE_POLICIES['wander-cap.v1']` instead of the interface. M3 is the
false positive the repair removes, and the same tree is RED under the old form
— which is the pair of measurements that says the repair is a repair and not a
loosening.

**Also corrected in that document (D4-c):** the note telling authors that a
multi-line check is dropped without a word — true of the parser until
2026-08-29, false since. Rewritten to record the history rather than deleted,
and its parked pointer marked closed.

---

## 6. The `--audit` question, answered and NOT implemented

The brief asked whether `--audit`'s vacuous-check detection could be extended
to catch D4's shape. **Answer: not by stretching `_VACUOUS`; yes by a separate,
advisory lint.** It is a `src/`-adjacent tooling change and therefore outside
this lane's no-`src` framing, so it is reported with exact locations and parked
(`PARKED.md` P-D5), not built.

- `tools/docs_verify.py:78-80` — `_VACUOUS`, a static regex anchored at the
  command's FIRST token.
- `tools/docs_verify.py:448-451` — where `cmd_audit` applies it, per check.
- `tools/docs_verify.py:504` — `cmd_self_test`'s pin on that behaviour, with
  the fixture-based audit assertions at `:506-524`. That is the only gate this
  file has: `:459-461` records that nothing in `tests/` exercises it.

`_VACUOUS` **cannot** be stretched to cover D4. It detects checks that CANNOT
FAIL. D4 is the opposite defect — a check that FAILS ON A TRUE CLAIM — and no
widening of a first-token regex reaches it. What could catch the SHAPE is an
additive lint in the same loop, flagging a check that derives a string from raw
source text (`inspect.getsource`, `read_text()`, an unanchored `grep -q
<bare-identifier>` over `*.py`) and then asserts identifier membership against
it. It must be ADVISORY: `SCHEMA.md` itself ships such a check as a worked
example, and `SUB-llm.md`'s anchored `^[[:space:]]*(from|import)` form is
comment-immune, so a hard rule would flag legitimate checks.

---

## 7. Measurement

### 7.1 The environment the numbers were taken in

    which python                         /usr/local/bin/python
    python -m pytest --version           pytest 9.1.1
    python -c "import deepreason"        /home/user/DeepReason/src/deepreason/__init__.py
    git rev-parse --is-shallow-repository true
    git rev-parse origin/main            84514a028
    lane base                            152c7e204

The editable install resolves `deepreason` to the MAIN checkout, not to this
worktree. That is safe for this lane and was verified rather than assumed:
`diff -rq /home/user/dr-lanes/lane-D/src /home/user/DeepReason/src` is EMPTY,
`tests/` likewise, and the main checkout is at the same commit with a clean
`git status`. Re-verified after the final measurement. This lane changes no
`src/`, so nothing it did could move that.

**The clone is SHALLOW**, so the three `CON-run-identity.md` git-history checks
fail for an environmental reason. Five is the right number here; two is the
right number on a full clone. `git fetch --unshallow` is a mutating command and
was deliberately not run.

### 7.2 `docs_verify`, full mode, before and after

Before — `proof/docs_verify_before.txt`, run on the lane base tree:

    docs_verify [full]: 70 documents, 1248 checks, 4 workers
    docs_verify: 10 failed

    SEAM-llm-x-rules.md:54          unparseable check          (out of scope, P3)
    CON-discharge-channel.md:150    V6_SIMULATION_TOOLCHAIN_REQUIRED   <- D3
    CON-run-identity.md:211         git history (shallow clone)
    CON-run-identity.md:213         git history (shallow clone)
    CON-run-identity.md:215         git history (shallow clone)
    INV-frozen-surfaces.md:181      transport_failure census   (pre-existing)
    INV-frozen-surfaces.md:734      stale digest pin           <- D2
    INV-signal-contract.md:243      LINEAGE_POLICIES in a comment      <- D4
    SEAM-llm-x-verification.md:19   invariants.py imports deepreason.llm  <- D1
    SUB-application.md:421          TIMEOUT after 300s         (CONTENTION)

After — `proof/docs_verify_after.txt`, run on this branch:

    docs_verify [full]: 70 documents, 1249 checks, 4 workers
    docs_verify: 7 failed

    SEAM-llm-x-rules.md:54          unparseable check          (out of scope, P3)
    CON-run-identity.md:211         git history (shallow clone)
    CON-run-identity.md:213         git history (shallow clone)
    CON-run-identity.md:215         git history (shallow clone)
    INV-frozen-surfaces.md:181      transport_failure census   (pre-existing)
    SUB-application.md:395          a restart-timing test      (CONTENTION)
    SUB-application.md:421          TIMEOUT after 300s         (CONTENTION)

**All four targets are gone from the failure set.** No target's line number
appears in the after list under any number.

FINAL for the first round — `proof/docs_verify_final.txt`, run last, on the
complete tree including the baseline and delivery edits, with the box quieter
than the previous two runs but NOT idle (§11.3 corrects the commit message
that called it a quiet box):

    docs_verify [full]: 70 documents, 1249 checks, 4 workers
    docs_verify: 5 failed

    SEAM-llm-x-rules.md:54          unparseable check          (out of scope, P3)
    CON-run-identity.md:211         git history (shallow clone)
    CON-run-identity.md:213         git history (shallow clone)
    CON-run-identity.md:215         git history (shallow clone)
    INV-frozen-surfaces.md:181      transport_failure census   (pre-existing)

Five, matching `docs/AUDIT_BASELINES.md`'s updated table ROW FOR ROW. Both
`SUB-application.md` rows passed in this run.

**That was one observation, and one observation was not enough.** An
independent reviewer ran the same command on the same branch and got SIX, with
`SUB-application.md:421` reporting `TIMEOUT after 300s`. §11.2 records the
finding; this section records the replication it forced.

### 7.2a Two fresh full runs, back to back, on the final tree

`proof/docs_verify_replicate_1.txt`, `proof/docs_verify_replicate_2.txt` —
started one after the other by a single script so nothing this lane ran could
overlap itself, on the tree that carries every repair including the D1
resolver fix:

    RUN 1   start 04:04:50 UTC   finish 04:20:31 UTC   15 m 41 s
            70 documents, 1250 checks, 4 workers        5 failed
            load average 1.87 at start, 4.81 at finish

    RUN 2   start 04:20:31 UTC   finish 04:33:45 UTC   13 m 14 s
            70 documents, 1250 checks, 4 workers        5 failed
            load average 4.81 at start, 3.77 at finish

Both returned the SAME five rows — `SEAM-llm-x-rules.md:54`, the three
`CON-run-identity.md` git-history rows, `INV-frozen-surfaces.md:181` — and
neither `SUB-application.md` row appeared in either. BOTH runs are recorded,
not the lower, because recording the lower is what produced the finding in the
first place. Neither box was idle: other lanes worked throughout, and the load
averages above are quoted rather than hidden.

**What two 5s do NOT establish.** They do not make 5 the total. The reviewer's
6 is equally real and its cause is measured: `:421` costs 161–213 s against a
300 s ceiling and the documented command runs 4 workers on 4 CPUs, so the row
is genuinely two-valued on this container. `docs/AUDIT_BASELINES.md` now
records the total as **5 or 6** with `:421` as a named CONTAINER-CONDITIONAL
row and a one-command disposition, which is what the instrument actually
produces here.

### 7.3 Both runs were contended, and this is stated rather than hidden

The brief required the authoritative run to have the box to itself. It did not.
Both full runs executed while other lanes ran pytest gates on the same 4-CPU
container, and the BEFORE run overlapped a second `docs_verify` belonging to
another lane. Two rows are artifacts of that and are NOT findings — both were
re-run serially on the same tree minutes later:

    SUB-application.md:421   TIMEOUT after 300s (loaded)  ->  PASS in 195 s serial
    SUB-application.md:395   1 failed, 1 passed (loaded)  ->  PASS serial

**This paragraph's reasoning was half right and is corrected here.** `:395`
really is load: it costs 23.2 s and 23.0 s in two fresh serial trials
(`proof/sub_application_check_timings.txt`) and has no margin problem at all.
`:421` is NOT the same thing, and blaming foreign load for it was wrong. It
costs 161–213 s across five independent serial timings against docs_verify's
own 300 s ceiling, while the documented command runs `min(16, os.cpu_count())`
= 4 workers on this 4-CPU box — so it self-contends, and needs no other lane
to time out. Passing in three consecutive runs does not settle a row that a
fourth run failed.

`docs/AUDIT_BASELINES.md` now records `:421` as a CONTAINER-CONDITIONAL
expected failure with its measured margin, and states the admissibility rule
in a form this container can actually meet: no full run here has been taken on
a proven-idle box, so a total is admissible only as a RANGE with the
conditional row named, and every delta is disposed of by re-running the
specific failing check alone before it is rowed. The narrowing question is
`PARKED.md` P-D8.

**So the honest failure sets are 9 before and 5-or-6 after**, both on a
shallow clone; 6 and 2-or-3 on a full clone by subtracting the three
git-history rows, which is arithmetic and not a measurement here. The BEFORE
figure of 9 is the loaded run's 10 minus the one contention row, corroborated
by this lane's committed reconnaissance, which measured the same nine ids on
the same tree. The AFTER figure was measured directly three times as 5 (§7.2,
§7.2a) and once, independently, as 6; the sixth row is `:421` and §7.2a says
why both are true.

### 7.4 The other modes — `proof/docs_verify_modes_final.txt`

Re-run after every edit, INCLUDING the post-review round, with each exit code
captured BEFORE any pipe:

    --self-test  rc=0   ok
    --links      rc=0   0 dangling reference(s), 70 document(s)
    --audit      rc=1   1 finding(s): SEAM-llm-x-rules.md:54  (unchanged; out of scope)
    --coverage   rc=1   7 seams swept, 19 without a Sweep: header, 2 finding(s)  (unchanged)

`--audit` and `--coverage` exit non-zero for findings that were already there
and are not this lane's. `proof/docs_verify_modes.txt` holds the same four
modes measured mid-tranche; the numbers did not move between them, and did not
move again after the review round's edits.

`--coverage`'s finding count did not move, which is the condition D1-e had to
satisfy while settling the `Sweep:` ratchet by withholding the header.

Map-wide check counts, measured directly through the parser:

    multi-line checks: 75   (SCHEMA.md's own self-test pins this at >= 70)
    total checks:    1250    documents: 70

The net movement is **+2 checks**: three checks were replaced in place (D1, D3,
D4), one was re-pinned in place (D2), one was added (the twin-pin check in
`INV-frozen-surfaces.md`'s new Traps entry), and one was added in the review
round (the sixteen-form crossing table in `SEAM-llm-x-verification.md`'s new
`Traps` entry, 4.3 s).

### 7.5 Per-check verdicts for `INV-frozen-surfaces.md` — the lane's stop condition

The brief made ANY OTHER PIN MOVING a STOP. Every check in that document was
run serially, one process at a time — `proof/d2_inv_frozen_surfaces_per_check.txt`:

    # 50 checks, 1 failed: [181]

`:181` is the pre-existing `transport_failure` census, deliberately untouched
and bubbled as `PARKED.md` P-D3. Everything else passes, including:

    :297   the frozen-surface branch tripwire            PASS
    :349   SPLIT_BUDGET pops                             PASS
    :422   the shipped qualification subject digest      PASS
    :527   source_config_hash + carriage                 PASS
    :612   qualification subject 02ee7e09 + exclusions   PASS
    :625   061efe5b + ENGINE_CONFIG_FIELD_NOT_CARRIED    PASS
    :661   SPLIT_BUDGET_SEAT_PROTOCOL pop                PASS
    :675   K_FRAME / PROMOTION_ENVIRONMENT_MAX           PASS
    :749   DISCHARGE_POLICY pop at its exact indent      PASS
    :755   6c2d01f6 / 2624603035 by schema version       PASS
    :762   the re-pinned discharge-wire digest           PASS
    :939   the NEW twin check: both pins agree           PASS

Before this lane the same document had TWO reds, `:181` and `:734`. It now has
one. No pin other than the one this lane was granted has moved.

The tripwire deserves its own line because it is the mechanical defence against
an unauthorized frozen-surface contact, and a green tripwire is only meaningful
if `origin/main` resolves:

    git rev-parse origin/main   ->  84514a0280f45d29e5066bb3be3d273ba73798db
    INV-frozen-surfaces.md:297  ->  PASS

### 7.6 Per-check verdicts for the other three targets — `proof/target_documents_per_check.txt`

    SEAM-llm-x-verification.md    4 checks, 0 failed
    CON-discharge-channel.md     21 checks, 0 failed
    INV-signal-contract.md       27 checks, 0 failed

Every one run serially on this tree, after the repairs. Re-run serially again
after the review round, when `SEAM-llm-x-verification.md` gained its fifth
check:

    SEAM-llm-x-verification.md    5 checks, 0 failed   (:36 :149 :198 :262 :306)

### 7.7 `docs/AUDIT_BASELINES.md`

Updated in this lane, per its own rule that it moves in a non-audit tranche in
the same commit as whatever moved the value — never to make a lane green. The
edit REDUCES the expected-failure list from six rows to two, adds a "REPAIRED
2026-08-30 and no longer expected — a failure here is a REGRESSION" paragraph
naming all four so a future audit cannot read the reduction as drift, refreshes
the stale line numbers (`657`→ gone, `222`→ gone, `200/202/204`→`211/213/215`),
refreshes the counts (1212/69 → 1250/70), and records the contention rows above.

The four repaired rows leave the baseline because they were REPAIRED and
measured green, not because a number was edited to match a wish. The two rows
that remain, remain.

**Corrected in the review round, and this is the substantive half.** The first
version of the entry recorded "2 failed on a full clone, 5 failed on a shallow
one" as a fixed value, from ONE observation of an instrument that had returned
four different totals that evening — and it recorded the lowest. It now
records:

- the total as a RANGE, **5 or 6** shallow / 2 or 3 full, because that is what
  the documented command produces here;
- a THIRD expected-failure row, `SUB-application.md:421`, classed
  CONTAINER-CONDITIONAL, carrying its five measured serial timings
  (160.88 / 182.8 / 186.9 / 195 / 213.1 s), the 300 s ceiling it runs against,
  and the worker arithmetic (`min(16, os.cpu_count())` = 4 on 4 CPUs) that
  makes the command self-contend;
- a one-command disposition for that row, so an auditor settles it before
  rowing a delta rather than after;
- every total ever observed on this container, including the two that were
  higher than the one first written down;
- `:395` separated from `:421` as a different class — 23.2 s and 23.0 s
  serially, load-sensitive, no margin problem;
- and an ADMISSIBILITY rule this container can actually meet, replacing "a
  total taken under concurrent load is not admissible as a baseline" — which
  no run here, including the ones behind these figures, has ever satisfied.

The range is not a weakening of the baseline. A baseline whose stated value
the documented command does not reproduce is not a stronger claim than a range
with a named cause; it is a claim that generates false findings on every
future audit run.

---

## 8. The cone, as measured

Measured, not asserted — `git diff --name-only 152c7e204..HEAD`:

    docs/AUDIT_BASELINES.md
    docs/map/CON-discharge-channel.md
    docs/map/INDEX.md
    docs/map/INV-frozen-surfaces.md
    docs/map/INV-signal-contract.md
    docs/map/SEAM-llm-x-verification.md
    docs/map/SUB-verification.md
    experiments/2026-08-30-fix-rotted-map-checks/DELIVERY.md
    experiments/2026-08-30-fix-rotted-map-checks/PARKED.md
    experiments/2026-08-30-fix-rotted-map-checks/proof/*

The review round added three proof artifacts to that list —
`d1_crossing_forms.py`, `docs_verify_replicate_1.txt`,
`docs_verify_replicate_2.txt`, `sub_application_check_timings.txt` — and
touched no document outside `SEAM-llm-x-verification.md`,
`docs/AUDIT_BASELINES.md` and this directory.

**Zero `src/`. Zero `tests/`. Zero `tools/`.** The frozen-surface branch
tripwire passes with `origin/main` resolvable, and no path in the diff matches
any of the seven frozen paths or the frozen-adjacent one. Every mutation in the
review round was run in a scratch mirror of `src/`, and each transcript ends
with `diff -rq` against the real tree plus `git status --short src tests`.

Every mutation proof in this tranche was run in a scratch copy — of `src/`
selected by `PYTHONPATH`, or of `docs/map` with `tests/` symlinked — and each
proof script asserts that the scratch copy is the tree actually imported before
trusting a red. `git status --short src/` was captured at the end of each proof
and is clean in every transcript.

### Verified-at stamps

Advanced to `152c7e204`, the commit whose source tree every re-derivation was
measured against. This lane changes no source, so the stamp names the tree the
claims were checked on:

| document | stamp | what was re-run |
|---|---|---|
| `SEAM-llm-x-verification.md` | `814268b46` → `152c7e204` | all 5 checks, serially (4 before the review round, 5 after) |
| `INV-frozen-surfaces.md` | `a40450f1c` → `152c7e204` | all 50 checks, serially |
| `CON-discharge-channel.md` | `a5a435e3e` → `152c7e204` | all 21 checks, serially |
| `INV-signal-contract.md` | `6c65f95e8` → `152c7e204` | all 27 checks, serially |
| `INDEX.md` | `5f7e413d6` → `152c7e204` | its one check (`--links`), plus the authoritative full run |
| `SUB-verification.md` | `e9fac8671` → `152c7e204` | its 31 checks, in the authoritative full run |

The last two were re-derived by the full run rather than a separate serial pass,
and that distinction is stated here rather than smoothed over.

---

## 9. Bubbled stops

All eight are in `PARKED.md` in this directory, each a ready-to-send prompt,
committed and pushed at the moment they were parked. P-D8 was added, and P-D7
amended, in the post-review round recorded in §11.

| id | what | why it is not decided here |
|---|---|---|
| P-D1 | the frozen-surface road not taken for D1 | pre-selected by the brief; recorded so it is not re-opened |
| P-D2 | ESCALATION: a granted contact moved a digest and the dark map pin was left behind | a disclosure the operator is owed, and an unpaid ~14 min / ~1160 call requalification |
| P-D3 | `INV-frozen-surfaces.md:181`, the falsified `transport_failure` census | a REAL DESIGN FORK: the honest repair changes what a granted contact's safety leg rests on |
| P-D4 | the end-to-end discharge road E56 names as missing | closing F-A is a claim about a road nobody has measured |
| P-D5 | extending `--audit` to catch D4's shape | analysis complete; implementation is a `src/` change |
| P-D6 | `SCHEMA.md` says `--audit` mutates the tree; `cmd_audit` never does | editing the contract every map document is written against is a fifth finding |
| P-D7 | `SUB-llm.md`'s forbidden-package grep omits `invariants`, AND is a dotted-prefix pattern that misses the leaf form for the packages it does name | arguably a separate change; noted in the seam body. Amended after review: its original premise about what else would catch an import was false when written (§11.1) |
| P-D8 | `SUB-application.md:421` costs 161–213 s against a 300 s ceiling, so the documented baseline command self-contends at its own default worker count | narrowing another document's check is a judgment about what someone else's claim is defended by, and that document is not one of this lane's four targets |

---

## 10. Residue — what remains unproven

**Accepted does not mean true.** What this tranche did NOT establish:

1. **The four repairs are proven against THIS tree, not against the future.**
   D1's check pins an exact seven-element crossing set and is brittle by
   design; the document says so, but a future author who widens it carelessly
   turns a strong check into a weak one. That is now PARTLY mechanical, and
   measured rather than asserted (`proof/d1_seam_crossings.txt`, THIRD probe):
   a module-level eighth crossing is red whether or not the widener also
   updates `expected`, because the check separately asserts that exactly ONE
   crossing sits at module level —

       M1  module-level 8th crossing, `expected` NOT widened      rc=1
       M2  SAME crossing, `expected` dutifully widened to match   rc=1

   — so following the documented widening procedure does not buy a silent
   falsification of the body's "one at module level" or of `INDEX.md`'s matrix
   score of 1. A careless widening that adds a FUNCTION-LOCAL crossing still
   has only the author's own care standing behind it.

1b. **D1's enforcement was over-claimed once already, and the correction is
   §11.1 rather than a footnote.** The first replacement check missed nine of
   sixteen import forms, including the one `src/` uses 29 times. The state
   claim survived unchanged; the enforcement claim did not, and the reason it
   was not caught in-lane is recorded: the mutation set planted only the form
   its author had in mind. The sixteen-form table is now itself a check, which
   removes this particular blind spot and no other.

2. **The full-clone figure (2 failed) is arithmetic, not a measurement.** No
   full clone was available. `git fetch --unshallow` was deliberately not run.
   Anyone quoting "2 failed" without saying which clone shape it came from is
   quoting a derivation.

3. **NO full run of this instrument on this container has been uncontended,
   and the total is not a single number.** Every run recorded here — five of
   them now, plus one by an independent reviewer — was taken while at least
   one other lane worked on the same 4-CPU box. More importantly, the
   documented command SELF-contends: `SUB-application.md:421` costs 161–213 s
   serially against docs_verify's own 300 s per-check ceiling, and the command
   runs 4 workers here, so that row can time out with no foreign load at all.
   The baseline therefore records 5 **or** 6 on a shallow clone with `:421` as
   a container-conditional row and a one-command disposition, rather than
   asserting the lowest observation. Calling any of these runs a "quiet box"
   — as commit `7fbbf2bc2`'s message did — was wrong, and §11.3 corrects it.
   A genuinely uncontended run still belongs to fan-in, and the BEFORE figure
   of 9 still rests partly on subtraction plus the committed reconnaissance
   rather than on one clean measurement.

4. **D3 proves ONE link of the discharge road.** The compile → echo → rebuild
   round trip carries the configured value. The road `ERRATA` E56 names as
   missing — a configuration file, through `start_manifest_run`, to a scheduler
   that resolves the preset — is still unmeasured, and
   `experiments/2026-08-26-pc2-rematch/PARKED.md` F-A is still OPEN. Nothing
   here closes it (`PARKED.md` P-D4).

5. **D4's claim is about the `Scheduler` class only.** The check reads
   `inspect.getsource(Scheduler)`. Module-level code in `scheduler.py` outside
   the class is not covered, and was not covered before either. Widening it was
   not part of the repair and is not claimed.

6. **The D2 requalification cost is unpaid.** The digest moved on 2026-08-28
   and the next live run against a home qualified before then pays ~14 minutes
   and ~1160 provider calls. This lane is offline; nothing here spends it or
   proves it is the only cost.

7. **`INV-frozen-surfaces.md:181` is still red** and this lane did not touch
   it. The expected-failure table still carries it. Repairing it is a judgment
   about what a granted contact's safety argument rests on, bubbled as P-D3.

8. **`SEAM-llm-x-rules.md:54` is still unparseable**, so
   `docs_verify --audit` still exits non-zero. Any workflow phase demanding
   "--audit reports 0 findings" is still unachievable, and must record this
   pre-existing finding rather than treat it as its own failure.

9. **Three findings in `docs/map` were REPORTED and not fixed**: `SCHEMA.md`
   describing an `--audit` behaviour its own tool does not have (P-D6),
   `SUB-llm.md`'s forbidden-package grep (P-D7, now with both of its holes
   named), and `SUB-application.md:421`'s cost against the check ceiling
   (P-D8). All three are real; all three are outside the four this lane was
   given.

11. **`proof/d1_sweep_probe.py`'s measurement is now reproducible; it was not
    before.** The `candidates=4 enforcement=0` figure that justifies
    withholding the `Sweep:` header was, until this round, produced by a
    script that read a hardcoded worktree path — so it measured lane-D no
    matter where it ran, and would have died outright once that worktree was
    removed. It is anchored now and proven to see its own tree (§11.4). The
    figure itself did not move.

10. **No live evidence of any kind.** This batch is offline by construction —
    no `OLLAMA_API_KEY`, no `env` file, no run root touched or created. Every
    number here comes from `docs_verify`, `pytest` through a check, or a
    scratch-copy mutation.

---

## 11. What independent review found, and what was done about it

Three reviewers re-ran this lane's claims after delivery `7fbbf2bc2`. They
confirmed three MAJOR defects and four minor ones (two of the minors were the
same defect found twice). Nothing they found was refuted; every finding
reproduced on first attempt. This section is the honest ledger of that round —
what was wrong, what changed, and what is still not claimed.

### 11.1 MAJOR — D1's crossing check enforced two import forms out of six

**The finding.** `SEAM-llm-x-verification.md` said `llm/` names the
verification side "NOWHERE, in any form, absolute or relative"; §2 of this
document said "0, in every form"; `PARKED.md` P-D7 rested on "the only thing
that would now catch a new import is this check". The check's `crossings()`
helper resolved an `ast.ImportFrom` by testing `node.module` against the
prefix list, and never tested `module + '.' + alias.name`. A package member
imported BY NAME therefore resolved to bare `deepreason` and matched nothing.

**Why it mattered rather than being a technicality.** That form is the repo's
own dominant idiom: `from deepreason import <module>` appears **29 times
across 24 files** in `src/`, and `src/` contains **zero** relative imports, so
a real reverse crossing written the way this codebase writes imports would
have walked straight through the guard. The forward direction had the same
hole, so the "pinned EXACTLY" seven-element set could be widened silently too.

**What was NOT wrong.** The state claim. The reverse direction was empty then
and is empty now, re-confirmed by AST under all sixteen forms. What was
over-claimed was the ENFORCEMENT — which is precisely the property §2 sold as
the value of the repair, so the over-claim is the important half.

**The repair.** `crossings()` now resolves each alias BOTH ways — the module
path first, then `mod + '.' + alias.name` — and records a fourth tuple
element saying whether the import sits at module level. That flag pins two
counted claims that nothing checked before: the body's "one at module level,
five inside the functions", and `INDEX.md`'s matrix score of 1 for this pair.

**The proof, and why the original proof was not enough.** The first mutation
set planted three forms, all DOTTED — the shape its author had in mind. The
replacement is a sixteen-form table, committed as
`proof/d1_crossing_forms.py`, run as a check of its own from the seam's
`Traps` section, and anchored to its own file location so it re-derives
anywhere:

    committed check (7fbbf2bc2)   16 forms planted,  9 MISSED   script exit=1
    repaired check                16 forms planted,  0 MISSED   script exit=0

The nine the committed check missed: `from deepreason import invariants`,
`from .. import invariants`, the same two for `verification`, the same for
`signals_read`, two function-local variants (one planted in a real `llm/`
file), the forward `from deepreason import llm`, and hoisting
`verification/report.py`'s crossing to module level. Full transcript, both
directions, in `proof/d1_seam_crossings.txt` under the 2026-08-30 SECOND ROUND
heading.

**Prose corrected rather than narrowed.** "In any form" still stands, because
the check now covers the forms. A paragraph beneath the check states that "in
any form" is a claim about the RESOLVER and says what it cost; a new `Traps`
entry records the defect with its lesson — *a mutation set that plants only
the form the author had in mind measures the author, not the check*.

**P-D7 amended, not quietly fixed.** Its premise was false when written. The
entry now says so, and carries a SECOND hole the same review exposed:
`SUB-llm.md`'s negative grep is itself a dotted-prefix pattern, so widening
its package list alone would not catch the leaf form either. Both holes are in
the prompt.

### 11.2 MAJOR — the docs_verify baseline rested on one unreplicated observation

**The finding.** `docs/AUDIT_BASELINES.md` recorded "2 failed on a full clone,
5 failed on a shallow one". The first independent run of the documented
command on the same branch returned **6**, with `SUB-application.md:421`
reporting `TIMEOUT after 300s`. Counting this lane's own three runs, the
instrument returned four different totals in one evening — 10, 7, 5 and 6 —
and the lane wrote the single LOWEST observation into a precedence-2 authority
whose own table says "a delta from THIS list is a finding".

**The reviewer also killed this lane's excuse.** §7.3 attributed the `:421`
timeout to foreign load. It measured `:421` at 213.1 s serially against
docs_verify's own 300 s ceiling — a 1.4x margin — while the documented command
runs `min(16, os.cpu_count())` = **4** workers on this 4-CPU box. The
documented command therefore SELF-CONTENDS: no foreign gate is required for
that row to time out.

**What was measured in response**, five independent serial timings of `:421`
across two days on this container:

    160.88 s   2026-08-29, idle box        (this lane, recorded 2026-08-29)
    182.8  s   2026-08-30                  (this round, trial 1)
    186.9  s   2026-08-30                  (this round, trial 2)
    195    s   2026-08-30                  (this lane, first round)
    213.1  s   2026-08-30                  (independent reviewer)

54% to 71% of its own ceiling before it shares four CPUs with three other
checks. `:395`, the other contended row, cost 23.2 s and 23.0 s in the same
pair of trials — it is not in the same class and its earlier failure really
was load.

**What changed in the baseline.** See §7 below, rewritten. In one sentence:
`SUB-application.md:421` is now recorded as a CONTAINER-CONDITIONAL expected
failure with its measured margin and its disposition command, so the baseline
states what the documented command actually produces here — 5 **or** 6 on a
shallow clone — instead of the luckiest of four observations. Two fresh full
runs were taken and BOTH are recorded, not the lower.

**What was NOT done, and why it is parked.** The reviewer's alternative repair
was to narrow `:421` to the claim it tests. That check belongs to
`SUB-application.md`, which is not one of this lane's four targets, and
narrowing it is a judgment about what someone else's claim is defended by —
exactly the kind of decision this batch's rules say to bubble. It is
`PARKED.md` **P-D8**, with the five timings, the arithmetic, the constraint
that the narrowed set must be shown RED on the reverted code shape, and the
two alternatives (pin a worker count; raise the ceiling) priced.

### 11.3 minor — "quiet box" was a label the record did not support

Commit `7fbbf2bc2`'s message called its final measurement "(quiet box,
complete tree)" while residue item 3 of this document, added in the same
commit, said of that same run "It is NOT proof that the box was idle: other
lanes were still working", §7.3 said "The brief required the authoritative run
to have the box to itself. It did not", and the `AUDIT_BASELINES.md` edit in
the same commit stated that "a docs_verify total taken under concurrent load
is not admissible as a baseline". The commit recorded a baseline from a run it
simultaneously declared inadmissible.

**Corrected here, as an honest-ledger entry rather than a re-measurement.**
A commit message cannot be amended once pushed, so it is corrected in place:
that measurement is described everywhere in this document and in
`AUDIT_BASELINES.md` as **materially quieter, not proven idle**, and
`AUDIT_BASELINES.md` now says beside the figures what load they were taken
under. The reviewer was right that the two statements could not both stand.

### 11.4 minor — a committed proof script that could not be re-derived anywhere else

`proof/d1_sweep_probe.py` hardcoded `REPO = pathlib.Path('/home/user/dr-lanes/
lane-D')` — an ephemeral worktree. Run from any other checkout it silently
measured the lane worktree instead of the tree under audit; once the worktree
is removed at fan-in it raises `FileNotFoundError`. In a repo whose documents
are authenticated by re-derivation, that is a stale stamp with a shebang.

Fixed: `REPO = pathlib.Path(__file__).resolve().parents[3]`. Proven, not
asserted — a real enforcement site was planted in a scratch mirror of the tree
and the script was run FROM that mirror:

    same planted mirror, committed (hardcoded) probe   candidates=4 enforcement=0
    same planted mirror, anchored probe                candidates=5 enforcement=1
    hardcoded probe with the worktree gone             FileNotFoundError
    anchored probe, real tree, from repo root and /    candidates=4 enforcement=0

The `candidates=4 enforcement=0` measurement that justifies WITHHOLDING the
`Sweep:` header (D1-e) is therefore reproducible after merge, which it was not
before. `proof/d1_sweep_candidates.txt` is unchanged because the fixed script
returns the same values on the real tree — that identity is the point of the
last row above.

`proof/d1_crossing_forms.py`, new in this round, is anchored the same way and
was run from two different working directories to prove it.

### 11.5 minor — the module-level split was pinned for one file only

Moving `verification/report.py`'s `route_fingerprint` import from
function-local to module level left the check GREEN while two claims written
in the same commit became false: the body's "one at module level, five inside
the functions", and `INDEX.md:122`'s matrix score of 1, which counts
module-level imports only. Fixed by the fourth tuple element described in
§11.1 — the split is now pinned for every crossing on the verification side,
not just for `invariants.py`. Mutations S1 (hoist `report.py`'s) and S2 (sink
`invariants.py`'s) are both RED in the sixteen-form table; S1 was GREEN
before.

A third probe was run because the reviewer's finding implies a second failure
mode the sixteen-form table does not reach: a widener who ADDS a module-level
crossing and dutifully updates `expected`, exactly as the document's own
instructions say to. The count assertion catches that too — both M1 (widened
tree, unwidened `expected`) and M2 (both widened) are RED. Recorded in
`proof/d1_seam_crossings.txt` under THIRD probe, with the scratch mirror of
both `src/` and the document restored and re-verified GREEN afterwards.

