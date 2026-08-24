# Delivered: Rung 5 — promotion problems and their criteria as programs
Branch: `claude/rung-5-promotion-criteria-wu31d8` (pushed, tree clean)

## What changed

Before this tranche the harness could represent an artifact that FRAMES the
problems around it — Rung 4 built that — but nothing could make one exist. A
promotion problem had to be filed by hand, so in practice nothing ever had
standing, and an assertion addressed to one was consulted the moment it was
accepted, whether or not anyone had examined it.

Two mechanisms close that. **Reach nominates**: `calculus/nomination.py` is a
measure-rule over the log — when one subject's reach events span at least
`Config.K_FRAME` distinct problem LINEAGES over a coherent candidate scope, it
spawns a promotion problem and freezes everything the judgment will need into
one content-addressed `poietic.reach-certificate.v1` artifact. It detects and
decides nothing: it writes a problem, its criteria and that certificate, and no
label anywhere. **Five criteria judge**: `calculus/promotion.py` implements
subject-demarcation, reach-integrity, scope-determinism, compatibility and
accounts-for as ordinary registry programs, each a pure function of a
candidate's own bytes plus that frozen certificate — never live graph state.

`accounts-for` is the strong succession relation, built strong from the start.
Recovery, rigidity, non-immunization and a strictness witness, all four
required. A rival that recovers the incumbent's explicanda and nothing more is
refused.

Remark 9.5's closure is an ORDER rather than a rule:
`promotion_criteria_sweep` runs immediately after the reach sweep and before
anything consumes standing, so an unattacked assertion cannot silently frame its
scope — its criteria fire first, a `fail` mints a demonstrative warrant through
the tree's one warrant constructor, and the renderer declines it. An `overrun`
mints nothing.

New files: `calculus/nomination.py`, `calculus/promotion.py`,
`views/knowledge.py`. `claims.py` gains the certificate body and its five frozen
parts; `programs.py` gains six structural registrations; `Config` gains two
knobs; the scheduler gains one step; `deepreason standing` gains a knowledge
section.

## What now causes a promotion problem to exist

One artifact's reach events spanning `K_FRAME` (default 2) distinct problem
LINEAGES — where a lineage is traced through problem ancestry AND through the
origin problem of any artifact a problem was spawned from — over a scope that
compiles in the closed DSL and admits exactly the problems reached.

## What a rival must survive to be called a successor

All four, none optional: it accounts for everything the incumbent did (or
carries an unrefuted bounded-validity account of the residue); it is no easier
to vary over the shared explicanda; no proper functional component of it can be
removed while preserving every registered accounting and criticism outcome; and
at least one of recovery, criticism survival or rigidity is STRICT.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "NOMINATION as a measure-rule over the log … ≥ K_frame distinct problem lineages over a coherent candidate scope ⇒ Spawn a promotion problem" | done-with-assumptions A1, A2 | `97fa5ff84`; VALIDATION S1, S3 |
| R2 | "The measure DETECTS; it never decides" | done | `97fa5ff84`; VALIDATION S1, both halves; `INV-axiom-basis` A8 |
| R3 | "K_frame ships as a Config knob with its `_versioned_source_config_data` line for EVERY schema version" | done | `97fa5ff84`; VALIDATION S2 — measured, no key reaches `engine_config_json` |
| R4 | "The five pinned criteria as programs" | done-with-assumptions A3, A5, A10 | `e3a6cadf5`; VALIDATION S4–S7 |
| R5 | "accounts-for implements the STRONG succession relation … four parts, ALL required" | done-with-assumptions A6, A8 | `e3a6cadf5`; VALIDATION S8 |
| R6 | "Building the weak form first is FORBIDDEN" | done | `e3a6cadf5`; the mutation proof — dropping strictness reds exactly the rival-that-only-recovers test |
| R7 | "Remark 9.5's default-consult closure … demonstrative program warrants BEFORE the renderer's next consultation" | done-with-assumption A8 | `e3a6cadf5`, `bce396edb`; VALIDATION S9 |
| R8 | "for empirical scopes, at least one commitment must be observation-valued … reuse Rung 2's cost answer" | done-with-assumption A9 | `e3a6cadf5`; VALIDATION S4. The row-number citation is wrong and is now `docs/ERRATA.md` E48 |
| R9 | "the knowledge view, always rendered with its definition inline … never the bare word" | done-with-assumption A7 | `bce396edb`; VALIDATION S10 |
| R10 | "THE STRONG RELATION REFUSES, four ways … Mutation proof on at least the first" | done | `e3a6cadf5`; VALIDATION S8 + the pasted mutation proof |
| R11 | "M-4 BOTH HALVES, and the live root is the negative half" | done | `e3ac7e1fb`; VALIDATION S11 + its mutation proof |
| R12 | "an assertion registered outside a promotion problem is an ordinary artifact the renderer ignores; an unattacked one … does not silently frame its scope" | done | `e3a6cadf5`; VALIDATION S9 |
| R13 | "every criterion terminates inside its declared budget; overrun means unobtainable, never slow" | done | `e3a6cadf5`, corrected in `812aa1aba`; VALIDATION S12 |
| R14 | "the whole promotion path completes on a SOLO configuration" | done | `bce396edb`; VALIDATION S13 |
| R15 | "nomination measured on the committed attempt-4 root … rather than on synthetic data alone" | done | `e3ac7e1fb`; VALIDATION S11 |
| R16 | "PROVES A8 …; PRESERVES A4, Genesis Inertness" | done | `bce396edb`; `docs/map/INV-axiom-basis.md` |
| R17 | "Deliver R-by-R with pasted PROOF, closing with two lines" | done | this document |
| **Amendment 1** | (self-reported) C2 size ceiling | **EXCEEDED, reported** | REQUEST.md Amendment 1; VALIDATION "Constraint compliance" |

Nothing is deferred and nothing is not-done.

## Assumptions the operator may override

- **A1** A problem's lineage root is traced through problem ancestry AND through
  the ORIGIN problem (first `state.addr` entry) of artifact sources. Not a free
  choice — measured against the committed live root before any code was written.
- **A2** Nomination DERIVES the candidate scope as a canonical enumeration over
  the reached problems; it authors no frame assertion.
- **A3** The criteria read a frozen certificate through the existing
  `BLOB_PROGRAMS` widening, never live graph state.
- **A4** ONE frozen artifact, not Rider 5 clause (4)'s four. **A deviation** —
  parked as P2.
- **A5** The candidate pool is frozen at nomination; a later subject answers
  `overrun`. Parked as P1.
- **A6** `X(e)` reuses `reach_sweep`'s all-qualifying-pass test.
- **A7** The knowledge view is not a new public surface — no entry point, no MCP
  tool, no schema change. Both wheel smokes prove it.
- **A8** Warrants fire through `register_fail_warrant`; `overrun` mints nothing.
- **A9** R8's "drift row S-5" citation points at the wrong row. Reported, not
  resolved — `docs/ERRATA.md` E48.
- **A10** The six new programs are declared `structural` and dual-registered, so
  the promotion axis grounds no reach and buys no prose immunity.

## Map delta

**Changed:** `INV-axiom-basis` (A8 PROVED with the spawn-half check it demanded;
A4 and Genesis Inertness preservation), `SUB-calculus` (nomination, the
criteria, two new Traps, one row NARROWED), `SEAM-evaluation-x-rules` (the
promotion lifecycle — the ladder's named exit artifact — plus one new Trap),
`SEAM-evaluation-x-ontology`, `SUB-evaluation`, `SUB-rules`,
`SEAM-adjudication-x-rules`, `CON-standing-and-background` (one row NARROWED),
`CON-problem-layer-lifecycle`, `INV-frozen-surfaces` (the granted contact and
its measurement), `SEAM-manifest-x-schools`, `SUB-manifest`, `SUB-scheduler`,
`SUB-application`, `CON-schools`, `INDEX`. **Created:** none.
**New checks:** ~20, every one RUN before it was written down.

Two checks were NARROWED rather than updated, and both were mutation-proved
afterwards: `CON-standing`'s "the scheduler imports nothing from `calculus/`"
and `SUB-calculus`'s NO SCHEDULER INTEGRATION row. In each case the check was a
proxy that had drifted wider than the claim it stood for, and the narrower form
names the module and accessors, so it cannot be dodged by renaming an import.

**Left stale:** eight documents `--stale` still lists —
`CON-criticism-source`, `CON-run-identity`, `CON-seats`, `INV-signal-contract`,
`SEAM-llm-x-scheduler`, `SEAM-llm-x-workflow`, `SUB-llm`, `SUB-verification`.
Each was made stale by a commit that pre-dates this branch. Advancing a stamp
over checks I did not re-read for their own document's sake is the false stamp
the map's own rule forbids, so they are left and parked as P4.

## Errata

**E48** — the ladder and the operator's brief both cite drift row S-5 for
§12.2's empirical-scope clause; S-5 is a different row (standing is derived and
never stored). The obligation was never ambiguous; the pointer is wrong, and a
reader following it lands on something Rung 3 already discharged.

**E49** — E45's census lesson recurred one tranche later in its own shape. This
SPEC.md declared the FILES it planned to edit and not the SYMBOL its own spec
item named as the mechanism (`register_fail_warrant`), so three call-site count
pins went unpredicted and were caught by the boundary gate four commits later.

## Parked (not done, not promised)

- **P1** Re-nomination — a subject conjectured after nomination can never be
  judged against the incumbent.
- **P2** Rider 5 clause (4) names four frozen artifacts; this rung shipped one.
- **P3** `load-bearing` demarcation is never written, so criterion 1 can refuse
  and abstain but never confirm.
- **P4** Eight map documents carry stale `Verified-at:` stamps from earlier
  tranches.

Each carries its ready-to-send prompt in `PARKED.md`.

**Recommended next: P3.** It is the only one that changes what a live run can
currently DO: without the `load` reading, `promotion_subject_demarcation`
returns `pass` for no candidate at all, so a first live promotion is not
reachable. P1 and P2 are design questions with no live consequence yet; P4 is
housekeeping.

## The instruments, in full

- Full gate: **3939 passed, 6 skipped, 0 failed.** Baseline re-derived at
  `ade214037` in this session: 3879 + 6 skipped. Delta 60 = this tranche's tests.
- `docs_verify` full: 3 failed — exactly the known `CON-run-identity`
  shallow-clone failures. `--audit` 0 findings. `--links` 0 dangling.
  `--coverage` 2 findings, identical at the base. `--stale` 15 → 8.
- Both wheel smokes exit 0, although neither was owed.
- Frozen surfaces: 12 lines in `run_manifest.py`, under R3 and C1's own grant,
  measured to move no qualification digest. Surfaces 1, 2, 3, 5 untouched.
- The cycle soak was not run and is not owed: this rung launches nothing.
