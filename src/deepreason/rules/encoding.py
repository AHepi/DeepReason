"""Encoder-role delegation (D2 rev 2, Item 7, R38).

The coder seat authors commitment CODE for the conjecturer's ALREADY-
ADMITTED prose — never a separate encoding artifact (rev 1's rejected
framing), never a new conjecture. Two-phase: the conjecturer's own turn
supplies the claim/mechanism prose first, exactly as today; only THEN,
if the ``"coder"`` seat is bound, does a follow-up call to the
``"encoder"`` role draft the checker source. ``"encoder"`` reuses
``property_designer``'s own configured endpoint via ``template_role``
(``llm/roles.py``'s own documented pattern for an auxiliary contract) —
sharing the SAME seat binding (``seat_bindings.GROUP_ROLES["coder"]``)
rather than registering a new, independently-routable role, so this
needs no new manifest role/route entry (R30's frozen-surface forecast).
"""


def draft_encoded_commitment(harness, adapter, conjecture_claim: str, conjecture_mechanism: str) -> dict | None:
    """Delegate authoring one commitment's checker source to the encoder
    (R38). Returns a ``{"source", "entry", "tests"}`` draft — the SAME
    shape ``ForbiddenCase.checker_spec``/``Countercondition.checker_spec``
    already carry (D2 rev 2 Item 2) — ready for the caller to attach via
    the existing two-phase draft/register compilation path
    (``compile_interface_draft``, unchanged).

    Returns ``None`` when the ``"coder"`` seat is not bound
    (``adapter.has_role("property_designer")`` is the SAME check
    ``rules/experiment.py::_property_step`` already uses, since
    ``"encoder"`` shares that seat's binding, not an independent one).
    This is the fallback's entire body: the caller's own Item 2 inline
    mechanism (the conjecturer embeds ``checker_spec`` itself) is
    untouched, a no-op from here."""
    if not adapter.has_role("property_designer"):
        return None

    from deepreason.llm.contracts import EncoderOutput

    pack = "\n".join([
        "CONJECTURE'S OWN EXPLANATION (already admitted; add no new claim):",
        f"claim: {conjecture_claim}",
        f"mechanism: {conjecture_mechanism}",
    ])
    output, llm_call = adapter.call(
        "property_designer", pack, EncoderOutput, template_role="encoder"
    )
    harness.record_llm_calls([llm_call], "encoder-delegation")
    return {
        "source": output.source,
        "entry": output.entry,
        "tests": [t.model_dump(mode="json", by_alias=True) for t in output.tests],
    }
