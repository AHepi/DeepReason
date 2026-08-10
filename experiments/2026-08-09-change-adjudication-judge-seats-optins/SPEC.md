# SPEC: adjudication / judge-seats / legacy-criticism / schools opt-ins
Traces: REQUEST.md R1-R9, C1-C12
Map preflight: DR-CON-seats, DR-SUB-adjudication, DR-CON-authority, DR-CON-schools,
DR-INV-frozen-surfaces, DR-SEAM-adjudication-x-authority, DR-SEAM-manifest-x-schools,
DR-SEAM-schools-x-scratch (read before this document; every design choice below is
checked against them)

Window discipline (C1, C4, C9, C12): SPEC-AND-STOP. No code this window. This
document is the sole deliverable, committed and pushed, then the session stops
for operator words — no intermediate stop (C12; Amendment 2 pre-authorizes
continuing through budget/fork questions rather than pausing for them, C10-C11).

Method note: every claim below was produced by one of ten parallel research
passes over the committed tree (six for the original two-halves request, three
more for Amendment 1's schools/judge-target/liveness-census scope), each
required to cite file:line or a pasted record excerpt. A sample of the most
decision-critical and most surprising claims (config_referee's opt-in gate and
live firing record; the judge-starving negative finding; the seat-binding
conflict rule) was independently re-verified by the executor before this
document was written. Every figure and quote below carries its citation;
none is asserted from memory.

---

# HALF 1 — THE WHY

## 1(a). The assignable-seat census, as of today

`src/deepreason/seat_bindings.py:34-43` — the whole vocabulary, verbatim:

```python
GROUP_ROLES: dict[str, frozenset[str]] = {
    "conjecture": frozenset({"conjecturer", "variator"}),
    "coder": frozenset({"property_designer", "encoder"}),
    "scratch": frozenset({"conjecturer", "synthesizer", "summarizer"}),
}
GROUP_ALIASES: dict[str, str] = {"simulation": "conjecture"}
```

`_known_groups()` (`seat_bindings.py:54-55`) — what `--seat GROUP=PATH` actually
accepts without a typed refusal — returns `{conjecture, coder, scratch,
simulation}`. Four names pass CLI validation. `argumentative_critic` and
`judge` are absent; `--seat critic=...` is refused before any provider call
(confirmed independently below, §1(a)-omnibus).

**The conflict rule** — `resolve_seat_bindings()`, `seat_bindings.py:172-185`:
walks every bound group (aliases canonicalized to their target first), and if
two different bound groups claim the same role name with different
`profile_digest`s, raises `SeatBindingError("SEAT_BINDING_ROLE_CONFLICT", ...)`;
identical digests are tolerated silently. The comment at `seat_bindings.py:158-165`
names the concrete collision this exists for: binding both `scratch=X` and
`conjecture=Y` (X≠Y) collides on the shared `conjecturer` role.

**Which of the four names is actually *effective* in an ordinary live run —
the numeric reconciliation:**

| Group | Role set | Live dispatch today? | Evidence |
|---|---|---|---|
| `conjecture` | `conjecturer`, `variator` | **LIVE**, both roles, essentially every cycle | `rules/conj.py:442,607,1849,1870,2068`; `scheduler/scheduler.py:1103,2168-2178,2487-2513` |
| `simulation` | alias → `conjecture` | **LIVE**, by definition — not an independent seat | `seat_bindings.py:43` |
| `coder` | `property_designer`, `encoder` | **DEAD**, both roles, structurally | see below |
| `scratch` | `conjecturer`, `synthesizer`, `summarizer` | **Only `conjecturer` fires** (re-covers `conjecture`'s own role); `synthesizer`/`summarizer` are off by default | see below |

`coder`'s `property_designer` — no public path ever fires it. Its sole
dispatch site, `scheduler/scheduler.py:2272-2296` (`_property_step`), only
runs when `checker_wf_commitment(base)` (`oracle.py:776`) already finds an
ACTIVE `program:property_oracle` commitment in the graph — and no code path
anywhere in `src/deepreason/` ever mints the *first* such commitment. This is
a bootstrap circularity, proven end-to-end and delivered as a live-run
finding: `experiments/2026-08-08-live-two-seat-ab-s6/PARKED.md:8` — **"P1
(DEFECT, found by the live run — parked, NOT fixed):
`property_designer` has no public path to ever fire"** — with the full
7-step call-graph proof at `PARKED.md:25-48`, and the corrected verdict at
`RESULTS.md:175-177`: *"Probability of the `coder` seat actually dispatching
a live call was **0, not low** — this is a structural dead path, not a
capability-channel-style stochastic one."* No committed root's `log.jsonl`
has ever carried a `"role": "property_designer"` record (`RESULTS.md:224-227`).
`coder`'s other role, `encoder`, has zero non-test callers: `draft_encoded_commitment`
(`rules/encoding.py:17`) is called only from `tests/test_encoding.py:9,21,33`.

`scratch`'s `synthesizer` — its one production call site,
`scheduler.py:1976-1985`, is gated by `uses_conjecturer`
(`scheduler.py:1911-1917`), which forces `True` unconditionally whenever
`run_manifest.schema_version == 6` — and every manifest the harness accepts
today *is* schema v6 (`run_manifest.py:3614-3621` rejects v1-5 and anything
above `LATEST_SCHEMA_VERSION=6`). So `synthesizer`'s only production path is
permanently bypassed on every run the CLI can produce. `summarizer`'s
scratch-specific consumer (`ScratchAuthoringService`) is gated behind two
independent off-by-default switches: `ScratchAuthoringPolicyV1.enabled: bool
= False` (`run_manifest.py:685`) and `ScratchpadConfig.enabled: bool = False`
(`config.py:156`).

**Numeric answer to "why only two seats are assignable":** 4 CLI-accepted
names collapse to 3 distinct groups (`simulation` is an alias, not a fourth);
of those 3, `coder` is categorically dead (0/2 roles ever reachable) and
`scratch`'s only live role duplicates `conjecture`'s own — its two
distinctive roles are both off by default or schema-bypassed. That leaves
exactly **`conjecture` and its `simulation` alias** as the operator's "two
seats": one truly independent, effective, live seat, wearing two names.

**Reconciled with the omnibus's parked no-critic-group gap** —
`experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry/PARKED.md:3-24`,
verbatim: **"P1 (GAP, not a defect): the reverse arm is structurally
impossible with today's seat vocabulary... There is no `"critic"` group, and
`argumentative_critic` is not a member of any `GROUP_ROLES` set... `--seat
critic=...` or `--seat argumentative_critic=...` is rejected by CLI
validation before any provider call is made -- this is a typed refusal, not
a stochastic miss."** This gap is orthogonal to the `coder`/S6 dead-seat
finding — `coder` is *bindable but non-functional*; `critic` is *not even
bindable*. The same PARKED.md explicitly anticipates the connection
(`PARKED.md:53-57`): a future `critic` group "must be checked against the
same class of dispatch-path question before being declared usable, not just
declared bindable" — i.e. the omnibus authors already knew "assignable" and
"effective" are different questions, from watching `coder` fail the second
one.

## 1(b). Design archaeology — deliberate exclusion, or never considered?

**Finding: never considered, not deliberately excluded.** No document in the
seat-binding design lineage — the plan, its S1 census, or S2's own SPEC —
contains a sentence of the form "critic/judge is out of scope" or "critic/judge
deliberately excluded." The silence is total, not argued.

`docs/proposals/ROLE_SEAT_SEPARATION_PLAN.md:14-17` — the plan's own anchors
section *names* `argumentative_critic` and `judge` as existing first-class
roles: *"Roles are first-class in `llm/roles.py` (spec §9): conjecturer,
argumentative_critic, batch_critic, config_referee, defender, variator,
judge, summarizer, synthesizer, embedder..."* — so their existence was known
to the plan's authors. But the very next scoping paragraph
(`ROLE_SEAT_SEPARATION_PLAN.md:35-40`) glosses only three names — "coder",
"conjecturer", "scratch" — and never mentions criticism-side roles,
positively or negatively: *"'Coder', in this plan, = the roles/call sites
whose output is executable... 'Conjecturer' = the conjecturer/variator text
roles. Scratch = the scratch-authoring call sites..."*

Rung S2's own SPEC.md (`experiments/2026-08-06-change-seat-binding-design-s2/SPEC.md`)
only elaborates the mapping for the plan's four pre-named groups
(`SPEC.md:425-445`) and raises exactly two operator questions
(`SPEC.md:594-617`, the conjecture/simulation alias overlap and a Config-field
sub-choice) — neither about critic/judge. Its "Out of scope (explicit)"
section (`SPEC.md:619-633`) does not name critic/judge scope as an excluded
item either — it is simply absent from the document, not listed as
rejected.

The measurement rung that fed S2, Rung S1's CENSUS.md
(`experiments/2026-08-06-change-seat-census-s1/CENSUS.md`), *did* fully
enumerate criticism/adjudication call sites with the same rigor as
conjecture-side ones (M6, M8-M11, M14-M15, M21, M23, M25-M30, M32-M33, M36,
M43) — but contains **zero occurrences of the word "group"** across its 433
lines. The four-group carve-up is entirely an S2 invention layered onto S1's
undifferentiated data; S1 never scoped away from criticism roles, S2 simply
never proposed a fifth one.

The one place "judge seat" vocabulary appears with real intent is Rung S7
(`ROLE_SEAT_SEPARATION_PLAN.md:149-162`, "packages" — after S3-S6, joins a
separate preplan), naming a "cold judge seat" as an *example preset name* —
never connected in the text to a decision about S2/S3's `GROUP_ROLES`.

**Direct evidence this is a genuine gap, not a documented boundary being
reaffirmed:** `docs/proposals/CRITICISM_SYMMETRY_RESEARCH_PREPLAN.md`
(written 2026-08-08, two days *after* S2/S3 shipped) itself writes `--seat
conjecture=A --seat critic=B` as though a `critic` group already existed
(`CRITICISM_SYMMETRY_RESEARCH_PREPLAN.md:43-48`). It does not. The gap was
only discovered when the omnibus's Block A tried to actually exercise the
reverse arm on 2026-08-09 and hit the typed CLI refusal — at which point it
was logged as *"GAP, not a defect"* (§1(a) above), not as a rediscovered,
deliberate limitation.

**One adjacent, easily-conflated, genuinely different mechanism**: the
tranche `experiments/2026-08-01-change-prose-can-refute/` wanted "school-bound
JUDGE seats" — but that is the *manifest's* `CriticismPolicyV1.bindings`
school-routing mechanism (§1(c) below), not `seat_bindings.py`'s
`GROUP_ROLES`. It predates `GROUP_ROLES`'s creation by five days and is never
cited by S2/the plan as precedent for the `GROUP_ROLES` scoping question.
`docs/map/INV-frozen-surfaces.md:68-72` records its outcome: *"The Pydantic
model permits `role="judge"`; the validator forbids it. The change was
redesigned to avoid the manifest entirely rather than widen the validator."*

## 1(c). The structural reconciliation — why they wouldn't work now

**The two mechanisms have different arity, not just different names.**
`seat_bindings.py::GROUP_ROLES` is `role_name → one endpoint`
(`resolve_seat_bindings()` returns `dict[role, ProviderProfileV1]`,
`seat_bindings.py:153-186`; `preparation.py:268-297`'s `_config_for_profile`
collapses it to one endpoint dict per role). `argumentative_critic`'s actual
routing, `CriticismPolicyV1` (`run_manifest.py:522-549`), is
`school_id → (role, seat, endpoint_id)`, a tuple of `SchoolRoleBindingV1`
records — an N-to-N structure school-keyed, not role-keyed:

```python
class SchoolRoleBindingV1(BaseModel):
    school_id: str = Field(pattern=r"^school-(0|[1-9][0-9]*)$")
    role: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    seat: int = Field(ge=0, le=1_023)
    endpoint_id: str
class CriticismPolicyV1(BaseModel):
    minimum_foreign_school_coverage: int
    bindings: tuple[SchoolRoleBindingV1, ...]
    max_batch_size: int
    target_eligibility: Literal["accepted_school_artifacts"]
    authority: Literal["observe_only", "defended_trial"]
    allow_shared: bool
```
(`run_manifest.py:467-549`)

A real manifest's bindings block
(`experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-f7718a2254b048b88d50d56208ef0726/run-manifest.json`):
```json
"bindings": [
  {"endpoint_id": "provider-profile-a3e4b48c4e5354407606d9ca", "role": "argumentative_critic", "school_id": "school-0", "seat": 0},
  {"endpoint_id": "provider-profile-a3e4b48c4e5354407606d9ca", "role": "argumentative_critic", "school_id": "school-1", "seat": 0},
  {"endpoint_id": "provider-profile-a3e4b48c4e5354407606d9ca", "role": "argumentative_critic", "school_id": "school-2", "seat": 0},
  {"endpoint_id": "provider-profile-a3e4b48c4e5354407606d9ca", "role": "argumentative_critic", "school_id": "school-3", "seat": 0}
]
```
Four schools, one entry each — required even when they share one endpoint
(`allow_shared: true`). One binding *per school*, not one override for the
role.

**The frozen validator** (§1(b) already cited; the full text, load-bearing
for "why not just widen it") — `_validate_v4_criticism_policy`,
`run_manifest.py:2751,2765-2768`:
```python
if binding.role != "argumentative_critic":
    raise ValueError(
        "V4_CRITICISM_ROLE_UNSUPPORTED: bindings must name argumentative_critic"
    )
```
Widening this to permit `role="judge"` is exactly the change
`docs/map/INV-frozen-surfaces.md` surface 4 names as frozen, and exactly the
change the 2026-08-01 tranche was redesigned to avoid.

**Judge routing/gating, today**: `judge_seats()` (`llm/adapter.py:624-633`)
is a pure, ungated getter — `tuple(self.leases.get("judge", ()))`, no
diversity check. The guarantee lives in `require_cross_family_judges()`
(`adapter.py:651-668`) → `require_cross_family_judge_ensemble`
(`llm/firewall.py:341-358`):
```python
def require_cross_family_judge_ensemble(leases):
    seats = tuple(leases.get("judge", ()))
    families = {lease.route.family.strip().casefold() for lease in seats if lease.route.family.strip()}
    if len(seats) < 2 or len(families) < 2:
        raise JudgeEnsemblePolicyError()
    return seats
```
"Family-counting" = counting distinct `Route.family` tags
(`run_manifest.py:176`) across the `judge` role's seats; the gate demands
≥2 seats from ≥2 families. The same requirement is independently re-enforced
at manifest-compile time for `defended_trial` criticism
(`run_manifest.py:2799-2814`, `V4_CRITICISM_CROSS_FAMILY_JUDGES_REQUIRED`)
and, for rubric trials specifically, by `RunManifest.rubric_policy`'s
`"require_cross_family"` default (`run_manifest.py:1187,3179-3192`,
`SECOND_JUDGE_FAMILY_REQUIRED` — proved to refuse compilation outright for a
genuinely single-model run by `tests/test_run_manifest.py:586-592`).

**Four concrete, named conflicts if `argumentative_critic`/`judge` were
rerouted through `seat_bindings.py`, each with file/line:**

1. **Foreign-school coverage semantics has nothing to subtract.**
   `plan_foreign_criticism`, `workflow/criticism.py:347,357`:
   ```python
   bindings = {binding.school_id: binding for binding in policy.bindings}
   foreign_schools = sorted(set(bindings) - {target.owner_school_id})
   ```
   This computes "foreign" as `set(school_ids bound) − {this artifact's own
   school}`. A seat-bound `argumentative_critic` (one endpoint, no
   `school_id` axis at all) produces no `bindings` dict to subtract from —
   `plan_foreign_criticism` requires `manifest.criticism_policy` and raises
   `V4_CRITICISM_POLICY_REQUIRED` if it's `None` (`workflow/criticism.py:338-340`).
   There is no analogous computation a seat binding could feed.

2. **School identity is not a property seat-binding's data model can
   express.** A critic's school membership for a call is verified against
   the call's actual routed receipt (`workflow/criticism.py:206-216`,
   comparing `receipt.school_id != assignment.critic_school_id`), and
   routing itself goes through `resolve_school_role_lease`
   (`llm/firewall.py:494-507`), which enumerates exactly two school-routable
   roles — `conjecturer` and `argumentative_critic` — and sends `judge`
   straight to `SCHOOL_ROUTE_ROLE_UNSUPPORTED`. `GROUP_ROLES`'s data model
   (`dict[str, frozenset[str]]`, resolved to `dict[role_name,
   ProviderProfileV1]`) has no `school_id` field anywhere — it cannot
   express "this critic serves school X" because it carries no per-school
   axis at all, independent of any validator.

3. **Family gates cannot be satisfied by a single seat-bound override, by
   arity.** `require_cross_family_judge_ensemble` demands ≥2 seats from ≥2
   families (`firewall.py:341-358`, quoted above); a seat-bound override
   is, by construction, exactly one endpoint (`resolve_seat_bindings()`
   yields one `ProviderProfileV1` per role). `len(seats) < 2` is therefore
   always true under a role-keyed override — this is a difference of
   cardinality (scalar vs. set), not a policy that could be loosened.

4. **The validator itself forbids the reroute categorically** (already
   cited): `V4_CRITICISM_ROLE_UNSUPPORTED` at `run_manifest.py:2765-2768`
   rejects any `SchoolRoleBindingV1.role != "argumentative_critic"` — so
   even a hypothetical `GROUP_ROLES["critic"]` group feeding *into* the
   manifest's school-keyed policy (rather than replacing it) would still
   need this frozen validator to change to admit anything beyond the
   status quo's one role name.

**Answer to "why they wouldn't work now," categorically**: `seat_bindings.py`
is a `role → endpoint` scalar mechanism built for roles that need exactly
one uniform-or-per-role override (conjecture/coder/scratch). `argumentative_critic`
and `judge` are structurally set-valued in ways that scalar mechanism cannot
express — critic needs a school-keyed *N*-entry map (conflict 1, 2), judge
needs a *≥2*-entry, *≥2*-family set (conflict 3) — and one of the two
validators guarding the school-keyed side is a named frozen surface
(conflict 4). This is not a missing CLI flag; it is two genuinely different
data shapes, one of which the frozen-surfaces law forbids widening in place.

## 1(d). Liveness census — config_referee, the judge-starving claim, and the steering signals

Applying the same discipline as the `property_designer` diagnosis
(§1(a)): a dispatch site that exists but is unreachable is DEAD.

### config_referee — LIVE, with real firing evidence

`src/deepreason/referee.py` (766 lines) implements a full transactional
dispatch: `run_config_referee()` (`referee.py:455`) builds a content-blind
evidence view (`build_config_review_view`, `referee.py:128`), dispatches to
the `argumentative_critic` role under template `config_referee`, validates
the verdict (`validate_config_referee_verdict`, `referee.py:250` — fails
closed unless every cited seq is a shown observation), and durably records a
`config-critique:` Measure (`record_config_critique`, `referee.py:264`).

**Dispatch site**: `scheduler/scheduler.py:1831` calls
`self._maybe_config_referee()` unconditionally every cycle;
`_maybe_config_referee` (`scheduler.py:640-670`) gates on: (1) the policy
being present and enabled, (2) `schema_version == 6`, (3) a token meter
present, (4) `self._cycles % cadence_cycles == 0` and `!= 0`, (5)
`adapter.has_role("argumentative_critic")`.

**Opt-in gate, re-verified directly**: `v6_policy.py:353-370`,
`engaged_config_referee_policy(environ)` — *"Return the operator-opted
config-referee authority, default OFF... `DEEPREASON_CONFIG_REFEREE` names
the review cadence in scheduler cycles... Unset keeps the policy absent —
existing manifests stay byte-identical."* Confirmed executor-side: the
function returns `None` unless `DEEPREASON_CONFIG_REFEREE` is set in the
environment.

**Firing evidence, re-verified directly** (`grep -c "config-critique"
experiments/live_research_2026-07-29/referee/runs/*/log.jsonl`):
`run-d17935a4bf5ffa67c7f6e67b9a637a00/log.jsonl:0`,
`run-e542c3c1fc266943e0260c5aa8d7c107/log.jsonl:1`,
`run-e6c07aec698426a9b21d01399ba6b5b0/log.jsonl:2` — real, non-degenerate
verdicts, quoted:
```
log.jsonl:437  inputs: ["config-critique:config_mistuned","recommendation:research_allowance_step_tighten","cited:342,343,...,430",...]
log.jsonl:280  inputs: ["config-critique:config_effective","recommendation:no_change","cited:30,268,273",...]
```
**Verdict: LIVE.** Unlike `property_designer`, `config_referee` has a
dispatch site gated only by an ordinary operator opt-in, and a real firing
record with two distinct verdict kinds.

### The judge-starving machinery — DOES NOT EXIST (not dead; never built)

`grep -rn "starve" src/deepreason/` (15 hits, re-verified: zero co-occur
with "judge") returns only problem-starvation (scheduler fairness), school-
capture starvation, cache/replay starvation, and informal-docket starvation
— none about the judge role. `grep -rn "zealous"` repo-wide hits only
operator quotes in this tranche's own REQUEST.md and a document explicitly
headed **`Status: PROPOSED`** — `docs/proposals/DUAL_MODE_CONJECTURE_PREPLAN.md:1-3,9-14`,
quoting the operator's own words: *"a mechanism that submits the correct
type of form so that the critic can't become too zealous and harsh when
it's uncalled for."* This is a design proposal, never implemented.

The nearest real code, `JUDGE_ERR_MAX: float | None = None`
(`config.py:269`), does the *opposite* of throttling — a high judge error
rate *spawns more* scrutiny (`informal/audits.py:268`: `if rate >
config.JUDGE_ERR_MAX: spawn_audit_problem(...)`). And its producer,
`planted_flaw_calibration()`/`bias_probes()` (`informal/audits.py:228,273`
— the latter is what would emit `judge-self-preference:`/
`judge-verbosity-bias:` signals), has **zero call sites in production code**
— re-verified directly: `grep -rn "planted_flaw_calibration|bias_probes"
src/deepreason/` returns only the two `def` lines. Every other reference is
`tests/test_audits.py`. `grep` for `judge-error-rate:`/
`judge-self-preference:`/`judge-verbosity-bias:` across every committed
`log.jsonl` under `experiments/` and `runs/` returns zero hits.

Existing per-cycle/per-artifact caps in the same family (`ADVISORY_TRIALS_PER_CYCLE`
default 0, `config.py:401`; `ARG_CRIT_PER_CYCLE`/`RUBRIC_TRIALS_PER_ARTIFACT`,
`config.py:358-359`; `DISC_ATTEMPTS_MAX`/`DISC_COOLDOWN`, `config.py:441-442`)
are static, operator-set constants — none adapt to a measured "zeal" signal.
`llm/budget.py` has zero `judge`-specific logic (`grep` returns no hits);
`TokenMeter` is a global, role-agnostic ceiling.

**Verdict: the judge-starving machinery the operator described does not
exist in the tree.** This is a different category from `property_designer`
(bindable-but-unreachable code) — there is no code here to be unreachable.
The judge-bias-measurement scaffolding that would have to underlie any such
throttle (`planted_flaw_calibration`, `bias_probes`) *does* exist as code
but is dead in production (test-only dispatch, zero committed firings).

### Steering/config-recommendation signals — the operator's description matches `referee.py`, not `llm/budget.py`

`llm/budget.py` (180 lines, re-read in full) is pure spend accounting
(`TokenMeter.check/add/reserve/snapshot`) — no diagnosis, no recommendation,
no judge dimension. Every signal it produces *is* consumed (adapter
enforcement, `views/thesis.py:115`, `cli/main.py:2602`, and
`capabilities/audit.py:456-458`'s `TOKEN_ACCOUNTING.json`, which
`referee.py:189` reads into the config-referee's evidence pack as raw
text) — so nothing in `llm/budget.py` itself is dead, but it is not the
"checks the config, diagnoses whether adjustments worked, sends a
recommendation" function the operator described.

That description is `run_config_referee`/`record_config_critique`
(`referee.py:455,264`) — already proven LIVE above, with a real
`research_allowance_step_tighten` verdict in the record. Every other
`"recommend"` hit in `src/deepreason/` (`views/basin.py`'s embedder
calibration, `cli/main.py`'s model-profile advisory) is live but unrelated
to judge/criticism config.

### Net verdict — is R9's conditional triggered?

R9: *"If these functions are dead and the signals are dead, then the
workflow needs a makeover."* **Split result, not triggered wholesale:**

| Claim | Verdict |
|---|---|
| "an additional function... sends out a config recommendation" | **LIVE** — `config_referee`, real firings |
| "configuration machinery to starve the judge if it's becoming too zealous" | **DOES NOT EXIST** — never built, not merely dead |
| judge-bias measurement (`JUDGE_ERR_MAX`'s producers) | **DEAD** — test-only dispatch, zero committed firings |
| `llm/budget.py` signals | **LIVE but generic** — not judge-specific, not a recommendation function |

The config-recommendation half of the operator's recollection is accurate
and working. The judge-starving half is either a misremembering of
`config_referee`'s existing research-allowance/criticism-weight response
menu (`CONFIG_REFEREE_RESPONSE_MENU`, `referee.py:42-47`:
`criticism_weighted_cycle`, `research_allowance_step_tighten/widen`,
`no_change` — none of which throttle judge dispatch *frequency*, only the
research allowance and a criticism-weighting lever), or a real gap that was
proposed (`DUAL_MODE_CONJECTURE_PREPLAN.md`, PROPOSED) but never built. Per
R9's own conditional wording ("these functions" plural), the judge-starving
half alone is enough live-dead evidence to warrant the workflow-makeover
road in the decision sheet (§5.6) — scoped to that half only, not to
`config_referee`, which does not need a makeover.

## 1(e). The judge summoning-condition measurement basis — O1a's even-cycle inventory

**It exists, and it is correct.** `experiments/2026-08-08-change-grounded-overlay-o1/scripts/o1a_semantics_diff.py`
computes Tarjan SCCs over the attack graph `(nodes, att)` and filters to a
"controversy inventory" (`o1a_semantics_diff.py:140-145`):
```python
controversy = [
    {"members": sorted(comp), "size": len(comp), "edges": scc_edge_count(comp)}
    for comp in sccs
    if (len(comp) > 1 or any((a, a) in att for a in comp))
    and any(labels0[a] == "suspended" for a in comp)
]
```
An SCC of size >1 — of which a mutual attack A→B, B→A is the minimal case —
containing at least one grounded-undecided (`label0 == "suspended"`)
artifact. `docs/map/SUB-adjudication.md:75`'s own executable check confirms
`label0` on a mutual-attack pair is exactly `{'a':'suspended',
'b':'suspended'}`, and `tests/test_adjudication.py::test_mutual_attack_suspended`
(`tests/test_adjudication.py:106-123`) is the codebase's own canonical
worked example of this — asserting both artifacts land on `Status.SUSPENDED`
when their warrants target each other.

**It is read-only and never wired into any live path.** Every overlay
script opens roots through `overlay_common.py:20-23`'s `open_root`, which
"always passes `read_only=True`" (`overlay_common.py:1-7`) and walks
*committed* roots (`Path("experiments").rglob("log.jsonl")`,
`overlay_common.py:14-17`). `grep -rln "tarjan_scc\|controversy_sccs\|o1a_semantics_diff"
src/deepreason/` returns **zero hits** — nothing in the live harness/scheduler
imports this mechanism. The underlying primitives ARE live-compatible in
principle — `harness.state.att` is populated live on every registration
(`harness.py:2178-2188`, called from `harness.py:121,2048,2159`), and
`label0`/`grounded_extension` are pure, stateless functions
(`docs/map/SUB-adjudication.md:22-23`) — but porting the SCC-controversy
computation into the scheduler's live step is unstarted work, not a wiring
gap in an existing call.

**It has never once fired historically.** `experiments/2026-08-08-change-grounded-overlay-o1/REPORT.md:109-138`,
running O1a against the full 37-root committed corpus: *"zero attack-graph
SCCs contain an undecided (`label0=="suspended"`) artifact, zero artifacts
are `label0`-suspended at all... Grounded and preferred coincide on every
committed root in this corpus... every edge observed forms a simple
attacker->target chain with no cycle."* Mutual attacks / grounded-undecidable
standoffs do not appear to have occurred yet in any committed run — the
summoning condition, as measured, would have fired zero times to date.

**No existing connection to the pairwise/trial guard machinery.**
`pairwise_discriminate` (`informal/trial.py:810-993`) is mature — mandatory
order-swap, referential-integrity check, execution-supremacy deference,
observe-only/status authority modes — and is exactly the ruling machinery
the operator names. Its one production call site,
`scheduler/scheduler.py:1838-1858`, fires only for **`Status.ACCEPTED`**
rival pairs under `SpawnTrigger.DISCRIMINATION` — the opposite status from
the grounded-undecidable `Status.SUSPENDED` pairs the operator's summoning
condition targets. No code path connects "two artifacts are mutually
suspended" to "run a pairwise trial between them" today; this is new
integration work, not a repurposing of an existing wire.

**No existing rate/budget throttle for judge summoning.** The closest
existing shapes — `ADVISORY_TRIALS_PER_CYCLE` (per-cycle cap),
`DISC_ATTEMPTS_MAX`/`DISC_COOLDOWN` (attempt-exhaustion + cooldown pair) —
are the right *pattern* but scoped to different triggers (advisory rubric
trials; accepted-rival discrimination). Nothing throttles judge activity
keyed to a suspended/mutual-attack condition, because that condition itself
has no live consumer yet.

## 1(f). School identity — minting, binding, and the consequence of school-as-seat

**A school is lineage, not a model assignment.** `docs/map/CON-schools.md:12-14`:
*"A school is a persistent conditioning regime for conjecture: a named
stance drawn from a fixed library, plus the lineage of artifacts whose
provenance carries that school id."* Two authorities are kept explicitly
separate (`CON-schools.md:23-26`): *"The **stance** is semantic prompt
material and grants nothing — no routing, no status, no budget. The
**binding** is manifest-owned routing that no prompt and no model response
can move."*

**Minting**: `init_schools`, `src/deepreason/capture/schools.py:68-82` —
`school_id = f"school-{i}"` for `i in range(config.N_SCHOOLS)`
(`config.py:274`, default `N_SCHOOLS=4`). A pure counter, zero randomness,
zero operator input beyond the count; each mint is a `Refl`-rule artifact.
The module's import set (`capture/schools.py`) excludes the manifest,
firewall, and `Config`'s own type entirely (`docs/map/SEAM-manifest-x-schools.md:170-181`)
— **minting has no concept of a route, endpoint, or model.**

**Membership**: assigned once, at conjecture time —
`Provenance(school=school["id"], ...)` (`rules/conj.py:2062-2072`), and
immutable thereafter (`Provenance` is a `FrozenRecord`,
`ontology/artifact.py:63`). Which model *executed* the call is a wholly
separate axis, cross-checked to name the same school id
(`rules/conj.py:697-701`) but never required to be a distinct model per
school — the shipped default already puts 4 different school identities on
1 shared criticism endpoint (`allow_shared=True`, `v6_policy.py:198-226`).

**Conjecture-side school→model binding exists as a mechanism but is
dormant everywhere shipped**: `SchoolExecutionPolicyV1(mode="route_bound",
...)` (`run_manifest.py:486-495`) is real and exercised by
`resolve_school_role_lease`'s conjecturer branch (`llm/firewall.py:494-495`),
but *"Every `SchoolExecutionPolicyV1` constructed anywhere in `src/` is
`conditioning_only`... So schools' routing authority is real, exercised
offline, and dormant in every shipped configuration"*
(`docs/map/SEAM-manifest-x-schools.md:219-225`). Criticism-side binding is
live and always populated (the shared-seat default above).

**Judge is categorically excluded from school routing, both directions**:
`resolve_school_role_lease` refuses `role="judge"` with
`SCHOOL_ROUTE_ROLE_UNSUPPORTED` (`firewall.py:503-507`), and the manifest
validators independently forbid any binding whose role isn't exactly
`conjecturer` or `argumentative_critic` (`V4_SCHOOL_ROLE_UNSUPPORTED`/
`V4_CRITICISM_ROLE_UNSUPPORTED`).

**The two consequences of school-as-seat, traced precisely and priced (per
C6, "never absorbed silently"):**

*Consequence A — "foreign" itself: unaffected.* `foreign_schools =
sorted(set(bindings) - {target.owner_school_id})`
(`workflow/criticism.py:357`) is a pure `school_id` string-set difference,
structurally blind to `endpoint_id`/model identity (already proven
inert by the shipped shared-seat default). Binding distinct schools to
distinct models changes `binding.endpoint_id` per row but never the key
set `foreign_schools` is computed over. **This is genuinely inert, not
hedged** — confirmed by the map's own pinned invariant,
`docs/map/CON-schools.md:197-200`: *"Foreign-criticism coverage is counted
by critic SCHOOL, never by endpoint or model. Two schools sharing one model
still count as two schools of coverage."*

*Consequence B — a different, adjacent mechanism silently degrades.*
`is_single_model_run`/`is_single_family_run` (`llm/firewall.py:299-338`)
pool leases **across every role in the run**, not scoped to schools:
```python
def is_single_family_run(leases):
    return len(_lease_families(leases)) == 1   # firewall.py:308, folds over ALL roles
```
This predicate gates the cheaper cross-school substitute in the argument
trial (`informal/trial.py:614-629`):
```python
if adapter.is_single_model():
    if len(adapter.leases.get("judge", ())) < 2: return _decline(..., "single-judge-seat", ...)
    ...
else:
    adapter.require_cross_family_judges()
```
Today, shipped public runs are single-endpoint across every role
(`v6_policy.py:203-204`), so `is_single_model()` is True and the cheap
cross-school substitute governs. The moment a school-seat opt-in gives
distinct schools distinct models (for conjecture or criticism), those
routes land in `adapter.leases[role]` for *whichever* role was touched, and
because the single-model/single-family predicate pools all roles
indiscriminately, the run's global determination flips to False — **even
though the `judge` role's own seats were never touched.** That flip routes
the argument trial into `require_cross_family_judges()`, which then fails
(`JudgeEnsemblePolicyError`) if `judge` still has only one seat/family — a
trial that used to succeed via the cross-school substitute now declines on a
gate it was never asked to satisfy. This is real, silent, and priced here
per C6: **a school-as-seat opt-in that adds route diversity anywhere in the
run's role table can unintentionally revoke the argument trial's
cross-school substitute eligibility for a completely untouched role.**

---

# HALF 2 — THE OPT-IN REDESIGN

Design law from C3/CLAUDE.md's frozen-surfaces law, applied uniformly to
every opt-in below: **the opt-in itself is a new `Config` field (never a new
manifest field/vocabulary — `docs/map/INV-frozen-surfaces.md:94-100`,
`docs/map/SEAM-adjudication-x-authority.md:118-121`), its *value* gets
projected into the existing frozen manifest structure it already controls at
mint time (the `ENGAGED_CRITICISM_AUTHORITY → CriticismPolicyV1.authority`
precedent, `preparation.py:395`), and any new top-level `Config` field
requires an explicit unconditional `.pop(...)` line in
`_versioned_source_config_data` (`run_manifest.py`) for every schema
version, per the trap already paid for at
`docs/map/INV-frozen-surfaces.md:185-208`.** Default = today's actual
behavior, byte-identical, in every case below (verified per opt-in). R-g
(formalism/kind is never an obligation and never a penalty) is stated once
here and applies to all four: none of these opt-ins may weight admission,
rank, or acceptance on whether a conjecture or criticism is formal or
informal — they gate *whether a mechanism runs at all*, never *what a
mechanism is allowed to accept*.

## 2(a). Adjudication opt-in

**Today's actual default, measured**: `Config()`'s bare default is
`ARGUMENTATIVE_AUTHORITY == "observe_only"` (`config.py:380-382`) and all
three text-authority surface knobs (`TEXT_RUBRIC_AUTHORITY`,
`PAIRWISE_AUTHORITY`, `INFRASTRUCTURE_REVIEW_AUTHORITY`) default
`observe_only` too — `docs/map/CON-authority.md:33-36`'s own checked claim:
*"everything defaults to `observe_only`... a run that configures nothing
spends no judge tokens on status-bearing text adjudication."*
`ENGAGED_CRITICISM_AUTHORITY` (`config.py:393`) likewise defaults
`observe_only`, and its own tranche
(`experiments/2026-08-03-change-rung2-engaged-criticism-switch/`)
**preserved** a pre-existing hard-coded `authority="observe_only"` literal
in `v6_policy.py` — it did not newly establish the default.
`observe_only` operationally: *"records scrutiny and mints nothing — a
critic-role artifact with no warrants and a `["scrutiny", target, critic]`
Measure. The target's `Status` and the attack set are untouched"*
(`CON-authority.md:168-171`). **The task issuer's claim "already effectively
opt-in via observe_only" is accurate**, with one measured exception: two
argumentative mint sites bypass authority entirely —
`imports.py::register_epistemic_import_failure` and
`rules/experiment.py::relevance_trial` — *"consult neither authority nor a
supremacy guard"* (`docs/map/SEAM-adjudication-x-authority.md:60,89-92,157-161`).
Status-changing criticism is NOT opt-in on those two paths today because
there is no gate at all, not because their gate defaults open.

**Placement, per the frozen-surfaces law**: a new explicit opt-in flag goes
on `Config`, consulted at mint sites (`rules/crit.py`, `informal/trial.py`),
never on the manifest — this is the codebase's own repeated precedent
(`ARGUMENTATIVE_AUTHORITY`, `ENGAGED_CRITICISM_AUTHORITY`) and the exact
guidance in `docs/map/SEAM-adjudication-x-authority.md:118-141`: *"A new
authority mode goes on `Config` and is consulted at a mint site. Never on
the manifest... Never make the label computation depend on anything outside
the record."* Rung 7's own SPEC (`experiments/2026-08-04-change-rung7-authority-as-declared-policy/SPEC.md:383-394`)
explicitly priced and rejected putting authority declarations into the
manifest schema (frozen surfaces 4 and 5). **Reading of C3's "mint-time
frozen into the manifest"**: this is the `Config`-knob-value-projected-into-
the-compiled-`CriticismPolicyV1.authority`-field pattern already proven by
`ENGAGED_CRITICISM_AUTHORITY`, not a literal new manifest field/vocabulary —
the SPEC design below follows that reading; if the operator meant the
literal reading, that reopens rung-7's already-rejected Option B and should
be flagged back explicitly (decision sheet §5.1).

**Design (Half 1(f)'s findings folded in — the adjudication opt-in must
also gate the two ungated mint sites, or "opt-in" remains false on those two
paths)**: one Config field, `ADJUDICATION_STATUS_AUTHORITY_ENABLED: bool =
False`, defaulting False (byte-identical to today's `observe_only`-everywhere
behavior). When False: the existing `observe_only`-default landscape holds
exactly as today, AND the two currently-ungated mint sites
(`imports.py::register_epistemic_import_failure`,
`rules/experiment.py::relevance_trial`) additionally consult it, defaulting
closed — closing the one place status-changing criticism is not actually
opt-in today. When True: does not itself flip any of the six existing
authority knobs to a trial mode — it only *permits* an operator to set
`ARGUMENTATIVE_AUTHORITY`/`ENGAGED_CRITICISM_AUTHORITY`/etc. away from
`observe_only`; those knobs' own defaults are unchanged. This makes "opt
in" mean what it says (a gate that must be explicitly opened before
status-changing criticism becomes reachable at all, including on the two
sites that bypass it today) without collapsing the six-knob vocabulary
`docs/map/CON-authority.md` already documents.

**Solo-law compliance (R1, C3's "no configuration may strand solo runs")**:
the existing `single_family_trial` value of `ARGUMENTATIVE_AUTHORITY`
(`config.py:371-377`) is precisely the accommodation the solo law requires
— school-carried independence in place of unobtainable cross-family
judging, gated on `is_single_family_run`. The new opt-in flag must not gate
this value away; a solo run that opts into adjudication retains the
`single_family_trial` road. The same-day sibling tranche
`experiments/2026-08-09-change-judge-evidence-review/REQUEST.md:52-57`
independently names concrete judge-free fallbacks (program/predicate
commitment refutation, counterexample execution, non-judge trial-guard
program checks) that remain reachable regardless of this flag's state —
these are not touched by this opt-in and remain the judge-free floor.

## 2(b). Judge seats opt-in — targeting the operator's own definition

**Today's actual default, measured**: judge participation is *de facto*
closed on the common path but as an emergent consequence of three
independently-defaulted-closed gates, not one switch: (1) role wiring is
open by default (`has_role("judge")` true whenever setup broadcasts one
profile uniformly); (2) a rubric-eval criterion must exist at all —
`WorkloadProblem.criteria: tuple[Commitment, ...] = ()` defaults empty
(`workloads/text.py:37`); (3) authority mode defaults `observe_only`/
`ADVISORY_TRIALS_PER_CYCLE=0` (`config.py:401`). For `workload_profile !=
"text"` (code/formal/website), `trial_authority_for` forces
`TrialAuthority.STATUS` unconditionally (`authority.py:101-102`) — **there
is no operator-facing suppression for judges once a rubric criterion exists
in a non-text workload.** There is no single `Config` field today named
anything like `ENABLE_JUDGES`.

**The operator's design target, restated as the spec's acceptance bar
(R6)**: dormant by default; summoned only for grounded-undecidable standoffs
(mutual/symmetric attack structures, measured by the O1a-style
even-cycle/controversy inventory); ruling through the existing
pairwise/trial-guard machinery, never as an open-ended prosecutor;
starvable via an explicit throttle. Half 1(e) establishes precisely what of
this exists and what must be built:

| Piece | Status | What's needed |
|---|---|---|
| Even-cycle/controversy detection logic | EXISTS, proven correct (`o1a_semantics_diff.py`) | Port from read-only offline script into a live, in-cycle check over `harness.state.att` — new integration work, not a rewire |
| Connection: suspended pair → pairwise trial | DOES NOT EXIST | New wiring: `pairwise_discriminate` today only fires for `Status.ACCEPTED` rivals under `SpawnTrigger.DISCRIMINATION`; a new trigger path for `Status.SUSPENDED` mutual-attack pairs is required |
| Ruling machinery itself | EXISTS, mature, reusable as-is | `pairwise_discriminate` (`informal/trial.py:810-993`) — order-swap, referential integrity, execution supremacy already built |
| Starvation throttle | DOES NOT EXIST for judge-summoning specifically | New Config fields modeled on the existing `ADVISORY_TRIALS_PER_CYCLE` (rate cap) + `DISC_ATTEMPTS_MAX`/`DISC_COOLDOWN` (attempt-exhaustion/cooldown) pattern |

**Design**: one Config field, `JUDGE_SEATS_ENABLED: bool = False`,
consulted at every current judge-dispatch gate (`has_role("judge")` checks
at `scheduler.py:1116-1117,2167-2168`, the property-step fail-closed check,
and the rubric-authority forced-STATUS path for non-text workloads) so that
**no judge role dispatches at all — zero tokens spent — unless this is
True**, closing the non-text-workload gap Half 1's measurement found. This
flag governs whether judges may fire *at all*; it does not by itself
implement the summoning-condition/pairwise-standoff redesign (that is new
scheduler integration work, scoped as its own follow-up per the decision
sheet §5.2 — this window specs the opt-in surface and the throttle fields,
not the live even-cycle wiring, per C4's no-code-this-window constraint).
Two new throttle fields, defaulting to preserve exactly zero judge activity
until both `JUDGE_SEATS_ENABLED` and a nonzero rate are set:
`JUDGE_SUMMONS_PER_CYCLE: int = 0` (per-cycle cap, modeled on
`ADVISORY_TRIALS_PER_CYCLE`) and `JUDGE_SUMMONS_COOLDOWN: int = 4` (modeled
on `DISC_COOLDOWN`, preventing one unresolved standoff from monopolizing
judge budget).

**Reconciliation with the cross-family gate (solo law)**: `JUDGE_SEATS_ENABLED=True`
on a solo run (single model family) cannot, by itself, satisfy
`require_cross_family_judges()`/`rubric_policy="require_cross_family"` —
confirmed to refuse manifest compilation outright
(`tests/test_run_manifest.py:586-592`, `SECOND_JUDGE_FAMILY_REQUIRED`). The
opt-in must not silently bypass this; it must either route through
`school_judge_bindings`/cross-school substitution (`adapter.py:645-649`,
requiring explicit school-judge-binding configuration) or surface the
refusal clearly at the same layer, with the same typed code, rather than
let the operator discover the contradiction only at compile time. This is
the solo-compatible road the standing law requires; it is not automatic —
opting into judges on a genuinely single-family solo run and expecting
diversity is a contradiction the system correctly refuses, and the opt-in
design must make that refusal legible, not silent.

**Judge-audit evidence surfaced at opt-in (judge-suspicion law, R2)**: per
the operator's standing law, the opt-in must present the judge-evidence-
review tranche's findings, not just a bare toggle
(`experiments/2026-08-09-change-judge-evidence-review/REVIEW.md`, already
consulted per the law's own requirement):
- The CRITIC stage is measured content-blind: objection rate 1.0 on both
  clean and corrupted content across three independent live studies
  (`REVIEW.md` §2.5).
- The JUDGE-gated conviction stage, under the harness's actual strict
  default configuration (cross-family, unanimous), has measured sensitivity
  of only **11.9%** against 42 planted, ground-truth defects, at **0%**
  false conviction — *"it almost never convicts"* (`REVIEW.md` §2.5). This
  under-catches; it does not over-prosecute, under the strict default.
- Loosening to same-family unanimous voting raises false conviction of
  clean work to **47.5%**; either-suffices to **60%** (`REVIEW.md` §2.4) —
  a quantified risk of any configuration that also relaxes the
  cross-family/unanimity guarantee.
- Self-preference/verbosity bias — the specific "discernable
  discrimination" the operator's law names — has **zero live measurements**
  in the committed record (`REVIEW.md` §2.2, §7c, §8.3); this remains an
  open evidentiary gap the opt-in cannot close by citing evidence, only by
  disclosing its absence.
- `observe_only` (today's default) already delivers a judge-free,
  solo-compatible road at zero cost (`REVIEW.md` §8.1) — the opt-in should
  frame turning judges on as *opting out of* that already-proven-safe
  floor, with the above numbers attached, not as merely adding a feature.

## 2(c). Legacy criticism paths opt-in

**Enumeration (from D1's CENSUS.md M6-M9, confirmed present under exactly
that numbering — `experiments/2026-08-08-change-pipeline-census-d1/CENSUS.md:320-536`
— and the authority-mode map, `docs/map/CON-authority.md`)**: `grep -i
"legacy"` across `rules/crit.py` and `informal/trial.py` returns **zero
hits** — neither file itself labels any path "legacy." The census and the
authority map describe a system of parallel, simultaneously-live,
config-selected mechanisms, not a legacy-being-phased-out structure.

| Path | file:line | Legacy or current | Evidence |
|---|---|---|---|
| `crit_program` (DEMONSTRATIVE) | `rules/crit.py:895`, called unconditionally `scheduler.py:1089` | CURRENT, always-on | No config gate; M6 |
| `crit_argumentative`/`_batch` | `rules/crit.py:1175,1336` | CURRENT, always-on | Dispatched every eligible cycle, no kind check; M6 |
| `observe_only` authority mode | `rules/crit.py:732`, gate `:1305-1312` | CURRENT, is the default | `config.py:380-401`; M7 |
| `trial_required`/`single_family_trial` | `informal/trial.py:553` | CURRENT, opt-in (not default) | Same 2026-08-01 tranche that built "prose can refute" — actively maintained |
| Manifest `CriticismPolicyV1.authority` (`observe_only`/`defended_trial`) | `run_manifest.py:522-536` | CURRENT — parallel vocabulary, not a supersession of Config's | `docs/map/CON-authority.md:106-112`: "TWO vocabularies... kept apart" |
| `ENGAGED_CRITICISM_AUTHORITY` | `config.py:393` | CURRENT — made a prior hard-coded call configurable | M7 |
| Pre-switch hard-coded `authority="observe_only"` literal in `v6_policy.py` | superseded, no longer present | **LEGACY — the one explicit, repo-documented supersession found** | `experiments/2026-08-03-change-rung2-engaged-criticism-switch/REQUEST.md:12,36,60` |
| `calibrated_status`/`TextAuthorityMode.CALIBRATED_STATUS` | `authority.py:16-20,104-130` | Present but functionally inert (not legacy, not current — unfinished) | `authority.py:113-130`: `calibration_receipt_is_verified` always returns `False` |
| Rubric trial vs. precomputed-case trial | `informal/trial.py:227,553` | Both CURRENT, structurally distinct, both live | Different `AuthoritySurface` gates |
| `_standing_recrit_pool` kind-conditional ordering | `scheduler.py:1150-1181` | CURRENT, gated by `RECRIT_STANDING` (default True) | M6, R-g audit finding |

**Verdict**: exactly one mechanism in this census is documented anywhere as
an explicit legacy-superseded-by-current pair — the pre-Rung-2 hard-coded
`v6_policy.py` literal, already fully replaced by the `ENGAGED_CRITICISM_AUTHORITY`
Config knob; there is no live code path left to opt into or out of for that
one, it is simply gone. Everything else is parallel, config-selected, and
already independently gated (§2(a)'s six knobs). **This means "legacy
criticism paths: opt in" has no additional distinct surface to design beyond
what 2(a)'s adjudication opt-in and the existing six authority knobs already
cover** — the census found no dormant legacy code requiring its own new
flag. The one candidate worth naming explicitly as a design option is
`calibrated_status` (present, selectable, but inert) — whether to build its
missing verifier is a decision-sheet fork (§5.3), not something this
request's evidence shows is "legacy" in the sense of needing an opt-out.

## 2(d). Schools opt-in (Amendment 1, R5)

**Today's actual default**: no `--seat school-N=<profile>` surface exists.
Conjecture-side school routing (`SchoolExecutionPolicyV1(mode="route_bound")`)
exists as a mechanism but is `conditioning_only` (its only shipped value)
everywhere in `src/` (`docs/map/SEAM-manifest-x-schools.md:219-225`).
Criticism-side school routing is always populated, sharing one endpoint
across all schools by default (`v6_policy.py:198-226`, `allow_shared=True`).

**Design, informed by Half 1(f)'s two-consequence trace**: a Config-level
opt-in, `SCHOOL_SEATS_ENABLED: bool = False`, gating whether
`SchoolExecutionPolicyV1.mode` may be set to `route_bound` (conjecture side)
and/or whether `CriticismPolicyV1.bindings` may carry per-school distinct
`endpoint_id`s (criticism side) at manifest-compile time — both already-
existing schema capabilities, currently reachable only via a direct
`compile_run_manifest` argument with no CLI/setup-time surface
(`docs/map/SEAM-manifest-x-schools.md:219-225`: *"only an operator-supplied
`control_plane_policy` argument... can produce a route-bound run"*). This
opt-in's job is to give that existing-but-unreachable schema capability an
operator-facing `--seat school-N=<profile>` surface (parallel in shape to
`seat_bindings.py`'s existing `--seat GROUP=PATH`), not to invent new
manifest fields.

**Priced explicitly, per C6 (must not be silently absorbed)**: Consequence
A (foreign-school coverage) is unaffected — proven inert by the map's own
pinned invariant. **Consequence B is a real cost this opt-in must document
and, ideally, guard against**: enabling school seats and giving even one
pair of schools distinct models will flip `is_single_model_run`/
`is_single_family_run` (`llm/firewall.py:299-338`) to False for the *whole
run*, because those predicates pool leases across every role, not just
schools. This can silently revoke the argument trial's cross-school
substitute for the **unrelated** `judge` role and cause
`require_cross_family_judges()` to raise where it previously did not. The
opt-in's SPEC (a later phase, not this window) must either (i) document
this as an accepted, disclosed cross-role consequence at opt-in time, with
the exact mechanism named to the operator, or (ii) scope the check more
precisely — e.g. a role-scoped variant of `is_single_model_run` that
excludes the seat-bound role from its pool — as a design option, priced in
the decision sheet (§5.4), not resolved here.

**Solo-law/qualification cost note**: moving a school to a different seat
is a qualification-battery cache miss and a full re-run of the qualification
battery for the new subject, per `docs/map/SEAM-manifest-x-schools.md:137-144`:
*"Three schools on three seats is eight pairs... Moving a school to a
different seat is therefore not a routing tweak — it is a cache miss and a
full battery."* This is a real, disclosed cost of the opt-in, not a defect;
it should be surfaced in the opt-in's operator-facing help text.

---

# FROZEN-SURFACE FORECAST (from scratch, authorizing nothing)

Per C4/window discipline, this is a forecast only — no code changes this
window, and nothing here authorizes touching any of these surfaces. Every
opt-in designed above is deliberately shaped to avoid frozen-surface contact
where possible; where contact is unavoidable, it is named here so a future
implementing tranche scopes it correctly from the start (map-preflight
discipline, `docs/map/INV-frozen-surfaces.md`).

- **`run_manifest.py` adjacency (surface 4, schemas AND validators)** — the
  task issuer's own expectation, confirmed real: `_versioned_source_config_data`
  needs an explicit unconditional `.pop(...)` line for every new top-level
  `Config` field this SPEC proposes (`ADJUDICATION_STATUS_AUTHORITY_ENABLED`,
  `JUDGE_SEATS_ENABLED`, `JUDGE_SUMMONS_PER_CYCLE`, `JUDGE_SUMMONS_COOLDOWN`,
  `SCHOOL_SEATS_ENABLED`), per every schema version, or the
  `ENGAGED_CRITICISM_AUTHORITY` trap
  (`docs/map/INV-frozen-surfaces.md:185-208`) recurs. This is Config-field
  adjacency to the manifest's canonical-hash machinery, not a schema/validator
  change itself — the fields stay on `Config`, never become manifest fields.
- **`V4_CRITICISM_ROLE_UNSUPPORTED` validator (surface 4)** — named, not
  touched. §1(c)/§2(c) show no opt-in design above requires widening it;
  if a future implementation ever wants `argumentative_critic`/`judge`
  routed through anything resembling `seat_bindings.py`'s mechanism, this
  validator is the wall it hits, and it is frozen.
- **`is_single_model_run`/`is_single_family_run` (`llm/firewall.py`)** —
  not itself a named frozen surface today, but §1(f)/§2(d)'s Consequence B
  makes it a de facto invariant every future run's argument-trial behavior
  depends on; a role-scoping fix here (decision-sheet option, §5.4) would
  need the same "fix readers, not the record" discipline the frozen-surfaces
  law states generally, even though this specific function isn't on the
  enumerated list of five.
- **Qualification subject digest (surface 5)** — any new `Config` field
  that participates in `qualification_subject_payload` widens what gets
  requalified; per `docs/map/INV-frozen-surfaces.md:84-90`, this SPEC's new
  fields must NOT enter that payload (they gate dispatch, not provider
  identity), and this should be an explicit acceptance check in the later
  CHECKLIST.md.
- **No opt-in in this SPEC requires touching**: `capabilities/state.py`,
  `harness.py` event application, `invariants.py`/replay-validation formats,
  or `route_fingerprint` — none of the four opt-ins change what is logged,
  how state is materialized, or how a root replays; they only gate whether
  certain mint sites/dispatch sites run at all.

---

# R-g KIND-BLINDNESS STATEMENT

Stated once, binding across all four opt-in designs (§2a-d): none of
`ADJUDICATION_STATUS_AUTHORITY_ENABLED`, `JUDGE_SEATS_ENABLED`,
`JUDGE_SUMMONS_PER_CYCLE`/`_COOLDOWN`, or `SCHOOL_SEATS_ENABLED` reads or
branches on whether a conjecture or criticism artifact is formal or
informal. Each gates *whether a class of mechanism runs at all* for the
whole run — a boolean/count on `Config`, consulted before dispatch — never
*what content a mechanism is willing to accept, rank, or admit* once it
runs. This satisfies the operator's standing law verbatim
(CLAUDE.md: *"nothing may force a conjecture to be formal, and nothing may
penalize a conjecture for being informal — not admission, not rank, not
criticism exposure, not acceptance"*): turning these opt-ins on or off
changes how much scrutiny exists in the run, uniformly across every
artifact regardless of kind, never which kind survives it.

---

# DECISION SHEET

Per Amendment 2 (C11): every fork below is priced as roads with a
recommendation; none is taken here. This window ends at SPEC.md, not at a
chosen implementation.

**RESOLVED by Amendment 5** (operator, "every decision-sheet recommendation
is approved as written"): every road below is now APPROVED at the
recommendation, annotated inline. Additionally, R13/Road E (the pre-school
criticism circuit's v6 transaction contract) is APPROVED and folded into
§2(c) as its concrete surface, to be built FIRST per the operator's
explicit ordering requirement. The whole tranche is scoped STATIC/mint-time
-frozen only — Amendment 5's benching directive defers every dynamic,
mid-run, signal-consuming mechanism this document named as future work
(§5.2's live standoff-summons wiring, §5.6's M1-M3 signal-adaptive
throttle, R12's Road C where it implied dynamic behavior) to a later
tranche, per `docs/proposals/GATES_AND_PACKAGES_PREPLAN.md` (merged to
main at `b19c5661b`; Stage 1 = what this tranche builds, Stage 2 = dynamic
flips, explicitly BENCHED there). Signal abstraction survives in STATIC
form only (R15): a uniform typed read surface over the liveness census's
confirmed-live signals, consumable at run boundaries, never mid-run.

## 5.1 — Reading of C3's "mint-time frozen into the manifest"

- **Road A (recommended)**: Config-knob-value-projected-into-existing-
  manifest-field, per the `ENGAGED_CRITICISM_AUTHORITY` precedent. Cost:
  none beyond the standard `_versioned_source_config_data` pop-line
  discipline. Consistent with rung-7's already-rejected Option B and every
  frozen-surfaces citation in this document.
- **Road B**: literal new manifest schema fields/vocabulary for these
  opt-ins. Cost: reopens rung-7's rejected Option B, touches frozen
  surfaces 4 and 5, invalidates cached qualification subjects for every
  run using a new field. No finding in this SPEC supports this road; it
  is priced only because C3's wording could be read this way.
- **Recommendation**: Road A. If the operator meant Road B, that is new
  information this SPEC does not currently have evidence for, and should
  be said explicitly rather than assumed.

## 5.2 — Judge-summons live wiring scope

- **Road A (recommended, smaller)**: this tranche (a future implementing
  one) delivers only the opt-in flags and throttle fields (§2b's table,
  rows 3-4) plus gating existing judge-dispatch sites on
  `JUDGE_SEATS_ENABLED`. The even-cycle-summons wiring (row 1-2) is its
  own follow-up program (see §5.6's rung sketch) — porting a read-only
  offline script into a live per-cycle check, then connecting
  `Status.SUSPENDED` mutual pairs to `pairwise_discriminate`, is
  substantial new scheduler integration, not a flag.
- **Road B (larger, one tranche)**: deliver the opt-in AND the live
  summoning wiring together. Cost: unknown diff size until the scheduler
  integration is actually scoped (no estimate exists yet — Half 1(e)
  found the pieces are real but disconnected); risk of exceeding a diff
  budget mid-tranche (though Amendment 2/C10 pre-authorizes continuing
  through that rather than stopping).
- **Recommendation**: Road A. The opt-in surface is independently useful
  (closes the always-on judge-dispatch gap Half 1(b) found for non-text
  workloads) even before the summoning redesign exists; shipping it first
  lets the operator immediately close that gap without waiting on the
  larger integration.

## 5.3 — `calibrated_status` (the one genuinely inert authority mode)

- **Road A**: leave it inert; out of scope for this tranche (it is not a
  "legacy" path per §2(c)'s finding, and the operator did not name it).
- **Road B**: build the missing `calibration_receipt_is_verified` verifier
  as part of the legacy-criticism-paths opt-in work, making
  `calibrated_status` a fifth real mode.
- **Recommendation**: Road A. Nothing in REQUEST.md names this mode; it
  surfaced only as a byproduct of the census. Building a verifier for an
  unrequested mode is exactly the kind of scope creep CLAUDE.md's "don't
  add features beyond what the task requires" law warns against.

## 5.4 — Consequence B's fix (schools flipping the run-wide single-model predicate)

- **Road A (recommended)**: disclose-only. The schools opt-in's help text
  and design doc name the exact mechanism (§2(d)) so an operator who
  enables school seats knows a `judge`-role trial may newly require
  cross-family judges. No code change to `firewall.py`.
- **Road B**: scope `is_single_model_run`/`is_single_family_run` (or add
  role-scoped variants) so a school-seat-only diversity change does not
  affect roles it never touched. Cost: touches a function multiple other
  gates depend on (`adapter.is_single_model()`, `_select_judge_ensemble`),
  needs careful regression coverage across every existing caller listed in
  Half 1(f); not a frozen surface by name but load-bearing enough to
  deserve the same care.
- **Recommendation**: Road A for the opt-in's initial ship; Road B as a
  named follow-up if disclosure proves insufficient in practice (i.e. if
  operators are repeatedly surprised by the interaction).

## 5.5 — Should a critic/judge SEAT vocabulary exist at all, given Half 1's findings?

This is the decision sheet's most consequential fork, directly answering
the task issuer's own framing question.

- **Road A — extend `seat_bindings.py`'s `GROUP_ROLES` vocabulary** (add a
  `critic`/`judge` group). **Not recommended.** Half 1(c) shows this
  mechanism is structurally the wrong shape: it is scalar
  (`role → one endpoint`) where criticism needs an N-entry school-keyed map
  and judges need a ≥2-seat, ≥2-family set. Extending `GROUP_ROLES` would
  either (i) only let an operator override the criticism policy's *shared*
  endpoint uniformly (no school differentiation — a real capability
  regression versus what `CriticismPolicyV1.bindings` already supports
  today), or (ii) require inventing a parallel N-ary binding shape inside
  `seat_bindings.py` that duplicates `CriticismPolicyV1` in a second place
  — two sources of truth for the same routing question.
- **Road B — school/family routing subsumes it; give the EXISTING
  manifest-owned mechanisms (`CriticismPolicyV1.bindings`,
  `SchoolExecutionPolicyV1`, the judge family gate) an operator-facing CLI
  surface, without inventing a new "seat" vocabulary.** **Recommended.**
  This is exactly what §2(d)'s schools opt-in design already does — it
  gives `SchoolExecutionPolicyV1(mode="route_bound")` and per-school
  `CriticismPolicyV1.bindings` diversity a `--seat school-N=<profile>`-style
  CLI surface, reusing the manifest's own school-keyed shape instead of
  bolting a role-keyed shape onto it. For judges specifically, Road B means
  the judge-seats opt-in (§2b) is a dispatch gate + throttle, not a routing
  mechanism — judge routing/diversity stays exactly where it already
  correctly lives (`RunManifest.roles["judge"]`, `require_cross_family_judges`),
  because that mechanism already does the ≥2-seat/≥2-family job correctly
  and `seat_bindings.py`'s shape cannot.
- **Recommendation**: Road B, categorically. Half 1's evidence — the S6
  dead-seat precedent (bindable ≠ effective), the omnibus's own
  anticipation that a hypothetical `critic` group would need the same
  liveness scrutiny `coder` failed, and the four concrete arity conflicts
  in §1(c) — all point the same direction: `seat_bindings.py`'s vocabulary
  was built for uniform-or-per-role scalar overrides and should stay that
  size. The right lever for critic/judge/school opt-ins is exposing what
  the manifest's own school/family machinery already does correctly, not
  widening a mechanism proven the wrong shape for two of the three roles
  under discussion.

## 5.6 — The workflow-makeover road (R9's conditional, triggered on the judge-starving half only)

Per Half 1(d)'s split verdict, only the judge-bias-measurement /
judge-starving half of R9's conditional is triggered — `config_referee`
itself needs no makeover. Scoped here as a priced follow-up program, not
designed in full (C4):

- **Rung M1 — wire the dead measurement code.** `planted_flaw_calibration`/
  `bias_probes` (`informal/audits.py:228,273`) exist, are presumably
  tested in isolation (`tests/test_audits.py`), but have zero production
  call sites. First rung: give them a real dispatch site (e.g. as part of
  the existing `_audit_step` sweep, `scheduler.py:2162-2185`, which already
  runs `paraphrase_invariance_audit` on the same cadence) so
  `judge-self-preference:`/`judge-verbosity-bias:` signals start actually
  being produced on live runs — directly closing the "zero live
  measurements" gap the judge-evidence-review tranche flagged
  (`REVIEW.md` §2.2, §7c, §8.3).
- **Rung M2 — build the actual throttle.** Once M1 produces real
  self-preference/verbosity signals, a genuine "starve the judge if it's
  becoming too zealous" mechanism can be built that *reads* those signals
  and adaptively tightens `JUDGE_SUMMONS_PER_CYCLE` (§2b) — this is the
  piece that does not exist today and cannot be built correctly before M1
  gives it real data to act on.
- **Rung M3 — connect to `config_referee`'s response menu**, so the
  referee's `criticism_weighted_cycle` lever (already live,
  `referee.py:42-47`) can also express "reduce judge-summons rate" as a
  menu option, giving the operator's two named mechanisms (config
  recommendation, judge starvation) one coherent connected surface instead
  of two independently-designed ones.
- **Pricing**: M1 is small (wire two already-written functions into an
  existing sweep). M2 is the substantial one — designing a signal-to-throttle
  adaptation policy is real design work, not a flag. M3 is small once M1/M2
  exist. **This is out of scope for the current tranche's implementation**
  (this SPEC's own §2b already ships static throttle fields, not adaptive
  ones) and should be captured as its own change request when the operator
  wants it, not folded into this tranche's CHECKLIST.md.

---

# REQUIREMENT RECONCILIATION

| Req | Satisfied by |
|---|---|
| R1 (adjudication opt-in) | §2(a) |
| R2 (judge seats opt-in) | §2(b) |
| R3 (legacy criticism paths opt-in) | §2(c) |
| R4 (WHY archaeology) | §1(a)-(c) |
| R5 (schools as opt-in seats) | §2(d) |
| R6 (judge design target: dormant/summoned/starvable) | §1(e), §2(b) |
| R7 (judge-starving machinery: find or establish absent) | §1(d) — established absent |
| R8 (config-recommendation function: find or establish absent) | §1(d) — found, LIVE (`config_referee`) |
| R9 (workflow-makeover conditional) | §1(d)'s split verdict; §5.6's rung sketch |
| C1-C5 (SPEC-AND-STOP, evidence discipline, process) | this document's structure and citations throughout |
| C6 (school/foreign consequence priced) | §1(f) Consequence A/B, §2(d) |
| C7 (starvable throttle specified) | §2(b)'s throttle fields |
| C8 (dead = unreachable, not just gated) | §1(a), §1(d) applied uniformly |
| C9 (everything else stands) | frozen-surface forecast, byte-identical defaults throughout §2 |
| C10 (budget-overrun pre-authorization) | honored — this document was not truncated for length; see note below |
| C11 (design forks recorded, none taken) | §5.1-5.6 |
| C12 (only the final stop) | this is that stop |

**Note on C10 (final total)**: this tranche ran ten parallel research agents
(six for the original two-halves request, three for Amendment 1, plus this
executor's own direct corroboration reads) rather than sequential research,
per CLAUDE.md's "tokens are cheap, the agent is not" law — the actual token
cost was not tracked against a pre-set ceiling because none was set for this
tranche; C10's pre-authorization was exercised in spirit (continuing through
a document of this length rather than truncating findings) even though no
formal budget-overrun stop was actually triggered.

---

# OPEN QUESTIONS CARRIED FORWARD (not resolved here, per C11 — priced, not decided)

- Q1 (REQUEST.md): whether the three original opt-ins (now four, with
  schools) are one unified flag or independent ones — this SPEC designs
  them as four independent `Config` booleans (§2a-d), the smallest-reasonable
  reading, consistent with the operator listing them as separate sentences
  both originally and in the amendment.
- Q2: resolved by Half 1(a) — "the two assignable seats" is `conjecture`
  and its `simulation` alias, with `coder` and `scratch` dead weight.
- Q3: resolved by Half 1(c)/§2(c) — legacy criticism paths census found
  exactly one true legacy-superseded pair (already gone from the tree); no
  new opt-in surface needed beyond §2(a)'s adjudication flag.
- §5.1, §5.4, §5.5: the three forks with real design-direction consequences,
  priced above, awaiting operator words.

---

# ADDENDUM (Amendment 3, R10-R12) — post-STOP clarifying findings

Sent after the SPEC-AND-STOP endpoint; answered here from direct code
verification rather than a new research fan-out, since all three questions
resolve from files already read for Half 1/2. No design change to §2(b)'s
opt-in surface results from this addendum — it sharpens the evidence behind
it and surfaces one additional structural gap (R12).

## R10 — config-based judge starvation: confirms §2(b) as designed

No new finding; §2(b)'s `JUDGE_SUMMONS_PER_CYCLE`/`JUDGE_SUMMONS_COOLDOWN`
fields are exactly this, modeled on the existing `ADVISORY_TRIALS_PER_CYCLE`/
`DISC_ATTEMPTS_MAX`/`DISC_COOLDOWN` pattern (§1(e)). Static (operator-set
caps), not adaptive to a live zeal measurement — the adaptive version is
§5.6's M2 rung, gated on M1 first producing real signals (next).

## R11 — built-in signals to detect active judges: two different things exist, in two different states

**Quality/misbehavior signals** (self-preference, verbosity bias, error
rate) — code exists, `informal/audits.py:228` (`planted_flaw_calibration`)
and `:273` (`bias_probes`, emitting `judge-self-preference:`/
`judge-verbosity-bias:`), consuming `JUDGE_ERR_MAX` (`config.py:269`). Per
Half 1(d), these have zero call sites in production — only
`tests/test_audits.py` calls them — and zero occurrences in any committed
`log.jsonl`. This is exactly §5.6's M1 rung: the signal-producing code is
written but never plugged in.

**Raw activity-rate signals** (how often the judge fires per cycle,
independent of quality) — no generic per-role counter exists. `TokenMeter`
(`llm/budget.py`) has `calls` but no role dimension (`grep` for "judge" in
`llm/budget.py` returns zero hits, confirmed in Half 1(d)). The pattern
exists only for narrower, already-named cases:
`self._advisory_trials_this_cycle` (`scheduler.py`, counted against
`ADVISORY_TRIALS_PER_CYCLE`) and the `DISC_ATTEMPTS_MAX` attempt counter —
both scoped to one trial kind, not "judge calls in general." A generic
judge-activity-rate counter would need to be added; it does not exist
today under any name.

## R12 — single-model, two-judge-seats: the runtime logic is built and correct; nothing today can construct the manifest it needs

**The runtime fallback already exists and is exactly the operator's
described shape.** `informal/trial.py:614-629` (`_argument_trial_steps`):
```python
if adapter.is_single_model():
    # One model in every position cannot supply cross-FAMILY independence:
    # the ensemble gate is unsatisfiable by construction, so the trial was
    # unreachable rather than strict. The substitute is cross-SCHOOL
    # CRITICISM -- the case must come from a school other than the one that
    # authored the target.
    if len(adapter.leases.get("judge", ())) < 2:
        return _decline(harness, target_id, "single-judge-seat", diagnostics)
    if not critic_school_id:
        return _decline(harness, target_id, "no-critic-school", diagnostics)
    if critic_school_id == target.provenance.school:
        return _decline(harness, target_id, "same-school-critic", diagnostics)
else:
    adapter.require_cross_family_judges()
```
When the whole run is single-model, this branch does **not** call
`require_cross_family_judges()` at all — it only requires ≥2 judge seats
(same model is fine, since the run is already known single-model) plus a
`critic_school_id` distinct from the target's own school. `critic_school_id`
comes from the criticism side's own foreign-school assignment
(§1(f) — a mechanism already live and working today), not from the
separately-noted-superseded `school_judge_bindings`/
`require_cross_school_judge_ensemble` path. So the school-based
independence substitute this branch implements is real, reachable
machinery, not dead code.

**The blocker is one level up: manifest construction has no way to produce
≥2 judge seats without also breaking single-model-ness.**
`run_manifest.py:3137-3160` (`compile_run_manifest`, `single_model` branch):
```python
for role in configured_roles:
    roles[role] = (exact,)          # every role, including judge, gets ONE route
    ...
if "judge" in configured_roles and judge_family:
    second_spec = _select_second_judge_spec(data, judge_family, exact.family, ...)
    roles["judge"] = (exact, _route_from_spec(second_spec, ...))   # a SECOND, DIFFERENT-family route
```
Without `--judge-family`, judge gets exactly one route — `len(judge seats)
< 2`, so the single-model branch above always declines with
`"single-judge-seat"`. The only CLI lever that adds a second judge route,
`--judge-family`, is built (by its own parameter name and
`_select_second_judge_spec`'s signature, which is explicitly handed
`exact.family` to select against) to pick a **different** family — by
design, never the same model twice. Adding that second, different-family
route makes `is_single_model_run` (which pools leases across *every* role,
`llm/firewall.py:299-338`, per §1(f)'s Consequence B) return False for the
whole run, so `_argument_trial_steps` takes the **other** branch
(`require_cross_family_judges()`) instead — which then also happens to
succeed, since judge already has its 2 distinct families. The practical
result: `--judge-family` gives you a working two-judge trial, but never
through the single-model/same-model-twice substitute path — it always
routes around it into the ordinary cross-family gate.

**Verdict: genuinely single-model, same-model-in-both-judge-seats is not
constructible through any operator-facing surface today**, despite the
runtime logic that would consume it being written, commented, and correct.
This is the same shape of finding as the dead seats in Half 1(a) and the
unwired O1a detector in Half 1(e) — real logic, no reachable path to it —
newly discovered by this question rather than by the original ten-agent
sweep, and it belongs in the same category: not a defect (nothing is
broken; the fallback was clearly built deliberately and correctly for this
exact case), but a gap between what the engine can do and what the CLI
exposes.

**Decision-sheet consequence**: this adds a fourth road option to §5.2
(judge-summons live wiring scope), priced here rather than reopening §5.2's
numbering:

- **Road C (new) — add a manifest-construction lever for "N identical judge
  seats, no forced family divergence."** Smallest fix: a CLI flag (e.g.
  `--judge-seats N` or reusing `--judge-family` with a sentinel meaning
  "same family, just more seats") that populates `roles["judge"]` with N
  copies of `exact` instead of requiring a second, different-family spec.
  Cost: small — the runtime consumer already exists and is already tested
  against this exact shape (`_argument_trial_steps`'s single-model branch);
  this is purely a manifest-construction change in `compile_run_manifest`
  plus a CLI argument, not new adjudication/trial logic.
  **Recommended** — of everything in this addendum, this is the one clear,
  low-cost, high-value fix: it makes an already-built, already-correct,
  already-tested-in-shape fallback actually reachable, directly serving
  the solo law (a solo run should not be structurally locked out of any
  harness capability, including a judge-mediated trial) at minimal
  implementation cost.
- **Road D — leave it unreachable; treat the `--judge-family` path as the
  only way to get a defended trial with judges on a mostly-single-model
  run.** No cost, but leaves a solo-law gap: an operator who genuinely
  wants school-carried independence instead of introducing a second model
  family has no way to get it, even though the code was built for exactly
  that preference.
- Recommendation: Road C, folded into the same follow-up program as §5.6's
  M1-M3 rungs (a natural M0, since it's smaller and independent of the
  judge-bias-signal wiring those rungs need) — not this tranche's
  implementation, since C4/no-code-this-window still holds, but worth
  naming as the cheapest of all the gaps this SPEC found.

## R13 (Amendment 4) — the pre-school criticism circuit: real, live-elsewhere, one contract away from working

The operator's own words: *"Can you trace the code for criticism before
schools? Because it exists. And the circuit can be switched back on if
schools are unwanted."* Traced directly; the claim is correct, and this
revises §2(c)'s earlier conclusion that the legacy-criticism census found
"no dormant legacy code requiring its own new flag" — it did not go deep
enough. This is a genuine, cheap, named legacy-criticism-path opt-in
candidate that supersedes that conclusion.

**The circuit**: `scheduler/scheduler.py::_arg_crit` (`:1187-1259`) branches
on whether `criticism_policy` is present:
```python
criticism_policy = (
    self.run_manifest.criticism_policy
    if self.run_manifest is not None and self.run_manifest.schema_version in {4, 5, 6}
    else None
)
...
if criticism_policy is not None:
    self._foreign_arg_crit()      # school-routed path (§1(c), §2(d))
    return
eligible: list[str] = [...]        # PLAIN path: no school assignment at all
...
for i in range(0, len(eligible), size):
    batch = eligible[i : i + size]
    if self.run_manifest is not None and self.run_manifest.schema_version == 6:
        for target_id in batch:
            self._defer_untransactional_v6_phase(
                "argumentative-criticism", "argumentative_critic", target_id,
            )
        continue
    crit_argumentative_batch(harness, batch, self.adapter, config)   # never reached under v6
```
The dispatch function itself, `crit_argumentative_batch`
(`rules/crit.py:1336`), is not a stale duplicate — it is the SAME function
`_foreign_arg_crit` calls to actually execute school-routed criticism
(`scheduler.py:1413-1419`, called directly, no deferral check, inside a
plain try/except). It is proven, live, actively-dispatching code today;
only the non-school *entry ramp* into it is blocked.

**Reachability of `criticism_policy=None`, verified**: `compile_run_manifest`'s
own parameter default is `criticism_policy: CriticismPolicyV1 | None = None`
(`run_manifest.py:2935`). The high-level convenience path every ordinary
`setup`/`prepare` run goes through, `build_preparation_manifest`
(`preparation.py:364-400`), unconditionally supplies
`criticism_policy=engaged_criticism_policy(...)` — schools are never
optional through that path. But the lower-level `deepreason compile` CLI
subcommand (`cli/main.py:696-711`) calls `compile_run_manifest` **without
ever passing `criticism_policy`**, so it already defaults to `None` through
that path, today, with zero code changes.

**Why it still doesn't fire under v6, precisely**: `_defer_untransactional_v6_phase`
(`scheduler.py:582-638`) — its own docstring: *"Defer a legacy model phase
that has no v6 transaction contract. RunManifest v6 makes the adapter fail
closed on every unbound provider dispatch. Optional legacy scheduler phases
must therefore become visible completion debt instead of tripping that
global guard."* For schema v6 it always returns `True`, so the `continue`
above always fires — `crit_argumentative_batch` is never reached in this
branch under the only schema version the harness accepts today. Instead a
permanent, append-only marker is recorded
(`"v6-model-phase-deferred.v1","argumentative-criticism","argumentative_critic",...`)
and nothing anywhere in the tree ever reads it back to retry the call —
confirmed by exhaustive grep: `workflow/criticism.py` (the actual
v6-transactional criticism machinery) is built exclusively around
school-keyed `ForeignCriticism*` types, and no other module references the
`"v6-model-phase-deferred.v1"` marker except the writer
(`scheduler.py`) and the reporter (`verification/report.py`, which surfaces
it as a diagnostic finding, `_deferred_model_phase_findings`,
`verification/report.py:1074`) — it is a one-way "this was skipped" receipt,
never a retry queue.

**This is a real, general v6-migration pattern, not unique to criticism**:
the identical shape gates the plain rubric/judge trial too
(`scheduler.py:1108-1115`: `if self._defer_untransactional_v6_phase("rubric-trial", "judge", ...): continue`)
and the plain HV-floor check (`scheduler.py:1097-1107`, phase
`"hv-floor"`/`"hv-spot-check"`) — the latter two are confirmed genuinely
LIVE and firing (81 occurrences across the committed corpus,
re-verified directly, e.g.
`experiments/2026-08-08-corpus-enrichment-patrol-pilot/.../log.jsonl:415`),
but exclusively for `hv-floor`/`hv-spot-check` — `grep` for
`"argumentative-criticism"` inside any deferral marker across the entire
committed corpus returns zero hits, confirming no committed run has yet
compiled with `criticism_policy=None` while also having eligible targets
reach this exact branch.

**What "switching it back on" actually requires**: not a config flip alone.
Two things are already true today (no code needed): `criticism_policy=None`
is reachable via `deepreason compile`, and the dispatch function
(`crit_argumentative_batch`) is proven live code. One thing is missing:
this specific phase needs the same treatment `_foreign_arg_crit`'s
school-routed call already has — a v6 transaction contract, so
`_defer_untransactional_v6_phase` either isn't consulted for this phase or
is backed by a real recovery path (mirroring how
`workflow/nonconjecture_recovery.py` already recovers OTHER interrupted v6
transactions, per Half 1(d)'s finding on `config_referee`'s own recovery
handler). Because the eligibility computation, budget capping
(`ARG_CRIT_PER_CYCLE`, `RECRIT_STANDING`, `CRIT_BATCH_K`), and the dispatch
function are all already written and exercised daily via the school-routed
path, this is a smaller, more contained change than either §5.2's judge-
summons wiring or the R12 judge-seat-count CLI lever — it is the single
cheapest concrete finding in this entire tranche.

**Decision-sheet consequence — Road E, added to §2(c)/§2(d)'s scope**:

- **Road E (new, recommended)**: give the `"argumentative-criticism"` phase
  a v6 transaction contract, making the already-existing
  `criticism_policy=None` circuit actually dispatch under v6. This becomes
  the genuine "schools opt-out, criticism keeps working" path §2(d) gestured
  at without yet naming a mechanism — a school-free `argumentative_critic`
  seat is not a new seat vocabulary (§5.5's Road B still holds — this is
  not seat_bindings.py-shaped), it is the pre-existing, non-school
  dispatch ramp, finished. Should be folded into the legacy-criticism-paths
  opt-in (§2(c)) as its one concrete, evidenced surface, superseding that
  section's earlier "no additional distinct surface" conclusion.
- **Road F — leave it deferred.** Schools remain effectively mandatory for
  any criticism to actually happen under v6, regardless of whether the
  operator wants them. This is the status quo Amendment 1 was raised to
  question in the first place; it does not serve "schools: opt-in"
  faithfully, since opting out of schools today silently opts out of
  criticism entirely (a silent, undisclosed consequence exactly of the
  kind C6 warned against for the schools-as-seats question, now found to
  apply to schools-as-mandatory-routing too).
- **Recommendation**: Road E. This is not a design fork with a real
  trade-off the way §5.1/§5.4/§5.5 are — Road F actively contradicts the
  operator's stated intent ("schools need to be opt in") by leaving
  criticism silently dependent on schools being on. Road E is priced here
  rather than executed only because C4 still holds (no code this window).

---

## R13 Road E — REVISED (Amendment 7, R19/R20; SUPERSEDES the Road A/Road B framing in CHECKLIST.md's step-3 stop report)

Traces: R13, R19, R20, C15. Written mid-execution, after CHECKLIST.md
step 3 hit a contradiction (`crit_argumentative_batch`'s `active_v6`
branch hard-requires `critic_school_id`) and the operator resolved it with
a third shape neither originally-priced road named: *"I need a clean
separation between school and criticism. Although they still need to
interact."*

### Measurements (this is a mid-execution DESIGN-AND-STOP correction; measure, don't reason)

M1: `git blame -L 1372,1380 -- src/deepreason/rules/crit.py` (after
`git fetch --unshallow`, since the container's shallow clone bottomed out
blame at a boundary commit) →
```
8cf27e850b (AHepi 2026-07-19 19:04:07 +1000) active_v6 = False
...
8cf27e850b (AHepi 2026-07-19 19:04:07 +1000) if active_v6 and (endpoint_lease is None or critic_school_id is None):
8cf27e850b (AHepi 2026-07-19 19:04:07 +1000)     raise ValueError("v6 criticism requires one manifest-bound school route")
```
Commit message: "Implement transactional inquiry runtime v6 remediation",
operator's own commit, predating both the `experiments/` tranche system
and the school mechanism's own maturity — the guard was the ONLY option
at the time it was written, not a considered exclusion of an alternative.
Supports: this coupling is safe to loosen; it was never a negotiated
policy decision to defend.

M2: full read of `_v6_transactional_batch_call` (`rules/crit.py:255-519`)
— its ONLY school-specific behavior is: (a) the type hint
`critic_school_id: str` (not `Optional`); (b) one explicit guard,
`rules/crit.py:299-300`: `if not critic_school_id: raise ValueError(...)`;
(c) `payload["critic_school_id"] = critic_school_id` (a plain dict value,
already tolerates `None` as JSON `null`); (d)
`adapter.call(..., school_id=critic_school_id, ...)` — **already proven to
tolerate `None`** by `referee.py:507,637`'s own identical usage
(`run_config_referee`'s no-`criticism_policy` branch sets
`critic_school_id = None` and passes it straight through the same
parameter). Supports: exactly one guard line is the entire coupling in
this function.

M3: full read of `_v6_transactional_atomic_critic_call`
(`rules/crit.py:522-...`, the per-target schema-exhaustion-retry path) —
**zero explicit school guards**; `critic_school_id` is carried only as a
payload field (`rules/crit.py:565`), same tolerate-`None` shape as M2(c).
Supports: the atomic-decomposition/retry machinery (schema-exhaustion
handling, per-target children) is ALREADY school-agnostic in practice —
only its type hint needs relaxing.

M4: `crit_argumentative_batch`'s own top-level guard,
`rules/crit.py:1378-1379`: `if active_v6 and (endpoint_lease is None or
critic_school_id is None): raise ValueError("v6 criticism requires one
manifest-bound school route")`, plus an `assert critic_school_id is not
None` at `rules/crit.py:1438` inside the `active_v6:` branch. Both are
guard/assert statements only — nothing downstream in this branch (traced
in full, `rules/crit.py:1436-1687`) reads `critic_school_id` for anything
except passing it through as a payload/call value already shown
`None`-tolerant in M2/M3.

M5: recovery side, `nonconjecture_recovery.py::_criticism_contract`
(`:643-718`) — the ONE place that genuinely requires more than a guard
relaxation: `_authority(policy is not None, "manifest does not authorize
criticism")` (line 649) requires `manifest.criticism_policy`, then
resolves `school_id = payload.get("critic_school_id")` against
`policy.bindings` (lines 651-653). This has no `None`-tolerant branch
today and needs one: when `critic_school_id is None`, the school-binding
lookup and the `criticism_policy is not None` requirement must both be
skippable, replaced by verifying `preparation.route_lease` against a
plain `argumentative_critic` role/route (mirroring `select_lease`'s own
resolution), not a specific school binding.

M6: blast-radius census, `grep -rln "critic_school_id" tests/ docs/map/`
→ 9 test files (`test_config_referee.py`,
`test_criticism_school_execution_c3.py`, `test_foreign_criticism_policy_c3.py`,
`test_l1_continue_resumable_crash.py`, `test_prose_refutation_boundaries.py`,
`test_v6_engaged_public_defaults.py`, `test_v6_live_repair_transactions.py`,
`test_v6_nonconjecture_recovery.py`, `test_v6_transaction_qualification.py`)
plus 6 map documents. Every hit is classified **MUST NOT MOVE** — this
design changes nothing about behavior when `critic_school_id` is provided
(every one of these tests exercises the school-present case); none is
EXPECTED TO MOVE. `grep` for `LEGACY_ARG_CRITICISM_CONTRACT_V1` (this
tranche's own step-2 addition) → only `rules/crit.py` and this tranche's
own `CHECKLIST.md`; safe to remove, nothing else references it.

### Design (revised)

Reject the payload-schema-fork shape entirely (no
`"legacy-argumentative-criticism.v1"` schema, no
`LEGACY_ARG_CRITICISM_CONTRACT_V1` constant — **Step 2's addition is
reverted as part of this revision**, since M2-M5 show it is unnecessary:
the clean separation is achieved by making the EXISTING
`"criticism.semantic-task.v1"` schema and `"batch-critic.v2"` contract
genuinely school-optional, not by forking a second schema). Concretely:

- S13a (R19): `rules/crit.py:1378-1379` — narrow the top-level guard to
  `if active_v6 and endpoint_lease is None: raise ValueError("v6
  criticism requires a manifest-bound route")` (drop the `critic_school_id
  is None` half; reword the message since it no longer names schools
  specifically).
  accept: `python -m pytest tests/test_v6_scheduler_model_phase_deferral.py -q`
  and the full `tests/test_foreign_school_criticism_scheduler_c3.py` still
  pass unmodified.
- S13b (R19): `rules/crit.py:1437-1438` — remove `assert critic_school_id
  is not None` (keep `assert endpoint_lease is not None`).
  accept: same test files as S13a.
- S13c (R19): `_v6_transactional_batch_call`
  (`rules/crit.py:255-262,299-300`) — widen `critic_school_id: str` to
  `critic_school_id: str | None = None`; remove the `if not
  critic_school_id: raise ValueError("transactional criticism requires a
  critic school")` guard (keep the `endpoint_lease.role !=
  "argumentative_critic"` guard).
  accept: `tests/test_v6_live_repair_transactions.py -q` passes unmodified
  (the file with the most direct assertions on this function).
- S13d (R19): `_v6_transactional_atomic_critic_call`
  (`rules/crit.py:522-528`) — widen `critic_school_id: str` to
  `critic_school_id: str | None = None` (type-hint only; M3 showed no
  guard to remove).
  accept: same as S13c.
- S13e (R20): `nonconjecture_recovery.py::_criticism_contract`
  (`:643-718`) — add the `critic_school_id is None` branch: skip the
  `criticism_policy is not None`/binding-lookup requirement (lines
  649-653) and instead verify `preparation.route_lease` names a route
  present in `manifest.roles.get("argumentative_critic", ())` (any seat),
  exactly mirroring how a plain `select_lease("argumentative_critic", 0)`
  resolves in the dispatch direction. The `school_id is not None` branch
  is UNTOUCHED — byte-identical to today.

  **Authority-recoverability clarification, CORRECTED (found alongside
  S13i, same root cause; superseding the first version of this
  paragraph):** `_criticism_contract(harness, manifest, item, preparation,
  payload)` receives no live `Config` object at all — checked directly,
  its signature carries no such parameter, and the file's only
  `Config`-shaped helper, `config_from_run_manifest(manifest)` (imported
  at `nonconjecture_recovery.py:32`, used once at `:349` for an unrelated
  purpose), DERIVES a `Config` from the frozen manifest — but
  `ARGUMENTATIVE_AUTHORITY` is, by the frozen-surfaces law itself, NEVER
  written into the manifest, so `config_from_run_manifest` cannot recover
  its true original value; it would always report the bare default
  (`observe_only`), silently masking a real override. Re-deriving
  authority live at recovery time (this paragraph's original proposal) is
  therefore WRONG twice over: no live `Config` reaches this function at
  all, and even a manifest-derived reconstruction cannot see this
  specific field. The correct fix, consistent with the "freeze at mint
  time, never reread mutable state at recovery" principle this codebase
  states repeatedly (`docs/map/INV-frozen-surfaces.md`,
  `SEAM-adjudication-x-authority.md`): bake the RESOLVED authority value
  into the durable transaction payload at ORIGINAL dispatch time — the
  same treatment `critic_school_id` already gets. Concretely: S13i-3's
  self-resolved dispatch, via the `transactional_call` closure inside
  `crit_argumentative_batch` (which already captures `authority` from its
  enclosing scope), adds one new field,
  `payload["dispatch_authority"] = authority if critic_school_id is None
  else None`, to `_v6_transactional_batch_call`'s payload construction
  (a new keyword-only parameter on that function, threaded from the
  closure — the school-routed case passes `None`/omits it, since that
  case already has its own frozen source of truth and does not need a
  second one). Recovery then reads `payload.get("dispatch_authority")`
  (frozen, replay-stable, exactly like `critic_school_id`) and refuses
  typed unless it equals `"observe_only"` — no live or reconstructed
  `Config` access anywhere in the recovery path.
  accept: `tests/test_v6_nonconjecture_recovery.py -q` passes in full,
  including every existing `_criticism_contract`-adjacent test
  unmodified, PLUS two new tests,
  `test_v6_nonconjecture_recovery.py::test_criticism_contract_recovers_without_a_school`
  (payload's `dispatch_authority` is `"observe_only"` — resolves and
  admits) and
  `::test_criticism_contract_refuses_recovery_without_a_school_when_dispatch_authority_is_not_observe_only`
  (payload's `dispatch_authority` is e.g. `"trial_required"` — refuses
  typed, mirroring the school-routed branch's own `'critic authority is
  not recoverable'` shape, sourced from the frozen payload field instead
  of `criticism_policy.authority`), PLUS a third test,
  `::test_v6_transactional_batch_call_freezes_dispatch_authority_for_school_free_calls`,
  proving the payload actually carries the resolved authority at dispatch
  time (not just that recovery reads it correctly).
- S13f (R19, R20): `scheduler.py::_arg_crit`'s plain branch
  (`:1244-1259`, the code Step 4 was going to touch) — replace the
  `_defer_untransactional_v6_phase(...)` + `continue` with: resolve
  `endpoint_lease = select_lease(adapter.leases, "argumentative_critic",
  0)` (the SAME fallback `run_config_referee` already uses when
  `criticism_policy is None`), then call `crit_argumentative_batch(harness,
  batch, self.adapter, config, run_manifest=self.run_manifest,
  endpoint_lease=endpoint_lease, critic_school_id=None,
  transaction_assignment_refs=(), transaction_trigger_ref=...)`. This is
  now the SAME dispatch function the school-routed path already calls
  (S13a-e made it accept `critic_school_id=None`), not a new parallel one
  — R19's "clean separation" (criticism dispatch does not require a
  school) and R20's "still interact" (the identical function, the
  identical contract, carries `critic_school_id` when one IS supplied)
  both hold in one code path.
  accept: `tests/test_v6_scheduler_model_phase_deferral.py::test_legacy_argumentative_criticism_dispatches_under_v6`
  (Step 3's originally-planned test, now written against the correct
  target) passes.
- S13g (process): revert Step 2's `LEGACY_ARG_CRITICISM_CONTRACT_V1`
  constant from `rules/crit.py` — dead per M6, superseded by S13a-f.
  accept: `grep -q LEGACY_ARG_CRITICISM_CONTRACT_V1 src/deepreason/rules/crit.py`
  exits 1 (not found).

### Frozen-surface contact forecast (revised)

Unchanged from the original Road E forecast: none of S13a-g touch
`capabilities/state.py`, `harness.py` event application, `invariants.py`,
or any `run_manifest.py` schema/validator. `nonconjecture_recovery.py`
(S13e) and `rules/crit.py` (S13a-d,f-g) are not on the five-surface list.
No new grant needed beyond R16's already-scoped `run_manifest.py`
`_versioned_source_config_data` pop-lines (unrelated to this revision).

### Blast-radius census

See M6 above — 9 test files, all classified MUST NOT MOVE, none EXPECTED
TO MOVE. This IS the census; nothing else greps against the touched
symbols.

### Budget (revised, replaces CHECKLIST.md's original ~600-line Road E estimate)

S13a: ~2 lines changed. S13b: ~1 line removed. S13c: ~3 lines (type hint +
guard removal). S13d: ~1 line (type hint). S13e: ~20 lines (new branch +
its own small helper). S13f: ~15 lines (scheduler wiring). S13g: ~4 lines
removed. New tests: S13e's recovery test ~30 lines, S13f's dispatch test
~40 lines (Step 3's original test, corrected). Map update (Traps entry,
`docs/map/SUB-scheduler.md`/a `SUB-workflow.md` note on `_criticism_contract`'s
new branch): ~15 lines.
`python3 -c "print(2+1+3+1+20+15+4+30+40+15)"` → **131 lines**, roughly
1/5 of the original ~600-line Road E estimate — confirms M1-M5's finding
that this is a small, surgical fix once the actual coupling is measured
rather than assumed. CHECKLIST.md's tranche-wide 1,600-line ceiling is
UNCHANGED (this revision reduces one component of it; does not need to
raise the total).

Rubric: 6/6 yes (every R19/R20 item has an accept criterion; blast-radius
census pasted and classified; frozen-surface forecast recorded — none;
measurements precede every design claim, per DESIGN-AND-STOP discipline
carried over from this being a mid-execution correction; options were not
separately priced because M1-M5 leave exactly one viable design, not a
genuine fork — Road A/Road B from the step-3 stop report are both
superseded, not chosen between; nothing here is untraceable to R13/R19/R20/C15).

---

## S13h (addendum, found executing CHECKLIST.md step 6) — a fourth guard site M1-M5 missed

`_critic_execution` (`rules/crit.py:106-134`) is called by BOTH
`crit_argumentative` and `crit_argumentative_batch`, before either reaches
the `active_v6` branch S13a-g already loosened. It has its own,
independent all-or-nothing guard:
```python
supplied = (
    endpoint_lease is not None,
    critic_school_id is not None,
    critic_school_context is not None,
)
if any(supplied) and not all(supplied):
    raise ValueError(
        "school-routed criticism requires endpoint_lease, critic_school_id, "
        "and critic_school_context"
    )
```
Road E's dispatch shape (`endpoint_lease` supplied, `critic_school_id`/
`critic_school_context` both `None`) is exactly the `any(supplied) and
not all(supplied)` case this raises on. S13a-g alone does not make Road E
actually dispatch — this is not a hypothetical, it is the next guard the
call would hit immediately after S13a-g's changes. M1-M5's read of
`crit_argumentative_batch`/`_v6_transactional_batch_call`/
`_v6_transactional_atomic_critic_call` did not include this earlier-called
helper; that is the miss.

**Design**: add one early-return branch, before the existing all-or-nothing
check, for exactly the Road E shape (`endpoint_lease` present, both school
fields absent) — mirroring the existing school-routed return's `call_kwargs`
shape but with `school_id: None` and no conditioning prefix (there is no
school stance to render):
```python
if endpoint_lease is not None and critic_school_id is None and critic_school_context is None:
    if endpoint_lease.role != "argumentative_critic":
        raise ValueError("criticism endpoint lease must belong to argumentative_critic")
    return (
        {
            "endpoint_index": endpoint_lease.seat,
            "endpoint_lease": endpoint_lease,
            "school_id": None,
        },
        "",
    )
```
Every other combination (all three `None`; all three present; a genuinely
partial supply like `endpoint_lease` + `critic_school_id` but no context)
falls through UNCHANGED to the existing logic — byte-identical for every
existing caller.

- S13h (R19, R20): `rules/crit.py:106-134` — add the branch above.
  accept: `tests/test_foreign_school_criticism_scheduler_c3.py -q` (its
  school-routed calls into `crit_argumentative_batch` exercise
  `_critic_execution` indirectly — it is a private, leading-underscore
  helper with no direct test-file callers by name, confirmed by
  `grep -rln "_critic_execution" tests/` returning zero hits) passes
  unmodified, PLUS a new test,
  `tests/test_v6_scheduler_model_phase_deferral.py::test_critic_execution_permits_endpoint_only_dispatch`,
  asserting `_critic_execution(endpoint_lease=<lease>,
  critic_school_id=None, critic_school_context=None)` returns
  `({"endpoint_index": ..., "endpoint_lease": ..., "school_id": None}, "")`
  without raising, AND that the ORIGINAL partial-supply rejection (e.g.
  `endpoint_lease` + `critic_school_id`, no context) still raises
  `ValueError` with the original message.

### Frozen-surface contact forecast (S13h)

None — `rules/crit.py`, already covered by S13a-g's forecast.

### Blast-radius census (S13h)

`grep -rln "_critic_execution" tests/ docs/map/` → zero hits in `tests/`
(it is called only internally by `crit_argumentative`/
`crit_argumentative_batch`, never named directly by a test); four map
documents (`SEAM-schools-x-scratch.md`, `SEAM-llm-x-rules.md`,
`CON-criticism-source.md`, `CON-schools.md`) describe it by name. All four
classified MUST NOT MOVE — none document the all-or-nothing guard's exact
three-way shape as an invariant (checked: none of the four contain the
literal guard text), so none needs updating for a widened combination;
the real regression surface is `test_foreign_school_criticism_scheduler_c3.py`'s
indirect exercise via `crit_argumentative_batch`'s school-routed calls,
already listed under M6's census and re-run as this item's accept
criterion.

### Budget (S13h)

~15 lines (new branch) + ~20 lines (new test) = 35 lines, added to the
Road E total: 131 + 35 = **166 lines**, still well inside the 1,600
ceiling and the ~1,131-line component sum.

Rubric: 4/4 yes (accept criterion present; blast-radius census pasted and
classified; frozen-surface forecast recorded — none; traceable to
R19/R20, the same authority as S13a-g, not a new fork).

---

## S13i (addendum, R21) — self-sufficient dispatch: how the scheduler-authority boundary and the school separation both hold

### Measurements

M7: `docs/map/SEAM-scheduler-x-rules.md`'s checked invariant (`check:` at
the "The scheduler never chooses a prose authority" paragraph):
```python
f = lambda m: [n for n in ast.walk(ast.parse(textwrap.dedent(inspect.getsource(getattr(S, m)))))
               if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "crit_argumentative_batch"]
a = f("_arg_crit"); b = f("_foreign_arg_crit")
assert len(a) == 1 and not a[0].keywords, [k.arg for k in a[0].keywords]
```
`_arg_crit`'s call to `crit_argumentative_batch` must carry ZERO keywords.
S13f as originally planned (scheduler resolves `endpoint_lease`, passes it
plus `run_manifest`/`critic_school_id=None` as keywords) violates this
literally and in principle — traced to `_resolve_authority`
(`rules/crit.py:91-93`): `if explicit_authority is None: if policy_call:
raise ValueError("manifest-bound criticism requires explicit
argumentative authority")`. `policy_call` becomes `True` the moment
`_critic_execution`'s `call_kwargs` is non-empty (`rules/crit.py:1213,1376`:
`policy_call = (bool(call_kwargs) or argumentative_authority is not None
or coverage_observer is not None)`), which S13h's own endpoint-only branch
makes non-empty. The scheduler would be the only party able to supply
`argumentative_authority` on this call site — exactly the "third state"
the seam's prose forbids.

M8: `LLMAdapter` already carries a private, pre-bound manifest reference
independent of any per-call argument — `llm/adapter.py:253-254`:
`self._v6_authority_harness = None; self._v6_authority_manifest = None`
at construction, populated by `bind_v6_authority(self, harness, manifest)`
(`:256-...`), called exactly once, at `Scheduler.__init__`
(`scheduler/scheduler.py:203`: `adapter.bind_v6_authority(harness,
run_manifest)`) — confirmed by
`tests/test_v6_scheduler_model_phase_deferral.py::test_v6_scheduler_rejects_an_unguarded_adapter_before_work`
raising `WorkflowAuthorizationError` when this binding is absent. By the
time ANY scheduler method runs under a v6 manifest, `self.adapter`
already carries the canonical manifest — no new call-time plumbing
needed.

M9: `policy_call`'s current computation (`bool(call_kwargs) or ...`) is
NEVER independently tested — `grep -rn "policy_call" tests/ docs/map/`
shows every hit either IS the computation itself (`rules/crit.py:1213,1376`)
or calls `_resolve_authority` directly with an explicit `policy_call=`
boolean (`test_prose_refutation_boundaries.py`,
`docs/map/CON-authority.md:132,148`, `docs/map/CON-criticism-source.md:37`)
— none exercises the internal `bool(call_kwargs)` derivation. Before
S13h, `call_kwargs` was non-empty if and only if `critic_school_id is not
None` (the old all-or-nothing guard made the two conditions identical for
every reachable combination) — so redefining `policy_call =
(critic_school_id is not None or argumentative_authority is not None or
coverage_observer is not None)` is behaviorally IDENTICAL to today for
every combination reachable before S13h, and differs only for the new
endpoint-only combination S13h introduced — which is exactly the case
that needs to differ.

### Design

- S13i-1 (R21): add one small public read-only accessor to `LLMAdapter`
  (`llm/adapter.py`, adjacent to `bind_v6_authority`):
  ```python
  def bound_v6_manifest(self):
      """The manifest bound by bind_v6_authority, or None if unbound."""
      return self._v6_authority_manifest
  ```
  accept: `tests/test_model_firewall.py` or a new small test asserts
  `LLMAdapter(...).bound_v6_manifest() is None` before binding and equals
  the bound manifest after `bind_v6_authority(harness, manifest)`.
- S13i-2 (R19, R21): redefine `policy_call` in BOTH `crit_argumentative`
  (`rules/crit.py:1213` region — the single-target function) and
  `crit_argumentative_batch` (`:1376` region) from `bool(call_kwargs) or
  argumentative_authority is not None or coverage_observer is not None`
  to `critic_school_id is not None or argumentative_authority is not None
  or coverage_observer is not None`. accept: every existing test in
  `tests/test_foreign_school_criticism_scheduler_c3.py`,
  `tests/test_prose_refutation_boundaries.py` passes unmodified (M9's
  proof made concrete).
- S13i-3 (R19, R21): in `crit_argumentative_batch`, when the caller
  supplies no `run_manifest`/`endpoint_lease`/`critic_school_id` (the
  scheduler's existing keyword-free call shape, UNCHANGED), self-detect
  v6-ness via `adapter.bound_v6_manifest()`: if non-None, internally set
  `run_manifest = adapter.bound_v6_manifest()` and `endpoint_lease =
  select_lease(adapter.leases, "argumentative_critic", 0)` (the identical
  fallback `run_config_referee` already uses, `referee.py:507-508`)
  before the existing `active_v6 = run_manifest.schema_version == 6`
  computation — `critic_school_id` stays `None`. If
  `adapter.bound_v6_manifest()` is None (a genuinely pre-v6/legacy
  adapter), behavior is BYTE-IDENTICAL to today (falls through to the
  existing non-transactional `else` branch). Also thread `dispatch_authority`
  (per S13e's corrected authority-recoverability design above) through the
  `transactional_call` closure into `_v6_transactional_batch_call`'s new
  payload field, sourced from `authority` (already in scope, computed
  earlier in this same function) whenever `critic_school_id is None`.
  accept: a new test,
  `tests/test_v6_scheduler_model_phase_deferral.py::test_legacy_argumentative_criticism_dispatches_under_v6`
  (Step 11's originally-planned test, now written against the corrected
  design) passes with the SCHEDULER'S call to `crit_argumentative_batch`
  unchanged (`harness, batch, self.adapter, config` — zero keywords),
  AND `python -c "import ast, inspect, textwrap; from deepreason.scheduler.scheduler import Scheduler as S; t = ast.parse(textwrap.dedent(inspect.getsource(S._arg_crit))); calls = [n for n in ast.walk(t) if isinstance(n, ast.Call) and getattr(n.func, 'id', '') == 'crit_argumentative_batch']; assert len(calls) == 1 and not calls[0].keywords"`
  exits 0 — this IS `SEAM-scheduler-x-rules.md`'s own checked invariant,
  re-run directly to prove S13i does not violate it.
- S13i-4 (R19, R21): simplify `scheduler.py::_arg_crit`'s plain branch —
  DELETE the `if self.run_manifest is not None and
  self.run_manifest.schema_version == 6: ... _defer_untransactional_v6_phase(...) ...
  continue` block entirely (S13i-3 makes `crit_argumentative_batch`
  self-sufficient under v6, so deferring is no longer needed for this
  phase); the call `crit_argumentative_batch(harness, batch, self.adapter,
  config)` becomes reachable unconditionally, exactly as it already is
  for schema versions other than 6. This is SMALLER than the original
  S13f plan (deletes code, adds none at the call site) and needs no new
  `select_lease`/`run_manifest`/`transaction_trigger_ref` plumbing in
  `scheduler.py` at all — that logic now lives entirely inside
  `crit_argumentative_batch` (S13i-3), which is the correct owner per
  "the scheduler decides what is worked on... the rules decide what that
  work means" (`SEAM-scheduler-x-rules.md`'s own opening line).
  accept: Step 13's reader test (deferral marker still correct for
  `hv-floor`/`hv-spot-check`/`rubric-trial`) passes unmodified.

### Frozen-surface contact forecast (S13i)

`llm/adapter.py` is touched (S13i-1) — NOT one of the five named frozen
surfaces (`capabilities/state.py`, `harness.py`, `invariants.py`,
`run_manifest.py`, replay-validation formats). The new accessor is
read-only, additive, and reads state the adapter already stores; no
construction-signature change, no new stored attribute. No grant needed
beyond R16's already-scoped `run_manifest.py` pop-lines (unrelated).

### Blast-radius census (S13i)

`grep -rln "bound_v6_manifest\|_v6_authority_manifest" tests/ docs/map/` →
`_v6_authority_manifest`/`_v6_authority_harness` appear only inside
`llm/adapter.py` itself per M8's trace (no test or map document names them
directly) — the new PUBLIC name `bound_v6_manifest` is genuinely new,
zero existing hits, nothing to classify as MUST NOT MOVE. `policy_call`'s
census is M9 above. `_arg_crit`'s call-shape census is
`SEAM-scheduler-x-rules.md`'s own check, re-run as S13i-3's accept
criterion rather than merely read.

### Budget (S13i)

S13i-1: ~5 lines. S13i-2: ~2 lines (two one-line redefinitions). S13i-3:
~10 lines. S13i-4: ~-12 lines (net deletion). New tests: ~25 lines net
(the accessor test and the corrected dispatch test both already counted
in earlier budgets; the deleted deferral-branch code reduces S13f's
original estimate). Net addition to the Road E total: approximately +20
lines against the 166-line S13a-h subtotal → **~186 lines**, still well
inside the 1,600 ceiling.

Rubric: 6/6 yes (every S13i item has an accept criterion; blast-radius
census pasted and classified; frozen-surface forecast recorded — `llm/adapter.py`
touched, confirmed not one of the five; every measurement precedes its
design claim; the design was independently verified to satisfy
`SEAM-scheduler-x-rules.md`'s own checked invariant, not merely argued to;
traceable to R19/R20/R21, not invented).

# ADDENDUM (Amendment 9, R22/R24) — content-blind same-model judge ensembles

Written after Part D (judge seats opt-in, CHECKLIST.md steps 33-41)
shipped and after the operator's clarification resolved R22's open
question: the independence guarantee a judge ensemble needs is
CONTENT-BLINDNESS (the judge never learns which model, role, or school
authored the target), not cross-family or cross-school model diversity —
diversity was always a proxy for an unstated blindness property. A
same-model (even literally one model in every judge seat) ensemble may
mint a real, status-changing warrant once blindness is established as a
pinned, enforced invariant rather than assumed.

## S14 — three enforcement sites, not two: the corrected census

R12's addendum (Amendment 3) already found and priced the gap for ONE of
two live judge-gated trial mechanisms (`_argument_trial_steps`/
`defended_trial`, `informal/trial.py:601+` — argumentative/prose
criticism). Re-reading for this addendum finds a THIRD site R12 did not
cover, because R12 was scoped to the `defended_trial` path only:

1. **`_argument_trial_steps`** (`informal/trial.py:614-629`,
   `defended_trial`): already has a single-model substitute — cross-SCHOOL
   diversity (`critic_school_id != target.provenance.school`), not
   blindness. R12/Road C priced making this reachable via a manifest-
   construction lever; still unreachable today (confirmed: no CLI flag
   populates `roles["judge"]` with >1 same-model route).
2. **`run_trial`/`_trial_steps`** (`informal/trial.py:227-360`, the rubric-
   commitment trial Part D's `JUDGE_SEATS_ENABLED` gates): calls
   `adapter.require_cross_family_judges()` UNCONDITIONALLY — no
   single-model branch exists here at all. This is the path Part D's new
   tests (`tests/test_budget.py::test_judge_summons_per_cycle_cap` and
   `::test_judge_summons_cooldown`) exercise, and the one
   `tests/test_judge_ensemble_boundary.py::test_trial_rejects_invalid_
   direct_ensemble_before_any_endpoint_call` PINS as rejecting a
   same-family two-judge pair TODAY (parametrized `same_family_pair=True`
   case) — this test's same-family branch is the one collateral change
   R24 requires, not a defect in it.
3. **`run_manifest.py`'s compile-time `V4_CRITICISM_CROSS_FAMILY_JUDGES_
   REQUIRED`** (`run_manifest.py:2819-2834`, `_validate_v4_criticism_
   policy`'s `policy.authority == "defended_trial"` branch) — a SEPARATE
   compile-time check on the school-routed `criticism_policy.authority`
   field, parallel to but distinct from `rubric_policy`'s own compile-time
   check (`run_manifest.py:1516,3199`, `SECOND_JUDGE_FAMILY_REQUIRED`) and
   from `llm/firewall.py::require_cross_family_judge_ensemble`'s runtime
   check (`firewall.py:341-358`) that both trial paths above ultimately
   consult through `LLMAdapter.require_cross_family_judges`/
   `_select_judge_ensemble` (`adapter.py:648-674`).

All three must move together for R24 to hold uniformly — relaxing only
the runtime gate would leave `compile_run_manifest` refusing to construct
the manifest a same-model judge ensemble needs; relaxing only
`rubric_policy` would leave `defended_trial`'s independent V4 check
enforcing the old requirement.

## S15 — blindness is already structurally true; pin it, don't build it

Read-only verification (Amendment 9 clarification, restated with file:line
precision): `informal/trial.py::_judge_pack` (`:174-194`) never
interpolates provenance/role/model/school; `llm/roles.py::TEMPLATES["judge"]`
(`:83-88`) is fixed boilerplate plus `{pack}`; `adapter.py::call`'s
`school_id`/`endpoint_lease` params are routing-only, never spliced into
prompt text (`:965-1062`). This repo already has EXACTLY this shape of
invariant test for the sibling critic pack —
`tests/test_prose_refutation_boundaries.py::test_the_criticism_prompt_
never_names_an_author_or_a_school` (R9) reads a real committed root's
rendered critic pack and asserts no school id and no `school`/`author`/
`provenance` substring appears. No equivalent test exists yet for the
JUDGE pack (`_judge_pack`'s output) specifically — S15's implementation is
that test's twin, not new mechanism.

## S16 — REVISED (operator, 2026-08-10, "The switch needs to be exposed to CLI is all. Otherwise it's not a setting.")

The additive-Config-knob design first drafted here is dropped: a
`Config`-only flag, settable only via `--config`'s YAML profile, does not
satisfy the operator's explicit requirement. The corrected design reuses
a mechanism this codebase already has, rather than inventing a new one:
`llm/firewall.py::require_cross_family_judge_ensemble`'s sibling,
`require_cross_school_judge_ensemble`, is ALREADY a structural substitute
for cross-family diversity — unlocked not by a boolean flag but by the
manifest's own frozen shape (`school_judge_bindings` configured +
`is_single_family_run`). R24's same-model substitute takes the identical
shape: accept EITHER cross-family diversity OR (≥2 judge seats AND every
seat carries the exact same `(provider, model_id)` — narrower than
family, confirmed against `is_single_model_run`'s own docstring: "two
different models of one family are one family and two models"). No
Config field, no threaded boolean parameter anywhere — the check reads
`manifest.roles["judge"]`/`leases["judge"]` directly, the same way its
cross-school sibling already does.

Under this design "the switch" is not a boolean at all — it is the CLI
lever that lets an operator reach the manifest shape this check now
accepts, which the frozen-surface finding (this addendum's earlier
"Verdict" and SPEC's original Road C) already established is
UNREACHABLE today through any operator-facing surface. That lever is:

- New `--blind-same-model-judges` flag on `deepreason config compile`
  (mutually exclusive with `--judge-family` — both requesting the second
  judge route is ambiguous). In `single_model` mode, populates
  `roles["judge"] = (exact, exact)` — two references to the one frozen
  route the whole run already uses — instead of requiring a second,
  different-family spec.
- `require_cross_family_judge_ensemble` (runtime) and `RunManifest`'s own
  `rubric_policy == "require_cross_family"` model-validator (compile-time)
  both gain the structural OR described above.
- The `defended_trial`/V4 criticism-policy check
  (`run_manifest.py:2819-2834`) gains the identical structural OR, reading
  the same `roles["judge"]` shape the CLI flag can now produce — no
  separate CLI lever for this second site, matching how every other
  `criticism_policy`-adjacent knob in this tranche (`ENGAGED_CRITICISM_
  AUTHORITY`, `LEGACY_CRITICISM_ENABLED`) is Config/YAML-only, never a
  CLI flag of its own.

**Verified before writing 57c** (not merely argued): the existing pinned
test `test_trial_rejects_invalid_direct_ensemble_before_any_endpoint_
call`'s `same_family_pair=True` case uses two DIFFERENT model strings
(`gemma-test-a`/`gemma-test-b`) of the same family — under the narrower
"exact same model" substitute, this case is UNCHANGED (still correctly
rejected), so this pinned test needs no collateral edit, only a sibling
positive-path test proving the genuinely-identical-model case now mints.

S15's blindness-pinning test remains the hard prerequisite this design
builds on — the structural OR is safe to ship only because `_judge_pack`
is independently proven never to leak the identity that would make
"same model" a meaningfully weaker guarantee than "different model."

## Frozen-surface forecast (Part D2)

`llm/firewall.py` (not previously listed as CLAUDE.md-frozen but treated
with the same care as manifest schemas per Amendment 9's grant) and
`run_manifest.py` (Amendment 9's grant, scoped specifically to this
relaxation — see REQUEST.md) both change. `informal/trial.py` gains the
new parameter thread but no behavior change when
`JUDGE_BLIND_SAME_MODEL_ALLOWED=False`. No `harness.py`/
`capabilities/state.py`/replay-validation-format change.

## Budget (Part D2, estimate)

S15 (blindness test): ~30 lines. S16 (new Config field + firewall param +
two manifest sites + threading + collateral test update in
`test_judge_ensemble_boundary.py` + new positive-path tests): ~150-200
lines. CLI/map updates: ~40 lines. Estimated total: ~250-300 lines,
comfortably inside a fresh 1,600-line ceiling for this addendum's own
diff-budget base commit (to be set at Part D2's first step).
