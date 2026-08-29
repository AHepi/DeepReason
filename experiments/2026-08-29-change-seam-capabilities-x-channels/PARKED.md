# PARKED — found on the way, not fixed here

Cone rule for this lane: `docs/map/SEAM-capabilities-x-channels.md` (new),
`docs/map/INDEX.md`, the `Seams:`/`Seams-undocumented:` HEADER LINES of
`SUB-capabilities.md` and `INV-evidence-channels.md`, and this tranche
directory. Nothing else. Each finding below is outside that cone and is
recorded rather than made.

---

## P1 — HIGH: multi-line `check:` blocks in map documents NEVER RUN

**What.** `tools/docs_verify.py` parses a check with
`_CHECK = re.compile(r"^\`check:\s*(?P<cmd>.+?)\`\s*$")`, matched against one
line at a time (`for line in text.splitlines()`). A check written as
``` `check: python -c " ``` followed by further lines and a closing ``` "` ```
therefore matches NOTHING and is silently skipped. The claim looks
authenticated and is not.

**Measured on this tree** (`experiments/2026-08-29-change-seam-capabilities-x-channels/proof/parse_census.txt`):

**Repo-wide: 72 check lines across 27 of the map's documents never run.** The
worst offenders, and the two documents that are the sides of this seam:

| Document | lines beginning `` `check: `` | checks actually parsed | never run |
|---|---|---|---|
| `docs/map/INV-frozen-surfaces.md` | 48 | 38 | **10** |
| `docs/map/INV-axiom-basis.md` | 43 | 35 | **8** |
| `docs/map/INV-render-layout.md` | 11 | 4 | **7** |
| `docs/map/SUB-calculus.md` | 35 | 29 | **6** |
| `docs/map/INV-evidence-channels.md` | 10 | 5 | **5** |
| `docs/map/CON-scheduler-ranking.md` | 13 | 9 | **4** |
| `docs/map/SEAM-llm-x-verification.md` | 4 | 1 | **3** |
| `docs/map/SUB-capabilities.md` | 18 | 17 | **1** |
| ...20 more | | | |

`INV-frozen-surfaces.md` heads the list, which is the sharpest form of the
problem: ten of the claims authenticating the repository's frozen-surface
grants are not being re-derived by the instrument that reports itself green.

Among the five unrun claims in `INV-evidence-channels.md` are the registry's
own membership check, the `enforcement`/`toggle` well-formedness check, the
`CHANNEL_UNKNOWN` notice check and the `DECOMMISSIONED` website check — the
four load-bearing claims of the channels side of this seam.

**Not fixed here** because `tools/docs_verify.py` is an external stop line for
this batch (another window is live on it) and rewriting other documents' checks
is outside this lane's cone. This tranche's own ten checks are all SINGLE-LINE
and all verified to parse and run.

**Prompt:**

```
TARGET REPOSITORY: AHepi/DeepReason.

Route through deepreason-orchestrator (this is a defect: claims that present
as checked are not checked). One tranche, one goal: no map document may carry
a `check:` that tools/docs_verify.py silently skips.

THE DEFECT, already measured — cite, do not re-derive:
experiments/2026-08-29-change-seam-capabilities-x-channels/PARKED.md P1 and
its proof/parse_census.txt. tools/docs_verify.py's _CHECK regex is matched per
LINE, so every multi-line `check: python -c "` ... `"` block parses as zero
checks. INV-evidence-channels.md has 10 check lines and 5 parsed checks;
SEAM-llm-x-verification.md has 4 and 1.

DECIDE FIRST, and say which in SPEC.md:
(a) teach the parser the multi-line form (a continuation until the closing
    backtick), or
(b) rewrite every multi-line check as a single line.
A separate window was reported to be landing (a) — check whether it landed
before choosing, and do not duplicate it.

EITHER WAY, the tranche must add the thing whose absence let this happen: a
docs_verify mode that FAILS when a document contains a line starting
`` `check: `` that did not become a parsed check. A silently-skipped check is
worse than an absent one, exactly as SCHEMA.md says of `check: true`.

PROOF OBLIGATION: run the newly-parsed checks. Some of them have not executed
since they were written and may be red on their own merits; a red one is a
finding for its own tranche, not something to weaken.

GATE: python tools/docs_verify.py, python tools/docs_verify.py --audit.
```

---

## P2 — LOW: `SUB-capabilities.md`'s body Seams table still says this pair is undocumented

**What.** `docs/map/SUB-capabilities.md` carries a `## Seams` table whose
`capabilities x channels` row reads `undocumented`. That row is now false —
`DR-SEAM-capabilities-x-channels` exists and the header line names it. This
lane's cone permits only the `Seams:`/`Seams-undocumented:` HEADER LINES of
that file, so the body row is left stale rather than edited out of cone.

Related and pre-existing: that same body table listed `capabilities x channels`
while the file's own `Seams-undocumented:` HEADER did NOT — the two disagreed
before this tranche. `--links` cannot catch it, because a body-table row is
prose.

**Prompt:**

```
TARGET REPOSITORY: AHepi/DeepReason.

Route through dr-change-orchestrator. One tranche, one goal: docs/map/
SUB-capabilities.md's body `## Seams` table agrees with its own headers.

WHAT TO DO: set the `capabilities x channels` row's Status to `documented` and
name DR-SEAM-capabilities-x-channels, the way the `capabilities x rules` row
already does. While there, reconcile every other row against the file's
`Seams:` and `Seams-undocumented:` header lines — they were already out of
agreement before 2026-08-29 (the channels pair appeared in the body and not in
the header).

THEN MAKE IT ENFORCEABLE, because a prose table drifts again: add a check to
that document asserting every body-table row's pair appears in exactly one of
the two headers, and every header entry appears as a row. That check must be
able to fail — verify with tools/docs_verify.py --audit.

SCOPE: docs/map/SUB-capabilities.md only. No src changes.

GATE: python tools/docs_verify.py at baseline, --links clean, --audit refuses
nothing.
```

---

## P3 — LOW: `INV-evidence-channels.md`'s "Where the toggle is read" table predates the runner fix

**What.** That table's `simulation` row says OFF compiles to
`SimulationCapabilityPolicyV1()`, which is correct. But the document's last
Trap still describes the severed simulation road in the PRESENT tense ("The
flag said ON from 2026-08-26; every `sandboxed_python_v1` proposal was
nonetheless denied `runner_profile_mismatch`") without recording that the
default runner flipped to `contained` on 2026-08-28 and the road is now
connected. Measured here: `engaged_simulation_policy` returns
`runner_profile="simulation.container.v1"` with the matching contained
toolchain. A Trap is never deleted, but per SCHEMA.md it is rewritten to say
when it was fixed; this one has not been.

Not fixed here: `INV-evidence-channels.md` body prose is outside this lane's
cone. `DR-SEAM-capabilities-x-channels`'s own Traps section records the fix
date, so the fact is now on the record somewhere.

**Prompt:**

```
TARGET REPOSITORY: AHepi/DeepReason.

Route through dr-change-orchestrator. One tranche, one goal: docs/map/
INV-evidence-channels.md's severed-simulation-road Trap says when it was fixed.

THE FACT, already measured — cite, do not re-derive:
docs/map/SEAM-capabilities-x-channels.md, first Traps entry. The 2026-08-28
default flip to the contained runner pairs runner_profile
(simulation.container.v1) with its own bound toolchain
(python@deepreason-public-contained.v1), so runner_profile_mismatch no longer
fires on the default configuration.

WHAT TO DO: rewrite that Trap to say it was fixed and when — never delete it
(SCHEMA.md) — and add the typed disclosure that now exists,
v6_policy.simulation_runner_notices' SIMULATION_RUNNER_UNAVAILABLE, to the
"Where the toggle is read" section. That notice is the P3 the execution-safety
tranche parked; record that it landed.

WHILE THERE: five of this document's ten `check:` lines never run (see
experiments/2026-08-29-change-seam-capabilities-x-channels/PARKED.md P1). If
P1's tranche has not landed, rewrite them single-line here and run them; some
may be red on their own merits, which is a finding, not something to weaken.

GATE: python tools/docs_verify.py, --audit refuses nothing.
```
