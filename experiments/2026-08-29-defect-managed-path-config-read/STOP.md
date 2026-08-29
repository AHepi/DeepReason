# STOP — the qualification price is measured, and the spend is the operator's call

Tranche: `experiments/2026-08-29-defect-managed-path-config-read/` (defect P14).
Raised at the end of stage 1 (goal / diagnose / reproduce), BEFORE any fix is
designed, exactly as the batch's frozen-surface disposition requires:

> IF carriage moves ANY QUALIFICATION SUBJECT DIGEST, that is a PRICED STOP,
> NOT a grant. Write the before/after digest and the battery cost into the lane
> parking brief, and STOP the lane. The operator decides that spend, not you.

A digest moves. The lane stops. Nothing was worked around, no gate was
weakened, and no fix was written.

## The decision, in one sentence

Letting `deepreason reason` read your `run-config.yaml` is free for 23 of the
24 gate switches — including all three you named — and costs one qualification
battery per home (~14 minutes, ~1160 provider calls, paid once then cached)
for the single switch that turns legacy criticism off; which of the three
carriage widths below should the fix implement?

## What is NOT at risk, said first

- **No committed run root changes.** Every one is READ, never recompiled.
- **No home pays anything today.** The default-valued configuration compiles
  byte-identically: manifest `sha256 37e3fa54edb75346…` and qualification
  subject `7c0ba0a174fdc2d9…`, both unchanged. A home only ever pays if its
  operator actually writes a configuration that asks for something — which
  today does nothing at all.
- **No frozen surface other than 4 is in play**, and surface 4 is not needed by
  any of the three roads below. This stop is about SPEND, not about permission.

## The three roads, priced

| road | what it carries | subject digests moved, over the 8 committed configs | battery cost |
|---|---|---|---|
| **A — narrow** | only the 25 `Config` fields the manifest's engine-config echo already drops | 7 of 8, all to ONE digest `99936f85f52b2471…` | one battery per home that sets `LEGACY_CRITICISM_ENABLED: false`; ZERO for every other switch |
| **B — full** | the operator's whole `Config`, except the seven fields the provider profile must own | 8 of 8, four distinct digests | one battery per home per distinct configuration |
| **C — disclose only** | nothing; read the file solely to emit `ENGINE_CONFIG_FIELD_NOT_CARRIED` notices | 0 of 8 | zero |

Measured, not estimated: `PRICE.md`, re-runnable as
`probe/price_qualification.py` -> `probe/price.out`.

The isolation measurement is what makes road A cheap. Carried one at a time,
23 of the 24 reachable dropped fields move NO digest at all —
`JUDGE_SEATS_ENABLED`, `ADJUDICATION_STATUS_AUTHORITY_ENABLED` and
`SCHOOL_SEATS_ENABLED` among them. Exactly one is priced:
`LEGACY_CRITICISM_ENABLED=False`, and it is priced because
`preparation.py:493-512` then compiles an engaged `criticism_policy` onto the
manifest — a real, typed behaviour-contract field. That is a case where
requalifying is arguably CORRECT rather than merely expensive: the run is
contracted to do something different, and the battery is the check that the
seats can do it.

## Recommendation: road A

- It satisfies the 2026-08-28 law's second limb for every switch the law names,
  at zero qualification cost for all but one.
- The one cost it does incur is a genuinely different behaviour contract, not a
  bookkeeping artefact — the case where a battery is the right answer.
- It cannot move a committed pin: dropped fields never enter
  `engine_config_json`, so `source_config_hash` is untouched at every schema
  version, which is the property the 2026-08-23, -26 and Rung 8 grants each had
  to prove for themselves.
- Road B additionally makes `RESEARCH_BACKEND` (and every other echoed field) a
  requalifying change, which is a much larger behavioural surface than the
  operator law asked for, and is better decided on its own evidence later.
- Road C is rejected on the same ground the P10 tranche rejected its own
  option C: a warning that carries nothing still cannot turn a gate ON, which
  is the half of the law that is still undelivered.

## What a "go" would authorise, precisely

Road A, plus the disposition of one consequence that is NOT a spend question
but must be answered in the same fix: **run identity does not currently cover
configuration** (`preparation.py:722`, `_request_digest` over a request with no
configuration field). Two runs of the same question under different
configurations would collide on one managed run id. Recorded as P18 in
`PARKED.md`; the fix tranche must dispose of it in FIX.md before code, either
by admitting the configuration digest into run identity or by stating what
stops the collision.

## Everything stage 1 owed is committed and complete

`GOAL.md` (with the map preflight ids), `DIAGNOSIS.md` (one primary cause,
41-root record evidence), `REPRO.md` + `tests/test_managed_path_config_read.py`
committed RED with `proof/repro_red.out`, `PRICE.md` + the re-runnable probe.
No production code was touched.
