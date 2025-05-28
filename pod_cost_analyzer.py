"""
AKS Pod Cost Analyzer - YAML-to-JSON FIXED VERSION
==================================================
Using YAML output conversion to avoid JSON parsing issues
"""

import subprocess
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import re
import yaml

logger = logging.getLogger(__name__)

class PodCostAnalyzer:
    """Pod cost analyzer with YAML-to-JSON conversion - ULTIMATE FIX"""

    def __init__(self, resource_group: str, cluster_name: str):
        self.resource_group = resource_group
        self.cluster_name = cluster_name
        self.timeout = 45

    def _safe_kubectl_command(self, kubectl_cmd: str, timeout: int = None) -> Optional[str]:
        """Execute kubectl commands via az aks command invoke - FIXED"""
        if timeout is None:
            timeout = self.timeout
            
        try:
            # CRITICAL FIX: Use proper command structure without shell interpretation
            full_cmd = [
                'az', 'aks', 'command', 'invoke',
                '--resource-group', self.resource_group,
                '--name', self.cluster_name,
                '--command', kubectl_cmd
            ]
            
            logger.debug(f"Executing command: {kubectl_cmd}")
            
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode != 0:
                logger.warning(f"kubectl command failed (exit {result.returncode}): {kubectl_cmd}")
                if result.stderr:
                    logger.warning(f"Error output: {result.stderr.strip()}")
                return None
                
            output = result.stdout.strip()
            if not output or output == "null" or output == "":
                logger.warning(f"Empty response from command: {kubectl_cmd}")
                return None
            
            # Check if output contains error messages
            if "error:" in output.lower() or "unknown" in output.lower():
                logger.error(f"Command error in output: {output[:200]}...")
                return None
                
            return output
                
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout}s: {kubectl_cmd}")
            return None
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return None

    def _safe_kubectl_yaml_command(self, kubectl_cmd: str, timeout: int = None) -> Optional[Dict]:
        """Execute kubectl commands with YAML output - FIXED"""
        try:
            # Add YAML output flag if not present
            if "-o yaml" not in kubectl_cmd and "--output=yaml" not in kubectl_cmd:
                yaml_cmd = f"{kubectl_cmd} -o yaml"
            else:
                yaml_cmd = kubectl_cmd
            
            output = self._safe_kubectl_command(yaml_cmd, timeout)
            if not output:
                return None
            
            # Extract YAML content from az aks command invoke output
            lines = output.split('\n')
            yaml_start = -1
            
            # Find where YAML content starts
            for i, line in enumerate(lines):
                if any(marker in line for marker in ['apiVersion:', 'kind:', 'items:']):
                    yaml_start = i
                    break
            
            if yaml_start >= 0:
                yaml_content = '\n'.join(lines[yaml_start:])
                try:
                    yaml_data = yaml.safe_load(yaml_content)
                    return yaml_data
                except yaml.YAMLError as e:
                    logger.error(f"YAML parsing error: {e}")
                    return None
            else:
                logger.warning("No YAML content found in output")
                return None
                
        except Exception as e:
            logger.error(f"YAML command execution error: {e}")
            return None

    def analyze_pod_costs(self, total_node_cost: float) -> Optional[Dict]:
        """Enhanced analysis with YAML-to-JSON conversion"""
        logger.info(f"🔍 Starting YAML-FIXED pod cost analysis for {self.cluster_name}")
        logger.info(f"💰 Total node cost to distribute: ${total_node_cost:.2f}")
        
        start_time = time.time()

        try:
            # Method 1: Try container usage analysis (text-based since kubectl top doesn't support YAML)
            logger.info("🔬 Attempting container usage analysis...")
            result = self._analyze_by_container_usage_text(total_node_cost)
            if result:
                logger.info(f"✅ Container usage analysis completed in {time.time() - start_time:.1f}s")
                result['analysis_method'] = 'container_usage'
                result['accuracy_level'] = 'Very High'
                return result

            # Method 2: Try YAML-based pod resource analysis
            logger.info("📋 Attempting YAML pod resource analysis...")
            result = self._analyze_by_pod_resources(total_node_cost)
            if result:
                logger.info(f"✅ YAML Pod resource analysis completed in {time.time() - start_time:.1f}s")
                result['analysis_method'] = 'pod_resources'
                result['accuracy_level'] = 'High'
                return result

            # Method 3: Fallback to text-based pod count analysis
            logger.info("🔢 Attempting text-based pod count analysis...")
            result = self._analyze_by_pod_count(total_node_cost)
            if result:
                logger.info(f"✅ Pod count analysis completed in {time.time() - start_time:.1f}s")
                result['analysis_method'] = 'pod_count_text'
                result['accuracy_level'] = 'Good'
                return result

            logger.error("❌ All analysis methods failed")
            return None

        except Exception as e:
            logger.error(f"💥 Pod cost analysis failed: {e}")
            return None

    def _analyze_by_pod_resources(self, total_cost: float) -> Optional[Dict]:
        """Pod resource analysis using YAML output - FIXED"""
        try:
            yaml_data = self._safe_kubectl_yaml_command('kubectl get pods --all-namespaces')
            
            if not yaml_data:
                logger.warning("⚠️ Pod YAML listing not available")
                return None

            namespace_pods = {}
            total_pods = 0
            
            # Process YAML data structure
            if isinstance(yaml_data, dict) and 'items' in yaml_data:
                for item in yaml_data['items']:
                    if 'metadata' in item:
                        namespace = item['metadata'].get('namespace', 'default')
                        namespace_pods[namespace] = namespace_pods.get(namespace, 0) + 1
                        total_pods += 1

            if total_pods == 0:
                return None

            # Calculate weighted distribution
            namespace_costs = {}
            total_weight = 0
            
            for namespace, pod_count in namespace_pods.items():
                weight = self._get_namespace_weight(namespace)
                total_weight += pod_count * weight

            for namespace, pod_count in namespace_pods.items():
                weight = self._get_namespace_weight(namespace)
                weighted_pods = pod_count * weight
                cost_share = (weighted_pods / total_weight) * total_cost if total_weight > 0 else 0
                namespace_costs[namespace] = max(cost_share, 0.01)

            logger.info(f"📊 YAML resource analysis: {len(namespace_costs)} namespaces, ${total_cost:.2f} distributed")
            
            return {
                'namespace_costs': namespace_costs,
                'total_pods_analyzed': total_pods,
                'total_namespaces': len(namespace_pods)
            }

        except Exception as e:
            logger.error(f"❌ YAML Pod resource analysis error: {e}")
            return None

    def _analyze_by_container_usage_text(self, total_cost: float) -> Optional[Dict]:
        """Text-based container usage analysis"""
        try:
            output = self._safe_kubectl_command("kubectl top pods --all-namespaces --no-headers")
            
            if not output:
                logger.warning("⚠️ Pod usage metrics not available")
                return None

            pods = []
            lines = output.split('\n')
            
            for line in lines:
                if not line.strip():
                    continue
                    
                try:
                    parts = line.split()
                    if len(parts) < 4:
                        continue

                    namespace = parts[0]
                    pod_name = parts[1]
                    cpu_str = parts[2]
                    memory_str = parts[3]

                    # Skip header lines
                    if any(header in line.upper() for header in ['NAMESPACE', 'NAME', 'CPU', 'MEMORY']):
                        continue
                        
                    # Skip lines with date patterns
                    if self._contains_date_pattern(cpu_str) or self._contains_date_pattern(memory_str):
                        continue

                    cpu_usage = self._parse_cpu_safe(cpu_str)
                    memory_usage = self._parse_memory_safe(memory_str)

                    if cpu_usage >= 0 and memory_usage >= 0:
                        pods.append({
                            'namespace': namespace,
                            'pod': pod_name,
                            'cpu_millicores': cpu_usage,
                            'memory_bytes': memory_usage
                        })

                except (ValueError, IndexError):
                    continue

            if not pods:
                logger.warning("⚠️ No valid pod usage data parsed from text")
                return None

            logger.info(f"📊 Text analyzed {len(pods)} pods across namespaces")
            return self._calculate_cost_by_usage(pods, total_cost)

        except Exception as e:
            logger.error(f"❌ Text Container analysis error: {e}")
            return None

    def _analyze_by_pod_count(self, total_cost: float) -> Optional[Dict]:
        """Text-based pod count analysis"""
        try:
            output = self._safe_kubectl_command("kubectl get pods --all-namespaces --no-headers")
            
            if not output:
                logger.warning("⚠️ Pod listing not available")
                return None

            namespace_data = {}
            total_pods = 0
            
            for line in output.split('\n'):
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        namespace = parts[0]
                        
                        if namespace.upper() in ['NAMESPACE', 'NAME']:
                            continue
                        
                        if namespace not in namespace_data:
                            namespace_data[namespace] = {
                                'pods': 0,
                                'weight': self._get_namespace_weight(namespace)
                            }
                        
                        namespace_data[namespace]['pods'] += 1
                        total_pods += 1

            if total_pods == 0:
                return None

            # Calculate weighted distribution
            total_weighted_pods = sum(
                data['pods'] * data['weight'] 
                for data in namespace_data.values()
            )
            
            namespace_costs = {}
            for namespace, data in namespace_data.items():
                weighted_pods = data['pods'] * data['weight']
                cost_share = (weighted_pods / total_weighted_pods) * total_cost if total_weighted_pods > 0 else 0
                namespace_costs[namespace] = max(cost_share, 0.01)

            logger.info(f"📊 Text pod count analysis: Distributed ${total_cost:.2f} across {len(namespace_costs)} namespaces")
            
            return {
                'namespace_costs': namespace_costs,
                'total_pods_analyzed': total_pods,
                'total_namespaces': len(namespace_data)
            }

        except Exception as e:
            logger.error(f"❌ Text Pod count analysis error: {e}")
            return None

    def _contains_date_pattern(self, text: str) -> bool:
        """Check if text contains date patterns"""
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',
            r'\d{2}/\d{2}/\d{4}',
            r'\d{2}:\d{2}:\d{2}',
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)',
            r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)'
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _parse_cpu_safe(self, cpu_str: str) -> float:
        """Enhanced CPU parsing"""
        if not cpu_str or cpu_str.strip() == '':
            return 0
            
        cpu_str = cpu_str.strip().lower()
        
        if any(skip in cpu_str for skip in ['cpu', 'namespace', 'name', 'memory']):
            return 0
            
        if self._contains_date_pattern(cpu_str):
            return 0
            
        if not any(c.isdigit() for c in cpu_str):
            return 0

        try:
            if cpu_str.endswith('m'):
                return max(0, float(cpu_str[:-1]))
            elif cpu_str.endswith('u'):
                return max(0, float(cpu_str[:-1]) / 1000)
            elif cpu_str.endswith('n'):
                return max(0, float(cpu_str[:-1]) / 1000000)
            else:
                return max(0, float(cpu_str) * 1000)
        except (ValueError, TypeError):
            return 0

    def _parse_memory_safe(self, memory_str: str) -> float:
        """Enhanced memory parsing"""
        if not memory_str or memory_str.strip() == '':
            return 0
            
        memory_str = memory_str.strip()
        
        if any(skip in memory_str.lower() for skip in ['memory', 'namespace', 'name', 'cpu']):
            return 0
            
        if self._contains_date_pattern(memory_str):
            return 0
            
        if not any(c.isdigit() for c in memory_str):
            return 0

        try:
            if memory_str.endswith('Ki'):
                return max(0, float(memory_str[:-2]) * 1024)
            elif memory_str.endswith('Mi'):
                return max(0, float(memory_str[:-2]) * 1024 * 1024)
            elif memory_str.endswith('Gi'):
                return max(0, float(memory_str[:-2]) * 1024 * 1024 * 1024)
            elif memory_str.endswith('Ti'):
                return max(0, float(memory_str[:-2]) * 1024 * 1024 * 1024 * 1024)
            else:
                return max(0, float(memory_str))
        except (ValueError, TypeError):
            return 0

    def _get_namespace_weight(self, namespace: str) -> float:
        """Assign weights to namespaces"""
        namespace_lower = namespace.lower()
        
        if namespace_lower in ['kube-system', 'kube-public', 'kube-node-lease', 'azure-system']:
            return 0.3
        
        if any(keyword in namespace_lower for keyword in ['prod', 'production', 'live']):
            return 2.5
        
        if any(keyword in namespace_lower for keyword in ['dev', 'test', 'staging', 'qa', 'uat']):
            return 1.5
        
        return 1.0

    def _calculate_cost_by_usage(self, pods: List[Dict], total_cost: float) -> Dict:
        """Calculate cost distribution based on pod usage"""
        namespace_usage = {}
        total_cpu = 0
        total_memory = 0

        for pod in pods:
            namespace = pod['namespace']
            cpu = pod['cpu_millicores']
            memory = pod['memory_bytes']

            if namespace not in namespace_usage:
                namespace_usage[namespace] = {'cpu': 0, 'memory': 0, 'pods': 0}

            namespace_usage[namespace]['cpu'] += cpu
            namespace_usage[namespace]['memory'] += memory
            namespace_usage[namespace]['pods'] += 1
            
            total_cpu += cpu
            total_memory += memory

        namespace_costs = {}
        for namespace, usage in namespace_usage.items():
            cpu_weight = (usage['cpu'] / total_cpu) * 0.7 if total_cpu > 0 else 0
            memory_weight = (usage['memory'] / total_memory) * 0.3 if total_memory > 0 else 0
            cost_allocation = (cpu_weight + memory_weight) * total_cost
            namespace_costs[namespace] = max(cost_allocation, 0.01)

        return {
            'namespace_costs': namespace_costs,
            'total_pods_analyzed': len(pods),
            'total_namespaces': len(namespace_usage),
            'usage_distribution': namespace_usage,
            'total_cpu_millicores': total_cpu,
            'total_memory_bytes': total_memory
        }


class WorkloadCostAnalyzer:
    """Enhanced workload analyzer using YAML-to-JSON conversion"""

    def __init__(self, resource_group: str, cluster_name: str):
        self.resource_group = resource_group
        self.cluster_name = cluster_name
        self.pod_analyzer = PodCostAnalyzer(resource_group, cluster_name)

    def _safe_kubectl_command(self, kubectl_cmd: str, timeout: int = None) -> Optional[str]:
        """Delegate to pod_analyzer's method"""
        return self.pod_analyzer._safe_kubectl_command(kubectl_cmd, timeout)

    def _safe_kubectl_yaml_command(self, kubectl_cmd: str, timeout: int = None) -> Optional[Dict]:
        """Delegate to pod_analyzer's method"""
        return self.pod_analyzer._safe_kubectl_yaml_command(kubectl_cmd, timeout)

    def analyze_workload_costs(self, total_node_cost: float) -> Optional[Dict]:
        """Analyze workload costs using YAML conversion"""
        logger.info("🚀 Starting YAML-FIXED workload cost analysis...")
        
        try:
            # Get workload information using YAML method
            deployments = self._get_workloads('deployment')
            statefulsets = self._get_workloads('statefulset')
            daemonsets = self._get_workloads('daemonset')

            # Get pod cost data
            pod_analysis = self.pod_analyzer.analyze_pod_costs(total_node_cost)
            if not pod_analysis:
                return None

            # Map pods to workloads
            all_workloads = deployments + statefulsets + daemonsets
            workload_costs = self._map_pods_to_workloads(all_workloads, pod_analysis)

            return {
                'workload_costs': workload_costs,
                'deployments_count': len(deployments),
                'statefulsets_count': len(statefulsets),
                'daemonsets_count': len(daemonsets),
                'namespace_summary': pod_analysis.get('namespace_costs', {}),
                'analysis_method': pod_analysis.get('analysis_method', 'unknown'),
                'accuracy_level': pod_analysis.get('accuracy_level', 'unknown')
            }

        except Exception as e:
            logger.error(f"❌ YAML-FIXED Workload analysis error: {e}")
            return None

    def _get_workloads(self, workload_type: str) -> List[Dict]:
        """Get workload information using YAML conversion - FIXED"""
        try:
            # CRITICAL FIX: Ensure correct resource type pluralization
            resource_types_map = {
                'deployment': 'deployments',
                'statefulset': 'statefulsets', 
                'daemonset': 'daemonsets',
                'pod': 'pods'
            }
            
            correct_resource_type = resource_types_map.get(workload_type, workload_type)
            
            # Use correct resource type
            cmd = f'kubectl get {correct_resource_type} --all-namespaces'
            yaml_data = self._safe_kubectl_yaml_command(cmd, timeout=30)
            
            if not yaml_data:
                logger.warning(f"⚠️ Could not get {workload_type}s via YAML: Empty response")
                return []

            workloads = []
            
            # Process YAML data structure
            if isinstance(yaml_data, dict) and 'items' in yaml_data:
                for item in yaml_data['items']:
                    if 'metadata' in item:
                        namespace = item['metadata'].get('namespace', 'default')
                        name = item['metadata'].get('name', 'unknown')
                        
                        # Get replica info from spec
                        replicas = 1
                        if 'spec' in item:
                            if 'replicas' in item['spec']:
                                replicas = item['spec']['replicas']
                            elif 'status' in item and 'replicas' in item['status']:
                                replicas = item['status']['replicas']

                        workloads.append({
                            'type': workload_type.title(),
                            'namespace': namespace,
                            'name': name,
                            'replicas': replicas
                        })
                        
            logger.info(f"Found {len(workloads)} {workload_type}s via YAML")
            return workloads

        except Exception as e:
            logger.warning(f"⚠️ Could not get {workload_type}s via YAML: {e}")
            return []

    def _map_pods_to_workloads(self, workloads: List[Dict], pod_analysis: Dict) -> Dict:
        """Map pod costs to workloads"""
        workload_costs = {}
        namespace_costs = pod_analysis.get('namespace_costs', {})

        namespace_workloads = {}
        for workload in workloads:
            namespace = workload['namespace']
            if namespace not in namespace_workloads:
                namespace_workloads[namespace] = []
            namespace_workloads[namespace].append(workload)

        for namespace, ns_workloads in namespace_workloads.items():
            namespace_cost = namespace_costs.get(namespace, 0)
            if len(ns_workloads) > 0:
                cost_per_workload = namespace_cost / len(ns_workloads)
                
                for workload in ns_workloads:
                    workload_key = f"{namespace}/{workload['name']}"
                    workload_costs[workload_key] = {
                        'cost': cost_per_workload,
                        'type': workload['type'],
                        'namespace': namespace,
                        'name': workload['name'],
                        'replicas': workload['replicas']
                    }

        return workload_costs


def get_enhanced_pod_cost_breakdown(resource_group: str, cluster_name: str, total_node_cost: float) -> Optional[Dict]:
    """
    YAML-FIXED Main integration function for AKS Cost Intelligence tool
    """
    logger.info(f"🔍 Starting YAML-FIXED enhanced pod cost analysis")
    logger.info(f"💰 Distributing ${total_node_cost:.2f} across pods")
    
    try:
        workload_analyzer = WorkloadCostAnalyzer(resource_group, cluster_name)
        
        workload_result = workload_analyzer.analyze_workload_costs(total_node_cost)
        
        if workload_result:
            logger.info(f"✅ YAML-FIXED Workload analysis successful")
            return {
                'analysis_type': 'workload',
                'success': True,
                **workload_result
            }

        pod_analyzer = PodCostAnalyzer(resource_group, cluster_name)
        pod_result = pod_analyzer.analyze_pod_costs(total_node_cost)
        
        if pod_result:
            logger.info(f"✅ YAML-FIXED Pod analysis successful")
            return {
                'analysis_type': 'pod',
                'success': True,
                **pod_result
            }

        logger.warning("⚠️ YAML-FIXED Pod cost analysis not available")
        return None

    except Exception as e:
        logger.error(f"❌ YAML-FIXED Pod cost analysis failed: {e}")
        return None
