# Spec for: the discharge-required criticism channel (REBUILD tranche F1)

Traces: every item cites R/C numbers from REQUEST.md. Untraceable items are bugs.
REQUEST.md re-read in full, including Amendment 1, before this was written.

**STOP RESOLVED — GRANTED 2026-08-26.** `tools/blast_radius.py` returned
`"frozen_surface_verdict": "CONTACT"` (pasted verbatim below), the tranche
stopped at this phase, and the operator's words arrived
(REQUEST.md Amendment 2, R16-R20, verbatim). All three batched questions are
answered: Q-OP-1 **GRANTED 2026-08-26** with four riders (S13 below);
Q-OP-2 resolved — C6 reads as "F2's fields", F1 proceeds (S14); Q-OP-3
resolved — one tranche, three commits, ~640 `src/` lines accepted, with a
typed STOP required if the ceiling grows (S15). `dr-plan-steps` may now run.

**Size disclosure (C7), stated rather than stopped on.** This document was 701
lines when the operator answered; recording Amendment 2 took it to 837. All 136
added lines are the grant and its four riders (S13), the C6 disposition and the
F2 composition note the operator asked be recorded (S14, R18), the ceiling
discipline (S15) and the fixed claim boundary (S16) — i.e. answers to
requirements the operator added, which they instructed SPEC.md to answer
explicitly. Nothing designed grew: the `src/` ceiling is unchanged at 640 and
S15 makes any growth in it a typed STOP. Disclosed here because C7 asks to be
told what grew, and stopping to ask permission to record a grant just given
would be theatre.

---

## The design in one paragraph

A new package `src/deepreason/discharge/` owns the whole channel behind ONE
declared interface (`deepreason.discharge.__init__`). It reads the record for
open criticisms on a problem, renders them into the conjecturer's binding block
(C1/R1), screens the submission for typed discharges (C2/R3), re-asks once and
then discloses (R4), and records each discharge as a Measure (never a warrant,
never a label — R5). Kinds and behavior live in a VERSIONED registry selected by
ONE new `Config` field (R12/R13); consumers (`rules/conj.py`, `llm/packs.py`,
`llm/wire.py`) know the interface and nothing else, pinned by an architecture
test that goes RED when a fourth kind cannot be added by declaration alone
(R14). The channel is OFF by default, so a channel-off run's wire bytes, pack
bytes and labels are byte-identical to today's.

The three layers, in `INV-signal-contract`'s own vocabulary (R14):

| Layer | Holds | Changing it takes |
|---|---|---|
| FROZEN | the interface itself: what `deepreason.discharge` exports and the law that a discharge never reaches a label, a warrant, or adjudication | an operator design law |
| VERSIONED | `DISCHARGE_KIND_DECLARATIONS` and `DISCHARGE_POLICY_PRESETS`, each a recorded artifact schema with a digest | a declaration + a recorded decision |
| FREE | which preset `Config.DISCHARGE_POLICY` names, and the caps inside a preset's envelope | ordinary configuration |

---

## Items

### S1 (R12, R13, R14, R15) — the declared interface and the versioned registry

Files: NEW `src/deepreason/discharge/__init__.py`, `policy.py`.

- before: no discharge machinery exists.
- after: `policy.py` declares `DischargeKindDeclaration(name, asserts, requires,
  directive_line, attackable)` and `DISCHARGE_KIND_DECLARATIONS: dict[str,
  DischargeKindDeclaration]` with exactly three entries — `revised`
  (`requires=("note","where")`), `rebutted` (`requires=("note",)`,
  `attackable=True`), `departure_declared` (`requires=("note",)`). `KINDS` is a
  DERIVED view, never a second hand-maintained copy (the `SIGNALS` /
  `SIGNAL_DECLARATIONS` pattern, `DR-INV-signal-contract`).
  `DischargePolicyV1` (schema string `discharge-policy.v1`) carries
  `policy_id`, `kinds: tuple[str, ...]`, `reask: Literal["once","never"]`,
  `disclose_undischarged: bool`, `handles_n: int`, `claim_head_chars: int`,
  `span_head_chars: int`, and a content-addressed `policy_digest()`.
  `DISCHARGE_POLICY_PRESETS` holds `"off"` (kinds=(), reask="never",
  disclose=False) and `"discharge-required.v1"` (all three kinds, reask="once",
  disclose=True, handles_n=8). `resolve_policy(config)` maps
  `Config.DISCHARGE_POLICY` to a preset and raises typed on an unknown id.
  `__init__.py` re-exports exactly: `resolve_policy`, `open_criticisms`,
  `render_open_criticism_context`, `screen_submission`, `record_discharges`,
  `discharge_kind_names`, `DischargePolicyV1`, `OpenCriticism`,
  `SubmissionScreening`.
- **R15 applied, in writing.** The tighter-and-smaller option (a module-level
  `_KINDS = ("revised", "rebutted", "departure_declared")` tuple read directly
  by `conj.py`, ~40 lines total) is REJECTED under R15: the operator has priced
  the fork and chosen the interface.

  accept: `python -c "from deepreason.discharge import resolve_policy,
  discharge_kind_names; from deepreason.discharge.policy import
  DISCHARGE_KIND_DECLARATIONS, KINDS; assert KINDS == {n: d.asserts for n, d in
  DISCHARGE_KIND_DECLARATIONS.items()}; assert
  set(discharge_kind_names()) == {'revised','rebutted','departure_declared'}"`
  → exit 0.

### S2 (R1, R2, C1) — open criticisms, read from the record

Files: NEW `src/deepreason/discharge/channel.py`.

- before: an `observe_only` criticism registers a critic-role artifact plus a
  `["scrutiny", target, critic]` Measure (`rules/crit.py::_observe_case`), and
  nothing that makes the next candidate ever reads it. W2 measured the
  consequence: **0 of 196 LLM attacks exposed to a later conjecture dispatch**
  (`experiments/2026-08-26-run-anatomy-w2-criticism/RESULTS.md` §3a).
- after: `open_criticisms(harness, problem_id, policy)` returns
  `tuple[OpenCriticism, ...]`, sorted by handle, capped at `policy.handles_n`
  with the cap stated in-band. A criticism is IN the population when BOTH
  channels are read — the `["scrutiny", target, critic]` Measures AND
  `state.att` attack edges — for every target `t` with `(t, problem_id) in
  state.addr`. It LEAVES the population when either (a) a discharge record
  names its handle, or (b) the criticism artifact's own `Status` is `REFUTED`
  (the `test_a_defeated_attacker_stops_occupying_a_crisis_slot` rule: a
  defeated attack is not an open indictment).
- `OpenCriticism` carries `handle`, `claim`, `span`, `target`, `source`
  (`"scrutiny"` or `"attack"`).
- **The handle is the critic artifact id** (A3 below). Stable by
  content-addressing, unique by construction, re-derivable on replay, and no
  handle map to reload — which is what keeps CLAUDE.md's recorded key-sort trap
  ("B1, B10, B2") out of this channel entirely.

  accept: `python -m pytest tests/test_discharge_channel.py -q -k
  "open_criticisms"` → passed; includes a case where an `observe_only`
  criticism with no warrant IS in the population (the W2 population) and one
  where a REFUTED critic artifact is NOT.

### S3 (R1, R2) — the render, INSIDE the binding block

Files: `src/deepreason/discharge/channel.py`, `src/deepreason/llm/packs.py`,
`src/deepreason/rules/conj.py`.

- before: `render_conj_pack` has sections `problem`(1), `criteria`(2),
  `mandatory-interface`(3) … `neighbourhood`(8) … `output-contract`(12).
  Criticism appears in NO conjecturer section.
- after: `render_open_criticism_context(harness, problem_id, policy)` →
  `str | None` (None, never an empty string or a "no criticisms" notice — the
  `RESEARCH_JUDGE_BLINDING` empty-slot rule Rung 6 already obeys). Threaded into
  `render_conj_pack(..., open_criticism_context=...)` from `rules/conj.py`
  beside the two frame values, and rendered as section id `open-criticisms` at
  **priority 2**, `droppable=False`, `compressible=False`.
  Priority 2 with `criteria` is the whole of "INSIDE the conjecturer's working
  section (not a sidebar section)": `allocate_pack` admits in `(priority, id)`
  order, `"criteria" < "open-criticisms"`, so the criticisms render in the
  block that states what the candidate is BOUND BY, above
  `mandatory-interface`(3) and far above the advisory sections
  (`scratch-advisory-context`(7), `neighbourhood`(8)). Non-droppable and
  non-compressible for Rung 6's own measured reason: a dropped section leaves
  no header, and a compressible one lost its middle at a tight budget.
  Bounded by construction via `policy.handles_n` / `claim_head_chars` /
  `span_head_chars`, so EXACT is affordable.
- The `output-contract` section (12) additionally carries the discharge
  precondition sentence when the channel renders anything — this is what makes
  it a submission precondition rather than advice.
- **R2's persistence rule needs no new mechanism**: `open_criticisms`
  re-derives from the record on every render, so a handle renders every cycle
  until discharged. It is asserted AT THE TERMINAL step, never at injection,
  exactly as `test_a_standing_attacker_at_cycle_k_still_renders_at_the_terminal_cycle`
  does — eight cycles of accumulating ACCEPTED state, criticism injected at
  cycle 2, the claim made at cycle 8 under a budget measured to bite.

  accept: `python -m pytest tests/test_discharge_channel.py -q -k
  "renders_in_the_binding_block or terminal_cycle or absent_renders_nothing"` →
  passed.

### S4 (R3, C5, C6) — the typed discharge on the wire

Files: `src/deepreason/llm/wire.py`, `src/deepreason/workloads/text.py`.

- before: `CompactConjectureCandidate` and `ReasoningCandidateProposal` carry no
  discharge field; a criticism has no channel back from the writer at all.
- after: NEW `DischargeWireV1(StrictWireModel)` with `handle: str`,
  `kind: str`, `note: str = ""`, `where: str | None = None`. Its `kind` enum in
  the EMITTED JSON schema is derived from `DISCHARGE_KIND_DECLARATIONS` at
  contract-construction time, so a fourth kind reaches the model by declaration
  (R12). Two additive, optional fields:
  `CompactConjectureCandidate.discharges: list[DischargeWireV1] =
  Field(default_factory=list, max_length=32)` and
  `ReasoningCandidateProposal.discharges: tuple[DischargeWireV1, ...] = ()`.
  These two models are the whole surface: `CompactConjectureCandidate` is
  reused by `ConjecturerTurnWireV4/V5/V6` AND `AtomicConjectureCandidateWireV1`,
  and `ReasoningCandidateProposal` by the three reasoning twins.
  The field is PRUNED from the emitted schema (`wire.prune_property`, the
  mechanism `ConjecturerTurnWireContractV6._omit_property` already uses) when
  the policy renders no open criticisms — so a channel-off run's wire bytes are
  byte-identical to today's.
  **Pruning binds EVERY contract that embeds these two models, not only the v6
  turn.** `CompactConjectureCandidate` is also embedded by
  `ConjecturerWireContract` (the plain compact contract) and
  `AtomicConjectureWireContractV1`; a field added and not pruned there would
  grow a schema this tranche has no business changing. The census below records
  three committed tests that read that `$def` directly, which is what turns this
  from an optimisation into a requirement.
- **Additive-and-optional is this file's own recorded precedent**, not an
  invention: `ReasoningCandidateProposal.checker_specs` carries the comment
  "additive and optional so counterconditions' own wire TYPE never changes …
  the narrower alternative that doesn't [need a contract-version bump]".
- **C6 disposition, disclosed rather than assumed** — see Q-OP-2 below.

  accept: `python -m pytest tests/test_discharge_wire.py -q` → passed —
  including a case asserting `"discharges" not in
  ConjecturerWireContract().model_json_schema()["$defs"]
  ["CompactConjectureCandidate"]["properties"]` and the same for the atomic and
  v6-turn contracts when the channel is off; and a `python -c` asserting the
  subject digest is still
  `b9038b84efdea313c3f3f2a8862d8acf180d3938ab3d1bf3588c3585dfe07386` (M4).

### S5 (R3, R4) — discharge-required submission, re-ask once, then disclose

Files: NEW `src/deepreason/discharge/submission.py`;
`src/deepreason/rules/conj.py`.

- before: `conj()` parses `output`, builds `candidate_rows` → `prepared_rows`,
  gates each candidate through `anti_relapse.check`, and registers. Nothing
  consults criticism at any point.
- after: immediately after `output` is parsed and BEFORE `candidate_rows` is
  built, `conj()` calls
  `screen_submission(harness, problem_id, output, policy, reask_index=
  _discharge_reask_index)` → `SubmissionScreening(verdict, open_handles,
  undischarged, accepted)`.
  - `verdict == "reask"` (undischarged handles present AND
    `policy.reask == "once"` AND `_discharge_reask_index == 0`): record a typed
    Measure `["discharge-reask", problem_id, <handles joined>]`, then RE-ENTER
    `conj(..., _discharge_reask_index=1,
    _discharge_open_handles=screening.open_handles)` and return its result. The
    re-entered pack carries a `discharge-reask` section naming the open list
    verbatim. This is the established recursion shape in this file
    (`_context_expansion_index`, `conj.py:2897`), not a new control flow.
    **It is a re-ask, not a repair grant** (R4's own distinction): it consumes
    no repair budget, touches no `RepairPatchWireContract`, and passes through
    `workflow_repair_observer` not at all.
  - `verdict == "accept"`: for every (candidate, still-open handle) pair, record
    `["discharge-undischarged", problem_id, candidate_ref, handle]` — the typed
    undischarged disclosure. Registration then proceeds UNCHANGED. **Disclose,
    never die**: no candidate is ever refused for an undischarged handle (the
    all-configurations law at the submission boundary).
  - The ONCE is counted per conjecture DISPATCH (A4 below).
- **R11 is honoured structurally, not by wording.** There is no acknowledgment
  kind, no `acknowledged` field, and no path where merely noting a criticism
  discharges it: every kind in the registry requires substantive content
  (`requires` is non-empty for all three), and a test greps the whole package
  for acknowledgment-shaped names.

  accept: `python -m pytest tests/test_discharge_submission.py -q` → passed;
  includes a case proving the second submission is accepted WITH the disclosure
  Measure and NOT re-asked a second time.

### S6 (R3, R6) — discharge records, and the rebuttal in the ordinary graph

Files: `src/deepreason/discharge/submission.py`.

- before: nothing.
- after: `record_discharges(harness, problem_id, candidate_ref, discharges)`
  writes ONE Measure per accepted discharge:
  `["discharge:<kind>", handle, candidate_ref, problem_id]`. A Measure is the
  right vehicle for the same reason gate decisions and evidence-citation checks
  already use it: attention/diagnostic, never a status.
  For `kind == "rebutted"` ONLY, it ALSO registers the rebuttal note as an
  ordinary artifact with TWO `MENTION` refs (the criticism handle's artifact,
  and the candidate) and NO dependence and NO warrant — mirroring
  `calculus/operations.py::file_departure_declaration` exactly, including its
  idempotence-by-content-address and its refusal to judge the declaration:
  whether a rebuttal is earned is an ordinary question for criticism.
  That registration IS R6: "a REBUTTED discharge is just a criticism artifact
  entering the ordinary graph" — attackable like anything else, protected by
  nothing.
- Label-safety is structural: `build_att` lifts attackers through EVIDENCE
  refs, not MENTION refs, so no pre-existing node's attacker set changes.

  accept: `python -m pytest tests/test_discharge_submission.py -q -k
  "rebuttal_is_itself_attackable or rebuttal_moves_no_existing_label"` → passed.

### S7 (R5, R7, R8) — THE LAW LINE, stated and pinned

**The law line, stated here as R5 requires it be stated in SPEC:**

> Discharge constrains how content is GENERATED — it is a precondition on
> SUBMISSION, nothing more. It never constrains what counts as EVIDENCE. No
> discharge field, kind, count, or record may feed a label, a warrant, a rank,
> an admission decision, or any adjudication pass. A REBUTTED discharge enters
> the ordinary graph as an ordinary artifact and is judged there, by criticism,
> like anything else. Discharge kinds carry no rank and no admission weight:
> the registry declares no numeric field, and no configuration can give one.

This is the operator's standing seats guardrail ("seats change how content is
GENERATED, never what counts as EVIDENCE", CLAUDE.md) and the formalism-optional
law (R-g, `DR-CON-conjecture-kinds`) applied to this channel.

Files: NEW `tests/test_discharge_law_line.py`; `proof/` in this tranche.

- Pin 1 (absence, the shape `test_nothing_that_ranks_admits_or_accepts_reads_a_departure`
  uses): no file under `src/deepreason/scheduler/`,
  `src/deepreason/adjudication/`, `src/deepreason/informal/`, or
  `src/deepreason/rules/` EXCEPT `rules/conj.py` may contain any of
  `DischargeWireV1`, `discharge_kind`, `DISCHARGE_KIND_DECLARATIONS`,
  `discharge-policy.v1`, `screen_submission`, `open_criticisms`. Each negative
  grep is paired with a POSITIVE anchor on the same tree, so a moved directory
  fails the test rather than making it vacuous.
- Pin 2 (R8): `DischargeKindDeclaration` has no numeric field at all —
  asserted over `model_fields` — so there is no weight to give.
- Pin 3 (R8): admission is byte-identical with and without discharges.
  `anti_relapse.check` on the same candidate content returns the same
  `(admitted, reason)` whether the wire object carried three discharges or none.
- **Pin 4 (R7) — the mutation proof.** In a scratch copy OUTSIDE the repo
  (`$SCRATCH/mutation/`), wire a discharge into label computation in
  `adjudication/`, run `tests/test_discharge_law_line.py` against it, capture
  the RED output to `proof/c3_red.txt`, then restore and capture the GREEN to
  `proof/c3_green.txt`. Both outputs are committed. The proof is that the pin
  CAN fail — the standard `docs_verify --audit` applies to a check that has no
  auditor of its own (`INV-frozen-surfaces`, the Rung 7 cascade-integrity note).

  accept: `python -m pytest tests/test_discharge_law_line.py -q` → passed, and
  `proof/c3_red.txt` exists and contains a FAILED line naming that test file.

### S8 (R12, R13, R14) — the architecture test that can go RED

Files: NEW `tests/test_discharge_contract.py`.

Four failable checks; each is the modularity claim made checkable rather than
decorative:

1. **Interface-only consumption.** No file in `src/` outside
   `src/deepreason/discharge/` may import a discharge SUBMODULE
   (`from deepreason.discharge.policy import …`); only the package. Positive
   anchor: at least two files DO import the package.
2. **The package consumes nothing it must not.** `src/deepreason/discharge/`'s
   own `deepreason` imports are confined to `ontology`, `config`, `packs`
   and `programs` — no `adjudication`, no `scheduler`, no `informal`, no
   `rules`. (The `controller.py` boundary test in `test_signal_contract.py` is
   the model.)
3. **A fourth kind enters by declaration.** The test registers a synthetic kind
   `"scoped_out"` into `DISCHARGE_KIND_DECLARATIONS` (monkeypatched) and asserts
   it (a) appears in the emitted wire schema's `kind` enum, (b) is accepted by
   `screen_submission`, and (c) renders its directive line in the pack — with
   `rules/conj.py`, `llm/packs.py` and `llm/wire.py` UNEDITED. Companion:
   none of those three files contains the literal strings `"revised"`,
   `"rebutted"` or `"departure_declared"`.
4. **A policy change is pure configuration.** Flipping
   `Config.DISCHARGE_POLICY` from `"off"` to `"discharge-required.v1"` changes
   the rendered pack and the screening verdict with no code edit; and a caps
   change (`handles_n`) changes the render with no code edit.

  accept: `python -m pytest tests/test_discharge_contract.py -q` → passed.
  Failability is demonstrated in the same tranche: `proof/arch_red.txt` records
  check 3 going RED against a deliberately hard-coded kind tuple.

### S9 (R9) — the coupling instrument, channel on vs off

Files: NEW `experiments/2026-08-26-change-f1-discharge-criticism-channel/
coupling.py`, `coupling.json`.

- Builds TWO offline stub-driven run roots on the deterministic stub adapter,
  identical but for `Config.DISCHARGE_POLICY`. Each root: a problem carrying a
  machine-evaluable commitment; a first candidate that FAILS it; a mechanical
  criticism whose warrant names that failed commitment (the mechanical respect);
  then a further conjecture dispatch from a RESPONSIVE stub — one that satisfies
  whatever criticism its pack actually shows it, and can do nothing about
  criticism it is not shown.
- Then W2's **committed** `census.py` and `q5.py` are run UNMODIFIED over both
  roots (`experiments/2026-08-26-run-anatomy-w2-criticism/`), and R1_mechanical
  `coupling - placebo` is read from their output. If either instrument cannot
  run on a stub root for want of a record field the stub path does not write,
  that is recorded as a measured limit and `coupling.py` reproduces R1 directly
  from `q5.py`'s own definition (lines 20–24: coupled iff the next candidate
  PASSES the commitment the criticized one failed, re-evaluated by
  `deepreason.programs.evaluate` on the next candidate's own bytes), citing the
  lines it reproduces.
- **What this proves, stated honestly now so RESULTS.md cannot overclaim.** It
  proves THE CHANNEL DELIVERS: a writer that responds to what it is shown
  couples above placebo when the channel is on, and cannot couple above placebo
  when it is off, because the criticism never reaches it. It does NOT prove that
  a real provider model responds — that needs the live A/B W2 parked as **P2**,
  and Q1's finding (a pack's own claim to have honoured a standing instruction
  is worthless as evidence) says it must not be assumed.

  accept: `python coupling.py coupling.json` → exit 0, and the JSON carries
  `on.R1_mechanical.coupling_minus_placebo > 0` and
  `off.R1_mechanical.coupling_minus_placebo == 0`.

### S10 (R10) — no label differs, channel on vs off

Files: `tests/test_discharge_law_line.py`.

- The two S9 roots are replayed and final labels compared over the artifact set
  present in BOTH. Every shared artifact's `Status` must be identical. The
  channel-on root additionally carries rebuttal artifacts and discharge
  Measures; those are the DELTA and are listed, never hidden.

  accept: `python -m pytest tests/test_discharge_law_line.py -q -k
  "no_label_differs"` → passed.

### S11 (R10, C8) — the map moves in the same commits

Files: NEW `docs/map/CON-discharge-channel.md`; edits to
`docs/map/INDEX.md` (concept table + a `Traps`-bearing row),
`docs/map/CON-packs-and-token-economy.md` (the new non-droppable section and
what its absence would mean), `docs/map/CON-criticism-source.md` (where an open
criticism now goes), `docs/map/CON-conjecture-source.md` (the submission
precondition), `docs/map/INV-frozen-surfaces.md` (the granted contact, if
granted).

The map preflight found **no existing id for a discharge channel**; creating
`DR-CON-discharge-channel` is therefore part of this tranche
(`dr-drive-harness` §4 step 5). Every load-bearing claim carries a `check:`
that would FAIL if the behaviour regressed, written and RUN before it is
written down (`SCHEMA.md`).

  accept: `python tools/docs_verify.py` (FULL) → failures unchanged from base;
  `python tools/docs_verify.py --audit` → 0 refused checks among the new ones;
  `python tools/docs_verify.py --links` → every `DR-` reference resolves.

### S12 (R10) — the gate

  accept: `python -m pytest tests/ -q -n 4` → `0 failed`.
  `python scripts/wheel_smoke.py` and `python -u
  scripts/wheel_operational_smoke.py` → PASS with pins unchanged (no console
  entry point, MCP tool, or wheel-layout change is planned; both are run as
  proof rather than assurance).


### S13 (R16) — the granted contact, and its four riders

Files: `src/deepreason/config.py`, `src/deepreason/run_manifest.py`,
`docs/map/INV-frozen-surfaces.md`, this tranche's `proof/`.

**GRANTED 2026-08-26** (rider a, discharged by this line and by the Q-OP-1
block above). The grant covers exactly ONE insertion:
`data.pop("DISCHARGE_POLICY", None)` in
`run_manifest.py::_versioned_source_config_data`, joining the twelve unconditional
pops already there. No schema, no validator, no Pydantic model, no check name,
no record format.

- **Rider (b) — pasted proof.** `proof/digest_before.txt` and
  `proof/digest_after.txt` are committed, each the output of one command over
  the tree at that moment: `source_config_hash(Config(), schema_version=v)` for
  v1..v6 AND `qualification_subject_digest(_manifest(_profile()), _profile())`.
  The claim is BYTE-IDENTICAL across the pair — `b9038b84efdea313…` before and
  after, `2624603035bc335e…` for v3-v6, `6c2d01f6b8cbe65e…` for v1-v2. A green
  suite is not the acceptance check; the digest is.
- **Rider (c) — same commit.** `docs/map/INV-frozen-surfaces.md` gains the
  granted-contact block in the SAME commit as the `run_manifest.py` line, with
  its own `check:` that would fail if the pop were removed. Not a later
  "update docs" commit — that is the commit that gets dropped.
- **Rider (d) — every schema version.** The pop is UNCONDITIONAL, outside the
  `if schema_version < 3:` guard, exactly as `ENGAGED_CRITICISM_AUTHORITY` and
  the eleven after it are. The operator named that knob's trap as this grant's
  ancestor, and the trap is precisely the scoped-fix that reasoned "no pinned
  test exists above v3" and was refuted by two v5 goldens
  (`DR-INV-frozen-surfaces` Traps). Acceptance is measured per version, not
  argued: the digest table above is compared for ALL SIX.

  accept: `python -c "from deepreason.config import Config; from
  deepreason.run_manifest import source_config_hash;
  h=[source_config_hash(Config(), schema_version=v) for v in (1,2,3,4,5,6)];
  assert h[0]==h[1]=='6c2d01f6b8cbe65e2a26bb57e864a80feec07b0896142fb2267bc83d2717dc81';
  assert h[2]==h[3]==h[4]==h[5]=='2624603035bc335e59da63f25426d3ae6619bf7f84d48657e8f25310de49edc5'"`
  → exit 0; and `test "$(grep -c 'data.pop(\"DISCHARGE_POLICY\", None)'
  src/deepreason/run_manifest.py)" -eq 1` with the line outside every
  `schema_version` guard; and `python tools/docs_verify.py` passing the new
  `INV-frozen-surfaces` check.

### S14 (R17, R18) — the C6 disposition and the F2 composition note

Files: this document; `docs/map/CON-discharge-channel.md`.

**C6 is resolved (R17):** it reads as "F2's field definitions". F1 edits none
of them; it adds two optional fields of its own, in a different region of
`wire.py`, measured digest-byte-identical (M4) and pruned from the emitted
schema when the channel is off (S4). Recorded here so the disposition is in
the ledger rather than in a chat reply.

**The composition note (R18), recorded for F2's window or a successor:**

> `DischargeWireV1.handle` is a REFERENCE-BEARING field. Its legal set is not
> free text: it is exactly `deepreason.discharge.open_criticisms(harness,
> problem_id, policy)`, in that call's own order, capped at
> `policy.handles_n` — ONE authority, computed from the record, already the
> single source the pack section renders from. F1 deliberately leaves `handle`
> as a plain `str` on the wire rather than inventing a private enum or menu,
> so that F2's menu renderer can key on this field by REGISTERING against that
> one-authority legal set, without F2 touching `discharge/` and without F1
> touching F2's renderer. If F2 lands first, F1's field registers into it; if
> F1 lands first, F2 finds a field already shaped for it. That is the
> modularity law doing the work it was stated to do — neither side had to
> learn about the other's subsystem.

  accept: `grep -q "reference-bearing" docs/map/CON-discharge-channel.md &&
  grep -q "open_criticisms" docs/map/CON-discharge-channel.md` → exit 0; and
  `python -c "from deepreason.llm.wire import DischargeWireV1; import typing;
  assert DischargeWireV1.model_fields['handle'].annotation is str"` → exit 0
  (the field stays a plain string; a private enum here would close the seam
  F2 needs).

### S15 (R19) — the ceiling, and the typed STOP if it moves

Files: none (a process obligation on `dr-execute-step`).

The `src/` ceiling declared in Budget below is **640**. `dr-execute-step` runs
`python tools/diff_budget.py <base> --paths src/ --ceiling 640` at every
`[COMMIT]` step and records `DIFF_BUDGET_RESULT_V1` verbatim in
CHECKLIST.md. An `EXCEEDED` verdict is a **typed STOP** presented to the
operator with what grew and why — never a silent overrun and never a
re-baselined ceiling. The operator's words: "a typed STOP if it grows beyond
what SPEC now declares, not silent growth."

This is Rung S5's recorded scar applied in advance: its own SPEC headline
(220–300) contradicted its own itemization (~325–435), and nothing checked the
ceiling against the ACTUAL diff until an executor noticed by hand.

  accept: every `[COMMIT]` step in CHECKLIST.md pastes a
  `DIFF_BUDGET_RESULT_V1` line; the final one carries `"verdict": "WITHIN"`
  against `640`, or an EXCEEDED that was stopped on and ruled.

### S16 (R20) — what RESULTS.md may claim, fixed now rather than at write-up

Files: this tranche's `RESULTS.md` (written at delivery).

The operator accepted the honesty paragraph AS SCOPED, so the claim boundary is
fixed here, before the evidence exists, where it cannot be widened to fit a
pleasing number:

- **F1 claims DELIVERY, not RESPONSE.** The offline gate proves the channel
  CARRIES criticism into the writer's working context and that the off-state
  CANNOT — a responsive writer couples above placebo iff the channel is on.
- **It does not claim a live provider model responds.** That is P2's question,
  and Q1's finding forbids assuming it: a pack's own claim to have honoured a
  standing instruction is the least reliable artifact in the trajectory.
- **The parked four-arm A/B remains the live proof** (PARKED.md P2, designed as
  Q5's four arms including vacuous-critique).
- Operator clarification, recorded verbatim so it is not mistaken for silence:
  "The upcoming P-C2 rematch will bear on it but does not replace P2's design."

  accept: `RESULTS.md` contains a "What this does NOT establish" section
  carrying all four points, and contains no sentence asserting that a live
  model responded to the channel.


---

## Assumptions (operator may override)

A1 (Q1): "INSIDE the conjecturer's working section (not a sidebar section)" is
implemented as section id `open-criticisms` at **priority 2**, sorting
immediately after `criteria` and above `mandatory-interface` — the block that
states what a candidate is bound by — with `droppable=False,
compressible=False`, plus the discharge precondition on the `output-contract`
section. Assumed, operator may override. Smallest reading that is structural
rather than a wording choice: it is decided by `allocate_pack`'s
`(priority, id)` order, not by a sentence a model may ignore.

A2 (Q2): a criticism is "open" if it appears in EITHER channel — an
`observe_only` `["scrutiny", target, critic]` Measure or a `state.att` attack
edge — against a target addressed to the problem, and is neither discharged nor
itself REFUTED. Assumed, operator may override. Including the `observe_only`
population is not a widening: it is the exact population W2 measured as never
routed anywhere (0 of 196), so excluding it would leave the tranche's own
motivating defect in place.

A3 (Q3): the stable discharge handle IS the critic artifact id. Assumed,
operator may override. It is stable by content-addressing, unique by
construction, re-derivable on replay, and needs no handle map — which keeps
CLAUDE.md's recorded key-sort trap out of the channel. A short ordinal (`K1`,
`K2`) was rejected: it renumbers when a lower-sorting criticism arrives, which
is exactly the instability R1 forbids.

A4 (Q4): the ONCE in R4 is counted per conjecture DISPATCH — one re-ask per
`conj()` entry, tracked by `_discharge_reask_index`, the same shape
`_context_expansion_index` already uses. Assumed, operator may override.
Smallest reading: it makes the bound local and replay-visible rather than
requiring a per-problem counter in state.

A5 (Q6): the terminal assertion for a handle is the Rung 6 assertion applied to
this section — a criticism injected at cycle 2 still renders in the PACK at
cycle 8, under a budget measured to bite, with the neighbourhood already
dropped. Assumed, operator may override.

A6 (Q7): "coupling must be measurably nonzero" is read on **R1_mechanical's
placebo-corrected value**, and R2_prose-quote is not quoted as a rate at all —
W2's own residue item 1 rules it inadmissible ("no discriminating power and must
not be quoted as a rate"). Assumed, operator may override; consistent with the
operator's own words ("reuse its committed operationalization R1").

A7 (R12, C6): `Config.DISCHARGE_POLICY` defaults to `"off"`. Assumed, operator
may override. Turning the channel on BY DEFAULT is a Config DEFAULT, which C6
reserves to F3 — so F1 builds the channel and F3 owns the default. This also
makes R10's "no label differs" provable rather than argued: with the default
off, every existing test, every existing pack byte and every existing wire byte
is unchanged.

A8 (R12): a discharge KIND may declare requirements over the DECLARED FIELD SET
(`note`, `where`). A kind needing a field outside that set is a wire change, not
a declaration. Assumed, operator may override — and stated plainly rather than
left for a reader to discover, because it is the honest boundary of this
tranche's modularity claim.

---

## Questions for operator — ALL ANSWERED 2026-08-26 (REQUEST.md Amendment 2)

**Q-OP-1 — the frozen-surface grant (surface 4/5, `run_manifest.py`).**
**GRANTED 2026-08-26** — operator verbatim: "GRANTED: the one-line
versioned-source entry for DISCHARGE_POLICY in run_manifest.py. This is not an
exception to the frozen surface — it is the documented recipe (a Config field
is not done WITHOUT that line; the ENGAGED_CRITICISM_AUTHORITY trap is its
ancestor)." Four riders bind; they are itemized as **S13**.
`tools/blast_radius.py` returns `"frozen_surface_verdict": "CONTACT"` with the
computed list pasted verbatim below. The contact is ONE line —
`data.pop("DISCHARGE_POLICY", None)` in
`run_manifest.py::_versioned_source_config_data` — owed by the new
`Config.DISCHARGE_POLICY` field, and it is the shape this document itself
prescribes ("Add the mode to `Config`, and add its key here in the same
commit") and has granted five times before.

Measured, not asserted (M2/M5 below): WITHOUT the pop the qualification subject
digest moves from `b9038b84efdea313…` to `a8991192b625c609…` and
`source_config_hash` v6 from `2624603035bc335e…` to `968175064a846bc6…`; WITH
the pop, the design is that both return byte-identical, and the acceptance
check is the digest itself at every schema version, not a green suite.

- **Grant it (RECOMMENDED)** — insertions only, 1 and 0; effect is to PRESERVE
  digests, not move them; no schema, validator or Pydantic model touched; no
  home owes a ~14-minute qualification rerun. Cost to you: one word.
- Withhold it — then the discharge policy cannot be config-selectable, which
  contradicts your own Amendment 1 ("the discharge policy … is a registered,
  config-selectable policy"). Cost: the tranche needs a redesign we have not
  found, and R12 goes unmet.

**Q-OP-2 — C6, the wire-contract boundary against F2.**
**ANSWERED 2026-08-26** — operator verbatim: "read C6 as 'F2's fields' — that
reading is the intent. The boundary exists to prevent collision, not to freeze
the wire layer… The wire.py merge is the monitor's problem, not yours."
Recommendation adopted; the composition note is **S14** (R18).
C6 says "If you need to edit wire-contract FIELD definitions (F2's) … STOP and
say so." This is the saying-so. F1 does **not** edit any existing field: it ADDS
two optional fields (`CompactConjectureCandidate.discharges`,
`ReasoningCandidateProposal.discharges`) plus one new model, all F1-owned, all
pruned from the emitted schema when the channel is off — measured NOT to move
the qualification subject digest (M4: `b9038b84efdea313…` unchanged).

- **Read C6 as "F2's field definitions", so this is inside F1's declared blast
  radius ("the submission path") — proceed (RECOMMENDED).** The tranche is
  impossible otherwise: R3 requires the submission to CARRY typed discharges,
  and there is no other channel for it to arrive on. `discharges[].handle` is
  precisely a reference-bearing field, so F2's menu interface can later give it
  a menu by registering — the two designs compose rather than collide. Cost to
  you: a merge in `wire.py` that F2 and F1 both touch in different regions.
- Read C6 as "any wire field" — then F1 blocks until F2 lands and F1 registers
  its field through F2's interface. Cost: F1 delivers nothing this tranche, and
  the coupling defect W2 measured stays live for another cycle.

**Q-OP-3 — the size.**
**ANSWERED 2026-08-26** — operator verbatim: "one tranche, three commits, ~640
lines accepted… The diff-budget discipline still applies at your stated ceiling
— a typed STOP if it grows beyond what SPEC now declares, not silent growth."
Recommendation adopted; the ceiling discipline is **S15** (R19). SPEC's own itemization sums to ~640 `src/` lines,
against `dr-spec-change`'s ~300-line guidance (C7's ~700-line limit is on the
SPEC document, which this is inside — 701 lines, one over the ~700 guidance, reported
rather than trimmed). The interface (S1) is ~140 of
that and exists because R15 chose it over the ~40-line tighter coupling.
- **Continue as one tranche, three commits (RECOMMENDED)**: the S9 gate proof
  needs the whole channel; a split would ship a render with no submission
  screen, which proves nothing. Rung 6 ran 810 `src/` lines under the same
  ruling.
- Split into F1a (S1–S3, render only) and F1b (S4–S10): each delivers, but F1a
  has no falsifiable coupling claim of its own.

---

## Out of scope (explicit)

- Turning the channel ON by default — a Config DEFAULT, C6 reserves it to F3.
- A menu of legal handles rendered into the wire schema — F2's interface;
  `discharges[].handle` is left as a plain string for F2 to key on.
- Any change to `rules/crit.py`'s recording of criticism — not requested; the
  channel READS what `_observe_case` already writes.
- Widening `Config.ARGUMENTATIVE_AUTHORITY` or any authority mode — not
  requested, and would cross the law line in S7.
- Making a discharge affect rank, admission, budget or scheduling — forbidden by
  R8 and pinned against in S7.
- The live A/B that would show a real provider model responds — W2's parked
  **P2**; S9 is explicit that it does not substitute for it.
- W2's parked **P1** (`admitted_refs` resolving to nothing on disk) — a real
  defect, not requested here; goes to PARKED.md.

---

## Frozen-surface contact forecast

`python tools/blast_radius.py --files src/deepreason/llm/packs.py
src/deepreason/llm/wire.py src/deepreason/rules/conj.py
src/deepreason/config.py src/deepreason/run_manifest.py
src/deepreason/workloads/text.py --symbols render_conj_pack conj
CompactConjectureCandidate ReasoningCandidateProposal DISCHARGE_POLICY`

`"frozen_surface_verdict": "CONTACT"`. The tool's own computed lists, verbatim:

```json
"frozen_surface_contacts": [
  {"surface": "manifest schemas and validators (run_manifest.py)",
   "tier": "DIRECT", "target": "src/deepreason/run_manifest.py",
   "detail": "target file is surface path src/deepreason/run_manifest.py"},
  {"surface": "replay-validation record formats (invariants.py)",
   "tier": "SYMBOL_INDIRECT", "target": "conj",
   "detail": "'conj' referenced in src/deepreason/invariants.py (grep-based; not proof of semantic contact)"}
],
"frozen_adjacent_contacts": [],
"qualification_digest": [
  {"target": "src/deepreason/run_manifest.py", "tier": "CONFIRMED",
   "detail": "target file is part of the manifest/qualification surface itself"}
],
"wheel_smoke_pins": [],
"reachability": [
  {"symbol": "render_conj_pack", "status_current": "REACHABLE"},
  {"symbol": "conj", "status_current": "REACHABLE"},
  {"symbol": "CompactConjectureCandidate", "status_current": "UNKNOWN"},
  {"symbol": "ReasoningCandidateProposal", "status_current": "UNKNOWN"},
  {"symbol": "DISCHARGE_POLICY", "status_current": "UNKNOWN"}
]
```

**Contact 1 — `run_manifest.py`, DIRECT. REAL. This is Q-OP-1's grant request.**

**Contact 2 — `invariants.py` / `conj`, SYMBOL_INDIRECT. FALSE POSITIVE,
disposed by measurement.** Every `conj` in `invariants.py` is a substring of
`conjecture`/`conjecturer` (`conjecture-call:`, `active_conjecture`,
`conjecturer_contract_id`, `conjecturer.turn.v4`). The module imports
`rules.conj` nowhere:

    $ grep -c "from deepreason.rules.conj\|rules import conj\|import conj$" src/deepreason/invariants.py
    0

The gate states its own method in the detail string ("grep-based; not proof of
semantic contact"), so this is the gate working as documented. `invariants.py`
is NOT a target of this tranche.

**The three `UNKNOWN` reachability rows** are class/field names the AST walk
cannot resolve to a call graph, and `dr-spec-change` step 5 requires the manual
cross-check for exactly those. It was run; results are in the census below.

---

## Blast-radius census

Tool-reported `consumers`, classified. Every hit is accounted for; none omitted.

| Target | Consumer hits | Classification |
|---|---|---|
| `render_conj_pack` | 37 test hits across `test_easy.py`, `test_frame_render.py`, `test_harness_fixes.py`, `test_jolt_trigger_pilot.py`, `test_pack_prefix.py`, `test_properties.py`, `test_prose_refutation_boundaries.py`, `test_runtime_workload_integration.py` | **MUST NOT MOVE.** The new parameter is keyword-only with a `None` default, and the section is absent when the channel is off (A7). Any movement here means the default leaked. |
| `conj` | 155 test hits across 60 files | **MUST NOT MOVE.** Same reason: with `DISCHARGE_POLICY="off"`, `screen_submission` returns `accept` with an empty `undischarged` and writes nothing. |
| `CompactConjectureCandidate` | `test_v6_patch_repair_and_wire.py:330,432`, `test_wire_contracts.py:58` | **MUST NOT MOVE.** Manual cross-check (the `UNKNOWN` row) — the three lines were READ, and two of them do inspect the emitted schema, so the "they only construct instances" reading would have been wrong: `test_v6_patch_repair_and_wire.py:330` asserts `"neighbours" not in schema["$defs"]["CompactConjectureCandidate"]["properties"]` and `:432` asserts that property's alias `enum`; `test_wire_contracts.py:58` asserts `additionalProperties is False` on the same `$def`. None enumerates the full property set, so a PRUNED `discharges` moves none of them — which is exactly why S4's pruning is a requirement rather than an optimisation. |
| `ReasoningCandidateProposal` | 14 hits in `test_conjecturer_turn_v4.py`, `test_live_smoke_regressions.py`, `test_semantic_freedom_constitution.py`, `test_skills_models.py` | **MUST NOT MOVE.** These construct instances (e.g. `test_skills_models.py:44` builds one with five keyword arguments) rather than enumerating fields, and the new field is optional with a default, so construction is unaffected. Re-checked at the first `[COMMIT]` step. |
| `src/deepreason/run_manifest.py` | `test_decommissioned_pipeline_stays_out.py:116` | **MUST NOT MOVE.** |
| `src/deepreason/config.py` | map: `CON-authority.md:4,72,81,82,84,85`, `CON-packs-and-token-economy.md:50`, `INV-frozen-surfaces.md:271`, `SEAM-manifest-x-schools.md:215`, `SUB-evaluation.md:184,185`, `SUB-periphery.md:269`, `SUB-scheduler.md:166` | **MUST NOT MOVE**, except `INV-frozen-surfaces.md` — **EXPECTED TO MOVE** (S11: the granted contact is recorded there, if granted). |
| `src/deepreason/llm/packs.py` | map: 33 hits, chiefly `CON-packs-and-token-economy.md` (17) and `SEAM-llm-x-rules.md` (6) | **EXPECTED TO MOVE**: `CON-packs-and-token-economy.md` gains the new non-droppable section (S11). The rest MUST NOT MOVE. |
| `src/deepreason/rules/conj.py` | map: 64 hits across 20 documents | **EXPECTED TO MOVE**: `CON-conjecture-source.md` (the submission precondition). The other 19 MUST NOT MOVE. |
| `src/deepreason/llm/wire.py` | map: 11 hits (`SUB-llm.md`, `SEAM-llm-x-rules.md`, `SEAM-rules-x-scratch.md`, `CON-capability-lifecycle.md`, `SUB-scratch.md`) | **MUST NOT MOVE** — none pins the candidate models' field sets; verified by reading each of the 11 lines. |
| `src/deepreason/workloads/text.py` | map: `SEAM-evaluation-x-ontology.md:54,75,139`, `SEAM-ontology-x-rules.md:72`, `SUB-periphery.md:99,162` | **MUST NOT MOVE.** |
| `conj` (map) | 200+ hits across 25 documents | **MUST NOT MOVE** except `CON-conjecture-source.md` as above. |
| `wheel_smoke_pins` | `[]` — empty | No console entry point, MCP tool or wheel-layout change. Both smokes run anyway (S12). |

Manual cross-check for the `UNKNOWN` symbol `DISCHARGE_POLICY`:
`grep -rn "DISCHARGE_POLICY" src/ tests/ docs/` → no hits (the name is new).

---

## Measurements

M1: `grep -c "from deepreason.rules.conj\|rules import conj\|import conj$"
src/deepreason/invariants.py` → `0` — supports the disposal of frozen contact 2
as a grep false positive.

M2 (baseline, unmodified tree): `source_config_hash(Config(), schema_version=v)`
→ v1,v2 `6c2d01f6b8cbe65e2a26bb57e864a80feec07b0896142fb2267bc83d2717dc81`;
v3–v6 `2624603035bc335e59da63f25426d3ae6619bf7f84d48657e8f25310de49edc5`.
Byte-identical to the values `DR-INV-frozen-surfaces` records for Rung 8 —
supports "the digest table is the acceptance check, and it is stable today".

M3 (baseline): `qualification_subject_digest(_manifest(_profile()), _profile())`
→ `b9038b84efdea313c3f3f2a8862d8acf180d3938ab3d1bf3588c3585dfe07386`.
Byte-identical to the value `DR-INV-frozen-surfaces` records — supports the same.

M4 (probe, reverted): with an extra `list[str]` field added to
`CompactConjectureCandidate`, the subject digest is
`b9038b84efdea313c3f3f2a8862d8acf180d3938ab3d1bf3588c3585dfe07386` —
**unchanged** — supports S4's claim that the wire additions leave surface 5 at
zero. `git diff --stat src/deepreason/llm/wire.py` after restore: empty.

M5 (probe, reverted): with `PROBE_M5_POLICY: str = "off"` added to `Config` and
NO `data.pop` line, `source_config_hash` v6 →
`968175064a846bc6d159a3f205f8379f446ddb30145bfb9b2c8e0c954dd3e2e6` and the
subject digest → `a8991192b625c60924afa64126f15a4c8aed1b01e479159266955ae720d9928f`
— both MOVED — supports Q-OP-1: the `data.pop` line is owed, and it is what
PRESERVES the digest rather than what disturbs it.
`git diff --stat src/deepreason/config.py` after restore: empty.

M6: `experiments/2026-08-26-run-anatomy-w2-criticism/RESULTS.md` §3a — 0 of 196
LLM attacks exposed to a later conjecture dispatch; placebo-corrected coupling
−12.7 / −1.9 / +5.9 / +0.0 pp; 0 of 92 coupled changes improved a score;
NeglectRate 82.2% / 90.6% — supports the whole tranche's premise and S2's
decision to include the `observe_only` population.

---

## Options

**A — tighter coupling, smaller.** A `_KINDS` tuple and a
`_render_open_criticisms()` helper inside `llm/packs.py`, with the screen inline
in `conj.py`. Files touched: 3. Frozen contact: `run_manifest.py` still (the
Config field). ~180 `src/` lines. Risk: a fourth kind needs three file edits.
**Rejected — cites R15** (the operator has priced this fork and chosen the
interface) **and R13** (customising would require editing code).

**B — declared interface package.** `src/deepreason/discharge/` with a versioned
registry, config-selected policy, and an architecture test that goes RED when a
kind cannot be added by declaration. Files touched: 6 + 4 new. Frozen contact:
`run_manifest.py`, one line. ~640 `src/` lines. Risk: larger diff.
**CHOSEN — cites R15, R14, and M4/M5** (the wire and Config costs are measured,
not feared).

**C — carry discharges at the TURN level rather than per candidate.** ~40 fewer
lines, one field instead of two. **Rejected — cites R3's own words** ("a new
candidate on a problem with open criticisms must carry, per criticism handle, a
typed discharge"): the obligation is stated on the candidate.

---

## Budget

```
python3 -c "print(sum([140, 110, 90, 45, 130, 60, 40, 25]))"   # 640  src/
python3 -c "print(sum([150, 120, 110, 90]))"                    # 470  tests/
python3 -c "print(sum([120, 60]))"                              # 180  docs/map/
```

- `src/` ceiling: **640** lines (S1 140, S2 110, S3 90, S4 45, S5 130, S6 60,
  S7-support 40, S8-support 25). This is the number
  `tools/diff_budget.py --paths src/` is checked against at every `[COMMIT]`.
- `tests/` ~470, `docs/map/` ~180, tranche artifacts + instrument ~350.
- Commits: **3** — (1) interface + registry + record + render (S1–S3, S11 part);
  (2) wire + submission + records (S4–S6, S11 part); (3) law line + architecture
  test + coupling instrument + gate (S7–S10, S12).
- Frozen surfaces touched: **1 — `run_manifest.py`, one insertion, GRANTED
  2026-08-26 (Q-OP-1, riders itemized at S13).** `invariants.py` disposed as a false positive (M1).

Rubric: 6/6 yes (re-run 2026-08-26 after Amendment 2) — every R has a spec item
with a machine-decidable accept (R1→S3, R2→S3, R3→S4/S5, R4→S5, R5→S7,
R6→S6, R7→S7 pin 4, R8→S7 pins 2/3, R9→S9, R10→S10/S11/S12, R11→S5,
R12→S1/S8, R13→S1/S8, R14→S8, R15→S1/Options, R16→S13, R17→S14, R18→S14,
R19→S15, R20→S16);
blast-radius census pasted and every hit classified; frozen-surface contact
forecast recorded with the tool's own list verbatim; every named mechanism
traced to code it reaches (Rung 6 render machinery → `calculus/render.py` +
`llm/packs.py` sections, traced; W2's R1 → `q5.py` lines 20–24, traced;
`prune_property` → `ConjecturerTurnWireContractV6._omit_property`, traced);
DESIGN-AND-STOP sections present (Measurements, Options) because this phase
stopped, and its stop is now resolved on the record (Amendment 2); nothing untraceable to an R/C number.
