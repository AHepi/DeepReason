"""The fixed inputs the conjecturer pack golden is captured from (SPEC S10.4).

The tranche this belongs to turns on ONE acceptance test: rendering the brief
under the shipped default layout must produce the same bytes after the
renderer becomes a walk over registered section plugins as it produced before.
A golden can only carry that weight if its inputs are themselves committed and
deterministic, so every case here is built from literals in this file against a
`Harness` in a throwaway directory -- artifact ids are content-derived
(`Artifact.compute_id`), so the same literals give the same ids on every
machine and in every container.

The five cases between them reach every section slot `render_conj_pack` can
emit, the two menu sections, the withheld notice and the restated question.

REGENERATION IS NOT A REPAIR. `python -m tests.conj_pack_golden_cases <dir>`
rewrites the fixtures, and it is legitimate ONLY before the refactor exists or
when the operator has approved a deliberate change to what the default layout
renders. A golden rewritten to make a failing test pass destroys the only
evidence the tranche has (SPEC S10.4, CHECKLIST step 15).
"""

from __future__ import annotations

import pathlib
import sys
import tempfile

from deepreason.harness import Harness
from deepreason.llm.layout import (
    LEGACY_LAYOUT_POLICY,
    ROBUST_LAYOUT_POLICY,
    RenderLayoutPolicyV1,
)
from deepreason.llm.packs import render_conj_pack
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
from deepreason.ontology.commitment import Budget, Commitment
from deepreason.scratch.render import RenderedScratchPackV1, ScratchRenderReceiptV1

FIXTURE_DIRNAME = "conj_pack_legacy_v0"

QUESTION = (
    "Why does the air in a large city stay several degrees warmer than the "
    "surrounding countryside on a clear, calm night?"
)

# A layout that turns the one section the two shipped arrangements both keep
# off. `superseded_summary_n` is an operator knob rather than a default
# (llm/layout.py), so without a third arrangement the golden would never see
# `superseded-conjectures` render at all.
SUPERSEDED_LAYOUT = RenderLayoutPolicyV1(
    policy_id="render-layout.golden-superseded", superseded_summary_n=3
)

_PROP_SOURCE = (
    '"""every candidate names the surface it exchanges heat with."""\n'
    "def check(candidate):\n"
    "    return 'surface' in candidate\n"
)


def _seed(home: pathlib.Path):
    """One deterministic run state, plus the problem and commitments it needs.

    Returns (problem, harness, ids) where `ids` names the artifacts the cases
    cite so a case can be read without re-deriving a content hash.
    """

    harness = Harness(home / "run")

    foundation = harness.create_artifact(
        "FOUNDATION: the surviving stage-1 design — a two-layer surface energy "
        "balance with an explicit sky view factor term.",
        interface=Interface(refs=[]),
        provenance=Provenance(role="seed"),
    )
    lineage = Commitment(
        id="k-lineage",
        eval="program:lineage_ref",
        budget=Budget(extra={"endpoints": foundation.id}),
    )
    surface = Commitment(
        id="k-surface",
        eval="predicate:names_a_surface",
    )
    harness.register_commitment(lineage)
    harness.register_commitment(surface)

    problem = harness.register_problem(
        Problem(
            id="p-golden",
            description=QUESTION,
            criteria=["k-lineage", "k-surface"],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )

    # An accepted proposed property: the `active-properties` section reads
    # ACCEPTED `code:python-prop` artifacts holding a MENTION ref into the
    # problem's own criteria, and nothing else.
    harness.create_artifact(
        _PROP_SOURCE,
        codec="code:python-prop",
        interface=Interface(
            refs=[Ref(target="k-surface", role=RefRole.MENTION)]
        ),
        provenance=Provenance(role="conjecturer"),
    )

    accepted = [
        harness.create_artifact(
            f"ACCEPTED CANDIDATE {n}: stored heat released from masonry after "
            f"sunset keeps the urban boundary layer {n} degrees warmer.",
            interface=Interface(refs=[]),
            provenance=Provenance(role="conjecturer"),
        )
        for n in (1, 2, 3, 4)
    ]

    # One REFUTED artifact, so the superseded case has something to show. A
    # sound, relevant argumentative warrant is what moves a status.
    doomed = harness.create_artifact(
        "REFUTED CANDIDATE: the whole gap is waste heat from vehicle engines.",
        interface=Interface(refs=[]),
        provenance=Provenance(role="conjecturer"),
    )
    nu = harness.create_artifact(
        "nu: the vehicle-heat attack is sound and relevant",
        interface=Interface(refs=[]),
        provenance=Provenance(role="critic"),
    )
    harness.create_artifact(
        "critic: measured vehicle heat flux is an order of magnitude short",
        provenance=Provenance(role="critic"),
        warrants=[
            Warrant(
                id="w-vehicle-heat",
                target=doomed.id,
                type=WarrantType.ARGUMENTATIVE,
                validity_node=nu.id,
            )
        ],
    )

    ids = {
        "foundation": foundation.id,
        "accepted": tuple(a.id for a in accepted),
        "refuted": doomed.id,
    }
    return problem, harness, ids


def _seed_bare(home: pathlib.Path):
    """The floor: a problem, one ordinary commitment, and an empty state.

    Deliberately NOT the rich seed with its foundation commitment and its
    accepted property -- `minimal` exists to pin what a first cycle renders,
    when the run has produced nothing yet.
    """

    harness = Harness(home / "bare")
    harness.register_commitment(
        Commitment(id="k-surface", eval="predicate:names_a_surface")
    )
    return harness.register_problem(
        Problem(
            id="p-golden-bare",
            description=QUESTION,
            criteria=["k-surface"],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    ), harness


def _scratch_context() -> dict:
    # `create` hashes exactly the keyword set it is given while the model's
    # own validator re-hashes the full dump, so every field is named here.
    receipt = ScratchRenderReceiptV1.create(
        state_seq=7,
        attention_receipt="sha256:" + "ab" * 32,
        block_handles={"B1": "sha256:" + "cd" * 32},
        cluster_handles={},
        link_handles={},
        guide_handles={},
    )
    return RenderedScratchPackV1(
        text=(
            "SCRATCH (advisory; nothing here is admitted evidence):\n"
            "- B1: the countryside cools faster because its sky view factor "
            "is close to one."
        ),
        receipt=receipt,
        truncated_fields=0,
    ).model_dump(mode="json", by_alias=True)


def _menus(ids) -> tuple:
    return menu_renders_for(
        "conjecturer.turn.v6",
        MenuBinding(citable_block_ids=("EV-001", "EV-002", "EV-003")),
        handle_kinds=("citable_block",),
    )


def _rich_kwargs(problem, harness, ids) -> dict:
    """Every optional context the renderer accepts, supplied at once."""

    return dict(
        problem=problem,
        state=harness.state,
        commitments=harness.commitments,
        blobs=harness.blobs,
        vs_k=3,
        school={
            "id": "school-thermal",
            "stance_text": "prefer explanations grounded in surface energy "
                           "balance over explanations grounded in emissions.",
            "weight": 0.62,
            "crossover": [ids["accepted"][0]],
        },
        complement=True,
        specs=[
            "a mechanism operating at the street canyon scale",
            "a mechanism operating at the regional boundary layer scale",
            "a mechanism that would be falsified by a windy night",
        ],
        neighbourhood_n=4,
        generation_context="prior rounds converged on radiative terms; the "
                           "convective side is unexplored.",
        scratch_context=_scratch_context(),
        frozen_evidence_context="FROZEN EVIDENCE (attached, digest-bound):\n"
                                "- EV-001: hourly screen-level temperatures, "
                                "12 station pairs, one clear-sky August.",
        citable_evidence_context="CITABLE BLOCKS:\n- EV-001\n- EV-002\n"
                                 "- EV-003",
        capability_result_context="program: sky_view_factor(canyon_ratio=1.4) "
                                  "-> 0.41",
        frame_slice_context="FRAME SLICE: the run is arguing inside a "
                            "surface-energy-balance frame.",
        frame_crisis_context="FRAME CRISIS: two accepted artifacts disagree "
                             "about whether advection is in scope.",
        open_criticism_context="OPEN CRITICISMS (discharge every handle):\n"
                               "- OC-1: no candidate has addressed wind speed.",
        allow_no_candidate_outcome=True,
        reference_menus=_menus(ids),
    )


def cases(home: pathlib.Path) -> dict[str, str]:
    """name -> rendered pack bytes, for the fixed inputs above."""

    problem, harness, ids = _seed(home)
    rich = _rich_kwargs(problem, harness, ids)

    bare_problem, bare = _seed_bare(home)
    minimal = dict(
        problem=bare_problem,
        state=bare.state,
        commitments=bare.commitments,
        blobs=bare.blobs,
        vs_k=2,
        token_budget=4000,
        neighbourhood_n=0,
        layout=ROBUST_LAYOUT_POLICY,
    )

    return {
        # Problem and criteria only: no optional context, no neighbourhood,
        # no menus. The floor every configuration renders.
        "minimal": render_conj_pack(**minimal),
        # Every optional context at a budget wide enough to keep all of them.
        "maximal": render_conj_pack(
            **rich, token_budget=6000, layout=ROBUST_LAYOUT_POLICY
        ),
        # The same inputs at a budget tight enough that the allocator cuts a
        # DISCLOSED_ON_DROP section and the withheld notice is forced.
        "withheld": render_conj_pack(
            **rich, token_budget=900, layout=ROBUST_LAYOUT_POLICY
        ),
        # The arrangement every committed root was rendered under.
        "legacy_layout": render_conj_pack(
            **rich, token_budget=6000, layout=LEGACY_LAYOUT_POLICY
        ),
        # The one section neither shipped arrangement turns on.
        "superseded": render_conj_pack(
            **rich, token_budget=6000, layout=SUPERSEDED_LAYOUT
        ),
    }


def render_all() -> dict[str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        return cases(pathlib.Path(tmp))


def main(argv: list[str]) -> int:
    target = pathlib.Path(
        argv[1] if len(argv) > 1 else pathlib.Path(__file__).parent / "fixtures" / FIXTURE_DIRNAME
    )
    target.mkdir(parents=True, exist_ok=True)
    for name, text in render_all().items():
        (target / f"{name}.txt").write_text(text, encoding="utf-8")
        print(f"{name}.txt {len(text)} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
