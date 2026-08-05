# Request: rung 5 — one deliberately dumb alternative, swapped in
Captured: 2026-08-04. Authority is two sources, both quoted verbatim
below. Rung 4 is complete and delivered (`0af00aff`, A1 confirmed at
`494a8213`); this is a clean tranche on a clean rung, per C1.

## Verbatim

> ### Rung 5 — one deliberately dumb alternative, swapped in  [EXECUTE WITH GUARDRAILS]
> Route: `dr-change-orchestrator` for the module; the live A/B is a
> separate step needing the OPERATOR (credentials are gitignored and did
> not survive rollback — ask for them; never commit them).
> Goal: implement one trivial alternative for the rung-3 socket (e.g.
> round-robin school allocation), register it as a non-default entry, and
> prove the socket real: offline, a run configured with the alternative
> completes and its root verifies; the default path stays byte-identical.
> The live A/B (same question, default vs dumb, compare typed outcomes) is
> valuable but OPTIONAL — run it only with operator-provided credentials,
> detached, with snapshot loop, per dr-drive-harness §3.
> Accept: full gate; sweep byte-identical; the alternative's offline run
> root replay-valid.
>
> — `docs/HANDOVER_2026-08-03.md`, "The program: seven rungs, in order,"
> Rung 5. Re-extracted from the file this turn, not carried from memory.

> A1 confirmed: SCHOOL_POPULATION only, other registries stay parked.
> Proceed to rung 5 via dr-change-orchestrator. Do the offline module work
> first; stop before the live A/B step and ask me for credentials.
>
> — operator's message this session, sent in response to rung 4's
> delivery report.

## Map preflight (resolved ids, recorded here so every later phase starts
## from the same map)

- `DR-INV-frozen-surfaces` — read in full during rung 4 this session.
  The five surfaces are unchanged. Nothing in rung 5's stated goal
  reaches one, but the forecast is `dr-spec-change`'s obligation (C10),
  not an assumption to carry from here.
- `DR-SEAM-schools-x-scheduler` — **the seam rung 5 exists to exercise.**
  Read in full this turn. Its "The agreement" section states rung 5's
  purpose in its own words: "The point of the indirection is rung 5: 'one
  deliberately dumb alternative, swapped in.' An alternative population
  strategy registers under a SECOND name, and no caller changes — only
  which name is resolved. That is why the name lives in exactly one place
  (`_ACTIVE_BACKEND_ID`) rather than being spelled at each of the ten
  call sites: rung 5 changes one constant's source, not ten files."
  Its "How to change it" step 1 binds directly: "A second backend (rung
  5) registers under a NEW name, never `default`."
- `DR-CON-schools` — owns `capture/schools.py`, `scheduler/scheduler.py`,
  `ontology/event.py` and (since rung 4) `module_events.py`.
- `DR-SUB-scheduler`, `DR-SUB-harness`, `DR-SUB-verification` — the
  offline run's completion and `verify_root` are judged through these.
- The socket's own protocol, verified fresh this turn:
  `SchoolPopulationBackend` (`capture/schools.py:214-227`) requires five
  methods — `fingerprint`, `init_schools`, `roster`, `allocate`,
  `reseed` — and `SchoolPopulationRegistry.register`
  (`capture/schools.py:240-247`) refuses a backend missing any of them,
  refuses a duplicate name, and pins the fingerprint at registration.

## Requirements

R1 (process): "Route: `dr-change-orchestrator` for the module".

R2 (process/constraint): "the live A/B is a separate step needing the
OPERATOR (credentials are gitignored and did not survive rollback — ask
for them; never commit them)."

R3 (behavior): "implement one trivial alternative for the rung-3 socket
(e.g. round-robin school allocation)".

R4 (behavior): "register it as a non-default entry".

R5 (behavior/artifact): "prove the socket real: offline, a run
configured with the alternative completes and its root verifies".

R6 (behavior/constraint): "the default path stays byte-identical".

R7 (process): "The live A/B (same question, default vs dumb, compare
typed outcomes) is valuable but OPTIONAL — run it only with
operator-provided credentials, detached, with snapshot loop, per
dr-drive-harness §3."

R8 (process): "Accept: full gate".

R9 (process): "sweep byte-identical".

R10 (process/artifact): "the alternative's offline run root
replay-valid".

R11 (process, operator's own words this session): "Proceed to rung 5 via
dr-change-orchestrator."

R12 (process, operator's own words this session): "Do the offline module
work first".

R13 (process, a STOP CONDITION in the operator's own words): "stop
before the live A/B step and ask me for credentials." This is stronger
than R7, which makes the live A/B optional: the operator has now made
the stop MANDATORY and named what the tranche must ask for. The tranche
does not reach the live A/B without a further operator message
supplying credentials.

## Standing constraints

C1: "One rung per tranche, minimum. A rung may take several tranches;
never let one tranche touch two rungs. Never begin rung N+1 in a tranche
that touched rung N." — `docs/HANDOVER_2026-08-03.md`, "Executor
calibration." This tranche is rung 5 only; rungs 6-7 remain untouched,
and rung 4's tranche is closed and delivered before this one opened.

C2: "Every rung ends with: acceptance commands run and pasted, tranche
committed and pushed, PARKED.md holding everything you noticed but did
not do." — same source.

C3: "Do not write to `docs/ERRATA_EXECUTOR.md` (operator-directed,
2026-08-03 …). That ledger has ONE writer: the monitoring session. When
anything in this file or the skills misleads you, contradicts the
record, or is silent where you needed it to speak, record the
observation in your own tranche's artifacts (PARKED.md or the phase
document where it surfaced) with the evidence pointer, then resolve the
question itself via `dr-ask-the-right-question`." — same source.

C4: "The frozen surfaces (`docs/map/INV-frozen-surfaces.md`) bind every
rung: state digests, harness event application, replay-validation
formats, manifest schemas AND validators, qualification subjects.
Readers may be fixed; formats may not; a change that moves a committed
root's verdict is wrong by definition." — same source.

C5 (inherited, standing across this session): known flake
`test_grounded_counterexample_recovery_does_not_invent_override_on_repeat`
can fail once under `-n 4`, rerun before diagnosing; commit and push at
every phase boundary; stop conditions are hard stops; where a spec is
silent, load `dr-ask-the-right-question` and route to the cheapest
authority — do not improvise; full gate must be run with `python -m
pytest`, never bare `pytest`.

C6 (verbatim, from the handover's environment facts — the section this
session's rung-4 tranche failed to read and paid for): "A bare `pip
install -e . --break-system-packages` does NOT restore the test/dev
dependencies after a rollback: `pytest`, `pytest-xdist`, and
`jsonschema` all had to be reinstalled this session (a missing
`jsonschema` alone produced two spurious docs_verify failures …).
Install them before trusting any red result."

C7 (verbatim, from the corrected handover, and carried forward from rung
4's C8): "Rule for the remaining rungs: accept lines state PROPERTIES;
any named mechanism is a suggestion the spec phase must verify for
reachability." This governs R3's "(e.g. round-robin school allocation)"
directly: the parenthetical is a SUGGESTION, not a mandate.

C8 (verbatim, from the corrected handover's environment facts):
"`docs_verify --fast` reuses cached check results, so it CANNOT catch a
map document newly broken by a `src/` change — only the full `python
tools/docs_verify.py` re-derives everything. Iterate with `--fast`; run
the full mode at least once before any commit that touches `src/`."

C9 (from `DR-SEAM-schools-x-scheduler`, "How to change it" step 1, and
binding for the same reason C4 is): "A second backend (rung 5) registers
under a NEW name, never `default`. `SchoolPopulationRegistry.register`
already refuses a duplicate name (mirroring `VerifierRegistry`); this is
the mechanical guarantee behind 'the default path stays byte-identical.'"

C10 (from `DR-SEAM-schools-x-scheduler`, "How to change it" step 4):
"A new call site uses `active_backend()`, and this document's counts
move with it. The three checks above pin exact per-file counts (3, 4,
3+1)." Rung 4 moved the scheduler count 2 → 3; any further call site
this rung adds moves it again, and the map check fails until it does.

C11 (from `DR-SEAM-schools-x-scheduler`, "How to change it" step 5):
"Finish with the two byte-identity instruments. The full gate and
`python tools/root_sweep.py`; plus
`tests/test_school_population_determinism.py`, which runs two
mock-endpoint schedulers and asserts their event logs are byte-identical
— the proof that the indirection changed nothing." Note rung 4 modified
that test's comparison (it now excludes the module-fingerprint stamp and
asserts the two stamps DIFFER); rung 5's alternative backend interacts
with it directly, because a non-default backend has a different
fingerprint by construction.

C12 (the sweep-probe rule, `dr-spec-change` step 3, carried from rung 4
where it was C13): a new typed-record OBSERVABLE needs a sweep probe
proposed in the spec, in its own SEPARATE commit. Rung 5 may or may not
add one — that is a spec-phase judgement, but it may not be skipped
silently.

## Open questions (for dr-spec-change)

**Q1 — WHICH operation the "trivial alternative" replaces.** R3 says
"one trivial alternative for the rung-3 socket" and offers round-robin
ALLOCATION as an example. But the socket is five methods, and a
registered backend must supply all five (`register` refuses one that
does not). So the alternative is a whole backend that differs in at
least one operation. Whether it should differ ONLY in `allocate`
(delegating the other four to the default implementations, as
`DefaultSchoolPopulationBackend` already delegates to module functions)
or differ more widely is undetermined by the words. Per C7 the
round-robin example is advisory and must be verified for reachability.

**Q2 — HOW a run is "configured with the alternative" (R5).** The seam
document says "rung 5 changes one constant's source, not ten files", and
`_ACTIVE_BACKEND_ID` (`capture/schools.py:329`) is that constant, with
its own comment: "A run-selected name (rung 5's 'a run configured with
the alternative') would replace this constant's value, not the call
sites." What SUPPLIES the run-selected name is undetermined and matters
a great deal: `Config` is the codebase's sanctioned home for a per-run
mode (`DR-INV-frozen-surfaces`, "Where authority is allowed to live
instead"), but rung 4's own M1 measured that a new top-level `Config`
field MOVES the qualification subject digest and the manifest sha unless
`run_manifest.py::_versioned_source_config_data` is explicitly told to
pop it — and `run_manifest.py` is frozen surface 4. **This is rung 4's
Q1 returning in a new place, and rung 4's answer (the operator closed
Option A) does not automatically transfer.** The alternatives to test:
a `Config` field with the surface-4 scrub line (needs operator
approval), an environment/CLI-supplied name that never enters Config, or
a test-only override that proves the socket without a production
selection path at all.

**Q3 — what "the default path stays byte-identical" (R6) is measured
against, given rung 4 changed the instrument.**
`tests/test_school_population_determinism.py` is the named instrument
(C11), and rung 4 modified it: it now excludes the module-fingerprint
stamp from its byte-identity comparison and asserts separately that a
substitute backend's stamp DIFFERS. A rung-5 alternative backend is
exactly such a substitute. So R6's "byte-identical" cannot mean "the two
runs' logs match in every byte" — rung 4 made that false by design for
any non-default backend. What it must mean is that a run that does NOT
select the alternative is unchanged. The spec must state which of the
two readings it is proving and with which instrument.

**Q4 — where the alternative's offline run root lives, and whether it is
committed (R10).** "the alternative's offline run root replay-valid"
implies a root exists and `verify_root` passes on it. Whether that root
is a session-local artifact (proved and discarded) or a COMMITTED root
(which would enter the 42-root sweep census and change every future
sweep baseline, exactly as rung 4's probe changed it) is undetermined,
and the two differ materially. Durable-test rule 1 prefers committed
evidence; the sweep census argues for care.

**Q5 — whether a deliberately DUMB backend is allowed to produce a worse
run, and how that is distinguished from a broken one.** R5 requires the
alternative's run to "complete" and its root to "verify". It does not
say the alternative must reason well — "deliberately dumb" says the
opposite. So a run that completes with poor epistemic outcomes is a
SUCCESS for this rung, and the spec must name the typed criteria that
separate "dumb but working" from "broken", or validation will have no
way to judge the offline run.

## Amendments

**Amendment 1 (2026-08-04, operator message).** The operator sent a
credential in response to this tranche's DELIVERY.md ask. **The value is
NOT reproduced here and is not in any committed file** — R2: "credentials
are gitignored and did not survive rollback — ask for them; never commit
them." It was written to
`experiments/2026-08-04-change-rung5-dumb-alternative-backend/env`
(mode 600), and that path was added to `.gitignore` and COMMITTED BEFORE
the file was created, because `.gitignore` lists env paths individually
and a new experiment directory is unprotected by default.

R14 (process): the credential's arrival discharges R13's ask and
authorizes the live A/B attempt under R7's conditions.

**Outcome: the live A/B is BLOCKED, and not by anything this tranche can
fix.** Measured against the real endpoint before any run was launched:

    /v1/models          + key -> 200   (18 models, glm-5.2 among them)
    /v1/chat/completions + key -> 401   glm-5.2
    /v1/chat/completions + key -> 401   gpt-oss:20b
    /v1/chat/completions + key -> 401   deepseek-v4-flash
    /api/chat (native)   + key -> 401
    /v1/chat/completions, NO key -> 401  (control: 401 is the generic reject)

The credential authenticates — a read-scoped call succeeds and returns the
catalogue — and is refused for inference on every model and both API
paths. That is an entitlement condition on the account (read-scoped key,
lapsed subscription, or exhausted credits), not a transmission fault: the
key is 56 chars, carries no whitespace, and matches the documented
`<32 hex>.<23 alnum>` shape.

No qualification was launched. Doing so would have spent ~14 minutes and
~1160 calls to arrive at the same 401, and CLAUDE.md's rule is to judge
typed outcomes rather than hope.

**Amendment 2 (2026-08-04, workflow change landing mid-tranche).** Commit
`f353ae12` added a mandatory BLAST-RADIUS CENSUS to `dr-spec-change`,
promoting this tranche's own PARKED P6 into the skill. Rung 5's spec phase
predates it. The census was run RETROACTIVELY rather than backfilled as
paperwork, and it confirms the rule is right: grepping
`tests/ docs/map/` for the seven changed symbols surfaces exactly the
files this tranche touched — including
`tests/test_school_population_registry.py`, the one test that broke at the
full gate three commits later than the census would have caught it. No
unhandled hit remains.

(append-only; later operator messages land here as R<n+1>... or
"R2a supersedes R2", each with its verbatim quote)
