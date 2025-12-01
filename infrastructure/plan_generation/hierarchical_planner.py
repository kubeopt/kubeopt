#!/usr/bin/env python3
"""
Hierarchical Planning for large clusters
1. Generate cluster overview with all metadata
2. Create workload-specific implementations in batches  
3. Synthesize comprehensive plan
"""

import json
from typing import Dict, List
import asyncio

class HierarchicalPlanner:
    """
    Two-phase planning approach:
    Phase 1: Cluster-wide analysis and strategy (compressed overview)
    Phase 2: Detailed workload implementation (batched execution)
    """
    
    def __init__(self, claude_generator, max_tokens_per_batch: int = 45000):
        self.claude_generator = claude_generator
        self.max_tokens_per_batch = max_tokens_per_batch
    
    def estimate_tokens(self, data) -> int:
        """Estimate tokens for data"""
        return len(json.dumps(data, default=str)) // 4
    
    async def _process_strategic_overview(self, overview_context: Dict, cluster_name: str, cluster_id: str) -> Dict:
        """
        SMART FIX: Generate strategic overview with templates and patterns, not detailed kubectl commands
        """
        strategic_prompt = f"""
Generate a HIGH-LEVEL STRATEGIC optimization plan for Kubernetes cluster '{cluster_name}'.

CRITICAL: This is Phase 1 - STRATEGIC OVERVIEW ONLY. Do NOT generate detailed kubectl commands.

Focus on:
1. Executive summary with cost analysis
2. High-level optimization phases
3. Strategic patterns and templates
4. Compliance frameworks
5. Implementation templates (not specific commands)

Return ONLY valid JSON with this structure:
{{
  "metadata": {{
    "plan_id": "{cluster_name}-strategic-plan",
    "cluster_name": "{cluster_name}",
    "plan_type": "strategic_overview",
    "analysis_confidence": "high"
  }},
  "executive_summary": {{
    "current_monthly_cost": 0,
    "potential_monthly_savings": 0,
    "savings_percentage": 0,
    "annual_savings": 0,
    "key_findings": "strategic findings",
    "business_impact": "business impact summary"
  }},
  "strategic_phases": [
    {{
      "phase_number": 1,
      "name": "Resource Optimization",
      "priority": "critical",
      "duration_days": 7,
      "strategy": "optimize resource allocation patterns",
      "template_actions": [
        "implement resource quotas template",
        "apply memory optimization pattern"
      ]
    }}
  ]
}}

Cluster context: {overview_context}
"""
        
        import asyncio
        
        try:
            response = await asyncio.to_thread(
                self.claude_generator.client.messages.create,
                model=self.claude_generator.model,
                max_tokens=3000,  # Strategic overview needs less tokens
                temperature=0.3,
                messages=[{"role": "user", "content": strategic_prompt}]
            )
            
            response_text = response.content[0].text
            return self.claude_generator._extract_json_from_response(response_text)
            
        except Exception as e:
            raise RuntimeError(f"Strategic overview generation failed: {e}")
    
    def create_cluster_overview(self, enhanced_input: Dict) -> Dict:
        """
        Create comprehensive cluster overview for strategic planning
        Includes all metadata but summarized workloads
        """
        
        workloads = enhanced_input.get('workloads', [])
        
        # Create workload summary with key patterns
        workload_summary = self._create_workload_summary(workloads)
        
        # Build overview context
        overview_context = {
            **{k: v for k, v in enhanced_input.items() if k != 'workloads'},
            'workload_analysis_summary': workload_summary,
            'cluster_scope': {
                'total_workloads': len(workloads),
                'analysis_type': 'strategic_overview',
                'detail_level': 'cluster_wide_strategy'
            }
        }
        
        overview_tokens = self.estimate_tokens(overview_context)
        print(f"📊 Cluster overview context: {overview_tokens:,} tokens")
        
        return overview_context
    
    def _create_workload_summary(self, workloads: List[Dict]) -> Dict:
        """Create strategic summary of all workloads for cluster-wide planning"""
        
        if not workloads:
            return {}
        
        # Categorize workloads by patterns
        by_namespace = {}
        by_type = {}
        high_cost_workloads = []
        optimization_candidates = []
        
        total_cost = 0
        total_savings_potential = 0
        
        for workload in workloads:
            # Basic categorization
            namespace = workload.get('namespace', 'unknown')
            workload_type = workload.get('type', 'unknown')
            cost = workload.get('cost', 0)
            savings = workload.get('savings_potential', 0)
            
            # Group by namespace
            if namespace not in by_namespace:
                by_namespace[namespace] = {'count': 0, 'total_cost': 0, 'workloads': []}
            by_namespace[namespace]['count'] += 1
            by_namespace[namespace]['total_cost'] += cost
            
            # Group by type  
            if workload_type not in by_type:
                by_type[workload_type] = {'count': 0, 'total_cost': 0}
            by_type[workload_type]['count'] += 1
            by_type[workload_type]['total_cost'] += cost
            
            # Track high-value targets
            if cost > 50:  # High cost threshold
                high_cost_workloads.append({
                    'name': workload.get('name'),
                    'namespace': namespace,
                    'cost': cost,
                    'savings_potential': savings
                })
            
            if savings > 20:  # High optimization potential
                optimization_candidates.append({
                    'name': workload.get('name'),
                    'namespace': namespace,
                    'cost': cost,
                    'savings_potential': savings
                })
            
            total_cost += cost
            total_savings_potential += savings
        
        # Sort and limit for strategy (strategic overview only needs top examples)
        high_cost_workloads.sort(key=lambda x: x['cost'], reverse=True)
        optimization_candidates.sort(key=lambda x: x['savings_potential'], reverse=True)
        
        # SMART FIX: Strategic overview only needs top examples, not all workloads
        high_cost_workloads = high_cost_workloads[:5]  # Top 5 for strategy
        optimization_candidates = optimization_candidates[:5]  # Top 5 for strategy
        
        return {
            'cluster_financial_summary': {
                'total_monthly_cost': total_cost,
                'total_savings_potential': total_savings_potential,
                'optimization_percentage': (total_savings_potential / total_cost * 100) if total_cost > 0 else 0
            },
            'namespace_distribution': dict(sorted(by_namespace.items(), key=lambda x: x[1]['total_cost'], reverse=True)),
            'workload_type_distribution': dict(sorted(by_type.items(), key=lambda x: x[1]['total_cost'], reverse=True)),
            'top_cost_targets': high_cost_workloads[:20],  # Top 20 expensive workloads
            'top_optimization_targets': optimization_candidates[:30],  # Top 30 optimization candidates
            'strategic_insights': {
                'primary_namespaces': list(dict(sorted(by_namespace.items(), key=lambda x: x[1]['total_cost'], reverse=True)).keys())[:5],
                'dominant_workload_types': list(dict(sorted(by_type.items(), key=lambda x: x[1]['count'], reverse=True)).keys())[:5],
                'cost_concentration': 'high' if len(high_cost_workloads) < len(workloads) * 0.1 else 'distributed'
            }
        }
    
    def create_implementation_batches(self, enhanced_input: Dict, strategic_plan: Dict) -> List[Dict]:
        """
        Create workload batches for detailed implementation
        Each batch includes strategic context from Phase 1
        """
        
        workloads = enhanced_input.get('workloads', [])
        base_context = {k: v for k, v in enhanced_input.items() if k != 'workloads'}
        
        # Add strategic guidance to each batch
        strategic_guidance = {
            'cluster_strategy': strategic_plan.get('implementation_plan', {}).get('strategic_approach', {}),
            'global_phases': strategic_plan.get('implementation_plan', {}).get('phases', []),
            'optimization_priorities': strategic_plan.get('implementation_plan', {}).get('optimization_priorities', []),
            'cluster_constraints': strategic_plan.get('implementation_plan', {}).get('constraints', {}),
        }
        
        base_tokens = self.estimate_tokens({**base_context, **strategic_guidance})
        available_tokens = self.max_tokens_per_batch - base_tokens
        
        print(f"🔍 Implementation batching:")
        print(f"   Base context + strategy: {base_tokens:,} tokens") 
        print(f"   Available for workloads: {available_tokens:,} tokens")
        
        # Create batches with strategic context
        batches = []
        current_batch = []
        current_batch_tokens = 0
        
        # SMART FIX: Optimized for comprehensive kubectl commands with 16K tokens
        max_workloads_per_batch = 3  # Balanced for comprehensive commands and reasonable batch count
        
        for workload in workloads:
            workload_tokens = self.estimate_tokens(workload)
            
            # Create new batch if: token limit OR workload count limit reached
            batch_full = (current_batch_tokens + workload_tokens > available_tokens) or \
                        (len(current_batch) >= max_workloads_per_batch)
            
            if current_batch and batch_full:
                # Finalize current batch with strategic guidance
                batch_context = {
                    **base_context,
                    **strategic_guidance,
                    'workloads': current_batch,
                    '_batch_metadata': {
                        'batch_number': len(batches) + 1,
                        'workload_count': len(current_batch),
                        'has_strategic_context': True,
                        'estimated_tokens': base_tokens + current_batch_tokens
                    }
                }
                batches.append(batch_context)
                
                current_batch = [workload]
                current_batch_tokens = workload_tokens
            else:
                current_batch.append(workload)
                current_batch_tokens += workload_tokens
        
        # Add final batch
        if current_batch:
            batch_context = {
                **base_context,
                **strategic_guidance,
                'workloads': current_batch,
                '_batch_metadata': {
                    'batch_number': len(batches) + 1,
                    'workload_count': len(current_batch),
                    'has_strategic_context': True,
                    'estimated_tokens': base_tokens + current_batch_tokens
                }
            }
            batches.append(batch_context)
        
        print(f"   Created {len(batches)} implementation batches with strategic context")
        return batches
    
    async def generate_hierarchical_plan(self, enhanced_input: Dict, cluster_name: str, cluster_id: str) -> Dict:
        """
        Generate comprehensive plan using hierarchical approach
        
        Phase 1: Strategic cluster-wide planning
        Phase 2: Detailed workload implementation in batches
        Phase 3: Synthesis into unified plan
        """
        
        print(f"\n{'='*70}")
        print(f"🏗️ HIERARCHICAL PLANNING MODE")
        print(f"{'='*70}")
        print(f"Cluster: {cluster_name}")
        print(f"Total workloads: {len(enhanced_input.get('workloads', []))}")
        print(f"{'='*70}\n")
        
        # ===== PHASE 1: STRATEGIC PLANNING =====
        print(f"🎯 Phase 1: Cluster-wide strategic planning...")
        
        overview_context = self.create_cluster_overview(enhanced_input)
        # SMART FIX: Phase 1 needs strategic prompt, not detailed implementation prompt
        strategic_plan = await self._process_strategic_overview(
            overview_context, cluster_name, cluster_id
        )
        
        print(f"✅ Strategic plan generated")
        
        # ===== PHASE 2: DETAILED IMPLEMENTATION =====
        print(f"\n🔧 Phase 2: Detailed workload implementation...")
        
        implementation_batches = self.create_implementation_batches(enhanced_input, strategic_plan)
        batch_results = []
        
        for i, batch_context in enumerate(implementation_batches):
            print(f"\n📦 Processing implementation batch {i+1}/{len(implementation_batches)}")
            
            batch_result = await self.claude_generator._process_single_batch(
                batch_context, cluster_name, cluster_id
            )
            batch_results.append(batch_result)
        
        # ===== PHASE 3: INTELLIGENT SYNTHESIS =====
        print(f"\n🔗 Phase 3: Synthesizing comprehensive plan...")
        
        unified_plan = self._synthesize_hierarchical_plan(
            strategic_plan, batch_results, enhanced_input, cluster_name
        )
        
        print(f"✅ Hierarchical plan generation complete!")
        return unified_plan
    
    def _synthesize_hierarchical_plan(self, strategic_plan: Dict, batch_results: List[Dict], 
                                    original_input: Dict, cluster_name: str) -> Dict:
        """Intelligently synthesize strategic plan with detailed implementations"""
        
        # Use strategic plan as foundation
        synthesis = strategic_plan.copy()
        impl_plan = synthesis.get('implementation_plan', {})
        
        # Ensure implementation_plan exists
        if not impl_plan:
            impl_plan = synthesis
        
        # Ensure phases key exists
        if 'phases' not in impl_plan:
            impl_plan['phases'] = []
        
        # Merge all detailed implementations
        all_phases = []
        all_workload_actions = []
        total_savings = 0
        
        # Collect all implementation details
        for batch_result in batch_results:
            batch_impl = batch_result.get('implementation_plan', {})
            batch_phases = batch_impl.get('phases', [])
            
            for phase in batch_phases:
                # Add batch-specific actions to strategic phases
                actions = phase.get('actions', [])
                all_workload_actions.extend(actions)
                
                savings = phase.get('estimated_savings', 0)
                if isinstance(savings, (int, float)):
                    total_savings += savings
        
        # Enhance strategic phases with detailed actions
        strategic_phases = impl_plan.get('phases', [])
        for phase in strategic_phases:
            # Assign relevant workload actions to strategic phases
            phase_actions = [a for a in all_workload_actions if self._matches_phase_scope(a, phase)]
            phase['actions'] = phase_actions
            phase['detailed_workload_count'] = len(phase_actions)
        
        # Update financial projections with detailed calculations
        if 'executive_summary' in impl_plan:
            impl_plan['executive_summary']['detailed_monthly_savings'] = total_savings
            impl_plan['executive_summary']['total_actionable_workloads'] = len(all_workload_actions)
        
        # Add synthesis metadata
        impl_plan['generation_metadata'] = {
            'approach': 'hierarchical_planning',
            'strategic_phases': len(strategic_phases),
            'implementation_batches': len(batch_results),
            'total_workloads_processed': len(original_input.get('workloads', [])),
            'synthesis_timestamp': '2025-11-21'
        }
        
        print(f"   Strategic phases: {len(strategic_phases)}")
        print(f"   Detailed actions: {len(all_workload_actions)}")
        print(f"   Total savings: ${total_savings:,.2f}/month")
        
        return synthesis
    
    def _matches_phase_scope(self, action: Dict, phase: Dict) -> bool:
        """Determine if an action belongs to a strategic phase"""
        action_type = action.get('name', '').lower()
        phase_name = phase.get('name', '').lower()
        
        # Simple matching logic - can be enhanced
        if 'performance' in phase_name or 'optimization' in phase_name:
            return any(keyword in action_type for keyword in ['resize', 'hpa', 'resource', 'cpu', 'memory'])
        elif 'infrastructure' in phase_name:
            return any(keyword in action_type for keyword in ['node', 'spot', 'autoscaler'])
        elif 'security' in phase_name:
            return any(keyword in action_type for keyword in ['policy', 'rbac', 'network'])
        elif 'cost' in phase_name or 'governance' in phase_name:
            return any(keyword in action_type for keyword in ['quota', 'monitoring', 'alert'])
        
        return True  # Default: include action in first available phase