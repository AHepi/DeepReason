"""Regenerate FORM_DR1_RUN_APPLICATION.md's Parts A/B1/D FROM IntakeFormV1.

Parts A (provider setup), B1 (seat assignments), and D (the question) are
generated from `IntakeFormV1`'s own `Field(description=...)` text, so the
form and the schema that actually validates it cannot drift apart the way
the prior hand-maintained prose could (and did — five stale `†` markers as
of 2026-08-11). Parts B2 through H are NOT regenerated: they document
surfaces `IntakeFormV1` does not model (either unmerged-branch-only, or
requiring external state a standalone file validator cannot see — see
SPEC.md Addendum 2, experiments/2026-08-11-change-qualification-messages-
s4b/) and remain the existing hand-maintained prose, untouched by this tool.

Usage:
    python tools/render_form_dr1.py           # write the file
    python tools/render_form_dr1.py --check   # exit 1 if the committed
                                               # file is stale, 0 if fresh
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FORM_PATH = Path(__file__).resolve().parent.parent / "docs" / "FORM_DR1_RUN_APPLICATION.md"

_LABEL = re.compile(r"^([A-Z])(\d+)")


def _sort_key(name: str, description: str, declaration_index: int) -> tuple:
    matched = _LABEL.match(description)
    letter, number = (matched.group(1), int(matched.group(2))) if matched else ("Z", 0)
    # Same label (e.g. two D5 fields) ties on declaration order in
    # IntakeFormV1, not field name — dossier/attach/allow_partial keep the
    # order they're declared in, not alphabetical.
    return (letter, number, declaration_index)


def _bullets(names: list[str]) -> str:
    from deepreason.intake_form import IntakeFormV1

    fields = IntakeFormV1.model_fields
    declaration_order = {name: index for index, name in enumerate(fields)}
    ordered = sorted(
        names,
        key=lambda n: _sort_key(n, fields[n].description or "", declaration_order[n]),
    )
    return "\n".join(f"- {fields[n].description}" for n in ordered)


def _render_generated_sections() -> dict[str, str]:
    from deepreason.intake_form import HOST_OWNED_FIELDS

    part_a_fields = sorted(HOST_OWNED_FIELDS)  # order fixed by _bullets' label sort
    part_b1_fields = ["seats"]
    part_d_fields = [
        "question",
        "cycles",
        "token_budget",
        "shallow",
        "dossier",
        "attach",
        "allow_partial",
    ]
    return {
        "PART A": _bullets(part_a_fields),
        "PART B1": _bullets(part_b1_fields),
        "PART D": _bullets(part_d_fields),
    }


def render() -> str:
    generated = _render_generated_sections()
    return f"""# FORM DR-1 — APPLICATION TO REASON ON A QUESTION

*Department of Popperian Inquiry. Complete Parts A–D for every
application. Parts E–H apply only where indicated. Incomplete
applications are refused with a typed reason — never lost, never
silently amended. Parts A, B1, and D below are GENERATED from
`src/deepreason/intake_form.py`'s `IntakeFormV1` schema
(`python tools/render_form_dr1.py`) — edit the schema, not this file,
to change them. Parts B2–H remain hand-maintained prose (they document
surfaces the schema does not yet model — see
`experiments/2026-08-11-change-qualification-messages-s4b/SPEC.md`
Addendum 2); fields marked † are pending the adjudication
opt-in tranche's delivery.*

## PART A — THE APPLICANT'S PROVIDER
(files once per home via `deepreason setup`; changes here alter your
qualification subject — see Part C notice)

{generated["PART A"]}

## PART B — SEAT ASSIGNMENTS
(all optional; B blank = one model fills every role, the protected
solo configuration)

{generated["PART B1"]}
- B2 † School seats, conjecture side: `--school-seat school-N=PROFILE`,
  repeatable — each school's conjecturer gets its own profile.
- B3 † School seats, criticism side: `--criticism-seat
  school-N=PROFILE`, repeatable — fully independent of B2.
- B4 NOTICE: every DISTINCT profile or combination bound creates its
  own qualification subject (Part C).

## PART C — QUALIFICATION (mandatory)

- C1 Battery: `deepreason qualify` — ~1,160 calls, ~14 min per new
  subject; cached by subject digest; cache invalidates when Part A
  answers or Part B bindings change.
- C2 Tier: FULL → all parts available. SHALLOW → Part D requires
  `--shallow`; full V6 reasoning refused (typed).
- C3 Zero-tolerance clause: one repair-scope violation in any
  role-pair fails that pair regardless of eventual-valid count.
  Appeal: re-sample via a fresh subject only.

## PART D — THE QUESTION (`deepreason reason "QUESTION"`)

{generated["PART D"]}
- D1a CONDITION: same question + same config = same run id; a
  leftover root refuses relaunch (RUN_ALREADY_STARTED) — retire it
  (H3) or vary the question. Seat bindings are NOT currently in
  identity (parked defect P2) — mind re-runs of identical text under
  different seats. (Not schema-checkable offline — see SPEC.md
  Addendum 2.)
- D6 Stops: budget exhaustion is a TYPED, RESUMABLE stop (Part H);
  unmet criticism coverage at stop is flagged, not corrupted — one
  continuation customarily clears it.

## PART E — CRITICISM & ADJUDICATION (defaults preserve review-only)

- E1 Argued-criticism authority: default `observe_only` — critics file
  scrutiny; prose changes no status. The record self-reports this
  posture (adjudication-blindness finding); readers of
  positions.accepted must consult it.
- E2 † Legacy (school-free) criticism circuit:
  `LEGACY_CRITICISM_ENABLED` — default ON as of the pending delivery.
- E3 † Schools: opt-in (`SCHOOL_SEATS_ENABLED` + B2/B3); schools are a
  conjecture-diversity tool — criticism is separate by doctrine.
- E4 Trial-based status-changing prose adjudication: requires judges ->
  Part F. CONDITION E4a: without Part F, prose cannot flip status —
  by design.

## PART F — JUDGES (opt-in only; suspect-by-default per standing law)

- F1 † `--judge-seats` — setup displays the judge-audit evidence
  before accepting this box.
- F2 Family-diversity route: two judge routes of DIFFERENT declared
  families (A5), e.g. `--judge-family` at compile.
- F3 † Solo route: `--blind-same-model-judges` — same-model ensemble
  with content-blindness structurally enforced; substitutes for F2.
  CONDITION F3a: F2 or F3 required for any trial to convene; neither
  → E4a applies.
- F4 Throttle: no adaptive judge-starving machinery exists (see
  ERRATA_EXECUTOR 2026-08-09-adjacent findings); static caps only.

## PART G — OPTIONAL INSTRUMENTS (each opt-in, mint-time frozen)

- G1 Dual-mode formal channel: contract `conjecturer.turn.v7`
  (opt-in; v6 default) — conjectures may attach runnable
  candidate-checker commitments; live-wired (CP1-M tranche).
- G2 Config referee: `DEEPREASON_CONFIG_REFEREE=<cycles>` — periodic
  content-blind review of run configuration, typed recommendations.
- G3 Research backend: `RESEARCH_BACKEND` = `agent` / `static:<file>`
  / `ask-user` / `web:<config>` / unset (off) — where a run may look
  is part of what it is; allowlist frozen into identity.
- G4 Capability channels: simulation/research proposals per policy;
  use is stochastic across identical runs (one miss inconclusive).

## PART H — AFTER THE VERDICT (append-only; nothing edits history)

- H1 Continue: `deepreason continue --budget cycles=N` — resumes a
  typed resumable stop under mint-time bindings; re-stamps seat
  provenance (two identical stamps = correct).
- H2 Amend: `deepreason amend` — appends an amendment epoch (reshape
  question / admit evidence) without minting a new identity; then H1.
- H3 Retirement: `git mv run-<id> failed-epochN-run-<id>`, commit the
  rename FIRST; never edit a committed root.
- H4 Verification: `verify_root` re-derives all state from the log;
  `replay_valid` + typed findings are the only admissible summary.

*Standing statutes binding every application: formalism is an option,
never an obligation; a solo run with everything on is always
available; seats and wrappers change how content is generated, never
what counts as evidence.*
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    rendered = render()
    if args.check:
        current = FORM_PATH.read_text() if FORM_PATH.exists() else ""
        if current != rendered:
            print(f"{FORM_PATH} is stale relative to its generator.", file=sys.stderr)
            return 1
        print(f"{FORM_PATH} is fresh.")
        return 0
    FORM_PATH.write_text(rendered)
    print(f"wrote {FORM_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
