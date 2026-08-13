# Reproduction

Form: unit-test (offline, no provider, no live run)

Artifact:
`experiments/2026-08-13-defect-controller-steering-inert/repro_controller_inert.py`

Fidelity — the fixture mirrors the record, not a convenience:
  - the SAME eleven role names `run-manifest.json` binds, not a subset;
  - every endpoint at the SAME `max_tokens=16384` the manifest pins;
  - clean signal only for the five roles the log shows actually calling a
    provider (`judge`, `argumentative_critic`, `defender`, `conjecturer`,
    `variator`), with `truncated=False, attempts=1` on every call —
    exactly the process signal the 666 `event.llm` records carry;
  - more than `CLEAN_WINDOWS` calls per role, so the efficiency branch is
    eligible and dwell cannot be the explanation;
  - eight cycles stepped, so `dwell=2` cannot be the explanation either.

Current output (verbatim, `python experiments/2026-08-13-defect-controller-steering-inert/repro_controller_inert.py`, exit 0):

    PART A — grounded manifest reproduced offline
      roles bound                 : 11
      every endpoint max_tokens   : [16384]
      roles with clean signal     : ['argumentative_critic', 'conjecturer', 'defender', 'judge', 'variator']
      controller.step() over 8 cy : [None, None, None, None, None, None, None, None]
      policy artifacts emitted    : 0
      controller-* records in log : []
      => inert, and SILENT        : True

    PART B — control: one cap moved inside its envelope
      conjecturer cap before      : 3000
      controller.step() cycle 1   : {'cap:conjecturer': 1875}
      conjecturer cap after       : 1875
      other caps unchanged        : [16384]
      policy artifacts emitted    : 1
      => steers normally          : True

    REPRODUCED: the controller is inert on manifest caps and steers on
    in-envelope caps. The envelope table is the gate.

Confirms diagnosis: yes. Part A shows the whole failure at once — the
controller is attached, has abundant valid process signal on five roles,
steps eight times, moves nothing, and writes NOTHING to the record. Part B
holds every variable fixed except one cap, moved from 16,384 (outside
`cap:conjecturer`'s `[800,5000]`) to 3,000 (inside it), and the controller
immediately proposes `{"cap:conjecturer": 1875}` — the exact value
DIAGNOSIS.md predicted, `round(3000/1.6)` — and emits one policy artifact.
The envelope bound is the gate; the wiring, the signal, the dwell and the
clean-streak logic are all working.

The two silent skips are separated by the two parts: the six roles with
envelopes fail at `controller.py:270` (out of range), the five without
fail at `controller.py:259` (no entry) — Part B's "other caps unchanged:
[16384]" line shows both classes still frozen while the one in-range role
moves.

Post-fix expectation:
  - Part A's `controller.step() over 8 cy` no longer reads all-`None`
    with an empty record. Whichever of the two shapes the approved FIX.md
    chooses, the assertion inverts cleanly:
      (i) if envelopes are widened/extended to cover the manifest's bound
          roles, `policy artifacts emitted` becomes >= 1 and the caps move
          within the new bounds; or
      (ii) if a role or cap remains genuinely unsteerable, `controller-*
          records in log` is NON-empty and names the typed
          nothing-to-steer reason per role.
    Silence — all-`None` AND an empty record — must become impossible.
  - Part B must keep passing UNCHANGED. It is the guard that a fix which
    widens envelopes does not break ordinary in-envelope steering.

Production code untouched by this phase.

## Post-fix re-run (added by dr-implement-fix, 2026-08-13)

The artifact inverted. It now exits **1** — "NOT REPRODUCED" — which is
the passing state for a fixed defect, exactly as the expectation above
specified. Verbatim:

    PART A — grounded manifest reproduced offline
      roles bound                 : 11
      every endpoint max_tokens   : [2500, 16384]
      roles with clean signal     : ['argumentative_critic', 'conjecturer', 'defender', 'judge', 'variator']
      controller.step() over 8 cy : [{'cap:judge': 10240, 'cap:argumentative_critic': 10240, 'cap:defender': 10240, 'cap:conjecturer': 10240, 'cap:variator': 10240}, None, {'cap:judge': 6400, ...}, None, {'cap:judge': 4000, ...}, None, {'cap:judge': 2500, ...}, None]
      policy artifacts emitted    : 4
      controller-* records in log : [['controller-authority', 'full', '{"steerable":["argumentative_critic","conjecturer","defender","grounding_reviewer","judge","property_designer","summarizer","synthesizer","thesis","variator","vision_critic"],"unsteerable":{}}']]
      => inert, and SILENT        : False

Read against the pre-fix output: eight `None`s became four real
proposals over five roles (damped to alternate cycles by `dwell=2`,
which is the design working, not a miss), zero policy artifacts became
four, and the empty record now carries one `controller-authority`
statement naming all eleven bound roles as steerable. Part B's
conjecturer still lands on exactly **1875** — the value DIAGNOSIS.md
predicted — while the other ten roles, which pre-fix were frozen at
16,384, now steer alongside it. Part B's `first == {"cap:conjecturer":
1875}` equality is therefore obsolete BY THE FIX rather than broken by
it: the whole point was that the other roles stop being excluded.

The artifact is kept unmodified as the dated record of the defect. Its
regression successor, which asserts the post-fix expectations and is run
by the gate, is `tests/test_controller_steering_parity.py`.
