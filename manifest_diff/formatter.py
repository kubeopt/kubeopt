"""Render resource changes without implying a change to infrastructure bills."""

from decimal import Decimal
from html import escape


def decimal_text(value):
    return format(value, "f").rstrip("0").rstrip(".") if value % 1 else str(int(value))


def _cell(value):
    return escape(str(value)).replace("|", "&#124;").replace("\n", " ").replace("\r", " ").replace("`", "&#96;")


def _delta(value):
    if value is None:
        return "Unavailable"
    return ("+" if value > 0 else "") + decimal_text(value)


def render_markdown(changes, node_monthly_cost=None):
    lines = ["## KubeOpt resource preview", "",
             "Manifest request changes describe requested capacity; they do not predict a billing increase.", ""]
    if not changes:
        lines.append("No supported workload resource changes found in changed manifest files.")
    for change in changes:
        lines.extend([
            f"### {_cell(change.namespace)} / {_cell(change.name)} ({change.kind}, {change.status})", "",
            "| Resource | Requests per pod | Requests total | Limits per pod | Limits total |",
            "| --- | ---: | ---: | ---: | ---: |",
        ])
        for key, label in (("cpu_millicores", "CPU (millicores)"), ("memory_bytes", "Memory (bytes)"),
                           ("nvidia_gpu", "NVIDIA GPUs"), ("amd_gpu", "AMD GPUs")):
            values = [getattr(getattr(change, attr), key) for attr in (
                "per_pod_requests_delta", "requests_delta", "per_pod_limits_delta", "limits_delta")]
            lines.append(f"| {label} | " + " | ".join(_delta(v) for v in values) + " |")
        before = change.before.replicas if change.before else 0
        after = change.after.replicas if change.after else 0
        lines.extend(["", f"Declared replicas: {before if before is not None else 'node-dependent'} -> {after if after is not None else 'node-dependent'}."])
        for warning in dict.fromkeys(w for state in (change.before, change.after) if state for w in state.warnings):
            lines.append(f"- {warning}")
        lines.append("")
    lines.extend(["", "Cost estimate unavailable. Whether another node is required: not evaluated."])
    if node_monthly_cost is not None:
        lines.extend(["", "### Pricing input", "",
                      f"Operator-provided node price: ${decimal_text(Decimal(node_monthly_cost))}/node/month (USD).",
                      "Node capacity, placement, and allocation rates are not modeled; this price alone cannot determine workload cost."])
    lines.extend(["", "Scope: changed plain-YAML apps/v1 Deployments, StatefulSets, and DaemonSets. "
                  "Container limits and before/after specifications are included in JSON. "
                  "Runtime autoscaling, admission defaults, pod overhead, Helm, and node placement are not evaluated."])
    return "\n".join(lines) + "\n"
