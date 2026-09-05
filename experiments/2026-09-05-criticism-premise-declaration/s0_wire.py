"""The §0 DEPENDENCE branch, rewritten as the critic DECLARING the premise.

`docs/proposals/OIS_1_1_to_DeepReason_configuration.md` §0 builds its graph by
hand. This script builds the same situation the way a run does: a critic seat
answers, its answer crosses the wire contract, the criticism rule dispatches
the defended trial, the trial mints the warrant, and only then is the premise
refuted. Nothing here touches `adjudication/`.

Two arms, both through the wire, differing ONLY in whether the critic filled
the declaration:

    declared   -> the EVIDENCE tuple ('accepted', 'refuted')
    undeclared -> the §0 tuple      ('refuted', 'accepted')

The second arm is the formalism-optional law made visible: a criticism that
declares nothing is exactly what it was before this road existed. (Its second
element is `accepted` rather than §0's `suspended_unsupported` because the
criticism here carries no dependence ref of its own to be orphaned by — the
declaration, not a support edge, is what this tranche added.)

Run offline; no run root, no provider, no key.
"""

import json
import pathlib
import tempfile

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_endpoints
from deepreason.ontology import Provenance, Warrant, WarrantType
from deepreason.rules.crit import crit_argumentative

_CASE = "the tilt account cannot explain the observed nocturnal gap"
_RULING = json.dumps({"verdict": "fail", "decisive_point": "the observed nocturnal gap"})


def _adapter(harness, critic_payload):
    endpoints = {
        "argumentative_critic": MockEndpoint(
            [json.dumps(critic_payload)], name="mock://critic", model="qwen-test"
        ),
        "defender": MockEndpoint(
            [json.dumps({"answer": "the tilt account does explain it"})],
            name="mock://defender",
            model="qwen-test",
        ),
        "judge": [
            MockEndpoint([_RULING], name="mock://judge-a", model="qwen-test"),
            MockEndpoint([_RULING], name="mock://judge-b", model="llama-test"),
        ],
    }
    return LLMAdapter(
        endpoints, harness.blobs, retry_max=2, leases=leases_from_endpoints(endpoints)
    )


def run(*, declare: bool):
    harness = Harness(pathlib.Path(tempfile.mkdtemp()) / "run")
    target = harness.create_artifact(
        "tilt account", provenance=Provenance(role="conjecturer")
    )
    premise = harness.create_artifact("standard k", provenance=Provenance(role="seed"))

    payload = {"attack": True, "case": _CASE}
    if declare:
        payload["premises_essential"] = [premise.id]

    criticism = crit_argumentative(
        harness,
        target.id,
        _adapter(harness, payload),
        Config(
            ARGUMENTATIVE_AUTHORITY="trial_required",
            ADJUDICATION_STATUS_AUTHORITY_ENABLED=True,
        ),
    )
    assert criticism is not None, "the trial minted nothing; the arms are not comparable"

    # Refute the premise, exactly as §0 does: a second criticism with its own
    # validity node.
    nu2 = harness.create_artifact("nu2", provenance=Provenance(role="critic"))
    harness.create_artifact(
        "criticism of k",
        provenance=Provenance(role="critic"),
        warrants=[
            Warrant(
                id="w2",
                target=premise.id,
                type=WarrantType.ARGUMENTATIVE,
                validity_node=nu2.id,
            )
        ],
    )
    return harness.state.status[target.id].value, harness.state.status[criticism.id].value


def main() -> int:
    declared = run(declare=True)
    undeclared = run(declare=False)
    print("critic DECLARED the premise essential   ", declared)
    print("critic declared nothing (today's path)  ", undeclared)

    if declared != ("accepted", "refuted"):
        print("\nFAIL: the declaration did not reach the EVIDENCE branch.")
        return 1
    if undeclared[0] != "refuted":
        print("\nFAIL: a criticism that declared nothing changed behaviour.")
        return 1
    print(
        "\nPASS: a criticism whose declared ground is refuted no longer defeats "
        "its target, and one that declares nothing is untouched."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
