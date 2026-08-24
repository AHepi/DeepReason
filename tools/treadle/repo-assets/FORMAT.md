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
