"""§9.4's five pinned promotion criteria, as PROGRAMS over a frozen input.

Every criterion here is a pure function of two things: the CANDIDATE's own
bytes and interface, and ONE frozen, fence-stamped reach certificate fetched
from the blob store by digest. Neither reads live graph state, which is Rider 5
clause (4) and is what makes a promotion verdict reproducible: a candidate
evaluated twice on one record gets one answer, whatever the run did in between.

The programs are registered in `programs.PROGRAMS` with `class_="structural"`
AND in `programs.BLOB_PROGRAMS`. The dual registration is mechanical, not
decorative: `programs_by_class()` -- and therefore
`measures/reach._STRUCTURAL_PROGRAMS` -- reads `PROGRAMS` alone, so a criterion
living only in `BLOB_PROGRAMS` would count as SUBSTANTIVE by default and would
both ground reach and confer prose immunity. Both are wrong here. Grounding
reach would let promotion paperwork manufacture the signal that nominates;
conferring immunity would sell protection for a verdict that passes VACUOUSLY
whenever there is no incumbent to succeed. The class in this tree only ever
WITHHOLDS a measure or a protection, never grants one, so declaring these
structural withholds exactly what must be withheld.
"""

from __future__ import annotations

import json

from deepreason.canonical import sha256_hex
from deepreason.ontology import Commitment
from deepreason.ontology.commitment import Budget

PASS, FAIL, OVERRUN = "pass", "fail", "overrun"

SUBJECT_DEMARCATION = "promotion_subject_demarcation"
REACH_INTEGRITY = "promotion_reach_integrity"
SCOPE_DETERMINISM = "promotion_scope_determinism"
COMPATIBILITY = "promotion_compatibility"
ACCOUNTS_FOR = "promotion_accounts_for"

PROMOTION_PROGRAMS: tuple[str, ...] = (
    SUBJECT_DEMARCATION,
    REACH_INTEGRITY,
    SCOPE_DETERMINISM,
    COMPATIBILITY,
    ACCOUNTS_FOR,
)

# Prop 12.1: a criterion terminates inside a DECLARED bound, and `overrun` means
# unobtainable rather than slow. The bound is a step count over the frozen
# environment, so it is a property of content and never of the machine.
PROMOTION_STEPS = 4_000


def criteria_for(certificate_ref: str) -> tuple[Commitment, ...]:
    """The five criteria, bound to ONE certificate by content address.

    The certificate digest is in the commitment id as well as in its frozen
    spec, so a criterion cannot be re-pointed at a different certificate without
    becoming a different commitment -- and the problem that pinned it would then
    no longer name it.
    """
    spec = json.dumps(
        {"certificate_ref": certificate_ref}, sort_keys=True, separators=(",", ":")
    )
    return tuple(
        Commitment(
            id=f"promotion:{name}@{certificate_ref[:12]}",
            eval=f"program:{name}",
            budget=Budget(steps=PROMOTION_STEPS, time_ms=2_000, extra={"spec": spec}),
        )
        for name in PROMOTION_PROGRAMS
    )
