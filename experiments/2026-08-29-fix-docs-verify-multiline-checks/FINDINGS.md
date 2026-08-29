# FINDINGS — R3, the first execution of the map's 72 dark checks

Instrument: `python tools/docs_verify.py` (full mode, no cache), at this
branch's R2 commit, container `python` 3.11.15 with the editable install
and `pytest` armed on the SAME interpreter the checks invoke (see
REPRO.md — the pre-fix 502 was that interpreter split, not the map).

    docs_verify [full]: 69 documents, 1212 checks, 4 workers
    docs_verify: 9 failed

## Counts

| | before | after |
|---|---|---|
| checks the instrument executes | 1141 | **1212** |
| of which multi-line | 0 | **71** (70 committed, 1 new in `SCHEMA.md`) |
| column-0 openers unaccounted for | 72 | **0** |
| failures | 4 (of which 1141 executed) | **9** (of 1212 executed) |

**66 of the 70 committed dark checks PASS.** That is the headline and it
is good news: the map's strongest claims were unproven, not wrong. Four
had rotted, and nothing had said so.

## Class (a) — passes, decay-free

1203 of 1212. Among them 66 of the 70 checks that had never once run,
including 8 of the 10 in `INV-frozen-surfaces.md`, all 8 in
`INV-axiom-basis.md`, all 7 in `INV-render-layout.md`, all 6 in
`SUB-calculus.md` and all 5 in `INV-evidence-channels.md`. The frozen
surfaces are, on today's tree, what those documents say they are.

## Class (b) — the claim rotted (4, all newly executed, none in this cone)

### B1 `SEAM-llm-x-verification.md:19` — the seam's core arrow is false

Claim it defends, verbatim: "Between them there is **no import in either
direction** — `invariants.py` names nothing from `llm/`, and `llm/` names
nothing from `invariants.py`."

    AssertionError: ('src/deepreason/invariants.py', 'deepreason.llm.firewall')

`src/deepreason/invariants.py:21` is a module-level
`from deepreason.llm.firewall import route_fingerprint`, with four more
function-local `deepreason.llm.*` imports at lines 1214, 1215, 1260 and
4101. The direction the seam denies exists five times over. Weight: the
symbol imported is `route_fingerprint`, which CLAUDE.md names as the
frozen-ADJACENT surface, and the importer is `invariants.py`, frozen
surface 3. This is the most load-bearing failure in the table.

### B2 `INV-frozen-surfaces.md:657` — a stale qualification digest pin

Claim it defends: the qualification subject digest is unmoved by the
`DISCHARGE_POLICY` drop (frozen surface 5, "anything altering
qualification subject digests").

    assert qualification_subject_digest(_manifest(p), p) == 'b9038b84...'
    AssertionError

    actual                          02ee7e098bb9239011708a4aa0bce4b7479619b3aff28eff46188125a869e713
    pinned at INV-frozen-surfaces:657  b9038b84efdea313c3f3f2a8862d8acf180d3938ab3d1bf3588c3585dfe07386
    pinned at INV-frozen-surfaces:533  02ee7e098bb9239011708a4aa0bce4b7479619b3aff28eff46188125a869e713

The same document pins the same expression twice, at :533 and at :657,
with two different values. :533 is right and :657 is stale. Both were
dark, so nothing could ever have made them argue. The digest itself has
not silently drifted — the current value is the one :533 asserts — so
this is a stale pin, not a broken surface. It still has to be corrected
by someone with the surface-5 authority to touch that document.

### B3 `CON-discharge-channel.md:150` — the check's fixture, not the claim

Claim it defends: the manifest echo drops `DISCHARGE_POLICY`, and
`config_from_run_manifest` restores the default — the evidence for the
document's own statement that its FREE layer "is, today, reachable only
by editing code", which the modularity law forbids.

    pydantic ValidationError for RunManifest
    Value error, V6_SIMULATION_TOOLCHAIN_REQUIRED: policy must bind one frozen toolchain

The check dies constructing its manifest, before reaching either
assertion. Cause, located: `run_manifest.py:3527-3538` requires exactly
one `manifest.toolchains` entry whose `id` equals
`capabilities.simulation.python_toolchain_identity`, and

    engaged_inquiry_capability_policy(...).simulation.python_toolchain_identity
        = python@deepreason-public-contained.v1
    engaged_local_simulation_toolchain().id
        = python@deepreason-public-local.v1

The check binds the LOCAL toolchain against a policy that names the
CONTAINED one. The claim about `DISCHARGE_POLICY` is untested either
way — it is not shown false, it is unreached.

### B4 `INV-signal-contract.md:222` — a check defeated by a comment

Claim it defends: "The consumer reads the interface and nothing else.
`scheduler.py` calls `wander.decide` and `wander.reading_from`; it never
names a policy function."

    for fn in ('wander_cap_v1', 'open_lineage_v1', 'LINEAGE_POLICIES'):
        assert fn not in src, fn
    AssertionError: LINEAGE_POLICIES

The single occurrence is `scheduler/scheduler.py:1127`, and it is a
COMMENT: `# The policy is selected by id from `wander.LINEAGE_POLICIES``.
`inspect.getsource` returns comments, so a sentence explaining the
decoupling trips the check that proves it. On the evidence the claim
still holds and the CHECK is what needs the fix (parse the AST, or scan
`ast.unparse` output, rather than raw source text). Recorded as (b)
rather than (c) because it is well-formed and runs; it is imprecise, not
malformed.

Note for the scheduler window: `scheduler/scheduler.py` is an in-flight
cone. This failure is on `main` at `ae490e26b`, before any of that work
landed — it is not theirs.

## Class (c) — malformed beyond the two-format grammar (1)

### C1 `SEAM-llm-x-rules.md:54` — a lost closing backtick swallowed a paragraph

    FAIL SEAM-llm-x-rules.md:54: unparseable check: a column-0 `check:
    opener must close with a trailing backtick ...

Exact committed text, one line, verbatim to its end:

    `check: test "$(python -c "import ast,pathlib; T=[ast.parse(p.read_text()) for p in pathlib.Path('src/deepreason/rules').rglob('*.py')]; n=[x for t in T for x in ast.walk(t) if isinstance(x, ast.ImportFrom) and (x.module or '').startswith('deepreason.llm')]; print(len({a.name for x in n for a in x.names}))")" = "41" What does not cross is every transport primitive — no `LLMAdapter`,

and the following two lines are the rest of that absorbed paragraph:

    `build_adapter`, `TokenMeter`, endpoint class, `select_lease`,
    `render_role_prompt` or `reject_model_control_fields` is importable by a rule.

A single-line check lost its closing backtick and the prose paragraph
that followed it lost its blank line, so the two merged. The check ends
at `= "41"`; everything after is prose. This is the count check the
document's own prose says was added because the number had already
drifted once ("this sentence read 'Thirty-nine' while the tree carried
FORTY") — so the repair it was written to prevent is exactly what it has
been unable to prevent since. Out of this tranche's cone; parked, not
repaired.

## Baseline — pre-existing, not newly executed, not this tranche's (4)

All four are single-line checks that have been running and failing since
before this branch. Listed so the R4 total is readable, not as findings.

| where | why |
|---|---|
| `CON-run-identity.md:200` | `git log -M --diff-filter=R` over history the shallow clone does not have |
| `CON-run-identity.md:202` | `fatal: ambiguous argument '1637e808'` — commit absent from a shallow clone |
| `CON-run-identity.md:204` | `fatal: ambiguous argument 'f304fec1'` — same |
| `INV-frozen-surfaces.md:181` | the falsified census: the check asserts ZERO committed attempts carry `outcome: "transport_failure"`; one does, in a root committed 2026-08-26 — `experiments/2026-08-26-pc2-rematch/retired-transport-timeout180-run-42ad288038dd606c/objects/workflow-provider-attempt-v1/f750d2979c3e248e549efb5754bfb11b947cba1cfa7fb2bb8c1d77babad3b570.json` |

## The residue — what this run does NOT prove

- That the map is now sound. It proves 1203 claims re-derive today and
  that 5 do not. Nine in ten prose lines in these documents carry no
  check at all (`SCHEMA.md`, "What a check can and cannot bind"), and
  this instrument has never been able to see them.
- That the 66 newly-green checks were green all along. They were dark;
  a check that had rotted and been repaired by an unrelated change would
  look identical from here. The record starts today.
- That B2's digest never moved. It proves the pin at :657 disagrees with
  the tree and with the same document's :533. Which of the three is
  historically correct is a question for the surface-5 owner.

## Addendum — the same run on a FULL clone

The clone was unshallowed (`git fetch --unshallow`) and the instrument
re-run from a cleared cache:

    docs_verify [full]: 69 documents, 1212 checks, 4 workers
      FAIL SEAM-llm-x-rules.md:54       (C1, malformed)
      FAIL CON-discharge-channel.md:150 (B3)
      FAIL INV-frozen-surfaces.md:181   (pre-existing falsified census)
      FAIL INV-frozen-surfaces.md:657   (B2)
      FAIL INV-signal-contract.md:222   (B4)
      FAIL SEAM-llm-x-verification.md:19 (B1)
    docs_verify: 6 failed

The three `CON-run-identity.md` git-history checks PASS on the full
clone, individually re-run and confirmed. So the honest totals are **6
failed on a full clone, 9 on a shallow one**, and both are recorded in
`docs/AUDIT_BASELINES.md` rather than one being presented as the truth.
