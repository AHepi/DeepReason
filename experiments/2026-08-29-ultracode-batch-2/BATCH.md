# BATCH.md — the 2026-08-29/30 ultracode batch 2

Orchestrator manifest. Five lanes, each in its own git worktree on its own
branch, integrated SERIALLY into `claude/deepreason-ultracode-batch-2-l9vj55`.
Setup baselines, measured before any lane started, are in `SETUP.md`; the
committed reconnaissance every lane implemented from is in `recon/`.

**Three lanes are DELIVERED and integrated. One is PARKED with its road built.
One was HANDED OFF mid-batch at the operator's instruction.** Nothing was
worked around, no assertion was weakened, and NO frozen surface was touched by
any lane — the batch changed exactly ONE source file in total.

**The batch's main result held for a third program running.** Every lane that
faced independent skeptics shipped work that passed its own review and its own
green checks and was still wrong. Lane C shipped a map check that could not
fail for the reason its prose gave. Lane D's baseline did not reproduce and its
new import check missed the form `from deepreason import invariants`, live 29
times in `src/`. Lane E cited a cross-arm measurement that was not in the
transcript it cited. Lane A shipped docstrings asserting a gate it had
reverted. Every one was found by a skeptic RE-RUNNING the claim, never by
reading it.

---

## 1. The manifest

| Lane | Tranche | Verdict | Cone (measured) | src/ touched | Gate evidence |
|---|---|---|---|---|---|
| **D** | `2026-08-30-fix-rotted-map-checks` | **DELIVERED, integrated** | 27 paths | **none — docs/map only** | 4 rotted checks repaired, each shown failing on the broken form and passing on the repaired one; every check in `INV-frozen-surfaces.md` re-run SERIALLY (50 checks, 1 pre-existing failure); expected-failure list reduced and re-baselined in this lane's own commit |
| **E** | `2026-08-30-change-execution-safety-parks` | **DELIVERED, integrated** | 17 paths | **none — tests + docs only** | 10 confession-shaped assertions replaced by 7 differentials, 5 of them two-armed, each mutation-proven RED against a weakened condition; ring 55 passed |
| **A** | `2026-08-30-change-checkpoint-hardening` | **PARTIAL, integrated** | 35 paths | `application/text_runs.py` (the batch's only source change) | ring #4 207 passed 0 failed; 2 blocking skeptic findings fixed; limb three PARKED as F9 with a measured acceptance target |
| **C** | `2026-08-30-defect-formalism-rank-penalty` | **PARKED, NOT integrated** (road built) | 31 paths | `scheduler/scheduler.py`, `capture/pareto.py` — on branch `claude/b2-lane-C` only | 11 tests RED before / GREEN after on its own branch; both architecture tests mutation-proven; `drop_road_a.sh` makes landing or discarding it one verified act |
| **B** | `2026-08-30-change-successor-questions` | **HANDED OFF** to a fresh window (operator instruction, mid-batch) | 36 paths | `llm/contracts.py`, `llm/wire.py`, `ontology/problem.py`, `signals.py`, new `successor/` — on branch `claude/b2-lane-B` only | 42 tests pass with `PYTHONPATH` at its own `src/`; ONE test RED by design, gated on operator question Q5; **no skeptic pass ran** |

Integration order was D, E, A — cheapest first, so a late failure could not
strand finished work. C and B are not integrated; see §3 and §4.

### Fan-in evidence, measured on the integrated tree, one instrument at a time

    full gate      python -m pytest tests/ -q -n 4
                   -> 4495 passed, 6 skipped, 0 failed in 1238s
                   (baseline 4486 at batch-1 close; +9 from new tests)

    docs_verify    python tools/docs_verify.py          [FULL, not --fast]
                   -> 70 documents, 1253 checks, 5 failed
                   -> DELTA FROM BASELINE: ZERO

    ring           93 passed, 0 failed across every lane's own test files

The 5 docs_verify failures are the baseline list exactly: `SEAM-llm-x-rules.md:54`
(malformed check, parked P3), `INV-frozen-surfaces.md:181` (the falsified
transport_failure census, parked P-D3), and the three `CON-run-identity.md`
git-history checks that a SHALLOW clone cannot satisfy — this container reports
`git rev-parse --is-shallow-repository` as `true`, and `docs/AUDIT_BASELINES.md`
records those three as not-findings on such a clone. The sixth
container-conditional row (`SUB-application.md:421`, a check that costs 54-71%
of its own 300 s ceiling before sharing 4 CPUs) passed this run; the baseline
records the total as 5 OR 6 for exactly that reason.

**All four of lane D's repaired checks are ABSENT from the failure list**, which
is the point of that lane: the repairs held on the integrated tree, not only on
lane D's own.

### Frozen surfaces — none touched, and the tripwire says so

    git diff --name-only origin/main...HEAD | grep -E "capabilities/state\.py|/harness\.py|/invariants\.py|/run_manifest\.py|/qualification\.py|llm/firewall\.py"
    -> (no output)

    git diff --name-only origin/main...HEAD | grep '^src/'
    -> src/deepreason/application/text_runs.py        (the only one)

**On the `INV-frozen-surfaces.md:297` branch tripwire.** The batch instruction
forecast that it would fire "if lane A or B touches nothing frozen but lane D
edits that file". It does NOT, and the reason is worth recording rather than
filing down. The tripwire greps the branch's changed-FILE-NAME list for six
frozen SOURCE paths; `docs/map/INV-frozen-surfaces.md` matches none of those
six regexes, so editing the document that HOSTS the tripwire does not trip it.
It stays green because no lane touched frozen source — which is the property it
exists to assert. Measured at every integration step and again at fan-in: PASS.

Two limits of that instrument, recorded so a green reading is not over-read:
it cannot see `src/deepreason/verification/` (also frozen surface 3) because
that path is not in its regex — checked separately here, and empty; and a green
tripwire is a write boundary, never an authorization.

---

## 2. What each delivered lane actually changed

**Lane D — four rotted map checks.** D1: the `llm x verification` seam claimed
"no import in either direction". False in one direction — 7 symbol crossings
across 6 statements verification->llm (`invariants.py:21` at top level plus four
function-local, and one in `verification/report.py`), and genuinely 0 the other
way. The seam now states the measured ASYMMETRIC relationship and pins the
crossing set in BOTH directions, including the empty one so it stays empty.
D2: the discharge-wire qualification subject digest re-pinned `b9038b84` ->
`02ee7e09`, with the trace recorded AT the pin site (moved 2026-08-28 in
`e9457f8ff` under the operator's conditional grant; two committed test pins were
updated and this dark map pin was missed), plus a new check that goes red if the
document's two pins ever disagree again — the property whose absence caused the
defect. D3: the discharge check's fixture rebound to the toolchain the policy
names. D4: the wander-registry check rebound to code via `ast.unparse`, so a
comment explaining the decoupling no longer defeats the check proving it.

**Lane E — execution safety.** E1 (P4): the containment tests asked the sandbox
to describe itself. A test that asks the sandbox what it is will believe a lie,
and that is how the original escape survived a committed proof. Ten
confession-shaped assertions are gone; seven differentials observe the EFFECT —
network denial per independently probed prefix, worker argv, scratch cwd/env/
teardown, an rlimit read back out of a real child, both environment scrubs.
E2 (P6): the fresh-container install gap is documented where CLAUDE.md's
Environment section is read, and the stale `~3100 passed` baseline now points at
`docs/AUDIT_BASELINES.md` as the living source so the number cannot rot again.

**Lane A — checkpoint hardening, PARTIAL.** What shipped is limb two, in part: a
failure terminal now records TYPED why it cannot be continued instead of being
silent — the operator's "corrupted stop". What did NOT ship is limb three, and
§3 states that plainly.

---

## 3. The security clause is OPEN, and the batch says so

The operator's P2 law carries a security sentence: *"I don't want a jailbroken
run to be continuable."* **That clause is not satisfied by this batch.**

Lane A built the continue/amend integrity gate, measured eight ring collisions
where its own spec predicted one, and reverted it under its own pre-registered
stop rule. Three independent skeptics then found that shipped docstrings and a
shipped reader still asserted the gate existed — and that S7, which HAD shipped
on that reverted premise, made `deepreason results --verify` print a FALSE
readiness verdict on exactly the population the law is about. S7 was therefore
reverted too; `results.py` and its test are byte-identical to `origin/main`.

The exposure is measured, not estimated, and committed as a re-runnable
instrument (`proof/forge_amend_ready.py`): forging ONE BYTE of a committed
amend-ready root's log makes `verify_root` report two SECURITY-channel
violations, and **both `amend` and `continue` still accept it**
(`jailbreak_open: True`). F9 is done when that reads `False`.

This is the batch's largest gap between what was asked and what was delivered,
and it is recorded here rather than softened.

---

## 4. The two lanes that are not integrated

**Lane C — PARKED on an operator fork, road built.** The batch asked for both
unlawful-penalty sites fixed. The brief the batch designated as its authority
says otherwise in its own words: site (a) needs an *"OPERATOR DECISION NEEDED
FIRST"* with three roads priced, and site (b) says *"do not design before it is
answered"*. Both are real design forks, which park rather than resolve.

The lane made the decision as cheap as possible to make. It re-measured the
defect at HEAD rather than inheriting the audit's numbers (233 survivors in
exactly two score triples, 146 informal at (0,0,0), 87 formal at (0,0,1),
frontier == the 87, zero of the 146 on it — the brief CONFIRMED in every
particular). It built the law-based narrowing as a RUNNABLE instrument
(`road_law_probe.py`): only road (a) passes all four probes derived from R-g's
own clauses; road (c) fails because a disclosure describes the disadvantage
instead of removing it. And it built road (a) with 11 tests RED-before/
GREEN-after, in a commit whose subject begins "BUILT AND PARKED, NOT
INTEGRATED", with `drop_road_a.sh` making the discard a single verified act.

Branch `claude/b2-lane-C` at `039cac0ae`, pushed. The operator's "yes" is a
merge; their "no" costs nothing.

**Lane B — HANDED OFF mid-batch at the operator's instruction.** Branch
`claude/b2-lane-B` at `fdfe8a6e4`, pushed, clean tree, full artifact set, and no
frozen contact — it found a lawful road avoiding `run_manifest.py`, so the
frozen-surface-4 grant it forecast was requested but not needed.
`HANDOFF-lane-B.md` carries what is done and what is not; the decisive item is
that **no adversarial skeptic pass ran on it**, so its claims are self-reported.
One test is RED by design, gated on operator question Q5, and the branch cannot
be integrated while it is.

---

## 5. Bubbled STOPS, by lane

Every one is committed as a ready-to-send prompt in its tranche's `PARKED.md`,
and pushed at the moment it was parked.

| id | lane | what it needs |
|---|---|---|
| F9 | A | the integrity gate itself — limb three. Acceptance target measured: `forge_amend_ready.py` must read `jailbreak_open: False` |
| F1 | A | does "every terminal leaves checkpoints sufficient for relaunch" require failure terminals to become RESUMABLE? Overturns owner decision 4a of 2026-07-27 — an operator call |
| F2, F3 | A | limb one's unshipped half (`WorkBudgetDenied` still terminates `operational_failure`, proven on two committed roots) and a second corrupted-stop path in `Scheduler._record_stop`. Both outside the granted cone |
| F4 | A | "unresolved containment-breach evidence" names a record type that DOES NOT EXIST — 77 `containment` hits in `src/` are all limits, timeouts or free-text traces. Creating it enters frozen surface 3 |
| F10 | A | the third exit of `_worker`'s except block records nothing; not fixed because `deepreason finalize` recovers that root, so a typed "cannot continue" would be a second wrong record |
| P-D3 | D | `INV-frozen-surfaces.md:181`'s falsified census — its honest repair changes what a 2026-08-25 grant's second safety leg rests on |
| P-D5, P-D6 | D | extending `--audit` to catch D4's shape (analysis complete: `_VACUOUS` CANNOT be stretched — it detects checks that cannot fail, D4 is a check that fails on a TRUE claim); and `SCHEMA.md` claiming `--audit` mutates the tree when `cmd_audit` never mutates and never executes |
| L1, L2 | C | the coverage-axis road (a/b/c, law narrows it to two) and P3, the prose-criticism penalty, carried forward verbatim |
| Q1–Q5 | B | the five-question operator block, Q3 the decisive one |

---

## 6. The residue, stated plainly

1. **The security clause is open** (§3). This batch hardened what a stop
   RECORDS; it did not gate what `continue` and `amend` ACCEPT.
2. **Lane B is unverified by any independent pass** and carries one red test.
3. **Lane C's fix is built but not landed**, and correctly so — the operator
   owns that fork.
4. **No live run was performed anywhere in this batch.** It is offline by
   construction: no API key exists in this container. Every claim here is an
   offline measurement, and no lane may be read as carrying live evidence.
5. **`docs_verify`'s total is container-conditional** (5 or 6 on a shallow
   clone, 2 or 3 on a full one). The baseline says so; a single observation of
   this instrument is not a baseline, which is a correction lane D had to make
   after review.
6. **The batch changed one source file.** That is a fact about what was
   ASKED — three of five lanes were docs, tests and map work — not evidence of
   thoroughness on its own.
