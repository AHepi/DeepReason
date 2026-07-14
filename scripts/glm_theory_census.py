"""Phase 1 forensic theory extraction for the GLM judge-problem run.

Mechanical fields (id, status, role, claim, refutation path) come from the
retained root. Analytical fields (variable definitions, conventions,
assumptions, claim type, ambiguities) are a committed operator reading,
marked as such, keyed by artifact id so a formula is never merged with a
same-symbol formula from another artifact. Zero LLM tokens.

Output: experiments/results/glm_judge_v1_theory_census.json
"""
from __future__ import annotations

import json
from pathlib import Path

from deepreason.harness import Harness

ROOT = Path("experiments/glm_judge_2026-07-14")
OUT = Path("experiments/results/glm_judge_v1_theory_census.json")

# Committed operator formalizations. Symbols are LOCAL to each artifact.
ANNOTATIONS = {
 "5b4538abe4a7": dict(
  theorem_id="T1-e-above-half",
  variables={"e": "per-candidate error probability", "k": "ensemble size",
             "recall_wrong": "question-level recall on wrong-majority candidate SETS",
             "FPR_right": "1 - precision on right-majority sets (set level)"},
  filtering_rule="SET-LEVEL VETO of the majority answer (not candidate removal); post-veto fallback unspecified",
  ensemble_convention="k=5 or 7 (odd)", tie_handling="unspecified",
  independence="candidate errors i.i.d. implied", claim_kind="global necessary condition ('only when e > 0.5')",
  proposed_inequality="strict beat only if e > 0.5 AND recall_wrong > (1-precision) * frac_right_flagged",
  executable="partially - the e>0.5 necessity is enumerable under candidate-removal semantics; the set-veto semantics need a fallback rule",
  ambiguities=["post-veto fallback answer undefined", "set-level vs candidate-level precision conflated"],
 ),
 "30e483eb4940": dict(
  theorem_id="T2-adaptive-threshold",
  variables={"p_veto": "critic confidence score per question", "tau": "veto threshold",
             "e": "per-candidate error probability", "k": "ensemble size"},
  filtering_rule="set-level veto when p_veto > tau", ensemble_convention="k >= 5",
  tie_handling="unspecified", independence="score distributions per majority-correctness class",
  claim_kind="biconditional over existence of tau (exists tau with positive net iff wrong-majority score distribution stochastically dominates right-majority distribution)",
  proposed_inequality="exists tau: E[net fixed-minus-broke] > 0 iff F_wrong-scores stochastically dominates F_right-scores",
  executable="simulation only - requires a score-distribution model; dominance order unspecified (assumed first-order)",
  ambiguities=["dominance order unspecified", "net-benefit tie cases unaddressed"],
 ),
 "c9386a6c7b30": dict(
  theorem_id="T3-per-question-rates",
  variables={"r_w(q)": "fraction of wrong candidates flagged on question q",
             "r_c(q)": "fraction of correct candidates flagged on question q",
             "n_wrong(q)/n_correct(q)": "realized counts in the k-candidate pool"},
  filtering_rule="remove all flagged candidates", ensemble_convention="k >= 3",
  tie_handling="unspecified", independence="none assumed (per-question conditional rates)",
  claim_kind="per-question iff with a cross-question quantifier ('for all other questions')",
  proposed_inequality="fix on q iff SC wrong AND r_w(q)*n_wrong(q) > n_wrong(q)-n_correct(q); no break on q' iff r_c(q')*n_correct(q') < n_correct(q')-n_wrong(q')",
  executable="yes - direct enumeration over explicit flag vectors",
  ambiguities=["the two inequalities use > and < asymmetrically at equality", "the fix inequality omits the flags-on-correct term on the same question"],
 ),
 "2d711b2eb5ff": dict(
  theorem_id="T4-window-k7-fragile-subset",
  variables={"e": "per-candidate error probability", "k": "odd ensemble size >= 7",
             "P": "critic precision on candidates within margin<=2 pools",
             "R": "critic recall on candidates within margin<=2 pools"},
  filtering_rule="remove flagged candidates (implied)", ensemble_convention="odd k >= 7",
  tie_handling="unspecified", independence="i.i.d. candidate errors (binomial)",
  claim_kind="sufficient condition for strict beat",
  proposed_inequality="1/(k+1) < e < k/(k+2) AND P > e AND R > 1-e (on fragile subset) => strict beat",
  executable="yes - enumerable; NOTE the mechanism's numeric constants (P_inc ~ 0.29) are k=7-specific approximations",
  ambiguities=["precision/recall defined on the fragile subset only; behavior elsewhere unspecified"],
 ),
 "7811dbda8316": dict(
  theorem_id="T5-window-wide",
  variables={"e": "per-candidate error probability", "k": "odd ensemble size >= 5",
             "recall_wrong": "candidate-level TPR", "falseflag_rate_correct": "candidate-level FPR",
             "precision_wrong": "candidate-level precision"},
  filtering_rule="remove flagged candidates", ensemble_convention="odd k >= 5",
  tie_handling="excluded (odd k only)", independence="i.i.d. candidate errors",
  claim_kind="necessity of window ('only in') plus stated critic conditions",
  proposed_inequality="strict beat only if 1/(k+1) < e < k/(k+1); with TPR > FPR and precision > 0.5",
  executable="yes",
  ambiguities=["UPPER BOUND k/(k+1) differs from T4/T6/T7's k/(k+2) and T8/T9's 1/2 - do not merge"],
 ),
 "e977c688ba00": dict(
  theorem_id="T6-realized-ratio-threshold",
  variables={"e": "per-candidate error probability", "k": "odd ensemble size >= 3",
             "p": "critic precision (candidate level)", "r": "critic recall (candidate level)",
             "F_broke": "count of fragile-CORRECT majorities (margin=1)",
             "F_fixed": "count of fragile-WRONG majorities (margin=1)"},
  filtering_rule="remove flagged candidates", ensemble_convention="odd k >= 3",
  tie_handling="excluded", independence="i.i.d. candidate errors",
  claim_kind="biconditional (iff)",
  proposed_inequality="strict beat iff 1/(k+1) < e < k/(k+2) AND p > (1-r)*F_broke/(r*F_fixed)",
  executable="yes - F_broke/F_fixed computable from the binomial model; threshold is realization-dependent",
  ambiguities=["F_broke/F_fixed naming inverts the natural reading (broke = fragile-correct at risk); flip risk noted",
               "margin=1 fragility here vs margin<=2 in T4"],
 ),
 "edc14bbd1ae6": dict(
  theorem_id="T7-pmin-closed-form",
  variables={"e": "per-candidate error probability", "k": "odd ensemble size >= 5",
             "p": "critic precision (candidate level)", "r": "critic recall (candidate level)",
             "p_min": "e*(k-1)/(k+1) / (e*(k-1)/(k+1) + (1-e)*r*(k+1)/(k-1))"},
  filtering_rule="remove flagged: TP removal prob r*e per candidate, FP removal prob (1-p)*(1-e)",
  ensemble_convention="odd k >= 5", tie_handling="excluded", independence="i.i.d. binomial",
  claim_kind="biconditional (iff)",
  proposed_inequality="strict beat iff 1/(k+1) < e < k/(k+2) AND p > p_min(e,r,k)",
  executable="yes - fully explicit closed form; NOTE the stated FP mechanism mixes precision with FPR: (1-p)*(1-e) treats (1-p) as an FPR, which equals it only under a specific flag-rate normalization",
  ambiguities=["precision-as-FPR substitution unproven", "p_min behavior at k=1 divides by zero (see S4)"],
 ),
 "3a28bc3e8bde": dict(
  theorem_id="T8-three-condition-iff",
  variables={"e": "per-candidate error probability", "k": "odd in {3,5,7}",
             "P": "critic precision (candidate level)", "R": "critic recall (candidate level)"},
  filtering_rule="remove flagged candidates", ensemble_convention="odd k in {3,5,7}",
  tie_handling="excluded", independence="i.i.d.",
  claim_kind="each condition individually necessary, jointly sufficient",
  proposed_inequality="strict beat iff 1/(k+1) < e < 1/2 AND P >= 1/2 AND R > 0",
  executable="yes",
  ambiguities=["UPPER BOUND 1/2 differs from T4-T7", "P >= 1/2 vs T9's strict P > 1/2"],
 ),
 "6389657ce964": dict(
  theorem_id="T9-three-condition-iff-with-loss",
  variables={"e": "per-candidate error probability", "k": "odd", "P": "candidate-level precision",
             "R": "candidate-level recall"},
  filtering_rule="remove flagged candidates", ensemble_convention="odd k",
  tie_handling="excluded", independence="i.i.d.",
  claim_kind="biconditional plus a strict-loss claim for P < 1/2",
  proposed_inequality="strict beat iff window AND P > 1/2 AND R > 0; P < 1/2 => strictly loses",
  executable="yes - the strict-loss branch is the most exposed (R -> 0 gives a no-op tie, not a loss)",
  ambiguities=["loss claim quantifier (always vs in expectation) unspecified"],
 ),
 "44c4273f5c5a": dict(
  theorem_id="T10-no-fixed-tuple",
  variables={"m_q": "error count on question q", "(e,P,R,k)": "aggregate tuple"},
  filtering_rule="remove flagged candidates", ensemble_convention="any k",
  tie_handling="unspecified", independence="heterogeneous questions",
  claim_kind="insufficiency meta-claim (no fixed tuple determines the sign)",
  proposed_inequality="exists two settings with identical (e,P,R,k) and opposite harness-vs-SC signs",
  executable="yes - existence claim; Experiment C is its direct test",
  ambiguities=[],
 ),
 "92918f72767b": dict(
  theorem_id="T11-perfect-precision-tail",
  variables={"e": "per-candidate error probability (may be below window)",
             "P": "critic precision = 1.0", "R": "recall > 0", "n": "question count >= 100"},
  filtering_rule="remove flagged candidates", ensemble_convention="k = 5 in examples",
  tie_handling="UNSPECIFIED and load-bearing (removing 1 of 3 wrong from k=5 can yield a 2-2 tie)",
  independence="i.i.d.",
  claim_kind="sufficient condition CONTRADICTING window necessity (T5/T8/T9)",
  proposed_inequality="P = 1.0 AND R > 0 AND >= 1 broken-majority item with >= 1 flagged error => strictly positive net",
  executable="yes - per tie rule; the contradiction with T5/T8/T9 is itself a censused fact",
  ambiguities=["'potentially fixing' vs 'strictly positive net' gap: partial removal may tie rather than fix"],
 ),
 "dea717ccf1ea": dict(
  theorem_id="T13-high-error-band",
  variables={"p": "BASE candidate error probability (collides with other artifacts' p = precision; never merge)",
             "phi": "critic recall (candidate level)", "psi": "critic precision (candidate level)",
             "k": "ensemble size (5 in examples)"},
  filtering_rule="remove flagged candidates", ensemble_convention="k = 5",
  tie_handling="acknowledged in mechanism ('at best a tie') but no rule given",
  independence="i.i.d.",
  claim_kind="necessity of a HIGH-error band ('only in' 0.55-0.75 at k=5) plus critic conditions",
  proposed_inequality="strict win only if base error in (0.55, 0.75) AND phi > 0.7 AND psi > 0.3; strict loss when psi < 0.2 and SC was right",
  executable="yes - enumerable; NOTE its band lies ABOVE 1/2, contradicting T8/T9's e < 1/2 upper bound",
  ambiguities=["symbol p = base error here, precision elsewhere", "band constants stated 'roughly'"],
 ),
 "88f00f0d4243": dict(
  theorem_id="T12-mutual-information",
  variables={"C": "flag pattern", "B": "per-candidate badness", "M_wrong": "majority-error indicator",
             "I(.;.)": "mutual information"},
  filtering_rule="remove flagged candidates", ensemble_convention="any k >= 3",
  tie_handling="unspecified", independence="arbitrary flag dependence permitted",
  claim_kind="biconditional (iff) in information-theoretic form",
  proposed_inequality="strict beat iff I(C;B) > I(C;M_wrong)",
  executable="simulation only - MI computable, but the iff is a strong claim over all distributions",
  ambiguities=["MI compares scalars with different supports; no rate/threshold linking MI gap to accuracy gap"],
 ),
 "5597507043f5": dict(
  theorem_id="S1-subsumption-chain",
  variables={}, filtering_rule="n/a", ensemble_convention="n/a", tie_handling="n/a",
  independence="n/a", claim_kind="structural meta-claim about artifact subsumption",
  proposed_inequality="8e9b8d5285aa is the base case generalized by T2 then T3",
  executable="no - claim about artifact relationships; note 8e9b8d5285aa itself was refuted by a program check (structurally invalid), so the chain's base is not a censused theory",
  ambiguities=["base artifact structurally invalid"],
 ),
 "324c6fa95403": dict(
  theorem_id="S2-T5-weakens-T4",
  variables={}, filtering_rule="n/a", ensemble_convention="n/a", tie_handling="n/a",
  independence="n/a", claim_kind="reduction claim (T5 is a weakening of T4)",
  proposed_inequality="window(T4) subset window(T5); T4 adds sufficiency gates",
  executable="partially - the window nesting k/(k+2) < k/(k+1) is checkable algebra; the sufficiency part inherits T4's verdict",
  ambiguities=[],
 ),
 "862de34bced3": dict(
  theorem_id="S3-window-nesting",
  variables={}, filtering_rule="n/a", ensemble_convention="odd k >= 7", tie_handling="n/a",
  independence="n/a", claim_kind="algebraic nesting claim",
  proposed_inequality="k/(k+2) < k/(k+1) for k > 0",
  executable="yes - trivial algebra",
  ambiguities=[],
 ),
 "457a95bed9d3": dict(
  theorem_id="S5-MI-collapse-claim",
  variables={}, filtering_rule="n/a", ensemble_convention="odd k >= 7", tie_handling="n/a",
  independence="i.i.d. errors, conditionally independent flags",
  claim_kind="reduction claim: T12's MI inequality collapses to T4's window under i.i.d. specialization",
  proposed_inequality="I(C;B) > I(C;M_wrong) evaluates to exactly 1/(k+1) < e < k/(k+2) under the stated restriction",
  executable="yes in principle - both sides computable under the specialization; the 'exactly that interval' claim is strong and testable",
  ambiguities=["suspended_unsupported: its support parent T12 was court-refuted, so grounded semantics suspended it",
               "'exactly' is doing enormous work - MI depends on P and R, the interval does not"],
 ),
 "a6806e68a370": dict(
  theorem_id="S6-MI-specialization-formula",
  variables={"D(x||y)": "binary KL divergence (as written, applied to rate pairs)"},
  filtering_rule="n/a", ensemble_convention="odd k", tie_handling="n/a",
  independence="binary-error/binary-flag model, uniform prior",
  claim_kind="reduction claim with an explicit (truncated) MI decomposition I = e*D(P||e) + (1-e)*D(R||...)",
  proposed_inequality="P > e and R > 1-e is the specialization of I(C;B) > I(C;M_wrong)",
  executable="partially - the stated decomposition is checkable against the true MI formula; the artifact text is truncated mid-formula in the record",
  ambiguities=["suspended_unsupported (parent T12 refuted)", "formula truncated in the emission",
               "D(P||e) applies KL to a precision and a base rate - dimensionally suspect"],
 ),
 "3c2294e39422": dict(
  theorem_id="S4-k1-degenerate-reduction",
  variables={}, filtering_rule="n/a", ensemble_convention="claims k=1 collapse", tie_handling="n/a",
  independence="n/a", claim_kind="dimensional-reduction claim",
  proposed_inequality="p_min(e,r,1) equals the pairwise veto tradeoff",
  executable="no as stated - p_min contains (k-1) factors, so k=1 gives 0/0 and a division by zero; the reduction is formally undefined",
  ambiguities=["k=1 substitution undefined in T7's formula"],
 ),
}


def main() -> None:
    h = Harness(ROOT)
    st = h.state
    rows = []
    for aid, artifact in st.artifacts.items():
        role = artifact.provenance.role.value
        if role not in ("conjecturer", "synthesizer"):
            continue
        short = aid[:12]
        ann = ANNOTATIONS.get(short)
        status = st.status[aid].value
        attackers = [
            {"warrant": w.id, "type": w.type.value}
            for w in h.warrants.values() if w.target == aid
        ]
        if ann is None:
            if status == "refuted" and all(a["type"] == "demonstrative" for a in attackers):
                continue  # structurally invalid emission; outside census scope
            raise SystemExit(f"structurally relevant artifact without annotation: {short}")
        ref = artifact.content_ref
        content = ref[7:] if ref.startswith("inline:") else ref
        parents = [r.target[:12] for r in artifact.interface.refs] if artifact.interface.refs else []
        rows.append({
            "artifact_id": aid,
            "final_status": status,
            "provenance_role": role,
            "parents_or_refs": parents,
            "complete_claim": content,
            "refutation_path": (
                "none" if status == "accepted" else
                "sustained defended argumentative trial" if any(a["type"] == "argumentative" for a in attackers)
                else "deterministic program check" if attackers
                else f"none - status {status} (grounded-semantics support change, not an attack)"),
            "warrants_against": attackers,
            **{k: v for k, v in ann.items()},
        })
    census = {
        "schema": "deepreason-glm-judge-theory-census-v1",
        "root": str(ROOT),
        "scope": ("every structurally valid conjecturer or synthesizer artifact: "
                  "14 standing plus 2 refuted by sustained defended trials; the 30 "
                  "program-refuted emissions are structurally invalid representations "
                  "and are excluded (their refutations say nothing about mathematical content)"),
        "annotation_provenance": "operator committed reading; symbols are artifact-local and never merged",
        "known_inconsistencies": [
            "three distinct fragility-window upper bounds coexist: k/(k+2) (T4,T6,T7), k/(k+1) (T5), 1/2 (T8,T9) - not mutually consistent as stated",
            "T11 (perfect-precision tail wins outside the window) directly contradicts the window-necessity claims of T5/T8/T9",
            "two distinct precision thresholds: closed-form p_min (T7) vs realized-ratio threshold (T6)",
            "precision-vs-FPR substitution in T7's mechanism is unproven",
        ],
        "artifacts": sorted(rows, key=lambda r: r["theorem_id"]),
    }
    OUT.write_text(json.dumps(census, indent=1, sort_keys=False))
    print(f"census: {len(rows)} artifacts")


if __name__ == "__main__":
    main()
