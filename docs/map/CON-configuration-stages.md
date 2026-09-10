<!-- DR-CON-configuration-stages -->
Verified-at: e158121de2
Verify: python tools/docs_verify.py
Owns:
Seams:
Seams-undocumented: application x manifest, llm x manifest

# The four stages a setting passes through

Read this at the moment of doubt: you believe a run was configured one
way, and it behaved as though configured another. A setting is not one
thing in one place. It passes through FOUR stages, and it can be altered,
dropped, or defaulted at each. Most reports that blame a model are
actually reading stage 1 and describing stage 4.

The rule this document exists to enforce: **never describe a run from the
file you wrote. Describe it from what compiled and ran.** One command does
all four stages at once —

    deepreason stop-report <run-root-or-home>

— and every stage below also names the narrower command that reveals it
alone.

## Stage 1 — the operator's file

What you wrote: a run-config YAML, a provider profile, CLI flags. This is
the ONLY stage that is not part of the record, and therefore the only one
that cannot be evidence about a run. A window that reports from here is
reporting its own intent.

Reveal it: read the file. Compare it against stage 2 with

    deepreason stop-report <root> --config <your-config.yaml>

which is the one path in the report that reads a YAML at all. Structural,
not a promise: the `yaml` import lives inside the single function that
builds that diff, so no other code path can reach it.
`check: python -c "
import ast, inspect
from deepreason.application import stop_report as m
tree = ast.parse(inspect.getsource(m))
holders = set()
for node in ast.walk(tree):
    if not isinstance(node, (ast.Import, ast.ImportFrom)):
        continue
    if not any(a.name.split('.')[0] == 'yaml' for a in node.names):
        continue
    holders.update(f.name for f in ast.walk(tree)
                   if isinstance(f, ast.FunctionDef)
                   and any(c is node for c in ast.walk(f)))
assert holders == {'_config_diff'}, holders
"`

## Stage 2 — the compiled manifest

`run-manifest.json` in the run root. This is the first stage that is
RECORD: typed, frozen with the run, replayable. Per-seat model, endpoint,
`max_tokens`, `timeout_s`, `reasoning`, and every policy the run compiled.

Reveal it:

    python -c "import json;m=json.load(open('<root>/run-manifest.json'));
    print(json.dumps(m['roles'], indent=1))"

Not every field survives into it. That is stage 3.
`check: python -c "
import json, pathlib
p = pathlib.Path('src/deepreason/run_manifest.py').read_text()
assert 'ENGINE_CONFIG_FIELD_NOT_CARRIED' in p
"`

## Stage 3 — run-time restoration from notices

Some engine-config fields are NOT carried by the compiled manifest. They
are recorded as `ENGINE_CONFIG_FIELD_NOT_CARRIED` compile notices and
restored at run time FROM those notices. The setting does take effect —
but the manifest alone does not show it, so a reader that inspects only
stage 2 will report the field as unset when it was set.

Reveal it:

    python -c "import json;m=json.load(open('<root>/run-manifest.json'));
    [print(n['pointer'], n['value']) for n in m['compile_notices']
     if n['code']=='ENGINE_CONFIG_FIELD_NOT_CARRIED']"

The stop report marks each of these `restored at run time from notice`
and carries its pointer, value and resolution.
`check: grep -q "restored at run time from notice" src/deepreason/application/stop_report.py`

**The second arm: a notice with no `value` discloses and does NOT restore.**
`CompileNoticeV1.value` is optional, and `_carried_config_values` skips a
notice that carries nothing before it checks anything else. Preparation uses
that arm for the values the HOST owns on the managed path — the six in
`_config_for_profile`'s `owned` that a configuration may state and never get
(`DR-CON-seats`). So under one code there are two facts: with a value, the
setting took effect and the manifest alone does not show it; without one, the
setting did NOT take effect and the host's own value did. A reader that treats
the code alone as "restored" tells an operator their configuration ran when it
did not, which is why the report branches on `value` rather than on the code.

The disclosure rides that code deliberately rather than a new one:
`qualification_subject_payload` strips exactly this code from the subject, so
saying a value was taken costs no home a qualification battery
(`DR-INV-frozen-surfaces` §5, the 2026-08-28 grant, whose rule this follows
rather than routes around).
`check: python -c "
from datetime import datetime, timezone
from deepreason.config import Config
from deepreason.preparation import build_preparation_manifest
from deepreason.provider_profile import ProviderProfileV1
from deepreason.qualification import qualification_subject_digest
p = ProviderProfileV1.create(provider='openai', endpoint='https://api.example.com/v1', model_id='model-a', model_revision='rev-a', family='family-a', context_window_tokens=262144, maximum_completion_tokens=4096, credential_env='DEEPREASON_TEST_KEY')
stamp = datetime(2026, 7, 23, tzinfo=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
base = build_preparation_manifest(p, question='Why is the sky blue?', compiled_at=stamp)
taken = build_preparation_manifest(p, question='Why is the sky blue?', compiled_at=stamp, config=Config.model_validate({'engine_profile': 'mini'}))
named = [n for n in (taken.compile_notices or ()) if n.pointer == '/engine_config/engine_profile']
assert len(named) == 1, named
assert named[0].code == 'ENGINE_CONFIG_FIELD_NOT_CARRIED'
assert named[0].value is None, 'a host-owned disclosure must not be a road back'
assert qualification_subject_digest(taken, p) == qualification_subject_digest(base, p)
"`

## Stage 4 — what the seat actually receives

The wire request one seat actually got: the rendered pack, the wire
contract, and the profile-resolved knob values. Recorded per attempt in
`log.jsonl` under `llm.attempt_trace[]` — `endpoint_id`, `seat`,
`model_profile`, `max_tokens`, `timeout_s`, `transport_diagnostics`,
`split_legs`.

Reveal it:

    python -c "
    import json
    for line in open('<root>/log.jsonl'):
        e=json.loads(line)
        if e.get('llm'):
            print(json.dumps(e['llm']['attempt_trace'][0], indent=1)); break"

`check: python -c "
import inspect
from deepreason.application import stop_report as m
src = inspect.getsource(m)
for field in ('attempt_trace', 'transport_diagnostics', 'split_legs', 'endpoint_id'):
    assert field in src, field
"`

## The traps, stated flatly

Each of these has cost a real window real time.

**1. Six engine-config fields are not carried by the manifest.** They are
restored at run time from notices (stage 3). Reading the manifest alone
reports them absent when they were set. The list is not memorised — it is
whatever the notices say; on the P-A1 root it is
`ADJUDICATION_STATUS_AUTHORITY_ENABLED`, `ENGAGED_CRITICISM_AUTHORITY`,
`JUDGE_SEATS_ENABLED`, `JUDGE_SUMMONS_PER_CYCLE`,
`LEGACY_CRITICISM_ENABLED`, `SCHOOL_SEATS_ENABLED`. Carrying them
properly is parked, not fixed
(`experiments/2026-09-03-change-stop-report/PARKED.md`).

**2. An omitted `reasoning` knob is the provider's DEFAULT, not "off".**
`"reasoning": null` in a manifest role means the harness sent no value,
so the provider applies its own default — which for a reasoning model can
be maximum effort, and can burn the whole completion cap on hidden
reasoning. The stop report renders it `omitted → provider default` for
exactly this reason, and never the word "off".
`check: grep -q "omitted → provider default" src/deepreason/application/stop_report.py`

**3. The split protocol arms on an omitted knob.** A seat with no explicit
reasoning value can take the split reason/extract path, whose extraction
leg has its own much smaller `max_tokens`. A truncation there looks like a
model failure and is a configuration consequence.

**4. The reasoning knob is NOT uniform across contracts on one model.**
Setting a seat's `reasoning` to `low` can pass 20/20 on one form and 5/20
on another, on the same model and endpoint. Measured, not theorised:
`experiments/2026-09-02-live-p-a2-corrected/RESULTS.md` segments 4 and 6 —
one pair went 5/20 at `low` and 20/20 at default effort, with everything
else byte-identical. So "the model can fill forms" is never a statement
about a model; it is a statement about a model × contract × knob.

**5. Qualification caches by subject digest, and the digest is the
filename.** `<home>/qualification-cache/<subject_digest>.json`. Same home
+ same provider profile + same opt-ins is a ~1 s cache hit; change any of
them and the full battery re-runs (~14 minutes). A cached PASS is
evidence about the SUBJECT, not about today.

**6. `deepreason frontier` prints the problem registry, not the artifact
frontier.** The name misleads; do not read it as the surviving-artifact
set.

**7. Env-var switches exist only on experiment branches.** They are not
configuration, are not carried in any manifest, and cannot be cited about
a run on `main`.

## Where to change what

| To find out... | Read | Command |
|---|---|---|
| what you asked for | your YAML | `cat` it — and remember it is not evidence |
| what compiled | `run-manifest.json` | `deepreason stop-report <root>` §1 |
| what was restored from a notice | `compile_notices` | `deepreason stop-report <root>` §1 |
| what the seat received | `log.jsonl` `attempt_trace` | `deepreason stop-report <root>` §3 |
| whether the seat could ever do it | the qualification record | `deepreason stop-report <root>` §2 |
| whether the stop was config, environment, model or harness | all of the above | `deepreason stop-report <root>` §4 |
| whether you wrote one thing and got another | your YAML vs the manifest | `deepreason stop-report <root> --config <f>` |

## Traps in reading this document

The stop report is a READER. It ranks four boxes by evidence and never
asserts a defect; a box marked `SUPPORTED` means the record carries
evidence for it, not that the thing is broken. `HARNESS` is claimable only
when the other three are `RULED OUT` with cited evidence.
`check: python -m pytest tests/test_stop_report.py -k "never_asserts_a_defect or harness_box" -q`

A seat that passed its form at full marks did not lose the ability between
qualification and the run. When the report says
`passed qualification 20/20`, look at stages 1-3 before the model.
`check: python -m pytest tests/test_stop_report.py -k passed_qualification_at_full_marks -q`
