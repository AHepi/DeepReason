"""Build a run's section plan from the receipts a renderer produced.

Shared by the two seats that render a brief, so neither reimplements the
mapping and the record cannot disagree with the pack. Kept out of `conj.py`
and `crit.py` for the same reason the walk is kept out of both renderers.
"""

from __future__ import annotations


def section_plans(transaction_service, preparation, receipts) -> tuple:
    """Zero plans when nothing rendered, one otherwise.

    A plan for a pack with no sections would be a record row asserting an
    absence the pack already shows, so the empty case writes nothing.
    """

    if not receipts:
        return ()
    from deepreason.llm.seat_sections import resolve_seat_pack_layout, resolve_seat_shell

    seat = getattr(preparation, "template_role", None) or "conjecturer"
    try:
        shell = resolve_seat_shell(seat)
        shell_id, layout = shell.shell_id, resolve_seat_pack_layout(seat)
    except Exception:
        # A seat with no registered shell still gets its sections recorded:
        # the plan is about what rendered, not about what configured it.
        shell_id, layout = "", None
    return (
        transaction_service.section_plan(
            preparation,
            layout_id=layout.layout_id if layout is not None else "",
            layout_version=layout.layout_version if layout is not None else "1.0.0",
            shell_id=shell_id,
            receipts=receipts,
        ),
    )
