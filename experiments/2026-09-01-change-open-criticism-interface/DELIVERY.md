# Delivered: maximum modularity, open exploration, and no formalism rank — phase one, the contribution-only criticism-source socket

Branch: `claude/open-criticism-contracts-delivery-rt5nde` (pushed, tree clean)
Tranche base: `main` @ `762178b63`. Merge: `ee61ba4147`, `--no-ff`, no conflict.

## What changed

One new public module, `src/deepreason/criticism_source.py` (140 lines), adds a
boundary through which an optional, externally supplied source may hand
criticism to DeepReason — and nothing else. It defines four closed contracts
(`CriticismSourceManifestV1`, `CriticismTargetV1`, `CriticismContributionV1`,
`CriticismInvocationResultV1`), a `CriticismSource` protocol, an explicit
`CriticismSourceRegistry` that a caller constructs by hand, and two functions:
`invoke_criticism_source`, which runs exactly one named source, and
`describe_criticism_sources`, which reports what is registered without invoking
anything.

The design is defined as much by what it refuses to carry. A contribution has
exactly two fields — `content` and `codec` — and both are transport data. There
is no score, rank, weight, confidence, severity, threshold, priority, verdict,
status, warrant, or authority field anywhere in the four contracts, and adding
one turns the contract test RED (mutation-proven, both `score` and `priority`).
The host binds the target, so a source cannot choose what it criticises. There
is no default source, no fallback, no winner, no aggregator, no learned order,
no automatic invocation and no scheduler attachment: two sources that disagree
are invoked separately and neither result touches the other. Prose, mathematical
notation, JSON-looking text and code-looking text all cross the same opaque
field byte-for-byte, unparsed and unclassified — so nothing here can make a
formal contribution outrank a prose one. Decline, unavailable and error are
host-written operational outcomes, not judgements about merit.

The socket is DELIBERATELY UNWIRED and stays that way: it has no consumer in
the shipped reasoning graph, imports nothing from DeepReason, and a test walks
every other shipped Python module and fails if any of them imports it — in both
the absolute and the relative spelling, each mutation-proven. Phase one proves
the boundary before connecting it to anything live.

Supporting changes: `tests/test_criticism_source_contract.py` (114 lines, 13
tests); three owner-map documents gained one executable `check:` each
(`CON-criticism-source.md` owns the module, `CON-conjecture-kinds.md` records
the representation-neutrality law line, `CON-authority.md` records that the
`contribution_only` ceiling cannot choose run authority); and
`scripts/wheel_smoke.py` pins the new module in the wheel and imports it in the
clean installed environment (2 lines). No frozen surface was touched — the
diff over all seven declared paths is empty and `blast_radius` reports `CLEAR`
with empty frozen and frozen-adjacent contact lists.

## How it is proven

On the rebased tree, in a capable container, against the same container's
untouched base:

| | base `762178b63` | head |
|---|---|---|
| `python -m pytest tests/ -q -n 4` | 4712 passed, 6 skipped, **0 failed** | 4725 passed, 6 skipped, **0 failed** |
| `python tools/docs_verify.py` | 1328 checks, 3 failed | 1331 checks, 3 failed (identical rows) |

The gate delta is `+13 passed, +0 failed` — exactly this tranche's 13 contract
tests. The docs delta is `+3 checks` — exactly this tranche's three owner-map
checks — with the failure list unchanged row for row. The twelve failing
nodeids recorded in `proof/full-gate.txt` were properties of the codex
container (no `python -I` package visibility, no AF_UNIX permission, no
unshared network namespace, a different absolute Python toolchain path, nested
containment restrictions); none exists here, so **no full-gate row needed
R13**. Also green: all five mutation pairs RED then GREEN with the tree
restored, the 16-test defended-trial ring, the three owner-map exact checks,
`wheel_smoke`, `docs_verify --links` (0 dangling), and `diff_budget` at
`280/280 WITHIN`. Full transcript: `proof/revalidation-2026-09-03.txt`.

Three `docs_verify` rows remain RED and are disposed under R13 because each
reproduces on the untouched base in this same container:
`SEAM-llm-x-rules.md:54` and `INV-frozen-surfaces.md:181` are recorded
baselines in `docs/AUDIT_BASELINES.md`; `CON-run-identity.md:298` is a newly
found instrument-cost row (its claim passes when run alone, in 345 s, against
the verifier's own 300 s ceiling) and is parked as P6 with an errata entry.
Disposal is a statement about attribution: the three checks did not pass, and
nothing was weakened, skipped, xfailed, shimmed or edited to make them appear
to.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "using these for improvements" | done-with-assumption A1 | `b467951fa9`; VALIDATION S1-S4; all four supplied reviews explicitly adopted/rejected/bounded in SPEC.md and VALIDATION.md |
| R2 | "maximum modularity and configurability is essential" | done | VALIDATION S2 — constructor injection and a caller-named source are the only roads in; no global default, fallback, winner, aggregator or scheduler attachment |
| R3 | "usability by other humans" | done-with-assumption A3 | VALIDATION S3 — deterministic id, version, summary, manifest digest and a host-owned plain-language power explanation, inspectable without invoking anything |
| R4 | "formalism shouldn't out rank valid prose" | done-with-assumption A5 | VALIDATION S1/S4 — no dedicated machine-interpreted epistemic or representation-control field; `content`/`codec` are byte-preserving transport data; mutation-proven closed |
| R5 | "prose isn't always mechanically valid" | done | VALIDATION S1/S4 — prose is neither parsed nor required to be mechanically valid; four text shapes cross unchanged |
| R6 | "avoid mechanically defining optimisation targets or statistical tightening of any sort" | done | VALIDATION S1/S2 — no score, rank, weight, confidence, threshold, feedback or optimisation target; `score` and `priority` mutants both RED |
| R7 | "allow open exploration without the mechanical constraint that may hinder it" | done | VALIDATION S2/S4 — explicit opt-in use; disagreeing sources stay independent with no automatic selection |
| R8 | "Heuristics imply something about the problem space being known" | done | VALIDATION S1/S2 — no heuristic priority, learned order, candidate reduction, or presumed problem-space vocabulary |
| R9 | "Which is what I was trying to create with DeepReason" | done | VALIDATION S3 + `CON-authority.md` check — a source may contribute criticism and cannot decide status or run authority |
| R10 | "Perfect! Can you get started?" | done-with-assumption A2 | the implemented, tested, mapped and pushed phase-one module |
| R11 | "use alphaXiv plugin whenever exploring options" | done | VALIDATION S6 — four alphaXiv sources recorded in SPEC.md's Research disposition, each adopted, rejected or bounded, none adopted as authority |
| R12 | "You ran out of credit. Keep going" | done, and NO LONGER LOAD-BEARING | the codex container's missing `bc` does not exist here (`bc 1.07.1` present); that row is closed GREEN rather than disposed |
| R13 | "every full-gate and docs_verify RED row that reproduces on the untouched tranche base under the same container is an environment-only known-not-yours baseline… proceed to delivery" | done | ledgered verbatim in REQUEST.md at `8827168a3f` BEFORE it was acted on; applied to exactly three `docs_verify` rows, each with base-reproduction evidence in `proof/revalidation-2026-09-03.txt` §A/§B; applied to **zero** full-gate rows |
| C1 | "There shouldn't be any reasons why defended trial is rejected" | partially met, remainder PARKED P1 | this socket adds no rejection or downgrade and the 16-test defended ring is green; the shipped `formally_backed` prose refusal is untouched and remains parked |
| C2 | "Observe only should be easily switched off" | preserved | no source outcome selects `observe_only`; the `contribution_only` ceiling describes what the interface may RETURN and cannot choose run authority |
| C3 | "If you're trying to ensure previous runs are compatible, don't" | done | no compatibility layer, digest preservation or historical-root edit exists in the diff; no committed run root was opened |

No requirement is `not-done`. No requirement is `deferred`.

## Assumptions the operator may override

- **A1** — the smallest authorized first increment is an unwired
  contribution-only source contract; candidate reducers, evaluator fabrics,
  projections and ranking are excluded because they would recreate mechanisms
  you rejected.
- **A2** — "get started" authorizes this first implementation tranche, not
  merely a design document.
- **A3** — phase-one human usability is a deterministic registry description; a
  CLI configuration explainer is a separate tranche (parked P4).
- **A4** — the blast-radius instrument is authoritative for the
  no-frozen-contact decision; it returned `CLEAR` both at plan time and on the
  rebased tree.
- **A5** — representation neutrality means the boundary has no dedicated,
  machine-interpreted representation or epistemic-control field. Content and
  codec are transport data; the boundary neither derives a category nor decides
  whether any text is valid.

## Map delta

changed: `docs/map/CON-criticism-source.md` (now also owns
`src/deepreason/criticism_source.py`), `docs/map/CON-conjecture-kinds.md`,
`docs/map/CON-authority.md`
created: none
new checks: **3**, one per changed document, each run and green before it was
written down, and each re-run green on the rebased tree.

left stale: all three, and knowingly. `docs_verify --stale` lists
`CON-criticism-source.md` (1 commit), `CON-conjecture-kinds.md` (56) and
`CON-authority.md` (14). Their `Verified-at:` anchors necessarily precede the
commit that contains each document, so the stamps were NOT advanced — a stale
stamp is honest, a false one is not. Their exact checks were re-run at current
HEAD after the same-commit map move. The other 43 stale entries, the 20 missing
`Sweep:` headers, and the 2 `--coverage` findings (both on UNCHANGED seams) are
pre-existing map debt, parked under P5 rather than silently edited in a
behaviour tranche.

## Errata

**E72** (minted as E71; renumbered at merge, that number was taken) added to `docs/ERRATA.md` in this commit:
`docs/AUDIT_BASELINES.md`'s docs_verify failure LIST is incomplete on a capable
full clone. A second check, `docs/map/CON-run-identity.md:298`, still costs more
than the verifier's own 300 s per-check ceiling (345.31 s serially, where it
PASSES), so it can only ever report `TIMEOUT` inside `docs_verify`. E67 retired
that conditional class after narrowing one instance of it; this is a second
instance that was never listed, and the totals kept matching because it
contributes the count the retired row used to. Left uncorrected deliberately —
`AUDIT_BASELINES.md` may only move in the tranche that moves the value — and
parked as P6.

## Parked (not done, not promised)

Six entries in `PARKED.md`, each carrying a ready-to-send prompt:

- **P1** — reconcile prose with the defended-trial supremacy guard. The shipped
  `formally_backed` refusal can still turn a prose case away before defender
  and judges; that is the remaining half of C1 and it is a direct conflict with
  your standing "formalism shouldn't out rank valid prose" law.
- **P2** — connect source selection to a run without adding hidden policy
  (per-run configuration, scheduler invocation, graph recording).
- **P3** — audit the inherited heuristic and reduction channels that predate
  this socket: `ConjectureCandidate.typicality` with its `tail_weighted`
  ordering, the Pareto reporting frontier, and `_standing_recrit_pool`.
- **P4** — a human-facing configuration explainer (the CLI surface A3 deferred).
- **P5** — map debt only. Its original ask, a capable-environment rerun, was
  DISCHARGED by this tranche; what remains is the malformed check, the rotted
  `transport_failure` census, the coverage findings and the stale entries.
- **P6** — narrow `CON-run-identity.md:298` so it returns a verdict instead of
  `TIMEOUT`, exactly as `experiments/2026-08-31-defect-jailbreak-gate-closure`
  did for `SUB-application.md`, and move `docs/AUDIT_BASELINES.md` in the same
  commit.

**recommended next: P1.** It is the one place where shipped behaviour still
contradicts a standing operator law, and wiring any source into criticism (P2)
before it is settled would cement that refusal into a new extension path. P6 is
cheap and independent and can go to an inexpensive executor whenever convenient.

## Residue — what this does NOT establish

The socket has no graph consumer and was never exercised against a provider or
a committed run root: "the boundary holds" is proven, "it works in a run" is not
claimed and cannot be until P2. The mutation evidence establishes five
enumerated constraints on this tree, not suite-wide certification, and no
aggregate kill score is claimed. C1 is not closed globally. The three
`docs_verify` rows remain RED and disposed, not passing. Accepted does not mean
true.
