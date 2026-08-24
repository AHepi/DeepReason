"""treadle engine -- the deterministic driver that walks the swarm board.

No LLM orchestrator: task order comes from the board (topological, routed by
id prefix), every artifact passes a deterministic acceptance command, and all
state transitions go through the repo's own swarm_gate.py, so the hash-chained
coordination log stays the single history. Models are called only inside
gated stages; failures refine (with verification feedback), then escalate
once, then requeue as BLOCKED with the evidence attached.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import client

FILE_BLOCK = re.compile(r"^===FILE: (.+?)===\s*?\n(.*?)^===END===\s*?$",
                        re.MULTILINE | re.DOTALL)
THINK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
CORE = re.compile(r"<!--\s*PROMPT-CORE-BEGIN\s*-->(.*?)<!--\s*PROMPT-CORE-END\s*-->", re.DOTALL)
VERDICT = re.compile(r"BEGIN_VERDICT\s*\n(.*?)END_VERDICT", re.DOTALL)


@dataclass
class Stage:
    name: str
    model: str
    skill: str
    kind: str = "generate"          # generate | review
    escalate_model: str = ""
    candidates: int = 1
    max_refinements: int = 2
    temperature: float = 0.0
    max_tokens: int = 4000
    context_budget_chars: int = 24000
    accept_timeout: int = 600
    context_files: list = None
    context_window: int = 0     # per-stage override; [driver] context_window default  # read-only reference paths ALWAYS included in
                                # the prompt, independent of the write cone
                                # (field fix: a skill must never demand
                                # conformance to a file the model cannot read)


@dataclass
class Config:
    repo: Path
    base_url: str
    stages: dict[str, Stage]
    routing: list[tuple[str, str]]  # (id_prefix, stage_name)
    worker: str = "treadle"
    seed: int = 17
    extra: dict = field(default_factory=dict)


def load_config(repo: Path) -> Config:
    import tomllib
    p = repo / "treadle.toml"
    if not p.exists():
        raise SystemExit(f"no treadle.toml in {repo}; copy repo-assets/treadle.toml there and edit")
    d = tomllib.loads(p.read_text(encoding="utf-8"))
    stages = {}
    for name, cfg in d.get("stage", {}).items():
        cfg = dict(cfg)
        cfg.setdefault("context_files", [])
        stages[name] = Stage(name=name, **cfg)
    routing = [(r["prefix"], r["stage"]) for r in d.get("routing", [])]
    drv = d.get("driver", {})
    import os
    env_base = os.environ.get("TREADLE_BASE_URL")
    base_url = env_base or drv.get("base_url", "http://localhost:11434/v1")
    drv["base_url_source"] = ("env:TREADLE_BASE_URL" if env_base
                              else "treadle.toml" if "base_url" in drv else "default")
    return Config(repo=repo, base_url=base_url,
                  stages=stages, routing=routing,
                  worker=drv.get("worker", "treadle"), seed=int(drv.get("seed", 17)),
                  extra=drv)


# ----------------------------------------------------------------- plumbing
def sh(repo: Path, *args: str, timeout: int = 120) -> tuple[int, str]:
    r = subprocess.run(list(args), cwd=str(repo), capture_output=True,
                       text=True, timeout=timeout)
    return r.returncode, (r.stdout + r.stderr).strip()


def gate(repo: Path, cfg: Config, *args: str) -> tuple[int, str]:
    return sh(repo, "python3", "scripts/swarm_gate.py", "--actor", cfg.worker, *args)


def log_call(repo: Path, record: dict) -> None:
    p = repo / ".treadle" / "calls.jsonl"
    p.parent.mkdir(exist_ok=True)
    prev = "0" * 64
    if p.exists():
        last = None
        with p.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    last = line.rstrip("\n")
        if last:
            prev = hashlib.sha256(last.encode()).hexdigest()
    record = {**record, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "prev": prev}
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


def _normalize_reply(r) -> tuple[str, str]:
    """Accept str (stubs, old clients) or (content, finish_reason)."""
    return (r if isinstance(r, tuple) else (r, "unknown"))


class Evidence:
    """Defect #2: everything the run learned is persisted, not just fed to
    the refinement prompt and dropped."""

    def __init__(self, repo: Path, task_id: str):
        d = repo / ".treadle" / "evidence"
        d.mkdir(parents=True, exist_ok=True)
        self.path = d / f"{task_id}-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.log"

    def add(self, tag: str, body: str) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(f"\n===== {tag} {time.strftime('%H:%M:%SZ', time.gmtime())} =====\n{body}\n")


def prompt_core(repo: Path, skill_rel: str) -> str:
    p = repo / skill_rel
    if not p.exists():
        raise SystemExit(f"stage skill not found: {p}")
    m = CORE.search(p.read_text(encoding="utf-8"))
    if not m:
        raise SystemExit(f"no PROMPT-CORE markers in {p}")
    return m.group(1).strip()


# ----------------------------------------------------------------- board
def read_board(repo: Path) -> dict:
    return json.loads((repo / ".swarm" / "board.json").read_text(encoding="utf-8"))


def route_stage(cfg: Config, task_id: str) -> str | None:
    for prefix, stage in cfg.routing:
        if task_id.startswith(prefix):
            return stage
    return None


def runnable(cfg: Config) -> list[tuple[str, dict, Stage]]:
    board = read_board(cfg.repo)
    tasks = board["tasks"]
    out = []
    for tid in sorted(tasks):
        t = tasks[tid]
        stage_name = route_stage(cfg, tid)
        if stage_name is None or stage_name not in cfg.stages:
            continue
        st = cfg.stages[stage_name]
        wanted_state = "READY" if st.kind == "generate" else "COMMITTED"
        if t["state"] != wanted_state:
            continue
        if any(tasks.get(d, {}).get("state") != "DONE" for d in t.get("depends_on", [])):
            continue
        out.append((tid, t, st))
    return out


# ----------------------------------------------------------------- context
def cone_context(repo: Path, task: dict, budget: int,
                 context_files: list | None = None) -> str:
    files: list[str] = []
    rc, tracked = sh(repo, "git", "ls-files")
    import fnmatch
    for f in tracked.split("\n"):
        if any(fnmatch.fnmatch(f, pat) for pat in task["cone"]):
            files.append(f)
    parts, used = [], 0
    for ref in (context_files or []):
        rp = repo / ref
        if rp.exists():
            body = rp.read_text(encoding="utf-8", errors="replace")[:8000]
            parts.append(f"--- READ-ONLY REFERENCE (not in your cone): {ref} ---\n{body}")
            used += len(body)
        else:
            parts.append(f"--- READ-ONLY REFERENCE {ref}: MISSING — if your skill "
                         "requires it, report BLOCKED rather than inventing ---")
    mp = repo / ".swarm" / "map.md"
    if mp.exists():
        head = mp.read_text(encoding="utf-8")[:2500]
        parts.append(f"--- REPO MAP (excerpt) ---\n{head}")
        used += len(head)
    for f in files:
        try:
            body = (repo / f).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        take = body[: max(0, budget - used)]
        if not take:
            parts.append(f"--- {f} (omitted: context budget) ---")
            continue
        parts.append(f"--- {f} ({len(body)} chars{', truncated' if len(take) < len(body) else ''}) ---\n{take}")
        used += len(take)
    return "\n\n".join(parts)


GENERATE_CONTRACT = (
    "Reason first in prose if useful. Then output every file you produce as "
    "blocks, and nothing after the last block:\n"
    "===FILE: relative/path/inside/your/cone===\n<full file content>\n===END===\n"
    "Rules: full file contents (no diffs, no ellipses); paths must lie inside "
    "your cone; do not touch any other file; if you cannot complete the task, "
    "output exactly one block ===FILE: BLOCKED.md=== explaining what blocks you."
)


def build_generate_prompt(cfg: Config, task_id: str, task: dict, st: Stage) -> list[dict]:
    core = prompt_core(cfg.repo, st.skill)
    user = (f"TASK {task_id}\nGOAL: {task['goal']}\n"
            f"CONE (you may write only these paths): {', '.join(task['cone'])}\n"
            f"ACCEPTANCE (will be executed): {task['accept']}\n"
            f"OUT OF SCOPE: {task['out_of_scope']}\n\n"
            f"{cone_context(cfg.repo, task, st.context_budget_chars, st.context_files)}\n\n"
            + GENERATE_CONTRACT)
    return [{"role": "system", "content": core}, {"role": "user", "content": user}]


# ----------------------------------------------------------------- artifacts
def parse_files(reply: str) -> dict[str, str]:
    reply = THINK.sub("", reply or "")
    return {m.group(1).strip(): m.group(2) for m in FILE_BLOCK.finditer(reply)}


def safe_write(repo: Path, task: dict, files: dict[str, str]) -> tuple[list[str], list[str]]:
    import fnmatch
    written, rejected = [], []
    for rel, body in files.items():
        norm = Path(rel)
        if norm.is_absolute() or ".." in norm.parts or rel == "BLOCKED.md":
            rejected.append(rel)
            continue
        real = (repo / rel).resolve()
        if not real.is_relative_to(repo.resolve()):
            rejected.append(rel)   # symlink/canonical escape: fnmatch is not filesystem truth
            continue
        if not any(fnmatch.fnmatch(rel, pat) for pat in task["cone"]):
            rejected.append(rel)
            continue
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
        written.append(rel)
    return written, rejected


# ----------------------------------------------------------------- run one
def _rollback(repo: Path, written: list[str]) -> None:
    """Restore tracked files, delete untracked ones -- failed artifacts never linger."""
    rc, tracked = sh(repo, "git", "ls-files", "--", *written)
    tracked_set = set(tracked.split("\n")) if tracked else set()
    for f in written:
        if f in tracked_set:
            sh(repo, "git", "checkout", "--", f)
        else:
            try:
                (repo / f).unlink()
            except OSError:
                pass


def run_generate(cfg: Config, task_id: str, task: dict, st: Stage,
                 chat_fn=client.chat, log=print) -> str:
    reads = list(st.context_files or []) + [st.skill]
    claim_args = ["claim", task_id, "--worker", cfg.worker, "--reads", *reads]
    rc, out = gate(cfg.repo, cfg, *claim_args)
    if rc != 0 and "REFUSED_MAP_STALE" in out:
        gate(cfg.repo, cfg, "map")
        rc, out = gate(cfg.repo, cfg, *claim_args)
    if rc != 0:
        log(f"[{task_id}] claim refused: {out.splitlines()[0]}")
        return "SKIPPED"

    token = str(read_board(cfg.repo)["tasks"][task_id].get("claim_token", 0))
    messages = build_generate_prompt(cfg, task_id, task, st)
    model, attempt_log = st.model, []
    ev = Evidence(cfg.repo, task_id)
    # context pre-flight: refuse before spending a model call (arithmetic stated)
    est_chars = sum(len(m["content"]) for m in messages)
    ratio = float(cfg.extra.get("chars_per_token", 3.5))
    window = int(getattr(st, "context_window", 0) or cfg.extra.get("context_window", 128000))
    est_total = int(est_chars / ratio) + st.max_tokens
    if est_total > window:
        msg = (f"REFUSED_CONTEXT_OVERFLOW: est prompt {est_chars} chars / {ratio} "
               f"chars-per-token = {est_chars/ratio:.0f} tokens + max_tokens {st.max_tokens} "
               f"= {est_total} > context_window {window}; shrink cone/context or split the task")
        ev.add("CONTEXT_OVERFLOW", msg)
        gate(cfg.repo, cfg, "requeue", task_id, "--note", f"treadle: {msg[:250]}")
        log(f"[{task_id}] {msg}")
        return "BLOCKED"
    cur_max_tokens = st.max_tokens
    tokens_cap = int(cfg.extra.get("max_tokens_cap", 32000))
    for attempt in range(st.max_refinements + 2):  # initial + refinements + one escalation
        if attempt == st.max_refinements + 1 and st.escalate_model:
            model = st.escalate_model
            log(f"[{task_id}] escalating to {model}")
        candidates = st.candidates if attempt == 0 else 1
        accepted = None
        for c in range(candidates):
            raw = chat_fn(messages, model=model, base_url=cfg.base_url,
                          temperature=st.temperature if candidates == 1 else max(st.temperature, 0.7),
                          seed=cfg.seed + attempt * 10 + c, max_tokens=cur_max_tokens)
            reply, finish = _normalize_reply(raw)
            log_call(cfg.repo, {"task": task_id, "stage": st.name, "model": model,
                                "attempt": attempt, "candidate": c, "finish": finish,
                                "max_tokens": cur_max_tokens,
                                "prompt_sha": hashlib.sha256(json.dumps(messages).encode()).hexdigest()[:16],
                                "reply_sha": hashlib.sha256(reply.encode()).hexdigest()[:16]})
            if not reply.strip():
                # Defect #1: empty reply = budget, not behavior. Diagnose,
                # raise the budget, and do NOT burn remaining candidates
                # on the identical failure.
                note = (f"attempt {attempt}.{c}: EMPTY_REPLY finish_reason={finish} "
                        f"at max_tokens={cur_max_tokens} -- reasoning-token budget "
                        "exhausted before content; auto-raising budget")
                attempt_log.append(note)
                ev.add("EMPTY_REPLY", note)
                if cur_max_tokens < tokens_cap:
                    cur_max_tokens = min(cur_max_tokens * 2, tokens_cap)
                    log(f"[{task_id}] empty reply ({finish}); max_tokens -> {cur_max_tokens}")
                break  # abandon identical candidates; retry with bigger budget
            ev.add(f"REPLY a{attempt}.c{c} {model}", reply[-20000:])
            files = parse_files(reply)
            if not files or "BLOCKED.md" in files:
                msg = f"attempt {attempt}.{c}: model blocked or emitted no file blocks"
                attempt_log.append(msg)
                ev.add("NO_FILES", msg + ("\nBLOCKED.md content:\n" + files.get("BLOCKED.md", "")
                                          if files else ""))
                continue
            written, rejected = safe_write(cfg.repo, task, files)
            if rejected:
                msg = f"attempt {attempt}.{c}: rejected out-of-cone paths {rejected}"
                attempt_log.append(msg)
                ev.add("CONE_REJECT", msg)
            if not written:
                continue
            rc, acc_out = sh(cfg.repo, "bash", "-lc", task["accept"], timeout=st.accept_timeout)
            if rc == 0 and task.get("verify"):
                # independent witness: a second command that shares no code
                # with the producer; exit code + recomputed witness, not
                # exit code alone
                rc2, ver_out = sh(cfg.repo, "bash", "-lc", task["verify"], timeout=st.accept_timeout)
                if rc2 != 0:
                    attempt_log.append(f"attempt {attempt}.{c}: acceptance passed but "
                                       f"INDEPENDENT VERIFY failed:\n{ver_out[-1200:]}")
                    ev.add("VERIFY_FAIL", ver_out[-20000:])
                    _rollback(cfg.repo, written)
                    continue
                acc_out += "\n[verify] " + ver_out[-2000:]
            if rc == 0:
                accepted = (written, acc_out)
                ev.add("ACCEPTED", acc_out[-4000:])
                break
            attempt_log.append(f"attempt {attempt}.{c}: acceptance failed:\n{acc_out[-1500:]}")
            ev.add("ACCEPTANCE_FAIL", acc_out[-20000:])
            _rollback(cfg.repo, written)
        if accepted:
            written, acc_out = accepted
            sh(cfg.repo, "git", "add", *written)
            rc, _ = sh(cfg.repo, "git", "commit", "-m",
                       f"{task_id}: {st.name} via treadle\n\nmodel: {model}\naccept: {task['accept']}")
            _, sha = sh(cfg.repo, "git", "rev-parse", "HEAD")
            rc, out = gate(cfg.repo, cfg, "done", task_id, "--sha", sha, "--token", token)
            if rc != 0 and not ("READSET_STALE" in out or "STALE_CLAIM_TOKEN" in out):
                ev.add("DONE_FAILED", out[:2000])
                gate(cfg.repo, cfg, "requeue", task_id, "--note",
                     f"treadle: done failed unexpectedly ({out.splitlines()[0][:120]}); see evidence")
                log(f"[{task_id}] done failed -> requeued")
                return "BLOCKED"
            if rc != 0 and ("READSET_STALE" in out or "STALE_CLAIM_TOKEN" in out):
                ev.add("DONE_REFUSED", out[:2000])
                sh(cfg.repo, "git", "reset", "--soft", "HEAD~1")
                _rollback(cfg.repo, written)
                gate(cfg.repo, cfg, "requeue", task_id, "--note",
                     f"treadle: done refused ({out.splitlines()[0][:150]}); work rolled back, rerun against fresh reads")
                log(f"[{task_id}] done refused -> rolled back and requeued")
                return "BLOCKED"
            _maybe_push(cfg, task_id, ev, log)
            log(f"[{task_id}] COMMITTED {sha[:10]} ({model})")
            return "COMMITTED"
        if attempt <= st.max_refinements:
            messages = messages + [
                {"role": "assistant", "content": "(previous attempt)"},
                {"role": "user", "content": "Your previous attempt failed acceptance. Evidence:\n"
                 + "\n".join(attempt_log[-2:])
                 + "\nFix the cause and re-emit ALL file blocks in full.\n" + GENERATE_CONTRACT}]
    ev.add("BLOCKED", "\n".join(attempt_log))
    gate(cfg.repo, cfg, "requeue", task_id, "--note",
         f"treadle: blocked after {st.max_refinements + 2} attempts; "
         f"full evidence: {ev.path}")
    log(f"[{task_id}] BLOCKED -> requeued (evidence: {ev.path})")
    return "BLOCKED"


def _maybe_push(cfg: Config, task_id: str, ev, log) -> None:
    """Defect #5: a push story. push = auto|true|false in [driver]."""
    mode = str(cfg.extra.get("push", "auto")).lower()
    if mode == "false":
        return
    rc, remotes = sh(cfg.repo, "git", "remote")
    if mode == "auto" and not remotes.strip():
        return
    rc, out = sh(cfg.repo, "git", "push", "origin", "HEAD", timeout=180)
    if rc != 0:
        cfg.extra["_push_failed"] = True
        msg = (f"push failed for {task_id}: {out[-500:]}\n"
               "shas are LOCAL-ONLY; reviews will run with --local-ok and be "
               "graded REVIEWED_LOCAL_OBJECTS; push manually when possible")
        ev.add("PUSH_FAIL", msg)
        log(f"[{task_id}] WARN {msg.splitlines()[0]}")


def recover_stale_claims(cfg: Config, log=print) -> int:
    """Defect #3: a task CLAIMED by this driver at startup is an orphan of a
    dead run (one driver per board); requeue it through the gate."""
    n = 0
    for tid, t in read_board(cfg.repo)["tasks"].items():
        if t.get("state") == "CLAIMED" and t.get("worker") == cfg.worker:
            gate(cfg.repo, cfg, "requeue", tid, "--note",
                 "treadle: stale claim recovered at startup (previous driver exited mid-flight)")
            log(f"[{tid}] stale claim recovered -> READY")
            n += 1
    return n


def run_review(cfg: Config, task_id: str, task: dict, st: Stage,
               chat_fn=client.chat, log=print) -> str:
    local = (str(cfg.extra.get("push", "auto")).lower() == "false"
             or cfg.extra.get("_push_failed"))
    args = ["review", task_id, "--reviewer", cfg.worker] + (["--local-ok"] if local else [])
    rc, out = gate(cfg.repo, cfg, *args)
    if rc != 0:
        log(f"[{task_id}] review refused: {out.splitlines()[0]}")
        return "SKIPPED"
    _, diff = sh(cfg.repo, "git", "diff", f"{task['base']}..{task['shas'][-1]}")
    core = prompt_core(cfg.repo, st.skill)
    user = (f"TASK {task_id}\nACCEPTANCE: {task['accept']}\nOUT OF SCOPE: {task['out_of_scope']}\n"
            f"DIFF ({task['base'][:10]}..{task['shas'][-1][:10]}):\n{diff[:st.context_budget_chars]}\n\n"
            "First reason in prose. Then emit exactly one block, last:\n"
            "BEGIN_VERDICT\ncheck: REVIEW\nverdict: PASS|FAIL\nseverity: BLOCKER|MAJOR|MINOR|NONE\n"
            'evidence_lines: <n or NONE>\nevidence: "<quote or NONE>"\nnote: <one sentence>\nEND_VERDICT')
    reply, _finish = _normalize_reply(
        chat_fn([{"role": "system", "content": core}, {"role": "user", "content": user}],
                model=st.model, base_url=cfg.base_url, temperature=0.0,
                seed=cfg.seed, max_tokens=st.max_tokens))
    log_call(cfg.repo, {"task": task_id, "stage": st.name, "model": st.model, "kind": "review",
                        "reply_sha": hashlib.sha256(reply.encode()).hexdigest()[:16]})
    blocks = VERDICT.findall(THINK.sub("", reply))
    verdict = "FAIL"
    note = "no parseable verdict block"
    if blocks:
        kv = dict(re.findall(r"^(\w+):\s*(.+)$", blocks[-1], re.MULTILINE))
        verdict = "PASS" if kv.get("verdict", "").strip().upper() == "PASS" else "FAIL"
        note = kv.get("note", "")[:200]
    if local:
        note = ("REVIEWED_LOCAL_OBJECTS: " + note)[:200]
    gate(cfg.repo, cfg, "verdict", task_id, "--result", verdict, "--note", note)
    log(f"[{task_id}] review -> {verdict} ({st.model})")
    return verdict


def run_loop(cfg: Config, once: bool = False, only: str | None = None,
             chat_fn=client.chat, log=print, recover: bool = True) -> dict:
    gate(cfg.repo, cfg, "map")
    if recover and cfg.extra.get("recover_stale", True):
        recover_stale_claims(cfg, log)
    results: dict[str, str] = {}
    while True:
        queue = [(tid, t, st) for tid, t, st in runnable(cfg)
                 if only is None or tid == only]
        queue = [(tid, t, st) for tid, t, st in queue if tid not in results or results[tid] == "COMMITTED"]
        pending = [(tid, t, st) for tid, t, st in queue if results.get(tid) != ("COMMITTED" if st.kind == "generate" else results.get(tid))]
        pick = next(((tid, t, st) for tid, t, st in queue if tid not in results), None)
        if pick is None:
            break
        tid, t, st = pick
        fn = run_generate if st.kind == "generate" else run_review
        results[tid] = fn(cfg, tid, t, st, chat_fn=chat_fn, log=log)
        if once:
            break
    return results
