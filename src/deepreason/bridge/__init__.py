"""Grounded final-output bridge.

Only the typed process-event envelope is introduced at C2.  Claim-ledger and
composition semantics are added at their later commit boundaries.
"""

from deepreason.bridge.events import BridgeAction, BridgeEventPayloadV1

__all__ = ["BridgeAction", "BridgeEventPayloadV1"]
