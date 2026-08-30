"""Test each of PARKED.md P2's three priced roads against R-g's binding form.

This is ANALYSIS, not a decision. It does not choose a road; it shows which
roads actually REMOVE the disadvantage R-g forbids and which only describe it,
so the operator's choice is narrowed by law rather than by preference.

The law under test, verbatim (docs/proposals/DUAL_MODE_CONJECTURE_PREPLAN.md
R-g, lines 42-57):

    no mechanism in this program -- nor anywhere in the harness -- may
    require formal encoding for a conjecture to enter, rank, survive, or be
    accepted; may weight ranking, scheduling, or acceptance on a
    conjecture's KIND ... Formal backing may confer PROTECTION
    (prose-immunity, as today); its absence confers no disadvantage. D3's
    and D4's regressions must prove kind-blindness: an informal
    conjecture's rank, criticism exposure, and acceptance path are
    byte-identical whether or not the formal channel exists in the build.

Note the clause "may weight ranking ... on a conjecture's KIND" is
DIRECTION-NEUTRAL. CLAUDE.md's headline sentence ("nothing may penalize a
conjecture for being informal") is one-directional; R-g's is not. Probe L3
below is grounded on R-g's clause, not on the headline.

Four probes, each a direct consequence of a quoted clause:

  L1  EQUAL STANDING ("its absence confers no disadvantage"). An informal
      survivor and a formal survivor, equal on every axis the harness
      actually measured for both, must both be on the frontier.

  L2  KIND-BLINDNESS / BYTE-IDENTITY ("byte-identical whether or not the
      formal channel exists in the build"). The informal survivor's frontier
      membership must be the same with a formally-backed sibling present as
      it is in a build where no artifact carries an evaluable commitment.

  L3  NO WEIGHT IN THE OTHER DIRECTION ("may weight ranking ... on a
      conjecture's KIND", direction-neutral). A commitment-free survivor
      must NOT dominate a formally-backed one whose battery partly passed.
      A road that flips the sign of the weight has not removed the weight.

  L4  THE AXIS KEEPS ITS MEANING (not R-g; the operator's own question at
      PARKED.md:73-77 -- "Should 'nothing to check' and 'checked and failed'
      share a coordinate?"). "Checked and failed" must still be dominated by
      "checked and passed", or the repair has destroyed the axis instead of
      fixing it.

Run:  python experiments/2026-08-30-defect-formalism-rank-penalty/road_law_probe.py
Exit 0 always -- the table is the output. The SHIPPED column is computed from
the real `capture.pareto.frontier` and the real `run_report` scoring rule, so
it re-reads whichever road the tree currently implements.
"""

import sys

AXES = ["hv", "reach", "coverage"]

# The four score shapes every probe is built from. `coverage: None` means the
# artifact carries no EVALUABLE commitment -- there was nothing to check --
# which is the state `run_report` currently writes as 0.0.
FORMAL_PASS = {"hv": 0.0, "reach": 0.0, "coverage": 1.0}
FORMAL_PARTIAL = {"hv": 0.0, "reach": 0.0, "coverage": 0.5}
FORMAL_FAIL = {"hv": 0.0, "reach": 0.0, "coverage": 0.0}
PROSE = {"hv": 0.0, "reach": 0.0, "coverage": None}


# --- the three roads, each defined here rather than imported, so the table is
# --- readable on a tree implementing any of them -------------------------


def _maximise(scored, axes, *, shared_only):
    def dominates(a, b):
        keys = [x for x in axes if x in a and x in b] if shared_only else axes
        if shared_only and not keys:
            return False
        if shared_only:
            return all(a[x] >= b[x] for x in keys) and any(a[x] > b[x] for x in keys)
        return all(a.get(x, 0.0) >= b.get(x, 0.0) for x in keys) and any(
            a.get(x, 0.0) > b.get(x, 0.0) for x in keys
        )

    return sorted(
        item
        for item, scores in scored
        if not any(dominates(other, scores) for _, other in scored)
    )


def road_today(scored):
    """The tree as PARKED.md found it: an empty battery scores 0.0."""
    return _maximise(
        [(i, {**s, "coverage": 0.0 if s["coverage"] is None else s["coverage"]})
         for i, s in scored],
        AXES,
        shared_only=False,
    )


def road_a(scored):
    """(a) NOT-MEASURED, not zero. An empty battery omits the coverage key;
    an axis absent from EITHER point leaves that pairwise comparison."""
    return _maximise(
        [(i, {k: v for k, v in s.items() if v is not None}) for i, s in scored],
        AXES,
        shared_only=True,
    )


def road_b_one(scored):
    """(b) Neutral default, the 1.0 variant ("nothing forbids it")."""
    return _maximise(
        [(i, {**s, "coverage": 1.0 if s["coverage"] is None else s["coverage"]})
         for i, s in scored],
        AXES,
        shared_only=False,
    )


def road_b_mean(scored):
    """(b) Neutral default, the population-mean variant."""
    measured = [s["coverage"] for _, s in scored if s["coverage"] is not None]
    fill = sum(measured) / len(measured) if measured else 1.0
    return _maximise(
        [(i, {**s, "coverage": fill if s["coverage"] is None else s["coverage"]})
         for i, s in scored],
        AXES,
        shared_only=False,
    )


def road_c(scored):
    """(c) Leave it and disclose. PARKED.md:88-90 -- "No behaviour change."
    The disclosure is a new typed field; the frontier is byte-identical to
    today's, which is what this function models."""
    return road_today(scored)


def road_shipped(scored):
    """Whatever the tree implements RIGHT NOW, through the shipped code.

    Not a copy of the rule: this builds a real root with the ordinary public
    constructors, one artifact per requested shape, and reads the frontier the
    shipped `scheduler.run_report` computes. `coverage` is steered by how many
    of the artifact's evaluable commitments pass, never hand-set.
    """
    import tempfile

    from deepreason.config import Config
    from deepreason.harness import Harness
    from deepreason.ontology import (
        Commitment, Interface, Problem, Provenance, SpawnTrigger,
    )
    from deepreason.ontology.problem import ProblemProvenance
    from deepreason.scheduler.scheduler import run_report

    # coverage is passes/evaluable, so the shape is chosen by the battery:
    #   1.0 -> one passing predicate; 0.5 -> one passing + one failing;
    #   0.0 -> one failing predicate; not-measured -> one observation.
    BATTERY = {
        1.0: ["ok"],
        0.5: ["ok", "no"],
        0.0: ["no"],
        None: ["obs"],
    }

    harness = Harness(tempfile.mkdtemp(prefix="road-law-probe-"))
    harness.register_commitment(Commitment(id="ok", eval="predicate:len(content) > 0"))
    harness.register_commitment(Commitment(id="no", eval="predicate:len(content) > 10**9"))
    harness.register_commitment(
        Commitment(id="obs", eval="observation", observation_valued=True)
    )
    problem = harness.register_problem(
        Problem(
            id="p1",
            description="a problem",
            criteria=["ok", "no", "obs"],
            provenance=ProblemProvenance(trigger=SpawnTrigger.SEED),
        )
    )

    ids = {}
    for label, s in scored:
        artifact = harness.create_artifact(
            f"content for {label}",
            interface=Interface(commitments=BATTERY[s["coverage"]]),
            provenance=Provenance(role="conjecturer"),
            problem_id=problem.id,
        )
        ids[artifact.id] = label
    # Unattacked, so the harness's own grounded-extension pass labels every
    # one ACCEPTED. No status is hand-set here.
    report = run_report(harness, Config())
    return sorted(ids[aid] for aid in report["frontier"] if aid in ids)


# --- the four probes ------------------------------------------------------


def probe_L1(road):
    kept = road([("formal", FORMAL_PASS), ("prose", PROSE)])
    return kept == ["formal", "prose"], f"frontier={kept}"


def probe_L2(road):
    # Three survivors, so a road whose fill value depends on the OTHER
    # artifacts in the run cannot hide behind a one-element population.
    with_channel = road(
        [("pass", FORMAL_PASS), ("partial", FORMAL_PARTIAL), ("prose", PROSE)]
    )
    # The same build with no formal channel at all: nothing carries an
    # evaluable commitment, so nothing has a coverage measurement.
    without_channel = road([("x1", PROSE), ("x2", PROSE), ("prose", PROSE)])
    a = "prose" in with_channel
    b = "prose" in without_channel
    return a == b, (
        f"prose_on_frontier: with_formal_channel={a} without={b}"
        f"  (with={with_channel})"
    )


def probe_L3(road):
    # Pairwise, so the question is dominance and not frontier bookkeeping:
    # does "nothing to check" out-rank "checked, and half of it passed"?
    kept = road([("formal_partial", FORMAL_PARTIAL), ("prose", PROSE)])
    dominated = "formal_partial" not in kept
    return not dominated, f"frontier={kept}"


def probe_L4(road):
    kept = road([("passed", FORMAL_PASS), ("failed", FORMAL_FAIL)])
    return kept == ["passed"], f"frontier={kept}"


PROBES = [
    ("L1 equal standing", probe_L1),
    ("L2 kind-blindness", probe_L2),
    ("L3 no reverse weight", probe_L3),
    ("L4 axis keeps meaning", probe_L4),
]

ROADS = [
    ("today (no change)", road_today),
    ("(a) not-measured", road_a),
    ("(b) neutral 1.0", road_b_one),
    ("(b) neutral mean", road_b_mean),
    ("(c) disclose only", road_c),
]


def main():
    width = max(len(n) for n, _ in ROADS) + 2
    header = "road".ljust(width) + "".join(n.split()[0].ljust(6) for n, _ in PROBES)
    print(header)
    print("-" * len(header))
    results = {}
    for road_name, road in ROADS:
        row = road_name.ljust(width)
        for probe_name, probe in PROBES:
            ok, _ = probe(road)
            results[(road_name, probe_name)] = ok
            row += ("PASS" if ok else "FAIL").ljust(6)
        print(row)

    print()
    print("Detail (the frontier each probe actually computed):")
    for road_name, road in ROADS:
        print(f"  {road_name}")
        for probe_name, probe in PROBES:
            ok, detail = probe(road)
            print(f"    {probe_name:<24} {'PASS' if ok else 'FAIL'}  {detail}")

    print()
    try:
        shipped_row = []
        for probe_name, probe in PROBES:
            ok, detail = probe(road_shipped)
            shipped_row.append((probe_name, ok, detail))
    except Exception as error:                          # pragma: no cover
        print(f"SHIPPED column unavailable ({type(error).__name__}: {error})")
        return 0
    print("SHIPPED (the tree this script was run against):")
    for probe_name, ok, detail in shipped_row:
        print(f"    {probe_name:<24} {'PASS' if ok else 'FAIL'}  {detail}")
    shipped_verdict = [ok for _, ok, _ in shipped_row]
    for road_name, road in ROADS:
        if [results[(road_name, p)] for p, _ in PROBES] == shipped_verdict:
            print(f"    -> the shipped tree matches road: {road_name}")
            break
    else:
        print("    -> the shipped tree matches NO road modelled here")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
