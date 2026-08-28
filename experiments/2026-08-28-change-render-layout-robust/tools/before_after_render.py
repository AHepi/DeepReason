"""Render one committed root's conjecturer pack under BOTH shipped policies.

C8 asks for a before -> after with a rendered example from the SAME root as
the census. The provider cannot be re-run, so the comparison is made where it
is decidable offline: the root's own committed epistemic state is replayed and
its pack re-rendered under `render-layout.legacy-v0` (what that run actually
dispatched) and `render-layout.v1` (what it would dispatch today).

The root is COPIED before it is opened. `Harness` opens writable and a
writable open repairs -- that is, destroys -- the evidence.
"""

import pathlib
import shutil
import sys
import tempfile

from deepreason.harness import Harness
from deepreason.llm.layout import (
    DEFAULT_LAYOUT_POLICY_ID,
    LEGACY_LAYOUT_POLICY_ID,
    count_standing_instructions,
    resolve_layout_policy,
)
from deepreason.llm.packs import render_conj_pack

SOURCE = pathlib.Path(
    "experiments/2026-08-25-change-constructive-frontier/"
    "void-inert-battery-run-6913328037a61ca6"
)


def measure(pack: str) -> dict:
    headers = [line[3:] for line in pack.splitlines() if line.startswith("## ")]
    question = "question" if "question" in headers else "problem"
    marker = f"## {question}\n"
    start = pack.index(marker) + len(marker)
    end = pack.find("\n## ", start)
    return {
        "chars": len(pack),
        "sections": len(headers),
        "order": headers,
        "question_section": question,
        "after_question_chars": 0 if end == -1 else len(pack) - end,
        "instructions": count_standing_instructions(pack),
    }


def main() -> int:
    scratch = pathlib.Path(tempfile.mkdtemp())
    root = scratch / "run"
    shutil.copytree(SOURCE, root)
    harness = Harness(root)
    problems = list(harness.state.problems.values())
    if not problems:
        print("root carries no problem", file=sys.stderr)
        return 1
    problem = problems[0]
    out = {}
    for policy_id in (LEGACY_LAYOUT_POLICY_ID, DEFAULT_LAYOUT_POLICY_ID):
        pack = render_conj_pack(
            problem,
            harness.state,
            harness.commitments,
            harness.blobs,
            vs_k=6,
            token_budget=2500,
            layout=resolve_layout_policy(policy_id),
        )
        out[policy_id] = (measure(pack), pack)

    for policy_id, (m, _pack) in out.items():
        print(f"=== {policy_id}")
        for key in ("chars", "sections", "instructions", "question_section",
                    "after_question_chars"):
            print(f"    {key:>22}: {m[key]}")
        print(f"    {'order':>22}: {' -> '.join(m['order'])}")
        print()
    before = out[LEGACY_LAYOUT_POLICY_ID][0]
    after = out[DEFAULT_LAYOUT_POLICY_ID][0]
    print(f"after_question_chars: {before['after_question_chars']} -> "
          f"{after['after_question_chars']}")
    print(f"chars:                {before['chars']} -> {after['chars']} "
          f"({after['chars'] - before['chars']:+d})")
    print(f"instructions:         {before['instructions']} -> "
          f"{after['instructions']} (ceiling "
          f"{resolve_layout_policy().instruction_ceiling})")
    print()
    print("=" * 72)
    print("THE RENDERED PACK, AFTER (render-layout.v1), tail from the "
          "neighbourhood on:")
    print("=" * 72)
    tail = out[DEFAULT_LAYOUT_POLICY_ID][1]
    cut = tail.find("## neighbourhood")
    print(tail[cut if cut != -1 else 0:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
