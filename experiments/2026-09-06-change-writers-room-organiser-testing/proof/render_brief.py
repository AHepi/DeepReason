"""The organiser's rendered brief, shown before any live call (SPEC S11, R11).

One conjecturer dispatch against the stub root of `tests/test_organiser_seat.py`
-- the committed attachment bound as the dossier under the managed envelope,
PACK_TOKEN_BUDGET 24000, the organiser shell and wording selected -- with a
mock endpoint that abstains. Writes the exact prompt the seat would receive
to ORGANISER_BRIEF.txt and the section plan the run recorded (which plugin
rendered, compressed, dropped or was absent, and at how many bytes) to
ORGANISER_RECEIPTS.json.

    python proof/render_brief.py
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO))


def main() -> int:
    os.environ["DEEPREASON_SEAT_SHELL"] = (
        "conjecturer=seat.conjecturer.organiser-v1"
    )
    os.environ["DEEPREASON_ROLE_PROMPT_TEMPLATE"] = "role-prompt.organiser-v1"
    from deepreason.llm.seat_plugins import ensure_seeded

    ensure_seeded()
    import tests.test_organiser_seat as fixture
    from tests.test_p4_citable_evidence import _abstain

    with tempfile.TemporaryDirectory() as scratch:
        root = pathlib.Path(scratch)
        harness, manifest, config, dossier, seed_id = fixture._room_root(root)
        prompts, _ = fixture._dispatch(harness, manifest, config, seed_id, _abstain())
        (prompt,) = prompts
        plans = []
        for path in sorted((root / "organiser-root" / "objects").rglob("*.json")):
            if "section-plan" not in path.parent.name:
                continue
            plans.append(json.loads(path.read_text(encoding="utf-8")))
    (HERE / "ORGANISER_BRIEF.txt").write_text(prompt, encoding="utf-8")
    receipts = {
        "schema": "organiser-brief-receipts.v1",
        "pack_token_budget": config.PACK_TOKEN_BUDGET,
        "prompt_chars": len(prompt),
        "prompt_bytes": len(prompt.encode("utf-8")),
        "section_plans": plans,
    }
    (HERE / "ORGANISER_RECEIPTS.json").write_text(
        json.dumps(receipts, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    rows = []
    for plan in plans:
        for row in (plan.get("data") or plan).get("sections", []):
            rows.append((row.get("section_id"), row.get("plugin_id"), row.get("disposition"), row.get("rendered_bytes")))
    print(f"prompt {len(prompt)} chars; section plans {len(plans)}")
    for row in rows:
        print("  ", row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
