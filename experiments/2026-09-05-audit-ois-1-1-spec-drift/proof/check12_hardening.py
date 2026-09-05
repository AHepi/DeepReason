"""CHECK 12 — the Hardening_Audit S-items that name a DeepReason analogue.

S05  admitted material counts although its own declared check failed
S17  merge / import keeps identity and location
S18  a unique temporal maximum is assumed
S22  alternatives vs. compatible rivals

Read-only.  Each item prints the observation and the pre-hardening question
answered yes/no; nothing is fixed.
"""
import pathlib, tempfile
from deepreason.harness import Harness
from deepreason.ontology import Interface, Provenance, Warrant, WarrantType
from deepreason.ontology.commitment import Commitment
from deepreason import programs


def new():
    return Harness(pathlib.Path(tempfile.mkdtemp()) / "run")


print("=" * 78)
print("S05 — does an artifact whose OWN declared check FAILS still label accepted?")
print("=" * 78)
h = new()
k = Commitment(id="k-fail", eval="predicate:'impossible-token' in content")
h.register_commitment(k)
a = h.create_artifact("an ordinary account that does not contain the token",
                      interface=Interface(commitments=["k-fail"]),
                      provenance=Provenance(role="conjecturer"))
verdict, trace = programs.evaluate(k, a, h.blobs)
print(f"  declared check              : {k.eval}")
print(f"  its verdict on this artifact: {verdict}")
print(f"  registered attacks on it    : {[x for x, t in h.state.att if t == a.id]}")
print(f"  adjudicated status          : {h.state.status[a.id].value}")
print(f"  S05 pre-hardening behaviour EXHIBITED: "
      f"{verdict == programs.FAIL and h.state.status[a.id].value == 'accepted'}")
print("  (the label reads the attack graph; nothing consults the declared check")
print("   until a criticism rule runs and mints a warrant)")

print()
print("=" * 78)
print("S17 — does import keep the artifact's identity, and its location?")
print("=" * 78)
h1, h2 = new(), new()
TEXT = "a contribution made in the source run"
src = h1.create_artifact(TEXT, provenance=Provenance(role="conjecturer"))
h2.create_artifact("something else first", provenance=Provenance(role="seed"))
h2.create_artifact("and something else again", provenance=Provenance(role="seed"))
imp = h2.create_artifact(TEXT, provenance=Provenance(role="import"))


def seq_of(h, aid):
    return next(e.seq for e in h.log.read() if aid in (e.outputs or []))


s_src, s_imp = seq_of(h1, src.id), seq_of(h2, imp.id)
print(f"  source   id {src.id[:24]}  log seq {s_src}  role {src.provenance.role.value}")
print(f"  imported id {imp.id[:24]}  log seq {s_imp}  role {imp.provenance.role.value}")
print(f"  identity kept      : {src.id == imp.id}   (ids are content-addressed)")
print(f"  original log location kept : {s_src == s_imp}")
print(f"  original role kept : {src.provenance.role == imp.provenance.role}")
print(f"  S17 pre-hardening behaviour EXHIBITED (the imported contribution is "
      f"relocated to the merge rather than keeping its own place): {s_src != s_imp}")
print("  Identity survives because an id is a hash of content, codec and interface.")
print("  Location does not: the import is a NEW event in the importing run's own")
print("  sequence, and the originating role is overwritten with `import`.")

print()
print("=" * 78)
print("S18 — is a unique maximum assumed where several could be maximal?")
print("=" * 78)
h = new()
a = h.create_artifact("the target", provenance=Provenance(role="conjecturer"))
labels = h.state.status
print(f"  status container type      : {type(labels).__name__} of "
      f"artifact-id -> one Status")
print(f"  values per artifact         : 1 (by construction)")
print(f"  any 'Appraise' record kind  : "
      f"{'Appraise' in getattr(h, 'SCHEMAS', {}) or False}")
print("  S18 pre-hardening behaviour EXHIBITED: no — but only because there are")
print("  no situated appraisals at all to be concurrent.  The single label is")
print("  COMPUTED by one policy, never SELECTED from competing records by log")
print("  order, which is the specific defect S18 names.")

print()
print("=" * 78)
print("S22 — can two rival contents be recorded compatibly in one cut?")
print("=" * 78)
h = new()
p = h.create_artifact("the problem", provenance=Provenance(role="seed"))
r1 = h.create_artifact("rival one: the account is X", provenance=Provenance(role="conjecturer"), problem_id=p.id)
r2 = h.create_artifact("rival two: the account is not-X", provenance=Provenance(role="conjecturer"), problem_id=p.id)
print(f"  rival one status : {h.state.status[r1.id].value}")
print(f"  rival two status : {h.state.status[r2.id].value}")
print(f"  attack edges     : {sorted(h.state.att)}")
print(f"  S22 pre-hardening behaviour EXHIBITED (a rival pair cannot share a "
      f"cut): {bool(h.state.att)}")
print("  There is no branch, cut or exclusivity relation over rivals: incompatible")
print("  CONTENT never makes the two RECORDS incompatible, which is the")
print("  hardened reading.")
