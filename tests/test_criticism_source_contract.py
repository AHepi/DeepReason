import ast
import importlib.util
from pathlib import Path

import pytest
from pydantic import ValidationError

from deepreason import criticism_source as cs


class _Source:
    def __init__(self, source_id: str, output: object) -> None:
        self.manifest = cs.CriticismSourceManifestV1(source_id=source_id, version="1", summary=source_id)
        self.output = output
        self.seen: list[cs.CriticismTargetV1] = []

    def contribute(self, target: cs.CriticismTargetV1) -> object:
        self.seen.append(target)
        if isinstance(self.output, Exception):
            raise self.output
        if self.output == "echo":
            return ({"content": target.content, "codec": target.codec},)
        return self.output


def test_contract_fields_are_closed_contract() -> None:
    assert set(cs.CriticismSourceManifestV1.model_fields) == {"schema_version", "source_id", "version", "summary", "authority_ceiling"}
    assert set(cs.CriticismTargetV1.model_fields) == {"target_id", "content", "codec"}
    assert set(cs.CriticismContributionV1.model_fields) == {"content", "codec"}
    assert set(cs.CriticismInvocationResultV1.model_fields) == {"source_id", "outcome", "manifest_digest", "contributions", "detail"}
    assert set(cs.CriticismSourceDescriptionV1.model_fields) == {"source_id", "version", "summary", "manifest_digest", "authority_explanation"}
    for model in (cs.CriticismSourceManifestV1, cs.CriticismTargetV1, cs.CriticismContributionV1, cs.CriticismInvocationResultV1, cs.CriticismSourceDescriptionV1):
        assert model.model_config["extra"] == "forbid"
        assert model.model_config["frozen"] is True
    with pytest.raises(ValidationError):
        cs.CriticismContributionV1.model_validate({"content": "x", "codec": "text", "score": 1})
    with pytest.raises(ValidationError):
        cs.CriticismSourceManifestV1(source_id="x", version="1", summary="x", authority_ceiling="observe_only")


@pytest.mark.parametrize("content", ["possibly, because...", "∀x P(x)", '{"x": 1}', "if x:\n    try_y()"])
def test_arbitrary_content_crosses_without_classification(content: str) -> None:
    source = _Source("echo", "echo")
    registry = cs.CriticismSourceRegistry((source,))
    target = cs.CriticismTargetV1(target_id="host-bound", content=content, codec="open/text")
    result = cs.invoke_criticism_source(registry, "echo", target)
    assert source.seen == [target] and result.outcome == "completed"
    assert result.contributions == (cs.CriticismContributionV1(content=content, codec="open/text"),)


@pytest.mark.parametrize("output", ["bare scalar", ({"content": "x", "target_id": "other"},)])
def test_host_bound_target_and_invalid_output_cannot_redirect(output: object) -> None:
    source, target = _Source("bad", output), cs.CriticismTargetV1(target_id="bound", content="t")
    result = cs.invoke_criticism_source(cs.CriticismSourceRegistry((source,)), "bad", target)
    assert (result.outcome, result.contributions, result.detail) == ("error", (), "CRITICISM_SOURCE_OUTPUT_INVALID")


def test_registry_is_explicit_and_rejects_duplicates() -> None:
    left, right = _Source("Left Source", None), _Source("RIGHT / Ω", None)
    registry = cs.CriticismSourceRegistry((right, left))
    assert [m.source_id for m in registry.manifests] == ["Left Source", "RIGHT / Ω"]
    with pytest.raises(ValueError, match="CRITICISM_SOURCE_DUPLICATE"):
        cs.CriticismSourceRegistry((left, left))


def test_operational_result_invocation_outcomes_are_local_and_unavailable() -> None:
    declined, failed = _Source("declined", None), _Source("failed", RuntimeError("boom"))
    registry = cs.CriticismSourceRegistry((declined, failed))
    target = cs.CriticismTargetV1(target_id="t", content="claim")
    missing = cs.invoke_criticism_source(registry, "missing", target)
    assert (missing.outcome, missing.detail) == ("unavailable", "CRITICISM_SOURCE_UNAVAILABLE")
    assert cs.invoke_criticism_source(registry, "declined", target).outcome == "declined"
    result = cs.invoke_criticism_source(registry, "failed", target)
    assert result.outcome == "error" and result.detail == "CRITICISM_SOURCE_EXECUTION_ERROR"


def test_disagreeing_sources_remain_independent() -> None:
    yes = _Source("yes", ({"content": "yes", "codec": "text"},))
    no = _Source("no", ({"content": "no", "codec": "text"},))
    registry, target = cs.CriticismSourceRegistry((yes, no)), cs.CriticismTargetV1(target_id="t", content="c")
    assert cs.invoke_criticism_source(registry, "yes", target).contributions[0].content == "yes"
    assert cs.invoke_criticism_source(registry, "no", target).contributions[0].content == "no"


def test_human_description_is_host_owned_and_deterministic() -> None:
    registry = cs.CriticismSourceRegistry((_Source("z", None), _Source("a", None)))
    first = cs.describe_criticism_sources(registry)
    assert [row.source_id for row in first] == ["a", "z"]
    assert all(row.authority_explanation == cs.CONTRIBUTION_ONLY_EXPLANATION for row in first)
    assert first == cs.describe_criticism_sources(registry) and all(len(row.manifest_digest) == 64 for row in first)


def test_module_has_no_deepreason_dependency() -> None:
    tree = ast.parse(Path("src/deepreason/criticism_source.py").read_text())
    allowed = {"__future__", "collections.abc", "hashlib", "json", "pydantic", "types", "typing"}
    imports = [(n.level, n.module or "") for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    imports += [(0, a.name) for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
    assert not [(level, name) for level, name in imports if level or name not in allowed]


def test_registry_is_deliberately_unwired_from_shipped_graph() -> None:
    offenders = []
    for path in Path("src/deepreason").rglob("*.py"):
        if path.name == "criticism_source.py":
            continue
        tree = ast.parse(path.read_text())
        imports = [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
        package = ".".join(path.relative_to("src").with_suffix("").parts[:-1])
        for node in (n for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)):
            module = importlib.util.resolve_name("." * node.level + (node.module or ""), package) if node.level else node.module or ""
            imports.extend(f"{module}.{alias.name}" for alias in node.names)
        if any(name == "deepreason.criticism_source" or name.startswith("deepreason.criticism_source.") for name in imports):
            offenders.append(str(path))
    assert offenders == []
