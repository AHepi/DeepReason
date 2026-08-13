# PARKED.md — 2026-08-13 audit

Every `parked` LEDGER row's fix prompt, ready to paste into an
executor session. This audit made no repo changes outside its own
tranche directory (verified: `git diff --stat` against `origin/main`
touches nothing else) — every prompt below is a proposal, not a
commit.

Where one LEDGER dimension produced many structurally-identical
`parked` rows (`dead.md`'s 69 per-package rows, `spec-drift.md`'s 9
typed-string batches), the prompts below consolidate them into one
paste per actionable decision, cross-referencing the full detail
already tabled in the dimension's own `.md` file — so the operator's
cost stays "one paste," not "one paste per row."

---

## P1 — fix `dr-audit-dead`'s methodology gap (route: `dr-change-orchestrator`)

```
Fix a methodology gap found in the dr-audit-dead skill
(.claude/skills/dr-audit-dead/SKILL.md), found during the 2026-08-13
audit tranche (experiments/2026-08-13-audit/dead.md, LEDGER row D83).

The worker's step 2 only searches for a symbol OUTSIDE its own
defining file (`rg -l -w NAME src/ tests/ scripts/ tools/ | grep -v
<defining-file>`). It never checks whether the symbol is called from
elsewhere WITHIN the same file. Across a full 82-package census (2640
top-level symbols), this produced 836 "candidate-dead" rows, but a
second mechanical check (does the symbol's own file contain more than
the one line where it's defined?) shows 821 of those 836 (98.2%) are
called from elsewhere in their own file — real, wired code, not dead
code. Only 15 have zero occurrences anywhere, including their own
file (dead.md's "15 true candidates" section).

Add a same-file occurrence check as a cheap pre-step, before a symbol
can be declared candidate-dead: `grep -c -w NAME <its own file>` must
also be 1 (only the definition line itself). This is one more grep
per symbol already in the worker's own toolset. Update the GATE and
Outlets sections accordingly. Add a regression fixture (a small
package with one genuinely-dead symbol and one intra-file-only-used
private helper) proving the worker no longer flags the latter.

Goal: candidate-dead's false-positive rate drops from ~98% to near
zero on the next audit run, without changing what counts as evidence
(G3 is preserved — this is a cheaper, more precise mechanical check,
not new judgment).
```

## P2 — review the 15 genuinely unreferenced symbols for deletion (route: `dr-change-orchestrator`)

```
Review 15 symbols found by the 2026-08-13 dr-audit-dead pass
(experiments/2026-08-13-audit/dead.md, "The 15 true candidates"
section) that have ZERO references anywhere in the tree, including
their own defining file — the strongest possible "dead code" signal
this worker's mechanical scans can produce:

last_json_line (src/deepreason/brain/log.py)
retrieval_metrics (src/deepreason/brain/metrics.py)
_cmd_check_proof, _cmd_code, _cmd_simulate (src/deepreason/cli/main.py
  -- confirmed genuinely unwired: main()'s if/elif args.command
  dispatch chain has no "check-proof"/"code"/"simulate" branch)
_slug, _fresh, _first_line (src/deepreason/easy.py)
suppressible_lineage_exemplars (src/deepreason/jolts.py)
_document_excerpt, alias_references (src/deepreason/llm/packs.py)
domain_log_input (src/deepreason/rules/guards/anti_relapse.py)
refl (src/deepreason/rules/refl.py)
materialize_run_config (src/deepreason/run_manifest.py)
record_trigger_decision (src/deepreason/views/jolt_signals.py)

For each: confirm it is genuinely unused (not a public API surface,
not referenced by name in a config/registry string this census's
scans might miss), then either delete it with a regression test
proving nothing broke, or leave it with a one-line comment explaining
why it must stay (e.g. a deliberately-unused stub). Full per-symbol
proof (both empty scans) is in experiments/2026-08-13-audit/proof/
dead-<package>-<symbol>.txt.
```

## P3 — fix `root_sweep.py`'s CLI vs `dr-audit-broken`'s documented invocation (route: `dr-change-orchestrator`)

```
experiments/2026-08-13-audit/broken.md (LEDGER row B6) found that
.claude/skills/dr-audit-broken/SKILL.md step 5 documents
`timeout 900 python tools/root_sweep.py > proof/broken-sweep.txt`
(stdout redirection), but tools/root_sweep.py (unchanged since
2026-08-11, commit 48506b4e0) requires sys.argv[1] as an explicit
output-path argument and crashes with IndexError if invoked as
documented.

Either fix the skill's documented command to
`timeout 900 python tools/root_sweep.py proof/broken-sweep.txt`, or
give root_sweep.py an argparse default that also accepts stdout
(operator's call which is more correct going forward). Whichever way,
also separately consider (not required for this fix, a second,
larger question): root_sweep.py accumulates every root's line in
memory and writes output only once, after the full loop -- a hang on
one root (the known experiments/live_tri_2026-07-27/
run-c5ab654afd1b4aa131aede83bdca0f03 hang, still live) loses ALL
roots' output, not just the hanging one. A future tranche could make
it write incrementally so a hang on one root doesn't erase results
for the other ~100.
```

## P4 — `docs/MINI_PLAN.md`'s Status line cites two missing evidence files (route: `dr-change-orchestrator`)

```
experiments/2026-08-13-audit/docs-drift.md (LEDGER row DD6) found
docs/MINI_PLAN.md's header Status claim ("Original build status: BUILT
AND LIVE-VERIFIED... the original M2 smoke PASS...
experiments/results/mini_smoke_report.json... all three judge seats
certified... experiments/results/mini_seat_certification.json") cites
two files as its live-verification evidence. Neither exists anywhere
in the tree (find . -iname 'mini_smoke_report*' -o -iname
'mini_seat_certification*' -- zero hits outside .git/).

Determine which: (a) the evidence files were produced but never
committed / were later pruned -- if recoverable, commit them or point
the doc at wherever the real evidence now lives; or (b) the claim was
always aspirational/from an ephemeral run and the Status line should
soften to something like "was live-verified in the cited tranche;
artifacts not retained in this tree." Update docs/MINI_PLAN.md
accordingly; this is a doc-only fix (mini/ itself does exist and is
not in question).
```

## P5 — `docs/SMALL_MODEL_COMPATIBILITY.md`'s named kernel identifier not found in code (route: `dr-change-orchestrator`)

```
experiments/2026-08-13-audit/docs-drift.md (LEDGER row DD7) found
docs/SMALL_MODEL_COMPATIBILITY.md's header ("The
deepreason-small-model-compat-v1 compatibility kernel and its v1.4
advisory extension are implemented") names a literal identifier,
deepreason-small-model-compat-v1, that appears nowhere in src/ or
tests/ (rg -l 'deepreason-small-model-compat-v1' and rg -l
'small-model-compat|small_model_compat', both zero hits).

Find whoever knows the current small-model-compatibility
implementation's real name (it likely exists under different
terminology -- the surrounding doc describes RunManifest compilation,
EndpointLease binding, wire-contract isolation, bounded repair
attempts, all of which sound implemented) and either update the doc's
header to the real identifier, or confirm the kernel was never built
under any name and the header needs a stronger correction.
```

## P6 — spec term `ContextRequest` vs code `ContextRequestV1` (route: `dr-change-orchestrator`)

```
experiments/2026-08-13-audit/spec-drift.md (LEDGER row SD1) found the
harness spec series names `ContextRequest`, but every code site
(conjecture_turn.py, scratch/conjecture.py, llm/wire.py, rules/conj.py,
invariants.py, harness.py) uses `ContextRequestV1`. Decide: does a
future spec amendment spell the versioned name, or is
`ContextRequest` meant as the version-agnostic concept name (in which
case this is a documentation nit, not drift)? Either way, note the
resolution in the next harness-spec amendment (append-only) rather
than editing existing spec text.
```

## P7 — spec term `codec:json` not found in code (route: `dr-change-orchestrator`)

```
experiments/2026-08-13-audit/spec-drift.md (LEDGER row SD3) found
harness-spec-v1.3.md section 10 describes informal-domain
`eval:program` commitments where "the candidate's content is
`codec:json` conforming to..." — but no call site anywhere under src/
sets or checks a "json" codec value (Artifact.codec exists, defaults
to "utf8", proof in experiments/2026-08-13-audit/proof/
spec-orphan-detail.txt). Confirm with whoever knows the informal-domain
skeleton-wf path whether this shipped under a different name/field, or
was never built, and either point to the real mechanism or flag the
spec section as aspirational/not-yet-implemented via a new amendment.
```

## P8 — spec term `novel-case` not found in code (route: `dr-change-orchestrator`)

```
experiments/2026-08-13-audit/spec-drift.md (LEDGER row SD5) found
harness-spec-v1.3.md section 10.5 describes "novel-case" criteria for
informal problems (Lakatos-style novel-fact commitments) — no form of
novel-case / novel_case appears anywhere under src/. Confirm whether
this shipped under an unrelated name, or was never built, and record
the answer in a new (append-only) amendment rather than editing
existing spec text.
```

## P9 — 3-way spelling drift on the `workflow-resume-decision` typed record (route: `dr-change-orchestrator`)

```
experiments/2026-08-13-audit/spec-drift.md (LEDGER row SD7) found
THREE different spellings of the same typed control record across the
spec and the tree, none matching the other two:
- spec (harness-spec-v1.5-amendment.md): workflow-resume-decision.v1
- code (storage/objects.py, workflow/replay.py, harness.py):
  "workflow-resume-decision"  (no .v1 suffix)
- code (workflow/models.py): "workflow.resume-decision.v1"  (dot
  before "resume", hyphen inside "resume-decision", .v1 suffix)

This is independent of the spec question -- it's a real naming
inconsistency inside the tree itself. Pick one canonical spelling and
conform all three code sites to it (with a migration/compat note if
any committed run root's log carries the old spelling verbatim -- the
append-only record must stay replayable), then update the spec via a
new amendment to match.
```

## P10 — CLI flags spec-silent (34 flags, route: `dr-change-orchestrator`)

```
experiments/2026-08-13-audit/spec-drift.md (LEDGER row SD8) found 34
of 75 CLI flags in src/deepreason/cli/main.py have no mention anywhere
in the harness-spec-*.md series: --allow-partial, --api-key-env,
--attached-evidence, --blind-same-model-judges, --capsule, --category,
--concurrency, --context-window-tokens, --control-plane-policy,
--credential-env, --criticism-seat, --dry-run, --engine-profile,
--expected-manifest-digest, --interval, --judge-family,
--maximum-completion-tokens, --model-revision, --no-browser,
--output-profile, --pack-profile, --production-contracts,
--provider-profile, --reshape-question, --retrieved-at,
--rubric-policy, --run-input-digest, --shallow, --single-model,
--title, --token-budget, --top-k, --upto, --workload-profile.

Decide, per spec-drift.md's own framing: is this expected (these flags
belong to the V6/qualification/judge-seats generation, documented
elsewhere, and harness-spec-*.md is intentionally scoped to a
different, earlier surface), or a genuine documentation gap that needs
a new amendment? If the latter, draft an append-only amendment
covering the CLI surface; do not edit existing spec text.
```

## P11 — config fields spec-silent (51 fields, route: `dr-change-orchestrator`)

```
experiments/2026-08-13-audit/spec-drift.md (LEDGER row SD9) found 51
of 75 top-level Config fields in src/deepreason/config.py have no
mention anywhere in harness-spec-*.md (full list in that row / in
experiments/2026-08-13-audit/proof/tree-config-fields.txt). Same
decision as P10: expected (V6-era surface documented elsewhere) or a
genuine gap needing a new amendment. If the latter, draft it
append-only.
```

## P12 — typed error/refusal strings spec-silent (118 strings across 7 feature areas, route: `dr-change-orchestrator`)

```
experiments/2026-08-13-audit/spec-drift.md (LEDGER rows SD10-SD16)
found 118 of 122 typed refusal codes in run_manifest.py/preparation.py
have no mention in harness-spec-*.md. The full list is batched by
feature area in spec-drift.md: manifest-generation V3-V6 (28 codes),
preparation/managed-run (20), run-input/manifest-file (11),
routing/bridge presentation (9), credential/path-safety (9),
judge-family/seats (6), and a 35-code remainder (scratch/embedder,
admission/qualification, public API defaults, misc).

This audit's read: these cluster almost entirely around the "V6"
RunManifest/policy generation and wire-contract series that CLAUDE.md
itself says is a SEPARATE documentation series from harness-spec-*.md
-- so a high spec-silent rate here may be correct-by-design rather
than drift. This audit cannot determine from the tree alone whether
that separate series (if it exists as committed docs, not just
CLAUDE.md's mention of it) actually covers this surface. Please
either point to where V6's typed refusals ARE documented (closing this
out as a false alarm), or confirm harness-spec-*.md should be extended
to cover them (in which case: draft append-only amendments, batched by
the 7 feature areas above, not 118 individual entries).
```

## P13 — adversarial test for "a generation seat cannot skip criticism" (route: `dr-change-orchestrator`)

```
experiments/2026-08-13-audit/goal-trace.md (LEDGER row L2) traced the
operator design law "Seats change how content is GENERATED, never what
counts as EVIDENCE" (CLAUDE.md, the modes/packages guardrail). Real
infrastructure exists (seat_bindings.py's generation/criticism
separation, tested in test_seat_bindings.py + 4 more files), but no
test pins the law's own specific claim -- "no seat, mode, or package
may let a generation seat's prose skip criticism" -- as an adversarial
invariant. The law's own citation, docs/proposals/
ROLE_SEAT_SEPARATION_PLAN.md's "S7 -- packages" rung, is explicitly
sequenced after S3-S6 and not yet built.

Add a regression test that tries to construct a seat/mode
configuration and asserts the harness cannot be made to skip
criticism for generated content -- proving the law rather than just
the seat-binding plumbing around it. If S7 ("packages") lands first,
the test belongs at that boundary instead; this prompt doesn't
prescribe which comes first, only that neither exists yet.
```

## Note on L5 (not a new prompt)

`goal-trace.md` (LEDGER row L5) found "All configurations should be
allowed" partially-enforced: ~13 sites converted, ~20 more
census-complete but not code-complete. This is **already parked** by
the delivering tranche itself
(`experiments/2026-08-12-change-all-configs-allowed/PARKED.md` P1,
routed `dr-change-orchestrator`). This audit confirms P1 is still open
— no later tranche has closed it — rather than creating a duplicate
prompt. If picking this up, use that tranche's own P1 text, not a new
one.
