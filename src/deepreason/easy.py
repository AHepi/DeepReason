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

_KNOBS = {
    # The validated app-run shape (runs/acting_loop_app2): no schools/fuzz/
    # property machinery for a website build; browser evidence + criticism.
    "FLOOR": 1, "K": 4, "VS_K": 2, "N_SCHOOLS": 0, "FUZZ_N": 0,
    "GEN_PROPOSE_PERIOD": 0, "PROP_PROPOSE_PERIOD": 0,
    "BROWSER_PER_CYCLE": 2, "ARG_CRIT_PER_CYCLE": 2, "CRIT_BATCH_K": 2,
    "PACK_TOKEN_BUDGET": 4000, "RETRY_MAX": 2,
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


def make(description: str, out: str | None = None, cycles: int = 6,
         token_budget: int | None = 150_000, config: str | None = None,
         root: str | None = None, echo=_echo) -> list[Path]:
    """Build a website from a plain-language description: seed, run the
    conjecture-criticism loop with a friendly ticker, export what survives.
    Returns the exported file paths (empty = nothing survived)."""
    from deepreason.config import load
    from deepreason.harness import Harness
    from deepreason.ontology import Status
    from deepreason.ops import run_scheduler
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
    seed_website(harness, description)
    echo(f"Building: {description.strip()}")
    echo(f"(work happens in {run_root}; every step is on the record there)\n")

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

    result, meter, accounting = run_scheduler(
        harness, cfg, cycles, token_budget=token_budget, on_cycle=ticker)
    spent = accounting.get("logged_tokens_this_run") or 0
    echo(f"\nDone thinking ({spent:,} tokens).")

    out_dir = Path(out) if out else Path(_slug(description) + "-site")
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
