# AKS Cost Optimizer

<div align="center">

![AKS Cost Optimizer](nivaya_kubeopt.png)

**Enterprise-Grade Azure Kubernetes Service Cost Optimization Tool**

[![License](https://img.shields.io/badge/license-Enterprise-blue.svg)](LICENSE)
[![Azure](https://img.shields.io/badge/Azure-Integrated-0078d4.svg)](https://azure.microsoft.com/)
[![Python](https://img.shields.io/badge/python-3.11+-3776ab.svg)](https://python.org/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ed.svg)](https://docker.com/)

*Developed by **Srinivas Kondepudi** for **Nivaya Technologies & kubeopt***

</div>

---

## 🎯 **Overview**

The AKS Cost Optimizer is a sophisticated enterprise-grade tool that provides comprehensive cost analysis and optimization for Azure Kubernetes Service environments. Built with Clean Architecture principles, it delivers real-time insights, machine learning-powered recommendations, and automated implementation planning.

### **Key Benefits**
- 🎯 **15-45% cost reduction** through intelligent resource optimization
- 🤖 **ML-powered insights** with anomaly detection and predictive analytics
- 🏢 **Enterprise features** including multi-subscription support and compliance
- 🔒 **Security-first design** with comprehensive input validation and threat protection
- 📊 **Real-time analysis** using Azure Cost Management and Monitor APIs

---

## 🚀 **Quick Start**

### **1. Build & Run (Most Secure)**
```bash
# Build with PyInstaller (default - most secure)
docker build -t aks-cost-optimizer .

# Run with Azure credentials and notifications
docker run -d -p 5000:5000 \
  -e AZURE_TENANT_ID=your-tenant-id \
  -e AZURE_CLIENT_ID=your-client-id \
  -e AZURE_CLIENT_SECRET=your-client-secret \
  -e AZURE_SUBSCRIPTION_ID=your-subscription-id \
  -e EMAIL_ENABLED=true \
  -e SMTP_USERNAME=your-email@domain.com \
  -e SMTP_PASSWORD=your-password \
  -e SLACK_ENABLED=true \
  -e SLACK_WEBHOOK_URL=your-webhook-url \
  aks-cost-optimizer
```

### **2. Access Your Tool**
```
http://localhost:5000
```

### **3. Configure Azure Credentials**
1. Go to **Settings** → **Azure Configuration**
2. Enter your Azure credentials
3. Click **"Test Azure Connection"**
4. Click **"Save Azure Settings"**

---

## 📁 **Project Structure**

### **🏗️ Clean Architecture Layout**

```
aks-cost-optimizer/
├── 📋 Core Application
│   ├── main.py                      # Main application entry point
│   ├── production_main.py           # Production entry point
│   └── requirements.txt             # Python dependencies
│
├── 🏗️ Clean Architecture Layers
│   ├── domain/                      # 🎯 Business Logic Layer
│   │   ├── entities/               # Business entities
│   │   ├── events/                 # Domain events
│   │   ├── repositories/           # Repository interfaces
│   │   ├── services/               # Domain services
│   │   └── value_objects/          # Value objects
│   │
│   ├── application/                 # 📋 Application Layer
│   │   ├── use_cases/              # Business use cases
│   │   │   ├── analyzers/          # Analysis use cases
│   │   │   ├── generators/         # Implementation generators
│   │   │   ├── models/             # Application models
│   │   │   ├── strategies/         # Optimization strategies
│   │   │   └── orchestrator.py     # Main orchestration logic
│   │   ├── dto/                    # Data transfer objects
│   │   └── services/               # Application services
│   │
│   ├── infrastructure/              # 🔧 Infrastructure Layer
│   │   ├── persistence/            # Data persistence
│   │   │   ├── database/           # SQLite databases
│   │   │   ├── processing/         # Data processing
│   │   │   └── scripts/            # Database utilities
│   │   ├── services/               # Infrastructure services
│   │   │   ├── azure_sdk_manager.py      # Azure SDK management
│   │   │   ├── subscription_manager.py   # Multi-subscription support
│   │   │   ├── license_manager.py        # License & tier management
│   │   │   ├── auto_analysis_scheduler.py # Background processing
│   │   │   └── cache_manager.py           # Caching system
│   │   ├── security/               # Security components
│   │   │   ├── security_posture_core.py  # Security analysis
│   │   │   ├── vulnerability_scanner.py  # Vulnerability detection
│   │   │   ├── compliance_framework.py   # Compliance checking
│   │   │   └── policy_analyzer.py        # Policy analysis
│   │   ├── caching/                # Caching layer
│   │   ├── messaging/              # Message handling
│   │   └── data/                   # Data processing
│   │
│   └── presentation/               # 🌐 Presentation Layer
│       ├── web/                    # Web interface
│       │   ├── templates/          # HTML templates
│       │   └── static/             # CSS, JS, images
│       ├── api/                    # REST API
│       │   ├── routes.py           # Main routes
│       │   ├── api_routes.py       # API endpoints
│       │   ├── auth_routes.py      # Authentication
│       │   └── license_routes.py   # License management
│       └── cli/                    # Command line interface
│
├── 📊 Analytics & ML
│   ├── analytics/                   # Cost analysis engine
│   │   ├── collectors/             # Data collection
│   │   │   ├── comprehensive_cost_collector.py    # Cost data collection
│   │   │   ├── aks_config_fetcher.py             # AKS configuration
│   │   │   └── aks_realtime_metrics.py           # Real-time metrics
│   │   ├── aggregators/            # Data aggregation
│   │   │   └── comprehensive_aks_analyzer.py     # Multi-dimensional analysis
│   │   └── processors/             # Data processing
│   │       ├── algorithmic_cost_analyzer.py      # Cost algorithms
│   │       ├── hpa_analyzer.py                   # HPA analysis
│   │       └── pod_cost_analyzer.py              # Pod-level cost analysis
│   │
│   └── machine_learning/           # ML & AI components
│       ├── core/                   # Core ML logic
│       │   ├── dynamic_plan_generator.py         # AI-powered planning
│       │   ├── enterprise_metrics.py             # Enterprise analytics
│       │   ├── ml_integration.py                 # ML integration layer
│       │   └── learn_optimize.py                 # Learning algorithms
│       ├── models/                 # ML models
│       │   ├── cost_anomaly_detection.py         # Anomaly detection
│       │   ├── cpu_optimization_planner.py       # CPU optimization
│       │   ├── workload_performance_analyzer.py  # Performance analysis
│       │   └── dna_analyzer.py                   # Workload DNA analysis
│       ├── training/               # Model training
│       ├── inference/              # Model inference
│       └── data/                   # ML data & models
│
├── ⚙️ Shared Components
│   └── shared/                     # Shared utilities
│       ├── config/                 # Configuration management
│       │   ├── config.py           # Main configuration
│       │   ├── cpu_optimization_config.py       # CPU config
│       │   └── environments.json   # Environment settings
│       ├── common/                 # Common utilities
│       │   └── input_validation.py # Input validation & security
│       ├── standards/              # Industry standards
│       │   ├── aks_concepts_standards.py        # AKS standards
│       │   ├── cost_optimization_standards.py   # Cost standards
│       │   ├── security_standards.py            # Security standards
│       │   └── performance_standards.py         # Performance standards
│       ├── utils/                  # Utility functions
│       ├── logging/                # Logging configuration
│       └── monitoring/             # Monitoring utilities
│
├── 🚀 Deployment
│   ├── deploy/                     # Deployment configurations
│   │   ├── docker/                 # Docker configurations
│   │   │   ├── Dockerfile.bytecode             # Bytecode protection
│   │   │   ├── Dockerfile.obfuscated           # Code obfuscation
│   │   │   ├── Dockerfile.pyinstaller          # PyInstaller build
│   │   │   ├── build-secure-containers.sh      # Multi-variant builds
│   │   │   ├── docker-compose.secure.yml       # Secure deployment
│   │   │   └── docker-entrypoint-binary.sh     # Binary entrypoint
│   │   ├── kubernetes/             # Kubernetes manifests
│   │   └── terraform/              # Infrastructure as Code
│   │
│   ├── Dockerfile                  # Default secure Dockerfile (PyInstaller)
│   ├── Dockerfile.production       # Production Dockerfile
│   ├── docker-compose.yml          # Development compose
│   ├── docker-compose.prod.yml     # Production compose
│   └── docker-entrypoint.sh        # Main entrypoint script
│
└── 📚 Documentation
    ├── docs/
    │   ├── setup/                  # Setup guides
    │   │   └── AZURE-SETUP.md      # Azure configuration
    │   ├── deployment/             # Deployment guides
    │   │   └── README.secure-containers.md      # Container security
    │   ├── architecture/           # Architecture documentation
    │   │   └── database-architecture.md         # Database design
    │   ├── features_aks.md         # AKS features documentation
    │   ├── features_nivaya.md      # Nivaya platform features
    │   └── PROJECT-STRUCTURE.md    # Project structure guide
    │
    ├── QUICK-START.md              # Quick setup guide
    ├── DEVELOPMENT-GUIDE.md        # Development setup
    ├── PRODUCTION-DEPLOYMENT.md    # Production deployment
    ├── LICENSE-MANAGEMENT-GUIDE.md # License management
    └── COMPREHENSIVE-ANALYSIS.md   # Complete technical analysis
```

---

## 🔧 **Key Components Explained**

### **1. Cost Analysis Engine**

**Location:** `analytics/`

**Core Files:**
- `collectors/comprehensive_cost_collector.py` - Enhanced Azure cost data collection
- `aggregators/comprehensive_aks_analyzer.py` - Multi-dimensional cost analysis  
- `processors/algorithmic_cost_analyzer.py` - Advanced cost optimization algorithms

**Features:**
- Real-time cost analysis via Azure Cost Management API
- Resource over-provisioning detection (>25% CPU, >20% memory gaps)
- Cost categorization (compute, storage, networking, monitoring)
- Savings calculation with confidence scoring

**Usage:**
```python
from analytics.collectors.comprehensive_cost_collector import ComprehensiveCostCollector

collector = ComprehensiveCostCollector()
cost_data = collector.collect_comprehensive_cost_data(subscription_id, cluster_name)
```

### **2. Machine Learning Module**

**Location:** `machine_learning/`

**Core Files:**
- `models/cost_anomaly_detection.py` - Advanced anomaly detection using Isolation Forest
- `models/cpu_optimization_planner.py` - CPU optimization planning with ML
- `models/workload_performance_analyzer.py` - Performance analysis and predictions
- `core/dynamic_plan_generator.py` - AI-powered implementation planning

**Features:**
- Cost anomaly detection with real-time alerting
- Memory-based HPA optimization (15-45% replica reduction)
- Workload DNA analysis for optimization recommendations
- Predictive modeling for capacity planning

**Usage:**
```python
from machine_learning.models.cost_anomaly_detection import CostAnomalyDetector

detector = CostAnomalyDetector()
anomalies = detector.detect_cost_anomalies(metrics_data)
```

### **3. Security Infrastructure**

**Location:** `infrastructure/security/`

**Core Files:**
- `security_posture_core.py` - Core security analysis engine
- `vulnerability_scanner.py` - Vulnerability detection and management
- `compliance_framework.py` - Compliance checking and reporting
- `shared/common/input_validation.py` - Input validation and sanitization

**Features:**
- Comprehensive input validation (XSS, SQL injection protection)
- Security posture analysis with compliance framework
- Vulnerability scanning with threat pattern detection
- Azure resource validation and sanitization

**Usage:**
```python
from shared.common.input_validation import InputValidator

validator = InputValidator()
result = validator.validate_cluster_name(cluster_name)
```

### **4. Enterprise Management**

**Location:** `infrastructure/services/`

**Core Files:**
- `subscription_manager.py` - Multi-subscription support with parallel processing
- `license_manager.py` - Tier-based feature controls (FREE/PRO/ENTERPRISE)
- `auto_analysis_scheduler.py` - Background processing and scheduled analysis
- `cache_manager.py` - Advanced caching with TTL and subscription isolation

**Features:**
- Multi-subscription support for enterprise environments
- License management with feature toggle controls
- Auto-analysis scheduling with configurable intervals
- Performance optimization through intelligent caching

**Usage:**
```python
from infrastructure.services.subscription_manager import azure_subscription_manager

subscriptions = azure_subscription_manager.get_available_subscriptions()
```

### **5. Web Interface & APIs**

**Location:** `presentation/`

**Core Files:**
- `api/routes.py` - Main application routes
- `api/api_routes.py` - REST API endpoints
- `api/auth_routes.py` - Authentication and session management
- `web/templates/` - HTML templates for web interface

**Features:**
- Modern web interface with responsive design
- RESTful API for programmatic access
- Authentication and authorization system
- Real-time dashboard with charts and metrics

**API Examples:**
```bash
# Get cluster analysis
GET /api/analyze/cluster/{cluster_name}

# Get cost optimization recommendations  
GET /api/optimize/cost/{cluster_name}

# Generate implementation plan
POST /api/generate/implementation-plan
```

---

## 🛠️ **Installation & Setup**

### **Prerequisites**
- Python 3.11+
- Docker and Docker Compose
- Azure CLI
- Azure subscription with appropriate permissions

### **Azure Permissions Required**
```json
{
  "permissions": [
    "Microsoft.ContainerService/managedClusters/read",
    "Microsoft.CostManagement/query/action", 
    "Microsoft.Insights/metrics/read",
    "Microsoft.Resources/subscriptions/read",
    "Microsoft.Authorization/roleAssignments/read"
  ]
}
```

### **Environment Variables**
```bash
# Azure Authentication
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id  
AZURE_CLIENT_SECRET=your-client-secret
AZURE_SUBSCRIPTION_ID=your-subscription-id

# Email Notifications (Optional)
EMAIL_ENABLED=true
SMTP_SERVER=smtpout.secureserver.net  # or smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@domain.com
SMTP_PASSWORD=your-email-password
EMAIL_RECIPIENTS=admin@company.com,devops@company.com

# Slack Notifications (Optional)
SLACK_ENABLED=true
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
SLACK_CHANNEL=#aks-cost-alerts

# Application Settings
FLASK_ENV=production
LOG_LEVEL=INFO
ENABLE_MULTI_SUBSCRIPTION=true
PARALLEL_PROCESSING=true
APP_URL=http://localhost:5001  # Base URL for dashboard links

# License Configuration (Optional)
LICENSE_TIER=enterprise  # free, pro, enterprise

# Development Settings (for .env.local in development)
FLASK_ENV=development     # Enable development mode
FLASK_DEBUG=true          # Enable Flask debug mode
LOG_LEVEL=DEBUG           # Verbose logging
PRODUCTION_MODE=false     # Disable production optimizations
kubeopt_DEV_MODE=true     # Enable full enterprise features
```

### **Development Setup**

1. **Clone and Setup:**
```bash
git clone <repository-url>
cd aks-cost-optimizer
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

2. **Configure Development Environment:**
```bash
# Copy development configuration template
cp config/examples/.env.development.example .env

# Edit .env with your Azure credentials and development settings
# Update Azure credentials and enable desired features

# Enable full Enterprise features for development
python3 dev-mode.py enable
```

3. **Start Development Server:**
```bash
# Start with development configuration
python3 main.py

# Or use Flask development server with hot reload
FLASK_ENV=development FLASK_DEBUG=true python3 main.py
```

4. **Access Development Application:**
```
http://localhost:5001
```

#### **Development Features:**
- 🔧 **Full Enterprise Features:** All features unlocked for development
- 🔄 **Hot Reload:** Automatic restart on code changes
- 📊 **Debug Logging:** Verbose logging for troubleshooting
- 🧪 **Test Configurations:** Lower thresholds for easier testing
- 📧 **Test Notifications:** Separate email/Slack for development

### **Production Deployment**

#### **Option 1: Docker (Recommended)**
```bash
# Build with PyInstaller (most secure)
docker build -t aks-cost-optimizer .

# Run in production mode with notifications
docker run -d -p 5000:5000 \
  --name aks-optimizer \
  -e AZURE_TENANT_ID=your-tenant-id \
  -e AZURE_CLIENT_ID=your-client-id \
  -e AZURE_CLIENT_SECRET=your-client-secret \
  -e AZURE_SUBSCRIPTION_ID=your-subscription-id \
  -e EMAIL_ENABLED=true \
  -e SMTP_USERNAME=your-email@domain.com \
  -e SMTP_PASSWORD=your-password \
  -e SLACK_ENABLED=true \
  -e SLACK_WEBHOOK_URL=your-webhook-url \
  -e APP_URL=https://your-domain.com \
  aks-cost-optimizer
```

#### **Option 2: Docker Compose**
```bash
# Development
docker-compose up -d

# Production  
docker-compose -f docker-compose.prod.yml up -d
```

#### **Option 3: Secure Container Variants**
```bash
# Build all secure variants
./deploy/docker/build-secure-containers.sh latest all

# Deploy with secure compose
docker-compose -f deploy/docker/docker-compose.secure.yml up -d
```

---

## 🔔 **Notifications Configuration**

The AKS Cost Optimizer supports multi-channel notifications for cost alerts, including Email, Slack, and In-app notifications.

### **Email Notifications**

Configure email notifications to receive alerts when cost thresholds are exceeded:

```bash
# Email Settings
EMAIL_ENABLED=true
SMTP_SERVER=smtpout.secureserver.net  # GoDaddy/Professional email
SMTP_PORT=587
SMTP_USERNAME=your-email@domain.com
SMTP_PASSWORD=your-email-password
EMAIL_RECIPIENTS=admin@company.com,devops@company.com
```

**Supported Email Providers:**
- **GoDaddy Email:** `smtpout.secureserver.net:587` (recommended for professional domains)
- **Gmail:** `smtp.gmail.com:587` (requires app-specific password)
- **Office 365:** `smtp-mail.outlook.com:587`
- **Custom SMTP:** Any SMTP server with STARTTLS support

### **Slack Notifications**

Configure Slack notifications for real-time team alerts:

```bash
# Slack Settings
SLACK_ENABLED=true
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
SLACK_CHANNEL=#aks-cost-alerts
```

**Slack Webhook Setup:**
1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Create a new app or select existing app
3. Go to "Incoming Webhooks" → "Add New Webhook to Workspace"
4. Select the channel and copy the webhook URL
5. Add the webhook URL to your environment configuration

**Slack Notification Features:**
- 🎯 **Rich Formatting:** Cost breakdowns with color-coded severity
- 🔗 **Clickable Links:** Direct links to cluster dashboards
- 🖱️ **Action Buttons:** "View Cluster Dashboard" and "View Portfolio" buttons
- 📊 **Detailed Metrics:** Current cost, threshold, overage amount, and percentage

### **In-App Notifications**

In-app notifications are enabled by default and appear in the dashboard:

- **Real-time Alerts:** Immediate notifications when alerts trigger
- **Notification History:** View past alerts and their status
- **Alert Management:** Mark as read, dismiss, or take action
- **Visual Indicators:** Color-coded severity levels

### **Alert Configuration**

Configure cost alert thresholds through the web interface:

1. **Go to Settings** → **Alerts Management**
2. **Create Alert:**
   - Alert Name: "Production Budget Alert"
   - Cluster: Select target cluster
   - Threshold: $1000.00 (monthly)
   - Notification Channels: Email, Slack, In-app
3. **Test Alert:** Use "Test Alert" button to verify notifications
4. **Monitor:** Alerts automatically trigger when thresholds are exceeded

**Notification Channels:**
- **Email:** Professional email alerts with detailed cost breakdown
- **Slack:** Real-time team notifications with dashboard links
- **In-app:** Dashboard notifications with full alert management

### **Security Considerations**

**Environment Variables:**
- Store sensitive data (passwords, webhook URLs) in `.env` (git-ignored)
- Use environment variables in production deployments
- Never commit secrets to version control

**Email Security:**
- Use app-specific passwords for Gmail (not regular password)
- Enable STARTTLS encryption (port 587 recommended)
- Validate recipient email addresses

**Slack Security:**
- Rotate webhook URLs periodically
- Limit webhook permissions to specific channels
- Monitor webhook usage in Slack admin panel

---

## 📊 **Usage Examples**

### **1. Basic Cost Analysis**
```bash
# Analyze specific cluster
curl -X GET "http://localhost:5000/api/analyze/cluster/my-aks-cluster" \
  -H "Authorization: Bearer your-token"

# Get cost breakdown
curl -X GET "http://localhost:5000/api/cost/breakdown/my-aks-cluster"
```

### **2. Optimization Recommendations**
```bash
# Get optimization recommendations
curl -X GET "http://localhost:5000/api/optimize/recommendations/my-aks-cluster"

# Generate implementation plan
curl -X POST "http://localhost:5000/api/generate/implementation-plan" \
  -H "Content-Type: application/json" \
  -d '{"cluster_name": "my-aks-cluster", "optimization_level": "aggressive"}'
```

### **3. Security Analysis**
```bash
# Security posture analysis
curl -X GET "http://localhost:5000/api/security/posture/my-aks-cluster"

# Compliance check
curl -X GET "http://localhost:5000/api/security/compliance/my-aks-cluster"
```

### **4. ML-Powered Insights**
```bash
# Anomaly detection
curl -X GET "http://localhost:5000/api/ml/anomalies/my-aks-cluster"

# Performance predictions
curl -X GET "http://localhost:5000/api/ml/predictions/my-aks-cluster"
```

---

## 🔒 **Security Features**

### **Input Validation & Sanitization**
```python
# Comprehensive input validation
DANGEROUS_PATTERNS = [
    r'<script[^>]*>.*?</script>',  # Script tags
    r'javascript:',                # JavaScript URLs
    r'union\s+select',            # SQL injection  
    r'drop\s+table',              # SQL injection
]
```

### **Container Security**
- **PyInstaller Protection:** Source code compiled to standalone executable
- **Non-root Execution:** Containers run as non-privileged user (1000:1000)
- **Minimal Attack Surface:** Production containers exclude source code
- **Multi-variant Builds:** Bytecode compilation and obfuscation options

### **Authentication & Authorization**
- **Azure AD Integration:** Native Azure authentication support
- **Session Management:** Secure session handling with timeout
- **Role-based Access:** Tier-based feature controls
- **API Security:** Token-based authentication for API access

---

## 🚀 **Performance Optimization**

### **Caching System**
```python
# Multi-level caching with subscription awareness
analysis_cache = {
    'clusters': {},           # Cluster-specific data
    'subscriptions': {},      # Subscription-level data
    'global_ttl_hours': 0.10, # Cache TTL
    'subscription_isolation_enabled': True
}
```

### **Background Processing**
- **Asynchronous Analysis:** Non-blocking analysis execution
- **Thread Pool Management:** CPU-aware thread pool sizing
- **Resource Optimization:** Memory and connection management
- **Scheduled Tasks:** Auto-analysis with configurable intervals

### **Database Optimization**
- **Connection Pooling:** Efficient database connection management
- **Query Optimization:** Optimized queries with proper indexing
- **Data Processing:** Pandas integration for efficient data manipulation
- **Multi-database Architecture:** Separate databases for different concerns

---

## 📈 **Monitoring & Observability**

### **Logging**
```python
# Structured logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(threadName)s] - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
```

### **Health Checks**
```bash
# Application health
curl -f http://localhost:5000/health

# Azure connectivity
curl -f http://localhost:5000/health/azure

# Database status
curl -f http://localhost:5000/health/database
```

### **Metrics & Analytics**
- **Real-time Metrics:** Live dashboard with performance indicators
- **Cost Tracking:** Historical cost trends and projections
- **Usage Analytics:** Feature usage and adoption metrics
- **Performance Monitoring:** Response times and resource utilization

---

## 🔧 **Configuration Management**

### **Tier-based Features**

| Feature | FREE | PRO | ENTERPRISE |
|---------|------|-----|------------|
| **Basic Cost Analysis** | ✅ | ✅ | ✅ |
| **Optimization Recommendations** | Limited | ✅ | ✅ |
| **Implementation Plans** | ❌ | ✅ | ✅ |
| **ML-powered Insights** | ❌ | ❌ | ✅ |
| **Security Analysis** | ❌ | ❌ | ✅ |
| **Multi-subscription Support** | ❌ | ❌ | ✅ |
| **Auto-analysis Scheduling** | ❌ | ❌ | ✅ |
| **Enterprise Metrics** | ❌ | ❌ | ✅ |

### **Environment Configuration**
```bash
# Development mode (full features)
python3 dev-mode.py enable

# Production mode (license-based)  
python3 dev-mode.py disable

# Check current status
python3 dev-mode.py status
```

---

## 🧪 **Testing & Quality Assurance**

### **Current Testing Status**
⚠️ **Critical Gap:** Comprehensive test suite needed

### **Recommended Test Structure**
```
tests/
├── unit/                    # Unit tests
│   ├── test_cost_analyzer.py
│   ├── test_ml_models.py
│   ├── test_security.py
│   └── test_azure_integration.py
├── integration/             # Integration tests  
│   ├── test_database.py
│   └── test_api_endpoints.py
├── e2e/                    # End-to-end tests
│   └── test_complete_workflow.py
└── fixtures/               # Test data
    ├── azure_responses.json
    └── sample_clusters.json
```

### **Quality Metrics**
- **Code Coverage Target:** 80%+
- **Test Types:** Unit, Integration, E2E
- **Azure API Mocking:** Complete Azure SDK mocking
- **Performance Testing:** Load and stress testing

---

## 🤝 **Contributing**

### **Development Workflow**
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for new functionality
4. Ensure all tests pass
5. Update documentation
6. Submit pull request

### **Code Standards**
- **Architecture:** Follow Clean Architecture principles
- **Code Style:** PEP 8 compliance with type hints
- **Security:** Input validation for all external inputs
- **Documentation:** Comprehensive docstrings and comments
- **Testing:** Test coverage for all new features

### **Security Guidelines**
- **No Hardcoded Secrets:** Use environment variables or Azure Key Vault
- **Input Validation:** Validate and sanitize all user inputs
- **Dependency Management:** Regular security updates and vulnerability scanning
- **Container Security:** Follow security best practices for container deployment

---

## 📚 **Documentation**

### **Available Documentation**
- 📋 **[Quick Start Guide](QUICK-START.md)** - Get started in 5 minutes
- 🔧 **[Development Guide](DEVELOPMENT-GUIDE.md)** - Development setup and workflow
- 🚀 **[Production Deployment](PRODUCTION-DEPLOYMENT.md)** - Production deployment guide
- 🔒 **[Security Guide](docs/deployment/README.secure-containers.md)** - Container security
- 🏗️ **[Architecture Guide](docs/architecture/database-architecture.md)** - System architecture
- ⚙️ **[Azure Setup](docs/setup/AZURE-SETUP.md)** - Azure configuration guide
- 📊 **[Comprehensive Analysis](COMPREHENSIVE-ANALYSIS.md)** - Complete technical analysis

### **API Documentation**
*Coming Soon: OpenAPI/Swagger documentation*

---

## 🛡️ **License & Support**

### **License Tiers**
- **FREE:** Basic cost analysis and recommendations
- **PRO:** Advanced optimization and implementation planning  
- **ENTERPRISE:** Full ML features, security analysis, and multi-subscription support

### **Support**
- **Documentation:** Comprehensive guides and tutorials
- **Community:** GitHub issues and discussions
- **Enterprise Support:** Available for ENTERPRISE tier customers

### **Contact**
- **Developer:** Srinivas Kondepudi
- **Organization:** Nivaya Technologies & kubeopt
- **Email:** [Contact through GitHub issues]
- **Website:** kubeopt.io

---

## 🎯 **Roadmap**

### **Phase 1: Foundation (Completed)**
- ✅ Clean Architecture implementation
- ✅ Azure integration and authentication
- ✅ Basic cost analysis and optimization
- ✅ Web interface and API development

### **Phase 2: Advanced Features (In Progress)**
- 🔄 Machine learning integration
- 🔄 Security analysis and compliance
- 🔄 Multi-subscription support
- 🔄 Enterprise features and licensing

### **Phase 3: Production Readiness (Planned)**
- 📋 Comprehensive test suite
- 📋 API documentation (OpenAPI/Swagger)
- 📋 Security hardening and vulnerability management
- 📋 Performance optimization and monitoring

### **Phase 4: Scale & Innovation (Future)**
- 📋 Microservices architecture
- 📋 Kubernetes-native deployment
- 📋 Advanced ML models and predictions
- 📋 Integration with external tools

---

<div align="center">

**⭐ Star this repository if you find it useful!**

**Built with ❤️ by the Nivaya Technologies & kubeopt team**

</div>