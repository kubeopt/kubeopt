#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & KubeVista
Project: AKS Cost Optimizer

Centralized Kubernetes Data Cache Manager
- Runs ALL kubectl commands in parallel (no static data, always fresh)
- Provides query interface for all components
- Eliminates duplicate API calls and improves performance from 25min to 2-3min
"""

import concurrent.futures
import json
import logging
import subprocess
import time
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)

class KubernetesDataCache:
    """Centralized cache for all Kubernetes cluster data - always fresh, no static caching"""
    
    def __init__(self, cluster_name: str, resource_group: str, subscription_id: str, auto_fetch: bool = True):
        self.cluster_name = cluster_name
        self.resource_group = resource_group  
        self.subscription_id = subscription_id
        self.data = {}  # Fresh data storage (no TTL, no persistence)
        
        # PROACTIVE: Fetch data immediately when cache is created
        if auto_fetch:
            logger.info(f"🚀 {self.cluster_name}: Auto-fetching data on cache creation...")
            self.fetch_all_data()
        
    def get_all_kubectl_commands(self) -> Dict[str, str]:
        """
        COMPLETE kubectl commands from ALL components - SINGLE SOURCE OF TRUTH
        Every kubectl command in the entire application should be listed here
        """
        return {
            # === CORE CLUSTER DATA ===
            "version": "kubectl version -o json",  # JSON format for proper parsing
            "nodes": "kubectl get nodes -o json",
            "nodes_text": "kubectl get nodes",
            "namespaces": "kubectl get namespaces -o json",
            
            # === WORKLOAD DATA (OPTIMIZED CUSTOM COLUMNS) ===  
            "pod_resources": '''kubectl get pods --all-namespaces -o custom-columns="NAMESPACE:.metadata.namespace,NAME:.metadata.name,CPU_REQ:.spec.containers[*].resources.requests.cpu,MEM_REQ:.spec.containers[*].resources.requests.memory,NODE:.spec.nodeName,CREATED:.metadata.creationTimestamp,STATUS:.status.phase" --field-selector=status.phase=Running''',
            "replicaset_timestamps": '''kubectl get replicasets --all-namespaces -o custom-columns="NAMESPACE:.metadata.namespace,NAME:.metadata.name,CREATED:.metadata.creationTimestamp,READY:.status.readyReplicas,AVAILABLE:.status.availableReplicas"''',
            "deployment_info": '''kubectl get deployments --all-namespaces -o custom-columns="NAMESPACE:.metadata.namespace,NAME:.metadata.name,READY:.status.readyReplicas,AVAILABLE:.status.availableReplicas,GENERATION:.metadata.generation"''',
            "pod_timestamps": '''kubectl get pods --all-namespaces -o custom-columns="NAMESPACE:.metadata.namespace,NAME:.metadata.name,CREATED:.metadata.creationTimestamp,STATUS:.status.phase,NODE:.spec.nodeName"''',
            
            # === RESOURCE UTILIZATION ===
            "node_usage": "kubectl top nodes --no-headers",
            "node_usage_headers": "kubectl top nodes", 
            "pod_usage": "kubectl top pods --all-namespaces --no-headers",
            "pod_usage_headers": "kubectl top pods",
            "cluster_utilization": "kubectl top nodes --no-headers | awk '{gsub(/\\%/, \"\", $3); gsub(/\\%/, \"\", $5); cpu+=$3; mem+=$5; count++} END {if(count>0) printf \"CPU:%.1f%%,Memory:%.1f%%\\n\", cpu/count, mem/count}'",
            
            # === WORKLOAD DETAILS ===
            "pods_running": "kubectl get pods --all-namespaces --field-selector=status.phase=Running",
            "pods_basic": "kubectl get pods --all-namespaces --no-headers --field-selector=status.phase=Running",
            "pods_all": "kubectl get pods --all-namespaces",
            "deployments": "kubectl get deployments --all-namespaces -o json",
            "deployments_text": "kubectl get deployments --all-namespaces",
            "replicasets": "kubectl get replicasets --all-namespaces -o json",
            "statefulsets": "kubectl get statefulsets --all-namespaces -o json",
            
            # === INFRASTRUCTURE ===
            "services": "kubectl get services --all-namespaces -o json", 
            "services_text": "kubectl get services --all-namespaces",
            "services_loadbalancer": "kubectl get services --all-namespaces --field-selector spec.type=LoadBalancer",
            "pvcs": "kubectl get pvc --all-namespaces -o json",
            "pvc_text": "kubectl get pvc --all-namespaces",
            "storage_classes": "kubectl get storageclass -o json",
            "storage_classes_text": "kubectl get storageclass",
            "volume_snapshot_classes": "kubectl get volumesnapshotclass",
            
            # === SECURITY & RBAC ===
            "network_policies": "kubectl get networkpolicies --all-namespaces -o json",
            "service_accounts": "kubectl get serviceaccounts --all-namespaces -o json",
            "service_accounts_default": "kubectl get serviceaccounts -n default",
            "cluster_roles": "kubectl get clusterroles -o json",
            "role_bindings": "kubectl get rolebindings --all-namespaces -o json",
            "roles_default": "kubectl get roles -n default", 
            "cluster_role_bindings": "kubectl get clusterrolebindings -o json",
            "resource_quotas": "kubectl get resourcequotas --all-namespaces -o json",
            "resource_quota_default": "kubectl get resourcequota -n default",
            "limit_ranges": "kubectl get limitranges --all-namespaces -o json",
            "secrets": "kubectl get secrets --all-namespaces -o json",
            "pod_security_policies": "kubectl get podsecuritypolicies -o json",
            
            # === SPECIALIZED RESOURCES ===
            "namespace_cost_monitoring": "kubectl get namespace cost-monitoring",
            "namespace_security_optimized": "kubectl get namespace security-optimized",
            "networkpolicy_comprehensive": "kubectl get networkpolicy comprehensive-network-security -n default",
            "storageclass_cost_optimized": "kubectl get storageclass cost-optimized-ssd",
            
            # === SYSTEM COMPONENTS ===
            "deployment_cluster_autoscaler": "kubectl get deployment cluster-autoscaler -n kube-system",
            "deployment_metrics_server": "kubectl get deployment metrics-server -n kube-system",
            "configmap_pv_lifecycle": "kubectl get configmap pv-lifecycle-policy -n kube-system",
            
            # === EVENTS & CONFIG ===
            "events": "kubectl get events --all-namespaces --sort-by='.lastTimestamp' --limit=200 -o json",
            "configmaps": "kubectl get configmaps --all-namespaces -o json",
            "applications": "kubectl get applications --all-namespaces -o json",  # ArgoCD
            "api_resources": "kubectl api-resources --output=wide",  # For config fetcher
            "api_versions": "kubectl api-versions",  # For config fetcher
            "cluster_info": "kubectl cluster-info",  # For ML framework health check
            
            # === HPA & AUTOSCALING ===
            "hpa": "kubectl get hpa --all-namespaces -o json",
            "hpa_text": "kubectl get hpa --all-namespaces",
            "hpa_no_headers": "kubectl get hpa --all-namespaces --no-headers",
            "hpa_basic": "kubectl get hpa",
            "hpa_custom": '''kubectl get hpa --all-namespaces -o custom-columns="NAMESPACE:.metadata.namespace,NAME:.metadata.name,REFERENCE:.spec.scaleTargetRef.name,METRICS:.spec.metrics[*].resource.name,MIN:.spec.minReplicas,MAX:.spec.maxReplicas"''',
            "hpa_high_cpu": '''kubectl get hpa --all-namespaces -o custom-columns="NAMESPACE:.metadata.namespace,NAME:.metadata.name,CPU_CURRENT:.status.currentMetrics[0].resource.current.averageUtilization,CPU_TARGET:.spec.metrics[0].resource.target.averageUtilization"''',
            
            # === JSON FALLBACKS (for backward compatibility) ===
            "pods": "kubectl get pods --all-namespaces -o json"  # Get ALL pods, not just running
        }
    
    def _execute_kubectl_command(self, cmd: str, timeout: int = None) -> Optional[str]:
        """Execute single kubectl command via az aks command invoke"""
        try:
            # Smart timeout based on command type
            if timeout is None:
                if "kubectl version" in cmd:
                    timeout = 30   # Version commands should be quick
                elif "kubectl top" in cmd:
                    timeout = 45  # Metrics server commands are faster but can fail
                elif "get namespaces" in cmd or "get nodes" in cmd:
                    timeout = 120  # Basic cluster info - allow more time
                elif "get pods --all-namespaces" in cmd:
                    timeout = 180  # Large clusters may have many pods
                elif "get services --all-namespaces" in cmd or "get pvc --all-namespaces" in cmd:
                    timeout = 150  # Service/storage queries can be slow
                elif "-o json" in cmd and ("events" in cmd or "secrets" in cmd):
                    timeout = 90   # JSON queries with potential large output
                else:
                    timeout = 75   # Default increased from 60 to 75
                    
                logger.info(f"🕐 {self.cluster_name}: Using {timeout}s timeout for: {cmd[:50]}...")
            
            cmd_start = time.time()
            full_cmd = [
                'az', 'aks', 'command', 'invoke',
                '--resource-group', self.resource_group,
                '--name', self.cluster_name,
                '--subscription', self.subscription_id,
                '--command', cmd
            ]
            
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            
            cmd_duration = time.time() - cmd_start
            
            if result.returncode == 0 and result.stdout:
                logger.info(f"✅ {self.cluster_name}: Command succeeded in {cmd_duration:.1f}s: {cmd[:50]}...")
                try:
                    response = json.loads(result.stdout)
                    # Extract the actual kubectl output from Azure CLI response
                    if 'logs' in response and response['logs']:
                        return response['logs']
                    else:
                        logger.warning(f"⚠️ {self.cluster_name}: No 'logs' in Azure CLI response for: {cmd[:50]}...")
                        return None
                except json.JSONDecodeError:
                    # If not JSON, try to extract kubectl output from raw text
                    return self._extract_kubectl_output_from_azure_text(result.stdout, cmd)
            else:
                # Special handling for metrics server commands
                if "kubectl top" in cmd:
                    logger.warning(f"⚠️ {self.cluster_name}: kubectl top failed (metrics server may be unavailable): {cmd[:60]}... (exit code: {result.returncode})")
                    if result.stderr and "metrics not available" in result.stderr.lower():
                        logger.info(f"📊 {self.cluster_name}: Metrics server not ready, will use resource requests as fallback")
                # Special handling for HPA commands
                elif "kubectl get hpa" in cmd:
                    error_msg = result.stderr.strip() if result.stderr else "No error message"
                    stdout_msg = result.stdout.strip() if result.stdout else "No stdout"
                    
                    # ENHANCED DEBUGGING for HPA failures
                    logger.warning(f"⚠️ {self.cluster_name}: HPA command failed: {cmd[:60]}... (exit code: {result.returncode})")
                    logger.info(f"🔍 DEBUGGING HPA ERROR: Full stderr: {error_msg}")
                    logger.info(f"🔍 DEBUGGING HPA ERROR: Full stdout: {stdout_msg}")
                    logger.info(f"🔍 DEBUGGING HPA ERROR: Used subscription: {self.subscription_id}")
                    
                    if "service unavailable" in error_msg.lower() or "the server doesn't have a resource type" in error_msg.lower():
                        logger.debug(f"📈 {self.cluster_name}: HPA API unavailable (cluster may not have HPA enabled): {cmd[:60]}...")
                    else:
                        logger.error(f"❌ {self.cluster_name}: Unexpected HPA command failure - this needs investigation")
                else:
                    # Handle different types of kubectl failures gracefully
                    error_msg = result.stderr.strip() if result.stderr else "No error message"
                    
                    # Check if it's a "resource not found" issue (normal behavior)
                    not_found_keywords = ["no resources found", "not found", "doesn't have a resource type"]
                    is_not_found = any(keyword in error_msg.lower() for keyword in not_found_keywords)
                    
                    # Check if it's a permission/RBAC issue
                    permission_keywords = ["forbidden", "unauthorized", "permission denied", "cannot list", "cannot get"]
                    is_permission_error = any(keyword in error_msg.lower() for keyword in permission_keywords)
                    
                    if is_not_found:
                        logger.debug(f"📭 {self.cluster_name}: Resource not found for {cmd[:60]}... (normal for optional resources)")
                    elif is_permission_error:
                        logger.info(f"🔐 {self.cluster_name}: Permission denied for {cmd[:60]}... - {error_msg}")
                    else:
                        logger.warning(f"⚠️ {self.cluster_name}: kubectl failed in {cmd_duration:.1f}s: {cmd[:60]}... (exit code: {result.returncode})")
                        logger.warning(f"🔍 {self.cluster_name}: Error details: {error_msg}")
                return None
                
        except subprocess.TimeoutExpired:
            # For critical commands, try once more with extended timeout
            if any(critical in cmd for critical in ["get nodes", "get namespaces", "get pods"]):
                logger.warning(f"⚠️ {self.cluster_name}: kubectl timeout, retrying with extended timeout: {cmd[:60]}...")
                try:
                    extended_timeout = timeout + 60  # Add 60 seconds
                    result = subprocess.run(
                        full_cmd,
                        capture_output=True,
                        text=True,
                        timeout=extended_timeout,
                        check=False
                    )
                    if result.returncode == 0 and result.stdout:
                        logger.info(f"✅ {self.cluster_name}: Retry successful for: {cmd[:60]}...")
                        try:
                            response = json.loads(result.stdout)
                            return response.get('logs', '') if 'logs' in response else result.stdout
                        except json.JSONDecodeError:
                            return result.stdout
                except subprocess.TimeoutExpired:
                    logger.error(f"❌ {self.cluster_name}: Retry also timed out: {cmd[:60]}...")
                except Exception as retry_error:
                    logger.error(f"❌ {self.cluster_name}: Retry error: {retry_error}")
                    
            logger.warning(f"⚠️ {self.cluster_name}: kubectl timeout after {timeout}s: {cmd[:60]}...")
            return None
        except Exception as e:
            logger.error(f"❌ {self.cluster_name}: kubectl error: {cmd[:60]}... - {e}")
            return None
    
    def _extract_kubectl_output_from_azure_text(self, azure_output: str, cmd: str) -> Optional[str]:
        """Extract actual kubectl output from Azure CLI text response"""
        try:
            # Azure CLI text output typically has format:
            # command started at ..., finished at ... with exitcode=0
            # <actual kubectl output>
            
            lines = azure_output.strip().split('\n')
            
            # Skip the Azure CLI metadata lines (usually first line)
            kubectl_lines = []
            skip_metadata = True
            
            for line in lines:
                if skip_metadata:
                    # Skip lines that look like Azure CLI metadata
                    if ('command started at' in line or 
                        'finished at' in line or
                        'exitcode=' in line):
                        continue
                    else:
                        skip_metadata = False
                
                kubectl_lines.append(line)
            
            kubectl_output = '\n'.join(kubectl_lines).strip()
            
            if kubectl_output:
                logger.debug(f"✅ {self.cluster_name}: Extracted kubectl output ({len(kubectl_output)} chars) from Azure CLI response")
                return kubectl_output
            else:
                logger.warning(f"⚠️ {self.cluster_name}: No kubectl output found in Azure CLI response for: {cmd[:50]}...")
                return None
                
        except Exception as e:
            logger.error(f"❌ {self.cluster_name}: Failed to extract kubectl output from Azure CLI response: {e}")
            return None
    def fetch_all_data(self) -> Dict[str, Any]:
        """Fetch ALL kubernetes data in parallel with retry mechanism"""
        all_commands = self.get_all_kubectl_commands()
        
        logger.info(f"🚀 {self.cluster_name}: Fetching {len(all_commands)} kubectl commands in PARALLEL...")
        logger.debug(f"ℹ️ {self.cluster_name}: Note: Failed commands will be retried after initial batch completes")
        start_time = time.time()
        
        # First attempt - execute all commands in parallel
        results, failed_commands = self._execute_commands_batch(all_commands, attempt=1)
        
        # Retry failed commands if any (only after ALL commands complete)
        if failed_commands:
            logger.info(f"🔄 {self.cluster_name}: Retrying {len(failed_commands)} failed commands after batch completion...")
            retry_results, still_failed = self._execute_commands_batch(failed_commands, attempt=2)
            
            # Merge retry results
            results.update(retry_results)
            
            # Log final failures
            if still_failed:
                logger.warning(f"⚠️ {self.cluster_name}: {len(still_failed)} commands failed after retry: {list(still_failed.keys())}")
        
        return self._finalize_results(results, start_time)

    def _execute_commands_batch(self, commands: Dict[str, str], attempt: int) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """Execute a batch of commands and return results + failed commands"""
        results = {}
        failed_commands = {}
        
        # Use minimal workers to prevent overwhelming the AKS API server
        max_workers = 3  # Reduced from 6 to 3 - AKS API server can get overwhelmed with too many concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit commands with slight delay to be gentle on AKS API server
            future_to_key = {}
            for key, cmd in commands.items():
                future_to_key[executor.submit(self._execute_kubectl_command, cmd)] = key
                if attempt == 1:  # Only delay on first attempt
                    time.sleep(0.1)  # 100ms delay between submissions to prevent API server overload
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    output = future.result()
                    if output:
                        # Process output based on command type
                        if self._is_text_output(key):
                            results[key] = output.strip()
                            lines = len(output.strip().split('\n')) if output.strip() else 0
                            logger.debug(f"✅ {self.cluster_name}: {key} = {lines} lines (attempt {attempt})")
                        else:
                            # JSON output
                            try:
                                parsed = json.loads(output)
                                results[key] = parsed
                                item_count = len(parsed.get('items', [])) if isinstance(parsed, dict) and 'items' in parsed else 'N/A'
                                logger.debug(f"✅ {self.cluster_name}: {key} = {item_count} items (attempt {attempt})")
                            except json.JSONDecodeError:
                                # For JSON commands that return non-JSON (empty or error), use empty JSON structure
                                results[key] = {"items": []}
                                logger.debug(f"⚠️ {self.cluster_name}: {key} = invalid JSON, using empty structure (attempt {attempt})")
                    else:
                        # Empty result - add to failed for retry
                        if attempt == 1:
                            failed_commands[key] = commands[key]
                            logger.debug(f"🔄 {self.cluster_name}: {key} = no data, will retry")
                        else:
                            results[key] = {"items": []} if not self._is_text_output(key) else ""
                            logger.debug(f"⚠️ {self.cluster_name}: {key} = no data after retry")
                        
                except Exception as e:
                    if attempt == 1:
                        failed_commands[key] = commands[key]
                        logger.debug(f"🔄 {self.cluster_name}: {key} failed, will retry - {e}")
                    else:
                        results[key] = {"items": []} if not self._is_text_output(key) else ""
                        logger.error(f"❌ {self.cluster_name}: {key} failed after retry - {e}")
        
        return results, failed_commands

    def _finalize_results(self, results: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """Finalize and store results"""
        # Store results
        self.data = results
        
        duration = time.time() - start_time
        successful_commands = sum(1 for v in results.values() if v)
        total_commands = len(self.get_all_kubectl_commands())
        logger.info(f"⚡ {self.cluster_name}: Parallel fetch completed in {duration:.1f}s")
        logger.info(f"📊 {self.cluster_name}: {successful_commands}/{total_commands} commands successful")
        
        return results
    
    def _is_text_output(self, key: str) -> bool:
        """Check if command returns text output (not JSON)"""
        text_commands = {
            'node_usage', 'pod_usage', 'pod_resources', 'replicaset_timestamps', 
            'deployment_info', 'pod_timestamps', 'pods_running', 'pods_basic',
            'pvc_text', 'services_text', 'storage_classes_text', 'nodes_text',
            'services_loadbalancer', 'volume_snapshot_classes', 'service_accounts_default',
            'roles_default', 'resource_quota_default', 'namespace_cost_monitoring',
            'namespace_security_optimized', 'networkpolicy_comprehensive', 
            'storageclass_cost_optimized', 'deployment_cluster_autoscaler',
            'deployment_metrics_server', 'configmap_pv_lifecycle', 'api_resources',
            'api_versions', 'cluster_info', 'hpa_text', 'hpa_no_headers', 'hpa_basic',
            'hpa_custom', 'hpa_high_cpu', 'deployments_text', 'pods_all', 'cluster_utilization'
        }
        return key in text_commands
    
    # === QUERY INTERFACE FOR COMPONENTS ===
    
    def get(self, key: str) -> Any:
        """Get any data by key"""
        return self.data.get(key)
    
    def _ensure_json_format(self, key: str) -> Dict[str, Any]:
        """Ensure data is in JSON dictionary format with items array"""
        raw_data = self.get(key)
        
        if not raw_data:
            return {"items": []}
        
        # If already a dictionary, return as-is
        if isinstance(raw_data, dict):
            return raw_data
            
        # If it's a string, try to parse as JSON
        if isinstance(raw_data, str):
            # Skip empty strings - they're valid empty results
            if not raw_data.strip():
                return {"items": []}
                
            try:
                parsed = json.loads(raw_data)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                # Only warn for non-empty strings that fail to parse
                logger.warning(f"⚠️ {self.cluster_name}: Failed to parse {key} as JSON, returning empty structure")
        
        # Fallback to empty structure
        return {"items": []}
    
    def get_workload_data(self) -> Dict[str, Any]:
        """Get workload data for ml_framework_generator"""
        # Debug pods data specifically since it's critical
        pods_raw = self.get('pods')
        pods_formatted = self._ensure_json_format('pods')
        pods_count = len(pods_formatted.get('items', []))
        logger.debug(f"🐛 {self.cluster_name}: Pods debug - raw data type: {type(pods_raw)}, formatted items: {pods_count}")
        
        # FALLBACK: If JSON pods data is empty but custom columns has data, construct JSON from custom columns
        if pods_count == 0:
            pod_resources_text = self.get('pod_resources')
            if pod_resources_text and isinstance(pod_resources_text, str) and len(pod_resources_text.strip()) > 100:
                logger.info(f"🔄 {self.cluster_name}: JSON pods empty but custom columns has data - using fallback")
                pods_formatted = self._construct_pods_json_from_custom_columns(pod_resources_text)
                pods_count = len(pods_formatted.get('items', []))
                logger.info(f"✅ {self.cluster_name}: Constructed {pods_count} pods from custom columns fallback")
        
        return {
            'pod_resources': self.get('pod_resources') or "",  # Text format - ensure string
            'pod_timestamps': self.get('pod_timestamps') or "",  # Text format - ensure string  
            'replicaset_timestamps': self.get('replicaset_timestamps') or "",  # Text format - ensure string
            'deployment_info': self.get('deployment_info') or "",  # Text format - ensure string
            'pods': pods_formatted,  # Use the (potentially fallback-constructed) pods data
            'deployments': self._ensure_json_format('deployments'),  # JSON - ensure dict with items
            'replicasets': self._ensure_json_format('replicasets'),  # JSON - ensure dict with items  
            'statefulsets': self._ensure_json_format('statefulsets'),  # JSON - ensure dict with items
            'services': self._ensure_json_format('services'),  # JSON - ensure dict with items
            'pvcs': self._ensure_json_format('pvcs'),  # JSON - ensure dict with items
            'namespaces': self._ensure_json_format('namespaces'),  # JSON - ensure dict with items
            'events': self._ensure_json_format('events'),  # JSON - ensure dict with items
            'configmaps': self._ensure_json_format('configmaps'),  # JSON - ensure dict with items
            'applications': self._ensure_json_format('applications'),  # JSON - ensure dict with items
            'version': self._ensure_json_format('version')  # JSON - ensure dict for version info
        }
    
    def get_resource_usage_data(self) -> Dict[str, Any]:
        """Get resource utilization for aks_realtime_metrics"""
        return {
            'node_usage': self.get('node_usage') or "",  # Text - kubectl top nodes
            'pod_usage': self.get('pod_usage') or "",  # Text - kubectl top pods 
            'nodes': self.get('nodes') or {"items": []},  # JSON - nodes data
            'nodes_text': self.get('nodes_text') or "",  # Text fallback
            'pod_resources': self.get('pod_resources') or "",  # Text - custom columns
            'pods_basic': self.get('pods_basic') or "",  # Text - basic pod list
            'hpa': self._ensure_json_format('hpa'),  # JSON - HPA data - ensure dict
            'hpa_text': self.get('hpa_text') or "",  # Text fallback for HPA
            'hpa_custom': self.get('hpa_custom') or "",  # Text - custom HPA format
            'hpa_high_cpu': self.get('hpa_high_cpu') or ""  # Text - high CPU detection format
        }
    
    def get_cost_analysis_data(self) -> Dict[str, Any]:
        """Get data for pod_cost_analyzer"""
        return {
            'pods_running': self.get('pods_running'),
            'nodes': self.get('nodes'), 
            'pvc_text': self.get('pvc_text'),
            'services_text': self.get('services_text'),
            'pod_usage': self.get('pod_usage'),  # kubectl top pods
            'storage_classes': self.get('storage_classes'),
            'storage_classes_text': self.get('storage_classes_text')
        }
    
    def get_security_data(self) -> Dict[str, Any]:
        """Get security and compliance data"""
        return {
            'namespaces': self._ensure_json_format('namespaces'),  # JSON - ensure dict
            'service_accounts': self._ensure_json_format('service_accounts'),  # JSON - ensure dict
            'cluster_roles': self._ensure_json_format('cluster_roles'),  # JSON - ensure dict
            'role_bindings': self._ensure_json_format('role_bindings'),  # JSON - ensure dict
            'cluster_role_bindings': self._ensure_json_format('cluster_role_bindings'),  # JSON - ensure dict
            'network_policies': self._ensure_json_format('network_policies'),  # JSON - ensure dict
            'resource_quotas': self._ensure_json_format('resource_quotas'),  # JSON - ensure dict
            'limit_ranges': self._ensure_json_format('limit_ranges'),  # JSON - ensure dict
            'secrets': self._ensure_json_format('secrets'),  # JSON - ensure dict
            'pod_security_policies': self._ensure_json_format('pod_security_policies')  # JSON - ensure dict
        }
    
    def get_infrastructure_data(self) -> Dict[str, Any]:
        """Get infrastructure data for ML framework"""
        return {
            'services': self._ensure_json_format('services'),  # JSON - ensure dict
            'services_text': self.get('services_text') or "",  # Text fallback
            'pvcs': self._ensure_json_format('pvcs'),  # JSON - ensure dict
            'pvc_text': self.get('pvc_text') or "",  # Text fallback
            'storage_classes': self._ensure_json_format('storage_classes'),  # JSON - ensure dict
            'storage_classes_text': self.get('storage_classes_text') or "",  # Text fallback
            'volume_snapshot_classes': self.get('volume_snapshot_classes') or "",  # Text
            'services_loadbalancer': self.get('services_loadbalancer') or "",  # Text
            'configmaps': self._ensure_json_format('configmaps'),  # JSON - ensure dict
            'nodes': self._ensure_json_format('nodes'),  # JSON - ensure dict
            'nodes_text': self.get('nodes_text') or ""  # Text fallback
        }
    
    def get_hpa_data(self) -> Dict[str, Any]:
        """Get HPA and autoscaling data - SINGLE SOURCE OF TRUTH with text parsing fallback"""
        
        # Try JSON format first
        hpa_json_data = self._ensure_json_format('hpa')
        
        # If JSON is empty but we have text data, try custom columns first, then basic text
        if not hpa_json_data.get('items'):
            if self.get('hpa_custom'):
                logger.info("🔄 HPA JSON empty, parsing from custom columns format")
                hpa_json_data = self._parse_hpa_custom_to_json()
            elif self.get('hpa_text'):
                logger.info("🔄 HPA JSON empty, parsing from basic text format")
                hpa_json_data = self._parse_hpa_text_to_json()
        
        return {
            'hpa': hpa_json_data,  # JSON - kubectl get hpa or parsed from text
            'hpa_text': self.get('hpa_text') or "",  # Text - kubectl get hpa --all-namespaces
            'hpa_custom': self.get('hpa_custom') or "",  # Text - custom columns format
            'deployments': self._ensure_json_format('deployments'),  # JSON - kubectl get deployments --all-namespaces -o json
            'statefulsets': self._ensure_json_format('statefulsets'),  # JSON - kubectl get statefulsets --all-namespaces -o json
            'replicasets': self._ensure_json_format('replicasets')  # JSON - kubectl get replicasets --all-namespaces -o json
        }
    
    def _parse_hpa_text_to_json(self) -> Dict[str, Any]:
        """Parse HPA text output into JSON-like structure"""
        try:
            hpa_text = self.get('hpa_text') or ""
            if not hpa_text.strip():
                return {'items': []}
            
            lines = hpa_text.strip().split('\n')
            if not lines:
                return {'items': []}
            
            # Skip header line if present
            if lines and ('NAMESPACE' in lines[0] or 'NAME' in lines[0]):
                lines = lines[1:]
            
            hpa_items = []
            for line in lines:
                if not line.strip():
                    continue
                
                # Parse HPA text line: NAMESPACE NAME REFERENCE TARGETS MINPODS MAXPODS REPLICAS AGE
                parts = line.split()
                if len(parts) >= 6:
                    namespace = parts[0]
                    name = parts[1]
                    reference = parts[2] if len(parts) > 2 else 'unknown'
                    targets = parts[3] if len(parts) > 3 else 'unknown'
                    min_replicas = parts[4] if len(parts) > 4 else '1'
                    max_replicas = parts[5] if len(parts) > 5 else '10'
                    
                    # Parse targets to extract detailed metrics information
                    metrics_list, current_metrics = self._parse_hpa_targets(targets)
                    
                    # Create enhanced HPA JSON structure with real metrics
                    hpa_item = {
                        'apiVersion': 'autoscaling/v2',
                        'kind': 'HorizontalPodAutoscaler',
                        'metadata': {
                            'name': name,
                            'namespace': namespace
                        },
                        'spec': {
                            'minReplicas': int(min_replicas) if min_replicas.isdigit() else 1,
                            'maxReplicas': int(max_replicas) if max_replicas.isdigit() else 10,
                            'scaleTargetRef': {
                                'name': reference.split('/')[-1] if '/' in reference else reference,
                                'kind': reference.split('/')[0] if '/' in reference else 'Deployment'
                            },
                            'metrics': metrics_list
                        },
                        'status': {
                            'currentReplicas': int(parts[6]) if len(parts) > 6 and parts[6].isdigit() else 1,
                            'currentMetrics': current_metrics,
                            '_parsed_from_text': True,
                            '_enhanced_parsing': True
                        }
                    }
                    hpa_items.append(hpa_item)
            
            # Debug: Log sample target strings to understand the real format
            if hpa_items:
                sample_count = min(5, len(hpa_items))
                logger.info(f"🔍 DEBUG: Sample HPA target formats from first {sample_count} HPAs:")
                sample_targets = []
                for line in lines[:sample_count]:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 4:
                            target = parts[3]
                            sample_targets.append(target)
                            logger.info(f"   Target: '{target}'")
                
                # Log metrics distribution for debugging
                cpu_count = sum(1 for item in hpa_items if any(m['resource']['name'] == 'cpu' for m in item['spec']['metrics']))
                memory_count = sum(1 for item in hpa_items if any(m['resource']['name'] == 'memory' for m in item['spec']['metrics']))
                mixed_count = sum(1 for item in hpa_items if len(item['spec']['metrics']) > 1)
                logger.info(f"🔍 DEBUG: Parsed metrics - CPU: {cpu_count}, Memory: {memory_count}, Mixed: {mixed_count}")
            
            logger.info(f"✅ Parsed {len(hpa_items)} HPAs from text format")
            return {'items': hpa_items}
            
        except Exception as e:
            logger.error(f"❌ Error parsing HPA text: {e}")
            return {'items': []}
    
    def _parse_hpa_targets(self, targets: str) -> Tuple[List[Dict], List[Dict]]:
        """
        Parse HPA targets string to extract detailed metrics information
        
        Examples:
        - '50%/70%' -> CPU metric with current 50%, target 70%
        - '100Mi/200Mi' -> Memory metric with current 100Mi, target 200Mi  
        - '60%/70%,100Mi/200Mi' -> Both CPU and Memory metrics
        """
        try:
            if not targets or targets == 'unknown' or '<unknown>' in targets:
                # Default to basic CPU metric
                return [
                    {
                        'type': 'Resource',
                        'resource': {
                            'name': 'cpu',
                            'target': {
                                'type': 'Utilization',
                                'averageUtilization': 70
                            }
                        }
                    }
                ], []
            
            metrics_list = []
            current_metrics = []
            
            # Split by comma for multiple metrics
            metric_pairs = targets.split(',')
            
            for pair in metric_pairs:
                if '/' in pair:
                    current_str, target_str = pair.split('/', 1)
                    current_str = current_str.strip()
                    target_str = target_str.strip()
                    
                    # Determine metric type based on format
                    if '%' in target_str:
                        # CPU percentage metric
                        try:
                            target_value = int(target_str.replace('%', ''))
                            current_value = int(current_str.replace('%', '')) if '%' in current_str and 'unknown' not in current_str else None
                        except:
                            target_value = 70
                            current_value = None
                            
                        metrics_list.append({
                            'type': 'Resource',
                            'resource': {
                                'name': 'cpu',
                                'target': {
                                    'type': 'Utilization',
                                    'averageUtilization': target_value
                                }
                            }
                        })
                        
                        if current_value is not None:
                            current_metrics.append({
                                'type': 'Resource',
                                'resource': {
                                    'name': 'cpu',
                                    'current': {
                                        'averageUtilization': current_value
                                    }
                                }
                            })
                    
                    elif any(unit in target_str for unit in ['Mi', 'Gi', 'Ki']):
                        # Memory quantity metric
                        metrics_list.append({
                            'type': 'Resource',
                            'resource': {
                                'name': 'memory',
                                'target': {
                                    'type': 'AverageValue',
                                    'averageValue': target_str
                                }
                            }
                        })
                        
                        if 'unknown' not in current_str:
                            current_metrics.append({
                                'type': 'Resource',
                                'resource': {
                                    'name': 'memory',
                                    'current': {
                                        'averageValue': current_str
                                    }
                                }
                            })
            
            # Default to CPU if no metrics parsed
            if not metrics_list:
                metrics_list.append({
                    'type': 'Resource',
                    'resource': {
                        'name': 'cpu',
                        'target': {
                            'type': 'Utilization', 
                            'averageUtilization': 70
                        }
                    }
                })
            
            return metrics_list, current_metrics
            
        except Exception as e:
            logger.debug(f"Error parsing HPA targets '{targets}': {e}")
            # Return default CPU metric
            return [
                {
                    'type': 'Resource',
                    'resource': {
                        'name': 'cpu',
                        'target': {
                            'type': 'Utilization',
                            'averageUtilization': 70
                        }
                    }
                }
            ], []
    
    def _parse_hpa_custom_to_json(self) -> Dict[str, Any]:
        """Parse HPA custom columns output to extract detailed metrics"""
        try:
            hpa_custom = self.get('hpa_custom') or ""
            if not hpa_custom.strip():
                return {'items': []}
            
            lines = hpa_custom.strip().split('\n')
            if not lines:
                return {'items': []}
            
            # Skip header if present
            if lines and 'NAMESPACE' in lines[0]:
                lines = lines[1:]
            
            hpa_items = []
            for line in lines:
                if not line.strip():
                    continue
                
                # Simplified custom columns format: NAMESPACE NAME REFERENCE METRICS MIN MAX
                parts = line.split()
                if len(parts) >= 6:
                    namespace = parts[0]
                    name = parts[1]
                    reference = parts[2] if len(parts) > 2 else 'unknown'
                    metrics_names = parts[3] if len(parts) > 3 else 'cpu'  # Comma-separated: "cpu" or "memory" or "cpu,memory"
                    min_replicas = parts[4] if len(parts) > 4 else '1'
                    max_replicas = parts[5] if len(parts) > 5 else '10'
                    
                    # Build metrics from resource names
                    metrics_list = []
                    
                    # Parse comma-separated metric names
                    if metrics_names and metrics_names != '<none>':
                        resource_names = [name.strip() for name in metrics_names.split(',')]
                        
                        for resource_name in resource_names:
                            if resource_name == 'cpu':
                                metrics_list.append({
                                    'type': 'Resource',
                                    'resource': {
                                        'name': 'cpu',
                                        'target': {
                                            'type': 'Utilization',
                                            'averageUtilization': 70  # Default target
                                        }
                                    }
                                })
                            elif resource_name == 'memory':
                                metrics_list.append({
                                    'type': 'Resource',
                                    'resource': {
                                        'name': 'memory',
                                        'target': {
                                            'type': 'AverageValue',
                                            'averageValue': '500Mi'  # Default target
                                        }
                                    }
                                })
                    
                    # Default to CPU if no metrics found
                    if not metrics_list:
                        metrics_list.append({
                            'type': 'Resource',
                            'resource': {
                                'name': 'cpu',
                                'target': {
                                    'type': 'Utilization',
                                    'averageUtilization': 70
                                }
                            }
                        })
                    
                    current_metrics = []  # Custom columns don't have current values
                    
                    hpa_item = {
                        'apiVersion': 'autoscaling/v2',
                        'kind': 'HorizontalPodAutoscaler',
                        'metadata': {
                            'name': name,
                            'namespace': namespace
                        },
                        'spec': {
                            'minReplicas': int(min_replicas) if min_replicas.isdigit() else 1,
                            'maxReplicas': int(max_replicas) if max_replicas.isdigit() else 10,
                            'scaleTargetRef': {
                                'name': reference.split('/')[-1] if '/' in reference else reference,
                                'kind': reference.split('/')[0] if '/' in reference else 'Deployment'
                            },
                            'metrics': metrics_list
                        },
                        'status': {
                            'currentReplicas': 1,  # Default since custom columns may not have this
                            'currentMetrics': current_metrics,
                            '_parsed_from_custom': True,
                            '_enhanced_parsing': True
                        }
                    }
                    hpa_items.append(hpa_item)
            
            # Debug logging for custom columns
            if hpa_items:
                logger.info(f"🔍 DEBUG: Custom columns sample metrics:")
                for i, line in enumerate(lines[:3]):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 4:
                            metrics_names = parts[3]
                            logger.info(f"   HPA {i+1}: Metrics='{metrics_names}'")
            
            logger.info(f"✅ Parsed {len(hpa_items)} HPAs from custom columns format")
            return {'items': hpa_items}
            
        except Exception as e:
            logger.error(f"❌ Error parsing HPA custom columns: {e}")
            return {'items': []}
    
    def get_all_data(self) -> Dict[str, Any]:
        """Get all cached data (backward compatibility)"""
        return self.data.copy()
    
    def get_cluster_utilization(self) -> Tuple[Optional[float], Optional[float]]:
        """
        Parse cluster utilization from cached data
        Returns: (cpu_percentage, memory_percentage) or (None, None) if not available
        """
        cluster_util_data = self.get('cluster_utilization')
        if not cluster_util_data:
            logger.warning(f"⚠️ {self.cluster_name}: No cluster utilization data in cache")
            return None, None
        
        try:
            # Expected format: "CPU:24.0%,Memory:36.5%"
            if 'CPU:' in cluster_util_data and 'Memory:' in cluster_util_data:
                parts = cluster_util_data.strip().split(',')
                cpu_part = [p for p in parts if p.startswith('CPU:')]
                mem_part = [p for p in parts if p.startswith('Memory:')]
                
                if cpu_part and mem_part:
                    cpu_str = cpu_part[0].replace('CPU:', '').replace('%', '')
                    mem_str = mem_part[0].replace('Memory:', '').replace('%', '')
                    
                    cpu_val = float(cpu_str)
                    mem_val = float(mem_str)
                    
                    logger.info(f"✅ {self.cluster_name}: Parsed cluster utilization - CPU: {cpu_val}%, Memory: {mem_val}%")
                    return cpu_val, mem_val
        except Exception as e:
            logger.error(f"❌ {self.cluster_name}: Error parsing cluster utilization '{cluster_util_data}': {e}")
        
        return None, None
    
    def execute_dynamic_command(self, cmd: str, timeout: int = 60) -> Optional[str]:
        """
        Execute dynamic kubectl commands (with variables like node names)
        This handles commands that can't be pre-cached because they have parameters
        """
        return self._execute_kubectl_command(cmd, timeout)
    
    def _construct_pods_json_from_custom_columns(self, pod_resources_text: str) -> Dict[str, Any]:
        """Construct basic JSON pods structure from custom columns data as fallback"""
        try:
            lines = pod_resources_text.strip().split('\n')
            if not lines:
                return {"items": []}
            
            # Skip header line
            if lines and ('NAMESPACE' in lines[0] or 'NAME' in lines[0]):
                lines = lines[1:]
            
            pods = []
            for line in lines:
                if not line.strip():
                    continue
                    
                # Parse custom columns format: NAMESPACE, NAME, CPU_REQ, MEM_REQ, NODE, CREATED, STATUS
                parts = line.split(None, 6)  # Split into max 7 parts
                if len(parts) >= 7:
                    namespace, name, cpu_req, mem_req, node, created, status = parts
                    
                    # Construct minimal pod JSON structure for security analysis
                    pod = {
                        "metadata": {
                            "name": name,
                            "namespace": namespace,
                            "creationTimestamp": created if created != '<none>' else None
                        },
                        "spec": {
                            "nodeName": node if node != '<none>' else None,
                            "containers": [
                                {
                                    "name": "main",  # Generic name since we don't have container details
                                    "resources": {
                                        "requests": {}
                                    }
                                }
                            ]
                        },
                        "status": {
                            "phase": status
                        }
                    }
                    
                    # Add resource requests if available
                    if cpu_req != '<none>':
                        pod["spec"]["containers"][0]["resources"]["requests"]["cpu"] = cpu_req
                    if mem_req != '<none>':
                        pod["spec"]["containers"][0]["resources"]["requests"]["memory"] = mem_req
                    
                    pods.append(pod)
            
            logger.info(f"🔄 {self.cluster_name}: Constructed {len(pods)} pods from custom columns")
            return {"items": pods}
            
        except Exception as e:
            logger.error(f"❌ {self.cluster_name}: Failed to construct pods JSON from custom columns: {e}")
            return {"items": []}
    
    def get_node_specific_data(self, node_name: str, query_type: str) -> Optional[str]:
        """Get specific data for an individual node"""
        # Try to get from cached nodes data first
        nodes_data = self.get('nodes')
        if nodes_data and 'items' in nodes_data:
            for node in nodes_data['items']:
                if node.get('metadata', {}).get('name') == node_name:
                    if query_type == 'instance-type':
                        return node.get('metadata', {}).get('labels', {}).get('node.kubernetes.io/instance-type', '')
                    elif query_type == 'cpu':
                        return node.get('status', {}).get('allocatable', {}).get('cpu', '')
                    elif query_type == 'memory':
                        return node.get('status', {}).get('allocatable', {}).get('memory', '')
        
        # Fallback to direct query if not found in cache
        cmd_map = {
            'instance-type': f"kubectl get node {node_name} -o jsonpath='{{.metadata.labels.node\\.kubernetes\\.io/instance-type}}'",
            'cpu': f"kubectl get node {node_name} -o jsonpath='{{.status.allocatable.cpu}}'",
            'memory': f"kubectl get node {node_name} -o jsonpath='{{.status.allocatable.memory}}'"
        }
        
        if query_type in cmd_map:
            return self._execute_kubectl_command(cmd_map[query_type])
        
        return None


# === GLOBAL CACHE MANAGER ===
_active_caches: Dict[str, KubernetesDataCache] = {}

def get_or_create_cache(cluster_name: str, resource_group: str, subscription_id: str) -> KubernetesDataCache:
    """
    Get or create cache instance for a cluster.
    Reuses existing cache if available, creates fresh cache only if needed.
    """
    cache_key = f"{subscription_id}:{resource_group}:{cluster_name}"
    
    # Check if cache already exists and reuse it
    if cache_key in _active_caches:
        logger.info(f"♻️ Reusing existing cache for {cluster_name} (avoiding duplicate kubectl execution)")
        return _active_caches[cache_key]
    
    # Create fresh cache only if none exists
    logger.info(f"🆕 Creating initial cache for {cluster_name} (first time - executing all kubectl commands)")
    _active_caches[cache_key] = KubernetesDataCache(cluster_name, resource_group, subscription_id, auto_fetch=True)
    
    return _active_caches[cache_key]

def fetch_cluster_data(cluster_name: str, resource_group: str, subscription_id: str) -> KubernetesDataCache:
    """Convenience function to get cache with fresh data (data is auto-fetched on creation)"""
    return get_or_create_cache(cluster_name, resource_group, subscription_id)

def clear_all_caches():
    """Clear all active caches"""
    global _active_caches
    _active_caches.clear()
    logger.info("🗑️ All caches cleared")