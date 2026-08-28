# GOAL — a configuration may never silently become a different configuration

Tranche: `experiments/2026-08-28-defect-manifest-config-disclosure/`
Route: `deepreason-orchestrator` (DEFECT).
Opened: 2026-08-28. Branch: `claude/seat-config-gates-audit-1o0mu8`.
Base: `2a5e984c8` (main).

## The one goal

A run whose `Config` set a behavioural switch that the manifest's engine-config
echo cannot carry must, at compile time, emit a TYPED DISCLOSURE naming that
switch, the value the builder set, and the value the run will actually take —
so that the revert is never silent.

Success criterion (falsifiable, offline):

> Compiling a manifest from a `Config` with `JUDGE_SEATS_ENABLED=True`,
> `ADJUDICATION_STATUS_AUTHORITY_ENABLED=True`,
> `ENGAGED_CRITICISM_AUTHORITY="defended_trial"`,
> `LEGACY_CRITICISM_ENABLED=False` and `SCHOOL_SEATS_ENABLED=True` — the
> P-T1 `run-config.yaml` shape — produces `compile_notices` containing one
> typed notice per switch that the run-time `Config` will not carry, each
> naming the configured value and the effective value; and compiling from a
> `Config()` whose dropped fields are all at their defaults produces a
> manifest BYTE-IDENTICAL to the one today, with an unchanged qualification
> subject digest.

Failure criterion: any committed manifest's canonical bytes, `sha256`, or
qualification subject digest moves; or a default-valued config gains a notice.

## Authority

Operator, 2026-08-28, verbatim: *"My intention was that configuration of seats
need to be able to turn gates on and off at will. Meaning no limits to what
model you place where. It also means that when and if I decide to replace
schools with something different, those flags don't gate seat configuration
paths. Gates are always optional: with warnings."*

Ledgered in CLAUDE.md as the seat-config-ungated/modes law. Companions:
the all-configurations law (2026-08-12 — what used to be a refusal becomes
"a typed disclosure recorded alongside the compiled result … never a stop")
and the operations-parity law (2026-08-13 — one run path, same lifecycle).

## Brief (not re-derived here)

- `experiments/2026-08-28-audit-run-problems/PARKED.md` §P10
- `experiments/2026-08-28-audit-run-problems/AUDIT_REPORT.md` §F-A and
  residue item 4
- `experiments/2026-08-28-audit-run-problems/probes/q2_judge_reachability.json`

## Map ids resolved (map preflight, per dr-drive-harness §4)

| id | why it is in scope |
|---|---|
| `DR-INV-frozen-surfaces` | surface 4 (`run_manifest.py` schemas + validators) — FORECAST contact, granted conditionally by the monitor |
| `DR-SUB-manifest` | owns `run_manifest.py`: the echo, `compile_run_manifest`, `config_from_run_manifest`, `CompileNoticeV1` |
| `DR-CON-authority` | owns the two authority vocabularies; `JUDGE_SEATS_ENABLED` and `ADJUDICATION_STATUS_AUTHORITY_ENABLED` are its master gates |
| `DR-SUB-scheduler` | run-time consumer of `JUDGE_SEATS_ENABLED`, `JUDGE_SUMMONS_*` |
| `DR-CON-seats` | the operator law is about seat configuration |
| `DR-SEAM-llm-x-manifest` | the only written seam touching `run_manifest.py`; holds `route_fingerprint` frozen-adjacent |

**Map gap, recorded as a finding rather than a blocker.** There is no
`SEAM-manifest-x-scheduler.md` and no `manifest × application` row in
`INDEX.md`'s matrix at all — yet the whole defect lives on exactly that
agreement: `run_scheduler` is handed `config_from_run_manifest(manifest)`, so
the manifest is the ONLY carrier of run-time `Config`. The pair is absent from
the matrix, which `INDEX.md` says means "no measured import traffic" — the
traffic is real but flows through `application/text_runs.py`, whose
`SUB-application.md` is not in the routing table either. Named here; closing it
is not this tranche's goal.

## Scope contract

IN: `run_manifest.py` compile-time disclosure; regression tests; map documents.

OUT (PARKED, not fixed here):
- Adding any dropped field to `engine_config_json` (prices every
  qualification subject digest — the brief forbids it without pricing).
- Making `compile_run_manifest` synthesise a `criticism_policy` from `Config`
  when a builder omits one (a behaviour change to compiled manifests, not a
  disclosure).
- P11, P12, P13 and every other finding of the audit.
- The render-layout and criticism tranches' cones (`llm/layout.py`,
  `llm/packs.py`, `llm/roles.py`, `informal/trial.py`, `premises.py`,
  `rules/crit.py`) — mutual stop lines, untouched.

## Stop conditions

Stop and report if the design moves any qualification subject digest or any
committed digest pin; if contact is required with a frozen surface other than
4; or if the diff exceeds ~150 changed lines of production code.
