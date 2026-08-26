"""The evidence-channel registry: which outside-reaching channels a run has,
whether each is on, and what turns one off.

The operator's standing ruling (2026-08-14, CLAUDE.md and
``experiments/2026-08-14-change-calculus-reconciliation-v2/`` REQUEST.md
Amendment 9) names four protected channels and, in a same-day correction,
separates them by what they MINT::

    "Code testing, simulation, scratch pad and research backends need to stay
     live and be able to mint their own evidence."
    "Sorry not scratch pad. that doesn't mint evidence"

Three of the four mint evidence and are declared here. The scratch pad is
protected-LIVE but ADVISORY (``advisory_non_grounding``) and is deliberately
NOT a row: a registry of evidence channels that listed it would be asserting
the thing the operator's own correction denies.

Why a registry rather than three ``if`` statements. Before this module the
three facts lived apart -- simulation on inside one preset builder, research
off unless an environment variable named hosts, code-testing ungated and
written down nowhere -- so "which channels does this run have" had no answer
that could be asked, and research was off for every run nobody had configured.
The operator's modularity law (2026-08-26) states the general form: every
behavior a run can vary is reachable as CONFIGURATION or a REGISTERED,
VERSIONED ARTIFACT, never by editing code. A channel therefore enters by
DECLARATION and is toggled by ONE ``Config`` field, so adding the fourth costs
a row and no new knob.

What this module is NOT. It decides ENABLEMENT and nothing else. It weights no
criticism, reads no status, mints no warrant and knows no conjecture or
criticism KIND. Turning a channel on gives a critic an ADDITIONAL road -- a
verdict a machine computed rather than a case that must be believed -- and
takes nothing whatever from a critic who reaches for prose (operator,
2026-08-26: "This doesn't demote prose as legitimate criticism"; the standing
2026-08-08 law says the same from the conjecture side).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChannelDeclaration:
    """One evidence-minting channel, declared.

    ``mints`` is stated in the operator's own terms from the 2026-08-14 ruling
    rather than in ours, because the whole point of the row is to record what
    the channel is FOR; a paraphrase would drift from the authority the next
    reader has to check it against. ``enforcement`` names where the toggle is
    actually read, so a declaration can never claim a switch that no consumer
    consults -- the failure mode this repo has already paid for once, in an
    allocation controller whose 47 decisions reached no dispatch.
    """

    id: str
    mints: str
    default_enabled: bool
    toggle: str
    enforcement: str
    authority: str


# The registry. Versioned as a whole: a change to what these rows MEAN is a
# versioned change under the signal-contract pattern, while a change to which
# ids a given run disables is free configuration.
CHANNEL_REGISTRY_VERSION = "evidence-channels.v1"

# The one Config field every channel's toggle names. ONE field for every
# channel present and future: a new channel gets its switch by registering,
# never by adding a knob, which is what makes "customisation is easy" a
# property of the design rather than a promise about future authors.
CHANNEL_TOGGLE_FIELD = "CHANNELS_DISABLED"

CHANNEL_DECLARATIONS: dict[str, ChannelDeclaration] = {
    "research": ChannelDeclaration(
        id="research",
        mints="fetch receipts as citable evidence",
        default_enabled=True,
        toggle=CHANNEL_TOGGLE_FIELD,
        enforcement="v6_policy.engaged_research_policy -> the compiled manifest",
        authority="operator 2026-08-14 (R68/R69), operator 2026-08-26",
    ),
    "simulation": ChannelDeclaration(
        id="simulation",
        mints="typed proposals through receipts",
        default_enabled=True,
        toggle=CHANNEL_TOGGLE_FIELD,
        enforcement="v6_policy.engaged_simulation_policy -> the compiled manifest",
        authority="operator 2026-08-14 (R68/R69), operator 2026-08-26",
    ),
    "code-testing": ChannelDeclaration(
        id="code-testing",
        mints="execution-grade verdicts",
        default_enabled=True,
        # The field a future off-switch must read. It has none today, and that
        # is recorded rather than hidden: this channel's only live entry points
        # are the commitment compilers in `workloads/text.py` and
        # `informal/skeleton.py`, whose commitment ids are CONTENT-ADDRESSED
        # digests over the compiled shape, so gating there would silently
        # change what a record contains. See the tranche's PARKED.md P1.
        toggle=CHANNEL_TOGGLE_FIELD,
        enforcement="unconditional — no gate exists; see PARKED.md P1",
        authority="operator 2026-08-14 (R68/R69), operator 2026-08-26",
    ),
}

# Declared ABSENCE, so the registry can be asked about the website pipeline and
# answer, instead of being silent. Operator, 2026-08-14: "There was a website
# development pipeline that I decommissioned a while ago. That needs to stay
# decommissioned." Silence would be indistinguishable from an oversight, and
# an oversight is how a remnant gets revived.
DECOMMISSIONED: frozenset[str] = frozenset({"website"})

# Research cannot be enabled without a frozen domain allowlist -- the policy
# validator refuses it ("enabled research requires a frozen domain allowlist")
# -- so a default-ON research channel REQUIRES a default list. Two stable,
# citable hosts is the smallest honest one. It is configuration in both
# directions: DEEPREASON_RESEARCH_ALLOWLIST overrides it exactly as before,
# and a different list here is a different qualification subject.
DEFAULT_RESEARCH_ALLOWLIST: tuple[str, ...] = ("arxiv.org", "en.wikipedia.org")


def _disabled_ids(config) -> frozenset[str]:
    raw = getattr(config, CHANNEL_TOGGLE_FIELD, ()) or ()
    return frozenset(str(entry).strip().lower() for entry in raw if str(entry).strip())


def enabled(channel_id: str, config) -> bool:
    """Is this channel on for this configuration?

    An id that names no declared channel is False -- including every
    decommissioned id, so a consumer that asks about the website gets a plain
    "no" rather than a KeyError it would have to interpret.
    """
    declaration = CHANNEL_DECLARATIONS.get(channel_id)
    if declaration is None:
        return False
    if not declaration.default_enabled:
        return False
    return channel_id not in _disabled_ids(config)


def disabled_channels(config) -> tuple[str, ...]:
    """Declared channels this configuration turns off, sorted.

    Only DECLARED ids appear: an unrecognised entry is a notice (below), not a
    disabled channel, because reporting it here would let a typo masquerade as
    a deliberate setting.
    """
    off = _disabled_ids(config)
    return tuple(sorted(i for i in CHANNEL_DECLARATIONS if i in off))


def unknown_channel_notices(config):
    """Entries in the toggle that name no declared channel, as typed notices.

    Disclose, never die -- the all-configurations law (operator, 2026-08-12:
    "All configurations should be allowed"). A configuration naming a channel
    that does not exist still compiles and still runs; it carries a notice
    saying so.

    ``CompileNoticeV1`` is imported HERE, at call time, rather than at module
    scope: the channel registry must stay importable without the manifest
    module, or a consumer that only wants to know whether research is on
    acquires a dependency on the thing that compiles manifests. The type is
    reused verbatim and never modified, the same way `allocation.py` reuses it.
    """
    from deepreason.run_manifest import CompileNoticeV1

    unknown = sorted(_disabled_ids(config) - set(CHANNEL_DECLARATIONS))
    known = ", ".join(sorted(CHANNEL_DECLARATIONS))
    return tuple(
        CompileNoticeV1(
            code="CHANNEL_UNKNOWN",
            message=f"{CHANNEL_TOGGLE_FIELD} names no declared channel {name!r}",
            pointer=f"/{CHANNEL_TOGGLE_FIELD}",
            resolution=(
                f"remove it, or name one of: {known}"
                + (
                    f" ({name!r} names a DECOMMISSIONED pipeline and is not a "
                    f"channel)"
                    if name in DECOMMISSIONED
                    else ""
                )
            ),
        )
        for name in unknown
    )
