#!/usr/bin/env python3
"""
Workload Batcher for handling large enhanced input data while preserving rich information
Splits workloads into manageable batches for Claude processing
"""

import json
from typing import Dict, List

class WorkloadBatcher:
    """Batches workloads from enhanced input data for large cluster processing"""
    
    def __init__(self, max_tokens_per_batch: int = 50000):
        self.max_tokens_per_batch = max_tokens_per_batch
    
    def estimate_tokens(self, data: any) -> int:
        """Estimate tokens for any data structure"""
        return len(json.dumps(data, default=str)) // 4
    
    def create_workload_batches(self, enhanced_input: Dict) -> List[Dict]:
        """
        Split enhanced input into workload batches while preserving rich data
        
        Args:
            enhanced_input: Enhanced analysis input (structured, ~800KB)
            
        Returns:
            List of batched contexts, each under token limit
        """
        
        workloads = enhanced_input.get('workloads', [])
        
        if not workloads:
            return [enhanced_input]
        
        # Calculate base context size (everything except workloads)
        base_context = {k: v for k, v in enhanced_input.items() if k != 'workloads'}
        
        # Optimize large sections if needed
        base_context = self._optimize_large_sections(base_context)
        
        base_tokens = self.estimate_tokens(base_context)
        
        # Available tokens for workloads in each batch
        available_tokens = self.max_tokens_per_batch - base_tokens
        
        if available_tokens < 5000:
            raise ValueError(f"Base context too large ({base_tokens} tokens), cannot fit workloads")
        
        print(f"🔍 Workload batching:")
        print(f"   Total workloads: {len(workloads)}")
        print(f"   Base context: {base_tokens:,} tokens") 
        print(f"   Available per batch: {available_tokens:,} tokens")
        
        # Create batches
        batches = []
        current_batch = []
        current_batch_tokens = 0
        
        for workload in workloads:
            workload_tokens = self.estimate_tokens(workload)
            
            # Check if adding this workload would exceed limit
            if current_batch and (current_batch_tokens + workload_tokens > available_tokens):
                # Finalize current batch
                batch_context = {
                    **base_context,
                    'workloads': current_batch,
                    '_batch_metadata': {
                        'batch_number': len(batches) + 1,
                        'workload_count': len(current_batch),
                        'estimated_tokens': base_tokens + current_batch_tokens
                    }
                }
                batches.append(batch_context)
                
                # Start new batch
                current_batch = [workload]
                current_batch_tokens = workload_tokens
            else:
                # Add to current batch
                current_batch.append(workload)
                current_batch_tokens += workload_tokens
        
        # Add final batch
        if current_batch:
            batch_context = {
                **base_context,
                'workloads': current_batch,
                '_batch_metadata': {
                    'batch_number': len(batches) + 1,
                    'workload_count': len(current_batch),
                    'estimated_tokens': base_tokens + current_batch_tokens
                }
            }
            batches.append(batch_context)
        
        print(f"   Created {len(batches)} batches")
        for i, batch in enumerate(batches):
            meta = batch['_batch_metadata']
            print(f"   Batch {i+1}: {meta['workload_count']} workloads, ~{meta['estimated_tokens']:,} tokens")
        
        return batches
    
    def merge_batch_results(self, batch_results: List[Dict]) -> Dict:
        """
        Merge results from multiple workload batches into comprehensive plan
        
        Args:
            batch_results: List of plan results from each batch
            
        Returns:
            Merged comprehensive implementation plan
        """
        
        if not batch_results:
            raise ValueError("No batch results to merge")
        
        if len(batch_results) == 1:
            return batch_results[0]
        
        print(f"🔗 Merging {len(batch_results)} batch results...")
        
        # Initialize merged plan with first batch
        merged_plan = batch_results[0].copy()
        merged_impl = merged_plan.get('implementation_plan', {})
        
        # Collect phases from all batches
        all_phases = []
        all_actions = []
        total_savings = 0.0
        
        for i, batch_result in enumerate(batch_results):
            impl_plan = batch_result.get('implementation_plan', {})
            phases = impl_plan.get('phases', [])
            
            print(f"   Batch {i+1}: {len(phases)} phases")
            
            for phase in phases:
                # Adjust phase numbers to be sequential across batches
                phase['phase_number'] = len(all_phases) + 1
                phase['batch_source'] = i + 1
                all_phases.append(phase)
                
                # Collect actions and calculate savings
                actions = phase.get('actions', [])
                all_actions.extend(actions)
                
                phase_savings = phase.get('estimated_savings', 0)
                if isinstance(phase_savings, (int, float)):
                    total_savings += phase_savings
        
        # Update merged plan with all phases
        merged_impl['phases'] = all_phases
        
        # Aggregate executive summary data from all batches
        total_monthly_savings = 0.0
        total_annual_savings = 0.0
        total_opportunities = 0
        total_issues = 0
        
        for batch_result in batch_results:
            exec_summary = batch_result.get('implementation_plan', {}).get('executive_summary', {})
            
            total_monthly_savings += exec_summary.get('potential_monthly_savings', 0)
            total_annual_savings += exec_summary.get('annual_savings', 0)
            total_opportunities += exec_summary.get('optimization_opportunities', 0)
            total_issues += exec_summary.get('critical_issues', 0)
        
        # Update executive summary with aggregated data
        if 'executive_summary' in merged_impl:
            merged_impl['executive_summary'].update({
                'potential_monthly_savings': total_monthly_savings,
                'annual_savings': total_annual_savings,
                'optimization_opportunities': total_opportunities,
                'critical_issues': total_issues,
                'implementation_phases': len(all_phases)
            })
        
        # Update metadata
        if 'metadata' in merged_impl:
            merged_impl['metadata']['generation_method'] = 'workload_batching'
            merged_impl['metadata']['batch_count'] = len(batch_results)
            merged_impl['metadata']['total_workloads_processed'] = sum(
                len(batch.get('workloads', [])) for batch in [
                    br.get('source_data', {}) for br in batch_results
                ] if batch
            )
        
        print(f"✅ Merged plan:")
        print(f"   Total phases: {len(all_phases)}")
        print(f"   Total actions: {len(all_actions)}")
        print(f"   Total savings: ${total_monthly_savings:,.2f}/month")
        
        return merged_plan
    
    def _optimize_large_sections(self, base_context: Dict) -> Dict:
        """Optimize large sections in base context to reduce token usage"""
        
        optimized_context = base_context.copy()
        
        # Check if inefficient_workloads section is too large
        inefficient_workloads = base_context.get('inefficient_workloads')
        if inefficient_workloads:
            inefficient_tokens = self.estimate_tokens(inefficient_workloads)
            
            if inefficient_tokens > 15000:  # If larger than 15K tokens
                print(f"   Optimizing inefficient_workloads: {inefficient_tokens:,} -> ", end="")
                
                # Keep only top 50 most inefficient workloads for context
                if isinstance(inefficient_workloads, list):
                    # Sort by cost impact and keep top 50
                    sorted_inefficient = sorted(
                        inefficient_workloads,
                        key=lambda w: w.get('cost_impact', 0) + w.get('savings_potential', 0),
                        reverse=True
                    )
                    optimized_context['inefficient_workloads'] = sorted_inefficient[:50]
                elif isinstance(inefficient_workloads, dict):
                    # If it's a dict, create summary
                    optimized_context['inefficient_workloads'] = {
                        'summary': f"Analysis of {len(str(inefficient_workloads))} inefficient resources",
                        'total_cost_impact': sum(
                            w.get('cost_impact', 0) for w in inefficient_workloads.get('workloads', [])
                        ) if 'workloads' in inefficient_workloads else 0,
                        'top_issues': inefficient_workloads.get('top_issues', [])[:10] if 'top_issues' in inefficient_workloads else []
                    }
                
                new_tokens = self.estimate_tokens(optimized_context['inefficient_workloads'])
                print(f"{new_tokens:,} tokens")
        
        return optimized_context