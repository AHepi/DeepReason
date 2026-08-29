<!-- DR-SEAM-capabilities-x-channels -->
Verified-at: 25a3a0687
Verify: python -m pytest tests/test_evidence_channels.py tests/test_simulation_runner_default.py tests/test_channel_and_wander_modularity.py -q
Owns:
Sides: DR-SUB-capabilities, DR-INV-evidence-channels
Seams:
Seams-undocumented:
Sweep: CHANNELS_DISABLED|_channel_enabled|channels\.enabled && inquiry_capability_policy|ResearchCapabilityPolicyV1|SimulationCapabilityPolicyV1|policy\.enabled

# capabilities x channels — the flag is compiled; the road is dispatched

## What this seam is

`DR-INV-evidence-channels` decides WHETHER a run may reach outside itself.
`DR-SUB-capabilities` owns the typed lifecycle that does the reaching. Between
them there is **no import in either direction**: nothing under
`capabilities/` names `deepreason.channels`, and `channels.py` names nothing
under `deepreason.capabilities`. Measured coupling is 0 both ways.

The same check pins a second, stronger absence that is the whole reason this
seam is safe: **`capabilities/` imports `deepreason.config` nowhere either.**
The capability side never reads a run's configuration. It reads one frozen
policy object and nothing else.

`check: python3 -c 'import ast,pathlib;R=pathlib.Path("src/deepreason");cap=sorted(R.glob("capabilities/*.py"));N=lambda p:{a.name for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,ast.Import) for a in n.names}|{((("deepreason."+".".join(str(p.relative_to(R)).split("/")[:-n.level])).rstrip(".")+("."+n.module if n.module else "")) if n.level else (n.module or "")) for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,ast.ImportFrom)};assert len(cap)==10,len(cap);bad=[str(p) for p in cap for m in N(p) if m.startswith("deepreason.channels") or m.startswith("deepreason.config")];assert not bad,bad;assert not [m for m in N(R/"channels.py") if m.startswith("deepreason.capabilities")];assert "deepreason.canonical" in N(R/"capabilities/state.py")'`

**This document exists because the pair was invisible to every instrument.**
`INDEX.md`'s seam matrix is built from measured import coupling, so a pair with
zero traffic never appears in it, and a pair absent from that table reads as
"no interaction". `DR-SEAM-llm-x-verification` is the precedent and states the
lesson: *a pair with zero measured traffic can still be load-bearing*. Here the
agreement cost four live epochs before anyone looked (`Traps`, below).

## The agreement, in one sentence each

**The channel decides at COMPILE time; the capability obeys at RUN time.** The
channel registry answers exactly one question — is this id on for this
configuration — and it answers it while the manifest is being built. What
crosses the seam is not a flag but a compiled, frozen policy object.

**The bridge is `v6_policy`, and it is the only module that speaks both
vocabularies.** `engaged_research_policy` and `engaged_simulation_policy`
consult `channels.enabled` (through `_channel_enabled`) and return
`ResearchCapabilityPolicyV1` / `SimulationCapabilityPolicyV1` — types owned by
`capabilities/policy.py`. That function pair IS the seam; there is no other
crossing.

**OFF is the all-zero policy, not an absence.** A disabled channel compiles to
a policy that is present, valid and unable to do anything: `enabled=False`,
zero requests, zero sources, empty allowlist. It COMPILES — the
all-configurations law (operator, 2026-08-12) — so the run starts, and the
refusal happens typed at the point of use.

`check: python3 -c 'from deepreason.v6_policy import engaged_research_policy as R,engaged_simulation_policy as S;from deepreason.config import Config;from deepreason.capabilities.policy import ResearchCapabilityPolicyV1 as RP,SimulationCapabilityPolicyV1 as SP;on=Config();off=Config(CHANNELS_DISABLED=("research","simulation"));assert isinstance(R({},config=on),RP) and isinstance(S({},config=on),SP);assert R({},config=on).enabled and S({},config=on).enabled;assert not R({},config=off).enabled and not S({},config=off).enabled;assert R({},config=off).maximum_requests==0 and R({},config=off).domain_allowlist==() and R({},config=off).maximum_sources==0'`

**A channel that compiled OFF becomes a typed DENIED transition, never
silence.** Each controller's reason ladder opens on its own policy's `enabled`
flag. The two reason codes are NOT the same word — research says
`research_disabled`, simulation says `capability_disabled` — and that asymmetry
is a fact to carry, not to harmonise: a reader grepping one code finds one
capability.

`check: python3 -c 'import inspect,re;from deepreason.capabilities.research import ResearchCapabilityController as R;from deepreason.capabilities.simulation import SimulationCapabilityController as S;r=inspect.getsource(R.execute);s=inspect.getsource(S.execute);assert re.search(r"if not self\.policy\.enabled:\s*\n\s*denied\(.research_disabled.\)",r),"research";assert re.search(r"if not self\.policy\.enabled:\s*\n\s*reason = .capability_disabled.",s),"simulation";assert r.index("research_disabled")<r.index("backend_identity_mismatch")'`

## Which fraction of each side is involved

Small on both sides, and the fractions are not symmetric.

**Channels side: two of the three declared rows.** `research` and `simulation`
cross this seam. `code-testing` does not cross it at all — the string appears
nowhere under `capabilities/`, because its live entry points are the commitment
compilers in `workloads/text.py` and `informal/skeleton.py`. Its declaration
records `enforcement="unconditional"`: it has no toggle any consumer reads, so
there is nothing for a capability policy to carry. **Do not reason about the
2026-08-27 sandbox escape from this document** — that defect lives on the
code-testing channel and therefore on the other side of this boundary;
`DR-INV-evidence-channels` owns it.

Of `channels.py`'s public surface only `enabled()` is consulted here.
`disabled_channels()` and `unknown_channel_notices()` serve reporting and
compile notices; they never reach a capability.

`check: python3 -c 'import pathlib;from deepreason import channels;assert set(channels.CHANNEL_DECLARATIONS)=={"research","simulation","code-testing"},sorted(channels.CHANNEL_DECLARATIONS);src="".join(p.read_text() for p in sorted(pathlib.Path("src/deepreason/capabilities").glob("*.py")));assert "code-testing" not in src and "code_testing" not in src;assert "research" in src and "simulation" in src;assert channels.CHANNEL_DECLARATIONS["code-testing"].enforcement.startswith("unconditional")'`

**Capabilities side: two of the five sub-policies in `policy.py`, and nothing
else.** The controllers, the state machine (`state.py`), the event envelope
(`events.py`), the phase records (`models.py`) and the audit writer never see a
channel id. Each controller is constructed from a harness and a manifest —
never a `Config` — and lifts its policy straight off
`manifest.inquiry_capability_policy`. That constructor shape is the seam's
whole run-time surface.

`check: python3 -c 'import inspect;from deepreason.capabilities.research import ResearchCapabilityController as R;from deepreason.capabilities.simulation import SimulationCapabilityController as S;assert list(inspect.signature(R.__init__).parameters)==["self","harness","manifest","transport"],list(inspect.signature(R.__init__).parameters);assert list(inspect.signature(S.__init__).parameters)==["self","harness","manifest"],list(inspect.signature(S.__init__).parameters);assert "manifest.inquiry_capability_policy" in inspect.getsource(R.__init__) and "manifest.inquiry_capability_policy" in inspect.getsource(S.__init__)'`

## Why the compile-time freeze is the load-bearing part

`CHANNELS_DISABLED` is **popped out of the manifest's Config echo**
(`run_manifest.py::_versioned_source_config_data`), for the stated reason that
its effect "is already visible in the compiled manifest's own capability
policies" and that keeping it would move every qualification subject digest and
every frozen manifest golden.

That is exactly the mechanism audit finding F-A caught silently reverting five
other switches. A `--run-manifest` launch rebuilds `Config` from the echo, so
every field the echo drops comes back at its DEFAULT. For
`JUDGE_SEATS_ENABLED` and its four siblings that meant the operator's
configuration was quietly replaced with a different one.

**It cannot do that here, and the reason is structural rather than lucky.**
The channel decision never travels in the echo; it travels as the compiled
policy, which the manifest carries and which the controllers read directly. The
differential below shows both halves at once: the rebuilt `Config` HAS lost the
toggle, and the compiled policy has NOT lost the decision.

`check: python3 -c 'import sys,json;sys.path.insert(0,".");from tests.test_v6_engaged_public_defaults import STAMP,_profile;from deepreason.preparation import build_preparation_manifest as B;from deepreason.run_manifest import config_from_run_manifest as C;m=B(_profile(),question="q",compiled_at=STAMP,channels_disabled=("research",));assert m.inquiry_capability_policy.research.enabled is False;assert m.inquiry_capability_policy.simulation.enabled is True;assert "CHANNELS_DISABLED" not in json.loads(m.engine_config_json);assert C(m).CHANNELS_DISABLED==(),C(m).CHANNELS_DISABLED'`

**The consequence for anyone changing this seam:** the immunity is bought by
the capability side reading no configuration. A change that gave a controller a
`Config` — to add one convenience knob, say — would reopen F-A's failure mode
on the channels, and no existing test would name it. The first check in this
document is what goes red.

## The flag is the cheap half — enablement is not dispatchability

Two different facts live here, and this is the seam's expensive lesson:

| Fact | Owned by | What it answers |
|---|---|---|
| the channel is ON | `channels.py`, through the compiled policy's `enabled` | may this run reach outside at all |
| the road is DISPATCHABLE | `policy.runner_profile` + `python_toolchain_identity`, admitted by `SimulationCapabilityController.execute` | can the thing it reaches for actually run |

A configuration can compile the first as True while the second is severed. Both
sides then report accurately and the run still mints nothing.

Today the two agree by construction — the default runner profile and the bound
toolchain identity are a matched pair, and naming the other runner moves both
together.

`check: python3 -c 'from deepreason.v6_policy import engaged_simulation_policy as S;from deepreason.config import Config;p=S({},config=Config());assert p.runner_profile=="simulation.container.v1",p.runner_profile;assert p.python_toolchain_identity=="python@deepreason-public-contained.v1",p.python_toolchain_identity;d=S({"DEEPREASON_SIMULATION_RUNNER":"declarative"},config=Config());assert d.runner_profile=="simulation.declarative.v1" and d.python_toolchain_identity!=p.python_toolchain_identity'`

Where they can still disagree — a host that refuses the network namespace the
contained runner needs — the disagreement is DISCLOSED rather than left for a
reader to infer from an empty result: `v6_policy.simulation_runner_notices`
emits `SIMULATION_RUNNER_UNAVAILABLE`. That notice is gated on the channel
being on, which is the seam in one line: a channel that is off has no road to
sever, so it earns no severed-road notice.

`check: python3 -c 'import deepreason.sandbox_os as so;so.network_denial_available=lambda:False;from deepreason.v6_policy import simulation_runner_notices as N;from deepreason.config import Config;e={"DEEPREASON_SIMULATION_RUNNER":"contained"};assert [n.code for n in N(e,config=Config())]==["SIMULATION_RUNNER_UNAVAILABLE"];assert [n.code for n in N(e,config=Config(CHANNELS_DISABLED=("simulation",)))]==[]'`

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| whether a channel is on by default, or add a channel | `CHANNEL_DECLARATIONS` in `channels.py` — a row, never a new knob | `tests/test_evidence_channels.py` |
| what OFF compiles to for a capability | `engaged_research_policy` / `engaged_simulation_policy` in `v6_policy.py` | `tests/test_evidence_channels.py -k compiles` |
| which runner a simulation policy binds, and its toolchain | `engaged_simulation_policy` — the profile and the identity move together or the road severs | `tests/test_simulation_runner_default.py::test_the_toolchain_always_pairs_with_the_runner_profile` |
| what a configuration DISCLOSES about a severed road | `simulation_runner_notices` in `v6_policy.py` | `tests/test_simulation_runner_default.py::test_an_unequipped_host_compiles_and_discloses_the_severed_road` |
| the typed reason a disabled channel denies with | the reason ladders in `capabilities/research.py` / `capabilities/simulation.py` | `tests/test_evidence_channels.py` |
| the shape of a capability policy | `capabilities/policy.py` — a manifest surface, so `DR-INV-frozen-surfaces` (surface 4) and the ~14-minute requalification cost apply | `tests/test_run_manifest_v5_inquiry.py` |

**The frozen surface near this seam.** Neither `channels.py` nor
`capabilities/` is frozen. The thing the seam hands across is: the compiled
`inquiry_capability_policy` is manifest data, and `run_manifest.py` is frozen
surface 4. Changing HOW a channel reaches a capability is ordinary work;
changing WHAT SHAPE the policy has is a frozen-surface change and moves every
qualification subject digest.

## Traps

- **The flag said ON for two days while the road was severed, and four live
  epochs were read as model reluctance.** `engaged_simulation_policy` returned
  `runner_profile="simulation.declarative.v1"` while binding
  `PUBLIC_SIMULATION_TOOLCHAIN_ID`, a Python toolchain the declarative profile
  can never dispatch to, so every `sandboxed_python_v1` proposal died
  `runner_profile_mismatch` after passing every channel check. The registry was
  ACCURATE the whole time; accuracy about the FLAG is not accuracy about the
  ROAD. Census and citations:
  `experiments/2026-08-27-change-execution-safety/SPEC.md` F2 and F3 (F3 states
  plainly that `DR-INV-evidence-channels` "is accurate and was never the
  problem"). **FIXED 2026-08-28** by flipping the default runner to
  `contained`, which pairs the profile with its own toolchain; the entry stays
  because a Trap is never deleted. The reverse of the same trap was caught in
  the same change and is recorded in `capabilities/simulation.py`: binding the
  declarative program to the declarative profile alone would have denied every
  `declarative_numeric_v1` proposal after the flip — "the exact defect this
  tranche exists to remove, pointed the other way."
`check: python3 -c 'import inspect,pathlib;s=pathlib.Path("src/deepreason/capabilities/simulation.py").read_text();assert "runner_profile_mismatch" in s and "2026-08-28 default flip" in s;from deepreason.capabilities.simulation import SimulationCapabilityController as C;e=inspect.getsource(C.execute);assert "simulation.container.v1" in e and "runner_profile_mismatch" in e'`

- **The live record of that trap is cited at SECOND HAND.** Both
  `DR-INV-evidence-channels` and the execution-safety tranche's PARKED.md P3
  name commit `74d9f71ca` on branch `claude/spec-to-code-technique-k5209o` as
  where the four epochs were recorded. That commit is not reachable from the
  main line (`git cat-file -t 74d9f71ca` → `Not a valid object name`), so no
  reader can open the root behind the claim. Treat the four-epoch figure as
  reported by those two documents, not as re-derivable here. Recorded at
  `experiments/2026-08-29-change-seam-capabilities-x-channels/REQUEST.md`.

- **The manifest Config echo silently reverts switches, and this seam survives
  it only because the capability side reads no Config.** Audit finding F-A
  (`experiments/2026-08-28-audit-run-problems/AUDIT_REPORT.md`) measured five
  switches — `JUDGE_SEATS_ENABLED`, `ADJUDICATION_STATUS_AUTHORITY_ENABLED`,
  `ENGAGED_CRITICISM_AUTHORITY`, `LEGACY_CRITICISM_ENABLED`,
  `SCHOOL_SEATS_ENABLED` — configured ON and effective OFF on a
  `--run-manifest` launch, with `compile_notices: []`. `CHANNELS_DISABLED` is
  popped from the SAME echo by the SAME function. It is not reverted because
  its effect was frozen into the manifest policy before the echo was written.
  Anyone adding a `Config` read to a controller removes that protection
  silently; the first check in this document is the tripwire.

- **A disabled channel is not a missing channel.** `enabled()` returns False
  for an id that is merely unknown, and for the DECOMMISSIONED `website`, with
  the same False a deliberate disable produces. The distinction is carried by
  `unknown_channel_notices` — which never reaches this side of the seam. So a
  capability controller cannot tell "the operator turned this off" from "the
  operator typed it wrong": both arrive as the all-zero policy. Read the
  compile notices, not the policy, to learn which happened.

- **`Seams:` on both sides must keep naming this document.** The pair was
  listed as `Seams-undocumented: capabilities x channels` on the channels side
  and carried a body-table row with no header entry on the capabilities side —
  a real analysis with no file behind it, which is what `SCHEMA.md` designed
  `Seams-undocumented:` to record honestly.
`check: python3 -c 'import pathlib,re;m=pathlib.Path("docs/map");assert (m/"SEAM-capabilities-x-channels.md").exists();h=lambda f,k:(re.search("^"+k+": (.*)$",(m/f).read_text(),re.M) or type("x",(),{"group":lambda s,i:""})()).group(1);assert "DR-SEAM-capabilities-x-channels" in h("SUB-capabilities.md","Seams"),h("SUB-capabilities.md","Seams");assert "DR-SEAM-capabilities-x-channels" in h("INV-evidence-channels.md","Seams");assert "capabilities x channels" not in h("INV-evidence-channels.md","Seams-undocumented")'`
