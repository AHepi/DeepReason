import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "jolt_trigger_glm52_pilot.py"
SPEC = importlib.util.spec_from_file_location("jolt_glm52_pilot", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_selection_evaluator_accepts_only_frozen_domain():
    assert MODULE._selection('{"selection":[1,4,7,12,16,20],"rationale":"x"}') == (1, 4, 7, 12, 16, 20)
    assert MODULE._selection('{"selection":[1,2,7,14,16,20]}') is None
    assert MODULE._selection('{"selection":[1,4,7,12,16,19]}') is None
    assert MODULE._selection('not json') is None


def test_pilot_config_has_only_thinking_disabled_conjecturer():
    cfg = MODULE.config()
    assert set(cfg.roles) == {"conjecturer"}
    route = cfg.roles["conjecturer"]
    assert route["model"] == "glm-5.2"
    assert route["reasoning"] == "none"
    assert cfg.ARG_CRIT_PER_CYCLE == 0
    assert cfg.ADVISORY_TRIALS_PER_CYCLE == 0


def test_mechanism_classes_are_deterministic():
    assert MODULE._mechanism((1, 4, 7, 12, 16, 20)) == "low-start"
    assert MODULE._mechanism((4, 7, 10, 12, 13, 14)) == "middle-start"
    assert MODULE._mechanism((7, 9, 11, 13, 15, 17)) == "high-start"
