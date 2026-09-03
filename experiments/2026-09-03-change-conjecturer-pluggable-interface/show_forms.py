"""Render both conjecturer forms, and demonstrate what "compiles" means.

Read-only. Answers the operator's 2026-09-03 question ("Can you show me both
forms? And explain what compiles?") with a re-derivable artifact rather than
prose, per the repo's own standard that model prose is never evidence.

Three things it shows:

  1. The two registered conjecturer forms side by side, as the model actually
     sees them -- the atomic single-candidate form and the composite turn
     form, the latter both with its optional capabilities off and at the
     LIVE shape the committed roots were run under.
  2. Their sizes, which is the variable the W1 form census and this
     tranche's own census both measure against admission rate.
  3. THE COMPILE STEP: the same candidate, written in each form's own wire
     shape, producing a byte-identical canonical artifact.

    python experiments/2026-09-03-change-conjecturer-pluggable-interface/show_forms.py
"""

from __future__ import annotations

import json
import sys

from deepreason.llm.wire import (
    AliasTable,
    AtomicConjectureWireContractV1,
    ConjecturerTurnWireContractV6,
    minimal_example,
)
from deepreason.run_manifest import ScratchAuthoringPolicyV1

ALIASES = AliasTable({"SRC_001": "artifact-a", "SRC_002": "artifact-b"})


def _live_turn() -> ConjecturerTurnWireContractV6:
    """The turn form at the shape the committed roots actually ran."""

    return ConjecturerTurnWireContractV6(
        reasoning=False,
        aliases=ALIASES,
        scratch_aliases={"SCR_001": "block-a"},
        permitted_retrieval_channels=("scratch",),
        simulation_enabled=True,
        maximum_simulation_proposals=2,
        simulation_input_aliases={"SIM_001": "grid"},
        scratch_authoring_policy=ScratchAuthoringPolicyV1(
            enabled=True,
            maximum_new_blocks_per_turn=3,
            maximum_revisions_per_turn=2,
            maximum_links_per_turn=3,
            maximum_unresolved_questions_per_turn=3,
            maximum_cluster_suggestions_per_turn=2,
            maximum_total_bytes=8000,
        ),
        research_enabled=True,
        maximum_research_proposals=1,
        discharge_enabled=True,
    )


def _tree(root: dict, node: dict, indent: int, seen: frozenset) -> list[str]:
    if "$ref" in node:
        key = node["$ref"].rsplit("/", 1)[-1]
        if key in seen:
            return [" " * indent + f"({key}, recursive)"]
        return _tree(root, root["$defs"][key], indent, seen | {key})
    lines = []
    required = node.get("required") or []
    for name, field in (node.get("properties") or {}).items():
        options = [o for o in (field.get("anyOf") or [field]) if o.get("type") != "null"]
        head = options[0] if options else field
        kind = (
            head.get("type")
            or head.get("$ref", "").rsplit("/", 1)[-1]
            or ("enum" if "enum" in head else "any")
        )
        extra = ""
        if "enum" in head:
            extra += f"  enum={head['enum']}"
        if head.get("maxItems") is not None:
            extra += f"  maxItems={head['maxItems']}"
        if head.get("pattern"):
            extra += f"  pattern={head['pattern']}"
        lines.append(" " * indent + f"{name}{'' if name in required else '?'}: {kind}{extra}")
        nested = head.get("items", head)
        if isinstance(nested, dict) and ("$ref" in nested or "properties" in nested):
            lines += _tree(root, nested, indent + 4, seen)
    return lines


def main() -> int:
    atomic = AtomicConjectureWireContractV1(ALIASES)
    lean = ConjecturerTurnWireContractV6(reasoning=False, aliases=ALIASES)
    live = _live_turn()

    print("SHOW_FORMS_V1\n")
    for label, contract in (
        ("ATOMIC — one candidate per call", atomic),
        ("TURN — optional capabilities OFF", lean),
        ("TURN — LIVE shape (scratch + simulation + research + discharge ON)", live),
    ):
        schema = contract.model_json_schema()
        packed = json.dumps(schema, separators=(",", ":"))
        print(f"===== {label} =====")
        print(
            f"  contract_id {contract.contract_id}"
            f" | wire {contract.wire_model.__name__}"
            f" | canonical {contract.canonical_model.__name__}"
        )
        print(
            f"  schema {len(packed)} bytes"
            f" | {len(schema.get('$defs', {}))} nested definitions"
        )
        print("\n".join(_tree(schema, schema, 2, frozenset())))
        print(f"  minimal example carried in the prompt: {minimal_example(contract)}")
        print()

    print("===== WHAT 'COMPILES' MEANS =====")
    body = {
        "content": "Heat loss scales with surface area, not volume.",
        "typicality": 0.25,
        "neighbours": ["SRC_001"],
    }
    turn_reply = json.dumps({"candidates": [body]})
    atomic_reply = json.dumps({"candidate": body})
    from_turn = lean.parse_compile(turn_reply)
    from_atomic = atomic.parse_compile(atomic_reply)

    print(f"  TURN reply   : {turn_reply}")
    print(f"  ATOMIC reply : {atomic_reply}")
    print(f"\n  both compile to {type(from_turn).__name__}:")
    print(
        "\n".join(
            "    " + line
            for line in json.dumps(
                from_turn.model_dump(mode="json"), indent=2, sort_keys=True
            ).splitlines()
        )
    )
    identical = from_turn.model_dump_json() == from_atomic.model_dump_json()
    print(f"\n  byte-identical canonical artifact from both forms: {identical}")
    print(
        "  note the alias resolution: the wire said neighbours=['SRC_001'],\n"
        "  a call-local handle; the canonical artifact carries\n"
        "  refs=[{role: dependence, target: artifact-a}], the real identifier.\n"
        "  That substitution IS the compile step, and it is the half this\n"
        "  tranche's SPEC (S8.3, assumption A2) forbids from ever varying."
    )
    return 0 if identical else 1


if __name__ == "__main__":
    sys.exit(main())
