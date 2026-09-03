# Spec for: the stop report — the harness writes the first failure report

Traces: every item cites R/C numbers from REQUEST.md. Untraceable items
are bugs. REQUEST.md re-read in full before writing this (no amendments
exist yet).

**Status: ANSWERED AND UNBLOCKED (REQUEST.md Amendment 1, 2026-09-03).** All
three questions below were put to the operator with priced options and a
recommendation each; the operator selected the recommended option in all
three, ledgered as R26 (new subcommand), R27 (rootless mode in scope) and
R28 (one tranche, two commit groups). The "Questions for operator"
section is retained verbatim as the record of what was asked and what it
cost; every fork in it is CLOSED.

---

## Measurements (every load-bearing claim below is a pasted command output)

These were taken before any design was written. Roots extracted read-only
from their own branches into the session scratchpad via `git archive`;
nothing was written into any root, and no root was copied into this
branch.

**M1 — the six ENGINE_CONFIG_FIELD_NOT_CARRIED notices are in the
manifest, machine-readable, with pointer/value/resolution.** (P-A1 root,
`run-manifest.json`, `compile_notices`.)

    ADJUDICATION_STATUS_AUTHORITY_ENABLED  /engine_config/...  "true"   resolution=null
    ENGAGED_CRITICISM_AUTHORITY            /engine_config/...  "defended_trial"
                                           resolution=/criticism_policy/authority
    JUDGE_SEATS_ENABLED                    /engine_config/...  "true"   resolution=null
    JUDGE_SUMMONS_PER_CYCLE                /engine_config/...  "2"      resolution=null
    LEGACY_CRITICISM_ENABLED               /engine_config/...  "false"
                                           resolution=/criticism_policy
    SCHOOL_SEATS_ENABLED                   /engine_config/...  "true"
                                           resolution=/control_plane_policy/school_execution

Supports R3 ("marked 'restored at run time from notice'") and R17 ("the
six not-carried fields"). The count SIX is measured here, not recalled.

**M2 — every per-seat field section 1 needs is already in
`manifest.roles`.** Example row (`defender`):

    {"endpoint_id": "ollama-glm-5.3", "family": "glm", "max_tokens": 49152,
     "model_id": "glm-5.3", "model_revision": "glm-5.3", "provider": "ollama",
     "output_mechanism": "json_text", "output_mode": "json_object",
     "reasoning": null, "temperature": null, "timeout_s": 1800,
     "context_window_tokens": 131072}

`reasoning: null` is the exact case R3 requires be rendered "omitted →
provider default" rather than "off". Supports R3, R7, R17.

**M3 — `EMBEDDER_MODEL` is carried inside `engine_config_json`.**

    EMBEDDER_MODEL = "nomic-ai/nomic-embed-text-v1.5"
    EMBEDDER_FAILURE_POLICY = "error"

Supports R3's embedder clause. A null here is reported as "hashing", per
R3's explicit "do not guess".

**M4 — provider health is derivable per seat from `log.jsonl`.** Each
event carries `llm.attempt_trace[]`, whose entries carry `endpoint_id`,
`seat`, `model_profile`, `max_tokens`, `timeout_s`, `valid`,
`natural_stop`, `usage_unknown`, `tokens`, `transport_attempts`,
`transport_diagnostics[]`, `validation_path`, `diagnostic_ref`, and
`split_legs[]` (each leg with its own `transport_diagnostics`).
Diagnostics are strings shaped `Kind:detail`, e.g.
`HTTPError:HTTP-429:HTTP Error 429: Too Many Requests`. Supports R5, R8,
R9 — including "429 with the provider's message when present", which is
the third colon-field.

**M5 — transport-fault census across the extracted roots** (this
instrument: walk `llm.attempt_trace[].transport_diagnostics` and
`split_legs[].transport_diagnostics`, count by kind):

    2026-09-01-live-all-modules-p-a1/run                          71 llm records
        41  RemoteDisconnected:Remote end closed connection without response
         1  HTTPError:HTTP-500:HTTP Error 500: Internal Server Error
    .../home-default/runs/failed-429-run-fe00609058e10605590206d51ab2b7a0
                                                                 71 llm records
        48  HTTPError:HTTP-429:HTTP Error 429: Too Many Requests
    .../home-default/runs/retired-1cycle-run-292f964edb58e58ef0e7d957f29bac55
                                                                 28 llm records
        31  HTTPError:HTTP-429:HTTP Error 429: Too Many Requests
    .../home-m1/runs/run-f23da86ddfd5ab820957221cfebe4b2e        105 llm records
         1  RemoteDisconnected:Remote end closed connection without response

**M5a — the P-A1 RemoteDisconnected streak is on ONE endpoint, and the
count is 41, not 39.** Broken down by (role, endpoint, kind):

    23  ('conjecturer', 'ollama-glm-5.3', 'RemoteDisconnected')
    18  ('defender',    'ollama-glm-5.3', 'RemoteDisconnected')
     1  ('conjecturer', 'ollama-glm-5.3', 'HTTPError')

REQUEST.md R18 says "39 RemoteDisconnected on one endpoint". "One
endpoint" is confirmed (`ollama-glm-5.3`, both roles). The count by this
instrument is **41**. Recorded per `dr-ask-the-right-question` §1, "cite
the instrument with the number" — the acceptance check in S18 binds the
instrument's number, not the prose's.

**M6 — the qualification record answers "did this seat pass this form"
directly, per seat × contract.** (P-A1, `production-contract-qualification.json`,
`schema: deepreason-production-contract-doctor-v1`, 23 pairs, 460 cases.)
The rows that matter to the operator's own complaint:

    conjecturer#0 conjecturer.turn.v6 ep=ollama-deepseek-v4-pro-0813
        first=20/20 eventual=20 repairs=0 qualified=True
    conjecturer#1 conjecturer.turn.v6 ep=ollama-glm-5.3
        first=20/20 eventual=20 repairs=0 qualified=True
    summarizer#0 scratch.cluster-guide.compact.v1 ep=ollama-glm-5.3
        first=15/20 eventual=20 repairs=5 qualified=True
    synthesizer#0 scratch.link.compact.v1 ep=ollama-glm-5.3
        first=19/20 eventual=20 repairs=1 qualified=True

This is the single most load-bearing measurement in the tranche. The
window the operator caught — the one that "reported a crash happened
because a conjecturer seat kept failing to fill a form" — would have been
contradicted by line 1 of this table, which the harness already had on
disk at the moment that window wrote its report. R9's rule ("If the seat
passed qualification 20/20 on that form, the report must SAY SO") is
therefore satisfiable from the existing record with no new record kind.

**M7 — per-case qualification failures carry a typed `failure_code`.**
(Phase-1 `evidence-429/c0-unqualified-doctor.json`, the M3-C0 case.)

    summary: case_count 300, eventual_valid_count 283, pair_count 15,
             qualified false, qualified_pair_count 11, repair_count 0
    case:    {"case_id": "case-002", "eventual_valid": false,
              "failure_code": "ENDPOINT_HTTP_429", "first_pass_valid": false,
              "repair_count": 0, "semantic_admission": false}

Supports R8 (ENVIRONMENT box) for the rootless case, and R4.

**M8 — a home caches qualification by subject digest, and the digest IS
the filename.** (Phase-1 `home-default/`.)

    home-default/
      provider.yaml
      qualification-cache/4b0c48889a00b48c37ea90f1470cb29e8c3426182972882ff7f83867df822f08.json
      runs/

    that file: {"schema": "deepreason-reusable-qualification.v1",
                "subject_digest": "4b0c4888...f08", "status", "pairs",
                "bundle_digest", "policy_preset_id", "policy_preset_digest",
                "provider_profile_digest"}

Supports R4's "If qualification was cached, say so and from which subject
digest" — answerable exactly, with no new record kind.

**M9 — `verify_root` already opens the root READ-ONLY.**
(`src/deepreason/invariants.py:942-943`.)

    h = Harness(root, read_only=True)
    second = Harness(root, read_only=True)

And `Harness.__init__` (`harness.py:97-106`) threads `read_only` into
`BlobStore`, `ObjectStore` and `EventLog`, and refuses a missing root
rather than creating one. Answers Q3 outright: calling `verify_root`
cannot write into a root, and the report's own opens use the same
`read_only=True` spelling. Supports R1, R12, C2.

**M10 — the CLI may not construct a Harness.**
(`src/deepreason/application/results.py:376-389`, docstring.)

    The path-taking entry point exists so CLI and MCP clients can report a
    run's geometry without constructing a `Harness` themselves: those clients
    are thin service dispatch by design, and
    `test_clients_have_only_thin_service_dispatch_and_one_registry` enforces
    it by asserting `Harness(` never appears in their source.

This DECIDES the architecture: all report logic lives in
`application/`, and the CLI is dispatch only. Not a preference — an
existing architecture test.

**M11 — `resolve_results_root` REFUSES a home with no run root.**
(`application/results.py:88-120`.)

    raise ResultsError(
        "RESULTS_ROOT_NOT_FOUND",
        f"{base} is neither a run root (no log.jsonl) nor a home holding one",
    )

Load-bearing: see the Contradiction section — three of R18's six named
failures are exactly this case, so the stop report cannot reuse this
resolver unchanged.

**M12 — the wheel-smoke pins do NOT pin the CLI subcommand set.**
(`scripts/wheel_smoke.py`.)

    24: EXPECTED_MCP_SCHEMA_SHA256 = ...
    32: "console_scripts": {          <- entry-point NAMES only
    41: EXPECTED_MCP_TOOLS = {...}

The pinned surface is: console-script entry-point names, the MCP tool
set, and the MCP schema sha. A new `deepreason` SUBCOMMAND moves none of
them unless an MCP tool is also added. R21's obligation is therefore
discharged by RUNNING both smokes and recording that the pins did not
move — and this spec adds NO MCP tool, precisely so that stays true.
(Re-verified at the S21 step, not assumed here.)

**M13 — the frozen-surface gate, run on the declared targets.** Verbatim
`BLAST_RADIUS_RESULT_V1` fields, pasted per `dr-spec-change` step 3:

    "frozen_surface_contacts": []
    "frozen_adjacent_contacts": []
    "frozen_surface_verdict": "CLEAR"
    "disclosure_summary": "This change touches none of the five frozen
      surfaces. 6 test file(s) and 8 map document(s) assert on the touched
      targets today. Reachability here means a syntactic call path exists
      from a known entry point; it does not prove the path is ever actually
      exercised at runtime -- a symbol can be syntactically reachable and
      still never fire because of a runtime precondition this gate does not
      evaluate."
    "reachability": resolve_results_root REACHABLE, results_summary REACHABLE,
      render_results REACHABLE, embedder_summary_for_root REACHABLE

Command run (files that do not yet exist are excluded because the gate
refuses a declared path that is absent — "evidence unavailable: declared
file does not exist"; new files carry no consumers and no frozen contact
by construction, and the gate is RE-RUN with them present at the first
`[COMMIT]` step):

    python tools/blast_radius.py \
      --files src/deepreason/cli/main.py src/deepreason/application/results.py \
              scripts/wheel_smoke.py docs/map/INDEX.md \
              .claude/skills/dr-diagnose/SKILL.md \
              .claude/skills/dr-drive-harness/SKILL.md \
      --symbols resolve_results_root results_summary render_results \
                embedder_summary_for_root

---

## THE MATERIAL CONTRADICTION (R18 vs the record) — read this first

`dr-spec-change` step 2: a mechanism the request NAMES is a suggestion,
not a requirement; verify it reaches the code, and where it cannot, that
is a material contradiction to record in writing.

R18 names six failures and says "Run the report against these committed
roots". **Three of the six produced no run root at all**, because they
died during QUALIFICATION, before a root existed. Verified against each
tranche's own committed narrative, not inferred:

| R18 row | Root on its branch? | What the record says |
|---|---|---|
| P-A1 | **YES** — `2026-09-01-live-all-modules-p-a1/run`, run_id `4565139800f5…` | `state=failed stop=operational_failure cycle=5`, msg `V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY … route seat has terminally exhausted its smallest authorized contract`. Matches R18. |
| P-A2 epoch 1 | **NO** | P-A2 RESULTS.md §4: "The live run never reached a reasoning cycle. The ladder stopped at qualification after 96 minutes with 22 of 23 pairs qualified, 445 of 460 cases". Cause confirmed there as the `reasoning` knob alone (blocked pair 5/20 at `low`, 20/20 at default effort). |
| P-A2 epoch 2 | **NO** | P-A2 RESULTS.md §5: "Epoch 2 launched 22:03:13Z and its qualification refused 26 minutes later … 5 of 23 pairs, 100 of 460 cases, and one failure code throughout: `ENDPOINT_HTTP_429`". |
| P-A2 epoch 3 | **YES** — `failed-epoch3-run-1b89ed64e050c354` | `state=failed stop=operational_failure cycle=0`, msg `v6 conjecture context must be planned after durable work preparation`; RESULTS.md §7 localizes it to `rules/conj.py:827`. Matches R18's HARNESS box. |
| Phase-1 M3-C0 | **NO** | Phase-1 PARKED.md P3: "`deepreason reason` then correctly refused with `QUALIFICATION_TIER_SHALLOW`, rc=1, **producing no run root at all**." |
| Phase-1 M1-H0 | **YES** — `home-default/runs/run-fe00609058e1…` | but `state=completed stop_reason=budget_exhausted`, exit 0, "a clean, successful run by every other measure, 47 admitted conjectures". Its issue is `terminal_lifecycle_refusal: STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY` blocking `continue` — a **section-5 CONTINUABILITY** case, **not** an ENVIRONMENT/429 case. |

Two consequences, both load-bearing, neither invented:

**(a) The report must accept a HOME with no run root.** The failure class
the operator complained about *most* — "that particular model passed
qualification with ease… it double checked and realised its config was
off" — is precisely the P-A2-epoch-1 class: a config-caused
QUALIFICATION refusal that never produces a root. A report that only
accepts a root is silent on three of six recorded cases and on the
operator's own example. This is not scope creep; it is R18 read against
the record. `resolve_results_root` refuses this case today (M11), so the
report needs its own tolerant resolution.

**(b) R18's phase-1 row is miscast, and a better root exists on the same
branch.** The root-bearing ENVIRONMENT/429 case on that branch is
`home-default/runs/failed-429-run-fe00609058e1…` — **48**
`HTTPError:HTTP-429` diagnostics (M5). This spec uses that root for the
ENVIRONMENT box and uses M1-H0 for the CONTINUABILITY section, which is
what each actually demonstrates. R18's rows are honoured by PROPERTY
(every box demonstrated on committed evidence), not by its literal root
naming, and this table is the written record of the deviation.

Nothing here is a defect claim against the harness. R18 was written from
tranche narratives; the narratives were right and the root inventory was
assumed. That is the same failure mode this tranche exists to remove,
which is worth stating plainly.

---

## Items

Notation: `accept:` is a command plus its expected result, decidable by a
machine. Every item cites its R/C numbers.

### Group A — the report (R1-R12)

**S1 (R1, R2, C2, M10)** — NEW `src/deepreason/application/stop_report.py`.
All gathering, classification and rendering. Before: no such module.
After: a pure read-only reader exposing
`stop_report(path, *, config_path=None) -> dict` and
`render_stop_report(report) -> str`. Every root/home open uses
`read_only=True` (M9). Deterministic: no wall-clock, no randomness, no
dict-order dependence — every list sorted by a stated key.
  accept: `python -m pytest tests/test_stop_report.py -q` → 0 failed; and
  a byte-equality test running the report twice on one root and asserting
  identical output (determinism, R1).
  accept: `grep -c 'read_only=True' src/deepreason/application/stop_report.py`
  ≥ 1 and `grep -c 'read_only=False' …` = 0.

**S2 (R1)** — the report NEVER writes into the root. Enforced, not
promised: the test snapshots `sha256` of every file under the root plus
the full path listing before and after a run of the report, and asserts
both unchanged.
  accept: `python -m pytest tests/test_stop_report.py -k not_write -q` → passed.

**S3 (R2)** — sources are the record only: `run-manifest.json`,
`run-status.json`, `progress.jsonl`, `log.jsonl`, `objects/`,
`REPLAY_VALIDATION.json`, `production-contract-qualification.json`,
`qualification-cache/*.json`, and `verify_root`. A run-config YAML is
read ONLY when `--config` is passed, and then only to populate the DIFF
subsection ("what you wrote" vs "what compiled").
  accept: an architecture test asserting no `.yaml`/`.yml` literal is
  read in `stop_report.py` outside the single `config_path` branch →
  passed.

**S4 (R3)** — section 1 WHAT ACTUALLY RAN. Per seat (role × seat index,
sorted by role then seat): model_id, model_revision, family, endpoint_id,
provider, model_profile stamp, `reasoning` rendered as its value or
`omitted → provider default` when null (M2), max_tokens, timeout_s,
output_mechanism, context_window_tokens, and split-protocol state. Then:
every gate and switch as compiled, with each of the six
ENGINE_CONFIG_FIELD_NOT_CARRIED fields marked `restored at run time from
notice` and carrying its pointer/value/resolution (M1); every compile
notice verbatim; embedder as compiled from `engine_config_json`
(`EMBEDDER_MODEL` null → the literal word `hashing`, never a guess) (M3).
  accept: on the P-A1 root the section prints exactly 6 lines matching
  `restored at run time from notice`; prints `omitted → provider default`
  for the `defender` seat; prints `nomic-ai/nomic-embed-text-v1.5`.

**S5 (R4)** — section 2 PRE-RUN CHECK. One row per seat × form from the
qualification record: `first_pass_valid_count`/`representative_cases`,
`eventual_valid_count`, `repair_count`, `qualified`. Rows for any seat
implicated in the stop are quoted IN FULL (all fields, plus per-case
`failure_code` tallies when present, M7). If qualification came from the
home cache, the section says so and names the subject digest (M8).
  accept: on the P-A1 root, section 2 contains the literal line for
  `conjecturer#0 conjecturer.turn.v6` with `first_pass 20/20` and
  `qualified True`.

**S6 (R5)** — section 3 PROVIDER HEALTH per seat: attempts, faults,
zero-token returns (`tokens == 0` or `usage_unknown`), transport
diagnostics grouped by kind with counts, the LAST fault verbatim, and any
`HTTP-429` rendered with the provider's own message text (M4).
  accept: on the P-A1 root, section 3 reports `RemoteDisconnected` = 41
  against endpoint `ollama-glm-5.3` (M5a — the instrument's number); on
  the `failed-429-…` root it reports `HTTP-429` = 48 with the message
  `HTTP Error 429: Too Many Requests`.

**S7 (R6, R7, R8, R9, R10, R11)** — section 4 THE STOP, CLASSIFIED. Four
boxes: CONFIGURATION, ENVIRONMENT, MODEL, HARNESS. Each box carries
(i) the typed evidence FOR it, (ii) the typed evidence that RULES IT OUT,
and (iii) a verdict of `SUPPORTED` / `RULED OUT` / `NO EVIDENCE EITHER
WAY`. The boxes are RANKED by evidence. The report never asserts a
defect (R11) — no box's text may contain a claim of a code defect; HARSH
constraint, tested. HARNESS is `SUPPORTED` only when the other three are
`RULED OUT` with cited evidence (R10).
  accept: a test asserting the rendered section-4 text contains none of
  the strings `is a bug`, `is a defect`, `caused by a defect` → passed.
  accept: per-box unit fixtures, S19.

**S8 (R9, M6)** — the qualification-vindication rule, stated as its own
item because it is the operator's own example. When the seat implicated
in the stop passed its failing form at full marks
(`first_pass_valid_count == representative_cases_per_pair`), the MODEL
box MUST print an explicit sentence naming the count and MUST be ranked
below CONFIGURATION and ENVIRONMENT.
  accept: on the P-A1 root the MODEL box contains the substring
  `passed qualification 20/20` and the CONFIGURATION box is ranked above
  it in the rendered order.

**S9 (R7)** — the CONFIGURATION box's four evidence probes, each typed:
(1) notice-restored fields present (M1); (2) YAML-vs-manifest diff, only
when `--config` given; (3) `reasoning` omitted on a seat whose
`CON-model-profiles` entry says the model needs a value; (4) split
protocol armed on a seat whose profile says the extraction leg breaks it.
Probes (3) and (4) consult the committed model-profile documents; where
no profile entry exists the probe reports `NO PROFILE ENTRY` rather than
guessing.
  accept: on the P-A1 root the CONFIGURATION box notes both
  "reasoning omitted → provider default" and "split armed", per R18's
  P-A1 row.

**S10 (R12)** — section 5 CONTINUABILITY: `state`, `stop_reason`,
`terminal_lifecycle_refusal`, the `verify_root` verdict summary (stored
by default; the module calls `verify_root` read-only, M9), and a plain
verdict on whether `continue`/`amend` would be accepted today.
  accept: on `home-default/runs/run-fe00609058e1…` (M1-H0) section 5
  prints `STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY` and a
  `continue: REFUSED` verdict.

**S11 (R1)** — Markdown AND JSON. `render_stop_report(report)` gives the
Markdown; the same `report` dict is the JSON (`--json`). Both carry every
section; neither is a subset of the other by accident.
  accept: a test asserting every section id present in the dict appears
  in the Markdown, and vice versa → passed.

**S12 (contradiction (a); R18 rows 2, 3, 5)** — ROOTLESS MODE. The report
accepts a run root OR a home. Given a home with no run root, it emits the
same five sections, with sections 1/3/5 reporting typed ABSENCE
(`no run root: the run never started` plus the refusal code when
recorded) and sections 2/4 built from the qualification record alone.
Its own resolution, not `resolve_results_root` (M11), which refuses this
case.
  accept: run against a home fixture holding only
  `qualification-cache/<digest>.json` → exit 0, section 2 populated,
  section 4 ranks ENVIRONMENT or CONFIGURATION per the failure codes.

### Group B — the refusal (R13-R15)

**S13 (R13, R14, R15)** — amend `.claude/skills/dr-diagnose/SKILL.md`:
DIAGNOSIS.md must OPEN with the stop report's section 4 pasted verbatim;
no phase may name a defect, a seat, or a model as the cause without
citing the report line supporting it; a window that cannot produce the
report stops there. Written per `authoring-skills`, and the incident is
quoted — the operator's own words from REQUEST.md, including "The window
that said criticism fails to leave a trace was wrong."
  accept: `grep -q 'stop report' .claude/skills/dr-diagnose/SKILL.md` and
  the file contains the verbatim operator quote → both true.

**S14 (R13)** — amend `.claude/skills/dr-drive-harness/SKILL.md` §5 so
the "where to look when something breaks" table names the stop report as
the FIRST instrument, above the per-file rows it subsumes.
  accept: the stop-report row precedes the `run-status.json` row in that
  table.

### Group C — the configuration-stages page (R16-R17)

**S15 (R16, C7)** — NEW `docs/map/CON-configuration-stages.md`, written
to `docs/map/SCHEMA.md`. Four stages, each with the command that reveals
it: the operator's file → the compiled manifest → run-time restoration
from notices → what the seat actually receives. Carries re-runnable
single-line `check:` lines at column 0.
  accept: `python tools/docs_verify.py` → 0 failed, and
  `python tools/docs_verify.py --audit` does not report any of this
  document's checks as unable to fail.

**S16 (R17)** — the traps section, stated flatly: the six not-carried
fields (M1); an omitted reasoning knob is the provider's DEFAULT, not
"off" (M2); the split protocol arms on an omitted knob; qualification
caches by subject digest (M8); the `frontier` CLI prints the problem
registry, not the artifact frontier; env-var switches exist only on
experiment branches and are not configuration.
  accept: all six traps present, each with a `check:` or an evidence
  pointer; document ≤ 200 lines ("short enough to read at the moment of
  doubt", R17).

**S17 (C7, R23)** — register the new document in `docs/map/INDEX.md`
(concept table + a routing row), and update `docs/map/SUB-application.md`
and `docs/map/SUB-periphery.md` for the new module and CLI surface — in
the SAME commit as the code (M13 named both as consumers).
  accept: `python tools/docs_verify.py --links` → every DR- reference
  resolves.

### Group D — the regression on the record (R18-R20)

**S18 (R18, contradiction (b))** — a committed proof script,
`experiments/2026-09-03-change-stop-report/proof/run_regression.py`,
runs the report over each case and asserts the expected box ranking with
the evidence quoted. Outputs committed under `proof/`. The roots are NOT
copied into this branch; the script takes a path and the proof records
the branch + commit each root came from, so it is re-runnable by
`git archive` (the exact commands recorded in the proof output).
  Cases and their required verdicts:
  | case | source | required |
  |---|---|---|
  | P-A1 | `origin/claude/live-reasoning-p-a1-bv65kl` | MODEL supported (seat exhaustion + insufficient-capability object) AND ENVIRONMENT supported (41 RemoteDisconnected, one endpoint); CONFIGURATION notes reasoning-omitted and split-armed |
  | P-A2 epoch 1 (rootless) | `origin/claude/executor-live-run-p-a2-84hyco` | CONFIGURATION + MODEL name the reasoning knob; MODEL does NOT say "cannot fill forms" |
  | P-A2 epoch 2 (rootless) | same | ENVIRONMENT supported, 429 usage cap, provider message quoted |
  | P-A2 epoch 3 | same, `failed-epoch3-run-1b89ed64…` | HARNESS supported, other three RULED OUT, stop message quoted |
  | Phase-1 429 root | `origin/claude/executor-window-phase-1-s5ex6w`, `failed-429-run-fe006090…` | ENVIRONMENT supported, 48 × HTTP-429 |
  | Phase-1 M3-C0 (rootless) | same, `evidence-429/` | ENVIRONMENT supported, `ENDPOINT_HTTP_429` per case |
  | Phase-1 M1-H0 | same, `run-fe006090…` | section 5: continue REFUSED, refusal code printed |
  | qualification-vindication | P-A1 | MODEL box says `passed qualification 20/20` |
  accept: `python experiments/2026-09-03-change-stop-report/proof/run_regression.py`
  → every case PASS, output committed.

**S19 (R20)** — `tests/test_stop_report.py` carries ONE unit fixture per
box: a minimal synthetic root (built in a tmp dir from typed records)
that lands in exactly that box. Committed in `tests/`, gate-runnable,
independent of any branch. Built to `dr-execute-step`'s durability rules:
each asserts the guarded CLAIM (this evidence ⇒ this box ranked first),
not an incidental string, so it fails only when the classifier drifts.
  accept: `python -m pytest tests/test_stop_report.py -q` → 0 failed, and
  the file contains four fixtures named for the four boxes.

**S20 (R19)** — the mutation proof. A NAIVE classifier (the one this
tranche exists to replace: read the run-config YAML and blame the seat
named in the stop message) is implemented in the proof script only, run
over the same cases, and shown to MISFILE at least the P-A1 and P-A2
epoch-1 cases. RED captured before GREEN, both committed.
  accept: `proof/naive_red.txt` shows ≥ 2 misfiled cases;
  `proof/shipped_green.txt` shows 0. Both committed in the same commit.
  The naive classifier lives OUTSIDE the module it judges (the treadle
  lesson in CLAUDE.md: keep what judges the work outside the cone it
  judges).

### Group E — process (R21-R25)

**S21 (R21, M12)** — run both wheel smokes; if any pin moves, update it
in the SAME commit as the surface change. This spec adds no MCP tool, so
the expectation is that no pin moves; that expectation is VERIFIED by
running, not assumed.
  accept: `python scripts/wheel_smoke.py` → rc 0;
  `python -u scripts/wheel_operational_smoke.py` → rc 0; the diff of
  `scripts/wheel_smoke.py` is empty OR the pin change rides this commit.

**S22 (R22)** — full gate. `python -m pytest tests/ -q -n 4` → 0 failed,
with the pre-authorized known-not-yours baselines (the `bc` map check;
the toolchain-digest pin) recorded against `docs/AUDIT_BASELINES.md`, not
stopped on.
  accept: gate output pasted in VALIDATION.md; any non-zero failure is
  either fixed or shown to be a recorded baseline.

**S23 (R24)** — DELIVERY.md reconciles R1-R25 one by one against the
operator's verbatim words.
  accept: DELIVERY.md contains a row for every R number.

**S24 (C3)** — PARKED.md carries a ready-to-send prompt for: the six
not-carried fields (surface 4, priced); the P2 config-echo gap if it
blocks section 1; and any defect found while building.
  accept: PARKED.md exists with one paste-ready fenced prompt per park.

---

## Assumptions (operator may override)

A1 (Q2) — **No new record kind is needed.** Decided from the record, not
asked: M1-M8 show every field all five sections need already exists in
committed roots and homes. Frozen surface 3 is therefore untouched, and
M13's gate agrees (`frozen_surface_verdict: CLEAR`). No PRICED STOP is
raised on Q2.

A2 (Q3) — **Nothing writes into a root.** Decided from the code: M9 shows
`verify_root` already opens `read_only=True`, and `Harness` threads that
into all three stores. The module uses the same spelling, and S2 makes it
a tested property rather than a promise. No PRICED STOP on Q3.

A3 — **Report logic lives in `application/`, CLI is thin dispatch.**
Forced by M10's existing architecture test, not chosen.

A4 — **The report reads the STORED `verify_root` verdict by default** and
re-derives only on an explicit flag, mirroring `deepreason results
--verify`. Smallest reading: re-deriving on every invocation would make a
diagnostic command expensive on large roots, and R12 asks for a
"verify_root summary", not a fresh derivation. Assumed, operator may
override.

A5 — **"Deterministic" (R1) means byte-identical output for the same root
and flags**, which S1 tests directly. Timestamps of the REPORT ITSELF are
therefore omitted from both renderings.

A6 — R18's P-A1 "39 RemoteDisconnected" is bound at the instrument's
number, **41** (M5a), with "one endpoint" confirmed. Assumed rather than
asked because the property R18 wants (a transport wall on one endpoint,
supporting the ENVIRONMENT box) is unchanged by the count.

---

## Questions for operator (STOP — non-empty)

**Q1 — is the command a new subcommand, or a flag on `deepreason
results`?** (The window prompt designates this a STOP-AND-ASK.)

Recommendation: **a new subcommand, `deepreason stop-report
<root-or-home> [--json] [--config FILE] [--verify]`.** Four reasons, each
measured rather than preferred:
  1. It must work where `results` cannot. Three of six recorded cases are
     rootless homes, and `resolve_results_root` REFUSES those (M11).
     A flag on `results` would either inherit that refusal or force a
     change to the resolver that every existing `results` caller shares —
     56 assertion sites in `tests/test_results_command.py` alone (M13).
  2. It is a different artifact. `results` answers "what did this run
     produce"; the stop report answers "why did it stop, and whose fault
     is it not". A flag that replaces the entire output shape is a
     subcommand wearing a flag's clothes.
  3. Discoverability is the point. R13/R14 require every diagnosing
     window to produce this. `deepreason stop-report` is findable from
     `--help`; a flag inside `results` is not.
  4. The modularity law (2026-08-26): "when a design forks between a
     tighter coupling that is smaller and a declared interface that is
     larger, the interface wins."
Cost of the alternative (flag on `results`): ~40 fewer lines, and a
shared resolver change that touches the most heavily asserted reader in
the tree. Cost of the recommendation: one new subcommand on the public
surface; no wheel-smoke pin moves (M12), verified at S21.

**Q1b — the scope fork the record forced (please confirm or veto).**
Contradiction (a) above: to cover the operator's own example (a config
error that fails QUALIFICATION and never makes a root), the report must
accept a rootless home — S12. This is ~60 lines beyond a root-only
report. Recommendation: **include it.** Without it the report is silent
on three of the six recorded cases, including the one the operator
described. Veto is cheap and reversible: drop S12 and the three rootless
regression rows, and the tranche still ships the other five.

**Q1c — the budget is large; may it ship as two ordered sub-tranches?**
The itemized estimate below is ~1 090 lines, over `dr-spec-change`'s ~300
guideline. Recommendation: **one tranche, two ordered commit groups**
(A: the report + regression + fixtures + smokes; B: the refusal + the
configuration-stages page), with a single DELIVERY.md reconciling
R1-R25 — because the operator approved three remedies as one answer, and
because R13's refusal is worthless without R1's report existing. Veto
option: ship group A only, and I hand back a paste-ready prompt for
group B.

---

## Out of scope (explicit)

- Carrying the six not-carried fields in the manifest — C3, surface 4,
  parked with a priced prompt at S24. Not requested.
- Fixing the P2 config-echo gap — C3. If it blocks section 1, S24 says so
  rather than fixing it. Not requested.
- Any defect found while building — parked, per `dr-change-orchestrator`
  scope contract. Not requested.
- An MCP tool for the stop report — would move the wheel-smoke pins
  (M12). Not requested.
- Changing `deepreason results` behaviour. Not requested.
- Re-running or repairing any of the six recorded runs. Not requested,
  and C2 forbids touching their roots.

## Frozen-surface contact forecast

**none expected — `frozen_surface_verdict: "CLEAR"`.** The gate's own
computed lists, pasted verbatim (M13):

    "frozen_surface_contacts": []
    "frozen_adjacent_contacts": []

Reads only: `verify_root` is CALLED read-only (M9), qualification records
are READ. Neither is edited. No new record kind (A1). The gate is RE-RUN
with the new files present at the first `[COMMIT]` step, per M13's noted
exclusion.

## Blast-radius census

From M13's `consumers` fields, every hit classified:

| target | consumer | verdict |
|---|---|---|
| `src/deepreason/cli/main.py` | `tests/test_calculus_standing.py:424` | MUST NOT MOVE — adding a parser does not change existing dispatch |
| `src/deepreason/application/results.py` | `tests/test_error_catalog.py:66` | MUST NOT MOVE — `results.py` is not edited (S12 gives the report its own resolver) |
| `scripts/wheel_smoke.py` | `tests/test_wheel_operational.py:4197` | MUST NOT MOVE — no MCP tool added (M12) |
| `resolve_results_root` | `tests/test_results_command.py` ×6 | MUST NOT MOVE — deliberately not reused (M11) |
| `results_summary` | 56 sites across 5 test files | MUST NOT MOVE — not edited |
| `render_results` | `tests/test_results_command.py` ×8 | MUST NOT MOVE — not edited |
| `src/deepreason/cli/main.py` | 17 map-check sites across 7 documents | MUST NOT MOVE except `SUB-periphery.md` (S17) — EXPECTED TO MOVE there only |
| `src/deepreason/application/results.py` | `SUB-application.md` ×4 | EXPECTED TO MOVE — S17 adds the new module's rows |
| `scripts/wheel_smoke.py` | `SUB-periphery.md` ×3 | MUST NOT MOVE |
| `docs/map/INDEX.md` | `CON-authority.md:340`, `REC-change-a-seam.md:40` | MUST NOT MOVE — S17 adds rows, does not renumber |
| `embedder_summary_for_root` | `SUB-application.md` ×3 | MUST NOT MOVE — reused as-is, not edited |

Manual cross-check (required where the gate reports UNKNOWN): the gate
reported no UNKNOWN reachability entries, so no supplementary grep is
owed. The four declared symbols all came back REACHABLE.

## Budget

Itemized:

| item | est. lines |
|---|---|
| S1-S12 `application/stop_report.py` | 470 |
| S1 CLI parser + thin dispatch (`cli/main.py`) | 35 |
| S19 `tests/test_stop_report.py` (4 box fixtures + determinism + not-write + rootless) | 320 |
| S15-S16 `docs/map/CON-configuration-stages.md` | 150 |
| S17 `INDEX.md` + `SUB-application.md` + `SUB-periphery.md` | 45 |
| S13 `.claude/skills/dr-diagnose/SKILL.md` | 35 |
| S14 `.claude/skills/dr-drive-harness/SKILL.md` | 12 |
| S18/S20 `proof/run_regression.py` (incl. the naive classifier) | 180 |
| S24 `PARKED.md` | 60 |

    python3 -c "print(sum([470,35,320,150,45,35,12,180,60]))"
    1307

Headline: **~1 307 changed lines, 6-8 commits.** Frozen surfaces
touched: **none** (M13, `CLEAR`). This exceeds `dr-spec-change`'s ~300
guideline; Q1c puts the split to the operator rather than deciding it
unilaterally. Generated proof outputs under `proof/` are artifacts, not
counted as source lines.

Rubric: 6/6 yes — every R has a machine-decidable accept (R1-R25 map to
S1-S24); blast-radius census pasted from the tool and every hit
classified; frozen-surface forecast recorded with the gate's verbatim
lists; every named mechanism traced to code it actually reaches (M9-M13),
with the one that does NOT reach recorded as the material contradiction;
DESIGN-AND-STOP measurement/option discipline applied to Q1; nothing in
this spec is untraceable to an R or C number.
