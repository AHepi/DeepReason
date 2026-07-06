"""Stress-campaign regressions at CI-small sizes (the full-scale sweep
lives in scripts/stress_test.py). Locks in the graph-pathology correctness
and the corruption-detection properties the campaign verified."""

import json
import shutil

import pytest

from deepreason.canonical import sha256_hex
from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.ontology import (
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    Ref,
    Status,
    Warrant,
)
from deepreason.ontology.artifact import RefRole
from deepreason.ontology.warrant import WarrantType


def _attack(h, target_id, note):
    nu = h.create_artifact(f"nu:{note}", provenance=Provenance(role="critic"))
    w = Warrant(id=f"w-{note}", target=target_id, type=WarrantType.ARGUMENTATIVE,
                validity_node=nu.id)
    critic = h.create_artifact(f"critic:{note}", provenance=Provenance(role="critic"),
                               warrants=[w])
    return critic, nu


def test_deep_attack_chain_alternates(tmp_path):
    """a0<-a1<-...<-aN: tip accepted, statuses alternate, no violations."""
    h = Harness(tmp_path / "run")
    base = h.create_artifact("base")
    prev, ids = base.id, [base.id]
    depth = 60
    for i in range(depth):
        c, _ = _attack(h, prev, f"d{i}")
        prev, _ = c.id, ids.append(c.id)
    st = h.state.status
    assert st[ids[-1]] == Status.ACCEPTED
    assert st[base.id] == (Status.ACCEPTED if depth % 2 == 0 else Status.REFUTED)
    assert verify_root(tmp_path / "run")["violations"] == []


def test_wide_fan_refutes(tmp_path):
    h = Harness(tmp_path / "run")
    t = h.create_artifact("target")
    for i in range(40):
        _attack(h, t.id, f"a{i}")
    assert h.state.status[t.id] == Status.REFUTED
    assert verify_root(tmp_path / "run")["violations"] == []


def test_deep_dependence_cascade_suspends(tmp_path):
    h = Harness(tmp_path / "run")
    prev, ids = None, []
    depth = 40
    for i in range(depth):
        iface = Interface(refs=[Ref(target=prev, role=RefRole.DEPENDENCE)]) if prev else Interface()
        a = h.create_artifact(f"node {i}", interface=iface)
        ids.append(a.id)
        prev = a.id
    _attack(h, ids[0], "kill-root")
    st = h.state.status
    assert st[ids[0]] == Status.REFUTED
    assert all(st[i] == Status.SUSPENDED_UNSUPPORTED for i in ids[1:])
    assert verify_root(tmp_path / "run")["violations"] == []


def test_pathological_content_round_trips(tmp_path):
    h = Harness(tmp_path / "run")
    from deepreason.programs import content_text
    weird = chr(0x1f4a5) + " " + chr(0x202e) + " " + chr(0) + " tabs\t\n\r end"
    cases = {"unicode": weird, "empty_bytes": b"", "big": ("z" * 200000).encode()}
    ids = {k: h.create_artifact(v).id for k, v in cases.items()}
    h2 = Harness(tmp_path / "run")
    assert content_text(h2.state.artifacts[ids["unicode"]], h2.blobs) == weird
    assert verify_root(tmp_path / "run")["violations"] == []


def test_verify_catches_corruption_but_not_truncation(tmp_path):
    base = tmp_path / "base"
    h = Harness(base)
    h.register_problem(Problem(id="pi", description="d",
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []})))
    good = h.create_artifact("target", problem_id="pi")
    _attack(h, good.id, "x")
    assert verify_root(base)["violations"] == []

    # duplicate seq -> caught
    dup = tmp_path / "dup"; shutil.copytree(base, dup)
    p = dup / "log.jsonl"; lines = p.read_text().splitlines()
    p.write_text("\n".join(lines + [lines[-1]]) + "\n")
    assert verify_root(dup)["violations"], "duplicate seq must be caught"

    # dangling object reference -> caught (open error)
    dang = tmp_path / "dang"; shutil.copytree(base, dang)
    oid = good.id
    (dang / "objects" / f"{sha256_hex(oid.encode())}.json").unlink()
    res = verify_root(dang)
    assert res["violations"], "dangling object reference must be caught"

    # truncation from the end -> valid earlier state, NOT a violation
    trunc = tmp_path / "trunc"; shutil.copytree(base, trunc)
    p = trunc / "log.jsonl"; lines = p.read_text().splitlines()
    p.write_text("\n".join(lines[:-2]) + "\n")
    assert verify_root(trunc)["violations"] == [], "truncation is a valid earlier state"
