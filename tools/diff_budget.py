#!/usr/bin/env python3
"""Actual-diff budget gate (Rung G1): measure real cumulative insertions
against a ledgered ceiling, not a plan-time estimate.

Recorded failure this closes: Rung S5 overran its ledgered budget twice
(REQUEST.md Amendments 2 and 3) because the ceiling was checked against
SPEC.md's own headline estimate, never against `git diff`'s actual count,
and the headline itself understated its own itemization by ~135 lines.

Usage:
    python tools/diff_budget.py <base> [--against REF] [--ceiling N] [--paths PATH ...]
    python tools/diff_budget.py --self-test

`<base>` is diffed against `--against REF` if given, else the current
working tree (staged and unstaged, matching the two-command convention
`git diff --stat <base>..HEAD` plus the working tree it replaces). Insertion
counts only -- a budget ceiling bounds what is ADDED, and this gate exists
to check that number, never deletions.

`git diff` is blind to files git has never seen: a brand-new file must be
`git add`ed before this gate can count it, same as any other `git diff`
invocation. Run `git add -A` (or the step's specific files) before this
gate, not after -- checking the budget on partially-staged work undercounts
exactly the files a step just created.

Emits one DIFF_BUDGET_RESULT_V1 JSON object to stdout on success:

    {
      "result_type": "DIFF_BUDGET_RESULT_V1",
      "base": "<base ref as given>",
      "against": "<against ref as given, or null for working tree>",
      "areas": {"<path-or-'total'>": <insertions:int>, ...},
      "total_insertions": <int>,
      "ceiling": <int|null>,
      "verdict": "WITHIN" | "EXCEEDED" | "NO_CEILING"
    }

Exit classes -- semantic verdicts live INSIDE the JSON, never in the exit
code; EXCEEDED is exit 0 like any other result, because the gate reports a
fact and the calling skill decides the policy:
    0  result emitted       -- JSON printed; verdict may be EXCEEDED
    2  invalid invocation   -- bad arguments; no JSON printed
    3  evidence unavailable -- a ref does not resolve, or this is not a
                                git work tree; no JSON printed
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

RESULT_TYPE = "DIFF_BUDGET_RESULT_V1"


class InvalidInvocation(Exception):
    pass


class EvidenceUnavailable(Exception):
    pass


def _run_git(args: list[str]) -> str:
    try:
        proc = subprocess.run(["git", *args], capture_output=True, text=True)
    except FileNotFoundError as error:
        raise EvidenceUnavailable(f"git not available: {error}") from error
    if proc.returncode != 0:
        raise EvidenceUnavailable(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc.stdout


def _insertions(base: str, against: str | None, paths: list[str]) -> int:
    """Sum insertion counts from `git diff --numstat` restricted to `paths`
    (the whole diff if empty). A "-\t-" numstat row is a binary file, whose
    line counts git cannot report; it contributes zero insertions rather
    than raising, since a budget gate that dies on a binary file in the
    diff is worse than one that under-counts it."""
    args = ["diff", "--numstat", base]
    if against is not None:
        args.append(against)
    if paths:
        args.append("--")
        args.extend(paths)
    total = 0
    for line in _run_git(args).splitlines():
        if not line.strip():
            continue
        added = line.split("\t", 1)[0]
        if added == "-":
            continue
        total += int(added)
    return total


def compute(base: str, against: str | None, ceiling: int | None, paths: list[str]) -> dict:
    areas = (
        {path: _insertions(base, against, [path]) for path in paths}
        if paths
        else {"total": _insertions(base, against, [])}
    )
    total_insertions = _insertions(base, against, [])
    if ceiling is None:
        verdict = "NO_CEILING"
    elif total_insertions <= ceiling:
        verdict = "WITHIN"
    else:
        verdict = "EXCEEDED"
    return {
        "result_type": RESULT_TYPE,
        "base": base,
        "against": against,
        "areas": areas,
        "total_insertions": total_insertions,
        "ceiling": ceiling,
        "verdict": verdict,
    }


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="diff_budget.py",
        description="Actual-diff budget gate: cumulative insertions vs a ledgered ceiling.",
    )
    parser.add_argument("base", nargs="?", help="base ref to diff from")
    parser.add_argument("--against", default=None, help="ref to diff against (default: working tree)")
    parser.add_argument("--ceiling", type=int, default=None, help="insertion ceiling")
    parser.add_argument("--paths", nargs="+", default=[], help="pathspecs, one area each")
    parser.add_argument("--self-test", action="store_true", help="run the fixture self-test and exit")
    namespace = parser.parse_args(argv)
    if not namespace.self_test and namespace.base is None:
        raise InvalidInvocation("<base> is required")
    if namespace.ceiling is not None and namespace.ceiling < 0:
        raise InvalidInvocation("--ceiling must be >= 0")
    return namespace


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    if "--self-test" in argv:
        return _self_test()
    try:
        namespace = _parse_args(argv)
    except InvalidInvocation as error:
        print(f"invalid invocation: {error}", file=sys.stderr)
        return 2
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 2
        return 2 if code != 0 else 0
    try:
        result = compute(namespace.base, namespace.against, namespace.ceiling, namespace.paths)
    except EvidenceUnavailable as error:
        print(f"evidence unavailable: {error}", file=sys.stderr)
        return 3
    print(json.dumps(result))
    return 0


def _self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)

        def git(*args: str) -> None:
            subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)

        def run(*args: str) -> subprocess.CompletedProcess:
            return subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), *args],
                cwd=repo, capture_output=True, text=True,
            )

        git("init", "-q")
        git("config", "user.email", "test@example.com")
        git("config", "user.name", "Test")
        (repo / "a.txt").write_text("line\n" * 10)
        (repo / "b.txt").write_text("line\n" * 10)
        git("add", "-A")
        git("commit", "-q", "-m", "base")
        base = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
        ).stdout.strip()
        (repo / "a.txt").write_text("line\n" * 10 + "new\n" * 5)
        (repo / "b.txt").write_text("line\n" * 10 + "new\n" * 3)
        git("add", "-A")
        git("commit", "-q", "-m", "change")

        result = run(base, "--ceiling", "5")
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["total_insertions"] == 8, data
        assert data["verdict"] == "EXCEEDED", data

        result = run(base, "--ceiling", "8")
        data = json.loads(result.stdout)
        assert data["verdict"] == "WITHIN", data

        result = run(base)
        data = json.loads(result.stdout)
        assert data["verdict"] == "NO_CEILING", data

        result = run(base, "--paths", "a.txt", "b.txt")
        data = json.loads(result.stdout)
        assert data["areas"] == {"a.txt": 5, "b.txt": 3}, data
        assert data["total_insertions"] == 8, data

        result = run()
        assert result.returncode == 2, result.stderr

        result = run("not-a-real-ref")
        assert result.returncode == 3, result.stderr

    print("SELF-TEST PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
