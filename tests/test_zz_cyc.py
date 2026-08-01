from deepreason.harness import Harness
from tests.test_v6_engaged_repair_verification import _engaged_root
def test_c(tmp_path):
    h=Harness(_engaged_root(tmp_path/"c"), read_only=True)
    print("\ncycles:", sum(1 for e in h.log.read() if e.inputs and str(e.inputs[0])=="cycle"),
          "artifacts:", len(h.state.artifacts), "att:", len(h.state.att))
