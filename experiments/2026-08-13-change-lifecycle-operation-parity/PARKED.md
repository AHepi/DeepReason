# PARKED.md — lifecycle-operation parity

Found while doing this tranche, deliberately NOT done here. Each entry is
one line of WHAT plus a ready-to-send prompt: the follow-up should cost
the operator a paste, not an authoring session.

---

## P1 — `deepreason reason` cannot take a compiled run-manifest

**What.** `deepreason reason` mints its own manifest through
`RunPreparationService` and has no `--run-manifest` flag
(`cli/main.py:285-326`, `cli/main.py:2240-2247`), so a compiled config
(judge ensembles, school-routed criticism) can only be launched through
`deepreason run --run-manifest`. This tranche gives that path every
lifecycle operation (SPEC A2), which delivers the operator's parity
sentence; adding a second surface that does the same job is a separate
change and was not requested as one.

**Ready-to-send prompt:**

```
Change tranche: launch-path parity — `deepreason reason` accepts a
precompiled run manifest. Route through dr-change-orchestrator.

AUTHORITY, operator verbatim (2026-08-13): "The new generic reason run
doesn't recognise the new config style nor does 'append'. This needs
fixing next. The flags and operations available to the newer reason runs
should be available to all configurations." The 'append' half was closed
by experiments/2026-08-13-change-lifecycle-operation-parity (see its
DELIVERY.md); the 'config style' half is this tranche.

READ FIRST: that tranche's SPEC.md assumption A2 (why this was parked),
INVENTORY.md row 17 (the proof of the gap), and docs/map/SUB-application.md.

SCOPE: `deepreason reason "Q" --run-manifest <path>` binds the compiled
manifest instead of minting one, keeping every other reason flag
(--cycles, --token-budget, --dossier, --attach, --allow-partial) working,
and keeping run identity deterministic (the manifest sha is the run id).
Decide and record in SPEC.md what happens when --run-manifest is combined
with a question whose minted identity would differ — per the 2026-08-12
all-configurations law this is a typed DISCLOSURE recorded alongside the
compiled result, never a compile-time refusal.

TESTS: a reason run launched with --run-manifest produces the same root
identity as `deepreason run --run-manifest` on the same manifest, and
reaches the same typed terminal. GATE: ring while iterating, full gate at
the boundary, docs_verify full. Map moves in the same commit
(SUB-application, CON-run-identity). Commit and push at every phase
boundary.
```

---

## P2 — no seam document covers application × amendment, application ×
## verification, or amendment × verification

**What.** `docs/map/INDEX.md`'s subsystem table omits `SUB-application.md`
and `SUB-amendment.md` entirely (both files exist and are verified), and
every pair this tranche actually spans is listed only under
`Seams-undocumented:` on the covering subsystem documents. The map
therefore routes a future reader to the two subsystems separately, which
is exactly the ten-times-too-much reading the seam rule exists to prevent.

**Ready-to-send prompt:**

```
Change tranche: map completeness — INDEX.md's subsystem table, and the
missing amendment/application/verification seams. Route through
dr-change-orchestrator.

AUTHORITY: finding recorded in
experiments/2026-08-13-change-lifecycle-operation-parity/REQUEST.md
("Map preflight") and PARKED.md P2 — SUB-application.md and
SUB-amendment.md exist and are Verified-at-stamped but appear in no
INDEX.md routing row, and the pairs application x amendment,
application x verification, amendment x verification carry no
SEAM- document.

READ FIRST: docs/map/SCHEMA.md (the contract), docs/map/INDEX.md,
docs/map/REC-change-a-seam.md.

SCOPE: (1) add the two missing INDEX.md subsystem rows and recompute the
seam matrix's coupling numbers for the pairs they introduce; (2) write
SEAM-amendment-x-application.md and SEAM-amendment-x-verification.md,
each with executable `check:` commands that would fail if the agreement
regressed. Every load-bearing claim carries a check that has been RUN.
GATE: python tools/docs_verify.py (0 failed), --audit (no check that
cannot fail), --links (every DR- reference resolves). Commit and push at
every phase boundary.
```

---

## P3 — operator lock files are committed inside run roots

**What.** `.run-operator.lock`, `.make-operator.lock`, `.run-input.lock`
and `.run-manifest.lock` are tracked in git inside
`experiments/2026-08-12-live-grounded-extension-expansion/run/`. They are
mutable single-owner locks — `DR-SUB-application`'s own "State it owns"
section classes every such file as control, not record — so any operation
that legitimately takes the lock shows up as a modification to a committed
root. That is cosmetically indistinguishable, in `git status`, from
editing the record, which is precisely the distinction the append-only law
turns on. Observed while finalizing the grounded root: the only real
change was `log.jsonl | 1 insertion, 0 deletions`, but two lock files
showed as `M` beside it.

**Ready-to-send prompt:**

```
Fix tranche: operator lock files must not be committed inside run roots.
Route through deepreason-orchestrator.

EVIDENCE: experiments/2026-08-13-change-lifecycle-operation-parity/PARKED.md
P3. `git diff --numstat` on a run root after a legitimate lock acquire
shows `.run-operator.lock` and `.make-operator.lock` as modified beside
`log.jsonl | 1 0`. Locks are control files (docs/map/SUB-application.md,
"State it owns"), never record content, so a reader auditing whether a
committed root was edited cannot tell the two apart at a glance.

READ FIRST: docs/map/SUB-application.md "State it owns",
src/deepreason/locking.py (OPERATOR_LOCK_NAMES), .gitignore.

SCOPE: add the operator lock names to .gitignore and `git rm --cached`
the tracked ones, so a run root's tracked contents are record and
documents only. Decide and record whether removing them from the index
changes any committed root's replay verdict -- it must not, and
`python tools/root_sweep.py` is the instrument that says so. GATE: full
gate at the boundary, root_sweep zero verdict drift, docs_verify full.
Map moves in the same commit if SUB-application's state section names
them. Commit and push at every phase boundary.
```

---

## P4 — citable evidence reaches SEED conjectures only, and quotes are asked for as optional

**Two findings, both from the record, and both correcting earlier claims
of mine that are retracted below.**

### P4a — evidence blocks are offered only on the seed problem

Every conjecturer prompt on this root, classified by the problem it was
working and whether the pack carried the `CITABLE EVIDENCE BLOCKS`
section:

    epoch 0       SEED          FULL-evidence     8
    epoch 0       SEED          alias-only        5
    epoch 0       sub-problem   alias-only       28
    continuation  sub-problem   alias-only        8

The evidence section appears ONLY on the seed problem — **0 of 36
sub-problem prompts in epoch 0**, and 0 of 8 in the continuation. A
spawned sub-problem's conjecturer is shown `LOCAL REFERENCES (copy
aliases, not identifiers)` — bare `SRC_001…SRC_008` aliases with no
source ids, no titles and no block ids — so it cannot emit a citation
that resolves: `EvidenceRefClaimV1.block` requires
`^[0-9a-f]{12,64}$`, and the seed-problem instruction itself says "Only
ids from this list resolve — artifact hashes and any other handles are
rejected as unknown."

Sub-problems are where most conjecture happens: 36 of 49 conjecturer
calls on this root. So most of the run's conjecture is structurally
unable to ground itself in admitted evidence.

**RETRACTION.** An earlier version of this entry claimed the AMENDMENT
path fails to present block ids while the run-start bind path presents
them. That is false. The variable is the PROBLEM being worked, not the
epoch: the continuation's 8 conjecture calls all happened to land on
sub-problems, which never carry the section in either epoch. Two prior
readings of the same 8-call sample — first "probably chance", then
"structural, not chance" — were both wrong; the operator's challenge is
what forced the classification above, and it is the only one supported by
the record.

### P4b — the quote is requested as optional, and is therefore never given

The seed-problem instruction, verbatim from a recorded prompt:

    CITABLE EVIDENCE BLOCKS — to ground a candidate in admitted
    evidence, name these block ids in its evidence_refs (optionally
    with an exact quote from the block; quotes are byte-checked
    against the recorded bytes). Only ids from this list resolve —
    artifact hashes and any other handles are rejected as unknown.

`quote` is parenthesised and marked optional. Outcome on this root:
**101 `EVIDENCE_CITATION_VERIFIED`, 0 quotes, 0
`EVIDENCE_QUOTE_MISMATCH`.** Every verified citation carries a block and
no quote, so each one means "this block exists and is citable", never
"this quotation is accurate". The byte-verifier in
`evidence/citations.py` has never in this root been given a byte to
check — not because quoting was accurate, but because none was asked for
in a way models act on.

### Ready-to-send prompt

```
Fix tranche: citable evidence reaches SEED conjectures only, and quotes
are requested as optional so they are never supplied. Route through
deepreason-orchestrator.

EVIDENCE (typed, already diagnosed -- verify, do not re-derive):
experiments/2026-08-13-change-lifecycle-operation-parity/PARKED.md P4.
Classifying every conjecturer prompt on grounded-extension root
8e22d0431fd2b98d by problem and pack form (LLMCall.prompt_ref):
  epoch 0      SEED        FULL-evidence   8
  epoch 0      SEED        alias-only      5
  epoch 0      sub-problem alias-only     28
  continuation sub-problem alias-only      8
0 of 36 sub-problem prompts carried CITABLE EVIDENCE BLOCKS. The dossier
holds 296 blocks. Sub-problems are 36 of 49 conjecturer calls.
And: 101 EVIDENCE_CITATION_VERIFIED, 0 quotes, 0 QUOTE_MISMATCH -- the
instruction says "(optionally with an exact quote...)".

START by reproducing that classification, then find what decides whether
the CITABLE EVIDENCE BLOCKS section is rendered. Look at the pack
builders in packs/ and DR-CON-packs-and-token-economy's section
allocation, and at how attached evidence is scoped to a problem --
whether a spawned sub-problem inherits its parent's citable set is the
crux.

SCOPE, two parts, and decide each explicitly:
(1) whether a sub-problem descended from a problem with attached evidence
    should be able to cite that evidence. If yes, make the citable set
    inheritable and deterministic; 296 blocks cannot all go in every
    pack, so record the selection rule in SPEC.md and make it replayable.
(2) whether `quote` should be requested rather than permitted -- e.g.
    "name the block id AND quote the sentence you rely on" instead of a
    parenthetical "optionally". This is a prompt-wording change with a
    measurable outcome: quotes supplied, and QUOTE_MISMATCH becoming a
    finding that can actually fire.

GUARDRAIL: CLAUDE.md's standing law -- nothing may penalize an informal
or uncited conjecture. This adds capability and asks more clearly; it
must not become a rank, admission or acceptance penalty for not citing.

TESTS: a sub-problem conjecture can emit an evidence_refs entry that
resolves against an inherited citable block; a candidate quoting text
that is NOT in the block produces EVIDENCE_QUOTE_MISMATCH (the verifier
proven live, not just present); an uncited conjecture is neither refused
nor down-ranked. GATE: ring while iterating, full gate at the boundary,
docs_verify full, root_sweep zero verdict drift. Map moves in the same
commit. Commit and push at every phase boundary.
```

---

## P5 — a refutation never tightens what the next conjecture must satisfy

**What.** The spec already has the mechanism by which a problem's criteria
bind every conjecture addressing it — §3: `B₀(a) = I(a).commitments ∪
instantiated criteria of addressed problems` — and
`workloads/models.py::compile_interface_draft` implements it literally:

    commitments = [cid for cid in (*problem.criteria, *owned.commitments)
                   if registered_or_drafted]
    # plus draft_forbidden_commitments(skeleton) from the model's own skeleton

So `problem.criteria` IS the problem interface, and it is load-bearing.
What is missing is any edge from a CONVICTION to a criterion. Every
spawn trigger in `rules/spawn.py::scan_spawns` fires on graph GEOMETRY,
never on the content of an argument, and the refutation-driven one
inherits rather than adds:

| Trigger | Fires when | Criteria given |
|---|---|---|
| `SEED` | the operator's question | none |
| `SUCCESSOR` | a candidate is REFUTED | **`criteria=parent.criteria` — verbatim** |
| `DISCRIMINATION` | ≥2 surviving rivals | none |
| `REMOVE_ARBITRARINESS` | ACCEPTED with hv < HV_MIN | inherits parent's |
| `EXPLANATION_DEBT` | reach>0 across ≥2 problems | union of addressed problems' criteria |
| `CONNECTION` | isolation floor breached | mints hv-floor + lineage-ref + relation-form |
| `RESEARCH` | observation-valued commitment, no evidence | none |
| `INTEGRATION` | two accepted, shared commitments, no relation | mints relation-form |

**Measured on the grounded-extension root** (`8e22d0431fd2b98d`), 2 894
problems:

    trigger census        INTEGRATION 2814(1 criterion) · CONNECTION 53(3)
                          DISCRIMINATION 10(0) · SUCCESSOR 8(0)+8(3)
                          SEED 1(0) · EXPLANATION_DEBT 0 · RA 0 · RESEARCH 0
    criterion families    relation-form x2875 · hv-floor x61 · lineage-ref x61
    SEED problem criteria []

All three families are minted by the scheduler from graph geometry. **Not
one criterion on this root originated in anything a critic concluded**,
and the only accreting trigger (`EXPLANATION_DEBT`) never fired. The
operator's seed question carries no criteria at all, so conjectures on it
face no accumulated surface.

**Why this is a design question before it is a defect.** The spec is
SILENT on conviction-to-criterion: §3 says criteria bind, §7 Brake 1
shows the pattern working (`hv-floor` pinned as the consequence of a
structural judgement), but nothing anywhere says a refutation should mint
an obligation. So this needs an operator/spec decision, not a bug fix.
The operator's framing, 2026-08-13: knowledge growth should shrink the
space of REACHABLE conjectures, "like in science" — and `hv-floor` is
proof the machinery can carry it.

**Ready-to-send prompt:**

```
DESIGN-AND-STOP tranche: should a conviction tighten what the next
conjecture must satisfy? Route through dr-change-orchestrator; the
deliverable is SPEC.md and an ended turn, NOT an implementation.

AUTHORITY, operator (2026-08-13): "minted convictions never tighten the
number of commitments a conjecture must satisfy? Meaning, like in
science, the scope of valid conjectures becomes smaller the more
knowledge grows? Maybe not valid, maybe reachable is a better word."

EVIDENCE (already measured -- verify, do not re-derive):
experiments/2026-08-13-change-lifecycle-operation-parity/PARKED.md P5.
On root 8e22d0431fd2b98d: 2894 problems, criterion families
relation-form x2875 / hv-floor x61 / lineage-ref x61, all
scheduler-minted from geometry; SUCCESSOR spawns pass criteria=
parent.criteria verbatim; the seed problem carries zero criteria;
EXPLANATION_DEBT never fired.

READ FIRST: docs/harness-spec-v1.3.md §3 (the B0 battery rule), §7 Brake 1
(hv-floor as criterion-not-gate -- the working precedent), §11.5 (negative
case law at the gate, the REACHABILITY half), rules/spawn.py::scan_spawns,
workloads/models.py::compile_interface_draft.

THE QUESTION TO DECIDE AND WRITE DOWN: when a warrant refutes a candidate,
should the successor problem carry an ADDITIONAL criterion derived from
that refutation -- and if so, what exactly is the criterion, who authors
it, and what makes it replay-stable? Price at least these options and
reject each with a measurement, not a preference:
  A. successor inherits + one harness-authored criterion naming the
     defeated commitment (deterministic, no model authorship)
  B. the critic proposes the criterion; it registers only under the same
     trial/validity-node discipline as any warrant
  C. no new criterion; narrow REACHABILITY instead via the negative-atlas
     gate (§11.5), which is already specified and needs no new semantics
  D. do nothing; record why the analogy to science does not transfer

HARD CONSTRAINTS the design must respect:
- CLAUDE.md's standing law: formalism is an option, never an obligation.
  Nothing here may penalize an informal or uncited conjecture, and no
  outcome may be weighted on conjecture KIND.
- Criteria feed compile_interface_draft, which feeds the artifact id
  (spec: id = sha256(canonical(content_ref, codec, interface))). Adding a
  criterion changes what FUTURE artifacts must satisfy and must not
  disturb any committed artifact's identity -- state explicitly why the
  chosen option is append-only safe.
- Measures never adjudicate (spec §0). A criterion is an attack surface,
  not a verdict.
- Determinism/replay: whatever mints the criterion must be a pure
  function of replayed state, or it breaks root validity.

STOP after committing SPEC.md with the options priced and one
recommendation. No code.
```

---

## P6 — the anti-relapse gate ran degraded for the whole run, silently

**What.** §11.5's negative case law — the refuted-region index at the
registration gate, the mechanism that narrows REACHABILITY — was inert
for this entire run. The typed record says so:

    relapse-gate-degraded  x250   missing: ["near_dup_eps"]
    embedder-fallback      nomic-ai/nomic-embed-text-v1.5,
                           "fastembed not installed"

The semantic-neighbour trigger stage needs embeddings; `fastembed` is an
optional extra (`pip install 'deepreason[embed]'`) that was absent, the
embedder fell back to `HashingEmbedder`, and the gate degraded for all
250 candidates. Zero blocks were recorded. The fallback IS logged, as
`ops.py::make_embedder` intends — but a run can still complete, report
`state: completed`, and pass `verify_root` with one of its two
knowledge-narrowing mechanisms switched off, and nothing in the typed
result says so.

Recorded here (not asked for) because it is a distinct, measured defect
from the same investigation and would otherwise be lost. Strike it if
unwanted.

**Ready-to-send prompt:**

```
Fix tranche: a degraded anti-relapse gate should be visible in the typed
result, not only in the log. Route through deepreason-orchestrator.

EVIDENCE: experiments/2026-08-13-change-lifecycle-operation-parity/
PARKED.md P6. On root 8e22d0431fd2b98d: relapse-gate-degraded x250
(missing near_dup_eps), embedder-fallback (fastembed not installed), zero
gate blocks, and run-result.json still reports state=completed with
integrity_valid=true and says nothing about the degradation.

READ FIRST: docs/harness-spec-v1.3.md §3 (anti-relapse, three stages) and
§11.5 (negative case law at the gate), ops.py::make_embedder (which
already logs the fallback and has an EMBEDDER_FAILURE_POLICY='error'
mode), and the verification report channels in verification/report.py.

SCOPE: decide and record whether a run whose anti-relapse gate never
armed should (a) surface an operational finding in the terminal
verification report, (b) refuse to start under a policy flag, or (c) both.
Note that EMBEDDER_FAILURE_POLICY='error' already exists for exactly this
class of problem in evidence mode -- the question is whether the relapse
gate deserves the same treatment and whether the default should change.
Do NOT make the fallback itself an error by default without pricing what
that does to every existing ladder.

TESTS: a run whose gate degrades produces a typed operational finding; a
run with the gate armed does not. GATE: full gate at the boundary,
docs_verify full, root_sweep zero verdict drift. Map moves in the same
commit. Commit and push at every phase boundary.
```
