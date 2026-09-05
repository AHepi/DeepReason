"""CHECK 11 — the labelling rule itself.

Spec §11.3 (policy DA-1) against DeepReason's adjudication/ (grounded label0
in pass 1, then the support cascade in pass 2).  Four fixtures, each built
twice: once as DA-1 applications for the specification's own reference
checker, once as harness artifacts through the public API.  Nothing is
judged here; the two label vectors are tabled side by side.

Run:  python check11_da1_vs_harness.py
"""
import pathlib, sys, tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]
                       / "docs/proposals/ois-1.1/verification"))
from reference_kernel import Application, Check, appraise          # noqa: E402

from deepreason.harness import Harness                              # noqa: E402
from deepreason.ontology import Interface, Provenance, Ref, Warrant, WarrantType  # noqa: E402
from deepreason.ontology.artifact import RefRole                    # noqa: E402


def harness_labels(build):
    h = Harness(pathlib.Path(tempfile.mkdtemp()) / "run")
    ids = build(h)
    return {name: h.state.status[aid].value for name, aid in ids.items()}


def art(h, text, *, deps=(), attacks=None):
    """One artifact.  `deps` become DEPENDENCE refs (the harness's essential-
    premise channel); `attacks` mounts an ARGUMENTATIVE warrant on a fresh nu."""
    interface = Interface(refs=[Ref(target=d, role=RefRole.DEPENDENCE) for d in deps])
    warrants = []
    if attacks is not None:
        nu = h.create_artifact(f"nu of {text}", provenance=Provenance(role="critic"))
        warrants = [Warrant(id=f"w:{text}", target=attacks,
                            type=WarrantType.ARGUMENTATIVE, validity_node=nu.id)]
    return h.create_artifact(text, interface=interface,
                             provenance=Provenance(role="critic"),
                             warrants=warrants)


# ---------------------------------------------------------------- fixtures --
FIXTURES = []


# F1  A criticism's essential premise is withdrawn by a counter-criticism.
#     Spec §11.3: "a dependent cannot remain in when one of those applications
#     is withdrawn as out in a recomputed appraisal."
def f1_spec():
    return appraise([
        Application("D"),
        Application("K", targets=frozenset()),           # attacked by D
        Application("C", essential=frozenset({"K"}), targets=frozenset({"A"})),
        Application("A"),
    ] and [
        Application("D", targets=frozenset({"K"})),
        Application("K"),
        Application("C", essential=frozenset({"K"}), targets=frozenset({"A"})),
        Application("A"),
    ])


def f1_harness(h):
    A = art(h, "A: the target account")
    K = art(h, "K: the standard the criticism rests on")
    C = art(h, "C: criticism of A, essentially using K", deps=[K.id], attacks=A.id)
    D = art(h, "D: counter-criticism of K", attacks=K.id)
    return {"A": A.id, "K": K.id, "C": C.id, "D": D.id}


FIXTURES.append(("F1 refuted essential premise", f1_spec, f1_harness,
                 "§11.3 — an out essential premise makes that dependent out"))


# F2  The essential premise is UNDECIDED (mutual attack), not out.
def f2_spec():
    return appraise([
        Application("K", targets=frozenset({"M"})),
        Application("M", targets=frozenset({"K"})),
        Application("C", essential=frozenset({"K"}), targets=frozenset({"A"})),
        Application("A"),
    ])


def f2_harness(h):
    """Mutual attack.  The harness mounts warrants only at creation time, so
    K's warrant against M is minted while M is still absent: `edges.py` states
    that refs and warrant targets may dangle and take effect when the target
    appears.  M's id is content-addressed, so it can be computed in advance."""
    from deepreason.ontology.artifact import Artifact
    M_TEXT = "M: rival standard"
    m_id = Artifact.compute_id(f"inline:{M_TEXT}", "utf8", Interface())
    A = art(h, "A: the target account")
    nuK = h.create_artifact("nu K->M", provenance=Provenance(role="critic"))
    K = h.create_artifact(
        "K: the standard", provenance=Provenance(role="critic"),
        warrants=[Warrant(id="w:K->M", target=m_id,
                          type=WarrantType.ARGUMENTATIVE, validity_node=nuK.id)])
    nuM = h.create_artifact("nu M->K", provenance=Provenance(role="critic"))
    M = h.create_artifact(
        M_TEXT, provenance=Provenance(role="critic"),
        warrants=[Warrant(id="w:M->K", target=K.id,
                          type=WarrantType.ARGUMENTATIVE, validity_node=nuM.id)])
    assert M.id == m_id, "content-addressed id prediction failed"
    C = art(h, "C: criticism of A, essentially using K", deps=[K.id], attacks=A.id)
    return {"A": A.id, "K": K.id, "M": M.id, "C": C.id}


FIXTURES.append(("F2 undecided essential premise", f2_spec, f2_harness,
                 "§11.3 — an undecided essential premise prevents its "
                 "dependent from becoming in"))


# F3  Plain reinstatement: a counter-criticism defeats the criticism.
def f3_spec():
    return appraise([
        Application("D", targets=frozenset({"C"})),
        Application("C", targets=frozenset({"A"})),
        Application("A"),
    ])


def f3_harness(h):
    A = art(h, "A: the target account")
    C = art(h, "C: criticism of A", attacks=A.id)
    D = art(h, "D: counter-criticism of C", attacks=C.id)
    return {"A": A.id, "C": C.id, "D": D.id}


FIXTURES.append(("F3 reinstatement", f3_spec, f3_harness,
                 "§11.3 — grounded reinstatement, the shared case"))


# F4  An UNKNOWN local check, unattacked.
def f4_spec():
    return appraise([
        Application("U", readiness=Check.UNKNOWN),
        Application("A", essential=frozenset({"U"})),
    ])


def f4_harness(h):
    U = art(h, "U: a use whose declared check is unavailable")
    A = art(h, "A: an account essentially using U", deps=[U.id])
    return {"U": U.id, "A": A.id}


FIXTURES.append(("F4 unknown readiness, unattacked", f4_spec, f4_harness,
                 "§11.3 — an UNKNOWN check does not become PASS because its "
                 "application is unattacked"))


# --------------------------------------------------------------------- run --
# The brief's instruction is to NAME the difference, not to judge it, so the
# classifier is stated before any fixture runs:
#   IN      usable / survives   -- DA-1 `in`,        DeepReason `accepted`
#   OUT     rejected            -- DA-1 `out`,       DeepReason `refuted`
#   NEITHER neither of those    -- DA-1 `undecided`, DeepReason `suspended`
#                                                 and `suspended_unsupported`
# same               : the exactly corresponding label
# differs in name    : the same class, a different label for it
# DIFFERS IN OUTCOME : a different class -- the two policies disagree about
#                      whether the thing survives, is rejected, or is open
CLASS = {"in": "IN", "out": "OUT", "undecided": "NEITHER",
         "accepted": "IN", "refuted": "OUT",
         "suspended": "NEITHER", "suspended_unsupported": "NEITHER"}
EXACT = {"in": "accepted", "out": "refuted"}


def verdict(spec_label, dr_label):
    cs, cd = CLASS[spec_label], CLASS[dr_label]
    if cs != cd:
        return "DIFFERS IN OUTCOME"
    if EXACT.get(spec_label) == dr_label or (cs == "NEITHER" and dr_label == "suspended"):
        return "same"
    return "differs in name"


print(f"{'fixture':<34} {'node':<5} {'DA-1 (§11.3)':<13} {'DeepReason':<24} verdict")
print("-" * 104)
for title, spec_fn, harness_fn, clause in FIXTURES:
    spec_labels = spec_fn()
    dr = harness_labels(harness_fn)
    for node in sorted(dr):
        s, d = spec_labels.of(node), dr[node]
        print(f"{title:<34} {node:<5} {s:<13} {d:<24} {verdict(s, d)}")
    print()
print("clauses under test:")
for title, _, _, clause in FIXTURES:
    print(f"  {title:<34} {clause}")
