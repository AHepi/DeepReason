"""The dry attach (SPEC S5, R5): how many blocks are admitted, how many one
call can see, and what the pack receipt withholds -- measured offline, before
any live call, on the committed attachment.

Two halves. First, ADMISSION through the same function `reason --attach`
calls (`admission/attach.py::admit_attachment_paths`, via a throwaway
admission store so nothing is written under the operator's home). Second, ONE
organiser render against a stub root that binds THIS dossier under the
managed attached-evidence envelope, reading the legend, the frozen pack and
the section receipts from the same fixture the stub test uses.

    python proof/dry_attach.py > proof/DRY_ATTACH.txt
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
TRANCHE = HERE.parent
REPO = TRANCHE.parents[1]
sys.path.insert(0, str(REPO))
ATTACHMENT = TRANCHE / "attachment"
FILES = ("01-conjectures.txt", "02-proposals.txt", "03-objections.txt")
QUESTION_FILE = (
    REPO / "experiments/2026-09-05-change-mini-isolation-programme/runs/input-d8/run-input.json"
)


def admission() -> dict:
    from deepreason.admission.attach import admit_attachment_paths

    question = json.loads(QUESTION_FILE.read_text())["problem"]["description"]
    with tempfile.TemporaryDirectory() as scratch:
        os.environ["DEEPREASON_HOME"] = scratch
        # The three files by name, never the directory: `--attach <dir>`
        # admits EVERY file under it, and the attachment directory also holds
        # CONVERSION.json and ATTACHMENT.sha256 (measured here first: the
        # directory form admitted 5 sources and 105 blocks). armR.sh passes
        # the same three paths.
        admitted = admit_attachment_paths(
            question, [str(ATTACHMENT / n) for n in FILES], supplied_by="dry attach", allow_partial=False
        )
    dossier, report = admitted.dossier, admitted.report
    by_file = {}
    for name in ("01-conjectures.txt", "02-proposals.txt", "03-objections.txt"):
        digest = hashlib.sha256((ATTACHMENT / name).read_bytes()).hexdigest()
        by_file[name] = sum(1 for b in dossier.blocks if b.source_sha256 == digest)
    return {
        "question_sha256": hashlib.sha256(question.encode()).hexdigest(),
        "dossier_digest": dossier.dossier_digest,
        "sources": report.source_count,
        "blocks": dict(report.block_counts),
        "tiers": dict(report.tier_counts),
        "refusals": list(report.refusals),
        "blocks_by_file": by_file,
        "blocks_sorted_by_id": list(dossier.blocks) == sorted(dossier.blocks, key=lambda b: b.id),
    }


def one_render() -> dict:
    os.environ["DEEPREASON_SEAT_SHELL"] = (
        "conjecturer=seat.conjecturer.organiser-v1,argumentative_critic=seat.critic.evidence-blind-v1"
    )
    os.environ["DEEPREASON_ROLE_PROMPT_TEMPLATE"] = "role-prompt.organiser-v1"
    from deepreason.llm.seat_plugins import ensure_seeded

    ensure_seeded()
    import tests.test_organiser_seat as fixture
    from tests.test_p4_citable_evidence import _abstain

    with tempfile.TemporaryDirectory() as scratch:
        harness, manifest, config, dossier, seed_id = fixture._room_root(pathlib.Path(scratch))
        prompts, _ = fixture._dispatch(harness, manifest, config, seed_id, _abstain())
        (prompt,) = prompts
        # The pack receipt: what one call was allowed to show, from the record.
        receipts = [
            e for e in harness.log.read() if e.inputs and e.inputs[0] == "dossier-pack-receipt.v1"
        ]
        (work,) = harness.workflow_state.transaction_work.values()
        exposed = [
            item.object_ref for item in work.exposure.exposed_items
            if item.namespace.value == "evidence"
        ]
    shown = [b for b in dossier.blocks if f"[{b.id[:16]}]" in prompt]
    kinds = {}
    for name in ("01-conjectures.txt", "02-proposals.txt", "03-objections.txt"):
        digest = hashlib.sha256((ATTACHMENT / name).read_bytes()).hexdigest()
        kinds[name] = sum(1 for b in shown if b.source_sha256 == digest)
    refuted_if_shown = 0
    for b in shown:
        src = next(p for p in ATTACHMENT.glob("*.txt")
                   if hashlib.sha256(p.read_bytes()).hexdigest() == b.source_sha256)
        head = src.read_bytes()[b.span_start:b.span_end].decode().split("\n", 1)[0]
        # The header no longer ends with the kind (P7 road A moved the
        # target reference to the tail); match the field itself.
        refuted_if_shown += " kind=refuted-if" in head
    return {
        "prompt_chars": len(prompt),
        "prompt_bytes": len(prompt.encode("utf-8")),
        "frozen_pack_sources": prompt.count("BEGIN UNTRUSTED SOURCE DATA"),
        "excluded_source_ids_line_present": "excluded_source_ids=" in prompt,
        "pack_receipt_events": len(receipts),
        "legend_shown": len(shown),
        "legend_withheld": len(dossier.blocks) - len(shown),
        "legend_shown_by_file": kinds,
        "legend_refuted_if_shown": refuted_if_shown,
        "exposure_receipt_items": len(exposed),
        "exposure_equals_legend": set(exposed) == {b.id for b in shown},
        "withheld_notice": (
            f"(+{len(dossier.blocks) - len(shown)} further citable blocks not shown)"
            in prompt
        ),
        "organiser_directive": "DIRECTIVE: ORGANISE, DO NOT INVENT." in prompt,
        "pack_token_budget": config.PACK_TOKEN_BUDGET,
    }


def main() -> int:
    a = admission()
    r = one_render()
    print("== dry attach: admission (admit_attachment_paths, the function reason --attach calls) ==")
    print(f"sources {a['sources']} blocks {sum(a['blocks'].values())} refusals {len(a['refusals'])}")
    print(json.dumps(a, indent=1, sort_keys=True))
    print("== one organiser render against the stub root (managed envelope: 16 sources, 8 per pack) ==")
    print(f"legend shown {r['legend_shown']} withheld {r['legend_withheld']}")
    print(f"frozen pack sources {r['frozen_pack_sources']} excluded {int(r['excluded_source_ids_line_present'])}")
    print(json.dumps(r, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
