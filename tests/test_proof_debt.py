"""Proof debt: what a derived judgment rests on, itemized and attackable.

Implements R4, R5, R10, R12 and R58 (v2 calculus program, Rung D — drift row
E-1). A derivation manifest is an ORDINARY registered artifact carrying the
three-part bill of materials `KERNEL_CHECK / OPEN_CERTIFICATES / AXIOM_DEBT`,
wired to a fail warrant's validity node as EVIDENCE. Nothing here is a new node
type and nothing here has an event rule: the whole mechanism is the ordinary
`att`/`dep` calculus plus one ref role that `adjudication/edges.py` already
knows how to close over.

The RECEIPT is not the manifest. The manifest is on the log because only
registered artifacts can be attacked; the receipt — the itemized statement of
what still stands — is recomputed from replayed state on every call and stored
nowhere (C4). That split is what makes "dependents are invalidated ON
RECOMPUTATION rather than retroactively" true without any invalidation
machinery at all.
"""

import pytest

from deepreason.canonical import canonical_json
from deepreason.calculus.claims import (
    DERIVATION_MANIFEST_V1,
    ClaimDecodeError,
    DerivationManifestV1,
    KernelCheckV1,
    decode,
    encode,
)
from deepreason.calculus.compiler import compile_interface
from deepreason.calculus.programs import (
    DERIVATION_MANIFEST_COMMITMENT,
    derivation_manifest_wf,
)
from deepreason.ontology import Interface, Provenance, Ref, Status
from deepreason.ontology.artifact import RefRole
from deepreason.premises import PREMISE_RENT, file_premise, premise_rent_sweep
from deepreason.proof_debt import (
    AXIOM_DEBT,
    KERNEL_CHECK,
    OPEN_CERTIFICATES,
    file_derivation_manifest,
    manifests_for,
    receipt,
)
from deepreason.programs import content_text
from deepreason.rules.warrants import register_fail_warrant
from tests.conftest import art, attack


_JSON = '{"sampled": ["a siren has a pitch"]}'


def _certificate(harness, text=_JSON):
    """An open certificate: an ordinary artifact the judgment leans on."""
    return art(harness, text, provenance=Provenance(role="critic"))


def _manifest(harness, subject, *, certificates=(), kernel_checks=(), axioms=("A2",)):
    return file_derivation_manifest(
        harness,
        subject,
        kernel_checks=list(kernel_checks),
        open_certificate_refs=[c.id for c in certificates],
        axiom_debt=list(axioms),
        provenance=Provenance(role="critic"),
    )


def _judged(harness, *, with_manifest=True):
    """A target refuted by a demonstrative fail warrant that carries a bill.

    Returns (target, certificate, manifest, critic). This is R58's fixture:
    everything the pinned regression needs, built once.
    """
    kappa_id = "proof-debt:test@v1"
    from deepreason.ontology import Commitment

    harness.register_commitment(Commitment(id=kappa_id, eval="program:json-wf"))
    target = art(harness, "the tide follows the moon")
    certificate = _certificate(harness)
    manifest = _manifest(harness, target.id, certificates=[certificate])
    critic = register_fail_warrant(
        harness,
        commitment_id=kappa_id,
        target_id=target.id,
        nu_content="nu: the verdict on the tide claim is sound and relevant",
        critic_content="critic: the tide claim fails its battery",
        trace_ref=harness.blobs.put(b'{"verdict": "fail"}'),
        manifest_ref=manifest.id if with_manifest else None,
    )
    return target, certificate, manifest, critic


# --- the claim body and its compiled interface (S1, S2) ---------------------


def test_the_closed_claim_name_set_does_not_grow(harness):
    """Rung D supplies producers for names the substrate ALREADY declared.

    An ontology addition riding in on a rung meant only to build one is exactly
    what the closure exists to stop, so the count is the property, not the
    presence.
    """
    from deepreason.calculus import CLAIM_SCHEMAS
    from deepreason.calculus.claims import _IMPLEMENTED

    assert len(CLAIM_SCHEMAS) == 9
    assert DERIVATION_MANIFEST_V1 in CLAIM_SCHEMAS
    assert DERIVATION_MANIFEST_V1 in _IMPLEMENTED


def test_open_certificates_are_dependences_and_the_subject_is_a_mention():
    """The one assignment that makes proof debt work at all.

    A certificate is a DEPENDENCE so `evidence_lineage` reaches it from the
    validity node — that is the attackable half. The subject is a MENTION for
    the mention law's own reason: a manifest that DEPENDED on the judgment's
    subject would be suspended the moment the subject was refuted, which is
    exactly when someone wants to read the bill of materials.
    """
    body = DerivationManifestV1(
        subject_ref="subject-1",
        kernel_checks=[],
        open_certificate_refs=["cert-1", "cert-2"],
        axiom_debt=["A2", "A10"],
    )
    interface = compile_interface(body)

    assert {(r.target, r.role) for r in interface.refs} == {
        ("subject-1", RefRole.MENTION),
        ("cert-1", RefRole.DEPENDENCE),
        ("cert-2", RefRole.DEPENDENCE),
    }
    assert interface.commitments == [DERIVATION_MANIFEST_COMMITMENT.id]


def test_axiom_debt_and_kernel_checks_never_become_refs():
    """Named debt is content, not an edge. An axiom is what you do NOT prove,
    so giving it a ref would promise an attack surface that cannot exist; a
    kernel check is re-derived, so a ref would freeze a verdict the receipt is
    supposed to recompute."""
    body = DerivationManifestV1(
        subject_ref="subject-1",
        kernel_checks=[
            KernelCheckV1(
                name="demarcation.crit",
                program="json-wf",
                target_ref="subject-1",
                recorded_verdict="pass",
            )
        ],
        open_certificate_refs=[],
        axiom_debt=["A2", "Ax 4.1"],
    )
    targets = {r.target for r in compile_interface(body).refs}

    assert targets == {"subject-1"}  # the mention only; no debt edge


def test_a_manifest_whose_interface_was_not_controller_compiled_is_refused(harness):
    """The compiler is the only authority on ref roles. An artifact whose
    interface the compiler would not have produced is not this claim, whatever
    its content says."""
    harness.register_commitment(DERIVATION_MANIFEST_COMMITMENT)
    body = DerivationManifestV1(
        subject_ref="subject-1", open_certificate_refs=["cert-1"], axiom_debt=[]
    )
    forged = art(
        harness,
        encode(body),
        interface=Interface(
            commitments=[DERIVATION_MANIFEST_COMMITMENT.id],
            # DEPENDENCE on the subject: the one role the compiler never emits.
            refs=[
                Ref(target="subject-1", role=RefRole.DEPENDENCE),
                Ref(target="cert-1", role=RefRole.DEPENDENCE),
            ],
        ),
    )
    verdict, trace = derivation_manifest_wf(
        content_text(forged, harness.blobs), None, forged
    )

    assert verdict == "fail"
    assert trace["reason"] == "claim-interface-not-controller-compiled"


# --- the receipt is derived, never stored (S5, R10) -------------------------


def test_a_receipt_is_recomputed_from_the_log_and_never_stored(harness):
    """R10. Two calls agree, and no event on the log carries a receipt.

    The manifest is on the log — it must be, to be attackable. The RECEIPT is
    not: it is a pure function of replayed state, and a stored one could fall
    out of step with the log that implies it.
    """
    target, certificate, manifest, critic = _judged(harness)
    warrant_id = next(iter(harness.warrants))

    first = receipt(harness, warrant_id)
    second = receipt(harness, warrant_id)

    assert first == second
    assert first.manifest_id == manifest.id
    assert first.subject_ref == target.id
    assert [item.ref for item in first.open_certificates] == [certificate.id]
    assert first.axiom_debt == ("A2",)
    assert first.standing is True

    # Nothing on the log is a receipt: the only registered claim is the
    # manifest itself.
    receipts_on_log = [
        aid
        for aid, a in harness.state.artifacts.items()
        if "receipt" in content_text(a, harness.blobs).lower()
    ]
    assert receipts_on_log == []


def test_a_receipt_reruns_its_kernel_checks_rather_than_reading_them_back(harness):
    """A kernel check is RE-RUN, so a recorded verdict cannot outlive its truth.

    The manifest here records `pass` for a `json-wf` check on an artifact whose
    bytes are not JSON. Reading the record back would report `pass`; re-running
    reports `fail`, and the receipt stops standing.
    """
    prose = art(harness, "the tide follows the moon")  # not JSON
    manifest = file_derivation_manifest(
        harness,
        prose.id,
        kernel_checks=[
            KernelCheckV1(
                name="wellformedness",
                program="json-wf",
                target_ref=prose.id,
                recorded_verdict="pass",
            )
        ],
        open_certificate_refs=[],
        axiom_debt=["A2"],
        provenance=Provenance(role="critic"),
    )
    from deepreason.ontology import Commitment

    harness.register_commitment(Commitment(id="pd:k@v1", eval="program:json-wf"))
    register_fail_warrant(
        harness,
        commitment_id="pd:k@v1",
        target_id=prose.id,
        nu_content="nu: sound and relevant",
        critic_content="critic: fails",
        trace_ref=harness.blobs.put(b"{}"),
        manifest_ref=manifest.id,
    )
    warrant_id = next(iter(harness.warrants))

    item = receipt(harness, warrant_id).kernel_checks[0]

    assert item.recorded_verdict == "pass"
    assert item.verdict == "fail"  # re-run now, not read back
    assert receipt(harness, warrant_id).standing is False


def test_a_warrant_with_no_manifest_has_no_receipt(harness):
    """Carrying a bill is a CAPACITY, not an obligation. Every existing
    registration site keeps its unchanged path, and the absence is typed rather
    than an empty receipt that looks like a discharged debt."""
    _judged(harness, with_manifest=False)
    warrant_id = next(iter(harness.warrants))

    assert receipt(harness, warrant_id) is None


def test_manifests_for_finds_every_bill_filed_against_a_subject(harness):
    target, certificate, manifest, _ = _judged(harness)

    assert [a.id for a in manifests_for(harness, target.id)] == [manifest.id]
    assert manifests_for(harness, certificate.id) == []


# --- the validity-node wiring (S8) and R58's pinned regression (S9) ---------


def test_a_manifest_is_wired_to_the_validity_node_as_evidence(harness):
    """R58: a blob is READABLE, an evidence ref is ATTACKABLE.

    The trace blob stays where it was — the manifest is added beside it, not
    instead of it — but the bill of materials now hangs off nu with the one ref
    role `edges.py` closes over.
    """
    _, _, manifest, critic = _judged(harness)
    warrant = next(iter(harness.warrants.values()))
    nu = harness.state.artifacts[warrant.validity_node]

    assert (manifest.id, RefRole.EVIDENCE) in {
        (r.target, r.role) for r in nu.interface.refs
    }
    assert warrant.trace_ref  # the readable blob is untouched


def test_attacking_a_manifest_item_disables_the_attack_before_pass_one(harness):
    """R58's own regression, end to end.

    target refuted -> manifest item attacked -> the critic loses its validity
    PRE-GROUNDED -> target reinstated. Nothing here is a view-level check: the
    evidence closure adds the attack on nu, the validity-node closure lifts it
    onto the critic, and the grounded pass does the rest.
    """
    target, certificate, _, critic = _judged(harness)

    assert harness.state.status[target.id] == Status.REFUTED

    attack(harness, certificate.id, "the sample was drawn from one housing only")

    assert harness.state.status[certificate.id] == Status.REFUTED
    assert harness.state.status[critic.id] == Status.REFUTED
    assert harness.state.status[target.id] == Status.ACCEPTED


def test_the_log_replays_identically_after_a_certificate_is_attacked(harness):
    """A2/A10 at this layer: the record round-trips through the code that wrote
    it. Replaying the whole log re-derives exactly the labels the live harness
    holds, and the receipt built from the replayed state is the same object."""
    from deepreason.harness import Harness

    target, certificate, _, critic = _judged(harness)
    attack(harness, certificate.id, "the sample was drawn from one housing only")
    warrant_id = next(iter(harness.warrants))
    live_status = dict(harness.state.status)
    live_receipt = receipt(harness, warrant_id)

    replayed = Harness(harness.root, read_only=True)

    assert dict(replayed.state.status) == live_status
    assert receipt(replayed, warrant_id) == live_receipt


def test_dependents_are_invalidated_on_recomputation_not_retroactively(harness):
    """The distinction E-1 insists on, made observable.

    Before the certificate is attacked the receipt STANDS and the target is
    refuted. After, the receipt does not stand and the target is back. The log
    events written before the attack are unchanged — nothing was rewritten, and
    the earlier labels were correct for the record as it then stood.
    """
    target, certificate, _, _ = _judged(harness)
    warrant_id = next(iter(harness.warrants))
    before_events = [
        canonical_json(event.model_dump(mode="json")) for event in harness.log.read()
    ]

    assert receipt(harness, warrant_id).standing is True
    assert harness.state.status[target.id] == Status.REFUTED

    attack(harness, certificate.id, "the sample was drawn from one housing only")

    assert receipt(harness, warrant_id).standing is False
    assert harness.state.status[target.id] == Status.ACCEPTED
    # Append-only: the prefix is byte-identical, so the earlier verdict was not
    # retroactively unmade — it was superseded by a later recomputation.
    after_events = [
        canonical_json(event.model_dump(mode="json")) for event in harness.log.read()
    ]
    assert after_events[: len(before_events)] == before_events
    assert len(after_events) > len(before_events)  # the attack really landed


# --- readout inertness (S20, R12) ------------------------------------------


def test_filing_a_manifest_moves_no_label(harness):
    """R12. A bill of materials is a statement, not a verdict: only attacks
    move labels."""
    subject = art(harness, "the tide follows the moon")
    certificate = _certificate(harness)
    before = dict(harness.state.status)

    manifest = _manifest(harness, subject.id, certificates=[certificate])

    after = {k: v for k, v in harness.state.status.items() if k != manifest.id}
    assert after == before
    assert harness.state.status[manifest.id] == Status.ACCEPTED


def test_the_read_path_holds_no_call_that_could_write(harness):
    """Structural, not behavioural, and deliberately so: a behavioural test
    proves a label did not move on the one input it tried, while this proves
    the module holds no call that COULD move one. Same guard
    `calculus/standing.py` carries."""
    import ast
    import pathlib

    tree = ast.parse(pathlib.Path("src/deepreason/proof_debt.py").read_text())
    read_paths = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name in {"receipt", "manifests_for"}
    ]
    assert len(read_paths) == 2
    for node in read_paths:
        calls = [ast.unparse(c.func) for c in ast.walk(node) if isinstance(c, ast.Call)]
        assert not [c for c in calls if "create_artifact" in c or "record_measure" in c]
    modules = [
        (node.module or "")
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    ]
    assert not [m for m in modules if "adjudication" in m], modules


# --- the first live producer (S10) -----------------------------------------


class _Variator:
    """The same deterministic stand-in `test_premise_channel.py` uses, so the
    sweep's behaviour is compared against a fixture the gate already trusts."""

    def __init__(self, variants=("a siren has a pitch",), *, differs=False):
        self.variants = list(variants)
        self.differs = differs
        self.sampled: list[str] = []

    def sample(self, artifact):
        self.sampled = list(self.variants)
        return content_text(artifact, self._blobs), list(self.variants)

    def role_variant_differs(self, text, variant):
        return self.differs

    def bind(self, harness):
        self._blobs = harness.blobs
        return self


def _problem(harness, description):
    from deepreason.ontology import Problem, ProblemProvenance

    return harness.register_problem(
        Problem(
            id=description.replace(" ", "-"),
            description=description,
            criteria=[],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    ).id


def test_the_rent_sweep_files_a_manifest_whose_sample_is_attackable(harness):
    """S10 — the shipped producer, and the reason this rung has one.

    The rent verdict's second reading rests on a SAMPLE. Before Rung D that
    sample lived only in an unattackable trace blob, so "your sample was
    unrepresentative" had no artifact to land on. Now the sample is an open
    certificate, and attacking it reinstates the premise by the same computed
    predicate that felled it (N1).
    """
    problem = _problem(harness, "what is the colour of a siren")
    premise, _ = file_premise(harness, problem, "a siren is the kind of thing "
                                                "that has a colour")
    critic = premise_rent_sweep(harness, _Variator().bind(harness))[0]
    warrant_id = next(
        wid for wid, w in harness.warrants.items() if w.commitment == PREMISE_RENT.id
    )

    bill = receipt(harness, warrant_id)

    assert bill is not None
    assert bill.subject_ref == premise.id
    assert [item.name for item in bill.kernel_checks] == ["demarcation.crit"]
    assert set(bill.axiom_debt) == {"A2", "A10"}
    assert len(bill.open_certificates) == 1
    sample_id = bill.open_certificates[0].ref
    assert "a siren has a pitch" in content_text(
        harness.state.artifacts[sample_id], harness.blobs
    )

    assert harness.state.status[premise.id] == Status.REFUTED

    attack(harness, sample_id, "one housing is not a sample of sirens")

    assert harness.state.status[critic.id] == Status.REFUTED
    assert harness.state.status[premise.id] == Status.ACCEPTED
    assert receipt(harness, warrant_id).standing is False


def test_the_rent_sweep_keeps_its_trace_blob(harness):
    """The certificate is added BESIDE the readable blob, never instead of it:
    a reader who wants the verbatim payload still finds it where it was."""
    from deepreason.canonical import canonical_json  # noqa: F401 - shape check

    problem = _problem(harness, "what is the colour of a siren")
    file_premise(harness, problem, "a siren is the kind of thing that has a colour")
    premise_rent_sweep(harness, _Variator().bind(harness))
    warrant = next(
        w for w in harness.warrants.values() if w.commitment == PREMISE_RENT.id
    )

    payload = harness.blobs.get(warrant.trace_ref)
    assert b"sampled_variants" in payload


def test_an_undecided_rent_verdict_files_no_manifest(harness):
    """No verdict, no bill. The abstention path registers nothing: a manifest
    for a judgment nobody made would be debt against a judgment that does not
    exist."""
    problem = _problem(harness, "what is the colour of a siren")
    premise, _ = file_premise(harness, problem, "a siren is the kind of thing "
                                                "that has a colour")

    assert premise_rent_sweep(harness) == []  # no variator: typed abstention
    assert manifests_for(harness, premise.id) == []


# --- the itemization constants are the receipt's vocabulary ----------------


def test_the_three_item_kinds_are_named_once(harness):
    """E-1's format, verbatim. They are constants rather than literals because
    a reader of a receipt and a writer of one must agree on the words."""
    assert (KERNEL_CHECK, OPEN_CERTIFICATES, AXIOM_DEBT) == (
        "KERNEL_CHECK",
        "OPEN_CERTIFICATES",
        "AXIOM_DEBT",
    )
    bill = DerivationManifestV1(subject_ref="s", axiom_debt=["A2"])
    assert decode(encode(bill)) == bill
