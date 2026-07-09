"""Experiment design (§3/§6 extension): the system designs its own experiments.

The fuzz pass (oracle.fuzz_property) turned the harness into an experimenter,
but its generators were spec-authored — a human still designed every probe of
the input space. This rule closes that loop: an LLM (the EXPERIMENTER role,
served by the conjecturer's endpoint) proposes `def gen(k)` sources for a
property oracle, and the harness adjudicates them BY THEIR FRUITS with an
ordinary program commitment (generator_wf: compile under the guard, yield
gate-valid inputs, reach at least one novel input). Accepted generators are
then enumerated by crit_fuzz alongside the spec's own.

Soundness is generator-independent by construction (§0): whoever wrote gen,
the FROZEN admission gate screens every input and the FROZEN checker decides
every violation — a generator can never manufacture a false refutation. It
only chooses where the harness looks. That is why no judge, no trial, and no
execution-supremacy interaction is needed here: a bad generator is refuted
mechanically for yield/novelty, a good one earns kills that are checked by
the same oracle as everything else. Generators are ordinary artifacts: D8
(nothing deleted) and N1 (no status final) apply, and a refuted generator can
be reinstated by criticizing its critic like anything else.
"""

from deepreason.llm.contracts import ExperimenterOutput
from deepreason.llm.packs import render_experiment_pack
from deepreason.ontology import Interface, Provenance, Ref, Rule, Status
from deepreason.ontology.artifact import RefRole
from deepreason.rules.crit import crit_program

GEN_CODEC = "code:python-gen"


def accepted_generators(harness, base_commitment_id: str) -> list[tuple[str, str]]:
    """ACCEPTED experimenter generators targeting the given property oracle,
    as (artifact_id, source) in state insertion order (deterministic)."""
    from deepreason.programs import content_text

    out: list[tuple[str, str]] = []
    for aid, artifact in harness.state.artifacts.items():
        if artifact.codec != GEN_CODEC:
            continue
        if harness.state.status.get(aid) != Status.ACCEPTED:
            continue
        if not any(
            r.role == RefRole.MENTION and r.target == base_commitment_id
            for r in artifact.interface.refs
        ):
            continue
        out.append((aid, content_text(artifact, harness.blobs)))
    return out


def propose_generators(harness, base, adapter, config) -> list:
    """One experimenter call for a property oracle: register each returned
    generator as an artifact carrying the derived generator_wf commitment and
    a MENTION ref to the base oracle, then adjudicate immediately via
    crit_program — a generator that doesn't compile, doesn't yield, or
    designs no new experiment is refuted on arrival, mechanically. Returns
    the artifacts that survived admission."""
    from deepreason.oracle import generator_wf_commitment

    wf = generator_wf_commitment(base)
    if wf is None:
        return []
    harness.register_commitment(wf)
    existing = [src for _, src in accepted_generators(harness, base.id)]
    pack = render_experiment_pack(
        base, existing, token_budget=config.PACK_TOKEN_BUDGET
    )
    output, llm_call = adapter.call(
        "conjecturer", pack, ExperimenterOutput, template_role="experimenter"
    )
    survivors: list = []
    llm_pending = llm_call
    for source in output.generators:
        if not source.strip():
            continue
        before = set(harness.state.artifacts)
        artifact = harness.create_artifact(
            source,
            codec=GEN_CODEC,
            interface=Interface(
                commitments=[wf.id],
                refs=[Ref(target=base.id, role=RefRole.MENTION)],
            ),
            provenance=Provenance(role="experimenter"),
            rule=Rule.CONJ,
            llm=llm_pending,
        )
        if artifact.id not in before:
            llm_pending = None  # a real event carried the shared call
        crit_program(harness, artifact.id)  # generator_wf adjudicates now
        if harness.state.status.get(artifact.id) == Status.ACCEPTED:
            survivors.append(artifact)
    if llm_pending is not None:
        # Nothing committed the call (empty/duplicate outputs): log it once.
        harness.record_measure(inputs=["experiment-design", base.id], llm=llm_pending)
    return survivors
