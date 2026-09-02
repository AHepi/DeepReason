# Validation — live full-judge seat/configuration census

## Verdict: FAIL

The campaign implementation and its 41-test regression file are green, but
delivery does not pass the repository's authoritative gates. The full
repository test command has 12 failures, the documentation verifier has 7
full-check failures plus 1 audit and 2 coverage findings, and the frozen live
configuration cross is still entirely pending. No baseline failure is waived,
no stopped prefix is renamed exhaustive, and no campaign source is changed to
manufacture a pass.

This is a release verdict, not a claim that the nine live findings are invalid.
Those findings remain immutable, typed evidence from the shipped defended-trial
path.

## Frozen identity and scope

| Item | Exact value |
|---|---|
| Branch | `codex/live-full-judge-seat-matrix-20260901` |
| Validation input checkpoint | `8f566fec96f3e42259983ced09932423ded850cd` |
| Frozen base | `00f10dde8c734e2f874358f9e2a375bb63aa4a35` |
| Authenticated catalog | 18 included models; 1 typed Kimi-K3 exclusion |
| Catalog digest | `77a5a11f946b21e82488ddc66473f1bfa50c6bd6c394fd420ad1baacc81754b4` |
| Seat-domain file digest | `1be915b5cccb5164b17691cb6602fa630d26603064d0096f4b3600fd2975442d` |
| Full-cross file digest | `148793d2bd570869a5e2be7b1d1a3845c1fb69095ac987e4396f3c99b9d9322e` |
| Frozen-surface contact | none; verdict `CLEAR` |
| Code/test budget | 4,073 inserted lines of 5,000; `WITHIN` |

The finite frozen cross independently varies each active seat's model,
profile, output mode, output mechanism, and safe reasoning value, along with
the registered split protocol, judge cardinality, optional variator, and
paraphrase count. Arbitrary future models, role counts, strings, numbers,
policy dictionaries, and provider fields remain expressly open dimensions.

## Acceptance-output ledger

| Gate or command | Exact result | Disposition |
|---|---|---|
| Preregistration file check | `PREREG.md:231:## Registered outcomes`; SHA-256 `33afd81aac209cdf280faf7bd59ff0a194d2abcf8794cd620f61172ab0e77ae6` | PASS |
| Matrix-domain JSON and oracle | `STRUCTURAL_COUNT=452 UNIQUE=452`; fixture `CATALOG_MODELS=22 JUDGE_PAIRS=484 CORE_COURTS=10648 NO_VARIATOR=234256 WITH_VARIATOR=5153632 TOTAL=5387888` | PASS |
| Full-cross fixture oracle | `SEAT_TUPLES=1584 JUDGE_2=149596687470624768 JUDGE_3=236961152953469632512 TOTAL=237110749640940257280` | PASS |
| Exact offline structural terminal set | `STRUCTURAL_EXPECTED=452 STRUCTURAL_TERMINAL=452 DUPLICATE=0 MISSING=0` | PASS |
| Defended-court soak | `SOAK_VERDICT=PASS CASE=judge-matrix CYCLES=8` | PASS |
| Authenticated reasoning probes | `EXPECTED=54 TERMINAL=54 USABLE=41 PROVIDER_INDETERMINATE=13 PEAK_IN_FLIGHT=3 FORBIDDEN_REASONING=0 SECRET_LEAK=0` | PASS as a complete probe census; indeterminate rows do not become refusals |
| Serial live smoke | `TERMINAL=1 POSSIBLE=1 CONFIGURATION_REFUSED=0 PROVIDER_INDETERMINATE=0 PENDING=1994543 PEAK_IN_FLIGHT=1` | PASS |
| Ordered-judge-pair live prefix | `EXPECTED=324 TERMINAL=9 POSSIBLE=8 IMPOSSIBLE=1 PROVIDER_INDETERMINATE=0 INTERRUPTED=0 PENDING=315 DUPLICATE=0 PEAK_IN_FLIGHT<=3` | Valid stopped prefix; incomplete |
| Campaign regression | `41 passed in 8.37s` | PASS |
| Actual-file blast-radius gate | frozen contacts `[]`; frozen-adjacent contacts `[]`; verdict `CLEAR` | PASS |
| Cumulative diff budget | `4073/5000 WITHIN` | PASS |
| Branch isolation | correct branch; 0 merge commits since frozen base; local and remote checkpoint matched; cached `origin/main` unchanged | PASS |
| Full repository test gate | `12 failed, 4618 passed, 26 skipped in 675.16s (0:11:15)` | **FAIL** |
| Documentation verifier | full: 7 failed; audit: 1 finding; links: 0 dangling; coverage: 2 findings; stale: 46 documents | **FAIL** |
| Exact-byte credential scan | `SECRET_SCAN=PASS LEAK_FILES=0` | PASS at the recorded live and result checkpoints; rerun before final handoff |

The full command outputs retained by the tranche include
`proof/all-matrix-tests-green.txt`, `proof/soak-green.txt`,
`proof/reasoning-probes.json`, `proof/summarize-green.txt`,
`proof/full-repository-tests-fail.txt`, and `proof/docs-verify-fail.txt`.

## Live result and resume position

| Ordered projection | Expected | Terminal | Pending |
|---|---:|---:|---:|
| Judge pairs | 324 | 9 | 315 |
| Core courts | 5,832 | 9 | 5,823 |
| No variator | 104,976 | 9 | 104,967 |
| Seat only | 1,994,544 | 9 | 1,994,535 |

The nine terminal judge-pair rows comprise eight `trial_outcome` results and
one deterministic `SECOND_JUDGE_FAMILY_REQUIRED` configuration refusal. There
are no provider-indeterminate or unexpected-error terminal rows in that live
prefix. Its next row is ordinal 9,
`sha256:8aa2e4b74b70124d7511bea92162ceb0edfeddca14d64934522d64a9b7653ae2`,
with judge 1 `kimi-k2.6`.

The independently ordered superseding full cross is:

```text
EXPECTED=71141539390075109376 TERMINAL=0 POSSIBLE=0 IMPOSSIBLE=0
PROVIDER_INDETERMINATE=0 UNEXPECTED_ERROR=0 INTERRUPTED=0
PENDING=71141539390075109376 NEXT_ORDINAL=0
NEXT_CASE_ID=sha256:1b50183d2639aadf2f05611d440a9036c564a7c9b537e2be93410a0bc5b4c25e
PEAK_IN_FLIGHT<=3 SCOPE=full-cross
```

`Configuration refused` means the shipped compiler or runtime rejected a
frozen configuration deterministically before a provider answer could decide
it. `Provider indeterminate` means transport, timeout, model-silence, parse, or
schema evidence could not establish configuration impossibility. A `trial
outcome` is a semantic result from the shipped path, not a model score.

## Requirement reconciliation

| Requirement | Status | Evidence and limit |
|---|---|---|
| R1 — design tests using the authorized API credential | MET | The campaign has red/green test history, a 41/41-green regression file, authenticated probes, and live typed receipts. Credential bytes never enter an argument, tracked artifact, diagnostic, or digest. |
| R2 — test all seat configurations on the full judge trial | NOT MET | The exact ordered queue exists, but only 9 of 324 judge-pair-prefix rows are terminal; the full cross is 0 of 71,141,539,390,075,109,376. |
| R3 — no observe-only | MET | Every executable manifest uses explicit `defended_trial`; observe-only is a pre-dispatch campaign-integrity failure. No observe-only request was dispatched. |
| R4 — exclude only Kimi K3 | MET | The authenticated catalog contains 18 included ids and one normalized typed `KIMI_K3_FORBIDDEN` exclusion. Kimi K2 remains included. |
| R5 — do not use thinking high | MET | Probes used explicit `none`, `low`, and `medium`; full trials used explicit `low`. Forbidden high/max/xhigh count is zero and no omitted/default reasoning road was dispatched. |
| R6 — check Ollama documentation | MET | First-party OpenAI compatibility, thinking, GLM-5.3, and GLM-5.3-Flash semantics were cited before live completion and translated into explicit wire-field tests. |
| R7 — preserve GLM-5.3 none/trace semantics | MET | `none` remains a requested wire value, never an assertion that trace is absent. The probe records trace-field presence, length, and digest exactly as returned; the observed GLM-5.3 `none` row had no populated trace field and was not reinterpreted. |
| R8 — at most three concurrent calls | MET | One coordinator and a shared bounded semaphore cover all endpoint calls; live and probe evidence reports peak 3 or less, and the fake-endpoint regression rejects four. |
| R9 — try to test everything | INCOMPLETE | The frozen exact membership and resumable order prevent sampling or silent pruning, but the enormous pending set remains unexecuted. |
| R10 — test all configurations as well | NOT MET | The superseding cross is immutable and directly addressable, but it has zero terminal rows. No prefix is presented as completion. |
| R11 — report what is possible and impossible | PARTIAL | The observed prefix reports 8 possible and 1 deterministic refusal, with 315 judge-pair rows pending. Unrun rows have no inferred classification. |
| R12 — use alphaXiv while exploring options | MET | The preregistration used alphaXiv only as advisory coverage input; it did not introduce ranking, pruning, or an optimization target. No later execution-only step explored new design options. |

## Standing-constraint reconciliation

| Constraint | Status | Evidence |
|---|---|---|
| C1 — never merge with main | MET | The work remains on the isolated campaign branch; the merge count since the frozen base is zero. No merge, rebase, pull, or main update occurred. |
| C2 — token use need not be minimized | MET | The campaign does not prune membership for cost. Per-request output/context bounds remain explicit safety and reproducibility controls. |
| C3 — GitHub damage is reversible | MET | Work is checkpointed only on the isolated branch; source commits bind live receipts, and no historical result root is rewritten. |
| C4 — never persist credential material | MET | The key is environment-only and exact-secret scanning reports no matching tracked or runtime file. No value or hash is recorded here. |
| C5 — formalism does not outrank valid prose | MET | Secret-scanned prose receipts are retained separately from parse/schema outcomes; a mechanical failure becomes provider-indeterminate, not epistemic invalidation. |
| C6 — no ranking or optimization | MET | The queue is an exact census. No score, leaderboard, eliminator, heuristic reduction, or statistical tightening was added. |
| C7 — exploration remains open | MET | Observed outcomes do not remove future rows. Every frozen row remains addressable and pending until it has one terminal receipt. |
| C8 — modular and human-readable | MET | Frozen JSON domains, immutable case ids, typed receipts, a constant-time summarizer, and prose reports separate machine identity from operator explanation. |

## Blocking repository-test gate

The exact failing nodes are preserved in
`proof/full-repository-tests-fail.txt`. They span the installed campaign CLI,
qualification-subject digest, brokered/default simulation behavior, the single
run path, public v6 defaults, and trusted workload/formal checks. None is in
`tests/test_live_full_judge_seat_matrix.py`. Their apparent pre-existing or
environment-sensitive character does not make them green; the authoritative
gate remains blocking.

## Blocking documentation gate

The full verifier checked 71 documents and 1,297 checks. Its seven failures
were an unparseable `SEAM-llm-x-rules.md` check, a nonzero historical
transport-failure census, two qualification/default test failures, one missing
historical remote ref, and a missing `bc` executable. Audit repeats the
unparseable check. Links are clean. Coverage reports two unnamed enforcement
sites: `src/deepreason/amendment/apply.py` and
`src/deepreason/informal/trial.py`.

Every stale row is disposed below with the same explicit result: **unresolved,
not changed by this tranche, and blocking a PASS until a separately scoped map
maintenance/revalidation tranche reads and either refreshes or clears it.**
The campaign touched no map document or shipped source, so silently updating
these rows here would exceed scope.

| Stale document | Disposition |
|---|---|
| `CON-authority.md` | unresolved; separate map revalidation required |
| `CON-capability-lifecycle.md` | unresolved; separate map revalidation required |
| `CON-conjecture-kinds.md` | unresolved; separate map revalidation required |
| `CON-conjecture-source.md` | unresolved; separate map revalidation required |
| `CON-criticism-source.md` | unresolved; separate map revalidation required |
| `CON-packs-and-token-economy.md` | unresolved; separate map revalidation required |
| `CON-run-identity.md` | unresolved; separate map revalidation required |
| `CON-scheduler-ranking.md` | unresolved; separate map revalidation required |
| `CON-schools.md` | unresolved; separate map revalidation required |
| `CON-seats.md` | unresolved; separate map revalidation required |
| `CON-successor-questions.md` | unresolved; separate map revalidation required |
| `INV-evidence-channels.md` | unresolved; separate map revalidation required |
| `INV-frozen-surfaces.md` | unresolved; separate map revalidation required |
| `INV-signal-contract.md` | unresolved; separate map revalidation required |
| `REC-change-a-seam.md` | unresolved; separate map revalidation required |
| `SEAM-adjudication-x-authority.md` | unresolved; separate map revalidation required |
| `SEAM-bridge-x-llm.md` | unresolved; separate map revalidation required |
| `SEAM-calculus-x-rules.md` | unresolved; separate map revalidation required |
| `SEAM-capabilities-x-rules.md` | unresolved; separate map revalidation required |
| `SEAM-evaluation-x-ontology.md` | unresolved; separate map revalidation required |
| `SEAM-evaluation-x-rules.md` | unresolved; separate map revalidation required |
| `SEAM-harness-x-verification.md` | unresolved; separate map revalidation required |
| `SEAM-harness-x-workflow.md` | unresolved; separate map revalidation required |
| `SEAM-llm-x-rules.md` | unresolved; separate map revalidation required |
| `SEAM-llm-x-scheduler.md` | unresolved; separate map revalidation required |
| `SEAM-llm-x-workflow.md` | unresolved; separate map revalidation required |
| `SEAM-manifest-x-schools.md` | unresolved; separate map revalidation required |
| `SEAM-periphery-x-verification.md` | unresolved; separate map revalidation required |
| `SEAM-rules-x-workflow.md` | unresolved; separate map revalidation required |
| `SEAM-scheduler-x-rules.md` | unresolved; separate map revalidation required |
| `SEAM-scheduler-x-workflow.md` | unresolved; separate map revalidation required |
| `SEAM-schools-x-scheduler.md` | unresolved; separate map revalidation required |
| `SEAM-schools-x-scratch.md` | unresolved; separate map revalidation required |
| `SEAM-scratch-x-workflow.md` | unresolved; separate map revalidation required |
| `SUB-amendment.md` | unresolved; separate map revalidation required |
| `SUB-application.md` | unresolved; separate map revalidation required |
| `SUB-evaluation.md` | unresolved; separate map revalidation required |
| `SUB-evidence.md` | unresolved; separate map revalidation required |
| `SUB-harness.md` | unresolved; separate map revalidation required |
| `SUB-llm.md` | unresolved; separate map revalidation required |
| `SUB-manifest.md` | unresolved; separate map revalidation required |
| `SUB-ontology.md` | unresolved; separate map revalidation required |
| `SUB-periphery.md` | unresolved; separate map revalidation required |
| `SUB-rules.md` | unresolved; separate map revalidation required |
| `SUB-scheduler.md` | unresolved; separate map revalidation required |
| `SUB-workflow.md` | unresolved; separate map revalidation required |

## Integrity incidents and disposition

An early external monitor mistook a nested-namespace PID for worker exit and
marked `attempt-0002` interrupted while it was active. The scoped worker was
stopped, all seven files were preserved, and the entire attempt was marked
`quarantined`. Quarantined means preserved for audit but excluded from counts
and resume decisions. A regression test now enforces that rule; the clean
replacement attempt produced eight receipts.

A transient GitHub data-API checkpoint clipped `matrix.py`. A local-to-remote
tree comparison detected it before execution; a non-force follow-up commit
restored the exact local blob. No live call was made from the mismatched tree.
The history is retained rather than rewritten.

## Replanning boundary

No further live campaign execution or implementation repair is authorized by
this FAIL record. A follow-up plan must separately decide whether to repair the
12 repository failures, restore the documentation verifier's environment and
historical references, perform the 46 map revalidations, and resume a bounded
portion of the immutable live queue. Until those gates are green and the exact
terminal set equals the frozen set, the delivery verdict remains FAIL.
