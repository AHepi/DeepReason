# Spec for: four evidence states over the record, and a per-cycle declaration
# that criticism ran in full

Traces: every item cites R/C numbers from REQUEST.md. Untraceable items are bugs.

Read first: REQUEST.md in full, including its Map ids section.

---

## 0. The declaration, designed FIRST (R5 orders this before anything else)

R5: *"Design the declaration FIRST in SPEC.md: prefer the existing
notice/measure channel (`record_measure`, the road the dead-seat tranche took
to avoid a new record kind); a NEW record object kind is a surface-2 contact
(harness.py) and a STOP for a grant."*

**Result: the measure channel carries it. NO new record object kind. NO
harness.py contact. NO grant needed, so no STOP.**

### What the record already offers

`Harness.record_measure(inputs=[...])` (`src/deepreason/harness.py:556`) appends
a `Rule.MEASURE` event carrying an arbitrary list of strings. Its docstring
states the constraint that makes it the right channel here: *"estimates steer
attention, never status"*. The declaration is exactly that — a fact about how
the run behaved, never a fact about any artifact's standing.

Three existing readers already treat measure inputs as a typed signal channel
with a positional grammar, so this is a road with three precedents rather than
a new idea:

| precedent | signal | read by |
|---|---|---|
| dead-seat tranche | `seat.retired.v1` | `application/results.py:432` `seat_retirement_summary` |
| defended trials | `trial-observation`, `trial-declined`, `trial-blocked:*` | `application/results.py:290` `_adjudication` |
| cycle heartbeat | `["cycle", <n>, <problem_id>]` | `scheduler/scheduler.py:2203` |

### The declaration

Signal name and writer live in a NEW module `src/deepreason/runtime/criticism_dispatch.py`,
beside `runtime/seat_retirement.py` and shaped like it: the constant and the
one writer in one place, so the scheduler emits it and the reader reads it
without either importing the other.

    CRITICISM_DISPATCH_SIGNAL = "criticism.dispatch.v1"

    inputs = [
        CRITICISM_DISPATCH_SIGNAL,
        str(cycle),          # the scheduler's own cycle index (self._cycles)
        outcome,             # see the vocabulary below
        str(planned),        # targets the pass intended to criticise
        str(dispatched),     # targets a criticism call was actually made for
        *dispatched_target_ids,
    ]

Outcome vocabulary — a CLOSED set, one member per way the pass can end, each
tied to a branch that exists in `Scheduler._arg_crit` today
(`src/deepreason/scheduler/scheduler.py:1514-1586`):

| outcome | the branch it reports | counts as full? |
|---|---|---|
| `complete` | every eligible target was dispatched and no batch call was dropped | YES |
| `cut:budget` | `config.ARG_CRIT_PER_CYCLE` truncated the eligible loop (`break` at :1552) | no |
| `cut:seat` | `self._role_available("argumentative_critic")` was false (:1530) | no |
| `cut:call` | a batch raised `SchemaRepairError`/`EndpointError` and was dropped (:1584) | no |
| `cut:foreign` | the manifest criticism policy took the `_foreign_arg_crit` road (:1542), which this declaration does not measure | no |

Only `complete` licenses the absence road of R4. Every other outcome, and the
absence of any declaration at all, leaves an un-attacked artifact OPEN. The
vocabulary is closed so that a future road that ends the pass some other way
must add a member rather than silently inherit `complete`.

**Why the dispatched target ids ride the declaration.** R4 binds the licence to
"the cycle", but a reader that only knew a cycle number would have to guess
which artifacts that cycle's criticism actually looked at. Naming the
dispatched targets makes the licence exact and conservative: an artifact is
licensed only if a `complete` pass names it.

**Why this is not a frozen-surface contact.** Surface 2 is `harness.py` event
application and well-formedness. This change calls `record_measure`; it does
not change it, does not add an event Rule, does not add an object kind, and
does not touch `_validate_warrant`, `register_batch` or any digest. The gate
agrees — see the forecast below, `frozen_surface_verdict: CLEAR`.

**What it costs an existing root.** Nothing. No committed root is edited (R10).
A root written before this tranche carries no declaration and the reader says
so as a typed absence.

---

## Items

### S1 (R1, R2, C2) — the reader and the four states

Files: `src/deepreason/views/evidence_states.py` (NEW).

`views/` is the read-only view layer; nothing in `scheduler/`, `adjudication/`
or `rules/` imports it today (measured: `grep -rn "from deepreason.views"
src/deepreason/{scheduler,adjudication,rules}/` -> 0 hits), which is what makes
R3's architecture test expressible.

Before: an admitted artifact reads as `Status.ACCEPTED` whether nobody ever
attacked it or it beat off a warranted attack.
After: `evidence_states(harness) -> dict[str, EvidenceState]` gives every
non-import admitted artifact exactly one of `OPEN`, `SUPPORTED`, `REFUTED`,
`CONTESTED`.

The inputs, all of them already on the record (R2):

| input | where it comes from | authority |
|---|---|---|
| warranted attacks | `state.att` — an edge exists only when a REGISTERED warrant naming the target is CARRIED | `DR-CON-warrants-and-attacks`, "No registered warrant, no edge" |
| whether an attack landed | `state.status[attacker]` | `adjudication/grounded.py`, `adjudication/support.py` |
| status labels | `state.status[target]` | same |
| trial outcomes | measure signals `trial-declined` / `trial-observation` / `trial-blocked:ensemble-split`, each carrying its target id at `inputs[1]` | `informal/trial.py:324,333,384` |
| completeness licence | `criticism.dispatch.v1` declarations with outcome `complete` | S2 |

Definitions, in evaluation order (first match wins):

    attackers(T)        = {C : (C,T) in state.att}
    failed(T)           = {C in attackers(T) : status[C] is REFUTED}
    standing(T)         = attackers(T) - failed(T)
    completed_trial(T)  = a trial-declined or trial-observation naming T
    split_trial(T)      = a trial-blocked:ensemble-split naming T
    licensed(T)         = T is named by a `complete` criticism.dispatch.v1

    REFUTED    <= status[T] is REFUTED
    CONTESTED  <= split_trial(T)
                  or (failed(T) and standing(T))
                  or (status[T] is SUSPENDED and attackers(T))
    SUPPORTED  <= failed(T) or completed_trial(T)
                  or (not attackers(T) and licensed(T))
    OPEN       <= otherwise

C2 is satisfied by construction: nothing here counts a critic CALL. Only a
registered warrant that became an attack edge, or a trial that reached a
ruling, moves an artifact off OPEN. The blind-critic finding — the critic
attacks everything it is shown — therefore cannot inflate SUPPORTED.

Import-role admission records are EXCLUDED from the population, not given a
state, per CLAUDE.md's standing invariant ("import-role admission records never
count as survivors") and `ontology/state.py:is_import_admission`. They are
reported as a separate `excluded_import_admissions` count so the exclusion is
visible rather than silent.

    accept: python -m pytest tests/test_evidence_states.py -q -> 0 failed
    accept: python -c "from deepreason.views.evidence_states import EvidenceState; \
      assert [s.value for s in EvidenceState] == ['open','supported','refuted','contested']"

### S2 (R4, R5) — the per-cycle completeness declaration

Files: `src/deepreason/runtime/criticism_dispatch.py` (NEW),
`src/deepreason/scheduler/scheduler.py` (emit at every exit of `_arg_crit`).

Before: nothing on the record says whether a cycle's criticism dispatch ran in
full, so an un-attacked artifact is indistinguishable from an un-visited one.
After: every criticism pass files exactly one `criticism.dispatch.v1` measure
naming its cycle, its outcome, its planned and dispatched counts, and the
targets it dispatched.

Emission points in `Scheduler._arg_crit`, one per exit:

1. role unavailable, no manifest policy (`return` at :1535) -> `cut:seat`,
   planned = len(admitted_ids), dispatched = 0.
2. manifest criticism policy road (`return` at :1544) -> `cut:foreign`.
3. after the batch loop -> `complete` if the eligible loop was not truncated by
   `ARG_CRIT_PER_CYCLE` and no batch was dropped; otherwise `cut:budget` or
   `cut:call`. `cut:call` wins when both happened, because a dropped call is
   the stronger statement that a planned call was not made.

Targets skipped because `status[aid] != Status.ACCEPTED` (already felled by
cheaper criticism, :1547) are NOT a cut: the pass did everything it planned.
They are excluded from `planned` for the same reason.

The `SchoolRouteResolutionError` raise at :1537 is left alone — it is a typed
stop, not a completed pass, and this tranche adds no declaration on a path that
raises.

    accept: python -m pytest tests/test_criticism_dispatch_declaration.py -q -> 0 failed
    accept: a stub-driven run's log contains exactly one criticism.dispatch.v1
            event per criticism pass (asserted in that test)

### S3 (R3) — the law line: the reading decides nothing

Files: `tests/test_evidence_states_law_line.py` (NEW).

Built on the shape of `tests/test_successor_law_line.py`, which is the repo's
established form for this exact obligation, with both halves it insists on:

- SPELLING half: no file under `src/deepreason/scheduler/`,
  `src/deepreason/adjudication/` or `src/deepreason/rules/` contains any of
  `deepreason.views.evidence_states`, `evidence_states`,
  `evidence_state_summary`, `EvidenceState`, `EVIDENCE_STATE`. Permitted
  exceptions: EMPTY.
- BEHAVIOURAL half: computing the reading over a root APPENDS NOTHING — the
  log's event count and the root's file mtimes are unchanged across the call,
  and `state.status` is identical before and after. A reader that wrote, or
  that re-adjudicated, turns this red.

The three packages are the operator's own list (R3). `informal/` and
`workflow/` are NOT in it and are not added: this spec does not widen the
operator's words.

    accept: python -m pytest tests/test_evidence_states_law_line.py -q -> 0 failed
    accept: the mutation record in proof/ shows each half RED under its own
            planted violation and green on revert (S8)

### S4 (R6) — `deepreason results`

Files: `src/deepreason/application/results.py`.

Before: `results_summary` has `artifacts` (accepted/refuted/suspended counts, a
frontier id list) and `adjudication`. Nothing distinguishes a survivor from an
untested conjecture.
After: a new top-level `evidence_states` section, built the way every other
section in that file is built, carrying:

    {"schema": "deepreason-evidence-states.v1",
     "counts": {"open": n, "supported": n, "refuted": n, "contested": n},
     "per_cycle": {"<cycle>": {"open": n, ...}, ...},
     "excluded_import_admissions": n,
     "completeness": {...} | {"absent": True, "reason": "NO_CRITICISM_DISPATCH_DECLARATION"}}

and a per-artifact column on the frontier listing: each previewed frontier id
gains its state. `render_results` gains an `## Evidence states` block and the
per-artifact column, in the operator's vocabulary — "nothing has attacked it
yet" for OPEN, "it beat off an attack" for SUPPORTED — never the bare label
alone.

Per-cycle attribution uses the cycle heartbeat that already segments the log
(`["cycle", <n>, <problem_id>]`, `scheduler.py:2203`, whose comment states the
rule: "every event that follows (by seq) until the next heartbeat belongs to
this cycle"). An artifact is attributed to the cycle in which it was first
registered. Artifacts registered before the first heartbeat are attributed to a
typed `"pre-cycle"` bucket rather than silently to cycle 0.

    accept: python -m pytest tests/test_results_command.py -q -> 0 failed
    accept: deepreason results <p-a2 root> --json | jq .evidence_states.counts
            -> the four keys, summing to the non-import artifact count

### S5 (R6) — `deepreason stop-report`

Files: `src/deepreason/application/stop_report.py`.

Before: five sections, none of them about what survived.
After: a sixth section `evidence_states` carrying the same payload as S4,
built from the report's own `root` (it already resolves one) via a read-only
`Harness`. For `kind == "home-no-root"` and `"root-no-log"` the section is a
typed absence with the reason those kinds already use, matching how
`provider_health` and `continuability` behave on the same kinds.

    accept: python -m pytest tests/test_stop_report.py -q -> 0 failed
    accept: deepreason stop-report <p-a2 root> | grep -q "Evidence states"

### S6 (R10) — typed absence over a record that predates the declaration

Files: covered by S1/S4/S5; asserted separately because it is its own claim.

Every committed root predates this tranche, so none carries a declaration. On
such a root the `completeness` block is
`{"absent": true, "reason": "NO_CRITICISM_DISPATCH_DECLARATION"}` and the
rendered line SAYS WHY in plain words: nothing on this record says whether the
criticism pass ran in full, so nothing is read as having survived merely
because nothing attacked it.

No committed root is read/written by anything but a read-only `Harness`.

    accept: python -m pytest tests/test_evidence_states.py -k predates -q -> 0 failed
    accept: git status --porcelain over every committed root touched by the
            test run is EMPTY

### S7 (R7, R8) — the `--survivors-only` switch on both instruments

Files:
`experiments/2026-09-03-change-conjecturer-pluggable-interface/analyse_form_arms.py`,
`experiments/2026-09-03-change-provenance-history-channel/measure_diversity_per_problem.py`.

Both gain `--survivors-only`, which restricts the artifacts considered to those
the reader calls SUPPORTED. Default OFF; with the flag absent, both scripts run
byte-identically to today (R8), pinned by a test that captures each script's
default output before and after this tranche and compares.

    accept: python experiments/.../analyse_form_arms.py --self-test -> ok
    accept: python -m pytest tests/test_survivors_only_switch.py -q -> 0 failed
    accept: default-path output is byte-identical to the pre-change capture

### S8 (R11) — the proof

Files: `tests/test_evidence_states.py`,
`tests/test_criticism_dispatch_declaration.py`,
`tests/test_evidence_states_law_line.py`,
`tests/test_survivors_only_switch.py`,
`experiments/2026-09-04-change-evidence-states/proof/` (mutation transcripts).

Mutation proof, one planted mutant per claim, each watched RED and then green
on revert, transcript committed under `proof/`:

| M | mutant | test that must go red |
|---|---|---|
| M1 | REFUTED branch removed | the REFUTED case |
| M2 | `failed(T)` treated as SUPPORTED-irrelevant | the SUPPORTED case |
| M3 | `split_trial` ignored | the CONTESTED case |
| M4 | OPEN default replaced by SUPPORTED | the OPEN case |
| M5 | **the completeness rule dropped** — absence of attack counts as SUPPORTED with NO declaration | `test_absence_needs_the_declaration` (R11's named obligation) |
| M6 | the reader named inside `scheduler/` | law line, spelling half |
| M7 | the reader appends a measure | law line, behavioural half |

Fixtures are built from committed roots by a helper that COPIES a root into
`tmp_path` and never opens the original writable.

**One named fixture does not exist, and this spec says so rather than
pretending** (dr-spec-change step 2, the named-mechanism rule). R11 names "the
blind-critic roots" as the canonical OPEN case. `experiments/2026-09-04-experiment-blind-critic/`
contains NO run root — measured: `find experiments/2026-09-04-experiment-blind-critic
-name log.jsonl` returns nothing. That tranche is a bench over direct provider
calls (`raw/`, `blind/`, `bench.py`), not a harness run, which is exactly WHY
its 480 attacks carry zero warrants: no harness was there to register one. The
PROPERTY R11 wants — a canonical OPEN case drawn from the committed record —
is delivered from a root that actually exists, chosen by census (S9) and named
in CHECKLIST.md. The blind-critic finding still binds the DESIGN through C2,
which S1 satisfies.

`experiments/2026-09-02-live-p-a2-corrected/run` IS "P-A2 epoch 4" (its
`run-status.json` reads `cycle: 4`, 75 accepted, 11 refuted) and does carry
sustained attacks, so that half of R11's fixture claim holds.

### S9 (R13) — the census the final message reports

Files: `experiments/2026-09-04-change-evidence-states/CENSUS.md`,
`experiments/2026-09-04-change-evidence-states/census.py`.

A committed script that runs the SHIPPED reader over every committed root and
tables OPEN vs SUPPORTED for the frontier artifacts. R13 says that number is
the point, so it is re-derivable by anyone holding the commit rather than
quoted from a session.

    accept: python experiments/2026-09-04-change-evidence-states/census.py
            -> a table, and CENSUS.md carries its pasted output

### S10 (R12) — the map moves in the same commit

Files: `docs/map/CON-evidence-states.md` (NEW), `docs/map/INDEX.md` (routing
row), `docs/map/SUB-application.md` and `docs/map/SUB-scheduler.md` (the two
documents whose `Owns:` files this change edits).

`CON-evidence-states.md` follows `SCHEMA.md`: `Verified-at:`, `Owns:`, `Seams:`,
and `check:` commands that CAN FAIL. At minimum:

- a check that the four states are exactly those four, in that order;
- a check that an artifact with no attack and no declaration reads OPEN;
- a check that the same artifact reads SUPPORTED once a `complete` declaration
  names it (this is the completeness rule, executable);
- a check that no deciding package names the reader (the law line, as a
  one-liner).

Each is written by first running it against the CURRENT tree and confirming it
FAILS, then implementing, then confirming it passes — the SCHEMA rule that a
new check must be one that would have caught the regression.

    accept: python tools/docs_verify.py -> 0 failed beyond the C4 known rows
    accept: python tools/docs_verify.py --audit -> CON-evidence-states.md has
            no check that cannot fail
    accept: python tools/docs_verify.py --links -> every DR- reference resolves

---

## Assumptions (operator may override)

A1 (Q1, R10). **R10's "OPEN/REFUTED only" is read as the ABSENCE road, not as a
ceiling on the whole reading.** R1 defines SUPPORTED as "survived at least one
warranted attack or defended trial" with no declaration precondition, and R4
attaches the declaration precondition specifically to "the absence of any
warranted attack". A root with no declarations can therefore still show
SUPPORTED (an attacker that was itself refuted — a real, positive survival on
the record) and CONTESTED (an ensemble-split trial that really happened).
Implementing the literal "OPEN/REFUTED only" would throw away the very evidence
the progress law asks for. The binding property, which IS implemented: **no
artifact is ever read as SUPPORTED on the strength of an absence unless a
`complete` declaration licenses it.** Assumed; operator may override.

A2 (Q2). **"Every planned criticism call was made" is measured at the
argumentative pass**, `Scheduler._arg_crit` — the pass that dispatches critic
calls at targets. Cheaper deterministic criticism upstream (`crit_program`,
`crit_fuzz` in `_criticize`) is not a "criticism call" in the sense R4 is
guarding, because it cannot be cut by budget or a retired seat: it is
deterministic and local. Assumed; operator may override.

A3 (Q3). **"The diversity instrument" is
`experiments/2026-09-03-change-provenance-history-channel/measure_diversity_per_problem.py`.**
Traced, not guessed. `analyse_form_arms.py` delegates its M1/M2/M3 to
`experiments/2026-08-28-diversity-generation/analyse.py`, which is the other
candidate — but that script reads `raw/<arm>/<question>/r<rep>/*.json`
directories of direct provider calls and never opens a run root, so it holds no
artifact that could HAVE an evidence state and `--survivors-only` would be
inert in it. `measure_diversity_per_problem.py` takes run roots positionally
and reads `objects/artifact/**` — it is the diversity instrument the switch can
actually reach. Recorded rather than silently substituted, per the
named-mechanism rule.

A4 (Q4). **"Typed absence" follows the file's own existing convention**:
`{"absent": True, "reason": "<CODE>"}` via `results.py:_absent`, rendered
through `_show`. No new absence vocabulary is invented.

A5 (Q5). **The reader lives in `src/deepreason/views/`** — the read-only view
layer, which no deciding package imports today (measured, 0 hits). The
declaration's signal constant and writer live in
`src/deepreason/runtime/criticism_dispatch.py` so that the scheduler can emit
without importing the reader; this is the same separation
`runtime/seat_retirement.py` already uses.

A6. **Per-cycle counts attribute an artifact to the cycle in which it was first
registered**, and artifacts registered before the first cycle heartbeat go to a
typed `"pre-cycle"` bucket. R6 asks for "counts per state per cycle" without
saying which cycle owns an artifact; first-registration is the only attribution
the record supports without inventing one.

## Questions for operator (STOP if non-empty)

None. Every fork above was decided from the record or from the operator's own
standing laws, and each decision is recorded as an assumption the operator can
overturn in one word. Nothing here needs operator attention before
`dr-plan-steps` — no frozen surface is contacted (gate verdict CLEAR, pasted
below) and no design law is in tension.

## Out of scope (explicit)

- Making any of the four states a real `Status`. R1 says "a DERIVED READING,
  not a new status". Not requested.
- Letting the reading feed admission, rank, immunity or refutation. R3 forbids
  it; the law line makes the prohibition falsifiable.
- Widening the declaration to the foreign-criticism road (`_foreign_arg_crit`).
  It gets a `cut:foreign` declaration, which is honest; measuring it properly is
  a separate tranche. PARKED.
- The two other queued CR-2.0 items (reason-use test on the response side;
  disclosed loss on revision). One tranche, one goal (C5).
- Fixing anything the census turns up about the committed roots. Read-only.

## Frozen-surface contact forecast

Forecast BEFORE code, as R9 requires. `tools/blast_radius.py` run over every
planned target file that exists today plus every planned symbol. The tool
refuses a declared file that does not exist yet (exit class 3, "evidence
unavailable"), so the two NEW modules are covered by the symbol declarations
and by the manual grep below, and the gate is RE-RUN over the real files as a
checklist step once they exist.

Command:

    python tools/blast_radius.py \
      --files src/deepreason/scheduler/scheduler.py \
              src/deepreason/application/results.py \
              src/deepreason/application/stop_report.py \
              experiments/2026-09-03-change-conjecturer-pluggable-interface/analyse_form_arms.py \
              experiments/2026-09-03-change-provenance-history-channel/measure_diversity_per_problem.py \
      --symbols evidence_states evidence_state_summary EvidenceState \
                CRITICISM_DISPATCH_SIGNAL declare_criticism_dispatch _arg_crit \
                results_summary render_results stop_report render_stop_report

Verbatim result fields:

    "frozen_surface_contacts": [],
    "frozen_adjacent_contacts": [],
    "frozen_surface_verdict": "CLEAR",
    "disclosure_summary": "This change touches none of the five frozen
      surfaces. 7 test file(s) and 8 map document(s) assert on the touched
      targets today. Reachability here means a syntactic call path exists from
      a known entry point; it does not prove the path is ever actually
      exercised at runtime -- a symbol can be syntactically reachable and still
      never fire because of a runtime precondition this gate does not
      evaluate."

**NO CONTACT, as R9 forecast.** The frozen-adjacent list is empty too, so
`route_fingerprint` is not in play.

Five `reachability` entries came back `UNKNOWN`: `evidence_states`,
`evidence_state_summary`, `EvidenceState`, `CRITICISM_DISPATCH_SIGNAL`,
`declare_criticism_dispatch`. All five are names this tranche INTRODUCES; the
gate cannot resolve a symbol that does not exist. dr-spec-change step 5 names
the required cross-check for exactly this case, and it was run:

    for s in evidence_states evidence_state_summary EvidenceState \
             CRITICISM_DISPATCH_SIGNAL declare_criticism_dispatch \
             survivors-only survivors_only; do
      echo "$s: $(grep -rn "$s" tests/ docs/map/ src/ | wc -l) hits"; done
    ->
    evidence_states: 0 hits
    evidence_state_summary: 0 hits
    EvidenceState: 0 hits
    CRITICISM_DISPATCH_SIGNAL: 0 hits
    declare_criticism_dispatch: 0 hits
    survivors-only: 0 hits
    survivors_only: 0 hits

Zero existing consumers and zero existing call paths, so no route from any of
them into a frozen surface can exist today. This is not a resolved UNKNOWN
being waved past; it is an UNKNOWN whose whole content is "this name is new",
cross-checked by the grep the skill names for it. The gate is re-run over the
real files at step [C4] of CHECKLIST.md, and a CONTACT there stops the tranche.

## Blast-radius census

From the same gate run. `consumers.tests` and `consumers.map_checks`, every hit
classified.

### consumers.tests

| target | hits | classification |
|---|---|---|
| `src/deepreason/scheduler/scheduler.py` | `tests/test_hv_v6_reachability.py:45`, `tests/test_successor_rank_tie.py:169`, `tests/test_wander_cap.py:530` | MUST NOT MOVE — none reads the criticism pass's measure stream |
| `src/deepreason/application/results.py` | `tests/test_error_catalog.py:66` | MUST NOT MOVE — an error-code census, no new code added |
| `_arg_crit` | `tests/test_all_configs_allowed_remainder.py:313`, `tests/test_successor_dispatch.py:475`, `tests/test_v6_engaged_public_defaults.py:795`, `:840`, `tests/test_v6_scheduler_model_phase_deferral.py:124`, `:393` | MUST NOT MOVE — all six assert on criticism BEHAVIOUR (what was dispatched, what was deferred), and the declaration adds a measure without changing any dispatch decision. If one moves, the emission changed behaviour and that is a defect, not a fixture update |
| `results_summary` | 60 hits, `tests/test_results_command.py` (42), `tests/test_jailbreak_gate.py` (5), `tests/test_provider_transport_faults.py` (4), `tests/test_failure_terminal_reports_real_token_spend.py` (4), `tests/test_terminal_lifecycle_refusal_is_recorded.py` (4), `tests/test_import_role_survivors.py` (2), `tests/test_stopped_run_resumption.py` (2) | EXPECTED TO MOVE, narrowly: any test asserting the EXACT key set of the summary dict, or an exact rendered-text match, gains the new section. Every test asserting a specific existing key MUST NOT MOVE |
| `render_results` | 10 hits, `tests/test_results_command.py` (8), `tests/test_provider_transport_faults.py` (2) | EXPECTED TO MOVE where a full-text match is asserted; MUST NOT MOVE where a single line is matched |
| `stop_report` | 24 hits, all `tests/test_stop_report.py` | EXPECTED TO MOVE where the `sections` key set is asserted exactly; MUST NOT MOVE otherwise |
| `render_stop_report` | 9 hits, all `tests/test_stop_report.py` | EXPECTED TO MOVE where a full-text match is asserted |

No hits at all for `experiments/.../analyse_form_arms.py` or
`experiments/.../measure_diversity_per_problem.py`: neither instrument has a
test today. S7 adds the first one, which is why R8's "no default behaviour
changes" needs a before-capture rather than an existing pin.

### consumers.map_checks

| target | hits | classification |
|---|---|---|
| `src/deepreason/scheduler/scheduler.py` | 71 rows across 24 map documents (`SUB-scheduler.md` 16, `SEAM-scheduler-x-rules.md` 8, `SEAM-scheduler-x-workflow.md` 8, `CON-scheduler-ranking.md` 4, plus 20 more documents) | MUST NOT MOVE — every one of them checks a scheduler behaviour this change does not alter. `INV-frozen-surfaces.md:384` is in this list and is the row to watch: it MUST stay green |
| `_arg_crit` | 16 rows, `SEAM-scheduler-x-rules.md` (7), `SUB-scheduler.md` (3), `CON-conjecture-kinds.md:203`, `CON-problem-layer-lifecycle.md:333`, `CON-successor-questions.md:37`, `SEAM-scheduler-x-workflow.md:355`, `:367` | MUST NOT MOVE, except `SUB-scheduler.md`'s description of what `_arg_crit` does, which EXPECTED TO MOVE (it gains the declaration) |
| `src/deepreason/application/results.py` | `SUB-application.md:111,276,321,373,410,452` | EXPECTED TO MOVE — `SUB-application.md` owns this file and gains the new section |
| `src/deepreason/application/stop_report.py` | `CON-configuration-stages.md:89,136`, `SUB-application.md:130` | `SUB-application.md` EXPECTED TO MOVE; both `CON-configuration-stages.md` rows MUST NOT MOVE (they are about config stages, not sections) |
| `results_summary` / `render_results` | `SUB-application.md:90,111,237,266` | EXPECTED TO MOVE |
| `stop_report` / `render_stop_report` | `CON-configuration-stages.md:41,89,110,136`, `SUB-application.md:112,130,132` | `SUB-application.md` EXPECTED TO MOVE; `CON-configuration-stages.md` MUST NOT MOVE |

`qualification_digest: []` and `wheel_smoke_pins: []` — no qualification subject
moves and no public-surface pin moves. The wheel smokes therefore need no
re-pin; the CLI gains no new console entry point and no new MCP tool.

### The manual cross-check (required for the UNKNOWN symbols)

Pasted above under the forecast: 0 hits for all five new names and for both
spellings of the new switch. Nothing existing depends on them.

## Record-observable guardrail (dr-spec-change step 4)

This change adds a new typed-record observable — the `criticism.dispatch.v1`
measure. The rule is: **the absence-tolerant READER lands before the writer
emits.** CHECKLIST.md orders it that way (S1 before S2), and S6 pins the
absence case on real committed roots, so every existing root stays valid with
the new data absent.

The sweep-probe half of that rule does NOT apply: `tools/root_sweep.py` is
RETIRED as an instrument by operator ruling of 2026-08-22 ("it just wastes
time"), and CLAUDE.md forbids any tranche from requiring a committed-root
sweep. The equivalent proof this tranche owes instead — and delivers — is S6's
targeted regression on committed roots plus S9's census over all of them.

## Budget

Itemized:

    S1  reader                                          130
    S2  declaration module + scheduler emission          70
    S3  law-line test                                    90
    S4  results section + render + frontier column       60
    S5  stop-report section + render                     35
    S6  absence regression                               40
    S7  two instruments + their pin test                 70
    S8  three state/declaration test files              180
    S9  census script + CENSUS.md                        60
    S10 CON-evidence-states.md + 3 map edits            120

    python3 -c "print(sum([130,70,90,60,35,40,70,180,60,120]))"
    -> 855

**855 lines, over the ~300 guideline, so the split is proposed rather than
ignored.** Three ordered commits inside this one tranche, each independently
green, rather than three separate deliveries — the pieces are not separately
useful (a reader with no surface reports to nobody; a declaration with no
reader is dead data) and splitting the delivery would put a half-wired feature
on main:

    commit 1  S1 + S2 + S3 + S8            the reading, the declaration, the law
    commit 2  S4 + S5 + S6                 the surfaces
    commit 3  S7 + S9 + S10                the baseline hook, the census, the map

The map moves in the SAME commit as the code it describes (R12): commit 3
carries `CON-evidence-states.md`, and the `SUB-application.md` /
`SUB-scheduler.md` edits ride commits 2 and 1 respectively, beside the code
each describes.

**Declared areas for the ceiling.** `tools/diff_budget.py --paths` takes these
and only these:

    src/ tests/ docs/map/ \
    experiments/2026-09-03-change-conjecturer-pluggable-interface/ \
    experiments/2026-09-03-change-provenance-history-channel/

The 855 estimates the CHANGE. This tranche's own ledger —
`experiments/2026-09-04-change-evidence-states/` — is not in it: REQUEST.md,
SPEC.md, CHECKLIST.md, the mutation transcripts and CENSUS.md are the record OF
the work, not the work, and no line of them ships. Stated because the first
[COMMIT] gate ran with the tranche directory included and read EXCEEDED at
1791/855 on 1130 lines of its own prose — a real reading of the wrong question.

Frozen surfaces touched: NONE (gate verdict CLEAR, pasted above).

Rubric: 6/6 yes
  - every R has a spec item with a machine-decidable accept: yes
    (R1,R2->S1; R3->S3; R4,R5->S2 and §0; R6->S4,S5; R7,R8->S7; R9->forecast;
     R10->S6; R11->S8; R12->S10 and the gate steps; R13->S9)
  - blast-radius census pasted and every hit classified: yes
  - frozen-surface contact forecast recorded, tool output verbatim: yes
  - every mechanism the request names traced to code it reaches: yes —
    `record_measure` traced (§0), `analyse_form_arms.py` traced (A3),
    the blind-critic roots traced and found ABSENT (S8), the P-A2 root traced
    and confirmed (S8)
  - DESIGN-AND-STOP sections: n/a, this is not a design-and-stop request
  - nothing untraceable to an R/C number: yes
