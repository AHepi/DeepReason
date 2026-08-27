"""The kind-signal sweep — Part 1's raw site list, reproducible.

    python experiments/2026-08-27-audit-formalism-optional/sweep.py > SWEEP_RAW.json

Every TERM below is a way `src/deepreason` code could learn a conjecture's or a
criticism's KIND (formal vs informal, battery-carrying vs not, envelope vs
prose, machine-evaluable claim vs argument), or could move one of the outcomes
the operator's law names.  The sweep is deliberately over-broad: it reports
every hit and marks which ones are in EXECUTABLE CODE rather than a comment or
a docstring, because the reduction from raw hits to outcome-influencing sites
is a judgment the audit has to show its work for, not hide inside a grep.

`code: false` rows are prose ABOUT the machinery (comments, docstrings). They
are kept in the output so a reader can see what the sweep saw and check that
nothing executable was dropped by the filter.
"""

import io
import json
import os
import re
import sys
import tokenize
from collections import Counter

TERMS = [
    # -- narrow: an unambiguous kind signal ---------------------------------
    "execution_backed",
    "formally_backed",
    r"programs\.evaluable",
    "candidate_checker",
    "checker_spec",
    "EXEC_PROGRAMS",
    "is_pure_code",
    "DEMONSTRATIVE",
    "ARGUMENTATIVE",
    "property_oracle",
    "exec_oracle",
    r"\.commitments",
    "active_properties",
    "observation_valued",
    # -- broad: an outcome the law names, or a word the design uses for kind -
    r"\bprose\b",
    r"\bformal\b",
    r"\binformal\b",
    "demarcat",
    "hv_floor|is_hv_floor|run_hv_floor",
    "reach_set|reach_eligib|reach_certificate|reachable",
    "discharge",
    "allocation|allocate",
    "wound",
    "attention",
    "battery",
    "envelope",
]

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")


def _non_code_lines(path):
    """Line numbers holding ONLY comment or string-literal content."""
    src = open(path, "rb").read()
    try:
        toks = list(tokenize.tokenize(io.BytesIO(src).readline))
    except (tokenize.TokenError, SyntaxError, IndentationError):
        return set()
    skip = {
        tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT,
        tokenize.DEDENT, tokenize.ENCODING, tokenize.ENDMARKER, tokenize.STRING,
    }
    code = set()
    for tok in toks:
        if tok.type in skip:
            continue
        code.update(range(tok.start[0], tok.end[0] + 1))
    total = src.decode("utf-8", "replace").count("\n") + 1
    return set(range(1, total + 1)) - code


def sweep():
    hits = []
    base = os.path.normpath(os.path.join(ROOT, "src", "deepreason"))
    for folder, _dirs, files in os.walk(base):
        for name in sorted(files):
            if not name.endswith(".py"):
                continue
            path = os.path.join(folder, name)
            rel = os.path.relpath(path, ROOT)
            non_code = _non_code_lines(path)
            for number, line in enumerate(
                open(path, encoding="utf-8").read().splitlines(), 1
            ):
                for term in TERMS:
                    if re.search(term, line):
                        hits.append({
                            "file": rel.replace(os.sep, "/"),
                            "line": number,
                            "term": term,
                            "code": number not in non_code,
                            "text": line.strip()[:200],
                        })
                        break
    return hits


def main():
    hits = sweep()
    code = [h for h in hits if h["code"]]
    per_term = Counter(h["term"] for h in hits)
    per_term_code = Counter(h["term"] for h in code)
    json.dump(
        {
            "schema": "formalism-audit.sweep.v1",
            "terms": TERMS,
            "raw_hits": len(hits),
            "code_hits": len(code),
            "per_term": {t: [per_term[t], per_term_code[t]] for t in TERMS},
            "hits": hits,
        },
        sys.stdout,
        indent=1,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
