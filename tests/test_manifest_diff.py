"""Manifest resource comparisons must preserve unknowns and Kubernetes units."""

from decimal import Decimal

import pytest

from manifest_diff.parser import ManifestError, parse_manifests, parse_quantity
from manifest_diff.differ import diff_workloads


def workload(*, name="api", replicas=2, cpu="250m", memory="128Mi", kind="Deployment"):
    return f"""apiVersion: apps/v1
kind: {kind}
metadata:
  name: {name}
spec:
  replicas: {replicas}
  template:
    spec:
      containers:
      - name: app
        resources:
          requests:
            cpu: {cpu}
            memory: {memory}
"""


@pytest.mark.parametrize("raw, expected", [
    ("250m", "0.250"), ("1", "1"), ("1e-3", "0.001"),
    ("128Mi", "134217728"), ("1G", "1000000000"),
    ("1.5Gi", "1610612736"), ("100n", "0.000000100"),
])
def test_quantities(raw, expected):
    assert parse_quantity(raw) == Decimal(expected)


@pytest.mark.parametrize("raw", ["NaN", "inf", "-1", "1foo", True])
def test_invalid_quantities_fail(raw):
    with pytest.raises(ManifestError):
        parse_quantity(raw)


def test_multidocument_and_non_kubernetes_yaml():
    parsed = parse_manifests("setting: value\n---\n" + workload() + "---\n" + workload(name="worker", kind="StatefulSet"))
    assert len(parsed) == 2
    assert parsed[0].namespace == "default"
    assert parsed[0].containers[0].requests.cpu_millicores == Decimal(250)
    assert parsed[0].containers[0].requests.memory_bytes == Decimal(134217728)


def test_gpu_limit_defaults_to_request_but_missing_cpu_stays_unknown():
    manifest = """apiVersion: apps/v1
kind: Deployment
metadata: {name: inference}
spec:
  template:
    spec:
      containers:
      - name: server
        resources:
          limits: {nvidia.com/gpu: 1, amd.com/gpu: 2}
"""
    parsed = parse_manifests(manifest)[0]
    assert parsed.replicas == 1
    assert parsed.containers[0].requests.nvidia_gpu == 1
    assert parsed.containers[0].requests.amd_gpu == 2
    assert parsed.containers[0].requests.cpu_millicores is None


@pytest.mark.parametrize("manifest", [
    "kind: [broken", workload(replicas=-1), workload(replicas="1.5"),
    workload(cpu="banana"), workload() + "metadata: {name: duplicate}\n",
])
def test_invalid_manifests_fail_with_source(manifest):
    with pytest.raises(ManifestError, match="app.yaml"):
        parse_manifests(manifest, source="app.yaml")


def test_replica_change_scales_requests_and_limits():
    before = parse_manifests(workload())
    after = parse_manifests(workload(replicas=3))
    changes = diff_workloads(before, after)
    assert len(changes) == 1
    assert changes[0].status == "modified"
    assert changes[0].requests_delta.cpu_millicores == 250
    assert changes[0].requests_delta.memory_bytes == 134217728
    assert changes[0].limits_delta.cpu_millicores is None


def test_equivalent_units_and_file_moves_do_not_change_resources():
    before = parse_manifests(workload(cpu="1000m", memory="1Gi"), source="old.yaml")
    after = parse_manifests(workload(cpu="1", memory="1024Mi"), source="new.yaml")
    assert diff_workloads(before, after) == []


def test_added_and_removed_workloads():
    parsed = parse_manifests(workload())
    added = diff_workloads([], parsed)[0]
    removed = diff_workloads(parsed, [])[0]
    assert added.status == "added"
    assert added.requests_delta.cpu_millicores == 500
    assert removed.status == "removed"
    assert removed.requests_delta.cpu_millicores == -500


def test_zero_replicas_means_zero_requested_capacity():
    before = parse_manifests(workload(replicas=0))
    after = parse_manifests(workload(replicas=1))
    assert diff_workloads(before, after)[0].requests_delta.cpu_millicores == 250


def test_daemonset_has_per_pod_delta_and_unknown_cluster_total():
    before = parse_manifests(workload(kind="DaemonSet"))
    after = parse_manifests(workload(kind="DaemonSet", cpu="500m"))
    change = diff_workloads(before, after)[0]
    assert before[0].replicas is None
    assert change.requests_delta.cpu_millicores is None
    assert change.per_pod_requests_delta.cpu_millicores == 250


def test_duplicate_workload_identity_is_an_error():
    parsed = parse_manifests(workload())
    with pytest.raises(ManifestError, match="Duplicate workload"):
        diff_workloads(parsed + parsed, [])


def test_container_changes_with_same_total_are_still_reported():
    before = parse_manifests(workload())
    after = parse_manifests(workload().replace("name: app", "name: replacement"))
    assert len(diff_workloads(before, after)) == 1


def test_init_containers_prevent_incorrect_total():
    manifest = workload().replace(
        "      containers:",
        "      initContainers:\n      - name: setup\n        resources:\n          requests: {cpu: '2', memory: 1Gi}\n      containers:",
    )
    parsed = parse_manifests(manifest)[0]
    assert parsed.total_requests.cpu_millicores is None
    assert parsed.warnings


def test_cpu_rejects_sub_millicore_precision():
    with pytest.raises(ManifestError, match="millicore precision"):
        parse_manifests(workload(cpu="0.0001"))


def test_multiple_containers_are_summed():
    manifest = workload() + """      - name: sidecar
        resources:
          requests: {cpu: 100m, memory: 32Mi}
"""
    parsed = parse_manifests(manifest)[0]
    assert parsed.total_requests.cpu_millicores == 700
    assert parsed.total_requests.memory_bytes == 335544320


def test_limit_only_change_is_reported():
    manifest = workload() + "          limits: {cpu: '1', memory: 256Mi}\n"
    changed = manifest.replace("limits: {cpu: '1'", "limits: {cpu: '2'")
    change = diff_workloads(parse_manifests(manifest), parse_manifests(changed))[0]
    assert change.requests_delta.cpu_millicores == 0
    assert change.limits_delta.cpu_millicores == 2000


def test_fractional_gpu_is_rejected():
    manifest = workload() + "          limits: {nvidia.com/gpu: 0.5}\n"
    with pytest.raises(ManifestError, match="whole numbers"):
        parse_manifests(manifest)


def test_kubernetes_list_is_supported():
    import yaml

    contents = yaml.safe_dump({"apiVersion": "v1", "kind": "List", "items": [yaml.safe_load(workload())]})
    assert len(parse_manifests(contents)) == 1


def test_gpu_request_must_equal_limit():
    manifest = workload() + "            nvidia.com/gpu: 1\n          limits: {nvidia.com/gpu: 2}\n"
    with pytest.raises(ManifestError, match="equal GPU limits"):
        parse_manifests(manifest)


def test_pod_level_resources_are_not_silently_ignored():
    manifest = workload().replace("      containers:", "      resources: {requests: {cpu: '4'}}\n      containers:")
    with pytest.raises(ManifestError, match="Pod-level resources"):
        parse_manifests(manifest)
