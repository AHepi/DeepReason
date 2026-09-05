"""Grounded record fixtures and separately stipulated appraisal interpretations.

All shown bodies and activation assessments are fixture data, not real studies.
The tests establish reference/label behavior, not truth of semantic predicates.
"""
from dataclasses import replace
from reference_kernel import Application as A, Case, ClaimKey, Entry as E, RecordModel, Reference as R, validate_slice


def key(predicate, before="xi0", after="xi1", contribution="delta1"):
    return ClaimKey(predicate, "s:contribution", "fixture_history", "s", "explanatory",
                    contribution, before, after, "stated_local_respect", "fixture-I-1")


def _entry(eid, created, refs, prior, kind="Record", actor="s"):
    return E(eid, actor, kind, frozenset(prior), frozenset(created), list(refs))


def balances():
    initial = frozenset({"p0", "b", "k_ref", "k_disc", "k_alg"})
    entries = []
    prev = []
    def add(eid, creates, refs=(), kind="Record", actor="s"):
        entries.append(_entry(eid, creates, refs, prev[-1:], kind, actor))
        prev.append(eid)
    add("e1", ["attention"], [R("p0"), R("b")], "Attend")
    add("e2", ["X1"], [R("p0")], "EnterConjecture")
    add("e2b", ["X2"], [R("p0")], "EnterConjecture")
    add("a0", ["w_initial"], [R("X1"), R("k_ref")], "SubmitCase", "rec")
    add("e3", ["c_ref"], [R("k_ref"), R("k_disc")], "Criticize", "rec")
    add("review1", ["assessment1"], [R("w_initial"), R("c_ref")], "AssessApplication", "rec")
    cut1 = frozenset(prev)
    add("e4", ["p1", "T4"], [R("p0"), R("c_ref"), R("p1", True), R("T4", True)], "Respond")
    add("e5", ["XM"], [R("p1"), R("b")], "EnterConjecture")
    add("e6", ["c_lim"], [R("X1"), R("XM"), R("k_alg")], "Criticize")
    add("e7", ["u_lim"], [R("c_lim"), R("p1")], "Respond")
    add("a1", ["w_lim"], [R("u_lim"), R("XM"), R("k_alg")], "SubmitCase", "rec")
    add("a2", ["w_progress"], [R("w_lim"), R("p0"), R("p1")], "SubmitCase", "rec")
    add("review2", ["assessment2"], [R("w_progress")], "AssessApplication", "rec")
    cut2 = frozenset(prev)
    add("e8", ["c_rule"], [R("k_alg"), R("k_disc")], "Criticize", "rec")
    add("review3", ["assessment3"], [R("c_rule")], "AssessApplication", "rec")
    cut3 = frozenset(prev)
    add("e9", ["c_counter"], [R("c_rule"), R("k_disc")], "Criticize")
    add("review4", ["assessment4"], [R("c_counter")], "AssessApplication", "rec")
    cut4 = frozenset(prev)
    add("e10", ["c_physical"], [R("XM"), R("k_disc")], "Criticize", "rec")
    add("review5", ["assessment5"], [R("c_physical")], "AssessApplication", "rec")
    cut5 = frozenset(prev)
    add("close", ["closed"], [R("p1")], "EngagementChange")
    model = RecordModel(initial, entries)
    src = {"ref": "k_ref", "disc": "k_disc", "initial": "w_initial", "crit_ref": "c_ref"}
    base = [A("ref"), A("disc"), A("initial", frozenset({"ref"})),
            A("crit_ref", frozenset({"disc"}), frozenset({"ref"}), role="criticism")]
    k0, kl, kp = key("Account", after="not_applicable"), key("Limitation"), key("Progress")
    c0 = Case("w_initial", k0, "positive", "initial")
    more = [A("alg"), A("xm_formal"), A("xm_physical"),
            A("crit_lim", frozenset({"alg", "xm_formal"}), role="criticism"),
            A("lim", frozenset({"crit_lim"})), A("progress", frozenset({"lim"}))]
    src2 = dict(src, alg="k_alg", xm_formal="XM", xm_physical="XM",
                crit_lim="c_lim", lim="w_lim", progress="w_progress")
    cases2 = [c0, Case("w_lim", kl, "positive", "lim"), Case("w_progress", kp, "positive", "progress")]
    stage_nodes = [base, base + more,
                   base + more + [A("crit_rule", frozenset({"disc"}), frozenset({"alg"}), role="criticism")]]
    stage_nodes.append(stage_nodes[-1] + [A("counter", frozenset({"disc"}), frozenset({"crit_rule"}), role="criticism")])
    stage_nodes.append(stage_nodes[-1] + [A("physical", frozenset({"disc"}), frozenset({"xm_physical"}), role="criticism")])
    sources = [src, src2, dict(src2, crit_rule="c_rule"),
               dict(src2, crit_rule="c_rule", counter="c_counter"),
               dict(src2, crit_rule="c_rule", counter="c_counter", physical="c_physical")]
    stages = []
    for i, (cut, nodes, subjects) in enumerate(zip([cut1, cut2, cut3, cut4, cut5], stage_nodes, sources), 1):
        apps = [replace(a, assessment=f"assessment{i}") for a in nodes]
        cases = [c0] if i == 1 else cases2
        validate_slice(model, cut, apps, subjects, cases)
        stages.append({"name": f"balances-r{i}", "model": model, "cut": cut,
                       "apps": apps, "cases": cases, "subjects": subjects,
                       "query": k0 if i == 1 else kp})
    return stages


def seasons():
    initial = frozenset({"XP", "p", "b", "b_new", "k_mech", "k_time", "k_scope"})
    entries, prior = [], []
    def add(eid, creates, refs=(), kind="Record", actor="s"):
        entries.append(_entry(eid, creates, refs, prior[-1:], kind, actor))
        prior.append(eid)
    add("s1", ["attention"], [R("XP"), R("p")], "Attend")
    add("s2", ["XA0"], [R("p"), R("b")], "EnterConjecture")
    add("s3", ["c_old"], [R("XP"), R("k_mech")], "Criticize")
    add("s4", ["adoption"], [R("c_old"), R("XA0")], "Respond")
    add("s5", ["c_lag"], [R("XA0"), R("k_time")], "Criticize", "rec")
    add("s6", ["XA1", "T6"], [R("XA0"), R("c_lag"), R("b_new"), R("XA1", True)], "Respond")
    add("s7", ["w_adequacy"], [R("XA1"), R("b_new"), R("k_time")], "SubmitCase", "rec")
    add("s8", ["w_gain"], [R("w_adequacy"), R("XA0"), R("XA1")], "SubmitCase", "rec")
    add("sr1", ["s_assessment1"], [R("w_gain")], "AssessApplication", "rec")
    cut1 = frozenset(prior)
    add("s9", ["w_negative"], [R("XA1"), R("k_scope")], "SubmitCase", "rec")
    add("s10", ["conflict_account"], [R("w_negative"), R("w_adequacy")], "Appraise", "rec")
    add("sr2", ["s_assessment2"], [R("conflict_account")], "AssessApplication", "rec")
    cut2 = frozenset(prior)
    add("s11", ["c_negative_scope"], [R("w_negative"), R("k_scope")], "Criticize")
    add("sr3", ["s_assessment3"], [R("c_negative_scope")], "AssessApplication", "rec")
    cut3 = frozenset(prior)
    model = RecordModel(initial, entries)
    ka, kp = key("Account", "seasons_xi1", "not_applicable", "seasons_delta"), key("Progress", "seasons_xi0", "seasons_xi1", "seasons_delta")
    base = [A("time"), A("scope"), A("adequacy", frozenset({"time"})),
            A("adequacy_use", frozenset({"adequacy"})), A("gain", frozenset({"adequacy_use"}))]
    sources = dict(time="k_time", scope="k_scope", adequacy="w_adequacy", adequacy_use="w_adequacy", gain="w_gain")
    c1 = [Case("w_adequacy", ka, "positive", "adequacy"), Case("w_gain", kp, "positive", "gain")]
    mid = base + [A("negative", frozenset({"scope"})),
                  A("conflict", frozenset({"negative"}), frozenset({"adequacy_use"}))]
    last = mid + [A("scope_criticism", frozenset({"scope"}), frozenset({"negative"}), role="criticism")]
    src2 = dict(sources, negative="w_negative", conflict="conflict_account")
    src3 = dict(src2, scope_criticism="c_negative_scope")
    stages = []
    for i, (cut, nodes, subjects) in enumerate(zip([cut1, cut2, cut3], [base, mid, last], [sources, src2, src3]), 1):
        apps = [replace(a, assessment=f"s_assessment{i}") for a in nodes]
        cases = c1 if i == 1 else c1 + [Case("w_negative", ka, "negative", "negative")]
        validate_slice(model, cut, apps, subjects, cases)
        stages.append({"name": f"seasons-r{i}", "model": model, "cut": cut,
                       "apps": apps, "cases": cases, "subjects": subjects, "query": kp})
    return stages
