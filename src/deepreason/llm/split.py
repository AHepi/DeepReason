"""The split-budget seat protocol: deliberate at B_r, then extract at B_a.

A reasoning model handed ONE completion budget must fit its hidden reasoning
and its schema-valid answer inside it.  Because the reasoning precedes the
answer autoregressively, a hard question spends the whole cap thinking and the
seat emits nothing at all -- the ledgered glm-5.2 empty-completion seat
failure.  Giving that call more tokens does not fix it: the extra tokens extend
the reasoning rather than produce an answer.

So the fix is modal, not budgetary.  One seat call becomes two provider legs
against the same route, the same lease and the same authorization: leg
``reason`` deliberates in prose and is allowed to be cut off, leg ``extract``
is fed whatever trace exists -- truncated, or empty -- and does nothing but
serialize it into the wire contract, with thinking switched off so its whole
budget reaches the answer.

Two constraints shape every number here.

* ``B_a`` is taken OUT of the ceiling, never added to it: ``B_r + B_a ==
  ceiling``.  A route lease binds the completion side of the envelope as a
  ceiling (``EndpointLease.verify``), and a split that spent both budgets on
  top of each other would escape the bound the controller is clamped to.
* Nothing here refuses.  A seat that cannot be split -- no reasoning knob, no
  ceiling, a ceiling too small to divide, no document describing the model --
  runs exactly as it did before and records a typed notice saying which.

The value the emission leg sends is READ FROM THE MODEL'S OWN DOCUMENT and is
never a literal in this file.  It used to be one: `providers.REASONING_OFF`,
the string "none", on every model.  On glm-5.3 that value does not stop the
thinking, it stops the SEPARATION -- the trace lands in `message.content` ahead
of the answer, this leg's budget is spent before any JSON appears, and the cap
ratchet then shrinks the budget until the seat exhausts.  Three runs died that
way.  See `DR-CON-model-profiles`.

This module is pure: no I/O, no route, no endpoint, no meter.  It computes a
plan and renders two request bodies; the adapter owns everything that spends.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from deepreason.llm.providers import reasoning_knob_available

if TYPE_CHECKING:  # pragma: no cover - typing only
    from deepreason.model_profiles import ModelProfileV1

SPLIT_LEG_REASON = "reason"
SPLIT_LEG_EXTRACT = "extract"

# Every typed notice this protocol can record.  A notice is never a refusal.
NOTICE_NOT_A_REASONING_SEAT = "split-budget:seat-thinking-is-disabled"
NOTICE_NO_REASONING_KNOB = "split-budget:provider-has-no-reasoning-knob"
NOTICE_THINKING_NOT_DISABLABLE = "split-budget:extraction-leg-cannot-stop-thinking"
NOTICE_NO_CEILING = "split-budget:route-declares-no-completion-ceiling"
NOTICE_CEILING_TOO_SMALL = "split-budget:ceiling-too-small-to-divide"
NOTICE_REPAIR_BUNDLE = "split-budget:repair-authorization-is-single-leg"
NOTICE_ENVELOPE = "split-budget:extraction-request-exceeds-the-frozen-envelope"
NOTICE_NO_HEADROOM = "split-budget:no-token-headroom-for-the-extraction-leg"
# Nobody has written this model's document, so nothing knows what its emission
# leg should send.  Under "nothing ships" (operator, 2026-09-01) this is the
# DEFAULT state of every model, not an edge case -- which is exactly why the
# protocol stands down here instead of guessing, and why the notice is
# disclosed only when a run explicitly asked to split.
NOTICE_MODEL_PROFILE_MISSING = "split-budget:no-model-profile-for-this-seat"
# The document exists but says nothing about reasoning.  Distinct from the
# above on purpose: one says nobody has looked at this model, the other says
# someone looked and did not record this.
NOTICE_PROFILE_DECLARES_NO_REASONING = "split-budget:profile-declares-no-reasoning"
# A route that constrains EVERY completion to the contract has no room for a
# deliberation leg: the first leg would be schema-bound too, which is the exact
# coupling the protocol exists to undo. Honoring the frozen output mode matters
# more than splitting, so the seat runs undivided and says why.
NOTICE_OUTPUT_MECHANISM = "split-budget:route-constrains-every-completion"

MODES = ("auto", "on", "off")

# The emission leg saturates well before it needs a large budget, but below
# this it cannot reliably close a JSON envelope at all, and a split that hands
# the reasoning leg less than the emission leg has inverted the whole point.
# Both floors come out of the same rule: the emission leg takes at most half
# the ceiling, and a ceiling that cannot afford this much on each side is not
# divided.
MIN_EXTRACT_TOKENS = 256


@dataclass(frozen=True)
class SplitPlan:
    """One attempt's division of one completion ceiling.

    Frozen because the division happens once, before the first leg is sent:
    a budget retuned between legs would let the pair escape the ceiling the
    reservation already booked against.
    """

    armed: bool
    reason_max_tokens: int
    extract_max_tokens: int
    # The reasoning value the extraction leg overrides onto its request, or
    # None for "send no override" -- which is the only honest thing to do for
    # a provider whose neutral knob has no realization.
    extract_reasoning: str | None
    # Typed reason the protocol was not fully honored; "" when it was.
    notice: str
    # Whether that notice belongs in the append-only record.  A notice
    # discloses an intent the run could not honor, and under "auto" a seat
    # that simply does not think expresses no such intent -- recording one
    # there would stamp a constant string on every attempt of every
    # non-reasoning run and say nothing.
    disclosed: bool


UNARMED_PLAN = SplitPlan(
    armed=False,
    reason_max_tokens=0,
    extract_max_tokens=0,
    extract_reasoning=None,
    notice="",
    disclosed=False,
)


def plan_split(
    *,
    mode: str,
    ceiling: int | None,
    extraction_tokens: int,
    provider: str,
    reasoning: str | int | None,
    profile: "ModelProfileV1 | None",
) -> SplitPlan:
    """Divide one completion ceiling into a reasoning leg and an emission leg.

    ``mode`` is the run's choice: ``off`` never splits, ``on`` always tries,
    ``auto`` splits exactly the seats whose route says they think.

    ``profile`` is this model's document, or ``None`` when nobody has written
    one.  It has NO DEFAULT deliberately: a caller that forgets it gets a
    ``TypeError`` rather than the guessing this parameter exists to end.  Two
    questions that used to be answered by a constant are answered by it, and
    both are per-MODEL facts that no per-provider table can hold:

    * what the emission leg should send -- ``reasoning.extraction_value``;
    * whether the seat is ALREADY thinking-off, which decides ``auto`` --
      ``reasoning.disabling_values``.  Unset is still not off, and now
      "explicitly set to the off token" is not off either unless this model's
      document says that token disables it.  On glm-5.3 it does not.
    """

    if mode not in MODES:
        raise ValueError(f"unknown split-budget mode {mode!r}; expected {MODES}")
    if mode == "off":
        return UNARMED_PLAN

    knob = reasoning_knob_available(provider)
    facts = getattr(profile, "reasoning", None)

    if mode == "auto" and not knob:
        return _replace_notice(NOTICE_NO_REASONING_KNOB)
    if profile is None:
        return _replace_notice(
            NOTICE_MODEL_PROFILE_MISSING, disclosed=(mode == "on")
        )
    if facts is None:
        return _replace_notice(
            NOTICE_PROFILE_DECLARES_NO_REASONING, disclosed=(mode == "on")
        )

    # Unset is NOT off, and neither is a value this model does not actually
    # stop thinking for.  Only the document decides.
    thinking_off = reasoning is not None and str(reasoning).strip() in tuple(
        facts.disabling_values
    )

    if mode == "auto":
        if thinking_off:
            return _replace_notice(NOTICE_NOT_A_REASONING_SEAT)
        notice = ""
    else:
        # Explicitly requested. A provider with no reasoning adapter cannot
        # carry any reasoning field, and a model whose document says thinking
        # cannot be disabled will keep thinking on the emission leg whatever
        # is sent; the leg runs anyway and the record says what could not be
        # honored.
        notice = (
            "" if (knob and facts.thinking_disablable)
            else NOTICE_THINKING_NOT_DISABLABLE
        )

    if not ceiling or int(ceiling) <= 0:
        return _replace_notice(NOTICE_NO_CEILING, disclosed=(mode == "on"))

    ceiling = int(ceiling)
    # Half is a ceiling on the emission leg, not a target: the split is meant
    # to be heavily skewed to reasoning, and taking B_a out of the ceiling
    # rather than adding it keeps B_r + B_a == ceiling.
    extract = min(int(extraction_tokens), ceiling // 2)
    if extract < MIN_EXTRACT_TOKENS:
        # Handing either leg a budget it cannot work in is worse than not
        # splitting at all.
        return _replace_notice(NOTICE_CEILING_TOO_SMALL, disclosed=(mode == "on"))
    reason = ceiling - extract

    return SplitPlan(
        armed=True,
        reason_max_tokens=reason,
        extract_max_tokens=extract,
        extract_reasoning=facts.extraction_value if knob else None,
        notice=notice,
        disclosed=bool(notice),
    )


def stand_down(notice: str) -> SplitPlan:
    """An armed plan abandoned at dispatch, keeping only its typed reason.

    The run-time preconditions the planner cannot see -- the frozen request
    envelope, the token meter, a repair authorization -- fail here rather than
    in ``plan_split``, and they fail into an ordinary undivided call.
    """

    return _replace_notice(notice, disclosed=True)


def _replace_notice(notice: str, *, disclosed: bool = False) -> SplitPlan:
    return SplitPlan(
        armed=False,
        reason_max_tokens=0,
        extract_max_tokens=0,
        extract_reasoning=None,
        notice=notice,
        disclosed=disclosed,
    )


_DELIBERATE = """

STEP 1 OF 2 - DELIBERATE ONLY.
Think this through in plain prose. Work the problem: say what it turns on,
weigh what tells against your reading, and name where you are still unsure.
Do NOT produce JSON and do not try to fill the schema above. A separate step
serializes the answer from whatever you write here, so partial work is
useful and being cut off mid-sentence costs nothing."""

_SERIALIZE = "STEP 2 OF 2 - SERIALIZE ONLY.\nReturn ONLY one JSON value matching this closed schema:"

_TRACE_HEADER = "DELIBERATION SO FAR (may be truncated, or empty):"


def deliberation_request(request: str) -> str:
    """The reasoning leg's body: the seat's own request, told to think first."""

    return request + _DELIBERATE


def extraction_request(*, schema: str, trace: str) -> str:
    """The emission leg's body: the schema, the trace, and nothing else.

    Deliberately minimal.  The tax a structured-output interface charges rises
    steeply with schema weight, and the whole point of the second leg is that
    it does no thinking -- so every constraint that belongs to deliberation
    stays on leg one, and redundant fields here are pure cost.
    """

    return "\n\n".join((_SERIALIZE, schema, _TRACE_HEADER, trace or "(nothing)"))
