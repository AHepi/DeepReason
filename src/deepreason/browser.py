"""Browser oracle — the app-medium evaluator (exogenous evidence).

The execution oracle (oracle.py) runs candidate CODE in-process; this module
runs a candidate APP (a single-file HTML/JS artifact) in its real medium:
headless Chromium drives a FROZEN interaction script (click/type/assert steps
under a VIRTUAL clock) and captures screenshots. Unlike the in-process
oracles, a browser run is not replay-deterministic, so it is treated exactly
like research fetches (research/backends.py): the run happens ONCE, its
verdict/trace/screenshots are materialized as import-role evidence artifacts
(rules/act.py), and replay reads the log — never the browser. Accordingly
``program:browser_oracle`` is deliberately NOT registered in programs.PROGRAMS
(crit_program skips it via programs.evaluable) and NOT in oracle.EXEC_PROGRAMS
(a DOM pass earns no execution supremacy: visual quality is precisely the
dimension DOM assertions cannot see, and the vision critic must remain free
to attack it).

Determinism measures for the single live run: fixed viewport and device
scale, reduced motion plus animation-killing CSS, content loaded via
set_content (no network, no temp files), and Playwright's clock API pinned to
a fixed epoch — ``tick`` steps advance VIRTUAL time, so "25 minutes pass" is
a deterministic instruction that executes instantly. Verdicts hinge on DOM
assertions only, never pixels; screenshots are evidence for the vision
critic, not inputs to adjudication.

Playwright is an OPTIONAL dependency: everything here imports lazily and
raises BrowserUnavailable with install instructions when missing.
"""

import json
import os
import shlex
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.ontology.commitment import Budget, Commitment

BROWSER_PROGRAM = "browser_oracle"
PASS, FAIL, OVERRUN = "pass", "fail", "overrun"

# Known Chromium binary in managed environments where the playwright package
# version does not match the downloaded browser build (registry launch fails).
_CHROMIUM_FALLBACK = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
# Fixed virtual epoch: the app's Date/setInterval/rAF all start here.
_EPOCH_MS = 1_767_225_600_000  # 2026-01-01T00:00:00Z
_STEP_TIMEOUT_MS = 5_000
_KILL_ANIMATIONS_CSS = (
    "*,*::before,*::after{animation:none!important;transition:none!important;"
    "caret-color:transparent!important}"
)

_STEP_OPS = frozenset(
    {"click", "type", "tick", "assert_text", "assert_visible", "assert_js", "screenshot"}
)


class BrowserUnavailable(RuntimeError):
    """playwright is not installed (optional dependency)."""


def chromium_executable() -> str | None:
    """An explicitly supplied or locally discoverable Chromium binary.

    Playwright's Python package and its browser payload are separate. Managed
    and offline environments often provide the executable through another
    channel, so a missing Playwright-managed download must not force a stale
    hard-coded path or disable browser verification.
    """
    configured = os.environ.get("DEEPREASON_CHROMIUM_PATH")
    candidates = [
        configured,
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        shutil.which("google-chrome"),
        _CHROMIUM_FALLBACK,
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return str(Path(candidate))
    return None


def chromium_launch_args() -> list[str]:
    """Optional launch flags for a supplied non-Playwright Chromium binary.

    Serverless Chromium distributions frequently need a small, vendor-specific
    flag set (for example, single-process mode).  Keeping it in an explicit
    environment variable makes that runtime input visible without changing a
    candidate app or silently weakening the normal Playwright path.
    """
    raw = os.environ.get("DEEPREASON_CHROMIUM_ARGS", "")
    return shlex.split(raw) if raw.strip() else []


@dataclass
class BrowserResult:
    verdict: str
    trace: dict
    screenshots: list[bytes] = field(default_factory=list)


def browser_commitment(script: list[dict], viewport: dict | None = None) -> Commitment:
    """Content-addressed browser-oracle commitment: the interaction script
    (and viewport) freeze into the id, so the same candidate under the same
    spec always names the same commitment. observation_valued=True: a browser
    verdict is an EMPIRICAL claim needing evidence — spawn.py auto-spawns the
    research:{cid}:{aid} problem that rules/act.py addresses its evidence to,
    which is also what finally lifts detection.evidence_lambda."""
    spec = {"script": script, "viewport": viewport or {"width": 800, "height": 600}}
    digest = sha256_hex(canonical_json(spec))[:12]
    return Commitment(
        id=f"browser@{digest}",
        eval=f"program:{BROWSER_PROGRAM}",
        observation_valued=True,
        budget=Budget(extra={"spec": json.dumps(spec, sort_keys=True)}),
    )


def load_spec(budget) -> dict:
    try:
        return json.loads(budget.extra.get("spec", "{}")) if budget and budget.extra else {}
    except (ValueError, AttributeError):
        return {}


class PlaywrightBrowser:
    """Duck-typed browser backend (mirror of research backends): ``.name`` +
    ``run(html, spec) -> BrowserResult``. Tests use a FakeBrowser instead —
    the suite never needs Chromium."""

    name = "playwright-chromium"

    def run(self, html: str, spec: dict) -> BrowserResult:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as e:
            raise BrowserUnavailable(
                "playwright is not installed — pip install 'deepreason[browser]' "
                "(or playwright) to enable the browser oracle"
            ) from e

        script = spec.get("script")
        if not isinstance(script, list) or not all(
            isinstance(s, dict) and s.get("op") in _STEP_OPS for s in script
        ):
            return BrowserResult(OVERRUN, {"error": "malformed interaction script"})
        viewport = spec.get("viewport") or {"width": 800, "height": 600}

        screenshots: list[bytes] = []
        steps_run: list[dict] = []
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch()
            except Exception as primary:  # noqa: BLE001 - external browser fallback
                executable = chromium_executable()
                if executable is None:
                    raise BrowserUnavailable(
                        "Playwright is installed but no Chromium executable is available; "
                        "install its browser payload or set DEEPREASON_CHROMIUM_PATH"
                    ) from primary
                browser = p.chromium.launch(
                    executable_path=executable,
                    args=chromium_launch_args(),
                )
            try:
                page = browser.new_page(
                    viewport=viewport, device_scale_factor=1, reduced_motion="reduce"
                )
                # `set_content` itself is local, but page assets or app code
                # could still try the network. Abort every HTTP(S) request so
                # the executable check enforces the same offline commitment
                # as the static assembler gate.
                page.route(
                    "**/*",
                    lambda route: route.abort()
                    if route.request.url.startswith(("http://", "https://"))
                    else route.continue_(),
                )
                page.set_default_timeout(_STEP_TIMEOUT_MS)
                # Virtual time MUST install before the app's scripts run.
                page.clock.install(time=_EPOCH_MS)
                page.set_content(html, wait_until="load")
                page.add_style_tag(content=_KILL_ANIMATIONS_CSS)
                for i, step in enumerate(script):
                    detail = self._step(page, step, screenshots)
                    steps_run.append({"i": i, **step, **(detail or {})})
                    if detail is not None and "error" in detail:
                        return BrowserResult(
                            FAIL,
                            {"failed_step": i, "steps": steps_run, "browser": self.name},
                            screenshots,
                        )
            finally:
                browser.close()
        return BrowserResult(
            PASS, {"steps": steps_run, "browser": self.name}, screenshots
        )

    @staticmethod
    def _step(page, step: dict, screenshots: list[bytes]) -> dict | None:
        """Run one step; a dict with 'error' means the step failed the app
        (assertion miss, missing selector, JS error) — a verdict, never an
        exception."""
        op = step["op"]
        try:
            if op == "click":
                page.click(step["selector"])
            elif op == "type":
                page.fill(step["selector"], step.get("text", ""))
            elif op == "tick":
                # run_for (not fast_forward): fires EVERY elapsed timer
                # callback, so a 1s interval ticks 1500 times across a
                # 25-minute jump — fast_forward would fire it once.
                page.clock.run_for(int(step.get("ms", 1000)))
            elif op == "assert_text":
                got = (page.text_content(step["selector"]) or "").strip()
                if got != step.get("expected", ""):
                    return {"error": "text mismatch", "got": got[:120],
                            "expected": step.get("expected", "")}
                return {"got": got[:120]}
            elif op == "assert_visible":
                if not page.is_visible(step["selector"]):
                    return {"error": "not visible"}
            elif op == "assert_js":
                value = page.evaluate(step["expr"])
                if not value:
                    return {"error": "expression falsy", "got": repr(value)[:120]}
                return {"got": repr(value)[:120]}
            elif op == "screenshot":
                screenshots.append(page.screenshot(type="png"))
                return {"screenshot_index": len(screenshots) - 1}
        except Exception as e:  # noqa: BLE001 - app faults are verdicts, not crashes
            return {"error": f"{type(e).__name__}: {str(e)[:160]}"}
        return None
