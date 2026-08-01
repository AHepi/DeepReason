# Delivered: implement amendment epochs

Branch: `claude/amendment-epochs-om0ztb` (pushed, tree clean)

Commits:

- `0a946726` — implementation (all four tranches)
- `2acddb67` — first-pass validation, verdict FAIL
- `a78ed1b6` — operator ruling applied: spec amended, R15 gap fixed,
  second-pass validation PASS
- this commit — RESULTS segment 8 and DELIVERY.md

## What changed

A stopped DeepReason run can now take new evidence and a new central
question without losing what it already established. `deepreason --root
ROOT amend [--attach FILE ...] [--reshape-question "TEXT"]` appends one
typed epoch to the same root: the attached files become their own
dossier with its own digest and its own import-role source records; the
new question enters as a seed problem whose provenance names the
question it supersedes; and a `run-amendment.v1` line chains the two
behind a declared event fence. `deepreason --root ROOT continue` then
resumes the same root, and the reshaped question takes the first cycle
on the scheduler's existing seed-priority guarantee. The same operation
is exposed to agents as the MCP tool `amend_run`, listed in
`get_capabilities` under a new `amendment` area.

Nothing is edited. Epoch 0's manifest, run input, and dossier keep their
exact canonical bytes; the ledger grows only by suffix; the old question
keeps its rivalries, its accepted positions, and its status. New code
lives in `src/deepreason/amendment/` (`models.py`, `state.py`,
`apply.py`); the durable shape is `run-amendments.jsonl` for the
committed chain and `run-epochs/NNN/` for each epoch's complete
documents. Readers were made epoch-aware additively — the citation
checker unions the bound dossiers, the conjecture pack draws from every
source bound at or before the current epoch, `verify_root` validates the
chain and runs its attached-evidence checks per fence window, and
terminal authority authorizes exactly an amendment's own application
events past a horizon. An unamended root yields one window covering the
whole log, so its validation is unchanged.

Writes are fail-closed in a fixed order — stage the epoch documents,
apply the ledger chain, commit the chain line. A crash leaves a staged
epoch with no committed line; `continue` refuses
`CONTINUE_AMENDMENT_INCOMPLETE` and `verify_root` reports it. Recovery
then splits on whether that epoch reached the ledger: if nothing was
applied, a different amendment supersedes it outright; if events were
applied, they belong to that epoch, so it is completed and the refusal
names the route to the next one.

How it is proven: `tests/test_amendment_epochs.py` (15 cases) covers the
four fixtures the spec names plus a real `continue_run` across the
fence, chained second epochs, both crash-recovery shapes, and the CLI
and MCP surfaces. Full gate **3128 passed, 0 failed** (baseline 3110).
`verify_root` over all fifteen committed run roots in
`experiments/live_research_2026-07-29/` is byte-identical to the
pre-change commit — known-good roots still clean, defect-era findings
all preserved, none masked.

**Not exercised live.** No amendment has been applied to any campaign
root; every claim above rests on offline regression. See RESULTS.md
segment 8 for what that leaves unproven.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "`deepreason amend [--attach ...] [--reshape-question ...] [--root ROOT]`" | superseded-by R1a | — |
| R1a | "correct the spec's usage line to the CLI's global --root" | done | `a78ed1b6`, VALIDATION S1 |
| R2 | "`deepreason continue`" resumes afterwards | done | `0a946726`, VALIDATION S2, S11 |
| R3 | "refuses (typed) unless the run stands at a typed terminal stop" | done | `0a946726`, VALIDATION S3 |
| R4 | "appends ONE atomic chain of typed events to the SAME root" | done | `0a946726`, VALIDATION S13 |
| R5 | "each `--attach` file is admitted as a NEW dossier ... with its own digest and its own attached-source records" | done | `0a946726`, VALIDATION S4 |
| R6 | "Dossier-1 is never touched ... remain byte-checkable forever" | done | `0a946726`, VALIDATION S5 |
| R7 | "citation checker consults the UNION of dossiers" | done | `0a946726`, VALIDATION S6 |
| R8 | "registers a NEW problem whose provenance is `{trigger: seed, from: [old-question-id]}`" | done | `0a946726`, VALIDATION S7 |
| R9 | "not deleted, not edited, not re-statused" | done | `0a946726`, VALIDATION S7 |
| R10 | "seed-priority ... first claim on the continuation budget" | done | `0a946726`, VALIDATION S8 |
| R11 | "`run-amendment.v1`, carrying [five named fields]" | done | `0a946726`, VALIDATION S9 |
| R12 | "successor manifest ... with the run-input reference and dossier list extended" | superseded-by R12a | — |
| R12a | "manifest copied verbatim, successor run-input carried by the amendment record" | done | `a78ed1b6`, VALIDATION S10 |
| R12b | "Park the successor-manifest digest materialization in PARKED.md" | done | `a78ed1b6`, PARKED.md P1 |
| R13 | "`continue` then resumes the same root ... against the union of old positions and new evidence" | done | `0a946726`, VALIDATION S11 |
| R14 | "append-only is preserved — new events behind a fence" | done | `0a946726`, VALIDATION S12 |
| R15 | "typed partial chain that recovery refuses to continue past (fail-closed)" | done | `0a946726`, VALIDATION S13 |
| R15a | "supersede exactly when it has applied no ledger events yet; keep the fail-closed refusal once events exist" | done | `a78ed1b6`, VALIDATION S13 |
| R16 | "piecewise validation ... `verify_root` walks the chain" | done | `0a946726`, VALIDATION S14 |
| R17 | "strictly additive — zero status flips" | done-with-assumption A5 | `0a946726`, VALIDATION S7 |
| R18 | "dossiers are immutable and cumulative" | done-with-assumption A3, A4 | `0a946726`, VALIDATION S5, S6 |
| R19 | "Run identity: unchanged" | done | `0a946726`, VALIDATION S12 |
| R20 | T1: record + state application + `verify_root` piecewise validation | done | `0a946726`, VALIDATION S9, S14 |
| R21 | T2: supplemental admission; citation checker unions dossiers | done | `0a946726`, VALIDATION S4, S6 |
| R22 | T3: `amend` CLI + typed refusals + `continue` fence check | done | `0a946726` + `a78ed1b6`, VALIDATION S1, S3, S13 |
| R23 | T4: MCP `amend_run` beside `continue_run` | done | `0a946726`, VALIDATION S15 |
| R24 | four named regression fixtures (a)-(d) | done | `0a946726` + `a78ed1b6`, VALIDATION S16 |

No requirement is deferred and none is not-done. Two are superseded by
the operator's own ruling, and both replacements are done.

## Assumptions the operator may override

Three assumptions remain live — behavior chosen where the spec was
silent, not requirements. Each is cheap to reverse now and expensive
later, so they are stated rather than buried.

- **A3** — the manifest's frozen attached-evidence budget binds the
  UNION of all bound dossiers, not the newest one alone. A run whose
  budget allows 8 sources therefore allows 8 across every epoch
  combined, not 8 per amendment.
- **A4** — a dossier's `problem_ref` belongs permanently to the question
  that admitted it, so a question-only amendment (no `--attach`)
  inherits its parent's dossier rather than minting a copy under the new
  question's id. The union deduplicates it, so the evidence is not
  double-counted.
- **A5** — the reshaped problem's criteria are the parent problem's
  criteria carried verbatim. A reshaped question is judged by the same
  standards as the question it supersedes unless the operator says
  otherwise.

Two earlier assumptions (A1: the manifest's frozen run-input could be
made per-epoch; A2: supersession of a staged epoch is always unsound)
were resolved by the R12a and R15a rulings and are no longer carried.

## Parked (not done, not promised)

**P1 — Materialize a distinct successor manifest digest per amendment
epoch.** Today the manifest is copied verbatim
(`successor_manifest_digest == parent_manifest_digest`) and the epoch's
superseding run-input is named by the amendment record. The alternative
makes the manifest itself the authority for which input an epoch runs
under. It is not a small change: the run's `(manifest digest,
run_input_digest)` pair is bound for a root's whole life by the
controller process state (`workflow/state.py`), the capability
transition chain (`capabilities/state.py`, a frozen surface), terminal
authority, continuation history, the qualification report, and ~20
identity checks in `invariants.py`. A second digest mid-root would
invalidate the authority chain of the epoch below the fence rather than
extend it.

What would justify unparking it: a concrete need the record-carried
design cannot serve — an amendment that must change routing, budgets, or
capability policy, not just the question and the evidence. Nothing
currently asks for that. If unparked it should carry its own goal, its
own frozen-surface approval, and a before/after `verify_root` sweep over
every committed root as its acceptance check.

Offered as a candidate next tranche. Not promised.

## Standing gap, for the record

The capability is proven correct and unproven useful: no amendment has
been applied to a live campaign root, and no live model has reasoned
across an amendment fence. RESULTS.md segment 8 records what that leaves
open — whether a reshaped question outperforms a fresh root, whether
glm-5.2 cites older dossier blocks once newer ones sit beside them, and
whether the cycle-0 seed win survives a frontier carrying real
discrimination and connection spawns. A live amendment run is the
natural next tranche.

## Addendum (post-delivery): PARKED P2 unparked and fixed

Found while answering an operator question about the admission path,
after the tranche was delivered: re-attaching a file already admitted to
the run was accepted by `amend` and then reported as a violation by
`verify_root`. Operator ruled (R25) that `amend` must reject it up front.

`amend` now refuses before any parse, blob write, or staging, with
`AMEND_SOURCE_ALREADY_ADMITTED`, naming the path and the source id it
duplicates. The check spans every epoch's dossier, not just the original.
Refusal is whole-invocation rather than admit-minus-duplicates, matching
the rule `collect_attachment_inputs` already applies to an unreadable
path — silently admitting a subset would misrepresent the evidence base.
The cross-epoch uniqueness rule in `verify_root` was left alone; it was
never wrong, it was correctly reporting a record `amend` should not have
produced.

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R25 | "Amend needs to reject up front" | done | PARKED.md P2 resolution; `test_amend_refuses_a_source_already_admitted_to_this_run`, `test_amend_refuses_content_admitted_by_an_earlier_amendment` |

Full gate after the fix: see the commit message. Parked list is now P1
only.

## Addendum 2 (post-delivery): coverage gaps closed (R26), live run blocked (R27)

A post-delivery review of my own work found three real gaps and some dead
API. Operator ruled: close all three, and attempt a live run.

**Gap 1 — the detectors had never fired.** Every existing test asserted a
clean root; none asserted that a *corrupted* amendment chain is caught.
`tests/test_amendment_chain_integrity.py` (36 cases) now corrupts exactly
one thing at a time — unreadable chain, non-canonical bytes, forged
digest, foreign manifest anchor, broken parent link, stalled fence,
out-of-order sequence, missing or deleted epoch documents, swapped
dossier, foreign epoch manifest, tampered source blob, a record naming a
dossier the epoch lacks, a record naming an unregistered question — and
requires `verify_root` to name each. All ten record-model rejection rules
are covered too. Amendment-module coverage 86% -> 95%; the record model
84% -> 100%.

Two of those tests were written expecting one behavior and found another.
Forging a staged record does not reach `AMEND_PENDING_CONFLICT`: it
breaks the authority that let the staged epoch's events cross the
terminal horizon, so `amend` fails closed at `AMEND_NOT_AT_TERMINAL`.
Sound, but the message pointed at the stop rather than the staged epoch,
so `_require_terminal_stop` now names the staged epoch and the terminal
detail code.

**Gap 2 — amendment beside a bridge episode.** One root now carries a
successfully composed grounded bridge AND an amendment past the same
terminal horizon; terminal authority, `verify_root_report` and
`verify_root` all stay valid, and the bridge episode still stands. The
negative case is the important half: planting an ordinary conjecturer
artifact past the horizon on an amended root still collapses authority
with `TERMINAL_POST_HORIZON_EVENT_UNAUTHORIZED`, so widening the rule for
amendments did not make it a general licence.

**Gap 3 — three chained epochs**, with four dossiers, four questions, and
a corrupted MIDDLE epoch still detected rather than masked by its
well-formed neighbours.

**Dead exports removed.** `epoch_fences`, `epoch_for_event_seq`,
`current_manifest`, `current_run_input`, `current_dossier` deleted;
`epoch_manifest_path` made private. Public surface 23 -> 18 names, every
one with a caller or a test.

Full gate: **3167 passed, 0 failed**.

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R26 | "Do all 3" | done | VALIDATION S17-S21 |
| R27 | "If you judge a live run might help, do it" | **not done — blocked** | VALIDATION "Live run attempt": HTTP 401 from the provider |

**R27 is the one thing I could not deliver.** I judged the live run worth
doing and tried to run it. The supplied Ollama key returns HTTP 401
`{"error":"Unauthorized"}` on `/v1/chat/completions`. I ruled out the
proxy (header echoes through byte-identical, no relay failures), the
endpoint and model name (`glm-5.2` is listed), and a misread of a healthy
key (`/v1/models` returns 200 for a deliberately bogus key too, so that
200 proves nothing; the bogus key and the supplied key give the identical
401 on inference). The key is valid-shaped but not entitled to inference.
The ladder is ready and needs one working credential plus ~30-40 minutes.

The standing gap from RESULTS segment 8 is therefore unchanged: amendment
epochs remain proven correct and unproven useful.
