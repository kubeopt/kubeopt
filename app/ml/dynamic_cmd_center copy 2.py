import asyncio
import logging
import json
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import openai
from azure.identity import DefaultAzureCredential
from azure.monitor.query import MetricsQueryClient, LogsQueryClient
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest
from kubernetes import client, config
from prometheus_api_client import PrometheusConnect
import mlflow
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
import hashlib
import base64

logger = logging.getLogger(__name__)

class OptimizationCategory(Enum):
    COST_REDUCTION = "cost_reduction"
    PERFORMANCE_IMPROVEMENT = "performance_improvement"
    SECURITY_ENHANCEMENT = "security_enhancement"
    COMPLIANCE_ALIGNMENT = "compliance_alignment"
    RELIABILITY_BOOST = "reliability_boost"
    OPERATIONS_EFFICIENCY = "operations_efficiency"
    SUSTAINABILITY = "sustainability"

class UrgencyLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ImplementationComplexity(Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"

@dataclass
class ActionableCommand:
    command_id: str
    title: str
    description: str
    category: OptimizationCategory
    urgency: UrgencyLevel
    complexity: ImplementationComplexity
    estimated_savings_monthly: float
    implementation_hours: float
    success_probability: float
    commands: Dict[str, List[str]]  # kubectl, az cli, terraform, etc.
    manifests: Dict[str, str]  # YAML files
    validation_steps: List[str]
    rollback_commands: List[str]
    prerequisites: List[str]
    expected_impact: str
    risk_assessment: str
    monitoring_setup: Optional[str] = None

@dataclass
class ExecutionPlan:
    plan_id: str
    generated_at: datetime
    cluster_info: Dict[str, Any]
    total_potential_savings: float
    total_implementation_hours: float
    overall_risk_score: float
    actionable_commands: List[ActionableCommand]
    execution_sequence: List[str]  # Ordered command IDs
    summary: Dict[str, Any]
    ai_insights: str

class RealTimeDataCollector:
    """Collects real-time data from various Azure and Kubernetes APIs"""
    
    def __init__(self):
        self.credential = DefaultAzureCredential()
        self.metrics_client = MetricsQueryClient(self.credential)
        self.logs_client = LogsQueryClient(self.credential)
        self.resource_graph_client = ResourceGraphClient(self.credential)
        self.prometheus_client = None
        self.k8s_client = None
        self._initialize_k8s_client()
    
    def _initialize_k8s_client(self):
        """Initialize Kubernetes client"""
        try:
            config.load_incluster_config()
            self.k8s_client = client.ApiClient()
            logger.info("Kubernetes client initialized (in-cluster)")
        except:
            try:
                config.load_kube_config()
                self.k8s_client = client.ApiClient()
                logger.info("Kubernetes client initialized (local config)")
            except Exception as e:
                logger.warning(f"Could not initialize Kubernetes client: {e}")
    
    def _initialize_prometheus(self, prometheus_url: str):
        """Initialize Prometheus client"""
        try:
            self.prometheus_client = PrometheusConnect(url=prometheus_url)
            logger.info(f"Prometheus client initialized: {prometheus_url}")
        except Exception as e:
            logger.warning(f"Could not initialize Prometheus client: {e}")
    
    async def get_real_time_cluster_metrics(self, cluster_resource_id: str) -> Dict[str, Any]:
        """Get real-time cluster metrics from Azure Monitor"""
        try:
            # Get cluster metrics for the last 24 hours
            timespan = timedelta(hours=24)
            
            # CPU and memory metrics
            cpu_metrics = await self.metrics_client.query_resource(
                resource_uri=cluster_resource_id,
                metric_names=["node_cpu_usage_percentage"],
                timespan=timespan,
                aggregations=["Average", "Maximum"]
            )
            
            memory_metrics = await self.metrics_client.query_resource(
                resource_uri=cluster_resource_id,
                metric_names=["node_memory_usage_percentage"],
                timespan=timespan,
                aggregations=["Average", "Maximum"]
            )
            
            # Pod and node counts
            node_metrics = await self.metrics_client.query_resource(
                resource_uri=cluster_resource_id,
                metric_names=["kube_node_status_ready", "kube_pod_status_ready"],
                timespan=timespan,
                aggregations=["Average"]
            )
            
            return {
                'cpu_utilization': self._process_metrics(cpu_metrics),
                'memory_utilization': self._process_metrics(memory_metrics),
                'node_status': self._process_metrics(node_metrics),
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error fetching real-time metrics: {e}")
            return {}
    
    async def get_cluster_resource_inventory(self, subscription_id: str, cluster_name: str) -> Dict[str, Any]:
        """Get comprehensive cluster resource inventory using Azure Resource Graph"""
        try:
            # Query for AKS cluster resources
            query = f"""
            Resources
            | where type == "Microsoft.ContainerService/managedClusters"
            | where name == "{cluster_name}"
            | extend nodePoolCount = array_length(properties.agentPoolProfiles)
            | extend totalNodes = toint(properties.agentPoolProfiles[0].count)
            | extend vmSize = tostring(properties.agentPoolProfiles[0].vmSize)
            | extend osDiskSize = toint(properties.agentPoolProfiles[0].osDiskSizeGB)
            | extend kubernetesVersion = tostring(properties.kubernetesVersion)
            | project id, name, location, resourceGroup, nodePoolCount, totalNodes, vmSize, osDiskSize, kubernetesVersion, properties
            """
            
            request = QueryRequest(query=query, subscriptions=[subscription_id])
            response = self.resource_graph_client.resources(request)
            
            if response.data:
                cluster_data = response.data[0]
                
                # Get associated resources (storage, networking, etc.)
                associated_resources_query = f"""
                Resources
                | where resourceGroup == "{cluster_data['resourceGroup']}"
                | where type in ("Microsoft.Storage/storageAccounts", 
                                "Microsoft.Network/virtualNetworks",
                                "Microsoft.Network/loadBalancers",
                                "Microsoft.Network/publicIPAddresses")
                | project type, name, sku, properties
                """
                
                assoc_request = QueryRequest(query=associated_resources_query, subscriptions=[subscription_id])
                assoc_response = self.resource_graph_client.resources(assoc_request)
                
                return {
                    'cluster_info': cluster_data,
                    'associated_resources': assoc_response.data,
                    'query_timestamp': datetime.now()
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error fetching cluster inventory: {e}")
            return {}
    
    async def get_live_workload_analysis(self) -> Dict[str, Any]:
        """Get live workload analysis from Kubernetes API"""
        if not self.k8s_client:
            return {}
            
        try:
            v1 = client.AppsV1Api()
            core_v1 = client.CoreV1Api()
            
            # Get all deployments
            deployments = v1.list_deployment_for_all_namespaces()
            
            # Get all pods
            pods = core_v1.list_pod_for_all_namespaces()
            
            # Get all services
            services = core_v1.list_service_for_all_namespaces()
            
            # Get all PVCs
            pvcs = core_v1.list_persistent_volume_claim_for_all_namespaces()
            
            # Analyze workload patterns
            workload_analysis = {
                'deployments': self._analyze_deployments(deployments.items),
                'pods': self._analyze_pods(pods.items),
                'services': self._analyze_services(services.items),
                'storage': self._analyze_storage(pvcs.items),
                'resource_utilization': await self._get_live_resource_utilization()
            }
            
            return workload_analysis
            
        except Exception as e:
            logger.error(f"Error in live workload analysis: {e}")
            return {}
    
    async def get_cost_allocation_data(self, workspace_id: str) -> Dict[str, Any]:
        """Get cost allocation data from Azure Monitor Logs"""
        try:
            # Query for cost allocation by namespace
            query = """
            KubePodInventory
            | where TimeGenerated > ago(24h)
            | extend Namespace = Namespace
            | summarize 
                PodCount = dcount(Name),
                AvgCpuCores = avg(PodCpuCoresRequested),
                AvgMemoryGB = avg(PodMemoryBytesRequested / 1024 / 1024 / 1024),
                TotalCpuCores = sum(PodCpuCoresRequested),
                TotalMemoryGB = sum(PodMemoryBytesRequested / 1024 / 1024 / 1024)
            by Namespace
            | order by TotalCpuCores desc
            """
            
            response = await self.logs_client.query_workspace(
                workspace_id=workspace_id,
                query=query,
                timespan=timedelta(hours=24)
            )
            
            cost_data = []
            for table in response.tables:
                for row in table.rows:
                    cost_data.append({
                        'namespace': row[0],
                        'pod_count': row[1],
                        'avg_cpu_cores': row[2],
                        'avg_memory_gb': row[3],
                        'total_cpu_cores': row[4],
                        'total_memory_gb': row[5]
                    })
            
            return {
                'namespace_costs': cost_data,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error fetching cost allocation data: {e}")
            return {}
    
    def _process_metrics(self, metrics_response) -> Dict[str, float]:
        """Process Azure Monitor metrics response"""
        if not metrics_response or not metrics_response.metrics:
            return {}
        
        processed = {}
        for metric in metrics_response.metrics:
            if metric.timeseries:
                values = []
                for ts in metric.timeseries:
                    if ts.data:
                        values.extend([point.average or point.total or point.maximum or 0 for point in ts.data])
                
                if values:
                    processed[metric.name] = {
                        'average': np.mean(values),
                        'maximum': np.max(values),
                        'minimum': np.min(values),
                        'latest': values[-1] if values else 0
                    }
        
        return processed
    
    def _analyze_deployments(self, deployments) -> Dict[str, Any]:
        """Analyze deployment configurations"""
        analysis = {
            'total_count': len(deployments),
            'without_resource_limits': 0,
            'without_resource_requests': 0,
            'without_hpa': 0,
            'high_replica_count': 0,
            'namespaces': set(),
            'resource_patterns': []
        }
        
        for deployment in deployments:
            analysis['namespaces'].add(deployment.metadata.namespace)
            
            # Check resource specifications
            containers = deployment.spec.template.spec.containers
            has_limits = all(c.resources and c.resources.limits for c in containers)
            has_requests = all(c.resources and c.resources.requests for c in containers)
            
            if not has_limits:
                analysis['without_resource_limits'] += 1
            if not has_requests:
                analysis['without_resource_requests'] += 1
            
            # Check replica count
            if deployment.spec.replicas and deployment.spec.replicas > 10:
                analysis['high_replica_count'] += 1
            
            # Collect resource patterns
            for container in containers:
                if container.resources:
                    analysis['resource_patterns'].append({
                        'deployment': deployment.metadata.name,
                        'namespace': deployment.metadata.namespace,
                        'requests': container.resources.requests,
                        'limits': container.resources.limits
                    })
        
        analysis['namespaces'] = list(analysis['namespaces'])
        return analysis
    
    def _analyze_pods(self, pods) -> Dict[str, Any]:
        """Analyze pod configurations and status"""
        analysis = {
            'total_count': len(pods),
            'running': 0,
            'pending': 0,
            'failed': 0,
            'resource_usage': {},
            'node_distribution': {}
        }
        
        for pod in pods:
            # Count by status
            phase = pod.status.phase
            if phase == 'Running':
                analysis['running'] += 1
            elif phase == 'Pending':
                analysis['pending'] += 1
            elif phase == 'Failed':
                analysis['failed'] += 1
            
            # Node distribution
            if pod.spec.node_name:
                analysis['node_distribution'][pod.spec.node_name] = \
                    analysis['node_distribution'].get(pod.spec.node_name, 0) + 1
        
        return analysis
    
    def _analyze_services(self, services) -> Dict[str, Any]:
        """Analyze service configurations"""
        analysis = {
            'total_count': len(services),
            'load_balancer': 0,
            'node_port': 0,
            'cluster_ip': 0,
            'external_services': []
        }
        
        for service in services:
            svc_type = service.spec.type
            if svc_type == 'LoadBalancer':
                analysis['load_balancer'] += 1
                analysis['external_services'].append({
                    'name': service.metadata.name,
                    'namespace': service.metadata.namespace,
                    'type': svc_type
                })
            elif svc_type == 'NodePort':
                analysis['node_port'] += 1
            else:
                analysis['cluster_ip'] += 1
        
        return analysis
    
    def _analyze_storage(self, pvcs) -> Dict[str, Any]:
        """Analyze storage configurations"""
        analysis = {
            'total_count': len(pvcs),
            'total_storage_gb': 0,
            'storage_classes': {},
            'access_modes': {},
            'unused_pvcs': []
        }
        
        for pvc in pvcs:
            # Storage size
            if pvc.spec.resources and pvc.spec.resources.requests:
                storage_size = pvc.spec.resources.requests.get('storage', '0Gi')
                size_gb = self._parse_storage_size(storage_size)
                analysis['total_storage_gb'] += size_gb
            
            # Storage class
            sc = pvc.spec.storage_class_name or 'default'
            analysis['storage_classes'][sc] = analysis['storage_classes'].get(sc, 0) + 1
            
            # Access modes
            for mode in pvc.spec.access_modes or []:
                analysis['access_modes'][mode] = analysis['access_modes'].get(mode, 0) + 1
            
            # Check if PVC is bound
            if pvc.status.phase != 'Bound':
                analysis['unused_pvcs'].append({
                    'name': pvc.metadata.name,
                    'namespace': pvc.metadata.namespace,
                    'status': pvc.status.phase
                })
        
        return analysis
    
    async def _get_live_resource_utilization(self) -> Dict[str, Any]:
        """Get live resource utilization from metrics server"""
        if not self.prometheus_client:
            return {}
        
        try:
            # CPU utilization
            cpu_query = 'avg(rate(container_cpu_usage_seconds_total[5m])) by (namespace, pod)'
            cpu_result = self.prometheus_client.get_current_metric_value(metric_name=cpu_query)
            
            # Memory utilization
            memory_query = 'avg(container_memory_usage_bytes) by (namespace, pod)'
            memory_result = self.prometheus_client.get_current_metric_value(metric_name=memory_query)
            
            return {
                'cpu_utilization': cpu_result,
                'memory_utilization': memory_result
            }
        except Exception as e:
            logger.warning(f"Could not get live resource utilization: {e}")
            return {}
    
    def _parse_storage_size(self, size_str: str) -> float:
        """Parse Kubernetes storage size string to GB"""
        if not size_str:
            return 0
        
        size_str = size_str.upper()
        multipliers = {'GI': 1, 'TI': 1024, 'MI': 1/1024, 'KI': 1/1024/1024}
        
        for suffix, multiplier in multipliers.items():
            if size_str.endswith(suffix):
                try:
                    return float(size_str[:-len(suffix)]) * multiplier
                except ValueError:
                    return 0
        
        return 0

class AIOptimizationEngine:
    """Uses AI/ML to generate intelligent optimization recommendations"""
    
    def __init__(self):
        self.openai_client = None
        self.ml_models = {}
        self._initialize_openai()
        self._load_ml_models()
    
    def _initialize_openai(self):
        """Initialize OpenAI client"""
        try:
            self.openai_client = openai.AzureOpenAI(
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_KEY"),
                api_version="2024-02-01"
            )
            logger.info("Azure OpenAI client initialized")
        except Exception as e:
            logger.warning(f"Could not initialize Azure OpenAI: {e}")
    
    def _load_ml_models(self):
        """Load pre-trained ML models"""
        try:
            # Load models from MLflow or local storage
            model_paths = {
                'cost_predictor': 'models/cost_optimization_model',
                'performance_predictor': 'models/performance_model',
                'risk_assessor': 'models/risk_assessment_model'
            }
            
            for model_name, path in model_paths.items():
                try:
                    self.ml_models[model_name] = mlflow.sklearn.load_model(path)
                    logger.info(f"Loaded ML model: {model_name}")
                except:
                    # Fallback to basic sklearn models
                    self.ml_models[model_name] = self._create_fallback_model(model_name)
                    logger.warning(f"Using fallback model for: {model_name}")
                    
        except Exception as e:
            logger.error(f"Error loading ML models: {e}")
    
    def _create_fallback_model(self, model_type: str):
        """Create fallback ML models"""
        if model_type == 'cost_predictor':
            return RandomForestRegressor(n_estimators=100, random_state=42)
        elif model_type == 'performance_predictor':
            return RandomForestRegressor(n_estimators=100, random_state=42)
        elif model_type == 'risk_assessor':
            return GradientBoostingClassifier(n_estimators=100, random_state=42)
        return None
    
    async def generate_ai_insights(self, cluster_data: Dict, analysis_results: Dict) -> str:
        """Generate AI-powered insights and recommendations"""
        if not self.openai_client:
            return self._generate_rule_based_insights(cluster_data, analysis_results)
        
        try:
            prompt = f"""
            Analyze this AKS cluster configuration and provide actionable optimization insights:
            
            Cluster Configuration:
            {json.dumps(cluster_data, indent=2, default=str)}
            
            Analysis Results:
            {json.dumps(analysis_results, indent=2, default=str)}
            
            Please provide:
            1. Top 3 cost optimization opportunities
            2. Performance improvement recommendations
            3. Security and compliance considerations
            4. Risk assessment and mitigation strategies
            5. Implementation priority ranking
            
            Focus on specific, actionable recommendations with quantifiable impact.
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")
            return self._generate_rule_based_insights(cluster_data, analysis_results)
    
    async def generate_optimized_commands(self, optimization_type: str, 
                                        context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate optimized commands using AI"""
        if not self.openai_client:
            return self._generate_template_commands(optimization_type, context)
        
        try:
            prompt = f"""
            Generate optimized Kubernetes commands for {optimization_type} based on this context:
            
            Context:
            {json.dumps(context, indent=2, default=str)}
            
            Generate:
            1. kubectl commands
            2. Azure CLI commands
            3. YAML manifests
            4. Validation steps
            5. Rollback commands
            
            Ensure all commands are production-ready and follow best practices.
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=3000
            )
            
            # Parse the AI response into structured format
            ai_content = response.choices[0].message.content
            return self._parse_ai_commands(ai_content)
            
        except Exception as e:
            logger.error(f"Error generating AI commands: {e}")
            return self._generate_template_commands(optimization_type, context)
    
    def predict_cost_savings(self, optimization_data: Dict[str, Any]) -> float:
        """Predict cost savings using ML model"""
        try:
            if 'cost_predictor' not in self.ml_models:
                return self._estimate_savings_heuristic(optimization_data)
            
            # Extract features for ML model
            features = self._extract_cost_features(optimization_data)
            
            # Make prediction
            model = self.ml_models['cost_predictor']
            if hasattr(model, 'predict'):
                savings = model.predict([features])[0]
                return max(0, savings)  # Ensure non-negative
            
            return self._estimate_savings_heuristic(optimization_data)
            
        except Exception as e:
            logger.error(f"Error predicting cost savings: {e}")
            return self._estimate_savings_heuristic(optimization_data)
    
    def assess_implementation_risk(self, command_data: Dict[str, Any]) -> float:
        """Assess implementation risk using ML model"""
        try:
            if 'risk_assessor' not in self.ml_models:
                return self._assess_risk_heuristic(command_data)
            
            # Extract features for risk assessment
            features = self._extract_risk_features(command_data)
            
            # Make prediction
            model = self.ml_models['risk_assessor']
            if hasattr(model, 'predict_proba'):
                risk_prob = model.predict_proba([features])[0][1]  # Probability of high risk
                return risk_prob
            
            return self._assess_risk_heuristic(command_data)
            
        except Exception as e:
            logger.error(f"Error assessing risk: {e}")
            return self._assess_risk_heuristic(command_data)
    
    def _generate_rule_based_insights(self, cluster_data: Dict, analysis_results: Dict) -> str:
        """Generate insights using rule-based approach"""
        insights = []
        
        # Cost optimization insights
        if analysis_results.get('total_cost', 0) > 5000:
            insights.append("🔥 HIGH COST CLUSTER: Consider implementing HPA and right-sizing resources")
        
        # Resource utilization insights
        cpu_avg = analysis_results.get('cpu_utilization', {}).get('average', 0)
        if cpu_avg < 30:
            insights.append("⚠️ LOW CPU UTILIZATION: Significant right-sizing opportunity detected")
        
        # Storage insights
        storage_gb = analysis_results.get('storage', {}).get('total_storage_gb', 0)
        if storage_gb > 1000:
            insights.append("💾 HIGH STORAGE USAGE: Review storage classes and implement lifecycle policies")
        
        return "\n".join(insights) if insights else "✅ Cluster appears well-optimized"
    
    def _generate_template_commands(self, optimization_type: str, context: Dict) -> Dict[str, Any]:
        """Generate template-based commands"""
        commands = {
            'kubectl': [],
            'azure_cli': [],
            'manifests': {},
            'validation': [],
            'rollback': []
        }
        
        if optimization_type == 'hpa_implementation':
            commands['kubectl'].extend([
                "kubectl apply -f hpa-manifest.yaml",
                "kubectl get hpa --all-namespaces"
            ])
            commands['manifests']['hpa-manifest.yaml'] = self._create_hpa_manifest(context)
            
        elif optimization_type == 'resource_rightsizing':
            commands['kubectl'].extend([
                "kubectl patch deployment {deployment} -p '{patch}'",
                "kubectl rollout status deployment/{deployment}"
            ])
        
        return commands
    
    def _parse_ai_commands(self, ai_content: str) -> Dict[str, Any]:
        """Parse AI-generated commands into structured format"""
        # This would implement parsing logic for AI-generated commands
        # For now, return a structured template
        return {
            'kubectl': [],
            'azure_cli': [],
            'manifests': {},
            'validation': [],
            'rollback': []
        }
    
    def _extract_cost_features(self, data: Dict) -> List[float]:
        """Extract features for cost prediction model"""
        return [
            data.get('node_count', 0),
            data.get('cpu_utilization', 0),
            data.get('memory_utilization', 0),
            data.get('storage_gb', 0),
            data.get('pod_count', 0)
        ]
    
    def _extract_risk_features(self, data: Dict) -> List[float]:
        """Extract features for risk assessment model"""
        return [
            len(data.get('commands', {}).get('kubectl', [])),
            1 if 'deployment' in str(data) else 0,
            1 if 'delete' in str(data).lower() else 0,
            data.get('complexity_score', 0.5)
        ]
    
    def _estimate_savings_heuristic(self, data: Dict) -> float:
        """Heuristic-based cost savings estimation"""
        base_cost = data.get('current_cost', 0)
        utilization = data.get('cpu_utilization', 50)
        
        if utilization < 30:
            return base_cost * 0.3  # 30% savings for low utilization
        elif utilization < 50:
            return base_cost * 0.15  # 15% savings for moderate utilization
        
        return base_cost * 0.05  # 5% baseline savings
    
    def _assess_risk_heuristic(self, data: Dict) -> float:
        """Heuristic-based risk assessment"""
        risk_score = 0.2  # Base risk
        
        # Increase risk for complex operations
        if any('delete' in cmd.lower() for cmd in data.get('commands', {}).get('kubectl', [])):
            risk_score += 0.3
        
        if data.get('affects_production', False):
            risk_score += 0.2
        
        return min(1.0, risk_score)
    
    def _create_hpa_manifest(self, context: Dict) -> str:
        """Create HPA manifest template"""
        deployment_name = context.get('deployment_name', 'example-deployment')
        namespace = context.get('namespace', 'default')
        
        return f"""apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {deployment_name}-hpa
  namespace: {namespace}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {deployment_name}
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
"""

class ComprehensiveAKSOptimizer:
    """Main optimization engine that analyzes data and generates actionable commands"""
    
    def __init__(self):
        self.data_collector = RealTimeDataCollector()
        self.ai_engine = AIOptimizationEngine()
        self.scenario_handlers = self._initialize_scenario_handlers()
        
        # Add these missing attributes
        self.cluster_config = {}  # Store cluster configuration
        self.logger = logging.getLogger(__name__)  # Add logger instance
    
    def _initialize_scenario_handlers(self) -> Dict[str, Any]:
        """Initialize handlers for different optimization scenarios"""
        return {
            'cost_reduction': self._handle_cost_reduction,
            'performance_optimization': self._handle_performance_optimization,
            'security_hardening': self._handle_security_hardening,
            'compliance_alignment': self._handle_compliance_alignment,
            'reliability_improvement': self._handle_reliability_improvement,
            'storage_optimization': self._handle_storage_optimization,
            'network_optimization': self._handle_network_optimization,
            'monitoring_enhancement': self._handle_monitoring_enhancement,
            'gitops_implementation': self._handle_gitops_implementation,
            'service_mesh_optimization': self._handle_service_mesh_optimization,
            'ai_ml_workload_optimization': self._handle_ai_ml_optimization,
            'disaster_recovery': self._handle_disaster_recovery,
            'sustainability_optimization': self._handle_sustainability_optimization
        }
    
    def set_cluster_config(self, cluster_config: Dict):
        """Set cluster configuration"""
        self.cluster_config = cluster_config
        self.logger.info("🛠️ Cluster config set for dynamic generator")
    
    def get_cluster_config(self) -> Dict:
        """Get current cluster configuration"""
        return self.cluster_config
    
    def update_cluster_config(self, updates: Dict):
        """Update cluster configuration with new values"""
        self.cluster_config.update(updates)
        self.logger.info(f"🔄 Updated cluster config with {len(updates)} new values")
    
    def validate_cluster_config(self) -> bool:
        """Validate that required cluster configuration is present"""
        required_fields = ['cluster_name', 'resource_group', 'subscription_id']
        
        for field in required_fields:
            if field not in self.cluster_config:
                self.logger.warning(f"⚠️ Missing required cluster config field: {field}")
                return False
        
        self.logger.info("✅ Cluster configuration validated successfully")
        return True
    
    def get_cluster_info(self) -> Dict[str, Any]:
        """Get cluster information from configuration"""
        return {
            'cluster_name': self.cluster_config.get('cluster_name', 'unknown'),
            'resource_group': self.cluster_config.get('resource_group', 'unknown'),
            'subscription_id': self.cluster_config.get('subscription_id', 'unknown'),
            'region': self.cluster_config.get('region', 'unknown'),
            'node_count': self.cluster_config.get('node_count', 0),
            'kubernetes_version': self.cluster_config.get('kubernetes_version', 'unknown')
        }
    
    async def initialize_for_cluster(self, cluster_config: Dict[str, Any]) -> bool:
        """Initialize the optimizer for a specific cluster"""
        try:
            self.set_cluster_config(cluster_config)
            
            # Initialize Prometheus if URL is provided
            prometheus_url = cluster_config.get('prometheus_url')
            if prometheus_url:
                self.data_collector._initialize_prometheus(prometheus_url)
            
            # Validate configuration
            if not self.validate_cluster_config():
                return False
            
            self.logger.info(f"🚀 Optimizer initialized for cluster: {cluster_config.get('cluster_name', 'unknown')}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize optimizer for cluster: {e}")
            return False
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """Get current optimization status"""
        return {
            'cluster_configured': bool(self.cluster_config),
            'cluster_name': self.cluster_config.get('cluster_name', 'not_set'),
            'supported_optimizations': len(self.scenario_handlers),
            'ai_engine_available': self.ai_engine.openai_client is not None,
            'data_collector_ready': self.data_collector.k8s_client is not None,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_supported_optimizations(self) -> List[str]:
        """Get list of supported optimization types"""
        return list(self.scenario_handlers.keys())
    
    async def generate_comprehensive_execution_plan(
        self,
        ml_strategy: Dict[str, Any],
        cluster_dna: Dict[str, Any], 
        analysis_results: Dict[str, Any],
        cluster_config: Dict[str, Any]
    ) -> ExecutionPlan:
        """
        Generate comprehensive execution plan with enhanced debugging
        """
        try:
            self.logger.info("🚀 Starting comprehensive execution plan generation")
            
            # Set cluster config if provided
            if cluster_config:
                self.set_cluster_config(cluster_config)
            
            # Log input validation
            self.logger.info("📋 Input Validation:")
            self.logger.info(f"   - ML Strategy: {bool(ml_strategy)} ({type(ml_strategy).__name__})")
            self.logger.info(f"   - Cluster DNA: {bool(cluster_dna)} ({type(cluster_dna).__name__})")
            self.logger.info(f"   - Analysis Results: {bool(analysis_results)} ({len(analysis_results) if isinstance(analysis_results, dict) else 'N/A'} keys)")
            self.logger.info(f"   - Cluster Config: {bool(cluster_config)} ({len(cluster_config) if isinstance(cluster_config, dict) else 'N/A'} keys)")

            
            # Step 1: Collect real-time data
            self.logger.info("📊 Phase 1: Collecting real-time data")
            real_time_data = await self._collect_comprehensive_data(self.cluster_config)
            self.logger.info(f"📊 Collected real-time data: {len(real_time_data)} data points")
            
            # Step 2: Enrich analysis results
            self.logger.info("🔍 Phase 2: Enriching analysis results")
            enriched_analysis = self._enrich_analysis_results(analysis_results, real_time_data, cluster_dna)
            self.logger.info("🔍 Analysis results enriched with real-time data")
            
            # Step 3: Identify optimization opportunities
            self.logger.info("🎯 Phase 3: Identifying optimization opportunities")
            opportunities = await self._identify_optimization_opportunities(
                enriched_analysis, ml_strategy, self.cluster_config
            )
            self.logger.info(f"🎯 Identified {len(opportunities)} optimization opportunities")
            
            if not opportunities:
                self.logger.warning("⚠️ No optimization opportunities identified, creating basic opportunities")
                opportunities = self._create_basic_opportunities(enriched_analysis)
            
            # Step 4: Generate actionable commands
            self.logger.info("⚙️ Phase 4: Generating actionable commands")
            all_commands = []
            
            for i, opportunity in enumerate(opportunities, 1):
                self.logger.info(f"⚙️ Processing opportunity {i}/{len(opportunities)}: {opportunity.get('title', 'Unknown')}")
                try:
                    commands = await self._generate_actionable_commands(
                        opportunity, enriched_analysis, self.cluster_config
                    )
                    all_commands.extend(commands)
                    self.logger.info(f"   ✅ Generated {len(commands)} commands for this opportunity")
                except Exception as e:
                    self.logger.error(f"   ❌ Error generating commands for opportunity: {e}")
                    # Create fallback command for this opportunity
                    fallback_cmd = self._create_fallback_command(opportunity, self.cluster_config)
                    all_commands.append(fallback_cmd)
            
            self.logger.info(f"⚙️ Total commands generated: {len(all_commands)}")
            
            if not all_commands:
                self.logger.error("❌ No commands generated from opportunities")
                # Create emergency fallback commands
                all_commands = self._create_emergency_commands(enriched_analysis, self.cluster_config)
                self.logger.info(f"🆘 Created {len(all_commands)} emergency fallback commands")
            
            # Step 5: Prioritize and sequence commands
            self.logger.info("📈 Phase 5: Prioritizing and sequencing commands")
            prioritized_commands = self._prioritize_commands(all_commands)
            execution_sequence = self._create_execution_sequence(prioritized_commands)
            
            # Step 6: Calculate metrics and create summary
            self.logger.info("📊 Phase 6: Calculating plan metrics")
            plan_metrics = self._calculate_plan_metrics(prioritized_commands)
            plan_summary = self._generate_plan_summary(prioritized_commands, plan_metrics)
            
            # Step 7: Generate AI insights
            self.logger.info("🤖 Phase 7: Generating AI insights")
            ai_insights = await self.ai_engine.generate_ai_insights(
                self.cluster_config, enriched_analysis
            )
            
            # Step 8: Create final execution plan
            self.logger.info("📋 Phase 8: Creating final execution plan")
            execution_plan = ExecutionPlan(
                plan_id=self._generate_plan_id(),
                generated_at=datetime.now(),
                cluster_info=self._extract_cluster_info(self.cluster_config, cluster_dna),
                total_potential_savings=plan_metrics['total_savings'],
                total_implementation_hours=plan_metrics['total_hours'],
                overall_risk_score=plan_metrics['risk_score'],
                actionable_commands=prioritized_commands,
                execution_sequence=execution_sequence,
                summary=plan_summary,
                ai_insights=ai_insights
            )
            
            self.logger.info(f"✅ Successfully generated execution plan:")
            self.logger.info(f"   📊 Commands: {len(execution_plan.actionable_commands)}")
            self.logger.info(f"   💰 Savings: ${execution_plan.total_potential_savings:,.2f}/month")
            self.logger.info(f"   ⏱️ Hours: {execution_plan.total_implementation_hours:.1f}")
            self.logger.info(f"   🎯 Risk: {execution_plan.overall_risk_score:.2f}")
            
            return execution_plan
            
        except Exception as e:
            self.logger.error(f"❌ Failed to generate comprehensive execution plan: {e}")
            import traceback
            self.logger.error(f"❌ Traceback: {traceback.format_exc()}")
            
            # Return emergency fallback plan
            return self._create_emergency_execution_plan(
                self.cluster_config or cluster_config or {}, 
                analysis_results
            )
    
    def _create_basic_opportunities(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create basic optimization opportunities when none are identified"""
        opportunities = []
        
        # Always create a cost review opportunity
        opportunities.append({
            'type': 'cost_reduction',
            'title': 'Cost Optimization Review',
            'description': 'Comprehensive cost optimization analysis and implementation',
            'potential_savings': analysis.get('total_cost', 0) * 0.15,
            'urgency': UrgencyLevel.MEDIUM,
            'category': OptimizationCategory.COST_REDUCTION,
            'complexity': ImplementationComplexity.MODERATE,
            'context': {
                'review_type': 'comprehensive',
                'analysis_results': analysis
            }
        })
        
        # Resource optimization opportunity
        opportunities.append({
            'type': 'performance_optimization',
            'title': 'Resource Optimization',
            'description': 'Optimize resource allocation and performance',
            'potential_savings': 0,
            'urgency': UrgencyLevel.MEDIUM,
            'category': OptimizationCategory.PERFORMANCE_IMPROVEMENT,
            'complexity': ImplementationComplexity.MODERATE,
            'context': {
                'optimization_type': 'resources'
            }
        })
        
        return opportunities
    
    def _create_fallback_command(self, opportunity: Dict, cluster_config: Dict) -> ActionableCommand:
        """Create a fallback command for an opportunity"""
        return ActionableCommand(
            command_id=f"fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{opportunity.get('type', 'unknown')}",
            title=f"Fallback: {opportunity.get('title', 'Unknown Optimization')}",
            description=f"Fallback implementation for: {opportunity.get('description', 'optimization task')}",
            category=opportunity.get('category', OptimizationCategory.OPERATIONS_EFFICIENCY),
            urgency=opportunity.get('urgency', UrgencyLevel.MEDIUM),
            complexity=opportunity.get('complexity', ImplementationComplexity.SIMPLE),
            estimated_savings_monthly=opportunity.get('potential_savings', 0),
            implementation_hours=2.0,
            success_probability=0.7,
            commands={
                'kubectl': [
                    "# Fallback command - manual review required",
                    "kubectl get all --all-namespaces"
                ]
            },
            manifests={},
            validation_steps=["Review implementation manually"],
            rollback_commands=["# No changes made"],
            prerequisites=["Manual review"],
            expected_impact="Manual optimization review",
            risk_assessment="Low risk - manual review only"
        )
    
    def _create_emergency_commands(self, analysis: Dict, cluster_config: Dict) -> List[ActionableCommand]:
        """Create emergency fallback commands when nothing else works"""
        commands = []
        
        # Basic cluster review command
        commands.append(ActionableCommand(
            command_id=f"emergency_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title="Emergency Cluster Review",
            description="Basic cluster review and optimization identification",
            category=OptimizationCategory.OPERATIONS_EFFICIENCY,
            urgency=UrgencyLevel.MEDIUM,
            complexity=ImplementationComplexity.SIMPLE,
            estimated_savings_monthly=analysis.get('total_cost', 0) * 0.1,
            implementation_hours=4.0,
            success_probability=0.8,
            commands={
                'kubectl': [
                    "kubectl get nodes -o wide",
                    "kubectl top nodes",
                    "kubectl get pods --all-namespaces",
                    "kubectl top pods --all-namespaces --sort-by=cpu"
                ],
                'azure_cli': [
                    f"az aks show --resource-group {cluster_config.get('resource_group', 'unknown')} --name {cluster_config.get('cluster_name', 'unknown')} --query agentPoolProfiles"
                ]
            },
            manifests={},
            validation_steps=[
                "Review cluster status",
                "Analyze resource utilization",
                "Identify optimization opportunities"
            ],
            rollback_commands=[],
            prerequisites=["Cluster access"],
            expected_impact="Baseline cluster analysis",
            risk_assessment="No risk - read-only operations"
        ))
        
        return commands
    
    def _create_emergency_execution_plan(self, cluster_config: Dict, analysis_results: Dict) -> ExecutionPlan:
        """Create emergency execution plan when all else fails"""
        emergency_commands = self._create_emergency_commands(analysis_results, cluster_config)
        
        return ExecutionPlan(
            plan_id=f"emergency_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            generated_at=datetime.now(),
            cluster_info=self._extract_cluster_info(cluster_config, {}),
            total_potential_savings=sum(cmd.estimated_savings_monthly for cmd in emergency_commands),
            total_implementation_hours=sum(cmd.implementation_hours for cmd in emergency_commands),
            overall_risk_score=0.1,
            actionable_commands=emergency_commands,
            execution_sequence=[cmd.command_id for cmd in emergency_commands],
            summary={
                'total_commands': len(emergency_commands),
                'emergency_mode': True,
                'generated_at': datetime.now().isoformat()
            },
            ai_insights="Emergency plan generated. Manual cluster review recommended to identify specific optimization opportunities."
        )

    async def _collect_comprehensive_data(self, cluster_config: Dict[str, Any]) -> Dict[str, Any]:
        """Collect comprehensive real-time data"""
        tasks = []
        
        # Get cluster resource ID if available
        cluster_resource_id = cluster_config.get('cluster_resource_id')
        if cluster_resource_id:
            tasks.append(
                self.data_collector.get_real_time_cluster_metrics(cluster_resource_id)
            )
        
        # Get cluster inventory
        subscription_id = cluster_config.get('subscription_id')
        cluster_name = cluster_config.get('cluster_name')
        if subscription_id and cluster_name:
            tasks.append(
                self.data_collector.get_cluster_resource_inventory(subscription_id, cluster_name)
            )
        
        # Get live workload analysis
        tasks.append(self.data_collector.get_live_workload_analysis())
        
        # Get cost allocation data
        workspace_id = cluster_config.get('log_analytics_workspace_id')
        if workspace_id:
            tasks.append(
                self.data_collector.get_cost_allocation_data(workspace_id)
            )
        
        # Execute all data collection tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        real_time_data = {}
        for i, result in enumerate(results):
            if not isinstance(result, Exception):
                real_time_data.update(result)
        
        return real_time_data
    
    def _enrich_analysis_results(
        self,
        analysis_results: Dict[str, Any],
        real_time_data: Dict[str, Any],
        cluster_dna: Any 
    ) -> Dict[str, Any]:
        """Enrich analysis results with real-time data - FIXED to handle ClusterDNA object"""
        try:
            enriched = analysis_results.copy()
            
            # Add real-time metrics
            enriched['real_time_metrics'] = real_time_data
            
            # Add cluster DNA insights - handle both dict and object
            if hasattr(cluster_dna, '__dict__'):
                # ClusterDNA object - convert to dict for storage
                enriched['cluster_dna'] = {
                    'cluster_personality': getattr(cluster_dna, 'cluster_personality', 'unknown'),
                    'optimization_readiness_score': getattr(cluster_dna, 'optimization_readiness_score', 0.5),
                    'uniqueness_score': getattr(cluster_dna, 'uniqueness_score', 0.5),
                    'temporal_readiness_score': getattr(cluster_dna, 'temporal_readiness_score', 0.5),
                    'rbac_enabled': getattr(cluster_dna, 'rbac_enabled', False),
                    'network_policies_enabled': getattr(cluster_dna, 'network_policies_enabled', False),
                    'pod_security_enabled': getattr(cluster_dna, 'pod_security_enabled', False),
                    'security_posture': getattr(cluster_dna, 'security_posture', 'unknown'),
                    'compliance_score': getattr(cluster_dna, 'compliance_score', 0.5)
                }
            else:
                # Dictionary - use as-is
                enriched['cluster_dna'] = cluster_dna
            
            # Calculate composite scores with improved error handling
            try:
                efficiency_score = self._calculate_efficiency_score(analysis_results, real_time_data)
                cost_potential = self._calculate_cost_potential(analysis_results, real_time_data)
                performance_score = self._calculate_performance_score(real_time_data)
                security_score = self._calculate_security_score(cluster_dna, real_time_data)
                sustainability_score = self._calculate_sustainability_score(analysis_results, real_time_data)
                
                enriched['composite_scores'] = {
                    'efficiency_score': efficiency_score,
                    'cost_optimization_potential': cost_potential,
                    'performance_score': performance_score,
                    'security_score': security_score,
                    'sustainability_score': sustainability_score
                }
            except Exception as score_error:
                logger.error(f"❌ Error calculating composite scores: {score_error}")
                # Provide default scores if calculation fails
                enriched['composite_scores'] = {
                    'efficiency_score': 50.0,
                    'cost_optimization_potential': 0.0,
                    'performance_score': 50.0,
                    'security_score': 50.0,
                    'sustainability_score': 50.0
                }
            
            return enriched
            
        except Exception as e:
            logger.error(f"❌ Error enriching analysis results: {e}")
            logger.error(f"❌ cluster_dna type: {type(cluster_dna)}")
            logger.error(f"❌ cluster_dna attributes: {dir(cluster_dna) if hasattr(cluster_dna, '__dict__') else 'not an object'}")
            
            # Return original results if enrichment fails
            return analysis_results

    async def _identify_optimization_opportunities(
        self,
        enriched_analysis: Dict[str, Any],
        ml_strategy: Dict[str, Any],
        cluster_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify specific optimization opportunities"""
        opportunities = []
        
        # Cost reduction opportunities
        cost_opportunities = self._identify_cost_opportunities(enriched_analysis)
        opportunities.extend(cost_opportunities)
        
        # Performance opportunities
        performance_opportunities = self._identify_performance_opportunities(enriched_analysis)
        opportunities.extend(performance_opportunities)
        
        # Security opportunities
        security_opportunities = self._identify_security_opportunities(enriched_analysis)
        opportunities.extend(security_opportunities)
        
        # Compliance opportunities
        compliance_opportunities = self._identify_compliance_opportunities(enriched_analysis)
        opportunities.extend(compliance_opportunities)
        
        # Reliability opportunities
        reliability_opportunities = self._identify_reliability_opportunities(enriched_analysis)
        opportunities.extend(reliability_opportunities)
        
        # Storage optimization opportunities
        storage_opportunities = self._identify_storage_opportunities(enriched_analysis)
        opportunities.extend(storage_opportunities)
        
        # Network optimization opportunities
        network_opportunities = self._identify_network_opportunities(enriched_analysis)
        opportunities.extend(network_opportunities)
        
        # Monitoring enhancement opportunities
        monitoring_opportunities = self._identify_monitoring_opportunities(enriched_analysis)
        opportunities.extend(monitoring_opportunities)
        
        # Sustainability opportunities
        sustainability_opportunities = self._identify_sustainability_opportunities(enriched_analysis)
        opportunities.extend(sustainability_opportunities)
        
        return opportunities
    
    def _identify_cost_opportunities(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify cost reduction opportunities"""
        opportunities = []
        
        # Right-sizing opportunity
        cpu_utilization = analysis.get('composite_scores', {}).get('efficiency_score', 50)
        if cpu_utilization < 40:
            opportunities.append({
                'type': 'resource_rightsizing',
                'title': 'Aggressive Resource Right-sizing',
                'description': f'CPU utilization at {cpu_utilization:.1f}% indicates significant over-provisioning',
                'potential_savings': analysis.get('total_cost', 0) * 0.35,
                'urgency': UrgencyLevel.HIGH,
                'category': OptimizationCategory.COST_REDUCTION,
                'complexity': ImplementationComplexity.MODERATE,
                'context': {
                    'current_utilization': cpu_utilization,
                    'target_utilization': 70,
                    'affected_workloads': analysis.get('real_time_metrics', {}).get('deployments', {})
                }
            })
        
        # HPA implementation opportunity
        deployments_without_hpa = analysis.get('real_time_metrics', {}).get('deployments', {}).get('without_hpa', 0)
        if deployments_without_hpa > 0:
            opportunities.append({
                'type': 'hpa_implementation',
                'title': 'Horizontal Pod Autoscaler Implementation',
                'description': f'{deployments_without_hpa} deployments lack autoscaling',
                'potential_savings': analysis.get('total_cost', 0) * 0.25,
                'urgency': UrgencyLevel.HIGH,
                'category': OptimizationCategory.COST_REDUCTION,
                'complexity': ImplementationComplexity.SIMPLE,
                'context': {
                    'deployments_count': deployments_without_hpa,
                    'target_cpu_percentage': 70
                }
            })
        
        # Node pool optimization
        real_time_data = analysis.get('real_time_metrics', {})
        if 'cluster_info' in real_time_data:
            cluster_info = real_time_data['cluster_info']
            total_nodes = cluster_info.get('totalNodes', 0)
            if total_nodes > 10:
                opportunities.append({
                    'type': 'node_pool_optimization',
                    'title': 'Node Pool Optimization',
                    'description': f'Large cluster with {total_nodes} nodes - optimize node pools',
                    'potential_savings': analysis.get('total_cost', 0) * 0.20,
                    'urgency': UrgencyLevel.MEDIUM,
                    'category': OptimizationCategory.COST_REDUCTION,
                    'complexity': ImplementationComplexity.COMPLEX,
                    'context': {
                        'current_nodes': total_nodes,
                        'vm_size': cluster_info.get('vmSize'),
                        'recommendation': 'implement_spot_instances'
                    }
                })
        
        # Storage cost optimization
        storage_data = analysis.get('real_time_metrics', {}).get('storage', {})
        total_storage_gb = storage_data.get('total_storage_gb', 0)
        if total_storage_gb > 500:
            opportunities.append({
                'type': 'storage_optimization',
                'title': 'Storage Cost Optimization',
                'description': f'{total_storage_gb:.1f}GB of storage with optimization potential',
                'potential_savings': min(analysis.get('total_cost', 0) * 0.15, total_storage_gb * 0.1),
                'urgency': UrgencyLevel.MEDIUM,
                'category': OptimizationCategory.COST_REDUCTION,
                'complexity': ImplementationComplexity.MODERATE,
                'context': {
                    'total_storage_gb': total_storage_gb,
                    'storage_classes': storage_data.get('storage_classes', {}),
                    'unused_pvcs': storage_data.get('unused_pvcs', [])
                }
            })
        
        return opportunities
    
    def _identify_performance_opportunities(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify performance improvement opportunities"""
        opportunities = []
        
        # Resource limits optimization
        deployments_data = analysis.get('real_time_metrics', {}).get('deployments', {})
        without_limits = deployments_data.get('without_resource_limits', 0)
        if without_limits > 0:
            opportunities.append({
                'type': 'resource_limits_optimization',
                'title': 'Resource Limits Implementation',
                'description': f'{without_limits} deployments lack resource limits',
                'potential_savings': 0,  # Performance improvement, not cost
                'urgency': UrgencyLevel.HIGH,
                'category': OptimizationCategory.PERFORMANCE_IMPROVEMENT,
                'complexity': ImplementationComplexity.SIMPLE,
                'context': {
                    'deployments_without_limits': without_limits,
                    'recommended_limits': 'implement_based_on_usage'
                }
            })
        
        # Node affinity optimization
        pods_data = analysis.get('real_time_metrics', {}).get('pods', {})
        node_distribution = pods_data.get('node_distribution', {})
        if len(node_distribution) > 1:
            # Check for uneven distribution
            pod_counts = list(node_distribution.values())
            if max(pod_counts) > min(pod_counts) * 2:
                opportunities.append({
                    'type': 'node_affinity_optimization',
                    'title': 'Pod Distribution Optimization',
                    'description': 'Uneven pod distribution across nodes detected',
                    'potential_savings': 0,
                    'urgency': UrgencyLevel.MEDIUM,
                    'category': OptimizationCategory.PERFORMANCE_IMPROVEMENT,
                    'complexity': ImplementationComplexity.MODERATE,
                    'context': {
                        'node_distribution': node_distribution,
                        'recommendation': 'implement_pod_anti_affinity'
                    }
                })
        
        return opportunities
    
    def _identify_security_opportunities(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify security enhancement opportunities"""
        opportunities = []
        
        # Pod Security Standards
        opportunities.append({
            'type': 'pod_security_standards',
            'title': 'Pod Security Standards Implementation',
            'description': 'Implement Pod Security Standards for enhanced security',
            'potential_savings': 0,
            'urgency': UrgencyLevel.HIGH,
            'category': OptimizationCategory.SECURITY_ENHANCEMENT,
            'complexity': ImplementationComplexity.MODERATE,
            'context': {
                'recommendation': 'implement_restricted_profile'
            }
        })
        
        # Network Policies
        services_data = analysis.get('real_time_metrics', {}).get('services', {})
        external_services = services_data.get('external_services', [])
        if len(external_services) > 0:
            opportunities.append({
                'type': 'network_policies',
                'title': 'Network Policies Implementation',
                'description': f'{len(external_services)} external services need network policies',
                'potential_savings': 0,
                'urgency': UrgencyLevel.HIGH,
                'category': OptimizationCategory.SECURITY_ENHANCEMENT,
                'complexity': ImplementationComplexity.COMPLEX,
                'context': {
                    'external_services': external_services,
                    'recommendation': 'implement_default_deny'
                }
            })
        
        return opportunities
    
    def _identify_compliance_opportunities(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify compliance alignment opportunities"""
        opportunities = []
        
        # RBAC audit
        opportunities.append({
            'type': 'rbac_optimization',
            'title': 'RBAC Security Audit and Optimization',
            'description': 'Implement least-privilege RBAC policies',
            'potential_savings': 0,
            'urgency': UrgencyLevel.MEDIUM,
            'category': OptimizationCategory.COMPLIANCE_ALIGNMENT,
            'complexity': ImplementationComplexity.COMPLEX,
            'context': {
                'recommendation': 'audit_and_minimize_permissions'
            }
        })
        
        return opportunities
    
    def _identify_reliability_opportunities(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify reliability improvement opportunities"""
        opportunities = []
        
        # Backup strategy
        opportunities.append({
            'type': 'backup_strategy',
            'title': 'Comprehensive Backup Strategy',
            'description': 'Implement automated backup and disaster recovery',
            'potential_savings': 0,
            'urgency': UrgencyLevel.MEDIUM,
            'category': OptimizationCategory.RELIABILITY_BOOST,
            'complexity': ImplementationComplexity.COMPLEX,
            'context': {
                'recommendation': 'implement_velero_backup'
            }
        })
        
        return opportunities
    
    def _identify_storage_opportunities(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify storage optimization opportunities"""
        opportunities = []
        
        storage_data = analysis.get('real_time_metrics', {}).get('storage', {})
        unused_pvcs = storage_data.get('unused_pvcs', [])
        
        if len(unused_pvcs) > 0:
            opportunities.append({
                'type': 'unused_storage_cleanup',
                'title': 'Unused Storage Cleanup',
                'description': f'{len(unused_pvcs)} unused PVCs consuming resources',
                'potential_savings': len(unused_pvcs) * 50,  # Estimate $50/month per unused PVC
                'urgency': UrgencyLevel.MEDIUM,
                'category': OptimizationCategory.COST_REDUCTION,
                'complexity': ImplementationComplexity.SIMPLE,
                'context': {
                    'unused_pvcs': unused_pvcs
                }
            })
        
        return opportunities
    
    def _identify_network_opportunities(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify network optimization opportunities"""
        opportunities = []
        
        services_data = analysis.get('real_time_metrics', {}).get('services', {})
        load_balancer_count = services_data.get('load_balancer', 0)
        
        if load_balancer_count > 3:
            opportunities.append({
                'type': 'ingress_consolidation',
                'title': 'Load Balancer Consolidation',
                'description': f'{load_balancer_count} LoadBalancer services - consider ingress controller',
                'potential_savings': load_balancer_count * 25,  # $25/month per LB saved
                'urgency': UrgencyLevel.MEDIUM,
                'category': OptimizationCategory.COST_REDUCTION,
                'complexity': ImplementationComplexity.MODERATE,
                'context': {
                    'load_balancer_count': load_balancer_count,
                    'recommendation': 'implement_nginx_ingress'
                }
            })
        
        return opportunities
    
    def _identify_monitoring_opportunities(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify monitoring enhancement opportunities"""
        opportunities = []
        
        # Always recommend comprehensive monitoring
        opportunities.append({
            'type': 'monitoring_enhancement',
            'title': 'Advanced Monitoring Implementation',
            'description': 'Implement comprehensive monitoring and alerting',
            'potential_savings': 0,
            'urgency': UrgencyLevel.MEDIUM,
            'category': OptimizationCategory.OPERATIONS_EFFICIENCY,
            'complexity': ImplementationComplexity.MODERATE,
            'context': {
                'recommendation': 'implement_prometheus_grafana'
            }
        })
        
        return opportunities
    
    def _identify_sustainability_opportunities(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify sustainability optimization opportunities"""
        opportunities = []
        
        sustainability_score = analysis.get('composite_scores', {}).get('sustainability_score', 50)
        if sustainability_score < 70:
            opportunities.append({
                'type': 'sustainability_optimization',
                'title': 'Carbon Footprint Optimization',
                'description': 'Optimize cluster for reduced carbon footprint',
                'potential_savings': 0,
                'urgency': UrgencyLevel.LOW,
                'category': OptimizationCategory.SUSTAINABILITY,
                'complexity': ImplementationComplexity.MODERATE,
                'context': {
                    'current_score': sustainability_score,
                    'recommendation': 'implement_spot_instances_and_scheduling'
                }
            })
        
        return opportunities
    
    async def _generate_actionable_commands(
        self,
        opportunity: Dict[str, Any],
        analysis: Dict[str, Any],
        cluster_config: Dict[str, Any]
    ) -> List[ActionableCommand]:
        """Generate actionable commands for a specific opportunity"""
        opportunity_type = opportunity['type']
        handler = self.scenario_handlers.get(opportunity_type, self._handle_generic_opportunity)
        
        try:
            commands = await handler(opportunity, analysis, cluster_config)
            return commands if isinstance(commands, list) else [commands]
        except Exception as e:
            logger.error(f"Error generating commands for {opportunity_type}: {e}")
            return []
    
    async def _handle_cost_reduction(self, opportunity: Dict, analysis: Dict, config: Dict) -> List[ActionableCommand]:
        """Handle cost reduction scenarios"""
        commands = []
        
        if opportunity['type'] == 'resource_rightsizing':
            # Generate right-sizing commands
            context = opportunity.get('context', {})
            affected_workloads = context.get('affected_workloads', {})
            
            ai_commands = await self.ai_engine.generate_optimized_commands(
                'resource_rightsizing', context
            )
            
            command = ActionableCommand(
                command_id=f"rightsizing_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                title=opportunity['title'],
                description=opportunity['description'],
                category=opportunity['category'],
                urgency=opportunity['urgency'],
                complexity=opportunity['complexity'],
                estimated_savings_monthly=opportunity['potential_savings'],
                implementation_hours=8.0,
                success_probability=0.85,
                commands={
                    'kubectl': [
                        "# Backup current deployment configurations",
                        "kubectl get deployments --all-namespaces -o yaml > deployment-backup.yaml",
                        "# Apply optimized resource configurations",
                        "kubectl apply -f optimized-resources.yaml",
                        "# Monitor rollout status",
                        "kubectl rollout status deployment/{deployment-name} -n {namespace}"
                    ],
                    'azure_cli': [
                        "# Monitor cluster metrics",
                        "az aks show --resource-group {rg} --name {cluster} --query 'agentPoolProfiles[0].count'"
                    ]
                },
                manifests={
                    'optimized-resources.yaml': self._generate_rightsizing_manifest(context)
                },
                validation_steps=[
                    "Verify all pods are running: kubectl get pods --all-namespaces",
                    "Check resource utilization: kubectl top nodes",
                    "Monitor application performance for 24 hours"
                ],
                rollback_commands=[
                    "kubectl apply -f deployment-backup.yaml",
                    "kubectl rollout undo deployment/{deployment-name} -n {namespace}"
                ],
                prerequisites=[
                    "Cluster admin access",
                    "Performance monitoring tools installed",
                    "Maintenance window scheduled"
                ],
                expected_impact=f"Reduce resource allocation by 30-50%, saving ${opportunity['potential_savings']:,.2f}/month",
                risk_assessment="Medium risk - potential performance impact if over-optimized"
            )
            commands.append(command)
        
        elif opportunity['type'] == 'hpa_implementation':
            # Generate HPA implementation commands
            context = opportunity.get('context', {})
            
            command = ActionableCommand(
                command_id=f"hpa_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                title=opportunity['title'],
                description=opportunity['description'],
                category=opportunity['category'],
                urgency=opportunity['urgency'],
                complexity=opportunity['complexity'],
                estimated_savings_monthly=opportunity['potential_savings'],
                implementation_hours=4.0,
                success_probability=0.90,
                commands={
                    'kubectl': [
                        "# Create HPA for deployments",
                        "kubectl autoscale deployment {deployment-name} --cpu-percent=70 --min=2 --max=10 -n {namespace}",
                        "# Apply custom HPA manifests",
                        "kubectl apply -f hpa-configs.yaml",
                        "# Verify HPA status",
                        "kubectl get hpa --all-namespaces"
                    ]
                },
                manifests={
                    'hpa-configs.yaml': self._generate_hpa_manifest(context)
                },
                validation_steps=[
                    "Verify HPA creation: kubectl get hpa --all-namespaces",
                    "Check scaling behavior: kubectl describe hpa {hpa-name}",
                    "Load test to verify autoscaling works"
                ],
                rollback_commands=[
                    "kubectl delete hpa --all --all-namespaces",
                    "kubectl scale deployment {deployment-name} --replicas=3 -n {namespace}"
                ],
                prerequisites=[
                    "Metrics server installed",
                    "Resource requests configured on deployments",
                    "Load testing tools available"
                ],
                expected_impact=f"Dynamic scaling based on demand, saving ${opportunity['potential_savings']:,.2f}/month",
                risk_assessment="Low risk - easily reversible, improves resource efficiency"
            )
            commands.append(command)
        
        return commands
    
    async def _handle_performance_optimization(self, opportunity: Dict, analysis: Dict, config: Dict) -> ActionableCommand:
        """Handle performance optimization scenarios"""
        context = opportunity.get('context', {})
        
        return ActionableCommand(
            command_id=f"perf_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title=opportunity['title'],
            description=opportunity['description'],
            category=opportunity['category'],
            urgency=opportunity['urgency'],
            complexity=opportunity['complexity'],
            estimated_savings_monthly=0,
            implementation_hours=6.0,
            success_probability=0.80,
            commands={
                'kubectl': [
                    "# Apply resource limits",
                    "kubectl apply -f resource-limits.yaml",
                    "# Configure pod anti-affinity",
                    "kubectl apply -f pod-affinity-rules.yaml"
                ]
            },
            manifests={
                'resource-limits.yaml': self._generate_resource_limits_manifest(context),
                'pod-affinity-rules.yaml': self._generate_affinity_manifest(context)
            },
            validation_steps=[
                "Check resource limits: kubectl describe deployment {deployment-name}",
                "Verify pod distribution: kubectl get pods -o wide"
            ],
            rollback_commands=[
                "kubectl delete -f resource-limits.yaml",
                "kubectl delete -f pod-affinity-rules.yaml"
            ],
            prerequisites=[
                "Understanding of workload requirements",
                "Performance baseline established"
            ],
            expected_impact="Improved application performance and stability",
            risk_assessment="Medium risk - monitor performance after implementation"
        )
    
    async def _handle_security_hardening(self, opportunity: Dict, analysis: Dict, config: Dict) -> ActionableCommand:
        """Handle security hardening scenarios"""
        return ActionableCommand(
            command_id=f"security_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title=opportunity['title'],
            description=opportunity['description'],
            category=opportunity['category'],
            urgency=opportunity['urgency'],
            complexity=opportunity['complexity'],
            estimated_savings_monthly=0,
            implementation_hours=12.0,
            success_probability=0.75,
            commands={
                'kubectl': [
                    "# Apply Pod Security Standards",
                    "kubectl apply -f pod-security-standards.yaml",
                    "# Implement Network Policies",
                    "kubectl apply -f network-policies.yaml",
                    "# Configure RBAC",
                    "kubectl apply -f rbac-config.yaml"
                ]
            },
            manifests={
                'pod-security-standards.yaml': self._generate_pod_security_manifest(),
                'network-policies.yaml': self._generate_network_policies_manifest(),
                'rbac-config.yaml': self._generate_rbac_manifest()
            },
            validation_steps=[
                "Test pod security: kubectl auth can-i create pod --as=system:serviceaccount:default:default",
                "Verify network policies: kubectl describe networkpolicy",
                "Audit RBAC permissions: kubectl auth can-i --list"
            ],
            rollback_commands=[
                "kubectl delete -f pod-security-standards.yaml",
                "kubectl delete -f network-policies.yaml",
                "kubectl delete -f rbac-config.yaml"
            ],
            prerequisites=[
                "Security team approval",
                "Application compatibility testing",
                "Emergency access procedures defined"
            ],
            expected_impact="Enhanced cluster security posture and compliance",
            risk_assessment="High risk - test thoroughly in non-production first"
        )
    
    async def _handle_compliance_alignment(self, opportunity: Dict, analysis: Dict, config: Dict) -> ActionableCommand:
        """Handle compliance alignment scenarios"""
        return ActionableCommand(
            command_id=f"compliance_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title=opportunity['title'],
            description=opportunity['description'],
            category=opportunity['category'],
            urgency=opportunity['urgency'],
            complexity=opportunity['complexity'],
            estimated_savings_monthly=0,
            implementation_hours=16.0,
            success_probability=0.70,
            commands={
                'kubectl': [
                    "# Apply compliance policies",
                    "kubectl apply -f compliance-policies.yaml",
                    "# Configure audit logging",
                    "kubectl apply -f audit-config.yaml"
                ],
                'azure_cli': [
                    "# Enable Azure Policy for AKS",
                    "az aks enable-addons --addons azure-policy --name {cluster} --resource-group {rg}"
                ]
            },
            manifests={
                'compliance-policies.yaml': self._generate_compliance_manifest(),
                'audit-config.yaml': self._generate_audit_manifest()
            },
            validation_steps=[
                "Verify policy compliance: kubectl get constrainttemplates",
                "Check audit logs: kubectl logs -n gatekeeper-system"
            ],
            rollback_commands=[
                "kubectl delete -f compliance-policies.yaml",
                "kubectl delete -f audit-config.yaml"
            ],
            prerequisites=[
                "Compliance team review",
                "Legal approval for audit logging",
                "Documentation update"
            ],
            expected_impact="Meet compliance requirements and pass audits",
            risk_assessment="Medium risk - ensure compatibility with existing workloads"
        )
    
    async def _handle_reliability_improvement(self, opportunity: Dict, analysis: Dict, config: Dict) -> ActionableCommand:
        """Handle reliability improvement scenarios"""
        return ActionableCommand(
            command_id=f"reliability_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title=opportunity['title'],
            description=opportunity['description'],
            category=opportunity['category'],
            urgency=opportunity['urgency'],
            complexity=opportunity['complexity'],
            estimated_savings_monthly=0,
            implementation_hours=20.0,
            success_probability=0.85,
            commands={
                'kubectl': [
                    "# Install Velero for backups",
                    "kubectl apply -f velero-install.yaml",
                    "# Configure backup schedules",
                    "kubectl apply -f backup-schedules.yaml",
                    "# Set up monitoring",
                    "kubectl apply -f monitoring-config.yaml"
                ]
            },
            manifests={
                'velero-install.yaml': self._generate_velero_manifest(),
                'backup-schedules.yaml': self._generate_backup_schedule_manifest(),
                'monitoring-config.yaml': self._generate_monitoring_manifest()
            },
            validation_steps=[
                "Verify Velero installation: kubectl get pods -n velero",
                "Test backup creation: velero backup create test-backup",
                "Validate monitoring: kubectl get servicemonitor"
            ],
            rollback_commands=[
                "kubectl delete namespace velero",
                "kubectl delete -f backup-schedules.yaml"
            ],
            prerequisites=[
                "Backup storage account configured",
                "Disaster recovery plan documented",
                "Recovery testing scheduled"
            ],
            expected_impact="Improved disaster recovery capabilities and data protection",
            risk_assessment="Low risk - backup solutions are non-intrusive"
        )
    
    async def _handle_storage_optimization(self, opportunity: Dict, analysis: Dict, config: Dict) -> ActionableCommand:
        """Handle storage optimization scenarios"""
        context = opportunity.get('context', {})
        unused_pvcs = context.get('unused_pvcs', [])
        
        return ActionableCommand(
            command_id=f"storage_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title=opportunity['title'],
            description=opportunity['description'],
            category=opportunity['category'],
            urgency=opportunity['urgency'],
            complexity=opportunity['complexity'],
            estimated_savings_monthly=opportunity['potential_savings'],
            implementation_hours=4.0,
            success_probability=0.95,
            commands={
                'kubectl': [
                    "# List unused PVCs",
                    "kubectl get pvc --all-namespaces",
                    "# Delete unused PVCs (after verification)",
                    f"# kubectl delete pvc {' '.join([pvc['name'] for pvc in unused_pvcs[:3]])}",
                    "# Optimize storage classes",
                    "kubectl apply -f optimized-storage-classes.yaml"
                ]
            },
            manifests={
                'optimized-storage-classes.yaml': self._generate_storage_class_manifest(context)
            },
            validation_steps=[
                "Verify no data loss: Check application functionality",
                "Monitor storage usage: kubectl get pv",
                "Validate storage class optimization"
            ],
            rollback_commands=[
                "# Restore from backup if needed",
                "kubectl apply -f original-storage-classes.yaml"
            ],
            prerequisites=[
                "Data backup completed",
                "Application owners notified",
                "Storage impact assessment done"
            ],
            expected_impact=f"Remove unused storage, save ${opportunity['potential_savings']:,.2f}/month",
            risk_assessment="Low risk - only removing confirmed unused resources"
        )
    
    async def _handle_network_optimization(self, opportunity: Dict, analysis: Dict, config: Dict) -> ActionableCommand:
        """Handle network optimization scenarios"""
        context = opportunity.get('context', {})
        
        return ActionableCommand(
            command_id=f"network_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title=opportunity['title'],
            description=opportunity['description'],
            category=opportunity['category'],
            urgency=opportunity['urgency'],
            complexity=opportunity['complexity'],
            estimated_savings_monthly=opportunity['potential_savings'],
            implementation_hours=8.0,
            success_probability=0.80,
            commands={
                'kubectl': [
                    "# Install NGINX Ingress Controller",
                    "kubectl apply -f nginx-ingress-controller.yaml",
                    "# Configure ingress rules",
                    "kubectl apply -f ingress-rules.yaml",
                    "# Update services to ClusterIP",
                    "kubectl apply -f updated-services.yaml"
                ]
            },
            manifests={
                'nginx-ingress-controller.yaml': self._generate_ingress_controller_manifest(),
                'ingress-rules.yaml': self._generate_ingress_rules_manifest(context),
                'updated-services.yaml': self._generate_updated_services_manifest(context)
            },
            validation_steps=[
                "Test ingress controller: kubectl get pods -n ingress-nginx",
                "Verify ingress rules: kubectl get ingress --all-namespaces",
                "Test application accessibility"
            ],
            rollback_commands=[
                "kubectl delete -f ingress-rules.yaml",
                "kubectl delete -f nginx-ingress-controller.yaml",
                "# Restore original LoadBalancer services"
            ],
            prerequisites=[
                "DNS configuration updated",
                "SSL certificates prepared",
                "Load testing planned"
            ],
            expected_impact=f"Consolidate load balancers, save ${opportunity['potential_savings']:,.2f}/month",
            risk_assessment="Medium risk - network changes affect application accessibility"
        )
    
    async def _handle_monitoring_enhancement(self, opportunity: Dict, analysis: Dict, config: Dict) -> ActionableCommand:
        """Handle monitoring enhancement scenarios"""
        return ActionableCommand(
            command_id=f"monitoring_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title=opportunity['title'],
            description=opportunity['description'],
            category=opportunity['category'],
            urgency=opportunity['urgency'],
            complexity=opportunity['complexity'],
            estimated_savings_monthly=0,
            implementation_hours=12.0,
            success_probability=0.85,
            commands={
                'kubectl': [
                    "# Install Prometheus stack",
                    "kubectl apply -f prometheus-stack.yaml",
                    "# Configure Grafana dashboards",
                    "kubectl apply -f grafana-dashboards.yaml",
                    "# Set up alerting rules",
                    "kubectl apply -f alert-rules.yaml"
                ]
            },
            manifests={
                'prometheus-stack.yaml': self._generate_prometheus_stack_manifest(),
                'grafana-dashboards.yaml': self._generate_grafana_dashboards_manifest(),
                'alert-rules.yaml': self._generate_alert_rules_manifest()
            },
            validation_steps=[
                "Verify Prometheus: kubectl get pods -n monitoring",
                "Check Grafana access: kubectl port-forward -n monitoring svc/grafana 3000:3000",
                "Test alerting: kubectl get prometheusrules"
            ],
            rollback_commands=[
                "kubectl delete namespace monitoring",
                "kubectl delete -f prometheus-stack.yaml"
            ],
            prerequisites=[
                "Storage provisioned for Prometheus data",
                "Alerting destinations configured",
                "Team training on Grafana"
            ],
            expected_impact="Comprehensive monitoring and alerting capabilities",
            risk_assessment="Low risk - monitoring is non-intrusive to workloads"
        )
    
    async def _handle_gitops_implementation(self, opportunity: Dict, analysis: Dict, config: Dict) -> ActionableCommand:
        """Handle GitOps implementation scenarios"""
        return ActionableCommand(
            command_id=f"gitops_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title="GitOps Implementation with ArgoCD",
            description="Implement GitOps workflow for better deployment management",
            category=OptimizationCategory.OPERATIONS_EFFICIENCY,
            urgency=UrgencyLevel.MEDIUM,
            complexity=ImplementationComplexity.COMPLEX,
            estimated_savings_monthly=0,
            implementation_hours=24.0,
            success_probability=0.75,
            commands={
                'kubectl': [
                    "# Install ArgoCD",
                    "kubectl create namespace argocd",
                    "kubectl apply -n argocd -f argocd-install.yaml",
                    "# Configure applications",
                    "kubectl apply -f argocd-applications.yaml"
                ]
            },
            manifests={
                'argocd-install.yaml': self._generate_argocd_manifest(),
                'argocd-applications.yaml': self._generate_argocd_applications_manifest()
            },
            validation_steps=[
                "Verify ArgoCD installation: kubectl get pods -n argocd",
                "Check application sync: kubectl get applications -n argocd",
                "Test GitOps workflow"
            ],
            rollback_commands=[
                "kubectl delete namespace argocd",
                "kubectl delete -f argocd-applications.yaml"
            ],
            prerequisites=[
                "Git repositories prepared",
                "RBAC configured for ArgoCD",
                "Team training on GitOps"
            ],
            expected_impact="Automated deployments and improved deployment consistency",
            risk_assessment="Medium risk - changes deployment workflow"
        )
    
    async def _handle_service_mesh_optimization(self, opportunity: Dict, analysis: Dict, config: Dict) -> ActionableCommand:
        """Handle service mesh optimization scenarios"""
        return ActionableCommand(
            command_id=f"servicemesh_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title="Istio Service Mesh Implementation",
            description="Implement Istio service mesh for enhanced observability and security",
            category=OptimizationCategory.PERFORMANCE_IMPROVEMENT,
            urgency=UrgencyLevel.LOW,
            complexity=ImplementationComplexity.EXPERT,
            estimated_savings_monthly=0,
            implementation_hours=40.0,
            success_probability=0.65,
            commands={
                'kubectl': [
                    "# Install Istio",
                    "kubectl apply -f istio-system.yaml",
                    "# Configure service mesh",
                    "kubectl apply -f istio-config.yaml",
                    "# Enable sidecar injection",
                    "kubectl label namespace default istio-injection=enabled"
                ]
            },
            manifests={
                'istio-system.yaml': self._generate_istio_manifest(),
                'istio-config.yaml': self._generate_istio_config_manifest()
            },
            validation_steps=[
                "Verify Istio installation: kubectl get pods -n istio-system",
                "Check sidecar injection: kubectl get pods",
                "Test service mesh features"
            ],
            rollback_commands=[
                "kubectl label namespace default istio-injection-",
                "kubectl delete namespace istio-system"
            ],
            prerequisites=[
                "Service mesh expertise",
                "Application compatibility testing",
                "Performance impact assessment"
            ],
            expected_impact="Enhanced security, observability, and traffic management",
            risk_assessment="High risk - significant architecture change"
        )
    
    async def _handle_ai_ml_optimization(self, opportunity: Dict, analysis: Dict, config: Dict) -> ActionableCommand:
        """Handle AI/ML workload optimization scenarios"""
        return ActionableCommand(
            command_id=f"aiml_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title="AI/ML Workload Optimization",
            description="Optimize cluster for AI/ML workloads with GPU support",
            category=OptimizationCategory.PERFORMANCE_IMPROVEMENT,
            urgency=UrgencyLevel.LOW,
            complexity=ImplementationComplexity.EXPERT,
            estimated_savings_monthly=0,
            implementation_hours=32.0,
            success_probability=0.70,
            commands={
                'azure_cli': [
                    "# Add GPU node pool",
                    "az aks nodepool add --cluster-name {cluster} --resource-group {rg} --name gpupool --node-vm-size Standard_NC6s_v3 --node-count 1",
                    "# Install NVIDIA device plugin",
                    "kubectl apply -f nvidia-device-plugin.yaml"
                ],
                'kubectl': [
                    "# Configure ML workloads",
                    "kubectl apply -f ml-workloads.yaml",
                    "# Set up Kubeflow",
                    "kubectl apply -f kubeflow-config.yaml"
                ]
            },
            manifests={
                'nvidia-device-plugin.yaml': self._generate_nvidia_plugin_manifest(),
                'ml-workloads.yaml': self._generate_ml_workloads_manifest(),
                'kubeflow-config.yaml': self._generate_kubeflow_manifest()
            },
            validation_steps=[
                "Verify GPU nodes: kubectl get nodes -l accelerator=nvidia-tesla-k80",
                "Test GPU workload: kubectl apply -f gpu-test-job.yaml",
                "Check Kubeflow: kubectl get pods -n kubeflow"
            ],
            rollback_commands=[
                "az aks nodepool delete --cluster-name {cluster} --resource-group {rg} --name gpupool",
                "kubectl delete -f kubeflow-config.yaml"
            ],
            prerequisites=[
                "GPU quota available",
                "ML team requirements defined",
                "Cost approval for GPU instances"
            ],
            expected_impact="Optimized infrastructure for AI/ML workloads",
            risk_assessment="Medium risk - GPU resources are expensive"
        )
    
    async def _handle_disaster_recovery(self, opportunity: Dict, analysis: Dict, config: Dict) -> ActionableCommand:
        """Handle disaster recovery scenarios"""
        return ActionableCommand(
            command_id=f"dr_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title="Disaster Recovery Implementation",
            description="Implement comprehensive disaster recovery strategy",
            category=OptimizationCategory.RELIABILITY_BOOST,
            urgency=UrgencyLevel.HIGH,
            complexity=ImplementationComplexity.EXPERT,
            estimated_savings_monthly=0,
            implementation_hours=48.0,
            success_probability=0.80,
            commands={
                'azure_cli': [
                    "# Create secondary region cluster",
                    "az aks create --resource-group {dr-rg} --name {dr-cluster} --location {dr-region}",
                    "# Set up cross-region networking",
                    "az network vnet peering create --name dr-peering --resource-group {rg} --vnet-name {vnet}"
                ],
                'kubectl': [
                    "# Configure disaster recovery",
                    "kubectl apply -f dr-config.yaml",
                    "# Set up data replication",
                    "kubectl apply -f data-replication.yaml"
                ]
            },
            manifests={
                'dr-config.yaml': self._generate_dr_config_manifest(),
                'data-replication.yaml': self._generate_data_replication_manifest()
            },
            validation_steps=[
                "Verify DR cluster: az aks get-credentials --resource-group {dr-rg} --name {dr-cluster}",
                "Test failover procedure",
                "Validate data replication"
            ],
            rollback_commands=[
                "az aks delete --resource-group {dr-rg} --name {dr-cluster}",
                "kubectl delete -f dr-config.yaml"
            ],
            prerequisites=[
                "DR region selected",
                "Network connectivity established",
                "RTO/RPO requirements defined"
            ],
            expected_impact="Complete disaster recovery capability",
            risk_assessment="High risk - complex multi-region setup"
        )
    
    async def _handle_sustainability_optimization(self, opportunity: Dict, analysis: Dict, config: Dict) -> ActionableCommand:
        """Handle sustainability optimization scenarios"""
        return ActionableCommand(
            command_id=f"sustainability_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title="Sustainability Optimization",
            description="Optimize cluster for reduced carbon footprint",
            category=OptimizationCategory.SUSTAINABILITY,
            urgency=UrgencyLevel.LOW,
            complexity=ImplementationComplexity.MODERATE,
            estimated_savings_monthly=0,
            implementation_hours=16.0,
            success_probability=0.85,
            commands={
                'azure_cli': [
                    "# Add spot instance node pool",
                    "az aks nodepool add --cluster-name {cluster} --resource-group {rg} --name spotpool --priority Spot --eviction-policy Delete --spot-max-price 0.1",
                    "# Configure carbon-aware scheduling",
                    "kubectl apply -f carbon-aware-scheduler.yaml"
                ]
            },
            manifests={
                'carbon-aware-scheduler.yaml': self._generate_carbon_aware_manifest(),
                'spot-workloads.yaml': self._generate_spot_workloads_manifest()
            },
            validation_steps=[
                "Verify spot nodes: kubectl get nodes -l kubernetes.azure.com/scalesetpriority=spot",
                "Test workload scheduling",
                "Monitor carbon metrics"
            ],
            rollback_commands=[
                "az aks nodepool delete --cluster-name {cluster} --resource-group {rg} --name spotpool",
                "kubectl delete -f carbon-aware-scheduler.yaml"
            ],
            prerequisites=[
                "Workload fault tolerance",
                "Sustainability metrics defined",
                "Team commitment to green practices"
            ],
            expected_impact="Reduced carbon footprint and energy consumption",
            risk_assessment="Medium risk - spot instances can be evicted"
        )
    
    async def _handle_generic_opportunity(self, opportunity: Dict, analysis: Dict, config: Dict) -> ActionableCommand:
        """Handle generic opportunities"""
        return ActionableCommand(
            command_id=f"generic_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title=opportunity.get('title', 'Generic Optimization'),
            description=opportunity.get('description', 'Generic optimization opportunity'),
            category=opportunity.get('category', OptimizationCategory.OPERATIONS_EFFICIENCY),
            urgency=opportunity.get('urgency', UrgencyLevel.MEDIUM),
            complexity=opportunity.get('complexity', ImplementationComplexity.MODERATE),
            estimated_savings_monthly=opportunity.get('potential_savings', 0),
            implementation_hours=8.0,
            success_probability=0.75,
            commands={'kubectl': ["# Generic optimization commands"]},
            manifests={},
            validation_steps=["Verify implementation"],
            rollback_commands=["# Rollback commands"],
            prerequisites=["Review requirements"],
            expected_impact="Generic optimization impact",
            risk_assessment="Medium risk - review before implementation"
        )
    
    def _prioritize_commands(self, commands: List[ActionableCommand]) -> List[ActionableCommand]:
        """Prioritize commands based on impact, urgency, and risk"""
        def calculate_priority_score(cmd: ActionableCommand) -> float:
            # Weight factors
            urgency_weights = {
                UrgencyLevel.CRITICAL: 10,
                UrgencyLevel.HIGH: 7,
                UrgencyLevel.MEDIUM: 4,
                UrgencyLevel.LOW: 1
            }
            
            complexity_weights = {
                ImplementationComplexity.SIMPLE: 1.0,
                ImplementationComplexity.MODERATE: 0.8,
                ImplementationComplexity.COMPLEX: 0.6,
                ImplementationComplexity.EXPERT: 0.4
            }
            
            # Calculate impact score (ROI)
            roi = cmd.estimated_savings_monthly / max(cmd.implementation_hours * 100, 1)  # Assuming $100/hour
            
            # Calculate priority score
            priority_score = (
                urgency_weights[cmd.urgency] * 0.4 +
                roi * 0.3 +
                cmd.success_probability * 10 * 0.2 +
                complexity_weights[cmd.complexity] * 5 * 0.1
            )
            
            return priority_score
        
        # Sort by priority score (descending)
        return sorted(commands, key=calculate_priority_score, reverse=True)
    
    def _create_execution_sequence(self, commands: List[ActionableCommand]) -> List[str]:
        """Create optimal execution sequence"""
        # Group by dependencies and complexity
        sequence = []
        
        # High urgency, low complexity first
        critical_simple = [cmd.command_id for cmd in commands 
                          if cmd.urgency == UrgencyLevel.CRITICAL 
                          and cmd.complexity == ImplementationComplexity.SIMPLE]
        sequence.extend(critical_simple)
        
        # High impact, medium complexity
        high_impact = [cmd.command_id for cmd in commands 
                      if cmd.estimated_savings_monthly > 1000 
                      and cmd.complexity == ImplementationComplexity.MODERATE
                      and cmd.command_id not in sequence]
        sequence.extend(high_impact)
        
        # Remaining commands by priority
        remaining = [cmd.command_id for cmd in commands if cmd.command_id not in sequence]
        sequence.extend(remaining)
        
        return sequence
    
    def _calculate_plan_metrics(self, commands: List[ActionableCommand]) -> Dict[str, float]:
        """Calculate overall plan metrics"""
        total_savings = sum(cmd.estimated_savings_monthly for cmd in commands)
        total_hours = sum(cmd.implementation_hours for cmd in commands)
        
        # Calculate weighted risk score
        risk_scores = []
        for cmd in commands:
            if cmd.complexity == ImplementationComplexity.EXPERT:
                risk_scores.append(0.8)
            elif cmd.complexity == ImplementationComplexity.COMPLEX:
                risk_scores.append(0.6)
            elif cmd.complexity == ImplementationComplexity.MODERATE:
                risk_scores.append(0.4)
            else:
                risk_scores.append(0.2)
        
        overall_risk = np.mean(risk_scores) if risk_scores else 0.5
        
        return {
            'total_savings': total_savings,
            'total_hours': total_hours,
            'risk_score': overall_risk,
            'command_count': len(commands),
            'avg_success_probability': np.mean([cmd.success_probability for cmd in commands])
        }
    
    def _generate_plan_summary(self, commands: List[ActionableCommand], metrics: Dict[str, float]) -> Dict[str, Any]:
        """Generate plan summary"""
        # Group by category
        category_summary = {}
        for cmd in commands:
            cat = cmd.category.value
            if cat not in category_summary:
                category_summary[cat] = {
                    'count': 0,
                    'savings': 0,
                    'hours': 0
                }
            category_summary[cat]['count'] += 1
            category_summary[cat]['savings'] += cmd.estimated_savings_monthly
            category_summary[cat]['hours'] += cmd.implementation_hours
        
        # Urgency breakdown
        urgency_summary = {}
        for cmd in commands:
            urgency = cmd.urgency.value
            urgency_summary[urgency] = urgency_summary.get(urgency, 0) + 1
        
        return {
            'total_commands': len(commands),
            'total_potential_savings': metrics['total_savings'],
            'total_implementation_hours': metrics['total_hours'],
            'estimated_roi': (metrics['total_savings'] * 12) / (metrics['total_hours'] * 100) if metrics['total_hours'] > 0 else 0,
            'overall_risk_score': metrics['risk_score'],
            'category_breakdown': category_summary,
            'urgency_breakdown': urgency_summary,
            'quick_wins': len([cmd for cmd in commands 
                             if cmd.complexity == ImplementationComplexity.SIMPLE 
                             and cmd.estimated_savings_monthly > 100]),
            'high_impact_initiatives': len([cmd for cmd in commands 
                                          if cmd.estimated_savings_monthly > 1000])
        }
    
    def _safe_extract_cluster_dna_attribute(self, cluster_dna: Any, attribute: str, default: Any = None) -> Any:
        """Safely extract attribute from ClusterDNA object or dictionary"""
        try:
            if hasattr(cluster_dna, 'get') and callable(getattr(cluster_dna, 'get')):
                # Dictionary-like access
                return cluster_dna.get(attribute, default)
            else:
                # Object attribute access
                return getattr(cluster_dna, attribute, default)
        except Exception:
            return default

    # Updated method signature and implementation
    def _extract_cluster_info(self, cluster_config: Dict, cluster_dna: Any) -> Dict[str, Any]:
        """Extract key cluster information - FIXED to handle ClusterDNA object"""
        try:
            base_info = {
                'cluster_name': cluster_config.get('cluster_name', 'unknown'),
                'resource_group': cluster_config.get('resource_group', 'unknown'),
                'region': cluster_config.get('region', 'unknown'),
                'node_count': cluster_config.get('node_count', 0),
                'kubernetes_version': cluster_config.get('kubernetes_version', 'unknown')
            }
            
            # Add ClusterDNA information safely
            if cluster_dna:
                base_info.update({
                    'cluster_size': self._safe_extract_cluster_dna_attribute(cluster_dna, 'cluster_size_category', 'unknown'),
                    'workload_type': self._safe_extract_cluster_dna_attribute(cluster_dna, 'primary_workload_type', 'unknown'),
                    'cluster_personality': self._safe_extract_cluster_dna_attribute(cluster_dna, 'cluster_personality', 'unknown'),
                    'optimization_readiness': self._safe_extract_cluster_dna_attribute(cluster_dna, 'optimization_readiness_score', 0.5),
                    'security_posture': self._safe_extract_cluster_dna_attribute(cluster_dna, 'security_posture', 'unknown')
                })
            
            return base_info
            
        except Exception as e:
            logger.error(f"❌ Error extracting cluster info: {e}")
            return {
                'cluster_name': cluster_config.get('cluster_name', 'unknown'),
                'resource_group': cluster_config.get('resource_group', 'unknown'),
                'region': 'unknown',
                'node_count': 0,
                'kubernetes_version': 'unknown',
                'cluster_size': 'unknown',
                'workload_type': 'unknown',
                'extraction_error': str(e)
            }
    
    def _generate_plan_id(self) -> str:
        """Generate unique plan ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_input = f"{timestamp}_{np.random.randint(1000, 9999)}"
        return f"plan_{timestamp}_{hashlib.md5(hash_input.encode()).hexdigest()[:8]}"
    
    # Scoring helper methods
    def _calculate_efficiency_score(self, analysis: Dict, real_time: Dict) -> float:
        """Calculate cluster efficiency score"""
        cpu_metrics = real_time.get('cpu_utilization', {})
        memory_metrics = real_time.get('memory_utilization', {})
        
        cpu_avg = cpu_metrics.get('average', 50)
        memory_avg = memory_metrics.get('average', 50)
        
        # Optimal range is 60-80%
        cpu_efficiency = 100 - abs(cpu_avg - 70)
        memory_efficiency = 100 - abs(memory_avg - 70)
        
        return (cpu_efficiency + memory_efficiency) / 2
    
    def _calculate_cost_potential(self, analysis: Dict, real_time: Dict) -> float:
        """Calculate cost optimization potential"""
        current_cost = analysis.get('total_cost', 0)
        if current_cost == 0:
            return 0
        
        efficiency = self._calculate_efficiency_score(analysis, real_time)
        potential = max(0, (100 - efficiency) / 100 * current_cost)
        
        return potential
    
    def _calculate_performance_score(self, real_time: Dict) -> float:
        """Calculate performance score"""
        cpu_metrics = real_time.get('cpu_utilization', {})
        memory_metrics = real_time.get('memory_utilization', {})
        
        cpu_max = cpu_metrics.get('maximum', 0)
        memory_max = memory_metrics.get('maximum', 0)
        
        # Lower max utilization indicates better headroom
        cpu_score = max(0, 100 - cpu_max)
        memory_score = max(0, 100 - memory_max)
        
        return (cpu_score + memory_score) / 2
    
    def _calculate_security_score(self, cluster_dna: Any, real_time: Dict) -> float:
        """Calculate security score"""
        # Basic security scoring based on configuration
        score = 50  # Base score
        
        try:
            # Check for security features - handle both dict and ClusterDNA object
            if hasattr(cluster_dna, 'get'):
                # Dictionary-like access
                if cluster_dna.get('rbac_enabled', False):
                    score += 20
                if cluster_dna.get('network_policies_enabled', False):
                    score += 15
                if cluster_dna.get('pod_security_enabled', False):
                    score += 15
            else:
                # Object attribute access
                if getattr(cluster_dna, 'rbac_enabled', False):
                    score += 20
                if getattr(cluster_dna, 'network_policies_enabled', False):
                    score += 15
                if getattr(cluster_dna, 'pod_security_enabled', False):
                    score += 15
        except Exception as e:
            logger.warning(f"⚠️ Error calculating security score: {e}")
            # Return base score if there's an error
            return 50
        
        return min(100, score)
    
    def _calculate_sustainability_score(self, analysis: Dict, real_time: Dict) -> float:
        """Calculate sustainability score"""
        efficiency = self._calculate_efficiency_score(analysis, real_time)
        
        # Higher efficiency = better sustainability
        base_score = efficiency
        
        # Additional factors could include region carbon intensity, spot instance usage, etc.
        
        return base_score
    
    # Manifest generation helper methods
    def _generate_rightsizing_manifest(self, context: Dict) -> str:
        """Generate resource right-sizing manifest"""
        return """# Example resource optimization
apiVersion: apps/v1
kind: Deployment
metadata:
  name: example-deployment
spec:
  template:
    spec:
      containers:
      - name: app
        resources:
          requests:
            cpu: "200m"
            memory: "256Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
"""
    
    def _generate_hpa_manifest(self, context: Dict) -> str:
        """Generate HPA manifest"""
        return """apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: example-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: example-deployment
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
"""
    
    def _generate_resource_limits_manifest(self, context: Dict) -> str:
        """Generate resource limits manifest"""
        return """apiVersion: v1
kind: LimitRange
metadata:
  name: resource-limits
spec:
  limits:
  - default:
      cpu: "500m"
      memory: "512Mi"
    defaultRequest:
      cpu: "100m"
      memory: "128Mi"
    type: Container
"""
    
    def _generate_affinity_manifest(self, context: Dict) -> str:
        """Generate pod affinity manifest"""
        return """apiVersion: apps/v1
kind: Deployment
metadata:
  name: example-deployment
spec:
  template:
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - example-app
              topologyKey: kubernetes.io/hostname
"""
    
    def _generate_pod_security_manifest(self) -> str:
        """Generate Pod Security Standards manifest"""
        return """apiVersion: v1
kind: Namespace
metadata:
  name: secure-namespace
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
"""
    
    def _generate_network_policies_manifest(self) -> str:
        """Generate network policies manifest"""
        return """apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-internal
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: default
"""
    
    def _generate_rbac_manifest(self) -> str:
        """Generate RBAC manifest"""
        return """apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: readonly-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "endpoints"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: readonly-binding
subjects:
- kind: User
  name: readonly-user
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: readonly-role
  apiGroup: rbac.authorization.k8s.io
"""
    
    def _generate_compliance_manifest(self) -> str:
        """Generate compliance policies manifest"""
        return """apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata:
  name: k8srequiredlabels
spec:
  crd:
    spec:
      names:
        kind: K8sRequiredLabels
      validation:
        type: object
        properties:
          labels:
            type: array
            items:
              type: string
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequiredlabels
        violation[{"msg": msg}] {
          required := input.parameters.labels
          provided := input.review.object.metadata.labels
          missing := required[_]
          not provided[missing]
          msg := sprintf("Missing required label: %v", [missing])
        }
"""
    
    def _generate_audit_manifest(self) -> str:
        """Generate audit configuration manifest"""
        return """apiVersion: audit.k8s.io/v1
kind: Policy
rules:
- level: RequestResponse
  resources:
  - group: ""
    resources: ["secrets", "configmaps"]
- level: Request
  resources:
  - group: ""
    resources: ["pods", "services", "deployments"]
"""
    
    def _generate_velero_manifest(self) -> str:
        """Generate Velero backup manifest"""
        return """apiVersion: v1
kind: Namespace
metadata:
  name: velero
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: velero
  namespace: velero
spec:
  replicas: 1
  selector:
    matchLabels:
      app: velero
  template:
    metadata:
      labels:
        app: velero
    spec:
      containers:
      - name: velero
        image: velero/velero:latest
        env:
        - name: AZURE_SUBSCRIPTION_ID
          value: "your-subscription-id"
        - name: AZURE_RESOURCE_GROUP
          value: "your-resource-group"
"""
    
    def _generate_backup_schedule_manifest(self) -> str:
        """Generate backup schedule manifest"""
        return """apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: daily-backup
  namespace: velero
spec:
  schedule: "0 2 * * *"
  template:
    includedNamespaces:
    - "*"
    excludedNamespaces:
    - kube-system
    - velero
    storageLocation: default
    ttl: 720h0m0s
"""
    
    def _generate_monitoring_manifest(self) -> str:
        """Generate monitoring configuration manifest"""
        return """apiVersion: v1
kind: ServiceMonitor
metadata:
  name: cluster-monitoring
spec:
  selector:
    matchLabels:
      app: prometheus
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
"""
    
    def _generate_storage_class_manifest(self, context: Dict) -> str:
        """Generate optimized storage class manifest"""
        return """apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: optimized-ssd
provisioner: disk.csi.azure.com
parameters:
  skuName: Premium_LRS
  cachingmode: ReadOnly
  kind: Managed
reclaimPolicy: Delete
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
"""
    
    def _generate_ingress_controller_manifest(self) -> str:
        """Generate NGINX ingress controller manifest"""
        return """apiVersion: v1
kind: Namespace
metadata:
  name: ingress-nginx
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-ingress-controller
  namespace: ingress-nginx
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nginx-ingress-controller
  template:
    metadata:
      labels:
        app: nginx-ingress-controller
    spec:
      containers:
      - name: nginx-ingress-controller
        image: k8s.gcr.io/ingress-nginx/controller:latest
        ports:
        - containerPort: 80
        - containerPort: 443
"""
    
    def _generate_ingress_rules_manifest(self, context: Dict) -> str:
        """Generate ingress rules manifest"""
        return """apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app-service
            port:
              number: 80
"""
    
    def _generate_updated_services_manifest(self, context: Dict) -> str:
        """Generate updated services manifest"""
        return """apiVersion: v1
kind: Service
metadata:
  name: app-service
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8080
  selector:
    app: example-app
"""
    
    def _generate_prometheus_stack_manifest(self) -> str:
        """Generate Prometheus stack manifest"""
        return """apiVersion: v1
kind: Namespace
metadata:
  name: monitoring
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:latest
        ports:
        - containerPort: 9090
"""
    
    def _generate_grafana_dashboards_manifest(self) -> str:
        """Generate Grafana dashboards manifest"""
        return """apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboards
  namespace: monitoring
data:
  cluster-overview.json: |
    {
      "dashboard": {
        "title": "Cluster Overview",
        "panels": [
          {
            "title": "CPU Usage",
            "type": "graph",
            "targets": [
              {
                "expr": "100 - (avg(irate(node_cpu_seconds_total{mode='idle'}[5m])) * 100)"
              }
            ]
          }
        ]
      }
    }
"""
    
    def _generate_alert_rules_manifest(self) -> str:
        """Generate alert rules manifest"""
        return """apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: cluster-alerts
  namespace: monitoring
spec:
  groups:
  - name: cluster.rules
    rules:
    - alert: HighCPUUsage
      expr: node_cpu_usage_percent > 80
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High CPU usage detected"
        description: "CPU usage is above 80% for more than 5 minutes"
"""
    
    def _generate_argocd_manifest(self) -> str:
        """Generate ArgoCD manifest"""
        return """apiVersion: v1
kind: Namespace
metadata:
  name: argocd
---
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: argocd
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://argoproj.github.io/argo-helm
    chart: argo-cd
    targetRevision: "*"
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
"""
    
    def _generate_argocd_applications_manifest(self) -> str:
        """Generate ArgoCD applications manifest"""
        return """apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: example-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/example/example-app
    targetRevision: main
    path: k8s/
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
"""
    
    def _generate_istio_manifest(self) -> str:
        """Generate Istio manifest"""
        return """apiVersion: v1
kind: Namespace
metadata:
  name: istio-system
---
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
metadata:
  name: control-plane
  namespace: istio-system
spec:
  components:
    pilot:
      k8s:
        resources:
          requests:
            cpu: 200m
            memory: 128Mi
"""
    
    def _generate_istio_config_manifest(self) -> str:
        """Generate Istio configuration manifest"""
        return """apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: example-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - "*"
---
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: example-vs
spec:
  hosts:
  - "*"
  gateways:
  - example-gateway
  http:
  - route:
    - destination:
        host: example-service
"""
    
    def _generate_nvidia_plugin_manifest(self) -> str:
        """Generate NVIDIA device plugin manifest"""
        return """apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: nvidia-device-plugin-daemonset
  namespace: kube-system
spec:
  selector:
    matchLabels:
      name: nvidia-device-plugin-ds
  updateStrategy:
    type: RollingUpdate
  template:
    metadata:
      labels:
        name: nvidia-device-plugin-ds
    spec:
      tolerations:
      - key: nvidia.com/gpu
        operator: Exists
        effect: NoSchedule
      containers:
      - image: nvidia/k8s-device-plugin:latest
        name: nvidia-device-plugin-ctr
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop: ["ALL"]
"""
    
    def _generate_ml_workloads_manifest(self) -> str:
        """Generate ML workloads manifest"""
        return """apiVersion: batch/v1
kind: Job
metadata:
  name: ml-training-job
spec:
  template:
    spec:
      containers:
      - name: ml-trainer
        image: tensorflow/tensorflow:latest-gpu
        resources:
          limits:
            nvidia.com/gpu: 1
          requests:
            cpu: "2"
            memory: "8Gi"
        command: ["python", "train.py"]
      restartPolicy: Never
"""
    
    def _generate_kubeflow_manifest(self) -> str:
        """Generate Kubeflow manifest"""
        return """apiVersion: v1
kind: Namespace
metadata:
  name: kubeflow
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kubeflow-dashboard
  namespace: kubeflow
spec:
  replicas: 1
  selector:
    matchLabels:
      app: kubeflow-dashboard
  template:
    metadata:
      labels:
        app: kubeflow-dashboard
    spec:
      containers:
      - name: dashboard
        image: kubeflownotebooks/jupyter-scipy:latest
        ports:
        - containerPort: 8888
"""
    
    def _generate_dr_config_manifest(self) -> str:
        """Generate disaster recovery configuration manifest"""
        return """apiVersion: v1
kind: ConfigMap
metadata:
  name: dr-config
data:
  primary-cluster: "cluster-primary"
  secondary-cluster: "cluster-dr"
  replication-interval: "300s"
  backup-retention: "30d"
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: dr-sync
spec:
  schedule: "*/5 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: dr-sync
            image: alpine:latest
            command: ["sh", "-c", "echo 'DR sync executed'"]
          restartPolicy: OnFailure
"""
    
    def _generate_data_replication_manifest(self) -> str:
        """Generate data replication manifest"""
        return """apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-replicator
spec:
  replicas: 1
  selector:
    matchLabels:
      app: data-replicator
  template:
    metadata:
      labels:
        app: data-replicator
    spec:
      containers:
      - name: replicator
        image: postgres:latest
        env:
        - name: PGPASSWORD
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: password
        command: ["pg_basebackup", "-h", "primary-db", "-D", "/backup"]
"""
    
    def _generate_carbon_aware_manifest(self) -> str:
        """Generate carbon-aware scheduling manifest"""
        return """apiVersion: v1
kind: ConfigMap
metadata:
  name: carbon-scheduler-config
data:
  config.yaml: |
    carbonIntensity:
      provider: "azure"
      region: "westeurope"
      updateInterval: "1h"
    scheduling:
      preferLowCarbon: true
      carbonThreshold: 50
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: carbon-scheduler
spec:
  replicas: 1
  selector:
    matchLabels:
      app: carbon-scheduler
  template:
    metadata:
      labels:
        app: carbon-scheduler
    spec:
      containers:
      - name: scheduler
        image: carbon-scheduler:latest
        volumeMounts:
        - name: config
          mountPath: /config
      volumes:
      - name: config
        configMap:
          name: carbon-scheduler-config
"""
    
    def _generate_spot_workloads_manifest(self) -> str:
        """Generate spot instance workloads manifest"""
        return """apiVersion: apps/v1
kind: Deployment
metadata:
  name: spot-workload
spec:
  replicas: 3
  selector:
    matchLabels:
      app: spot-workload
  template:
    metadata:
      labels:
        app: spot-workload
    spec:
      nodeSelector:
        kubernetes.azure.com/scalesetpriority: spot
      tolerations:
      - key: kubernetes.azure.com/scalesetpriority
        operator: Equal
        value: spot
        effect: NoSchedule
      containers:
      - name: app
        image: nginx:latest
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
"""

class AdvancedExecutableCommandGenerator:
    """
    Advanced executable command generator that wraps ComprehensiveAKSOptimizer
    for backward compatibility and enhanced command generation.
    """
    
    def __init__(self):
        self.optimizer = ComprehensiveAKSOptimizer()
        self.logger = logging.getLogger(__name__)
    
    def set_cluster_config(self, cluster_config: Dict):
        """Set cluster configuration"""
        self.optimizer.set_cluster_config(cluster_config)
        self.logger.info("🛠️ Cluster config set for advanced generator")
    
    def get_cluster_config(self) -> Dict:
        """Get current cluster configuration"""
        return self.optimizer.get_cluster_config()
    
    async def initialize_for_cluster(self, cluster_config: Dict[str, Any]) -> bool:
        """Initialize for a specific cluster"""
        return await self.optimizer.initialize_for_cluster(cluster_config)
    
    async def generate_comprehensive_execution_plan(
        self,
        ml_strategy: Dict[str, Any],
        cluster_dna: Dict[str, Any], 
        analysis_results: Dict[str, Any],
        cluster_config: Dict[str, Any]
    ) -> ExecutionPlan:
        """
        Generate comprehensive execution plan - main method your code expects
        
        Args:
            ml_strategy: ML-driven optimization strategy
            cluster_dna: Cluster DNA/fingerprint data
            analysis_results: Cost and performance analysis results
            cluster_config: Current cluster configuration
            
        Returns:
            ExecutionPlan: Comprehensive plan with actionable commands
        """
        try:
            self.logger.info("🚀 Generating comprehensive execution plan using advanced ML engine")
            
            # Set cluster config if provided
            if cluster_config:
                self.set_cluster_config(cluster_config)
            
            # Use the comprehensive optimizer to generate the execution plan
            execution_plan = await self.optimizer.generate_comprehensive_execution_plan(
                ml_strategy=ml_strategy,
                cluster_dna=cluster_dna,
                analysis_results=analysis_results,
                cluster_config=self.optimizer.cluster_config
            )
            
            self.logger.info(f"✅ Generated comprehensive plan with {len(execution_plan.actionable_commands)} actionable commands")
            self.logger.info(f"💰 Total potential savings: ${execution_plan.total_potential_savings:,.2f}/month")
            self.logger.info(f"⏱️ Total implementation time: {execution_plan.total_implementation_hours:.1f} hours")
            
            return execution_plan
            
        except Exception as e:
            self.logger.error(f"❌ Failed to generate comprehensive execution plan: {e}")
            # Return a fallback plan
            return self._create_fallback_execution_plan(
                self.optimizer.cluster_config or cluster_config or {}, 
                analysis_results
            )
    
    async def generate_executable_commands(
        self,
        ml_strategy: Dict[str, Any],
        cluster_dna: Dict[str, Any],
        analysis_results: Dict[str, Any],
        cluster_config: Dict[str, Any] = None
    ) -> ExecutionPlan:
        """
        Generate executable commands - alternative method name
        """
        return await self.generate_comprehensive_execution_plan(
            ml_strategy=ml_strategy,
            cluster_dna=cluster_dna,
            analysis_results=analysis_results,
            cluster_config=cluster_config or self.optimizer.cluster_config
        )
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """Get optimization status"""
        status = self.optimizer.get_optimization_status()
        status['generator_type'] = 'AdvancedExecutableCommandGenerator'
        return status
    
    def get_plan_status(self, plan_id: str) -> Dict[str, Any]:
        """Get status of a specific execution plan"""
        return {
            'plan_id': plan_id,
            'status': 'generated',
            'timestamp': datetime.now().isoformat(),
            'generator_type': 'AdvancedExecutableCommandGenerator'
        }

    def validate_execution_plan(self, execution_plan: ExecutionPlan) -> Dict[str, bool]:
        """Validate an execution plan"""
        validation_results = {
            'has_commands': len(execution_plan.actionable_commands) > 0,
            'has_sequence': len(execution_plan.execution_sequence) > 0,
            'has_cluster_info': bool(execution_plan.cluster_info),
            'savings_calculated': execution_plan.total_potential_savings >= 0,
            'hours_estimated': execution_plan.total_implementation_hours > 0
        }
        
        validation_results['is_valid'] = all(validation_results.values())
        
        self.logger.info(f"📋 Plan validation: {'✅ Valid' if validation_results['is_valid'] else '❌ Invalid'}")
        
        return validation_results

    async def preview_execution_plan(
        self,
        ml_strategy: Dict[str, Any],
        cluster_dna: Dict[str, Any], 
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a preview of what the execution plan would contain"""
        try:
            # Generate a lightweight preview without full command generation
            opportunities = len(self.optimizer.scenario_handlers)
            estimated_savings = analysis_results.get('total_cost', 0) * 0.2  # Rough estimate
            
            preview = {
                'estimated_commands': min(opportunities, 15),  # Cap at reasonable number
                'estimated_savings': estimated_savings,
                'estimated_hours': opportunities * 6,  # Rough estimate
                'categories_available': list(OptimizationCategory.__members__.keys()),
                'cluster_configured': bool(self.optimizer.cluster_config),
                'ai_available': self.optimizer.ai_engine.openai_client is not None,
                'preview_timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"👀 Generated execution plan preview: {preview['estimated_commands']} commands, ${preview['estimated_savings']:,.2f} savings")
            
            return preview
            
        except Exception as e:
            self.logger.error(f"❌ Failed to generate plan preview: {e}")
            return {
                'error': str(e),
                'estimated_commands': 0,
                'estimated_savings': 0,
                'preview_timestamp': datetime.now().isoformat()
            }
    
    def get_supported_optimizations(self) -> List[str]:
        """Get supported optimization types"""
        return self.optimizer.get_supported_optimizations()
    
    def _create_fallback_execution_plan(
        self, 
        cluster_config: Dict[str, Any], 
        analysis_results: Dict[str, Any]
    ) -> ExecutionPlan:
        """Create a basic fallback execution plan"""
        
        fallback_command = ActionableCommand(
            command_id=f"fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title="Manual Cluster Review",
            description="Perform manual cluster optimization review",
            category=OptimizationCategory.OPERATIONS_EFFICIENCY,
            urgency=UrgencyLevel.MEDIUM,
            complexity=ImplementationComplexity.SIMPLE,
            estimated_savings_monthly=analysis_results.get('total_cost', 0) * 0.1,
            implementation_hours=4.0,
            success_probability=0.8,
            commands={
                'kubectl': [
                    "kubectl get all --all-namespaces",
                    "kubectl top nodes",
                    "kubectl top pods --all-namespaces"
                ],
                'azure_cli': [
                    f"az aks show --resource-group {cluster_config.get('resource_group', 'unknown')} --name {cluster_config.get('cluster_name', 'unknown')}"
                ]
            },
            manifests={},
            validation_steps=[
                "Review cluster resource utilization",
                "Identify optimization opportunities",
                "Plan implementation strategy"
            ],
            rollback_commands=[],
            prerequisites=["Cluster access", "kubectl configured"],
            expected_impact="Manual optimization identification",
            risk_assessment="Low risk - review only"
        )
        
        return ExecutionPlan(
            plan_id=f"fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            generated_at=datetime.now(),
            cluster_info={
                'cluster_name': cluster_config.get('cluster_name', 'unknown'),
                'resource_group': cluster_config.get('resource_group', 'unknown'),
                'fallback_mode': True
            },
            total_potential_savings=fallback_command.estimated_savings_monthly,
            total_implementation_hours=fallback_command.implementation_hours,
            overall_risk_score=0.2,
            actionable_commands=[fallback_command],
            execution_sequence=[fallback_command.command_id],
            summary={
                'total_commands': 1,
                'fallback_mode': True,
                'reason': 'Advanced command generation failed'
            },
            ai_insights="Fallback plan activated. Manual review recommended to identify optimization opportunities."
        )

# Example usage
async def main():
    """Example usage of the enhanced AKS optimizer"""
    
    # Initialize the optimizer
    optimizer = ComprehensiveAKSOptimizer()
    
    # Example input data (this would come from your existing analysis)
    ml_strategy = {
        "optimization_focus": "cost_reduction",
        "risk_tolerance": "medium",
        "timeline": "3_months"
    }
    
    cluster_dna = {
        "cluster_size_category": "medium",
        "primary_workload_type": "web_applications",
        "compliance_requirements": ["GDPR"],
        "high_availability": True
    }
    
    analysis_results = {
        "total_cost": 5000.0,
        "cpu_utilization": 25.0,
        "memory_utilization": 35.0,
        "storage_gb": 1500.0,
        "namespace_count": 8,
        "deployment_count": 25
    }
    
    cluster_config = {
        "cluster_name": "production-cluster",
        "resource_group": "rg-production",
        "subscription_id": "12345678-abcd-1234-abcd-123456789abc",
        "region": "eastus",
        "node_count": 6,
        "kubernetes_version": "1.28.5",
        "cluster_resource_id": "/subscriptions/12345678-abcd-1234-abcd-123456789abc/resourceGroups/rg-production/providers/Microsoft.ContainerService/managedClusters/production-cluster"
    }
    
    # Generate comprehensive execution plan
    execution_plan = await optimizer.generate_comprehensive_execution_plan(
        ml_strategy, cluster_dna, analysis_results, cluster_config
    )
    
    # Display results
    print(f"Generated {len(execution_plan.actionable_commands)} actionable commands")
    print(f"Total potential savings: ${execution_plan.total_potential_savings:,.2f}/month")
    print(f"Implementation effort: {execution_plan.total_implementation_hours:.1f} hours")
    
    for i, cmd in enumerate(execution_plan.actionable_commands[:3], 1):
        print(f"\n{i}. {cmd.title}")
        print(f"   Category: {cmd.category.value}")
        print(f"   Urgency: {cmd.urgency.value}")
        print(f"   Savings: ${cmd.estimated_savings_monthly:,.2f}/month")
        print(f"   Effort: {cmd.implementation_hours:.1f} hours")

if __name__ == "__main__":
    asyncio.run(main())