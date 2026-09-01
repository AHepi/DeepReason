# Spec for: test all seat configurations on full judge trial

Traces: every item cites `REQUEST.md`. Untraceable work is out of scope.

## Outcome boundary

This tranche builds and starts an exact, resumable test campaign. It does not
claim that a multi-million-case live campaign can finish inside one interactive
session. Completion is a typed set-equality fact: every frozen case id has
exactly one terminal result. Until that equality holds, the report says how
many are complete, pending, provider-indeterminate, or interrupted; it never
renames a prefix or a percentage as exhaustive.

"Possible" means the shipped v6 path reached the configured provider seats and
produced a typed trial outcome. "Impossible" means the shipped compiler or
runtime produced a deterministic typed refusal before a provider-dependent
answer could decide the case. Transport errors, timeouts, malformed model
responses, and model silence are `provider_indeterminate`, never configuration
impossibility. Trial outcomes such as `defence-sustained`, `ensemble-split`,
`referential-integrity`, and `paraphrase-flip` are not configuration refusals.

The campaign is a reachability and configuration census. It does not score,
rank, optimize, eliminate, or statistically tighten models, prose, seats, or
configurations.

## Items

### S1 — frozen research and provider-semantics preregistration

Traces: R6, R7, R12, C2.

Targets: `PREREG.md`, `MATRIX_DOMAIN.json`.

Before: the repository has individual judge canaries and historical experiments
but no current Ollama full-court configuration census.

After: a pushed preregistration names the exact domains, ordering, case-id
algorithm, provider-call ceiling, result taxonomy, stop conditions, and the
registered outcomes before any completion request. The provider part cites
Ollama's first-party OpenAI-compatibility, thinking, GLM-5.3, and
GLM-5.3-Flash documentation. alphaXiv evidence is advisory coverage input only:

| Source | Adopted coverage consequence | Not adopted |
|---|---|---|
| https://www.alphaxiv.org/abs/2607.08535 | preserve parser/fallback logs; keep evaluator replacements distinct | model ranking or a reliability optimization target |
| https://www.alphaxiv.org/abs/2606.22329 | judge seat order is a separate case id | a preferred order |
| https://www.alphaxiv.org/abs/2608.00243 | include homogeneous and heterogeneous panels | majority, confidence, or error-correlation heuristics |

Provider authorities:

| Source | Consequence |
|---|---|
| https://docs.ollama.com/api/openai-compatibility | inspect the actual OpenAI-compatible `reasoning_effort` wire field |
| https://docs.ollama.com/capabilities/thinking | reasoning-capable models may think by default; omission is not assumed safe |
| https://ollama.com/library/glm-5.3:cloud | never omit reasoning for this default-max model; probe only non-high values |
| https://ollama.com/library/glm-5.3-flash:cloud | reasoning is always on; `none` is measured, never interpreted from its spelling |

Accept:

```text
python experiments/2026-09-01-change-live-full-judge-seat-matrix/matrix.py prereg-check
PREREG_OK ... forbidden_reasoning=[] forbidden_models=[] authority=defended_trial
```

### S2 — exact finite domains, never representative sampling

Traces: R2, R9, R10, R11.

Targets: `matrix.py`, `MATRIX_DOMAIN.json`.

The authenticated `GET /v1/models` response is sorted, byte-frozen, and pushed
before chat completions. Every returned text-chat model enters the roster
except an id whose punctuation-insensitive normalized form contains `kimik3`.
An unreachable or non-chat model remains a case and may return a provider
refusal; it is not silently filtered. The current documented roster predicts
22 non-Kimi-K3 model ids, but the authenticated snapshot controls.

The live court domain is the exact ordered product:

```text
critic x defender x judge[0] x judge[1] x (variator absent | variator model)
```

For roster size `M`, this is `M^4 + M^5` cases. Judge order is observable and
never collapsed. Every case first dispatches the configured critic for provider
compatibility, then drives the shipped precomputed argumentative trial with a
fixed valid ungrounded case so critic willingness cannot hide whether defender
and both judges are reachable. A separate scheduler arm, once per critic model
and topology class, records natural live-critic behavior without substituting it
for the guaranteed court arm.

The execution queue is ordered to make useful complete prefixes without
changing the full set: all `M^2` ordered judge pairs; all `M^3`
defender/judge courts; all `M^4` no-variator courts; then the remaining `M^5`
variator courts. A prefix is always labelled a prefix.

The offline structural domain is exactly exhaustive over the following frozen
finite boundary values:

| Axis | Frozen values |
|---|---|
| construction | managed preparation, direct compilation, single-model duplicate judges, single-model foreign-family judge |
| status authority | false, true; explicit manifest policy remains defended in both |
| judge master gate | false, true; explicit manifest policy remains defended in both |
| legacy criticism | false, true; explicit manifest policy remains defended in both |
| role cardinality | critic 1/2; defender 0/1/2; judge 0/1/2/3; variator 0/1/2 |
| judge identity | identical provider/model, same-family distinct model, cross-family, all orderings |
| auxiliary diversity | each active non-judge role independently same-model/different-model |
| schools | `N_SCHOOLS` 0/1/2/3/4; all 15 labelled partitions for four schools; every owner; coverage 1..N and N+1 |
| presentation | compact, standard, frontier; direct and compact contracts |
| output | text/json-object x native-schema/grammar/json-text |
| reasoning | none, low, medium, integer 2000; 2001 is a typed excluded case because the adapter maps it to high |
| split protocol | auto, on, off |
| paraphrase count | -1, 0, 1, 2, 3 |
| envelope | below, exactly at, and above request capacity |

Arbitrary model strings, list lengths, temperatures, token bounds, school
counts, and future provider options make global mathematical exhaustiveness
impossible. The report therefore uses the exact phrase "exhaustive over frozen
domain `<digest>`" and separately lists those unbounded dimensions. It never
uses pairwise coverage as a synonym for all configurations.

Accept:

```text
python experiments/2026-09-01-change-live-full-judge-seat-matrix/matrix.py enumerate --fixture-catalog
CATALOG_MODELS=22 JUDGE_PAIRS=484 CORE_COURTS=10648 NO_VARIATOR=234256 WITH_VARIATOR=5153632 TOTAL=5387888
```

The command also asserts generated ids equal the literal Cartesian product and
that reversed judge seats have different ids.

### S3 — defended-trial and provider-safety invariants

Traces: R3, R4, R5, R7.

Targets: `matrix.py`, `tests/test_live_full_judge_seat_matrix.py`.

Every executable manifest receives an explicit non-`None`
`CriticismPolicyV1(authority="defended_trial")`. The runner verifies Config,
manifest authority, defender contract, every judge contract, and the optional
variator contract before any provider call. Any consumed `observe_only` value
is a campaign-integrity failure before dispatch; it is not a test case.

Model ids are normalized across case, whitespace, punctuation, tags, and cloud
suffixes before the Kimi K3 ban is checked. The final serialized provider body,
not merely the source value, is checked for `high`, `max`, and `xhigh`. Numeric
reasoning above 2000 is excluded because DeepReason maps it to `high`.

Each roster model receives small, strict-JSON probes under explicit `none`,
`low`, and `medium`; never omitted, high, max, or xhigh. The result records the
raw message key set and the presence, length, and digest—not text—of
`reasoning`, `reasoning_content`, and `thinking`. A GLM-5.3 `none` response with
a populated trace is recorded as exactly that, not rewritten as disabled.
Full trials use `none` if the model accepts it and emits a usable form,
otherwise `low`; GLM-5.3-Flash and GPT-OSS use `low` if `none` is refused or
incompatible. There is no omitted/default road in live trials.

Accept:

```text
python -m pytest tests/test_live_full_judge_seat_matrix.py -q -k 'authority or kimi or reasoning or contracts'
... passed, 0 failed
```

### S4 — shipped court path and boundary taxonomy

Traces: R1, R2, R11.

Targets: `matrix.py`, `tests/test_live_full_judge_seat_matrix.py`.

The guaranteed arm compiles v6, binds exact leases and behavioral grants,
preseeds one accepted non-formally-backed target, supplies one valid ungrounded
attack, and calls the shipped `run_argument_trial_from_case` path. The expected
logical sequence for `J` judges and `P` returned paraphrases is:

```text
critic + defender + J initial judges + [variator + P*J rerulings]
```

For two judges and two paraphrases this is nine calls with a variator and four
without. Schema repairs and split legs are additional typed attempts, not new
seat configurations. The first missing or refusing boundary is preserved with
stage, exception type, code, pointer, exact message, and dispatch history.

Compile notices never filter a case. Managed preparation, missing roles,
single-judge, same-family/different-model, exact-duplicate, cross-family,
three-judge, same/foreign critic school, school binding, contract grant,
envelope, and formal-backing boundaries are all driven to their first shipped
outcome. A refusal inside shipped `trial.py` or `rules/crit.py` is a finding and
is never hotfixed in this tranche.

The runner records a distinct managed-path finding: current managed preparation
can construct only one judge seat. It must be tested as shipped and classified;
the direct compiler road is not allowed to make that managed road look green.

Accept:

```text
python -m pytest tests/test_live_full_judge_seat_matrix.py -q -k 'topology or typed or managed or sequence'
... passed, 0 failed
```

### S5 — three-call ceiling, credentials, and restart integrity

Traces: R1, R8, C3, C4.

Targets: `matrix.py`, `tests/test_live_full_judge_seat_matrix.py`.

One coordinator process owns at most three worker threads. A shared
`threading.BoundedSemaphore(3)` wraps every actual
`OpenAICompatEndpoint.complete` call, including retries and privately created
doctor endpoints. Qualification/probe and trial phases never overlap. A test
with blocking fake endpoints and retries must observe peak in-flight calls of
exactly three and never four.

The credential is accepted only from `OLLAMA_API_KEY` in process environment.
No `--api-key`, config value, manifest value, exception request dump, header
dump, environment dump, or credential hash exists. Each manifest contains only
`api_key_env="OLLAMA_API_KEY"`. Before any result is persisted, the process
scans the proposed bytes for the exact secret in memory; a match withholds the
diagnostic and emits `SECRET_BEARING_DIAGNOSTIC_WITHHELD` without printing the
secret or its hash.

The frozen domain and roster digests bind resume. Completed results are
immutable. An interrupted attempt is moved unchanged and a new numbered attempt
root is created; no committed or interrupted root is reopened writable. Case
results are temp-written, fsynced, and atomically renamed. A changed domain or
catalog refuses resume.

Accept:

```text
python -m pytest tests/test_live_full_judge_seat_matrix.py -q -k 'concurrency or credential or resume or digest'
... passed, 0 failed
```

### S6 — live launch and human possibility report

Traces: R1, R9, R11, C1, C2.

Targets: `PREREG.md`, `RESULTS.md`, `proof/`, runtime results outside git until
terminal and redaction-checked.

No chat completion occurs until PREREG and the authenticated catalog snapshot
are committed and pushed. The exact offline matrix builder and shipped direct
court run green against deterministic endpoints before provider contact. The
live process stops globally only for missing credential, credential leakage,
domain-digest mismatch, or corrupt driver state. A case-level refusal or model
failure is recorded and the queue continues.

Before the first live completion, `matrix.py soak` constructs an
experiment-owned `cycle_soak.SoakCase`, injects it into the soak driver's case
table in memory, and runs the unchanged `scripts/cycle_soak.py` machinery for
eight deterministic cycles on a Kimi-K3-free defended-court configuration. The
committed soak driver is imported and not edited. A green unrelated case is not
accepted as coverage for this launch shape.

`RESULTS.md` leads with current exact counts and a table of configuration
outcomes. It distinguishes direct full-court reachability, managed-launch
reachability, qualification/contract compatibility, semantic trial outcome,
and provider-indeterminate rows. Human-readable rows name model ids and seat
positions; machine artifacts retain canonical ids and digests. No result is a
model leaderboard or claim about truth, unanimity, guard quality, or live judge
behavior beyond the observed case.

Accept:

```text
python experiments/2026-09-01-change-live-full-judge-seat-matrix/matrix.py summarize
EXPECTED=<n> TERMINAL=<n> POSSIBLE=<n> IMPOSSIBLE=<n> PROVIDER_INDETERMINATE=<n> PENDING=<n> PEAK_IN_FLIGHT<=3
```

Launch gate:

```text
python -u experiments/2026-09-01-change-live-full-judge-seat-matrix/matrix.py soak
SOAK_VERDICT=PASS CASE=judge-matrix CYCLES=8
```

### S7 — branch isolation

Traces: C1, C3.

The entire campaign stays on
`codex/live-full-judge-seat-matrix-20260901`. No merge, rebase, pull, or update
of `main` is performed. GitHub is used only for commits on this branch. No
historical run root is edited, relaunched, amended, or reverified.

Accept:

```text
git rev-list --merges 00f10dde8c734e2f874358f9e2a375bb63aa4a35..HEAD
(empty)
```

## Assumptions (operator may override)

A1 (Q1): "all" means exact exhaustiveness over a pushed, finite domain digest:
every current catalog model in all five dispatched role positions, plus an
exact offline product over every finite control-flow boundary listed in S2.
Arbitrarily long role lists, arbitrary numbers, arbitrary strings, and future
models are explicitly unbounded and cannot form a finite global set.

A2 (Q1): the two initial judge positions are the full-court boundary because
the requested canary names both initial judges and their order. Three-judge
behavior is included in the offline boundary suite; arbitrary judge count is
unbounded and not misreported as exhaustively live-tested.

A3 (Q2): the prior credential handoff authorizes live Ollama use but not secret
persistence. Because this process currently has no safe credential source, live
execution pauses after preregistration until `OLLAMA_API_KEY` is mounted in the
workspace process environment. The operator is never asked to paste it into a
tracked file or command line.

A4: `none` is a requested wire setting, not an assertion that thinking is
absent. Observed trace fields control the report; their text is never stored.

A5: token use is unmetered at the campaign level (`TokenMeter(None)`), while
per-request completion bounds remain high enough to avoid silent truncation and
are still recorded as route process controls.

## Questions for operator

None before offline implementation and frozen preregistration. Live provider
contact requires the secure environment condition in A3.

## Out of scope

No change to `src/deepreason/`, Config defaults, manifest schemas, qualification
semantics, provider adapters, firewall identity, scheduler selection, trial
logic, criticism logic, formal-backing logic, bridge, Pareto/frontier,
successor/scratch, historical roots, or `main`.

No refusal found by the campaign is fixed here. It is recorded as a candidate
future defect tranche.

## Frozen-surface contact forecast

The only planned writes are new files under this tranche and one new test file.
No frozen or frozen-adjacent source file is edited. The plan-time gate can
inspect the existing tranche file and reports the lists verbatim:

```json
"frozen_surface_contacts": []
"frozen_adjacent_contacts": []
```

Full output:

```json
{"result_type": "BLAST_RADIUS_RESULT_V1", "targets": {"files": ["experiments/2026-09-01-change-live-full-judge-seat-matrix/REQUEST.md"], "symbols": []}, "base": null, "frozen_surface_contacts": [], "frozen_adjacent_contacts": [], "reachability": [], "consumers": {"tests": [], "map_checks": [], "qualification_digest": [], "wheel_smoke_pins": []}, "disclosure_summary": "This change touches none of the five frozen surfaces. 0 test file(s) and 0 map document(s) assert on the touched targets today.", "frozen_surface_verdict": "CLEAR"}
```

The gate refuses nonexistent planned files at spec time:

```text
evidence unavailable: declared file does not exist: experiments/2026-09-01-change-live-full-judge-seat-matrix/run_matrix.py
```

Therefore the first execution checkpoint creates the new files without provider
contact, immediately reruns `tools/blast_radius.py` over their actual bytes, and
stops before commit or provider contact if either computed list is nonempty.
This is not a grant to edit a frozen surface.

## Blast-radius census

Plan-time `consumers.tests`, `consumers.map_checks`,
`consumers.qualification_digest`, and `consumers.wheel_smoke_pins` are all `[]`
for the existing tranche target. New experiment/test files have no current
consumer by definition. MUST NOT MOVE: every `src/deepreason/` file, all map
documents, qualification digests, wheel pins, and historical roots.

Existing controls intentionally reused and MUST NOT MOVE:

| Control | Current result |
|---|---|
| `tests/test_judge_ensemble_boundary.py` | part of 13-pass ring below |
| `tests/test_judge_canary_dispatch.py` | part of 13-pass ring below |
| `tests/test_judge_canary_compile_gap.py` | part of 13-pass ring below |

## Measurements

M1 — current shipped canary/ensemble ring:

```text
python -m pytest tests/test_judge_ensemble_boundary.py tests/test_judge_canary_dispatch.py tests/test_judge_canary_compile_gap.py -q
.............                                                            [100%]
13 passed in 2.30s
```

M2 — currently documented 22-model roster arithmetic:

```text
M=22
ordered_judge_pairs=484
core_defender_judge_courts=10648
no_variator_full_role_product=234256
variator_full_role_product=5153632
live_total_M4_plus_M5=5387888
upper_default_calls=47319712
```

M3 — wall-time price at the account's hard ceiling, excluding repairs,
qualification, retries, and queue overhead:

```text
1s average/request -> 182.6 days at three in flight
10s average/request -> 1825.6 days at three in flight
30s average/request -> 5476.8 days at three in flight
60s average/request -> 10953.6 days at three in flight
```

M4 — DeepReason's actual Ollama wire mapping:

```text
None -> field omitted
integer <= 2000 -> reasoning_effort=low
integer > 2000 -> reasoning_effort=high
string -> reasoning_effort=<string>
```

M5 — safe credential census:

```text
{'OLLAMA_API_KEY_present': False, 'credential_store_exists': False, 'experiment_env_count': 0}
```

M6 — managed/direct construction measurement from the shipped tree:

```text
build_preparation_manifest always calls compile_run_manifest without
single_model, judge_family, or blind_same_model_judges; public managed seat
groups cannot add a second judge. Direct Config.roles may carry ordered judge
routes, and compile_run_manifest accepts the exact-duplicate or cross-family
two-seat shapes.
```

## Options

| Road | Scope | Price | Disposition |
|---|---|---|---|
| A — exact full live product | `M^4 + M^5`, every ordered role assignment, no sampling | 5,387,888 cases and up to 47,319,712 logical calls at M=22; months to years at three in flight | CHOSEN as the immutable long queue because R2/R9/R10 explicitly ask for all |
| B — core court only | every defender/judge0/judge1 assignment, fixed critic/variator | 10,648 cases at M=22; useful but does not test every critic and variator assignment | CHOSEN only as an early complete prefix of A, never as final exhaustiveness |
| C — ordered judge pairs only | 484 cases at M=22 | fastest possible/impossible judge-topology map, but omits defender/critic/variator assignments | CHOSEN only as the first prefix of A |
| D — family/equivalence sample | one or a few representatives per topology class | cheap | REJECTED for the live matrix because it contradicts R10; retained only for mathematically unbounded offline axes and labelled control-flow coverage |

The recommendation is A with C then B as deterministic queue order. It obeys
the operator's literal request while yielding useful evidence long before the
tail can finish.

## Budget

Implementation budget, excluding ledger/proof/result artifacts:

```text
matrix/domain + safety + resume: 260 lines
shipped-court live adapter:       270 lines
tests:                            190 lines
total:                            720 lines
python -c "print(sum([260,270,190]))" -> 720
```

Because 720 exceeds the workflow's approximately 300-line single-change
ceiling, implementation is split into two ordered code checkpoints with an
independent commit and validation after each: domain/safety/resume first
(estimated 300 including its tests), shipped-court live adapter second
(estimated 420 including its tests and the experiment-owned soak wrapper). No
paid call occurs between them. The
campaign launch and result ledger are a third evidence-only checkpoint.

Frozen surfaces edited: none. Estimated code commits: two. Evidence commits:
preregistration, authenticated catalog freeze, prefix checkpoints, and final or
stopped result segments.

Rubric: 9/9 yes — every R is mapped; every named mechanism is traced to a
shipped path; exact finite and unbounded domains are distinguished; options are
priced; alphaXiv and Ollama authorities are recorded; credential and
concurrency gates are explicit; blast-radius output is pasted; frozen contact
is empty; no untraceable behavior is added.
