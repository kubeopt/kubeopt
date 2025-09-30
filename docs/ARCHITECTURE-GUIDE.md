# AKS Cost Optimizer - Architecture Guide

**Architecture Pattern:** Clean Architecture (Domain-Driven Design)  
**Design Principles:** SOLID, DRY, KISS, Separation of Concerns  
**Target Audience:** Software Architects, Senior Developers, Technical Leads  

---

## 📋 **Table of Contents**

1. [Architecture Overview](#architecture-overview)
2. [Clean Architecture Implementation](#clean-architecture-implementation)
3. [System Components](#system-components)
4. [Data Flow Architecture](#data-flow-architecture)
5. [Integration Architecture](#integration-architecture)
6. [Scalability Architecture](#scalability-architecture)
7. [Security Architecture](#security-architecture)
8. [Performance Architecture](#performance-architecture)
9. [Monitoring Architecture](#monitoring-architecture)
10. [Deployment Architecture](#deployment-architecture)

---

## 🏗️ **Architecture Overview**

### **High-Level System Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           AKS Cost Optimizer - System Architecture                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐                │
│  │   Web Client    │    │   REST API      │    │      CLI        │                │
│  │   (Browser)     │    │   (External)    │    │   (Terminal)    │                │
│  └─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘                │
│            │                      │                      │                        │
│            └──────────────────────┼──────────────────────┘                        │
│                                   │                                               │
│  ┌─────────────────────────────────┼─────────────────────────────────────────────┐ │
│  │                    Presentation Layer                                       │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │ │
│  │  │  Web Interface  │  │   API Routes    │  │  Authentication │             │ │
│  │  │  (Flask/HTML)   │  │   (REST/JSON)   │  │   (Session)     │             │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘             │ │
│  └─────────────────────────────────┼─────────────────────────────────────────────┘ │
│                                    │                                               │
│  ┌─────────────────────────────────┼─────────────────────────────────────────────┐ │
│  │                    Application Layer                                        │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │ │
│  │  │   Use Cases     │  │  Orchestrator   │  │   Generators    │             │ │
│  │  │  (Business)     │  │  (Workflow)     │  │ (Implementation)│             │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘             │ │
│  └─────────────────────────────────┼─────────────────────────────────────────────┘ │
│                                    │                                               │
│  ┌─────────────────────────────────┼─────────────────────────────────────────────┐ │
│  │                  Infrastructure Layer                                       │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │ │
│  │  │   Persistence   │  │    Services     │  │    Security     │             │ │
│  │  │   (Database)    │  │    (Azure)      │  │  (Validation)   │             │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘             │ │
│  └─────────────────────────────────┼─────────────────────────────────────────────┘ │
│                                    │                                               │
│  ┌─────────────────────────────────┼─────────────────────────────────────────────┐ │
│  │                     Domain Layer                                            │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │ │
│  │  │    Entities     │  │  Value Objects  │  │   Repositories  │             │ │
│  │  │  (Core Models)  │  │   (Immutable)   │  │  (Interfaces)   │             │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘             │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                     │
│  ┌─────────────────────────────────┬─────────────────────────────────────────────┐ │
│  │          External Systems       │            Machine Learning                 │ │
│  │  ┌─────────────────┐            │  ┌─────────────────┐                       │ │
│  │  │  Azure APIs     │            │  │   ML Models     │                       │ │
│  │  │ (Cost/Monitor)  │            │  │  (Anomaly/CPU)  │                       │ │
│  │  └─────────────────┘            │  └─────────────────┘                       │ │
│  └─────────────────────────────────┴─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### **Architecture Principles**

#### **1. Clean Architecture (Robert C. Martin)**
- **Independence of Frameworks** - Core business logic is framework-agnostic
- **Testability** - Business rules can be tested without UI, database, or external services
- **Independence of UI** - UI can change without changing business rules
- **Independence of Database** - Business rules are not bound to database specifics
- **Independence of External Services** - Business rules don't know about Azure APIs

#### **2. SOLID Principles**
- **S** - Single Responsibility: Each class has one reason to change
- **O** - Open/Closed: Open for extension, closed for modification
- **L** - Liskov Substitution: Derived classes must be substitutable for base classes
- **I** - Interface Segregation: Clients shouldn't depend on interfaces they don't use
- **D** - Dependency Inversion: Depend on abstractions, not concretions

#### **3. Domain-Driven Design (DDD)**
- **Ubiquitous Language** - Common language between developers and domain experts
- **Bounded Contexts** - Clear boundaries between different business domains
- **Aggregates** - Consistency boundaries for business rules
- **Value Objects** - Immutable objects that represent concepts

---

## 🔧 **Clean Architecture Implementation**

### **Layer Dependencies (Dependency Inversion)**

```
┌─────────────────────────────────────────────────────────┐
│  Dependency Flow (Inner → Outer)                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Domain (Core) ←─┐                                     │
│      ↑           │                                     │
│      │           │                                     │
│  Application ←───┼─── Infrastructure                   │
│      ↑           │         ↑                          │
│      │           │         │                          │
│  Presentation ───┘         │                          │
│                            │                          │
│  External Services ────────┘                          │
│  (Azure, Database)                                     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### **Layer Responsibilities**

#### **Domain Layer (Core Business Logic)**
```python
# Location: domain/
# Purpose: Core business rules and entities

# Example: domain/entities/cluster.py
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class Cluster:
    """Core cluster entity with business rules"""
    
    cluster_id: str
    name: str
    subscription_id: str
    resource_group: str
    node_count: int
    kubernetes_version: str
    
    def __post_init__(self):
        """Enforce business rules"""
        if self.node_count < 1:
            raise ValueError("Cluster must have at least 1 node")
        
        if not self.name.isalnum():
            raise ValueError("Cluster name must be alphanumeric")
    
    def can_be_optimized(self) -> bool:
        """Business rule: clusters with 1 node cannot be optimized"""
        return self.node_count > 1
    
    def calculate_minimum_nodes(self, workload_requirements: 'WorkloadRequirements') -> int:
        """Business logic for minimum node calculation"""
        # Business rules for node optimization
        pass

# Example: domain/value_objects/cost.py
@dataclass(frozen=True)
class Cost:
    """Immutable cost value object"""
    
    amount: float
    currency: str = "USD"
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Cost cannot be negative")
    
    def add(self, other: 'Cost') -> 'Cost':
        """Add two costs together"""
        if self.currency != other.currency:
            raise ValueError("Cannot add costs with different currencies")
        return Cost(self.amount + other.amount, self.currency)
```

#### **Application Layer (Use Cases & Orchestration)**
```python
# Location: application/
# Purpose: Application-specific business rules and use cases

# Example: application/use_cases/analyze_cluster_cost.py
from typing import Dict, List
from domain.entities.cluster import Cluster
from domain.repositories.cluster_repository import ClusterRepository
from domain.repositories.cost_repository import CostRepository

class AnalyzeClusterCostUseCase:
    """Use case for analyzing cluster cost"""
    
    def __init__(
        self,
        cluster_repo: ClusterRepository,
        cost_repo: CostRepository,
        cost_analyzer: 'CostAnalyzer'
    ):
        self._cluster_repo = cluster_repo
        self._cost_repo = cost_repo
        self._cost_analyzer = cost_analyzer
    
    def execute(self, cluster_id: str) -> 'CostAnalysisResult':
        """Execute cost analysis use case"""
        
        # 1. Get cluster (domain entity)
        cluster = self._cluster_repo.get_by_id(cluster_id)
        if not cluster:
            raise ClusterNotFoundError(f"Cluster {cluster_id} not found")
        
        # 2. Business rule: check if cluster can be analyzed
        if not cluster.can_be_optimized():
            return CostAnalysisResult.not_optimizable(cluster)
        
        # 3. Get cost data
        cost_data = self._cost_repo.get_cluster_costs(cluster_id)
        
        # 4. Perform analysis (domain service)
        analysis = self._cost_analyzer.analyze(cluster, cost_data)
        
        # 5. Return result
        return CostAnalysisResult.success(cluster, analysis)

# Example: application/use_cases/orchestrator.py
class AKSOptimizationOrchestrator:
    """Main orchestrator coordinating multiple use cases"""
    
    def __init__(self, config: OptimizationConfig):
        self.config = config
        self._initialize_generators()
    
    def generate_comprehensive_optimization_plan(
        self, 
        cluster: Cluster, 
        analysis_results: Dict
    ) -> ComprehensiveExecutionPlan:
        """Orchestrate multiple optimization generators"""
        
        # Coordinate multiple use cases
        cost_commands = self.cost_generator.generate_commands(cluster, analysis_results)
        security_commands = self.security_generator.generate_commands(cluster, analysis_results)
        performance_commands = self.performance_generator.generate_commands(cluster, analysis_results)
        
        # Apply business rules for prioritization
        prioritized_commands = self._prioritize_commands(
            cost_commands + security_commands + performance_commands
        )
        
        return ComprehensiveExecutionPlan(
            cluster=cluster,
            commands=prioritized_commands,
            estimated_savings=self._calculate_total_savings(prioritized_commands)
        )
```

#### **Infrastructure Layer (External Concerns)**
```python
# Location: infrastructure/
# Purpose: Implementation details for external systems

# Example: infrastructure/persistence/cluster_repository_impl.py
from domain.repositories.cluster_repository import ClusterRepository
from domain.entities.cluster import Cluster
import sqlite3

class SQLiteClusterRepository(ClusterRepository):
    """SQLite implementation of cluster repository"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def get_by_id(self, cluster_id: str) -> Optional[Cluster]:
        """Get cluster by ID - infrastructure implementation"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM clusters WHERE cluster_id = ?",
                (cluster_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return Cluster(
                    cluster_id=row[0],
                    name=row[1],
                    subscription_id=row[2],
                    resource_group=row[3],
                    node_count=row[4],
                    kubernetes_version=row[5]
                )
            return None
    
    def save(self, cluster: Cluster) -> None:
        """Save cluster - infrastructure implementation"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO clusters 
                (cluster_id, name, subscription_id, resource_group, node_count, kubernetes_version)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    cluster.cluster_id,
                    cluster.name,
                    cluster.subscription_id,
                    cluster.resource_group,
                    cluster.node_count,
                    cluster.kubernetes_version
                )
            )

# Example: infrastructure/services/azure_cost_service.py
from domain.repositories.cost_repository import CostRepository
from azure.mgmt.costmanagement import CostManagementClient

class AzureCostService(CostRepository):
    """Azure implementation of cost repository"""
    
    def __init__(self, credential, subscription_id: str):
        self.client = CostManagementClient(credential)
        self.subscription_id = subscription_id
    
    def get_cluster_costs(self, cluster_id: str) -> CostData:
        """Get cluster costs from Azure Cost Management API"""
        
        # Azure-specific implementation
        scope = f"/subscriptions/{self.subscription_id}"
        
        query_definition = {
            "type": "ActualCost",
            "timeframe": "MonthToDate",
            "dataset": {
                "granularity": "Daily",
                "aggregation": {
                    "totalCost": {
                        "name": "PreTaxCost",
                        "function": "Sum"
                    }
                },
                "filter": {
                    "and": [
                        {
                            "dimension": {
                                "name": "ResourceGroup",
                                "operator": "In",
                                "values": [cluster_id]
                            }
                        }
                    ]
                }
            }
        }
        
        result = self.client.query.usage(scope, query_definition)
        return self._transform_azure_response(result)
```

#### **Presentation Layer (External Interfaces)**
```python
# Location: presentation/
# Purpose: External interfaces (web, API, CLI)

# Example: presentation/api/routes.py
from flask import Flask, request, jsonify
from application.use_cases.analyze_cluster_cost import AnalyzeClusterCostUseCase

class ClusterAnalysisController:
    """REST API controller for cluster analysis"""
    
    def __init__(self, analyze_use_case: AnalyzeClusterCostUseCase):
        self.analyze_use_case = analyze_use_case
    
    def analyze_cluster(self, cluster_id: str):
        """API endpoint for cluster analysis"""
        try:
            # Input validation (presentation concern)
            if not cluster_id or len(cluster_id) < 3:
                return jsonify({"error": "Invalid cluster ID"}), 400
            
            # Execute use case (application layer)
            result = self.analyze_use_case.execute(cluster_id)
            
            # Transform to API response (presentation concern)
            return jsonify({
                "cluster_id": result.cluster.cluster_id,
                "cluster_name": result.cluster.name,
                "analysis": {
                    "total_cost": result.analysis.total_cost.amount,
                    "potential_savings": result.analysis.potential_savings.amount,
                    "recommendations": [
                        self._transform_recommendation(rec) 
                        for rec in result.analysis.recommendations
                    ]
                }
            })
            
        except ClusterNotFoundError as e:
            return jsonify({"error": str(e)}), 404
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return jsonify({"error": "Internal server error"}), 500

# Example: presentation/web/main.py
@app.route('/dashboard')
def dashboard():
    """Web interface for dashboard"""
    
    # Get data through use cases (not directly from infrastructure)
    clusters = get_all_clusters_use_case.execute()
    cost_summary = get_cost_summary_use_case.execute()
    
    # Render template (presentation concern)
    return render_template(
        'dashboard.html',
        clusters=clusters,
        cost_summary=cost_summary
    )
```

---

## 🔄 **System Components**

### **Core Components Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                               Component Architecture                                │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                        Analytics Engine                                     │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐           │   │
│  │  │   Collectors    │  │   Aggregators   │  │   Processors    │           │   │
│  │  │ (Data Sources)  │  │  (Analysis)     │  │  (Algorithms)   │           │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘           │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                     Machine Learning Engine                                │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐           │   │
│  │  │     Models      │  │      Core       │  │   Training      │           │   │
│  │  │  (Anomaly/CPU)  │  │ (Integration)   │  │  (Learning)     │           │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘           │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                    Security Engine                                         │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐           │   │
│  │  │   Validation    │  │   Compliance    │  │ Vulnerability   │           │   │
│  │  │  (Input/Auth)   │  │   (Framework)   │  │   (Scanner)     │           │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘           │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                  Infrastructure Services                                   │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐           │   │
│  │  │     Azure       │  │   Database      │  │     Cache       │           │   │
│  │  │ (SDK Manager)   │  │  (Persistence)  │  │   (Manager)     │           │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘           │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### **Component Interaction Patterns**

#### **1. Observer Pattern (Event-Driven)**
```python
# Event-driven communication between components

from abc import ABC, abstractmethod
from typing import List

class AnalysisEventListener(ABC):
    @abstractmethod
    def on_analysis_completed(self, event: 'AnalysisCompletedEvent'):
        pass

class AnalysisCompletedEvent:
    def __init__(self, cluster_id: str, analysis_result: 'AnalysisResult'):
        self.cluster_id = cluster_id
        self.analysis_result = analysis_result
        self.timestamp = datetime.now()

class AnalysisOrchestrator:
    def __init__(self):
        self._listeners: List[AnalysisEventListener] = []
    
    def add_listener(self, listener: AnalysisEventListener):
        self._listeners.append(listener)
    
    def complete_analysis(self, cluster_id: str, result: 'AnalysisResult'):
        event = AnalysisCompletedEvent(cluster_id, result)
        
        # Notify all listeners
        for listener in self._listeners:
            try:
                listener.on_analysis_completed(event)
            except Exception as e:
                logger.error(f"Error notifying listener: {e}")

# Example listeners
class CacheUpdateListener(AnalysisEventListener):
    def on_analysis_completed(self, event: AnalysisCompletedEvent):
        cache_manager.update_analysis_cache(event.cluster_id, event.analysis_result)

class NotificationListener(AnalysisEventListener):
    def on_analysis_completed(self, event: AnalysisCompletedEvent):
        if event.analysis_result.has_critical_findings():
            notification_service.send_alert(event.cluster_id, event.analysis_result)
```

#### **2. Factory Pattern (Component Creation)**
```python
# Factory pattern for creating components based on configuration

from abc import ABC, abstractmethod
from typing import Dict, Type

class CostCollectorFactory:
    """Factory for creating appropriate cost collectors"""
    
    _collectors: Dict[str, Type['CostCollector']] = {}
    
    @classmethod
    def register_collector(cls, name: str, collector_class: Type['CostCollector']):
        cls._collectors[name] = collector_class
    
    @classmethod
    def create_collector(cls, collector_type: str, config: dict) -> 'CostCollector':
        if collector_type not in cls._collectors:
            raise ValueError(f"Unknown collector type: {collector_type}")
        
        collector_class = cls._collectors[collector_type]
        return collector_class(config)

# Register collectors
CostCollectorFactory.register_collector('azure', AzureCostCollector)
CostCollectorFactory.register_collector('mock', MockCostCollector)

# Usage
config = {'subscription_id': 'abc-123', 'credentials': azure_credentials}
collector = CostCollectorFactory.create_collector('azure', config)
```

#### **3. Strategy Pattern (Algorithm Selection)**
```python
# Strategy pattern for different optimization algorithms

class OptimizationStrategy(ABC):
    @abstractmethod
    def optimize(self, cluster: Cluster, metrics: ClusterMetrics) -> OptimizationResult:
        pass

class AggressiveOptimizationStrategy(OptimizationStrategy):
    def optimize(self, cluster: Cluster, metrics: ClusterMetrics) -> OptimizationResult:
        # Aggressive optimization logic
        recommendations = []
        
        # CPU optimization
        if metrics.cpu_utilization < 30:
            recommendations.append(DownsizeNodesRecommendation(target_reduction=0.5))
        
        # Memory optimization
        if metrics.memory_utilization < 40:
            recommendations.append(ReduceReplicasRecommendation(target_reduction=0.3))
        
        return OptimizationResult(recommendations, risk_level='high')

class ConservativeOptimizationStrategy(OptimizationStrategy):
    def optimize(self, cluster: Cluster, metrics: ClusterMetrics) -> OptimizationResult:
        # Conservative optimization logic
        recommendations = []
        
        # Only recommend changes with low risk
        if metrics.cpu_utilization < 20:  # Higher threshold
            recommendations.append(DownsizeNodesRecommendation(target_reduction=0.2))
        
        return OptimizationResult(recommendations, risk_level='low')

class OptimizationContext:
    def __init__(self, strategy: OptimizationStrategy):
        self._strategy = strategy
    
    def set_strategy(self, strategy: OptimizationStrategy):
        self._strategy = strategy
    
    def execute_optimization(self, cluster: Cluster, metrics: ClusterMetrics) -> OptimizationResult:
        return self._strategy.optimize(cluster, metrics)
```

---

## 📊 **Data Flow Architecture**

### **Data Processing Pipeline**

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              Data Flow Architecture                                 │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Azure     │    │    Data     │    │    Data     │    │    Data     │         │
│  │  Sources    │───▶│ Collection  │───▶│ Processing  │───▶│  Storage    │         │
│  │             │    │             │    │             │    │             │         │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘         │
│        │                   │                   │                   │             │
│        │                   │                   │                   │             │
│        ▼                   ▼                   ▼                   ▼             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   - Cost    │    │ - Validate  │    │ - Transform │    │ - SQLite    │         │
│  │   - Monitor │    │ - Sanitize  │    │ - Aggregate │    │ - Cache     │         │
│  │   - AKS     │    │ - Normalize │    │ - Enrich    │    │ - Index     │         │
│  │   - Metrics │    │ - Filter    │    │ - Calculate │    │ - Backup    │         │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘         │
│                                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │    ML       │    │  Analysis   │    │    API      │    │     UI      │         │
│  │ Processing  │◀───│ Execution   │◀───│ Requests    │◀───│ Interaction │         │
│  │             │    │             │    │             │    │             │         │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘         │
│        │                   │                   │                   │             │
│        ▼                   ▼                   ▼                   ▼             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │ - Anomaly   │    │ - Cost      │    │ - REST      │    │ - Dashboard │         │
│  │ - Predict   │    │ - Security  │    │ - GraphQL   │    │ - Reports   │         │
│  │ - Optimize  │    │ - Performance│   │ - WebSocket │    │ - Charts    │         │
│  │ - Learn     │    │ - Generate  │    │ - Webhooks  │    │ - Export    │         │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘         │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### **Data Models & Transformations**

#### **1. Raw Data Collection**
```python
# Raw data structures from Azure APIs

@dataclass
class RawCostData:
    """Raw cost data from Azure Cost Management API"""
    
    subscription_id: str
    resource_group: str
    resource_name: str
    meter_category: str
    meter_subcategory: str
    meter_name: str
    usage_quantity: float
    pretax_cost: float
    currency: str
    billing_period: str
    usage_date: datetime
    
    @classmethod
    def from_azure_response(cls, azure_row: dict) -> 'RawCostData':
        """Transform Azure API response to internal format"""
        return cls(
            subscription_id=azure_row['subscriptionId'],
            resource_group=azure_row['resourceGroup'],
            resource_name=azure_row['resourceName'],
            meter_category=azure_row['meterCategory'],
            meter_subcategory=azure_row['meterSubcategory'],
            meter_name=azure_row['meterName'],
            usage_quantity=float(azure_row['usageQuantity']),
            pretax_cost=float(azure_row['pretaxCost']),
            currency=azure_row['currency'],
            billing_period=azure_row['billingPeriod'],
            usage_date=datetime.fromisoformat(azure_row['usageDate'])
        )

@dataclass
class RawMetricsData:
    """Raw metrics data from Azure Monitor"""
    
    resource_id: str
    metric_name: str
    timestamp: datetime
    value: float
    unit: str
    aggregation_type: str
    
    @classmethod
    def from_azure_metrics(cls, metrics_response: dict) -> List['RawMetricsData']:
        """Transform Azure Monitor response to internal format"""
        results = []
        
        for timeseries in metrics_response['value']:
            for data_point in timeseries['data']:
                if 'average' in data_point:
                    results.append(cls(
                        resource_id=metrics_response['resourceregion'],
                        metric_name=metrics_response['name']['value'],
                        timestamp=datetime.fromisoformat(data_point['timeStamp']),
                        value=float(data_point['average']),
                        unit=metrics_response['unit'],
                        aggregation_type='average'
                    ))
        
        return results
```

#### **2. Data Processing & Transformation**
```python
# Data transformation pipeline

class DataTransformationPipeline:
    """Pipeline for transforming raw data to analysis-ready format"""
    
    def __init__(self):
        self.validators = [
            DataQualityValidator(),
            BusinessRuleValidator(),
            SecurityValidator()
        ]
        
        self.transformers = [
            DataNormalizer(),
            DataEnricher(),
            DataAggregator()
        ]
    
    def process(self, raw_data: List[RawCostData]) -> ProcessedCostData:
        """Process raw data through transformation pipeline"""
        
        # Step 1: Validation
        validated_data = raw_data
        for validator in self.validators:
            validated_data = validator.validate(validated_data)
        
        # Step 2: Transformation
        processed_data = validated_data
        for transformer in self.transformers:
            processed_data = transformer.transform(processed_data)
        
        return processed_data

class DataNormalizer:
    """Normalize data to standard formats"""
    
    def transform(self, data: List[RawCostData]) -> List[NormalizedCostData]:
        """Normalize cost data"""
        normalized = []
        
        for item in data:
            normalized.append(NormalizedCostData(
                cluster_id=self._extract_cluster_id(item.resource_name),
                cost_category=self._categorize_cost(item.meter_category),
                normalized_cost=self._normalize_currency(item.pretax_cost, item.currency),
                date=item.usage_date.date(),
                resource_type=self._classify_resource_type(item.meter_subcategory)
            ))
        
        return normalized

class DataAggregator:
    """Aggregate data for analysis"""
    
    def transform(self, data: List[NormalizedCostData]) -> AggregatedCostData:
        """Aggregate cost data by cluster and category"""
        
        aggregations = defaultdict(lambda: defaultdict(float))
        
        for item in data:
            aggregations[item.cluster_id][item.cost_category] += item.normalized_cost
        
        return AggregatedCostData(
            aggregations=dict(aggregations),
            total_cost=sum(sum(cats.values()) for cats in aggregations.values()),
            aggregation_date=datetime.now()
        )
```

#### **3. Processed Data Models**
```python
# Analysis-ready data models

@dataclass
class ClusterCostAnalysis:
    """Complete cost analysis for a cluster"""
    
    cluster_id: str
    cluster_name: str
    subscription_id: str
    analysis_date: datetime
    
    # Cost breakdown
    total_monthly_cost: float
    cost_by_category: Dict[str, float]  # compute, storage, networking, etc.
    cost_trend: List[Tuple[date, float]]  # historical cost trend
    
    # Utilization metrics
    cpu_utilization: float
    memory_utilization: float
    storage_utilization: float
    
    # Optimization opportunities
    potential_savings: float
    savings_confidence: float
    optimization_recommendations: List['OptimizationRecommendation']
    
    # ML insights
    anomalies: List['CostAnomaly']
    predictions: 'CostPrediction'
    
    def calculate_savings_percentage(self) -> float:
        """Calculate potential savings as percentage"""
        if self.total_monthly_cost == 0:
            return 0.0
        return (self.potential_savings / self.total_monthly_cost) * 100

@dataclass
class OptimizationRecommendation:
    """Individual optimization recommendation"""
    
    id: str
    category: str  # cost, performance, security
    priority: str  # high, medium, low
    title: str
    description: str
    
    # Impact estimation
    potential_savings: float
    implementation_effort: str  # low, medium, high
    risk_level: str  # low, medium, high
    
    # Implementation details
    implementation_steps: List[str]
    rollback_procedure: str
    monitoring_requirements: List[str]
    
    # Confidence and validation
    confidence_score: float  # 0.0 to 1.0
    validation_criteria: List[str]
```

---

## 🔗 **Integration Architecture**

### **External System Integration**

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           Integration Architecture                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                        Azure Cloud Services                                │   │
│  │                                                                             │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │   │
│  │  │    Cost     │  │   Monitor   │  │   AKS/K8s   │  │   Key Vault │       │   │
│  │  │ Management  │  │   Service   │  │   Service   │  │   Service   │       │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │   │
│  │         │                 │                 │                 │           │   │
│  └─────────┼─────────────────┼─────────────────┼─────────────────┼───────────┘   │
│            │                 │                 │                 │               │
│            ▼                 ▼                 ▼                 ▼               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                     Azure SDK Manager                                      │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │   │
│  │  │   Client    │  │   Client    │  │   Client    │  │   Client    │       │   │
│  │  │   Factory   │  │    Pool     │  │    Auth     │  │   Retry     │       │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                    Application Services                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │   │
│  │  │    Cost     │  │  Analytics  │  │ Security    │  │    ML       │       │   │
│  │  │  Service    │  │   Service   │  │  Service    │  │  Service    │       │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### **Azure SDK Integration Pattern**

#### **1. Centralized SDK Manager**
```python
# Location: infrastructure/services/azure_sdk_manager.py

class AzureSDKManager:
    """Centralized Azure SDK management with connection pooling and retry logic"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern for global SDK manager"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialize_clients()
            self._initialized = True
    
    def _initialize_clients(self):
        """Initialize Azure clients with proper authentication and configuration"""
        
        # Authentication chain
        self.credential = ChainedTokenCredential(
            ManagedIdentityCredential(),  # Try managed identity first
            AzureCliCredential(),         # Fall back to CLI
            EnvironmentCredential()       # Fall back to environment variables
        )
        
        # Client cache
        self._clients = {}
        self._client_lock = threading.Lock()
        
        # Connection pool settings
        self._session = requests.Session()
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=Retry(
                total=3,
                backoff_factor=0.3,
                status_forcelist=[500, 502, 503, 504]
            )
        )
        self._session.mount('https://', adapter)
    
    def get_cost_management_client(self) -> CostManagementClient:
        """Get cost management client with caching"""
        return self._get_cached_client('cost_management', CostManagementClient)
    
    def get_monitor_client(self) -> MonitorManagementClient:
        """Get monitor client with caching"""
        return self._get_cached_client('monitor', MonitorManagementClient)
    
    def get_container_service_client(self, subscription_id: str) -> ContainerServiceClient:
        """Get container service client with caching"""
        key = f'container_service_{subscription_id}'
        return self._get_cached_client(key, ContainerServiceClient, subscription_id)
    
    def _get_cached_client(self, key: str, client_class, *args):
        """Get cached client or create new one"""
        with self._client_lock:
            if key not in self._clients:
                self._clients[key] = client_class(self.credential, *args)
            return self._clients[key]
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((HttpResponseError, RequestException))
    )
    def execute_with_retry(self, operation, *args, **kwargs):
        """Execute Azure operation with retry logic"""
        try:
            return operation(*args, **kwargs)
        except Exception as e:
            logger.error(f"Azure operation failed: {e}")
            raise
```

#### **2. Service Integration Patterns**
```python
# Service layer that uses Azure SDK Manager

class AzureCostCollectionService:
    """Service for collecting cost data from Azure"""
    
    def __init__(self):
        self.sdk_manager = AzureSDKManager()
        self.rate_limiter = RateLimiter(calls=100, period=60)  # 100 calls per minute
    
    @rate_limiter.limit
    async def collect_subscription_costs(
        self, 
        subscription_id: str, 
        start_date: date, 
        end_date: date
    ) -> List[RawCostData]:
        """Collect cost data for subscription with rate limiting"""
        
        client = self.sdk_manager.get_cost_management_client()
        scope = f"/subscriptions/{subscription_id}"
        
        query_definition = self._build_cost_query(start_date, end_date)
        
        try:
            # Execute with retry logic
            result = await self.sdk_manager.execute_with_retry(
                client.query.usage,
                scope,
                query_definition
            )
            
            return [RawCostData.from_azure_response(row) for row in result.rows]
            
        except HttpResponseError as e:
            if e.status_code == 403:
                raise InsufficientPermissionsError(f"No access to subscription {subscription_id}")
            elif e.status_code == 429:
                raise RateLimitExceededError("Azure API rate limit exceeded")
            else:
                raise AzureAPIError(f"Azure API error: {e}")
    
    def _build_cost_query(self, start_date: date, end_date: date) -> dict:
        """Build Azure Cost Management query"""
        return {
            "type": "ActualCost",
            "timeframe": "Custom",
            "timePeriod": {
                "from": start_date.isoformat(),
                "to": end_date.isoformat()
            },
            "dataset": {
                "granularity": "Daily",
                "aggregation": {
                    "totalCost": {
                        "name": "PreTaxCost",
                        "function": "Sum"
                    }
                },
                "grouping": [
                    {
                        "type": "Dimension",
                        "name": "ResourceGroup"
                    },
                    {
                        "type": "Dimension", 
                        "name": "MeterCategory"
                    }
                ]
            }
        }

# Similar pattern for other Azure services
class AzureMonitorService:
    """Service for collecting metrics from Azure Monitor"""
    
    def __init__(self):
        self.sdk_manager = AzureSDKManager()
        self.metrics_cache = TTLCache(maxsize=1000, ttl=300)  # 5-minute cache
    
    @cached(cache=metrics_cache)
    async def get_cluster_metrics(
        self, 
        resource_id: str, 
        metric_names: List[str], 
        timespan: str
    ) -> List[RawMetricsData]:
        """Get cluster metrics with caching"""
        
        monitor_client = self.sdk_manager.get_monitor_client()
        
        try:
            result = await self.sdk_manager.execute_with_retry(
                monitor_client.metrics.list,
                resource_id,
                metricnames=','.join(metric_names),
                timespan=timespan,
                interval='PT1H'  # 1-hour intervals
            )
            
            return [RawMetricsData.from_azure_metrics(metric) for metric in result.value]
            
        except Exception as e:
            logger.error(f"Failed to get metrics for {resource_id}: {e}")
            raise
```

### **Event-Driven Integration**

#### **1. Event Bus Architecture**
```python
# Event-driven communication between services

class EventBus:
    """Central event bus for decoupled communication"""
    
    def __init__(self):
        self._handlers: Dict[str, List[callable]] = defaultdict(list)
        self._event_store = EventStore()
    
    def subscribe(self, event_type: str, handler: callable):
        """Subscribe to event type"""
        self._handlers[event_type].append(handler)
    
    def publish(self, event: 'DomainEvent'):
        """Publish event to all subscribers"""
        
        # Store event for audit trail
        self._event_store.store(event)
        
        # Notify handlers
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                asyncio.create_task(handler(event))
            except Exception as e:
                logger.error(f"Event handler error: {e}")

@dataclass
class DomainEvent:
    """Base domain event"""
    
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = ""
    data: dict = field(default_factory=dict)

class ClusterAnalysisCompletedEvent(DomainEvent):
    """Event published when cluster analysis is completed"""
    
    def __init__(self, cluster_id: str, analysis_result: 'ClusterCostAnalysis'):
        super().__init__(
            event_type='cluster_analysis_completed',
            source='analytics_service',
            data={
                'cluster_id': cluster_id,
                'total_cost': analysis_result.total_monthly_cost,
                'potential_savings': analysis_result.potential_savings,
                'recommendations_count': len(analysis_result.optimization_recommendations)
            }
        )
        self.cluster_id = cluster_id
        self.analysis_result = analysis_result

# Event handlers
class CacheUpdateHandler:
    """Handler to update cache when analysis completes"""
    
    async def handle_analysis_completed(self, event: ClusterAnalysisCompletedEvent):
        cache_key = f"analysis:{event.cluster_id}"
        await cache_manager.set(cache_key, event.analysis_result, ttl=3600)

class NotificationHandler:
    """Handler to send notifications for significant findings"""
    
    async def handle_analysis_completed(self, event: ClusterAnalysisCompletedEvent):
        if event.analysis_result.potential_savings > 1000:  # $1000+ savings
            await notification_service.send_high_savings_alert(
                event.cluster_id,
                event.analysis_result.potential_savings
            )

# Setup event bus
event_bus = EventBus()
event_bus.subscribe('cluster_analysis_completed', CacheUpdateHandler().handle_analysis_completed)
event_bus.subscribe('cluster_analysis_completed', NotificationHandler().handle_analysis_completed)
```

---

This architecture guide provides a comprehensive overview of the AKS Cost Optimizer's design patterns, component interactions, and integration strategies. The Clean Architecture implementation ensures maintainability, testability, and scalability while following enterprise-grade software engineering practices.