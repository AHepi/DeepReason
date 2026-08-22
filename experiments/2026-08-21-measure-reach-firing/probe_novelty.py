"""Join probe (READ-ONLY): the novelty x pass cross-tabulation for
`relation-form`, the one criterion that carries 584,303 of the corpus's
585,096 gate pairs.

`relation_form_commitment()` builds its id from the digest of a CONSTANT
expression, so every connection and integration problem in every run shares
ONE commitment id. reach_sweep requires a qualifying foreign criterion to be
NOVEL to the artifact's own battery AND to be passed. This probe measures
whether those two requirements can be met by the same artifact:

  carries x passes, over every candidate (ACCEPTED + addressing) artifact.
"""

import collections
import json
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[2]
# The complete qualifying vocabulary the census found in the corpus
# (census.json `_qualifying_vocab`): every substantive-and-evaluable
# criterion that any foreign problem carries.
QUALIFYING = ("relation-form@578e42df713e", "reasoning-envelope-wf")


def probe(root: pathlib.Path) -> dict:
    from deepreason import programs
    from deepreason.harness import Harness
    from deepreason.ontology.state import Status

    harness = Harness(root, read_only=True)
    state = harness.state
    addressed = {aid for aid, _pid in state.addr}
    counts = collections.Counter()
    for cid in QUALIFYING:
        commitment = harness.commitments.get(cid)
        for aid, status in state.status.items():
            if status != Status.ACCEPTED or aid not in addressed:
                continue
            if commitment is None:
                counts[f"{cid}: not-registered-in-this-root"] += 1
                continue
            artifact = state.artifacts[aid]
            carries = cid in set(artifact.interface.commitments)
            verdict, _trace = programs.evaluate(commitment, artifact, harness.blobs)
            counts[f"{cid}: carries={carries} passes={verdict == programs.PASS}"] += 1
    return {"root": str(root.relative_to(REPO)), **dict(counts)}


if __name__ == "__main__":
    roots = sorted({p.parent for p in (REPO / "experiments").rglob("log.jsonl")})
    rows, totals = [], collections.Counter()
    for root in roots:
        try:
            row = probe(root)
        except Exception as error:
            row = {"root": str(root.relative_to(REPO)),
                   "open_error": f"{type(error).__name__}: {error}"}
        rows.append(row)
        for key, value in row.items():
            if isinstance(value, int):
                totals[key] += value
    path = pathlib.Path(__file__).with_name("probe_novelty.json")
    path.write_text(json.dumps(
        {"roots": rows, "totals": dict(sorted(totals.items()))}, indent=2) + "\n")
    print("=== TOTALS (candidate artifacts, whole corpus) ===")
    for key, value in sorted(totals.items()):
        print(f"  {key:52} {value}")
    print(f"\nwrote {path}")
