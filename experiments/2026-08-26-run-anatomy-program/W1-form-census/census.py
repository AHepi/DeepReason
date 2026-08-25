"""W1 — the form-filling census.

What the provider models actually wrote into every typed form, over every
committed run root. Read-only: opens each root's `log.jsonl`, `objects/`
and `blobs/` and writes nothing back into any root.

One row per PROVIDER ATTEMPT. A row says which form (contract id), which
seat, which role, which cycle, whether the attempt arrived VALID, and — for
an invalid arrival — which field failed and how, taken from the record's own
diagnostic `code` rather than from a taxonomy invented here.

THE JOIN, and why it is this one (docs/ERRATA.md E42)
-----------------------------------------------------
`attempt_trace[i].diagnostic_ref` is NOT the authority for attempt i's
failure. `workflow/repair_transaction.py::_terminalize_invalid` writes it as
`trace_ref or next_diagnostic_ref`, so on a repair attempt it names the
diagnostic derived AFTER the patch was applied. A census keyed on it scores
attempt N's response against attempt N+1's authority, which is exactly how
E42 read thirteen convergent repairs as off-target patches.

This census joins instead through
`workflow-semantic-admission-v1.provider_attempt_ref`, whose
`diagnostic_refs` are the diagnostics derived from THAT attempt. Do not
"simplify" this to the attempt_trace field: it is the same mistake with a
shorter line.

A SECOND join hazard of the same family, found by this census and recorded
here so the next reader does not pay for it again: `attempt_trace[i].attempt`
is the index of the entry WITHIN that log record's own trace list, and is 0
for every attempt in every committed root. It is NOT the workflow attempt
index the repair grant meters. That number lives only on
`workflow-provider-attempt-v1.attempt_index`. Joining on
(work_id, attempt_index, raw_ref) therefore silently drops every repair
attempt — the exact rows a repair census exists to see. The join key is
(work_id, raw_ref), and the attempt index is READ FROM the object.

CYCLE ATTRIBUTION
-----------------
`log.jsonl` carries no cycle number. `progress.jsonl` carries `cycle` and
`token_spend` at each `cycle complete`, and token spend is the monotone sum
of the log's own per-attempt `tokens`. An attempt therefore belongs to the
first cycle whose recorded cumulative spend covers the running total after
that attempt. The join is checked, not assumed: `cycle_join_exact` reports
whether the final cumulative log total reconciles with the record, and every
consumer must read that flag before quoting a per-cycle number.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PROGRAM = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(PROGRAM))

# The 2026-08-22 lossless-spelling fix (experiments/2026-08-22-fix-repair-patch-
# transport, commit 97a964583) absorbs exactly these spellings: containers
# unwrapped, harness echoes dropped, `pointer` renamed to `path`. A root that
# ran BEFORE that commit may show them; a root that ran after may not, and that
# is the post-fix question the census answers.
LOSSLESS_SPELLING_FIX_TS = "2026-08-22T00:00:00+00:00"
ECHO_OR_CONTAINER_POINTERS = {
    "/patch",
    "/patches",
    "/operations",
    "/repair.patch.v1",
    "/repair_patch_v1",
    "/contract",
    "/baseline_sha256",
    "/schema",
    "/pointer",
}

# Conservative hedge/refusal markers. Listed here rather than hidden in a
# regex so a reader can audit and re-run with a different list; a hit is a
# CANDIDATE hedge, not a proven one, and the census reports exemplars so the
# classification can be checked by eye.
HEDGE_MARKERS = (
    "insufficient",
    "unknown",
    "not enough information",
    "cannot determine",
    "cannot be determined",
    "unable to",
    "no evidence",
    "n/a",
    "not applicable",
    "unclear",
    "i cannot",
    "i can't",
    "as an ai",
    "not provided",
    "not specified",
    "placeholder",
    "tbd",
)

FENCE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.MULTILINE)
FENCED_BLOCK = re.compile(r"```(?:json)?\s*(.+?)```", re.DOTALL)


# --------------------------------------------------------------------------
# root plumbing
# --------------------------------------------------------------------------


def load_object_family(root: str, family: str) -> dict:
    """Every object of one schema family, keyed by its content id."""
    d = os.path.join(root, "objects", family)
    out = {}
    if not os.path.isdir(d):
        return out
    for name in os.listdir(d):
        if not name.endswith(".json"):
            continue
        rec = json.load(open(os.path.join(d, name)))
        data = rec.get("data", rec)
        out[data.get("id") or rec.get("id") or name[:-5]] = data
    return out


def read_blob(root: str, ref: str):
    """A blob by content ref. Returns (parsed_json_or_None, raw_text_or_None)."""
    if not ref:
        return None, None
    ref = ref.split(":")[-1]
    p = os.path.join(root, "blobs", ref[:2], ref)
    if not os.path.exists(p):
        return None, None
    try:
        text = open(p, encoding="utf-8", errors="replace").read()
    except OSError:
        return None, None
    try:
        return json.loads(text), text
    except ValueError:
        return None, text


def parse_model_json(text: str) -> tuple[object | None, str]:
    """(parsed, wire_shape) for one raw response.

    The tolerance here is a READING convenience for the content census and
    says nothing about whether the harness accepted the response — arrival
    validity always comes from the record's own `valid` flag, never from
    whether this function succeeded. `wire_shape` is the census's own
    measurement of HOW the JSON arrived, which is the PhantomFill
    "format violation" axis: a model that wraps required JSON in prose is
    paying the refusal tax in a form this harness happens to tolerate.
    """
    if not text:
        return None, "empty"
    try:
        return json.loads(text), "bare_json"
    except ValueError:
        pass
    stripped = FENCE.sub("", text).strip()
    try:
        return json.loads(stripped), "fenced_json"
    except ValueError:
        pass
    blocks = FENCED_BLOCK.findall(text)
    for block in reversed(blocks):
        try:
            return json.loads(block), "prose_wrapped_fenced_json"
        except ValueError:
            continue
    start = text.find("{")
    if start > 0:
        depth, in_str, esc = 0, False, False
        for i in range(start, len(text)):
            ch = text[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start : i + 1]), "prose_wrapped_bare_json"
                    except ValueError:
                        break
    return None, "unparsed_by_census"


def cycle_index(root: str) -> tuple[list[tuple[int, int]], int | None]:
    """(cycle, cumulative_token_spend) at each recorded cycle completion."""
    p = os.path.join(root, "progress.jsonl")
    if not os.path.exists(p):
        return [], None
    marks, limit = [], None
    for line in open(p):
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        limit = rec.get("token_limit", limit)
        if rec.get("activity") == "cycle complete":
            marks.append((rec.get("cycle"), rec.get("token_spend") or 0))
    marks.sort(key=lambda m: m[1])
    return marks, limit


# --------------------------------------------------------------------------
# diagnostics
# --------------------------------------------------------------------------


def flatten_diagnostics(blob) -> list[dict]:
    """One record's diagnostics, whichever of the four shapes it carries.

    The record writes four different blob shapes under `diagnostic_refs`:
    a bare field diagnostic (`error`/`path`), a repair ENVELOPE carrying a
    `diagnostics` list, a component failure (`error_code`), and an
    unrepairable note (`message` only). All four are real diagnostics and
    none may be dropped, or the invalid-attempt counts stop summing.
    """
    if not isinstance(blob, dict):
        return []
    if isinstance(blob.get("diagnostics"), list):
        out = []
        for d in blob["diagnostics"]:
            if isinstance(d, dict):
                d = dict(d)
                d.setdefault("contract", blob.get("contract"))
                d["_kind"] = "repair_envelope"
                out.append(d)
        return out
    if "error" in blob:
        d = dict(blob)
        d["message"] = blob.get("error")
        d["_kind"] = "field_diagnostic"
        return [d]
    if "error_code" in blob:
        return [
            {
                "code": blob.get("error_code"),
                "message": blob.get("message"),
                "path": None,
                "component": blob.get("component"),
                "phase": blob.get("phase"),
                "disposition": blob.get("disposition"),
                "_kind": "component_failure",
            }
        ]
    if "message" in blob:
        return [
            {
                "code": blob.get("schema") or "note",
                "message": blob.get("message"),
                "path": None,
                "contract": blob.get("contract"),
                "_kind": "note",
            }
        ]
    return []


def normalize_message(msg: str) -> str:
    """A diagnostic message with its variable parts removed, so the same
    failure written about two different fields collapses to one key."""
    msg = re.sub(r"'[^']*'", "'X'", msg or "")
    msg = re.sub(r"/\d+", "/N", msg)
    return re.sub(r"\b\d+\b", "N", msg).strip()


def build_message_code_table(roots: list[str]) -> dict:
    """message -> code, learned from diagnostics that carry BOTH.

    The record writes the same pydantic failure in two shapes: inside a repair
    envelope it carries a machine-readable `code`, and as a bare field
    diagnostic it carries only `error`. Rather than invent codes for the bare
    shape, this learns the mapping from the shapes that state both, and
    applies it only where the mapping is UNAMBIGUOUS — a message seen with two
    different codes is left uncoded rather than guessed at.
    """
    seen: dict[str, set] = defaultdict(set)
    for root_rel in roots:
        root = os.path.join(REPO, root_rel)
        for adm in load_object_family(root, "workflow-semantic-admission-v1").values():
            for ref in adm.get("diagnostic_refs") or []:
                blob, _ = read_blob(root, ref)
                for d in flatten_diagnostics(blob):
                    if d.get("code") and d.get("message"):
                        seen[normalize_message(d["message"])].add(str(d["code"]))
    return {m: next(iter(c)) for m, c in seen.items() if len(c) == 1}


def failure_class(diag: dict, message_codes: dict | None = None) -> str:
    """A named field-level cause.

    The primary key is the record's own machine-readable `code`. Where a
    diagnostic carries none, the code the record itself attaches to that same
    message elsewhere is used (`build_message_code_table`). Only the four
    wire-level shapes, which never carry a code anywhere, are matched by text.
    """
    code = diag.get("code")
    if code:
        return str(code)
    msg = (diag.get("message") or "").strip()
    learned = (message_codes or {}).get(normalize_message(msg))
    if learned:
        return learned
    low = msg.lower()
    if "length limit" in low and "cut off" in low:
        return "TRUNCATED_MID_JSON"
    if "no complete top-level json value" in low:
        return "WIRE_NO_COMPLETE_JSON"
    if "multiple top-level json values" in low or "trailing content" in low:
        return "WIRE_TRAILING_CONTENT"
    if low.startswith("extra field at"):
        return "extra_forbidden"
    if not msg:
        return "UNCODED_EMPTY"
    return "UNCODED_OTHER"


def normalize_pointer(path) -> str:
    """A JSON pointer with list indices collapsed, so /cases/0/x and
    /cases/7/x aggregate as one field."""
    if not path:
        return ""
    return re.sub(r"/\d+", "/*", str(path))


# --------------------------------------------------------------------------
# content classes
# --------------------------------------------------------------------------


def walk_values(value, pointer=""):
    """Every leaf and array in a parsed response, with its normalized pointer."""
    if isinstance(value, dict):
        for k, v in value.items():
            yield from walk_values(v, f"{pointer}/{k}")
    elif isinstance(value, list):
        if value and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in value):
            yield pointer, "numeric_array", value
        for x in value:
            yield from walk_values(x, f"{pointer}/*")
    else:
        if isinstance(value, bool):
            yield pointer, "bool", value
        elif isinstance(value, (int, float)):
            yield pointer, "number", value
        elif isinstance(value, str):
            yield pointer, "string", value
        elif value is None:
            yield pointer, "null", value


def decimal_places(x) -> int:
    s = repr(float(x))
    if "e" in s or "E" in s:
        return -1
    return len(s.split(".")[1].rstrip("0")) if "." in s else 0


def hedge_hits(text: str) -> list[str]:
    low = text.lower()
    return [m for m in HEDGE_MARKERS if m in low]


# --------------------------------------------------------------------------
# the census over one root
# --------------------------------------------------------------------------


def census_root(root_rel: str, message_codes: dict | None = None) -> dict:
    root = os.path.join(REPO, root_rel)
    status = json.load(open(os.path.join(root, "run-status.json")))

    provider_attempts = load_object_family(root, "workflow-provider-attempt-v1")
    admissions_by_attempt = {}
    for adm in load_object_family(root, "workflow-semantic-admission-v1").values():
        admissions_by_attempt[adm.get("provider_attempt_ref")] = adm
    terminals = load_object_family(root, "workflow-work-terminal-v1")
    preparations = load_object_family(root, "workflow-work-preparation-v1")
    decompositions = load_object_family(root, "workflow-contract-decomposition-transition-v1")
    insufficiency = load_object_family(root, "workflow-route-seat-insufficient-capability-v1")

    # Provider attempts, keyed by (work_id, raw_ref) — see the join hazard in
    # the module docstring. `collisions` counts keys that resolve to more than
    # one attempt object; it is reported rather than hidden, because a nonzero
    # value would mean the key is not a key on this root and its per-attempt
    # numbers must not be quoted.
    pa_by_key: dict = {}
    pa_collisions = 0
    for pa in provider_attempts.values():
        key = (pa.get("work_id"), pa.get("raw_ref"))
        if key in pa_by_key:
            pa_collisions += 1
            continue
        pa_by_key[key] = pa

    marks, token_limit = cycle_index(root)

    rows: list[dict] = []
    running = 0
    content_fields: dict[tuple, Counter] = defaultdict(Counter)
    content_kinds: dict[tuple, Counter] = defaultdict(Counter)
    numeric_precision: dict[tuple, Counter] = defaultdict(Counter)
    string_hedges: dict[tuple, Counter] = defaultdict(Counter)
    hedge_exemplars: list[dict] = []
    unparsed_valid = 0
    wire_shapes: Counter = Counter()
    wire_shape_by_contract: dict = defaultdict(Counter)
    prose_exemplars: list[dict] = []

    for line in open(os.path.join(root, "log.jsonl")):
        line = line.strip()
        if not line:
            continue
        event = json.loads(line)
        llm = event.get("llm")
        if not llm:
            continue
        work_id = llm.get("work_order_id")
        for trace in llm.get("attempt_trace") or []:
            running += trace.get("tokens") or 0
            # The first cycle whose recorded cumulative spend covers this
            # attempt. Attempts past the last recorded boundary belong to a
            # cycle that never completed; they are labelled, not dropped.
            cycle, cycle_complete = None, True
            for c, spend in marks:
                if running <= spend:
                    cycle = c
                    break
            if cycle is None:
                cycle = (marks[-1][0] + 1) if marks else None
                cycle_complete = False
            pa = pa_by_key.get((work_id, trace.get("raw_ref")))
            adm = admissions_by_attempt.get(pa["id"]) if pa else None

            diags = []
            for ref in (adm or {}).get("diagnostic_refs") or []:
                blob, _ = read_blob(root, ref)
                diags.extend(flatten_diagnostics(blob))

            row = {
                "seq": event["seq"],
                "ts": event["ts"],
                "rule": event["rule"],
                "role": llm.get("role"),
                "model": llm.get("model"),
                "seat": trace.get("seat"),
                "endpoint_id": trace.get("endpoint_id"),
                "contract_id": trace.get("contract_id"),
                # From the attempt OBJECT: the workflow index the grant meters.
                # `trace["attempt"]` is the within-record list index and is
                # always 0 — never use it here.
                "attempt_index": (pa or {}).get("attempt_index"),
                "attempt_object_found": pa is not None,
                "is_repair": bool(trace.get("repair_scope")),
                "repair_scope": trace.get("repair_scope") or "",
                "cycle": cycle,
                "cycle_completed": cycle_complete,
                "valid_on_arrival": bool(trace.get("valid")),
                "truncated": bool(trace.get("truncated")),
                "natural_stop": trace.get("natural_stop"),
                "transport_attempts": trace.get("transport_attempts"),
                "transport_diagnostics": trace.get("transport_diagnostics") or [],
                "tokens": trace.get("tokens"),
                "max_tokens": trace.get("max_tokens"),
                "work_id": work_id,
                "raw_ref": trace.get("raw_ref"),
                "admission_outcome": (adm or {}).get("outcome"),
                "failures": [
                    {
                        "class": failure_class(d, message_codes),
                        "field": normalize_pointer(d.get("path")),
                        "field_raw": d.get("path"),
                        "message": (d.get("message") or "")[:400],
                        "allowed": (d.get("allowed") or "")[:200],
                        "rejected_handle": d.get("rejected_handle"),
                        "observed_handle_kind": d.get("observed_handle_kind"),
                        "omission_or_unknown_legal": d.get("omission_or_unknown_legal"),
                        "legal_handles": d.get("legal_handles"),
                        "kind": d.get("_kind"),
                    }
                    for d in diags
                ],
            }
            rows.append(row)

            if row["valid_on_arrival"]:
                _, text = read_blob(root, trace.get("raw_ref"))
                parsed, shape = parse_model_json(text)
                cid = trace.get("contract_id")
                wire_shapes[shape] += 1
                wire_shape_by_contract[cid][shape] += 1
                if shape.startswith("prose_wrapped") and len(prose_exemplars) < 12:
                    prose_exemplars.append(
                        {
                            "seq": event["seq"],
                            "contract_id": cid,
                            "role": llm.get("role"),
                            "shape": shape,
                            "preamble": (text or "")[: (text or "").find("{") if "{" in (text or "") else 200][:400],
                        }
                    )
                if parsed is None:
                    unparsed_valid += 1
                    continue
                for ptr, kind, value in walk_values(parsed):
                    key = (cid, ptr)
                    content_kinds[key][kind] += 1
                    if kind == "string":
                        content_fields[key][value if len(value) <= 64 else "<<long>>"] += 1
                        hits = hedge_hits(value)
                        if hits:
                            string_hedges[key][hits[0]] += 1
                            if len(hedge_exemplars) < 40:
                                hedge_exemplars.append(
                                    {
                                        "root": root_rel,
                                        "seq": event["seq"],
                                        "contract_id": cid,
                                        "field": ptr,
                                        "marker": hits[0],
                                        "value": value[:300],
                                    }
                                )
                    elif kind == "bool":
                        content_fields[key][str(value)] += 1
                    elif kind == "number":
                        numeric_precision[key][decimal_places(value)] += 1
                    elif kind == "numeric_array":
                        numeric_precision[key][f"len={len(value)}"] += 1
                        for x in value:
                            numeric_precision[key][decimal_places(x)] += 1

    # ---- per-contract repair fights, against the manifest's own grant ----
    grants = {}
    mp = os.path.join(root, "run-manifest.json")
    if os.path.exists(mp):
        pol = json.load(open(mp)).get("contract_schema_repair_policy") or {}
        for g in pol.get("grants") or []:
            grants[g.get("contract_id")] = {
                "maximum_provider_calls": g.get("maximum_provider_calls"),
                "maximum_schema_repairs": g.get("maximum_schema_repairs"),
            }

    per_work = defaultdict(list)
    for r in rows:
        per_work[r["work_id"]].append(r)

    fights = []
    for wid, group in per_work.items():
        group.sort(key=lambda r: (r["attempt_index"] or 0, r["seq"]))
        if len(group) == 1 and group[0]["valid_on_arrival"]:
            continue
        term = None
        for t in terminals.values():
            if t.get("work_id") == wid:
                term = t
                break
        prep = None
        for p in preparations.values():
            if p.get("id") == wid or wid == p.get("id"):
                prep = p
                break
        fights.append(
            {
                "work_id": wid,
                "contract_id": group[0]["contract_id"],
                "role": group[0]["role"],
                "seat": group[0]["seat"],
                "cycle": group[0]["cycle"],
                "calls_consumed": len(group),
                "grant": grants.get(group[0]["contract_id"]),
                "arrival_validity": [r["valid_on_arrival"] for r in group],
                "asked_for": [
                    [f["field"] for f in r["failures"] if f["field"]] for r in group
                ],
                "came_back_at": [r["repair_scope"] for r in group],
                "terminal_status": (term or {}).get("status"),
                "terminal_reason": (term or {}).get("reason_code"),
                "task_kind": (prep or {}).get("task_kind"),
            }
        )

    # ---- coercion: fabricate-vs-escape at reference fields ----
    coercion = {"escape_legal": 0, "fabricated_handle": 0, "handle_kinds": Counter()}
    for r in rows:
        for f in r["failures"]:
            if f["observed_handle_kind"]:
                coercion["handle_kinds"][f["observed_handle_kind"]] += 1
            if f["omission_or_unknown_legal"] is True:
                coercion["escape_legal"] += 1
                if f["observed_handle_kind"] == "unknown":
                    coercion["fabricated_handle"] += 1
    coercion["handle_kinds"] = dict(coercion["handle_kinds"])

    # ---- did the NEXT attempt take the escape it was offered? ----
    escape_followups = Counter()
    for wid, group in per_work.items():
        group.sort(key=lambda r: (r["attempt_index"] or 0, r["seq"]))
        for i, r in enumerate(group[:-1]):
            offered = [
                f for f in r["failures"] if f["omission_or_unknown_legal"] is True
            ]
            if not offered:
                continue
            nxt = group[i + 1]
            _, text = read_blob(root, nxt["raw_ref"])
            body = (text or "").lower()
            if not text:
                escape_followups["no_response_recorded"] += 1
            elif '"remove"' in body:
                escape_followups["escape_taken_remove"] += 1
            elif nxt["valid_on_arrival"]:
                escape_followups["repaired_without_remove"] += 1
            else:
                escape_followups["still_invalid"] += 1

    # ---- lossless-spelling class (E42) ----
    spelling = Counter()
    for r in rows:
        for f in r["failures"]:
            if f["class"] == "extra_forbidden" and f["field_raw"] in ECHO_OR_CONTAINER_POINTERS:
                spelling[f["field_raw"]] += 1

    first_ts = rows[0]["ts"] if rows else None
    valid = sum(1 for r in rows if r["valid_on_arrival"])
    per_contract = defaultdict(lambda: {"attempts": 0, "valid": 0, "repair_attempts": 0})
    for r in rows:
        b = per_contract[r["contract_id"]]
        b["attempts"] += 1
        b["valid"] += int(r["valid_on_arrival"])
        b["repair_attempts"] += int(r["is_repair"])
    for cid, b in per_contract.items():
        b["grant"] = grants.get(cid)
        b["validity_rate"] = round(b["valid"] / b["attempts"], 4) if b["attempts"] else None

    failure_classes = Counter()
    failure_fields = Counter()
    for r in rows:
        for f in r["failures"]:
            failure_classes[f["class"]] += 1
            if f["field"]:
                failure_fields[(r["contract_id"], f["field"], f["class"])] += 1

    return {
        "schema": "run-anatomy.form-census.root.v1",
        "root": root_rel,
        "run_id": status.get("run_id"),
        "state": status.get("state"),
        "stop_reason": status.get("stop_reason"),
        "cycles_reached": status.get("cycle"),
        "first_ts": first_ts,
        "attempts": len(rows),
        "valid_on_arrival": valid,
        "validity_rate": round(valid / len(rows), 4) if rows else None,
        "repair_attempts": sum(1 for r in rows if r["is_repair"]),
        "truncated_attempts": sum(1 for r in rows if r["truncated"]),
        "unnatural_stop_attempts": sum(1 for r in rows if r["natural_stop"] is False),
        "cycle_join_exact": bool(marks) and running >= (marks[-1][1] if marks else 0),
        "attempt_objects_missing": sum(1 for r in rows if not r["attempt_object_found"]),
        "attempt_key_collisions": pa_collisions,
        "cumulative_log_tokens": running,
        "token_limit": token_limit,
        "per_contract": dict(per_contract),
        "failure_classes": dict(failure_classes.most_common()),
        "failure_fields": [
            {"contract_id": c, "field": f, "class": k, "count": n}
            for (c, f, k), n in failure_fields.most_common()
        ],
        "coercion": coercion,
        "escape_followups": dict(escape_followups),
        "lossless_spelling_pointers": dict(spelling),
        "decomposition_events": [
            {
                "source_contract_id": d.get("source_contract_id"),
                "atomic_contract_id": d.get("atomic_contract_id"),
                "trigger": d.get("trigger"),
                "role": (d.get("route_lease") or {}).get("role"),
                "seat": (d.get("route_lease") or {}).get("seat"),
                "children": len(d.get("child_keys") or []),
            }
            for d in decompositions.values()
        ],
        "route_seat_insufficient_capability": [
            {
                "contract_id": i.get("contract_id"),
                "attempted_contract_ids": i.get("attempted_contract_ids"),
                "maximum_provider_calls": i.get("maximum_provider_calls"),
                "maximum_schema_repairs": i.get("maximum_schema_repairs"),
                "observed_provider_calls": i.get("observed_provider_calls"),
                "outcome": i.get("outcome"),
            }
            for i in insufficiency.values()
        ],
        "work_terminals": dict(
            Counter(
                f"{t.get('status')}/{t.get('reason_code')}" for t in terminals.values()
            ).most_common()
        ),
        "repair_fights": fights,
        "content": {
            "valid_responses_unparsed": unparsed_valid,
            "wire_shapes": dict(wire_shapes.most_common()),
            "wire_shapes_by_contract": {
                c: dict(v.most_common()) for c, v in sorted(wire_shape_by_contract.items())
            },
            "prose_wrapped_exemplars": prose_exemplars,
            "field_kinds": {
                f"{c}{p}": dict(k) for (c, p), k in sorted(content_kinds.items())
            },
            "string_vocabularies": {
                f"{c}{p}": dict(v.most_common(12))
                for (c, p), v in sorted(content_fields.items())
                if len(v) <= 12
            },
            "string_hedges": {
                f"{c}{p}": dict(v) for (c, p), v in sorted(string_hedges.items())
            },
            "hedge_exemplars": hedge_exemplars,
            "numeric_precision": {
                f"{c}{p}": {str(kk): vv for kk, vv in sorted(v.items(), key=lambda x: str(x[0]))}
                for (c, p), v in sorted(numeric_precision.items())
            },
        },
        "rows": rows,
    }


def slug(root_rel: str) -> str:
    return root_rel.replace("experiments/", "").replace("/", "__")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", default=os.path.join(PROGRAM, "ROOT_INVENTORY.json"))
    ap.add_argument("--out", default=os.path.join(HERE, "census"))
    ap.add_argument("--only", default=None, help="substring filter on root path")
    args = ap.parse_args()

    inv = json.load(open(args.inventory))
    os.makedirs(args.out, exist_ok=True)

    # Learned over EVERY root, not just the filtered ones: the mapping is a
    # property of the record format, and a --only run must classify the same
    # way a full run does or two censuses of the same root disagree.
    message_codes = build_message_code_table([r["root"] for r in inv["roots"]])
    with open(os.path.join(HERE, "MESSAGE_CODE_TABLE.json"), "w") as fh:
        json.dump(
            {
                "schema": "run-anatomy.message-code-table.v1",
                "derived_from": "diagnostics carrying both `code` and `message`",
                "unambiguous_entries": len(message_codes),
                "table": message_codes,
            },
            fh,
            indent=1,
        )
        fh.write("\n")

    summaries = []
    for rec in inv["roots"]:
        root_rel = rec["root"]
        if args.only and args.only not in root_rel:
            continue
        doc = census_root(root_rel, message_codes)
        with open(os.path.join(args.out, f"{slug(root_rel)}.json"), "w") as fh:
            json.dump(doc, fh, indent=1)
            fh.write("\n")
        summary = {k: v for k, v in doc.items() if k not in ("rows", "repair_fights", "content")}
        summary["content_valid_responses_unparsed"] = doc["content"]["valid_responses_unparsed"]
        summary["wire_shapes"] = doc["content"]["wire_shapes"]
        summary["repair_fight_count"] = len(doc["repair_fights"])
        summaries.append(summary)
        print(
            f"{root_rel:100s} {doc['attempts']:5d} attempts "
            f"{doc['valid_on_arrival']:5d} valid ({doc['validity_rate']})"
        )

    with open(os.path.join(HERE, "CENSUS_PER_ROOT.json"), "w") as fh:
        json.dump(
            {"schema": "run-anatomy.form-census.per-root.v1", "roots": summaries},
            fh,
            indent=1,
        )
        fh.write("\n")
    print(f"\n{len(summaries)} roots -> {args.out}/ and CENSUS_PER_ROOT.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
