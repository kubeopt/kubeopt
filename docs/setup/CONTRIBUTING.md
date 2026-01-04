# Contributing to AKS Cost Optimizer

**Welcome!** We're excited that you're interested in contributing to the AKS Cost Optimizer project. This guide will help you understand our development process, coding standards, and how to submit your contributions effectively.

---

## 📋 **Table of Contents**

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Coding Standards](#coding-standards)
5. [Testing Requirements](#testing-requirements)
6. [Documentation Guidelines](#documentation-guidelines)
7. [Pull Request Process](#pull-request-process)
8. [Issue Reporting](#issue-reporting)
9. [Security Guidelines](#security-guidelines)
10. [Release Process](#release-process)

---

## 🤝 **Code of Conduct**

### **Our Commitment**

We are committed to providing a welcoming and inclusive environment for all contributors. By participating in this project, you agree to abide by our code of conduct.

### **Expected Behavior**

- **Be respectful** and considerate in all communications
- **Be collaborative** and help others learn and grow
- **Be constructive** when providing feedback
- **Be patient** with newcomers and questions
- **Focus on the code and ideas**, not personal characteristics

### **Unacceptable Behavior**

- Harassment, discrimination, or offensive comments
- Personal attacks or trolling
- Publishing private information without permission
- Any behavior that would be inappropriate in a professional setting

### **Reporting Issues**

If you encounter unacceptable behavior, please report it by emailing the project maintainers. All reports will be handled confidentially.

---

## 🚀 **Getting Started**

### **Prerequisites**

Before contributing, ensure you have:

- **Python 3.11+** installed
- **Docker** and **Docker Compose**
- **Azure CLI** configured
- **Git** version control
- Basic understanding of **Azure Kubernetes Service**
- Familiarity with **Clean Architecture** principles

### **Development Environment Setup**

1. **Fork and Clone**
```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/your-username/aks-cost-optimizer.git
cd aks-cost-optimizer

# Add upstream remote
git remote add upstream https://github.com/original-repo/aks-cost-optimizer.git
```

2. **Setup Development Environment**
```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements/dev.txt

# Install pre-commit hooks
pre-commit install

# Enable development mode
python dev-mode.py enable
```

3. **Verify Setup**
```bash
# Run tests
pytest

# Run quality checks
make quality

# Start development server
python main.py
```

### **Understanding the Codebase**

#### **Architecture Overview**
The project follows **Clean Architecture** principles with four main layers:

```
domain/          # Core business logic (entities, value objects)
application/     # Use cases and application services
infrastructure/  # External concerns (database, Azure APIs)
presentation/    # User interfaces (web, API, CLI)
```

#### **Key Directories**
- `analytics/` - Cost analysis and data collection
- `machine_learning/` - ML models and algorithms
- `infrastructure/` - Infrastructure services and integrations
- `shared/` - Common utilities and configurations
- `tests/` - Test suites (unit, integration, e2e)
- `docs/` - Documentation and guides

---

## 🔄 **Development Workflow**

### **Branch Strategy**

We use **Git Flow** with the following branch types:

#### **Branch Naming Convention**
```bash
# Feature branches
feature/add-new-cost-analyzer
feature/improve-ml-models
feature/azure-integration-enhancement

# Bug fix branches
bugfix/fix-authentication-issue
bugfix/resolve-memory-leak
bugfix/handle-api-timeout

# Hot fix branches (for urgent production fixes)
hotfix/critical-security-patch
hotfix/data-corruption-fix

# Release branches
release/v1.2.0
release/v2.0.0

# Documentation branches
docs/update-api-documentation
docs/improve-setup-guide
```

### **Contribution Workflow**

#### **1. Planning Phase**
```bash
# Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name

# Create or update issue
# Discuss approach in issue comments
```

#### **2. Development Phase**
```bash
# Enable development mode
python dev-mode.py enable

# Make your changes following coding standards
# Write tests first (TDD approach recommended)
# Run tests frequently during development

# Check your work
make quality          # Run all quality checks
pytest               # Run test suite
python main.py       # Test manually
```

#### **3. Pre-submission Phase**
```bash
# Final quality check
make quality

# Update documentation if needed
# Add entry to CHANGELOG.md if significant

# Commit your changes
git add .
git commit -m "feat(analytics): add comprehensive cost collector

- Implement new cost collection functionality
- Add support for multi-subscription analysis  
- Include unit tests and documentation
- Resolves #123"

# Push to your fork
git push origin feature/your-feature-name
```

#### **4. Submission Phase**
```bash
# Create pull request on GitHub
gh pr create --title "Add comprehensive cost collector" --body "
## Summary
This PR implements a new comprehensive cost collector that supports multi-subscription analysis.

## Changes Made
- Added ComprehensiveCostCollector class
- Implemented multi-subscription support
- Added comprehensive unit tests
- Updated API documentation

## Testing
- All existing tests pass
- Added 15 new unit tests
- Manual testing with 3 Azure subscriptions
- Performance testing shows 20% improvement

## Breaking Changes
None

## Related Issues
Resolves #123
Related to #456
"
```

---

## 📝 **Coding Standards**

### **Code Style Guidelines**

#### **Python Style (PEP 8 + Black)**
```python
# Good: Clear, descriptive names
class AzureCostCollector:
    """Collects cost data from Azure Cost Management API"""
    
    def __init__(self, subscription_id: str, credential: TokenCredential):
        self.subscription_id = subscription_id
        self.credential = credential
        self._client = self._create_client()
    
    def collect_monthly_costs(self, start_date: date, end_date: date) -> List[CostData]:
        """Collect cost data for specified date range"""
        try:
            raw_data = self._fetch_cost_data(start_date, end_date)
            return [self._transform_cost_item(item) for item in raw_data]
        except Exception as e:
            logger.error(f"Failed to collect costs: {e}")
            raise CostCollectionError(f"Unable to collect cost data: {e}")

# Bad: Unclear names and poor structure
class CC:
    def __init__(self, sid, cred):
        self.sid = sid
        self.cred = cred
        self.client = CostManagementClient(cred)
    
    def get_costs(self, start, end):
        data = self.client.query.usage(f"/subscriptions/{self.sid}", {
            "type": "ActualCost",
            "timeframe": "Custom",
            "timePeriod": {"from": start, "to": end}
        })
        return data.rows
```

#### **Type Hints (Required)**
```python
# Good: Complete type annotations
from typing import Dict, List, Optional, Union
from datetime import datetime, date

def analyze_cluster_costs(
    cluster_id: str, 
    subscription_id: str,
    date_range: Optional[tuple[date, date]] = None
) -> Dict[str, Union[float, List[str]]]:
    """Analyze costs for a specific cluster"""
    pass

# Good: Custom types for clarity
from dataclasses import dataclass
from typing import NewType

ClusterId = NewType('ClusterId', str)
SubscriptionId = NewType('SubscriptionId', str)

@dataclass
class CostAnalysisResult:
    cluster_id: ClusterId
    total_cost: float
    recommendations: List[str]
    confidence_score: float
```

#### **Error Handling Standards**
```python
# Good: Specific exceptions with context
class AKSOptimizerError(Exception):
    """Base exception for AKS Optimizer"""
    pass

class ClusterNotFoundError(AKSOptimizerError):
    """Raised when cluster cannot be found"""
    pass

class InsufficientPermissionsError(AKSOptimizerError):
    """Raised when Azure permissions are insufficient"""
    pass

def get_cluster_info(cluster_id: str) -> ClusterInfo:
    """Get cluster information with proper error handling"""
    try:
        cluster = azure_client.get_cluster(cluster_id)
        if not cluster:
            raise ClusterNotFoundError(f"Cluster '{cluster_id}' not found")
        return ClusterInfo.from_azure_cluster(cluster)
    
    except HttpResponseError as e:
        if e.status_code == 403:
            raise InsufficientPermissionsError(
                f"No permission to access cluster '{cluster_id}'"
            )
        elif e.status_code == 404:
            raise ClusterNotFoundError(f"Cluster '{cluster_id}' not found")
        else:
            raise AKSOptimizerError(f"Azure API error: {e}")
    
    except Exception as e:
        logger.error(f"Unexpected error getting cluster {cluster_id}: {e}")
        raise AKSOptimizerError(f"Failed to get cluster information: {e}")
```

#### **Documentation Standards**
```python
# Good: Comprehensive docstrings
def calculate_optimization_savings(
    current_costs: Dict[str, float],
    optimization_recommendations: List[OptimizationRecommendation],
    confidence_threshold: float = 0.8
) -> OptimizationSavingsResult:
    """Calculate potential savings from optimization recommendations.
    
    This function analyzes the current cost structure and applies optimization
    recommendations to estimate potential savings. Only recommendations with
    confidence scores above the threshold are considered.
    
    Args:
        current_costs: Dictionary mapping cost categories to amounts (USD)
        optimization_recommendations: List of optimization recommendations
        confidence_threshold: Minimum confidence score to include recommendation
    
    Returns:
        OptimizationSavingsResult containing:
            - total_potential_savings: Total estimated savings (USD)
            - savings_by_category: Breakdown by cost category
            - high_confidence_savings: Savings from high-confidence recommendations
            - implementation_complexity: Overall complexity score
    
    Raises:
        ValueError: If current_costs contains negative values
        TypeError: If recommendations list contains invalid types
    
    Example:
        >>> costs = {"compute": 1000.0, "storage": 500.0}
        >>> recommendations = [rightsizing_rec, storage_optimization_rec]
        >>> result = calculate_optimization_savings(costs, recommendations)
        >>> print(f"Potential savings: ${result.total_potential_savings:.2f}")
        Potential savings: $450.00
    """
    if any(cost < 0 for cost in current_costs.values()):
        raise ValueError("Current costs cannot contain negative values")
    
    # Implementation details...
```

### **Architecture Guidelines**

#### **Clean Architecture Adherence**
```python
# Good: Domain layer (pure business logic)
# File: domain/entities/cluster.py
class Cluster:
    """Core cluster entity - no dependencies on infrastructure"""
    
    def __init__(self, cluster_id: str, name: str, node_count: int):
        self._validate_cluster_data(cluster_id, name, node_count)
        self.cluster_id = cluster_id
        self.name = name
        self.node_count = node_count
    
    def can_be_right_sized(self) -> bool:
        """Business rule: clusters with 1 node cannot be right-sized"""
        return self.node_count > 1
    
    def calculate_minimum_nodes(self, cpu_utilization: float) -> int:
        """Business logic for minimum node calculation"""
        if cpu_utilization < 0.3:  # 30% threshold
            return max(1, int(self.node_count * 0.7))
        return self.node_count

# Good: Application layer (use cases)
# File: application/use_cases/optimize_cluster.py
class OptimizeClusterUseCase:
    """Use case for cluster optimization - coordinates domain and infrastructure"""
    
    def __init__(
        self,
        cluster_repo: ClusterRepository,  # Interface, not implementation
        cost_analyzer: CostAnalyzer,      # Domain service
        notification_service: NotificationService  # Interface
    ):
        self._cluster_repo = cluster_repo
        self._cost_analyzer = cost_analyzer
        self._notification_service = notification_service
    
    def execute(self, cluster_id: str) -> OptimizationResult:
        """Execute optimization use case"""
        cluster = self._cluster_repo.get_by_id(cluster_id)
        if not cluster:
            raise ClusterNotFoundError(f"Cluster {cluster_id} not found")
        
        if not cluster.can_be_right_sized():
            return OptimizationResult.not_applicable(cluster)
        
        analysis = self._cost_analyzer.analyze(cluster)
        
        if analysis.potential_savings > 100:  # Business rule
            self._notification_service.send_optimization_alert(cluster, analysis)
        
        return OptimizationResult.success(cluster, analysis)

# Good: Infrastructure layer (implementation details)
# File: infrastructure/persistence/sqlite_cluster_repository.py
class SQLiteClusterRepository(ClusterRepository):
    """SQLite implementation of cluster repository"""
    
    def get_by_id(self, cluster_id: str) -> Optional[Cluster]:
        """Get cluster by ID from SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT cluster_id, name, node_count FROM clusters WHERE cluster_id = ?",
                (cluster_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return Cluster(
                    cluster_id=row[0],
                    name=row[1], 
                    node_count=row[2]
                )
            return None
```

#### **Dependency Injection**
```python
# Good: Dependency injection for testability
class OptimizationService:
    def __init__(
        self,
        cluster_repo: ClusterRepository,
        cost_service: CostService,
        ml_service: MLService
    ):
        self._cluster_repo = cluster_repo
        self._cost_service = cost_service
        self._ml_service = ml_service
    
    def optimize_cluster(self, cluster_id: str) -> OptimizationResult:
        # Use injected dependencies
        cluster = self._cluster_repo.get_by_id(cluster_id)
        costs = self._cost_service.get_cluster_costs(cluster_id)
        predictions = self._ml_service.predict_optimizations(cluster, costs)
        return self._generate_optimization_plan(cluster, costs, predictions)

# Good: Factory pattern for dependency creation
class ServiceFactory:
    @staticmethod
    def create_optimization_service(config: Config) -> OptimizationService:
        """Create optimization service with proper dependencies"""
        
        # Create repositories
        cluster_repo = SQLiteClusterRepository(config.database_path)
        
        # Create services
        azure_client = AzureClientFactory.create_client(config.azure_credentials)
        cost_service = AzureCostService(azure_client)
        ml_service = MLOptimizationService(config.ml_models_path)
        
        return OptimizationService(cluster_repo, cost_service, ml_service)

# Bad: Direct dependencies (hard to test)
class OptimizationService:
    def __init__(self):
        self._cluster_repo = SQLiteClusterRepository("/path/to/db")  # Hard dependency
        self._azure_client = CostManagementClient(DefaultAzureCredential())  # Hard dependency
    
    def optimize_cluster(self, cluster_id: str):
        # Difficult to test due to hard dependencies
        pass
```

---

## 🧪 **Testing Requirements**

### **Testing Philosophy**

We follow the **Testing Pyramid** approach:
- **70% Unit Tests** - Fast, isolated, focused on business logic
- **20% Integration Tests** - Test component interactions
- **10% End-to-End Tests** - Test complete user workflows

### **Test Structure**

```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── domain/             # Domain logic tests
│   ├── application/        # Use case tests
│   ├── infrastructure/     # Infrastructure tests
│   └── presentation/       # API/UI tests
├── integration/            # Integration tests
│   ├── azure/             # Azure API integration
│   ├── database/          # Database integration
│   └── services/          # Service integration
├── e2e/                   # End-to-end tests
│   ├── api/               # API workflow tests
│   └── web/               # Web interface tests
├── fixtures/              # Test data and mocks
└── conftest.py           # Pytest configuration
```

### **Testing Standards**

#### **Unit Test Example**
```python
# tests/unit/domain/test_cluster.py
import pytest
from domain.entities.cluster import Cluster

class TestCluster:
    """Unit tests for Cluster entity"""
    
    def test_cluster_creation_with_valid_data(self):
        """Test successful cluster creation"""
        cluster = Cluster(
            cluster_id="test-cluster-123",
            name="test-cluster",
            node_count=3
        )
        
        assert cluster.cluster_id == "test-cluster-123"
        assert cluster.name == "test-cluster"
        assert cluster.node_count == 3
    
    def test_cluster_creation_with_invalid_node_count(self):
        """Test cluster creation fails with invalid node count"""
        with pytest.raises(ValueError, match="Node count must be positive"):
            Cluster(
                cluster_id="test-cluster-123",
                name="test-cluster",
                node_count=0
            )
    
    def test_can_be_right_sized_with_multiple_nodes(self):
        """Test right-sizing eligibility for multi-node cluster"""
        cluster = Cluster("test-123", "test", 3)
        assert cluster.can_be_right_sized() is True
    
    def test_cannot_be_right_sized_with_single_node(self):
        """Test right-sizing eligibility for single-node cluster"""
        cluster = Cluster("test-123", "test", 1)
        assert cluster.can_be_right_sized() is False
    
    @pytest.mark.parametrize("cpu_util,node_count,expected", [
        (0.2, 5, 3),  # Low utilization, reduce nodes
        (0.3, 5, 5),  # Threshold utilization, keep nodes
        (0.8, 5, 5),  # High utilization, keep nodes
        (0.1, 1, 1),  # Single node, minimum is 1
    ])
    def test_calculate_minimum_nodes(self, cpu_util, node_count, expected):
        """Test minimum node calculation with various utilization levels"""
        cluster = Cluster("test-123", "test", node_count)
        result = cluster.calculate_minimum_nodes(cpu_util)
        assert result == expected
```

#### **Integration Test Example**
```python
# tests/integration/test_azure_cost_service.py
import pytest
from unittest.mock import Mock, patch
from infrastructure.services.azure_cost_service import AzureCostService

class TestAzureCostServiceIntegration:
    """Integration tests for Azure Cost Service"""
    
    @pytest.fixture
    def mock_azure_client(self):
        """Mock Azure client for testing"""
        client = Mock()
        client.query.usage.return_value = Mock(
            rows=[
                {
                    'subscriptionId': 'test-sub-123',
                    'resourceGroup': 'test-rg',
                    'pretaxCost': 100.50,
                    'usageDate': '2023-09-01T00:00:00Z',
                    'meterCategory': 'Virtual Machines'
                }
            ]
        )
        return client
    
    @pytest.fixture
    def cost_service(self, mock_azure_client):
        """Cost service with mocked Azure client"""
        service = AzureCostService(subscription_id="test-sub-123")
        service._client = mock_azure_client
        return service
    
    async def test_collect_subscription_costs_success(self, cost_service, mock_azure_client):
        """Test successful cost collection"""
        from datetime import date
        
        start_date = date(2023, 9, 1)
        end_date = date(2023, 9, 30)
        
        results = await cost_service.collect_subscription_costs(
            "test-sub-123",
            start_date,
            end_date
        )
        
        assert len(results) == 1
        assert results[0].subscription_id == "test-sub-123"
        assert results[0].pretax_cost == 100.50
        
        # Verify Azure client was called correctly
        mock_azure_client.query.usage.assert_called_once()
        
    async def test_collect_subscription_costs_with_api_error(self, cost_service, mock_azure_client):
        """Test error handling for Azure API failures"""
        from azure.core.exceptions import HttpResponseError
        
        mock_azure_client.query.usage.side_effect = HttpResponseError("API Error")
        
        with pytest.raises(AzureAPIError):
            await cost_service.collect_subscription_costs(
                "test-sub-123",
                date(2023, 9, 1),
                date(2023, 9, 30)
            )
```

#### **Test Coverage Requirements**

```bash
# Minimum coverage requirements
pytest --cov=. --cov-report=html --cov-fail-under=80

# Coverage by component
Domain Layer: 95%+      # Core business logic must be well tested
Application Layer: 90%+ # Use cases and services
Infrastructure: 80%+    # External integrations
Presentation: 75%+      # APIs and interfaces
```

### **Mocking Guidelines**

```python
# Good: Mock external dependencies, not domain logic
@patch('infrastructure.services.azure_cost_service.CostManagementClient')
def test_cost_collection_with_mock(mock_client_class):
    """Test cost collection with mocked Azure client"""
    
    # Setup mock
    mock_client = Mock()
    mock_client_class.return_value = mock_client
    mock_client.query.usage.return_value = Mock(rows=[test_data])
    
    # Test with mock
    service = AzureCostService("test-subscription")
    result = service.collect_costs()
    
    # Assert behavior
    assert len(result) == 1
    mock_client.query.usage.assert_called_once()

# Good: Use fixtures for common test data
@pytest.fixture
def sample_cluster():
    """Sample cluster for testing"""
    return Cluster(
        cluster_id="test-cluster-123",
        name="test-cluster",
        node_count=3
    )

@pytest.fixture
def sample_cost_data():
    """Sample cost data for testing"""
    return [
        RawCostData(
            subscription_id="test-sub",
            resource_group="test-rg",
            pretax_cost=100.0,
            usage_date=datetime(2023, 9, 1)
        )
    ]

# Bad: Mocking domain entities or value objects
@patch('domain.entities.cluster.Cluster')  # Don't mock domain objects
def test_something(mock_cluster):
    # This makes the test less valuable
    pass
```

---

## 📚 **Documentation Guidelines**

### **Documentation Types**

#### **1. Code Documentation**
- **Docstrings** for all public classes and functions
- **Type hints** for all function parameters and returns
- **Inline comments** for complex business logic only

#### **2. API Documentation**
- **OpenAPI/Swagger** specs for REST endpoints
- **Request/response examples** for all endpoints
- **Error code documentation** with explanations

#### **3. Architecture Documentation**
- **Decision records** (ADRs) for significant architectural decisions
- **Component diagrams** for system overview
- **Sequence diagrams** for complex workflows

#### **4. User Documentation**
- **Setup guides** for different environments
- **Usage examples** with real scenarios
- **Troubleshooting guides** for common issues

### **Documentation Standards**

#### **Docstring Format (Google Style)**
```python
def analyze_cluster_performance(
    cluster_id: str,
    metrics_timeframe: timedelta,
    include_predictions: bool = False
) -> PerformanceAnalysisResult:
    """Analyze cluster performance and identify optimization opportunities.
    
    Performs comprehensive performance analysis including CPU, memory, and storage
    utilization patterns. Optionally includes ML-based performance predictions.
    
    Args:
        cluster_id: Unique identifier for the AKS cluster
        metrics_timeframe: Time range for metrics collection (e.g., timedelta(days=7))
        include_predictions: Whether to include ML-based performance predictions
    
    Returns:
        PerformanceAnalysisResult containing:
            - current_performance: Current performance metrics
            - bottlenecks: Identified performance bottlenecks
            - recommendations: Performance optimization recommendations
            - predictions: Future performance predictions (if requested)
    
    Raises:
        ClusterNotFoundError: If the specified cluster doesn't exist
        InsufficientDataError: If not enough metrics data is available
        MetricsCollectionError: If metrics collection fails
    
    Example:
        Analyze performance for the last 7 days with predictions:
        
        >>> result = analyze_cluster_performance(
        ...     cluster_id="prod-cluster-01",
        ...     metrics_timeframe=timedelta(days=7),
        ...     include_predictions=True
        ... )
        >>> print(f"CPU utilization: {result.current_performance.cpu_avg:.1f}%")
        CPU utilization: 45.2%
        
        >>> for bottleneck in result.bottlenecks:
        ...     print(f"Bottleneck: {bottleneck.component} - {bottleneck.severity}")
        Bottleneck: memory - high
        Bottleneck: storage_io - medium
    
    Note:
        This function requires 'Monitoring Reader' permissions on the Azure subscription.
        Performance predictions require at least 7 days of historical data.
    """
```

#### **README Structure**
Each significant module should have a README with:

```markdown
# Module Name

Brief description of the module's purpose and functionality.

## Overview

Detailed explanation of what this module does and how it fits into the overall system.

## Components

### ClassName1
Brief description of the class and its responsibilities.

### ClassName2
Brief description of the class and its responsibilities.

## Usage Examples

```python
# Basic usage example
from module_name import ClassName

instance = ClassName(config)
result = instance.main_method()
```

## Configuration

List of configuration options and their purposes.

## Dependencies

- External dependencies
- Internal dependencies
- Azure services used

## Testing

How to run tests for this module and any special considerations.
```

---

## 🔀 **Pull Request Process**

### **Before Submitting**

#### **Pre-submission Checklist**
- [ ] All tests pass (`pytest`)
- [ ] Code coverage meets requirements (`pytest --cov`)
- [ ] Code quality checks pass (`make quality`)
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated (for significant changes)
- [ ] No merge conflicts with main branch
- [ ] Commit messages follow conventional format

#### **Self-Review**
- [ ] Code follows project conventions
- [ ] No hardcoded secrets or credentials
- [ ] Error handling is appropriate
- [ ] Performance considerations addressed
- [ ] Security implications considered

### **Pull Request Template**

```markdown
## Summary
Brief description of what this PR does and why.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)
- [ ] Performance improvement

## Changes Made
- Detailed list of changes
- Include files modified
- Include new dependencies added

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed
- [ ] Performance testing (if applicable)

### Test Results
```bash
# Include test run output
pytest --cov=. --cov-report=term-missing
# Coverage: 85%
```

## Breaking Changes
List any breaking changes and migration steps if applicable.

## Performance Impact
Describe any performance implications (positive or negative).

## Security Considerations
Describe any security implications and how they're addressed.

## Documentation
- [ ] Code comments updated
- [ ] API documentation updated
- [ ] User documentation updated
- [ ] Architecture docs updated (if applicable)

## Related Issues
- Closes #123
- Related to #456
- Addresses #789

## Deployment Notes
Any special considerations for deployment or configuration changes.

## Screenshots/Examples
Include screenshots for UI changes or examples for new features.
```

### **Review Process**

#### **Automated Checks**
All PRs must pass:
- **CI/CD Pipeline** (tests, linting, security scans)
- **Code Quality Gates** (coverage thresholds, complexity metrics)
- **Security Scans** (dependency vulnerabilities, secret detection)

#### **Manual Review Requirements**
- **At least 1 approval** from a maintainer
- **2 approvals** for breaking changes or architectural changes
- **Security review** for changes involving authentication, authorization, or data handling

#### **Review Criteria**
Reviewers will evaluate:
- **Correctness** - Does the code work as intended?
- **Design** - Is the code well-designed and fits the architecture?
- **Functionality** - Does it meet the requirements?
- **Complexity** - Is the code unnecessarily complex?
- **Tests** - Are there appropriate automated tests?
- **Naming** - Are variables, functions, and classes well-named?
- **Comments** - Are comments clear and useful?
- **Documentation** - Is relevant documentation updated?

### **Addressing Review Feedback**

#### **Responding to Comments**
```markdown
# Good response to review feedback

**Reviewer:** "This function is quite long. Consider breaking it down."

**Response:** "Good point! I've refactored the function into three smaller functions:
- `_validate_input_data()` - handles input validation
- `_process_cost_data()` - processes the cost data
- `_generate_recommendations()` - generates optimization recommendations

The main function now just orchestrates these steps. See commits abc123f and def456g."

**Reviewer:** "Can you add error handling for the Azure API call?"

**Response:** "Added comprehensive error handling in commit ghi789h:
- Handles HttpResponseError with specific status codes
- Implements retry logic for transient failures  
- Adds logging for debugging
- Raises appropriate domain-specific exceptions"
```

#### **Making Changes**
```bash
# Make changes based on feedback
git add .
git commit -m "refactor: break down long function into smaller components

- Split analyze_cluster_costs into 3 focused functions
- Improve readability and testability
- Add error handling for Azure API calls

Addresses feedback from PR review"

# Push changes
git push origin feature/your-feature-name

# Comment on PR
echo "Thanks for the feedback! I've addressed all the comments. Please take another look."
```

---

## 🐛 **Issue Reporting**

### **Issue Types**

#### **Bug Reports**
Use this template for reporting bugs:

```markdown
## Bug Description
Clear and concise description of the bug.

## Steps to Reproduce
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Environment
- OS: [e.g., macOS 13.0, Ubuntu 20.04, Windows 11]
- Python Version: [e.g., 3.11.2]
- Docker Version: [e.g., 20.10.21]
- Azure CLI Version: [e.g., 2.50.0]
- Application Version/Commit: [e.g., v1.2.0 or commit hash]

## Azure Environment
- Subscription Type: [e.g., Pay-as-you-go, Enterprise]
- Number of Clusters: [e.g., 5]
- Cluster Sizes: [e.g., 3-50 nodes]
- Azure Regions: [e.g., East US, West Europe]

## Additional Context
- Error logs (if any)
- Screenshots (if applicable)
- Configuration files (redacted)

## Error Logs
```
[Paste error logs here, remove sensitive information]
```

## Possible Solution
If you have ideas on how to fix the issue.
```

#### **Feature Requests**
Use this template for feature requests:

```markdown
## Feature Description
Clear description of the feature you'd like to see.

## Problem/Use Case
What problem does this feature solve? What's your use case?

## Proposed Solution
Detailed description of how you think this should work.

## Alternative Solutions
Other approaches you've considered.

## Additional Context
- Screenshots/mockups
- Examples from other tools
- Related issues or discussions

## Implementation Considerations
- Performance implications
- Security considerations
- Breaking changes potential
- Dependencies required

## Priority
- [ ] Low (nice to have)
- [ ] Medium (would be helpful)
- [ ] High (blocking my work)
- [ ] Critical (essential for project success)
```

### **Issue Triage Process**

#### **Labels**
We use the following labels:

**Type:**
- `bug` - Something isn't working
- `enhancement` - New feature or improvement
- `documentation` - Documentation improvements
- `question` - Questions about usage
- `security` - Security-related issues

**Priority:**
- `priority/critical` - Critical issues requiring immediate attention
- `priority/high` - High priority issues
- `priority/medium` - Medium priority issues
- `priority/low` - Low priority issues

**Status:**
- `status/triage` - Needs triage
- `status/accepted` - Accepted for development
- `status/in-progress` - Currently being worked on
- `status/blocked` - Blocked by external factors

**Component:**
- `component/analytics` - Analytics engine
- `component/ml` - Machine learning
- `component/infrastructure` - Infrastructure layer
- `component/api` - REST API
- `component/web` - Web interface

#### **Response Times**
We aim for the following response times:

| Priority | First Response | Resolution Target |
|----------|---------------|-------------------|
| Critical | 4 hours | 24 hours |
| High | 24 hours | 1 week |
| Medium | 3 days | 2 weeks |
| Low | 1 week | 1 month |

---

## 🔒 **Security Guidelines**

### **Security-First Development**

#### **Secure Coding Practices**

1. **Input Validation**
```python
# Good: Comprehensive input validation
from shared.common.input_validation import InputValidator

def analyze_cluster(cluster_name: str) -> AnalysisResult:
    """Analyze cluster with proper input validation"""
    
    # Validate input
    validator = InputValidator()
    validation_result = validator.validate_cluster_name(cluster_name)
    
    if not validation_result.valid:
        raise ValueError(f"Invalid cluster name: {validation_result.error}")
    
    # Use sanitized input
    sanitized_name = validation_result.sanitized_input
    return perform_analysis(sanitized_name)

# Bad: No input validation
def analyze_cluster_bad(cluster_name: str) -> AnalysisResult:
    # Direct use without validation - security risk
    return perform_analysis(cluster_name)
```

2. **Secret Management**
```python
# Good: Secure secret handling
import os
from azure.keyvault.secrets import SecretClient

def get_azure_credentials() -> AzureCredentials:
    """Get Azure credentials from secure sources"""
    
    # Try environment variables first
    client_id = os.environ.get('AZURE_CLIENT_ID')
    client_secret = os.environ.get('AZURE_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        # Fall back to Key Vault
        kv_client = SecretClient(vault_url=KEY_VAULT_URL, credential=credential)
        client_id = kv_client.get_secret('azure-client-id').value
        client_secret = kv_client.get_secret('azure-client-secret').value
    
    return AzureCredentials(client_id, client_secret)

# Bad: Hardcoded secrets
def get_azure_credentials_bad():
    return AzureCredentials(
        'hardcoded-client-id',      # Never do this!
        'hardcoded-client-secret'   # Major security vulnerability!
    )
```

3. **Error Handling Security**
```python
# Good: Secure error handling
def authenticate_user(username: str, password: str) -> AuthResult:
    """Authenticate user without information disclosure"""
    try:
        user = user_repository.get_by_username(username)
        if user and user.verify_password(password):
            return AuthResult(success=True, user=user)
        else:
            # Don't reveal whether username exists
            logger.warning(f"Failed login attempt for username: {username}")
            return AuthResult(success=False, message="Invalid credentials")
    except Exception as e:
        # Log detailed error securely
        logger.error(f"Authentication system error: {e}", extra={'username': username})
        # Return generic error to user
        return AuthResult(success=False, message="Authentication failed")

# Bad: Information disclosure
def authenticate_user_bad(username: str, password: str) -> AuthResult:
    user = user_repository.get_by_username(username)
    if not user:
        return AuthResult(success=False, message="User not found")  # Reveals username validity
    
    if not user.verify_password(password):
        return AuthResult(success=False, message="Wrong password")  # Reveals password is wrong
    
    return AuthResult(success=True, user=user)
```

#### **Security Review Checklist**

Before submitting code, verify:

- [ ] **No hardcoded secrets** or credentials
- [ ] **Input validation** for all external inputs
- [ ] **Output sanitization** to prevent XSS
- [ ] **Parameterized queries** to prevent SQL injection
- [ ] **Proper error handling** without information disclosure
- [ ] **Authentication** and authorization checks
- [ ] **Secure communication** (HTTPS, encrypted connections)
- [ ] **Audit logging** for security-relevant events
- [ ] **Resource limits** to prevent DoS attacks
- [ ] **Data encryption** for sensitive information

### **Vulnerability Reporting**

#### **Security Issues**
For security vulnerabilities:

1. **Do NOT create public issues** for security vulnerabilities
2. **Email security reports** to the maintainers privately
3. **Include detailed information** about the vulnerability
4. **Wait for confirmation** before public disclosure

#### **Security Report Template**
```markdown
Subject: Security Vulnerability Report - [Brief Description]

## Vulnerability Summary
Brief description of the vulnerability.

## Vulnerability Details
- Component affected
- Vulnerability type (e.g., XSS, SQL injection, authentication bypass)
- Attack vector
- Impact assessment

## Steps to Reproduce
1. Detailed steps to reproduce
2. Include any required setup
3. Provide example payloads if applicable

## Impact Assessment
- Confidentiality impact
- Integrity impact  
- Availability impact
- Privilege escalation potential

## Proof of Concept
[Include screenshots, code snippets, or other evidence]

## Suggested Remediation
Your recommendations for fixing the vulnerability.

## Contact Information
Your preferred method of contact for follow-up.
```

---

## 🚀 **Release Process**

### **Versioning Strategy**

We follow **Semantic Versioning (SemVer)**:
- `MAJOR.MINOR.PATCH` (e.g., `1.2.3`)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

#### **Version Examples**
```bash
1.0.0   # Initial release
1.0.1   # Bug fix release
1.1.0   # New feature release
2.0.0   # Breaking changes release
```

### **Release Workflow**

#### **1. Prepare Release**
```bash
# Create release branch
git checkout main
git pull upstream main
git checkout -b release/v1.2.0

# Update version numbers
# Update CHANGELOG.md
# Update documentation
```

#### **2. Test Release**
```bash
# Run full test suite
pytest --cov=. --cov-report=html

# Run integration tests
pytest tests/integration/

# Run security scans
bandit -r .
safety check

# Build and test containers
docker build -t aks-cost-optimizer:v1.2.0 .
docker run --rm aks-cost-optimizer:v1.2.0 --version
```

#### **3. Create Release**
```bash
# Merge release branch
git checkout main
git merge release/v1.2.0

# Create and push tag
git tag -a v1.2.0 -m "Release v1.2.0: Add multi-subscription support"
git push upstream main --tags

# Create GitHub release
gh release create v1.2.0 --title "v1.2.0: Multi-Subscription Support" --notes-file RELEASE_NOTES.md
```

### **Release Notes Template**

```markdown
# Release v1.2.0: Multi-Subscription Support

## 🎉 New Features
- **Multi-subscription analysis**: Analyze costs across multiple Azure subscriptions
- **Enhanced dashboard**: New subscription selector and cross-subscription reports
- **Improved ML models**: 25% better accuracy in cost predictions

## 🐛 Bug Fixes
- Fixed authentication timeout issues with large Azure tenants
- Resolved memory leak in background processing
- Fixed incorrect cost calculations for reserved instances

## 🔧 Improvements
- **Performance**: 40% faster cost data collection
- **Security**: Enhanced input validation and audit logging
- **UI/UX**: Improved dashboard responsiveness and user experience

## 🚨 Breaking Changes
- **API**: Changed `/api/analyze` endpoint to require subscription ID parameter
- **Config**: Removed deprecated `SINGLE_SUBSCRIPTION_MODE` environment variable
- **Database**: Schema changes require migration (see upgrade guide)

## 📈 Performance
- Cost collection: 40% faster
- Memory usage: 30% reduction
- Dashboard load time: 50% improvement

## 🔒 Security
- Updated all dependencies to latest secure versions
- Enhanced input validation for all API endpoints
- Improved audit logging coverage

## 📦 Dependencies
- Updated Azure SDK to v1.13.0
- Updated Flask to v2.3.3
- Added support for Python 3.11

## 🏃 Migration Guide
See [UPGRADE.md](UPGRADE.md) for detailed migration instructions.

## 📚 Documentation
- Updated API documentation with new endpoints
- Added multi-subscription setup guide
- Improved troubleshooting section

## 🙏 Contributors
Thank you to all contributors who made this release possible:
- @contributor1 - Multi-subscription support
- @contributor2 - Performance improvements
- @contributor3 - Security enhancements

## 🔗 Full Changelog
[View full changelog](https://github.com/org/aks-cost-optimizer/compare/v1.1.0...v1.2.0)
```

---

## 🎯 **Getting Help**

### **Communication Channels**

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and discussions
- **Documentation**: Comprehensive guides and API reference
- **Code Review**: Feedback on pull requests

### **Best Practices for Getting Help**

1. **Search existing issues** before creating new ones
2. **Provide complete information** (environment, steps, error messages)
3. **Use appropriate templates** for issues and PRs
4. **Be patient and respectful** in all communications
5. **Follow up** on your issues and PRs

### **Maintainer Response Times**

- **Critical issues**: 4-24 hours
- **General issues**: 1-3 business days
- **Pull requests**: 2-5 business days
- **Feature requests**: 1-2 weeks for initial triage

---

## 🏆 **Recognition**

### **Contributor Recognition**

We recognize contributors through:
- **Contributor credits** in release notes
- **GitHub contributor graphs** and statistics
- **Special mentions** for significant contributions
- **Maintainer privileges** for consistent, high-quality contributions

### **Types of Contributions**

All contributions are valued:
- **Code contributions** (features, bug fixes, refactoring)
- **Documentation improvements** (guides, examples, API docs)
- **Testing** (test cases, bug reports, manual testing)
- **Issue triage** (reproducing bugs, categorizing issues)
- **Community support** (helping other users, answering questions)

---

**Thank you for contributing to AKS Cost Optimizer! Your efforts help make cloud cost optimization accessible to everyone.** 🚀

---

**For questions about this contributing guide, please open an issue or reach out to the maintainers.**