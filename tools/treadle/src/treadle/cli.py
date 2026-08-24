from __future__ import annotations
import argparse, shutil, subprocess, sys
from pathlib import Path
from . import engine


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="treadle", description="Deterministic driver: hit play on the board")
    p.add_argument("--repo", type=Path, default=Path("."))
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor", help="check environment and configuration")
    sub.add_parser("plan", help="show the runnable queue without calling any model")
    pr = sub.add_parser("run", help="walk the board: claim, generate, gate, commit")
    pr.add_argument("--once", action="store_true", help="run a single task then stop")
    pr.add_argument("--task", default=None, help="run only this task id")
    pr.add_argument("--no-recover", action="store_true",
                    help="do not requeue stale claims held by this driver at startup")
    return dispatch(p.parse_args(argv))


def dispatch(a) -> int:
    repo = a.repo.resolve()
    if a.cmd == "doctor":
        ok = True
        for name, test in [
            ("git repo", lambda: subprocess.run(["git", "-C", str(repo), "rev-parse", "--git-dir"], capture_output=True).returncode == 0),
            ("swarm gate", lambda: (repo / "scripts/swarm_gate.py").exists()),
            (".swarm board", lambda: (repo / ".swarm/board.json").exists()),
            ("treadle.toml", lambda: (repo / "treadle.toml").exists()),
            ("httpx", lambda: __import__("httpx") is not None),
        ]:
            good = False
            try:
                good = bool(test())
            except Exception:
                good = False
            print(f"{'OK  ' if good else 'MISS'} {name}")
            ok = ok and good
        if ok:
            cfg = engine.load_config(repo)
            print(f"     base_url: {cfg.base_url}  (source: {cfg.extra.get('base_url_source')})")
            for s in cfg.stages.values():
                exists = (repo / s.skill).exists()
                print(f"{'OK  ' if exists else 'MISS'} stage {s.name}: skill {s.skill} model {s.model}")
                ok = ok and exists
            import os
            print(f"{'OK  ' if os.environ.get('OLLAMA_API_KEY') or 'localhost' in cfg.base_url else 'WARN'} "
                  f"credentials for {cfg.base_url}")
            for st_ in cfg.stages.values():
                for ref in (st_.context_files or []):
                    present = (repo / ref).exists()
                    print(f"{'OK  ' if present else 'WARN'} stage {st_.name} context file {ref}"
                          + ("" if present else " MISSING (dangling read reference)"))
            import hashlib as _h, tomllib as _t
            tools = _t.loads((repo / "treadle.toml").read_text()).get("tools", {})
            for name, spec in tools.items():
                tp = repo / spec.get("path", "")
                got = _h.sha256(tp.read_bytes()).hexdigest() if tp.exists() else "MISSING"
                ok_ = got == spec.get("sha256")
                print(f"{'OK  ' if ok_ else 'MISS'} pinned tool {name}: {spec.get('path')}"
                      + ("" if ok_ else f" content hash mismatch ({got[:12]} != pinned)"))
                ok = ok and ok_
            try:  # defect-adjacent: unknown model tags fail HERE, not mid-run
                import httpx
                r = httpx.get(f"{cfg.base_url.rstrip('/')}/models", timeout=4.0,
                              headers={"Authorization": f"Bearer {os.environ.get('OLLAMA_API_KEY', '')}"}
                              if os.environ.get("OLLAMA_API_KEY") else {})
                avail = {m.get("id", "") for m in r.json().get("data", [])}
                for st_ in cfg.stages.values():
                    for tag in filter(None, {st_.model, st_.escalate_model}):
                        print(f"{'OK  ' if tag in avail else 'WARN'} model tag {tag}"
                              + ("" if tag in avail else " NOT on endpoint -- verify with `ollama search`"))
            except Exception:
                print("NOTE model-tag check skipped (endpoint unreachable from here)")
        print("doctor:", "ready -- treadle run" if ok else "fix MISS lines first (see AGENT_INSTALL.md)")
        return 0 if ok else 1
    cfg = engine.load_config(repo)
    if a.cmd == "plan":
        q = engine.runnable(cfg)
        if not q:
            print("nothing runnable (need READY tasks routed to a stage; check board + [routing])")
        for tid, t, st in q:
            print(f"{tid:14} stage={st.name:12} kind={st.kind:8} model={st.model}  goal={t['goal'][:60]}")
        return 0
    if a.cmd == "run":
        results = engine.run_loop(cfg, once=a.once, only=a.task, recover=not a.no_recover)
        print("\n=== treadle summary ===")
        for tid, res in results.items():
            print(f"{tid:14} {res}")
        return 0 if all(r in ("COMMITTED", "PASS") for r in results.values()) or not results else 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
