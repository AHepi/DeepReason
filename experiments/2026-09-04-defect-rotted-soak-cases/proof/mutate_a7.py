"""Mutation proof for A7-record-fully-read, in BOTH directions.

Lives OUTSIDE scripts/ deliberately: a proof that shares a file with the thing
it judges can be made to pass by the same edit that breaks the subject.

Usage:  python proof/mutate_a7.py <kept-soak-root>
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
import cycle_soak  # noqa: E402


def a7(root: Path) -> dict:
    checks = cycle_soak.assess_run(
        root, {"typed_error": None, "terminal": {}}, cycles=8, case=None, criteria=[]
    )
    return next(c for c in checks if c["id"] == "A7-record-fully-read")


def main() -> int:
    root = Path(sys.argv[1])
    clean = a7(root)
    print(f"  clean root      -> ok={clean['ok']}  {clean['detail']}")

    mutant = root.parent / (root.name + "-mutant")
    if mutant.exists():
        shutil.rmtree(mutant)
    shutil.copytree(root, mutant)
    victims = sorted((mutant / "objects" / "workflow-provider-attempt-v1").glob("*.json"))
    if not victims:
        print("  NO ATTEMPT RECORDS -- cannot mutate; proof inconclusive")
        return 2
    victims[0].write_text("{ this is not json")
    dirty = a7(mutant)
    print(f"  one byte broken -> ok={dirty['ok']}  {dirty['detail']}")

    ok = clean["ok"] is True and dirty["ok"] is False
    print(f"\n  MUTATION PROOF: {'PASS' if ok else 'FAIL'} "
          f"(silent on a clean record, fires on a broken one)")
    shutil.rmtree(mutant)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
