"""
Context Builder for Claude API Integration

Handles intelligent data compacting for large clusters to fit within Claude's token limits
while preserving critical optimization information.

Token Limits Strategy:
- Small clusters (<20k tokens): Send complete data
- Medium clusters (<50k tokens): Executive summary + top 30 resources  
- Large clusters (>50k tokens): Aggregated statistics + top 10 examples

This ensures Claude receives the most relevant information for generating
effective implementation plans regardless of cluster size.
"""

import json
from typing import Dict, List, Any, Tuple
from datetime import datetime
import logging


class ContextBuilder:
    """Builds optimized context for Claude API based on cluster size and complexity"""
    
    def __init__(self, target_token_limit: int = 45000):
        """
        Initialize context builder with token management.
        
        Args:
            target_token_limit: Maximum tokens to send to Claude (default: 45k for safety)
        """
        self.target_token_limit = target_token_limit
        self.logger = logging.getLogger(__name__)
        
        # Initialize tokenizer for accurate token counting
        try:
            import tiktoken
            self.encoding = tiktoken.encoding_for_model("gpt-4")
        except ImportError:
            self.logger.warning("tiktoken not available - using character-based estimation")
            self.encoding = None
        except Exception:
            try:
                import tiktoken
                # Fallback to cl100k_base if model-specific encoding fails
                self.encoding = tiktoken.get_encoding("cl100k_base")
            except ImportError:
                self.logger.warning("tiktoken not available - using character-based estimation")
                self.encoding = None
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken or character-based estimation."""
        if self.encoding:
            return len(self.encoding.encode(str(text)))
        else:
            # Fallback: estimate tokens as roughly 1/4 of character count
            # This is a rough approximation for English text
            return len(str(text)) // 4
    
    def build_context(self, enhanced_input: Dict) -> Dict:
        """Build optimally-sized context for Claude API"""
        
        print(f"\n{'='*60}")
        print(f"🔍 DEBUG build_context called")
        print(f"  enhanced_input type: {type(enhanced_input)}")
        print(f"{'='*60}")
        
        # Validate input
        if not isinstance(enhanced_input, dict):
            raise TypeError(f"enhanced_input must be dict, got {type(enhanced_input)}")
        
        # Estimate tokens - MUST return int
        estimated_tokens = self._estimate_tokens(enhanced_input)
        
        # Validate return type
        if not isinstance(estimated_tokens, int):
            raise TypeError(f"_estimate_tokens returned {type(estimated_tokens)}, expected int")
        
        print(f"Input size: ~{estimated_tokens:,} tokens")
        
        # Now safe to compare (both are ints)
        if estimated_tokens < 20000:
            return self._add_metadata(enhanced_input, "complete")
        elif estimated_tokens < 50000:
            return self._build_prioritized_context(enhanced_input, top_n=30)
        else:
            return self._build_aggregated_context(enhanced_input, top_n=10)

    def _estimate_tokens(self, data: Dict) -> int:
        """Estimate token count from JSON size"""
        
        print(f"🔍 DEBUG _estimate_tokens:")
        print(f"  Input type: {type(data)}")
        print(f"  Input is dict: {isinstance(data, dict)}")
        
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict, got {type(data)}")
        
        try:
            json_str = json.dumps(data)
            token_count = len(json_str) // 4
            
            print(f"  JSON length: {len(json_str)}")
            print(f"  Token count: {token_count}")
            print(f"  Return type: {type(token_count)}")
            print(f"  Return value: {token_count}")
            
            # CRITICAL: Ensure we're returning an int, not dict
            if not isinstance(token_count, int):
                raise TypeError(f"Expected int, got {type(token_count)}: {token_count}")
            
            return token_count
            
        except (TypeError, ValueError) as e:
            print(f"  ❌ Error: {e}")
            raise ValueError(f"Cannot serialize data to estimate tokens: {e}")

    def _add_metadata(self, data: Dict, strategy: str) -> Dict:
        """Add context metadata for Claude's awareness"""
        return {
            **data,
            "_context_metadata": {
                "strategy": strategy,
                "timestamp": data.get("cluster_info", {}).get("analysis_timestamp"),
                "completeness": "full" if strategy == "complete" else "partial"
            }
        }

    def _build_prioritized_context(self, enhanced_input: Dict, top_n: int = 30) -> Dict:
        """Build context with top N prioritized resources"""
        workloads = enhanced_input.get('workloads', [])
        
        def safe_get_numeric(workload, key, default=0):
            """Safely get numeric value from workload, handling dict values"""
            value = workload.get(key, default)
            if isinstance(value, (int, float)):
                return value
            elif isinstance(value, dict):
                if 'total' in value:
                    return value.get('total', default)
                elif 'value' in value:
                    return value.get('value', default)
                else:
                    return default
            else:
                return default
        
        # Sort by cost + savings potential (safely handling dict values)
        try:
            sorted_workloads = sorted(
                workloads,
                key=lambda w: (safe_get_numeric(w, 'cost', 0) + safe_get_numeric(w, 'savings_potential', 0)),
                reverse=True
            )
        except Exception as e:
            print(f"❌ ERROR in _build_prioritized_context sorting: {e}")
            for i, w in enumerate(workloads):
                cost = w.get('cost', 0)
                savings = w.get('savings_potential', 0)
                print(f"  Workload {i}: cost={cost} (type: {type(cost)}), savings={savings} (type: {type(savings)})")
                if i > 3:
                    break
            raise
        
        top_workloads = sorted_workloads[:top_n]
        
        context = {
            **enhanced_input,
            'workloads': top_workloads,
            '_context_metadata': {
                "strategy": f"prioritized_top_{top_n}",
                "original_workload_count": len(workloads),
                "selected_workload_count": len(top_workloads),
                "timestamp": enhanced_input.get("cluster_info", {}).get("analysis_timestamp"),
                "completeness": "partial"
            }
        }
        
        return context

    def _build_aggregated_context(self, enhanced_input: Dict, top_n: int = 10) -> Dict:
        """Build context with aggregated stats and top examples"""
        workloads = enhanced_input.get('workloads', [])
        
        def safe_get_numeric(workload, key, default=0):
            """Safely get numeric value from workload, handling dict values"""
            value = workload.get(key, default)
            if isinstance(value, (int, float)):
                return value
            elif isinstance(value, dict):
                if 'total' in value:
                    return value.get('total', default)
                elif 'value' in value:
                    return value.get('value', default)
                else:
                    return default
            else:
                return default
        
        # Get top workloads (safely handling dict values)
        try:
            sorted_workloads = sorted(
                workloads,
                key=lambda w: (safe_get_numeric(w, 'cost', 0) + safe_get_numeric(w, 'savings_potential', 0)),
                reverse=True
            )
        except Exception as e:
            print(f"❌ ERROR in _build_aggregated_context sorting: {e}")
            for i, w in enumerate(workloads):
                cost = w.get('cost', 0)
                savings = w.get('savings_potential', 0)
                print(f"  Workload {i}: cost={cost} (type: {type(cost)}), savings={savings} (type: {type(savings)})")
                if i > 3:
                    break
            raise
        
        top_workloads = sorted_workloads[:top_n]
        
        # Create aggregated statistics
        aggregated_stats = self._create_aggregated_statistics(enhanced_input)
        
        context = {
            "cluster_info": enhanced_input.get("cluster_info", {}),
            "cost_analysis": enhanced_input.get("cost_analysis", {}),
            "aggregated_statistics": aggregated_stats,
            "top_optimization_targets": top_workloads,
            "executive_summary": self._create_executive_summary(enhanced_input),
            '_context_metadata': {
                "strategy": f"aggregated_top_{top_n}",
                "original_workload_count": len(workloads),
                "selected_workload_count": len(top_workloads),
                "timestamp": enhanced_input.get("cluster_info", {}).get("analysis_timestamp"),
                "completeness": "aggregated"
            }
        }
        
        return context

    def build_optimized_context(self, enhanced_input: Dict, cluster_name: str) -> Dict:
        """
        Build optimized context based on data size and complexity.
        
        Args:
            enhanced_input: The full enhanced analysis data
            cluster_name: Name of the AKS cluster
            
        Returns:
            Optimized context dictionary ready for Claude API
        """
        # First, get current token count
        try:
            full_context_json = json.dumps(enhanced_input, indent=2)
            current_tokens = self.count_tokens(full_context_json)
            
            print(f"🔍 DEBUG build_optimized_context:")
            print(f"  current_tokens type: {type(current_tokens)}")
            print(f"  current_tokens value: {current_tokens}")
            
            # Validate that current_tokens is an integer
            if not isinstance(current_tokens, int):
                self.logger.error(f"Token count returned {type(current_tokens)}: {current_tokens}")
                raise TypeError(f"Token count must be int, got {type(current_tokens)}: {current_tokens}")
                
        except (TypeError, ValueError) as e:
            self.logger.error(f"Error serializing enhanced_input: {e}")
            raise RuntimeError(f"Cannot serialize enhanced_input for token counting: {e}") from e
        
        self.logger.info(f"Cluster {cluster_name}: {current_tokens} tokens")
        
        # Determine optimization strategy based on token count
        if current_tokens <= 20000:
            # Small cluster: send everything
            self.logger.info(f"Small cluster - sending complete data ({current_tokens} tokens)")
            return self._build_complete_context(enhanced_input, cluster_name)
            
        elif current_tokens <= 50000:
            # Medium cluster: executive summary + top resources
            self.logger.info(f"Medium cluster - applying moderate compacting ({current_tokens} tokens)")
            return self._build_medium_context(enhanced_input, cluster_name)
            
        else:
            # Large cluster: aggressive compacting with key statistics
            self.logger.info(f"Large cluster - applying aggressive compacting ({current_tokens} tokens)")
            return self._build_compact_context(enhanced_input, cluster_name)
    
    def _build_complete_context(self, enhanced_input: Dict, cluster_name: str) -> Dict:
        """For small clusters: return complete data with minimal processing."""
        return {
            "cluster_name": cluster_name,
            "context_type": "complete",
            "token_optimization": "none_applied",
            "data": enhanced_input
        }
    
    def _build_medium_context(self, enhanced_input: Dict, cluster_name: str) -> Dict:
        """For medium clusters: executive summary + top 30 resources."""
        cost_analysis = enhanced_input.get('cost_analysis', {})
        workloads = enhanced_input.get('workloads', [])
        
        # Create executive summary
        summary = self._create_executive_summary(enhanced_input)
        
        # Get top cost resources (up to 30)
        top_resources = self._get_top_cost_resources(workloads, limit=30)
        
        # Simplified workload data
        simplified_workloads = self._simplify_workloads(top_resources)
        
        # Keep essential cost analysis but simplify breakdowns
        simplified_cost_analysis = self._simplify_cost_analysis(cost_analysis)
        
        optimized_context = {
            "cluster_name": cluster_name,
            "context_type": "medium_optimization",
            "token_optimization": "top_30_resources_plus_summary",
            "executive_summary": summary,
            "cost_analysis": simplified_cost_analysis,
            "workloads": simplified_workloads,
            "cluster_info": enhanced_input.get('cluster_info', {}),
            "node_analysis": self._simplify_node_analysis(enhanced_input.get('node_analysis', {}))
        }
        
        return optimized_context
    
    def _build_compact_context(self, enhanced_input: Dict, cluster_name: str) -> Dict:
        """For large clusters: aggressive compacting with aggregated statistics."""
        cost_analysis = enhanced_input.get('cost_analysis', {})
        workloads = enhanced_input.get('workloads', [])
        
        # Create detailed executive summary
        summary = self._create_executive_summary(enhanced_input)
        
        # Get only top 10 most expensive resources
        top_resources = self._get_top_cost_resources(workloads, limit=10)
        
        # Create aggregated statistics
        aggregated_stats = self._create_aggregated_statistics(enhanced_input)
        
        # Essential cost data only
        essential_cost_analysis = {
            "total_cost": cost_analysis.get('total_cost', 0),
            "total_savings": cost_analysis.get('total_savings', 0),
            "current_usage": cost_analysis.get('current_usage', {}),
            "savings_breakdown": cost_analysis.get('savings_breakdown', {})
        }
        
        optimized_context = {
            "cluster_name": cluster_name,
            "context_type": "aggressive_optimization", 
            "token_optimization": "top_10_resources_plus_aggregated_stats",
            "executive_summary": summary,
            "aggregated_statistics": aggregated_stats,
            "cost_analysis": essential_cost_analysis,
            "top_optimization_targets": self._get_simplified_workloads(top_resources),
            "cluster_overview": self._create_cluster_overview(enhanced_input)
        }
        
        return optimized_context
    
    def _create_executive_summary(self, enhanced_input: Dict) -> Dict:
        """Create comprehensive executive summary of the cluster analysis."""
        cost_analysis = enhanced_input.get('cost_analysis', {})
        workloads = enhanced_input.get('workloads', [])
        
        # Calculate key metrics
        total_workloads = len(workloads)
        total_cost = cost_analysis.get('total_cost', 0)
        total_savings = cost_analysis.get('total_savings', 0)
        savings_percentage = (total_savings / total_cost * 100) if total_cost > 0 else 0
        
        # Analyze workload patterns
        namespace_counts = {}
        resource_types = {}
        high_cost_workloads = 0
        
        for workload in workloads:
            namespace = workload.get('namespace', 'unknown')
            namespace_counts[namespace] = namespace_counts.get(namespace, 0) + 1
            
            resource_type = workload.get('type', 'unknown')
            resource_types[resource_type] = resource_types.get(resource_type, 0) + 1
            
            # Check cost threshold (safely handle dict values)
            cost_value = workload.get('cost', 0)
            if isinstance(cost_value, dict):
                cost_value = cost_value.get('total', cost_value.get('value', 0))
            if isinstance(cost_value, (int, float)) and cost_value > 50:
                high_cost_workloads += 1
        
        return {
            "cluster_analysis_summary": {
                "total_workloads": total_workloads,
                "total_monthly_cost": total_cost,
                "optimization_potential": total_savings,
                "cost_reduction_percentage": round(savings_percentage, 2),
                "high_cost_workload_count": high_cost_workloads
            },
            "workload_distribution": {
                "namespaces": dict(sorted(namespace_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
                "resource_types": dict(sorted(resource_types.items(), key=lambda x: x[1], reverse=True)[:10])
            },
            "optimization_opportunities": self._identify_optimization_opportunities(enhanced_input),
            "complexity_indicators": self._assess_cluster_complexity(enhanced_input)
        }
    
    def _identify_optimization_opportunities(self, enhanced_input: Dict) -> List[str]:
        """Identify key optimization opportunities from the analysis."""
        opportunities = []
        cost_analysis = enhanced_input.get('cost_analysis', {})
        savings_breakdown = cost_analysis.get('savings_breakdown', {})
        
        # HPA opportunities
        hpa_savings = savings_breakdown.get('hpa_savings', 0)
        if hpa_savings > 100:
            opportunities.append(f"HPA implementation could save ${hpa_savings:.2f}/month")
        
        # Right-sizing opportunities  
        rightsizing_savings = savings_breakdown.get('right_sizing_savings', 0)
        if rightsizing_savings > 100:
            opportunities.append(f"Resource right-sizing could save ${rightsizing_savings:.2f}/month")
        
        # Orphaned resources (safely handle dict values)
        workloads = enhanced_input.get('workloads', [])
        
        def safe_get_cpu_utilization(workload, default=0):
            """Safely get CPU utilization from workload"""
            util = workload.get('utilization', {})
            cpu_val = util.get('cpu', default)
            if isinstance(cpu_val, dict):
                return cpu_val.get('value', cpu_val.get('current', default))
            return cpu_val if isinstance(cpu_val, (int, float)) else default
        
        orphaned_count = sum(1 for w in workloads if safe_get_cpu_utilization(w, 100) < 5)
        if orphaned_count > 0:
            opportunities.append(f"{orphaned_count} potential orphaned resources identified")
        
        # Over-provisioned resources
        overprovisioned = sum(1 for w in workloads if safe_get_cpu_utilization(w, 0) < 30)
        if overprovisioned > 5:
            opportunities.append(f"{overprovisioned} over-provisioned resources need right-sizing")
        
        return opportunities[:5]  # Top 5 opportunities
    
    def _assess_cluster_complexity(self, enhanced_input: Dict) -> Dict:
        """Assess cluster complexity indicators."""
        workloads = enhanced_input.get('workloads', [])
        
        # Count unique namespaces
        namespaces = set(w.get('namespace', '') for w in workloads)
        
        # Count resource types
        resource_types = set(w.get('type', '') for w in workloads)
        
        # Assess configuration complexity (safely handle values)
        def safe_get_replicas(workload):
            replicas = workload.get('replicas', 1)
            if isinstance(replicas, dict):
                return replicas.get('current', replicas.get('value', 1))
            return replicas if isinstance(replicas, int) else 1
        
        complex_configs = sum(1 for w in workloads 
                            if len(w.get('containers', [])) > 3 or 
                               safe_get_replicas(w) > 10)
        
        return {
            "namespace_count": len(namespaces),
            "resource_type_diversity": len(resource_types),
            "complex_configurations": complex_configs,
            "total_workload_count": len(workloads),
            "complexity_score": min(100, (len(namespaces) * 5 + len(resource_types) * 3 + complex_configs * 2))
        }
    
    def _get_top_cost_resources(self, workloads: List[Dict], limit: int = 30) -> List[Dict]:
        """Get top cost resources sorted by cost impact."""
        
        def safe_get_numeric(workload, key, default=0):
            """Safely get numeric value from workload, handling dict values"""
            value = workload.get(key, default)
            if isinstance(value, (int, float)):
                return value
            elif isinstance(value, dict):
                # If it's a dict, try to get a total or sum
                if 'total' in value:
                    return value.get('total', default)
                elif 'value' in value:
                    return value.get('value', default)
                else:
                    print(f"⚠️ WARNING: {key} is dict, using default {default}: {value}")
                    return default
            else:
                print(f"⚠️ WARNING: {key} is {type(value)}, using default {default}: {value}")
                return default
        
        # Sort by cost and potential savings with safe numeric extraction
        try:
            sorted_workloads = sorted(
                workloads,
                key=lambda w: (safe_get_numeric(w, 'cost', 0) + safe_get_numeric(w, 'savings_potential', 0)),
                reverse=True
            )
            return sorted_workloads[:limit]
        except Exception as e:
            print(f"❌ ERROR in _get_top_cost_resources: {e}")
            # Debug the problematic workload
            for i, w in enumerate(workloads):
                cost = w.get('cost', 0)
                savings = w.get('savings_potential', 0)
                print(f"  Workload {i}: cost={cost} (type: {type(cost)}), savings={savings} (type: {type(savings)})")
                if i > 5:  # Only show first few
                    break
            raise
    
    def _simplify_workloads(self, workloads: List[Dict]) -> List[Dict]:
        """Simplify workload data while preserving optimization-relevant information."""
        simplified = []
        
        for workload in workloads:
            simplified_workload = {
                "name": workload.get('name'),
                "namespace": workload.get('namespace'),
                "type": workload.get('type'),
                "cost": workload.get('cost', 0),
                "savings_potential": workload.get('savings_potential', 0),
                "utilization": workload.get('utilization', {}),
                "recommendations": workload.get('recommendations', [])[:3],  # Top 3 recommendations
                "current_resources": workload.get('current_resources', {}),
                "suggested_resources": workload.get('suggested_resources', {})
            }
            simplified.append(simplified_workload)
        
        return simplified
    
    def _get_simplified_workloads(self, workloads: List[Dict]) -> List[Dict]:
        """Get highly simplified workload data for aggressive compacting."""
        simplified = []
        
        for workload in workloads:
            simplified_workload = {
                "name": workload.get('name'),
                "namespace": workload.get('namespace'),
                "type": workload.get('type'),
                "monthly_cost": workload.get('cost', 0),
                "savings_potential": workload.get('savings_potential', 0),
                "cpu_utilization": workload.get('utilization', {}).get('cpu', 0),
                "memory_utilization": workload.get('utilization', {}).get('memory', 0),
                "primary_recommendation": workload.get('recommendations', [{}])[0] if workload.get('recommendations') else {}
            }
            simplified.append(simplified_workload)
        
        return simplified
    
    def _simplify_cost_analysis(self, cost_analysis: Dict) -> Dict:
        """Simplify cost analysis while keeping essential data."""
        return {
            "total_cost": cost_analysis.get('total_cost', 0),
            "total_savings": cost_analysis.get('total_savings', 0),
            "current_usage": cost_analysis.get('current_usage', {}),
            "savings_breakdown": cost_analysis.get('savings_breakdown', {}),
            "optimization_summary": cost_analysis.get('optimization_summary', {})
        }
    
    def _simplify_node_analysis(self, node_analysis: Dict) -> Dict:
        """Simplify node analysis to essential information."""
        return {
            "total_nodes": node_analysis.get('total_nodes', 0),
            "node_utilization": node_analysis.get('avg_utilization', {}),
            "scaling_recommendations": node_analysis.get('scaling_recommendations', [])[:3]
        }
    
    def _create_aggregated_statistics(self, enhanced_input: Dict) -> Dict:
        """Create aggregated statistics for large clusters."""
        workloads = enhanced_input.get('workloads', [])
        
        # Aggregate by namespace
        namespace_stats = {}
        for workload in workloads:
            namespace = workload.get('namespace', 'unknown')
            if namespace not in namespace_stats:
                namespace_stats[namespace] = {
                    "workload_count": 0,
                    "total_cost": 0,
                    "total_savings": 0,
                    "avg_cpu_utilization": 0,
                    "avg_memory_utilization": 0
                }
            
            # Helper function to safely extract numeric values
            def safe_numeric(value, default=0):
                if isinstance(value, dict):
                    return value.get('total', value.get('value', value.get('current', default)))
                return value if isinstance(value, (int, float)) else default
            
            stats = namespace_stats[namespace]
            stats["workload_count"] += 1
            stats["total_cost"] += safe_numeric(workload.get('cost', 0))
            stats["total_savings"] += safe_numeric(workload.get('savings_potential', 0))
            stats["avg_cpu_utilization"] += safe_numeric(workload.get('utilization', {}).get('cpu', 0))
            stats["avg_memory_utilization"] += safe_numeric(workload.get('utilization', {}).get('memory', 0))
        
        # Calculate averages
        for stats in namespace_stats.values():
            if stats["workload_count"] > 0:
                stats["avg_cpu_utilization"] /= stats["workload_count"]
                stats["avg_memory_utilization"] /= stats["workload_count"]
        
        # Aggregate by resource type
        resource_type_stats = {}
        for workload in workloads:
            resource_type = workload.get('type', 'unknown')
            if resource_type not in resource_type_stats:
                resource_type_stats[resource_type] = {
                    "count": 0,
                    "total_cost": 0,
                    "avg_utilization": 0
                }
            
            # Helper function to safely extract numeric values
            def safe_numeric(value, default=0):
                if isinstance(value, dict):
                    return value.get('total', value.get('value', value.get('current', default)))
                return value if isinstance(value, (int, float)) else default
            
            stats = resource_type_stats[resource_type]
            stats["count"] += 1
            stats["total_cost"] += safe_numeric(workload.get('cost', 0))
            stats["avg_utilization"] += safe_numeric(workload.get('utilization', {}).get('cpu', 0))
        
        # Calculate resource type averages
        for stats in resource_type_stats.values():
            if stats["count"] > 0:
                stats["avg_utilization"] /= stats["count"]
        
        return {
            "total_workloads_analyzed": len(workloads),
            "namespace_aggregation": dict(sorted(namespace_stats.items(), 
                                               key=lambda x: x[1]['total_cost'], reverse=True)[:15]),
            "resource_type_aggregation": dict(sorted(resource_type_stats.items(),
                                                   key=lambda x: x[1]['total_cost'], reverse=True)[:10]),
            "cluster_utilization_summary": self._calculate_cluster_utilization_summary(workloads)
        }
    
    def _calculate_cluster_utilization_summary(self, workloads: List[Dict]) -> Dict:
        """Calculate overall cluster utilization summary."""
        if not workloads:
            return {}
        
        def safe_get_numeric_value(workload, path, default=0):
            """Safely extract numeric values from nested dict paths"""
            if path == 'cost':
                value = workload.get('cost', default)
            elif path == 'savings_potential':
                value = workload.get('savings_potential', default)
            elif path == 'cpu_utilization':
                value = workload.get('utilization', {}).get('cpu', default)
            elif path == 'memory_utilization':
                value = workload.get('utilization', {}).get('memory', default)
            else:
                return default
                
            if isinstance(value, dict):
                return value.get('total', value.get('value', value.get('current', default)))
            return value if isinstance(value, (int, float)) else default
        
        total_cpu = sum(safe_get_numeric_value(w, 'cpu_utilization', 0) for w in workloads)
        total_memory = sum(safe_get_numeric_value(w, 'memory_utilization', 0) for w in workloads)
        total_cost = sum(safe_get_numeric_value(w, 'cost', 0) for w in workloads)
        total_savings = sum(safe_get_numeric_value(w, 'savings_potential', 0) for w in workloads)
        
        # Utilization categories (safely handle dict values)
        underutilized = sum(1 for w in workloads if safe_get_numeric_value(w, 'cpu_utilization', 100) < 30)
        optimized = sum(1 for w in workloads if 30 <= safe_get_numeric_value(w, 'cpu_utilization', 0) <= 70)
        overutilized = sum(1 for w in workloads if safe_get_numeric_value(w, 'cpu_utilization', 0) > 70)
        
        return {
            "average_cpu_utilization": round(total_cpu / len(workloads), 2),
            "average_memory_utilization": round(total_memory / len(workloads), 2),
            "total_monthly_cost": round(total_cost, 2),
            "total_savings_potential": round(total_savings, 2),
            "utilization_distribution": {
                "underutilized_workloads": underutilized,
                "optimized_workloads": optimized,
                "overutilized_workloads": overutilized
            },
            "cost_efficiency_ratio": round((total_savings / total_cost * 100), 2) if total_cost > 0 else 0
        }
    
    def _create_cluster_overview(self, enhanced_input: Dict) -> Dict:
        """Create high-level cluster overview for context."""
        cluster_info = enhanced_input.get('cluster_info', {})
        node_analysis = enhanced_input.get('node_analysis', {})
        
        return {
            "cluster_version": cluster_info.get('version'),
            "region": cluster_info.get('region'),
            "node_count": node_analysis.get('total_nodes', 0),
            "total_workloads": len(enhanced_input.get('workloads', [])),
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    def estimate_response_tokens(self, optimized_context: Dict) -> int:
        """Estimate tokens for Claude's response based on context complexity."""
        context_type = optimized_context.get('context_type', 'complete')
        workload_count = len(optimized_context.get('workloads', optimized_context.get('top_optimization_targets', [])))
        
        # Base response size estimates
        base_tokens = {
            'complete': 8000,
            'medium_optimization': 6000, 
            'aggressive_optimization': 4000
        }
        
        # Add tokens based on workload count (each workload generates ~100 tokens of recommendations)
        workload_tokens = min(workload_count * 100, 4000)  # Cap at 4k for workloads
        
        estimated_response = base_tokens.get(context_type, 6000) + workload_tokens
        
        self.logger.info(f"Estimated response tokens: {estimated_response}")
        return estimated_response
    
    def get_optimization_report(self, original_size: int, optimized_size: int, context_type: str) -> Dict:
        """Generate optimization report for logging and debugging."""
        reduction_percentage = ((original_size - optimized_size) / original_size * 100) if original_size > 0 else 0
        
        return {
            "original_tokens": original_size,
            "optimized_tokens": optimized_size,
            "reduction_percentage": round(reduction_percentage, 2),
            "optimization_strategy": context_type,
            "bytes_saved": original_size - optimized_size,
            "optimization_timestamp": datetime.utcnow().isoformat()
        }