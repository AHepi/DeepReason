"""att/dep construction from interfaces (spec §1, §2).

- Each carried warrant => attack edge (carrier -> warrant.target).
- Each ``dependence`` ref => support edge (this -> target); dep must stay a
  DAG — reject any dependence ref that would create a cycle.
- Validity-node closure: any attacker of a warrant's validity_node attacks
  the warrant (hence its carrier's attack edge).
- Closure extension (case law, §1/§10.3): the nu of a rubric-derived warrant
  mentions the standard it applied; every registered attacker of that
  standard attacks the nu. Refute a standard => every nu citing it is
  attacked => every warrant under it falls => targets reinstate, all in
  pass 1.
"""


def build_att(state) -> list[tuple[str, str]]:
    """Attack edges incl. both closure rules. TODO(P0)."""
    raise NotImplementedError


def build_dep(state) -> list[tuple[str, str]]:
    """Support edges; cycle rejection. TODO(P0)."""
    raise NotImplementedError
