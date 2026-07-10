"""The two-command path (spec §13 usability): setup once, then make things.

    deepreason setup                  # pick a provider, paste a key — once
    deepreason make "a recipe website"

Everything here is sugar over the same machinery the expert surface uses —
seed_problem_payload-grade seeding, run_scheduler, views/export — so the
easy path produces the same append-only, replayable record as the hard one.
Nothing is decided here; this module only removes ceremony.

Key handling: the engine config still holds only ``api_key_env`` NAMES
(keys never live in configs, packs, or the log — §1). The wizard stores the
actual key in ~/.deepreason/credentials (chmod 0600, the aws/gh precedent)
and load_credentials() injects it into the process environment at startup,
losing to any variable the user already exported."""

import getpass
import os
import re
import stat
import sys
from pathlib import Path

import yaml

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

_PLAN_TEMPLATE = """Write a PRODUCT PLAN for this website: {description}

Each candidate's `content` MUST be one plan document in plain prose or
markdown — NOT code, NOT HTML. It must cover: the pages, the feature list,
the key interactions, a content inventory (what text/data actually appears),
and concrete acceptance criteria a reviewer could check one by one. Be
specific enough that a designer could work from the plan alone. Differ
substantively across candidates (different scopes and priorities), not
rewordings."""

_DESIGN_TEMPLATE = """Produce a DESIGN SPECIFICATION for this website:
{description}

It must implement the plan shown in FOUNDATION faithfully — deviations from
the plan are criticism bait. Each candidate's `content` MUST be one design
document in plain prose or markdown — NOT code, NOT HTML: layout per page,
visual direction (palette, typography, spacing), component inventory,
interaction and state behavior, and the responsive strategy. Differ
substantively across candidates (different layouts and visual directions),
not rewordings."""

_BUILD_TEMPLATE = (
    "Implement the design specification shown in FOUNDATION faithfully — "
    "its layout, palette, components, and interactions are the adjudicated "
    "groundwork, not suggestions.\n\n" + _DESCRIPTION_TEMPLATE
)

_KNOBS = {
    # The validated app-run shape (runs/acting_loop_app2): no schools/fuzz/
    # property machinery for a website build; browser evidence + criticism.
    "FLOOR": 1, "K": 4, "VS_K": 2, "N_SCHOOLS": 0, "FUZZ_N": 0,
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


def setup_wizard(input_fn=input, getpass_fn=None) -> Path:
    """Two questions: provider, key. Writes ~/.deepreason/engine.yaml (models
    and knobs, editable, NO key) and stores the key separately. Returns the
    config path."""
    getpass_fn = getpass_fn or getpass.getpass
    print("Let's set DeepReason up (one time, ~30 seconds).\n")
    keys = list(PROVIDERS)
    for i, key in enumerate(keys, 1):
        print(f"  {i}) {PROVIDERS[key]['label']}")
    while True:
        raw = input_fn(f"\nWhich AI provider do you use? [1-{len(keys)}]: ").strip()
        if raw in {str(i) for i in range(1, len(keys) + 1)}:
            preset = PROVIDERS[keys[int(raw) - 1]]
            break
        print("Please answer with a number from the list.")
    base, model = preset["base"], preset["model"]
    if base is None:
        base = input_fn("Endpoint URL (e.g. https://api.example.com/v1): ").strip()
        model = input_fn("Model name: ").strip()
    key = ""
    while not key:
        key = getpass_fn("Paste your API key (input stays hidden): ").strip()
    save_credential(preset["env"], key)

    config = {**_KNOBS, "roles": preset["roles"](base, model, preset["env"])}
    if preset["vision"]:
        config["VISION_CRIT_PER_CYCLE"] = 2
    path = config_path()
    path.write_text(
        "# DeepReason engine config — written by `deepreason setup`.\n"
        "# Edit models/limits freely. Your API key is NOT here: it lives in\n"
        f"# {credentials_path()} (private to your user), referenced by name.\n"
        + yaml.safe_dump(config, sort_keys=False)
    )
    print(f"\nDone. Config: {path}")
    print(f"Key stored:  {credentials_path()} (only your user can read it)")
    print('\nTry:  deepreason make "a pomodoro timer website"')
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
               min_cycles: int = 2) -> dict:
    """One staged run_scheduler invocation, selection locked to the stage's
    problem family. The ticker counts candidates addressed into the family
    (successor generations included) and — for plan/design stages — stops
    the stage early once a survivor exists, so leftover cycles flow to the
    build. Returns the invocation's accounting for budget threading."""
    from deepreason.ontology import Status
    from deepreason.ops import run_scheduler
    from deepreason.scheduler.scheduler import problem_family

    stage_cfg = cfg.model_copy(update={"FOCUS_FAMILY": root_pid})
    rounds = [0]

    def ticker(scheduler):
        rounds[0] += 1
        state = scheduler.harness.state
        family = problem_family(state, root_pid)
        mine = {aid for aid, pid in state.addr if pid in family}
        cands = [aid for aid in mine
                 if (a := state.artifacts.get(aid)) is not None
                 and a.provenance
                 and a.provenance.role.value in ("conjecturer", "synthesizer")]
        alive = sum(1 for a in cands if state.status.get(a) == Status.ACCEPTED)
        dead = sum(1 for a in cands if state.status.get(a) == Status.REFUTED)
        echo(f"  {label} round {rounds[0]}/{cycles}: {alive} standing, "
             f"{dead} criticized away")
        if stop_on_survivor and rounds[0] >= min_cycles:
            return pick_survivor(harness, root_pid) is not None
        return False

    _, _, accounting = run_scheduler(
        harness, stage_cfg, cycles, token_budget=token_budget, on_cycle=ticker)
    return accounting


def _first_line(harness, aid: str, limit: int = 100) -> str:
    from deepreason.programs import content_text

    text = content_text(harness.state.artifacts[aid], harness.blobs).strip()
    head = text.splitlines()[0] if text else ""
    return head[:limit].lstrip("# ").strip()


def make(description: str, out: str | None = None, cycles: int = 10,
         token_budget: int | None = 150_000, config: str | None = None,
         root: str | None = None, echo=_echo, staged: bool = True) -> list[Path]:
    """Build a website from a plain-language description the way a person
    would: PLAN it (what pages/features), DESIGN it (layout, look, behavior),
    then BUILD it — each stage's survivor is enforced groundwork for the
    next (lineage commitments + dependence edges, criticizable and on the
    record like everything else). Exports what survives; returns the
    exported file paths. staged=False runs the legacy single-stage loop
    (programmatic/tests only)."""
    from deepreason.config import load
    from deepreason.harness import Harness
    from deepreason.ontology import Status
    from deepreason.views.export import export_run

    load_credentials()
    cfg_path = Path(config) if config else config_path()
    if not cfg_path.exists():
        if config is None and sys.stdin.isatty():
            echo("First run — let's set up your AI provider.\n")
            cfg_path = setup_wizard()
            echo("")
        else:
            raise SystemExit(
                "No engine config found. Run `deepreason setup` once first "
                f"(looked for {cfg_path})."
            )
    cfg = load(cfg_path)
    missing = sorted({
        seat["api_key_env"]
        for role in cfg.roles.values()
        for seat in (role if isinstance(role, list) else [role])
        if isinstance(seat, dict) and seat.get("api_key_env")
        and not os.environ.get(seat["api_key_env"])
    })
    if missing:
        raise SystemExit(
            f"Missing API key ({', '.join(missing)}). Run `deepreason setup` "
            "to store it, or export it in your shell."
        )

    run_root = Path(root) if root else _fresh(Path("runs") / _slug(description))
    harness = Harness(run_root)
    out_dir = Path(out) if out else Path(_slug(description) + "-site")
    echo(f"Building: {description.strip()}")
    echo(f"(work happens in {run_root}; every step is on the record there)\n")

    if not staged:
        return _make_single(harness, cfg, description, out_dir, cycles,
                            token_budget, echo)

    plan_cycles = max(2, cycles // 4)
    design_cycles = max(2, cycles // 4)
    build_cycles = max(2, cycles - plan_cycles - design_cycles)
    echo(f"Stages: planning (up to {plan_cycles} rounds) -> designing "
         f"(up to {design_cycles}) -> building ({build_cycles})\n")
    spent = 0

    def remaining() -> int | None:
        return None if token_budget is None else max(0, token_budget - spent)

    def spend(accounting: dict) -> None:
        nonlocal spent
        spent += (accounting.get("metered_tokens")
                  or accounting.get("logged_tokens_this_run") or 0)

    # ---- stage 1: plan ----
    seed_plan(harness, description)
    spend(_run_stage(harness, cfg, label="planning", root_pid="pi-plan",
                     cycles=plan_cycles, token_budget=remaining(), echo=echo,
                     stop_on_survivor=True))
    plan_id = pick_survivor(harness, "pi-plan")
    if plan_id is None:
        echo("\nNo plan survived criticism — that's the tool being honest. "
             f'Try more rounds:\n  deepreason make "{description.strip()}" '
             f"--cycles {cycles + 4}")
        return []
    harness.record_measure(inputs=["stage-pick", "plan", plan_id])
    echo(f"  plan chosen: {_first_line(harness, plan_id)}\n")
    if remaining() == 0:
        echo("Ran out of token budget after planning — raise --token-budget.")
        return []

    # ---- stage 2: design ----
    seed_design(harness, description, plan_id)
    spend(_run_stage(harness, cfg, label="designing", root_pid="pi-design",
                     cycles=design_cycles, token_budget=remaining(), echo=echo,
                     stop_on_survivor=True))
    design_id = pick_survivor(harness, "pi-design")
    if design_id is None:
        echo("\nA plan survived but no design did — try more rounds:\n"
             f'  deepreason make "{description.strip()}" --cycles {cycles + 4}')
        return []
    harness.record_measure(inputs=["stage-pick", "design", design_id])
    echo(f"  design chosen: {_first_line(harness, design_id)}\n")
    if remaining() == 0:
        echo("Ran out of token budget after designing — raise --token-budget.")
        return []

    # ---- stage 3: build ----
    seed_build(harness, description, design_id)
    spend(_run_stage(harness, cfg, label="building", root_pid="pi-website",
                     cycles=build_cycles, token_budget=remaining(), echo=echo,
                     stop_on_survivor=False))
    echo(f"\nDone thinking ({spent:,} tokens).")

    paths = export_run(harness, out_dir)
    from deepreason.programs import content_text
    for stage, aid in (("plan", plan_id), ("design", design_id)):
        doc = out_dir / f"{stage}-{aid[:12]}.md"
        doc.write_text(content_text(harness.state.artifacts[aid], harness.blobs))
        paths.append(doc)
    pages = [p for p in paths if p.suffix == ".html"]
    if pages:
        echo(f"\nYour website is ready — {len(pages)} version(s) survived criticism:")
        for p in pages:
            echo(f"  {p.resolve()}")
        echo("\nDouble-click one to open it in your browser. The folder also "
             "holds the plan and design it implements, and the README "
             "explains why each version survived.")
    else:
        echo("\nThe plan and design survived, but no build did — that's the "
             "tool being honest, not broken. Try again with more rounds:\n"
             f'  deepreason make "{description.strip()}" --cycles {cycles + 4}')
        if harness.state.status.get(design_id) != Status.ACCEPTED:
            echo("(Note: the chosen design was itself refuted under later "
                 "criticism, so builds depending on it were suspended — "
                 "orphaned, not proven wrong.)")
    return paths


def _make_single(harness, cfg, description: str, out_dir: Path, cycles: int,
                 token_budget: int | None, echo) -> list[Path]:
    """The legacy single-stage loop: conjecture finished pages directly."""
    from deepreason.ontology import Status
    from deepreason.ops import run_scheduler
    from deepreason.views.export import export_run

    seed_website(harness, description)

    def ticker(scheduler):
        # Count ALL design candidates in the run, not just those addressed
        # to the seed problem: refuted designs spawn successor problems and
        # later candidates address THOSE (observed live: the eventual
        # survivor sat three successor generations deep). The root is
        # dedicated to this one build, so the global count is the build.
        state = scheduler.harness.state
        designs = [aid for aid, a in state.artifacts.items()
                   if a.provenance and a.provenance.role.value
                   in ("conjecturer", "synthesizer")]
        alive = sum(1 for a in designs if state.status.get(a) == Status.ACCEPTED)
        dead = sum(1 for a in designs if state.status.get(a) == Status.REFUTED)
        n = scheduler._cycles
        echo(f"  round {n}/{cycles}: {alive} design(s) standing, "
             f"{dead} criticized away")

    _, _, accounting = run_scheduler(
        harness, cfg, cycles, token_budget=token_budget, on_cycle=ticker)
    spent = accounting.get("logged_tokens_this_run") or 0
    echo(f"\nDone thinking ({spent:,} tokens).")

    paths = export_run(harness, out_dir)
    pages = [p for p in paths if p.suffix == ".html"]
    if pages:
        echo(f"\nYour website is ready — {len(pages)} version(s) survived criticism:")
        for p in pages:
            echo(f"  {p.resolve()}")
        echo("\nDouble-click one to open it in your browser. The folder's "
             "README explains why each survived.")
    else:
        echo("\nNothing survived criticism this time — that's the tool being "
             "honest, not broken. Try again with more rounds:\n"
             f'  deepreason make "{description.strip()}" --cycles {cycles + 4}')
    return paths
