#!/usr/bin/env python
"""Render the committed thesis for a finished run's problem (views/thesis).

Read-only over the root: the adapter gets a SCRATCH blob store, the run's
log and blobs are untouched, and the call's spend is printed in the
output header instead of landing on the log.

Usage:
    DEEPSEEK_API_KEY=... python scripts/thesis.py \\
        --root runs/arrow_full --problem pi-arrow [--model deepseek-v4-pro]
"""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from deepreason.config import (  # noqa: E402
    apply_overrides,
    load as load_config,
    parse_value,
    role_api_key_envs,
)
from deepreason.harness import Harness  # noqa: E402
from deepreason.llm.adapter import SchemaRepairError, build_adapter  # noqa: E402
from deepreason.llm.budget import TokenBudgetExceeded, TokenMeter  # noqa: E402
from deepreason.llm.endpoints import EndpointError  # noqa: E402
from deepreason.storage.blobs import BlobStore  # noqa: E402
from deepreason.views.thesis import render_thesis, thesis  # noqa: E402


def _open_harness(root: Path | str, at_seq: int | None) -> Harness:
    """Open only a physically read-only view of the requested run fence."""

    if at_seq is not None:
        if isinstance(at_seq, bool) or at_seq < 0:
            raise ValueError("--at-seq must be a non-negative event sequence")
        return Harness.at(root, at_seq)
    return Harness(root, read_only=True)


def _validated_output_path(run_root: Path | str, output: Path | str | None) -> Path | None:
    """Resolve an optional output without permitting writes into the run.

    The thesis command opens both current and historical runs read-only.  Its
    optional rendered copy must therefore live outside that same filesystem
    tree, including when either path reaches the tree through a symlink.
    """

    if output is None:
        return None
    canonical_root = Path(run_root).resolve(strict=True)
    canonical_output = Path(output).resolve(strict=False)
    try:
        canonical_output.relative_to(canonical_root)
    except ValueError:
        return canonical_output
    raise ValueError("--out must be outside the read-only run root")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--problem", default=None,
                        help="problem id (default: the root's seed problem)")
    parser.add_argument(
        "--at-seq",
        type=int,
        default=None,
        help="render from this physically read-only historical event sequence",
    )
    parser.add_argument(
        "--config",
        default=str(Path(__file__).resolve().parents[1] / "config" / "deepseek.yaml"),
        help="partial YAML profile containing a thesis role",
    )
    parser.add_argument("--model", default=None, help="exact thesis model override")
    parser.add_argument("--base-url", default=None, help="thesis endpoint override")
    parser.add_argument("--api-key-env", default=None,
                        help="thesis API-key environment-name override")
    parser.add_argument("--budget", type=int, default=6000,
                        help="evidence pack budget in TOKENS (chars/4)")
    parser.add_argument("--token-budget", type=int, default=40_000,
                        help="hard meter ceiling for the thesis call(s)")
    parser.add_argument("--reasoning", default="policy",
                        help="thesis reasoning override: policy|default|none|high|max")
    parser.add_argument("--out", default=None, help="also write markdown here")
    args = parser.parse_args(argv)

    if args.at_seq is not None and args.at_seq < 0:
        print("invalid sequence: --at-seq must be non-negative", file=sys.stderr)
        return 1

    try:
        config = load_config(Path(args.config))
        if "thesis" not in config.roles:
            raise ValueError("profile has no thesis role")
        overrides = {}
        if args.model is not None:
            overrides["roles.thesis.model"] = args.model
        if args.base_url is not None:
            overrides["roles.thesis.endpoint"] = args.base_url
        if args.api_key_env is not None:
            overrides["roles.thesis.api_key_env"] = args.api_key_env
        if args.reasoning != "policy":
            overrides["roles.thesis.reasoning"] = (
                None if args.reasoning == "default" else parse_value(args.reasoning)
            )
        config = apply_overrides(config, overrides)
    except (OSError, ValueError) as error:
        print(f"invalid config: {error}", file=sys.stderr)
        return 1
    missing = sorted(
        name for name in role_api_key_envs(config, {"thesis"})
        if not os.environ.get(name)
    )
    if missing:
        print(f"{', '.join(missing)} not set", file=sys.stderr)
        return 1

    try:
        harness = _open_harness(Path(args.root), args.at_seq)
    except (OSError, ValueError) as error:
        print(f"invalid run: {error}", file=sys.stderr)
        return 1
    try:
        output_path = _validated_output_path(harness.root, args.out)
    except (OSError, ValueError) as error:
        print(f"invalid output: {error}", file=sys.stderr)
        return 1
    meter = TokenMeter(budget=args.token_budget)
    scratch = BlobStore(Path(tempfile.mkdtemp(prefix="thesis-blobs-")))
    adapter = build_adapter(config, scratch, meter=meter, only_roles={"thesis"})

    try:
        result = thesis(harness, adapter, problem_id=args.problem,
                        budget_chars=args.budget * 4)
    except (SchemaRepairError, EndpointError, TokenBudgetExceeded) as e:
        print(f"thesis failed: {e}", file=sys.stderr)
        return 1

    prose = render_thesis(result)
    print(prose)
    if output_path is not None:
        output_path.write_text(prose + "\n\n---\n" + json.dumps(
            {k: result[k] for k in ("problem", "citations", "citation_check",
                                    "pack_chars", "spend")}, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
