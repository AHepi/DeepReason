"""M2 sub-measurement: how much of a rendered prompt is the JSON schema?

Offline, from committed roots. No API calls, no live run. The window
instruction asks that M2 "record separately the share of each prompt that is
the JSON schema (P-A1: ~19k of 30k chars)". That figure is re-derived here
rather than quoted, because the whole point of the pack-budget sweep is to know
what the budget is actually buying: if most of a prompt is a fixed schema, then
raising PACK_TOKEN_BUDGET raises the part that is NOT the schema, and the
sweep's x-axis means something different from what it looks like.

## How the schema block is delimited

By what the schema IS, not by the sentence that introduces it -- see
`_schema_span`, which also records why: an earlier marker-anchored version
silently measured a biased subset. Every balanced `{...}` in the prompt is
parsed (respecting string literals and escapes, so prose braces cannot
truncate it) and the largest one that is actually a JSON Schema wins. A prompt
with no such object is counted as UNDELIMITED and excluded from the mean rather
than contributing a wrong share; that count is printed beside every result.

## What this does and does not show

DOES: the fixed overhead every conjecturer call pays on these committed roots,
per contract, in characters and as a share.

DOES NOT: anything about tokens. Characters are not tokens and the ratio is
model-specific; `prompt_tokens` is recorded on the attempt and is reported
beside the character count so the two are never conflated.

Usage: measure_schema_share.py <run-root> [<run-root> ...]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import sys
from collections import defaultdict


def _balanced(text: str, start: int) -> int | None:
    """End index of the JSON value opening at `start`, or None if unbalanced."""
    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i + 1
    return None


def _schema_span(text: str) -> tuple[int, int] | None:
    """(start, end) of the largest embedded JSON SCHEMA value, or None.

    Marker-independent by construction, and that is a correction rather than a
    preference. The first version of this probe anchored on the sentence
    "Return ONLY one JSON value matching this closed schema:". Three contracts
    word their preamble differently -- `batch-critic.v2` opens "You are an
    argumentative critic...", `conjecturer.turn.v6` opens "You are the
    conjecture operator (gamma)..." -- so 123 of 292 prompts on one root were
    reported as having no delimitable schema when they plainly had one. The
    shares that survived were therefore a mean over a BIASED subset: only the
    prompts that happened to use one phrasing.

    So the schema is now found by what it IS rather than by what introduces it:
    every balanced `{...}` in the prompt is parsed, and the largest one that
    actually looks like a JSON Schema (carrying `$defs` or `properties`) wins.
    A prompt with no such object is reported as undelimited and excluded from
    the mean rather than contributing a wrong share.
    """
    best: tuple[int, int] | None = None
    i = 0
    while True:
        start = text.find("{", i)
        if start < 0:
            break
        end = _balanced(text, start)
        if end is None:
            break
        blob = text[start:end]
        if len(blob) > 200 and ('"$defs"' in blob or '"properties"' in blob):
            try:
                parsed = json.loads(blob)
            except Exception:  # noqa: BLE001
                parsed = None
            if isinstance(parsed, dict) and ("$defs" in parsed or "properties" in parsed):
                if best is None or (end - start) > (best[1] - best[0]):
                    best = (start, end)
        i = start + 1
    return best


def _attempts(root: pathlib.Path):
    directory = root / "objects" / "workflow-provider-attempt-v1"
    if not directory.exists():
        return
    for path in sorted(directory.rglob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))["data"]
        except Exception:  # noqa: BLE001
            continue
        digest = data.get("prompt_sha256")
        if not digest:
            continue
        blob = root / "blobs" / digest[:2] / digest
        if not blob.exists():
            continue
        yield data, blob.read_text(encoding="utf-8", errors="replace")


def report(root: pathlib.Path) -> None:
    per_contract: dict[str, list[tuple[int, int, int]]] = defaultdict(list)
    undelimited = 0
    total = 0
    for data, text in _attempts(root):
        total += 1
        span = _schema_span(text)
        if span is None:
            undelimited += 1
            continue
        schema_chars = span[1] - span[0]
        per_contract[str(data.get("contract_id"))].append(
            (len(text), schema_chars, int(data.get("prompt_tokens") or 0))
        )

    print(f"\n=== {root} ===")
    print(f"  attempts with a stored prompt blob : {total}")
    print(f"  prompts with NO delimitable schema : {undelimited}")
    if not per_contract:
        print("  nothing measurable")
        return
    all_rows = [row for rows in per_contract.values() for row in rows]
    print(f"  prompts measured                   : {len(all_rows)}")
    print(
        f"  mean prompt chars                  : "
        f"{statistics.mean(r[0] for r in all_rows):,.0f}"
    )
    print(
        f"  mean schema chars                  : "
        f"{statistics.mean(r[1] for r in all_rows):,.0f}"
    )
    shares = [r[1] / r[0] for r in all_rows if r[0]]
    print(f"  mean schema SHARE                  : {statistics.mean(shares):.1%}")
    print(f"  min / max share                    : {min(shares):.1%} / {max(shares):.1%}")
    toks = [r[2] for r in all_rows if r[2]]
    if toks:
        print(f"  mean recorded prompt_tokens        : {statistics.mean(toks):,.0f}")
        print(
            "  (characters are NOT tokens; both are reported so the two are "
            "never conflated)"
        )
    print("  by contract:")
    for contract, rows in sorted(per_contract.items()):
        s = [r[1] / r[0] for r in rows if r[0]]
        print(
            f"      {contract}: n={len(rows)}  "
            f"prompt~{statistics.mean(r[0] for r in rows):,.0f} chars  "
            f"schema~{statistics.mean(r[1] for r in rows):,.0f} chars  "
            f"share {statistics.mean(s):.1%}"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("roots", nargs="+")
    args = parser.parse_args()
    for raw in args.roots:
        report(pathlib.Path(raw))
    return 0


if __name__ == "__main__":
    sys.exit(main())
