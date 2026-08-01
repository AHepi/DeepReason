"""End-to-end E3.1 demo benchmark builder.

Generates a small demonstration benchmark — 3 synthetic axiom-domain problems
with depth-graded theorem targets and 3 program-checkable construction
problems — runs every difficulty/solvability certificate, seals verifiers and
answer keys into the ``holdout/`` namespace, and writes:

    <out>/manifest.json          benchmark manifest (ids, classes, seeds,
                                 certificate digests, Lean validation status)
    <out>/build_report.json      certificate statistics
    <out>/problems/<id>/...      problem-facing files only
    <out>/holdout/...            sealed blobs + holdout manifest (§10.5/§14)

Everything is deterministic from the fixed seed: same seed, same bytes.  No
LLM call, no network.  If the pinned Lean toolchain is not installed, the
.lean sources are still emitted and the manifest records kernel validation as
pending (recorded, never faked).
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from e31_benchmark import axiom_domains, constructions
from e31_benchmark.sealed import SealedProblem, seal_holdout, sealing_violations

DEMO_SEED = 20260713
BUILDER_VERSION = "e31-build-demo-v1"
BENCHMARK_MANIFEST_SCHEMA = "e31-benchmark-manifest-v1"

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = _REPO_ROOT / "experiments" / "e31_demo_benchmark"


def _dump(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, indent=2).encode() + b"\n"


def _lean_validation_status() -> dict[str, Any]:
    """Record (never fake) whether the pinned Lean kernel could validate the
    emitted sources at build time."""

    executable = shutil.which("lean")
    if executable is None:
        return {
            "status": "pending",
            "reason": (
                "toolchain_missing: no lean executable on PATH; pinned "
                f"{axiom_domains.LEAN_TOOLCHAIN_ID} not installed at build time"
            ),
            "toolchain_id": axiom_domains.LEAN_TOOLCHAIN_ID,
            "lean_sources_emitted": True,
        }
    return {
        "status": "pending",
        "reason": (
            "kernel_validation_not_run: a lean executable exists but no "
            "verification was executed by this builder; run the pinned "
            "LeanBackend against the emitted requests to close this"
        ),
        "toolchain_id": axiom_domains.LEAN_TOOLCHAIN_ID,
        "executable": executable,
        "lean_sources_emitted": True,
    }


def _axiom_statement_md(problem_id: str, public: dict[str, Any]) -> str:
    lines = [
        f"# {problem_id} — synthetic axiom domain ({public['signature']['class_name']})",
        "",
        "Class 1 (instance-fresh): a freshly generated axiomatic system over",
        "uninterpreted symbols, pinned in Lean 4 (`domain.lean`).  Schema",
        "templates are recognizable structure a model may know in the",
        "abstract; every instance (symbols, operator assignments,",
        "orientations) is freshly generated at build time, so this exact",
        "problem cannot appear in any training corpus.",
        "Prove the target theorems from the class hypotheses; the pinned",
        "verification request (`pinned_lean_request.json`) forbids `sorry`.",
        "",
        "## Axioms",
        "",
    ]
    lines += [f"- `{axiom}`" for axiom in public["axioms"]]
    lines += [
        "",
        "## Targets (graded by bounded canonical rewrite depth — relative",
        "to the build-time bounded prover, not a bound on all proof methods)",
        "",
    ]
    lines += [
        f"- `{target['lean_name']}` (depth grade {target['depth_grade']}): "
        f"`{target['statement']}`"
        for target in public["targets"]
    ]
    lines += [
        "",
        "Difficulty certificates and derivations are sealed in the holdout",
        "namespace (digests in the manifest) and revealed only post-hoc.",
        "",
    ]
    return "\n".join(lines)


def _construction_statement_md(problem: constructions.ConstructionProblem) -> str:
    spec = problem.check_spec
    return "\n".join(
        [
            f"# {problem.problem_id} — construction problem ({problem.family})",
            "",
            "Class 2 (program-checkable construction, parameterization",
            "randomized at benchmark build time).",
            "",
            "## Task",
            "",
            problem.statement,
            "",
            "## Verification",
            "",
            f"The trusted checker (CheckSpec `{spec.id}`, runner `{spec.runner}`,"
            f" argv `{list(spec.argv)}`) is sealed in the holdout namespace and",
            "revealed only post-hoc; its content address is listed in the",
            "manifest.  Solvability was certified at build time by exhaustive",
            "brute force (census sealed with the answer key).",
            "",
        ]
    )


def build_benchmark(out_dir: Path, *, seed: int = DEMO_SEED) -> dict[str, Any]:
    """Build the demo benchmark under ``out_dir``; return the build report."""

    out_dir = Path(out_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    problems_dir = out_dir / "problems"
    problems_dir.mkdir(parents=True)

    manifest_problems: list[dict[str, Any]] = []
    sealed_problems: list[SealedProblem] = []
    axiom_stats: list[dict[str, Any]] = []
    construction_stats: list[dict[str, Any]] = []

    # --- class 1: synthetic axiom domains -----------------------------------
    for index in range(3):
        problem_id = f"e31-axiom-{index:03d}"
        problem_seed = f"{seed}/axiom/{index}"
        domain = axiom_domains.generate_domain(problem_seed)
        targets = axiom_domains.enumerate_targets(domain)
        if not targets:
            raise RuntimeError(f"{problem_id}: enumerator produced no certified targets")
        lean_source = axiom_domains.render_lean(domain, targets).encode()
        request = axiom_domains.pinned_request(lean_source, targets)
        public = axiom_domains.domain_public_json(domain, targets)
        public["id"] = problem_id
        certificate = axiom_domains.domain_sealed_certificate(domain, targets)

        sealed = SealedProblem(
            problem_id=problem_id,
            problem_class="axiom_domain",
            seed=problem_seed,
            blobs={"certificate.json": _dump(certificate)},
            # Generator-template metadata lives ONLY in the sealed holdout
            # namespace; problem-facing JSON must not name the schema
            # templates behind each axiom.
            generator_metadata={
                "template_kinds": list(domain.template_kinds),
            },
        )
        sealed_problems.append(sealed)
        public["sealed_refs"] = sealed.refs()

        problem_dir = problems_dir / problem_id
        problem_dir.mkdir()
        (problem_dir / "domain.lean").write_bytes(lean_source)
        (problem_dir / "pinned_lean_request.json").write_bytes(
            _dump(request.model_dump(mode="json"))
        )
        (problem_dir / "problem.json").write_bytes(_dump(public))
        (problem_dir / "statement.md").write_text(
            _axiom_statement_md(problem_id, public), encoding="utf-8"
        )

        manifest_problems.append(
            {
                "id": problem_id,
                "class": "axiom_domain",
                "seed": problem_seed,
                "files": sorted(p.name for p in problem_dir.iterdir()),
                "certificate_digest": sealed.certificate_digest,
                "sealed_refs": sealed.refs(),
                "lean_source_sha256": request.source_ref,
                "target_theorems": list(request.target_theorems),
            }
        )
        axiom_stats.append(
            {
                "id": problem_id,
                "class_name": domain.signature.class_name,
                "attempt": domain.attempt,
                "n_axioms": len(domain.axioms),
                # template_kinds intentionally absent: generator-template
                # metadata is sealed holdout material, not report material.
                "targets": [
                    {
                        "lean_name": target.lean_name,
                        "depth": target.depth,
                        "nontrivial": target.certificate["nontrivial"],
                        "nodes_expanded_small": target.certificate["outcome_small"][
                            "nodes_expanded"
                        ],
                        "nodes_expanded_large": target.certificate["outcome_large"][
                            "nodes_expanded"
                        ],
                    }
                    for target in targets
                ],
            }
        )

    # --- class 2: program-checkable constructions ---------------------------
    for offset, family in enumerate(constructions.FAMILIES):
        index = 3 + offset
        problem = constructions.generate_construction(seed, family, index)
        problem_id = problem.problem_id
        answer_key = problem.sealed_answer_key()

        sealed = SealedProblem(
            problem_id=problem_id,
            problem_class="construction",
            seed=problem.seed,
            blobs={
                "checker.py": problem.checker_source.encode(),
                "answer_key.json": _dump(answer_key),
            },
            certificate_blob="answer_key.json",
        )
        sealed_problems.append(sealed)
        public = problem.public_json()
        public["sealed_refs"] = sealed.refs()

        problem_dir = problems_dir / problem_id
        problem_dir.mkdir()
        (problem_dir / "problem.json").write_bytes(_dump(public))
        (problem_dir / "statement.md").write_text(
            _construction_statement_md(problem), encoding="utf-8"
        )

        brute = problem.brute_force
        manifest_problems.append(
            {
                "id": problem_id,
                "class": "construction",
                "seed": problem.seed,
                "files": sorted(p.name for p in problem_dir.iterdir()),
                "certificate_digest": sealed.certificate_digest,
                "sealed_refs": sealed.refs(),
                "family": problem.family,
            }
        )
        construction_stats.append(
            {
                "id": problem_id,
                "family": problem.family,
                "attempt": problem.attempt,
                "parameters": problem.params,
                "search_space_size": brute["search_space_size"],
                "candidates_enumerated": brute["candidates_enumerated"],
                "enumeration_steps": brute["enumeration_steps"],
                "solutions_found": brute["solutions_found"],
                "solution_density": brute["solutions_found"]
                / brute["candidates_enumerated"],
                "solvable": brute["witness"] is not None,
            }
        )

    # --- sealed holdout (§10.5/§14) ------------------------------------------
    holdout_manifest = seal_holdout(out_dir / "holdout", sealed_problems)
    violations = sealing_violations(problems_dir, sealed_problems)
    if violations:
        raise RuntimeError("holdout sealing violated: " + "; ".join(violations))

    depth_values = sorted(
        target["depth"] for stat in axiom_stats for target in stat["targets"]
    )
    depth_distribution = {
        str(depth): depth_values.count(depth) for depth in sorted(set(depth_values))
    }
    lean_status = _lean_validation_status()

    manifest = {
        "schema": BENCHMARK_MANIFEST_SCHEMA,
        "builder_version": BUILDER_VERSION,
        "generator_versions": {
            "axiom_domains": axiom_domains.GENERATOR_VERSION,
            "constructions": constructions.GENERATOR_VERSION,
        },
        "seed": seed,
        "program_doc": "docs/EXPERIMENT_PROGRAM_2026-07.md (E3.1)",
        "counts": {
            "axiom_domain": len(axiom_stats),
            "construction": len(construction_stats),
            "total": len(manifest_problems),
        },
        "lean_kernel_validation": lean_status,
        "holdout": {
            "manifest": "holdout/manifest.json",
            "reveal_policy": holdout_manifest["reveal_policy"],
            "namespace": holdout_manifest["namespace"],
        },
        "problems": manifest_problems,
    }
    (out_dir / "manifest.json").write_bytes(_dump(manifest))

    report = {
        "schema": "e31-build-report-v1",
        "builder_version": BUILDER_VERSION,
        "seed": seed,
        "budgets": {
            "prover_small": axiom_domains.B_SMALL.to_json(),
            "prover_large": axiom_domains.B_LARGE.to_json(),
        },
        "axiom_domains": axiom_stats,
        "theorem_depth_distribution": depth_distribution,
        "nontrivial_targets": sum(
            1
            for stat in axiom_stats
            for target in stat["targets"]
            if target["nontrivial"]
        ),
        "total_targets": len(depth_values),
        "constructions": construction_stats,
        "sealing_audit": {"violations": violations, "clean": not violations},
        "lean_kernel_validation": lean_status,
        "deferred": [
            "LLM single-shot difficulty-calibration baselines (prereg, E3.1 "
            "certificate clause b)",
            "Lean kernel validation of emitted sources (pending toolchain)",
            "class 3 post-cutoff facts (text workload; separate curation)",
        ],
    }
    (out_dir / "build_report.json").write_bytes(_dump(report))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--seed", type=int, default=DEMO_SEED)
    args = parser.parse_args(argv)
    report = build_benchmark(args.out, seed=args.seed)
    print(json.dumps(
        {
            "out": str(args.out),
            "theorem_depth_distribution": report["theorem_depth_distribution"],
            "nontrivial_targets": report["nontrivial_targets"],
            "total_targets": report["total_targets"],
            "constructions": [
                {
                    "id": stat["id"],
                    "family": stat["family"],
                    "search_space_size": stat["search_space_size"],
                    "solutions_found": stat["solutions_found"],
                }
                for stat in report["constructions"]
            ],
            "sealing_clean": report["sealing_audit"]["clean"],
            "lean_kernel_validation": report["lean_kernel_validation"]["status"],
        },
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
