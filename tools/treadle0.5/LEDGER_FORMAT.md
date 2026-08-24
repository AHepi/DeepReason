# LEDGER_FORMAT.md — the review-call ledger

One JSONL file (canonically `zoo/reviews/calls.jsonl`), append-only, one row
per external model call, written by `review_harness.py`.

## Row fields

| field | meaning |
|---|---|
| `seq` | 1-based, contiguous |
| `prev_sha256` | sha256 of the previous row's exact bytes ("GENESIS" for row 1) |
| `job` | job name |
| `model` | exact model tag — DATED tags only; an undated tag silently moves |
| `role` | REVIEWER / BACK-TRANSLATOR / COMPARATOR / ... |
| `params` | temperature, seed, max_tokens as configured |
| `system_sha256`, `prompt_sha256` | digests of the exact bytes sent |
| `reply_sha256`, `reply_chars` | digests of the exact bytes received |
| `out` | transcript path the reply was written to |

## The four semantics (each is a field report)

1. **What the ledger guarantees** (and all it guarantees): the exact bytes
   each model was SHOWN can be rechecked, because packets are assembled from
   named file slices and the prompt digest is recorded. It is auditability.
2. **It is not reproducibility** (FR-16). An identical packet at temperature
   0 with a fixed seed has returned different replies. `params` is
   provenance. Transcripts carry `reproducibility: none` in their header,
   and no external call is ever an acceptance command.
3. **Superseded rows** (FR-17). A re-run job overwrites its transcript; the
   ledger keeps every row. The transcript must agree with the LATEST row
   naming its path; older rows for that path are superseded but keep their
   digests, so a reader can see a different packet was sent and its reply is
   gone. The hash chain covers superseded rows: a re-run cannot drop one.
4. **No credentials** (standing). Keys live in the process environment only.
   Verification fails any row containing `api_key`, `authorization`, or a
   bearer token shape.

## Verification

`review_harness.verify_ledger(path, transcripts_root)` checks: contiguous
seq; unbroken hash chain; latest-row-per-path agreement with the transcript
header; digests present on every row including superseded ones; no
credential material. Run it in your test suite; prove it per SETUP step 5 by
corrupting a COPY.
