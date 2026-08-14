# SPEC — Rung 1: vocabulary and groundwork

Traces to REQUEST.md R1–R9.

## Diff budget

**Ceiling: 300 lines** of cumulative insertions across `src/`, `tests/`,
`docs/`, measured by `python tools/diff_budget.py` against the branch point.
LADDER.md estimated 150–250; the ceiling carries the extra because scoping found
two more renderer sites than forecast.

## Changes

### S1 — the display seam maps `accepted → unrefuted` (R1, R2)

`src/deepreason/status_display.py::display_status` currently returns
`"standing"` when `workload_profile == "text"` and the raw value otherwise. It
becomes profile-independent and returns `"unrefuted"` for `Status.ACCEPTED`;
every other label renders unchanged (`refuted`, `suspended`,
`suspended_unsupported` are already the calculus's own words).

`workload_profile` and `authority_policy` are RETAINED in the signature, unused,
for the reason the docstring already gives for `authority_policy`: this is the
seam where later distinctions land without mutating the enum.

**Why `"standing"` must go, beyond H3:** it is the calculus's word for the OTHER
axis (§9.1 — an artifact's role in the economy of generation). Rung 4 introduces
that axis; a display label already using the word would make a reader of a text
run see "standing" meaning "unrefuted".

### S2 — `status_gloss` (R1)

New in the same module: `status_gloss(status) -> str`, returning the
plain-language meaning for the surfaces that have room for it. The glosses are
`RECONCILIATION.md` H3's table:

| stored | rendered | gloss |
|---|---|---|
| `accepted` | `unrefuted` | every attack so far is defeated — survival, not endorsement |
| `refuted` | `refuted` | a warranted attack stands |
| `suspended` | `suspended` | under unresolved attack |
| `suspended_unsupported` | `suspended_unsupported` | orphaned, not false — it lost its ground, it was not shown wrong |

Used by `views/why.py` (the human "why is this the status" surface). Other
surfaces route through `display_status` only; a gloss on every line would be
noise.

### S3 — five renderer sites route through the seam (R4)

| Site | Today |
|---|---|
| `views/why.py` (validity-node label) | `nu_status.value` |
| `views/why.py` (node label) | `status.value` |
| `views/evidence.py::_status` | `status.value` |
| `views/theory.py` | `status.value` |
| `views/export.py` (README `**Status:**`) | `status.value` |

Each becomes `display_status(...)`, preserving its existing absent-value
sentinel (`'?'`, `"unregistered"`, `'unknown'`) exactly.

### S4 — controller rename (R6)

`_under_standing_attack` → `_under_unresolved_attack`, with its one caller and
the one test reference. Private method; no stored string, no config name, no
event payload.

### S5 — `docs/map/CON-standing-and-background.md` (R5, R9)

New concept document per `SCHEMA.md`: `DR-CON-standing-and-background`, with
`Verified-at`, a `Verify:` command, `Owns:` (`status_display.py`), and the
standard sections. Content: the two axes, Prop 9.1's rigidity dilemma as the
rationale for why one axis cannot host P11, the vocabulary table, and the
three-site collision census. Checks must be able to fail — each pins a claim
that a future edit could break.

### S6 — CLAUDE.md design law (R7, R8)

One entry appended to "Operator design laws": the signal-contract layering,
attributed to the operator 2026-08-14, with the FROZEN/VERSIONED/FREE split and
the no-workflow-until-two-recipe-failures tripwire. Text only.

### S7 — regression tests

New `tests/test_calculus_vocabulary.py`:

1. stored labels unchanged — `Status.ACCEPTED.value == "accepted"` and the enum's
   full value set is exactly the four historical strings;
2. `display_status` returns `unrefuted` for both `text` and `formal` profiles;
3. the four glosses exist and are non-empty;
4. `views/theory.py` and `views/why.py` render `unrefuted` and never the bare
   word `accepted` for an accepted artifact;
5. machine JSON is untouched: `findings.py`'s `positions` dict still keys
   `"accepted"`.

Docstrings name the motivating program (`Regression (v2 calculus program, Rung
1): ...`).

## Predicted fixture updates (declared BEFORE any edit)

CLAUDE.md permits a fixture that depended on the old behaviour to be minimally
updated **only when the design document predicted it**. Predicted here, exactly
four assertions in `tests/test_text_authority_policy.py`:

| Line | Was | Becomes |
|---|---|---|
| 419 | `display_status(Status.ACCEPTED, "text") == "standing"` | `== "unrefuted"` |
| 420 | `display_status(Status.ACCEPTED, "formal") == "accepted"` | `== "unrefuted"` |
| 422 / 430 / 449 | `{"standing": 1}` | `{"unrefuted": 1}` |

No assertion is weakened: each still pins an exact label, and S7 adds the
stored-label test the old fixtures never had.

**Anything else that fails is NOT a predicted update** and is a stop.

## Acceptance checks

| # | R | Check |
|---|---|---|
| A1 | R1 | `display_status(Status.ACCEPTED, p) == "unrefuted"` for `p in {None,"text","formal"}` |
| A2 | R2 | `Status.ACCEPTED.value == "accepted"`; `grep` proves `ontology/state.py` contains no `"unrefuted"` |
| A3 | R2 | `findings.py` still emits the `"accepted"` machine key |
| A4 | R3 | `python tools/root_sweep.py` — zero verdict drift vs. the pre-change sweep |
| A5 | R4 | no `status.value` render survives in `views/` |
| A6 | R5 | `python tools/docs_verify.py` full — 0 failed; `--links` resolves the new id |
| A7 | R6 | `_under_standing_attack` appears nowhere in `src/` or `tests/` |
| A8 | R7 | the design law is in CLAUDE.md |
| A9 | R8 | no file added under `.claude/skills/` |
| A10 | all | `python -m pytest tests/ -q -n 4` — 0 failed |

## Out of scope, recorded

- **Pack vocabulary.** Packs render to the MODEL, not to a reader; changing what
  the generator sees is a behavioural change with live-run consequences, and H3's
  line is about reader-facing surfaces. Deferred, explicitly, to the rung that
  changes pack sections (Rung 6).
- **`RECRIT_STANDING` / `_standing_recrit_pool`** — REQUEST.md §4, parked to
  Rung 4.
- **The signal-contract MECHANISM** — Rung 1b.
