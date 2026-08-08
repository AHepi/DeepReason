# Request: pipeline census — Rung D1 of the dual-mode conjecture program

Captured: 2026-08-08 from this session's opening task message, plus
its cited source document
`docs/proposals/DUAL_MODE_CONJECTURE_PREPLAN.md` (the whole document,
per the task's own instruction, with the Rung D1 section and
requirements R-a..R-g as binding scope).

## Verbatim

This session's task message, opening instruction (full text):

> Read CLAUDE.md in full first — including the new "Operator design
> laws" section — then .claude/skills/README.md. Load
> dr-explain-to-operator before your first message and follow it for
> every message, intermediary and final. You are the executor for
> Rung D1 of the dual-mode conjecture program: the pipeline census.
> MEASURE ONLY — src/, tests/, tools/ stay byte-untouched; your
> deliverables are the tranche's artifacts plus one new map document.
> Setup: base your working branch on origin/claude/monitor-session-
> handover-63ajqv and verify its head is 371e84d7 — if not, stop and
> say so. Run the session preflight (which deepreason || pip install
> -e . --break-system-packages -q).
> Route through dr-change-orchestrator, starting with
> dr-capture-request. Authority: docs/proposals/
> DUAL_MODE_CONJECTURE_PREPLAN.md — the whole document, its Rung D1
> section verbatim as your scope, and requirements R-a through R-g
> (R-g is the operator's binding guardrail: formalism optional,
> informality never penalized — your census must test it, not assume
> it). Map preflight per the skill; the S1 census tranche
> (experiments/2026-08-06-change-seat-census-s1/) is your template for
> what a delivered census looks like (M-numbered rows, pasted
> commands, no claim without evidence).
> The census must measure, each row with a pasted command:
> Every path by which an artifact acquires an executable commitment
> today — the simulation/research capability channels, lambda_run,
> the dead property-oracle path (S6 PARKED P1 has the diagnosis
> chain), safe-skeleton forbidden-case compilation
> (workloads/models.py:105), and any path you find that these miss.
> Criticism dispatch per kind — how crit_program vs crit_argumentative
> selection actually works; what the critic's rendered pack shows
> about a target's kind; where ARGUMENTATIVE_AUTHORITY (observe_only /
> trial_required) is read and enforced; the exact semantics of
> execution_backed / formally_backed prose-immunity (rules/warrants.py).
> Refutation semantics per kind — what dies when a property fails
> (the DEMONSTRATIVE path, rules/crit.py:805), what a trial-guarded
> prose refutation can and cannot do, and what happens to dependents
> (the suspended_unsupported mechanics).
> The R-g audit — hunt for any place rank, admission, criticism
> exposure, survival, or acceptance keys on a conjecture's kind:
> scheduler ranking terms, pack rendering differences, acceptance
> criteria. Expected finding per the monitor's spot-checks:
> protection-only asymmetry, no penalty — but your job is to try to
> REFUTE that, not confirm it. Any penalty found is a load-bearing
> finding, reported plainly.
> The load-knob inventory (feeds D4) — every budget, period, ceiling,
> and share knob across config, v6_policy, capability controllers,
> criticism policy, scratch attention: name, location, unit, default,
> and whether it's frozen into the manifest at mint time or read live
> at label time.
> Historical encoding-failure evidence — the turmite and jolt cycle-0
> diagnostic blobs, capability-channel validation failures across
> committed roots: what fraction of executable-authoring attempts by
> the conjecturer failed on encoding rather than content.
> Deliverables: the measured census in the tranche directory, plus
> docs/map/CON-conjecture-kinds.md (per docs/map/SCHEMA.md — read it
> before writing; every load-bearing claim carries a check: line that
> must exit 0, and a new document needs checks that would fail if the
> behavior regressed). Accept: every census row has its pasted
> command; python tools/docs_verify.py full mode 0 failed and --audit
> 0 findings; full pytest gate untouched (you changed no code — run it
> once at the boundary to prove it: 0 failed net of the named
> pre-existing P1/P3).
> Anything broken you notice is PARKED with a ready-to-send prompt,
> never fixed — one tranche, one goal. Commit and push at every phase
> boundary with retry (2s/4s/8s/16s). Deliver through
> dr-validate-change and dr-deliver-change, then stop.

`docs/proposals/DUAL_MODE_CONJECTURE_PREPLAN.md` Rung D1 section,
quoted verbatim:

> ### Rung D1 — pipeline census  [MEASURE ONLY, no code]
> Absorbs coder-as-tool T1. Enumerate: every path by which an artifact
> acquires an executable commitment today (capability channel,
> lambda_run, the dead property path); the exact criticism dispatch
> per kind (crit_program vs crit_argumentative selection logic, pack
> rendering — what the critic SEES about a target's kind); the
> refutation semantics per kind (what dies when a property fails, what
> the trial can and cannot do to prose); the full inventory of load
> knobs (name, location, unit, current default, mint-time vs
> label-time). Historical: encoding-failure evidence from committed
> roots (cycle-0 blobs; capability-channel validation failures).
> Deliverable: measured table + `docs/map/CON-conjecture-kinds.md`.
> Accept: every claim carries a pasted command; docs_verify green.

`docs/proposals/DUAL_MODE_CONJECTURE_PREPLAN.md` requirements R-a
through R-g, quoted verbatim:

> - R-a: informal conjecture and criticism survive untouched — the
>   default loop is not weakened or gated.
> - R-b: the conjecturer has the OPTION to submit a conjecture in both
>   forms — informal claim and formal (executable/machine-checkable)
>   encoding — into the official epistemology loop.
> - R-c: a verifiable, typed signal says which kind each committed
>   conjecture is.
> - R-d: criticism arrives on the form matched to the kind — an
>   informal conjecture is never attacked with formal-grade demands
>   ("too zealous and harsh when it's uncalled for"), and a formal one
>   gets mechanical recourse first.
> - R-e: submitting formally is never disincentivised when the
>   conjecture implies a testable form.
> - R-f: a load-dial mechanism — operator-settable priority and share
>   for conjecture vs criticism load, scratchpad load, simulation
>   load, and coding load.
> - R-g (BINDING GUARDRAIL, operator's words 2026-08-08, "something
>   I've repeated endlessly": "as long as the existing infrastructure
>   does not force formalism and penalize conjectures that are not
>   formal"): no mechanism in this program — nor anywhere in the
>   harness — may require formal encoding for a conjecture to enter,
>   rank, survive, or be accepted; may weight ranking, scheduling, or
>   acceptance on a conjecture's KIND; or may escalate the
>   formal-channel option into pressure (the "when it implies"
>   surfacing is a one-time option rendering, never a repeated nudge,
>   never a penalty for declining). Formal backing may confer
>   PROTECTION (prose-immunity, as today); its absence confers no
>   disadvantage. D3's and D4's regressions must prove kind-blindness:
>   an informal conjecture's rank, criticism exposure, and acceptance
>   path are byte-identical whether or not the formal channel exists
>   in the build, and D5's formal-submission-rate metric is a
>   MEASUREMENT, never a target any mechanism optimizes toward.

CLAUDE.md "Operator design laws" section, quoted verbatim (binding
standing law, cited by the task as this tranche's R-g source):

> - **Formalism is an option, never an obligation** (2026-08-08,
>   repeated by the operator "endlessly" — do not make them repeat it
>   again): nothing may force a conjecture to be formal, and nothing
>   may penalize a conjecture for being informal — not admission, not
>   rank, not criticism exposure, not acceptance. Formal backing may
>   grant protection (prose-immunity); its absence grants no
>   disadvantage. Any design that weights outcomes on conjecture KIND
>   violates this law. See DUAL_MODE_CONJECTURE_PREPLAN.md R-g for the
>   full binding form.

## Requirements

R1 (process): "MEASURE ONLY — src/, tests/, tools/ stay
byte-untouched; your deliverables are the tranche's artifacts plus one
new map document."

R2 (process): "Setup: base your working branch on
origin/claude/monitor-session-handover-63ajqv and verify its head is
371e84d7 — if not, stop and say so." — done this session: verified.

R3 (process): "Run the session preflight (which deepreason || pip
install -e . --break-system-packages -q)." — done this session.

R4 (process): "Route through dr-change-orchestrator, starting with
dr-capture-request." — in progress (this document).

R5 (process): "Map preflight per the skill" — resolve this tranche's
work to `DR-SUB-`/`DR-CON-`/`DR-SEAM-` ids from `docs/map/INDEX.md`
before designing, per CLAUDE.md's map-preflight rule.

R6 (behavior): "The census must measure, each row with a pasted
command: Every path by which an artifact acquires an executable
commitment today — the simulation/research capability channels,
lambda_run, the dead property-oracle path (S6 PARKED P1 has the
diagnosis chain), safe-skeleton forbidden-case compilation
(workloads/models.py:105), and any path you find that these miss."

R7 (behavior): "Criticism dispatch per kind — how crit_program vs
crit_argumentative selection actually works; what the critic's
rendered pack shows about a target's kind; where
ARGUMENTATIVE_AUTHORITY (observe_only / trial_required) is read and
enforced; the exact semantics of execution_backed / formally_backed
prose-immunity (rules/warrants.py)."

R8 (behavior): "Refutation semantics per kind — what dies when a
property fails (the DEMONSTRATIVE path, rules/crit.py:805), what a
trial-guarded prose refutation can and cannot do, and what happens to
dependents (the suspended_unsupported mechanics)."

R9 (behavior): "The R-g audit — hunt for any place rank, admission,
criticism exposure, survival, or acceptance keys on a conjecture's
kind: scheduler ranking terms, pack rendering differences, acceptance
criteria. Expected finding per the monitor's spot-checks:
protection-only asymmetry, no penalty — but your job is to try to
REFUTE that, not confirm it. Any penalty found is a load-bearing
finding, reported plainly."

R10 (behavior): "The load-knob inventory (feeds D4) — every budget,
period, ceiling, and share knob across config, v6_policy, capability
controllers, criticism policy, scratch attention: name, location,
unit, default, and whether it's frozen into the manifest at mint time
or read live at label time."

R11 (behavior): "Historical encoding-failure evidence — the turmite
and jolt cycle-0 diagnostic blobs, capability-channel validation
failures across committed roots: what fraction of
executable-authoring attempts by the conjecturer failed on encoding
rather than content."

R12 (artifact): "Deliverables: the measured census in the tranche
directory, plus docs/map/CON-conjecture-kinds.md (per
docs/map/SCHEMA.md — read it before writing; every load-bearing claim
carries a check: line that must exit 0, and a new document needs
checks that would fail if the behavior regressed)."

R13 (process): "Accept: every census row has its pasted command;
python tools/docs_verify.py full mode 0 failed and --audit 0
findings; full pytest gate untouched (you changed no code — run it
once at the boundary to prove it: 0 failed net of the named
pre-existing P1/P3)."

R14 (process): "Anything broken you notice is PARKED with a
ready-to-send prompt, never fixed — one tranche, one goal."

R15 (process): "Commit and push at every phase boundary with retry
(2s/4s/8s/16s)."

R16 (process): "Deliver through dr-validate-change and
dr-deliver-change, then stop."

R17 (process, from dr-explain-to-operator): "Load dr-explain-to-operator
before your first message and follow it for every message,
intermediary and final." — done this session.

## Standing constraints

C1: "src/, tests/, tools/ stay byte-untouched" — hard boundary; no
edit to any file under those three trees for the duration of this
tranche.

C2: "the S1 census tranche (experiments/2026-08-06-change-seat-census-s1/)
is your template for what a delivered census looks like (M-numbered
rows, pasted commands, no claim without evidence)."

C3 (R-g, quoted above in full): binding guardrail against any
formalism-forcing or informality-penalizing design; the census's job
is to test it, not assume it.

C4 (CLAUDE.md, standing): "The map moves in the SAME COMMIT as the
code — a separate 'update docs' commit is the commit that gets
dropped." — applies loosely here since no code changes; the new map
document is delivered alongside the census artifacts, not as an
afterthought commit.

C5 (CLAUDE.md, standing): "Commits: one defect or one change per
commit; message states what, why, the live evidence (run ids), and
'Full gate: N passed, 0 failed' when code changed." — no code changes
in this tranche, so the gate-count clause does not apply, but commit
discipline still does.

## Open questions (for dr-spec-change)

Q1: "the dead property-oracle path (S6 PARKED P1 has the diagnosis
chain)" — need to locate the S6 tranche's PARKED.md entry P1 to anchor
this measurement before treating it as already-diagnosed rather than
re-deriving it from scratch.

Q2: "any path you find that these miss" — open-ended; the spec phase
needs to bound how exhaustively to search (e.g. grep for
`compile(`, `exec(`, `eval(`, subprocess/sandbox entry points) so the
tranche has a decidable stopping point.

Q3: "R-g audit ... hunt for any place rank, admission, criticism
exposure, survival, or acceptance keys on a conjecture's kind" — needs
a concrete search strategy (which modules/functions to grep and read)
decided in dr-spec-change so the audit is falsifiable rather than an
unbounded search.

Q4: "what fraction of executable-authoring attempts by the
conjecturer failed on encoding rather than content" — needs a defined
corpus (which committed roots count) and a defined method for
classifying "encoding failure" vs "content failure" from the typed
record, to be fixed in dr-spec-change.

Q5: the task says "full pytest gate untouched ... run it once at the
boundary to prove it: 0 failed net of the named pre-existing P1/P3" —
"P1/P3" here appears to reference known pre-existing gate failures
(not this tranche's own PARKED numbering); need to identify what P1/P3
refers to (likely from a prior tranche's RESULTS.md/PARKED.md) before
running the gate, so a pre-existing failure isn't mistaken for a
regression.

## Amendments

(none yet)
