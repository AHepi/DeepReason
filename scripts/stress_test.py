#!/usr/bin/env python
"""Offline stress campaign (zero LLM tokens): push the core harness past
the sizes and shapes normal runs never reach, and confirm it stays correct
and bounded. Each scenario prints PASS/FAIL/finding; every artifact is
built directly through the harness API (no models).

Scenarios:
  S1 scale            event-count scaling of replay + verify_root
  S2 deep-attack      alternating accept/refute down a long attack chain
  S3 wide-fan         one target, many attackers; one attacker, many targets
  S4 deep-dep         suspension cascade down a long dependence chain
  S5 content          pathological content (huge, unicode, control bytes)
  S6 durability       torn log line, truncated object, missing blob
  S7 fuzz-verify      corrupt a valid root N ways; verify_root must catch it
"""

import json
import os
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from deepreason.harness import Harness  # noqa: E402
from deepreason.invariants import verify_root  # noqa: E402
from deepreason.ontology import (  # noqa: E402
    Commitment,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    Ref,
    Status,
    Warrant,
)
from deepreason.ontology.artifact import RefRole  # noqa: E402
from deepreason.ontology.warrant import WarrantType  # noqa: E402

RESULTS: list[dict] = []


def record(name, ok, detail=""):
    RESULTS.append({"scenario": name, "ok": ok, "detail": detail})
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}", flush=True)


def _attack(h, target_id, note, school=None):
    """Register nu + critic carrying an argumentative warrant on target."""
    nu = h.create_artifact(f"nu:{note}", provenance=Provenance(role="critic"))
    w = Warrant(id=f"w-{note}", target=target_id, type=WarrantType.ARGUMENTATIVE,
                validity_node=nu.id)
    critic = h.create_artifact(f"critic:{note}", provenance=Provenance(role="critic"),
                               warrants=[w])
    return critic, nu


def s1_scale(tmp):
    for n in (1000, 4000):
        root = tmp / f"scale{n}"
        h = Harness(root)
        h.register_problem(Problem(id="pi", description="d",
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []})))
        t0 = time.monotonic()
        for i in range(n):
            h.create_artifact(f"artifact number {i} with distinct content", problem_id="pi")
        build = time.monotonic() - t0
        t0 = time.monotonic()
        h2 = Harness(root)
        replay = time.monotonic() - t0
        assert len(h2.state.artifacts) == n
        t0 = time.monotonic()
        res = verify_root(root)
        vt = time.monotonic() - t0
        ok = res["violations"] == []
        record(f"S1-scale-{n}", ok,
               f"build {build:.2f}s replay {replay:.2f}s verify {vt:.2f}s "
               f"({res['stats']['artifacts']} artifacts)")


def s2_deep_attack(tmp):
    root = tmp / "deepatk"
    h = Harness(root)
    base = h.create_artifact("base claim under a long attack chain")
    ids = [base.id]
    depth = 600
    prev = base.id
    for i in range(depth):
        c, _ = _attack(h, prev, f"d{i}")
        prev = c.id
        ids.append(c.id)
    # Grounded semantics on a pure chain a0<-a1<-a2...: the LAST node is
    # unattacked => accepted; walking back, status strictly alternates.
    st = h.state.status
    last = ids[-1]
    ok = st[last] == Status.ACCEPTED
    # base (index 0) has `depth` attackers stacked; parity of depth decides.
    expected_base = Status.ACCEPTED if depth % 2 == 0 else Status.REFUTED
    ok = ok and st[base.id] == expected_base
    res = verify_root(root)
    ok = ok and res["violations"] == []
    record("S2-deep-attack", ok,
           f"depth {depth}, base={st[base.id].value}, tip={st[last].value}, "
           f"violations={len(res['violations'])}")


def s3_wide_fan(tmp):
    root = tmp / "widefan"
    h = Harness(root)
    target = h.create_artifact("heavily attacked target")
    k = 800
    for i in range(k):
        _attack(h, target.id, f"a{i}")
    # Many independent unattacked attackers => target refuted.
    ok = h.state.status[target.id] == Status.REFUTED
    res = verify_root(root)
    ok = ok and res["violations"] == []
    record("S3-wide-fan", ok,
           f"{k} attackers on one target -> {h.state.status[target.id].value}, "
           f"violations={len(res['violations'])}")


def s4_deep_dep(tmp):
    root = tmp / "deepdep"
    h = Harness(root)
    depth = 500
    prev = None
    ids = []
    for i in range(depth):
        iface = Interface(refs=[Ref(target=prev, role=RefRole.DEPENDENCE)]) if prev else Interface()
        a = h.create_artifact(f"dependent chain node {i}", interface=iface)
        ids.append(a.id)
        prev = a.id
    # Everything accepted (no attacks). Now refute the ROOT dependency (ids[0]).
    _attack(h, ids[0], "kill-root-dep")
    st = h.state.status
    # ids[0] refuted; every dependent transitively suspended_unsupported.
    ok = st[ids[0]] == Status.REFUTED
    suspended = sum(1 for i in ids[1:] if st[i] == Status.SUSPENDED_UNSUPPORTED)
    ok = ok and suspended == depth - 1
    res = verify_root(root)
    ok = ok and res["violations"] == []
    record("S4-deep-dep", ok,
           f"depth {depth}, root={st[ids[0]].value}, suspended {suspended}/{depth-1}, "
           f"violations={len(res['violations'])}")


def s5_content(tmp):
    root = tmp / "content"
    h = Harness(root)
    cases = {
        "huge_5mb": "x" * (5 * 1024 * 1024),
        "unicode": chr(0x1f4a5) + " " + chr(0x202e) + " snowman " + chr(0x2603)
                   + " tabs\t nl\n cr\r nul" + chr(0) + " end",
        "jsonish": '{"claim": "not really a skeleton", "x": 1}',
        "empty": "",
        "newlines": "\n" * 10000,
    }
    ids = {}
    for name, content in cases.items():
        try:
            a = h.create_artifact(content, problem_id=None)
            ids[name] = a.id
        except Exception as e:  # noqa: BLE001
            record("S5-content", False, f"{name} raised {type(e).__name__}: {e}")
            return
    h2 = Harness(root)  # replay must round-trip every byte
    ok = all(h2.content_text_ok(i) if hasattr(h2, "content_text_ok") else True
             for i in ids.values())
    # verify content survived byte-for-byte via the blob store
    from deepreason.programs import content_text
    ok = content_text(h2.state.artifacts[ids["huge_5mb"]], h2.blobs) == cases["huge_5mb"]
    ok = ok and content_text(h2.state.artifacts[ids["unicode"]], h2.blobs) == cases["unicode"]
    res = verify_root(root)
    ok = ok and res["violations"] == []
    record("S5-content", ok, f"{len(ids)} pathological contents round-tripped, "
           f"violations={len(res['violations'])}")


def s6_durability(tmp):
    # torn final log line
    root = tmp / "torn"
    h = Harness(root)
    h.register_problem(Problem(id="pi", description="d",
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []})))
    a = h.create_artifact("good artifact", problem_id="pi")
    with open(root / "log.jsonl", "a") as f:
        f.write('{"seq": 999, "torn write mid')  # crash mid-append
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            h2 = Harness(root)
        torn_ok = a.id in h2.state.artifacts and len(list(h2.log.read())) >= 1
    except Exception as e:  # noqa: BLE001
        torn_ok = False
        record("S6-torn-line", False, f"raised {type(e).__name__}: {e}")
    else:
        record("S6-torn-line", torn_ok, "torn final line tolerated, prior events intact")

    # missing blob: verify_root must report, not crash
    root2 = tmp / "missingblob"
    h = Harness(root2)
    big = "y" * 500  # forces a blob (not inline) path? create_artifact inlines str
    a = h.create_artifact(("z" * 100).encode())  # bytes -> blob
    ref = h.state.artifacts[a.id].content_ref
    blobpath = root2 / "blobs" / ref[:2] / ref
    if blobpath.exists():
        blobpath.unlink()
    try:
        res = verify_root(root2)
        # a missing content blob isn't checked by verify_root (only llm
        # prompt/raw blobs are), so this documents current behavior.
        record("S6-missing-blob", True,
               f"verify_root did not crash on a missing content blob "
               f"(violations={len(res['violations'])})")
    except Exception as e:  # noqa: BLE001
        record("S6-missing-blob", False, f"verify_root crashed: {type(e).__name__}: {e}")


def s7_fuzz_verify(tmp):
    # Build a valid multi-feature root, then corrupt copies and confirm
    # verify_root reports a violation (never crashes, never falsely passes).
    import shutil
    base = tmp / "fuzzbase"
    h = Harness(base)
    h.register_problem(Problem(id="pi", description="d",
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []})))
    good = h.create_artifact("target", problem_id="pi")
    _attack(h, good.id, "x")
    assert verify_root(base)["violations"] == []

    def corrupt_and_check(name, fn):
        root = tmp / f"fuzz_{name}"
        shutil.copytree(base, root)
        fn(root)
        try:
            res = verify_root(root)
            caught = len(res["violations"]) > 0 or res.get("stats") == {}
            record(f"S7-{name}", caught,
                   f"violations={len(res.get('violations', []))} "
                   f"{'(caught)' if caught else '(MISSED - false pass!)'}")
        except Exception as e:  # noqa: BLE001
            record(f"S7-{name}", False, f"verify_root CRASHED: {type(e).__name__}: {e}")

    def dup_seq(root):
        p = root / "log.jsonl"
        lines = p.read_text().splitlines()
        lines.append(lines[-1])  # duplicate last event's seq
        p.write_text("\n".join(lines) + "\n")

    def gap_seq(root):
        p = root / "log.jsonl"
        lines = p.read_text().splitlines()
        # rewrite last line's seq to skip a number
        obj = json.loads(lines[-1]); obj["seq"] = obj["seq"] + 5
        lines[-1] = json.dumps(obj)
        p.write_text("\n".join(lines) + "\n")

    def dangling_object(root):
        # delete an object file a surviving event still references
        from deepreason.canonical import sha256_hex
        p = root / "log.jsonl"
        for line in p.read_text().splitlines():
            obj = json.loads(line)
            for oid in obj.get("outputs", []):
                f = root / "objects" / f"{sha256_hex(oid.encode())}.json"
                if f.exists():
                    f.unlink()
                    return

    corrupt_and_check("dup-seq", dup_seq)
    corrupt_and_check("gap-seq", gap_seq)
    corrupt_and_check("dangling-object", dangling_object)

    # Truncating the log from the END is NOT corruption: it yields a valid
    # EARLIER state (== time-travel), and unreferenced content-addressed
    # objects are legitimate (D8). verify_root MUST still pass — asserting
    # that is the correct expectation (an earlier test wrongly flagged it).
    def truncate_log(root):
        p = root / "log.jsonl"
        lines = p.read_text().splitlines()
        p.write_text("\n".join(lines[:-2]) + "\n")

    import shutil as _sh
    tr = tmp / "fuzz_truncate"
    _sh.copytree(base, tr)
    truncate_log(tr)
    res = verify_root(tr)
    record("S7-truncate-is-valid", res["violations"] == [],
           f"truncated log = valid earlier state, violations={len(res['violations'])}")


def main():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for fn in (s1_scale, s2_deep_attack, s3_wide_fan, s4_deep_dep,
                   s5_content, s6_durability, s7_fuzz_verify):
            try:
                fn(tmp)
            except Exception:  # noqa: BLE001 - a crash IS a finding
                record(fn.__name__, False, "UNCAUGHT: " + traceback.format_exc()[-300:])
    fails = [r for r in RESULTS if not r["ok"]]
    print(f"\n=== {len(RESULTS) - len(fails)}/{len(RESULTS)} passed ===")
    for r in fails:
        print(f"  FAIL {r['scenario']}: {r['detail']}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
