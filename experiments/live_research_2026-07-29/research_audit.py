"""Audit one completed run's durable research-capability record.

Usage: research_audit.py <deepreason_home> <run_id>

Everything printed is re-derived from the append-only log and
content-addressed objects alone: proposals, the full transition chain,
fetch receipts, consumptions, citable blocks, and every
research-fetch / evidence-citation measure.
"""

import json
import os
import sys

HOME, RUN_ID = sys.argv[1], sys.argv[2]
os.environ["DEEPREASON_HOME"] = HOME

from deepreason.capabilities.models import (  # noqa: E402
    ResearchConsumptionV1,
    ResearchExecutionReceiptV1,
    ResearchFetchProposalV1,
    ResearchResultPackageV1,
)
from deepreason.capabilities.research import consumed_research_blocks  # noqa: E402
from deepreason.harness import Harness  # noqa: E402
from deepreason.preparation import resolve_managed_run_root  # noqa: E402

root = resolve_managed_run_root(RUN_ID)
harness = Harness(root, read_only=True)
state = harness.capability_state

proposals = [
    {
        "id": p.id,
        "index": p.proposal_index,
        "purpose": p.purpose,
        "urls": list(p.urls),
        "work": p.originating_work_order_ref,
    }
    for p in state.proposals.values()
    if isinstance(p, ResearchFetchProposalV1)
]
transitions = [
    {
        "request": t.request_ref[:24],
        "lifecycle": t.lifecycle.value,
        "reason": t.reason_code,
    }
    for t in state.transitions.values()
    if any(t.request_ref == p["id"] for p in proposals)
]
receipts = [
    {
        "proposal": r.proposal_ref[:24],
        "outcome": r.outcome,
        "used": r.requests_used_total,
        "limit": r.requests_limit,
        "attempts": [
            {
                "url": a.url,
                "outcome": a.outcome,
                "status": a.http_status,
                "bytes": a.byte_count,
            }
            for a in r.attempts
        ],
    }
    for r in state.receipts.values()
    if isinstance(r, ResearchExecutionReceiptV1)
]
consumptions = [
    {
        "proposal": c.proposal_ref[:24],
        "evidence_refs": list(c.evidence_refs),
    }
    for c in state.consumptions.values()
    if isinstance(c, ResearchConsumptionV1)
]
packages = [
    {
        "proposal": p.proposal_ref[:24],
        "items": [
            {"url": i.url, "bytes": i.byte_count, "text": i.text_sha256[:16]}
            for i in p.items
        ],
    }
    for p in state.result_packages.values()
    if isinstance(p, ResearchResultPackageV1)
]
blocks = consumed_research_blocks(harness)
measures = [
    list(event.inputs)
    for event in harness.log.read()
    if event.inputs
    and any(
        str(value).startswith(("research-fetch:", "evidence-citation:"))
        for value in event.inputs
    )
]

print(
    json.dumps(
        {
            "run_id": RUN_ID,
            "proposals": proposals,
            "transitions": transitions,
            "receipts": receipts,
            "packages": packages,
            "consumptions": consumptions,
            "citable_blocks": [block.id[:16] for block in blocks],
            "measures": measures,
        },
        indent=2,
    )
)
