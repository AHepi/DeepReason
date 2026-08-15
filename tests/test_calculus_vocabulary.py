"""The stored vocabulary and the rendered vocabulary are different, on purpose.

Regression (v2 calculus program, Rung 1): the calculus names the grounded-
extension label ``unrefuted`` deliberately (COMPUTABLE_CALCULUS §6) because
"accepted" invites a reader to supply endorsement the label does not carry --
the same misreading spec v1.7 §E's ``adjudication-blindness`` check exists to
warn about. Rung 1 adopts the calculus vocabulary at the VIEW layer only.

The line these tests pin: a string WRITTEN INTO A ROOT stays ``accepted``; a
string RENDERED TO A READER says ``unrefuted``. Break either half and every
committed root either changes meaning or stops being readable.
"""

from deepreason.ontology import Status
from deepreason.status_display import display_status, display_status_counts, status_gloss
from deepreason.views.theory import theory
from deepreason.views.why import why


def test_stored_labels_are_unchanged():
    """The four historical strings, exactly. Committed roots hold these bytes."""
    assert Status.ACCEPTED.value == "accepted"
    assert {s.value for s in Status} == {
        "accepted", "refuted", "suspended", "suspended_unsupported"
    }


def test_ontology_never_learns_the_rendered_word():
    """The rendered vocabulary must not leak into the stored enum."""
    import importlib
    import pathlib

    module = importlib.import_module(Status.__module__)
    assert "unrefuted" not in pathlib.Path(module.__file__).read_text()


def test_display_maps_accepted_to_unrefuted_on_every_profile():
    """Profile-independent: the calculus does not vary its vocabulary by workload.

    The previous mapping rendered ACCEPTED as "standing" for text runs, which is
    the calculus's word for the OTHER axis (frame role, §9.1). Rung 4 introduces
    that axis; the label had to be freed before it arrives.
    """
    for profile in (None, "text", "formal"):
        assert display_status(Status.ACCEPTED, profile) == "unrefuted"
    assert display_status(Status.REFUTED, "text") == "refuted"
    assert display_status(Status.SUSPENDED_UNSUPPORTED, "text") == "suspended_unsupported"
    assert display_status(Status.ACCEPTED) == "unrefuted"


def test_every_status_has_a_gloss():
    """A label without its meaning is what produced the misreading in the first place."""
    for status in Status:
        assert status_gloss(status), status
    assert "not false" in status_gloss(Status.SUSPENDED_UNSUPPORTED)


def _accepted_artifact(harness):
    a = harness.create_artifact("a claim that survives", codec="utf8")
    return a


def test_views_render_the_calculus_vocabulary(harness):
    """theory() and why() are reader surfaces, so they render `unrefuted`."""
    a = _accepted_artifact(harness)
    assert harness.state.status.get(a.id) == Status.ACCEPTED

    rendered = theory(a.id, harness.state, harness.blobs)
    assert "[unrefuted]" in rendered
    assert "[accepted]" not in rendered

    chain = why(a.id, harness.state)
    assert "[unrefuted]" in chain
    assert "'unrefuted' (stored 'accepted')" in chain


def test_display_status_counts_use_the_rendered_vocabulary(harness):
    _accepted_artifact(harness)
    counts = display_status_counts(harness, workload_profile="text")
    assert counts.get("unrefuted") == 1
    assert "standing" not in counts
    assert "accepted" not in counts


def test_machine_json_keeps_the_stored_key():
    """`positions.accepted` is a machine key readers compare across roots.

    v1.7 §E names it explicitly ("a reader of positions.accepted MUST consult
    this finding"), so the key is load-bearing across every committed root.
    The rendered vocabulary must not reach it.
    """
    import pathlib

    from deepreason import findings

    text = pathlib.Path(findings.__file__).read_text()
    assert '"accepted": [], "refuted": [], "suspended": [],' in text
    assert "unrefuted" not in text
