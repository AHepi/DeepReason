<!-- DR-INV-evidence-channels -->
Verified-at: 9cda513bd
Verify: python -m pytest tests/test_evidence_channels.py -q
Owns: src/deepreason/channels.py
Seams: DR-SEAM-capabilities-x-rules
Seams-undocumented: capabilities x channels, channels x manifest

# Evidence channels — the three that mint, on by default, and what turns one off

Read this before changing what a run may reach for outside its own reasoning.

## The law it encodes

Operator, 2026-08-14, standing (CLAUDE.md; ledgered at
`experiments/2026-08-14-change-calculus-reconciliation-v2/` REQUEST.md
Amendment 9, R68/R69):

> Code testing, simulation, scratch pad and research backends need to stay live
> and be able to mint their own evidence.

and, the same day, the correction that separates the four:

> Sorry not scratch pad. that doesn't mint evidence

Operator, 2026-08-26, which made "live" mean "on by default":

> now the fix. including turning research and, simulation and coding
> permanently on

and, the reason, the same day:

> simulation and code backends are important. so is research. Otherwise how is
> an LLM supposed to test code

**Three rows, not four.** The scratch pad is protected-LIVE but ADVISORY
(`advisory_non_grounding`): it informs conjecture and mints nothing. A registry
of EVIDENCE channels that listed it would assert the thing the operator's own
correction denies, so its absence is a decision and not an oversight.

`check: python -c "from deepreason import channels; assert set(channels.CHANNEL_DECLARATIONS) == {'research','simulation','code-testing'}, sorted(channels.CHANNEL_DECLARATIONS); assert not {'scratch','scratchpad'} & set(channels.CHANNEL_DECLARATIONS)"`

## What a declaration is

`ChannelDeclaration` carries `id`, `mints` (in the operator's own words),
`default_enabled`, `toggle` (the `Config` field that turns it off),
`enforcement` (where that toggle is actually READ) and `authority`.

`enforcement` is the field that earns its place. A declaration that claimed a
switch no consumer consults would be exactly the failure this repo has already
paid for once: `Controller._apply_cap` wrote `endpoint.max_tokens` for two days
while nothing read it, and 47 recorded tuning decisions became the `max_tokens`
of no call at all (`DR-SEAM-llm-x-scheduler`, the third-link section). A
registry can lie the same way, so every row says where it is enforced.

`check: python -c "
from deepreason import channels
from deepreason.config import Config
fields = type(Config()).model_fields
for cid, d in channels.CHANNEL_DECLARATIONS.items():
    assert d.toggle in fields, (cid, d.toggle)
    assert d.enforcement and d.authority, cid
"`

## On by default, and one field turns any of them off

Every declared channel is `default_enabled=True`, and `Config.CHANNELS_DISABLED`
— ONE field, for every channel present and future — names the ids that are off.
A new channel gets its switch by REGISTERING, never by adding a knob: that is
what makes the operator's modularity law ("Customisation needs to be easy",
2026-08-26) a property of the design rather than a promise about future authors.

`check: python -c "
from deepreason import channels
from deepreason.config import Config
c = Config()
assert all(d.default_enabled for d in channels.CHANNEL_DECLARATIONS.values())
assert all(channels.enabled(i, c) for i in channels.CHANNEL_DECLARATIONS)
off = Config(CHANNELS_DISABLED=('research',))
assert not channels.enabled('research', off) and channels.enabled('simulation', off)
assert len({d.toggle for d in channels.CHANNEL_DECLARATIONS.values()}) == 1
"`

An id naming no declared channel is a typed `CompileNoticeV1`
(`CHANNEL_UNKNOWN`), never a refusal — the all-configurations law (operator,
2026-08-12: "All configurations should be allowed") applied to channels. A typo
must not stop a run, and must not pass silently either: silence is how an
operator believes a channel is off when it is on.

`check: python -c "
from deepreason import channels
from deepreason.config import Config
(n,) = channels.unknown_channel_notices(Config(CHANNELS_DISABLED=('reserch',)))
assert n.code == 'CHANNEL_UNKNOWN' and 'research' in (n.resolution or '')
assert channels.disabled_channels(Config(CHANNELS_DISABLED=('reserch',))) == ()
"`

## The website is a DECLARED ABSENCE

Operator, 2026-08-14: "There was a website development pipeline that I
decommissioned a while ago. That needs to stay decommissioned."

`DECOMMISSIONED` names it, so the registry can be ASKED about the website and
answer. A registry silent about it is indistinguishable from one that forgot
it, and an oversight is how a remnant gets revived — `SpawnTrigger.SUCCESSOR`
survived one census on exactly that reasoning (Rung 3a, corrected at 3d).

`check: python -c "
from deepreason import channels
from deepreason.config import Config
assert 'website' in channels.DECOMMISSIONED
assert 'website' not in channels.CHANNEL_DECLARATIONS
assert channels.enabled('website', Config(CHANNELS_DISABLED=('website',))) is False
"`

## The road, not the flag

An enabled channel with a zero budget, or research with an empty allowlist,
is a severed road wearing an enabled flag — and its own policy validator
refuses that shape ("enabled research requires a frozen domain allowlist").
A default-ON research channel therefore REQUIRES a default list, which is why
`DEFAULT_RESEARCH_ALLOWLIST` exists. `DEEPREASON_RESEARCH_ALLOWLIST` still
overrides it: the setting names WHICH hosts, never WHETHER research runs.

`check: python -c "
from deepreason import channels
from deepreason.config import Config
from deepreason.v6_policy import engaged_research_policy
p = engaged_research_policy({}, config=Config())
assert p.enabled and p.domain_allowlist and p.maximum_requests > 0 and p.maximum_sources > 0
blank = engaged_research_policy({'DEEPREASON_RESEARCH_ALLOWLIST': ' , ,'}, config=Config())
assert blank.enabled and blank.domain_allowlist == channels.DEFAULT_RESEARCH_ALLOWLIST
named = engaged_research_policy({'DEEPREASON_RESEARCH_ALLOWLIST': 'example.org'}, config=Config())
assert named.domain_allowlist == ('example.org',)
"`

## Enablement, and NOTHING else

This module decides whether a channel is on. It weights no criticism, reads no
status, mints no warrant, and knows no conjecture or criticism KIND.

Operator, 2026-08-26: **"This doesn't demote prose as legitimate criticism."**
Turning a channel on gives a critic an ADDITIONAL road — a verdict a machine
computed rather than a case that must be believed — and takes nothing from a
critic who reaches for prose. This is the criticism-side reading of the
standing 2026-08-08 law, which says the same thing from the conjecture side:
nothing may penalize a conjecture for being informal, "not admission, not rank,
not criticism exposure, not acceptance".

The guard is a DIFFERENTIAL, not an assurance — the same instrument
`DR-INV-signal-contract` requires of allocation: one scripted record whose only
criticism is prose, adjudicated with the channels on and with them off, every
label, edge, warrant and dependency identical.

`check: python -m pytest tests/test_evidence_channels.py -q -k "prose or kind_blind"`

## Where the toggle is read

| Channel | Enforcement site | What OFF compiles to |
|---|---|---|
| `research` | `v6_policy.engaged_research_policy` → the compiled manifest | `ResearchCapabilityPolicyV1()`, the all-zero policy |
| `simulation` | `v6_policy.engaged_simulation_policy` → the compiled manifest | `SimulationCapabilityPolicyV1()`, the all-zero policy |
| `code-testing` | none — **unconditional** | nothing; see the trap below |

Both enforced toggles reach the manifest through ONE door,
`preparation.build_preparation_manifest`, which every launch path enters
(operations-parity law, 2026-08-13). A channels-off configuration COMPILES; it
does not refuse.

`check: python -m pytest tests/test_evidence_channels.py -q -k compiles`

## Traps

- **A default that is `True` over a road that is severed.** The flag is the
  cheap half. Assert the values a dispatch or a controller would actually
  CONSUME — a non-empty allowlist, a positive request budget, a controller that
  constructs against the compiled manifest — or the registry states an
  enablement the run cannot use. The allocation controller is the worked
  example: `DR-SEAM-llm-x-scheduler`.
- **Code-testing has no off-switch, and that is recorded rather than hidden.**
  Its `enforcement` reads `unconditional`. Its only live entry points are the
  commitment compilers in `workloads/text.py` and `informal/skeleton.py`, whose
  commitment ids are CONTENT-ADDRESSED digests over the compiled shape — gating
  there would change what a record CONTAINS rather than what a run may reach
  for, which is evidence-side surgery and needs its own tranche. Parked at
  `experiments/2026-08-26-change-f3-channels-and-wander-cap/` PARKED.md P1. The
  claim that it is nonetheless ON is checked by DRIVING the road, not asserted.
`check: python -m pytest tests/test_evidence_channels.py -q -k code_testing`
- **Turning research on moves every qualification subject digest.** The
  allowlist is part of the compiled manifest and the manifest is part of the
  qualification behavior subject, so the change from "no research" to the
  declared default requalifies every home (~14 min, ~1160 calls). That is the
  price of the default, and it was measured before the code rather than
  discovered after (that tranche's SPEC.md, M1).
- **An enabled channel can still be a severed ROAD one layer down, and the
  simulation channel was.** The flag said ON from 2026-08-26; every
  `sandboxed_python_v1` proposal was nonetheless denied
  `runner_profile_mismatch`, because `engaged_simulation_policy` returns
  `runner_profile="simulation.declarative.v1"` by default while binding
  `PUBLIC_SIMULATION_TOOLCHAIN_ID` — a Python toolchain the declarative
  profile can never dispatch to. Four live epochs were read as model
  reluctance before the record said otherwise (commit `74d9f71ca`, branch
  `claude/spec-to-code-technique-k5209o`). This is the first Trap above
  happening for real: the registry was accurate, and accuracy about the
  FLAG is not accuracy about the ROAD. Census and citations:
  `experiments/2026-08-27-change-execution-safety/SPEC.md` F2/F3. The typed
  disclosure this shape requires under the all-configurations law is parked
  at that tranche's PARKED.md P3.
- **`code-testing` executes model-authored Python TODAY, and its containment
  is weaker than the channel that is off.** The row above says the channel is
  ungated; what that means operationally is that `codec="code:python"`
  artifacts and model-authored `checker_spec.source` run on every run through
  `oracle_sandbox`, which has no network namespace and applies its rlimits
  fail-OPEN. A 2026-08-27 assessment escaped both that guard and
  `verification/contained.py`'s by a running-generator frame walk
  (`gg.gi_frame.f_back.f_back.f_globals` — no leading-underscore attribute
  anywhere, so neither denylist sees it), reached the real `builtins`, and
  opened a TCP connection to the open internet while the exec-oracle
  commitment returned `pass`. Verdict, gap list and a re-runnable
  self-cleaning reproduction:
  `experiments/2026-08-27-change-execution-safety/SAFETY.md` and its
  `proof/`. **FIXED the same day**, on the operator's instruction ("can you fix
  please"): the attribute boundary moved to `deepreason.sandbox_guard`, which
  denies CPython's whole introspection prefix set and proves that set closed by
  re-derivation; and this channel's worker now runs behind the network
  namespace `deepreason.sandbox_os` probes, where before it carried no OS
  boundary whatsoever. The entry stays because a Trap is never deleted: the
  lesson is that a channel being ON says nothing about the containment of the
  road it opens, and that both facts have to be checked separately.
`check: python -m pytest tests/test_sandbox_guard.py -q -k "code_testing or network"`
- **Adding a channel is a row; adding a KNOB for it is a mistake.** One toggle
  field serves every channel. A second field would move every qualification
  subject digest again and would make the registry no longer the one authority
  on what is customizable.
