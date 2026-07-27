#!/usr/bin/env python3
"""Build a matched-pair court-calibration corpus from court_cross_pool_v1.json.

Deterministic and rerunnable. No randomness, no LLM calls. All mutations
are mechanical string or structure edits applied to a parsed copy of the
clean item content.
"""

import copy
import hashlib
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_PATH = REPO_ROOT / "experiments" / "court_cross_pool_v1.json"
OUTPUT_DIR = REPO_ROOT / "experiments" / "court_calibration_items"
OUTPUT_PATH = OUTPUT_DIR / "pairs_v1.json"

POOL_PREFIX = 85
PAIR_COUNT = 42

DEFECT_CLASSES = [
    "chronology-error",
    "unsupported-comparison",
    "scope-contradiction",
    "vacuous-forbidden-case",
    "evidence-misquotation",
    "causal-non-sequitur",
]

# Year regex: a 3-4 digit number that heads an optional range and is
# anchored to an era marker (BC / BCE / BP), so durations like
# "300-year" are not mistaken for calendar years.
YEAR_RE = re.compile(r"\b(\d{3,4})(?=(?:\s*[-–]\s*\d{3,4})?\s*(?:BC|BCE|BP)\b)")

YEAR_FIELDS = ("claim", "mechanism", "prose_notes")

CHRONOLOGY_FALLBACK = " This process began in earnest around 800 BC."
UNSUPPORTED_COMPARISON = (
    " Unlike Kassite Babylonia, which faced identical maritime and climatic"
    " shocks yet retained every palace institution unchanged."
)
VACUOUS_CASE = "Evidence emerges that contradicts the central claim of this account."
EVIDENCE_MISQUOTE = (
    " The Amarna letters, written during the collapse itself, describe these"
    " final raids in detail."
)
NON_SEQUITUR = (
    " It follows that maritime trade had never been economically significant"
    " in the eastern Mediterranean."
)


def select_items(pool):
    """Return the first PAIR_COUNT eligible items, in order."""
    selected = []
    for item in pool[:POOL_PREFIX]:
        try:
            inner = json.loads(item["content"])
        except (KeyError, TypeError, ValueError):
            continue
        if not isinstance(inner, dict):
            continue
        if not inner.get("claim") or not inner.get("mechanism"):
            continue
        if not isinstance(inner.get("scope"), dict):
            continue
        selected.append(item)
        if len(selected) == PAIR_COUNT:
            break
    return selected


def mutate_chronology(inner):
    for field in YEAR_FIELDS:
        text = inner.get(field)
        if not isinstance(text, str):
            continue
        match = YEAR_RE.search(text)
        if match:
            shifted = str(int(match.group(1)) - 400)
            inner[field] = text[: match.start(1)] + shifted + text[match.end(1):]
            return (
                field,
                "Shifted the year %s to %s (400 years later) in %s."
                % (match.group(1), shifted, field),
            )
    inner["mechanism"] = inner["mechanism"] + CHRONOLOGY_FALLBACK
    return (
        "mechanism",
        "No year found; appended an anachronistic 800 BC onset sentence to mechanism.",
    )


def mutate_comparison(inner):
    inner["mechanism"] = inner["mechanism"] + UNSUPPORTED_COMPARISON
    return (
        "mechanism",
        "Appended an unsupported Kassite Babylonia comparison sentence to mechanism.",
    )


def mutate_scope(inner):
    first_cover = inner["scope"]["covers"][0]
    inner["scope"]["excludes"] = list(inner["scope"]["excludes"]) + [first_cover]
    return (
        "scope",
        "Appended the first scope.covers entry to scope.excludes, listing the"
        " same case in both.",
    )


def mutate_forbidden(inner):
    forbidden = inner.get("forbidden")
    if isinstance(forbidden, list) and forbidden:
        forbidden[0]["case"] = VACUOUS_CASE
        note = "Replaced the first forbidden case text with a vacuous circular case."
    else:
        inner["forbidden"] = [{"case": VACUOUS_CASE, "eval": "rubric:std-hist"}]
        note = "Added a vacuous circular forbidden case (skeleton had none)."
    return ("forbidden", note)


def mutate_evidence(inner):
    inner["prose_notes"] = inner.get("prose_notes", "") + EVIDENCE_MISQUOTE
    return (
        "prose_notes",
        "Appended a misdated Amarna letters citation sentence to prose_notes.",
    )


def mutate_non_sequitur(inner):
    inner["mechanism"] = inner["mechanism"] + NON_SEQUITUR
    return (
        "mechanism",
        "Appended a non-sequitur conclusion about maritime trade to mechanism.",
    )


MUTATORS = {
    "chronology-error": mutate_chronology,
    "unsupported-comparison": mutate_comparison,
    "scope-contradiction": mutate_scope,
    "vacuous-forbidden-case": mutate_forbidden,
    "evidence-misquotation": mutate_evidence,
    "causal-non-sequitur": mutate_non_sequitur,
}


def assert_single_difference(clean_inner, bad_inner, defect_class, changed_field):
    """Assert exactly the expected field-level difference and no other."""
    assert set(clean_inner) <= set(bad_inner), "corrupted twin dropped a key"
    extra = set(bad_inner) - set(clean_inner)
    if defect_class == "vacuous-forbidden-case" and "forbidden" not in clean_inner:
        assert extra == {"forbidden"}, extra
    else:
        assert not extra, extra
    diff_keys = [
        key
        for key in bad_inner
        if bad_inner.get(key) != clean_inner.get(key)
    ]
    assert diff_keys == [changed_field], (defect_class, diff_keys)

    clean_val = clean_inner.get(changed_field)
    bad_val = bad_inner[changed_field]
    if changed_field == "scope":
        sub_diff = [k for k in bad_val if bad_val[k] != clean_val.get(k)]
        assert sub_diff == ["excludes"], sub_diff
        assert bad_val["excludes"] == clean_val["excludes"] + [clean_val["covers"][0]]
    elif changed_field == "forbidden":
        if clean_val:
            assert len(bad_val) == len(clean_val)
            assert bad_val[1:] == clean_val[1:]
            entry_diff = [
                k for k in bad_val[0] if bad_val[0][k] != clean_val[0].get(k)
            ]
            assert entry_diff == ["case"], entry_diff
        assert bad_val[0]["case"] == VACUOUS_CASE
    elif defect_class == "chronology-error" and clean_val is not None and not bad_val.endswith(CHRONOLOGY_FALLBACK):
        assert len(bad_val) <= len(clean_val), "year substitution grew the field"
    else:
        prefix = clean_val if clean_val is not None else ""
        assert bad_val.startswith(prefix), "append mutation altered existing text"
        assert len(bad_val) > len(prefix), "append mutation added nothing"


def build_pairs():
    pool = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))["items"]
    selected = select_items(pool)
    assert len(selected) == PAIR_COUNT, len(selected)

    pairs = []
    class_counts = {name: 0 for name in DEFECT_CLASSES}
    for index, item in enumerate(selected):
        clean = item["content"]
        defect_class = DEFECT_CLASSES[index % len(DEFECT_CLASSES)]
        class_counts[defect_class] += 1

        clean_inner = json.loads(clean)
        bad_inner = copy.deepcopy(clean_inner)
        changed_field, note = MUTATORS[defect_class](bad_inner)
        corrupted = json.dumps(bad_inner, ensure_ascii=False)

        assert corrupted != clean
        reparsed = json.loads(corrupted)
        assert reparsed == bad_inner
        assert_single_difference(clean_inner, reparsed, defect_class, changed_field)

        pairs.append(
            {
                "pair_id": "cal-%02d" % (index + 1),
                "base_sha256": hashlib.sha256(clean.encode("utf-8")).hexdigest(),
                "defect_class": defect_class,
                "clean": clean,
                "corrupted": corrupted,
                "defect_note": note,
            }
        )

    assert len(pairs) == PAIR_COUNT
    assert all(count == PAIR_COUNT // len(DEFECT_CLASSES) for count in class_counts.values()), class_counts
    return pairs, class_counts


def main():
    pairs, class_counts = build_pairs()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(pairs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("wrote %d pairs to %s" % (len(pairs), OUTPUT_PATH))
    for name in DEFECT_CLASSES:
        print("  %s: %d" % (name, class_counts[name]))


if __name__ == "__main__":
    main()
