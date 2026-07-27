"""Browser oracle (browser.py): real-Chromium tests, skipped wholesale when
playwright is missing (optional dependency). Verdicts hinge on DOM assertions
under a VIRTUAL clock; screenshots are evidence bytes, never adjudication
inputs."""

import pytest

pytest.importorskip("playwright")

from deepreason.browser import (  # noqa: E402
    BROWSER_PROGRAM,
    PlaywrightBrowser,
    browser_commitment,
    chromium_executable,
    chromium_launch_args,
    load_spec,
)

# A minimal clock-driven countdown app — the pomodoro shape in miniature.
COUNTDOWN = """
<button id="start">start</button><div id="t">10</div>
<script>
let n = 10, h = null;
document.getElementById('start').onclick = () => {
  if (h) return;
  h = setInterval(() => { n -= 1; document.getElementById('t').textContent = n; }, 1000);
};
</script>
"""

PASSING = [
    {"op": "assert_text", "selector": "#t", "expected": "10"},
    {"op": "screenshot"},
    {"op": "click", "selector": "#start"},
    {"op": "tick", "ms": 3000},
    {"op": "assert_text", "selector": "#t", "expected": "7"},
    {"op": "assert_js", "expr": "document.querySelectorAll('button').length === 1"},
    {"op": "screenshot"},
]


@pytest.fixture(scope="module")
def browser():
    return PlaywrightBrowser()


def test_configured_chromium_path_is_discovered(tmp_path, monkeypatch):
    executable = tmp_path / "chromium"
    executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(0o755)
    monkeypatch.setenv("DEEPREASON_CHROMIUM_PATH", str(executable))
    assert chromium_executable() == str(executable)


def test_configured_chromium_launch_args_are_shell_split(monkeypatch):
    monkeypatch.setenv("DEEPREASON_CHROMIUM_ARGS", "--single-process --headless='shell'")
    assert chromium_launch_args() == ["--single-process", "--headless=shell"]


def test_commitment_is_content_addressed_and_observation_valued():
    c = browser_commitment(PASSING)
    assert c.id.startswith("browser@")
    assert c.eval == f"program:{BROWSER_PROGRAM}"
    assert c.observation_valued is True
    assert c.id == browser_commitment(PASSING).id
    assert load_spec(c.budget)["script"] == PASSING


def test_clock_controlled_countdown_passes_and_screenshots(browser):
    result = browser.run(COUNTDOWN, load_spec(browser_commitment(PASSING).budget))
    assert result.verdict == "pass", result.trace
    assert len(result.screenshots) == 2
    assert all(png.startswith(b"\x89PNG") for png in result.screenshots)


def test_wrong_expectation_fails_with_step_trace(browser):
    script = [
        {"op": "click", "selector": "#start"},
        {"op": "tick", "ms": 3000},
        {"op": "assert_text", "selector": "#t", "expected": "9"},  # actually 7
    ]
    result = browser.run(COUNTDOWN, {"script": script})
    assert result.verdict == "fail"
    assert result.trace["failed_step"] == 2
    assert result.trace["steps"][2]["got"] == "7"


def test_missing_selector_is_a_verdict_not_a_crash(browser):
    result = browser.run(COUNTDOWN, {"script": [{"op": "click", "selector": "#nope"}]})
    assert result.verdict == "fail"
    assert "error" in result.trace["steps"][0]


def test_malformed_script_is_overrun(browser):
    assert browser.run(COUNTDOWN, {"script": [{"op": "explode"}]}).verdict == "overrun"
    assert browser.run(COUNTDOWN, {"script": "nope"}).verdict == "overrun"


def test_broken_app_fails_by_execution(browser):
    broken = COUNTDOWN.replace("n -= 1", "n -= 2")  # counts down twice as fast
    result = browser.run(broken, {"script": PASSING})
    assert result.verdict == "fail"  # 10 - 2*3 = 4, expected 7
