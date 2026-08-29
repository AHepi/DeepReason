<!-- DR-SEAM-capabilities-x-channels -->
Verified-at: 56d4df1e7
Verify: python -m pytest tests/test_evidence_channels.py tests/test_simulation_runner_default.py tests/test_channel_and_wander_modularity.py -q
Owns:
Sides: DR-SUB-capabilities, DR-INV-evidence-channels
Seams:
Seams-undocumented:

# capabilities x channels — the flag is compiled; the road is dispatched

## What this seam is

`DR-INV-evidence-channels` decides WHETHER a run may reach outside itself.
`DR-SUB-capabilities` owns the typed lifecycle that does the reaching. Between
them there is **no import in either direction**: nothing under
`capabilities/` names `deepreason.channels`, and `channels.py` names nothing
under `deepreason.capabilities`. Measured coupling is 0 both ways.

The same check pins a second, stronger absence that is the whole reason this
seam is safe: **`capabilities/` imports `deepreason.config` nowhere either.**
The capability side never reads a run's configuration: it obeys one frozen
policy object, lifted off the manifest. That is this seam's load-bearing
property — but this check pins the ARROWS, not the property. What it does and
does not catch, measured by mutation, is stated under "Why the compile-time
freeze is the load-bearing part"; read that before relying on it as a tripwire.

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

Of `channels.py`'s public surface only `enabled()` is consulted here — and
`enabled()` is the only one consulted ANYWHERE under `src/`.
`disabled_channels()` and `unknown_channel_notices()` have NO PRODUCTION CALLER.
Outside `channels.py` itself the two names appear once as a docstring mention in
`v6_policy.py` and otherwise only in `tests/test_evidence_channels.py` and
`tests/test_channel_and_wander_modularity.py`. The first draft of this document
said they "serve reporting and compile notices"; that was false and is corrected
here, ledgered at
`experiments/2026-08-29-change-seam-capabilities-x-channels/RESULTS.md`. The
half this seam turns on survives the correction — they never reach a capability
— and the fourth Trap below, which had been resting on the false half, is
rewritten with it.

`check: python3 -c 'import pathlib,re;R=pathlib.Path("src/deepreason");d=(R/"channels.py").read_text();assert "def disabled_channels" in d and "def unknown_channel_notices" in d and "def enabled" in d;C=re.compile(r"(disabled_channels|unknown_channel_notices)\s*\(");callers=sorted(str(p.relative_to(R)) for p in R.rglob("*.py") if "__pycache__" not in str(p) and p.name!="channels.py" and C.search(p.read_text()));assert callers==[],callers'`

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

**The SILENCE is over; the DROP is not.** F-A's `compile_notices: []` was fixed
on 2026-08-28 by `a40450f1c` (audit finding P10), which is in the tree this
document describes: a compile now emits a typed `ENGINE_CONFIG_FIELD_NOT_CARRIED`
notice for every configured field the echo does not carry, and
`CHANNELS_DISABLED` is one of them. So a channels-off `--run-manifest` launch is
now DISCLOSED — the operator law it answers is "Gates are always optional: with
warnings" (2026-08-28). The notice is CONSERVATIVE here: it reports the drop
without knowing that this field's decision was compiled elsewhere, and it
carries no resolution pointer, because `CHANNELS_DISABLED` is absent from
`run_manifest.py::_DROPPED_FIELD_CARRIERS`. A reader is told the field was
dropped, not that the decision survived. The survival is what the differential
below measures. (If a later tranche registers a carrier for this field, the
check on the next line goes red and this paragraph gets rewritten — which is
the intended behaviour, not a defect in the check.)

`check: python3 -c 'import sys;sys.path.insert(0,".");from tests.test_v6_engaged_public_defaults import STAMP,_profile;from deepreason.preparation import build_preparation_manifest as B;P=lambda cd:[(n.code,n.resolution) for n in (B(_profile(),question="q",compiled_at=STAMP,channels_disabled=cd).compile_notices or ()) if n.pointer=="/engine_config/CHANNELS_DISABLED"];assert P(("research",))==[("ENGINE_CONFIG_FIELD_NOT_CARRIED",None)],P(("research",));assert P(())==[],P(());assert B(_profile(),question="q",compiled_at=STAMP,channels_disabled=("research",)).inquiry_capability_policy.research.enabled is False'`

**It cannot do that here, and the reason is structural rather than lucky.**
The channel decision never travels in the echo; it travels as the compiled
policy, which the manifest carries and which the controllers read directly.

**Updated 2026-08-29 (P15 carriage).** Until carriage, this differential also
showed the rebuilt `Config` having LOST the toggle, and that loss was the
point: the decision survived only in the policy. Carriage restores the toggle
too — the notice that disclosed the drop now carries the value — so the two
halves no longer disagree. The immunity claim is UNCHANGED and is what the
check still pins: the compiled policy carries the decision whether or not the
`Config` does, so a controller reading the policy is right either way. What is
gone is the asymmetry, not the immunity.

`check: python3 -c 'import sys,json;sys.path.insert(0,".");from tests.test_v6_engaged_public_defaults import STAMP,_profile;from deepreason.preparation import build_preparation_manifest as B;from deepreason.run_manifest import config_from_run_manifest as C;m=B(_profile(),question="q",compiled_at=STAMP,channels_disabled=("research",));assert m.inquiry_capability_policy.research.enabled is False;assert m.inquiry_capability_policy.simulation.enabled is True;assert "CHANNELS_DISABLED" not in json.loads(m.engine_config_json);assert C(m).CHANNELS_DISABLED==("research",),C(m).CHANNELS_DISABLED'`

**The consequence for anyone changing this seam:** the immunity is bought by
the capability side reading no configuration. A change that gave a controller a
`Config` — to add one convenience knob, say — would reopen F-A's failure mode
on the channels.

Two checks guard that, and they guard DIFFERENT HALVES; an earlier draft of this
document claimed the first guarded both, and adversarial mutation falsified it.

- The IMPORT check at the top of this document pins the ARROWS. A controller
  that names `deepreason.config` or `deepreason.channels` directly turns it red
  (measured: adding `from deepreason.config import Config` to
  `capabilities/simulation.py` reddens it and nothing else).
- It does NOT catch an INDIRECT read. A controller that imports
  `deepreason.v6_policy` and recompiles its own policy from the ambient
  environment draws no arrow this document forbids: measured, that mutation left
  ALL of this document's checks green while the compiled manifest said
  `research.enabled=False` and the controller said `True` with a budget of 6 —
  F-A's failure mode, reopened, invisible. The check on the next line closes it
  by demanding the policy a controller obeys BE the manifest's own compiled
  object rather than an equal one, so any recompilation route reddens it
  whatever it imports.

`check: python3 -c 'import sys;sys.path.insert(0,".");from tests.test_v6_engaged_public_defaults import STAMP,_profile;from deepreason.preparation import build_preparation_manifest as B;from deepreason.capabilities.research import ResearchCapabilityController as R;from deepreason.capabilities.simulation import SimulationCapabilityController as S;m=B(_profile(),question="q",compiled_at=STAMP,channels_disabled=("research","simulation"));t=m.inquiry_capability_policy;r=R(None,m);s=S(None,m);assert r.policy is t.research,"research policy is not the manifest object";assert s.policy is t.simulation,"simulation policy is not the manifest object";assert not r.policy.enabled and not s.policy.enabled;assert r.policy.maximum_requests==0 and r.policy.domain_allowlist==()'`

Neither check makes the capability side INCAPABLE of obtaining a `Config`.
`capabilities/audit.py` already imports `deepreason.run_manifest`, which exports
`config_from_run_manifest`; a read through an already-permitted module would
pass both checks. The behavioural authority for that case is the capability test
suite, not this document — under the indirect-read mutation above,
`tests/test_research_capability.py` returns `7 failed, 4 passed`. State the
division plainly rather than let a map check stand in for a gate.

## Completeness: why `--coverage` is silent here, and what stands in for it

`SCHEMA.md` has a seam document declare a `Sweep:` header so
`docs_verify --coverage` can flag enforcing sites the prose forgot. This
document HAD one. It is REMOVED, because it could not fail.

`--coverage` calls a file an enforcement site only if it COMPARES on the field
(`field ==`, `!= field`) or RAISES on it. The channel decision is never compared
and never raised on: every consumption site is a boolean guard —
`if not _channel_enabled("research", config)` in `v6_policy.py`. Recomputed by
hand on this tree, the removed header's own regexes matched three candidate
files (`preparation.py`, `run_manifest.py`, `v6_policy.py`) and ZERO enforcement
sites. With zero enforcement sites the sweep cannot produce a finding for this
seam whatever the document says, so its reported zero was not evidence — it was
a number that could not have come out any other way. `SCHEMA.md` records the
neighbouring case (`SEAM-evaluation-x-ontology`, where every candidate flags only
readers) and prescribes the same remedy: leave the header off and say why in the
body. If the channel decision ever becomes a comparison or a raise, the header
comes back.

What stands in for it is a census that CAN come out differently: EXACTLY ONE
module under `src/deepreason` reaches the channel registry at all, and this
document names it. A second reader — plain, aliased or relative — reddens it.

`check: python3 -c 'import ast,pathlib;R=pathlib.Path("src/deepreason");N=lambda p:(lambda t:{a.name for n in ast.walk(t) if isinstance(n,ast.Import) for a in n.names}|{b+s for n in ast.walk(t) if isinstance(n,ast.ImportFrom) for b in [((("deepreason."+".".join(str(p.relative_to(R)).split("/")[:-n.level])).rstrip(".")+("."+n.module if n.module else "")) if n.level else (n.module or ""))] for s in [""]+["."+a.name for a in n.names]})(ast.parse(p.read_text()));readers=sorted(str(p.relative_to(R)) for p in R.rglob("*.py") if "__pycache__" not in str(p) and any(m.startswith("deepreason.channels") for m in N(p)));assert readers==["v6_policy.py"],readers'`

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
  **The check below was strengthened after adversarial mutation.** As first
  written it asserted only that two STRINGS appeared in `execute`, and
  `SCHEMA.md`'s check-writing rule 2 says exactly why that is not enough:
  deleting the guard reddened it, but INVERTING the guard —
  `!= "simulation.container.v1"` mutated to `!= "simulation.declarative.v1"`,
  which is this very trap pointed the other way and would deny every
  `sandboxed_python_v1` proposal under the default profile — left every check in
  this document green, because both strings survive elsewhere in `execute`. It
  now pins the guard's AST: the two comparisons, their operators, their literals
  and the reason code they set, together. Measured RED under the inversion, RED
  under deletion, GREEN restored. The behavioural authority remains the ring in
  this document's `Verify:` header —
  `tests/test_simulation_runner_default.py::test_the_default_policy_admits_dispatches_and_executes_end_to_end`
  fails under the inversion.
`check: python3 -c 'import ast,inspect,textwrap,pathlib;s=pathlib.Path("src/deepreason/capabilities/simulation.py").read_text();assert "runner_profile_mismatch" in s and "2026-08-28 default flip" in s;from deepreason.capabilities.simulation import SimulationCapabilityController as C;t=ast.parse(textwrap.dedent(inspect.getsource(C.execute)));L=lambda c:[x.value for x in c.comparators if isinstance(x,ast.Constant)];g=[n for n in ast.walk(t) if isinstance(n,ast.If) and isinstance(n.test,ast.BoolOp) and isinstance(n.test.op,ast.And) and all(isinstance(c,ast.Compare) for c in n.test.values) and [type(c.ops[0]).__name__ for c in n.test.values]==["Eq","NotEq"] and [v for c in n.test.values for v in L(c)]==["sandboxed_python_v1","simulation.container.v1"] and "runner_profile_mismatch" in ast.dump(n)];assert len(g)==1,len(g)'`

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
  **The `compile_notices: []` half was FIXED 2026-08-28** (`a40450f1c`, audit
  finding P10): the drop of `CHANNELS_DISABLED` is now typed and disclosed as
  `ENGINE_CONFIG_FIELD_NOT_CARRIED` at `/engine_config/CHANNELS_DISABLED`. The
  entry stays because a Trap is never deleted, and because the DROP itself is
  unchanged — only the silence went. Anyone adding a `Config` read to a
  controller still removes the protection; the tripwire is the identity check in
  "Why the compile-time freeze is the load-bearing part", NOT the import check
  at the top of this document — see that section for which mutation each one
  actually catches.

- **A disabled channel is not a missing channel — and NOTHING TYPES THE
  DIFFERENCE INTO A COMPILED MANIFEST.** `enabled()` returns False for an id
  that is merely unknown, and for the DECOMMISSIONED `website`, with the same
  False a deliberate disable produces. `channels.unknown_channel_notices` can
  type the distinction as `CHANNEL_UNKNOWN` — and has no production caller, so
  it never runs outside the tests. Measured: `channels_disabled=("reserch",)`
  compiles a manifest whose ONLY notice is the P10
  `ENGINE_CONFIG_FIELD_NOT_CARRIED` above, with research still ENABLED. An
  earlier draft of this entry told the reader to "read the compile notices, not
  the policy, to learn which happened"; that advice was FALSE and is withdrawn.
  What a reader can actually do is read the VALUE the P10 notice quotes back
  (`CHANNELS_DISABLED=['reserch']`) and compare it against
  `channels.CHANNEL_DECLARATIONS` themselves — the typed answer exists in the
  registry and is simply not wired into the compile. Wiring it in is a change
  for `DR-INV-evidence-channels`, whose module owns the function; when it lands,
  the check below goes red and this entry gets rewritten.
`check: python3 -c 'import sys;sys.path.insert(0,".");from tests.test_v6_engaged_public_defaults import STAMP,_profile;from deepreason.preparation import build_preparation_manifest as B;from deepreason import channels;from deepreason.config import Config;assert [n.code for n in channels.unknown_channel_notices(Config(CHANNELS_DISABLED=("reserch",)))]==["CHANNEL_UNKNOWN"];m=B(_profile(),question="q",compiled_at=STAMP,channels_disabled=("reserch",));assert [n.code for n in (m.compile_notices or ())]==["ENGINE_CONFIG_FIELD_NOT_CARRIED"],[n.code for n in (m.compile_notices or ())];assert m.inquiry_capability_policy.research.enabled is True'`

- **`Seams:` on both sides must keep naming this document.** The pair was
  listed as `Seams-undocumented: capabilities x channels` on the channels side
  and carried a body-table row with no header entry on the capabilities side —
  a real analysis with no file behind it, which is what `SCHEMA.md` designed
  `Seams-undocumented:` to record honestly.
`check: python3 -c 'import pathlib,re;m=pathlib.Path("docs/map");assert (m/"SEAM-capabilities-x-channels.md").exists();h=lambda f,k:(re.search("^"+k+": (.*)$",(m/f).read_text(),re.M) or type("x",(),{"group":lambda s,i:""})()).group(1);assert "DR-SEAM-capabilities-x-channels" in h("SUB-capabilities.md","Seams"),h("SUB-capabilities.md","Seams");assert "DR-SEAM-capabilities-x-channels" in h("INV-evidence-channels.md","Seams");assert "capabilities x channels" not in h("INV-evidence-channels.md","Seams-undocumented")'`
