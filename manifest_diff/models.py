"""Normalized quantities retain decimal precision and explicit unknowns."""

from __future__ import annotations

from dataclasses import dataclass, fields
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class Resources:
    cpu_millicores: Optional[Decimal] = None
    memory_bytes: Optional[Decimal] = None
    nvidia_gpu: Optional[Decimal] = Decimal(0)
    amd_gpu: Optional[Decimal] = Decimal(0)

    @classmethod
    def zero(cls):
        return cls(*(Decimal(0) for _ in fields(cls)))

    @classmethod
    def unknown(cls):
        return cls(*(None for _ in fields(cls)))

    def scale(self, count: Optional[int]):
        if count is None:
            return self.unknown()
        if count == 0:
            return self.zero()
        return Resources(*(
            None if (value := getattr(self, f.name)) is None else value * count
            for f in fields(self)
        ))

    def minus(self, other: Resources):
        return Resources(*(
            None if (a := getattr(self, f.name)) is None or (b := getattr(other, f.name)) is None
            else a - b for f in fields(self)
        ))


def sum_resources(items):
    totals = []
    for field in fields(Resources):
        values = [getattr(item, field.name) for item in items]
        totals.append(None if any(v is None for v in values) else sum(values, Decimal(0)))
    return Resources(*totals)


@dataclass(frozen=True)
class Container:
    name: str
    requests: Resources
    limits: Resources


@dataclass(frozen=True)
class Workload:
    kind: str
    namespace: str
    name: str
    replicas: Optional[int]
    containers: tuple[Container, ...]
    init_containers: tuple[Container, ...] = ()
    source: str = "<manifest>"

    @property
    def identity(self):
        return self.kind, self.namespace, self.name

    @property
    def warnings(self):
        warnings = []
        if self.kind == "DaemonSet":
            warnings.append("DaemonSet pod count depends on eligible nodes; cluster totals are unavailable.")
        if self.init_containers:
            warnings.append("Init-container scheduling is not modeled; aggregate requests and limits are unavailable.")
        return warnings

    @property
    def per_pod_requests(self):
        return Resources.unknown() if self.init_containers else sum_resources([c.requests for c in self.containers])

    @property
    def per_pod_limits(self):
        return Resources.unknown() if self.init_containers else sum_resources([c.limits for c in self.containers])

    @property
    def total_requests(self):
        return self.per_pod_requests.scale(self.replicas)

    @property
    def total_limits(self):
        return self.per_pod_limits.scale(self.replicas)


@dataclass(frozen=True)
class WorkloadDiff:
    kind: str
    namespace: str
    name: str
    status: str
    before: Optional[Workload]
    after: Optional[Workload]
    requests_delta: Resources
    limits_delta: Resources
    per_pod_requests_delta: Resources
    per_pod_limits_delta: Resources
