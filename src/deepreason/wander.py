"""The wander cap: how much of a run's attention the operator's own question
is guaranteed, expressed as a selectable allocation policy.

The measurement that motivated it. W6's line-item post-mortem of P-C1 ARM H
(`experiments/2026-08-26-run-anatomy-program/W6-token-flow/`) cut 702 789
tokens by the problem each call was posed against:

    the operator's seed question         61 calls   373 903   53.2 %
    audit:ritual, spawned by the run    203 calls   289 676   41.2 %
    repair re-asks                       28 calls    39 210    5.6 %

`audit:ritual` -- "audit the critic: adjudication-ritual flags sustained
(§11.3)" -- appeared at log seq 345 of 3 200, about two cycles in, and then
spawned `disc:audit:ritual`. Before that event the run spent 100 % of its
budget on the operator's question; after it, 48.3 %. Nothing was wrong: every
spawn was lawful and the wandering was the harness working as built. It simply
had no floor.

What this module is. A FLOOR on the seed lineage's share of worked cycles,
decided by a policy selected from a registry by id, consumed by the scheduler
through ONE entry point. It is the VERSIONED layer of the signal contract
(`DR-INV-signal-contract`): the registry and the algorithm may change through
`DR-REC-revise-allocation-policy`; the protocol over them may not.

What it is NOT, and this is the strictest row of the contract it lives under:
**allocation touches EFFICIENCY, NEVER EVIDENCE.** Nothing here reads a status,
mints a warrant, constructs an edge, or knows a conjecture's or a criticism's
KIND. A throttle decides which problem a cycle LOOKS AT next. It confers
nothing on what it looks at and takes nothing from what it does not, and the
guard on that claim is a differential over one scripted record rather than this
paragraph.
"""

from __future__ import annotations

from dataclasses import dataclass

# The signals a shipped lineage policy reads and emits. Declared in
# `signals.py` and listed in `allocation.POLICY_SIGNALS` with a producer
# predicate each -- the pair, never half of it. Named here so a policy author
# can see, in the module they are editing, exactly what the record will carry.
SIGNALS: tuple[str, ...] = (
    "allocation.seed-lineage-share.v1",
    "allocation.wander-throttled.v1",
)


@dataclass(frozen=True)
class LineageReading:
    """Everything a lineage policy is handed, and nothing else.

    Numbers over PROCESS facts -- how many cycles have been worked, how they
    split between the operator's seeded lineage, everything the run spawned for
    itself and the run's own capability work, and the configured floor. No
    status, no artifact, no problem body, no criticism kind: a policy that
    cannot SEE an outcome has no outcome to game, which is the same structural
    argument the allocation controller's process-only signal diet rests on.
    """

    cycles: int
    seed_worked: int
    other_worked: int
    floor: float
    # Cycles the capability step took. NOT a fifth process fact bolted on: it
    # completes the partition, so seed_worked + other_worked +
    # capability_cycles == cycles exactly. A capability cycle advances the
    # scheduler's counter and selects no problem, so a throttle has no
    # candidacy to restrict on it; the POLICY decides what that means, which
    # is why the count arrives here rather than being resolved by the caller.
    capability_cycles: int = 0


@dataclass(frozen=True)
class LineageDecision:
    """One policy's answer, and the record of how it got there.

    `engaged` is the whole behavioural output. `share`, `floor` and `policy_id`
    exist so the disclosure can state the reading rather than merely announce
    the verdict -- a throttle that says "throttling" and not "0.31 against a
    floor of 0.50" is not disclosable evidence about its own behaviour.
    """

    policy_id: str
    engaged: bool
    share: float
    floor: float
    fallback_from: str | None = None

    def disclosure(self) -> str:
        return (
            f"{self.policy_id}: seed-lineage share {self.share:.4f} "
            f"{'below' if self.engaged else 'at or above'} floor {self.floor:.4f}"
        )


def wander_cap_v1(reading: LineageReading) -> LineageDecision:
    """The shipped policy: throttle while the seed lineage is under its floor.

    Before the first cycle the share is 1.0, not 0.0. A run that has worked
    nothing has not yet failed its floor, and treating an empty record as a
    violation would throttle cycle 0 -- the one cycle the operator's question
    is guaranteed outright by the scheduler's own oldest tie-break rule
    (`DR-CON-scheduler-ranking`).

    The denominator is GOVERNED cycles, not all of them: a capability cycle
    selects no problem, so this throttle -- a candidacy gate and nothing else
    -- has no candidacy to withhold on it. Counting it would drive the share
    down for a reason the gate can never act on. Live evidence that this is not
    hypothetical: P-T1 epoch 6 spent 20 of 24 cycles inside one simulation
    (audit finding F-F).
    """
    governed = reading.cycles - reading.capability_cycles
    share = (reading.seed_worked / governed) if governed > 0 else 1.0
    return LineageDecision(
        policy_id="wander-cap.v1",
        engaged=governed > 0 and share < reading.floor,
        share=share,
        floor=reading.floor,
    )


def open_lineage_v1(reading: LineageReading) -> LineageDecision:
    """The null policy: never throttle.

    Shipped, and not merely available: a registry with one entry cannot
    demonstrate that selection WORKS, and "you may turn the cap off" has to be
    a configuration rather than a code edit like everything else here. It is
    also the second arm of the evidence differential.
    """
    governed = reading.cycles - reading.capability_cycles
    share = (reading.seed_worked / governed) if governed > 0 else 1.0
    return LineageDecision(
        policy_id="open-lineage.v1",
        engaged=False,
        share=share,
        floor=reading.floor,
    )


# The VERSIONED registry. A new throttle enters by declaration and is selected
# by `Config.ATTENTION_ALLOCATION_POLICY`; nothing downstream is taught its name.
LINEAGE_POLICIES = {
    "wander-cap.v1": wander_cap_v1,
    "open-lineage.v1": open_lineage_v1,
}

DEFAULT_POLICY_ID = "wander-cap.v1"


def decide(config, reading: LineageReading) -> LineageDecision:
    """The ONE entry point a consumer may call.

    An unknown policy id falls back to the shipped default and SAYS SO in the
    decision (`fallback_from`) -- the all-configurations law: a configuration
    naming a policy that does not exist still compiles and still runs, and
    discloses. Refusing here would make a typo terminal for a run that is
    otherwise entirely lawful.
    """
    requested = getattr(config, "ATTENTION_ALLOCATION_POLICY", DEFAULT_POLICY_ID)
    policy = LINEAGE_POLICIES.get(requested)
    if policy is None:
        return LINEAGE_POLICIES[DEFAULT_POLICY_ID](reading).__class__(
            **{
                **vars(LINEAGE_POLICIES[DEFAULT_POLICY_ID](reading)),
                "fallback_from": str(requested),
            }
        )
    return policy(reading)


def reading_from(
    config, *, cycles: int, seed_worked: int, capability_cycles: int = 0
) -> LineageReading:
    """Build the reading from the counters a scheduler already keeps.

    Here rather than in the scheduler so that the floor is read from
    configuration in ONE place: a consumer that assembled its own reading could
    quietly consult a different knob, and then the policy would be deciding
    against a floor nobody configured.
    """
    return LineageReading(
        cycles=int(cycles),
        seed_worked=int(seed_worked),
        other_worked=max(0, int(cycles) - int(seed_worked) - int(capability_cycles)),
        floor=float(getattr(config, "SEED_PROBLEM_BUDGET_FLOOR", 0.0)),
        capability_cycles=int(capability_cycles),
    )
