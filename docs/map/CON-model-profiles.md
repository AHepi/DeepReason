<!-- DR-CON-model-profiles -->
Verified-at: dd0916fb5
Verify: python -m pytest tests/test_model_profiles_document.py tests/test_model_profile_registry.py -q
Owns: src/deepreason/model_profiles/
Seams: 
Seams-undocumented: llm x model-profiles, model-profiles x scheduler

# Model profiles — a model's settings are a document a human wrote

## What it is

A model profile is one Markdown document, `agent.md`, that a human writes to
say what is known about one model: which reasoning values its provider
documents, which value the emission leg should send, whether thinking can be
switched off at all, where the trace lands for each value, how big its window
is, how fast it is, whether it can obey "respond more compactly", what its
transport does, when this was measured, and the command that re-checks it. The
harness READS that document and holds no per-model opinion of its own. Nothing
ships: the documents live in the operator's home directory, so a harness with
no documents knows nothing about any model, and says so rather than guessing.

This is a CONCEPT and not a subsystem because the package is only its loader.
The thing itself spans `llm/split.py` (which reads a profile instead of a
constant), `scheduler/scheduler.py` (which stamps the installed set into the
run's record) and a directory outside the repo entirely — the shape
`docs/map/SCHEMA.md` gives for `CON-`.

It replaces a constant. `llm/providers.py` used to carry `REASONING_OFF =
"none"` and `llm/split.py` sent it on every emission leg of every model. On
glm-5.3 that value does not stop the thinking, it stops the SEPARATION: the
trace lands in `message.content` ahead of the answer, the 512-token leg is cut
before any JSON, and the cap ratchet then shrinks the budget until the seat
exhausts. See `Traps` below.

## Entry points

`deepreason.model_profiles` is the only legal import surface. A consumer that
reaches into `document` or `registry` directly has left the contract.

| call | answers |
|---|---|
| `resolve(model_id, *, home=None, environ=None)` | this model's profile, or `None` — never an exception for an unknown model |
| `installed(...)` | every profile found, id-keyed |
| `profiles_root(...)` | where the harness is looking |
| `register(profile)` / `unregister(model_id)` | in-process registration, for tests and for a plugin; writes no file |
| `registry_fingerprint(...)` | the identity the run's record stamps |
| `parse_document(text)` | one document's declared block, validated |

`check: python -c "
import deepreason.model_profiles as mp
for name in ('resolve', 'installed', 'profiles_root', 'register', 'unregister', 'registry_fingerprint', 'parse_document', 'ModelProfileV1', 'ModelProfileError'):
    assert name in mp.__all__ and hasattr(mp, name), name
assert mp.resolve('a-model-that-does-not-exist', environ={'DEEPREASON_HOME': '/nonexistent'}) is None
"`

## State it owns

Documents on disk, at `profiles_root()` — `$DEEPREASON_HOME/model-profiles/`,
else `~/.deepreason/model-profiles/`. One directory per model, one `agent.md`
inside it. In-process registrations from `register()` live for the process only.

**The declared `model_id` is the key; the directory name is a convenience.**
Provider ids carry colons (`deepseek-v4-pro:0813`, `gpt-oss:120b`,
`qwen3.5:397b`), and an escaping scheme would be one more thing a human has to
know. The loader scans `*/agent.md` and keys by what each document declares.

`check: python -c "
import pathlib, tempfile
from deepreason.model_profiles import resolve
root = pathlib.Path(tempfile.mkdtemp())
d = root / 'model-profiles' / 'a-directory-named-nothing-like-it'
d.mkdir(parents=True)
(d / 'agent.md').write_text('prose\n\n\`\`\`deepreason-model-profile-v1\nschema: deepreason-model-profile.v1\nmodel_id: declared-id:7b\nmeasured_on: 2026-09-01\n\`\`\`\n')
env = {'DEEPREASON_HOME': str(root)}
assert resolve('declared-id:7b', environ=env) is not None
assert resolve('a-directory-named-nothing-like-it', environ=env) is None
"`

**Nothing ships.** The operator's words of 2026-09-01, deciding where documents
live: "Home directory only, nothing ships". So `src/deepreason/model_profiles/`
contains code and no document, and a fresh container knows nothing about any
model until a human installs one. That is not a gap to be closed later — it is
the requirement. The reference copies in `docs/model-profiles/` are for a human
to read and copy; the loader never reads them.

`check: test -f src/deepreason/model_profiles/registry.py && test -z "$(find src/deepreason/model_profiles -name '*.md' -o -name '*.yaml' -o -name '*.yml')" && ! grep -rn "docs/model-profiles" src/deepreason/`

## The document grammar is total

Exactly one fenced block whose info string is `deepreason-model-profile-v1`.
Zero blocks, two blocks and an unclosed block are each a typed error, never a
guess — a parser free to decide which of two blocks was meant is how a document
comes to say something nobody wrote. `docs/map/SCHEMA.md` states the same rule
for its own `check:` spans, and states the price of the alternative: 72 checks
that looked exactly like checks and never ran. A fenced block of any OTHER kind
is invisible, so a document may show an example without declaring it.

`check: python -c "
from deepreason.model_profiles import parse_document, ModelProfileError, FENCE_INFO
body = 'schema: deepreason-model-profile.v1\nmodel_id: x\nmeasured_on: 2026-09-01\n'
one = '\`\`\`' + FENCE_INFO + '\n' + body + '\`\`\`\n'
codes = []
for text in ('prose only\n', one + '\n' + one, '\`\`\`' + FENCE_INFO + '\n' + body):
    try:
        parse_document(text)
    except ModelProfileError as error:
        codes.append(error.code)
assert codes == ['MODEL_PROFILE_NO_BLOCK', 'MODEL_PROFILE_MULTIPLE_BLOCKS', 'MODEL_PROFILE_UNCLOSED_BLOCK'], codes
assert parse_document('\`\`\`yaml\nmodel_id: decoy\n\`\`\`\n' + one).model_id == 'x'
"`

## A profile DESCRIBES; it never restricts

The operator, 2026-09-01, answering a question about what should happen when a
run config names a value the document does not list: *"These questions miss the
point. Harness is supposed to accommodate all possible future models and
configurations"*. So a configured `reasoning:` value travels to the provider
exactly as written, whatever a document says. `documented_values` is read by
the PROBE and by a human; no dispatch path consults it. The only field the
harness acts on is `extraction_value`, and it acts on it only where it would
otherwise have supplied a constant of its own.

Absence stays absent, for the same reason: every field but `schema`,
`model_id` and `measured_on` defaults to nothing, and the loader supplies no
value the author did not write. A default would be the machine deciding a
model's settings.

`check: python -c "
from deepreason.model_profiles import parse_document, FENCE_INFO
p = parse_document('\`\`\`' + FENCE_INFO + '\nschema: deepreason-model-profile.v1\nmodel_id: x\nmeasured_on: 2026-09-01\n\`\`\`\n')
assert p.reasoning is None and p.can_compact is None and p.context_window_tokens is None
assert p.max_output_tokens is None and p.tokens_per_second is None and p.probe is None
assert p.transport_notes == () and p.evidence == ()
"`

## What reads a profile, and what happens without one

Two consumers, and no others. `llm/adapter.py::_split_plan` resolves the seat's
model through the interface and hands the profile to `plan_split`, which sends
`reasoning.extraction_value` on the emission leg and asks
`reasoning.disabling_values` whether the seat is already thinking-off. And
`cli/main.py::_reasoning_disclosure` says, at launch, what the configured value
will do — as a DISCLOSURE. It used to be a refusal (`REASONING_MUST_BE_DISABLED`)
demanding `reasoning: none`, which on glm-5.3 is the value that breaks it; the
operator's 2026-08-28 law ("Gates are always optional: with warnings") and
2026-09-01 answer ("Harness is supposed to accommodate all possible future
models and configurations") both forbid the veto.

With no document the split protocol stands down with a typed notice and the
seat runs exactly as it did before the protocol existed. Nothing refuses, and
nothing is sent that a human did not either configure or declare.

`check: python -c "
from deepreason.llm.split import plan_split, NOTICE_MODEL_PROFILE_MISSING, NOTICE_PROFILE_DECLARES_NO_REASONING
import inspect
from deepreason.llm.adapter import LLMAdapter
source = inspect.getsource(LLMAdapter._split_plan)
assert 'model_profiles' in source and 'lease.route.model_id' in source, source
plan = plan_split(mode='on', ceiling=4096, extraction_tokens=512, provider='ollama', reasoning='high', profile=None)
assert not plan.armed and plan.notice == NOTICE_MODEL_PROFILE_MISSING and plan.extract_reasoning is None
quiet = plan_split(mode='auto', ceiling=4096, extraction_tokens=512, provider='ollama', reasoning=None, profile=None)
assert quiet.notice == NOTICE_MODEL_PROFILE_MISSING and not quiet.disclosed
assert NOTICE_PROFILE_DECLARES_NO_REASONING != NOTICE_MODEL_PROFILE_MISSING
"`

`check: python -c "
import ast, pathlib
import deepreason.cli.main as main
text = pathlib.Path(main.__file__).read_text()
tree = ast.parse(text)
found = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == '_reasoning_disclosure']
assert len(found) == 1, 'positive anchor: exactly one disclosure function'
function = found[0]
assert 'model_profiles' in ast.get_source_segment(text, function), 'it must ask the document, not a constant'
emitted = [
    node.value
    for node in ast.walk(function)
    if isinstance(node, ast.Constant) and isinstance(node.value, str)
    and node is not function.body[0].value
]
assert not any(v.startswith('REASONING_MUST_BE_DISABLED') for v in emitted), 'the launch refusal code is emitted again'
assert any(v.startswith('MODEL_PROFILE_MISSING') for v in emitted), 'positive anchor: it still discloses'
callers = [
    node for node in ast.walk(tree)
    if isinstance(node, ast.Call) and getattr(node.func, 'id', '') == '_reasoning_disclosure'
]
assert len(callers) == 2, callers
"`

## Invariants

- `DR-INV-frozen-surfaces` — this concept touches none of the five. It reaches
  the run's record through the module-fingerprints event, whose payload
  materializes no state, and it puts nothing in the RunManifest and nothing in
  the qualification subject. Both compile-time roads were measured and rejected
  in `experiments/2026-09-01-change-model-profile-registry/SPEC.md` M3.
- The 2026-08-26 modularity law — adding a model is writing a document, never
  a source edit. `tests/test_model_profile_registry.py` is the check that can
  fail.
- The 2026-08-12 all-configurations law — an unknown model is disclosed, never
  refused; `resolve` returns `None` and no path raises.

## Where to change what

| to do this | edit | test |
|---|---|---|
| describe a new model | write `$DEEPREASON_HOME/model-profiles/<id>/agent.md` — NO source edit | `tests/test_model_profile_registry.py::test_adding_a_model_needs_no_source_edit` |
| add a field to the document | `model_profiles/document.py` | `tests/test_model_profiles_document.py` |
| change where documents are found | `model_profiles/registry.py::profiles_root` | `tests/test_model_profile_registry.py` |
| change what the emission leg sends | the model's own document — NOT the code | `tests/test_split_budget_protocol.py` |
| change what the record stamps | `scheduler/scheduler.py::_record_module_fingerprints` | `tests/test_model_profile_registry.py` |

## Traps

- **A neutral vocabulary is not a per-model fact, and treating it as one killed
  three runs.** `llm/providers.py` carried `REASONING_OFF = "none"` and
  `llm/split.py:163` sent it on every emission leg regardless of model. On
  glm-5.3, `reasoning_effort: "none"` does not stop the thinking — it stops the
  separation, so the trace lands in `message.content` ahead of the answer:
  0/8 clean at `none` against 8/8 clean at `low`, and `none` is also the more
  expensive of the two (64 median completion tokens against 7). P-S1 measured
  it (`git show origin/claude/deepreason-p-s1-commitments-wowcib:experiments/2026-08-31-p-s1-commitments/SEAT_REASONING_FINDINGS.md`);
  P-S1's `MISTAKES.md` M-1 and M-16 record the two deaths it caused, through
  the 512-token emission leg at cycle 0 and the cap ratchet's 1,953-token floor
  at cycle 11; and P-A1 re-ran it verbatim in run `4565139800f5ca02`
  (`experiments/2026-09-01-live-all-modules-p-a1/MONITOR_REVIEW.md`, addendum).
  FIXED 2026-09-01 by this concept: the constant is retired and the emission
  leg sends what the model's own document declares, or stands down.
- **Two documents can disagree about what a provider "accepts", and both be
  right.** The API parameter set for `reasoning_effort` includes `none`; the
  glm-5.3 model page lists `low`, `high`, `max`. The model accepts `none` on
  the wire and behaves badly with it. That is why `documented_values` and
  `trace_destination` are separate fields: collapsing "what the wire takes"
  into "what the model does with it" is the mistake that produced the constant.
- **A missing profile is the normal state, not an error state.** Nothing ships,
  so every model is unknown until a human writes a document. Any design that
  treats "no profile" as exceptional — a raise, a refusal, a warning every
  attempt — will fire on every run in every fresh container. The split
  protocol's stand-down notice is therefore disclosed only under `on`, matching
  the module's own existing rule for a seat that simply does not think.
