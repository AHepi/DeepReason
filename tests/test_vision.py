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
