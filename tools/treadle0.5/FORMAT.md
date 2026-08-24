# Battery file machine grammar (zoo/batteries/FORMAT.md)

Parsed by scripts/battery_digest.py. Deviations fail acceptance.

1. One instance per heading, exactly: `### <ID> - <title>`
   where <ID> matches `^[PNB][0-9]+$` (P positive, N near-miss, B boundary).
2. The instance block is every line after its heading up to the next
   `### ` heading or the registry heading; digested as raw bytes with
   trailing whitespace stripped per line and exactly one final newline.
3. The file ends with the registry, exactly:

   ## Registry

   | id | kind | partner | digest |
   |----|------|---------|--------|
   | P1 | positive | N1 | PENDING-DIGEST |

   One row per instance, ids matching the headings one-to-one. The
   `kind` column is a CLOSED vocabulary: positive | near-miss | boundary
   (exactly these strings; P-ids are positive, N-ids near-miss, B-ids
   boundary, and the checker may enforce the correspondence). `partner`
   names the minimal-pair partner or `-`. Write PENDING-DIGEST; the tool
   fills real digests (`--write`) and acceptance verifies (`--verify`).

4. Refutation modes (FR-20). A battery that tests an INVARIANCE must say so:
   a rejected reading can fail by COLLAPSE (it gives both members of a pair
   the same status where the intent separates them) or by SPLIT (it separates
   members the intent holds equal). Invariances need SPLIT pairs; a battery
   that only detects collapse cannot test an invariance at all. Each pair's
   registry row may be annotated in prose with its mode; the pair index in
   the battery body SHOULD carry a `mode` column.

5. Separability statement (FR-20). When the battery serves a decision among
   named candidate options, the battery file MUST end (before the registry)
   with a short section stating, for every pair of live options, which
   instance separates them — or declaring the pair observationally
   inseparable. An inseparable pair means the choice is convention, not
   semantics, and the decider must be told.
