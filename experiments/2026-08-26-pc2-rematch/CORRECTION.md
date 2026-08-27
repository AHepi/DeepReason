# CORRECTION — the retired 32768 attempt was NOT broken

Written 2026-08-27, before P-C2b is designed, because P-C2b's design would
otherwise inherit a false premise from Amendments 1 and 2.

## What I reported, and what the record actually says

I reported ARM H3's first attempt as failing with "100 % truncated, 100 %
arrival-invalid, produced nothing", and Amendment 1 raised `max_tokens` from
32 768 to 100 000 on that basis.

**The record does not support that reading.** The split-budget seat protocol
(`llm/split.py`) was ARMED and working the whole time:

| seat call | leg | max_tokens | valid | natural_stop |
|---|---|---|---|---|
| seq 27 | `reason` | 32 768 | False | False |
| seq 27 | **`extract`** | 32 768 | **True** | **True** |
| seq 41 | `reason` | 32 768 | False | False |
| seq 41 | **`extract`** | 32 768 | **True** | **True** |
| seq 45 | `reason` | 32 768 | False | False |
| seq 45 | **`extract`** | 32 768 | **True** | **True** |

**Every extract leg was valid, with a natural stop.** The run produced 18
artifacts and 6 warrants in 3 seat calls.

## Why I got it wrong

W6's `flow.scan_root` emits ONE row per `workflow-provider-attempt-v1`
object, and that row carries the REASON leg. The extract leg lives in the
log event's `attempt_trace`, which that instrument does not surface. I read
the reason leg's `truncated=True, arrival_valid=False` as the seat's outcome.

**It is the protocol's intended behaviour, and `split.py` says so in its own
docstring:** leg `reason` "deliberates in prose and is ALLOWED to be cut
off", leg `extract` "is fed whatever trace exists — truncated, or empty —
and does nothing but serialize it into the wire contract". A truncated
reason leg is the design working, not failing.

## What follows, stated plainly

1. **Amendment 1 was a fix to a non-problem.** The cap was not too small.
2. **Amendment 1 probably CAUSED Amendment 2's failure.** Raising the ceiling
   to 100 000 gave the reason leg a 99 488-token budget, and a leg that long
   ran past the 180 s socket timeout — the transport failure. At 32 768 the
   reason leg was bounded at 32 256 and completed.
3. **The evidenced configuration is 32 768**, which is also P-C1's and ARM
   S2's cap. `SPLIT_BUDGET_SEAT_PROTOCOL` defaults to `"auto"`, which arms
   exactly the seats whose route says they think — so with `reasoning` unset
   the protocol is already on, with no configuration needed.
4. **The timeout still needed raising, for a different reason.** Measured
   wall clock per seat call at 32 768, both legs: **737 s, 420 s, 460 s
   (mean 539 s)**. Every one exceeds a 180 s timeout. So Amendment 2's
   `timeout_s: 900` was right, and its stated cause was wrong.

## What this costs, and what it does not

Two run attempts were retired on a misdiagnosis. Both are kept and both
remain real measurements — the first now reads as a WORKING configuration
that was merely slow, which is a more useful fact than the one I recorded.

No committed result is affected: neither retired attempt was ever quoted as
an ARM H3 result, and ARM H2's numbers were measured with thinking off and
no split, so nothing in them depends on this.

**The rule I broke** is CLAUDE.md's own: *"When a run dies at cycle 0, READ
THE DIAGNOSTIC BLOB before theorising."* I read a summary instrument's row
instead of the attempt trace, and theorised from it twice.

---

## AMENDMENT, same day: "working" was too generous

P-C2b's soak found that the split protocol writes a record `verify_root`
rejects — the two legs go into `attempt_trace`, which replay validation reads
as a repair ladder. The retired 32 768 root carries **15 violations** across
four checks.

So this document's claim that the run "was working" holds for the PROVIDER
legs (all three extraction legs valid, natural stop) and **fails for the
record it wrote**. In this project the record is the only admissible
evidence, so both halves must be stated together: the legs succeeded and the
record is not replay-valid.

Full diagnosis, contrast table and ready-to-send prompt:
`experiments/2026-08-27-pc2b-symmetric-reasoning/BLOCKER.md`.
