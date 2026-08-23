"""Proof debt -- the bill of materials a derived judgment travels with (Rung D).

The harness already kept this discipline for ONE class of judgment: a warrant
carries a validity node, so a criticism can itself be criticised. What it did
not do was say WHAT the criticism rests on in a form anyone could attack. The
demarcation rent verdict is the standing example -- its second reading is a
SAMPLE, recorded in a trace blob that is readable and inert. "Your sample was
unrepresentative" had nowhere to land.

Two objects, and keeping them apart is the whole design:

- the **derivation manifest** is a registered ARTIFACT. It has to be, because
  in this harness only registered artifacts can be attacked, and an
  unattackable bill of materials is the blob again. It itemizes three kinds --
  KERNEL_CHECK, OPEN_CERTIFICATES, AXIOM_DEBT -- and the compiler makes each
  open certificate a DEPENDENCE so `edges.py`'s evidence closure reaches it.
- the **receipt** is not stored anywhere. It is the statement of what STILL
  STANDS, rebuilt on every call from replayed state, with every re-runnable
  kernel check RE-RUN rather than read back. Same discipline as
  `calculus.standing` and `premises.premise_orphaned` (C4).

That split is also why "dependents are invalidated ON RECOMPUTATION rather than
retroactively" needs no invalidation machinery. Nothing rewrites a past event:
the next `build_att` sees the new attack and the judgment loses, while the log's
prefix replays to exactly what it always replayed to.

NOTHING HERE MOVES A LABEL. A bill is a statement, not a verdict; only attacks
move labels, and the manifest is attackable like any other artifact.
"""

from __future__ import annotations

from dataclasses import dataclass

from deepreason.calculus.claims import (
    ClaimDecodeError,
    DerivationManifestV1,
    KernelCheckV1,
    decode,
    encode,
)
from deepreason.calculus.compiler import compile_interface
from deepreason.calculus.programs import DERIVATION_MANIFEST_COMMITMENT
from deepreason.ontology import Commitment, Status
from deepreason.programs import content_text

# E-1's format, verbatim. Constants rather than literals because the writer of
# a bill and the reader of a receipt must agree on the words.
KERNEL_CHECK = "KERNEL_CHECK"
OPEN_CERTIFICATES = "OPEN_CERTIFICATES"
AXIOM_DEBT = "AXIOM_DEBT"

# A kernel check whose `program` is empty is not re-runnable here. The receipt
# reports this rather than the recorded verdict, because "we could not check"
# must never look like "we checked and it was fine" -- the same typed
# abstention `premises.premise_rent_sweep` records when it has no variator.
NOT_RERUNNABLE = "not-rerunnable"


@dataclass(frozen=True)
class KernelVerdict:
    """One kernel check as a reader sees it: what was recorded, and what is
    true NOW. Both, never one: a recorded verdict that has stopped being true
    is precisely the failure the receipt exists to expose, and hiding either
    half would hide it."""

    name: str
    program: str
    target_ref: str
    recorded_verdict: str
    verdict: str


@dataclass(frozen=True)
class CertificateItem:
    """One open certificate and its CURRENT label. `standing` is false the
    moment the certificate is refuted or loses its own support -- which is what
    a critic buys by attacking it."""

    ref: str
    status: str
    standing: bool


@dataclass(frozen=True)
class Receipt:
    """DERIVED. Built on every call and stored nowhere, so there is no receipt
    record to fall out of step with the log that implies it."""

    warrant_id: str
    manifest_id: str
    subject_ref: str
    kernel_checks: tuple[KernelVerdict, ...]
    open_certificates: tuple[CertificateItem, ...]
    axiom_debt: tuple[str, ...]
    standing: bool


def _manifest_body(harness, artifact) -> DerivationManifestV1 | None:
    """The recognised manifest body of an artifact, or None.

    Recognition is by INTERFACE STRUCTURE, never by a kind field (C3), and the
    declared interface must be what the controller's compiler WOULD have
    emitted. That last condition carries the ref-role semantics: an artifact
    whose interface the compiler would not have produced is not this claim,
    whatever its content says.
    """
    if DERIVATION_MANIFEST_COMMITMENT.id not in artifact.interface.commitments:
        return None
    try:
        body = decode(content_text(artifact, harness.blobs))
    except (ClaimDecodeError, UnicodeDecodeError, KeyError):
        return None
    if not isinstance(body, DerivationManifestV1):
        return None
    declared = {(r.target, r.role.value) for r in artifact.interface.refs}
    expected = {
        (r.target, r.role.value) for r in compile_interface(body).refs
    }
    return body if declared == expected else None


def file_derivation_manifest(
    harness,
    subject_ref: str,
    *,
    kernel_checks=(),
    open_certificate_refs=(),
    axiom_debt=(),
    provenance=None,
):
    """Register the bill a judgment rests on. Returns the manifest artifact.

    Content-addressed, so filing the same bill twice is idempotent rather than
    a duplicate. The interface comes from the controller's compiler and from
    nowhere else -- a caller that could choose its own ref roles could make an
    open certificate a MENTION and quietly remove the one thing that makes it
    attackable.
    """
    harness.register_commitment(DERIVATION_MANIFEST_COMMITMENT)
    body = DerivationManifestV1(
        subject_ref=subject_ref,
        kernel_checks=list(kernel_checks),
        open_certificate_refs=list(open_certificate_refs),
        axiom_debt=list(axiom_debt),
    )
    return harness.create_artifact(
        encode(body),
        codec="json",
        interface=compile_interface(body),
        provenance=provenance,
    )


def manifests_for(harness, subject_ref: str) -> list:
    """Every manifest filed against this subject, id-sorted for determinism."""
    found = [
        artifact
        for artifact in harness.state.artifacts.values()
        if (body := _manifest_body(harness, artifact)) is not None
        and body.subject_ref == subject_ref
    ]
    return sorted(found, key=lambda artifact: artifact.id)


def _rerun(harness, check: KernelCheckV1) -> str:
    """Re-run one kernel check NOW. Never reads the recorded verdict back.

    A missing program or a missing target is reported as not-rerunnable rather
    than as a pass: a check nobody can re-run has not been checked, and the
    receipt's whole value is that it does not confuse the two.
    """
    if not check.program or not check.target_ref:
        return NOT_RERUNNABLE
    target = harness.state.artifacts.get(check.target_ref)
    if target is None:
        return NOT_RERUNNABLE
    from deepreason import programs

    kappa = Commitment(id=f"kernel:{check.name}", eval=f"program:{check.program}")
    if not programs.evaluable(kappa):
        return NOT_RERUNNABLE
    verdict, _ = programs.evaluate(kappa, target, harness.blobs)
    return verdict


def receipt(harness, warrant_id: str) -> Receipt | None:
    """What this judgment still rests on. DERIVED; nothing here writes.

    None when the warrant carries no bill. That is a typed absence rather than
    an empty receipt, because an empty bill would read as a discharged debt --
    carrying a manifest is a CAPACITY every registration site has and no site
    is obliged to use.
    """
    warrant = harness.warrants.get(warrant_id)
    if warrant is None or not warrant.validity_node:
        return None
    nu = harness.state.artifacts.get(warrant.validity_node)
    if nu is None:
        return None
    for ref in nu.interface.refs:
        if ref.role.value != "evidence":
            continue
        artifact = harness.state.artifacts.get(ref.target)
        if artifact is None:
            continue
        body = _manifest_body(harness, artifact)
        if body is None:
            continue
        checks = tuple(
            KernelVerdict(
                name=check.name,
                program=check.program,
                target_ref=check.target_ref,
                recorded_verdict=check.recorded_verdict,
                verdict=_rerun(harness, check),
            )
            for check in body.kernel_checks
        )
        certificates = tuple(
            CertificateItem(
                ref=certificate,
                status=str(harness.state.status.get(certificate, "")),
                standing=harness.state.status.get(certificate) == Status.ACCEPTED,
            )
            for certificate in body.open_certificate_refs
        )
        return Receipt(
            warrant_id=warrant_id,
            manifest_id=artifact.id,
            subject_ref=body.subject_ref,
            kernel_checks=checks,
            open_certificates=certificates,
            axiom_debt=tuple(body.axiom_debt),
            # The manifest's own label already carries every certificate's
            # fall, because each certificate is a DEPENDENCE: pass two suspends
            # the manifest when one falls. So the bill stands iff the manifest
            # stands and every re-runnable check still passes.
            standing=(
                harness.state.status.get(artifact.id) == Status.ACCEPTED
                and all(
                    check.verdict in ("pass", NOT_RERUNNABLE) for check in checks
                )
            ),
        )
    return None
