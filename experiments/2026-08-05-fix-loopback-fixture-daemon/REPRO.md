# Reproduction

Form: **in-memory / structural** — imports the smoke module without
running `main()`, so nothing is built, installed, or dispatched. No
provider call, no network beyond loopback.

Artifact: `experiments/2026-08-05-fix-loopback-fixture-daemon/repro.py`

## Current output

    THE DEFECT, structurally:
      _provider_server call sites : 0
      _provider_server name refs  : 0
      ProviderState() constructions: 0
      -> the fixture is defined and unreachable

    THE PREDICTION: call the dead function directly
      server bound on port : 41491
      serve_forever thread : alive=True daemon=True
      POST /v1/chat/completions -> status=200
         completion present : True (17 chars)
         recorded by fixture: total_calls=1 qualification_calls=1

    VERDICT: fixture body SOUND -- only the wiring is missing

Confirms diagnosis: **yes.** DIAGNOSIS.md predicted that calling the
dead function directly would produce a live listener answering the
provider protocol, which would prove the body sound and the wiring the
sole defect. It does: the server binds, the daemon thread runs, a
realistic schema-bearing request returns 200 with a schema-conforming
completion (`{"candidates":[]}`), and the fixture's own accounting
records it as a qualification call.

## Two wrong turns on the way, kept because they shaped the artifact

The first two attempts got **401** and then **500**, and neither was a
fixture defect:

- 401 — the handler validates `Authorization` against `TEST_CREDENTIAL`;
  the first request sent `Bearer x`.
- 500 `loopback_fixture_failure` — the handler requires an advertised
  output schema (`_schema_from_request`, lines 1136-1149) and raises
  without one; the second request carried no `response_format`.

Both were the reproduction sending an unrealistic request, not the
fixture misbehaving. They are recorded because they establish something
the fix must respect: **the handler swallows every exception into an
opaque 500** (`except Exception:` at line 1229). Once the fixture is
wired up, any genuine fixture bug will surface to the product as a
500 with a fixed message and no traceback — the same class of blindness
that made this defect take two tranches to find. That is a finding for
FIX.md to consider, not a licence to rewrite the handler here.

## Post-fix expectation

- `repro.py` keeps printing the same two halves; its structural counts
  become `call sites: 1, name refs: 1, ProviderState(): 1` once
  `main()` wires the fixture, and the VERDICT line stays SOUND. It is a
  measurement of the wiring, so it changes with the fix rather than
  inverting.
- `python -u scripts/wheel_operational_smoke.py` reaches beyond
  `STAGE_QUALIFY` — the first time in the file's history — and exits 0.
- `python scripts/wheel_smoke.py` continues to exit 0.
- The full gate stays at 0 failed and `docs_verify` at 0 failed.
