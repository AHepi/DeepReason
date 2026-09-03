<!-- tranche: stop report -->
# Request: "an errors report? a better agent.md that walks LLMs through how configuration works?"

Captured: 2026-09-03, from the executor window prompt for CHANGE TRANCHE
"the stop report — the harness writes the first failure report, and no
window may diagnose without it".

Base: `main` at or after `7653b04393` (this branch's head at capture:
`7653b0439`). Branch: `claude/executor-stop-report-paiagc`.

## Verbatim (the authority for everything below)

Operator, 2026-09-03, message 1:

> "the other windows keep making a lot of mistakes. I can't tell if
>  they're causing the crashes or not. The window that said criticism
>  fails to leave a trace was wrong. One window reported a crash happened
>  because a conjecturer seat kept failing to fill a form. When I said
>  that particular model passed qualification with ease, it double
>  checked and realised it's config was off. So many of these mistakes
>  it's hard to tell genuine failure from merely a bad manifest. What do
>  you recommend? Ab errors report? A better agent.md that walks LLMs
>  through how configuration works?"

Operator, 2026-09-03, message 2 (approving the monitor's answer to
"What do you recommend?"):

> "do it."

Note on message 1, recorded and NOT corrected in the requirements: "Ab
errors report" is read as "An errors report" (nearest repo-context
resolution; `dr-ask-the-right-question` §2, the typo row). "agent.md" is
read as the LLM-facing operating documentation of this repo — CLAUDE.md
and the skills under `.claude/skills/` — there being no `agent.md` in the
tree. Both resolutions are recorded here rather than silently applied.

## Monitor's reading (MARKED AS SUCH — not the operator's words)

> The pattern is: the first report is written from the settings file the
> window WROTE, not from what the run actually COMPILED and RAN, and the
> window corrects itself only after the operator objects. Three remedies,
> one tranche: (R1) the harness produces the first failure report itself,
> from the record only; (R2) the diagnosis skill refuses to proceed
> without that report attached; (R3) a one-page map of how a setting
> travels from the operator's file to what a seat receives, with the
> command that shows each stage. The structural cause underneath — six
> settings not carried in the compiled manifest and restored at run time
> from notices — is PARKED with a priced prompt, not fixed here.

The operator's "do it." (message 2) approves EXACTLY this three-part
remedy — `dr-ask-the-right-question` §2, the "do it" row: approval of the
stated plan, not license to widen.

## Requirements

Traceability: R1-R12 are the monitor's remedy (1); R13-R15 remedy (2);
R16-R17 remedy (3); R18-R20 the regression proof; R21-R25 process.
Each answers the operator's own worry, quoted per requirement group.

### Group A — R1: the stop report (the harness writes the first report)

Answers: *"So many of these mistakes it's hard to tell genuine failure
from merely a bad manifest."*

R1 (behavior): "One command over a run root, read-only, never writing
into the root, deterministic, emitting Markdown and JSON."

R2 (behavior): "Every line derived from the record (manifest, notices,
qualification results, attempt traces, workflow objects, run-status,
verify_root); NEVER from a run-config YAML unless one is passed
explicitly for a DIFF section that shows 'what you wrote' against 'what
compiled'."

R3 (behavior) — section 1: "WHAT ACTUALLY RAN: per seat — model,
model-profile stamp, reasoning knob value as sent (or 'omitted →
provider default'), max_tokens, timeout, split protocol; every gate and
switch as compiled, with the ENGINE_CONFIG_FIELD_NOT_CARRIED fields
marked 'restored at run time from notice'; every compile notice; embedder
as compiled (EMBEDDER_MODEL null → say 'hashing', do not guess)."

R4 (behavior) — section 2: "PRE-RUN CHECK: qualification result per seat
× form (eventual valid, first-pass, repairs), with the rows for any seat
implicated in the stop quoted in full. If qualification was cached, say
so and from which subject digest."

R5 (behavior) — section 3: "PROVIDER HEALTH per seat: attempts, faults,
zero-token returns, transport diagnostics by kind, last fault, HTTP 429
with the provider's message when present."

R6 (behavior) — section 4, the four boxes: "THE STOP, CLASSIFIED into
four boxes, each with the typed evidence that supports or rules it out."

R7 (behavior) — box CONFIGURATION: "the run did not carry what was set
(notice-restored fields; YAML-vs-manifest diff; reasoning omitted where
the profile says the model needs a value; split armed on a seat whose
profile says the extraction leg breaks it)."

R8 (behavior) — box ENVIRONMENT: "account usage cap (429 + message),
transport wall (RemoteDisconnected streaks), container restart marks,
orphaned qualification processes if detectable."

R9 (behavior) — box MODEL: "the failing work item's attempt ladder
(schema invalid / truncated at cap / semantic rejection / compact
recovery / decomposition / insufficient-capability object) set beside
THAT seat's qualification row for THAT form. If the seat passed
qualification 20/20 on that form, the report must SAY SO in the model box
and point at configuration or environment instead."

R10 (behavior) — box HARNESS: "the stop message and exception path,
claimable only when the three boxes above are ruled out with evidence."

R11 (behavior) — the non-assertion rule: "The report never asserts a
defect; it ranks the boxes by evidence and says which are ruled out and
why."

R12 (behavior) — section 5: "CONTINUABILITY: state, stop_reason,
lifecycle refusal, verify_root summary, and whether `continue`/`amend`
would be accepted today."

### Group B — R2: the refusal (no window may diagnose without it)

Answers: *"The window that said criticism fails to leave a trace was
wrong."*

R13 (artifact): "Amend `.claude/skills/dr-diagnose/SKILL.md` (and the
live-run driving manual `dr-drive-harness`): DIAGNOSIS.md must open with
the stop report's classification section pasted verbatim."

R14 (artifact): "no phase may name a defect, a seat, or a model as the
cause without citing the report line that supports it. A window that
cannot produce the report stops there."

R15 (process): "Follow `authoring-skills` for the edit; this is a rule
added after an incident, and the incident is quoted."

### Group C — R3: the configuration stages page

Answers: *"A better agent.md that walks LLMs through how configuration
works?"*

R16 (artifact): "One page (a map CON- document, with re-runnable
single-line `check:` lines) showing the four stages a setting passes
through — the operator's file → the compiled manifest → run-time
restoration from notices → what the seat actually receives (pack, wire
form, profile-resolved knob) — with the command that reveals each stage."

R17 (artifact) — the traps, stated flatly: "the six not-carried fields;
an omitted reasoning knob is the provider's DEFAULT, not 'off'; the split
protocol arms on an omitted knob; qualification caches by subject digest;
the `frontier` CLI prints the problem registry, not the artifact
frontier; env-var switches exist only on experiment branches and are not
configuration. Short enough to read at the moment of doubt."

### Group D — the regression on the record (the mutation proof)

Answers: *"I can't tell if they're causing the crashes or not."*

R18 (behavior): "Run the report against these committed roots and require
each to land in the right box with the evidence quoted":
  - "P-A1 (branch claude/live-reasoning-p-a1-bv65kl, run 4565139800…):
     MODEL box (seat exhaustion, insufficient-capability object) AND
     ENVIRONMENT box (39 RemoteDisconnected on one endpoint), with the
     CONFIGURATION box noting reasoning omitted → provider default max and
     split armed."
  - "P-A2 epoch 1 (branch claude/executor-live-run-p-a2-84hyco):
     qualification refusal on ONE seat × form; CONFIGURATION/MODEL boxes
     naming the reasoning knob, not 'the model cannot fill forms'."
  - "P-A2 epoch 2: ENVIRONMENT (429 usage cap, provider message quoted)."
  - "P-A2 epoch 3: HARNESS (all other boxes ruled out; last provider call
     valid; stop message quoted)."
  - "Phase-1 M3-C0 and M1-H0 (branch claude/executor-window-phase-1-
     s5ex6w): ENVIRONMENT, self-inflicted concurrency 429s."
  - "Any root where the seat passed qualification 20/20 on the failing
     form: the MODEL box must say so explicitly."

R19 (behavior): "show a naive version RED (misfiling) and the shipped one
GREEN."

R20 (behavior): "Add a unit fixture per box so the classifier cannot
drift."

### Group E — process, scope and validation

R21 (process): "If the command is a new public CLI subcommand, update the
wheel-smoke pins in the SAME commit (CLAUDE.md: 'any commit changing that
surface updates the pins and re-runs the smoke in the same commit')."

R22 (process): "VALIDATION: full gate, 0 failed target; pre-authorized
known-not-yours baselines (bc map check; the toolchain-digest pin)
recorded, not stopped on."

R23 (process): "Map moves in the SAME commit."

R24 (process): "DELIVERY.md reconciles against the operator's words
above, requirement by requirement."

R25 (process): "Verify before your first commit that no tracked file
carries a credential."

## Standing constraints

C1 (frozen surfaces): "FROZEN SURFACES: none edited. The report READS
qualification results and CALLS verify_root; it edits neither. If any
section needs a new record kind, that is surface 3 → PRICED STOP; prefer
reading what exists." — window prompt.

C2 (read-only over roots): "read-only, never writing into the root" —
window prompt R1. Reinforced by CLAUDE.md: "Never edit a committed run
root's contents."

C3 (out of scope, parked with ready prompts): "carrying the six
not-carried fields in the manifest (surface 4, priced); the P2 'config
does not echo every field' gap if it turns out to block section 1 (say
so); any defect found while building." — window prompt.

C4 (branch): "Work on your window's assigned branch; commit and push at
every phase boundary." — window prompt. Branch:
`claude/executor-stop-report-paiagc`.

C5 (base): "Base on main at or after 7653b04393." — window prompt.

C6 (the record is the only evidence): CLAUDE.md — "Model prose is never
evidence; `log.jsonl`, `objects/`, `progress.jsonl`, `run-status.json`,
`REPLAY_VALIDATION.json`, and `verify_root` are." This is what R2 above
operationalizes.

C7 (map preflight): CLAUDE.md — "resolve the work to `DR-SUB-`/`DR-CON-`/
`DR-SEAM-` ids from `docs/map/INDEX.md`, read the seam before the
subsystems, and read `INV-frozen-surfaces.md` before designing. Record the
ids in the tranche's first artifact." — discharged in the next section.

C8 (prompts inline): CLAUDE.md Conventions — "Prompts written for the
operator to paste into executor windows are delivered inline in the chat
reply as ONE fenced code block". Binds the parked prompts of C3.

## Map preflight (C7 discharged)

Read before designing, in the order the map requires:

1. `docs/map/INDEX.md` — the routing table (read).
2. `docs/map/INV-frozen-surfaces.md` — **read first, always** (read).
   Five surfaces spanning seven paths; the report touches NONE as a
   writer. It CALLS `verify_root` (surface 3) and READS qualification
   results (surface 5 territory) — both read-only, per C1.

Resolved ids the work touches (to be confirmed and extended in SPEC.md):

| id | why this tranche touches it |
|---|---|
| `DR-SUB-verification` | `verify_root` is CALLED for section 5 (read-only) |
| `DR-SUB-manifest` | the compiled manifest is the source for section 1 (read-only) |
| `DR-SUB-llm` | seats, profiles, packs, wire contracts — sections 1 and 3 |
| `DR-SUB-periphery` | the CLI surface, if R1's command lands there |
| `DR-CON-seats` | "per seat" is the spine of sections 1-3 |
| `DR-CON-model-profiles` | "model-profile stamp", "reasoning knob value as sent" |
| `DR-CON-run-identity` | the run root the command is pointed at |
| `DR-INV-frozen-surfaces` | C1 — the boundary this tranche must not cross |
| `DR-CON-configuration-stages` | **does not exist yet** — R16 creates it |

Seam documents to read BEFORE the subsystems (map ordering rule), to be
confirmed in SPEC.md: `SEAM-llm-x-manifest.md` (what the manifest carries
into a seat request — the heart of R3/R7), `SEAM-harness-x-verification.md`
(what section 5 may call), `SEAM-llm-x-verification.md`.

A missing id is a finding, not a blocker (`dr-drive-harness` §4):
`DR-CON-configuration-stages` is missing, and creating it IS R16.

## Open questions (for dr-spec-change — NOT answered here)

The window prompt names three STOP-AND-ASK triggers. Recorded verbatim:

Q1: "whether the command is a new subcommand or a flag on `deepreason
results`" — user-facing shape; `dr-ask-the-right-question` §4 lists taste
on user-facing shape as question-earning. To be derived as far as the
record allows, then batched.

Q2: "any new record kind" — would be frozen surface 3 (C1) → PRICED STOP.
To be answered by the record: does everything the five sections need
already exist in committed roots?

Q3: "anything that would make the report write into a root" — C2. To be
answered by the record: can `verify_root` be called without a writable
open? (CLAUDE.md/`dr-drive-harness` §5: "open the root READ-ONLY — a
writable open repairs, i.e. destroys, the evidence".)

## Amendments

(append-only; later operator messages land here as R26... or "R7a
supersedes R7", each with its verbatim quote)

### Amendment 1 — 2026-09-03, the three STOP questions answered

The operator was presented with SPEC.md's batched question set (Q1, Q1b,
Q1c), each option priced, each carrying a recommendation. They selected
the recommended option in all three. Their selections, verbatim as the
option labels they chose:

Q1 — "Should the stop report be its own command, or a flag on the
existing `deepreason results`?"

> "New subcommand (Recommended)"

Q1b — "Should the report also cover failures that never produced a run
root (config errors that fail qualification)?"

> "Include it (Recommended)"

Q1c — "The itemized budget is ~1,300 lines, well over the ~300-line
guideline. How should it ship?"

> "One tranche, two commit groups (Recommended)"

**R26 (behavior, answers Q1):** the stop report is a NEW public CLI
subcommand — `deepreason stop-report <root-or-home> [--json]
[--config FILE] [--verify]` — not a flag on `deepreason results`.
`deepreason results` is not edited. Binds S1, S12, and the Q1 fork in
SPEC.md, which is hereby CLOSED.

**R27 (behavior, answers Q1b):** ROOTLESS MODE IS IN SCOPE. The report
accepts a home that holds no run root and reports from the qualification
record alone, so the failure class the operator described — a
configuration error that fails qualification and never mints a root —
is covered. Binds S12 and the three rootless regression rows of S18.
The Q1b fork is CLOSED.

**R28 (process, answers Q1c):** ONE TRANCHE, TWO ORDERED COMMIT GROUPS.
Group A: the report (S1-S12), the regression proof (S18, S20), the unit
fixtures (S19), the wheel smokes (S21). Group B: the diagnosis-skill
refusal (S13, S14) and the configuration-stages page (S15-S17). ONE
DELIVERY.md reconciles R1-R28. The Q1c fork is CLOSED.

Recorded per `dr-ask-the-right-question` §2, the "do it" row: the
operator approved EXACTLY the recommended options as stated, which is
approval of those plans and not a licence to widen any of them.


### Amendment 2 — 2026-09-03, the budget ceiling raised

Raised at step 9 as a STOP (`dr-execute-step` §6: an EXCEEDED
`diff_budget.py` verdict is a stop, not a footnote). The operator was
given the measured overrun, its cause, and three priced roads. Their
selection, verbatim as the option label chosen:

> "Raise the ceiling, continue (Recommended)"

**R29 (process):** SPEC.md's ~1 307-line source ceiling is SUPERSEDED by
a ceiling of **2 100 source insertions** across `src/deepreason`,
`tests`, `docs/map` and `.claude/skills` (1 561 landed at step 9, ~420
projected for Group B and the proof script, plus headroom). The tranche
ledger under `experiments/` and generated proof outputs remain artifacts
and are not counted, as SPEC.md's Budget section already stated. R28's
two-commit-group shape is unchanged.

Recorded cause, so the overrun is not read as scope creep: every line
traces to an existing R number. The excess is three capabilities the
LIVE RECORD forced, none of which the estimate could have contained
because the estimate was written before the roots were read —
(1) the `root-no-log` third source kind, because R18's P-A2 epochs 1 and
2 are neither a run root nor a bare home; (2) the clean-stop guard,
because R6 must not manufacture blame for a run that reached a clean
terminal; (3) the vindication-scoping fix, because R9 must not let one
seat's pass excuse a different seat's failure. Each ships with its own
regression test in commit 72046a17b4.
