"""Regression cases for finite bookkeeping and explicitly stipulated countermodels.

The semantic fixtures here assign meanings for the purpose of testing a rule.
They are not experiments demonstrating real-world creativity or understanding.
"""
from __future__ import annotations
from dataclasses import replace
from itertools import product
import unittest

from reference_kernel import (
    Application as A, Case, Check, ClaimKey, ContractError, Entry as E,
    RecordModel, Reference as R, appraise, case_state, finite_variation_summary,
    match_contribution, merge_view, report,
)

BASE = ClaimKey("OCA", "system_s:content_x", "history_h", "boundary_s", "explanatory",
                "contribution_e1", "situation_0", "situation_1", "reconstruction", "I-1")
BINDINGS = {"authority_digest": "fixture-authority", "specification_digest": "fixture-spec",
            "interpretation_version": "I-1", "profile_version": "fixture-profile",
            "checker_version": "reference-1.1", "policy_version": "DA-1"}


def entry(eid, causes=(), creates=(), payload=None, kind="Record", actor="s", parents=()):
    return E(eid, actor, kind, frozenset(causes), frozenset(creates), payload, tuple(parents))


def minimal_balances():
    """Two rival contents coexist; response and transport are created atomically."""
    initial = frozenset({"p0", "b", "k_ref", "k_disc", "k_alg"})
    events = [
        entry("e1", creates=("attention",), payload=[R("p0"), R("b")], kind="Attend"),
        entry("e2", ("e1",), ("X1",), [R("p0"), R("b")], "EnterConjecture"),
        entry("e2b", ("e1",), ("X2",), [R("p0"), R("b")], "EnterConjecture"),
        entry("e3", ("e2",), ("c_ref",), [R("k_ref"), R("k_disc"), R("X1")], "Criticize"),
        entry("e4", ("e3",), ("p1", "T4"),
              [R("c_ref"), R("p0"), R("p1", True), R("T4", True)], "Respond",
              parents=(("p1", "p0"),)),
        entry("e5", ("e4",), ("XM",), [R("p1"), R("b")], "EnterConjecture"),
        entry("e6", ("e5",), ("c_lim",), [R("XM"), R("k_alg"), R("X1")], "Criticize"),
        entry("e7", ("e6",), ("limitation",), [R("c_lim"), R("p1")], "Respond"),
        entry("e8", ("e7", "e2b"), ("comparison",),
              [R("X1"), R("X2"), R("limitation")], "Compare"),
        entry("e9", ("e8",), ("closed_for_now",), [R("p1")], "EngagementChange"),
    ]
    return RecordModel(initial, events)


class RecordTests(unittest.TestCase):
    def test_balances_full_record_is_grounded(self):
        model = minimal_balances()
        self.assertEqual(len(model.validate_cut(e.id for e in model.entries)), 10)

    def test_balances_prefix_and_cut_digest_are_inert(self):
        model = minimal_balances()
        cut = {"e1", "e2", "e3"}
        self.assertEqual(model.digest(cut), model.digest(reversed(sorted(cut))))

    def test_rivals_can_coexist(self):
        model = minimal_balances()
        self.assertIn("e2b", model.validate_cut({"e1", "e2", "e2b"}))

    def test_counterfactual_rival_cannot_ground_actual_comparison(self):
        base = minimal_balances()
        with self.assertRaisesRegex(ContractError, "incompatible causal history"):
            RecordModel(base.initial, base.entries, (frozenset({"e2", "e2b"}),))

    def test_atomic_result_transport_is_allowed(self):
        model = minimal_balances()
        self.assertTrue(model.validate_cut({"e1", "e2", "e3", "e4"}))

    def test_external_future_transport_is_rejected(self):
        with self.assertRaisesRegex(ContractError, "ungrounded historical"):
            RecordModel(frozenset(), [entry("respond", creates=("y",), payload=R("T")),
                                     entry("later", ("respond",), ("T",))])

    def test_local_reference_cannot_name_nonlocal_artifact(self):
        with self.assertRaisesRegex(ContractError, "ungrounded local"):
            RecordModel(frozenset({"old"}), [entry("e", payload=R("old", True))])

    def test_hidden_nested_reference_is_checked(self):
        with self.assertRaisesRegex(ContractError, "missing_ground"):
            RecordModel(frozenset({"target"}), [entry("e", creates=("c",),
                payload={"target": R("target"), "body": [{"ground": R("missing_ground")}]} )])

    def test_target_only_template_eligibility_is_insufficient(self):
        available = {"target"}
        legacy_eligible = "target" in available
        self.assertTrue(legacy_eligible)
        with self.assertRaises(ContractError):
            RecordModel(frozenset(available), [entry("c", payload=[R("target"), R("standard")])])

    def test_duplicate_artifact_id_across_concurrent_events_is_rejected(self):
        with self.assertRaisesRegex(ContractError, "duplicate"):
            RecordModel(frozenset(), [entry("a", creates=("x",)), entry("b", creates=("x",))])

    def test_initial_artifact_cannot_be_recreated(self):
        with self.assertRaisesRegex(ContractError, "duplicate"):
            RecordModel(frozenset({"x"}), [entry("e", creates=("x",))])

    def test_duplicate_event_id_is_rejected(self):
        with self.assertRaisesRegex(ContractError, "duplicate entry"):
            RecordModel(frozenset(), [entry("e"), entry("e")])

    def test_causal_cycle_is_rejected(self):
        with self.assertRaisesRegex(ContractError, "causal cycle"):
            RecordModel(frozenset(), [entry("a", ("b",)), entry("b", ("a",))])

    def test_unknown_cause_is_rejected(self):
        with self.assertRaisesRegex(ContractError, "unknown cause"):
            RecordModel(frozenset(), [entry("e", ("missing",))])

    def test_non_downward_closed_cut_is_rejected(self):
        model = RecordModel(frozenset(), [entry("a"), entry("b", ("a",))])
        with self.assertRaisesRegex(ContractError, "downward"):
            model.validate_cut({"b"})

    def test_alternative_criticism_actions_are_representable(self):
        m = RecordModel(frozenset({"target"}),
                        [entry("a", payload=R("target"), kind="Criticize"),
                         entry("b", payload=R("target"), kind="Criticize")],
                        (frozenset({"a", "b"}),))
        self.assertEqual(m.validate_cut({"a"}), frozenset({"a"}))
        with self.assertRaisesRegex(ContractError, "alternative"):
            m.validate_cut({"a", "b"})

    def test_ancestry_from_initial_content(self):
        m = RecordModel(frozenset({"old"}),
                        [entry("e", creates=("new",), parents=(("new", "old"),))])
        self.assertTrue(m.validate_cut({"e"}))

    def test_self_ancestry_is_rejected(self):
        with self.assertRaisesRegex(ContractError, "ancestry"):
            RecordModel(frozenset(), [entry("e", creates=("x",), parents=(("x", "x"),))])

    def test_absorption_preserves_old_events(self):
        self.assertEqual(merge_view({"new"}, {"old"}, {"old", "new"}), {"old", "new"})
        legacy_forward_only = {e for e, time in (("old", 1),) if 3 <= time}
        self.assertEqual(legacy_forward_only, set())

    def test_absorption_does_not_import_future(self):
        with self.assertRaises(ContractError):
            merge_view({"now"}, {"future"}, {"now"})

    def test_terminal_target_and_closed_episode_are_representable(self):
        m = RecordModel(frozenset({"p"}), [entry("last", payload=R("p"), kind="EngagementChange")])
        self.assertEqual(m.validate_cut({"last"}), {"last"})

    def test_same_actor_may_act_as_recorder_and_target(self):
        m = RecordModel(frozenset(), [entry("a", creates=("x",), actor="s"),
            entry("b", ("a",), ("case",), R("x"), "SubmitCase", actor="s")])
        self.assertTrue(m.validate_cut({"a", "b"}))

    def test_digest_changes_with_content(self):
        a = RecordModel(frozenset(), [entry("e", payload="first")])
        b = RecordModel(frozenset(), [entry("e", payload="second")])
        self.assertNotEqual(a.digest({"e"}), b.digest({"e"}))


class AppraisalTests(unittest.TestCase):
    def test_ordinary_observation_defeat_reaches_dependent_criticism(self):
        labels = appraise([A("observation", role="observation_use"),
                           A("criticism", frozenset({"observation"}), role="criticism"),
                           A("undercut", targets=frozenset({"observation"}))])
        self.assertEqual(labels.of("observation"), "out")
        self.assertEqual(labels.of("criticism"), "out")

    def test_standard_defeat_reaches_criticism_without_exemption(self):
        labels = appraise([A("standard", role="standard_use"),
                           A("criticism", frozenset({"standard"}), role="criticism"),
                           A("challenge", targets=frozenset({"standard"}))])
        self.assertEqual(labels.of("criticism"), "out")

    def test_independent_application_survives_loss_of_other_support(self):
        labels = appraise([A("p"), A("arg1", frozenset({"p"})), A("arg2"),
                           A("attack", targets=frozenset({"p"}))])
        self.assertEqual(labels.of("arg1"), "out")
        self.assertEqual(labels.of("arg2"), "in")

    def test_unknown_premise_prevents_dependent_in(self):
        labels = appraise([A("p", readiness=Check.UNKNOWN), A("u", frozenset({"p"}))])
        self.assertEqual(labels.of("u"), "undecided")

    def test_failed_body_does_not_count_without_a_criticism(self):
        apps = [A("failed_test", readiness=Check.FAIL)]
        out = report(BASE, [Case("w", BASE, "positive", "failed_test")], apps, "cut", BINDINGS)
        self.assertEqual(out["raw"], "POSITIVE_CASE_ONLY")
        self.assertEqual(out["usable"], "NO_CASE")
        # The old grounded function includes every unattacked argument regardless of body checks.
        old_unattacked_grounded = {"failed_test"}
        self.assertIn("failed_test", old_unattacked_grounded)
        self.assertEqual(out["semantic_decision"], "NOT_EVALUATED")

    def test_missing_activation_is_unknown_not_in(self):
        self.assertEqual(appraise([A("u", assessment="")]).of("u"), "undecided")

    def test_mutual_opposition_is_undecided(self):
        labels = appraise([A("a", targets=frozenset({"b"})), A("b", targets=frozenset({"a"}))])
        self.assertEqual(labels.undecided, {"a", "b"})

    def test_external_defeater_resolves_cycle(self):
        labels = appraise([A("a", targets=frozenset({"b"})), A("b", targets=frozenset({"a"})),
                           A("c", targets=frozenset({"b"}))])
        self.assertEqual(labels.inside, {"a", "c"})
        self.assertEqual(labels.outside, {"b"})

    def test_support_cycle_does_not_bootstrap(self):
        self.assertEqual(appraise([A("a", frozenset({"b"})), A("b", frozenset({"a"}))]).undecided,
                         {"a", "b"})

    def test_reinstatement_after_countercriticism(self):
        before = [A("w"), A("attack", targets=frozenset({"w"}))]
        after = before + [A("counter", targets=frozenset({"attack"}))]
        self.assertEqual(appraise(before).of("w"), "out")
        self.assertEqual(appraise(after).of("w"), "in")

    def test_failed_attack_does_not_defeat(self):
        labels = appraise([A("w"), A("a", targets=frozenset({"w"}), readiness=Check.FAIL)])
        self.assertEqual(labels.of("w"), "in")

    def test_unknown_attack_is_not_silently_erased(self):
        labels = appraise([A("w"), A("a", targets=frozenset({"w"}), readiness=Check.UNKNOWN)])
        self.assertEqual(labels.of("w"), "undecided")

    def test_missing_dependency_is_contract_error(self):
        with self.assertRaises(ContractError):
            appraise([A("a", frozenset({"unregistered_ordinary_premise"}))])

    def test_annotation_is_not_an_essential_dependency(self):
        labels = appraise([A("annotation", readiness=Check.FAIL), A("u")])
        self.assertEqual(labels.of("u"), "in")

    def test_empty_appraisal_is_defined(self):
        self.assertEqual(appraise([]).inside, set())

    def test_two_cases_do_not_become_truth(self):
        cases = [Case("p", BASE, "positive", "p"), Case("n", BASE, "negative", "n")]
        out = report(BASE, cases, [A("p"), A("n")], "cut", BINDINGS)
        self.assertEqual(out["usable"], "BOTH_CASES")
        self.assertEqual(out["semantic_decision"], "NOT_EVALUATED")
        self.assertNotIn("true", out)

    def test_duplicate_presence_bit_does_not_discard_case_ids(self):
        cases = [Case("p1", BASE, "positive", "a"), Case("p2", BASE, "positive", "b")]
        out = report(BASE, cases, [A("a"), A("b")], "cut", BINDINGS)
        self.assertEqual(out["raw"], "POSITIVE_CASE_ONLY")
        self.assertEqual(len(out["raw_case_ids"]), 2)

    def test_foreign_boundary_does_not_answer_query(self):
        foreign = replace(BASE, boundary="someone_else")
        out = report(BASE, [Case("f", foreign, "positive", "a")], [A("a")], "cut", BINDINGS)
        self.assertEqual(out["raw"], "NO_CASE")

    def test_missing_binding_is_rejected(self):
        with self.assertRaises(ContractError):
            report(BASE, [], [], "cut", {})

    def test_wrong_interpretation_binding_is_rejected(self):
        with self.assertRaises(ContractError):
            report(BASE, [], [], "cut", dict(BINDINGS, interpretation_version="I-other"))

    def test_newness_completeness_guard_is_essential(self):
        labels = appraise([A("coverage"), A("newness_case", frozenset({"coverage"})),
                           A("coverage_criticism", targets=frozenset({"coverage"}))])
        self.assertEqual(labels.of("newness_case"), "out")


class ProjectionAndCountermodelTests(unittest.TestCase):
    def test_same_contribution_keys_match_only_correct_predicates(self):
        self.assertTrue(match_contribution(BASE, replace(BASE, predicate="Attempt"),
            replace(BASE, predicate="New"), replace(BASE, predicate="Authors")))
        self.assertFalse(match_contribution(BASE, BASE, BASE, BASE))

    def test_later_authorship_cannot_validate_earlier_act(self):
        attempted = replace(BASE, predicate="Attempt")
        new = replace(BASE, predicate="New")
        later = replace(BASE, predicate="Authors", contribution="e2")
        self.assertFalse(match_contribution(BASE, attempted, new, later))
        # Original formula omitted the contribution index from Authors.
        authored_somewhere_in_history = True
        self.assertTrue(True and True and authored_somewhere_in_history)

    def test_reconstruction_not_disqualified_by_received_equivalent(self):
        # A stipulated semantic case, not an empirical attribution.
        authored_reconstruction = True
        prior_possessed_equivalent = False
        received_equivalent = True
        old_origin_gate = authored_reconstruction and not received_equivalent
        correct_oca_in_this_interpretation = authored_reconstruction and not prior_possessed_equivalent
        self.assertFalse(old_origin_gate)
        self.assertTrue(correct_oca_in_this_interpretation)

    def test_inherited_target_and_original_response_need_not_share_lineage(self):
        connected_critical_episode = True
        connected_originative_response = True
        target_descends_from_response = False
        self.assertFalse(connected_critical_episode and target_descends_from_response)
        self.assertTrue(connected_critical_episode and connected_originative_response)

    def test_good_inherited_explanation_does_not_require_oca(self):
        good_in_stipulated_respect, originated_by_user = True, False
        self.assertFalse(good_in_stipulated_respect and originated_by_user)
        self.assertTrue(good_in_stipulated_respect)

    def test_false_easy_variants_not_mistaken_for_rigidity(self):
        variants = [{"material": True, "actually_adequate": False, "free_claimed_work": True}]
        old_htv = all(not (v["material"] and v["actually_adequate"]) for v in variants)
        self.assertTrue(old_htv)
        self.assertEqual(finite_variation_summary(True, [v["free_claimed_work"] for v in variants]),
                         "FREE_VARIANT_CASE_FOUND")

    def test_empty_variation_family_is_uninformative(self):
        self.assertTrue(all([]))  # The empty universal in the old HTV formula.
        self.assertEqual(finite_variation_summary(True, []), "UNINFORMATIVE_FAMILY")

    def test_renaming_only_variations_are_uninformative(self):
        self.assertEqual(finite_variation_summary(False, [False]), "UNINFORMATIVE_FAMILY")

    def test_no_free_variant_in_range_is_not_universal_hardness(self):
        self.assertEqual(finite_variation_summary(True, [False]), "NO_FREE_VARIANT_CASE_FOUND_IN_V")

    def test_record_completeness_is_not_repertoire_completeness(self):
        recorded = {"x"}
        actual_repertoire = {"x", "forgotten_y"}
        self.assertEqual(recorded, set(sorted(recorded)))
        self.assertNotEqual(recorded, actual_repertoire)

    def test_same_final_action_can_use_different_reasons(self):
        episodes = [("suspend", "instrument ambiguity"), ("suspend", "missing boundary condition")]
        self.assertEqual(episodes[0][0], episodes[1][0])
        self.assertNotEqual(episodes[0][1], episodes[1][1])

    def test_community_availability_is_distinct_from_creator_retention(self):
        creator_retains, named_community_retains = False, True
        self.assertTrue(creator_retains or named_community_retains)
        self.assertFalse(creator_retains)

    def test_changed_evidence_does_not_change_fixed_historical_claim(self):
        historical_truth_in_model = {"progress_at_xi0_xi1": False}
        appraisal_then, appraisal_now = "holds", "fails"
        self.assertNotEqual(appraisal_then, appraisal_now)
        self.assertFalse(historical_truth_in_model["progress_at_xi0_xi1"])

    def test_supplied_answer_does_not_meet_unsupplied_solution_respect(self):
        reconstructed_supplied_answer = True
        achievement_respect = "originate_unsupplied_solution"
        self.assertTrue(reconstructed_supplied_answer)
        self.assertNotEqual(achievement_respect, "reconstruct_supplied_explanation")

    def test_finite_coverage_is_compatible_with_domain_barrier(self):
        observed = {"p1": True, "p2": True}
        unrestricted = dict(observed, p3=True)
        bounded = dict(observed, p3=False)
        self.assertEqual({k: unrestricted[k] for k in observed}, observed)
        self.assertEqual({k: bounded[k] for k in observed}, observed)
        self.assertNotEqual(all(unrestricted.values()), all(bounded.values()))

    def test_balances_invariance_exact_rational_examples(self):
        from fractions import Fraction
        x, a, b = Fraction(12), Fraction(-2), Fraction(0)
        for shift in (Fraction(-7), Fraction(1, 3), Fraction(20)):
            self.assertEqual((x + shift) + (a - shift), 10)
            self.assertEqual((x + shift) + (b - shift), 12)
        self.assertEqual(b - a, 2)


class ExhaustivePolicyTests(unittest.TestCase):
    def test_all_two_node_graphs_match_least_complete_labeling(self):
        """Independent enumeration of 2,304 graph/readiness cases and fixed points."""
        names = ("0", "1")
        edge_slots = tuple(product(names, repeat=2))
        states = ("in", "out", "undecided")
        count = 0
        for dep_mask in range(16):
            deps = {x: {y for k, (a, y) in enumerate(edge_slots) if a == x and dep_mask & (1 << k)}
                    for x in names}
            for attack_mask in range(16):
                targets = {x: {y for k, (a, y) in enumerate(edge_slots) if a == x and attack_mask & (1 << k)}
                           for x in names}
                attackers = {x: {a for a in names if x in targets[a]} for x in names}
                for readiness in product(Check, repeat=2):
                    ready = dict(zip(names, readiness))
                    apps = [A(x, frozenset(deps[x]), frozenset(targets[x]), ready[x]) for x in names]
                    computed = appraise(apps)
                    complete = []
                    for values in product(states, repeat=2):
                        lab = dict(zip(names, values))
                        output = {}
                        for x in names:
                            if (ready[x] == Check.FAIL or any(lab[y] == "out" for y in deps[x])
                                or any(lab[y] == "in" for y in attackers[x])):
                                output[x] = "out"
                            elif (ready[x] == Check.PASS and all(lab[y] == "in" for y in deps[x])
                                  and all(lab[y] == "out" for y in attackers[x])):
                                output[x] = "in"
                            else:
                                output[x] = "undecided"
                        if output == lab:
                            complete.append(lab)
                    self.assertTrue(complete)
                    actual = {x: computed.of(x) for x in names}
                    self.assertIn(actual, complete)
                    for lab in complete:
                        self.assertTrue(all(actual[x] == "undecided" or actual[x] == lab[x] for x in names))
                    for a in apps:
                        if computed.of(a.id) == "in":
                            self.assertTrue(a.essential.issubset(computed.inside))
                    self.assertLessEqual(computed.rounds, 4)
                    count += 1
        self.assertEqual(count, 2304)



class IntegratedFixtureTests(unittest.TestCase):
    def test_balances_method_challenge_reaches_critic_and_progress(self):
        from fixtures import balances
        stages = balances()
        self.assertEqual(appraise(stages[0]["apps"]).of("initial"), "out")
        self.assertEqual(appraise(stages[1]["apps"]).of("progress"), "in")
        self.assertEqual(appraise(stages[2]["apps"]).of("crit_lim"), "out")
        self.assertEqual(appraise(stages[2]["apps"]).of("progress"), "out")
        self.assertEqual(appraise(stages[3]["apps"]).of("progress"), "in")

    def test_physical_model_criticism_does_not_refute_conditional_algebra(self):
        from fixtures import balances
        labels = appraise(balances()[4]["apps"])
        self.assertEqual(labels.of("xm_physical"), "out")
        self.assertEqual(labels.of("xm_formal"), "in")
        self.assertEqual(labels.of("lim"), "in")

    def test_seasons_contrary_case_is_not_silently_bypassed(self):
        from fixtures import seasons
        stages = seasons()
        self.assertEqual(appraise(stages[0]["apps"]).of("gain"), "in")
        self.assertEqual(appraise(stages[1]["apps"]).of("adequacy"), "in")
        self.assertEqual(appraise(stages[1]["apps"]).of("adequacy_use"), "out")
        self.assertEqual(appraise(stages[1]["apps"]).of("gain"), "out")
        self.assertEqual(appraise(stages[2]["apps"]).of("gain"), "in")

    def test_future_assessment_cannot_be_used_at_earlier_cut(self):
        from fixtures import balances
        from reference_kernel import validate_slice
        stage = balances()[0]
        bad_apps = [replace(a, assessment="assessment2") for a in stage["apps"]]
        with self.assertRaisesRegex(ContractError, "activation assessment"):
            validate_slice(stage["model"], stage["cut"], bad_apps, stage["subjects"], stage["cases"])


class SnapshotIsolationTests(unittest.TestCase):
    def test_mutating_input_payload_does_not_mutate_validated_snapshot(self):
        payload = {"body": [R("initial")]}
        model = RecordModel(frozenset({"initial"}), [entry("e", payload=payload)])
        before = model.digest({"e"})
        payload["body"].append(R("unavailable"))
        self.assertEqual(before, model.digest({"e"}))
        with self.assertRaises(TypeError):
            model.entries[0].payload["other"] = "change"


if __name__ == "__main__":
    unittest.main(verbosity=2)
