# KubeOpt

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://python.org)
[![GitHub stars](https://img.shields.io/github/stars/kubeopt/kubeopt)](https://github.com/kubeopt/kubeopt/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/kubeopt/kubeopt)](https://github.com/kubeopt/kubeopt/network)

**The Cost Engineer for Kubernetes**

KubeOpt analyzes your Kubernetes clusters, identifies cost optimization opportunities, and generates actionable implementation plans with copy-paste kubectl commands.

Works with **Azure AKS**, **AWS EKS**, and **Google GKE**.

---

## What It Does

- Connects to your cloud provider APIs and Kubernetes clusters
- Runs 16 optimization algorithms (rightsizing, HPA, storage, networking, node pools, anomaly detection)
- Calculates actual vs optimal costs with specific dollar savings per resource
- Generates a 3-week implementation plan with kubectl commands ready to execute
- Dashboard with cost breakdowns, workload analysis, and optimization scores

## Claude AI Integration (MCP)

Ask Claude about your Kubernetes costs in plain English.

KubeOpt ships an [MCP](https://modelcontextprotocol.io) server (`mcp_server/`) that exposes 6 tools over stdio transport. Once connected, Claude Desktop, Cursor, or Windsurf can query your cluster data directly — no copy-pasting dashboards.

**Tools exposed:**

| Tool | What it does |
|------|-------------|
| `list_clusters` | List all monitored clusters with cost data |
| `get_cost_summary` | Portfolio-level cost summary across all clusters |
| `get_cluster_analysis` | Detailed analysis for a specific cluster |
| `get_recommendations` | Actionable recommendations sorted by savings impact |
| `analyze_cluster` | Trigger a fresh analysis and poll until complete |
| `get_pod_costs` | Per-pod cost breakdown, filterable by namespace |

### Prerequisites

- KubeOpt running locally (`python main.py`) or deployed on Railway
- Python virtual environment with dependencies installed (`pip install -r requirements.txt`)

### Claude Desktop

Edit `~/.claude/claude_desktop_config.json`:

```json
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
```

Restart Claude Desktop after saving.

### Cursor

Open **Cursor Settings → MCP** and add a new server entry:

```json
{
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
```

### Windsurf / Codeium

Edit `~/.codeium/windsurf/mcp_config.json` (create it if it doesn't exist):

```json
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
```

Restart Windsurf after saving.

### Example prompts

```
What are my top 3 cost savings opportunities across all clusters?
Which pods are costing the most in the production namespace?
Give me a summary of total Kubernetes spend this month.
What's the optimization score for my staging cluster?
Trigger a fresh analysis on cluster prod-aks-eastus and report back.
```

For more on the protocol: [modelcontextprotocol.io](https://modelcontextprotocol.io)

---

## GitHub Action

Run a Kubernetes cost scan on every pull request or on a schedule. The action posts a summary as a PR comment (upserted on re-runs) and writes results to the GitHub Step Summary.

**What you get on each PR:**

```
## KubeOpt Cost Scan — 2026-04-27

| Cluster          | Provider | Monthly Spend | Savings Available |
|------------------|----------|---------------|-------------------|
| prod-eks-us-east | AWS      | $4,120        | $890/mo           |
| staging-aks-weu  | Azure    | $1,340        | $210/mo           |

**Total potential savings: $1,100/mo**

<details>
<summary>Top opportunities</summary>

1. $540/mo — prod-eks-us-east — Rightsize 6 over-provisioned node groups
2. $350/mo — prod-eks-us-east — Enable HPA on 4 deployments with static replicas
3. $210/mo — staging-aks-weu  — Remove 3 idle nodes outside business hours

</details>
```

### Setup

**1. Add secrets to your repository**

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Value |
|--------|-------|
| `KUBEOPT_URL` | URL of your KubeOpt instance (e.g. `https://demo.kubeopt.com`) |
| `KUBEOPT_USERNAME` | KubeOpt username |
| `KUBEOPT_PASSWORD` | KubeOpt password |

**2. Create `.github/workflows/cost-scan.yml`**

```yaml
name: K8s Cost Scan

on:
  pull_request:
    types: [opened, synchronize]
  schedule:
    - cron: '0 8 * * 1'   # Every Monday at 08:00 UTC
  workflow_dispatch:

permissions:
  contents: read
  pull-requests: write

jobs:
  cost-scan:
    name: KubeOpt Cost Scan
    runs-on: ubuntu-latest
    steps:
      - name: Run KubeOpt cost scan
        id: kubeopt
        uses: kubeopt/kubeopt@v1
        with:
          kubeopt-url:      ${{ secrets.KUBEOPT_URL }}
          kubeopt-username: ${{ secrets.KUBEOPT_USERNAME }}
          kubeopt-password: ${{ secrets.KUBEOPT_PASSWORD }}
          top:              5
          post-comment:     ${{ github.event_name == 'pull_request' && 'true' || 'false' }}

      - name: Print savings to log
        if: always()
        run: echo "Total savings available: ${{ steps.kubeopt.outputs.total-savings }}/mo"
```

### Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `kubeopt-url` | yes | | URL of your KubeOpt instance |
| `kubeopt-username` | yes | `kubeopt` | KubeOpt username |
| `kubeopt-password` | yes | | KubeOpt password |
| `cluster-id` | no | (all clusters) | Scan a specific cluster only |
| `top` | no | `5` | Number of top savings opportunities to show |
| `post-comment` | no | `true` | Post results as a PR comment |

### Outputs

| Output | Description |
|--------|-------------|
| `total-savings` | Total potential monthly savings in USD |
| `scan-summary` | Full markdown summary (use in downstream steps) |

### Scan a specific cluster

```yaml
- uses: kubeopt/kubeopt@v1
  with:
    kubeopt-url:      ${{ secrets.KUBEOPT_URL }}
    kubeopt-username: ${{ secrets.KUBEOPT_USERNAME }}
    kubeopt-password: ${{ secrets.KUBEOPT_PASSWORD }}
    cluster-id:       prod-eks-us-east-1
    top:              10
```

### Notes

- The action checks out `kubeopt/kubeopt@v1` at runtime to run the scan. No local install needed.
- PR comments are upserted: re-running the action updates the existing comment rather than adding a new one.
- Requires `pull-requests: write` permission to post comments.
- The action does not modify your cluster. It is read-only.

---

## Architecture

```
                         KubeOpt Platform
 +----------------------------------------------------------+
 |                                                          |
 |   React SPA (Recharts)     FastAPI REST API (v2)         |
 |   frontend/dist/           presentation/api/v2/          |
 |                                                          |
 +---------------------------+------------------------------+
                             |
          +------------------+------------------+
          |                  |                  |
  +-------v------+  +-------v------+  +--------v-------+
  |  Algorithms  |  |  Analytics   |  |  ML Models     |
  |  (16 modules)|  |  Collectors  |  |  Anomaly Det.  |
  |  rightsizing |  |  Processors  |  |  CPU Optimizer |
  |  HPA, storage|  |  Scorer      |  |  Workload Cls  |
  +--------------+  +--------------+  +----------------+
          |                  |                  |
  +-------v------------------v------------------v-------+
  |              Cloud Provider Abstraction              |
  |  6 interfaces: Auth, Executor, Metrics, Costs,      |
  |                Accounts, Inspector                   |
  +---+-----------------+-----------------+-------------+
      |                 |                 |
  +---v---+        +----v----+       +----v----+
  | Azure |        |   AWS   |       |   GCP   |
  | (AKS) |        |  (EKS)  |       |  (GKE)  |
  +-------+        +---------+       +---------+
```

### Hosted Services (not in this repo)

| Service | Purpose | Endpoint |
|---------|---------|----------|
| Plan Generation | Generates optimization plans | plan.kubeopt.com |
| AI Chat | Conversational cluster analysis | ai.kubeopt.com |
| License Manager | License validation | license.kubeopt.com |

These services require a PRO or ENTERPRISE license. The core analysis engine works without them.

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend build)
- Cloud provider credentials (Azure, AWS, or GCP)

### Run Locally

```bash
# Clone and install
git clone https://github.com/kubeopt/kubeopt.git
cd kubeopt
pip install -r requirements.txt

# Set up credentials (copy and fill in your values)
cp .env.example .env

# Build frontend
cd frontend && npm install && npm run build && cd ..

# Run
python main.py
# Open http://localhost:5001
```

### Run with Docker

```bash
docker build -t kubeopt .
docker run -p 5001:5001 --env-file .env kubeopt
```

### Run via CLI

```bash
npx kubeopt clusters          # List clusters
npx kubeopt analyze <id>      # Run analysis
npx kubeopt report <id>       # View report
```

## Cloud Provider Setup

### Azure (AKS)

Set these environment variables:

```
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id
```

Requires a Service Principal with Reader role. See [docs/setup/AZURE-SETUP.md](docs/setup/AZURE-SETUP.md).

### AWS (EKS)

```
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_DEFAULT_REGION=us-east-1
```

Requires IAM user with EKS, Cost Explorer, and CloudWatch read access.

### Google Cloud (GKE)

```
GCP_SERVICE_ACCOUNT_KEY={"type":"service_account",...}
GCP_BILLING_DATASET=your_billing_dataset
GCP_BILLING_ACCOUNT_ID=your-billing-account-id
```

See [docs/setup/GCP-BILLING-SETUP.md](docs/setup/GCP-BILLING-SETUP.md).

## Project Structure

```
kubeopt/
  algorithms/          16 optimization algorithm modules
  analytics/           Cost collectors, processors, cluster scorer
  application/         Orchestrator, command generators
  infrastructure/
    cloud_providers/   Azure, AWS, GCP adapters (6 interfaces each)
    services/          Auth, caching, license validation, settings
    persistence/       Database, analysis engine
  machine_learning/    Anomaly detection, CPU optimizer, workload classifier
  presentation/
    api/v2/            FastAPI routers, schemas, dependencies
  frontend/            React SPA (TypeScript, Recharts, Tailwind)
  shared/
    standards/         16 YAML-based optimization standards
    config/            Application configuration
  mcp_server/          MCP server (6 tools, stdio transport)
```

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.11+, FastAPI, uvicorn |
| Frontend | React 19, TypeScript, Vite, Recharts, Tailwind CSS |
| ML | Pandas, NumPy, Scikit-learn |
| Cloud | Azure SDK, boto3, google-cloud SDK |
| Database | SQLite (dev), PostgreSQL (prod) |
| Deployment | Docker, Railway, Kubernetes |

## License

Apache License 2.0. See [LICENSE](LICENSE).

The core analysis engine is open source and free to use. Plan generation and AI chat are hosted services that require a [PRO or ENTERPRISE license](https://kubeopt.com/pricing).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Security

To report security vulnerabilities, email support@kubeopt.com. See [SECURITY.md](SECURITY.md).

---

Built by [Nivaya Technologies](https://nivaya.co.za)
