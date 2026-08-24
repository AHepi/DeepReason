#!/usr/bin/env python3
"""treadle 0.5.0 selftest: every guard proven on a planted violation (FR-18).

Acceptance command:  python3 treadle0.5/selftest.py

Deterministic, offline, stdlib-only. Two halves per guard: the guard PASSES
on good input, and FAILS on a planted violation. A guard that cannot be shown
to fail is treated as not existing - three guards in the source cycle passed
while checking nothing, and were found only this way.

Exit 0: all checks OK. Exit 1: any check failed, listed plainly.
"""
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKERS = HERE / "checkers"
RESULTS = []
PLANTED_REFUSED = 0


def check(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    print(f"{'OK  ' if ok else 'FAIL'} {name}" + (f" -- {detail}" if detail and not ok else ""))


def planted(name, refused, detail=""):
    global PLANTED_REFUSED
    if refused:
        PLANTED_REFUSED += 1
    check(f"[planted] {name}", refused, detail)


def load(module_name):
    spec = importlib.util.spec_from_file_location(module_name, CHECKERS / f"{module_name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_checker(script, args, cwd):
    return subprocess.run([sys.executable, str(CHECKERS / script), *args],
                          capture_output=True, text=True, cwd=cwd)


GOOD_BATTERY = """# battery

### P1 - a positive
body of p1

### N1 - its near miss
body of n1

## Registry

| id | kind | partner | digest |
|----|------|---------|--------|
| P1 | positive | N1 | PENDING-DIGEST |
| N1 | near-miss | P1 | PENDING-DIGEST |
"""


def test_battery_digest(tmp):
    battery = tmp / "BATTERY.md"
    battery.write_text(GOOD_BATTERY, encoding="utf-8")
    w = run_checker("battery_digest.py", [str(battery), "--write"], tmp)
    v = run_checker("battery_digest.py", [str(battery), "--verify"], tmp)
    check("battery_digest accepts a good battery", w.returncode == 0 and v.returncode == 0,
          w.stdout + v.stdout)
    # Planted 1: tamper one digest character.
    text = battery.read_text(encoding="utf-8")
    import re
    match = re.search(r"\| ([0-9a-f]{16}) \|", text)
    tampered = text.replace(match.group(1), ("0" if match.group(1)[0] != "0" else "1") + match.group(1)[1:], 1)
    battery.write_text(tampered, encoding="utf-8")
    v2 = run_checker("battery_digest.py", [str(battery), "--verify"], tmp)
    planted("battery_digest refuses a tampered digest", v2.returncode != 0)
    # Planted 2: registry heading gone (defect-10 guard).
    battery.write_text(GOOD_BATTERY.replace("## Registry", "## Not A Registry"), encoding="utf-8")
    v3 = run_checker("battery_digest.py", [str(battery), "--verify"], tmp)
    planted("battery_digest refuses a missing registry", v3.returncode != 0)


def test_consistency_packet(tmp):
    (tmp / "docs").mkdir()
    (tmp / "docs" / "a.md").write_text("The blast radius is one table.\n", encoding="utf-8")
    (tmp / "docs" / "b.md").write_text("Elsewhere: the blast radius is one table too.\n", encoding="utf-8")
    claims = {"packet": "PACKET.md", "window": 40, "max_chars": 5000, "claims": [
        {"label": "A", "path": "docs/a.md", "patterns": ["blast radius"]},
        {"label": "B", "path": "docs/b.md", "patterns": ["blast radius"]}]}
    (tmp / "claims.json").write_text(json.dumps(claims), encoding="utf-8")
    w = run_checker("consistency_packet.py", ["--write"], tmp)
    v = run_checker("consistency_packet.py", ["--verify"], tmp)
    check("consistency_packet builds and verifies", w.returncode == 0 and v.returncode == 0,
          w.stdout + v.stdout)
    # Planted 1: source document changes a quoted claim.
    (tmp / "docs" / "a.md").write_text("The blast radius is TWO tables.\n", encoding="utf-8")
    planted("consistency_packet refuses a stale packet",
            run_checker("consistency_packet.py", ["--verify"], tmp).returncode != 0)
    # Planted 2: a pattern that matches nothing must FAIL, not shrink coverage.
    claims["claims"][0]["patterns"] = ["zzz-renamed-away"]
    (tmp / "claims.json").write_text(json.dumps(claims), encoding="utf-8")
    planted("consistency_packet refuses a claim matching nothing",
            run_checker("consistency_packet.py", ["--write"], tmp).returncode != 0)
    # Planted 3: ceiling (FR-15) -- remedy must name shrinking, not budgets.
    claims["claims"][0]["patterns"] = ["blast radius"]
    claims["max_chars"] = 10
    (tmp / "claims.json").write_text(json.dumps(claims), encoding="utf-8")
    over = run_checker("consistency_packet.py", ["--write"], tmp)
    planted("consistency_packet refuses an over-ceiling packet",
            over.returncode != 0 and "Shrink" in over.stdout)


def test_influence_probe():
    probe_module = load("influence_probe")
    try:
        message = probe_module._demo()
        check("influence_probe demo (notices, gates, restores)", message.startswith("OK"))
    except AssertionError as exc:
        check("influence_probe demo (notices, gates, restores)", False, str(exc))

    class Target:
        def __init__(self):
            self.field = 1

    with probe_module.probe(Target) as reads:
        reads.arm()
        Target().field  # planted read
    planted("influence_probe notices a planted read", "field" in reads.seen)


def test_review_harness(tmp):
    harness = load("review_harness")
    (tmp / "in.md").write_text("# doc\nclaim text here\n", encoding="utf-8")

    def job(name, ceiling=24000, out="out/reply.md"):
        return harness.Job(name=name, role="REVIEWER", model="null-model:2026-01-01",
                           skill_core="Protocol: answer from the material only.",
                           task="Audit the claim.", inputs=(harness.Slice("in.md"),),
                           out=out, packet_ceiling=ceiling)

    row = harness.run_job(job("smoke"), harness.NullTransport, root=tmp)
    count = harness.verify_ledger("calls.jsonl", root=tmp)
    check("review_harness runs a NullTransport job and verifies", count == 1 and row["seq"] == 1)
    transcript = (tmp / "out" / "reply.md").read_text(encoding="utf-8")
    check("transcript carries the FR-16 provenance line", "reproducibility: none" in transcript)

    # Superseded semantics (FR-17): re-run with a changed packet.
    (tmp / "in.md").write_text("# doc\nclaim text CHANGED\n", encoding="utf-8")
    harness.run_job(job("smoke"), harness.NullTransport, root=tmp)
    check("superseded row kept; latest agrees", harness.verify_ledger("calls.jsonl", root=tmp) == 2)
    # Planted 1: transcript matching only the SUPERSEDED row must fail.
    rows = [json.loads(l) for l in (tmp / "calls.jsonl").read_text().splitlines()]
    old_header = (f"<!-- reproducibility: none -->\n<!-- prompt_sha256={rows[0]['prompt_sha256']} -->\n")
    (tmp / "out" / "reply.md").write_text(old_header, encoding="utf-8")
    try:
        harness.verify_ledger("calls.jsonl", root=tmp)
        planted("verify_ledger refuses a transcript matching a superseded row", False)
    except harness.HarnessError:
        planted("verify_ledger refuses a transcript matching a superseded row", True)
    # Planted 2: hash-chain break.
    lines = (tmp / "calls.jsonl").read_text().splitlines()
    bad = json.loads(lines[1]); bad["prev_sha256"] = "sha256:" + "0" * 64
    (tmp / "chain.jsonl").write_text(lines[0] + "\n" + json.dumps(bad, sort_keys=True) + "\n")
    try:
        harness.verify_ledger("chain.jsonl", root=tmp)
        planted("verify_ledger refuses a broken chain", False)
    except harness.HarnessError:
        planted("verify_ledger refuses a broken chain", True)
    # Planted 3: credential material in a row.
    (tmp / "cred.jsonl").write_text(lines[0].replace('"role": "REVIEWER"',
                                    '"role": "REVIEWER", "api_key": "x"') + "\n")
    try:
        harness.verify_ledger("cred.jsonl", root=tmp)
        planted("verify_ledger refuses credential material", False)
    except harness.HarnessError:
        planted("verify_ledger refuses credential material", True)
    # Planted 3b (found by running SETUP's own printed commands): the reply
    # digest must be checked against the transcript's reply BYTES. The final
    # row of the chain has no successor protecting it, so without the
    # cross-check a tampered reply -- or row -- was accepted. First restore a
    # clean state (re-run appends row 3 with a fresh transcript), prove clean,
    # then tamper ONLY the reply body and demand refusal WITH THE RIGHT
    # MESSAGE -- an earlier draft of this very check matched "reply" against
    # the file PATH "out/reply.md" and passed vacuously (FR-18, recursively).
    harness.run_job(job("smoke"), harness.NullTransport, root=tmp)
    check("ledger clean after restore", harness.verify_ledger("calls.jsonl", root=tmp) == 3)
    with open(tmp / "out" / "reply.md", "a", encoding="utf-8") as handle:
        handle.write("tampered line\n")
    try:
        harness.verify_ledger("calls.jsonl", root=tmp)
        planted("verify_ledger refuses a tampered transcript reply", False)
    except harness.HarnessError as exc:
        planted("verify_ledger refuses a tampered transcript reply",
                "does not match the ledger's reply_sha256" in str(exc), str(exc))
    harness.run_job(job("smoke"), harness.NullTransport, root=tmp)

    # Planted 4: packet over the governor's ceiling (FR-15), remedy named.
    try:
        job("big", ceiling=10).user(tmp)
        planted("packet governor refuses an oversized packet", False)
    except harness.HarnessError as exc:
        planted("packet governor refuses an oversized packet",
                "Shrink the packet" in str(exc) and "output budget" in str(exc))
    # Planted 5: forbidden slice (isolation).
    isolated = harness.Job(name="iso", role="BACK-TRANSLATOR", model="null-model:2026-01-01",
                           skill_core="x", task="t", inputs=(harness.Slice("in.md"),),
                           out="out/i.md", forbidden=("in.md",))
    try:
        isolated.user(tmp)
        planted("isolation check refuses a forbidden slice", False)
    except harness.HarnessError:
        planted("isolation check refuses a forbidden slice", True)


def test_package_shape():
    for doc in ("README.md", "SETUP.md", "MODULES.md", "FIELD_REPORTS.md",
                "FORMAT.md", "LEDGER_FORMAT.md"):
        check(f"doc present: {doc}", (HERE / doc).is_file())
    skills = sorted(p.parent.name for p in HERE.glob("skills/*/SKILL.md"))
    check("twelve skills present", len(skills) == 12, str(skills))
    for skill in HERE.glob("skills/*/SKILL.md"):
        text = skill.read_text(encoding="utf-8")
        ok = ("PROMPT-CORE-BEGIN" in text and "PROMPT-CORE-END" in text
              and text.startswith("---\nname:"))
        check(f"skill well-formed: {skill.parent.name}", ok)


def main():
    with tempfile.TemporaryDirectory() as d1:
        test_battery_digest(Path(d1))
    with tempfile.TemporaryDirectory() as d2:
        test_consistency_packet(Path(d2))
    test_influence_probe()
    with tempfile.TemporaryDirectory() as d3:
        test_review_harness(Path(d3))
    test_package_shape()
    failed = [name for name, ok, _ in RESULTS if not ok]
    print(f"\n{len(RESULTS)} checks, {PLANTED_REFUSED} planted violations correctly refused, "
          f"{len(failed)} failed")
    if failed:
        for name in failed:
            print(f"  FAILED: {name}")
        sys.exit(1)


if __name__ == "__main__":
    main()
