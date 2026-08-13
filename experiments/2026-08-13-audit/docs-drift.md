# docs-drift.md — 2026-08-13 audit

| id | dimension | target | gate | verdict | proof file | disposition |
|---|---|---|---|---|---|---|
| DD1 | docs-drift | docs_verify (default, full) | pass | baseline | proof/docs-full.txt | baseline |
| DD2 | docs-drift | docs_verify --audit (toothless-check scan) | pass | baseline | proof/docs-audit.txt | baseline |
| DD3 | docs-drift | docs_verify --links (dangling DR- refs) | pass | baseline | proof/docs-links.txt | baseline |
| DD4 | docs-drift | docs_verify --stale | pass | baseline | proof/docs-stale.txt | baseline |
| DD5 | docs-drift | `docs/ADMISSION_SPEC.md` Status line | pass | baseline | proof/docs-unchecked-claims.txt | baseline |
| DD6 | docs-drift | `docs/MINI_PLAN.md` Status line | pass | drifted | proof/docs-unchecked-claims.txt | parked |
| DD7 | docs-drift | `docs/SMALL_MODEL_COMPATIBILITY.md` header claim | pass | drifted | proof/docs-unchecked-claims.txt | parked |
| DD8 | docs-drift | `docs/RESEARCH_BACKEND.md` Status line | pass | drifted (already errata E20) | docs/ERRATA.md#E20 | baseline (known, already ledgered) |
| DD9 | docs-drift | `docs/EXPERIMENT_PROGRAM_2026-07.md` "nothing has been run" claim | pass | not mechanically checkable | proof/docs-unchecked-claims.txt | noted, not parked |

**Count: 9 findings tabled, 0 `toothless-check`, 0 dangling links, 0
stale stamps, 2 new `drifted`, 1 already-known `drifted` (errata),
1 unverifiable-by-grep noted, 5 `baseline`.**

## Instrument runs (steps 1–4)

**DD1 — `python tools/docs_verify.py`** (reused from B2, identical
instrument against an unchanged tree — see `proof/docs-full.txt`):
`53 documents, 861 checks, 4 workers`, `3 failed`, all
`CON-run-identity.md` git-history checks (matches
`docs/AUDIT_BASELINES.md`'s baseline exactly). **Verdict: baseline.**

**DD2 — `python tools/docs_verify.py --audit`**:
`0 finding(s)` — no toothless (unfalsifiable) checks found.
**Verdict: baseline.**

**DD3 — `python tools/docs_verify.py --links`**:
`0 dangling reference(s), 53 document(s)` — every `DR-` cross-reference
resolves. **Verdict: baseline.**

**DD4 — `python tools/docs_verify.py --stale`**:
`0 document(s) worth re-reading`. **Verdict: baseline.**

## Step 5 — unchecked-claims census (`docs/*.md`, top level only)

37 top-level files in `docs/`. `rg -c 'check:' <file>` is nonzero only
for `docs/ERRATA_EXECUTOR.md` (4 — a process ledger with its own
per-entry verification commands, out of scope for this pass) and
`docs/harness-spec-v1.3.md` (1, a stray literal `check:` inside prose
discussing the map's own convention, not a real executable check —
also out of scope here; it is covered by `dr-audit-spec-drift`
instead). The remaining 35 files have zero `check:` lines and were
each read for a header/Status-line current-state claim
(`proof/docs-unchecked-claims.txt` records the full per-file scan).
Only files asserting a concrete, grep-checkable present-tense claim
were verified — narrative/handover documents dated to a specific past
day, or methodology descriptors, assert nothing about the *current*
tree and were left unrowed, per this worker's "row only the
header/Status claim" scope limit (deep prose audit belongs to
`dr-audit-spec-drift` or a manual tranche).

**DD5 — `docs/ADMISSION_SPEC.md`** line 3: "Status: v1 IMPLEMENTED
(2026-07-28) — all three decided build items are live and tested,"
naming `src/deepreason/admission/` and `tests/test_admission.py`.
Both exist. **Verdict: baseline.**

**DD6 — `docs/MINI_PLAN.md`** lines 3–6: "*Original build status:
BUILT AND LIVE-VERIFIED — see `mini/`. M0–M4 done... the original M2
smoke PASS (... `experiments/results/mini_smoke_report.json`); all
three judge seats certified... (`experiments/results/
mini_seat_certification.json`).*" `mini/` exists (`README.md`,
`minireason/`, `scripts/`), but neither
`experiments/results/mini_smoke_report.json` nor
`experiments/results/mini_seat_certification.json` exists anywhere in
the tree (`find . -iname 'mini_smoke_report*' -o -iname
'mini_seat_certification*'` — zero hits, outside `.git/`). The doc
cites two specific files as its live-verification evidence and
neither is present. **Verdict: drifted.** Disposition: parked — see
`PARKED.md` P-DD6 (this needs the operator to say whether the
evidence moved/was pruned, or the claim itself is stale and should
soften to "was live-verified in the cited tranche, artifacts not
retained").

**DD7 — `docs/SMALL_MODEL_COMPATIBILITY.md`** lines 1–4: "The
`deepreason-small-model-compat-v1` compatibility kernel and its v1.4
advisory extension are implemented." The literal identifier
`deepreason-small-model-compat-v1` (also tried as
`small-model-compat` / `small_model_compat`) does not appear anywhere
under `src/` or `tests/` (`rg -l` — zero hits both forms).
**Verdict: drifted** — either the kernel was implemented under a
different name and the doc's own identifier never got updated, or the
kernel described here was never built under this literal name.
Disposition: parked — see `PARKED.md` P-DD7 (this is a doc-vs-code
identifier mismatch; someone who knows the current small-model-compat
implementation's real name needs to resolve which side moved).

**DD8 — `docs/RESEARCH_BACKEND.md`** line 6: "V6 in-run enablement
remains gated (`V6_RESEARCH_UNAVAILABLE`) and is tranche 2" — this is
`docs/ERRATA.md` **E20**, already found and ledgered (the gate is
conditional in `run_manifest.py`, and the document's own later
sections + a replayed live root show tranche 2 shipped and worked).
Not re-parked here; E20 already records it, and the errata ledger's
own convention is that closed tranche artifacts and prior findings
stay as recorded, not re-opened by a later audit. **Verdict: drifted
(pre-existing, already known).** Disposition: baseline (no new
action; this audit's job is to confirm it is still ledgered, not to
re-find it — confirmed above).

**DD9 — `docs/EXPERIMENT_PROGRAM_2026-07.md`** line 3: "Nothing here
has been run; every experiment below still requires its own
pre-registration file..." This is a negative existential claim
("nothing has run") that cannot be verified by a single targeted grep
against the tree without first extracting and cross-checking every
named experiment in the program (a deep-prose task, out of this
worker's scope per its own "row only the header/Status claim, deep
prose audit is a spec-drift or manual tranche" limit). Noted, not
parked — flagged here so a future pass with the bandwidth for a full
program-vs-`experiments/` cross-check can pick it up if the operator
wants it.

## Outlet note

No `Impulse to fix the doc now` was acted on — both DD6 and DD7 are
parked for a `dr-change-orchestrator` tranche, per this worker's own
Outlets table.
