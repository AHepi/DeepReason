"""Process-only MiniReason reporting helpers.

These functions may rank or summarize an already-created record.  They never
participate in artifact admission, registration, status, or adjudication.
"""

import re


def normalize(text: str) -> frozenset[str]:
    """Return normalized tokens for offline diversity diagnostics."""
    return frozenset(re.findall(r"[a-z0-9]+", text.lower()))
