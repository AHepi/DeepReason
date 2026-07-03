"""Warrant schema (spec §1, Def 3.4).

Both warrant types are contentful (packaged in artifacts); a bare verdict is
never an edge. Closure rule: any attacker of ``validity_node`` attacks the
warrant. Closure extension (case law): the nu of any rubric-derived warrant
must carry a mention ref to the standard it applied, and attackers of that
standard attack the nu (see adjudication/edges.py).
"""

from enum import Enum

from pydantic import BaseModel


class WarrantType(str, Enum):
    DEMONSTRATIVE = "demonstrative"
    ARGUMENTATIVE = "argumentative"


class Warrant(BaseModel):
    id: str
    target: str  # artifact id under attack
    type: WarrantType
    # Demonstrative-only fields:
    commitment: str | None = None  # the kappa that failed on target
    verdict: str | None = None  # "fail"
    trace_ref: str | None = None  # blob: full trace (for rubric warrants: trial transcript, §2)
    # nu(kappa): asserts the test is sound & relevant; attackable (N1).
    validity_node: str
