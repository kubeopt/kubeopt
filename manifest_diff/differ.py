"""Compare workload identity and normalized resource specifications."""

from .models import Resources, WorkloadDiff
from .parser import ManifestError


def _index(workloads):
    result = {}
    for workload in workloads:
        if workload.identity in result:
            raise ManifestError(f"Duplicate workload: {'/'.join(workload.identity)}")
        result[workload.identity] = workload
    return result


def diff_workloads(before, after) -> list[WorkloadDiff]:
    old, new = _index(before), _index(after)
    result = []
    for key in sorted(old.keys() | new.keys()):
        a, b = old.get(key), new.get(key)
        if a and b and (a.replicas, a.containers, a.init_containers) == (b.replicas, b.containers, b.init_containers):
            continue
        status = "added" if a is None else "removed" if b is None else "modified"
        deltas = []
        for attr in ("total_requests", "total_limits", "per_pod_requests", "per_pod_limits"):
            before_resources = getattr(a, attr) if a else Resources.zero()
            after_resources = getattr(b, attr) if b else Resources.zero()
            deltas.append(after_resources.minus(before_resources))
        result.append(WorkloadDiff(*key, status, a, b, *deltas))
    return result
