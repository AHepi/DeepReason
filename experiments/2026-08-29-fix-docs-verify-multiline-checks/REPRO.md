# REPRO — the smallest demonstration, at two levels

## Level 1 — the parser (offline, instant)

A scratch map document holding TWO checks that must both fail, one
multi-line and one single-line as a control:

```
`check: python -c "
assert False, 'this multi-line check must fail the run'
"`
...
`check: python -c "assert False, 'single-line control'"`
```

Against `tools/docs_verify.py` at main `ae490e26b`:

```
planted document holds TWO failing checks (1 multi-line, 1 single-line)
parser sees: 1 -> [(12, 'python -c "assert False, \'single-line control\'"')]

checks the instrument counts across docs/map/: 1142
```

1142 = the map's 1141 real single-line checks plus the planted control.
The multi-line failure is not among them. It is not reported as
skipped, malformed, or unparsed; it does not exist to the instrument.

## Level 2 — the whole run (the verdict is unmoved)

The same planted document, full `python tools/docs_verify.py`, with and
without the multi-line failing check:

```
RUN A (multi-line failing check present):  docs_verify: 502 failed
RUN B (multi-line failing check removed):  docs_verify: 502 failed
```

Identical verdicts. A check written to fail the run cannot fail the run.

The 502 is an ENVIRONMENT artifact of that measurement, not a map
finding, and it is recorded here so it is never mistaken for one: this
container has `python` -> `/usr/local/bin/python` while `pip` ->
`/usr/bin/pip`, so `pip install -e .` armed a different interpreter than
the checks invoke, and every `python -m pytest` check died with
`No module named pytest`. Corrected for R3 with
`python -m pip install -e . pytest pytest-xdist jsonschema
--break-system-packages`. R3's numbers are taken only after that.

## What the reproduction fixes about the diagnosis

Nothing was revised. The blob-first discipline applies to run deaths;
here the instrument's own parse output is the primary record and it says
what the monitor said it says.
