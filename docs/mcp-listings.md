# KubeOpt MCP Server — Directory Listing Content

Submission-ready content for MCP server directories.

---

## 1. awesome-mcp-servers README Entry

Paste this line into the appropriate section (DevOps / Infrastructure / Kubernetes) of the
[awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) list:

```
- [kubeopt](https://github.com/kubeopt/kubeopt) — Kubernetes cost optimization: analyze AKS/EKS/GKE clusters, get rightsizing recommendations, and query per-pod costs in plain English. ([MIT](https://github.com/kubeopt/kubeopt/blob/main/LICENSE))
```

**PR target:** `https://github.com/punkpeye/awesome-mcp-servers` — edit `README.md`, add under
the DevOps/Infrastructure section, open a PR with title:
`Add kubeopt — Kubernetes cost optimization MCP server`

---

## 2. glama.ai Submission

glama.ai auto-indexes MCP servers from GitHub. No manual form — it discovers servers via GitHub
topics and README signals.

### What glama needs to pick up the repo

1. **GitHub topics** — add all of the following to the repo's "Topics" field
   (Settings → General → Topics):

   ```
   mcp
   mcp-server
   model-context-protocol
   kubernetes
   kubernetes-cost-optimization
   k8s
   eks
   aks
   gke
   devops
   cloud-cost
   rightsizing
   ```

2. **README signals** — the README should contain:
   - A section titled `## MCP Server` or `## Usage with Claude / MCP`
   - The phrase `Model Context Protocol` (spelled out at least once)
   - The Claude Desktop JSON config block (already present in `mcp_server/server.py` docstring —
     promote this to the README)
   - A `## Tools` section listing the 6 tools with one-line descriptions

3. **`mcp-server` topic is the primary trigger** for glama's crawler. Confirm it is set before
   expecting indexing.

4. Optionally submit directly at `https://glama.ai/mcp/servers/submit` with the GitHub URL:
   `https://github.com/kubeopt/kubeopt`

---

## 3. mcp.so Submission Form Content

**Name:**
```
KubeOpt
```

**Description (one line):**
```
Query Kubernetes cluster costs, rightsizing recommendations, and pod-level spend directly from your AI assistant.
```

**Long description (2-3 sentences):**
```
KubeOpt exposes 6 MCP tools that connect to a running KubeOpt instance and surface cost analysis
data for AKS, EKS, and GKE clusters. You can list monitored clusters, pull a portfolio-wide cost
summary, drill into per-cluster cost breakdowns with node recommendations and anomaly detection,
and get per-pod cost breakdowns filtered by namespace — all from a natural-language prompt.
Triggering a fresh analysis is also supported: the tool polls in the background and returns
results when complete.
```

**Category:**
```
DevOps / Infrastructure
```

**Tags:**
```
kubernetes, k8s, cost-optimization, eks, aks, gke, devops, cloud-cost, rightsizing, infrastructure
```

**GitHub URL:**
```
https://github.com/kubeopt/kubeopt
```

**Setup instructions (brief):**
```
1. Clone the repo and install dependencies: pip install -r requirements/mcp.txt
2. Add the server to Claude Desktop's config (~/.claude/claude_desktop_config.json):
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
3. Start a KubeOpt instance (Docker: docker-compose up) and add at least one cluster via the dashboard.
4. Restart Claude Desktop. The kubeopt tools will appear automatically.
```

**Example prompts (3):**
```
1. "What are the top cost-saving opportunities across all my Kubernetes clusters?"
2. "Show me the most expensive pods in the production namespace on my EKS cluster."
3. "Run a fresh analysis on cluster abc-123 and tell me what node types I should be using."
```

---

## 4. Reddit / HN Launch Post

Suitable for: r/ClaudeAI, r/mcp, r/devops, r/kubernetes, or a Show HN post.

---

**Title:**
```
Show HN: KubeOpt MCP server — query Kubernetes cluster costs from Claude
```

**Body:**

> I built an MCP server for KubeOpt, an open-source Kubernetes cost optimization tool.
>
> It exposes 6 tools over stdio:
>
> - `list_clusters` — lists all monitored clusters with cost and savings data
> - `get_cost_summary` — portfolio-level spend summary across all clusters
> - `get_cluster_analysis` — per-cluster cost breakdown, CPU/memory utilization gaps, node
>   recommendations, anomaly detection
> - `get_recommendations` — ranked list of rightsizing and optimization actions sorted by
>   estimated monthly savings
> - `analyze_cluster` — triggers a fresh analysis, polls in the background, returns results
>   when done (1–15 min depending on cluster size)
> - `get_pod_costs` — per-pod cost breakdown, filterable by namespace
>
> Works with AKS, EKS, and GKE. Connects to a local or hosted KubeOpt instance via username/password.
>
> **Setup** — add this to your Claude Desktop config and point it at a running KubeOpt instance:
>
> ```json
> {
>   "mcpServers": {
>     "kubeopt": {
>       "command": "/path/to/.venv/bin/python3",
>       "args": ["-m", "mcp_server.server"],
>       "env": {
>         "KUBEOPT_API_URL": "http://localhost:5001",
>         "KUBEOPT_USERNAME": "kubeopt",
>         "KUBEOPT_PASSWORD": "your-password"
>       }
>     }
>   }
> }
> ```
>
> Then ask things like:
> - "What's my total Kubernetes spend this month?"
> - "Which pods in the payments namespace are costing the most?"
> - "What node types should I be using on my prod cluster?"
>
> Repo: https://github.com/kubeopt/kubeopt
> The MCP server lives in `mcp_server/`.
>
> Happy to answer questions about how the analysis works or the MCP integration.
