"""KubeOpt MCP Server.

Exposes KubeOpt's Kubernetes cost-optimization data to Claude via the
Model Context Protocol (MCP) over stdio transport.

Usage (Claude Desktop / claude_desktop_config.json):
    {
      "mcpServers": {
        "kubeopt": {
          "command": "uvx",
          "args": ["kubeopt-mcp"],
          "env": {
            "KUBEOPT_API_URL": "https://demo.kubeopt.com",
            "KUBEOPT_USERNAME": "your-username",
            "KUBEOPT_PASSWORD": "your-password"
          }
        }
      }
    }
"""

import logging
import sys
from typing import Optional

from mcp.server import MCPServer

from mcp_server.api_client import KubeOptAPIClient

# ---------------------------------------------------------------------------
# Logging -- stderr only (stdout is reserved for MCP stdio transport)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("kubeopt-mcp")

# ---------------------------------------------------------------------------
# Server + API client singletons
# ---------------------------------------------------------------------------
server = MCPServer("kubeopt")
api_client = KubeOptAPIClient()


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _fmt_currency(val) -> str:
    try:
        return f"${float(val):,.2f}"
    except (TypeError, ValueError):
        return "$0.00"


def _fmt_pct(val) -> str:
    try:
        return f"{float(val):.1f}%"
    except (TypeError, ValueError):
        return "0.0%"


def _fmt_clusters(clusters: list) -> str:
    if not clusters:
        return "No clusters found. Add a cluster via the KubeOpt dashboard first."

    lines = [f"Found {len(clusters)} cluster(s):\n"]
    for i, c in enumerate(clusters, 1):
        name = c.get("cluster_name", "unknown")
        provider = (c.get("cloud_provider") or "azure").upper()
        region = c.get("region", "n/a")
        cost = _fmt_currency(c.get("total_cost"))
        savings = _fmt_currency(c.get("potential_savings"))
        score = _fmt_pct(c.get("optimization_score"))
        cid = c.get("cluster_id", "")
        status = c.get("status", "active")

        lines.append(
            f"{i}. {name}\n"
            f"   Provider: {provider}  |  Region: {region}  |  Status: {status}\n"
            f"   Monthly cost: {cost}  |  Potential savings: {savings}\n"
            f"   Optimization score: {score}\n"
            f"   Cluster ID: {cid}"
        )
    return "\n\n".join(lines)


def _fmt_portfolio(summary: dict) -> str:
    total_clusters = summary.get("total_clusters", 0)
    total_cost = _fmt_currency(summary.get("total_monthly_cost"))
    total_savings = _fmt_currency(summary.get("total_potential_savings"))
    avg_score = _fmt_pct(summary.get("average_optimization_score"))
    total_nodes = summary.get("total_nodes", 0)
    attention = summary.get("clusters_needing_attention", 0)

    return (
        f"Portfolio Cost Summary\n"
        f"======================\n"
        f"Total clusters:             {total_clusters}\n"
        f"Total nodes:                {total_nodes}\n"
        f"Total monthly cost:         {total_cost}\n"
        f"Total potential savings:    {total_savings}\n"
        f"Average optimization:       {avg_score}\n"
        f"Clusters needing attention: {attention}"
    )


def _fmt_analysis(data: dict, cluster_id: str) -> str:
    total_cost = _fmt_currency(data.get("total_cost"))
    cpu_gap = _fmt_pct(data.get("cpu_gap"))
    mem_gap = _fmt_pct(data.get("memory_gap"))
    hpa_eff = _fmt_pct(data.get("hpa_efficiency"))
    ns_count = data.get("namespace_count", 0)
    wl_count = data.get("workload_count", 0)

    lines = [
        f"Cluster Analysis: {cluster_id}",
        f"{'=' * 50}",
        f"Total monthly cost:     {total_cost}",
        f"CPU utilization gap:    {cpu_gap}",
        f"Memory utilization gap: {mem_gap}",
        f"HPA efficiency:         {hpa_eff}",
        f"Namespaces: {ns_count}  |  Workloads: {wl_count}",
    ]

    categories = data.get("cost_categories", [])
    if categories:
        lines.append("\nCost Breakdown by Category:")
        for cat in categories:
            lines.append(f"  - {cat.get('name', '?')}: {_fmt_currency(cat.get('value'))}")

    savings = data.get("savings_breakdown", {})
    if savings:
        lines.append("\nSavings Opportunities:")
        for key, val in savings.items():
            if isinstance(val, (int, float)) and val > 0:
                lines.append(f"  - {key}: {_fmt_currency(val)}")

    node_recs = data.get("node_recommendations", [])
    if node_recs:
        lines.append(f"\nNode Recommendations ({len(node_recs)}):")
        for rec in node_recs[:5]:
            if isinstance(rec, dict):
                current = rec.get("current_vm", rec.get("current_vm_size", "?"))
                recommended = rec.get("recommended_vm", rec.get("recommended_vm_size", "?"))
                pool = rec.get("node_pool", rec.get("name", "?"))
                sav = _fmt_currency(rec.get("monthly_savings", rec.get("savings", 0)))
                lines.append(f"  - Pool '{pool}': {current} -> {recommended} (saves {sav}/mo)")

    anomaly = data.get("anomaly_detection", {})
    if anomaly and anomaly.get("total_anomalies", 0) > 0:
        lines.append(
            f"\nAnomalies Detected: {anomaly['total_anomalies']} "
            f"(avg severity: {_fmt_pct(anomaly.get('average_severity'))})"
        )

    insights = data.get("insights", [])
    if insights:
        lines.append(f"\nKey Insights ({len(insights)}):")
        for ins in insights[:8]:
            if isinstance(ins, dict):
                cat = ins.get("category", "")
                msg = ins.get("message", str(ins))
                lines.append(f"  [{cat}] {msg}")
            else:
                lines.append(f"  - {ins}")

    return "\n".join(lines)


def _fmt_recommendations(data: dict, cluster_id: str) -> str:
    items = []

    savings = data.get("savings_breakdown", {})
    for key, val in savings.items():
        if isinstance(val, (int, float)) and val > 0:
            items.append({
                "category": key,
                "action": f"Optimize {key.replace('_', ' ')}",
                "estimated_savings": float(val),
                "confidence": "high",
            })

    node_recs = data.get("node_recommendations", [])
    for rec in node_recs:
        if isinstance(rec, dict):
            sav = float(rec.get("monthly_savings", rec.get("savings", 0)) or 0)
            if sav > 0:
                current = rec.get("current_vm", rec.get("current_vm_size", "?"))
                recommended = rec.get("recommended_vm", rec.get("recommended_vm_size", "?"))
                pool = rec.get("node_pool", rec.get("name", "?"))
                items.append({
                    "category": "Node rightsizing",
                    "action": f"Resize pool '{pool}' from {current} to {recommended}",
                    "estimated_savings": sav,
                    "confidence": rec.get("confidence", "medium"),
                })

    insights = data.get("insights", [])
    for ins in insights:
        if isinstance(ins, dict) and ins.get("message"):
            msg = ins["message"].lower()
            if "sav" in msg or "reduc" in msg or "optim" in msg:
                items.append({
                    "category": ins.get("category", "general"),
                    "action": ins.get("message", ""),
                    "estimated_savings": 0,
                    "confidence": "info",
                })

    items.sort(key=lambda x: x["estimated_savings"], reverse=True)

    if not items:
        return (
            f"No actionable recommendations found for cluster {cluster_id}. "
            f"The cluster may not have been analyzed yet -- try analyze_cluster first."
        )

    lines = [
        f"Optimization Recommendations for {cluster_id}",
        f"{'=' * 50}",
        f"Found {len(items)} recommendation(s), sorted by estimated savings:\n",
    ]
    for i, item in enumerate(items, 1):
        sav_str = _fmt_currency(item["estimated_savings"]) if item["estimated_savings"] > 0 else "n/a"
        lines.append(
            f"{i}. [{item['category']}] {item['action']}\n"
            f"   Estimated savings: {sav_str}/mo  |  Confidence: {item['confidence']}"
        )

    return "\n\n".join(lines)


def _fmt_pods(data: dict, cluster_id: str, namespace_filter: Optional[str]) -> str:
    pods = data.get("pods", [])
    if not pods:
        return (
            f"No pod data found for cluster {cluster_id}. "
            f"Run an analysis first to collect Kubernetes data."
        )

    if namespace_filter:
        pods = [p for p in pods if p.get("namespace", "") == namespace_filter]
        if not pods:
            return f"No pods found in namespace '{namespace_filter}' for cluster {cluster_id}."

    def _sort_key(p):
        return float(p.get("cost", p.get("cpu_usage", 0)) or 0)

    pods.sort(key=_sort_key, reverse=True)

    header = f"Pod Cost Breakdown for {cluster_id}"
    if namespace_filter:
        header += f" (namespace: {namespace_filter})"
    lines = [header, "=" * 50, f"Total pods: {len(pods)}\n"]

    for i, p in enumerate(pods[:30], 1):
        name = p.get("name", "unknown")
        ns = p.get("namespace", "default")
        workload = p.get("workload", p.get("controller", "n/a"))
        cpu = p.get("cpu_usage", p.get("cpu_requests", "n/a"))
        mem = p.get("memory_usage", p.get("memory_requests", "n/a"))
        cost = p.get("cost", None)
        status = p.get("status", p.get("phase", "Running"))

        cost_str = _fmt_currency(cost) if cost is not None else "n/a"
        lines.append(
            f"{i}. {name}\n"
            f"   Namespace: {ns}  |  Workload: {workload}  |  Status: {status}\n"
            f"   CPU: {cpu}  |  Memory: {mem}  |  Est. cost: {cost_str}/mo"
        )

    if len(pods) > 30:
        lines.append(f"\n... and {len(pods) - 30} more pods (showing top 30 by cost)")

    return "\n\n".join(lines)


# ---------------------------------------------------------------------------
# Tools (MCPServer v2 pattern)
# ---------------------------------------------------------------------------

@server.tool()
async def list_clusters() -> str:
    """List all Kubernetes clusters being monitored with their latest cost and optimization data."""
    clusters = await api_client.list_clusters()
    return _fmt_clusters(clusters)


@server.tool()
async def get_cost_summary() -> str:
    """Get portfolio-level cost summary across all clusters."""
    summary = await api_client.get_portfolio_summary()
    return _fmt_portfolio(summary)


@server.tool()
async def get_cluster_analysis(cluster_id: str) -> str:
    """Get detailed cost analysis for a specific cluster including cost breakdown, resource utilization, node recommendations, and anomaly detection.

    Args:
        cluster_id: The cluster ID to analyze. Use list_clusters to find IDs.
    """
    data = await api_client.get_chart_data(cluster_id, "overview")
    return _fmt_analysis(data, cluster_id)


@server.tool()
async def get_recommendations(cluster_id: str) -> str:
    """Get actionable optimization recommendations for a cluster, sorted by estimated savings impact.

    Args:
        cluster_id: The cluster ID to get recommendations for.
    """
    data = await api_client.get_chart_data(cluster_id, "overview")
    return _fmt_recommendations(data, cluster_id)


@server.tool()
async def analyze_cluster(cluster_id: str) -> str:
    """Trigger a fresh cost analysis for a cluster. Polls for completion and returns results. Takes 1-15 minutes depending on cluster size.

    Args:
        cluster_id: The cluster ID to analyze.
    """
    import asyncio

    trigger = await api_client.analyze_cluster(cluster_id)
    trigger_status = trigger.get("status", "unknown")

    if trigger_status not in ("started", "running", "queued"):
        return f"Failed to start analysis: {trigger.get('message', trigger_status)}"

    lines = [f"Analysis triggered for cluster {cluster_id}. Polling for completion..."]

    max_polls = 120
    for poll_num in range(1, max_polls + 1):
        await asyncio.sleep(10)

        try:
            status_data = await api_client.get_analysis_status(cluster_id)
        except Exception as exc:
            logger.warning("Status poll %d failed: %s", poll_num, exc)
            continue

        current_status = status_data.get("status", "unknown")
        progress = float(status_data.get("progress", 0))
        phase = status_data.get("current_phase", "")
        message = status_data.get("message", "")

        if poll_num % 3 == 0:
            logger.info(
                "Analysis %s: %.0f%% - %s (%s)",
                cluster_id, progress * 100 if progress <= 1 else progress,
                phase, message,
            )

        if current_status == "completed":
            lines.append(f"Analysis completed after ~{poll_num * 10} seconds.")
            try:
                data = await api_client.get_chart_data(cluster_id, "overview")
                lines.append("")
                lines.append(_fmt_analysis(data, cluster_id))
            except Exception as exc:
                lines.append(f"Analysis completed but failed to fetch results: {exc}")
            return "\n".join(lines)

        elif current_status in ("failed", "error"):
            error = status_data.get("error", message or "Unknown error")
            lines.append(f"Analysis failed: {error}")
            return "\n".join(lines)

    lines.append(
        "Analysis is still running after 20 minutes. "
        "Use get_cluster_analysis later to check results."
    )
    return "\n".join(lines)


@server.tool()
async def get_pod_costs(cluster_id: str, namespace: Optional[str] = None) -> str:
    """Get per-pod cost breakdown for a cluster, useful for identifying expensive workloads.

    Args:
        cluster_id: The cluster ID to get pod costs for.
        namespace: Optional Kubernetes namespace to filter pods by.
    """
    data = await api_client.get_pods_by_cluster(cluster_id)
    return _fmt_pods(data, cluster_id, namespace)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run():
    """Sync entry point for uvx / console_scripts."""
    logger.info("Starting KubeOpt MCP server (API: %s)", api_client.base_url)
    server.run_stdio_async()


if __name__ == "__main__":
    run()
