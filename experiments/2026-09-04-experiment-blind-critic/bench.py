#!/usr/bin/env python3
"""Put the same 120 targets to the critic under each of the four briefs.

One bench run root per (cell, target): the REAL `rules/crit.py::crit_argumentative`
against the REAL provider, so every call leaves the typed record the harness
always writes -- the filled form, the critic artifact or its absence, the
scrutiny Measure, any attack edge, and the endpoint's own usage. Nothing here
reads `att` to decide whether criticism happened; `att` is one measure's
numerator and nothing else (PREREG section 1).

No committed root is opened for writing and none is edited. Targets are
COPIES: the body from `SELECTION.json` (clean) or `DEFECT_KEY.json` (planted),
the provenance copied field for field from the source artifact, and the
history records written into the bench state under a prefix no shipped section
plugin reads.

Concurrency: the layout is selected through a process-wide environment
variable, so a cell is worked to completion before the next begins and the
three workers inside a cell all share that one constant value. Three
concurrent provider calls, never more.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import pathlib
import sys
import threading
import time
import traceback

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]

import cells  # noqa: E402  (registers the plugins and the four layouts)

MODEL = "glm-5.2"
BASE_URL = "https://ollama.com/v1"
MAX_TOKENS = 8192
TIMEOUT_S = 300
PACK_TOKEN_BUDGET = 4000
CONCURRENCY = 3

_write_lock = threading.Lock()


def _api_key() -> str:
    """Read at call time from the tranche's gitignored env file. Never logged,
    never written to any artifact, never placed in a process argument."""
    for line in (HERE / "env").read_text(encoding="utf-8").splitlines():
        if line.startswith("OLLAMA_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no OLLAMA_API_KEY in the tranche env file")


def _config():
    from deepreason.config import Config

    # observe_only in every cell: the operator asked about a CRITIC, and a
    # trial authority would put a judge ensemble between the critic and every
    # measure this tranche takes (SPEC A8).
    return Config(
        ARGUMENTATIVE_AUTHORITY="observe_only",
        JUDGE_SEATS_ENABLED=False,
        PACK_TOKEN_BUDGET=PACK_TOKEN_BUDGET,
    )


def _adapter(blobs, key):
    from deepreason.llm.adapter import LLMAdapter
    from deepreason.llm.endpoints import OpenAICompatEndpoint

    endpoint = OpenAICompatEndpoint(
        base_url=BASE_URL, model=MODEL, api_key=key,
        max_tokens=MAX_TOKENS, timeout_s=TIMEOUT_S, json_mode=True,
        provider="ollama",
    )
    return LLMAdapter({"argumentative_critic": endpoint}, blobs)


def _bodies():
    selection = json.loads((HERE / "SELECTION.json").read_text(encoding="utf-8"))
    key = json.loads((HERE / "DEFECT_KEY.json").read_text(encoding="utf-8"))
    planted = {pair["target_id"]: pair for pair in key["pairs"]}
    rows = []
    for row in selection["targets"]:
        pair = planted.get(row["target_id"])
        body = pair["planted"] if pair else row["body"]
        assert (pair is not None) == (row["arm"] == "planted")
        rows.append({
            "target_id": row["target_id"],
            "arm": row["arm"],
            "artifact_id": row["artifact_id"],
            "source_root": row["source_root"],
            "school": row["school"],
            "role": row["role"],
            "defect_class": pair["defect_class"] if pair else None,
            "body": body,
            "history": row["history"],
        })
    return rows


def _seed(root: pathlib.Path, row: dict):
    """A bench harness holding one target and its recorded criticism history.

    The history artifacts are critic-role records carrying no warrants, which
    is what an unanswered objection already is in the record; they are NOT
    wired into `att`, because none of them landed and an edge would assert
    that one had.
    """
    from deepreason.harness import Harness
    from deepreason.ontology import Provenance

    harness = Harness(root)
    target = harness.create_artifact(
        json.dumps(row["body"], ensure_ascii=False, sort_keys=True),
        provenance=Provenance(role=row["role"], school=row["school"]),
    )
    for record in row["history"]:
        harness.create_artifact(
            cells.HISTORY_PREFIX + json.dumps({
                "target": target.id,
                "seq": record["seq"],
                "objection": record["objection"],
                "outcome": (
                    "raised and LANDED; the target was refuted on it"
                    if record["landed"] else
                    "raised and not answered; the target's status did not move"
                ),
            }, ensure_ascii=False),
            provenance=Provenance(role="critic"),
        )
    return harness, target.id


def _one_call(cell: str, row: dict, key: str, out_root: pathlib.Path) -> dict:
    from deepreason.llm.packs import render_crit_pack
    from deepreason.rules.crit import crit_argumentative

    started = time.time()
    record = {
        "cell": cell, "target_id": row["target_id"], "arm": row["arm"],
        "artifact_id": row["artifact_id"], "school": row["school"],
        "defect_class": row["defect_class"], "history_rows": len(row["history"]),
    }
    root = out_root / cell / row["target_id"]
    try:
        harness, target_id = _seed(root, row)
        config = _config()
        adapter = _adapter(harness.blobs, key)
        endpoint = adapter.endpoints["argumentative_critic"]

        # The pack the seat actually receives, captured before the call so a
        # failed call still leaves the brief it was given.
        record["pack"] = render_crit_pack(
            target_id, harness.state, harness.commitments, harness.blobs,
            token_budget=PACK_TOKEN_BUDGET,
        )
        record["bench_artifact_id"] = target_id

        before_att = set(harness.state.att)
        critic = crit_argumentative(harness, target_id, adapter, config)

        record["att_edges_minted"] = len(set(harness.state.att) - before_att)
        record["critic_artifact"] = None if critic is None else critic.id
        record["usage"] = endpoint.last_usage
        record["finish_reason"] = endpoint.last_finish_reason
        record["scrutiny_events"] = sum(
            1 for line in (root / "log.jsonl").open(encoding="utf-8")
            if '"scrutiny"' in line
        )
        # The filled form, recovered from the record rather than from the
        # object the call returned: a non-attacking reply returns None, and
        # its `attack=false` is exactly what M2 needs.
        record.update(_recover_form(harness, root))
        record["ok"] = True
    except Exception as error:  # noqa: BLE001 - a failed call is data
        record["ok"] = False
        record["error"] = f"{type(error).__name__}: {error}"
        record["traceback"] = traceback.format_exc()[-2000:]
    record["seconds"] = round(time.time() - started, 2)
    return record


def _recover_form(harness, root: pathlib.Path) -> dict:
    """The critic's own filled form, read back out of the run's own record.

    R17: every criticism ATTEMPT, from the typed object the record holds per
    call -- not from `att`, which holds only the attacks that landed and is
    why the previous attempt at this question could not discriminate. The
    object is the `raw_ref` blob each `attempt_trace` entry names, so a call
    whose reply was `attack=false` -- which registers no artifact and returns
    None -- is just as readable as one that attacked. That is the whole
    denominator M2 needs.
    """
    from deepreason.llm.adapter import _extract_json

    attempts = []
    for line in (root / "log.jsonl").open(encoding="utf-8"):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        block = event.get("llm")
        if not isinstance(block, dict) or block.get("role") != "argumentative_critic":
            continue
        trace = block.get("attempt_trace") or [{"raw_ref": block.get("raw_ref")}]
        for entry in trace:
            raw = harness.blobs.get(entry.get("raw_ref") or "")
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", "replace")
            if not raw:
                continue
            # The harness's OWN normaliser, not a hand-rolled one: a reply
            # arrives fenced in a markdown code block often enough that a
            # measurement parsing it differently from the adapter would be
            # measuring a different object than the run acted on.
            try:
                payload = json.loads(_extract_json(raw))
            except Exception:  # noqa: BLE001 - an unparseable reply is data
                attempts.append({"unparseable": True, "raw": raw[:4000]})
                continue
            if isinstance(payload, dict) and "attack" in payload:
                attempts.append({
                    "attack": bool(payload.get("attack")),
                    "case": str(payload.get("case") or ""),
                    "successor_question": payload.get("successor_question"),
                })
    usable = [a for a in attempts if "attack" in a]
    last = usable[-1] if usable else {}
    return {
        "attempts": len(attempts),
        "form_attack": last.get("attack"),
        "form_case": last.get("case", ""),
        "form_successor_question": last.get("successor_question"),
    }


def run(rows, cells_to_run, out_root: pathlib.Path, calls_path: pathlib.Path) -> int:
    key = _api_key()
    layouts = cells.register()
    done = failed = 0
    calls_path.parent.mkdir(parents=True, exist_ok=True)
    with calls_path.open("a", encoding="utf-8") as sink:
        for cell in cells_to_run:
            # Set once per cell: `resolve_seat_pack_layout` reads the
            # environment per call, so the value must be constant for every
            # worker inside a cell.
            cells.select(cell, layouts)
            print(f"[bench] cell {cell} -> {layouts[cell]}  ({len(rows)} targets)",
                  flush=True)
            with concurrent.futures.ThreadPoolExecutor(CONCURRENCY) as pool:
                futures = [pool.submit(_one_call, cell, row, key, out_root)
                           for row in rows]
                for future in concurrent.futures.as_completed(futures):
                    record = future.result()
                    done += 1
                    failed += not record["ok"]
                    with _write_lock:
                        sink.write(json.dumps(record, ensure_ascii=False) + "\n")
                        sink.flush()
                    if done % 20 == 0 or not record["ok"]:
                        print(f"[bench] {done} calls, {failed} failed"
                              f"  last={record['cell']}/{record['target_id']}"
                              f" ok={record['ok']}", flush=True)
    os.environ.pop("DEEPREASON_SEAT_PACK_LAYOUT", None)
    print(f"[bench] complete: {done} calls, {failed} failed", flush=True)
    return failed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true",
                    help="one target through all four cells")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    rows = _bodies()
    assert len(rows) == 120, len(rows)

    if args.smoke:
        out = pathlib.Path(args.out or "/tmp/blind-critic-smoke")
        calls = out / "calls.jsonl"
        if calls.exists():
            calls.unlink()
        failed = run(rows[:1], cells.CELL_IDS, out, calls)
        parsed = sum(
            1 for line in calls.open(encoding="utf-8")
            if json.loads(line).get("form_attack") is not None
        )
        print(f"smoke: {parsed}/4 parsed")
        return 0 if (parsed == 4 and failed == 0) else 1

    out = pathlib.Path(args.out or (HERE / "raw" / "roots"))
    return run(rows, cells.CELL_IDS, out, HERE / "raw" / "calls.jsonl")


if __name__ == "__main__":
    sys.exit(main())
