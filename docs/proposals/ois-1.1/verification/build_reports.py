"""Re-run the finite tests and selected mutations, then produce release evidence."""
from __future__ import annotations
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
import re
import subprocess
import sys

from fixtures import balances, seasons
from reference_kernel import report
from run_mutations import run as run_mutations

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def main() -> None:
    test_run = subprocess.run([sys.executable, "-m", "unittest", "-v"], cwd=HERE,
        text=True, capture_output=True, timeout=30)
    log = test_run.stdout + test_run.stderr
    (HERE / "test_results.txt").write_text(log)
    if test_run.returncode:
        raise RuntimeError("baseline tests failed; see test_results.txt")
    match = re.search(r"Ran (\d+) tests", log)
    if match is None:
        raise RuntimeError("could not extract unittest count")
    count = int(match.group(1))
    mutations = run_mutations()
    (HERE / "mutation_results.json").write_text(json.dumps(mutations, indent=2) + "\n")
    if not all(m["detected"] for m in mutations):
        raise RuntimeError("undetected selected mutation")
    bindings = {
        "authority_digest": digest(ROOT / "PopperSemanticsV1_1.md"),
        "specification_digest": digest(ROOT / "Open_Inquiry_Specification_1_1.md"),
        "interpretation_version": "fixture-I-1",
        "profile_version": "stipulated-fixtures-1.1",
        "checker_version": "reference-1.1:" + digest(HERE / "reference_kernel.py"),
        "policy_version": "DA-1",
    }
    outputs = []
    for fixture in balances() + seasons():
        cut_digest = fixture["model"].digest(fixture["cut"])
        result = report(fixture["query"], fixture["cases"], fixture["apps"], cut_digest, bindings)
        outputs.append({"fixture": fixture["name"], "entry_count": len(fixture["cut"]),
                        "subject_bindings": fixture["subjects"], "report": result})
    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(), "baseline_tests": count,
        "two_node_combinations": 2304,
        "selected_mutations": len(mutations),
        "detected_mutations": sum(m["detected"] for m in mutations),
        "interpretive_limit": "Stipulated fixture meanings; no semantic truth or capacity decision.",
        "fixtures": outputs,
    }
    (HERE / "fixture_results.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    rows = "\n".join(
        f"| {o['fixture']} | {o['entry_count']} | {o['report']['raw']} | {o['report']['usable']} | NOT_EVALUATED |"
        for o in outputs)
    mrows = "\n".join(f"| {m['mutation']} | detected | {len(m['failing_checks'])} |" for m in mutations)
    text = f"""# Verification report\n\n## Actual run\n\nThe finite reference passed **{count} tests**. The test suite includes independent enumeration of **2,304** two-node dependency/attack/readiness combinations. All **{len(mutations)} selected mutations were detected** by compiling the mutated checker and running tests against it. The two fixture generators produced **{len(outputs)} grounded, application-bound appraisal slices**.\n\nRun timestamp: `{payload['generated_utc']}`. Runtime: Python `{payload['python']}`. The code uses the standard library only.\n\nThese are results about the delivered finite reference and stipulated interpretations. They do not prove semantic truth, creativity, explanation quality, physical realizability, or universal capacity. Passing the small exhaustive family is not a proof of every graph size. The specification supplies a separate mathematical argument for the finite policy.\n\n## Exact document bindings\n\nAuthority SHA-256: `{bindings['authority_digest']}`.\n\nSpecification SHA-256: `{bindings['specification_digest']}`.\n\nChecker SHA-256: `{digest(HERE / 'reference_kernel.py')}`.\n\n## Fixture reports\n\nThe balances-r1 query concerns the original adequacy case. All subsequent displayed queries concern the fixture's local progress case. Raw and usable are summaries of evidence applications, not semantic verdicts. Full labels, exact claim keys, sources, and stamps are in `fixture_results.json`.\n\n| Fixture | Entries at cut | Raw cases | Usable cases | Semantic decision |\n|---|---:|---|---|---|\n{rows}\n\n## Selected live mutations\n\n| Mutation | Result | Reported failing checks |\n|---|---|---:|\n{mrows}\n\nA detected mutation is not counted from a syntax failure or timeout. The individual failures are retained in `mutation_results.json`. The runner does not claim that each mutation is an independent semantic axiom or that every specification requirement is covered.\n\n## Coverage and limits\n\nThe implementation covers finite reference grounding, unique artifact IDs, partial-order cuts, alternative-history constraints, initial ancestry, immutable input-payload snapshots, atomic local references, typed claim-key identity, supplied application dependency and attack graphs, DA-1 labels, evidence-presence summaries, source binding for the integrated fixtures, and selected projection guards. It includes simple absorption and finite-variation reporting helpers.\n\nThe implementation does not discover hidden premises or determine whether a supplied activation judgment is sound. It does not implement full natural-language parsing, persistent storage, a complete target-history interpreter, the typed derivation adapter, semantic authorship or reason-use judgment, generalized progress assessment, or a capacity detector. Some tests use stipulated semantic counterexamples to expose a logical mismatch; those are not experiments on real thinkers.\n\n## Reproduce\n\nFrom the `verification` directory, run:\n\n```sh\npython -m unittest -v\npython run_mutations.py\npython build_reports.py\n```\n\n`build_reports.py` repeats the tests and mutations and regenerates this report and the JSON results using the document bytes present at execution. A later rerun has a new timestamp. It does not modify the authority or specification.\n"""
    (HERE / "Verification_Report.md").write_text(text)
    print(f"{count} tests passed; {len(mutations)} mutations detected; {len(outputs)} fixture slices generated.")


if __name__ == "__main__":
    main()
