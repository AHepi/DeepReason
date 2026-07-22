"""Provider setup helpers and retired Easy execution scaffolding.

The historical website execution facade is fail-closed. Managed V6
question-to-run preparation is internal here; public CLI and MCP wiring land
in a later bounded tranche.

Key handling: the typed provider profile holds only a credential environment
variable name. The wizard stores a newly supplied value separately in
``~/.deepreason/credentials`` (chmod 0600); an existing environment or stored
credential is reused without asking the operator to paste it again."""

import getpass
import os
import re
import stat
from pathlib import Path

from deepreason.provider_profile import (
    ProviderProfileV1,
    setup_provider_profile_path,
    write_provider_profile,
)
from deepreason.run_manifest import infer_model_family, infer_provider


class EasyV6PreparationRequired(RuntimeError):
    """A retired Easy execution entry cannot prepare a canonical V6 run."""

    code = "V6_PREPARATION_REQUIRED"

    def __init__(self) -> None:
        super().__init__(
            f"{self.code}: Easy execution is retired; use an operator-prepared "
            "bound and qualified V6 root until managed preparation is implemented"
        )


def _preparation_required() -> None:
    raise EasyV6PreparationRequired()

# Generic website smoke script: loads, renders something, survives two
# seconds of virtual time. Deliberately minimal — DOM assertions gate only
# "it is a working page"; QUALITY criticism is the argumentative and vision
# critics' job (a rich frozen script can't be written for an app we haven't
# seen; per-app scripts remain the expert surface's power tool).
WEBSITE_SCRIPT: list[dict] = [
    {"op": "assert_js", "expr": "document.body && document.body.children.length > 0"},
    {"op": "screenshot"},
    {"op": "tick", "ms": 2000},
    {"op": "assert_js",
     "expr": "!!(document.title && document.title.trim()) || "
             "!!document.querySelector('h1,h2,header')"},
    {"op": "screenshot"},
]

_DESCRIPTION_TEMPLATE = """Build this website: {description}

Each candidate's `content` MUST be ONE complete, self-contained HTML5
document (<!doctype html> through </html>) with ALL CSS and JavaScript
inline — no external files, no CDN links, no network requests. It must
render meaningful content immediately when opened as a local file, look
polished (real layout, spacing, a deliberate color scheme), and work on
both desktop and mobile widths. Interactive behavior must actually work.
Differ substantively across candidates (different layout/structure and
visual direction), not cosmetic rewordings."""

# Binding for candidates AND critics: the critic pack renders the problem
# statement, so this text is what stops unbounded scope-expansion criticism
# ("lacks accessibility provisions", "no data-minimisation policy") from
# refuting every finite document — observed live against plan candidates.
_SCOPE_NOTE = """
SCOPE (binding for candidates and critics alike): this is a small,
self-contained, client-only website delivered as ONE local HTML file — no
server, no accounts, no analytics, and no data leaving the browser. A FAULT
is a missing or wrong element that would make the finished website fail its
stated purpose for its user. Proposals to ADD scope (compliance programs,
integrations, infrastructure, enterprise concerns) are design choices, not
faults."""

_PLAN_TEMPLATE = """Write a PRODUCT PLAN for this website: {description}

Each candidate's `content` MUST be one plan document in plain prose or
markdown — NOT code, NOT HTML. It must cover: the pages, the feature list,
the key interactions, a content inventory (what text/data actually appears),
and concrete acceptance criteria a reviewer could check one by one. Be
specific enough that a designer could work from the plan alone. The content
inventory must supply the actual headings, labels, explanatory copy, facts,
and data the page will display—not placeholders or descriptions such as
"educational text" or "a philosophical question." When motion is requested,
the plan must apply the user's system-level `prefers-reduced-motion` setting
before any animation starts; a manual toggle may supplement but cannot replace
that automatic behavior. Differ
substantively across candidates (different scopes and priorities), not
rewordings.
""" + _SCOPE_NOTE

_DESIGN_TEMPLATE = """Produce a DESIGN SPECIFICATION for this website:
{description}

It must implement the plan shown in FOUNDATION faithfully — deviations from
the plan are criticism bait. Each candidate's `content` MUST be one design
document in plain prose or markdown—not implementation HTML, JavaScript, or
CSS—with one exception: the chunked workflow's explicitly required fenced
COMPONENT MANIFEST is allowed as structured design metadata. Cover layout per
page, visual direction (palette, typography, spacing), component inventory,
interaction and state behavior, and the responsive strategy. Differ
substantively across candidates (different layouts and visual directions),
not rewordings.
""" + _SCOPE_NOTE

_BUILD_TEMPLATE = (
    "Implement the design specification shown in FOUNDATION faithfully — "
    "its layout, palette, components, and interactions are the adjudicated "
    "groundwork, not suggestions.\n\n" + _DESCRIPTION_TEMPLATE + "\n" + _SCOPE_NOTE
)

# ---- chunked pipeline templates (manifest.py) -------------------------- #
# The chunked build never asks one call for a whole page: the design stage
# declares a component manifest, each component is its own bounded problem,
# and repository code assembles the accepted fragments deterministically.

_MANIFEST_NOTE = '''
The design MUST end with a fenced COMPONENT MANIFEST block exactly in this
shape (JSON inside a ```manifest fence):

```manifest
{{
  "title": "<page title>",
  "libs": ["classless"],
  "art_direction": null,
  "dependencies": [],
  "components": [
    {{"name": "header", "purpose": "one sentence", "element_id": "site-header",
      "css_prefix": "hd-", "js_exports": [], "js_uses": [],
      "events_emitted": [], "events_listened": [], "libs": [],
      "runtime_imports": [], "order": 0}}
  ]
}}
```

Manifest rules (machine-checked): 2-8 components, each small enough to
build alone (its fragment must fit {chunk_max} characters); names,
element_ids, css_prefixes and orders unique; js_exports are the
window.<name> functions a component defines for the others; js_uses may
name only other components' exports; custom events must be declared on
both the emitting and listening component. "libs" selects from the
vendored catalog — already-styled infrastructure that costs the build
nothing: {libs}. Choose libs deliberately: selections are design
decisions on the record, criticizable like everything else.'''

_IMPORT_NOTE = '''

Runtime dependencies are OPTIONAL. Prefer native CSS animation, Web
Animations, IntersectionObserver, sticky positioning, View Transitions and
scroll-driven timelines when they suffice. If the art direction genuinely
needs a project library, describe `art_direction` first (motion language,
scroll narrative, depth structure, transition grammar, texture language,
reduced-motion version and static fallback), then add a dependency request.
Each request declares: capability_slot, artistic_requirement,
technical_capability, preferred_provider, alias, required_features,
intended_components, reduced_motion, fallback, lifecycle and byte budget.
Components may use only the declared alias through
`DeepReasonImports.<alias>`; they never install or directly import packages.
The harness researches and resolves exact bytes after the design survives.
Do not choose a package merely to demonstrate it.'''

_DESIGN_CHUNKED_TEMPLATE = _DESIGN_TEMPLATE + "\n" + _MANIFEST_NOTE + _IMPORT_NOTE

_COMPONENT_TEMPLATE = """Build ONE component of a larger website: {name} — {purpose}

The website: {description}

Each candidate's `content` MUST be ONE self-contained HTML FRAGMENT — never
a full document (no <!doctype>, <html>, <head> or <body> tags) — that
implements just this component, faithful to the design in FOUNDATION.

The component's contract (machine-checked):
- Root element with id="{element_id}"; any extra ids must be
  {element_id}-* (namespaces prevent collisions at assembly).
- Custom CSS in <style> scoped to #{element_id} or .{css_prefix}* classes
  ONLY. The assembled page already ships base styles ({libs}) — do NOT
  re-derive resets, fonts, generic buttons/forms, or page-level layout.
  Custom CSS is for THIS component's design-specific look.
- JavaScript in <script>: define exactly these window exports: {exports}.
  You may call other components' exports: {uses}. Custom events you may
  emit: {emitted}; custom events you may listen for: {listened}.
- Approved project aliases: {runtime_aliases}. Access them only through
  DeepReasonImports.<alias>; direct imports, require(), CDNs and network
  fetching are forbidden. The bounded verified API capsules are:
{api_capsules}
- Import lineage refs required in the candidate interface: {import_refs}.
- Animated code must implement the declared initializer/cleanup lifecycle,
  release listeners/observers/timelines/canvases/RAF callbacks, respect
  prefers-reduced-motion, and preserve the static fallback. JavaScript must
  explicitly query window.matchMedia('(prefers-reduced-motion: reduce)') and
  choose the static path when it matches; a manual motion toggle alone does
  not implement the operating-system preference.
  Lifecycle contract: {lifecycle}.
- HARD SIZE BOUND: at most {max_chars} characters total.

Keep the fragment semantic and minimal; repository code assembles all
components in declared order into the final page.
""" + _SCOPE_NOTE

MAKE_OVERRIDES = {
    # The validated app-run shape (runs/acting_loop_app2): no fuzz/property
    # machinery for a website build; browser evidence + criticism. Schools
    # are NOT zeroed: capture control (spec §11) is mandatory in normal
    # runs — N_SCHOOLS inherits the configured default so the convergence
    # tripwires and the reseed ladder have a population to act on.
    # Disabling capture is an explicit replay/test configuration, never a
    # side effect of the app profile.
    "FLOOR": 1, "K": 4, "VS_K": 2, "FUZZ_N": 0,
    "GEN_PROPOSE_PERIOD": 0, "PROP_PROPOSE_PERIOD": 0,
    "BROWSER_PER_CYCLE": 2, "ARG_CRIT_PER_CYCLE": 2, "CRIT_BATCH_K": 2,
    # 6000: a stage pack must fit the FOUNDATION section (a full plan or
    # design document, capped at FOUNDATION_CHARS) without clipping the
    # trailing directive (_clip truncates the tail).
    "PACK_TOKEN_BUDGET": 6000, "RETRY_MAX": 2,
}

# Provider presets. Every seat combination below has been driven live in a
# committed session record; the model lines are plain YAML the user can edit.
PROVIDERS = {
    "deepseek": {
        "label": "DeepSeek (api.deepseek.com)",
        "env": "DEEPSEEK_API_KEY",
        "vision": False,
        "roles": lambda base, model, env: {
            "conjecturer": _seat(base, model, env, 1.0, 6000, reasoning="none",
                                 logprobs=True),
            "variator": _seat(base, model, env, 1.0, 6000, reasoning="none"),
            "argumentative_critic": _seat(base, model, env, 0.7, 2800, reasoning="none"),
            "synthesizer": _seat(base, model, env, 0.9, 1400, reasoning="none"),
            "summarizer": _seat(base, model, env, 0.3, 1200, reasoning="none"),
        },
        "base": "https://api.deepseek.com",
        "model": "deepseek-v4-pro",
    },
    "ollama": {
        "label": "Ollama Cloud (ollama.com)",
        "env": "OLLAMA_API_KEY",
        "vision": True,
        "roles": lambda base, model, env: {
            "conjecturer": _seat(base, "qwen3-coder:480b", env, 0.9, 7000,
                                 logprobs=False),
            "variator": _seat(base, "qwen3-coder:480b", env, 0.9, 6000),
            "summarizer": _seat(base, "qwen3-coder:480b", env, 0.3, 1200),
            "argumentative_critic": _seat(base, "gpt-oss:120b", env, 0.7, 2800,
                                          provider="openai", reasoning="low"),
            "synthesizer": _seat(base, "gpt-oss:120b", env, 0.9, 1400,
                                 provider="openai", reasoning="low"),
            "vision_critic": _seat(base, "gemini-3-flash-preview", env, 0.2, 1500),
        },
        "base": "https://ollama.com/v1",
        "model": "qwen3-coder:480b",
    },
    "custom": {
        "label": "Other (any OpenAI-compatible URL)",
        "env": "LLM_API_KEY",
        "vision": False,
        "roles": lambda base, model, env: {
            "conjecturer": _seat(base, model, env, 1.0, 6000, logprobs=False),
            "variator": _seat(base, model, env, 1.0, 6000),
            "argumentative_critic": _seat(base, model, env, 0.7, 2800),
            "synthesizer": _seat(base, model, env, 0.9, 1400),
            "summarizer": _seat(base, model, env, 0.3, 1200),
        },
        "base": None,  # asked interactively
        "model": None,
    },
    # A deliberately single-model profile for controlled operator studies.
    # It is separate from the general Ollama preset above, which intentionally
    # mixes models by role.  Here every enabled role, including judges and the
    # visual critic, is pinned to the same concrete cloud model id.
    "gemma4_31b": {
        "label": "Ollama Cloud — Gemma 4 31B everywhere",
        "env": "OLLAMA_API_KEY",
        "vision": True,
        "roles": lambda base, model, env: {
            "conjecturer": _seat(base, model, env, 0.9, 7000,
                                 provider="ollama", reasoning="none", logprobs=False),
            "variator": _seat(base, model, env, 0.9, 6000,
                               provider="ollama", reasoning="none"),
            "argumentative_critic": _seat(base, model, env, 0.7, 3200,
                                           provider="ollama", reasoning="none"),
            "defender": _seat(base, model, env, 0.5, 2000,
                              provider="ollama", reasoning="none"),
            "judge": [
                _seat(base, model, env, 0.0, 2600, provider="ollama", reasoning="none"),
                _seat(base, model, env, 0.0, 2600, provider="ollama", reasoning="none"),
            ],
            "synthesizer": _seat(base, model, env, 0.8, 2500,
                                  provider="ollama", reasoning="none"),
            "summarizer": _seat(base, model, env, 0.3, 1600,
                                 provider="ollama", reasoning="none"),
            "vision_critic": _seat(base, model, env, 0.2, 2500,
                                   provider="ollama", reasoning="none"),
            "property_designer": _seat(base, model, env, 0.7, 4000,
                                        provider="ollama", reasoning="none"),
            "thesis": _seat(base, model, env, 0.3, 6000,
                            provider="ollama", reasoning="none"),
        },
        "base": "https://ollama.com/v1",
        "model": "gemma4:31b",
    },
}


def _seat(base, model, env, temperature, max_tokens, provider=None,
          reasoning=None, logprobs=None):
    seat = {"endpoint": base, "model": model, "temperature": temperature,
            "max_tokens": max_tokens, "json_mode": True, "api_key_env": env}
    if provider:
        seat["provider"] = provider
    if reasoning is not None:
        seat["reasoning"] = reasoning
    if logprobs is not None:
        seat["logprobs"] = logprobs
    return seat


def base_dir() -> Path:
    return Path(os.environ.get("DEEPREASON_HOME") or Path.home() / ".deepreason")


def credentials_path() -> Path:
    return base_dir() / "credentials"


def config_path() -> Path:
    return base_dir() / "engine.yaml"


def load_credentials() -> int:
    """Inject stored keys into the environment (existing variables win).
    Returns how many were loaded. Safe to call when nothing is stored."""
    path = credentials_path()
    if not path.exists():
        return 0
    loaded = 0
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        if name.strip() and value.strip() and name.strip() not in os.environ:
            os.environ[name.strip()] = value.strip()
            loaded += 1
    return loaded


def save_credential(name: str, key: str) -> Path:
    """Merge NAME=key into the credentials file, owner-read-write only."""
    path = credentials_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    if path.exists():
        lines = [ln for ln in path.read_text().splitlines()
                 if ln.strip() and not ln.startswith(f"{name}=")]
    lines.append(f"{name}={key}")
    path.write_text("\n".join(lines) + "\n")
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 0600
    return path


def _stored_credential_present(name: str) -> bool:
    path = credentials_path()
    if not path.is_file() or path.is_symlink():
        return False
    for line in path.read_text().splitlines():
        candidate, separator, value = line.partition("=")
        if separator and candidate.strip() == name and value.strip():
            return True
    return False


def _positive_capacity(value, *, label: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} must be a positive integer") from error
    if isinstance(value, bool) or parsed <= 0 or str(value).strip() != str(parsed):
        raise ValueError(f"{label} must be a positive integer")
    return parsed


def setup_wizard(
    input_fn=input,
    getpass_fn=None,
    *,
    provider: str | None = None,
    endpoint: str | None = None,
    model: str | None = None,
    model_revision: str | None = None,
    family: str | None = None,
    context_window_tokens: int | None = None,
    maximum_completion_tokens: int | None = None,
    credential_env: str | None = None,
) -> Path:
    """Write one strict setup provider profile, interactively or explicitly."""
    getpass_fn = getpass_fn or getpass.getpass
    print("Let's set DeepReason up (one time, ~30 seconds).\n")
    preset = None
    if provider is None:
        keys = list(PROVIDERS)
        for i, key in enumerate(keys, 1):
            print(f"  {i}) {PROVIDERS[key]['label']}")
        while True:
            raw = input_fn(
                f"\nWhich AI provider do you use? [1-{len(keys)}]: "
            ).strip()
            if raw in {str(i) for i in range(1, len(keys) + 1)}:
                provider = keys[int(raw) - 1]
                preset = PROVIDERS[provider]
                break
            print("Please answer with a number from the list.")
    elif provider in PROVIDERS:
        preset = PROVIDERS[provider]

    endpoint = endpoint or (preset and preset["base"])
    model = model or (preset and preset["model"])
    credential_env = credential_env or (preset and preset["env"])
    if endpoint is None:
        endpoint = input_fn("Endpoint URL (e.g. https://api.example.com/v1): ").strip()
    if model is None:
        model = input_fn("Model name: ").strip()
    if credential_env is None:
        credential_env = input_fn("Credential environment variable name: ").strip()
    if context_window_tokens is None:
        context_window_tokens = _positive_capacity(
            input_fn("Finite model context-window tokens: ").strip(),
            label="context-window capacity",
        )
    else:
        context_window_tokens = _positive_capacity(
            context_window_tokens, label="context-window capacity"
        )
    if maximum_completion_tokens is None:
        maximum_completion_tokens = _positive_capacity(
            input_fn("Finite maximum completion tokens: ").strip(),
            label="maximum completion capacity",
        )
    else:
        maximum_completion_tokens = _positive_capacity(
            maximum_completion_tokens, label="maximum completion capacity"
        )

    provider_kind = infer_provider(endpoint) if preset is not None else provider
    if provider_kind is None:
        provider_kind = infer_provider(endpoint)
    profile = ProviderProfileV1.create(
        provider=provider_kind,
        endpoint=endpoint,
        model_id=model,
        model_revision=model_revision,
        family=family or infer_model_family(model, provider_kind),
        context_window_tokens=context_window_tokens,
        maximum_completion_tokens=maximum_completion_tokens,
        credential_env=credential_env,
    )
    path = write_provider_profile(profile, setup_provider_profile_path())
    already_available = bool(os.environ.get(credential_env, "").strip()) or (
        _stored_credential_present(credential_env)
    )
    if not already_available:
        key = ""
        while not key:
            key = getpass_fn("Paste your API key (input stays hidden): ").strip()
        save_credential(credential_env, key)

    print(f"\nDone. Provider profile: {path}")
    if already_available:
        print(f"Credential reference: {credential_env} (already available)")
    else:
        print(f"Credential stored: {credentials_path()} (only your user can read it)")
    print("\nProvider configuration saved. Qualification remains an explicit action.")
    return path


def seed_website(harness, description: str):
    """Register the generic browser smoke commitment + the website problem."""
    from deepreason.browser import browser_commitment
    from deepreason.ontology import Problem, ProblemProvenance

    commitment = browser_commitment(WEBSITE_SCRIPT)
    if commitment.id not in harness.commitments:
        harness.register_commitment(commitment)
    return harness.register_problem(Problem(
        id="pi-website",
        description=_DESCRIPTION_TEMPLATE.format(description=description.strip()),
        criteria=[commitment.id],
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
    ))


def _stage_gate(name: str, expr: str):
    """Light mechanical stage gate, content-addressed like lineage-ref: the
    predicate is frozen into the id, so verdicts are replay-stable."""
    from deepreason.canonical import canonical_json, sha256_hex
    from deepreason.ontology import Commitment

    return Commitment(id=f"{name}@{sha256_hex(canonical_json(expr))[:12]}",
                      eval=f"predicate:{expr}")


# A real document, not an HTML file emitted a stage early.
_PLAN_GATE_EXPR = "len(content) > 400 and 'doctype' not in content.lower()[:200]"
_DESIGN_GATE_EXPR = "len(content) > 600 and 'doctype' not in content.lower()[:200]"


def seed_plan(harness, description: str):
    """Stage 1: product-plan problem. Prose criteria only — no browser
    commitment, so browser/vision/research machinery no-ops for it."""
    from deepreason.ontology import Problem, ProblemProvenance

    gate = _stage_gate("plan-doc", _PLAN_GATE_EXPR)
    if gate.id not in harness.commitments:
        harness.register_commitment(gate)
    return harness.register_problem(Problem(
        id="pi-plan",
        description=_PLAN_TEMPLATE.format(description=description.strip()),
        criteria=[gate.id],
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
    ))


def seed_design(harness, description: str, plan_id: str):
    """Stage 2: design problem, lineage-bound to the surviving plan — every
    design MUST declare dependence on it (program:lineage_ref refutes the
    rest mechanically) and the plan's full text renders as the pack's
    FOUNDATION section."""
    from deepreason.ontology import Problem, ProblemProvenance
    from deepreason.unification.isolation import lineage_ref_commitment

    gate = _stage_gate("design-doc", _DESIGN_GATE_EXPR)
    lineage = lineage_ref_commitment([plan_id])
    for kappa in (gate, lineage):
        if kappa.id not in harness.commitments:
            harness.register_commitment(kappa)
    return harness.register_problem(Problem(
        id="pi-design",
        description=_DESIGN_TEMPLATE.format(description=description.strip()),
        criteria=[gate.id, lineage.id],
        provenance=ProblemProvenance.model_validate(
            {"trigger": "seed", "from": [plan_id]}),
    ))


def seed_build(harness, description: str, design_id: str):
    """Stage 3: the build problem — browser smoke commitment plus lineage
    binding to the surviving design. Keeps the id `pi-website` so export
    semantics are unchanged."""
    from deepreason.browser import browser_commitment
    from deepreason.ontology import Problem, ProblemProvenance
    from deepreason.unification.isolation import lineage_ref_commitment

    browser = browser_commitment(WEBSITE_SCRIPT)
    lineage = lineage_ref_commitment([design_id])
    for kappa in (browser, lineage):
        if kappa.id not in harness.commitments:
            harness.register_commitment(kappa)
    return harness.register_problem(Problem(
        id="pi-website",
        description=_BUILD_TEMPLATE.format(description=description.strip()),
        criteria=[browser.id, lineage.id],
        provenance=ProblemProvenance.model_validate(
            {"trigger": "seed", "from": [design_id]}),
    ))


def seed_design_chunked(harness, description: str, plan_id: str):
    """Stage 2 (chunked): the design problem additionally requires a valid
    COMPONENT MANIFEST (program:manifest_wf) — the manifest lives inside the
    ordinary, criticizable design artifact, never outside the graph."""
    from deepreason import assets
    from deepreason.manifest import manifest_commitment
    from deepreason.ontology import Problem, ProblemProvenance
    from deepreason.unification.isolation import lineage_ref_commitment

    gate = _stage_gate("design-doc", _DESIGN_GATE_EXPR)
    manifest_gate = manifest_commitment(assets.catalog_names())
    lineage = lineage_ref_commitment([plan_id])
    for kappa in (gate, manifest_gate, lineage):
        if kappa.id not in harness.commitments:
            harness.register_commitment(kappa)
    return harness.register_problem(Problem(
        id="pi-design",
        description=_DESIGN_CHUNKED_TEMPLATE.format(
            description=description.strip(),
            chunk_max=4000,
            libs=", ".join(sorted(assets.catalog_names())),
        ),
        criteria=[gate.id, manifest_gate.id, lineage.id],
        provenance=ProblemProvenance.model_validate(
            {"trigger": "seed", "from": [plan_id]}),
    ))


def seed_component(harness, description: str, design_id: str, manifest,
                   spec, chunk_max: int, suffix: str = "",
                   repair_of: str | None = None, resolved_imports=None):
    """One component problem per manifest entry, seeded once the design
    survivor is known. Criteria: the fragment contract (component_wf, spec
    frozen in) + lineage binding to the design — candidates flow through the
    ordinary Conj -> Crit -> Adj machinery like any other problem. A repair
    problem (suffix != "") is a SUCCESSOR spawned from the implicated
    component artifact: prior history is never mutated."""
    from deepreason.manifest import component_commitment
    from deepreason.ontology import Problem, ProblemProvenance
    from deepreason.unification.isolation import lineage_ref_commitment

    allowed_uses = sorted(set(spec.js_uses))
    import_ids = [resolved_imports.record_id] if (
        resolved_imports is not None and spec.runtime_imports
    ) else []
    contract = component_commitment(spec, chunk_max, allowed_uses, import_ids)
    lineage = lineage_ref_commitment([design_id])
    for kappa in (contract, lineage):
        if kappa.id not in harness.commitments:
            harness.register_commitment(kappa)
    libs = sorted(set(manifest.libs) | set(spec.libs)) or ["baseline only"]
    capsules = []
    if resolved_imports is not None:
        from deepreason.programs import content_text

        for request, capsule_id in zip(
            resolved_imports.requests, resolved_imports.capsule_ids, strict=True
        ):
            if request.alias in spec.runtime_imports:
                capsules.append(content_text(harness.state.artifacts[capsule_id], harness.blobs))
    provenance = (
        {"trigger": "successor", "from": [repair_of]}
        if repair_of else {"trigger": "seed", "from": [design_id]}
    )
    return harness.register_problem(Problem(
        id=f"pi-comp-{spec.name}{suffix}",
        description=_COMPONENT_TEMPLATE.format(
            name=spec.name,
            purpose=spec.purpose or "see the design",
            description=description.strip(),
            element_id=spec.element_id,
            css_prefix=spec.css_prefix,
            libs=", ".join(libs),
            exports=", ".join(spec.js_exports) or "none",
            uses=", ".join(spec.js_uses) or "none",
            emitted=", ".join(spec.events_emitted) or "none",
            listened=", ".join(spec.events_listened) or "none",
            runtime_aliases=", ".join(spec.runtime_imports) or "none",
            api_capsules="\n".join(capsules) or "  none",
            import_refs=", ".join(import_ids) or "none",
            lifecycle=spec.lifecycle.model_dump_json(),
            max_chars=spec.max_chars or chunk_max,
        ),
        criteria=[contract.id, lineage.id],
        provenance=ProblemProvenance.model_validate(provenance),
    ))


def register_assembly(harness, design_id: str, manifest, chosen: dict,
                      resolved_imports=None, import_policy=None):
    """Deterministic assembly (repository code, no LLM): compose the accepted
    fragments into one page, register the selected vendored libs as import
    artifacts, and register the assembled page carrying DEPENDENCE refs to
    the design (manifest), every component, and every injected lib — full
    traceability, and standard support semantics (a refuted foundation
    suspends the assembly rather than deleting it). The page carries the
    browser smoke commitment and the static integration commitment."""
    from deepreason import assets
    from deepreason.browser import browser_commitment
    from deepreason.manifest import assemble_html, integration_commitment
    from deepreason.ontology import Problem, ProblemProvenance, Provenance
    from deepreason.ontology.artifact import Interface, Ref, RefRole
    from deepreason.programs import content_text

    lib_names = sorted(
        set(manifest.libs) | {lib for c in manifest.components for lib in c.libs}
    )
    catalog = assets.catalog()
    lib_css = {name: catalog[name] for name in lib_names}
    lib_ids = []
    for name in lib_names:
        lib = harness.create_artifact(
            f"/* vendored:{name} */\n" + lib_css[name],
            codec="code:css",
            provenance=Provenance(role="import"),
        )
        lib_ids.append(lib.id)

    fragments = {
        name: content_text(harness.state.artifacts[aid], harness.blobs)
        for name, aid in chosen.items()
    }
    runtime_css = ""
    runtime_js = ""
    runtime_ids: list[str] = []
    bundle_metadata_id = None
    if resolved_imports is not None:
        from deepreason.config import ImportPolicy
        from deepreason.imports import ImportService

        service = ImportService(harness, import_policy or ImportPolicy())
        bundle = service.bundle_components(manifest, fragments, resolved_imports)
        fragments = bundle.fragments
        runtime_css = bundle.css
        runtime_js = bundle.javascript
        runtime_ids = resolved_imports.dependence_ids
        lifecycle_id = None
        if bundle.lifecycle_source:
            lifecycle = harness.create_artifact(
                bundle.lifecycle_source,
                codec="code:javascript",
                interface=Interface(refs=[
                    Ref(target=design_id, role=RefRole.DEPENDENCE),
                    Ref(target=resolved_imports.record_id, role=RefRole.DEPENDENCE),
                ]),
                provenance=Provenance(role="import"),
            )
            lifecycle_id = lifecycle.id
            runtime_ids.append(lifecycle.id)
        metadata_refs = [
            Ref(target=resolved_imports.toolchain_id, role=RefRole.DEPENDENCE),
            Ref(target=resolved_imports.record_id, role=RefRole.DEPENDENCE),
        ]
        if lifecycle_id:
            metadata_refs.append(Ref(target=lifecycle_id, role=RefRole.DEPENDENCE))
        metadata = harness.create_artifact(
            __import__("json").dumps(bundle.metadata, sort_keys=True),
            codec="json",
            interface=Interface(refs=metadata_refs),
            provenance=Provenance(role="import"),
        )
        bundle_metadata_id = metadata.id
        runtime_ids.append(metadata.id)
    html = assemble_html(
        manifest, fragments, lib_css, assets.baseline(), runtime_css, runtime_js
    )

    browser = browser_commitment(WEBSITE_SCRIPT)
    integration = integration_commitment(manifest)
    for kappa in (browser, integration):
        if kappa.id not in harness.commitments:
            harness.register_commitment(kappa)
    if "pi-website" not in harness.state.problems:
        harness.register_problem(Problem(
            id="pi-website",
            description="the assembled website (deterministic composition of "
                        "the accepted design manifest and component fragments)",
            criteria=[browser.id, integration.id],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": [design_id]}),
        ))
    refs = [Ref(target=design_id, role=RefRole.DEPENDENCE)]
    refs += [Ref(target=aid, role=RefRole.DEPENDENCE) for aid in sorted(chosen.values())]
    refs += [Ref(target=lid, role=RefRole.DEPENDENCE) for lid in lib_ids]
    refs += [Ref(target=rid, role=RefRole.DEPENDENCE) for rid in runtime_ids]
    interface = Interface(refs=refs, commitments=[browser.id, integration.id])
    assembled = harness.create_artifact(
        html,
        codec="code:html",
        interface=interface,
        provenance=Provenance(role="seed"),
        problem_id="pi-website",
    )
    measure = ["assembled", assembled.id, *sorted(chosen)]
    if bundle_metadata_id:
        measure.extend(["bundle-metadata", bundle_metadata_id])
    harness.record_measure(inputs=measure)
    return assembled


def integration_criticism(harness, assembled_id: str, manifest, cfg,
                          browser_backend=None) -> list[str]:
    """Integration criticism over the WHOLE page: the static integration
    commitment (duplicate ids, missing mounts, unmet dependencies, silent
    events) through the ordinary crit_program verdict/warrant path, plus the
    executable browser smoke run when a backend is available. Locally valid
    components can still compose into a broken application — this is where
    that shows up. Returns the manifest component names implicated by a
    static failure (for TARGETED repair problems, never a full rebuild)."""
    import json as _json

    from deepreason.manifest import integration_commitment, integration_wf
    from deepreason.rules.crit import crit_program

    crit_program(harness, assembled_id)
    if browser_backend is not None:
        from deepreason.rules.act import needs_browser_run, run_browser_evidence

        if needs_browser_run(harness, assembled_id):
            run_browser_evidence(harness, assembled_id, browser_backend, cfg)
    kappa = integration_commitment(manifest)
    verdict, trace = integration_wf(
        _page_text(harness, assembled_id), kappa.budget
    )
    if verdict == "pass":
        return []
    implicated = list(trace.get("implicated") or [])
    harness.record_measure(
        inputs=["integration-repair", assembled_id,
                _json.dumps(sorted(implicated))]
    )
    return implicated


def _page_text(harness, aid: str) -> str:
    from deepreason.programs import content_text

    return content_text(harness.state.artifacts[aid], harness.blobs)


def pick_survivor(harness, root_pid: str) -> str | None:
    """Deterministic stage survivor: ACCEPTED candidate artifacts addressed
    into the stage's problem family; EARLIEST event_seq wins (the longest-
    standing survivor has faced the most re-criticism sweeps — the most
    corroborated conjecture). Ties break on id."""
    from deepreason.ontology import Status
    from deepreason.scheduler.scheduler import problem_family

    family = problem_family(harness.state, root_pid)
    best: tuple[int, str] | None = None
    for aid, pid in harness.state.addr:
        if pid not in family:
            continue
        artifact = harness.state.artifacts.get(aid)
        if artifact is None or harness.state.status.get(aid) != Status.ACCEPTED:
            continue
        role = artifact.provenance.role.value if artifact.provenance else ""
        if role not in ("conjecturer", "synthesizer"):
            continue
        seq = artifact.provenance.event_seq
        key = (seq if seq is not None else 1 << 62, aid)
        if best is None or key < best:
            best = key
    return best[1] if best else None


def _slug(text: str) -> str:
    words = re.findall(r"[a-z0-9]+", text.lower())[:4]
    return "-".join(words) or "site"


def _fresh(path: Path) -> Path:
    if not path.exists():
        return path
    n = 2
    while Path(f"{path}-{n}").exists():
        n += 1
    return Path(f"{path}-{n}")


def _echo(message: str) -> None:
    print(message, flush=True)  # progress must reach pipes/logs live, not buffered


def _run_stage(harness, cfg, *, label: str, root_pid: str, cycles: int,
               token_budget: int | None, echo, stop_on_survivor: bool,
               min_cycles: int = 1, run_manifest=None) -> dict:
    """Retired scheduler facade retained only for import stability."""
    _preparation_required()


def _first_line(harness, aid: str, limit: int = 100) -> str:
    from deepreason.programs import content_text

    text = content_text(harness.state.artifacts[aid], harness.blobs).strip()
    head = text.splitlines()[0] if text else ""
    return head[:limit].lstrip("# ").strip()


def make(description: str, out: str | None = None, cycles: int = 10,
         token_budget: int | None = 150_000, config: str | None = None,
         root: str | None = None, echo=_echo, staged: bool = True,
         chunked: bool | None = None) -> list[Path]:
    """Fail closed before configuration, root, adapter, or provider activity."""
    _preparation_required()


def _make_chunked(harness, cfg, description: str, out_dir: Path, cycles: int,
                  token_budget: int | None, echo,
                  config_path: Path | None = None, run_manifest=None) -> list[Path]:
    """Retired chunked execution facade retained only for import stability."""
    _preparation_required()

def _make_single(harness, cfg, description: str, out_dir: Path, cycles: int,
                 token_budget: int | None, echo, *, run_manifest=None) -> list[Path]:
    """Retired single-stage execution facade retained only for import stability."""
    _preparation_required()
