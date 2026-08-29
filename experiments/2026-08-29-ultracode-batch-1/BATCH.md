# BATCH.md — the 2026-08-29 ultracode batch

Orchestrator manifest. Four lanes, each in its own git worktree on its own
branch, integrated SERIALLY into `claude/deepreason-ultracode-batch-7j6vqe`.
Setup baselines, measured before any lane started, are in `SETUP.md`.

**Three lanes delivered and are integrated. Two tranches are WITHHELD on
operator decisions — both stopped on the same mechanized instrument, neither
waived.** Nothing was worked around, no assertion was weakened anywhere, and
no frozen surface was touched.

---

## 1. The manifest

| Lane | Tranche | Verdict | Cone (measured) | src/ touched | Gate evidence |
|---|---|---|---|---|---|
| **A** | `2026-08-28-change-premise-invitation-reachability` (P11) | **DELIVERED, integrated** | 21 paths | `premises.py`, `rules/crit.py`, `signals.py` | full gate on merged tree **4443 passed, 6 skipped, 0 failed**; docs_verify 4 failed = baseline, delta zero; ring after integration 54 passed |
| **D** | `2026-08-29-change-seam-capabilities-x-channels` (P5) | **DELIVERED, integrated** | 13 paths | **none — docs only** | `--audit` 0 findings; `--links` 0 dangling over 70 documents; all 33 check lines of both touched documents run by hand, 0 failed; ring after integration 56 passed |
| **B1** | `2026-08-29-defect-managed-path-config-read` (P14) | **DELIVERED, integrated** (gap closed post-verification) | 45 paths | `preparation.py`, `cli/main.py` (75 insertions, diff budget WITHIN 150) | ring 172 passed, 0 failed; blast-radius ring 219 passed, 1 skipped; 6 of 6 committed digest pins UNMOVED |
| **B2** | `2026-08-29-change-config-carriage` (P15) | **WITHHELD — operator stop** | not integrated | — | work complete and green; implementation uncommitted, preserved as `proof/implementation.patch` |
| **C** | `2026-08-29-defect-qualification-circuit-breaker` (P7-A) | **WITHHELD — operator stop** | 26 paths on its branch | `cli/doctor.py`, `llm/endpoints.py` | full gate on its branch **4451 passed, 6 skipped, 0 failed**; 13 mutations, one per regression test |

Integration order was D, A, B1 — cheapest first, so a late failure could not
strand finished work. C and B2 were not integrated; see §2.

### Frozen surfaces — the grant was forecast and NEVER USED

    git diff --name-only origin/main...HEAD | grep -E "capabilities/state\.py|/harness\.py|/invariants\.py|/run_manifest\.py|/qualification\.py|llm/firewall\.py"
    -> (no output)

Surface 4 (`run_manifest.py`) was forecast for B2 and granted conditionally.
B2 is withheld and its implementation is uncommitted, so no committed history
on this branch touches any of the seven frozen paths. **`SETUP.md`'s forecast
of a fifth `docs_verify` failure from the `INV-frozen-surfaces.md:297` branch
tripwire is therefore RETIRED — the tripwire correctly stays green.** The
forecast was honest when written and is wrong in outcome; recorded rather than
deleted.

---

## 2. Bubbled STOPs — both are yours, neither was waived

Both lanes stopped on `tools/diff_budget.py`, which `dr-implement-fix` step 8
types as a STOP decided above the lane, with a recorded precedent (V1 tranche
2026-08-05: 193 insertions landed against a <=150 ceiling with no stop). The
orchestrator verified the instrument is real and committed before honouring
the stops.

### STOP 1 — Lane C, `.../STOP.md`

**323 inserted lines against a 150 ceiling. `diff_budget.py` verdict:
EXCEEDED.**

The scope never moved: every added line sits inside a change site `FIX.md`
already enumerated, and the file cone never changed. What overshot is the
ESTIMATE — `FIX.md` guessed `cli/doctor.py` at ~78 lines; the real figure is
216, most of the gap docstrings and the constraint comments CLAUDE.md
requires. `FIX.md`'s own declared contingency (drop the per-endpoint keying)
was MEASURED and does not work: it saves ~6 of the 173 lines needed and makes
the fix strictly worse, because one dead route would then stop the battery
measuring every other. `STOP.md` prices four roads.

The work itself is finished and green: full gate 4451 passed / 0 failed, 13
mutations one per test, both directions pinned (an account-level refusal trips
the breaker; a transient 429 that clears does not), the opt-out restores the
old exhaustive behaviour with a typed warning, and two architecture tests go
red if changing the behaviour ever needs a code edit.

### STOP 2 — Lane B2, `.../STOP.md`

**Source 94 lines against a 90 ceiling; source+tests+map 513 against 420.
EXCEEDED on both.**

Traces to one planning miss, not scope creep: the spec itemised three change
sites and missed a small helper. **Carriage costs NO requalification.** The
gate sits BEFORE the implementation commit by design, so the implementation is
deliberately uncommitted and preserved as `proof/implementation.patch`
(`git apply --check` verified clean at HEAD) — one command restores it.

### The priced decision underneath both — carriage of the 22 switches

Measured on all 8 committed operator configs (`probe/price_qualification.py`),
with a control row proving a defaults-only configuration is byte-identical to
today (that control caught and killed one measurement artefact before it could
be reported as a cost):

| road | carries | configs whose fingerprint moves | cost |
|---|---|---|---|
| **A — narrow** | the 25 settings the echo already drops | 7 of 8, all to ONE fingerprint | one battery per home that sets `LEGACY_CRITICISM_ENABLED: false`; **zero for every other switch** |
| **B — full** | the whole config file bar 7 profile-owned fields | 8 of 8, four fingerprints | one battery per home per distinct config |
| **C — warn only** | nothing | 0 of 8 | zero — and still cannot turn a gate ON |

**23 of the 24 reachable switches carry FREE**, including
`JUDGE_SEATS_ENABLED`, `ADJUDICATION_STATUS_AUTHORITY_ENABLED` and
`SCHOOL_SEATS_ENABLED`. Exactly one is priced: `LEGACY_CRITICISM_ENABLED=false`,
because `preparation.py:493-512` then compiles an engaged criticism policy onto
the manifest. Lane B recommends road A. Nothing is paid retroactively; no
committed manifest is recompiled.

---

## 3. What adversarial verification changed, and why it is the batch's main result

Every lane was re-checked by independent skeptics under two lenses (mutation;
discipline) that re-ran the lane's claims rather than reading its prose. **Two
lanes shipped work that passed their own review, their own green checks and a
green gate, and were still wrong.**

### Lane D — six falsified claims in a brand-new map document

A map document here is authenticated by RE-DERIVATION: every load-bearing
claim carries a shell `check:` that must exit 0. The document had ten green
checks and was wrong in six places:

1. **False.** It attributed a role to `disabled_channels()` and
   `unknown_channel_notices()` ("serve reporting and compile notices"). A
   repo-wide grep finds **no production caller of either**.
2. **False.** A census sub-claim named a check among five that never run; that
   check is single-line and does run. The five that genuinely never run are
   lines 55, 72, 89, 107, 124.
3. **Overclaim.** Its first check was named as the tripwire against a
   capability controller reading run configuration. The check pins IMPORT
   ARROWS; an INDIRECT read (importing a policy-builder instead) reopens the
   exact audit failure — compiled manifest says research OFF, controller says
   ON with budget 6 — and **all ten checks stayed green**.
4. **Overclaim.** The Traps check was strings-only. Deleting the guard
   reddened it; INVERTING it (the same defect pointed the other way) left
   every check green.
5. **Vacuous evidence.** A `--coverage` zero offered as proof of completeness.
   Recomputed by hand: three candidate files, **zero enforcement sites** — the
   sweep cannot produce a finding here whatever the document says.
6. **Stale.** The narrative framed the echo drop through the old audit's
   silence, without noting the P10 fix (`a40450f1c`, in this tree) now types
   and discloses that exact drop.

All corrected, plus a **seventh found while correcting** (a Traps entry told
readers to consult a compile notice that nothing emits). No check deleted or
weakened; checks went **10 -> 15** on the seam and **17 -> 18** on
`SUB-capabilities.md`, each new or changed check proven RED under mutation and
GREEN after restore BEFORE being written down — twelve mutations, transcript
committed. Mutations ran on an isolated byte-copy of the tree, verified
byte-identical afterwards.

### Lane B1 — correct code with zero regression protection

Inserting `return None` at the top of `_load_operator_config` reinstates
defect P14 exactly. The whole 8-file blast-radius ring returned **217 passed,
1 skipped — byte-identical to clean.** Nothing went red anywhere.

Structural, not a missed assertion: one test monkeypatched
`RunPreparationService` wholesale (so it could only see the config path
ARRIVE, never what `prepare()` did with it); the other seven called the
builders directly, bypassing `prepare()`. **No test crossed the join that IS
the fix.** Change site 7 (`_qualify_one_profile`, the operations-parity limb
the fix's own commit message calls load-bearing) had no test at all —
`grep -rln "_qualify_one_profile" tests/` returned nothing. And a map check at
`SUB-application.md:214` stayed green with that site deleted: a check that
could not fail.

Closed by **tests only** (`git diff --name-only a4f0d3ce2..HEAD -- src/` is
empty), then re-verified by a second independent pass that re-ran both
mutations (1 failed / 218 passed each), confirmed the eight pre-existing tests
are blind to both (8 passed, 2 deselected), and added **six mutations of its
own**:

| mutation | caught? |
|---|---|
| `_load_operator_config` returns a defaults `Config()` | CAUGHT |
| `prepare()` compiles configured but qualifies UNCONFIGURED | CAUGHT (`QUALIFICATION_SUBJECT_MISMATCH`) |
| shared builder silently drops its `config=` argument | CAUGHT (3 tests) |
| revert change site 6 (`_cmd_reason`) | CAUGHT |
| innocuous refactor control | correctly stays green |
| **partial read — keeps only the 2 fields the new tests assert on** | **MISSED** |
| **swallows the typed `CONFIG_PROFILE_INVALID` refusal** | **MISSED** |

The two misses are recorded below as findings, not papered over.

### A merge that would have broken the branch

Lane B's branch TIP carries B2's regression suite committed deliberately RED
(commit `1117bf736`) with its implementation uncommitted. Merging the tip
would have put **10 permanently-failing tests** on the session branch. The
discipline lens caught it. B1 alone ends at `a4f0d3ce2`; an isolated worktree
was built at exactly that commit and only that history was merged.

### Non-load-bearing findings recorded rather than dropped

- **Lane A** summary claims `+81/-16` source lines; measured is `+73/-8` (its
  own `DELIVERY.md` says 73). False as stated, changes nothing.
- **Lane A** touched a third source file, `signals.py`, beyond the dispatch's
  enumerated cone — disclosed in advance (`SPEC.md` S3, `CHECKLIST.md` step 6)
  and contract-forced, because the new `premise-answer:` tag must be declared
  in the signal registry. Not a breach; recorded because the enumeration did
  not name it.
- **Lane C** claims 13 mutations "each reddening exactly its own test"; run
  without the `-k` filter, M1 reddens seven. Conservative error — more tests
  detect it, not fewer.
- **Lane D** `proof/cone.txt` recorded 7 paths against a 12-path diff;
  regenerated.

---

## 4. Parked findings — every one, none fixed in-batch

Numbering continues the run-problems audit and the P10 tranche; collisions
with parallel windows are noted where they occurred.

### From Lane B (10)

| id | finding |
|---|---|
| **P17** | `docs/map/INDEX.md` declares itself the map's entry point and routes to NONE of eight committed documents (`SUB-application`, `SUB-amendment`, `SUB-periphery`, `CON-problem-layer-lifecycle`, `INV-signal-contract`, `REC-add-signal`, `REC-revise-allocation-policy`, `SEAM-schools-x-scheduler`) |
| **P18** | The managed path's run identity does not cover the run's CONFIGURATION (`preparation.py:722`). Harmless while configuration cannot vary; becomes a run-id collision the moment carriage lands |
| **P19** | `docs_verify` check `SUB-application.md:403` uses 54% of its own 300s timeout on an IDLE box (measured: 15 passed in 160.88s), so it goes red whenever the box is busy. A wall-clock failure, not a false claim |
| **P20** | `deepreason status` and the web page report readiness for a subject a configured run will not use |
| **P21** | The profile-owned override is silent; disclosing it would need frozen surfaces 4 AND 5 |
| **P22** | `reason` over MCP has no configuration input at all |
| **P23** | An ERRATA entry this tranche earned but could not write (file outside the lane cone) |
| **P25** | The carriage notice keeps a code reading NOT_CARRIED even when the value IS carried |
| **P26** | The agreement this tranche changes has no seam document in the map |
| **P27** | Two committed map `check:` lines are written in a multi-line form the verifier never parses — never executed, never failed, invisible to `--audit` |

### From Lane C (6)

| id | finding |
|---|---|
| **C1** | Two committed audit documents state an "18 minutes" figure **no surviving record supports** — see §5 |
| **C2** | **CLOSED by the fix**, not parked onward: an account-level condition can no longer eat the flake budget |
| **C3** | The falsified census at `INV-frozen-surfaces.md:181` characterised: its count of zero `transport_failure` attempts was falsified the day AFTER the grant it authenticates, by a root containing exactly the record shape the grant was written to admit. The census's zero is wrong; the grant is right |
| **C4** | The provider status reaches the RECORD but not the `deepreason qualify` console line — putting it there means editing `qualification.py`, frozen surface 5, so it needs an operator grant first |
| **C5** | `_failure_code` returns a schema-invalid code for any error carrying a NUMERIC `.code` — real but unreachable today, and this fix makes it strictly less reachable |
| **C6** | Duplicate of P19 (found independently by both lanes) |

### From Lane A (3) and Lane D (4)

- Lane A: the counterfactual pricing probe is INHERITED, not re-confirmed —
  the four run records it replays are not in this checkout. One older inert
  multi-line check remains in `CON-criticism-source.md` (pre-dates the
  tranche; resolves when the multi-line-check window lands). The live
  re-measurement the request asks for is still owed and was impossible here
  (offline batch, no provider).
- Lane D: P1 (a `SUB-capabilities.md` check that never runs — left
  deliberately, it is the repo-wide parked item another window is fixing);
  P2 **CLOSED** rather than parked (the header/body contradiction was fixed
  in-cone with a ratchet check); plus the residues in §6.

### New, from the post-verification pass on B1 (3)

| finding | status |
|---|---|
| **`LEGACY_CRITICISM_ENABLED: false` is NEITHER carried NOR disclosed** — B1's own success criterion is false for it. 7 of 8 committed configs set it, and it is precisely the field the price analysis identified as the priced one. Re-measured: runtime comes back `True`, `compile_notices` empty | **Belongs to the carriage decision in §2**, not to B1 |
| R9 pins two field NAMES rather than the general read, so a partial read or a swallowed `CONFIG_PROFILE_INVALID` still passes. `grep -rn "CONFIG_PROFILE_INVALID" tests/` returns nothing — the typed refusal has zero coverage. `VERIFY.md` overstates coverage by omission | parked |
| The school-seat scenario the fix's own motivation names still cannot start on the managed path: `QUALIFICATION_POLICY_PRESET_MISMATCH`. B1 replaced one typed refusal with another — typed, not silent | parked |

---

## 5. A correction the batch owes the record

**The symptom P7-A was dispatched to fix has no surviving committed
instance.** The evidence file the brief named
(`qualify-attempt2-VOID-agent-error.json`) records an HTTP **401** — a
credential refusal, which is not on the retryable list — so the backoff ladder
never slept once and that battery took about a minute, not eighteen. P7's
original file had already been overwritten by a later successful battery.

Lane C did not drop the claim or retreat from the defect. It **generated the
missing evidence offline** — the real doctor, the real manifest, the real
endpoint and the real retry ladder, with only the network call and
`time.sleep` faked:

| account-level condition | cases | HTTP calls | sleeps | mandated wait | record written |
|---|---|---|---|---|---|
| **429** (quota — retryable) | 260 | 1040 | 780 | **3640 s (60.7 min)** | `{'ENDPOINT_ERROR': 260}` |
| **401** (credential — not retryable) | 260 | 260 | 0 | **0 s** | `{'ENDPOINT_ERROR': 260}` |

Two failures an hour apart in cost — one that clears on its own, one that
never will — leave **byte-identical records**. That is the defect in one
table, and it is why the 2026-08-25 report was misread by its own author, in
writing, at the time. The number was wrong; the defect is real and is now
better evidenced than the audit had it. **C1** parks the ERRATA correction the
two audit documents still owe.

Lane C also found `doctor.py:535-560`, the brief's cited range, has MOVED —
it is now inside a single case's repair loop, not the battery loop.

---

## 6. Residue — what remains unproven, stated as such

- **No live run.** The batch is offline by construction: no provider
  credential exists in this container. Every claim is a compile-time or
  read-time property of committed evidence. Lane A's request for a live
  re-measurement is still owed.
- **Two B1 mutations are still missed** (partial read; swallowed typed
  refusal) — §4.
- **Lane D's new tripwire does not make configuration unreachable** from the
  capability side; a read through an already-permitted module passes it. The
  test suite is the authority there, and the document now says so instead of
  letting a map check stand in for a gate.
- **Lane D's completeness census is an import census, not a use census** — it
  would not catch a channel decision smuggled across as a plain boolean.
  Nothing suggests that exists; nothing rules it out.
- **Removing the vacuous `Sweep:` header** leaves that document with no
  mechanical completeness sweep, only the hand census. That is the honest
  cost of removing evidence that could not fail.
- **Lane A's counterfactual probe is inherited**, not re-derived — the roots
  it replays are not in this checkout.
- **Lane B's coverage of five other change sites is unaudited**: M1 still
  proves site 6 only through a stand-in, and M2/M3/M5/M6/M7 exercise the
  builders directly rather than through a public command.

Accepted does not mean true.

---

## 7. Fan-in gate — ONE full gate, ONE docs_verify, on the integrated branch

Session branch `85e288224`. Raw transcript: `evidence/fanin_gate.out`.
Started 12:16:53, ended 12:42:58.

### Full gate — 0 failed

    $ python -m pytest tests/ -q -n 4
    4453 passed, 6 skipped in 923.92s (0:15:23)

**0 failed. The only acceptable result, and it was met.** No assertion was
weakened anywhere in this batch to reach it.

Growth priced against the measurement, not the dispatch: `SETUP.md` recorded
4438 collected on `main`; this branch collects **4458**, +20 from the lanes'
new regression tests. (The batch brief stated a 4419 baseline; that figure was
already stale when the batch began, which is why `SETUP.md` re-measured it.)

### docs_verify — 4 failed, delta ZERO

    $ python tools/docs_verify.py
    docs_verify [full]: 70 documents, 1174 checks, 4 workers
      FAIL CON-run-identity.md:211   (shallow clone: rename history absent)
      FAIL CON-run-identity.md:213   fatal: ambiguous argument '1637e808'
      FAIL CON-run-identity.md:215   fatal: ambiguous argument 'f304fec1'
      FAIL INV-frozen-surfaces.md:181  (pre-existing falsified census)
    docs_verify: 4 failed

**Exactly the stated baseline, with no fifth and no different failure.** The
three `CON-run-identity.md` line numbers moved (200/213/215 from 200/202/204)
because the document grew; they are the same three shallow-clone checks.

The instrument itself grew with the batch: **69 -> 70 documents** (Lane D's
new seam document) and **1150 -> 1174 checks** (+24), every one of them run
and passing.

**The forecast fifth failure did not occur, as `SETUP.md`'s retraction in
section 1 predicted:** the `INV-frozen-surfaces.md:297` branch tripwire stays
green because no committed history on this branch touches a frozen path.

### One unreconciled observation, recorded rather than explained away

Collect-only reports **4458** items; the gate reports **4453 passed + 6
skipped = 4459 outcomes** — one more outcome than the tree collects. The same
+1 was independently observed by the B1 verifier on its own tree (4446
collectable, 4447 outcomes), so it is systematic and reproduces, not a
transcription slip.

Ruled out by measurement, not by argument:

    grep -rn "pytest_generate_tests|pytest_collection_modifyitems|collect_ignore|pytest_ignore_collect" tests/conftest.py conftest.py   -> no hooks
    grep -rln "pytest.main|subprocess.*pytest" tests/                                                                                  -> no test invokes pytest
    pip list | grep -iE "rerun|flaky|repeat"                                                                                           -> no rerun plugin (xdist 3.8.0 only)
    python -m pytest tests/ -q --collect-only        -> 4458
    python -m pytest tests/ -q --collect-only -n 4   -> 4458   (identical; not an xdist collection difference)

The three `pytestmark = pytest.mark.skipif(...)` modules were considered and
rejected as the cause: `skipif` is evaluated at run time, so those items ARE
collected and are already inside the 4458.

**It affects no verdict** — 0 failed either way, and the acceptance criterion
is failures, not arithmetic. It is left as an open question about the
instrument rather than given an explanation nobody measured. Fitting, for a
batch whose main result is that instruments can pass while not measuring what
they claim.
