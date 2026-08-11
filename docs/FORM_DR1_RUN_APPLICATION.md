# FORM DR-1 — APPLICATION TO REASON ON A QUESTION

*Department of Popperian Inquiry. Complete Parts A–D for every
application. Parts E–H apply only where indicated. Incomplete
applications are refused with a typed reason — never lost, never
silently amended. Rendered 2026-08-10 from the live CLI/config surface
at the opt-in tranche's head; fields marked † are pending that
tranche's delivery. This document is a READER of the tree; the tree is
the authority — regenerate on surface changes.*

## PART A — THE APPLICANT'S PROVIDER
(files once per home via `deepreason setup`; changes here alter your
qualification subject — see Part C notice)

- A1 Provider: `--provider` (e.g. `ollama`)
- A2 Endpoint: `--endpoint` (https)
- A3 Model, exact id: `--model`
- A4 Model revision: `--model-revision`
- A5 Model family: `--family` — NOTICE: family declarations govern
  Part F judge eligibility
- A6 Context window: `--context-window-tokens`
- A7 Completion ceiling: `--maximum-completion-tokens` — ADVISORY:
  reasoning-class models may burn this entirely on hidden thought; a
  typed seat failure is your notice to raise it, not a defect report
- A8 Reasoning mode: `--reasoning`
- A9 Credential: `--credential-env` (env var name; keys never stored)

## PART B — SEAT ASSIGNMENTS
(all optional; B blank = one model fills every role, the protected
solo configuration)

- B1 Role-group seats: `--seat GROUP=PROFILE`, repeatable. GROUPS:
  `conjecture` (conjecturer+variator), `coder` (encoder; requires
  Part G dual-mode opt-in to have any effect), `scratch`,
  `simulation` (alias of conjecture). CONDITION B1a: groups sharing a
  role may not bind conflicting profiles.
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

- D1 Question text: verbatim; part of run identity. CONDITION D1a:
  same question + same config = same run id; a leftover root refuses
  relaunch (RUN_ALREADY_STARTED) — retire it (H3) or vary the
  question. Seat bindings are NOT currently in identity (parked
  defect P2) — mind re-runs of identical text under different seats.
- D2 Cycles: `--cycles` <= 12 (V6 ceiling).
- D3 Token budget: `--token-budget` <= 200000 (V6 ceiling; refused
  typed at intake if exceeded).
- D4 Shallow mode: `--shallow` — mandatory when C2 = SHALLOW.
- D5 Evidence: `--attach FILE-or-DIR` (repeatable; mints dossier
  digest) or `--dossier SHA256` (must match this exact question);
  `--allow-partial` admits bounded prefixes of oversized attachments.
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
- E4 Trial-based status-changing prose adjudication: requires judges →
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
