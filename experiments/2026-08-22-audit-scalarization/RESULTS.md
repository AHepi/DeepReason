# Results — the scalarization census

Honest-ledger segments. What the record shows, and the residue: what remains
unproven. Accepted does not mean true.

---

## 2026-08-22 — census run at `2a744325f`, read-only

**Outcome: the claim survives, with one named exception.** "Grounded
adjudication is consumed as a partition, not as a ranking, confidence, or
weighted score" is now a checked statement over 193 distinct consumption lines
in 51 files, rather than a belief. The forbidden class is empty; one
SELECTION-BY-SCORE site exists and is medium severity; four near-misses and nine
lawful label-to-scalar conversions are recorded by name so the next reader does
not have to rediscover them.

### What was measured

The producer boundary was closed by re-derivation rather than judgement, using
two checks already committed in `docs/map/SUB-adjudication.md`: exactly two
modules in `src/` import the adjudication package (`harness.py`,
`invariants.py`), and `Harness._adjudicate` is the sole writer of
`state.status`. Adjudication therefore reaches the rest of the system through
four durable fields (`att`, `dep`, `status`, `conn`), the `Status` enum, direct
entry-point calls, and the record wire aliases — seven channels, enumerated
mechanically by `census_sites.py`.

    total candidate sites: 261   (a line matching two channels counts twice)
    distinct (file, line):  193
    distinct files:          51
    census rows:            110

`census_sites.py --check` reconciles the enumerator against `CENSUS.md`
line-by-line and exits 0: every enumerated site is classified exactly once. No
sampling, no cap, no representative-files shortcut.

### Verdict per class

| Class | Rows | |
|---|---|---|
| PRODUCER (excluded, listed) | 8 | the three logic modules, four `harness.py` groups, the `StateDiff` wire aliases, `conn_map` |
| EVIDENCE/LABEL FEEDBACK | **0** | as expected by construction |
| SELECTION-BY-SCORE | **1** | `bridge/evidence_pack.py` |
| ATTENTION/SCHEDULE | 75 | lawful; nine convert labels to a scalar, eight of those are thresholds |
| RENDER | 26 | lawful; no scalar is presented as a verdict |

### The one finding

`bridge/evidence_pack.py:757` sorts the ACCEPTED partition by `-hv` and `:766`
truncates to `MAX_EVIDENCE_PACK_ITEMS`. When survivors exceed the cap, a scalar
decides which reach the delivered evidence pack.

It is MEDIUM, not severe, and the reason matters: `hv` is
adjudication-independent (`measures/hv.py` contains no reference to `Status`),
so no adjudication result is being scalarised, and the ordering cannot promote
across strata — a REFUTED artifact never enters at any `hv`. By the source
paper's own criterion that is the LAWFUL kind of within-stratum ranking. The
truncation is what turns it into a selection. Two mechanical consequences: an
unmeasured survivor sorts below an `hv = 0.0` one (`-1.0` default), and `hv` is
a one-per-cycle variator-gated spot-check, so pack membership can turn on
whether the measurement happened to reach an artifact. Nothing records that a
truncation occurred. Parked as `PARKED.md` §P1.

### Zero feedback, and the four near-misses

Labels are a pure function of `(artifacts, warrants, commitments, carries)` —
the adjudication package's whole import surface is `deepreason.ontology`, and no
measure/rank/provenance word appears in its three logic modules (both checks are
committed in the map). The only remaining route would be a scalar steering
warrant minting. Seven modules construct a `Warrant(`; four of them
(`imports.py`, `informal/trial.py`, `ontology/warrant.py`, `rules/warrants.py`)
have zero enumerated sites, and `rules/crit.py` — the criticism source itself —
also has zero. The three that do read adjudication read partition membership,
never a number: `rules/relatedness.py:78` (prose-immunity, "the shield falls,
the artifact doesn't"), `rules/experiment.py:302` (a BOOLEAN sort key ordering
which carriers are executed to find a promotion witness, capped at 8),
`rules/vision.py:38` (refuted screenshots excluded from a critic's evidence),
plus `rules/guards/anti_relapse.py:293-389` on the admission side.

These four are recorded in a FEEDBACK-PROXIMITY ledger precisely because "no
scalar" is the reason each stays lawful, and that reason is exactly what a
future change could delete without tripping any current check.

### The compensatory sum

One site sums an adjudication-derived term with non-adjudication terms:
`informal/appellate.py:43` adds `+2` for an unresolved rivalry (≥2 ACCEPTED
rivals) alongside ensemble-split `+3`, audit-hit `+2`, guard-block `+1`, sorts
by `-score`, and truncates to `USER_RULINGS_BUDGET` (default 2). It is the
closest thing in the codebase to the -10pp shape. It remains lawful because it
allocates attention only, the user's ruling is an independent input that
registers as an ordinary attackable artifact, and its sole caller is the
operator-facing CLI — three conditions a later change could remove silently.
Recorded as finding-grade, parked as `PARKED.md` §P2.

### What the census confirms positively

- **The allocation signal contract holds at the consumer.** `controller.py` has
  zero references to `Status` or `state.status`; it reaches the graph only
  through two boolean readers (`controller.py:348,508,556`). `INV-signal-contract`'s
  interface-only clause is upheld where it matters, not just where it is stated.
- **`easy.py::pick_survivor` is the lawful model** for best-candidate selection:
  partition membership, then a purely typed tie-break `(event_seq, aid)`. Live
  in the website workflow at four call sites.
- **The Pareto frontier cannot scalarise**: `run_report` takes the partition
  first, then `capture/pareto.py::frontier` applies strict domination — no axis
  is summed, so no measure can promote a REFUTED artifact.
- **The findings surface refuses to name a winner**, in its own words: "the
  record deliberately preserves the disagreement rather than merging it."
- **The display layer works against scalar misreading**: `status_display.py`
  renames ACCEPTED to "unrefuted" ("survival, not endorsement"), and
  `views/why.py` tells the operator that a status is computed and cannot be set.

### Residue — what this does NOT establish

1. **It is a snapshot, not a property.** Nothing in the gate prevents a new
   status read from being added tomorrow in any shape. `CENSUS.md` §7 names four
   candidate regression pins in value order; none was written, because this
   tranche is read-only on `src/` and `tests/`.
2. **It is a static read of `src/deepreason/`.** No live run was used, and no
   committed root was replayed to observe an actual truncation in
   `bridge/evidence_pack.py`. The finding is established from the code path, not
   from a recorded pack that dropped a survivor. Whether the cap has ever
   actually bitten on a real root is UNMEASURED.
3. **`tests/` was not censused.** A test could encode a scalar consumption that
   `src/` does not, and this census would not see it.
4. **The classification of the nine label-to-scalar conversions rests on reading
   their consumers.** Each was traced one hop (e.g. `status_churn` →
   `runtime/stop.py:165`); a second hop was not walked exhaustively. The eight
   "threshold" verdicts are as good as those one-hop reads.
5. **The external claim itself is unverified here.** The -10pp / +16.7 numbers
   come from `docs/RESEARCH_SHAPE_CRITIQUE_2026-08-22.md`, which is
   operator-supplied external text with the standing of design intelligence, not
   evidence. This census does not confirm them; it acts on the question they
   raise.

### Also found (parked, not fixed)

`docs/map/INDEX.md`'s Subsystems table lists 15 documents; `docs/map/` holds 18
`SUB-*.md` files. `SUB-application.md`, `SUB-amendment.md` and
`SUB-periphery.md` are unroutable. This census reached `SUB-application.md` by
filename — the thing the map exists to make unnecessary. `PARKED.md` §P3,
including the check that would have caught it.

### Gate, sized read-only

`git diff --stat origin/main` touches no path under `src/` or `tests/`. No
pytest gate owed. No map document moved, so `docs_verify` was not run as a gate;
the two SUB-adjudication checks the census depends on were re-run individually
and both exit 0.
