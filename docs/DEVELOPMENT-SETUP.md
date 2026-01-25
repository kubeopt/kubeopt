# AKS Cost Optimizer - Development Setup Guide

**Target Audience:** Developers, Contributors, Technical Team  
**Prerequisites:** Python 3.11+, Docker, Azure CLI  
**Setup Time:** 15-30 minutes  

---

## 📋 **Table of Contents**

1. [Quick Setup](#quick-setup)
2. [Development Environment](#development-environment)
3. [IDE Configuration](#ide-configuration)
4. [Testing Setup](#testing-setup)
5. [Docker Development](#docker-development)
6. [Azure Integration](#azure-integration)
7. [Debugging Guide](#debugging-guide)
8. [Code Quality Tools](#code-quality-tools)
9. [Development Workflow](#development-workflow)
10. [Troubleshooting](#troubleshooting)

---

## 🚀 **Quick Setup**

### **1-Minute Setup (Development Mode)**

```bash
# Clone repository
git clone <repository-url>
cd aks-cost-optimizer

# Setup Python environment
python3.11 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Enable development mode (unlocks all features)
python3 dev-mode.py enable

# Start development server
python3 main.py
```

**Access:** http://localhost:5001

### **Development Mode Features**
- 🔧 **Red "DEV MODE"** indicator in top-right corner
- 🏢 **Full Enterprise tier** with all features unlocked
- 📋 **Implementation Plans** visible and working
- 📊 **Enterprise Metrics** tab enabled
- 🔒 **Security Posture** tab enabled
- 📧 **Email/Slack Alerts** working
- 🤖 **Auto-Analysis** enabled

---

## 🛠️ **Development Environment**

### **System Requirements**

| Component | Requirement | Notes |
|-----------|-------------|--------|
| **Python** | 3.11+ | Required for modern type hints |
| **Memory** | 8GB+ | ML models and data processing |
| **Storage** | 10GB+ | Dependencies and data |
| **CPU** | 4+ cores | Parallel processing |

### **Prerequisites Installation**

#### **macOS**
```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11
brew install python@3.11

# Install Azure CLI
brew install azure-cli

# Install Docker Desktop
brew install --cask docker

# Install Git (if not already installed)
brew install git
```

#### **Ubuntu/Debian**
```bash
# Update package manager
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev -y

# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Install Docker
sudo apt install docker.io docker-compose -y
sudo usermod -aG docker $USER

# Install development tools
sudo apt install git build-essential -y
```

#### **Windows**
```powershell
# Install using Chocolatey
choco install python311 azure-cli docker-desktop git -y

# Or use winget
winget install Python.Python.3.11
winget install Microsoft.AzureCLI
winget install Docker.DockerDesktop
winget install Git.Git
```

### **Project Setup**

#### **1. Repository Setup**
```bash
# Clone repository
git clone <repository-url>
cd aks-cost-optimizer

# Check Python version
python3.11 --version  # Should be 3.11+

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

#### **2. Dependencies Installation**
```bash
# Install base requirements
pip install -r requirements.txt

# Install development requirements
pip install -r requirements/dev.txt

# Install ML requirements (optional)
pip install -r requirements/ml.txt

# Verify installation
python -c "import flask, azure.identity, sklearn, pandas; print('All dependencies installed successfully')"
```

#### **3. Environment Configuration**
```bash
# Create development environment file
cp config/examples/.env.example .env.development

# Edit .env.development with your settings
nano .env.development
```

**Development Environment File (.env.development):**
```bash
# ===========================
# Development Configuration
# ===========================

# Azure Configuration (Required for full functionality)
AZURE_TENANT_ID=your-dev-tenant-id
AZURE_CLIENT_ID=your-dev-client-id
AZURE_CLIENT_SECRET=your-dev-client-secret
AZURE_SUBSCRIPTION_ID=your-dev-subscription-id

# Application Settings
FLASK_ENV=development
FLASK_DEBUG=1
LOG_LEVEL=DEBUG
SECRET_KEY=dev-secret-key-change-in-production

# Development Features
ENABLE_MULTI_SUBSCRIPTION=true
PARALLEL_PROCESSING=false  # Easier debugging
DEV_MODE=true
SKIP_AZURE_AUTH=false  # Set to true for local development without Azure

# Database
DATABASE_PATH=./dev_data/aks_optimizer.db
ML_DATA_PATH=./dev_data/ml_models

# Performance (Development optimized)
CACHE_TTL_HOURS=0.05  # 3 minutes for faster development
MAX_ANALYSIS_THREADS=2
BACKGROUND_PROCESSING_ENABLED=false  # Manual testing

# Debugging
ENABLE_PROFILING=true
ENABLE_DEBUG_TOOLBAR=true
SQLALCHEMY_ECHO=true  # SQL query logging
```

#### **4. Development Mode Activation**
```bash
# Enable development mode (unlocks all enterprise features)
python3 dev-mode.py enable

# Check status
python3 dev-mode.py status

# Test different tiers
python3 dev-mode.py tier --tier free      # Test FREE tier limitations
python3 dev-mode.py tier --tier pro       # Test PRO tier features
python3 dev-mode.py tier --tier enterprise # Test ENTERPRISE features
```

#### **5. Start Development Server**
```bash
# Start with auto-reload
python3 main.py

# Or use development entry point
python3 main_dev.py

# Access application
open http://localhost:5001
```

---

## 💻 **IDE Configuration**

### **Visual Studio Code Setup**

#### **Required Extensions**
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.flake8",
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-python.mypy-type-checker",
    "ms-vscode.vscode-typescript-next",
    "bradlc.vscode-tailwindcss",
    "ms-azuretools.vscode-docker",
    "ms-vscode.azure-account"
  ]
}
```

#### **VS Code Settings (.vscode/settings.json)**
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length=88"],
  "python.sortImports.args": ["--profile", "black"],
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.pytestArgs": [
    "tests"
  ],
  "files.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/venv": true,
    "**/*.pyc": true
  },
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

#### **Launch Configuration (.vscode/launch.json)**
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug AKS Optimizer",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/main.py",
      "console": "integratedTerminal",
      "envFile": "${workspaceFolder}/.env.development",
      "args": [],
      "justMyCode": false
    },
    {
      "name": "Debug Tests",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["tests/", "-v"],
      "console": "integratedTerminal",
      "envFile": "${workspaceFolder}/.env.test"
    },
    {
      "name": "Debug ML Models",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/machine_learning/core/ml_integration.py",
      "console": "integratedTerminal",
      "envFile": "${workspaceFolder}/.env.development"
    }
  ]
}
```

### **PyCharm Setup**

#### **Project Structure**
```
Project Settings > Project Structure:
- Mark 'venv' as Excluded
- Mark 'tests' as Test Sources Root
- Mark project root as Sources Root
```

#### **Code Style Configuration**
```
Settings > Editor > Code Style > Python:
- Use Black formatter
- Line length: 88
- Import organization: isort compatible
```

#### **Run Configurations**
```xml
<!-- AKS Optimizer Debug -->
<configuration name="Debug Main" type="PythonConfigurationType">
  <module name="__main__" />
  <option name="INTERPRETER_OPTIONS" value="" />
  <option name="PARENT_ENVS" value="true" />
  <envs>
    <env name="FLASK_ENV" value="development" />
    <env name="FLASK_DEBUG" value="1" />
  </envs>
  <option name="SDK_HOME" value="./venv/bin/python" />
  <option name="WORKING_DIRECTORY" value="$PROJECT_DIR$" />
  <option name="IS_MODULE_SDK" value="false" />
  <option name="ADD_CONTENT_ROOTS" value="true" />
  <option name="ADD_SOURCE_ROOTS" value="true" />
  <option name="SCRIPT_NAME" value="$PROJECT_DIR$/main.py" />
</configuration>
```

---

## 🧪 **Testing Setup**

### **Testing Framework Installation**
```bash
# Install testing dependencies
pip install pytest pytest-cov pytest-mock pytest-asyncio
pip install pytest-flask pytest-xdist  # Flask and parallel testing
pip install factory-boy faker  # Test data generation
pip install responses httpx  # HTTP mocking
```

### **Test Structure Creation**
```bash
# Create test directory structure
mkdir -p tests/{unit,integration,e2e,fixtures}
mkdir -p tests/unit/{analytics,application,domain,infrastructure,presentation}
mkdir -p tests/unit/machine_learning/{models,core}

# Create test configuration files
touch tests/__init__.py
touch tests/conftest.py
touch tests/pytest.ini
```

### **Test Configuration (tests/conftest.py)**
```python
#!/usr/bin/env python3
"""
Test configuration and fixtures for AKS Cost Optimizer
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch

# Add project root to path
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture(scope="session")
def app():
    """Create application instance for testing"""
    from main import create_app
    
    # Create temporary database
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app()
    app.config.update({
        'TESTING': True,
        'DATABASE_PATH': db_path,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })
    
    yield app
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()

@pytest.fixture
def mock_azure_client():
    """Mock Azure SDK clients"""
    with patch('infrastructure.services.azure_sdk_manager.AzureSDKManager') as mock:
        mock_instance = Mock()
        mock_instance.test_connection.return_value = True
        mock_instance.get_cost_data.return_value = {
            'total_cost': 1000.0,
            'cost_breakdown': {'compute': 600.0, 'storage': 400.0}
        }
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def sample_cluster_data():
    """Sample cluster data for testing"""
    return {
        'cluster_name': 'test-cluster',
        'subscription_id': 'test-subscription-id',
        'resource_group': 'test-rg',
        'node_count': 3,
        'node_size': 'Standard_D2s_v3',
        'kubernetes_version': '1.28.0',
        'location': 'eastus'
    }

@pytest.fixture
def sample_cost_data():
    """Sample cost data for testing"""
    return {
        'monthly_cost': 1250.00,
        'cost_breakdown': {
            'compute': 800.00,
            'storage': 250.00,
            'networking': 150.00,
            'control_plane': 50.00
        },
        'utilization': {
            'cpu_utilization': 35.5,
            'memory_utilization': 42.3,
            'storage_utilization': 67.8
        }
    }
```

### **Sample Test Files**

#### **Unit Test Example (tests/unit/analytics/test_cost_collector.py)**
```python
#!/usr/bin/env python3
"""
Unit tests for Cost Collector
"""

import pytest
from unittest.mock import Mock, patch
from analytics.collectors.comprehensive_cost_collector import ComprehensiveCostCollector

class TestComprehensiveCostCollector:
    
    def setup_method(self):
        """Setup test environment"""
        self.collector = ComprehensiveCostCollector()
    
    def test_initialization(self):
        """Test collector initialization"""
        assert self.collector is not None
        assert hasattr(self.collector, 'cost_categories')
        assert 'compute' in self.collector.cost_categories
    
    @patch('analytics.collectors.comprehensive_cost_collector.azure_client')
    def test_collect_cost_data(self, mock_azure_client, sample_cost_data):
        """Test cost data collection"""
        mock_azure_client.get_cost_data.return_value = sample_cost_data
        
        result = self.collector.collect_comprehensive_cost_data(
            subscription_id='test-subscription',
            cluster_name='test-cluster'
        )
        
        assert result is not None
        assert result['monthly_cost'] == 1250.00
        assert 'cost_breakdown' in result
    
    def test_categorize_costs(self, sample_cost_data):
        """Test cost categorization"""
        categorized = self.collector._categorize_costs(sample_cost_data)
        
        assert 'compute' in categorized
        assert 'storage' in categorized
        assert categorized['compute']['amount'] == 800.00
    
    def test_calculate_savings_potential(self, sample_cost_data):
        """Test savings calculation"""
        savings = self.collector._calculate_savings_potential(sample_cost_data)
        
        assert savings['total_potential_savings'] > 0
        assert savings['confidence_score'] >= 0
        assert savings['confidence_score'] <= 1
```

#### **Integration Test Example (tests/integration/test_api_endpoints.py)**
```python
#!/usr/bin/env python3
"""
Integration tests for API endpoints
"""

import pytest
import json

class TestAPIEndpoints:
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
    
    def test_cluster_analysis_endpoint(self, client, mock_azure_client, sample_cluster_data):
        """Test cluster analysis endpoint"""
        response = client.get('/api/analyze/cluster/test-cluster')
        
        # Should return 200 or 401 (depending on auth setup)
        assert response.status_code in [200, 401]
    
    def test_cost_breakdown_endpoint(self, client, mock_azure_client):
        """Test cost breakdown endpoint"""
        response = client.get('/api/cost/breakdown/test-cluster')
        
        # Should return JSON response
        assert response.content_type == 'application/json'
```

### **Running Tests**

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test category
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run with verbose output
pytest -v

# Run in parallel
pytest -n auto

# Run specific test file
pytest tests/unit/analytics/test_cost_collector.py

# Run specific test method
pytest tests/unit/analytics/test_cost_collector.py::TestComprehensiveCostCollector::test_initialization
```

---

## 🐳 **Docker Development**

### **Development Docker Setup**

#### **Development Dockerfile (Dockerfile.dev)**
```dockerfile
# Development Dockerfile with source code mounting
FROM python:3.11-slim-bookworm

# Install development tools
RUN apt-get update && apt-get install -y \
    curl \
    git \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Install Azure CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# Create development user
RUN groupadd -g 1000 developer && \
    useradd -r -u 1000 -g developer developer

# Set up work directory
WORKDIR /app
RUN chown developer:developer /app

# Switch to development user
USER developer

# Copy requirements first (better caching)
COPY --chown=developer:developer requirements.txt requirements/
RUN pip install --user --no-cache-dir -r requirements.txt
RUN pip install --user --no-cache-dir -r requirements/dev.txt

# Environment variables for development
ENV PYTHONPATH=/app
ENV FLASK_ENV=development
ENV FLASK_DEBUG=1
ENV PATH="/home/developer/.local/bin:$PATH"

# Expose port
EXPOSE 5001

# Default command for development
CMD ["python", "main.py"]
```

#### **Docker Compose for Development**
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  aks-optimizer-dev:
    build:
      context: .
      dockerfile: Dockerfile.dev
    image: aks-optimizer:dev
    container_name: aks-optimizer-dev
    
    ports:
      - "5001:5001"
      - "5678:5678"  # Debug port
    
    volumes:
      # Mount source code for live editing
      - .:/app:cached
      # Exclude venv and cache directories
      - /app/venv
      - /app/__pycache__
      - /app/.pytest_cache
      
      # Persistent data
      - dev_data:/app/dev_data
      - dev_logs:/app/logs
      
      # Azure credentials (read-only)
      - ${HOME}/.azure:/home/developer/.azure:ro
    
    environment:
      - FLASK_ENV=development
      - FLASK_DEBUG=1
      - LOG_LEVEL=DEBUG
      - DEV_MODE=true
      - AZURE_CONFIG_DIR=/home/developer/.azure
      
    # Override command for development
    command: ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5001", "--reload"]
    
    # Health check
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    
    networks:
      - aks-dev-network

  # Development database (PostgreSQL)
  postgres-dev:
    image: postgres:15
    container_name: postgres-dev
    
    environment:
      POSTGRES_DB: aks_optimizer_dev
      POSTGRES_USER: aks_dev_user
      POSTGRES_PASSWORD: dev_password
    
    ports:
      - "5432:5432"
    
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    
    networks:
      - aks-dev-network

  # Redis for caching
  redis-dev:
    image: redis:7-alpine
    container_name: redis-dev
    
    ports:
      - "6379:6379"
    
    networks:
      - aks-dev-network

volumes:
  dev_data:
    driver: local
  dev_logs:
    driver: local
  postgres_dev_data:
    driver: local

networks:
  aks-dev-network:
    driver: bridge
```

### **Development Commands**

```bash
# Build development environment
docker-compose -f docker-compose.dev.yml build

# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f aks-optimizer-dev

# Execute commands in container
docker-compose -f docker-compose.dev.yml exec aks-optimizer-dev bash

# Run tests in container
docker-compose -f docker-compose.dev.yml exec aks-optimizer-dev pytest

# Stop development environment
docker-compose -f docker-compose.dev.yml down

# Stop and remove volumes
docker-compose -f docker-compose.dev.yml down -v
```

---

## ☁️ **Azure Integration**

### **Azure CLI Setup**

```bash
# Login to Azure
az login

# Set default subscription
az account set --subscription "your-subscription-id"

# Verify access
az account show

# Test AKS access
az aks list --output table

# Test cost management access
az costmanagement query \
  --type "ActualCost" \
  --timeframe "MonthToDate" \
  --dataset-aggregation totals='{
    "name": "PreTaxCost",
    "function": "Sum"
  }'
```

### **Service Principal for Development**

```bash
# Create development service principal
az ad sp create-for-rbac \
  --name "aks-cost-optimizer-dev" \
  --role "Cost Management Reader" \
  --scopes "/subscriptions/{subscription-id}" \
  --output json

# Add additional roles
az role assignment create \
  --assignee {service-principal-id} \
  --role "Monitoring Reader" \
  --scope "/subscriptions/{subscription-id}"

az role assignment create \
  --assignee {service-principal-id} \
  --role "Azure Kubernetes Service Cluster User Role" \
  --scope "/subscriptions/{subscription-id}"
```

### **Local Azure Authentication**

#### **Option 1: Environment Variables**
```bash
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
```

#### **Option 2: Azure CLI Authentication**
```bash
# Use Azure CLI authentication (recommended for development)
az login
# Application will automatically use CLI credentials
```

#### **Option 3: Managed Identity (for Azure VM development)**
```bash
# No additional setup needed if developing on Azure VM with managed identity
export AZURE_USE_MSI=true
```

---

## 🐛 **Debugging Guide**

### **Debug Configuration**

#### **VS Code Debug Setup**
```json
{
  "name": "Debug with Azure",
  "type": "python",
  "request": "launch",
  "program": "${workspaceFolder}/main.py",
  "console": "integratedTerminal",
  "envFile": "${workspaceFolder}/.env.development",
  "env": {
    "FLASK_DEBUG": "1",
    "LOG_LEVEL": "DEBUG",
    "AZURE_CORE_COLLECT_TELEMETRY": "false"
  },
  "args": [],
  "justMyCode": false,
  "stopOnEntry": false
}
```

#### **Remote Debugging with Docker**
```yaml
# Add to docker-compose.dev.yml
environment:
  - DEBUGPY_LISTEN=0.0.0.0:5678
  - DEBUGPY_WAIT_FOR_CLIENT=0

ports:
  - "5678:5678"  # Debug port

# In main.py (for remote debugging)
if os.environ.get('DEBUGPY_LISTEN'):
    import debugpy
    debugpy.listen(("0.0.0.0", 5678))
    if os.environ.get('DEBUGPY_WAIT_FOR_CLIENT'):
        debugpy.wait_for_client()
```

### **Debugging Commands**

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with profiling
python -m cProfile -o profile.stats main.py

# Analyze profile
python -c "
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative').print_stats(20)
"

# Debug specific module
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from analytics.collectors.comprehensive_cost_collector import ComprehensiveCostCollector
collector = ComprehensiveCostCollector()
print('Collector initialized successfully')
"
```

### **Common Debug Scenarios**

#### **Debug Azure Authentication**
```python
# Test Azure authentication
from infrastructure.services.azure_sdk_manager import AzureSDKManager

manager = AzureSDKManager()
try:
    result = manager.test_connection()
    print(f"Azure connection: {result}")
except Exception as e:
    print(f"Azure connection failed: {e}")
    import traceback
    traceback.print_exc()
```

#### **Debug Database Issues**
```python
# Test database connection
import sqlite3
from infrastructure.persistence.cluster_database import EnhancedMultiSubscriptionClusterManager

try:
    manager = EnhancedMultiSubscriptionClusterManager()
    print("Database manager initialized successfully")
    
    # Test database operations
    clusters = manager.get_all_clusters()
    print(f"Found {len(clusters)} clusters")
except Exception as e:
    print(f"Database error: {e}")
    import traceback
    traceback.print_exc()
```

#### **Debug ML Models**
```python
# Test ML model loading
from machine_learning.models.cost_anomaly_detection import CostAnomalyDetector
import pandas as pd

try:
    detector = CostAnomalyDetector()
    print("Anomaly detector initialized")
    
    # Test with sample data
    sample_data = pd.DataFrame({
        'timestamp': pd.date_range('2025-01-01', periods=100, freq='H'),
        'cost': [100 + i * 2 + (i % 10) * 5 for i in range(100)]
    })
    
    anomalies = detector.detect_anomalies(sample_data)
    print(f"Anomaly detection completed: {len(anomalies.anomalies)} anomalies found")
except Exception as e:
    print(f"ML model error: {e}")
    import traceback
    traceback.print_exc()
```

---

## 🔍 **Code Quality Tools**

### **Linting and Formatting**

#### **Pre-commit Hooks Setup**
```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict

  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ["--max-line-length=88", "--extend-ignore=E203,W503"]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
EOF

# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

#### **Code Quality Configuration**

**setup.cfg:**
```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503, E501
exclude = 
    .git,
    __pycache__,
    venv,
    .venv,
    build,
    dist

[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
ignore_missing_imports = True

[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --tb=short
    --strict-markers
    --strict-config
    --cov=.
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=80

markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    azure: marks tests that require Azure access
```

### **Quality Assurance Commands**

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .

# Type checking
mypy .

# Security audit
bandit -r . -x tests/

# Dependency check
safety check

# All quality checks
make quality  # If using Makefile
```

### **Makefile for Development**

```makefile
# Makefile
.PHONY: help install dev-install test lint format type-check security quality clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies
	pip install -r requirements.txt

dev-install:  ## Install development dependencies
	pip install -r requirements.txt -r requirements/dev.txt
	pre-commit install

test:  ## Run tests
	pytest

test-cov:  ## Run tests with coverage
	pytest --cov=. --cov-report=html

lint:  ## Lint code
	flake8 .

format:  ## Format code
	black .
	isort .

type-check:  ## Type checking
	mypy .

security:  ## Security audit
	bandit -r . -x tests/
	safety check

quality: format lint type-check security  ## Run all quality checks

clean:  ## Clean cache files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	rm -rf htmlcov/
	rm -rf .coverage

dev-start:  ## Start development server
	python dev-mode.py enable
	python main.py

docker-dev:  ## Start development with Docker
	docker-compose -f docker-compose.dev.yml up -d

docker-dev-logs:  ## View development logs
	docker-compose -f docker-compose.dev.yml logs -f

docker-dev-stop:  ## Stop development Docker
	docker-compose -f docker-compose.dev.yml down
```

---

## 🔄 **Development Workflow**

### **Git Workflow**

#### **Branch Naming Convention**
```bash
# Feature branches
feature/add-new-cost-analyzer
feature/improve-ml-models
feature/azure-integration-enhancement

# Bug fix branches
bugfix/fix-authentication-issue
bugfix/resolve-memory-leak

# Hot fix branches
hotfix/critical-security-patch

# Release branches
release/v1.2.0
```

#### **Commit Message Convention**
```bash
# Format: <type>(<scope>): <description>

# Examples:
feat(analytics): add comprehensive cost collector
fix(auth): resolve Azure authentication timeout
docs(api): update API documentation
test(ml): add unit tests for anomaly detection
refactor(database): optimize query performance
perf(cache): improve caching efficiency
style(ui): update dashboard styling
chore(deps): update dependencies
```

### **Development Process**

#### **1. Setup New Feature**
```bash
# Create feature branch
git checkout -b feature/new-feature

# Enable development mode
python dev-mode.py enable

# Create tests first (TDD approach)
touch tests/unit/test_new_feature.py
```

#### **2. Development Cycle**
```bash
# Make changes
# Run tests frequently
pytest tests/unit/test_new_feature.py

# Check code quality
make quality

# Test manually
python main.py
```

#### **3. Pre-commit Checklist**
```bash
# Run full test suite
pytest

# Check code coverage
pytest --cov=. --cov-report=term-missing

# Verify code quality
make quality

# Test in Docker
docker-compose -f docker-compose.dev.yml up --build

# Manual testing checklist:
# - Basic functionality works
# - Azure integration works  
# - No console errors
# - All features accessible
```

#### **4. Commit and Push**
```bash
# Stage changes
git add .

# Commit with conventional message
git commit -m "feat(analytics): add comprehensive cost collector"

# Push to remote
git push origin feature/new-feature

# Create pull request
gh pr create --title "Add comprehensive cost collector" --body "Implements new cost collection functionality with Azure integration"
```

---

## 🚨 **Troubleshooting**

### **Common Development Issues**

#### **1. Python Environment Issues**

**Problem:** `ModuleNotFoundError: No module named 'flask'`
```bash
# Solution: Check virtual environment
which python
pip list | grep flask

# Reinstall if needed
pip install -r requirements.txt
```

**Problem:** `Python version mismatch`
```bash
# Solution: Use correct Python version
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### **2. Azure Authentication Issues**

**Problem:** `Azure authentication failed`
```bash
# Check Azure CLI login
az account show

# Re-login if needed
az login

# Test service principal
az login --service-principal \
  --username $AZURE_CLIENT_ID \
  --password $AZURE_CLIENT_SECRET \
  --tenant $AZURE_TENANT_ID
```

**Problem:** `Insufficient permissions`
```bash
# Check current permissions
az role assignment list --assignee $AZURE_CLIENT_ID

# Add required roles
az role assignment create \
  --assignee $AZURE_CLIENT_ID \
  --role "Cost Management Reader" \
  --scope "/subscriptions/$AZURE_SUBSCRIPTION_ID"
```

#### **3. Database Issues**

**Problem:** `Database locked error`
```bash
# Solution: Check for hanging connections
ps aux | grep python
kill -9 <process_id>

# Delete lock files
rm -f infrastructure/persistence/database/*.db-wal
rm -f infrastructure/persistence/database/*.db-shm
```

**Problem:** `Database schema mismatch`
```bash
# Solution: Run database migration
python -m infrastructure.persistence.scripts.fix_database
```

#### **4. Performance Issues**

**Problem:** `Slow startup time`
```bash
# Solution: Profile startup
python -c "
import time
start = time.time()
from main import create_app
app = create_app()
print(f'Startup time: {time.time() - start:.2f}s')
"

# Check for slow imports
python -X importtime main.py 2>&1 | grep -E '.*\|.*\|'
```

**Problem:** `Memory usage too high`
```bash
# Solution: Profile memory usage
pip install memory-profiler
python -m memory_profiler main.py

# Check for memory leaks
pip install objgraph
python -c "
import objgraph
objgraph.show_most_common_types()
"
```

### **Debug Environment Variables**

```bash
# Enable detailed logging
export LOG_LEVEL=DEBUG
export AZURE_CORE_COLLECT_TELEMETRY=false
export FLASK_DEBUG=1

# Enable SQL query logging
export SQLALCHEMY_ECHO=true

# Enable performance profiling
export ENABLE_PROFILING=true

# Disable background processing for debugging
export BACKGROUND_PROCESSING_ENABLED=false

# Enable request debugging
export FLASK_DEBUG_TB_ENABLED=true
```

### **Health Check Scripts**

#### **Development Health Check**
```bash
#!/bin/bash
# dev-healthcheck.sh

echo "🔍 AKS Cost Optimizer Development Health Check"
echo "=============================================="

# Check Python version
echo "📋 Python Version:"
python --version

# Check virtual environment
echo "📋 Virtual Environment:"
echo $VIRTUAL_ENV

# Check dependencies
echo "📋 Key Dependencies:"
python -c "
try:
    import flask, azure.identity, sklearn, pandas
    print('✅ All key dependencies available')
except ImportError as e:
    print(f'❌ Missing dependency: {e}')
"

# Check Azure CLI
echo "📋 Azure CLI:"
if command -v az &> /dev/null; then
    az --version | head -1
    echo "✅ Azure CLI available"
else
    echo "❌ Azure CLI not found"
fi

# Check environment variables
echo "📋 Environment Variables:"
if [ -n "$AZURE_TENANT_ID" ]; then
    echo "✅ AZURE_TENANT_ID set"
else
    echo "⚠️ AZURE_TENANT_ID not set"
fi

# Check application startup
echo "📋 Application Startup:"
timeout 10s python -c "
from main import create_app
app = create_app()
print('✅ Application starts successfully')
" 2>/dev/null || echo "❌ Application startup failed"

echo "=============================================="
echo "🏁 Health check completed"
```

This comprehensive development setup guide provides everything needed to get started with developing the AKS Cost Optimizer, from basic setup to advanced debugging and quality assurance practices.