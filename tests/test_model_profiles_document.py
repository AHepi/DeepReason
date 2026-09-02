"""The model-profile document: one `agent.md`, one machine-readable block.

Operator, 2026-09-01 (CLAUDE.md's request ledger for this tranche,
`experiments/2026-09-01-change-model-profile-registry/REQUEST.md`), verbatim:

    "Would this work for all unknown models as well? Surely creating agent.md
     would be better. Take this particular task out of the hands of the
     machine because we don't really know what future LLMs settings will be?"

and, answering where the document lives and what it is called:

    "model-profiles/glm-5.3/agent.md"

These tests pin the DOCUMENT half of that: what a human may write, and what the
loader is allowed to conclude from it.  The block grammar is TOTAL for the same
reason `docs/map/SCHEMA.md` makes its `check:` grammar total -- a parser free to
guess which of two blocks was meant is how a document comes to say something
nobody wrote.

Tranche: experiments/2026-09-01-change-model-profile-registry/ (S1).
"""

import pytest

from deepreason.model_profiles.document import (
    FENCE_INFO,
    ModelProfileError,
    parse_document,
)


def _document(block: str, *, prose: str = "Notes a human wrote.\n") -> str:
    return f"# a model\n\n{prose}\n```{FENCE_INFO}\n{block}```\n\nMore prose.\n"


MINIMAL = """schema: deepreason-model-profile.v1
model_id: x-1
measured_on: 2026-09-01
"""

FULL = """schema: deepreason-model-profile.v1
model_id: glm-5.3
measured_on: 2026-08-31
reasoning:
  documented_values: [low, high, max]
  extraction_value: low
  thinking_disablable: false
  disabling_values: []
  trace_destination:
    none: content
    low: side_channel
    high: side_channel
context_window_tokens: 131072
max_output_tokens: 32768
can_compact: false
transport_notes:
  - "drops at ~300s at max effort"
evidence:
  - "git show 0123456789abcdef0123456789abcdef01234567:findings.md"
probe: "python scripts/model_profile_probe.py --model glm-5.3"
"""


def test_a_document_is_prose_around_one_declared_block():
    """The prose is for the human; only the fenced block is read."""

    profile = parse_document(_document(MINIMAL))
    assert profile.model_id == "x-1"
    assert profile.measured_on.isoformat() == "2026-09-01"
    # Nothing was inferred from the prose, and absence stays absent rather
    # than acquiring a default the document never declared.
    assert profile.reasoning is None
    assert profile.can_compact is None
    assert profile.context_window_tokens is None


def test_every_declared_field_round_trips():
    profile = parse_document(_document(FULL))
    assert profile.model_id == "glm-5.3"
    assert profile.reasoning.documented_values == ("low", "high", "max")
    assert profile.reasoning.extraction_value == "low"
    assert profile.reasoning.thinking_disablable is False
    assert profile.reasoning.disabling_values == ()
    assert profile.reasoning.trace_destination["none"] == "content"
    assert profile.can_compact is False
    assert profile.transport_notes == ("drops at ~300s at max effort",)
    assert profile.evidence and profile.probe


def test_a_model_id_carrying_a_colon_needs_no_escaping():
    """`deepseek-v4-pro:0813`, `gpt-oss:120b`, `qwen3.5:397b` are real ids.

    The declared id is the key, so a provider's own spelling is never
    translated into a filesystem-safe one that a human would then have to
    reverse.
    """

    block = MINIMAL.replace("model_id: x-1", 'model_id: "gpt-oss:120b"')
    assert parse_document(_document(block)).model_id == "gpt-oss:120b"


def test_no_block_is_a_typed_error_naming_the_fence():
    with pytest.raises(ModelProfileError) as caught:
        parse_document("# a model\n\nall prose, no block.\n")
    assert caught.value.code == "MODEL_PROFILE_NO_BLOCK"
    assert FENCE_INFO in str(caught.value)


def test_two_blocks_are_a_typed_error_rather_than_a_guess():
    """The grammar is total: a second block is never 'probably an example'."""

    doubled = _document(MINIMAL) + f"\n```{FENCE_INFO}\n{FULL}```\n"
    with pytest.raises(ModelProfileError) as caught:
        parse_document(doubled)
    assert caught.value.code == "MODEL_PROFILE_MULTIPLE_BLOCKS"


def test_an_unclosed_block_is_a_typed_error():
    with pytest.raises(ModelProfileError) as caught:
        parse_document(f"# a model\n\n```{FENCE_INFO}\n{MINIMAL}")
    assert caught.value.code == "MODEL_PROFILE_UNCLOSED_BLOCK"


def test_a_fenced_block_of_another_kind_is_not_read():
    """An ordinary ```yaml example in the prose is prose, not a declaration."""

    text = "# a model\n\n```yaml\nmodel_id: decoy\n```\n\n" + _document(MINIMAL)
    assert parse_document(text).model_id == "x-1"


def test_an_undeclared_field_is_refused_rather_than_ignored():
    """`extra="forbid"`: a typo must not become silence.

    A field the loader ignores is a claim the author believes is being read
    and is not -- the failure mode this whole tranche exists to end.
    """

    with pytest.raises(ModelProfileError) as caught:
        parse_document(_document(MINIMAL + "reasoning_effort: low\n"))
    assert caught.value.code == "MODEL_PROFILE_INVALID"


def test_a_block_that_is_not_a_mapping_is_a_typed_error():
    with pytest.raises(ModelProfileError) as caught:
        parse_document(_document("- just\n- a\n- list\n"))
    assert caught.value.code == "MODEL_PROFILE_MALFORMED"


def test_a_missing_measured_on_is_refused():
    """A profile with no date cannot go stale, which is the point of the date."""

    block = "\n".join(
        line for line in MINIMAL.splitlines() if not line.startswith("measured_on")
    ) + "\n"
    with pytest.raises(ModelProfileError) as caught:
        parse_document(_document(block))
    assert caught.value.code == "MODEL_PROFILE_INVALID"


def test_the_digest_covers_the_declared_content_and_not_the_prose():
    """Two documents with different prose and the same block are the same
    profile: the digest is what the record stamps, so it must not move when a
    human rewords a sentence."""

    a = parse_document(_document(FULL, prose="one wording\n"))
    b = parse_document(_document(FULL, prose="an entirely different wording\n"))
    assert a.digest == b.digest and len(a.digest) == 64

    changed = parse_document(_document(FULL.replace("extraction_value: low", "extraction_value: high")))
    assert changed.digest != a.digest
