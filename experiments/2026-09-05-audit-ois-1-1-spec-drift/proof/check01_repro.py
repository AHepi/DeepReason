import tempfile, pathlib
from deepreason.harness import Harness
from deepreason.ontology import Provenance, Warrant, WarrantType, Interface, Ref
from deepreason.ontology.artifact import RefRole

def run(role):
    h = Harness(pathlib.Path(tempfile.mkdtemp())/'run')
    a  = h.create_artifact('tilt account', provenance=Provenance(role='seed'))
    k  = h.create_artifact('standard k',   provenance=Provenance(role='seed'))
    nu = h.create_artifact('nu of criticism', provenance=Provenance(role='critic'),
                           interface=Interface(refs=[Ref(target=k.id, role=role)]))
    c  = h.create_artifact('criticism of tilt using k', provenance=Provenance(role='critic'),
                           interface=Interface(refs=[Ref(target=k.id, role=role)]),
                           warrants=[Warrant(id='w1', target=a.id, type=WarrantType.ARGUMENTATIVE, validity_node=nu.id)])
    nu2 = h.create_artifact('nu2', provenance=Provenance(role='critic'))
    h.create_artifact('criticism of k', provenance=Provenance(role='critic'),
                      warrants=[Warrant(id='w2', target=k.id, type=WarrantType.ARGUMENTATIVE, validity_node=nu2.id)])
    return h.state.status[a.id].value, h.state.status[c.id].value

print('DEPENDENCE', run(RefRole.DEPENDENCE))
print('EVIDENCE  ', run(RefRole.EVIDENCE))
