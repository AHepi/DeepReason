"""Census of REAL dispatched prompts against the four robust layout rules.

Evidence, not reconstruction: every prompt measured here is a blob whose
sha256 equals the `prompt_sha256` of a committed `workflow-provider-attempt-v1`
record, so the bytes measured are the bytes that reached the provider.

The four rules (docs/RESEARCH_ATTENTION_LAYOUT_2026-08-28.md, "Robust across
models"), as this instrument operationalises them:

(a) nothing load-bearing after the question  -> `after_question_chars`
(b) standing instructions at or under ~40    -> `instructions`
(c) prior-round material distilled, full text retrievable by reference
                                             -> `carry_forward`
(d) few large blocks, not many small ones    -> `blocks`, `median_block_chars`

Counting rules, stated so they can be disputed rather than trusted:

*   A BLOCK is a delimiter-bounded region of the rendered prompt: each `## id`
    pack section, plus each `\n\n`-separated region of the pre-pack head.
    This is the unit the research note's scale-free U-shape claim is about.
*   A STANDING INSTRUCTION is one normative clause addressed to the model in
    the NATURAL-LANGUAGE portion: a sentence or semicolon-clause that is
    imperative or carries a deontic marker (must/never/only/do not/may
    not/always/should/required/forbidden/return/propose/judge/...).
    EXCLUDED, and this exclusion is a disclosed choice: the JSON Schema, the
    syntax example, and data lines (artifact bodies, `predicate:`/`program:`
    commitment schemas, alias listings). The harness VALIDATES the schema
    mechanically and repairs violations, so schema clauses do not compete for
    the adherence budget 2607.19257 measured; prose clauses do.
*   ATTEMPT INDEX is reported separately: attempt 0 is the run's real layout;
    attempts >0 are REPAIR turns whose pack is a diagnostic envelope carrying
    the model's own rejected output, so their block counts measure the repair
    protocol rather than the layout under test.
*   SCHEMA CONSTRAINTS are counted separately and are NOT part of the standing
    instruction count, for the reason above. The number is reported so the
    exclusion can be judged rather than trusted.
*   THE QUESTION is the element that states what is being asked of this seat.
    On the two IR renderers it is a pack section -- `problem` for a
    conjecturer, `problem-context` for a critic. On the seats that are NOT on
    the IR (judge, defender, variator, batch critic, summarizer, thesis) the
    pack is unstructured prose, so the question is the first line opening with
    a task marker: `QUESTION:`, `DIRECTIVE:` or `TASK:`. A seat with neither
    is reported as having no locatable question rather than as compliant.
    `after_question_chars` counts the characters rendered after the question
    ends, excluding nothing -- every one of them is material the model reads
    after having read what it was asked.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import statistics
import sys

_DEONTIC = re.compile(
    r"\b(must|never|only|always|should|shall|may not|cannot|do not|don't|"
    r"required|require|forbidden|invalid|rejected|refuted|ensure|avoid)\b",
    re.IGNORECASE,
)
# An imperative opener: a sentence beginning with a bare verb we actually use.
_IMPERATIVE = re.compile(
    r"^(return|respond|propose|give|judge|answer|write|mount|assess|state|"
    r"choose|include|carry|apply|classify|concede|explore|complete|vary|"
    r"reconcile|produce|argue|tie|set|use|read|list|report|treat|copy|"
    r"submit|address|explain|name|cite|quote|repair|do|never|always)\b",
    re.IGNORECASE,
)
_DATA_LINE = re.compile(
    r"^\s*(\{|\[|- [0-9a-f]{12,}|- SRC_\d+|- [A-Za-z0-9_.@-]+: (predicate|program):"
    r"|\"|PROBLEM [0-9a-z-]+$|TARGET [0-9a-f]{12,}|spec \d+:)"
)
_QUESTION_MARKER = re.compile(r"(?m)^(QUESTION|DIRECTIVE|TASK):")
_QUESTION_SECTION = {
    "conjecturer": ("problem", "problem-context"),
    "argumentative_critic": ("problem-context", "problem"),
    "defender": ("problem-context", "problem"),
    "judge": ("problem-context", "problem"),
    "variator": ("problem-context", "problem"),
    "summarizer": ("problem-context", "problem"),
    "thesis": ("problem-context", "problem"),
}


def _strip_json(text: str) -> str:
    """Drop machine-checked and data regions, keep model-facing prose."""
    out = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if _DATA_LINE.match(line):
            continue
        if len(stripped) > 400 and stripped.count('"') > 20:
            continue  # an inlined record rendered on one line
        out.append(line)
    return "\n".join(out)


_SCHEMA_KEYWORD = re.compile(
    r'"(pattern|enum|const|maxItems|minItems|maxLength|minLength|maximum|'
    r'minimum|additionalProperties|required)"'
)


def count_schema_constraints(prompt: str) -> int:
    """Machine-checked constraints, reported but excluded from `instructions`."""
    return len(_SCHEMA_KEYWORD.findall(prompt))


def count_instructions(prose: str) -> int:
    n = 0
    for chunk in re.split(r"(?<=[.!?;:])\s+|\n", prose):
        clause = chunk.strip(" -\t")
        if len(clause) < 12:
            continue
        if _IMPERATIVE.match(clause) or _DEONTIC.search(clause):
            n += 1
    return n


def split_blocks(prompt: str) -> tuple[list[tuple[str, str]], str, str]:
    """-> (blocks, head, pack). A block is (label, text)."""
    marker = "\nINPUT:\n"
    if marker in prompt:
        cut = prompt.index(marker)
        head, pack = prompt[:cut], prompt[cut + len(marker) :]
    else:
        # Standard template: role prose, then the JSON-only line + schema, then
        # the pack. The pack starts at the first `## ` section header.
        m = re.search(r"(?m)^## ", prompt)
        if m:
            head, pack = prompt[: m.start()], prompt[m.start() :]
        else:
            head, pack = prompt, ""
    blocks = [("head", part) for part in head.split("\n\n") if part.strip()]
    for m in re.finditer(r"(?m)^## (\S+)\n", pack):
        end = pack.find("\n## ", m.end())
        body = pack[m.end() : end if end != -1 else len(pack)]
        blocks.append((m.group(1), body))
    return blocks, head, pack


def census_one(prompt: str, role: str) -> dict:
    blocks, head, pack = split_blocks(prompt)
    prose = _strip_json(prompt)
    ids = [label for label, _ in blocks]
    question = None
    for candidate in _QUESTION_SECTION.get(role, ("problem", "problem-context")):
        if candidate in ids:
            question = candidate
            break
    after = None
    after_ids: list[str] = []
    if question is None:
        # Not on the IR: locate the task marker in the raw prompt instead.
        marker = _QUESTION_MARKER.search(prompt)
        if marker is not None:
            end = prompt.find("\n\n", marker.end())
            question = f"marker:{marker.group(1).lower()}"
            after = 0 if end == -1 else len(prompt) - end - 2
    elif question is not None:
        m = re.search(rf"(?m)^## {re.escape(question)}\n", pack)
        end = pack.find("\n## ", m.end())
        after = 0 if end == -1 else len(pack) - end
        after_ids = [i for i in ids[ids.index(question) + 1 :]]
    sizes = [len(body) for _, body in blocks]
    return {
        "chars": len(prompt),
        "blocks": len(blocks),
        "block_ids": ids,
        "median_block_chars": int(statistics.median(sizes)) if sizes else 0,
        "small_blocks": sum(1 for s in sizes if s < 400),
        "instructions": count_instructions(prose),
        "schema_constraints": count_schema_constraints(prompt),
        "prose_chars": len(prose),
        "question_section": question,
        "after_question_chars": after,
        "after_question_ids": after_ids,
    }


def collect(base: pathlib.Path = pathlib.Path("experiments")):
    rows = []
    for log in base.rglob("log.jsonl"):
        root = log.parent
        attempts = root / "objects" / "workflow-provider-attempt-v1"
        blobs = root / "blobs"
        if not attempts.is_dir() or not blobs.is_dir():
            continue
        index = {}
        for p in blobs.rglob("*"):
            if p.is_file():
                index[hashlib.sha256(p.read_bytes()).hexdigest()] = p
        for p in attempts.glob("*.json"):
            d = json.load(p.open())["data"]
            blob = index.get(d.get("prompt_sha256"))
            if blob is None:
                continue
            try:
                text = blob.read_text("utf-8")
            except UnicodeDecodeError:
                continue
            role = d["route_lease"]["role"]
            row = census_one(text, role)
            row.update(
                root=str(root),
                role=role,
                contract=d.get("contract_id"),
                prompt_tokens=d.get("prompt_tokens"),
                prompt_sha256=d["prompt_sha256"],
                attempt_index=d.get("attempt_index"),
                blob=str(blob),
            )
            rows.append(row)
    return rows


if __name__ == "__main__":
    rows = collect()
    out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
    seats: dict[str, list[dict]] = {}
    first = [r for r in rows if r.get("attempt_index") == 0]
    for r in first:
        seats.setdefault(f"{r['role']}/{r['contract']}", []).append(r)
    print(f"{len(rows)} sha-verified dispatched prompts across "
          f"{len({r['root'] for r in rows})} committed roots; "
          f"{len(first)} are first turns (attempt 0) and only those are "
          f"tabled -- repair turns measure the repair protocol, not the "
          f"layout.\n")
    hdr = (f"{'seat (role/contract)':<44} {'n':>5} {'instr':>10} {'blocks':>9} "
           f"{'medblk':>7} {'small':>6} {'afterQ chars':>13} {'schema':>8}")
    print(hdr)
    print("-" * len(hdr))
    for seat, rs in sorted(seats.items()):
        i = [r["instructions"] for r in rs]
        b = [r["blocks"] for r in rs]
        aq = [r["after_question_chars"] for r in rs
              if r["after_question_chars"] is not None]
        print(
            f"{seat:<44} {len(rs):>5} "
            f"{min(i):>4}-{max(i):<5} "
            f"{min(b):>3}-{max(b):<5} "
            f"{int(statistics.median([len(x['block_ids']) and x['median_block_chars'] for x in rs])):>7} "
            f"{int(statistics.median([x['small_blocks'] for x in rs])):>6} "
            f"{(str(min(aq)) + '-' + str(max(aq))) if aq else 'no question section':>13} "
            f"{int(statistics.median([x['schema_constraints'] for x in rs])):>8}"
        )
    if out:
        out.write_text(json.dumps(rows, indent=1, sort_keys=True))
        print(f"\nrows -> {out}")
