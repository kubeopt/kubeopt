# 🎯 **KubeOpt - Complete Architecture & Code Flow Guide**

> **Developer:** Srinivas Kondepudi  
> **Organization:** Nivaya Technologies & kubeopt  
> **Project:** AKS Cost Optimizer (KubeOpt)

---

## 📋 **Table of Contents**
1. [High-Level Overview](#high-level-overview)
2. [System Architecture](#system-architecture)
3. [Complete Code Flow](#complete-code-flow)
4. [File-by-File Interactions](#file-by-file-interactions)
5. [Execution Paths](#execution-paths)
6. [Data Flow](#data-flow)
7. [Component Dependencies](#component-dependencies)
8. [Deployment Guide](#deployment-guide)
9. [Optimization Guide](#optimization-guide)

---

## 🏗️ **High-Level Overview**

**KubeOpt** is a comprehensive AKS cost optimization platform with:
- 🤖 **Automated cost analysis** with ML-powered insights
- 🛡️ **Security compliance scanning** 
- 📊 **Real-time dashboards** with actionable recommendations
- 🔄 **Hands-off automation** with intelligent scheduling
- 🌐 **Multi-subscription support** for enterprise environments

---

## 🏗️ **System Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                        🌐 KubeOpt Platform                      │
├─────────────────────────────────────────────────────────────────┤
│  Presentation Layer   │  Application Layer    │  Infrastructure │
│  ─────────────────    │  ────────────────────  │  ─────────────  │
│  • Web UI (Flask)    │  • Business Logic      │  • Data Storage │
│  • REST APIs         │  • ML Models           │  • External APIs│
│  • Authentication    │  • Analysis Engine     │  • Caching      │
│  • Auto Refresh      │  • Scheduler           │  • Security     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 **Complete Code Flow**

### **1. Application Bootstrap Flow**

```
main.py (Entry Point)
    ↓
shared/config/config.py (Global Configuration)
    ↓
presentation/web/main.py (Flask App Setup)
    ↓
[Route Registration]
    ├── presentation/api/auth_routes.py (Authentication)
    ├── presentation/api/routes.py (Web Routes)
    ├── presentation/api/api_routes.py (API Endpoints)
    └── presentation/api/license_routes.py (Licensing)
    ↓
[Service Initialization]
    ├── infrastructure/services/auto_analysis_scheduler.py
    ├── infrastructure/services/azure_sdk_manager.py
    ├── infrastructure/services/auth_manager.py
    └── infrastructure/persistence/cluster_database.py
```

### **2. Request Processing Flow**

```
HTTP Request → Flask Router → Authentication → Business Logic → Data Access → Response
     ↓              ↓              ↓               ↓               ↓            ↓
   Browser    auth_routes.py  auth_manager.py  api_routes.py  cluster_database.py  JSON/HTML
     ↑                                                             ↓
   User                                                        SQLite DBs
```

### **3. Auto Analysis Flow**

```
Background Scheduler Thread
    ↓
auto_analysis_scheduler.py._scheduler_loop()
    ↓
Check Analysis Interval (100 minutes default)
    ↓
Trigger Analysis via Internal API Call
    ↓
api_routes.py./api/clusters/<id>/analyze
    ↓
analytics/collectors/comprehensive_cost_collector.py
    ↓
Azure SDK Data Collection
    ↓
machine_learning/core/ml_integration.py
    ↓
application/use_cases/orchestrator.py
    ↓
infrastructure/persistence/cluster_database.py
    ↓
Update Database & Cache
```

---

## 📁 **File-by-File Interactions**

### **Entry Points**
```
main.py
├── Loads environment variables
├── Imports shared/config/config.py
├── Creates Flask app
├── Calls presentation/web/main.py.create_app()
└── Starts development server

production_main.py (Production Entry)
├── Same as main.py but with production configurations
└── WSGI-ready setup
```

### **Configuration & Globals**
```
shared/config/config.py
├── Sets up logging
├── Initializes global managers:
│   ├── enhanced_cluster_manager (cluster_database.py)
│   ├── azure_subscription_manager (subscription_manager.py)
│   ├── auth_manager (auth_manager.py)
│   └── auto_scheduler (auto_analysis_scheduler.py)
├── Creates thread-safe analysis storage
└── Configures Azure SDK connections
```

### **Presentation Layer**
```
presentation/web/main.py
├── create_app() function
├── Registers all route modules:
│   ├── auth_routes.py → /login, /logout, /register
│   ├── routes.py → /, /dashboard, /settings
│   ├── api_routes.py → /api/* endpoints
│   └── license_routes.py → /license/*
├── Sets up static file serving
└── Initializes template engine

presentation/api/api_routes.py (MAIN API ENDPOINTS)
├── /api/clusters → CRUD cluster operations
├── /api/clusters/<id>/analyze → Trigger analysis
├── /api/clusters/<id>/analysis-status → Get status
├── /api/scheduler/* → Auto scheduler control
├── /api/portfolio/summary → Dashboard data
├── /api/security/* → Security endpoints
└── Integration with:
    ├── infrastructure/persistence/cluster_database.py
    ├── analytics/collectors/comprehensive_cost_collector.py
    ├── machine_learning/core/ml_integration.py
    └── infrastructure/services/auto_analysis_scheduler.py
```

### **Infrastructure Layer**
```
infrastructure/services/auto_analysis_scheduler.py
├── AutoAnalysisScheduler class
├── Runs in background thread
├── _scheduler_loop() every 100 minutes
├── _trigger_cluster_analysis() calls API internally
├── Integrates with:
│   ├── shared/config/config.py (global config)
│   ├── presentation/api/api_routes.py (internal API calls)
│   └── infrastructure/persistence/cluster_database.py
└── Status exposed via /api/scheduler/* endpoints

infrastructure/persistence/cluster_database.py
├── ClusterDatabaseManager class
├── SQLite database operations
├── Methods:
│   ├── get_clusters_with_subscription_info()
│   ├── store_analysis_result()
│   ├── update_analysis_status()
│   └── cleanup_stale_analysis_statuses()
├── Database files:
│   ├── clusters.db (main cluster data)
│   ├── ml_analytics.db (ML results)
│   └── security_analytics.db (security scans)
└── Used by all API endpoints and schedulers

infrastructure/services/azure_sdk_manager.py
├── AzureSDKManager class
├── Handles Azure API authentication
├── Resource discovery and data collection
├── Cost Management API integration
└── Used by analytics collectors
```

### **Analytics & ML Layer**
```
analytics/collectors/comprehensive_cost_collector.py
├── Collects cost data from Azure
├── Processes metrics and resource usage
├── Integrates with:
│   ├── infrastructure/services/azure_sdk_manager.py
│   └── analytics/collectors/aks_realtime_metrics.py
└── Feeds data to ML models

machine_learning/core/ml_integration.py
├── ML model orchestration
├── Feature engineering
├── Prediction generation
├── Integrates with:
│   ├── machine_learning/models/*.py
│   ├── analytics data collectors
│   └── application/use_cases/orchestrator.py
└── Stores results in ml_analytics.db

application/use_cases/orchestrator.py
├── Business logic orchestration
├── Combines cost analysis + ML predictions
├── Generates optimization recommendations
├── Creates implementation plans
└── Returns structured results to API layer
```

### **Frontend Layer**
```
presentation/web/templates/
├── base.html → Base template with navigation
├── cluster_portfolio.html → Main dashboard (calls JavaScript)
├── unified_dashboard.html → Analysis results view
└── settings.html → Configuration page

presentation/web/static/js/
├── global-refresh-manager.js → Silent page refresh system
├── auto-analysis-scheduler.js → Scheduler UI widget
├── cluster-portfolio.js → Main dashboard interactions
├── charts.js → Data visualization
├── enhanced-ui.js → Dynamic UI updates
└── security/ → Security dashboard components

JavaScript → API Flow:
cluster-portfolio.js
├── Calls /api/clusters (GET) → Load cluster list
├── Calls /api/clusters (POST) → Add new cluster
├── Calls /api/clusters/<id>/analyze (POST) → Trigger analysis
└── Updates UI based on responses

global-refresh-manager.js
├── Runs page refresh every 60 seconds (when user inactive)
├── Replaced old API polling system
└── Reduces server load significantly
```

---

## 🎯 **Execution Paths**

### **Path 1: User Adds New Cluster**
```
1. User fills form in cluster_portfolio.html
2. cluster-portfolio.js.submitForm() 
3. POST /api/clusters
4. api_routes.py.api_clusters()
5. cluster_database.py.add_cluster()
6. SQLite INSERT into clusters.db
7. Return success JSON
8. JavaScript updates UI
```

### **Path 2: Manual Analysis Trigger**
```
1. User clicks "Analyze" button
2. cluster-portfolio.js.triggerAnalysis()
3. POST /api/clusters/<id>/analyze  
4. api_routes.py.api_analyze_cluster()
5. comprehensive_cost_collector.py.collect_cost_data()
6. azure_sdk_manager.py → Azure APIs
7. ml_integration.py.process_analysis()
8. orchestrator.py.generate_recommendations()
9. cluster_database.py.store_analysis_result()
10. Return analysis results JSON
```

### **Path 3: Automatic Scheduled Analysis**
```
1. auto_analysis_scheduler.py._scheduler_loop() (background thread)
2. Check if 100 minutes elapsed
3. _run_scheduled_analysis()
4. Get cluster list from cluster_database.py
5. For each cluster: _trigger_cluster_analysis()
6. Internal API call to /api/clusters/<id>/analyze
7. Same flow as Path 2 (steps 4-10)
8. Schedule next run
```

### **Path 4: Dashboard Data Loading**
```
1. User visits / or /dashboard
2. routes.py.cluster_portfolio()
3. cluster_database.py.get_portfolio_summary()
4. Render cluster_portfolio.html with data
5. JavaScript loads additional data:
   - /api/clusters → Get cluster list
   - /api/portfolio/summary → Get metrics
6. charts.js renders visualizations
```

### **Path 5: Auto Refresh System**
```
1. global-refresh-manager.js initializes on page load
2. Detects user activity (mouse, keyboard, scroll)
3. Every 60 seconds: check if user inactive for 30+ seconds
4. If inactive: window.location.reload() (silent page refresh)
5. No API polling → Reduced server load
```

---

## 📊 **Data Flow**

### **Data Sources → Processing → Storage → UI**
```
Azure APIs
    ↓
azure_sdk_manager.py (Authentication & Collection)
    ↓
comprehensive_cost_collector.py (Data Processing)
    ↓
ml_integration.py (ML Analysis)
    ↓
orchestrator.py (Business Logic)
    ↓
cluster_database.py (Storage)
    ↓
SQLite Databases:
├── clusters.db (cluster info, analysis results)
├── ml_analytics.db (ML predictions, models)
├── security_analytics.db (security scans)
└── operational_data.db (operational metrics)
    ↓
API Endpoints (api_routes.py)
    ↓
Frontend JavaScript
    ↓
User Interface
```

### **Database Schema Flow**
```
clusters.db (Main Database)
├── clusters table → Basic cluster info
├── analysis_results → Cost analysis data  
├── analysis_status → Current analysis state
├── optimization_recommendations → ML suggestions
└── implementation_plans → Actionable steps

ml_analytics.db
├── training_data → Historical patterns
├── model_predictions → Future cost predictions
├── feature_importance → ML model insights
└── anomaly_detection → Cost anomalies

security_analytics.db
├── security_scans → Compliance results
├── vulnerability_data → Security issues
├── policy_violations → Configuration problems
└── compliance_scores → Security metrics
```

---

## 🔧 **Component Dependencies**

### **Critical Dependencies Map**
```
auto_analysis_scheduler.py
├── Depends on: Flask app context
├── Uses: cluster_database.py (data access)
├── Calls: api_routes.py (internal API)
└── Status: Core component - DO NOT DISABLE

cluster_database.py  
├── Depends on: SQLite files
├── Used by: All API endpoints, scheduler, ML models
├── Status: Core component - Central data hub
└── Thread-safe: Yes (with locks)

global-refresh-manager.js
├── Depends on: Browser DOM
├── Replaces: Old API polling system
├── Reduces: Server load by 80%+
└── Status: Optimization component

api_routes.py
├── Depends on: Flask, auth_manager, cluster_database
├── Exposes: All REST endpoints
├── Used by: Frontend, scheduler, external tools
└── Status: Core component - Main interface

auth_manager.py
├── Depends on: Session storage
├── Used by: All protected routes
├── Provides: Authentication, authorization
└── Status: Core component - Security layer
```

### **Optional vs Critical Components**
```
✅ CRITICAL (DO NOT REMOVE):
├── auto_analysis_scheduler.py → Auto analysis
├── cluster_database.py → Data storage
├── api_routes.py → API interface
├── auth_manager.py → Security
├── azure_sdk_manager.py → Azure integration
└── ml_integration.py → ML analysis

⚠️ IMPORTANT (NEEDED FOR FULL FEATURES):
├── routes.py → Web UI
├── comprehensive_cost_collector.py → Data collection
├── orchestrator.py → Business logic
└── global-refresh-manager.js → UI optimization

🔧 OPTIONAL (UI ENHANCEMENTS):
├── auto-analysis-scheduler.js → Scheduler UI widget
├── charts.js → Visualizations  
├── enhanced-ui.js → UI polish
└── security/ JavaScript → Security dashboards
```

---

## 🚀 **Deployment Guide**

### **For New Developers**
1. **Environment Setup:**
   ```bash
   git clone <repository>
   cd aks-cost-optimizer
   cp .env.example .env
   # Edit .env with Azure credentials
   ```

2. **Dependencies:**
   ```bash
   pip install -r requirements.txt
   # Azure CLI installed and authenticated
   # Kubernetes access configured
   ```

3. **Database Initialization:**
   ```bash
   python -c "from infrastructure.persistence.cluster_database import ClusterDatabaseManager; ClusterDatabaseManager().create_tables()"
   ```

4. **Run Application:**
   ```bash
   python main.py  # Development
   python production_main.py  # Production
   ```

### **For Operations Teams**
1. **Docker Deployment:**
   ```bash
   docker-compose up -d
   # Access at http://localhost:5020
   ```

2. **Environment Variables:**
   ```bash
   AZURE_TENANT_ID=<tenant-id>
   AZURE_CLIENT_ID=<client-id>  
   AZURE_CLIENT_SECRET=<secret>
   FLASK_ENV=production
   ```

3. **Health Checks:**
   ```bash
   curl http://localhost:5020/health
   curl http://localhost:5020/api/scheduler/status
   ```

### **For End Users**
1. **Initial Setup:**
   - Login with credentials
   - Add Azure subscription details
   - Add AKS clusters to monitor

2. **Daily Usage:**
   - Dashboard auto-refreshes with latest data
   - Analysis runs automatically every 100 minutes
   - Alerts notify of cost anomalies

3. **Actions:**
   - Export cost reports (PDF, Excel)
   - Download optimization scripts
   - Implement recommendations

---

## 🎯 **Optimization Guide**

### **Current Optimizations Applied**
✅ **Reduced API Polling:** 
- Replaced frequent `/api/clusters` calls with silent page refresh
- Reduced server load by 80%+

✅ **Database Optimizations:**
- Added cleanup for stale analysis statuses
- Implemented connection pooling
- Added database indexes

✅ **Caching Layer:**
- Azure API response caching
- Analysis result caching
- Session caching

### **Further Optimization Opportunities**
🔄 **Database Migration:**
- SQLite → PostgreSQL for better concurrency
- Redis for session storage
- Time-series database for metrics

🔄 **API Optimizations:**
- GraphQL for flexible data queries
- API rate limiting
- Response compression

🔄 **Frontend Optimizations:**
- JavaScript bundling and minification
- Image optimization
- Service worker for offline support

### **Scaling Considerations**
📈 **Horizontal Scaling:**
- Separate analysis workers
- Load balancer for multiple instances
- Distributed caching

📈 **Performance Monitoring:**
- APM integration (New Relic, DataDog)
- Custom metrics dashboard
- Error tracking and alerts

---

## 📞 **Support & Handover**

### **Key Contacts**
- **Developer:** Srinivas Kondepudi (Nivaya Technologies)
- **Organization:** kubeopt
- **Project:** AKS Cost Optimizer → KubeOpt

### **Critical Knowledge Transfer**
1. **Auto Scheduler:** Never disable `auto_analysis_scheduler.py` - it's the heart of automation
2. **Database:** `cluster_database.py` is the central data hub - all components depend on it
3. **API Polling:** Fixed with `global-refresh-manager.js` - don't revert to old polling
4. **Authentication:** `auth_manager.py` handles all security - maintain session management
5. **Azure Integration:** `azure_sdk_manager.py` requires proper credentials and permissions

### **Emergency Procedures**
- **Database Issues:** Run `infrastructure/persistence/scripts/fix_database.py`
- **Scheduler Stuck:** Restart via `/api/scheduler/stop` then `/api/scheduler/start`
- **High Load:** Check `global-refresh-manager.js` is active (not old polling)
- **Authentication:** Clear sessions and restart auth service

---

## 🏆 **Summary**

**KubeOpt** is a sophisticated, enterprise-ready platform that transforms AKS cost management from reactive to proactive. The architecture is designed for:

- 🔄 **Zero-touch automation** with intelligent scheduling
- 🧠 **ML-powered insights** for predictive optimization  
- 🛡️ **Security-first** design with comprehensive compliance
- 📊 **Real-time visibility** with actionable recommendations
- 🌐 **Enterprise scale** supporting multiple subscriptions

The codebase follows clean architecture principles with clear separation of concerns, making it maintainable and extensible for future enhancements.

---

*This guide serves as the complete reference for understanding, maintaining, and extending the KubeOpt platform. Keep this documentation updated as the system evolves.*