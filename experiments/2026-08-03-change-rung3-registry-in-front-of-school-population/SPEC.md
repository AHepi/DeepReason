# Spec for: rung 3, tranche A — the school-population registry (build only, no call sites migrated)
Traces: every item cites R/C numbers. Untraceable items are bugs.

## Map preflight (R4)

`docs/map/INDEX.md` resolves the two sides:
`DR-CON-schools` (owns `src/deepreason/capture/schools.py`,
`src/deepreason/scheduler/scheduler.py`, and others) and
`DR-SUB-scheduler` (owns `src/deepreason/scheduler/`). Both documents'
own headers list `scheduler x schools` under `Seams-undocumented:` —
confirmed by direct read, not the numbered coupling matrix (that matrix
is scoped to `SUB-<pkg>` pairs only and does not cover `CON-` concepts
like schools at all, so its absence there is not evidence of
non-interaction — `docs/map/REC-change-a-seam.md` Step 2's own caveat).
This tranche's design therefore creates
`docs/map/SEAM-schools-x-scheduler.md` (alphabetical: schools <
scheduler) as part of the work, following `REC-change-a-seam.md` Step 7's
template, rather than extending an existing seam document.
`docs/map/INV-frozen-surfaces.md` re-read: none of this tranche's five
surfaces are touched — no state digest, no harness event application, no
replay-validation format, no manifest schema, no qualification subject.

## Scope decision: splitting rung 3 into two tranches (recorded here, not
a REQUEST.md contradiction — the handover's own C1 explicitly allows
"a rung may take several tranches")

Rung 3's full scope (build the registry AND migrate every call site AND
prove end-to-end determinism) is right at or over the ~300-line
guideline once the true blast radius is counted: a new protocol +
default backend + registry class (~90 lines, mirroring `verification/
registry.py`'s 101), a brand-new `docs/map/SEAM-schools-x-scheduler.md`
(~60-80 lines, no existing document to extend), call-site changes across
THREE files that include the live scheduler
(`src/deepreason/scheduler/scheduler.py`, the single most sensitive file
in the codebase) and the response ladder
(`src/deepreason/capture/ladder.py`), plus a full offline no-provider
scheduler-run determinism test (~50-80 lines, reusing `tests/
test_attached_evidence_citation.py`'s fixture pattern). Bundling all of
this into one tranche means one commit touching the live scheduler with
no independent checkpoint if something goes wrong partway.

**This tranche (Tranche A) builds and proves the registry mechanism in
isolation — the protocol, the default backend (an unchanged wrapper
around today's four functions), the registry class, the new seam
document, and a UNIT-level equivalence test (backend-resolved calls
produce byte-identical results to today's bare function calls) — with
ZERO call sites migrated yet.** No live-path file (`scheduler.py`,
`capture/ladder.py`, `cli/main.py`) is touched. Tranche B (a follow-up,
not opened here) migrates the actual call sites and adds the full
end-to-end offline-run determinism test R7 asks for. This tranche alone
cannot satisfy R2's literal "resolves through a named registry entry"
for any LIVE caller yet — that is Tranche B's job — but it delivers the
registry as a real, tested, map-documented artifact ready for Tranche B
to consume, which is the smaller, safer first step.

## Resolving Q1-Q3 (dr-ask-the-right-question applied; record first)

**Q1 (exact shape)** — resolved by direct read of both named files:
`verification/registry.py`'s shape is `Protocol` (backend contract) +
`@dataclass(frozen=True)` registration record + `Registry` class with
`register`/`get`/`resolve`/`ids`/`fingerprint`/`fingerprint_is_pinned`.
`capture/schools.py`'s four functions take `(harness, config)` /
`(harness)` / `(harness, problem, schools, config)` /
`(harness, school_id, current, reason, crossover_from=None)` — different
signatures per function, unlike `VerifierBackend.verify`'s single
uniform signature. The backend protocol below mirrors each function's
own signature as its own method. Recorded as **A1**.

**Q2 (test pattern)** — resolved by direct read: `tests/
test_attached_evidence_citation.py::_attached_evidence_root` builds a
full v6 run via `TextRunApplicationService.start(...)` with
`monkeypatch.setattr("deepreason.ops.run_scheduler", finish_without_
provider)` — a full offline stand-in that never calls a real provider.
This is the pattern R7's determinism test will reuse, but only in
Tranche B (once call sites exist to prove the FULL run is unaffected).
For Tranche A, the equivalent, smaller-scope determinism proof is a
DIRECT equivalence test: the default backend's four methods called
against a fixture harness produce results identical to calling
`capture.schools`'s bare module functions with the same arguments —
proving the wrapper adds nothing and changes nothing, the precondition
Tranche B's larger test will build on. Recorded as **A2**.

**Q3 (migration scope for call sites — deferred to Tranche B, not
resolved here)** — not this tranche's decision; Tranche B's own
`dr-spec-change` will resolve which call sites (`scheduler.py`'s
`init_schools`/`allocate`; `capture/ladder.py`'s `roster`/`reseed`
call sites, both are live decision-making, not diagnostics; `cli/
main.py`'s `reseed` command, a write operation) migrate, versus
purely-diagnostic `roster()` reads (`report.py`; `cli/main.py`'s
`schools` display command) that carry no backend-dependent behavior and
may reasonably stay as direct module calls. Recorded as a live
open question for Tranche B's own spec, not resolved by fiat here.

No reading above differs materially enough to warrant an operator stop
for THIS tranche's own scope. **Questions for operator: none** — the
sub-tranche split itself is explicitly pre-authorized by the handover's
own C1 ("a rung may take several tranches").

## Items

S1 (R2, R3): Add to `src/deepreason/capture/schools.py`: a
`SchoolPopulationBackend` `Protocol` (methods: `fingerprint(self) ->
dict`, `init_schools(self, harness, config) -> dict[str, dict]`,
`roster(self, harness) -> dict[str, dict]`, `allocate(self, harness,
problem, schools, config) -> list[str]`, `reseed(self, harness,
school_id, current, reason, crossover_from=None) -> dict`); a
`@dataclass(frozen=True)` `SchoolPopulationRegistration` (mirroring
`VerifierRegistration`'s shape: `backend_id: str`, `backend:
SchoolPopulationBackend`, `pinned_fingerprint: dict`); a
`SchoolPopulationRegistry` class copying `VerifierRegistry`'s shape
(`register`, `get`/`resolve` alias, `ids`, `fingerprint`,
`fingerprint_is_pinned`) — no `verify` method (schools has no single
verb like that); errors `SchoolPopulationRegistryError(ValueError)` and
`UnknownSchoolPopulationBackend(SchoolPopulationRegistryError,
KeyError)`, mirroring `VerifierRegistryError`/`UnknownVerifier`.
accept: `python -c "from deepreason.capture.schools import SchoolPopulationRegistry, SchoolPopulationBackend, SchoolPopulationRegistration; assert callable(SchoolPopulationBackend.__dict__.get('init_schools')) and callable(SchoolPopulationBackend.__dict__.get('roster')) and callable(SchoolPopulationBackend.__dict__.get('allocate')) and callable(SchoolPopulationBackend.__dict__.get('reseed')) and callable(SchoolPopulationBackend.__dict__.get('fingerprint'))"`
AND `python -c "from deepreason.capture.schools import SchoolPopulationRegistry; r = SchoolPopulationRegistry(); assert hasattr(r, 'register') and hasattr(r, 'get') and hasattr(r, 'resolve') and hasattr(r, 'ids') and hasattr(r, 'fingerprint') and hasattr(r, 'fingerprint_is_pinned')"`.

S2 (R2, R3): Add a `DefaultSchoolPopulationBackend` class implementing
`SchoolPopulationBackend`, whose four methods delegate UNCHANGED to
today's existing module-level `init_schools`/`roster`/`allocate`/
`reseed` functions (those functions themselves are NOT modified — the
class is a thin pass-through wrapper) and whose `fingerprint()` returns
a small stable dict identifying this backend (e.g.
`{"backend": "default", "stance_count": len(_STANCES)}` — deterministic,
derived from existing module state, not a new hard-coded literal that
could drift).
accept: `python -c "from deepreason.capture.schools import DefaultSchoolPopulationBackend; b = DefaultSchoolPopulationBackend(); fp = b.fingerprint(); assert fp['backend'] == 'default'"`.

S3 (R2): Add a module-level pre-populated singleton,
`SCHOOL_POPULATION = SchoolPopulationRegistry()` with
`DefaultSchoolPopulationBackend()` registered under the name
`"default"` — mirroring `workloads/registry.py`'s `WORKLOADS =
WorkloadRegistry()` singleton precedent, so Tranche B's call-site
migration has a ready-made resolution point requiring no new
construction logic at each call site.
accept: `python -c "from deepreason.capture.schools import SCHOOL_POPULATION; assert SCHOOL_POPULATION.ids() == ('default',)"`.

S4 (R7, A2 — Tranche A's scoped determinism proof): Add a new test file
`tests/test_school_population_registry.py` proving: (a) the registry's
mechanics (register, get, unknown-name error, duplicate-registration
error) mirroring `tests/test_verifier_registry.py`'s own coverage shape;
(b) the DEFAULT backend's four methods, called against a fixture
harness with seeded schools, produce results identical to calling
`capture.schools`'s bare module functions with the same arguments — the
Tranche-A-scoped "byte-identical before/after" proof (the wrapper is
provably a no-op layer).
accept: `python -m pytest tests/test_school_population_registry.py -q`
0 failed, at least 5 test functions collectable.

S5 (R4, R6): Create `docs/map/SEAM-schools-x-scheduler.md` in the SAME
commit as S1-S4's code, following `REC-change-a-seam.md`'s template
(`Owns:`, `Sides: DR-CON-schools, DR-SUB-scheduler`, "The agreement,"
"Where it is expressed," "What is deliberately absent," "How to change
it," "Traps"). `Owns:` at minimum `src/deepreason/capture/schools.py`
(the new registry lives here) — `scheduler/scheduler.py` stays
UNCLAIMED by this new seam document in Tranche A specifically, since
Tranche A adds no scheduler.py lines at all; Tranche B's own map update
will add it to `Owns:` when the scheduler actually starts consuming the
registry. "What is deliberately absent" names precisely this: the
registry exists and is proven correct, but nothing in the live scheduler
resolves through it yet — that migration is Tranche B, not an oversight.
Update `docs/map/CON-schools.md`'s and `docs/map/SUB-scheduler.md`'s
`Seams:`/`Seams-undocumented:` headers to reference the new document
(remove `scheduler x schools` from both `Seams-undocumented:` lines, add
`DR-SEAM-schools-x-scheduler` to both `Seams:` lines).
accept: `python tools/docs_verify.py` 0 failed AND `--audit` 0 findings
AND `--links` 0 dangling AND `grep -q "DR-SEAM-schools-x-scheduler" docs/map/CON-schools.md docs/map/SUB-scheduler.md`.

S6 (R5, R6): Full gate and root sweep after S1-S5 land: `python -m
pytest tests/ -q -n 4` (expect ~3293-3298 passed depending on S4's exact
test count, 0 failed — rerun once if only the known flake fails, per
C5); `python tools/root_sweep.py` compared against the last accepted
baseline — must be byte-identical (42 rows, 11 ERROR expected).

## Assumptions (operator may override)

A1 (Q1): the registry/protocol shape mirrors `verification/registry.py`
field-for-field and method-for-method, adapted only for `schools`'
four differently-shaped functions instead of one uniform `verify` call;
no `verify`-equivalent single-entry-point method is added (there is no
single verb that unifies `init_schools`/`roster`/`allocate`/`reseed`).

A2 (Q2): Tranche A's determinism proof is a DIRECT method-vs-
bare-function equivalence test (S4), not yet the full offline-run
proof R7 literally asks for — that lands in Tranche B once call sites
actually route through the registry. Recorded plainly so nobody mistakes
Tranche A alone as satisfying R7 in full.

A3 (Tranche split itself): rung 3 splits into (at least) two tranches;
this SPEC.md covers Tranche A only. Tranche B (call-site migration +
full end-to-end determinism test) opens as its own tranche once Tranche
A is delivered, per the handover's own "a rung may take several
tranches" allowance (C1) and "never let one tranche touch two rungs"
(same constraint, satisfied trivially since both A and B are rung 3).

## Questions for operator

None for Tranche A's own scope.

## Out of scope (explicit)

- Migrating ANY call site (`scheduler.py`, `capture/ladder.py`,
  `cli/main.py`) to resolve through the registry — Tranche B.
- The full end-to-end offline-no-provider-run determinism test R7
  literally describes — Tranche B (Tranche A's S4 is a scoped,
  smaller-footprint proof for THIS tranche's own delivered surface).
- Rung 5's "one deliberately dumb alternative, swapped in" — a later,
  separate rung, explicitly out of scope per C1.
- Registering a SECOND backend of any kind — "the current behavior as
  the only, default entry" (R2's own words); this tranche registers
  exactly one.

## Amendment 1 (discovered executing step 6/S3, R6)

S7 (R6): `docs/map/SEAM-manifest-x-schools.md`'s checked claim at line
179 ("The school side cannot describe what a route is") asserts a
CLOSED-WORLD import set for `capture/schools.py`:
`mods=={'json','deepreason.ontology'}`. S1's new imports
(`copy`, `typing.Any`/`typing.Protocol`, `collections.abc.Iterable`,
`dataclasses.dataclass`, `deepreason.canonical.canonical_json`,
`deepreason.ontology.frozen.FrozenDict`) break this literal assertion.
The invariant the check exists to protect — schools.py cannot reach the
manifest, the firewall, or `Config`'s type, so allocation cannot become
route-aware — is NOT violated: none of the six new imports touch
`run_manifest`, `llm.firewall`, or `config`. This is the same class of
discovery as tranche 2's Amendment 1 (a literal-grep/closed-world check
too narrow for a legitimate addition, not a violated invariant). Fix:
widen the closed-world set in the check to include the six new imports,
while preserving the check's actual protective assertions unchanged
(the `SchoolRoleBindingV1` pattern tests, the
`! grep -q "deepreason\.capture" src/deepreason/run_manifest.py`
reverse-direction check, and the `school_id = f"school-{i}"` grep) —
none of those need to change, only the import-set literal.
accept: `python tools/docs_verify.py --fast` 0 failed (SEAM-manifest-x-schools.md's check specifically passing) AND the check still asserts
`not {'run_manifest', 'llm.firewall', 'deepreason.config'} & mods`-style
exclusion (i.e., the fix widens, it does not weaken the exclusion the
check exists to prove).

## Budget

~90 lines (protocol + registration dataclass + registry class +
default-backend wrapper + module singleton, `capture/schools.py`),
~60-80 lines (new `SEAM-schools-x-scheduler.md`), ~10-15 lines
(`CON-schools.md`/`SUB-scheduler.md` header updates), ~60-80 lines
(new test file, S4). Total ~220-265 lines, 1-2 commits (code+map
together per R6, then a gate-confirmation commit). Under the 300-line
guideline for Tranche A specifically (the full, unsplit rung would not
have been). Frozen surfaces touched: none.
