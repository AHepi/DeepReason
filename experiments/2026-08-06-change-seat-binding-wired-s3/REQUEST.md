# Request: the binding, wired — Rung S3 of role-seat separation

Captured: 2026-08-06 from the operator's message opening this
tranche, plus the plan document's own Rung S3 text.

## Verbatim

Operator's message opening this tranche:

> S2 SPEC approved: Option A, sub-choice 2a. Q1: (a) — simulation
> aliases conjecture for S3, and conflicting --seat values for the
> shared role set get a typed refusal, never last-one-wins. Q2: 2a
> confirmed. A1–A3 stand. Proceed to Rung S3 via dr-change-orchestrator:
> implement the approved binding — setup accepts per-role-group
> profile paths, _config_for_profile generalized per SM1/SM2, default
> no-flags behavior byte-identical to today. Full gate 0 failed; sweep
> byte-identical; two-MockEndpoint routing proof asserted from the
> typed attempt records. One rung only.

The plan's own Rung S3 text, quoted verbatim from
`docs/proposals/ROLE_SEAT_SEPARATION_PLAN.md` lines 91-98:

> ### Rung S3 — the binding, wired  [EXECUTE, after S2 approval]
> Implement the approved design: named profiles in setup, SeatBinding
> resolution where leases are built, default single-seat behaviour
> byte-identical for existing configs (the whole gate must not notice).
> Accept: full gate 0 failed; sweep byte-identical; a unit run with two
> MockEndpoint-backed seats shows role-correct routing (each role's
> calls land on its seat's endpoint — asserted from the typed attempt
> records, which already carry work attribution per call).

The approved design this tranche implements, quoted verbatim from
`experiments/2026-08-06-change-seat-binding-design-s2/SPEC.md` (Items
S1/S2, the recommendation the operator's amendment R11 approved):

> S1 ... **Mechanism:** `deepreason setup` gains a form to bind named
> profiles to role groups (exact CLI surface: `--seat
> conjecture=<profile-path> --seat coder=<profile-path> --seat
> scratch=<profile-path> --seat simulation=<profile-path>`, each
> value an explicit path resolved via the ALREADY-EXISTING
> `resolve_provider_profile` explicit-path branch ... Default (no
> `--seat` flags): every role group maps to the single resolved
> profile — byte-identical to today's `_config_for_profile` behavior
> ...
> S2 ... (2a) Resolve role-group->profile ENTIRELY at the CLI/setup
> layer, before any `Config` is built — `Config.roles` receives only
> ordinary per-role endpoint dicts (exactly what it already accepts
> today, SM1) with no new `Config` field naming "which named profile"
> produced them. **Zero SM6 risk**...

## Requirements

R1 (behavior): "setup accepts per-role-group profile paths" — `deepreason
setup` accepts `--seat <group>=<profile-path>` flags per the plan's own
named surface (`--seat conjecture=<profile> --seat coder=<profile>
--seat scratch=<profile> --seat simulation=<profile>`).

R2 (behavior): "_config_for_profile generalized per SM1/SM2" —
generalize `_config_for_profile` (or its caller path) to build
`Config.roles` from the resolved per-role-group profiles, using
`Config.roles`'s already-heterogeneous type (SM1) and
`compile_run_manifest`'s already-independent per-role route resolution
(SM2) — no manifest schema or validator change.

R3 (behavior): "default no-flags behavior byte-identical to today" /
"default single-seat behaviour byte-identical for existing configs
(the whole gate must not notice)" — when no `--seat` flags are given,
every role group must resolve to the single profile, byte-identical to
current `_config_for_profile` output and every existing test/golden.

R4 (behavior): "SeatBinding resolution where leases are built" — the
resolution from named profiles to concrete leases happens where the
plan's S2 design places it (compile time, per SPEC.md's Option A/2a),
not at call-dispatch or continuation time.

R5 (process): "Full gate 0 failed" — `pytest tests/ -q -n 4` must end
0 failed.

R6 (process): "sweep byte-identical" — the 42-root sweep
(`tools/root_sweep.py`) must produce a byte-identical result
before/after this change.

R7 (behavior): "two-MockEndpoint routing proof asserted from the typed
attempt records" / "a unit run with two MockEndpoint-backed seats
shows role-correct routing (each role's calls land on its seat's
endpoint — asserted from the typed attempt records, which already
carry work attribution per call)" — a test proves, from typed attempt
records (not mocked internals), that two seats bound to two different
MockEndpoints each receive only their own role's calls.

R8 (behavior): "Q1: (a) — simulation aliases conjecture for S3" — the
"simulation" seat group is implemented as an alias of "conjecture"
(same role set, same profile), not a separately bindable group with
its own role set.

R9 (behavior): "conflicting --seat values for the shared role set get
a typed refusal, never last-one-wins" — if `--seat conjecture=X` and
`--seat simulation=Y` are both given with `X != Y`, `deepreason setup`
must raise a typed refusal, not silently apply whichever flag was
parsed last.

R10 (process): "Q2: 2a confirmed" — implement sub-choice 2a: no new
`Config` field; the role-group->profile resolution happens entirely
before `Config` construction.

R11 (process): "One rung only." — this tranche delivers Rung S3 only;
it does not begin S4 (qualification per seat), S5 (seats in the typed
record), or any later rung.

## Standing constraints

C1 (from the plan document, Rung S2's own text, still binding per S2's
SPEC.md Item S6/placement-law section): bindings must resolve to
concrete `Route`s at manifest-compile (mint) time, never at
call-dispatch or continuation time — inherited from the approved S2
design, not re-litigated here.

C2 (from CLAUDE.md, standing project instruction): "Commits: one
defect or one change per commit; message states what, why, the live
evidence (run ids), and 'Full gate: N passed, 0 failed' when code
changed."

C3 (from `docs/map/INV-frozen-surfaces.md`, and S2's SPEC.md forecast):
this design is approved specifically because it forecasts zero
frozen-surface contact; any implementation step that turns out to
require touching `run_manifest.py` schemas/validators, capability
digests, harness event application, or replay-validation formats is a
stop condition per `dr-change-orchestrator`'s own rule 3, not a detail
to route around silently.

## Open questions (for dr-spec-change)

Q1: The plan's Rung S3 acceptance criterion says "a unit run with two
MockEndpoint-backed seats" (R7) — does this mean a single new test
function using `MockEndpoint`-style test doubles (matching existing
test patterns in the suite), or a literal live CLI run under a test
`DEEPREASON_HOME`? The plan's own phrasing ("unit run", "asserted from
the typed attempt records") suggests a unit test, not a live run.

Q2: R1's exact CLI flag repeatability/parsing shape (`--seat
group=path`, repeated per group) needs a concrete argparse
implementation choice — `action="append"` with `key=value` parsing, or
one flag per named group (`--seat-conjecture`, `--seat-coder`, etc.).
The plan's own example syntax (`--seat conjecture=<profile> --seat
coder=<profile> ...`) already fixes this to the repeated
`--seat group=path` form; not genuinely open, noted for SPEC.md to
confirm rather than re-decide.

## Amendments

(none yet)
