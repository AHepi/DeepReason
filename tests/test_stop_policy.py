from deepreason.runtime.stop import StopController, StopMetrics, StopPolicy


def _metric(cycle, **updates):
    return StopMetrics(cycle=cycle, **updates)


def test_convergence_requires_sustained_windows():
    controller = StopController(
        StopPolicy(min_cycles=1, window=2, stable_windows=2)
    )
    assert not controller.evaluate(_metric(1)).stop
    assert not controller.evaluate(_metric(2)).stop
    assert controller.evaluate(_metric(3)).reason == "converged"


def test_stuck_signal_alone_cannot_stop():
    controller = StopController(
        StopPolicy(window=2, stable_windows=99, stuck_signal_window=2, escape_attempts=0)
    )
    for cycle in range(5):
        decision = controller.evaluate(_metric(cycle, stuck_signal=True))
    assert not decision.stop


def test_corroborated_stuck_exhausts_fixed_escape_ladder_before_stop():
    controller = StopController(
        StopPolicy(window=2, stable_windows=99, stuck_signal_window=2, escape_attempts=0)
    )
    actions = []
    decision = None
    for cycle in range(10):
        decision = controller.evaluate(
            _metric(cycle, stuck_signal=True, gate_orbit=True)
        )
        if decision.escape_action:
            actions.append(decision.escape_action)
        if decision.stop:
            break
    assert len(actions) == 5
    assert decision.reason == "stuck"
