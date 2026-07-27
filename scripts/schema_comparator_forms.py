"""Deterministic form transformer for schema comparator v1 (zero tokens).

Builds the three matched representations of every parseable pool item and
freezes them at experiments/schema_comparator_forms_v1.json.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

POOL = Path("experiments/court_cross_pool_v1.json")
OUT = Path("experiments/schema_comparator_forms_v1.json")
EFFECTIVE = 85


def sentences_mentioning(text: str, case: str) -> str | None:
    for sentence in re.split(r"(?<=[.!?])\s+", text or ""):
        if case.lower().split("(")[0].strip()[:12] in sentence.lower():
            return sentence.strip()
    return None


def build_forms(content: str) -> dict | None:
    try:
        skeleton = json.loads(content)
    except ValueError:
        return None
    if not isinstance(skeleton, dict) or "claim" not in skeleton:
        return None
    scope = skeleton.get("scope") or {}
    covers = list(scope.get("covers") or [])
    excludes = list(scope.get("excludes") or [])
    prose = str(skeleton.get("prose_notes") or "")

    comparator = dict(skeleton)
    comparator.pop("scope", None)
    comparator["target_cases"] = covers
    comparator["comparison_cases"] = excludes
    comparator["differential_outcomes"] = [
        {
            "case": case,
            "outcome": "did not undergo the same collapse",
            "explanation": sentences_mentioning(prose, case)
            or "the account does not state a differential explanation for this case",
        }
        for case in excludes
    ]
    forbidden = skeleton.get("forbidden") or []
    prose_form = "\n".join(
        part
        for part in (
            f"CLAIM: {skeleton.get('claim', '')}",
            f"MECHANISM: {skeleton.get('mechanism', '')}",
            "FORBIDDEN CASES (observations that would refute this account): "
            + "; ".join(str(c.get("case", c)) if isinstance(c, dict) else str(c)
                        for c in forbidden)
            if forbidden else "",
            f"NOTES: {prose}" if prose else "",
        )
        if part
    )
    return {
        "A_original": content,
        "B_comparator_aware": json.dumps(comparator, sort_keys=True),
        "C_scope_neutral_prose": prose_form,
    }


def main() -> None:
    pool = json.loads(POOL.read_text())["items"][:EFFECTIVE]
    forms, excluded = [], 0
    for item in pool:
        built = build_forms(item["content"])
        if built is None:
            excluded += 1
            continue
        forms.append({"sha256": item["sha256"], "forms": built})
    OUT.write_text(json.dumps(
        {
            "schema": "deepreason-schema-comparator-forms-v1",
            "source_pool": str(POOL),
            "effective_pool": EFFECTIVE,
            "items": forms,
            "excluded_unparseable": excluded,
        },
        indent=1, sort_keys=True,
    ))
    print(f"forms frozen: {len(forms)} items, {excluded} excluded")


if __name__ == "__main__":
    main()
