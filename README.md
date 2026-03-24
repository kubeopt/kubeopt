# KubeOpt

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://python.org)

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

To report security vulnerabilities, email security@kubeopt.com. See [SECURITY.md](SECURITY.md).

---

Built by [Nivaya Technologies](https://nivaya.co.za)
