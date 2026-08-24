#!/usr/bin/env python3
"""swarm_gate.py -- coordination gate for LLM agent swarms working a git repo.

Stdlib only. Drop into scripts/ and commit it; every agent sandbox that can
run git can run the gate. State lives in .swarm/ (board.json, map.md,
log.jsonl with a hash chain). The gate REFUSES bad transitions with a fixed
vocabulary; agents are instructed to obey refusals, never work around them.

Refusal codes (first line of output, exit 1):
  REFUSED_BRIEF_INCOMPLETE  REFUSED_WIP_LIMIT      REFUSED_CONE_OVERLAP
  REFUSED_MAP_STALE         REFUSED_BASE_UNKNOWN   REFUSED_SHA_UNKNOWN
  REFUSED_CONE_VIOLATION    REFUSED_NOT_COMMITTED  REFUSED_NOT_ON_REMOTE
  REFUSED_BAD_TRANSITION    REFUSED_TASK_UNKNOWN   REFUSED_LOCK_TIMEOUT
Warnings (non-fatal, printed as WARN_*): WARN_CONE_MATCHES_NOTHING,
WARN_DIRTY_TREE, WARN_BASE_BEHIND.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

SWARM_DIR = ".swarm"
BRIEF_FIELDS = ["goal", "cone", "base", "accept", "out_of_scope"]
STATES = ["DRAFT", "READY", "CLAIMED", "COMMITTED", "IN_REVIEW", "DONE", "BLOCKED"]
GENESIS = "0" * 64


# ----------------------------------------------------------------- plumbing
def git(root: Path, *args: str, check: bool = True) -> str:
    r = subprocess.run(["git", "-C", str(root), *args],
                       capture_output=True, text=True)
    if check and r.returncode != 0:
        die(2, f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def die(code: int, msg: str) -> None:
    print(msg)
    sys.exit(code)


def refuse(code: str, msg: str):
    if JSON_MODE:
        print(json.dumps({"ok": False, "refusal": code, "msg": msg}))
    else:
        print(code)
        print(msg)
    sys.exit(1)


class Lock:
    def __init__(self, root: Path):
        self.p = root / SWARM_DIR / ".lock"

    def __enter__(self):
        for _ in range(40):
            try:
                fd = os.open(self.p, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                return self
            except FileExistsError:
                time.sleep(0.25)
        refuse("REFUSED_LOCK_TIMEOUT", f"{self.p} held; retry or remove if stale")

    def __exit__(self, *a):
        try:
            self.p.unlink()
        except FileNotFoundError:
            pass


def board_path(root: Path) -> Path:
    return root / SWARM_DIR / "board.json"


TASK_DEFAULTS = {"state": "DRAFT", "goal": "", "cone": [], "base": "",
                 "accept": "", "verify": "", "out_of_scope": "",
                 "depends_on": [], "worker": "", "reviewer": "",
                 "shas": [], "notes": [], "reads": [], "claim_token": 0,
                 "state_ts": 0.0}

JSON_MODE = False
GATE_VERSION = "0.4.1"
SCHEMA_VERSION = 3


def _sha_file(root: Path, rel: str) -> str:
    p = root / rel
    if not p.exists():
        return "MISSING"
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _check_protocol(board: dict) -> None:
    proto = board.get("config", {}).get("protocol", 1)
    if proto > SCHEMA_VERSION:
        refuse("REFUSED_PROTOCOL_MISMATCH",
               f"board protocol {proto} > this gate's schema {SCHEMA_VERSION}; "
               "upgrade the gate before touching this board")


def load_board(root: Path) -> dict:
    p = board_path(root)
    if not p.exists():
        die(2, f"no {p}; run: swarm_gate.py init")
    board = json.loads(p.read_text(encoding="utf-8"))
    # defect #6: schema defaults for hand-written or older entries --
    # a missing optional key must never crash a gate command
    _check_protocol(board)
    for t in board.get("tasks", {}).values():
        for k, v in TASK_DEFAULTS.items():
            t.setdefault(k, list(v) if isinstance(v, list) else v)
    return board


def save_board(root: Path, board: dict) -> None:
    board_path(root).write_text(json.dumps(board, indent=2, sort_keys=True) + "\n",
                                encoding="utf-8")


def log_append(root: Path, action: str, task: str, actor: str, detail: dict) -> None:
    p = root / SWARM_DIR / "log.jsonl"
    prev = GENESIS
    if p.exists():
        last = None
        with p.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    last = line.rstrip("\n")
        if last:
            prev = hashlib.sha256(last.encode()).hexdigest()
    rec = {"gate_v": GATE_VERSION, "schema": SCHEMA_VERSION, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "action": action, "task": task, "actor": actor,
           "detail": detail, "prev": prev}
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, sort_keys=True, separators=(",", ":")) + "\n")


def log_verify(root: Path) -> tuple[bool, str]:
    p = root / SWARM_DIR / "log.jsonl"
    if not p.exists():
        return True, "empty log"
    prev = GENESIS
    with p.open(encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.rstrip("\n")
            if not line.strip():
                continue
            if json.loads(line).get("prev") != prev:
                return False, f"chain broken at line {n}"
            prev = hashlib.sha256(line.encode()).hexdigest()
    return True, "chain intact"


# ----------------------------------------------------------------- repo map
def tree_sha(root: Path) -> str:
    return git(root, "rev-parse", "HEAD^{tree}")


def build_map(root: Path) -> str:
    files = git(root, "ls-files").split("\n")
    dirs: dict[str, int] = {}
    for f in files:
        parts = f.split("/")
        for depth in (1, 2):
            if len(parts) > depth:
                dirs["/".join(parts[:depth]) + "/"] = dirs.get("/".join(parts[:depth]) + "/", 0) + 1
    lines = [
        "# Repo map (generated -- do not edit; regenerate with: swarm_gate.py map)",
        f"branch: {git(root, 'rev-parse', '--abbrev-ref', 'HEAD')}",
        f"head: {git(root, 'rev-parse', 'HEAD')}",
        f"tree_sha: {tree_sha(root)}",
        f"tracked_files: {len(files)}",
        "",
        "## Directories",
    ]
    lines += [f"- `{d}` -- {n} files" for d, n in sorted(dirs.items())]
    lines += ["", "## Key documents (tracked .md, first heading)"]
    count = 0
    for f in sorted(files):
        if not f.endswith(".md") or count >= 80:
            continue
        try:
            for ln in (root / f).read_text(encoding="utf-8", errors="replace").split("\n")[:5]:
                if ln.startswith("# "):
                    lines.append(f"- `{f}` -- {ln[2:].strip()[:90]}")
                    count += 1
                    break
        except OSError:
            pass
    return "\n".join(lines) + "\n"


def map_stale(root: Path) -> bool:
    mp = root / SWARM_DIR / "map.md"
    if not mp.exists():
        return True
    for ln in mp.read_text(encoding="utf-8").split("\n")[:6]:
        if ln.startswith("tree_sha: "):
            return ln.split(": ", 1)[1].strip() != tree_sha(root)
    return True


# ----------------------------------------------------------------- cones
def cone_files(root: Path, cone: list[str]) -> list[str]:
    files = git(root, "ls-files").split("\n")
    return sorted({f for f in files for pat in cone if fnmatch.fnmatch(f, pat)})


def cones_overlap(root: Path, a: list[str], b: list[str]) -> list[str]:
    fa, fb = set(cone_files(root, a)), set(cone_files(root, b))
    hits = sorted(fa & fb)
    hits += sorted(set(a) & set(b) - set(hits))  # identical patterns (incl. not-yet-existing)
    return hits


def in_cone(path: str, cone: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pat) for pat in cone)


# ----------------------------------------------------------------- commands
def cmd_init(root: Path, a) -> None:
    d = root / SWARM_DIR
    d.mkdir(exist_ok=True)
    if not board_path(root).exists():
        save_board(root, {"config": {"wip_limit": a.wip_limit, "protocol": SCHEMA_VERSION,
                                     "require_remote": "auto"},
                          "tasks": {}})
    (d / "map.md").write_text(build_map(root), encoding="utf-8")
    log_append(root, "init", "-", a.actor, {"wip_limit": a.wip_limit})
    print(f"initialized {d} (wip_limit={a.wip_limit})")


def cmd_map(root: Path, a) -> None:
    if a.check:
        if map_stale(root):
            refuse("REFUSED_MAP_STALE",
                   "map.md does not match HEAD tree; run: swarm_gate.py map "
                   "then read .swarm/map.md before dispatching")
        print("map fresh")
        return
    (root / SWARM_DIR / "map.md").write_text(build_map(root), encoding="utf-8")
    log_append(root, "map", "-", a.actor, {"tree_sha": tree_sha(root)})
    print(f"map regenerated -> {SWARM_DIR}/map.md")


def cmd_add(root: Path, a) -> None:
    with Lock(root):
        board = load_board(root)
        if a.id in board["tasks"]:
            refuse("REFUSED_BAD_TRANSITION", f"task {a.id} already exists")
        board["tasks"][a.id] = {
            "state": "DRAFT", "goal": a.goal or "", "cone": a.cone or [],
            "base": a.base or "", "accept": a.accept or "",
            "out_of_scope": a.out_of_scope or "", "depends_on": a.depends_on or [],
            "worker": "", "reviewer": "", "shas": [], "notes": [],
            "state_ts": time.time(),
        }
        save_board(root, board)
        log_append(root, "add", a.id, a.actor, {"goal": a.goal})
    print(f"added {a.id} (DRAFT)")


def _brief_missing(t: dict) -> list[str]:
    return [f for f in BRIEF_FIELDS if not t.get(f)]


def cmd_rebuild(root: Path, a) -> None:
    """rebuild --check: replay the log's determinable projection (states,
    workers, shas, claim tokens) into a fresh board and compare with
    board.json. Two representations existing separately is the corruption
    detector; this computes the comparison. Undetermined fields are listed
    NOT_CHECKED. Replay across a schema version boundary is refused."""
    if not a.check:
        die(2, "only rebuild --check is supported; the board is operating state, not a cache")
    board = load_board(root)
    lp = root / SWARM_DIR / "log.jsonl"
    events = [json.loads(l) for l in lp.read_text(encoding="utf-8").splitlines() if l.strip()]
    schemas = {e.get("schema", 1) for e in events}
    if len(schemas) > 1:
        refuse("REFUSED_REPLAY_DIVERGENT",
               f"log spans schema versions {sorted(schemas)}; replay across a "
               "schema change is refused -- migrate explicitly (owner decision)")
    exc_p = root / SWARM_DIR / "rebuild-exceptions.json"
    exceptions = json.loads(exc_p.read_text()) if exc_p.exists() else {}
    proj = {}
    for e in events:
        tid = e.get("task")
        if not tid or tid == "-":
            continue
        t = proj.setdefault(tid, {"state": "DRAFT", "worker": "", "shas": [], "claim_token": 0})
        act, d = e.get("action"), e.get("detail", {}) or {}
        if act == "ready":
            t["state"] = "READY"
        elif act == "edit":
            t["state"] = "DRAFT"
        elif act == "claim":
            t["state"] = "CLAIMED"; t["worker"] = d.get("worker", t["worker"]); t["claim_token"] += 1
        elif act == "done":
            t["state"] = "COMMITTED"
            sha = d.get("shas", d.get("sha"))
            if isinstance(sha, list):
                t["shas"] += sha
            elif sha:
                t["shas"].append(sha)
        elif act == "verdict":
            t["state"] = "DONE" if d.get("result") == "PASS" else "READY"
        elif act == "requeue":
            t["state"] = "READY"
    diffs = []
    for tid, why in exceptions.items():
        print(f"EXCEPTED {tid}: {why} (disclosed; not compared)")
    proj = {k: v for k, v in proj.items() if k not in exceptions}
    for tid, p in proj.items():
        b = board["tasks"].get(tid)
        if b is None:
            diffs.append(f"{tid}: in log, absent from board"); continue
        if b["state"] != p["state"]:
            diffs.append(f"{tid}: state board={b['state']} replay={p['state']}")
        if int(b.get("claim_token", 0)) != p["claim_token"]:
            diffs.append(f"{tid}: claim_token board={b.get('claim_token')} replay={p['claim_token']}")
    for tid in board["tasks"]:
        if tid not in proj and tid not in exceptions:
            diffs.append(f"{tid}: on board, never in log")
    if diffs:
        refuse("REFUSED_REPLAY_DIVERGENT", "; ".join(diffs[:5]))
    print(f"rebuild --check: projection agrees ({len(proj)} task(s)); "
          "NOT_CHECKED by replay: goal/cone/accept/verify/base/notes bodies")


def cmd_note(root: Path, a) -> None:
    """Append a note to a task in ANY state (including DONE) through the
    gate — closes the out-of-band board edit that annotating finished
    work used to require. Notes are append-only and logged."""
    with Lock(root):
        board = load_board(root)
        t = board["tasks"].get(a.id) or refuse("REFUSED_TASK_UNKNOWN", a.id)
        if a.amend_index is not None:
            i = int(a.amend_index)
            if not (0 <= i < len(t["notes"])):
                refuse("REFUSED_BAD_TRANSITION", f"no note at index {i} to amend")
            old = t["notes"][i]
            t["notes"][i] = {"by": a.actor, "ts": time.time(), "note": a.note,
                             "amends": old}
            save_board(root, board)
            log_append(root, "note-amend", a.id, a.actor,
                       {"index": i, "old": old, "new": a.note})
        else:
            t["notes"].append({"by": a.actor, "ts": time.time(), "note": a.note})
            save_board(root, board)
            log_append(root, "note", a.id, a.actor, {"note": a.note})
    print(f"{a.id}: note appended")


def cmd_edit(root: Path, a) -> None:
    """Defect #7: brief repair through the gate, never by hand-editing
    board.json. Allowed only before work starts (DRAFT/READY/BLOCKED);
    any edit drops the task to DRAFT so `ready` re-validates."""
    with Lock(root):
        board = load_board(root)
        t = board["tasks"].get(a.id) or refuse("REFUSED_TASK_UNKNOWN", a.id)
        if t["state"] not in ("DRAFT", "READY", "BLOCKED"):
            refuse("REFUSED_BAD_TRANSITION",
                   f"{a.id} is {t['state']}; briefs are frozen once claimed -- requeue first")
        changed = {}
        for field in ("goal", "base", "accept", "verify"):
            v = getattr(a, field, None)
            if v is not None:
                t[field] = v; changed[field] = v
        if a.out_of_scope is not None:
            t["out_of_scope"] = a.out_of_scope; changed["out_of_scope"] = a.out_of_scope
        if a.cone:
            t["cone"] = a.cone; changed["cone"] = a.cone
        if a.depends_on is not None:
            t["depends_on"] = a.depends_on; changed["depends_on"] = a.depends_on
        if not changed:
            refuse("REFUSED_BAD_TRANSITION", "edit called with nothing to change")
        t["state"], t["state_ts"] = "DRAFT", time.time()
        save_board(root, board)
        log_append(root, "edit", a.id, a.actor, changed)
    print(f"{a.id} edited -> DRAFT (re-run: ready {a.id})")


def cmd_ready(root: Path, a) -> None:
    with Lock(root):
        board = load_board(root)
        t = board["tasks"].get(a.id) or refuse("REFUSED_TASK_UNKNOWN", a.id)
        missing = _brief_missing(t)
        if missing:
            refuse("REFUSED_BRIEF_INCOMPLETE",
                   f"task {a.id} missing brief fields: {', '.join(missing)}. "
                   "If you cannot fill them, you do not yet understand the task "
                   "well enough to delegate it.")
        if not git(root, "cat-file", "-e", f"{t['base']}^{{commit}}", check=False) == "" \
                and subprocess.run(["git", "-C", str(root), "cat-file", "-e",
                                    f"{t['base']}^{{commit}}"]).returncode != 0:
            refuse("REFUSED_BASE_UNKNOWN", f"base {t['base']} is not a commit here")
        matched = cone_files(root, t["cone"])
        if not matched:
            print(f"WARN_CONE_MATCHES_NOTHING cone {t['cone']} matches no tracked file "
                  "(fine only if the task creates new files; check the paths against .swarm/map.md)")
        t["state"], t["state_ts"] = "READY", time.time()
        save_board(root, board)
        log_append(root, "ready", a.id, a.actor, {"cone": t["cone"], "matched": len(matched)})
    print(f"{a.id} READY ({len(matched)} tracked files in cone)")


def cmd_claim(root: Path, a) -> None:
    if map_stale(root):
        refuse("REFUSED_MAP_STALE",
               "repo map is stale; run: swarm_gate.py map, read .swarm/map.md, retry")
    with Lock(root):
        board = load_board(root)
        t = board["tasks"].get(a.id) or refuse("REFUSED_TASK_UNKNOWN", a.id)
        if t["state"] != "READY":
            refuse("REFUSED_BAD_TRANSITION", f"{a.id} is {t['state']}, not READY")
        active = {k: v for k, v in board["tasks"].items()
                  if v["state"] in ("CLAIMED", "COMMITTED", "IN_REVIEW") and k != a.id}
        limit = board["config"]["wip_limit"]
        if len(active) >= limit:
            refuse("REFUSED_WIP_LIMIT",
                   f"{len(active)} tasks in flight (limit {limit}): "
                   f"{', '.join(sorted(active))}. Finish or requeue one first; "
                   "prefer sequential dispatch.")
        for k, v in active.items():
            hits = cones_overlap(root, t["cone"], v["cone"])
            if hits:
                refuse("REFUSED_CONE_OVERLAP",
                       f"cone overlaps active task {k} on: {', '.join(hits[:8])}. "
                       "Two writers on one file conflict; serialize these tasks.")
        for dep in t.get("depends_on", []):
            dt = board["tasks"].get(dep)
            if dt and dt["state"] != "DONE":
                refuse("REFUSED_BAD_TRANSITION",
                       f"dependency {dep} is {dt['state']}, not DONE")
        head = git(root, "rev-parse", "HEAD")
        if t["base"] not in (head, head[:len(t["base"])]) and \
                git(root, "merge-base", "--is-ancestor", t["base"], "HEAD", check=False) == "" and \
                subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor",
                                t["base"], "HEAD"]).returncode != 0:
            print(f"WARN_BASE_BEHIND base {t['base'][:12]} is not an ancestor of HEAD; "
                  "consider re-briefing on the current head")
        t["claim_token"] = int(t.get("claim_token", 0)) + 1
        t["reads"] = [[r, _sha_file(root, r)] for r in (a.reads or [])]
        t["state"], t["worker"], t["state_ts"] = "CLAIMED", a.worker, time.time()
        save_board(root, board)
        log_append(root, "claim", a.id, a.worker, {"cone": t["cone"]})
    print(f"{a.id} CLAIMED by {a.worker}; write-lease on: {', '.join(t['cone'])}")


def cmd_done(root: Path, a) -> None:
    with Lock(root):
        board = load_board(root)
        t = board["tasks"].get(a.id) or refuse("REFUSED_TASK_UNKNOWN", a.id)
        if t["state"] != "CLAIMED":
            refuse("REFUSED_BAD_TRANSITION", f"{a.id} is {t['state']}, not CLAIMED "
                   "(done is the WORKER's move; COMMITTED tasks close via review + verdict)")
        if a.token is not None and int(a.token) != int(t.get("claim_token", 0)):
            refuse("REFUSED_STALE_CLAIM_TOKEN",
                   f"{a.id}: presented token {a.token}, current {t.get('claim_token')} — "
                   "a newer claim owns this task; this writer's work must not land")
        stale = [(r, old, _sha_file(root, r)) for r, old in t.get("reads", [])
                 if _sha_file(root, r) != old]
        if stale:
            details = "; ".join(f"{r}: {o[:8]} -> {n[:8]}" for r, o, n in stale)
            refuse("REFUSED_READSET_STALE",
                   f"{a.id}: read-context changed since claim ({details}) — "
                   "the work was produced against stale reads; requeue and rerun")
        if not a.sha:
            refuse("REFUSED_NOT_COMMITTED",
                   "done requires --sha. A report without commit SHAs is a claim, "
                   "not evidence; commit (and push) first.")
        strays = []
        for sha in a.sha:
            if subprocess.run(["git", "-C", str(root), "cat-file", "-e",
                               f"{sha}^{{commit}}"]).returncode != 0:
                refuse("REFUSED_SHA_UNKNOWN", f"{sha} is not a commit in this repository")
            touched = git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", sha)
            strays += [f for f in touched.split("\n") if f and not in_cone(f, t["cone"])]
        if strays:
            refuse("REFUSED_CONE_VIOLATION",
                   f"commits touch files outside the cone: {', '.join(sorted(set(strays))[:8])}. "
                   "Revert the strays or request a cone change (requeue), never both-and-silence.")
        if git(root, "status", "--porcelain"):
            print("WARN_DIRTY_TREE working tree has uncommitted changes; "
                  "anything not committed is invisible to reviewers")
        t["state"], t["shas"], t["state_ts"] = "COMMITTED", list(a.sha), time.time()
        save_board(root, board)
        log_append(root, "done", a.id, a.actor, {"shas": list(a.sha)})
    print(f"{a.id} COMMITTED ({len(a.sha)} sha)")


def _remote_required(root: Path, board: dict) -> bool:
    cfg = board["config"].get("require_remote", "auto")
    if cfg == "auto":
        return bool(git(root, "remote", check=False))
    return bool(cfg)


def cmd_review(root: Path, a) -> None:
    board = load_board(root)
    t = board["tasks"].get(a.id) or refuse("REFUSED_TASK_UNKNOWN", a.id)
    if t["state"] not in ("COMMITTED", "IN_REVIEW"):
        refuse("REFUSED_NOT_COMMITTED",
               f"{a.id} is {t['state']}. Review only recorded commits; the working "
               "tree and un-pushed local work are not reviewable objects. "
               "Ask the worker to commit+push and run done.")
    if getattr(a, "local_ok", False):
        _require_owner(board, a)
    if _remote_required(root, board) and not getattr(a, "local_ok", False):
        git(root, "fetch", "-q", "--all", check=False)
        for sha in t["shas"]:
            if not git(root, "branch", "-r", "--contains", sha, check=False):
                refuse("REFUSED_NOT_ON_REMOTE",
                       f"{sha[:12]} is not on any remote branch; the worker has not "
                       "pushed. Do not review; report REVIEW_BLOCKED.")
    for sha in t["shas"]:
        if subprocess.run(["git", "-C", str(root), "cat-file", "-e",
                           f"{sha}^{{commit}}"]).returncode != 0:
            refuse("REFUSED_SHA_UNKNOWN", f"recorded sha {sha} not found; fetch or re-record")
    with Lock(root):
        board = load_board(root)
        board["tasks"][a.id]["state"] = "IN_REVIEW"
        board["tasks"][a.id]["reviewer"] = a.reviewer
        board["tasks"][a.id]["state_ts"] = time.time()
        save_board(root, board)
        log_append(root, "review", a.id, a.reviewer, {"shas": t["shas"]})
    print(f"{a.id} IN_REVIEW. Review exactly: git diff {t['base']}..{t['shas'][-1]} "
          f"(base {t['base'][:12]}); acceptance: {t['accept']}")


def _require_owner(board: dict, a) -> None:
    key = board.get("config", {}).get("owner_token_sha256")
    if not key:
        return
    tok = getattr(a, "owner_token", None) or ""
    if hashlib.sha256(tok.encode()).hexdigest() != key:
        refuse("REFUSED_OWNER_UNVERIFIED",
               "this action requires the owner token (board config "
               "owner_token_sha256 is set); attribution by flag is not authority")


def cmd_verdict(root: Path, a) -> None:
    with Lock(root):
        board = load_board(root)
        _require_owner(board, a)
        t = board["tasks"].get(a.id) or refuse("REFUSED_TASK_UNKNOWN", a.id)
        if t["state"] != "IN_REVIEW":
            refuse("REFUSED_BAD_TRANSITION", f"{a.id} is {t['state']}, not IN_REVIEW")
        t["state"] = "DONE" if a.result == "PASS" else "BLOCKED"
        t["notes"].append({"by": a.actor, "result": a.result, "note": a.note or ""})
        t["state_ts"] = time.time()
        save_board(root, board)
        log_append(root, "verdict", a.id, a.actor, {"result": a.result, "note": a.note})
    print(f"{a.id} -> {t['state']}")


def cmd_requeue(root: Path, a) -> None:
    with Lock(root):
        board = load_board(root)
        t = board["tasks"].get(a.id) or refuse("REFUSED_TASK_UNKNOWN", a.id)
        if t["state"] not in ("CLAIMED", "BLOCKED", "COMMITTED", "IN_REVIEW"):
            refuse("REFUSED_BAD_TRANSITION", f"{a.id} is {t['state']}")
        t["state"], t["worker"], t["state_ts"] = "READY" if not a.to_draft else "DRAFT", "", time.time()
        if a.note:
            t["notes"].append({"by": a.actor, "result": "REQUEUE", "note": a.note})
        save_board(root, board)
        log_append(root, "requeue", a.id, a.actor, {"note": a.note})
    print(f"{a.id} -> {t['state']}")


def cmd_board(root: Path, a) -> None:
    board = load_board(root)
    for k in sorted(board["tasks"]):
        t = board["tasks"][k]
        extra = f" worker={t['worker']}" if t["worker"] else ""
        extra += f" shas={[s[:8] for s in t['shas']]}" if t["shas"] else ""
        print(f"{k:12} {t['state']:10} cone={t['cone']}{extra}")
    print(f"(wip_limit={board['config']['wip_limit']})")


def cmd_verify(root: Path, a) -> None:
    board = load_board(root)
    findings = []

    def f(sev, note, quote=""):
        findings.append({"severity": sev, "note": note, "quote": quote})

    active = {k: v for k, v in board["tasks"].items()
              if v["state"] in ("CLAIMED", "COMMITTED", "IN_REVIEW")}
    keys = sorted(active)
    for i, k1 in enumerate(keys):
        for k2 in keys[i + 1:]:
            hits = cones_overlap(root, active[k1]["cone"], active[k2]["cone"])
            if hits:
                f("BLOCKER", f"active cone overlap {k1}/{k2}", ", ".join(hits[:6]))
    if len(active) > board["config"]["wip_limit"]:
        f("MAJOR", f"WIP {len(active)} exceeds limit {board['config']['wip_limit']}",
          ", ".join(keys))
    for k, t in board["tasks"].items():
        for sha in t.get("shas", []):
            if subprocess.run(["git", "-C", str(root), "cat-file", "-e",
                               f"{sha}^{{commit}}"]).returncode != 0:
                f("BLOCKER", f"{k} records unknown sha", sha)
        if t["state"] in ("CLAIMED", "IN_REVIEW") and \
                time.time() - t.get("state_ts", time.time()) > a.stale_hours * 3600:
            f("MINOR", f"{k} stuck in {t['state']} > {a.stale_hours}h", t.get("worker", ""))
    if map_stale(root):
        f("MAJOR", "repo map stale vs HEAD tree", "run swarm_gate.py map")
    ok, msg = log_verify(root)
    if not ok:
        f("BLOCKER", "coordination log hash chain broken", msg)
    for x in findings:
        print(json.dumps(x, sort_keys=True))
    if not findings:
        print("OK: board invariants hold")
    sys.exit(1 if any(x["severity"] in ("BLOCKER", "MAJOR") for x in findings) else 0)


def cmd_log_verify(root: Path, a) -> None:
    ok, msg = log_verify(root)
    print(msg)
    sys.exit(0 if ok else 1)


# ----------------------------------------------------------------- main
def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="swarm_gate.py")
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--actor", default=os.environ.get("SWARM_ACTOR") or None)
    p.add_argument("--json", action="store_true", help="machine-readable refusals")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init"); s.add_argument("--wip-limit", type=int, default=2)
    s = sub.add_parser("map"); s.add_argument("--check", action="store_true")
    s = sub.add_parser("add")
    s.add_argument("id"); s.add_argument("--goal"); s.add_argument("--cone", nargs="+")
    s.add_argument("--base"); s.add_argument("--accept"); s.add_argument("--verify")
    s.add_argument("--out-of-scope")
    s.add_argument("--depends-on", nargs="*")
    s = sub.add_parser("note"); s.add_argument("id"); s.add_argument("--note", required=True)
    s.add_argument("--amend-index", default=None, help="replace note at index; correction event logged atomically")
    s = sub.add_parser("edit")
    s.add_argument("id"); s.add_argument("--goal"); s.add_argument("--cone", nargs="+")
    s.add_argument("--base"); s.add_argument("--accept"); s.add_argument("--verify")
    s.add_argument("--out-of-scope")
    s.add_argument("--depends-on", nargs="*")
    s = sub.add_parser("ready"); s.add_argument("id")
    s = sub.add_parser("claim"); s.add_argument("id"); s.add_argument("--worker", required=True)
    s.add_argument("--reads", nargs="*", help="read-context paths hashed at claim, re-verified at done")
    s = sub.add_parser("done"); s.add_argument("id"); s.add_argument("--sha", nargs="+")
    s.add_argument("--token", default=None, help="claim token issued at claim; stale tokens are refused")
    s = sub.add_parser("review"); s.add_argument("id"); s.add_argument("--reviewer", required=True)
    s.add_argument("--owner-token")
    s.add_argument("--local-ok", action="store_true",
                   help="review local objects even when a remote exists (graded, not silent)")
    s = sub.add_parser("verdict"); s.add_argument("id"); s.add_argument("--owner-token")
    s.add_argument("--result", choices=["PASS", "FAIL"], required=True); s.add_argument("--note")
    s = sub.add_parser("requeue"); s.add_argument("id")
    s.add_argument("--note"); s.add_argument("--to-draft", action="store_true")
    sub.add_parser("board")
    s = sub.add_parser("verify"); s.add_argument("--stale-hours", type=float, default=6.0)
    s = sub.add_parser("rebuild"); s.add_argument("--check", action="store_true")
    sub.add_parser("log-verify")

    a = p.parse_args(argv)
    global JSON_MODE
    JSON_MODE = bool(getattr(a, "json", False))
    if not getattr(a, "actor", None):
        refuse("REFUSED_ANONYMOUS_ACTOR",
               "--actor is required (or SWARM_ACTOR env): attribution is part of the audit trail")
    root = a.root.resolve()
    if subprocess.run(["git", "-C", str(root), "rev-parse", "--git-dir"],
                      capture_output=True).returncode != 0:
        die(2, f"{root} is not a git repository")
    {"init": cmd_init, "map": cmd_map, "add": cmd_add, "ready": cmd_ready,
     "claim": cmd_claim, "done": cmd_done, "review": cmd_review, "edit": cmd_edit,
     "note": cmd_note, "rebuild": cmd_rebuild,
     "verdict": cmd_verdict, "requeue": cmd_requeue, "board": cmd_board,
     "verify": cmd_verify, "log-verify": cmd_log_verify}[a.cmd](root, a)


if __name__ == "__main__":
    main()
