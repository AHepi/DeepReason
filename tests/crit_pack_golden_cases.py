"""The fixed inputs the CRITIC pack golden is captured from (SPEC S10.4, §17.3).

Amendment 2 makes the acceptance test two-seated: the critic's brief must
render the same bytes after `render_crit_pack` becomes a walk over registered
section plugins as it renders before. Built exactly like its conjecturer
sibling (`tests/conj_pack_golden_cases.py`) — literals in this file against a
`Harness` in a throwaway directory, so the state reproduces anywhere.

The four cases between them reach all thirteen critic section slots, the menu
section, the withheld notice and the restated question.

REGENERATION IS NOT A REPAIR. `python -m tests.crit_pack_golden_cases <dir>`
rewrites the fixtures, and it is legitimate ONLY before the refactor exists or
when the operator has approved a deliberate change to what the default layout
renders (SPEC S10.4, §17.3; CHECKLIST step 21).
"""

from __future__ import annotations

import pathlib
import sys
import tempfile

from deepreason.harness import Harness
from deepreason.llm.layout import LEGACY_LAYOUT_POLICY, ROBUST_LAYOUT_POLICY
from deepreason.llm.packs import render_crit_pack
from deepreason.llm.reference_menu import MenuBinding, menu_renders_for
from deepreason.ontology import (
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    Ref,
    Warrant,
    WarrantType,
)
from deepreason.ontology.artifact import RefRole
from deepreason.ontology.commitment import Commitment

FIXTURE_DIRNAME = "crit_pack_legacy_v0"

QUESTION = (
    "Why does the air in a large city stay several degrees warmer than the "
    "surrounding countryside on a clear, calm night?"
)


def _seed(home: pathlib.Path):
    """One deterministic state carrying a rich target and a bare one.

    The rich target declares an execution oracle (so `counterexample-recourse`
    renders), a support chain into known artifacts (so both support sections
    render) and already carries one standing attack.
    """

    harness = Harness(home / "run")

    harness.register_commitment(
        Commitment(id="k-exec", eval="program:exec_oracle")
    )
    harness.register_commitment(
        Commitment(id="k-surface", eval="predicate:names_a_surface")
    )

    problem = harness.register_problem(
        Problem(
            id="p-golden-crit",
            description=QUESTION,
            criteria=["k-exec", "k-surface"],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )

    support_a = harness.create_artifact(
        "SUPPORT A: nocturnal boundary layers over masonry decouple from the "
        "regional flow below about two metres per second.",
        interface=Interface(refs=[]),
        provenance=Provenance(role="seed"),
        problem_id=problem.id,
    )
    support_b = harness.create_artifact(
        "SUPPORT B: measured sky view factors in the study canyons range from "
        "0.34 to 0.58.",
        interface=Interface(refs=[]),
        provenance=Provenance(role="seed"),
        problem_id=problem.id,
    )

    target = harness.create_artifact(
        "TARGET CLAIM: the nocturnal urban-rural gap is set by the sky view "
        "factor, which fixes how much longwave radiation escapes to the cold "
        "sky; stored heat release is a second-order term.",
        interface=Interface(
            commitments=["k-exec", "k-surface"],
            refs=[
                Ref(target=support_a.id, role=RefRole.DEPENDENCE),
                Ref(target=support_b.id, role=RefRole.MENTION),
            ],
        ),
        provenance=Provenance(role="conjecturer"),
        problem_id=problem.id,
    )

    # One standing attack, so `standing-attacks` renders.
    nu = harness.create_artifact(
        "nu: the advection attack is sound and relevant",
        interface=Interface(refs=[]),
        provenance=Provenance(role="critic"),
    )
    harness.create_artifact(
        "critic: the claim ignores regional advection on the calm nights it "
        "is measured over.",
        provenance=Provenance(role="critic"),
        warrants=[
            Warrant(
                id="w-advection",
                target=target.id,
                type=WarrantType.ARGUMENTATIVE,
                validity_node=nu.id,
            )
        ],
    )

    bare = harness.create_artifact(
        "BARE TARGET: cities are warmer at night because there are more "
        "people in them.",
        interface=Interface(refs=[]),
        provenance=Provenance(role="conjecturer"),
    )

    return harness, problem, target.id, bare.id


def _menus() -> tuple:
    return menu_renders_for(
        "conjecturer.turn.v6",
        MenuBinding(citable_block_ids=("EV-001", "EV-002")),
        handle_kinds=("citable_block",),
    )


def _rich_kwargs(harness, problem, target_id) -> dict:
    return dict(
        target_id=target_id,
        state=harness.state,
        commitments=harness.commitments,
        blobs=harness.blobs,
        premise_invitation=problem.id,
        citable_evidence_context="CITABLE BLOCKS:\n- EV-001\n- EV-002",
        frame_slice_context="FRAME SLICE: the run is arguing inside a "
                            "surface-energy-balance frame.",
        frame_crisis_context="FRAME CRISIS: two accepted artifacts disagree "
                             "about whether advection is in scope.",
        reference_menus=_menus(),
    )


def cases(home: pathlib.Path) -> dict[str, str]:
    """name -> rendered pack bytes, for the fixed inputs above."""

    harness, problem, target_id, bare_id = _seed(home)
    rich = _rich_kwargs(harness, problem, target_id)

    return {
        # A target with no support chain, no attackers, no optional context.
        "minimal": render_crit_pack(
            target_id=bare_id,
            state=harness.state,
            commitments=harness.commitments,
            blobs=harness.blobs,
            token_budget=4000,
            layout=ROBUST_LAYOUT_POLICY,
        ),
        # Every optional context at a budget wide enough to keep all of them.
        "maximal": render_crit_pack(
            **rich, token_budget=6000, layout=ROBUST_LAYOUT_POLICY
        ),
        # Tight enough that the allocator cuts a DISCLOSED_ON_DROP section
        # (standing-attacks, premise-invitation) and forces the notice.
        "withheld": render_crit_pack(
            **rich, token_budget=520, layout=ROBUST_LAYOUT_POLICY
        ),
        # The arrangement every committed root was rendered under.
        "legacy_layout": render_crit_pack(
            **rich, token_budget=6000, layout=LEGACY_LAYOUT_POLICY
        ),
    }


def render_all() -> dict[str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        return cases(pathlib.Path(tmp))


def main(argv: list[str]) -> int:
    target = pathlib.Path(
        argv[1] if len(argv) > 1
        else pathlib.Path(__file__).parent / "fixtures" / FIXTURE_DIRNAME
    )
    target.mkdir(parents=True, exist_ok=True)
    for name, text in render_all().items():
        (target / f"{name}.txt").write_text(text, encoding="utf-8")
        print(f"{name}.txt {len(text)} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
