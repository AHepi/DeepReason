"""Workload adapters share one graph engine and one deterministic scheduler."""

from __future__ import annotations

from typing import Protocol


class WorkloadAdapter(Protocol):
    profile: str

    def completion(self, root) -> bool: ...


class WorkloadRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, WorkloadAdapter] = {}

    def register(self, adapter: WorkloadAdapter) -> None:
        if adapter.profile in self._adapters:
            raise ValueError(f"workload adapter already registered: {adapter.profile}")
        self._adapters[adapter.profile] = adapter

    def get(self, profile: str) -> WorkloadAdapter:
        try:
            return self._adapters[profile]
        except KeyError as error:
            raise ValueError(f"unknown workload profile: {profile}") from error


WORKLOADS = WorkloadRegistry()
