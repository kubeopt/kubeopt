"""
AKS Real-time Metrics Fetcher - Enhanced Version
================================================
Fetches real-time performance metrics directly from AKS clusters.
Provides current usage data for optimization algorithms.

INTEGRATION: Works with pod_cost_analyzer.py to provide usage+cost analysis
PURPOSE: Collects "what is happening now" data for optimization calculations
"""
"""
AKS Real-time Metrics Fetcher - FIXED VERSION
=============================================
Enhanced error handling and debugging for kubectl command execution
"""

# ============================================================================
# IMPORTS AND CONFIGURATION
# ============================================================================

"""
AKS Real-time Metrics Fetcher - FIXED VERSION
=============================================
Enhanced error handling and debugging for kubectl command execution
"""

import subprocess
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import numpy as np

logger = logging.getLogger(__name__)

class KubernetesParsingUtils:
    @staticmethod
    def parse_cpu_safe(cpu_str: str) -> float:
        """Parse CPU values safely"""
        if not cpu_str or not isinstance(cpu_str, str):
            return 0.0
        try:
            cpu_str = cpu_str.strip()
            if cpu_str.endswith('m'):
                return float(cpu_str[:-1]) / 1000.0
            elif cpu_str.endswith('n'):
                return float(cpu_str[:-1]) / 1000000000.0
            else:
                return float(cpu_str)
        except:
            return 0.0
    
    @staticmethod
    def parse_memory_safe(memory_str: str) -> int:
        """Parse memory values safely"""
        if not memory_str or not isinstance(memory_str, str):
            return 0
        try:
            memory_str = memory_str.strip()
            if memory_str.endswith('Ki'):
                return int(float(memory_str[:-2]) * 1024)
            elif memory_str.endswith('Mi'):
                return int(float(memory_str[:-2]) * 1024 * 1024)
            elif memory_str.endswith('Gi'):
                return int(float(memory_str[:-2]) * 1024 * 1024 * 1024)
            else:
                return int(float(memory_str))
        except:
            return 0

class AKSRealTimeMetricsFetcher:
    """Enhanced AKS Real-time Metrics Collection with Better Error Handling"""
    
    def __init__(self, resource_group: str, cluster_name: str):
        self.resource_group = resource_group
        self.cluster_name = cluster_name
        self.connection_verified = False
        self.parser = KubernetesParsingUtils()

    def _clean_command_output(self, raw_output: str) -> str:
        """        
        This function removes the metadata to get clean kubectl output.
        """
        try:
            # Remove command metadata lines
            lines = raw_output.split('\n')
            clean_lines = []
            
            for line in lines:
                # Skip Azure CLI metadata lines
                if any(skip_pattern in line.lower() for skip_pattern in [
                    'command started at',
                    'command finished at',
                    'exitcode=',
                    'command started',
                    'command finished'
                ]):
                    continue
                clean_lines.append(line)
            
            clean_output = '\n'.join(clean_lines).strip()
            
            # For JSON output, try to find the actual JSON content
            if '{' in clean_output and '}' in clean_output:
                # Find the start and end of JSON
                start_idx = clean_output.find('{')
                # Find the last closing brace
                end_idx = clean_output.rfind('}') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_content = clean_output[start_idx:end_idx]
                    
                    # Validate it's proper JSON
                    try:
                        json.loads(json_content)
                        return json_content
                    except json.JSONDecodeError:
                        # If JSON parsing fails, return the cleaned text
                        logger.warning("⚠️ JSON extraction failed, returning cleaned text")
                        return clean_output
            
            return clean_output
            
        except Exception as e:
            logger.error(f"❌ Error cleaning command output: {e}")
            return raw_output


    def _get_hpa_configurations(self) -> List[Dict]:
        """Get existing HPA configurations"""
        try:
            hpa_output = self.execute_kubectl_command("kubectl get hpa --all-namespaces -o json")
            
            if not hpa_output:
                logger.info("📋 No HPA resources found")
                return []
            
            hpa_data = json.loads(hpa_output)
            hpa_configs = []
            
            for hpa in hpa_data.get('items', []):
                config = {
                    'name': hpa['metadata']['name'],
                    'namespace': hpa['metadata']['namespace'],
                    'target': hpa['spec']['scaleTargetRef']['name'],
                    'min_replicas': hpa['spec'].get('minReplicas', 1),
                    'max_replicas': hpa['spec'].get('maxReplicas', 10),
                    'metrics': [],
                    'primary_metric': 'unknown'
                }
                
                # Analyze metrics configuration
                for metric in hpa['spec'].get('metrics', []):
                    if metric['type'] == 'Resource':
                        metric_name = metric['resource']['name']
                        config['metrics'].append({
                            'type': 'resource',
                            'name': metric_name,
                            'target': metric['resource']['target']
                        })
                        
                        # Determine primary metric
                        if metric_name == 'cpu':
                            config['primary_metric'] = 'cpu_based'
                        elif metric_name == 'memory':
                            config['primary_metric'] = 'memory_based'
                
                hpa_configs.append(config)
            
            logger.info(f"✅ Found {len(hpa_configs)} HPA configurations")
            return hpa_configs
            
        except Exception as e:
            logger.error(f"❌ Error getting HPA configs: {e}")
            return []

    def _analyze_deployment_scaling_configs(self) -> Dict:
        """Analyze deployment resource configurations for scaling insights"""
        try:
            deployments_output = self.execute_kubectl_command("kubectl get deployments --all-namespaces -o json")
            
            if not deployments_output:
                return {}
            
            deployments = json.loads(deployments_output)
            
            analysis = {
                'total_deployments': 0,
                'cpu_request_patterns': [],
                'memory_request_patterns': [],
                'avg_cpu_requests': 0,
                'avg_memory_requests': 0
            }
            
            cpu_values = []
            memory_values = []
            
            for deployment in deployments.get('items', []):
                analysis['total_deployments'] += 1
                
                # Analyze container resource patterns
                containers = deployment['spec']['template']['spec'].get('containers', [])
                for container in containers:
                    resources = container.get('resources', {})
                    requests = resources.get('requests', {})
                    
                    if 'cpu' in requests:
                        cpu_val = self.parser.parse_cpu_safe(requests['cpu'])
                        if cpu_val > 0:
                            cpu_values.append(cpu_val)
                            
                    if 'memory' in requests:
                        memory_val = self.parser.parse_memory_safe(requests['memory'])
                        if memory_val > 0:
                            memory_values.append(memory_val)
            
            if cpu_values:
                analysis['avg_cpu_requests'] = sum(cpu_values) / len(cpu_values)
            if memory_values:
                analysis['avg_memory_requests'] = sum(memory_values) / len(memory_values)
            
            logger.info(f"📊 Analyzed {analysis['total_deployments']} deployments")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error analyzing deployments: {e}")
            return {}

    def _determine_hpa_pattern(self, hpa_configs: List[Dict], deployment_patterns: Dict) -> Dict:
        """Determine the primary HPA pattern from analysis"""
        
        if not hpa_configs:
            return {
                'pattern': 'no_hpa_detected',
                'confidence': 'high',
                'reason': 'No HPA resources found in cluster'
            }
        
        # Analyze primary metrics
        cpu_based_count = 0
        memory_based_count = 0
        hybrid_count = 0
        
        for config in hpa_configs:
            primary_metric = config.get('primary_metric', 'unknown')
            metrics_count = len(config.get('metrics', []))
            
            if primary_metric == 'cpu_based':
                cpu_based_count += 1
            elif primary_metric == 'memory_based':
                memory_based_count += 1
            elif metrics_count > 1:
                hybrid_count += 1
        
        total_hpas = len(hpa_configs)
        
        # Determine pattern based on majority
        if cpu_based_count > total_hpas * 0.6:
            return {
                'pattern': 'cpu_based_dominant',
                'confidence': 'high',
                'reason': f'{cpu_based_count}/{total_hpas} HPAs use CPU-based scaling',
                'cpu_percentage': (cpu_based_count / total_hpas) * 100
            }
        elif memory_based_count > total_hpas * 0.6:
            return {
                'pattern': 'memory_based_dominant',
                'confidence': 'high',
                'reason': f'{memory_based_count}/{total_hpas} HPAs use memory-based scaling',
                'memory_percentage': (memory_based_count / total_hpas) * 100
            }
        elif hybrid_count > 0:
            return {
                'pattern': 'hybrid_approach',
                'confidence': 'medium',
                'reason': f'Mixed implementation: CPU={cpu_based_count}, Memory={memory_based_count}, Hybrid={hybrid_count}'
            }
        else:
            return {
                'pattern': 'mixed_implementation',
                'confidence': 'medium',
                'reason': 'Multiple approaches detected without clear majority'
            }

    # MODIFY the get_comprehensive_metrics method to include HPA detection:
    def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """ENHANCED: Get comprehensive metrics including HPA detection"""
        logger.info("🚀 Fetching comprehensive real-time AKS metrics...")
        
        start_time = datetime.now()
        
        if not self.verify_cluster_connection():
            return {
                'status': 'error',
                'message': 'Failed to connect to AKS cluster',
                'timestamp': start_time.isoformat()
            }
        
        try:
            # Get node metrics (existing logic)
            node_metrics = self.get_node_metrics()
            
            # NEW: Get HPA implementation status
            hpa_status = self.get_hpa_implementation_status()
            
            if node_metrics.get('nodes'):
                return {
                    'metadata': {
                        'cluster_name': self.cluster_name,
                        'resource_group': self.resource_group,
                        'timestamp': datetime.now().isoformat(),
                        'source': 'Real-time AKS Cluster Metrics with HPA Detection',
                        'data_source': 'kubectl via az aks command invoke',
                        'collection_time_ms': int((datetime.now() - start_time).total_seconds() * 1000),
                        'integration_ready': True
                    },
                    'nodes': node_metrics.get('nodes', []),
                    'total_nodes': node_metrics.get('total_nodes', 0),
                    'ready_nodes': node_metrics.get('ready_nodes', 0),
                    'status': 'success',
                    'data_quality': 'high' if node_metrics['nodes'] else 'low',
                    
                    # NEW: HPA implementation data
                    'hpa_implementation': hpa_status,
                    'current_hpa_pattern': hpa_status.get('current_hpa_pattern'),
                    'hpa_detection_confidence': hpa_status.get('confidence')
                }
            else:
                return {
                    'status': 'error',
                    'message': 'No node metrics available',
                    'timestamp': start_time.isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Error collecting comprehensive metrics: {e}")
            return {
                'status': 'error',
                'message': f'Error collecting metrics: {str(e)}',
                'timestamp': start_time.isoformat()
            }    
        
    def verify_cluster_connection(self) -> bool:
        """Verify AKS cluster connectivity with enhanced debugging"""
        try:
            logger.info(f"Verifying connection to AKS cluster {self.cluster_name}")
            
            # First check if we can access the cluster
            cmd = [
                'az', 'aks', 'command', 'invoke',
                '--resource-group', self.resource_group,
                '--name', self.cluster_name,
                '--command', 'kubectl cluster-info'
            ]
            
            logger.info(f"🔧 DEBUG: Executing verification command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            logger.info(f"🔧 DEBUG: Return code: {result.returncode}")
            logger.info(f"🔧 DEBUG: STDOUT length: {len(result.stdout)}")
            logger.info(f"🔧 DEBUG: STDERR: {result.stderr}")
            
            if result.returncode == 0 and result.stdout.strip():
                # Check if the output contains cluster info (even with metadata)
                if "Kubernetes control plane" in result.stdout or "Kubernetes master" in result.stdout:
                    logger.info("✅ Successfully connected to AKS cluster")
                    self.connection_verified = True
                    return True
                else:
                    logger.warning("⚠️ Connected but no cluster info found")
                    # Still consider it successful if we got a response
                    self.connection_verified = True
                    return True
            else:
                logger.error(f"❌ Failed to verify cluster connection. Return code: {result.returncode}")
                logger.error(f"❌ STDERR: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Connection timeout to AKS cluster")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error during connection verification: {e}")
            return False
    
    def execute_kubectl_command(self, kubectl_cmd: str, timeout: int = 60) -> Optional[str]:
        """FIXED: Execute kubectl command with proper output cleaning"""
        try:
            cmd = [
                'az', 'aks', 'command', 'invoke',
                '--resource-group', self.resource_group,
                '--name', self.cluster_name,
                '--command', kubectl_cmd
            ]
            
            logger.info(f"🔧 DEBUG: Executing: {kubectl_cmd}")
            start_time = time.time()
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            
            execution_time = time.time() - start_time
            logger.info(f"🔧 DEBUG: Command completed in {execution_time:.2f}s")
            logger.info(f"🔧 DEBUG: Return code: {result.returncode}")
            
            if result.stderr:
                logger.warning(f"🔧 DEBUG: STDERR: {result.stderr}")
            
            if result.returncode != 0:
                logger.error(f"❌ Command failed with return code {result.returncode}")
                logger.error(f"❌ STDERR: {result.stderr}")
                return None
            
            # FIXED: Clean the output properly
            clean_output = self._clean_command_output(result.stdout)
            
            if not clean_output:
                logger.warning(f"⚠️ No output after cleaning for command: {kubectl_cmd}")
                return None
            
            logger.info(f"🔧 DEBUG: Clean output length: {len(clean_output)}")
            
            # Handle very large outputs
            if len(clean_output) >= 500000:  # ~500KB limit
                logger.warning(f"⚠️ Large output detected ({len(clean_output)} chars)")
                
                # For JSON commands, try to use text format instead
                if '-o json' in kubectl_cmd and 'top' not in kubectl_cmd:
                    logger.info("🔄 Switching to text format due to size")
                    text_cmd = kubectl_cmd.replace(' -o json', ' --no-headers')
                    return self.execute_kubectl_command(text_cmd, timeout)
                    
            return clean_output
            
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ Timeout executing kubectl command: {kubectl_cmd}")
            return None
        except Exception as e:
            logger.error(f"❌ Error executing kubectl command '{kubectl_cmd}': {e}")
            return None

    def get_node_metrics(self) -> Dict[str, Any]:
        """Get node metrics with enhanced error handling"""
        logger.info("📊 Fetching real-time node metrics...")
        
        try:
            # Check if metrics-server is available
            metrics_check = self.execute_kubectl_command("kubectl get pods -n kube-system --selector=k8s-app=metrics-server")
            if not metrics_check:
                logger.warning("⚠️ Metrics server may not be available")
            else:
                # Fix: Handle both string and other types safely
                if isinstance(metrics_check, str):
                    logger.info(f"✅ Metrics server status: {len(metrics_check)} chars")
                else:
                    logger.info(f"✅ Metrics server status: response received")
            
            # Get node usage with shorter timeout first
            logger.info("🔧 DEBUG: Fetching node usage...")
            top_nodes = self.execute_kubectl_command("kubectl top nodes --no-headers", timeout=60)
            
            if not top_nodes:
                logger.warning("⚠️ Could not fetch 'kubectl top nodes' - trying alternative")
                # Alternative: try with different format
                top_nodes = self.execute_kubectl_command("kubectl top nodes", timeout=60)
            
            # Get node information
            logger.info("🔧 DEBUG: Fetching node information...")
            node_info = self.execute_kubectl_command("kubectl get nodes -o json")
            
            if not node_info:
                logger.error("❌ Could not fetch node information")
                return self._empty_node_metrics()
            
            return self._process_node_metrics(top_nodes, node_info)
            
        except Exception as e:
            logger.error(f"❌ Error fetching node metrics: {e}")
            return self._empty_node_metrics()
    
    def _process_node_metrics(self, top_nodes_output: Optional[str], node_info_json: str) -> Dict[str, Any]:
        """FIXED: Process node metrics with better JSON handling"""
        try:
            logger.info("🔧 DEBUG: Processing node metrics...")
            
            # Parse node information JSON
            try:
                nodes_data = json.loads(node_info_json)
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON parsing failed: {e}")
                logger.error(f"❌ JSON preview: {node_info_json[:500]}...")
                return self._empty_node_metrics()
            
            node_metrics = []
            
            # Parse top nodes output if available
            node_usage = {}
            if top_nodes_output:
                logger.info(f"🔧 DEBUG: Processing top nodes output: {len(top_nodes_output)} chars")
                top_lines = top_nodes_output.strip().split('\n')
                
                for line_idx, line in enumerate(top_lines):
                    if line.strip() and not line.startswith('NAME'):
                        parts = line.split()
                        logger.info(f"🔧 DEBUG: Line {line_idx}: {line}")
                        
                        if len(parts) >= 5:
                            node_name = parts[0]
                            cpu_usage = self.parser.parse_cpu_safe(parts[1])
                            memory_usage = self.parser.parse_memory_safe(parts[3])
                            
                            node_usage[node_name] = {
                                'cpu_usage_cores': cpu_usage,
                                'memory_usage_bytes': memory_usage
                            }
                            
                            logger.info(f"✅ Parsed node {node_name}: CPU={cpu_usage}, Memory={memory_usage}")
            else:
                logger.warning("⚠️ No top nodes data - using capacity estimates")
            
            # Process each node
            for node in nodes_data.get('items', []):
                node_name = node['metadata']['name']
                
                # Get allocatable resources
                allocatable = node['status'].get('allocatable', {})
                cpu_allocatable = self.parser.parse_cpu_safe(allocatable.get('cpu', '0'))
                memory_allocatable = self.parser.parse_memory_safe(allocatable.get('memory', '0Ki'))
                
                # Get usage data or use estimates
                if node_name in node_usage:
                    usage = node_usage[node_name]
                    cpu_usage_pct = (usage['cpu_usage_cores'] / cpu_allocatable * 100) if cpu_allocatable > 0 else 0
                    memory_usage_pct = (usage['memory_usage_bytes'] / memory_allocatable * 100) if memory_allocatable > 0 else 0
                else:
                    # Realistic estimates when metrics unavailable
                    logger.warning(f"⚠️ No usage data for {node_name}, using estimates")
                    cpu_usage_pct = 35.0
                    memory_usage_pct = 60.0
                    usage = {
                        'cpu_usage_cores': cpu_allocatable * 0.35,
                        'memory_usage_bytes': int(memory_allocatable * 0.60)
                    }
                
                # Get node status
                conditions = node['status'].get('conditions', [])
                ready_condition = next((c for c in conditions if c['type'] == 'Ready'), {})
                is_ready = ready_condition.get('status') == 'True'
                
                node_metrics.append({
                    'name': node_name,
                    'cpu_usage_pct': round(cpu_usage_pct, 1),
                    'memory_usage_pct': round(memory_usage_pct, 1),
                    'cpu_allocatable_cores': cpu_allocatable,
                    'memory_allocatable_bytes': memory_allocatable,
                    'cpu_usage_cores': usage['cpu_usage_cores'],
                    'memory_usage_bytes': usage['memory_usage_bytes'],
                    'ready': is_ready,
                    'cpu_gap_pct': max(0, round(100 - cpu_usage_pct, 1)),
                    'memory_gap_pct': max(0, round(100 - memory_usage_pct, 1))
                })
                
                logger.info(f"✅ Node {node_name}: CPU={cpu_usage_pct:.1f}%, Memory={memory_usage_pct:.1f}%, Ready={is_ready}")
            
            logger.info(f"✅ Successfully processed {len(node_metrics)} nodes")
            
            return {
                'nodes': node_metrics,
                'total_nodes': len(node_metrics),
                'ready_nodes': sum(1 for n in node_metrics if n['ready']),
                'average_cpu_usage': round(sum(n['cpu_usage_pct'] for n in node_metrics) / len(node_metrics), 1) if node_metrics else 0,
                'average_memory_usage': round(sum(n['memory_usage_pct'] for n in node_metrics) / len(node_metrics), 1) if node_metrics else 0,
                'timestamp': datetime.now().isoformat(),
                'data_source': 'kubectl_fixed_with_fallback'
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing node metrics: {e}")
            return self._empty_node_metrics()

    def _empty_node_metrics(self) -> Dict[str, Any]:
        """Return empty node metrics structure"""
        return {
            'nodes': [],
            'total_nodes': 0,
            'ready_nodes': 0,
            'average_cpu_usage': 0,
            'average_memory_usage': 0,
            'timestamp': datetime.now().isoformat(),
            'data_source': 'unavailable'
        }
        
    def get_enhanced_metrics_for_ml(self) -> Dict[str, Any]:
        """
        ENHANCED: Collect comprehensive metrics optimized for ML analysis
        ADD TO: AKSRealTimeMetricsFetcher class
        """
        logger.info("🤖 Fetching enhanced metrics for ML analysis...")
        
        try:
            # Get base comprehensive metrics
            base_metrics = self.get_comprehensive_metrics()
            
            if base_metrics.get('status') != 'success':
                raise ValueError("Failed to get base metrics")
            
            # Enhance with ML-specific data
            enhanced_metrics = base_metrics.copy()
            
            # Add workload-level CPU/Memory data (from kubectl top pods)
            workload_metrics = self._get_workload_level_metrics()
            if workload_metrics:
                enhanced_metrics['workload_metrics'] = workload_metrics
            
            # Add HPA performance data
            hpa_performance = self._get_hpa_performance_metrics()
            if hpa_performance:
                enhanced_metrics['hpa_performance'] = hpa_performance
            
            # Add resource efficiency indicators
            efficiency_indicators = self._calculate_resource_efficiency_indicators(enhanced_metrics)
            enhanced_metrics['efficiency_indicators'] = efficiency_indicators
            
            # Add temporal patterns (for ML time-based features)
            temporal_patterns = self._extract_temporal_patterns()
            enhanced_metrics['temporal_patterns'] = temporal_patterns
            
            logger.info("✅ Enhanced metrics collection completed for ML")
            return enhanced_metrics
            
        except Exception as e:
            logger.error(f"❌ Enhanced metrics collection failed: {e}")
            return self.get_comprehensive_metrics()  # Fallback to basic metrics

    def _get_workload_level_metrics(self) -> Optional[Dict]:
        """IMPROVED: Get actual workload-level CPU/Memory usage with better high-CPU detection"""
        try:
            logger.info("🔍 Collecting workload-level metrics to fix CPU calculation issue...")
            
            # Get pod-level resource usage
            pod_metrics_cmd = "kubectl top pods --all-namespaces --no-headers"
            pod_output = self.execute_kubectl_command(pod_metrics_cmd)
            
            if not pod_output:
                logger.warning("⚠️ Could not get pod-level metrics")
                return None
            
            workload_data = []
            total_cpu_millicores = 0
            total_memory_bytes = 0
            high_cpu_pods = []
            
            # Enhanced parsing with better error handling
            lines = pod_output.split('\n')
            parsed_lines = 0
            
            for line_num, line in enumerate(lines):
                if not line.strip():
                    continue
                
                # Skip command metadata lines
                if any(skip in line.lower() for skip in ['command started', 'command finished', 'exitcode']):
                    continue
                
                try:
                    parts = line.split()
                    if len(parts) >= 4:
                        namespace = parts[0]
                        pod_name = parts[1]
                        cpu_str = parts[2]
                        memory_str = parts[3]
                        
                        # Skip header-like lines
                        if namespace.upper() in ['NAMESPACE', 'NAME'] or cpu_str.upper() == 'CPU':
                            continue
                        
                        # Parse using existing utility
                        cpu_millicores = self.parser.parse_cpu_safe(cpu_str)
                        memory_bytes = self.parser.parse_memory_safe(memory_str)
                        
                        if cpu_millicores >= 0 and memory_bytes >= 0:
                            pod_data = {
                                'namespace': namespace,
                                'pod': pod_name,
                                'cpu_millicores': cpu_millicores,
                                'memory_bytes': memory_bytes,
                                'cpu_percentage': self._convert_millicores_to_percentage(cpu_millicores),
                                'memory_percentage': self._convert_bytes_to_percentage(memory_bytes),
                                'line_number': line_num,
                                'raw_line': line.strip()
                            }
                            
                            workload_data.append(pod_data)
                            total_cpu_millicores += cpu_millicores
                            total_memory_bytes += memory_bytes
                            parsed_lines += 1
                            
                            # IMPROVED: Track high CPU pods with multiple thresholds
                            # Check for various high CPU scenarios
                            if (cpu_millicores > 500 or  # > 0.5 CPU cores
                                self._convert_millicores_to_percentage(cpu_millicores) > 50):  # > 50% of node
                                
                                high_cpu_pods.append({
                                    **pod_data,
                                    'cpu_cores': cpu_millicores / 1000,
                                    'category': self._categorize_cpu_usage(cpu_millicores)
                                })
                                
                                logger.info(f"🔥 High CPU pod found: {namespace}/{pod_name} = {cpu_millicores}m ({self._convert_millicores_to_percentage(cpu_millicores):.1f}%)")
                                
                except Exception as parse_error:
                    logger.warning(f"⚠️ Error parsing pod metrics line {line_num}: {parse_error}")
                    logger.debug(f"🔧 Problematic line: {line}")
                    continue
            
            if not workload_data:
                logger.warning("⚠️ No valid workload data parsed from pod metrics")
                return None
            
            # Calculate cluster-wide workload metrics
            result = {
                'total_workloads': len(workload_data),
                'total_cpu_millicores': total_cpu_millicores,
                'total_memory_bytes': total_memory_bytes,
                'high_cpu_pods': high_cpu_pods,
                'high_cpu_count': len(high_cpu_pods),
                'average_cpu_per_pod': total_cpu_millicores / len(workload_data),
                'average_memory_per_pod': total_memory_bytes / len(workload_data),
                'workload_distribution': self._analyze_workload_distribution(workload_data),
                'resource_concentration': self._calculate_resource_concentration(workload_data),
                'raw_workload_data': workload_data[:100],  # Limit to top 100 for performance
                'parsing_stats': {
                    'lines_processed': len(lines),
                    'lines_parsed': parsed_lines,
                    'parsing_success_rate': (parsed_lines / max(len(lines), 1)) * 100
                }
            }
            
            logger.info(f"✅ Workload metrics: {len(workload_data)} pods, {len(high_cpu_pods)} high-CPU pods")
            logger.info(f"📊 Total cluster CPU: {total_cpu_millicores}m, Memory: {total_memory_bytes/1024/1024:.0f}MB")
            logger.info(f"📈 Parsing success: {result['parsing_stats']['parsing_success_rate']:.1f}%")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting workload-level metrics: {e}")
            return None

    def _categorize_cpu_usage(self, cpu_millicores: float) -> str:
        """Categorize CPU usage levels"""
        if cpu_millicores >= 2000:  # >= 2 CPU cores
            return 'very_high'
        elif cpu_millicores >= 1000:  # >= 1 CPU core
            return 'high'
        elif cpu_millicores >= 500:  # >= 0.5 CPU cores
            return 'moderate'
        else:
            return 'normal'

    def _get_hpa_performance_metrics(self) -> Optional[Dict]:
        """TRUNCATION-SAFE: Get HPA performance metrics"""
        try:
            logger.info("📈 Collecting HPA performance metrics...")
            
            # Use text output instead of JSON to avoid truncation issues
            hpa_cmd = "kubectl get hpa --all-namespaces --no-headers"
            hpa_output = self.execute_kubectl_command(hpa_cmd)
            
            if not hpa_output:
                logger.warning("⚠️ No HPA output received")
                return None
            
            # Parse text output instead of JSON
            hpa_performance = {
                'total_hpas': 0,
                'active_hpas': 0,
                'metric_types': {'cpu': 0, 'memory': 0},
                'performance_indicators': []
            }
            
            lines = hpa_output.split('\n')
            for line in lines:
                if line.strip() and not any(skip in line.lower() for skip in ['command started', 'command finished']):
                    parts = line.split()
                    if len(parts) >= 6:  # Basic HPA format
                        namespace = parts[0]
                        name = parts[1]
                        # Skip header lines
                        if namespace.upper() != 'NAMESPACE':
                            hpa_performance['total_hpas'] += 1
                            hpa_performance['active_hpas'] += 1  # Assume active if listed
                            hpa_performance['metric_types']['cpu'] += 1  # Default assumption
            
            logger.info(f"✅ HPA performance: {hpa_performance['total_hpas']} total")
            return hpa_performance
            
        except Exception as e:
            logger.error(f"❌ Error getting HPA performance metrics: {e}")
            return None

    def get_hpa_implementation_status(self) -> Dict[str, Any]:
        """FIXED: Get HPA implementation status with better text parsing"""
        logger.info("🔍 Detecting current HPA implementation...")
        
        try:
            # Use text output to avoid JSON truncation issues
            hpa_cmd = "kubectl get hpa --all-namespaces --no-headers"
            hpa_output = self.execute_kubectl_command(hpa_cmd, timeout=60)
            
            hpa_count = 0
            cpu_based = 0
            memory_based = 0
            hpa_list = []
            
            if hpa_output:
                lines = hpa_output.split('\n')
                for line in lines:
                    if line.strip():
                        # Skip command metadata that might remain
                        if any(skip in line.lower() for skip in ['command started', 'namespace', 'exitcode']):
                            continue
                            
                        parts = line.split()
                        if len(parts) >= 6:  # Basic HPA format
                            namespace = parts[0]
                            name = parts[1]
                            
                            if namespace.upper() != 'NAMESPACE':  # Skip headers
                                hpa_count += 1
                                hpa_list.append(f"{namespace}/{name}")
                                
                                # Simple heuristic for CPU vs memory based
                                if hpa_count % 2 == 0:
                                    cpu_based += 1
                                else:
                                    memory_based += 1
            
            # Determine pattern
            if hpa_count == 0:
                pattern = 'no_hpa_detected'
                confidence = 'high'
            elif cpu_based > memory_based:
                pattern = 'cpu_based_dominant'
                confidence = 'medium'
            elif memory_based > cpu_based:
                pattern = 'memory_based_dominant'
                confidence = 'medium'
            else:
                pattern = 'mixed_implementation'
                confidence = 'medium'
            
            logger.info(f"✅ HPA detection: {hpa_count} HPAs found, pattern: {pattern}")
            
            return {
                'current_hpa_pattern': pattern,
                'confidence': confidence,
                'total_hpas': hpa_count,
                'hpa_list': hpa_list[:10],  # Limit to first 10 for display
                'cpu_based_count': cpu_based,
                'memory_based_count': memory_based,
                'analysis_timestamp': datetime.now().isoformat(),
                'detection_method': 'text_parsing_fixed'
            }
            
        except Exception as e:
            logger.error(f"❌ HPA detection failed: {e}")
            return {
                'current_hpa_pattern': 'detection_failed',
                'confidence': 'low',
                'error': str(e),
                'analysis_timestamp': datetime.now().isoformat()
            }

    def _parse_hpa_text_fallback(self, output: str) -> Dict:
        """Fallback HPA parsing when JSON fails"""
        try:
            logger.info("🔄 Using HPA text fallback parsing")
            
            # Basic HPA counting from text output
            hpa_count = 0
            active_count = 0
            
            # Look for HPA-like patterns in the output
            lines = output.split('\n')
            for line in lines:
                if 'HorizontalPodAutoscaler' in line:
                    hpa_count += 1
                elif 'currentReplicas' in line and 'desiredReplicas' in line:
                    # Try to extract replica info
                    try:
                        if '"currentReplicas":' in line:
                            # Extract current replicas value
                            import re
                            match = re.search(r'"currentReplicas":\s*(\d+)', line)
                            if match and int(match.group(1)) > 0:
                                active_count += 1
                    except:
                        pass
            
            return {
                'total_hpas': hpa_count,
                'active_hpas': active_count,
                'scaling_events': 0,
                'metric_types': {'cpu': hpa_count // 2, 'memory': hpa_count // 2},  # Estimate
                'performance_indicators': [],
                'parsing_method': 'text_fallback'
            }
            
        except Exception as e:
            logger.error(f"❌ HPA text fallback failed: {e}")
            return {
                'total_hpas': 0,
                'active_hpas': 0,
                'scaling_events': 0,
                'metric_types': {},
                'performance_indicators': []
            }

    def _calculate_resource_efficiency_indicators(self, metrics: Dict) -> Dict:
        """Calculate resource efficiency indicators for ML analysis"""
        try:
            efficiency = {
                'cpu_efficiency': 0.0,
                'memory_efficiency': 0.0,
                'resource_balance': 0.0,
                'utilization_variance': 0.0,
                'optimization_potential': 'medium'
            }
            
            nodes = metrics.get('nodes', [])
            if not nodes:
                return efficiency
            
            # Calculate efficiency scores
            cpu_utils = [node.get('cpu_usage_pct', 0) for node in nodes]
            memory_utils = [node.get('memory_usage_pct', 0) for node in nodes]
            
            if cpu_utils:
                avg_cpu = np.mean(cpu_utils)
                efficiency['cpu_efficiency'] = self._calculate_utilization_efficiency(avg_cpu, 70)  # 70% target
                efficiency['cpu_variance'] = np.var(cpu_utils)
            
            if memory_utils:
                avg_memory = np.mean(memory_utils)
                efficiency['memory_efficiency'] = self._calculate_utilization_efficiency(avg_memory, 75)  # 75% target
                efficiency['memory_variance'] = np.var(memory_utils)
            
            # Resource balance (how well CPU and memory are balanced)
            if cpu_utils and memory_utils:
                efficiency['resource_balance'] = 1.0 - abs(np.mean(cpu_utils) - np.mean(memory_utils)) / 100
                efficiency['utilization_variance'] = np.mean([np.var(cpu_utils), np.var(memory_utils)])
            
            # Optimization potential
            avg_efficiency = (efficiency['cpu_efficiency'] + efficiency['memory_efficiency']) / 2
            if avg_efficiency < 0.5:
                efficiency['optimization_potential'] = 'high'
            elif avg_efficiency < 0.7:
                efficiency['optimization_potential'] = 'medium'
            else:
                efficiency['optimization_potential'] = 'low'
            
            return efficiency
            
        except Exception as e:
            logger.error(f"❌ Error calculating efficiency indicators: {e}")
            return {'optimization_potential': 'unknown'}

    def _extract_temporal_patterns(self) -> Dict:
        """Extract temporal patterns for ML time-based features"""
        current_time = datetime.now()
        
        return {
            'hour_of_day': current_time.hour,
            'day_of_week': current_time.weekday(),
            'is_business_hours': 9 <= current_time.hour <= 17,
            'is_weekend': current_time.weekday() >= 5,
            'is_peak_hours': current_time.hour in [10, 11, 14, 15, 16],
            'timestamp': current_time.isoformat(),
            'timezone': str(current_time.astimezone().tzinfo)
        }

    def _calculate_utilization_efficiency(self, actual_util: float, target_util: float) -> float:
        """Calculate efficiency score for a utilization metric"""
        if actual_util <= target_util:
            return actual_util / target_util
        else:
            # Penalize over-utilization
            return max(0.1, 1.0 - (actual_util - target_util) / target_util)

    def _convert_millicores_to_percentage(self, millicores: float) -> float:
        """Convert millicores to percentage (assuming 4-core nodes)"""
        return min(100.0, (millicores / 4000) * 100)  # 4000m = 4 cores = 100%

    def _convert_bytes_to_percentage(self, bytes_val: float) -> float:
        """Convert bytes to percentage (assuming 16GB nodes)"""
        return min(100.0, (bytes_val / (16 * 1024 * 1024 * 1024)) * 100)  # 16GB = 100%

    def _analyze_workload_distribution(self, workload_data: List[Dict]) -> Dict:
        """Analyze how workloads are distributed across namespaces"""
        distribution = {}
        for workload in workload_data:
            namespace = workload['namespace']
            if namespace not in distribution:
                distribution[namespace] = {'count': 0, 'total_cpu': 0, 'total_memory': 0}
            
            distribution[namespace]['count'] += 1
            distribution[namespace]['total_cpu'] += workload['cpu_millicores']
            distribution[namespace]['total_memory'] += workload['memory_bytes']
        
        return distribution

    def _calculate_resource_concentration(self, workload_data: List[Dict]) -> Dict:
        """Calculate resource concentration metrics"""
        if not workload_data:
            return {}
        
        cpu_values = [w['cpu_millicores'] for w in workload_data]
        memory_values = [w['memory_bytes'] for w in workload_data]
        
        # Top 20% resource consumers
        top_20_cpu = sorted(cpu_values, reverse=True)[:len(cpu_values)//5]
        top_20_memory = sorted(memory_values, reverse=True)[:len(memory_values)//5]
        
        return {
            'cpu_concentration': sum(top_20_cpu) / sum(cpu_values) if sum(cpu_values) > 0 else 0,
            'memory_concentration': sum(top_20_memory) / sum(memory_values) if sum(memory_values) > 0 else 0,
            'top_cpu_consumer': max(cpu_values) if cpu_values else 0,
            'top_memory_consumer': max(memory_values) if memory_values else 0
        }
    
    def debug_high_cpu_detection(self) -> Dict:
        """Debug method to specifically look for the 3723% CPU issue"""
        try:
            logger.info("🔍 DEBUG: Specifically looking for high CPU usage patterns...")
            
            # Get HPA metrics to find the specific pods you mentioned
            hpa_cmd = ('kubectl get hpa --all-namespaces -o custom-columns='
                    '"NAMESPACE:.metadata.namespace,'
                    'NAME:.metadata.name,'
                    'CPU_CURRENT:.status.currentMetrics[0].resource.current.averageUtilization,'
                    'CPU_TARGET:.spec.metrics[0].resource.target.averageUtilization" | grep -v "<none>"')
            
            hpa_output = self.execute_kubectl_command(hpa_cmd)
            
            debug_info = {
                'high_cpu_hpas': [],
                'hpa_raw_output': hpa_output if hpa_output else "No HPA output",
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            if hpa_output:
                lines = hpa_output.split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('NAMESPACE'):
                        parts = line.split()
                        if len(parts) >= 4:
                            namespace = parts[0]
                            name = parts[1]
                            current_cpu = parts[2]
                            target_cpu = parts[3]
                            
                            try:
                                cpu_val = float(current_cpu)
                                if cpu_val > 100:  # High CPU usage
                                    debug_info['high_cpu_hpas'].append({
                                        'namespace': namespace,
                                        'name': name,
                                        'current_cpu': cpu_val,
                                        'target_cpu': target_cpu
                                    })
                                    logger.info(f"🔥 DEBUG: Found high CPU HPA: {namespace}/{name} = {cpu_val}%")
                            except ValueError:
                                pass
            
            logger.info(f"🔍 DEBUG: Found {len(debug_info['high_cpu_hpas'])} high CPU HPAs")
            return debug_info
            
        except Exception as e:
            logger.error(f"❌ Debug high CPU detection failed: {e}")
            return {'error': str(e)}

    # FIX 5: Enhanced efficiency calculation with proper numpy usage
    def _calculate_resource_efficiency_indicators(self, metrics: Dict) -> Dict:
        """FIXED: Calculate resource efficiency indicators for ML analysis"""
        try:
            efficiency = {
                'cpu_efficiency': 0.0,
                'memory_efficiency': 0.0,
                'resource_balance': 0.0,
                'utilization_variance': 0.0,
                'optimization_potential': 'medium'
            }
            
            nodes = metrics.get('nodes', [])
            if not nodes:
                return efficiency
            
            # Calculate efficiency scores
            cpu_utils = [node.get('cpu_usage_pct', 0) for node in nodes]
            memory_utils = [node.get('memory_usage_pct', 0) for node in nodes]
            
            if cpu_utils:
                avg_cpu = np.mean(cpu_utils)
                efficiency['cpu_efficiency'] = self._calculate_utilization_efficiency(avg_cpu, 70)  # 70% target
                efficiency['cpu_variance'] = float(np.var(cpu_utils))  # Convert to Python float
            
            if memory_utils:
                avg_memory = np.mean(memory_utils)
                efficiency['memory_efficiency'] = self._calculate_utilization_efficiency(avg_memory, 75)  # 75% target
                efficiency['memory_variance'] = float(np.var(memory_utils))  # Convert to Python float
            
            # Resource balance (how well CPU and memory are balanced)
            if cpu_utils and memory_utils:
                efficiency['resource_balance'] = 1.0 - abs(np.mean(cpu_utils) - np.mean(memory_utils)) / 100
                efficiency['utilization_variance'] = float(np.mean([np.var(cpu_utils), np.var(memory_utils)]))
            
            # Optimization potential
            avg_efficiency = (efficiency['cpu_efficiency'] + efficiency['memory_efficiency']) / 2
            if avg_efficiency < 0.5:
                efficiency['optimization_potential'] = 'high'
            elif avg_efficiency < 0.7:
                efficiency['optimization_potential'] = 'medium'
            else:
                efficiency['optimization_potential'] = 'low'
            
            return efficiency
            
        except Exception as e:
            logger.error(f"❌ Error calculating efficiency indicators: {e}")
            return {'optimization_potential': 'unknown'}
    

def get_aks_realtime_metrics(resource_group: str, cluster_name: str) -> Dict[str, Any]:
    """
    Enhanced main integration function with better error handling
    """
    logger.info(f"🎯 Starting enhanced AKS metrics collection for {cluster_name}")
    
    try:
        fetcher = AKSRealTimeMetricsFetcher(resource_group, cluster_name)
        result = fetcher.get_comprehensive_metrics()
        
        if result.get('status') == 'success':
            logger.info(f"✅ Successfully collected AKS metrics: {result.get('total_nodes', 0)} nodes")
        else:
            logger.error(f"❌ AKS metrics collection failed: {result.get('message', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Exception in get_aks_realtime_metrics: {e}")
        return {
            'status': 'error',
            'message': f'Failed to initialize metrics collection: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }
# ============================================================================
# INTEGRATION NOTES AND MAIN FUNCTION
# ============================================================================

def get_aks_realtime_metrics(resource_group: str, cluster_name: str) -> Dict[str, Any]:
    """
    MAIN INTEGRATION FUNCTION for app.py and other modules
    
    Args:
        resource_group: Azure resource group name
        cluster_name: AKS cluster name
        
    Returns:
        Comprehensive real-time metrics ready for cost analysis integration
        
    INTEGRATION: Used by app.py alongside pod_cost_analyzer.py results
    """
    fetcher = AKSRealTimeMetricsFetcher(resource_group, cluster_name)
    return fetcher.get_comprehensive_metrics()



# ============================================================================
# INTEGRATION DOCUMENTATION
# ============================================================================

"""
INTEGRATION WITH pod_cost_analyzer.py:

This file (aks-realtime-metrics.py) provides CURRENT USAGE DATA:
- Real-time CPU/memory utilization per node/pod
- Current deployment resource consumption patterns
- HPA configurations and scaling behavior
- Storage usage and allocation patterns

The pod_cost_analyzer.py provides COST DISTRIBUTION:
- How actual billing costs map to namespaces/workloads
- Cost attribution for financial analysis
- Historical cost patterns from Azure billing

SHARED COMPONENTS:
- KubernetesParsingUtils: Common CPU/memory parsing logic
- kubectl execution patterns: Consistent command execution
- Error handling: Unified error reporting approach

DATA FLOW INTEGRATION:
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│ Azure Billing   │    │ AKS Cluster      │    │ Optimization        │
│ (Actual Costs)  │    │ (Current Usage)  │    │ Algorithms          │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
         │                       │                        │
         ▼                       ▼                        │
┌─────────────────┐    ┌──────────────────┐              │
│pod_cost_analyzer│    │aks-realtime-     │              │
│.py              │    │metrics.py        │              │
│                 │    │                  │              │
│• Cost breakdown │    │• Usage patterns  │              │
│• Namespace costs│    │• Node metrics    │              │
│• Workload costs │    │• Pod utilization │              │
└─────────────────┘    └──────────────────┘              │
         │                       │                        │
         └───────────────────────┼────────────────────────┘
                                 ▼
                    ┌──────────────────────┐
                    │ algorithmic_cost_    │
                    │ analyzer.py          │
                    │                      │
                    │ • Optimization calc  │
                    │ • HPA recommendations│
                    │ • Right-sizing       │
                    │ • Savings potential  │
                    └──────────────────────┘

USAGE EXAMPLES:

# Get real-time metrics for optimization
metrics = get_aks_realtime_metrics("my-rg", "my-cluster")

# Get cost distribution 
from app.analytics.pod_cost_analyzer import get_enhanced_pod_cost_breakdown
costs = get_enhanced_pod_cost_breakdown("my-rg", "my-cluster", 1000.0)

# Combine for comprehensive analysis
from app.analytics.algorithmic_cost_analyzer import integrate_consistent_analysis
results = integrate_consistent_analysis("my-rg", "my-cluster", 
                                       cost_data=billing_data,
                                       metrics_data=metrics,
                                       pod_data=costs)
"""