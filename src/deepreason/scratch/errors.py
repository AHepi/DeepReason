"""Stable, transport-neutral scratch workspace errors."""

from __future__ import annotations

from typing import Any


class ScratchServiceError(ValueError):
    """An expected scratch API error suitable for CLI and MCP callers."""

    code = "SCRATCH_ERROR"

    def __init__(
        self,
        message: str,
        *,
        location: str = "",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.location = location
        self.details = dict(details or {})
        suffix = f" at {location}" if location else ""
        super().__init__(f"{self.code}{suffix}: {message}")

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "code": self.code,
            "message": str(self).split(": ", 1)[-1],
            "location": self.location,
        }
        if self.details:
            result["details"] = dict(self.details)
        return result


class ScratchBlockNotFound(ScratchServiceError):
    code = "SCRATCH_BLOCK_NOT_FOUND"


class ScratchBlockPrefixAmbiguous(ScratchServiceError):
    code = "SCRATCH_BLOCK_PREFIX_AMBIGUOUS"


class ScratchLinkNotFound(ScratchServiceError):
    code = "SCRATCH_LINK_NOT_FOUND"


class ScratchLinkPrefixAmbiguous(ScratchServiceError):
    code = "SCRATCH_LINK_PREFIX_AMBIGUOUS"


class ScratchClusterNotFound(ScratchServiceError):
    code = "SCRATCH_CLUSTER_NOT_FOUND"


class ScratchClusterPrefixAmbiguous(ScratchServiceError):
    code = "SCRATCH_CLUSTER_PREFIX_AMBIGUOUS"


class ScratchAlreadyMember(ScratchServiceError):
    code = "SCRATCH_ALREADY_MEMBER"


class ScratchNotMember(ScratchServiceError):
    code = "SCRATCH_NOT_MEMBER"


class ScratchLinkRetired(ScratchServiceError):
    code = "SCRATCH_LINK_RETIRED"


class ScratchReadOnly(ScratchServiceError):
    code = "SCRATCH_READ_ONLY"


class ScratchRootBusy(ScratchServiceError):
    code = "SCRATCH_ROOT_BUSY"


class ScratchLimitInvalid(ScratchServiceError):
    code = "SCRATCH_LIMIT_INVALID"


__all__ = [
    "ScratchAlreadyMember",
    "ScratchBlockNotFound",
    "ScratchBlockPrefixAmbiguous",
    "ScratchClusterNotFound",
    "ScratchClusterPrefixAmbiguous",
    "ScratchLimitInvalid",
    "ScratchLinkNotFound",
    "ScratchLinkPrefixAmbiguous",
    "ScratchLinkRetired",
    "ScratchNotMember",
    "ScratchReadOnly",
    "ScratchRootBusy",
    "ScratchServiceError",
]
