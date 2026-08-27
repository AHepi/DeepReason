"""Part 2 — classify every committed artifact by KIND and compare outcomes.

    python experiments/2026-08-27-audit-formalism-optional/kind_census.py

Writes KIND_CENSUS.json.  Roots are opened READ-ONLY: a writable open repairs,
i.e. destroys, the evidence.

## The operationalization (stated, because the whole comparison rests on it)

`Artifact` carries no kind field -- `DR-CON-conjecture-kinds` is explicit that
formal-vs-informal is a fact about `Interface.commitments`, discovered by
reading the list.  So the census reads exactly what the CODE reads, three ways:

  K1  BATTERY-CARRYING   >=1 registered commitment whose eval is `evaluable`
                         (`programs.evaluable`).  This is the distinction
                         `coverage`, `_evaluable_battery` and `crit_program`
                         read.
  K2  SUBSTANTIVE-BACKED >=1 registered SUBSTANTIVE commitment
                         (`measures/reach._substantive`: evaluable and not a
                         structural well-formedness program).  This is the
                         distinction `formally_backed` reads -- the one that
                         actually buys prose-immunity.
  K3  EXECUTION-BACKED   >=1 commitment in `oracle.EXEC_PROGRAMS`.  The
                         narrow guard `crit.py` and `_standing_recrit_pool`
                         read.

K3 is a subset of K2 is a subset of K1.  A "PROSE" artifact in the tables is
one that is NOT battery-carrying (K1 false): nothing on its declared surface
can be machine-decided.

CONTENT FORM is reported separately and NEVER substituted for the above: an
artifact whose bytes parse as a reasoning envelope or a skeleton is
`structured`, otherwise `free-prose`.  Content form is what a human would call
"formal-looking"; it is NOT what any of the guards read, and the two disagree
often -- which is itself worth seeing.

## The outcomes, per artifact

status, survivor, attacks received (incoming `att` edges), warrants against it
split DEMONSTRATIVE/ARGUMENTATIVE, reach>0, on the Pareto frontier, in the
knowledge view.  Every one is read from replayed state, never from prose.
"""

import json
import os
import sys
import traceback
from collections import Counter, defaultdict

ROOTS_NAMED = [
    ("P-R1", "experiments/2026-08-25-poietics-program/run"),
    ("P-C1 ARM H", "experiments/2026-08-25-change-constructive-frontier/run"),
    ("P-C2b", "experiments/2026-08-27-pc2b-symmetric-reasoning/run"),
    ("attempt-4", "experiments/2026-08-22-change-epoch3-second-lineage/run"),
]
INVENTORY = "experiments/2026-08-26-run-anatomy-program/ROOT_INVENTORY.json"
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))


def _structured(text):
    """Does the artifact's own content parse as an envelope or a skeleton?"""
    from deepreason.informal.skeleton import parse_skeleton
    from deepreason.workloads.text import ReasoningEnvelopeV1

    if parse_skeleton(text) is not None:
        return "skeleton"
    try:
        ReasoningEnvelopeV1.model_validate_json(text)
        return "envelope"
    except Exception:
        pass
    stripped = text.strip()
    if stripped[:1] in "{[":
        try:
            json.loads(stripped)
            return "json-other"
        except ValueError:
            pass
    return "free-prose"


def census_root(rel):
    from deepreason import programs
    from deepreason.harness import Harness
    from deepreason.measures.reach import _substantive
    from deepreason.oracle import EXEC_PROGRAMS
    from deepreason.ontology import Status, WarrantType
    from deepreason.ontology.state import counts_as_survivor

    harness = Harness(os.path.join(REPO, rel), read_only=True)
    state = harness.state
    execution_evals = {f"program:{p}" for p in EXEC_PROGRAMS}

    incoming = Counter(target for _source, target in state.att)
    warrants = defaultdict(Counter)
    for warrant in harness.warrants.values():
        warrants[warrant.target][warrant.type.value] += 1

    frontier_ids, frontier_error = set(), None
    try:
        from deepreason.config import Config
        from deepreason.scheduler.scheduler import run_report

        frontier_ids = set(run_report(harness, Config())["frontier"])
    except Exception as error:
        frontier_error = f"{type(error).__name__}: {error}"

    knowledge_ids, knowledge_error = set(), None
    try:
        from deepreason.views.knowledge import knowledge_view

        knowledge_ids = {row["artifact"] for row in knowledge_view(harness)["rows"]}
    except Exception as error:
        knowledge_error = f"{type(error).__name__}: {error}"

    rows = []
    for aid, artifact in state.artifacts.items():
        carried = [
            harness.commitments[cid]
            for cid in artifact.interface.commitments
            if cid in harness.commitments
        ]
        k1 = any(programs.evaluable(k) for k in carried)
        k2 = any(_substantive(k) for k in carried)
        k3 = any(k.eval in execution_evals for k in carried)
        try:
            text = programs.content_text(artifact, harness.blobs)
        except Exception:
            text = ""
        status = state.status.get(aid)
        rows.append({
            "artifact": aid,
            "role": (artifact.provenance.role.value
                     if artifact.provenance and hasattr(artifact.provenance.role, "value")
                     else str(getattr(getattr(artifact, "provenance", None), "role", ""))),
            "n_commitments": len(artifact.interface.commitments),
            "n_registered": len(carried),
            "battery_carrying": k1,
            "substantive_backed": k2,
            "execution_backed": k3,
            "content_form": _structured(text),
            "status": status.value if status else None,
            "survivor": counts_as_survivor(state, aid),
            "attacks_received": incoming.get(aid, 0),
            "warrants_demonstrative": warrants[aid].get(WarrantType.DEMONSTRATIVE.value, 0),
            "warrants_argumentative": warrants[aid].get(WarrantType.ARGUMENTATIVE.value, 0),
            "reach": state.reach.get(aid, 0.0),
            "on_frontier": aid in frontier_ids,
            "in_knowledge_view": aid in knowledge_ids,
        })
    return {
        "root": rel,
        "n_artifacts": len(rows),
        "frontier_error": frontier_error,
        "knowledge_error": knowledge_error,
        "artifacts": rows,
    }


def main():
    inventory = json.load(open(os.path.join(REPO, INVENTORY)))
    named = dict((path, label) for label, path in ROOTS_NAMED)
    paths = [path for _label, path in ROOTS_NAMED]
    for entry in inventory["roots"]:
        if entry["root"] not in named:
            paths.append(entry["root"])

    out, failed = [], []
    for rel in paths:
        try:
            doc = census_root(rel)
        except Exception as error:
            failed.append({"root": rel, "error": f"{type(error).__name__}: {error}",
                           "traceback": traceback.format_exc()[-400:]})
            print(f"FAILED {rel}: {type(error).__name__}: {error}", file=sys.stderr)
            continue
        doc["label"] = named.get(rel)
        out.append(doc)
        print(f"ok {doc['n_artifacts']:6d} artifacts  {rel}", file=sys.stderr)

    json.dump({
        "schema": "formalism-audit.kind-census.v1",
        "named_roots": ROOTS_NAMED,
        "roots_attempted": len(paths),
        "roots_read": len(out),
        "roots_failed": failed,
        "roots": out,
    }, open(os.path.join(HERE, "KIND_CENSUS.json"), "w"), indent=1)
    print(f"\nread {len(out)} of {len(paths)} roots; "
          f"{sum(d['n_artifacts'] for d in out)} artifacts", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
