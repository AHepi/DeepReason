"""W6 — the token-flow map: every provider token, by purpose and by outcome.

Read-only. Reads the committed roots named by ../ROOT_INVENTORY.json and
writes three tables beside itself:

    FLOW_CALLS.jsonl      one row per provider attempt, every root
    FLOW_AGGREGATE.json   by-purpose and by-outcome rollups, per root and total
    METER_RECONCILIATION.json  the three token instruments, root by root

Nothing here invents a taxonomy.  Every class is a field the record already
carries:

    purpose   <- contract_id (which form was being filled)
    call_kind <- attempt_trace.repair_scope: empty is a first ask, non-empty
                 names the JSON pointer a repair re-ask was aimed at
    outcome   <- workflow-work-terminal-v1.status + .reason_code
    admission <- workflow-semantic-admission-v1.outcome
    fate      <- the replayed EpistemicState's status for the artifacts the
                 call's downstream window created

THE JOIN.  A provider call is one `llm` event on a `Control` rule.  Its
control refs (inputs + outputs + decision_ref) contain EXACTLY ONE
workflow-provider-attempt-v1 object id -- verified 3155/3155 across all 54
roots, and re-asserted here per root rather than assumed.  That object
carries the exact prompt/completion split; `log.jsonl`'s `llm.tokens`
carries only the total.  From the attempt, (work_id, attempt_index) joins
the work terminal and the semantic admission.

THE DOWNSTREAM WINDOW.  Tokens buy artifacts, and the artifacts a call
bought are the ones the log applies before the next provider call: the
record is append-only and single-threaded, so events strictly between call
N and call N+1 are call N's consequences.  That rule is not assumed either
-- conjecturer calls carry an explicit `conjecture-call:<seq>` backref on
the Conj event, and `window_backref_agreement` reports how often the window
rule and the backref name the same call.  A disagreement would invalidate
the fate column and is reported, never smoothed.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PROGRAM = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(PROGRAM, "..", ".."))

# contract_id -> (purpose, purpose_detail).  The mapping is a naming of the
# record's own contract ids, not a judgement about them: every contract that
# appears in any committed root is listed, and an unseen contract lands in
# "unclassified" loudly rather than being folded into a neighbour.
PURPOSE = {
    "conjecturer.turn.v6": ("generation", "conjecture-turn"),
    "conjecturer.atomic-candidate.v1": ("generation", "conjecture-atomic-leg"),
    "variator.direct.v1": ("generation", "variation"),
    "batch-critic.v2": ("criticism", "batch-critic"),
    "critic.atomic-target.v1": ("criticism", "critic-atomic-leg"),
    "judgeruling.direct.v1": ("adjudication", "judge-ruling"),
    "defender.direct.v1": ("adjudication", "defence"),
    "bridge.ledger.v3": ("report", "ledger"),
    "bridge.ledger-batch.v1": ("report", "ledger-batch"),
    "bridge.composition.v2": ("report", "composition"),
    "bridge.composition-batch.v1": ("report", "composition-batch"),
    "config-referee.v1": ("configuration", "config-referee"),
}

# Contracts whose admitted output is APPLIED as new artifacts.  A judge
# ruling, a defence, a variation and a report pass all legitimately create
# no artifact -- they move a status, or they compose prose -- so "this call
# bought no artifact" means something different for them than it does for a
# conjecture turn.
ARTIFACT_PRODUCING = {
    "conjecturer.turn.v6",
    "conjecturer.atomic-candidate.v1",
    "batch-critic.v2",
    "critic.atomic-target.v1",
}

# Terminal status -> the coarse outcome the operator's question asks for.
OUTCOME = {
    "completed": "admitted",
    "rejected": "rejected-into-repair",
    "schema_exhausted": "invalid-discarded",
    "abandoned": "abandoned",
    "budget_denied": "budget-denied-no-call",
}


def load_objects(root: str, family: str) -> list[dict]:
    d = os.path.join(root, "objects", family)
    if not os.path.isdir(d):
        return []
    return [json.load(open(os.path.join(d, f)))["data"] for f in sorted(os.listdir(d))]


def cycle_marks(root: str) -> list[tuple[int, int]]:
    """(cycle, cumulative token_spend) at each recorded cycle completion.

    progress.jsonl is the only place a cycle boundary is stamped against a
    token count; log.jsonl carries no per-event cycle.  Rows with a zero
    spend are skipped: a zero is the pre-run and post-terminal shape, not a
    boundary at the origin.
    """
    p = os.path.join(root, "progress.jsonl")
    if not os.path.exists(p):
        return []
    marks = []
    for line in open(p):
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        if row.get("token_spend") and row.get("activity") == "cycle complete":
            marks.append((row["cycle"], row["token_spend"]))
    return marks


def assign_cycle(marks: list[tuple[int, int]], cum_after: int) -> int | None:
    """The first completed cycle whose cumulative spend covers this call.

    A call past the last mark belongs to a cycle that never completed; it is
    reported as the last mark's cycle + 1 so the tail is visible rather than
    dropped.  With no marks at all the axis is absent, not zero.
    """
    if not marks:
        return None
    for cycle, spend in marks:
        if cum_after <= spend:
            return cycle
    return marks[-1][0] + 1


def replay_status(root: str) -> dict[str, str] | None:
    """Final status per artifact id, from a READ-ONLY replay of the root.

    A writable open repairs the root, which is to say destroys the evidence
    (dr-drive-harness section 5).  A root the reader cannot replay yields
    None and its fate column reports the absence.
    """
    try:
        from deepreason.harness import Harness

        h = Harness(os.path.join(REPO, root), read_only=True)
        return {aid: st.value for aid, st in h.state.status.items()}
    except Exception as exc:  # noqa: BLE001 - a legacy root may defeat the reader
        print(f"    replay unavailable for {root}: {type(exc).__name__}", file=sys.stderr)
        return None


def scan_root(root: str) -> dict:
    abs_root = os.path.join(REPO, root)
    attempts = {a["id"]: a for a in load_objects(abs_root, "workflow-provider-attempt-v1")}
    terminals = {
        (t["work_id"], t["attempt_index"]): t
        for t in load_objects(abs_root, "workflow-work-terminal-v1")
    }
    admissions = {
        (a["work_id"], a["attempt_index"]): a
        for a in load_objects(abs_root, "workflow-semantic-admission-v1")
    }
    events = [json.loads(l) for l in open(os.path.join(abs_root, "log.jsonl")) if l.strip()]
    by_seq = {e["seq"]: e for e in events}
    marks = cycle_marks(abs_root)
    status = replay_status(root)

    # log seq of every provider call, in order -- the downstream windows
    call_seqs = [e["seq"] for e in events if e.get("llm")]
    next_call = {s: (call_seqs[i + 1] if i + 1 < len(call_seqs) else None)
                 for i, s in enumerate(call_seqs)}

    # explicit conjecture-call backrefs, for the window rule's self-check
    backref: dict[int, list[int]] = defaultdict(list)
    for e in events:
        for i in e.get("inputs") or []:
            if isinstance(i, str) and i.startswith("conjecture-call:"):
                backref[int(i.split(":", 1)[1])].append(e["seq"])

    rows: list[dict] = []
    agree = disagree = 0
    ambiguous_joins = 0
    cum = 0
    for e in events:
        llm = e.get("llm")
        if not llm:
            continue
        control = e.get("control") or {}
        refs = set(control.get("inputs") or []) | set(control.get("outputs") or [])
        if control.get("decision_ref"):
            refs.add(control["decision_ref"])
        matched = [r for r in refs if r in attempts]
        if len(matched) != 1:
            ambiguous_joins += 1
            attempt = None
        else:
            attempt = attempts[matched[0]]

        trace = (llm.get("attempt_trace") or [{}])[0]
        contract = trace.get("contract_id") or "?"
        purpose, detail = PURPOSE.get(contract, ("unclassified", contract))
        repair_scope = trace.get("repair_scope") or ""

        total = llm.get("tokens") or 0
        cum += total
        if attempt is not None:
            prompt_t = attempt.get("prompt_tokens")
            compl_t = attempt.get("completion_tokens")
            usage = attempt.get("usage_status")
            key = (attempt["work_id"], attempt["attempt_index"])
        else:
            prompt_t, compl_t, usage, key = llm.get("prompt_tokens"), llm.get("completion_tokens"), None, None
        term = terminals.get(key) if key else None
        adm = admissions.get(key) if key else None

        # the downstream window: artifacts this call's admitted output created
        lo, hi = e["seq"], next_call[e["seq"]]
        created: list[str] = []
        for s in range(lo + 1, hi if hi is not None else (events[-1]["seq"] + 1)):
            ev = by_seq.get(s)
            if ev is None:
                continue
            created.extend(ev["state_diff"].get("A+") or [])
        if backref.get(e["seq"]):
            if all(lo < s < (hi if hi is not None else 10 ** 12) for s in backref[e["seq"]]):
                agree += 1
            else:
                disagree += 1

        fates = Counter(status.get(a, "unknown") for a in created) if status is not None else None
        rows.append({
            "root": root,
            "seq": e["seq"],
            "ts": e["ts"],
            "cycle": assign_cycle(marks, cum),
            "role": llm.get("role"),
            "seat": trace.get("seat"),
            "model": llm.get("model"),
            "endpoint_id": trace.get("endpoint_id"),
            "contract_id": contract,
            "purpose": purpose,
            "purpose_detail": detail,
            "call_kind": "repair" if repair_scope else "first-ask",
            "repair_scope": repair_scope,
            "validation_path": trace.get("validation_path") or "",
            "arrival_valid": trace.get("valid"),
            "truncated": bool(llm.get("truncated")),
            "natural_stop": trace.get("natural_stop"),
            "max_tokens": trace.get("max_tokens"),
            "split_leg": trace.get("split_leg", None),
            "split_notice": trace.get("split_notice", None),
            "split_max_tokens": trace.get("split_max_tokens", None),
            "prompt_tokens": prompt_t,
            "completion_tokens": compl_t,
            "total_tokens": total,
            "cumulative_tokens": cum,
            "usage_status": usage,
            "ms": llm.get("ms"),
            "work_id": key[0] if key else None,
            "attempt_index": key[1] if key else None,
            "terminal_status": (term or {}).get("status"),
            "terminal_reason_code": (term or {}).get("reason_code"),
            "outcome": OUTCOME.get((term or {}).get("status"), "no-terminal-record"),
            "admission_outcome": (adm or {}).get("outcome"),
            "artifacts_created": len(created),
            "artifact_fates": dict(fates) if fates is not None else None,
        })

    # work terminals that never reached a provider call at all
    called = {(r["work_id"], r["attempt_index"]) for r in rows if r["work_id"]}
    uncalled = Counter(
        t["reason_code"] for k, t in terminals.items() if k not in called
    )
    return {
        "rows": rows,
        "ambiguous_joins": ambiguous_joins,
        "window_backref_agreement": {"agree": agree, "disagree": disagree},
        "replay_available": status is not None,
        "terminals_without_provider_call": dict(uncalled),
        "cycle_marks": marks,
    }


def reconcile(root: str, rows: list[dict]) -> dict:
    """The three token instruments, side by side, with the residual named.

    run-status.json's `token_spend`, TOKEN_ACCOUNTING.json's
    `inquiry_provider_tokens`, and the sum over log.jsonl are three
    independent statements about one quantity.  Where they disagree the
    residual is attributed to the contracts the accounting counter does not
    cover, so the disagreement is explained rather than merely reported.
    """
    abs_root = os.path.join(REPO, root)
    st = json.load(open(os.path.join(abs_root, "run-status.json")))
    ta_path = os.path.join(abs_root, "TOKEN_ACCOUNTING.json")
    ta = json.load(open(ta_path)) if os.path.exists(ta_path) else None
    log_total = sum(r["total_tokens"] for r in rows)
    acct = (ta or {}).get("inquiry_provider_tokens")
    acct_calls = (ta or {}).get("inquiry_provider_calls")

    by_purpose = Counter()
    for r in rows:
        by_purpose[r["purpose"]] += r["total_tokens"]
    # the report purpose is the post-terminal composition pass; it is the
    # usual residual, so it is named explicitly rather than inferred
    report_tokens = by_purpose.get("report", 0)
    residual = None if acct is None else log_total - acct
    return {
        "root": root,
        "state": st.get("state"),
        "stop_reason": st.get("stop_reason"),
        "token_limit": st.get("token_limit"),
        "run_status_token_spend": st.get("token_spend"),
        "accounting_inquiry_provider_tokens": acct,
        "accounting_inquiry_provider_calls": acct_calls,
        "accounting_bridge_provider_calls": (ta or {}).get("bridge_provider_calls"),
        "log_total_tokens": log_total,
        "log_calls": len(rows),
        "residual_log_minus_accounting": residual,
        "report_purpose_tokens": report_tokens,
        "report_purpose_calls": sum(1 for r in rows if r["purpose"] == "report"),
        "residual_explained_by_report_purpose": (
            None if residual is None else residual == report_tokens
        ),
        "status_spend_agrees_with_log": st.get("token_spend") == log_total,
        "status_spend_agrees_with_accounting": st.get("token_spend") == acct,
    }


def fate_class(row: dict) -> str:
    """What this call's tokens bought, in one phrase.

    The distinction between the last three classes is the whole point: a
    judge ruling that creates no artifact did its job, a rejected conjecture
    that creates no artifact did not, and a decomposition leg that creates
    no artifact is banking its work in a sibling leg.
    """
    fates = row["artifact_fates"]
    if fates is None:
        return "replay-unavailable"
    if fates:
        if fates.get("accepted"):
            return "bought-an-artifact-that-ended-accepted"
        return "bought-an-artifact-that-ended-refuted-or-suspended"
    if row["outcome"] != "admitted":
        return "bought-nothing-output-rejected-or-discarded"
    if row["contract_id"] not in ARTIFACT_PRODUCING:
        return "bought-nothing-contract-produces-no-artifact"
    return "bought-nothing-in-window-admitted-artifact-producing-contract"


def rollup(rows: list[dict], keys: tuple[str, ...]) -> dict:
    agg: dict[str, dict] = {}
    for r in rows:
        k = " | ".join(str(r[x]) for x in keys)
        a = agg.setdefault(k, {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0,
                               "total_tokens": 0, "prompt_tokens_known": 0})
        a["calls"] += 1
        a["total_tokens"] += r["total_tokens"]
        if r["prompt_tokens"] is not None:
            a["prompt_tokens"] += r["prompt_tokens"]
            a["completion_tokens"] += r["completion_tokens"] or 0
            a["prompt_tokens_known"] += 1
    for a in agg.values():
        a["prompt_share"] = (
            round(a["prompt_tokens"] / a["total_tokens"], 4) if a["total_tokens"] else None
        )
        a["mean_total_per_call"] = round(a["total_tokens"] / a["calls"], 1)
    return dict(sorted(agg.items(), key=lambda kv: -kv[1]["total_tokens"]))


def main() -> int:
    inv = json.load(open(os.path.join(PROGRAM, "ROOT_INVENTORY.json")))
    all_rows: list[dict] = []
    per_root: dict[str, dict] = {}
    recon: list[dict] = []
    for r in inv["roots"]:
        root = r["root"]
        print(f"  {root}", file=sys.stderr)
        scanned = scan_root(root)
        rows = scanned.pop("rows")
        for row in rows:
            row["fate_class"] = fate_class(row)
        all_rows.extend(rows)
        recon.append(reconcile(root, rows))
        per_root[root] = {
            **scanned,
            "run_id": r.get("run_id"),
            "state": r.get("state"),
            "stop_reason": r.get("stop_reason"),
            "calls": len(rows),
            "total_tokens": sum(x["total_tokens"] for x in rows),
            "by_purpose": rollup(rows, ("purpose",)),
            "by_outcome": rollup(rows, ("outcome",)),
            "by_call_kind": rollup(rows, ("call_kind",)),
            "by_fate_class": rollup(rows, ("fate_class",)),
        }

    with open(os.path.join(HERE, "FLOW_CALLS.jsonl"), "w") as fh:
        for row in all_rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    fate_tokens = Counter()
    for row in all_rows:
        f = row["artifact_fates"]
        if f is None:
            fate_tokens["replay-unavailable"] += row["total_tokens"]
        elif not f:
            fate_tokens["no-artifact-created"] += row["total_tokens"]
        else:
            # a call whose window created artifacts of several fates is
            # counted once per fate present, and the token total is split
            # in proportion to the artifact counts -- stated so the number
            # is reproducible, not because proportionality is meaningful
            n = sum(f.values())
            for k, v in f.items():
                fate_tokens[k] += row["total_tokens"] * v // n

    doc = {
        "schema": "run-anatomy.w6.token-flow-aggregate.v1",
        "regenerate": "python3 flow.py",
        "roots": len(per_root),
        "calls": len(all_rows),
        "total_tokens": sum(r["total_tokens"] for r in all_rows),
        "total_prompt_tokens": sum(r["prompt_tokens"] or 0 for r in all_rows),
        "total_completion_tokens": sum(r["completion_tokens"] or 0 for r in all_rows),
        "program_by_purpose": rollup(all_rows, ("purpose",)),
        "program_by_purpose_detail": rollup(all_rows, ("purpose", "purpose_detail")),
        "program_by_contract": rollup(all_rows, ("contract_id",)),
        "program_by_role_seat": rollup(all_rows, ("role", "seat")),
        "program_by_model": rollup(all_rows, ("model",)),
        "program_by_outcome": rollup(all_rows, ("outcome",)),
        "program_by_outcome_reason": rollup(all_rows, ("outcome", "terminal_reason_code")),
        "program_by_call_kind": rollup(all_rows, ("call_kind",)),
        "program_tokens_by_artifact_fate": dict(fate_tokens.most_common()),
        "program_by_fate_class": rollup(all_rows, ("fate_class",)),
        "program_by_fate_class_and_purpose": rollup(all_rows, ("fate_class", "purpose_detail")),
        "split_budget": {
            "attempts_carrying_split_fields": sum(
                1 for r in all_rows if r["split_leg"] is not None
            ),
            "attempts_with_non_empty_split_leg": sum(
                1 for r in all_rows if r["split_leg"]
            ),
            "split_notices": dict(
                Counter(r["split_notice"] for r in all_rows if r["split_notice"])
            ),
            "roots_carrying_split_fields": sorted(
                {r["root"] for r in all_rows if r["split_leg"] is not None}
            ),
        },
        "per_root": per_root,
    }
    with open(os.path.join(HERE, "FLOW_AGGREGATE.json"), "w") as fh:
        json.dump(doc, fh, indent=1)
        fh.write("\n")
    with open(os.path.join(HERE, "METER_RECONCILIATION.json"), "w") as fh:
        json.dump({
            "schema": "run-anatomy.w6.meter-reconciliation.v1",
            "regenerate": "python3 flow.py",
            "roots": recon,
            "roots_where_status_disagrees_with_log": sum(
                1 for x in recon if not x["status_spend_agrees_with_log"]
            ),
            "roots_where_status_is_zero_but_log_is_not": sum(
                1 for x in recon if x["run_status_token_spend"] == 0 and x["log_total_tokens"]
            ),
            "roots_with_non_zero_residual": sum(
                1 for x in recon if x["residual_log_minus_accounting"]
            ),
            "roots_whose_residual_is_exactly_the_report_pass": sum(
                1 for x in recon if x["residual_explained_by_report_purpose"] and
                x["residual_log_minus_accounting"]
            ),
        }, fh, indent=1)
        fh.write("\n")

    print(f"{len(all_rows)} calls over {len(per_root)} roots, "
          f"{doc['total_tokens']} tokens "
          f"({doc['total_prompt_tokens']} prompt / {doc['total_completion_tokens']} completion)")
    unclassified = doc["program_by_purpose"].get("unclassified")
    if unclassified:
        print(f"WARNING: {unclassified['calls']} calls on unclassified contracts")
    amb = sum(v["ambiguous_joins"] for v in per_root.values())
    print(f"ambiguous provider-attempt joins: {amb} (must be 0)")
    ag = sum(v["window_backref_agreement"]["agree"] for v in per_root.values())
    dis = sum(v["window_backref_agreement"]["disagree"] for v in per_root.values())
    print(f"downstream-window vs conjecture-call backref: {ag} agree, {dis} disagree")
    return 1 if (amb or dis) else 0


if __name__ == "__main__":
    sys.exit(main())
