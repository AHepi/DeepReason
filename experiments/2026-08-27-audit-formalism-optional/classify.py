"""Classify every kind-read site and emit SITES.md.

Four classes, from the tranche brief:

  LAWFUL-PROTECTION  formal backing granting immunity or extra scrutiny --
                     the direction the law explicitly allows (D2 Amendment 1:
                     "nothing stops a formal one from carrying MORE scrutiny
                     than a prose-only one either")
  UNLAWFUL-PENALTY   informality reducing admission, rank, exposure
                     protection, or acceptance
  STRUCTURAL-GAP     a road that does not exist for prose -- not a violation,
                     but rowed separately with what a prose road would need
  NEUTRAL            kind is read but no outcome moves (the row says why it
                     reads it)

Run:  python experiments/2026-08-27-audit-formalism-optional/classify.py
"""

import json
import os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))

# (class, reads, moves, note) keyed by "file:line".  Every site not named here
# falls to its file's GROUP default below; every site not covered by either is
# reported as UNCLASSIFIED and the script exits non-zero, so the table can
# never silently omit a row.
SITE = {
 # ---- the two prose-immunity guards, and their consumers ------------------
 "src/deepreason/rules/warrants.py:45": ("LAWFUL-PROTECTION", "EXEC_PROGRAMS eval set", "prose-immunity", "`execution_backed` builds the narrow execution eval set. Returns False -- no protection -- for a target with none; it can never remove standing the target would otherwise have."),
 "src/deepreason/rules/warrants.py:50": ("LAWFUL-PROTECTION", "target's commitment list", "prose-immunity", "The `saw` loop: no execution commitment => `saw` stays False => `False`. Absence grants nothing and costs nothing."),
 "src/deepreason/rules/warrants.py:104": ("LAWFUL-PROTECTION", "substantive commitment presence", "prose-immunity", "`formally_backed`, the wide guard. Same shape, same one-way direction; `_substantive` excludes structural well-formedness so `program:json-wf` cannot buy immunity."),
 "src/deepreason/informal/trial.py:920": ("LAWFUL-PROTECTION", "formally_backed(target)", "acceptance", "The ONLY point where prose can mint a status-changing warrant, and the one place the wide guard belongs. A formal target declines the trial; an informal target proceeds unimpeded."),
 "src/deepreason/informal/trial.py:1298": ("LAWFUL-PROTECTION", "execution_backed(loser)", "acceptance", "A pairwise loser that execution backs is not demoted on preference. Informal losers are not protected -- but they were not protected before the guard existed either."),
 "src/deepreason/rules/crit.py:1544": ("LAWFUL-PROTECTION", "execution_backed(target)", "criticism exposure", "Execution supremacy: a purely argumentative case cannot override a passing oracle. Informal targets take the case."),
 "src/deepreason/rules/crit.py:2157": ("LAWFUL-PROTECTION", "execution_backed(case.target)", "criticism exposure", "Batch-path twin of 1544."),
 "src/deepreason/rules/vision.py:91": ("LAWFUL-PROTECTION", "execution_backed(target)", "criticism exposure", "Uniform supremacy for the vision critic: a passing in-process oracle beats a visual argument."),
 "src/deepreason/rules/crit.py:1551": ("LAWFUL-PROTECTION", "_has_property_oracle(target)", "criticism exposure", "Counterexample RETRIES are offered only against a property-oracle carrier -- MORE attack surface for formal, none removed from prose."),
 "src/deepreason/rules/crit.py:2174": ("LAWFUL-PROTECTION", "_has_property_oracle(case.target)", "criticism exposure", "Batch-path twin of 1551."),
 # ---- the frontier: THE FINDING -------------------------------------------
 "src/deepreason/scheduler/scheduler.py:221": ("UNLAWFUL-PENALTY", "artifact's evaluable commitments", "rank (Pareto frontier, and through frontier_delta the stop decision)", "F1. `run_report` scores every survivor on PARETO_AXES = [hv, reach, coverage]. This line collects the EVALUABLE commitments only."),
 "src/deepreason/scheduler/scheduler.py:222": ("UNLAWFUL-PENALTY", "programs.evaluable(kappa)", "rank (Pareto frontier)", "F1, continued. `coverage = passes/len(commitments) if commitments else 0.0` -- an artifact with NO evaluable commitment scores 0.0 on an axis a formally-backed sibling scores 1.0 on, and `frontier()` maximises every axis, so the formal sibling DOMINATES and the prose one leaves the frontier. Reproduced with a mutation proof in `repro_coverage_rank.py`."),
 # ---- reach: no road for a commitment-free artifact ------------------------
 "src/deepreason/measures/reach.py:137": ("STRUCTURAL-GAP", "_substantive(criterion)", "reach eligibility", "G1. Only SUBSTANTIVE (non-structural) criteria qualify as foreign reach targets, and `reach_sweep`'s `if not carried: continue` skips any artifact whose own commitment set is empty. Reach is unreachable for a commitment-free artifact -- and reach>0 is a hard gate on promotion nomination and on the knowledge view."),
 "src/deepreason/measures/reach.py:87": ("NEUTRAL", "programs.evaluable(commitment)", "none", "`_substantive`'s own evaluability precondition; it classifies, it does not gate."),
 # ---- knowledge view -------------------------------------------------------
 "src/deepreason/views/knowledge.py:52": ("STRUCTURAL-GAP", "crit(artifact) -- nonempty attack surface", "render presence (the knowledge view)", "G2. Two independent conjuncts exclude a commitment-free artifact from the knowledge view: `reach > 0` (see G1) and `crit`. A view, not a status -- but it is the run's own statement of what it knows."),
 # ---- promotion ------------------------------------------------------------
 "src/deepreason/calculus/promotion.py:239": ("STRUCTURAL-GAP", "subject.demarcation == 'no-attack-surface'", "promotion", "G3. Rung 5's subject-demarcation criterion FAILS a subject that declares nothing. `nomination.py:260` computes that label from `crit` alone, so it is the commitment-free case again, one rung higher."),
 "src/deepreason/calculus/promotion.py:245": ("NEUTRAL", "subject.demarcation == 'declared-only'", "promotion", "`declared-only` is OVERRUN -- pending, never a refutation. \"We could not check\" is deliberately not the strongest criticism in the calculus."),
 "src/deepreason/calculus/promotion.py:550": ("STRUCTURAL-GAP", "subject.commitments empty", "promotion", "G3, the RENT criterion's own copy: an enumerated-nothing subject FAILS."),
 "src/deepreason/calculus/promotion.py:225": ("NEUTRAL", "spec.observation_valued", "promotion", "The EMPIRICAL clause's scope test -- reads the SCOPE's criteria, not the subject's kind."),
 "src/deepreason/calculus/promotion.py:231": ("LAWFUL-PROTECTION", "spec.observation_valued on subject", "promotion", "An empirical scope demands an observation-valued commitment on the subject. This is a demand for EMPIRICAL content, not formal encoding -- an `observation` eval is prose."),
 "src/deepreason/calculus/promotion.py:232": ("NEUTRAL", "subject.commitments iteration", "promotion", "Iteration for the clause above."),
 "src/deepreason/calculus/promotion.py:461": ("NEUTRAL", "len(rival.commitments) >= 2", "promotion", "COMPATIBILITY's bundle-size test on a RIVAL, not on the subject's kind."),
 "src/deepreason/calculus/promotion.py:477": ("NEUTRAL", "rival.commitments", "promotion", "Iteration for the clause above."),
 "src/deepreason/calculus/promotion.py:483": ("NEUTRAL", "spec.observation_valued", "promotion", "Rival-side empirical test, same shape."),
 "src/deepreason/calculus/promotion.py:554": ("NEUTRAL", "subject.commitments", "promotion", "Enumeration check for the RENT clause."),
 "src/deepreason/calculus/promotion.py:174": ("NEUTRAL", "certificate.commitments", "promotion", "Frozen-environment iteration."),
 "src/deepreason/calculus/promotion.py:626": ("NEUTRAL", "eval in PROMOTION_PROGRAMS", "promotion", "Selects which criteria the sweep fires -- a criterion-type test, not a subject-kind test."),
 "src/deepreason/calculus/promotion.py:627": ("NEUTRAL", "eval partition", "promotion", "Same clause."),
 "src/deepreason/calculus/promotion.py:633": ("NEUTRAL", "FRAME_ASSERTION_COMMITMENT present", "promotion", "Artifacts making no frame claim are skipped ENTIRELY rather than evaluated and failed -- the module says so and it is the right direction."),
 "src/deepreason/calculus/nomination.py:182": ("STRUCTURAL-GAP", "_substantive(criterion)", "promotion nomination", "G1's twin on the nomination side."),
 "src/deepreason/calculus/nomination.py:260": ("STRUCTURAL-GAP", "crit(artifact)", "promotion nomination", "G3's source: `declared-only` vs `no-attack-surface` is decided by whether ANY registered commitment is carried."),
 # ---- the one kind-conditional SCHEDULING term ----------------------------
 "src/deepreason/scheduler/scheduler.py:1396": ("LAWFUL-PROTECTION", "EXEC_PROGRAMS eval set", "criticism exposure ordering", "C1 (closest call). `_standing_recrit_pool` returns `backed + rest`: execution-oracle carriers queue FIRST for leftover-capacity re-criticism."),
 "src/deepreason/scheduler/scheduler.py:1412": ("LAWFUL-PROTECTION", "kappa.eval in execution_evals", "criticism exposure ordering", "C1, continued. R-g's letter forbids weighting SCHEDULING on kind; D2 Amendment 1 re-anchored R-g to one direction and permits MORE scrutiny on formal, which is this direction. The `_recrit_cursor` rotation bounds the effect further. Rowed as the audit's closest call, not as a clean row."),
 "src/deepreason/scheduler/scheduler.py:1414": ("LAWFUL-PROTECTION", "artifact.interface.commitments", "criticism exposure ordering", "C1, continued."),
 # ---- the mandatory-envelope admission road -------------------------------
 "src/deepreason/workloads/text.py:178": ("STRUCTURAL-GAP", "checker_specs paired with counterconditions", "admission", "G4's neighbourhood. `ReasoningCandidateProposal.counterconditions` is `min_length=1`: on the `reasoning.text.v1` workload a candidate MUST name at least one countercondition or the wire contract rejects it. What it must name is PROSE (`eval` defaults to `observation`), so this forces an ENVELOPE, not a FORMALISM -- but there is no admission road for un-enveloped prose on that workload."),
 "src/deepreason/workloads/text.py:191": ("NEUTRAL", "checker_specs presence", "admission", "Pairs specs to cases when building the envelope; a missing spec means `eval=observation`, i.e. prose."),
 "src/deepreason/workloads/text.py:224": ("NEUTRAL", "eval == 'observation'", "commitment construction", "Marks a prose countercondition observation-valued. Additive."),
 "src/deepreason/workloads/text.py:225": ("NEUTRAL", "observation_valued", "commitment construction", "Routes a prose countercondition to `reasoning_observation_pending` -- a PENDING program, so an unevaluable prose countercondition never reads as a failure."),
 "src/deepreason/workloads/text.py:243": ("LAWFUL-PROTECTION", "checker_spec is not None", "criticism exposure", "An optional checker gives the candidate's own prose a machine attack surface -- extra scrutiny for the candidate that opts in."),
 "src/deepreason/workloads/text.py:280": ("LAWFUL-PROTECTION", "is_pure_code(field)", "admission", "The ANTI-formalism direction: a claim or mechanism that is SOLELY code FAILS the mandatory well-formedness program. Prose is required; code alone is refuted."),
 "src/deepreason/workloads/text.py:81": ("NEUTRAL", "eval == 'program:candidate_checker'", "wire validation", "Contract coupling: a checker eval requires checker source. Pure well-formedness."),
 "src/deepreason/workloads/text.py:83": ("NEUTRAL", "checker_spec completeness", "wire validation", "Same coupling."),
 "src/deepreason/workloads/text.py:87": ("NEUTRAL", "checker_spec without checker eval", "wire validation", "Same coupling, other direction."),
 "src/deepreason/workloads/text.py:90": ("NEUTRAL", "error text", "wire validation", "Message string for the coupling above."),
 "src/deepreason/informal/skeleton.py:67": ("NEUTRAL", "eval == 'program:candidate_checker'", "wire validation", "`ForbiddenCase`'s copy of the same coupling."),
 "src/deepreason/informal/skeleton.py:69": ("NEUTRAL", "checker_spec completeness", "wire validation", "Same."),
 "src/deepreason/informal/skeleton.py:73": ("NEUTRAL", "checker_spec without checker eval", "wire validation", "Same."),
 "src/deepreason/informal/skeleton.py:76": ("NEUTRAL", "error text", "wire validation", "Same."),
 "src/deepreason/informal/skeleton.py:119": ("LAWFUL-PROTECTION", "is_pure_code(field)", "admission", "Anti-formalism twin of workloads/text.py:280, on the skeleton-wf opt-in path."),
 "src/deepreason/informal/skeleton.py:136": ("LAWFUL-PROTECTION", "case.checker_spec is not None", "criticism exposure", "Opt-in machine attack surface on a forbidden case."),
 # ---- criticism dispatch: the kind-blind sockets ---------------------------
 "src/deepreason/rules/crit.py:945": ("NEUTRAL", "saw_property_oracle", "criticism", "`crit_program` is a data-driven no-op when nothing on the target is evaluable -- not a branch that skips informal targets. This is what makes an informal target's DEMONSTRATIVE pass free of side effects."),
 "src/deepreason/rules/crit.py:954": ("NEUTRAL", "target commitments", "criticism", "Same loop."),
 "src/deepreason/rules/crit.py:956": ("NEUTRAL", "programs.evaluable(kappa)", "criticism", "Same loop's evaluability test."),
 "src/deepreason/rules/crit.py:1005": ("NEUTRAL", "target commitments", "criticism", "Fuzz pass's own commitment walk; same no-op shape."),
 "src/deepreason/rules/crit.py:840": ("NEUTRAL", "kappa lookup", "criticism", "Commitment resolution for the pack."),
 "src/deepreason/rules/crit.py:842": ("NEUTRAL", "target commitments", "criticism", "Same."),
 "src/deepreason/rules/crit.py:877": ("NEUTRAL", "target commitments", "criticism", "Same."),
 "src/deepreason/rules/crit.py:1083": ("NEUTRAL", "property commitments", "criticism", "Active-property resolution."),
 "src/deepreason/rules/crit.py:1084": ("NEUTRAL", "kappa lookup", "criticism", "Same."),
 "src/deepreason/rules/crit.py:1141": ("NEUTRAL", "active_properties", "criticism", "Property-oracle machinery; reaches only targets that carry one."),
 # ---- packs ----------------------------------------------------------------
 "src/deepreason/llm/packs.py:37": ("NEUTRAL", "EXEC_PROGRAMS eval set", "pack rendering", "Module constant."),
 "src/deepreason/llm/packs.py:200": ("LAWFUL-PROTECTION", "carries an execution oracle", "criticism exposure", "`_carries_execution_oracle` gates `_COUNTEREXAMPLE_NOTE`: critics of a formal target are offered an EXTRA attack channel. Nothing is withheld from a prose target that a prose target could use."),
 "src/deepreason/llm/packs.py:842": ("NEUTRAL", "target commitments", "pack rendering", "One template for every target; the commitments section is populated from data and is empty for a commitment-free target."),
 "src/deepreason/llm/packs.py:858": ("NEUTRAL", "target commitments", "pack rendering", "Renders `(none)` rather than omitting the line -- an absence stated, not hidden."),
 "src/deepreason/llm/packs.py:1050": ("LAWFUL-PROTECTION", "eval in _EXECUTION_EVALS", "criticism exposure", "Counterexample-retry pack shows the frozen spec so a critic can aim. Formal-only, additive."),
 "src/deepreason/llm/packs.py:1111": ("NEUTRAL", "target commitments", "pack rendering", "`render_crit_pack`'s TARGET COMMITMENTS list -- one template, data-driven."),
 # ---- hv --------------------------------------------------------------------
 "src/deepreason/measures/hv.py:52": ("NEUTRAL", "own evaluable commitments", "rank (hv axis)", "The equivalence battery puts the artifact's OWN evaluable commitments first..."),
 "src/deepreason/measures/hv.py:53": ("NEUTRAL", "programs.evaluable", "rank (hv axis)", "...same clause."),
 "src/deepreason/measures/hv.py:54": ("LAWFUL-PROTECTION", "foreign registered evaluable commitments", "rank (hv axis)", "...then FOREIGN ones. Read own-only, a prose premise's battery would be empty and no variant could differ from it; the foreign half is the recorded repair that keeps prose measurable."),
 "src/deepreason/measures/hv.py:55": ("NEUTRAL", "programs.evaluable", "rank (hv axis)", "Same clause."),
 "src/deepreason/measures/hv.py:104": ("NEUTRAL", "own commitments", "rank (hv axis)", "`_evaluable_battery` (B0) is own-only by design -- B0 is the PASS battery, not the discrimination battery."),
 "src/deepreason/measures/hv.py:105": ("NEUTRAL", "programs.evaluable", "rank (hv axis)", "Same."),
 "src/deepreason/measures/hv.py:134": ("NEUTRAL", "kernel == 'mu_struct'", "variation kernel", "Kernel choice reads whether the CONTENT parses as a skeleton. It changes how edits are sampled, not whether the artifact may be measured; a skeleton gets the harder (role-level) kernel, so if anything the structured form is treated more severely."),
 "src/deepreason/measures/demarcation.py:42": ("STRUCTURAL-GAP", "any registered commitment", "demarcation / knowledge / promotion", "G2/G3's shared predicate: `crit` is False for a commitment-free artifact, and three consumers gate on it."),
 "src/deepreason/measures/demarcation.py:64": ("NEUTRAL", "is_hv_floor", "demarcation", "Stratification: the demarcation reading must not consume its own output."),
 "src/deepreason/scheduler/scheduler.py:1326": ("NEUTRAL", "artifact commitments", "criticism dispatch", "Per-commitment trial dispatch; reaches only what is carried."),
 "src/deepreason/scheduler/scheduler.py:1330": ("LAWFUL-PROTECTION", "is_hv_floor(kappa)", "rank (hv axis)", "hv-floor runs only for a carrier -- extra scrutiny for the artifact that carries it. Non-carriers keep hv=0.0, which is the default for every unmeasured artifact and is itself part of F1's arithmetic."),
 # ---- misc kind reads with no outcome -------------------------------------
 "src/deepreason/authority.py:97": ("NEUTRAL", "argumentative-authority value", "config validation", "Vocabulary check on the policy string. The POLICY it validates is rowed as G5 in VERDICT.md -- `observe_only` is the default, so a prose case changes no status unless the operator opts in."),
 "src/deepreason/scheduler/scheduler.py:830": ("NEUTRAL", "eval == 'program:reasoning-envelope-wf'", "output model choice", "Selects the reasoning-workload contract from the PROBLEM's criteria. A workload switch, not a conjecture-kind switch."),
 "src/deepreason/scheduler/scheduler.py:832": ("NEUTRAL", "commitment registered", "output model choice", "Same clause."),
 "src/deepreason/rules/conj.py:950": ("NEUTRAL", "eval == 'program:reasoning-envelope-wf'", "output model choice", "Same switch, conjecture side."),
 "src/deepreason/rules/conj.py:952": ("NEUTRAL", "commitment registered", "output model choice", "Same."),
 "src/deepreason/rules/conj.py:1549": ("NEUTRAL", "eval == 'program:reasoning-envelope-wf'", "output model choice", "Same."),
 "src/deepreason/rules/conj.py:1551": ("NEUTRAL", "commitment registered", "output model choice", "Same."),
 "src/deepreason/rules/conj.py:2290": ("NEUTRAL", "base + draft commitments", "admission", "Two-phase compilation's draft pool union -- additive, and the drafts come from the candidate's OWN counterconditions."),
 "src/deepreason/workloads/models.py:101": ("NEUTRAL", "problem.criteria + owned", "admission", "THE ADMISSION FACT. An artifact's commitments are compiled from the PROBLEM's criteria plus harness-owned mandatory ones -- never from whether the model wrote formal content. Two candidates on one problem carry the same battery whatever their prose looks like."),
 "src/deepreason/workloads/models.py:102": ("NEUTRAL", "registered or drafted", "admission", "Same clause."),
 "src/deepreason/workloads/models.py:142": ("LAWFUL-PROTECTION", "drafted-but-unregistered", "admission", "Safe-skeleton compilation is the ONE model-authored route that ADDS commitments -- purely additive, and `ForbiddenCase` forbids `predicate:` there for RCE reasons."),
 "src/deepreason/workloads/models.py:143": ("NEUTRAL", "not yet registered", "admission", "Same clause."),
 "src/deepreason/scheduler/scheduler.py:2588": ("NEUTRAL", "carries the property eval", "fuzz dispatch", "Fuzz probing reaches property-oracle carriers -- extra machine scrutiny for formal."),
 "src/deepreason/scheduler/scheduler.py:2589": ("NEUTRAL", "artifact commitments", "fuzz dispatch", "Same."),
 "src/deepreason/scheduler/scheduler.py:2668": ("NEUTRAL", "active_properties count", "property design budget", "Caps property proposals per oracle; reads no conjecture."),
 "src/deepreason/rules/spawn.py:184": ("NEUTRAL", "kappa.observation_valued", "spawn (research)", "Spawns a research problem for an observation-valued commitment -- additive work, and observation-valued commitments are the PROSE end of the eval vocabulary."),
 "src/deepreason/rules/spawn.py:182": ("NEUTRAL", "artifact commitments", "spawn", "Same loop."),
 "src/deepreason/rules/spawn.py:123": ("NEUTRAL", "criterion registered", "spawn", "Explanation-debt criteria union."),
 "src/deepreason/premises.py:506": ("STRUCTURAL-GAP", "PREMISE_RENT carried", "premise refutation", "G6. The recorded reconciliation is explicit that this battery exists so a category-error premise falls by a PROGRAM verdict rather than a prose one: \"For move 4 to be a program verdict rather than a prose verdict, a premise artifact must carry a demarcation criterion at registration.\" Argument-alone refutation has no direct road; it is routed through an encoding."),
 "src/deepreason/premises.py:173": ("NEUTRAL", "artifact commitments", "premise machinery", "Commitment walk."),
 "src/deepreason/proof_debt.py:126": ("NEUTRAL", "DERIVATION_MANIFEST carried", "proof debt", "Recognition by INTERFACE STRUCTURE, never by a kind field -- the module says so."),
 "src/deepreason/proof_debt.py:199": ("NEUTRAL", "programs.evaluable(kappa)", "proof debt", "Classifies a commitment as open certificate vs kernel check."),
 "src/deepreason/rules/act.py:52": ("NEUTRAL", "target commitments", "browser evidence", "Browser machinery reaches only browser-commitment carriers."),
 "src/deepreason/rules/act.py:77": ("NEUTRAL", "target commitments", "browser evidence", "Same."),
 "src/deepreason/rules/act.py:95": ("NEUTRAL", "target commitments", "browser evidence", "Same."),
 "src/deepreason/rules/experiment.py:60": ("NEUTRAL", "artifact commitments", "property machinery", "Walks a carrier's commitments."),
 "src/deepreason/rules/experiment.py:62": ("NEUTRAL", "programs.evaluable", "property machinery", "Same."),
 "src/deepreason/rules/experiment.py:122": ("NEUTRAL", "base commitment carried", "property machinery", "Same."),
 "src/deepreason/rules/experiment.py:258": ("NEUTRAL", "active_properties", "property machinery", "Same."),
 "src/deepreason/rules/experiment.py:298": ("NEUTRAL", "base commitment carried", "property machinery", "Same."),
 "src/deepreason/rules/experiment.py:435": ("NEUTRAL", "base commitment carried", "property machinery", "Same."),
 "src/deepreason/rules/experiment.py:461": ("NEUTRAL", "active_properties", "property machinery", "Same."),
 "src/deepreason/capture/detection.py:167": ("NEUTRAL", "accepted AND has commitments", "diagnostic (criticism debt)", "`criticism_debt`'s denominator excludes commitment-free artifacts. Attention/diagnostic only -- never a status input."),
 "src/deepreason/capture/detection.py:173": ("NEUTRAL", "commitment registered", "diagnostic", "Same metric."),
 "src/deepreason/capture/detection.py:174": ("NEUTRAL", "not evaluable", "diagnostic", "Same metric -- NON-evaluable commitments are what create debt, so prose criteria raise the debt signal rather than lowering it."),
 "src/deepreason/capture/detection.py:176": ("NEUTRAL", "artifact commitments", "diagnostic", "Same metric."),
 "src/deepreason/capture/detection.py:217": ("NEUTRAL", "eval startswith rubric:", "diagnostic (grounding lambda)", "Counts non-rubric verdicts as exogenous."),
 "src/deepreason/capture/detection.py:218": ("NEUTRAL", "eval startswith rubric:", "diagnostic", "Same."),
 "src/deepreason/capture/detection.py:249": ("NEUTRAL", "artifact commitments", "diagnostic (evidence lambda)", "Same family."),
 "src/deepreason/capture/detection.py:251": ("NEUTRAL", "observation_valued", "diagnostic", "Returns None when the run makes no empirical claims, so a pure explanatory run reads None rather than 0.0."),
 "src/deepreason/capture/ladder.py:52": ("NEUTRAL", "accepted AND has commitments", "diagnostic", "Ladder rung counting; attention only."),
 "src/deepreason/capture/diagnostics.py:352": ("NEUTRAL", "artifact commitments", "diagnostic", "Diagnostic walk."),
 "src/deepreason/capture/diagnostics.py:356": ("NEUTRAL", "programs.evaluable", "diagnostic", "Same."),
 "src/deepreason/rules/guards/anti_relapse.py:131": ("NEUTRAL", "registry or draft overlay", "admission (relapse domain)", "The relapse domain digests the artifact's evaluable battery. Two candidates on one problem share it, so the guard cannot distinguish them by kind."),
 "src/deepreason/rules/guards/anti_relapse.py:134": ("NEUTRAL", "artifact commitments", "admission", "Same."),
 "src/deepreason/rules/guards/anti_relapse.py:135": ("NEUTRAL", "programs.evaluable", "admission", "Same."),
 "src/deepreason/rules/guards/anti_relapse.py:249": ("NEUTRAL", "programs.evaluable", "admission", "Same, pairwise form."),
 "src/deepreason/rules/guards/anti_relapse.py:256": ("NEUTRAL", "registry or draft overlay", "admission", "Same."),
 "src/deepreason/rules/guards/anti_relapse.py:294": ("NEUTRAL", "registry or draft overlay", "admission", "Same."),
 "src/deepreason/views/evidence.py:68": ("NEUTRAL", "artifact commitments", "view", "Evidence view rendering."),
 "src/deepreason/views/evidence.py:70": ("NEUTRAL", "artifact commitments", "view", "Same."),
 "src/deepreason/views/evidence.py:76": ("NEUTRAL", "observation_valued", "view", "Labels an observation-valued commitment in the render."),
 "src/deepreason/views/evidence.py:102": ("NEUTRAL", "warrant commitment", "view", "Same."),
 "src/deepreason/views/export.py:43": ("NEUTRAL", "commitment registered", "view", "Export rendering."),
 "src/deepreason/views/export.py:45": ("NEUTRAL", "artifact commitments", "view", "Same."),
 "src/deepreason/views/theory.py:40": ("NEUTRAL", "artifact commitments", "view", "Prints an attack-surface line when there is one."),
 "src/deepreason/report.py:372": ("NEUTRAL", "commitment registered", "report", "Rubric-warrant counting."),
 "src/deepreason/report.py:373": ("NEUTRAL", "eval startswith rubric:", "report", "Same."),
 "src/deepreason/informal/audits.py:27": ("NEUTRAL", "warrant commitment", "audit render", "Warrant provenance render."),
 "src/deepreason/harness.py:360": ("NEUTRAL", "commitment already registered", "registry", "Idempotent registration."),
 "src/deepreason/harness.py:507": ("NEUTRAL", "artifact commitments", "well-formedness", "Every declared commitment must be registered -- frozen surface, kind-blind."),
 "src/deepreason/harness.py:508": ("NEUTRAL", "commitment registered", "well-formedness", "Same."),
 "src/deepreason/harness.py:1976": ("NEUTRAL", "warrant commitment registered", "well-formedness", "Same."),
 "src/deepreason/harness.py:1982": ("NEUTRAL", "eval startswith", "well-formedness", "Warrant/commitment agreement check."),
 "src/deepreason/skills/validate.py:174": ("NEUTRAL", "artifact commitments", "skill validation", "Adoption diffing."),
 "src/deepreason/skills/validate.py:183": ("NEUTRAL", "artifact commitments", "skill validation", "Same."),
 "src/deepreason/calculus/audit.py:130": ("NEUTRAL", "subject commitments", "calculus audit", "Environment enumeration."),
 "src/deepreason/calculus/audit.py:245": ("NEUTRAL", "commitment registered", "calculus audit", "Same."),
 "src/deepreason/calculus/standing.py:72": ("NEUTRAL", "FRAME_ASSERTION carried", "standing", "Frame-assertion recognition by interface structure."),
 "src/deepreason/calculus/standing.py:101": ("NEUTRAL", "FRAME_ASSERTION carried", "standing", "Same."),
 "src/deepreason/calculus/views.py:29": ("NEUTRAL", "PROBLEM_SUBJECT carried", "calculus view", "Same shape."),
 "src/deepreason/calculus/render.py:183": ("NEUTRAL", "DEPARTURE_DECLARATION carried", "calculus render", "Same shape."),
 "src/deepreason/calculus/nomination.py:310": ("NEUTRAL", "commitment registered", "nomination", "Certificate freezing."),
 "src/deepreason/calculus/nomination.py:349": ("NEUTRAL", "commitment registered", "nomination", "Same."),
 "src/deepreason/bridge/derived.py:404": ("NEUTRAL", "commitment registry", "bridge", "Object-id union for the derived ledger."),
 "src/deepreason/bridge/derived.py:446": ("NEUTRAL", "commitment registry", "bridge", "Same."),
 "src/deepreason/bridge/harness.py:1272": ("NEUTRAL", "registry unchanged", "bridge", "No-write assertion."),
 "src/deepreason/bridge/harness.py:1275": ("NEUTRAL", "registry unchanged", "bridge", "Same."),
 "src/deepreason/storage/merge.py:34": ("NEUTRAL", "object is a commitment", "storage", "Object-kind dispatch, not conjecture kind."),
 "src/deepreason/amendment/apply.py:319": ("NEUTRAL", "commitment registered", "amendment", "Re-registration guard."),
 "src/deepreason/application/text_runs.py:447": ("NEUTRAL", "commitment lookup", "application", "Render helper."),
 "src/deepreason/workflow/conjecture_recovery.py:303": ("NEUTRAL", "commitment registered", "recovery", "Reasoning-workload switch, recovery side."),
 "src/deepreason/workflows/website.py:578": ("NEUTRAL", "commitment registry", "website workflow", "Manifest-commitment intersection."),
 "src/deepreason/workflows/website.py:585": ("NEUTRAL", "artifact commitments", "website workflow", "Same."),
 "src/deepreason/research/backends.py:263": ("NEUTRAL", "criterion registered", "research", "Criteria filter."),
 "src/deepreason/evidence/render.py:113": ("NEUTRAL", "criterion registered", "evidence render", "Criteria filter."),
 "src/deepreason/rules/synth.py:57": ("NEUTRAL", "criterion registered", "synthesis", "Criteria filter."),
 "src/deepreason/imports.py:353": ("NEUTRAL", "commitment registered", "imports", "Registration guard."),
 "src/deepreason/jolts.py:446": ("NEUTRAL", "commitment registry", "jolts", "Digest input."),
 "src/deepreason/ops.py:91": ("NEUTRAL", "skeleton-wf in criteria", "ops", "Opt-in check for the skeleton workload."),
 "src/deepreason/run_manifest.py:4514": ("NEUTRAL", "commitment registered", "manifest", "Manifest projection."),
 "src/deepreason/signals.py:535": ("NEUTRAL", "signal semantics string", "none", "Documentation string in the signal registry."),
 "src/deepreason/easy.py:604": ("NEUTRAL", "commitment registered", "convenience API", "Registration guards in the easy-mode builder."),
 "src/deepreason/easy.py:635": ("NEUTRAL", "commitment registered", "convenience API", "Same."),
 "src/deepreason/easy.py:656": ("NEUTRAL", "commitment registered", "convenience API", "Same."),
 "src/deepreason/easy.py:678": ("NEUTRAL", "commitment registered", "convenience API", "Same."),
 "src/deepreason/easy.py:702": ("NEUTRAL", "commitment registered", "convenience API", "Same."),
 "src/deepreason/easy.py:739": ("NEUTRAL", "commitment registered", "convenience API", "Same."),
 "src/deepreason/easy.py:865": ("NEUTRAL", "commitment registered", "convenience API", "Same."),
}

ORDER = ["UNLAWFUL-PENALTY", "STRUCTURAL-GAP", "LAWFUL-PROTECTION", "NEUTRAL"]


def main():
    data = json.load(open(os.path.join(HERE, "KIND_READS.json")))
    rows, missing = [], []
    for hit in data["sites"]:
        key = f"{hit['file']}:{hit['line']}"
        entry = SITE.get(key)
        if entry is None:
            missing.append(key)
            continue
        rows.append((key, hit, entry))

    counts = Counter(entry[0] for _k, _h, entry in rows)
    lines = [
        "<!-- generated by classify.py; do not hand-edit -->",
        "# SITES — every place `src/deepreason` reads a conjecture's or a criticism's KIND",
        "",
        f"Sweep: `python sweep.py` — {data['raw_hits']} raw hits over 26 terms, "
        f"{data['code_hits']} in executable code.",
        f"Reduction: `python reduce.py` — **{data['kind_reads']} kind-reads** "
        "(a kind signal in a boolean position). Drop reasons, all machine-recorded:",
        "",
    ]
    for reason, count in sorted(data["dropped"].items(), key=lambda x: -x[1]):
        lines.append(f"- `{reason}`: {count}")
    lines += [
        "",
        "Every one of the kind-reads is rowed below. No sampling: the count in "
        "this table equals `KIND_READS.json`'s `kind_reads`, and `classify.py` "
        "exits non-zero if any site is unrowed.",
        "",
        "| class | count |",
        "|---|---|",
    ]
    for name in ORDER:
        lines.append(f"| {name} | {counts.get(name, 0)} |")
    lines.append(f"| **total** | **{len(rows)}** |")
    lines.append("")

    for name in ORDER:
        chosen = [r for r in rows if r[2][0] == name]
        if not chosen:
            continue
        lines += [f"## {name} — {len(chosen)} sites", "",
                  "| site | reads | moves | note |", "|---|---|---|---|"]
        for key, _hit, (_cls, reads, moves, note) in sorted(chosen):
            lines.append(f"| `{key}` | {reads} | {moves} | {note} |")
        lines.append("")

    open(os.path.join(HERE, "SITES.md"), "w").write("\n".join(lines) + "\n")
    print(f"rowed {len(rows)} of {data['kind_reads']} kind-reads")
    for name in ORDER:
        print(f"  {name:20s} {counts.get(name, 0)}")
    if missing:
        print(f"\nUNCLASSIFIED ({len(missing)}):")
        for key in missing:
            print("  " + key)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
