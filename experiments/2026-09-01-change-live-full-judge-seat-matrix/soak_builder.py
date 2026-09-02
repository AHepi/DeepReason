#!/usr/bin/env python3
"""Delegate judge-matrix soak construction to a proven full-court builder.

The source builder owns the defended, school-routed, cross-family court shape.
This wrapper supplies the loopback-redacted configuration created by the
unchanged soak driver, then verifies the launch-critical properties on both
the source Config and the bound manifest before the managed run can start.
"""
from __future__ import annotations

import importlib.util
import re
import sys
import unicodedata
from pathlib import Path
from types import ModuleType
from typing import Any, Iterator, Mapping

from deepreason.config import load as load_config
from deepreason.run_manifest import load_run_manifest

TRANCHE = Path(__file__).resolve().parent
REPO = TRANCHE.parents[1]
SOURCE_TRANCHE = REPO / "experiments" / "2026-08-12-live-grounded-extension-expansion"
SOURCE_BUILDER = SOURCE_TRANCHE / "build_manifest.py"
FORBIDDEN_REASONING = frozenset({"high", "max", "xhigh"})


def _load_source_builder() -> ModuleType:
    name = "_judge_matrix_grounded_builder"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, SOURCE_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load source builder: {SOURCE_BUILDER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_SOURCE = _load_source_builder()
QUESTION = _SOURCE.QUESTION
CRITERIA = ()
COMPILED_AT = _SOURCE.COMPILED_AT


def _normalized_model_id(value: str) -> str:
    folded = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"[^a-z0-9]", "", folded)


def _routes(config: Any) -> Iterator[Mapping[str, Any]]:
    for configured in config.roles.values():
        seats = configured if isinstance(configured, list) else [configured]
        for route in seats:
            if not isinstance(route, Mapping):
                raise RuntimeError("judge-matrix route is not a mapping")
            yield route


def _validate_source_config(config: Any) -> None:
    if not config.ADJUDICATION_STATUS_AUTHORITY_ENABLED:
        raise RuntimeError("judge-matrix status authority gate is disabled")
    if config.ENGAGED_CRITICISM_AUTHORITY != "defended_trial":
        raise RuntimeError("judge-matrix criticism is not defended_trial")
    if config.LEGACY_CRITICISM_ENABLED:
        raise RuntimeError("judge-matrix legacy criticism is enabled")
    if not config.JUDGE_SEATS_ENABLED:
        raise RuntimeError("judge-matrix judge seats are disabled")
    if len(config.roles.get("judge") or ()) < 2:
        raise RuntimeError("judge-matrix requires at least two judge seats")

    for route in _routes(config):
        model_id = str(route.get("model") or "")
        if "kimik3" in _normalized_model_id(model_id):
            raise RuntimeError("judge-matrix source contains a forbidden model")
        reasoning = route.get("reasoning")
        if isinstance(reasoning, str) and reasoning.casefold() in FORBIDDEN_REASONING:
            raise RuntimeError("judge-matrix source contains forbidden reasoning")


def _validate_manifest(manifest: Any) -> None:
    policy = manifest.criticism_policy
    if policy is None or policy.authority != "defended_trial":
        raise RuntimeError("judge-matrix manifest lost defended trial authority")

    plan = manifest.route_seat_behavioral_capability_plan
    grants = {
        (entry.role, entry.seat): {grant.contract_id for grant in entry.contracts}
        for entry in plan.entries
    }
    if "defender.direct.v1" not in grants.get(("defender", 0), set()):
        raise RuntimeError("judge-matrix defender contract is absent")
    for seat in range(2):
        if "judgeruling.direct.v1" not in grants.get(("judge", seat), set()):
            raise RuntimeError(f"judge-matrix judge[{seat}] contract is absent")


def build(root: Path, *, config_path: Path) -> dict[str, Any]:
    """Build the delegated root from the soak driver's redacted config."""
    config_path = Path(config_path)
    _validate_source_config(load_config(config_path))

    previous_path = _SOURCE.CONFIG_PATH
    _SOURCE.CONFIG_PATH = config_path
    try:
        summary = dict(_SOURCE.build(root))
    finally:
        _SOURCE.CONFIG_PATH = previous_path

    manifest = load_run_manifest(root / "run-manifest.json")
    _validate_manifest(manifest)
    summary.update(
        {
            "criteria": [],
            "attached_evidence_enabled": (
                manifest.inquiry_capability_policy.attached_evidence.enabled
            ),
        }
    )
    return summary
