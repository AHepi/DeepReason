import json
import subprocess
import sys
from pathlib import Path

import os
import pytest
os.environ.setdefault("SWARM_ACTOR", "test")

from treadle import engine

ASSETS = Path(__file__).resolve().parents[1] / "repo-assets"


def sh(repo, *args):
    r = subprocess.run(list(args), cwd=str(repo), capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    return r.stdout.strip()


@pytest.fixture()
def repo(tmp_path):
    subprocess.run(["git", "init", "-q", "-b", "main", str(tmp_path)], check=True)
    for k, v in (("user.email", "t@t"), ("user.name", "t")):
        subprocess.run(["git", "-C", str(tmp_path), "config", k, v], check=True)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/swarm_gate.py").write_text((ASSETS / "swarm_gate.py").read_text())
    (tmp_path / "skills/test-stage").mkdir(parents=True)
    (tmp_path / "skills/test-stage/SKILL.md").write_text(
        "---\nname: t\ndescription: t\n---\n<!-- PROMPT-CORE-BEGIN -->\nYou write files.\n<!-- PROMPT-CORE-END -->\n")
    (tmp_path / "treadle.toml").write_text(
        '[driver]\nbase_url = "http://stub"\n\n'
        '[stage.gen]\nmodel = "stub-model"\nescalate_model = "stub-big"\n'
        'skill = "skills/test-stage/SKILL.md"\nmax_refinements = 1\n\n'
        '[stage.rev]\nkind = "review"\nmodel = "stub-reviewer"\n'
        'skill = "skills/test-stage/SKILL.md"\n\n'
        '[[routing]]\nprefix = "GEN-"\nstage = "gen"\n'
        '[[routing]]\nprefix = "GEN-"\nstage = "gen"\n'
    )
    (tmp_path / "out").mkdir()
    (tmp_path / "out/keep.txt").write_text("seed\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-qm", "init"], check=True)
    sh(tmp_path, "python3", "scripts/swarm_gate.py", "init")
    head = sh(tmp_path, "git", "rev-parse", "HEAD")
    sh(tmp_path, "python3", "scripts/swarm_gate.py", "add", "GEN-1",
       "--goal", "write greeting", "--cone", "out/*",
       "--base", head, "--accept", "grep -q hello out/hello.txt",
       "--out-of-scope", "everything else")
    sh(tmp_path, "python3", "scripts/swarm_gate.py", "ready", "GEN-1")
    return tmp_path


GOOD = "thinking...\n===FILE: out/hello.txt===\nhello world\n===END===\n"
BAD_PATH = "===FILE: ../evil.txt===\nx\n===END===\n===FILE: out/hello.txt===\nnope\n===END===\n"


def test_parse_and_cone_safety(tmp_path):
    files = engine.parse_files(GOOD)
    assert files == {"out/hello.txt": "hello world\n"}
    task = {"cone": ["out/*"]}
    written, rejected = engine.safe_write(tmp_path, task, engine.parse_files(BAD_PATH))
    assert rejected == ["../evil.txt"] and written == ["out/hello.txt"]


def test_happy_path_commits_and_marks_done(repo):
    cfg = engine.load_config(repo)
    calls = []

    def stub(messages, **kw):
        calls.append(kw["model"])
        return GOOD

    res = engine.run_loop(cfg, chat_fn=stub, log=lambda *a: None)
    assert res == {"GEN-1": "COMMITTED"}
    board = engine.read_board(repo)
    assert board["tasks"]["GEN-1"]["state"] == "COMMITTED"
    assert "GEN-1" in sh(repo, "git", "log", "-1", "--format=%s")
    assert (repo / ".treadle/calls.jsonl").exists()


def test_refine_then_escalate_then_block(repo):
    cfg = engine.load_config(repo)
    seen = []

    def stub(messages, **kw):
        seen.append(kw["model"])
        return "===FILE: out/hello.txt===\ngoodbye\n===END===\n"  # never passes accept

    res = engine.run_loop(cfg, chat_fn=stub, log=lambda *a: None)
    assert res == {"GEN-1": "BLOCKED"}
    assert "stub-big" in seen  # escalation happened
    board = engine.read_board(repo)
    assert board["tasks"]["GEN-1"]["state"] == "READY"  # requeued
    # failed artifact must not linger (untracked file: deleted; tracked: restored)
    p = repo / "out/hello.txt"
    assert not p.exists() or not p.read_text().startswith("goodbye")


def test_refinement_feedback_reaches_model(repo):
    cfg = engine.load_config(repo)
    replies = iter(["===FILE: out/hello.txt===\nwrong\n===END===\n", GOOD])
    prompts = []

    def stub(messages, **kw):
        prompts.append(messages[-1]["content"])
        return next(replies)

    res = engine.run_loop(cfg, chat_fn=stub, log=lambda *a: None)
    assert res == {"GEN-1": "COMMITTED"}
    assert "acceptance failed" in prompts[1]


def test_review_task_flow(repo):
    cfg = engine.load_config(repo)
    engine.run_loop(cfg, chat_fn=lambda m, **k: GOOD, log=lambda *a: None)
    head = sh(repo, "git", "rev-parse", "HEAD")
    sh(repo, "python3", "scripts/swarm_gate.py", "add", "REV-1",
       "--goal", "review GEN-1", "--cone", "out/*",
       "--base", sh(repo, "git", "rev-parse", "HEAD~1"),
       "--accept", "true", "--out-of-scope", "n/a")
    # move REV-1 into COMMITTED state pointing at GEN-1's sha
    board = json.loads((repo / ".swarm/board.json").read_text())
    board["tasks"]["REV-1"].update(state="COMMITTED", shas=[head])
    (repo / ".swarm/board.json").write_text(json.dumps(board))
    cfg2 = engine.load_config(repo)
    cfg2.routing.append(("REV-", "rev"))
    reply = ("looks right\nBEGIN_VERDICT\ncheck: REVIEW\nverdict: PASS\nseverity: NONE\n"
             'evidence_lines: NONE\nevidence: NONE\nnote: matches goal\nEND_VERDICT')
    res = engine.run_loop(cfg2, chat_fn=lambda m, **k: reply, log=lambda *a: None)
    assert res.get("REV-1") == "PASS"
    board = engine.read_board(repo)
    assert board["tasks"]["REV-1"]["state"] == "DONE"


def test_empty_reply_diagnosed_and_budget_raised(repo):
    cfg = engine.load_config(repo)
    replies = iter([("", "length"), GOOD])
    seen_tokens = []

    def stub(messages, **kw):
        seen_tokens.append(kw["max_tokens"])
        return next(replies)

    res = engine.run_loop(cfg, chat_fn=stub, log=lambda *a: None)
    assert res == {"GEN-1": "COMMITTED"}
    assert seen_tokens[1] == seen_tokens[0] * 2  # auto-raise, not burned candidates
    ev = list((repo / ".treadle/evidence").glob("GEN-1-*.log"))
    assert ev and "EMPTY_REPLY" in ev[0].read_text()


def test_blocked_evidence_persisted_and_referenced(repo):
    cfg = engine.load_config(repo)
    res = engine.run_loop(cfg, chat_fn=lambda m, **k: "===FILE: out/hello.txt===\nwrong\n===END===\n",
                          log=lambda *a: None)
    assert res == {"GEN-1": "BLOCKED"}
    ev = list((repo / ".treadle/evidence").glob("GEN-1-*.log"))
    assert ev and "ACCEPTANCE_FAIL" in ev[0].read_text()
    board = engine.read_board(repo)
    assert str(ev[0]) in json.dumps(board["tasks"]["GEN-1"]["notes"])


def test_stale_claim_recovered_at_startup(repo):
    sh(repo, "python3", "scripts/swarm_gate.py", "--actor", "treadle",
       "claim", "GEN-1", "--worker", "treadle")
    assert engine.read_board(repo)["tasks"]["GEN-1"]["state"] == "CLAIMED"
    cfg = engine.load_config(repo)
    res = engine.run_loop(cfg, chat_fn=lambda m, **k: GOOD, log=lambda *a: None)
    assert res == {"GEN-1": "COMMITTED"}


def test_env_base_url_precedence(repo, monkeypatch):
    monkeypatch.setenv("TREADLE_BASE_URL", "http://envhost:9/v1")
    cfg = engine.load_config(repo)
    assert cfg.base_url == "http://envhost:9/v1"
    assert cfg.extra["base_url_source"] == "env:TREADLE_BASE_URL"


def test_gate_survives_missing_optional_keys(repo):
    board = json.loads((repo / ".swarm/board.json").read_text())
    for k in ("worker", "notes", "shas"):
        board["tasks"]["GEN-1"].pop(k, None)
    (repo / ".swarm/board.json").write_text(json.dumps(board))
    out = sh(repo, "python3", "scripts/swarm_gate.py", "board")
    assert "GEN-1" in out


def test_gate_edit_repairs_brief_through_gate(repo):
    head = sh(repo, "git", "rev-parse", "HEAD")
    sh(repo, "python3", "scripts/swarm_gate.py", "add", "GEN-2",
       "--goal", "g", "--cone", "out/*", "--accept", "true", "--out-of-scope", "n")
    r = subprocess.run(["python3", "scripts/swarm_gate.py", "ready", "GEN-2"],
                       cwd=str(repo), capture_output=True, text=True)
    assert r.returncode != 0  # incomplete brief refused at ready (defect #7 half one)
    sh(repo, "python3", "scripts/swarm_gate.py", "edit", "GEN-2", "--base", head)
    sh(repo, "python3", "scripts/swarm_gate.py", "ready", "GEN-2")
    assert engine.read_board(repo)["tasks"]["GEN-2"]["state"] == "READY"


def test_local_ok_review_grades_verdict(repo):
    cfg = engine.load_config(repo)
    engine.run_loop(cfg, chat_fn=lambda m, **k: GOOD, log=lambda *a: None)
    board = json.loads((repo / ".swarm/board.json").read_text())
    board["config"]["require_remote"] = True
    (repo / ".swarm/board.json").write_text(json.dumps(board))
    r = subprocess.run(["python3", "scripts/swarm_gate.py", "--actor", "r",
                        "review", "GEN-1", "--reviewer", "r"],
                       cwd=str(repo), capture_output=True, text=True)
    assert "REFUSED_NOT_ON_REMOTE" in r.stdout + r.stderr
    cfg2 = engine.load_config(repo)
    cfg2.extra["push"] = "false"
    cfg2.routing.append(("GEN-", "rev"))
    reply = ("ok\nBEGIN_VERDICT\ncheck: REVIEW\nverdict: PASS\nseverity: NONE\n"
             'evidence_lines: NONE\nevidence: NONE\nnote: fine\nEND_VERDICT')
    board = json.loads((repo / ".swarm/board.json").read_text())
    res = engine.run_review(cfg2, "GEN-1", board["tasks"]["GEN-1"],
                            cfg2.stages["rev"], chat_fn=lambda m, **k: reply,
                            log=lambda *a: None)
    assert res == "PASS"
    notes = engine.read_board(repo)["tasks"]["GEN-1"]["notes"]
    assert any("REVIEWED_LOCAL_OBJECTS" in str(n) for n in notes)


def test_battery_digest_hardened(tmp_path):
    import shutil
    tool = Path(__file__).resolve().parents[1] / "repo-assets" / "battery_digest.py"
    good = tmp_path / "B.md"
    good.write_text("### P1 - a\nbody one\n\n### N1 - b\nbody two\n\n## Registry\n\n"
                    "| id | kind | partner | digest |\n|----|----|----|----|\n"
                    "| P1 | positive | N1 | PENDING-DIGEST |\n"
                    "| N1 | near-miss | P1 | PENDING-DIGEST |\n")
    r = subprocess.run([sys.executable, str(tool), str(good), "--write"], capture_output=True, text=True)
    assert r.returncode == 0 and "wrote 2" in r.stdout
    r = subprocess.run([sys.executable, str(tool), str(good), "--verify"], capture_output=True, text=True)
    assert r.returncode == 0
    r = subprocess.run([sys.executable, str(tool), str(good), "--write"], capture_output=True, text=True)
    assert r.returncode == 1  # defect-12 guard: zero rewritten is loud
    noreg = tmp_path / "N.md"
    noreg.write_text("### P1 - a\nbody\n")
    r = subprocess.run([sys.executable, str(tool), str(noreg), "--verify"], capture_output=True, text=True)
    assert r.returncode == 1 and "registry" in r.stdout.lower()  # defect-10 guard


def test_context_files_reach_prompt_independent_of_cone(repo):
    (repo / "zoo/batteries").mkdir(parents=True)
    (repo / "zoo/batteries/FORMAT.md").write_text("GRAMMAR-SENTINEL-XYZ\n")
    (repo / "treadle.toml").write_text((repo / "treadle.toml").read_text().replace(
        'skill = "skills/test-stage/SKILL.md"\nmax_refinements = 1',
        'skill = "skills/test-stage/SKILL.md"\nmax_refinements = 1\ncontext_files = ["zoo/batteries/FORMAT.md"]', 1))
    cfg = engine.load_config(repo)
    prompts = []

    def stub(messages, **kw):
        prompts.append(messages[-1]["content"] if messages[-1]["role"] == "user" else messages[1]["content"])
        return GOOD

    engine.run_loop(cfg, chat_fn=stub, log=lambda *a: None)
    assert "GRAMMAR-SENTINEL-XYZ" in prompts[0]
    assert "READ-ONLY REFERENCE" in prompts[0]


DC = Path(__file__).resolve().parents[1] / "repo-assets" / "derivation_check.py"
EX = Path(__file__).resolve().parents[1] / "repo-assets" / "derivations-example"


def _dc(*paths, lax=False):
    return subprocess.run([sys.executable, str(DC)] + [str(p) for p in paths]
                          + (["--lax"] if lax else []), capture_output=True, text=True)


def test_derivation_valid_passes():
    r = _dc(EX / "rules.json", EX / "theory.json", EX / "example-derivation.json")
    assert r.returncode == 0 and "PASS (4 step" in r.stdout


def test_derivation_errors_are_step_addressed(tmp_path):
    d = json.loads((EX / "example-derivation.json").read_text())
    d["steps"][2]["premises"] = ["s2", "s1"]  # MP arguments swapped
    p = tmp_path / "bad.json"; p.write_text(json.dumps(d))
    r = _dc(EX / "rules.json", EX / "theory.json", p)
    assert r.returncode == 1 and "step s3" in r.stdout


def test_conclusion_must_match_target_bytes(tmp_path):
    d = json.loads((EX / "example-derivation.json").read_text())
    d["target"] = "T1"  # conclusion is the AND, target is Q alone
    p = tmp_path / "bad.json"; p.write_text(json.dumps(d))
    r = _dc(EX / "rules.json", EX / "theory.json", p)
    assert r.returncode == 1 and "does not match target" in r.stdout


def test_grade_cannot_exceed_premise_authority(tmp_path):
    d = json.loads((EX / "example-derivation.json").read_text())
    d["steps"][0]["grade"] = "T"   # premise D-row claimed as T... premise grade is free
    d["steps"][2]["grade"] = "D"   # derived step claiming HIGHER authority (D < T floor? order D,T => D index0 < min) 
    p = tmp_path / "bad.json"; p.write_text(json.dumps(d))
    r = _dc(EX / "rules.json", EX / "theory.json", p)
    assert r.returncode == 1 and "exceeds authority" in r.stdout


def test_manual_side_condition_is_cannot_verify(tmp_path):
    theory = json.loads((EX / "theory.json").read_text())
    d = {"schema": "DERIVATION_V1", "theory": "toy", "target": "T3",
         "steps": [
             {"id": "s1", "rule": "PREMISE", "row": "AX1", "grade": "D"},
             {"id": "s2", "rule": "ALL_E", "premises": ["s1"],
              "formula": ["implies", ["rel", "R", ["elem", "A", "a0"], ["elem", "A", "a0"]],
                                      ["rel", "Q", ["elem", "A", "a0"], ["elem", "A", "a0"]]],
              "grade": "T"}],
         "conclusion_step": "s2"}
    theory["rows"]["T3"] = {"kind": "claim", "condition": d["steps"][1]["formula"]}
    tp = tmp_path / "theory.json"; tp.write_text(json.dumps(theory))
    # ALL_E needs ?xv/?t bound: they appear only in side conditions -> unbound => substitution refs unbound
    p = tmp_path / "d.json"; p.write_text(json.dumps(d))
    r = _dc(EX / "rules.json", tp, p)
    assert r.returncode == 1 and "unbound" in r.stdout


def test_readset_stale_refused_and_rolled_back(repo):
    (repo / "zoo/batteries").mkdir(parents=True, exist_ok=True)
    ctx = repo / "zoo/batteries/FORMAT.md"
    ctx.write_text("v1\n")
    (repo / "treadle.toml").write_text((repo / "treadle.toml").read_text().replace(
        'skill = "skills/test-stage/SKILL.md"\nmax_refinements = 1',
        'skill = "skills/test-stage/SKILL.md"\nmax_refinements = 1\ncontext_files = ["zoo/batteries/FORMAT.md"]', 1))
    cfg = engine.load_config(repo)

    def stub(messages, **kw):
        ctx.write_text("v2 CHANGED MID-TASK\n")  # read set mutates while the model works
        return GOOD
    res = engine.run_loop(cfg, chat_fn=stub, log=lambda *a: None)
    assert res == {"GEN-1": "BLOCKED"}
    board = engine.read_board(repo)
    assert board["tasks"]["GEN-1"]["state"] == "READY"  # requeued, work not landed
    assert "READSET" in json.dumps(board["tasks"]["GEN-1"]["notes"])
    assert "GEN-1" not in sh(repo, "git", "log", "-1", "--format=%s")  # commit rolled back


def test_stale_claim_token_refused(repo):
    head = sh(repo, "git", "rev-parse", "HEAD")
    sh(repo, "python3", "scripts/swarm_gate.py", "--actor", "w1",
       "claim", "GEN-1", "--worker", "w1")
    sh(repo, "python3", "scripts/swarm_gate.py", "--actor", "w1", "requeue", "GEN-1",
       "--note", "orphan")
    sh(repo, "python3", "scripts/swarm_gate.py", "--actor", "w2",
       "claim", "GEN-1", "--worker", "w2")  # token now 2
    r = subprocess.run(["python3", "scripts/swarm_gate.py", "--actor", "w1", "done",
                        "GEN-1", "--sha", head, "--token", "1"],
                       cwd=str(repo), capture_output=True, text=True)
    assert "REFUSED_STALE_CLAIM_TOKEN" in r.stdout + r.stderr


def test_independent_verify_command_gates_acceptance(repo):
    sh(repo, "python3", "scripts/swarm_gate.py", "edit", "GEN-1",
       "--verify", "grep -q world out/hello.txt")
    sh(repo, "python3", "scripts/swarm_gate.py", "ready", "GEN-1")
    cfg = engine.load_config(repo)
    bad = "===FILE: out/hello.txt===\nhello mars\n===END===\n"  # accept passes, verify fails
    res = engine.run_loop(cfg, chat_fn=lambda m, **k: bad, log=lambda *a: None)
    assert res == {"GEN-1": "BLOCKED"}
    ev = list((repo / ".treadle/evidence").glob("GEN-1-*.log"))
    assert any("VERIFY_FAIL" in e.read_text() for e in ev)


def test_attestation_human_audited_with_transitive_taint(tmp_path):
    theory = json.loads((EX / "theory.json").read_text())
    d = {"schema": "DERIVATION_V1", "theory": "toy", "target": "T3",
         "steps": [
             {"id": "s1", "rule": "PREMISE", "row": "AX1", "grade": "D"},
             {"id": "s2", "rule": "HAND_ID", "premises": ["s1"],
              "formula": theory["rows"]["AX1"]["condition"], "grade": "T"},
             {"id": "s3", "rule": "AND_I", "premises": ["s2", "s2"],
              "formula": ["and", theory["rows"]["AX1"]["condition"],
                          theory["rows"]["AX1"]["condition"]], "grade": "T"}],
         "conclusion_step": "s3"}
    theory["rows"]["T3"] = {"kind": "claim", "condition": d["steps"][2]["formula"]}
    rules = json.loads((EX / "rules.json").read_text())
    rules["rules"]["HAND_ID"] = {"premises": ["?A"], "conclusion": "?A",
                                 "side_conditions": [{"kind": "MANUAL",
                                                      "text": "instantiation checked by hand"}]}
    rp = tmp_path / "rules.json"; rp.write_text(json.dumps(rules))
    tp = tmp_path / "theory.json"; tp.write_text(json.dumps(theory))
    dp = tmp_path / "d.json"; dp.write_text(json.dumps(d))
    r = _dc(rp, tp, dp)
    assert r.returncode == 3, r.stdout  # unattested MANUAL: strict failure
    import hashlib as h
    sys.path.insert(0, str(DC.parent))
    from derivation_check import attest_key
    key = attest_key(h.sha256(rp.read_bytes()).hexdigest(),
                     h.sha256(dp.read_bytes()).hexdigest(), "s2",
                     "instantiation checked by hand")
    ap = tmp_path / "att.json"
    ap.write_text(json.dumps({"attestations": [
        {"key": key, "by": "owner", "date": "2026-08-22", "reason": "checked on paper"}]}))
    r = subprocess.run([sys.executable, str(DC), str(rp), str(tp), str(dp),
                        "--attest", str(ap)], capture_output=True, text=True)
    assert r.returncode == 0 and "PASS_HUMAN_AUDITED" in r.stdout, r.stdout
    assert "2 step(s) transitively dependent" in r.stdout, r.stdout
    dp.write_text(json.dumps(d) + "\n")  # any byte edit invalidates the attestation
    r = subprocess.run([sys.executable, str(DC), str(rp), str(tp), str(dp),
                        "--attest", str(ap)], capture_output=True, text=True)
    assert r.returncode == 3


def test_rebuild_check_clean_and_divergent(repo):
    cfg = engine.load_config(repo)
    engine.run_loop(cfg, chat_fn=lambda m, **k: GOOD, log=lambda *a: None)
    out = sh(repo, "python3", "scripts/swarm_gate.py", "rebuild", "--check")
    assert "projection agrees" in out
    board = json.loads((repo / ".swarm/board.json").read_text())
    board["tasks"]["GEN-1"]["state"] = "DONE"  # out-of-band mutation
    (repo / ".swarm/board.json").write_text(json.dumps(board))
    r = subprocess.run(["python3", "scripts/swarm_gate.py", "rebuild", "--check"],
                       cwd=str(repo), capture_output=True, text=True)
    assert "REFUSED_REPLAY_DIVERGENT" in r.stdout + r.stderr


def test_p1_verdict_replays_done_and_exceptions_disclosed(repo):
    cfg = engine.load_config(repo)
    engine.run_loop(cfg, chat_fn=lambda m, **k: GOOD, log=lambda *a: None)
    sh(repo, "python3", "scripts/swarm_gate.py", "--actor", "r",
       "review", "GEN-1", "--reviewer", "r")
    sh(repo, "python3", "scripts/swarm_gate.py", "--actor", "r",
       "verdict", "GEN-1", "--result", "PASS", "--note", "ok")
    out = sh(repo, "python3", "scripts/swarm_gate.py", "rebuild", "--check")
    assert "projection agrees" in out  # P1: PASS verdict now replays as DONE
    # P2: off-log task handled by disclosed exception, not synthetic history
    board = json.loads((repo / ".swarm/board.json").read_text())
    board["tasks"]["OFFLOG-1"] = dict(board["tasks"]["GEN-1"], state="DONE")
    (repo / ".swarm/board.json").write_text(json.dumps(board))
    r = subprocess.run(["python3", "scripts/swarm_gate.py", "rebuild", "--check"],
                       cwd=str(repo), capture_output=True, text=True)
    assert "REFUSED_REPLAY_DIVERGENT" in r.stdout + r.stderr
    (repo / ".swarm/rebuild-exceptions.json").write_text(
        json.dumps({"OFFLOG-1": "closed off-log during 0.4.0 apply; disclosed"}))
    out = sh(repo, "python3", "scripts/swarm_gate.py", "rebuild", "--check")
    assert "EXCEPTED OFFLOG-1" in out and "projection agrees" in out


def test_anonymous_actor_and_owner_token(repo, monkeypatch):
    monkeypatch.delenv("SWARM_ACTOR", raising=False)
    r = subprocess.run(["python3", "scripts/swarm_gate.py", "board"],
                       cwd=str(repo), capture_output=True, text=True,
                       env={k: v for k, v in os.environ.items() if k != "SWARM_ACTOR"})
    assert "REFUSED_ANONYMOUS_ACTOR" in r.stdout + r.stderr
    cfg = engine.load_config(repo)
    engine.run_loop(cfg, chat_fn=lambda m, **k: GOOD, log=lambda *a: None)
    import hashlib as h
    board = json.loads((repo / ".swarm/board.json").read_text())
    board["config"]["owner_token_sha256"] = h.sha256(b"s3cret").hexdigest()
    (repo / ".swarm/board.json").write_text(json.dumps(board))
    sh(repo, "python3", "scripts/swarm_gate.py", "--actor", "r",
       "review", "GEN-1", "--reviewer", "r")
    r = subprocess.run(["python3", "scripts/swarm_gate.py", "--actor", "r", "verdict",
                        "GEN-1", "--result", "PASS", "--note", "n"],
                       cwd=str(repo), capture_output=True, text=True)
    assert "REFUSED_OWNER_UNVERIFIED" in r.stdout + r.stderr
    sh(repo, "python3", "scripts/swarm_gate.py", "--actor", "r", "verdict",
       "GEN-1", "--result", "PASS", "--note", "n", "--owner-token", "s3cret")


def test_note_amend_and_json_refusal(repo):
    sh(repo, "python3", "scripts/swarm_gate.py", "--actor", "a",
       "note", "GEN-1", "--note", "truncated not")
    sh(repo, "python3", "scripts/swarm_gate.py", "--actor", "a",
       "note", "GEN-1", "--note", "truncated note, corrected", "--amend-index", "0")
    board = engine.read_board(repo)
    n = board["tasks"]["GEN-1"]["notes"][0]
    assert n["note"].endswith("corrected") and n["amends"]["note"] == "truncated not"
    r = subprocess.run(["python3", "scripts/swarm_gate.py", "--json", "--actor", "a",
                        "claim", "NOPE", "--worker", "w"],
                       cwd=str(repo), capture_output=True, text=True)
    payload = json.loads((r.stdout + r.stderr).strip().splitlines()[-1])
    assert payload["ok"] is False and payload["refusal"] in (
        "REFUSED_TASK_UNKNOWN", "REFUSED_MAP_STALE")


def test_protocol_mismatch_refused(repo):
    board = json.loads((repo / ".swarm/board.json").read_text())
    board["config"]["protocol"] = 99
    (repo / ".swarm/board.json").write_text(json.dumps(board))
    r = subprocess.run(["python3", "scripts/swarm_gate.py", "board"],
                       cwd=str(repo), capture_output=True, text=True,
                       env={**os.environ, "SWARM_ACTOR": "t"})
    assert "REFUSED_PROTOCOL_MISMATCH" in r.stdout + r.stderr


def test_symlink_escape_rejected(repo):
    import tempfile
    outside = Path(tempfile.mkdtemp())  # genuinely outside the repo (repo IS tmp_path)
    (repo / "out/link").symlink_to(outside)
    task = {"cone": ["out/*"]}
    written, rejected = engine.safe_write(
        repo, task, {"out/link/evil.txt": "x", "out/ok.txt": "y"})
    assert "out/link/evil.txt" in rejected and written == ["out/ok.txt"]


def test_push_success_and_remote_review(repo, tmp_path):
    bare = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
    sh(repo, "git", "remote", "add", "origin", str(bare))
    cfg = engine.load_config(repo)  # push=auto + remote present -> pushes
    res = engine.run_loop(cfg, chat_fn=lambda m, **k: GOOD, log=lambda *a: None)
    assert res == {"GEN-1": "COMMITTED"}
    local = sh(repo, "git", "rev-parse", "HEAD")
    remote = subprocess.run(["git", "-C", str(bare), "rev-parse", "refs/heads/main"],
                            capture_output=True, text=True).stdout.strip()
    assert local == remote  # push-success path exercised (I2)
    sh(repo, "python3", "scripts/swarm_gate.py", "--actor", "r",
       "review", "GEN-1", "--reviewer", "r")  # remote check passes, no --local-ok


def test_calls_chain_integrity(repo):
    cfg = engine.load_config(repo)
    engine.run_loop(cfg, chat_fn=lambda m, **k: GOOD, log=lambda *a: None)
    import hashlib as h
    lines = (repo / ".treadle/calls.jsonl").read_text().splitlines()
    prev = "0" * 64
    for ln in lines:
        rec = json.loads(ln)
        assert rec["prev"] == prev, "hash chain broken"
        prev = h.sha256(ln.encode()).hexdigest()


def test_context_overflow_refused_with_arithmetic(repo):
    (repo / "treadle.toml").write_text((repo / "treadle.toml").read_text().replace(
        'max_refinements = 1', 'max_refinements = 1\ncontext_window = 100', 1))
    cfg = engine.load_config(repo)
    called = []
    res = engine.run_loop(cfg, chat_fn=lambda m, **k: called.append(1) or GOOD,
                          log=lambda *a: None)
    assert res == {"GEN-1": "BLOCKED"} and not called  # refused BEFORE any model call
    assert "REFUSED_CONTEXT_OVERFLOW" in json.dumps(engine.read_board(repo)["tasks"]["GEN-1"]["notes"])


def test_cross_schema_replay_refused(repo):
    lp = repo / ".swarm/log.jsonl"
    lp.write_text(lp.read_text() + json.dumps(
        {"gate_v": "0.0.1", "schema": 1, "action": "note", "task": "GEN-1",
         "actor": "old", "detail": {"note": "x"}, "prev": "x", "ts": "t"}) + "\n")
    r = subprocess.run(["python3", "scripts/swarm_gate.py", "rebuild", "--check"],
                       cwd=str(repo), capture_output=True, text=True,
                       env={**os.environ, "SWARM_ACTOR": "t"})
    assert "REFUSED_REPLAY_DIVERGENT" in r.stdout + r.stderr and "schema versions" in r.stdout + r.stderr


def test_substitution_capture_refused():
    sys.path.insert(0, str(DC.parent))
    from derivation_check import subst
    # substituting t=["var","y"] into forall y ... would capture y: refuse (None)
    f = ["forall", "y", "A", ["rel", "R", ["var", "x"], ["var", "y"]]]
    assert subst(f, "x", ["var", "y"]) is None
    # safe case: fresh term substitutes fine
    ok = subst(f, "x", ["elem", "A", "a0"])
    assert ok == ["forall", "y", "A", ["rel", "R", ["elem", "A", "a0"], ["var", "y"]]]
