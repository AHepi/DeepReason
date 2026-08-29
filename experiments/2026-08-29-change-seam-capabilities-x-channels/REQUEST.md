# REQUEST — write `docs/map/SEAM-capabilities-x-channels.md`

Lane D of the 2026-08-29 parallel batch. Docs-only: **zero `src/` paths may
appear in this tranche's diff.**

## Authority, verbatim

The standing request is P5 of the execution-safety tranche
(`experiments/2026-08-27-change-execution-safety/PARKED.md`), quoted whole
because it is the authority this tranche traces to:

> ## P5 — LOW: the `capabilities × channels` seam has no map document
>
> **What.** `docs/map/INV-evidence-channels.md` lists
> `Seams-undocumented: capabilities x channels, channels x manifest`. This
> tranche's whole subject — a channel flag that is ON over a capability
> road that is severed — lives exactly on the first of those. Recorded per
> the map preflight rule that a missing id is a finding, not a blocker.
>
> WHAT THE SEAM ACTUALLY IS, with the worked example already in hand:
> a channel's enablement flag (channels.py) and a capability's dispatchable
> road (capabilities/policy.py runner_profile, capabilities/simulation.py
> admission) are two different facts, and the second can be severed while
> the first says ON. experiments/2026-08-27-change-execution-safety/SPEC.md
> findings F2 and F3 are the case study; commit 74d9f71ca is the live
> record of it costing four epochs.
>
> The document's Traps section owns that story, with its run id.
>
> GATE: python tools/docs_verify.py, and --audit must not refuse any check
> you write.

## Numbered requirements

- **R1** — author `docs/map/SEAM-capabilities-x-channels.md` to `SCHEMA.md`:
  sides alphabetical in the filename, canonical id on line 1, required
  headers, bare `DR-` cross-references, `Seams:` naming only documents that
  EXIST.
- **R2** — every load-bearing claim carries a SINGLE-LINE `check:` at column 0
  that exits 0. Run each before writing it down.
- **R3** — say which FRACTION of each side is actually involved, and what the
  two sides AGREE about — what the fields of one record MEAN to the other.
- **R4** — a `Traps` section naming the real recorded incidents: the
  execution-safety F2/F3 severed road, and audit finding F-A's silent config
  revert.
- **R5** — update `docs/map/INDEX.md` in the SAME commit: routing table and
  seam matrix row, with MEASURED coupling (counted, never estimated).
- **R6** — back-reference the seam from both sides' `Seams:` /
  `Seams-undocumented:` header lines only.
- **R7** — `docs_verify.py` at the measured 4-failure baseline; `--links`
  resolves every `DR-` reference; `--audit` refuses none of the new checks.
  Demonstrate at least two checks going RED under a deliberate mutation.

## MAP PREFLIGHT (CLAUDE.md, recorded here so every later phase starts from
## the same map)

| Id | Role in this tranche |
|---|---|
| `DR-SEAM-capabilities-x-channels` | **the document this tranche creates** — did not exist |
| `DR-SUB-capabilities` | the capabilities side; `Owns: src/deepreason/capabilities/` |
| `DR-INV-evidence-channels` | the channels side; `Owns: src/deepreason/channels.py`. There is no `SUB-channels.md`, so this side of the seam is an `INV-` document |
| `DR-INV-frozen-surfaces` | read BEFORE designing. `capabilities/state.py` (surface 1) and `run_manifest.py` (surface 4) are both frozen and both sit near this seam |
| `DR-SEAM-capabilities-x-rules` | the sibling seam already written on the capabilities side; read for the house style of a capabilities seam |
| `DR-SEAM-llm-x-verification` | the precedent for a ZERO-COUPLING seam — the shape this pair turns out to have |
| `DR-CON-capability-lifecycle` | the typed walk the channel decision gates |
| `DR-INDEX` | routing table + seam matrix, updated in the same commit |

**Frozen-surface finding, recorded before designing:** this seam's two `Owns:`
files — `src/deepreason/capabilities/` and `src/deepreason/channels.py` — are
NOT frozen. But the decision this seam carries is frozen INTO a surface that
is: the compiled `inquiry_capability_policy` lives in the manifest, and
`run_manifest.py` is surface 4. This tranche writes no code and therefore
contacts no frozen surface; the fact is recorded because any FUTURE change to
how a channel reaches a capability moves a manifest schema.

## Source finding — one cited source is not on this tree

`INV-evidence-channels.md` and PARKED.md P3 both cite commit `74d9f71ca` on
branch `claude/spec-to-code-technique-k5209o` as the live record of the severed
simulation road. Neither that commit nor `experiments/2026-08-27-change-technique-run/`
is reachable from this worktree:

    $ git cat-file -t 74d9f71ca
    fatal: Not a valid object name 74d9f71ca

So the live four-epoch evidence is cited here at SECOND HAND, through the two
committed documents that quote it, and the seam document says so rather than
implying a root it could re-read. Reported as a finding, not worked around.
