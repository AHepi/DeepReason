"""Six mutations of a run root, and which predicate sees them.

The control test `test_committed_roots_are_byte_unchanged_by_this_module`
exists so this module can never move the evidence it reads.  A control is
worth exactly what its mutation proof covers, and the first one covered ONE
class -- a modified top-level `log.jsonl`.  The skeptic pass measured the
rest: the filesystem-keyed predicate it shipped with keyed on
`(Path(line[3:]).parent / "log.jsonl").exists()`, so every mutation that
REMOVES that file, and every file below the root's top level, was invisible.

This runs each arm against REAL `git status` output in a scratch repository
laid out like this one, and asks both predicates.  No committed root is
touched: the arms need a repository they may break, so they get their own.

    python experiments/2026-08-30-change-checkpoint-hardening/proof/control_predicate_arms.py

Writes control_predicate_arms.txt beside itself.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "control_predicate_arms.txt"

ROOT = "experiments/fake-tranche/run-abc"


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, check=True
    ).stdout


def old_predicate(status_nl: str) -> list[str]:
    """The predicate as commit c930d26a9 shipped it, verbatim in behaviour."""

    return [
        line
        for line in status_nl.split("\n")
        if line.strip() and (Path(line[3:].strip()).parent / "log.jsonl").exists()
    ]


def build(where: Path) -> None:
    root = where / ROOT
    (root / "blobs" / "03").mkdir(parents=True)
    (root / "objects").mkdir(parents=True)
    (root / "log.jsonl").write_text('{"seq":0}\n')
    (root / "run-status.json").write_text('{"state":"completed"}\n')
    (root / "blobs" / "03" / "031d5c").write_text("evidence\n")
    (root / "objects" / "problem-1.json").write_text('{"id":"p1"}\n')
    # The legitimate exclusion the narrowing was for: tranche narrative that
    # is NOT inside a root and must never trip the control.
    (where / "experiments" / "fake-tranche" / "PARKED.md").write_text("notes\n")
    (where / "runs").mkdir()
    (where / "runs" / ".keep").write_text("\n")
    git("-C", str(where), "init", "-q")
    git("-C", str(where), "add", "-A")
    git("-C", str(where), "-c", "user.email=a@b", "-c", "user.name=t",
        "commit", "-qm", "roots")


ARMS: list[tuple[str, object]] = [
    ("modify log.jsonl (the original mutation proof)",
     lambda w: (w / ROOT / "log.jsonl").write_text('{"seq":0}\nTAMPER\n')),
    ("delete log.jsonl",
     lambda w: (w / ROOT / "log.jsonl").unlink()),
    ("delete the whole run root",
     lambda w: shutil.rmtree(w / ROOT)),
    ("modify content-addressed evidence under blobs/",
     lambda w: (w / ROOT / "blobs" / "03" / "031d5c").write_text("FORGED\n")),
    ("rename a root file out of the root",
     lambda w: git("-C", str(w), "mv", f"{ROOT}/objects/problem-1.json",
                   "experiments/fake-tranche/problem-1.json")),
    ("CONTROL: edit tranche narrative that is not inside any root",
     lambda w: (w / "experiments" / "fake-tranche" / "PARKED.md").write_text("more\n")),
]


def main() -> int:
    sys.path.insert(0, str(REPO))
    os.environ.setdefault("PYTHONPATH", str(REPO / "src"))
    from tests.test_checkpoint_hardening import _moved_run_root_paths

    lines: list[str] = [
        "control predicate arms -- real git output, scratch repository",
        f"repo under test: {REPO}",
        "",
    ]
    verdicts = []
    for name, mutate in ARMS:
        with tempfile.TemporaryDirectory() as scratch:
            where = Path(scratch) / "repo"
            where.mkdir()
            build(where)
            cwd = Path.cwd()
            os.chdir(where)
            try:
                mutate(where)
                status_z = git("status", "--porcelain", "--untracked-files=no",
                               "-z", "experiments", "runs")
                status_nl = git("status", "--porcelain", "--untracked-files=no",
                                "experiments", "runs")
                tracked = git("ls-files", "-z", "experiments", "runs")
                seen_new = _moved_run_root_paths(status_z, tracked)
                seen_old = old_predicate(status_nl)
            finally:
                os.chdir(cwd)
        expected_red = not name.startswith("CONTROL")
        new_red = bool(seen_new)
        old_red = bool(seen_old)
        verdicts.append((name, expected_red, new_red, old_red))
        lines += [
            f"### {name}",
            f"    git status says      : {status_nl.strip().splitlines()}",
            f"    NEW predicate flags  : {seen_new}",
            f"    OLD predicate flags  : {seen_old}",
            f"    control goes RED     : new={new_red}  old={old_red}"
            f"   (must be {expected_red})",
            "",
        ]
    ok = all(new == want for _n, want, new, _o in verdicts)
    missed_by_old = [n for n, want, _new, old in verdicts if want and not old]
    lines += [
        f"NEW predicate correct on all {len(verdicts)} arms: {ok}",
        f"arms the OLD predicate MISSED ({len(missed_by_old)}): {missed_by_old}",
    ]
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
