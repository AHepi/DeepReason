# Parked — Rung S6 (the live two-seat A/B)

Noticed during this tranche, deliberately NOT fixed here — this is a
LIVE-RUN tranche; `src/`, `tests/`, `tools/`, `docs/map/` stay
byte-untouched throughout, so a defect found here routes to
`deepreason-orchestrator`, not to an inline fix.

## P1 (DEFECT, found by the live run — parked, NOT fixed): `property_designer` has no public path to ever fire

**What's broken:** the `coder` seat group (`GROUP_ROLES["coder"] =
{"property_designer"}`) binds a real profile correctly and is stamped
correctly into the typed record (Rung S5's own mechanism, proven both
offline and live), but the role it binds can never actually be
DISPATCHED through any path reachable from the public CLI. This was
first mischaracterized in this tranche's own `RESULTS.md` (initial
segment) as a "stochastic miss," matching CLAUDE.md's own documented
capability-channel stochasticity doctrine — that characterization is
WRONG and has been corrected in a dated `RESULTS.md` segment (never
editing the original) rather than silently fixed in place.

**The diagnosis chain, verbatim from the correcting `RESULTS.md`
segment — reproduced here so this parked item carries its own complete
evidence, not a pointer that could rot:**

1. `GROUP_ROLES["coder"] = frozenset({"property_designer"})`
   (`seat_bindings.py`) — the `coder` group's ONLY role.
2. `property_designer` is dispatched from exactly one call site,
   `rules/experiment.py::propose_properties`, which early-returns `[]`
   unless `oracle.py::checker_wf_commitment(base)` returns non-`None`.
3. `checker_wf_commitment(base)` (`oracle.py:776`) itself early-returns
   `None` unless `base.eval == f"program:{PROPERTY_PROGRAM}"` — i.e.
   unless an ACTIVE property-oracle commitment already exists in the
   run's own graph.
4. The only function anywhere in `src/deepreason/` that constructs a
   NEW `Commitment` with `eval == "program:property_oracle"` is
   `oracle.py::property_oracle_commitment` (line 335).
5. `property_oracle_commitment`'s only caller in the entire tree is
   `oracle.py::admit_counterexample` (line 431 — confirmed the exact
   one call site outside the function's own definition).
6. `admit_counterexample` (`oracle.py:386`) itself REQUIRES `base.eval
   == f"program:{PROPERTY_PROGRAM}"` as its own precondition (line
   397) — it mints a counterexample-derived oracle INHERITING an
   existing base oracle's own spec; it does not mint the first one.
7. Every other reference to `PROPERTY_PROGRAM` in the tree
   (`run_manifest.py:3830`, `rules/crit.py:779,813,942`,
   `scheduler/scheduler.py:2201,2246,2288`) READS `commitment.eval ==
   f"program:{PROPERTY_PROGRAM}"` to gate some OTHER behavior; none of
   them constructs one.

**The circularity, stated plainly:** minting a property-oracle
commitment requires an existing property-oracle commitment as input.
No public path — the CLI, the seed-problem admission path, or any rule
this tranche's live run actually exercised — constructs the FIRST one.
`property_designer` therefore has no way to ever fire on ANY run
launched through the public surface, structurally, independent of
question, cycle budget, or which models are bound to which seats. This
is consistent with an independent, standing observation: no
`log.jsonl` under `experiments/` or `runs/` in this repository's entire
history has ever carried a `"role": "property_designer"` LLM-call
record.

**Why this was missed on first read:** reasoning by analogy to
CLAUDE.md's documented capability-channel stochasticity doctrine
(which genuinely does govern OTHER, live-model-driven proposal paths)
without tracing `property_oracle_commitment`'s own caller graph to its
end — the same shape as `docs/map/INV-frozen-surfaces.md`'s own
recorded trap "reading a model and not its validator," applied here to
a different mechanism entirely.

**Not fixed here, on purpose:** whether property oracles should be
publicly mintable at all — e.g. a new CLI path, an attached-evidence
shape that seeds one, or some other bootstrap — is an OPERATOR DESIGN
DECISION, not a bug this live-run tranche is positioned to fix. Building
one unilaterally would be scope creep into a feature question dressed
as a defect fix. This tranche's own live-demonstration need was
satisfied by re-running on a seat proven to do real work
(`conjecture`, binding `conjecturer`+`variator`) instead — see
`RESULTS.md`'s own re-run segment.

**Ready-to-send prompt:** "Diagnose whether `property_designer` /
`coder`-seat work should ever be publicly reachable, and if so design
the bootstrap path for the FIRST `program:property_oracle` commitment
— via `deepreason-orchestrator`, starting from `dr-set-goal` with this
PARKED.md's P1 entry (the full call-graph evidence chain above) as the
starting diagnosis. This is a design question first (does the operator
want this path open at all) and only a `dr-implement-fix` matter
second, once that's answered."

## In-flight note

The re-run reuses `home-s6/` (same `DEEPREASON_HOME`, a fresh run
identity since the seat group changes the compiled manifest's roles
table and therefore the request digest). Its new run root is committed
only after the ladder exits and `verify_root` has judged it — never
mid-append, per this program's own established rule (`DR-SEAM-harness-
x-verification`'s torn-tail concern).
