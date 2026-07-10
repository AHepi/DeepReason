"""Vision plumbing: multimodal payloads through the adapter (content-parts
with base64 data URLs), and — later in the file as the rule lands — the
vision critic judging rendered screenshots."""

import base64
import json

from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.contracts import ProseOutput
from deepreason.llm.endpoints import MockEndpoint, OpenAICompatEndpoint

PNG = base64.b64decode(  # 1x1 transparent PNG
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYGBgAAAABQAB"
    "h6FO1AAAAABJRU5ErkJggg=="
)


def _endpoint(**kw):
    return OpenAICompatEndpoint(base_url="https://example.test/v1", model="m", **kw)


def test_build_body_without_images_is_a_bare_string():
    body = _endpoint().build_body("hello")
    assert body["messages"] == [{"role": "user", "content": "hello"}]


def test_build_body_with_images_uses_content_parts():
    body = _endpoint().build_body("describe this", images=[PNG, PNG])
    content = body["messages"][0]["content"]
    assert isinstance(content, list) and len(content) == 3
    assert content[0] == {"type": "text", "text": "describe this"}
    for part in content[1:]:
        assert part["type"] == "image_url"
        url = part["image_url"]["url"]
        assert url.startswith("data:image/png;base64,")
        assert base64.b64decode(url.split(",", 1)[1]) == PNG


def test_adapter_threads_images_to_the_endpoint(harness):
    endpoint = MockEndpoint([json.dumps({"prose": "a red square"})])
    adapter = LLMAdapter({"summarizer": endpoint}, harness.blobs, retry_max=2)
    output, call = adapter.call("summarizer", "look", ProseOutput, images=[PNG])
    assert output.prose == "a red square"
    assert endpoint.last_images == [PNG]  # the bytes reached the endpoint


def test_adapter_without_images_keeps_legacy_single_arg_call(harness):
    class OneArgEndpoint(MockEndpoint):
        def complete(self, prompt):  # legacy signature: must keep working
            return super().complete(prompt)

    endpoint = OneArgEndpoint([json.dumps({"prose": "ok"})])
    adapter = LLMAdapter({"summarizer": endpoint}, harness.blobs, retry_max=2)
    output, _ = adapter.call("summarizer", "hi", ProseOutput)
    assert output.prose == "ok"


# ---- crit_vision: an LLM that LOOKS at the rendered app ----

from deepreason.browser import browser_commitment  # noqa: E402
from deepreason.config import Config  # noqa: E402
from deepreason.ontology import Interface, Problem, ProblemProvenance, Provenance, Status, WarrantType  # noqa: E402
from deepreason.ontology.artifact import RefRole  # noqa: E402
from deepreason.oracle import property_oracle_commitment  # noqa: E402
from deepreason.rules.vision import crit_vision  # noqa: E402
from tests.conftest import attack  # noqa: E402
from tests.test_act import PNG as ACT_PNG, SCRIPT, FakeBrowser  # noqa: E402


def _rendered_app(harness, verdict="pass"):
    from deepreason.rules.act import run_browser_evidence

    c = browser_commitment(SCRIPT)
    harness.register_commitment(c)
    harness.register_problem(Problem(
        id="pi-app", description="build a pomodoro timer",
        criteria=[c.id],
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
    ))
    app = harness.create_artifact(
        "<div id=t>25:00</div>", codec="code:html",
        interface=Interface(commitments=[c.id]),
        provenance=Provenance(role="conjecturer"), problem_id="pi-app",
    )
    run_browser_evidence(harness, app.id, FakeBrowser(verdict), Config())
    return c, app


def _vision_adapter(harness, attack, case="buttons are unlabeled"):
    endpoint = MockEndpoint([json.dumps(
        {"attack": attack, "case": case, "screenshot_index": 0}
    )])
    return endpoint, LLMAdapter({"vision_critic": endpoint}, harness.blobs, retry_max=2)


def test_vision_attack_registers_argumentative_warrant(harness):
    _, app = _rendered_app(harness)
    endpoint, adapter = _vision_adapter(harness, attack=True)

    critic = crit_vision(harness, app.id, adapter, Config())

    assert critic is not None
    assert endpoint.last_images and endpoint.last_images[0] == ACT_PNG  # it SAW
    assert harness.state.status[app.id] == Status.REFUTED
    w = next(w for w in harness.warrants.values() if w.target == app.id)
    assert w.type == WarrantType.ARGUMENTATIVE
    # The nu declares the screenshot(s) as load-bearing EVIDENCE.
    nu = harness.state.artifacts[w.validity_node]
    from deepreason.rules.act import browser_evidence

    shot = browser_evidence(harness, app.id)[0]["screenshots"][0]
    assert any(r.target == shot and r.role == RefRole.EVIDENCE for r in nu.interface.refs)


def test_refuting_browser_reliability_reinstates_visually_refuted_app(harness):
    """Evidence invalidation is graph closure, not a hidden view-level check."""
    _, app = _rendered_app(harness)
    _, adapter = _vision_adapter(harness, attack=True)
    vision_critic = crit_vision(harness, app.id, adapter, Config())
    assert vision_critic is not None
    assert harness.state.status[app.id] == Status.REFUTED

    from deepreason.rules.act import browser_evidence

    payload = browser_evidence(harness, app.id)[0]
    evidence = harness.state.artifacts[payload["evidence_id"]]
    reliability_id = next(
        ref.target for ref in evidence.interface.refs if ref.role == RefRole.DEPENDENCE
    )

    attack(harness, reliability_id, "browser-source-is-unreliable")

    assert harness.state.status[reliability_id] == Status.REFUTED
    assert harness.state.status[evidence.id] == Status.SUSPENDED_UNSUPPORTED
    assert harness.state.status[vision_critic.id] == Status.REFUTED
    assert harness.state.status[app.id] == Status.ACCEPTED


def test_vision_no_attack_logs_measure(harness):
    _, app = _rendered_app(harness)
    _, adapter = _vision_adapter(harness, attack=False, case="")
    assert crit_vision(harness, app.id, adapter, Config()) is None
    assert harness.state.status[app.id] == Status.ACCEPTED
    last = list(harness.log.read())[-1]
    assert last.inputs == ["vision-crit", app.id] and last.llm is not None


def test_vision_without_screenshots_is_a_noop(harness):
    app = harness.create_artifact("prose, never rendered")
    _, adapter = _vision_adapter(harness, attack=True)
    assert crit_vision(harness, app.id, adapter, Config()) is None  # no call made


def test_supremacy_boundary_in_process_oracle_blocks_visual_argument(harness):
    # Deliberate, documented boundary: a target ALSO backed by a PASSING
    # in-process property oracle cannot be refuted by visual argument.
    prop = property_oracle_commitment(
        "solve", [[[1]]],
        "def check(inp, out):\n    return out == inp[0]\n",
    )
    harness.register_commitment(prop)
    c = browser_commitment(SCRIPT)
    harness.register_commitment(c)
    app = harness.create_artifact(
        "def solve(xs):\n    return xs",
        codec="code:python",
        interface=Interface(commitments=[prop.id, c.id]),
        provenance=Provenance(role="conjecturer"),
    )
    from deepreason.rules.act import run_browser_evidence

    run_browser_evidence(harness, app.id, FakeBrowser("pass"), Config())
    _, adapter = _vision_adapter(harness, attack=True)

    assert crit_vision(harness, app.id, adapter, Config()) is None
    assert harness.state.status[app.id] == Status.ACCEPTED
    last = list(harness.log.read())[-1]
    assert last.inputs[0] == "vision-crit-overridden-by-execution"


def test_scheduler_renders_then_judges(tmp_path):
    from deepreason.harness import Harness
    from deepreason.scheduler.scheduler import Scheduler

    harness = Harness(tmp_path / "run")
    c = browser_commitment(SCRIPT)
    harness.register_commitment(c)
    harness.register_problem(Problem(
        id="pi-app", description="build a pomodoro timer", criteria=[c.id],
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
    ))
    conj = json.dumps({"candidates": [
        {"content": "<div id=t>25:00</div>", "typicality": 0.9},
    ]})
    vision = json.dumps({"attack": False, "case": ""})
    vision_endpoint = MockEndpoint([vision])
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint([conj, conj]), "vision_critic": vision_endpoint},
        harness.blobs, retry_max=2,
    )
    config = Config(VS_K=1, N_SCHOOLS=0, FUZZ_N=0, GEN_PROPOSE_PERIOD=0,
                    PROP_PROPOSE_PERIOD=0)
    scheduler = Scheduler(harness, adapter, config, browser_backend=FakeBrowser("pass"))
    scheduler.step()
    scheduler.step()
    # The browser ran, evidence recorded, and the vision critic SAW the render.
    from deepreason.rules.act import browser_evidence

    rendered = [a.id for a in harness.state.artifacts.values()
                if browser_evidence(harness, a.id)]
    assert rendered
    assert vision_endpoint.last_images  # multimodal call actually happened
