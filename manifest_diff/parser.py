"""Parse plain Kubernetes manifests without executing templates or plugins."""

from __future__ import annotations

from decimal import Decimal, DecimalException
import re

import yaml

from .models import Container, Resources, Workload


class ManifestError(ValueError):
    pass


_DECIMAL_SUFFIXES = {"": 0, "n": -9, "u": -6, "m": -3, "k": 3, "K": 3,
                     "M": 6, "G": 9, "T": 12, "P": 15, "E": 18}
_BINARY_SUFFIXES = {s + "i": Decimal(1024) ** i for i, s in enumerate("KMGTPE", 1)}
_QUANTITY = re.compile(r"([+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))([eE][+-]?[0-9]+|[numkKMGTPE]|[KMGTPE]i)?\Z")


def parse_quantity(value) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ManifestError("Resource quantities must be non-negative numbers or quantity strings")
    match = _QUANTITY.fullmatch(str(value))
    if not match:
        raise ManifestError(f"Invalid resource quantity: {value!r}")
    number, suffix = match.groups()
    suffix = suffix or ""
    try:
        if suffix in _BINARY_SUFFIXES:
            result = Decimal(number) * _BINARY_SUFFIXES[suffix]
        elif suffix in _DECIMAL_SUFFIXES:
            result = Decimal(number) * Decimal(10) ** _DECIMAL_SUFFIXES[suffix]
        else:
            result = Decimal(number) * Decimal(10) ** int(suffix[1:])
        if not result.is_finite() or result > Decimal(2) ** 63 - 1:
            raise ManifestError("Resource quantity exceeds the supported Kubernetes range")
        return result
    except (DecimalException, OverflowError) as exc:
        raise ManifestError("Invalid resource quantity") from exc


class _Loader(yaml.SafeLoader):
    pass


def _unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ManifestError(f"Duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_Loader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


def _mapping(value, label):
    if not isinstance(value, dict):
        raise ManifestError(f"{label} must be a mapping")
    return value


def _resources(raw, defaults=None):
    raw = _mapping(raw, "resources")
    defaults = defaults or {}
    values = []
    for key, multiplier in (("cpu", 1000), ("memory", 1), ("nvidia.com/gpu", 1), ("amd.com/gpu", 1)):
        value = raw.get(key, defaults.get(key))
        parsed = parse_quantity(value) * multiplier if value is not None else (Decimal(0) if "gpu" in key else None)
        if key == "cpu" and parsed is not None and parsed != parsed.to_integral_value():
            raise ManifestError("CPU quantities must have at most millicore precision")
        if key == "memory" and parsed is not None:
            parsed = parsed.to_integral_value(rounding="ROUND_CEILING")
        if "gpu" in key and parsed != parsed.to_integral_value():
            raise ManifestError("GPU quantities must be whole numbers")
        values.append(parsed)
    return Resources(*values)


def _containers(raw):
    if not isinstance(raw, list):
        raise ManifestError("containers must be a list")
    result = []
    names = set()
    for item in raw:
        item = _mapping(item, "container")
        name = item.get("name")
        if not isinstance(name, str) or not name or name in names:
            raise ManifestError("Containers require unique non-empty names")
        names.add(name)
        resources = _mapping(item.get("resources", {}), "resources")
        limits = _mapping(resources.get("limits", {}), "limits")
        requests = _mapping(resources.get("requests", {}), "requests")
        request_values, limit_values = _resources(requests, limits), _resources(limits)
        for key, attr in (("nvidia.com/gpu", "nvidia_gpu"), ("amd.com/gpu", "amd_gpu")):
            if key in requests and (key not in limits or getattr(request_values, attr) != getattr(limit_values, attr)):
                raise ManifestError("GPU requests require equal GPU limits")
        result.append(Container(name, request_values, limit_values))
    return tuple(sorted(result, key=lambda c: c.name))


def _parse_document(doc, source):
    if not isinstance(doc, dict):
        return []
    if doc.get("kind") == "List":
        items = doc.get("items", [])
        if not isinstance(items, list):
            raise ManifestError("List.items must be a list")
        return [w for item in items for w in _parse_document(item, source)]
    kind = doc.get("kind")
    if kind not in ("Deployment", "StatefulSet", "DaemonSet"):
        return []
    if doc.get("apiVersion") != "apps/v1":
        raise ManifestError("Supported workloads require apiVersion: apps/v1")
    metadata = _mapping(doc.get("metadata", {}), "metadata")
    name = metadata.get("name")
    namespace = metadata.get("namespace", "default")
    if not all(isinstance(v, str) and v for v in (name, namespace)):
        raise ManifestError("Workloads require a name and a non-empty namespace")
    spec = _mapping(doc.get("spec", {}), "spec")
    replicas = None if kind == "DaemonSet" else spec.get("replicas", 1)
    if kind != "DaemonSet" and (type(replicas) is not int or replicas < 0):
        raise ManifestError("replicas must be a non-negative integer")
    template = _mapping(spec.get("template", {}), "template")
    pod_spec = _mapping(template.get("spec", {}), "pod spec")
    if "resources" in pod_spec:
        raise ManifestError("Pod-level resources are not supported; only container resource declarations are modeled")
    containers = _containers(pod_spec.get("containers", []))
    if not containers:
        raise ManifestError("Workloads require at least one container")
    return [Workload(kind, namespace, name, replicas, containers,
                     _containers(pod_spec.get("initContainers", [])), source)]


def parse_manifests(text: str, source="<manifest>") -> list[Workload]:
    try:
        return [w for doc in yaml.load_all(text, Loader=_Loader)
                for w in _parse_document(doc, source)]
    except (yaml.YAMLError, ManifestError, TypeError, RecursionError) as exc:
        raise ManifestError(f"{source}: invalid or unsupported manifest ({exc})") from exc
