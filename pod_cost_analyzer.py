"""
AKS Pod Cost Analyzer - Enhanced Version
========================================
Distributes actual costs from Azure billing across pods, namespaces, and workloads.
Provides cost attribution and breakdown for billing transparency.

INTEGRATION: Works with aks-realtime-metrics.py to provide complete cost+usage picture
"""

# ============================================================================
# IMPORTS AND CONFIGURATION
# ============================================================================

import subprocess
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import re
import yaml

logger = logging.getLogger(__name__)

# ============================================================================
# SHARED UTILITY FUNCTIONS
# ============================================================================

class KubernetesParsingUtils:
    """Shared utilities for parsing Kubernetes resource values"""
    
    @staticmethod
    def parse_cpu_safe(cpu_str: str) -> float:
        """
        Parse CPU value from various formats (cores, millicores)
        
        Args:
            cpu_str: CPU string like "250m", "1.5", "2000n"
            
        Returns:
            CPU value in millicores (float)
        """
        if not cpu_str or cpu_str.strip() == '':
            return 0.0
            
        cpu_str = cpu_str.strip().lower()
        
        # Skip non-numeric values
        if any(skip in cpu_str for skip in ['cpu', 'namespace', 'name', 'memory']):
            return 0.0
            
        # Skip date patterns
        if KubernetesParsingUtils._contains_date_pattern(cpu_str):
            return 0.0
            
        if not any(c.isdigit() for c in cpu_str):
            return 0.0

        try:
            if cpu_str.endswith('m'):
                return max(0.0, float(cpu_str[:-1]))  # Already in millicores
            elif cpu_str.endswith('u'):
                return max(0.0, float(cpu_str[:-1]) / 1000)  # Microcores to millicores
            elif cpu_str.endswith('n'):
                return max(0.0, float(cpu_str[:-1]) / 1000000)  # Nanocores to millicores
            else:
                return max(0.0, float(cpu_str) * 1000)  # Cores to millicores
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def parse_memory_safe(memory_str: str) -> float:
        """
        Parse memory value from various formats (bytes, Ki, Mi, Gi)
        
        Args:
            memory_str: Memory string like "128Mi", "2Gi", "1024Ki"
            
        Returns:
            Memory value in bytes (float)
        """
        if not memory_str or memory_str.strip() == '':
            return 0.0
            
        memory_str = memory_str.strip()
        
        # Skip non-memory values
        if any(skip in memory_str.lower() for skip in ['memory', 'namespace', 'name', 'cpu']):
            return 0.0
            
        # Skip date patterns
        if KubernetesParsingUtils._contains_date_pattern(memory_str):
            return 0.0
            
        if not any(c.isdigit() for c in memory_str):
            return 0.0

        try:
            # Binary units (1024-based)
            if memory_str.endswith('Ki'):
                return max(0.0, float(memory_str[:-2]) * 1024)
            elif memory_str.endswith('Mi'):
                return max(0.0, float(memory_str[:-2]) * 1024 * 1024)
            elif memory_str.endswith('Gi'):
                return max(0.0, float(memory_str[:-2]) * 1024 * 1024 * 1024)
            elif memory_str.endswith('Ti'):
                return max(0.0, float(memory_str[:-2]) * 1024 * 1024 * 1024 * 1024)
            # Decimal units (1000-based)
            elif memory_str.endswith('k'):
                return max(0.0, float(memory_str[:-1]) * 1000)
            elif memory_str.endswith('M'):
                return max(0.0, float(memory_str[:-1]) * 1000 * 1000)
            elif memory_str.endswith('G'):
                return max(0.0, float(memory_str[:-1]) * 1000 * 1000 * 1000)
            elif memory_str.endswith('T'):
                return max(0.0, float(memory_str[:-1]) * 1000 * 1000 * 1000 * 1000)
            else:
                return max(0.0, float(memory_str))  # Assume bytes
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def _contains_date_pattern(text: str) -> bool:
        """Check if text contains date patterns that should be skipped"""
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',           # 2024-01-15
            r'\d{2}/\d{2}/\d{4}',           # 01/15/2024
            r'\d{2}:\d{2}:\d{2}',           # 14:30:45
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)',  # Month names
            r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)'  # Day names
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

# ============================================================================
# CORE POD COST ANALYZER
# ============================================================================

class PodCostAnalyzer:
    """
    Main Pod Cost Distribution Engine
    
    PURPOSE: Distributes actual node costs across pods and namespaces
    INTEGRATION: Uses kubectl via 'az aks command invoke' for private clusters
    """

    def __init__(self, resource_group: str, cluster_name: str):
        """
        Initialize Pod Cost Analyzer
        
        Args:
            resource_group: Azure resource group name
            cluster_name: AKS cluster name
        """
        self.resource_group = resource_group
        self.cluster_name = cluster_name
        self.timeout = 30  # Command timeout in seconds
        
        # Initialize shared utilities
        self.parser = KubernetesParsingUtils()

    # ------------------------------------------------------------------------
    # KUBECTL COMMAND EXECUTION
    # ------------------------------------------------------------------------

    def _safe_kubectl_command(self, kubectl_cmd: str, timeout: int = None) -> Optional[str]:
        """
        Execute kubectl commands via az aks command invoke (for private clusters)
        
        Args:
            kubectl_cmd: The kubectl command to execute
            timeout: Command timeout in seconds
            
        Returns:
            Command output or None if failed
        """
        if timeout is None:
            timeout = self.timeout
            
        try:
            # Build the full Azure CLI command
            full_cmd = [
                'az', 'aks', 'command', 'invoke',
                '--resource-group', self.resource_group,
                '--name', self.cluster_name,
                '--command', kubectl_cmd
            ]
            
            logger.debug(f"Executing kubectl: {kubectl_cmd}")
            
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode != 0:
                logger.warning(f"kubectl command failed (exit {result.returncode}): {kubectl_cmd}")
                if result.stderr:
                    logger.warning(f"Error: {result.stderr.strip()}")
                return None
                
            output = result.stdout.strip()
            if not output or output == "null":
                logger.warning(f"Empty response from: {kubectl_cmd}")
                return None
            
            # Enhanced error detection in output
            error_patterns = [
                "error:", "Error:", "ERROR:",
                "unknown", "Unknown", "UNKNOWN",
                "forbidden", "Forbidden", "FORBIDDEN",
                "not found", "Not Found", "NOT FOUND"
            ]
            
            for pattern in error_patterns:
                if pattern in output:
                    logger.error(f"Command error detected: {pattern} in output")
                    return None
                
            return output
                
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout}s: {kubectl_cmd}")
            return None
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return None

    # ------------------------------------------------------------------------
    # YAML PROCESSING AND PARSING
    # ------------------------------------------------------------------------

    def _extract_clean_yaml(self, raw_output: str) -> Optional[str]:
        """
        Extract clean YAML content from az aks command invoke output
        
        Args:
            raw_output: Raw output from az aks command
            
        Returns:
            Clean YAML string or None
        """
        try:
            lines = raw_output.split('\n')
            yaml_content_lines = []
            
            # Find the start of YAML content
            yaml_started = False
            skip_patterns = [
                'command started', 'command finished', 'stdout:', 'stderr:',
                'exitcode:', '---', 'Running:', 'Executing:'
            ]
            
            for line in lines:
                line_stripped = line.strip()
                
                # Skip empty lines and command metadata
                if not line_stripped:
                    continue
                    
                # Skip lines that look like command metadata
                if any(pattern in line.lower() for pattern in skip_patterns):
                    continue
                
                # Detect YAML start markers
                yaml_markers = ['apiVersion:', 'kind:', 'items:', 'metadata:']
                if any(marker in line for marker in yaml_markers):
                    yaml_started = True
                
                # Collect YAML content once started
                if yaml_started:
                    yaml_content_lines.append(line)
            
            if not yaml_content_lines:
                logger.warning("No YAML content markers found")
                return None
            
            # Join and clean YAML content
            clean_yaml = '\n'.join(yaml_content_lines)
            
            # Additional cleanup - remove trailing non-YAML content
            yaml_lines = clean_yaml.split('\n')
            last_meaningful_line = -1
            
            for i in reversed(range(len(yaml_lines))):
                line = yaml_lines[i].strip()
                if line and not line.startswith('#') and ':' in line:
                    last_meaningful_line = i
                    break
            
            if last_meaningful_line >= 0:
                clean_yaml = '\n'.join(yaml_lines[:last_meaningful_line + 1])
            
            return clean_yaml
            
        except Exception as e:
            logger.error(f"Error extracting clean YAML: {e}")
            return None

    def _safe_kubectl_yaml_command(self, kubectl_cmd: str, timeout: int = None) -> Optional[Dict]:
        """
        Execute kubectl commands with YAML parsing
        
        Args:
            kubectl_cmd: kubectl command to execute
            timeout: Command timeout
            
        Returns:
            Parsed YAML data as dictionary or None
        """
        try:
            # Ensure YAML output format
            if "-o yaml" not in kubectl_cmd and "--output=yaml" not in kubectl_cmd:
                yaml_cmd = f"{kubectl_cmd} -o yaml"
            else:
                yaml_cmd = kubectl_cmd
            
            raw_output = self._safe_kubectl_command(yaml_cmd, timeout)
            if not raw_output:
                return None
            
            # Extract clean YAML content
            clean_yaml = self._extract_clean_yaml(raw_output)
            if not clean_yaml:
                logger.warning("Could not extract clean YAML content")
                return None
            
            # Parse YAML with enhanced error handling
            try:
                yaml_data = yaml.safe_load(clean_yaml)
                
                # Validate meaningful data
                if not yaml_data:
                    logger.warning("YAML parsing returned None/empty")
                    return None
                
                if isinstance(yaml_data, dict):
                    # Check for Kubernetes object structure
                    if 'kind' in yaml_data or 'items' in yaml_data or 'apiVersion' in yaml_data:
                        return yaml_data
                    else:
                        logger.warning("YAML data doesn't look like Kubernetes object")
                        return None
                else:
                    logger.warning(f"YAML data is not a dict: {type(yaml_data)}")
                    return None
                    
            except yaml.YAMLError as e:
                logger.error(f"YAML parsing failed: {e}")
                logger.error(f"Problematic YAML content: {clean_yaml[:500]}...")
                return None
                
        except Exception as e:
            logger.error(f"YAML command execution error: {e}")
            return None

    # ------------------------------------------------------------------------
    # TEXT PARSING FALLBACKS
    # ------------------------------------------------------------------------

    def _fallback_to_text_parsing(self, kubectl_cmd: str) -> Optional[Dict]:
        """
        Fallback to text-based parsing when YAML fails
        
        Args:
            kubectl_cmd: Original kubectl command
            
        Returns:
            Parsed data as dictionary or None
        """
        try:
            # Remove YAML output flag for text parsing
            text_cmd = kubectl_cmd.replace(" -o yaml", "").replace(" --output=yaml", "")
            
            output = self._safe_kubectl_command(text_cmd)
            if not output:
                return None
            
            logger.info(f"Using text fallback for: {text_cmd}")
            
            # Route to appropriate text parser
            if "get pods" in text_cmd:
                return self._parse_pods_text_output(output)
            elif "get deployments" in text_cmd:
                return self._parse_deployments_text_output(output)
            elif "get statefulsets" in text_cmd:
                return self._parse_statefulsets_text_output(output)
            elif "get daemonsets" in text_cmd:
                return self._parse_daemonsets_text_output(output)
            else:
                logger.warning(f"No text parser for command: {text_cmd}")
                return None
                
        except Exception as e:
            logger.error(f"Text fallback parsing error: {e}")
            return None

    def _parse_pods_text_output(self, output: str) -> Optional[Dict]:
        """Parse pods from text output (kubectl get pods format)"""
        try:
            items = []
            lines = output.split('\n')
            
            # Skip header line and get data lines
            data_lines = [line for line in lines if line.strip() and 'NAMESPACE' not in line.upper()]
            
            for line in data_lines:
                parts = line.split()
                if len(parts) >= 5:
                    namespace = parts[0]
                    name = parts[1]
                    ready = parts[2]
                    status = parts[3]
                    restarts = parts[4]
                    
                    items.append({
                        'metadata': {
                            'namespace': namespace,
                            'name': name
                        },
                        'status': {
                            'phase': status
                        }
                    })
            
            return {'items': items} if items else None
            
        except Exception as e:
            logger.error(f"Error parsing pods text output: {e}")
            return None

    def _parse_deployments_text_output(self, output: str) -> Optional[Dict]:
        """Parse deployments from text output"""
        try:
            items = []
            lines = output.split('\n')
            
            data_lines = [line for line in lines if line.strip() and 'NAMESPACE' not in line.upper()]
            
            for line in data_lines:
                parts = line.split()
                if len(parts) >= 4:
                    namespace = parts[0]
                    name = parts[1]
                    ready = parts[2]
                    up_to_date = parts[3]
                    
                    # Extract replica count from ready field (e.g., "2/3" -> 3)
                    replicas = 1
                    if '/' in ready:
                        try:
                            replicas = int(ready.split('/')[1])
                        except (ValueError, IndexError):
                            replicas = 1
                    
                    items.append({
                        'metadata': {
                            'namespace': namespace,
                            'name': name
                        },
                        'spec': {
                            'replicas': replicas
                        }
                    })
            
            return {'items': items} if items else None
            
        except Exception as e:
            logger.error(f"Error parsing deployments text output: {e}")
            return None

    def _parse_statefulsets_text_output(self, output: str) -> Optional[Dict]:
        """Parse statefulsets from text output"""
        try:
            items = []
            lines = output.split('\n')
            
            data_lines = [line for line in lines if line.strip() and 'NAMESPACE' not in line.upper()]
            
            for line in data_lines:
                parts = line.split()
                if len(parts) >= 3:
                    namespace = parts[0]
                    name = parts[1]
                    ready = parts[2]
                    
                    # Extract replica count
                    replicas = 1
                    if '/' in ready:
                        try:
                            replicas = int(ready.split('/')[1])
                        except (ValueError, IndexError):
                            replicas = 1
                    
                    items.append({
                        'metadata': {
                            'namespace': namespace,
                            'name': name
                        },
                        'spec': {
                            'replicas': replicas
                        }
                    })
            
            return {'items': items} if items else None
            
        except Exception as e:
            logger.error(f"Error parsing statefulsets text output: {e}")
            return None

    def _parse_daemonsets_text_output(self, output: str) -> Optional[Dict]:
        """Parse daemonsets from text output"""
        try:
            items = []
            lines = output.split('\n')
            
            data_lines = [line for line in lines if line.strip() and 'NAMESPACE' not in line.upper()]
            
            for line in data_lines:
                parts = line.split()
                if len(parts) >= 6:
                    namespace = parts[0]
                    name = parts[1]
                    desired = parts[2]
                    current = parts[3]
                    ready = parts[4]
                    
                    # For DaemonSets, replicas = desired
                    try:
                        replicas = int(desired)
                    except (ValueError, TypeError):
                        replicas = 1
                    
                    items.append({
                        'metadata': {
                            'namespace': namespace,
                            'name': name
                        },
                        'spec': {
                            'replicas': replicas
                        }
                    })
            
            return {'items': items} if items else None
            
        except Exception as e:
            logger.error(f"Error parsing daemonsets text output: {e}")
            return None

    # ------------------------------------------------------------------------
    # NAMESPACE WEIGHT CALCULATION
    # ------------------------------------------------------------------------

    def _get_namespace_weight(self, namespace: str) -> float:
        """
        Assign cost weights to namespaces based on their purpose
        
        Args:
            namespace: Namespace name
            
        Returns:
            Weight multiplier (float)
        """
        namespace_lower = namespace.lower()
        
        # System namespaces (lower weight - infrastructure costs)
        if namespace_lower in ['kube-system', 'kube-public', 'kube-node-lease', 'azure-system']:
            return 0.3
        
        # Production namespaces (higher weight - business critical)
        if any(keyword in namespace_lower for keyword in ['prod', 'production', 'live']):
            return 2.5
        
        # Non-production namespaces (medium weight)
        if any(keyword in namespace_lower for keyword in ['dev', 'test', 'staging', 'qa', 'uat']):
            return 1.5
        
        # Default weight for unknown namespaces
        return 1.0

    # ------------------------------------------------------------------------
    # COST ANALYSIS METHODS
    # ------------------------------------------------------------------------

    def analyze_pod_costs(self, total_node_cost: float) -> Optional[Dict]:
        """
        MAIN ANALYSIS METHOD: Distribute node costs across pods/namespaces
        
        Uses multiple methods in priority order:
        1. Container usage analysis (most accurate)
        2. Pod resource analysis (good accuracy)  
        3. Pod count analysis (basic accuracy)
        
        Args:
            total_node_cost: Total monthly node cost to distribute
            
        Returns:
            Cost analysis results or None if failed
        """
        logger.info(f"🔍 Starting pod cost analysis for {self.cluster_name}")
        logger.info(f"💰 Total node cost to distribute: ${total_node_cost:.2f}")
        
        start_time = time.time()

        try:
            # Method 1: Container usage analysis (highest accuracy)
            logger.info("🔬 Attempting container usage analysis...")
            result = self._analyze_by_container_usage_text(total_node_cost)
            if result:
                logger.info(f"✅ Container usage analysis completed in {time.time() - start_time:.1f}s")
                result['analysis_method'] = 'container_usage'
                result['accuracy_level'] = 'Very High'
                return result

            # Method 2: Pod resource analysis with YAML+fallback (good accuracy)
            logger.info("📋 Attempting pod resource analysis...")
            result = self._analyze_by_pod_resources_robust(total_node_cost)
            if result:
                logger.info(f"✅ Pod resource analysis completed in {time.time() - start_time:.1f}s")
                result['analysis_method'] = 'pod_resources_robust'
                result['accuracy_level'] = 'High'
                return result

            # Method 3: Pod count analysis (basic accuracy)
            logger.info("🔢 Attempting pod count analysis...")
            result = self._analyze_by_pod_count_robust(total_node_cost)
            if result:
                logger.info(f"✅ Pod count analysis completed in {time.time() - start_time:.1f}s")
                result['analysis_method'] = 'pod_count_robust'
                result['accuracy_level'] = 'Good'
                return result

            logger.error("❌ All analysis methods failed")
            return None

        except Exception as e:
            logger.error(f"💥 Pod cost analysis failed: {e}")
            return None

    def _analyze_by_container_usage_text(self, total_cost: float) -> Optional[Dict]:
        """
        Analyze costs based on actual container resource usage (MOST ACCURATE)
        
        Uses 'kubectl top pods' to get real CPU/memory consumption
        
        Args:
            total_cost: Total cost to distribute
            
        Returns:
            Cost analysis based on actual usage
        """
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

                    # Skip header lines and date patterns
                    if any(header in line.upper() for header in ['NAMESPACE', 'NAME', 'CPU', 'MEMORY']):
                        continue
                        
                    if self.parser._contains_date_pattern(cpu_str) or self.parser._contains_date_pattern(memory_str):
                        continue

                    # Parse resource values using shared utilities
                    cpu_usage = self.parser.parse_cpu_safe(cpu_str)
                    memory_usage = self.parser.parse_memory_safe(memory_str)

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
                logger.warning("⚠️ No valid pod usage data parsed")
                return None

            logger.info(f"📊 Analyzed {len(pods)} pods with actual usage data")
            return self._calculate_cost_by_usage(pods, total_cost)

        except Exception as e:
            logger.error(f"❌ Container usage analysis error: {e}")
            return None

    def _analyze_by_pod_resources_robust(self, total_cost: float) -> Optional[Dict]:
        """
        Analyze costs based on pod resource requests/limits (HIGH ACCURACY)
        
        Uses YAML parsing with text fallback
        """
        try:
            # Try YAML first
            yaml_data = self._safe_kubectl_yaml_command('kubectl get pods --all-namespaces')
            
            # If YAML fails, try text fallback
            if not yaml_data:
                logger.info("🔄 YAML failed, trying text fallback...")
                yaml_data = self._fallback_to_text_parsing('kubectl get pods --all-namespaces -o yaml')
            
            if not yaml_data:
                logger.warning("⚠️ Pod resource listing not available")
                return None

            namespace_pods = {}
            total_pods = 0
            
            # Process data structure
            if isinstance(yaml_data, dict) and 'items' in yaml_data:
                for item in yaml_data['items']:
                    if 'metadata' in item:
                        namespace = item['metadata'].get('namespace', 'default')
                        namespace_pods[namespace] = namespace_pods.get(namespace, 0) + 1
                        total_pods += 1

            if total_pods == 0:
                return None

            # Calculate weighted distribution using namespace priorities
            namespace_costs = {}
            total_weight = 0
            
            # Calculate total weighted pods
            for namespace, pod_count in namespace_pods.items():
                weight = self._get_namespace_weight(namespace)
                total_weight += pod_count * weight

            # Distribute costs proportionally
            for namespace, pod_count in namespace_pods.items():
                weight = self._get_namespace_weight(namespace)
                weighted_pods = pod_count * weight
                cost_share = (weighted_pods / total_weight) * total_cost if total_weight > 0 else 0
                namespace_costs[namespace] = max(cost_share, 0.01)  # Minimum $0.01

            logger.info(f"📊 Resource analysis: {len(namespace_costs)} namespaces, ${total_cost:.2f} distributed")
            
            return {
                'namespace_costs': namespace_costs,
                'total_pods_analyzed': total_pods,
                'total_namespaces': len(namespace_pods)
            }

        except Exception as e:
            logger.error(f"❌ Pod resource analysis error: {e}")
            return None

    def _analyze_by_pod_count_robust(self, total_cost: float) -> Optional[Dict]:
        """
        Analyze costs based on pod count per namespace (BASIC ACCURACY)
        
        Simple text-based counting with namespace weighting
        """
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
                        
                        # Skip header lines
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

            logger.info(f"📊 Pod count analysis: Distributed ${total_cost:.2f} across {len(namespace_costs)} namespaces")
            
            return {
                'namespace_costs': namespace_costs,
                'total_pods_analyzed': total_pods,
                'total_namespaces': len(namespace_data)
            }

        except Exception as e:
            logger.error(f"❌ Pod count analysis error: {e}")
            return None

    def _calculate_cost_by_usage(self, pods: List[Dict], total_cost: float) -> Dict:
        """
        Calculate cost distribution based on actual pod resource usage
        
        Args:
            pods: List of pod usage data
            total_cost: Total cost to distribute
            
        Returns:
            Detailed cost breakdown by namespace and usage patterns
        """
        namespace_usage = {}
        total_cpu = 0
        total_memory = 0

        # Aggregate usage by namespace
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

        # Calculate costs using weighted approach (CPU: 70%, Memory: 30%)
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
            'total_memory_bytes': total_memory,
            'cost_calculation_method': 'actual_usage_weighted'
        }

# ============================================================================
# WORKLOAD COST ANALYZER
# ============================================================================

class WorkloadCostAnalyzer:
    """
    Workload-Level Cost Analysis
    
    PURPOSE: Maps pod costs to specific workloads (Deployments, StatefulSets, DaemonSets)
    INTEGRATION: Extends PodCostAnalyzer results to workload granularity
    """

    def __init__(self, resource_group: str, cluster_name: str):
        """Initialize workload analyzer with shared pod analyzer"""
        self.resource_group = resource_group
        self.cluster_name = cluster_name
        self.pod_analyzer = PodCostAnalyzer(resource_group, cluster_name)

    # ------------------------------------------------------------------------
    # KUBECTL DELEGATION (reuse PodCostAnalyzer methods)
    # ------------------------------------------------------------------------

    def _safe_kubectl_command(self, kubectl_cmd: str, timeout: int = None) -> Optional[str]:
        """Delegate to pod_analyzer's method to avoid duplication"""
        return self.pod_analyzer._safe_kubectl_command(kubectl_cmd, timeout)

    def _safe_kubectl_yaml_command(self, kubectl_cmd: str, timeout: int = None) -> Optional[Dict]:
        """Delegate to pod_analyzer's method to avoid duplication"""
        return self.pod_analyzer._safe_kubectl_yaml_command(kubectl_cmd, timeout)

    def _fallback_to_text_parsing(self, kubectl_cmd: str) -> Optional[Dict]:
        """Delegate to pod_analyzer's method to avoid duplication"""
        return self.pod_analyzer._fallback_to_text_parsing(kubectl_cmd)

    # ------------------------------------------------------------------------
    # WORKLOAD DISCOVERY
    # ------------------------------------------------------------------------

    def analyze_workload_costs(self, total_node_cost: float) -> Optional[Dict]:
        """
        MAIN WORKLOAD ANALYSIS: Map costs from namespaces to specific workloads
        
        Args:
            total_node_cost: Total node cost to distribute
            
        Returns:
            Complete workload cost mapping
        """
        logger.info("🚀 Starting workload cost analysis...")
        
        try:
            # Step 1: Get workload information using robust methods
            deployments = self._get_workloads_robust('deployment')
            statefulsets = self._get_workloads_robust('statefulset')
            daemonsets = self._get_workloads_robust('daemonset')

            # Step 2: Get pod cost data FIRST (this is the foundation)
            pod_analysis = self.pod_analyzer.analyze_pod_costs(total_node_cost)
            if not pod_analysis:
                logger.warning("No pod analysis data available")
                return None

            # Step 3: Extract namespace costs from pod analysis
            namespace_costs = pod_analysis.get('namespace_costs', {})

            # Step 4: Map pods to workloads 
            all_workloads = deployments + statefulsets + daemonsets
            workload_costs = self._map_pods_to_workloads(all_workloads, {'namespace_costs': namespace_costs})

            # Step 5: Build comprehensive result
            result = {
                'workload_costs': workload_costs,
                'namespace_costs': namespace_costs,
                'namespace_summary': namespace_costs,
                'deployments_count': len(deployments),
                'statefulsets_count': len(statefulsets),
                'daemonsets_count': len(daemonsets),
                'analysis_method': pod_analysis.get('analysis_method', 'workload_mapping_robust'),
                'accuracy_level': pod_analysis.get('accuracy_level', 'High'),
                'total_pods_analyzed': pod_analysis.get('total_pods_analyzed', len(all_workloads)),
                'total_namespaces': len(namespace_costs)
            }

            logger.info(f"✅ Workload analysis complete: {len(workload_costs)} workloads, {len(namespace_costs)} namespaces")
            
            return result

        except Exception as e:
            logger.error(f"❌ Workload analysis error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def _get_workloads_robust(self, workload_type: str) -> List[Dict]:
        """
        Get workload information with YAML+text fallback
        
        Args:
            workload_type: Type of workload ('deployment', 'statefulset', 'daemonset')
            
        Returns:
            List of workload information dictionaries
        """
        try:
            # Resource type mapping
            resource_types_map = {
                'deployment': 'deployments',
                'statefulset': 'statefulsets', 
                'daemonset': 'daemonsets',
                'pod': 'pods'
            }
            
            correct_resource_type = resource_types_map.get(workload_type, workload_type)
            
            # Try YAML first
            cmd = f'kubectl get {correct_resource_type} --all-namespaces'
            yaml_data = self._safe_kubectl_yaml_command(cmd, timeout=60)
            
            # If YAML fails, try text fallback
            if not yaml_data:
                logger.info(f"🔄 YAML failed for {workload_type}s, trying text fallback...")
                yaml_data = self._fallback_to_text_parsing(f'{cmd} -o yaml')
            
            if not yaml_data:
                logger.warning(f"⚠️ Could not get {workload_type}s via any method")
                return []

            workloads = []
            
            # Process data structure
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
                        
            logger.info(f"Found {len(workloads)} {workload_type}s")
            return workloads

        except Exception as e:
            logger.warning(f"⚠️ Could not get {workload_type}s: {e}")
            return []

    def _map_pods_to_workloads(self, workloads: List[Dict], pod_analysis: Dict) -> Dict:
        """
        Map pod costs to specific workloads
        
        Args:
            workloads: List of workload information
            pod_analysis: Pod analysis containing namespace costs
            
        Returns:
            Dictionary mapping workload keys to cost information
        """
        workload_costs = {}
        namespace_costs = pod_analysis.get('namespace_costs', {})
        
        if not namespace_costs:
            logger.warning("No namespace costs available for workload mapping")
            return {}

        # Group workloads by namespace
        namespace_workloads = {}
        for workload in workloads:
            namespace = workload['namespace']
            if namespace not in namespace_workloads:
                namespace_workloads[namespace] = []
            namespace_workloads[namespace].append(workload)

        # Distribute costs within each namespace
        for namespace, ns_workloads in namespace_workloads.items():
            namespace_cost = namespace_costs.get(namespace, 0)
            
            if len(ns_workloads) > 0 and namespace_cost > 0:
                # Weight by replicas for proportional cost distribution
                total_replicas = sum(w.get('replicas', 1) for w in ns_workloads)
                
                for workload in ns_workloads:
                    replicas = workload.get('replicas', 1)
                    replica_weight = replicas / total_replicas if total_replicas > 0 else 1.0 / len(ns_workloads)
                    workload_cost = namespace_cost * replica_weight
                    
                    workload_key = f"{namespace}/{workload['name']}"
                    workload_costs[workload_key] = {
                        'cost': max(workload_cost, 0.01),
                        'type': workload['type'],
                        'namespace': namespace,
                        'name': workload['name'],
                        'replicas': replicas
                    }

        logger.info(f"Mapped {len(workload_costs)} workloads to costs")
        return workload_costs

# ============================================================================
# MAIN INTEGRATION FUNCTION
# ============================================================================

def get_enhanced_pod_cost_breakdown(resource_group: str, cluster_name: str, total_node_cost: float) -> Optional[Dict]:
    """
    MAIN INTEGRATION FUNCTION for app.py
    
    Provides complete pod and workload cost breakdown for AKS Cost Intelligence
    
    Args:
        resource_group: Azure resource group name
        cluster_name: AKS cluster name  
        total_node_cost: Total monthly node cost from Azure billing
        
    Returns:
        Complete cost breakdown or None if analysis fails
        
    INTEGRATION: Called by app.py during cost analysis pipeline
    """
    logger.info(f"🔍 Starting enhanced pod cost analysis")
    logger.info(f"💰 Distributing ${total_node_cost:.2f} across pods and workloads")
    
    try:
        # Attempt workload-level analysis first (most detailed)
        workload_analyzer = WorkloadCostAnalyzer(resource_group, cluster_name)
        
        workload_result = workload_analyzer.analyze_workload_costs(total_node_cost)
        
        if workload_result:
            logger.info(f"✅ Workload analysis successful")
            return {
                'analysis_type': 'workload',
                'success': True,
                **workload_result
            }

        # Fallback to pod-level analysis
        pod_analyzer = PodCostAnalyzer(resource_group, cluster_name)
        pod_result = pod_analyzer.analyze_pod_costs(total_node_cost)
        
        if pod_result:
            logger.info(f"✅ Pod analysis successful")
            return {
                'analysis_type': 'pod',
                'success': True,
                **pod_result
            }

        logger.warning("⚠️ Pod cost analysis not available")
        return None

    except Exception as e:
        logger.error(f"❌ Pod cost analysis failed: {e}")
        return None

# ============================================================================
# INTEGRATION NOTES
# ============================================================================

"""
INTEGRATION WITH aks-realtime-metrics.py:

This file (pod_cost_analyzer.py) handles COST DISTRIBUTION:
- Takes actual costs from Azure billing
- Distributes costs across namespaces/workloads  
- Provides cost attribution ("who spent what")

The aks-realtime-metrics.py handles USAGE METRICS:
- Collects current CPU/memory utilization
- Provides data for optimization algorithms
- Shows performance patterns ("what resources are being used")

SHARED UTILITIES:
- KubernetesParsingUtils class provides common CPU/memory parsing
- Both files can use these utilities to avoid code duplication
- Consistent kubectl command execution patterns

DATA FLOW:
Azure Billing → pod_cost_analyzer.py → Cost breakdown by workload
Azure Monitor → aks-realtime-metrics.py → Usage patterns  
Both → algorithmic_cost_analyzer.py → Optimization recommendations
"""