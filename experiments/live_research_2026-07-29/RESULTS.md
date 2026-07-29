# Live in-run research: glm-5.2 under two frozen allowlists (2026-07-29)

One frontier model (glm-5.2 on Ollama Cloud), one question — what
distinguishes an idempotent operation from a safe one, and which does an
append-only event log require of its writers — asked twice, with the ONLY
difference between runs being the frozen research domain allowlist:

- **wide**: `en.wikipedia.org`, `www.rfc-editor.org`
- **narrow**: `docs.python.org`

Each allowlist is manifest behavior, so each ladder ran its own full
qualification battery (wide 484 s, narrow 443 s, both rc=0 at full tier —
the first qualifications ever run against a schema exposing
`research_proposals`). Every claim below is re-derived from append-only
logs; the audit JSONs beside this file carry the complete records.

## What the model did, live

**In all three runs glm-5.2 proposed directed research unprompted by any
example — three proposals per run, every URL on-topic.** It translated the
question into whatever its frozen list allowed: RFC 9110 §9.2 section URLs
under the wide list; Python `logging`/`sqlite3`/`queue` documentation —
retry semantics, append-mode handlers, delivery guarantees — under the
narrow list. No proposal ever targeted an off-list host: told the truth
about the frozen allowlist in the question text, the model stayed inside it.

## Three runs, three containment stories

**narrow (run-7d8723fb) — the full success path.** Three proposals →
granted → fetched (4/6 request budget; the two-URL proposal spent two) →
packaged → consumed into 100 citable admission blocks → run completed →
bridge composed at `partially_answered`. Replay valid.

**wide, first attempt (run-0c3ce902) — fetch success plus a live
byte-ceiling refusal, then a harness crash.** The model fetched RFC and
Wikipedia material successfully (consumed, citable), and one response
exceeded the frozen 4 MiB per-response ceiling — refused with a typed
`RESEARCH_RESPONSE_TOO_LARGE` attempt inside a `nothing_fetched` receipt,
request spent. The reasoning then crashed mid-run on a simulation-only
assumption in the scheduler (see "Harness fixes"). The root replays VALID
and is pinned as the regression fixture `tests/test_research_root_replay.py`.

**wide, second attempt (run-5a771259) — typed exhaustion end to end.** The
model proposed `rfc9110#section-9.2` URLs; the redirect chain landed on a
page exceeding the 4 MiB ceiling, so all three URLs were refused (typed,
one spent request per hop), exhausting the 6-request budget exactly
(receipt `nothing_fetched`, 6/6). The two follow-up proposals were DENIED
with typed `requests_budget_exhausted` transitions — the cumulative budget
working live. The run then completed and bridged at `partially_answered`
**with the fetch refusals surfacing in the final answer's epistemics**: the
composed output explicitly records that verbatim RFC definitions are
unavailable and downgrades exactly the claims that needed them, while still
answering the core question (writers cannot be "safe"; the log requires
idempotence — with a preserved live rivalry over whether RFC-sense
idempotence suffices or a stronger log-specific dedup property is needed).

## Harness fixes the live runs forced

The first live research-enabled run exposed three simulation-only
assumptions outside the capability layer, each now fixed and committed:

1. `write_tranche_a_audits` crashed on research proposals/consumptions;
   it now reports contained fetches (RESEARCH_SOURCE_AUDIT.md) and counts
   research requests in TOKEN_ACCOUNTING.json.
2. `verify_root` crashed on research grants/compiled/receipts/packages and
   checked all capability transitions against the simulation policy digest;
   it now validates the research chain against the frozen research policy
   (allowlist host membership, request/source budgets, per-turn caps).
3. The scheduler treated any unconsumed `RESULT_PACKAGED` package as a
   simulation follow-up — this crashed run-0c3ce902; research packages now
   stay inside their own conjecture cycle.

## Honest caveats

- The wide/narrow ladder questions contain a literal `'\''` artifact from a
  quoting bug in `run_research.sh`; run-5a771259 used the clean text. The
  question semantics were unaffected.
- Fetched material became citable blocks, but no candidate in these short
  (6-cycle) runs recorded an `evidence-citation` measure against them —
  citable blocks surface in packs for later turns, and the runs ended
  before any candidate cited one. Demonstrating a byte-checked citation of
  fetched text in a live run remains open.
- `bridge_trio.py` reports `FAIL bridge_result has resolution` on both
  completed runs; it reads a key the result payload does not carry. Both
  bridges completed with `process_status=success`,
  `resolution=partially_answered` (see bridge-status lines in the .txt).
- run-0c3ce902's reasoning is incomplete (crashed pre-fix); its value is
  the intact, replay-valid research record.
