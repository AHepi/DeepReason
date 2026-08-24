"""Shared harness fixture for T3 tests.

Matches the definition in INPUT_conftest.txt.
"""

import pytest

from deepreason.harness import Harness


@pytest.fixture
def harness(tmp_path) -> Harness:
    """Create a fresh Harness rooted at a temporary directory."""
    return Harness(tmp_path / "run")
