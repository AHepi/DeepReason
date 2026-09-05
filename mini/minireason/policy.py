"""Which commitment channels a mini run executes.

Implements S3 (R3, C10) of the mini isolation programme. R3 is the operator's
"it needs to run its full conjecture/criticism cycles with commitments
disabled".

TWO SWITCHES, NOT ONE, because there are two channels and the operator must be
able to restore either. `mandatory_skeleton_wf` is the well-formedness
commitment compiled onto EVERY candidate; `model_authored_forbidden` is the
candidate's own `forbidden[]` cases. Collapsing them into one flag would leave
no way back from either.

SWITCHING ONE OFF IS A WARNING, NEVER A REFUSAL AND NEVER SILENCE (C10, the
operator's own words of 2026-08-28: "Gates are always optional: with
warnings"). The warning text names what is no longer being checked, and the
run writes it into its OWN RECORD -- a reader opening the root months later
must be able to see that these cycles ran without the checks.
"""

from __future__ import annotations

from dataclasses import dataclass


#: The typed marker every commitments-disabled warning starts with, so a
#: reader can find them in a record without knowing this module's vocabulary.
COMMITMENTS_DISABLED_MARKER = "mini:commitments-disabled"


@dataclass(frozen=True, slots=True)
class MiniCommitmentPolicyV1:
    """Which commitment channels this run executes. Both ON by default."""

    mandatory_skeleton_wf: bool = True
    model_authored_forbidden: bool = True

    @property
    def disabled_channels(self) -> tuple[str, ...]:
        """The channels this policy switches OFF, named for the record."""

        off = []
        if not self.mandatory_skeleton_wf:
            off.append("skeleton-wf")
        if not self.model_authored_forbidden:
            off.append("model-authored-forbidden")
        return tuple(off)

    def warning_markers(self) -> tuple[str, ...]:
        """One typed marker per disabled channel, plus a summary line.

        Stated per channel rather than as one blob because a reader wants to
        know WHICH check did not run; a single "commitments disabled" marker
        would leave them unable to tell the two configurations apart.
        """

        off = self.disabled_channels
        if not off:
            return ()
        return tuple(f"{COMMITMENTS_DISABLED_MARKER}:{name}" for name in off) + (
            f"{COMMITMENTS_DISABLED_MARKER}: these cycles ran without "
            + ", ".join(off),
        )


DEFAULT_MINI_COMMITMENT_POLICY = MiniCommitmentPolicyV1()


__all__ = [
    "COMMITMENTS_DISABLED_MARKER",
    "DEFAULT_MINI_COMMITMENT_POLICY",
    "MiniCommitmentPolicyV1",
]
