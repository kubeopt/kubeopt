"""KubeOpt MCP Server.

Exposes KubeOpt's Kubernetes cost-optimization data to Claude via the
Model Context Protocol (MCP) over stdio transport.

Usage (Claude Desktop config):
    {
      "mcpServers": {
        "kubeopt": {
          "command": "/path/to/kubeopt/.venv/bin/python3",
          "args": ["-m", "mcp_server.server"],
          "env": {
            "KUBEOPT_API_URL": "http://localhost:5001",
            "KUBEOPT_USERNAME": "kubeopt",
            "KUBEOPT_PASSWORD": "your-password"
          }
        }
      }
    }
"""

import asyncio
import logging
import sys

from mcp.server import Server
from mcp.types import TextContent, Tool
import mcp.server.stdio

from mcp_server.api_client import KubeOptAPIClient

# ---------------------------------------------------------------------------
# Logging — stderr only (stdout is reserved for MCP stdio transport)
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
server = Server("kubeopt")
api_client = KubeOptAPIClient()

# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _fmt_currency(val) -> str:
    """Format a number as USD currency."""
    try:
        return f"${float(val):,.2f}"
    except (TypeError, ValueError):
        return "$0.00"


def _fmt_pct(val) -> str:
    """Format a number as a percentage."""
    try:
        return f"{float(val):.1f}%"
    except (TypeError, ValueError):
        return "0.0%"


def _fmt_clusters(clusters: list) -> str:
    """Format cluster list into readable text."""
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
    """Format portfolio summary into readable text."""
    total_clusters = summary.get("total_clusters", 0)
    total_cost = _fmt_currency(summary.get("total_monthly_cost"))
    total_savings = _fmt_currency(summary.get("total_potential_savings"))
    avg_score = _fmt_pct(summary.get("average_optimization_score"))
    total_nodes = summary.get("total_nodes", 0)
    attention = summary.get("clusters_needing_attention", 0)

    return (
        f"Portfolio Cost Summary\n"
        f"======================\n"
        f"Total clusters:            {total_clusters}\n"
        f"Total nodes:               {total_nodes}\n"
        f"Total monthly cost:        {total_cost}\n"
        f"Total potential savings:   {total_savings}\n"
        f"Average optimization:      {avg_score}\n"
        f"Clusters needing attention: {attention}"
    )


def _fmt_analysis(data: dict, cluster_id: str) -> str:
    """Format chart-data analysis response into readable text."""
    total_cost = _fmt_currency(data.get("total_cost"))
    cpu_gap = _fmt_pct(data.get("cpu_gap"))
    mem_gap = _fmt_pct(data.get("memory_gap"))
    hpa_eff = _fmt_pct(data.get("hpa_efficiency"))
    ns_count = data.get("namespace_count", 0)
    wl_count = data.get("workload_count", 0)

    lines = [
        f"Cluster Analysis: {cluster_id}",
        f"{'=' * 50}",
        f"Total monthly cost:  {total_cost}",
        f"CPU utilization gap:  {cpu_gap}",
        f"Memory utilization gap: {mem_gap}",
        f"HPA efficiency:      {hpa_eff}",
        f"Namespaces: {ns_count}  |  Workloads: {wl_count}",
    ]

    # Cost categories breakdown
    categories = data.get("cost_categories", [])
    if categories:
        lines.append("\nCost Breakdown by Category:")
        for cat in categories:
            lines.append(f"  - {cat.get('name', '?')}: {_fmt_currency(cat.get('value'))}")

    # Savings breakdown
    savings = data.get("savings_breakdown", {})
    if savings:
        lines.append("\nSavings Opportunities:")
        for key, val in savings.items():
            if isinstance(val, (int, float)) and val > 0:
                lines.append(f"  - {key}: {_fmt_currency(val)}")

    # Node recommendations
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

    # Anomaly detection
    anomaly = data.get("anomaly_detection", {})
    if anomaly and anomaly.get("total_anomalies", 0) > 0:
        lines.append(f"\nAnomalies Detected: {anomaly['total_anomalies']} (avg severity: {_fmt_pct(anomaly.get('average_severity'))})")

    # Insights
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
    """Extract and format optimization recommendations sorted by savings impact."""
    items = []

    # From savings_breakdown
    savings = data.get("savings_breakdown", {})
    for key, val in savings.items():
        if isinstance(val, (int, float)) and val > 0:
            items.append({
                "category": key,
                "action": f"Optimize {key.replace('_', ' ')}",
                "estimated_savings": float(val),
                "confidence": "high",
            })

    # From node_recommendations
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

    # From insights that mention savings
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

    # Sort by estimated_savings descending
    items.sort(key=lambda x: x["estimated_savings"], reverse=True)

    if not items:
        return f"No actionable recommendations found for cluster {cluster_id}. The cluster may not have been analyzed yet -- try running analyze_cluster first."

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


def _fmt_pods(data: dict, cluster_id: str, namespace_filter: str | None) -> str:
    """Format pod cost data into readable text."""
    pods = data.get("pods", [])
    if not pods:
        return f"No pod data found for cluster {cluster_id}. Run an analysis first to collect Kubernetes data."

    if namespace_filter:
        pods = [p for p in pods if p.get("namespace", "") == namespace_filter]
        if not pods:
            return f"No pods found in namespace '{namespace_filter}' for cluster {cluster_id}."

    # Sort by cost descending (if cost data available), otherwise by CPU
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
# Tool definitions
# ---------------------------------------------------------------------------

TOOLS = [
    Tool(
        name="list_clusters",
        description=(
            "List all Kubernetes clusters being monitored with their latest "
            "cost and optimization data"
        ),
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    Tool(
        name="get_cost_summary",
        description="Get portfolio-level cost summary across all clusters",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    Tool(
        name="get_cluster_analysis",
        description=(
            "Get detailed cost analysis for a specific cluster including "
            "cost breakdown, resource utilization, node recommendations, "
            "and anomaly detection"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "cluster_id": {
                    "type": "string",
                    "description": "The cluster ID to analyze (use list_clusters to find IDs)",
                },
            },
            "required": ["cluster_id"],
        },
    ),
    Tool(
        name="get_recommendations",
        description=(
            "Get actionable optimization recommendations for a cluster, "
            "sorted by estimated savings impact"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "cluster_id": {
                    "type": "string",
                    "description": "The cluster ID to get recommendations for",
                },
            },
            "required": ["cluster_id"],
        },
    ),
    Tool(
        name="analyze_cluster",
        description=(
            "Trigger a fresh cost analysis for a cluster. This runs in the "
            "background and takes 1-15 minutes depending on cluster size and "
            "cloud provider. Polls for completion and returns the results."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "cluster_id": {
                    "type": "string",
                    "description": "The cluster ID to analyze",
                },
            },
            "required": ["cluster_id"],
        },
    ),
    Tool(
        name="get_pod_costs",
        description=(
            "Get per-pod cost breakdown for a cluster, useful for identifying "
            "expensive workloads. Optionally filter by namespace."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "cluster_id": {
                    "type": "string",
                    "description": "The cluster ID to get pod costs for",
                },
                "namespace": {
                    "type": "string",
                    "description": "Optional: filter pods to this Kubernetes namespace",
                },
            },
            "required": ["cluster_id"],
        },
    ),
]


# ---------------------------------------------------------------------------
# MCP handlers
# ---------------------------------------------------------------------------

@server.list_tools()
async def handle_list_tools():
    return TOOLS


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    """Dispatch tool calls to the appropriate handler."""
    try:
        if name == "list_clusters":
            return await _tool_list_clusters()
        elif name == "get_cost_summary":
            return await _tool_get_cost_summary()
        elif name == "get_cluster_analysis":
            return await _tool_get_cluster_analysis(arguments["cluster_id"])
        elif name == "get_recommendations":
            return await _tool_get_recommendations(arguments["cluster_id"])
        elif name == "analyze_cluster":
            return await _tool_analyze_cluster(arguments["cluster_id"])
        elif name == "get_pod_costs":
            return await _tool_get_pod_costs(
                arguments["cluster_id"],
                arguments.get("namespace"),
            )
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as exc:
        logger.error("Tool %s failed: %s", name, exc, exc_info=True)
        return [TextContent(type="text", text=f"Error running {name}: {exc}")]


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

async def _tool_list_clusters():
    clusters = await api_client.list_clusters()
    return [TextContent(type="text", text=_fmt_clusters(clusters))]


async def _tool_get_cost_summary():
    summary = await api_client.get_portfolio_summary()
    return [TextContent(type="text", text=_fmt_portfolio(summary))]


async def _tool_get_cluster_analysis(cluster_id: str):
    data = await api_client.get_chart_data(cluster_id, "overview")
    return [TextContent(type="text", text=_fmt_analysis(data, cluster_id))]


async def _tool_get_recommendations(cluster_id: str):
    data = await api_client.get_chart_data(cluster_id, "overview")
    return [TextContent(type="text", text=_fmt_recommendations(data, cluster_id))]


async def _tool_analyze_cluster(cluster_id: str):
    """Trigger analysis and poll until complete or timeout."""
    # Trigger the analysis
    trigger = await api_client.analyze_cluster(cluster_id)
    trigger_status = trigger.get("status", "unknown")

    if trigger_status not in ("started", "running", "queued"):
        return [TextContent(
            type="text",
            text=f"Failed to start analysis: {trigger.get('message', trigger_status)}",
        )]

    lines = [f"Analysis triggered for cluster {cluster_id}. Polling for completion..."]

    # Poll every 10 seconds, up to 20 minutes (120 iterations)
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

        # Log progress periodically (every 30 seconds)
        if poll_num % 3 == 0:
            logger.info(
                "Analysis %s: %.0f%% - %s (%s)",
                cluster_id, progress * 100 if progress <= 1 else progress,
                phase, message,
            )

        if current_status == "completed":
            lines.append(
                f"Analysis completed after ~{poll_num * 10} seconds."
            )
            # Fetch the fresh results
            try:
                data = await api_client.get_chart_data(cluster_id, "overview")
                lines.append("")
                lines.append(_fmt_analysis(data, cluster_id))
            except Exception as exc:
                lines.append(f"Analysis completed but failed to fetch results: {exc}")
            return [TextContent(type="text", text="\n".join(lines))]

        elif current_status in ("failed", "error"):
            error = status_data.get("error", message or "Unknown error")
            lines.append(f"Analysis failed: {error}")
            return [TextContent(type="text", text="\n".join(lines))]

    # Timeout
    lines.append(
        "Analysis is still running after 20 minutes. "
        "Use get_cluster_analysis later to check results."
    )
    return [TextContent(type="text", text="\n".join(lines))]


async def _tool_get_pod_costs(cluster_id: str, namespace: str | None):
    data = await api_client.get_pods_by_cluster(cluster_id)
    return [TextContent(type="text", text=_fmt_pods(data, cluster_id, namespace))]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main():
    """Run the MCP server over stdio."""
    logger.info("Starting KubeOpt MCP server (API: %s)", api_client.base_url)
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
