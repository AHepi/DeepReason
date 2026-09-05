"""The mini form registry, and the STORED default that must not move.

Implements S2 (R2, R7, R-stored, C1, C9) of the mini isolation programme.

R-stored is the operator's own instruction of 2026-09-05: "For now, the
current default conjecture form needs stored but not deleted." Everything else
in this file is about relaxing what a mini seat may say; this first test is
about the one form that may not change while that happens.
"""

import json
import pathlib

_GOLDEN = pathlib.Path(__file__).parent / "goldens" / "mini_stored_conjecturer_form.json"


def test_the_stored_form_is_byte_identical():
    """R-stored: the current default conjecture form is STORED, not deleted.

    The golden is the whole contract as a mini run sees it -- its id, its
    variant, the names of both models, and the complete JSON Schema a seat is
    shown. Comparing the rendered BYTES rather than a field or two is
    deliberate: a form is what the model is asked for, and a change anywhere
    in that schema is a change to the question, however small it looks in a
    diff.
    """
    from deepreason.llm.wire import ReferenceFreeConjecturerWireContract

    contract = ReferenceFreeConjecturerWireContract()
    rendered = (
        json.dumps(
            {
                "contract_id": contract.contract_id,
                "variant": contract.variant,
                "wire_model": contract.wire_model.__name__,
                "canonical_model": contract.canonical_model.__name__,
                "schema": contract.model_json_schema(),
            },
            sort_keys=True,
            indent=2,
        )
        + "\n"
    )
    assert rendered == _GOLDEN.read_text(encoding="utf-8"), (
        "the stored default conjecture form moved; R-stored says it is stored, "
        "not changed. If a new form is wanted, REGISTER ONE BESIDE IT."
    )
