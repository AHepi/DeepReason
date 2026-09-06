"""Reproduction for the criticism-premise-declaration tranche.

Three arms over ONE four-artifact graph. The first two are the §0 script of
`docs/proposals/OIS_1_1_to_DeepReason_configuration.md`, unchanged. The third
is this tranche's falsifiable prediction: keep the criticism's own DEPENDENCE
ref exactly where §0 put it, and add ONE `EVIDENCE` ref on the criticism's
validity node ν -- the only thing a mint site would do differently if the
critic could declare what its case rests on.

Run offline; no run root, no provider, no key.
"""

import pathlib
import tempfile

from deepreason.harness import Harness
from deepreason.ontology import Interface, Provenance, Ref, Warrant, WarrantType
from deepreason.ontology.artifact import RefRole


def _scenario(*, criticism_ref_role, nu_declares_premise):
    """`a` is attacked by a criticism that leans on `k`; then `k` is refuted.

    `criticism_ref_role` is the role the criticism artifact carries toward
    `k`. `nu_declares_premise` decides whether the criticism's VALIDITY NODE
    also declares `k` -- as `EVIDENCE`, the closure's only entry point.
    """
    harness = Harness(pathlib.Path(tempfile.mkdtemp()) / "run")
    a = harness.create_artifact("tilt account", provenance=Provenance(role="seed"))
    k = harness.create_artifact("standard k", provenance=Provenance(role="seed"))

    nu_refs = [Ref(target=k.id, role=criticism_ref_role)]
    if nu_declares_premise:
        nu_refs = [Ref(target=k.id, role=RefRole.EVIDENCE)]
    nu = harness.create_artifact(
        "nu of criticism",
        provenance=Provenance(role="critic"),
        interface=Interface(refs=nu_refs),
    )
    criticism = harness.create_artifact(
        "criticism of tilt using k",
        provenance=Provenance(role="critic"),
        interface=Interface(refs=[Ref(target=k.id, role=criticism_ref_role)]),
        warrants=[
            Warrant(
                id="w1",
                target=a.id,
                type=WarrantType.ARGUMENTATIVE,
                validity_node=nu.id,
            )
        ],
    )

    nu2 = harness.create_artifact("nu2", provenance=Provenance(role="critic"))
    harness.create_artifact(
        "criticism of k",
        provenance=Provenance(role="critic"),
        warrants=[
            Warrant(
                id="w2",
                target=k.id,
                type=WarrantType.ARGUMENTATIVE,
                validity_node=nu2.id,
            )
        ],
    )
    return harness.state.status[a.id].value, harness.state.status[criticism.id].value


def main() -> int:
    baseline_dependence = _scenario(
        criticism_ref_role=RefRole.DEPENDENCE, nu_declares_premise=False
    )
    baseline_evidence = _scenario(
        criticism_ref_role=RefRole.EVIDENCE, nu_declares_premise=False
    )
    predicted = _scenario(
        criticism_ref_role=RefRole.DEPENDENCE, nu_declares_premise=True
    )

    print("A  §0 DEPENDENCE, nu declares nothing  ", baseline_dependence)
    print("B  §0 EVIDENCE,   nu declares nothing  ", baseline_evidence)
    print("C  DEPENDENCE, nu declares k EVIDENCE  ", predicted)

    assert baseline_dependence == ("refuted", "suspended_unsupported"), (
        "arm A no longer reproduces the defect: " + repr(baseline_dependence)
    )
    assert baseline_evidence == ("accepted", "refuted"), (
        "arm B no longer shows the correct branch: " + repr(baseline_evidence)
    )
    if predicted != ("accepted", "refuted"):
        print(
            "\nDIAGNOSIS REFUTED: declaring the premise on nu did NOT reinstate "
            "the target; the cause is inside adjudication/, which GOAL.md puts "
            "out of scope. STOP and report."
        )
        return 1
    print(
        "\nDIAGNOSIS CONFIRMED: one EVIDENCE ref on the validity node is the "
        "whole difference. The mint site is the fix site; adjudication/ is not."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
