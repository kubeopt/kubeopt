#!/usr/bin/env python3
"""
Unified Node Data Processor
===========================
Central module for consistent node data processing across all components.
This ensures all components use the same node data structure.

Author: Clean Architecture Implementation
"""

import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class NodeDataProcessor:
    """
    Unified processor for node data ensuring consistent structure across:
    - kubernetes_data_cache (raw kubectl data)
    - cluster_metrics_collector (metrics collection)
    - ML pipeline (feature extraction)
    - Scoring framework (resource calculations)
    """
    
    @staticmethod
    def parse_node_data(raw_nodes: Any) -> List[Dict]:
        """
        Parse raw node data from any source into consistent structure.
        
        Returns list of nodes with guaranteed fields:
        - name: str
        - allocatable_cpu: float (in cores)
        - allocatable_memory: float (in bytes)
        - cpu_usage_pct: float (0-100)
        - memory_usage_pct: float (0-100)
        - nodepool: str
        - status: str
        """
        if not raw_nodes:
            logger.warning("No nodes data provided to parse")
            return []
            
        # Handle string JSON data
        if isinstance(raw_nodes, str):
            import json
            try:
                raw_nodes = json.loads(raw_nodes)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse nodes JSON: {raw_nodes[:200]}")
                return []
        
        # Ensure we have a list
        if not isinstance(raw_nodes, list):
            logger.error(f"Expected list of nodes, got {type(raw_nodes)}")
            return []
        
        processed_nodes = []
        for idx, node in enumerate(raw_nodes):
            try:
                processed_node = NodeDataProcessor._process_single_node(node, idx)
                if processed_node:
                    processed_nodes.append(processed_node)
            except Exception as e:
                logger.warning(f"Failed to process node {idx}: {e}")
                continue
        
        logger.info(f"✅ Processed {len(processed_nodes)} nodes successfully")
        return processed_nodes
    
    @staticmethod
    def _process_single_node(node: Dict, idx: int) -> Optional[Dict]:
        """Process a single node into consistent format."""
        
        # Check if already processed
        if 'allocatable_cpu' in node and isinstance(node['allocatable_cpu'], (int, float)):
            # Already in processed format
            return {
                'name': node.get('name', f'node-{idx}'),
                'allocatable_cpu': float(node['allocatable_cpu']),
                'allocatable_memory': float(node.get('allocatable_memory', 0)),
                'cpu_usage_pct': float(node.get('cpu_usage_pct', 0)),
                'memory_usage_pct': float(node.get('memory_usage_pct', 0)),
                'nodepool': node.get('nodepool', 'default'),
                'status': node.get('status', 'Ready')
            }
        
        # Process raw Kubernetes format
        if 'metadata' in node or 'status' in node:
            return NodeDataProcessor._process_kubernetes_node(node, idx)
        
        # Unknown format
        logger.warning(f"Unknown node format at index {idx}: {list(node.keys())[:10]}")
        return None
    
    @staticmethod
    def _process_kubernetes_node(node: Dict, idx: int) -> Dict:
        """Process raw Kubernetes node format."""
        
        # Extract name
        name = 'unknown-node'
        if 'metadata' in node:
            name = node['metadata'].get('name', f'node-{idx}')
        elif 'name' in node:
            name = node['name']
        
        # Extract nodepool and VM size from labels
        nodepool = 'default'
        vm_size = 'unknown'
        if 'metadata' in node and 'labels' in node['metadata']:
            labels = node['metadata']['labels']
            nodepool = labels.get('agentpool', labels.get('kubernetes.azure.com/agentpool', 'default'))
            vm_size = labels.get('node.kubernetes.io/instance-type', labels.get('beta.kubernetes.io/instance-type', 'unknown'))
        
        # Extract allocatable resources - NO DEFAULTS per .clauderc
        if 'status' not in node or 'allocatable' not in node['status']:
            raise ValueError(f"Node {name} missing status.allocatable - required for any AKS cluster")
        
        allocatable = node['status']['allocatable']
        
        # Parse CPU - REQUIRED
        cpu_str = allocatable.get('cpu')
        if not cpu_str:
            raise ValueError(f"Node {name} missing allocatable.cpu")
        
        try:
            if cpu_str.endswith('m'):
                # Millicores to cores
                allocatable_cpu = float(cpu_str[:-1]) / 1000
            else:
                allocatable_cpu = float(cpu_str)
                
            if allocatable_cpu <= 0:
                raise ValueError(f"Node {name} has invalid allocatable CPU: {allocatable_cpu}")
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Node {name} failed to parse CPU '{cpu_str}': {e}") from e
        
        # Parse Memory - REQUIRED
        memory_str = allocatable.get('memory')
        if not memory_str:
            raise ValueError(f"Node {name} missing allocatable.memory")
            
        try:
            allocatable_memory = NodeDataProcessor._parse_memory_string(memory_str)
            if allocatable_memory <= 0:
                raise ValueError(f"Node {name} has invalid allocatable memory: {allocatable_memory}")
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Node {name} failed to parse memory '{memory_str}': {e}") from e
        
        # Extract usage percentages (if available from metrics)
        cpu_usage_pct = 0.0
        memory_usage_pct = 0.0
        
        if 'usage' in node:
            usage = node['usage']
            if 'cpu' in usage and allocatable_cpu > 0:
                cpu_used = NodeDataProcessor._parse_cpu_string(usage['cpu'])
                cpu_usage_pct = (cpu_used / allocatable_cpu) * 100
            
            if 'memory' in usage and allocatable_memory > 0:
                memory_used = NodeDataProcessor._parse_memory_string(usage['memory'])
                memory_usage_pct = (memory_used / allocatable_memory) * 100
        
        # Alternative: check for pre-calculated percentages
        elif 'cpu_usage_pct' in node:
            cpu_usage_pct = float(node['cpu_usage_pct'])
            memory_usage_pct = float(node.get('memory_usage_pct', 0))
        
        # Extract status
        status = 'Unknown'
        if 'status' in node and 'conditions' in node['status']:
            for condition in node['status']['conditions']:
                if condition.get('type') == 'Ready':
                    status = 'Ready' if condition.get('status') == 'True' else 'NotReady'
                    break
        
        return {
            'name': name,
            'allocatable_cpu': allocatable_cpu,
            'allocatable_memory': allocatable_memory,
            'cpu_usage_pct': cpu_usage_pct,
            'memory_usage_pct': memory_usage_pct,
            'nodepool': nodepool,
            'vm_size': vm_size,
            'status': status
        }
    
    @staticmethod
    def _parse_cpu_string(cpu_str: str) -> float:
        """Parse CPU string to cores."""
        if not cpu_str:
            return 0.0
        
        cpu_str = str(cpu_str).strip()
        if cpu_str.endswith('m'):
            # Millicores
            return float(cpu_str[:-1]) / 1000
        elif cpu_str.endswith('n'):
            # Nanocores
            return float(cpu_str[:-1]) / 1_000_000_000
        else:
            # Assume cores
            return float(cpu_str)
    
    @staticmethod
    def _parse_memory_string(memory_str: str) -> float:
        """Parse memory string to bytes."""
        if not memory_str:
            return 0.0
        
        memory_str = str(memory_str).strip()
        
        # Remove 'i' suffix if present (e.g., Ki, Mi, Gi)
        if memory_str[-1] == 'i':
            memory_str = memory_str[:-1]
        
        if memory_str.endswith('K'):
            return float(memory_str[:-1]) * 1024
        elif memory_str.endswith('M'):
            return float(memory_str[:-1]) * 1024 * 1024
        elif memory_str.endswith('G'):
            return float(memory_str[:-1]) * 1024 * 1024 * 1024
        elif memory_str.endswith('T'):
            return float(memory_str[:-1]) * 1024 * 1024 * 1024 * 1024
        else:
            # Assume bytes
            return float(memory_str)
    
    @staticmethod
    def calculate_cluster_totals(nodes: List[Dict]) -> Dict:
        """
        Calculate cluster-wide totals from processed nodes.
        
        Returns:
        - total_cpu_cores: Total allocatable CPU in cores
        - total_memory_bytes: Total allocatable memory in bytes
        - avg_cpu_utilization: Average CPU utilization percentage
        - avg_memory_utilization: Average memory utilization percentage
        - node_count: Number of nodes
        """
        if not nodes:
            return {
                'total_cpu_cores': 0.0,
                'total_memory_bytes': 0.0,
                'avg_cpu_utilization': 0.0,
                'avg_memory_utilization': 0.0,
                'node_count': 0
            }
        
        total_cpu = sum(n.get('allocatable_cpu', 0) for n in nodes)
        total_memory = sum(n.get('allocatable_memory', 0) for n in nodes)
        
        # Calculate weighted average utilization
        total_cpu_used = sum(
            n.get('allocatable_cpu', 0) * n.get('cpu_usage_pct', 0) / 100
            for n in nodes
        )
        total_memory_used = sum(
            n.get('allocatable_memory', 0) * n.get('memory_usage_pct', 0) / 100
            for n in nodes
        )
        
        avg_cpu_util = (total_cpu_used / total_cpu * 100) if total_cpu > 0 else 0
        avg_memory_util = (total_memory_used / total_memory * 100) if total_memory > 0 else 0
        
        return {
            'total_cpu_cores': total_cpu,
            'total_memory_bytes': total_memory,
            'avg_cpu_utilization': avg_cpu_util,
            'avg_memory_utilization': avg_memory_util,
            'node_count': len(nodes)
        }
    
    @staticmethod
    def validate_node_data(nodes: List[Dict]) -> Tuple[bool, List[str]]:
        """
        Validate node data for completeness and correctness.
        
        Returns:
        - is_valid: bool
        - errors: List of error messages
        """
        errors = []
        
        if not nodes:
            errors.append("No nodes data available")
            return False, errors
        
        for idx, node in enumerate(nodes):
            if not isinstance(node, dict):
                errors.append(f"Node {idx} is not a dictionary")
                continue
            
            # Check required fields
            required_fields = ['name', 'allocatable_cpu', 'allocatable_memory']
            for field in required_fields:
                if field not in node:
                    errors.append(f"Node {idx} missing required field: {field}")
            
            # Validate numeric fields
            if 'allocatable_cpu' in node:
                cpu = node['allocatable_cpu']
                if not isinstance(cpu, (int, float)) or cpu <= 0:
                    errors.append(f"Node {node.get('name', idx)} has invalid CPU: {cpu}")
            
            if 'allocatable_memory' in node:
                mem = node['allocatable_memory']
                if not isinstance(mem, (int, float)) or mem <= 0:
                    errors.append(f"Node {node.get('name', idx)} has invalid memory: {mem}")
        
        is_valid = len(errors) == 0
        if not is_valid:
            logger.error(f"Node data validation failed with {len(errors)} errors")
            for error in errors[:5]:  # Log first 5 errors
                logger.error(f"  - {error}")
        
        return is_valid, errors