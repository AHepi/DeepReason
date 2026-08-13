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
