# Spec for: rung 3, tranche B — migrate the call sites through the registry
Traces: every item cites R/C numbers. Untraceable items are bugs.

## Map preflight (R4)

Same two sides as Tranche A: `DR-CON-schools` and `DR-SUB-scheduler`,
joined by `DR-SEAM-schools-x-scheduler` — the seam document Tranche A
created, read here BEFORE the subsystems per `REC-change-a-seam.md`
Step 2. `DR-INV-frozen-surfaces` re-read: this tranche's design touches
none of the five surfaces (proven, not assumed — see S7's frozen-surface
check and the Q2 resolution below, which deliberately avoids the one
design that WOULD have touched surface 4).

**Predicted map change, planned not discovered.** `SEAM-schools-x-
scheduler.md` currently carries two checks that assert the migration has
NOT happened:

    line 64: `check: ! grep -q "SCHOOL_POPULATION" src/deepreason/scheduler/scheduler.py`
    line 65: `check: ! grep -q "SCHOOL_POPULATION" src/deepreason/capture/ladder.py`

Both are TRUE today and both become FALSE the moment S2/S3 land. That is
the temporary state Tranche A's "What is deliberately absent" section
explicitly documented. S6 rewrites that section and inverts those checks
in the SAME commit as the code — this is not an amendment waiting to
happen, it is a planned item.

## Resolving Q1-Q3 (dr-ask-the-right-question applied; record first)

**Q2 (how a call site names the backend) — resolved from the record, no
operator question.** Two findings decide it. First, the shape rung 3
tells us to copy resolves the name in ONE place, from data:
`VerificationRunner.verify` is the single `self.registry.verify(
request.backend, ...)` site (`verification/runner.py:281`), and
`WORKLOADS` has one `register` call and zero resolutions anywhere in
`src/`. Second, the obvious "put it on `Config`" design is NOT free:
rung 2 tranche 2 proved that ANY new top-level `Config` field breaks
pinned canonical-hash goldens across several schema versions unless
scrubbed in `run_manifest.py::_versioned_source_config_data` — `DR-INV-
frozen-surfaces` surface 4, which cost that tranche an explicit operator
approval gate (its REQUEST.md Amendment 3). Rung 3 asks for "the current
behavior as the ONLY, DEFAULT entry"; rung 5 is the rung whose words
require configurability ("a run configured with the alternative"). So:
ONE module-level constant and ONE helper in `capture/schools.py`, no
`Config` field, no frozen surface. Recorded as **A1**.

**Q1 (which call sites migrate) — resolved, with the counter-argument
recorded.** The rung names four functions; this tranche migrates every
call site of those four and nothing else. Verified fresh against the
current tree (line numbers re-read at spec time, not carried from
capture):

| File | Line | Call |
|---|---|---|
| `scheduler/scheduler.py` | 272 | `schools.init_schools(harness, config)` |
| `scheduler/scheduler.py` | 1804 | `schools.allocate(harness, problem, self.schools, config)` |
| `capture/ladder.py` | 28 | `schools.roster(harness)` |
| `capture/ladder.py` | 39 | `schools.reseed(...)` |
| `capture/ladder.py` | 73 | `schools.roster(harness)` |
| `capture/ladder.py` | 81 | `schools.reseed(...)` |
| `cli/main.py` | 906 | `schools_mod.roster(harness)` (read-only display) |
| `cli/main.py` | 1064 | `schools_mod.roster(harness)` (feeds the reseed command) |
| `cli/main.py` | 1068 | `schools_mod.reseed(...)` |
| `report.py` | 402 | `schools.roster(harness)` (read-only report) |

Explicitly NOT migrated (none is among the rung's four named functions):
`scheduler.py:951/952/955` (`STANCE_LIBRARY`, `stance_weight`,
`crossover_exemplars`), `cli/main.py:911/912` and `report.py:407/408`
(`stance_weight`, `lineage_size`). Recorded as **A2**, with its
counter-argument in "Out of scope" below.

**Q3 (what the determinism test can actually be) — a genuine
requirement-vs-record contradiction, resolved by delivering the property
R7 wants rather than the fixture R7 names.** R7 says to prove
byte-identity "before/after the registry" by reusing the offline
no-provider fixture pattern from `tests/test_attached_evidence_
citation.py`. That fixture does
`monkeypatch.setattr("deepreason.ops.run_scheduler",
finish_without_provider)`, and `ops.run_scheduler` (`ops.py:328`) is
precisely where the `Scheduler` is constructed ("Meter + adapter +
conjecturer check + Scheduler.run"). Its replacement,
`finish_without_provider`, never builds a `Scheduler` — so
`init_schools` (`scheduler.py:272`, inside `Scheduler.__init__`) and
`allocate` (`scheduler.py:1804`, inside `Scheduler.step`) are NEVER
REACHED by that fixture. A byte-identity test built on it would compare
two runs, neither of which executes one line of this tranche's migrated
code, and would pass trivially while proving nothing.

The dominance test kills this fork rather than sending it to the
operator: no reasonable operator holding "never claim more than the
record shows" prefers a test that passes without touching the changed
code over one that actually exercises it. So the test is built on the
pattern that DOES reach the migrated path — the mock-endpoint `Scheduler`
already used throughout `tests/test_schools.py`
(`Scheduler(harness, adapter, config)` with
`MockEndpoint(lambda p: _vs(...))`), which constructs the real
`Scheduler` (hitting `init_schools`) and whose `.run()`/`.step()` reaches
`allocate`. Two runs, identical seeds and config: one through the
migrated registry path, one with `capture.schools`'s four functions
monkeypatched back to bare-function behaviour, asserted byte-identical on
their event logs. Recorded as **A3**; flagged plainly in DELIVERY.md so
the deviation from R7's named fixture is impossible to miss.

**Questions for operator: none.** All three resolved from the record or
by dominance; the one contradiction (Q3) is reported in writing here and
will be reported again at delivery, per the orchestrator's "report the
contradiction, do not pick a side silently" rule — the side picked is
documented with its evidence.

## Items

S1 (R2, R3, A1): In `src/deepreason/capture/schools.py`, add a
module-level `_ACTIVE_BACKEND_ID = "default"` constant and an
`active_backend()` helper returning
`SCHOOL_POPULATION.resolve(_ACTIVE_BACKEND_ID).backend`. This is the
single place the backend NAME lives (the precedent's property) and the
single resolution point every migrated call site uses. No `Config`
field; no frozen surface.
accept: `python -c "from deepreason.capture.schools import active_backend, DefaultSchoolPopulationBackend; assert isinstance(active_backend(), DefaultSchoolPopulationBackend)"`.

S2 (R2, C6): Migrate `src/deepreason/scheduler/scheduler.py`'s two call
sites (272 `init_schools`, 1804 `allocate`) to
`schools.active_backend().init_schools(...)` / `.allocate(...)`.
Behaviour must be identical — the default backend delegates to the same
functions.
accept: `grep -c "schools.active_backend()" src/deepreason/scheduler/scheduler.py` is 2 AND `python -m pytest tests/test_schools.py tests/test_scheduler.py tests/test_rotation.py -q` 0 failed.

S3 (R2): Migrate `src/deepreason/capture/ladder.py`'s four call sites
(28, 73 `roster`; 39, 81 `reseed`) the same way.
accept: `grep -c "schools.active_backend()" src/deepreason/capture/ladder.py` is 4 AND `python -m pytest tests/test_orbit.py tests/test_schools.py -q` 0 failed.

S4 (R2): Migrate `src/deepreason/cli/main.py`'s three call sites (906,
1064 `roster`; 1068 `reseed`) and `src/deepreason/report.py`'s one (402
`roster`).
accept: `grep -c "active_backend()" src/deepreason/cli/main.py` is 3 AND `grep -c "active_backend()" src/deepreason/report.py` is 1.

S5 (R2, R3): After S2-S4, NO call site of the four named functions calls
the bare module function directly outside `capture/schools.py` itself
(where `DefaultSchoolPopulationBackend`'s methods legitimately delegate
to them). Exactly one backend stays registered.
accept: `python -c "import pathlib,re; bad=[(p,l) for p in ('src/deepreason/scheduler/scheduler.py','src/deepreason/capture/ladder.py','src/deepreason/cli/main.py','src/deepreason/report.py') for l in pathlib.Path(p).read_text().splitlines() if re.search(r'schools(_mod)?\.(init_schools|roster|allocate|reseed)\(', l)]; assert not bad, bad"`
AND `python -c "from deepreason.capture.schools import SCHOOL_POPULATION; assert SCHOOL_POPULATION.ids() == ('default',)"`.

S6 (R4, and the map's same-commit rule): Update
`docs/map/SEAM-schools-x-scheduler.md` in the SAME commit as S1-S4:
rewrite "What is deliberately absent" (the no-call-sites-yet paragraph
is now false), INVERT the two `! grep -q "SCHOOL_POPULATION"` checks at
lines 64-65 into positive assertions that the migration landed, add the
migrated call sites to the "Where it is expressed" table, and add
`src/deepreason/scheduler/scheduler.py` to the document's `Owns:` header
(Tranche A's own "How to change it" step 4 instructed exactly this).
accept: `python tools/docs_verify.py` 0 failed AND `--audit` 0 findings
AND `--links` 0 dangling AND `grep -q "src/deepreason/scheduler/scheduler.py" docs/map/SEAM-schools-x-scheduler.md`.

S7 (R7, A3): Add ONE new test file,
`tests/test_school_population_determinism.py`: build two mock-endpoint
`Scheduler` runs over identically-seeded harnesses and identical
`Config` — run A through the migrated registry path, run B with
`capture.schools`'s four functions monkeypatched so the backend's
delegation is bypassed — and assert the two runs' event logs are
byte-identical, and that each root's `verify_root` reports no violation
introduced by this tranche. The exact monkeypatch shape is settled at
execution time against the real helpers; if bypassing cannot be
expressed cleanly, the fallback is asserting run A's log is
byte-identical to a run built with the pre-migration call shape
reconstructed in the test itself.
accept: `python -m pytest tests/test_school_population_determinism.py -q` 0 failed, at least 1 test collectable, and the test genuinely executes `Scheduler.__init__` (asserted in-test by checking the scheduler's roster is non-empty).

S8 (R5, R6): Full gate and root sweep after S1-S7 land: `python -m
pytest tests/ -q -n 4` (expect ~3302+, 0 failed — rerun once if only the
known flake fails, per C5); `python tools/root_sweep.py` compared
against the last accepted capture — must be byte-identical (42 rows, 11
ERROR).

## Amendment 1 (discovered executing step 6/S6, R4)

S9 (R4, and the map's same-commit rule): `docs/map/CON-schools.md:121`
carries a checked claim — "**`N_SCHOOLS = 0` disables the mechanism
entirely**" — pinned by `grep -q "if config.N_SCHOOLS > 0 else {}"
src/deepreason/scheduler/scheduler.py`. S2's migration made that call
too long for one line (the single-line form is 110 characters against
the repo's own `line-length = 100` in `pyproject.toml`), so it wraps,
and the pinned literal no longer appears contiguously. **The claim is
untouched** — the guard is still `if config.N_SCHOOLS > 0 ... else {}`,
still returns an empty roster at zero; only its formatting moved. This
is a FOURTH map document affected, and the same class as Tranche A's
own Amendment 1: a form-brittle check broken by a legitimate edit, not
a violated invariant.

Fix: replace the contiguous-literal grep with a whitespace-tolerant
regex over the file that pins the SAME claim
(`if config.N_SCHOOLS > 0` ... `else {}` across an optional line
break). The check is thereby made robust to formatting without being
weakened — it still fails if the guard is deleted or its `else {}`
branch changed. Keeping the original literal was considered first and
rejected on evidence: it would require a 110-character line, which the
repo's own linter forbids.
accept: `python tools/docs_verify.py --fast` 0 failed, with
`CON-schools.md`'s claim still failing if the guard is removed
(mutation-tested before the new check is written down, per the map's
"run it before you write it down" rule).

## Amendment 2 (discovered executing step 10/S6, R4)

S10 (R4, and the map's same-commit rule): `docs/map/SEAM-scheduler-x-
rules.md:147` slices `Scheduler.step`'s source between two literal
markers to isolate the discrimination branch, and its closing marker is
`"assigned = schools.allocate("` — the exact text S2 migrated. The check
died with `ValueError: substring not found`. As with Amendment 1, the
CLAIM is untouched (that branch still runs `pairwise_discriminate` and
neither `conj` nor `synthesize`, and still ends in `return`); only a
source literal used as a slice boundary moved.

Fix: shorten the closing marker to `"assigned = schools"`, which matches
BOTH the pre- and post-migration call forms and slices exactly the same
segment (verified against the real source before writing it down). The
check's assertions are otherwise untouched, so it is made robust to
formatting without being weakened.

**The instrument lesson, which is the more valuable half of this
finding:** step 6 ran `docs_verify --fast` and got 0 failed. `--fast`
reuses cached results for documents whose OWN text is unchanged —
`SEAM-scheduler-x-rules.md` was not edited by this tranche, so its check
was never re-executed, even though the SOURCE FILE that check reads had
changed underneath it. A check can therefore be broken by an edit to a
file the document does not own, and `--fast` will not see it. Recorded
so future tranches do not treat a green `--fast` as evidence the map is
intact after a `src/` change: only the full run is that evidence.
accept: `python tools/docs_verify.py` (FULL, not `--fast`) 0 failed.

## Assumptions (operator may override)

A1 (Q2): the backend name is a module-level constant
(`_ACTIVE_BACKEND_ID = "default"`) plus one `active_backend()` helper —
NOT a `Config` field. Chosen because rung 3's words say "the only,
default entry", rung 5's words are the ones that require
configurability, and a `Config` field would cost a frozen-surface touch
(surface 4) plus an operator gate for zero rung-3 benefit.

A2 (Q1): all ten call sites of the four named functions migrate,
including the two read-only diagnostic ones (`cli/main.py:906`,
`report.py:402`). Assumed, operator may override — see the
counter-argument under "Out of scope".

A3 (Q3): the determinism test uses the mock-endpoint `Scheduler` pattern
from `tests/test_schools.py`, NOT the offline-no-provider fixture R7
names, because that fixture provably never reaches the migrated code
(`ops.run_scheduler` — where the `Scheduler` is built — is exactly what
it replaces). The property R7 asks for is delivered; the fixture it
names is not the one used. Flagged again at delivery.

## Questions for operator

None. (Q3's contradiction is reported above and at delivery rather than
blocking, because the dominance test settles which side to take and the
delivered proof is strictly stronger than the one literally specified.)

## Out of scope (explicit)

- **Migrating `stance_weight` / `lineage_size` / `crossover_exemplars` /
  `STANCE_LIBRARY` call sites.** Not among the rung's four named
  functions; not requested.
- **A `Config` knob selecting the backend.** Rung 5's job (A1). Building
  it here would touch a frozen surface for no rung-3 benefit.
- **Registering a second backend.** Rung 5, explicitly. "the current
  behavior as the only, default entry" (R3).
- **The counter-argument to A2, recorded so the operator can overrule
  it:** a purely diagnostic reader (`cli/main.py:906`'s `schools`
  display, `report.py:402`'s report) arguably SHOULD read the raw log
  truth rather than whatever an active backend says the roster is — so
  that a broken backend is visible in diagnostics rather than
  self-consistent. Today there is exactly one backend and it delegates
  unchanged, so the two readings are behaviourally identical; the
  question only bites once rung 5 adds an alternative. Migrated for
  coherence with the rung's own sentence; trivially reversible.

## Budget

~6 lines (`capture/schools.py`: constant + helper), ~10 lines across the
four migrated files, ~30-45 lines (`SEAM-schools-x-scheduler.md` rewrite
of one section + inverted checks + table rows + `Owns:`), ~60-90 lines
(new determinism test). Total ~110-150 lines, 2 commits (code+map
together per the same-commit rule, then the test, then a
gate-confirmation commit). Under the 300-line guideline. **Frozen
surfaces touched: none** — proven by S7's own diff check at validation,
and by A1's deliberate avoidance of the `Config`-field design that would
have touched surface 4.
