#!/usr/bin/env python
"""Schema validator for the two-tier hard question set (SPEC.md R3/R11).

Usage:
    python schema_check.py <file.json> --kind math|coding|both|open
    python schema_check.py --selftest
"""

import argparse
import json
import sys

COMMON_V = {"id", "tier", "q", "kind", "source", "license", "verification"}
MATH_ONLY = {"accept"}
CODING_ONLY = {"checker"}

OPEN_FIELDS = {
    "id", "tier", "q", "attribution", "source_url",
    "still_open_verified", "computable_special_case", "verification",
}


def _err(msg):
    return f"error: {msg}"


def validate_record_v(rec, index, errors):
    missing = COMMON_V - rec.keys()
    if missing:
        errors.append(_err(f"record {index} ({rec.get('id', '?')}): missing {sorted(missing)}"))
        return
    if rec.get("tier") != "V":
        errors.append(_err(f"record {index} ({rec['id']}): tier must be 'V'"))
    kind = rec.get("kind")
    if kind == "math":
        if MATH_ONLY - rec.keys():
            errors.append(_err(f"record {index} ({rec['id']}): kind=math missing 'accept'"))
        if not isinstance(rec.get("accept"), list) or not rec["accept"]:
            errors.append(_err(f"record {index} ({rec['id']}): 'accept' must be a non-empty list"))
    elif kind == "coding":
        if CODING_ONLY - rec.keys():
            errors.append(_err(f"record {index} ({rec['id']}): kind=coding missing 'checker'"))
    else:
        errors.append(_err(f"record {index} ({rec.get('id', '?')}): kind must be 'math' or 'coding', got {kind!r}"))
    src = rec.get("source")
    if not isinstance(src, dict) or not {"dataset", "problem_id", "url"} <= src.keys():
        errors.append(_err(f"record {index} ({rec.get('id', '?')}): 'source' must have dataset/problem_id/url"))
    if "checker" in rec and not isinstance(rec["checker"], str):
        errors.append(_err(f"record {index} ({rec.get('id', '?')}): 'checker' must be a string path"))


def validate_record_open(rec, index, errors):
    missing = OPEN_FIELDS - rec.keys()
    if missing:
        errors.append(_err(f"record {index} ({rec.get('id', '?')}): missing {sorted(missing)}"))
        return
    if rec.get("tier") != "O":
        errors.append(_err(f"record {index} ({rec['id']}): tier must be 'O'"))
    if rec.get("verification") != "open — hygiene scored":
        errors.append(_err(f"record {index} ({rec['id']}): verification must be 'open — hygiene scored'"))
    if not rec.get("still_open_verified"):
        errors.append(_err(f"record {index} ({rec['id']}): still_open_verified must be a non-empty date string"))
    if not rec.get("source_url"):
        errors.append(_err(f"record {index} ({rec['id']}): source_url must be non-empty"))


def validate(data, kind, errors):
    if not isinstance(data, list):
        errors.append(_err("top level must be a JSON array"))
        return
    ids = []
    for i, rec in enumerate(data):
        if not isinstance(rec, dict):
            errors.append(_err(f"record {i}: not an object"))
            continue
        ids.append(rec.get("id"))
        if kind == "open":
            validate_record_open(rec, i, errors)
        elif kind in ("math", "coding"):
            validate_record_v(rec, i, errors)
            if rec.get("kind") != kind:
                errors.append(_err(f"record {i} ({rec.get('id', '?')}): expected kind={kind}, got {rec.get('kind')!r}"))
        elif kind == "both":
            validate_record_v(rec, i, errors)
        else:
            raise ValueError(f"unknown --kind {kind!r}")
    dupes = {x for x in ids if ids.count(x) > 1}
    if dupes:
        errors.append(_err(f"duplicate ids: {sorted(dupes)}"))


VALID_FIXTURE = [
    {
        "id": "tv-m01", "tier": "V", "q": "What is 2+2?", "kind": "math",
        "accept": ["4"],
        "source": {"dataset": "MATH", "problem_id": "algebra/0001.json", "url": "https://example.invalid/0001"},
        "license": "MIT",
        "verification": "checker script (run against known answer before commit)",
    },
    {
        "id": "tv-c01", "tier": "V", "q": "Write a function that adds one.", "kind": "coding",
        "checker": "experiments/tier_v_checkers/tv-c01_checker.py",
        "source": {"dataset": "HumanEval", "problem_id": "HumanEval/0", "url": "https://example.invalid/HumanEval-0"},
        "license": "MIT",
        "verification": "checker script (run against reference solution before commit)",
    },
]

BROKEN_FIXTURE = [
    {
        "id": "tv-m01", "tier": "V", "q": "What is 2+2?", "kind": "math",
        # missing 'accept' and 'source' on purpose
        "license": "MIT",
        "verification": "checker script",
    },
]


def selftest():
    good_errors = []
    validate(VALID_FIXTURE, "both", good_errors)
    if good_errors:
        print("SELFTEST FAIL: valid fixture rejected:", good_errors)
        return 1
    bad_errors = []
    validate(BROKEN_FIXTURE, "both", bad_errors)
    if not bad_errors:
        print("SELFTEST FAIL: broken fixture was accepted")
        return 1
    print("SELFTEST PASS: valid fixture accepted (0 errors), "
          f"broken fixture rejected ({len(bad_errors)} errors: {bad_errors})")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="?")
    parser.add_argument("--kind", choices=["math", "coding", "both", "open"])
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.selftest:
        return selftest()

    if not args.file or not args.kind:
        parser.error("file and --kind are required unless --selftest")

    data = json.loads(open(args.file).read())
    errors = []
    validate(data, args.kind, errors)
    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        print(f"FAIL: {len(errors)} error(s) in {args.file}", file=sys.stderr)
        return 1
    print(f"PASS: {args.file} ({len(data)} records, kind={args.kind})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
