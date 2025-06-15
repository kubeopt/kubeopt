#!/usr/bin/env python3
"""
Real-Time AKS Cost Intelligence Platform - Backend
Enterprise-grade cost optimization with live Azure data integration
"""

import asyncio
import json
import logging
import os
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid
import pandas as pd
import numpy as np

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

import structlog

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger()

class AzureDataCollector:
    """Real-time Azure data collector for AKS costs and metrics."""
    
    def __init__(self):
        self.cache = {}
        self.last_update = {}
        
    async def get_aks_cost_data(self, resource_group: str, cluster_name: str, 
                               days_back: int = 30) -> Dict[str, Any]:
        """Get real AKS cost data using Azure CLI and Cost Management API."""
        try:
            logger.info(f"Fetching cost data for {cluster_name} in {resource_group}")
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Use the provided cost data function
            cost_df = await self._get_aks_specific_cost_data(
                resource_group, cluster_name, start_date, end_date
            )
            
            if cost_df is not None and not cost_df.empty:
                processed_data = self._process_cost_dataframe(cost_df)
                return {
                    "success": True,
                    "data": processed_data,
                    "metadata": {
                        "cluster_name": cluster_name,
                        "resource_group": resource_group,
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "end_date": end_date.strftime("%Y-%m-%d"),
                        "days_analyzed": days_back
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "No cost data found or failed to retrieve data",
                    "data": None
                }
                
        except Exception as e:
            logger.error(f"Failed to get cost data: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    async def _get_aks_specific_cost_data(self, resource_group: str, cluster_name: str, 
                                        start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """Get AKS-specific cost data for a specific date range"""
        logger.info(f"Fetching AKS-specific cost data for {cluster_name} from {start_date} to {end_date}")
        
        try:
            # Format dates
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
            
            logger.info(f"Using date range: {start_date_str} to {end_date_str}")
            
            # Get subscription ID
            sub_cmd = "az account show --query id -o tsv"
            sub_result = subprocess.run(sub_cmd, shell=True, check=True, capture_output=True, text=True)
            subscription_id = sub_result.stdout.strip()
            
            if not subscription_id:
                logger.error("Failed to retrieve subscription ID")
                return None
            
            # Get the node resource group
            node_rg_cmd = f"az aks show --resource-group {resource_group} --name {cluster_name} --query nodeResourceGroup -o tsv"
            node_rg_result = subprocess.run(node_rg_cmd, shell=True, check=True, capture_output=True, text=True)
            node_resource_group = node_rg_result.stdout.strip()
            
            logger.info(f"Using node resource group: {node_resource_group}")
            
            # Create cost query
            cost_query = {
                "type": "ActualCost",
                "timeframe": "Custom",
                "timePeriod": {
                    "from": start_date_str,
                    "to": end_date_str
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
                        {"type": "Dimension", "name": "ResourceType"},
                        {"type": "Dimension", "name": "ResourceGroupName"},
                        {"type": "Dimension", "name": "ServiceName"},
                        {"type": "Dimension", "name": "ResourceId"}
                    ],
                    "filter": {
                        "dimensions": {
                            "name": "ResourceGroupName",
                            "operator": "In",
                            "values": [resource_group, node_resource_group]
                        }
                    }
                }
            }
            
            # Save query to temp file
            query_file = f'aks_cost_query_{int(time.time())}.json'
            with open(query_file, 'w', encoding='utf-8') as f:
                json.dump(cost_query, f, indent=2)
            
            try:
                # Execute the REST API call
                api_cmd = f"""
                az rest --method POST \
                --uri "https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.CostManagement/query?api-version=2023-11-01" \
                --body @{query_file} \
                --output json
                """
                
                logger.info("Executing AKS-specific Cost Management API query")
                api_result = subprocess.run(api_cmd, shell=True, check=True, capture_output=True, text=True)
                
                cost_data = json.loads(api_result.stdout)
                logger.info("Successfully parsed cost API response")
                
                # Process the data and create DataFrame
                cost_df = self._process_aks_cost_data(cost_data)
                
                # Add metadata
                if cost_df is not None:
                    cost_df.attrs['start_date'] = start_date_str
                    cost_df.attrs['end_date'] = end_date_str
                    cost_df.attrs['data_source'] = 'Azure Cost Management API'
                
                return cost_df
            
            finally:
                # Clean up temp file
                try:
                    if os.path.exists(query_file):
                        os.remove(query_file)
                except Exception as file_e:
                    logger.warning(f"Failed to remove temporary query file: {file_e}")
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed with return code {e.returncode}")
            logger.error(f"STDERR: {e.stderr}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching AKS-specific cost data: {str(e)}")
            return None

    def _process_aks_cost_data(self, cost_data: Dict) -> Optional[pd.DataFrame]:
        """Process raw cost data from Azure API into DataFrame."""
        try:
            if 'properties' not in cost_data or 'rows' not in cost_data['properties']:
                logger.warning("No cost data found in API response")
                return None
            
            rows = cost_data['properties']['rows']
            columns = cost_data['properties']['columns']
            
            if not rows:
                logger.warning("No cost rows found in API response")
                return None
            
            # Create column mapping
            col_names = [col['name'] for col in columns]
            
            # Create DataFrame
            df = pd.DataFrame(rows, columns=col_names)
            
            # Convert cost column to numeric
            if 'PreTaxCost' in df.columns:
                df['PreTaxCost'] = pd.to_numeric(df['PreTaxCost'], errors='coerce')
            
            # Convert date column
            if 'UsageDate' in df.columns:
                df['UsageDate'] = pd.to_datetime(df['UsageDate'], errors='coerce')
            
            logger.info(f"Processed {len(df)} cost records")
            return df
            
        except Exception as e:
            logger.error(f"Failed to process cost data: {e}")
            return None

    def _process_cost_dataframe(self, cost_df: pd.DataFrame) -> Dict[str, Any]:
        """Process cost DataFrame into summary data."""
        try:
            # Daily costs aggregation
            daily_costs = []
            if 'UsageDate' in cost_df.columns and 'PreTaxCost' in cost_df.columns:
                daily_aggregated = cost_df.groupby(cost_df['UsageDate'].dt.date)['PreTaxCost'].sum().reset_index()
                daily_costs = [
                    {"date": str(row['UsageDate']), "cost": round(row['PreTaxCost'], 2)}
                    for _, row in daily_aggregated.iterrows()
                ]
            
            # Total cost
            total_cost = cost_df['PreTaxCost'].sum() if 'PreTaxCost' in cost_df.columns else 0
            
            # Service breakdown
            service_breakdown = {}
            if 'ServiceName' in cost_df.columns and 'PreTaxCost' in cost_df.columns:
                service_breakdown = cost_df.groupby('ServiceName')['PreTaxCost'].sum().to_dict()
                service_breakdown = {k: round(v, 2) for k, v in service_breakdown.items()}
            
            # Resource type breakdown
            resource_breakdown = {}
            if 'ResourceType' in cost_df.columns and 'PreTaxCost' in cost_df.columns:
                resource_breakdown = cost_df.groupby('ResourceType')['PreTaxCost'].sum().to_dict()
                resource_breakdown = {k: round(v, 2) for k, v in resource_breakdown.items()}
            
            # Calculate trends
            average_daily_cost = total_cost / max(len(daily_costs), 1)
            
            return {
                "daily_costs": sorted(daily_costs, key=lambda x: x['date']),
                "total_cost": round(total_cost, 2),
                "average_daily_cost": round(average_daily_cost, 2),
                "service_breakdown": service_breakdown,
                "resource_breakdown": resource_breakdown,
                "currency": "USD",
                "record_count": len(cost_df)
            }
            
        except Exception as e:
            logger.error(f"Failed to process cost dataframe: {e}")
            return {"daily_costs": [], "total_cost": 0, "service_breakdown": {}, "resource_breakdown": {}}
    
    async def get_aks_metrics(self, resource_group: str, cluster_name: str) -> Dict[str, Any]:
        """Get real-time AKS metrics using kubectl via az aks command invoke."""
        try:
            logger.info(f"Fetching live metrics for {cluster_name}")
            
            # Collect various metrics
            metrics = {}
            
            # Node metrics
            node_metrics = await self._get_node_metrics(resource_group, cluster_name)
            metrics.update(node_metrics)
            
            # Pod metrics
            pod_metrics = await self._get_pod_metrics(resource_group, cluster_name)
            metrics.update(pod_metrics)
            
            # Resource utilization
            utilization_metrics = await self._get_utilization_metrics(resource_group, cluster_name)
            metrics.update(utilization_metrics)
            
            # Namespace metrics
            namespace_metrics = await self._get_namespace_metrics(resource_group, cluster_name)
            metrics.update(namespace_metrics)
            
            # Service metrics
            service_metrics = await self._get_service_metrics(resource_group, cluster_name)
            metrics.update(service_metrics)
            
            return {
                "success": True,
                "data": metrics,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get AKS metrics: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": {}
            }
    
    async def _execute_kubectl_command(self, resource_group: str, cluster_name: str, 
                                     kubectl_cmd: str) -> Optional[Dict]:
        """Execute kubectl command via az aks command invoke."""
        try:
            full_cmd = f'az aks command invoke --resource-group {resource_group} --name {cluster_name} --command "{kubectl_cmd}"'
            
            result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                logger.error(f"kubectl command failed: {result.stderr}")
                return None
            
            response_data = json.loads(result.stdout)
            
            # Extract the actual kubectl output from the logs
            if 'logs' in response_data:
                kubectl_output = '\n'.join(response_data['logs'])
                try:
                    return json.loads(kubectl_output)
                except json.JSONDecodeError:
                    # If it's not JSON, return as text
                    return {"output": kubectl_output}
            
            return response_data
            
        except Exception as e:
            logger.error(f"Failed to execute kubectl command: {e}")
            return None
    
    async def _get_node_metrics(self, resource_group: str, cluster_name: str) -> Dict[str, Any]:
        """Get comprehensive node-level metrics."""
        try:
            # Get nodes in JSON format
            nodes_data = await self._execute_kubectl_command(
                resource_group, cluster_name, "kubectl get nodes -o json"
            )
            
            if not nodes_data or 'items' not in nodes_data:
                return {"node_count": 0, "node_status": {}, "node_details": []}
            
            nodes = nodes_data.get('items', [])
            
            node_metrics = {
                "node_count": len(nodes),
                "node_status": {},
                "node_capacity": {},
                "node_details": [],
                "node_conditions": {}
            }
            
            for node in nodes:
                node_name = node.get('metadata', {}).get('name', 'unknown')
                
                # Node status and conditions
                conditions = node.get('status', {}).get('conditions', [])
                ready_condition = next((c for c in conditions if c.get('type') == 'Ready'), {})
                node_status = ready_condition.get('status', 'Unknown')
                
                node_metrics["node_status"][node_name] = node_status
                
                # Store all conditions
                node_metrics["node_conditions"][node_name] = {
                    condition.get('type', 'Unknown'): condition.get('status', 'Unknown')
                    for condition in conditions
                }
                
                # Node capacity and allocatable resources
                capacity = node.get('status', {}).get('capacity', {})
                allocatable = node.get('status', {}).get('allocatable', {})
                
                node_metrics["node_capacity"][node_name] = {
                    "cpu_capacity": capacity.get('cpu', '0'),
                    "memory_capacity": capacity.get('memory', '0'),
                    "pods_capacity": capacity.get('pods', '0'),
                    "cpu_allocatable": allocatable.get('cpu', '0'),
                    "memory_allocatable": allocatable.get('memory', '0'),
                    "pods_allocatable": allocatable.get('pods', '0')
                }
                
                # Detailed node information
                node_info = node.get('status', {}).get('nodeInfo', {})
                node_metrics["node_details"].append({
                    "name": node_name,
                    "status": node_status,
                    "capacity": capacity,
                    "allocatable": allocatable,
                    "node_info": node_info,
                    "labels": node.get('metadata', {}).get('labels', {}),
                    "taints": node.get('spec', {}).get('taints', []),
                    "creation_timestamp": node.get('metadata', {}).get('creationTimestamp'),
                    "kernel_version": node_info.get('kernelVersion'),
                    "os_image": node_info.get('osImage'),
                    "container_runtime": node_info.get('containerRuntimeVersion')
                })
            
            return node_metrics
            
        except Exception as e:
            logger.error(f"Failed to get node metrics: {e}")
            return {"node_count": 0, "node_status": {}, "node_details": []}
    
    async def _get_pod_metrics(self, resource_group: str, cluster_name: str) -> Dict[str, Any]:
        """Get comprehensive pod-level metrics."""
        try:
            # Get pods across all namespaces
            pods_data = await self._execute_kubectl_command(
                resource_group, cluster_name, "kubectl get pods --all-namespaces -o json"
            )
            
            if not pods_data or 'items' not in pods_data:
                return {"pod_count": 0, "pod_status": {}, "namespace_distribution": {}}
            
            pods = pods_data.get('items', [])
            
            pod_metrics = {
                "pod_count": len(pods),
                "pod_status": {},
                "namespace_distribution": {},
                "pod_phases": {},
                "pod_details": [],
                "container_count": 0,
                "restart_count": 0
            }
            
            for pod in pods:
                namespace = pod.get('metadata', {}).get('namespace', 'default')
                pod_name = pod.get('metadata', {}).get('name', 'unknown')
                phase = pod.get('status', {}).get('phase', 'Unknown')
                
                # Count by namespace
                pod_metrics["namespace_distribution"][namespace] = \
                    pod_metrics["namespace_distribution"].get(namespace, 0) + 1
                
                # Count by phase
                pod_metrics["pod_phases"][phase] = \
                    pod_metrics["pod_phases"].get(phase, 0) + 1
                
                # Container information
                containers = pod.get('spec', {}).get('containers', [])
                container_statuses = pod.get('status', {}).get('containerStatuses', [])
                
                pod_metrics["container_count"] += len(containers)
                
                # Calculate restart counts
                for container_status in container_statuses:
                    pod_metrics["restart_count"] += container_status.get('restartCount', 0)
                
                # Detailed pod information
                pod_metrics["pod_details"].append({
                    "name": pod_name,
                    "namespace": namespace,
                    "phase": phase,
                    "node_name": pod.get('spec', {}).get('nodeName'),
                    "start_time": pod.get('status', {}).get('startTime'),
                    "container_count": len(containers),
                    "restart_count": sum(cs.get('restartCount', 0) for cs in container_statuses),
                    "ready": pod.get('status', {}).get('conditions', [{}])[-1].get('status') == 'True',
                    "labels": pod.get('metadata', {}).get('labels', {}),
                    "annotations": pod.get('metadata', {}).get('annotations', {})
                })
            
            return pod_metrics
            
        except Exception as e:
            logger.error(f"Failed to get pod metrics: {e}")
            return {"pod_count": 0, "pod_status": {}, "namespace_distribution": {}}
    
    async def _get_utilization_metrics(self, resource_group: str, cluster_name: str) -> Dict[str, Any]:
        """Get real-time resource utilization metrics."""
        try:
            utilization = {
                "cpu_utilization": 0,
                "memory_utilization": 0,
                "node_utilization": {},
                "cluster_resource_summary": {}
            }
            
            # Get node resource usage using kubectl top
            top_nodes_data = await self._execute_kubectl_command(
                resource_group, cluster_name, "kubectl top nodes --no-headers"
            )
            
            if top_nodes_data and 'output' in top_nodes_data:
                kubectl_output = top_nodes_data['output']
                
                total_cpu_used = 0
                total_memory_used = 0
                node_count = 0
                
                for line in kubectl_output.strip().split('\n'):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 5:
                            node_name = parts[0]
                            cpu_used = parts[1]
                            cpu_percent = parts[2].rstrip('%')
                            memory_used = parts[3]
                            memory_percent = parts[4].rstrip('%')
                            
                            try:
                                cpu_pct = float(cpu_percent)
                                mem_pct = float(memory_percent)
                                
                                utilization["node_utilization"][node_name] = {
                                    "cpu_percent": cpu_pct,
                                    "memory_percent": mem_pct,
                                    "cpu_used": cpu_used,
                                    "memory_used": memory_used
                                }
                                
                                total_cpu_used += cpu_pct
                                total_memory_used += mem_pct
                                node_count += 1
                                
                            except ValueError:
                                continue
                
                if node_count > 0:
                    utilization["cpu_utilization"] = round(total_cpu_used / node_count, 2)
                    utilization["memory_utilization"] = round(total_memory_used / node_count, 2)
            
            # Get pod resource usage
            top_pods_data = await self._execute_kubectl_command(
                resource_group, cluster_name, "kubectl top pods --all-namespaces --no-headers"
            )
            
            pod_resource_usage = []
            if top_pods_data and 'output' in top_pods_data:
                kubectl_output = top_pods_data['output']
                
                for line in kubectl_output.strip().split('\n'):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 4:
                            namespace = parts[0]
                            pod_name = parts[1]
                            cpu_used = parts[2]
                            memory_used = parts[3]
                            
                            pod_resource_usage.append({
                                "namespace": namespace,
                                "pod_name": pod_name,
                                "cpu_used": cpu_used,
                                "memory_used": memory_used
                            })
            
            utilization["pod_resource_usage"] = pod_resource_usage
            
            return utilization
            
        except Exception as e:
            logger.error(f"Failed to get utilization metrics: {e}")
            return {"cpu_utilization": 0, "memory_utilization": 0, "node_utilization": {}}
    
    async def _get_namespace_metrics(self, resource_group: str, cluster_name: str) -> Dict[str, Any]:
        """Get comprehensive namespace-level metrics."""
        try:
            # Get namespaces
            ns_data = await self._execute_kubectl_command(
                resource_group, cluster_name, "kubectl get namespaces -o json"
            )
            
            if not ns_data or 'items' not in ns_data:
                return {"namespace_count": 0, "namespaces": []}
            
            namespaces = ns_data.get('items', [])
            
            namespace_details = []
            for ns in namespaces:
                ns_name = ns.get('metadata', {}).get('name', 'unknown')
                creation_time = ns.get('metadata', {}).get('creationTimestamp')
                labels = ns.get('metadata', {}).get('labels', {})
                status = ns.get('status', {}).get('phase', 'Unknown')
                
                namespace_details.append({
                    "name": ns_name,
                    "status": status,
                    "creation_time": creation_time,
                    "labels": labels
                })
            
            return {
                "namespace_count": len(namespaces),
                "namespaces": [ns['name'] for ns in namespace_details],
                "namespace_details": namespace_details
            }
            
        except Exception as e:
            logger.error(f"Failed to get namespace metrics: {e}")
            return {"namespace_count": 0, "namespaces": []}

    async def _get_service_metrics(self, resource_group: str, cluster_name: str) -> Dict[str, Any]:
        """Get service and deployment metrics."""
        try:
            # Get services
            services_data = await self._execute_kubectl_command(
                resource_group, cluster_name, "kubectl get services --all-namespaces -o json"
            )
            
            # Get deployments
            deployments_data = await self._execute_kubectl_command(
                resource_group, cluster_name, "kubectl get deployments --all-namespaces -o json"
            )
            
            service_metrics = {
                "service_count": 0,
                "deployment_count": 0,
                "services": [],
                "deployments": []
            }
            
            # Process services
            if services_data and 'items' in services_data:
                services = services_data.get('items', [])
                service_metrics["service_count"] = len(services)
                
                for svc in services:
                    service_metrics["services"].append({
                        "name": svc.get('metadata', {}).get('name'),
                        "namespace": svc.get('metadata', {}).get('namespace'),
                        "type": svc.get('spec', {}).get('type'),
                        "cluster_ip": svc.get('spec', {}).get('clusterIP'),
                        "external_ip": svc.get('status', {}).get('loadBalancer', {}).get('ingress', [{}])[0].get('ip') if svc.get('status', {}).get('loadBalancer', {}).get('ingress') else None
                    })
            
            # Process deployments
            if deployments_data and 'items' in deployments_data:
                deployments = deployments_data.get('items', [])
                service_metrics["deployment_count"] = len(deployments)
                
                for dep in deployments:
                    service_metrics["deployments"].append({
                        "name": dep.get('metadata', {}).get('name'),
                        "namespace": dep.get('metadata', {}).get('namespace'),
                        "replicas": dep.get('spec', {}).get('replicas', 0),
                        "ready_replicas": dep.get('status', {}).get('readyReplicas', 0),
                        "available_replicas": dep.get('status', {}).get('availableReplicas', 0),
                        "strategy": dep.get('spec', {}).get('strategy', {}).get('type')
                    })
            
            return service_metrics
            
        except Exception as e:
            logger.error(f"Failed to get service metrics: {e}")
            return {"service_count": 0, "deployment_count": 0, "services": [], "deployments": []}

class CostOptimizationAnalyzer:
    """Analyze real cost data and generate optimization recommendations."""
    
    def __init__(self):
        self.analyzer_cache = {}
    
    async def analyze_cluster_costs(self, cost_data: Dict, metrics_data: Dict, 
                                  cluster_config: Dict) -> Dict[str, Any]:
        """Perform comprehensive cost analysis with real data."""
        try:
            analysis = {
                "timestamp": datetime.now().isoformat(),
                "cluster_name": cluster_config.get("cluster_name", "unknown"),
                "cost_analysis": {},
                "efficiency_analysis": {},
                "optimization_opportunities": [],
                "recommendations": [],
                "potential_savings": 0,
                "risk_assessment": {},
                "implementation_plan": []
            }
            
            # Cost trend analysis
            if cost_data.get("success") and cost_data.get("data"):
                cost_analysis = await self._analyze_cost_trends(cost_data["data"])
                analysis["cost_analysis"] = cost_analysis
            
            # Resource efficiency analysis
            if metrics_data.get("success") and metrics_data.get("data"):
                efficiency_analysis = await self._analyze_resource_efficiency(metrics_data["data"])
                analysis["efficiency_analysis"] = efficiency_analysis
                
                # Generate optimization recommendations
                recommendations = await self._generate_recommendations(
                    cost_data.get("data", {}), 
                    metrics_data.get("data", {}),
                    cluster_config
                )
                analysis["recommendations"] = recommendations
                analysis["potential_savings"] = sum(r.get("potential_savings", 0) for r in recommendations)
            
            # Generate implementation plan
            implementation_plan = await self._generate_implementation_plan(analysis["recommendations"])
            analysis["implementation_plan"] = implementation_plan
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze cluster costs: {e}")
            return {"error": str(e)}
    
    async def _analyze_cost_trends(self, cost_data: Dict) -> Dict[str, Any]:
        """Analyze cost trends using real data."""
        try:
            daily_costs = cost_data.get("daily_costs", [])
            total_cost = cost_data.get("total_cost", 0)
            service_breakdown = cost_data.get("service_breakdown", {})
            
            if not daily_costs:
                return {"trend": "insufficient_data", "total_cost": total_cost}
            
            # Calculate trend
            costs = [item["cost"] for item in daily_costs]
            dates = [item["date"] for item in daily_costs]
            
            if len(costs) > 1:
                # Linear trend calculation
                x = list(range(len(costs)))
                trend_slope = np.polyfit(x, costs, 1)[0]
                
                trend_direction = "increasing" if trend_slope > 0.1 else "decreasing" if trend_slope < -0.1 else "stable"
                trend_magnitude = abs(trend_slope)
            else:
                trend_direction = "stable"
                trend_magnitude = 0
            
            # Cost statistics
            avg_cost = np.mean(costs) if costs else 0
            max_cost = max(costs) if costs else 0
            min_cost = min(costs) if costs else 0
            cost_variance = np.var(costs) if len(costs) > 1 else 0
            
            # Identify cost spikes
            cost_spikes = []
            if len(costs) > 1:
                threshold = avg_cost * 1.5  # 50% above average
                for i, cost in enumerate(costs):
                    if cost > threshold:
                        cost_spikes.append({
                            "date": dates[i],
                            "cost": cost,
                            "spike_percentage": round(((cost - avg_cost) / avg_cost) * 100, 1)
                        })
            
            return {
                "trend_direction": trend_direction,
                "trend_magnitude": round(trend_magnitude, 2),
                "total_cost": total_cost,
                "average_daily_cost": round(avg_cost, 2),
                "max_daily_cost": round(max_cost, 2),
                "min_daily_cost": round(min_cost, 2),
                "cost_variance": round(cost_variance, 2),
                "cost_stability": "stable" if cost_variance < avg_cost * 0.1 else "volatile",
                "daily_costs": daily_costs,
                "service_breakdown": service_breakdown,
                "cost_spikes": cost_spikes,
                "top_services": sorted(service_breakdown.items(), key=lambda x: x[1], reverse=True)[:5]
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze cost trends: {e}")
            return {"error": str(e), "total_cost": 0}
    
    async def _analyze_resource_efficiency(self, metrics_data: Dict) -> Dict[str, Any]:
        """Analyze resource utilization efficiency with real metrics."""
        try:
            cpu_utilization = metrics_data.get("cpu_utilization", 0)
            memory_utilization = metrics_data.get("memory_utilization", 0)
            node_count = metrics_data.get("node_count", 0)
            pod_count = metrics_data.get("pod_count", 0)
            namespace_count = metrics_data.get("namespace_count", 0)
            
            # Calculate efficiency scores
            cpu_efficiency = self._calculate_efficiency_score(cpu_utilization)
            memory_efficiency = self._calculate_efficiency_score(memory_utilization)
            overall_efficiency = (cpu_efficiency + memory_efficiency) / 2
            
            # Resource density calculations
            pod_density = pod_count / max(node_count, 1)
            namespace_density = namespace_count / max(node_count, 1)
            
            # Identify inefficiencies
            inefficiencies = []
            recommendations = []
            
            if cpu_utilization < 30:
                inefficiencies.append("low_cpu_utilization")
                recommendations.append("Consider reducing node sizes or count")
            if memory_utilization < 30:
                inefficiencies.append("low_memory_utilization")
                recommendations.append("Review memory requests and limits")
            if pod_density < 10:
                inefficiencies.append("low_pod_density")
                recommendations.append("Optimize pod placement and resource requests")
            if cpu_utilization > 85:
                inefficiencies.append("high_cpu_utilization")
                recommendations.append("Consider adding more nodes or optimizing workloads")
            if memory_utilization > 85:
                inefficiencies.append("high_memory_utilization")
                recommendations.append("Consider adding more memory or optimizing applications")
            
            # Node utilization analysis
            node_utilization = metrics_data.get("node_utilization", {})
            unbalanced_nodes = []
            for node_name, util in node_utilization.items():
                cpu_pct = util.get("cpu_percent", 0)
                mem_pct = util.get("memory_percent", 0)
                if abs(cpu_pct - memory_utilization) > 30 or abs(mem_pct - memory_utilization) > 30:
                    unbalanced_nodes.append(node_name)
            
            return {
                "cpu_utilization": cpu_utilization,
                "memory_utilization": memory_utilization,
                "cpu_efficiency_score": cpu_efficiency,
                "memory_efficiency_score": memory_efficiency,
                "overall_efficiency_score": round(overall_efficiency, 1),
                "node_count": node_count,
                "pod_count": pod_count,
                "namespace_count": namespace_count,
                "pod_density": round(pod_density, 1),
                "namespace_density": round(namespace_density, 1),
                "inefficiencies": inefficiencies,
                "recommendations": recommendations,
                "unbalanced_nodes": unbalanced_nodes,
                "optimization_potential": "high" if overall_efficiency < 60 else "medium" if overall_efficiency < 80 else "low"
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze resource efficiency: {e}")
            return {"error": str(e)}
    
    def _calculate_efficiency_score(self, utilization: float) -> float:
        """Calculate efficiency score based on utilization (optimal range: 60-80%)."""
        if 60 <= utilization <= 80:
            return 100.0  # Optimal range
        elif utilization < 60:
            return max(0, 100 - (60 - utilization) * 1.5)  # Penalty for underutilization
        else:
            return max(0, 100 - (utilization - 80) * 2)  # Higher penalty for overutilization
    
    async def _generate_recommendations(self, cost_data: Dict, metrics_data: Dict, 
                                      cluster_config: Dict) -> List[Dict[str, Any]]:
        """Generate specific optimization recommendations based on real data."""
        recommendations = []
        
        try:
            cpu_utilization = metrics_data.get("cpu_utilization", 0)
            memory_utilization = metrics_data.get("memory_utilization", 0)
            node_count = metrics_data.get("node_count", 1)
            pod_count = metrics_data.get("pod_count", 0)
            avg_daily_cost = cost_data.get("average_daily_cost", 0)
            total_cost = cost_data.get("total_cost", 0)
            service_breakdown = cost_data.get("service_breakdown", {})
            
            # Right-sizing recommendations based on actual utilization
            if cpu_utilization < 40 and memory_utilization < 40:
                potential_savings = total_cost * 0.25  # 25% savings potential
                recommendations.append({
                    "id": str(uuid.uuid4()),
                    "title": "Right-size Overprovisioned Node Pools",
                    "description": f"Current utilization is very low (CPU: {cpu_utilization}%, Memory: {memory_utilization}%). Significant cost savings possible through right-sizing.",
                    "category": "Infrastructure Optimization",
                    "priority": "High",
                    "potential_savings": round(potential_savings, 2),
                    "implementation_effort": "Medium",
                    "risk_level": "Low",
                    "confidence": 95,
                    "technical_details": {
                        "current_cpu_utilization": cpu_utilization,
                        "current_memory_utilization": memory_utilization,
                        "current_node_count": node_count,
                        "recommended_action": "reduce_node_size_or_count",
                        "estimated_reduction": "25-35%"
                    },
                    "implementation_steps": [
                        "Analyze historical usage patterns over 2-4 weeks",
                        "Test with smaller instance types in dev environment",
                        "Create new node pool with optimized instance sizes",
                        "Gradually migrate workloads with rolling deployment",
                        "Monitor performance metrics during migration",
                        "Remove old oversized nodes after validation"
                    ]
                })
            
            # Auto-scaling recommendations
            potential_autoscaling_savings = total_cost * 0.15  # 15% savings from auto-scaling
            recommendations.append({
                "id": str(uuid.uuid4()),
                "title": "Implement Intelligent Auto-scaling",
                "description": "Enable cluster autoscaler and HPA to automatically adjust resources based on actual demand patterns.",
                "category": "Automation",
                "priority": "High",
                "potential_savings": round(potential_autoscaling_savings, 2),
                "implementation_effort": "Low",
                "risk_level": "Low",
                "confidence": 90,
                "technical_details": {
                    "current_nodes": node_count,
                    "recommended_min_nodes": max(1, node_count // 3),
                    "recommended_max_nodes": node_count + 3,
                    "features": ["cluster_autoscaler", "horizontal_pod_autoscaler", "vertical_pod_autoscaler"]
                },
                "implementation_steps": [
                    "Enable cluster autoscaler on node pools",
                    "Configure appropriate min/max node counts",
                    "Implement Horizontal Pod Autoscaler (HPA) for deployments",
                    "Set up Vertical Pod Autoscaler (VPA) for resource recommendations",
                    "Configure monitoring and alerting for scaling events",
                    "Fine-tune scaling policies based on workload patterns"
                ]
            })
            
            # Spot instances recommendation for significant cost savings
            if total_cost > 500:  # For clusters with substantial costs
                potential_spot_savings = total_cost * 0.5  # 50% savings with spot instances
                recommendations.append({
                    "id": str(uuid.uuid4()),
                    "title": "Implement Spot Instance Strategy",
                    "description": "Deploy spot instances for non-critical workloads to achieve significant cost reductions (up to 70%).",
                    "category": "Cost Optimization",
                    "priority": "Medium",
                    "potential_savings": round(potential_spot_savings, 2),
                    "implementation_effort": "High",
                    "risk_level": "Medium",
                    "confidence": 85,
                    "technical_details": {
                        "suitable_workloads": ["development", "testing", "batch_processing", "stateless_applications"],
                        "estimated_cost_reduction": "50-70%",
                        "interruption_handling": "required",
                        "recommended_ratio": "70% spot, 30% on-demand"
                    },
                    "implementation_steps": [
                        "Identify fault-tolerant and stateless workloads",
                        "Create dedicated spot instance node pools",
                        "Implement pod disruption budgets",
                        "Configure node affinity and pod scheduling",
                        "Set up monitoring for spot instance interruptions",
                        "Implement graceful handling of interruptions"
                    ]
                })
            
            # Resource requests optimization based on pod density
            pod_density = pod_count / max(node_count, 1)
            if pod_density < 15:
                potential_resource_savings = total_cost * 0.12  # 12% savings
                recommendations.append({
                    "id": str(uuid.uuid4()),
                    "title": "Optimize Resource Requests and Limits",
                    "description": f"Low pod density ({pod_density:.1f} pods/node) indicates oversized resource requests. Optimize for better resource utilization.",
                    "category": "Resource Management",
                    "priority": "Medium",
                    "potential_savings": round(potential_resource_savings, 2),
                    "implementation_effort": "Medium",
                    "risk_level": "Medium",
                    "confidence": 80,
                    "technical_details": {
                        "current_pod_density": round(pod_density, 1),
                        "target_pod_density": "20-30",
                        "action": "optimize_resource_requests",
                        "tools": ["VPA", "resource_analysis", "load_testing"]
                    },
                    "implementation_steps": [
                        "Deploy Vertical Pod Autoscaler (VPA) in recommendation mode",
                        "Analyze current resource requests vs actual usage",
                        "Identify over-provisioned applications",
                        "Implement right-sized resource specifications",
                        "Load test applications with new resource limits",
                        "Monitor application performance and adjust as needed"
                    ]
                })
            
            # Storage optimization based on service breakdown
            storage_costs = sum(cost for service, cost in service_breakdown.items() 
                             if 'storage' in service.lower() or 'disk' in service.lower())
            if storage_costs > total_cost * 0.2:  # Storage costs > 20% of total
                potential_storage_savings = storage_costs * 0.3  # 30% storage savings
                recommendations.append({
                    "id": str(uuid.uuid4()),
                    "title": "Optimize Storage Configuration",
                    "description": f"Storage costs are ${storage_costs:.2f} ({(storage_costs/total_cost)*100:.1f}% of total). Optimize storage tiers and configurations.",
                    "category": "Storage Optimization",
                    "priority": "Medium",
                    "potential_savings": round(potential_storage_savings, 2),
                    "implementation_effort": "Medium",
                    "risk_level": "Low",
                    "confidence": 85,
                    "technical_details": {
                        "current_storage_cost": round(storage_costs, 2),
                        "storage_percentage": round((storage_costs/total_cost)*100, 1),
                        "optimization_areas": ["storage_classes", "persistent_volumes", "backup_retention"]
                    },
                    "implementation_steps": [
                        "Audit current storage classes and usage patterns",
                        "Implement lifecycle policies for storage tiers",
                        "Optimize persistent volume configurations",
                        "Review and optimize backup retention policies",
                        "Consider using Azure managed disks efficiently",
                        "Monitor storage usage and costs regularly"
                    ]
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return []
    
    async def _generate_implementation_plan(self, recommendations: List[Dict]) -> List[Dict[str, Any]]:
        """Generate phased implementation plan based on real analysis."""
        if not recommendations:
            return []
        
        # Sort recommendations by priority, confidence, and potential savings
        priority_order = {"High": 3, "Medium": 2, "Low": 1}
        sorted_recs = sorted(
            recommendations,
            key=lambda x: (
                priority_order.get(x.get("priority", "Low"), 1),
                x.get("confidence", 0),
                x.get("potential_savings", 0)
            ),
            reverse=True
        )
        
        phases = [
            {
                "phase": 1,
                "title": "Quick Wins & Low-Risk Optimizations",
                "duration": "1-2 weeks",
                "description": "Implement high-confidence, low-risk optimizations with immediate impact",
                "recommendations": [],
                "estimated_savings": 0,
                "risk_level": "Low"
            },
            {
                "phase": 2,
                "title": "Infrastructure & Automation",
                "duration": "3-5 weeks", 
                "description": "Optimize cluster infrastructure and implement automated scaling",
                "recommendations": [],
                "estimated_savings": 0,
                "risk_level": "Medium"
            },
            {
                "phase": 3,
                "title": "Advanced Cost Optimization",
                "duration": "6-8 weeks",
                "description": "Implement advanced features like spot instances and advanced monitoring",
                "recommendations": [],
                "estimated_savings": 0,
                "risk_level": "Medium"
            }
        ]
        
        # Distribute recommendations across phases based on risk and complexity
        for rec in sorted_recs:
            risk_level = rec.get("risk_level", "Medium")
            effort = rec.get("implementation_effort", "Medium")
            
            # Phase 1: Low risk, any effort
            if risk_level == "Low":
                phase_idx = 0
            # Phase 2: Medium risk, low-medium effort
            elif risk_level == "Medium" and effort in ["Low", "Medium"]:
                phase_idx = 1
            # Phase 3: High risk or high effort
            else:
                phase_idx = 2
            
            phases[phase_idx]["recommendations"].append(rec)
            phases[phase_idx]["estimated_savings"] += rec.get("potential_savings", 0)
        
        # Round estimated savings
        for phase in phases:
            phase["estimated_savings"] = round(phase["estimated_savings"], 2)
        
        return phases

class RealTimeAKSPlatform:
    """Main platform application with real Azure integration."""
    
    def __init__(self):
        self.app = FastAPI(title="Real-Time AKS Cost Intelligence Platform")
        self.data_collector = AzureDataCollector()
        self.analyzer = CostOptimizationAnalyzer()
        self.active_connections = []
        
        self._setup_middleware()
        self._setup_static_files()
        self._setup_routes()
    
    def _setup_static_files(self):
        """Setup static file serving for frontend assets."""
        # Serve the current directory as static files for frontend assets
        # This allows serving HTML, JS, CSS files
        try:
            # Mount static files only if we're in a directory with frontend files
            if os.path.exists("templates/next_gen_dashboard.html"):
                self.app.mount("/static", StaticFiles(directory="."), name="static")
                logger.info("✅ Static file serving enabled for frontend assets")
            else:
                logger.warning("⚠️ Frontend files not found in current directory")
        except Exception as e:
            logger.warning(f"⚠️ Could not setup static file serving: {e}")
    
    def _setup_middleware(self):
        """Setup CORS middleware for cross-origin requests."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production, specify exact origins
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Setup API routes and frontend serving."""
        
        @self.app.get("/", response_class=RedirectResponse)
        async def root():
            """Redirect to dashboard."""
            return RedirectResponse(url="/dashboard", status_code=302)
        
        @self.app.get("/dashboard", response_class=HTMLResponse)
        async def serve_dashboard():
            """Serve the main dashboard."""
            try:
                # Check if the HTML file exists
                html_file = "templates/next_gen_dashboard.html"
                if not os.path.exists(html_file):
                    return HTMLResponse(
                        content=self._get_file_not_found_html(),
                        status_code=404
                    )
                
                # Read and serve the HTML file
                with open(html_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                return HTMLResponse(content=html_content)
                
            except Exception as e:
                logger.error(f"Error serving dashboard: {e}")
                return HTMLResponse(
                    content=self._get_error_html(str(e)),
                    status_code=500
                )
        
        @self.app.get("/static/js/dashboard.js")
        async def serve_dashboard_js():
            """Serve the dashboard JavaScript file."""
            try:
                js_file = "static/js/dashboard.js"
                if not os.path.exists(js_file):
                    raise HTTPException(status_code=404, detail="JavaScript file not found")
                
                return FileResponse(js_file, media_type="application/javascript")
                
            except Exception as e:
                logger.error(f"Error serving JavaScript: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/favicon.ico")
        async def favicon():
            """Handle favicon requests to avoid 404 errors."""
            # Return a simple response or serve an actual favicon if you have one
            raise HTTPException(status_code=204, detail="No favicon")
        
        @self.app.get("/api/info")
        async def api_info():
            """API information endpoint."""
            return {
                "message": "Real-Time AKS Cost Intelligence Platform API",
                "version": "1.0.0",
                "status": "running",
                "frontend_available": os.path.exists("templates/next_gen_dashboard.html"),
                "endpoints": {
                    "dashboard": "/dashboard",
                    "analyze": "/api/analyze",
                    "metrics": "/api/metrics/{resource_group}/{cluster_name}",
                    "costs": "/api/costs/{resource_group}/{cluster_name}",
                    "health": "/api/health",
                    "websocket": "/ws/analytics/{cluster_id}"
                }
            }
        
        @self.app.post("/api/analyze")
        async def analyze_cluster(request_data: dict):
            """Analyze AKS cluster with real Azure data."""
            try:
                subscription_id = request_data.get("subscription_id")
                resource_group = request_data.get("resource_group") 
                cluster_name = request_data.get("cluster_name")
                analysis_period = int(request_data.get("analysis_period", 30))
                
                if not all([subscription_id, resource_group, cluster_name]):
                    raise HTTPException(status_code=400, detail="Missing required parameters")
                
                logger.info(f"Starting comprehensive analysis for {cluster_name}")
                
                # Set Azure subscription context
                subprocess.run(f"az account set --subscription {subscription_id}", 
                             shell=True, check=True, capture_output=True)
                
                # Collect real cost data
                cost_data = await self.data_collector.get_aks_cost_data(
                    resource_group, cluster_name, analysis_period
                )
                
                # Collect real metrics data
                metrics_data = await self.data_collector.get_aks_metrics(
                    resource_group, cluster_name
                )
                
                # Perform comprehensive analysis
                analysis_result = await self.analyzer.analyze_cluster_costs(
                    cost_data, metrics_data, request_data
                )
                
                return {
                    "success": True,
                    "analysis": analysis_result,
                    "cost_data": cost_data,
                    "metrics_data": metrics_data,
                    "timestamp": datetime.now().isoformat()
                }
                
            except subprocess.CalledProcessError as e:
                logger.error(f"Azure CLI command failed: {e}")
                raise HTTPException(status_code=500, detail=f"Azure CLI error: {e.stderr}")
            except Exception as e:
                logger.error(f"Analysis failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/metrics/{resource_group}/{cluster_name}")
        async def get_real_time_metrics(resource_group: str, cluster_name: str):
            """Get real-time metrics for a specific cluster."""
            try:
                metrics_data = await self.data_collector.get_aks_metrics(
                    resource_group, cluster_name
                )
                return metrics_data
            except Exception as e:
                logger.error(f"Failed to get real-time metrics: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/costs/{resource_group}/{cluster_name}")
        async def get_cost_data(resource_group: str, cluster_name: str, days: int = 30):
            """Get cost data for a specific cluster."""
            try:
                cost_data = await self.data_collector.get_aks_cost_data(
                    resource_group, cluster_name, days
                )
                return cost_data
            except Exception as e:
                logger.error(f"Failed to get cost data: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.websocket("/ws/analytics/{cluster_id}")
        async def websocket_analytics(websocket: WebSocket, cluster_id: str):
            """WebSocket endpoint for real-time analytics."""
            await websocket.accept()
            self.active_connections.append(websocket)
            
            try:
                while True:
                    # Send periodic updates every 60 seconds
                    await asyncio.sleep(60)
                    
                    update_data = {
                        "type": "metrics_update",
                        "timestamp": datetime.now().isoformat(),
                        "cluster_id": cluster_id,
                        "status": "connected"
                    }
                    
                    await websocket.send_text(json.dumps(update_data))
                    
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
        
        @self.app.get("/api/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy", 
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "azure_cli_available": self._check_azure_cli(),
                "frontend_files_available": {
                    "html": os.path.exists("templates/next_gen_dashboard.html"),
                    "js": os.path.exists("static/js/dashboard.js")
                }
            }
    
    def _check_azure_cli(self) -> bool:
        """Check if Azure CLI is available and authenticated."""
        try:
            result = subprocess.run("az account show", shell=True, capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False
    
    def _get_file_not_found_html(self) -> str:
        """Return HTML for file not found error."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>AKS Cost Intelligence - File Not Found</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #1a1a2e; color: white; }
                .container { max-width: 600px; margin: 0 auto; text-align: center; }
                .error { color: #ef4444; }
                .info { color: #3b82f6; margin-top: 20px; }
                .code { background: #333; padding: 10px; border-radius: 5px; margin: 10px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔧 AKS Cost Intelligence Platform</h1>
                <div class="error">
                    <h2>❌ Dashboard Files Not Found</h2>
                    <p>The frontend files are missing from the current directory.</p>
                </div>
                <div class="info">
                    <h3>Required Files:</h3>
                    <ul style="text-align: left;">
                        <li><code>templates/next_gen_dashboard.html</code></li>
                        <li><code>static/js/dashboard.js</code></li>
                    </ul>
                    
                    <h3>🚀 Quick Fix:</h3>
                    <p>Make sure these files are in the same directory as your Python script:</p>
                    <div class="code">
                        enhanced_aks_platform.py<br>
                        templates/next_gen_dashboard.html<br>
                        static/js/dashboard.js
                    </div>
                    
                    <h3>📊 API Endpoints Still Available:</h3>
                    <p><a href="/api/info" style="color: #10b981;">/api/info</a> - API Information</p>
                    <p><a href="/api/health" style="color: #10b981;">/api/health</a> - Health Check</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_error_html(self, error_message: str) -> str:
        """Return HTML for general errors."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AKS Cost Intelligence - Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #1a1a2e; color: white; }}
                .container {{ max-width: 600px; margin: 0 auto; text-align: center; }}
                .error {{ color: #ef4444; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔧 AKS Cost Intelligence Platform</h1>
                <div class="error">
                    <h2>❌ Error Loading Dashboard</h2>
                    <p>{error_message}</p>
                    <p><a href="/api/info" style="color: #10b981;">Check API Status</a></p>
                </div>
            </div>
        </body>
        </html>
        """

    async def run_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the platform server."""
        logger.info(f"Starting Real-Time AKS Cost Intelligence Platform on {host}:{port}")
        
        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            log_level="info",
            reload=False
        )
        
        server = uvicorn.Server(config)
        await server.serve()

if __name__ == "__main__":
    async def main():
        try:
            # Check Azure CLI availability
            result = subprocess.run("az --version", shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("Azure CLI not found. Please install Azure CLI and ensure it's in your PATH.")
                return
                
            # Check Azure authentication
            result = subprocess.run("az account show", shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("Azure CLI not authenticated. Please run 'az login' first.")
                return
                
            logger.info("✅ Azure CLI is available and authenticated")
            
            platform = RealTimeAKSPlatform()
            logger.info("🚀 Starting AKS Cost Intelligence Platform...")
            logger.info("📊 Dashboard available at: http://localhost:8000/dashboard")
            logger.info("🔧 API endpoints available at: http://localhost:8000/api/")
            logger.info("🌐 Direct access: http://localhost:8000 (auto-redirects to dashboard)")
            
            await platform.run_server()
            
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
    
    asyncio.run(main())