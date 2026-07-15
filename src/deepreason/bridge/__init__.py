"""Grounded final-output bridge.

Exports are lazy because the ontology event envelope itself references bridge
events.  Eagerly importing that envelope here creates a package-initialization
cycle for direct ``deepreason.bridge.models`` consumers.
"""

_EVENT_EXPORTS = {"BridgeAction", "BridgeEventPayloadV1"}
_MODEL_EXPORTS = {
    "BridgeOutputV1",
    "BridgeResolution",
    "BridgeValidationFindingV1",
    "BridgeValidationReportV1",
    "ClaimClass",
    "ClaimLedgerEntryV1",
    "ClaimLedgerV1",
    "ClaimUseV1",
    "CorrectionMode",
    "GroundingFindingV1",
    "GroundingReviewV1",
    "GroundingStatus",
    "RenderingMode",
    "SourceConflictV1",
    "UncoveredRequirementV1",
    "UnresolvedItemV1",
}
__all__ = sorted(_EVENT_EXPORTS | _MODEL_EXPORTS)


def __getattr__(name: str):
    if name in _EVENT_EXPORTS:
        # Initializing ontology first lets its Event -> bridge.events edge
        # resolve in the established direction rather than entering through
        # bridge.events -> ontology while both packages are partial.
        from importlib import import_module

        import_module("deepreason.ontology")
        from deepreason.bridge.events import BridgeAction, BridgeEventPayloadV1

        return {
            "BridgeAction": BridgeAction,
            "BridgeEventPayloadV1": BridgeEventPayloadV1,
        }[name]
    if name in _MODEL_EXPORTS:
        from importlib import import_module

        return getattr(import_module("deepreason.bridge.models"), name)
    raise AttributeError(name)
