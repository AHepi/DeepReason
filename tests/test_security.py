"""Security regression: predicate eval() RCE (found by the stress campaign).

An LLM-generated skeleton candidate's forbidden case carried an eval string
copied verbatim into a registered Commitment; a `predicate:` there put
attacker-controlled text into programs.evaluate's eval(), which escapes the
__builtins__={} sandbox via the object-subclasses walk — arbitrary code
execution reachable from ordinary criticism. Two layers now block it:
untrusted forbidden cases may not carry a predicate at all, and the
predicate evaluator rejects dunder access even for trusted predicates."""

import json

import pytest

from deepreason.harness import Harness
from deepreason.informal.skeleton import (
    parse_skeleton,
    skeleton_wf_commitment,
)
from deepreason.ontology import Commitment
from deepreason.programs import UnsafePredicate, _validate_predicate, evaluate

ESCAPE = (
    "predicate:[c for c in ().__class__.__base__.__subclasses__() "
    "if c.__name__=='catch_warnings'][0]()._module.__builtins__"
    "['open']({path!r},'w').write('pwned') or len(content) >= 0"
)


def _malicious_skeleton(payload: str) -> str:
    return json.dumps({
        "claim": "benign", "mechanism": "benign",
        "scope": {"covers": [], "excludes": []},
        "forbidden": [{"case": "x", "eval": payload}],
        "prose_notes": "n"})


def test_layer1_skeleton_rejects_predicate_forbidden_eval(tmp_path):
    """Untrusted skeleton content with a predicate forbidden-eval must fail
    to parse — so it never registers a dangerous commitment."""
    payload = ESCAPE.format(path=str(tmp_path / "pwned.txt"))
    assert parse_skeleton(_malicious_skeleton(payload)) is None
    # A rubric forbidden-eval (the legitimate form) still parses.
    ok = _malicious_skeleton("rubric:std-hist")
    assert parse_skeleton(ok) is not None


def test_layer1_full_crit_path_no_execution(tmp_path):
    """Even driving the exact conj->crit path, no code executes."""
    sentinel = tmp_path / "pwned.txt"
    payload = ESCAPE.format(path=str(sentinel))
    h = Harness(tmp_path / "run")
    h.register_commitment(skeleton_wf_commitment())
    sk = parse_skeleton(_malicious_skeleton(payload))
    assert sk is None  # blocked before compilation even begins


def test_layer2_direct_predicate_eval_is_sandboxed(tmp_path):
    """Defense-in-depth: if a predicate reaches evaluate() by any path
    (e.g. an operator commitment), the escape still cannot execute."""
    sentinel = tmp_path / "pwned2.txt"
    payload = ESCAPE.format(path=str(sentinel))
    h = Harness(tmp_path / "run")
    art = h.create_artifact("some content here")
    kappa = Commitment(id="k-evil", eval=payload)
    verdict, trace = evaluate(kappa, h.state.artifacts[art.id], h.blobs)
    assert verdict == "fail"
    assert "dunder" in trace["error"]
    assert not sentinel.exists()


def test_validate_predicate_blocks_escapes_allows_legit():
    for bad in [
        "().__class__.__bases__[0]",
        "''.__class__.__mro__",
        "[c for c in ().__class__.__base__.__subclasses__()]",
        "__import__('os')",
        "9**9**9",
    ]:
        with pytest.raises(UnsafePredicate):
            _validate_predicate(bad)
    for good in [
        "len(content) > 120",
        "'moon' in content.lower()",
        "('moon' in content.lower() or 'lunar' in content.lower())",
        "all(len(w) > 0 for w in content.split())",
        "sum(1 for c in content if c.isdigit()) > 3",
    ]:
        _validate_predicate(good)  # must not raise
