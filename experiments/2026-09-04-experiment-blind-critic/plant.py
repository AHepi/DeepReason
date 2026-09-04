#!/usr/bin/env python3
"""Plant one defect in each of the 60 planted targets, by the judge study's method.

The method is `scripts/court_calibration_corpus.py`'s and nothing here departs
from it: deterministic and rerunnable, no randomness, no LLM call, every
mutation a mechanical string or structure edit applied to a PARSED COPY of the
clean body, exactly one defect per artifact, the classes balanced, and an
assertion after every mutation that exactly one field differs and nothing else
moved. Ground truth is by construction, which is the whole point -- a detector
scored against it cannot be argued with afterwards.

Three of the six classes are the source's, applied verbatim. Three are adapted,
and SPEC A2 records the measurement that forced each adaptation: across all 238
eligible artifacts of this shape, `scope.covers`, `scope.excludes`,
`derivation`, `premises`, `uncertainties` and `definitions` are EMPTY and there
is no `prose_notes` field at all, so the source's `chronology-error` (needs a
year), its `scope-contradiction` (needs `scope.covers`) and its
`evidence-misquotation` (needs `prose_notes`) cannot be applied as written.

The planted sentences are deliberately defective ON THEIR OWN TERMS rather than
against this domain's facts. A critic that has to know graph theory to see the
fault would be measuring domain knowledge; a critic that has to read is
measuring what the operator asked about.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent

DEFECT_CLASSES = [
    "unsupported-comparison",
    "causal-non-sequitur",
    "evidence-misquotation",
    "circular-mechanism",
    "scope-contradiction",
    "vacuous-forbidden-case",
]

UNSUPPORTED_COMPARISON = (
    " Unlike every previously studied system of this kind, which faced"
    " identical structural constraints yet exhibited none of this behaviour."
)
NON_SEQUITUR = (
    " It follows that the underlying structure was never relevant to the"
    " outcome at all."
)
EVIDENCE_MISQUOTE = (
    " This is precisely the result Erdos and Renyi established in their 1959"
    " paper, which states this conclusion in exactly these terms."
)
# The source's own string, byte for byte (court_calibration_corpus.py).
VACUOUS_CASE = "Evidence emerges that contradicts the central claim of this account."


def _lead(text: str) -> str:
    """The claim's first sentence, trimmed. Mechanical: the first '. ' or the
    first 200 characters, whichever comes first."""
    head = text.split(". ")[0].strip()
    return (head[:200]).rstrip(" .")


def mutate_comparison(inner):
    inner["mechanism"] = inner["mechanism"] + UNSUPPORTED_COMPARISON
    return ("mechanism",
            "Appended an unsupported comparison to an unnamed reference class"
            " of 'every previously studied system of this kind' to mechanism.")


def mutate_non_sequitur(inner):
    inner["mechanism"] = inner["mechanism"] + NON_SEQUITUR
    return ("mechanism",
            "Appended a non-sequitur conclusion -- that the underlying"
            " structure was never relevant -- to mechanism.")


def mutate_evidence(inner):
    inner["mechanism"] = inner["mechanism"] + EVIDENCE_MISQUOTE
    return ("mechanism",
            "Appended a fabricated attribution of the result to Erdos and"
            " Renyi 1959 to mechanism.")


def mutate_circular(inner):
    lead = _lead(inner["claim"])
    inner["mechanism"] = inner["mechanism"] + (
        f" The reason this holds is that {lead}, which is what the mechanism"
        " above establishes."
    )
    return ("mechanism",
            "Appended a circular step to mechanism: the claim is given as the"
            " reason for the claim.")


def mutate_scope(inner):
    lead = _lead(inner["claim"])
    scope = dict(inner["scope"])
    scope["excludes"] = list(scope.get("excludes") or []) + [lead]
    inner["scope"] = scope
    return ("scope",
            "Appended the claim's own leading sentence to scope.excludes, so"
            " the artifact excludes from its scope the very case it asserts.")


def mutate_forbidden(inner):
    conditions = copy.deepcopy(inner["counterconditions"])
    conditions[0] = dict(conditions[0])
    conditions[0]["case"] = VACUOUS_CASE
    inner["counterconditions"] = conditions
    return ("counterconditions",
            "Replaced the first countercondition's case with a vacuous"
            " circular case that forbids nothing.")


MUTATORS = {
    "unsupported-comparison": mutate_comparison,
    "causal-non-sequitur": mutate_non_sequitur,
    "evidence-misquotation": mutate_evidence,
    "circular-mechanism": mutate_circular,
    "scope-contradiction": mutate_scope,
    "vacuous-forbidden-case": mutate_forbidden,
}


def assert_single_difference(clean, bad, defect_class, changed_field):
    """Exactly the expected field-level difference, and no other.

    The source's own guard, kept because ground truth by construction is only
    ground truth if the construction is checked: a mutator that also
    reformatted a neighbouring field would put a second, unlabelled defect in
    front of the critic and every M1 number would be measuring the wrong thing.
    """
    assert set(clean) == set(bad), (set(bad) ^ set(clean))
    differing = [k for k in bad if bad[k] != clean.get(k)]
    assert differing == [changed_field], (defect_class, differing)

    clean_value, bad_value = clean.get(changed_field), bad[changed_field]
    if changed_field == "scope":
        sub = [k for k in bad_value if bad_value[k] != clean_value.get(k)]
        assert sub == ["excludes"], sub
        assert bad_value["excludes"] == list(clean_value.get("excludes") or []) + [
            bad_value["excludes"][-1]
        ]
    elif changed_field == "counterconditions":
        assert len(bad_value) == len(clean_value)
        assert bad_value[1:] == clean_value[1:]
        entry = [k for k in bad_value[0] if bad_value[0][k] != clean_value[0].get(k)]
        assert entry == ["case"], entry
        assert bad_value[0]["case"] == VACUOUS_CASE
    else:
        assert bad_value.startswith(clean_value), "append mutation altered existing text"
        assert len(bad_value) > len(clean_value), "append mutation added nothing"


def build(selection):
    planted = [row for row in selection["targets"] if row["arm"] == "planted"]
    assert len(planted) == 60, len(planted)

    pairs = []
    counts = {name: 0 for name in DEFECT_CLASSES}
    for index, row in enumerate(planted):
        defect_class = DEFECT_CLASSES[index % len(DEFECT_CLASSES)]
        counts[defect_class] += 1

        clean = row["body"]
        bad = copy.deepcopy(clean)
        changed_field, note = MUTATORS[defect_class](bad)
        assert_single_difference(clean, bad, defect_class, changed_field)

        clean_text = json.dumps(clean, ensure_ascii=False, sort_keys=True)
        bad_text = json.dumps(bad, ensure_ascii=False, sort_keys=True)
        assert bad_text != clean_text

        pairs.append({
            "target_id": row["target_id"],
            "artifact_id": row["artifact_id"],
            "source_root": row["source_root"],
            "defect_class": defect_class,
            "changed_field": changed_field,
            "defect_note": note,
            "clean_sha256": hashlib.sha256(clean_text.encode()).hexdigest(),
            "planted_sha256": hashlib.sha256(bad_text.encode()).hexdigest(),
            "clean": clean,
            "planted": bad,
        })
    return pairs, counts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    selection = json.loads((HERE / "SELECTION.json").read_text(encoding="utf-8"))
    pairs, counts = build(selection)

    payload = {
        "schema": "blind-critic-defect-key.v1",
        "method": "scripts/court_calibration_corpus.py (three classes verbatim,"
                  " three adapted -- SPEC A2)",
        "classes": DEFECT_CLASSES,
        "class_counts": counts,
        "pairs": pairs,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    if args.write:
        (HERE / "DEFECT_KEY.json").write_text(text, encoding="utf-8")
    print(f"{len(pairs)} pairs, {min(counts.values())} per class")
    for name in DEFECT_CLASSES:
        print(f"  {name}: {counts[name]}")
    print("DEFECT_KEY.sha256:", hashlib.sha256(text.encode()).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main())
