"""
Claude API Integration for Plan Generation

Handles communication with Claude API to generate structured implementation plans
for AKS cost optimization based on enhanced analysis input.
"""

import anthropic
import json
import asyncio
import os
from typing import Dict, Optional
from datetime import datetime
import logging
from pydantic import BaseModel, Field, validator
from .plan_schema import (
    KubeOptImplementationPlan, ImplementationPlanDocument, 
    KUBEOPT_IMPLEMENTATION_PLAN_SCHEMA, create_empty_plan
)
from .plan_validator import PlanValidator
from .context_builder import ContextBuilder
from .cost_tracker import get_cost_tracker
from .cost_limiter import check_cost_limit

# Import standards loader for YAML-based configuration
from shared.standards.standards_loader import get_standards_loader


class ClaudePlanGenerator:
    """Generates implementation plans using Claude API with intelligent context compacting"""
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_output_tokens: Optional[int] = None,
        max_context_tokens: int = 180000
    ):
        """
        Initialize the plan generator.
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use (defaults to env CLAUDE_MODEL or Sonnet 3.5)
            max_output_tokens: Max tokens for output (defaults to env or model-specific)
            max_context_tokens: Maximum tokens for input context
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not provided and not found in environment")
        
        # Get model from parameter, environment, or default
        self.model = model or os.getenv("CLAUDE_MODEL", "claude-3-haiku-20240307")
        
        # Get max output tokens with explicit validation
        if max_output_tokens is not None:
            if not isinstance(max_output_tokens, int) or max_output_tokens <= 0:
                raise ValueError(f"max_output_tokens must be a positive integer, got: {max_output_tokens}")
            self.max_output_tokens = max_output_tokens
        else:
            env_max_tokens = os.getenv("CLAUDE_MAX_OUTPUT_TOKENS")
            if env_max_tokens and env_max_tokens.strip():
                # Handle comments in environment variable values
                clean_tokens = env_max_tokens.split('#')[0].strip()
                self.max_output_tokens = int(clean_tokens)
            else:
                # Use model-specific default
                self.max_output_tokens = self._get_model_max_output_tokens(self.model)
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.validator = PlanValidator()
        self.context_builder = ContextBuilder(target_token_limit=max_context_tokens)
        self.logger = logging.getLogger(__name__)
        
        print(f"✓ Initialized ClaudePlanGenerator")
        print(f"  Model: {self.model}")
        print(f"  Max output tokens: {self.max_output_tokens} (cost-optimized)")
        print(f"  Max context tokens: {max_context_tokens}")
        print(f"✓ Token limit set to {self.max_output_tokens} (cost-optimized)")
    
    def _get_model_max_output_tokens(self, model: str) -> int:
        """
        Get the maximum output tokens for a given model.
        
        Returns model-specific safe defaults.
        """
        model_limits = {
            # Latest Claude 4.5 models (2025) - Cost-optimized
            "claude-sonnet-4-5-20250929": 3000,  # Reduced from 16000 for cost optimization
            "claude-haiku-4-5-20251001": 3000,   # Reduced from 16000 for cost optimization
            
            # Claude 4 models (2025) - Cost-optimized
            "claude-opus-4-1-20250805": 3000,    # Reduced from 16000 for cost optimization
            "claude-sonnet-4-20250514": 3000,    # Reduced from 16000 for cost optimization
            "claude-opus-4-20250514": 3000,      # Reduced from 16000 for cost optimization
            
            # Claude 3.7 models - Cost-optimized
            "claude-3-7-sonnet-20250219": 3000,  # Reduced from 8192 for cost optimization
            
            # Legacy Claude 3.5 models - Cost-optimized
            "claude-3-haiku-20240307": 4000,     # Increased to fix JSON truncation issue
            "claude-3-5-sonnet-20240620": 3000,  # Reduced from 8192 for cost optimization
            
            # Legacy Claude 3 models - Cost-optimized
            "claude-3-opus-20240229": 3000,      # Reduced from 4096 for cost optimization
            "claude-3-sonnet-20240229": 3000,    # Reduced from 4096 for cost optimization
            "claude-3-haiku-20240307": 4000,     # Increased to fix JSON truncation issue
        }
        
        max_tokens = model_limits.get(model, 3000)  # Conservative default - cost-optimized
        
        if model not in model_limits:
            print(f"⚠️ Unknown model {model}, using conservative {max_tokens} max output tokens")
        
        return max_tokens
        
    async def generate_plan(
        self, 
        enhanced_input: Dict,
        cluster_name: str,
        cluster_id: str,
        max_retries: int = None
    ) -> KubeOptImplementationPlan:
        """
        Generate implementation plan.
        
        Automatically uses split mode for Haiku (2 calls),
        single mode for other models.
        """
        
        # Validate inputs
        if not enhanced_input:
            raise ValueError("enhanced_input is required and cannot be empty")
        if not isinstance(enhanced_input, dict):
            raise TypeError(f"enhanced_input must be a dictionary, got: {type(enhanced_input)}")
        if not cluster_name or not isinstance(cluster_name, str) or not cluster_name.strip():
            raise ValueError("cluster_name must be a non-empty string")
        if not cluster_id or not isinstance(cluster_id, str) or not cluster_id.strip():
            raise ValueError("cluster_id must be a non-empty string")
        
        # Determine mode
        use_split = "haiku" in self.model.lower() or os.getenv("CLAUDE_USE_SPLIT_MODE", "true").lower() == "true"
        
        if use_split:
            # Use split mode (2 API calls)
            return await self.generate_plan_split(enhanced_input, cluster_name, cluster_id)
        else:
            # Use single call mode (for Sonnet/Opus)
            return await self.generate_plan_single(enhanced_input, cluster_name, cluster_id, max_retries)
    
    async def generate_plan_single(
        self, 
        enhanced_input: Dict,
        cluster_name: str,
        cluster_id: str,
        max_retries: int = None
    ) -> KubeOptImplementationPlan:
        """
        Generate implementation plan from enhanced analysis input with intelligent context optimization.
        
        Args:
            enhanced_input: The enhanced analysis JSON from Phase 1
            cluster_name: Name of the AKS cluster
            cluster_id: Unique cluster identifier
            max_retries: Number of API retry attempts (uses env CLAUDE_MAX_RETRIES if None)
            
        Returns:
            KubeOptImplementationPlan object with structured recommendations
        """
        # Get max_retries from environment if not provided
        if max_retries is None:
            max_retries = int(os.getenv("CLAUDE_MAX_RETRIES", 1))  # Default to 1 for cost savings
        # Build optimized context based on data size
        optimized_context = self.context_builder.build_optimized_context(enhanced_input, cluster_name)
        
        # Log optimization details
        original_tokens = self.context_builder.count_tokens(json.dumps(enhanced_input, indent=2))
        optimized_tokens = self.context_builder.count_tokens(json.dumps(optimized_context, indent=2))
        optimization_report = self.context_builder.get_optimization_report(
            original_tokens, optimized_tokens, optimized_context.get('context_type', 'unknown')
        )
        
        self.logger.info(f"Context optimization: {optimization_report}")
        
        # Build prompts with optimized context
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(optimized_context, cluster_name)
        
        for attempt in range(max_retries):
            try:
                # BEFORE making API call: Check cost limit
                estimated_cost = (2284 * 0.25 + 3000 * 1.25) / 1_000_000  # ~$0.004
                
                if not check_cost_limit(estimated_cost):
                    raise Exception("Daily cost limit exceeded - blocking Claude API call")
                
                self.logger.info(f"Generating plan for cluster {cluster_name} (attempt {attempt + 1})")
                
                response = await asyncio.to_thread(
                    self.client.messages.create,
                    model=self.model,
                    max_tokens=self.max_output_tokens,
                    temperature=0.3,
                    system=system_prompt,
                    messages=[{
                        "role": "user",
                        "content": user_prompt
                    }]
                )
                
                # Add response inspection before processing
                print(f"\n{'─'*70}")
                print(f"📥 RAW RESPONSE FROM CLAUDE")
                print(f"{'─'*70}")
                
                # Show response metadata
                print(f"Response type: {type(response)}")
                print(f"Response attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}")
                
                if hasattr(response, 'usage'):
                    print(f"\nToken usage:")
                    print(f"   Input: {response.usage.input_tokens}")
                    print(f"   Output: {response.usage.output_tokens}")
                
                if hasattr(response, 'content'):
                    content = response.content[0].text
                    print(f"\nContent length: {len(content)} characters")
                    print(f"\nFirst 1000 characters:")
                    print(content[:1000])
                    print(f"\n...")
                    print(f"\nLast 500 characters:")
                    print(content[-500:])
                
                print(f"{'─'*70}\n")
                
                # Extract token usage and calculate costs
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                
                # Calculate cost (Claude Haiku pricing)
                input_cost = (input_tokens * 0.25) / 1_000_000  # Haiku: $0.25 per 1M input tokens
                output_cost = (output_tokens * 1.25) / 1_000_000  # Haiku: $1.25 per 1M output tokens
                total_cost = input_cost + output_cost
                
                # Log detailed usage
                print(f"\n{'='*60}")
                print(f"💰 CLAUDE API COST BREAKDOWN")
                print(f"{'='*60}")
                print(f"Model: {self.model}")
                print(f"Input tokens:  {input_tokens:,} × $0.25/1M = ${input_cost:.6f}")
                print(f"Output tokens: {output_tokens:,} × $1.25/1M = ${output_cost:.6f}")
                print(f"{'─'*60}")
                print(f"Total cost: ${total_cost:.4f}")
                print(f"{'='*60}\n")
                
                # Warning if output is close to limit
                if output_tokens > self.max_output_tokens * 0.9:
                    print(f"⚠️  WARNING: Output tokens ({output_tokens}) near limit ({self.max_output_tokens})")
                    print(f"   Plan may be truncated. Consider increasing max_tokens if needed.")
                
                # Track costs in log file
                tracker = get_cost_tracker()
                tracker.log_cost(
                    cluster_id=cluster_id,
                    model=self.model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost=total_cost,
                    success=True
                )
                
                # Extract JSON from response with detailed logging
                try:
                    plan_json = self._extract_json(response.content[0].text)
                    print(f"✅ JSON parsing succeeded")
                    print(f"   Keys in plan_json: {list(plan_json.keys())}")
                except Exception as parse_error:
                    print(f"❌ JSON PARSING FAILED!")
                    print(f"   Error: {parse_error}")
                    print(f"\n   Raw content that failed to parse:")
                    print(f"   {response.content[0].text}")
                    raise
                
                # Add required fields if missing
                if 'generated_at' not in plan_json:
                    plan_json['generated_at'] = datetime.utcnow().isoformat()
                if 'cluster_id' not in plan_json:
                    plan_json['cluster_id'] = cluster_id
                if 'version' not in plan_json:
                    plan_json['version'] = "1.0"
                if 'generated_by' not in plan_json:
                    plan_json['generated_by'] = f"claude-api-{self.model}"
                
                # Validate against schema with context optimization info
                try:
                    plan = self.validator.validate(plan_json, cluster_id, cluster_name, optimization_report)
                    print(f"✅ Validation succeeded")
                except Exception as validation_error:
                    print(f"❌ VALIDATION FAILED!")
                    print(f"   Error: {validation_error}")
                    print(f"\n   Plan dict that failed validation:")
                    print(json.dumps(plan_json, indent=2)[:2000])
                    raise
                
                # Add metadata including optimization info
                plan.generated_at = datetime.utcnow()
                plan.version = "1.0"
                plan.generated_by = f"claude-api-{self.model}"
                
                # Add context optimization metadata to plan
                plan.metadata.context_optimization = {
                    "original_tokens": original_tokens,
                    "optimized_tokens": optimized_tokens,
                    "optimization_strategy": optimized_context.get('context_type'),
                    "reduction_percentage": optimization_report.get('reduction_percentage', 0)
                }
                
                self.logger.info(f"Successfully generated plan with {plan.total_actions} actions")
                return plan
                
            except anthropic.NotFoundError as e:
                # 404 = Model doesn't exist - DON'T RETRY (wastes money!)
                print(f"❌ Model not found: {self.model}")
                print(f"   This is a configuration error, not a temporary issue.")
                print(f"   Retrying won't help and costs money!")
                raise e  # Fail immediately, don't retry
                
            except anthropic.RateLimitError as e:
                # Rate limit - retry with exponential backoff
                if attempt == max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                print(f"⚠️ Rate limited, waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
                
            except anthropic.APIError as e:
                # Other API errors - retry
                if attempt == max_retries - 1:
                    print(f"❌ All {max_retries} attempts failed")
                    raise
                wait_time = 2 ** attempt
                print(f"⚠️ API error (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"   This means Claude didn't return valid JSON")
                if attempt < max_retries - 1:
                    print(f"⚠️ This retry will cost additional money!")
                    wait_time = 2 ** attempt
                    print(f"   Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"❌ All {max_retries} attempts failed - no more retries")
                    # Don't raise here - let it fall through to the final error
                    
            except Exception as e:
                print(f"\n{'='*70}")
                print(f"🔍 DETAILED ERROR ANALYSIS")
                print(f"{'='*70}")
                
                # Show error type and message
                print(f"\nError Type: {type(e).__name__}")
                print(f"Error Message: {str(e)}")
                
                # If it's from Claude API, show response details
                if hasattr(e, 'response'):
                    print(f"\nAPI Response:")
                    print(f"   Status: {e.response.status_code if hasattr(e.response, 'status_code') else 'N/A'}")
                    print(f"   Body: {e.response.text if hasattr(e.response, 'text') else 'N/A'}")
                
                # Show what we sent to Claude
                print(f"\nContext sent to Claude:")
                print(f"   Cluster: {cluster_name}")
                print(f"   Input keys: {list(optimized_context.keys())}")
                if 'optimization_metadata' in optimized_context:
                    print(f"   Optimization: {optimized_context['optimization_metadata']}")
                
                # Show response if we got one
                if 'response' in locals():
                    print(f"\nClaude Response:")
                    print(f"   Content length: {len(response.content[0].text) if hasattr(response, 'content') else 'N/A'}")
                    print(f"   First 500 chars: {response.content[0].text[:500] if hasattr(response, 'content') else 'N/A'}")
                
                # Show parsing attempt
                if 'plan_json' in locals():
                    print(f"\nParsed plan keys: {list(plan_json.keys())}")
                
                # Show validation errors
                if 'validation' in str(e).lower():
                    print(f"\n⚠️ This looks like a VALIDATION error")
                    print(f"   The API call succeeded, but the response didn't pass validation")
                
                # Show full traceback
                import traceback
                print(f"\nFull Traceback:")
                print(traceback.format_exc())
                
                print(f"{'='*70}\n")
                
                # Save the failing input for debugging
                debug_file = f"debug_failed_input_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                try:
                    with open(debug_file, 'w') as f:
                        json.dump({
                            'cluster_name': cluster_name,
                            'cluster_id': cluster_id,
                            'optimized_context': optimized_context,
                            'error': str(e),
                            'error_type': type(e).__name__,
                            'timestamp': datetime.now().isoformat(),
                            'attempt': attempt + 1,
                            'model': self.model
                        }, f, indent=2, default=str)
                    
                    print(f"💾 Failed input saved to: {debug_file}")
                    print(f"   Use this file to reproduce the error!")
                except Exception as save_error:
                    print(f"⚠️ Could not save debug file: {save_error}")
                
                if attempt < max_retries - 1:
                    print(f"⚠️ This retry will cost additional money!")
                    wait_time = 2 ** attempt
                    print(f"   Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"❌ All {max_retries} attempts failed - no more retries")
                    # Don't raise here - let it fall through to the final error
                
        error_msg = (
            f"Claude API plan generation failed after {max_retries} attempts for cluster {cluster_name}. "
            f"Model: {self.model}. Check API key, network connectivity, and model availability. "
            f"This is a production system - no fallback plans will be generated."
        )
        self.logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    async def generate_plan_split(
        self,
        enhanced_input: dict,
        cluster_name: str,
        cluster_id: str
    ) -> dict:
        """
        Generate complete plan using two API calls (for Haiku).
        
        Call 1: Core implementation plan (~3,000 tokens)
        Call 2: Detailed analysis (~2,500 tokens)
        
        Returns: Combined complete plan dictionary
        """
        
        # Check if workload batching is needed
        from .workload_batcher import WorkloadBatcher
        batcher = WorkloadBatcher(max_tokens_per_batch=50000)
        
        enhanced_tokens = batcher.estimate_tokens(enhanced_input)
        
        # SMART ROUTING: Use hierarchical planning for multi-workload scenarios
        workload_count = len(enhanced_input.get('workloads', []))
        
        if enhanced_tokens <= 50000 and workload_count <= 20:
            print(f"\n{'='*70}")
            print(f"🔀 SPLIT GENERATION MODE (2 API Calls)")
            print(f"{'='*70}")
            print(f"Cluster: {cluster_name}")
            print(f"Model: {self.model}")
            print(f"Enhanced input: {enhanced_tokens:,} tokens (no batching needed)")
            print(f"Expected cost: ~$0.008 (2 × $0.004)")
            print(f"{'='*70}\n")
            
            # Use original enhanced input directly
            context = enhanced_input
        else:
            # Use hierarchical planning for large clusters
            from .hierarchical_planner import HierarchicalPlanner
            hierarchical_planner = HierarchicalPlanner(self, max_tokens_per_batch=45000)
            
            return await hierarchical_planner.generate_hierarchical_plan(
                enhanced_input, cluster_name, cluster_id
            )
        
        # Continue with original split mode for smaller inputs
        context = enhanced_input
        
        # Track totals
        total_input_tokens = 0
        total_output_tokens = 0
        total_cost = 0.0
        
        # ═══════════════════════════════════════════════════════
        # CALL 1: CORE IMPLEMENTATION PLAN
        # ═══════════════════════════════════════════════════════
        
        print(f"{'─'*70}")
        print(f"📤 CALL 1/2: Generating core implementation plan...")
        print(f"{'─'*70}")
        
        core_system_prompt = self._build_core_plan_system_prompt()
        core_user_prompt = self._build_core_plan_user_prompt(context, cluster_name)
        
        try:
            core_response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=self.max_output_tokens,  # Use configured max tokens
                temperature=0.3,
                system=core_system_prompt,
                messages=[{"role": "user", "content": core_user_prompt}]
            )
            
            # Track usage
            call1_input = core_response.usage.input_tokens
            call1_output = core_response.usage.output_tokens
            call1_cost = self._calculate_cost(call1_input, call1_output)
            
            total_input_tokens += call1_input
            total_output_tokens += call1_output
            total_cost += call1_cost
            
            print(f"✅ Call 1 complete")
            print(f"   Input: {call1_input:,} tokens")
            print(f"   Output: {call1_output:,} tokens ({call1_output/4000*100:.1f}% of limit)")
            print(f"   Cost: ${call1_cost:.6f}")
            
            # Parse JSON
            response_text = core_response.content[0].text
            print(f"📥 Raw response preview: {response_text[:500]}...")
            
            try:
                core_plan = self._extract_json_from_response(response_text)
                if not core_plan:
                    raise ValueError("Failed to extract JSON from core plan response")
                print(f"✅ Core plan parsed: {list(core_plan.keys())}")
            except Exception as parse_error:
                print(f"❌ JSON parsing failed!")
                print(f"   Error: {parse_error}")
                print(f"   Full response:")
                print(f"   {response_text}")
                raise ValueError(f"Failed to parse JSON: {parse_error}")
            
        except Exception as e:
            print(f"❌ Call 1 failed: {e}")
            raise RuntimeError(f"Core plan generation failed: {e}")
        
        # ═══════════════════════════════════════════════════════
        # CALL 2: DETAILED ANALYSIS
        # ═══════════════════════════════════════════════════════
        
        print(f"\n{'─'*70}")
        print(f"📤 CALL 2/2: Generating detailed analysis...")
        print(f"{'─'*70}")
        
        analysis_system_prompt = self._build_analysis_system_prompt()
        analysis_user_prompt = self._build_analysis_user_prompt(context, cluster_name)
        
        try:
            analysis_response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=3500,  # Increased for comprehensive analysis
                temperature=0.3,
                system=analysis_system_prompt,
                messages=[{"role": "user", "content": analysis_user_prompt}]
            )
            
            # Track usage
            call2_input = analysis_response.usage.input_tokens
            call2_output = analysis_response.usage.output_tokens
            call2_cost = self._calculate_cost(call2_input, call2_output)
            
            total_input_tokens += call2_input
            total_output_tokens += call2_output
            total_cost += call2_cost
            
            print(f"✅ Call 2 complete")
            print(f"   Input: {call2_input:,} tokens")
            print(f"   Output: {call2_output:,} tokens ({call2_output/3500*100:.1f}% of limit)")
            print(f"   Cost: ${call2_cost:.6f}")
            
            # Parse JSON
            analysis = self._extract_json_from_response(analysis_response.content[0].text)
            
            if not analysis:
                print(f"⚠️ Call 2 failed to parse - using minimal analysis")
                analysis = self._get_minimal_analysis()
            else:
                print(f"✅ Analysis parsed: {list(analysis.keys())}")
            
        except Exception as e:
            print(f"⚠️ Call 2 failed: {e}")
            print(f"   Proceeding with core plan only")
            analysis = self._get_minimal_analysis()
            # Don't raise - core plan is enough to proceed
        
        # ═══════════════════════════════════════════════════════
        # MERGE AND RETURN
        # ═══════════════════════════════════════════════════════
        
        print(f"\n{'─'*70}")
        print(f"🔗 Merging results...")
        print(f"{'─'*70}")
        
        # Combine into complete plan
        complete_plan_dict = {
            'implementation_plan': {
                # From Call 1 (Core)
                'metadata': core_plan.get('metadata', {}),
                'implementation_summary': core_plan.get('implementation_summary', {}),
                'phases': core_plan.get('phases', []),
                'roi_summary': core_plan.get('roi_summary', {}),
                'monitoring': core_plan.get('monitoring', {}),
                'next_steps': core_plan.get('next_steps', []),
                
                # From Call 2 (Analysis)
                'cluster_dna_analysis': analysis.get('cluster_dna_analysis', {}),
                'build_quality_assessment': analysis.get('build_quality_assessment', {}),
                'naming_conventions_analysis': analysis.get('naming_conventions_analysis', {}),
                'roi_analysis': analysis.get('roi_analysis', {}),
                'review_schedule': analysis.get('review_schedule', []),
            }
        }
        
        # Add required fields for validation
        if 'generated_at' not in complete_plan_dict:
            complete_plan_dict['generated_at'] = datetime.utcnow().isoformat()
        if 'cluster_id' not in complete_plan_dict:
            complete_plan_dict['cluster_id'] = cluster_id
        if 'version' not in complete_plan_dict:
            complete_plan_dict['version'] = "1.0"
        if 'generated_by' not in complete_plan_dict:
            complete_plan_dict['generated_by'] = f"claude-api-{self.model}-split"
        
        # ═══════════════════════════════════════════════════════
        # PROPER VALIDATION WITH PYDANTIC SCHEMAS
        # ═══════════════════════════════════════════════════════
        
        print(f"\n{'─'*70}")
        print(f"🔍 Validating with Pydantic schemas...")
        print(f"{'─'*70}")
        
        # 🔧 SMART MAPPING: Handle Claude's structure variations
        implementation_summary = core_plan.get('implementation_summary', {})
        executive_summary = core_plan.get('executive_summary', {})
        
        # Map executive_summary fields to implementation_summary if empty
        if not implementation_summary and executive_summary:
            print("🔄 Mapping executive_summary to implementation_summary for schema compatibility...")
            implementation_summary = executive_summary
        
        # Combine the two responses
        combined_plan_content = {
            'metadata': core_plan.get('metadata', {}),
            'implementation_summary': implementation_summary,
            'phases': core_plan.get('phases', []),
            'roi_summary': core_plan.get('roi_summary', {}),
            'monitoring': core_plan.get('monitoring', {}),
            'next_steps': core_plan.get('next_steps', []),
            
            # Optional from Call 2
            'cluster_dna_analysis': analysis.get('cluster_dna_analysis'),
            'build_quality_assessment': analysis.get('build_quality_assessment'),
            'naming_conventions_analysis': analysis.get('naming_conventions_analysis'),
            'roi_analysis': analysis.get('roi_analysis'),
            'review_schedule': analysis.get('review_schedule'),
        }
        
        # Import split mode schemas
        from .plan_schema import SplitModeImplementationPlan
        from pydantic import ValidationError
        
        # Create and validate with proper Pydantic model
        try:
            complete_plan = SplitModeImplementationPlan.create_validated(
                data=combined_plan_content,
                cluster_id=cluster_id,
                generated_by=f"claude-api-{self.model}-split"
            )
            
            if complete_plan.validation_passed:
                print(f"✅ Plan content validated successfully")
                print(f"   Total actions: {complete_plan.total_actions}")
                print(f"   Total phases: {len(complete_plan.phases)}")
                print(f"   Total savings: ${complete_plan.total_savings_monthly:.2f}/month")
                print(f"   Schema version: {complete_plan.schema_version}")
            else:
                print(f"⚠️ Plan created but validation failed")
                print(f"   Validation errors: {len(complete_plan.validation_errors or [])}")
                for error in (complete_plan.validation_errors or []):
                    print(f"     - {error}")
                print(f"   Plan still usable but may have data quality issues")
            
        except Exception as critical_error:
            print(f"❌ CRITICAL VALIDATION FAILURE!")
            print(f"Schema validation errors:")
            print(f"   Error: {critical_error}")
            
            # Save debug data
            debug_file = f"debug_validation_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(debug_file, 'w') as f:
                json.dump({
                    'error': str(critical_error),
                    'raw_data': combined_plan_content,
                    'cluster_id': cluster_id,
                    'model': self.model
                }, f, indent=2, default=str)
            
            print(f"💾 Debug data saved to: {debug_file}")
            print(f"\nOptions:")
            print(f"1. Fix the prompt to return correct structure")
            print(f"2. Update schema to accept Claude's format")
            print(f"3. Add data transformation before validation")
            
            raise RuntimeError(f"Plan validation failed: {critical_error}")
        
        # Add metadata including split mode info
        complete_plan.generated_at = datetime.utcnow()
        complete_plan.version = "1.0"
        complete_plan.generated_by = f"claude-api-{self.model}-split"
        
        # ═══════════════════════════════════════════════════════
        # SUMMARY
        # ═══════════════════════════════════════════════════════
        
        print(f"\n{'='*70}")
        print(f"💰 SPLIT GENERATION COMPLETE")
        print(f"{'='*70}")
        print(f"Total input tokens:  {total_input_tokens:,}")
        print(f"Total output tokens: {total_output_tokens:,}")
        print(f"Total tokens:        {total_input_tokens + total_output_tokens:,}")
        print(f"Total cost:          ${total_cost:.6f}")
        print(f"")
        print(f"✅ Full rich plan generated with 2 API calls!")
        print(f"   Plan: {complete_plan.total_actions} actions across {len(complete_plan.phases)} phases")
        print(f"   Cost: 47% cheaper than Sonnet 3.5 single call")
        print(f"{'='*70}\n")
        
        self.logger.info(f"Successfully generated split mode plan with {complete_plan.total_actions} actions")
        return complete_plan
    
    async def _process_single_batch(self, batch_context: Dict, cluster_name: str, cluster_id: str) -> Dict:
        """Process a single workload batch using split mode"""
        
        batch_meta = batch_context.get('_batch_metadata', {})
        print(f"Processing batch {batch_meta.get('batch_number', 1)}: {batch_meta.get('workload_count', 0)} workloads")
        
        # ═══════════════════════════════════════════════════════
        # CALL 1: CORE IMPLEMENTATION PLAN FOR THIS BATCH
        # ═══════════════════════════════════════════════════════
        
        core_system_prompt = self._build_core_plan_system_prompt()
        core_user_prompt = self._build_core_plan_user_prompt(batch_context, cluster_name)
        
        try:
            core_response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=self.max_output_tokens,  # Use configured max tokens for comprehensive plans
                temperature=0.3,
                system=core_system_prompt,
                messages=[{"role": "user", "content": core_user_prompt}]
            )
            
            # Parse JSON
            response_text = core_response.content[0].text
            core_plan = self._extract_json_from_response(response_text)
            
            if not core_plan:
                raise ValueError("Failed to extract JSON from core plan response")
            
            print(f"✅ Batch core plan parsed: {list(core_plan.keys())}")
            
        except Exception as e:
            print(f"❌ Batch core plan failed: {e}")
            raise RuntimeError(f"Batch core plan generation failed: {e}")
        
        # ═══════════════════════════════════════════════════════
        # CALL 2: DETAILED ANALYSIS FOR THIS BATCH
        # ═══════════════════════════════════════════════════════
        
        analysis_system_prompt = self._build_analysis_system_prompt()
        analysis_user_prompt = self._build_analysis_user_prompt(batch_context, cluster_name)
        
        try:
            analysis_response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=3500,
                temperature=0.3,
                system=analysis_system_prompt,
                messages=[{"role": "user", "content": analysis_user_prompt}]
            )
            
            # Parse JSON
            analysis = self._extract_json_from_response(analysis_response.content[0].text)
            
            if not analysis:
                print(f"⚠️ Batch analysis failed - using minimal analysis")
                analysis = self._get_minimal_analysis()
            else:
                print(f"✅ Batch analysis parsed: {list(analysis.keys())}")
                
        except Exception as e:
            print(f"⚠️ Batch analysis failed: {e}")
            analysis = self._get_minimal_analysis()
        
        # ═══════════════════════════════════════════════════════
        # COMBINE BATCH RESULTS
        # ═══════════════════════════════════════════════════════
        
        batch_plan = {
            'implementation_plan': {
                # From Call 1 (Core)
                'metadata': core_plan.get('metadata', {}),
                'implementation_summary': core_plan.get('implementation_summary', {}),
                'phases': core_plan.get('phases', []),
                'roi_summary': core_plan.get('roi_summary', {}),
                'monitoring': core_plan.get('monitoring', {}),
                'next_steps': core_plan.get('next_steps', []),
                
                # From Call 2 (Analysis)
                'cluster_dna_analysis': analysis.get('cluster_dna_analysis', {}),
                'build_quality_assessment': analysis.get('build_quality_assessment', {}),
                'naming_conventions_analysis': analysis.get('naming_conventions_analysis', {}),
                'roi_analysis': analysis.get('roi_analysis', {}),
                'review_schedule': analysis.get('review_schedule', []),
            },
            'source_data': batch_context  # Track which data was used
        }
        
        return batch_plan
    
    def _build_system_prompt(self) -> str:
        """
        Defines Claude's role and output format for comprehensive AKS implementation plans.
        Enhanced to generate comprehensive plans with health analysis, standards compliance, 
        DNS analysis, and detailed executable commands.
        """
        # Load standards from YAML configuration
        loader = get_standards_loader()
        scoring_standards = loader.load_scoring_standards()
        impl_standards = loader.load_implementation_standards()
        
        cpu_standards = loader.get_cpu_utilization_target()
        memory_standards = loader.get_memory_utilization_target()
        hpa_standards = loader.get_hpa_standards()
        opt_thresholds = loader.get_optimization_thresholds()
        
        # Get JSON schema (already a string, no formatting issues)
        schema_json = json.dumps(KUBEOPT_IMPLEMENTATION_PLAN_SCHEMA, indent=2)
        
        # Build dynamic standards section with f-string
        standards_section = f"""These standards are based on: CNCF, FinOps Foundation, Azure Well-Architected Framework, Google SRE
Configuration Version: {scoring_standards.get('version', 'unknown')} / {impl_standards.get('version', 'unknown')}

CPU Utilization Standards:
- Target Range: {cpu_standards['target_min']:.0f}%-{cpu_standards['target_max']:.0f}%
- Optimal: {cpu_standards['optimal']:.0f}%
- Source: {cpu_standards['source']}

Memory Utilization Standards:
- Target Range: {memory_standards['target_min']:.0f}%-{memory_standards['target_max']:.0f}%
- Optimal: {memory_standards['optimal']:.0f}%
- Source: {memory_standards['source']}

HPA Standards:
- Target CPU Utilization: {hpa_standards['target_cpu_utilization']:.0f}%
- Target Memory Utilization: {hpa_standards['target_memory_utilization']:.0f}%
- Coverage Target: {hpa_standards['coverage_target']:.0f}% of eligible workloads
- Default Min Replicas: {hpa_standards['min_replicas_default']}
- Default Max Replicas: {hpa_standards['max_replicas_default']}
- Source: {hpa_standards['source']}

Optimization Decision Thresholds:
- Maximum Payback Period: {opt_thresholds['payback_threshold_months']} months
- Minimum Monthly Savings: ${opt_thresholds['minimum_monthly_savings']:.2f}
- Minimum Savings Percentage: {opt_thresholds['minimum_savings_percentage']*100:.1f}%
- High Priority Threshold: ${opt_thresholds['high_priority_savings']:.2f}/month"""
        
        # Enhanced schema section with comprehensive structure matching expected format
        comprehensive_structure = """CRITICAL: YOUR RESPONSE MUST EXACTLY MATCH THIS STRUCTURE:

{
  "implementation_plan": {
    "metadata": {
      "plan_id": "aks-dpl-mad-dev-ne2-1-comprehensive-optimization-plan",
      "cluster_name": "ACTUAL_CLUSTER_NAME",
      "resource_group": "ACTUAL_RESOURCE_GROUP", 
      "subscription_id": "ACTUAL_SUBSCRIPTION_ID",
      "generated_date": "2025-11-18",
      "plan_version": "2.0",
      "analysis_confidence": "high",
      "implementation_complexity": "high",
      "estimated_duration_days": 45
    },
    "executive_summary": {
      "current_monthly_cost": 1842.15,
      "potential_monthly_savings": 581.07,
      "savings_percentage": 31.5,
      "annual_savings": 6972.84,
      "payback_period_months": 2.1,
      "roi_12_months": 247.7,
      "optimization_opportunities": 674,
      "critical_issues": 12,
      "implementation_phases": 6
    },
    "cluster_health_analysis": {
      "overall_cluster_score": 42,
      "cluster_grade": "D+",
      "health_categories": {
        "cost_efficiency": { 
          "score": 18, 
          "grade": "F", 
          "issues": ["674 workloads over-provisioned (99.8% of total)", "CPU utilization at 30.9% (target: 70-80%)", "Zero HPA coverage (target: 80%)"]
        },
        "performance_optimization": { 
          "score": 35, 
          "grade": "F", 
          "issues": ["Critical: momo-aggregator at 3813% CPU utilization", "High: subscription-fulfillment-system at 166% CPU", "No resource limits on 45% of workloads"]
        },
        "security_compliance": { 
          "score": 55, 
          "grade": "D", 
          "issues": ["Network policies not implemented", "Pod security standards not enforced", "No admission controller policies"]
        },
        "operational_excellence": { 
          "score": 48, 
          "grade": "D-", 
          "issues": ["No monitoring stack deployed", "Missing backup strategies", "No disaster recovery plan"]
        },
        "dns_analysis": { 
          "score": 62, 
          "grade": "D+", 
          "current_setup": "Azure DNS with CoreDNS",
          "issues": ["DNS caching not optimized", "External DNS queries high (cost impact)", "No DNS monitoring configured"],
          "recommendations": ["Enable DNS caching optimization", "Implement DNS query monitoring", "Configure internal DNS forwarding"]
        }
      }
    },
    "standards_compliance_analysis": {
      "cncf_finops_score": 23,
      "azure_waf_score": 41,
      "kubernetes_best_practices_score": 38,
      "compliance_gaps": {
        "finops_foundation": ["No cost allocation tags", "Missing resource quotas", "No showback/chargeback", "Lack of cost anomaly detection"],
        "azure_well_architected": ["Poor resource utilization", "No autoscaling configured", "Missing monitoring baselines", "Inadequate backup strategy"],
        "kubernetes_standards": ["No resource limits/requests ratio optimization", "Missing liveness/readiness probes on 67% workloads", "No pod security policies"]
      }
    },
    "phases": [...],
    "roi_analysis": {
      "implementation_costs": {"personnel_hours": 180, "hourly_rate": 150, "total_implementation_cost": 30700},
      "savings_timeline": {"month_1": 127.50, "month_6": 581.07, "annual_savings": 6972.84},
      "break_even_analysis": {"break_even_month": 4.4, "roi_12_months": 22.7}
    },
    "success_metrics": {...},
    "monitoring_and_alerting": {...},
    "disaster_recovery": {
      "backup_strategy": {"etcd_backups": "Every 6 hours to Azure Storage", "recovery_time_objective": "2 hours"},
      "rollback_procedures": {"deployment_rollback": "kubectl rollout undo", "configuration_rollback": "ArgoCD sync to previous version"}
    },
    "compliance_and_governance": {
      "policy_frameworks": ["CIS Kubernetes Benchmark", "Azure Security Baseline", "FinOps Foundation Principles"],
      "audit_requirements": {"configuration_changes": "Git history + ArgoCD logs", "access_logs": "Azure AD integration"},
      "compliance_scores": {"security_baseline": "Target: 90%", "cost_optimization": "Target: 85%"}
    }
  },
  "next_steps": [
    "Week 1: Execute Phase 1 (Critical Performance Issues)",
    "Week 2-3: Execute Phase 2 (Infrastructure Optimization)",
    "Month 3: Full optimization review and fine-tuning",
    "Month 6: ROI assessment and next optimization cycle"
  ]
}

CRITICAL: Your response MUST be wrapped in this exact structure. Do not put phases, roi_analysis, etc. at the top level."""
        
        # Enhanced command generation requirements
        command_excellence = """CRITICAL COMMAND GENERATION REQUIREMENTS:

YOU MUST GENERATE EXACT, EXECUTABLE COMMANDS USING REAL DATA:

✅ **REAL RESOURCE NAMES**: Use actual deployment names, namespaces, and values from the input data
✅ **COPY-PASTE READY**: Every command must be executable without modification
✅ **COMPLETE SEQUENCES**: Backup → Execute → Verify → Monitor for each action
✅ **SPECIFIC VALUES**: Use actual CPU/memory values, not placeholders like {deployment}
✅ **ROLLBACK READY**: Provide exact rollback commands for every change

COMMAND EXAMPLES TO FOLLOW:
- kubectl patch deployment momo-aggregator -n madapi-dev -p '{...real JSON...}'
- az aks update --resource-group rg-dpl-mad-dev-ne2-2 --name aks-dpl-mad-dev-ne2-1 ...
- kubectl autoscale deployment subscription-fulfillment-system -n madapi-dev --cpu-percent=70

SCORING AND GRADING METHODOLOGY:
- Cost Efficiency (0-100): Based on optimization_candidates %, utilization efficiency
- Performance (0-100): Based on over/under-utilized workloads, resource limits coverage
- Security (0-100): Based on network policies, admission controllers, RBAC coverage
- Operations (0-100): Based on monitoring, backup, disaster recovery readiness
- DNS (0-100): Based on CoreDNS config optimization, caching efficiency

GRADE MAPPING: 90-100=A+, 80-89=A, 70-79=B+, 60-69=B, 50-59=C+, 40-49=C, 30-39=D+, 20-29=D, 0-19=F"""
        
        # Schema and format section
        schema_section = f"""SCHEMA YOU MUST FOLLOW:
{schema_json}

OUTPUT FORMAT:
- Start your response with ```json
- End with ```
- No markdown except the code fence
- No explanatory text outside the JSON
- Structure must match the enhanced comprehensive schema exactly"""
        
        # Combine all sections with ENHANCED command generation instructions
        return f"""🚀 You are an ELITE Kubernetes FinOps Expert & Azure Solutions Architect specializing in comprehensive AKS cost optimization.

Your mission: Generate a COMPREHENSIVE, PRODUCTION-READY implementation plan that delivers measurable cost savings and operational excellence.

═══════════════════════════════════════════════════════════════════════════════════════════
🎯 COMPREHENSIVE IMPLEMENTATION PLAN REQUIREMENTS
═══════════════════════════════════════════════════════════════════════════════════════════

{comprehensive_structure}

═══════════════════════════════════════════════════════════════════════════════════════════
🎯 CRITICAL DATA USAGE REQUIREMENTS  
═══════════════════════════════════════════════════════════════════════════════════════════

**YOU MUST USE REAL DATA FROM THE INPUT:**

✅ **CLUSTER INFORMATION**: Use actual cluster_name, resource_group, subscription_id
✅ **COST SAVINGS**: Use cost_savings.total_monthly_savings, annual_savings, savings_percentage  
✅ **WORKLOAD NAMES**: Use actual workload names from workloads array
✅ **NAMESPACES**: Use actual namespace names from workloads
✅ **RESOURCE SPECS**: Use actual CPU/memory from resources.requests and actual_usage
✅ **OPTIMIZATION CANDIDATES**: Use workloads with optimization_candidate: true
✅ **NODE INFORMATION**: Use actual vm_sku, node_count from node_pools
✅ **UTILIZATION DATA**: Use actual_usage.cpu/memory percentages

**CALCULATE PRECISE VALUES:**
- Right-sizing: (current_requests - optimal_usage*1.2) × Azure_pricing_rates
- HPA savings: estimated_replica_reduction × pod_cost  
- Infrastructure: spot_instance_potential × 70% savings
- Network: optimization_opportunities.networking_cost × improvement_percentage

{command_excellence}

═══════════════════════════════════════════════════════════════════════════════════════════
🎯 PHASE STRUCTURE REQUIREMENTS
═══════════════════════════════════════════════════════════════════════════════════════════

**PHASE 1: CRITICAL ISSUES** (1-3 days)
- Target: Workloads with >1000% CPU utilization or critical performance issues
- Focus: Immediate stability and obvious cost wins
- Risk: Very Low

**PHASE 2: INFRASTRUCTURE OPTIMIZATION** (4-10 days)  
- Target: Node pools, spot instances, cluster autoscaling
- Focus: Foundation for scaling and cost efficiency
- Risk: Low-Medium

**PHASE 3: WORKLOAD RIGHT-SIZING** (11-21 days)
- Target: Over-provisioned workloads based on actual usage
- Focus: Systematic resource optimization
- Risk: Medium  

**PHASE 4: AUTO-SCALING & GOVERNANCE** (22-35 days)
- Target: HPA/VPA implementation, resource quotas, policies
- Focus: Dynamic scaling and compliance
- Risk: Medium

**PHASE 5: MONITORING & SECURITY** (36-42 days)
- Target: Observability stack, security policies, cost governance
- Focus: Operational excellence and compliance
- Risk: Low

**PHASE 6: ADVANCED OPTIMIZATION** (43+ days)
- Target: ML-based scaling, GitOps, advanced features
- Focus: Future-proofing and innovation
- Risk: Low

{standards_section}

{schema_section}

═══════════════════════════════════════════════════════════════════════════════════════════
🎯 CRITICAL SUCCESS REQUIREMENTS
═══════════════════════════════════════════════════════════════════════════════════════════

**RESPOND WITH:**
- ONLY valid JSON wrapped in ```json code fence
- NO explanatory text before or after
- ALL strings in double quotes
- Numbers without symbols (no $, %, etc.)
- No trailing commas
- No comments inside JSON

**QUALITY STANDARDS:**
- Every command must be copy-paste executable
- Every savings estimate must be calculated from real data
- Every workload reference must use actual names
- Every metric must be measurable and specific
- Every timeline must be realistic and achievable

**YOUR MISSION: Generate the most comprehensive, executable, and profitable AKS optimization plan ever created.**"""
    
    def _build_user_prompt(self, optimized_context: Dict, cluster_name: str) -> str:
        """
        Builds user prompt from optimized context data.
        """
        context_type = optimized_context.get('context_type', 'complete')
        
        if context_type == 'complete':
            return self._build_complete_prompt(optimized_context, cluster_name)
        elif context_type == 'medium_optimization':
            return self._build_medium_prompt(optimized_context, cluster_name)
        else:  # aggressive_optimization
            # Use enhanced compact prompt with proper schema
            return self._build_enhanced_compact_prompt(optimized_context, cluster_name)
    
    def _build_complete_prompt(self, optimized_context: Dict, cluster_name: str) -> str:
        """Build enhanced prompt for complete data (small clusters) including cost savings."""
        enhanced_input = optimized_context.get('data', {})
        cost_analysis = enhanced_input.get('cost_analysis', {})
        cluster_info = enhanced_input.get('cluster_info', {})
        workloads = enhanced_input.get('workloads', [])
        node_pools = enhanced_input.get('node_pools', [])
        
        # Extract cost savings data (if available from our enhanced analysis)
        cost_savings = cost_analysis.get('cost_savings', {})
        total_cost = cost_analysis.get('total_cost', 0)
        total_savings = cost_savings.get('total_monthly_savings', 0)
        savings_breakdown = cost_savings.get('savings_breakdown', {})
        
        # Calculate optimization candidate count
        optimization_candidates = len([w for w in workloads if w.get('optimization_candidate', False)])
        
        # Extract critical workloads for specific targeting
        critical_workloads = []
        for workload in workloads:
            if workload.get('optimization_candidate', False):
                cpu_util = workload.get('cpu_utilization_percent', 0)
                memory_util = workload.get('memory_utilization_percent', 0)
                if cpu_util > 150 or memory_util > 150:  # Critical over-utilization
                    critical_workloads.append({
                        'name': workload.get('name', 'unknown'),
                        'namespace': workload.get('namespace', 'default'),
                        'cpu_util': cpu_util,
                        'memory_util': memory_util,
                        'current_cpu': workload.get('resources', {}).get('requests', {}).get('cpu', '0'),
                        'current_memory': workload.get('resources', {}).get('requests', {}).get('memory', '0')
                    })
        
        # Build critical workloads section
        critical_workloads_text = ""
        if critical_workloads:
            critical_workloads_text = "\n\nCRITICAL WORKLOADS REQUIRING IMMEDIATE ATTENTION:"
            for i, wl in enumerate(critical_workloads[:5]):  # Top 5 critical
                critical_workloads_text += f"""
- {wl['name']} (namespace: {wl['namespace']})
  - CPU Utilization: {wl['cpu_util']:.1f}% (CRITICAL - target: 70-80%)
  - Memory Utilization: {wl['memory_util']:.1f}%
  - Current CPU Request: {wl['current_cpu']}
  - Current Memory Request: {wl['current_memory']}
  - USE THIS EXACT NAME AND NAMESPACE IN ALL COMMANDS"""
        
        return f"""Generate a comprehensive implementation plan for AKS cluster: {cluster_name}

CLUSTER CONTEXT:
- Resource Group: {cluster_info.get('resource_group', 'unknown')}
- Subscription: {cluster_info.get('subscription_id', 'unknown')}
- Location: {cluster_info.get('location', 'unknown')}
- Kubernetes Version: {cluster_info.get('kubernetes_version', 'unknown')}
- Node Count: {cluster_info.get('node_count', 0)}
- Total Pods: {cluster_info.get('total_pods', 0)}
- Total Namespaces: {cluster_info.get('total_namespaces', 0)}

COST ANALYSIS SUMMARY:
- Current Monthly Cost: ${total_cost:.2f}
- Potential Monthly Savings: ${total_savings:.2f}
- Node Cost: ${cost_analysis.get('node_cost', 0):.2f}
- Storage Cost: ${cost_analysis.get('storage_cost', 0):.2f}
- Networking Cost: ${cost_analysis.get('networking_cost', 0):.2f}

OPTIMIZATION OPPORTUNITIES:
- Total Workloads: {len(workloads)}
- Optimization Candidates: {optimization_candidates}
- HPA Savings Potential: ${savings_breakdown.get('hpa_optimization_savings', 0):.2f}
- Right-sizing Savings: ${savings_breakdown.get('right_sizing_savings', 0):.2f}
- Infrastructure Savings: ${savings_breakdown.get('infrastructure_savings', 0):.2f}

OPTIMIZED CLUSTER ANALYSIS DATA:
```json
{json.dumps(context, indent=2)}
```

{critical_workloads_text}

REQUIREMENTS:
1. Generate a plan using the EXACT structure from the system prompt (implementation_plan wrapper)
2. Use REAL workload names and namespaces from the critical workloads list above
3. Include ALL enterprise sections: roi_analysis, disaster_recovery, compliance_and_governance
4. Generate workload-specific commands with actual names (e.g., kubectl patch deployment momo-aggregator -n madapi-dev)
5. Calculate precise savings per workload based on actual utilization data
6. Include comprehensive DNS analysis, compliance gaps, and timeline-based next steps
7. Ensure schema matches expected format exactly

CRITICAL: Wrap your entire response in the implementation_plan structure from the system prompt.

Generate the complete comprehensive implementation plan as valid JSON."""

    def _build_medium_prompt(self, optimized_context: Dict, cluster_name: str) -> str:
        """Build enhanced prompt for medium optimization (medium clusters) with cost savings."""
        cost_analysis = optimized_context.get('cost_analysis', {})
        executive_summary = optimized_context.get('executive_summary', {})
        workloads = optimized_context.get('workloads', [])
        
        cluster_summary = executive_summary.get('cluster_analysis_summary', {})
        opportunities = executive_summary.get('optimization_opportunities', [])
        
        # Extract cost savings data if available
        cost_savings = cost_analysis.get('cost_savings', {})
        total_savings = cost_savings.get('total_monthly_savings', 0)
        savings_breakdown = cost_savings.get('savings_breakdown', {})
        
        # Calculate optimization candidate count
        optimization_candidates = len([w for w in workloads if w.get('optimization_candidate', False)])
        
        return f"""Generate a comprehensive implementation plan for AKS cluster: {cluster_name}

CLUSTER: {cluster_name}
CONTEXT: Medium cluster analysis - Top 30 optimization targets with executive summary

EXECUTIVE SUMMARY:
- Total workloads: {cluster_summary.get('total_workloads', 0)}
- Monthly cost: ${cluster_summary.get('total_monthly_cost', 0):.2f}
- Potential monthly savings: ${total_savings:.2f}
- Optimization candidates: {optimization_candidates}
- Cost reduction potential: {cluster_summary.get('cost_reduction_percentage', 0):.1f}%

COST SAVINGS BREAKDOWN:
- HPA Optimization: ${savings_breakdown.get('hpa_optimization_savings', 0):.2f}
- Right-sizing Savings: ${savings_breakdown.get('right_sizing_savings', 0):.2f}
- Infrastructure Optimization: ${savings_breakdown.get('infrastructure_savings', 0):.2f}
- Network Optimization: ${savings_breakdown.get('networking_optimization_savings', 0):.2f}

KEY OPTIMIZATION OPPORTUNITIES:
{chr(10).join(f"- {opp}" for opp in opportunities)}

COST ANALYSIS:
```json
{json.dumps(cost_analysis, indent=2)}
```

TOP OPTIMIZATION TARGETS (30 highest impact workloads):
```json
{json.dumps(workloads, indent=2)}
```

CLUSTER PATTERNS:
```json
{json.dumps(executive_summary.get('workload_distribution', {}), indent=2)}
```

REQUIREMENTS:
1. Generate a comprehensive plan using the EXACT structure from the system prompt
2. Focus on the top 30 workloads provided for detailed recommendations
3. Use REAL workload names, namespaces, and resource values from the data
4. Include executable kubectl and Azure CLI commands with actual parameter values
5. Provide detailed cluster health analysis and standards compliance scoring
6. Include comprehensive ROI analysis and phased implementation timeline
7. Generate specific savings estimates for each optimization action

Generate the complete comprehensive implementation plan as valid JSON."""

    def _build_enhanced_compact_prompt(self, optimized_context: Dict, cluster_name: str) -> str:
        """Build enhanced compact prompt with proper schema and critical workload detection"""
        
        # Extract optimization targets (these contain the real workload data)
        optimization_targets = optimized_context.get('top_optimization_targets', [])
        cluster_overview = optimized_context.get('cluster_overview', {})
        executive_summary = optimized_context.get('executive_summary', {})
        
        # Extract critical workloads from optimization targets
        critical_workloads = []
        for target in optimization_targets[:5]:  # Top 5 critical
            cpu_util = target.get('cpu_utilization', 0)
            memory_util = target.get('memory_utilization', 0)
            if cpu_util > 100 or memory_util > 100:  # Critical threshold
                critical_workloads.append({
                    'name': target.get('name', 'unknown'),
                    'namespace': target.get('namespace', 'default'),
                    'cpu_util': cpu_util,
                    'memory_util': memory_util,
                    'current_cpu': target.get('cpu_request', '0'),
                    'current_memory': target.get('memory_request', '0')
                })
        
        # Build critical workloads section
        critical_workloads_text = ""
        if critical_workloads:
            critical_workloads_text = "\n\nCRITICAL WORKLOADS REQUIRING IMMEDIATE ATTENTION:"
            for wl in critical_workloads:
                critical_workloads_text += f"""
- {wl['name']} (namespace: {wl['namespace']})
  - CPU Utilization: {wl['cpu_util']:.1f}% (CRITICAL - target: 70-80%)
  - Memory Utilization: {wl['memory_util']:.1f}%
  - Current CPU Request: {wl['current_cpu']}
  - Current Memory Request: {wl['current_memory']}
  - USE THIS EXACT NAME AND NAMESPACE IN ALL COMMANDS"""
        
        return f"""Generate a comprehensive optimization plan for: {cluster_name}

CLUSTER CONTEXT:
- Total workloads: {executive_summary.get('total_workloads', 0)}
- Current monthly cost: ${executive_summary.get('current_monthly_cost', 0):.2f}
- Optimization opportunities: {executive_summary.get('optimization_opportunities', 0)}

TOP OPTIMIZATION TARGETS:
{json.dumps(optimization_targets, indent=2)}

{critical_workloads_text}

REQUIREMENTS:
1. Generate a plan using the EXACT structure from the system prompt (implementation_plan wrapper)
2. Use REAL workload names from critical workloads and optimization targets above
3. Include ALL enterprise sections: roi_analysis, disaster_recovery, compliance_and_governance
4. Generate workload-specific commands with actual names and namespaces
5. Include comprehensive DNS analysis and compliance gaps
6. Ensure schema matches expected format exactly

CRITICAL: Wrap your entire response in the implementation_plan structure from the system prompt.

Generate the complete comprehensive implementation plan as valid JSON."""

    def _build_compact_prompt(self, optimized_context: Dict, cluster_name: str) -> str:
        """Build enhanced prompt for aggressive optimization (large clusters) with cost savings."""
        cost_analysis = optimized_context.get('cost_analysis', {})
        executive_summary = optimized_context.get('executive_summary', {})
        aggregated_stats = optimized_context.get('aggregated_statistics', {})
        top_targets = optimized_context.get('top_optimization_targets', [])
        cluster_overview = optimized_context.get('cluster_overview', {})
        
        cluster_summary = executive_summary.get('cluster_analysis_summary', {})
        opportunities = executive_summary.get('optimization_opportunities', [])
        complexity = executive_summary.get('complexity_indicators', {})
        
        # Extract cost savings data if available
        cost_savings = cost_analysis.get('cost_savings', {})
        total_savings = cost_savings.get('total_monthly_savings', 0)
        savings_breakdown = cost_savings.get('savings_breakdown', {})
        
        # Calculate optimization potential
        optimization_candidates = len([t for t in top_targets if t.get('optimization_candidate', False)])
        
        return f"""Generate a comprehensive implementation plan for this large AKS cluster: {cluster_name}

CLUSTER: {cluster_name}
CONTEXT: Large cluster analysis - Aggregated statistics with top 10 optimization targets

CLUSTER OVERVIEW:
- Total workloads: {cluster_summary.get('total_workloads', 0)}
- Monthly cost: ${cluster_summary.get('total_monthly_cost', 0):.2f}
- Potential monthly savings: ${total_savings:.2f}
- Complexity score: {complexity.get('complexity_score', 0)}/100
- Namespaces: {complexity.get('namespace_count', 0)}
- Top optimization targets: {optimization_candidates}

COST SAVINGS POTENTIAL:
- HPA Optimization: ${savings_breakdown.get('hpa_optimization_savings', 0):.2f}
- Right-sizing Savings: ${savings_breakdown.get('right_sizing_savings', 0):.2f}
- Infrastructure Optimization: ${savings_breakdown.get('infrastructure_savings', 0):.2f}
- Network Optimization: ${savings_breakdown.get('networking_optimization_savings', 0):.2f}

KEY OPTIMIZATION OPPORTUNITIES:
{chr(10).join(f"- {opp}" for opp in opportunities)}

ESSENTIAL COST DATA:
```json
{json.dumps(cost_analysis, indent=2)}
```

AGGREGATED CLUSTER STATISTICS:
```json
{json.dumps(aggregated_stats, indent=2)}
```

TOP 10 OPTIMIZATION TARGETS (highest impact):
```json
{json.dumps(top_targets, indent=2)}
```

CLUSTER METADATA:
```json
{json.dumps(cluster_overview, indent=2)}
```

REQUIREMENTS FOR LARGE CLUSTER:
1. Generate a comprehensive plan using the EXACT structure from the system prompt
2. Focus recommendations on the top 10 targets provided
3. Use REAL workload names and resource values from the targets data
4. Generate scalable implementation phases suitable for large clusters
5. Include kubectl commands that work with multiple resources efficiently
6. Provide detailed cluster health analysis and standards compliance scoring
7. Calculate precise savings estimates based on aggregated data and actual targets
8. Consider cluster complexity in implementation timeline and risk assessment

Generate the complete comprehensive implementation plan as valid JSON."""

    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from Claude's response with enhanced error handling for escape issues."""
        text = text.strip()
        
        # Remove markdown code fences
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
            
        if text.endswith("```"):
            text = text[:-3]
            
        # Try to find JSON content
        text = text.strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"⚠️  Initial JSON parse failed: {e}")
            print(f"   Error location: line {getattr(e, 'lineno', '?')} column {getattr(e, 'colno', '?')}")
            print(f"   Error message: {str(e)}")
            print(f"   Attempting enhanced JSON cleaning...")
            
            # Try common fixes for Claude response issues
            if "Expecting property name enclosed in double quotes" in str(e):
                print(f"   🔧 Fixing unquoted property names...")
                fixed_text = self._fix_unquoted_properties(text)
                try:
                    result = json.loads(fixed_text)
                    print(f"✅ Fixed unquoted property names successfully")
                    return result
                except json.JSONDecodeError as e_fixed:
                    print(f"❌ Property name fix failed: {e_fixed}")
                    text = fixed_text  # Use the fixed version for further processing
            
            # Try common fixes for missing delimiters
            if "Expecting ',' delimiter" in str(e):
                print(f"   🔧 Fixing missing commas...")
                fixed_text = self._fix_missing_commas(text)
                try:
                    result = json.loads(fixed_text)
                    print(f"✅ Fixed missing commas successfully")
                    return result
                except json.JSONDecodeError as e_fixed:
                    print(f"❌ Comma fix failed: {e_fixed}")
                    text = fixed_text
            
            # Try to fix truncated responses
            if "Unterminated string" in str(e) or hasattr(e, 'pos'):
                print(f"   🔧 Fixing truncated response...")
                fixed_text = self._fix_truncated_response(text)
                try:
                    result = json.loads(fixed_text)
                    print(f"✅ Fixed truncated response successfully")
                    return result
                except json.JSONDecodeError as e_fixed:
                    print(f"❌ Truncation fix failed: {e_fixed}")
                    text = fixed_text
            
            # Try to find JSON within the text
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_text = text[start_idx:end_idx]
                
                # Show problematic area for debugging
                if hasattr(e, 'pos') and e.pos < len(json_text):
                    error_context = json_text[max(0, e.pos-50):e.pos+50]
                    print(f"   Error context: ...{error_context}...")
                
                # SMART FIX: Preserve comprehensive plans - avoid cleaning truncated JSON
                error_msg = str(e)
                
                if "Unterminated string starting at" in error_msg or "Expecting value" in error_msg:
                    print(f"   🚫 SMART BYPASS: Truncated JSON - cleaning would destroy comprehensive kubectl commands")
                    print(f"   💡 Solution: Increase CLAUDE_MAX_OUTPUT_TOKENS or reduce workloads per batch")
                    
                    # Save debug but don't corrupt with cleaning
                    from datetime import datetime
                    debug_file = f"debug_json_truncation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    with open(debug_file, 'w') as f:
                        f.write(f"TRUNCATION ERROR - DO NOT CLEAN\n")
                        f.write(f"Original error: {e}\n")
                        f.write(f"JSON is truncated at: line {getattr(e, 'lineno', '?')} column {getattr(e, 'colno', '?')}\n")
                        f.write(f"Truncated JSON (first 2000 chars):\n{json_text[:2000]}\n")
                    
                    raise e  # Don't clean truncated JSON - it makes it worse
                
                print(f"   Original JSON has syntax issues - applying targeted cleaning...")
                
                # Enhanced JSON cleaning for escape issues (only for malformed JSON)
                cleaned_json = self._clean_json_text(json_text)
                
                try:
                    result = json.loads(cleaned_json)
                    print(f"✅ JSON cleaned and parsed successfully after escape fixing")
                    return result
                except json.JSONDecodeError as e2:
                    print(f"❌ Enhanced cleaning failed: {e2}")
                    print(f"   Second error location: line {getattr(e2, 'lineno', '?')} column {getattr(e2, 'colno', '?')}")
                    
                    # Last resort: try to fix the specific error location
                    if hasattr(e2, 'pos') and e2.pos < len(cleaned_json):
                        print(f"   Attempting targeted fix at position {e2.pos}")
                        fixed_json = self._fix_json_at_position(cleaned_json, e2.pos)
                        try:
                            result = json.loads(fixed_json)
                            print(f"✅ JSON fixed with targeted repair")
                            return result
                        except json.JSONDecodeError as e3:
                            print(f"❌ Targeted fix failed: {e3}")
                    
                    # Save the problematic JSON for debugging
                    from datetime import datetime
                    debug_file = f"debug_json_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    try:
                        with open(debug_file, 'w') as f:
                            f.write(f"Original error: {e}\n")
                            f.write(f"Enhanced cleaning error: {e2}\n")
                            f.write(f"Original text:\n{text}\n\n")
                            f.write(f"Cleaned JSON:\n{cleaned_json}\n")
                        print(f"💾 Debug info saved to: {debug_file}")
                    except Exception:
                        pass
                    
                    raise e2
            else:
                raise e
    
    def _fix_json_at_position(self, json_text: str, error_pos: int) -> str:
        """
        Attempt to fix JSON at a specific error position.
        Used as a last resort when general cleaning fails.
        """
        # Common fixes for specific positions
        if error_pos < len(json_text):
            char = json_text[error_pos]
            
            # If it's a backslash issue, try to escape it
            if char == '\\':
                # Look ahead to see what follows
                if error_pos + 1 < len(json_text):
                    next_char = json_text[error_pos + 1]
                    # If it's not a valid escape sequence, double the backslash
                    if next_char not in '"\\/bfnrtu':
                        return json_text[:error_pos] + '\\' + json_text[error_pos:]
            
            # If it's an unescaped quote in a string, escape it
            elif char == '"':
                # Check if we're inside a string value (not a key)
                # This is a simple heuristic
                before_context = json_text[max(0, error_pos-10):error_pos]
                if ':' in before_context and not before_context.strip().endswith(':'):
                    return json_text[:error_pos] + '\\"' + json_text[error_pos+1:]
        
        return json_text
    
    def _fix_unquoted_properties(self, text: str) -> str:
        """Fix unquoted property names in JSON (common Claude error)"""
        import re
        
        # Pattern to find unquoted property names
        # Matches: word_chars: (but not "word_chars":)
        pattern = r'(\s+)([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*'
        
        def quote_property(match):
            whitespace = match.group(1)
            prop_name = match.group(2)
            
            # Don't quote if already quoted or if it's a boolean/null
            if prop_name in ['true', 'false', 'null']:
                return match.group(0)
            
            return f'{whitespace}"{prop_name}": '
        
        # Apply the fix
        fixed_text = re.sub(pattern, quote_property, text)
        
        # Also fix cases at the beginning of lines
        fixed_text = re.sub(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*', r'"\1": ', fixed_text, flags=re.MULTILINE)
        
        return fixed_text
    
    def _fix_missing_commas(self, text: str) -> str:
        """Fix missing commas in JSON (common Claude error)"""
        import re
        
        # Pattern to find missing commas before closing braces or brackets
        # Matches: "value"\n} or "value"\n] (missing comma)
        
        # Fix missing commas before closing braces
        text = re.sub(r'"\s*\n\s*}', '"\n}', text)
        text = re.sub(r']\s*\n\s*}', '],\n}', text)
        text = re.sub(r'}\s*\n\s*}', '},\n}', text)
        
        # Fix missing commas before closing brackets  
        text = re.sub(r'"\s*\n\s*]', '"\n]', text)
        text = re.sub(r'}\s*\n\s*]', '},\n]', text)
        text = re.sub(r']\s*\n\s*]', '],\n]', text)
        
        # Fix missing commas between object properties
        text = re.sub(r'"\s*\n\s*"', '",\n"', text)
        text = re.sub(r'}\s*\n\s*"', '},\n"', text)
        text = re.sub(r']\s*\n\s*"', '],\n"', text)
        
        return text
    
    def _fix_truncated_response(self, text: str) -> str:
        """Fix truncated JSON responses by completing incomplete structures"""
        
        # Find the last complete brace structure
        brace_stack = []
        last_complete_pos = 0
        
        for i, char in enumerate(text):
            if char == '{':
                brace_stack.append('{')
            elif char == '}':
                if brace_stack:
                    brace_stack.pop()
                    if not brace_stack:  # Found complete structure
                        last_complete_pos = i + 1
            elif char == '[':
                brace_stack.append('[')
            elif char == ']':
                if brace_stack and brace_stack[-1] == '[':
                    brace_stack.pop()
        
        if last_complete_pos > 0:
            # Truncate at last complete structure
            fixed_text = text[:last_complete_pos]
            print(f"   Truncating at position {last_complete_pos} to complete structure")
            return fixed_text
        
        # If no complete structure, try to close unclosed strings and brackets
        lines = text.split('\n')
        fixed_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for unterminated strings
            if line.count('"') % 2 != 0:
                # Odd number of quotes, close the string
                if line.endswith('"'):
                    fixed_lines.append(line)
                else:
                    # Find last quote and close it
                    if '"' in line:
                        fixed_lines.append(line + '"')
                    else:
                        fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        
        # Close any unclosed braces
        fixed_text = '\n'.join(fixed_lines)
        
        # Count and close missing braces
        open_braces = fixed_text.count('{') - fixed_text.count('}')
        open_brackets = fixed_text.count('[') - fixed_text.count(']')
        
        # Close missing structures
        for _ in range(open_brackets):
            fixed_text += '\n]'
        for _ in range(open_braces):
            fixed_text += '\n}'
            
        return fixed_text
    
    def _clean_json_text(self, json_text: str) -> str:
        """
        Clean common JSON formatting issues from Claude responses with enhanced escape handling.
        Specifically handles kubectl commands and complex strings that cause JSON parsing errors.
        """
        import re
        
        # CRITICAL FIX: Handle invalid escape sequences first
        # This is the main cause of "Invalid \escape" errors
        json_text = self._fix_escape_sequences(json_text)
        
        # Fix percentage values (e.g., "120%" -> "120")
        json_text = re.sub(r':\s*(\d+(?:\.\d+)?)%', r': \1', json_text)
        
        # Fix currency values (e.g., "$342.85" -> "342.85")
        json_text = re.sub(r':\s*"\$(\d+(?:\.\d+)?)"', r': \1', json_text)
        json_text = re.sub(r':\s*\$(\d+(?:\.\d+)?)', r': \1', json_text)
        
        # Remove trailing commas before closing braces/brackets
        json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
        
        # Fix missing commas between array elements (common Claude issue)
        json_text = re.sub(r'"\s*\n\s*"', r'",\n"', json_text)
        json_text = re.sub(r'}\s*\n\s*{', r'},\n{', json_text)
        json_text = re.sub(r']\s*\n\s*"', r'],\n"', json_text)
        
        # Fix unquoted property names (but be careful not to quote strings in arrays)
        lines = json_text.split('\n')
        for i, line in enumerate(lines):
            # Only fix property names (lines with colons outside of quotes)
            if ':' in line and not line.strip().startswith('"'):
                # Match word characters followed by colon (property names)
                lines[i] = re.sub(r'(\w+):', r'"\1":', line)
            
            # Fix unquoted property values that are not numbers
            # Pattern: "property": unquoted_value  ->  "property": "quoted_value"
            if ':' in line:
                # Match quoted property followed by unquoted non-numeric value
                lines[i] = re.sub(r'("[\w-]+"):\s*([a-zA-Z][a-zA-Z0-9-]*)\s*([,}])', r'\1: "\2"\3', line)
                # Also handle case with dots like requests.cpu -> "requests.cpu"
                lines[i] = re.sub(r'(\w+\.\w+):', r'"\1":', line)
        json_text = '\n'.join(lines)
        
        # Fix single quotes to double quotes (but be careful with contractions)
        json_text = re.sub(r"'([^']*)':", r'"\1":', json_text)  # Property names
        json_text = re.sub(r":\s*'([^']*)'", r': "\1"', json_text)  # String values
        
        # Remove comments (// or /* */)
        json_text = re.sub(r'//.*?$', '', json_text, flags=re.MULTILINE)
        json_text = re.sub(r'/\*.*?\*/', '', json_text, flags=re.DOTALL)
        
        # Fix common Claude mistakes with arrays
        json_text = re.sub(r'"\s*\]\s*,\s*\[', r'"],\n[', json_text)
        
        return json_text
    
    def _fix_escape_sequences(self, text: str) -> str:
        """
        Fix invalid escape sequences that cause JSON parsing errors.
        
        This addresses the core issue: Claude generates kubectl commands with backslashes
        that aren't properly escaped for JSON, causing "Invalid \\escape" errors.
        """
        import re
        
        # First, let's handle the most common kubectl command issues
        # Fix unescaped backslashes in kubectl commands
        # Pattern: Look for strings containing kubectl commands with unescaped backslashes
        def fix_kubectl_escapes(match):
            content = match.group(1)
            # Escape any lone backslashes that aren't already escaped
            # This is tricky - we need to escape backslashes but not break already valid escapes
            content = re.sub(r'\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', r'\\\\', content)
            return '"' + content + '"'
        
        # Apply the fix to quoted strings (likely command strings)
        text = re.sub(r'"([^"]*kubectl[^"]*)"', fix_kubectl_escapes, text)
        
        # CRITICAL FIX: Handle JSONPath expressions with unescaped quotes
        # Pattern: kubectl ... -o jsonpath='{...=="value"...}' 
        # The =="value" needs to be escaped as ==\\"value\\"
        def fix_jsonpath_quotes(match):
            full_string = match.group(0)  # Full quoted string
            # Fix unescaped quotes in JSONPath expressions only
            # Look for patterns like =="NoSchedule" and escape them as ==\\"NoSchedule\\"
            fixed_string = re.sub(r'(==)"([^"]*)"', r'\1\\"\\2\\"', full_string)
            # Also fix other JSONPath comparison operators
            fixed_string = re.sub(r'(!=)"([^"]*)"', r'\1\\"\\2\\"', fixed_string)
            fixed_string = re.sub(r'(@\.effect==)"([^"]*)"', r'\1\\"\\2\\"', fixed_string)
            return fixed_string
        
        # Apply fix to any string containing kubectl with jsonpath
        text = re.sub(r'"[^"]*kubectl[^"]*-o jsonpath=[^"]*"', fix_jsonpath_quotes, text)
        
        # ADDITIONAL FIX: Handle response truncation issues
        # If the response is truncated, we often get incomplete JSON at the end
        # Try to complete common incomplete patterns
        text = self._fix_truncated_response(text)
        
        # Handle other common escape issues
        # Fix unescaped backslashes in any quoted string
        def fix_general_escapes(match):
            content = match.group(1)
            # Only escape lone backslashes, preserve valid JSON escapes
            content = re.sub(r'\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', r'\\\\', content)
            return '"' + content + '"'
        
        # Apply to all remaining quoted strings that might have issues
        text = re.sub(r'"([^"]*\\[^"]*)"', fix_general_escapes, text)
        
        # Fix specific problematic patterns that Claude commonly generates
        # Fix namespace patterns like \n that should be \\n
        text = re.sub(r'([^\\])\\n', r'\1\\\\n', text)
        text = re.sub(r'([^\\])\\t', r'\1\\\\t', text)
        text = re.sub(r'([^\\])\\r', r'\1\\\\r', text)
        
        # CRITICAL: Fix actual control characters (not escape sequences)
        # These are real newlines/tabs in strings that need to be escaped
        def escape_control_chars(match):
            content = match.group(1)
            # Replace actual control characters with their escaped versions
            content = content.replace('\n', '\\n')
            content = content.replace('\t', '\\t')
            content = content.replace('\r', '\\r')
            content = content.replace('\b', '\\b')
            content = content.replace('\f', '\\f')
            return '"' + content + '"'
        
        # Apply to quoted strings that might contain control characters
        text = re.sub(r'"([^"]*[\n\t\r\b\f][^"]*)"', escape_control_chars, text)
        
        # Additional comprehensive control character fix for all JSON strings
        # This catches cases the regex above might miss
        import json
        def fix_all_control_chars_in_strings(text):
            # Handle the text as a single string to properly track JSON state
            result = ""
            in_string = False
            escape_next = False
            i = 0
            
            while i < len(text):
                char = text[i]
                
                if escape_next:
                    # Previous char was backslash, keep this char as is
                    result += char
                    escape_next = False
                elif char == '\\' and in_string:
                    # Check if it's already a valid escape sequence
                    if i + 1 < len(text) and text[i + 1] in '"\\/bfnrtu':
                        result += char  # Keep valid escape as is
                        escape_next = True
                    else:
                        result += '\\\\'  # Escape lone backslash
                elif char == '"':
                    # Toggle string state (only if not escaped)
                    in_string = not in_string
                    result += char
                elif in_string:
                    # We're inside a JSON string, escape control characters
                    if char == '\n':
                        result += '\\n'
                    elif char == '\t':
                        result += '\\t'
                    elif char == '\r':
                        result += '\\r'
                    elif char == '\b':
                        result += '\\b'
                    elif char == '\f':
                        result += '\\f'
                    elif ord(char) < 32:  # Any control character
                        result += f'\\u{ord(char):04x}'
                    else:
                        result += char
                else:
                    # Outside string, copy as is
                    result += char
                
                i += 1
            
            return result
        
        text = fix_all_control_chars_in_strings(text)
        
        # Fix kubectl patch JSON patterns that commonly break
        # Pattern like: 'kubectl patch ... -p '{\"spec\":...}'
        # The single quotes around JSON cause issues
        def fix_kubectl_json_patch(match):
            prefix = match.group(1)  # everything before -p
            json_content = match.group(2)  # the JSON inside single quotes
            
            # The JSON content needs to be treated as a string, not parsed JSON
            # So we need to escape it properly for inclusion in the outer JSON
            escaped_json = json_content.replace('\\', '\\\\').replace('\"', '\\\"')
            return f'kubectl patch {prefix} -p \'{escaped_json}\''
        
        text = re.sub(r"kubectl patch ([^']*) -p '([^']*)'", fix_kubectl_json_patch, text)
        
        # Fix kubectl apply with heredoc YAML content that breaks JSON
        # Pattern: "kubectl apply -f - <<EOF\n<YAML content>\nEOF"
        def fix_kubectl_yaml_heredoc(match):
            command_start = match.group(1)
            yaml_content = match.group(2)
            
            # Properly escape the entire kubectl command as a JSON string
            # Replace actual newlines with \n, escape quotes, etc.
            escaped_content = yaml_content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\t', '\\t').replace('\r', '\\r')
            full_command = f"{command_start}<<EOF\\n{escaped_content}\\nEOF"
            return f'"{full_command}"'
        
        # Match kubectl apply commands with heredoc
        text = re.sub(r'"(kubectl apply -f - )<<EOF\s*\n([^"]*?)\nEOF"', fix_kubectl_yaml_heredoc, text, flags=re.MULTILINE | re.DOTALL)
        
        # Fix common path separators in container paths
        text = re.sub(r'(/[^"\s]*)', lambda m: m.group(1).replace('\\', '/'), text)
        
        # Final JSON validation and repair
        text = self._final_json_repair(text)
        
        return text
    
    def _fix_truncated_response(self, text: str) -> str:
        """
        Fix common truncation issues in Claude responses where JSON is incomplete.
        This often happens when the response hits token limits.
        """
        import re
        
        # Remove any trailing incomplete content that's clearly truncated
        # Look for common truncation patterns
        
        # If JSON ends with incomplete string or structure
        text = text.strip()
        
        # Find the last complete JSON structure
        # Count braces to find where valid JSON might end
        open_braces = 0
        last_valid_pos = len(text)
        
        for i, char in enumerate(text):
            if char == '{':
                open_braces += 1
            elif char == '}':
                open_braces -= 1
                if open_braces == 0:
                    # Found a complete top-level object
                    last_valid_pos = i + 1
        
        # If we have unclosed braces, truncate to last valid position
        if open_braces > 0 and last_valid_pos < len(text):
            print(f"🔧 Truncating response at position {last_valid_pos} to remove incomplete JSON")
            text = text[:last_valid_pos]
        
        # Fix common truncation artifacts
        # Remove trailing incomplete quotes or strings
        text = re.sub(r'[^}]\s*$', '', text)  # Remove trailing non-brace content
        
        # If text ends with incomplete array or object, try to close it
        if text.endswith(','):
            text = text[:-1]  # Remove trailing comma
        
        # Ensure proper closing
        if not text.endswith('}') and not text.endswith(']'):
            # Try to find the last complete structure
            for end_char in ['}', ']']:
                last_pos = text.rfind(end_char)
                if last_pos > 0:
                    text = text[:last_pos + 1]
                    break
        
        return text
    
    def _final_json_repair(self, text: str) -> str:
        """Final attempt to repair JSON structure"""
        import re
        import json
        
        # Ensure the JSON is properly closed
        text = text.strip()
        
        # Count braces to see if we need to close the JSON
        open_braces = text.count('{')
        close_braces = text.count('}')
        
        # Count brackets for arrays
        open_brackets = text.count('[')
        close_brackets = text.count(']')
        
        # Remove trailing commas before closing braces/brackets
        text = re.sub(r',(\s*[}\]])', r'\1', text, flags=re.MULTILINE)
        
        # Fix incomplete arrays or objects at the end
        # Look for incomplete structures like: "key": [
        text = re.sub(r':\s*\[\s*$', r': []', text)
        text = re.sub(r':\s*\{\s*$', r': {}', text)
        
        # Fix incomplete quoted strings at the end
        # Count quotes to see if we have an unterminated string
        quote_count = text.count('"')
        if quote_count % 2 != 0:  # Odd number of quotes means unterminated string
            # Find the last quote and close the string
            last_quote_pos = text.rfind('"')
            if last_quote_pos != -1:
                # Check if this quote is at the very end or followed by incomplete content
                remaining = text[last_quote_pos + 1:].strip()
                if remaining and not remaining.startswith(',') and not remaining.startswith('}') and not remaining.startswith(']'):
                    # Terminate the string
                    text = text[:last_quote_pos + 1] + '"' + text[last_quote_pos + 1:]
        
        # Add missing closing brackets for arrays
        while close_brackets < open_brackets:
            text += '\n]'
            close_brackets += 1
        
        # Add missing closing braces for objects
        while close_braces < open_braces:
            text += '\n}'
            close_braces += 1
        
        # Fix any remaining double escape issues
        text = re.sub(r'\\\\n', r'\\n', text)  # \\n -> \n
        text = re.sub(r'\\\\t', r'\\t', text)  # \\t -> \t
        text = re.sub(r'\\\\r', r'\\r', text)  # \\r -> \r
        
        # Final validation attempt
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError as e:
            # If it still fails, try to fix common issues
            if "Expecting ',' delimiter" in str(e):
                # Try to add missing commas before closing braces
                text = re.sub(r'\n(\s*[}\]])', r',\n\1', text)
                # Remove any double commas
                text = re.sub(r',,+', r',', text)
                # Remove comma before closing
                text = re.sub(r',(\s*[}\]])', r'\1', text)
            
            elif "Expecting property name" in str(e):
                # Try to fix missing property names
                text = re.sub(r'{\s*,', r'{', text)
                text = re.sub(r',\s*}', r'}', text)
            
            return text
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on model"""
        if "haiku" in self.model.lower():
            return (input_tokens * 0.25 + output_tokens * 1.25) / 1_000_000
        elif "sonnet" in self.model.lower() and "3-5" in self.model:
            return (input_tokens * 3.0 + output_tokens * 15.0) / 1_000_000
        else:
            return (input_tokens * 3.0 + output_tokens * 15.0) / 1_000_000

    def _get_minimal_analysis(self) -> dict:
        """Return minimal analysis structure as fallback"""
        return {
            'cluster_dna_analysis': {
                'overall_score': 0,
                'description': 'Analysis unavailable'
            },
            'build_quality_assessment': {
                'quality_checks': []
            },
            'naming_conventions_analysis': {
                'overall_score': 0
            },
            'roi_analysis': {
                'summary_metrics': []
            },
            'review_schedule': []
        }
    
    def _extract_json_from_response(self, text: str) -> dict:
        """Extract JSON from response text"""
        return self._extract_json(text)
    
    def _build_core_plan_system_prompt(self) -> str:
        """System prompt for core implementation plan (Call 1)"""
        
        from shared.standards.standards_loader import get_standards_loader
        loader = get_standards_loader()
        
        # Get individual standards components
        cpu_standards = loader.get_cpu_utilization_target()
        memory_standards = loader.get_memory_utilization_target()
        hpa_standards = loader.get_hpa_standards()
        optimization_thresholds = loader.get_optimization_thresholds()
        
        standards_text = self._format_standards_brief({
            'resource_utilization': {
                'cpu': cpu_standards,
                'memory': memory_standards
            },
            'hpa_standards': hpa_standards,
            'optimization_thresholds': optimization_thresholds
        })
        
        return f"""You are a Kubernetes FinOps Expert creating comprehensive enterprise-grade implementation plans.

CRITICAL: This is PART 1 of a 2-part response. Generate ONLY the core implementation plan with enterprise-level detail.

Your response must be under 3,500 tokens and include ALL of these sections:

✅ metadata (plan_id, cluster_name, generated_date, resource_group, subscription_id, plan_version, analysis_confidence, implementation_complexity, estimated_duration_days)
✅ executive_summary (current_monthly_cost, potential_monthly_savings, savings_percentage, annual_savings, payback_period_months, roi_12_months, optimization_opportunities, critical_issues, implementation_phases)
✅ cluster_health_analysis (overall_cluster_score, cluster_grade, health_categories with cost_efficiency, performance_optimization, security_compliance, operational_excellence scores and issues)
✅ standards_compliance_analysis (cncf_finops_score, azure_waf_score, kubernetes_best_practices_score, compliance_gaps)
✅ phases (4-6 phases with phase_number, name, priority, duration_days, estimated_savings, description, prerequisites, actions, monitoring)
✅ success_metrics (cost_targets, operational_targets, governance_targets)
✅ monitoring_and_alerting (cost_monitoring, performance_monitoring, security_monitoring)

DO NOT INCLUDE (these are in Part 2):
❌ cluster_dna_analysis
❌ build_quality_assessment  
❌ naming_conventions_analysis
❌ roi_analysis (full breakdown)
❌ disaster_recovery
❌ compliance_and_governance
❌ next_steps

ENTERPRISE REQUIREMENTS:
- Each phase must have 2-4 detailed actions
- Each action must include: action_id, name, priority, estimated_savings, commands (backup, implement, validate, rollback), success_criteria
- Include comprehensive monitoring strategies
- Provide detailed compliance analysis
- Focus on production-ready implementations

STANDARDS TO FOLLOW:
{standards_text}

OUTPUT FORMAT:
Respond ONLY with valid JSON wrapped in ```json code fence.

CRITICAL JSON RULES:
- ALL strings must be in double quotes
- Numbers must be pure numbers (no %, $, or other symbols)
- Use decimal numbers for percentages (e.g., 0.315 not 31.5%)
- Use numbers for currency (e.g., 342.85 not "$342.85")
- No trailing commas
- No comments inside JSON

Example structure:
```json
{{
  "metadata": {{ "plan_id": "...", "cluster_name": "...", "generated_date": "...", "plan_version": "2.0", "analysis_confidence": "high", "implementation_complexity": "high", "estimated_duration_days": 45 }},
  "executive_summary": {{ "current_monthly_cost": 2111.71, "potential_monthly_savings": 682.45, "savings_percentage": 0.323, "annual_savings": 8189.4, "payback_period_months": 2.1, "roi_12_months": 287.3, "optimization_opportunities": 674, "critical_issues": 12, "implementation_phases": 6 }},
  "cluster_health_analysis": {{ "overall_cluster_score": 42, "cluster_grade": "D+", "health_categories": {{ "cost_efficiency": {{ "score": 18, "grade": "F", "issues": [...] }}, "performance_optimization": {{ "score": 35, "grade": "F", "issues": [...] }} }} }},
  "phases": [{{ "phase_number": 1, "name": "Critical Performance Issues Resolution", "priority": "critical", "duration_days": 3, "estimated_savings": 127.50, "actions": [{{ "action_id": "1.1", "name": "...", "priority": "critical", "estimated_savings": 67.30, "commands": {{ "backup": [...], "implement": [...], "validate": [...], "rollback": [...] }}, "success_criteria": [...] }}] }}],
  "success_metrics": {{ "cost_targets": {{ "monthly_cost_reduction": 0.315 }}, "operational_targets": {{ "application_availability": 0.999 }} }}
}}
```

Create a comprehensive, enterprise-grade implementation plan with detailed actions and monitoring."""

    def _build_core_plan_user_prompt(self, context: dict, cluster_name: str) -> str:
        """User prompt for core implementation plan"""
        
        import json
        context_json = json.dumps(context, indent=2)
        
        return f"""Generate a comprehensive enterprise-grade implementation plan for cluster: {cluster_name}

Cluster context:
{context_json}

REQUIREMENTS:
- Create 4-6 implementation phases with detailed actions
- Include comprehensive cluster health analysis with scoring
- Provide standards compliance assessment (FinOps, Azure WAF, Kubernetes best practices)
- Add executive summary with ROI projections
- Include detailed monitoring and alerting strategies
- Focus on production-ready, enterprise-grade optimizations
- Ensure each action has backup, implement, validate, and rollback commands
- Include success criteria and estimated savings per action

CRITICAL FOCUS AREAS:
1. Performance optimization (CPU/memory right-sizing, HPA, VPA)
2. Infrastructure optimization (spot instances, autoscaling)
3. Security compliance (network policies, pod security standards)
4. Cost governance (resource quotas, monitoring, alerting)
5. Operational excellence (monitoring stack, observability)

Keep response under 3,500 tokens but include all required enterprise sections."""

    def _build_analysis_system_prompt(self) -> str:
        """System prompt for detailed analysis (Call 2)"""
        
        return """You are a Kubernetes FinOps Expert providing comprehensive enterprise analysis and governance.

CRITICAL: This is PART 2 of a 2-part response. Generate ONLY the detailed analysis and governance sections.

Your response must be under 3,000 tokens and include ALL of these sections:

✅ cluster_dna_analysis (overall_score, metrics with descriptions, data_sources)
✅ build_quality_assessment (quality_checks, strengths, improvements, scorecard with quality_dimensions)
✅ naming_conventions_analysis (overall_score, resources with types and scores, recommendations)
✅ roi_analysis (summary_metrics, implementation_costs, savings_timeline, break_even_analysis, risk_factors)
✅ disaster_recovery (backup_strategy, rollback_procedures with RTOs and RPOs)
✅ compliance_and_governance (policy_frameworks, audit_requirements, compliance_scores)
✅ next_steps (timeline-based milestones for weeks/months)

DO NOT INCLUDE (already in Part 1):
❌ metadata
❌ executive_summary
❌ cluster_health_analysis
❌ standards_compliance_analysis
❌ phases
❌ success_metrics
❌ monitoring_and_alerting

ENTERPRISE REQUIREMENTS:
- ROI analysis must include implementation costs and break-even analysis
- Disaster recovery must specify RTOs, RPOs, and detailed procedures
- Compliance framework must reference industry standards (CIS, Azure Security Baseline, FinOps Foundation)
- Include specific audit trails and governance controls
- Provide risk assessment and mitigation strategies

OUTPUT FORMAT:
Respond ONLY with valid JSON wrapped in ```json code fence.

CRITICAL JSON RULES:
- ALL strings must be in double quotes
- Numbers must be pure numbers (no %, $, or other symbols)
- Use decimal numbers for percentages (e.g., 0.89 not 89%)
- Use numbers for currency (e.g., 342.85 not "$342.85")
- No trailing commas
- No comments inside JSON

Example structure:
```json
{
  "cluster_dna_analysis": { "overall_score": 0.89, "metrics": [{"name": "Workload Diversity", "score": 0.7, "description": "..."}], "data_sources": ["Kubernetes API", "Kubecost", "Prometheus"] },
  "roi_analysis": { "implementation_costs": {"personnel_hours": 180, "hourly_rate": 150, "total_implementation_cost": 30700}, "savings_timeline": {"month_1": 127.50}, "break_even_analysis": {"break_even_month": 4.4, "roi_12_months": 22.7} },
  "disaster_recovery": { "backup_strategy": {"etcd_backups": "Every 6 hours to Azure Storage", "recovery_time_objective": "2 hours", "recovery_point_objective": "15 minutes"} },
  "compliance_and_governance": { "policy_frameworks": ["CIS Kubernetes Benchmark", "Azure Security Baseline"], "compliance_scores": {"security_baseline": "Target: 90%"} },
  "next_steps": ["Week 1: Execute Phase 1 (Critical Performance Issues)", "Month 3: Full optimization review"]
}
```

Provide enterprise-grade analysis with comprehensive governance and risk management."""

    def _build_analysis_user_prompt(self, context: dict, cluster_name: str) -> str:
        """User prompt for detailed analysis"""
        
        import json
        context_json = json.dumps(context, indent=2)
        
        return f"""Generate comprehensive enterprise analysis and governance framework for cluster: {cluster_name}

Cluster context:
{context_json}

REQUIREMENTS:
- Analyze cluster DNA with detailed metrics and scoring
- Assess build quality across multiple dimensions (scalability, security, observability)
- Evaluate naming conventions and provide recommendations
- Create detailed ROI analysis with implementation costs, savings timeline, and break-even analysis
- Design disaster recovery strategy with RTOs, RPOs, and backup procedures
- Establish compliance and governance framework with industry standards
- Include risk assessment and mitigation strategies
- Provide timeline-based next steps and milestones

ENTERPRISE GOVERNANCE FOCUS:
1. Financial governance (cost allocation, budget controls, anomaly detection)
2. Security governance (policy enforcement, admission controllers, audit trails)
3. Operational governance (SLIs, SLOs, monitoring, alerting)
4. Compliance governance (CIS benchmarks, Azure Security Baseline, FinOps principles)
5. Risk management (backup strategies, rollback procedures, business continuity)

Keep response under 3,000 tokens but include all required governance sections."""

    def _format_standards_brief(self, standards: dict) -> str:
        """Format standards briefly for prompt"""
        cpu = standards['resource_utilization']['cpu']
        mem = standards['resource_utilization']['memory']
        hpa = standards['hpa_standards']
        opt = standards.get('optimization_thresholds', {})
        
        standards_text = f"""CPU: {cpu['target_min']:.0f}-{cpu['target_max']:.0f}% target, {cpu['optimal']:.0f}% optimal
Memory: {mem['target_min']:.0f}-{mem['target_max']:.0f}% target, {mem['optimal']:.0f}% optimal
HPA: {hpa['target_cpu_utilization']}% CPU target, {hpa['coverage_target']:.0f}% coverage goal"""
        
        if opt is not None and opt:
            standards_text += f"""
Optimization Thresholds: Max {opt['payback_threshold_months']} months payback, min ${opt['minimum_monthly_savings']:.2f}/month"""
        
        return standards_text
    
