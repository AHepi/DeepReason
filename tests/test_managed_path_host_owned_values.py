"""Regression (brief-variation arms A0/A1/A1P/A2/A3, run-fe00609058e10605590206d51ab2b7a0):
the managed path must not replace an operator's stated value in silence.

Those five roots compiled `scratch_policy.embedder_model = null`,
`embedder_backend = "deterministic_hashing"` with `compile_notices` empty, and
stamped `["embedder","hashing-128",...]` at seq 8 — so every distance reading
they carry is on the hashing scale, and no record says a configured value was
dropped. The cause is `preparation._config_for_profile`'s `owned` dictionary,
which takes SEVEN values whatever the operator's configuration says, before the
compiler — whose own disclosure channel therefore has nothing left to disclose
(`experiments/2026-09-10-defect-managed-path-host-owned-overrides/DIAGNOSIS.md`).

Operator law this enforces (CLAUDE.md, 2026-08-28, verbatim): "configuration of
seats need to be able to turn gates on and off at will ... Gates are always
optional: with warnings."
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from deepreason.application.results import embedder_line, embedder_summary_for_root
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.ops import make_embedder
from deepreason.preparation import (
    build_preparation_manifest,
    engaged_bridge_source,
    engaged_scratchpad_source,
)
from deepreason.provider_profile import ProviderProfileV1
from deepreason.qualification import qualification_subject_digest
from deepreason.run_manifest import config_from_run_manifest
from deepreason.scheduler.scheduler import Scheduler

STAMP = datetime(2026, 7, 23, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
DISCLOSURE = "ENGINE_CONFIG_FIELD_NOT_CARRIED"
NEURAL = "nomic-ai/nomic-embed-text-v1.5"

# The seven `preparation._config_for_profile` owns. `EMBEDDER_MODEL` is the one
# this tranche made carryable; the other six stay host-owned and are disclosed.
HOST_OWNED = (
    "engine_profile",
    "model_profile",
    "scratchpad",
    "bridge",
    "EMBEDDER_MODEL",
    "CHANNELS_DISABLED",
    "roles",
)
CARRIED = ("EMBEDDER_MODEL",)
DISCLOSED = tuple(name for name in HOST_OWNED if name not in CARRIED)


def _profile() -> ProviderProfileV1:
    return ProviderProfileV1.create(
        provider="openai",
        endpoint="https://api.example.com/v1",
        model_id="model-a",
        model_revision="rev-a",
        family="family-a",
        context_window_tokens=262144,
        maximum_completion_tokens=4096,
        credential_env="DEEPREASON_TEST_KEY",
    )


def _stated(name: str):
    """One value per host-owned field, stated AWAY from the host's own.

    `scratchpad` and `bridge` start from the host's OWN preset and move one
    field, so neither can pass by accidentally matching a code default the
    managed path never uses.
    """

    if name == "engine_profile":
        return "mini"
    if name == "model_profile":
        return "frontier"
    if name == "EMBEDDER_MODEL":
        return NEURAL
    if name == "CHANNELS_DISABLED":
        return ["simulation"]
    if name == "roles":
        return {
            "conjecturer": {
                "provider": "openai",
                "model": "model-z",
                "endpoint": "https://elsewhere.example/v1",
            }
        }
    if name == "scratchpad":
        value = dict(engaged_scratchpad_source())
        value["similarity_top_k"] = 13
        return value
    if name == "bridge":
        value = dict(engaged_bridge_source())
        value["output_section_limit"] = 6
        return value
    raise AssertionError(name)


def _config(**stated) -> Config:
    """Build the operator's configuration the way `load()` does.

    `model_validate` on a partial mapping, never `Config(**everything)`: the
    fix reads `model_fields_set` to tell a value the operator STATED from the
    shipped default, and `Config().EMBEDDER_MODEL` is the neural model, so the
    two are indistinguishable by value.
    """

    return Config.model_validate(dict(stated))


def _managed(config: Config | None):
    kwargs = {} if config is None else {"config": config}
    return build_preparation_manifest(
        _profile(), question="Why is the sky blue?", compiled_at=STAMP, **kwargs
    )


def _pointers(manifest) -> set[str]:
    return {
        notice.pointer
        for notice in (manifest.compile_notices or ())
        if notice.code == DISCLOSURE
    }


@pytest.mark.parametrize("name", HOST_OWNED)
def test_every_host_owned_value_is_carried_or_disclosed(name):
    """The disjunction the 2026-08-28 law requires, over the seven it was
    silent about. A row that is neither is the defect the five arms carry."""

    stated = _stated(name)
    manifest = _managed(_config(**{name: stated}))
    runtime = config_from_run_manifest(manifest)
    operator = _config(**{name: stated})

    carried = getattr(runtime, name) == getattr(operator, name)
    disclosed = f"/engine_config/{name}" in _pointers(manifest)
    assert carried or disclosed, (
        f"{name} is neither carried into the run nor disclosed as taken by the "
        f"host: the operator stated {stated!r} and the run got "
        f"{getattr(runtime, name)!r} with no notice naming it"
    )


@pytest.mark.parametrize("name", DISCLOSED)
def test_a_disclosed_value_is_named_exactly_once_and_never_restored(name):
    """Six stay host-owned, and the notice must NOT be a road back.

    `roles` and `model_profile` bind the endpoint and the credential: a notice
    carrying the operator's value would be restored by
    `_carried_config_values` and would redirect a managed run to another
    endpoint, which is the hole the override exists to close. `value is None`
    is what keeps the disclosure a disclosure.
    """

    stated = _stated(name)
    manifest = _managed(_config(**{name: stated}))
    named = [
        notice
        for notice in (manifest.compile_notices or ())
        if notice.pointer == f"/engine_config/{name}"
    ]
    assert len(named) == 1, f"{name}: expected one notice, got {named}"
    assert named[0].code == DISCLOSURE
    assert named[0].value is None, (
        f"{name}: a disclosure that carries a value is restored at run time; "
        "the host must keep this one"
    )
    runtime = config_from_run_manifest(manifest)
    assert getattr(runtime, name) != getattr(_config(**{name: stated}), name), (
        f"{name} reached the run after all: the notice says the host took it"
    )


def test_a_stated_embedder_reaches_the_compiled_run():
    """The arms' exact condition, and the test they would have failed."""

    manifest = _managed(_config(EMBEDDER_MODEL=NEURAL))
    assert manifest.scratch_policy.embedder_backend == "neural"
    assert manifest.scratch_policy.embedder_model == NEURAL
    assert config_from_run_manifest(manifest).EMBEDDER_MODEL == NEURAL
    assert "/engine_config/EMBEDDER_MODEL" not in _pointers(manifest), (
        "a carried value needs no disclosure; a notice here would also be a "
        "road back into the qualification subject"
    )


def test_a_stated_embedder_is_what_the_run_measures_with(tmp_path, monkeypatch):
    """End to end on the reader `deepreason results` calls.

    The neural backend is stubbed so the assertion is about CARRIAGE, not about
    whether this container's weight cache is warm: a run whose geometry
    depended on the cache would have made run identity depend on the machine.
    """

    from deepreason.llm import embedder as embedder_module

    class _Stub:
        model = NEURAL

        def fingerprint(self):
            return {"model": NEURAL, "version": "stub-1", "sentinel": "0" * 16}

    monkeypatch.setattr(embedder_module, "build_embedder", lambda model: _Stub())

    manifest = _managed(_config(EMBEDDER_MODEL=NEURAL))
    runtime = config_from_run_manifest(manifest)
    harness = Harness(tmp_path / "root")
    embedder = make_embedder(harness, runtime)
    scheduler = Scheduler(harness, None, runtime, embedder=embedder)
    fingerprint = scheduler._embedder_fingerprint()
    harness.record_measure(
        inputs=[
            "embedder",
            fingerprint["model"],
            fingerprint["version"],
            fingerprint["sentinel"],
        ]
    )

    kinds = [
        str(event.inputs[0])
        for event in harness.log.read()
        if event.inputs and str(event.inputs[0]).startswith("embedder")
    ]
    assert "embedder-unconfigured" not in kinds, (
        "the run reported no embedder in its compiled configuration, which is "
        "the silent drop this tranche removed"
    )
    summary = embedder_summary_for_root(tmp_path / "root")
    assert summary["backend"] == "neural"
    assert summary["model"] == NEURAL
    assert NEURAL in embedder_line(summary)


def test_a_configuration_that_states_nothing_changes_nothing():
    """The half that must NOT move: reading a configuration costs no battery.

    `Config().EMBEDDER_MODEL` is the neural model, so a fix comparing values
    instead of reading `model_fields_set` would carry it here and move every
    existing home's qualification subject.
    """

    baseline = _managed(None)
    empty = _managed(_config())
    assert empty.sha256 == baseline.sha256
    assert empty.source_config_hash == baseline.source_config_hash
    assert not (empty.compile_notices or ())
    assert empty.scratch_policy.embedder_backend == "deterministic_hashing"


@pytest.mark.parametrize("name", DISCLOSED)
def test_a_disclosed_value_moves_no_qualification_subject_digest(name):
    """The disclosure rides a code `qualification_subject_payload` strips.

    Fifteen committed run-configs name `roles` alone. A notice under a NEW code
    would enter the subject and cost every home a ~14-minute battery for a run
    that compiles identically — the waste the 2026-08-28 grant to frozen
    surface 5 exists to prevent.
    """

    profile = _profile()
    baseline = qualification_subject_digest(_managed(None), profile)
    disclosed = _managed(_config(**{name: _stated(name)}))
    assert f"/engine_config/{name}" in _pointers(disclosed)
    assert qualification_subject_digest(disclosed, profile) == baseline


def test_a_stated_embedder_moves_its_own_subject_digest_and_that_is_the_price():
    """The one digest that DOES move, stated where a reader meets it.

    A configuration naming an embedder compiles a different scratch policy, so
    it is a different subject and that home owes one battery (~14 minutes).
    That is the configuration taking effect, not a code change moving what
    enters the digest — the distinction frozen surface 5 turns on.
    """

    profile = _profile()
    baseline = qualification_subject_digest(_managed(None), profile)
    neural = _managed(_config(EMBEDDER_MODEL=NEURAL))
    assert qualification_subject_digest(neural, profile) != baseline
    assert json.loads(neural.engine_config_json)["EMBEDDER_MODEL"] == NEURAL


def test_appending_the_disclosure_changes_the_manifest_in_one_field_only():
    """The re-validation must not quietly rewrite anything else.

    `build_preparation_manifest` returns the compiled manifest re-validated
    with the host notices appended. A round trip through `model_dump` and
    `model_validate` that normalised any other field would change what the run
    binds while looking like a disclosure, so the difference is pinned rather
    than trusted: exactly one key moves, and it is `compile_notices`.
    """

    baseline = _managed(None).model_dump(mode="json")
    disclosed = _managed(_config(engine_profile="mini")).model_dump(mode="json")
    moved = {
        key
        for key in set(baseline) | set(disclosed)
        if baseline.get(key) != disclosed.get(key)
    }
    assert moved == {"compile_notices"}, moved
    # Absent, not null: the field is dropped from the dump when there are no
    # notices, which is why appending to it cannot disturb the baseline bytes.
    assert "compile_notices" not in baseline
    assert [n["code"] for n in disclosed["compile_notices"]] == [DISCLOSURE]
    assert "value" not in disclosed["compile_notices"][0]
