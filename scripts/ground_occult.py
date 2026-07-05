#!/usr/bin/env python
"""Ground the occult domain (stress campaign T4 follow-up): exercise the
full §12 research pipeline live, end-to-end, against the surviving
sunspot-hormone claim in runs/T4_occult.

Pipeline (all sanctioned machinery, no shortcuts):
  1. register an observation-valued commitment + carrier artifact stating
     the claim's own forbidden case as an observable;
  2. scan_spawns spawns the research problem;
  3. a StaticBackend carrying the real literature covers it via
     run_research (import evidence + attackable source-reliability node);
  4. the evidence's verdict lands as a demonstrative warrant against the
     sunspot claim — its self-stated forbidden case OBTAINED in the
     published record. Real-world data enters as a warrant, never a score.

Free: no API calls.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from deepreason.harness import Harness  # noqa: E402
from deepreason.ontology import Commitment, Provenance, Status  # noqa: E402
from deepreason.rules.warrants import register_fail_warrant  # noqa: E402
from deepreason.research.backends import StaticBackend, covered, run_research  # noqa: E402
from deepreason.rules.spawn import scan_spawns  # noqa: E402
from deepreason.config import load as load_config  # noqa: E402

SUNSPOT = "225bf27026ca"  # surviving claim: prenatal hormones tied to sunspot cycles

EVIDENCE = """\
Published evidence on birth-time-linked personality effects:

1. Dean, G. & Kelly, I.W. (2003), 'Is Astrology Relevant to Consciousness
   and Psi?', Journal of Consciousness Studies 10(6-7): the 'time twins'
   test tracked 2,101 people born in London 3-9 May 1958 (minutes apart,
   same place — identical zodiac AND identical solar-cycle phase) across
   100+ measured personality/life variables. Result, quoting the authors:
   'The test conditions could hardly have been more conducive to success
   ... but the results are uniformly negative.'
   Bearing on the claim under test: if prenatal solar/geomagnetic exposure
   shaped personality, time twins (maximal shared exposure) would cluster.
   They do not.

2. The claim's own forbidden case — 'zodiac sign effects are stable across
   different solar cycle phases' — is the observed reality in the null
   record: no sign effect exists to vary with solar phase in any large
   controlled sample (seasonal confounds adjusted).

Known caveats, stated for the reliability node: Dean's full time-twins
dataset remained unpublished as of the commentary literature, and critics
dispute the resemblance criteria (see Currey's commentary in Astrological
Review Letters). The reliability node below is the attack surface for
those objections.
"""


def main() -> int:
    harness = Harness(Path("runs/T4_occult"))
    if harness.state.status.get(_full(harness, SUNSPOT)) != Status.ACCEPTED:
        print("sunspot claim is not accepted — nothing to ground")
        return 0

    # 1. Observation-valued commitment + carrier stating the forbidden case
    #    as an observable.
    kappa_id = "k-timetwins-clustering"
    if kappa_id not in harness.commitments:
        harness.register_commitment(
            Commitment(id=kappa_id, eval="predicate:True", observation_valued=True)
        )
    from deepreason.ontology import Interface

    carrier = harness.create_artifact(
        "proposed observation: if prenatal solar/geomagnetic exposure shapes "
        "personality, people born at the same time and place (time twins) "
        "must show personality clustering; and sign effects must vary with "
        "solar cycle phase",
        interface=Interface(commitments=[kappa_id]),
        provenance=Provenance(role="conjecturer"),
    )

    # 2. Spawn the research problem for the uncovered observation.
    config = load_config()
    scan_spawns(harness, config)
    rid = f"research:{kappa_id}:{carrier.id[:12]}"
    assert rid in harness.state.problems, "research problem did not spawn"
    print(f"research problem spawned: {rid}")

    # 3. Cover it from the literature backend.
    problem = harness.state.problems[rid]
    backend = StaticBackend({problem.description: (EVIDENCE, "Dean & Kelly 2003, J. Consciousness Studies")})
    evidence = run_research(harness, problem, backend)
    assert evidence is not None and covered(harness, rid), "research did not cover"
    print(f"evidence registered: {evidence.id[:12]} (covered={covered(harness, rid)})")

    # 4. The forbidden case obtained: demonstrative warrant against the claim.
    target = _full(harness, SUNSPOT)
    register_fail_warrant(
        harness,
        commitment_id=kappa_id,
        target_id=target,
        nu_content=(
            f"nu: the time-twins verdict of {kappa_id} on {target[:12]} is sound — "
            "to attack it, attack the evidence's reliability node "
            "(unpublished full dataset; disputed resemblance criteria)"
        ),
        critic_content=(
            "critic: the claim's self-stated forbidden case obtained in the "
            "published record — time twins with maximal shared prenatal "
            f"solar/geomagnetic exposure show no personality clustering "
            f"(evidence {evidence.id[:12]})"
        ),
        trace_ref=harness.blobs.put(EVIDENCE.encode()),
    )
    print(f"sunspot claim status: {harness.state.status.get(target).value}")
    return 0


def _full(harness, prefix: str) -> str:
    matches = [a for a in harness.state.artifacts if a.startswith(prefix)]
    return matches[0] if len(matches) == 1 else prefix


if __name__ == "__main__":
    sys.exit(main())
