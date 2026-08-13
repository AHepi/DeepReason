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

## P4 — evidence admitted by `amend` is VISIBLE to the models but not CITABLE

**What.** `deepreason amend --attach` admits sources and the models do read
them — but the amendment epoch's pack presents them as display handles
(`SRC_001`…`SRC_008`) and shows **no dossier block ids at all**, while the
run-start bind path shows blocks with their ids. An `evidence_refs` entry
requires `block` matching `^[0-9a-f]{12,64}$`, so a model working from an
amendment-epoch pack **cannot** emit a checkable citation however much it
wants to. The instruction to cite is still in the prompt, which makes it
worse: the model is asked for verifiable citations and handed nothing
verifiable to cite.

**Measured on the grounded-extension root** (`8e22d0431fd2b98d`), across
every conjecturer prompt recorded via `LLMCall.prompt_ref`:

    dossier blocks that COULD be cited: 296

    epoch 0      : 41 conjecturer prompts |  8 contain a dossier block id
                   | 44 distinct blocks shown
    continuation :  8 conjecturer prompts |  0 contain a dossier block id
                   |  0 distinct blocks shown

    epoch 0 prompt      : 50 hex block ids · "block" x34 · 1 SRC_ handle
    continuation prompt :  0 dossier block ids · "block" x8 · 8 SRC_ handles

Consequence in the candidates, same four-key shape in both epochs:

    epoch 0       evidence_refs = [{"block": "09ffabcd92979168"}, ...]
    continuation  evidence_refs = []
                  neighbours    = ["SRC_002", "SRC_005"]

The continuation made 181 model calls; 48 named an admitted source in
`neighbours` (all 23 argumentative-critic calls did), and 0 produced an
`evidence_refs` entry. **That is not a small-sample effect.** Epoch 0's
conjecturer emitted refs on 17 of 40 calls (42.5%), so 0 of 8 would be a
~1-in-84 coincidence — but the prompt census removes chance from the
question entirely: zero block ids were ever shown, so zero was the only
possible outcome.

**What it does NOT mean.** The evidence reached the seats and changed what
they said; this is not evidence blindness. And note that epoch 0's own
`evidence_refs` entries carry `block` with no `quote`, so its 101
`EVIDENCE_CITATION_VERIFIED` results mean "this block exists and is
citable", not "this quotation is accurate" — no quote was ever supplied in
this root, and `EVIDENCE_QUOTE_MISMATCH` is 0 for that reason, not because
quoting was accurate.

**Ready-to-send prompt:**

```
Fix tranche: evidence admitted by `amend` is visible to the models but not
citable. Route through deepreason-orchestrator.

EVIDENCE (typed, already diagnosed from the record -- do NOT re-derive it,
verify it): experiments/2026-08-13-change-lifecycle-operation-parity/
PARKED.md P4. On the grounded-extension root 8e22d0431fd2b98d, across every
conjecturer prompt recorded via LLMCall.prompt_ref:
  epoch 0      41 prompts,  8 contain a dossier block id, 44 blocks shown
  continuation  8 prompts,  0 contain a dossier block id,  0 blocks shown
The dossier holds 296 citable blocks. EvidenceRefClaimV1.block requires
^[0-9a-f]{12,64}$, so an amendment-epoch model cannot cite checkably.
Candidates confirm it: evidence_refs [] with neighbours ["SRC_002","SRC_005"].

START by re-running that prompt census to confirm it still reproduces, then
find where the run-start bind path renders citable blocks into the pack and
why the amendment-epoch path does not. union_citable_blocks in
amendment/state.py and the pack builders in packs/ are the first places to
look; DR-CON-packs-and-token-economy owns the section allocation that may
be dropping them.

SCOPE: an amendment epoch's pack must present its admitted blocks with the
same citable identity the run-start bind gives them. Two guardrails:
(1) CLAUDE.md's standing law -- nothing may penalize an informal or
uncited conjecture, so this adds capability, never a rank or admission
penalty; (2) token economy -- 296 blocks cannot all go in every pack, so
decide and record in SPEC.md how blocks are selected, and make the
selection deterministic and replayable.

CONSIDER ALSO, and decide explicitly rather than by omission: whether
`quote` should be requested, not just permitted. Every evidence_refs entry
in this root carries a block and no quote, so the byte-verifier that exists
has never actually verified a quotation -- 101 EVIDENCE_CITATION_VERIFIED
results all mean "block exists", and EVIDENCE_QUOTE_MISMATCH is 0 because
nothing was quoted.

TESTS: a regression that a conjecture in an amendment epoch can emit an
evidence_refs entry resolving to an admitted block, and one that an uncited
conjecture is neither refused nor down-ranked. GATE: ring while iterating,
full gate at the boundary, docs_verify full, root_sweep zero verdict drift.
Map moves in the same commit. Commit and push at every phase boundary.
```
