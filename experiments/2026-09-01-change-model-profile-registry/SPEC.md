# Spec for: "Take this particular task out of the hands of the machine"

Traces: every item cites R/C numbers from REQUEST.md (R1-R6 the operator's
2026-09-01 words; R7-R9 Amendment 1; C1-C9 standing constraints; M1-M8 the
monitor's decomposition, itself traced to R numbers there). Untraceable items
are bugs.

Map ids in scope, resolved at capture: `DR-INV-frozen-surfaces`,
`DR-SEAM-llm-x-manifest`, `DR-SEAM-llm-x-verification`, `DR-SEAM-llm-x-workflow`,
`DR-SEAM-llm-x-scheduler`, `DR-SUB-llm`, `DR-SUB-manifest`, `DR-CON-seats`,
`DR-CON-packs-and-token-economy`.

## The one-sentence design

A model's settings become a document a human writes
(`$DEEPREASON_HOME/model-profiles/<model-id>/agent.md`), the harness reads that
document through one declared interface and holds no per-model opinion of its
own, and a model with no document runs with the knob omitted and the split
protocol stood down — which, because nothing ships (R8), is the state every
model starts in.

## Items

### S1 (R3, R4, R5, R7, R8; M1) — the registry: documents, loader, validator

**Files (new):** `src/deepreason/model_profiles/__init__.py`,
`src/deepreason/model_profiles/document.py`,
`src/deepreason/model_profiles/registry.py`.

**Before:** no such concept. Per-model facts exist only as a constant in
`llm/providers.py:70` and as prose in tranche write-ups.

**After:**

*Document shape.* One directory per model, one document inside it named
`agent.md` (R7, the operator's words). The document is Markdown — a human
writes whatever prose they like — carrying EXACTLY ONE fenced block whose info
string is `deepreason-model-profile-v1`. The loader reads only that block; the
prose is for the reader. Exactly one, not at-least-one: a second block is a
typed error, for the same reason `docs/map/SCHEMA.md` makes its `check:` grammar
total — a parser free to guess which block was meant is how a document comes to
say something nobody wrote.

*The key is the declaration, not the path.* The directory name is a
convenience; `model_id` inside the block is authority. The loader scans
`<root>/*/agent.md` and keys by the declared id. This is what lets a model id
containing characters awkward in a path (`deepseek-v4-pro:0813`,
`gpt-oss:120b`, `qwen3.5:397b`) be described without inventing an escaping
scheme the operator would have to learn — and it is what makes "all possible
future models" (R9) a property of the loader rather than a promise.

*Fields* (M1's minimum set, with two renamings the record forced — see A2):

| field | meaning |
|---|---|
| `schema` | `deepreason-model-profile.v1` |
| `model_id` | the id the run config names |
| `measured_on` | ISO date the claims below were measured |
| `reasoning.documented_values` | the values the provider's own documentation lists for this model. DESCRIPTIVE ONLY (R9) |
| `reasoning.extraction_value` | the value the extraction leg should send. `null` means "send nothing" |
| `reasoning.thinking_disablable` | whether thinking can be switched off at all |
| `reasoning.disabling_values` | the values that actually stop this model thinking (may be empty) |
| `reasoning.trace_destination` | per value: `side_channel` \| `content` \| `absent` |
| `context_window_tokens`, `max_output_tokens` | declared capacity |
| `tokens_per_second` | measured speed |
| `can_compact` | can it obey "respond more compactly" |
| `transport_notes` | free-text transport quirks |
| `evidence` | pointers to the record that measured each claim |
| `probe` | the command that re-verifies the claims |

*Interface.* `deepreason.model_profiles` exports and nothing else is a legal
import site: `resolve(model_id) -> ModelProfileV1 | None`, `installed()`,
`profiles_root(home=None, environ=None)`, `register(profile)`,
`unregister(model_id)`, `registry_fingerprint()`,
`MODEL_PROFILE_REGISTRY_VERSION`.

*Location.* `profiles_root` is `provider_state_dir(...) / "model-profiles"`,
i.e. `$DEEPREASON_HOME/model-profiles/` (else `~/.deepreason/model-profiles/`).
Nothing ships (R8): `src/deepreason/` gains no document and no default row.
`register()` exists for tests and for a future plugin, and is in-process only —
it never writes a file.

accept:
    python -c "
    import tempfile, pathlib
    from deepreason import model_profiles as mp
    d = pathlib.Path(tempfile.mkdtemp())/'model-profiles'/'x-1'
    d.mkdir(parents=True)
    (d/'agent.md').write_text('''# x-1\n\nprose a human wrote\n\n\`\`\`deepreason-model-profile-v1\nschema: deepreason-model-profile.v1\nmodel_id: x-1\nmeasured_on: 2026-09-01\nreasoning:\n  documented_values: [low, high]\n  extraction_value: low\n  thinking_disablable: false\n  disabling_values: []\n  trace_destination: {low: side_channel, high: side_channel}\n\`\`\`\n''')
    p = mp.resolve('x-1', home=None, environ={'DEEPREASON_HOME': str(d.parent.parent)})
    assert p is not None and p.model_id == 'x-1' and p.reasoning.extraction_value == 'low'
    assert mp.resolve('never-heard-of-it', environ={'DEEPREASON_HOME': str(d.parent.parent)}) is None
    " -> exits 0

### S2 (R1, R4; M2) — retire the hard-coded off-token; the readers read

**Files:** `src/deepreason/llm/providers.py`, `src/deepreason/llm/split.py`,
`src/deepreason/llm/adapter.py`, `tests/test_providers.py`.

**Before:** `providers.py:70` `REASONING_OFF = "none"`, a module constant;
`split.py:163` `extract_reasoning=REASONING_OFF if knob else None`, so every
extraction leg on every model sends the literal `"none"`. No configuration
value can change it. `providers.py:93` `reasoning_disabled(value)` decides
"this seat is already thinking-off" by string-comparing against that same
constant — which is a per-MODEL claim decided by a per-VOCABULARY constant, and
is false on glm-5.3 (M1 below).

**After:** `REASONING_OFF` and `reasoning_disabled` are DELETED from
`providers.py`. What remains there is provider-shaped and stays: `infer_provider`,
`reasoning_body` (neutral knob → wire fields), `reasoning_knob_available`
(whether this PROVIDER realizes the knob at all — a provider fact, not a model
fact). `split.py` takes a `profile: ModelProfileV1 | None` keyword and sends
`profile.reasoning.extraction_value`; it names no reasoning literal anywhere.
`adapter.py::_split_plan` resolves the profile from `lease.route.model` through
the interface and passes it. The parameter has NO DEFAULT: a caller that
forgets it gets a TypeError, never the old guessing behaviour.

accept:
    ! grep -rn "REASONING_OFF\|def reasoning_disabled" src/ tests/ docs/
    && grep -q "profile: \"ModelProfileV1\" | None" src/deepreason/llm/split.py
    && python -c "
    from deepreason.llm.split import plan_split
    plan_split(mode='on', ceiling=4096, extraction_tokens=512, provider='ollama', reasoning='high')
    " 2>&1 | grep -q "required keyword-only argument: 'profile'"
    -> exits 0

### S3 (R2, R5, R9; M3) — the unknown model, which is every model until a human writes a document

**Files:** `src/deepreason/llm/split.py`, `tests/test_split_budget_protocol.py`,
`tests/test_split_leg_recording.py`.

**Before:** the split protocol arms for any provider with a reasoning adapter,
regardless of the model, and sends `"none"`.

**After:** three typed dispositions, none of them a refusal (C9, the
all-configurations law):

| state | disposition | notice |
|---|---|---|
| no profile for this model | stand down | `split-budget:no-model-profile-for-this-seat` (NEW) |
| profile exists, declares no `reasoning` block | stand down | `split-budget:profile-declares-no-reasoning` (NEW) |
| profile declares `extraction_value` | arm, send that value | `""`, or `split-budget:extraction-leg-cannot-stop-thinking` (EXISTING) when `thinking_disablable` is false |

`disclosed` follows the module's own existing rule verbatim
(`_replace_notice(NOTICE_NO_CEILING, disclosed=(mode == "on"))`): disclosed
under `on` (the run explicitly asked to split and could not), silent under
`auto`. This is not a softening — it is the reason `SplitPlan.disclosed` exists,
stated at `split.py:88-93`: under R8 no container has any profile, so a
disclosed-always notice would stamp one constant string on every attempt of
every run and say nothing. The once-per-run disclosure is S4's record stamp.

Both new strings are free of frozen surfaces, measured not assumed:
`LLMSplitLegV1.notice` is `notice: str = ""` with no `Literal`
(`ontology/event.py:90-91`), and the only limb of `verify_root` that reads a
notice tests it for emptiness (`invariants.py:4338`).

accept:
    python -m pytest tests/test_split_budget_protocol.py -q -> 0 failed
    && python -c "
    from deepreason.llm.split import plan_split, NOTICE_MODEL_PROFILE_MISSING
    p = plan_split(mode='on', ceiling=4096, extraction_tokens=512, provider='ollama', reasoning='high', profile=None)
    assert not p.armed and p.notice == NOTICE_MODEL_PROFILE_MISSING and p.disclosed
    " -> exits 0

### S4 (R2, R4; M3) — the run's own record says which profiles built it

**Files:** `src/deepreason/scheduler/scheduler.py`.

**Before:** nothing in a run's record says which model documents existed when it
ran, so two runs that differ only in an installed document are
indistinguishable after the fact.

**After:** `_record_module_fingerprints` stamps a SECOND
`ModuleFingerprintV1`, `registry="model-profiles"`, carrying the registry
version, the count, and each installed profile's `model_id`, `digest` and
`measured_on`. Zero installed profiles is a valid, meaningful stamp — it is the
`model-profile-missing` disclosure for the whole run, and under R8 it is the
common case.

This road, and not a `CompileNoticeV1`, on measurement (M2, M3 below): the
`ModuleFingerprintV1` docstring declares the extension point in terms
(`module_events.py:31-32`, "`registry` names the registry that resolved it, so
further registries can be stamped later **without a schema change**"), the
payload materializes no state so replay applies it by ignoring it
(`harness.py:638-641`), and no frozen surface is edited. The compile-notice road
was measured and rejected: it moves the qualification subject digest.

accept:
    python -m pytest tests/test_model_profile_registry.py -k record_stamp -q -> 0 failed
    && python -c "
    import inspect
    from deepreason.scheduler.scheduler import Scheduler
    s = inspect.getsource(Scheduler._record_module_fingerprints)
    assert 'model-profiles' in s and 'registry_fingerprint' in s
    " -> exits 0

### S5 (R1, R3, R5; M5) — the five authored documents

**Files (new):** `docs/model-profiles/README.md` and
`docs/model-profiles/<model-id>/agent.md` for `glm-5.3` (FIRST),
`glm-5.2`, `deepseek-v4-pro:0813`, `qwen3.5:397b`, `gpt-oss:120b`.

**These are reference copies the loader never reads** (R8: home only).
Installing one is a human act: `cp -r docs/model-profiles/glm-5.3
"$DEEPREASON_HOME/model-profiles/"`. README states exactly that, and states
where the harness looks.

Every declared value cites the record that measured it, by
`git show <sha>:<path>` and never a moving branch head — the evidence lives on
branches this branch does not carry (C4), so a citation naming a bare path
would fail its own check here. Nothing is declared from memory, and where the
record has no measurement the field is ABSENT rather than guessed.

glm-5.3's document, which is the one that answers R1, declares
`extraction_value: low`, `thinking_disablable: false`, `disabling_values: []`,
`can_compact: false`, and the ~300 s transport note.

accept:
    python -c "
    from deepreason.model_profiles.document import parse_document
    import pathlib
    for p in sorted(pathlib.Path('docs/model-profiles').glob('*/agent.md')):
        prof = parse_document(p.read_text())
        assert prof.measured_on and prof.evidence, p
    assert len(list(pathlib.Path('docs/model-profiles').glob('*/agent.md'))) == 5
    " -> exits 0

### S6 (R5; M6) — the probe that makes a stale document fail a check, not a run

**File (new):** `scripts/model_profile_probe.py`.

For one model id: send each `documented_value` on a fixed prompt N times;
report clean-content rate, trace destination, completion tokens and latency;
compare against the document's own claims; exit NON-ZERO when a claim fails.
`--offline` runs the comparison against a recorded fixture so the script is
testable without a provider. Prints `profiles_root()` so an operator can see
where the harness is looking.

**Q4 disposition — priced, not asked, and not implemented (C3, C8, M6).**
M6 asks for the probe to be "wired so qualification or preflight can run it per
seat and record the result typed". Measured: `qualification.py` carries no
registry, hook, plugin or policy object by which a per-seat probe result could
be recorded — every path into it is a source edit, and its subject payload
dumps the manifest and the provider profile WHOLE (`qualification.py:264`,
`281-289`), so any field carrying a probe result enters the digest
automatically. Price of doing it: every existing home loses its cached
"qualified" verdict and owes a fresh battery (~14 min, ~1160 calls) per model
configuration; measured precedent for exactly this shape, changing
`ProviderProfileV1.reasoning` from `none` to `high`, moves the subject
`66e4c331… -> cb7ac430…`. C3 makes that an immediate stop, and R6/M6 itself
says "do not edit it". **Disposition: the probe ships standalone and is named
by each document's `probe:` field. Not wired into qualification. Not wired into
`cli/doctor.py` either** — doctor.py is not frozen, but its cases feed the same
subject, so wiring there buys the same battery through a side door.

accept:
    python scripts/model_profile_probe.py --self-test -> exits 0
    && python scripts/model_profile_probe.py --offline --fixture <recorded>
       --document docs/model-profiles/glm-5.3/agent.md -> exits 0
    && (same, against a fixture mutated to contradict one claim) -> exits non-zero

### S7 (R4; M7) — the architecture test, which must be able to go red

**File (new):** `tests/test_model_profile_registry.py`.

Four failable checks, written to the genre this repo already uses
(`tests/test_channel_and_wander_modularity.py`,
`tests/test_discharge_contract.py`, `tests/test_successor_registry.py`) — AST
census with positive anchors, plus behavioural bypass detection:

1. **No per-model literal outside the registry.** AST scan of every
   `src/deepreason/**/*.py`: no string constant equal to a known model id, and
   no reasoning-vocabulary literal (`none`/`low`/`medium`/`high`/`max`) reached
   by `llm/split.py` or assigned as a module constant in `llm/providers.py`.
   Positive anchor: assert the scan actually visited > 200 files, so a moved or
   renamed tree fails instead of passing vacuously (SCHEMA.md check-rule 1).
2. **`REASONING_OFF` never returns.** Absence grep paired with a positive
   anchor on `providers.py` itself.
3. **Adding a model needs no source edit.** Write a document for a model id
   that appears nowhere in the tree into a temporary home, resolve it through
   the public interface alone, and assert every file under `src/deepreason/` is
   byte-identical before and after.
4. **Consumers reach the registry only through its interface.** AST
   `ImportFrom` scan with levels resolved (SCHEMA.md check-rule 3): nothing
   outside `model_profiles/` imports `model_profiles.document` or
   `model_profiles.registry` directly.

Each is shown RED against a planted bypass and then GREEN, in the
`MUTATION_PROOF_V1` format the compile-gap tranche committed
(`experiments/2026-09-01-defect-judge-canary-compile-gap/MUTATION_RED.txt`).

accept: MUTATION_RED.txt and MUTATION_GREEN.txt committed for S2, S3 and S7
(C6), each carrying `production_tree`, `test_file_sha256`, `command`, `exit`.

### S8 (R3, R4; M8) — the map moves in the same commit

**Files:** `docs/map/CON-model-profiles.md` (new), `docs/map/SUB-llm.md`,
`docs/map/CON-seats.md`, `docs/map/INDEX.md`.

- `CON-model-profiles.md`: a CONCEPT document, not a subsystem one — the
  registry is a package but the thing it governs is spread across `llm/`,
  `scheduler/` and the operator's home directory, which is exactly the case
  `SCHEMA.md` gives for `CON-`. Full anatomy, re-runnable single-line `check:`
  lines at column 0, `Seams:` naming only documents that exist.
- `SUB-llm.md`: `Owns:` unchanged; the entry-points check at :102 loses
  `reasoning_disabled`; the split rows at :163-165 gain the profile parameter.
  The Traps entry at :245-255 ("Unset reasoning is not off") is **rewritten in
  place to say when and how its premise stopped holding, never deleted** —
  `SCHEMA.md`'s own rule. A new Traps entry names P-S1 (M-1, M-16) and P-A1 run
  `4565139800f5ca02`.
- `CON-seats.md:138`: its check calls `plan_split(...)` by exact keyword and
  asserts `p.armed`; it gains the `profile` argument. Same commit, or it goes
  red.
- `INDEX.md`: one concept-table row and one routing row.

accept:
    python tools/docs_verify.py -> 0 failed
    && python tools/docs_verify.py --audit -> no vacuous/unparseable checks
    && python tools/docs_verify.py --links -> every DR- reference resolves

### S2b (R1, R4, R9; forced by S2) — the launch refusal becomes a disclosure

**Discovered during execution, not at spec time.** Added here rather than done
silently, because it changes a public CLI behaviour the spec did not forecast.

**File:** `src/deepreason/cli/main.py`.

**What was found.** `_reasoning_disabled_refusal` consumed
`providers.reasoning_disabled` through a FUNCTION-LOCAL import (line 2379),
which `tools/blast_radius.py` cannot see, so it appears in no census in this
document. It gated two commands — `deepreason reason` and the qualification
battery — and it REFUSED to spend a provider call unless the profile carried
`reasoning: none`, printing `REASONING_MUST_BE_DISABLED` and returning 1.

**Why it could not simply be left alone.** S2 deletes `reasoning_disabled`
(required by M2), and this is its only remaining consumer. Something had to
change; the only question was what.

**Why it became a disclosure rather than a corrected refusal.** Two reasons,
one factual and one about authority.

1. It was wrong about the fact, in the sharpest possible way. On glm-5.3
   `reasoning: none` is the value that breaks the model (M1: 0/8 clean). This
   guard therefore DEMANDED the setting that killed three runs and refused the
   one that works. A profile-informed refusal would fix that particular error
   while keeping the shape that produced it.
2. It was a launch gate vetoing a configuration the operator chose. The
   operator, 2026-08-28: "Gates are always optional: with warnings." And,
   2026-09-01, answering this tranche's own question: "Harness is supposed to
   accommodate all possible future models and configurations." R9 is
   unambiguous.

**Why this was decided and not asked.** `dr-ask-the-right-question` requires a
fork the record kills to be decided and noted rather than put to the operator,
and this window has already spent one operator round trip on a question the
laws had answered. The dominance test: under "nothing ships", a
profile-informed REFUSAL cannot evaluate anything for a model with no document
— which is every model — so it either blocks every run or passes every run;
passing every run makes it dead code, and blocking every run is the veto R9
forbids. A disclosure keeps the signal and blocks nothing. It dominates both
alternatives.

**Honest note on the earlier exemption.** The 2026-08-12 all-configurations
tranche deliberately PRESERVED `REASONING_MUST_BE_DISABLED` as a launch-time
refusal, exempt from that law on the grounds that impossibility surfaces at the
point of use. This item reverses that exemption. It does so on the strength of
two LATER operator statements (2026-08-28 and 2026-09-01), not by disagreeing
with the earlier reading — but the operator should know a prior deliberate
decision was reversed, and can reverse it back with a word.

**After:** `_reasoning_disclosure` prints and the command CONTINUES. Silent
when the model's document says the configured value disables thinking; a
`REASONING_STAYS_ON` line when it says otherwise; a `MODEL_PROFILE_MISSING`
line when no document describes the model. Nothing refuses.

accept:
    python -c "
    import ast, pathlib, deepreason.cli.main as main
    tree = ast.parse(pathlib.Path(main.__file__).read_text())
    fn = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == '_reasoning_disclosure']
    assert len(fn) == 1
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, 'id', '') == '_reasoning_disclosure']
    assert len(calls) == 2
    " -> exits 0, and `docs/map/CON-model-profiles.md`'s disclosure check is green

## Assumptions (operator may override)

A1 (Q1, settled by R7/R8; this is the residue): the five authored documents
live in the repo at `docs/model-profiles/<id>/agent.md` as REFERENCE COPIES the
loader never reads, and installing one is `cp -r`. R8 says nothing ships and
R7 names the filename; neither says where an authored document is kept before a
human installs it, and M5 requires the five to exist. Smallest reading: keep
them where a human reads documents, and give the loader exactly one root.

A2 (M1): two of M1's field names are changed, and the change is recorded here
rather than made silently. "most-off value" becomes `extraction_value`, and
`thinking_disablable` is joined by `disabling_values`. Reason, measured (M1
below): on glm-5.3 the value that produces a clean answer (`low`, 8/8, median 7
completion tokens) is neither the most-off value nor a disabling value — `none`
is more "off" by the neutral vocabulary and is the one that ruins the answer.
A field called "most-off" would have to be filled with `low` while meaning
something else, which is how a document comes to lie. Assumed; the operator may
rename.

A3 (M4, superseded by R9): no substitution, no veto, no nearest-value logic
exists anywhere in this spec. A configured `reasoning:` value travels to the
provider exactly as written, whatever the document says. The document's
`documented_values` is descriptive and is read by the PROBE (S6), never by the
dispatch path.

A4 (M6): "N times" is `--trials`, default 8, matching the trial count P-S1
used for its glm-5.3 table so a re-run is comparable with the committed
measurement rather than merely internally consistent.

A5 (S3): `SPLIT_BUDGET_SEAT_PROTOCOL` keeps its `auto` default. Changing a
config default is not requested by any R, and under S3 `auto` with no installed
profile already produces the safe disposition (stand down).

## Questions for operator (STOP if non-empty)

None. The three the window reserved (C8) were asked and answered in REQUEST.md
Amendment 1; R9 dissolved the third rather than deciding it. The frozen-surface
forecast below is CLEAR, so no grant is required and no stop is owed.

## Out of scope (explicit)

- Raising `SPLIT_BUDGET_EXTRACTION_TOKENS` from 512 — not requested (C5);
  PARKED.md P3, and the measurement that would answer it cannot be taken until
  the thinking prose is gone.
- The ~300 s transport wall and blind identical retries — not requested (C5);
  PARKED.md P2. The glm-5.3 document DESCRIBES the wall; nothing reads that
  description yet, and this spec adds no reader for it.
- Seat exhaustion killing the run — not requested (C5); PARKED.md P1.
- Any new live reasoning run — not requested (C5). S6's probe is committed and
  runnable; this tranche does not run it against a provider.
- A `deepreason model-profiles` CLI command — not requested by any R. S6's
  probe prints the resolved root, which is the discoverability the requirements
  actually name.
- Changing `EndpointSpec.model_profile` (the `compact|standard|frontier`
  presentation field) — a name collision, not a requirement. It is untouched;
  the new concept is named `model-profiles` (plural, hyphenated) everywhere it
  appears on disk and `deepreason.model_profiles` in code.

## Frozen-surface contact forecast

`tools/blast_radius.py --files src/deepreason/llm/providers.py
src/deepreason/llm/split.py src/deepreason/llm/adapter.py
src/deepreason/scheduler/scheduler.py --symbols REASONING_OFF plan_split
reasoning_disabled reasoning_knob_available _split_plan
_record_module_fingerprints`, its own fields verbatim:

    "frozen_surface_contacts": []
    "frozen_adjacent_contacts": []
    "frozen_surface_verdict": "CLEAR"
    "disclosure_summary": "This change touches none of the five frozen
      surfaces. 5 test file(s) and 8 map document(s) assert on the touched
      targets today. Reachability here means a syntactic call path exists from
      a known entry point; it does not prove the path is ever actually
      exercised at runtime -- a symbol can be syntactically reachable and still
      never fire because of a runtime precondition this gate does not
      evaluate."

The gate reported ONE `UNKNOWN` reachability entry, `{"symbol":
"REASONING_OFF", "status_current": "UNKNOWN"}` — it is a module constant, not a
callable, so the gate has no call path to compute. Resolved by the manual
census step 5 requires for exactly this case, `grep -rn "REASONING_OFF" src/
tests/ docs/ tools/ scripts/`, pasted whole:

    src/deepreason/llm/split.py:36:    REASONING_OFF,
    src/deepreason/llm/split.py:163:        extract_reasoning=REASONING_OFF if knob else None,
    src/deepreason/llm/providers.py:70:REASONING_OFF = "none"
    src/deepreason/llm/providers.py:93:    return value is not None and str(value).strip().casefold() == REASONING_OFF

Four sites, all in `src/`, none in `tests/`, `docs/`, `tools/` or `scripts/`.
The UNKNOWN is resolved, not outrun: nothing pins the constant, so deleting it
breaks no check.

**Two frozen surfaces were reached BY DESIGN CONSIDERATION and deliberately not
touched. Both were measured, and the measurement is what excluded them:**

1. Surface 4/5 via a `CompileNoticeV1`. `qualification.py:267-273` strips
   exactly one notice code and keeps every other, so a `MODEL_PROFILE_MISSING`
   notice enters `manifest_behavior` and moves the subject digest (M3 below).
   Under R8 it would fire on every run in a fresh container. EXCLUDED — S4's
   record stamp replaces it, which is the road C2 already preferred.
2. Surface 4 via a manifest field carrying the profile id/digest. Not measured
   directly, and stated as the weaker claim it is: M3 measures that changing
   `compile_notices` — one field of the manifest — moves both digests, so a
   NEW field carrying a populated profile identity is strictly the larger
   change, and `run_manifest.py:1207-1218` records the same result measured
   both ways for a field addition. Independently decisive without any digest
   arithmetic: `INV-frozen-surfaces.md:669` runs `price_compile_gap.py --expect
   fixed` as a live `check:` pinning 28 sha256 literals over seven committed
   run configurations, so ANY manifest byte change turns `docs_verify` red.
   EXCLUDED.

Frozen-ADJACENT `route_fingerprint` (`llm/firewall.py`): NOT touched. `Route`
keeps its exact shape and `Route.reasoning` keeps its exact meaning; the
extraction leg's override travels in the request BODY and never mutates the
endpoint (`adapter.py:1125-1126`), so `EndpointLease.verify` still sees the
route's own value — the property this design depends on and does not change.

## Blast-radius census

Every hit from the gate's `consumers` field, classified. None omitted.

`consumers.tests`:

| target | hit | verdict |
|---|---|---|
| `plan_split` | `tests/test_split_budget_protocol.py` :48 :119 :127 :137 :147 :154 :173 :193 :201 :362 :413 :465 :541 | EXPECTED TO MOVE — S2 adds a required keyword; S3 changes the no-profile disposition |
| `reasoning_disabled` | `tests/test_providers.py` :114 :126 :127 :128 :129 :130 :132 :133 | EXPECTED TO MOVE — S2 deletes the function |
| `reasoning_disabled` | `tests/test_split_budget_protocol.py:146` | EXPECTED TO MOVE — same deletion |
| `reasoning_knob_available` | `tests/test_providers.py` :115 :119 :120 :121 :122 :123 | MUST NOT MOVE — the function is provider-shaped and survives unchanged |
| `_split_plan` | `tests/test_split_leg_recording.py:217` | EXPECTED TO MOVE — the adapter now resolves and passes a profile |
| `src/deepreason/scheduler/scheduler.py` | `tests/test_successor_rank_tie.py:169`, `tests/test_wander_cap.py:530` | MUST NOT MOVE — neither asserts on module fingerprints |

`consumers.map_checks` — 8 documents. Classified by whether the hit is on a
symbol this spec changes, not by whether the file name appears:

| document:line | verdict |
|---|---|
| `SUB-llm.md:102` (entry-points check pins `reasoning_disabled`, `reasoning_knob_available`, `reasoning_body`, `infer_provider` as top-level defs) | EXPECTED TO MOVE — S8 |
| `SUB-llm.md:157` (reasoning-knob row), `:163-165` (split rows), `:244-255` (the "Unset reasoning is not off" trap), `:249`, `:250`, `:90` | EXPECTED TO MOVE — S8; :244-255 is REWRITTEN, never deleted |
| `CON-seats.md:113` (`_split_plan`/`plan_split` prose), `:138` (the check that calls `plan_split` by keyword and asserts `armed`) | EXPECTED TO MOVE — S8 |
| `SEAM-llm-x-manifest.md:44` (names `providers.py`) | MUST NOT MOVE — the seam claim is about route compilation, not the off-token |
| `SEAM-llm-x-verification.md:165`, `:194` (`_split_plan` and what a leg records) | MUST NOT MOVE — S3 adds no field to `LLMSplitLegV1`; only new notice STRINGS, and `notice` is an open `str` |
| `SEAM-schools-x-scheduler.md:57 :58 :74 :79`, `CON-schools.md:93`, `CON-seats.md:98` (`_record_module_fingerprints`) | MUST NOT MOVE — S4 appends a second registry row; the school-population row is untouched. **Verify explicitly**: any of these that pins the module list LENGTH moves, and is then EXPECTED TO MOVE |
| every other `adapter.py`/`scheduler.py` hit (44 + 65 lines listed by the gate) | MUST NOT MOVE — they pin unrelated claims about files this spec edits in one function each |

Cross-check beyond the gate, for the two symbol shapes it cannot resolve:
`REASONING_OFF` (census above, 4 sites, 0 in tests/docs) and the notice STRINGS
(string labels, not identifiers): `grep -rn "split-budget:" tests/ docs/` before
S3 lands, and every hit classified in CHECKLIST.md.

## Measurements

M1 — glm-5.3's measured behaviour, which is what R1 is about, and which
contradicts one line of the monitor's own framing:

    git show origin/claude/deepreason-p-s1-commitments-wowcib:experiments/2026-08-31-p-s1-commitments/SEAT_REASONING_FINDINGS.md

    | reasoning_effort | clean content | separate reasoning field | median completion tokens |
    | none             | 0/8           | 0/8                      | 64 |
    | low              | 8/8           | 3/8                      | 7  |
    | omitted          | 8/8           | 8/8                      | 61 |

    "on glm-5.3, reasoning_effort: "none" does not turn thinking OFF. It turns
    off the SEPARATION."

Supports: `extraction_value: low`, `thinking_disablable: false`,
`disabling_values: []`, and A2's renaming. **Correction to the window's own
evidence block**, stated plainly because a profile must not inherit it: the
window says "Ollama's glm-5.3 page: reasoning_effort accepts low / high / max
... `none` is not in the set." The API parameter's documented set DOES include
`none` (same source, §1: `"high" | "medium" | "low" | "max" | "none"`), the
model accepts it on the wire, and what is wrong with it is behavioural, not a
rejection. The document therefore separates `documented_values` (the model
page) from `trace_destination` (what each value measurably does), because
collapsing them is the mistake that produced the wrong constant in the first
place.

M2 — the extension point S4 uses, declared in terms by the code it extends:

    src/deepreason/module_events.py:31-32
    "``registry`` names the registry that resolved it, so further registries
     can be stamped later without a schema change."
    src/deepreason/harness.py:638-641
    "The payload materializes no state, so replay applies it by ignoring it and
     no historical root acquires a new obligation."

Supports: S4 needs no schema change, no harness edit, and no replay obligation.

M3 — the two roads S4 replaces, priced by measurement, not argument:

    src/deepreason/qualification.py:264-273 — `behavior = manifest.model_dump(...)`
      then strips ONLY `ENGINE_CONFIG_FIELD_NOT_CARRIED`; every other compile
      notice enters the digested subject.
    src/deepreason/run_manifest.py:1207-1218 — "a `"value": null` on an
      unrelated notice moves the manifest sha256 AND every qualification
      subject digest that manifest feeds. Measured both ways."

Re-derived in this tranche rather than taken on report — the probe and its
output are committed as `price_notice_road.py` and `PRICE_NOTICE_ROAD.txt`,
so the claim is re-runnable rather than quoted:

    $ python experiments/2026-09-01-change-model-profile-registry/price_notice_road.py
    schema_version 6
    manifest sha BASE    1950b3d0ee2281137ee3a54def61252b129a955ff30a938feb9044d5ed7ff628
    profile from experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/provider.yaml
    subject BASE         b3f807f386f29cd83e69993beaed2a91723fc14d59eb93b5122c68acc2eee79b
    manifest sha +NOTICE b6afc4045d8125bea069c6cbb9452eaca5ac787692074ab0bd1d9d69003febea
    subject      +NOTICE 29bcca270c006ec5687037b20eab597942fb0261e107ffe58186e4ad20d43bd8

One added `MODEL_PROFILE_MISSING` notice, nothing else changed, and BOTH the
manifest sha and the qualification subject digest move. The probe adds the
notice to an already-compiled committed manifest rather than recompiling, which
is the narrowest form of the question: it isolates the notice as the only
variable.

Supports: both compile-time roads are frozen-surface motion; the record stamp
is not. This is the whole reason S4 looks the way it does.

M4 — the new notice strings cost nothing:

    src/deepreason/ontology/event.py:90-91 — `notice: str = ""`, no `Literal`
    src/deepreason/invariants.py:4338 — the only limb reading a notice tests
      `extract.notice == ""`

Supports: S3 adds two strings with no frozen-surface contact.

M5 — the census that resolves the gate's UNKNOWN: pasted in full in the
frozen-surface section above. Four sites, none outside `src/`.

M6 — `qualification.py` has no extension point, so S6's probe must stay
standalone: the subject payload dumps the manifest and the provider profile
WHOLE (`qualification.py:264`, `281-289`); the only exclusion machinery is
three hard-coded `behavior.pop` lines. Supports S6's Q4 disposition.

## Options

A — profile identity in the RunManifest (a new optional field). Files:
`run_manifest.py` (+ config, + qualification by consequence). Frozen contact:
surface 4 AND surface 5. ~60 lines. Risk: a battery rerun per configuration,
plus `INV-frozen-surfaces.md:669`'s 28 pinned shas go red.
**REJECTED — cites the committed `check:` at `INV-frozen-surfaces.md:669`
directly (a manifest byte change turns `docs_verify` red, no digest arithmetic
needed), with M3 as the supporting measurement that manifest-field changes move
both digests.**

B — `model-profile-missing` as a `CompileNoticeV1`. Files: a registry +
`v6_policy` wiring. Frozen contact: surface 5 by consequence. ~40 lines. Risk:
under R8 it fires on every run in a fresh container, so every home mints a new
qualification subject and owes ~14 min / ~1160 calls.
**REJECTED — cites M3.**

C — a second `ModuleFingerprintV1` row on the existing module-fingerprints
event, plus two new split notice strings. Files: `scheduler.py` (one function),
`split.py`. Frozen contact: none. ~90 lines. Risk: the stamp is written once
per run and a reader must know to look for it — mitigated by S8's map document
naming it.
**CHOSEN — cites M2 and M4.**

D — ship default profiles inside the package and let home override. Files: as C
plus package data. Frozen contact: none. **REJECTED — cites R8**, the
operator's own words ("Home directory only, nothing ships"), not a measurement.

## Budget

Itemized, and the headline is the computed sum of the items, not a restatement:

    python3 -c "print(sum([25,120,130,16,67,12,32,150,220,60,25,10,130,30,5,4,380]))"
    1416

    25   S1  src/deepreason/model_profiles/__init__.py
    120  S1  src/deepreason/model_profiles/document.py
    130  S1  src/deepreason/model_profiles/registry.py
    16   S2  src/deepreason/llm/providers.py
    67   S2  src/deepreason/llm/split.py
    12   S2  src/deepreason/llm/adapter.py
    32   S4  src/deepreason/scheduler/scheduler.py
    150  S6  scripts/model_profile_probe.py
    220  S7  tests/test_model_profile_registry.py
    60   S3  tests/test_split_budget_protocol.py
    25   S2  tests/test_providers.py
    10   S3  tests/test_split_leg_recording.py
    130  S8  docs/map/CON-model-profiles.md
    30   S8  docs/map/SUB-llm.md
    5    S8  docs/map/CON-seats.md
    4    S8  docs/map/INDEX.md
    380  S5  docs/model-profiles/ (5 documents + README)

**~1416 lines, 8 commits. Frozen surfaces touched: none.**

This exceeds the ~300-line guidance, and the split the guidance asks for is
recorded rather than taken. The arithmetic says why: the machinery is 552 lines
(`src/` + `scripts/`), the tests are 315, and the remaining 549 are AUTHORED
DOCUMENTS that R5/M5 and R8/M8 require by name — five model documents and two
map documents. Splitting content away from the code it describes would put the
map in a second commit, which `SCHEMA.md` forbids ("the map moves in the SAME
COMMIT as the code — a separate 'update docs' commit is the commit that gets
dropped"), and would deliver a registry with no profile in it. The protection
the guidance buys is kept by structure instead: eight ordered commits, each
with its own acceptance check above, and `tools/diff_budget.py` checked at
every one against this ceiling. Recorded here so the operator can overrule it.

Rubric: 6/6 yes
- every R has a spec item with a machine-decidable accept — R1:S2/S5, R2:S3,
  R3:S1/S5/S8, R4:S2/S4/S7/S8, R5:S1/S5/S6, R6:the tranche itself, R7:S1,
  R8:S1/S5, R9:A3 (and its absence from every dispatch path is checked by S7).
- blast-radius census pasted and every hit classified — yes.
- frozen-surface contact forecast recorded, with the gate's own fields
  verbatim and its one UNKNOWN resolved by census — yes.
- every mechanism the request names traced to code it actually reaches — yes:
  `providers.py:70` and `split.py:163` confirmed at those exact lines;
  `price_compile_gap.py` read and its role as a live `check:` pin discovered;
  `ModuleFingerprintV1`'s extension point read in the source, not assumed.
- DESIGN-AND-STOP sections — measurements and options priced, every rejection
  citing a measurement or an operator word.
- nothing untraceable to an R/C number — yes; the CLI command that tempted was
  moved to Out of scope.
